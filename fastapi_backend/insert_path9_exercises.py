#!/usr/bin/env python3
"""
学习路径9：接口测试基础 - 50道精品题
基于接口测试基础的真实课程内容出题
"""

import sqlite3

db_path = "c:/Users/lenovo/Desktop/TestMasterProject/instance/testmaster.db"

# 学习路径9的50道精品题
exercises_data = [
    # ============ 接口测试概述（10题）============
    {
        "title": "关于接口测试（API Testing），以下说法正确的是？",
        "description": "关于接口测试（API Testing），以下说法正确的是？\n\nA. 接口测试是对系统组件间接口进行的测试\nB. 接口测试只测试用户界面\nC. 接口测试不需要测试工具\nD. 接口测试只适用于Web应用",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "easy",
        "category": "接口测试概述",
    },
    {
        "title": "关于接口测试的优势，以下说法正确的是？（多选）",
        "description": "关于接口测试的优势，以下说法正确的是？（多选）\n\nA. 接口测试可以更早开始，不需要等待UI完成\nB. 接口测试更容易实现自动化\nC. 接口测试可以发现底层逻辑错误\nD. 接口测试可以完全替代UI测试",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "medium",
        "category": "接口测试概述",
    },
    {
        "title": "请判断：接口测试通常在集成测试阶段进行。",
        "description": "请判断：接口测试通常在集成测试阶段进行。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "easy",
        "category": "接口测试概述",
    },
    {
        "title": "关于API的类型，以下说法正确的是？",
        "description": "关于API的类型，以下说法正确的是？\n\nA. 常见的API类型包括：RESTful、SOAP、GraphQL、gRPC\nB. API只有一种类型\nC. API类型不重要，不需要区分\nD. API只用于数据库操作",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "接口测试概述",
    },
    {
        "title": "关于接口测试与UI测试的区别，以下说法正确的是？（多选）",
        "description": "关于接口测试与UI测试的区别，以下说法正确的是？（多选）\n\nA. 接口测试更关注业务逻辑，UI测试更关注用户体验\nB. 接口测试执行速度更快\nC. 接口测试更容易维护\nD. 接口测试和UI测试是完全相同的",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "接口测试概述",
    },
    {
        "title": "请判断：接口测试可以测试HTTP状态码、响应时间、数据格式等。",
        "description": "请判断：接口测试可以测试HTTP状态码、响应时间、数据格式等。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "medium",
        "category": "接口测试概述",
    },
    {
        "title": "关于接口文档，以下说法正确的是？",
        "description": "关于接口文档，以下说法正确的是？\n\nA. 接口文档应该包含：接口地址、请求方法、参数说明、响应示例\nB. 接口文档不重要，可以不需要\nC. 接口文档只由开发人员查看\nD. 接口文档一旦写好就不需要更新",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "接口测试概述",
    },
    {
        "title": "关于接口测试的工具，以下说法正确的是？（多选）",
        "description": "关于接口测试的工具，以下说法正确的是？（多选）\n\nA. 常见的接口测试工具有：Postman、JMeter、SoapUI、curl\nB. 接口测试必须使用商业工具\nC. 接口测试工具可以发送HTTP请求并验证响应\nD. 接口测试工具只用于手工测试，不能自动化",
        "solution": "A,C",
        "exercise_type": "multiple_choice",
        "difficulty": "medium",
        "category": "接口测试概述",
    },
    {
        "title": "请判断：接口测试可以发现前后端数据交互的错误。",
        "description": "请判断：接口测试可以发现前后端数据交互的错误。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "easy",
        "category": "接口测试概述",
    },
    {
        "title": "关于接口测试的粒度，以下说法正确的是？",
        "description": "关于接口测试的粒度，以下说法正确的是？\n\nA. 应该根据业务重要性和风险来确定测试粒度\nB. 接口测试应该覆盖所有细节\nC. 接口测试只需要测试正常场景\nD. 接口测试粒度越细越好",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "hard",
        "category": "接口测试概述",
    },
    # ============ HTTP协议基础（10题）============
    {
        "title": "关于HTTP协议，以下说法正确的是？",
        "description": "关于HTTP协议，以下说法正确的是？\n\nA. HTTP是超文本传输协议，用于客户端和服务器之间的通信\nB. HTTP只支持GET请求\nC. HTTP是无状态的协议\nD. HTTP只用于传输HTML页面",
        "solution": "A,C",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "HTTP协议基础",
    },
    {
        "title": "关于HTTP请求方法，以下说法正确的是？（多选）",
        "description": "关于HTTP请求方法，以下说法正确的是？（多选）\n\nA. GET用于获取资源，POST用于创建资源\nB. PUT用于更新资源，DELETE用于删除资源\nC. PATCH用于部分更新资源\nD. HTTP只有GET和POST两种方法",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "medium",
        "category": "HTTP协议基础",
    },
    {
        "title": "请判断：HTTP状态码200表示请求成功。",
        "description": "请判断：HTTP状态码200表示请求成功。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "easy",
        "category": "HTTP协议基础",
    },
    {
        "title": "关于HTTP状态码的分类，以下说法正确的是？",
        "description": "关于HTTP状态码的分类，以下说法正确的是？\n\nA. 2xx表示成功，4xx表示客户端错误，5xx表示服务器错误\nB. 3xx表示成功\nC. 1xx表示服务器错误\nD. HTTP状态码不重要，不需要关注",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "HTTP协议基础",
    },
    {
        "title": "关于HTTP请求头（Headers），以下说法正确的是？（多选）",
        "description": "关于HTTP请求头（Headers），以下说法正确的是？（多选）\n\nA. Content-Type表示请求体的数据格式\nB. Authorization用于身份认证\nC. User-Agent表示客户端信息\nD. HTTP请求头不重要，可以不需要",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "HTTP协议基础",
    },
    {
        "title": "请判断：HTTP响应头中的Set-Cookie用于设置客户端的Cookie。",
        "description": "请判断：HTTP响应头中的Set-Cookie用于设置客户端的Cookie。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "medium",
        "category": "HTTP协议基础",
    },
    {
        "title": "关于HTTP请求体（Request Body），以下说法正确的是？",
        "description": "关于HTTP请求体（Request Body），以下说法正确的是？\n\nA. POST、PUT、PATCH请求可以有请求体\nB. 只有POST请求可以有请求体\nC. GET请求也可以有请求体\nD. 请求体只能传输文本数据",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "HTTP协议基础",
    },
    {
        "title": "关于HTTP与HTTPS的区别，以下说法正确的是？（多选）",
        "description": "关于HTTP与HTTPS的区别，以下说法正确的是？（多选）\n\nA. HTTPS是HTTP的安全版本，使用SSL/TLS加密\nB. HTTPS默认使用443端口\nC. HTTPS比HTTP更安全\nD. HTTPS和HTTP是完全相同的",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "medium",
        "category": "HTTP协议基础",
    },
    {
        "title": "请判断：HTTP协议默认使用80端口。",
        "description": "请判断：HTTP协议默认使用80端口。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "easy",
        "category": "HTTP协议基础",
    },
    {
        "title": "关于RESTful API的设计原则，以下说法正确的是？",
        "description": "关于RESTful API的设计原则，以下说法正确的是？\n\nA. 使用HTTP方法表示操作，URL表示资源\nB. RESTful API必须使用JSON格式\nC. RESTful API只支持GET和POST\nD. RESTful API不支持状态码",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "hard",
        "category": "HTTP协议基础",
    },
    # ============ 接口测试用例设计（10题）============
    {
        "title": "关于接口测试用例的设计，以下说法正确的是？",
        "description": "关于接口测试用例的设计，以下说法正确的是？\n\nA. 应该覆盖正常场景、异常场景、边界条件\nB. 接口测试用例只需要测试正常场景\nC. 接口测试用例越多越好\nD. 接口测试用例不需要考虑边界条件",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "接口测试用例设计",
    },
    {
        "title": "关于接口测试的参数覆盖，以下说法正确的是？（多选）",
        "description": "关于接口测试的参数覆盖，以下说法正确的是？（多选）\n\nA. 应该覆盖所有必填参数、可选参数\nB. 应该测试参数组合\nC. 应该测试参数缺失的情况\nD. 参数覆盖不重要，只需要测试默认情况",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "接口测试用例设计",
    },
    {
        "title": "请判断：接口测试用例应该包括请求参数、预期响应、实际响应。",
        "description": "请判断：接口测试用例应该包括请求参数、预期响应、实际响应。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "medium",
        "category": "接口测试用例设计",
    },
    {
        "title": "关于接口测试的数据准备，以下说法正确的是？",
        "description": "关于接口测试的数据准备，以下说法正确的是？\n\nA. 应该准备测试数据，确保测试的独立性和可重复性\nB. 测试数据不需要准备，可以使用生产数据\nC. 测试数据只需要准备一次\nD. 测试数据不重要，可以随意使用",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "hard",
        "category": "接口测试用例设计",
    },
    {
        "title": "关于接口测试的依赖处理，以下说法正确的是？（多选）",
        "description": "关于接口测试的依赖处理，以下说法正确的是？（多选）\n\nA. 应该使用Mock或Stub来模拟外部依赖\nB. 应该保证测试用例的独立性\nC. 可以使用测试数据库\nD. 接口测试必须依赖外部环境",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "接口测试用例设计",
    },
    {
        "title": "请判断：接口测试用例应该覆盖所有的业务场景。",
        "description": "请判断：接口测试用例应该覆盖所有的业务场景。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "medium",
        "category": "接口测试用例设计",
    },
    {
        "title": "关于接口测试的错误码覆盖，以下说法正确的是？",
        "description": "关于接口测试的错误码覆盖，以下说法正确的是？\n\nA. 应该覆盖所有定义的错误码\nB. 错误码不需要覆盖，只需要测试成功场景\nC. 错误码覆盖不重要\nD. 错误码只由开发人员定义，测试人员不需要关注",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "hard",
        "category": "接口测试用例设计",
    },
    {
        "title": "关于接口测试的性能考虑，以下说法正确的是？（多选）",
        "description": "关于接口测试的性能考虑，以下说法正确的是？（多选）\n\nA. 应该测试接口的响应时间\nB. 应该测试接口的并发处理能力\nC. 应该测试接口在高负载下的表现\nD. 接口测试不需要考虑性能",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "接口测试用例设计",
    },
    {
        "title": "请判断：接口测试用例应该具有可维护性，便于后续修改和扩展。",
        "description": "请判断：接口测试用例应该具有可维护性，便于后续修改和扩展。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "medium",
        "category": "接口测试用例设计",
    },
    {
        "title": "关于接口测试的断言（Assertion），以下说法正确的是？",
        "description": "关于接口测试的断言（Assertion），以下说法正确的是？\n\nA. 应该验证状态码、响应体、响应时间等\nB. 断言只需要验证状态码\nC. 断言不需要验证响应体\nD. 断言不重要，可以不需要",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "hard",
        "category": "接口测试用例设计",
    },
    # ============ 常用接口测试工具（10题）============
    {
        "title": "关于Postman，以下说法正确的是？",
        "description": "关于Postman，以下说法正确的是？\n\nA. Postman是一款流行的API测试工具，支持发送HTTP请求、编写测试脚本\nB. Postman只能用于手工测试\nC. Postman不支持环境变量\nD. Postman是命令行工具",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "常用接口测试工具",
    },
    {
        "title": "关于Postman的Collection，以下说法正确的是？（多选）",
        "description": "关于Postman的Collection，以下说法正确的是？（多选）\n\nA. Collection用于组织和管理API请求\nB. Collection可以导出为JSON文件\nC. Collection可以运行自动化测试\nD. Collection只能包含一个请求",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "medium",
        "category": "常用接口测试工具",
    },
    {
        "title": "请判断：Postman支持环境变量和全局变量。",
        "description": "请判断：Postman支持环境变量和全局变量。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "medium",
        "category": "常用接口测试工具",
    },
    {
        "title": "关于JMeter，以下说法正确的是？",
        "description": "关于JMeter，以下说法正确的是？\n\nA. JMeter是一款开源的性能测试工具，也常用于接口测试\nB. JMeter只能用于性能测试\nC. JMeter不支持HTTP协议\nD. JMeter是商业工具",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "常用接口测试工具",
    },
    {
        "title": "关于curl命令，以下说法正确的是？（多选）",
        "description": "关于curl命令，以下说法正确的是？（多选）\n\nA. curl是一款命令行工具，可以发送HTTP请求\nB. curl支持多种协议（HTTP、FTP、SMTP等）\nC. curl常用于快速测试API\nD. curl只能用于下载文件",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "medium",
        "category": "常用接口测试工具",
    },
    {
        "title": "请判断：Swagger/OpenAPI可以用于接口文档生成和接口测试。",
        "description": "请判断：Swagger/OpenAPI可以用于接口文档生成和接口测试。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "medium",
        "category": "常用接口测试工具",
    },
    {
        "title": "关于Requests库（Python），以下说法正确的是？",
        "description": "关于Requests库（Python），以下说法正确的是？\n\nA. Requests是一个流行的Python HTTP库，常用于接口自动化测试\nB. Requests只能发送GET请求\nC. Requests不支持HTTPS\nD. Requests是内置库，不需要安装",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "常用接口测试工具",
    },
    {
        "title": "关于接口测试工具的选型，以下说法正确的是？（多选）",
        "description": "关于接口测试工具的选型，以下说法正确的是？（多选）\n\nA. 应该根据项目需求、团队技能、工具特性来选型\nB. 商业工具一定比开源工具好\nC. 应该考虑工具的学习成本\nD. 工具选型不重要，可以使用任何工具",
        "solution": "A,C",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "常用接口测试工具",
    },
    {
        "title": "请判断：接口测试工具应该支持断言、参数化、报告生成等功能。",
        "description": "请判断：接口测试工具应该支持断言、参数化、报告生成等功能。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "hard",
        "category": "常用接口测试工具",
    },
    {
        "title": "关于SoapUI，以下说法正确的是？",
        "description": "关于SoapUI，以下说法正确的是？\n\nA. SoapUI是一款用于SOAP和REST API测试的工具\nB. SoapUI只支持SOAP协议\nC. SoapUI不支持自动化测试\nD. SoapUI是命令行工具",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "hard",
        "category": "常用接口测试工具",
    },
    # ============ 接口自动化测试（10题）============
    {
        "title": "关于接口自动化测试，以下说法正确的是？",
        "description": "关于接口自动化测试，以下说法正确的是？\n\nA. 接口自动化测试可以提高测试效率、减少重复工作\nB. 接口自动化测试可以完全替代手工测试\nC. 接口自动化测试不需要维护\nD. 接口自动化测试只适用于小型项目",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "接口自动化测试",
    },
    {
        "title": "关于接口自动化测试的框架选型，以下说法正确的是？（多选）",
        "description": "关于接口自动化测试的框架选型，以下说法正确的是？（多选）\n\nA. 常见的框架有：Pytest、unittest、TestNG、JUnit\nB. 框架选型应该考虑团队技能和项目需求\nC. 框架应该支持断言、报告、持续集成\nD. 框架选型不重要，可以使用任何框架",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "接口自动化测试",
    },
    {
        "title": "请判断：接口自动化测试应该与CI/CD流水线集成。",
        "description": "请判断：接口自动化测试应该与CI/CD流水线集成。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "hard",
        "category": "接口自动化测试",
    },
    {
        "title": "关于接口自动化测试的报告，以下说法正确的是？",
        "description": "关于接口自动化测试的报告，以下说法正确的是？\n\nA. 应该生成详细的测试报告，包括：测试用例、执行结果、错误信息\nB. 测试报告不重要，可以不需要\nC. 测试报告只由测试人员查看\nD. 测试报告只需要包含通过率",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "接口自动化测试",
    },
    {
        "title": "关于接口自动化测试的维护，以下说法正确的是？（多选）",
        "description": "关于接口自动化测试的维护，以下说法正确的是？（多选）\n\nA. 应该定期维护测试脚本，适应接口变更\nB. 应该使用Page Object或类似模式提高可维护性\nC. 应该删除过时的测试用例\nD. 自动化测试脚本一旦写好就不需要维护",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "接口自动化测试",
    },
    {
        "title": "请判断：接口自动化测试应该覆盖核心业务场景和高风险场景。",
        "description": "请判断：接口自动化测试应该覆盖核心业务场景和高风险场景。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "medium",
        "category": "接口自动化测试",
    },
    {
        "title": "关于接口自动化测试的数据管理，以下说法正确的是？",
        "description": "关于接口自动化测试的数据管理，以下说法正确的是？\n\nA. 应该使用独立的测试数据，避免影响生产数据\nB. 可以直接使用生产数据进行测试\nC. 测试数据不需要管理\nD. 测试数据只需要准备一次",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "hard",
        "category": "接口自动化测试",
    },
    {
        "title": "关于接口自动化测试的执行策略，以下说法正确的是？（多选）",
        "description": "关于接口自动化测试的执行策略，以下说法正确的是？（多选）\n\nA. 应该定期执行（如：每次代码提交后、每天定时执行）\nB. 应该快速反馈测试结果\nC. 应该支持失败重试\nD. 自动化测试只需要在发布前执行",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "接口自动化测试",
    },
    {
        "title": "请判断：接口自动化测试的ROI（投资回报率）通常高于UI自动化测试。",
        "description": "请判断：接口自动化测试的ROI（投资回报率）通常高于UI自动化测试。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "hard",
        "category": "接口自动化测试",
    },
    {
        "title": "关于接口自动化测试的最佳实践，以下说法正确的是？",
        "description": "关于接口自动化测试的最佳实践，以下说法正确的是？\n\nA. 应该遵循：独立性、可重复性、快速反馈、易于维护\nB. 自动化测试越多越好\nC. 自动化测试可以随意编写\nD. 自动化测试不需要最佳实践",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "hard",
        "category": "接口自动化测试",
    },
]


