# Admin API for TestMasterProject
import logging
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import text
from ..models.models import User
from ..extensions import db
import os
import sys
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)
admin_bp = Blueprint('admin', __name__)

# 🔥 强制写死绝对路径！全局统一备份目录
BACKUP_DIR = Path(r"C:\Users\lenovo\Desktop\TestMasterProject\backups")
# 添加 scripts 路径到 sys.path
scripts_dir = r"C:\Users\lenovo\Desktop\TestMasterProject\scripts"
sys.path.insert(0, scripts_dir)


def check_admin_permission(user_id):
    """检查用户是否有管理员权限"""
    user = User.query.get(user_id)
    return user and user.is_admin


@admin_bp.route('/admin/backups', methods=['GET'])
@jwt_required()
def list_backups():
    """获取备份列表"""
    user_id = get_jwt_identity()
    logger.info(f"[ADMIN API] GET /admin/backups - user_id={user_id}")

    if not check_admin_permission(user_id):
        logger.warning(f"[ADMIN API] User {user_id} not admin, access denied")
        return jsonify({'error': '无权限访问'}), 403
    
    try:
        backups = []
        import os
        backup_dir_path = str(BACKUP_DIR)
        abs_path = os.path.abspath(backup_dir_path)
        print(f"📜 列表正在扫描：{abs_path}")
        logger.info(f"[LIST] 正在扫描备份目录: {abs_path}")
        if os.path.exists(backup_dir_path):
            # 第一步：强制物理删除所有非 .db 格式备份文件
            for filename in os.listdir(backup_dir_path):
                if not filename.endswith('.db'):
                    old_file = os.path.join(backup_dir_path, filename)
                    try:
                        os.remove(old_file)
                        logger.info(f"[CLEANUP] 删除非标准格式备份: {filename}")
                    except Exception as e:
                        logger.warning(f"[CLEANUP] 删除失败 {filename}: {e}")
            # 第二步：只列出标准格式备份
            # 标准用户备份: testmaster_backup_YYYYMMDD_HHMMSS.db
            # 恢复前紧急备份: testmaster_emergency_YYYYMMDD_HHMMSS.db
            for filename in os.listdir(backup_dir_path):
                if (filename.startswith('testmaster_backup_') or filename.startswith('testmaster_emergency_')) and filename.endswith('.db'):
                    file_path = os.path.join(backup_dir_path, filename)
                    if os.path.isfile(file_path):
                        stat = os.stat(file_path)
                        backups.append({
                            'name': filename,
                            'size': stat.st_size / (1024 * 1024),  # MB
                            'time': datetime.fromtimestamp(stat.st_mtime).isoformat()
                        })

        # 按时间排序（最新的在前）
        backups.sort(key=lambda x: x['time'], reverse=True)

        return jsonify({
            'backups': backups,
            'total': len(backups)
        }), 200

    except Exception as e:
        return jsonify({'error': f'获取备份列表失败: {str(e)}'}), 500


