"""
JMeter 脚本导出/导入服务

功能：
1. 将接口用例/场景导出为 JMeter .jmx 文件
2. 解析 JMeter .jmx 文件并导入为接口用例
"""
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional
from datetime import datetime
from urllib.parse import urlparse
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
    
    # scheduler + duration: 当 duration>0 时启用持续时长控制
    duration = int(thread_group_config.get("duration", 0))
    if duration > 0:
        _add_element_prop(thread_group, "ThreadGroup.scheduler", "true")
        _add_element_prop(thread_group, "ThreadGroup.duration", str(duration))
        _add_element_prop(thread_group, "ThreadGroup.delay", "0")
    else:
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
        sampler_hash_tree = _add_http_sampler(thread_group_hash_tree, case, i)
        
        # 添加断言到采样器的 hashTree 中
        if thread_group_config.get("add_assertion"):
            _add_response_assertion(sampler_hash_tree, case, i, "status_code", "200")
        if thread_group_config.get("add_response_assertion"):
            _add_response_assertion(sampler_hash_tree, case, i, "contains", "")
        
        # 添加定时器（放在采样器的 hashTree 中，在下一个请求之前生效）
        think_time = thread_group_config.get("think_time", 0)
        if think_time > 0:
            _add_think_time(sampler_hash_tree, think_time)
        elif thread_group_config.get("timer_type") == "constant":
            _add_constant_timer(sampler_hash_tree, 1000)
        elif thread_group_config.get("timer_type") == "uniform":
            _add_uniform_random_timer(sampler_hash_tree, 500, 2000)
    
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
    
    # 解析 URL（使用标准库，正确处理端口、认证、query 等）
    url = case.get("url", "")
    method = case.get("method", "GET")
    
    parsed = urlparse(url)
    protocol = parsed.scheme or "https"
    domain = parsed.hostname or ""
    port = str(parsed.port) if parsed.port else ""
    path = parsed.path or "/"
    if parsed.query:
        path += "?" + parsed.query
    
    _add_element_prop(sampler, "HTTPSampler.domain", domain)
    _add_element_prop(sampler, "HTTPSampler.port", port)
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
    
    return sampler_hash_tree


def _add_think_time(parent, think_time_ms):
    """添加思考时间（固定定时器）"""
    _add_constant_timer(parent, think_time_ms)


def _add_constant_timer(parent, delay_ms):
    """添加固定定时器"""
    timer = ET.SubElement(parent, "ConstantTimer")
    timer.set("guiclass", "ConstantTimerGui")
    timer.set("testclass", "ConstantTimer")
    timer.set("testname", f"Think Time ({delay_ms}ms)")
    timer.set("enabled", "true")
    _add_element_prop(timer, "ConstantTimer.delay", str(delay_ms))
    _add_element_prop(timer, "ConstantTimer.comment", "")
    ET.SubElement(parent, "hashTree")


def _add_uniform_random_timer(parent, min_ms, max_ms):
    """添加均匀随机定时器"""
    timer = ET.SubElement(parent, "UniformRandomTimer")
    timer.set("guiclass", "UniformRandomTimerGui")
    timer.set("testclass", "UniformRandomTimer")
    timer.set("testname", f"Random Timer ({min_ms}-{max_ms}ms)")
    timer.set("enabled", "true")
    _add_element_prop(timer, "UniformRandomTimer.delay", str(min_ms))
    _add_element_prop(timer, "UniformRandomTimer.range", str(max_ms - min_ms))
    ET.SubElement(parent, "hashTree")


def _add_response_assertion(parent, case, index, assert_type, expected):
    """添加响应断言"""
    assertion = ET.SubElement(parent, "ResponseAssertion")
    assertion.set("guiclass", "AssertionGui")
    assertion.set("testclass", "ResponseAssertion")
    assertion.set("testname", f"{case.get('name', f'Req {index}')} - Assertion")
    assertion.set("enabled", "true")
    
    _add_element_prop(assertion, "Assertion.scope", "all")
    _add_element_prop(assertion, "Assertion.test_field", 
        "Assertion.response_code" if assert_type == "status_code" else "Assertion.response_data")
    _add_element_prop(assertion, "Assertion.assume_success", "false")
    _add_element_prop(assertion, "Assertion.test_type", "2" if assert_type == "contains" else "8")
    
    # 断言内容
    collection = ET.SubElement(assertion, "collectionProp")
    collection.set("name", "Assertion.test_strings")
    string_prop = ET.SubElement(collection, "stringProp")
    string_prop.set("name", "0")
    string_prop.text = str(expected)
    
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


# ========== 树形脚本导出 ==========

