"""
TestMaster 学习路径综合迁移脚本 V3
功能:
1. 删除重复的学习路径（同标题保留一个）
2. 删除所有旧学习路径及其课程章节
3. 创建18个合理分类的学习路径（5阶段×全面测试领域覆盖）
4. 为每个路径补充详细的课程内容（Markdown格式）
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select, delete, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from fastapi_backend.core.config import settings
from fastapi_backend.models.models import LearningPath, LessonSection

DATABASE_URL = settings.DATABASE_URL
engine = create_async_engine(DATABASE_URL, echo=False)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# ============================================================
# 18个精心分类的学习路径
# ============================================================
ALL_PATHS = [
    # Stage 1: 测试入门 (Beginner)
    {
        "title": "软件测试基础理论",
        "description": "系统学习软件测试的基本概念、原则、分类和流程，建立正确的测试思维。掌握V模型、W模型、敏捷测试等开发模型，理解黑盒测试与白盒测试的核心区别，学习缺陷管理全流程。",
        "learning_objectives": "理解软件测试的定义与目的；掌握ISTQB七大测试原则；熟悉测试分类体系；理解缺陷的生命周期；掌握测试用例八大要素；理解测试金字塔模型",
        "knowledge_outline": "1.软件测试概述 2.测试七大原则 3.测试分类(按阶段/方法/方向) 4.软件开发生命周期 5.缺陷管理 6.测试用例基础 7.测试级别详解 8.敏捷测试与持续测试",
        "supporting_resources": "《软件测试的艺术》、ISTQB基础级大纲、IEEE 829标准",
        "prerequisites": "无",
        "language": "中文",
        "difficulty": "beginner",
        "stage": 1,
        "estimated_hours": 20,
    },
    {
        "title": "SQL数据库基础",
        "description": "掌握关系型数据库的核心概念和SQL语言，从数据库设计、建表、数据查询到索引优化与事务管理。课程涵盖MySQL实战操作，为接口测试和数据分析打下坚实基础。",
        "learning_objectives": "理解关系型数据库核心概念；熟练掌握SELECT/INSERT/UPDATE/DELETE；掌握多表JOIN和子查询；理解索引原理与事务ACID特性；能独立完成数据库设计",
        "knowledge_outline": "1.数据库基础概念 2.SQL数据类型与建表 3.数据查询SELECT(上) 4.数据查询SELECT(下) 5.DML操作 6.多表连接查询 7.子查询 8.索引与事务",
        "supporting_resources": "《SQL必知必会》、MySQL官方文档",
        "prerequisites": "无",
        "language": "中文",
        "difficulty": "beginner",
        "stage": 1,
        "estimated_hours": 15,
    },
    {
        "title": "Linux基础命令",
        "description": "掌握测试工程师必备的Linux操作技能，包括文件系统操作、文本处理三剑客(grep/sed/awk)、进程管理、系统监控和网络调试命令。",
        "learning_objectives": "熟悉Linux目录结构与文件操作；掌握grep/sed/awk文本处理；学会进程管理与后台运行；能查看系统日志和网络状态；了解Shell脚本基础",
        "knowledge_outline": "1.Linux文件系统与基本操作 2.文本处理三剑客 3.进程管理与系统监控 4.Shell脚本基础 5.日志查看与分析 6.网络调试命令",
        "supporting_resources": "《鸟哥的Linux私房菜》、Linux Man Pages",
        "prerequisites": "无",
        "language": "中文",
        "difficulty": "beginner",
        "stage": 1,
        "estimated_hours": 10,
    },
    {
        "title": "Python编程基础",
        "description": "从零开始学习Python编程语言，涵盖环境搭建、数据类型、流程控制、函数、面向对象、文件操作和异常处理。特别针对测试工程师的常用场景设计实战练习。",
        "learning_objectives": "掌握Python基本语法与数据类型；熟练编写函数和类；理解文件读写与JSON处理；掌握异常处理机制；能使用常用标准库编写自动化脚本",
        "knowledge_outline": "1.Python环境与基础语法 2.变量与数据类型 3.条件判断与循环 4.列表与元组 5.字典与集合 6.函数 7.面向对象编程 8.文件操作 9.异常处理 10.常用标准库",
        "supporting_resources": "《Python编程:从入门到实践》、Python官方文档",
        "prerequisites": "无",
        "language": "中文",
        "difficulty": "beginner",
        "stage": 1,
        "estimated_hours": 25,
    },
    {
        "title": "计算机基础与网络知识",
        "description": "理解计算机组成原理和网络基础知识，重点掌握HTTP/HTTPS协议、TCP/IP协议栈、DNS解析、RESTful API设计规范等测试工程师必备的网络知识。",
        "learning_objectives": "理解HTTP协议的请求与响应结构；掌握TCP三次握手与四次挥手；熟悉常见HTTP状态码；了解OSI七层模型与TCP/IP四层模型；掌握RESTful API设计原则",
        "knowledge_outline": "1.HTTP协议深度解析 2.TCP/IP与网络基础 3.DNS与域名解析 4.RESTful API设计规范 5.WebSocket协议入门 6.常用网络调试工具",
        "supporting_resources": "《图解HTTP》、《TCP/IP详解》、MDN Web Docs",
        "prerequisites": "无",
        "language": "中文",
        "difficulty": "beginner",
        "stage": 1,
        "estimated_hours": 10,
    },
    # Stage 2: 测试设计 (Beginner→Intermediate)
    {
        "title": "测试用例设计方法",
        "description": "深入掌握黑盒测试用例设计方法，包括等价类划分法、边界值分析法、判定表法、因果图法、正交实验法、场景法和错误推测法。通过大量实战案例，学会设计高效精准的测试用例。",
        "learning_objectives": "掌握等价类划分法并独立设计用例；熟练运用边界值分析法；理解判定表与因果图的应用场景；掌握场景法进行业务流程测试；能用正交实验法减少用例数量",
        "knowledge_outline": "1.等价类划分法 2.边界值分析法 3.判定表法 4.因果图法 5.正交实验法 6.场景法 7.错误推测法 8.测试用例评审与管理",
        "supporting_resources": "《软件测试方法和技术》、ISTQB测试分析师大纲",
        "prerequisites": "软件测试基础理论",
        "language": "中文",
        "difficulty": "beginner",
        "stage": 2,
        "estimated_hours": 15,
    },
    {
        "title": "缺陷管理与追踪",
        "description": "系统学习缺陷管理的完整流程，包括缺陷发现、报告、跟踪、验证和关闭。掌握JIRA/禅道等主流缺陷管理工具，学习缺陷分析和根因分析方法。",
        "learning_objectives": "掌握缺陷生命周期各阶段；能撰写高质量缺陷报告；熟练使用JIRA管理缺陷；理解缺陷严重程度与优先级的区别；掌握缺陷根因分析技术",
        "knowledge_outline": "1.缺陷生命周期详解 2.高质量缺陷报告编写 3.缺陷严重度与优先级判定 4.JIRA/禅道工具实战 5.缺陷统计与趋势分析 6.根因分析与5-Why法 7.缺陷预防策略",
        "supporting_resources": "《软件缺陷管理最佳实践》、JIRA官方文档",
        "prerequisites": "软件测试基础理论",
        "language": "中文",
        "difficulty": "beginner",
        "stage": 2,
        "estimated_hours": 10,
    },
    {
        "title": "测试计划编写与项目管理",
        "description": "学习如何制定科学的测试计划和测试策略，掌握测试估算方法、风险评估技术和测试进度管理。了解测试团队的组织结构和角色分工。",
        "learning_objectives": "能独立编写测试计划文档；掌握测试工作量估算方法(WBS/功能点)；学会测试风险识别与评估；理解测试策略的制定原则；掌握测试进度跟踪与报告",
        "knowledge_outline": "1.测试计划核心要素 2.测试策略制定 3.测试工作量估算 4.测试风险评估与管理 5.测试进度跟踪 6.测试报告编写 7.测试团队角色与分工",
        "supporting_resources": "《测试管理指南》、IEEE 829测试文档标准、PMBOK",
        "prerequisites": "软件测试基础理论",
        "language": "中文",
        "difficulty": "intermediate",
        "stage": 2,
        "estimated_hours": 12,
    },
    # Stage 3: 自动化测试 (Intermediate)
    {
        "title": "接口测试基础",
        "description": "系统学习接口测试的理论与实践。掌握HTTP API测试方法，熟练使用Postman进行接口调试与自动化。学习RESTful设计规范、接口文档管理、Token鉴权机制和Mock服务搭建。",
        "learning_objectives": "理解HTTP/HTTPS协议在接口测试中的应用；熟练使用Postman发送各类请求；掌握接口测试用例设计方法；学会使用环境变量和断言；了解接口Mock技术",
        "knowledge_outline": "1.API基础与RESTful规范 2.Postman工具详解 3.请求方法与参数传递 4.环境变量与脚本 5.接口断言与测试集 6.鉴权机制(Token/OAuth/JWT) 7.Mock服务搭建 8.接口文档(Swagger/OpenAPI)",
        "supporting_resources": "《API测试指南》、Postman官方文档、Swagger规范",
        "prerequisites": "计算机基础与网络知识、SQL数据库基础",
        "language": "中文",
        "difficulty": "intermediate",
        "stage": 3,
        "estimated_hours": 15,
    },
    {
        "title": "UI自动化测试 - Selenium",
        "description": "从零掌握Selenium WebDriver进行Web UI自动化测试。学习元素定位策略、等待机制、Page Object设计模式、测试框架搭建和持续集成。",
        "learning_objectives": "掌握Selenium八大元素定位方法；熟练运用显式等待与隐式等待；理解并实践Page Object模式；能搭建完整的UI自动化测试框架；实现自动化测试与CI/CD集成",
        "knowledge_outline": "1.Selenium环境搭建 2.元素定位策略详解 3.浏览器操作与截图 4.等待机制(显式/隐式/流畅) 5.Page Object设计模式 6.测试框架搭建(pytest+Selenium) 7.数据驱动测试 8.多浏览器兼容测试 9.测试报告(Allure) 10.CI/CD集成",
        "supporting_resources": "《Selenium自动化测试实战》、Selenium官方文档、W3C WebDriver标准",
        "prerequisites": "Python编程基础",
        "language": "中文",
        "difficulty": "intermediate",
        "stage": 3,
        "estimated_hours": 20,
    },
    {
        "title": "接口自动化测试 - Requests+Pytest",
        "description": "深入掌握基于Python的接口自动化测试框架搭建。学习Requests库的高级用法、Pytest测试框架、参数化测试、数据驱动、Allure报告和接口自动化框架的分层架构设计。",
        "learning_objectives": "熟练使用Requests库进行HTTP请求；掌握Pytest框架核心特性(fixture/参数化/conftest)；能搭建分层接口自动化框架；实现数据驱动和关键字驱动；生成专业的Allure测试报告",
        "knowledge_outline": "1.Requests库高级用法 2.Pytest框架核心 3.Fixture与conftest 4.参数化与数据驱动 5.接口关联与鉴权处理 6.断言与响应校验 7.框架分层设计(API层/业务层/用例层) 8.Allure报告 9.多环境配置管理 10.基于YAML/Excel的数据驱动",
        "supporting_resources": "《Python接口自动化测试》、Pytest官方文档、Allure文档",
        "prerequisites": "Python编程基础、接口测试基础",
        "language": "中文",
        "difficulty": "intermediate",
        "stage": 3,
        "estimated_hours": 18,
    },
    {
        "title": "移动端测试基础",
        "description": "系统学习移动应用测试的完整知识体系。涵盖Android和iOS平台特性、移动端专项测试方法、Appium自动化测试框架、移动端性能测试和兼容性测试。",
        "learning_objectives": "了解Android和iOS平台差异；掌握移动端功能测试方法；学会使用Appium进行移动UI自动化；理解移动端性能指标和测试方法；掌握移动端兼容性测试策略",
        "knowledge_outline": "1.移动端测试概述与分类 2.Android与iOS平台特性 3.移动端功能测试方法 4.专项测试(安装/卸载/升级/中断) 5.移动端兼容性测试 6.弱网与网络切换测试 7.Appium自动化入门 8.移动端性能测试",
        "supporting_resources": "《移动App测试实战》、Appium官方文档、Android/iOS开发者指南",
        "prerequisites": "软件测试基础理论",
        "language": "中文",
        "difficulty": "intermediate",
        "stage": 3,
        "estimated_hours": 12,
    },
    # Stage 4: 高级测试 (Advanced)
    {
        "title": "性能测试 - JMeter与Locust",
        "description": "深入掌握性能测试的理论与实践。从性能指标体系到实战工具(JMeter/Locust)，学习负载测试、压力测试、稳定性测试的完整流程，掌握性能瓶颈分析和调优方法。",
        "learning_objectives": "理解TPS/QPS/RT等核心性能指标；熟练使用JMeter编写性能测试脚本；掌握Locust进行分布式压测；学会性能监控与瓶颈分析；能编写专业性能测试报告",
        "knowledge_outline": "1.性能测试基础与指标体系 2.JMeter环境配置与组件 3.JMeter脚本开发(HTTP/SQL) 4.参数化与关联 5.分布式压测 6.Locust脚本开发 7.性能监控(Prometheus/Grafana) 8.瓶颈分析与性能调优 9.性能测试报告 10.全链路压测方案设计",
        "supporting_resources": "《性能测试从零开始》、JMeter官方文档、Locust文档",
        "prerequisites": "Python编程基础、计算机基础与网络知识",
        "language": "中文",
        "difficulty": "advanced",
        "stage": 4,
        "estimated_hours": 20,
    },
    {
        "title": "安全测试基础",
        "description": "掌握Web安全测试的核心知识，从OWASP Top 10出发，深入学习SQL注入、XSS、CSRF、SSRF、文件上传漏洞等常见安全风险的原理、检测方法和防御策略。",
        "learning_objectives": "理解OWASP Top 10安全风险；掌握SQL注入检测与防御；能识别XSS漏洞类型和利用方式；理解CSRF攻击原理与防护；学会使用Burp Suite等安全工具",
        "knowledge_outline": "1.Web安全概述与OWASP Top10 2.SQL注入原理与防御 3.XSS跨站脚本攻击 4.CSRF跨站请求伪造 5.SSRF服务器端请求伪造 6.文件上传漏洞 7.认证与授权安全 8.Burp Suite工具实战 9.安全编码规范 10.漏洞扫描与渗透测试基础",
        "supporting_resources": "《Web安全测试》、OWASP Testing Guide、Burp Suite文档",
        "prerequisites": "计算机基础与网络知识、SQL数据库基础",
        "language": "中文",
        "difficulty": "advanced",
        "stage": 4,
        "estimated_hours": 18,
    },
    {
        "title": "持续集成与DevOps",
        "description": "学习现代软件工程中的CI/CD实践，掌握Jenkins Pipeline、Docker容器化、GitLab CI、自动化部署和质量门禁的配置与应用。",
        "learning_objectives": "理解CI/CD的核心概念和价值；掌握Jenkins Pipeline脚本编写；学会Docker镜像构建与容器管理；能搭建完整的CI/CD流水线；掌握自动化测试在流水线中的集成",
        "knowledge_outline": "1.CI/CD概念与价值 2.Git工作流与分支策略 3.Jenkins Pipeline(Groovy) 4.Docker基础与Dockerfile 5.Docker Compose编排 6.GitLab CI配置 7.自动化测试集成 8.质量门禁与SonarQube 9.制品管理与发布策略 10.蓝绿部署与金丝雀发布",
        "supporting_resources": "《持续交付》、Jenkins官方文档、Docker官方文档",
        "prerequisites": "Linux基础命令",
        "language": "中文",
        "difficulty": "advanced",
        "stage": 4,
        "estimated_hours": 15,
    },
    {
        "title": "测试平台开发",
        "description": "从零构建测试管理平台，涵盖前后端技术选型、数据库设计、RESTful API开发、前端页面开发、用例管理系统、执行引擎和报表系统。",
        "learning_objectives": "理解测试平台的架构设计；掌握FastAPI/Django后端开发；学会Vue前端开发基础；能设计合理的数据库模型；了解测试平台的部署和运维",
        "knowledge_outline": "1.测试平台需求分析 2.技术选型与架构设计 3.数据库设计与ORM 4.RESTful API开发(FastAPI) 5.前端页面开发(Vue3+Element Plus) 6.用例管理模块 7.测试执行引擎 8.测试报表与可视化 9.定时任务与通知 10.平台部署与运维",
        "supporting_resources": "《Python Web开发实战》、FastAPI官方文档、Vue3文档",
        "prerequisites": "Python编程基础、SQL数据库基础",
        "language": "中文",
        "difficulty": "advanced",
        "stage": 4,
        "estimated_hours": 20,
    },
    # Stage 5: 专家级 (Advanced)
    {
        "title": "AI测试与智能化",
        "description": "探索AI技术在软件测试中的前沿应用。学习视觉回归测试、智能测试用例生成、基于ML的缺陷预测、NLP在测试中的应用以及自愈自动化测试。",
        "learning_objectives": "了解AI在测试领域的应用场景；掌握视觉回归测试工具(Applitools/Percy)；理解智能测试用例生成原理；学会使用AI辅助编写测试代码；了解自愈测试的概念与实现",
        "knowledge_outline": "1.AI测试概述与发展趋势 2.视觉回归测试(Visual Testing) 3.智能测试用例生成 4.ML缺陷预测与风险评估 5.NLP辅助需求分析与测试设计 6.AI驱动测试数据生成 7.自愈自动化测试 8.大模型在测试中的应用 9.AI测试工具生态 10.AI测试的局限与展望",
        "supporting_resources": "《AI-Driven Testing》、ISTQB AI测试大纲、各类AI测试工具文档",
        "prerequisites": "接口自动化测试 - Requests+Pytest",
        "language": "中文",
        "difficulty": "advanced",
        "stage": 5,
        "estimated_hours": 15,
    },
    {
        "title": "测试架构设计与质量度量",
        "description": "从测试工程师向测试架构师进阶的核心课程。学习测试架构设计方法、可测试性设计、微服务测试策略、质量度量模型、过程改进和测试团队建设。",
        "learning_objectives": "掌握测试架构设计原则；理解可测试性设计(DFT)；学会制定微服务测试策略；熟练运用质量度量模型(GQM/CMMI)；掌握测试过程改进方法(TMMi/TPI)",
        "knowledge_outline": "1.测试架构师的角色与能力 2.测试架构设计原则 3.可测试性设计(DFT) 4.微服务测试策略 5.分层测试体系设计 6.质量度量模型(GQM/ISO 25010) 7.缺陷分析与质量改进 8.测试成熟度模型(TMMi) 9.测试团队建设与人才培养 10.技术选型与工具链规划",
        "supporting_resources": "《软件测试架构》、TMMi标准、ISO 25010标准",
        "prerequisites": "测试平台开发、持续集成与DevOps",
        "language": "中文",
        "difficulty": "advanced",
        "stage": 5,
        "estimated_hours": 18,
    },
]

# ============================================================
# 详尽课程内容（每个路径至少6-8节）
# ============================================================
LESSON_CONTENT = {}

# ── 路径1: 软件测试基础理论 (8节) ──
LESSON_CONTENT["软件测试基础理论"] = [
    {
        "title": "第1节：软件测试的定义与目的",
        "sort_order": 1,
        "knowledge_point": "测试基础概念",
        "time_estimate": 20,
        "content": """## 软件测试的定义

