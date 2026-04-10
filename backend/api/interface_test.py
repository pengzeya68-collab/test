"""
接口测试 API 路由
处理接口测试用例的增删改查和请求发送
完善支持 Apipost 风格的功能：文件夹分组、环境管理、form-data等
"""
import json
import requests
import re
from datetime import datetime
from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from backend.extensions import db, limiter
from backend.models.models import InterfaceTestCase, InterfaceTestFolder, InterfaceTestEnvironment, InterfaceTestPlan, InterfaceTestReport, InterfaceTestReportResult

interface_test_bp = Blueprint('interface_test', __name__)


# ============ 文件夹管理 ============

@interface_test_bp.route('/interface-test/folders', methods=['GET'])
@jwt_required()
def get_folders():
    """获取当前用户的所有文件夹（树形结构）"""
    user_id = get_jwt_identity()
    folders = InterfaceTestFolder.query\
        .filter_by(user_id=user_id)\
        .order_by(InterfaceTestFolder.created_at.asc())\
        .all()
    
    # 构建树形结构
    folder_map = {f.id: {
        'id': f.id,
        'name': f.name,
        'description': f.description,
        'parent_id': f.parent_id,
        'children': [],
        'created_at': f.created_at.isoformat() if f.created_at else None,
        'updated_at': f.updated_at.isoformat() if f.updated_at else None
    } for f in folders}
    
    root_folders = []
    for f in folders:
        if f.parent_id is None:
            root_folders.append(folder_map[f.id])
        else:
            if f.parent_id in folder_map:
                folder_map[f.parent_id]['children'].append(folder_map[f.id])
    
    return jsonify(root_folders)


@interface_test_bp.route('/interface-test/folders', methods=['POST'])
@jwt_required()
def create_folder():
    """创建新文件夹"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data.get('name'):
        return jsonify({'error': '文件夹名称不能为空'}), 400
    
    # 正确处理 parent_id=null：明确设置 None 表示顶级文件夹
    parent_id = data.get('parent_id')
    if parent_id is None or parent_id == 'null':
        parent_id = None
        
    folder = InterfaceTestFolder(
        user_id=user_id,
        name=data['name'],
        description=data.get('description', ''),
        parent_id=parent_id
    )
    
    db.session.add(folder)
    db.session.commit()
    
    return jsonify({
        'message': '创建成功',
        'id': folder.id,
        'folder': {
            'id': folder.id,
            'name': folder.name,
            'parent_id': folder.parent_id
        }
    }), 201


@interface_test_bp.route('/interface-test/folders/<int:folder_id>', methods=['PUT'])
@jwt_required()
def update_folder(folder_id):
    """更新文件夹"""
    user_id = get_jwt_identity()
    folder = InterfaceTestFolder.query.get(folder_id)
    
    if not folder:
        return jsonify({'error': '文件夹不存在'}), 404
    if folder.user_id != user_id:
        return jsonify({'error': '无权限修改'}), 403
    
    data = request.get_json()
    if 'name' in data:
        folder.name = data['name']
    if 'description' in data:
        folder.description = data['description']
    if 'parent_id' in data:
        # 检查不能设置父文件夹为自己
        if data['parent_id'] == folder_id:
            return jsonify({'error': '不能将自己设置为子文件夹'}), 400
        folder.parent_id = data['parent_id']
    
    folder.updated_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({'message': '更新成功'})


@interface_test_bp.route('/interface-test/folders/<int:folder_id>', methods=['DELETE'])
@jwt_required()
def delete_folder(folder_id):
    """删除文件夹（同时会删除里面的所有用例）"""
    user_id = get_jwt_identity()
    folder = InterfaceTestFolder.query.get(folder_id)
    
    if not folder:
        return jsonify({'error': '文件夹不存在'}), 404
    if folder.user_id != user_id:
        return jsonify({'error': '无权限删除'}), 403
    
    # 删除文件夹下所有用例
    InterfaceTestCase.query\
        .filter_by(user_id=user_id, folder_id=folder_id)\
        .delete()
    
    db.session.delete(folder)
    db.session.commit()
    
    return jsonify({'message': '删除成功'})


# ============ 环境管理 ============

@interface_test_bp.route('/interface-test/environments', methods=['GET'])
@jwt_required()
def get_environments():
    """获取当前用户的所有环境"""
    user_id = get_jwt_identity()
    envs = InterfaceTestEnvironment.query\
        .filter_by(user_id=user_id)\
        .order_by(InterfaceTestEnvironment.is_default.desc(), InterfaceTestEnvironment.created_at.asc())\
        .all()
    
    result = []
    for env in envs:
        try:
            variables = json.loads(env.variables) if env.variables else {}
            # 如果是数组格式 [{key: "", value: ""}]，转换为 {key: value} 对象
            if isinstance(variables, list):
                new_vars = {}
                for item in variables:
                    if isinstance(item, dict) and 'key' in item and 'value' in item:
                        if item['key'] and item['key'].strip():
                            new_vars[item['key'].strip()] = item['value'] or ''
                variables = new_vars
            # 如果是错误格式 {"0": "{\"key\": ...}", "1": "{\"key\": ...}"}，转换为正确格式
            elif isinstance(variables, dict):
                # 检查是不是这种错误格式：值都是 JSON 字符串
                first_value = next(iter(variables.values()), None)
                if first_value and isinstance(first_value, str) and first_value.strip().startswith('{'):
                    new_vars = {}
                    for item_str in variables.values():
                        try:
                            item = json.loads(item_str)
                            if isinstance(item, dict) and 'key' in item and 'value' in item:
                                if item['key'] and item['key'].strip():
                                    new_vars[item['key'].strip()] = item['value'] or ''
                        except:
                            pass
                    variables = new_vars
        except:
            variables = {}
        result.append({
            'id': env.id,
            'name': env.name,
            'base_url': env.base_url,
            'variables': variables,
            'is_default': env.is_default,
            'created_at': env.created_at.isoformat() if env.created_at else None,
            'updated_at': env.updated_at.isoformat() if env.updated_at else None
        })
    
    return jsonify(result)


@interface_test_bp.route('/interface-test/environments', methods=['POST'])
@jwt_required()
def create_environment():
    """创建新环境"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data.get('name'):
        return jsonify({'error': '环境名称不能为空'}), 400
    
    env = InterfaceTestEnvironment(
        user_id=user_id,
        name=data['name'],
        base_url=data.get('base_url', ''),
        variables=json.dumps(data.get('variables', {}), ensure_ascii=False),
        is_default=data.get('is_default', False)
    )
    
    # 如果是默认环境，取消其他默认
    if env.is_default:
        InterfaceTestEnvironment.query\
            .filter_by(user_id=user_id)\
            .update({'is_default': False})
    
    db.session.add(env)
    db.session.commit()
    
    return jsonify({
        'message': '创建成功',
        'id': env.id
    }), 201


