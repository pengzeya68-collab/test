import paramiko
import os
import sys
import time
sys.stdout.reconfigure(encoding='utf-8')

HOST = os.environ.get("SERVER_HOST", "")
USER = 'root'
PASSWORD = os.environ.get("SERVER_PASS", "")
if not HOST or not PASSWORD:
    print("错误: 请设置环境变量 SERVER_HOST 和 SERVER_PASS")
    sys.exit(1)

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASSWORD, timeout=30)

print('=== 1. Pull latest code from git ===')
stdin, stdout, stderr = ssh.exec_command(
    'cd /root/TestMasterProject && git pull origin main 2>&1',
    timeout=30
)
print(stdout.read().decode('utf-8', errors='replace').strip())

print('\n=== 2. Force rebuild backend (no cache) ===')
stdin, stdout, stderr = ssh.exec_command(
    'cd /root/TestMasterProject && docker compose build --no-cache backend 2>&1 | tail -10',
    timeout=300
)
out = stdout.read().decode('utf-8', errors='replace').strip()
print(out[-800:] if len(out) > 800 else out)

print('\n=== 3. Restart backend ===')
stdin, stdout, stderr = ssh.exec_command(
    'cd /root/TestMasterProject && docker compose up -d backend 2>&1',
    timeout=60
)
print(stdout.read().decode('utf-8', errors='replace').strip())

time.sleep(8)

print('\n=== 4. Verify setup_sql in sandbox.py ===')
stdin, stdout, stderr = ssh.exec_command("""
docker exec testmaster-backend grep -n "setup_sql" /app/fastapi_backend/routers/sandbox.py 2>&1
""")
out = stdout.read().decode('utf-8', errors='replace').strip()
print(out if out else 'STILL NOT FOUND!')

print('\n=== 5. Verify setup_sql in sandbox_service.py ===')
stdin, stdout, stderr = ssh.exec_command("""
docker exec testmaster-backend grep -n "setup_sql" /app/fastapi_backend/services/sandbox_service.py 2>&1
""")
out = stdout.read().decode('utf-8', errors='replace').strip()
print(out if out else 'STILL NOT FOUND!')

print('\n=== 6. Verify setup_sql in sandbox schema ===')
stdin, stdout, stderr = ssh.exec_command("""
docker exec testmaster-backend grep -n "setup_sql" /app/fastapi_backend/schemas/sandbox.py 2>&1
""")
out = stdout.read().decode('utf-8', errors='replace').strip()
print(out if out else 'STILL NOT FOUND!')

ssh.close()
print('\nDone!')