软件测试（Software Testing）是使用人工或自动手段来运行或测定某个系统的过程，其目的在于检验它是否满足规定的需求，或弄清预期结果与实际结果之间的差别。

换句话说，软件测试就是**验证软件的正确性、完整性和质量**的过程。

## 测试的核心目的

**1. 发现缺陷（Find Bugs）**
这是测试最直接的目的。通过执行测试用例，尽可能多地发现软件中存在的缺陷和问题。著名的测试原则是：**测试只能证明缺陷存在，而不能证明缺陷不存在。**

**2. 验证需求（Verify Requirements）**
确保软件的功能、性能、安全性等方面符合需求规格说明书中定义的要求。每一个需求都应该有对应的测试用例来验证。

**3. 评估质量（Assess Quality）**
测试为项目干系人提供关于软件质量的客观信息，帮助做出发布决策。测试报告中的缺陷密度、通过率等指标是质量评估的重要依据。

**4. 预防缺陷（Prevent Defects）**
通过早期介入测试（如需求评审、设计评审），在缺陷产生之前就发现并纠正问题，大幅降低修复成本。

## 验证 vs 确认

- **验证（Verification）**：我们正确地建造产品了吗？关注过程，如评审、走查。
- **确认（Validation）**：我们建造了正确的产品吗？关注结果，如系统测试、验收测试。

## 测试与调试的区别

| 方面 | 测试 | 调试 |
|------|------|------|
| 目的 | 发现缺陷 | 定位并修复缺陷 |
| 执行者 | 测试人员 | 开发人员 |
| 阶段 | 贯穿整个开发过程 | 主要在编码阶段 |
| 方式 | 运行程序或静态检查 | 分析代码、断点跟踪 |

> 测试是发现错误的过程，而调试是修复错误的过程。两者相辅相成。

## 小结

软件测试是软件质量保障的核心活动。一个好的测试工程师不仅要有发现问题的敏锐嗅觉，还要理解测试在整个软件工程中的定位和价值。""",
    },
    {
        "title": "第2节：测试的七大原则",
        "sort_order": 2,
        "knowledge_point": "测试原则",
        "time_estimate": 25,
        "content": """## ISTQB定义的测试七大原则

### 原则1：测试说明存在缺陷（Testing shows the presence of defects）
测试可以证明缺陷存在，但不能证明没有缺陷。即使测试没有发现任何问题，也不能说明软件是完美的。

### 原则2：穷尽测试是不可能的（Exhaustive testing is impossible）
除了极其简单的小程序，想测试所有输入组合和前置条件是不可能的。我们需要使用风险评估和测试设计技术来确定测试的重点和范围。

**举例**：一个接受两个32位整数相加的函数，输入组合是2^64种，即超过184亿亿种组合。

### 原则3：早期测试（Early testing）
测试活动应尽早开始。缺陷发现得越早，修复成本越低。

**修复成本递增规律**：
- 需求阶段发现缺陷：修复成本 = 1x
- 设计阶段发现缺陷：修复成本 = 10x
- 编码阶段发现缺陷：修复成本 = 50x
- 测试阶段发现缺陷：修复成本 = 100x
- 生产环境发现缺陷：修复成本 = 1000x

### 原则4：缺陷集群性（Defect clustering）
大部分缺陷往往集中在少部分模块中。80%的缺陷通常只存在于20%的模块中（帕累托法则）。

### 原则5：杀虫剂悖论（Pesticide Paradox）
如果反复使用相同的测试用例集，最终将无法发现新的缺陷。解决方法是定期审查和修订测试用例。

### 原则6：测试依赖于上下文（Testing is context dependent）
不同类型的软件需要不同的测试方法。电商网站和航空控制系统的测试策略完全不同。

### 原则7：没有缺陷就是好用？（Absence-of-errors fallacy）
即使软件没有缺陷，也不代表它满足用户需求。测试不仅要找Bug，还要验证需求。

## 小结
这七大原则是每个测试工程师必须牢记的准则。""",
    },
    {
        "title": "第3节：软件开发生命周期与测试模型",
        "sort_order": 3,
        "knowledge_point": "开发模型",
        "time_estimate": 25,
        "content": """## 常见的软件开发模型

### 瀑布模型（Waterfall Model）
```
需求分析 → 设计 → 编码 → 测试 → 维护
```
测试只在编码完成后进行，返工成本很高。现在已很少单独使用。

### V模型（V-Model）
V模型强调了测试活动与开发活动的对应关系：
```
需求分析 ←→ 验收测试
概要设计 ←→ 系统测试
详细设计 ←→ 集成测试
  编码   ←→ 单元测试
```
**优点**：左侧开发、右侧测试、一一对应
**缺点**：仍然是线性模型，需求变更困难

### W模型（W-Model）
在V模型基础上强调：测试应该伴随着整个开发过程，不仅要对代码进行测试，还要对需求和设计进行测试。

### 敏捷开发中的测试
- **持续测试**：每天都在进行测试
- **自动化优先**：自动化测试是敏捷的基石
- **测试驱动开发（TDD）**：先写测试再写代码
- **行为驱动开发（BDD）**：用自然语言描述测试场景

### TDD的"红-绿-重构"循环
```
1. 红（Red）：编写一个失败的测试用例
2. 绿（Green）：编写最少的代码让测试通过
3. 重构（Refactor）：优化代码结构，保持测试通过
```

## 小结
理解各种开发模型对测试策略的选择至关重要。""",
    },
    {
        "title": "第4节：测试分类体系",
        "sort_order": 4,
        "knowledge_point": "测试分类",
        "time_estimate": 25,
        "content": """## 按测试阶段分类

### 单元测试（Unit Testing）
对软件的最小可测试单元（函数、方法、类）进行测试。通常由开发人员编写和执行。

**特点**：粒度最小、执行速度快、是自动化测试的基础
**常用框架**：JUnit（Java）、pytest（Python）、Jest（JavaScript）

### 集成测试（Integration Testing）
测试多个单元/模块之间的交互是否正确。

**集成策略**：
- **自顶向下**：从顶层模块开始，使用桩模块
- **自底向上**：从底层模块开始，使用驱动模块
- **三明治集成**：结合两种方式
- **大爆炸集成**：一次性集成所有模块（不推荐）

### 系统测试（System Testing）
将整个软件系统作为一个整体进行测试，验证其是否满足需求规格。

**系统测试类型**：功能测试、性能测试、安全性测试、兼容性测试、易用性测试、可靠性测试

### 验收测试（Acceptance Testing）
由用户或客户进行的测试，确认系统满足业务需求。
- **Alpha测试**：在开发环境中由用户进行
- **Beta测试**：在用户实际环境中进行
- **UAT（用户验收测试）**：正式的业务验收

## 按测试方法分类

### 黑盒测试（Black-box Testing）
不关心内部结构，只关注输入和输出。方法：等价类划分、边界值分析、因果图、判定表、场景法。

### 白盒测试（White-box Testing）
基于代码内部逻辑的测试。覆盖标准：语句覆盖、判定覆盖、条件覆盖、路径覆盖。

### 灰盒测试（Gray-box Testing）
介于黑盒和白盒之间，了解部分内部结构但主要从外部测试。

## 按是否执行分类
- **静态测试**：不运行程序，通过审查、走查、静态分析工具检查
- **动态测试**：实际运行程序

## 按测试目的分类
- **功能测试**：验证功能是否正确
- **非功能测试**：性能、安全性、可用性
- **回归测试**：验证修改后原有功能未受影响
- **冒烟测试**：验证基本功能是否可用
- **探索性测试**：基于经验和直觉的自由测试""",
    },
    {
        "title": "第5节：缺陷管理",
        "sort_order": 5,
        "knowledge_point": "缺陷管理",
        "time_estimate": 20,
        "content": """## 什么是软件缺陷（Bug）？

软件缺陷是指软件产品中存在的、导致系统不能正常工作的问题。

## 缺陷的生命周期

```
New（新建）→ Open（打开/分配）→ Fixed（已修复）→ Verified（已验证）→ Closed（关闭）
                                   ↓
                              Reopened（重新打开）
                                   ↓
                              Rejected（拒绝/不是bug）
```

### 各状态说明
| 状态 | 说明 | 负责人 |
|------|------|--------|
| New | 测试人员刚提交的缺陷 | 测试人员 |
| Open | 已确认是bug，分配给开发 | 开发经理 |
| Fixed | 开发人员已修复 | 开发人员 |
| Verified | 测试人员验证修复通过 | 测试人员 |
| Closed | 缺陷已解决并关闭 | 测试经理 |
| Reopened | 修复未通过，重新打开 | 测试人员 |
| Rejected | 不是bug或重复提交 | 开发人员 |

## 缺陷的重要属性

### 严重程度（Severity）
- **Blocker/Critical（致命）**：系统崩溃、数据丢失
- **Major（严重）**：主要功能错误，严重影响使用
- **Minor（一般）**：次要功能错误，有替代方案
- **Trivial（轻微）**：界面错字、排版问题

### 优先级（Priority）
- **P0-立即**：必须立即修复
- **P1-高**：应尽快在下一个版本中修复
- **P2-中**：按正常排期修复
- **P3-低**：可以在资源允许时修复

> 严重程度是技术评估，优先级是业务决策。

## 缺陷报告（Bug Report）
一份好的缺陷报告应包含：
1. **标题**：简短准确地描述问题
2. **复现步骤**：详细、可重复的操作步骤
3. **实际结果**：执行操作后的实际现象
4. **预期结果**：按照需求应该出现的结果
5. **环境信息**：操作系统、浏览器、版本等
6. **附件**：截图、日志、录屏等

## 常用缺陷管理工具
- **JIRA**：最流行的商业项目管理工具
- **禅道**：国产开源项目管理工具
- **Bugzilla**：经典的开源缺陷管理工具
- **GitHub Issues**：适合小团队""",
    },
    {
        "title": "第6节：测试用例设计基础",
        "sort_order": 6,
        "knowledge_point": "测试用例要素",
        "time_estimate": 20,
        "content": """## 什么是测试用例？

测试用例（Test Case）是为特定测试目标而设计的一组输入、执行条件和预期结果的集合。

## 测试用例的八大要素

| 要素 | 说明 | 是否必须 |
|------|------|----------|
| 用例编号 | 唯一标识，如TC_LOGIN_001 | 必须 |
| 测试模块 | 所属功能模块 | 必须 |
| 用例标题 | 简述测试内容 | 必须 |
| 前置条件 | 执行前需要满足的条件 | 可选 |
| 测试步骤 | 详细的操作步骤 | 必须 |
| 测试数据 | 输入的具体数据 | 必须 |
| 预期结果 | 期望看到的输出/现象 | 必须 |
| 后置处理 | 测试后的清理操作 | 可选 |

## 测试用例设计原则

### 单一原则
每个测试用例只测试一个场景或功能点。

### 独立性
测试用例之间应该相互独立。

### 可重复性
任何人按照测试用例描述的步骤执行，都应该得到相同的测试结果。

### 清晰性
步骤和预期结果要清晰明确，避免歧义。

## 好的测试用例 vs 差的测试用例

**差的测试用例**：
> 测试登录功能，输入一些账号密码，看看能不能登录成功。

**好的测试用例**：
> **用例编号**：TC_LOGIN_001
> **标题**：验证正确账号密码可以成功登录
> **前置条件**：已注册账号admin/Test@123
> **步骤**：
> 1. 打开登录页面
> 2. 输入用户名：admin
> 3. 输入密码：Test@123
> 4. 点击"登录"按钮
> **预期结果**：
> 1. 页面跳转到首页
> 2. 右上角显示用户名"admin" """,
    },
    {
        "title": "第7节：测试级别详解",
        "sort_order": 7,
        "knowledge_point": "测试级别",
        "time_estimate": 25,
        "content": """## 测试金字塔

测试金字塔是Mike Cohn提出的测试策略模型：

```
        ╱  E2E  ╲
       ╱  (少量)  ╲
      ╱─────────────╲
     ╱   集成测试    ╲
    ╱   (中等数量)   ╲
   ╱─────────────────╲
  ╱     单元测试       ╲
 ╱     (最多数量)       ╲
```

**核心思想**：
- 底层（单元测试）数量最多，执行最快，成本最低
- 中层（集成测试）数量适中
- 顶层（E2E/UI测试）数量最少，执行最慢，维护成本最高

## 单元测试深入

### FIRST原则
- **F**ast（快速）：每个单元测试应快速执行
- **I**solate（隔离）：测试之间相互独立
- **R**epeatable（可重复）：任何环境下都能重复运行
- **S**elf-validating（自验证）：测试结果明确
- **T**imely（及时）：在编码时同步编写

## E2E测试

E2E测试模拟真实用户场景，测试整个系统的完整流程。
**常用工具**：Selenium、Cypress、Playwright

## 小结
测试金字塔是指导测试策略的核心模型。投入比例应该是：单元测试 > 集成测试 > E2E测试。""",
    },
    {
        "title": "第8节：敏捷测试与持续测试",
        "sort_order": 8,
        "knowledge_point": "敏捷测试",
        "time_estimate": 25,
        "content": """## 敏捷测试的核心概念

### 敏捷测试的特点

**1. 全团队对质量负责**
不只是测试人员关心质量，开发、产品、设计都需要为质量负责。

**2. 测试左移（Shift-Left）**
把测试活动提前到开发的最早期阶段。测试人员在需求评审时就参与进来。

**3. 持续测试（Continuous Testing）**
每一次代码提交都会触发自动化测试，问题在第一时间被发现和修复。

**4. 自动化是基石**
至少要实现：单元测试自动化、接口测试自动化、关键流程的UI自动化。

**5. 探索性测试**
自动化覆盖不了所有场景，探索性测试发挥测试人员的创造性和直觉。

## Scrum中的测试角色

### Sprint开始
- 参与Sprint Planning，评估测试工作量
- 评审User Story，编写测试用例
- 准备测试数据和测试环境

### Sprint进行中
- 每日站会汇报测试进展和阻塞问题
- 执行新功能的测试和回归测试
- 与开发人员沟通发现的缺陷

### Sprint结束
- 参与Sprint Review，展示测试成果
- Sprint Retrospective中提出改进建议

## 行为驱动开发（BDD）

```gherkin
Feature: 用户登录
  Scenario: 使用正确的账号密码登录
    Given 用户在登录页面
    When 输入用户名 "admin" 和密码 "123456"
    And 点击登录按钮
    Then 页面跳转到首页
    And 显示欢迎信息 "欢迎回来，admin"
```

## CI/CD
```
代码提交 → 编译 → 单元测试 → 代码扫描 → 集成测试 → 构建镜像 → 部署测试环境 → 自动化测试 → 部署生产
```

## 小结
敏捷测试要求测试人员具备更全面的技能：编程能力、自动化能力、沟通能力和分析能力。这是从"找Bug的人"到"质量保障者"的转变。""",
    },
]

# ── 路径2: SQL数据库基础 (8节) ──
LESSON_CONTENT["SQL数据库基础"] = [
    {
        "title": "第1节：数据库基础概念",
        "sort_order": 1,
        "knowledge_point": "数据库概述",
        "time_estimate": 20,
        "content": """## 什么是数据库？

数据库（Database）是按照数据结构来组织、存储和管理数据的仓库。

## 关系型数据库（RDBMS）

关系型数据库将数据组织成**表（Table）**，表之间通过**关系（Relation）**来关联。

### 核心概念
| 概念 | 说明 | 类比 |
|------|------|------|
| 数据库（Database） | 存放所有数据的容器 | 一个文件夹 |
| 表（Table） | 某种类型数据的集合 | 一个Excel表格 |
| 行（Row/Record） | 一条完整的数据记录 | 表格中的一行 |
| 列（Column/Field） | 数据的一个属性 | 表格中的一列 |
| 主键（Primary Key） | 唯一标识一条记录 | 身份证号 |
| 外键（Foreign Key） | 关联其他表 | 引用关系 |

### 常见的关系型数据库
| 数据库 | 特点 | 适用场景 |
|--------|------|----------|
| MySQL | 开源免费 | Web应用 |
| PostgreSQL | 功能强大 | 复杂查询 |
| Oracle | 商业数据库 | 大型企业 |
| SQL Server | 与.NET集成好 | Windows生态 |
| SQLite | 轻量级 | 移动应用、小型项目 |

## SQL语言简介

| 类别 | 作用 | 常用语句 |
|------|------|----------|
| DDL（数据定义语言） | 定义数据库结构 | CREATE、ALTER、DROP |
| DML（数据操纵语言） | 操作数据 | SELECT、INSERT、UPDATE、DELETE |
| DCL（数据控制语言） | 控制访问权限 | GRANT、REVOKE |
| TCL（事务控制语言） | 管理事务 | COMMIT、ROLLBACK |

