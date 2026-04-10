"""
自动化测试 API 路由
处理自动化测试用例的增删改查，以及从在线接口测试导入用例
"""
import json
from datetime import datetime
from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from backend.extensions import db
from backend.models.models import AutoTestCase, AutoTestGroup, InterfaceTestCase

auto_test_bp = Blueprint('auto_test', __name__)


# ========== 数据完整性诊断 ==========

@auto_test_bp.route('/auto-test/diagnose/report/<int:report_id>', methods=['GET'])
@jwt_required()
def diagnose_report(report_id):
    """
    诊断报告数据完整性：检测同一 report_id 下是否有累积的孤儿步骤数据
    返回：{has_orphans: bool, orphan_count: int, total_count: int, latest_step_id: int}
    """
    from backend.models.models import InterfaceTestReport, InterfaceTestReportResult

    report = InterfaceTestReport.query.get(report_id)
    if not report:
        return jsonify({'error': '报告不存在'}), 404

    all_steps = InterfaceTestReportResult.query.filter_by(report_id=report_id)\
        .order_by(InterfaceTestReportResult.id).all()

    total_count = len(all_steps)

    if total_count == 0:
        return jsonify({
            'has_orphans': False,
            'orphan_count': 0,
            'total_count': 0,
            'latest_step_id': None,
            'step_ids': []
        })

    # 获取最新报告的步骤数量（从 steps 字段解析）
    latest_steps_count = 0
    try:
        if report.steps and isinstance(report.steps, str):
            steps_list = json.loads(report.steps)
            latest_steps_count = len(steps_list)
        elif isinstance(report.steps, list):
            latest_steps_count = len(report.steps)
    except:
        latest_steps_count = 0

    has_orphans = total_count > latest_steps_count if latest_steps_count > 0 else False
    orphan_count = total_count - latest_steps_count if has_orphans else 0

    return jsonify({
        'has_orphans': has_orphans,
        'orphan_count': orphan_count,
        'total_count': total_count,
        'expected_count': latest_steps_count,
        'latest_step_id': all_steps[-1].id if all_steps else None,
        'step_ids': [s.id for s in all_steps]
    })


@auto_test_bp.route('/auto-test/diagnose/scenario/<int:scenario_id>', methods=['GET'])
@jwt_required()
def diagnose_scenario(scenario_id):
    """
    诊断场景数据完整性：检查该场景下所有报告的数据一致性
    """
    from backend.models.models import InterfaceTestReport

    reports = InterfaceTestReport.query.filter_by(plan_id=scenario_id)\
        .order_by(InterfaceTestReport.id.desc()).all()

    report_diagnostics = []
    for report in reports:
        all_steps = InterfaceTestReportResult.query.filter_by(report_id=report.id).count()
        report_diagnostics.append({
            'report_id': report.id,
            'status': report.status,
            'total_count_db': report.total_count,
            'actual_steps': all_steps,
            'executed_at': report.executed_at.isoformat() if report.executed_at else None
        })

    return jsonify({
        'scenario_id': scenario_id,
        'total_reports': len(reports),
        'reports': report_diagnostics
    })


# ========== 分组管理 ==========

@auto_test_bp.route('/auto-test/groups', methods=['GET'])
@jwt_required()
def get_groups():
    """获取当前用户的所有分组（树形结构）"""
    user_id = get_jwt_identity()
    groups = AutoTestGroup.query\
        .filter_by(user_id=user_id)\
        .order_by(AutoTestGroup.created_at.asc())\
        .all()

    # 构建树形结构
    group_map = {g.id: {
        'id': g.id,
        'name': g.name,
        'description': g.description,
        'parent_id': g.parent_id,
        'caseCount': len(g.cases) if g.cases else 0,
        'children': [],
        'created_at': g.created_at.isoformat() if g.created_at else None,
        'updated_at': g.updated_at.isoformat() if g.updated_at else None
    } for g in groups}

    root_groups = []
    for g in groups:
        if g.parent_id is None:
            root_groups.append(group_map[g.id])
        else:
            if g.parent_id in group_map:
                group_map[g.parent_id]['children'].append(group_map[g.id])

    return jsonify(root_groups)


@auto_test_bp.route('/auto-test/groups', methods=['POST'])
@jwt_required()
def create_group():
    """创建新分组"""
    user_id = get_jwt_identity()
    data = request.get_json()

    if not data.get('name'):
        return jsonify({'error': '分组名称不能为空'}), 400

    parent_id = data.get('parent_id')
    if parent_id is None or parent_id == 'null':
        parent_id = None

    group = AutoTestGroup(
        user_id=user_id,
        name=data['name'],
        description=data.get('description', ''),
        parent_id=parent_id
    )

    db.session.add(group)
    db.session.commit()

    return jsonify({
        'message': '创建成功',
        'id': group.id,
        'group': {
            'id': group.id,
            'name': group.name,
            'parent_id': group.parent_id
        }
    }), 201


@auto_test_bp.route('/auto-test/groups/<int:group_id>', methods=['PUT'])
@jwt_required()
def update_group(group_id):
    """更新分组"""
    user_id = get_jwt_identity()
    group = AutoTestGroup.query.get(group_id)

    if not group:
        return jsonify({'error': '分组不存在'}), 404
    if group.user_id != user_id:
        return jsonify({'error': '无权限修改'}), 403

    data = request.get_json()

    if 'name' in data:
        group.name = data['name']
    if 'description' in data:
        group.description = data['description']
    if 'parent_id' in data:
        parent_id = data['parent_id']
        if parent_id is None or parent_id == 'null':
            parent_id = None
        group.parent_id = parent_id

    db.session.commit()

    return jsonify({'message': '更新成功'})


@auto_test_bp.route('/auto-test/groups/<int:group_id>', methods=['DELETE'])
@jwt_required()
def delete_group(group_id):
    """删除分组"""
    user_id = get_jwt_identity()
    group = AutoTestGroup.query.get(group_id)

    if not group:
        return jsonify({'error': '分组不存在'}), 404
    if group.user_id != user_id:
        return jsonify({'error': '无权限删除'}), 403

    db.session.delete(group)
    db.session.commit()

    return jsonify({'message': '删除成功'})


# ========== 用例管理 ==========

@auto_test_bp.route('/auto-test/cases', methods=['GET'])
@jwt_required()
def get_cases():
    """获取当前用户的所有用例"""
    user_id = get_jwt_identity()
    # 处理空字符串安全转换为int
    folder_id_str = request.args.get('folder_id')
    folder_id = None
    if folder_id_str and folder_id_str != '':
        try:
            folder_id = int(folder_id_str)
        except (ValueError, TypeError):
            folder_id = None

    query = AutoTestCase.query.filter_by(user_id=user_id)

    if folder_id:
        query = query.filter_by(folder_id=folder_id)

    cases = query.order_by(AutoTestCase.created_at.desc()).all()

    result = []
    for case in cases:
        result.append({
            'id': case.id,
            'name': case.name,
            'method': case.method,
            'url': case.url,
            'description': case.description,
            'folder_id': case.folder_id,
            'group_id': case.folder_id,  # 🔥 前端期望的字段名
            'headers': case.headers,
            'extractors': case.extractors,
            'body': case.body,
            'payload': case.body,  # 🔥 前端期望的字段名
            'body_type': case.body_type,
            'created_at': case.created_at.isoformat() if case.created_at else None,
            'updated_at': case.updated_at.isoformat() if case.updated_at else None
        })

    return jsonify(result)


