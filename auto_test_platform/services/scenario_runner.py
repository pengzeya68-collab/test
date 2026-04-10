"""
场景执行引擎
核心逻辑：按顺序执行场景中的每个步骤，通过全局上下文传递变量
"""
import asyncio
import json
import subprocess
import time
import uuid
import httpx
from pathlib import Path
from typing import Dict, Any, List, Optional
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from auto_test_platform.database import async_session
from auto_test_platform.models import TestScenario, ScenarioStep, ApiCase, Environment, ScenarioExecutionRecord
from auto_test_platform.utils.email_notifier import get_email_notifier
from auto_test_platform.utils.parser import replace_variables


class ScenarioExecutionEngine:
    """
    场景执行引擎

    核心概念：
    - context_vars: 全局上下文字典，存储提取的变量（如 token）
    - 每一步执行完后，其 Extractors 提取的变量存入 context_vars
    - 下一步构造请求时，通过 replace_variables 自动从 context_vars 读取变量
    """

    def __init__(self, scenario_id: int, env_id: Optional[int] = None):
        self.scenario_id = scenario_id
        self.env_id = env_id
        self.context_vars: Dict[str, Any] = {}  # 全局上下文
        self.step_results: List[Dict[str, Any]] = []
        self.total_duration = 0
        self.base_url: str = ""  # 基础 URL，用于拼接相对路径

    async def execute(self) -> Dict[str, Any]:
        """
        执行整个场景
        返回执行结果（包含完整的步骤列表和 Allure 报告链接）
        """
        start_time = time.time()
        report_url = None
        scenario_name = ""

        # ========== 核心执行逻辑 ==========
        try:
            async with async_session() as db:
                # 加载场景及其步骤
                result = await db.execute(
                    select(TestScenario)
                    .options(selectinload(TestScenario.steps).selectinload(ScenarioStep.api_case))
                    .where(TestScenario.id == self.scenario_id)
                )
                scenario = result.scalar_one_or_none()
                if not scenario:
                    raise ValueError(f"场景 {self.scenario_id} 不存在")

                scenario_name = scenario.name

                # 加载环境变量
                env_config = {}
                env = None
                if self.env_id:
                    result = await db.execute(
                        select(Environment).where(Environment.id == self.env_id)
                    )
                    env = result.scalar_one_or_none()
                else:
                    # 获取默认环境
                    result = await db.execute(
                        select(Environment).where(Environment.is_default == True)
                    )
                    env = result.scalar_one_or_none()
                    if not env:
                        # 获取第一个环境
                        result = await db.execute(select(Environment))
                        env = result.scalars().first()
                
                if env:
                    self.context_vars.update(env.variables or {})
                    # 如果 URL 不是以 http 开头，尝试使用 base_url
                    if env.base_url:
                        self.base_url = env.base_url
                        # 将 base_url 添加到 context_vars，供变量替换使用
                        self.context_vars["base_url"] = env.base_url

                # 获取所有启用的步骤并排序
                all_steps = sorted([s for s in scenario.steps if s.is_active], key=lambda x: x.step_order)
                total_active_steps = len(all_steps)

                # ========== 使用 has_failed 标志位，确保所有步骤都被处理（完全按照骨架）==========
                has_failed = False
                failed_step_index = None

                for idx, step in enumerate(all_steps):
                    # 1. 如果前面已经有步骤失败了，后面的步骤直接标记为跳过，不发请求
                    if has_failed:
                        self.step_results.append({
                            "step_id": step.id,
                            "step_order": step.step_order,
                            "api_case_id": step.api_case_id,
                            "api_case_name": step.api_case.name if step.api_case else f"Step {step.step_order}",
                            "method": step.api_case.method if step.api_case else "GET",
                            "success": True,
                            "status": "skipped",
                            "response_time": 0,
                            "error": None,
                            "skipped_reason": f"因 Step {failed_step_index + 1} 失败而跳过"
                        })
                        continue

                    # 2. 正常执行当前步骤
                    try:
                        step_result = await self._execute_step(db, step)

                        if not step_result.get("success", False):
                            # 3. 步骤报错，设置失败标志位
                            step_result["status"] = "failed"
                            self.step_results.append(step_result)
                            self.total_duration += step_result.get("duration", 0)
                            has_failed = True
                            failed_step_index = idx
                        else:
                            step_result["status"] = "success"
                            self.step_results.append(step_result)
                            self.total_duration += step_result.get("duration", 0)

                    except AssertionError as e:
                        # 断言失败，设置失败标志位
                        step_duration = int((time.time() - start_time) * 1000)
                        self.step_results.append({
                            "step_id": step.id,
                            "step_order": step.step_order,
                            "api_case_id": step.api_case_id,
                            "api_case_name": step.api_case.name if step.api_case else f"Step {step.step_order}",
                            "method": step.api_case.method if step.api_case else "GET",
                            "success": False,
                            "status": "failed",
                            "response_time": step_duration,
                            "error": f"断言失败: {str(e)}"
                        })
                        has_failed = True
                        failed_step_index = idx

                    except Exception as e:
                        # 其他异常，设置失败标志位
                        step_duration = int((time.time() - start_time) * 1000)
                        self.step_results.append({
                            "step_id": step.id,
                            "step_order": step.step_order,
                            "api_case_id": step.api_case_id,
                            "api_case_name": step.api_case.method if step.api_case else "GET",
                            "success": False,
                            "status": "failed",
                            "response_time": step_duration,
                            "error": f"执行异常: {str(e)}"
                        })
                        has_failed = True
                        failed_step_index = idx

        finally:
            # ========== Bug2 修复：强制生成报告（通过 pytest + allure）==========
            overall_duration = int((time.time() - start_time) * 1000)

            base_dir = Path(__file__).parent.parent.absolute()
            temp_pytest_dir = base_dir / "temp_pytest_tests"
            allure_results_dir = base_dir / "allure-results" / f"scenario_{self.scenario_id}"
            report_dir = base_dir / "reports" / f"scenario_{self.scenario_id}"

            temp_pytest_dir.mkdir(parents=True, exist_ok=True)
            allure_results_dir.mkdir(parents=True, exist_ok=True)
            report_dir.mkdir(parents=True, exist_ok=True)

            history_id = str(uuid.uuid4())[:8]

            # Step 1: 动态生成 pytest 测试文件
            test_file_path = self._generate_pytest_test_file(temp_pytest_dir, scenario_name, history_id)

            # Step 2: 执行 pytest 生成 allure-results
            pytest_success = self._run_pytest_and_generate_report(
                test_file_path,
                str(allure_results_dir),
                str(report_dir)
            )

            # 检查报告是否生成成功
            index_html = report_dir / "index.html"
            if index_html.exists():
                report_url = f"/reports/scenario_{self.scenario_id}/index.html"
                print(f"[ScenarioExecutionEngine] Allure 报告生成成功: {report_url}")
            else:
                report_url = None
                print(f"[ScenarioExecutionEngine] Allure 报告生成失败，index.html 不存在")

        # ========== 基于 step_results 动态统计 ==========
        total_steps = len(self.step_results)
        success_steps = len([r for r in self.step_results if r.get("status") == "success"])
        failed_steps = len([r for r in self.step_results if r.get("status") == "failed"])
        skipped_steps = len([r for r in self.step_results if r.get("status") == "skipped"])

        print(f"[ScenarioExecutionEngine] 执行完成: 总步骤={total_steps}, 成功={success_steps}, 失败={failed_steps}, 跳过={skipped_steps}, report_url={report_url}")

        # ========== 第一步：保存执行记录到数据库 ==========
        from sqlalchemy.ext.asyncio import AsyncSession
        async with async_session() as db:
            # 判断整体状态
            if failed_steps > 0:
                status = "failed"
            elif success_steps == total_steps:
                status = "success"
            else:
                status = "error"

            record = ScenarioExecutionRecord(
                scenario_id=self.scenario_id,
                status=status,
                total_steps=total_steps,
                failed_steps=failed_steps,
                success_steps=success_steps,
                skipped_steps=skipped_steps,
                total_time=overall_duration,
                report_url=report_url
            )
            db.add(record)
            await db.commit()
            await db.refresh(record)
            print(f"[ScenarioExecutionEngine] 执行记录已保存到数据库，ID: {record.id}")

        # ========== 第二步：发送邮件通知（异步，不阻塞执行） ==========
        import auto_test_platform.settings as settings
        admin_email = getattr(settings, "EMAIL_ADMIN_TO", None)
        if admin_email and report_url:
            notifier = get_email_notifier()
            # 使用 asyncio.create_task 异步发送，不阻塞执行
            asyncio.create_task(
                notifier.send_scenario_result(
                    to_email=admin_email,
                    scenario_name=scenario_name,
                    scenario_id=self.scenario_id,
                    status=status,
                    total_steps=total_steps,
                    success_steps=success_steps,
                    failed_steps=failed_steps,
                    skipped_steps=skipped_steps,
                    total_time=overall_duration,
                    report_url=report_url,
                    base_url=getattr(settings, "BASE_URL", "")
                )
            )

        return {
            "scenario_id": self.scenario_id,
            "scenario_name": scenario_name,
            "total_steps": total_steps,
            "success_count": success_steps,
            "failed_count": failed_steps,
            "skipped_count": skipped_steps,
            "total_time": overall_duration,
            "context_vars": self.context_vars,
            "step_results": self.step_results,
            "report_url": report_url,
            "execution_record_id": record.id if 'record' in locals() else None
        }

    def _generate_pytest_test_file(self, temp_dir: Path, scenario_name: str, history_id: str) -> Path:
        """
        Bug2 修复：动态生成 pytest 测试文件

        Allure 需要通过 pytest 执行测试才能正确生成报告结构。
        因此我们动态生成 test_xxx.py 文件，然后通过 pytest 执行。
        """
        test_filename = f"test_scenario_{self.scenario_id}_{history_id}.py"
        test_file_path = temp_dir / test_filename

        # 构建测试用例代码
        test_code = self._build_pytest_test_code(scenario_name, history_id)

        with open(test_file_path, "w", encoding="utf-8") as f:
            f.write(test_code)

        print(f"[ScenarioExecutionEngine] 动态生成 pytest 测试文件: {test_file_path}")
        return test_file_path

    def _build_pytest_test_code(self, scenario_name: str, history_id: str) -> str:
        """
        构建 pytest 测试代码
        每个步骤对应一个 test function
        """
        test_functions = []

        for i, step in enumerate(self.step_results):
            i_plus_1 = i + 1
            step_name = step.get("api_case_name", f"步骤 {i+1}")
            method = step.get("method", "GET")
            url = step.get("url", "")
            headers = step.get("headers", {})
            payload = step.get("payload", {})
            status_code = step.get("status_code", 0)
            response_time = step.get("response_time", 0)
            success = step.get("success", False)
            error = step.get("error", "")

            response_data = step.get("response", {})
            response_body = response_data.get("body", "")

            # 处理断言信息
            assertions = step.get("assertions", {})
            failed_assertions = assertions.get("failed", [])
            passed_assertions = assertions.get("passed", 0)
            total_assertions = assertions.get("total", 0)

            # 构建断言失败消息
            assert_messages = []
            for fa in failed_assertions:
                if isinstance(fa, dict):
                    reason = fa.get("reason", str(fa))
                    assert_messages.append(reason)
                else:
                    assert_messages.append(str(fa))

            # 根据步骤状态决定 pytest 的 assert 语句
            if success:
                # 成功的步骤：使用 assert True（但 Allure 会记录为 passed）
                test_func = '''@allure.feature("{scenario_name}")
@allure.story("{step_name}")
@allure.title("测试步骤: {step_name}")
def test_step_{i_plus_1}_{step_id}(shared_ctx):
    """[{method}] {step_name} - HTTP {status_code}"""
    # 步骤 {i_plus_1}: {step_name}
    # URL: {url}
    # 状态码: {status_code}
    # 响应时间: {response_time}ms
    # 断言结果: {passed_assertions}/{total_assertions} 通过

    # 请求信息
    shared_ctx["steps"].append({{
        "name": "[{method}] {step_name}",
        "status": "passed",
        "status_code": {status_code},
        "response_time": {response_time},
        "url": "{url}"
    }})

    # 1. 发起 HTTP 请求 - 记录请求信息
    with allure.step("1. 发起HTTP请求: {method} {url}"):
        # 附加请求信息
        request_info = {{
            "url": "{url}",
            "method": "{method}",
            "headers": {headers},
            "payload": {payload}
        }}
        allure.attach(
            json.dumps(request_info, ensure_ascii=False, indent=2),
            name="请求信息",
            attachment_type=allure.attachment_type.JSON
        )

        # 这里实际请求已经在场景引擎中执行过了，这里只是为了 Allure 报告记录占位
        # 状态码和响应信息已经提前获取
        pass

    # 2. 记录响应信息
    status_code = {status_code}
    response_time_ms = {response_time}
    response_body = {response_body_quoted}
    with allure.step("2. 获取响应信息"):
        response_info = {{
            "status_code": status_code,
            "response_time_ms": response_time_ms,
            "body": response_body
        }}
        allure.attach(
            json.dumps(response_info, ensure_ascii=False, indent=2),
            name="响应信息",
            attachment_type=allure.attachment_type.JSON
        )

    # 对于成功的步骤，Allure 自动记录为 passed
    assert True, "步骤执行成功"
'''.format(
    i_plus_1=i_plus_1,
    step_id=step.get("step_id", i),
    scenario_name=scenario_name,
    step_name=step_name,
    method=method,
    url=url,
    headers=json.dumps(headers, ensure_ascii=False),
    payload=json.dumps(payload, ensure_ascii=False),
    status_code=status_code,
    response_time=response_time,
    response_body_quoted=json.dumps(response_body[:2000] if response_body else "", ensure_ascii=False),
    passed_assertions=passed_assertions,
    total_assertions=total_assertions
)
            else:
                # 失败的步骤：使用 assert False 并附带详细错误信息
                error_msg = error or "; ".join(assert_messages) or f"期望 2xx/3xx, 实际返回 {status_code}"
                error_msg_escaped = error_msg.replace('"', '\\"').replace('\n', ' ')

                test_func = '''@allure.feature("{scenario_name}")
@allure.story("{step_name}")
@allure.title("测试步骤: {step_name}")
def test_step_{i_plus_1}_{step_id}(shared_ctx):
    """[{method}] {step_name} - HTTP {status_code}"""
    # 步骤 {i_plus_1}: {step_name}
    # URL: {url}
    # 状态码: {status_code}
    # 响应时间: {response_time}ms
    # 断言结果: {passed_assertions}/{total_assertions} 通过

    # 请求信息
    shared_ctx["steps"].append({{
        "name": "[{method}] {step_name}",
        "status": "failed",
        "status_code": {status_code},
        "response_time": {response_time},
        "url": "{url}",
        "error": "{error_msg_escaped}"
    }})

    # 1. 发起 HTTP 请求 - 记录请求信息
    with allure.step("1. 发起HTTP请求: {method} {url}"):
        # 附加请求信息
        request_info = {{
            "url": "{url}",
            "method": "{method}",
            "headers": {headers},
            "payload": {payload}
        }}
        allure.attach(
            json.dumps(request_info, ensure_ascii=False, indent=2),
            name="请求信息",
            attachment_type=allure.attachment_type.JSON
        )
        pass

    # 2. 记录响应信息
    status_code = {status_code}
    response_time_ms = {response_time}
    response_body = {response_body_quoted}
    with allure.step("2. 获取响应信息"):
        response_info = {{
            "status_code": status_code,
            "response_time_ms": response_time_ms,
            "body": response_body
        }}
        allure.attach(
            json.dumps(response_info, ensure_ascii=False, indent=2),
            name="响应信息",
            attachment_type=allure.attachment_type.JSON
        )

    # 3. 执行断言校验
    with allure.step("3. 执行断言校验"):
        # Allure 会将此步骤记录为 failed
        assert False, "步骤执行失败: {error_msg_escaped}"
'''.format(
    i_plus_1=i_plus_1,
    step_id=step.get("step_id", i),
    scenario_name=scenario_name,
    step_name=step_name,
    method=method,
    url=url,
    headers=json.dumps(headers, ensure_ascii=False),
    payload=json.dumps(payload, ensure_ascii=False),
    status_code=status_code,
    response_time=response_time,
    response_body_quoted=json.dumps(response_body[:2000] if response_body else "", ensure_ascii=False),
    passed_assertions=passed_assertions,
    total_assertions=total_assertions,
    error_msg_escaped=error_msg_escaped
)
            test_functions.append(test_func)

        # 合并所有测试函数
        test_code = '''
"""
场景测试自动生成文件
Scenario: {scenario_name}
Scenario ID: {scenario_id}
History ID: {history_id}
Total Steps: {len_steps}
"""
import pytest
import sys
import allure
import json
import time

# 共享数据容器
@pytest.fixture(scope="session")
def shared_ctx():
    """共享上下文容器（避免和 pytest 内置 request 重名）"""
    return {{"steps": []}}

# 生成 environment.properties 文件（Allure 环境信息）
@pytest.fixture(scope="session", autouse=True)
def write_allure_environment(request):
    """写入 Allure 环境信息文件"""
    import sys
    from pathlib import Path

    allure_dir = request.config.getoption("--alluredir")
    if allure_dir:
        env_file = Path(allure_dir) / "environment.properties"
        with open(env_file, "w", encoding="utf-8") as f:
            f.write("Platform=TestMaster_AutoTest\\n")
            f.write("Python_Version=" + sys.version.split()[0] + "\\n")
            f.write("Scenario_ID={scenario_id}\\n")
            f.write("Scenario_Name={scenario_name}\\n")
            f.write("History_ID={history_id}\\n")
            f.write("Total_Steps={len_steps}\\n")
    yield

# 场景级别的前置和后置
@pytest.fixture(scope="session", autouse=True)
def scenario_setup_teardown():
    """场景级别的 setup 和 teardown"""
    print("\\n[ScenarioExecutionEngine] 开始执行场景: {{scenario_name}}")
    yield
    print("\\n[ScenarioExecutionEngine] 场景执行完成")

# 动态生成测试函数
{test_functions_joined}

# 汇总测试结果
def test_scenario_summary(request):
    """场景执行汇总"""
    steps = request.node.session.config.cache.get("steps", [])
    total = len(request.node.session.config.cache.get("step_results", []))
    passed = len([s for s in request.node.session.config.cache.get("step_results", []) if s.get("status") == "success"])
    failed = len([s for s in request.node.session.config.cache.get("step_results", []) if s.get("status") == "failed"])

    print(f"\\n[Summary] Total: {{total}}, Passed: {{passed}}, Failed: {{failed}}")

    # 最终汇总断言：只要有失败的步骤，整体就失败
    has_failed = any(s.get("status") == "failed" for s in request.node.session.config.cache.get("step_results", []))
    assert not has_failed, "场景执行存在失败的步骤"
'''.format(
    scenario_name=scenario_name,
    scenario_id=self.scenario_id,
    history_id=history_id,
    len_steps=len(self.step_results),
    test_functions_joined='\n'.join(test_functions)
)
        return test_code

    def _run_pytest_and_generate_report(self, test_file_path: Path, allure_results_dir: str, report_dir: str) -> bool:
        """
        Bug2 修复：执行 pytest 生成 Allure 报告

        正确的链路：
        1. subprocess.run(['pytest', 'test_xxx.py', '--alluredir=./temp_results'])
        2. subprocess.run(['allure', 'generate', './temp_results', '-o', './reports/xxx'])

        关键修复：确保 --alluredir 路径和 allure generate 读取的路径完全一致
        """
        import shutil
        import sys
        from pathlib import Path

        # 转换为绝对路径 - 这是修复空报告Bug的关键！
        allure_results_dir_abs = str(Path(allure_results_dir).absolute())
        report_dir_abs = str(Path(report_dir).absolute())

        # 清理旧的结果（如果存在）- 必须完全清理否则会影响新报告
        shutil.rmtree(allure_results_dir_abs, ignore_errors=True)
        Path(allure_results_dir_abs).mkdir(parents=True, exist_ok=True)

        try:
            # Step 1: 执行 pytest 生成 allure-results
            # 兼容处理：尝试两种方式，保证在任何环境都能运行
            # 方式1: python -m pytest (使用当前 Python，能找到当前环境安装的 allure-pytest)
            # 方式2: 直接调用 pytest 命令 (当当前 Python 没有安装 pytest 但 PATH 中有时使用)
            result = None
            print(f"[ScenarioExecutionEngine] 测试文件路径: {test_file_path.absolute()}")
            print(f"[ScenarioExecutionEngine] 测试文件存在: {test_file_path.exists()}")
            print(f"[ScenarioExecutionEngine] Allure 结果目录: {allure_results_dir_abs}")
            print(f"[ScenarioExecutionEngine] 目录存在: {Path(allure_results_dir_abs).exists()}")

            # 列出目录内容在 pytest 执行前
            before_files = list(Path(allure_results_dir_abs).glob("*"))
            print(f"[ScenarioExecutionEngine] Pytest 执行前目录内有 {len(before_files)} 个文件")

            # 尝试 1: 使用当前 Python 解释器执行 pytest
            python_executable = sys.executable
            cmd1 = [
                python_executable,
                "-m",
                "pytest",
                str(test_file_path.absolute()),
                f"--alluredir={allure_results_dir_abs}",
                "-v",
                "--tb=short"
            ]

            print(f"[ScenarioExecutionEngine] 尝试方式1: {' '.join(cmd1)}")
            result = subprocess.run(
                cmd1,
                capture_output=True,
                text=True,
                timeout=120,
                cwd=str(test_file_path.parent),
                shell=True  # Windows 上需要 shell=True
            )

            print(f"[ScenarioExecutionEngine] 方式1 结果: returncode={result.returncode}")
            if result.stdout:
                print(f"[ScenarioExecutionEngine] 方式1 stdout:\n{result.stdout}")
            if result.stderr:
                print(f"[ScenarioExecutionEngine] 方式1 stderr:\n{result.stderr}")

            # 检查是否生成了结果文件
            result_files = list(Path(allure_results_dir_abs).glob("*.json"))
            print(f"[ScenarioExecutionEngine] 方式1 后 JSON 结果文件数量: {len(result_files)}")

            # 如果方式1失败（No module named pytest），尝试方式2和方式3
            if len(result_files) == 0 and result.returncode != 0 and "No module named pytest" in result.stderr:
                print(f"[ScenarioExecutionEngine] 方式1失败，尝试其他方式")

                # 方式2: 尝试从 Python 的 Scripts 目录找到 pytest.exe (Windows 常见位置)
                python_dir = Path(sys.executable).parent
                pytest_exe = python_dir / "Scripts" / "pytest.exe"

                if pytest_exe.exists():
                    cmd2 = [
                        str(pytest_exe),
                        str(test_file_path.absolute()),
                        f"--alluredir={allure_results_dir_abs}",
                        "-v",
                        "--tb=short"
                    ]
                    print(f"[ScenarioExecutionEngine] 尝试方式2 (Python Scripts): {' '.join(cmd2)}")
                    result = subprocess.run(
                        cmd2,
                        capture_output=True,
                        text=True,
                        timeout=120,
                        cwd=str(test_file_path.parent),
                        shell=True
                    )
                    print(f"[ScenarioExecutionEngine] 方式2 结果: returncode={result.returncode}")
                    if result.stdout:
                        print(f"[ScenarioExecutionEngine] 方式2 stdout:\n{result.stdout}")
                    if result.stderr:
                        print(f"[ScenarioExecutionEngine] 方式2 stderr:\n{result.stderr}")
                    result_files = list(Path(allure_results_dir_abs).glob("*.json"))
                    print(f"[ScenarioExecutionEngine] 方式2 后 JSON 结果文件数量: {len(result_files)}")
                else:
                    print(f"[ScenarioExecutionEngine] Scripts/pytest.exe 不存在: {pytest_exe}")

                # 如果方式2也失败，尝试方式3: 直接调用 pytest 命令 (PATH 中)
                if len(result_files) == 0:
                    print(f"[ScenarioExecutionEngine] 尝试方式3 (PATH 中): 直接调用 pytest 命令")
                    cmd3 = [
                        "pytest",
                        str(test_file_path.absolute()),
                        f"--alluredir={allure_results_dir_abs}",
                        "-v",
                        "--tb=short"
                    ]
                    print(f"[ScenarioExecutionEngine] 尝试方式3: {' '.join(cmd3)}")
                    result = subprocess.run(
                        cmd3,
                        capture_output=True,
                        text=True,
                        timeout=120,
                        cwd=str(test_file_path.parent),
                        shell=True
                    )
                    print(f"[ScenarioExecutionEngine] 方式3 结果: returncode={result.returncode}")
                    if result.stdout:
                        print(f"[ScenarioExecutionEngine] 方式3 stdout:\n{result.stdout}")
                    if result.stderr:
                        print(f"[ScenarioExecutionEngine] 方式3 stderr:\n{result.stderr}")
                    result_files = list(Path(allure_results_dir_abs).glob("*.json"))
                    print(f"[ScenarioExecutionEngine] 方式3 后 JSON 结果文件数量: {len(result_files)}")

            for f in result_files:
                print(f"[ScenarioExecutionEngine]   - {f.name} ({f.stat().st_size} bytes)")

            all_files = list(Path(allure_results_dir_abs).glob("*"))
            print(f"[ScenarioExecutionEngine] 目录内总文件数: {len(all_files)}")
            for f in all_files:
                if not f.name.endswith(".json"):
                    print(f"[ScenarioExecutionEngine]   - {f.name} (not json)")

            # 如果还是找不到 pytest，尝试自动安装 pytest 和 allure-pytest
            if len(result_files) == 0:
                print(f"[ScenarioExecutionEngine] 三种方式都找不到 pytest，尝试自动安装...")
                install_cmd = [
                    sys.executable,
                    "-m",
                    "pip",
                    "install",
                    "pytest",
                    "allure-pytest"
                ]
                print(f"[ScenarioExecutionEngine] 执行安装: {' '.join(install_cmd)}")
                install_result = subprocess.run(
                    install_cmd,
                    capture_output=True,
                    text=True,
                    shell=True
                )
                if install_result.returncode == 0:
                    print(f"[ScenarioExecutionEngine] 安装成功，重新尝试执行...")
                    # 安装成功后，重试方式1：python -m pytest
                    cmd_retry = [
                        sys.executable,
                        "-m",
                        "pytest",
                        str(test_file_path.absolute()),
                        f"--alluredir={allure_results_dir_abs}",
                        "-v",
                        "--tb=short"
                    ]
                    print(f"[ScenarioExecutionEngine] 重试: {' '.join(cmd_retry)}")
                    result = subprocess.run(
                        cmd_retry,
                        capture_output=True,
                        text=True,
                        timeout=300,  # 安装后重试给更长时间
                        cwd=str(test_file_path.parent),
                        shell=True
                    )
                    print(f"[ScenarioExecutionEngine] 重试结果: returncode={result.returncode}")
                    if result.stdout:
                        print(f"[ScenarioExecutionEngine] 重试 stdout:\n{result.stdout}")
                    if result.stderr:
                        print(f"[ScenarioExecutionEngine] 重试 stderr:\n{result.stderr}")
                    result_files = list(Path(allure_results_dir_abs).glob("*.json"))
                    print(f"[ScenarioExecutionEngine] 重试后 JSON 结果文件数量: {len(result_files)}")

            if len(result_files) == 0:
                print(f"[ScenarioExecutionEngine] 错误：所有方式都尝试了（包括自动安装），但仍然没有生成任何 Allure 结果文件！")
                return False

            # Step 2: 生成 Allure 报告
            # 关键修复：allure generate 读取的路径必须与 --alluredir 写入的路径完全一致
            report_result = subprocess.run(
                ["allure", "generate", allure_results_dir_abs, "-o", report_dir_abs, "--clean"],
                capture_output=True,
                text=True,
                timeout=60,
                shell=True
            )

            print(f"[ScenarioExecutionEngine] Allure generate stdout:\n{report_result.stdout}")
            if report_result.stderr:
                print(f"[ScenarioExecutionEngine] Allure generate stderr:\n{report_result.stderr}")

            if report_result.returncode == 0:
                print(f"[ScenarioExecutionEngine] Allure 报告生成成功: {report_dir_abs}")
                # 验证 index.html 是否真的生成了
                index_html = Path(report_dir_abs) / "index.html"
                if index_html.exists():
                    print(f"[ScenarioExecutionEngine] index.html 已生成: {index_html}")
                    return True
                else:
                    print(f"[ScenarioExecutionEngine] 警告：Allure generate 返回成功，但 index.html 不存在！")
                    return False
            else:
                print(f"[ScenarioExecutionEngine] Allure 报告生成失败, returncode={report_result.returncode}")
                return False

        except subprocess.TimeoutExpired:
            print(f"[ScenarioExecutionEngine] Pytest 执行超时")
            return False
        except FileNotFoundError as e:
            print(f"[ScenarioExecutionEngine] pytest 或 allure 命令未找到: {e}")
            return False
        except Exception as e:
            print(f"[ScenarioExecutionEngine] 执行异常: {e}")
            return False

    def _write_allure_result(self, allure_results_dir: Path, scenario_name: str, history_id: str, start_time: float, duration: int):
        """写入 Allure 结果文件（符合 Allure JSON 规范）- 已废弃，请使用 _generate_pytest_test_file"""
        # 此方法已废弃，保留仅用于兼容
        pass

    async def _execute_step(self, db, step: ScenarioStep) -> Dict[str, Any]:
        """
        执行单个步骤
        """
        api_case = step.api_case
        step_start_time = time.time()

        try:
            # 1. 合并变量：全局变量 + 步骤局部覆盖
            # 🔥 修复字段名：兼容 body 和 payload
            request_config = {
                "method": api_case.method,
                "url": api_case.url,
                "headers": api_case.headers or {},
                "body": getattr(api_case, 'body', None) or getattr(api_case, 'payload', None) or "",
                "payload": getattr(api_case, 'body', None) or getattr(api_case, 'payload', None) or "",
            }

            # 应用局部变量覆盖
            if step.variable_overrides:
                overrides = step.variable_overrides
                if "url" in overrides:
                    request_config["url"] = overrides["url"]
                if "headers" in overrides:
                    request_config["headers"].update(overrides["headers"])
                if "payload" in overrides:
                    request_config["payload"].update(overrides["payload"])

            # 2. 变量替换：先用环境变量，再用 context_vars
            all_vars = dict(self.context_vars)  # 复制，避免修改原字典
            request_config["url"] = replace_variables(request_config["url"], all_vars)
            request_config["headers"] = replace_variables(request_config["headers"], all_vars)
            request_config["payload"] = replace_variables(request_config["payload"], all_vars)

            # 3. 如果 URL 不是以 http 开头，则拼接 base_url
            if not request_config["url"].startswith(("http://", "https://")):
                if self.base_url:
                    request_config["url"] = self.base_url.rstrip("/") + "/" + request_config["url"].lstrip("/")

            # 4. 提取变量
            method = request_config["method"]
            url = request_config["url"]

            # 5. 标准化 Headers 和 Payload 处理（大厂级稳定逻辑）
            import json

            # 1. 提取并清理 Headers
            final_headers = {}
            raw_headers = request_config.get("headers", {})
            if isinstance(raw_headers, list):
                for h in raw_headers:
                    if isinstance(h, dict) and h.get("name"):
                        final_headers[str(h.get("name")).strip()] = str(h.get("value")).strip()
            elif isinstance(raw_headers, dict):
                final_headers.update(raw_headers)
            elif isinstance(raw_headers, str):
                # 如果是 JSON 字符串，尝试解析
                try:
                    parsed = json.loads(raw_headers)
                    if isinstance(parsed, list):
                        for h in parsed:
                            if isinstance(h, dict) and h.get("name"):
                                final_headers[str(h.get("name")).strip()] = str(h.get("value")).strip()
                    elif isinstance(parsed, dict):
                        final_headers.update(parsed)
                except:
                    pass

            # 优先获取 body，如果没有再获取 payload（兼容两种字段名）
            raw_payload = request_config.get("body") or request_config.get("payload") or ""

            # 2. 初始化核心参数
            req_kwargs = {
                "method": method,
                "url": url,
            }

            # 3. 极其重要的 Payload 处理（利用 httpx 原生 json 参数自动注入 Header）
            if raw_payload:
                if isinstance(raw_payload, str):
                    try:
                        # 尝试解析为 Dict。如果成功，直接交给 json=，httpx 会自动完美设置 application/json
                        parsed_json = json.loads(raw_payload)
                        req_kwargs["json"] = parsed_json
                    except json.JSONDecodeError:
                        # 如果不是合法 JSON（比如普通文本），再回退到 content=，并手动兜底 header
                        req_kwargs["content"] = raw_payload.encode('utf-8')
                        if not any(k.lower() == "content-type" for k in final_headers.keys()):
                            final_headers["Content-Type"] = "application/json"
                elif isinstance(raw_payload, dict):
                    req_kwargs["json"] = raw_payload
                else:
                    req_kwargs["content"] = str(raw_payload).encode('utf-8')

            # 🔥 第一步：无条件强制注入 Content-Type
            # 只要是 POST/PUT/PATCH 请求且没有 Content-Type，强制添加 application/json
            if method.upper() in ['POST', 'PUT', 'PATCH']:
                if not any(k.lower() == 'content-type' for k in final_headers.keys()):
                    final_headers['Content-Type'] = 'application/json'

            # 4. 强行挂载 Headers 到最终发包参数中（确保不丢失！）
            req_kwargs["headers"] = final_headers

            # 🔥 第三步：强制兜底 JSON - 如果空 body 但是 JSON content-type，给空字典
            if not raw_payload and 'application/json' in final_headers.get('Content-Type', ''):
                req_kwargs["json"] = {}

            # 5. 打印最终参数并发送（方便排错）
            print(f"🔥 [ScenarioRunner] 最终发包参数: {req_kwargs}")
            # 执行 HTTP 请求
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.request(**req_kwargs)

            step_duration = int((time.time() - step_start_time) * 1000)

            # ========== Bug1 修复：强制默认断言检查 ==========
            # 在解析响应之前，先检查状态码
            # 如果状态码 >= 400，并且用户没有显式针对状态码写断言，强制抛出 AssertionError
            assertions = api_case.assert_rules
            has_status_code_assertion = False

            # 判断用户是否显式针对 status_code 写了断言
            if assertions:
                if isinstance(assertions, list):
                    for rule in assertions:
                        field = rule.get("field") or rule.get("target", "")
                        if field == "status_code":
                            has_status_code_assertion = True
                            break
                elif isinstance(assertions, dict):
                    if "status_code" in assertions:
                        has_status_code_assertion = True

            # 【关键修复】如果状态码 >= 400，强制抛出 AssertionError 标记为失败
            if response.status_code >= 400:
                raise AssertionError(f"默认断言失败: 期望 2xx/3xx (< 400), 实际返回 {response.status_code}")
            # ========== Bug1 修复结束 ==========

            # 5. 解析响应
            response_data = {
                "status": response.status_code,
                "body": response.text,
                "headers": dict(response.headers),
            }

            try:
                response_json = response.json()
                response_data["json"] = response_json
            except:
                pass

            # 6. 执行断言（现在用户已明确不会有 status_code >= 400 的情况因为上面的检查已经处理了）
            if not assertions:
                assertions = []
            elif isinstance(assertions, dict):
                if len(assertions) == 0:
                    assertions = []
                else:
                    normalized_assertions = []
                    for key, value in assertions.items():
                        if isinstance(value, dict):
                            normalized_assertions.append({
                                "field": key,
                                "operator": value.get("operator", "equals"),
                                "expectedValue": value.get("expectedValue") or value.get("eq")
                            })
                        else:
                            normalized_assertions.append({
                                "field": key,
                                "operator": "equals",
                                "expectedValue": value
                            })
                    assertions = normalized_assertions
            elif not isinstance(assertions, list):
                assertions = []

            passed_assertions = 0
            failed_assertions = []
            total_assertions = 0

            # 执行用户配置的断言
            if assertions:
                total_assertions = len(assertions)
                for assertion in assertions:
                    passed, reason = self._check_assertion(assertion, response_data)
                    if passed:
                        passed_assertions += 1
                    else:
                        failed_assertions.append({"assertion": assertion, "reason": reason})

            # 7. 提取变量（如果配置了 Extractors）
            extractors = getattr(api_case, 'extractors', None) or []
            if isinstance(api_case.headers, str):
                try:
                    extractors = json.loads(api_case.headers)
                except:
                    extractors = []
            self._extract_variables(extractors, response_data)

            step_result = {
                "step_id": step.id,
                "step_order": step.step_order,
                "api_case_id": api_case.id,
                "api_case_name": api_case.name,
                "method": api_case.method,
                "url": request_config["url"],
                "success": len(failed_assertions) == 0,
                "status_code": response.status_code,
                "response_time": step_duration,
                "response": response_data,
                "assertions": {
                    "total": total_assertions,
                    "passed": passed_assertions,
                    "failed": failed_assertions
                },
                "extracted_vars": {k: v for k, v in self.context_vars.items() if k not in (self._get_initial_vars())}
            }

            return step_result

        except AssertionError:
            # AssertionError 会被外层捕获用于判断步骤失败，不需要额外处理
            raise
        except Exception as e:
            step_duration = int((time.time() - step_start_time) * 1000)
            raise  # 重新抛出，让外层处理

    def _get_initial_vars(self) -> set:
        """获取初始变量（环境变量），这些变量不计入提取"""
        return set()

    def _check_assertion(self, assertion: Dict, response_data: Dict) -> tuple:
        """
        检查断言是否通过
        支持两种格式:
        1. 旧格式: {field, operator, expectedValue}
        2. 新格式: {target, condition, value, expression?}
        返回 (passed: bool, reason: str)
        """
        # 兼容新旧两种格式
        field = assertion.get("field") or assertion.get("target", "")
        operator = assertion.get("operator") or assertion.get("condition", "equals")
        expected = assertion.get("expectedValue") or assertion.get("value", "")
        expression = assertion.get("expression", "")

        try:
            # 获取实际值
            if field == "status_code":
                actual = response_data.get("status", 0)
            elif field == "body":
                actual = response_data.get("body", "")
            elif expression:
                # JSONPath 表达式 (新格式)
                if isinstance(response_data.get("json"), dict):
                    keys = expression.replace("$.", "").split(".")
                    actual = response_data["json"]
                    for key in keys:
                        if isinstance(actual, dict) and key in actual:
                            actual = actual[key]
                        else:
                            actual = None
                            break
                else:
                    actual = None
            elif field.startswith("body."):
                # JSONPath 简化版：body.key
                parts = field.split(".", 1)
                if len(parts) == 2 and isinstance(response_data.get("json"), dict):
                    actual = response_data["json"].get(parts[1], "")
                else:
                    actual = ""
            else:
                actual = ""

            # 规范化操作符
            op_map = {
                "eq": "equals",
                "equals": "equals",
                "equal": "equals",
                "ne": "not_equals",
                "not_equals": "not_equals",
                "not_equal": "not_equals",
                "contains": "contains",
                "not_contains": "not_contains",
                "gt": "gt",
                "lt": "lt",
                "regex": "regex",
                "match": "regex"
            }
            operator = op_map.get(operator, operator)

            # 比较
            if operator == "equals":
                passed = str(actual) == str(expected)
            elif operator == "not_equals":
                passed = str(actual) != str(expected)
            elif operator == "contains":
                passed = str(expected) in str(actual)
            elif operator == "not_contains":
                passed = str(expected) not in str(actual)
            elif operator == "gt":
                passed = float(actual) > float(expected) if actual and expected else False
            elif operator == "lt":
                passed = float(actual) < float(expected) if actual and expected else False
            elif operator == "gte":
                passed = float(actual) >= float(expected) if actual and expected else False
            elif operator == "lte":
                passed = float(actual) <= float(expected) if actual and expected else False
            elif operator == "regex":
                import re
                passed = bool(re.search(str(expected), str(actual)))
            elif operator == "range":
                # 处理范围格式，如 "2xx/3xx", "2xx", "3xx"
                range_text = str(expected).lower()
                if "2xx/3xx" in range_text or ("2xx" in range_text and "3xx" in range_text):
                    passed = 200 <= actual < 400
                elif "2xx" == range_text:
                    passed = 200 <= actual < 300
                elif "3xx" == range_text:
                    passed = 300 <= actual < 400
                elif "5xx" == range_text:
                    passed = 500 <= actual < 600
                elif "4xx" == range_text:
                    passed = 400 <= actual < 500
                else:
                    passed = 200 <= actual < 400  # 默认 2xx/3xx
            else:
                passed = False

            return passed, "" if passed else f"期望 {expected}，实际 {actual}"

        except Exception as e:
            return False, f"断言检查异常: {str(e)}"

    def _extract_variables(self, extractors: List[Dict], response_data: Dict):
        """
        从响应中提取变量，存入 context_vars
        """
        if not extractors:
            return

        body = response_data.get("body", "")

        for extractor in extractors:
            var_name = extractor.get("variableName")
            extractor_type = extractor.get("extractorType", "jsonpath")
            expression = extractor.get("expression")
            default_value = extractor.get("defaultValue", "")

            if not var_name or not expression:
                continue

            value = default_value

            try:
                if extractor_type == "jsonpath":
                    # 简化 JSONPath：直接用 key 访问
                    if isinstance(response_data.get("json"), dict):
                        value = response_data["json"].get(expression, default_value)

                elif extractor_type == "regex":
                    import re
                    match = re.search(expression, body)
                    if match:
                        value = match.group(1) if match.groups() else match.group(0)

                elif extractor_type == "css":
                    # CSS 选择器简化版：不实现
                    pass

            except Exception as e:
                print(f"变量提取失败 {var_name}: {str(e)}")

            # 存入全局上下文
            self.context_vars[var_name] = value