## 范式（Normalization）
- **1NF**：每个字段不可再分（原子性）
- **2NF**：非主键字段完全依赖于主键
- **3NF**：非主键字段不依赖于其他非主键字段""",
    },
    {
        "title": "第2节：SQL数据类型与建表",
        "sort_order": 2,
        "knowledge_point": "DDL建表",
        "time_estimate": 25,
        "content": """## MySQL常用数据类型

### 数值类型
| 类型 | 大小 | 范围 | 用途 |
|------|------|------|------|
| TINYINT | 1字节 | -128~127 | 年龄、状态码 |
| INT | 4字节 | -21亿~21亿 | 主键、数量 |
| BIGINT | 8字节 | 极大 | 大数据量ID |
| DECIMAL(M,D) | 变长 | 精确小数 | 金额 |

### 字符串类型
| 类型 | 说明 | 使用场景 |
|------|------|----------|
| CHAR(N) | 定长字符串 | 性别、状态码 |
| VARCHAR(N) | 变长字符串 | 用户名、邮箱 |
| TEXT | 长文本 | 文章内容 |

### 日期时间类型
| 类型 | 格式 | 说明 |
|------|------|------|
| DATE | YYYY-MM-DD | 日期 |
| DATETIME | YYYY-MM-DD HH:MM:SS | 日期时间 |
| TIMESTAMP | 时间戳 | 自动更新 |

## CREATE TABLE 详解

```sql
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '用户ID',
    username VARCHAR(50) NOT NULL COMMENT '用户名',
    email VARCHAR(100) UNIQUE NOT NULL COMMENT '邮箱',
    password_hash VARCHAR(128) NOT NULL COMMENT '密码哈希',
    age INT COMMENT '年龄',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否激活',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户表';
```

## 常用约束
| 约束 | 说明 | 示例 |
|------|------|------|
| NOT NULL | 不能为空 | `username VARCHAR(50) NOT NULL` |
| UNIQUE | 值唯一 | `email VARCHAR(100) UNIQUE` |
| PRIMARY KEY | 主键 | `id INT PRIMARY KEY` |
| AUTO_INCREMENT | 自增 | `id INT AUTO_INCREMENT` |
| DEFAULT | 默认值 | `status INT DEFAULT 1` |
| FOREIGN KEY | 外键 | `FOREIGN KEY (user_id) REFERENCES users(id)` |

## ALTER TABLE 修改表结构
```sql
ALTER TABLE users ADD COLUMN phone VARCHAR(20);
ALTER TABLE users MODIFY COLUMN age TINYINT;
ALTER TABLE users DROP COLUMN phone;
ALTER TABLE users ADD INDEX idx_username (username);
```""",
    },
    {
        "title": "第3节：数据查询SELECT（上）",
        "sort_order": 3,
        "knowledge_point": "SQL基础查询",
        "time_estimate": 25,
        "content": """## SELECT 基本语法

```sql
SELECT 列名1, 列名2, ... FROM 表名 WHERE 条件 ORDER BY 排序列 LIMIT 数量;
```

### WHERE 条件过滤

**比较运算符**：
```sql
SELECT * FROM users WHERE age = 25;
SELECT * FROM users WHERE age > 18 AND age <= 30;
```

**BETWEEN 区间查询**：
```sql
SELECT * FROM users WHERE age BETWEEN 18 AND 30;
```

**IN 集合查询**：
```sql
SELECT * FROM users WHERE id IN (1, 3, 5, 7);
SELECT * FROM users WHERE id IN (SELECT user_id FROM orders WHERE amount > 1000);
```

**LIKE 模糊查询**：
```sql
SELECT * FROM users WHERE username LIKE '张%';  -- 以'张'开头
SELECT * FROM users WHERE email LIKE '%test%';   -- 包含'test'
SELECT * FROM users WHERE username LIKE '_小_';  -- 第二个字是'小'
```

> `%` 匹配任意多个字符，`_` 匹配单个字符。

**IS NULL / IS NOT NULL**：
```sql
SELECT * FROM users WHERE age IS NULL;
SELECT * FROM users WHERE age IS NOT NULL;
```
> 注意：不能用 `age = NULL`，必须用 `IS NULL`。

### 逻辑运算符
```sql
-- AND（与）
SELECT * FROM users WHERE age >= 18 AND age <= 30 AND is_active = TRUE;
-- OR（或）
SELECT * FROM users WHERE age < 18 OR age > 60;
-- NOT（非）
SELECT * FROM users WHERE NOT (age BETWEEN 18 AND 30);
```

### ORDER BY 排序
```sql
SELECT * FROM users ORDER BY age ASC;   -- 升序
SELECT * FROM users ORDER BY age DESC;  -- 降序
SELECT * FROM users ORDER BY age DESC, created_at ASC;
```

### LIMIT 限制返回数量
```sql
SELECT * FROM users LIMIT 10;        -- 前10条
SELECT * FROM users LIMIT 20, 10;    -- 分页（跳过20条，返回10条）
SELECT * FROM users LIMIT 10 OFFSET 20;
```

执行顺序：`SELECT → FROM → WHERE → ORDER BY → LIMIT`""",
    },
    {
        "title": "第4节：数据查询SELECT（下）",
        "sort_order": 4,
        "knowledge_point": "高级查询",
        "time_estimate": 30,
        "content": """## 聚合函数

| 函数 | 说明 | 示例 |
|------|------|------|
| COUNT() | 计数 | `COUNT(*)` 计数所有行 |
| SUM() | 求和 | `SUM(amount)` 总金额 |
| AVG() | 平均值 | `AVG(score)` 平均分 |
| MAX() | 最大值 | `MAX(salary)` 最高薪资 |
| MIN() | 最小值 | `MIN(age)` 最小年龄 |

```sql
-- 统计不同城市数量（去重计数）
SELECT COUNT(DISTINCT city) FROM users;

-- 订单统计
SELECT
    SUM(amount) AS total_amount,
    AVG(amount) AS avg_amount,
    MAX(amount) AS max_amount,
    MIN(amount) AS min_amount
FROM orders WHERE status = 'completed';
```

## GROUP BY 分组

```sql
-- 按部门分组统计
SELECT department_id, COUNT(*) AS emp_count
FROM employees GROUP BY department_id;
```

执行顺序：`FROM → WHERE → GROUP BY → HAVING → SELECT → ORDER BY → LIMIT`

## HAVING 过滤分组

WHERE在GROUP BY之前过滤行，HAVING在GROUP BY之后过滤分组。

```sql
SELECT customer_id, SUM(amount) AS total_amount
FROM orders GROUP BY customer_id
HAVING SUM(amount) > 1000;
```

## DISTINCT 去重
```sql
SELECT DISTINCT city FROM users;
```

## CASE WHEN 条件表达式
```sql
SELECT name, score,
    CASE WHEN score >= 90 THEN '优秀'
         WHEN score >= 80 THEN '良好'
         WHEN score >= 60 THEN '及格'
         ELSE '不及格'
    END AS grade
FROM students;
```

## 综合查询示例
```sql
SELECT category, COUNT(*) AS product_count, AVG(price) AS avg_price
FROM products WHERE is_active = TRUE
GROUP BY category HAVING COUNT(*) > 3
ORDER BY avg_price DESC LIMIT 10;
```""",
    },
    {
        "title": "第5节：数据操作 INSERT UPDATE DELETE",
        "sort_order": 5,
        "knowledge_point": "DML操作",
        "time_estimate": 20,
        "content": """## INSERT 插入数据

```sql
-- 插入单行
INSERT INTO users (username, email, age) VALUES ('zhangsan', 'zhangsan@test.com', 25);

-- 插入多行
INSERT INTO users (username, email, age) VALUES
    ('lisi', 'lisi@test.com', 30),
    ('wangwu', 'wangwu@test.com', 28);

-- 有则更新（ON DUPLICATE KEY）
INSERT INTO users (username, email, age) VALUES ('zhangsan', 'new@test.com', 26)
ON DUPLICATE KEY UPDATE email = VALUES(email), age = VALUES(age);
```

## UPDATE 更新数据

```sql
UPDATE users SET age = 26 WHERE username = 'zhangsan';
UPDATE users SET age = 27, is_active = FALSE WHERE id = 5;
```

> **危险提示**：不带WHERE的UPDATE会更新**所有行**！

## DELETE 删除数据

```sql
DELETE FROM orders WHERE status = 'cancelled';
DELETE FROM users WHERE id = 10;
```

**DELETE vs TRUNCATE**：
- DELETE：逐行删除，支持WHERE，可回滚
- TRUNCATE：直接清空，不可回滚，速度更快

> **安全第一**：生产环境执行DELETE/UPDATE前，先用SELECT确认WHERE条件。

## 数据操作最佳实践
1. **先SELECT后UPDATE/DELETE**
2. **使用事务**：多次操作放在事务中，出错可回滚
3. **备份重要数据**
4. **WHERE条件尽量用主键**
5. **避免在循环中执行SQL**""",
    },
    {
        "title": "第6节：多表连接查询",
        "sort_order": 6,
        "knowledge_point": "多表连接",
        "time_estimate": 30,
        "content": """## 连接分类

| 连接类型 | 说明 |
|----------|------|
| INNER JOIN | 只返回匹配的行 |
| LEFT JOIN | 返回左表所有行，右表不匹配填NULL |
| RIGHT JOIN | 返回右表所有行，左表不匹配填NULL |
| CROSS JOIN | 笛卡尔积（每行×每行） |

## INNER JOIN（内连接）

```sql
SELECT u.username, o.product_name, o.amount
FROM users u
INNER JOIN orders o ON u.id = o.user_id;

-- 三表连接
SELECT u.username, o.product_name, p.category
FROM users u
INNER JOIN orders o ON u.id = o.user_id
INNER JOIN products p ON o.product_id = p.id;
```

## LEFT JOIN（左外连接）

```sql
-- 所有用户及其订单（包括没有订单的用户）
SELECT u.username, o.product_name, o.amount
FROM users u LEFT JOIN orders o ON u.id = o.user_id;

-- 查找没有订单的用户
SELECT u.username FROM users u
LEFT JOIN orders o ON u.id = o.user_id
WHERE o.id IS NULL;
```

## 连接查询 vs 子查询

需要显示两个表的字段 → **用JOIN**
只需要一个表的字段，用另一个表做筛选 → **两者都可以**

## 最佳实践
1. **使用表别名**：`FROM users u`
2. **ON条件明确**
3. **INNER JOIN优先**
4. **避免笛卡尔积**
5. **用EXPLAIN分析查询**：
```sql
EXPLAIN SELECT u.username, o.product_name
FROM users u LEFT JOIN orders o ON u.id = o.user_id;
```""",
    },
    {
        "title": "第7节：子查询",
        "sort_order": 7,
        "knowledge_point": "子查询",
        "time_estimate": 25,
        "content": """## 什么是子查询？

子查询是嵌套在另一个SQL语句内部的查询。

```sql
SELECT username FROM users
WHERE id IN (SELECT user_id FROM orders WHERE amount > 1000);
```

## 子查询分类

### 按位置分类
| 位置 | 示例 |
|------|------|
| WHERE子句中 | `WHERE id IN (SELECT ...)` |
| SELECT子句中 | `SELECT name, (SELECT ...) AS cnt` |
| FROM子句中 | `FROM (SELECT ...) AS sub` |

### 标量子查询（返回单个值）
```sql
SELECT name, salary FROM employees
WHERE salary > (SELECT AVG(salary) FROM employees);
```

### 列子查询（返回一列多行）
```sql
-- IN
SELECT name FROM employees WHERE department_id IN (SELECT id FROM departments WHERE location = '北京');
-- ANY/ALL
SELECT name, salary FROM employees WHERE salary > ALL (SELECT salary FROM employees WHERE department_id = 3);
```

## 相关子查询
引用外部查询的列，对外部查询的每一行都要执行一次子查询。

```sql
SELECT name, salary, department_id FROM employees e
WHERE salary > (SELECT AVG(salary) FROM employees WHERE department_id = e.department_id);
```

## EXISTS / NOT EXISTS
```sql
SELECT username FROM users u WHERE EXISTS (SELECT 1 FROM orders o WHERE o.user_id = u.id);
SELECT username FROM users u WHERE NOT EXISTS (SELECT 1 FROM orders o WHERE o.user_id = u.id);
```

## 性能注意事项
1. 非相关子查询通常比相关子查询快
2. IN + 子查询可能很慢，改用JOIN或EXISTS
3. 避免在SELECT中使用子查询（每行执行一次）
4. 使用EXPLAIN查看执行计划""",
    },
    {
        "title": "第8节：索引与事务",
        "sort_order": 8,
        "knowledge_point": "索引与事务",
        "time_estimate": 25,
        "content": """## 索引（Index）

索引就像一本书的目录，能帮助数据库快速定位数据。

```
没有索引（全表扫描）：查询 id=999 → 从第1行扫描到第999行 → O(n)
有索引（B+Tree）：查询 id=999 → 通过索引树快速定位 → O(log n)
```

### 创建索引
```sql
CREATE INDEX idx_username ON users(username);
CREATE UNIQUE INDEX idx_email ON users(email);
CREATE INDEX idx_name_age ON users(username, age);
```

### 使用原则
**应该创建索引**：WHERE条件频繁使用的列、JOIN连接的列、ORDER BY的列
**不应该创建**：区分度低的列（如性别）、频繁更新的列、小表

### 最左前缀原则
对于联合索引 `(a, b, c)`，查询条件必须从a开始才能使用索引。

## 事务（Transaction）

事务是一组不可分割的数据库操作，要么全部成功，要么全部失败回滚。

### ACID特性
| 特性 | 说明 |
|------|------|
| **A**tomacity | 操作不可分割 |
| **C**onsistency | 数据前后一致 |
| **I**solation | 事务间不干扰 |
| **D**urability | 提交后永久保存 |

### 事务操作
```sql
START TRANSACTION;
UPDATE accounts SET balance = balance - 100 WHERE id = 1;
UPDATE accounts SET balance = balance + 100 WHERE id = 2;
COMMIT;  -- 确认
-- 或 ROLLBACK;  -- 撤销
```

### 事务隔离级别
| 级别 | 脏读 | 不可重复读 | 幻读 |
|------|------|-----------|------|
| READ UNCOMMITTED | 可能 | 可能 | 可能 |
| READ COMMITTED | 不会 | 可能 | 可能 |
| REPEATABLE READ（MySQL默认） | 不会 | 不会 | 可能 |
| SERIALIZABLE | 不会 | 不会 | 不会 |""",
    },
]

# ── 路径3: Linux基础命令 (5节) ──
LESSON_CONTENT["Linux基础命令"] = [
    {
        "title": "第1节：Linux文件系统与基本操作",
        "sort_order": 1,
        "knowledge_point": "文件操作",
        "time_estimate": 20,
        "content": """## Linux目录结构

```
/          根目录
├── bin/    基础命令
├── etc/    配置文件
├── home/   用户目录
├── var/    日志、缓存
├── tmp/    临时文件
├── usr/    用户程序
└── opt/    第三方软件
```

## 基础文件命令

```bash
ls          查看目录内容
ls -l       显示详细信息
ls -la      显示所有文件（含隐藏文件）
cd /path    切换目录；cd .. 返回上级；cd ~ 回到用户主目录
pwd         显示当前路径
mkdir dir   创建目录；mkdir -p a/b/c 递归创建
cp src dst  复制文件；cp -r src dst 复制目录
mv src dst  移动/重命名
rm file     删除文件；rm -r dir 删除目录；rm -rf dir 强制删除（危险！）
cat file    查看文件内容
less file   分页查看（q退出）
head -n 20 file  查看前20行
tail -n 100 file 查看最后100行
touch file  创建空文件
```

## 文件权限

```bash
ls -l  # -rwxr-xr-- 1 user group 1024 Jan 15 file.txt
# r=4, w=2, x=1
chmod 755 file   # rwxr-xr-x
chmod 644 file   # rw-r--r--
chmod +x script  # 添加执行权限
```

## 查看日志（测试工程师核心技能）

```bash
tail -f error.log        # 实时查看日志
tail -n 100 app.log      # 查看最后100行
head -n 20 app.log       # 查看前20行
grep "ERROR" app.log     # 搜索包含ERROR的行
grep -n "ERROR" app.log  # 显示行号
grep -rn "ERROR" logs/   # 递归搜索目录
grep -C 5 "ERROR" log    # 显示匹配行及前后5行
```""",
    },
    {
        "title": "第2节：文本处理三剑客",
        "sort_order": 2,
        "knowledge_point": "grep/sed/awk",
        "time_estimate": 25,
        "content": """## grep - 文本搜索

```bash
grep "pattern" file        # 搜索包含pattern的行
grep -i "error" app.log    # 不区分大小写
grep -v "DEBUG" app.log    # 反向匹配（排除DEBUG）
grep -c "ERROR" app.log    # 统计匹配行数
grep -rn "TODO" src/       # 递归搜索目录
grep -A 3 "ERROR" log      # 显示匹配行及后3行
grep -B 2 "ERROR" log      # 显示匹配行及前2行
```

## sed - 流编辑器

```bash
# 替换
sed 's/localhost/192.168.1.100/' file     # 替换第一个
sed 's/localhost/192.168.1.100/g' file    # 全局替换
sed -i 's/old/new/g' file                 # 直接修改文件

# 删除行
sed '5d' file              # 删除第5行
sed '/DEBUG/d' file        # 删除包含DEBUG的行

# 提取行
sed -n '10,20p' file       # 显示10-20行
```

## awk - 文本分析工具

```bash
awk '{print $1}' file           # 打印第1列
awk '{print $1, $NF}' file      # 打印第1列和最后一列
awk -F: '{print $1}' /etc/passwd  # 指定分隔符为:
awk -F',' '{print $2}' data.csv   # CSV文件处理
awk '$3 > 100' file             # 第3列大于100的行
awk '/ERROR/ {print $1, $4}' log   # 含ERROR的行，打印第1和第4列
awk '{sum+=$3} END {print sum}' data  # 第3列求和
```

## 管道与组合（测试工程师必会）

