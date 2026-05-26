import requests
import json

print("=" * 50)
print("TestMaster 项目健康检查")
print("=" * 50)

# 1. 测试后端健康状态
print("\n1. 后端健康状态检查")
try:
    r = requests.get("http://localhost:5001/health", timeout=5)
    print(f"   /health: {r.status_code} - {r.json()}")
except Exception as e:
    print(f"   /health: 错误 - {e}")

try:
    r = requests.get("http://localhost:5001/api/health", timeout=5)
    print(f"   /api/health: {r.status_code} - {r.json()}")
except Exception as e:
    print(f"   /api/health: 错误 - {e}")

# 2. 测试登录
print("\n2. 登录测试")
try:
    r = requests.post("http://localhost:5001/api/v1/auth/login", 
                      json={"username": "admin", "password": "admin123"}, 
                      timeout=5)
    print(f"   Login: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        token = data.get("access_token")
        print(f"   Token获取: 成功")
        print(f"   用户信息: {data.get('user', {}).get('username')}")
        
        # 3. 测试需要认证的API
        print("\n3. 认证API测试")
        headers = {"Authorization": f"Bearer {token}"}
        
        # 学习路径
        r = requests.get("http://localhost:5001/api/v1/learning-paths", 
                        headers=headers, timeout=5)
        print(f"   /api/v1/learning-paths: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            if isinstance(data, list):
                print(f"   返回数据: {len(data)} 条记录")
            else:
                print(f"   返回数据: {data}")
        
        # 面试会话
        r = requests.get("http://localhost:5001/api/v1/interview/sessions", 
                        headers=headers, timeout=5)
        print(f"   /api/v1/interview/sessions: {r.status_code}")
        
        # 练习列表
        r = requests.get("http://localhost:5001/api/v1/exercises", 
                        headers=headers, timeout=5)
        print(f"   /api/v1/exercises: {r.status_code}")
        
    else:
        print(f"   Login失败: {r.text[:200]}")
except Exception as e:
    print(f"   Login: 错误 - {e}")

# 4. 测试前端代理
print("\n4. 前端代理测试")
try:
    r = requests.get("http://localhost:5173/", timeout=5)
    print(f"   前端首页: {r.status_code}")
except Exception as e:
    print(f"   前端首页: 错误 - {e}")

try:
    r = requests.get("http://localhost:5173/api/health", timeout=5)
    print(f"   前端代理/api/health: {r.status_code}")
except Exception as e:
    print(f"   前端代理/api/health: 错误 - {e}")

print("\n" + "=" * 50)
print("检查完成")
print("=" * 50)
