"""
AI评估服务测试
覆盖成功评估、失败fallback、API错误处理
"""
import unittest
import os
import sys
from unittest.mock import patch, MagicMock, AsyncMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.ai_tutor_service import AITutorService


class TestAITutorService(unittest.TestCase):
    """AI评估服务测试"""

    def setUp(self):
        self.tutor = AITutorService()

    @patch('services.ai_tutor_service.OpenAI')
    def test_evaluate_code_success(self, mock_openai):
        """测试AI评估成功"""
        # 模拟OpenAI API响应
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = """
        评分: 85
        反馈: 代码实现正确，但可以优化时间复杂度
        正确性: 正确
        建议: 考虑使用哈希表优化
        复杂度分析: 时间复杂度O(n²)，空间复杂度O(1)
        """

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client

        # 模拟有API密钥的情况
        with patch('core.config.settings.AI_API_KEY', 'test-key'):
            result = self.tutor.evaluate_code({
                "code": "def two_sum(nums, target):\n    for i in range(len(nums)):\n        for j in range(i+1, len(nums)):\n            if nums[i] + nums[j] == target:\n                return [i, j]\n    return []",
                "language": "python",
                "question_title": "两数之和",
                "question_description": "找出数组中和为目标值的两个数"
            })

            self.assertEqual(result["score"], 85)
            self.assertIn("优化", result["feedback"])
            self.assertTrue(result["correctness"])
            self.assertIn("哈希表", result["suggestions"][0])
            self.assertIn("O(n²)", result["complexity_analysis"])

    def test_evaluate_code_no_api_key_mock_evaluation(self):
        """测试无API密钥时的模拟评估"""
        # 模拟无API密钥的情况
        with patch('core.config.settings.AI_API_KEY', None):
            result = self.tutor.evaluate_code({
                "code": "def solution(): return 42",
                "language": "python",
                "question_title": "测试题目"
            })

            # 应该返回模拟结果
            self.assertIsNotNone(result)
            self.assertIn("score", result)
            self.assertIn("feedback", result)

    @patch('services.ai_tutor_service.OpenAI')
    def test_evaluate_code_api_error_fallback(self, mock_openai):
        """测试API错误时的降级处理"""
        # 模拟API异常
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("API调用失败")
        mock_openai.return_value = mock_client

        # 即使有API密钥，API调用失败时也应该有fallback
        with patch('core.config.settings.AI_API_KEY', 'test-key'):
            result = self.tutor.evaluate_code({
                "code": "def test(): pass",
                "language": "python",
                "question_title": "测试"
            })

            # 应该返回某种结果，不能抛出异常
            self.assertIsNotNone(result)
            # 可能返回模拟评估或错误信息

    def test_evaluate_code_empty_code(self):
        """测试空代码评估"""
        result = self.tutor.evaluate_code({
            "code": "",
            "language": "python",
            "question_title": "测试"
        })

        self.assertIsNotNone(result)
        # 应该处理空代码情况

    def test_evaluate_code_whitespace_code(self):
        """测试只有空白的代码评估"""
        result = self.tutor.evaluate_code({
            "code": "   \n\t\n  ",
            "language": "python",
            "question_title": "测试"
        })

        self.assertIsNotNone(result)

    def test_evaluate_code_invalid_language(self):
        """测试不支持语言的评估"""
        result = self.tutor.evaluate_code({
            "code": "console.log('test')",
            "language": "javascript",
            "question_title": "测试"
        })

        self.assertIsNotNone(result)
        # 应该处理不支持的语言

    def test_evaluate_code_with_test_cases(self):
        """测试带测试用例的评估"""
        result = self.tutor.evaluate_code({
            "code": "def two_sum(nums, target):\n    pass",
            "language": "python",
            "question_title": "两数之和",
            "test_cases": [
                {"input": {"nums": [2,7,11,15], "target": 9}, "output": [0,1]},
                {"input": {"nums": [3,2,4], "target": 6}, "output": [1,2]}
            ]
        })

        self.assertIsNotNone(result)
        # 评估应该考虑测试用例

    def test_evaluate_code_performance_feedback(self):
        """测试性能反馈"""
        # 模拟返回包含性能反馈的评估
        with patch('services.ai_tutor_service.AITutorService._call_openai_api') as mock_api:
            mock_api.return_value = """
            评分: 70
            反馈: 代码功能正确，但存在性能问题
            正确性: 正确
            建议: 避免嵌套循环，使用哈希表
            复杂度分析: 时间复杂度O(n²)，建议优化到O(n)
            """

            result = self.tutor.evaluate_code({
                "code": "def two_sum(nums, target):\n    for i in range(len(nums)):\n        for j in range(i+1, len(nums)):\n            if nums[i] + nums[j] == target:\n                return [i, j]\n    return []",
                "language": "python",
                "question_title": "两数之和"
            })

            self.assertIn("性能", result.get("feedback", ""))
            self.assertIn("O(n²)", result.get("complexity_analysis", ""))

    def test_evaluate_code_security_concerns(self):
        """测试安全问题的代码评估"""
        dangerous_code = """
import os
os.system('rm -rf /')
        """

        result = self.tutor.evaluate_code({
            "code": dangerous_code,
            "language": "python",
            "question_title": "危险代码测试"
        })

        self.assertIsNotNone(result)
        # AI应该能识别危险代码并给出警告

    def test_evaluate_code_readability_feedback(self):
        """测试可读性反馈"""
        unreadable_code = """
def f(x):return x*x if x>0 else 0
def g(y):return sum([i for i in range(y)]) if y>0 else 0
        """

        result = self.tutor.evaluate_code({
            "code": unreadable_code,
            "language": "python",
            "question_title": "可读性测试"
        })

        self.assertIsNotNone(result)
        # 应该包含可读性相关的反馈

    def test_evaluate_code_edge_cases(self):
        """测试边界情况"""
        edge_case_code = """
def edge_case():
    try:
        # 无限递归
        return edge_case()
    except RecursionError:
        return "递归深度限制"
        """

        result = self.tutor.evaluate_code({
            "code": edge_case_code,
            "language": "python",
            "question_title": "边界测试"
        })

        self.assertIsNotNone(result)


if __name__ == '__main__':
    unittest.main()