```bash
# 统计404错误数量
cat access.log | grep "404" | wc -l

# 提取Python进程PID
ps aux | grep python | awk '{print $2}'

# 最常用的10个命令
history | awk '{print $2}' | sort | uniq -c | sort -rn | head -10

# 查找大文件（测试日志分析常用）
find /var/log -type f -size +100M -exec ls -lh {} \\;

# 批量替换配置文件
find . -name "*.conf" -exec sed -i 's/localhost/prod-server/g' {} \\;
```""",
    },
    {
        "title": "第3节：进程管理与系统监控",
        "sort_order": 3,
        "knowledge_point": "进程管理",
        "time_estimate": 20,
        "content": """## 进程管理

```bash
ps aux                     # 查看所有进程
ps aux | grep python       # 查找Python进程
top                        # 实时进程监控（q退出）
htop                       # 更友好的top（需安装）
kill PID                   # 终止进程（优雅）
kill -9 PID                # 强制终止
killall process_name       # 按名称终止

# 后台运行
nohup python app.py &      # 后台运行，忽略挂断信号
nohup python app.py > log.txt 2>&1 &  # 重定向输出
```

## 系统信息

```bash
df -h                      # 磁盘使用情况
du -sh *                   # 当前目录下各文件/文件夹大小
free -h                    # 内存使用情况
uname -a                   # 系统信息
uptime                     # 运行时间
w                          # 当前登录用户
```

## 网络命令（测试必备）

```bash
netstat -tlnp              # 查看监听端口
lsof -i :5001              # 查看5001端口占用
curl http://localhost:5001 # HTTP请求测试
curl -X POST -H "Content-Type: application/json" -d '{"key":"val"}' http://localhost/api
ping -c 4 google.com       # 连通性测试
telnet host port           # 端口连通性测试
```""",
    },
    {
        "title": "第4节：Shell脚本基础",
        "sort_order": 4,
        "knowledge_point": "Shell脚本",
        "time_estimate": 25,
        "content": """## Shell脚本入门

```bash
#!/bin/bash
# 这是我的第一个Shell脚本

echo "Hello, TestMaster!"

# 变量
NAME="TestMaster"
echo "Welcome to $NAME"

# 数组
SERVERS=("dev" "test" "prod")
for server in "${SERVERS[@]}"; do
    echo "Deploying to $server..."
done

# 条件判断
if [ -f "config.yml" ]; then
    echo "配置文件存在"
else
    echo "配置文件不存在，使用默认配置"
fi

# 函数
check_service() {
    if pgrep -x "$1" > /dev/null; then
        echo "$1 is running"
    else
        echo "$1 is NOT running"
    fi
}
check_service "nginx"
```

## 测试工程师常用Shell脚本

```bash
#!/bin/bash
# 自动化测试运行脚本

TEST_ENV=${1:-"dev"}
echo "Running tests on $TEST_ENV environment..."

# 启动服务
nohup python app.py > app.log 2>&1 &
APP_PID=$!
sleep 3

# 执行测试
pytest tests/ -v --env=$TEST_ENV

# 检查结果
if [ $? -eq 0 ]; then
    echo "✅ All tests passed!"
else
    echo "❌ Some tests failed!"
fi

# 清理
kill $APP_PID
```

## 定时任务（Crontab）

```bash
crontab -e   # 编辑定时任务
# 格式：分 时 日 月 周 命令
0 6 * * * /home/user/run_tests.sh    # 每天早上6点执行
*/30 * * * * /usr/bin/python health_check.py  # 每30分钟执行
0 2 * * 0 /opt/backup.sh             # 每周日凌晨2点执行备份
```""",
    },
    {
        "title": "第5节：日志分析与故障排查",
        "sort_order": 5,
        "knowledge_point": "日志分析",
        "time_estimate": 20,
        "content": """## 日志类型与位置

```bash
/var/log/
├── syslog          # 系统日志
├── auth.log        # 认证日志
├── nginx/          # Nginx日志
│   ├── access.log  # 访问日志
│   └── error.log   # 错误日志
└── app/            # 应用日志
```

## 日志分析实战

```bash
# 统计各HTTP状态码数量
awk '{print $9}' access.log | sort | uniq -c | sort -rn

# 统计访问量前10的IP
awk '{print $1}' access.log | sort | uniq -c | sort -rn | head -10

# 统计请求耗时超过3秒的请求
awk '$NF > 3 {print $7, $NF}' access.log

# 查看某个时间段的错误
grep "2024-01-15 10:" error.log | grep "ERROR"

# 统计每分钟的请求量
awk '{print substr($4,2,17)}' access.log | uniq -c

# 查看大文件尾部并持续监控
tail -f app.log | grep --color "ERROR\|WARN"

# 查找包含特定错误的堆栈信息
grep -A 20 "NullPointerException" app.log
```

## 磁盘空间与文件清理

```bash
# 查找大于100M的文件
find / -type f -size +100M -exec ls -lh {} \\; 2>/dev/null

# 清理30天前的日志
find /var/log -name "*.log" -mtime +30 -delete

# 压缩旧日志
find /var/log -name "*.log" -mtime +7 -exec gzip {} \\;

# 查看目录大小并按大小排序
du -sh /var/log/* | sort -rh | head -10
```""",
    },
]

# ── 路径4: Python编程基础 (10节) ──
LESSON_CONTENT["Python编程基础"] = [
    {
        "title": "第1节：Python环境搭建与基础语法",
        "sort_order": 1,
        "knowledge_point": "Python环境",
        "time_estimate": 20,
        "content": """## Python简介

Python是一种**解释型、面向对象、动态类型**的高级编程语言。

### Python的特点
| 特点 | 说明 |
|------|------|
| 简洁易读 | 语法清晰，使用缩进定义代码块 |
| 解释型 | 逐行执行，无需编译 |
| 动态类型 | 变量无需声明类型 |
| 丰富的库 | "Batteries Included"（自带电池）理念 |
| 跨平台 | Windows/Linux/Mac都能运行 |

## 安装Python

### pip包管理器
```bash
pip install requests
pip install pytest
pip list
pip uninstall requests
pip install django==4.2.0
```

## 第一个Python程序
```python
print("Hello, World!")
print("欢迎来到Python世界！")
```

## Python基础语法

### 注释
```python
# 这是单行注释
'''
这是多行注释（docstring）
'''
```

### 缩进
Python使用**缩进**定义代码块，通常用4个空格。混用Tab和空格会导致 `IndentationError`。

### 命名规范（PEP 8）
```python
my_variable = 10        # 变量：蛇形命名法（snake_case）
MY_CONSTANT = 100       # 常量：全大写
my_function()           # 函数：蛇形命名法
MyClass                 # 类：驼峰命名（PascalCase）
```

### print() 函数
```python
print("a", "b", "c", sep="-")  # a-b-c
print("Loading...", end="")
print("Done!")                  # Loading...Done!
name = "张三"
print(f"我叫{name}，今年{25}岁")  # f-string格式化
```""",
    },
    {
        "title": "第2节：变量与数据类型",
        "sort_order": 2,
        "knowledge_point": "变量与数据类型",
        "time_estimate": 25,
        "content": """## 变量

Python中变量不需要声明类型，直接赋值即可。变量是**对象的引用**（标签）。

```python
name = "张三"       # 字符串
age = 25             # 整数
height = 1.75        # 浮点数
is_student = True    # 布尔值

# 多重赋值
x, y, z = 1, 2, 3
a, b = b, a          # 交换变量（不需要中间变量！）
```

## 数值类型

```python
a = 10
d = 1_000_000     # 下划线增强可读性
e = 0xFF          # 十六进制 = 255
f = 0b1010        # 二进制 = 10

# 运算
5 + 3    # 8
5 // 3   # 整除：1
5 % 3    # 取余：2
5 ** 3   # 幂运算：125
```

> 浮点数精度：`0.1 + 0.2` 不等于 `0.3`，所有语言共有的问题。

## 字符串（str）

```python
s = "Hello, Python"
s[0]     # 'H'
s[-1]    # 'n'
s[0:5]   # 'Hello'（切片）
s[::-1]  # 'nohtyP ,olleH'（反转）
len(s)   # 14

# 常用方法
s.strip()              # 去首尾空格
s.upper() / s.lower()  # 大小写转换
s.replace('World', 'Python')  # 替换
s.split(',')           # 分割
'-'.join(['a','b'])    # 连接 → 'a-b'
s.find('World')        # 查找位置
s.count('l')           # 计数
```

### f-string 格式化
```python
name = "张三"; age = 25; score = 92.5
print(f"姓名：{name}，年龄：{age}，成绩：{score}")
print(f"成绩：{score:.1f}")     # 保留1位小数
print(f"进度：{3/7:.1%}")       # 百分比
```

## 布尔类型（bool）

```python
True and False   # False
True or False    # True
not True         # False
5 > 3            # True
5 == 5           # True
```

## 类型转换
```python
int('123')       # 字符串→整数：123
str(123)         # 整数→字符串：'123'
float('3.14')    # 字符串→浮点数：3.14
bool(1)          # True
```""",
    },
    {
        "title": "第3节：条件判断与循环",
        "sort_order": 3,
        "knowledge_point": "流程控制",
        "time_estimate": 25,
        "content": """## if 条件判断

```python
score = 85
if score >= 90:
    grade = 'A'
elif score >= 80:
    grade = 'B'
elif score >= 70:
    grade = 'C'
elif score >= 60:
    grade = 'D'
else:
    grade = 'F'

# 三元表达式
result = '及格' if score >= 60 else '不及格'

# 链式比较（Python独有）
if 18 <= age <= 30:
    print("青年用户")
```

## for 循环

```python
fruits = ['apple', 'banana', 'orange']
for fruit in fruits:
    print(fruit)

# range() 生成数字序列
for i in range(5):        # 0 1 2 3 4
    print(i)
for i in range(1, 10, 2): # 1 3 5 7 9
    print(i)

# enumerate() 同时获取索引和值
for index, fruit in enumerate(fruits, start=1):
    print(f"{index}: {fruit}")

# zip() 并行遍历
names = ['张三', '李四', '王五']
scores = [85, 92, 78]
for name, score in zip(names, scores):
    print(f"{name}: {score}")
```

## while 循环

```python
count = 0
while count < 5:
    print(count)
    count += 1

while True:
    user_input = input("请输入 'quit' 退出：")
    if user_input == 'quit':
        break
```

## break 和 continue

```python
# break：跳出整个循环
for i in range(10):
    if i == 5: break
    print(i)  # 0 1 2 3 4

# continue：跳过当前迭代
for i in range(10):
    if i % 2 == 0: continue
    print(i)  # 1 3 5 7 9
```

## 循环的else子句（Python特有）
当循环**正常结束**（没有被break中断）时执行else：
```python
for i in range(10):
    if i == 20:
        print("找到了"); break
else:
    print("循环正常结束，没找到")
```""",
    },
    {
        "title": "第4节：列表与元组",
        "sort_order": 4,
        "knowledge_point": "列表元组",
        "time_estimate": 25,
        "content": """## 列表（List）

```python
fruits = ['apple', 'banana', 'orange']
fruits[0]      # 'apple'
fruits[-1]     # 'orange'
fruits[0:2]    # ['apple', 'banana']
len(fruits)    # 3
'apple' in fruits  # True
```

### 修改列表
```python
fruits.append('melon')     # 末尾添加
fruits.insert(1, 'kiwi')   # 指定位置插入
fruits.remove('grape')     # 删除指定元素
popped = fruits.pop()      # 删除并返回最后一个
del fruits[0]              # 删除指定位置
fruits.clear()             # 清空
```

### 列表高级操作
```python
a = [1, 2, 3]; b = [4, 5, 6]
c = a + b              # [1, 2, 3, 4, 5, 6]
d = a * 3              # [1, 2, 3, 1, 2, 3, 1, 2, 3]

numbers = [3, 1, 4, 1, 5, 9]
numbers.sort()                    # 原地排序
numbers.sort(reverse=True)        # 降序
sorted_numbers = sorted(numbers)  # 返回新排序列表
numbers.reverse()                 # 原地反转
numbers.index(4)                  # 查找索引
numbers.count(1)                  # 计数
```

### 列表推导式（Python最强特性之一）
```python
squares = [x**2 for x in range(10)]
evens = [x for x in range(20) if x % 2 == 0]
pairs = [(x, y) for x in range(3) for y in range(2)]
```

## 元组（Tuple）
元组是**不可变的**（创建后不能修改）。

```python
t1 = (1, 2, 3)
t2 = 1, 2, 3          # 括号可以省略
t3 = (1,)             # 单元素元组（逗号不能省略！）
```

### 元组解包
```python
point = (3, 4)
x, y = point
first, *middle, last = [1, 2, 3, 4, 5]
# first=1, middle=[2,3,4], last=5
```

| 场景 | 用列表还是元组？ |
|------|-----------------|
| 数据会改变 | 列表 |
| 数据不变 | 元组 |
| 函数返回多个值 | 元组 |
| 字典的键 | 元组 |""",
    },
    {
        "title": "第5节：字典与集合",
        "sort_order": 5,
        "knowledge_point": "字典集合",
        "time_estimate": 25,
        "content": """## 字典（Dictionary）

```python
user = {'name': '张三', 'age': 25, 'email': 'zhangsan@test.com'}
user['name']           # '张三'
user.get('name')       # '张三'
user.get('phone', 'N/A')  # 不存在返回默认值
user['age'] = 26       # 修改
user['phone'] = '13800138000'  # 添加
del user['phone']      # 删除
```

### 字典遍历
```python
for key in user:
    print(key)
for value in user.values():
    print(value)
for key, value in user.items():
    print(f"{key}: {value}")
```

### 字典推导式
```python
original = {'a': 1, 'b': 2, 'c': 3}
swapped = {v: k for k, v in original.items()}  # {1: 'a', 2: 'b', 3: 'c'}
passed = {k: v for k, v in scores.items() if v >= 60}
```

### 字典高级用法
```python
# 合并字典（Python 3.9+）
d1 = {'a': 1, 'b': 2}
d2 = {'b': 3, 'c': 4}
merged = d1 | d2  # {'a': 1, 'b': 3, 'c': 4}

# setdefault
user.setdefault('level', 1)
```

## 集合（Set）
集合是**无序的、不重复的**元素集合。

```python
empty_set = set()  # 不能写{}，那是字典！
numbers = {1, 2, 3, 4}
numbers.add(5)
3 in numbers  # O(1)时间复杂度，比列表快得多

# 集合运算
a = {1, 2, 3, 4}; b = {3, 4, 5, 6}
a & b  # 交集 {3, 4}
a | b  # 并集 {1, 2, 3, 4, 5, 6}
a - b  # 差集 {1, 2}
a ^ b  # 对称差集 {1, 2, 5, 6}

# 去重
numbers = [1, 2, 2, 3, 3, 3, 4]
unique = list(set(numbers))  # [1, 2, 3, 4]
```

## 数据类型对比
| 数据类型 | 符号 | 有序？ | 可变？ | 可重复？ |
|----------|------|--------|--------|----------|
| list | [] | 有序 | 可变 | 可重复 |
| tuple | () | 有序 | 不可变 | 可重复 |
| dict | {:} | 有序(3.7+) | 可变 | 键不可重复 |
| set | {} | 无序 | 可变 | 不可重复 |""",
    },
    {
        "title": "第6节：函数",
        "sort_order": 6,
        "knowledge_point": "函数",
        "time_estimate": 30,
        "content": """## 函数的定义

```python
def add(a, b):
    '''返回两个数的和'''
    return a + b

result = add(3, 5)   # result = 8
```

## 参数类型

### 位置参数
```python
def describe(name, age):
    print(f"{name}今年{age}岁")
```

### 关键字参数
```python
describe(age=25, name='张三')  # 不依赖顺序
```

### 默认参数
```python
def greet(name, greeting='Hello'):
    print(f"{greeting}, {name}!")

# 默认参数陷阱：不要用可变对象作为默认值！
def good_append(item, lst=None):  # 正确的做法
    if lst is None: lst = []
    lst.append(item)
    return lst
```

### 可变参数（*args、**kwargs）
```python
def sum_all(*numbers):
    return sum(numbers)

def print_info(**kwargs):
    for key, value in kwargs.items():
        print(f"{key}: {value}")

print_info(name='张三', age=25, city='北京')
```

## 返回值
```python
def min_max(numbers):
    return min(numbers), max(numbers)

low, high = min_max([3, 1, 4, 1, 5])  # low=1, high=5
```

## 作用域（LEGB规则）
```python
# Local → Enclosing → Global → Built-in
x = 'global'
def outer():
    x = 'enclosing'
    def inner():
        x = 'local'
        print(x)  # local
    inner()
    print(x)      # enclosing
outer()
print(x)          # global
```

## lambda 匿名函数
```python
square = lambda x: x ** 2
sorted_users = sorted(users, key=lambda u: u['age'])
doubled = list(map(lambda x: x * 2, numbers))
evens = list(filter(lambda x: x % 2 == 0, numbers))
```

## docstring
```python
def calculate_bmi(weight, height):
    '''
    计算BMI指数。
    Args:
        weight: 体重（千克）
        height: 身高（米）
    Returns:
        BMI值（浮点数）
    '''
    if weight <= 0 or height <= 0:
        raise ValueError("体重和身高必须为正数")
    return weight / (height ** 2)
```""",
    },
    {
        "title": "第7节：面向对象编程",
        "sort_order": 7,
        "knowledge_point": "面向对象",
        "time_estimate": 30,
        "content": """## 类与对象

```python
class TestCase:
    total_cases = 0  # 类属性
    
    def __init__(self, name, description):
        self.name = name
        self.description = description
        self.status = 'pending'
        TestCase.total_cases += 1
    
    def run(self):
        self.status = 'running'
        self.status = 'passed' if self._execute() else 'failed'
        return self.status
    
    def _execute(self):
        return True

tc = TestCase('登录测试', '验证正常登录流程')
tc.run()
print(tc.status)  # passed
```

## 继承（Inheritance）

```python
class Animal:
    def __init__(self, name):
        self.name = name
    def speak(self): pass

class Dog(Animal):
    def speak(self):
        return f"{self.name}说：汪汪！"

class Cat(Animal):
    def speak(self):
        return f"{self.name}说：喵喵！"

# 多态：不同对象对同一方法有不同表现
animals = [Dog('旺财'), Cat('咪咪')]
for animal in animals:
    print(animal.speak())
```