@interface_test_bp.route('/interface-test/environments/<int:env_id>', methods=['PUT'])
@jwt_required()
def update_environment(env_id):
    """更新环境"""
    user_id = get_jwt_identity()
    env = InterfaceTestEnvironment.query.get(env_id)
    
    if not env:
        return jsonify({'error': '环境不存在'}), 404
    if env.user_id != user_id:
        return jsonify({'error': '无权限修改'}), 403
    
    data = request.get_json()
    if 'name' in data:
        env.name = data['name']
    if 'base_url' in data:
        env.base_url = data['base_url']
    if 'variables' in data:
        env.variables = json.dumps(data['variables'], ensure_ascii=False)
    if 'is_default' in data:
        if data['is_default']:
            # 取消其他默认
            InterfaceTestEnvironment.query\
                .filter_by(user_id=user_id)\
                .update({'is_default': False})
        env.is_default = data['is_default']
    
    env.updated_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({'message': '更新成功'})


@interface_test_bp.route('/interface-test/environments/<int:env_id>', methods=['DELETE'])
@jwt_required()
def delete_environment(env_id):
    """删除环境"""
    user_id = get_jwt_identity()
    env = InterfaceTestEnvironment.query.get(env_id)
    
    if not env:
        return jsonify({'error': '环境不存在'}), 404
    if env.user_id != user_id:
        return jsonify({'error': '无权限删除'}), 403
    
    db.session.delete(env)
    db.session.commit()
    
    return jsonify({'message': '删除成功'})


# ============ 用例管理 ============

@interface_test_bp.route('/interface-test/cases', methods=['GET'])
@jwt_required(optional=True)
def get_cases():
    """获取当前用户的接口测试用例列表，可以按文件夹筛选"""
    user_id = get_jwt_identity()
    if not user_id:
        return jsonify({'error': '需要登录'}), 401

    # 处理空字符串安全转换为int
    folder_id_str = request.args.get('folder_id')
    folder_id = None
    if folder_id_str and folder_id_str != '':
        try:
            folder_id = int(folder_id_str)
        except (ValueError, TypeError):
            folder_id = None
    
    # 查询用户的所有用例，按更新时间倒序
    query = InterfaceTestCase.query.filter_by(user_id=user_id)
    if folder_id is not None:
        query = query.filter_by(folder_id=folder_id)
    
    cases = query.order_by(InterfaceTestCase.updated_at.desc()).all()
    
    result = []
    for case in cases:
        result.append({
            'id': case.id,
            'folder_id': case.folder_id,
            'name': case.name,
            'description': case.description,
            'url': case.url,
            'method': case.method,
            'headers': case.headers if case.headers is not None else '{}',
            'body': case.body if case.body is not None else '',
            'body_type': case.body_type,
            'is_public': case.is_public,
            'created_at': case.created_at.isoformat() if case.created_at else None,
            'updated_at': case.updated_at.isoformat() if case.updated_at else None
        })

    return jsonify(result)


@interface_test_bp.route('/interface-test/cases/<int:case_id>', methods=['GET'])
@jwt_required(optional=True)
def get_case(case_id):
    """获取单个接口测试用例详情"""
    user_id = get_jwt_identity()
    case = InterfaceTestCase.query.get(case_id)
    
    if not case:
        return jsonify({'error': '用例不存在'}), 404
    
    # 权限检查：只有自己能看私有用例
    if not case.is_public and case.user_id != user_id:
        return jsonify({'error': '无权限'}), 403
    
    return jsonify({
        'id': case.id,
        'user_id': case.user_id,
        'name': case.name,
        'description': case.description,
        'url': case.url,
        'method': case.method,
        'headers': case.headers,
        'body': case.body,
        'body_type': case.body_type,
        'is_public': case.is_public,
        'created_at': case.created_at.isoformat() if case.created_at else None,
        'updated_at': case.updated_at.isoformat() if case.updated_at else None
    })


