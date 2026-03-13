# Exercises management API for TestMasterProject
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models import Exercise, LearningPath

# Get all exercises
@jwt_required()
def get_exercises():
    try:
        current_user_id = get_jwt_identity()
        # Get public exercises and user's private exercises
        exercises = Exercise.query.filter(
            ((Exercise.user_id == current_user_id) | (Exercise.is_public == True))
        ).all()
        
        result = []
        for ex in exercises:
            result.append({
                'id': ex.id,
                'title': ex.title,
                'description': ex.description,
                'difficulty': ex.difficulty,
                'language': ex.language,
                'category': ex.category,
                'time_estimate': ex.time_estimate,
                'is_public': ex.is_public,
                'created_by': ex.user_id
            })
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Get single exercise
@jwt_required()
def get_exercise(exercise_id):
    try:
        exercise = Exercise.query.filter_by(id=exercise_id).first()
        
        if not exercise:
            return jsonify({'error': 'Exercise not found'}), 404
            
        # Check if exercise is public or belongs to user
        current_user_id = get_jwt_identity()
        if not exercise.is_public and exercise.user_id != current_user_id:
            return jsonify({'error': 'Access denied'}), 403
            
        result = {
            'id': exercise.id,
            'title': exercise.title,
            'description': exercise.description,
            'instructions': exercise.instructions,
            'solution': exercise.solution if exercise.user_id == current_user_id else None,
            'difficulty': exercise.difficulty,
            'language': exercise.language,
            'category': exercise.category,
            'time_estimate': exercise.time_estimate,
            'is_public': exercise.is_public,
            'created_by': exercise.user_id,
            'learning_path_id': exercise.learning_path_id
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
        
        required_fields = ['title', 'description', 'language']
        if not data or any(field not in data for field in required_fields):
            return jsonify({'error': 'Title, description and language are required'}), 400
            
        new_exercise = Exercise(
            title=data['title'],
            description=data['description'],
            instructions=data.get('instructions', ''),
            solution=data.get('solution', ''),
            difficulty=data.get('difficulty', 'easy'),
            language=data['language'],
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
        if 'category' in data:
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
