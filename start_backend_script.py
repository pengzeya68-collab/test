import sys
import os
import subprocess
import time

os.chdir(r'c:\Users\lenovo\Desktop\TestMasterProject')
sys.path.insert(0, r'c:\Users\lenovo\Desktop\TestMasterProject')

print("[START] Starting Flask backend on port 5000...")
proc = subprocess.Popen(
    [sys.executable, '-m', 'backend.app'],
    cwd=r'c:\Users\lenovo\Desktop\TestMasterProject',
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    bufsize=1
)

# Wait and check if it started
time.sleep(3)

# Check if process is still running
if proc.poll() is None:
    print("[OK] Backend started successfully (PID: {})".format(proc.pid))
    # Read a few lines of output
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', 5000))
    sock.close()
    if result == 0:
        print("[OK] Backend is listening on port 5000")
    else:
        print("[WARN] Backend process running but port 5000 not responding yet")
else:
    print("[ERROR] Backend exited immediately with code:", proc.returncode)
    output, _ = proc.communicate()
    print("Output:")
    print(output)