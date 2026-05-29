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
    return rc, out, err

def api(method, path, data=None, token=None):
    headers = '-H "Content-Type: application/json"'
    if token:
        headers += f' -H "Authorization: Bearer {token}"'
    d = f"-d '{json.dumps(data)}'" if data else ""
    cmd = f'curl -s -X {method} http://localhost:5001{path} {headers} {d}'
    rc, out, err = run_cmd(cmd, timeout=15)
    try:
        return json.loads(out)
    except:
        return {"raw": out}

try:
    client.connect(HOST, username=USER, password=PASS, timeout=30)
    print("✅ SSH connected")

    result = api("POST", "/api/v1/auth/login", {"username": "admin", "password": "admin123"})
    token = result.get("access_token", "")
    print(f"Login: {'✅' if token else '❌'}")

    print("\n=== Create API cases with url ===")
    cases = []
    test_apis = [
        {"name": "获取用户列表", "method": "GET", "url": "https://httpbin.org/get", "group_id": 1},
        {"name": "创建用户", "method": "POST", "url": "https://httpbin.org/post", "group_id": 1},
        {"name": "获取订单列表", "method": "GET", "url": "https://httpbin.org/get", "group_id": 2},
        {"name": "创建订单", "method": "POST", "url": "https://httpbin.org/post", "group_id": 2},
        {"name": "系统健康检查", "method": "GET", "url": "https://httpbin.org/get", "group_id": 3},
    ]
    for case_data in test_apis:
        result = api("POST", "/api/auto-test/cases", case_data, token)
        cid = result.get("id")
        cases.append(cid)
        print(f"  {case_data['name']}: {'✅ id=' + str(cid) if cid else '❌ ' + str(result)[:100]}")

    print("\n=== Update scenarios with steps ===")
    for sid, name, step_cases in [
        (1, "用户管理测试", cases[:2]),
        (2, "订单流程测试", cases[2:4]),
        (3, "全流程回归测试", cases),
    ]:
        steps = []
        for j, cid in enumerate(step_cases):
            if cid:
                steps.append({"api_case_id": cid, "step_order": j + 1})
        result = api("PUT", f"/api/auto-test/scenarios/{sid}", {
            "steps": steps
        }, token)
        print(f"  {name}: {'✅' if 'id' in result else '❌ ' + str(result)[:100]}")

    print("\n=== Verify ===")
    result = api("GET", "/api/auto-test/scenarios", token=token)
    print(f"Scenarios: {result.get('total', 0)}")
    for item in result.get('items', []):
        print(f"  - {item.get('name')}: step_count={item.get('step_count', 0)}")

    result = api("GET", "/api/auto-test/cases", token=token)
    print(f"Cases: {result.get('total', 0)}")

    result = api("GET", "/api/auto-test/environments", token=token)
    print(f"Environments: {len(result) if isinstance(result, list) else result}")

    print("\n✅ Test data created!")

except Exception as e:
    print(f"Error: {e}")
finally:
    client.close()
