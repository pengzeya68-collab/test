# TestMaster 一键部署指南

> 本指南适用于 **任何 AI 助手 (CodeBuddy/Cursor/GitHub Copilot)** 或 **人工运维**。  
> 按顺序执行，30 分钟内完成从零到上线。

---

## 项目信息

| 项 | 值 |
|----|----|
| 项目名 | TestMaster |
| 后端 | FastAPI + SQLAlchemy + Celery |
| 前端 | Vue 3 + Vite + Element Plus |
| 数据库 | SQLite（生产也用，足够了） |
| GitHub | `https://github.com/pengzeya68-collab/test` |
| 协议 | AGPL-3.0 |

---

## 第一步：本地环境确认

```bash
# 确认以下工具已安装
git --version
docker --version
node --version    # >= 18
python --version  # >= 3.10
```

**如果没有 Docker**：
```bash
curl -fsSL https://get.docker.com | sh
```

---

## 第二步：克隆项目

```bash
git clone https://github.com/pengzeya68-collab/test.git TestMaster
cd TestMaster
```

---

## 第三步：配置环境变量

```bash
cp .env.example .env
```

编辑 `.env`，**必须修改**以下项：

```env
SECRET_KEY=<用 openssl rand -hex 32 生成>
ADMIN_PASSWORD=<你的管理员密码>
ADMIN_SECRET_KEY=<用 openssl rand -hex 32 生成>
CORS_ORIGINS=http://你的服务器IP
TESTMASTER_ENCRYPTION_KEY=<用 openssl rand -hex 32 生成>
```

---

## 第四步：构建前端（如果有新前端代码）

```bash
cd frontend
npm install
# 构建时指定服务器 API 地址
set VITE_FASTAPI_BASE_URL=http://你的服务器IP:5001
npm run build
cd ..
```

构建产物在 `frontend/dist/`，已在 Git 仓库中。

---

## 第五步：推送数据库和代码到 GitHub

```bash
# 把本地数据库纳入版本控制
git add -f instance/testmaster.db

# 提交所有修改
git add -A
git commit -m "deploy: 初始部署"
git push origin main
```

> ⚠️ 如果 GitHub 推送失败（中国常见），参考"常见问题"第 2 条。

---

## 第六步：服务器拉取并启动

SSH 连接到服务器后：

```bash
cd /root/TestMaster
git pull origin main

# 如果 docker-compose.yml 更新了，服务器执行这个重建
docker compose up -d --build

# 等待启动后检查
docker compose ps
curl -s http://localhost:5001/api/health
```

---

## 第七步：开放端口

服务器安全组开放如下端口：

| 端口 | 用途 |
|------|------|
| 80 | Nginx 前端 |
| 5001 | 后端 API |

---

## 访问地址

| 地址 | 说明 |
|------|------|
| `http://你的IP` | 前台 |
| `http://你的IP/admin/login` | 后台管理 |
| `http://你的IP:5001/api/docs` | API 文档 |

---

## 🔧 常见问题速查

### 1. 管理员登录失败

```bash
# 在服务器重置 admin 密码为 admin123456
docker exec testmaster-backend pip install bcrypt==4.2.1 -q
docker exec testmaster-backend python3 -c "
import sqlite3, bcrypt
hashed = bcrypt.hashpw(b'admin123456', bcrypt.gensalt(rounds=12)).decode()
conn = sqlite3.connect('/app/instance/testmaster.db')
conn.execute('UPDATE users SET password_hash=? WHERE username=?', (hashed, 'admin'))
conn.commit()
conn.close()
print('Done')
"
```

### 2. git push 失败（代理/网络问题）

**中国用户**：需要科学上网代理。

```bash
# 设置代理
git config --global http.proxy http://127.0.0.1:10808
git config --global https.proxy http://127.0.0.1:10808

# 如果 token 过期，去 https://github.com/settings/tokens 生成新 token
git remote set-url origin https://你的token@github.com/pengzeya68-collab/test.git
git push origin main
```

### 3. 后端启动报错 / 502 Bad Gateway

```bash
# 查看日志
cd /root/TestMaster && docker compose logs backend --tail 20

# 常见原因和修复：
# a) Nginx 没重启 → docker compose restart nginx
# b) 数据库丢失 → 见下方"数据库恢复"
# c) 依赖缺失 → 见 requirements.txt 是否完整
```

### 4. 数据库丢失/数据不保存

**根因**：数据库在容器内部的 `/tmp/` 目录，重启即消失。

