# Interview System API for TestMasterProject
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models.models import InterviewQuestion, InterviewSession, InterviewQuestionRecord, InterviewQuestionCollection
from ..extensions import db
from datetime import datetime
import json
import random

interview_bp = Blueprint('interview', __name__)

def format_question(question, user_id=None):
    """格式化面试题"""
    data = {
        'id': question.id,
        'title': question.title,
        'content': question.content or '',
        'category': question.category,
        'difficulty': question.difficulty,
        'position_level': question.position_level,
        'tags': question.tags.split(',') if question.tags else [],
        'company': question.company,
        'view_count': question.view_count,
        'collect_count': question.collect_count,
        'created_at': question.created_at.strftime('%Y-%m-%d %H:%M:%S')
    }
    
    # 如果传入用户ID，检查是否已收藏
    if user_id:
        collected = InterviewQuestionCollection.query.filter_by(
            user_id=user_id, 
            question_id=question.id
        ).first()
        data['is_collected'] = collected is not None
    
    return data

def format_session(session):
    """格式化面试会话"""
    return {
        'id': session.id,
        'title': session.title,
        'position': session.position,
        'level': session.level,
        'interview_type': session.interview_type,
        'total_score': session.total_score,
        'user_score': session.user_score,
        'status': session.status,
        'start_time': session.start_time.strftime('%Y-%m-%d %H:%M:%S') if session.start_time else None,
        'end_time': session.end_time.strftime('%Y-%m-%d %H:%M:%S') if session.end_time else None,
        'feedback': session.feedback,
        'improvement_suggestions': session.improvement_suggestions,
        'question_count': len(session.questions) if hasattr(session, 'questions') else 0
    }

