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
import time


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
    
    return prop
def _add_save_config(parent):
    """添加保存配置（用于结果收集器）- JMeter 5.x 兼容格式"""
    configs = {
        "time": "true", "latency": "true", "timestamp": "true",
        "success": "true", "label": "true", "code": "true",
        "message": "true", "threadName": "true", "dataType": "true",
        "encoding": "false", "assertions": "true", "subresults": "true",
        "responseData": "false", "samplerData": "false", "xml": "false",
        "fieldNames": "true", "responseHeaders": "false", "requestHeaders": "false",
        "responseDataOnError": "false", "saveAssertionResultsFailureMessage": "false",
        "assertionsResults": "true", "bytes": "true", "sentBytes": "true",
        "url": "true", "threadCounts": "true", "idleTime": "true",
        "connectTime": "true",
    }
    for name, value in configs.items():
        el = ET.SubElement(parent, name)
        el.text = value


_JMX_TYPE_MAP = {
    'TestPlan': 'TestPlan',
    'ThreadGroup': 'ThreadGroup',
    'HTTPSamplerProxy': 'HttpSampler', 'HTTPSampler': 'HttpSampler',
    'ResponseAssertion': 'ResponseAssertion',
    'DurationAssertion': 'DurationAssertion',
    'SizeAssertion': 'SizeAssertion',
    'JSONPathAssertion': 'JSONPathAssertion',
    'XPath2Assertion': 'XPath2Assertion',
    'XMLAssertion': 'XMLAssertion',
    'BeanShellAssertion': 'BeanShellAssertion',
    'JSR223Assertion': 'JSR223Assertion',
    'CompareAssertion': 'CompareAssertion',
    'SMIMEAssertionTest': 'SMIMEAssertion',
    'HTMLAssertion': 'HTMLAssertion',
    'MD5HexAssertion': 'MD5HexAssertion',
    'BeanShellPreProcessor': 'BeanShellPreProcessor',
    'BeanShellPostProcessor': 'BeanShellPostProcessor',
    'JSR223PreProcessor': 'JSR223PreProcessor',
    'JSR223PostProcessor': 'JSR223PostProcessor',
    'UserParametersPreProcessor': 'UserParametersPreProcessor',
    'SampleTimeout': 'SampleTimeout',
    'JSONPostProcessor': 'JSONExtractor',
    'RegexExtractor': 'RegexExtractor',
    'BoundaryExtractor': 'BoundaryExtractor',
    'CSSSelectorExtractor': 'CSSSelectorExtractor',
    'XPathExtractor': 'XPathExtractor',
    'HeaderManager': 'HttpHeaderManager',
    'CookieManager': 'HTTPCookieManager',
    'CacheManager': 'HttpCacheManager',
    'AuthManager': 'HttpAuthManager',
    'DNSCacheManager': 'DNSCacheManager',
    'UserParameters': 'UserParameters',
    'CSVDataSet': 'CsvDataSource',
    'RandomVariableConfig': 'RandomVariableConfig',
    'IfController': 'IfController',
    'LoopController': 'LoopController',
    'TransactionController': 'TransactionController',
    'OnceOnlyController': 'OnceOnlyController',
    'ForEachController': 'ForEachController',
    'SwitchController': 'SwitchController',
    'WhileController': 'WhileController',
    'RandomController': 'RandomController',
    'InterleaveController': 'InterleaveController',
    'IncludeController': 'IncludeController',
    'ModuleController': 'ModuleController',
    'RunTimeController': 'RunTimeController',
    'ThroughputController': 'ThroughputController',
    'ViewResultsFullVisualizer': 'ViewResultsTree',
    'SummaryReport': 'SummaryReport',
    'StatGraphVisualizer': 'AggregateGraph',
    'Summariser': 'Summariser',
    'GraphListener': 'GraphListener',
    'BackendListener': 'InfluxDBBackendListener',
    'DebugSampler': 'DebugSampler',
    'ConstantTimer': 'ConstantTimer',
    'UniformRandomTimer': 'UniformRandomTimer',
    'GaussianRandomTimer': 'GaussianRandomTimer',
    'PoissonRandomTimer': 'PoissonRandomTimer',
    'ConstantThroughputTimer': 'ConstantThroughputTimer',
    'SynchronizingTimer': 'SynchronizingTimer',
}

_IGNORED_TYPES = {'ResultCollector', 'PropertyDisplay', 'Arguments', 'hashTree'}


def import_jmx_to_full_tree(xml_content: str) -> Dict[str, Any]:
    """解析完整JMX文件为树形结构"""
    try:
        root = ET.fromstring(xml_content)
    except ET.ParseError as e:
        raise ValueError(f"JMX XML 解析失败: {e}")

    def _find_test_plan(elem):
        if elem.tag == 'TestPlan':
            return elem
        for child in elem:
            found = _find_test_plan(child)
            if found is not None:
                return found
        return None

    test_plan_elem = _find_test_plan(root)

    if test_plan_elem is None:
        raise ValueError('未找到测试计划(TestPlan)节点')

    node = _parse_single_element(test_plan_elem)

    def _find_hash_tree_for(parent, root_elem):
        for child in root_elem:
            if child.tag == 'hashTree':
                for sub in child:
                    if sub is parent:
                        return child
                found = _find_hash_tree_for(parent, child)
                if found is not None:
                    return found
        return None

    ht = _find_hash_tree_for(test_plan_elem, root)
    if ht is not None:
        node['children'] = _parse_hash_tree_children(ht)
    else:
        parent_of_tp = None
        for child in root.iter():
            for sub in child:
                if sub is test_plan_elem:
                    parent_of_tp = child
                    break
            if parent_of_tp is not None:
                break
        if parent_of_tp is not None:
            siblings = list(parent_of_tp)
            ht2 = _find_hash_tree_after(test_plan_elem, siblings)
            if ht2 is not None:
                node['children'] = _parse_hash_tree_children(ht2)
            else:
                node['children'] = []
        else:
            node['children'] = []
    return node


def _find_hash_tree_after(parent, siblings):
    for i, s in enumerate(siblings):
        if s is parent and i + 1 < len(siblings) and siblings[i + 1].tag == 'hashTree':
            return siblings[i + 1]
    return None


