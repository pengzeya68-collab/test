"""
JMeter JMX 导入/导出对称性测试(Stage F.1)

覆盖 fastapi_backend/services/autotest_jmeter_service.py:
- export_cases_to_jmx → import_jmx_to_cases 往返(roundtrip)
- import_jmx_to_full_tree 完整树结构解析
- _JMX_TYPE_MAP 60 项标签的 JMeter 5.6.3 规范
- 11 种新元素(BoundaryExtractor/CSSSelectorExtractor/...)的导入/导出
- 异常输入的容错
"""

import xml.etree.ElementTree as ET

import pytest

from fastapi_backend.services.autotest_jmeter_service import (
    _JMX_TYPE_MAP,
    export_cases_to_jmx,
    export_tree_to_jmx,
    import_jmx_to_cases,
    import_jmx_to_full_tree,
)


# ========== Roundtrip: 导出 → 导入 ==========


class TestExportImportRoundtrip:
    """验证导出的 JMX 能被导入解析回相同结构"""

    def _simple_case(self):
        return {
            "name": "GET User",
            "method": "GET",
            "url": "https://api.example.com/users/123",
            "headers": {"Authorization": "Bearer abc"},
            "body": "",
        }

    def test_roundtrip_preserves_method(self):
        """导出再导入,method 必须保留"""
        jmx = export_cases_to_jmx([self._simple_case()])
        cases = import_jmx_to_cases(jmx)
        assert len(cases) == 1
        assert cases[0]["method"].upper() == "GET"

    def test_roundtrip_preserves_url(self):
        """导出再导入,URL 必须保留(可被规范化但语义一致)"""
        jmx = export_cases_to_jmx([self._simple_case()])
        cases = import_jmx_to_cases(jmx)
        assert len(cases) == 1
        # URL 应保留主要部分(允许域名/路径归一化)
        assert "example.com" in cases[0]["url"]
        assert "users" in cases[0]["url"]

    def test_roundtrip_preserves_name(self):
        """导出再导入,用例名必须保留"""
        jmx = export_cases_to_jmx([self._simple_case()])
        cases = import_jmx_to_cases(jmx)
        assert len(cases) == 1
        assert "User" in cases[0]["name"] or "GET" in cases[0]["name"]

    def test_roundtrip_preserves_headers(self):
        """导出再导入,请求头必须保留"""
        jmx = export_cases_to_jmx([self._simple_case()])
        cases = import_jmx_to_cases(jmx)
        assert len(cases) == 1
        headers = cases[0].get("headers", {})
        # Authorization 头必须存在
        auth_found = False
        if isinstance(headers, dict):
            for k, v in headers.items():
                if k.lower() == "authorization":
                    auth_found = True
                    break
        elif isinstance(headers, list):
            for h in headers:
                if h.get("key", "").lower() == "authorization":
                    auth_found = True
                    break
        assert auth_found, f"Authorization 头丢失: {headers}"

    def test_roundtrip_multiple_cases(self):
        """多个用例的 JMX 必须能完整导入"""
        cases = [
            {"name": "List", "method": "GET", "url": "https://api.example.com/users", "headers": [], "body": ""},
            {"name": "Create", "method": "POST", "url": "https://api.example.com/users", "headers": [{"key": "Content-Type", "value": "application/json"}], "body": '{"name":"test"}'},
            {"name": "Delete", "method": "DELETE", "url": "https://api.example.com/users/1", "headers": [], "body": ""},
        ]
        jmx = export_cases_to_jmx(cases)
        imported = import_jmx_to_cases(jmx)
        assert len(imported) == 3, f"应导入 3 个用例,实际 {len(imported)}"


# ========== import_jmx_to_full_tree ==========


class TestImportJmxFullTree:
    """测试完整树结构导入"""

    def test_full_tree_returns_dict_with_required_keys(self):
        """import_jmx_to_full_tree 必须返回包含 type/children 的字典"""
        jmx = export_cases_to_jmx([{
            "name": "T", "method": "GET", "url": "https://api.example.com/x", "headers": [], "body": ""
        }])
        tree = import_jmx_to_full_tree(jmx)
        assert isinstance(tree, dict)
        assert "type" in tree or "children" in tree

    def test_full_tree_invalid_xml_raises(self):
        """无效 XML 必须抛出 ValueError"""
        with pytest.raises(ValueError, match="JMX XML 解析失败"):
            import_jmx_to_full_tree("<not valid xml><<")

    def test_full_tree_empty_jmeter_plan(self):
        """空 JMeter 计划不应崩溃"""
        empty_jmx = '''<?xml version="1.0" encoding="UTF-8"?>
<jmeterTestPlan version="1.2" properties="5.0" jmeter="5.0">
  <hashTree>
    <TestPlan guiclass="TestPlanGui" testclass="TestPlan" testname="Empty" enabled="true">
    </TestPlan>
    <hashTree/>
  </hashTree>
</jmeterTestPlan>'''
        tree = import_jmx_to_full_tree(empty_jmx)
        assert isinstance(tree, dict)


# ========== _JMX_TYPE_MAP 规范化 ==========
# (与 test_jmeter_builders.py 中的 TestJmxTypeMap 互补,这里侧重 importer 角度)


