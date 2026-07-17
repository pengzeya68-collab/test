"""
TestMaster 一键部署脚本（从本地 Windows 部署到远程 Linux 服务器）
用法: python deploy.py <服务器IP> <服务器密码> [旧服务器IP] [旧服务器密码]
示例:
  全新部署:           python deploy.py 1.2.3.4 YourServerPass
  从旧服务器迁移数据: python deploy.py 1.2.3.4 YourServerPass 10.0.0.1 OldServerPass

安全提示: 建议使用 SSH 密钥认证，避免在命令行中传递密码。
         也可设置环境变量 SERVER_HOST / SERVER_PASS。
"""

import paramiko
import os
import sys
import time

if len(sys.argv) < 3 and not (os.environ.get("SERVER_HOST") and os.environ.get("SERVER_PASS")):
    print("错误: 必须提供服务器 IP 和密码")
    print("用法: python deploy.py <服务器IP> <服务器密码> [旧服务器IP] [旧服务器密码]")
    sys.exit(1)

HOST = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("SERVER_HOST", "")
PASS = sys.argv[2] if len(sys.argv) > 2 else os.environ.get("SERVER_PASS", "")
USER = "root"
REPO_URL = "https://github.com/pengzeya68-collab/test.git"
INSTALL_DIR = "/root/TestMasterProject"
OLD_SERVER = sys.argv[3] if len(sys.argv) > 3 else ""
OLD_PASS = sys.argv[4] if len(sys.argv) > 4 else PASS

LOCAL_DIST = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend", "dist")


def run_ssh(transport, cmd, label="", timeout=300):
    print(f"\n[SSH] {label}")
    print(f"  命令: {cmd[:120]}...")
    channel = transport.open_session()
    channel.exec_command(cmd)
    channel.settimeout(timeout)

    out = b""
    err = b""
    while True:
        if channel.recv_ready():
            out += channel.recv(65536)
        if channel.recv_stderr_ready():
            err += channel.recv_stderr(65536)
        if channel.exit_status_ready():
            while channel.recv_ready():
                out += channel.recv(65536)
            while channel.recv_stderr_ready():
                err += channel.recv_stderr(65536)
            break
        time.sleep(0.1)

    out_str = out.decode("utf-8", errors="replace")
    err_str = err.decode("utf-8", errors="replace")
    exit_code = channel.recv_exit_status()

    if out_str.strip():
        for line in out_str.strip().split("\n"):
            print(f"  {line}")
    if err_str.strip() and exit_code != 0:
        for line in err_str.strip().split("\n")[:5]:
            print(f"  [ERR] {line}")
    if exit_code != 0:
        print(f"  [EXIT CODE] {exit_code}")
    channel.close()
    return out_str, err_str, exit_code


def sftp_upload_dir(sftp, local_dir, remote_dir):
    try:
        sftp.stat(remote_dir)
    except FileNotFoundError:
        sftp.mkdir(remote_dir)
    for item in os.listdir(local_dir):
        local_path = os.path.join(local_dir, item)
        remote_path = remote_dir + "/" + item
        if os.path.isdir(local_path):
            sftp_upload_dir(sftp, local_path, remote_path)
        else:
            sftp.put(local_path, remote_path)


