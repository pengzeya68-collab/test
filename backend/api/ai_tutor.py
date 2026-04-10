# AI Tutor API for TestMasterProject
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
import json
import os
import requests
from datetime import datetime
from ..models.models import User, Exercise, Progress

ai_bp = Blueprint('ai_tutor', __name__)

# 尝试导入OpenAI
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("Warning: openai package not installed, AI tutor will use fallback responses")

# 火山方舟（豆包大模型）配置
ARK_API_KEY = os.environ.get('ARK_API_KEY', '')  # 火山方舟 API Key
ARK_MODEL = os.environ.get('ARK_MODEL', 'doubao-pro-32k')  # 默认使用豆包Pro模型
ARK_BASE_URL = os.environ.get('ARK_BASE_URL', 'https://ark.cn-beijing.volces.com/api/v3')

# 检查是否使用火山方舟
USE_ARK = os.environ.get('USE_ARK', 'false').lower() == 'true'

# AI角色设定
SYSTEM_PROMPT = """
你是一位资深的软件测试工程师AI导师，名字叫TestMaster，拥有10年以上的测试行业经验，精通软件测试全栈技术，包括功能测试、接口测试、自动化测试、性能测试等。
你的任务是帮助用户学习软件测试相关知识，解答他们的问题，指导他们提升测试技能。

回答要求：
1. 专业且易懂：用通俗易懂的语言解释专业概念，避免过于晦涩的术语
2. 实用性强：多给实际案例和可操作的建议，不要空泛的理论
3. 鼓励为主：对用户的问题保持耐心，给予积极的反馈和鼓励
4. 结构清晰：分点回答，重点突出，便于用户理解
5. 针对性强：根据用户的问题给出具体的解决方案，不要答非所问

你擅长的领域：
- 软件测试基础理论、测试流程、测试方法
- Web/APP功能测试、测试用例设计、缺陷管理
- 接口测试、HTTP协议、Postman、接口自动化
- 自动化测试、Selenium/Appium、Python自动化框架
- 性能测试、Jmeter、性能调优
- 编程能力：Python、SQL、Shell脚本
- 测试工程师面试指导、简历优化

当用户提问时，如果涉及代码问题，要详细解释代码逻辑，指出可能的问题并给出优化建议。
如果用户询问学习建议，要结合测试工程师的成长路径给出合理的学习计划。
"""

# 预设场景的提示词模板
PROMPT_TEMPLATES = {
    'general': """
用户问题：{question}
请作为测试工程师导师回答这个问题，回答要专业、详细、有实用性。
""",
    
    'code_review': """
用户提交的{language}代码：
{code}

请审查这段代码，从以下几个方面给出反馈：
1. 代码是否有语法错误或逻辑错误
2. 代码的优点是什么
3. 可以优化的地方有哪些
4. 优化后的代码示例
5. 相关的编程知识讲解

回答要详细，易于理解，对新手友好。
""",
    
    'exercise_explain': """
用户正在做这道习题：
习题标题：{title}
习题描述：{description}
用户的答案：{user_answer}
正确答案：{correct_answer}
用户回答错误，请详细解释错误原因，讲解这道题涉及的知识点，帮助用户理解。
""",
    
    'learning_advice': """
用户当前的技能情况：
{skill_data}

请根据用户的技能情况，给出个性化的学习建议，包括：
1. 当前阶段应该重点学习的内容
2. 推荐的学习资源和学习方法
3. 可以练习的项目和实战方向
4. 短期和长期的学习规划
5. 提升学习效率的技巧

建议要具体、可执行，符合测试工程师的成长路径。
""",
    
    'interview_simulation': """
用户现在要模拟测试工程师面试，你作为面试官提问。
用户的目标岗位是：{position}
用户的工作经验：{experience}年
当前面试轮次：{round}

请先介绍一下面试流程，然后提出第一个面试问题，问题要符合对应岗位和经验的难度。
面试问题要覆盖技术能力、项目经验、软素质等方面。
用户回答后，你要给出评价和改进建议，然后提出下一个问题。
"""
}

# 对话历史存储（简单实现，实际项目可以存入数据库）
conversation_history = {}

