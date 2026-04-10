import urllib.request
import json

url = "http://127.0.0.1:5002/api/cases/1"
try:
    with urllib.request.urlopen(url, timeout=5) as resp:
        data = json.loads(resp.read().decode())
        print(f"Status: {resp.status}")
        print(f"assert_rules type: {type(data.get('assert_rules'))}")
        print(f"assert_rules value: {repr(data.get('assert_rules'))}")
except Exception as e:
    print(f"Error: {e}")