import psutil
import os

for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
    try:
        if 'python' in proc.info['name'].lower():
            cmdline = proc.info['cmdline']
            if cmdline:
                cmdline_str = ' '.join(cmdline)
                if '5002' in cmdline_str or 'uvicorn' in cmdline_str or 'auto_test' in cmdline_str:
                    print(f"PID: {proc.info['pid']}")
                    print(f"  Name: {proc.info['name']}")
                    print(f"  Cmd: {cmdline_str[:200]}")
                    print()
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        pass