@auto_test_bp.route('/auto-test/cases/<int:case_id>', methods=['GET'])
@jwt_required()
def get_case(case_id):
    """获取单个用例详情"""
    user_id = get_jwt_identity()
    case = AutoTestCase.query.get(case_id)

    if not case:
        return jsonify({'error': '用例不存在'}), 404
    if case.user_id != user_id:
        return jsonify({'error': '无权限查看'}), 403

    return jsonify({
        'id': case.id,
        'name': case.name,
        'method': case.method,
        'url': case.url,
        'description': case.description,
        'folder_id': case.folder_id,
        'group_id': case.folder_id,  # 🔥 前端期望的字段名
        'headers': case.headers,
        'extractors': case.extractors,
        'assertions': case.assertions,
        'body': case.body,
        'payload': case.body,  # 🔥 前端期望的字段名
        'body_type': case.body_type,
        'created_at': case.created_at.isoformat() if case.created_at else None,
        'updated_at': case.updated_at.isoformat() if case.updated_at else None
    })


@auto_test_bp.route('/auto-test/cases', methods=['POST'])
@jwt_required()
def create_case():
    """创建新用例"""
    user_id = get_jwt_identity()
    data = request.get_json()

    if not data.get('name'):
        return jsonify({'error': '用例名称不能为空'}), 400
    if not data.get('url'):
        return jsonify({'error': 'URL不能为空'}), 400

    # 🔥 防御修复：必须选择所属项目（分组），避免 NOT NULL 约束失败
    project_id = data.get('project_id') or data.get('group_id') or data.get('folder_id')
    if not project_id:
        return jsonify({'error': '保存失败：必须选择所属项目/分组！'}), 400

    # 字段映射：前端 group_id → folder_id, payload → body
    # headers 前端是数组 [{"key": "xxx", "value": "xxx", description: "xxx"}], 直接 JSON 序列化保存
    headers_val = data.get('headers')
    if isinstance(headers_val, list):
        headers_val = json.dumps(headers_val, ensure_ascii=False)
    elif headers_val is None:
        headers_val = '[]'

    # extractors 前端是数组，直接 JSON 序列化保存
    extractors_val = data.get('extractors')
    if isinstance(extractors_val, list):
        extractors_val = json.dumps(extractors_val, ensure_ascii=False)
    elif extractors_val is None:
        extractors_val = '[]'

    # assertions 前端是数组，直接 JSON 序列化保存
    assertions_val = data.get('assertions') or data.get('assert_rules')
    if isinstance(assertions_val, list):
        assertions_val = json.dumps(assertions_val, ensure_ascii=False)
    elif assertions_val is None:
        assertions_val = '[]'

    body_val = data.get('payload') or data.get('body', '')
    if isinstance(body_val, (dict, list)):
        body_val = json.dumps(body_val, ensure_ascii=False)

    case = AutoTestCase(
        user_id=user_id,
        folder_id=data.get('group_id') or data.get('folder_id'),
        name=data['name'],
        method=data.get('method', 'GET'),
        url=data['url'],
        description=data.get('description', ''),
        headers=headers_val,
        extractors=extractors_val,
        assertions=assertions_val,
        body=body_val,
        body_type=data.get('body_type', 'json')
    )

    db.session.add(case)
    db.session.commit()

    return jsonify({
        'message': '创建成功',
        'id': case.id
    }), 201


@auto_test_bp.route('/auto-test/cases/<int:case_id>', methods=['PUT'])
@jwt_required()
def update_case(case_id):
    """更新用例"""
    user_id = get_jwt_identity()
    case = AutoTestCase.query.get(case_id)

    if not case:
        return jsonify({'error': '用例不存在'}), 404
    if case.user_id != user_id:
        return jsonify({'error': '无权限修改'}), 403

    data = request.get_json()

    if 'name' in data:
        case.name = data['name']
    if 'method' in data:
        case.method = data['method']
    if 'url' in data:
        case.url = data['url']
    if 'description' in data:
        case.description = data['description']
    # 兼容 group_id 和 folder_id
    if 'group_id' in data:
        case.folder_id = data['group_id']
    elif 'folder_id' in data:
        case.folder_id = data['folder_id']
    if 'headers' in data:
        # 前端 headers 是数组 [{"key": "xxx", "value": "xxx", description: "xxx"}], 直接 JSON 序列化保存
        if isinstance(data['headers'], list):
            case.headers = json.dumps(data['headers'], ensure_ascii=False)
        elif data['headers'] is None:
            case.headers = '[]'
        else:
            case.headers = json.dumps(data['headers'], ensure_ascii=False)
    if 'extractors' in data:
        # extractors 前端是数组，直接 JSON 序列化保存
        if isinstance(data['extractors'], list):
            case.extractors = json.dumps(data['extractors'], ensure_ascii=False)
        elif data['extractors'] is None:
            case.extractors = '[]'
        else:
            case.extractors = json.dumps(data['extractors'], ensure_ascii=False)
    if 'assertions' in data or 'assert_rules' in data:
        # assertions 前端是数组，直接 JSON 序列化保存
        assertions_data = data.get('assertions') or data.get('assert_rules')
        if isinstance(assertions_data, list):
            case.assertions = json.dumps(assertions_data, ensure_ascii=False)
        elif assertions_data is None:
            case.assertions = '[]'
        else:
            case.assertions = json.dumps(assertions_data, ensure_ascii=False)
    # 兼容 payload 和 body
    if 'payload' in data:
        body_val = data['payload']
        if isinstance(body_val, (dict, list)):
            case.body = json.dumps(body_val, ensure_ascii=False)
        else:
            case.body = body_val
    elif 'body' in data:
        body_val = data['body']
        if isinstance(body_val, (dict, list)):
            case.body = json.dumps(body_val, ensure_ascii=False)
        else:
            case.body = body_val
    if 'body_type' in data:
        case.body_type = data['body_type']

    db.session.commit()

    return jsonify({'message': '更新成功'})


