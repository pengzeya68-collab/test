import urllib.request
import json

# 测试更新用例接口
url = "http://127.0.0.1:5002/api/cases/1"
payload = json.dumps({
    "name": "测试用例-新名称",
    "method": "GET",
    "url": "http://example.com/api/test",
    "group_id": 2,
    "assert_rules": [{"field": "status_code", "operator": "equals", "expectedValue": "200"}]
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
    print(f"Error body: {e.read().decode()}")
except Exception as e:
    print(f"Error: {e}")