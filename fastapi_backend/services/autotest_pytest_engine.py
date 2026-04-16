"""
Pytest 数据驱动执行引擎（迁移自 auto_test_platform/services/pytest_engine.py）

核心功能：
1. 接收场景步骤 (Steps) 和驱动数据 (DataMatrix)
2. 动态生成 Pytest 测试文件，使用 @pytest.mark.parametrize
3. 上下文变量替换机制 ({{变量名}})
4. 提取器 (Extractors) 机制，上下文传递给下一步
5. Allure 集成与报告生成
"""
import os
import re
import json
import time
import asyncio
import logging
import yaml
import requests
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

_logger = logging.getLogger(__name__)

# 项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
AUTOTEST_DATA_DIR = PROJECT_ROOT / "fastapi_backend" / "autotest_data"


class PytestDataDrivenEngine:
    """
    基于 Pytest 的数据驱动执行引擎
    """

    def __init__(self, scenario_id: int, scenario_name: str = "测试场景"):
        self.scenario_id = scenario_id
        self.scenario_name = scenario_name
        self.base_dir = AUTOTEST_DATA_DIR
        self.temp_dir = self.base_dir / "temp_run_data"
        self.allure_results_dir = self.base_dir / "allure-results" / f"scenario_{scenario_id}"
        self.report_dir = self.base_dir / "reports" / f"scenario_{scenario_id}"

        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.allure_results_dir.mkdir(parents=True, exist_ok=True)
        self.report_dir.mkdir(parents=True, exist_ok=True)

        self.run_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    def execute(self, steps: List[Dict], data_matrix: Dict[str, Any], env_vars: Dict[str, Any] = None) -> Dict[str, Any]:
        start_time = time.time()

        try:
            data_file = self._generate_data_file(steps, data_matrix, env_vars)
            test_file = self._generate_test_file(steps, data_matrix, env_vars)
            result = self._run_pytest(test_file, data_file)
            report_url = self._generate_allure_report()

            overall_duration = int((time.time() - start_time) * 1000)

            return {
                "success": result["returncode"] == 0,
                "total_iterations": len(data_matrix.get("rows", [])),
                "passed": result["passed"],
                "failed": result["failed"],
                "duration": overall_duration,
                "report_url": report_url,
                "stdout": result["stdout"],
                "stderr": result["stderr"],
                "test_file": str(test_file),
                "data_file": str(data_file)
            }

        except Exception as e:
            overall_duration = int((time.time() - start_time) * 1000)
            return {
                "success": False,
                "error": str(e),
                "duration": overall_duration,
                "report_url": None
            }

    def _generate_data_file(self, steps: List[Dict], data_matrix: Dict[str, Any], env_vars: Dict[str, Any] = None) -> Path:
        data_file = self.temp_dir / f"data_scenario_{self.scenario_id}_{self.run_id}.yaml"
        data = {
            "scenario_id": self.scenario_id,
            "scenario_name": self.scenario_name,
            "env_vars": env_vars or {},
            "steps": steps,
            "columns": data_matrix.get("columns", []),
            "rows": data_matrix.get("rows", [])
        }
        with open(data_file, "w", encoding="utf-8") as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False)
        return data_file

    def _generate_test_file(self, steps: List[Dict], data_matrix: Dict[str, Any], env_vars: Dict[str, Any] = None) -> Path:
        test_file = self.temp_dir / f"test_scenario_{self.scenario_id}_{self.run_id}.py"
        test_code = self._generate_test_code(steps, data_matrix, env_vars)
        with open(test_file, "w", encoding="utf-8") as f:
            f.write(test_code)
        return test_file

    def _generate_test_code(self, steps: List[Dict], data_matrix: Dict[str, Any], env_vars: Dict[str, Any] = None) -> str:
        columns = data_matrix.get("columns", [])
        steps_json = json.dumps(steps, ensure_ascii=False, indent=8)
        env_vars_json = json.dumps(env_vars or {}, ensure_ascii=False, indent=8)

        code = f'''"""
自动生成的场景测试文件
场景: {self.scenario_name}
生成时间: {datetime.now().isoformat()}
"""
import pytest
import yaml
import requests
import time
import allure
import json
import re
from pathlib import Path


SCENARIO_ID = {self.scenario_id}
SCENARIO_NAME = "{self.scenario_name}"
ENV_VARS = {env_vars_json}
STEPS = {steps_json}
COLUMNS = {json.dumps(columns)}


def find_variables(text):
    if not isinstance(text, str):
        return []
    return list(set(re.findall(r'\\{{(\\w+)\\}}', text)))


def replace_variables_in_text(text, variables):
    if not isinstance(text, str):
        return text
    def replace_match(match):
        var_name = match.group(1)
        return str(variables.get(var_name, match.group(0)))
    return re.sub(r'\\{{(\\w+)\\}}', replace_match, text)


def replace_variables(obj, variables):
    if isinstance(obj, str):
        return replace_variables_in_text(obj, variables)
    elif isinstance(obj, dict):
        return {{key: replace_variables(value, variables) for key, value in obj.items()}}
    elif isinstance(obj, list):
        return [replace_variables(item, variables) for item in obj]
    else:
        return obj


def extract_value(response_data, expression, extractor_type="jsonpath", default=""):
    try:
        if extractor_type == "jsonpath":
            if isinstance(response_data, dict):
                return response_data.get(expression, default)
        elif extractor_type == "regex":
            body = response_data.get("body", "") if isinstance(response_data, dict) else str(response_data)
            match = re.search(expression, body)
            if match:
                return match.group(1) if match.groups() else match.group(0)
    except Exception:
        pass
    return default


def check_assertion(actual, operator, expected):
    try:
        if operator == "equals" or operator == "eq":
            return str(actual) == str(expected)
        elif operator == "not_equals":
            return str(actual) != str(expected)
        elif operator == "contains":
            return str(expected) in str(actual)
        elif operator == "not_contains":
            return str(expected) not in str(actual)
        elif operator == "gt":
            return float(actual) > float(expected)
        elif operator == "lt":
            return float(actual) < float(expected)
        elif operator == "regex":
            return bool(re.search(str(expected), str(actual)))
        return False
    except Exception:
        return False


@pytest.fixture(scope="session")
def test_data(request):
    data_path = request.config.getoption("--data_file")
    if not data_path:
        pytest.fail("必须指定 --data_file 参数")
    with open(data_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="session")
def allure_dir(request):
    return request.config.getoption("--alluredir") or "./allure-results"


def test_scenario_iteration(test_data, allure_dir, request):
    iteration_index = 0
    iteration_id = request.node.callspec.id if hasattr(request.node, 'callspec') else "0"
    try:
        iteration_index = int(iteration_id.split("-")[-1]) if iteration_id else 0
    except Exception:
        iteration_index = 0

    columns = test_data.get("columns", [])
    rows = test_data.get("rows", [])
    current_row = rows[iteration_index] if iteration_index < len(rows) else []

    row_vars = dict(zip(columns, current_row))
    row_vars.update(test_data.get("env_vars", {{}}))

    context_vars = {{}}
    steps = test_data.get("steps", [])

    with allure.step(f"[迭代 #{{iteration_index + 1}}] {{' | '.join([f'{{k}}={{v}}' for k, v in row_vars.items()])}}"):
        pass

    iteration_passed = True
    iteration_errors = []

    for step_idx, step in enumerate(steps):
        step_order = step.get("step_order", step_idx)
        step_name = step.get("name", f"步骤 {{step_order}}")
        method = step.get("method", "GET").upper()
        url = step.get("url", "")
        headers = step.get("headers", {{}})
        payload = step.get("payload", {{}})
        assert_rules = step.get("assert_rules", {{}})
        extractors = step.get("extractors", [])
        variable_overrides = step.get("variable_overrides", {{}}) or {{}}

        all_vars = {{}}
        all_vars.update(row_vars)
        all_vars.update(context_vars)
        all_vars.update(variable_overrides)
        all_vars.update(test_data.get("env_vars", {{}}))

        url = replace_variables(url, all_vars)
        headers = replace_variables(headers, all_vars)
        payload = replace_variables(payload, all_vars)

        step_num = step_idx + 1

        with allure.step(f"[步骤 {{step_num}}] {{method}} {{url}}"):
            allure.attach(
                json.dumps({{"url": url, "method": method, "headers": headers, "payload": payload}}, ensure_ascii=False, indent=2),
                name=f"[{{step_num}}] 请求信息",
                attachment_type=allure.attachment_type.JSON
            )

            step_start = time.time()

            try:
                if method == "GET":
                    response = requests.get(url, headers=headers, timeout=30)
                elif method == "POST":
                    response = requests.post(url, headers=headers, json=payload, timeout=30)
                elif method == "PUT":
                    response = requests.put(url, headers=headers, json=payload, timeout=30)
                elif method == "DELETE":
                    response = requests.delete(url, headers=headers, timeout=30)
                elif method == "PATCH":
                    response = requests.patch(url, headers=headers, json=payload, timeout=30)
                else:
                    raise ValueError(f"不支持的请求方法: {{method}}")

                step_duration = int((time.time() - step_start) * 1000)

                if response.status_code >= 400:
                    try:
                        response_json = response.json()
                        response_data = {{"status": response.status_code, "body": response.text, "json": response_json}}
                    except Exception:
                        response_data = {{"status": response.status_code, "body": response.text}}
                    allure.attach(
                        json.dumps({{"status": response.status_code, "duration_ms": step_duration, "body": str(response_data)[:500]}}, ensure_ascii=False, indent=2),
                        name=f"[{{step_num}}] 响应信息",
                        attachment_type=allure.attachment_type.JSON
                    )
                    raise AssertionError(f"默认断言失败: 期望 2xx/3xx (< 400), 实际返回 {{{response.status_code}}}")

                try:
                    response_json = response.json()
                    response_data = {{"status": response.status_code, "body": response.text, "json": response_json}}
                except Exception:
                    response_data = {{"status": response.status_code, "body": response.text}}

                allure.attach(
                    json.dumps({{"status": response.status_code, "duration_ms": step_duration, "body": str(response_data)[:500]}}, ensure_ascii=False, indent=2),
                    name=f"[{{step_num}}] 响应信息",
                    attachment_type=allure.attachment_type.JSON
                )

                with allure.step(f"[{{step_num}}] 执行断言"):
                    assertion_failed = False
                    assertion_errors = []

                    if "status_code" in assert_rules:
                        expected = assert_rules["status_code"]
                        if response.status_code != expected:
                            assertion_failed = True
                            assertion_errors.append(f"状态码: 期望 {{expected}}, 实际 {{response.status_code}}")

                    if "json_path" in assert_rules and isinstance(response_json, dict):
                        for path, rule in assert_rules["json_path"].items():
                            keys = path.replace("$.", "").split(".")
                            value = response_json
                            for key in keys:
                                if isinstance(value, dict) and key in value:
                                    value = value[key]
                                else:
                                    value = None
                                    break
                            for op, expected_val in rule.items():
                                if not check_assertion(value, op, expected_val):
                                    assertion_failed = True
                                    assertion_errors.append(f"{{path}} {{op}} {{expected_val}}, 实际: {{value}}")

                    allure.attach(
                        "\\n".join(assertion_errors) if assertion_errors else "所有断言通过",
                        name=f"[{{step_num}}] 断言结果",
                        attachment_type=allure.attachment_type.TEXT
                    )

                    if assertion_failed:
                        iteration_passed = False
                        iteration_errors.extend(assertion_errors)

                if extractors:
                    with allure.step(f"[{{step_num}}] 提取变量"):
                        for extractor in extractors:
                            var_name = extractor.get("variableName") or extractor.get("variable_name")
                            expr = extractor.get("expression")
                            ext_type = extractor.get("extractorType", "jsonpath")
                            default = extractor.get("defaultValue", "")
                            if not var_name or not expr:
                                continue
                            value = extract_value(response_data, expr, ext_type, default)
                            context_vars[var_name] = value
                            allure.attach(f"{{var_name}} = {{value}}", name=f"[{{step_num}}] 提取: {{var_name}}", attachment_type=allure.attachment_type.TEXT)

            except requests.exceptions.Timeout:
                iteration_passed = False
                iteration_errors.append(f"[步骤 {{step_num}}] 请求超时")
            except requests.exceptions.ConnectionError as e:
                iteration_passed = False
                iteration_errors.append(f"[步骤 {{step_num}}] 连接失败: {{str(e)}}")
            except Exception as e:
                iteration_passed = False
                iteration_errors.append(f"[步骤 {{step_num}}] {{str(e)}}")

    if not iteration_passed:
        pytest.fail("迭代失败: " + "; ".join(iteration_errors))


def pytest_configure(config):
    config.addinivalue_line("markers", "scenario: mark test as scenario execution")


def pytest_addoption(parser):
    parser.addoption("--data_file", action="store", default=None, help="YAML 测试数据文件路径")
'''
        return code

    def _run_pytest(self, test_file: Path, data_file: Path) -> Dict[str, Any]:
        import sys
        import subprocess

        allure_results_dir_abs = str(self.allure_results_dir.absolute())

        import shutil
        shutil.rmtree(str(self.allure_results_dir), ignore_errors=True)
        self.allure_results_dir.mkdir(parents=True, exist_ok=True)

        python_executable = sys.executable
        cmd1 = [
            python_executable, "-m", "pytest", str(test_file),
            f"--data_file={data_file}", f"--alluredir={allure_results_dir_abs}",
            "-v", "--tb=short", "--no-header", "-p", "no:warnings"
        ]

        result = subprocess.run(cmd1, capture_output=True, text=True,
                                cwd=str(self.temp_dir))
        result_files = list(self.allure_results_dir.glob("*.json"))

        if len(result_files) == 0 and result.returncode != 0 and "No module named pytest" in result.stderr:
            python_dir = Path(sys.executable).parent
            pytest_exe = python_dir / "Scripts" / "pytest.exe"

            if pytest_exe.exists():
                cmd2 = [str(pytest_exe), str(test_file), f"--data_file={data_file}",
                        f"--alluredir={allure_results_dir_abs}", "-v", "--tb=short", "--no-header", "-p", "no:warnings"]
                result = subprocess.run(cmd2, capture_output=True, text=True,
                                        cwd=str(self.temp_dir))
                result_files = list(self.allure_results_dir.glob("*.json"))

            if len(result_files) == 0:
                cmd3 = ["pytest", str(test_file), f"--data_file={data_file}",
                        f"--alluredir={allure_results_dir_abs}", "-v", "--tb=short", "--no-header", "-p", "no:warnings"]
                result = subprocess.run(cmd3, capture_output=True, text=True,
                                        cwd=str(self.temp_dir))
                result_files = list(self.allure_results_dir.glob("*.json"))

        passed = 0
        failed = 0
        for line in result.stdout.split("\n"):
            if "passed" in line.lower():
                match = re.search(r"(\d+) passed", line)
                if match:
                    passed = int(match.group(1))
            if "failed" in line.lower():
                match = re.search(r"(\d+) failed", line)
                if match:
                    failed = int(match.group(1))

        return {
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "passed": passed,
            "failed": failed
        }

    def _generate_allure_report(self) -> str:
        try:
            import shutil
            result_files = list(self.allure_results_dir.glob("*.json"))
            if not result_files:
                return None

            old_report_history = self.report_dir / "history"
            new_results_history = self.allure_results_dir / "history"
            if old_report_history.exists() and old_report_history.is_dir():
                if new_results_history.exists():
                    shutil.rmtree(str(new_results_history))
                shutil.copytree(str(old_report_history), str(new_results_history))

            cmd_result = subprocess.run(
                ["allure", "generate", str(self.allure_results_dir.absolute()),
                 "-o", str(self.report_dir.absolute()), "--clean"],
                capture_output=True, text=True, timeout=60
            )

            if cmd_result.returncode == 0:
                index_html = self.report_dir / "index.html"
                if index_html.exists():
                    return f"/reports/scenario_{self.scenario_id}/index.html"
            return None
        except Exception:
            return None

    def cleanup(self):
        import shutil
        try:
            for pattern in [f"*_{self.run_id}*"]:
                for f in self.temp_dir.glob(pattern):
                    f.unlink()
            cutoff = time.time() - 3600
            for f in self.temp_dir.iterdir():
                if f.is_file() and f.stat().st_mtime < cutoff:
                    try:
                        f.unlink()
                    except OSError:
                        pass
        except Exception:
            pass


def run_scenario_pytest(scenario_id: int, scenario_name: str, steps: List[Dict], data_matrix: Dict[str, Any], env_vars: Dict[str, Any] = None) -> Dict[str, Any]:
    """执行数据驱动测试的入口函数"""
    engine = PytestDataDrivenEngine(scenario_id, scenario_name)
    result = engine.execute(steps, data_matrix, env_vars)
    engine.cleanup()
    return result
