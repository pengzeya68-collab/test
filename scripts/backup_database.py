#!/usr/bin/env python3
"""
数据库备份工具
支持：手动备份、自动备份、定时备份
"""

import os
import sys
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

# 🔥 强制写死绝对路径！全局统一备份目录
BACKUP_DIR = Path(r"C:\Users\lenovo\Desktop\TestMasterProject\backups")
# 数据库路径
DB_PATH = Path(r"C:\Users\lenovo\Desktop\TestMasterProject\instance\testmaster.db")

# 保留的备份数量（防止占用太多空间）
MAX_BACKUPS = 10


def ensure_backup_dir():
    """确保备份目录存在"""
    BACKUP_DIR.mkdir(exist_ok=True)


def create_backup():
    """创建数据库备份"""
    ensure_backup_dir()
    
    if not DB_PATH.exists():
        print(f"错误：数据库文件不存在: {DB_PATH}")
        return None
    
    # 生成备份文件名：testmaster_backup_YYYYMMDD_HHMMSS.db（统一命名规范）
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"testmaster_backup_{timestamp}.db"
    backup_path = BACKUP_DIR / backup_filename
    
    try:
        # 使用 SQLite 的备份功能（比直接复制更安全）
        source = sqlite3.connect(str(DB_PATH))
        backup = sqlite3.connect(str(backup_path))
        
        with backup:
            source.backup(backup)
        
        source.close()
        backup.close()
        
        # 获取文件大小
        size = backup_path.stat().st_size / (1024 * 1024)  # MB
        abs_path = os.path.abspath(str(backup_path))
        print(f"💾 备份已写入目录: {os.path.dirname(abs_path)}")
        print(f"[OK] 备份成功: {backup_filename}")
        print(f"   大小: {size:.2f} MB")
        print(f"   路径: {abs_path}")

        return backup_path
        
    except Exception as e:
        print(f"[ERROR] 备份失败: {e}")
        return None


def list_backups():
    """列出所有备份"""
    ensure_backup_dir()
    
    backups = []
    # 只列出标准格式备份：testmaster_backup_* 或 testmaster_emergency_*，且必须 .db 后缀
    import os
    for filename in os.listdir(BACKUP_DIR):
        if (filename.startswith('testmaster_backup_') or filename.startswith('testmaster_emergency_')) and filename.endswith('.db'):
            file_path = BACKUP_DIR / filename
            if file_path.is_file():
                stat = file_path.stat()
                backups.append({
                    'file': file_path,
                    'name': filename,
                    'size': stat.st_size / (1024 * 1024),
                    'time': datetime.fromtimestamp(stat.st_mtime)
                })
    
    # 按时间排序（最新的在前）
    backups.sort(key=lambda x: x['time'], reverse=True)
    return backups


def show_backups():
    """显示备份列表"""
    backups = list_backups()
    
    if not backups:
        print("[INFO] 暂无备份文件")
        return
    
    print(f"\n[INFO] 共有 {len(backups)} 个备份文件：\n")
    print(f"{'序号':<6}{'文件名':<30}{'大小':<12}{'备份时间':<20}")
    print("-" * 70)
    
    for i, backup in enumerate(backups, 1):
        time_str = backup['time'].strftime("%Y-%m-%d %H:%M:%S")
        print(f"{i:<6}{backup['name']:<30}{backup['size']:.2f} MB{'':<4}{time_str}")


def restore_backup(backup_name_or_index):
    """从备份恢复数据库"""
    backups = list_backups()
    
    if not backups:
        print("[ERROR] 没有可用的备份文件")
        return False
    
    # 尝试解析为索引
    try:
        index = int(backup_name_or_index) - 1
        if 0 <= index < len(backups):
            backup_file = backups[index]['file']
        else:
            print(f"[ERROR] 无效的序号: {backup_name_or_index}")
            return False
    except ValueError:
        # 作为文件名处理
        backup_file = BACKUP_DIR / backup_name_or_index
        if not backup_file.exists():
            print(f"[ERROR] 备份文件不存在: {backup_name_or_index}")
            return False
    
    # 确认恢复
    print(f"\n[WARNING] 警告：恢复备份将覆盖当前数据库！")
    print(f"   备份文件: {backup_file.name}")
    print(f"   备份时间: {datetime.fromtimestamp(backup_file.stat().st_mtime)}")
    
    confirm = input("\n确定要恢复吗？(yes/no): ")
    if confirm.lower() != 'yes':
        print("已取消恢复操作")
        return False
    
    try:
        # 先备份当前数据库（以防万一）
        if DB_PATH.exists():
            emergency_backup = BACKUP_DIR / f"testmaster_emergency_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            shutil.copy2(str(DB_PATH), str(emergency_backup))
            print(f"[OK] 已创建紧急备份: {emergency_backup.name}")
        
        # 恢复备份
        shutil.copy2(str(backup_file), str(DB_PATH))
        print(f"[OK] 数据库恢复成功！")
        return True
        
    except Exception as e:
        print(f"[ERROR] 恢复失败: {e}")
        return False


def clean_old_backups():
    """清理旧的备份文件，只保留最新的 MAX_BACKUPS 个"""
    backups = list_backups()

    if len(backups) <= MAX_BACKUPS:
        return

    old_backups = backups[MAX_BACKUPS:]
    print(f"\n[INFO] 清理 {len(old_backups)} 个旧备份...")

    for backup in old_backups:
        try:
            backup['file'].unlink()
            print(f"   已删除: {backup['name']}")
        except Exception as e:
            print(f"   删除失败 {backup['name']}: {e}")


def auto_backup():
    """自动备份（带清理旧备份）"""
    print("[AutoBackup] 执行自动备份...")
    backup_path = create_backup()

    if backup_path:
        clean_old_backups()
        return True
    return False


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='TestMaster 数据库备份工具')
    parser.add_argument('command', choices=['create', 'list', 'restore', 'auto'], 
                        help='命令: create(创建备份), list(列出备份), restore(恢复备份), auto(自动备份)')
    parser.add_argument('--file', '-f', help='恢复时指定的备份文件名或序号')
    
    args = parser.parse_args()
    
    if args.command == 'create':
        create_backup()
    elif args.command == 'list':
        show_backups()
    elif args.command == 'restore':
        if not args.file:
            show_backups()
            print("\n请使用 --file 指定要恢复的备份（文件名或序号）")
            print("示例: python backup_database.py restore --file 1")
            print("      python backup_database.py restore --file testmaster_20240322_120000.db")
        else:
            restore_backup(args.file)
    elif args.command == 'auto':
        auto_backup()


if __name__ == '__main__':
    main()