**已修复**：`docker-compose.yml` 已将数据库挂载到持久化目录：
```yaml
volumes:
  - ./instance:/app/instance
```

数据库文件位置：`/root/TestMaster/instance/testmaster.db`

### 5. admin 用户不存在

```bash
# 检查数据库
docker exec testmaster-backend sqlite3 /app/instance/testmaster.db \
  "SELECT username, is_admin FROM users WHERE username='admin'"

# 如果不存在，手动创建
docker exec testmaster-backend pip install bcrypt==4.2.1 -q
docker exec testmaster-backend python3 -c "
import sqlite3, bcrypt
h = bcrypt.hashpw(b'admin123456', bcrypt.gensalt(rounds=12)).decode()
conn = sqlite3.connect('/app/instance/testmaster.db')
conn.execute('INSERT INTO users (username,email,password_hash,is_admin,is_super_admin,is_active,level,score) VALUES (?,?,?,?,?,?,?,?)',
    ('admin','admin@test.com',h,1,1,1,99,99999))
conn.commit()
conn.close()
print('Admin created')
"
```

### 6. 登录返回 500 错误（DetachedInstanceError）

**已修复**：`auth_service.py` 中 `authenticate_user` 方法加了 `selectinload(User.role_obj)`。

如果遇到此错误，检查 `fastapi_backend/services/auth_service.py`：
```python
# 正确写法
stmt = select(User).where(...).options(selectinload(User.role_obj))

# 错误写法（会导致 500）
stmt = select(User).where(...)
```

### 7. 前后端 API 路径不匹配

以下文件存在前后端路径不一致，**已修复**：
- `BackupManager.vue`：下载 URL 缺少 `/v1` 前缀
- `SystemMonitor.vue`：API 路径 `/info` → `/system-info`、`/process` → `/process-info`
- `admin_system.py`：audit-logs 返回 `list` → `logs`

### 8. passlib/bcrypt 版本冲突

密码哈希使用 **bcrypt 直接 API**，不要用 passlib。`requirements.txt` 已锁定 `bcrypt==4.2.1`。

---

## 📦 Docker 架构说明

```
Nginx (:80) ──→ Frontend 静态文件 (/frontend/dist)
            ──→ API 代理 ──→ Backend (:5001) ──→ SQLite (/app/instance/testmaster.db)
                                          ──→ Redis (:6379)
                                          ──→ Celery Worker
```

**容器列表**：

| 容器 | 端口 | 用途 |
|------|------|------|
| testmaster-nginx | 80 | 前端托管 + API 反向代理 |
| testmaster-backend | 5001 | FastAPI |
| testmaster-celery | - | 异步任务 |
| testmaster-redis | 6379 | 缓存和消息队列 |

---

## 🚀 日常部署流程

```
本地改代码
    ↓
git add -A && git commit -m "更新说明"
    ↓
git push origin main
    ↓
SSH 到服务器：
  cd /root/TestMaster
  git pull origin main
  docker compose up -d
    ↓
浏览器刷新 → 看到更新 ✅
```

---

## 🔑 关键文件清单

| 文件 | 作用 | 必须正确 |
|------|------|----------|
| `requirements.txt` | Python 依赖 | 完整列表 + bcrypt==4.2.1 |
| `Dockerfile` | Docker 镜像构建 | root 运行，单 worker |
| `docker-compose.yml` | 服务编排 | 挂载 instance 目录 + 健康检查 |
| `nginx.conf` | 前端 + API 代理 | SPA try_files |
| `.env` | 环境变量 | SECRET_KEY, ADMIN_PASSWORD 等 |
| `instance/testmaster.db` | 数据库 | Git 跟踪，持久化 |
| `.github/workflows/deploy.yml` | CI/CD | GitHub Actions SSH 部署 |

---

## 🆘 终极恢复方案

如果服务器全崩了，从头来：

```bash
# 1. 确保服务器有 Docker
curl -fsSL https://get.docker.com | sh

# 2. 克隆项目
git clone https://github.com/pengzeya68-collab/test.git /root/TestMaster
cd /root/TestMaster

# 3. 配置
cp .env.example .env
nano .env  # 改 SECRET_KEY 和 ADMIN_PASSWORD

# 4. 启动
docker compose up -d

# 5. 如果登录不了，执行"常见问题 1"重置密码
```

---

> 📅 最后更新：2026-05-27  
> 📝 本指南基于实际部署踩坑经验整理
