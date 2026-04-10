import psutil
import os

pid_22288 = None
pid_27452 = None

for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
    try:
        pid = proc.info['pid']
        if pid == 22288 or pid == 27452:
            cmdline = proc.info['cmdline']
            cmdline_str = ' '.join(cmdline) if cmdline else ''
            print(f"PID {pid}: {cmdline_str[:150]}")
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        pass

# 检查 5002 端口
for conn in psutil.net_connections():
    if conn.laddr.port == 5002:
        print(f"\nPort 5002 is used by PID: {conn.pid}")