### super() 调用父类方法
```python
class APITestRunner(TestRunner):
    def __init__(self, name, base_url):
        super().__init__(name)  # 调用父类的__init__
        self.base_url = base_url
```

## 封装（Encapsulation）

```python
class BankAccount:
    def __init__(self, owner, balance=0):
        self.owner = owner          # 公开
        self._bank = 'ICBC'         # 受保护（约定）
        self.__balance = balance    # 私有（名称改编）
    
    def get_balance(self):
        return self.__balance
```

## 特殊方法（魔术方法）

```python
class TestResult:
    def __str__(self):
        return f"{'✓' if self.passed else '✗'} {self.case_name}"
    
    def __repr__(self):
        return f"TestResult('{self.case_name}', {self.passed})"
    
    def __eq__(self, other):
        return self.case_name == other.case_name
```

## @property 装饰器

```python
class Rectangle:
    def __init__(self, width, height):
        self._width = width
        self._height = height
    
    @property
    def area(self):
        return self._width * self._height  # rect.area（不用括号！）
    
    @property
    def width(self):
        return self._width
    
    @width.setter
    def width(self, value):
        if value <= 0:
            raise ValueError("宽度必须为正数")
        self._width = value
```""",
    },
    {
        "title": "第8节：文件操作",
        "sort_order": 8,
        "knowledge_point": "文件操作",
        "time_estimate": 20,
        "content": """## 文件操作基础

```python
# 推荐：with语句（自动关闭文件）
with open('data.txt', 'r', encoding='utf-8') as f:
    content = f.read()
    print(content)
```

### 文件模式
| 模式 | 说明 |
|------|------|
| 'r' | 只读（默认） |
| 'w' | 只写（文件存在则清空） |
| 'a' | 追加 |
| 'x' | 创建新文件 |
| 'r+' | 读写 |
| 'b' | 二进制模式（如'rb'） |

## 读取文件

```python
# read() - 读取全部
with open('data.txt', 'r') as f:
    content = f.read()

# 逐行遍历（最佳实践，内存友好）
with open('data.txt', 'r') as f:
    for line in f:
        print(line.strip())

# readlines() - 所有行为列表
with open('data.txt', 'r') as f:
    lines = f.readlines()
```

## 写入文件

```python
with open('output.txt', 'w', encoding='utf-8') as f:
    f.write('Hello, World!\\n')
    f.write('第二行内容\\n')

with open('output.txt', 'a', encoding='utf-8') as f:
    f.write('追加的一行\\n')
```

## 处理JSON文件

```python
import json

# 读取JSON
with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

# 写入JSON
data = {'users': [{'name': '张三', 'age': 25}], 'total': 1}
with open('users.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
```

## 路径处理

```python
import os
current_dir = os.path.dirname(__file__)
file_path = os.path.join(current_dir, 'data', 'config.json')
os.path.exists(file_path)  # 检查是否存在
```""",
    },
    {
        "title": "第9节：异常处理",
        "sort_order": 9,
        "knowledge_point": "异常处理",
        "time_estimate": 20,
        "content": """## 异常类型

```python
10 / 0              # ZeroDivisionError
'hello' + 5         # TypeError
open('不存在.txt')   # FileNotFoundError
{'a': 1}['b']       # KeyError
```

## try-except 捕获异常

```python
try:
    value = int(input("请输入数字: "))
    result = 100 / value
except ValueError:
    print("请输入有效的数字！")
except ZeroDivisionError:
    print("不能除以零！")
except Exception as e:
    print(f"未知错误: {e}")
else:
    # try成功时执行
    print(f"结果: {result}")
finally:
    # 无论是否异常都执行
    print("清理资源")
```

## 手动抛出异常（raise）

```python
def validate_age(age):
    if age < 0:
        raise ValueError("年龄不能为负数")
    if age > 150:
        raise ValueError("年龄不能超过150岁")

try:
    validate_age(-5)
except ValueError as e:
    print(e)
```

## 自定义异常

```python
class TestExecutionError(Exception):
    def __init__(self, case_name, message):
        self.case_name = case_name
        super().__init__(f"[{case_name}] {message}")

class TimeoutError(TestExecutionError):
    pass
```

## 测试中的异常处理模板

```python
import requests

def api_call(url, timeout=30):
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        print(f"请求超时: {url}")
        return None
    except requests.exceptions.ConnectionError:
        print(f"连接失败: {url}")
        return None
    except requests.exceptions.HTTPError as e:
        print(f"HTTP错误: {e.response.status_code}")
        return None
```""",
    },
    {
        "title": "第10节：常用标准库与测试脚本实战",
        "sort_order": 10,
        "knowledge_point": "标准库",
        "time_estimate": 25,
        "content": """## datetime - 日期时间

```python
from datetime import datetime, timedelta

now = datetime.now()
print(now.strftime("%Y-%m-%d %H:%M:%S"))

tomorrow = now + timedelta(days=1)
three_days_ago = now - timedelta(days=3)
diff = datetime(2024, 2, 1) - datetime(2024, 1, 15)
print(diff.days)  # 17
```

## json - JSON数据处理

```python
import json
data = {'name': '张三', 'skills': ['Python', 'SQL']}
json_str = json.dumps(data, ensure_ascii=False, indent=2)
data = json.loads('{"name": "张三", "age": 25}')
```

## random - 随机数

```python
import random
random.randint(1, 10)         # [1, 10]随机整数
random.choice([1, 3, 5])      # 随机选择
random.sample(range(10), 3)   # 不放回抽样
random.shuffle(lst)           # 打乱列表
random.seed(42)               # 设置随机种子
```

## 测试工程师实用脚本模板

```python
import requests
import json
import time
from datetime import datetime

def api_test(url, method='GET', headers=None, data=None, expected_status=200):
    start = time.time()
    try:
        if method.upper() == 'GET':
            resp = requests.get(url, headers=headers, timeout=30)
        elif method.upper() == 'POST':
            resp = requests.post(url, headers=headers, json=data, timeout=30)
        
        elapsed = time.time() - start
        passed = resp.status_code == expected_status
        
        return {
            'url': url, 'method': method,
            'status_code': resp.status_code,
            'passed': passed, 'elapsed': round(elapsed, 3),
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        return {
            'url': url, 'passed': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

# 批量测试
test_cases = [
    {'url': 'https://api.example.com/health', 'method': 'GET'},
    {'url': 'https://api.example.com/login', 'method': 'POST',
     'data': {'username': 'admin', 'password': '123456'}},
]

results = []
for case in test_cases:
    result = api_test(**case)
    results.append(result)
    status = '✓' if result['passed'] else '✗'
    print(f"  {status} {case['method']} {case['url']}")

print(f"通过: {sum(1 for r in results if r['passed'])}/{len(results)}")
```""",
    },
]

# ── 路径5: 计算机基础与网络知识 (5节) ──
LESSON_CONTENT["计算机基础与网络知识"] = [
    {
        "title": "第1节：HTTP协议深度解析",
        "sort_order": 1,
        "knowledge_point": "HTTP协议",
        "time_estimate": 25,
        "content": """## HTTP请求结构

```
POST /api/login HTTP/1.1          ← 请求行（方法 URL 版本）
Host: www.example.com             ← 请求头
Content-Type: application/json
Authorization: Bearer token123

{"username":"admin","password":"123"}  ← 请求体
```

## HTTP响应结构

```
HTTP/1.1 200 OK                   ← 状态行
Content-Type: application/json    ← 响应头
Content-Length: 42

{"status":"success","token":"..."} ← 响应体
```

## HTTP方法

| 方法 | 用途 | 幂等 | 安全 |
|------|------|------|------|
| GET | 获取资源 | 是 | 是 |
| POST | 创建资源 | 否 | 否 |
| PUT | 完整更新 | 是 | 否 |
| PATCH | 部分更新 | 否 | 否 |
| DELETE | 删除资源 | 是 | 否 |
| HEAD | 获取头部 | 是 | 是 |
| OPTIONS | 查看支持的方法 | 是 | 是 |

## HTTP状态码速查

- **2xx 成功**：200 OK、201 Created、204 No Content
- **3xx 重定向**：301 永久重定向、302 临时重定向、304 Not Modified
- **4xx 客户端错误**：400 Bad Request、401 Unauthorized、403 Forbidden、404 Not Found、405 Method Not Allowed、429 Too Many Requests
- **5xx 服务器错误**：500 Internal Server Error、502 Bad Gateway、503 Service Unavailable、504 Gateway Timeout

## HTTPS
HTTPS = HTTP + SSL/TLS。数据传输过程中被加密。
```bash
openssl s_client -connect example.com:443 -servername example.com
```""",
    },
    {
        "title": "第2节：TCP/IP与网络基础",
        "sort_order": 2,
        "knowledge_point": "TCP/IP",
        "time_estimate": 20,
        "content": """## TCP/IP四层模型

| 层 | 协议 | 说明 |
|-----|------|------|
| 应用层 | HTTP/DNS/FTP/SSH | 应用程序间通信 |
| 传输层 | TCP/UDP | 端到端数据传输 |
| 网络层 | IP/ICMP/ARP | 路由和寻址 |
| 链路层 | Ethernet/WiFi | 物理网络传输 |

## TCP三次握手

```
客户端 → SYN → 服务器     (我想建立连接)
客户端 ← SYN+ACK ← 服务器 (好的，我也想)
客户端 → ACK → 服务器     (收到，连接建立)
```

## TCP四次挥手

```
客户端 → FIN → 服务器     (我没有数据要发了)
客户端 ← ACK ← 服务器     (知道了)
客户端 ← FIN ← 服务器     (我也没有了)
客户端 → ACK → 服务器     (好的，再见)
```

## TCP vs UDP

| 对比 | TCP | UDP |
|------|-----|-----|
| 连接 | 面向连接 | 无连接 |
| 可靠性 | 可靠（确认重传） | 不可靠 |
| 速度 | 较慢 | 较快 |
| 场景 | HTTP、数据库、文件传输 | 视频直播、游戏、DNS |

## 常用网络调试命令

```bash
ping google.com          # 连通性测试
tracert google.com       # 路由追踪(Windows)
traceroute google.com    # 路由追踪(Linux)
nslookup example.com     # DNS查询
netstat -an              # 查看网络连接
```""",
    },
    {
        "title": "第3节：RESTful API设计规范",
        "sort_order": 3,
        "knowledge_point": "RESTful API",
        "time_estimate": 20,
        "content": """## RESTful API核心原则

**REST**（Representational State Transfer）是目前最流行的API设计风格。

### 六大约束
1. **客户端-服务器**：前后端分离
2. **无状态**：每个请求包含所有必要信息
3. **可缓存**：响应应声明是否可缓存
4. **统一接口**：资源通过URL标识，使用标准HTTP方法
5. **分层系统**：客户端不知道是否直接连接服务器
6. **按需代码**（可选）：服务器可向客户端发送可执行代码

## URL设计规范

```
GET    /api/users           # 获取用户列表
GET    /api/users/123       # 获取用户123
POST   /api/users           # 创建用户
PUT    /api/users/123       # 完整更新用户123
PATCH  /api/users/123       # 部分更新用户123
DELETE /api/users/123       # 删除用户123

# 子资源
GET    /api/users/123/orders        # 用户123的订单列表
GET    /api/users/123/orders/456    # 用户123的456号订单
```

## 命名规范

| 规则 | 正确 ✅ | 错误 ❌ |
|------|---------|---------|
| 使用名词复数 | `/users` | `/getUsers` |
| 小写字母 | `/user-profiles` | `/UserProfiles` |
| 连字符分隔 | `/order-items` | `/orderItems`、`/order_items` |
| 避免动词 | `POST /users` | `/createUser` |
| 嵌套不超过2层 | `/users/1/orders` | `/users/1/orders/5/items` |

## 请求与响应设计

```json
// 请求（POST /api/users）
{
    "username": "zhangsan",
    "email": "zhangsan@test.com",
    "age": 25
}

// 成功响应（201 Created）
{
    "code": 0,
    "message": "创建成功",
    "data": {
        "id": 123,
        "username": "zhangsan",
        "email": "zhangsan@test.com",
        "created_at": "2024-01-15T10:30:00Z"
    }
}

// 错误响应（400 Bad Request）
{
    "code": 1001,
    "message": "用户名已存在",
    "details": {
        "field": "username",
        "reason": "duplicate"
    }
}
```

## 认证方式

| 方式 | 说明 | 使用场景 |
|------|------|----------|
| Basic Auth | 用户名:密码 Base64编码 | 内部工具、简单场景 |
| Token | 登录后获取token | Web应用 |
| JWT | 自包含的JSON Token | 微服务、分布式系统 |
| OAuth 2.0 | 第三方授权 | 开放平台 |
| API Key | 固定密钥 | 机器间通信 |

```bash
# Bearer Token
curl -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." https://api.example.com/users
```""",
    },
    {
        "title": "第4节：DNS与域名解析",
        "sort_order": 4,
        "knowledge_point": "DNS",
        "time_estimate": 15,
        "content": """## DNS概述

DNS（Domain Name System）将域名转换为IP地址，是互联网的电话簿。

```
用户输入 www.example.com
        ↓
DNS解析：www.example.com → 93.184.216.34
        ↓
浏览器向 93.184.216.34 发送HTTP请求
```

## DNS解析过程

```
1. 浏览器缓存 → 2. 操作系统缓存(Hosts文件)
→ 3. 本地DNS服务器 → 4. 根域名服务器
→ 5. .com顶级域名服务器 → 6. example.com权威DNS服务器
```

## DNS记录类型

| 类型 | 用途 | 示例 |
|------|------|------|
| A | 域名→IPv4地址 | example.com → 93.184.216.34 |
| AAAA | 域名→IPv6地址 | example.com → 2606:2800:220:1:... |
| CNAME | 域名别名 | www.example.com → example.com |
| MX | 邮件服务器 | example.com → mail.example.com |
| TXT | 文本记录 | SPF、DKIM、域名验证 |
| NS | 域名服务器 | 指定DNS服务器 |

## 测试中的DNS问题排查

```bash
# DNS查询
nslookup example.com
dig example.com

# hosts文件位置
# Windows: C:\\Windows\\System32\\drivers\\etc\\hosts
# Linux: /etc/hosts

# 常见hosts配置（测试环境）
# 192.168.1.100  api.test.com
# 192.168.1.101  admin.test.com
```""",
    },
    {
        "title": "第5节：WebSocket与实时通信",
        "sort_order": 5,
        "knowledge_point": "WebSocket",
        "time_estimate": 15,
        "content": """## WebSocket概述

WebSocket是一种在单个TCP连接上进行**全双工通信**的协议。与HTTP不同，WebSocket连接建立后，服务器可以主动向客户端推送数据。

## HTTP vs WebSocket

| 对比 | HTTP | WebSocket |
|------|------|-----------|
| 通信方式 | 请求-响应（半双工） | 全双工 |
| 连接 | 短连接/长连接 | 持久连接 |
| 服务器推送 | 不支持（需轮询） | 原生支持 |
| 适用场景 | RESTful API | 实时消息、监控大屏 |

## WebSocket握手

```
客户端请求：
GET /chat HTTP/1.1
Host: server.example.com
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==
Sec-WebSocket-Version: 13

服务器响应：
HTTP/1.1 101 Switching Protocols
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Accept: s3pPLMBiTxaQ9kYGzzhZRbK+xOo=
```

## 测试WebSocket

```bash
# 使用wscat工具
npm install -g wscat
wscat -c ws://localhost:5001/ws

# Python测试WebSocket
# pip install websocket-client
import websocket
ws = websocket.WebSocket()
ws.connect("ws://localhost:5001/ws")
ws.send('{"type": "ping"}')
result = ws.recv()
print(result)
ws.close()
```""",
    },
]

# ── 路径6: 测试用例设计方法 (8节) ──
LESSON_CONTENT["测试用例设计方法"] = [
    {
        "title": "第1节：等价类划分法",
        "sort_order": 1,
        "knowledge_point": "等价类划分",
        "time_estimate": 25,
        "content": """## 等价类划分法的定义

等价类划分法（Equivalence Partitioning）是黑盒测试中最基础、最常用的测试用例设计方法。核心思想：**将所有可能的输入数据划分为若干个等价类，从每个等价类中选取少量有代表性的数据作为测试用例。**

基于合理假设：某个等价类中的一个测试用例发现了缺陷，该等价类中其他测试用例也很可能发现相同的缺陷；反之亦然。

## 有效等价类与无效等价类

**有效等价类**：对规格说明合理的、有意义的输入数据构成的集合。用于验证程序实现了规定的功能。

**无效等价类**：不合理的、无意义的输入数据。用于验证程序对异常输入的处理能力。

## 操作步骤

1. 阅读需求规格说明，确定输入条件和取值范围
2. 为每个输入条件划分等价类（一个有效等价类+若干个无效等价类）
3. 为每个等价类分配唯一编号
4. 设计测试用例尽可能覆盖多个有效等价类
5. 每个无效等价类至少一个独立测试用例（程序遇到第一个错误就可能终止）

## 实战：手机号输入框等价类划分

需求：手机号必填，11位数字，以1开头，第二位为3456789之一。

**有效等价类**：
- E1：以1开头，第二位3-9，11位全数字（如13800138000）

**无效等价类**：
- I1：空值（未填写）
- I2：少于11位（如1380013800）
- I3：多于11位（如138001380001）
- I4：不以1开头（如23800138000）
- I5：第二位不在3-9范围（如12000138000）
- I6：包含非数字字符（如1380013800A）
- I7：包含特殊符号（如138-0013-8000）

**测试用例设计**：

| 用例ID | 输入值 | 覆盖等价类 | 预期结果 |
|--------|--------|-----------|----------|
| TC_001 | 13800138000 | E1 | 通过校验 |
| TC_002 | (空) | I1 | 提示"手机号不能为空" |
| TC_003 | 1380013800 | I2 | 提示"手机号必须为11位" |
| TC_004 | 138001380001 | I3 | 提示"手机号必须为11位" |
| TC_005 | 23800138000 | I4 | 提示"手机号格式不正确" |
| TC_006 | 1380013800A | I6 | 提示"手机号只能包含数字" |""",
    },
    {
        "title": "第2节：边界值分析法",
        "sort_order": 2,
        "knowledge_point": "边界值分析",
        "time_estimate": 25,
        "content": """## 边界值分析法的原理

