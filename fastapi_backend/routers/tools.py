"""
测试工具导航路由
"""

from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/tools", tags=["工具导航"])

# 内置测试工具数据
TOOL_CATEGORIES = [
    {
        "id": "api_testing",
        "name": "接口测试",
        "icon": "Connection",
        "tools": [
            {
                "name": "Postman",
                "desc": "最流行的API开发和测试工具，支持REST/SOAP/GraphQL",
                "url": "https://www.postman.com/",
                "level": "入门",
            },
            {
                "name": "JMeter",
                "desc": "Apache开源性能测试工具，支持HTTP/TCP/JDBC等多种协议",
                "url": "https://jmeter.apache.org/",
                "level": "进阶",
            },
            {
                "name": "SoapUI",
                "desc": "专业的SOAP和REST API测试工具",
                "url": "https://www.soapui.org/",
                "level": "入门",
            },
            {
                "name": "Apifox",
                "desc": "国产API一体化协作平台，集文档/调试/Mock/测试于一体",
                "url": "https://apifox.com/",
                "level": "入门",
            },
        ],
    },
    {
        "id": "performance",
        "name": "性能测试",
        "icon": "Odometer",
        "tools": [
            {
                "name": "JMeter",
                "desc": "Apache开源性能测试工具，分布式压测能力强",
                "url": "https://jmeter.apache.org/",
                "level": "进阶",
            },
            {
                "name": "Locust",
                "desc": "Python编写的高性能负载测试工具，支持分布式",
                "url": "https://locust.io/",
                "level": "进阶",
            },
            {
                "name": "k6",
                "desc": "Grafana出品的现代负载测试工具，JS编写测试脚本",
                "url": "https://k6.io/",
                "level": "进阶",
            },
            {
                "name": "Gatling",
                "desc": "基于Scala的高性能压力测试工具，报表强大",
                "url": "https://gatling.io/",
                "level": "专家",
            },
        ],
    },
    {
        "id": "automation",
        "name": "自动化测试",
        "icon": "SetUp",
        "tools": [
            {
                "name": "Selenium",
                "desc": "Web自动化测试标准，支持多浏览器和多语言",
                "url": "https://www.selenium.dev/",
                "level": "进阶",
            },
            {
                "name": "Playwright",
                "desc": "微软出品的现代Web自动化框架，速度快、API简洁",
                "url": "https://playwright.dev/",
                "level": "入门",
            },
            {
                "name": "Cypress",
                "desc": "前端测试框架，实时重载、时间旅行调试",
                "url": "https://www.cypress.io/",
                "level": "入门",
            },
            {
                "name": "Appium",
                "desc": "移动端自动化测试框架，支持iOS/Android",
                "url": "https://appium.io/",
                "level": "进阶",
            },
            {
                "name": "Pytest",
                "desc": "Python测试框架，插件生态丰富",
                "url": "https://pytest.org/",
                "level": "入门",
            },
        ],
    },
    {
        "id": "security",
        "name": "安全测试",
        "icon": "Lock",
        "tools": [
            {
                "name": "Burp Suite",
                "desc": "Web安全渗透测试工具集",
                "url": "https://portswigger.net/burp",
                "level": "专家",
            },
            {
                "name": "OWASP ZAP",
                "desc": "开源的Web应用安全扫描器",
                "url": "https://www.zaproxy.org/",
                "level": "进阶",
            },
            {
                "name": "SQLMap",
                "desc": "自动化SQL注入检测和利用工具",
                "url": "https://sqlmap.org/",
                "level": "专家",
            },
        ],
    },
    {
        "id": "management",
        "name": "测试管理",
        "icon": "Document",
        "tools": [
            {
                "name": "JIRA",
                "desc": "Atlassian项目管理与缺陷跟踪工具",
                "url": "https://www.atlassian.com/software/jira",
                "level": "入门",
            },
            {
                "name": "禅道",
                "desc": "国产开源项目管理软件，集成产品/项目/测试管理",
                "url": "https://www.zentao.net/",
                "level": "入门",
            },
            {
                "name": "TestLink",
                "desc": "开源测试管理工具，支持测试用例管理和执行跟踪",
                "url": "https://testlink.org/",
                "level": "入门",
            },
            {
                "name": "Xray",
                "desc": "JIRA上的测试管理插件，支持手动和自动化测试",
                "url": "https://www.getxray.app/",
                "level": "进阶",
            },
        ],
    },
    {
        "id": "ci_cd",
        "name": "CI/CD",
        "icon": "Refresh",
        "tools": [
            {
                "name": "Jenkins",
                "desc": "最流行的开源CI/CD工具，插件生态丰富",
                "url": "https://www.jenkins.io/",
                "level": "进阶",
            },
            {
                "name": "GitLab CI",
                "desc": "GitLab内置的CI/CD管道工具",
                "url": "https://docs.gitlab.com/ee/ci/",
                "level": "进阶",
            },
            {
                "name": "GitHub Actions",
                "desc": "GitHub内置的自动化工作流",
                "url": "https://github.com/features/actions",
                "level": "入门",
            },
            {
                "name": "Allure",
                "desc": "灵活的测试报告框架，支持多语言、多工具集成",
                "url": "https://allurereport.org/",
                "level": "进阶",
            },
        ],
    },
]


@router.get("/categories")
async def get_tool_categories():
    return {"categories": TOOL_CATEGORIES}
