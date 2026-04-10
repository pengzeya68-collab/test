# Skills statistics and radar chart API for TestMasterProject
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models.models import User, Exercise, Progress
from ..extensions import db
from datetime import datetime, timedelta

skills_bp = Blueprint('skills', __name__)

# 技能维度定义
SKILL_DIMENSIONS = {
    'test_theory': {
        'name': '测试基础理论',
        'description': '软件测试基础概念、测试方法、测试流程、测试模型等',
        'weight': 0.15
    },
    'functional_test': {
        'name': '功能测试',
        'description': 'Web/APP/小程序功能测试、测试用例设计、缺陷管理等',
        'weight': 0.15
    },
    'api_test': {
        'name': '接口测试',
        'description': 'HTTP协议、接口测试方法、接口自动化、接口测试工具等',
        'weight': 0.15
    },
    'automation_test': {
        'name': '自动化测试',
        'description': 'UI自动化、接口自动化、自动化框架设计、持续集成等',
        'weight': 0.15
    },
    'performance_test': {
        'name': '性能测试',
        'description': '性能测试方法、性能指标、Jmeter使用、性能调优等',
        'weight': 0.1
    },
    'programming': {
        'name': '编程能力',
        'description': 'Python/Shell等编程语言、数据结构、算法等',
        'weight': 0.1
    },
    'database': {
        'name': '数据库能力',
        'description': 'SQL语法、数据库设计、数据库测试、性能优化等',
        'weight': 0.1
    },
    'linux': {
        'name': 'Linux能力',
        'description': 'Linux常用命令、Shell脚本、环境部署、日志排查等',
        'weight': 0.05
    }
}

# 各阶段对应的技能点
STAGE_SKILLS = {
    1: ['test_theory', 'database', 'linux'],
    2: ['functional_test', 'test_theory'],
    3: ['api_test', 'database', 'linux', 'programming'],
    4: ['automation_test', 'api_test', 'programming', 'performance_test'],
    5: ['automation_test', 'performance_test', 'programming']
}

# 技能维度 → 习题分类/语言 的映射（用于从 Progress 表关联查询）
SKILL_CATEGORY_MAP = {
    'test_theory': {
        'categories': ['测试基础', '测试用例设计', '功能测试'],
        'languages': ['通用'],
    },
    'functional_test': {
        'categories': ['功能测试', '测试用例设计', '测试基础'],
        'languages': ['通用'],
    },
    'api_test': {
        'categories': ['接口测试'],
        'languages': ['通用'],
        'modules': ['api'],
    },
    'automation_test': {
        'categories': ['自动化测试'],
        'languages': ['Python', 'Java'],
        'modules': ['automation'],
    },
    'performance_test': {
        'categories': ['性能测试'],
        'languages': ['通用'],
    },
    'programming': {
        'categories': ['Python编程', 'Java编程', 'Shell脚本'],
        'languages': ['Python', 'Java', 'Shell'],
    },
    'database': {
        'categories': ['SQL查询', '数据库'],
        'languages': ['SQL'],
    },
    'linux': {
        'categories': ['Linux命令', 'Shell脚本'],
        'languages': ['Linux', 'Shell'],
    },
}

def calculate_skill_score(user_id, skill_key):
    """
    根据用户真实答题记录计算技能得分（0-100）。
    计算逻辑：
      - 找出与该技能维度相关的所有习题（按 category / language / module 匹配）
      - 统计用户在这些习题中的 完成数量 和 平均得分
      - 基础分 = 完成率 * 70（最高 70 分）
      - 质量分 = 平均正确率 * 30（最高 30 分）
      - 如果该技能完全没有相关习题，则分数为 0
    """
    mapping = SKILL_CATEGORY_MAP.get(skill_key, {})
    categories = mapping.get('categories', [])
    languages = mapping.get('languages', [])
    modules = mapping.get('modules', [])

    # 查找该技能关联的习题
    q = Exercise.query.filter(Exercise.is_public == True)
    conditions = []
    from sqlalchemy import or_
    if categories:
        conditions.append(Exercise.category.in_(categories))
    if languages:
        conditions.append(Exercise.language.in_(languages))
    if modules:
        conditions.append(Exercise.module.in_(modules))

    if conditions:
        q = q.filter(or_(*conditions))

    related_exercises = q.all()
    total_exercises = len(related_exercises)

    if total_exercises == 0:
        return 0

    exercise_ids = [e.id for e in related_exercises]

    # 查询用户在这些习题上的进度记录
    user_progress = Progress.query.filter(
        Progress.user_id == user_id,
        Progress.exercise_id.in_(exercise_ids)
    ).all()

    if not user_progress:
        return 0

    completed = [p for p in user_progress if p.completed]
    completion_rate = len(completed) / total_exercises  # 0~1

    # 质量分：有得分记录的取平均；没有则按完成数量给满
    scores_with_value = [p.score for p in user_progress if p.score is not None]
    if scores_with_value:
        avg_score_rate = sum(scores_with_value) / (len(scores_with_value) * 100)  # 归一化到 0~1
    else:
        # 没有评分信息，按完成率估算质量
        avg_score_rate = completion_rate

    base_score = completion_rate * 70
    quality_score = avg_score_rate * 30
    total = round(base_score + quality_score)

    return min(total, 100)