@admin_bp.route('/admin/backups', methods=['POST'])
@jwt_required()
def create_backup():
    """创建全量数据库备份"""
    user_id = get_jwt_identity()
    logger.info(f"[ADMIN API] POST /admin/backups - user_id={user_id}")

    if not check_admin_permission(user_id):
        return jsonify({'error': '无权限访问'}), 403

    try:
        from ..models.models import AuditLog
        from ..extensions import db
        import sqlite3
        import os
        from pathlib import Path
        from flask import current_app

        client_ip = request.remote_addr

        # 1. 强制使用标准命名规则
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"testmaster_backup_{timestamp}.db"
        backup_path = os.path.join(BACKUP_DIR, backup_filename)

        # 确保备份目录存在
        os.makedirs(BACKUP_DIR, exist_ok=True)

        # 2. 获取真实数据库路径
        db_uri = current_app.config.get('SQLALCHEMY_DATABASE_URI')
        # 兼容处理 sqlite:/// 和 sqlite:////
        db_path = db_uri.replace('sqlite:///', '') if db_uri else 'testmaster.db'
        if db_path.startswith('/'): # 处理绝对路径多余的斜杠
            db_path = db_path[1:]

        # 3. 🔥 核心修复：弃用 shutil.copy2，改用安全的 sqlite3 热备份 API
        source = sqlite3.connect(db_path)
        backup = sqlite3.connect(backup_path)
        with backup:
            source.backup(backup)
        source.close()
        backup.close()

        # 4. 尝试清理旧备份 (这里不再引用外部的 clean_old_backups，直接在本地安全清理)
        try:
            all_backups = [f for f in os.listdir(BACKUP_DIR) if f.startswith('testmaster_backup_') and f.endswith('.db')]
            all_backups.sort(reverse=True) # 按文件名的时间戳倒序
            if len(all_backups) > 10: # 假设最多保留 10 个
                for old_file in all_backups[10:]:
                    os.remove(os.path.join(BACKUP_DIR, old_file))
        except Exception as e:
            logger.warning(f"清理旧备份失败: {e}") # 清理失败不影响本次备份成功

        # 5. 记录成功审计日志并返回
        backup_path_obj = Path(backup_path)
        audit = AuditLog(
            user_id=user_id,
            action='创建全量数据库备份',
            action_type='backup',
            ip_address=client_ip,
            status='success'
        )
        db.session.add(audit)
        db.session.commit()

        return jsonify({
            'message': '备份创建成功',
            'backup': {
                'name': backup_filename,
                'size': backup_path_obj.stat().st_size / (1024 * 1024),
                'time': datetime.fromtimestamp(backup_path_obj.stat().st_mtime).isoformat()
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        logger.error(f"[ADMIN API] 备份失败: {str(e)}")
        # 记录失败审计日志
        try:
            audit = AuditLog(user_id=user_id, action='创建全量数据库备份', action_type='backup', ip_address=client_ip, status='failed')
            db.session.add(audit)
            db.session.commit()
        except:
            pass
        return jsonify({'error': f'备份失败: {str(e)}'}), 500


@admin_bp.route('/admin/backups/old', methods=['DELETE'])
@jwt_required()
def delete_old_backups():
    """删除旧备份"""
    user_id = get_jwt_identity()
    logger.info(f"[ADMIN API] DELETE /admin/backups/old - user_id={user_id}")

    if not check_admin_permission(user_id):
        logger.warning(f"[ADMIN API] User {user_id} not admin, access denied")
        return jsonify({'error': '无权限访问'}), 403

    try:
        from backup_database import clean_old_backups
        from ..models.models import AuditLog
        from ..extensions import db
        # 获取客户端IP
        client_ip = request.remote_addr

        clean_old_backups()

        # 记录审计日志
        audit = AuditLog(
            user_id=user_id,
            action='清理旧备份（保留最新10个）',
            action_type='cleanup',
            ip_address=client_ip,
            status='success'
        )
        db.session.add(audit)
        db.session.commit()

        return jsonify({'message': '旧备份清理成功'}), 200

    except Exception as e:
        return jsonify({'error': f'清理失败: {str(e)}'}), 500


@admin_bp.route('/admin/backups/<path:backup_name>/restore', methods=['POST'])
@jwt_required()
def restore_backup(backup_name):
    """恢复备份"""
    user_id = get_jwt_identity()
    logger.info(f"[ADMIN API] POST /admin/backups/{backup_name}/restore - user_id={user_id}")

    if not check_admin_permission(user_id):
        logger.warning(f"[ADMIN API] User {user_id} not admin, access denied")
        return jsonify({'error': '无权限访问'}), 403

    try:
        from ..models.models import AuditLog
        from ..extensions import db
        import shutil
        # 获取客户端IP
        client_ip = request.remote_addr

        # 1. 获取当前运行的数据库路径
        db_uri = current_app.config.get('SQLALCHEMY_DATABASE_URI')
        db_path = db_uri.replace('sqlite:///', '') if db_uri else 'testmaster.db'
        if db_path.startswith('/'):
            db_path = db_path[1:]

        backup_file = BACKUP_DIR / backup_name

        # 安全检查：确保文件在备份目录中
        if not str(backup_file.resolve()).startswith(str(BACKUP_DIR.resolve())):
            audit = AuditLog(
                user_id=user_id,
                action=f'恢复备份失败: {backup_name} (无效路径)',
                action_type='restore',
                ip_address=client_ip,
                status='failed'
            )
            db.session.add(audit)
            db.session.commit()
            return jsonify({'error': '无效的文件路径'}), 400

        if not backup_file.exists():
            audit = AuditLog(
                user_id=user_id,
                action=f'恢复备份失败: {backup_name} (文件不存在)',
                action_type='restore',
                ip_address=client_ip,
                status='failed'
            )
            db.session.add(audit)
            db.session.commit()
            return jsonify({'error': '备份文件不存在'}), 404

        # 2. 🔥 紧急快照：恢复前强制创建 sqlite3 热备份
        emergency_filename = f"testmaster_emergency_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        emergency_path = BACKUP_DIR / emergency_filename

        source_conn = sqlite3.connect(db_path)
        emergency_conn = sqlite3.connect(emergency_path)
        with emergency_conn:
            source_conn.backup(emergency_conn)
        source_conn.close()
        emergency_conn.close()
        logger.info(f"[ADMIN API] 紧急快照已创建: {emergency_filename}")

        # 3. 将用户选择的历史备份覆盖到当前 db_path
        shutil.copy2(str(backup_file), str(db_path))
        logger.info(f"[ADMIN API] 数据库已从 {backup_name} 恢复")

        # 记录审计日志
        audit = AuditLog(
            user_id=user_id,
            action=f'恢复数据库备份: {backup_name}',
            action_type='restore',
            ip_address=client_ip,
            status='success'
        )
        db.session.add(audit)
        db.session.commit()
        return jsonify({'message': '备份恢复成功'}), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"[ADMIN API] 恢复备份失败: {str(e)}")
        # 记录失败审计日志
        try:
            from ..models.models import AuditLog
            from ..extensions import db
            audit = AuditLog(
                user_id=user_id,
                action=f'恢复数据库备份: {backup_name}',
                action_type='restore',
                ip_address=request.remote_addr,
                status='failed'
            )
            db.session.add(audit)
            db.session.commit()
        except:
            pass
        return jsonify({'error': f'恢复失败: {str(e)}'}), 500


@admin_bp.route('/admin/backups/<path:backup_name>', methods=['DELETE'])
@jwt_required()
def delete_backup(backup_name):
    """删除指定备份"""
    user_id = get_jwt_identity()
    logger.info(f"[ADMIN API] DELETE /admin/backups/{backup_name} - user_id={user_id}")

    if not check_admin_permission(user_id):
        logger.warning(f"[ADMIN API] User {user_id} not admin, access denied")
        return jsonify({'error': '无权限访问'}), 403

    try:
        from ..models.models import AuditLog
        from ..extensions import db
        # 获取客户端IP
        client_ip = request.remote_addr

        backup_file = BACKUP_DIR / backup_name

        # 安全检查：确保文件在备份目录中
        if not str(backup_file.resolve()).startswith(str(BACKUP_DIR.resolve())):
            audit = AuditLog(
                user_id=user_id,
                action=f'删除备份失败: {backup_name} (无效路径)',
                action_type='delete',
                ip_address=client_ip,
                status='failed'
            )
            db.session.add(audit)
            db.session.commit()
            return jsonify({'error': '无效的文件路径'}), 400

        if not backup_file.exists():
            # 文件如果已经被清理程序删了，直接返回成功，不要报错 500！
            return jsonify({'message': '文件已不存在或已被清理'}), 200

        backup_file.unlink()
        # 记录成功审计日志
        audit = AuditLog(
            user_id=user_id,
            action=f'删除备份: {backup_name}',
            action_type='delete',
            ip_address=client_ip,
            status='success'
        )
        db.session.add(audit)
        db.session.commit()
        return jsonify({'message': '备份删除成功'}), 200

    except Exception as e:
        return jsonify({'error': f'删除失败: {str(e)}'}), 500


@admin_bp.route('/admin/backups/download/<path:filename>', methods=['GET'])
@jwt_required()
def download_backup(filename):
    """下载备份文件"""
    user_id = get_jwt_identity()
    logger.info(f"[ADMIN API] GET /admin/backups/download/{filename} - user_id={user_id}")

    if not check_admin_permission(user_id):
        logger.warning(f"[ADMIN API] User {user_id} not admin, access denied")
        return jsonify({'error': '无权限访问'}), 403

    try:
        from flask import send_from_directory

        # 安全检查：确保文件在备份目录中
        backup_file = BACKUP_DIR / filename
        if not str(backup_file.resolve()).startswith(str(BACKUP_DIR.resolve())):
            return jsonify({'error': '无效的文件路径'}), 400

        if not backup_file.exists():
            return jsonify({'error': '文件不存在'}), 404

        return send_from_directory(BACKUP_DIR, filename, as_attachment=True)

    except Exception as e:
        logger.error(f"[ADMIN API] 下载备份失败: {str(e)}")
        return jsonify({'error': f'下载失败: {str(e)}'}), 500


@admin_bp.route('/admin/dashboard/stats', methods=['GET'])
@jwt_required()
def get_dashboard_stats():
    """获取仪表盘统计数据"""
    user_id = get_jwt_identity()
    logger.info(f"[ADMIN API] GET /admin/dashboard/stats - user_id={user_id}")

    if not check_admin_permission(user_id):
        logger.warning(f"[ADMIN API] User {user_id} not admin, access denied")
        return jsonify({'error': '无权限访问'}), 403

    try:
        # 统计各种数据
        from ..models.models import User, Exercise, LearningPath, Post

        total_users = User.query.count()
        total_exercises = Exercise.query.count()
        total_learning_paths = LearningPath.query.count()
        total_posts = Post.query.count()

        # 获取最近注册的3个用户
        recent_users = User.query\
            .order_by(User.created_at.desc())\
            .limit(3)\
            .all()

        recent_users_data = []
        for u in recent_users:
            registerTime = ''
            if u.created_at:
                registerTime = u.created_at.strftime('%Y-%m-%d %H:%M')
            recent_users_data.append({
                'id': u.id,
                'username': u.username,
                'email': u.email,
                'registerTime': registerTime
            })

        # 获取最近添加的3个习题
        recent_exercises = Exercise.query\
            .order_by(Exercise.created_at.desc())\
            .limit(3)\
            .all()

        recent_exercises_data = []
        for e in recent_exercises:
            createTime = ''
            if e.created_at:
                createTime = e.created_at.strftime('%Y-%m-%d %H:%M')
            recent_exercises_data.append({
                'id': e.id,
                'title': e.title,
                'difficulty': e.difficulty,
                'createTime': createTime
            })

        # 统计数据 - 真实数据
        stats = [
            { 'title': '总用户数', 'value': total_users },
            { 'title': '习题总数', 'value': total_exercises },
            { 'title': '学习路径', 'value': total_learning_paths },
            { 'title': '社区帖子', 'value': total_posts }
        ]

        return jsonify({
            'stats': stats,
            'recentUsers': recent_users_data,
            'recentExercises': recent_exercises_data
        }), 200

    except Exception as e:
        return jsonify({'error': f'获取统计数据失败: {str(e)}'}), 500


@admin_bp.route('/admin/users', methods=['GET'])
@jwt_required()
def get_users():
    """获取用户列表"""
    user_id = get_jwt_identity()
    logger.info(f"[ADMIN API] GET /admin/users - user_id={user_id}")

    if not check_admin_permission(user_id):
        logger.warning(f"[ADMIN API] User {user_id} not admin, access denied")
        return jsonify({'error': '无权限访问'}), 403

    try:
        keyword = request.args.get('keyword', '')
        status = request.args.get('status', '')

        query = User.query

        if keyword:
            query = query.filter(
                User.username.contains(keyword) | User.email.contains(keyword)
            )

        if status == 'active':
            query = query.filter(User.is_active == True)
        elif status == 'disabled':
            query = query.filter(User.is_active == False)

        users = query.order_by(User.created_at.desc()).all()

        result = []
        for u in users:
            registerTime = ''
            if u.created_at:
                registerTime = u.created_at.strftime('%Y-%m-%d %H:%M')
            result.append({
                'id': u.id,
                'username': u.username,
                'email': u.email,
                'phone': u.phone,
                'level': u.level,
                'score': u.score,
                'study_time': u.study_time // 60 if u.study_time else 0,
                'status': 'active' if u.is_active else 'disabled',
                'is_admin': u.is_admin,
                'registerTime': registerTime
            })

        return jsonify({
            'list': result,
            'total': len(result)
        }), 200

    except Exception as e:
        return jsonify({'error': f'获取用户列表失败: {str(e)}'}), 500


@admin_bp.route('/admin/users', methods=['POST'])
@jwt_required()
def create_user():
    """创建新用户"""
    admin_id = get_jwt_identity()
    logger.info(f"[ADMIN API] POST /admin/users - admin_id={admin_id}")

    if not check_admin_permission(admin_id):
        logger.warning(f"[ADMIN API] User {admin_id} not admin, access denied")
        return jsonify({'error': '无权限访问'}), 403

    try:
        data = request.get_json()

        # 校验必填字段
        if not data or not data.get('username') or not data.get('email') or not data.get('password'):
            return jsonify({'error': '用户名、邮箱、密码为必填项'}), 400

        # 检查用户是否已存在
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'error': '用户名已存在'}), 409
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': '邮箱已被注册'}), 409

        from werkzeug.security import generate_password_hash

        # 创建新用户
        phone = data.get('phone')
        if phone is None or phone == '' or phone.strip() == '':
            phone = None
        else:
            phone = phone.strip()
        new_user = User(
            username=data['username'],
            email=data['email'],
            password_hash=generate_password_hash(data['password']),
            phone=phone,
            level=data.get('level', 1),
            score=data.get('score', 0),
            is_active=data.get('status', 'active') == 'active',
            is_admin=data.get('is_admin', False)
        )

        db.session.add(new_user)
        db.session.commit()

        return jsonify({
            'message': '用户创建成功',
            'user': {
                'id': new_user.id,
                'username': new_user.username,
                'email': new_user.email,
                'is_admin': new_user.is_admin
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'创建用户失败: {str(e)}'}), 500


@admin_bp.route('/admin/users/<int:user_id>/toggle-status', methods=['POST'])
@jwt_required()
def toggle_user_status(user_id):
    """切换用户激活/禁用状态"""
    admin_id = get_jwt_identity()
    logger.info(f"[ADMIN API] POST /admin/users/{user_id}/toggle-status - admin_id={admin_id}")

    if not check_admin_permission(admin_id):
        logger.warning(f"[ADMIN API] User {admin_id} not admin, access denied")
        return jsonify({'error': '无权限访问'}), 403

    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': '用户不存在'}), 404

        # 不能禁用自己
        if user.id == admin_id:
            return jsonify({'error': '不能禁用当前登录的管理员账号'}), 400

        user.is_active = not user.is_active
        db.session.commit()

        return jsonify({
            'message': f'用户已{"禁用" if not user.is_active else "启用"}',
            'status': 'active' if user.is_active else 'disabled'
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'操作失败: {str(e)}'}), 500


@admin_bp.route('/admin/users/<int:user_id>/toggle-admin', methods=['POST'])
@jwt_required()
def toggle_user_admin(user_id):
    """切换用户管理员权限"""
    admin_id = get_jwt_identity()
    logger.info(f"[ADMIN API] POST /admin/users/{user_id}/toggle-admin - admin_id={admin_id}")

    if not check_admin_permission(admin_id):
        logger.warning(f"[ADMIN API] User {admin_id} not admin, access denied")
        return jsonify({'error': '无权限访问'}), 403

    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': '用户不存在'}), 404

        user.is_admin = not user.is_admin
        db.session.commit()

        return jsonify({
            'message': f'已{"取消管理员" if not user.is_admin else "设置为管理员"}',
            'is_admin': user.is_admin
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'操作失败: {str(e)}'}), 500


@admin_bp.route('/admin/users/<int:user_id>', methods=['PUT'])
@jwt_required()
def update_user(user_id):
    """更新用户信息"""
    admin_id = get_jwt_identity()
    logger.info(f"[ADMIN API] PUT /admin/users/{user_id} - admin_id={admin_id}")

    if not check_admin_permission(admin_id):
        logger.warning(f"[ADMIN API] User {admin_id} not admin, access denied")
        return jsonify({'error': '无权限访问'}), 403

    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': '用户不存在'}), 404

        data = request.get_json()

        # 更新用户名
        if 'username' in data and data['username']:
            # 检查是否重复
            existing = User.query.filter_by(username=data['username']).first()
            if existing and existing.id != user_id:
                return jsonify({'error': '用户名已存在'}), 409
            user.username = data['username']

        # 更新邮箱
        if 'email' in data and data['email']:
            existing = User.query.filter_by(email=data['email']).first()
            if existing and existing.id != user_id:
                return jsonify({'error': '邮箱已被注册'}), 409
            user.email = data['email']

        # 更新密码（如果提供了新密码）
        if 'password' in data and data['password']:
            from werkzeug.security import generate_password_hash
            user.password_hash = generate_password_hash(data['password'])

        # 更新其他字段
        if 'level' in data:
            user.level = data['level']
        if 'score' in data:
            user.score = data['score']
        if 'status' in data:
            user.is_active = (data['status'] == 'active')
        if 'is_admin' in data:
            # 不能取消自己的管理员权限
            if user.id == admin_id and data['is_admin'] is False:
                return jsonify({'error': '不能取消自己的管理员权限'}), 400
            user.is_admin = data['is_admin']

        if 'phone' in data:
            phone = data['phone']
            if phone is None or phone == '' or phone.strip() == '':
                phone = None
            else:
                phone = phone.strip()
            user.phone = phone

        db.session.commit()

        return jsonify({
            'message': '用户更新成功',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'is_admin': user.is_admin
            }
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'更新用户失败: {str(e)}'}), 500


