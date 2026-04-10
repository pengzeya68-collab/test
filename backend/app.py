import logging
import os
import sys
import shutil
from datetime import datetime
from datetime import timedelta
import pytz
from flask import Flask
from flask import send_from_directory
from flask_cors import CORS
from .extensions import db, jwt, migrate, limiter
from backend.config import config

# 导入 APScheduler 定时任务调度
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

# 配置日志 - 让所有日志都输出到控制台
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


def get_env_flag(name, default=False):
    """Parse boolean-like environment variables in a predictable way."""
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {'1', 'true', 'yes', 'on'}

# 确保工作目录正确
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.getcwd() != project_root:
    os.chdir(project_root)
    print(f"[INFO] Working directory set to: {project_root}")

# 设置时区为东八区（Asia/Shanghai）
os.environ['TZ'] = 'Asia/Shanghai'
try:
    import time
    time.tzset()
except:
    # Windows 不支持 time.tzset()，忽略
    pass

# 启动时自动备份数据库
def auto_backup_on_start():
    """应用启动时自动备份数据库"""
    try:
        # 获取项目根目录
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        scripts_dir = os.path.join(project_root, 'scripts')

        # 添加 scripts 目录到路径
        if scripts_dir not in sys.path:
            sys.path.insert(0, scripts_dir)

        # 导入备份模块
        from backup_database import auto_backup

        print("\n" + "=" * 50)
        print("[Auto Backup] Running automatic backup on startup...")
        print("=" * 50)

        success = auto_backup()

        print("=" * 50)
        if success:
            print("[OK] Auto backup completed")
        else:
            print("[WARN] Auto backup failed or database not found")
        print("=" * 50 + "\n")

    except Exception as e:
        print(f"[WARN] Auto backup error: {e}")
        print("      App will continue starting...\n")

