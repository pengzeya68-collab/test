import paramiko
import time

HOST = "34.150.26.84"
USER = "root"
PASS = "PENGZEYA19940821"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

def run_cmd(cmd, timeout=300):
    print(f">>> {cmd[:120]}...")
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode("utf-8", errors="replace")
    err = stderr.read().decode("utf-8", errors="replace")
    rc = stdout.channel.recv_exit_status()
    if out:
        print(out[-1500:] if len(out) > 1500 else out)
    if err and rc != 0:
        print(f"[ERR] {err[-500:]}")
    return rc, out, err

try:
    client.connect(HOST, username=USER, password=PASS, timeout=30)
    print("✅ SSH connected")

    print("\n=== Rebuild nginx with new frontend ===")
    run_cmd("docker stop testmaster-nginx 2>/dev/null; docker rm testmaster-nginx 2>/dev/null", timeout=30)
    rc, out, err = run_cmd(
        "cd /root/TestMasterProject && docker compose up -d --build --force-recreate nginx",
        timeout=180
    )

    time.sleep(10)

    print("\n=== Verify ===")
    run_cmd("docker ps --format 'table {{.Names}}\t{{.Status}}'", timeout=10)

    rc, out, err = run_cmd("curl -sk -o /dev/null -w '%{http_code}' https://localhost/", timeout=10)
    print(f"Frontend HTTPS: {out}")

    rc, out, err = run_cmd("curl -s http://localhost:5001/api/health", timeout=10)
    print(f"Backend: {'✅ OK' if 'ok' in out.lower() else '❌'}")

    print("\n✅ Nginx rebuild complete!")

except Exception as e:
    print(f"Error: {e}")
finally:
    client.close()
