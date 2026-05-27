import paramiko
import os

HOST = "34.150.26.84"
USER = "root"
PASSWORD = "PENGZEYA19940821"
LOCAL_DIST = r"c:\Users\lenovo\Desktop\TestMasterProject\frontend\dist"
REMOTE_DIST = "/root/TestMaster/frontend/dist"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, username=USER, password=PASSWORD, timeout=30)

stdin, stdout, stderr = client.exec_command(f"rm -rf {REMOTE_DIST} && mkdir -p {REMOTE_DIST}")
stdout.read()

sftp = client.open_sftp()

uploaded = 0
for root, dirs, files in os.walk(LOCAL_DIST):
    rel = root.replace(LOCAL_DIST, "").replace(chr(92), "/")
    remote_dir = REMOTE_DIST + rel
    for d in dirs:
        rdir = remote_dir + "/" + d
        try:
            sftp.stat(rdir)
        except FileNotFoundError:
            sftp.mkdir(rdir)
    for f in files:
        local_path = os.path.join(root, f)
        remote_path = remote_dir + "/" + f
        sftp.put(local_path, remote_path)
        uploaded += 1
        if uploaded % 20 == 0:
            print(f"  uploaded {uploaded} files...")

sftp.close()
client.close()
print(f"Done! Uploaded {uploaded} files to {REMOTE_DIST}")
