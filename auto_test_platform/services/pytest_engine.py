"""
Pytest 数据驱动执行引擎
按照用户 Prompt 2 要求实现

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
import subprocess
import yaml
import requests
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime


# ========== 核心引擎类 ==========

class PytestDataDrivenEngine:
    """
    基于 Pytest 的数据驱动执行引擎

    工作流程：
    1. 接收场景数据（steps + data_matrix）
    2. 动态生成临时测试文件和数据文件
    3. 使用 subprocess 调用 pytest --data_file=xxx --alluredir=xxx
    4. 解析 pytest 输出，返回执行结果
    5. 生成 Allure 报告

    数据流：
    - steps: List[StepConfig] - 场景中的步骤列表
    - data_matrix: {columns: [...], rows: [[...], [...]]} - 数据矩阵
    - context_vars: Dict - 上下文变量（跨步骤传递）
    """

    def __init__(self, scenario_id: int, scenario_name: str = "测试场景"):
        self.scenario_id = scenario_id
        self.scenario_name = scenario_name
        self.base_dir = Path(__file__).parent.parent.absolute()
        self.temp_dir = self.base_dir / "temp_run_data"
        self.allure_results_dir = self.base_dir / "allure-results" / f"scenario_{scenario_id}"
        self.report_dir = self.base_dir / "reports" / f"scenario_{scenario_id}"

        # 确保目录存在
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.allure_results_dir.mkdir(parents=True, exist_ok=True)
        self.report_dir.mkdir(parents=True, exist_ok=True)

        # 生成唯一标识
        self.run_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    def execute(self, steps: List[Dict], data_matrix: Dict[str, Any], env_vars: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        执行数据驱动测试

        Args:
            steps: 步骤配置列表，每个步骤包含:
                {
                    "step_order": 1,
                    "name": "登录接口",
                    "method": "POST",
                    "url": "/api/login",
                    "headers": {...},
                    "payload": {...},
                    "assert_rules": {...},
                    "extractors": [...],  # 可选，提取器列表
                    "variable_overrides": {...}  # 可选，局部变量覆盖
                }
            data_matrix: 数据矩阵，包含:
                {
                    "columns": ["username", "password", "expected"],
                    "rows": [["admin", "123456", "success"], ["test", "wrong", "fail"]]
                }
            env_vars: 环境变量字典（可选）

        Returns:
            执行结果字典
        """
        start_time = time.time()

        try:
            # 1. 生成数据文件
            data_file = self._generate_data_file(steps, data_matrix, env_vars)

            # 2. 生成测试文件
            test_file = self._generate_test_file(steps, data_matrix, env_vars)

            # 3. 调用 pytest 执行
            result = self._run_pytest(test_file, data_file)

            # 4. 生成 Allure 报告
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
        """
        生成 YAML 数据文件

        文件格式供 @pytest.mark.parametrize 使用
        """
        data_file = self.temp_dir / f"data_scenario_{self.scenario_id}_{self.run_id}.yaml"

        # 构建完整的数据结构
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
        """
        动态生成 Pytest 测试文件

        使用 @pytest.mark.parametrize 实现数据驱动
        每个测试函数代表一次迭代（一行数据）
        """
        test_file = self.temp_dir / f"test_scenario_{self.scenario_id}_{self.run_id}.py"

        # 生成测试函数代码
        test_code = self._generate_test_code(steps, data_matrix, env_vars)

        with open(test_file, "w", encoding="utf-8") as f:
            f.write(test_code)

        return test_file

    def _generate_test_code(self, steps: List[Dict], data_matrix: Dict[str, Any], env_vars: Dict[str, Any] = None) -> str:
        """
        生成测试代码字符串

        核心设计：
        - 使用 pytest.mark.parametrize 读取 YAML 中的 rows
        - 每个迭代执行所有步骤
        - 通过 context_vars 在步骤间传递变量
        - 使用 allure.attach 记录详细信息
        """

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


# ========== 全局配置 ==========

