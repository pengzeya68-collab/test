import urllib.request, json

BASE = 'http://localhost:5001'

# The CORRECT URL based on test results
correct_paths = [
    '/api/v1/learning-paths/learning-paths/25',
    '/api/v1/learning-paths/learning-paths/26',
    '/api/v1/learning-paths/learning-paths?stage=1',
]

for p in correct_paths:
    try:
        req = urllib.request.Request(BASE + p)
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
            if isinstance(data, list):
                print(f'LIST {p}: {len(data)} items')
                for item in data[:2]:
                    print(f'  id={item.get("id")}, title={repr(item.get("title",""))}, exercises={item.get("exercise_count",0)}')
            else:
                exercises = data.get('exercises', [])
                print(f'OK {p}')
                print(f'  title={repr(data.get("title",""))}, exercises_count={len(exercises)}')
                for ex in exercises[:3]:
                    print(f'  ex id={ex["id"]}, title={repr(ex.get("title",""))}')
    except Exception as e:
        print(f'FAIL {p}: {e}')
