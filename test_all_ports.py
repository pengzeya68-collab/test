import urllib.request, json, socket

for port in [5000, 5001, 5002, 5173, 8000, 3000]:
    try:
        sock = socket.create_connection(('localhost', port), timeout=1)
        sock.close()
        print(f'Port {port}: OPEN')
    except Exception:
        print(f'Port {port}: closed')