def _parse_hash_tree_children(hash_tree):
    children = []
    siblings = list(hash_tree)
    i = 0
    while i < len(siblings):
        elem = siblings[i]
        if elem.tag == 'hashTree':
            i += 1
            continue
        tag = elem.tag
        if tag in _IGNORED_TYPES or tag.startswith(('stringProp', 'boolProp', 'longProp', 'intProp', 'collectionProp', 'elementProp', 'value')):
            i += 1
            continue
        mapped_type = _JMX_TYPE_MAP.get(tag)
        if not mapped_type:
            i += 1
            continue
        node = _parse_single_element(elem)
        ht = None
        if i + 1 < len(siblings) and siblings[i + 1].tag == 'hashTree':
            ht = siblings[i + 1]
            node['children'] = _parse_hash_tree_children(ht)
            i += 2
        else:
            node['children'] = []
            i += 1
        children.append(node)
    return children


def _parse_single_element(elem):
    tag = elem.tag
    name = elem.get('testname', tag)
    enabled = elem.get('enabled', 'true') != 'false'
    mapped_type = _JMX_TYPE_MAP.get(tag, tag)
    props = {}
    if mapped_type == 'TestPlan':
        props = _parse_test_plan_props(elem)
    elif mapped_type == 'ThreadGroup':
        props = _parse_thread_group_props(elem)
    elif mapped_type == 'HttpSampler':
        props = _parse_sampler_props(elem)
    elif mapped_type in ('ResponseAssertion', 'DurationAssertion', 'SizeAssertion'):
        props = _parse_assertion_props(elem, mapped_type)
    elif mapped_type in ('JSONPathAssertion', 'XPath2Assertion', 'XMLAssertion', 'CompareAssertion', 'HTMLAssertion', 'MD5HexAssertion', 'SMIMEAssertion'):
        props = _parse_assertion_props(elem, mapped_type)
    elif mapped_type == 'BeanShellAssertion':
        props = _parse_beanshell_assertion_props(elem)
    elif mapped_type == 'JSR223Assertion':
        props = _parse_jsr223_assertion_props(elem)
    elif mapped_type in ('BeanShellPreProcessor', 'BeanShellPostProcessor'):
        props = _parse_beanshell_processor_props(elem, mapped_type)
    elif mapped_type in ('JSR223PreProcessor', 'JSR223PostProcessor'):
        props = _parse_jsr223_processor_props(elem, mapped_type)
    elif mapped_type in ('JSONExtractor', 'RegexExtractor', 'BoundaryExtractor', 'CSSSelectorExtractor', 'XPathExtractor'):
        props = _parse_extractor_props(elem, mapped_type)
    elif mapped_type == 'HttpHeaderManager':
        props = _parse_header_manager_props(elem)
    elif mapped_type == 'HTTPCookieManager':
        props = _parse_cookie_manager_props(elem)
    elif mapped_type == 'HttpCacheManager':
        props = {}
    elif mapped_type == 'HttpAuthManager':
        props = _parse_auth_manager_props(elem)
    elif mapped_type == 'UserParameters':
        props = _parse_user_params_props(elem)
    elif mapped_type == 'CsvDataSource':
        props = _parse_csv_data_source_props(elem)
    elif mapped_type == 'RandomVariableConfig':
        props = _parse_random_var_props(elem)
    elif mapped_type in ('IfController', 'WhileController', 'LoopController', 'ForEachController', 'SwitchController', 'TransactionController', 'OnceOnlyController', 'IncludeController', 'ModuleController', 'RunTimeController', 'ThroughputController', 'InterleaveController', 'RandomController'):
        props = _parse_controller_props(elem, mapped_type)
    elif mapped_type in ('ViewResultsTree', 'SummaryReport', 'AggregateGraph', 'Summariser', 'GraphListener', 'InfluxDBBackendListener'):
        props = _parse_listener_props(elem, mapped_type)
    elif mapped_type == 'DebugSampler':
        props = {'jmeter_function': 'DEBUG'}
    elif mapped_type in ('ConstantTimer', 'UniformRandomTimer', 'GaussianRandomTimer', 'PoissonRandomTimer', 'ConstantThroughputTimer', 'SynchronizingTimer'):
        props = _parse_timer_props(elem, mapped_type)
    else:
        props = {}
    return {
        '_uid': f"node_{id(elem)}_{time.time()}",
        'type': mapped_type,
        'name': name,
        'enabled': enabled,
        'props': props,
    }


def _get_str_prop(elem, name, default=''):
    e = elem.find(f".//stringProp[@name='{name}']")
    return e.text.strip() if e is not None and e.text else default

def _get_bool_prop(elem, name, default=False):
    e = elem.find(f".//boolProp[@name='{name}']")
    if e is not None and e.text:
        return e.text.lower() == 'true'
    return default

def _get_int_prop(elem, name, default=0):
    e = elem.find(f".//intProp[@name='{name}']")
    try:
        return int(e.text) if e is not None and e.text else default
    except:
        return default

def _get_long_prop(elem, name, default=0):
    e = elem.find(f".//longProp[@name='{name}']")
    try:
        return int(e.text) if e is not None and e.text else default
    except:
        return default


def _parse_test_plan_props(elem):
    vars_list = []
    args = elem.find(".//elementProp[@name='TestPlan.user_defined_variables']")
    if args is not None:
        for arg in args.findall(".//elementProp[@elementType='Argument']"):
            n = _get_str_prop(arg, 'Argument.name')
            v = _get_str_prop(arg, 'Argument.value')
            if n:
                vars_list.append({'name': n, 'value': v})
    return {
        'comments': _get_str_prop(elem, 'TestPlan.comments'),
        'functional_mode': _get_bool_prop(elem, 'TestPlan.functional_mode'),
        'teardown_on_shutdown': _get_bool_prop(elem, 'TestPlan.teardown_on_shutdown'),
        'serialize_threadgroups': _get_bool_prop(elem, 'TestPlan.serialize_threadgroups'),
        'variables': vars_list,
    }

