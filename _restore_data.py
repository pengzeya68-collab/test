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
    print(out[-2000:] if len(out) > 2000 else out)
    if err:
        print(f"[STDERR] {err[-500:]}")
    return rc, out, err

try:
    client.connect(HOST, username=USER, password=PASS, timeout=30)
    print("✅ SSH connected")

    print("\n=== Step 1: Restore old data into current database ===")
    print("Strategy: Drop current schema, restore old dump, then add new columns")

    print("\n=== Step 1a: Backup current new data (just in case) ===")
    run_cmd(
        "docker exec testmaster-postgres pg_dump -U testmaster testmaster > /tmp/current_testmaster_dump.sql",
        timeout=60
    )
    run_cmd("ls -la /tmp/current_testmaster_dump.sql", timeout=5)

    print("\n=== Step 1b: Drop current schema and restore old dump ===")
    run_cmd(
        'docker exec testmaster-postgres psql -U testmaster -d testmaster -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"',
        timeout=30
    )

    print("\n=== Step 1c: Restore old dump ===")
    rc, out, err = run_cmd(
        "docker exec -i testmaster-postgres psql -U testmaster -d testmaster < /tmp/old_testmaster_dump.sql",
        timeout=120
    )

    print("\n=== Step 2: Verify data restoration ===")
    tables = [
        ("users", 26), ("learning_paths", 18), ("exercises", 897),
        ("interview_questions", 343), ("exam_questions", 126),
        ("lesson_sections", 133), ("exams", 12),
        ("interface_test_cases", 78), ("interface_test_folders", 15),
        ("daily_checkins", 105), ("exam_answers", 78),
        ("exam_attempts", 5), ("exercise_submissions", 8),
        ("posts", 11), ("roles", 3), ("permissions", 29),
        ("test_scenarios", 6), ("scenario_steps", 3),
        ("environments", 3),
    ]
    all_ok = True
    for table, expected in tables:
        rc, out, err = run_cmd(
            f'docker exec testmaster-postgres psql -U testmaster -d testmaster -t -c "SELECT COUNT(*) FROM {table}"',
            timeout=5
        )
        count = int(out.strip()) if out.strip().isdigit() else 0
        status = "✅" if count >= expected else "⚠️"
        if count < expected:
            all_ok = False
        print(f"  {status} {table}: {count} (expected >= {expected})")

    print("\n=== Step 3: Add missing new columns to test_scenarios ===")
    new_columns = [
        "ALTER TABLE test_scenarios ADD COLUMN IF NOT EXISTS schedule_cron_expression VARCHAR(200)",
        "ALTER TABLE test_scenarios ADD COLUMN IF NOT EXISTS schedule_webhook_url TEXT",
        "ALTER TABLE test_scenarios ADD COLUMN IF NOT EXISTS schedule_env_id INTEGER",
        "ALTER TABLE test_scenarios ADD COLUMN IF NOT EXISTS schedule_task_name VARCHAR(200)",
        "ALTER TABLE test_scenarios ADD COLUMN IF NOT EXISTS schedule_is_active BOOLEAN DEFAULT true",
        "ALTER TABLE test_scenarios ADD COLUMN IF NOT EXISTS project_id INTEGER",
        "ALTER TABLE test_scenarios ADD COLUMN IF NOT EXISTS fail_fast BOOLEAN DEFAULT false",
        "ALTER TABLE test_scenarios ADD COLUMN IF NOT EXISTS webhook_token VARCHAR(64)",
    ]
    for sql in new_columns:
        run_cmd(f'docker exec testmaster-postgres psql -U testmaster -d testmaster -c "{sql}"', timeout=10)

    print("\n=== Step 4: Rename old columns if they exist ===")
    renames = [
        ("cron_expression", "schedule_cron_expression"),
        ("webhook_url", "schedule_webhook_url"),
        ("environment_id", "schedule_env_id"),
    ]
    for old, new in renames:
        run_cmd(
            f'docker exec testmaster-postgres psql -U testmaster -d testmaster -c "'
            f"DO $$ BEGIN IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='test_scenarios' AND column_name='{old}') THEN "
            f"ALTER TABLE test_scenarios RENAME COLUMN {old} TO {new}; END IF; END $$\"",
            timeout=10
        )

    print("\n=== Step 5: Drop obsolete columns if they exist ===")
    for col in ["case_ids", "data_matrix", "user_id"]:
        run_cmd(
            f'docker exec testmaster-postgres psql -U testmaster -d testmaster -c "'
            f"ALTER TABLE test_scenarios DROP COLUMN IF EXISTS {col}\"",
            timeout=10
        )

    print("\n=== Step 6: Stamp alembic ===")
    run_cmd(
        "docker exec testmaster-backend bash -c 'cd /app/fastapi_backend && alembic stamp head'",
        timeout=30
    )

    print("\n=== Step 7: Restart services ===")
    run_cmd("docker restart testmaster-backend", timeout=30)
    time.sleep(8)
    run_cmd("docker restart testmaster-celery", timeout=30)
    time.sleep(10)

    print("\n=== Step 8: Final verification ===")
    run_cmd("docker ps --format 'table {{.Names}}\t{{.Status}}'", timeout=10)

    rc, out, err = run_cmd("curl -s http://localhost:5001/api/health", timeout=10)
    print(f"Backend: {'✅ OK' if 'ok' in out.lower() else '❌'}")

    if all_ok:
        print("\n🎉 All data restored successfully!")
    else:
        print("\n⚠️ Some tables have fewer rows than expected, please check")

except Exception as e:
    print(f"Error: {e}")
finally:
    client.close()
