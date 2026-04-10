# Exercises management API for TestMasterProject
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..extensions import db
from ..models.models import Exercise, LearningPath

# Get all exercises
def get_exercises():
    try:
        # Get all public exercises
        query = Exercise.query.filter(Exercise.is_public == True)
        
        # Support filter by module, stage and category
        module = request.args.get('module')
        stage_str = request.args.get('stage')
        category = request.args.get('category')
        knowledge_point = request.args.get('knowledge_point')

        stage = None
        if stage_str and stage_str != '':
            try:
                stage = int(stage_str)
            except (ValueError, TypeError):
                stage = None

        if module:
            query = query.filter_by(module=module)
        if stage is not None:
            query = query.filter_by(stage=stage)
        if category:
            query = query.filter_by(category=category)
        if knowledge_point:
            # 使用参数化查询防止SQL注入
            query = query.filter(Exercise.knowledge_point.like('%' + knowledge_point + '%'))
            
        exercises = query.all()
        
        result = []
        for ex in exercises:
            result.append({
                'id': ex.id,
                'title': ex.title,
                'description': ex.description,
                'difficulty': ex.difficulty,
                'language': ex.language,
                'module': ex.module,
                'category': ex.category,
                'stage': ex.stage,
                'knowledge_point': ex.knowledge_point,
                'time_estimate': ex.time_estimate,
                'is_public': ex.is_public,
                'created_by': ex.user_id,
                'created_at': ex.created_at.isoformat()
            })
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Get single exercise
def get_exercise(exercise_id):
    try:
        exercise = Exercise.query.filter_by(id=exercise_id).first()
        
        if not exercise:
            return jsonify({'error': 'Exercise not found'}), 404
            
        # Only allow public exercises for unauthenticated users
        if not exercise.is_public:
            return jsonify({'error': 'Access denied'}), 403
            
        result = {
            'id': exercise.id,
            'title': exercise.title,
            'description': exercise.description,
            'instructions': exercise.instructions,
            'solution': exercise.solution,
            'difficulty': exercise.difficulty,
            'language': exercise.language,
            'module': exercise.module,
            'category': exercise.category,
            'stage': exercise.stage,
            'knowledge_point': exercise.knowledge_point,
            'time_estimate': exercise.time_estimate,
            'is_public': exercise.is_public,
            'created_by': exercise.user_id,
            'learning_path_id': exercise.learning_path_id,
            'test_cases': exercise.test_cases,
            'created_at': exercise.created_at.isoformat(),
            'updated_at': exercise.updated_at.isoformat()
        }
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Create new exercise
@jwt_required()
def create_exercise():
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        required_fields = ['title', 'description', 'language', 'category']
        if not data or any(field not in data or not data[field] for field in required_fields):
            return jsonify({'error': '标题、描述、语言、分类为必填字段，不能为空'}), 400
            
        new_exercise = Exercise(
            title=data['title'],
            description=data['description'],
            instructions=data.get('instructions', ''),
            solution=data.get('solution', ''),
            difficulty=data.get('difficulty', 'easy'),
            language=data['language'],
            module=data.get('module', 'normal'),
            category=data.get('category'),
            time_estimate=data.get('time_estimate'),
            is_public=data.get('is_public', True),
            user_id=current_user_id,
            learning_path_id=data.get('learning_path_id')
        )
        
        db.session.add(new_exercise)
        db.session.commit()
        
        return jsonify({
            'message': 'Exercise created successfully',
            'exercise': {
                'id': new_exercise.id,
                'title': new_exercise.title,
                'language': new_exercise.language,
                'difficulty': new_exercise.difficulty
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Update exercise
@jwt_required()
def update_exercise(exercise_id):
    try:
        current_user_id = get_jwt_identity()
        
        exercise = Exercise.query.filter_by(id=exercise_id).first()
        
        if not exercise:
            return jsonify({'error': 'Exercise not found'}), 404
        
        if exercise.user_id != current_user_id:
            return jsonify({'error': 'Access denied'}), 403
        
        data = request.get_json()
        
        if 'title' in data:
            exercise.title = data['title']
        if 'description' in data:
            exercise.description = data['description']
        if 'instructions' in data:
            exercise.instructions = data['instructions']
        if 'solution' in data:
            exercise.solution = data['solution']
        if 'difficulty' in data:
            exercise.difficulty = data['difficulty']
        if 'language' in data:
            exercise.language = data['language']
        if 'module' in data:
            exercise.module = data['module']
        if 'category' in data:
            if not data['category']:
                return jsonify({'error': '分类不能为空'}), 400
            exercise.category = data['category']
        if 'time_estimate' in data:
            exercise.time_estimate = data['time_estimate']
        if 'is_public' in data:
            exercise.is_public = data['is_public']
        if 'learning_path_id' in data:
            exercise.learning_path_id = data['learning_path_id']
        
        db.session.commit()
        
        return jsonify({'message': 'Exercise updated successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Delete exercise
@jwt_required()
def delete_exercise(exercise_id):
    try:
        current_user_id = get_jwt_identity()
        
        exercise = Exercise.query.filter_by(id=exercise_id).first()
        
        if not exercise:
            return jsonify({'error': 'Exercise not found'}), 404
        
        if exercise.user_id != current_user_id:
            return jsonify({'error': 'Access denied'}), 403
        
        db.session.delete(exercise)
        db.session.commit()
        
        return jsonify({'message': 'Exercise deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Submit exercise solution
@jwt_required()
def submit_solution():
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or 'exercise_id' not in data or 'solution' not in data:
            return jsonify({'error': 'Exercise ID and solution are required'}), 400
            
        exercise = Exercise.query.filter_by(id=data['exercise_id']).first()
        
        if not exercise:
            return jsonify({'error': 'Exercise not found'}), 404
            
        # Simple solution check - compare with expected solution
        is_correct = data['solution'].strip() == exercise.solution.strip()
        
        return jsonify({
            'correct': is_correct,
            'message': 'Solution submitted successfully',
            'expected_solution': exercise.solution if is_correct else None
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Get user's exercises
@jwt_required()
def get_user_exercises():
    try:
        current_user_id = get_jwt_identity()
        exercises = Exercise.query.filter_by(user_id=current_user_id).all()
        
        result = []
        for ex in exercises:
            result.append({
                'id': ex.id,
                'title': ex.title,
                'difficulty': ex.difficulty,
                'language': ex.language,
                'module': ex.module,
                'category': ex.category,
                'is_public': ex.is_public
            })
            
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Get public exercises
@jwt_required()
def get_public_exercises():
    try:
        exercises = Exercise.query.filter_by(is_public=True).all()
        
        result = []
        for ex in exercises:
            result.append({
                'id': ex.id,
                'title': ex.title,
                'difficulty': ex.difficulty,
                'language': ex.language,
                'module': ex.module,
                'category': ex.category,
                'created_by': ex.user_id
            })
            
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Get exercise categories
@jwt_required()
def get_categories():
    try:
        current_user_id = get_jwt_identity()
        language = request.args.get('language')
        
        query = Exercise.query.filter(
            ((Exercise.user_id == current_user_id) | (Exercise.is_public == True))
        )
        
        if language:
            query = query.filter(Exercise.language == language)
        
        exercises = query.all()
        
        # Group by category
        categories = {}
        for ex in exercises:
            category = ex.category or 'Uncategorized'
            if category not in categories:
                categories[category] = []
            categories[category].append({
                'id': ex.id,
                'title': ex.title,
                'difficulty': ex.difficulty,
                'time_estimate': ex.time_estimate
            })
        
        return jsonify(categories), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Create exercises blueprint
from flask import Blueprint

exercises_bp = Blueprint('exercises', __name__)

# Register routes
exercises_bp.route('/exercises', methods=['GET'])(get_exercises)
exercises_bp.route('/exercises/<int:exercise_id>', methods=['GET'])(get_exercise)
exercises_bp.route('/exercises', methods=['POST'])(create_exercise)
exercises_bp.route('/exercises/<int:exercise_id>', methods=['PUT'])(update_exercise)
exercises_bp.route('/exercises/<int:exercise_id>', methods=['DELETE'])(delete_exercise)
exercises_bp.route('/exercises/submit', methods=['POST'])(submit_solution)
exercises_bp.route('/exercises/user', methods=['GET'])(get_user_exercises)
exercises_bp.route('/exercises/public', methods=['GET'])(get_public_exercises)
exercises_bp.route('/exercises/categories', methods=['GET'])(get_categories)

# Execute SQL for SQL exercise verification
@jwt_required()
def execute_sql():
    """Execute user's SQL statement on a temporary in-memory database
    First runs the setup SQL (creates tables and inserts data), then executes user's SQL
    Returns the query result
    """
    try:
        data = request.get_json()
        if not data or 'setup_sql' not in data or 'user_sql' not in data:
            return jsonify({'error': '缺少必要参数：setup_sql 和 user_sql 都是必填项'}), 400
        
        setup_sql = data['setup_sql']
        user_sql = data['user_sql'].strip()
        
        if not user_sql:
            return jsonify({'error': '请输入SQL语句'}), 400
        
        # 禁止危险操作
        dangerous_keywords = ['drop', 'delete', 'truncate', 'alter', 'create', 'insert', 'update', 'pragma']
        lower_sql = user_sql.lower()
        for keyword in dangerous_keywords:
            if keyword in lower_sql:
                # 禁止用户执行这些危险操作
                return jsonify({'success': False, 'error': f'禁止执行包含 {keyword} 关键字的SQL语句'}), 400
        
        import sqlite3
        import time
        
        start_time = time.time()
        
        # 创建内存数据库
        conn = sqlite3.connect(':memory:')
        cursor = conn.cursor()
        
        try:
            # 执行建表和插入初始化数据
            if setup_sql.strip():
                cursor.executescript(setup_sql)
                conn.commit()
            
            # 执行用户SQL
            cursor.execute(user_sql)
            
            # 如果是查询，获取结果
            if user_sql.lower().startswith(('select', 'show', 'describe', 'explain')):
                # 获取列名
                columns = [description[0] for description in cursor.description] if cursor.description else []
                rows = cursor.fetchall()
                
                conn.commit()
                conn.close()
                
                elapsed_ms = int((time.time() - start_time) * 1000)
                
                return jsonify({
                    'success': True,
                    'columns': columns,
                    'rows': [list(row) for row in rows],
                    'row_count': len(rows),
                    'elapsed_ms': elapsed_ms
                }), 200
            else:
                # 非查询语句
                conn.commit()
                row_count = cursor.rowcount
                conn.close()
                elapsed_ms = int((time.time() - start_time) * 1000)
                
                return jsonify({
                    'success': True,
                    'message': f'执行成功，影响 {row_count} 行',
                    'row_count': row_count,
                    'elapsed_ms': elapsed_ms
                }), 200
                
        except sqlite3.Error as e:
            conn.close()
            elapsed_ms = int((time.time() - start_time) * 1000)
            return jsonify({
                'success': False,
                'error': str(e),
                'elapsed_ms': elapsed_ms
            }), 400
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Register the new route
exercises_bp.route('/exercises/execute-sql', methods=['POST'])(execute_sql)