def _parse_thread_group_props(elem):
    tg_type = elem.get('guiclass', '')
    num_threads = _get_int_prop(elem, 'ThreadGroup.num_threads', 10)
    ramp_time = _get_int_prop(elem, 'ThreadGroup.ramp_time', 1)
    loops = -1
    ctrl = elem.find(".//elementProp[@name='ThreadGroup.main_controller']")
    if ctrl is not None:
        lp = ctrl.find(".//intProp[@name='LoopController.loops']")
        if lp is not None and lp.text:
            loops = int(lp.text)
        forever = ctrl.find(".//boolProp[@name='LoopController.continue_forever']")
        if forever is not None and forever.text and forever.text.lower() == 'true':
            loops = -1
    delay = _get_str_prop(elem, 'ThreadGroup.delay', '0')
    on_sample_error = _get_str_prop(elem, 'ThreadGroup.on_sample_error', 'continue')
    sched = _get_bool_prop(elem, 'ThreadGroup.scheduler')
    duration = 0
    start_time = 0
    end_time = 0
    if sched:
        duration = _get_int_prop(elem, 'ThreadGroup.duration')
        start_time = _get_long_prop(elem, 'ThreadGroup.start_time')
        end_time = _get_long_prop(elem, 'ThreadGroup.end_time')
    return {
        'num_threads': num_threads,
        'ramp_time': ramp_time,
        'loops': loops,
        'delay': delay,
        'on_sample_error': on_sample_error,
        'scheduler': sched,
        'duration': duration,
        'start_time': start_time,
        'end_time': end_time,
        'tg_type': tg_type,
    }


def _parse_sampler_props(elem):
    method = _get_str_prop(elem, 'HTTPSampler.method', 'GET')
    domain = _get_str_prop(elem, 'HTTPSampler.domain', '')
    port = _get_str_prop(elem, 'HTTPSampler.port', '')
    protocol = _get_str_prop(elem, 'HTTPSampler.protocol', 'https')
    path = _get_str_prop(elem, 'HTTPSampler.path', '/')
    encoding = _get_str_prop(elem, 'HTTPSampler.contentEncoding', 'utf-8')
    follow_redirects = _get_bool_prop(elem, 'HTTPSampler.follow_redirects', True)
    auto_redirects = _get_bool_prop(elem, 'HTTPSampler.auto_redirects', False)
    use_keepalive = _get_bool_prop(elem, 'HTTPSampler.use_keepalive', True)
    do_multipart_post = _get_bool_prop(elem, 'HTTPSampler.DO_MULTIPART_POST', False)
    embedded_url_resource = _get_str_prop(elem, 'HTTPSampler.embeddedUrlReString', '')
    connect_timeout = _get_str_prop(elem, 'HTTPSampler.connect_timeout', '')
    response_timeout = _get_str_prop(elem, 'HTTPSampler.response_timeout', '')
    port_str = f":{port}" if port else ''
    url = f"{protocol}://{domain}{port_str}{path}"
    body = ''
    post_body_raw = _get_str_prop(elem, 'HTTPSampler.postBodyRaw', '')
    if post_body_raw:
        body = post_body_raw
    else:
        args_elem = elem.find(".//elementProp[@name='HTTPsampler.Arguments']")
        if args_elem is not None:
            parts = []
            for arg in args_elem.findall(".//elementProp[@elementType='Argument']"):
                aname = _get_str_prop(arg, 'Argument.name')
                aval = _get_str_prop(arg, 'Argument.value')
                meta = _get_str_prop(arg, 'Argument.metadata', '=')
                if aname:
                    parts.append(f"{aname}{meta}{aval}")
            body = '&'.join(parts)
    return {
        'method': method,
        'url': url,
        'headers': [],
        'body': body,
        'body_type': 'json' if len(body) > 0 and (body.strip().startswith('{') or body.strip().startswith('[')) else 'form-data' if body and not body.strip().startswith('{') else 'none',
        'encoding': encoding,
        'follow_redirects': follow_redirects,
        'auto_redirects': auto_redirects,
        'use_keepalive': use_keepalive,
        'do_multipart_post': do_multipart_post,
        'embedded_url_resource': embedded_url_resource,
        'connect_timeout': connect_timeout,
        'response_timeout': response_timeout,
    }


def _parse_assertion_props(elem, assertion_type):
    if assertion_type == 'ResponseAssertion':
        field = _get_str_prop(elem, 'Assertion.test_field', 'Assertion.response_data')
        assume_success = _get_bool_prop(elem, 'Assertion.assume_success')
        comments = _get_str_prop(elem, 'Assertion.custom_message', '')
        test_type = _get_int_prop(elem, 'Assertion.test_type', 8)
        type_map = {2: 'Contains', 4: 'Not Contains', 6: 'Matches', 8: 'Equals', 16: 'Substring', 32: 'Not Substring'}
        check_type = type_map.get(test_type, 'Contains')
        patterns = []
        coll = elem.find(".//collectionProp[@name='Asserion.test_strings']")
        if coll is not None:
            for p in coll.findall(".//stringProp[@name='Assertion.test_string']"):
                if p.text is not None:
                    patterns.append(p.text)
        return {
            'field': field,
            'assume_success': assume_success,
            'check_type': check_type,
            'patterns': patterns,
            'custom_message': comments,
            'is_regex': test_type in (6, 16),
        }
    elif assertion_type == 'DurationAssertion':
        return {'duration_ms': _get_str_prop(elem, 'DurationAssertion.duration', '1000')}
    elif assertion_type == 'SizeAssertion':
        size = _get_str_prop(elem, 'SizeAssertion.size', '0')
        operator = _get_int_prop(elem, 'SizeAssertion.operator', 2)
        op_map = {1: '=', 2: '>', 3: '<', 4: '!=', 5: '>=', 6: '<='}
        return {'size': size, 'operator': op_map.get(operator, '>')}
    return {}


def _parse_beanshell_assertion_props(elem):
    script = ''
    params = _get_str_prop(elem, 'BeanShellAssertion.params', '')
    filename = _get_str_prop(elem, 'BeanShellAssertion.filename', '')
    script_elem = elem.find(".//stringProp[@name='BeanShellAssertion.script']")
    if script_elem is not None and script_elem.text:
        script = script_elem.text
    return {
        'script': script,
        'params': params,
        'filename': filename,
    }

def _parse_jsr223_assertion_props(elem):
    cache_key = _get_str_prop(elem, 'cacheKey', '')
    language = _get_str_prop(elem, 'scriptLanguage', 'groovy')
    script = _get_str_prop(elem, 'script', '')
    params = _get_str_prop(elem, 'parameters', '')
    filename = _get_str_prop(elem, 'filename', '')
    return {
        'language': language,
        'script': script,
        'params': params,
        'filename': filename,
        'cache_key': cache_key,
    }


def _parse_beanshell_processor_props(elem, proc_type):
    script = ''
    params = _get_str_prop(elem, f'{proc_type}.params', '')
    filename = _get_str_prop(elem, f'{proc_type}.filename', '')
    prop_name = f'{proc_type}.script'
    script_elem = elem.find(f".//stringProp[@name='{prop_name}']")
    if script_elem is not None and script_elem.text:
        script = script_elem.text
    return {
        'script': script,
        'params': params,
        'filename': filename,
    }

