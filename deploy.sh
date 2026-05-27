#!/bin/bash
# ============================================================
# TestMaster 一键部署脚本
# 用法: chmod +x deploy.sh && ./deploy.sh
# 前置条件: 服务器安装 docker + docker-compose
# 说明: 构建前端 + 重建后端镜像 + 启动所有服务
# ============================================================
set -e

echo "=========================================="
echo "  TestMaster 部署开始"
echo "  时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "=========================================="

# 检测 docker compose 命令
DOCKER_COMPOSE="docker compose"
if ! docker compose version >/dev/null 2>&1; then
    DOCKER_COMPOSE="docker-compose"
    if ! command -v docker-compose >/dev/null 2>&1; then
        echo "[错误] 请先安装 docker-compose"
        echo "  安装: curl -fsSL https://get.docker.com | bash"
        exit 1
    fi
fi
echo "[1/6] Docker: $(docker --version)"
echo "       Compose: $($DOCKER_COMPOSE version 2>/dev/null || echo ok)"

# 清理旧前端文件
echo "[2/6] 清理旧前端文件..."
rm -rf frontend/dist
mkdir -p frontend/dist

# 构建前端
echo "[3/6] 构建前端..."
cd frontend
if [ ! -d "node_modules" ] || [ ! -f "node_modules/.package-lock.json" ]; then
    echo "  安装依赖..."
    npm install
fi
npx vite build
cd ..
echo "  前端构建完成 ✓"

# 重建后端镜像并启动服务
echo "[4/6] 启动 Docker 服务..."
$DOCKER_COMPOSE up -d --build
echo "  Docker 服务启动完成 ✓"

# 健康检查
echo "[5/6] 健康检查..."
sleep 3
BACKEND_OK=false
for i in {1..15}; do
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5001/api/health 2>/dev/null || echo "000")
    if [ "$STATUS" = "200" ]; then
        echo "  后端服务 OK (状态码: $STATUS, 用时: ${i}s)"
        BACKEND_OK=true
        break
    fi
    echo "  等待后端启动... ($i/15)"
    sleep 2
done

if [ "$BACKEND_OK" = false ]; then
    echo "  ⚠ 后端启动超时! 请检查日志: docker logs testmaster-backend"
fi

# 验证 Nginx
echo "[6/6] 验证 Nginx..."
sleep 1
NGINX_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/ 2>/dev/null || echo "000")
echo "  Nginx 状态码: $NGINX_STATUS"

echo ""
echo "=========================================="
echo "  部署完成！"
echo "  访问地址: http://$(curl -s ifconfig.me 2>/dev/null || echo '服务器IP')/"
if [ "$BACKEND_OK" = true ] && [ "$NGINX_STATUS" = "200" ]; then
    echo "  状态: ✅ 全部正常"
else
    echo "  状态: ⚠ 部分异常，请检查日志"
fi
echo "=========================================="