@auto_test_bp.route('/auto-test/cases/<int:case_id>', methods=['DELETE'])
@jwt_required()
def delete_case(case_id):
    """删除用例 - 暴力清除所有关联幽灵数据"""
    user_id = get_jwt_identity()
    from backend.models.models import (
        AutoTestCase, AutoTestStep,
        InterfaceTestReportResult, AutoTestReportResult
    )
    case = AutoTestCase.query.get(case_id)

    if not case:
        return jsonify({'error': '用例不存在'}), 404
    if case.user_id != user_id:
        return jsonify({'error': '无权限删除'}), 403

    # 🔍 调试打印：输出各关联表引用计数
    steps_count = AutoTestStep.query.filter_by(api_case_id=case_id).count()
    interface_result_count = InterfaceTestReportResult.query.filter_by(case_id=case_id).count()
    auto_result_count = AutoTestReportResult.query.filter_by(case_id=case_id).count()
    print(f"\n[DEBUG] 删除接口ID {case_id} 引用计数 -> 场景步骤: {steps_count}, 接口结果: {interface_result_count}, 自动化结果: {auto_result_count}")

    # 🔥 焦土政策：无差别清除所有关联该接口的幽灵数据
    # 1. 删除所有场景步骤中关联该接口的记录
    AutoTestStep.query.filter_by(api_case_id=case_id).delete(synchronize_session=False)

    # 2. 删除接口测试历史报告结果中关联该用例的记录
    InterfaceTestReportResult.query.filter_by(case_id=case_id).delete(synchronize_session=False)

    # 3. 删除自动化测试报告结果中关联该用例的记录
    AutoTestReportResult.query.filter_by(case_id=case_id).delete(synchronize_session=False)

    # 4. 最后删除接口本身
    db.session.delete(case)
    db.session.commit()

    print(f"[DEBUG] 删除接口ID {case_id} 完成！")
    return jsonify({'message': '接口及所有幽灵关联数据已彻底粉碎！'}), 200


# ========== 从在线接口测试导入 ==========

@auto_test_bp.route('/auto-test/import-from-interface', methods=['POST'])
@jwt_required()
def import_from_interface():
    """
    从在线接口测试用例导入到自动化测试用例
    请求体: { "case_ids": [1, 2, 3], "folder_id": 1 }
    """
    user_id = get_jwt_identity()
    data = request.get_json()

    if not data.get('case_ids') or not isinstance(data['case_ids'], list):
        return jsonify({'error': '请选择要导入的用例'}), 400

    case_ids = data['case_ids']
    folder_id = data.get('folder_id')  # 可选，导入到指定分组

    # 获取在线接口测试用例
    interface_cases = InterfaceTestCase.query.filter(
        InterfaceTestCase.id.in_(case_ids)
    ).all()

    if not interface_cases:
        return jsonify({'error': '未找到指定的接口测试用例'}), 404

    imported_count = 0
    imported_ids = []

    for interface_case in interface_cases:
        # 检查是否已存在同名的用例（可选：避免重复）
        existing = AutoTestCase.query.filter_by(
            user_id=user_id,
            name=interface_case.name,
            url=interface_case.url
        ).first()

        if existing:
            continue  # 跳过已存在的用例

        # 创建新的自动化测试用例
        auto_case = AutoTestCase(
            user_id=user_id,
            folder_id=folder_id,
            name=interface_case.name,
            method=interface_case.method,
            url=interface_case.url,
            description=interface_case.description or '',
            headers=interface_case.headers or '{}',
            body=interface_case.body or '',
            body_type=interface_case.body_type or 'json'
        )

        db.session.add(auto_case)
        imported_ids.append(auto_case.id)
        imported_count += 1

    db.session.commit()

    return jsonify({
        'message': f'成功导入 {imported_count} 个用例',
        'imported_count': imported_count,
        'imported_ids': imported_ids
    }), 201


@auto_test_bp.route('/auto-test/available-for-import', methods=['GET'])
@jwt_required()
def get_available_for_import():
    """
    获取可导入的在线接口测试用例列表
    用于在导入对话框中展示
    """
    user_id = get_jwt_identity()

    # 获取所有公开的或属于当前用户的接口测试用例
    cases = InterfaceTestCase.query.filter(
        db.or_(
            InterfaceTestCase.is_public == True,
            InterfaceTestCase.user_id == user_id
        )
    ).order_by(InterfaceTestCase.created_at.desc()).all()

    # 获取已导入的用例ID（避免重复导入提示）
    existing_auto_cases = AutoTestCase.query.filter_by(user_id=user_id).all()
    existing_urls = set()
    for ac in existing_auto_cases:
        existing_urls.add((ac.name, ac.url))

    result = []
    for case in cases:
        is_already_imported = (case.name, case.url) in existing_urls
        result.append({
            'id': case.id,
            'name': case.name,
            'description': case.description,
            'method': case.method,
            'url': case.url,
            'folder_id': case.folder_id,
            'is_public': case.is_public,
            'already_imported': is_already_imported
        })

    return jsonify(result)


# ========== 批量操作 ==========

@auto_test_bp.route('/auto-test/cases/batch-delete', methods=['POST'])
@jwt_required()
def batch_delete_cases():
    """批量删除用例"""
    user_id = get_jwt_identity()
    data = request.get_json()

    if not data.get('case_ids') or not isinstance(data['case_ids'], list):
        return jsonify({'error': '请选择要删除的用例'}), 400

    case_ids = data['case_ids']

    # 删除属于当前用户的用例
    deleted_count = AutoTestCase.query.filter(
        AutoTestCase.id.in_(case_ids),
        AutoTestCase.user_id == user_id
    ).delete(synchronize_session=False)

    db.session.commit()

    return jsonify({
        'message': f'成功删除 {deleted_count} 个用例',
        'deleted_count': deleted_count
    })


# ========== 测试场景（计划）管理 ==========

@auto_test_bp.route('/auto-test/scenarios', methods=['GET'])
@jwt_required()
def get_scenarios():
    """获取当前用户的所有测试场景"""
    user_id = get_jwt_identity()
    from backend.models.models import AutoTestPlan, AutoTestStep
    scenarios = AutoTestPlan.query\
        .filter_by(user_id=user_id)\
        .order_by(AutoTestPlan.created_at.desc())\
        .all()

    result = []
    for s in scenarios:
        # 解析 case_ids
        case_ids = []
        try:
            case_ids = json.loads(s.case_ids)
        except:
            pass

        # 动态计算步骤数量
        step_count = AutoTestStep.query\
            .filter_by(scenario_id=s.id, is_active=True)\
            .count()

        result.append({
            'id': s.id,
            'name': s.name,
            'description': s.description,
            'environment_id': s.environment_id,
            'cron_expression': getattr(s, 'cron_expression', None),
            'webhook_url': getattr(s, 'webhook_url', None),
            'webhook_token': getattr(s, 'webhook_token', None),
            'case_count': len(case_ids) if case_ids else 0,
            'step_count': step_count,
            'is_active': True,
            'created_at': s.created_at.isoformat() if s.created_at else None,
            'updated_at': s.updated_at.isoformat() if s.updated_at else None
        })

    return jsonify(result)


