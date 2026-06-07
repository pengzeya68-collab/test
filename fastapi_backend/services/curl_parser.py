"""
cURL 命令解析器

功能：
- 解析 cURL 命令为结构化的请求数据
- 支持 -X, -H, -d, --data-raw, -u, --url 等参数
"""

import shlex
from urllib.parse import unquote
from typing import Any, Dict


def parse_curl(curl_string: str) -> Dict[str, Any]:
    """
    解析 cURL 命令字符串，返回结构化数据。

    返回格式:
    {
        "method": "POST",
        "url": "https://api.example.com/users",
        "headers": {"Content-Type": "application/json", "Authorization": "Bearer xxx"},
        "body": {"name": "test"},
        "body_type": "raw",
        "content_type": "application/json"
    }
    """
    if not curl_string or not curl_string.strip():
        raise ValueError("cURL 命令不能为空")

    # 预处理：移除反斜杠续行符
    curl_string = curl_string.replace("\\\n", " ").replace("\\\r\n", " ")
    curl_string = curl_string.strip()

    # 移除开头的 curl 命令
    if curl_string.startswith("curl "):
        curl_string = curl_string[5:]
    elif curl_string == "curl":
        raise ValueError("cURL 命令不完整")

    # 使用 shlex 分词（处理引号）
    try:
        tokens = shlex.split(curl_string)
    except ValueError:
        # 如果 shlex 解析失败（比如引号不匹配），用简单分割
        tokens = curl_string.split()

    method = "GET"
    url = ""
    headers = {}
    body = None
    body_str = None
    body_type = "none"
    content_type = "application/json"

    i = 0
    while i < len(tokens):
        token = tokens[i]

        if token in ("-X", "--request"):
            i += 1
            if i < len(tokens):
                method = tokens[i].upper()

        elif token in ("-H", "--header"):
            i += 1
            if i < len(tokens):
                header_str = tokens[i]
                if ":" in header_str:
                    key, value = header_str.split(":", 1)
                    headers[key.strip()] = value.strip()

        elif token in ("-d", "--data", "--data-raw", "--data-binary", "--data-urlencode"):
            i += 1
            if i < len(tokens):
                data_str = tokens[i]
                if method == "GET":
                    method = "POST"  # 有 body 时默认改为 POST

                # 合并多个 -d 参数
                if body_str:
                    body_str += "&" + data_str
                else:
                    body_str = data_str

                # 尝试解析为 JSON
                try:
                    import json

                    body = json.loads(body_str)
                    body_type = "raw"
                    content_type = "application/json"
                except (json.JSONDecodeError, ValueError):
                    # 尝试解析为 form data（支持单参数和多参数）
                    if "=" in body_str:
                        body = {}
                        for pair in body_str.split("&"):
                            if "=" in pair:
                                k, v = pair.split("=", 1)
                                body[unquote(k)] = unquote(v)
                        body_type = "form-data"
                        content_type = "application/x-www-form-urlencoded"
                    else:
                        body = body_str
                        body_type = "raw"

        elif token in ("-u", "--user"):
            i += 1
            if i < len(tokens):
                import base64

                auth_str = tokens[i]
                encoded = base64.b64encode(auth_str.encode()).decode()
                headers["Authorization"] = f"Basic {encoded}"

        elif token == "--url":
            i += 1
            if i < len(tokens):
                url = tokens[i]

        elif not token.startswith("-"):
            # 没有前缀的参数通常是 URL
            if not url and ("." in token or token.startswith("http") or token.startswith("/")):
                url = token

        elif token in ("-k", "--insecure"):
            pass  # 忽略 SSL 验证

        elif token in ("-s", "--silent", "-S", "--show-error", "-v", "--verbose", "-i", "--include"):
            pass  # 忽略输出控制参数

        elif token.startswith("--"):
            # 未知的长参数，跳过
            pass

        i += 1

    if not url:
        raise ValueError("未能从 cURL 命令中解析出 URL")

    # 确定 Content-Type
    if "Content-Type" in headers:
        content_type = headers["Content-Type"]
    elif "content-type" in headers:
        content_type = headers["content-type"]

    return {
        "method": method,
        "url": url,
        "headers": headers,
        "body": body,
        "body_type": body_type,
        "content_type": content_type,
    }