def export_tree_to_jmx(tree: List[Dict], plan_name: str = "Test Plan", plan_vars: List = None) -> str:
    """
    将树形脚本结构导出为完整 JMX
    
    Args:
        tree: [{type, name, props, children}, ...]
        plan_name: 测试计划名称
        plan_vars: [{name, value}, ...] 用户定义变量
    """
    jmeter_test_plan = ET.Element("jmeterTestPlan")
    jmeter_test_plan.set("version", "1.2")
    jmeter_test_plan.set("properties", "5.0")
    jmeter_test_plan.set("jmeter", "5.6.3")

    root_hash_tree = ET.SubElement(jmeter_test_plan, "hashTree")

    # TestPlan
    test_plan = ET.SubElement(root_hash_tree, "TestPlan")
    test_plan.set("guiclass", "TestPlanGui")
    test_plan.set("testclass", "TestPlan")
    test_plan.set("testname", plan_name)
    test_plan.set("enabled", "true")
    _add_element_prop(test_plan, "TestPlan.comments", "")
    _add_element_prop(test_plan, "TestPlan.functional_mode", "false")
    _add_element_prop(test_plan, "TestPlan.tearDown_on_shutdown", "true")
    _add_element_prop(test_plan, "TestPlan.serialize_threadgroups", "false")
    _add_element_prop(test_plan, "TestPlan.user_define_classpath", "")
    _add_arguments_prop(test_plan, "TestPlan.user_defined_variables", plan_vars or [])

    test_plan_hash_tree = ET.SubElement(root_hash_tree, "hashTree")

    # 遍历树节点
    for node in tree:
        _build_tree_node(test_plan_hash_tree, node)

    # 序列化
    xml_str = ET.tostring(jmeter_test_plan, encoding="UTF-8")
    import xml.dom.minidom as minidom
    dom = minidom.parseString(xml_str)
    return dom.toprettyxml(indent="  ", encoding="UTF-8").decode("UTF-8")


def _build_tree_node(parent_hash_tree, node: Dict):
    """递归构建 JMeter 元素树"""
    ntype = node.get("type", "")
    props = node.get("props", {})
    name = node.get("name", ntype)
    children = node.get("children", [])

    if ntype == "ThreadGroup":
        _build_thread_group(parent_hash_tree, name, props, children)
    elif ntype == "HttpSampler":
        _build_http_sampler(parent_hash_tree, name, props, children)
    elif ntype == "ResponseAssertion":
        _build_assertion(parent_hash_tree, name, props)
    elif ntype == "DurationAssertion":
        _build_duration_assertion(parent_hash_tree, name, props)
    elif ntype == "JsonAssertion":
        _build_json_assertion(parent_hash_tree, name, props)
    elif ntype in ("RegexExtractor", "JsonExtractor"):
        _build_extractor(parent_hash_tree, ntype, name, props)
    elif ntype == "ConstantTimer":
        _build_constant_timer(parent_hash_tree, name, props)
    elif ntype == "UniformRandomTimer":
        _build_uniform_random_timer(parent_hash_tree, name, props)
    elif ntype == "GaussianRandomTimer":
        _build_gaussian_timer(parent_hash_tree, name, props)
    elif ntype == "SyncTimer":
        _build_sync_timer(parent_hash_tree, name, props)
    elif ntype == "CSVDataSet":
        _build_csv_dataset(parent_hash_tree, name, props)
    elif ntype == "BeanShellPreProcessor":
        _build_beanshell(parent_hash_tree, name, props, "pre")
    elif ntype == "BeanShellPostProcessor":
        _build_beanshell(parent_hash_tree, name, props, "post")
    elif ntype == "JDBCConnection":
        _build_jdbc_connection(parent_hash_tree, name, props)
    elif ntype == "JDBCSampler":
        _build_jdbc_sampler(parent_hash_tree, name, props)
    elif ntype == "ViewResultsTree":
        _build_listener(parent_hash_tree, name, "ViewResultsFullVisualizer", "ResultCollector")
    elif ntype == "SummaryReport":
        _build_listener(parent_hash_tree, name, "SummaryReport", "ResultCollector")
    elif ntype == "AggregateGraph":
        _build_listener(parent_hash_tree, name, "StatGraphVisualizer", "ResultCollector")


