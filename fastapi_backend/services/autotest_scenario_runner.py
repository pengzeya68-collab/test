"""
场景执行引擎（迁移自 auto_test_platform/services/scenario_runner.py）
核心逻辑：按顺序执行场景中的每个步骤，通过全局上下文传递变量
"""
import asyncio
import json
import logging
import subprocess
import time
import uuid
import httpx
from pathlib import Path
from typing import Dict, Any, List, Optional
from sqlalchemy import select
from sqlalchemy.orm import selectinload

_logger = logging.getLogger(__name__)


from fastapi_backend.utils.autotest_helpers import convert_to_dict, extract_jsonpath_value
from fastapi_backend.services.autotest_variable_service import save_variables_to_db
from fastapi_backend.services.autotest_report_service import write_allure_results

from fastapi_backend.core.autotest_database import async_session
from fastapi_backend.models.autotest import (
    AutoTestScenario,
    AutoTestScenarioStep,
    AutoTestCase,
    AutoTestEnvironment,
    AutoTestScenarioExecutionRecord,
)
from fastapi_backend.services.autotest_email_notifier import get_email_notifier
from fastapi_backend.utils.parser import replace_variables
from fastapi_backend.core.autotest_settings import get_settings

# 项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
AUTOTEST_DATA_DIR = PROJECT_ROOT / "fastapi_backend" / "autotest_data"