@interface_test_bp.route('/interface-test/cases', methods=['POST'])
@jwt_required()
def create_case():
    """创建新的接口测试用例"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data.get('name'):
        return jsonify({'error': '用例名称不能为空'}), 400
    if not data.get('url'):
        return jsonify({'error': 'URL不能为空'}), 400
    
    case = InterfaceTestCase(
        user_id=user_id,
        folder_id=data.get('folder_id'),
        name=data['name'],
        description=data.get('description', ''),
        url=data['url'],
        method=data.get('method', 'GET'),
        headers=data.get('headers', '{}'),
        body=data.get('body', ''),
        body_type=data.get('body_type', 'json'),
        is_public=data.get('is_public', False)
    )
    
    db.session.add(case)
    db.session.commit()
    
    return jsonify({
        'message': '创建成功',
        'id': case.id,
        'case': {
            'id': case.id,
            'folder_id': case.folder_id,
            'name': case.name,
            'url': case.url,
            'method': case.method
        }
    }), 201


@interface_test_bp.route('/interface-test/cases/<int:case_id>', methods=['PUT'])
@jwt_required()
def update_case(case_id):
    """更新接口测试用例"""
    user_id = get_jwt_identity()
    case = InterfaceTestCase.query.get(case_id)
    
    if not case:
        return jsonify({'error': '用例不存在'}), 404
    if case.user_id != user_id:
        return jsonify({'error': '无权限修改'}), 403
    
    data = request.get_json()
    
    if 'name' in data:
        case.name = data['name']
    if 'description' in data:
        case.description = data['description']
    if 'folder_id' in data:
        case.folder_id = data['folder_id']
    if 'url' in data:
        case.url = data['url']
    if 'method' in data:
        case.method = data['method']
    if 'headers' in data:
        case.headers = data['headers']
    if 'body' in data:
        case.body = data['body']
    if 'body_type' in data:
        case.body_type = data['body_type']
    if 'is_public' in data:
        case.is_public = data['is_public']
    
    case.updated_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({'message': '更新成功'})


@interface_test_bp.route('/interface-test/cases/<int:case_id>', methods=['DELETE'])
@jwt_required()
def delete_case(case_id):
    """删除接口测试用例"""
    user_id = get_jwt_identity()
    case = InterfaceTestCase.query.get(case_id)
    
    if not case:
        return jsonify({'error': '用例不存在'}), 404
    if case.user_id != user_id:
        return jsonify({'error': '无权限删除'}), 403
    
    db.session.delete(case)
    db.session.commit()
    
    return jsonify({'message': '删除成功'})


@interface_test_bp.route('/interface-test/cases/<int:case_id>/copy', methods=['POST'])
@jwt_required()
def copy_case(case_id):
    """复制用例"""
    user_id = get_jwt_identity()
    original = InterfaceTestCase.query.get(case_id)
    
    if not original:
        return jsonify({'error': '原用例不存在'}), 404
    if original.user_id != user_id and not original.is_public:
        return jsonify({'error': '无权限复制此用例'}), 403
    
    # 创建副本
    copy = InterfaceTestCase(
        user_id=user_id,
        folder_id=original.folder_id,
        name=f"{original.name} 副本",
        description=original.description,
        url=original.url,
        method=original.method,
        headers=original.headers,
        body=original.body,
        body_type=original.body_type,
        is_public=False
    )
    
    db.session.add(copy)
    db.session.commit()
    
    return jsonify({
        'message': '复制成功',
        'id': copy.id
    }), 201


def substitute_variables(content, variables):
    """替换环境变量，格式 {{variable}}，使用正则替换所有匹配的占位符"""
    if not content or not variables:
        return content

    # 如果 content 不是字符串（比如已经是 dict 对象），直接返回不替换
    # 替换只对字符串进行
    if not isinstance(content, str):
        return content

    def replace_match(match):
        var_name = match.group(1).strip()
        return str(variables.get(var_name, match.group(0)))

    # 使用正则替换所有 {{变量名}} 格式，变量名可以包含任意字符（除了 }}）
    return re.sub(r'\{\{(.*?)\}\}', replace_match, content)


@interface_test_bp.route('/interface-test/send', methods=['POST'])
@jwt_required(optional=True)
@limiter.limit("1000 per hour")
def send_request():
    """发送接口请求（代理执行，支持环境变量替换）"""
    data = request.get_json()

    if not data.get('url'):
        return jsonify({'error': 'URL不能为空'}), 400

    url = data['url'].strip()
    method = data.get('method', 'GET').upper()
    headers_str = data.get('headers', '{}')
    body = data.get('body', '')
    body_type = data.get('body_type', 'json')

    # 正确获取环境变量：支持两种方式
    # 1. 前端直接传 variables 对象
    # 2. 前端传 env_id，后端从数据库查询获取环境变量
    user_id = get_jwt_identity()
    env_variables = {}
    env_id = data.get('env_id')

    if env_id:
        # 根据 env_id 从数据库查询环境变量
        environment = InterfaceTestEnvironment.query.get(env_id)
        if environment and (environment.user_id == user_id or not user_id):
            # 解析环境变量，支持多种格式
            try:
                if environment.variables:
                    parsed_vars = json.loads(environment.variables)
                    if isinstance(parsed_vars, list):
                        # 列表格式 [{key: "k", value: "v"}, ...]
                        for item in parsed_vars:
                            if isinstance(item, dict) and 'key' in item and 'value' in item:
                                if item['key'].strip():
                                    env_variables[item['key'].strip()] = item['value']
                    elif isinstance(parsed_vars, dict):
                        # 字典格式 {key: value}
                        env_variables = parsed_vars
            except Exception as e:
                print(f"[DEBUG] Failed to parse environment variables: {e}")
                env_variables = {}
            # 添加 base_url 到环境变量（如果有）
            if environment.base_url and 'base_url' not in env_variables:
                env_variables['base_url'] = environment.base_url
    else:
        # 前端直接传 variables
        env_variables = data.get('variables', {})

    # 如果还是空，尝试获取用户的默认环境
    if not env_variables and user_id:
        default_env = InterfaceTestEnvironment.query.filter_by(user_id=user_id, is_default=True).first()
        if default_env:
            try:
                if default_env.variables:
                    parsed_vars = json.loads(default_env.variables)
                    if isinstance(parsed_vars, list):
                        for item in parsed_vars:
                            if isinstance(item, dict) and 'key' in item and 'value' in item:
                                if item['key'].strip():
                                    env_variables[item['key'].strip()] = item['value']
                    elif isinstance(parsed_vars, dict):
                        env_variables = parsed_vars
                if default_env.base_url and 'base_url' not in env_variables:
                    env_variables['base_url'] = default_env.base_url
            except:
                pass

    # 环境变量替换
    url = substitute_variables(url, env_variables)
    headers_str = substitute_variables(headers_str, env_variables)
    body = substitute_variables(body, env_variables)

    # Debug: print final URL and env_variables after substitution
    print(f"[DEBUG] Final URL after substitution: {url}")
    print(f"[DEBUG] env_variables resolved: {env_variables}")

    # URL 合法性强制校验
    # 检查是否仍然包含 {{ 占位符，说明替换失败
    if '{{' in url or '}}' in url:
        return jsonify({'error': f'环境变量替换失败，URL 中仍存在未替换的占位符: {url}'}), 400
    # 检查是否以 http:// 或 https:// 开头
    if not (url.startswith('http://') or url.startswith('https://')):
        return jsonify({'error': f'生成的 URL 不合法，必须以 http:// 或 https:// 开头: {url}'}), 400

#     # SSRF防护：验证URL，禁止访问内网地址
#     from urllib.parse import urlparse
#     import ipaddress
#     import socket
#     
#     try:
#         parsed = urlparse(url)
#         # 如果没有 scheme，自动添加 http://
#         if not parsed.scheme:
#             url = 'http://' + url
#             parsed = urlparse(url)
#         if parsed.scheme not in ['http', 'https']:
#             return jsonify({'error': '仅支持HTTP/HTTPS协议'}), 400
# 
#         hostname = parsed.hostname
#         if not hostname:
#             return jsonify({'error': '无效的URL'}), 400
#         
#         # 函数：检查IP是否为内网地址
#         # 开发环境允许 localhost/127.0.0.1，只阻止其他内网地址
#         def is_private_ip(ip_str):
#             try:
#                 ip = ipaddress.ip_address(ip_str)
#                 # 允许本地回环，禁止真正的内网网段
#                 if ip.is_loopback:
#                     return False  # 允许回环地址访问
#                 return ip.is_private or ip.is_reserved or ip.is_multicast
#             except ValueError:
#                 return False
# 
#         # 检查hostname本身就是IP地址
#         try:
#             if is_private_ip(hostname):
#                 return jsonify({'error': '禁止访问内网地址'}), 403
#         except ValueError:
#             pass
# 
#         # 检查常见内网域名 - 允许 localhost 在开发环境使用
#         # internal_domains = ['localhost', '127.0.0.1', '0.0.0.0', '::1']
#         # if hostname.lower() in internal_domains:
#         #    return jsonify({'error': '禁止访问内网地址'}), 403
#         
#         # 检查hostname中是否包含内网IP模式
#         private_pattern = r'(?:10|127|192\.168)(?:\.\d+){3}|172\.(?:1[6-9]|2[0-9]|3[01])\.\d+\.\d+'
#         if re.search(private_pattern, hostname):
#             return jsonify({'error': '禁止访问内网地址'}), 403
#         
#         # 解析域名获取所有IP地址，逐个检查（防止绕过，比如 user@ip 这种URL格式）
#         try:
#             addr_infos = socket.getaddrinfo(hostname, None)
#             for addr_info in addr_infos:
#                 ip_addr = addr_info[4][0]
#                 # 分离IP地址（IPv6可能带端口）
#                 clean_ip = ip_addr.split('%')[0].lstrip('[').rstrip(']')
#                 if is_private_ip(clean_ip):
#                     return jsonify({'error': '禁止访问内网地址'}), 403
#         except Exception:
#             # 如果解析失败，默认允许（域名解析失败通常不会命中内网）
#             pass
#     except Exception as e:
#         return jsonify({'error': f'URL解析错误: {str(e)}'}), 400
    
    # 解析请求头 - 兼容字符串和对象两种格式
    try:
        if headers_str:
            if isinstance(headers_str, str):
                headers = json.loads(headers_str)
            elif isinstance(headers_str, dict):
                headers = headers_str
            else:
                headers = {}
        else:
            headers = {}
    except json.JSONDecodeError as e:
        return jsonify({'error': f'请求头JSON格式错误: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': f'请求头解析错误: {str(e)}'}), 400

    # 🔥 战役一：自动注入 Authorization Token
    # 如果环境变量中有 token 字段，且 headers 中还没有 Authorization，自动添加 Bearer token
    if 'token' in env_variables and 'Authorization' not in headers:
        token_value = str(env_variables['token']).strip()
        if token_value:
            # 如果 token 已经以 Bearer 开头，直接使用；否则添加 Bearer 前缀
            if token_value.lower().startswith('bearer '):
                headers['Authorization'] = token_value
            else:
                headers['Authorization'] = f'Bearer {token_value}'

    # 🔥 战役二：智能注入 Content-Type
    # 如果用户选择 JSON/raw 类型且没有手动设置 Content-Type，自动添加 application/json
    if body_type in ['json', 'raw'] and body:
        # 检查用户是否已经手动设置了 content-type（忽略大小写）
        has_content_type = any(k.lower() == 'content-type' for k in headers.keys())
        if not has_content_type:
            headers['Content-Type'] = 'application/json'

    # 准备请求参数
    request_kwargs = {
        'headers': headers,
        'timeout': 30,  # 30秒超时
        'allow_redirects': True
    }
    
    # 处理请求体
    if method in ['POST', 'PUT', 'PATCH', 'DELETE'] and body:
        if body_type == 'json':
            try:
                # body是字符串，尝试解析为JSON
                if body.strip():
                    request_kwargs['json'] = json.loads(body)
            except json.JSONDecodeError as e:
                return jsonify({'error': f'JSON格式错误: {str(e)}'}), 400
            if not body.strip():
                request_kwargs['data'] = ''
        elif body_type == 'form':
            # form-urlencoded
            try:
                request_kwargs['data'] = json.loads(body)
            except json.JSONDecodeError as e:
                return jsonify({'error': f'表单数据JSON格式错误: {str(e)}'}), 400
        elif body_type == 'form-data':
            # multipart/form-data 暂不支持文件上传，后续完善
            try:
                request_kwargs['data'] = json.loads(body)
            except json.JSONDecodeError as e:
                return jsonify({'error': f'form-data格式错误: {str(e)}'}), 400
        else:  # text / raw
            # 确保正确编码为 UTF-8 bytes
            if isinstance(body, str):
                request_kwargs['data'] = body.encode('utf-8')
            else:
                request_kwargs['data'] = body
    
    try:
        # 发送请求
        start_time = datetime.now()
        response = requests.request(method, url, **request_kwargs)
        end_time = datetime.now()
        
        # 计算耗时（毫秒）
        elapsed_ms = int((end_time - start_time).total_seconds() * 1000)
        
        # 获取响应头
        response_headers = dict(response.headers)
        
        # 获取响应内容
        response_text = response.text
        # 尝试解析JSON格式化
        try:
            response_json = response.json()
            response_content = json.dumps(response_json, indent=2, ensure_ascii=False)
        except ValueError:
            response_json = None
            response_content = response_text
        
        return jsonify({
            'status_code': response.status_code,
            'elapsed_ms': elapsed_ms,
            'headers': response_headers,
            'content_type': response.headers.get('Content-Type', ''),
            'response_text': response_text,
            'response_content': response_content,
            'response_json': response_json
        })
    
    except requests.exceptions.MissingSchema:
        return jsonify({
            "code": 400,
            "msg": f"请求执行失败：URL格式错误，请包含 http:// 或 https://",
            "error": f"URL格式错误，请包含 http:// 或 https://",
            "data": None
        }), 200
    except requests.exceptions.InvalidURL:
        return jsonify({
            "code": 400,
            "msg": "请求执行失败：URL无效",
            "error": "URL无效",
            "data": None
        }), 200
    except requests.exceptions.ConnectionError:
        return jsonify({
            "code": 400,
            "msg": "请求执行失败：连接被拒绝。请检查『环境管理』中的 Base URL 和端口号是否正确启动！",
            "error": "连接失败，请检查URL和网络",
            "data": None
        }), 200
    except requests.exceptions.Timeout:
        return jsonify({
            "code": 400,
            "msg": "请求执行失败：接口响应超时！",
            "error": "请求超时（30秒）",
            "data": None
        }), 200
    except requests.exceptions.RequestException as e:
        return jsonify({
            "code": 400,
            "msg": f"请求执行抛出异常: {str(e)}",
            "error": f"请求执行失败: {str(e)}",
            "data": None
        }), 200
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"服务器内部测试引擎出错: {str(e)}",
            "error": f"请求发送失败: {str(e)}",
            "data": None
        }), 500


# 公开接口 - 获取公开用例列表
@interface_test_bp.route('/interface-test/public', methods=['GET'])
def get_public_cases():
    """获取公开的接口测试用例列表"""
    cases = InterfaceTestCase.query\
        .filter_by(is_public=True)\
        .order_by(InterfaceTestCase.updated_at.desc())\
        .limit(50)\
        .all()
    
    result = []
    for case in cases:
        result.append({
            'id': case.id,
            'name': case.name,
            'description': case.description,
            'url': case.url,
            'method': case.method,
            'body_type': case.body_type,
            'user_id': case.user_id,
            'created_at': case.created_at.isoformat() if case.created_at else None,
            'updated_at': case.updated_at.isoformat() if case.updated_at else None
        })
    
    return jsonify(result)


# ============ 测试计划管理 ============

# 获取用户的测试计划列表
@interface_test_bp.route('/interface-test/plans', methods=['GET'])
@jwt_required()
def get_plans():
    """获取当前用户的所有测试计划"""
    user_id = get_jwt_identity()
    plans = InterfaceTestPlan.query\
        .filter_by(user_id=user_id)\
        .order_by(InterfaceTestPlan.updated_at.desc())\
        .all()
    
    result = []
    for plan in plans:
        # 解析 case_ids
        case_ids = json.loads(plan.case_ids) if plan.case_ids else []
        result.append({
            'id': plan.id,
            'name': plan.name,
            'description': plan.description,
            'case_ids': case_ids,
            'case_count': len(case_ids),
            'environment_id': plan.environment_id,
            'created_at': plan.created_at.isoformat() if plan.created_at else None,
            'updated_at': plan.updated_at.isoformat() if plan.updated_at else None
        })
    
    return jsonify(result)


# 创建测试计划
@interface_test_bp.route('/interface-test/plans', methods=['POST'])
@jwt_required()
@limiter.limit("1000 per hour")
def create_plan():
    """创建新的测试计划"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data.get('name'):
        return jsonify({'error': '计划名称不能为空'}), 400
    
    case_ids = data.get('case_ids', [])
    if not case_ids or len(case_ids) == 0:
        return jsonify({'error': '至少选择一个用例'}), 400
    
    plan = InterfaceTestPlan(
        user_id=user_id,
        name=data['name'],
        description=data.get('description', ''),
        case_ids=json.dumps(case_ids, ensure_ascii=False),
        environment_id=data.get('environment_id')
    )
    
    db.session.add(plan)
    db.session.commit()
    
    return jsonify({
        'id': plan.id,
        'name': plan.name,
        'description': plan.description,
        'case_ids': case_ids,
        'environment_id': plan.environment_id,
        'created_at': plan.created_at.isoformat() if plan.created_at else None,
        'updated_at': plan.updated_at.isoformat() if plan.updated_at else None
    })


