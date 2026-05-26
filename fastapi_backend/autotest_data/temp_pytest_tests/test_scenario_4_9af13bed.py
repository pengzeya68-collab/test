
"""
场景测试自动生成文件
Scenario: BrowserScenario01
Scenario ID: 4
History ID: 9af13bed
Total Steps: 0
"""
import pytest
import sys
import allure
import json
import time

@pytest.fixture(scope="session", autouse=True)
def write_allure_environment(request):
    import sys
    from pathlib import Path
    allure_dir = request.config.getoption("--alluredir")
    if allure_dir:
        env_file = Path(allure_dir) / "environment.properties"
        with open(env_file, "w", encoding="utf-8") as f:
            f.write("Platform=TestMaster_AutoTest\n")
            f.write("Python_Version=" + sys.version.split()[0] + "\n")
            f.write("Scenario_ID=4\n")
            f.write("Scenario_Name=BrowserScenario01\n")
            f.write("History_ID='9af13bed'\n")
            f.write("Total_Steps=0\n")
    yield

@allure.suite("BrowserScenario01")
@allure.feature("BrowserScenario01")
class TestScenario4:
    """场景: BrowserScenario01 (0个步骤)"""


