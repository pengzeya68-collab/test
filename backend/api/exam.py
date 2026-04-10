# Exam System API for TestMasterProject
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models.models import Exam, ExamQuestion, ExamAttempt, ExamAnswer, Exercise
from ..extensions import db
from datetime import datetime, timedelta
import json
import random
import re

exam_bp = Blueprint('exam', __name__)

def format_exam(exam, user_id=None):
    """格式化考试信息"""
    data = {
        'id': exam.id,
        'title': exam.title,
        'description': exam.description,
        'exam_type': exam.exam_type,
        'difficulty': exam.difficulty,
        'duration': exam.duration,
        'total_score': exam.total_score,
        'pass_score': exam.pass_score,
        'is_published': exam.is_published,
        'start_time': exam.start_time.strftime('%Y-%m-%d %H:%M:%S') if exam.start_time else None,
        'end_time': exam.end_time.strftime('%Y-%m-%d %H:%M:%S') if exam.end_time else None,
        'created_at': exam.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        'question_count': len(exam.questions),
        'author': {
            'id': exam.user.id,
            'username': exam.user.username
        }
    }
    
    # 如果传入用户ID，检查用户是否已经参加过考试
    if user_id:
        attempt = ExamAttempt.query.filter_by(user_id=user_id, exam_id=exam.id).order_by(ExamAttempt.created_at.desc()).first()
        if attempt:
            data['attempt_status'] = attempt.status
            data['attempt_score'] = attempt.score
            data['attempt_id'] = attempt.id
    
    return data

def format_question(question, show_answer=False):
    """格式化题目信息"""
    data = {
        'id': question.id,
        'question_type': question.question_type,
        'content': question.content,
        'score': question.score,
        'sort_order': question.sort_order
    }
    
    # 选择题返回选项
    if question.question_type in ['single_choice', 'multiple_choice']:
        data['options'] = json.loads(question.options) if question.options else []
    
    # 显示答案的情况（考试结束后）
    if show_answer:
        data['correct_answer'] = question.correct_answer
        data['analysis'] = question.analysis
    
    return data

def calculate_score(attempt):
    """计算考试得分"""
    total_score = 0
    answers = ExamAnswer.query.filter_by(attempt_id=attempt.id).all()
    
    for answer in answers:
        question = answer.question
        if question.question_type in ['single_choice', 'multiple_choice', 'true_false']:
            # 客观题自动判分
            if answer.user_answer == question.correct_answer:
                answer.is_correct = True
                answer.score = question.score
                total_score += question.score
            else:
                answer.is_correct = False
                answer.score = 0
        elif question.question_type == 'code':
            # 代码题判分 - 检查代码质量和正确性
            user_code = answer.user_answer or ''
            correct_answer = question.correct_answer or ''
            
            if not user_code:
                answer.is_correct = False
                answer.score = 0
            else:
                # 计算代码相似度（简单的字符串匹配）
                # 去除空白字符后比较
                user_code_normalized = ''.join(user_code.split()).lower()
                correct_normalized = ''.join(correct_answer.split()).lower()
                
                # 检查关键逻辑点
                score_ratio = 0
                
                # 基础分：有代码就给10%
                score_ratio = 0.1
                
                # 检查关键函数或方法名
                if correct_answer:
                    # 提取可能的函数名（简化处理）
                    func_pattern = r'def\s+(\w+)\s*\('
                    correct_funcs = set(re.findall(func_pattern, correct_answer))
                    user_funcs = set(re.findall(func_pattern, user_code))
                    
                    if correct_funcs and user_funcs:
                        common_funcs = correct_funcs.intersection(user_funcs)
                        func_match_ratio = len(common_funcs) / len(correct_funcs)
                        score_ratio += 0.3 * func_match_ratio
                
                # 检查代码长度合理性（不能太长或太短）
                if correct_answer:
                    len_ratio = len(user_code) / len(correct_answer)
                    if 0.5 <= len_ratio <= 2.0:
                        score_ratio += 0.2
                
                # 检查是否有明显的语法错误模式
                syntax_errors = ['syntax error', 'indentationerror', 'nameerror']
                if not any(err in user_code.lower() for err in syntax_errors):
                    score_ratio += 0.2
                
                # 检查是否包含关键逻辑关键词
                if correct_answer:
                    # 简单的关键词匹配
                    correct_keywords = set(re.findall(r'\b\w+\b', correct_answer.lower()))
                    user_keywords = set(re.findall(r'\b\w+\b', user_code.lower()))
                    common_keywords = correct_keywords.intersection(user_keywords)
                    if correct_keywords:
                        keyword_ratio = len(common_keywords) / len(correct_keywords)
                        score_ratio += 0.2 * keyword_ratio
                
                # 确保分数在合理范围内
                score_ratio = min(1.0, max(0, score_ratio))
                
                answer.score = int(question.score * score_ratio)
                answer.is_correct = answer.score >= question.score * 0.6
                total_score += answer.score
        else:
            # 主观题暂时不给分，需要人工评分
            answer.is_correct = None
            answer.score = 0
    
    attempt.score = total_score
    attempt.is_passed = total_score >= attempt.exam.pass_score
    attempt.status = 'graded'
    
    db.session.commit()
    return total_score