class ScenarioExecutionEngine:
    """
    场景执行引擎

    核心概念：
    - context_vars: 全局上下文字典，存储提取的变量（如 token）
    - 每一步执行完后，其 Extractors 提取的变量存入 context_vars
    - 下一步构造请求时，通过 replace_variables 自动从 context_vars 读取变量
    """

    def __init__(self, scenario_id: int, env_id: Optional[int] = None, progress_callback=None):
        self.scenario_id = scenario_id
        self.env_id = env_id
        self.context_vars: Dict[str, Any] = {}
        self.step_results: List[Dict[str, Any]] = []
        self.total_duration = 0
        self.base_url: str = ""
        self.progress_callback = progress_callback

    async def execute(self) -> Dict[str, Any]:
        """
        执行整个场景
        返回执行结果（包含完整的步骤列表和 Allure 报告链接）
        """
        start_time = time.time()
        report_url = None
        scenario_name = ""
        env_name = ""

        try:
            async with async_session() as db:
                result = await db.execute(
                    select(AutoTestScenario)
                    .options(selectinload(AutoTestScenario.steps).selectinload(AutoTestScenarioStep.api_case))
                    .where(AutoTestScenario.id == self.scenario_id)
                )
                scenario = result.scalar_one_or_none()
                if not scenario:
                    raise ValueError(f"场景 {self.scenario_id} 不存在")

                scenario_name = scenario.name

                # 加载环境变量
                env = None
                if self.env_id:
                    result = await db.execute(
                        select(AutoTestEnvironment).where(AutoTestEnvironment.id == self.env_id)
                    )
                    env = result.scalar_one_or_none()
                else:
                    result = await db.execute(
                        select(AutoTestEnvironment).where(AutoTestEnvironment.is_default == True)
                    )
                    env = result.scalar_one_or_none()
                    if not env:
                        result = await db.execute(select(AutoTestEnvironment))
                        env = result.scalars().first()

                if env:
                    env_name = env.env_name or env.name or ""
                    if isinstance(env.variables, dict):
                        self.context_vars.update(env.variables)
                    if env.base_url:
                        self.base_url = env.base_url
                        self.context_vars["base_url"] = env.base_url

                # 获取所有启用的步骤并排序
                all_steps = sorted([s for s in scenario.steps if s.is_active], key=lambda x: x.step_order)

                total_steps = len(all_steps)

                if self.progress_callback:
                    self.progress_callback(0, total_steps, '加载场景和环境中...')

                for idx, step in enumerate(all_steps):
                    step_name = step.api_case.name if step.api_case else f"Step {step.step_order}"
                    if self.progress_callback:
                        self.progress_callback(idx, total_steps, f'执行: {step_name}')

                    try:
                        step_result = await self._execute_step(db, step)
                        if not step_result.get("success", False):
                            step_result["status"] = "failed"
                            self.step_results.append(step_result)
                            self.total_duration += step_result.get("duration", 0)
                        else:
                            step_result["status"] = "success"
                            self.step_results.append(step_result)
                            self.total_duration += step_result.get("duration", 0)

                        if self.progress_callback:
                            self.progress_callback(idx + 1, total_steps, f'完成: {step_name}')

                    except AssertionError as e:
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

                        if self.progress_callback:
                            self.progress_callback(idx + 1, total_steps, f'失败: {step_name}')

                    except Exception as e:
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

                        if self.progress_callback:
                            self.progress_callback(idx + 1, total_steps, f'异常: {step_name}')

        finally:
            overall_duration = int((time.time() - start_time) * 1000)

            temp_pytest_dir = AUTOTEST_DATA_DIR / "temp_pytest_tests"
            allure_results_dir = AUTOTEST_DATA_DIR / "allure-results" / f"scenario_{self.scenario_id}"
            report_dir = AUTOTEST_DATA_DIR / "reports" / f"scenario_{self.scenario_id}"

            temp_pytest_dir.mkdir(parents=True, exist_ok=True)
            allure_results_dir.mkdir(parents=True, exist_ok=True)
            report_dir.mkdir(parents=True, exist_ok=True)

            history_id = str(uuid.uuid4())[:8]

            test_file_path = self._generate_pytest_test_file(temp_pytest_dir, scenario_name, history_id)
            self._run_pytest_and_generate_report(test_file_path, str(allure_results_dir), str(report_dir))

            index_html = report_dir / "index.html"
            if index_html.exists():
                report_url = f"/reports/scenario_{self.scenario_id}/index.html"
            else:
                report_url = None

        # 统计
        total_steps = len(self.step_results)
        success_steps = len([r for r in self.step_results if r.get("status") == "success"])
        failed_steps = len([r for r in self.step_results if r.get("status") == "failed"])
        skipped_steps = len([r for r in self.step_results if r.get("status") == "skipped"])

        # 保存执行记录到数据库
        async with async_session() as db:
            if failed_steps > 0:
                status = "failed"
            elif success_steps == total_steps:
                status = "success"
            else:
                status = "error"

            record = AutoTestScenarioExecutionRecord(
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

            # 保存完整的步骤结果到 JSON 文件
            step_results_file = AUTOTEST_DATA_DIR / "step_results" / f"scenario_{self.scenario_id}_record_{record.id}.json"
            step_results_file.parent.mkdir(parents=True, exist_ok=True)
            with open(step_results_file, "w", encoding="utf-8") as f:
                json.dump(self.step_results, f, ensure_ascii=False, indent=2, default=str)

        # 邮件通知
        settings = get_settings()
        admin_email = getattr(settings, "EMAIL_ADMIN_TO", None)
        if admin_email and report_url:
            notifier = get_email_notifier()
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
                    base_url=getattr(settings, "BASE_URL", ""),
                )
            )

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
            "execution_record_id": record.id if 'record' in locals() else None,
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
            passed_assertions = assertions.get("passed", 0)
            total_assertions = assertions.get("total", 0)

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
                    step_error = error or "; ".join(assert_messages) or f"期望 2xx/3xx, 实际返回 {status_code}"

            step_error_escaped = step_error.replace('\\', '\\\\').replace('"', '\\"').replace('\n', ' ').replace("'", "\\'")
            step_name_escaped = step_name.replace('\\', '\\\\').replace('"', '\\"').replace("'", "\\'")

            if step_status == "failed":
                assert_block = f'        assert False, "步骤{i_plus_1}失败: {step_error_escaped}"'
            else:
                assert_block = '        pass'

            step_method = '''
    @allure.title("用例{i_plus_1}: {step_name_escaped}")
    def test_step_{i_plus_1}(self):
        """[{method}] {step_name_escaped}"""
        with allure.step("1. 发起HTTP请求: {method} {url}"):
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
    step_name_escaped=step_name_escaped,
    method=method,
    url=url,
    headers=json.dumps(headers, ensure_ascii=False),
    payload=json.dumps(payload, ensure_ascii=False),
    status_code=status_code,
    response_time=response_time,
    response_body_quoted=json.dumps(response_body[:2000] if response_body else "", ensure_ascii=False),
    assert_block=assert_block
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
    scenario_name=scenario_name,
    scenario_id=self.scenario_id,
    history_id=history_id,
    history_id_quoted=repr(str(history_id)),
    len_steps=len(self.step_results),
    methods_joined=methods_joined
)
        return test_code

    def _run_pytest_and_generate_report(self, test_file_path: Path, allure_results_dir: str, report_dir: str) -> bool:
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

            result = subprocess.run(cmd1, capture_output=True, text=True, timeout=120,
                                    cwd=str(test_file_path.parent), shell=True)

            result_files = list(Path(allure_results_dir_abs).glob("*.json"))

            if len(result_files) == 0 and result.returncode != 0 and "No module named pytest" in result.stderr:
                python_dir = Path(sys.executable).parent
                pytest_exe = python_dir / "Scripts" / "pytest.exe"

                if pytest_exe.exists():
                    cmd2 = [str(pytest_exe), str(test_file_path.absolute()),
                            f"--alluredir={allure_results_dir_abs}", "-v", "--tb=short"]
                    result = subprocess.run(cmd2, capture_output=True, text=True, timeout=120,
                                            cwd=str(test_file_path.parent), shell=True)
                    result_files = list(Path(allure_results_dir_abs).glob("*.json"))

                if len(result_files) == 0:
                    cmd3 = ["pytest", str(test_file_path.absolute()),
                            f"--alluredir={allure_results_dir_abs}", "-v", "--tb=short"]
                    result = subprocess.run(cmd3, capture_output=True, text=True, timeout=120,
                                            cwd=str(test_file_path.parent), shell=True)
                    result_files = list(Path(allure_results_dir_abs).glob("*.json"))

            if len(result_files) == 0:
                install_cmd = [sys.executable, "-m", "pip", "install", "pytest", "allure-pytest"]
                install_result = subprocess.run(install_cmd, capture_output=True, text=True, shell=True)
                if install_result.returncode == 0:
                    cmd_retry = [sys.executable, "-m", "pytest", str(test_file_path.absolute()),
                                 f"--alluredir={allure_results_dir_abs}", "-v", "--tb=short"]
                    result = subprocess.run(cmd_retry, capture_output=True, text=True, timeout=300,
                                            cwd=str(test_file_path.parent), shell=True)
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

            report_result = subprocess.run(
                ["allure", "generate", allure_results_dir_abs, "-o", report_dir_abs, "--clean"],
                capture_output=True, text=True, timeout=60, shell=True
            )

            if report_result.returncode == 0:
                index_html = Path(report_dir_abs) / "index.html"
                return index_html.exists()
            return False

        except Exception:
            return False

    def write_allure_results(self, allure_results_dir: Path, scenario_name: str, history_id: str, start_time: float, duration: int):
        """已废弃，保留兼容"""
        pass

    async def _execute_step(self, db, step: AutoTestScenarioStep) -> Dict[str, Any]:
        api_case = step.api_case
        if api_case is None:
            return {
                "step_order": step.step_order,
                "step_name": step.step_name or f"步骤{step.step_order}",
                "status": "error",
                "error": f"关联的接口用例不存在 (api_case_id={step.api_case_id})",
                "assertion_results": [],
                "variable_extractions": [],
            }
        step_start_time = time.time()

        try:
            request_config = {
                "method": api_case.method,
                "url": api_case.url,
                "headers": api_case.headers or {},
                "body": getattr(api_case, 'body', None) or getattr(api_case, 'payload', None) or "",
                "payload": getattr(api_case, 'body', None) or getattr(api_case, 'payload', None) or "",
            }

            if step.variable_overrides:
                overrides = step.variable_overrides
                if "url" in overrides:
                    request_config["url"] = overrides["url"]
                if "headers" in overrides:
                    request_config["headers"].update(overrides["headers"])
                if "payload" in overrides:
                    request_config["payload"].update(overrides["payload"])

            all_vars = dict(self.context_vars)
            request_config["url"] = replace_variables(request_config["url"], all_vars)
            request_config["headers"] = replace_variables(request_config["headers"], all_vars)
            request_config["payload"] = replace_variables(request_config["payload"], all_vars)

            if not request_config["url"].startswith(("http://", "https://")):
                if self.base_url:
                    request_config["url"] = self.base_url.rstrip("/") + "/" + request_config["url"].lstrip("/")

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

            req_kwargs = {"method": method, "url": url}

            if raw_payload:
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
                    final_headers['Content-Type'] = 'application/json'

            req_kwargs["headers"] = final_headers

            if not raw_payload and 'application/json' in final_headers.get('Content-Type', ''):
                req_kwargs["json"] = {}

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.request(**req_kwargs)

            step_duration = int((time.time() - step_start_time) * 1000)

            # 默认断言：状态码 >= 400 视为失败
            assertions = api_case.assert_rules
            has_status_code_assertion = False
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

            if response.status_code >= 400:
                raise AssertionError(f"默认断言失败: 期望 2xx/3xx (< 400), 实际返回 {response.status_code}")

            # 解析响应
            response_data = {
                "status": response.status_code,
                "body": response.text,
                "headers": dict(response.headers),
            }
            try:
                response_json = response.json()
                response_data["json"] = response_json
            except Exception:
                pass

            # 执行断言
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

            if assertions:
                total_assertions = len(assertions)
                for assertion in assertions:
                    passed, reason = self._check_assertion(assertion, response_data)
                    if passed:
                        passed_assertions += 1
                    else:
                        failed_assertions.append({"assertion": assertion, "reason": reason})

            # 提取变量
            extractors = getattr(api_case, 'extractors', None) or []
            self._extract_variables(extractors, response_data)

            step_result = {
                "step_id": step.id,
                "step_order": step.step_order,
                "api_case_id": api_case.id,
                "api_case_name": api_case.name,
                "method": api_case.method,
                "url": request_config["url"],
                "headers": final_headers,
                "payload": raw_payload if isinstance(raw_payload, dict) else (json.loads(raw_payload) if raw_payload and raw_payload.strip() else {}),
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

        except AssertionError:
            raise
        except Exception:
            raise

    def _get_initial_vars(self) -> set:
        return set()

    def _check_assertion(self, assertion: Dict, response_data: Dict) -> tuple:
        field = assertion.get("field") or assertion.get("target", "")
        operator = assertion.get("operator") or assertion.get("condition", "equals")
        expected = assertion.get("expectedValue") or assertion.get("value", "")
        expression = assertion.get("expression", "")

        try:
            if field == "status_code":
                actual = response_data.get("status", 0)
            elif field == "body":
                actual = response_data.get("body", "")
            elif expression:
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
                parts = field.split(".", 1)
                if len(parts) == 2 and isinstance(response_data.get("json"), dict):
                    actual = response_data["json"].get(parts[1], "")
                else:
                    actual = ""
            else:
                actual = ""

            op_map = {
                "eq": "equals", "equals": "equals", "equal": "equals",
                "ne": "not_equals", "not_equals": "not_equals", "not_equal": "not_equals",
                "contains": "contains", "not_contains": "not_contains",
                "gt": "gt", "lt": "lt", "regex": "regex", "match": "regex"
            }
            operator = op_map.get(operator, operator)

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
                    passed = 200 <= actual < 400
            else:
                passed = False

            return passed, "" if passed else f"期望 {expected}，实际 {actual}"

        except Exception as e:
            return False, f"断言检查异常: {str(e)}"

    def _extract_variables(self, extractors: List[Dict], response_data: Dict):
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
                    json_data = response_data.get("json")
                    if json_data is not None:
                        value = extract_jsonpath_value(json_data, expression, default_value)
                elif extractor_type == "regex":
                    import re
                    match = re.search(expression, body)
                    if match:
                        value = match.group(1) if match.groups() else match.group(0)
            except Exception as e:
                _logger.warning(f"变量提取失败 {var_name}: {str(e)}")

            self.context_vars[var_name] = value

        # 🔥 修复：将提取的变量持久化到全局变量表
        if self.context_vars:
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(save_variables_to_db(dict(self.context_vars)))
            except RuntimeError:
                _logger.debug("无运行中的事件循环，跳过变量持久化")



    def __init__(self, scenario_id: int, env_id: Optional[int] = None):
        self.scenario_id = scenario_id
        self.env_id = env_id
        self.iterations: List[Dict[str, Any]] = []
        self.total_duration = 0

    async def execute(self) -> Dict[str, Any]:
        start_time = time.time()

        async with async_session() as db:
            result = await db.execute(
                select(AutoTestScenario)
                .options(
                    selectinload(AutoTestScenario.steps).selectinload(AutoTestScenarioStep.api_case),
                    selectinload(AutoTestScenario.dataset)
                )
                .where(AutoTestScenario.id == self.scenario_id)
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

            env_config = {}
            env = None
            if self.env_id:
                result = await db.execute(
                    select(AutoTestEnvironment).where(AutoTestEnvironment.id == self.env_id)
                )
                env = result.scalar_one_or_none()
            else:
                result = await db.execute(
                    select(AutoTestEnvironment).where(AutoTestEnvironment.is_default == True)
                )
                env = result.scalar_one_or_none()
                if not env:
                    result = await db.execute(select(AutoTestEnvironment))
                    env = result.scalars().first()

            if env:
                env_config = env.variables if isinstance(env.variables, dict) else {}

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

        engine = ScenarioExecutionEngine(self.scenario_id, self.env_id)
        engine.context_vars = dict(env_config)
        engine.context_vars.update(row_vars)

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


async def run_scenario_data_driven(
    scenario_id: int,
    env_id: Optional[int] = None
) -> Dict[str, Any]:
    """数据驱动执行场景的入口函数"""
    engine = DataDrivenScenarioExecutionEngine(scenario_id, env_id)
    return await engine.execute()
