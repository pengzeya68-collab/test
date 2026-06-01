import paramiko
import os
import sys
sys.stdout.reconfigure(encoding='utf-8')

HOST = os.environ.get("SERVER_HOST", "")
PASS = os.environ.get("SERVER_PASS", "")
if not HOST or not PASS:
    print("错误: 请设置环境变量 SERVER_HOST 和 SERVER_PASS")
    sys.exit(1)

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username='root', password=PASS, timeout=15)

print('=== ALL CODE EXERCISES AUDIT ===')
print()

stdin, stdout, stderr = ssh.exec_command("""
docker exec testmaster-postgres psql -U testmaster -d testmaster -t -A -c "
SELECT id, title, language,
       CASE WHEN test_cases IS NOT NULL AND length(test_cases) > 5 THEN 'TC_OK' ELSE 'NO_TC' END as tc,
       CASE WHEN solution IS NOT NULL AND length(solution) > 5 THEN 'SOL_OK' ELSE 'NO_SOL' END as sol,
       CASE WHEN code_template IS NOT NULL AND length(code_template) > 5 THEN 'TPL_OK' ELSE 'NO_TPL' END as tpl,
       CASE WHEN setup_sql IS NOT NULL AND length(setup_sql) > 10 THEN 'SETUP_OK' ELSE 'NO_SETUP' END as setup,
       CASE WHEN hint IS NOT NULL AND length(hint) > 3 THEN 'HINT_OK' ELSE 'NO_HINT' END as hint
FROM exercises 
WHERE exercise_type='code'
ORDER BY language, id;
" 2>&1
""")
out = stdout.read().decode('utf-8', errors='replace').strip()
print(out)

print('\n\n=== SUMMARY BY LANGUAGE ===')
stdin, stdout, stderr = ssh.exec_command("""
docker exec testmaster-postgres psql -U testmaster -d testmaster -t -A -c "
SELECT language, 
       COUNT(*) as total,
       SUM(CASE WHEN test_cases IS NOT NULL AND length(test_cases) > 5 THEN 1 ELSE 0 END) as has_tc,
       SUM(CASE WHEN solution IS NOT NULL AND length(solution) > 5 THEN 1 ELSE 0 END) as has_sol,
       SUM(CASE WHEN code_template IS NOT NULL AND length(code_template) > 5 THEN 1 ELSE 0 END) as has_tpl,
       SUM(CASE WHEN setup_sql IS NOT NULL AND length(setup_sql) > 10 THEN 1 ELSE 0 END) as has_setup
FROM exercises 
WHERE exercise_type='code'
GROUP BY language
ORDER BY language;
" 2>&1
""")
print(stdout.read().decode('utf-8', errors='replace').strip())

ssh.close()
