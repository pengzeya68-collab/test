# TestMaster 在线学习平台

一个功能完整的软件测试在线学习平台，包含前台学习系统和后台管理系统。

## 项目结构

```
TestMasterProject/
├── backend/                      # Flask 后端（学习平台，端口 5000）
│   ├── __init__.py
│   ├── app.py                   # 应用工厂
│   ├── config.py                # 配置
│   ├── extensions.py            # 扩展初始化
│   ├── models/                  # 数据模型
│   │   └── models.py
│   └── api/                     # API 路由模块
│       ├── auth.py              # 用户认证
│       ├── admin.py             # 后台管理
│       ├── exercises.py         # 习题管理
│       ├── learning_paths.py    # 学习路径
│       ├── interview.py         # 面试系统
│       ├── exam.py             # 考试系统
│       ├── code_executor.py     # 代码执行沙箱
│       ├── skills.py            # 技能统计
│       ├── ai_tutor.py          # AI导师
│       ├── interface_test.py    # 接口测试（旧版）
│       ├── auto_test.py         # 自动化测试入口
│       └── community.py         # 社区
├── frontend/                    # 前端（Vue 3 + Vite，端口 5173）
│   └── src/
│       ├── views/              # 页面组件
│       ├── api/                # API 调用
│       └── ...
├── auto_test_platform/          # 自动化测试模块（FastAPI，端口 5002）
│   ├── main.py                 # FastAPI 主入口
│   ├── models.py               # 数据模型
│   ├── schemas.py              # Pydantic schemas
│   ├── database.py             # 数据库连接
│   ├── routers/                # API 路由
│   │   ├── groups.py           # 分组管理
│   │   ├── cases.py            # 用例管理
│   │   ├── environments.py     # 环境管理
│   │   └── scenarios.py        # 场景管理
│   ├── services/               # 核心服务
│   │   ├── execution.py        # 断言执行
│   │   ├── pytest_engine.py     # Pytest 引擎
│   │   ├── scenario_runner.py   # 场景执行引擎
│   │   └── scheduler.py         # 定时任务调度
│   ├── allure-results/         # Allure 测试结果
│   └── reports/                # Allure HTML 报告
├── scripts/                    # 数据库初始化脚本
│   ├── init_all.py             # 完整初始化
│   ├── init_db.py              # 数据库初始化
│   └── ...
├── migrations/                 # 数据库迁移
├── instance/                   # SQLite 数据库文件
├── docs/                       # 项目文档
├── requirements.txt            # 学习平台依赖
├── auto_test_platform/requirements.txt  # 自动化测试依赖
└── README.md
```

## 技术栈

- **后端**：Python Flask + SQLAlchemy + JWT + Flask-Limiter
- **前端**：Vue 3 + TypeScript + Vite + Element Plus + ECharts
- **数据库**：SQLite（开发）/ MySQL（生产）

## 功能模块

### 前台学习
- [x] 用户注册/登录（短信验证码）
- [x] 首页展示
- [x] 学习路径浏览
- [x] 在线做题（支持代码在线执行）
- [x] 面试系统
- [x] 技能雷达图统计
- [x] 个人中心
- [ ] 社区讨论

### 后台管理
- [x] 管理员登录
- [x] 数据仪表盘（数据统计图表）
- [x] 习题管理（CRUD + 批量导入）
- [x] 学习路径管理（关联习题）
- [x] 用户管理（权限控制）
- [x] 面试题库管理
- [x] 考试管理

### 自动化测试模块（auto_test_platform）
- [x] 接口分组管理（树形结构）
- [x] 接口用例管理（CRUD + 批量导入）
- [x] 环境配置管理（base_url、全局变量）
- [x] 场景编排执行（多步骤串联、变量传递）
- [x] 数据驱动执行（CSV/Excel 导入）
- [x] 定时任务调度（APScheduler + Cron 表达式）
- [x] Allure 测试报告生成
- [x] 断言规则配置（支持新旧两种格式）

## 本地开发

### ⚠️ 重要：安全修复后的启动步骤

由于安全修复要求强制设置密钥，**首次启动前必须完成以下步骤**：

#### 步骤 1：设置环境变量

**Windows (PowerShell):**
```powershell
# 设置环境变量（每次新窗口都需要执行）
$env:SECRET_KEY="your-super-secret-key-change-this-in-production"
$env:JWT_SECRET_KEY="your-jwt-secret-key-change-this-in-production"

# 可选：AI导师功能需要
$env:OPENAI_API_KEY="your-openai-api-key"  # 可选
$env:OPENAI_BASE_URL="https://api.openai.com/v1"  # 可选
```

**Windows (CMD):**
```cmd
set SECRET_KEY=your-super-secret-key-change-this-in-production
set JWT_SECRET_KEY=your-jwt-secret-key-change-this-in-production
```

**Linux/Mac:**
```bash
export SECRET_KEY="your-super-secret-key-change-this-in-production"
export JWT_SECRET_KEY="your-jwt-secret-key-change-this-in-production"
```

**或使用 .env 文件（推荐）:**
```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，填入你的密钥
# 注意：.env 文件已添加到 .gitignore，不会被提交
```

#### 步骤 2：重新初始化数据库

由于 User 模型添加了 `phone` 字段，需要重新创建数据库：

```bash
# 删除旧数据库
rm instance/testmaster.db  # Linux/Mac
# 或: del instance\testmaster.db  # Windows

# 初始化新数据库
python scripts/init_all.py
```

#### 步骤 3：启动服务

**后端启动：**
```bash
# 确保环境变量已设置
# 进入项目目录
cd TestMasterProject

# 创建虚拟环境（可选推荐）
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或: venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 启动开发服务器
python wsgi.py
```
后端服务运行在 http://localhost:5000

**前端启动：**
```bash
cd frontend
npm install
npm run dev
```
前端服务运行在 http://localhost:5173

**自动化测试平台启动：**
```bash
# 安装依赖
pip install -r auto_test_platform/requirements.txt

# 启动服务
cd auto_test_platform
uvicorn main:app --host 0.0.0.0 --port 5002 --reload
```
自动化测试平台运行在 http://localhost:5002

### 默认账号

- **管理员**：admin / admin123
- **测试用户**：testuser / password123

## 生产部署

### 使用 Gunicorn + Nginx 部署

1. **上传代码到服务器**

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **配置环境变量**
```bash
cp .env.example .env
# 编辑 .env 修改密钥和数据库配置
```

4. **初始化数据库**
```bash
python scripts/init_all.py
```

5. **使用 Gunicorn 启动**
```bash
gunicorn --workers 4 --bind 127.0.0.1:5000 wsgi:app
```

6. **Nginx 配置**
```nginx
# 前端静态文件
location / {
    root /path/to/TestMasterProject/frontend/dist;
    try_files $uri $uri/ /index.html;
}

# 后端 API 反向代理
location /api {
    proxy_pass http://127.0.0.1:5000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
```

详细部署文档请看 [docs/deployment.md](docs/deployment.md)

## 时区

项目默认使用 **东八区（Asia/Shanghai）** 时区，日志和时间戳都会使用本地时间。

## 许可证

MIT
