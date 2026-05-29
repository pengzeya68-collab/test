"""
Auto-discover and register all APIRouter instances from fastapi_backend.routers.

Each router module should expose a top-level `router = APIRouter(...)` variable.
Optionally, a module can define `ROUTER_GROUP: str` to assign it to a named group.
"""
from __future__ import annotations

import importlib
import logging
from pathlib import Path
from typing import Dict, List

from fastapi import APIRouter

_logger = logging.getLogger(__name__)

ROUTER_DIR = Path(__file__).resolve().parent.parent / "routers"

GROUP_MAP: Dict[str, List[str]] = {
    "admin": [
        "admin",
        "admin_users",
        "admin_exercises",
        "admin_paths",
        "admin_exams",
        "admin_community",
        "admin_system",
        "admin_system_mgmt",
        "ai_config",
        "backup",
        "rbac",
    ],
    "autotest": [
        "autotest_groups",
        "autotest_cases",
        "autotest_environments",
        "autotest_scenarios",
        "autotest_execution",
        "autotest_diagnostic",
        "autotest_global_variables",
        "autotest_jmeter",
        "autotest_data_factory",
        "autotest_diff",
        "autotest_suites",
        "autotest_health",
        "autotest_debug",
        "performance_report",
    ],
    "learning": [
        "learning_paths",
        "skills",
        "assessment",
        "achievements",
        "checkin",
        "leaderboard",
        "report",
        "notes",
        "certificates",
        "exam",
        "exercise",
        "exercises",
        "projects",
    ],
    "ai_tools": [
        "interview",
        "sandbox",
        "ai_tutor",
        "community",
    ],
}

STANDALONE_ROUTERS = [
    "auth",
    "notifications",
    "favorites",
    "search",
    "tools",
    "reports",
    "mock_api",
    "assert_templates",
]


def _load_router(module_name: str) -> APIRouter | None:
    try:
        mod = importlib.import_module(f"fastapi_backend.routers.{module_name}")
        router = getattr(mod, "router", None)
        if router is None:
            _logger.warning(f"Router module {module_name} has no 'router' attribute, skipping")
            return None
        return router
    except Exception as e:
        _logger.error(f"Failed to import router module {module_name}: {e}")
        return None


def discover_routers() -> Dict[str, APIRouter | List[APIRouter]]:
    result: Dict[str, APIRouter | List[APIRouter]] = {}

    for group_name, module_names in GROUP_MAP.items():
        group_router = APIRouter()
        loaded = 0
        for module_name in module_names:
            router = _load_router(module_name)
            if router is not None:
                group_router.include_router(router)
                loaded += 1
        if loaded > 0:
            result[group_name] = group_router
            _logger.info(f"Router group '{group_name}': {loaded} routers loaded")

    standalone_routers: List[APIRouter] = []
    for module_name in STANDALONE_ROUTERS:
        router = _load_router(module_name)
        if router is not None:
            standalone_routers.append(router)
    result["standalone"] = standalone_routers

    return result
