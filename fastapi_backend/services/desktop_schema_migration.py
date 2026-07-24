"""Schema migration entry point used by the bundled desktop backend."""

from __future__ import annotations

import os
import sys
from argparse import Namespace
from pathlib import Path


def _resource_root() -> Path:
    """Return the directory containing bundled Alembic scripts."""
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS"))
    return Path(__file__).resolve().parents[2]


def upgrade_desktop_database() -> None:
    """Advance the desktop SQLite database to the packaged Alembic head.

    This is deliberately fail-closed.  ``create_all`` can create a fresh
    schema but cannot add or transform columns in an existing user database.
    """
    if os.getenv("TESTMASTER_DESKTOP_LOCAL") != "1":
        return

    from alembic import command
    from alembic.config import Config

    root = _resource_root()
    config_path = root / "fastapi_backend" / "alembic.ini"
    script_path = root / "fastapi_backend" / "alembic"
    if not config_path.is_file() or not script_path.is_dir():
        raise RuntimeError("桌面端数据库迁移文件缺失，请重新安装 TestMaster Desktop")

    config = Config(str(config_path))
    config.set_main_option("script_location", str(script_path))
    # The custom Alembic environment distinguishes a safe ``upgrade head``
    # bootstrap from replaying historical revisions on an empty database. The
    # command-line runner normally supplies these options; set their minimal
    # equivalent for this in-process desktop invocation.
    config.cmd_opts = Namespace(cmd=(command.upgrade, []), revision="head")
    command.upgrade(config, "head")
