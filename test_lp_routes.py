import urllib.request, json

BASE = 'http://localhost:5001'

# Try different prefixes
for prefix in ['/api/v1', '/api', '/learning-paths', '/api/learning-paths']:
    try:
        req = urllib.request.Request(f'{BASE}{prefix}')
        with urllib.request.urlopen(req, timeout=3) as resp:
            print(f'SUCCESS {prefix}: {resp.status}')
    except Exception as e:
        print(f'FAIL {prefix}: {e}')
