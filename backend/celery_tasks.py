# -*- coding: utf-8 -*-
"""
Celery 异步任务 - 自动化测试场景执行

所有耗时任务在这里定义，通过 Celery Worker 异步执行。
"""

import sys
import os
import json
import re
import subprocess
import uuid
from pathlib import Path
from datetime import datetime, timedelta
import pytz

# 全局使用东八区北京时间
SHA_TZ = pytz.timezone('Asia/Shanghai')

# 添加项目根目录到 Python 路径（Worker 启动时需要）
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
if os.path.join(project_root, 'backend') not in sys.path:
    sys.path.insert(0, os.path.join(project_root, 'backend'))

# 🔒 【S0级钉死】强制统一绝对路径：所有 Allure 报告输出到 backend/reports 目录
# 彻底根除路径错位，确保和 FastAPI 5002 端口挂载完全一致
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# 所有报告强制输出到 backend/reports/{report_id}/
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
ALLURE_RESULTS_DIR = os.path.join(BASE_DIR, "allure-results")

# Webhook 报告链接基础 URL（飞书需要绝对路径才能点击跳转）
# 修改这里改成你的服务器/本机实际对外IP
BASE_WEBHOOK_URL = "http://192.168.31.25:5000"

# 确保根目录存在
os.makedirs(REPORTS_DIR, exist_ok=True)
os.makedirs(ALLURE_RESULTS_DIR, exist_ok=True)

from backend.celery_worker import celery_app


def get_flask_app():
    """创建独立的 Flask 应用上下文（供 Celery Worker 使用）"""
    from backend.app import create_app
    from backend.extensions import db
    app = create_app()
    return app, db


