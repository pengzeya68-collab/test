"""
认证相关测试
覆盖登录、Token刷新、用户信息获取、修改密码
"""
import unittest
import os
import sys
from unittest.mock import patch, AsyncMock, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestAuth(unittest.TestCase):
    """认证功能测试"""

    def test_login_invalid_credentials(self):
        """测试无效凭据登录应返回401"""
        from fastapi.testclient import TestClient
        from main import app
        client = TestClient(app)
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "nonexistent", "password": "wrongpassword"}
        )
        self.assertEqual(response.status_code, 401)

    def test_get_me_without_token(self):
        """测试无Token获取用户信息应返回401"""
        from fastapi.testclient import TestClient
        from main import app
        client = TestClient(app)
        response = client.get("/api/v1/auth/me")
        self.assertEqual(response.status_code, 401)

    def test_refresh_token_invalid(self):
        """测试无效的刷新Token应返回401"""
        from fastapi.testclient import TestClient
        from main import app
        client = TestClient(app)
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid.token.here"}
        )
        self.assertEqual(response.status_code, 401)

    def test_change_password_without_token(self):
        """测试无Token修改密码应返回401"""
        from fastapi.testclient import TestClient
        from main import app
        client = TestClient(app)
        response = client.post(
            "/api/v1/auth/change-password",
            json={"old_password": "old", "new_password": "new"}
        )
        self.assertEqual(response.status_code, 401)

    def test_profile_without_token(self):
        """测试无Token获取个人信息应返回401"""
        from fastapi.testclient import TestClient
        from main import app
        client = TestClient(app)
        response = client.get("/api/v1/auth/profile")
        self.assertEqual(response.status_code, 401)

    @patch('services.auth_service.AuthService.authenticate_user', new_callable=AsyncMock)
    @patch('services.auth_service.AuthService.create_token_pair')
    def test_login_with_mock(self, mock_create_token, mock_authenticate):
        """使用Mock测试登录成功"""
        from models.models import User
        mock_user = User(
            id=1, username="mockuser", email="mock@example.com",
            password_hash="hashed", is_active=True, is_admin=False
        )
        mock_authenticate.return_value = mock_user
        mock_create_token.return_value = {
            "access_token": "test_access_token",
            "refresh_token": "test_refresh_token",
            "token_type": "bearer",
            "expires_in": 3600,
            "user": {"id": 1, "username": "mockuser", "email": "mock@example.com"}
        }

        from fastapi.testclient import TestClient
        from main import app
        client = TestClient(app)
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "mockuser", "password": "mockpass"}
        )
        self.assertEqual(response.status_code, 200)


class TestAssessment(unittest.TestCase):
    """入学测评API测试"""

    def test_get_questions_without_token(self):
        """测试无Token获取测评题目应返回401"""
        from fastapi.testclient import TestClient
        from main import app
        client = TestClient(app)
        response = client.get("/api/v1/assessment/questions")
        self.assertEqual(response.status_code, 401)

    def test_submit_without_token(self):
        """测试无Token提交测评应返回401"""
        from fastapi.testclient import TestClient
        from main import app
        client = TestClient(app)
        response = client.post(
            "/api/v1/assessment/submit",
            json={"answers": []}
        )
        self.assertEqual(response.status_code, 401)

    def test_status_without_token(self):
        """测试无Token获取测评状态应返回401"""
        from fastapi.testclient import TestClient
        from main import app
        client = TestClient(app)
        response = client.get("/api/v1/assessment/status")
        self.assertEqual(response.status_code, 401)


class TestSkills(unittest.TestCase):
    """技能API测试"""

    def test_radar_without_token(self):
        """测试无Token获取技能雷达应返回401"""
        from fastapi.testclient import TestClient
        from main import app
        client = TestClient(app)
        response = client.get("/api/v1/skills/radar")
        self.assertEqual(response.status_code, 401)

    def test_progress_without_token(self):
        """测试无Token获取技能进度应返回401"""
        from fastapi.testclient import TestClient
        from main import app
        client = TestClient(app)
        response = client.get("/api/v1/skills/progress")
        self.assertEqual(response.status_code, 401)


class TestExercise(unittest.TestCase):
    """练习API测试"""

    def test_submit_without_token(self):
        """测试无Token提交练习应返回401"""
        from fastapi.testclient import TestClient
        from main import app
        client = TestClient(app)
        response = client.post(
            "/api/v1/exercise/submit",
            json={"exercise_id": 1, "solution": "print('hello')"}
        )
        self.assertEqual(response.status_code, 401)

    def test_evaluate_without_token(self):
        """测试无Token评估代码应返回422（缺少认证）"""
        from fastapi.testclient import TestClient
        from main import app
        client = TestClient(app)
        response = client.post(
            "/api/v1/exercise/evaluate",
            json={"exercise_id": 1, "language": "python", "source_code": "print('hello')"}
        )
        self.assertIn(response.status_code, [401, 422])


class TestInterview(unittest.TestCase):
    """面试API测试"""

    def test_questions_without_token(self):
        """测试无Token获取面试题目应返回401"""
        from fastapi.testclient import TestClient
        from main import app
        client = TestClient(app)
        response = client.get("/api/v1/interview/questions")
        self.assertEqual(response.status_code, 401)

    def test_follow_up_without_token(self):
        """测试无Token获取追问应返回401"""
        from fastapi.testclient import TestClient
        from main import app
        client = TestClient(app)
        response = client.post(
            "/api/v1/interview/follow-up",
            json={"question_title": "test", "user_answer": "test"}
        )
        self.assertEqual(response.status_code, 401)

    def test_statistics_without_token(self):
        """测试无Token获取面试统计应返回401"""
        from fastapi.testclient import TestClient
        from main import app
        client = TestClient(app)
        response = client.get("/api/v1/interview/statistics")
        self.assertEqual(response.status_code, 401)


if __name__ == '__main__':
    unittest.main()
