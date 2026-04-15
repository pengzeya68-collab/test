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
_FALLBACK_KEY = "testmaster-dev-encryption-key-2024"


def _derive_fernet_key(seed: str) -> bytes:
    derived = hashlib.sha256(seed.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(derived)


_KEY_SEED = os.environ.get(_FERNET_KEY_ENV, _FALLBACK_KEY)
KEY = _derive_fernet_key(_KEY_SEED)
fernet = Fernet(KEY)


def encrypt(data: str) -> str:
    if not data:
        return data
    return fernet.encrypt(data.encode()).decode()


def decrypt(data: str) -> str:
    if not data:
        return data
    try:
        return fernet.decrypt(data.encode()).decode()
    except Exception:
        _logger.warning("解密失败，返回原始数据（可能是密钥变更前的密文）")
        return data
