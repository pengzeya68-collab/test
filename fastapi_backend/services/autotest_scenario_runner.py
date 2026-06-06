"""
场景执行引擎（迁移自 auto_test_platform/services/scenario_runner.py）
核心逻辑：按顺序执行场景中的每个步骤，通过全局上下文传递变量
"""
import asyncio
import json
import logging
import os
import re
import subprocess
import time
import uuid
import httpx
from html import escape
from pathlib import Path
from typing import Dict, Any, List, Optional

from fastapi_backend.utils.autotest_helpers import convert_to_dict, extract_jsonpath_value
from fastapi_backend.services.autotest_variable_service import save_variables_to_db
from fastapi_backend.services.autotest_assertion_engine import get_field_value, compare_values, get_operator_text
# from fastapi_backend.services.autotest_report_service import write_allure_results
from fastapi_backend.core.autotest_database import async_session
from fastapi_backend.models.autotest import (
    AutoTestScenario,
    AutoTestScenarioStep,
    # AutoTestCase,
    AutoTestEnvironment,
    AutoTestScenarioExecutionRecord,
    AutoTestGlobalVariable,
)
from fastapi_backend.services.autotest_email_notifier import get_email_notifier
from fastapi_backend.utils.parser import replace_variables
from fastapi_backend.core.autotest_settings import get_settings
from sqlalchemy import select
from sqlalchemy.orm import selectinload

_logger = logging.getLogger(__name__)

# 项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
AUTOTEST_DATA_DIR = PROJECT_ROOT / "fastapi_backend" / "autotest_data"

# Docker 内部访问后端服务的地址（可通过环境变量覆盖）
_DOCKER_BACKEND_HOST = os.environ.get("SCENARIO_RUNNER_BACKEND_HOST", "backend")


def _is_running_in_docker() -> bool:
    """检测当前进程是否运行在 Docker 容器内。"""
    if os.path.exists("/.dockerenv"):
        return True
    try:
        with open("/proc/1/cgroup", "rt") as f:
            return "docker" in f.read() or "kubepods" in f.read()
    except (OSError, IOError):
        return False


def _rewrite_localhost_url(url: str) -> str:
    """
    当场景执行器运行在 Docker 容器内时，将 URL 中的 localhost/127.0.0.1
    替换为 Docker 内部后端服务名，确保 celery-worker 能正确访问 backend。
    """
    if not url:
        return url
    # 只在 Docker 容器内生效
    if not _is_running_in_docker():
        return url
    # 替换 localhost 和 127.0.0.1（保留端口）
    rewritten = re.sub(
        r"(https?://)(localhost|127\.0\.0\.1)(:\d+)?",
        lambda m: f"{m.group(1)}{_DOCKER_BACKEND_HOST}{m.group(3) or ''}",
        url,
    )
    if rewritten != url:
        _logger.info(f"[ScenarioRunner] URL rewritten: {url} -> {rewritten}")
    return rewritten





def _safe_format_value(val):
    """安全转义 format 字符串中的特殊字符，防止代码注入"""
    if isinstance(val, str):
        return val.replace('{', '{{').replace('}', '}}')
    return val


