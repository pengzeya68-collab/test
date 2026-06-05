"""
AutoTest 全局变量持久化服务
从 utils/autotest_helpers.py 迁移
"""
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict

from sqlalchemy import select

_logger = logging.getLogger(__name__)


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

                # 使用数据库层面的 UPSERT，避免 TOCTOU 竞态条件
                try:
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
                        index_elements=['name', 'user_id'],
                        set_={
                            'value': serialized,
                            'updated_at': now,
                            'description': f"从{source}提取",
                        }
                    )
                    await session.execute(stmt)
                except Exception:
                    # 必须先回滚，清除 session 的错误状态
                    await session.rollback()
                    # 如果 UPSERT 失败，回退到 select-then-update
                    query = select(AutoTestGlobalVariable).where(AutoTestGlobalVariable.name == var_name)
                    if user_id is not None:
                        query = query.where(AutoTestGlobalVariable.user_id == user_id)
                    else:
                        query = query.where(AutoTestGlobalVariable.user_id.is_(None))
                    result = await session.execute(query)
                    existing_var = result.scalar_one_or_none()

                    if existing_var:
                        existing_var.value = serialized
                        existing_var.updated_at = now
                    else:
                        new_var = AutoTestGlobalVariable(
                            name=var_name,
                            value=serialized,
                            description=f"从{source}提取",
                            is_encrypted=False,
                            user_id=user_id,
                        )
                        session.add(new_var)

            await session.commit()
            return True
    except Exception as e:
        _logger.error(f"保存变量到数据库失败: {e}")
        return False
