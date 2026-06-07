"""
加密工具模块

提供对敏感信息的加密和解密功能
密钥从环境变量或固定配置中获取，确保重启后可解密
"""

import os
import base64
import hashlib
import logging

_logger = logging.getLogger(__name__)

from cryptography.fernet import Fernet

_FERNET_KEY_ENV = "TESTMASTER_ENCRYPTION_KEY"


def _derive_fernet_key(seed: str) -> bytes:
    derived = hashlib.sha256(seed.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(derived)


_KEY_SEED = os.environ.get(_FERNET_KEY_ENV)
if _KEY_SEED is None:
    env = os.environ.get("ENVIRONMENT", "development")
    if env == "production":
        raise RuntimeError(f"生产环境必须设置 {_FERNET_KEY_ENV}，请在 .env 文件中配置 TESTMASTER_ENCRYPTION_KEY")
    else:
        # 开发环境使用机器特定种子（hostname + 用户名），比硬编码更安全
        import platform

        machine_seed = f"dev-key-{platform.node()}-{os.environ.get('USERNAME', 'default')}"
        _KEY_SEED = machine_seed
        _logger.warning(
            "开发环境使用机器特定加密密钥，生产环境请务必在 .env 中设置 %s",
            _FERNET_KEY_ENV,
        )
KEY = _derive_fernet_key(_KEY_SEED)
fernet = Fernet(KEY)


def encrypt(data: str) -> str:
    if not data:
        return data
    return fernet.encrypt(data.encode()).decode()


class DecryptionError(Exception):
    pass


def decrypt(data: str) -> str:
    if not data:
        return data
    try:
        return fernet.decrypt(data.encode()).decode()
    except Exception:
        _logger.error("解密失败，密文损坏或密钥不匹配")
        raise DecryptionError("解密失败，密文损坏或密钥不匹配")
