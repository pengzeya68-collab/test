import requests
import json

# 测试后端API
url = "http://127.0.0.1:5002/api/cases/1"
data = {"name": "test-update"}
try:
    r = requests.put(url, json=data)
    print(f"Status: {r.status_code}")
    print(f"Response: {r.text[:500]}")
except Exception as e:
    print(f"Error: {e}")