def get_ark_response(messages):
    """调用火山方舟（豆包大模型）API获取回答"""
    if not ARK_API_KEY:
        print("Warning: ARK_API_KEY not set, skipping Ark API")
        return None
    
    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {ARK_API_KEY}"
        }
        
        # 转换消息格式（确保符合OpenAI兼容格式）
        formatted_messages = []
        for msg in messages:
            if isinstance(msg, dict) and 'role' in msg and 'content' in msg:
                formatted_messages.append({
                    "role": msg['role'],
                    "content": msg['content']
                })
        
        data = {
            "model": ARK_MODEL,
            "messages": formatted_messages,
            "temperature": 0.7,
            "max_tokens": 2000
        }
        
        # 处理base URL，确保路径正确
        # 如果ARK_BASE_URL以 /v3 结尾，我们需要改成 /v1 才能正确访问chat/completions
        base_url = ARK_BASE_URL
        if base_url.endswith('/v3'):
            base_url = base_url.replace('/v3', '/v1')
        elif not base_url.endswith('/v1') and not base_url.endswith('/'):
            base_url = base_url + '/v1'
        
        url = f"{base_url}/chat/completions"
        response = requests.post(
            url,
            headers=headers,
            json=data,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            if 'choices' in result and len(result['choices']) > 0:
                return result['choices'][0]['message']['content']
            else:
                print(f"Ark API返回异常: {result}")
                return None
        else:
            print(f"Ark API调用失败: HTTP {response.status_code}, {response.text}")
            return None
            
    except Exception as e:
        print(f"Ark API调用异常: {str(e)}")
        return None

def get_ai_response(messages):
    """调用AI接口获取回答"""
    
    # 优先使用火山方舟（如果配置了）
    if USE_ARK and ARK_API_KEY:
        try:
            response = get_ark_response(messages)
            if response:
                print(f"[AI] 使用火山方舟模型: {ARK_MODEL}")
                return response
        except Exception as e:
            print(f"火山方舟API调用失败: {str(e)}, 尝试其他API")
    
    # 尝试调用OpenAI API
    api_key = os.environ.get('OPENAI_API_KEY')
    base_url = os.environ.get('OPENAI_BASE_URL', 'https://api.openai.com/v1')
    model = os.environ.get('OPENAI_MODEL', 'gpt-3.5-turbo')
    
    if OPENAI_AVAILABLE and api_key:
        try:
            client = OpenAI(api_key=api_key, base_url=base_url)
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.7,
                max_tokens=2000
            )
            print(f"[AI] 使用OpenAI模型: {model}")
            return response.choices[0].message.content
        except Exception as e:
            print(f"OpenAI API调用失败: {str(e)}")
    
    # Fallback: 使用预设回答
    print("[AI] 使用预设回答")
    return get_fallback_response(messages)

