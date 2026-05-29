import paramiko
import time

HOST = "34.150.26.84"
USER = "root"
PASS = "PENGZEYA19940821"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

def run_cmd(cmd, timeout=120):
    print(f">>> {cmd[:120]}...")
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

    print("=== Copying updated files into running backend container ===")

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

    for f in backend_files:
        local = f"c:/Users/lenovo/Desktop/TestMasterProject/{f}"
        remote = f"/root/TestMasterProject/{f}"
        try:
            sftp.put(local, remote)
            print(f"  OK: {f}")
        except Exception as e:
            print(f"  FAIL: {f} -> {e}")

    sftp.close()

    print("\n=== Copying files into Docker container ===")
    run_cmd("docker cp /root/TestMasterProject/fastapi_backend testmaster-backend:/app/", timeout=30)
    run_cmd("docker cp /root/TestMasterProject/fastapi_backend testmaster-celery:/app/", timeout=30)

    print("\n=== Installing httpx in containers ===")
    run_cmd("docker exec testmaster-backend pip install httpx --quiet", timeout=60)
    run_cmd("docker exec testmaster-celery pip install httpx --quiet", timeout=60)

    print("\n=== Restarting backend ===")
    run_cmd("docker restart testmaster-backend", timeout=30)
    time.sleep(5)
    run_cmd("docker restart testmaster-celery", timeout=30)
    time.sleep(10)

    print("\n=== Verifying ===")
    run_cmd("docker ps --format 'table {{.Names}}\t{{.Status}}'", timeout=10)

    run_cmd("curl -s http://localhost:5001/api/health", timeout=10)

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

    run_cmd(
        'TOKEN=$(curl -s -X POST http://localhost:5001/api/v1/auth/login -H "Content-Type: application/json" -d \'{"username":"admin","password":"admin123"}\' | python3 -c "import sys,json;print(json.load(sys.stdin)[\'access_token\'])"); curl -s "http://localhost:5001/api/v1/admin/system/metrics" -H "Authorization: Bearer $TOKEN" | python3 -c "import sys,json; d=json.load(sys.stdin); print(\'DB:\', d.get(\'database\',{}).get(\'size_mb\'), \'MB, Healthy:\', d.get(\'database\',{}).get(\'healthy\'))"',
        timeout=10
    )

    print("\n✅ Hot deployment complete!")

except Exception as e:
    print(f"Error: {e}")
finally:
    client.close()
