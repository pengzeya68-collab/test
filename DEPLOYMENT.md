# TestMaster 部署指南 & 踩坑记录

> 适用环境: Linux (Ubuntu/Debian/Rocky Linux)，Docker + docker-compose

---

## 一、快速部署（新服务器）

```bash
# 1. 安装 Docker
curl -fsSL https://get.docker.com | bash -s docker
sudo systemctl enable docker && sudo systemctl start docker

# 2. 克隆代码
git clone <你的仓库地址> /root/TestMaster
cd /root/TestMaster

# 3. 配置环境变量（参考 .env.example）
cp .env.example .env
# 编辑 .env 填入你的密钥...

# 4. 一键部署
chmod +x deploy.sh
./deploy.sh
```

---

## 二、更新部署（已有服务器）

### 方法 A: 一键（推荐）
```bash
cd /root/TestMaster
git pull                          # 拉取最新代码
./deploy.sh                       # 构建前端 + 重建后端 + 重启
```

### 方法 B: 只更新前端（不改后端代码时）
```bash
cd /root/TestMaster/frontend
npm install && npx vite build     # 构建前端
cd /root/TestMaster
docker compose restart nginx      # 重启 Nginx 生效
```

### 方法 C: 只更新后端（不改前端时）
```bash
cd /root/TestMaster
docker compose up -d --build      # 重建镜像并重启
```

---

## 三、架构说明

```
┌──────────────────────────────────────────────────┐
│  Nginx (端口 80)                                  │
│  ├── /api/* → 反向代理到 backend:5001              │
│  └── /* → 静态文件 /usr/share/nginx/html           │
├──────────────────────────────────────────────────┤
│  Backend (FastAPI, 端口 5001)                     │
├──────────────────────────────────────────────────┤
│  Celery Worker (异步任务)                         │
├──────────────────────────────────────────────────┤
│  Redis (消息队列 + 缓存)                          │
└──────────────────────────────────────────────────┘
```

### 数据持久化
- SQLite 数据库: `./instance/` → `/app/instance/`
- 测试报告: `./fastapi_backend/autotest_data/` → `/app/fastapi_backend/autotest_data/`

---

## 四、踩坑全记录（所有踩过的坑）

> ⚠️ 换服务器前必看！以下每个坑都可能导致部署失败或功能异常。

### 坑1: 后端代码改了，容器不生效

**症状**: 修改了 `fastapi_backend/` 下代码，`docker restart testmaster-backend` 后改动不生效。

**原因**: 旧版 `docker-compose.yml` 的 backend 容器没有挂载源码目录。代码在 Dockerfile 构建时复制进镜像，restart 不会重新构建。

**修复**: 
```yaml
# docker-compose.yml → backend volumes 部分加上：
volumes:
  - ./fastapi_backend:/app/fastapi_backend          # 源码热挂载
  - ./requirements.txt:/app/requirements.txt        # 依赖更新
```

**教训**: 
- 改了 Python 代码 → **不需要重建镜像**，只需 `docker compose restart backend`
- 改了 `requirements.txt` → 需要重建: `docker compose up -d --build`
- 建议始终保留源码 volume mount，开发效率提升 10 倍

### 坑2: Nginx 缓存 JS/CSS 一年

**症状**: 前端更新后部署到服务器，用户刷新浏览器看不到新功能。

**原因**: nginx.conf 中静态资源设置了 `expires 1y` 和 `Cache-Control: public, immutable`

**修复**: 
```nginx
# nginx.conf
location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
    expires 0;                                                      # 禁用缓存
    add_header Cache-Control "no-cache, must-revalidate, proxy-revalidate";
}
```

**教训**: 
- 开发阶段**永远不要**设置 `expires 1y`，否则用户看到的是旧版本
- 部署后如果用户还是看不到更新，让他按 `Ctrl+Shift+R` 强制刷新

### 坑3: 前端部署传错目录

**症状**: 上传了 dist 但页面没变化。

**原因**: Nginx 容器挂载的是 `/root/TestMaster/frontend/dist`，但脚本传到了 `/opt/testmaster/dist`

**修复**: 必须确认挂载点: `docker inspect testmaster-nginx --format='{{range .Mounts}}{{.Source}} {{.Destination}}{{"\n"}}{{end}}'`

**教训**: 
- 部署前先查 `docker inspect` 确认挂载路径
- 服务器上的 `deploy.sh` 应包含此验证步骤

### 坑4: 服务器积累大量旧构建文件

