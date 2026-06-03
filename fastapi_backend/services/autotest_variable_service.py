"""
AutoTest 全局变量持久化服务
从 utils/autotest_helpers.py 迁移
"""
import logging
from datetime import datetime, timezone
from typing import Any, Dict

from sqlalchemy import select

_logger = logging.getLogger(__name__)


async def save_variables_to_db(variables: Dict[str, Any], source: str = "测试", user_id: int = None) -> bool:
    if not variables:
        return False

    from fastapi_backend.core.autotest_database import async_session
    from fastapi_backend.models.autotest import AutoTestGlobalVariable

    try:
        async with async_session() as session:
            for var_name, var_value in variables.items():
                query = select(AutoTestGlobalVariable).where(AutoTestGlobalVariable.name == var_name)
                if user_id is not None:
                    query = query.where(AutoTestGlobalVariable.user_id == user_id)
                result = await session.execute(query)
                existing_var = result.scalar_one_or_none()

                if existing_var:
                    existing_var.value = str(var_value)
                    existing_var.updated_at = datetime.now(timezone.utc)
                else:
                    new_var = AutoTestGlobalVariable(
                        name=var_name,
                        value=str(var_value),
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
