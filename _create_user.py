import paramiko
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
    print(out[-1000:] if len(out) > 1000 else out)
    if err and rc != 0:
        print(f"[ERR] {err[-300:]}")
    return rc, out, err

try:
    client.connect(HOST, username=USER, password=PASS, timeout=30)

    print("=== Current users ===")
    run_cmd(
        """docker exec testmaster-postgres psql -U testmaster -d testmaster -c "SELECT id, username, email, is_admin FROM users" """
    )

    print("\n=== Register testuser ===")
    rc, out, err = run_cmd(
        'curl -s -X POST http://localhost:5001/api/v1/auth/register '
        '-H "Content-Type: application/json" '
        "-d '{\"username\":\"testuser\",\"email\":\"testuser@testmaster.com\",\"password\":\"password123\"}'"
    )
    try:
        result = json.loads(out)
        if "access_token" in result:
            print("✅ testuser 注册成功!")
        else:
            print(f"结果: {out[:300]}")
    except:
        print(f"结果: {out[:300]}")

    print("\n=== Verify login with testuser ===")
    rc, out, err = run_cmd(
        'curl -s -X POST http://localhost:5001/api/v1/auth/login '
        '-H "Content-Type: application/json" '
        "-d '{\"username\":\"testuser\",\"password\":\"password123\"}'"
    )
    try:
        result = json.loads(out)
        if "access_token" in result:
            print("✅ testuser 登录成功!")
        else:
            print(f"❌ 登录失败: {out[:300]}")
    except:
        print(f"结果: {out[:300]}")

    print("\n=== Also verify admin login ===")
    rc, out, err = run_cmd(
        'curl -s -X POST http://localhost:5001/api/v1/auth/login '
        '-H "Content-Type: application/json" '
        "-d '{\"username\":\"admin\",\"password\":\"admin123\"}'"
    )
    try:
        result = json.loads(out)
        if "access_token" in result:
            print("✅ admin 登录成功!")
    except:
        pass

    print("\n=== Make admin an admin user ===")
    run_cmd(
        """docker exec testmaster-postgres psql -U testmaster -d testmaster -c "UPDATE users SET is_admin=true, role='admin' WHERE username='admin'" """
    )

    print("\n=== Final users ===")
    run_cmd(
        """docker exec testmaster-postgres psql -U testmaster -d testmaster -c "SELECT id, username, email, is_admin, role FROM users" """
    )

except Exception as e:
    print(f"Error: {e}")
finally:
    client.close()