def _parse_jsr223_processor_props(elem, proc_type):
    cache_key = _get_str_prop(elem, 'cacheKey', '')
    language = _get_str_prop(elem, 'scriptLanguage', 'groovy')
    script = _get_str_prop(elem, 'script', '')
    params = _get_str_prop(elem, 'parameters', '')
    return {
        'language': language,
        'script': script,
        'params': params,
        'filename': '',
        'cache_key': cache_key,
    }


def _parse_extractor_props(elem, ext_type):
    var_names = _get_str_prop(elem, f'{ext_type}.refNames', '')
    match_num = _get_str_prop(elem, f'{ext_type}.matchNumber', '0')
    default_val = _get_str_prop(elem, f'{ext_type}.defaultValue', '')
    template = _get_str_prop(elem, f'{ext_type}.template', '$1$')
    if ext_type == 'JSONExtractor':
        json_path_exprs = _get_str_prop(elem, 'JSONPostProcessor.jsonPathExprs', '')
        match_numbers = _get_str_prop(elem, 'JSONPostProcessor.matchNumbers', '')
        default_values = _get_str_prop(elem, 'JSONPostProcessor.defaultValues', '')
        return {
            'var_names': var_names.split(',') if var_names else [],
            'json_path_expressions': json_path_exprs.split(',') if json_path_exprs else [],
            'match_numbers': match_numbers.split(',') if match_numbers else [],
            'default_values': default_values.split(',') if default_values else [],
        }
    elif ext_type == 'RegexExtractor':
        regex = _get_str_prop(elem, 'RegexExtractor.regex', '')
        template = _get_str_prop(elem, 'RegexExtractor.template', '$1$')
        return {
            'reference_name': var_names,
            'regex_expression': regex,
            'template': template,
            'match_number': match_num,
            'default_value': default_val,
        }
    elif ext_type == 'BoundaryExtractor':
        lboundary = _get_str_prop(elem, 'BoundaryExtractor.lboundary', '')
        rboundary = _get_str_prop(elem, 'BoundaryExtractor.rboundary', '')
        return {
            'reference_name': var_names,
            'left_boundary': lboundary,
            'right_boundary': rboundary,
            'match_number': match_num,
            'default_value': default_val,
        }
    elif ext_type == 'CSSSelectorExtractor':
        css = _get_str_prop(elem, 'CSSSelectorExtractor.css', '')
        attr = _get_str_prop(elem, 'CSSSelectorExtractor.attribute', '')
        return {
            'reference_name': var_names,
            'css_selector': css,
            'attribute': attr,
            'match_number': match_num,
            'default_value': default_val,
        }
    elif ext_type == 'XPathExtractor':
        xpath = _get_str_prop(elem, 'XPathExtractor.xpathQuery', '')
        frag = _get_bool_prop(elem, 'XPathExtractor.validate', False)
        tol = _get_bool_prop(elem, 'XPathExtractor.tolerant', False)
        return {
            'reference_name': var_names,
            'xpath_query': xpath,
            'validate': frag,
            'tolerant': tol,
            'match_number': match_num,
            'default_value': default_val,
        }
    return {}

def _parse_header_manager_props(elem):
    headers = []
    coll = elem.find(".//collectionProp[@name='HeaderManager.headers']")
    if coll is not None:
        for h in coll.findall(".//elementProp[@elementType='Header']"):
            hn = _get_str_prop(h, 'Header.name')
            hv = _get_str_prop(h, 'Header.value')
            if hn:
                headers.append({'key': hn, 'value': hv})
    return {'headers': headers}


def _parse_cookie_manager_props(elem):
    cookies = []
    coll = elem.find(".//collectionProp[@name='CookieManager.cookies']")
    if coll is not None:
        for c in coll.findall(".//elementProp[@elementType='Cookie']"):
            cookies.append({
                'name': _get_str_prop(c, 'Cookie.name'),
                'value': _get_str_prop(c, 'Cookie.value'),
                'domain': _get_str_prop(c, 'Cookie.domain', ''),
                'path': _get_str_prop(c, 'Cookie.path', '/'),
                'secure': _get_bool_prop(c, 'Cookie.secure'),
                'expires': _get_long_prop(c, 'Cookie.expires', 0),
            })
    policy = _get_int_prop(elem, 'CookieManager.policy', 0)
    return {
        'cookies': cookies,
        'policy': policy,
        'clear_each_iteration': _get_bool_prop(elem, 'CookieManager.clearEachIteration', False),
    }

def _parse_auth_manager_props(elem):
    auth_mech_list = []
    mech_list = elem.find(".//collectionProp[@name='AuthManager.auth_list']")
    if mech_list is not None:
        for m in mech_list.findall(".//elementProp[@elementType='Authorization']"):
            auth_mech_list.append({
                'url': _get_str_prop(m, 'Authorization.url'),
                'username': _get_str_prop(m, 'Authorization.username'),
                'password': _get_str_prop(m, 'Authorization.password'),
                'domain': _get_str_prop(m, 'Authorization.domain', ''),
                'realm': _get_str_prop(m, 'Authorization.realm', ''),
                'mechanism': _get_int_prop(m, 'Authorization.mechanism', 0),
            })
    return {
        'auth_list': auth_mech_list,
        'control_panel': _get_bool_prop(elem, 'AuthManager.controlledByThreadGroup', True),
    }

def _parse_user_params_props(elem):
    params = []
    coll = elem.find(".//collectionProp[@name='UserParameters.names']")
    vals_coll = elem.find(".//collectionProp[@name='UserParameters.thread_values']")
    names = []
    if coll is not None:
        for n in coll.findall(".//stringProp[@name='UserParameters.names']"):
            if n.text:
                names.append(n.text)
    per_thread_vals = []
    if vals_coll is not None:
        for tv in vals_coll.findall(".//collectionProp[@name='UserParameters.thread_1']"):
            row = []
            for sv in tv.findall(".//stringProp[@name='UserParameters.thread_1']"):
                row.append(sv.text if sv.text else '')
            per_thread_vals.append(row)
    return {
        'names': names,
        'per_thread_values': per_thread_vals,
    }

