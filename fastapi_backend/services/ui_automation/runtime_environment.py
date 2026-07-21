"""Resolve the runtime environment for a trusted UI execution client."""

from __future__ import annotations

import re
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_backend.core.exceptions import BusinessException
from fastapi_backend.models.autotest import AutoTestEnvironment, AutoTestGlobalVariable
from fastapi_backend.services.autotest_variable_service import get_effective_variables
from fastapi_backend.utils.encryption import decrypt


_SENSITIVE_VARIABLE = re.compile(
    r"(password|passwd|secret|token|api[_-]?key|private[_-]?key|authorization|cookie|session)",
    re.IGNORECASE,
)


async def resolve_runtime_environment(
    db: AsyncSession,
    *,
    user_id: int,
    environment_id: int | None,
) -> dict[str, Any]:
    """Return an owner-scoped execution snapshot, including required secrets.

    This result must only be returned to an authenticated user execution client
    or to the Agent that owns an already assigned run. Callers must never place
    the returned variables in logs, execution events, or persisted plans.
    """
    variables: dict[str, str] = {}
    secret_keys: set[str] = set()

    globals_result = await db.execute(select(AutoTestGlobalVariable).where(AutoTestGlobalVariable.user_id == user_id))
    for item in globals_result.scalars().all():
        try:
            value = decrypt(item.value) if item.is_encrypted else item.value
        except Exception as exc:
            raise BusinessException(
                "Runtime secret is unavailable",
                code="RUNTIME_SECRET_UNAVAILABLE",
                status_code=409,
            ) from exc
        variables[item.name] = "" if value is None else str(value)
        if item.is_encrypted or _SENSITIVE_VARIABLE.search(item.name):
            secret_keys.add(item.name)

    environment_name: str | None = None
    base_url = ""
    services: list[dict[str, Any]] = []
    if environment_id is not None:
        environment = await db.scalar(
            select(AutoTestEnvironment).where(
                AutoTestEnvironment.id == environment_id,
                AutoTestEnvironment.user_id == user_id,
            )
        )
        if environment is None:
            raise BusinessException(
                "Environment not found",
                code="ENVIRONMENT_NOT_FOUND",
                status_code=404,
            )
        environment_name = environment.env_name
        base_url = environment.base_url or ""
        services = environment.services if isinstance(environment.services, list) else []
        for item in await get_effective_variables(db, environment_id, user_id=user_id):
            name = str(item["name"])
            variables[name] = "" if item["value"] is None else str(item["value"])
            if _SENSITIVE_VARIABLE.search(name):
                secret_keys.add(name)

    return {
        "id": environment_id,
        "name": environment_name,
        "base_url": base_url,
        "services": services,
        "variables": variables,
        "secret_keys": sorted(secret_keys),
    }