@exam_bp.route('/exams', methods=['GET'])
def get_exams():
    """获取考试列表"""
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

    exam_type = request.args.get('type', '')
    difficulty = request.args.get('difficulty', '')
    search = request.args.get('search', '')
    
    query = Exam.query.filter_by(is_published=True)
    
    if exam_type:
        query = query.filter_by(exam_type=exam_type)
    if difficulty:
        query = query.filter_by(difficulty=difficulty)
    if search:
        query = query.filter(Exam.title.like(f'%{search}%') | Exam.description.like(f'%{search}%'))
    
    # 按创建时间倒序
    query = query.order_by(Exam.created_at.desc())
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    exams = pagination.items
    
    # 获取当前用户ID（如果登录了）
    user_id = None
    try:
        user_id = get_jwt_identity()
    except:
        pass
    
    return jsonify({
        'list': [format_exam(exam, user_id) for exam in exams],
        'total': pagination.total,
        'page': page,
        'per_page': per_page
    }), 200

@exam_bp.route('/exams/<int:exam_id>', methods=['GET'])
def get_exam_detail(exam_id):
    """获取考试详情（包含题目列表）"""
    exam = Exam.query.get(exam_id)
    if not exam:
        return jsonify({'error': '考试不存在'}), 404
    
    if not exam.is_published:
        return jsonify({'error': '考试未发布'}), 403
    
    # 获取当前用户ID（如果登录了）
    user_id = None
    try:
        user_id = get_jwt_identity()
    except:
        pass
    
    # 格式化考试信息 + 题目列表
    data = format_exam(exam, user_id)
    # 按顺序返回所有题目
    questions = [format_question(q) for q in exam.questions.order_by(ExamQuestion.sort_order).all()]
    data['questions'] = questions
    
    return jsonify(data), 200

@exam_bp.route('/exams/<int:exam_id>', methods=['DELETE'])
@jwt_required()
def delete_exam(exam_id):
    """删除考试"""
    user_id = get_jwt_identity()
    exam = Exam.query.get(exam_id)
    
    if not exam:
        return jsonify({'error': '考试不存在'}), 404
    
    # 检查权限：只能删除自己创建的考试
    if exam.user_id != user_id:
        return jsonify({'error': '无权限删除此考试'}), 403
    
    # 检查是否有正在进行的考试尝试
    in_progress_attempt = ExamAttempt.query.filter_by(
        exam_id=exam_id, 
        status='in_progress'
    ).first()
    
    if in_progress_attempt:
        return jsonify({'error': '有用户正在进行此考试，无法删除'}), 400
    
    try:
        # 删除相关的考试答案
        ExamAnswer.query.filter(
            ExamAnswer.attempt_id.in_(
                db.session.query(ExamAttempt.id).filter_by(exam_id=exam_id)
            )
        ).delete(synchronize_session=False)
        
        # 删除考试尝试记录
        ExamAttempt.query.filter_by(exam_id=exam_id).delete(synchronize_session=False)
        
        # 删除考试题目
        ExamQuestion.query.filter_by(exam_id=exam_id).delete(synchronize_session=False)
        
        # 删除考试
        db.session.delete(exam)
        db.session.commit()
        
        return jsonify({'message': '考试删除成功'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'删除失败: {str(e)}'}), 500