# 更新测试计划
@interface_test_bp.route('/interface-test/plans/<int:plan_id>', methods=['PUT'])
@jwt_required()
@limiter.limit("1000 per hour")
def update_plan(plan_id):
    """更新测试计划"""
    user_id = get_jwt_identity()
    plan = InterfaceTestPlan.query.filter_by(id=plan_id, user_id=user_id).first()
    
    if not plan:
        return jsonify({'error': '计划不存在'}), 404
    
    data = request.get_json()
    
    if 'name' in data and data['name']:
        plan.name = data['name']
    if 'description' in data:
        plan.description = data['description']
    if 'case_ids' in data:
        plan.case_ids = json.dumps(data['case_ids'], ensure_ascii=False)
    if 'environment_id' in data:
        plan.environment_id = data['environment_id']
    
    db.session.commit()
    
    return jsonify({'success': True})


# 删除测试计划
@interface_test_bp.route('/interface-test/plans/<int:plan_id>', methods=['DELETE'])
@jwt_required()
@limiter.limit("1000 per hour")
def delete_plan(plan_id):
    """删除测试计划"""
    user_id = get_jwt_identity()
    plan = InterfaceTestPlan.query.filter_by(id=plan_id, user_id=user_id).first()
    
    if not plan:
        return jsonify({'error': '计划不存在'}), 404
    
    db.session.delete(plan)
    db.session.commit()
    
    return jsonify({'success': True})


