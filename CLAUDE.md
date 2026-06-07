# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

TestMaster 是基于 FastAPI + Vue 3 的全栈智能测试管理平台，采用商业许可协议。

## 常用命令

### 后端开发
```bash
# 安装依赖
pip install -r requirements.txt

# 启动后端（开发模式，自动重载）
cd fastapi_backend && uvicorn main:app --host 0.0.0.0 --port 5001 --reload

# 运行后端测试
pytest fastapi_backend/tests -q

# 代码检查（使用 ruff）
ruff check fastapi_backend/
ruff format fastapi_backend/
```

### 前端开发
```bash
cd frontend
npm install
npm run dev          # 启动开发服务器 (http://localhost:5173)
npm run lint         # ESLint 检查
npm run build        # 构建生产版本
```

### Docker 部署
```bash
# 一键启动所有服务
docker compose up -d

# 查看服务状态
docker compose ps

# 查看日志
docker compose logs -f backend

# 重新构建并启动
docker compose up -d --build
```

## 架构概览

### 后端 (fastapi_backend/)
- **main.py**: FastAPI 应用入口，自动发现并注册路由
- **routers/**: 40+ API 路由模块，分为以下组：
  - `admin_*`: 管理后台接口
  - `autotest_*`: 自动化测试模块（核心功能）
  - 学习、AI、社区等独立路由
- **models/**: SQLAlchemy 数据模型
- **services/**: 业务逻辑层
- **schemas/**: Pydantic 请求/响应模型
- **core/**: 配置、数据库连接、异常处理
- **deps/**: 依赖注入（认证等）

### 前端 (frontend/)
- Vue 3 + Vite + Element Plus
- 状态管理: Pinia
- 代码编辑器: CodeMirror
- 数据可视化: ECharts

### 核心功能模块
- AI 导师（智能问答）
- 学习路径 + 练习/考试系统
- 自动化测试（接口测试编排执行）
- 面试模拟
- 代码沙盒
- 社区论坛

## 关键配置

### 环境变量 (.env)
- `SECRET_KEY`: JWT 签名密钥（必填）
- `ADMIN_PASSWORD`: 管理员密码（必填）
- `DATABASE_URL`: 数据库连接（默认 SQLite，生产用 PostgreSQL）
- `CORS_ORIGINS`: 跨域白名单（必填）
- `AI_API_KEY`: AI 功能密钥（可选）

### 代码规范 (ruff.toml)
- 行长度限制: 120 字符
- 忽略规则: E402（模块级导入位置）、E721/E722（类型比较）、F821（未定义名称）

## 开发注意事项

1. **路由自动注册**: `core/router_registry.py` 自动发现 routers/ 下的模块，无需手动注册
2. **数据库迁移**: 使用 Alembic，开发环境可设置 `AUTO_CREATE_TABLES_ON_STARTUP=true` 自动建表
3. **异步优先**: 后端全面使用 async/await，数据库操作使用 aiosqlite/asyncpg
4. **错误处理**: 统一的 BusinessException 和 ErrorResponse 格式
5. **AutoTest 模块**: 拥有独立数据库和调度器，初始化失败不影响主服务