def _parse_csv_data_source_props(elem):
    return {
        'file_path': _get_str_prop(elem, 'filename', ''),
        'variable_names': _get_str_prop(elem, 'variableNames', ''),
        'delimiter': _get_str_prop(elem, 'delimiter', ','),
        'share_mode': _get_str_prop(elem, 'shareMode', 'allThreads'),
        'quoted_data': _get_bool_prop(elem, 'quotedData', False),
        'recycle': _get_bool_prop(elem, 'recycle', True),
        'stop_thread': _get_bool_prop(elem, 'stopThread', False),
        'ignore_first_line': _get_bool_prop(elem, 'firstLineIsNames', True),
    }

def _parse_random_var_props(elem):
    return {
        'variable_name': _get_str_prop(elem, 'variable_name', ''),
        'min_value': _get_str_prop(elem, 'min_value', ''),
        'max_value': _get_str_prop(elem, 'max_value', ''),
        'per_thread': _get_bool_prop(elem, 'perThread', False),
    }

def _parse_controller_props(elem, ctrl_type):
    if ctrl_type == 'IfController':
        return {
            'condition': _get_str_prop(elem, 'IfController.condition', ''),
            'evaluate_all': _get_bool_prop(elem, 'IfController.evaluateAll', False),
            'use_interpreter': _get_bool_prop(elem, 'IfController.useInterpretedConditionAsExpression', True),
        }
    elif ctrl_type == 'LoopController':
        loops = _get_int_prop(elem, 'LoopController.loops', -1)
        forever = _get_bool_prop(elem, 'LoopController.continue_forever', loops <= 0)
        return {'loops': loops if not forever else -1, 'continue_forever': forever}
    elif ctrl_type == 'WhileController':
        return {'condition': _get_str_prop(elem, 'WhileController.condition', '')}
    elif ctrl_type == 'ForEachController':
        return {
            'input_var_prefix': _get_str_prop(elem, 'ForEachController.inputVar', ''),
            'output_var_name': _get_str_prop(elem, 'ForEachController.returnVal', ''),
            'use_separator': _get_bool_prop(elem, 'ForEachController.useSeparator', True),
        }
    elif ctrl_type == 'SwitchController':
        return {'condition': _get_str_prop(elem, 'SwitchController.value', '')}
    elif ctrl_type == 'TransactionController':
        return {
            'parent': _get_bool_prop(elem, 'TransactionController.parent', True),
            'include_timers': _get_bool_prop(elem, 'TransactionController.includeTimers', False),
        }
    elif ctrl_type == 'OnceOnlyController':
        return {}
    elif ctrl_type == 'IncludeController':
        return {'include_path': _get_str_prop(elem, 'IncludeController.includepath', '')}
    elif ctrl_type == 'ThroughputController':
        style = _get_int_prop(elem, 'ThroughputController.style', 1)
        max_throughput = _get_int_prop(elem, 'ThroughputController.maxThroughput', 1)
        percent = _get_float_prop(elem, 'ThroughputController.percentThroughput', 100.0) if hasattr(_get_float_prop, '__call__') else 100.0
        per_thread = _get_bool_prop(elem, 'ThroughputController.perThread', False)
        executions = _get_int_prop(elem, 'ThroughputController.maxExecutions', 0)
        return {'style': style, 'max_throughput': max_throughput, 'percent': percent, 'per_thread': per_thread, 'executions': executions}
    elif ctrl_type == 'RunTimeController':
        return {'seconds': _get_int_prop(elem, 'RuntimeController.runtime', 60)}
    return {}

def _get_float_prop(elem, name, default=0.0):
    e = elem.find(f".//floatProp[@name='{name}']")
    try:
        return float(e.text) if e is not None and e.text else default
    except:
        return default

def _parse_listener_props(elem, listener_type):
    if listener_type == 'InfluxDBBackendListener':
        influxdb_host = _get_str_prop(elem, 'influxdbMetricsSender.influxdbHost', '')
        influxdb_port = _get_str_prop(elem, 'influxdbMetricsSender.influxdbPort', '8086')
        return {
            'influxdbHost': influxdb_host,
            'influxdbPort': influxdb_port,
            'influxdbDatabase': _get_str_prop(elem, 'influxdbMetricsSender.influxdbDatabase', 'jmeter'),
            'retentionPolicy': _get_str_prop(elem, 'influxdbMetricsSender.retentionPolicy', ''),
            'measurement': _get_str_prop(elem, 'influxdbMetricsSender.measurement', 'jmeter'),
            'summaryOnly': _get_bool_prop(elem, 'influxdbMetricsSender.summaryOnly', False),
            'samplersList': _get_str_prop(elem, 'influxdbMetricsSender.samplersList', ''),
            'testTitle': _get_str_prop(elem, 'testTitle', ''),
        }
    elif listener_type == 'ViewResultsTree':
        return {'auto_expand': _get_bool_prop(elem, 'autoExpandCols', False)}
    return {}