# 获取测试计划详情（包含完整用例信息）
@interface_test_bp.route('/interface-test/plans/<int:plan_id>', methods=['GET'])
@jwt_required()
def get_plan_detail(plan_id):
    """获取测试计划详情，包含完整用例信息用于执行"""
    user_id = get_jwt_identity()
    plan = InterfaceTestPlan.query.filter_by(id=plan_id, user_id=user_id).first()
    
    if not plan:
        return jsonify({'error': '计划不存在'}), 404
    
    case_ids = json.loads(plan.case_ids) if plan.case_ids else []
    # 获取完整的用例信息
    cases = []
    for case_id in case_ids:
        case = InterfaceTestCase.query.filter_by(id=case_id, user_id=user_id).first()
        if case:
            cases.append({
                'id': case.id,
                'name': case.name,
                'description': case.description,
                'url': case.url,
                'method': case.method,
                'headers': case.headers,
                'body': case.body,
                'body_type': case.body_type
            })
    
    return jsonify({
        'id': plan.id,
        'name': plan.name,
        'description': plan.description,
        'case_ids': case_ids,
        'cases': cases,
        'environment_id': plan.environment_id,
        'created_at': plan.created_at.isoformat() if plan.created_at else None,
        'updated_at': plan.updated_at.isoformat() if plan.updated_at else None
    })


