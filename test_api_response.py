import requests
import json

# 测试获取用例接口
resp = requests.get("http://127.0.0.1:5002/auto-test/api/cases/1")
print(f"Status: {resp.status_code}")
data = resp.json()
print(f"assert_rules type: {type(data.get('assert_rules'))}")
print(f"assert_rules value: {repr(data.get('assert_rules'))}")

# 测试更新用例接口 - 先获取，再发送回去
print("\n--- Testing Update ---")
resp = requests.put(
    "http://127.0.0.1:5002/auto-test/api/cases/1",
    json={
        "name": "测试用例-新名称",
        "method": "GET",
        "url": "http://example.com/api/test",
        "group_id": 2,
        "assert_rules": [{"field": "status_code", "operator": "equals", "expectedValue": "200"}]
    }
)
print(f"Update status: {resp.status_code}")
print(f"Update response: {resp.text[:500]}")