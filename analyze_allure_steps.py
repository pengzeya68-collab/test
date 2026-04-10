"""
详细分析 allure-results 中的请求信息
"""
import json
import os

allure_dir = r"c:/Users/lenovo/Desktop/TestMasterProject/auto_test_platform/allure-results/scenario_1"

# 找一个包含完整信息的文件
for filename in sorted(os.listdir(allure_dir))[:5]:
    if filename.endswith('.json'):
        filepath = os.path.join(allure_dir, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        print(f"\n{'='*60}")
        print(f"文件: {filename}")
        print(f"{'='*60}")
        print(f"场景ID: {data.get('scenario_id')}")
        print(f"场景名称: {data.get('name')}")
        print(f"执行状态: {data.get('status')}")

        for i, step in enumerate(data.get('steps', [])[:3]):  # 只看前3步
            print(f"\n--- 步骤 {i+1} ---")
            print(f"  api_case_id: {step.get('api_case_id')}")
            print(f"  api_case_name: {step.get('api_case_name')}")
            print(f"  method: {step.get('method')}")
            print(f"  url: {step.get('url')}")
            print(f"  request: {json.dumps(step.get('request'), indent=2, ensure_ascii=False) if step.get('request') else 'None'}")
            print(f"  response: {json.dumps(step.get('response'), indent=2, ensure_ascii=False) if step.get('response') else 'None'}")