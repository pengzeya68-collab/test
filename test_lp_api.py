import urllib.request, json

BASE = 'http://localhost:5001'

# Test 1: Get all learning paths
req = urllib.request.Request(f'{BASE}/api/v1/learning-paths')
req.add_header('Content-Type', 'application/json')
try:
    with urllib.request.urlopen(req, timeout=5) as resp:
        data = json.loads(resp.read())
        print(f'=== /api/v1/learning-paths ({len(data)} paths) ===')
        for p in data[:3]:
            print(f"  id={p['id']}, title={repr(p.get('title',''))}, exercises={p.get('exercise_count',0)}")
except Exception as e:
    print(f'ERROR /learning-paths: {e}')

# Test 2: Get learning path detail (id=25)
try:
    req2 = urllib.request.Request(f'{BASE}/api/v1/learning-paths/25')
    with urllib.request.urlopen(req2, timeout=5) as resp:
        d = json.loads(resp.read())
        print(f'\n=== /api/v1/learning-paths/25 ===')
        print(f"  title={repr(d.get('title',''))}")
        exercises = d.get('exercises', [])
        print(f"  exercises count: {len(exercises)}")
        for ex in exercises[:3]:
            print(f"    ex id={ex['id']}, title={repr(ex.get('title',''))}")
        if len(exercises) == 0:
            print('  [WARNING] No exercises returned!')
            # Check raw keys
            print(f"  Available keys: {list(d.keys())}")
except Exception as e:
    print(f'ERROR /learning-paths/25: {e}')
