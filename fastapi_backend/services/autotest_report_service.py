"""
AutoTest 报告服务
从 routers/autotest_execution.py 的 get_report_detail 端点下沉的业务逻辑
包含 Allure 报告生成与写入
"""
import json
import logging
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_backend.models.autotest import AutoTestHistory, AutoTestScenarioExecutionRecord

_logger = logging.getLogger(__name__)


def get_autotest_data_dir() -> Path:
    from fastapi_backend.core.autotest_database import INSTANCE_DIR
    return INSTANCE_DIR


def load_step_results_from_file(record: AutoTestScenarioExecutionRecord) -> List[Dict]:
    step_results = []
    step_results_file = get_autotest_data_dir() / "step_results" / f"scenario_{record.scenario_id}_record_{record.id}.json"
    if step_results_file.exists():
        try:
            with open(step_results_file, "r", encoding="utf-8") as f:
                step_results = json.load(f)
        except Exception:
            step_results = []
    return step_results


def parse_allure_step_results(scenario_id: int) -> List[Dict]:
    step_results = []
    allure_results_dir = get_autotest_data_dir() / "allure-results" / f"scenario_{scenario_id}"
    if not allure_results_dir.exists():
        return step_results

    for json_file in sorted(allure_results_dir.glob("*.json")):
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                allure_data = json.load(f)
                if allure_data.get("fullName", "").startswith("TestScenario"):
                    step_name = allure_data.get("name", "")
                    step_status = allure_data.get("status", "passed")
                    description = allure_data.get("description", "")
                    method = "GET"
                    if description.startswith("["):
                        method = description.split("]")[0].strip("[")
                    elif step_name.startswith("["):
                        method = step_name.split("]")[0].strip("[")
                    api_case_name = step_name
                    if ": " in step_name:
                        api_case_name = step_name.split(": ", 1)[1]
                    status_code = 0
                    response_body = None
                    for sub_step in allure_data.get("steps", []):
                        for att in sub_step.get("attachments", []):
                            if att.get("name") == "响应信息" and att.get("body"):
                                try:
                                    resp_info = json.loads(att["body"])
                                    status_code = resp_info.get("status_code", 0)
                                    response_body = resp_info.get("body", "")
                                except Exception:
                                    pass
                    step_results.append({
                        "name": step_name,
                        "status": "skipped" if step_status == "skipped" else ("success" if step_status == "passed" else "failed"),
                        "success": step_status == "passed",
                        "duration": allure_data.get("duration", 0),
                        "method": method,
                        "api_case_name": api_case_name,
                        "url": "",
                        "status_code": status_code,
                        "response": {"body": response_body} if response_body else None,
                        "error": allure_data.get("statusDetails", {}).get("message") if step_status == "failed" else None
                    })
                else:
                    for step in allure_data.get("steps", []):
                        step_results.append({
                            "name": step.get("name", ""),
                            "status": "passed" if step.get("status") == "passed" else "failed",
                            "success": step.get("status") == "passed",
                            "duration": step.get("duration", 0),
                            "method": step.get("name", "").split()[0].strip("[]") if step.get("name") else "GET",
                            "api_case_name": " ".join(step.get("name", "").split()[1:]) if step.get("name") else "未知用例",
                            "url": "",
                            "status_code": 0,
                            "response": None,
                            "error": None
                        })
        except Exception:
            pass

    return step_results


async def get_report_detail(report_id: int, db: AsyncSession) -> Optional[Dict]:
    """
    获取执行报告详情
    先查 AutoTestScenarioExecutionRecord，再查 AutoTestHistory
    """
    result = await db.execute(
        select(AutoTestScenarioExecutionRecord)
        .where(AutoTestScenarioExecutionRecord.id == report_id)
    )
    record = result.scalar_one_or_none()
    if record:
        step_results = load_step_results_from_file(record)

        if not step_results and record.report_url:
            step_results = parse_allure_step_results(record.scenario_id)

        step_detail_available = bool(step_results)
        if not step_detail_available and record.total_steps > 0:
            _logger.warning(
                "报告 %d (scenario_id=%d) 有 %d 个步骤但无法读取步骤详情数据",
                record.id, record.scenario_id, record.total_steps,
            )

        return {
            "id": record.id,
            "scenario_id": record.scenario_id,
            "status": record.status,
            "total_steps": record.total_steps,
            "success_steps": record.success_steps,
            "failed_steps": record.failed_steps,
            "skipped_steps": record.skipped_steps,
            "total_time": record.total_time,
            "report_url": record.report_url,
            "step_results": step_results,
            "step_detail_available": step_detail_available,
            "created_at": record.created_at,
        }

    result = await db.execute(
        select(AutoTestHistory).where(AutoTestHistory.id == report_id)
    )
    history = result.scalar_one_or_none()
    if history:
        return {
            "id": history.id,
            "case_id": history.case_id,
            "status": history.status,
            "execution_time": history.execution_time,
            "response_data": history.response_data,
            "error_message": history.error_message,
            "created_at": history.created_at,
            "step_results": [],
            "step_detail_available": True,
        }

    return None


