import pytest
import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE = "https://34.150.26.84"


@pytest.fixture(scope="session")
def auth():
    """登录获取token，整个测试会话复用"""
    r = requests.post(f"{BASE}/api/v1/auth/login",
                      json={"username": "testuser", "password": "password123"},
                      verify=False, timeout=10)
    assert r.status_code == 200, f"登录失败: {r.text}"
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture(scope="session")
def admin_auth():
    """管理员登录"""
    r = requests.post(f"{BASE}/api/v1/auth/login",
                      json={"username": "admin", "password": "admin123"},
                      verify=False, timeout=10)
    if r.status_code == 200:
        return {"Authorization": f"Bearer {r.json()['access_token']}"}
    return {}
