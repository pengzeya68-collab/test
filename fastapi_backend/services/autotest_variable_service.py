"""
AutoTest 全局变量持久化服务
从 utils/autotest_helpers.py 迁移
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

_logger = logging.getLogger(__name__)


# ========== 环境变量继承机制 ==========
# 支持多层继承（A 继承 B，B 继承 C），最大深度 5 层避免循环。
# 解析规则：从根环境（最顶层祖先）开始，逐层向下，子环境的同名变量覆盖父环境。


# 最大继承链长度（含当前环境），即最大深度 5 层
MAX_INHERITANCE_DEPTH: int = 5


class InheritanceError(Exception):
    """环境继承异常基类（循环继承、超出最大深度等）"""

    def __init__(self, message: str, code: str = "inheritance_error"):
        super().__init__(message)
        self.message = message
        self.code = code


class CyclicInheritanceError(InheritanceError):
    """循环继承错误"""

    def __init__(self, message: str):
        super().__init__(message, code="cyclic_inheritance")


class MaxDepthExceededError(InheritanceError):
    """超出最大继承深度错误"""

    def __init__(self, message: str):
        super().__init__(message, code="max_depth_exceeded")


class EnvironmentNotFoundError(InheritanceError):
    """环境不存在错误"""

    def __init__(self, message: str):
        super().__init__(message, code="environment_not_found")


async def get_inheritance_chain(
    session: AsyncSession,
    env_id: int,
    user_id: Optional[int] = None,
) -> List[Any]:
    """
    获取环境继承链（从根环境到当前环境，按继承顺序排列）。

    解析逻辑：
    1. 从当前环境向上遍历 parent_id 直到根环境；
    2. 检测循环继承（出现重复 ID 立即抛出 CyclicInheritanceError）；
    3. 限制最大深度 MAX_INHERITANCE_DEPTH，超出抛出 MaxDepthExceededError；
    4. 反转链表，返回 [root, ..., current] 顺序。

    Args:
        session: 数据库会话
        env_id: 起始环境ID

    Returns:
        从根环境到当前环境的 AutoTestEnvironment 列表

    Raises:
        EnvironmentNotFoundError: 起始环境不存在
        CyclicInheritanceError: 检测到循环继承
        MaxDepthExceededError: 继承链长度超过 MAX_INHERITANCE_DEPTH
    """
    # 延迟导入避免循环引用
    from fastapi_backend.models.autotest import AutoTestEnvironment

    # 自底向上收集链路（先放当前环境）
    chain_bottom_up: List[Any] = []
    visited_ids: set[int] = set()
    current_id: Optional[int] = env_id
    steps = 0

    while current_id is not None:
        if current_id in visited_ids:
            # 已访问过，说明出现循环
            cycle_path = " -> ".join(str(e.id) for e in chain_bottom_up) + f" -> {current_id}"
            raise CyclicInheritanceError(
                f"检测到循环继承：{cycle_path}。请检查环境的 parent_id 配置。"
            )
        if steps >= MAX_INHERITANCE_DEPTH:
            raise MaxDepthExceededError(
                f"继承链深度超过最大限制 {MAX_INHERITANCE_DEPTH} 层。"
                f"请减少环境继承层级（当前已遍历 {steps} 层）。"
            )

        query = select(AutoTestEnvironment).where(AutoTestEnvironment.id == current_id)
        if user_id is not None:
            query = query.where(AutoTestEnvironment.user_id == user_id)
        result = await session.execute(query)
        env = result.scalar_one_or_none()
        if env is None:
            if steps == 0:
                raise EnvironmentNotFoundError(f"环境 ID={env_id} 不存在。")
            # 中途找不到父环境（数据不一致），中断向上查找
            _logger.warning(
                "继承链解析时父环境 ID=%s 不存在，链路在中间断开。", current_id
            )
            break

        visited_ids.add(current_id)
        chain_bottom_up.append(env)
        current_id = env.parent_id
        steps += 1

    # 反转为从根到当前的顺序
    chain_top_down = list(reversed(chain_bottom_up))
    return chain_top_down


async def get_effective_variables(
    session: AsyncSession,
    env_id: int,
    user_id: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    计算合并后的有效变量列表（含来源标注）。

    合并规则：
    1. 调用 get_inheritance_chain 得到 [root, ..., current]；
    2. 从根环境开始逐层合并变量字典，子环境覆盖父环境同名变量；
    3. 每个最终变量标注 source_environment_id/source_environment_name；
    4. is_overridden=True 表示该变量在更上层环境中曾被定义但被下层覆盖。

    Args:
        session: 数据库会话
        env_id: 目标环境ID

    Returns:
        合并后的变量列表，每个元素为 dict：
        {name, value, source_environment_id, source_environment_name, is_overridden}
    """
    chain = await get_inheritance_chain(session, env_id, user_id=user_id)

    # 记录每个变量名首次出现的来源（最上层），用于判断 is_overridden
    # 同时记录最终生效的值与来源
    # first_seen: name -> (env_id, env_name)
    first_seen: Dict[str, tuple[int, str]] = {}
    # final: name -> (value, env_id, env_name)
    final: Dict[str, tuple[Any, int, str]] = {}

    for env in chain:
        env_vars = env.variables if isinstance(env.variables, dict) else {}
        for var_name, var_value in env_vars.items():
            if var_name not in first_seen:
                first_seen[var_name] = (env.id, env.env_name)
            # 子环境覆盖父环境（后写入覆盖先写入）
            final[var_name] = (var_value, env.id, env.env_name)

    result: List[Dict[str, Any]] = []
    for var_name, (value, src_id, src_name) in final.items():
        first_id, _ = first_seen[var_name]
        # 如果当前生效来源与首次出现来源不同，说明被子环境覆盖
        is_overridden = src_id != first_id
        result.append(
            {
                "name": var_name,
                "value": value,
                "source_environment_id": src_id,
                "source_environment_name": src_name,
                "is_overridden": is_overridden,
            }
        )

    # 按变量名排序，便于稳定输出与测试断言
    result.sort(key=lambda v: v["name"])
    return result


