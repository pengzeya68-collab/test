"""
TestMaster WSGI entrypoint.
"""
import os

from backend.app import create_app


os.environ['TZ'] = 'Asia/Shanghai'

app = create_app()


if __name__ == '__main__':
    import socket

    port = int(os.environ.get('PORT', '5000'))
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)
    print('TestMaster API starting...')
    print(f'Local: http://localhost:{port}')
    print(f'Network: http://{ip_address}:{port}')
    app.run(debug=False, host='0.0.0.0', port=port)
