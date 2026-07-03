"""
数据库操作服务

支持 MySQL/PostgreSQL/Redis 数据库查询，复用现有加密和变量提取工具。
"""

import logging
import time
from typing import Any, Dict, Optional, Tuple

_logger = logging.getLogger(__name__)

# MySQL 连接池（按 host:port:db 复用，避免每次查询新建连接）
_mysql_pools: Dict[str, Any] = {}


async def _get_mysql_pool(host: str, port: int, database: str, username: str, password: str):
    """获取或创建 MySQL 连接池（按连接配置复用）"""
    import aiomysql

    key = f"{host}:{port}:{database}"
    if key not in _mysql_pools:
        _mysql_pools[key] = await aiomysql.create_pool(
            host=host,
            port=port,
            db=database,
            user=username,
            password=password,
            connect_timeout=10,
            maxsize=10,
        )
    return _mysql_pools[key]


async def execute_db_query(
    connection_id: int,
    query: str,
    user_id: Optional[int] = None,
) -> Tuple[Any, int]:
    """
    执行数据库查询并返回结果。

    Returns:
        (result_data, elapsed_ms)
    """
    from fastapi_backend.core.autotest_database import async_session
    from fastapi_backend.models.autotest import AutoTestDBConnection
    from fastapi_backend.utils.encryption import decrypt
    from sqlalchemy import select

    start_time = time.time()

    async with async_session() as db:
        stmt = select(AutoTestDBConnection).where(AutoTestDBConnection.id == connection_id)
        if user_id is not None:
            stmt = stmt.where(AutoTestDBConnection.user_id == user_id)
        result = await db.execute(stmt)
        conn = result.scalar_one_or_none()

        if not conn:
            raise ValueError(f"数据库连接 {connection_id} 不存在")
        if not conn.is_active:
            raise ValueError(f"数据库连接 {conn.name} 已停用")

        # 解密密码
        password = None
        if conn.password_encrypted:
            try:
                password = decrypt(conn.password_encrypted)
            except Exception:
                # 解密失败说明密钥已更换或数据来自其他环境
                # 不能用密文当密码(会导致认证失败且令人困惑)
                raise ValueError(
                    f"数据库连接 [{conn.name}] 的密码解密失败,可能因加密密钥已更换。"
                    "请在'数据库连接'管理中重新编辑该连接并输入正确密码,然后重试。"
                )

        db_type = conn.db_type.lower()
        host = conn.host
        port = conn.port
        database = conn.database_name or ""
        username = conn.username or ""

    elapsed_ms = int((time.time() - start_time) * 1000)

    if db_type == "postgresql":
        return await _exec_postgresql(host, port, database, username, password, query, start_time)
    elif db_type == "mysql":
        return await _exec_mysql(host, port, database, username, password, query, start_time)
    elif db_type == "redis":
        return await _exec_redis(host, port, password, query, start_time)
    else:
        raise ValueError(f"不支持的数据库类型: {db_type}")


async def _exec_postgresql(
    host: str,
    port: int,
    database: str,
    username: str,
    password: str,
    query: str,
    start_time: float,
) -> Tuple[Any, int]:
    """执行 PostgreSQL 查询"""
    try:
        import asyncpg
    except ImportError:
        raise RuntimeError("asyncpg 未安装，无法连接 PostgreSQL")

    conn = await asyncpg.connect(
        host=host,
        port=port,
        database=database,
        user=username,
        password=password,
        timeout=10,
    )
    try:
        rows = await conn.fetch(query)
        elapsed = int((time.time() - start_time) * 1000)
        # 转换为 dict 列表
        result = [dict(row) for row in rows] if rows else []
        return result, elapsed
    finally:
        await conn.close()


async def _exec_mysql(
    host: str,
    port: int,
    database: str,
    username: str,
    password: str,
    query: str,
    start_time: float,
) -> Tuple[Any, int]:
    """执行 MySQL 查询（使用连接池复用连接）"""
    try:
        import aiomysql
    except ImportError:
        raise RuntimeError("aiomysql 未安装，无法连接 MySQL")

    pool = await _get_mysql_pool(host, port, database, username, password)
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(query)
            rows = await cur.fetchall()
            elapsed = int((time.time() - start_time) * 1000)
            return list(rows) if rows else [], elapsed


async def _exec_redis(
    host: str,
    port: int,
    password: str,
    query: str,
    start_time: float,
) -> Tuple[Any, int]:
    """执行 Redis 命令"""
    try:
        import redis.asyncio as aioredis
    except ImportError:
        raise RuntimeError("redis 未安装")

    r = aioredis.Redis(host=host, port=port, password=password, decode_responses=True, socket_timeout=10)
    try:
        # 简单命令解析: GET key, HGETALL key, KEYS pattern 等
        parts = query.strip().split()
        cmd = parts[0].upper() if parts else ""
        args = parts[1:] if len(parts) > 1 else []

        if cmd == "GET" and args:
            result = await r.get(args[0])
        elif cmd == "HGETALL" and args:
            result = await r.hgetall(args[0])
        elif cmd == "KEYS" and args:
            result = await r.keys(args[0])
        elif cmd == "SMEMBERS" and args:
            result = list(await r.smembers(args[0]))
        elif cmd == "LRANGE" and len(args) >= 3:
            result = await r.lrange(args[0], int(args[1]), int(args[2]))
        else:
            # 通用命令执行
            result = await r.execute_command(cmd, *args)

        elapsed = int((time.time() - start_time) * 1000)
        return result, elapsed
    finally:
        await r.aclose()


async def test_db_connection(connection_id: int, user_id: Optional[int] = None) -> Dict[str, Any]:
    """测试数据库连接是否可用"""
    from fastapi_backend.core.autotest_database import async_session
    from fastapi_backend.models.autotest import AutoTestDBConnection
    from sqlalchemy import select

    try:
        async with async_session() as db:
            stmt = select(AutoTestDBConnection).where(AutoTestDBConnection.id == connection_id)
            if user_id is not None:
                stmt = stmt.where(AutoTestDBConnection.user_id == user_id)
            result = await db.execute(stmt)
            conn = result.scalar_one_or_none()
            if not conn:
                return {"success": False, "elapsed_ms": 0, "message": "连接不存在"}
            db_type = conn.db_type.lower()

        # Redis 用 PING 测试，其他用 SELECT 1
        test_query = "PING" if db_type == "redis" else "SELECT 1"
        result_data, elapsed = await execute_db_query(connection_id, test_query, user_id)
        return {"success": True, "elapsed_ms": elapsed, "message": "连接成功"}
    except Exception as e:
        return {"success": False, "elapsed_ms": 0, "message": str(e)}
