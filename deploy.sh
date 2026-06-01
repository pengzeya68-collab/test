#!/bin/bash
set -e

echo "============================================================"
echo "  TestMaster 一键部署脚本"
echo "============================================================"

REPO_URL="${1:-https://github.com/pengzeya/TestMaster.git}"
INSTALL_DIR="${2:-/root/TestMasterProject}"

echo ""
echo "仓库地址: $REPO_URL"
echo "安装目录: $INSTALL_DIR"
echo ""

# ==================== 1. 系统依赖 ====================
echo ""
echo "====== [1/8] 安装系统依赖 ======"
if ! command -v docker &> /dev/null; then
    echo "安装 Docker..."
    curl -fsSL https://get.docker.com | sh
    systemctl enable docker
    systemctl start docker
    echo "Docker 安装完成"
else
    echo "Docker 已安装: $(docker --version)"
fi

if ! command -v docker compose &> /dev/null; then
    echo "安装 Docker Compose 插件..."
    apt-get update -qq
    apt-get install -y -qq docker-compose-plugin 2>/dev/null || {
        mkdir -p /usr/local/lib/docker/cli-plugins
        curl -SL "https://github.com/docker/compose/releases/latest/download/docker-compose-linux-x86_64" \
            -o /usr/local/lib/docker/cli-plugins/docker-compose
        chmod +x /usr/local/lib/docker/cli-plugins/docker-compose
    }
    echo "Docker Compose 安装完成"
else
    echo "Docker Compose 已安装"
fi

if ! command -v node &> /dev/null; then
    echo "安装 Node.js 20..."
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
    apt-get install -y -qq nodejs
    echo "Node.js 安装完成: $(node --version)"
else
    echo "Node.js 已安装: $(node --version)"
fi

if ! command -v git &> /dev/null; then
    apt-get update -qq && apt-get install -y -qq git
fi

# ==================== 2. 克隆代码 ====================
echo ""
echo "====== [2/8] 克隆代码 ======"
if [ -d "$INSTALL_DIR/.git" ]; then
    echo "代码已存在，拉取最新版本..."
    cd "$INSTALL_DIR"
    git fetch --all
    git reset --hard origin/main
else
    echo "克隆仓库..."
    git clone "$REPO_URL" "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi

# ==================== 3. 配置环境变量 ====================
echo ""
echo "====== [3/8] 配置环境变量 ======"
if [ ! -f .env ]; then
    cp .env.example .env
    SECRET_KEY=$(openssl rand -hex 32)
    DB_PASSWORD=$(openssl rand -hex 16)
    sed -i "s/DB_PASSWORD=testmaster2024/DB_PASSWORD=$DB_PASSWORD/" .env
    sed -i "s/SECRET_KEY=.*/SECRET_KEY=$SECRET_KEY/" .env
    sed -i "s|DATABASE_URL=.*|DATABASE_URL=postgresql+asyncpg://testmaster:$DB_PASSWORD@postgres:5432/testmaster|" .env
    echo "已生成 .env 文件（随机密码和密钥）"
else
    echo ".env 文件已存在，跳过"
fi

# ==================== 4. 生成 SSL 自签名证书 ====================
echo ""
echo "====== [4/8] 配置 SSL 证书 ======"
mkdir -p ssl
if [ ! -f ssl/cert.pem ] || [ ! -f ssl/key.pem ]; then
    echo "生成自签名 SSL 证书..."
    openssl req -x509 -nodes -days 3650 \
        -newkey rsa:2048 \
        -keyout ssl/key.pem \
        -out ssl/cert.pem \
        -subj "/CN=testmaster.local/O=TestMaster/C=CN" \
        2>/dev/null
    echo "SSL 证书已生成（自签名，浏览器会提示不安全，可替换为正式证书）"
else
    echo "SSL 证书已存在，跳过"
fi

# ==================== 5. 构建前端 ====================
echo ""
echo "====== [5/8] 构建前端 ======"
cd frontend
if [ ! -d node_modules ]; then
    echo "安装前端依赖..."
    npm install --legacy-peer-deps
