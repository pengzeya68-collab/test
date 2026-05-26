# TestMaster - 智能测试管理平台

> ⚠️ **版权声明 — 请务必阅读**
>
> 本项目采用 **[AGPL-3.0](./LICENSE)** 许可证。**禁止任何人**在未遵循本协议的情况下：
> - ❌ 将本项目用于商业目的或商用产品
> - ❌ 闭源修改后重新发布
> - ❌ 将本项目作为 SaaS 服务提供给第三方而不公开源代码
> - ❌ 声称本项目为自行开发
>
> ✅ **允许**：个人学习、研究、非商业展示。
>
> 📧 如需商业授权，请联系项目作者。

基于 FastAPI + Vue 3 的全栈智能测试管理平台。

## 项目结构

```
TestMaster/
├── fastapi_backend/          # FastAPI 后端
│   ├── main.py              # 应用入口
│   ├── routers/             # API 路由（40+ 模块）
│   ├── models/              # 数据模型
│   ├── services/            # 业务逻辑
│   └── core/                # 核心配置
├── frontend/                 # Vue 3 前端
│   ├── src/                 # 源代码
│   └── dist/                # 构建产物（已包含在仓库中）
├── nginx.conf                # Nginx 前端托管配置
├── Dockerfile                # Docker 镜像构建
├── docker-compose.yml        # 服务编排（后端+Redis+Celery+Nginx）
└── requirements.txt          # Python 依赖
```

---

## 🚀 Docker 一键部署（推荐）

> **零依赖，一条命令部署到生产服务器！**

### 第1步：安装 Docker

```bash
curl -fsSL https://get.docker.com | sh
```

### 第2步：克隆项目

```bash
git clone https://github.com/pengzeya68-collab/test.git TestMaster
cd TestMaster
```

### 第3步：配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件，**必须修改**以下配置：

```bash
nano .env
```

```env
# 生产环境必改项
ENVIRONMENT=production
SECRET_KEY=随机32位以上字符串（用 openssl rand -hex 32 生成）
ADMIN_PASSWORD=你的管理员密码
ADMIN_SECRET_KEY=随机32位以上字符串
CORS_ORIGINS=http://你的服务器IP

# 其他可选配置
TESTMASTER_ENCRYPTION_KEY=随机32位字符串（用于加密敏感数据）
AI_API_KEY=你的AI密钥（如需AI功能）
AI_BASE_URL=https://api.openai.com/v1
```

### 第4步：启动服务

```bash
docker compose up -d
```

### 第5步：开放端口

服务器控制台安全组开放 **80** 和 **5001** 端口。

### 第6步：访问

| 地址 | 说明 |
|------|------|
| `http://你的IP` | 前端首页 |
| `http://你的IP/api/health` | API 健康检查 |
| `http://你的IP:5001/api/docs` | API 文档 (Swagger) |

**默认管理员**：`admin` / 你设置的密码

---

## 🖥️ 本地开发

### 环境准备

- Python >= 3.10
- Node.js >= 18
- （可选）Redis（用于 Celery 任务队列）

### 启动后端

```bash
# 安装依赖
pip install -r requirements.txt

# 复制环境变量并配置
cp .env.example .env

# 启动
cd fastapi_backend
uvicorn main:app --host 0.0.0.0 --port 5001 --reload
```

后端运行在 http://localhost:5001

### 启动前端

```bash
cd frontend
npm install
npm run dev
```

前端运行在 http://localhost:5173

---

## 🧪 测试

```bash
# 后端测试
pytest fastapi_backend/tests -q

# 前端代码检查
cd frontend && npm run lint
```

---

## 🐳 Docker 服务说明

| 服务 | 端口 | 说明 |
|------|------|------|
| Nginx | 80 | 前端托管 + API 代理 |
| Backend | 5001 | FastAPI 后端 |
| Celery Worker | - | 异步任务处理 |
| Redis | 6379 | 缓存 & 任务队列 |

### 常用命令

```bash
# 查看服务状态
docker compose ps

# 查看日志
docker compose logs -f backend

# 重启服务
docker compose restart

# 停止服务
docker compose down

# 更新代码后重新部署
git pull
docker compose up -d --build
```

---

## 📦 技术栈

| 层面 | 技术 |
|------|------|
| 后端框架 | FastAPI (异步) |
| ORM | SQLAlchemy 2.0 |
| 数据库迁移 | Alembic |
| 任务队列 | Celery + Redis |
| 前端框架 | Vue 3 + Vite |
| UI 组件 | Element Plus |
| 状态管理 | Pinia |
| 代码编辑器 | CodeMirror |
| 数据可视化 | ECharts |

---

## 🔧 环境变量说明

| 变量 | 说明 | 必填 |
|------|------|------|
| `SECRET_KEY` | JWT 签名密钥 | ✅ |
| `ADMIN_PASSWORD` | 管理员密码 | ✅ |
| `ADMIN_SECRET_KEY` | 管理员密钥 | ✅ |
| `TESTMASTER_ENCRYPTION_KEY` | 数据加密密钥 | ✅ |
| `DATABASE_URL` | 数据库连接 | - |
| `CORS_ORIGINS` | 跨域白名单 | ✅ |
| `AI_API_KEY` | AI API 密钥 | 可选 |
| `EMAIL_ENABLED` | 启用邮件 | 可选 |
| `CELERY_BROKER_URL` | 消息队列 | Docker 自动配置 |

---

## 📝 功能模块

- 🧠 **AI 导师**：智能学习问答
- 📚 **学习路径**：体系化学习内容
- ✍️ **练习系统**：在线刷题
- 📝 **考试系统**：在线考试自动评分
- 🤖 **自动化测试**：接口测试编排执行
- 💬 **面试模拟**：AI 模拟面试
- 🏆 **成就系统**：勋章积分排行榜
- 👥 **社区交流**：论坛发帖互动
- 🏗️ **代码沙盒**：安全代码执行
- 🛠️ **测试工具**：API 调试、数据工厂
