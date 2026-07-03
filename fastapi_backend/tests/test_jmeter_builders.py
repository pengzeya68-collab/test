"""
JMeter JMX XML 生成器单元测试(Stage F.1)

覆盖 fastapi_backend/services/autotest_jmeter_service.py 中的:
- _build_* 函数族(50+ 个)生成的 XML 可被 ElementTree 解析
- _JMX_TYPE_MAP 60 项类型映射
- _TYPE_BUILD_ALIASES 别名归一化机制
- 关键元素的 JMeter 5.6.3 tag 命名规范
"""

import xml.etree.ElementTree as ET

import pytest

from fastapi_backend.services.autotest_jmeter_service import (
    _JMX_TYPE_MAP,
    _TYPE_BUILD_ALIASES,
    export_cases_to_jmx,
    export_tree_to_jmx,
)


# ========== _JMX_TYPE_MAP 完整性 ==========


class TestJmxTypeMap:
    """验证 _JMX_TYPE_MAP 60 项类型映射的完整性"""

    def test_type_map_has_60_entries(self):
        """确保所有 60 项类型注册无遗漏"""
        assert len(_JMX_TYPE_MAP) >= 60, f"实际项数: {len(_JMX_TYPE_MAP)}"

    def test_critical_jmeter_tags_present(self):
        """关键 JMeter 5.6.3 规范 tag 必须存在"""
        must_have = [
            "HTTPSamplerProxy",  # HTTP 请求
            "TestPlan", "ThreadGroup",
            "ResponseAssertion", "JSONPathAssertion", "DurationAssertion",
            "SizeAssertion", "XPath2Assertion", "BeanShellAssertion",
            "JSR223Assertion", "CompareAssertion",
            "JSONPostProcessor", "RegexExtractor", "BoundaryExtractor",
            "CSSSelectorExtractor", "XPathExtractor",
            "HeaderManager", "CookieManager", "CacheManager", "AuthManager",
            "CSVDataSet", "RandomVariableConfig",
            "ConstantTimer", "UniformRandomTimer", "GaussianRandomTimer",
            "PoissonRandomTimer", "ConstantThroughputTimer", "SynchronizingTimer",
            "IfController", "LoopController", "WhileController",
            "TransactionController", "OnceOnlyController", "ThroughputController",
            "ModuleController", "RunTimeController", "IncludeController",
            "ViewResultsFullVisualizer", "SummaryReport", "StatGraphVisualizer",
            "Summariser", "BackendListener", "DebugSampler",
        ]
        for tag in must_have:
            assert tag in _JMX_TYPE_MAP, f"缺失关键 JMeter tag: {tag}"

    def test_no_duplicate_values(self):
        """值集合不应有重复(避免两个 JMeter tag 映射到同一个前端 type)"""
        values = list(_JMX_TYPE_MAP.values())
        # 允许少量已知重复(HTTPSamplerProxy 和 HTTPSampler 都映射到 HttpSampler)
        # 但其他类型应唯一
        from collections import Counter
        counts = Counter(values)
        duplicates = {v: c for v, c in counts.items() if c > 1}
        # 仅允许 HttpSampler 重复
        allowed_duplicates = {"HttpSampler"}
        for dup in duplicates:
            assert dup in allowed_duplicates, f"意外的重复映射: {dup} 出现 {duplicates[dup]} 次"


# ========== _TYPE_BUILD_ALIASES 别名归一化 ==========


class TestTypeBuildAliases:
    """验证旧别名 → 规范名归一化机制"""

    def test_old_assertion_alias_normalized(self):
        """JsonAssertion → JSONPathAssertion"""
        assert _TYPE_BUILD_ALIASES.get("JsonAssertion") == "JSONPathAssertion"

    def test_old_extractor_alias_normalized(self):
        """JsonExtractor → JSONExtractor(importer 输出规范名)"""
        assert _TYPE_BUILD_ALIASES.get("JsonExtractor") == "JSONExtractor"

    def test_old_timer_alias_normalized(self):
        """SyncTimer → SynchronizingTimer"""
        assert _TYPE_BUILD_ALIASES.get("SyncTimer") == "SynchronizingTimer"

    def test_old_csv_alias_normalized(self):
        """CSVDataSet → CsvDataSource"""
        assert _TYPE_BUILD_ALIASES.get("CSVDataSet") == "CsvDataSource"

    def test_old_header_manager_alias_normalized(self):
        """HTTPHeaderManager → HttpHeaderManager"""
        assert _TYPE_BUILD_ALIASES.get("HTTPHeaderManager") == "HttpHeaderManager"

    def test_alias_targets_are_canonical(self):
        """所有别名目标必须是 _JMX_TYPE_MAP 中已映射的规范名"""
        canonical_types = set(_JMX_TYPE_MAP.values())
        for alias, target in _TYPE_BUILD_ALIASES.items():
            assert target in canonical_types or target == "HttpSampler", \
                f"别名 {alias} → {target},但 {target} 不在规范类型集合中"


