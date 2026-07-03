"""
AutoTest 统一路由 - 数据库连接管理

路径前缀: /api/auto-test/db-connections
CRUD + 测试连接，复用 environments 路由模式，密码加密复用 encryption.py
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi_backend.core.autotest_database import get_autotest_db as get_db
from fastapi_backend.deps.auth import get_current_active_user
from fastapi_backend.models.autotest import AutoTestDBConnection
from fastapi_backend.models.models import User
from fastapi_backend.schemas.autotest import (
    DBConnectionCreate,
    DBConnectionUpdate,
)
from fastapi_backend.utils.encryption import encrypt, decrypt, DecryptionError

router = APIRouter(prefix="/api/auto-test/db-connections", tags=["AutoTest-数据库连接"])


def _conn_to_dict(conn: AutoTestDBConnection) -> dict:
    """将连接对象转为字典（脱敏密码,但会检测密码是否可解密）"""
    password_decryptable = True
    if conn.password_encrypted:
        try:
            decrypt(conn.password_encrypted)
        except DecryptionError:
            password_decryptable = False

    return {
        "id": conn.id,
        "name": conn.name,
        "db_type": conn.db_type,
        "host": conn.host,
        "port": conn.port,
        "database_name": conn.database_name,
        "username": conn.username,
        "is_active": conn.is_active,
        "user_id": conn.user_id,
        "has_password": bool(conn.password_encrypted),
        "password_decryptable": password_decryptable,
        "created_at": conn.created_at.isoformat() if conn.created_at else None,
        "updated_at": conn.updated_at.isoformat() if conn.updated_at else None,
    }


@router.get("")
async def get_all_connections(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """获取所有数据库连接"""
    result = await db.execute(
        select(AutoTestDBConnection)
        .where(AutoTestDBConnection.user_id == current_user.id)
        .order_by(AutoTestDBConnection.created_at)
    )
    conns = result.scalars().all()
    return [_conn_to_dict(c) for c in conns]


@router.get("/{conn_id}")
async def get_connection(
    conn_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """获取单个数据库连接"""
    result = await db.execute(
        select(AutoTestDBConnection).filter(
            AutoTestDBConnection.id == conn_id,
            AutoTestDBConnection.user_id == current_user.id,
        )
    )
    conn = result.scalar_one_or_none()
    if not conn:
        raise HTTPException(status_code=404, detail="数据库连接不存在")
    return _conn_to_dict(conn)


@router.post("", status_code=201)
async def create_connection(
    conn_in: DBConnectionCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """创建数据库连接"""
    data = conn_in.model_dump()
    password = data.pop("password", None)

    conn = AutoTestDBConnection(**data, user_id=current_user.id)
    if password:
        conn.password_encrypted = encrypt(password)

    db.add(conn)
    await db.commit()
    await db.refresh(conn)
    return _conn_to_dict(conn)


@router.put("/{conn_id}")
async def update_connection(
    conn_id: int,
    conn_in: DBConnectionUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """更新数据库连接"""
    result = await db.execute(
        select(AutoTestDBConnection).filter(
            AutoTestDBConnection.id == conn_id,
            AutoTestDBConnection.user_id == current_user.id,
        )
    )
    conn = result.scalar_one_or_none()
    if not conn:
        raise HTTPException(status_code=404, detail="数据库连接不存在")

    update_data = conn_in.model_dump(exclude_unset=True)
    password = update_data.pop("password", None)

    for field, value in update_data.items():
        setattr(conn, field, value)

    # 密码特殊处理：空字符串表示清除，"****"表示不修改
    if password is not None and password != "****":
        conn.password_encrypted = encrypt(password) if password else None

    await db.commit()
    await db.refresh(conn)
    return _conn_to_dict(conn)


@router.delete("/{conn_id}")
async def delete_connection(
    conn_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """删除数据库连接"""
    result = await db.execute(
        select(AutoTestDBConnection).filter(
            AutoTestDBConnection.id == conn_id,
            AutoTestDBConnection.user_id == current_user.id,
        )
    )
    conn = result.scalar_one_or_none()
    if not conn:
        raise HTTPException(status_code=404, detail="数据库连接不存在")

    await db.delete(conn)
    await db.commit()
    return {"success": True, "message": "删除成功"}


@router.post("/{conn_id}/test")
async def test_connection(
    conn_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """测试数据库连接是否可用"""
    from fastapi_backend.services.db_operation_service import test_db_connection

    # 先验证连接归属
    result = await db.execute(
        select(AutoTestDBConnection).filter(
            AutoTestDBConnection.id == conn_id,
            AutoTestDBConnection.user_id == current_user.id,
        )
    )
    conn = result.scalar_one_or_none()
    if not conn:
        raise HTTPException(status_code=404, detail="数据库连接不存在")

    test_result = await test_db_connection(conn_id, current_user.id)
    return test_result