@celery_app.task(bind=True, name='auto_test:run_scenario_async')
def run_scenario_async(self, task_data):
    """
    异步执行自动化测试场景（支持数据驱动）

    参数：
        task_data: 字典，包含 scenario_id, user_id, env_id, webhook_url

    返回：
        包含完整执行结果的字典
    """
    # 第一时间解包并打印调试日志
    import logging
    logger = logging.getLogger(__name__)
    scenario_id = task_data.get('scenario_id')
    user_id = task_data.get('user_id', 1)
    env_id = task_data.get('env_id')
    webhook_url = task_data.get('webhook_url')

    logger.warning(f"===== Celery 收到任务字典 =====\n{task_data}")
    print(f"[Celery DEBUG] 收到任务字典: {task_data}")
    print(f"[Celery DEBUG] 解包 webhook_url = {repr(webhook_url)}")

    app, db = get_flask_app()

    with app.app_context():
        from backend.models.models import (
            AutoTestPlan, AutoTestStep,
            InterfaceTestReport, InterfaceTestReportResult,
            InterfaceTestEnvironment
        )

        # ========== 加载场景 ==========
        scenario = AutoTestPlan.query.filter_by(id=scenario_id, user_id=user_id).first()
        if not scenario:
            return {'error': '场景不存在', 'status': 'failed'}

        # ========== 加载步骤 ==========
        steps = AutoTestStep.query\
            .filter_by(scenario_id=scenario_id, is_active=True)\
            .order_by(AutoTestStep.step_order)\
            .all()

        total_steps_in_scenario = len(steps)
        if total_steps_in_scenario == 0:
            return {'error': '场景没有可用步骤', 'status': 'failed'}

        # ========== 解析数据驱动数据集 ==========
        # 格式: { "columns": ["username", "password"], "rows": [["user1", "pass1"], ["user2", "pass2"]], "name": "dataset_name" }
        # 如果没有数据集，默认执行 1 次，空数据
        import json as python_json
        data_matrix = None
        if scenario.data_matrix and str(scenario.data_matrix).strip():
            try:
                data_matrix = python_json.loads(scenario.data_matrix)
                print(f"[Celery] 解析数据集成功: {python_json.dumps(data_matrix, ensure_ascii=False)[:200]}...")
            except Exception as e:
                print(f"[Celery] ❌ 解析数据集失败: {e}，原值={scenario.data_matrix[:100]}，按普通模式执行")
                data_matrix = None

        rows = [{}]  # 默认单次空数据执行
        columns = []
        if data_matrix is not None:
            # 支持多种格式：
            # 1. 标准格式: { "columns": [...], "rows": [...]}
            if isinstance(data_matrix, dict) and 'rows' in data_matrix:
                found_rows = data_matrix['rows']
                if len(found_rows) > 0:
                    rows = found_rows
                    columns = data_matrix.get('columns', [])
                    # 转换为字典列表
                    new_rows = []
                    for row in found_rows:
                        if len(columns) == len(row):
                            row_data = dict(zip(columns, row))
                            new_rows.append(row_data)
                        else:
                            new_rows.append(row)
                    rows = new_rows
                    print(f"[Celery] ✅ 使用标准格式: {len(rows)} 行, {len(columns)} 列")
            # 2. 直接就是行数数组：每一行是 dict
            elif isinstance(data_matrix, list) and len(data_matrix) > 0:
                rows = data_matrix
                print(f"[Celery] ✅ 使用简化格式: {len(rows)} 行")
            else:
                print(f"[Celery] ⚠️ 数据集格式不识别，按普通模式执行: {type(data_matrix)}")

        total_iterations = len(rows)
        print(f"[Celery] 数据驱动模式: 共 {total_iterations} 行数据需要执行")

        # ========== 【Bug修复】不再删除历史报告 ==========
        # 历史报告必须保留，每一次执行都是一条新记录累加！
        # 旧代码删除所有旧报告这里被禁用：
        # old_reports = InterfaceTestReport.query.filter_by(plan_id=scenario_id, user_id=user_id).all()
        # for old_report in old_reports:
        #     InterfaceTestReportResult.query.filter_by(report_id=old_report.id).delete()
        # InterfaceTestReport.query.filter_by(plan_id=scenario_id, user_id=user_id).delete()
        # db.session.commit()
        # print(f'[Celery] 🧹 已清理场景 {scenario_id} 的旧报告数据，准备创建新报告')
        print(f'[Celery] 📜 历史报告保留，将创建新的报告记录')

        # ========== 加载环境变量（所有迭代共享） ==========
        base_env_vars = {}
        if env_id:
            try:
                # 确保导入了正确的模型
                from backend.models.models import InterfaceTestEnvironment
                env = InterfaceTestEnvironment.query.get(int(env_id)) # 强转int
                if env and env.variables:
                    import json
                    if isinstance(env.variables, str):
                        try:
                            base_env_vars = json.loads(env.variables)
                        except:
                            base_env_vars = {}
                    else:
                        base_env_vars = env.variables

                    # 合并基本URL
                    if hasattr(env, 'base_url') and env.base_url:
                        base_env_vars['base_url'] = env.base_url
                        # 为了兼容 {{my_base_url}}，再塞一个进去！
                        base_env_vars['my_base_url'] = env.base_url

                    print(f"✅ [Celery] 成功加载环境 ID {env_id} 的变量: {base_env_vars}")
            except Exception as e:
                print(f"❌ [Celery] 加载环境变量失败: {str(e)}")
        else:
            print("⚠️ [Celery] 警告: env_id 为 None，无法加载任何环境变量！")

        # ========== 创建报告记录 ==========
        total_steps = total_steps_in_scenario * total_iterations
        report = InterfaceTestReport(
            user_id=user_id,
            plan_id=scenario_id,
            plan_name=scenario.name,
            status='running',
            total_count=total_steps
        )
        db.session.add(report)
        db.session.commit()
        report_id = report.id

        # 使用东八区北京时间
        start_time = datetime.now(SHA_TZ)
        start_time_utc = datetime.utcnow()

        # ========== 数据驱动：遍历每一行数据 ==========
        overall_success_steps = 0
        overall_failed_steps = 0
        overall_total_time = 0
        all_step_results = []
        current_step_index = 0

        for iteration_index, row_data in enumerate(rows):
            # ========== 核心：用当前行数据初始化 context_vars ==========
            # 已经在上面解析的时候转换过了，row_data 已经是字典
            if isinstance(row_data, dict):
                context_vars = row_data.copy()
            else:
                # fallback: 如果还没转换，再转一次
                if columns and len(columns) == len(row_data):
                    context_vars = dict(zip(columns, row_data))
                else:
                    context_vars = {}

            # 合并环境变量（环境变量优先级低于数据行，不覆盖）
            for k, v in base_env_vars.items():
                if k not in context_vars:
                    context_vars[k] = v

            # 更新 Celery 任务进度（按总步骤计算）
            total_progress_steps = current_step_index + len(steps)
            self.update_state(
                state='PROGRESS',
                meta={
                    'current': current_step_index + 1,
                    'total': total_steps,
                    'percent': int((current_step_index + 1) / total_steps * 100),
                    'status': f'正在执行数据行 {iteration_index + 1}/{total_iterations}，步骤 {current_step_index + 1}/{total_steps}',
                    'current_api': f'数据行 {iteration_index + 1}'
                }
            )

            # ========== 执行当前数据行的所有步骤 ==========
            for step in steps:
                current_step_index += 1

                if overall_failed_steps > 0 and not step.is_active:
                    all_step_results.append({
                        'step_id': step.id,
                        'iteration': iteration_index + 1,
                        'api_case_name': step.api_case.name if step.api_case else 'Unknown',
                        'method': step.api_case.method if step.api_case else 'UNKNOWN',
                        'url': step.api_case.url if step.api_case else '',
                        'status': 'skipped',
                        'success': False,
                        'duration': 0
                    })
                    continue

                step_start = datetime.now(SHA_TZ)

                # 调用真正的步骤执行函数
                result = _execute_single_step(step, context_vars)

                step_duration = int((datetime.now(SHA_TZ) - step_start).total_seconds() * 1000)
                overall_total_time += step_duration

                if result['success']:
                    overall_success_steps += 1
                else:
                    overall_failed_steps += 1

                if 'extracted_vars' in result and result['extracted_vars']:
                    context_vars.update(result['extracted_vars'])

                all_step_results.append({
                    'step_id': step.id,
                    'iteration': iteration_index + 1,
                    'api_case_name': step.api_case.name if step.api_case else 'Unknown',
                    'method': step.api_case.method if step.api_case else 'UNKNOWN',
                    'url': result.get('url', ''),
                    'status': 'success' if result['success'] else 'failed',
                    'success': result['success'],
                    'status_code': result.get('status_code'),
                    'error': result.get('error'),
                    'response': result.get('response'),
                    'duration': step_duration
                })

                # 保存结果到数据库
                report_result = InterfaceTestReportResult(
                    report_id=report_id,
                    case_id=step.api_case_id,
                    case_name=step.api_case.name if step.api_case else 'Unknown',
                    method=step.api_case.method if step.api_case else 'UNKNOWN',
                    url=result.get('url', ''),
                    status_code=result.get('status_code'),
                    success=result['success'],
                    time=step_duration,
                    error=result.get('error'),
                    request_headers=json.dumps(result.get('request_headers', {})) if result.get('request_headers') else None,
                    request_body=json.dumps(result.get('request_body', {})) if isinstance(result.get('request_body'), dict) else result.get('request_body'),
                    response=json.dumps(result.get('response', {})),
                    response_headers=json.dumps(result.get('response_headers', {})) if result.get('response_headers') else None
                )
                db.session.add(report_result)
                db.session.commit()

        # ========== 更新报告状态 ==========
        # 统一使用东八区北京时间
        end_time = datetime.now(SHA_TZ).replace(tzinfo=None)

        # 强制重新统计，确保数据正确
        success_count = sum(1 for res in all_step_results if res.get('success') == True)
        failed_count = sum(1 for res in all_step_results if res.get('success') == False)

        # 整体状态判断：只要有失败步骤，就标记为 failed
        if failed_count > 0:
            report.status = 'failed'
        else:
            report.status = 'completed'
        report.success_count = success_count
        report.failed_count = failed_count
        report.total_time = overall_total_time
        report.executed_at = end_time
        db.session.commit()

        # ========== 生成物理 Allure 报告 ==========
        # 使用全局钉死的绝对路径（和 FastAPI 5002 挂载完全对齐）
        allure_results_dir = Path(ALLURE_RESULTS_DIR) / f'report_{report_id}'
        report_output_dir = os.path.join(REPORTS_DIR, str(report.id))
        index_file_path = os.path.join(report_output_dir, 'index.html')

        # 【强制清理】每次生成前彻底删除旧结果目录，确保新旧不混合
        import shutil
        if allure_results_dir.exists():
            shutil.rmtree(allure_results_dir)
            print(f"[Celery Allure] 已清理旧临时结果: {allure_results_dir}")

        # 重新创建干净的空目录
        allure_results_dir.mkdir(parents=True, exist_ok=True)
        os.makedirs(report_output_dir, exist_ok=True)

        # 生成唯一 ID
        history_id = str(uuid.uuid4())[:8]

        # 将执行结果写入 Allure 结果文件（每个步骤一个独立测试用例）
        _write_allure_results(allure_results_dir, scenario_id, {
            'start_time': start_time.timestamp(),
            'duration': overall_total_time,
            'failed_steps': failed_count,
            'step_results': all_step_results,
            'scenario_name': scenario.name
        }, history_id)

        # 🔒 【防弹防御 1】：在调用 allure 前，先强行写一个临时文件！
        # 只要 5002 挂载对了，最差也能看到这句话，绝不 404！
        with open(index_file_path, 'w', encoding='utf-8') as f:
            f.write("<h1 style='padding: 50px; font-family: sans-serif;'>正在生成报告，如果一直停留在此页面，说明 Allure 命令执行失败！请检查系统 PATH 环境！</h1>")

        try:
            import subprocess
            # 🔒 【防弹防御 2】：Windows 必须加 shell=True，否则绝对找不到 allure 命令（因为实际是 allure.bat）
            # 这里不使用 check=True，自己判断返回码
            result = subprocess.run(
                ['allure', 'generate', str(allure_results_dir), '-o', str(report_output_dir), '--clean'],
                capture_output=True, text=True, timeout=60, shell=True
            )
            if result.returncode != 0:
                raise Exception(f"Allure 命令执行失败 (code={result.returncode}):\n{result.stderr}")
            print(f'[Celery] Allure 报告生成成功: /reports/{report.id}/index.html')
            if result.stdout:
                print(f'[Celery] Allure stdout: {result.stdout}')
            if result.stderr:
                print(f'[Celery] Allure stderr: {result.stderr}')
        except Exception as e:
            # 🔒 【防弹防御 3】：捕获一切异常，将错误直接写在 HTML 页面上，绝不 404！
            error_msg = str(e)
            print(f'[Celery] ❌ Allure 生成遭遇异常: {error_msg}')
            with open(index_file_path, 'w', encoding='utf-8') as f:
                f.write(f'''<!DOCTYPE html>
                <html>
                <head><meta charset="utf-8"></head>
                <body style="padding: 50px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; max-width: 900px; margin: 0 auto;">
                    <h1 style="color: #dc3545;">❌ Allure 报告生成失败</h1>
                    <hr>
                    <h3>错误详情：</h3>
                    <pre style="background: #f8f9fa; padding: 15px; border-radius: 6px; border: 1px solid #dee2e6; color: #dc3545; white-space: pre-wrap; word-break: break-all;">{error_msg}</pre>
                    <hr>
                    <h3>可能原因：</h3>
                    <ul>
                        <li>Allure CLI 未安装，请从 https://github.com/allure-framework/allure2 下载安装</li>
                        <li>Allure 的 bin 目录没有添加到系统 PATH 环境变量</li>
                        <li>权限不足，无法写入报告目录</li>
                    </ul>
                    <p><strong>当前报告目录：</strong><code>{report_output_dir}</code></p>
                </body>
                </html>
                ''')

        # 最后更新数据库的 report_url 并提交
        report.report_url = f'/reports/{report.id}/index.html'
        db.session.commit()

        # ========== Webhook 告警通知（执行完毕后发送） ==========
        # 优先级：定时任务传入 > 场景本身配置
        import logging
        logger = logging.getLogger(__name__)
        logger.warning("===== Webhook调试 =====")
        logger.warning(f"定时任务传入的 webhook_url = {repr(webhook_url)}")
        logger.warning(f"场景本身的 webhook_url = {repr(getattr(scenario, 'webhook_url', None))}")
        final_webhook_url = webhook_url if (webhook_url and str(webhook_url).strip()) else getattr(scenario, 'webhook_url', None)
        logger.warning(f"最终使用 final_webhook_url = {repr(final_webhook_url)}")
        if final_webhook_url and str(final_webhook_url).strip():
            import logging
            logger = logging.getLogger(__name__)
            final_webhook_url = str(final_webhook_url).strip()
            logger.info(f"[Webhook] 准备发送 Webhook 到: {final_webhook_url}")
            print(f"[Webhook] 准备发送 Webhook 到: {final_webhook_url}")
            try:
                # 获取环境名称
                env_name = "默认环境"
                if env_id:
                    env = InterfaceTestEnvironment.query.filter_by(id=env_id, user_id=user_id).first()
                    if env:
                        env_name = env.name or f"环境 {env_id}"

                # 构造报告完整 URL - 强制使用绝对路径（飞书等外部App需要完整IP才能访问）
                report_url = report.report_url
                full_report_url = f"{BASE_WEBHOOK_URL}{report_url}"

                # 统计结果 & 动态颜色
                template_color = "green" if failed_count == 0 else "red"
                current_time = datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S')

                # 自动判断格式：飞书互动卡片 vs 钉钉/企业微信 markdown
                import requests
                if 'feishu.cn' in final_webhook_url or 'feishu.com' in final_webhook_url:
                    # 飞书机器人 - 升级为互动卡片格式
                    webhook_data = {
                        "msg_type": "interactive",
                        "card": {
                            "config": {"update_multi": True},
                            "header": {
                                "template": template_color,
                                "title": {
                                    "content": "🤖 TestMaster 自动化测试报告",
                                    "tag": "plain_text"
                                }
                            },
                            "elements": [
                                {
                                    "tag": "div",
                                    "fields": [
                                        {
                                            "is_short": True,
                                            "text": {"content": f"**场景名称：**\n{scenario.name}", "tag": "lark_md"}
                                        },
                                        {
                                            "is_short": True,
                                            "text": {"content": f"**执行环境：**\n{env_name}", "tag": "lark_md"}
                                        }
                                    ]
                                },
                                {"tag": "hr"},
                                {
                                    "tag": "div",
                                    "fields": [
                                        {
                                            "is_short": True,
                                            "text": {"content": f"**测试统计：**\n✅ 通过：{success_count}\n❌ 失败：{failed_count}", "tag": "lark_md"}
                                        },
                                        {
                                            "is_short": True,
                                            "text": {"content": f"**耗时：**\n{overall_total_time} ms", "tag": "lark_md"}
                                        }
                                    ]
                                },
                                {
                                    "tag": "action",
                                    "actions": [
                                        {
                                            "tag": "button",
                                            "text": {"content": "查看详细 Allure 报告", "tag": "plain_text"},
                                            "type": "primary",
                                            "url": full_report_url
                                        }
                                    ]
                                },
                                {
                                    "tag": "note",
                                    "elements": [
                                        {
                                            "content": f"报告生成时间：{current_time} (东八区)",
                                            "tag": "plain_text"
                                        }
                                    ]
                                }
                            ]
                        }
                    }
                    logger.info("[Webhook] 检测到飞书Webhook，使用飞书互动卡片格式，绝对链接: " + full_report_url)
                else:
                    # 钉钉/企业微信机器人 markdown 格式
                    result_emoji = "🟢" if failed_count == 0 else "🔴"
                    result_text = "通过" if failed_count == 0 else "有失败用例"
                    markdown_msg = f"""# 🤖 自动化测试报告
**场景名称**: {scenario.name}
**执行环境**: {env_name}
**测试结果**: {result_emoji}{result_text} | ✅通过 {success_count} 个 | ❌失败 {failed_count} 个
**运行时长**: {overall_total_time} ms
[点击查看 Allure 详细报告]({full_report_url})
"""
                    webhook_data = {
                        "msgtype": "markdown",
                        "markdown": {
                            "content": markdown_msg
                        }
                    }
                logger.info(f"[Webhook] 组装消息完成，正在发送请求...")
                resp = requests.post(final_webhook_url, json=webhook_data, timeout=10)
                if resp.status_code == 200:
                    logger.info(f"[Webhook] ✅ Webhook 发送成功，状态码: {resp.status_code}, 响应: {resp.text[:200]}")
                    print(f"[Webhook] ✅ Webhook 发送成功")
                else:
                    logger.warning(f"[Webhook] ⚠️ Webhook 发送返回非200状态码: {resp.status_code}, 响应: {resp.text[:500]}")
                    print(f"[Webhook] ⚠️ Webhook 发送返回码: {resp.status_code}")
            except Exception as e:
                logger.error(f"[Webhook] ❌ Webhook 发送异常: {str(e)}", exc_info=True)
                print(f"[Webhook] ❌ Webhook 发送异常: {str(e)}")

        return {
            'status': 'completed' if failed_count == 0 else 'failed',
            'scenario_id': scenario_id,
            'scenario_name': scenario.name,
            'total_steps': total_steps,
            'success_steps': success_count,
            'failed_steps': failed_count,
            'duration': overall_total_time,
            'step_results': all_step_results,
            'report_id': report_id,
            'report_url': report.report_url or f'/reports/{report_id}/index.html'
        }


