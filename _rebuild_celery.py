import paramiko
import time
import json

HOST = "34.150.26.84"
USER = "root"
PASS = "PENGZEYA19940821"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

def run_cmd(cmd, timeout=60):
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode("utf-8", errors="replace")
    err = stderr.read().decode("utf-8", errors="replace")
    rc = stdout.channel.recv_exit_status()
    if out:
        print(out[-1000:] if len(out) > 1000 else out)
    if err and rc != 0:
        print(f"[ERR] {err[-300:]}")
    return rc, out, err

try:
    client.connect(HOST, username=USER, password=PASS, timeout=30)

    print("=== Rebuild celery with latest code ===")
    run_cmd("docker stop testmaster-celery 2>/dev/null; docker rm testmaster-celery 2>/dev/null", timeout=30)
    run_cmd("cd /root/TestMasterProject && docker compose up -d --build --force-recreate celery-worker", timeout=180)

    time.sleep(15)

    print("\n=== Fix permissions ===")
    run_cmd("docker exec -u root testmaster-backend chown -R appuser:appuser /app/fastapi_backend/autotest_data /app/instance /app/backups", timeout=15)
    run_cmd("docker exec -u root testmaster-backend chmod -R 777 /app/fastapi_backend/autotest_data /app/instance /app/backups", timeout=15)
    run_cmd("docker exec -u root testmaster-celery chown -R appuser:appuser /app/fastapi_backend/autotest_data /app/instance", timeout=15)
    run_cmd("docker exec -u root testmaster-celery chmod -R 777 /app/fastapi_backend/autotest_data /app/instance", timeout=15)

    print("\n=== Verify all services ===")
    run_cmd("docker ps --format 'table {{.Names}}\t{{.Status}}'", timeout=10)

    rc, out, err = run_cmd("curl -s http://localhost:5001/api/health", timeout=10)
    print(f"Backend: {'✅' if 'ok' in out.lower() else '❌'}")

    print("\n=== Test save to API library ===")
    rc, out, err = run_cmd(
        'curl -s -X POST http://localhost:5001/api/v1/auth/login '
        '-H "Content-Type: application/json" '
        "-d '{\"username\":\"testuser\",\"password\":\"password123\"}'",
        timeout=10
    )
    token = ""
    try:
        token = json.loads(out).get("access_token", "")
    except:
        pass
    print(f"Login: {'✅' if token else '❌'}")

    if token:
        rc, out, err = run_cmd(
            f'curl -s -X POST "http://localhost:5001/api/auto-test/cases" '
            f'-H "Authorization: Bearer {token}" '
            f'-H "Content-Type: application/json" '
            f"-d '{{\"name\":\"测试接口\",\"method\":\"GET\",\"url\":\"https://httpbin.org/get\",\"group_id\":1}}'",
            timeout=10
        )
        try:
            result = json.loads(out)
            if "id" in result:
                print(f"Save to library: ✅ (id={result['id']})")
            else:
                print(f"Save to library: ❌ {out[:200]}")
        except:
            print(f"Save to library: ❌ {out[:200]}")

    print("\n✅ All done!")

except Exception as e:
    print(f"Error: {e}")
finally:
    client.close()