# 执行自动备份
def create_app():
    app = Flask(__name__)
    flask_env = os.environ.get('FLASK_ENV', 'development')
    config_class = config.get(flask_env, config['default'])
    is_celery_worker = any('celery' in arg.lower() for arg in sys.argv)
    
    # Configuration
    # 密钥首先从环境变量读取，其次从 .env 文件读取
    secret_key = os.environ.get('SECRET_KEY')
    jwt_secret_key = os.environ.get('JWT_SECRET_KEY')
    
    # 如果环境变量未设置，尝试从 .env 文件读取
    if not secret_key or not jwt_secret_key:
        try:
            env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
            if os.path.exists(env_path):
                with open(env_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            key = key.strip()
                            value = value.strip().strip('"\'')
                            if key == 'SECRET_KEY' and not secret_key:
                                secret_key = value
                            elif key == 'JWT_SECRET_KEY' and not jwt_secret_key:
                                jwt_secret_key = value
        except Exception as e:
            print(f"Warning: Failed to read .env file: {e}")
    
    # 最终检查
    if not secret_key:
        raise ValueError(
            "SECRET_KEY is required. Please set it via:\n"
            "  1. Environment variable: $env:SECRET_KEY='your-key'\n"
            "  2. Or create .env file (see .env.example)\n"
            "  3. See STARTUP_GUIDE.md for details"
        )
    if not jwt_secret_key:
        raise ValueError(
            "JWT_SECRET_KEY is required. Please set it via:\n"
            "  1. Environment variable: $env:JWT_SECRET_KEY='your-key'\n"
            "  2. Or create .env file (see .env.example)\n"
            "  3. See STARTUP_GUIDE.md for details"
        )
    
    app.config['SECRET_KEY'] = secret_key
    # SQLite 默认存放到 instance 目录（Flask 标准惯例）
    instance_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance')
    os.makedirs(instance_path, exist_ok=True)
    db_path = os.path.join(instance_path, 'testmaster.db')
    # 使用绝对路径
    db_path = os.path.abspath(db_path)
    # 转换为正斜杠（SQLite 在 Windows 上也支持）
    db_path = db_path.replace('\\', '/')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', f'sqlite:///{db_path}')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    # 增加 SQLite 连接超时，减少 "database is locked" 死锁概率
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'connect_args': {'timeout': 15}}
    app.config['JWT_SECRET_KEY'] = jwt_secret_key
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
    # 完全禁用速率限制 - 本地开发调试不需要
    app.config['RATELIMIT_ENABLED'] = get_env_flag('RATELIMIT_ENABLED', flask_env != 'development')
    
    # Debug mode
    app.debug = config_class.DEBUG
    
    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    limiter.init_app(app)

    # Get CORS origins from config
    cors_origins = config_class.CORS_ORIGINS
    CORS(app, origins=cors_origins)

    if get_env_flag('AUTO_BACKUP_ON_STARTUP', False) and not is_celery_worker:
        auto_backup_on_start()
    
    # Import and register blueprints
    print("Importing blueprints...")
    from .api.auth import auth_bp
    from .api.learning_paths import learning_bp
    from .api.exercises import exercises_bp
    from .api.code_executor import code_bp
    from .api.skills import skills_bp
    from .api.ai_tutor import ai_bp
    from .api.community import community_bp
    from .api.exam import exam_bp
    from .api.interview import interview_bp
    from .api.interface_test import interface_test_bp
    from .api.backup import backup_bp
    from .api.admin import admin_bp
    from .api.auto_test import auto_test_bp

    app.register_blueprint(auth_bp, url_prefix='/api')
    app.register_blueprint(learning_bp, url_prefix='/api')
    app.register_blueprint(exercises_bp, url_prefix='/api')
    app.register_blueprint(code_bp, url_prefix='/api')
    app.register_blueprint(skills_bp, url_prefix='/api')
    app.register_blueprint(ai_bp, url_prefix='/api')
    app.register_blueprint(community_bp, url_prefix='/api')
    app.register_blueprint(exam_bp, url_prefix='/api')
    app.register_blueprint(interview_bp, url_prefix='/api')
    app.register_blueprint(interface_test_bp, url_prefix='/api')
    app.register_blueprint(backup_bp, url_prefix='/api')
    app.register_blueprint(admin_bp, url_prefix='/api')
    app.register_blueprint(auto_test_bp, url_prefix='/api')
    
    print("All blueprints registered!")

    # Add root route
    @app.route('/')
    def home():
        return {
            'message': 'TestMaster API is running!',
            'endpoints': [
                'POST /api/register',
                'POST /api/login',
                'GET /api/learning-paths',
                'GET /api/exercises'
            ]
        }

    # ========== 暴露 Allure 报告静态文件 ==========
    # 让 /reports/{report_id}/index.html 可以直接访问，加载所有 css/js 资源
    REPORTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'reports')

    @app.route('/reports/<path:report_path>')
    def serve_allure_report(report_path):
        return send_from_directory(REPORTS_DIR, report_path)

    # Create tables and initialize scheduler
    with app.app_context():
        from .models import models

        if get_env_flag('AUTO_CREATE_TABLES_ON_STARTUP', False):
            db.create_all()
            print("[Startup] AUTO_CREATE_TABLES_ON_STARTUP enabled, database tables ensured.")

        # ========== 初始化 APScheduler 定时任务调度 ==========
        # 【致命修复】绝对禁止 Celery worker 进程启动 scheduler！
        # 检测是否是 Celery worker 进程，如果是，跳过 scheduler 初始化
        is_celery_worker = any('celery' in arg.lower() for arg in sys.argv)
        if is_celery_worker:
            print("[Scheduler] ⚠️  当前是 Celery worker 进程，跳过 scheduler 初始化（防止裂变）")
        # 仅在主线程（Flask Web 进程）初始化一次
        elif not app.debug or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
            def scheduled_job_wrapper(task_id):
                """定时任务包装器：在应用上下文中执行"""
                with app.app_context():
                    from backend.models.models import ScheduledTask
                    from backend.celery_tasks import run_scenario_async

                    task = ScheduledTask.query.get(task_id)
                    if not task or not task.is_active:
                        print(f"[Scheduler] 任务 {task_id} 不存在或已禁用，跳过")
                        return

                    # 更新最后运行时间 - 统一使用东八区北京时间
                    task.last_run_at = datetime.now(pytz.timezone('Asia/Shanghai')).replace(tzinfo=None)
                    db.session.commit()

                    # 触发 Celery 异步执行，传入 webhook_url（定时任务配置优先）
                    print(f"[Scheduler] 触发定时任务: {task.name} (ID: {task_id}), 场景: {task.scenario_id}")
                    # 打包为单个字典参数传递，彻底杜绝参数位置错位
                    import logging
                    logger = logging.getLogger(__name__)
                    task_data = {
                        'scenario_id': task.scenario_id,
                        'user_id': task.user_id,
                        'env_id': task.env_id,
                        'webhook_url': str(task.webhook_url).strip() if (task.webhook_url and str(task.webhook_url).strip()) else None
                    }
                    logger.info(f"[Scheduler] 准备推送任务到 Celery，task_data = {task_data}")
                    print(f"[Scheduler DEBUG] 推送字典: {task_data}")
                    run_scenario_async.delay(task_data)

            # 创建后台调度器
            scheduler = BackgroundScheduler(timezone='Asia/Shanghai')

            # 从数据库加载所有启用的任务
            from backend.models.models import ScheduledTask
            active_tasks = ScheduledTask.query.filter_by(is_active=True).all()

            for task in active_tasks:
                try:
                    # 解析 cron 表达式并添加任务
                    trigger = CronTrigger.from_crontab(task.cron_expression, timezone='Asia/Shanghai')
                    job_id = f'task_{task.id}'
                    scheduler.add_job(
                        scheduled_job_wrapper,
                        trigger=trigger,
                        args=[task.id],
                        id=job_id,
                        replace_existing=True
                    )
                    # 如果任务已被禁用（is_active=False），在引擎层挂起
                    if not task.is_active:
                        scheduler.pause_job(job_id)
                        print(f"[Scheduler] 已加载并挂起: {task.name} (ID: {task.id})")
                    else:
                        print(f"[Scheduler] 已加载并启用: {task.name} (ID: {task.id}), cron: {task.cron_expression}")
                except Exception as e:
                    print(f"[Scheduler] 加载任务 {task.id} 失败: {e}")

            # 启动调度器
            scheduler.start()
            print(f"[Scheduler] 定时调度器启动完成，共加载 {len(active_tasks)} 个用户定时任务")

            # ========== 新增系统内置任务：每天凌晨3点自动清理7天前的报告 ==========
            from sqlalchemy import text

            SHA_TZ = pytz.timezone('Asia/Shanghai')

            def auto_cleanup_reports():
                """系统自动清理：删除创建时间超过7天的报告，节省硬盘空间"""
                with app.app_context():
                    from backend.models.models import InterfaceTestReport
                    from backend.extensions import db

                    print("\n[AutoCleanup] 开始执行自动清理任务...")

                    # 计算7天前的时间点
                    cutoff = datetime.now(SHA_TZ).replace(tzinfo=None) - timedelta(days=7)
                    print(f"[AutoCleanup] 清理 {cutoff} 之前创建的报告...")

                    # 查询超过7天的报告
                    old_reports = InterfaceTestReport.query\
                        .filter(InterfaceTestReport.executed_at < cutoff)\
                        .all()

                    if not old_reports:
                        print("[AutoCleanup] 没有需要清理的旧报告，完成\n")
                        return

                    deleted_count = 0
                    deleted_size = 0
                    for report in old_reports:
                        try:
                            # 1. 先物理删除硬盘上的 Allure 报告文件夹
                            report_output_dir = os.path.join(
                                os.path.dirname(os.path.abspath(__file__)),
                                'reports',
                                str(report.id)
                            )
                            if os.path.exists(report_output_dir):
                                # 获取文件夹大小
                                total_size = sum(
                                    os.path.getsize(os.path.join(dirpath, filename))
                                    for dirpath, _, filenames in os.walk(report_output_dir)
                                    for filename in filenames
                                )
                                deleted_size += total_size
                                shutil.rmtree(report_output_dir)
                                print(f"[AutoCleanup] 已删除物理文件: {report_output_dir} ({total_size / 1024 / 1024:.2f} MB)")

                            # 2. 再删除数据库记录
                            # 先删除所有步骤结果（正确表名是复数 interface_test_report_results）
                            db.session.execute(
                                text("DELETE FROM interface_test_report_results WHERE report_id = :report_id"),
                                {"report_id": report.id}
                            )
                            db.session.delete(report)
                            deleted_count += 1

                        except Exception as e:
                            print(f"[AutoCleanup] ❌ 删除报告 {report.id} 失败: {e}")
                            continue

                    db.session.commit()
                    mb_size = deleted_size / 1024 / 1024
                    print(f"[AutoCleanup] ✅ 自动清理完成，共删除 {deleted_count} 条旧报告，节省 {mb_size:.2f} MB\n")

            # 添加到调度器：每天凌晨 3 点执行（CronTrigger 已经在顶部全局导入）
            trigger = CronTrigger.from_crontab('0 3 * * *', timezone='Asia/Shanghai')
            scheduler.add_job(
                auto_cleanup_reports,
                trigger=trigger,
                id='system_auto_cleanup_reports',
                replace_existing=True
            )
            print("[Scheduler] ✅ 系统自动清理任务已加载: 每天凌晨 3:00 清理7天前报告")

            # 将调度器保存到 app 供后续使用（添加/删除任务时）
            app.scheduler = scheduler

    return app

if __name__ == '__main__':
    app = create_app()
    print('TestMaster API starting on http://localhost:5000')
    app.run(debug=False, host='0.0.0.0', port=5000)