def verify_assertions(response, assertion_rules, context_vars):
    """
    执行断言校验，支持变量动态替换
    返回：(passed: bool, error_message: str)
    """
    from backend.api.interface_test import substitute_variables

    if not assertion_rules:
        return True, None

    for rule in assertion_rules:
        target = rule.get('target')       # status_code, json_body, response_time
        operator = rule.get('operator')  # ==, !=, contains, <, >
        raw_expected = str(rule.get('expected', ''))
        expression = rule.get('expression', '')

        # 1. 替换期望值中的变量（支持数据驱动变量/环境变量/提取变量）
        #    这一步必须做！用户报错就是因为这里漏了，实际上没漏，但再确认
        expected_val = substitute_variables(raw_expected, context_vars)

        actual_val = None
        try:
            # 2. 提取实际值
            if target == 'status_code':
                actual_val = str(response.status_code)
                # expected_val 已经替换完成，保证是字符串
            elif target == 'json_body':
                from jsonpath_ng import parse
                try:
                    json_data = response.json()
                except:
                    json_data = None

                if not json_data or not expression:
                    actual_val = "NOT_FOUND"
                else:
                    jsonpath_expr = parse(expression)
                    matches = [match.value for match in jsonpath_expr.find(json_data)]
                    if matches:
                        actual_val = str(matches[0])
                    else:
                        actual_val = "NOT_FOUND"
            elif target == 'response_time':
                actual_val = response.elapsed.total_seconds() * 1000
                # 对期望值也需要替换后再转 float
                expected_val = float(expected_val)

            # 3. 执行比对（统一转换为字符串比较，避免类型错误）
            passed = False
            if operator == '==':
                passed = (str(actual_val) == str(expected_val))
            elif operator == '!=':
                passed = (str(actual_val) != str(expected_val))
            elif operator == 'contains':
                passed = (str(expected_val) in str(actual_val))
            elif operator == '<':
                passed = (float(actual_val) < float(expected_val))
            elif operator == '>':
                passed = (float(actual_val) > float(expected_val))
            else:
                # 默认不通过，操作符不支持
                passed = False

            if not passed:
                return False, f"断言失败: [{target}] 期望 {operator} '{expected_val}', 实际为 '{actual_val}'"

        except Exception as e:
            return False, f"断言解析异常: {str(e)}"

    # 所有断言都通过
    return True, None


