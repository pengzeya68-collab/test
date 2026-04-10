import urllib.request
import json

# 通过 Vite 代理测试（模拟前端行为）
# Vite 代理配置: /auto-test -> http://127.0.0.1:5002, rewrite 去除 /auto-test

# 测试通过代理访问
url = "http://127.0.0.1:5173/auto-test/api/cases/1"  # 通过 Vite 代理
try:
    req = urllib.request.Request(url, method='GET')
    with urllib.request.urlopen(req, timeout=5) as resp:
        data = json.loads(resp.read().decode())
        print(f"GET through Vite proxy: {resp.status}")
        print(f"  assert_rules: {data.get('assert_rules')}")
except Exception as e:
    print(f"GET through Vite proxy FAILED: {e}")

# 测试 PUT through Vite proxy
url = "http://127.0.0.1:5173/auto-test/api/cases/1"
payload = json.dumps({
    "name": "Test Update",
    "assert_rules": [{"field": "status_code", "operator": "equals", "expectedValue": "200"}]
}).encode('utf-8')
try:
    req = urllib.request.Request(url, data=payload, method='PUT')
    req.add_header('Content-Type', 'application/json')
    with urllib.request.urlopen(req, timeout=5) as resp:
        print(f"\nPUT through Vite proxy: {resp.status}")
except urllib.error.HTTPError as e:
    print(f"\nPUT through Vite proxy HTTP Error: {e.code}")
    print(f"  Body: {e.read().decode()[:200]}")
except Exception as e:
    print(f"\nPUT through Vite proxy FAILED: {e}")