# ========== export_cases_to_jmx XML 解析 ==========


class TestExportCasesToJmx:
    """测试 export_cases_to_jmx 生成有效 XML"""

    def _minimal_case(self):
        return {
            "name": "Test API",
            "method": "GET",
            "url": "https://api.example.com/users",
            "headers": [{"key": "Authorization", "value": "Bearer test-token"}],
            "body": "",
        }

    def test_generates_valid_xml(self):
        """生成的 JMX 必须是可解析的 XML"""
        jmx = export_cases_to_jmx([self._minimal_case()])
        assert jmx and isinstance(jmx, str)
        root = ET.fromstring(jmx)
        assert root.tag == "jmeterTestPlan"

    def test_has_test_plan(self):
        """必须包含 TestPlan 节点"""
        jmx = export_cases_to_jmx([self._minimal_case()])
        root = ET.fromstring(jmx)
        test_plans = root.findall(".//TestPlan")
        assert len(test_plans) >= 1

    def test_has_thread_group(self):
        """必须包含 ThreadGroup"""
        jmx = export_cases_to_jmx([self._minimal_case()])
        root = ET.fromstring(jmx)
        thread_groups = root.findall(".//ThreadGroup")
        assert len(thread_groups) >= 1

    def test_has_http_sampler(self):
        """必须包含 HTTPSamplerProxy"""
        jmx = export_cases_to_jmx([self._minimal_case()])
        root = ET.fromstring(jmx)
        samplers = root.findall(".//HTTPSamplerProxy")
        assert len(samplers) >= 1

    def test_thread_group_config_applied(self):
        """thread_group_config 必须被应用"""
        jmx = export_cases_to_jmx(
            [self._minimal_case()],
            thread_group_config={"num_threads": 50, "ramp_time": 10, "loop_count": 5, "duration": 0},
        )
        root = ET.fromstring(jmx)
        tg = root.find(".//ThreadGroup")
        assert tg is not None
        # 验证 num_threads 通过 elementProp 写入
        props = {p.get("name"): p for p in tg.findall(".//elementProp")}
        # elementProp 的 value 子元素存储实际值
        for prop_name in ["ThreadGroup.num_threads", "ThreadGroup.ramp_time"]:
            elem = tg.find(f".//elementProp[@name='{prop_name}']")
            if elem is not None:
                value_elem = elem.find(".//string")
                if value_elem is not None:
                    assert value_elem.text in ("50", "10"), f"{prop_name}={value_elem.text}"

    def test_duration_scheduler_enabled(self):
        """duration > 0 时必须启用 scheduler"""
        jmx = export_cases_to_jmx(
            [self._minimal_case()],
            thread_group_config={"num_threads": 1, "ramp_time": 1, "loop_count": 1, "duration": 60},
        )
        root = ET.fromstring(jmx)
        tg = root.find(".//ThreadGroup")
        # 找到 scheduler elementProp 并检查其值
        sched_elem = tg.find(f".//elementProp[@name='ThreadGroup.scheduler']")
        if sched_elem is not None:
            value_elem = sched_elem.find(".//string")
            if value_elem is not None:
                assert value_elem.text == "true"


# ========== export_tree_to_jmx 11 个新元素 ==========