def _parse_timer_props(elem, timer_type):
    if timer_type == 'ConstantTimer':
        return {'delay': _get_str_prop(elem, 'ConstantTimer.delay', '300')}
    elif timer_type == 'UniformRandomTimer':
        return {
            'delay': _get_str_prop(elem, 'RandomTimer.delay', '0'),
            'range': _get_str_prop(elem, 'RandomTimer.range', '100'),
        }
    elif timer_type == 'ConstantThroughputTimer':
        return {
            'throughput': _get_str_prop(elem, 'throughput', '60.0'),
            'calc_duration': _get_int_prop(elem, 'calcDuration', 60),
            'mode': _get_int_prop(elem, 'mode', 1),
        }
    elif timer_type == 'SynchronizingTimer':
        return {
            'virtual_users': _get_int_prop(elem, 'numUsers', 0),
            'timeout': _get_long_prop(elem, 'timeoutInMs', 0),
        }
    return {'delay': '300'}


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
    elif ntype == "BeanShellAssertion":
        _build_beanshell_assertion(parent_hash_tree, name, props)
    elif ntype == "JSR223Assertion":
        _build_jsr223_assertion(parent_hash_tree, name, props)
    elif ntype == "SizeAssertion":
        _build_size_assertion(parent_hash_tree, name, props)
    elif ntype == "XPathAssertion":
        _build_xpath_assertion(parent_hash_tree, name, props)
    elif ntype == "CompareAssertion":
        _build_compare_assertion(parent_hash_tree, name, props)
    elif ntype == "XMLAssertion":
        _build_xml_assertion(parent_hash_tree, name, props)
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
    elif ntype == "JSR223PreProcessor":
        _build_jsr223(parent_hash_tree, name, props, "pre")
    elif ntype == "JSR223PostProcessor":
        _build_jsr223(parent_hash_tree, name, props, "post")
    elif ntype == "JDBCConnection":
        _build_jdbc_connection(parent_hash_tree, name, props)
    elif ntype == "JDBCSampler":
        _build_jdbc_sampler(parent_hash_tree, name, props)
    elif ntype == "HTTPHeaderManager":
        _build_header_manager(parent_hash_tree, name, props)
    elif ntype == "HTTPCookieManager":
        _build_cookie_manager(parent_hash_tree, name, props)
    elif ntype == "HTTPRequestDefaults":
        _build_http_request_defaults(parent_hash_tree, name, props)
    elif ntype == "IfController":
        _build_if_controller(parent_hash_tree, name, props, children)
    elif ntype == "LoopController":
        _build_loop_controller(parent_hash_tree, name, props, children)
    elif ntype == "WhileController":
        _build_while_controller(parent_hash_tree, name, props, children)
    elif ntype == "TransactionController":
        _build_transaction_controller(parent_hash_tree, name, props, children)
    elif ntype == "ThroughputController":
        _build_throughput_controller(parent_hash_tree, name, props, children)
    elif ntype == "OnceOnlyController":
        _build_once_only_controller(parent_hash_tree, name, props, children)
    elif ntype == "ViewResultsTree":
        _build_listener(parent_hash_tree, name, "ViewResultsFullVisualizer", "ResultCollector")
    elif ntype == "SummaryReport":
        _build_listener(parent_hash_tree, name, "SummaryReport", "ResultCollector")
    elif ntype == "AggregateGraph":
        _build_listener(parent_hash_tree, name, "StatGraphVisualizer", "ResultCollector")
    elif ntype == "AggregateReport":
        _build_listener(parent_hash_tree, name, "StatAggregateVisualizer", "ResultCollector")
    elif ntype == "ResponseTimeGraph":
        _build_listener(parent_hash_tree, name, "RespTimeGraphVisualizer", "ResultCollector")
    elif ntype == "InfluxDBBackendListener":
        _build_influxdb_backend_listener(parent_hash_tree, name, props)
    elif ntype == "UserParameters":
        _build_user_parameters(parent_hash_tree, name, props)
    elif ntype == "DebugSampler":
        _build_debug_sampler(parent_hash_tree, name)
    elif ntype == "ForEachController":
        _build_foreach_controller(parent_hash_tree, name, props, children)
    elif ntype == "SwitchController":
        _build_switch_controller(parent_hash_tree, name, props, children)
    elif ntype in ("RandomController", "InterleaveController"):
        _build_random_interleave_controller(parent_hash_tree, ntype, name, children)
    elif ntype == "IncludeController":
        _build_include_controller(parent_hash_tree, name, props)


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


def _build_jsr223(parent, name, props, phase):
    tag = "JSR223PreProcessor" if phase == "pre" else "JSR223PostProcessor"
    gui = "TestBeanGUI"
    p = ET.SubElement(parent, tag)
    p.set("guiclass", gui)
    p.set("testclass", tag)
    p.set("testname", name or f"JSR223 {phase}")
    p.set("enabled", "true")
    _add_element_prop(p, "scriptLanguage", props.get("language", "groovy"))
    _add_element_prop(p, "script", props.get("script", ""))
    ET.SubElement(parent, "hashTree")


def _build_header_manager(parent, name, props):
    hm = ET.SubElement(parent, "HeaderManager")
    hm.set("guiclass", "HeaderPanel")
    hm.set("testclass", "HeaderManager")
    hm.set("testname", name or "HTTP Header Manager")
    hm.set("enabled", "true")
    cp = ET.SubElement(hm, "collectionProp")
    cp.set("name", "HeaderManager.headers")
    for h in (props.get("headers") or []):
        if not h.get("key"): continue
        he = ET.SubElement(cp, "elementProp")
        he.set("name", "")
        he.set("elementType", "Header")
        _add_element_prop(he, "Header.name", h["key"])
        _add_element_prop(he, "Header.value", str(h.get("value", "")))
    ET.SubElement(parent, "hashTree")


def _build_cookie_manager(parent, name, props):
    cm = ET.SubElement(parent, "CookieManager")
    cm.set("guiclass", "CookiePanel")
    cm.set("testclass", "CookieManager")
    cm.set("testname", name or "HTTP Cookie Manager")
    cm.set("enabled", "true")
    _add_element_prop(cm, "CookieManager.clearEachIteration", "true" if props.get("clearEachIteration") else "false")
    ET.SubElement(parent, "hashTree")


def _build_http_request_defaults(parent, name, props):
    d = ET.SubElement(parent, "ConfigTestElement")
    d.set("guiclass", "HttpDefaultsGui")
    d.set("testclass", "ConfigTestElement")
    d.set("testname", name or "HTTP Request Defaults")
    d.set("enabled", "true")
    url = props.get("url", "")
    from urllib.parse import urlparse as up
    pu = up(url) if url else None
    _add_element_prop(d, "HTTPSampler.domain", pu.hostname if pu else "")
    _add_element_prop(d, "HTTPSampler.port", str(pu.port) if pu and pu.port else "")
    _add_element_prop(d, "HTTPSampler.protocol", pu.scheme if pu else "")
    _add_element_prop(d, "HTTPSampler.contentEncoding", "UTF-8")
    _add_element_prop(d, "HTTPSampler.path", "")
    ET.SubElement(parent, "hashTree")


def _build_if_controller(parent, name, props, children):
    c = ET.SubElement(parent, "IfController")
    c.set("guiclass", "IfControllerPanel")
    c.set("testclass", "IfController")
    c.set("testname", name or "If Controller")
    c.set("enabled", "true")
    _add_element_prop(c, "IfController.condition", props.get("condition", "${JMeterThread.last_sample_ok}"))
    _add_element_prop(c, "IfController.evaluateAll", "true" if props.get("evaluateAll") else "false")
    _add_element_prop(c, "IfController.useExpression", "true" if props.get("useExpression") else "false")
    sh = ET.SubElement(parent, "hashTree")
    for child in children:
        _build_tree_node(sh, child)