async def validate_parent_id(
    session: AsyncSession,
    env_id: Optional[int],
    parent_id: Optional[int],
    user_id: Optional[int] = None,
) -> None:
    """
    校验 parent_id 是否合法（不形成循环、不超出最大深度、父环境存在）。

    应在创建/更新环境时调用。

    Args:
        session: 数据库会话
        env_id: 当前环境ID（创建时为 None）
        parent_id: 拟设置的父环境ID

    Raises:
        EnvironmentNotFoundError: 父环境不存在
        CyclicInheritanceError: 形成循环继承（包括指向自身）
        MaxDepthExceededError: 继承链超出最大深度
    """
    from fastapi_backend.models.autotest import AutoTestEnvironment

    if parent_id is None:
        return  # 无父环境，无需校验

    # 不允许指向自身（更新场景）
    if env_id is not None and parent_id == env_id:
        raise CyclicInheritanceError(
            f"环境不能继承自身：env_id={env_id}, parent_id={parent_id}。"
        )

    # 校验父环境存在
    parent_query = select(AutoTestEnvironment).where(AutoTestEnvironment.id == parent_id)
    if user_id is not None:
        parent_query = parent_query.where(AutoTestEnvironment.user_id == user_id)
    result = await session.execute(parent_query)
    parent_env = result.scalar_one_or_none()
    if parent_env is None:
        raise EnvironmentNotFoundError(f"父环境 ID={parent_id} 不存在。")

    # 临时模拟设置 parent_id 后的链路是否合法：
    # 从父环境向上走到根，加上当前环境这一层，总深度不能超过 MAX_INHERITANCE_DEPTH。
    # 同时检测循环（如果父环境的祖先链中包含 env_id，则形成环）。
    if env_id is not None:
        # 检查父环境的祖先链是否已包含当前 env_id（会形成循环）
        visited: set[int] = set()
        cursor: Optional[int] = parent_id
        while cursor is not None:
            if cursor == env_id:
                raise CyclicInheritanceError(
                    f"设置 parent_id={parent_id} 会形成循环继承（祖先链中已包含 env_id={env_id}）。"
                )
            if cursor in visited:
                # 父环境自身已存在循环（数据异常），抛出明确错误
                raise CyclicInheritanceError(
                    f"父环境 ID={parent_id} 的继承链已存在循环，无法继续继承。"
                )
            visited.add(cursor)
            cursor_query = select(AutoTestEnvironment.parent_id).where(AutoTestEnvironment.id == cursor)
            if user_id is not None:
                cursor_query = cursor_query.where(AutoTestEnvironment.user_id == user_id)
            r = await session.execute(cursor_query)
            row = r.first()
            cursor = row[0] if row else None

        # 深度检查：visited 已包含父环境及其全部祖先，加上当前环境共 len(visited)+1 层
        if len(visited) + 1 > MAX_INHERITANCE_DEPTH:
            raise MaxDepthExceededError(
                f"设置 parent_id={parent_id} 后继承链深度将超过最大限制 "
                f"{MAX_INHERITANCE_DEPTH} 层。"
            )
    else:
        # 创建场景：仅需校验父环境的祖先链深度 + 父本身 + 当前 不超过限制
        # 同时复用 get_inheritance_chain 的循环检测逻辑
        chain = await get_inheritance_chain(session, parent_id, user_id=user_id)
        # chain 为 [root, ..., parent]，加上当前环境共 len(chain) + 1 层
        if len(chain) + 1 > MAX_INHERITANCE_DEPTH:
            raise MaxDepthExceededError(
                f"设置 parent_id={parent_id} 后继承链深度将超过最大限制 "
                f"{MAX_INHERITANCE_DEPTH} 层。"
            )


