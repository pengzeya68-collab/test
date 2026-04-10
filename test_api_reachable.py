import urllib.request
import json

tests = [
    ("GET", "http://127.0.0.1:5002/api/cases?page=1&page_size=1", None),
    ("GET", "http://127.0.0.1:5002/api/groups", None),
    ("GET", "http://127.0.0.1:5002/api/cases/1", None),
]

for method, url, data in tests:
    try:
        if data:
            req = urllib.request.Request(url, data=json.dumps(data).encode(), method=method)
            req.add_header('Content-Type', 'application/json')
        else:
            req = urllib.request.Request(url, method=method)
        with urllib.request.urlopen(req, timeout=5) as resp:
            print(f"OK {method} {url} -> {resp.status}")
    except Exception as e:
        print(f"FAIL {method} {url} -> {type(e).__name__}: {e}")