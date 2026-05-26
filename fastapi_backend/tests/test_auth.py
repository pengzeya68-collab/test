"""
认证相关测试
覆盖登录、Token刷新、用户信息获取、修改密码
"""
from fastapi_backend.deps.auth import get_auth_service
from fastapi_backend.main import app
from fastapi_backend.models.models import User


class TestAuth:
    """认证功能测试"""

    def test_login_invalid_credentials(self, client):
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "nonexistent", "password": "wrongpassword"}
        )
        assert response.status_code == 401

    def test_get_me_without_token(self, client):
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401

    def test_refresh_token_invalid(self, client):
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid.token.here"}
        )
        assert response.status_code == 401

    def test_change_password_without_token(self, client):
        response = client.post(
            "/api/v1/auth/change-password",
            json={"old_password": "old", "new_password": "new"}
        )
        assert response.status_code == 401

    def test_profile_without_token(self, client):
        response = client.get("/api/v1/auth/profile")
        assert response.status_code == 401

    def test_login_with_mock(self, client):
        mock_user = User(
            id=1,
            username="mockuser",
            email="mock@example.com",
            password_hash="hashed",
            is_active=True,
            is_admin=False,
        )

        class FakeAuthService:
            async def authenticate_user(self, db, username, password):
                return mock_user

            async def migrate_password_if_needed(self, db, user, password):
                return True

            def create_token_pair(self, user):
                return {
                    "access_token": "test_access_token",
                    "refresh_token": "test_refresh_token",
                    "token_type": "bearer",
                    "expires_in": 3600,
                    "user": {
                        "id": 1,
                        "username": "mockuser",
                        "email": "mock@example.com",
                        "phone": None,
                        "is_active": True,
                        "is_admin": False,
                        "role": "user",
                        "avatar": None,
                        "level": 0,
                        "score": 0,
                        "study_time": 0,
                        "created_at": None,
                    },
                }

        app.dependency_overrides[get_auth_service] = lambda: FakeAuthService()

        response = client.post(
            "/api/v1/auth/login",
            json={"username": "mockuser", "password": "mockpass"}
        )
        assert response.status_code == 200
        app.dependency_overrides.pop(get_auth_service, None)


class TestAssessment:
    """入学测评API测试"""

    def test_get_questions_without_token(self, client):
        response = client.get("/api/v1/assessment/questions")
        assert response.status_code == 401

    def test_submit_without_token(self, client):
        response = client.post(
            "/api/v1/assessment/submit",
            json={"answers": []}
        )
        assert response.status_code == 401

    def test_status_without_token(self, client):
        response = client.get("/api/v1/assessment/status")
        assert response.status_code == 401


class TestSkills:
    """技能API测试"""

    def test_radar_without_token(self, client):
        response = client.get("/api/v1/skills/radar")
        assert response.status_code == 401

    def test_progress_without_token(self, client):
        response = client.get("/api/v1/skills/progress")
        assert response.status_code == 401


class TestExercise:
    """练习API测试"""

    def test_submit_without_token(self, client):
        response = client.post(
            "/api/v1/exercise/submit",
            json={"exercise_id": 1, "solution": "print('hello')"}
        )
        assert response.status_code == 401

    def test_evaluate_without_token(self, client):
        response = client.post(
            "/api/v1/exercise/evaluate",
            json={"exercise_id": 1, "language": "python", "source_code": "print('hello')"}
        )
        assert response.status_code in [401, 422]


class TestInterview:
    """面试API测试"""

    def test_questions_without_token(self, client):
        response = client.get("/api/v1/interview/questions")
        assert response.status_code == 401

    def test_follow_up_without_token(self, client):
        response = client.post(
            "/api/v1/interview/follow-up",
            json={"question_title": "test", "user_answer": "test"}
        )
        assert response.status_code == 401

    def test_statistics_without_token(self, client):
        response = client.get("/api/v1/interview/statistics")
        assert response.status_code == 401