@auto_test_bp.route('/auto-test/scenarios', methods=['POST'])
@jwt_required()
def create_scenario():
    """创建新测试场景"""
    user_id = get_jwt_identity()
    data = request.get_json()

    if not data.get('name'):
        return jsonify({'error': '场景名称不能为空'}), 400

    from backend.models.models import AutoTestPlan
    from backend.extensions import db

    case_ids = data.get('case_ids', [])

    try:
        scenario = AutoTestPlan(
            user_id=user_id,
            name=data.get('name'),
            description=data.get('description', ''),
            environment_id=data.get('environment_id'),
            cron_expression=data.get('cron_expression'),
            webhook_url=data.get('webhook_url'),
            case_ids=json.dumps(case_ids)
        )

        db.session.add(scenario)
        db.session.commit()

        return jsonify({
            'message': '创建成功',
            'id': scenario.id,
            'scenario': {
                'id': scenario.id,
                'name': scenario.name,
                'description': scenario.description,
                'cron_expression': scenario.cron_expression,
                'webhook_url': scenario.webhook_url
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'创建场景失败: {str(e)}'}), 500


# ========== 定时任务 ==========

@auto_test_bp.route('/auto-test/scheduler/tasks', methods=['GET'])
@jwt_required()
def get_scheduler_tasks():
    """获取定时任务列表"""
    user_id = get_jwt_identity()
    from backend.models.models import ScheduledTask, AutoTestPlan
    from sqlalchemy import text
    tasks = ScheduledTask.query\
        .filter_by(user_id=user_id)\
        .order_by(ScheduledTask.id.desc())\
        .all()

    # 手动查询环境名称，因为 environment 模型没有在本模块定义，无法使用 relationship
    env_names = {}
    env_ids = [task.env_id for task in tasks if task.env_id]
    if env_ids:
        try:
            # 直接 SQL 查询环境名称（使用模型定义的真实表名）
            query = text("SELECT id, name FROM interface_test_environments WHERE id IN (" + ",".join(map(str, env_ids)) + ")")
            with db.engine.connect() as conn:
                rows = conn.execute(query)
                for row in rows:
                    env_names[row.id] = row.name
        except Exception as e:
            print(f"[get_scheduler_tasks] 查询环境名称失败: {e}")

    result = []
    for task in tasks:
        scenario = AutoTestPlan.query.get(task.scenario_id)
        env_name = env_names.get(task.env_id) if task.env_id else None
        result.append({
            'id': task.id,
            'name': task.name or (scenario.name if scenario else f'任务 {task.id}'),
            'scenario_id': task.scenario_id,
            'scenario_name': scenario.name if scenario else '已删除',
            'cron_expression': task.cron_expression,
            'env_id': task.env_id,
            'env_name': env_name,
            'webhook_url': task.webhook_url,
            'is_active': task.is_active,
            'last_run_at': task.last_run_at.isoformat() if task.last_run_at else None,
            'created_at': task.created_at.isoformat() if hasattr(task, 'created_at') and task.created_at else None
        })
    return jsonify(result)


@auto_test_bp.route('/auto-test/scheduler/tasks', methods=['POST'])
@jwt_required()
def create_scheduler_task():
    """创建定时任务"""
    user_id = get_jwt_identity()
    from backend.models.models import ScheduledTask
    data = request.get_json()

    if not data.get('scenario_id'):
        return jsonify({'error': '必须选择测试场景'}), 400
    if not data.get('cron_expression'):
        return jsonify({'error': 'Cron 表达式不能为空'}), 400

    task = ScheduledTask(
        user_id=user_id,
        scenario_id=data['scenario_id'],
        name=data.get('name'),
        cron_expression=data['cron_expression'],
        env_id=data.get('env_id'),
        webhook_url=data.get('webhook_url'),
        is_active=data.get('is_active', True)
    )
    db.session.add(task)
    db.session.commit()

    # 同步到 APScheduler：如果任务禁用，立即暂停
    from flask import current_app
    job_id = f'task_{task.id}'
    scheduler = current_app.scheduler
    try:
        if not task.is_active:
            scheduler.pause_job(job_id)
    except Exception as e:
        print(f"[Scheduler Create] 暂停任务 {job_id} 失败: {e}")

    return jsonify({
        'message': '创建成功',
        'id': task.id,
        'task': {
            'id': task.id,
            'name': task.name,
            'scenario_id': task.scenario_id,
            'cron_expression': task.cron_expression
        }
    }), 201


@auto_test_bp.route('/auto-test/scheduler/tasks/<int:task_id>', methods=['PUT'])
@jwt_required()
def update_scheduler_task(task_id):
    """更新定时任务"""
    user_id = get_jwt_identity()
    from backend.models.models import ScheduledTask
    task = ScheduledTask.query.filter_by(id=task_id, user_id=user_id).first()

    if not task:
        return jsonify({'error': '任务不存在'}), 404

    data = request.get_json()
    if 'name' in data:
        task.name = data['name']
    if 'cron_expression' in data:
        task.cron_expression = data['cron_expression']
    if 'env_id' in data:
        task.env_id = data['env_id']
    if 'webhook_url' in data:
        task.webhook_url = data['webhook_url']
    if 'is_active' in data:
        task.is_active = data['is_active']

    db.session.commit()

    # 同步到 APScheduler：根据 is_active 状态暂停或恢复
    from flask import current_app
    job_id = f'task_{task_id}'
    scheduler = current_app.scheduler
    try:
        if task.is_active:
            scheduler.resume_job(job_id)
        else:
            scheduler.pause_job(job_id)
    except Exception as e:
        print(f"[Scheduler Update] 同步任务 {job_id} 状态失败: {e}")

    return jsonify({'success': True, 'message': '更新成功'})


@auto_test_bp.route('/auto-test/scheduler/tasks/<int:task_id>', methods=['DELETE'])
@jwt_required()
def delete_scheduler_task(task_id):
    """删除定时任务"""
    user_id = get_jwt_identity()
    from backend.models.models import ScheduledTask
    task = ScheduledTask.query.filter_by(id=task_id, user_id=user_id).first()

    if not task:
        return jsonify({'error': '任务不存在'}), 404

    db.session.delete(task)
    db.session.commit()
    return jsonify({'success': True, 'message': '删除成功'})


@auto_test_bp.route('/auto-test/scheduler/tasks/<int:task_id>/toggle', methods=['POST'])
@jwt_required()
def toggle_scheduler_task(task_id):
    """启动/暂停定时任务"""
    from flask import current_app
    user_id = get_jwt_identity()
    from backend.models.models import ScheduledTask
    task = ScheduledTask.query.filter_by(id=task_id, user_id=user_id).first()

    if not task:
        return jsonify({'error': '任务不存在'}), 404

    # 翻转状态
    task.is_active = not task.is_active
    db.session.commit()

    # 操作 APScheduler 引擎：暂停/恢复
    job_id = f'task_{task_id}'
    scheduler = current_app.scheduler
    try:
        if task.is_active:
            scheduler.resume_job(job_id)
        else:
            scheduler.pause_job(job_id)
    except Exception as e:
        print(f"[Scheduler Toggle] 操作任务 {job_id} 失败: {e}")
        # 即使调度器操作失败，数据库状态已经翻转，不影响用户使用

    status = '启用' if task.is_active else '暂停'
    return jsonify({
        'success': True,
        'message': f'已{status}任务',
        'is_active': task.is_active
    })


# ========== 场景详情和编辑 ==========

@auto_test_bp.route('/auto-test/scenarios/<int:scenario_id>', methods=['GET'])
@jwt_required()
def get_scenario_detail(scenario_id):
    """获取场景详情，包含完整步骤信息"""
    user_id = get_jwt_identity()
    from backend.models.models import AutoTestPlan, AutoTestStep
    scenario = AutoTestPlan.query.filter_by(id=scenario_id, user_id=user_id).first()

    if not scenario:
        return jsonify({'error': '场景不存在'}), 404

    # 获取所有步骤
    steps = AutoTestStep.query\
        .filter_by(scenario_id=scenario_id)\
        .order_by(AutoTestStep.step_order)\
        .all()

    steps_data = []
    for step in steps:
        steps_data.append({
            'id': step.id,
            'scenario_id': step.scenario_id,
            'api_case_id': step.api_case_id,
            'step_order': step.step_order,
            'is_active': step.is_active,
            'variable_overrides': json.loads(step.variable_overrides) if step.variable_overrides else None,
            'extractors': json.loads(step.extractors) if step.extractors else None,
            'api_case': {
                'id': step.api_case.id,
                'name': step.api_case.name,
                'url': step.api_case.url,
                'method': step.api_case.method,
                'headers': step.api_case.headers,
                'body': step.api_case.body,
                'body_type': step.api_case.body_type
            } if step.api_case else None
        })

    # 获取数据集（如果有）
    dataset = None
    if hasattr(scenario, 'data_matrix') and scenario.data_matrix:
        try:
            dataset = json.loads(scenario.data_matrix)
        except:
            dataset = None

    return jsonify({
        'id': scenario.id,
        'name': scenario.name,
        'description': scenario.description,
        'is_active': scenario.is_active,
        'environment_id': scenario.environment_id,
        'cron_expression': getattr(scenario, 'cron_expression', None),
        'webhook_url': getattr(scenario, 'webhook_url', None),
        'webhook_token': getattr(scenario, 'webhook_token', None),
        'steps': steps_data,
        'data_matrix': dataset
    })


@auto_test_bp.route('/auto-test/scenarios/<int:scenario_id>', methods=['PUT'])
@jwt_required()
def update_scenario(scenario_id):
    """更新场景基本信息"""
    user_id = get_jwt_identity()
    from backend.models.models import AutoTestPlan
    scenario = AutoTestPlan.query.filter_by(id=scenario_id, user_id=user_id).first()

    if not scenario:
        return jsonify({'error': '场景不存在'}), 404

    data = request.get_json()
    if 'name' in data and data['name']:
        scenario.name = data['name']
    if 'description' in data:
        scenario.description = data['description']
    if 'is_active' in data:
        scenario.is_active = data['is_active']
    if 'environment_id' in data:
        scenario.environment_id = data['environment_id']
    if 'cron_expression' in data:
        scenario.cron_expression = data['cron_expression']
    if 'webhook_url' in data:
        scenario.webhook_url = data['webhook_url']

    scenario.updated_at = datetime.utcnow()
    db.session.commit()

    return jsonify({'success': True, 'message': '更新成功'})


@auto_test_bp.route('/auto-test/scenarios/<int:scenario_id>', methods=['DELETE'])
@jwt_required()
def delete_scenario(scenario_id):
    """删除场景及其所有步骤"""
    user_id = get_jwt_identity()
    from backend.models.models import AutoTestPlan, AutoTestStep, InterfaceTestReport
    scenario = AutoTestPlan.query.filter_by(id=scenario_id, user_id=user_id).first()

    if not scenario:
        return jsonify({'error': '场景不存在'}), 404

    # 级联删除：先删除所有历史报告（只删除当前用户的）
    InterfaceTestReport.query.filter_by(plan_id=scenario_id, user_id=user_id).delete()
    # 级联删除：再删除所有步骤
    AutoTestStep.query.filter_by(scenario_id=scenario_id).delete()
    # 最后删除场景本身
    db.session.delete(scenario)
    db.session.commit()

    return jsonify({'success': True, 'message': '删除成功'})


# ========== 场景步骤操作 ==========

@auto_test_bp.route('/auto-test/scenarios/<int:scenario_id>/steps', methods=['POST'])
@jwt_required()
def add_scenario_step(scenario_id):
    """添加场景步骤"""
    user_id = get_jwt_identity()
    from backend.models.models import AutoTestPlan, AutoTestStep, AutoTestCase
    scenario = AutoTestPlan.query.filter_by(id=scenario_id, user_id=user_id).first()

    if not scenario:
        return jsonify({'error': '场景不存在'}), 404

    data = request.get_json()
    api_case_id = data.get('api_case_id')
    step_order = data.get('step_order', 0)
    is_active = data.get('is_active', True)

    api_case = AutoTestCase.query.get(api_case_id)
    if not api_case:
        return jsonify({'error': '接口用例不存在'}), 404

    step = AutoTestStep(
        scenario_id=scenario_id,
        api_case_id=api_case_id,
        step_order=step_order,
        is_active=is_active
    )
    db.session.add(step)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': '添加成功',
        'id': step.id
    }), 201


