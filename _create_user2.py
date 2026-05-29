import paramiko
import json
import sys

HOST = "34.150.26.84"
USER = "root"
PASS = "PENGZEYA19940821"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    client.connect(HOST, username=USER, password=PASS, timeout=15)
    print("✅ SSH connected")

    stdin, stdout, stderr = client.exec_command(
        """docker exec testmaster-postgres psql -U testmaster -d testmaster -c "SELECT id, username, email FROM users" """,
        timeout=15
    )
    out = stdout.read().decode("utf-8", errors="replace")
    print(f"Current users:\n{out}")

    stdin, stdout, stderr = client.exec_command(
        'curl -s -X POST http://localhost:5001/api/v1/auth/register '
        '-H "Content-Type: application/json" '
        "-d '{\"username\":\"testuser\",\"email\":\"testuser@testmaster.com\",\"password\":\"password123\"}'",
        timeout=15
    )
    out = stdout.read().decode("utf-8", errors="replace")
    print(f"Register testuser: {out[:300]}")

    stdin, stdout, stderr = client.exec_command(
        'curl -s -X POST http://localhost:5001/api/v1/auth/login '
        '-H "Content-Type: application/json" '
        "-d '{\"username\":\"testuser\",\"password\":\"password123\"}'",
        timeout=15
    )
    out = stdout.read().decode("utf-8", errors="replace")
    try:
        result = json.loads(out)
        if "access_token" in result:
            print("✅ testuser 登录成功!")
        else:
            print(f"❌ 登录失败: {out[:300]}")
    except:
        print(f"结果: {out[:300]}")

    stdin, stdout, stderr = client.exec_command(
        """docker exec testmaster-postgres psql -U testmaster -d testmaster -c "UPDATE users SET is_admin=true WHERE username='admin'" """,
        timeout=15
    )
    out = stdout.read().decode("utf-8", errors="replace")
    print(f"Set admin role: {out.strip()}")

except Exception as e:
    print(f"Error: {e}")
finally:
    client.close()
