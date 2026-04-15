import requests

print("=== Test 1: Duplicate phone (should return 409) ===")
r = requests.post('http://localhost:8000/api/v1/auth/register', json={
    "username": "dupuser",
    "email": "dupuser@test.com",
    "phone": "13900139000",
    "password": "123456"
}, timeout=5)
print(f'Status: {r.status_code}')
print(f'Response: {r.json()}')

print("\n=== Test 2: New user (should return 200) ===")
r2 = requests.post('http://localhost:8000/api/v1/auth/register', json={
    "username": "freshuser",
    "email": "freshuser@test.com",
    "phone": "13700137000",
    "password": "123456"
}, timeout=5)
print(f'Status: {r2.status_code}')
if r2.status_code == 200:
    data = r2.json()
    print(f'user: {data.get("user", {}).get("username")}')
    print('[OK] Both tests passed!')
else:
    print(f'Response: {r2.json()}')
