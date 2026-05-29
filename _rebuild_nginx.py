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
    print("✅ SSH connected")

    print("\n=== Rebuild and restart nginx with new frontend ===")
    rc, out, err = run_cmd(
        "cd /root/TestMasterProject && docker compose up -d --build --force-recreate nginx",
        timeout=180
    )

    time.sleep(5)

    print("\n=== Verify all services ===")
    run_cmd("docker ps --format 'table {{.Names}}\t{{.Status}}'", timeout=10)

    rc, out, err = run_cmd("curl -s http://localhost:5001/api/health", timeout=10)
    print(f"Backend health: {'✅ OK' if 'ok' in out.lower() else '❌ FAILED'}")

    rc, out, err = run_cmd("curl -s -o /dev/null -w '%{http_code}' http://localhost/", timeout=10)
    print(f"Frontend HTTP status: {out}")

    print("\n✅ Full deployment complete!")

except Exception as e:
    print(f"Error: {e}")
finally:
    client.close()
