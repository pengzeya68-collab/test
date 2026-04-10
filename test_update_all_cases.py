import urllib.request
import json

# 模拟前端发送的完整请求格式
url = "http://127.0.0.1:5002/api/cases/2"
payload = json.dumps({
    "group_id": 2,
    "method": "GET",
    "name": "获取习题列表（按阶段1过滤）",
    "url": "{{base_url}}{{api_prefix}}/exercises",
    "description": "",
    "headers": {},
    "payload": None,
    "assert_rules": [
        {"field": "status_code", "operator": "equals", "expectedValue": "200"}
    ]
}).encode('utf-8')

req = urllib.request.Request(url, data=payload, method='PUT')
req.add_header('Content-Type', 'application/json')

try:
    with urllib.request.urlopen(req, timeout=10) as resp:
        print(f"Status: {resp.status}")
        data = json.loads(resp.read().decode())
        print(f"Response assert_rules: {data.get('assert_rules')}")
except urllib.error.HTTPError as e:
    print(f"HTTP Error: {e.code}")
    print(f"Error body: {e.read().decode()[:500]}")
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")