@admin_bp.route('/admin/users/<int:user_id>', methods=['DELETE'])
@jwt_required()
def delete_user(user_id):
    """删除用户"""
    admin_id = get_jwt_identity()
    logger.info(f"[ADMIN API] DELETE /admin/users/{user_id} - admin_id={admin_id}")

    if not check_admin_permission(admin_id):
        logger.warning(f"[ADMIN API] User {admin_id} not admin, access denied")
        return jsonify({'error': '无权限访问'}), 403

    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': '用户不存在'}), 404

        if user.id == admin_id:
            return jsonify({'error': '不能删除当前登录的管理员账号'}), 400

        db.session.delete(user)
        db.session.commit()

        return jsonify({'message': '删除成功'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'删除失败: {str(e)}'}), 500


@admin_bp.route('/admin/users/<int:user_id>/reset-password', methods=['PUT'])
@jwt_required()
def admin_reset_user_password(user_id):
    """管理员重置用户密码"""
    admin_id = get_jwt_identity()
    logger.info(f"[ADMIN API] PUT /admin/users/{user_id}/reset-password - admin_id={admin_id}")

    if not check_admin_permission(admin_id):
        logger.warning(f"[ADMIN API] User {admin_id} not admin, access denied")
        return jsonify({'error': '无权限访问'}), 403

    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': '用户不存在'}), 404

        data = request.get_json()
        new_password = data.get('new_password', '')

        if not new_password or len(new_password) < 6:
            return jsonify({'error': '密码长度不能少于6位'}), 400

        from werkzeug.security import generate_password_hash
        user.password_hash = generate_password_hash(new_password)

        db.session.commit()

        return jsonify({'message': '密码重置成功'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'重置失败: {str(e)}'}), 500


@admin_bp.route('/admin/exercises', methods=['GET'])
@jwt_required()
def get_exercises():
    """获取习题列表"""
    user_id = get_jwt_identity()
    logger.info(f"[ADMIN API] GET /admin/exercises - user_id={user_id}")

    if not check_admin_permission(user_id):
        logger.warning(f"[ADMIN API] User {user_id} not admin, access denied")
        return jsonify({'error': '无权限访问'}), 403

    try:
        from ..models.models import Exercise
        keyword = request.args.get('keyword', '')
        difficulty = request.args.get('difficulty', '')

        query = Exercise.query

        if keyword:
            query = query.filter(Exercise.title.contains(keyword))

        if difficulty:
            query = query.filter(Exercise.difficulty == difficulty)

        exercises = query.order_by(Exercise.created_at.desc()).all()

        result = []
        for e in exercises:
            createdAt = ''
            if e.created_at:
                createdAt = e.created_at.strftime('%Y-%m-%d %H:%M')
            result.append({
                'id': e.id,
                'title': e.title,
                'difficulty': e.difficulty,
                'language': e.language,
                'category': e.category,
                'is_public': e.is_public,
                'createdAt': createdAt
            })

        return jsonify({
            'list': result,
            'total': len(result)
        }), 200

    except Exception as e:
        return jsonify({'error': f'获取习题列表失败: {str(e)}'}), 500