def _build_loop_controller(parent, name, props, children):
    c = ET.SubElement(parent, "LoopController")
    c.set("guiclass", "LoopControlPanel")
    c.set("testclass", "LoopController")
    c.set("testname", name or "Loop Controller")
    c.set("enabled", "true")
    _add_element_prop(c, "LoopController.loops", str(props.get("loops", 3)))
    _add_element_prop(c, "LoopController.continue_forever", "true" if props.get("forever") else "false")
    sh = ET.SubElement(parent, "hashTree")
    for child in children:
        _build_tree_node(sh, child)


def _build_while_controller(parent, name, props, children):
    c = ET.SubElement(parent, "WhileController")
    c.set("guiclass", "WhileControllerGui")
    c.set("testclass", "WhileController")
    c.set("testname", name or "While Controller")
    c.set("enabled", "true")
    _add_element_prop(c, "WhileController.condition", props.get("condition", ""))
    sh = ET.SubElement(parent, "hashTree")
    for child in children:
        _build_tree_node(sh, child)


def _build_transaction_controller(parent, name, props, children):
    c = ET.SubElement(parent, "TransactionController")
    c.set("guiclass", "TransactionControllerGui")
    c.set("testclass", "TransactionController")
    c.set("testname", name or "Transaction Controller")
    c.set("enabled", "true")
    _add_element_prop(c, "TransactionController.includeTimers", "true" if props.get("includeTimers") else "false")
    _add_element_prop(c, "TransactionController.parent", "true" if props.get("parent") else "false")
    sh = ET.SubElement(parent, "hashTree")
    for child in children:
        _build_tree_node(sh, child)


def _build_throughput_controller(parent, name, props, children):
    c = ET.SubElement(parent, "ThroughputController")
    c.set("guiclass", "ThroughputControllerGui")
    c.set("testclass", "ThroughputController")
    c.set("testname", name or "Throughput Controller")
    c.set("enabled", "true")
    style_map = {"percent": "0", "total": "1", "perMinute": "2"}
    _add_element_prop(c, "ThroughputController.style", style_map.get(props.get("style"), "0"))
    _add_element_prop(c, "ThroughputController.percentThroughput", str(props.get("percent", 50)))
    _add_element_prop(c, "ThroughputController.maxThroughput", str(props.get("maxThroughput", 1)))
    _add_element_prop(c, "ThroughputController.perThread", "true" if props.get("perThread") else "false")
    sh = ET.SubElement(parent, "hashTree")
    for child in children:
        _build_tree_node(sh, child)


def _build_once_only_controller(parent, name, props, children):
    c = ET.SubElement(parent, "OnceOnlyController")
    c.set("guiclass", "OnceOnlyControllerGui")
    c.set("testclass", "OnceOnlyController")
    c.set("testname", name or "Once Only Controller")
    c.set("enabled", "true")
    sh = ET.SubElement(parent, "hashTree")
    for child in children:
        _build_tree_node(sh, child)


def _build_beanshell_assertion(parent, name, props):
    a = ET.SubElement(parent, "BeanShellAssertion")
    a.set("guiclass", "BeanShellAssertionGui")
    a.set("testclass", "BeanShellAssertion")
    a.set("testname", name or "BeanShell Assertion")
    a.set("enabled", "true")
    _add_element_prop(a, "BeanShellAssertion.query", props.get("script", ""))
    _add_element_prop(a, "BeanShellAssertion.filename", props.get("filename", ""))
    _add_element_prop(a, "BeanShellAssertion.parameters", props.get("parameters", ""))
    _add_element_prop(a, "BeanShellAssertion.resetInterpreter", "true" if props.get("resetInterpreter") else "false")
    ET.SubElement(parent, "hashTree")


def _build_jsr223_assertion(parent, name, props):
    a = ET.SubElement(parent, "JSR223Assertion")
    a.set("guiclass", "TestBeanGUI")
    a.set("testclass", "JSR223Assertion")
    a.set("testname", name or "JSR223 Assertion")
    a.set("enabled", "true")
    _add_element_prop(a, "scriptLanguage", props.get("language", "groovy"))
    _add_element_prop(a, "script", props.get("script", ""))
    ET.SubElement(parent, "hashTree")


def _build_size_assertion(parent, name, props):
    a = ET.SubElement(parent, "SizeAssertion")
    a.set("guiclass", "SizeAssertionGui")
    a.set("testclass", "SizeAssertion")
    a.set("testname", name or "Size Assertion")
    a.set("enabled", "true")
    cmp = {"<": "2", "=": "3", ">": "4", "≠": "5"}
    _add_element_prop(a, "SizeAssertion.size", str(props.get("size", 5000)))
    _add_element_prop(a, "SizeAssertion.operator", cmp.get(props.get("operator", ">"), "4"))
    ET.SubElement(parent, "hashTree")


def _build_xpath_assertion(parent, name, props):
    a = ET.SubElement(parent, "XPathAssertion")
    a.set("guiclass", "XPathAssertionGui")
    a.set("testclass", "XPathAssertion")
    a.set("testname", name or "XPath Assertion")
    a.set("enabled", "true")
    _add_element_prop(a, "XPathAssertion.xpath", props.get("xpath", "/"))
    _add_element_prop(a, "XPathAssertion.validate", "true")
    _add_element_prop(a, "XPathAssertion.whitespace", "true")
    _add_element_prop(a, "XPathAssertion.tolerant", "false")
    _add_element_prop(a, "XPathAssertion.namespace", "false")
    _add_element_prop(a, "XPathAssertion.negate", "true" if props.get("negate") else "false")
    ET.SubElement(parent, "hashTree")


def _build_compare_assertion(parent, name, props):
    a = ET.SubElement(parent, "CompareAssertion")
    a.set("guiclass", "TestBeanGUI")
    a.set("testclass", "CompareAssertion")
    a.set("testname", name or "Compare Assertion")
    a.set("enabled", "true")
    cmp = {"==": "8", "contains": "6", "matches": "2", "≠": "11", "substring": "7"}
    _add_element_prop(a, "CompareAssertion.test_field", props.get("testField", "Assertion.response_data"))
    _add_element_prop(a, "CompareAssertion.test_type", cmp.get(props.get("compareType", "contains"), "6"))
    _add_element_prop(a, "CompareAssertion.compare_content", "true" if props.get("compareContent") else "false")
    cp = ET.SubElement(a, "collectionProp")
    cp.set("name", "CompareAssertion.test_strings")
    sp = ET.SubElement(cp, "stringProp")
    sp.set("name", "0")
    sp.text = str(props.get("expected", ""))
    ET.SubElement(parent, "hashTree")


