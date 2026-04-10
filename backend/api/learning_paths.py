# Learning paths management API for TestMasterProject
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..extensions import db
from ..models.models import LearningPath, Exercise

# Get all learning paths (public, no auth required)
def get_learning_paths():
    try:
        # Get all public paths, support filter by stage
        stage_str = request.args.get('stage')
        query = LearningPath.query.filter_by(is_public=True)

        stage = None
        if stage_str and stage_str != '':
            try:
                stage = int(stage_str)
            except (ValueError, TypeError):
                stage = None

        if stage is not None:
            query = query.filter_by(stage=stage)
            
        paths = query.all()
        
        result = []
        for path in paths:
            result.append({
                'id': path.id,
                'title': path.title,
                'description': path.description,
                'language': path.language,
                'difficulty': path.difficulty,
                'stage': path.stage,
                'estimated_hours': path.estimated_hours,
                'is_public': path.is_public,
                'created_by': path.user_id,
                'exercise_count': len(path.exercises)
            })
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Get single learning path
def get_learning_path(path_id):
    try:
        path = LearningPath.query.filter_by(id=path_id).first()
        
        if not path:
            return jsonify({'error': 'Learning path not found'}), 404
            
        # Only allow public learning paths for unauthenticated users
        if not path.is_public:
            return jsonify({'error': 'Access denied'}), 403
            
        result = {
            'id': path.id,
            'title': path.title,
            'description': path.description,
            'language': path.language,
            'difficulty': path.difficulty,
            'stage': path.stage,
            'estimated_hours': path.estimated_hours,
            'is_public': path.is_public,
            'created_by': path.user_id,
            'created_at': path.created_at.isoformat(),
            'updated_at': path.updated_at.isoformat(),
            'exercises': [{
                'id': ex.id,
                'title': ex.title,
                'description': ex.description,
                'difficulty': ex.difficulty,
                'category': ex.category,
                'knowledge_point': ex.knowledge_point,
                'time_estimate': ex.time_estimate
            } for ex in path.exercises]
        }
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Create new learning path
@jwt_required()
def create_learning_path():
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or not data.get('title') or not data.get('language'):
            return jsonify({'error': 'Title and language are required'}), 400
            
        new_path = LearningPath(
            title=data['title'],
            description=data.get('description', ''),
            language=data['language'],
            difficulty=data.get('difficulty', 'beginner'),
            estimated_hours=data.get('estimated_hours', 10),
            is_public=data.get('is_public', True),
            user_id=current_user_id
        )
        
        db.session.add(new_path)
        db.session.commit()
        
        return jsonify({
            'message': 'Learning path created successfully',
            'learning_path': {
                'id': new_path.id,
                'title': new_path.title,
                'language': new_path.language,
                'difficulty': new_path.difficulty
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Update learning path
@jwt_required()
def update_learning_path(path_id):
    try:
        current_user_id = get_jwt_identity()
        
        learning_path = LearningPath.query.filter_by(id=path_id).first()
        
        if not learning_path:
            return jsonify({'error': 'Learning path not found'}), 404
        
        if learning_path.user_id != current_user_id:
            return jsonify({'error': 'Access denied'}), 403
        
        data = request.get_json()
        
        if 'title' in data:
            learning_path.title = data['title']
        if 'description' in data:
            learning_path.description = data['description']
        if 'language' in data:
            learning_path.language = data['language']
        if 'difficulty' in data:
            learning_path.difficulty = data['difficulty']
        if 'estimated_hours' in data:
            learning_path.estimated_hours = data['estimated_hours']
        if 'is_public' in data:
            learning_path.is_public = data['is_public']
        
        db.session.commit()
        
        return jsonify({'message': 'Learning path updated successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Delete learning path
@jwt_required()
def delete_learning_path(path_id):
    try:
        current_user_id = get_jwt_identity()
        
        learning_path = LearningPath.query.filter_by(id=path_id).first()
        
        if not learning_path:
            return jsonify({'error': 'Learning path not found'}), 404
        
        if learning_path.user_id != current_user_id:
            return jsonify({'error': 'Access denied'}), 403
        
        db.session.delete(learning_path)
        db.session.commit()
        
        return jsonify({'message': 'Learning path deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Get exercises in a learning path
@jwt_required()
def get_path_exercises(path_id):
    try:
        path = LearningPath.query.filter_by(id=path_id).first()
        
        if not path:
            return jsonify({'error': 'Learning path not found'}), 404
            
        current_user_id = get_jwt_identity()
        if not path.is_public and path.user_id != current_user_id:
            return jsonify({'error': 'Access denied'}), 403
            
        exercises = []
        for ex in path.exercises:
            exercises.append({
                'id': ex.id,
                'title': ex.title,
                'description': ex.description,
                'difficulty': ex.difficulty,
                'language': ex.language,
                'category': ex.category,
                'time_estimate': ex.time_estimate
            })
            
        return jsonify(exercises), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Add exercise to learning path
@jwt_required()
def add_exercise_to_path(path_id):
    try:
        current_user_id = get_jwt_identity()
        
        learning_path = LearningPath.query.filter_by(id=path_id).first()
        
        if not learning_path:
            return jsonify({'error': 'Learning path not found'}), 404
        
        if learning_path.user_id != current_user_id:
            return jsonify({'error': 'Access denied'}), 403
        
        data = request.get_json()
        
        if not data or not data.get('exercise_id'):
            return jsonify({'error': 'Exercise ID is required'}), 400
        
        exercise = Exercise.query.filter_by(id=data['exercise_id']).first()
        
        if not exercise:
            return jsonify({'error': 'Exercise not found'}), 404
        
        if exercise.user_id != current_user_id:
            return jsonify({'error': 'Access denied to exercise'}), 403
        
        exercise.learning_path_id = path_id
        db.session.commit()
        
        return jsonify({'message': 'Exercise added to learning path successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Create learning paths blueprint
from flask import Blueprint

learning_bp = Blueprint('learning_paths', __name__)

# Register routes
learning_bp.route('/learning-paths', methods=['GET'])(get_learning_paths)
learning_bp.route('/learning-paths/<int:path_id>', methods=['GET'])(get_learning_path)
learning_bp.route('/learning-paths', methods=['POST'])(create_learning_path)
learning_bp.route('/learning-paths/<int:path_id>', methods=['PUT'])(update_learning_path)
learning_bp.route('/learning-paths/<int:path_id>', methods=['DELETE'])(delete_learning_path)
learning_bp.route('/learning-paths/<int:path_id>/exercises', methods=['GET'])(get_path_exercises)
learning_bp.route('/learning-paths/<int:path_id>/exercises', methods=['POST'])(add_exercise_to_path)
