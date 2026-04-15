"""Update existing choice exercises with ABCD options in description"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from fastapi_backend.core.config import settings
from fastapi_backend.models.models import Exercise

DATABASE_URL = settings.DATABASE_URL
engine = create_async_engine(DATABASE_URL, echo=False)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

CHOICE_UPDATES = {
    "软件测试的定义与目的": {
        "description": "理解软件测试的核心定义，区分验证(Verification)和确认(Validation)的概念，掌握测试的终极目标。\n\nA. 软件测试的目的是证明软件没有缺陷\nB. 软件测试的目的是发现软件中的缺陷，同时评估软件质量\nC. 软件测试的目的是确保软件100%正确\nD. 软件测试的目的是找开发人员的错误",
    },
    "测试原则 - 杀虫剂悖论": {
        "description": "杀虫剂悖论是软件测试的重要原则之一：如果反复使用相同的测试用例集，最终将无法发现新的缺陷。请问以下哪种做法最能应对杀虫剂悖论？\n\nA. 增加测试用例的数量\nB. 定期评审和修改测试用例，增加新的测试场景\nC. 减少测试用例数量，只保留核心用例\nD. 完全依赖自动化测试",
    },
    "黑盒测试与白盒测试的区别": {
        "description": "黑盒测试和白盒测试是两种基本的测试方法。黑盒测试关注输入和输出，不考虑内部结构；白盒测试关注程序内部逻辑结构。以下关于两者的说法，哪个是正确的？\n\nA. 黑盒测试不需要了解需求规格说明，白盒测试需要了解代码实现\nB. 黑盒测试和白盒测试可以互相替代，选择一种即可\nC. 白盒测试只能由开发人员执行，测试人员无法进行\nD. 黑盒测试只能发现功能缺陷，无法发现性能问题",
    },
    "缺陷的严重程度与优先级": {
        "description": "缺陷管理中，严重程度(Severity)和优先级(Priority)是两个重要概念。一个导致系统崩溃的偶发缺陷，严重程度应该是什么级别？\n\nA. 致命(Fatal) - 系统崩溃、数据丢失等\nB. 严重(Critical) - 主要功能不可用\nC. 一般(Major) - 次要功能问题\nD. 轻微(Minor) - 界面显示等小问题",
    },
    "V模型中的测试阶段": {
        "description": "V模型是经典的软件开发模型，它将测试活动与开发活动对应起来。在V模型中，系统测试对应哪个开发阶段？\n\nA. 需求分析\nB. 概要设计\nC. 系统设计/概要设计\nD. 编码",
    },
    "HTTP状态码识别": {
        "description": "HTTP状态码是Web测试中最常见的概念。当服务器返回404状态码时，表示什么含义？\n\nA. 服务器内部错误\nB. 请求的资源未找到\nC. 请求被重定向\nD. 请求成功",
    },
    "GET与POST请求的区别": {
        "description": "GET和POST是HTTP最常用的两种请求方法。以下关于GET和POST的说法，哪个是错误的？\n\nA. GET请求参数在URL中，POST请求参数在请求体中\nB. GET请求有长度限制，POST请求理论上没有限制\nC. GET请求可以被缓存，POST请求不会被缓存\nD. POST请求比GET请求更安全，绝对不会被拦截",
    },
    "TCP三次握手": {
        "description": "TCP建立连接需要三次握手。请描述三次握手的过程：第一次握手客户端发送什么标志位的报文？\n\nA. SYN\nB. ACK\nC. SYN+ACK\nD. FIN",
    },
    "文件权限chmod命令": {
        "description": "在Linux中，chmod 755 file.txt 命令将文件权限设置为什么？请解释755各数字的含义。\n\nA. 所有者：读+写+执行(7)；所属组：读+执行(5)；其他用户：读+执行(5)\nB. 所有者：读+写(7)；所属组：读+写(5)；其他用户：读+写(5)\nC. 所有者：读+执行(7)；所属组：写+执行(5)；其他用户：读(5)\nD. 所有者：写+执行(7)；所属组：读+写(5)；其他用户：执行(5)",
    },
    "等价类划分法实战": {
        "description": "某系统要求用户输入年龄，有效范围是18-60岁。请使用等价类划分法，划分出有效等价类和无效等价类。\n\nA. 有效等价类：18-60；无效等价类：小于18、大于60\nB. 有效等价类：18-60；无效等价类：小于18、大于60、非数字输入\nC. 有效等价类：1-100；无效等价类：其他\nD. 有效等价类：18、60；无效等价类：17、61",
    },
    "边界值分析法": {
        "description": "一个文本框允许输入1-100之间的整数。使用边界值分析法，应该测试哪些边界值？\n\nA. 1和100\nB. 0、1、100、101\nC. 0、1、2、99、100、101\nD. 1、50、100",
    },
    "场景法设计测试用例": {
        "description": "电商下单流程：用户登录→浏览商品→加入购物车→填写地址→选择支付方式→确认支付。请使用场景法设计测试场景，以下哪个是异常场景？\n\nA. 用户登录后浏览商品并成功下单\nB. 用户未登录直接访问购物车\nC. 用户选择货到付款方式完成订单\nD. 用户支付时余额不足导致支付失败",
    },
    "因果图法应用": {
        "description": "某注册页面有如下规则：①用户名不能为空 ②密码长度6-16位 ③确认密码必须与密码一致 ④手机号必须是11位数字。请使用因果图法分析，以下哪个测试用例覆盖了'密码长度不足6位且手机号格式错误'的组合？\n\nA. 用户名为空，密码5位，确认密码5位，手机号10位\nB. 用户名填写，密码5位，确认密码5位，手机号abc12345678\nC. 用户名填写，密码8位，确认密码8位，手机号11位\nD. 用户名为空，密码8位，确认密码7位，手机号11位",
    },
    "测试计划核心要素": {
        "description": "一份完整的测试计划文档应包含哪些核心要素？以下哪个不属于测试计划的必要组成部分？\n\nA. 测试范围和测试策略\nB. 测试资源和进度安排\nC. 风险评估和应对措施\nD. 开发人员的绩效考核标准",
    },
    "测试风险评估": {
        "description": "在项目测试过程中，以下哪种风险属于项目风险（而非产品风险）？\n\nA. 软件存在严重的安全漏洞\nB. 测试人员不足导致测试进度延迟\nC. 系统性能未达到预期指标\nD. 用户界面不符合设计规范",
    },
    "RESTful API设计规范": {
        "description": "RESTful API遵循特定的设计规范。以下哪个URL设计符合RESTful规范，用于获取ID为123的用户信息？\n\nA. GET /api/users/123\nB. POST /api/users/123\nC. GET /api/getUser?id=123\nD. GET /api/users?action=get&id=123",
    },
    "接口测试用例设计": {
        "description": "对一个登录接口 POST /api/login (参数: username, password) 进行测试，以下哪个不属于必须测试的场景？\n\nA. 正确的用户名和密码登录\nB. 空用户名或空密码登录\nC. 用户名包含特殊字符\nD. 登录后浏览器的Cookie设置方式",
    },
    "Selenium元素定位": {
        "description": "在Selenium中，以下哪种定位方式是最推荐的，因为它最稳定且性能最好？\n\nA. By.ID\nB. By.XPATH\nC. By.CSS_SELECTOR\nD. By.NAME",
    },
    "显式等待与隐式等待": {
        "description": "Selenium中有两种等待机制。以下关于显式等待(WebDriverWait)和隐式等待(implicitly_wait)的说法，哪个是正确的？\n\nA. 隐式等待比显式等待更灵活，推荐优先使用\nB. 显式等待和隐式等待可以同时使用，效果叠加\nC. 显式等待针对特定条件等待，更灵活可控；隐式等待对全局生效\nD. 显式等待只能等待元素出现，不能等待元素可点击",
    },
    "POM设计模式": {
        "description": "页面对象模型(POM)是UI自动化测试的最佳实践。以下关于POM的说法，哪个是错误的？\n\nA. POM将页面元素定位和操作封装在独立的类中\nB. POM提高了测试脚本的可维护性和可复用性\nC. POM中页面类的修改不需要改动测试用例代码\nD. POM要求每个测试用例都必须创建新的页面类实例",
    },
    "接口自动化框架分层": {
        "description": "企业级接口自动化框架通常采用分层设计。以下哪个不属于标准的框架分层？\n\nA. API层 - 封装接口请求\nB. 业务层 - 组合接口实现业务流程\nC. 数据层 - 管理测试数据\nD. UI层 - 处理页面元素操作",
    },
    "性能测试核心指标": {
        "description": "性能测试中，TPS(Transactions Per Second)和QPS(Queries Per Second)是两个重要指标。以下关于它们的说法，哪个是正确的？\n\nA. TPS和QPS完全相同，只是叫法不同\nB. TPS衡量事务处理能力，QPS衡量查询处理能力，TPS通常包含QPS\nC. QPS一定大于TPS\nD. TPS只适用于数据库测试",
    },
    "SQL注入识别": {
        "description": "以下哪个输入最可能是SQL注入攻击的尝试？\n\nA. 张三\nB. test123\nC. ' OR 1=1 --\nD. 13800138000",
    },
    "XSS攻击类型": {
        "description": "XSS(跨站脚本)攻击分为存储型、反射型和DOM型三种。以下关于三种类型的说法，哪个是正确的？\n\nA. 存储型XSS的恶意脚本保存在服务器端，所有访问该页面的用户都会受到影响\nB. 反射型XSS的危害最大，因为它可以永久存储\nC. DOM型XSS需要服务器端参与处理\nD. 三种XSS的防御方法完全相同",
    },
    "CSRF防护机制": {
        "description": "CSRF(跨站请求伪造)是一种常见的Web安全漏洞。以下哪种方式是最常用的CSRF防护手段？\n\nA. 使用HTTPS协议\nB. 使用CSRF Token验证\nC. 限制IP访问\nD. 使用验证码",
    },
    "AI测试应用场景": {
        "description": "AI在软件测试中有多种应用场景。以下哪个不是目前AI在测试领域的主要应用方向？\n\nA. AI辅助测试用例自动生成\nB. 视觉回归测试自动对比\nC. 智能缺陷预测和根因分析\nD. AI完全替代人工测试，无需人类参与",
    },
    "视觉回归测试原理": {
        "description": "视觉回归测试(Visual Regression Testing)通过对比截图来发现UI变化。以下关于视觉回归测试的说法，哪个是正确的？\n\nA. 视觉回归测试只能发现功能缺陷\nB. 视觉回归测试通过像素级对比基准图和实际截图来发现UI变化\nC. 视觉回归测试不需要维护基准图\nD. 视觉回归测试只能用于Web应用",
    },
    "Docker基础命令": {
        "description": "Docker是容器化部署的核心工具。以下哪个命令用于构建Docker镜像？\n\nA. docker build -t image_name .\nB. docker run image_name\nC. docker pull image_name\nD. docker push image_name",
    },
    "Jenkins Pipeline语法": {
        "description": "Jenkins Pipeline使用Groovy DSL定义流水线。以下哪个是声明式Pipeline的正确结构？\n\nA. pipeline { stage('Build') { sh 'make' } }\nB. pipeline { stages { stage('Build') { steps { sh 'make' } } } }\nC. node { stage('Build') { sh 'make' } }\nD. job('Build') { steps { sh 'make' } }",
    },
    "质量度量指标设计": {
        "description": "构建质量度量体系是测试架构师的核心能力。以下哪个指标最适合衡量代码质量？\n\nA. 代码行数(LOC)\nB. Bug数量\nC. 代码覆盖率(Code Coverage)\nD. 开发人员数量",
    },
}


async def update_choices():
    async with async_session() as session:
        updated = 0
        for title, updates in CHOICE_UPDATES.items():
            stmt = select(Exercise).where(Exercise.title == title)
            result = await session.execute(stmt)
            exercise = result.scalar_one_or_none()
            if exercise:
                for key, value in updates.items():
                    setattr(exercise, key, value)
                updated += 1
                print(f"  [OK] Updated: {title}")
            else:
                print(f"  [SKIP] Not found: {title}")

        await session.commit()
        print(f"\n[DONE] Updated {updated} exercises with choice options")


if __name__ == "__main__":
    print("=" * 60)
    print("[START] Updating choice exercises with ABCD options...")
    print("=" * 60)
    asyncio.run(update_choices())