边界值分析法（Boundary Value Analysis, BVA）是等价类划分法的有力补充。大量实践表明，**程序中的缺陷往往集中在输入或输出范围的边界上**。因为开发人员在写边界条件时容易出现"差1错误"（Off-by-One Error），例如将 `>=` 写成 `>`。

核心思想：选择刚好等于、刚好大于或刚好小于边界值的测试数据来设计测试用例。

## 边界值选取规则

对于范围 [min, max]：

| 边界点 | 含义 | 示例(min=1, max=100) |
|--------|------|----------------------|
| min-1 | 刚好小于最小值 | 0 |
| min | 等于最小值 | 1 |
| min+1 | 刚好大于最小值 | 2 |
| max-1 | 刚好小于最大值 | 99 |
| max | 等于最大值 | 100 |
| max+1 | 刚好大于最大值 | 101 |

通常还需要一个正常值（如50）作为对照。

## 实战：年龄输入框边界值测试

需求：年龄输入框，接受0到150之间的整数。

| 用例ID | 输入值 | 类型 | 预期结果 |
|--------|--------|------|----------|
| TC_AGE_001 | -1 | 边界值(min-1) | 提示"年龄不能为负数" |
| TC_AGE_002 | 0 | 边界值(min) | 通过校验 |
| TC_AGE_003 | 1 | 边界值(min+1) | 通过校验 |
| TC_AGE_004 | 25 | 正常值 | 通过校验 |
| TC_AGE_005 | 149 | 边界值(max-1) | 通过校验 |
| TC_AGE_006 | 150 | 边界值(max) | 通过校验 |
| TC_AGE_007 | 151 | 边界值(max+1) | 提示"年龄不能超过150" |

## 边界值分析的两个假设

**单缺陷假设**：缺陷很少由两个或多个缺陷同时导致。因此测试用例中通常只让一个变量取边界值，其他取正常值。

**健壮性测试**：除了有效边界值，还要测试无效边界值（min-1和max+1），以验证程序的异常处理能力。

## 实战：密码长度边界值测试

需求：密码长度6-20位。

| 用例ID | 密码长度 | 密码示例 | 预期结果 |
|--------|----------|----------|----------|
| TC_PW_001 | 5 | "12345" | 提示"密码至少6位" |
| TC_PW_002 | 6 | "123456" | 通过校验 |
| TC_PW_003 | 7 | "1234567" | 通过校验 |
| TC_PW_004 | 12 | "123456789012" | 通过校验 |
| TC_PW_005 | 19 | "1234567890123456789" | 通过校验 |
| TC_PW_006 | 20 | "12345678901234567890" | 通过校验 |
| TC_PW_007 | 21 | "123456789012345678901" | 提示"密码最多20位" |

## 边界值分析的最佳实践

1. **先等价类划分，再边界值分析**：两者配合使用效果最佳
2. **关注隐含边界**：如内存限制、数据库字段长度等
3. **数值边界≠逻辑边界**：如"前100名用户享受折扣"，100既是数值边界也是逻辑边界
4. **关注输出边界**：不仅是输入有边界，输出也有（如报表最多导出多少条）""",
    },
    {
        "title": "第3节：判定表法",
        "sort_order": 3,
        "knowledge_point": "判定表",
        "time_estimate": 25,
        "content": """## 判定表法概述

判定表法（Decision Table Testing）适用于**多个条件组合影响结果**的场景。当系统的业务规则比较复杂，存在多个输入条件的组合，每种组合产生不同的结果时，判定表是最佳选择。

## 判定表的组成

判定表由四部分组成：
1. **条件桩**：列出所有条件
2. **条件项**：每个条件的取值（Y/N或具体值）
3. **动作桩**：列出所有可能的操作/结果
4. **动作项**：在对应条件组合下应采取的动作

## 实战：信用卡额度审批

需求：某银行信用卡额度审批规则如下：
- 年收入>10万且信用评分>700：批准，额度5万
- 年收入>10万但信用评分≤700：审批中，需人工审核
- 年收入≤10万但信用评分>700：批准，额度2万
- 年收入≤10万且信用评分≤700：拒绝
- 无论哪种情况，如果是老客户：额度上浮20%

**条件桩**：
- C1：年收入>10万？
- C2：信用评分>700？
- C3：是老客户？

**动作桩**：
- A1：批准
- A2：审批中
- A3：拒绝
- A4：额度5万
- A5：额度2万
- A6：额度上浮20%

**判定表**：

| 条件/动作 | 规则1 | 规则2 | 规则3 | 规则4 |
|-----------|-------|-------|-------|-------|
| C1: 年收入>10万 | Y | Y | N | N |
| C2: 信用评分>700 | Y | N | Y | N |
| **动作** | | | | |
| 结果 | 批准 | 审批中 | 批准 | 拒绝 |
| 额度 | 5万 | - | 2万 | - |

注意老客户是独立维度，需要与上述4条规则结合，但在判定表中通常单独处理或作为扩展规则处理。

## 判定表的化简

如果两个规则的动作完全相同，且条件只差一个（其他条件相同），则可以将这两个规则合并。

```
化简前：C1=Y, C2=Y → A1; C1=Y, C2=N → A1
化简后：C1=Y, C2=- → A1（"-"表示任意值）
```

## 实战：登录功能判定表

需求：用户登录需要同时满足账号存在、密码正确、账号未被锁定。

| 条件/动作 | 规则1 | 规则2 | 规则3 | 规则4 |
|-----------|-------|-------|-------|-------|
| 账号存在 | Y | Y | Y | N |
| 密码正确 | Y | Y | N | - |
| 账号未锁定 | Y | N | - | - |
| **动作** | | | | |
| 登录成功 | ✓ | | | |
| 提示"账号被锁定" | | ✓ | | |
| 提示"密码错误" | | | ✓ | |
| 提示"账号不存在" | | | | ✓ |

## 判定表法的优势和局限

**优势**：
- 保证覆盖所有条件组合，不会遗漏
- 适合复杂业务规则的测试
- 表格形式直观易懂

**局限**：
- 条件越多，规则数呈指数增长（n个条件=2^n条规则）
- 不适合输入值连续变化的情况（用边界值+等价类）

> n个二值条件最多产生2^n条规则。5个条件=32条，6个条件=64条。因此实际应用中需要化简。""",
    },
    {
        "title": "第4节：因果图法与正交实验法",
        "sort_order": 4,
        "knowledge_point": "因果图与正交",
        "time_estimate": 25,
        "content": """## 因果图法（Cause-Effect Graphing）

因果图法是一种利用图解法分析输入（原因）与输出（结果）之间关系的测试设计方法。

### 因果图的基本符号

**原因（Cause）和结果（Effect）的关系**：
- **恒等（Identity）**：原因出现→结果出现
- **非（NOT）**：原因出现→结果不出现
- **与（AND）**：多个原因同时出现→结果出现
- **或（OR）**：任一原因出现→结果出现

### 约束条件符号
- **E（Exclusive）**：原因之间互斥，最多一个为真
- **I（Include）**：至少一个为真
- **O（Only One）**：有且仅有一个为真
- **R（Require）**：原因A出现，原因B必须出现

### 因果图法的步骤
1. 分析需求规格，找出所有原因（输入条件）和结果（输出/操作）
2. 绘制因果图，表示原因和结果的逻辑关系
3. 标注约束条件
4. 将因果图转化为判定表
5. 根据判定表设计测试用例

## 正交实验法（Orthogonal Array Testing）

正交实验法用于**多因素多水平**的测试场景，通过选择有代表性的组合来大幅减少测试用例数量。

### 核心概念
- **因素（Factor）**：测试中变化的变量（如操作系统、浏览器、分辨率）
- **水平（Level）**：每个因素的可能取值

### 正交表表示
L_n(q^k) 表示：
- n：需要的实验次数（即测试用例数）
- q：每个因素的水平数
- k：最多能容纳的因素数

例如：L_9(3^4) 表示9个用例、每个因素3个水平、最多4个因素。

### 实战：Web兼容性测试

因素与水平：
- A: 操作系统（Windows, macOS, Linux）→ 3个水平
- B: 浏览器（Chrome, Firefox, Edge）→ 3个水平
- C: 分辨率（1920×1080, 2560×1440, 1366×768）→ 3个水平

全组合：3×3×3 = 27个用例
使用正交表 L_9(3^4)：只需要9个用例！

| 用例 | 操作系统 | 浏览器 | 分辨率 |
|------|----------|--------|--------|
| 1 | Windows | Chrome | 1920×1080 |
| 2 | Windows | Firefox | 2560×1440 |
| 3 | Windows | Edge | 1366×768 |
| 4 | macOS | Chrome | 2560×1440 |
| 5 | macOS | Firefox | 1366×768 |
| 6 | macOS | Edge | 1920×1080 |
| 7 | Linux | Chrome | 1366×768 |
| 8 | Linux | Firefox | 1920×1080 |
| 9 | Linux | Edge | 2560×1440 |

## 对比总结

| 方法 | 适用场景 | 用例数量 | 覆盖程度 |
|------|----------|----------|----------|
| 全组合 | 所有因素组合 | 指数增长 | 100%覆盖 |
| 因果图 | 有逻辑关系的条件组合 | 约2^n | 全面覆盖 |
| 正交实验 | 多因素多水平 | 大幅减少 | 均匀分布 |
| 两两组合(Pairwise) | 多因素多水平 | 较少 | 覆盖两两组合 |""",
    },
    {
        "title": "第5节：场景法与业务流程测试",
        "sort_order": 5,
        "knowledge_point": "场景法",
        "time_estimate": 25,
        "content": """## 场景法概述

场景法（Scenario Testing）通过模拟用户使用软件的真实场景来设计测试用例。核心是**用业务流把多个功能点串联起来**，真实模拟用户的操作路径。

场景法设计基础是**事件流**：
- **基本流（Happy Path）**：最正常、最常用的业务流程，一切顺利
- **备选流（Alternative Flow）**：异常情况或分支流程

## 实战：ATM取款场景

**基本流**：
```
插卡 → 输入密码 → 选择"取款" → 输入金额 → 确认 → 取钞 → 退卡
```

**备选流**：
- 备选流1：密码错误（输入密码→密码错误→重新输入→正确→继续）
- 备选流2：余额不足（输入金额→余额不足→提示→返回）
- 备选流3：超过每日限额（输入金额→超过限额→提示→返回）
- 备选流4：取款机余额不足（确认→机器余额不足→提示→退卡）
- 备选流5：超时未操作（任何步骤→超时→吞卡）

## 场景法测试用例设计

| 场景ID | 场景描述 | 经过的流 | 预期结果 |
|--------|----------|----------|----------|
| SC_001 | 取款成功 | 基本流 | 成功取款，余额正确减少 |
| SC_002 | 密码第一次错误 | 备选流1→基本流 | 重新输入后成功 |
| SC_003 | 密码3次错误 | 备选流1×3 | 吞卡，账户锁定 |
| SC_004 | 余额不足 | 备选流2 | 提示余额不足，不扣款 |
| SC_005 | 超过每日限额 | 备选流3 | 提示超过限额 |
| SC_006 | 取消操作 | 基本流→取消 | 退卡，交易取消 |

## 场景法的适用场景

| 场景类型 | 说明 | 示例 |
|----------|------|------|
| 端到端流程 | 完整业务流程 | 注册→登录→选购→支付→收货 |
| 用户旅程 | 特定角色的操作路径 | 管理员：创建用户→分配权限→审核 |
| 异常恢复 | 系统故障后的恢复 | 支付中断→重新发起→订单状态恢复 |
| 并发场景 | 多人同时操作 | 两人同时抢最后一个库存 |

## 场景法设计的注意事项

1. **从用户角度思考**：不要只从功能角度设计场景
2. **覆盖关键路径**：至少覆盖核心业务流程的Happy Path
3. **不要遗漏异常场景**：
   - 必填项未填
   - 网络中断/超时
   - 数据边界
   - 重复提交
4. **考虑数据的生命周期**：如订单从创建→支付→发货→签收→退货的完整链路""",
    },
    {
        "title": "第6节：错误推测法与探索性测试",
        "sort_order": 6,
        "knowledge_point": "错误推测",
        "time_estimate": 20,
        "content": """## 错误推测法（Error Guessing）

错误推测法基于测试人员的**经验、直觉和对系统的了解**，推测程序中可能存在的错误，有针对性地设计测试用例。

### 常见推测方向

| 容易出错的情况 | 推测内容 | 测试方法 |
|---------------|----------|----------|
| 空值/Null | 未输入就提交 | 留空必填项提交 |
| 特殊字符 | 引号、尖括号、表情符号 | 输入`<script>alert(1)</script>` |
| 超长输入 | 超过字段限制 | 输入10000个字符 |
| 空格处理 | 前后空格 | "  admin  "是否被trim |
| 并发重复 | 快速双击提交 | 快速连续点击提交按钮 |
| 时间边界 | 跨天/跨月/跨年 | 23:59:59和00:00:00 |
| 数据类型 | 类型不匹配 | 数字框输入字母 |
| 数据依赖 | 删除关联数据 | 删除已被引用的记录 |

### 错误推测法的增强版：错误猜测清单

**输入验证类**：
- [ ] 输入空值/空格
- [ ] 输入SQL注入语句（`' OR '1'='1`）
- [ ] 输入XSS脚本（`<script>alert('xss')</script>`）
- [ ] 输入超长字符串
- [ ] 输入特殊Unicode字符（emoji等）
- [ ] 输入负数/零
- [ ] 上传超大文件
- [ ] 上传非预期格式文件

**业务逻辑类**：
- [ ] 重复提交表单
- [ ] 后退按钮/刷新页面
- [ ] 同时打开多个Tab操作
- [ ] 使用过期Session/Token
- [ ] 越权访问（修改URL参数）

## 探索性测试（Exploratory Testing）

探索性测试是一种**同时进行测试设计、测试执行和学习**的测试方法。它不是随机的"乱点"，而是有策略的自由测试。

### 探索性测试的核心要素
1. **测试宪章（Charter）**：定义本次探索的目标和范围
2. **时间盒（Timebox）**：固定时间（如90分钟）聚焦探索
3. **笔记（Session Notes）**：记录发现了什么、怎么发现的
4. **汇报（Debrief）**：向团队汇报探索结果

### 测试宪章模板
```
探索：[功能/模块名称]
目标：发现[某类]问题
时间：90分钟
范围：[具体功能范围]
策略：[探索思路]
```

### 探索性测试的常用策略

**漫游测试（Tour Testing）**：
- **指南针漫游**：跟随需求文档/用户手册测试
- **地标漫游**：逐个测试关键功能
- **极限漫游**：测试极端值、极限场景
- **深夜漫游**：模拟夜间批量任务运行
- **快递员漫游**：跟踪数据在系统中的流转""",
    },
    {
        "title": "第7节：白盒测试方法",
        "sort_order": 7,
        "knowledge_point": "白盒测试",
        "time_estimate": 25,
        "content": """## 白盒测试概述

白盒测试（White-box Testing）基于**代码内部逻辑**设计测试用例。测试人员需要阅读源代码，理解程序的控制流和数据流。

## 逻辑覆盖标准

### 语句覆盖（Statement Coverage）
要求每条可执行语句至少执行一次。最弱的标准。

```python
def classify(score):
    if score >= 90:
        return 'A'
    elif score >= 60:
        return 'B'
    else:
        return 'C'
```
语句覆盖只需一个用例 score=90 就能覆盖大部分行，但else分支未覆盖。

### 判定覆盖（Decision/Branch Coverage）
要求每个判断的真假分支至少执行一次。

```python
if a > 0 and b > 0:  # True分支和False分支
```
需要：a>0且b>0（True分支）和 a≤0或b≤0（False分支）

### 条件覆盖（Condition Coverage）
要求每个条件的所有可能取值至少出现一次。

```python
if a > 0 and b > 0:  # a>0的True/False, b>0的True/False各至少一次
```

### 判定-条件覆盖
同时满足判定覆盖和条件覆盖。

### 路径覆盖（Path Coverage）
要求程序中每条可能的路径至少执行一次。最强标准但路径数可能爆炸性增长。

## 覆盖标准的强度关系

```
语句覆盖 < 判定覆盖 < 条件覆盖 < 判定-条件覆盖 < 路径覆盖
```

## 基本路径测试法

通过程序的**环路复杂度（Cyclomatic Complexity）**确定基本路径集合。

环路复杂度 V(G) = E - N + 2
- E：边的数量
- N：节点的数量
- 或 V(G) = P + 1（P为判定节点数）

## 代码审查（Code Review）

代码审查是白盒测试的重要补充手段。

**检查清单**：
- [ ] 变量是否初始化？
- [ ] 数组下标是否会越界？
- [ ] 循环终止条件是否正确？
- [ ] 除零保护了吗？
- [ ] 资源是否正确释放（文件句柄、数据库连接）？
- [ ] 异常处理是否完善？
- [ ] 日志是否记录了足够信息？
- [ ] 是否有硬编码的密码/密钥？""",
    },
    {
        "title": "第8节：测试用例评审与维护",
        "sort_order": 8,
        "knowledge_point": "用例评审",
        "time_estimate": 20,
        "content": """## 测试用例评审

### 评审的目的
1. 发现遗漏的测试场景
2. 消除冗余的测试用例
3. 确保用例清晰可执行
4. 统一团队的测试设计思路
5. 提高测试用例质量

### 评审checklist

**完整性**：
- [ ] 所有需求都有对应的测试用例吗？
- [ ] 正常场景和异常场景都覆盖了吗？
- [ ] 边界条件覆盖了吗？

**正确性**：
- [ ] 预期结果与需求一致吗？
- [ ] 前置条件描述准确吗？
- [ ] 测试数据合理吗？

**清晰性**：
- [ ] 步骤描述清晰吗？新人能看懂吗？
- [ ] 用例编号符合规范吗？
- [ ] 是否过于简单（无意义）或过于复杂？

