"""
面试会话相关测试
"""
import unittest
import os
import sys
from unittest.mock import patch, MagicMock, AsyncMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from main import app


class TestInterviewSession(unittest.TestCase):
    """面试会话测试"""

    def setUp(self):
        self.client = TestClient(app)
        self.headers = {"Authorization": "Bearer mock.token"}
        self.user_id = 1
        self.question_id = 100

    @patch('routers.interview.get_current_active_user')
    @patch('routers.interview.get_db')
    def test_create_session_success(self, mock_get_db, mock_get_user):
        """测试成功创建面试会话"""
        # Mock当前用户
        from models.models import User
        mock_user = User(
            id=self.user_id,
            username="testuser",
            email="test@example.com",
            is_active=True,
            is_admin=False
        )
        mock_get_user.return_value = mock_user

        # Mock数据库会话
        mock_db = AsyncMock()
        mock_get_db.return_value = mock_db

        # Mock题目查询 - 题目存在且已发布
        from models.models import InterviewQuestion
        mock_question = InterviewQuestion(
            id=self.question_id,
            title="测试题目",
            is_published=True
        )

        # Mock查询执行
        mock_scalar = MagicMock()
        mock_scalar.scalar_one_or_none.return_value = mock_question
        mock_db.execute.return_value = mock_scalar

        # Mock活跃会话查询 - 没有活跃会话
        mock_scalar2 = MagicMock()
        mock_scalar2.scalar_one_or_none.return_value = None
        mock_db.execute.side_effect = [mock_scalar, mock_scalar2]

        # 调用创建会话接口
        response = self.client.post(
            "/api/v1/interview/sessions",
            json={"question_id": self.question_id},
            headers=self.headers
        )

        # 验证响应
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["code"], 200)
        self.assertIn("data", data)
        self.assertIn("id", data["data"])

    @patch('routers.interview.get_current_active_user')
    @patch('routers.interview.get_db')
    def test_create_session_existing_active(self, mock_get_db, mock_get_user):
        """测试存在活跃会话时返回现有会话"""
        # Mock当前用户
        from models.models import User
        mock_user = User(
            id=self.user_id,
            username="testuser",
            email="test@example.com",
            is_active=True,
            is_admin=False
        )
        mock_get_user.return_value = mock_user

        # Mock数据库会话
        mock_db = AsyncMock()
        mock_get_db.return_value = mock_db

        # Mock题目查询
        from models.models import InterviewQuestion
        mock_question = InterviewQuestion(
            id=self.question_id,
            title="测试题目",
            is_published=True
        )

        # Mock活跃会话查询 - 存在活跃会话
        from models.models import InterviewSession
        mock_session = InterviewSession(
            id=50,
            user_id=self.user_id,
            question_id=self.question_id,
            status="started"
        )

        mock_scalar = MagicMock()
        mock_scalar.scalar_one_or_none.return_value = mock_question

        mock_scalar2 = MagicMock()
        mock_scalar2.scalar_one_or_none.return_value = mock_session

        mock_db.execute.side_effect = [mock_scalar, mock_scalar2]

        # 调用创建会话接口
        response = self.client.post(
            "/api/v1/interview/sessions",
            json={"question_id": self.question_id},
            headers=self.headers
        )

        # 应该返回现有会话
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["code"], 200)
        self.assertEqual(data["data"]["id"], 50)

    @patch('routers.interview.get_current_active_user')
    @patch('routers.interview.get_db')
    def test_create_session_question_not_found(self, mock_get_db, mock_get_user):
        """测试题目不存在时创建会话失败"""
        # Mock当前用户
        from models.models import User
        mock_user = User(
            id=self.user_id,
            username="testuser",
            email="test@example.com",
            is_active=True,
            is_admin=False
        )
        mock_get_user.return_value = mock_user

        # Mock数据库会话
        mock_db = AsyncMock()
        mock_get_db.return_value = mock_db

        # Mock题目查询 - 题目不存在
        mock_scalar = MagicMock()
        mock_scalar.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_scalar

        # 调用创建会话接口
        response = self.client.post(
            "/api/v1/interview/sessions",
            json={"question_id": 999},  # 不存在的题目ID
            headers=self.headers
        )

        # 验证响应 - 应该返回404
        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertEqual(data["code"], 404)

    def test_create_session_without_auth(self):
        """测试未认证用户创建会话失败"""
        response = self.client.post(
            "/api/v1/interview/sessions",
            json={"question_id": self.question_id}
            # 不提供Authorization头
        )
        self.assertEqual(response.status_code, 401)

    @patch('routers.interview.get_current_active_user')
    @patch('routers.interview.get_db')
    def test_list_my_sessions(self, mock_get_db, mock_get_user):
        """测试获取我的会话列表"""
        # Mock当前用户
        from models.models import User
        mock_user = User(
            id=self.user_id,
            username="testuser",
            email="test@example.com",
            is_active=True,
            is_admin=False
        )
        mock_get_user.return_value = mock_user

        # Mock数据库会话
        mock_db = AsyncMock()
        mock_get_db.return_value = mock_db

        # Mock查询结果
        from models.models import InterviewSession, InterviewQuestion
        mock_session = InterviewSession(
            id=1,
            user_id=self.user_id,
            question_id=self.question_id,
            status="started"
        )
        mock_question_title = "测试题目"
        mock_question_difficulty = "easy"

        mock_result = MagicMock()
        mock_result.all.return_value = [
            (mock_session, mock_question_title, mock_question_difficulty)
        ]

        mock_count_result = MagicMock()
        mock_count_result.scalar_one.return_value = 1

        mock_db.execute.side_effect = [mock_count_result, mock_result]

        # 调用获取会话列表接口
        response = self.client.get(
            "/api/v1/interview/sessions",
            headers=self.headers
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["code"], 200)
        self.assertIn("data", data)
        self.assertIn("items", data["data"])
        self.assertEqual(len(data["data"]["items"]), 1)


if __name__ == '__main__':
    unittest.main()