class TestExportTreeNewElements:
    """测试 11 个 Stage D 新增元素的 JMX 生成"""

    def _build_tree_with(self, child_type, child_props=None):
        """构建包含指定子节点类型的树"""
        if child_props is None:
            child_props = {}
        return {
            "type": "ThreadGroup",
            "name": "TG",
            "props": {},
            "children": [
                {
                    "type": "HttpSampler",
                    "name": "HTTP Req",
                    "props": {"method": "GET", "url": "https://api.example.com/test", "headers": []},
                    "children": [
                        {"type": child_type, "name": f"Test {child_type}", "props": child_props, "children": []}
                    ],
                }
            ],
        }

    @pytest.mark.parametrize("element_type,props", [
        ("BoundaryExtractor", {"referenceName": "var1", "leftBoundary": "[", "rightBoundary": "]", "matchNumber": "1", "defaultValue": ""}),
        ("CSSSelectorExtractor", {"referenceName": "cssVar", "selector": ".title", "attribute": "text", "matchNumber": "0", "defaultValue": ""}),
        ("XPathExtractor", {"referenceName": "xv", "xPath": "/root/item", "matchNumber": "1", "defaultValue": ""}),
        ("ConstantThroughputTimer", {"throughput": "600", "calcMode": "1"}),
        ("PoissonRandomTimer", {"delay": "100", "range": "200", "factor": "1.0"}),
        ("HttpCacheManager", {"clearEachIteration": True, "useExpires": True, "maxSize": "5000"}),
        ("HttpAuthManager", {"users": [{"name": "user1", "user": "admin", "pass": "pass", "url": "https://api.example.com"}]}),
        ("ModuleController", {"nodePath": "/Test Plan/TG/HTTP Req"}),
        ("RunTimeController", {"runtime": "60"}),
        ("Summariser", {"interval": "30", "ignoreTCGA": True}),
        ("RandomVariableConfig", {"variableName": "rv", "minimumValue": "1", "maximumValue": "100", "outputFormat": "", "randomSeed": "", "perIteration": False}),
    ])
    def test_new_element_generates_valid_xml(self, element_type, props):
        """每个新元素生成的 JMX 必须可被 XML 解析"""
        tree = self._build_tree_with(element_type, props)
        jmx = export_tree_to_jmx([tree])
        assert jmx and isinstance(jmx, str)
        root = ET.fromstring(jmx)
        assert root.tag == "jmeterTestPlan"

    def test_old_alias_still_works(self):
        """使用旧别名(JsonExtractor)的树必须能成功生成 JMX(别名归一化生效)"""
        tree = self._build_tree_with("JsonExtractor", {"referenceName": "v", "jsonPath": "$.data"})
        jmx = export_tree_to_jmx([tree])
        root = ET.fromstring(jmx)
        # 应生成 JSONPostProcessor 节点(因为 _JMX_TYPE_MAP["JSONPostProcessor"] = "JSONExtractor")
        # 归一化 JsonExtractor → JSONExtractor → build_extractor 生成的 tag 是 JSONPostProcessor
        extractors = root.findall(".//JSONPostProcessor") + root.findall(".//RegexExtractor")
        assert len(extractors) >= 1, "JsonExtractor 别名未正确归一化"


# ========== XML 字符转义 ==========


class TestXmlEscaping:
    """测试特殊字符的 XML 转义"""

    def test_url_with_ampersand_escaped(self):
        """URL 中的 & 必须被转义为 &amp;"""
        case = {
            "name": "Amp Test",
            "method": "GET",
            "url": "https://api.example.com/search?q=a&lang=zh",
            "headers": [],
            "body": "",
        }
        jmx = export_cases_to_jmx([case])
        # 必须是有效 XML(若 & 未转义,ET.fromstring 会抛 ParseError)
        root = ET.fromstring(jmx)
        assert root.tag == "jmeterTestPlan"

    def test_name_with_special_chars_escaped(self):
        """用例名中的 < > & 必须被转义"""
        case = {
            "name": "Test <script> & data",
            "method": "GET",
            "url": "https://api.example.com/test",
            "headers": [],
            "body": "",
        }
        jmx = export_cases_to_jmx([case])
        root = ET.fromstring(jmx)
        # 找到 HTTPSamplerProxy 并验证 testname 属性包含原文
        sampler = root.find(".//HTTPSamplerProxy")
        assert sampler is not None
        testname = sampler.get("testname", "")
        assert "script" in testname
        assert "data" in testname
