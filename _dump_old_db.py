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
    print(out[-3000:] if len(out) > 3000 else out)
    if err and rc != 0:
        print(f"[ERR] {err[-500:]}")
    return rc, out, err

try:
    client.connect(HOST, username=USER, password=PASS, timeout=30)
    print("✅ SSH connected")

    print("\n=== Step 1: Dump old PostgreSQL data from old volume ===")
    print("Starting a temporary postgres container with old volume...")
    rc, out, err = run_cmd(
        "docker run -d --name old-postgres "
        "-v testmaster_pg_data:/var/lib/postgresql/data "
        "-e POSTGRES_USER=testmaster "
        "-e POSTGRES_PASSWORD=testmaster_pass "
        "-e POSTGRES_DB=testmaster "
        "postgres:16",
        timeout=60
    )

    time.sleep(10)

    print("\n=== Step 2: Check if old postgres started ===")
    run_cmd("docker ps --filter name=old-postgres --format '{{.Names}} {{.Status}}'", timeout=10)

    print("\n=== Step 3: List tables in old database ===")
    run_cmd(
        "docker exec old-postgres psql -U testmaster -d testmaster -c '\\dt'",
        timeout=15
    )

    print("\n=== Step 4: Check row counts for important tables ===")
    tables = [
        "users", "learning_paths", "exercises", "interview_questions",
        "interview_sessions", "posts", "notes", "progress",
        "environments", "interface_test_folders", "interface_test_cases",
        "test_scenarios", "scenario_steps", "global_variables",
        "exam_questions", "exams", "exam_attempts", "exam_answers",
        "exercise_submissions", "daily_checkins", "favorites",
        "lesson_sections", "notifications", "roles", "permissions"
    ]
    for table in tables:
        run_cmd(
            f'docker exec old-postgres psql -U testmaster -d testmaster -c "SELECT COUNT(*) as {table} FROM {table}" 2>/dev/null || echo "Table {table} not found"',
            timeout=5
        )

    print("\n=== Step 5: Dump the old database ===")
    rc, out, err = run_cmd(
        "docker exec old-postgres pg_dump -U testmaster testmaster > /tmp/old_testmaster_dump.sql",
        timeout=120
    )
    run_cmd("ls -la /tmp/old_testmaster_dump.sql", timeout=5)

    print("\n=== Step 6: Stop old postgres container ===")
    run_cmd("docker stop old-postgres", timeout=30)
    run_cmd("docker rm old-postgres", timeout=15)

    print("\n✅ Old database dump created!")

except Exception as e:
    print(f"Error: {e}")
    try:
        run_cmd("docker stop old-postgres 2>/dev/null; docker rm old-postgres 2>/dev/null", timeout=15)
    except:
        pass
finally:
    client.close()