def _build_thread_group(parent, name, props, children):
    tg = ET.SubElement(parent, "ThreadGroup")
    tg.set("guiclass", "ThreadGroupGui")
    tg.set("testclass", "ThreadGroup")
    tg.set("testname", name or "Thread Group")
    tg.set("enabled", "true")
    _add_element_prop(tg, "ThreadGroup.on_sample_error", "continue")
    _add_element_prop(tg, "ThreadGroup.num_threads", str(props.get("threads", 10)))
    _add_element_prop(tg, "ThreadGroup.ramp_time", str(props.get("rampUp", 5)))
    
    duration = int(props.get("duration", 0))
    if duration > 0:
        _add_element_prop(tg, "ThreadGroup.scheduler", "true")
        _add_element_prop(tg, "ThreadGroup.duration", str(duration))
        _add_element_prop(tg, "ThreadGroup.delay", "0")
    else:
        _add_element_prop(tg, "ThreadGroup.scheduler", "false")
    
    _add_element_prop(tg, "ThreadGroup.same_user_on_next_iteration", "true")
    
    # Loop controller
    lc = ET.SubElement(tg, "elementProp")
    lc.set("name", "ThreadGroup.main_controller")
    lc.set("elementType", "LoopController")
    lc.set("guiclass", "LoopControlPanel")
    lc.set("testclass", "LoopController")
    lc.set("testname", "Loop Controller")
    lc.set("enabled", "true")
    loops = int(props.get("loops", 1))
    _add_element_prop(lc, "LoopController.loops", str(loops))
    _add_element_prop(lc, "LoopController.continue_forever", "false")
    
    children_hash_tree = ET.SubElement(parent, "hashTree")
    
    # HTTP Request Defaults
    defaults = ET.SubElement(children_hash_tree, "ConfigTestElement")
    defaults.set("guiclass", "HttpDefaultsGui")
    defaults.set("testclass", "ConfigTestElement")
    defaults.set("testname", "HTTP Request Defaults")
    defaults.set("enabled", "true")
    _add_element_prop(defaults, "HTTPSampler.domain", "")
    _add_element_prop(defaults, "HTTPSampler.port", "")
    _add_element_prop(defaults, "HTTPSampler.protocol", "")
    _add_element_prop(defaults, "HTTPSampler.contentEncoding", "UTF-8")
    _add_element_prop(defaults, "HTTPSampler.path", "")
    ET.SubElement(children_hash_tree, "hashTree")
    
    # Cookie Manager
    cm = ET.SubElement(children_hash_tree, "CookieManager")
    cm.set("guiclass", "CookiePanel")
    cm.set("testclass", "CookieManager")
    cm.set("testname", "HTTP Cookie Manager")
    cm.set("enabled", "true")
    _add_element_prop(cm, "CookieManager.clearEachIteration", "false")
    ET.SubElement(children_hash_tree, "hashTree")
    
    for child in children:
        _build_tree_node(children_hash_tree, child)


def _build_http_sampler(parent, name, props, children):
    sampler = ET.SubElement(parent, "HTTPSamplerProxy")
    sampler.set("guiclass", "HttpTestSampleGui")
    sampler.set("testclass", "HTTPSamplerProxy")
    sampler.set("testname", name or "HTTP Request")
    sampler.set("enabled", "true")
    
    url = props.get("url", "")
    from urllib.parse import urlparse as uparse
    parsed = uparse(url)
    _add_element_prop(sampler, "HTTPSampler.domain", parsed.hostname or "")
    _add_element_prop(sampler, "HTTPSampler.port", str(parsed.port) if parsed.port else "")
    _add_element_prop(sampler, "HTTPSampler.protocol", parsed.scheme or "https")
    path_q = (parsed.path or "/") + ("?" + parsed.query if parsed.query else "")
    _add_element_prop(sampler, "HTTPSampler.path", path_q)
    _add_element_prop(sampler, "HTTPSampler.method", props.get("method", "GET"))
    _add_element_prop(sampler, "HTTPSampler.contentEncoding", "UTF-8")
    _add_element_prop(sampler, "HTTPSampler.follow_redirects", "true")
    _add_element_prop(sampler, "HTTPSampler.auto_redirects", "false")
    _add_element_prop(sampler, "HTTPSampler.use_keepalive", "true")
    _add_element_prop(sampler, "HTTPSampler.DO_MULTIPART_POST", "false")
    
    body = props.get("body", "")
    if body and props.get("method", "GET") != "GET":
        _add_element_prop(sampler, "HTTPSampler.postBodyRaw", str(body))
    
    sh = ET.SubElement(parent, "hashTree")
    
    # Headers
    headers = props.get("headers", [])
    if headers:
        hm = ET.SubElement(sh, "HeaderManager")
        hm.set("guiclass", "HeaderPanel")
        hm.set("testclass", "HeaderManager")
        hm.set("testname", f"{name} - Headers")
        hm.set("enabled", "true")
        cp = ET.SubElement(hm, "collectionProp")
        cp.set("name", "HeaderManager.headers")
        for h in headers:
            if not h.get("key"): continue
            he = ET.SubElement(cp, "elementProp")
            he.set("name", "")
            he.set("elementType", "Header")
            _add_element_prop(he, "Header.name", h["key"])
            _add_element_prop(he, "Header.value", str(h.get("value", "")))
        ET.SubElement(sh, "hashTree")
    
    for child in children:
        _build_tree_node(sh, child)