**可维护性**：
- [ ] 用例之间有依赖吗？
- [ ] 是否便于自动化？

### 评审流程
```
1. 作者自审 → 2. 发送评审邀请 → 3. 评审会议
→ 4. 记录问题 → 5. 作者修改 → 6. 复审确认
```

## 测试用例维护

### 什么时候需要更新用例？
- 需求变更
- 发现新缺陷后补充用例
- 测试策略调整
- 用例长期未执行
- 自动化用例失败率过高

### 用例优先级划分
| 优先级 | 说明 | 执行频率 |
|--------|------|----------|
| P0 | 核心功能/冒烟测试 | 每次提交 |
| P1 | 主要功能/回归测试 | 每日构建 |
| P2 | 次要功能 | 每次迭代 |
| P3 | 边缘场景/探索性 | 按需 |

## 需求追溯矩阵（RTM）

```
需求 → 测试用例 → 测试结果 → 缺陷
RT-001 → TC_001, TC_002 → Pass → (无缺陷)
RT-002 → TC_003, TC_004 → Fail → BUG-001
```

RTM帮助我们确保：
- 每个需求都有测试覆盖
- 测试结果可追溯到需求
- 评估需求的测试状态""",
    },
]

# ── 路径7: 缺陷管理与追踪 (6节) ──
LESSON_CONTENT["缺陷管理与追踪"] = [
    {
        "title": "第1节：缺陷生命周期详解",
        "sort_order": 1,
        "knowledge_point": "缺陷流程",
        "time_estimate": 20,
        "content": """## 缺陷生命周期

```
New（新建）→ Open（打开/分配）→ Fixed（已修复）→ Verified（已验证）→ Closed（关闭）
                                   ↓                       ↓
                              Reopened（重新打开）    Rejected（拒绝）
```

### 各阶段详解

| 状态 | 角色 | 操作 | 下一状态 |
|------|------|------|----------|
| New | 测试 | 发现并提交缺陷 | Open/Rejected |
| Open | 开发经理 | 确认并分配给开发 | Fixed/Rejected |
| Fixed | 开发 | 修复代码并提交 | Verified |
| Verified | 测试 | 验证修复结果 | Closed/Reopened |
| Closed | 测试经理 | 确认关闭 | - |
| Reopened | 测试 | 修复不通过重新打开 | Open |
| Rejected | 开发/经理 | 不是Bug/重复/无法复现 | Closed(经确认) |

## 不同团队的工作流

### 小团队简化流程
```
待处理 → 处理中 → 已解决 → 已关闭
```

### 标准流程
```
提交 → 确认 → 分配 → 修复 → 测试 → 关闭
```

### 严格流程（金融/医疗）
```
提交 → 确认 → 分配 → 修复 → 代码审查 → 单元测试 → 测试 → 回归测试 → 发布验证 → 关闭
```""",
    },
    {
        "title": "第2节：高质量缺陷报告编写",
        "sort_order": 2,
        "knowledge_point": "缺陷报告",
        "time_estimate": 25,
        "content": """## 缺陷报告的黄金法则

**好报告 = 让开发人员5分钟内理解问题并开始修复**

### 缺陷报告模板

```
标题：[模块] 简短描述（20字以内）

环境：
- 操作系统：Windows 11
- 浏览器版本：Chrome 120.0
- 测试环境：staging
- 复现时间：2024-01-15 14:30

严重程度：Major
优先级：P1

复现步骤：
1. 打开登录页面
2. 输入账号：testuser@test.com
3. 输入密码：Test@123
4. 点击"登录"按钮

实际结果：
页面刷新后仍停留在登录页，没有任何提示信息。

预期结果：
登录成功后跳转到首页，右上角显示用户名。

复现率：100%（5/5次尝试均复现）

附件：
- 截图：login_error.png
- 控制台日志：console.log
- 网络请求记录：network.har
```

## 写好标题的技巧

| 差标题 ❌ | 好标题 ✅ |
|-----------|----------|
| 登录有问题 | [登录] 正确账号密码登录后页面无跳转 |
| 数据显示不对 | [订单列表] 金额超过1000元的订单金额显示为0 |
| 页面崩了 | [商品详情] 库存为0时点击"加入购物车"导致页面白屏 |

坏标题公式：缺少模块 + 模糊描述

## 写清复现步骤

**原则**：让一个不了解你项目的人也能按照步骤复现问题。

- 步骤编号清晰
- 每个步骤一个动作
- 包含具体的输入数据
- 说明起始页面/状态

## 常见缺陷报告错误

1. **一个报告包含多个问题**：开发只修复了其中一个，另一个被遗漏
2. **缺少关键信息**：没有环境、没有复现步骤
3. **加入主观评价**："这个设计太烂了" → 只描述客观事实
4. **预期结果不明确**："应该正常显示" → 什么算"正常"？
5. **不提供复现率**：开发无法判断是偶现还是必现""",
    },
    {
        "title": "第3节：缺陷严重度与优先级判定",
        "sort_order": 3,
        "knowledge_point": "严重度与优先级",
        "time_estimate": 20,
        "content": """## 严重程度（Severity）vs 优先级（Priority）

> 严重程度是**技术评估**，优先级是**业务决策**。

### 严重程度分级

| 级别 | 描述 | 示例 |
|------|------|------|
| Blocker/Critical | 系统崩溃、数据丢失、核心功能完全不可用 | 支付模块全部崩溃 |
| Major | 主要功能错误，严重影响使用 | 订单金额计算错误 |
| Minor | 次要功能错误，有替代方案 | 分页功能失效 |
| Trivial | 界面问题、错别字 | Logo颜色偏差 |
| Enhancement | 改进建议（严格来说不是缺陷） | 建议增加快捷键 |

### 优先级分级

| 级别 | 描述 | 修复时间 |
|------|------|----------|
| P0-紧急 | 立即修复，阻塞发布 | 小时级 |
| P1-高 | 本迭代内必须修复 | 天级 |
| P2-中 | 下个迭代修复 | 周级 |
| P3-低 | 资源允许时修复 | 月级或下版本 |

### 严重度与优先级的交叉

| 严重度 | 优先级 | 场景 |
|--------|--------|------|
| Trivial | P0 | 首页Logo显示为竞品Logo |
| Critical | P2 | 极少使用的后台报表功能崩溃 |

## 缺陷分类

| 分类 | 说明 | 处理方式 |
|------|------|----------|
| 功能缺陷 | 功能不符合需求 | 必须修复 |
| UI缺陷 | 界面显示问题 | 视影响修复 |
| 性能缺陷 | 响应慢、资源占用高 | 优化或重构 |
| 安全缺陷 | 可被利用的漏洞 | 必须紧急修复 |
| 兼容性缺陷 | 特定环境问题 | 评估用户覆盖率 |
| 文档缺陷 | 帮助文档错误 | 更新文档 |

## 缺陷拒绝的正当理由

| 理由 | 说明 |
|------|------|
| By Design | 这是设计如此，不是缺陷 |
| Duplicate | 已有相同的缺陷报告 |
| Cannot Reproduce | 无法复现（请补充更多信息） |
| Not a Bug | 不是缺陷（如用户操作失误） |
| Won't Fix | 评估后决定不修复（成本>收益） |""",
    },
    {
        "title": "第4节：JIRA与禅道工具实战",
        "sort_order": 4,
        "knowledge_point": "缺陷工具",
        "time_estimate": 25,
        "content": """## JIRA核心操作

### 创建Issue
```
项目：TEST
类型：Bug
标题：[登录] 密码包含特殊字符时登录失败
描述：按照模板填写
优先级：High
组件：登录模块
影响版本：v2.1.0
修复版本：v2.1.1
指派人：developer_name
```

### JQL（JIRA查询语言）

```sql
-- 查询我的待处理缺陷
assignee = currentUser() AND status != Closed ORDER BY priority DESC

-- 查询本周发现的高优缺陷
project = TEST AND type = Bug AND priority = High AND created >= startOfWeek()

-- 查询长时间未解决的缺陷
project = TEST AND status = Open AND created <= -30d

-- 查询特定模块的缺陷
project = TEST AND component = "支付模块" AND status != Closed
```

### JIRA工作流定制

典型自定义状态：
```
Open → In Progress → In Review → Resolved → Testing → Closed
```

## 禅道核心操作

### 提Bug
1. 进入"测试" → "Bug"
2. 点击"提Bug"
3. 填写基本信息：所属产品、模块、Bug标题、重现步骤
4. 选择严重程度和优先级
5. 指派给相关负责人
6. 提交

### 禅道Bug状态流转
```
激活 → 已确认 → 已解决 → 已关闭
```

### 禅道常用操作
- **转Bug**：将用例执行失败转换为Bug
- **关联用例**：将Bug关联到发现它的测试用例
- **关联需求**：将Bug关联到相关需求

## 缺陷管理最佳实践

1. **唯一且可搜索的ID**：不要用汉字做编号
2. **完整的变更历史**：谁、什么时间、做了什么操作
3. **关联关系**：链接到需求、用例、代码提交
4. **通知机制**：状态变更自动通知相关人员
5. **定期回顾**：每迭代分析缺陷趋势和分布""",
    },
    {
        "title": "第5节：缺陷统计与趋势分析",
        "sort_order": 5,
        "knowledge_point": "缺陷分析",
        "time_estimate": 20,
        "content": """## 缺陷度量指标

### 基础指标

| 指标 | 公式 | 说明 |
|------|------|------|
| 缺陷密度 | 缺陷数 / 模块规模(KLOC/功能点) | 衡量模块质量 |
| 缺陷发现率 | 单位时间发现缺陷数 | 测试效率 |
| 缺陷修复率 | 单位时间修复缺陷数 | 开发效率 |
| 缺陷逃逸率 | 生产缺陷 / 总缺陷 | 测试有效性 |
| 缺陷重开率 | Reopened / (Fixed+Reopened) | 修复质量 |
| 平均修复时间 | 从Open到Fixed的平均时间 | 响应速度 |

### 缺陷分布分析

**按模块分布**：
```
模块A: ████████████████ 16个
模块B: ██████ 6个
模块C: ████████ 8个
模块D: ██ 2个
```
模块A缺陷最多 → 可能是高风险模块，需要加大测试力度或进行重构

**按严重程度分布**：
```
Critical: 3%  ■
Major:    22% ██████
Minor:    45% █████████████
Trivial:  30% █████████
```

### 缺陷趋势图

```
缺陷数量
    ↑
30  |    ●
20  |   ╱ ╲
10  |  ╱   ╲___●
  0 |_●_________●__→ 时间
      S1  S2  S3  S4
```

**分析要点**：
- 趋势上升：新功能引入大量缺陷，功能不稳定
- 趋势下降：质量改善，测试趋于饱和
- 突然激增：大规模重构或新功能上线
- 持续高位：技术债务累积，需增加投入

## 缺陷收敛判断

发布标准通常包括：
- 无Critical/Blocker级别缺陷
- Major缺陷 < N个
- 新缺陷发现率趋于零
- 缺陷修复率 > 发现率""",
    },
    {
        "title": "第6节：根因分析与5-Why法",
        "sort_order": 6,
        "knowledge_point": "根因分析",
        "time_estimate": 20,
        "content": """## 根因分析（Root Cause Analysis）

根因分析不是追究责任，而是**找到问题的根本原因，防止再次发生**。

### 5-Why分析法

通过连续追问5个"为什么"来追溯根本原因。

**示例：生产环境数据丢失**

```
问题：生产环境用户数据丢失了

Why 1：为什么会丢数据？
→ 因为数据库执行了一条不带WHERE的DELETE语句

Why 2：为什么不带WHERE的DELETE被执行了？
→ 因为运维人员在生产环境直接执行SQL

Why 3：为什么运维人员可以在生产环境直接执行SQL？
→ 因为生产数据库没有访问控制

Why 4：为什么没有访问控制？
→ 因为当初上线时没有制定数据库操作规范

Why 5：为什么没有制定规范？
→ 因为团队没有生产环境变更管理流程

根本原因：缺少生产环境变更管理流程
```

### 鱼骨图（因果图）

```
        人员              流程              工具
          \               |               /
           \ 培训不足      | 缺少审批      / 缺少SQL审核工具
            \             |             /
             →→→→→→→→ 数据丢失 ←←←←←←←
                     /             \\
                    / 数据库直连    \\ 缺少审计
                   /                \\
              环境                  技术
```

## 缺陷预防策略

| 阶段 | 预防措施 | 说明 |
|------|----------|------|
| 需求 | 需求评审 | 澄清歧义，发现逻辑矛盾 |
| 设计 | 技术方案评审 | 评估技术风险 |
| 编码 | 代码审查 + 静态扫描 | 发现编码缺陷 |
| 测试 | 缺陷分析 → 补充用例 | 根因→补充→固化 |
| 发布 | 灰度发布 + 监控告警 | 快速发现线上问题 |

## 缺陷回顾会议

**频率**：每个迭代结束后
**参与人**：开发、测试、产品
**议程**：
1. 回顾本迭代所有P0/P1缺陷
2. 分析Top 3根因
3. 讨论改进措施
4. 分配Action Item""",
    },
]