SCENARIO_ID = {self.scenario_id}
SCENARIO_NAME = "{self.scenario_name}"
ENV_VARS = {env_vars_json}
STEPS = {steps_json}
COLUMNS = {json.dumps(columns)}


# ========== 辅助函数 ==========

def find_variables(text):
    """查找字符串中的 {{variable_name}} 占位符"""
    if not isinstance(text, str):
        return []
    return list(set(re.findall(r'\\{{(\\w+)\\}}', text)))


def replace_variables_in_text(text, variables):
    """替换字符串中的 {{variable}} 占位符"""
    if not isinstance(text, str):
        return text

    def replace_match(match):
        var_name = match.group(1)
        return str(variables.get(var_name, match.group(0)))

    return re.sub(r'\\{{(\\w+)\\}}', replace_match, text)


def replace_variables(obj, variables):
    """递归替换对象中的所有 {{variable}} 占位符"""
    if isinstance(obj, str):
        return replace_variables_in_text(obj, variables)
    elif isinstance(obj, dict):
        return {{key: replace_variables(value, variables) for key, value in obj.items()}}
    elif isinstance(obj, list):
        return [replace_variables(item, variables) for item in obj]
    else:
        return obj


def extract_value(response_data, expression, extractor_type="jsonpath", default=""):
    """从响应中提取值"""
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
    """执行断言并返回结果"""
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
    except:
        return False


# ========== Pytest Fixtures ==========

@pytest.fixture(scope="session")
def test_data(request):
    """加载测试数据"""
    data_path = request.config.getoption("--data_file")
    if not data_path:
        pytest.fail("必须指定 --data_file 参数")

    with open(data_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="session")
def allure_dir(request):
    """获取 Allure 结果目录"""
    return request.config.getoption("--alluredir") or "./allure-results"


# ========== 测试函数 ==========

