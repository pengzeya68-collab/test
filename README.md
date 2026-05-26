# TestMaster - 智能测试管理平台

基于 FastAPI + Vue 3 的全栈智能测试管理平台。

## 项目结构

```
TestMaster/
├── fastapi_backend/          # FastAPI 后端
├── frontend/                 # Vue 3 主前端（端口 5173）
├── workspace/                # React 辅助前端（端口 5174）
├── start_backend.bat         # 启动后端
├── start_frontend.bat        # 启动主前端
├── start_workspace.bat       # 启动辅助前端
├── test_backend.bat          # 运行后端测试
└── requirements.txt          # Python 依赖
```

## 快速开始

### 1. 环境准备

- Python >= 3.10
- Node.js >= 18
- （可选）Redis（用于 Celery 任务队列）

### 2. 配置环境变量

复制 `.env.example` 为 `.env`：

```bash
cp .env.example .env
```

编辑 `.env` 中的数据库、AI API Key 等配置。

### 3. 安装后端依赖

```bash
pip install -r requirements.txt
```

### 4. 启动后端

```bash
start_backend.bat
```

或手动：

```bash
cd fastapi_backend
python -m uvicorn main:app --host 0.0.0.0 --port 5001 --reload
```

后端默认运行在 http://localhost:5001。

### 5. 启动主前端

```bash
cd frontend
npm install
npm run dev
```

主前端运行在 http://localhost:5173。

### 6. 启动辅助前端（可选）

```bash
cd workspace
npm install
npm run dev
```

辅助前端运行在 http://localhost:5174。

## 测试

### 后端测试

```bash
test_backend.bat
```

或手动：

```bash
pytest fastapi_backend/tests -q
```

### 前端代码检查

```bash
cd frontend
npm run lint
```

## 数据库

- 开发环境可使用 SQLite（默认）
- 生产环境建议使用 PostgreSQL/MySQL
- 数据库迁移使用 Alembic

## 环境变量说明

| 变量 | 说明 | 默认值 |
|------|------|--------|
| DATABASE_URL | 数据库连接 | sqlite+aiosqlite:///./instance/testmaster.db |
| SECRET_KEY | JWT 密钥 | 必填 |
| CORS_ORIGINS | 允许跨域域名 | http://localhost:5173 |
| AI_API_KEY | OpenAI API Key | 必填 |
| CELERY_BROKER_URL | Celery Broker | redis://localhost:6379/0 |

## 技术栈

- 后端：FastAPI, SQLAlchemy, Alembic, Celery
- 主前端：Vue 3, Vite, Element Plus, Pinia
- 辅助前端：React, Vite

## 开发说明

- 后端 `.env` 放在项目根目录
- 前端开发代理已配置在 `vite.config.js` 中
- 测试环境设置 `ENVIRONMENT=testing` 可避免启动副作用
