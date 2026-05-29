"""
面试模拟主链路测试
使用 app.dependency_overrides 而非 patch，确保鉴权替换稳定
"""

from fastapi_backend.main import app
from fastapi_backend.deps.auth import get_current_active_user
from fastapi_backend.models.models import User


async def _mock_user():
    return User(
        id=1,
        username="testuser",
        email="test@test.com",
        password_hash="hash",
        is_active=True,
        is_admin=False,
    )


class TestInterviewFlow:
    """面试主链路测试"""

    def test_create_session_without_auth(self, client):
        """未认证：POST /sessions → 401"""
        response = client.post(
            "/api/v1/interview/sessions",
            json={"difficulty": "medium", "category": "technical", "question_count": 5},
        )
        assert response.status_code == 401

    def test_get_questions_without_auth(self, client):
        """未认证：GET /questions → 401"""
        response = client.get("/api/v1/interview/questions")
        assert response.status_code == 401

    def test_submit_answer_without_auth(self, client):
        """未认证：不存在的 answer 路由应返回 404。"""
        response = client.post(
            "/api/v1/interview/answer",
            json={"session_id": 1, "question_id": 1, "answer": "test"},
        )
        assert response.status_code == 404

    def test_get_statistics_without_auth(self, client):
        """未认证：GET /statistics → 401"""
        response = client.get("/api/v1/interview/statistics")
        assert response.status_code == 401

    def test_create_session_with_auth(self, client):
        """认证用户：缺少 question_id 时应返回 422。"""
        app.dependency_overrides[get_current_active_user] = _mock_user
        try:
            response = client.post(
                "/api/v1/interview/sessions",
                json={
                    "difficulty": "medium",
                    "category": "technical",
                    "question_count": 5,
                },
            )
            assert response.status_code == 422
        finally:
            app.dependency_overrides.pop(get_current_active_user, None)

    def test_get_profile_with_auth(self, client):
        """认证用户：未实现的 profile 路由应返回 404。"""
        app.dependency_overrides[get_current_active_user] = _mock_user
        try:
            response = client.get("/api/v1/interview/profile")
            assert response.status_code == 404
        finally:
            app.dependency_overrides.pop(get_current_active_user, None)