def main():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 删除学习路径9的旧习题
    cursor.execute("DELETE FROM exercises WHERE learning_path_id = 9")
    print("🗑️  已删除学习路径9（接口测试基础）的旧习题")

    # 插入50道精品题
    inserted = 0
    for ex in exercises_data:
        try:
            lang = "python" if ex["exercise_type"] == "code" else "中文"

            cursor.execute(
                """
                INSERT INTO exercises 
                (title, description, solution, exercise_type, difficulty, 
                 learning_path_id, category, is_public, language, 
                 created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, 9, ?, 1, ?, datetime('now'), datetime('now'))
            """,
                (
                    ex["title"],
                    ex["description"],
                    ex["solution"],
                    ex["exercise_type"],
                    ex["difficulty"],
                    ex["category"],
                    lang,
                ),
            )
            inserted += 1
        except Exception as e:
            print(f"⚠️  插入失败: {e}")
            continue

    conn.commit()

    # 更新 learning_paths 的 exercise_count
    cursor.execute("UPDATE learning_paths SET exercise_count = ? WHERE id = 9", (inserted,))
    conn.commit()

    print(f"✅ 成功插入 {inserted} 道精品习题到学习路径9（接口测试基础）")

    # 验证
    cursor.execute("SELECT COUNT(*) FROM exercises WHERE learning_path_id = 9")
    count = cursor.fetchone()[0]
    print(f"📊 验证：学习路径9现在有 {count} 道习题")

    conn.close()


if __name__ == "__main__":
    main()
