# Authentication and authorization module for TestMasterProject
from flask import request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
print("✅ Auth module imported successfully!")
from extensions import db
from models import User

# User registration
def register_user():
    data = request.get_json()
    
    # Validate required fields
    if not data or not data.get('username') or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Username, email and password are required'}), 400
    
    # Check if user already exists
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username already exists'}), 409
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already exists'}), 409
    
    # Create new user
    try:
        hashed_password = generate_password_hash(data['password'])
        new_user = User(
            username=data['username'],
            email=data['email'],
            password_hash=hashed_password
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        # Generate tokens
        access_token = create_access_token(identity=new_user.id)
        refresh_token = create_refresh_token(identity=new_user.id)
        
        return jsonify({
            'message': 'User created successfully',
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': {
                'id': new_user.id,
                'username': new_user.username,
                'email': new_user.email
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# User login
def login_user():
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Username and password are required'}), 400
    
    user = User.query.filter_by(username=data['username']).first()
    
    if not user or not check_password_hash(user.password_hash, data['password']):
        return jsonify({'error': 'Invalid credentials'}), 401
    
    if not user.is_active:
        return jsonify({'error': 'Account is deactivated'}), 403
    
    # Generate tokens
    access_token = create_access_token(identity=user.id)
    refresh_token = create_refresh_token(identity=user.id)
    
    return jsonify({
        'message': 'Login successful',
        'access_token': access_token,
        'refresh_token': refresh_token,
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email
        }
    }), 200

# Get current user profile
@jwt_required()
def get_current_user():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify({
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'created_at': user.created_at.isoformat()
        }
    }), 200

# Refresh token
@jwt_required(refresh=True)
def refresh_token():
    current_user_id = get_jwt_identity()
    new_access_token = create_access_token(identity=current_user_id)
    
    return jsonify({
        'access_token': new_access_token
    }), 200

# Update user profile
@jwt_required()
def update_profile():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    
    if 'email' in data and data['email'] != user.email:
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email already exists'}), 409
        user.email = data['email']
    
    if 'password' in data:
        user.password_hash = generate_password_hash(data['password'])
    
    try:
        db.session.commit()
        return jsonify({'message': 'Profile updated successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Logout (client-side token removal)
def logout_user():
    return jsonify({'message': 'Logout successful'}), 200

# Create auth blueprint
from flask import Blueprint

auth_bp = Blueprint('auth', __name__)

# Register routes
auth_bp.route('/register', methods=['POST'])(register_user)
auth_bp.route('/login', methods=['POST'])(login_user)
auth_bp.route('/profile', methods=['GET'])(get_current_user)
auth_bp.route('/refresh', methods=['POST'])(refresh_token)
auth_bp.route('/profile', methods=['PUT'])(update_profile)
auth_bp.route('/logout', methods=['POST'])(logout_user)