@interview_bp.route('/interview/questions', methods=['GET'])
def get_questions():
    """获取面试题列表"""
    # 处理空字符串安全转换为int
    page_str = request.args.get('page')
    per_page_str = request.args.get('per_page')

    page = 1
    if page_str and page_str != '':
        try:
            page = int(page_str)
        except (ValueError, TypeError):
            page = 1

    per_page = 10
    if per_page_str and per_page_str != '':
        try:
            per_page = int(per_page_str)
        except (ValueError, TypeError):
            per_page = 10

    category = request.args.get('category', '')
    difficulty = request.args.get('difficulty', '')
    position_level = request.args.get('level', '')
    search = request.args.get('search', '')
    tag = request.args.get('tag', '')
    
    query = InterviewQuestion.query
    
    if category:
        query = query.filter_by(category=category)
    if difficulty:
        query = query.filter_by(difficulty=difficulty)
    if position_level:
        query = query.filter_by(position_level=position_level)
    if search:
        query = query.filter(InterviewQuestion.title.like(f'%{search}%') | InterviewQuestion.content.like(f'%{search}%'))
    if tag:
        query = query.filter(InterviewQuestion.tags.like(f'%{tag}%'))
    
    query = query.order_by(InterviewQuestion.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    questions = pagination.items
    
    # 获取当前用户ID（如果登录了）
    user_id = None
    try:
        user_id = get_jwt_identity()
    except:
        pass
    
    return jsonify({
        'list': [format_question(q, user_id) for q in questions],
        'total': pagination.total,
        'page': page,
        'per_page': per_page
    }), 200

@interview_bp.route('/interview/questions/<int:question_id>', methods=['GET'])
def get_question_detail(question_id):
    """获取面试题详情"""
    question = InterviewQuestion.query.get(question_id)
    if not question:
        return jsonify({'error': '题目不存在'}), 404
    
    # 增加浏览次数
    question.view_count += 1
    db.session.commit()
    
    # 获取当前用户ID（如果登录了）
    user_id = None
    try:
        user_id = get_jwt_identity()
    except:
        pass
    
    data = format_question(question, user_id)
    data['answer'] = question.answer  # 详情页返回答案
    
    return jsonify(data), 200

@interview_bp.route('/interview/questions/<int:question_id>/toggle-collect', methods=['POST'])
@jwt_required()
def toggle_collect_question(question_id):
    """收藏/取消收藏面试题"""
    user_id = get_jwt_identity()
    question = InterviewQuestion.query.get(question_id)
    
    if not question:
        return jsonify({'error': '题目不存在'}), 404
    
    collected = InterviewQuestionCollection.query.filter_by(
        user_id=user_id, 
        question_id=question_id
    ).first()
    
    if collected:
        # 取消收藏
        db.session.delete(collected)
        question.collect_count = max(0, question.collect_count - 1)
        action = 'uncollected'
    else:
        # 收藏
        collection = InterviewQuestionCollection(
            user_id=user_id,
            question_id=question_id
        )
        db.session.add(collection)
        question.collect_count += 1
        action = 'collected'
    
    db.session.commit()
    
    return jsonify({
        'message': f'{action == "collected" and "收藏" or "取消收藏"}成功',
        'action': action,
        'collect_count': question.collect_count
    }), 200

@interview_bp.route('/interview/my-collections', methods=['GET'])
@jwt_required()
def get_my_collections():
    """获取我收藏的面试题"""
    user_id = get_jwt_identity()
    # 处理空字符串安全转换为int
    page_str = request.args.get('page')
    per_page_str = request.args.get('per_page')

    page = 1
    if page_str and page_str != '':
        try:
            page = int(page_str)
        except (ValueError, TypeError):
            page = 1

    per_page = 10
    if per_page_str and per_page_str != '':
        try:
            per_page = int(per_page_str)
        except (ValueError, TypeError):
            per_page = 10
    
    collections = InterviewQuestionCollection.query.filter_by(user_id=user_id).order_by(
        InterviewQuestionCollection.created_at.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)
    
    questions = []
    for c in collections.items:
        q = format_question(c.question, user_id)
        q['is_collected'] = True
        questions.append(q)
    
    return jsonify({
        'list': questions,
        'total': collections.total,
        'page': page,
        'per_page': per_page
    }), 200

@interview_bp.route('/interview/sessions', methods=['GET'])
@jwt_required()
def get_my_sessions():
    """获取我的面试记录"""
    user_id = get_jwt_identity()
    # 处理空字符串安全转换为int
    page_str = request.args.get('page')
    per_page_str = request.args.get('per_page')

    page = 1
    if page_str and page_str != '':
        try:
            page = int(page_str)
        except (ValueError, TypeError):
            page = 1

    per_page = 10
    if per_page_str and per_page_str != '':
        try:
            per_page = int(per_page_str)
        except (ValueError, TypeError):
            per_page = 10

    status = request.args.get('status', '')
    
    query = InterviewSession.query.filter_by(user_id=user_id)
    
    if status:
        query = query.filter_by(status=status)
    
    query = query.order_by(InterviewSession.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    sessions = pagination.items
    
    return jsonify({
        'list': [format_session(s) for s in sessions],
        'total': pagination.total,
        'page': page,
        'per_page': per_page
    }), 200

@interview_bp.route('/interview/sessions/create', methods=['POST'])
@jwt_required()
def create_interview_session():
    """创建新的面试会话"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    position = data.get('position', '测试工程师')
    level = data.get('level', '中级')
    interview_type = data.get('type', '技术面')
    question_count = data.get('question_count', 10)
    categories = data.get('categories', [])
    
    # 从题库中随机抽取题目
    query = InterviewQuestion.query.filter_by(position_level=level)
    
    if categories:
        query = query.filter(InterviewQuestion.category.in_(categories))
    
    questions = query.order_by(db.func.random()).limit(question_count).all()
    
    # 如果题目不够，补充其他分类的题目
    if len(questions) < question_count:
        extra = InterviewQuestion.query.filter(
            InterviewQuestion.position_level == level,
            InterviewQuestion.id.notin_([q.id for q in questions])
        ).order_by(db.func.random()).limit(question_count - len(questions)).all()
        questions.extend(extra)
    
    # 创建面试会话
    session = InterviewSession(
        user_id=user_id,
        title=f'{position} {level} {interview_type}模拟面试',
        position=position,
        level=level,
        interview_type=interview_type
    )
    
    db.session.add(session)
    db.session.flush()
    
    # 添加题目到会话
    for idx, q in enumerate(questions):
        record = InterviewQuestionRecord(
            session_id=session.id,
            question_id=q.id
        )
        db.session.add(record)
    
    db.session.commit()
    
    return jsonify({
        'message': '面试会话创建成功',
        'session_id': session.id,
        'session': format_session(session)
    }), 201

@interview_bp.route('/interview/sessions/<int:session_id>', methods=['GET'])
@jwt_required()
def get_interview_session(session_id):
    """获取面试会话详情"""
    user_id = get_jwt_identity()
    session = InterviewSession.query.get(session_id)
    
    if not session:
        return jsonify({'error': '面试会话不存在'}), 404
    
    if session.user_id != user_id:
        return jsonify({'error': '无权限查看此面试'}), 403
    
    # 获取题目列表（用join预加载question避免lazy加载问题）
    from sqlalchemy.orm import joinedload
    records = InterviewQuestionRecord.query\
        .filter_by(session_id=session_id)\
        .options(joinedload(InterviewQuestionRecord.question))\
        .all()
    
    questions = []
    for record in records:
        q = format_question(record.question)
        q['record_id'] = record.id
        q['user_answer'] = record.user_answer
        q['ai_feedback'] = record.ai_feedback
        q['score'] = record.score
        q['is_answered'] = record.is_answered
        questions.append(q)
    
    return jsonify({
        'session': format_session(session),
        'questions': questions
    }), 200

@interview_bp.route('/interview/sessions/<int:session_id>/submit-answer', methods=['POST'])
@jwt_required()
def submit_answer(session_id):
    """提交面试题答案"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    record_id = data.get('record_id')
    user_answer = data.get('answer', '')
    
    record = InterviewQuestionRecord.query.get(record_id)
    if not record:
        return jsonify({'error': '答题记录不存在'}), 404
    
    if record.session.user_id != user_id:
        return jsonify({'error': '无权限操作'}), 403
    
    if record.session.status == 'completed':
        return jsonify({'error': '面试已结束'}), 400
    
    # 保存答案
    record.user_answer = user_answer
    record.is_answered = True
    
    # 简单AI评分和反馈（后续可以对接AI接口实现智能点评）
    question = record.question
    score = calculate_answer_score(user_answer, question.answer)
    feedback = generate_feedback(user_answer, question.answer, score)
    
    record.score = score
    record.ai_feedback = feedback
    
    db.session.commit()
    
    return jsonify({
        'message': '答案提交成功',
        'score': score,
        'feedback': feedback,
        'correct_answer': question.answer
    }), 200

@interview_bp.route('/interview/sessions/<int:session_id>/complete', methods=['POST'])
@jwt_required()
def complete_interview(session_id):
    """结束面试"""
    user_id = get_jwt_identity()
    session = InterviewSession.query.get(session_id)
    
    if not session:
        return jsonify({'error': '面试会话不存在'}), 404
    
    if session.user_id != user_id:
        return jsonify({'error': '无权限操作'}), 403
    
    if session.status == 'completed':
        return jsonify({'error': '面试已经结束'}), 400
    
    # 计算总分
    total_score = 0
    answered_count = 0
    for record in session.questions:
        if record.is_answered and record.score is not None:
            total_score += record.score
            answered_count += 1
    
    # 平均得分（百分制）
    if answered_count > 0:
        avg_score = total_score / answered_count
        user_score = int(avg_score * 10)  # 0-10分转百分制
    else:
        user_score = 0
    
    session.user_score = user_score
    session.status = 'completed'
    session.end_time = datetime.utcnow()
    
    # 生成总体评价和改进建议
    session.feedback = generate_overall_feedback(user_score, session.level)
    session.improvement_suggestions = generate_improvement_suggestions(session.questions)
    
    db.session.commit()
    
    return jsonify({
        'message': '面试结束',
        'score': user_score,
        'feedback': session.feedback,
        'suggestions': session.improvement_suggestions
    }), 200

def calculate_answer_score(user_answer, correct_answer):
    """简单计算答案得分（0-10分）"""
    if not user_answer or len(user_answer) < 10:
        return 2  # 回答太短
    
    # 计算关键词匹配度
    user_words = set(user_answer.lower().split())
    correct_words = set(correct_answer.lower().split())
    
    if len(correct_words) == 0:
        return 5
    
    common_words = user_words.intersection(correct_words)
    match_rate = len(common_words) / len(correct_words)
    
    if match_rate > 0.8:
        return 9
    elif match_rate > 0.6:
        return 7
    elif match_rate > 0.4:
        return 5
    elif match_rate > 0.2:
        return 3
    else:
        return 2

def generate_feedback(user_answer, correct_answer, score):
    """生成答案反馈"""
    if score >= 8:
        return "回答非常优秀！要点基本都覆盖到了，表达清晰准确，对知识点理解很透彻。"
    elif score >= 6:
        return "回答不错，核心要点都提到了，但还有一些细节可以补充，继续加油。"
    elif score >= 4:
        return "回答基本正确，但不够全面，有部分关键点遗漏，建议加强对这个知识点的理解。"
    else:
        return "回答不太理想，知识点掌握不够牢固，建议重新学习相关内容，多练习类似题目。"

def generate_overall_feedback(score, level):
    """生成总体评价"""
    if score >= 90:
        return f"🎉 恭喜你！你的{level}测试工程师面试表现非常出色，超过了90%的候选人，完全符合岗位要求！"
    elif score >= 80:
        return f"👍 表现不错！你的{level}测试工程师面试成绩良好，基本符合岗位要求，个别知识点再加强一下就更完美了。"
    elif score >= 70:
        return f"😊 表现合格！你的{level}测试工程师面试基本达标，但还有不少提升空间，建议多加练习。"
    elif score >= 60:
        return f"💪 刚刚及格！你的{level}测试工程师面试还有较大差距，需要系统学习相关知识，多做模拟面试。"
    else:
        return f"📚 还需要努力！你的{level}测试工程师面试差距较大，建议从基础开始系统学习，打好基础后再进行面试模拟。"

def generate_improvement_suggestions(questions):
    """生成改进建议"""
    # 统计各分类得分情况
    category_scores = {}
    for record in questions:
        if record.is_answered and record.score is not None:
            category = record.question.category
            if category not in category_scores:
                category_scores[category] = {'total': 0, 'count': 0}
            category_scores[category]['total'] += record.score
            category_scores[category]['count'] += 1
    
    suggestions = []
    for category, data in category_scores.items():
        avg = data['total'] / data['count']
        if avg < 6:
            suggestions.append(f"🔍 {category}方面掌握较弱，建议重点加强这部分知识的学习")
    
    if not suggestions:
        suggestions.append("✅ 各方面知识掌握都不错，建议多进行模拟面试，积累面试经验")
    
    return "\n".join(suggestions)

# 面试题分类选项
@interview_bp.route('/interview/categories', methods=['GET'])
def get_categories():
    """获取面试题分类"""
    categories = [
        {'value': '基础测试', 'label': '基础测试理论'},
        {'value': '功能测试', 'label': '功能测试'},
        {'value': '自动化测试', 'label': '自动化测试'},
        {'value': '性能测试', 'label': '性能测试'},
        {'value': '接口测试', 'label': '接口测试'},
        {'value': '数据库', 'label': '数据库知识'},
        {'value': '编程', 'label': '编程能力'},
        {'value': 'Linux', 'label': 'Linux知识'},
        {'value': 'HR面', 'label': 'HR面试'},
        {'value': '项目经验', 'label': '项目经验'},
        {'value': '职业规划', 'label': '职业规划'}
    ]
    return jsonify(categories), 200