def get_fallback_response(messages):
    """当AI API不可用时使用的预设回答"""
    import time
    time.sleep(0.5)  # 模拟延迟
    
    last_user_message = [m for m in messages if m['role'] == 'user'][-1]['content']
    
    # 根据问题关键词返回不同的预设回答
    if 'Python' in last_user_message or 'python' in last_user_message:
        return """
### Python学习建议
Python是测试工程师必备的编程语言，学习路径建议：

1. **基础阶段（1-2个月）**
   - 掌握Python基础语法：变量、数据类型、条件判断、循环、函数、类和对象
   - 练习小项目：计算器、 todo 列表、简单的爬虫
   - 重点掌握：列表、字典、字符串处理、文件操作

2. **进阶阶段（2-3个月）**
   - 学习常用库：requests（接口请求）、pytest（单元测试）、selenium（UI自动化）
   - 学习面向对象编程、异常处理、模块和包的使用
   - 实战项目：接口自动化测试框架、UI自动化测试脚本

3. **高级阶段（持续学习）**
   - 学习数据结构和算法、设计模式
   - 学习框架开发、持续集成相关知识
   - 实战项目：开发测试工具、自动化测试平台

💡 学习技巧：多写多练，每天至少写30分钟代码，遇到问题先查官方文档。
"""
    elif '接口测试' in last_user_message:
        return """
### 接口测试学习指南
接口测试是测试工程师的核心技能之一，学习建议：

1. **基础准备**
   - 熟练掌握HTTP/HTTPS协议，了解请求方法、状态码、请求头、响应头
   - 掌握JSON/XML数据格式，了解RESTful API设计规范
   - 学会使用Postman/ApiPost等接口测试工具

2. **进阶技能**
   - 学习接口自动化测试：使用Python+Requests+pytest实现接口自动化
   - 掌握接口用例设计方法：正例、反例、边界值、异常场景
   - 了解接口签名、加密、鉴权等安全相关知识

3. **实战要点**
   - 接口测试流程：需求分析→用例设计→执行测试→缺陷提交→报告输出
   - 重点关注：接口返回正确性、性能、安全性、兼容性
   - 常见问题：参数校验不严格、异常处理不完善、性能不达标

📌 实战建议：找一个开源项目，独立完成所有接口的测试用例设计和自动化脚本开发。
"""
    elif '代码' in last_user_message or 'code' in last_user_message:
        return """
### 代码审查结果
我看了你提交的代码，整体实现逻辑是对的，有几个可以优化的地方：

✅ **优点：**
- 基本功能实现正确，逻辑清晰
- 变量命名比较规范，可读性不错
- 有基本的注释说明

🔧 **优化建议：**
1. **增加异常处理**：现在的代码没有异常捕获，遇到输入错误会直接崩溃，建议加上try-except块
2. **函数拆分**：可以把核心逻辑拆分成多个小函数，提高代码的可复用性
3. **参数校验**：增加输入参数的合法性校验，避免非法输入导致的问题
4. **单元测试**：建议编写对应的单元测试用例，保证代码质量

💡 优化后的代码示例：
```python
def calculate_sum(numbers):
    \"\"\"计算列表中所有数字的和\"\"\"
    if not isinstance(numbers, list):
        raise TypeError("输入必须是列表类型")
    
    total = 0
    for num in numbers:
        if not isinstance(num, (int, float)):
            raise ValueError(f"元素{num}不是数字类型")
        total += num
    return total

# 测试
if __name__ == "__main__":
    try:
        print(calculate_sum([1, 2, 3, 4, 5]))  # 输出: 15
        print(calculate_sum([1, "2", 3]))      # 会抛出异常
    except Exception as e:
        print(f"错误: {e}")
```

继续加油，多写多练代码能力会提升很快的！
"""
    else:
        return """
### 测试工程师学习建议
作为测试工程师，建议你按照以下路径系统学习：

1. **第一阶段：测试基础（1-2个月）**
   - 软件测试基础概念、测试流程、测试方法
   - 测试用例设计方法、缺陷管理流程
   - 常用测试工具的使用：Jira、禅道、Xmind等

2. **第二阶段：功能测试（2-3个月）**
   - Web/APP功能测试实战
   - 专项测试：兼容性测试、易用性测试、安全性测试
   - 测试计划、测试方案、测试报告编写

3. **第三阶段：技术进阶（3-6个月）**
   - 接口测试：HTTP协议、Postman、接口自动化
   - 数据库：SQL语法、数据库测试
   - Linux：常用命令、Shell脚本、环境部署
   - 编程语言：Python基础

4. **第四阶段：自动化测试（6-12个月）**
   - UI自动化测试：Selenium/Appium
   - 接口自动化测试：Requests+pytest
   - 自动化框架设计、持续集成

5. **第五阶段：高级技能（1年以上）**
   - 性能测试：Jmeter、性能调优
   - 安全测试基础
   - 测试平台开发、测试左移/右移

💡 学习技巧：理论学习和实战相结合，多做项目积累经验，遇到问题多思考多总结。

有什么具体的问题可以随时问我哦！

---
*注：当前AI导师使用预设回答。如需接入真实AI，请设置 OPENAI_API_KEY 环境变量。*
"""

def build_messages(user_id, question, context=None):
    """构建对话消息"""
    # 初始化用户对话历史
    if user_id not in conversation_history:
        conversation_history[user_id] = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]
    
    # 添加上下文信息
    if context:
        conversation_history[user_id].append({"role": "system", "content": f"上下文信息：{context}"})
    
    # 添加用户问题
    conversation_history[user_id].append({"role": "user", "content": question})
    
    # 只保留最近10轮对话，避免token过长
    if len(conversation_history[user_id]) > 20:
        # 保留系统提示和最近9轮对话
        conversation_history[user_id] = [conversation_history[user_id][0]] + conversation_history[user_id][-18:]
    
    return conversation_history[user_id]