def get_skill_level(score):
    """根据得分获取技能等级"""
    if score >= 90:
        return '专家'
    elif score >= 80:
        return '精通'
    elif score >= 70:
        return '熟练'
    elif score >= 60:
        return '掌握'
    elif score >= 40:
        return '了解'
    else:
        return '入门'

def get_improvement_suggestion(skill_key, score):
    """获取技能提升建议"""
    suggestions = {
        'test_theory': {
            'low': '建议先学习软件测试基础概念、测试流程和测试模型，多做测试用例设计练习。',
            'medium': '可以深入学习测试方法论、测试策略制定，尝试参与测试计划编写。',
            'high': '可以研究测试左移、测试右移等先进理念，探索质量体系建设。'
        },
        'functional_test': {
            'low': '多练习Web/APP功能测试，学习测试用例设计方法和缺陷管理流程。',
            'medium': '可以学习专项测试（兼容性、易用性、安全性），提升测试深度。',
            'high': '可以尝试测试流程优化、测试方法创新，提升整体测试效率。'
        },
        'api_test': {
            'low': '先学习HTTP协议基础，掌握Postman等接口测试工具的使用。',
            'medium': '学习接口自动化测试，掌握Requests库和Pytest框架的使用。',
            'high': '可以研究接口自动化框架设计，接入CI/CD流程。'
        },
        'automation_test': {
            'low': '先掌握Python编程基础，学习Selenium/Appium等自动化工具的基本使用。',
            'medium': '学习自动化框架设计，掌握PageObject、数据驱动等设计模式。',
            'high': '可以研究自动化测试平台开发，提升自动化测试覆盖率和稳定性。'
        },
        'performance_test': {
            'low': '先学习性能测试基础概念和指标，掌握Jmeter的基本使用。',
            'medium': '学习性能场景设计、性能监控和瓶颈分析方法。',
            'high': '可以研究全链路压测、性能调优等高级技术。'
        },
        'programming': {
            'low': '从Python基础语法开始学习，多做编程练习题，提升编码能力。',
            'medium': '学习面向对象编程，掌握常用库和框架的使用，多做实战项目。',
            'high': '可以学习数据结构和算法，提升代码质量和性能。'
        },
        'database': {
            'low': '先学习SQL基础语法，掌握常用的增删改查和多表查询。',
            'medium': '学习数据库设计、索引优化、存储过程等高级特性。',
            'high': '可以研究数据库性能优化、分布式数据库等高级技术。'
        },
        'linux': {
            'low': '先学习Linux常用命令，掌握文件操作、进程管理、网络配置等基础操作。',
            'medium': '学习Shell脚本编写，掌握日志排查、环境部署等技能。',
            'high': '可以研究Linux系统优化、自动化运维等高级技术。'
        }
    }
    
    suggestion = suggestions.get(skill_key, {})
    if score < 60:
        return suggestion.get('low', '继续加油，多练习就能提升！')
    elif score < 80:
        return suggestion.get('medium', '继续深入学习，提升技能水平！')
    else:
        return suggestion.get('high', '已经很优秀了，可以尝试更高难度的挑战！')