# ── 路径8: 测试计划编写与项目管理 (6节) ──
LESSON_CONTENT["测试计划编写与项目管理"] = [
    {
        "title": "第1节：测试计划核心要素",
        "sort_order": 1,
        "knowledge_point": "测试计划",
        "time_estimate": 25,
        "content": """## 测试计划概述

测试计划（Test Plan）描述了测试活动的范围、方法、资源和时间安排的文档。

### IEEE 829标准测试计划要素

| 要素 | 说明 |
|------|------|
| 测试计划标识符 | 文档编号、版本、日期 |
| 引言 | 项目背景、测试目标 |
| 测试项 | 被测对象和范围 |
| 需测试的特性 | 本次测试覆盖的功能点 |
| 不需测试的特性 | 明确排除的内容及原因 |
| 测试方法 | 测试类型、测试策略、测试工具 |
| 测试通过/失败标准 | 可量化的质量标准 |
| 暂停/恢复标准 | 什么条件暂停、恢复测试 |
| 测试交付物 | 测试用例、报告、缺陷清单 |
| 测试任务与进度 | WBS分解、甘特图 |
| 环境需求 | 硬件、软件、网络、数据 |
| 角色与职责 | 各角色的R&R |
| 风险与应急 | 风险识别、缓解措施、应急方案 |

### 测试计划的层级

```
项目级测试计划（Master Test Plan）
  ├── 集成测试计划
  ├── 系统测试计划
  ├── 性能测试计划
  ├── 安全测试计划
  └── UAT测试计划
```

### 编写测试计划的时机

| 阶段 | 计划类型 | 编写时机 |
|------|----------|----------|
| 需求阶段 | 测试策略 | 需求评审后 |
| 设计阶段 | 测试计划 | 概要设计后 |
| 编码阶段 | 详细测试计划 | 详细设计后 |
| 测试阶段 | 测试执行计划 | 测试开始前 |

## 测试计划编写的最佳实践

1. **让干系人参与评审**：开发、产品、运维都需要Review
2. **保持可执行性**：不要写无法执行的"理想计划"
3. **有弹性**：预留缓冲时间处理突发情况
4. **版本控制**：需求变更时同步更新测试计划
5. **量化目标**：占位字符用具体数字，如"缺陷发现率>85%"

## 常见错误

| 错误 | 后果 | 正确做法 |
|------|------|----------|
| 测试范围过大 | 资源不足，质量下降 | 基于风险划定范围 |
| 时间估算过于乐观 | 加班/延期 | 参考历史数据+预留缓冲 |
| 忽略环境准备 | 测试无法开展 | 提前确认环境就绪 |
| 未明确退出标准 | 测试无法结束 | 定义量化通过标准 |""",
    },
    {
        "title": "第2节：测试策略制定",
        "sort_order": 2,
        "knowledge_point": "测试策略",
        "time_estimate": 25,
        "content": """## 测试策略的核心问题

测试策略回答四个关键问题：
1. **测什么**（范围）
2. **怎么测**（方法）
3. **测多少**（深度）
4. **谁来测**（资源）

## 基于风险的测试策略

```
风险 = 失败概率 × 失败影响

高概率 + 高影响 → 深度测试（自动化+人工）
高概率 + 低影响 → 中等测试
低概率 + 高影响 → 防御性测试
低概率 + 低影响 → 轻量测试/不测
```

### 风险优先级矩阵

|  | 高影响 | 中影响 | 低影响 |
|--|--------|--------|--------|
| **高概率** | P0-全面测试 | P1-重点测试 | P2-抽样测试 |
| **中概率** | P1-重点测试 | P2-抽样测试 | P3-基本测试 |
| **低概率** | P2-抽样测试 | P3-基本测试 | P4-不测试 |

## 测试策略的类型

### 1. 分析型策略
基于需求分析和风险分析确定测试重点。
- **适用**：需求明确的传统项目

### 2. 模型型策略
基于系统模型（状态图、流程图）设计测试。
- **适用**：状态复杂、业务流程多的系统

### 3. 方法型策略
系统化地使用测试设计技术（等价类、边界值等）。
- **适用**：所有项目的基础

### 4. 过程型策略
遵循既定的测试过程和标准（如ISTQB、ISO）。
- **适用**：需要认证/合规的行业（金融、医疗）

### 5. 动态策略
根据测试过程中发现的问题动态调整。
- **适用**：敏捷项目、探索性测试

## 不同项目类型的策略选择

| 项目类型 | 推荐策略 | 重点 |
|----------|----------|------|
| Web电商 | 分析型+动态 | 功能、性能、安全、支付 |
| 移动App | 方法型+动态 | 兼容性、弱网、耗电 |
| 金融系统 | 分析型+过程型 | 资金安全、合规、精确性 |
| IoT/嵌入式 | 模型型+方法型 | 实时性、硬件交互 |
| AI/ML系统 | 动态+探索性 | 数据质量、模型准确性 |
| 微服务 | 分析型+方法型 | 接口契约、服务间通信 |

## 测试策略文档模板

```markdown
# 测试策略文档

## 1. 测试范围
## 2. 测试级别与类型
## 3. 测试环境策略
## 4. 测试数据策略
## 5. 自动化策略（哪些自动化，哪些手工）
## 6. 回归测试策略
## 7. 缺陷管理策略
## 8. 测试度量与报告
## 9. 风险与缓解措施
```""",
    },
    {
        "title": "第3节：测试工作量估算",
        "sort_order": 3,
        "knowledge_point": "工作量估算",
        "time_estimate": 20,
        "content": """## 测试工作量估算方法

### 1. 比例法（最常用）
```
测试工作量 = 开发工作量 × 比例系数

开发工作量 = 100人天
比例系数 = 0.3 ~ 0.5
测试工作量 = 30 ~ 50人天
```

不同项目的比例系数：
| 项目类型 | 测试/开发比例 |
|----------|:-----------:|
| 内部管理系统 | 0.2 ~ 0.3 |
| Web应用 | 0.3 ~ 0.5 |
| 金融系统 | 0.5 ~ 1.0 |
| 安全关键系统 | 1.0 ~ 2.0 |
| 航天/医疗 | 2.0 ~ 5.0 |

### 2. WBS（工作分解结构）法

```
测试项目 (100%)
├── 测试计划 (10%)
│   ├── 需求分析 (4%)
│   ├── 策略制定 (3%)
│   └── 计划编写 (3%)
├── 测试设计 (25%)
│   ├── 用例设计 (15%)
│   ├── 用例评审 (5%)
│   └── 数据准备 (5%)
├── 测试执行 (45%)
│   ├── 冒烟测试 (5%)
│   ├── 功能测试 (20%)
│   ├── 回归测试 (10%)
│   └── 缺陷验证 (10%)
├── 测试报告 (10%)
│   ├── 结果分析 (5%)
│   └── 报告编写 (5%)
└── 项目管理 (10%)
    ├── 沟通协调 (5%)
    └── 风险跟踪 (5%)
```

### 3. 功能点法

```
测试工作量 = 功能点数 × 每功能点测试时间

每功能点测试时间：
- 简单功能：2-4小时
- 中等功能：4-8小时
- 复杂功能：8-16小时
```

### 4. 用例点法
```
测试工作量 = 用例数量 × 平均耗时

平均耗时参考：
- 手工测试：10-30分钟/用例
- 自动化用例开发：1-4小时/用例
- 自动化用例执行：1-5分钟/用例
```

## 时间估算的常见陷阱

| 陷阱 | 表现 | 解决方案 |
|------|------|----------|
| 乐观偏差 | 以为一切顺利 | 预留20-30%缓冲 |
| 遗漏隐性工作 | 忽略沟通、开会、写报告 | WBS分解要全面 |
| 忽略环境问题 | 环境搭建耗时 | 提前评估环境复杂度 |
| 不考虑Bug修复时间 | 最理想情况 | 按缺陷密度估算修复时间 |
| 未考虑学习成本 | 新技术/新工具 | 预留培训/学习时间 |

## 工作量估算公式

```
实际所需时间 = (理想估算时间 + 缓冲) × 环境系数 × 团队系数

环境系数：稳定环境=1.0, 新环境=1.3, 不成熟环境=1.5
团队系数：资深团队=0.8, 普通团队=1.0, 新人为主=1.5
```""",
    },
    {
        "title": "第4节：测试风险评估与管理",
        "sort_order": 4,
        "knowledge_point": "风险管理",
        "time_estimate": 25,
        "content": """## 测试风险管理流程

```
风险识别 → 风险分析 → 风险应对 → 风险监控
```

## 常见测试风险清单

### 进度风险
| 风险 | 概率 | 影响 | 缓解措施 |
|------|:----:|:----:|----------|
| 开发延期交付 | 高 | 高 | 设定里程碑，每日跟踪 |
| 需求频繁变更 | 高 | 中 | 冻结窗口，变更流程 |
| 测试人员不足 | 中 | 高 | 交叉培训，外部支援 |
| 测试时间被压缩 | 高 | 高 | 明确底线，风险升级 |

### 质量风险
| 风险 | 概率 | 影响 | 缓解措施 |
|------|:----:|:----:|----------|
| 核心模块质量差 | 中 | 高 | 代码审查，架构评审 |
| 第三方依赖不稳定 | 低 | 高 | 提前集成测试 |
| 遗留缺陷过多 | 中 | 中 | 缺陷收敛跟踪 |
| 性能不达标 | 低 | 高 | 早期性能测试 |

### 技术风险
| 风险 | 概率 | 影响 | 缓解措施 |
|------|:----:|:----:|----------|
| 测试环境不可用 | 中 | 高 | 备用环境，本地环境 |
| 测试工具问题 | 低 | 中 | 提前验证工具兼容性 |
| 自动化脚本不稳定 | 中 | 中 | 维护预算，定期Review |
| 数据安全问题 | 低 | 高 | 脱敏数据，权限管控 |

### 人员风险
| 风险 | 概率 | 影响 | 缓解措施 |
|------|:----:|:----:|----------|
| 关键人员离职 | 低 | 高 | 知识传承，文档化 |
| 团队技能不足 | 中 | 中 | 培训计划，外部咨询 |
| 沟通不畅 | 中 | 中 | 日站会，周回顾 |

## 风险评估矩阵

计算风险值 R = P × I
- P: 发生概率 (1-5)
- I: 影响程度 (1-5)
- R >= 15: 高风险，必须制定应对方案
- R 8-14: 中风险，需要密切关注
- R <= 7: 低风险，定期Review

## 风险应对策略

| 策略 | 说明 | 示例 |
|------|------|------|
| 规避 | 消除风险源 | 换用成熟技术 |
| 转移 | 转移给第三方 | 购买测试服务 |
| 缓解 | 降低概率或影响 | 增加Code Review |
| 接受 | 承认并准备应急 | 预留应急时间 |

## 风险登记册模板

| ID | 风险描述 | P | I | R | 应对策略 | 负责人 | 状态 |
|----|----------|:--:|:--:|:--:|----------|--------|:----:|
| R1 | 登录模块延迟2天 | 4 | 4 | 16 | 缓解:每日跟踪 | 张三 | 监控中 |
| R2 | 性能测试工具授权过期 | 2 | 3 | 6 | 接受:用开源替代 | 李四 | 已关闭 |""",
    },
    {
        "title": "第5节：测试进度跟踪与报告",
        "sort_order": 5,
        "knowledge_point": "进度报告",
        "time_estimate": 20,
        "content": """## 测试进度跟踪指标

### 核心KPI

| 指标 | 计算公式 | 说明 |
|------|----------|------|
| 用例执行率 | 已执行/总数 | 测试进度 |
| 用例通过率 | 通过数/已执行 | 测试质量 |
| 缺陷发现率 | 新增缺陷/周 | 缺陷趋势 |
| 缺陷修复率 | 已修复/总缺陷 | 开发响应速度 |
| 缺陷收敛率 | (本周-上周)/上周 | 负值表示收敛中 |
| 需求覆盖率 | 已覆盖需求/总需求 | 测试完备性 |
| 自动化覆盖率 | 自动化用例/总用例 | 自动化程度 |

### 每日进度跟踪表

```
日期：2024-01-15
模块    计划用例  已执行  通过  失败  阻塞  完成率
登录    50       50     48    2     0     100%
订单    80       65     58    5     2     81%
支付    40       20     18    2     0     50%
商品    60       40     38    1     1     67%
--------
总计    230      175    162   10    3     76%
```

## 测试报告类型

### 日报（Daily Report）
- **内容**：当日执行情况、新增Bug、风险提示
- **频率**：每天
- **受众**：测试团队、开发经理

### 周报（Weekly Report）
```markdown
# 测试周报 - 第X周

## 本周测试概况
- 计划执行：500条 | 实际执行：480条 (96%)
- 通过率：92%
- 新增缺陷：15个 | 已修复：12个 | 遗留：8个

## 风险提示
1. 支付模块仍有3个P0缺陷待修
2. 环境不稳定导致阻塞3小时

## 下周计划
1. 完成订单模块回归测试
2. 启动性能测试第一轮
```

### 里程碑报告（Milestone Report）
- **内容**：阶段测试总结、质量评估、发布建议
- **频率**：每个测试阶段结束
- **受众**：项目经理、产品负责人

### 发布报告（Release Report）
```markdown
# 测试发布报告

## 版本信息
- 版本号：v2.1.0
- 测试周期：2024-01-05 ~ 2024-01-20

## 测试范围与完成度
- 计划用例：1200条 | 执行：1200条 (100%)
- 通过：1150条 (95.8%)
- 需求覆盖率：100%

## 缺陷总结
- 总计：85个 | P0: 0个（已全部修复）
- P1: 2个（已知问题，下版本修复）

## 遗留风险
1. 大并发场景下的偶发超时（发生概率<1%）

## 发布建议
☑ 建议发布（带已知风险说明）
```

## 测试进度可视化

### 燃尽图（Burndown Chart）
```
横轴：时间
纵轴：剩余工作量
理想线：匀速递减
实际线：反映真实进度

理想线高于实际线 → 进度超前
实际线高于理想线 → 进度落后
```

### 缺陷趋势图
```
每日新增缺陷数 → 应呈下降趋势
每日修复缺陷数 → 应呈上升趋势
两者交叉点 → 缺陷收敛点
```""",
    },
    {
        "title": "第6节：测试团队角色与分工",
        "sort_order": 6,
        "knowledge_point": "团队管理",
        "time_estimate": 20,
        "content": """## 测试团队组织架构

### 小团队（< 5人）
```
测试经理/Leader
  ├── 测试工程师 × 2
  │   ├── 功能测试
  │   └── 自动化测试
  └── 测试工程师 × 2
      ├── 专项测试
      └── 测试开发
```

### 中型团队（5-15人）
```
测试总监/高级经理
  ├── 功能测试组
  │   ├── 测试组长
  │   └── 测试工程师 × N
  ├── 自动化测试组
  │   ├── 自动化测试经理
  │   └── SDET × N
  └── 性能测试组
      ├── 性能测试工程师
      └── 性能测试工程师
```

### 大型团队（15+人）
```
质量VP/QA总监
  ├── 测试架构师
  ├── 功能测试团队
  ├── 自动化测试团队
  ├── 专项测试团队（性能/安全/兼容性）
  ├── 测试工具与平台团队
  ├── 测试数据与环境团队
  └── 质量度量与改进团队
```

## 测试角色与职责（RACI矩阵）

| 活动 | 测试经理 | 测试组长 | 测试工程师 | 自动化工程师 | 产品经理 |
|------|:--------:|:--------:|:----------:|:------------:|:--------:|
| 测试策略制定 | A | R | C | C | I |
| 测试计划编写 | A | R | C | C | I |
| 用例设计 | I | A | R | C | C |
| 用例评审 | I | A | R | R | R |
| 功能测试执行 | I | A | R | - | I |
| 自动化开发 | I | A | C | R | - |
| 缺陷分析 | A | R | R | C | I |
| 测试报告 | A | R | C | C | I |
| 发布决策 | C | R | C | C | A |

A=Accountable(负责), R=Responsible(执行), C=Consulted(咨询), I=Informed(知会)

## 各角色的核心能力

### 测试工程师（初级）
- 执行测试用例
- 提交清晰的缺陷报告
- 协助复现问题
- 维护测试数据

### 测试工程师（中级）
- 独立设计测试用例
- 制定模块测试策略
- 编写自动化脚本
- 指导初级工程师

### 高级测试工程师
- 制定整体测试策略
- 设计测试框架
- 性能/安全专项测试
- 技术方案评审

### 测试架构师
- 测试技术选型与规划
- 可测试性设计评审
- 测试平台架构设计
- 质量度量体系建设

### 测试经理
- 团队管理与人才培养
- 资源分配与进度管控
- 跨团队沟通协调
- 质量风险决策

## 团队建设建议

1. **T型人才培养**：一个方向深入 + 多个方向了解
2. **定期轮岗**：功能测试与自动化测试之间轮换
3. **技术分享**：每周技术分享会
4. **Code Review**：自动化代码相互Review
5. **外部学习**：参加技术大会、考取ISTQB认证""",
    },
]

# ── 从外部内容模块导入剩余课程 ──
from seed_lessons_p3 import LESSON_CONTENT_3
from seed_lessons_p4 import LESSON_CONTENT_4
from seed_lessons_p5 import LESSON_CONTENT_5

for d in [LESSON_CONTENT_3, LESSON_CONTENT_4, LESSON_CONTENT_5]:
    for k, v in d.items():
        if k in LESSON_CONTENT:
            LESSON_CONTENT[k].extend(v)
        else:
            LESSON_CONTENT[k] = v

print(f"[INFO] Loaded {sum(len(v) for v in LESSON_CONTENT.values())} lesson sections for {len(LESSON_CONTENT)} paths")


# ============================================================
# 主执行函数
# ============================================================
async def seed_all():
    async with async_session() as session:
        print("=" * 70)
        print("[STEP 1] 清理旧的关联数据...")
        print("=" * 70)

        result = await session.execute(text("SELECT COUNT(*) FROM exercises WHERE learning_path_id IS NOT NULL"))
        ex_count = result.scalar()
        print(f"  Clearing {ex_count} exercise references...")
        await session.execute(text("UPDATE exercises SET learning_path_id = NULL"))
        await session.commit()

        result = await session.execute(text("SELECT COUNT(*) FROM lesson_sections"))
        ls_count = result.scalar()
        print(f"  Deleting {ls_count} old lesson sections...")
        await session.execute(delete(LessonSection))
        await session.commit()

        result = await session.execute(text("SELECT COUNT(*) FROM learning_paths"))
        lp_count = result.scalar()
        print(f"  Deleting {lp_count} old learning paths...")
        await session.execute(delete(LearningPath))
        await session.commit()
        print("  [OK] Cleanup complete!")

        print("\n" + "=" * 70)
        print(f"[STEP 2] 创建 {len(ALL_PATHS)} 个学习路径...")
        print("=" * 70)

        path_objects = {}
        for pdata in ALL_PATHS:
            existing = await session.execute(select(LearningPath).where(LearningPath.title == pdata["title"]))
            if existing.scalar_one_or_none():
                print(f"  [SKIP] '{pdata['title']}' already exists")
                continue

            path = LearningPath(
                title=pdata["title"],
                description=pdata["description"],
                learning_objectives=pdata["learning_objectives"],
                knowledge_outline=pdata["knowledge_outline"],
                supporting_resources=pdata["supporting_resources"],
                prerequisites=pdata["prerequisites"],
                language=pdata["language"],
                difficulty=pdata["difficulty"],
                stage=pdata["stage"],
                estimated_hours=pdata["estimated_hours"],
                exercise_count=0,
                is_public=True,
            )
            session.add(path)
            await session.flush()
            path_objects[pdata["title"]] = path
            print(f"  [OK] Stage {pdata['stage']} | {pdata['difficulty']:>12} | {pdata['title']}")

        await session.commit()
        print(f"\n  Created {len(path_objects)} new learning paths!")

        print("\n" + "=" * 70)
        print("[STEP 3] 插入课程章节...")
        print("=" * 70)

        total_lessons = 0
        stats = {}

        for title, lessons in LESSON_CONTENT.items():
            if title not in path_objects:
                result = await session.execute(select(LearningPath).where(LearningPath.title == title))
                path = result.scalar_one_or_none()
                if path:
                    path_objects[title] = path
                else:
                    print(f"  [WARN] Path not found: '{title}', skipping {len(lessons)} lessons")
                    continue

            path = path_objects[title]
            added = 0
            for lesson_data in lessons:
                lesson = LessonSection(
                    title=lesson_data["title"],
                    content=lesson_data["content"],
                    sort_order=lesson_data["sort_order"],
                    knowledge_point=lesson_data["knowledge_point"],
                    time_estimate=lesson_data["time_estimate"],
                    learning_path_id=path.id,
                )
                session.add(lesson)
                added += 1

            await session.flush()
            total_lessons += added
            stats[title] = added
            print(f"  [OK] '{title}' ← {added} lessons")

        await session.commit()

        print("\n" + "=" * 70)
        print("[RESULT] 迁移完成！")
        print("=" * 70)
        print(f"  学习路径: {len(path_objects)} 个")
        print(f"  课程章节: {total_lessons} 节")
        print()
        for title, count in stats.items():
            bar = "█" * min(count, 20)
            print(f"  {title:<24} {bar} ({count}节)")
        print("=" * 70)

        path_count = len(path_objects)
        if path_count != len(ALL_PATHS):
            missing = set(p["title"] for p in ALL_PATHS) - set(path_objects.keys())
            print(f"\n[NOTE] {path_count}/{len(ALL_PATHS)} paths created.")
            if missing:
                print(f"  Missing: {missing}")


async def verify_all_lessons():
    """验证所有路径都有课程内容"""
    async with async_session() as session:
        result = await session.execute(
            text("""
            SELECT lp.title, lp.stage, lp.difficulty, lp.estimated_hours,
                   (SELECT COUNT(*) FROM lesson_sections ls WHERE ls.learning_path_id = lp.id) as lesson_cnt
            FROM learning_paths lp
            ORDER BY lp.stage, lp.difficulty, lp.title
        """)
        )
        rows = result.fetchall()
        print("\n[VERIFY] 学习路径与课程统计：")
        print("-" * 80)
        empty = 0
        for row in rows:
            flag = " ⚠ EMPTY" if row[4] == 0 else ""
            print(f"  Stage{row[1]} | {row[2]:>12} | {row[3]:>3}h | {row[4]:>3}节 | {row[0]}{flag}")
            if row[4] == 0:
                empty += 1
        print("-" * 80)
        print(f"  总计: {len(rows)} 个路径, {empty} 个缺少课程内容")
        return empty == 0


async def main():
    print("\n" + "█" * 70)
    print("█  TestMaster 学习路径综合迁移脚本 V3")
    print("█  功能: 清理重复 → 重建18个路径 → 补充全部课程")
    print("█" * 70 + "\n")
    await seed_all()
    all_have_lessons = await verify_all_lessons()
    if all_have_lessons:
        print("\n✓ 全部学习路径都有完整的课程内容！")
    else:
        print("\n✗ 部分路径缺少课程内容，请检查！")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
