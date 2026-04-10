# Code execution sandbox for TestMasterProject
import os
import sys
import subprocess
import tempfile
import json
from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

code_bp = Blueprint('code', __name__)

# 支持的语言配置
LANGUAGE_CONFIG = {
    'python': {
        'command': 'python',
        'extension': '.py',
        'timeout': 5  # 执行超时时间，秒
    },
    'sql': {
        'command': 'sqlite3',
        'extension': '.sql',
        'timeout': 3
    },
    'shell': {
        'command': 'bash',
        'extension': '.sh',
        'timeout': 5
    }
}

# 安全限制：禁止执行危险命令
# 使用正则表达式进行更精确的匹配
import re

DANGEROUS_PATTERNS = [
    # 文件删除命令
    r'\brm\s+-[rf]*', r'\brmdir\s+', r'\bdel\s+', r'\bformat\s+', 
    r'\bmkfs\.', r'\bdd\s+if=', r'\bshred\s+',
    # 系统控制命令
    r'\bshutdown\b', r'\breboot\b', r'\bhalt\b', r'\bpoweroff\b',
    # 权限提升
    r'\bsudo\b', r'\bsu\s+-', r'\bdoas\b',
    # 网络下载
    r'\bwget\s+', r'\bcurl\s+.*-[oO]', r'\bscp\s+', r'\bsftp\b',
    r'\bftp\b', r'\bnc\s+', r'\bnetcat\b',
    # 包管理器
    r'\bpip\s+(install|uninstall)', r'\bconda\s+install', 
    r'\bapt\s+(install|remove|purge)', r'\byum\s+install',
    r'\bdnf\s+install', r'\bbrew\s+install', r'\bapk\s+add',
    r'\bnpm\s+(install|i)\s', r'\byarn\s+add',
    # 文件权限修改
    r'\bchmod\s+', r'\bchown\s+', r'\bchgrp\s+',
    # Python危险操作
    r'\bos\.system\s*\(', r'\bos\.popen\s*\(', r'\bsubprocess\.', 
    r'\bexec\s*\(', r'\beval\s*\(', r'\bcompile\s*\(',
    r'\b__import__\s*\(', r'\bimportlib\.', r'\bimport\s+os\s*;',
    # Shell危险操作
    r'[|;&]\s*\b(?:rm|del|format|shutdown)\b',
    r'`[^`]*\b(?:rm|del|format)\b[^`]*`',
    r'\$\([^)]*\b(?:rm|del|format)\b[^)]*\)',
    # 路径遍历
    r'\.\./', r'\.\.\\', r'~/\.', r'/etc/passwd', r'/etc/shadow',
    # 网络扫描
    r'\bnmap\b', r'\bping\s+-[cf]', r'\btraceroute\b',
]

def is_code_safe(code, language):
    """检查代码是否安全 - 使用正则表达式进行精确匹配"""
    code_lower = code.lower()
    
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, code_lower):
            return False, f"检测到危险代码模式"
    
    # 额外的安全检查：禁止多行命令链
    dangerous_chain_chars = [';', '&&', '||', '|']
    if language == 'shell':
        # Shell脚本允许管道，但要检查危险命令
        lines = code.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('#'):
                continue
            # 检查是否尝试执行危险操作
            if re.search(r'\b(?:bash|sh|zsh)\s+-c\s+', line):
                return False, "禁止嵌套执行shell命令"
    
    return True, "安全"