**症状**: `assets/` 目录下有几十个不同版本的 `index-*.js`、`JmeterAssistant-*.js` 等冗余文件。

**原因**: 每次部署只上传新增文件，不清除旧的。Vite 每次构建生成不同哈希文件名，旧文件永不删除。

**修复**: 部署前先清空:
```bash
rm -rf /root/TestMaster/frontend/dist/*
```

**教训**: 
- 部署脚本必须先 `rm -rf` 再上传

### 坑5: 后端 API 参数校验过于严格

**症状**: `GET /api/auto-test/cases?page_size=200` 返回 422

**原因**: 后端 `page_size` 限制 `le=100`，前端传 200 超出范围

**修复**: 放宽限制: `page_size: int = Query(20, ge=1, le=1000)`

### 坑6: 前端 API 响应字段名不匹配

**症状**: 接口返回数据但页面空白/功能无反应。

**原因**: 后端返回 `{items: [...]}` 但前端读 `res.cases`；后端返回纯数组但前端读 `res.data`。

**修复**: 前端做兼容处理:
```javascript
const data = Array.isArray(res) ? res : (res.items || res.data || [])
```

### 坑7: SQLite 并发写入问题

**现象**: 偶尔出现 `database is locked` 错误。

**原因**: SQLite 不支持高并发写入。多个 worker 或高并发请求同时写数据库。

**解决方案** (二选一):
- 单worker运行（当前方案）: `CMD ["uvicorn", "fastapi_backend.main:app", "--host", "0.0.0.0", "--port", "5001"]`
- 生产环境: 迁移到 PostgreSQL

### 坑8: Docker 网络问题

**现象**: Nginx 无法代理到 backend，返回 502。

**原因**: Docker 容器间的 DNS 解析问题。Nginx 中 `proxy_pass http://backend:5001;` 需要 resolver。

**修复**: nginx.conf 中:
```nginx
location /api {
    resolver 127.0.0.11 valid=10s ipv6=off;
    set $backend_upstream "backend:5001";
    proxy_pass http://$backend_upstream;
}
```

### 坑9: `.env` 文件缺失

**现象**: 后端启动报错，缺少密钥或配置。

**原因**: docker-compose.yml 引用 `env_file: .env`，但 `.env` 不在仓库中。

**教训**: 
- 创建 `.env.example` 模板并提交到仓库
- 部署文档中明确要求先 `cp .env.example .env`

### 坑10: 两个 requirements.txt 不同步导致依赖缺失

**症状**: 本地开发正常，部署后后端启动报 `ModuleNotFoundError: No module named 'docx'`。

**原因**: 项目中存在两个 requirements.txt：
- `/requirements.txt`（根目录）— **Dockerfile 使用这个**
- `/fastapi_backend/requirements.txt`（子目录）— 开发时用这个

Dockerfile 中 `COPY requirements.txt .` 只复制根目录的文件。如果只在 `fastapi_backend/requirements.txt` 中添加了新依赖，Docker 构建时不会安装。

**修复**:
```bash
# 确保两个文件同步，或修改 Dockerfile 指向正确路径
# 方案A（推荐）: 修改 Dockerfile
COPY fastapi_backend/requirements.txt .
# 方案B: 每次添加依赖时同步更新两个文件
```

**教训**:
- 添加 Python 依赖时，**必须同时更新根目录 `requirements.txt`**
- 建议只保留一个 requirements.txt，避免维护两份
- 部署前执行 `diff requirements.txt fastapi_backend/requirements.txt` 检查一致性

### 坑11: Docker 容器名冲突导致重建失败

**症状**: `docker compose up -d --force-recreate` 报错 `Conflict. The container name "/testmaster-celery" is already in use`。

**原因**: Docker 在 recreate 过程中，旧容器未完全删除，新容器尝试使用相同名称。

**修复**:
```bash
# 先强制删除旧容器再重建
docker rm -f testmaster-celery testmaster-backend testmaster-nginx
docker compose up -d
```

**教训**:
- 遇到容器名冲突，先 `docker rm -f` 清理再启动
- 不要依赖 `--force-recreate`，它不一定能处理所有冲突场景

### 坑12: SSH 执行长时间构建命令超时卡死

**症状**: 通过 `_ssh_runner.py` 执行 `docker compose build` 时，SSH 连接卡住无响应，本地终端假死。

**原因**: `_ssh_runner.py` 使用 `stdout.read()` 同步阻塞读取，构建 matplotlib/numpy 等大型包耗时 5-10 分钟，SSH 通道超时断开，`read()` 永远不会返回。