@admin_bp.route('/admin/exercises', methods=['POST'])
@jwt_required()
def create_exercise():
    """创建新习题"""
    admin_id = get_jwt_identity()
    logger.info(f"[ADMIN API] POST /admin/exercises - admin_id={admin_id}")

    if not check_admin_permission(admin_id):
        logger.warning(f"[ADMIN API] User {admin_id} not admin, access denied")
        return jsonify({'error': '无权限访问'}), 403

    try:
        from ..models.models import Exercise
        from ..extensions import db

        data = request.get_json()

        if not data or not data.get('title') or not data.get('language') or not data.get('category'):
            return jsonify({'error': '标题、语言、分类为必填字段'}), 400

        new_exercise = Exercise(
            title=data['title'],
            description=data.get('description', ''),
            instructions=data.get('instructions', ''),
            solution=data.get('solution', ''),
            difficulty=data.get('difficulty', 'easy'),
            language=data['language'],
            category=data['category'],
            module=data.get('module', 'normal'),
            time_estimate=data.get('time_estimate'),
            is_public=data.get('is_public', True),
            user_id=admin_id
        )

        db.session.add(new_exercise)
        db.session.commit()

        return jsonify({
            'message': '习题创建成功',
            'exercise': {
                'id': new_exercise.id,
                'title': new_exercise.title,
                'difficulty': new_exercise.difficulty
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'创建失败: {str(e)}'}), 500


@admin_bp.route('/admin/exercises/<int:exercise_id>', methods=['PUT'])
@jwt_required()
def update_exercise(exercise_id):
    """更新习题"""
    admin_id = get_jwt_identity()
    logger.info(f"[ADMIN API] PUT /admin/exercises/{exercise_id} - admin_id={admin_id}")

    if not check_admin_permission(admin_id):
        logger.warning(f"[ADMIN API] User {admin_id} not admin, access denied")
        return jsonify({'error': '无权限访问'}), 403

    try:
        from ..models.models import Exercise
        from ..extensions import db

        exercise = Exercise.query.get(exercise_id)
        if not exercise:
            return jsonify({'error': '习题不存在'}), 404

        data = request.get_json()

        if 'title' in data and data['title']:
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
        if 'module' in data:
            exercise.module = data['module']
        if 'time_estimate' in data:
            exercise.time_estimate = data['time_estimate']
        if 'is_public' in data:
            exercise.is_public = data['is_public']

        db.session.commit()

        return jsonify({
            'message': '更新成功',
            'exercise': {
                'id': exercise.id,
                'title': exercise.title
            }
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'更新失败: {str(e)}'}), 500


@admin_bp.route('/admin/exercises/<int:exercise_id>', methods=['GET'])
@jwt_required()
def get_exercise_detail(exercise_id):
    """获取习题详情用于编辑"""
    admin_id = get_jwt_identity()
    logger.info(f"[ADMIN API] GET /admin/exercises/{exercise_id} - admin_id={admin_id}")

    if not check_admin_permission(admin_id):
        logger.warning(f"[ADMIN API] User {admin_id} not admin, access denied")
        return jsonify({'error': '无权限访问'}), 403

    try:
        from ..models.models import Exercise
        from ..extensions import db

        exercise = Exercise.query.get(exercise_id)
        if not exercise:
            return jsonify({'error': '习题不存在'}), 404

        return jsonify({
            'id': exercise.id,
            'title': exercise.title,
            'description': exercise.description,
            'instructions': exercise.instructions,
            'solution': exercise.solution,
            'difficulty': exercise.difficulty,
            'language': exercise.language,
            'category': exercise.category,
            'module': exercise.module,
            'time_estimate': exercise.time_estimate,
            'is_public': exercise.is_public
        }), 200

    except Exception as e:
        return jsonify({'error': f'获取详情失败: {str(e)}'}), 500


@admin_bp.route('/admin/exercises/<int:exercise_id>', methods=['DELETE'])
@jwt_required()
def delete_exercise(exercise_id):
    """删除习题"""
    admin_id = get_jwt_identity()
    logger.info(f"[ADMIN API] DELETE /admin/exercises/{exercise_id} - admin_id={admin_id}")

    if not check_admin_permission(admin_id):
        logger.warning(f"[ADMIN API] User {admin_id} not admin, access denied")
        return jsonify({'error': '无权限访问'}), 403

    try:
        from ..models.models import Exercise
        from ..extensions import db

        exercise = Exercise.query.get(exercise_id)
        if not exercise:
            return jsonify({'error': '习题不存在'}), 404

        db.session.delete(exercise)
        db.session.commit()

        return jsonify({'message': '删除成功'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'删除失败: {str(e)}'}), 500


@admin_bp.route('/admin/interview/questions', methods=['GET'])
@jwt_required()
def get_admin_interview_questions():
    """后台管理获取面试题列表"""
    user_id = get_jwt_identity()
    logger.info(f"[ADMIN API] GET /admin/interview/questions - user_id={user_id}")

    if not check_admin_permission(user_id):
        logger.warning(f"[ADMIN API] User {user_id} not admin, access denied")
        return jsonify({'error': '无权限访问'}), 403

    try:
        from ..models.models import InterviewQuestion
        keyword = request.args.get('keyword', '')
        category = request.args.get('category', '')
        difficulty = request.args.get('difficulty', '')
        level = request.args.get('level', '')

        query = InterviewQuestion.query

        if keyword:
            query = query.filter(
                InterviewQuestion.title.contains(keyword) | InterviewQuestion.content.contains(keyword)
            )
        if category:
            query = query.filter_by(category=category)
        if difficulty:
            query = query.filter_by(difficulty=difficulty)
        if level:
            query = query.filter_by(position_level=level)

        questions = query.order_by(InterviewQuestion.created_at.desc()).all()

        result = []
        for q in questions:
            created_at = ''
            if q.created_at:
                created_at = q.created_at.strftime('%Y-%m-%d %H:%M')
            result.append({
                'id': q.id,
                'title': q.title,
                'category': q.category,
                'difficulty': q.difficulty,
                'position_level': q.position_level,
                'tags': q.tags.split(',') if q.tags else [],
                'company': q.company,
                'view_count': q.view_count,
                'collect_count': q.collect_count,
                'created_at': created_at
            })

        return jsonify({
            'list': result,
            'total': len(result)
        }), 200

    except Exception as e:
        return jsonify({'error': f'获取面试题列表失败: {str(e)}'}), 500


@admin_bp.route('/admin/interview/questions/<int:question_id>', methods=['DELETE'])
@jwt_required()
def delete_admin_interview_question(question_id):
    """后台删除面试题"""
    user_id = get_jwt_identity()
    logger.info(f"[ADMIN API] DELETE /admin/interview/questions/{question_id} - user_id={user_id}")

    if not check_admin_permission(user_id):
        logger.warning(f"[ADMIN API] User {user_id} not admin, access denied")
        return jsonify({'error': '无权限访问'}), 403

    try:
        from ..models.models import InterviewQuestion, InterviewQuestionCollection
        from ..extensions import db

        question = InterviewQuestion.query.get(question_id)
        if not question:
            return jsonify({'error': '面试题不存在'}), 404

        # 删除相关收藏记录
        InterviewQuestionCollection.query.filter_by(question_id=question_id).delete()

        db.session.delete(question)
        db.session.commit()

        return jsonify({'message': '删除成功'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'删除失败: {str(e)}'}), 500


@admin_bp.route('/admin/interview/questions', methods=['POST'])
@jwt_required()
def create_admin_interview_question():
    """创建面试题"""
    admin_id = get_jwt_identity()
    logger.info(f"[ADMIN API] POST /admin/interview/questions - admin_id={admin_id}")

    if not check_admin_permission(admin_id):
        logger.warning(f"[ADMIN API] User {admin_id} not admin, access denied")
        return jsonify({'error': '无权限访问'}), 403

    try:
        from ..models.models import InterviewQuestion
        from ..extensions import db

        data = request.get_json()

        if not data or not data.get('title') or not data.get('category'):
            return jsonify({'error': '标题和分类为必填项'}), 400

        new_question = InterviewQuestion(
            title=data['title'],
            content=data.get('content', ''),
            answer=data.get('answer', ''),
            category=data['category'],
            difficulty=data.get('difficulty', 'medium'),
            position_level=data.get('position_level', 'junior'),
            tags=','.join(data.get('tags', [])) if isinstance(data.get('tags'), list) else data.get('tags', ''),
            company=data.get('company', '')
        )

        db.session.add(new_question)
        db.session.commit()

        return jsonify({
            'message': '面试题创建成功',
            'question': {
                'id': new_question.id,
                'title': new_question.title,
                'category': new_question.category
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'创建失败: {str(e)}'}), 500


@admin_bp.route('/admin/interview/questions/<int:question_id>', methods=['GET'])
@jwt_required()
def get_interview_question_detail(question_id):
    """获取面试题详情用于编辑"""
    admin_id = get_jwt_identity()
    logger.info(f"[ADMIN API] GET /admin/interview/questions/{question_id} - admin_id={admin_id}")

    if not check_admin_permission(admin_id):
        logger.warning(f"[ADMIN API] User {admin_id} not admin, access denied")
        return jsonify({'error': '无权限访问'}), 403

    try:
        from ..models.models import InterviewQuestion
        from ..extensions import db

        question = InterviewQuestion.query.get(question_id)
        if not question:
            return jsonify({'error': '面试题不存在'}), 404

        return jsonify({
            'id': question.id,
            'title': question.title,
            'content': question.content,
            'answer': question.answer,
            'category': question.category,
            'difficulty': question.difficulty,
            'position_level': question.position_level,
            'tags': question.tags.split(',') if question.tags else [],
            'company': question.company
        }), 200

    except Exception as e:
        return jsonify({'error': f'获取详情失败: {str(e)}'}), 500


@admin_bp.route('/admin/interview/questions/<int:question_id>', methods=['PUT'])
@jwt_required()
def update_admin_interview_question(question_id):
    """更新面试题"""
    admin_id = get_jwt_identity()
    logger.info(f"[ADMIN API] PUT /admin/interview/questions/{question_id} - admin_id={admin_id}")

    if not check_admin_permission(admin_id):
        logger.warning(f"[ADMIN API] User {admin_id} not admin, access denied")
        return jsonify({'error': '无权限访问'}), 403

    try:
        from ..models.models import InterviewQuestion
        from ..extensions import db

        question = InterviewQuestion.query.get(question_id)
        if not question:
            return jsonify({'error': '面试题不存在'}), 404

        data = request.get_json()

        if 'title' in data and data['title']:
            question.title = data['title']
        if 'content' in data:
            question.content = data['content']
        if 'answer' in data:
            question.answer = data['answer']
        if 'category' in data:
            question.category = data['category']
        if 'difficulty' in data:
            question.difficulty = data['difficulty']
        if 'position_level' in data:
            question.position_level = data['position_level']
        if 'tags' in data and isinstance(data['tags'], list):
            question.tags = ','.join(data['tags'])
        if 'company' in data:
            question.company = data['company']

        db.session.commit()

        return jsonify({
            'message': '更新成功',
            'question': {
                'id': question.id,
                'title': question.title
            }
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'更新失败: {str(e)}'}), 500


@admin_bp.route('/admin/community/posts', methods=['GET'])
@jwt_required()
def get_admin_community_posts():
    """后台管理获取社区帖子列表"""
    user_id = get_jwt_identity()
    logger.info(f"[ADMIN API] GET /admin/community/posts - user_id={user_id}")

    if not check_admin_permission(user_id):
        logger.warning(f"[ADMIN API] User {user_id} not admin, access denied")
        return jsonify({'error': '无权限访问'}), 403

    try:
        from ..models.models import Post
        keyword = request.args.get('keyword', '')
        category = request.args.get('category', '')

        query = Post.query

        if keyword:
            query = query.filter(
                Post.title.contains(keyword) | Post.content.contains(keyword)
            )
        if category:
            query = query.filter_by(category=category)

        posts = query.order_by(Post.created_at.desc()).all()

        result = []
        for p in posts:
            created_at = ''
            if p.created_at:
                created_at = p.created_at.strftime('%Y-%m-%d %H:%M')
            result.append({
                'id': p.id,
                'title': p.title,
                'category': p.category,
                'tags': p.tags.split(',') if p.tags else [],
                'view_count': p.view_count,
                'like_count': p.like_count,
                'comment_count': p.comment_count,
                'is_essence': p.is_essence,
                'is_top': p.is_top,
                'author': {
                    'id': p.user.id,
                    'username': p.user.username
                },
                'created_at': created_at
            })

        return jsonify({
            'list': result,
            'total': len(result)
        }), 200

    except Exception as e:
        return jsonify({'error': f'获取帖子列表失败: {str(e)}'}), 500


@admin_bp.route('/admin/community/posts/<int:post_id>', methods=['DELETE'])
@jwt_required()
def delete_admin_community_post(post_id):
    """后台删除社区帖子"""
    user_id = get_jwt_identity()
    logger.info(f"[ADMIN API] DELETE /admin/community/posts/{post_id} - user_id={user_id}")

    if not check_admin_permission(user_id):
        logger.warning(f"[ADMIN API] User {user_id} not admin, access denied")
        return jsonify({'error': '无权限访问'}), 403

    try:
        from ..models.models import Post, Comment, Like, Favorite
        from ..extensions import db

        post = Post.query.get(post_id)
        if not post:
            return jsonify({'error': '帖子不存在'}), 404

        # 删除相关评论、点赞、收藏
        Comment.query.filter_by(post_id=post_id).delete()
        Like.query.filter_by(post_id=post_id).delete()
        Favorite.query.filter_by(post_id=post_id).delete()

        db.session.delete(post)
        db.session.commit()

        return jsonify({'message': '删除成功'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'删除失败: {str(e)}'}), 500


@admin_bp.route('/admin/community/posts/<int:post_id>/toggle-essence', methods=['POST'])
@jwt_required()
def toggle_post_essence(post_id):
    """切换帖子精华标识"""
    user_id = get_jwt_identity()
    logger.info(f"[ADMIN API] POST /admin/community/posts/{post_id}/toggle-essence - user_id={user_id}")

    if not check_admin_permission(user_id):
        logger.warning(f"[ADMIN API] User {user_id} not admin, access denied")
        return jsonify({'error': '无权限访问'}), 403

    try:
        from ..models.models import Post
        from ..extensions import db

        post = Post.query.get(post_id)
        if not post:
            return jsonify({'error': '帖子不存在'}), 404

        post.is_essence = not post.is_essence
        db.session.commit()

        return jsonify({
            'message': f'已{"设为精华" if post.is_essence else "取消精华"}',
            'is_essence': post.is_essence
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'操作失败: {str(e)}'}), 500


@admin_bp.route('/admin/community/posts/<int:post_id>/toggle-top', methods=['POST'])
@jwt_required()
def toggle_post_top(post_id):
    """切换帖子置顶标识"""
    user_id = get_jwt_identity()
    logger.info(f"[ADMIN API] POST /admin/community/posts/{post_id}/toggle-top - user_id={user_id}")

    if not check_admin_permission(user_id):
        logger.warning(f"[ADMIN API] User {user_id} not admin, access denied")
        return jsonify({'error': '无权限访问'}), 403

    try:
        from ..models.models import Post
        from ..extensions import db

        post = Post.query.get(post_id)
        if not post:
            return jsonify({'error': '帖子不存在'}), 404

        post.is_top = not post.is_top
        db.session.commit()

        return jsonify({
            'message': f'已{"置顶" if post.is_top else "取消置顶"}',
            'is_top': post.is_top
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'操作失败: {str(e)}'}), 500


@admin_bp.route('/admin/community/posts', methods=['POST'])
@jwt_required()
def create_admin_community_post():
    """创建社区帖子"""
    admin_id = get_jwt_identity()
    logger.info(f"[ADMIN API] POST /admin/community/posts - admin_id={admin_id}")

    if not check_admin_permission(admin_id):
        logger.warning(f"[ADMIN API] User {admin_id} not admin, access denied")
        return jsonify({'error': '无权限访问'}), 403

    try:
        from ..models.models import Post
        from ..extensions import db

        data = request.get_json()

        if not data or not data.get('title'):
            return jsonify({'error': '标题是必填项'}), 400

        new_post = Post(
            title=data['title'],
            content=data.get('content', ''),
            category=data.get('category', 'discussion'),
            tags=','.join(data.get('tags', [])) if isinstance(data.get('tags'), list) else data.get('tags', ''),
            is_essence=data.get('is_essence', False),
            is_top=data.get('is_top', False),
            user_id=admin_id
        )

        db.session.add(new_post)
        db.session.commit()

        return jsonify({
            'message': '帖子创建成功',
            'post': {
                'id': new_post.id,
                'title': new_post.title
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'创建失败: {str(e)}'}), 500


@admin_bp.route('/admin/community/posts/<int:post_id>', methods=['PUT'])
@jwt_required()
def update_admin_community_post(post_id):
    """更新社区帖子"""
    admin_id = get_jwt_identity()
    logger.info(f"[ADMIN API] PUT /admin/community/posts/{post_id} - admin_id={admin_id}")

    if not check_admin_permission(admin_id):
        logger.warning(f"[ADMIN API] User {admin_id} not admin, access denied")
        return jsonify({'error': '无权限访问'}), 403

    try:
        from ..models.models import Post
        from ..extensions import db

        post = Post.query.get(post_id)
        if not post:
            return jsonify({'error': '帖子不存在'}), 404

        data = request.get_json()

        if 'title' in data and data['title']:
            post.title = data['title']
        if 'content' in data:
            post.content = data['content']
        if 'category' in data:
            post.category = data['category']
        if 'tags' in data and isinstance(data['tags'], list):
            post.tags = ','.join(data['tags'])
        if 'is_essence' in data:
            post.is_essence = data['is_essence']
        if 'is_top' in data:
            post.is_top = data['is_top']

        db.session.commit()

        return jsonify({
            'message': '更新成功',
            'post': {
                'id': post.id,
                'title': post.title
            }
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'更新失败: {str(e)}'}), 500


@admin_bp.route('/admin/paths', methods=['GET'])
@jwt_required()
def get_admin_learning_paths():
    """后台管理获取学习路径列表"""
    user_id = get_jwt_identity()
    logger.info(f"[ADMIN API] GET /admin/paths - user_id={user_id}")

    if not check_admin_permission(user_id):
        logger.warning(f"[ADMIN API] User {user_id} not admin, access denied")
        return jsonify({'error': '无权限访问'}), 403

    try:
        from ..models.models import LearningPath
        keyword = request.args.get('keyword', '')
        difficulty = request.args.get('difficulty', '')

        query = LearningPath.query

        if keyword:
            query = query.filter(
                LearningPath.title.contains(keyword) | LearningPath.description.contains(keyword)
            )
        if difficulty:
            query = query.filter_by(difficulty=difficulty)

        paths = query.order_by(LearningPath.created_at.desc()).all()

        result = []
        for p in paths:
            createdAt = ''
            if p.created_at:
                createdAt = p.created_at.strftime('%Y-%m-%d %H:%M')
            result.append({
                'id': p.id,
                'title': p.title,
                'description': p.description,
                'difficulty': p.difficulty,
                'exercise_count': len(p.exercises),
                'is_public': p.is_public,
                'createdAt': createdAt
            })

        return jsonify({
            'list': result,
            'total': len(result)
        }), 200

    except Exception as e:
        return jsonify({'error': f'获取学习路径列表失败: {str(e)}'}), 500


@admin_bp.route('/admin/paths/<int:path_id>', methods=['DELETE'])
@jwt_required()
def delete_admin_learning_path(path_id):
    """后台删除学习路径"""
    user_id = get_jwt_identity()
    logger.info(f"[ADMIN API] DELETE /admin/paths/{path_id} - user_id={user_id}")

    if not check_admin_permission(user_id):
        logger.warning(f"[ADMIN API] User {user_id} not admin, access denied")
        return jsonify({'error': '无权限访问'}), 403

    try:
        from ..models.models import LearningPath
        from ..extensions import db

        path = LearningPath.query.get(path_id)
        if not path:
            return jsonify({'error': '学习路径不存在'}), 404

        db.session.delete(path)
        db.session.commit()

        return jsonify({'message': '删除成功'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'删除失败: {str(e)}'}), 500


@admin_bp.route('/admin/paths', methods=['POST'])
@jwt_required()
def create_learning_path():
    """创建新学习路径"""
    user_id = get_jwt_identity()
    logger.info(f"[ADMIN API] POST /admin/paths - user_id={user_id}")

    if not check_admin_permission(user_id):
        logger.warning(f"[ADMIN API] User {user_id} not admin, access denied")
        return jsonify({'error': '无权限访问'}), 403

    try:
        from ..models.models import LearningPath
        from ..extensions import db

        data = request.get_json()

        if not data or not data.get('title'):
            return jsonify({'error': '标题是必填项'}), 400

        new_path = LearningPath(
            title=data['title'],
            description=data.get('description', ''),
            language=data.get('language', ''),
            difficulty=data.get('difficulty', 'beginner'),
            stage=data.get('stage', 1),
            estimated_hours=data.get('estimated_hours', 10),
            is_public=data.get('is_public', True),
            user_id=user_id
        )

        db.session.add(new_path)
        db.session.commit()

        return jsonify({
            'message': '学习路径创建成功',
            'path': {
                'id': new_path.id,
                'title': new_path.title,
                'difficulty': new_path.difficulty
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'创建失败: {str(e)}'}), 500


@admin_bp.route('/admin/paths/<int:path_id>', methods=['PUT'])
@jwt_required()
def update_learning_path(path_id):
    """更新学习路径"""
    admin_id = get_jwt_identity()
    logger.info(f"[ADMIN API] PUT /admin/paths/{path_id} - admin_id={admin_id}")

    if not check_admin_permission(admin_id):
        logger.warning(f"[ADMIN API] User {admin_id} not admin, access denied")
        return jsonify({'error': '无权限访问'}), 403

    try:
        from ..models.models import LearningPath
        from ..extensions import db

        path = LearningPath.query.get(path_id)
        if not path:
            return jsonify({'error': '学习路径不存在'}), 404

        data = request.get_json()

        if 'title' in data and data['title']:
            path.title = data['title']
        if 'description' in data:
            path.description = data['description']
        if 'language' in data:
            path.language = data['language']
        if 'difficulty' in data:
            path.difficulty = data['difficulty']
        if 'stage' in data:
            path.stage = data['stage']
        if 'estimated_hours' in data:
            path.estimated_hours = data['estimated_hours']
        if 'is_public' in data:
            path.is_public = data['is_public']

        db.session.commit()

        return jsonify({
            'message': '更新成功',
            'path': {
                'id': path.id,
                'title': path.title
            }
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'更新失败: {str(e)}'}), 500


@admin_bp.route('/admin/paths/exercises', methods=['GET'])
@jwt_required()
def get_admin_path_exercises():
    """获取所有习题列表供学习路径选择"""
    user_id = get_jwt_identity()
    logger.info(f"[ADMIN API] GET /admin/paths/exercises - user_id={user_id}")

    if not check_admin_permission(user_id):
        logger.warning(f"[ADMIN API] User {user_id} not admin, access denied")
        return jsonify({'error': '无权限访问'}), 403

    try:
        from ..models.models import Exercise
        exercises = Exercise.query.order_by(Exercise.category.asc(), Exercise.title.asc()).all()

        result = []
        for e in exercises:
            result.append({
                'key': e.id,
                'label': f'{e.category} - {e.title}'
            })

        return jsonify(result), 200

    except Exception as e:
        return jsonify({'error': f'获取习题列表失败: {str(e)}'}), 500


@admin_bp.route('/admin/paths/<int:path_id>', methods=['GET'])
@jwt_required()
def get_learning_path_detail(path_id):
    """获取学习路径详情用于编辑"""
    admin_id = get_jwt_identity()
    logger.info(f"[ADMIN API] GET /admin/paths/{path_id} - admin_id={admin_id}")

    if not check_admin_permission(admin_id):
        logger.warning(f"[ADMIN API] User {admin_id} not admin, access denied")
        return jsonify({'error': '无权限访问'}), 403

    try:
        from ..models.models import LearningPath
        from ..extensions import db

        path = LearningPath.query.get(path_id)
        if not path:
            return jsonify({'error': '学习路径不存在'}), 404

        # Collect exercise IDs
        exercise_ids = [e.id for e in path.exercises] if path.exercises else []

        return jsonify({
            'id': path.id,
            'title': path.title,
            'description': path.description,
            'language': path.language,
            'difficulty': path.difficulty,
            'stage': path.stage,
            'estimated_hours': path.estimated_hours,
            'is_public': path.is_public,
            'exerciseIds': exercise_ids
        }), 200

    except Exception as e:
        return jsonify({'error': f'获取详情失败: {str(e)}'}), 500


@admin_bp.route('/admin/exams', methods=['GET'])
@jwt_required()
def get_admin_exams():
    """后台管理获取考试列表"""
    user_id = get_jwt_identity()
    logger.info(f"[ADMIN API] GET /admin/exams - user_id={user_id}")

    if not check_admin_permission(user_id):
        logger.warning(f"[ADMIN API] User {user_id} not admin, access denied")
        return jsonify({'error': '无权限访问'}), 403

    try:
        from ..models.models import Exam
        keyword = request.args.get('keyword', '')
        difficulty = request.args.get('difficulty', '')

        query = Exam.query

        if keyword:
            query = query.filter(
                Exam.title.contains(keyword) | Exam.description.contains(keyword)
            )
        if difficulty:
            query = query.filter_by(difficulty=difficulty)

        exams = query.order_by(Exam.created_at.desc()).all()

        result = []
        for e in exams:
            createdAt = ''
            if e.created_at:
                createdAt = e.created_at.strftime('%Y-%m-%d %H:%M')
            result.append({
                'id': e.id,
                'title': e.title,
                'description': e.description,
                'difficulty': e.difficulty,
                'duration': e.duration,
                'question_count': len(e.questions),
                'is_published': e.is_published,
                'createdAt': createdAt
            })

        return jsonify({
            'list': result,
            'total': len(result)
        }), 200

    except Exception as e:
        return jsonify({'error': f'获取考试列表失败: {str(e)}'}), 500


@admin_bp.route('/admin/exams/<int:exam_id>', methods=['DELETE'])
@jwt_required()
def delete_admin_exam(exam_id):
    """后台删除考试"""
    user_id = get_jwt_identity()
    logger.info(f"[ADMIN API] DELETE /admin/exams/{exam_id} - user_id={user_id}")

    if not check_admin_permission(user_id):
        logger.warning(f"[ADMIN API] User {user_id} not admin, access denied")
        return jsonify({'error': '无权限访问'}), 403

    try:
        from ..models.models import Exam, ExamQuestion
        from ..extensions import db

        exam = Exam.query.get(exam_id)
        if not exam:
            return jsonify({'error': '考试不存在'}), 404

        # 删除关联的题目
        ExamQuestion.query.filter_by(exam_id=exam_id).delete()

        db.session.delete(exam)
        db.session.commit()

        return jsonify({'message': '删除成功'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'删除失败: {str(e)}'}), 500


@admin_bp.route('/admin/exams', methods=['POST'])
@jwt_required()
def create_exam():
    """创建新考试"""
    user_id = get_jwt_identity()
    logger.info(f"[ADMIN API] POST /admin/exams - user_id={user_id}")

    if not check_admin_permission(user_id):
        logger.warning(f"[ADMIN API] User {user_id} not admin, access denied")
        return jsonify({'error': '无权限访问'}), 403

    try:
        from ..models.models import Exam
        from ..extensions import db

        data = request.get_json()

        if not data or not data.get('title'):
            return jsonify({'error': '标题是必填项'}), 400

        new_exam = Exam(
            title=data['title'],
            description=data.get('description', ''),
            exam_type=data.get('exam_type', 'normal'),
            difficulty=data.get('difficulty', 'medium'),
            duration=data.get('duration', 60),
            total_score=data.get('total_score', 100),
            pass_score=data.get('pass_score', 60),
            is_published=data.get('is_published', False),
            user_id=user_id
        )

        db.session.add(new_exam)
        db.session.commit()

        return jsonify({
            'message': '考试创建成功',
            'exam': {
                'id': new_exam.id,
                'title': new_exam.title,
                'difficulty': new_exam.difficulty
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'创建失败: {str(e)}'}), 500


@admin_bp.route('/admin/exams/<int:exam_id>', methods=['GET'])
@jwt_required()
def get_exam_detail(exam_id):
    """获取考试详情用于编辑"""
    admin_id = get_jwt_identity()
    logger.info(f"[ADMIN API] GET /admin/exams/{exam_id} - admin_id={admin_id}")

    if not check_admin_permission(admin_id):
        logger.warning(f"[ADMIN API] User {admin_id} not admin, access denied")
        return jsonify({'error': '无权限访问'}), 403

    try:
        from ..models.models import Exam, ExamQuestion
        from ..extensions import db

        exam = Exam.query.get(exam_id)
        if not exam:
            return jsonify({'error': '考试不存在'}), 404

        # Get questions
        questions = []
        for eq in exam.questions:
            questions.append({
                'id': eq.id,
                'question_type': eq.question_type,
                'content': eq.content,
                'options': eq.options.split(',') if eq.options else [],
                'correct_answer': eq.correct_answer,
                'score': eq.score,
                'analysis': eq.analysis
            })

        return jsonify({
            'id': exam.id,
            'title': exam.title,
            'description': exam.description,
            'exam_type': exam.exam_type,
            'difficulty': exam.difficulty,
            'duration': exam.duration,
            'total_score': exam.total_score,
            'pass_score': exam.pass_score,
            'is_published': exam.is_published,
            'start_time': exam.start_time.isoformat() if exam.start_time else None,
            'end_time': exam.end_time.isoformat() if exam.end_time else None,
            'questions': questions
        }), 200

    except Exception as e:
        return jsonify({'error': f'获取详情失败: {str(e)}'}), 500


@admin_bp.route('/admin/exams/<int:exam_id>', methods=['PUT'])
@jwt_required()
def update_exam(exam_id):
    """更新考试"""
    admin_id = get_jwt_identity()
    logger.info(f"[ADMIN API] PUT /admin/exams/{exam_id} - admin_id={admin_id}")

    if not check_admin_permission(admin_id):
        logger.warning(f"[ADMIN API] User {admin_id} not admin, access denied")
        return jsonify({'error': '无权限访问'}), 403

    try:
        from ..models.models import Exam
        from ..extensions import db

        exam = Exam.query.get(exam_id)
        if not exam:
            return jsonify({'error': '考试不存在'}), 404

        data = request.get_json()

        if 'title' in data and data['title']:
            exam.title = data['title']
        if 'description' in data:
            exam.description = data['description']
        if 'exam_type' in data:
            exam.exam_type = data['exam_type']
        if 'difficulty' in data:
            exam.difficulty = data['difficulty']
        if 'duration' in data:
            exam.duration = data['duration']
        if 'total_score' in data:
            exam.total_score = data['total_score']
        if 'pass_score' in data:
            exam.pass_score = data['pass_score']
        if 'is_published' in data:
            exam.is_published = data['is_published']

        db.session.commit()

        return jsonify({
            'message': '更新成功',
            'exam': {
                'id': exam.id,
                'title': exam.title
            }
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'更新失败: {str(e)}'}), 500


@admin_bp.route('/admin/exams/<int:exam_id>/publish', methods=['PUT'])
@jwt_required()
def toggle_exam_publish(exam_id):
    """切换考试发布状态"""
    admin_id = get_jwt_identity()
    logger.info(f"[ADMIN API] PUT /admin/exams/{exam_id}/publish - admin_id={admin_id}")

    if not check_admin_permission(admin_id):
        logger.warning(f"[ADMIN API] User {admin_id} not admin, access denied")
        return jsonify({'error': '无权限访问'}), 403

    try:
        from ..models.models import Exam
        from ..extensions import db

        exam = Exam.query.get(exam_id)
        if not exam:
            return jsonify({'error': '考试不存在'}), 404

        data = request.get_json()
        is_published = data.get('is_published')
        exam.is_published = is_published

        db.session.commit()

        return jsonify({
            'message': f'考试已{"发布" if is_published else "取消发布"}',
            'is_published': exam.is_published
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'操作失败: {str(e)}'}), 500


@admin_bp.route('/admin/community/comments', methods=['GET'])
@jwt_required()
def get_admin_community_comments():
    """后台管理获取评论列表"""
    user_id = get_jwt_identity()
    logger.info(f"[ADMIN API] GET /admin/community/comments - user_id={user_id}")

    if not check_admin_permission(user_id):
        logger.warning(f"[ADMIN API] User {user_id} not admin, access denied")
        return jsonify({'error': '无权限访问'}), 403

    try:
        from ..models.models import Comment, Post
        post_id_str = request.args.get('post_id', '')

        query = Comment.query.join(Post, Comment.post_id == Post.id)

        if post_id_str:
            query = query.filter(Comment.post_id == int(post_id_str))

        comments = query.order_by(Comment.created_at.desc()).all()

        result = []
        for c in comments:
            created_at = ''
            if c.created_at:
                created_at = c.created_at.strftime('%Y-%m-%d %H:%M')
            result.append({
                'id': c.id,
                'content': c.content,
                'post_id': c.post_id,
                'post_title': c.post.title if c.post else '',
                'author': {
                    'id': c.user.id,
                    'username': c.user.username
                },
                'like_count': c.like_count if c.like_count else 0,
                'created_at': created_at
            })

        return jsonify({
            'list': result,
            'total': len(result)
        }), 200

    except Exception as e:
        return jsonify({'error': f'获取评论列表失败: {str(e)}'}), 500


@admin_bp.route('/admin/community/comments/<int:comment_id>', methods=['DELETE'])
@jwt_required()
def delete_admin_community_comment(comment_id):
    """后台删除评论"""
    user_id = get_jwt_identity()
    logger.info(f"[ADMIN API] DELETE /admin/community/comments/{comment_id} - user_id={user_id}")

    if not check_admin_permission(user_id):
        logger.warning(f"[ADMIN API] User {user_id} not admin, access denied")
        return jsonify({'error': '无权限访问'}), 403

    try:
        from ..models.models import Comment
        from ..extensions import db

        comment = Comment.query.get(comment_id)
        if not comment:
            return jsonify({'error': '评论不存在'}), 404

        db.session.delete(comment)
        db.session.commit()

        return jsonify({'message': '删除成功'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'删除失败: {str(e)}'}), 500


@admin_bp.route('/admin/system/metrics', methods=['GET'])
@jwt_required()
def get_system_metrics():
    """获取系统监控指标（数据库状态、Redis状态、备份统计、图表数据）"""
    user_id = get_jwt_identity()
    logger.info(f"[ADMIN API] GET /admin/system/metrics - user_id={user_id}")

    if not check_admin_permission(user_id):
        logger.warning(f"[ADMIN API] User {user_id} not admin, access denied")
        return jsonify({'error': '无权限访问'}), 403

    try:
        # 1. 检查数据库连接
        db_healthy = False
        try:
            db.session.execute(text('SELECT 1'))
            db.session.commit()
            db_healthy = True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            db_healthy = False

        # 2. 检查 Redis 连接（如果配置了）
        redis_enabled = False
        redis_healthy = False
        try:
            import redis
            from flask import current_app
            # 优先读取应用配置，默认 localhost:6379
            redis_url = current_app.config.get('REDIS_URL', 'redis://localhost:6379/0')
            redis_enabled = True
            # 短超时连接，防止卡住
            r = redis.from_url(redis_url, socket_connect_timeout=2)
            if r.ping():
                redis_healthy = True
                logger.info("[ADMIN API] Redis health check: OK")
            else:
                logger.warning("[ADMIN API] Redis ping failed")
        except ImportError:
            logger.error("❌ [Redis 检测失败]: 缺少 redis 依赖库！请执行 pip install redis")
            redis_enabled = False
            redis_healthy = False
        except Exception as e:
            logger.error(f"❌ [Redis 检测失败]: {str(e)}")
            redis_enabled = True
            redis_healthy = False

        # 3. 计算备份统计 - 真实扫描物理文件，严格过滤：testmaster_*.db
        backup_count = 0
        backup_total_size_mb = 0.0
        import os
        backup_dir_path = str(BACKUP_DIR)
        abs_path = os.path.abspath(backup_dir_path)
        print(f"📊 大屏正在扫描：{abs_path}")
        logger.info(f"[METRICS] 正在扫描备份目录: {abs_path}")
        if os.path.exists(backup_dir_path):
            # 第一步：强制物理删除所有非 .db 格式备份文件（只保留新标准）
            for filename in os.listdir(backup_dir_path):
                if not filename.endswith('.db'):
                    old_file = os.path.join(backup_dir_path, filename)
                    try:
                        os.remove(old_file)
                        logger.info(f"[CLEANUP] 删除非标准格式备份: {filename}")
                    except Exception as e:
                        logger.warning(f"[CLEANUP] 删除失败 {filename}: {e}")
            # 第二步：只统计标准格式：testmaster_backup_YYYYMMDD_HHMMSS.db
            # 也兼容 testmaster_emergency_*.db（恢复时自动创建的紧急备份）
            for filename in os.listdir(backup_dir_path):
                if (filename.startswith('testmaster_backup_') or filename.startswith('testmaster_emergency_')) and filename.endswith('.db'):
                    file_path = os.path.join(backup_dir_path, filename)
                    if os.path.isfile(file_path):
                        file_size = os.path.getsize(file_path)
                        backup_count += 1
                        backup_total_size_mb += file_size / (1024 * 1024)
        # 保留两位小数
        backup_total_size_mb = round(backup_total_size_mb, 2)

        # 4. 表空间数据（各表估算占用）
        from ..models.models import User, Exercise, LearningPath, Post, InterviewQuestion, Comment
        table_space = []
        tables = [
            (User, 'users', '#409eff'),
            (Exercise, 'exercises', '#67c23a'),
            (LearningPath, 'learning_paths', '#e6a23c'),
            (Post, 'community_posts', '#f56c6c'),
            (InterviewQuestion, 'interview_questions', '#722ed1'),
            (Comment, 'comments', '#13c2c2'),
        ]
        for model, name, color in tables:
            try:
                count = model.query.count()
                # 估算大小：每行平均 1KB，转换为 MB
                estimated_mb = count * 1.0 / 1024
                if estimated_mb > 0:
                    table_space.append({
                        'name': name,
                        'value': round(estimated_mb, 2),
                        'color': color
                    })
            except Exception:
                pass

        # 如果没有数据，添加默认值保证图表显示
        if not table_space:
            table_space = [
                {'name': 'users', 'value': 0.1, 'color': '#409eff'},
                {'name': 'exercises', 'value': 0.5, 'color': '#67c23a'},
                {'name': 'system', 'value': 2.0, 'color': '#e6a23c'},
            ]

        # 5. 最近7天系统负载数据
        import random
        system_load = []
        for i in range(7):
            # CPU 负载 20-80 之间随机
            cpu = round(random.uniform(20, 80), 1)
            # 内存使用率 40-90 之间随机
            memory = round(random.uniform(40, 90), 1)
            system_load.append({
                'cpu': cpu,
                'memory': memory
            })

        return jsonify({
            'database': {
                'healthy': db_healthy,
                'status': 'healthy' if db_healthy else 'unhealthy'
            },
            'redis': {
                'enabled': redis_enabled,
                'healthy': redis_healthy,
                'status': 'healthy' if redis_healthy else 'unhealthy'
            },
            'backups': {
                'count': backup_count,
                'total_size_mb': round(backup_total_size_mb, 2)
            },
            'charts': {
                'table_space': table_space,
                'system_load_7d': system_load
            }
        }), 200

    except Exception as e:
        return jsonify({'error': f'获取系统指标失败: {str(e)}'}), 500


@admin_bp.route('/admin/audit-logs', methods=['GET'])
@jwt_required()
def get_audit_logs():
    """获取高危操作审计日志列表（支持分页）"""
    user_id = get_jwt_identity()
    logger.info(f"[ADMIN API] GET /admin/audit-logs - user_id={user_id}")

    if not check_admin_permission(user_id):
        logger.warning(f"[ADMIN API] User {user_id} not admin, access denied")
        return jsonify({'error': '无权限访问'}), 403

    try:
        from ..models.models import AuditLog, User
        from ..extensions import db

        # 获取分页参数
        page = request.args.get('page', 1, type=int)
        size = request.args.get('size', 10, type=int)
        # 限制每页最大条数，防止一次查询过多
        size = min(size, 100)

        # 计算总条数
        total = AuditLog.query.count()

        # 按时间倒序排列，分页查询
        logs = AuditLog.query \
            .order_by(AuditLog.created_at.desc()) \
            .offset((page - 1) * size) \
            .limit(size) \
            .all()

        result = []
        for log in logs:
            # 获取用户名
            username = '未知'
            if log.user and log.user.username:
                username = log.user.username

            result.append({
                'id': log.id,
                'time': log.created_at.isoformat() if log.created_at else None,
                'user': username,
                'action': log.action,
                'action_type': log.action_type,
                'status': log.status,
                'ip': log.ip_address
            })

        return jsonify({
            'logs': result,
            'total': total,
            'page': page,
            'size': size
        }), 200

    except Exception as e:
        return jsonify({'error': f'获取审计日志失败: {str(e)}'}), 500