class ScenarioExecutionEngine:
    """
    场景执行引擎

    核心概念：
    - context_vars: 全局上下文字典，存储提取的变量（如 token）
    - 每一步执行完后，其 Extractors 提取的变量存入 context_vars
    - 下一步构造请求时，通过 replace_variables 自动从 context_vars 读取变量
    """

    def __init__(self, scenario_id: int, env_id: Optional[int] = None, progress_callback=None, user_id: int = None, _skip_record=False):
        self.scenario_id = scenario_id
        self.env_id = env_id
        self.context_vars: Dict[str, Any] = {}
        self.step_results: List[Dict[str, Any]] = []
        self.total_duration = 0
        self.base_url: str = ""
        self.progress_callback = progress_callback
        self.user_id = user_id
        self._skip_record = _skip_record
        self._initial_var_keys: set = set()
        self.env = None  # 初始化 env 属性，避免 finally 块中 AttributeError

    async def execute(self) -> Dict[str, Any]:
        """
        执行整个场景
        返回执行结果（包含完整的步骤列表和 Allure 报告链接）
        """
        start_time = time.time()
        report_url = None
        scenario_name = f"场景 {self.scenario_id}"
        env_name = ""

        try:
            async with async_session() as db:
                query = select(AutoTestScenario).options(selectinload(AutoTestScenario.steps).selectinload(AutoTestScenarioStep.api_case)).where(AutoTestScenario.id == self.scenario_id)
                if self.user_id is not None:
                    query = query.where(AutoTestScenario.user_id == self.user_id)
                result = await db.execute(query)
                scenario = result.scalar_one_or_none()
                if not scenario:
                    raise ValueError(f"场景 {self.scenario_id} 不存在")

                scenario_name = scenario.name

                # 加载环境变量
                env = None
                if self.env_id:
                    env_query = select(AutoTestEnvironment).where(AutoTestEnvironment.id == self.env_id)
                    if self.user_id is not None:
                        env_query = env_query.where(AutoTestEnvironment.user_id == self.user_id)
                    result = await db.execute(env_query)
                    env = result.scalar_one_or_none()
                else:
                    env_query = select(AutoTestEnvironment).where(AutoTestEnvironment.is_default.is_(True))
                    if self.user_id is not None:
                        env_query = env_query.where(AutoTestEnvironment.user_id == self.user_id)
                    result = await db.execute(env_query)
                    env = result.scalar_one_or_none()
                    if not env:
                        fallback_query = select(AutoTestEnvironment)
                        if self.user_id is not None:
                            fallback_query = fallback_query.where(AutoTestEnvironment.user_id == self.user_id)
                        result = await db.execute(fallback_query)
                        env = result.scalars().first()

                if env:
                    self.env = env  # 保存到 self.env，供 finally 块写数据库记录使用
                    env_name = env.env_name or ""
                    if isinstance(env.variables, dict):
                        self.context_vars.update(env.variables)
                    if env.base_url:
                        self.base_url = env.base_url
                        self.context_vars["base_url"] = env.base_url

                self._initial_var_keys = set(self.context_vars.keys())

                # 获取所有启用的步骤并排序
                all_steps = sorted([s for s in scenario.steps if s.is_active], key=lambda x: x.step_order)

                # 预加载步骤数据到内存，避免db会话关闭后DetachedInstanceError
                steps_data = []
                for step in all_steps:
                    step_info = {
                        'id': step.id,
                        'step_order': step.step_order,
                        'api_case_id': step.api_case_id,
                        'is_active': step.is_active,
                        'variable_overrides': step.variable_overrides,
                    }
                    if step.api_case:
                        step_info['api_case_name'] = step.api_case.name
                        step_info['api_case_method'] = step.api_case.method
                        step_info['api_case_url'] = step.api_case.url
                        step_info['api_case_headers'] = step.api_case.headers
                        step_info['api_case_params'] = step.api_case.params
                        step_info['api_case_body'] = step.api_case.payload
                        step_info['api_case_body_type'] = step.api_case.body_type
                        step_info['api_case_assert_rules'] = step.api_case.assert_rules
                        step_info['api_case_extractors'] = step.api_case.extractors
                    steps_data.append(step_info)

                total_steps = len(all_steps)
                fail_fast_enabled = getattr(scenario, 'fail_fast', False)

                if self.progress_callback:
                    self.progress_callback(0, total_steps, '加载场景和环境中...')

            # 阶段2：执行步骤（不需要数据库会话，避免高并发下连接池耗尽）
            failed_encountered = False
            for idx, step_info in enumerate(steps_data):
                step_name = step_info.get('api_case_name', f"Step {step_info['step_order']}")
                step_start = time.time()

                if failed_encountered and fail_fast_enabled:
                    self.step_results.append({
                        "step_id": step_info['id'],
                        "step_order": step_info['step_order'],
                        "api_case_id": step_info['api_case_id'],
                        "api_case_name": step_info.get('api_case_name', f"Step {step_info['step_order']}"),
                        "method": step_info.get('api_case_method', 'GET'),
                        "success": False,
                        "status": "skipped",
                        "response_time": 0,
                        "error": "因前序步骤失败且启用 fail_fast，跳过此步骤"
                    })
                    if self.progress_callback:
                        self.progress_callback(idx + 1, total_steps, f'跳过: {step_name}')
                    continue

                if self.progress_callback:
                    self.progress_callback(idx, total_steps, f'执行: {step_name}')

                try:
                    step_result = await self._execute_step(step_info)
                    if not step_result.get("success", False):
                        step_result["status"] = "failed"
                        self.step_results.append(step_result)
                        self.total_duration += step_result.get("duration", 0)
                        failed_encountered = True
                    else:
                        step_result["status"] = "success"
                        self.step_results.append(step_result)
                        self.total_duration += step_result.get("duration", 0)

                    if self.progress_callback:
                        self.progress_callback(idx + 1, total_steps, f'完成: {step_name}')

                except AssertionError as e:
                    step_duration = int((time.time() - step_start) * 1000)
                    self.step_results.append({
                        "step_id": step_info['id'],
                        "step_order": step_info['step_order'],
                        "api_case_id": step_info['api_case_id'],
                        "api_case_name": step_info.get('api_case_name', f"Step {step_info['step_order']}"),
                        "method": step_info.get('api_case_method', 'GET'),
                        "success": False,
                        "status": "failed",
                        "response_time": step_duration,
                        "error": f"断言失败: {str(e)}"
                    })
                    failed_encountered = True

                    if self.progress_callback:
                        self.progress_callback(idx + 1, total_steps, f'失败: {step_name}')

                except Exception as e:
                    step_duration = int((time.time() - step_start) * 1000)
                    self.step_results.append({
                        "step_id": step_info['id'],
                        "step_order": step_info['step_order'],
                        "api_case_id": step_info['api_case_id'],
                        "api_case_name": step_info.get('api_case_name', f"Step {step_info['step_order']}"),
                        "success": False,
                        "status": "failed",
                        "response_time": step_duration,
                        "error": f"执行异常: {str(e)}"
                    })
                    failed_encountered = True

                    if self.progress_callback:
                        self.progress_callback(idx + 1, total_steps, f'异常: {step_name}')

        finally:
            overall_duration = int((time.time() - start_time) * 1000)
            history_id = str(uuid.uuid4())[:8]

            # 统计
            total_steps = len(self.step_results)
            success_steps = len([r for r in self.step_results if r.get("status") == "success"])
            failed_steps = len([r for r in self.step_results if r.get("status") == "failed"])
            skipped_steps = len([r for r in self.step_results if r.get("status") == "skipped"])

            if failed_steps > 0:
                status = "failed"
            elif success_steps == total_steps:
                status = "success"
            else:
                status = "error"

            # 保存执行记录到数据库
            record = None
            if not self._skip_record:
                try:
                    async with async_session() as db:
                        record = AutoTestScenarioExecutionRecord(
                            scenario_id=self.scenario_id,
                            env_id=self.env.id if self.env else None,
                            status=status,
                            total_steps=total_steps,
                            failed_steps=failed_steps,
                            success_steps=success_steps,
                            skipped_steps=skipped_steps,
                            total_time=overall_duration,
                            report_url=None,  # 先设为None，报告生成后更新
                            user_id=self.user_id
                        )
                        db.add(record)
                        await db.commit()
                        await db.refresh(record)

                        # 保存完整的步骤结果到 JSON 文件
                        step_results_file = AUTOTEST_DATA_DIR / "step_results" / f"scenario_{self.scenario_id}_record_{record.id}.json"
                        step_results_file.parent.mkdir(parents=True, exist_ok=True)
                        with open(step_results_file, "w", encoding="utf-8") as f:
                            json.dump(self.step_results, f, ensure_ascii=False, indent=2, default=str)
                except Exception as e:
                    _logger.error(f"保存执行记录失败: {e}", exc_info=True)

            # 报告生成
            temp_pytest_dir = AUTOTEST_DATA_DIR / "temp_pytest_tests"
            allure_results_dir = AUTOTEST_DATA_DIR / "allure-results" / f"scenario_{self.scenario_id}_{history_id}"
            report_dir = AUTOTEST_DATA_DIR / "reports" / f"scenario_{self.scenario_id}_{history_id}"

            temp_pytest_dir.mkdir(parents=True, exist_ok=True)
            allure_results_dir.mkdir(parents=True, exist_ok=True)
            report_dir.mkdir(parents=True, exist_ok=True)

            test_file_path = self._generate_pytest_test_file(temp_pytest_dir, scenario_name, history_id)
            report_generated = await self._run_pytest_and_generate_report(test_file_path, str(allure_results_dir), str(report_dir))
            if not report_generated:
                self._write_fallback_report(report_dir, scenario_name, env_name, overall_duration)

            index_html = report_dir / "index.html"
            if index_html.exists():
                report_url = f"/reports/scenario_{self.scenario_id}_{history_id}/index.html"
            else:
                report_url = None

            # 更新记录中的 report_url
            if record and not self._skip_record:
                try:
                    async with async_session() as db:
                        # 重新查询记录以避免 DetachedInstanceError
                        from sqlalchemy import update as sa_update
                        await db.execute(
                            sa_update(AutoTestScenarioExecutionRecord)
                            .where(AutoTestScenarioExecutionRecord.id == record.id)
                            .values(report_url=report_url)
                        )
                        await db.commit()
                except Exception as e:
                    _logger.warning(f"更新报告URL失败: {e}")

            # 邮件通知（移到报告生成之后，确保 report_url 不为 None）
            try:
                settings = get_settings()
                admin_email = getattr(settings, "EMAIL_ADMIN_TO", None)
                if admin_email and report_url:
                    notifier = get_email_notifier()
                    email_task = asyncio.create_task(
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
                            base_url=getattr(settings, "AUTO_TEST_BASE_URL", ""),
                        )
                    )
                    def _on_email_done(t: asyncio.Task):
                        if not t.cancelled():
                            exc = t.exception()
                            if exc:
                                _logger.warning(f"邮件通知发送失败: {exc}")
                    email_task.add_done_callback(_on_email_done)
            except Exception as e:
                _logger.warning(f"邮件通知创建失败: {e}")

        return {
            "scenario_id": self.scenario_id,
            "scenario_name": scenario_name,
            "env_name": env_name,
            "total_steps": total_steps,
            "success_steps": success_steps,
            "failed_steps": failed_steps,
            "skipped_steps": skipped_steps,
            "success_count": success_steps,
            "failed_count": failed_steps,
            "skipped_count": skipped_steps,
            "total_time": overall_duration,
            "context_vars": self.context_vars,
            "step_results": self.step_results,
            "report_url": report_url,
            "execution_record_id": record.id if record else None,
            "report_id": f"scenario_{self.scenario_id}" if report_url else None,
        }

    def _generate_pytest_test_file(self, temp_dir: Path, scenario_name: str, history_id: str) -> Path:
        test_filename = f"test_scenario_{self.scenario_id}_{history_id}.py"
        test_file_path = temp_dir / test_filename
        test_code = self._build_pytest_test_code(scenario_name, history_id)
        with open(test_file_path, "w", encoding="utf-8") as f:
            f.write(test_code)
        return test_file_path

    def _build_pytest_test_code(self, scenario_name: str, history_id: str) -> str:
        step_methods = []

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

            assertions = step.get("assertions", {})
            failed_assertions = assertions.get("failed", [])
            # passed_assertions = assertions.get("passed", 0)
            # total_assertions = assertions.get("total", 0)

            assert_messages = []
            for fa in failed_assertions:
                if isinstance(fa, dict):
                    assert_messages.append(fa.get("reason", str(fa)))
                else:
                    assert_messages.append(str(fa))

            is_really_success = success and status_code > 0 and url

            if is_really_success:
                step_status = "passed"
                step_error = ""
            else:
                step_status = "failed"
                if success and (status_code == 0 or not url):
                    step_error = f"请求未成功发出 (status_code={status_code}, url为空)"
                else:
                    step_error = error or "; ".join(assert_messages) or f"请求失败, 状态码 {status_code}"

            step_error_escaped = json.dumps(step_error)[1:-1]
            step_name_escaped = json.dumps(step_name)[1:-1]
            url_escaped = json.dumps(url)[1:-1]

            if step_status == "failed":
                assert_block = f'        assert False, "步骤{i_plus_1}失败: {step_error_escaped}"'
            else:
                assert_block = '        pass'

            step_method = '''
    @allure.title("用例{i_plus_1}: {step_name_escaped}")
    def test_step_{i_plus_1}(self):
        """[{method}] {step_name_escaped}"""
        with allure.step("1. 发起HTTP请求: {method} {url_escaped}"):
            request_info = {{
                "url": "{url_escaped}",
                "method": "{method}",
                "headers": {headers},
                "payload": {payload}
            }}
            allure.attach(
                json.dumps(request_info, ensure_ascii=False, indent=2),
                name="请求信息",
                attachment_type=allure.attachment_type.JSON
            )
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
        with allure.step("3. 执行断言校验"):
    {assert_block}
'''.format(
    i_plus_1=i_plus_1,
    step_name_escaped=_safe_format_value(step_name_escaped),
    method=_safe_format_value(method),
    url_escaped=_safe_format_value(url_escaped),
    headers=_safe_format_value(json.dumps(headers, ensure_ascii=False)),
    payload=_safe_format_value(json.dumps(payload, ensure_ascii=False)),
    status_code=status_code,
    response_time=response_time,
    response_body_quoted=_safe_format_value(json.dumps(response_body[:2000] if response_body else "", ensure_ascii=False)),
    assert_block=_safe_format_value(assert_block)
)
            step_methods.append(step_method)

        methods_joined = '\n'.join(step_methods)

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

