# TestMaster Project Memory

## 项目架构 (更新 2026-04-11 最终)
- **单后端架构**: FastAPI(5001) 统一入口，纯 FastAPI，无 Flask 依赖
- **前端**: Vue + Vite，所有代理指向 5001
- **数据库**: 
  - 主数据库: SQLite(`instance/testmaster.db`)，FastAPI async SQLAlchemy
  - AutoTest数据库: SQLite(`instance/auto_test.db`)，独立 async SQLAlchemy
- **旧代码已完全删除**: `backend/` 和 `auto_test_platform/` 目录已删除
- **数据目录**: `fastapi_backend/autotest_data/` 存放 allure-results/reports/temp 等

## 迁移进度 (2026-04-11 全部完成)
### Phase A: Flask 独有模块 → FastAPI ✅
- ✅ Community/LearningPaths/Skills/Exam/Exercises/AITutor/Backup

### Phase B: AutoTest 原生迁移 ✅
- ✅ 8个模型 (fastapi_backend/models/autotest.py)
- ✅ 完整 Schema (fastapi_backend/schemas/autotest.py)
- ✅ 独立数据库 (fastapi_backend/core/autotest_database.py)
- ✅ 5个路由 (groups/cases/environments/scenarios/execution)
- ✅ 5个服务层 (execution/scenario_runner/scheduler/pytest_engine/email_notifier)
- ✅ 设置模块 (fastapi_backend/core/autotest_settings.py)
- ✅ 变量解析 (fastapi_backend/utils/parser.py)

### Phase C: 服务层完全迁移 ✅
- ✅ autotest_scenario_runner.py - 场景执行引擎
- ✅ autotest_scheduler.py - APScheduler 定时任务
- ✅ autotest_pytest_engine.py - Pytest 数据驱动
- ✅ autotest_email_notifier.py - 邮件通知
- ✅ autotest_execution.py - 用例执行
- ✅ autotest_settings.py - 配置管理

### Phase D: 旧代码删除 ✅
- ✅ backend/ 目录已删除
- ✅ auto_test_platform/ 目录已删除
- ✅ 所有 `from auto_test_platform` 引用已替换为 `from fastapi_backend`
- ✅ 数据库路径从 `auto_test_platform/auto_test.db` 迁至 `instance/auto_test.db`
- ✅ 数据目录从 `auto_test_platform/` 迁至 `fastapi_backend/autotest_data/`

### Phase E: 路由对齐与清理 (2026-04-11) ✅
- ✅ BASE_URL 端口修复 5002→5001 (autotest_settings.py)
- ✅ 后端补全5个缺失路由: send/tasks/{id}/tasks/{id}/cancel/scheduler/toggle/reports/{id}
- ✅ 前端路由修复: interface-test/environments→auto-test/environments, interface-test/send→auto-test/send, scenarios/history→history
- ✅ 根目录53个临时.py脚本已清理
- ✅ scripts/ 目录旧路径引用已更新
- ✅ 场景执行支持 task_store（内存任务状态存储，替代 Celery）
- ✅ 调度器支持 toggle_task_status（启用/暂停切换）
- ✅ 全部181个路由验证通过

### Phase F: 前端路由对齐 & Admin 后端补全 (2026-04-12) ✅
- ✅ 前端 AutoTest/InterfaceTest/Interview 模块路由修复
- ✅ 前端 Login 路由修复 (/login → /api/v1/auth/login)
- ✅ 旧版 Admin Vue 组件替换 Mock 为真实 API (Users/Exercises/LearningPaths)
- ✅ Settings.vue 已使用统一 request 客户端
- ✅ admin_manage.py 补全: login/info/backups/audit-logs/system-metrics/learning-paths兼容路径
- ✅ admin_manage.py 修正: get_password_hash → AuthService.hash_password
- ✅ 所有47+个前端 API 调用与后端路由完全对齐

## 关键架构决策
- AutoTest 使用独立数据库（auto_test.db）而非主数据库（testmaster.db）
- AutoTest 模型使用独立 Base（AutoTestBase），避免与主数据库模型冲突
- Schema 使用 Any 类型代替严格类型，兼容脏数据
- 路由返回字典而非严格 response_model，避免数据验证错误
- 数据库文件统一放在 `instance/` 目录下
- 临时文件统一放在 `fastapi_backend/autotest_data/` 下

## 用户偏好
- 称呼：亚哥
- 语言：中文

## 关键技术注意
- FastAPI 路由用 `fastapi_backend.deps.auth` 导入认证依赖
- AutoTest 数据库: `fastapi_backend.core.autotest_database.get_autotest_db`
- AutoTest 异步会话: `fastapi_backend.core.autotest_database.async_session`
- 主数据库: `fastapi_backend.core.database.get_db`
- AutoTest 设置: `fastapi_backend.core.autotest_settings.get_settings()`
- Exam 模型在 `fastapi_backend/models/models.py`
- AutoTest 模型在 `fastapi_backend/models/autotest.py`
- 密码哈希用 `AuthService.hash_password()` (在 services/auth_service.py)
- 不存在 `core/security.py`，密码操作统一用 AuthService
- Admin 路由分两个文件: admin.py(面试题管理) + admin_manage.py(其他管理)，共享 prefix /api/v1/admin