@exam_bp.route('/exams/<int:exam_id>/questions', methods=['GET'])
@jwt_required()
def get_exam_questions(exam_id):
    """获取考试题目（开始考试时调用）"""
    user_id = get_jwt_identity()
    exam = Exam.query.get(exam_id)
    
    if not exam:
        return jsonify({'error': '考试不存在'}), 404
    
    if not exam.is_published:
        return jsonify({'error': '考试未发布'}), 403
    
    # 检查考试时间
    now = datetime.utcnow()
    if exam.start_time and now < exam.start_time:
        return jsonify({'error': '考试尚未开始'}), 403
    if exam.end_time and now > exam.end_time:
        return jsonify({'error': '考试已结束'}), 403
    
    # 检查用户是否已经有正在进行的考试
    existing_attempt = ExamAttempt.query.filter_by(
        user_id=user_id, 
        exam_id=exam_id, 
        status='in_progress'
    ).first()
    
    if existing_attempt:
        # 返回已有的考试尝试
        attempt_id = existing_attempt.id
    else:
        # 创建新的考试尝试
        attempt = ExamAttempt(
            user_id=user_id,
            exam_id=exam_id,
            start_time=now
        )
        db.session.add(attempt)
        db.session.commit()
        attempt_id = attempt.id
    
    # 返回题目（不包含答案）
    questions = ExamQuestion.query.filter_by(exam_id=exam_id).order_by(ExamQuestion.sort_order).all()
    
    return jsonify({
        'attempt_id': attempt_id,
        'exam': format_exam(exam),
        'questions': [format_question(q) for q in questions]
    }), 200

@exam_bp.route('/exams/attempts/<int:attempt_id>/submit', methods=['POST'])
@jwt_required()
def submit_exam(attempt_id):
    """提交考试"""
    user_id = get_jwt_identity()
    attempt = ExamAttempt.query.get(attempt_id)
    
    if not attempt:
        return jsonify({'error': '考试记录不存在'}), 404
    
    if attempt.user_id != user_id:
        return jsonify({'error': '无权限操作此考试'}), 403
    
    if attempt.status != 'in_progress':
        return jsonify({'error': '考试已经提交过了'}), 400
    
    data = request.get_json()
    answers = data.get('answers', [])
    
    # 保存用户答案
    for ans in answers:
        question_id = ans.get('question_id')
        user_answer = ans.get('answer', '')
        
        answer = ExamAnswer(
            attempt_id=attempt_id,
            question_id=question_id,
            user_answer=user_answer
        )
        db.session.add(answer)
    
    # 更新考试状态
    attempt.end_time = datetime.utcnow()
    attempt.status = 'submitted'
    db.session.commit()
    
    # 自动判分
    total_score = calculate_score(attempt)
    
    return jsonify({
        'message': '考试提交成功',
        'score': total_score,
        'is_passed': attempt.is_passed,
        'attempt_id': attempt_id
    }), 200

@exam_bp.route('/exams/attempts/<int:attempt_id>/result', methods=['GET'])
@jwt_required()
def get_exam_result(attempt_id):
    """获取考试结果"""
    user_id = get_jwt_identity()
    attempt = ExamAttempt.query.get(attempt_id)
    
    if not attempt:
        return jsonify({'error': '考试记录不存在'}), 404
    
    if attempt.user_id != user_id:
        return jsonify({'error': '无权限查看此考试结果'}), 403
    
    if attempt.status == 'in_progress':
        return jsonify({'error': '考试尚未提交'}), 400
    
    # 获取用户答案和正确答案
    answers = ExamAnswer.query.filter_by(attempt_id=attempt_id).all()
    result = []
    
    for ans in answers:
        question = ans.question
        result.append({
            'question': format_question(question, show_answer=True),
            'user_answer': ans.user_answer,
            'is_correct': ans.is_correct,
            'score': ans.score,
            'feedback': ans.feedback
        })
    
    # 统计各题型得分
    question_types = {}
    for item in result:
        q_type = item['question']['question_type']
        if q_type not in question_types:
            question_types[q_type] = {
                'total': 0,
                'correct': 0,
                'score': 0,
                'total_score': 0
            }
        question_types[q_type]['total'] += 1
        question_types[q_type]['total_score'] += item['question']['score']
        if item['is_correct']:
            question_types[q_type]['correct'] += 1
        question_types[q_type]['score'] += item['score'] or 0
    
    return jsonify({
        'exam': format_exam(attempt.exam),
        'attempt': {
            'id': attempt.id,
            'start_time': attempt.start_time.strftime('%Y-%m-%d %H:%M:%S'),
            'end_time': attempt.end_time.strftime('%Y-%m-%d %H:%M:%S'),
            'duration': int((attempt.end_time - attempt.start_time).total_seconds() / 60),
            'score': attempt.score,
            'is_passed': attempt.is_passed,
            'status': attempt.status
        },
        'result': result,
        'statistics': {
            'total_questions': len(result),
            'correct_count': sum(1 for item in result if item['is_correct']),
            'wrong_count': sum(1 for item in result if not item['is_correct'] and item['is_correct'] is not False),
            'score_rate': round(attempt.score / attempt.exam.total_score * 100, 1) if attempt.exam.total_score > 0 else 0,
            'question_type_stats': question_types
        }
    }), 200