def _build_assertion(parent, name, props):
    at = props.get("assertType", "status_code")
    if at == "duration":
        _build_duration_assertion(parent, name, props)
        return
    if at == "jsonpath":
        _build_json_assertion(parent, name, props)
        return

    a = ET.SubElement(parent, "ResponseAssertion")
    a.set("guiclass", "AssertionGui")
    a.set("testclass", "ResponseAssertion")
    a.set("testname", name or "Assertion")
    a.set("enabled", "true")
    _add_element_prop(a, "Assertion.scope", "all")
    _add_element_prop(a, "Assertion.test_field", "Assertion.response_code" if at == "status_code" else "Assertion.response_data")
    _add_element_prop(a, "Assertion.assume_success", "false")
    _add_element_prop(a, "Assertion.test_type", "2" if at == "contains" else "8" if at == "matches" else "8")
    cp = ET.SubElement(a, "collectionProp")
    cp.set("name", "Assertion.test_strings")
    sp = ET.SubElement(cp, "stringProp")
    sp.set("name", "0")
    sp.text = str(props.get("expected", "200"))
    ET.SubElement(parent, "hashTree")


def _build_duration_assertion(parent, name, props):
    a = ET.SubElement(parent, "DurationAssertion")
    a.set("guiclass", "DurationAssertionGui")
    a.set("testclass", "DurationAssertion")
    a.set("testname", name or "Duration Assertion")
    a.set("enabled", "true")
    _add_element_prop(a, "DurationAssertion.duration", str(props.get("maxDuration", 1000)))
    ET.SubElement(parent, "hashTree")


def _build_json_assertion(parent, name, props):
    a = ET.SubElement(parent, "JSONPathAssertion")
    a.set("guiclass", "JSONPathAssertionGui")
    a.set("testclass", "JSONPathAssertion")
    a.set("testname", name or "JSON Assertion")
    a.set("enabled", "true")
    _add_element_prop(a, "JSON_PATH", props.get("jsonPath", "$"))
    _add_element_prop(a, "EXPECTED_VALUE", str(props.get("expected", "")))
    _add_element_prop(a, "JSONVALIDATION", "true")
    _add_element_prop(a, "EXPECT_NULL", "false")
    _add_element_prop(a, "INVERT", "false")
    ET.SubElement(parent, "hashTree")


def _build_extractor(parent, ntype, name, props):
    if ntype == "JsonExtractor":
        e = ET.SubElement(parent, "JSONPostProcessor")
        e.set("guiclass", "JSONPostProcessorGui")
        e.set("testclass", "JSONPostProcessor")
        _add_element_prop(e, "JSONPostProcessor.referenceNames", props.get("varName", ""))
        _add_element_prop(e, "JSONPostProcessor.jsonPathExprs", props.get("jsonPath", "$"))
        _add_element_prop(e, "JSONPostProcessor.defaultValues", props.get("defaultValue", "NOT_FOUND"))
    else:
        e = ET.SubElement(parent, "RegexExtractor")
        e.set("guiclass", "RegexExtractorGui")
        e.set("testclass", "RegexExtractor")
        _add_element_prop(e, "RegexExtractor.useHeaders", "false")
        _add_element_prop(e, "RegexExtractor.refname", props.get("varName", ""))
        _add_element_prop(e, "RegexExtractor.regex", props.get("regex", ""))
        _add_element_prop(e, "RegexExtractor.match_number", "1")
        _add_element_prop(e, "RegexExtractor.default", props.get("defaultValue", "NOT_FOUND"))
    e.set("testname", name or "Extractor")
    e.set("enabled", "true")
    ET.SubElement(parent, "hashTree")


def _build_constant_timer(parent, name, props):
    t = ET.SubElement(parent, "ConstantTimer")
    t.set("guiclass", "ConstantTimerGui")
    t.set("testclass", "ConstantTimer")
    t.set("testname", name or "Timer")
    t.set("enabled", "true")
    _add_element_prop(t, "ConstantTimer.delay", str(props.get("delay", 1000)))
    ET.SubElement(parent, "hashTree")


