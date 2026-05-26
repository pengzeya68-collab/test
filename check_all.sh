#!/bin/bash

echo "=== TestMaster 项目全面健康检查 ==="
echo ""

# 1. 检查后端健康状态
echo "1. 后端健康状态："
curl -s http://localhost:5001/health | python -m json.tool 2>/dev/null || curl -s http://localhost:5001/health
echo ""

curl -s http://localhost:5001/api/health | python -m json.tool 2>/dev/null || curl -s http://localhost:5001/api/health
echo ""
echo ""

# 2. 测试登录
echo "2. 登录测试："
LOGIN_RESULT=$(curl -s http://localhost:5001/api/v1/auth/login -X POST -H "Content-Type: application/json" -d '{"username":"admin","password":"admin123"}')
TOKEN=$(echo "$LOGIN_RESULT" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

if [ -n "$TOKEN" ]; then
    echo "   登录成功！"
    echo "   Token长度: ${#TOKEN}"
    echo ""
    
    # 3. 测试需要认证的API
    echo "3. 认证API测试："
    
    # 学习路径
    echo "   - 学习路径 API:"
    LP_RESULT=$(curl -s -H "Authorization: Bearer $TOKEN" http://localhost:5001/api/v1/learning-paths)
    echo "     $LP_RESULT" | head -c 200
    echo ""
    
    # 面试会话
    echo "   - 面试会话 API:"
    INTERVIEW_RESULT=$(curl -s -H "Authorization: Bearer $TOKEN" http://localhost:5001/api/v1/interview/sessions)
    echo "     $INTERVIEW_RESULT" | head -c 200
    echo ""
    
    # 练习列表
    echo "   - 练习列表 API:"
    EXERCISE_RESULT=$(curl -s -H "Authorization: Bearer $TOKEN" http://localhost:5001/api/v1/exercises)
    echo "     $EXERCISE_RESULT" | head -c 200
    echo ""
    
else
    echo "   登录失败！"
    echo "   $LOGIN_RESULT"
fi

echo ""
echo "4. 前端状态："
FRONTEND_RESULT=$(curl -s http://localhost:5173/ | grep -o '<title>.*</title>')
if [ -n "$FRONTEND_RESULT" ]; then
    echo "   前端运行正常: $FRONTEND_RESULT"
else
    echo "   前端未启动或异常"
fi

echo ""
echo "5. 前端代理测试："
PROXY_RESULT=$(curl -s http://localhost:5173/api/health)
if [ -n "$PROXY_RESULT" ]; then
    echo "   代理正常: $PROXY_RESULT"
else
    echo "   代理异常或返回空"
fi

echo ""
echo "=== 检查完成 ==="