@exam_bp.route('/exams/my-attempts', methods=['GET'])
@jwt_required()
def get_my_attempts():
    """获取我的考试记录"""
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
    
    query = ExamAttempt.query.filter_by(user_id=user_id).order_by(ExamAttempt.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    attempts = pagination.items
    
    result = []
    for attempt in attempts:
        result.append({
            'id': attempt.id,
            'exam_title': attempt.exam.title,
            'exam_type': attempt.exam.exam_type,
            'score': attempt.score,
            'total_score': attempt.exam.total_score,
            'is_passed': attempt.is_passed,
            'status': attempt.status,
            'created_at': attempt.created_at.strftime('%Y-%m-%d %H:%M:%S')
        })
    
    return jsonify({
        'list': result,
        'total': pagination.total,
        'page': page,
        'per_page': per_page
    }), 200

@exam_bp.route('/exams/generate', methods=['POST'])
@jwt_required()
def generate_exam():
    """智能生成试卷 - 从习题库中随机抽取题目"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    exam_type = data.get('exam_type', '模拟考试')
    difficulty = data.get('difficulty', 'medium')
    duration = data.get('duration', 60)
    knowledge_points = data.get('knowledge_points', [])
    question_count = data.get('question_count', {
        'single_choice': 10,
        'multiple_choice': 5,
        'true_false': 5,
        'code': 2
    })
    
    import random
    
    # 从习题库中随机抽取题目组成试卷
    questions = []
    total_score = 0
    used_exercise_ids = set()  # 避免重复抽取同一道题
    
    def get_random_exercises(query, count):
        """从查询结果中随机抽取指定数量的题目"""
        all_exercises = query.all()
        available = [e for e in all_exercises if e.id not in used_exercise_ids]
        if len(available) <= count:
            selected = available
        else:
            selected = random.sample(available, count)
        for e in selected:
            used_exercise_ids.add(e.id)
        return selected
    
    # 单选题 - 从multiple_choice中筛选单选题（答案只有一个字母）
    if question_count.get('single_choice', 0) > 0:
        # 查询所有multiple_choice类型的题目，然后根据答案判断是单选还是多选
        all_mc = Exercise.query.filter(
            Exercise.exercise_type == 'multiple_choice',
            Exercise.difficulty == difficulty,
            Exercise.is_public == True
        ).all()
        
        # 筛选单选题：答案长度为1且是单个字母
        single_choices = [e for e in all_mc if e.solution and len(e.solution.strip()) == 1 and e.solution.strip() in 'ABCDEF']
        
        # 随机抽取
        if len(single_choices) > question_count['single_choice']:
            single_choices = random.sample(single_choices, question_count['single_choice'])
        
        for q in single_choices:
            used_exercise_ids.add(q.id)
            # 从description中解析选项
            options = parse_options_from_content(q.description)
            questions.append({
                'type': 'single_choice',
                'content': q.title,
                'options': json.dumps(options),
                'correct_answer': q.solution.strip().upper(),
                'score': 2,
                'analysis': q.description
            })
            total_score += 2
    
    # 多选题 - 从multiple_choice中筛选多选题（答案包含逗号或多个字母）
    if question_count.get('multiple_choice', 0) > 0:
        all_mc = Exercise.query.filter(
            Exercise.exercise_type == 'multiple_choice',
            Exercise.difficulty == difficulty,
            Exercise.is_public == True
        ).all()
        
        # 筛选多选题：答案包含逗号或长度大于1
        multiple_choices = [e for e in all_mc if e.solution and (',' in e.solution or len(e.solution.strip()) > 1) and e.id not in used_exercise_ids]
        
        if len(multiple_choices) > question_count['multiple_choice']:
            multiple_choices = random.sample(multiple_choices, question_count['multiple_choice'])
        
        for q in multiple_choices:
            used_exercise_ids.add(q.id)
            options = parse_options_from_content(q.description)
            # 标准化答案格式
            answer = q.solution.strip().upper()
            if ',' in answer:
                answer = ','.join([a.strip() for a in answer.split(',')])
            questions.append({
                'type': 'multiple_choice',
                'content': q.title,
                'options': json.dumps(options),
                'correct_answer': answer,
                'score': 4,
                'analysis': q.description
            })
            total_score += 4
    
    # 判断题
    if question_count.get('true_false', 0) > 0:
        true_false = get_random_exercises(
            Exercise.query.filter(
                Exercise.exercise_type == 'true_false',
                Exercise.difficulty == difficulty,
                Exercise.is_public == True
            ),
            question_count['true_false']
        )
        
        for q in true_false:
            # 标准化答案
            answer = q.solution.strip().lower()
            if answer in ['true', 't', 'yes', 'y', '正确', '对', '是']:
                answer = 'true'
            else:
                answer = 'false'
            
            questions.append({
                'type': 'true_false',
                'content': q.title,
                'correct_answer': answer,
                'score': 2,
                'analysis': q.description
            })
            total_score += 2
    
    # 代码题
    if question_count.get('code', 0) > 0:
        code_questions = get_random_exercises(
            Exercise.query.filter(
                Exercise.exercise_type == 'code',
                Exercise.difficulty == difficulty,
                Exercise.is_public == True
            ),
            question_count['code']
        )
        
        for q in code_questions:
            questions.append({
                'type': 'code',
                'content': q.title + '\n\n' + (q.description or ''),
                'correct_answer': q.solution or '',
                'score': 20,
                'analysis': q.description
            })
            total_score += 20
    
    # 如果没有抽到足够的题目，从其他难度补充
    total_needed = sum(question_count.values())
    if len(questions) < total_needed * 0.5:  # 如果抽到的题目不足50%
        return jsonify({
            'error': f'题库中{difficulty}难度的题目不足，请尝试其他难度或联系管理员添加更多题目'
        }), 400
    
    # 创建试卷
    exam = Exam(
        title=f'{difficulty}难度{exam_type}',
        description=f'自动生成的{difficulty}难度{exam_type}，包含{len(questions)}道题（单选{len([q for q in questions if q["type"]=="single_choice"])}道、多选{len([q for q in questions if q["type"]=="multiple_choice"])}道、判断{len([q for q in questions if q["type"]=="true_false"])}道、代码{len([q for q in questions if q["type"]=="code"])}道）',
        exam_type=exam_type,
        difficulty=difficulty,
        duration=duration,
        total_score=total_score,
        pass_score=int(total_score * 0.6),
        is_published=True,
        user_id=user_id
    )
    
    db.session.add(exam)
    db.session.flush()
    
    # 添加题目
    for idx, q in enumerate(questions):
        eq = ExamQuestion(
            exam_id=exam.id,
            question_type=q['type'],
            content=q['content'],
            options=q.get('options'),
            correct_answer=q['correct_answer'],
            score=q['score'],
            analysis=q.get('analysis'),
            sort_order=idx
        )
        db.session.add(eq)
    
    db.session.commit()
    
    return jsonify({
        'message': '试卷生成成功',
        'exam_id': exam.id,
        'exam': format_exam(exam)
    }), 201

def parse_options_from_content(content):
    """从题目内容中解析选项"""
    if not content:
        return ['选项A', '选项B', '选项C', '选项D']
    
    options = []
    lines = content.split('\n')
    for line in lines:
        line = line.strip()
        # 匹配 A. xxx 或 A、xxx 或 A) xxx 或 A xxx 格式
        if line and line[0] in 'ABCDEF' and len(line) > 1:
            if line[1] in ['.', '。', '、', ')', ']', ' ']:
                option_text = line[2:].strip()
                if option_text:
                    options.append(option_text)
    
    # 如果没解析到选项，返回默认选项
    if len(options) < 2:
        return ['选项A', '选项B', '选项C', '选项D']
    
    return options