def _build_uniform_random_timer(parent, name, props):
    t = ET.SubElement(parent, "UniformRandomTimer")
    t.set("guiclass", "UniformRandomTimerGui")
    t.set("testclass", "UniformRandomTimer")
    t.set("testname", name or "Random Timer")
    t.set("enabled", "true")
    mn = int(props.get("minDelay", 500))
    mx = int(props.get("maxDelay", 2000))
    _add_element_prop(t, "UniformRandomTimer.delay", str(mn))
    _add_element_prop(t, "UniformRandomTimer.range", str(mx - mn))
    ET.SubElement(parent, "hashTree")


def _build_gaussian_timer(parent, name, props):
    t = ET.SubElement(parent, "GaussianRandomTimer")
    t.set("guiclass", "GaussianRandomTimerGui")
    t.set("testclass", "GaussianRandomTimer")
    t.set("testname", name or "Gaussian Timer")
    t.set("enabled", "true")
    _add_element_prop(t, "GaussianRandomTimer.delay", str(props.get("offset", 300)))
    _add_element_prop(t, "GaussianRandomTimer.range", str(props.get("deviation", 100)))
    ET.SubElement(parent, "hashTree")


def _build_sync_timer(parent, name, props):
    t = ET.SubElement(parent, "SyncTimer")
    t.set("guiclass", "SyncTimerGui")
    t.set("testclass", "SyncTimer")
    t.set("testname", name or "Sync Timer")
    t.set("enabled", "true")
    _add_element_prop(t, "SyncTimer.groupSize", str(props.get("groupSize", 100)))
    _add_element_prop(t, "SyncTimer.timeoutInMs", "0")
    ET.SubElement(parent, "hashTree")


def _build_csv_dataset(parent, name, props):
    c = ET.SubElement(parent, "CSVDataSet")
    c.set("guiclass", "TestBeanGUI")
    c.set("testclass", "CSVDataSet")
    c.set("testname", name or "CSV Data")
    c.set("enabled", "true")
    _add_element_prop(c, "filename", props.get("filename", "data.csv"))
    _add_element_prop(c, "variableNames", props.get("variableNames", ""))
    _add_element_prop(c, "delimiter", props.get("delimiter", ","))
    _add_element_prop(c, "recycle", "true" if props.get("recycle", True) else "false")
    _add_element_prop(c, "stopThread", "false")
    _add_element_prop(c, "ignoreFirstLine", "true")
    ET.SubElement(parent, "hashTree")


def _build_beanshell(parent, name, props, phase):
    tag = "BeanShellPreProcessor" if phase == "pre" else "BeanShellPostProcessor"
    gui = "TestBeanGUI"
    b = ET.SubElement(parent, tag)
    b.set("guiclass", gui)
    b.set("testclass", tag)
    b.set("testname", name or f"BeanShell {phase}")
    b.set("enabled", "true")
    _add_element_prop(b, "script", props.get("script", ""))
    ET.SubElement(parent, "hashTree")


def _build_jdbc_connection(parent, name, props):
    c = ET.SubElement(parent, "JDBCDataSource")
    c.set("guiclass", "TestBeanGUI")
    c.set("testclass", "JDBCDataSource")
    c.set("testname", name or "JDBC Connection")
    c.set("enabled", "true")
    _add_element_prop(c, "dataSource", name or "JDBC")
    _add_element_prop(c, "dbUrl", props.get("dbUrl", ""))
    _add_element_prop(c, "driver", props.get("driver", "com.mysql.cj.jdbc.Driver"))
    _add_element_prop(c, "username", props.get("dbUser", ""))
    _add_element_prop(c, "password", props.get("dbPass", ""))
    ET.SubElement(parent, "hashTree")


def _build_jdbc_sampler(parent, name, props):
    j = ET.SubElement(parent, "JDBCSampler")
    j.set("guiclass", "TestBeanGUI")
    j.set("testclass", "JDBCSampler")
    j.set("testname", name or "JDBC Request")
    j.set("enabled", "true")
    _add_element_prop(j, "dataSource", "")
    _add_element_prop(j, "query", props.get("sql", ""))
    ET.SubElement(parent, "hashTree")


def _build_listener(parent, name, guiclass, testclass):
    l = ET.SubElement(parent, "ResultCollector")
    l.set("guiclass", guiclass)
    l.set("testclass", testclass)
    l.set("testname", name or "Listener")
    l.set("enabled", "true")
    _add_element_prop(l, "ResultCollector.error_logging", "false")
    op = ET.SubElement(l, "objProp")
    v = ET.SubElement(op, "value")
    v.set("class", "SampleSaveConfiguration")
    _add_save_config(v)
    ET.SubElement(parent, "hashTree")
