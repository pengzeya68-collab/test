import urllib.request, json

BASE = 'http://localhost:5001'

# Simple health check
try:
    req = urllib.request.Request(BASE)
    with urllib.request.urlopen(req, timeout=3) as resp:
        print(f'Root: {resp.status}')
except Exception as e:
    print(f'Root error: {e}')

# Try docs
try:
    req2 = urllib.request.Request(f'{BASE}/docs')
    with urllib.request.urlopen(req2, timeout=3) as resp:
        print(f'Docs: {resp.status}')
except Exception as e:
    print(f'Docs error: {e}')
