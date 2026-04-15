import urllib.request, json

BASE = 'http://localhost:5001'

# Test the API
req = urllib.request.Request(f'{BASE}/api/v1/learning-paths/learning-paths/25')
try:
    with urllib.request.urlopen(req, timeout=5) as resp:
        data = json.loads(resp.read())
        exercises = data.get('exercises', [])
        print(f'学习路径: {data.get("title")}')
        print(f'练习数量: {len(exercises)}')
        for ex in exercises:
            print(f'  [{ex["id"]}] {ex.get("title", "无标题")} ({ex.get("exercise_type")})')
except Exception as e:
    print(f'API Error: {e}')
