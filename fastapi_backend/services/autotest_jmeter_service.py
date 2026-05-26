"""
JMeter 脚本导出/导入服务

功能：
1. 将接口用例/场景导出为 JMeter .jmx 文件
2. 解析 JMeter .jmx 文件并导入为接口用例
"""
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional
from datetime import datetime
import io


def export_cases_to_jmx(
    cases: List[Dict[str, Any]],
    test_plan_name: str = "TestMaster Performance Test",
    thread_group_config: Optional[Dict[str, Any]] = None,
) -> str:
    """
    将接口用例导出为 JMeter .jmx 文件内容（XML 格式）
    
    Args:
        cases: 接口用例列表
        test_plan_name: 测试计划名称
        thread_group_config: 线程组配置
            - num_threads: 线程数
            - ramp_time: ramp-up 时间（秒）
            - loop_count: 循环次数
            - duration: 持续时间（秒）
    
    Returns:
        JMeter .jmx 文件内容（XML 字符串）
    """
    if thread_group_config is None:
        thread_group_config = {
            "num_threads": 1,
            "ramp_time": 1,
            "loop_count": 1,
            "duration": 60,
        }
    
    # 创建根元素
    jmeter_test_plan = ET.Element("jmeterTestPlan")
    jmeter_test_plan.set("version", "1.2")
    jmeter_test_plan.set("properties", "5.0")
    jmeter_test_plan.set("jmeter", "5.6.3")
    
    # 创建 HashTree 根节点
    root_hash_tree = ET.SubElement(jmeter_test_plan, "hashTree")
    
    # 添加 TestPlan
    test_plan = ET.SubElement(root_hash_tree, "TestPlan")
    test_plan.set("guiclass", "TestPlanGui")
    test_plan.set("testclass", "TestPlan")
    test_plan.set("testname", test_plan_name)
    test_plan.set("enabled", "true")
    
    # TestPlan 属性
    _add_element_prop(test_plan, "TestPlan.comments", "")
    _add_element_prop(test_plan, "TestPlan.functional_mode", "false")
    _add_element_prop(test_plan, "TestPlan.tearDown_on_shutdown", "true")
    _add_element_prop(test_plan, "TestPlan.serialize_threadgroups", "false")
    _add_element_prop(test_plan, "TestPlan.user_define_classpath", "")
    
    # 添加用户定义的变量
    _add_arguments_prop(test_plan, "TestPlan.user_defined_variables", [])
    
    # TestPlan HashTree
    test_plan_hash_tree = ET.SubElement(root_hash_tree, "hashTree")
    
    # 添加 ThreadGroup
    thread_group = ET.SubElement(test_plan_hash_tree, "ThreadGroup")
    thread_group.set("guiclass", "ThreadGroupGui")
    thread_group.set("testclass", "ThreadGroup")
    thread_group.set("testname", "Thread Group")
    thread_group.set("enabled", "true")
    
    _add_element_prop(thread_group, "ThreadGroup.on_sample_error", "continue")
    _add_element_prop(thread_group, "ThreadGroup.num_threads", str(thread_group_config.get("num_threads", 1)))
    _add_element_prop(thread_group, "ThreadGroup.ramp_time", str(thread_group_config.get("ramp_time", 1)))
    _add_element_prop(thread_group, "ThreadGroup.scheduler", "false")
    _add_element_prop(thread_group, "ThreadGroup.same_user_on_next_iteration", "true")
    
    # 循环控制
    loop_controller = ET.SubElement(thread_group, "elementProp")
    loop_controller.set("name", "ThreadGroup.main_controller")
    loop_controller.set("elementType", "LoopController")
    loop_controller.set("guiclass", "LoopControlPanel")
    loop_controller.set("testclass", "LoopController")
    loop_controller.set("testname", "Loop Controller")
    loop_controller.set("enabled", "true")
    
    _add_element_prop(loop_controller, "LoopController.loops", str(thread_group_config.get("loop_count", 1)))
    _add_element_prop(loop_controller, "LoopController.continue_forever", "false")
    
    # ThreadGroup HashTree
    thread_group_hash_tree = ET.SubElement(test_plan_hash_tree, "hashTree")
    
    # 添加 HTTP Request Defaults
    defaults = ET.SubElement(thread_group_hash_tree, "ConfigTestElement")
    defaults.set("guiclass", "HttpDefaultsGui")
    defaults.set("testclass", "ConfigTestElement")
    defaults.set("testname", "HTTP Request Defaults")
    defaults.set("enabled", "true")
    
    _add_element_prop(defaults, "HTTPSampler.domain", "")
    _add_element_prop(defaults, "HTTPSampler.port", "")
    _add_element_prop(defaults, "HTTPSampler.protocol", "")
    _add_element_prop(defaults, "HTTPSampler.contentEncoding", "UTF-8")
    _add_element_prop(defaults, "HTTPSampler.path", "")
    _add_element_prop(defaults, "HTTPSampler.concurrentPool", "4")
    
    ET.SubElement(thread_group_hash_tree, "hashTree")
    
    # 添加 HTTP Cookie Manager
    cookie_manager = ET.SubElement(thread_group_hash_tree, "CookieManager")
    cookie_manager.set("guiclass", "CookiePanel")
    cookie_manager.set("testclass", "CookieManager")
    cookie_manager.set("testname", "HTTP Cookie Manager")
    cookie_manager.set("enabled", "true")
    
    _add_element_prop(cookie_manager, "CookieManager.clearEachIteration", "false")
    _add_element_prop(cookie_manager, "CookieManager.controlledByThreadGroup", "false")
    
    ET.SubElement(thread_group_hash_tree, "hashTree")
    
    # 添加用例
    for i, case in enumerate(cases, 1):
        _add_http_sampler(thread_group_hash_tree, case, i)
        
        # 添加思考时间（如果有）
        if case.get("think_time"):
            _add_think_time(thread_group_hash_tree, case.get("think_time"))
    
    # 添加 View Results Tree（查看结果树）
    result_tree = ET.SubElement(thread_group_hash_tree, "ResultCollector")
    result_tree.set("guiclass", "ViewResultsFullVisualizer")
    result_tree.set("testclass", "ResultCollector")
    result_tree.set("testname", "View Results Tree")
    result_tree.set("enabled", "true")
    
    _add_element_prop(result_tree, "ResultCollector.error_logging", "false")
    obj_prop = ET.SubElement(result_tree, "objProp")
    value = ET.SubElement(obj_prop, "value")
    value.set("class", "SampleSaveConfiguration")
    _add_save_config(value)
    
    ET.SubElement(thread_group_hash_tree, "hashTree")
    
    # 添加 Summary Report（聚合报告）
    summary = ET.SubElement(thread_group_hash_tree, "ResultCollector")
    summary.set("guiclass", "SummaryReport")
    summary.set("testclass", "ResultCollector")
    summary.set("testname", "Summary Report")
    summary.set("enabled", "true")
    
    _add_element_prop(summary, "ResultCollector.error_logging", "false")
    obj_prop = ET.SubElement(summary, "objProp")
    value = ET.SubElement(obj_prop, "value")
    value.set("class", "SampleSaveConfiguration")
    _add_save_config(value)
    
    ET.SubElement(thread_group_hash_tree, "hashTree")
    
    # 生成 XML 字符串
    xml_str = ET.tostring(jmeter_test_plan, encoding="UTF-8")
    
    # 格式化 XML
    import xml.dom.minidom as minidom
    dom = minidom.parseString(xml_str)
    formatted_xml = dom.toprettyxml(indent="  ", encoding="UTF-8").decode("UTF-8")
    
    return formatted_xml


