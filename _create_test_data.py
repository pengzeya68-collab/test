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

    print("\n=== Login ===")
    result = api("POST", "/api/v1/auth/login", {"username": "admin", "password": "admin123"})
    token = result.get("access_token", "")
    print(f"Login: {'✅' if token else '❌'}")

    print("\n=== Create environments ===")
    for name, base_url in [("测试环境", "https://httpbin.org"), ("开发环境", "http://localhost:8080"), ("生产环境", "https://api.example.com")]:
        result = api("POST", "/api/auto-test/environments", {"env_name": name, "base_url": base_url}, token)
        print(f"  {name}: {'✅' if 'id' in result else '❌ ' + str(result)[:100]}")

    print("\n=== Create API groups ===")
    groups = []
    for name in ["用户管理", "订单管理", "系统管理"]:
        result = api("POST", "/api/auto-test/groups", {"name": name}, token)
        gid = result.get("id")
        groups.append(gid)
        print(f"  {name}: {'✅ id=' + str(gid) if gid else '❌ ' + str(result)[:100]}")

    print("\n=== Create API cases ===")
    cases = []
    test_apis = [
        {"name": "获取用户列表", "method": "GET", "path": "/get", "group_id": groups[0] if groups else None},
        {"name": "创建用户", "method": "POST", "path": "/post", "group_id": groups[0] if groups else None},
        {"name": "获取订单列表", "method": "GET", "path": "/get", "group_id": groups[1] if len(groups) > 1 else None},
        {"name": "创建订单", "method": "POST", "path": "/post", "group_id": groups[1] if len(groups) > 1 else None},
        {"name": "系统健康检查", "method": "GET", "path": "/get", "group_id": groups[2] if len(groups) > 2 else None},
    ]
    for case_data in test_apis:
        result = api("POST", "/api/auto-test/cases", case_data, token)
        cid = result.get("id")
        cases.append(cid)
        print(f"  {case_data['name']}: {'✅ id=' + str(cid) if cid else '❌ ' + str(result)[:100]}")

    print("\n=== Create scenarios ===")
    for i, (name, step_cases) in enumerate([
        ("用户管理测试", cases[:2]),
        ("订单流程测试", cases[2:4]),
        ("全流程回归测试", cases),
    ]):
        steps = []
        for j, cid in enumerate(step_cases):
            if cid:
                steps.append({"api_case_id": cid, "step_order": j + 1})
        result = api("POST", "/api/auto-test/scenarios", {
            "name": name,
            "description": f"{name} - 自动创建的测试场景",
            "steps": steps
        }, token)
        print(f"  {name}: {'✅ id=' + str(result.get('id', '')) if 'id' in result else '❌ ' + str(result)[:100]}")

    print("\n=== Verify ===")
    result = api("GET", "/api/auto-test/scenarios", token=token)
    print(f"Scenarios: {result.get('total', 0)}")
    result = api("GET", "/api/auto-test/cases", token=token)
    print(f"Cases: {result.get('total', 0)}")
    result = api("GET", "/api/auto-test/environments", token=token)
    print(f"Environments: {len(result) if isinstance(result, list) else result}")

    print("\n✅ Test data created!")

except Exception as e:
    print(f"Error: {e}")
finally:
    client.close()
