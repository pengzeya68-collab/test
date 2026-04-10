import urllib.request
import json

# 测试 group_id 为 null 的情况
url = "http://127.0.0.1:5002/api/cases/2"
payload = json.dumps({
    "group_id": None,  # 关键测试点
    "method": "GET",
    "name": "获取习题列表（按阶段1过滤）",
    "url": "{{base_url}}{{api_prefix}}/exercises",
    "headers": {},
    "assert_rules": []
}).encode('utf-8')

req = urllib.request.Request(url, data=payload, method='PUT')
req.add_header('Content-Type', 'application/json')

try:
    with urllib.request.urlopen(req, timeout=10) as resp:
        print(f"Status: {resp.status}")
        data = json.loads(resp.read().decode())
        print(f"Success!")
except urllib.error.HTTPError as e:
    print(f"HTTP Error: {e.code}")
    print(f"Error body: {e.read().decode()[:500]}")
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")