@auto_test_bp.route('/auto-test/scenarios/<int:scenario_id>/steps/<int:step_id>', methods=['PUT'])
@jwt_required()
def update_scenario_step(scenario_id, step_id):
    """更新场景步骤"""
    user_id = get_jwt_identity()
    from backend.models.models import AutoTestPlan, AutoTestStep
    scenario = AutoTestPlan.query.filter_by(id=scenario_id, user_id=user_id).first()

    if not scenario:
        return jsonify({'error': '场景不存在'}), 404

    step = AutoTestStep.query.filter_by(id=step_id, scenario_id=scenario_id).first()
    if not step:
        return jsonify({'error': '步骤不存在'}), 404

    data = request.get_json()
    if 'is_active' in data:
        step.is_active = data['is_active']
    if 'variable_overrides' in data:
        step.variable_overrides = json.dumps(data['variable_overrides'], ensure_ascii=False)
    if 'extractors' in data:
        if data['extractors'] is None:
            step.extractors = None
        else:
            step.extractors = json.dumps(data['extractors'], ensure_ascii=False)

    db.session.commit()
    return jsonify({'success': True, 'message': '更新成功'})


@auto_test_bp.route('/auto-test/scenarios/<int:scenario_id>/steps/<int:step_id>', methods=['DELETE'])
@jwt_required()
def delete_scenario_step(scenario_id, step_id):
    """删除场景步骤"""
    user_id = get_jwt_identity()
    from backend.models.models import AutoTestPlan, AutoTestStep
    scenario = AutoTestPlan.query.filter_by(id=scenario_id, user_id=user_id).first()

    if not scenario:
        return jsonify({'error': '场景不存在'}), 404

    step = AutoTestStep.query.filter_by(id=step_id, scenario_id=scenario_id).first()
    if not step:
        return jsonify({'error': '步骤不存在'}), 404

    db.session.delete(step)
    db.session.commit()

    return jsonify({'success': True, 'message': '删除成功'})


@auto_test_bp.route('/auto-test/scenarios/<int:scenario_id>/steps/reorder', methods=['PUT'])
@jwt_required()
def reorder_scenario_steps(scenario_id):
    """重新排序场景步骤"""
    user_id = get_jwt_identity()
    from backend.models.models import AutoTestPlan, AutoTestStep
    scenario = AutoTestPlan.query.filter_by(id=scenario_id, user_id=user_id).first()

    if not scenario:
        return jsonify({'error': '场景不存在'}), 404

    data = request.get_json()
    step_orders = data  # 期望格式: [{step_id: 1, step_order: 0}, ...]

    for item in step_orders:
        step = AutoTestStep.query.filter_by(
            id=item['step_id'],
            scenario_id=scenario_id
        ).first()
        if step:
            step.step_order = item['step_order']

    db.session.commit()
    return jsonify({'success': True, 'message': '排序保存成功'})