def write_allure_results(allure_results_dir: Path, scenario_id: int, result: dict, history_id: str):
    start_time = result.get("start_time")
    if start_time:
        if isinstance(start_time, (int, float)):
            base_start_ms = int(start_time * 1000) if start_time < 1e10 else int(start_time)
        else:
            try:
                dt = datetime.fromisoformat(str(start_time).replace('Z', '+00:00'))
                base_start_ms = int(dt.timestamp() * 1000)
            except Exception:
                base_start_ms = int(time.time() * 1000)
    else:
        base_start_ms = int(time.time() * 1000)

    step_results = result.get("step_results", [])
    scenario_name = result.get("scenario_name", f"场景 {scenario_id}")

    cumulative_ms = 0

    for i, step in enumerate(step_results):
        i_plus_1 = i + 1
        step_duration = step.get("duration", 0)
        step_start_ms = base_start_ms + cumulative_ms
        step_stop_ms = step_start_ms + step_duration
        cumulative_ms += step_duration

        step_status_raw = step.get("status", "success")
        if step_status_raw == "skipped":
            step_status = "skipped"
            status_details = {"message": step.get("skipped_reason", "步骤被跳过")}
        else:
            success = step_status_raw != "failed"
            status_code = step.get("status_code", 0)
            url = step.get("url", "")
            is_really_success = success and status_code > 0 and url

            if is_really_success:
                step_status = "passed"
                status_details = {}
            else:
                step_status = "failed"
                error_msg = step.get("error", "")
                if not error_msg:
                    assertions = step.get("assertions", {})
                    failed_asserts = assertions.get("failed", [])
                    if failed_asserts:
                        msgs = []
                        for fa in failed_asserts:
                            if isinstance(fa, dict):
                                msgs.append(fa.get("reason", str(fa)))
                            else:
                                msgs.append(str(fa))
                        error_msg = "; ".join(msgs)
                    if not error_msg:
                        if success and (status_code == 0 or not url):
                            error_msg = f"请求未成功发出 (status_code={status_code}, url为空)"
                        else:
                            error_msg = f"期望 2xx/3xx, 实际返回 {status_code}"
                status_details = {"message": error_msg}

        api_case_name = step.get("api_case_name", f"步骤 {i_plus_1}")
        method = step.get("method", "GET")
        step_title = f"用例{i_plus_1}: {api_case_name}"

        sub_steps = []

        request_step = {
            "name": f"1. 发起HTTP请求: {method} {url}",
            "status": step_status,
            "stage": "finished",
            "start": step_start_ms,
            "stop": step_start_ms + max(step_duration // 3, 1),
            "duration": max(step_duration // 3, 1),
            "steps": [],
            "attachments": [],
        }
        request_info = {"url": url, "method": method, "headers": step.get("headers", {}), "payload": step.get("payload", {})}
        request_step["attachments"].append({
            "name": "请求信息",
            "type": "application/json",
            "source": f"request_{i_plus_1}.json",
            "body": json.dumps(request_info, ensure_ascii=False, indent=2)
        })
        sub_steps.append(request_step)

        response_step = {
            "name": "2. 获取响应信息",
            "status": step_status,
            "stage": "finished",
            "start": step_start_ms + max(step_duration // 3, 1),
            "stop": step_start_ms + max(step_duration * 2 // 3, 1),
            "duration": max(step_duration // 3, 1),
            "steps": [],
            "attachments": [],
        }
        response_body = ""
        if step.get("response"):
            response_body = step["response"].get("body", "")
        response_info = {"status_code": status_code, "response_time_ms": step.get("response_time", 0), "body": str(response_body)[:2000] if response_body else ""}
        response_step["attachments"].append({
            "name": "响应信息",
            "type": "application/json",
            "source": f"response_{i_plus_1}.json",
            "body": json.dumps(response_info, ensure_ascii=False, indent=2)
        })
        sub_steps.append(response_step)

        assertion_step = {
            "name": "3. 执行断言校验",
            "status": step_status,
            "stage": "finished",
            "start": step_start_ms + max(step_duration * 2 // 3, 1),
            "stop": step_stop_ms,
            "duration": max(step_duration // 3, 1),
            "steps": [],
            "attachments": [],
        }
        if step.get("extracted_vars"):
            vars_info = ", ".join([f"{k}={v}" for k, v in step["extracted_vars"].items()])
            assertion_step["attachments"].append({
                "name": f"提取变量_{i_plus_1}",
                "type": "text/plain",
                "source": f"vars_{i_plus_1}.txt",
                "body": vars_info
            })
        sub_steps.append(assertion_step)

        step_uuid = str(uuid.uuid4())
        test_case_result = {
            "name": step_title,
            "uuid": step_uuid,
            "historyId": f"TestScenario{scenario_id}.test_step_{i_plus_1}",
            "fullName": f"TestScenario{scenario_id}.test_step_{i_plus_1}",
            "status": step_status,
            "stage": "finished",
            "start": step_start_ms,
            "stop": step_stop_ms,
            "duration": step_duration,
            "description": f"[{method}] {api_case_name}",
            "labels": [
                {"name": "suite", "value": scenario_name},
                {"name": "feature", "value": scenario_name},
                {"name": "severity", "value": "normal"},
                {"name": "scenario_id", "value": str(scenario_id)},
                {"name": "thread", "value": "main"},
                {"name": "host", "value": "localhost"},
            ],
            "parameters": [],
            "links": [],
            "steps": sub_steps,
            "attachments": [],
        }
        if status_details:
            test_case_result["statusDetails"] = status_details

        output_file = allure_results_dir / f"scenario-{scenario_id}-step-{i_plus_1}-{history_id}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(test_case_result, f, ensure_ascii=False, indent=2)
