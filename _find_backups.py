import paramiko
import time

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
    print(out[-3000:] if len(out) > 3000 else out)
    if err and rc != 0:
        print(f"[ERR] {err[-500:]}")
    return rc, out, err

try:
    client.connect(HOST, username=USER, password=PASS, timeout=30)
    print("✅ SSH connected")

    print("\n=== 1. Find database dump files ===")
    run_cmd("find / -name '*.sql' -o -name '*.dump' -o -name '*.backup' -o -name '*.pg_dump' 2>/dev/null | head -30", timeout=30)

    print("\n=== 2. Find backup directories ===")
    run_cmd("find /root -type d -name 'backup*' -o -name 'backups' -o -name 'db_backup' 2>/dev/null", timeout=15)
    run_cmd("find /var -type d -name 'backup*' -o -name 'backups' 2>/dev/null", timeout=15)

    print("\n=== 3. Check /root/TestMasterProject for backup files ===")
    run_cmd("find /root/TestMasterProject -name '*.sql' -o -name '*.dump' -o -name '*.backup' -o -name '*.json' 2>/dev/null | head -30", timeout=15)

    print("\n=== 4. Check Docker volumes ===")
    run_cmd("docker volume ls | grep -i postgres", timeout=10)
    run_cmd("docker volume ls | grep -i backup", timeout=10)

    print("\n=== 5. Check old postgres data volume ===")
    run_cmd("docker volume inspect testmasterproject_postgres-data 2>/dev/null || echo 'Volume not found'", timeout=10)

    print("\n=== 6. List all docker volumes ===")
    run_cmd("docker volume ls", timeout=10)

    print("\n=== 7. Check for pg_dump in container ===")
    run_cmd("docker exec testmaster-postgres ls -la /var/lib/postgresql/data/ 2>/dev/null | head -20", timeout=10)

    print("\n=== 8. Check backup API data ===")
    run_cmd("ls -la /root/TestMasterProject/fastapi_backend/autotest_data/ 2>/dev/null", timeout=10)
    run_cmd("ls -la /root/TestMasterProject/backups/ 2>/dev/null", timeout=10)

    print("\n=== 9. Check for any .sql or .dump in common locations ===")
    run_cmd("ls -la /tmp/*.sql /tmp/*.dump /tmp/*.backup 2>/dev/null; ls -la /root/*.sql /root/*.dump /root/*.backup 2>/dev/null; ls -la /home/*.sql /home/*.dump 2>/dev/null", timeout=10)

    print("\n=== 10. Check crontab for backup jobs ===")
    run_cmd("crontab -l 2>/dev/null; ls -la /etc/cron.d/ 2>/dev/null", timeout=10)

    print("\n=== 11. Check if old postgres container data still exists ===")
    run_cmd("find /var/lib/docker/volumes -name 'PG_VERSION' 2>/dev/null", timeout=15)

    print("\n=== 12. List docker volumes with details ===")
    run_cmd("for vol in $(docker volume ls -q); do echo \"=== $vol ===\"; docker volume inspect $vol 2>/dev/null | grep Mountpoint; done", timeout=30)

except Exception as e:
    print(f"Error: {e}")
finally:
    client.close()
