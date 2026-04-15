import urllib.request, json

BASE = 'http://localhost:5001'

paths_to_test = [
    '/api/v1/learning-paths/learning-paths',
    '/api/v1/learning-paths/25',
    '/api/v1/learning-paths',
]

for p in paths_to_test:
    try:
        req = urllib.request.Request(BASE + p)
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
            print(f'OK {p}: {str(data)[:200]}')
    except Exception as e:
        print(f'FAIL {p}: {e}')
