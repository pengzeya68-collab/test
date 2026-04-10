import urllib.request
import json

# 测试 PUT 请求，模拟前端完整数据
url = "http://127.0.0.1:5002/api/cases/1"
payload = json.dumps({
    "group_id": None,
    "method": "POST",
    "name": "测试登录接口",
    "url": "{{base_url}}{{api_prefix}}/login",
    "description": "测试管理员登录",
    "headers": {},
    "payload": None,
    "assert_rules": [{"field": "status_code", "operator": "equals", "expectedValue": "200"}]
}).encode('utf-8')

req = urllib.request.Request(url, data=payload, method='PUT')
req.add_header('Content-Type', 'application/json')

try:
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode())
        print(f"Status: {resp.status}")
        print(f"assert_rules: {data.get('assert_rules')}")
except urllib.error.HTTPError as e:
    print(f"HTTP Error: {e.code}")
    body = e.read().decode()
    print(f"Body: {body}")
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")