@pytest.fixture(scope="session", autouse=True)
def write_allure_environment(request):
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
            f.write("History_ID={history_id_quoted}\\n")
            f.write("Total_Steps={len_steps}\\n")
    yield

@allure.suite("{scenario_name}")
@allure.feature("{scenario_name}")
class TestScenario{scenario_id}:
    """场景: {scenario_name} ({len_steps}个步骤)"""

{methods_joined}
'''.format(
    scenario_name=_safe_format_value(scenario_name),
    scenario_id=self.scenario_id,
    history_id=history_id,
    history_id_quoted=repr(str(history_id)),
    len_steps=len(self.step_results),
    methods_joined=_safe_format_value(methods_joined)
)
        return test_code

    async def _run_pytest_and_generate_report(self, test_file_path: Path, allure_results_dir: str, report_dir: str) -> bool:
        import shutil
        import sys
        import os

        allure_results_dir_abs = str(Path(allure_results_dir).absolute())
        report_dir_abs = str(Path(report_dir).absolute())

        # 强制执行前彻底清理旧数据（包含 pycache 和临时文件）
        _logger.info(f"[AllureReport] 清理旧结果目录：{allure_results_dir_abs}")
        if os.path.exists(allure_results_dir_abs):
            try:
                shutil.rmtree(allure_results_dir_abs)
                _logger.info(f"[AllureReport] 已删除旧目录：{allure_results_dir_abs}")
            except Exception as e:
                _logger.warning(f"[AllureReport] 清理失败：{e}")
        # 重新创建空目录
        Path(allure_results_dir_abs).mkdir(parents=True, exist_ok=True)
        _logger.info(f"[AllureReport] 已创建新目录：{allure_results_dir_abs}")

        try:
            python_executable = sys.executable
            cmd1 = [
                python_executable, "-m", "pytest",
                str(test_file_path.absolute()),
                f"--alluredir={allure_results_dir_abs}",
                "-v", "--tb=short"
            ]

            result = await asyncio.to_thread(subprocess.run, cmd1, capture_output=True, text=True, timeout=120,
                                    cwd=str(test_file_path.parent))

            result_files = list(Path(allure_results_dir_abs).glob("*.json"))

            if len(result_files) == 0 and result.returncode != 0 and "No module named pytest" in result.stderr:
                python_dir = Path(sys.executable).parent
                pytest_exe = python_dir / "Scripts" / "pytest.exe"

                if pytest_exe.exists():
                    cmd2 = [str(pytest_exe), str(test_file_path.absolute()),
                            f"--alluredir={allure_results_dir_abs}", "-v", "--tb=short"]
                    result = await asyncio.to_thread(subprocess.run, cmd2, capture_output=True, text=True, timeout=120,
                                            cwd=str(test_file_path.parent))
                    result_files = list(Path(allure_results_dir_abs).glob("*.json"))

                if len(result_files) == 0:
                    cmd3 = ["pytest", str(test_file_path.absolute()),
                            f"--alluredir={allure_results_dir_abs}", "-v", "--tb=short"]
                    result = await asyncio.to_thread(subprocess.run, cmd3, capture_output=True, text=True, timeout=120,
                                            cwd=str(test_file_path.parent))
                    result_files = list(Path(allure_results_dir_abs).glob("*.json"))

            if len(result_files) == 0:
                install_cmd = [sys.executable, "-m", "pip", "install", "pytest", "allure-pytest"]
                install_result = await asyncio.to_thread(subprocess.run, install_cmd, capture_output=True, text=True)
                if install_result.returncode == 0:
                    cmd_retry = [sys.executable, "-m", "pytest", str(test_file_path.absolute()),
                                 f"--alluredir={allure_results_dir_abs}", "-v", "--tb=short"]
                    result = await asyncio.to_thread(subprocess.run, cmd_retry, capture_output=True, text=True, timeout=300,
                                            cwd=str(test_file_path.parent))
                    result_files = list(Path(allure_results_dir_abs).glob("*.json"))

            if len(result_files) == 0:
                return False

            old_report_history = Path(report_dir_abs) / "history"
            new_results_history = Path(allure_results_dir_abs) / "history"
            if old_report_history.exists() and old_report_history.is_dir():
                if new_results_history.exists():
                    shutil.rmtree(str(new_results_history))
                shutil.copytree(str(old_report_history), str(new_results_history))
                _logger.info(f"[AllureReport] 已拷贝历史趋势数据: {old_report_history} -> {new_results_history}")

            report_result = await asyncio.to_thread(subprocess.run,
                ["allure", "generate", allure_results_dir_abs, "-o", report_dir_abs, "--clean"],
                capture_output=True, text=True, timeout=60
            )

            if report_result.returncode == 0:
                index_html = Path(report_dir_abs) / "index.html"
                return index_html.exists()
            _logger.warning(
                "[AllureReport] 生成 HTML 失败，returncode=%s, stdout=%s, stderr=%s",
                report_result.returncode,
                (report_result.stdout or "")[:1000],
                (report_result.stderr or "")[:1000],
            )
            return False

        except Exception as e:
            _logger.error(f"Pytest 执行或 Allure 报告生成失败: {e}", exc_info=True)
            return False

    def _write_fallback_report(self, report_dir: Path, scenario_name: str, env_name: str, overall_duration: int) -> None:
        """Allure 生成失败时，兜底写一个可查看的静态 HTML 报告。"""
        report_dir.mkdir(parents=True, exist_ok=True)
        success_steps = len([r for r in self.step_results if r.get("status") == "success"])
        failed_steps = len([r for r in self.step_results if r.get("status") == "failed"])
        skipped_steps = len([r for r in self.step_results if r.get("status") == "skipped"])

        cards = []
        for index, step in enumerate(self.step_results, start=1):
            status = step.get("status", "unknown")
            status_text = {"success": "通过", "failed": "失败", "skipped": "跳过"}.get(status, status)
            color = {"success": "#67c23a", "failed": "#f56c6c", "skipped": "#909399"}.get(status, "#409eff")
            method = escape(str(step.get("method", "GET")))
            name = escape(str(step.get("api_case_name", f"步骤 {index}")))
            url = escape(str(step.get("url", "")))
            error_text = escape(str(step.get("error", "")))
            response_body = step.get("response", {}).get("body", "") if isinstance(step.get("response"), dict) else ""
            response_preview = escape(str(response_body)[:3000])
            cards.append(f"""
            <div class="step-card">
              <div class="step-head">
                <span class="step-index">{index}</span>
                <span class="status" style="background:{color};">{status_text}</span>
                <span class="method">{method}</span>
                <span class="name">{name}</span>
              </div>
              <div class="meta">URL: {url or '-'}</div>
              <div class="meta">状态码: {step.get("status_code", "-")} | 耗时: {step.get("response_time", 0)}ms</div>
              <div class="meta">错误: {error_text or '-'}</div>
              <pre>{response_preview or '(无响应体)'}</pre>
            </div>
            """)

        html = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <title>{escape(scenario_name)} - 执行报告</title>
  <style>
    body {{ font-family: Arial, sans-serif; background:#0f172a; color:#e5e7eb; margin:0; padding:24px; }}
    .wrap {{ max-width: 1200px; margin: 0 auto; }}
    .header, .step-card {{ background:#111827; border:1px solid #334155; border-radius:12px; padding:20px; margin-bottom:16px; }}
    .stats {{ display:flex; gap:16px; flex-wrap:wrap; margin-top:16px; }}
    .stat {{ background:#1f2937; border-radius:10px; padding:12px 16px; min-width:120px; }}
    .step-head {{ display:flex; gap:10px; align-items:center; flex-wrap:wrap; margin-bottom:10px; }}
    .step-index {{ width:28px; height:28px; border-radius:999px; background:#2563eb; display:inline-flex; align-items:center; justify-content:center; }}
    .status {{ padding:2px 8px; border-radius:999px; color:#fff; font-size:12px; }}
    .method {{ font-weight:bold; color:#93c5fd; }}
    .name {{ font-size:16px; }}
    .meta {{ color:#cbd5e1; margin:4px 0; word-break:break-all; }}
    pre {{ background:#020617; color:#e2e8f0; padding:12px; border-radius:8px; overflow:auto; white-space:pre-wrap; word-break:break-word; }}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="header">
      <h1>{escape(scenario_name)}</h1>
      <div>环境: {escape(env_name or '未指定')}</div>
      <div>总耗时: {overall_duration}ms</div>
      <div class="stats">
        <div class="stat">总步骤: {len(self.step_results)}</div>
        <div class="stat">成功: {success_steps}</div>
        <div class="stat">失败: {failed_steps}</div>
        <div class="stat">跳过: {skipped_steps}</div>
      </div>
    </div>
    {''.join(cards) if cards else '<div class="step-card">暂无步骤数据</div>'}
  </div>
</body>
</html>"""

        (report_dir / "index.html").write_text(html, encoding="utf-8")

    def write_allure_results(self, allure_results_dir: Path, scenario_name: str, history_id: str, start_time: float, duration: int):
        """已废弃，保留兼容"""
        pass

    async def _execute_step(self, step_info: Dict[str, Any]) -> Dict[str, Any]:
        """执行单个步骤，接受预加载的步骤数据字典（避免DetachedInstanceError）"""
        # 检查是否有api_case数据
        api_case_name = step_info.get('api_case_name')
        if not api_case_name:
            return {
                "step_order": step_info['step_order'],
                "api_case_name": f"步骤{step_info['step_order']}",
                "status": "error",
                "success": False,
                "error": f"关联的接口用例不存在 (api_case_id={step_info.get('api_case_id')})",
                "assertion_results": [],
                "variable_extractions": [],
            }
        step_start_time = time.time()

        try:
            import copy
            request_config = {
                "method": step_info.get('api_case_method', 'GET'),
                "url": step_info.get('api_case_url', ''),
                "headers": copy.deepcopy(step_info.get('api_case_headers')) or {},
                "params": copy.deepcopy(step_info.get('api_case_params')) or {},
                "body": copy.deepcopy(step_info.get('api_case_body')) or "",
                "payload": copy.deepcopy(step_info.get('api_case_body')) or "",
            }

            if step_info.get('variable_overrides'):
                overrides = step_info['variable_overrides']
                if "url" in overrides:
                    request_config["url"] = overrides["url"]
                if "headers" in overrides:
                    request_config["headers"].update(overrides["headers"])
                if "payload" in overrides:
                    override_payload = overrides["payload"]
                    if isinstance(request_config["payload"], dict) and isinstance(override_payload, dict):
                        request_config["payload"].update(override_payload)
                    else:
                        request_config["payload"] = override_payload
                    # 同步更新 body，确保后续 raw_payload 取值一致
                    request_config["body"] = request_config["payload"]

            all_vars = dict(self.context_vars)
            request_config["url"] = replace_variables(request_config["url"], all_vars)
            # 对 dict/list 类型的值，先序列化为 JSON 字符串再替换再反序列化
            if isinstance(request_config["headers"], dict):
                headers_str = json.dumps(request_config["headers"], ensure_ascii=False)
                request_config["headers"] = json.loads(replace_variables(headers_str, all_vars))
            else:
                request_config["headers"] = replace_variables(request_config["headers"], all_vars)
            if isinstance(request_config["params"], dict):
                params_str = json.dumps(request_config["params"], ensure_ascii=False)
                request_config["params"] = json.loads(replace_variables(params_str, all_vars))
            else:
                request_config["params"] = replace_variables(request_config["params"], all_vars)
            if isinstance(request_config["payload"], (dict, list)):
                payload_str = json.dumps(request_config["payload"], ensure_ascii=False)
                request_config["payload"] = json.loads(replace_variables(payload_str, all_vars))
            else:
                request_config["payload"] = replace_variables(request_config["payload"], all_vars)

            if not request_config["url"].startswith(("http://", "https://")):
                if self.base_url:
                    request_config["url"] = self.base_url.rstrip("/") + "/" + request_config["url"].lstrip("/")

            # Docker 内部执行时，将 localhost 重写为后端服务名
            request_config["url"] = _rewrite_localhost_url(request_config["url"])

            # SSRF 安全校验
            from fastapi_backend.core.ssrf_guard import validate_url_safety
            safe, reason = validate_url_safety(request_config["url"])
            if not safe:
                raise ValueError(f"URL 安全校验失败: {reason}")

            method = request_config["method"]
            url = request_config["url"]

            # 标准化 Headers
            final_headers = {}
            raw_headers = convert_to_dict(request_config.get("headers"))
            if isinstance(raw_headers, list):
                for h in raw_headers:
                    if isinstance(h, dict) and h.get("name"):
                        final_headers[str(h.get("name")).strip()] = str(h.get("value")).strip()
            elif isinstance(raw_headers, dict):
                final_headers.update(raw_headers)

            raw_payload = request_config.get("body") or request_config.get("payload") or ""
            raw_params = request_config.get("params") or {}

            req_kwargs = {"method": method, "url": url}

            if raw_params and isinstance(raw_params, dict):
                req_kwargs["params"] = raw_params

            # 获取 body_type，决定如何发送请求体
            body_type = step_info.get('api_case_body_type') or ''

            if raw_payload:
                if body_type in ('form-data', 'form', 'multipart'):
                    # form-data / x-www-form-urlencoded：使用 data 发送
                    if isinstance(raw_payload, str):
                        try:
                            parsed = json.loads(raw_payload)
                            req_kwargs["data"] = parsed if isinstance(parsed, dict) else raw_payload
                        except json.JSONDecodeError:
                            # 尝试解析 key=value&key2=value2 格式
                            form_data = {}
                            for pair in raw_payload.split('&'):
                                if '=' in pair:
                                    k, v = pair.split('=', 1)
                                    form_data[k.strip()] = v.strip()
                            req_kwargs["data"] = form_data if form_data else raw_payload
                    elif isinstance(raw_payload, dict):
                        req_kwargs["data"] = raw_payload
                    else:
                        req_kwargs["data"] = str(raw_payload)
                    # form-data 不设置 Content-Type，让 httpx 自动处理
                    if 'Content-Type' in final_headers:
                        del final_headers['Content-Type']
                elif body_type == 'raw':
                    # raw 模式：直接发送原始字符串
                    if isinstance(raw_payload, str):
                        req_kwargs["content"] = raw_payload.encode('utf-8')
                    else:
                        req_kwargs["content"] = str(raw_payload).encode('utf-8')
                else:
                    # 默认 JSON 模式
                    if isinstance(raw_payload, str):
                        try:
                            parsed_json = json.loads(raw_payload)
                            req_kwargs["json"] = parsed_json
                        except json.JSONDecodeError:
                            req_kwargs["content"] = raw_payload.encode('utf-8')
                            if not any(k.lower() == "content-type" for k in final_headers.keys()):
                                final_headers["Content-Type"] = "application/json"
                    elif isinstance(raw_payload, dict):
                        req_kwargs["json"] = raw_payload
                    else:
                        req_kwargs["content"] = str(raw_payload).encode('utf-8')

            if method.upper() in ['POST', 'PUT', 'PATCH']:
                if not any(k.lower() == 'content-type' for k in final_headers.keys()):
                    if 'json' in req_kwargs or (not raw_payload and 'data' not in req_kwargs):
                        final_headers['Content-Type'] = 'application/json'

            req_kwargs["headers"] = final_headers

            if not raw_payload and 'application/json' in final_headers.get('Content-Type', ''):
                req_kwargs["json"] = {}

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.request(**req_kwargs)

            step_duration = int((time.time() - step_start_time) * 1000)

            # 解析断言规则（由断言引擎统一判断，不再提前拦截）
            assertions = step_info.get('api_case_assert_rules')

            # 对断言规则中的变量占位符做替换（支持dict/list类型）
            if assertions:
                if isinstance(assertions, (dict, list)):
                    import json
                    assertions_str = json.dumps(assertions, ensure_ascii=False)
                    assertions_str = replace_variables(assertions_str, all_vars)
                    try:
                        assertions = json.loads(assertions_str)
                    except json.JSONDecodeError:
                        pass
                elif isinstance(assertions, str):
                    assertions = replace_variables(assertions, all_vars)

            # 解析响应
            response_data = {
                "status": response.status_code,
                "body": response.text,
                "headers": dict(response.headers),
            }
            try:
                response_json = response.json()
                response_data["json"] = response_json
            except Exception as e:
                _logger.debug(f"响应JSON解析失败: {e}")

            # 执行断言
            if not assertions:
                assertions = []
            elif isinstance(assertions, dict):
                if len(assertions) == 0:
                    assertions = []
                else:
                    normalized_assertions = []
                    for key, value in assertions.items():
                        # 处理特殊键：status_code 和 json_path
                        if key == "status_code":
                            normalized_assertions.append({
                                "field": "status_code",
                                "operator": "equals" if isinstance(value, (int, str)) else (value.get("operator", "equals") if isinstance(value, dict) else "equals"),
                                "expectedValue": value if not isinstance(value, dict) else value.get("expectedValue", value.get("eq", ""))
                            })
                        elif key == "json_path":
                            # json_path 断言格式: {"json_path": {"$.path": {"operator": "eq", "expectedValue": "val"}}}
                            if isinstance(value, dict):
                                for jp, jp_val in value.items():
                                    if isinstance(jp_val, dict):
                                        normalized_assertions.append({
                                            "field": jp,
                                            "operator": jp_val.get("operator", "equals"),
                                            "expectedValue": jp_val.get("expectedValue") or jp_val.get("eq", "")
                                        })
                                    else:
                                        normalized_assertions.append({
                                            "field": jp,
                                            "operator": "equals",
                                            "expectedValue": jp_val
                                        })
                        elif isinstance(value, dict):
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

            if assertions:
                total_assertions = len(assertions)
                for assertion in assertions:
                    passed, reason = self._check_assertion(assertion, response_data, step_duration)
                    if passed:
                        passed_assertions += 1
                    else:
                        failed_assertions.append({"assertion": assertion, "reason": reason})

            # 提取变量
            extractors = step_info.get('api_case_extractors') or []
            await self._extract_variables(extractors, response_data)

            # 安全解析 payload 为 JSON，解析失败时保留原始字符串
            if isinstance(raw_payload, (dict, list)):
                payload_for_result = raw_payload
            elif isinstance(raw_payload, str) and raw_payload.strip():
                try:
                    payload_for_result = json.loads(raw_payload)
                except (json.JSONDecodeError, TypeError, ValueError) as e:
                    _logger.warning(f"步骤结果中 payload JSON 解析失败: {e}")
                    payload_for_result = raw_payload
            else:
                payload_for_result = {}

            step_result = {
                "step_id": step_info['id'],
                "step_order": step_info['step_order'],
                "api_case_id": step_info['api_case_id'],
                "api_case_name": step_info.get('api_case_name', ''),
                "method": step_info.get('api_case_method', 'GET'),
                "url": request_config["url"],
                "headers": final_headers,
                "payload": payload_for_result,
                "success": len(failed_assertions) == 0,
                "status_code": response.status_code,
                "response_time": step_duration,
                "response": response_data,
                "assertions": {
                    "total": total_assertions,
                    "passed": passed_assertions,
                    "failed": failed_assertions
                },
                "extracted_vars": {k: v for k, v in self.context_vars.items() if k not in self._get_initial_vars()}
            }

            return step_result

        except AssertionError as e:
            _logger.warning(f"断言检查失败: {str(e)}")
            raise
        except Exception as e:
            _logger.error(f"步骤执行异常: {str(e)}", exc_info=True)
            raise

    def _get_initial_vars(self) -> set:
        return self._initial_var_keys

    def _check_assertion(self, assertion: Dict, response_data: Dict, step_duration: int = 0) -> tuple:
        field = assertion.get("field") or assertion.get("target", "")
        operator = assertion.get("operator") or assertion.get("condition", "equals")
        expected = assertion.get("expectedValue") or assertion.get("value", "")

        # 使用 expression 作为 field 的备选（兼容旧格式）
        expression = assertion.get("expression", "")
        if expression and not field:
            field = expression

        # 标准化操作符（与断言引擎一致）
        op_map = {
            "eq": "equals", "equal": "equals",
            "ne": "not_equals", "not_equal": "not_equals",
            "match": "regex",
        }
        operator = op_map.get(operator, operator)

        try:
            status_code = response_data.get("status", 0)
            response_body = response_data.get("json") if "json" in response_data else response_data.get("body", "")
            response_time_ms = step_duration
            response_headers = response_data.get("headers")

            actual = get_field_value(field, status_code, response_body, response_time_ms, response_headers)
            passed = compare_values(actual, operator, expected)

            return passed, "" if passed else f"字段 {field} {get_operator_text(operator)} {expected}，实际: {actual}"

        except Exception as e:
            return False, f"断言检查异常: {str(e)}"

    async def _extract_variables(self, extractors: List[Dict], response_data: Dict):
        if not extractors:
            return

        body = response_data.get("body", "")
        new_vars = {}  # 只记录本步骤新提取的变量

        for extractor in extractors:
            var_name = extractor.get("variableName")
            extractor_type = extractor.get("extractorType", "jsonpath")
            expression = extractor.get("expression")
            default_value = extractor.get("defaultValue", "")

            if extractor_type == "header":
                if not var_name or not extractor.get("name"):
                    continue
            else:
                if not var_name or not expression:
                    continue

            value = default_value

            try:
                if extractor_type == "jsonpath":
                    json_data = response_data.get("json")
                    if json_data is not None:
                        value = extract_jsonpath_value(json_data, expression, default_value)
                elif extractor_type == "regex":
                    import re
                    match = re.search(expression, body)
                    if match:
                        value = match.group(1) if match.groups() else match.group(0)
                elif extractor_type == "header":
                    headers = response_data.get("headers", {})
                    if headers:
                        header_name = (extractor.get("name") or expression or "").lower()
                        for k, v in headers.items():
                            if k.lower() == header_name:
                                value = v
                                break
            except Exception as e:
                _logger.warning(f"变量提取失败 {var_name}: {str(e)}")

            self.context_vars[var_name] = value
            new_vars[var_name] = value

        # 只持久化本步骤新提取的变量，而非整个 context_vars（避免环境变量泄露）
        if new_vars:
            try:
                await save_variables_to_db(new_vars, user_id=self.user_id)
                # 使全局变量缓存失效
                from fastapi_backend.services.autotest_execution import _invalidate_global_vars_cache
                await _invalidate_global_vars_cache(self.user_id)
            except Exception as e:
                _logger.warning(f"变量持久化失败: {e}")


class DataDrivenScenarioExecutionEngine:
    """数据驱动场景执行引擎"""

    def __init__(self, scenario_id: int, env_id: Optional[int] = None, progress_callback=None, user_id: int = None):
        self.scenario_id = scenario_id
        self.env_id = env_id
        self.iterations: List[Dict[str, Any]] = []
        self.total_duration = 0
        self.progress_callback = progress_callback
        self.user_id = user_id

    async def execute(self) -> Dict[str, Any]:
        start_time = time.time()

        async with async_session() as db:
            query = select(AutoTestScenario).options(selectinload(AutoTestScenario.steps).selectinload(AutoTestScenarioStep.api_case), selectinload(AutoTestScenario.dataset)).where(AutoTestScenario.id == self.scenario_id)
            if self.user_id is not None:
                query = query.where(AutoTestScenario.user_id == self.user_id)
            result = await db.execute(query)
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

            env_config = {}
            env = None
            if self.env_id:
                env_query = select(AutoTestEnvironment).where(AutoTestEnvironment.id == self.env_id)
                if self.user_id is not None:
                    env_query = env_query.where(AutoTestEnvironment.user_id == self.user_id)
                result = await db.execute(env_query)
                env = result.scalar_one_or_none()
            else:
                env_query = select(AutoTestEnvironment).where(AutoTestEnvironment.is_default.is_(True))
                if self.user_id is not None:
                    env_query = env_query.where(AutoTestEnvironment.user_id == self.user_id)
                result = await db.execute(env_query)
                env = result.scalar_one_or_none()
                if not env:
                    fallback_query = select(AutoTestEnvironment)
                    if self.user_id is not None:
                        fallback_query = fallback_query.where(AutoTestEnvironment.user_id == self.user_id)
                    result = await db.execute(fallback_query)
                    env = result.scalars().first()

            if env:
                env_config = env.variables if isinstance(env.variables, dict) else {}
                if env.base_url:
                    env_config["base_url"] = env.base_url

            for row_index, row_data in enumerate(rows):
                iteration_result = await self._execute_iteration(
                    db=db, scenario=scenario, columns=columns,
                    row_data=row_data, row_index=row_index, env_config=env_config
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
        self, db, scenario, columns: List[str], row_data: List[Any],
        row_index: int, env_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        iteration_start_time = time.time()

        row_vars = {}
        for col_name, value in zip(columns, row_data):
            row_vars[col_name] = value

        # 迭代前记录当前全局变量的 key 集合，用于迭代后清理
        from fastapi_backend.services.autotest_execution import _get_global_variables_cached, _invalidate_global_vars_cache
        pre_global_var_keys = set((await _get_global_variables_cached(self.user_id)).keys())

        engine = ScenarioExecutionEngine(self.scenario_id, self.env_id, progress_callback=self.progress_callback, user_id=self.user_id, _skip_record=True)
        engine.context_vars = dict(env_config)
        engine.context_vars.update(row_vars)
        if env_config.get("base_url"):
            engine.base_url = env_config["base_url"]
            engine.context_vars["base_url"] = env_config["base_url"]

        try:
            result = await engine.execute()
            iteration_duration = int((time.time() - iteration_start_time) * 1000)

            return {
                "iteration_index": row_index,
                "data_row": dict(zip(columns, row_data)),
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
        finally:
            # 清理本次迭代新增的全局变量，避免影响下一次迭代
            try:
                post_global_var_keys = set((await _get_global_variables_cached(self.user_id)).keys())
                new_var_keys = post_global_var_keys - pre_global_var_keys
                if new_var_keys:
                    from sqlalchemy import delete as sa_delete
                    async with async_session() as cleanup_session:
                        for var_name in new_var_keys:
                            del_stmt = sa_delete(AutoTestGlobalVariable).where(AutoTestGlobalVariable.name == var_name)
                            if self.user_id is not None:
                                del_stmt = del_stmt.where(AutoTestGlobalVariable.user_id == self.user_id)
                            else:
                                del_stmt = del_stmt.where(AutoTestGlobalVariable.user_id.is_(None))
                            await cleanup_session.execute(del_stmt)
                        await cleanup_session.commit()
                    await _invalidate_global_vars_cache(self.user_id)
                    _logger.info(f"迭代 {row_index} 清理了 {len(new_var_keys)} 个新增全局变量: {new_var_keys}")
            except Exception as cleanup_err:
                _logger.warning(f"清理迭代 {row_index} 新增全局变量失败: {cleanup_err}")


async def run_scenario_data_driven(
    scenario_id: int,
    env_id: Optional[int] = None,
    progress_callback=None,
    user_id: int = None,
) -> Dict[str, Any]:
    """数据驱动执行场景的入口函数"""
    engine = DataDrivenScenarioExecutionEngine(scenario_id, env_id, progress_callback=progress_callback, user_id=user_id)
    return await engine.execute()


async def run_scenario(
    scenario_id: int,
    env_id: Optional[int] = None,
    progress_callback=None,
    user_id: int = None,
) -> Dict[str, Any]:
    """普通场景执行入口，不要求预先配置数据集。"""
    engine = ScenarioExecutionEngine(scenario_id, env_id, progress_callback=progress_callback, user_id=user_id)
    return await engine.execute()
