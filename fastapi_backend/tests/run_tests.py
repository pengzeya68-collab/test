"""
测试运行脚本
运行所有测试或指定测试
"""
import unittest
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run_all_tests():
    """运行所有测试"""
    # 设置测试环境变量
    os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
    os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-tests"
    os.environ["ENVIRONMENT"] = "testing"

    # 发现并运行测试
    loader = unittest.TestLoader()
    start_dir = os.path.dirname(__file__)
    suite = loader.discover(start_dir, pattern="test_*.py")

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()

def run_specific_test(test_class_name, test_method_name=None):
    """运行特定测试"""
    os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
    os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-tests"
    os.environ["ENVIRONMENT"] = "testing"

    # 导入所有测试模块
    import test_auth
    import test_interview_session
    import test_submission
    import test_sandbox
    import test_ai_evaluation

    # 构建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # 根据参数添加测试
    if test_class_name == "auth":
        suite.addTests(loader.loadTestsFromTestCase(test_auth.TestAuth))
    elif test_class_name == "interview":
        suite.addTests(loader.loadTestsFromTestCase(test_interview_session.TestInterviewSession))
    elif test_class_name == "submission":
        suite.addTests(loader.loadTestsFromTestCase(test_submission.TestSubmission))
    elif test_class_name == "sandbox":
        suite.addTests(loader.loadTestsFromTestCase(test_sandbox.TestSandboxService))
    elif test_class_name == "ai":
        suite.addTests(loader.loadTestsFromTestCase(test_ai_evaluation.TestAITutorService))
    else:
        print(f"未知测试类: {test_class_name}")
        return False

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="运行AI面试后端测试")
    parser.add_argument("--test", type=str, help="运行特定测试类: auth, interview, submission, sandbox, ai")
    parser.add_argument("--method", type=str, help="运行特定测试方法")

    args = parser.parse_args()

    if args.test:
        success = run_specific_test(args.test, args.method)
    else:
        success = run_all_tests()

    sys.exit(0 if success else 1)