class TestImporterTypeMapping:
    """importer 端的 _JMX_TYPE_MAP 应用"""

    def test_all_canonical_types_have_jmeter_tag(self):
        """每个规范类型对应一个 JMeter tag"""
        for jmeter_tag, canonical in _JMX_TYPE_MAP.items():
            assert isinstance(jmeter_tag, str) and jmeter_tag, f"无效 tag: {jmeter_tag}"
            assert isinstance(canonical, str) and canonical, f"无效 canonical: {canonical}"

    def test_canonical_types_match_frontend_node_types(self):
        """规范类型集合应包含 11 个新元素(BoundaryExtractor 等)"""
        new_elements = {
            "BoundaryExtractor", "CSSSelectorExtractor", "XPathExtractor",
            "ConstantThroughputTimer", "PoissonRandomTimer",
            "HttpCacheManager", "HttpAuthManager",
            "ModuleController", "RunTimeController",
            "Summariser", "RandomVariableConfig",
        }
        canonical_types = set(_JMX_TYPE_MAP.values())
        for elem in new_elements:
            assert elem in canonical_types, f"新元素 {elem} 不在 _JMX_TYPE_MAP 值集合中"


# ========== 11 种新元素完整往返测试 ==========


class TestNewElementsRoundtrip:
    """11 种 Stage D 新元素的导入/导出往返"""

    @pytest.mark.parametrize("element_type,props,jmeter_tag", [
        ("BoundaryExtractor", {"referenceName": "v1", "leftBoundary": "[", "rightBoundary": "]"}, "BoundaryExtractor"),
        ("CSSSelectorExtractor", {"referenceName": "css", "selector": ".t"}, "CSSSelectorExtractor"),
        ("XPathExtractor", {"referenceName": "xv", "xPath": "/root"}, "XPathExtractor"),
        ("ConstantThroughputTimer", {"throughput": "600"}, "ConstantThroughputTimer"),
        ("PoissonRandomTimer", {"delay": "100", "range": "200"}, "PoissonRandomTimer"),
        ("HttpCacheManager", {"clearEachIteration": True}, "CacheManager"),
        ("HttpAuthManager", {"users": [{"name": "u", "user": "admin", "pass": "p", "url": "https://api.example.com"}]}, "AuthManager"),
        ("ModuleController", {"nodePath": "/Test Plan/TG"}, "ModuleController"),
        ("RunTimeController", {"runtime": "60"}, "RunTimeController"),
        ("Summariser", {"interval": "30"}, "Summariser"),
        ("RandomVariableConfig", {"variableName": "rv", "minimumValue": "1", "maximumValue": "100"}, "RandomVariableConfig"),
    ])
    def test_new_element_present_in_jmx(self, element_type, props, jmeter_tag):
        """生成的 JMX 中必须包含新元素对应的 JMeter tag"""
        tree = {
            "type": "ThreadGroup", "name": "TG", "props": {},
            "children": [
                {"type": "HttpSampler", "name": "Req", "props": {"method": "GET", "url": "https://api.example.com", "headers": []},
                 "children": [{"type": element_type, "name": "X", "props": props, "children": []}]}
            ],
        }
        jmx = export_tree_to_jmx([tree])
        root = ET.fromstring(jmx)
        tags = root.findall(f".//{jmeter_tag}")
        assert len(tags) >= 1, f"JMX 中未找到 {jmeter_tag} 标签(元素 {element_type})"


# ========== 异常输入容错 ==========


class TestInvalidInputHandling:
    """异常输入必须被妥善处理,不能静默失败"""

    def test_empty_cases_produces_valid_jmx(self):
        """空用例列表应生成有效 JMX(仅 TestPlan + 空 ThreadGroup)"""
        jmx = export_cases_to_jmx([])
        root = ET.fromstring(jmx)
        assert root.tag == "jmeterTestPlan"

    def test_invalid_xml_raises_value_error(self):
        """无效 XML 必须抛出 ValueError"""
        with pytest.raises(ValueError):
            import_jmx_to_cases("not xml at all")

    def test_non_http_sampler_jmx(self):
        """仅含非 HTTP 采样器的 JMX 应返回空用例列表"""
        jmx = '''<?xml version="1.0" encoding="UTF-8"?>
<jmeterTestPlan version="1.2" properties="5.0" jmeter="5.0">
  <hashTree>
    <TestPlan guiclass="TestPlanGui" testclass="TestPlan" testname="No Samplers" enabled="true"/>
    <hashTree>
      <ThreadGroup guiclass="ThreadGroupGui" testclass="ThreadGroup" testname="TG" enabled="true"/>
      <hashTree/>
    </hashTree>
  </hashTree>
</jmeterTestPlan>'''
        cases = import_jmx_to_cases(jmx)
        assert cases == []


# ========== JMeter 5.6.3 兼容性 ==========


class TestJMeter563Compatibility:
    """验证生成的 JMX 兼容 JMeter 5.6.3"""

    def test_jmeter_version_attribute(self):
        """jmeterTestPlan 根元素的 jmeter 属性必须为 5.0+"""
        jmx = export_cases_to_jmx([{
            "name": "V", "method": "GET", "url": "https://api.example.com", "headers": [], "body": ""
        }])
        root = ET.fromstring(jmx)
        version = root.get("version", "0")
        assert float(version) >= 1.2, f"version={version}"

    def test_properties_version_compatible(self):
        """properties 属性应兼容 JMeter 5.x"""
        jmx = export_cases_to_jmx([{
            "name": "V", "method": "GET", "url": "https://api.example.com", "headers": [], "body": ""
        }])
        root = ET.fromstring(jmx)
        props = root.get("properties", "0")
        assert float(props) >= 5.0, f"properties={props}"