def test_scenario_iteration(test_data, allure_dir, request):
    """
    数据驱动场景测试

    每个迭代使用 data_matrix 中的一行数据
    上下文变量在步骤间传递
    """
    # 获取当前迭代的行索引（从 pytest id 中提取）
    iteration_index = 0
    iteration_id = request.node.callspec.id if hasattr(request.node, 'callspec') else "0"
    try:
        iteration_index = int(iteration_id.split("-")[-1]) if iteration_id else 0
    except:
        iteration_index = 0

    # 获取当前行数据
    columns = test_data.get("columns", [])
    rows = test_data.get("rows", [])
    current_row = rows[iteration_index] if iteration_index < len(rows) else []

    # 构建当前迭代的变量字典（从数据行）
    row_vars = dict(zip(columns, current_row))
    # 合并环境变量
    row_vars.update(test_data.get("env_vars", {{}}))

    # 上下文字典（跨步骤传递）
    context_vars = {{}}

    steps = test_data.get("steps", [])

    # Allure 报告 - 迭代信息
    with allure.step(f"[迭代 #{iteration_index + 1}] {{' | '.join([f'{{k}}={{v}}' for k, v in row_vars.items()])}}"):
        pass

    iteration_passed = True
    iteration_errors = []

    # 按顺序执行每个步骤
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

        # 合并变量：row_vars -> context_vars -> 步骤覆盖 -> env_vars
        all_vars = {{}}
        all_vars.update(row_vars)  # 数据行变量
        all_vars.update(context_vars)  # 上一步提取的变量
        all_vars.update(variable_overrides)  # 局部覆盖
        all_vars.update(test_data.get("env_vars", {{}}))  # 环境变量（包含 base_url, api_prefix 等）

        # 变量替换
        url = replace_variables(url, all_vars)
        headers = replace_variables(headers, all_vars)
        payload = replace_variables(payload, all_vars)

        with allure.step(f"[步骤 {{step_num}}] {{method}} {{url}}"):
            # 记录请求详情
            allure.attach(
                json.dumps({{"url": url, "method": method, "headers": headers, "payload": payload}}, ensure_ascii=False, indent=2),
                name=f"[{{step_num}}] 请求信息",
                attachment_type=allure.attachment_type.JSON
            )

            step_start = time.time()

            try:
                # 发送请求
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
                step_num = step_idx + 1

                # ========== Bug 1 修复：状态码拦截 - 发起请求后立即检查 ==========
                # 只要状态码 >= 400，强制抛出异常标记为失败
                if response.status_code >= 400:
                    # 解析响应
                    try:
                        response_json = response.json()
                        response_data = {{"status": response.status_code, "body": response.text, "json": response_json}}
                    except:
                        response_data = {{"status": response.status_code, "body": response.text}}
                    # 记录响应
                    allure.attach(
                        json.dumps({{"status": response.status_code, "duration_ms": step_duration, "body": str(response_data)[:500]}}, ensure_ascii=False, indent=2),
                        name=f"[{{step_num}}] 响应信息",
                        attachment_type=allure.attachment_type.JSON
                    )
                    # 强制抛出异常，标记测试失败
                    raise AssertionError(f"默认断言失败: 期望 2xx/3xx (< 400), 实际返回 {{{response.status_code}}}")
                # ========== Bug 1 修复结束 ==========

                # 解析响应
                try:
                    response_json = response.json()
                    response_data = {{"status": response.status_code, "body": response.text, "json": response_json}}
                except:
                    response_data = {{"status": response.status_code, "body": response.text}}

                # 记录响应
                allure.attach(
                    json.dumps({{"status": response.status_code, "duration_ms": step_duration, "body": str(response_data)[:500]}}, ensure_ascii=False, indent=2),
                    name=f"[{{step_num}}] 响应信息",
                    attachment_type=allure.attachment_type.JSON
                )

                # 执行断言
                with allure.step(f"[{{step_num}}] 执行断言"):
                    assertion_failed = False
                    assertion_errors = []

                    # 状态码断言
                    if "status_code" in assert_rules:
                        expected = assert_rules["status_code"]
                        if response.status_code != expected:
                            assertion_failed = True
                            assertion_errors.append(f"状态码: 期望 {{expected}}, 实际 {{response.status_code}}")

                    # JSON 路径断言
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

                # 提取变量（如果配置了 Extractors）
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

                            allure.attach(
                                f"{{var_name}} = {{value}}",
                                name=f"[{{step_num}}] 提取: {{var_name}}",
                                attachment_type=allure.attachment_type.TEXT
                            )

            except requests.exceptions.Timeout:
                iteration_passed = False
                iteration_errors.append(f"[步骤 {{step_num}}] 请求超时")
                allure.attach("请求超时", name=f"[{{step_num}}] 错误", attachment_type=allure.attachment_type.TEXT)

            except requests.exceptions.ConnectionError as e:
                iteration_passed = False
                iteration_errors.append(f"[步骤 {{step_num}}] 连接失败: {{str(e)}}")
                allure.attach(f"连接失败: {{str(e)}}", name=f"[{{step_num}}] 错误", attachment_type=allure.attachment_type.TEXT)

            except Exception as e:
                iteration_passed = False
                iteration_errors.append(f"[步骤 {{step_num}}] {{str(e)}}")
                allure.attach(str(e), name=f"[{{step_num}}] 错误", attachment_type=allure.attachment_type.TEXT)

    # 最终断言
    if not iteration_passed:
        pytest.fail("迭代失败: " + "; ".join(iteration_errors))


def pytest_configure(config):
    """注册自定义命令行参数"""
    config.addinivalue_line(
        "markers", "scenario: mark test as scenario execution"
    )


def pytest_addoption(parser):
    """添加自定义命令行参数"""
    parser.addoption(
        "--data_file",
        action="store",
        default=None,
        help="YAML 测试数据文件路径"
    )