# ========== 数据驱动数据集 ==========

@auto_test_bp.route('/auto-test/scenarios/<int:scenario_id>/dataset', methods=['GET'])
@jwt_required()
def get_scenario_dataset(scenario_id):
    """获取场景数据驱动数据集"""
    user_id = get_jwt_identity()
    from backend.models.models import AutoTestPlan
    scenario = AutoTestPlan.query.filter_by(id=scenario_id, user_id=user_id).first()

    if not scenario:
        return jsonify({'error': '场景不存在'}), 404

    if not scenario.data_matrix:
        return jsonify({
            'scenario_id': scenario_id,
            'data_matrix': None
        })

    try:
        data_matrix = json.loads(scenario.data_matrix)
    except:
        data_matrix = None

    return jsonify({
        'scenario_id': scenario_id,
        'data_matrix': data_matrix
    })


@auto_test_bp.route('/auto-test/scenarios/<int:scenario_id>/dataset', methods=['POST'])
@jwt_required()
def save_scenario_dataset(scenario_id):
    """保存场景数据驱动数据集"""
    user_id = get_jwt_identity()
    from backend.models.models import AutoTestPlan
    scenario = AutoTestPlan.query.filter_by(id=scenario_id, user_id=user_id).first()

    if not scenario:
        return jsonify({'error': '场景不存在'}), 404

    data = request.get_json()
    data_matrix = data.get('data_matrix')

    scenario.data_matrix = json.dumps(data_matrix, ensure_ascii=False)
    scenario.updated_at = datetime.utcnow()
    db.session.commit()

    return jsonify({
        'success': True,
        'message': '数据集保存成功'
    })


@auto_test_bp.route('/auto-test/scenarios/<int:scenario_id>/dataset', methods=['DELETE'])
@jwt_required()
def delete_scenario_dataset(scenario_id):
    """删除场景数据驱动数据集"""
    user_id = get_jwt_identity()
    from backend.models.models import AutoTestPlan
    scenario = AutoTestPlan.query.filter_by(id=scenario_id, user_id=user_id).first()

    if not scenario:
        return jsonify({'error': '场景不存在'}), 404

    scenario.data_matrix = None
    scenario.updated_at = datetime.utcnow()
    db.session.commit()

    return jsonify({
        'success': True,
        'message': '数据集已清空'
    })


# ========== 场景执行 ==========

@auto_test_bp.route('/auto-test/scenarios/<int:scenario_id>/run', methods=['POST'])
@jwt_required()
def run_scenario(scenario_id):
    """异步执行场景 - 立即返回 task_id，前端轮询查询结果"""
    user_id = get_jwt_identity()
    from backend.models.models import AutoTestPlan, AutoTestStep
    from backend.extensions import db

    scenario = AutoTestPlan.query.filter_by(id=scenario_id, user_id=user_id).first()
    if not scenario:
        return jsonify({'error': '场景不存在'}), 404

    # 获取前端传来的 env_id（安全容错）
    # silent=True: 解析 JSON 失败不抛出异常，返回 None
    data = request.get_json(silent=True) or {}
    env_id_raw = data.get('env_id')

    # 安全转换 env_id：空字符串、null、0 都转为 None
    # 只接受非空的整数 ID
    env_id = None
    if env_id_raw not in (None, '', 0, '0'):
        try:
            env_id = int(env_id_raw)
        except (ValueError, TypeError):
            env_id = None

    # 获取步骤数量做快速验证
    steps = AutoTestStep.query\
        .filter_by(scenario_id=scenario_id, is_active=True)\
        .order_by(AutoTestStep.step_order)\
        .all()

    total_steps = len(steps)
    if total_steps == 0:
        return jsonify({'error': '场景没有可用步骤'}), 400

    # 提交 Celery 异步任务（单字典传参格式）
    from backend.celery_tasks import run_scenario_async
    # 从请求中获取可选的 webhook_url（手动触发也支持传入 Webhook）
    webhook_url = data.get('webhook_url')
    task_data = {
        'scenario_id': scenario_id,
        'user_id': user_id,
        'env_id': env_id,
        'webhook_url': webhook_url
    }
    task = run_scenario_async.delay(task_data)

    return jsonify({
        'code': 200,
        'msg': '任务已提交，请通过 task_id 查询执行结果',
        'data': {
            'task_id': task.id,
            'scenario_id': scenario_id,
            'scenario_name': scenario.name,
            'total_steps': total_steps
        }
    })


@auto_test_bp.route('/auto-test/tasks/<task_id>', methods=['GET'])
@jwt_required()
def get_task_status(task_id):
    """查询 Celery 异步任务状态和结果"""
    from celery.result import AsyncResult
    from backend.celery_worker import celery_app

    result = AsyncResult(task_id, app=celery_app)

    response = {
        'task_id': task_id,
        'status': result.state,  # PENDING / STARTED / PROGRESS / SUCCESS / FAILURE
    }

    if result.state == 'SUCCESS':
        data = result.get(timeout=5)
        # 【修复】直接将 celery task 返回的数据合并到顶层，保持与前端访问方式一致
        response.update(data)
        response['status'] = 'completed'
    elif result.state == 'FAILURE':
        response['error'] = str(result.info) if result.info else '任务执行失败'
    elif result.state == 'PROGRESS':
        response['progress'] = result.info
    elif result.state == 'PENDING':
        response['message'] = '任务等待中...'
    else:
        response['message'] = f'任务状态: {result.state}'

    return jsonify(response)


@auto_test_bp.route('/auto-test/tasks/<task_id>/cancel', methods=['POST'])
@jwt_required()
def cancel_task(task_id):
    """强制终止正在执行的 Celery 任务"""
    from backend.celery_worker import celery_app
    from celery.app.control import Control

    try:
        # 使用 Celery control 撤销任务并强制终止进程
        celery_app.control.revoke(task_id, terminate=True, signal='SIGKILL')
        return jsonify({
            'code': 200,
            'msg': '任务已强制终止'
        }), 200
    except Exception as e:
        return jsonify({
            'code': 500,
            'error': f'终止任务失败: {str(e)}'
        }), 500