fi
echo "构建前端..."
npm run build
cd ..
echo "前端构建完成"

# ==================== 6. 构建并启动 Docker 容器 ====================
echo ""
echo "====== [6/8] 构建并启动 Docker 容器 ======"
docker compose build --no-cache backend
docker compose up -d
echo "等待服务启动..."
sleep 15

# ==================== 7. 初始化数据库 ====================
echo ""
echo "====== [7/8] 初始化数据库 ======"
echo "等待 PostgreSQL 就绪..."
for i in $(seq 1 30); do
    if docker exec testmaster-postgres pg_isready -U testmaster &>/dev/null; then
        echo "PostgreSQL 已就绪"
        break
    fi
    echo "等待中... ($i/30)"
    sleep 2
done

MIGRATION_FILE="${3:-}"
if [ -n "$MIGRATION_FILE" ] && [ -f "$MIGRATION_FILE" ]; then
    echo "检测到数据迁移文件: $MIGRATION_FILE"
    echo "导入旧服务器数据..."

    if [[ "$MIGRATION_FILE" == *.gz ]]; then
        gunzip -c "$MIGRATION_FILE" | docker exec -i testmaster-postgres psql -U testmaster -d testmaster 2>&1 || echo "导入完成（部分警告可忽略）"
    else
        docker exec -i testmaster-postgres psql -U testmaster -d testmaster < "$MIGRATION_FILE" 2>&1 || echo "导入完成（部分警告可忽略）"
    fi
    echo "数据迁移完成！"

    echo "运行代码题修复..."
    docker exec testmaster-backend python -c "
import asyncio
from fastapi_backend.seed_all_data import _fix_code_exercises
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from fastapi_backend.core.config import settings
engine = create_async_engine(settings.DATABASE_URL, echo=False)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
async def fix():
    async with async_session() as session:
        await _fix_code_exercises(session)
asyncio.run(fix())
" 2>&1 || echo "代码题修复跳过"
else
    echo "未指定迁移文件，运行种子数据脚本..."
    docker exec testmaster-backend python -m fastapi_backend.seed_all_data 2>&1 || {
        echo "种子数据脚本执行失败，尝试备用方式..."
        docker exec testmaster-backend python -c "
import asyncio
from fastapi_backend.seed_all_data import seed_all
asyncio.run(seed_all())
" 2>&1 || echo "警告：种子数据初始化失败，可能需要手动执行"
    }
fi

# ==================== 8. 验证部署 ====================
echo ""
echo "====== [8/8] 验证部署 ======"

echo ""
echo "--- 容器状态 ---"
docker compose ps

echo ""
echo "--- 后端健康检查 ---"
curl -sf http://localhost:5001/api/health && echo " ✅ 后端正常" || echo " ❌ 后端异常"

echo ""
echo "--- 前端检查 ---"
curl -sf http://localhost/health && echo " ✅ 前端正常" || echo " ❌ 前端异常"

echo ""
echo "--- HTTPS 检查 ---"
curl -sfk https://localhost/health && echo " ✅ HTTPS 正常" || echo " ❌ HTTPS 异常"

echo ""
echo "============================================================"
echo "  部署完成！"
echo "============================================================"
echo ""
echo "访问地址:"
echo "  HTTPS: https://$(hostname -I | awk '{print $1}')"
echo "  HTTP:  http://$(hostname -I | awk '{print $1}') (自动跳转HTTPS)"
echo ""
echo "注意: 请使用 .env 中配置的 ADMIN_USERNAME / ADMIN_PASSWORD 登录"
echo "如果使用了种子数据，请在首次登录后立即修改默认密码！"
echo ""
echo "常用命令:"
echo "  查看日志:   docker compose logs -f backend"
echo "  重启服务:   docker compose restart"
echo "  停止服务:   docker compose down"
echo "  更新部署:   git pull && cd frontend && npm run build && cd .. && docker compose up -d --build"
echo ""
