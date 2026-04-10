"""
TestMaster 在线学习平台
WSGI 入口文件 - 用于生产环境部署（Gunicorn）
"""
import os
from backend.app import create_app

# 设置时区为东八区
os.environ['TZ'] = 'Asia/Shanghai'

app = create_app()

if __name__ == '__main__':
    import socket
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)
    print(f'TestMaster API starting...')
    print(f'Local: http://localhost:3000')
    print(f'Network: http://{ip_address}:3000')
    # 禁用自动重启以避免路径问题
    app.run(debug=False, host='0.0.0.0', port=3000)