@ai_bp.route('/ai/chat', methods=['POST'])
@jwt_required()
def ai_chat():
    """AI对话接口"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    question = data.get('question', '')
    context = data.get('context', '')
    chat_type = data.get('type', 'general')  # general/code_review/exercise_explain/learning_advice/interview
    
    if not question:
        return jsonify({'error': '问题不能为空'}), 400
    
    try:
        # 构建消息
        messages = build_messages(user_id, question, context)
        
        # 获取AI回答
        answer = get_ai_response(messages)
        
        # 保存AI回答到历史
        conversation_history[user_id].append({"role": "assistant", "content": answer})
        
        return jsonify({
            'answer': answer,
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'AI服务异常：{str(e)}'}), 500

@ai_bp.route('/ai/code-review', methods=['POST'])
@jwt_required()
def code_review():
    """代码审查接口"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    code = data.get('code', '')
    language = data.get('language', 'python')
    
    if not code:
        return jsonify({'error': '代码不能为空'}), 400
    
    try:
        # 构建代码审查提示词
        question = PROMPT_TEMPLATES['code_review'].format(
            language=language,
            code=code
        )
        
        # 构建消息
        messages = build_messages(user_id, question)
        
        # 获取AI回答
        answer = get_ai_response(messages)
        
        # 保存AI回答到历史
        conversation_history[user_id].append({"role": "assistant", "content": answer})
        
        return jsonify({
            'review_result': answer,
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'代码审查异常：{str(e)}'}), 500

@ai_bp.route('/ai/learning-advice', methods=['GET'])
@jwt_required()
def learning_advice():
    """获取个性化学习建议"""
    user_id = get_jwt_identity()
    
    try:
        # 这里可以获取用户的技能数据
        skill_data = {
            'test_theory': 85,
            'functional_test': 70,
            'api_test': 50,
            'automation_test': 30,
            'performance_test': 20,
            'programming': 65,
            'database': 75,
            'linux': 60
        }
        
        # 构建学习建议提示词
        question = PROMPT_TEMPLATES['learning_advice'].format(
            skill_data=json.dumps(skill_data, ensure_ascii=False, indent=2)
        )
        
        # 构建消息
        messages = build_messages(user_id, question)
        
        # 获取AI回答
        answer = get_ai_response(messages)
        
        return jsonify({
            'advice': answer,
            'skill_data': skill_data,
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'获取学习建议异常：{str(e)}'}), 500

@ai_bp.route('/ai/explain-exercise', methods=['POST'])
@jwt_required()
def explain_exercise():
    """习题解析"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    exercise_id = data.get('exercise_id')
    user_answer = data.get('user_answer', '')
    
    if not exercise_id:
        return jsonify({'error': '习题ID不能为空'}), 400
    
    try:
        # 获取习题信息
        exercise = Exercise.query.get(exercise_id)
        if not exercise:
            return jsonify({'error': '习题不存在'}), 404
        
        # 构建习题解析提示词
        question = PROMPT_TEMPLATES['exercise_explain'].format(
            title=exercise.title,
            description=exercise.description,
            user_answer=user_answer,
            correct_answer=exercise.solution
        )
        
        # 构建消息
        messages = build_messages(user_id, question)
        
        # 获取AI回答
        answer = get_ai_response(messages)
        
        return jsonify({
            'explanation': answer,
            'exercise_title': exercise.title,
            'correct_answer': exercise.solution,
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'习题解析异常：{str(e)}'}), 500

@ai_bp.route('/ai/clear-history', methods=['POST'])
@jwt_required()
def clear_history():
    """清空对话历史"""
    user_id = get_jwt_identity()
    
    if user_id in conversation_history:
        # 保留系统提示
        conversation_history[user_id] = [conversation_history[user_id][0]]
    
    return jsonify({'message': '对话历史已清空'}), 200
