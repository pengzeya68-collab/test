import subprocess, json
r = subprocess.run(["curl", "-s", "http://localhost:5001/api/auto-test/jmeter/quick-bench/72258c74-abfe-434b-8c2c-6786fe17d173"], capture_output=True, text=True)
d = json.loads(r.stdout)
print("status:", d.get("status"))
print("percent:", d.get("percent"))
print("progress:", d.get("progress"))
res = d.get("result")
if res:
    print("result.total:", res.get("total"))
    print("result.samples count:", len(res.get("samples", [])))
else:
    print("no result yet")
