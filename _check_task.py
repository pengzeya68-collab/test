import paramiko, json, sys

host = "34.150.26.84"
user = "root"
password = "PENGZEYA19940821"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, username=user, password=password, timeout=30)

task_id = sys.argv[1] if len(sys.argv) > 1 else ""
cmd = f"""python3 -c "
import json, os, sys
sys.path.insert(0, '/app')
os.chdir('/app')

# Try to read from the in-memory store or file
try:
    # Check if there's a way to get task status
    import subprocess
    r = subprocess.run(['curl', '-s', f'http://localhost:5001/api/auto-test/jmeter/quick-bench/{task_id}', '-H', 'Content-Type: application/json'], capture_output=True, text=True)
    print('RAW RESPONSE:', r.stdout[:2000])
except Exception as e:
    print('ERROR:', e)
"
"""
stdin, stdout, stderr = client.exec_command(cmd)
out = stdout.read().decode()
err = stderr.read().decode()
if out:
    print(out, end="")
if err:
    print("STDERR:", err[:500], end="")

client.close()