def _build_xml_assertion(parent, name, props):
    a = ET.SubElement(parent, "XMLAssertion")
    a.set("guiclass", "XMLAssertionGui")
    a.set("testclass", "XMLAssertion")
    a.set("testname", name or "XML Assertion")
    a.set("enabled", "true")
    ET.SubElement(parent, "hashTree")


def _build_influxdb_backend_listener(parent, name, props):
    el = ET.SubElement(parent, "BackendListener")
    el.set("guiclass", "BackendListenerGui")
    el.set("testclass", "BackendListener")
    el.set("testname", name or "InfluxDB Backend Listener")
    el.set("enabled", "true")
    _add_element_prop(el, "classname", "org.apache.jmeter.visualizers.backend.influxdb.InfluxDBBackendListenerClient")
    args = ET.SubElement(el, "elementProp")
    args.set("name", "arguments")
    args.set("elementType", "Arguments",)
    args.set("guiclass", "ArgumentsPanel")
    args.set("testclass", "Arguments")
    coll = ET.SubElement(args, "collectionProp")
    coll.set("name", "Arguments.arguments")
    influxdb_args = [
        ("influxdbUrl", props.get("influxdbUrl", "http://localhost:8086/write?db=jmeter")),
        ("application", props.get("application", "test")),
        ("measurement", props.get("measurement", "jmeter")),
        ("summaryOnly", str(props.get("summaryOnly", False)).lower()),
        ("samplersRegex", props.get("samplersRegex", "")),
        ("percentiles", props.get("percentiles", "50;90;95;99")),
        ("testTitle", props.get("testTitle", "")),
        ("eventTags", props.get("eventTags", "")),
        ("tagRandom", props.get("tagRandom", "")),
    ]
    for i, (aname, aval) in enumerate(influxdb_args):
        arg = ET.SubElement(coll, "elementProp")
        arg.set(f"Argument.name_{i}", aname)
        arg.set("elementType", "Argument")
        arg.set("guiclass", "ArgumentPanel")
        arg.set("testclass", "Argument")
        arg.set("enabled", "true")
        sp = ET.SubElement(arg, "stringProp")
        sp.set("name", "Argument.value")
        sp.text = aval
        sp2 = ET.SubElement(arg, "stringProp")
        sp2.set("name", "Argument.metadata")
        sp2.text = "="
    ET.SubElement(parent, "hashTree")


def _build_user_parameters(parent, name, props):
    el = ET.SubElement(parent, "UserParameters")
    el.set("guiclass", "UserParametersGui")
    el.set("testclass", "UserParameters")
    el.set("testname", name or "User Parameters")
    el.set("enabled", "true")
    names = props.get("names", ["sid"])
    users = props.get("users", [["user1"]])
    per_iter = props.get("perIteration", False)
    _add_element_prop(el, "UserNames_per_iteration", "true" if per_iter else "false")
    names_coll = ET.SubElement(el, "collectionProp")
    names_coll.set("name", "UserNames.names")
    for n in names:
        sp = ET.SubElement(names_coll, "stringProp")
        sp.set("name", n if n else f"{len(names_coll)}")
        sp.text = n
    thread_users = ET.SubElement(el, "collectionProp")
    thread_users.set("name", "UserUsers.thread_users")
    for ui, user in enumerate(users):
        up = ET.SubElement(thread_users, "collectionProp")
        up.set(f"name_{ui}", f"{ui}")
        for vi, val in enumerate(user):
            sp = ET.SubElement(up, "stringProp")
            sp.set(f"name_{vi}", val if val else "")
            sp.text = val
    ET.SubElement(parent, "hashTree")


def _build_debug_sampler(parent, name):
    el = ET.SubElement(parent, "DebugSampler")
    el.set("guiclass", "TestBeanGUI")
    el.set("testclass", "DebugSampler")
    el.set("testname", name or "Debug Sampler")
    el.set("enabled", "true")
    _add_element_prop(el, "displayJMeterProperties", "false")
    _add_element_prop(el, "displayJMeterVariables", "true")
    _add_element_prop(el, "displaySystemProperties", "false")
    ET.SubElement(parent, "hashTree")


def _build_foreach_controller(parent, name, props, children):
    c = ET.SubElement(parent, "ForeachController")
    c.set("guiclass", "ForeachControlPanel")
    c.set("testclass", "ForeachController")
    c.set("testname", name or "For Each Controller")
    c.set("enabled", "true")
    _add_element_prop(c, "ForeachController.inputVar", props.get("inputVar", ""))
    _add_element_prop(c, "ForeachController.outputVar", props.get("outputVar", ""))
    _add_element_prop(c, "ForeachController.useSeparator", "true" if props.get("useSeparator") else "false")
    _add_element_prop(c, "ForeachController.separator", props.get("separator", "_"))
    sh = ET.SubElement(parent, "hashTree")
    for child in children:
        _build_tree_node(sh, child)


def _build_switch_controller(parent, name, props, children):
    c = ET.SubElement(parent, "SwitchController")
    c.set("guiclass", "SwitchControllerGui")
    c.set("testclass", "SwitchController")
    c.set("testname", name or "Switch Controller")
    c.set("enabled", "true")
    _add_element_prop(c, "SwitchController.switch_value", props.get("switchValue", ""))
    sh = ET.SubElement(parent, "hashTree")
    for child in children:
        _build_tree_node(sh, child)


def _build_random_interleave_controller(parent, ntype, name, children):
    if ntype == "RandomController":
        guiclass, testclass = "RandomControlGui", "RandomController"
        label = "Random Controller"
    else:
        guiclass, testclass = "InterleaveControlGui", "InterleaveControl"
        label = "Interleave Controller"
    c = ET.SubElement(parent, testclass)
    c.set("guiclass", guiclass)
    c.set("testclass", testclass)
    c.set("testname", name or label)
    c.set("enabled", "true")
    sh = ET.SubElement(parent, "hashTree")
    for child in children:
        _build_tree_node(sh, child)


def _build_include_controller(parent, name, props):
    c = ET.SubElement(parent, "IncludeController")
    c.set("guiclass", "IncludeControlGui")
    c.set("testclass", "IncludeController")
    c.set("testname", name or "Include Controller")
    c.set("enabled", "true")
    _add_element_prop(c, "IncludeController.includepath", props.get("includePath", ""))
    ET.SubElement(parent, "hashTree")
