import paramiko, json, sys

host = "34.150.26.84"
user = "root"
password = "PENGZEYA19940821"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, username=user, password=password, timeout=30)

task_id = sys.argv[1] if len(sys.argv) > 1 else ""
cmd = f"curl -s 'http://localhost:5001/api/auto-test/jmeter/quick-bench/{task_id}'"
stdin, stdout, stderr = client.exec_command(cmd)
out = stdout.read().decode()

try:
    d = json.loads(out)
    print("status:", d.get("status"))
    print("percent:", d.get("percent"))
    r = d.get("result", {})
    if r:
        print("result keys:", list(r.keys()))
        print("samples count:", len(r.get("samples", [])))
        samples = r.get("samples", [])
        if samples:
            print("first sample:", json.dumps(samples[0], ensure_ascii=False, indent=2)[:500])
    else:
        print("no result field")
    print("detail:", d.get("detail", ""))
except Exception as e:
    print("parse error:", e)
    print("raw:", out[:500])

client.close()
