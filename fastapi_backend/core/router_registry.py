from __future__ import annotations

import importlib
import logging
from typing import Any

_logger = logging.getLogger(__name__)

_ROUTER_MODULES = {
    "admin": [
        "fastapi_backend.routers.admin",
        "fastapi_backend.routers.admin_users",
        "fastapi_backend.routers.admin_system",
        "fastapi_backend.routers.admin_system_mgmt",
        "fastapi_backend.routers.admin_paths",
        "fastapi_backend.routers.admin_exercises",
        "fastapi_backend.routers.admin_exams",
        "fastapi_backend.routers.admin_community",
        "fastapi_backend.routers.backup",
        "fastapi_backend.routers.rbac",
        "fastapi_backend.routers.ai_config",
    ],
    "autotest": [
        "fastapi_backend.routers.autotest_cases",
        "fastapi_backend.routers.autotest_scenarios",
        "fastapi_backend.routers.autotest_execution",
        "fastapi_backend.routers.autotest_groups",
        "fastapi_backend.routers.autotest_environments",
        "fastapi_backend.routers.autotest_global_variables",
        "fastapi_backend.routers.autotest_health",
        "fastapi_backend.routers.autotest_jmeter",
        "fastapi_backend.routers.autotest_diff",
        "fastapi_backend.routers.autotest_diagnostic",
        "fastapi_backend.routers.autotest_debug",
        "fastapi_backend.routers.autotest_data_factory",
        "fastapi_backend.routers.autotest_suites",
        "fastapi_backend.routers.autotest_ai_generate",
        "fastapi_backend.routers.autotest_coverage",
        "fastapi_backend.routers.autotest_export",
        "fastapi_backend.routers.performance_report",
    ],
    "learning": [
        "fastapi_backend.routers.learning_paths",
        "fastapi_backend.routers.exercise",
        "fastapi_backend.routers.exercises",
        "fastapi_backend.routers.exam",
        "fastapi_backend.routers.interview",
        "fastapi_backend.routers.skills",
        "fastapi_backend.routers.projects",
        "fastapi_backend.routers.assessment",
    ],
    "ai_tools": [
        "fastapi_backend.routers.ai_tutor",
        "fastapi_backend.routers.sandbox",
        "fastapi_backend.routers.mock_api",
    ],
    "standalone": [
        "fastapi_backend.routers.auth",
        "fastapi_backend.routers.checkin",
        "fastapi_backend.routers.leaderboard",
        "fastapi_backend.routers.favorites",
        "fastapi_backend.routers.notes",
        "fastapi_backend.routers.notifications",
        "fastapi_backend.routers.achievements",
        "fastapi_backend.routers.certificates",
        "fastapi_backend.routers.community",
        "fastapi_backend.routers.search",
        "fastapi_backend.routers.tools",
        "fastapi_backend.routers.assert_templates",
        "fastapi_backend.routers.report",
        "fastapi_backend.routers.reports",
    ],
}


def _load_router(module_name: str) -> Any:
    try:
        mod = importlib.import_module(module_name)
        if hasattr(mod, "router"):
            return mod.router
        _logger.warning("模块 %s 没有 router 属性，跳过", module_name)
        return None
    except Exception:
        _logger.exception("加载路由模块 %s 失败", module_name)
        return None


def _load_extra_routers(module_name: str) -> list:
    """加载模块中除 router 外的额外路由（如 mock_public_router）"""
    try:
        mod = importlib.import_module(module_name)
        extra_names = getattr(mod, "EXTRA_ROUTERS", [])
        routers = []
        for name in extra_names:
            if hasattr(mod, name):
                routers.append(getattr(mod, name))
        return routers
    except Exception:
        return []


def discover_routers() -> dict[str, Any]:
    result: dict[str, Any] = {}
    for group_name, modules in _ROUTER_MODULES.items():
        if group_name == "standalone":
            routers = []
            for mod_name in modules:
                router = _load_router(mod_name)
                if router is not None:
                    routers.append(router)
            result["standalone"] = routers
        else:
            from fastapi import APIRouter

            group_router = APIRouter()
            loaded = 0
            for mod_name in modules:
                router = _load_router(mod_name)
                if router is not None:
                    group_router.include_router(router)
                    loaded += 1
                # 加载额外路由
                for extra in _load_extra_routers(mod_name):
                    group_router.include_router(extra)
                    loaded += 1
            if loaded > 0:
                result[group_name] = group_router
            else:
                _logger.warning("分组 %s 没有成功加载任何路由", group_name)
    return result