@auto_test_bp.route('/auto-test/reports/<int:report_id>', methods=['GET'])
@jwt_required()
def get_report_detail(report_id):
    """获取场景执行报告详情（包含所有步骤结果）"""
    from backend.models.models import InterfaceTestReport, InterfaceTestReportResult
    user_id = get_jwt_identity()

    report = InterfaceTestReport.query.filter_by(id=report_id, user_id=user_id).first()
    if not report:
        return jsonify({'error': '报告不存在'}), 404

    # 获取所有步骤结果 - 严格按 report_id 过滤，绝对不能按 scenario_id/plan_id 过滤
    # 修复数据穿透问题：必须只返回当前报告的步骤，不能返回该场景下所有历史步骤
    step_results = InterfaceTestReportResult.query.filter_by(report_id=report.id).order_by(InterfaceTestReportResult.id).all()

    # 格式化步骤结果
    formatted_steps = []
    for step in step_results:
        # 解析 JSON 字段
        try:
            request_headers = json.loads(step.request_headers) if step.request_headers else {}
        except:
            request_headers = {}
        try:
            request_body = json.loads(step.request_body) if step.request_body else {}
        except:
            request_body = step.request_body
        try:
            response = json.loads(step.response) if step.response else {}
        except:
            response = step.response
        try:
            response_headers = json.loads(step.response_headers) if step.response_headers else {}
        except:
            response_headers = {}

        formatted_steps.append({
            'id': step.id,
            'step_id': step.case_id,
            'api_case_name': step.case_name,
            'method': step.method,
            'url': step.url,
            'status_code': step.status_code,
            'success': step.success,
            'status': 'success' if step.success else 'failed',
            'error': step.error,
            'duration': step.time,
            'request_headers': request_headers,
            'request_body': request_body,
            'response': response,
            'response_headers': response_headers
        })

    # 获取 report_url，容错处理（旧数据没有该字段）
    report_url = getattr(report, 'report_url', None)
    if not report_url:
        report_url = f'/reports/{report.id}/index.html'

    return jsonify({
        'id': report.id,
        'plan_id': report.plan_id,
        'plan_name': report.plan_name,
        'status': report.status,
        'total_steps': len(formatted_steps),
        'success_steps': len([s for s in formatted_steps if s['success']]),
        'failed_steps': len([s for s in formatted_steps if not s['success']]),
        'total_time': report.total_time,
        'executed_at': report.executed_at.isoformat() if report.executed_at else None,
        'report_url': report_url,
        'step_results': formatted_steps,
        'context_vars': {}
    })


def execute_single_step(step, context_vars):
    """执行单个场景步骤"""
    from backend.models.models import AutoTestCase
    api_case = step.api_case
    if not api_case:
        return {
            'success': False,
            'error': '关联的接口用例不存在',
            'url': None,
            'status_code': None,
            'extracted_vars': {}
        }

    # 获取原始请求信息，应用变量覆盖
    url = apply_variables((step.variable_overrides and step.variable_overrides.get('url')) or api_case.url, context_vars)
    method = api_case.method

    # 处理 Headers
    headers = {}
    try:
        if api_case.headers:
            headers = json.loads(api_case.headers)
    except:
        pass

    # 应用局部变量覆盖
    if step.variable_overrides and 'headers' in step.variable_overrides:
        for key, value in step.variable_overrides['headers'].items():
            headers[key] = apply_variables(value, context_vars)

    # 处理 Body
    body = api_case.body
    body_type = api_case.body_type or 'json'

    # 发送请求
    try:
        import requests
        req_kwargs = {
            'headers': headers,
            'timeout': 30,
            'allow_redirects': True
        }

        if method in ['POST', 'PUT', 'PATCH'] and body:
            if body_type == 'json' and body.strip():
                try:
                    req_kwargs['json'] = json.loads(body)
                except:
                    req_kwargs['data'] = body
            else:
                req_kwargs['data'] = body

        step_start_time = datetime.utcnow()
        response = requests.request(method, url, **req_kwargs)
        duration_ms = int((datetime.utcnow() - step_start_time).total_seconds() * 1000)

        # ========== Bug1 修复：状态码拦截 ==========
        # 只要状态码 >= 400，强制标记失败
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
        # ========== Bug1 修复结束 ==========

        success = 200 <= response.status_code < 400

        return {
            'success': success,
            'url': url,
            'method': method,
            'status_code': response.status_code,
            'response': response.text[:10000],
            'duration': duration_ms,
            'request_headers': headers,
            'request_body': body,
            'response_headers': dict(response.headers),
            'extracted_vars': {}
        }
    except Exception as e:
        return {
            'success': False,
            'url': url,
            'error': str(e),
            'status_code': None,
            'extracted_vars': {}
        }


def apply_variables(template, context):
    """替换变量 {{var}} 格式"""
    if not template or not context:
        return template
    if not isinstance(template, str):
        return template

    import re
    def replace_match(match):
        var_name = match.group(1).strip()
        return str(context.get(var_name, match.group(0)))

    return re.sub(r'\{\{\s*(\w+)\s*\}\}', replace_match, template)


@auto_test_bp.route('/auto-test/scenarios/<int:scenario_id>/run-data-driven', methods=['POST'])
@jwt_required()
def run_scenario_data_driven(scenario_id):
    """数据驱动执行场景"""
    user_id = get_jwt_identity()
    from backend.models.models import AutoTestPlan, AutoTestStep, InterfaceTestEnvironment
    scenario = AutoTestPlan.query.filter_by(id=scenario_id, user_id=user_id).first()

    if not scenario:
        return jsonify({'error': '场景不存在'}), 404

    # 获取数据集：优先从 scenario.data_matrix 读取，兼容前端直接传来的 JSON
    data_matrix = None
    data = request.get_json(silent=True) or {}

    # 安全获取 env_id
    env_id_raw = data.get('env_id')
    env_id = None
    if env_id_raw not in (None, '', 0, '0'):
        try:
            env_id = int(env_id_raw)
        except (ValueError, TypeError):
            env_id = None

    if data and 'data_matrix' in data:
        # 前端直接传来 data_matrix（内联方式）
        data_matrix = data['data_matrix']
    elif scenario.data_matrix:
        try:
            data_matrix = json.loads(scenario.data_matrix)
        except:
            return jsonify({'error': '数据集格式错误'}), 400

    if not data_matrix:
        return jsonify({'error': '没有找到数据集'}), 400

    columns = data_matrix.get('columns', [])
    rows = data_matrix.get('rows', [])

    if not rows or len(rows) == 0:
        return jsonify({'error': '数据集为空'}), 400

    # ========== 加载环境变量（所有迭代共享） ==========
    # 优先级：数据行变量 > 环境变量
    base_env_vars = {}
    if env_id:
        env = InterfaceTestEnvironment.query.filter_by(id=env_id, user_id=user_id).first()
        if env:
            if env.variables:
                try:
                    if isinstance(env.variables, str):
                        base_env_vars = json.loads(env.variables)
                    else:
                        base_env_vars = env.variables
                except Exception:
                    base_env_vars = {}
            if env.base_url and 'base_url' not in base_env_vars:
                base_env_vars['base_url'] = env.base_url

    # 获取所有激活的步骤
    steps = AutoTestStep.query\
        .filter_by(scenario_id=scenario_id, is_active=True)\
        .order_by(AutoTestStep.step_order)\
        .all()

    if not steps:
        return jsonify({'error': '场景没有可用步骤'}), 400

    # 逐行执行
    iterations = []
    success_iterations = 0
    failed_iterations = 0
    total_duration = 0

    for row_index, row_data in enumerate(rows):
        iteration_start = datetime.utcnow()
        # 用当前行数据初始化 context
        iteration_context = dict(zip(columns, row_data))
        # 合并环境变量（环境变量优先级低于数据行，不覆盖）
        for k, v in base_env_vars.items():
            if k not in iteration_context:
                iteration_context[k] = v

        iteration_passed = True
        iteration_errors = []
        step_results = []

        for step in steps:
            step_result = execute_single_step(step, iteration_context)
            if step_result['success']:
                step_results.append({
                    'step_id': step.id,
                    'api_case_name': step.api_case.name if step.api_case else 'Unknown',
                    'status': 'success',
                    'status_code': step_result.get('status_code'),
                    'duration': step_result.get('duration', 0)
                })
                # 提取变量到迭代上下文
                if step_result.get('extracted_vars'):
                    iteration_context.update(step_result['extracted_vars'])
            else:
                iteration_passed = False
                iteration_errors.append(f"步骤 {step.id} 执行失败: {step_result.get('error', '未知错误')}")
                step_results.append({
                    'step_id': step.id,
                    'api_case_name': step.api_case.name if step.api_case else 'Unknown',
                    'status': 'failed',
                    'status_code': step_result.get('status_code'),
                    'error': step_result.get('error'),
                    'duration': step_result.get('duration', 0)
                })
                # 如果某步骤失败，后续步骤跳过
                break

        iteration_duration = int((datetime.utcnow() - iteration_start).total_seconds() * 1000)
        total_duration += iteration_duration

        if iteration_passed:
            success_iterations += 1
        else:
            failed_iterations += 1

        iterations.append({
            'iteration_index': row_index,
            'data_row': dict(zip(columns, row_data)),
            'step_results': step_results,
            'success': iteration_passed,
            'duration': iteration_duration,
            'error': '; '.join(iteration_errors) if iteration_errors else None
        })

    return jsonify({
        'scenario_id': scenario_id,
        'scenario_name': scenario.name,
        'dataset_name': data_matrix.get('name', 'default'),
        'total_iterations': len(rows),
        'success_iterations': success_iterations,
        'failed_iterations': failed_iterations,
        'total_duration': total_duration,
        'iterations': iterations
    })


