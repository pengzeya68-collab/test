# Authentication and authorization module for TestMasterProject
import logging
from flask import request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
print("Auth module imported successfully!")
from ..extensions import db
from ..models.models import User

logger = logging.getLogger(__name__)

# User registration
def register_user():
    logger.info("[API] POST /register - Registration attempt")
    data = request.get_json()
    
    # Validate required fields
    if not data or not data.get('username') or not data.get('email') or not data.get('password') or not data.get('phone'):
        return jsonify({'error': 'Username, email, phone and password are required'}), 400
    
    # Validate phone format
    phone = data.get('phone')
    if not phone or len(phone) != 11 or not phone.isdigit():
        return jsonify({'error': 'Invalid phone number format (must be 11 digits)'}), 400
    
    # Check if user already exists
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username already exists'}), 409
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already exists'}), 409
    
    if User.query.filter_by(phone=phone).first():
        return jsonify({'error': 'Phone number already registered'}), 409
    
    # Create new user
    try:
        hashed_password = generate_password_hash(data['password'])
        new_user = User(
            username=data['username'],
            email=data['email'],
            phone=phone,
            password_hash=hashed_password
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        # Generate tokens
        access_token = create_access_token(identity=new_user.id)
        refresh_token = create_refresh_token(identity=new_user.id)
        
        return jsonify({
            'code': 0,
            'msg': '注册成功',
            'data': {
                'access_token': access_token,
                'refresh_token': refresh_token,
                'user': {
                    'id': new_user.id,
                    'username': new_user.username,
                    'email': new_user.email,
                    'phone': new_user.phone
                }
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Forgot password - 验证码存储（生产环境应使用Redis）
# 格式: {phone: {'code': '123456', 'expires': timestamp}}
_verification_codes = {}

import random
import time

def generate_verification_code():
    """生成6位随机验证码"""
    return ''.join(random.choices('0123456789', k=6))

def cleanup_expired_codes():
    """清理已过期的验证码"""
    now = time.time()
    expired_phones = [phone for phone, record in _verification_codes.items() if now > record['expires']]
    for phone in expired_phones:
        del _verification_codes[phone]

def is_code_valid(phone, code):
    """验证验证码是否有效"""
    # 先清理过期验证码
    cleanup_expired_codes()
    if phone not in _verification_codes:
        return False
    record = _verification_codes[phone]
    if time.time() > record['expires']:
        del _verification_codes[phone]
        return False
    return record['code'] == code

def forgot_password():
    logger.info("[API] POST /forgot-password - Password reset attempt")
    data = request.get_json()
    
    if not data or not data.get('phone') or not data.get('code') or not data.get('new_password'):
        return jsonify({'error': 'Phone number, verification code and new password are required'}), 400
    
    # 验证新密码长度
    if len(data['new_password']) < 6:
        return jsonify({'error': '新密码长度不能少于6位'}), 400
    
    # Verify code
    if not is_code_valid(data['phone'], data['code']):
        return jsonify({'error': 'Invalid or expired verification code'}), 400
    
    # Find user by phone
    user = User.query.filter_by(phone=data['phone']).first()
    if not user:
        return jsonify({'error': 'Phone number not registered'}), 404
    
    try:
        # Update password
        user.password_hash = generate_password_hash(data['new_password'])
        db.session.commit()
        
        # 清除已使用的验证码
        if data['phone'] in _verification_codes:
            del _verification_codes[data['phone']]
        
        return jsonify({
            'code': 0,
            'msg': '密码重置成功'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Send verification code
def send_verification_code():
    """发送验证码"""
    logger.info("[API] POST /send-verification-code - Send verification code")
    data = request.get_json()
    
    if not data or not data.get('phone'):
        return jsonify({'error': 'Phone number is required'}), 400
    
    phone = data['phone']
    
    # 验证手机号格式
    if not phone or len(phone) != 11 or not phone.isdigit():
        return jsonify({'error': 'Invalid phone number format'}), 400
    
    # 检查手机号是否已注册
    user = User.query.filter_by(phone=phone).first()
    if not user:
        return jsonify({'error': 'Phone number not registered'}), 404
    
    # 生成验证码，有效期5分钟
    code = generate_verification_code()
    _verification_codes[phone] = {
        'code': code,
        'expires': time.time() + 300  # 5分钟有效期
    }
    
    # TODO: 生产环境应调用短信服务商API发送验证码 (例如阿里云/腾讯云)
    # 当前为开发环境实现，直接将验证码返回给前端
    # 警告：上线前必须移除以下返回验证码的逻辑！
    return jsonify({
        'code': 0,
        'msg': 'Verification code sent successfully',
        'data': {
            'message': '验证码已发送',
            'code': code  # 仅限开发测试环境
        }
    }), 200

# Change password
@jwt_required()
def change_password():
    current_user_id = get_jwt_identity()
    logger.info(f"[API] POST /change-password - user_id={current_user_id}")
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    if not data or not data.get('old_password') or not data.get('new_password'):
        return jsonify({'error': 'Old password and new password are required'}), 400
    
    # Verify old password
    if not check_password_hash(user.password_hash, data['old_password']):
        return jsonify({'error': 'Old password is incorrect'}), 400
    
    try:
        # Update password
        user.password_hash = generate_password_hash(data['new_password'])
        db.session.commit()
        
        return jsonify({
            'code': 0,
            'msg': '密码修改成功'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# User login
def login_user():
    data = request.get_json()
    username = data.get('username', 'unknown') if data else 'unknown'
    logger.info(f"[API] POST /login - Login attempt for username: {username}")
    
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
        'code': 0,
        'msg': '登录成功',
        'data': {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'phone': user.phone,
                'is_admin': user.is_admin
            }
        }
    }), 200

# Get current user profile
@jwt_required()
def get_current_user():
    current_user_id = get_jwt_identity()
    logger.info(f"[API] GET /profile - user_id={current_user_id}")
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify({
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'phone': user.phone,
            'created_at': user.created_at.isoformat()
        }
    }), 200

# Refresh token
@jwt_required(refresh=True)
def refresh_token():
    current_user_id = get_jwt_identity()
    logger.info(f"[API] POST /refresh - Refresh token for user_id={current_user_id}")
    new_access_token = create_access_token(identity=current_user_id)
    
    return jsonify({
        'access_token': new_access_token
    }), 200

# Update user profile
@jwt_required()
def update_profile():
    current_user_id = get_jwt_identity()
    logger.info(f"[API] PUT /profile - Update profile for user_id={current_user_id}")
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
    logger.info("[API] POST /logout - Logout")
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
auth_bp.route('/forgot-password', methods=['POST'])(forgot_password)
auth_bp.route('/send-verification-code', methods=['POST'])(send_verification_code)
auth_bp.route('/change-password', methods=['POST'])(change_password)