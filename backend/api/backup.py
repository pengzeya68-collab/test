
# Backup Management API for TestMasterProject
# 统一使用与 admin.py 一致的备份格式
import os
import shutil
from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models.models import User

backup_bp = Blueprint('backup', __name__)

# 强制使用绝对路径，与 admin.py 保持一致
BACKUP_DIR = r"C:\Users\lenovo\Desktop\TestMasterProject\backups"
MAX_BACKUPS = 10

os.makedirs(BACKUP_DIR, exist_ok=True)

def get_database_path():
    """获取数据库文件路径"""
    return r"C:\Users\lenovo\Desktop\TestMasterProject\instance\testmaster.db"

def list_backups():
    """列出所有备份，按时间倒序"""
    backups = []
    if not os.path.exists(BACKUP_DIR):
        return []

    for filename in os.listdir(BACKUP_DIR):
        # 统一格式：testmaster_backup_*.db 或 testmaster_emergency_*.db
        if (filename.startswith('testmaster_backup_') or filename.startswith('testmaster_emergency_')) and filename.endswith('.db'):
            filepath = os.path.join(BACKUP_DIR, filename)
            if os.path.isfile(filepath):
                stat = os.stat(filepath)
                backups.append({
                    'name': filename,
                    'size': stat.st_size / (1024 * 1024),
                    'time': stat.st_mtime * 1000
                })

    backups.sort(key=lambda x: x['time'], reverse=True)
    return backups

def create_backup():
    """创建新备份"""
    src_db = get_database_path()
    if not os.path.exists(src_db):
        return None, "数据库文件不存在"

    # 生成备份文件名，与 admin.py 保持一致
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_filename = f"testmaster_backup_{timestamp}.db"
    backup_path = os.path.join(BACKUP_DIR, backup_filename)

    try:
        import sqlite3
        source = sqlite3.connect(src_db)
        backup = sqlite3.connect(backup_path)
        with backup:
            source.backup(backup)
        source.close()
        backup.close()
        return backup_filename, None
    except Exception as e:
        return None, str(e)

def delete_backup(backup_name):
    """删除指定备份"""
    backup_path = os.path.join(BACKUP_DIR, backup_name)
    if not os.path.exists(backup_path):
        return False, "备份文件不存在"

    try:
        os.remove(backup_path)
        return True, None
    except Exception as e:
        return False, str(e)

def clean_old_backups():
    """清理旧备份，只保留最近 MAX_BACKUPS 个"""
    backups = list_backups()
    if len(backups) <= MAX_BACKUPS:
        return 0

    deleted = 0
    for backup in backups[MAX_BACKUPS:]:
        ok, _ = delete_backup(backup['name'])
        if ok:
            deleted += 1
    return deleted

@backup_bp.route('/admin/backups', methods=['GET'])
@jwt_required()
def get_backups():
    """获取备份列表"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user or not user.is_admin:
        return jsonify({'error': '无权限'}), 403

    backups = list_backups()
    return jsonify({
        'backups': backups,
        'max_backups': MAX_BACKUPS
    }), 200

@backup_bp.route('/admin/backups', methods=['POST'])
@jwt_required()
def create_new_backup():
    """创建新备份"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user or not user.is_admin:
        return jsonify({'error': '无权限'}), 403

    backup_name, error = create_backup()
    if error:
        return jsonify({'error': f'创建备份失败: {error}'}), 500

    clean_old_backups()

    return jsonify({
        'message': '备份创建成功',
        'backup_name': backup_name
    }), 200

@backup_bp.route('/admin/backups/old', methods=['DELETE'])
@jwt_required()
def clean_old():
    """清理旧备份"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user or not user.is_admin:
        return jsonify({'error': '无权限'}), 403

    deleted = clean_old_backups()
    return jsonify({
        'message': f'清理完成，删除了 {deleted} 个旧备份',
        'deleted': deleted
    }), 200

@backup_bp.route('/admin/backups/<path:backup_name>/restore', methods=['POST'])
@jwt_required()
def restore(backup_name):
    """恢复备份"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user or not user.is_admin:
        return jsonify({'error': '无权限'}), 403

    backup_path = os.path.join(BACKUP_DIR, backup_name)
    if not os.path.exists(backup_path):
        return jsonify({'error': '备份文件不存在'}), 404

    src_db = get_database_path()

    # 恢复前创建紧急备份
    if os.path.exists(src_db):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        emergency_backup = os.path.join(BACKUP_DIR, f"testmaster_emergency_{timestamp}.db")
        shutil.copy2(src_db, emergency_backup)

    try:
        shutil.copy2(backup_path, src_db)
        return jsonify({'message': '备份恢复成功'}), 200
    except Exception as e:
        return jsonify({'error': f'恢复失败: {str(e)}'}), 500

@backup_bp.route('/admin/backups/<path:backup_name>', methods=['DELETE'])
@jwt_required()
def delete(backup_name):
    """删除备份"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user or not user.is_admin:
        return jsonify({'error': '无权限'}), 403

    ok, error = delete_backup(backup_name)
    if error:
        return jsonify({'error': f'删除失败: {error}'}), 500

    return jsonify({'message': '备份删除成功'}), 200