def _serialize_var_value(var_value: Any) -> str:
    """将变量值序列化为字符串，保留类型信息"""
    if isinstance(var_value, (dict, list)):
        return json.dumps(var_value, ensure_ascii=False)
    if isinstance(var_value, bool):
        # bool 必须在 int 之前检查，因为 bool 是 int 的子类
        return json.dumps({"__type__": "bool", "__value__": str(var_value)})
    if isinstance(var_value, int):
        return json.dumps({"__type__": "int", "__value__": var_value})
    if isinstance(var_value, float):
        return json.dumps({"__type__": "float", "__value__": var_value})
    if isinstance(var_value, str):
        # 🔥 修复：为 str 类型也添加类型标记，避免反序列化时
        # json.loads("123") 把字符串 "123" 误判为 int 123
        return json.dumps({"__type__": "str", "__value__": var_value})
    return str(var_value)


def deserialize_var_value(raw_value: str) -> Any:
    """将数据库中的字符串值反序列化为原始类型"""
    if not raw_value:
        return raw_value
    # 尝试解析带类型信息的 JSON
    try:
        parsed = json.loads(raw_value)
        if isinstance(parsed, dict) and "__type__" in parsed and "__value__" in parsed:
            type_tag = parsed["__type__"]
            val = parsed["__value__"]
            if type_tag == "bool":
                return val == "True"
            if type_tag == "int":
                return int(val)
            if type_tag == "float":
                return float(val)
            if type_tag == "str":
                # 显式 str 标记：直接返回字符串值，不再做类型推断
                return str(val)
            return val
        # dict/list 直接返回
        return parsed
    except (json.JSONDecodeError, TypeError):
        pass
    return raw_value


async def save_variables_to_db(variables: Dict[str, Any], source: str = "测试", user_id: int = None) -> bool:
    if not variables:
        return False

    from fastapi_backend.core.autotest_database import async_session
    from fastapi_backend.models.autotest import AutoTestGlobalVariable
    from sqlalchemy import insert as sa_insert

    try:
        async with async_session() as session:
            for var_name, var_value in variables.items():
                serialized = _serialize_var_value(var_value)
                now = datetime.now(timezone.utc)

                if user_id is None:
                    # user_id 为 NULL 时 ON CONFLICT 不触发（PostgreSQL 中 NULL != NULL），
                    # 需要先查询再决定插入或更新
                    query = select(AutoTestGlobalVariable).where(
                        AutoTestGlobalVariable.name == var_name,
                        AutoTestGlobalVariable.user_id.is_(None),
                    )
                    result = await session.execute(query)
                    existing_var = result.scalar_one_or_none()
                    if existing_var:
                        existing_var.value = serialized
                        existing_var.updated_at = now
                        # 不更新 description，保留用户设置的值
                    else:
                        session.add(
                            AutoTestGlobalVariable(
                                name=var_name,
                                value=serialized,
                                description=f"从{source}提取",
                                is_encrypted=False,
                                user_id=user_id,
                            )
                        )
                else:
                    # user_id 非 NULL 时使用 ON CONFLICT
                    # 使用 savepoint 避免单个变量失败回滚所有已成功的变更
                    try:
                        async with session.begin_nested():
                            # PostgreSQL: INSERT ... ON CONFLICT DO UPDATE
                            stmt = sa_insert(AutoTestGlobalVariable).values(
                                name=var_name,
                                value=serialized,
                                description=f"从{source}提取",
                                is_encrypted=False,
                                user_id=user_id,
                                updated_at=now,
                            )
                            stmt = stmt.on_conflict_do_update(
                                index_elements=["name", "user_id"],
                                set_={
                                    "value": serialized,
                                    "updated_at": now,
                                    # 不更新 description，保留用户设置的值
                                },
                            )
                            await session.execute(stmt)
                    except Exception:
                        # savepoint 已自动回滚，回退到 select-then-update
                        query = select(AutoTestGlobalVariable).where(
                            AutoTestGlobalVariable.name == var_name,
                            AutoTestGlobalVariable.user_id == user_id,
                        )
                        result = await session.execute(query)
                        existing_var = result.scalar_one_or_none()

                        if existing_var:
                            existing_var.value = serialized
                            existing_var.updated_at = now
                        else:
                            session.add(
                                AutoTestGlobalVariable(
                                    name=var_name,
                                    value=serialized,
                                    description=f"从{source}提取",
                                    is_encrypted=False,
                                    user_id=user_id,
                                )
                            )

            await session.commit()
            return True
    except Exception as e:
        _logger.error(f"保存变量到数据库失败: {e}")
        return False
