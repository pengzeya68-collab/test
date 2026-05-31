import paramiko, sys
sys.stdout.reconfigure(encoding='utf-8')
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('34.150.26.84', username='root', password='PENGZEYA19940821', timeout=15)

print('=== exercise.py submit SQL section ===')
stdin, stdout, stderr = ssh.exec_command('docker exec testmaster-backend grep -n "setup_sql\|combined_sql\|execute_code.*sql" /app/fastapi_backend/routers/exercise.py 2>&1')
print(stdout.read().decode('utf-8', errors='replace').strip())

print('\n=== exercise.py lines 310-340 ===')
stdin, stdout, stderr = ssh.exec_command('docker exec testmaster-backend sed -n "310,340p" /app/fastapi_backend/routers/exercise.py 2>&1')
print(stdout.read().decode('utf-8', errors='replace').strip())

ssh.close()
