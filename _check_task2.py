import subprocess, json

task_id = "72258c74-abfe-434b-8c2c-6786fe17d173"
r = subprocess.run(['curl', '-s', f'http://localhost:5001/api/auto-test/jmeter/quick-bench/{task_id}'], capture_output=True, text=True)
print(r.stdout[:3000])