'''

        return code

    def _run_pytest(self, test_file: Path, data_file: Path) -> Dict[str, Any]:
        """
        使用 subprocess 调用 pytest 执行测试

        Returns:
            {
                "returncode": int,
                "stdout": str,
                "stderr": str,
                "passed": int,
                "failed": int
            }
        """
        import sys
        # 兼容处理：尝试两种方式，保证在任何环境都能运行
        # 方式1: python -m pytest (使用当前 Python，能找到当前环境安装的 allure-pytest)
        # 方式2: 直接调用 pytest 命令 (当当前 Python 没有安装 pytest 但 PATH 中有时使用)

        allure_results_dir_abs = str(self.allure_results_dir.absolute())

        # 尝试 1: 使用当前 Python 解释器执行 pytest
        python_executable = sys.executable
        cmd1 = [
            python_executable,
            "-m",
            "pytest",
            str(test_file),
            f"--data_file={data_file}",
            f"--alluredir={allure_results_dir_abs}",
            "-v",
            "--tb=short",
            "--no-header",
            "-p", "no:warnings"
        ]

        print(f"[PytestEngine] 尝试方式1: {' '.join(cmd1)}")
        result = subprocess.run(
            cmd1,
            capture_output=True,
            text=True,
            cwd=str(self.temp_dir),
            shell=True  # Windows 上需要 shell=True
        )

        # 检查是否生成了结果文件
        result_files = list(self.allure_results_dir.glob("*.json"))
        print(f"[PytestEngine] 方式1 后 JSON 结果文件数量: {len(result_files)}")

        # 如果方式1失败（No module named pytest），尝试方式2和方式3
        if len(result_files) == 0 and result.returncode != 0 and "No module named pytest" in result.stderr:
            print(f"[PytestEngine] 方式1失败，尝试其他方式")

            # 方式2: 尝试从 Python 的 Scripts 目录找到 pytest.exe (Windows 常见位置)
            python_dir = Path(sys.executable).parent
            pytest_exe = python_dir / "Scripts" / "pytest.exe"

            if pytest_exe.exists():
                cmd2 = [
                    str(pytest_exe),
                    str(test_file),
                    f"--data_file={data_file}",
                    f"--alluredir={allure_results_dir_abs}",
                    "-v",
                    "--tb=short",
                    "--no-header",
                    "-p", "no:warnings"
                ]
                print(f"[PytestEngine] 尝试方式2 (Python Scripts): {' '.join(cmd2)}")
                result = subprocess.run(
                    cmd2,
                    capture_output=True,
                    text=True,
                    cwd=str(self.temp_dir),
                    shell=True
                )
                print(f"[PytestEngine] 方式2 结果: returncode={result.returncode}")
                if result.stdout:
                    print(f"[PytestEngine] 方式2 stdout:\n{result.stdout}")
                if result.stderr:
                    print(f"[PytestEngine] 方式2 stderr:\n{result.stderr}")
                result_files = list(self.allure_results_dir.glob("*.json"))
                print(f"[PytestEngine] 方式2 后 JSON 结果文件数量: {len(result_files)}")
            else:
                print(f"[PytestEngine] Scripts/pytest.exe 不存在: {pytest_exe}")

            # 如果方式2也失败，尝试方式3: 直接调用 pytest 命令 (PATH 中)
            if len(result_files) == 0:
                print(f"[PytestEngine] 尝试方式3 (PATH 中): 直接调用 pytest 命令")
                cmd3 = [
                    "pytest",
                    str(test_file),
                    f"--data_file={data_file}",
                    f"--alluredir={allure_results_dir_abs}",
                    "-v",
                    "--tb=short",
                    "--no-header",
                    "-p", "no:warnings"
                ]
                print(f"[PytestEngine] 尝试方式3: {' '.join(cmd3)}")
                result = subprocess.run(
                    cmd3,
                    capture_output=True,
                    text=True,
                    cwd=str(self.temp_dir),
                    shell=True
                )
                print(f"[PytestEngine] 方式3 结果: returncode={result.returncode}")
                if result.stdout:
                    print(f"[PytestEngine] 方式3 stdout:\n{result.stdout}")
                if result.stderr:
                    print(f"[PytestEngine] 方式3 stderr:\n{result.stderr}")
                result_files = list(self.allure_results_dir.glob("*.json"))
                print(f"[PytestEngine] 方式3 后 JSON 结果文件数量: {len(result_files)}")

        # 解析输出获取通过/失败数量
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
        """生成 Allure 报告并返回报告 URL"""
        try:
            print(f"[PytestEngine] 检查 Allure 结果目录: {self.allure_results_dir}")
            result_files = list(self.allure_results_dir.glob("*.json"))
            print(f"[PytestEngine] Allure 结果文件数量: {len(result_files)}")

            for f in result_files:
                print(f"[PytestEngine]   - {f.name} ({f.stat().st_size} bytes)")

            cmd_result = subprocess.run(
                ["allure", "generate", str(self.allure_results_dir.absolute()), "-o", str(self.report_dir.absolute()), "--clean"],
                capture_output=True,
                text=True,
                timeout=60,
                shell=True  # Windows 上需要 shell=True 才能运行 .cmd 文件
            )
            # 检查命令执行结果
            if cmd_result.stdout:
                print(f"[PytestEngine] Allure generate stdout:\n{cmd_result.stdout}")
            if cmd_result.stderr:
                print(f"[PytestEngine] Allure generate stderr:\n{cmd_result.stderr}")

            if cmd_result.returncode == 0:
                index_html = self.report_dir / "index.html"
                if index_html.exists():
                    report_url = f"/reports/scenario_{self.scenario_id}/index.html"
                    print(f"[PytestEngine] Allure 报告生成成功: {report_url}, index.html = {index_html.exists()}")
                    return report_url
                else:
                    print(f"[PytestEngine] 警告：Allure generate 返回成功，但 index.html 不存在于 {index_html}")
                    return None
            else:
                print(f"[PytestEngine] Allure 报告生成失败, returncode={cmd_result.returncode}")
                return None
        except FileNotFoundError as e:
            print(f"[PytestEngine] Allure 命令未找到，请安装 Allure: {e}")
            return None
        except Exception as e:
            print(f"[PytestEngine] Allure 报告生成异常: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    def cleanup(self):
        """清理临时文件"""
        import shutil
        try:
            # 清理本次运行的临时文件
            for pattern in [f"*_{self.run_id}*"]:
                for f in self.temp_dir.glob(pattern):
                    f.unlink()
        except Exception:
            pass


# ========== 便捷函数 ==========

def run_scenario_pytest(scenario_id: int, scenario_name: str, steps: List[Dict], data_matrix: Dict[str, Any], env_vars: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    执行数据驱动测试的入口函数

    Args:
        scenario_id: 场景 ID
        scenario_name: 场景名称
        steps: 步骤列表
        data_matrix: 数据矩阵
        env_vars: 环境变量

    Returns:
        执行结果
    """
    engine = PytestDataDrivenEngine(scenario_id, scenario_name)
    result = engine.execute(steps, data_matrix, env_vars)
    engine.cleanup()
    return result


# ========== 单元测试 ==========

if __name__ == "__main__":
    # 测试数据
    test_steps = [
        {
            "step_order": 1,
            "name": "登录接口",
            "method": "POST",
            "url": "http://localhost:3000/api/login",
            "headers": {"Content-Type": "application/json"},
            "payload": {"username": "{{username}}", "password": "{{password}}"},
            "assert_rules": {"status_code": 200},
            "extractors": [
                {"variableName": "token", "expression": "token", "extractorType": "jsonpath"}
            ]
        },
        {
            "step_order": 2,
            "name": "获取用户信息",
            "method": "GET",
            "url": "http://localhost:3000/api/user/info",
            "headers": {"Authorization": "Bearer {{token}}"},
            "assert_rules": {"status_code": 200}
        }
    ]

    test_data_matrix = {
        "columns": ["username", "password"],
        "rows": [
            ["admin", "admin123"],
            ["test", "test123"]
        ]
    }

    # 执行测试
    result = run_scenario_pytest(
        scenario_id=999,
        scenario_name="测试场景",
        steps=test_steps,
        data_matrix=test_data_matrix
    )

    print(json.dumps(result, indent=2, ensure_ascii=False))