def execute_python(code, test_input=None):
    """执行Python代码"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
        f.write(code)
        temp_file = f.name
    
    try:
        result = subprocess.run(
            [sys.executable, temp_file],
            capture_output=True,
            text=True,
            timeout=5,
            input=test_input
        )
        return {
            'stdout': result.stdout,
            'stderr': result.stderr,
            'returncode': result.returncode,
            'success': result.returncode == 0
        }
    except subprocess.TimeoutExpired:
        return {
            'stdout': '',
            'stderr': '代码执行超时（超过5秒）',
            'returncode': -1,
            'success': False
        }
    finally:
        os.unlink(temp_file)

def execute_sql(code):
    """执行SQL代码（使用内存SQLite数据库）"""
    import sqlite3
    import io
    
    # 创建内存数据库
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    
    # 捕获输出
    output = []
    
    try:
        cursor = conn.cursor()
        
        # 分割多条SQL语句
        statements = [s.strip() for s in code.split(';') if s.strip()]
        
        for statement in statements:
            try:
                cursor.execute(statement)
                
                # 如果是SELECT语句，获取结果
                if statement.upper().startswith('SELECT'):
                    rows = cursor.fetchall()
                    if rows:
                        # 获取列名
                        columns = [description[0] for description in cursor.description]
                        output.append('\t'.join(columns))
                        output.append('-' * 40)
                        for row in rows:
                            output.append('\t'.join(str(cell) for cell in row))
                    else:
                        output.append("(没有数据)")
                else:
                    conn.commit()
                    output.append(f"执行成功，影响行数: {cursor.rowcount}")
                    
            except sqlite3.Error as e:
                output.append(f"SQL错误: {str(e)}")
                return {
                    'stdout': '\n'.join(output),
                    'stderr': str(e),
                    'returncode': 1,
                    'success': False
                }
        
        return {
            'stdout': '\n'.join(output) if output else "执行成功",
            'stderr': '',
            'returncode': 0,
            'success': True
        }
        
    except Exception as e:
        return {
            'stdout': '\n'.join(output) if output else "",
            'stderr': str(e),
            'returncode': 1,
            'success': False
        }
    finally:
        conn.close()

def execute_shell(code):
    """执行Shell代码"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False, encoding='utf-8') as f:
        f.write(code)
        temp_file = f.name
    
    try:
        result = subprocess.run(
            ['bash', temp_file],
            capture_output=True,
            text=True,
            timeout=5
        )
        return {
            'stdout': result.stdout,
            'stderr': result.stderr,
            'returncode': result.returncode,
            'success': result.returncode == 0
        }
    except subprocess.TimeoutExpired:
        return {
            'stdout': '',
            'stderr': 'Shell执行超时（超过5秒）',
            'returncode': -1,
            'success': False
        }
    finally:
        os.unlink(temp_file)

@code_bp.route('/code/execute', methods=['POST'])
@jwt_required()
def execute_code():
    """执行代码接口"""
    try:
        data = request.get_json()
        code = data.get('code', '').strip()
        language = data.get('language', 'python').lower()
        test_input = data.get('test_input', '')
        
        if not code:
            return jsonify({'error': '代码不能为空'}), 400
        
        if language not in LANGUAGE_CONFIG:
            return jsonify({'error': f'不支持的语言：{language}'}), 400
        
        # 安全检查
        safe, msg = is_code_safe(code, language)
        if not safe:
            return jsonify({'error': msg}), 403
        
        # 执行代码
        if language == 'python':
            result = execute_python(code, test_input)
        elif language == 'sql':
            result = execute_sql(code)
        elif language == 'shell':
            result = execute_shell(code)
        else:
            return jsonify({'error': '不支持的语言'}), 400
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@code_bp.route('/code/submit', methods=['POST'])
@jwt_required()
def submit_code():
    """提交代码并判题"""
    try:
        data = request.get_json()
        code = data.get('code', '').strip()
        language = data.get('language', 'python').lower()
        exercise_id = data.get('exercise_id')
        user_id = get_jwt_identity()
        
        if not code or not exercise_id:
            return jsonify({'error': '代码和习题ID不能为空'}), 400
        
        # 这里可以添加判题逻辑，对比预期输出
        # 先执行代码看是否正确
        execution_result = execute_python(code) if language == 'python' else \
                          execute_sql(code) if language == 'sql' else \
                          execute_shell(code)
        
        # 模拟判题结果，实际项目中需要根据习题的测试用例判断
        is_correct = execution_result['success'] and 'hello world' in execution_result['stdout'].lower()
        
        # 保存提交记录到数据库
        # submit_record = CodeSubmission(
        #     user_id=user_id,
        #     exercise_id=exercise_id,
        #     code=code,
        #     language=language,
        #     is_correct=is_correct,
        #     stdout=execution_result['stdout'],
        #     stderr=execution_result['stderr']
        # )
        # db.session.add(submit_record)
        # db.session.commit()
        
        return jsonify({
            'execution': execution_result,
            'is_correct': is_correct,
            'message': '答案正确！' if is_correct else '答案不正确，再试试？'
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