def main():
    print("=" * 60)
    print("  TestMaster 一键部署")
    print(f"  服务器: {HOST}")
    print(f"  用户: {USER}")
    print("=" * 60)

    paramiko.util.log_to_file("paramiko_deploy.log")

    transport = paramiko.Transport((HOST, 22))
    try:
        transport.connect(username=USER)
        transport.auth_password(USER, PASS)
        print("[OK] SSH 连接成功")
    except Exception as e:
        print(f"[FAIL] SSH 认证失败: {e}")
        sys.exit(1)

    sftp = paramiko.SFTPClient.from_transport(transport)

    try:
        # Step 1: 安装依赖
        print("\n" + "#" * 60)
        print("# [1/7] 安装系统依赖")
        print("#" * 60)
        run_ssh(transport, "docker --version", "检查 Docker")
        run_ssh(transport, "docker compose version", "检查 Docker Compose")
        run_ssh(transport, "node --version || echo 'Node.js 未安装'", "检查 Node.js")

        # Step 2: 克隆/更新代码
        print("\n" + "#" * 60)
        print("# [2/7] 更新代码")
        print("#" * 60)
        _, _, code = run_ssh(transport, f"test -d {INSTALL_DIR}/.git && echo 'EXISTS' || echo 'NOT_EXISTS'", "检查代码目录")
        if "EXISTS" in _:
            run_ssh(transport, f"cd {INSTALL_DIR} && git fetch --all && git reset --hard origin/main", "更新代码")
        else:
            run_ssh(transport, f"git clone {REPO_URL} {INSTALL_DIR}", "克隆代码")

        # Step 3: 配置环境变量
        print("\n" + "#" * 60)
        print("# [3/7] 配置环境变量")
        print("#" * 60)
        run_ssh(transport, f"""
if [ ! -f {INSTALL_DIR}/.env ]; then
    cp {INSTALL_DIR}/.env.example {INSTALL_DIR}/.env
    SECRET_KEY=$(openssl rand -hex 32)
    DB_PASSWORD=$(openssl rand -hex 16)
    sed -i "s/^DB_PASSWORD=.*/DB_PASSWORD=$DB_PASSWORD/" {INSTALL_DIR}/.env
    sed -i "s/^SECRET_KEY=.*/SECRET_KEY=$SECRET_KEY/" {INSTALL_DIR}/.env
    sed -i "s|^DATABASE_URL=.*|DATABASE_URL=postgresql+asyncpg://testmaster:$DB_PASSWORD@postgres:5432/testmaster|" {INSTALL_DIR}/.env
    sed -i "s/^ENVIRONMENT=.*/ENVIRONMENT=production/" {INSTALL_DIR}/.env
    sed -i "s/^AUTO_CREATE_TABLES_ON_STARTUP=.*/AUTO_CREATE_TABLES_ON_STARTUP=true/" {INSTALL_DIR}/.env
    echo ".env 已生成，数据库使用 Docker 内部 PostgreSQL"
else
    echo ".env 已存在，跳过"
fi
""", "配置 .env")

        # Step 4: SSL 证书
        print("\n" + "#" * 60)
        print("# [4/7] SSL 证书")
        print("#" * 60)
        run_ssh(transport, f"""
mkdir -p {INSTALL_DIR}/ssl
if [ ! -f {INSTALL_DIR}/ssl/cert.pem ]; then
    openssl req -x509 -nodes -days 3650 -newkey rsa:2048 \
        -keyout {INSTALL_DIR}/ssl/key.pem -out {INSTALL_DIR}/ssl/cert.pem \
        -subj "/CN=testmaster.local/O=TestMaster/C=CN" 2>/dev/null
    echo "SSL 证书已生成"
else
    echo "SSL 证书已存在"
fi
""", "配置 SSL")

        # Step 5: 构建前端（本地构建 + SFTP 上传）
        print("\n" + "#" * 60)
        print("# [5/7] 构建并上传前端")
        print("#" * 60)

        if os.path.exists(LOCAL_DIST) and os.listdir(LOCAL_DIST):
            print("  本地 dist 目录存在，直接上传...")
            run_ssh(transport, f"rm -rf {INSTALL_DIR}/frontend/dist/*", "清空旧 dist")
            run_ssh(transport, f"mkdir -p {INSTALL_DIR}/frontend/dist", "确保目录存在")
            sftp_upload_dir(sftp, LOCAL_DIST, f"{INSTALL_DIR}/frontend/dist")
            print("  [OK] 前端上传完成")
        else:
            print("  本地无 dist，在服务器上构建...")
            run_ssh(transport, f"""
cd {INSTALL_DIR}/frontend
if [ ! -d node_modules ]; then
    npm install --legacy-peer-deps
fi
npm run build
""", "服务器上构建前端", timeout=600)

        # Step 6: Docker 构建并启动
        print("\n" + "#" * 60)
        print("# [6/7] Docker 构建并启动")
        print("#" * 60)
        run_ssh(transport, f"cd {INSTALL_DIR} && docker compose build --no-cache backend", "构建后端镜像", timeout=600)
        run_ssh(transport, f"cd {INSTALL_DIR} && docker compose up -d", "启动所有容器")
        print("  等待服务启动 (20秒)...")
        time.sleep(20)

        # Step 7: 初始化数据库
        print("\n" + "#" * 60)
        print("# [7/7] 初始化数据库")
        print("#" * 60)
        run_ssh(transport, """
for i in $(seq 1 30); do
    if docker exec testmaster-postgres pg_isready -U testmaster &>/dev/null; then
        echo "PostgreSQL 已就绪"
        break
    fi
    echo "等待中... ($i/30)"
    sleep 2
done
""", "等待 PostgreSQL")

        if OLD_SERVER:
            print(f"\n  从旧服务器 {OLD_SERVER} 迁移数据...")
            old_transport = paramiko.Transport((OLD_SERVER, 22))
            try:
                old_transport.connect(username=USER)
                old_transport.auth_password(USER, OLD_PASS)
                print("  旧服务器连接成功")
                run_ssh(old_transport, "docker exec testmaster-postgres pg_dump -U testmaster -d testmaster --no-owner --no-acl > /root/testmaster_migration.sql && gzip -f /root/testmaster_migration.sql && echo 'DUMP_OK'", "导出旧数据库", timeout=120)
            finally:
                old_transport.close()

            print("  下载备份文件...")
            old_transport2 = paramiko.Transport((OLD_SERVER, 22))
            old_transport2.connect(username=USER)
            old_transport2.auth_password(USER, OLD_PASS)
            old_sftp = paramiko.SFTPClient.from_transport(old_transport2)
            local_dump = os.path.join(os.path.dirname(os.path.abspath(__file__)), "testmaster_migration.sql.gz")
            old_sftp.get("/root/testmaster_migration.sql.gz", local_dump)
            old_sftp.close()
            old_transport2.close()
            print(f"  备份文件已下载: {local_dump} ({os.path.getsize(local_dump)} bytes)")

            print("  上传到新服务器...")
            sftp.put(local_dump, f"{INSTALL_DIR}/testmaster_migration.sql.gz")
            print("  导入数据...")
            run_ssh(transport, f"gunzip -c {INSTALL_DIR}/testmaster_migration.sql.gz | docker exec -i testmaster-postgres psql -U testmaster -d testmaster 2>&1 | tail -5", "导入旧数据", timeout=120)
            print("  数据迁移完成！")

            print("  运行代码题修复...")
            run_ssh(transport, f"""
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
""", "代码题修复", timeout=60)
        else:
            print("  未指定旧服务器，运行种子数据...")
            run_ssh(transport, f"""
docker exec testmaster-backend python -c "
import asyncio
from fastapi_backend.seed_all_data import seed_all
asyncio.run(seed_all())
" 2>&1 || echo "种子数据可能已存在"
""", "运行种子数据", timeout=120)

        # 验证
        print("\n" + "#" * 60)
        print("# 验证部署")
        print("#" * 60)
        run_ssh(transport, f"cd {INSTALL_DIR} && docker compose ps", "容器状态")
        run_ssh(transport, "curl -sf http://localhost:5001/api/health && echo ' ✅ 后端正常' || echo ' ❌ 后端异常'", "后端检查")
        run_ssh(transport, "curl -sfk https://localhost/health && echo ' ✅ HTTPS 正常' || echo ' ❌ HTTPS 异常'", "HTTPS 检查")

        print("\n" + "=" * 60)
        print("  部署完成！")
        print("=" * 60)
        print(f"\n  访问地址: https://{HOST}")
        print("  注意: 请使用 .env 中配置的 ADMIN_USERNAME / ADMIN_PASSWORD 登录")
        print("  如果使用了种子数据，请在首次登录后立即修改默认密码！")

    finally:
        sftp.close()
        transport.close()


if __name__ == "__main__":
    main()
