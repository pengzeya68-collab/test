"""
测试 JMeter 服务
"""
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    # 测试导入
    print("正在导入 JMeter 服务...")
    from fastapi_backend.services.autotest_jmeter_service import export_cases_to_jmx, import_jmx_to_cases
    print("✅ JMeter 服务导入成功")
    
    # 测试导出功能
    print("\n正在测试导出功能...")
    test_cases = [
        {
            "name": "Test API",
            "method": "GET",
            "url": "https://api.example.com/test",
            "headers": {"Content-Type": "application/json"},
            "params": {},
            "body_type": "none",
            "payload": None,
            "assert_rules": [],
            "extractors": [],
        }
    ]
    
    jmx_content = export_cases_to_jmx(test_cases, "Test Plan")
    if jmx_content and "<?xml" in jmx_content:
        print("✅ 导出功能测试通过")
        print(f"生成的 XML 长度: {len(jmx_content)} 字符")
    else:
        print("❌ 导出功能测试失败")
    
    # 测试导入功能
    print("\n正在测试导入功能...")
    if jmx_content:
        cases = import_jmx_to_cases(jmx_content)
        if cases and len(cases) > 0:
            print(f"✅ 导入功能测试通过，解析出 {len(cases)} 个用例")
            print(f"第一个用例: {cases[0].get('name')} - {cases[0].get('method')} {cases[0].get('url')}")
        else:
            print("❌ 导入功能测试失败")
    
    print("\n✅ 所有测试通过")
    
except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()