def import_jmx_to_cases(xml_content: str) -> List[Dict[str, Any]]:
    """
    解析 JMeter .jmx 文件，提取接口用例
    
    Args:
        xml_content: JMeter .jmx 文件内容（XML 字符串）
    
    Returns:
        接口用例列表
    """
    try:
        root = ET.fromstring(xml_content)
    except ET.ParseError as e:
        raise ValueError(f"JMeter XML 解析失败: {e}")
    
    cases = []
    
    for sampler, sampler_hash_tree in _iter_http_samplers(root):
        case = _parse_http_sampler(sampler, sampler_hash_tree)
        if case:
            cases.append(case)
    
    return cases


# ========== 辅助函数 ==========

def _add_element_prop(parent, name, value):
    """添加元素属性"""
    prop = ET.SubElement(parent, "stringProp")
    prop.set("name", name)
    prop.text = str(value)


def _add_arguments_prop(parent, name, arguments):
    """添加参数属性（用于用户定义的变量等）"""
    prop = ET.SubElement(parent, "elementProp")
    prop.set("name", name)
    prop.set("elementType", "Arguments")
    prop.set("guiclass", "ArgumentsPanel")
    prop.set("testclass", "Arguments")
    prop.set("testname", "User Defined Variables")
    prop.set("enabled", "true")
    
    collection_prop = ET.SubElement(prop, "collectionProp")
    collection_prop.set("name", "Arguments.arguments")
    
    for arg in arguments:
        arg_elem = ET.SubElement(collection_prop, "elementProp")
        arg_elem.set("name", arg.get("name", ""))
        arg_elem.set("elementType", "Argument")
        arg_elem.set("guiclass", "HTTPArgumentsPanel")
        arg_elem.set("testclass", "Argument")
        arg_elem.set("testname", arg.get("name", ""))
        arg_elem.set("enabled", "true")
        
        _add_element_prop(arg_elem, "Argument.name", arg.get("name", ""))
        _add_element_prop(arg_elem, "Argument.value", arg.get("value", ""))
        _add_element_prop(arg_elem, "Argument.metadata", "=")
    
    ET.SubElement(prop, "hashTree")