**修复**:
```bash
# 方案A: 后台执行 + 日志轮询（推荐）
py _ssh_runner.py "cd /root/TestMaster && nohup docker compose build backend celery-worker > /tmp/build.log 2>&1 & echo PID=\$!"
# 等待一段时间后检查
py _ssh_runner.py "tail -20 /tmp/build.log"
py _ssh_runner.py "ps aux | grep 'docker compose build' | grep -v grep | wc -l"  # 0表示构建完成

# 方案B: 增大 SSH 超时时间
# 在 _ssh_runner.py 中设置 exec_command(cmd, timeout=600)
```

**教训**:
- **永远不要**通过 SSH 同步执行耗时超过 2 分钟的命令
- 长任务用 `nohup cmd > /tmp/log 2>&1 &` 后台执行，再轮询日志
- `_ssh_runner.py` 的 `exec_command` 应设置合理超时（如 300 秒）

### 坑13: Docker 构建缓存导致依赖未更新

**症状**: 更新了 `requirements.txt` 添加了新依赖，`docker compose build` 显示 `CACHED`，新依赖未安装。

**原因**: Docker 的层缓存机制：如果 `COPY requirements.txt .` 这一步的文件哈希没变（或 Docker 使用了旧缓存），`RUN pip install` 也会使用缓存。

**修复**:
```bash
# 方案A: 强制无缓存构建
docker compose build --no-cache backend celery-worker

# 方案B: 确保服务器上的 requirements.txt 是最新的
cd /root/TestMaster && git pull
docker compose build backend celery-worker
```

**教训**:
- 更新依赖后，先 `git pull` 确保服务器代码最新
- 如果 `docker compose build` 显示 `CACHED` 但你改了 requirements.txt，用 `--no-cache`
- 可以在 Dockerfile 中加 `ARG CACHEBUST=1` 打破缓存

### 坑14: 服务器项目路径不确定

**症状**: 执行 `cd /root/testmaster && ...` 报 `No such file or directory`。

**原因**: 不同部署环境下项目路径可能不同（如 `/root/TestMaster` vs `/root/testmaster`）。

**修复**:
```bash
# 先查找项目位置
find / -name 'docker-compose.yml' -type f 2>/dev/null | head -5
# 或
ls -la /root/ | grep -i test
```

**教训**:
- 部署前确认项目实际路径
- 建议在 `deploy.sh` 中使用环境变量 `PROJECT_DIR=/root/TestMaster`

---

## 五、服务器迁移清单

换服务器时按此清单操作，避免遗漏：

```bash
# 1. 安装 Docker
curl -fsSL https://get.docker.com | bash

# 2. 克隆代码
git clone <仓库> /root/TestMaster
cd /root/TestMaster

# 3. 配置环境
cp .env.example .env
# 编辑 .env 填入: SECRET_KEY, JWT_SECRET_KEY, 邮件配置等

# 4. 迁移数据（旧服务器）
tar -czf instance_backup.tar.gz instance/
tar -czf autotest_data_backup.tar.gz fastapi_backend/autotest_data/
scp instance_backup.tar.gz autotest_data_backup.tar.gz 新服务器:/root/TestMaster/

# 5. 恢复数据（新服务器）
cd /root/TestMaster
tar -xzf instance_backup.tar.gz
tar -xzf autotest_data_backup.tar.gz

# 6. 一键部署
chmod +x deploy.sh
./deploy.sh

# 7. 验证
curl http://localhost/api/health                # 应返回 200
curl http://localhost/api/auto-test/groups      # 应返回分组列表
```

---

## 六、常用运维命令

```bash
# 查看日志
docker logs testmaster-backend --tail 100 -f    # 后端日志（实时）
docker logs testmaster-nginx --tail 50          # Nginx 日志
docker logs testmaster-celery --tail 50         # Celery 日志

# 重启服务
docker compose restart backend                  # 只重启后端（代码改后）
docker compose restart nginx                    # 只重启 Nginx（前端改后）
docker compose up -d --build                    # 重建并重启全部

# 进入容器
docker exec -it testmaster-backend /bin/bash

# 查看挂载
docker inspect testmaster-backend --format='{{range .Mounts}}{{.Source}} → {{.Destination}}{{"\n"}}{{end}}'
docker inspect testmaster-nginx --format='{{range .Mounts}}{{.Source}} → {{.Destination}}{{"\n"}}{{end}}'

# 健康检查
curl http://localhost/api/health
```