# ============ 测试报告管理 ============

# 执行测试计划并保存报告
@interface_test_bp.route('/interface-test/plans/<int:plan_id>/execute', methods=['POST'])
@jwt_required()
@limiter.limit("10000 per hour")
def execute_plan(plan_id):
    """执行测试计划并保存报告"""
    user_id = get_jwt_identity()
    plan = InterfaceTestPlan.query.filter_by(id=plan_id, user_id=user_id).first()

    if not plan:
        return jsonify({'error': '计划不存在'}), 404

    # 获取环境变量
    env_variables = {}
    environment = None
    if plan.environment_id:
        environment = InterfaceTestEnvironment.query.get(plan.environment_id)
    if not environment:
        # 获取默认环境
        environment = InterfaceTestEnvironment.query.filter_by(user_id=user_id, is_default=True).first()
    if not environment:
        environment = InterfaceTestEnvironment.query.filter_by(user_id=user_id).first()

    if environment:
        if environment.variables:
            try:
                parsed_vars = json.loads(environment.variables)
                if isinstance(parsed_vars, list):
                    # 列表格式 [{key: "k", value: "v"}, ...]
                    for item in parsed_vars:
                        if isinstance(item, dict) and 'key' in item and 'value' in item:
                            if item['key'].strip():
                                env_variables[item['key'].strip()] = item['value']
                elif isinstance(parsed_vars, dict):
                    # 字典格式 {key: value}
                    env_variables = parsed_vars
            except Exception as e:
                print(f"[DEBUG] Failed to parse environment variables in execute_plan: {e}")
                pass
        if environment.base_url and 'base_url' not in env_variables:
            env_variables['base_url'] = environment.base_url

    # 解析用例ID
    case_ids = json.loads(plan.case_ids) if plan.case_ids else []

    # 创建报告
    report = InterfaceTestReport(
        user_id=user_id,
        plan_id=plan.id,
        plan_name=plan.name,
        status='running'
    )
    db.session.add(report)
    db.session.flush()  # 获取 report.id

    results = []
    success_count = 0
    failed_count = 0
    total_time = 0

    for case_id in case_ids:
        case = InterfaceTestCase.query.filter_by(id=case_id, user_id=user_id).first()
        if not case:
            continue

        case_result = {
            'id': case.id,
            'name': case.name,
            'method': case.method,
            'url': case.url,
            'status': 0,
            'success': False,
            'time': 0,
            'error': '',
            'request_headers': {},
            'request_body': case.body or '',
            'response': None,
            'response_headers': None
        }

        start_time = datetime.utcnow()

        try:
            # 替换变量 - 使用统一的 substitute_variables 函数（正则替换）
            url = substitute_variables(case.url, env_variables)

            headers = {}
            if case.headers:
                try:
                    headers_str = substitute_variables(case.headers, env_variables)
                    headers = json.loads(headers_str)
                except:
                    # 如果解析失败，保持原样
                    if isinstance(case.headers, dict):
                        headers = case.headers
                pass
            case_result['request_headers'] = headers

            body = substitute_variables(case.body or '', env_variables)

            # URL 合法性强制校验
            if '{{' in url or '}}' in url:
                case_result['success'] = False
                case_result['error'] = f'环境变量替换失败，URL 中仍存在未替换的占位符: {url}'
                failed_count += 1
                elapsed_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
                case_result['time'] = elapsed_ms
                total_time += case_result['time']
                # 保存结果到数据库
                result_record = InterfaceTestReportResult(
                    report_id=report.id,
                    case_id=case.id,
                    case_name=case.name,
                    method=case.method,
                    url=case.url,
                    status_code=case_result['status'],
                    success=case_result['success'],
                    time=case_result['time'],
                    error=case_result['error'],
                    request_headers=json.dumps(case_result['request_headers'], ensure_ascii=False) if case_result['request_headers'] else None,
                    request_body=case_result['request_body'],
                    response=case_result['response'],
                    response_headers=json.dumps(case_result['response_headers'], ensure_ascii=False) if case_result['response_headers'] else None
                )
                db.session.add(result_record)
                results.append(case_result)
                continue

            if not (url.startswith('http://') or url.startswith('https://')):
                case_result['success'] = False
                case_result['error'] = f'生成的 URL 不合法，必须以 http:// 或 https:// 开头: {url}'
                failed_count += 1
                elapsed_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
                case_result['time'] = elapsed_ms
                total_time += case_result['time']
                # 保存结果到数据库
                result_record = InterfaceTestReportResult(
                    report_id=report.id,
                    case_id=case.id,
                    case_name=case.name,
                    method=case.method,
                    url=case.url,
                    status_code=case_result['status'],
                    success=case_result['success'],
                    time=case_result['time'],
                    error=case_result['error'],
                    request_headers=json.dumps(case_result['request_headers'], ensure_ascii=False) if case_result['request_headers'] else None,
                    request_body=case_result['request_body'],
                    response=case_result['response'],
                    response_headers=json.dumps(case_result['response_headers'], ensure_ascii=False) if case_result['response_headers'] else None
                )
                db.session.add(result_record)
                results.append(case_result)
                continue

            # 发送请求
            req_kwargs = {
                'method': case.method,
                'url': url,
                'headers': headers if headers else {},
                'timeout': 30
            }

            if case.method in ['POST', 'PUT', 'PATCH'] and body:
                if case.body_type == 'json':
                    try:
                        req_kwargs['json'] = json.loads(body)
                    except:
                        req_kwargs['data'] = body
                else:
                    req_kwargs['data'] = body

            resp = requests.request(**req_kwargs)
            elapsed_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

            case_result['status'] = resp.status_code
            case_result['time'] = elapsed_ms
            case_result['success'] = 200 <= resp.status_code < 300
            case_result['response'] = resp.text[:10000]  # 限制响应长度
            case_result['response_headers'] = dict(resp.headers)

            if case_result['success']:
                success_count += 1
            else:
                failed_count += 1

        except Exception as e:
            elapsed_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            case_result['time'] = elapsed_ms
            case_result['success'] = False
            case_result['error'] = str(e)
            failed_count += 1

        total_time += case_result['time']

        # 保存结果到数据库
        result_record = InterfaceTestReportResult(
            report_id=report.id,
            case_id=case.id,
            case_name=case.name,
            method=case.method,
            url=case.url,
            status_code=case_result['status'],
            success=case_result['success'],
            time=case_result['time'],
            error=case_result['error'],
            request_headers=json.dumps(case_result['request_headers'], ensure_ascii=False) if case_result['request_headers'] else None,
            request_body=case_result['request_body'],
            response=case_result['response'],
            response_headers=json.dumps(case_result['response_headers'], ensure_ascii=False) if case_result['response_headers'] else None
        )
        db.session.add(result_record)
        results.append(case_result)

    # 更新报告状态
    report.total_count = len(case_ids)
    report.success_count = success_count
    report.failed_count = failed_count
    report.total_time = total_time
    report.status = 'completed'
    db.session.commit()

    return jsonify({
        'report_id': report.id,
        'plan_id': plan.id,
        'plan_name': plan.name,
        'total': len(case_ids),
        'success': success_count,
        'failed': failed_count,
        'totalTime': total_time,
        'results': results
    })


