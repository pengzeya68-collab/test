import requests
import json

# Test registration endpoint
url = "http://localhost:5000/api/register"
headers = {
    "Content-Type": "application/json"
}
data = {
    "username": "testuser",
    "email": "test@example.com",
    "password": "password123"
}

print("Testing registration endpoint...")
print(f"URL: {url}")
print(f"Request data: {json.dumps(data, indent=2)}")

try:
    response = requests.post(url, headers=headers, json=data)
    print(f"\nStatus Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
except Exception as e:
    print(f"Error: {e}")

# Test login endpoint
print("\n" + "="*50)
print("Testing login endpoint...")
login_url = "http://localhost:5000/api/login"
login_data = {
    "username": "testuser",
    "password": "password123"
}

try:
    response = requests.post(login_url, headers=headers, json=login_data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
except Exception as e:
    print(f"Error: {e}")