@auto_test_bp.route('/auto-test/scenarios/<int:scenario_id>/history', methods=['GET'])
@jwt_required()
def get_scenario_history(scenario_id):
    """获取场景执行历史"""
    user_id = get_jwt_identity()
    from backend.models.models import InterfaceTestReport
    page_str = request.args.get('page', '1')
    per_page_str = request.args.get('per_page', '20')

    try:
        page = int(page_str)
        per_page = int(per_page_str)
    except:
        page = 1
        per_page = 20

    reports = InterfaceTestReport.query\
        .filter_by(user_id=user_id, plan_id=scenario_id)\
        .order_by(InterfaceTestReport.executed_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)

    items = []
    for report in reports.items:
        items.append({
            'id': report.id,
            'status': report.status,
            'total_steps': report.total_count,
            'success_steps': report.success_count,
            'failed_steps': report.failed_count,
            'total_time': report.total_time,
            'created_at': report.executed_at.isoformat() if report.executed_at else None
        })

    return jsonify({
        'total': reports.total,
        'page': reports.page,
        'pages': reports.pages,
        'items': items
    })


@auto_test_bp.route('/auto-test/scenarios/available-cases', methods=['GET'])
@jwt_required()
def get_available_cases():
    """获取可添加到场景的接口用例列表"""
    user_id = get_jwt_identity()
    from backend.models.models import AutoTestCase

    keyword = request.args.get('keyword', '')
    query = AutoTestCase.query.filter_by(user_id=user_id)

    if keyword:
        query = query.filter(
            (AutoTestCase.name.contains(keyword)) | (AutoTestCase.url.contains(keyword))
        )

    cases = query.order_by(AutoTestCase.created_at.desc()).limit(100).all()

    result = []
    for case in cases:
        result.append({
            'id': case.id,
            'name': case.name,
            'url': case.url,
            'method': case.method,
            'folder_id': case.folder_id
        })

    return jsonify(result)


@auto_test_bp.route('/auto-test/scenarios/history/<int:history_id>', methods=['DELETE'])
@jwt_required()
def delete_scenario_history(history_id):
    """手动删除单条执行历史记录（同时删除物理文件和数据库记录）"""
    from backend.models.models import InterfaceTestReport, InterfaceTestReportResult
    from backend.extensions import db
    import os
    import shutil
    from sqlalchemy import text

    user_id = get_jwt_identity()

    # 查找报告，必须匹配用户ID
    report = InterfaceTestReport.query.filter_by(id=history_id, user_id=user_id).first()
    if not report:
        return jsonify({'error': '报告不存在或无权限删除'}), 404

    try:
        # 1. 物理删除硬盘上的 Allure 报告文件夹
        reports_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'reports'
        )
        reports_dir = os.path.abspath(reports_dir)
        report_output_dir = os.path.join(reports_dir, str(history_id))

        if os.path.exists(report_output_dir):
            try:
                shutil.rmtree(report_output_dir)
                print(f"[DeleteHistory] 已删除物理文件: {report_output_dir}")
            except Exception as e:
                print(f"[DeleteHistory] ⚠️  删除物理文件失败: {e}（继续删除数据库记录）")

        # 2. 先删除所有步骤结果（正确表名是复数 interface_test_report_results）
        db.session.execute(
            text("DELETE FROM interface_test_report_results WHERE report_id = :report_id"),
            {"report_id": history_id}
        )
        # 3. 再删除报告主记录
        db.session.delete(report)
        db.session.commit()

        return jsonify({
            'code': 200,
            'message': '删除成功'
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'error': f'删除失败: {str(e)}'
        }), 500


# ========== CI/CD Webhook 外部触发 ==========
@auto_test_bp.route('/auto-test/scenarios/webhook/<string:token>', methods=['POST'])
def trigger_scenario_by_webhook(token):
    """CI/CD 外部触发自动化测试 - 公开接口，不需要JWT认证"""
    from backend.models.models import AutoTestPlan, ScheduledTask
    from backend.celery_tasks import run_scenario_async

    # 1. 验证 token
    scenario = AutoTestPlan.query.filter_by(webhook_token=token).first()
    if not scenario:
        return jsonify({
            'code': 404,
            'error': '无效的 Webhook Token'
        }), 404

    # 2. 接收外部传来的环境ID（可选）
    data = request.get_json() or {}
    env_id = data.get('env_id')

    # 兜底逻辑：如果请求体没传，找场景绑定的；如果场景没绑，强制给个保底值！
    if not env_id:
        if scenario.environment_id:
            env_id = scenario.environment_id
        else:
            # 保底：默认测试服环境 ID 是 4
            env_id = 4
    # 确保是整数
    if env_id:
        env_id = int(env_id)

    # 3. 查询该场景绑定的定时任务，获取 webhook_url
    scheduled_task = ScheduledTask.query.filter_by(scenario_id=scenario.id).first()
    if scheduled_task and scheduled_task.webhook_url:
        current_webhook_url = scheduled_task.webhook_url
    else:
        # 降级：如果没有定时任务，使用场景自身的 webhook_url
        current_webhook_url = scenario.webhook_url

    # 4. 异步推送到 Celery 执行，记在创建者名下
    task_data = {
        'scenario_id': scenario.id,
        'user_id': scenario.user_id,
        'env_id': env_id,
        'webhook_url': current_webhook_url
    }
    task = run_scenario_async.delay(task_data)

    # 返回成功
    return jsonify({
        'code': 200,
        'msg': '自动化测试已触发',
        'task_id': task.id,
        'scenario_name': scenario.name
    })