def _execute_single_step(step, context_vars):
    """
    执行单个场景步骤（Celery 任务专用版本，不依赖 Flask 请求上下文）
    """
    from backend.api.interface_test import substitute_variables

    if not step.api_case:
        return {'success': False, 'error': '步骤未关联 API 用例'}

    api_case = step.api_case

    # 📝 数据库原始数据检查 - 打印从数据库拿到的原始提取规则
    print(f"📝 [DATABASE_CHECK] 接口ID: {api_case.id}, 原始提取规则: {api_case.extractors}")
    print(f"📝 [DATABASE_CHECK] 接口ID: {api_case.id}, 原始URL: {api_case.url}")
    print(f"📝 [DATABASE_CHECK] 接口ID: {api_case.id}, 原始headers: {api_case.headers}")

    # 🔍 调试日志：打印当前变量池和原始 URL
    print(f"🔍 [DEBUG] 当前变量池内容: {context_vars}")
    print(f"🔍 [DEBUG] 准备替换 URL: {api_case.url}")

    # 变量替换 - URL
    url = substitute_variables(api_case.url or '', context_vars)
    print(f"🔍 [DEBUG] 替换后 URL: {url}")
    method = api_case.method or 'GET'

    # 处理 headers（现在存储格式是数组：[{"key", "value", "description"}]）
    headers = {}
    try:
        headers_raw = api_case.headers or '[]'
        if isinstance(headers_raw, str):
            headers_array = json.loads(headers_raw)
        else:
            headers_array = headers_raw or []

        # 对每个 header value 进行变量替换，然后转为字典
        for header in headers_array:
            if 'key' in header and 'value' in header:
                key = substitute_variables(header['key'], context_vars)
                value = substitute_variables(header['value'], context_vars)
                headers[key] = value
    except Exception as e:
        print(f"[Celery] 解析 headers 失败: {e}")
        headers = {}

    # 处理 body 变量替换
    body = api_case.body or ''
    print(f"🔍 [DEBUG] 准备替换 Body: {body[:100]}")
    body = substitute_variables(body, context_vars)
    print(f"🔍 [DEBUG] 替换后 Body: {body[:100]}")
    body_type = api_case.body_type or 'json'

    # 🔥 自动注入 Authorization Token
    # 如果环境上下文中有 token 字段，且 headers 中还没有 Authorization，自动添加 Bearer token
    if 'token' in context_vars and 'Authorization' not in headers:
        token_value = str(context_vars['token']).strip()
        if token_value:
            if token_value.lower().startswith('bearer '):
                headers['Authorization'] = token_value
            else:
                headers['Authorization'] = f'Bearer {token_value}'

    # 🔥 暴力注入 Content-Type：只要 POST/PUT/PATCH 没设置 Content-Type，强制添加 application/json
    if method.upper() in ['POST', 'PUT', 'PATCH']:
        has_content_type = any(k.lower() == 'content-type' for k in headers.keys())
        if not has_content_type:
            headers['Content-Type'] = 'application/json'

    # 发送请求 - 大厂级标准化处理
    try:
        import requests

        # 暴力重新处理 payload，确保正确
        actual_body = body
        req_kwargs = {
            'headers': headers,
            'timeout': 30,
            'allow_redirects': True
        }

        if actual_body and isinstance(actual_body, str):
            try:
                # 尝试解析为 JSON，如果成功交给 requests 原生 json 参数，自动带 Content-Type
                parsed_json = json.loads(actual_body)
                req_kwargs['json'] = parsed_json
            except json.JSONDecodeError:
                # 解析失败，手动编码，已经有 Content-Type 了
                req_kwargs['data'] = actual_body.encode('utf-8')
        elif isinstance(actual_body, dict):
            req_kwargs['json'] = actual_body
        elif actual_body:
            req_kwargs['data'] = str(actual_body).encode('utf-8')
        # 如果空 body 但是 JSON content-type，给空字典
        elif not actual_body and 'application/json' in headers.get('Content-Type', ''):
            req_kwargs['json'] = {}

        print(f"🔥🔥🔥 [REAL RUNNER - Celery] 最终发包参数: method={method}, url={url}, headers={headers}, body={repr(actual_body[:200])}")
        step_start_time = datetime.now(SHA_TZ)
        response = requests.request(method, url, **req_kwargs)
        duration_ms = int((datetime.now(SHA_TZ) - step_start_time).total_seconds() * 1000)

        # 状态码 >= 400 强制失败
        if response.status_code >= 400:
            return {
                'success': False,
                'url': url,
                'method': method,
                'status_code': response.status_code,
                'response': response.text[:10000],
                'duration': duration_ms,
                'request_headers': headers,
                'request_body': body,
                'response_headers': dict(response.headers),
                'error': f'默认断言失败: 期望 2xx/3xx (< 400), 实际返回 {response.status_code}',
                'extracted_vars': {}
            }

        success = 200 <= response.status_code < 400

        # 🔥 战役：上下游动态传参 - 后置 JSON 提取
        # 如果接口用例配置了提取规则，从响应 JSON 中提取变量存入 context
        extracted_vars = {}
        if success and api_case.extractors and str(api_case.extractors).strip():
            try:
                # 鲁棒性解析提取规则数组
                extractor_rules = []
                raw_extractors = getattr(api_case, 'extractors', [])

                if isinstance(raw_extractors, str) and raw_extractors.strip():
                    extractor_rules = json.loads(raw_extractors)
                elif isinstance(raw_extractors, list):
                    extractor_rules = raw_extractors

                if extractor_rules and isinstance(extractor_rules, list):
                    # 尝试解析响应为 JSON
                    try:
                        response_json = response.json()
                    except:
                        # 响应不是 JSON，无法提取
                        response_json = None

                    if response_json is not None:
                        # 对每个提取规则执行提取，兼容多种字段名（驼峰/下划线）
                        from jsonpath_ng import parse
                        for rule in extractor_rules:
                            # 兼容所有命名风格：variableName (驼峰) / variable_name (下划线) / name
                            var_name = (rule.get('variableName') or
                                       rule.get('variable_name') or
                                       rule.get('name'))
                            # 兼容所有命名风格：expression / json_path / jsonPath
                            json_path = (rule.get('expression') or
                                       rule.get('json_path') or
                                       rule.get('jsonPath'))

                            if var_name and json_path:
                                print(f"✅ [DEBUG] 准备从响应提取: {var_name} 使用路径 {json_path}")
                                try:
                                    jsonpath_expr = parse(json_path)
                                    matches = jsonpath_expr.find(response_json)
                                    if matches:
                                        # 取第一个匹配的值
                                        extracted_value = matches[0].value
                                        extracted_vars[var_name] = extracted_value
                                        print(f"✅ [DEBUG] 成功提取变量: {var_name} = {repr(extracted_value)}")
                                        print(f"🔍 [DEBUG] 即将更新变量池: +{extracted_vars}")
                                except Exception as extract_err:
                                    print(f"❌ [DEBUG] 变量 {var_name} 提取失败: {str(extract_err)}")
                            else:
                                print(f"⚠️ [DEBUG] 规则无效，跳过: 变量名={var_name}, 路径={json_path}, 原始规则={rule}")
            except Exception as e:
                print(f"[Celery] 解析提取规则失败: {e}")

        # ========== 执行断言校验 ==========
        assertion_success = True
        assertion_error = None
        if api_case.assertions and str(api_case.assertions).strip():
            try:
                assertion_rules = []
                raw_assertions = getattr(api_case, 'assertions', [])

                if isinstance(raw_assertions, str) and raw_assertions.strip():
                    assertion_rules = json.loads(raw_assertions)
                elif isinstance(raw_assertions, list):
                    assertion_rules = raw_assertions

                if assertion_rules and isinstance(assertion_rules, list):
                    assertion_success, assertion_error = verify_assertions(
                        response, assertion_rules, context_vars
                    )
                    if not assertion_success:
                        success = False
            except Exception as e:
                assertion_success = False
                assertion_error = f"断言解析失败: {str(e)}"
                success = False
                print(f"[Celery] 断言执行失败: {e}")

        return {
            'success': success and assertion_success,
            'url': url,
            'method': method,
            'status_code': response.status_code,
            'response': response.text[:10000],
            'duration': duration_ms,
            'request_headers': headers,
            'request_body': body,
            'response_headers': dict(response.headers),
            'extracted_vars': extracted_vars,
            'error': assertion_error
        }
    except Exception as e:
        return {
            'success': False,
            'url': url,
            'error': str(e),
            'status_code': None,
            'extracted_vars': {}
        }


