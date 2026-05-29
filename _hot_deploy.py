import paramiko
import time
import os

HOST = "34.150.26.84"
USER = "root"
PASS = "PENGZEYA19940821"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

def run_cmd(cmd, timeout=120):
    print(f">>> {cmd[:150]}...")
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode("utf-8", errors="replace")
    err = stderr.read().decode("utf-8", errors="replace")
    rc = stdout.channel.recv_exit_status()
    if out:
        print(out[-2000:] if len(out) > 2000 else out)
    if err and rc != 0:
        print(f"[ERR] {err[-1000:]}")
    return rc, out, err

try:
    client.connect(HOST, username=USER, password=PASS, timeout=30)
    print("✅ SSH connected")

    print("\n=== Step 1: Git pull latest code ===")
    rc, out, err = run_cmd("cd /root/TestMasterProject && git fetch origin deepseek-support && git reset --hard origin/deepseek-support", timeout=60)
    if rc != 0:
        print("Git pull failed, trying git pull...")
        run_cmd("cd /root/TestMasterProject && git pull origin deepseek-support", timeout=60)

    print("\n=== Step 2: Copy updated files via SFTP ===")
    sftp = client.open_sftp()

    backend_files = [
        "fastapi_backend/main.py",
        "fastapi_backend/core/config.py",
        "fastapi_backend/core/database.py",
        "fastapi_backend/core/ssrf_guard.py",
        "fastapi_backend/core/router_registry.py",
        "fastapi_backend/core/autotest_database.py",
        "fastapi_backend/models/autotest.py",
        "fastapi_backend/models/models.py",
        "fastapi_backend/routers/autotest_execution.py",
        "fastapi_backend/routers/autotest_scenarios.py",
        "fastapi_backend/routers/autotest_cases.py",
        "fastapi_backend/routers/autotest_debug.py",
        "fastapi_backend/routers/autotest_environments.py",
        "fastapi_backend/routers/autotest_global_variables.py",
        "fastapi_backend/routers/autotest_health.py",
        "fastapi_backend/routers/autotest_suites.py",
        "fastapi_backend/routers/autotest_diagnostic.py",
        "fastapi_backend/routers/autotest_jmeter.py",
        "fastapi_backend/routers/backup.py",
        "fastapi_backend/routers/admin_system.py",
        "fastapi_backend/services/autotest_execution.py",
        "fastapi_backend/services/autotest_scenario_runner.py",
        "fastapi_backend/services/autotest_request_service.py",
        "fastapi_backend/services/autotest_scheduler.py",
        "fastapi_backend/services/autotest_schedule_persistence.py",
        "fastapi_backend/services/autotest_pytest_engine.py",
        "fastapi_backend/services/autotest_task_store.py",
        "fastapi_backend/tasks.py",
        "fastapi_backend/celery_config.py",
    ]

    migration_files = []
    local_migration_dir = "c:/Users/lenovo/Desktop/TestMasterProject/fastapi_backend/alembic/versions"
    for fname in os.listdir(local_migration_dir):
        if fname.endswith(".py"):
            migration_files.append(f"fastapi_backend/alembic/versions/{fname}")

    all_files = backend_files + migration_files

    for f in all_files:
        local = f"c:/Users/lenovo/Desktop/TestMasterProject/{f}"
        remote = f"/root/TestMasterProject/{f}"
        try:
            remote_dir = "/".join(remote.split("/")[:-1])
            try:
                sftp.stat(remote_dir)
            except FileNotFoundError:
                run_cmd(f"mkdir -p {remote_dir}")
            sftp.put(local, remote)
            print(f"  OK: {f}")
        except Exception as e:
            print(f"  FAIL: {f} -> {e}")

    sftp.close()

    print("\n=== Step 3: Copy files into Docker containers ===")
    run_cmd("docker cp /root/TestMasterProject/fastapi_backend testmaster-backend:/app/", timeout=30)
    run_cmd("docker cp /root/TestMasterProject/fastapi_backend testmaster-celery:/app/", timeout=30)

    print("\n=== Step 4: Run database migration (alembic upgrade head) ===")
    rc, out, err = run_cmd(
        "docker exec testmaster-backend python -m alembic -c /app/fastapi_backend/alembic.ini upgrade head",
        timeout=120
    )
    if rc != 0:
        print("Alembic migration failed, trying alternative path...")
        rc, out, err = run_cmd(
            "docker exec testmaster-backend bash -c 'cd /app/fastapi_backend && alembic upgrade head'",
            timeout=120
        )
    if rc != 0:
        print("Alembic still failed, trying direct SQL fix...")
        run_cmd(
            '''docker exec testmaster-backend python -c "
import asyncio
from sqlalchemy import text
from fastapi_backend.core.database import engine

async def fix_schema():
    async with engine.begin() as conn:
        cols = await conn.run_sync(lambda c: [col['name'] for col in c.execute(text('SELECT column_name FROM information_schema.columns WHERE table_name=\\'test_scenarios\\'')).fetchall()])
        print('Current columns:', cols)
        if 'cron_expression' in [c[0] if isinstance(c, tuple) else c for c in cols]:
            print('Renaming cron_expression -> schedule_cron_expression')
            await conn.execute(text('ALTER TABLE test_scenarios RENAME COLUMN cron_expression TO schedule_cron_expression'))
        if 'webhook_url' in [c[0] if isinstance(c, tuple) else c for c in cols]:
            print('Renaming webhook_url -> schedule_webhook_url')
            await conn.execute(text('ALTER TABLE test_scenarios RENAME COLUMN webhook_url TO schedule_webhook_url'))
        if 'environment_id' in [c[0] if isinstance(c, tuple) else c for c in cols]:
            print('Renaming environment_id -> schedule_env_id')
            await conn.execute(text('ALTER TABLE test_scenarios RENAME COLUMN environment_id TO schedule_env_id'))
        print('Schema fix done')

asyncio.run(fix_schema())
"''',
            timeout=60
        )

    print("\n=== Step 5: Restart backend & celery ===")
    run_cmd("docker restart testmaster-backend", timeout=30)
    time.sleep(8)
    run_cmd("docker restart testmaster-celery", timeout=30)
    time.sleep(10)

    print("\n=== Step 6: Verify services ===")
    run_cmd("docker ps --format 'table {{.Names}}\t{{.Status}}'", timeout=10)

    rc, out, err = run_cmd("curl -s http://localhost:5001/api/health", timeout=10)
    if rc == 0 and "ok" in out.lower():
        print("✅ Backend health check passed")
    else:
        print("❌ Backend health check failed")

    run_cmd(
        'curl -s -X POST http://localhost:5001/api/v1/auth/login -H "Content-Type: application/json" -d \'{"username":"admin","password":"admin123"}\' | python3 -c "import sys,json; d=json.load(sys.stdin); print(\'Login:\', \'OK\' if d.get(\'access_token\') else \'FAILED\')"',
        timeout=10
    )

    run_cmd(
        'TOKEN=$(curl -s -X POST http://localhost:5001/api/v1/auth/login -H "Content-Type: application/json" -d \'{"username":"admin","password":"admin123"}\' | python3 -c "import sys,json;print(json.load(sys.stdin)[\'access_token\'])"); curl -s "http://localhost:5001/api/auto-test/scenarios" -H "Authorization: Bearer $TOKEN" | python3 -c "import sys,json; d=json.load(sys.stdin); print(\'Scenarios:\', type(d).__name__, len(d) if isinstance(d, list) else d.get(\'total\', d))"',
        timeout=10
    )

    run_cmd(
        'TOKEN=$(curl -s -X POST http://localhost:5001/api/v1/auth/login -H "Content-Type: application/json" -d \'{"username":"admin","password":"admin123"}\' | python3 -c "import sys,json;print(json.load(sys.stdin)[\'access_token\'])"); curl -s "http://localhost:5001/api/auto-test/cases" -H "Authorization: Bearer $TOKEN" | python3 -c "import sys,json; d=json.load(sys.stdin); print(\'Cases:\', d.get(\'total\', len(d) if isinstance(d, list) else d))"',
        timeout=10
    )

    run_cmd(
        'TOKEN=$(curl -s -X POST http://localhost:5001/api/v1/auth/login -H "Content-Type: application/json" -d \'{"username":"admin","password":"admin123"}\' | python3 -c "import sys,json;print(json.load(sys.stdin)[\'access_token\'])"); curl -s "http://localhost:5001/api/auto-test/environments" -H "Authorization: Bearer $TOKEN" | python3 -c "import sys,json; d=json.load(sys.stdin); print(\'Envs:\', len(d) if isinstance(d, list) else d)"',
        timeout=10
    )

    print("\n✅ Deployment complete!")

except Exception as e:
    print(f"Error: {e}")
finally:
    client.close()