# 获取测试报告列表
@interface_test_bp.route('/interface-test/reports', methods=['GET'])
@jwt_required()
def get_reports():
    """获取当前用户的所有测试报告"""
    user_id = get_jwt_identity()
    # 处理空字符串安全转换为int
    page_str = request.args.get('page')
    per_page_str = request.args.get('per_page')

    page = 1
    if page_str and page_str != '':
        try:
            page = int(page_str)
        except (ValueError, TypeError):
            page = 1

    per_page = 20
    if per_page_str and per_page_str != '':
        try:
            per_page = int(per_page_str)
        except (ValueError, TypeError):
            per_page = 20

    reports = InterfaceTestReport.query\
        .filter_by(user_id=user_id)\
        .order_by(InterfaceTestReport.executed_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)

    result = []
    for report in reports.items:
        result.append({
            'id': report.id,
            'plan_id': report.plan_id,
            'plan_name': report.plan_name,
            'total': report.total_count,
            'success': report.success_count,
            'failed': report.failed_count,
            'total_time': report.total_time,
            'status': report.status,
            'executed_at': report.executed_at.isoformat() if report.executed_at else None
        })

    return jsonify({
        'data': result,
        'total': reports.total,
        'page': reports.page,
        'pages': reports.pages
    })


# 获取测试报告详情
@interface_test_bp.route('/interface-test/reports/<int:report_id>', methods=['GET'])
@jwt_required()
def get_report_detail(report_id):
    """获取测试报告详情，包含每个用例的执行结果"""
    user_id = get_jwt_identity()
    report = InterfaceTestReport.query.filter_by(id=report_id, user_id=user_id).first()

    if not report:
        return jsonify({'error': '报告不存在'}), 404

    results = []
    for r in report.results:
        results.append({
            'id': r.id,
            'case_id': r.case_id,
            'case_name': r.case_name,
            'method': r.method,
            'url': r.url,
            'status': r.status_code,
            'success': r.success,
            'time': r.time,
            'error': r.error,
            'request_headers': json.loads(r.request_headers) if r.request_headers else {},
            'request_body': r.request_body,
            'response': r.response,
            'response_headers': json.loads(r.response_headers) if r.response_headers else None,
            'executed_at': r.executed_at.isoformat() if r.executed_at else None
        })

    return jsonify({
        'id': report.id,
        'plan_id': report.plan_id,
        'plan_name': report.plan_name,
        'total': report.total_count,
        'success': report.success_count,
        'failed': report.failed_count,
        'total_time': report.total_time,
        'status': report.status,
        'executed_at': report.executed_at.isoformat() if report.executed_at else None,
        'results': results
    })


# 删除测试报告
@interface_test_bp.route('/interface-test/reports/<int:report_id>', methods=['DELETE'])
@jwt_required()
def delete_report(report_id):
    """删除测试报告"""
    user_id = get_jwt_identity()
    report = InterfaceTestReport.query.filter_by(id=report_id, user_id=user_id).first()

    if not report:
        return jsonify({'error': '报告不存在'}), 404

    db.session.delete(report)
    db.session.commit()

    return jsonify({'success': True})