def _add_save_config(parent):
    """添加保存配置（用于结果收集器）"""
    configs = {
        "time": "true",
        "latency": "true",
        "timestamp": "true",
        "success": "true",
        "label": "true",
        "code": "true",
        "message": "true",
        "threadName": "true",
        "dataType": "true",
        "encoding": "false",
        "assertions": "true",
        "subresults": "true",
        "responseData": "false",
        "samplerData": "false",
        "xml": "false",
        "fieldNames": "true",
        "responseHeaders": "false",
        "requestHeaders": "false",
        "responseDataOnError": "false",
        "saveAssertionResultsFailureMessage": "false",
        "assertionsResults": "true",
        "bytes": "true",
        "sentBytes": "true",
        "url": "true",
        "threadCounts": "true",
        "idleTime": "true",
        "connectTime": "true",
    }
    
    for name, value in configs.items():
        prop = ET.SubElement(parent, "value")
        prop.set("class", "bool")
        prop.set("name", f"save{name[:1].upper()}{name[1:]}")
        prop.text = value


def _add_http_sampler(parent, case, index):
    """添加 HTTP 请求采样器"""
    sampler = ET.SubElement(parent, "HTTPSamplerProxy")
    sampler.set("guiclass", "HttpTestSampleGui")
    sampler.set("testclass", "HTTPSamplerProxy")
    sampler.set("testname", case.get("name", f"Request {index}"))
    sampler.set("enabled", "true")
    
    # 解析 URL
    url = case.get("url", "")
    method = case.get("method", "GET")
    
    # 简单解析 URL（实际应该使用 urllib.parse）
    if "://" in url:
        protocol, rest = url.split("://", 1)
        if "/" in rest:
            domain, path = rest.split("/", 1)
            path = "/" + path
        else:
            domain = rest
            path = "/"
    else:
        protocol = "https"
        if "/" in url:
            domain, path = url.split("/", 1)
            path = "/" + path
        else:
            domain = url
            path = "/"
    
    _add_element_prop(sampler, "HTTPSampler.domain", domain)
    _add_element_prop(sampler, "HTTPSampler.port", "")
    _add_element_prop(sampler, "HTTPSampler.protocol", protocol)
    _add_element_prop(sampler, "HTTPSampler.contentEncoding", "UTF-8")
    _add_element_prop(sampler, "HTTPSampler.path", path)
    _add_element_prop(sampler, "HTTPSampler.method", method)
    _add_element_prop(sampler, "HTTPSampler.follow_redirects", "true")
    _add_element_prop(sampler, "HTTPSampler.auto_redirects", "false")
    _add_element_prop(sampler, "HTTPSampler.use_keepalive", "true")
    _add_element_prop(sampler, "HTTPSampler.DO_MULTIPART_POST", "false")
    _add_element_prop(sampler, "HTTPSampler.monitor", "false")
    _add_element_prop(sampler, "HTTPSampler.embedded_url_re", "")
    
    # 添加请求体（如果有）
    payload = case.get("payload")
    if payload and method in ["POST", "PUT", "PATCH"]:
        if isinstance(payload, dict):
            import json as json_module
            payload_str = json_module.dumps(payload, ensure_ascii=False)
        else:
            payload_str = str(payload)
        
        _add_element_prop(sampler, "HTTPSampler.postBodyRaw", payload_str)
    
    sampler_hash_tree = ET.SubElement(parent, "hashTree")

    # 添加请求头
    headers = case.get("headers", {})
    if headers and isinstance(headers, dict):
        default_name = f"Request {index}"
        header_manager = ET.SubElement(sampler_hash_tree, "HeaderManager")
        header_manager.set("guiclass", "HeaderPanel")
        header_manager.set("testclass", "HeaderManager")
        header_manager.set("testname", f"{case.get('name', default_name)} - HTTP Header Manager")
        header_manager.set("enabled", "true")
        
        collection_prop = ET.SubElement(header_manager, "collectionProp")
        collection_prop.set("name", "HeaderManager.headers")
        
        for key, value in headers.items():
            header_elem = ET.SubElement(collection_prop, "elementProp")
            header_elem.set("name", "")
            header_elem.set("elementType", "Header")
            header_elem.set("guiclass", "HTTPArgumentsPanel")
            header_elem.set("testclass", "Header")
            header_elem.set("testname", "")
            header_elem.set("enabled", "true")
            
            _add_element_prop(header_elem, "Header.name", key)
            _add_element_prop(header_elem, "Header.value", str(value))
        
        ET.SubElement(sampler_hash_tree, "hashTree")


