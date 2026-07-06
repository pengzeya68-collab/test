import os
from urllib.parse import urljoin

import pytest
import requests
import urllib3


def _env_bool(name, default=True):
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@pytest.fixture(scope="session")
def remote_base_url():
    base_url = os.getenv("TESTMASTER_REMOTE_BASE_URL")
    if not base_url:
        pytest.skip("设置 TESTMASTER_REMOTE_BASE_URL 后才会执行远程回归测试")
    return base_url.rstrip("/")


@pytest.fixture(scope="session")
def remote_timeout():
    return float(os.getenv("TESTMASTER_REMOTE_TIMEOUT", "15"))


@pytest.fixture(scope="session")
def remote_verify_tls():
    verify = _env_bool("TESTMASTER_REMOTE_VERIFY_TLS", True)
    if not verify:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    return verify


@pytest.fixture(scope="session")
def remote_session(remote_verify_tls):
    session = requests.Session()
    session.verify = remote_verify_tls
    return session


@pytest.fixture(scope="session")
def remote_request(remote_base_url, remote_session, remote_timeout):
    def request(method, path, headers=None, **kwargs):
        url = urljoin(f"{remote_base_url}/", path.lstrip("/"))
        kwargs.setdefault("timeout", remote_timeout)
        return getattr(remote_session, method.lower())(url, headers=headers, **kwargs)

    return request


def _login(remote_request, username_env, password_env, label, required=True):
    username = os.getenv(username_env)
    password = os.getenv(password_env)
    if not username or not password:
        if required:
            pytest.skip(f"设置 {username_env} 和 {password_env} 后才会执行需要{label}登录的远程测试")
        return {}

    response = remote_request(
        "post",
        "/api/v1/auth/login",
        json={"username": username, "password": password},
    )
    assert response.status_code == 200, f"{label}登录失败: {response.text}"
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.fixture(scope="session")
def auth(remote_request):
    """登录获取普通用户 token，整个测试会话复用。"""
    return _login(
        remote_request,
        "TESTMASTER_REMOTE_USER",
        "TESTMASTER_REMOTE_PASSWORD",
        "普通用户",
    )


@pytest.fixture(scope="session")
def admin_auth(remote_request):
    """登录获取管理员 token；未配置管理员账号时返回空 header。"""
    return _login(
        remote_request,
        "TESTMASTER_REMOTE_ADMIN_USER",
        "TESTMASTER_REMOTE_ADMIN_PASSWORD",
        "管理员",
        required=False,
    )


@pytest.fixture
def api(remote_request):
    """统一远程 API 调用。"""
    return remote_request