@skills_bp.route('/skills/radar', methods=['GET'])
@jwt_required()
def get_skill_radar():
    """获取用户技能雷达图数据"""
    user_id = get_jwt_identity()
    
    # 计算各项技能得分
    skills_data = []
    total_score = 0
    
    for key, config in SKILL_DIMENSIONS.items():
        score = calculate_skill_score(user_id, key)
        total_score += score * config['weight']
        skills_data.append({
            'key': key,
            'name': config['name'],
            'description': config['description'],
            'score': score,
            'level': get_skill_level(score),
            'suggestion': get_improvement_suggestion(key, score),
            'weight': config['weight']
        })
    
    # 计算综合能力得分
    overall_score = round(total_score, 1)
    overall_level = get_skill_level(overall_score)
    
    # 行业平均数据（用于对比）
    industry_average = [
        {'name': '测试基础理论', 'score': 75},
        {'name': '功能测试', 'score': 70},
        {'name': '接口测试', 'score': 60},
        {'name': '自动化测试', 'score': 45},
        {'name': '性能测试', 'score': 35},
        {'name': '编程能力', 'score': 55},
        {'name': '数据库能力', 'score': 65},
        {'name': 'Linux能力', 'score': 50}
    ]
    
    return jsonify({
        'overall_score': overall_score,
        'overall_level': overall_level,
        'skills': skills_data,
        'industry_average': industry_average,
        'radar_data': {
            'indicators': [{'name': s['name'], 'max': 100} for s in skills_data],
            'user_data': [s['score'] for s in skills_data],
            'industry_data': [s['score'] for s in industry_average]
        }
    }), 200

@skills_bp.route('/skills/detail/<skill_key>', methods=['GET'])
@jwt_required()
def get_skill_detail(skill_key):
    """获取单个技能的详细信息"""
    if skill_key not in SKILL_DIMENSIONS:
        return jsonify({'error': '技能不存在'}), 404
    
    user_id = get_jwt_identity()
    config = SKILL_DIMENSIONS[skill_key]
    score = calculate_skill_score(user_id, skill_key)
    
    # 获取该技能下的推荐习题
    recommended_exercises = Exercise.query.filter_by(
        category=config['name'],
        is_public=True
    ).limit(5).all()
    
    exercises = [{
        'id': ex.id,
        'title': ex.title,
        'difficulty': ex.difficulty,
        'time_estimate': ex.time_estimate
    } for ex in recommended_exercises]
    
    return jsonify({
        'key': skill_key,
        'name': config['name'],
        'description': config['description'],
        'score': score,
        'level': get_skill_level(score),
        'suggestion': get_improvement_suggestion(skill_key, score),
        'recommended_exercises': exercises
    }), 200

@skills_bp.route('/skills/progress', methods=['GET'])
@jwt_required()
def get_skill_progress():
    """获取技能提升进度（基于真实答题记录）"""
    user_id = get_jwt_identity()

    now = datetime.utcnow()
    one_month_ago = now - timedelta(days=30)

    progress_data = []

    # 只展示分数 > 0 或有做题记录的技能（过滤掉完全没动的）
    for key, config in SKILL_DIMENSIONS.items():
        current_score = calculate_skill_score(user_id, key)

        # 计算一个月前的"快照"分数：排除最近30天完成的习题后重新计算
        mapping = SKILL_CATEGORY_MAP.get(key, {})
        categories = mapping.get('categories', [])
        languages = mapping.get('languages', [])
        modules = mapping.get('modules', [])

        from sqlalchemy import or_
        q = Exercise.query.filter(Exercise.is_public == True)
        conditions = []
        if categories:
            conditions.append(Exercise.category.in_(categories))
        if languages:
            conditions.append(Exercise.language.in_(languages))
        if modules:
            conditions.append(Exercise.module.in_(modules))
        if conditions:
            q = q.filter(or_(*conditions))
        related_exercises = q.all()
        total_exercises = len(related_exercises)

        monthly_growth = 0
        if total_exercises > 0:
            exercise_ids = [e.id for e in related_exercises]
            # 近30天新增完成的习题数
            recent_completed = Progress.query.filter(
                Progress.user_id == user_id,
                Progress.exercise_id.in_(exercise_ids),
                Progress.completed == True,
                Progress.completed_at >= one_month_ago
            ).count()
            # 近30天增长分 = (新增完成/总题数) * 70 粗略估算
            monthly_growth = round((recent_completed / total_exercises) * 70)

        # 目标：当前技能分 + 20，最高 100
        target = min(current_score + 20, 100)
        if current_score >= 80:
            target = 100

        if current_score > 0 or monthly_growth > 0:
            item = {
                'skill': config['name'],
                'current': current_score,
                'target': target,
                'monthly_growth': monthly_growth
            }
            remaining = target - current_score
            if monthly_growth > 0 and remaining > 0:
                item['months_needed'] = round(remaining / monthly_growth, 1)
            elif remaining <= 0:
                item['months_needed'] = 0
            else:
                item['months_needed'] = None
            progress_data.append(item)

    # 按当前分数降序，最多展示6个有进展的技能
    progress_data.sort(key=lambda x: x['current'], reverse=True)
    progress_data = progress_data[:6]

    return jsonify({
        'progress': progress_data,
        'last_updated': now.strftime('%Y-%m-%d')
    }), 200
