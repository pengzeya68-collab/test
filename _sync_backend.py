import paramiko

HOST = "34.150.26.84"
USER = "root"
PASSWORD = "PENGZEYA19940821"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, username=USER, password=PASSWORD, timeout=30)

sftp = client.open_sftp()

files = [
    (r"c:\Users\lenovo\Desktop\TestMasterProject\fastapi_backend\services\autotest_jmeter_service.py",
     "/root/TestMaster/fastapi_backend/services/autotest_jmeter_service.py"),
    (r"c:\Users\lenovo\Desktop\TestMasterProject\frontend\src\components\JmeterTreeNode.vue",
     "/root/TestMaster/frontend/src/components/JmeterTreeNode.vue"),
    (r"c:\Users\lenovo\Desktop\TestMasterProject\frontend\src\views\JmeterAssistant.vue",
     "/root/TestMaster/frontend/src/views/JmeterAssistant.vue"),
]

for local, remote in files:
    sftp.put(local, remote)
    print(f"  synced {remote}")

sftp.close()

stdin, stdout, stderr = client.exec_command("cd /root/TestMaster && docker compose restart backend 2>&1")
out = stdout.read().decode()
err = stderr.read().decode()
if out: print(out)
if err: print(err)

client.close()
print("Backend restarted!")