def _add_think_time(parent, think_time_ms):
    """添加思考时间（定时器）"""
    timer = ET.SubElement(parent, "ConstantTimer")
    timer.set("guiclass", "ConstantTimerGui")
    timer.set("testclass", "ConstantTimer")
    timer.set("testname", "Think Time")
    timer.set("enabled", "true")
    
    _add_element_prop(timer, "ConstantTimer.delay", str(think_time_ms))
    _add_element_prop(timer, "ConstantTimer.comment", "")
    
    ET.SubElement(parent, "hashTree")


def _iter_http_samplers(parent):
    children = list(parent)
    for index, child in enumerate(children):
        if child.tag in ("HTTPSamplerProxy", "HTTPSampler"):
            sampler_hash_tree = children[index + 1] if index + 1 < len(children) and children[index + 1].tag == "hashTree" else None
            yield child, sampler_hash_tree
        yield from _iter_http_samplers(child)


def _parse_http_sampler(sampler, sampler_hash_tree=None):
    """解析 HTTP 采样器，提取接口信息"""
    try:
        case = {}
        
        # 获取名称
        case["name"] = sampler.get("testname", "Untitled")
        
        # 获取方法
        method_elem = sampler.find(".//stringProp[@name='HTTPSampler.method']")
        case["method"] = method_elem.text if method_elem is not None else "GET"
        
        # 获取 URL 组件
        domain_elem = sampler.find(".//stringProp[@name='HTTPSampler.domain']")
        port_elem = sampler.find(".//stringProp[@name='HTTPSampler.port']")
        protocol_elem = sampler.find(".//stringProp[@name='HTTPSampler.protocol']")
        path_elem = sampler.find(".//stringProp[@name='HTTPSampler.path']")
        
        domain = domain_elem.text if domain_elem is not None and domain_elem.text else ""
        port = port_elem.text if port_elem is not None and port_elem.text else ""
        protocol = protocol_elem.text if protocol_elem is not None and protocol_elem.text else "https"
        path = path_elem.text if path_elem is not None and path_elem.text else "/"
        
        # 构造 URL
        port_str = f":{port}" if port else ""
        case["url"] = f"{protocol}://{domain}{port_str}{path}"
        
        # 获取请求头
        headers = {}
        if sampler_hash_tree is not None:
            for header_manager in sampler_hash_tree.findall("./HeaderManager"):
                for header_elem in header_manager.findall(".//elementProp[@elementType='Header']"):
                    name_elem = header_elem.find(".//stringProp[@name='Header.name']")
                    value_elem = header_elem.find(".//stringProp[@name='Header.value']")
                    if name_elem is not None and value_elem is not None:
                        headers[name_elem.text] = value_elem.text
        
        case["headers"] = headers if headers else None
        
        # 获取请求体
        post_body_elem = sampler.find(".//stringProp[@name='HTTPSampler.postBodyRaw']")
        if post_body_elem is not None and post_body_elem.text:
            try:
                import json as json_module
                case["payload"] = json_module.loads(post_body_elem.text)
            except:
                case["payload"] = post_body_elem.text
        else:
            case["payload"] = None
        
        case["body_type"] = "json" if headers.get("Content-Type", "").startswith("application/json") else "none"
        case["assert_rules"] = []
        case["extractors"] = []
        
        return case
    
    except Exception as e:
        print(f"解析采样器失败: {e}")
        return None