async def run_scenario(scenario_id: int, env_id: Optional[int] = None) -> Dict[str, Any]:
    """
    执行场景的入口函数
    """
    engine = ScenarioExecutionEngine(scenario_id, env_id)
    return await engine.execute()


# ========== 数据驱动执行引擎 ==========

class DataDrivenScenarioExecutionEngine:
    """
    数据驱动场景执行引擎

    核心概念：
    - data_matrix: 二维数据矩阵，包含 columns（变量名）和 rows（数据行）
    - 每一行数据会驱动场景执行一次
    - 每次迭代开始时，将该行数据注入到 context_vars 中
    - 场景执行完毕后，收集结果并汇总
    """

    def __init__(self, scenario_id: int, env_id: Optional[int] = None):
        self.scenario_id = scenario_id
        self.env_id = env_id
        self.iterations: List[Dict[str, Any]] = []
        self.total_duration = 0

    async def execute(self) -> Dict[str, Any]:
        """
        执行数据驱动的场景
        返回所有迭代的汇总结果
        """
        start_time = time.time()

        async with async_session() as db:
            # 加载场景及其步骤和数据集
            result = await db.execute(
                select(TestScenario)
                .options(
                    selectinload(TestScenario.steps).selectinload(ScenarioStep.api_case),
                    selectinload(TestScenario.dataset)
                )
                .where(TestScenario.id == self.scenario_id)
            )
            scenario = result.scalar_one_or_none()
            if not scenario:
                raise ValueError(f"场景 {self.scenario_id} 不存在")

            dataset = scenario.dataset
            if not dataset or not dataset.data_matrix:
                raise ValueError("该场景没有配置数据驱动数据集")

            data_matrix = dataset.data_matrix
            columns = data_matrix.get("columns", [])
            rows = data_matrix.get("rows", [])

            if not columns or not rows:
                raise ValueError("数据集为空")

            # 加载环境变量
            env_config = {}
            env = None
            if self.env_id:
                result = await db.execute(
                    select(Environment).where(Environment.id == self.env_id)
                )
                env = result.scalar_one_or_none()
            else:
                # 获取默认环境
                result = await db.execute(
                    select(Environment).where(Environment.is_default == True)
                )
                env = result.scalar_one_or_none()
                if not env:
                    # 获取第一个环境
                    result = await db.execute(select(Environment))
                    env = result.scalars().first()
            
            if env:
                env_config = env.variables or {}

            # 逐行执行
            for row_index, row_data in enumerate(rows):
                iteration_result = await self._execute_iteration(
                    db=db,
                    scenario=scenario,
                    columns=columns,
                    row_data=row_data,
                    row_index=row_index,
                    env_config=env_config
                )
                self.iterations.append(iteration_result)
                self.total_duration += iteration_result.get("duration", 0)

        overall_duration = int((time.time() - start_time) * 1000)
        success_count = len([i for i in self.iterations if i.get("success")])
        failed_count = len(self.iterations) - success_count

        return {
            "scenario_id": self.scenario_id,
            "scenario_name": scenario.name,
            "dataset_name": dataset.name,
            "total_iterations": len(self.iterations),
            "success_iterations": success_count,
            "failed_iterations": failed_count,
            "total_duration": overall_duration,
            "iterations": self.iterations,
        }

    async def _execute_iteration(
        self,
        db,
        scenario,
        columns: List[str],
        row_data: List[Any],
        row_index: int,
        env_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        执行单次迭代

        将该行数据注入 context_vars，然后执行场景
        """
        iteration_start_time = time.time()

        # 构建该行的上下文变量
        row_vars = {}
        for col_name, value in zip(columns, row_data):
            row_vars[col_name] = value

        # 创建执行引擎实例
        engine = ScenarioExecutionEngine(self.scenario_id, self.env_id)
        engine.context_vars = dict(env_config)  # 基础环境变量
        engine.context_vars.update(row_vars)  # 注入该行数据

        try:
            # 执行场景
            result = await engine.execute()

            iteration_duration = int((time.time() - iteration_start_time) * 1000)

            return {
                "iteration_index": row_index,
                "data_row": dict(zip(columns, row_data)),  # 该行的键值对
                "step_results": result.get("step_results", []),
                "success": result.get("failed_steps", 0) == 0,
                "duration": iteration_duration,
                "context_vars": engine.context_vars,
                "error": None
            }
        except Exception as e:
            iteration_duration = int((time.time() - iteration_start_time) * 1000)
            return {
                "iteration_index": row_index,
                "data_row": dict(zip(columns, row_data)),
                "step_results": [],
                "success": False,
                "duration": iteration_duration,
                "context_vars": engine.context_vars,
                "error": str(e)
            }


async def run_scenario_data_driven(
    scenario_id: int,
    env_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    数据驱动执行场景的入口函数
    """
    engine = DataDrivenScenarioExecutionEngine(scenario_id, env_id)
    return await engine.execute()
