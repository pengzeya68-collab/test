"""
从 allure-results 中提取接口用例信息
"""
import json
import os
from collections import defaultdict

allure_dir = r"c:/Users/lenovo/Desktop/TestMasterProject/auto_test_platform/allure-results/scenario_1"

# 存储提取的接口用例信息
api_cases = {}  # {api_case_id: info}
scenarios = {}  # {scenario_id: {name, steps: []}}

for filename in os.listdir(allure_dir):
    if filename.endswith('.json'):
        filepath = os.path.join(allure_dir, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 提取场景信息
        scenario_id = data.get('scenario_id')
        if scenario_id and scenario_id not in scenarios:
            scenarios[scenario_id] = {
                'name': data.get('name'),
                'steps': []
            }

        # 提取步骤中的接口信息
        for step in data.get('steps', []):
            api_case_id = step.get('api_case_id')
            if api_case_id and api_case_id not in api_cases:
                api_cases[api_case_id] = {
                    'id': api_case_id,
                    'name': step.get('api_case_name'),
                    'method': step.get('method'),
                    'url': step.get('url'),
                    'response_status_code': step.get('status_code'),
                }

            if scenario_id:
                scenarios[scenario_id]['steps'].append({
                    'api_case_id': api_case_id,
                    'name': step.get('api_case_name'),
                    'method': step.get('method'),
                    'url': step.get('url'),
                })

print("=" * 60)
print("从 allure-results 提取的接口用例信息")
print("=" * 60)

print(f"\n发现 {len(api_cases)} 个唯一接口用例:\n")
for case_id in sorted(api_cases.keys()):
    case = api_cases[case_id]
    print(f"ID: {case_id}")
    print(f"  名称: {case['name']}")
    print(f"  方法: {case['method']}")
    print(f"  URL: {case['url']}")
    print()

print(f"\n发现 {len(scenarios)} 个场景:\n")
for scenario_id, scenario in sorted(scenarios.items()):
    print(f"场景 ID: {scenario_id}, 名称: {scenario['name']}")
    print(f"  包含 {len(scenario['steps'])} 个步骤:")
    for i, step in enumerate(scenario['steps']):
        print(f"    {i+1}. [{step['method']}] {step['name']} (case_id={step['api_case_id']})")
    print()