def _write_allure_results(allure_results_dir: Path, scenario_id: int, result: dict, history_id: str):
    """
    将场景执行结果写入 Allure 结果文件（每个步骤作为独立测试用例）

    Args:
        allure_results_dir: Allure 结果目录
        scenario_id: 场景ID
        result: 执行结果字典，包含 step_results
        history_id: 本次执行的历史ID
    """
    import json
    import uuid
    import time

    # 获取步骤结果和场景信息
    step_results = result.get("step_results", [])
    scenario_name = result.get("scenario_name", f"场景 {scenario_id}")

    # 计算整体开始时间戳（毫秒）
    start_time = result.get("start_time")
    if start_time:
        if isinstance(start_time, (int, float)):
            scenario_start_ms = int(start_time * 1000) if start_time < 1e10 else int(start_time)
        else:
            scenario_start_ms = int(time.time() * 1000)
    else:
        scenario_start_ms = int(time.time() * 1000)

    # 循环遍历每个步骤，每个步骤生成一个独立的测试用例 JSON 文件
    for idx, step in enumerate(step_results):
        step_uuid = str(uuid.uuid4())
        step_id = step.get("step_id", idx)
        iteration = step.get("iteration", 1)  # DDT 数据行号

        # 计算步骤时间
        step_duration = step.get("duration", 0)
        step_start_ms = scenario_start_ms + sum(
            s.get("duration", 0) for s in step_results[:idx]
        )
        step_stop_ms = step_start_ms + step_duration

        # 判断步骤状态
        success = step.get("success", False)
        status = "passed" if success else "failed"

        # 提取关键信息
        api_case_name = step.get("api_case_name", f"未知接口")
        # 如果是数据驱动，在测试用名称中加上行号，便于区分
        iteration_info = f"[行 {iteration}] " if len(step_results) > 1 else ""
        method = step.get("method", "GET")
        url = step.get("url", "")
        status_code = step.get("status_code", 0)
        error = step.get("error", "")
        response = step.get("response", "")

        # 构建独立测试用例（每个接口一步算作一个 Allure TestCase）
        test_case = {
            "name": f"{iteration_info}步骤 {idx+1}: {api_case_name}",
            "status": status,
            "stage": "finished",
            "start": step_start_ms,
            "stop": step_stop_ms,
            "duration": step_duration,
            "uuid": step_uuid,
            "historyId": f"{scenario_id}_{step_id}_iter{iteration}",
            "statusDetails": {
                "message": error if error else ("成功" if success else "未知错误"),
                "trace": ""
            },
            "labels": [
                {"name": "parentSuite", "value": "自动化场景测试"},
                {"name": "suite", "value": f"场景: {scenario_name}"},
                {"name": "subSuite", "value": f"ID: {scenario_id}"},
                {"name": "severity", "value": "normal"},
                {"name": "host", "value": "localhost"}
            ],
            "parameters": [
                {"name": "Method", "value": method},
                {"name": "URL", "value": url[:100] if url else ""}
            ],
            "attachments": []
        }

        # 添加响应详情作为 attachment（Allure 2.x 需要实际文件）
        if response or error:
            step_details = f"""API: {method} {url}
状态码: {status_code}
耗时: {step_duration}ms
错误: {error if error else '无错误'}
响应: {str(response)[:1000] if response else '无响应体'}"""

            # 创建 attachment 文件（Allure 2.x 标准）
            attachment_filename = f"response_{idx+1}.txt"
            attachment_path = allure_results_dir / attachment_filename
            with open(attachment_path, "w", encoding="utf-8") as af:
                af.write(step_details)

            test_case["attachments"].append({
                "name": "响应详情",
                "type": "text/plain",
                "source": attachment_filename
            })

        # 如果有提取的变量
        if step.get("extracted_vars"):
            vars_info = ", ".join([f"{k}={v}" for k, v in step["extracted_vars"].items()])
            # 创建 vars attachment 文件
            vars_filename = f"vars_{idx+1}.txt"
            vars_path = allure_results_dir / vars_filename
            with open(vars_path, "w", encoding="utf-8") as vf:
                vf.write(vars_info)
            test_case["attachments"].append({
                "name": "提取变量",
                "type": "text/plain",
                "source": vars_filename
            })

        # 写入独立的 JSON 文件（Allure 要求 {uuid}-result.json）
        result_file = allure_results_dir / f"{step_uuid}-result.json"
        with open(result_file, "w", encoding="utf-8") as f:
            json.dump(test_case, f, ensure_ascii=False, indent=2)
