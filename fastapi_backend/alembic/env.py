from logging.config import fileConfig
import os
import sys

from pathlib import Path

from sqlalchemy import engine_from_config, inspect, text
from sqlalchemy import pool

from alembic import context
from alembic.script import ScriptDirectory

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), ".."))

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

from fastapi_backend.models.models import Base as MainBase
import fastapi_backend.models.autotest as _autotest_models  # noqa: F401
import fastapi_backend.models.ui_automation as _ui_automation_models  # noqa: F401
from fastapi_backend.core.config import settings

db_url = settings.DATABASE_URL
if db_url.startswith("sqlite+aiosqlite:///./"):
    db_url = "sqlite+aiosqlite:///" + str(
        (Path(__file__).resolve().parent.parent.parent / db_url.removeprefix("sqlite+aiosqlite:///./")).resolve()
    )
elif db_url.startswith("sqlite:///./"):
    db_url = "sqlite:///" + str(
        (Path(__file__).resolve().parent.parent.parent / db_url.removeprefix("sqlite:///./")).resolve()
    )
if db_url.startswith("sqlite+aiosqlite:///"):
    db_url = db_url.replace("sqlite+aiosqlite:///", "sqlite:///", 1)
elif db_url.startswith("postgresql+asyncpg://"):
    db_url = db_url.replace("postgresql+asyncpg://", "postgresql://", 1)
config.set_main_option("sqlalchemy.url", db_url)

target_metadata = MainBase.metadata


def _is_head_upgrade_command() -> bool:
    """Return true only for the deployment operation ``alembic upgrade head``."""
    command_options = getattr(config, "cmd_opts", None)
    command = getattr(command_options, "cmd", None)
    command_callable = command[0] if isinstance(command, tuple) and command else command
    command_name = getattr(command_callable, "__name__", "")
    revision = str(getattr(command_options, "revision", "")).strip().lower()
    return command_name == "upgrade" and revision in {"head", "heads"}


def _is_non_head_upgrade_command() -> bool:
    command_options = getattr(config, "cmd_opts", None)
    command = getattr(command_options, "cmd", None)
    command_callable = command[0] if isinstance(command, tuple) and command else command
    return getattr(command_callable, "__name__", "") == "upgrade"


def _bootstrap_empty_database(connection) -> bool:
    """Create a trustworthy head schema only when the database has no tables.

    The historical first revision was generated against an already-existing
    legacy schema, so it cannot build a brand-new database by itself. Existing
    databases are intentionally excluded: their state must always be advanced
    through ordinary Alembic revisions and is never auto-stamped here.
    """
    if inspect(connection).get_table_names():
        return False
    # Schema inspection starts SQLAlchemy's implicit read transaction on some
    # dialects. End it before opening the single bootstrap write transaction.
    connection.commit()
    head = ScriptDirectory.from_config(config).get_current_head()
    if not head:
        raise RuntimeError("Alembic 未找到可用于空库初始化的 head revision")
    with connection.begin():
        target_metadata.create_all(bind=connection)
        connection.execute(text(
            "CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL)"
        ))
        connection.execute(
            text("INSERT INTO alembic_version (version_num) VALUES (:revision)"),
            {"revision": head},
        )
    return True


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        if not inspect(connection).get_table_names():
            if _is_head_upgrade_command() and _bootstrap_empty_database(connection):
                return
            if _is_non_head_upgrade_command():
                raise RuntimeError(
                    "空数据库只能执行 'alembic upgrade head' 初始化；"
                    "历史迁移链无法安全构建指定旧版本。"
                )
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,
        )

        with context.begin_transaction():
            context.run_migrations()
        # SQLite treats DDL as non-transactional, but its alembic_version
        # UPDATE can still remain in an implicit transaction. Commit after
        # every migration run so schema and recorded revision cannot diverge.
        connection.commit()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
