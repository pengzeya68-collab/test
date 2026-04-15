import urllib.request, json

BASE = 'http://localhost:5001'

# Try learning-paths/25 with and without auth
paths_to_test = [
    '/api/v1/learning-paths/25',
    '/api/v1/learning-paths/learning-paths/25',
    '/api/v1/learning-paths/learning-paths?stage=1',
]

for p in paths_to_test:
    try:
        req = urllib.request.Request(BASE + p)
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
            exercises = data.get('exercises', [])
            print(f'OK {p}')
            print(f'  title={repr(data.get("title",""))}, exercises_count={len(exercises)}')
            if exercises:
                for ex in exercises[:3]:
                    print(f'  ex id={ex["id"]}, title={repr(ex.get("title",""))}')
            else:
                print(f'  [EMPTY] keys={list(data.keys())}')
    except Exception as e:
        print(f'FAIL {p}: {e}')
