import sys

HEADER = '''"""
TestMaster 教程内容填充脚本 P5
路径17: AI测试与智能化 + 路径18: 测试架构设计与质量度量
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from fastapi_backend.core.config import settings
from fastapi_backend.models.models import Base, LessonSection, LearningPath

DATABASE_URL = settings.DATABASE_URL
engine = create_async_engine(DATABASE_URL, echo=False)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

LESSON_CONTENT_5 = {}
'''

def esc(s):
    return s.replace('\\', '\\\\').replace('"', '\\"')

def make_section(title, sort_order, knowledge_point, time_estimate, content):
    lines = []
    lines.append("    {")
    lines.append(f'        "title": "{title}",')
    lines.append(f'        "sort_order": {sort_order},')
    lines.append(f'        "knowledge_point": "{knowledge_point}",')
    lines.append(f'        "time_estimate": {time_estimate},')
    safe_content = content.replace('"""', '\\"""')
    lines.append(f'        "content": """{safe_content}"""')
    lines.append("    },")
    return "\n".join(lines)

def make_path_sections(path_name, sections):
    lines = []
    lines.append("# " + "=" * 60)
    lines.append(f"# 路径: {path_name}")
    lines.append("# " + "=" * 60)
    lines.append(f'LESSON_CONTENT_5["{path_name}"] = [')
    for s in sections:
        lines.append(make_section(**s))
    lines.append("]")
    lines.append("")
    return "\n".join(lines)

# ============================================================
# Path 17: AI测试与智能化 (7 sections)
# ============================================================

path17_sections = []

# Section 1
path17_sections.append({
    "title": "第1节：AI在软件测试中的全景应用(2024趋势)",
    "sort_order": 1, "knowledge_point": "AI测试概述", "time_estimate": 25,
    "content": """## AI测试的时代背景与行业趋势

2024年，人工智能正在以前所未有的速度重塑软件测试领域。Gartner预测，到2027年超过60%的企业级应用测试将引入AI辅助能力。AI不再是测试的"选修课"，而是测试工程师的核心竞争力之一。

AI测试的本质是**利用机器学习、自然语言处理、计算机视觉等技术来增强、自动化或替代传统测试流程中的重复性、分析性和创造性工作**。它不是要取代测试人员，而是让测试人员从繁琐的手工操作中解放出来，将精力集中在更高价值的策略制定和探索性测试上。

## AI在测试生命周期中的全景图谱

```
+---------------------------------------------------------------------------+
|                       AI在软件测试中的全景应用                              |
+------------------+-----------------------+---------------------------------+
|   需求分析阶段    |     测试设计阶段       |       测试执行阶段               |
|                  |                       |                                 |
| . NLP需求分析     | . AI辅助用例生成       | . 自愈自动化测试                  |
| . 需求质量评估    | . 组合测试优化         | . 智能回归策略                    |
| . 用户故事拆分    | . 测试数据合成         | . 视觉回归测试(AI对比)            |
| . 风险评估建议    | . 优先级智能排序       | . 异常行为检测                    |
+------------------+-----------------------+---------------------------------+
|   缺陷分析阶段    |     质量度量阶段       |       运维监控阶段               |
|                  |                       |                                 |
| . 缺陷自动分类    | . ML缺陷预测          | . 日志异常检测                    |
| . 相似缺陷去重    | . 质量风险评分        | . 根因自动定位                    |
| . 根因智能推断    | . 发布质量门禁        | . 智能告警降噪                    |
| . Bug定位建议     | . 测试覆盖率分析      | . 生产环境健康度预测               |
+------------------+-----------------------+---------------------------------+
```

## 2024年AI测试的核心技术趋势

| 趋势 | 技术说明 | 成熟度 | 典型工具 |
|------|----------|--------|----------|
| LLM驱动的测试生成 | 利用GPT-4/Claude等大模型生成测试代码和用例 | ★★★★☆ | Copilot, CodiumAI |
| 视觉AI回归测试 | 深度学习驱动的UI视觉对比 | ★★★★★ | Applitools, Percy |
| 自愈测试自动化 | AI自动修复因UI变更导致的脚本失效 | ★★★★☆ | Testim, Mabl |
| 智能测试数据管理 | GAN生成逼真测试数据 | ★★★☆☆ | Tonic.ai, Mostly AI |
| 预测性质量分析 | 基于历史数据的缺陷预测 | ★★★☆☆ | Sealights, Launchable |
| AI辅助安全测试 | 智能模糊测试与漏洞探测 | ★★★☆☆ | Bright Security |
| 自然语言测试编写 | 用自然语言描述测试，AI转化为可执行脚本 | ★★★☆☆ | Cucumber AI, TestGPT |

## AI测试落地的三个阶段

**第一阶段：辅助增强（当前主流阶段）**
AI作为测试工程师的"副驾驶"，提供智能建议、自动补全、代码审查等辅助功能。测试工程师仍然主导测试设计和关键决策。

**第二阶段：人机协作（逐步推广中）**
AI深度参与测试用例生成、执行分析和缺陷诊断。测试人员专注于策略制定、探索性测试和质量风险评估，形成"人机互补"的协作模式。

**第三阶段：自主测试（未来愿景）**
AI具备自主理解需求、自动设计测试策略、自动执行并自我修复的能力。测试人员转变为"AI测试训练师"和"质量架构师"。

## AI测试的成功衡量指标

| 指标 | 定义 | 目标值参考 |
|------|------|-----------|
| 测试覆盖率提升率 | 引入AI后代码/需求覆盖率的提升比例 | >=15% |
| 缺陷逃逸率降低 | 生产环境缺陷占比的下降幅度 | >=30% |
| 测试脚本维护成本降低 | 脚本维护时间/资源的减少比例 | >=40% |
| 回归测试时间缩短 | 相同覆盖度下回归测试执行时间缩减 | >=50% |
| 误报率 | AI告警中被确认为非缺陷的比例 | <=10% |

## 本节小结

AI测试不是一蹴而就的变革，而是渐进式的演进。对于测试团队而言，重要的是从现在开始建立AI测试的思维框架，选择适合自身业务场景的AI工具，在实战中积累经验。接下来的章节将逐一深入探讨AI测试的各个细分领域。"""
})

# Section 2: 视觉回归测试
path17_sections.append({
    "title": "第2节：视觉回归测试(Visual Testing/Applitools/Percy/Playwright)",
    "sort_order": 2, "knowledge_point": "视觉回归测试", "time_estimate": 30,
    "content": """## 视觉回归测试是什么

视觉回归测试（Visual Regression Testing）是通过对比页面截图或DOM渲染结果的像素级差异，来检测UI意外变更的一种自动化测试方法。传统的功能测试只能验证"功能是否可用"，而视觉回归测试能回答"界面是否好看、布局是否正确"的问题。

核心流程：**基线截图 → 新版本截图 → 像素对比 → 差异标注 → 人工审核 → 更新基线**。

## 传统视觉测试的痛点

| 痛点 | 描述 | 影响 |
|------|------|------|
| 手动UI检查耗时 | 每个版本需要逐页检查UI展现 | 回归效率低下 |
| CSS变更的蝴蝶效应 | 修改一个CSS可能导致多页面布局错乱 | 问题遗漏风险高 |
| 跨浏览器兼容性 | 同一页面在不同浏览器中展现不一致 | 用户体验差 |
| 响应式布局问题 | 不同分辨率下布局错位 | 移动端故障率高 |
| 主题/换肤回归 | 多主题切换时的视觉质量难以保障 | 品牌形象受损 |

## 主流视觉回归测试工具对比

| 维度 | Applitools Eyes | Percy (BrowserStack) | Playwright 内置 | BackstopJS |
|------|----------------|----------------------|-----------------|------------|
| 核心技术 | AI驱动的视觉AI引擎 | 像素级+抗锯齿对比 | 像素级截图对比 | 基于Puppeteer的截图对比 |
| 对比方式 | 布局感知+内容感知 | DOM快照+像素对比 | 逐像素RGB对比 | 配置化截图对比 |
| 云端执行 | 支持 | 支持 | 不支持(本地) | 不支持(本地) |
| AI去噪能力 | 极强 | 中等 | 较弱 | 较弱 |
| 跨浏览器/设备 | 海量组合 | 丰富组合 | 单浏览器 | 单浏览器 |
| CI/CD集成 | 深度集成 | 深度集成 | 需自建 | 需自建 |
| 价格 | 企业级收费 | 免费额度+付费 | 免费开源 | 免费开源 |
| 适用场景 | 大型企业/品牌敏感 | 中小团队/快速迭代 | 开发者自测 | 本地开发验证 |

## Playwright视觉回归测试实战

```python
from playwright.sync_api import sync_playwright, expect

def test_homepage_visual_regression():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.goto("https://example.com")

        # 全页面截图对比 (推荐阈值0.1-0.5%)
        expect(page).to_have_screenshot(
            "homepage_baseline.png", max_diff_pixel_ratio=0.01)

        # 特定元素截图对比
        header = page.locator(".main-header")
        expect(header).to_have_screenshot("header_baseline.png")

        # 全页面截图（非断言的灵活性方式）
        page.screenshot(path="screenshots/fullpage.png", full_page=True)
        browser.close()

def test_responsive_layouts():
    # 多分辨率下的视觉一致性
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        devices = [
            {"name": "mobile", "width": 375, "height": 812},
            {"name": "tablet", "width": 768, "height": 1024},
            {"name": "desktop", "width": 1440, "height": 900},
        ]
        for device in devices:
            page.set_viewport_size(
                {"width": device["width"], "height": device["height"]})
            page.goto("https://example.com")
            expect(page).to_have_screenshot(
                f"homepage_{device['name']}.png", max_diff_pixel_ratio=0.02)
        browser.close()
```

## Applitools实战：AI驱动的智能视觉对比

Applitools的核心优势在于其Visual AI引擎，它不像传统工具做像素级对比，而是模拟人眼的视觉感知：

```python
from applitools.selenium import Eyes, Target
from selenium import webdriver

def test_with_applitools_ai():
    driver = webdriver.Chrome()
    eyes = Eyes()
    eyes.api_key = "YOUR_API_KEY"
    try:
        eyes.open(driver, "MyApp", "Homepage Visual Test")
        driver.get("https://example.com")
        # AI对比：布局感知，忽略抗锯齿、像素偏移等非人为差异
        eyes.check("Homepage", Target.window().fully().layout())
        # 特定区域对比：只关注核心内容区
        eyes.check("Content Area",
                    Target.region_by_css(".main-content").layout())
        # 严格对比模式（品牌logo）
        eyes.check("Logo", Target.region_by_css(".logo").strict())
        eyes.close_async()
    finally:
        driver.quit()
        eyes.abort_async()
```

## 视觉回归测试的最佳实践清单

- [ ] 在稳定版本（如发布候选版）上建立视觉基线，而非开发分支
- [ ] 不同区域设置不同的对比灵敏度；Logo/品牌区域严格对比，大文本区域宽松对比
- [ ] 广告、推荐列表、时间戳等动态区域使用ignore或floating区域策略
- [ ] 根据产品流量分析选择Top设备分辨率组合
- [ ] 优先对独立组件做视觉测试，减少整页截图的不稳定性
- [ ] 将视觉测试作为PR合入门禁，在每次部署前自动执行
- [ ] 建立人工审核机制，对AI标记的差异进行确认（接受/拒绝）
- [ ] 当产品UI发生有意变更时，及时更新基线避免累积大量假阳性

## 视觉测试中的常见挑战与解决方案

| 挑战 | 表现 | 解决方案 |
|------|------|----------|
| 动画干扰 | GIF/动画导致截图时机不一致 | 冻结动画、使用animation:none |
| 字体渲染差异 | 不同OS字体渲染导致差异 | 使用Web字体保证一致性 |
| 异步数据加载 | 截图时数据未加载完成 | 设置明确的等待条件 |
| 系统弹窗遮挡 | Cookie提示/订阅弹窗阻挡 | 脚本化关闭弹窗 |
| 视频自动播放 | 封面帧不一致 | 统一替换为占位图 |

## 本节小结

视觉回归测试已成为现代UI自动化测试体系的重要组成部分。Playwright适合开发者的快速自测，Percy适合中小团队的CI/CD集成，Applitools适合对品牌一致性要求极高的大型企业。无论选择哪种工具，建立完善的视觉测试策略和审查流程才是成功的关键。"""
})

# Section 3: AI辅助测试用例生成
path17_sections.append({
    "title": "第3节：智能化测试用例生成(AI辅助设计/组合测试)",
    "sort_order": 3, "knowledge_point": "AI用例生成", "time_estimate": 30,
    "content": """## AI辅助测试用例生成的概述

测试用例设计是软件测试中最核心也最耗时的工作之一。传统设计依赖测试工程师的经验和对需求的深入理解，但过程往往存在遗漏、偏见和效率瓶颈。AI辅助测试用例生成利用大语言模型(LLM)、约束求解和机器学习技术，从需求文档、用户故事或代码中自动或半自动地推导出测试用例。

AI测试用例生成的三种主要模式：

| 模式 | 输入源 | 技术手段 | 输出 | 典型场景 |
|------|--------|----------|------|----------|
| 需求驱动的生成 | PRD/用户故事/AC | LLM语义理解+NLP | 功能性测试用例 | 敏捷Sprint测试准备 |
| 代码驱动的生成 | 源代码/API定义 | 静态分析+符号执行 | 单元测试/API测试 | TDD/代码补全 |
| 模型驱动的生成 | 状态机/流程图 | 组合测试/路径覆盖 | 场景/E2E测试 | 复杂业务流程验证 |

## 基于LLM的需求到用例的转化实战

```python
# LLM从用户故事生成测试用例的核心思路
import openai

def generate_test_cases_from_requirement(feature_desc, acceptance_criteria):
    prompt = f'''
    你是一名资深的软件测试工程师。请根据以下需求生成详细的测试用例。

    【功能描述】
    {feature_desc}

    【验收标准(AC)】
    {acceptance_criteria}

    请生成测试用例（至少5条）：
    1. 包含正向场景、边界场景、异常场景
    2. 每条包含：用例ID、标题、前置条件、测试步骤、预期结果、优先级
    3. 对于异常场景，要明确错误码或错误提示
    '''
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3, max_tokens=2000
    )
    return response.choices[0].message.content

# 使用示例
feature = "用户登录功能，支持用户名/密码登录和短信验证码登录"
ac_list = \"""
AC1: 用户输入正确的用户名和密码后跳转到首页
AC2: 连续5次输入错误密码后账号锁定30分钟
AC3: 短信验证码有效期为5分钟
AC4: 支持记住密码功能（有效期7天）
\"""
test_cases = generate_test_cases_from_requirement(feature, ac_list)
```

## 组合测试（Combinatorial Testing）

组合测试是解决"参数组合爆炸"问题的科学方法。当一个功能有N个参数，每个参数有多个取值时，遍历所有组合（全因子测试）在现实中不可行。

**核心原理：两因子组合覆盖（Pairwise Testing）**
Pairwise测试确保任意两个参数的所有取值组合至少被覆盖一次。研究表明，约70%的软件缺陷由单参数或双参数交互触发。

```
参数组合爆炸 vs Pairwise优化效果：
- 参数: 5个, 每个3个取值 → 全组合: 3^5=243 → Pairwise: 约9-12条
- 参数: 10个, 每个3个取值 → 全组合: 3^10=59,049 → Pairwise: 约15-20条
- 参数: 20个, 每个2个取值 → 全组合: 2^20=1,048,576 → Pairwise: 约10-15条
```

**Python AllPairs实现示例：**

```python
from allpairspy import AllPairs

parameters = [
    ["Windows", "macOS", "Linux"],
    ["Chrome", "Firefox", "Safari", "Edge"],
    ["CN", "EN", "JP"],
    ["Admin", "Editor", "Viewer"],
    ["HTTP", "HTTPS"],
]

print(f"全组合数量: {3 * 4 * 3 * 3 * 2} = 216")
print(f"\\nPairwise优化后的测试组合:\\n")

pairwise_count = 0
for i, combo in enumerate(AllPairs(parameters)):
    pairwise_count += 1
    print(f"  {i+1:>2}. " + " | ".join(combo))

print(f"\\nPairwise组合: {pairwise_count} "
      f"(优化率: {100 - pairwise_count/216*100:.1f}%)")
```

## AI驱动的智能测试数据生成

```python
from faker import Faker
import random

class SmartTestDataGenerator:
    def __init__(self):
        self.fake = Faker("zh_CN")

    def generate_user_registration_data(self, scenario="normal"):
        scenarios = {
            "normal": {
                "username": self.fake.user_name()[:20],
                "email": self.fake.email(),
                "password": "Test@123456",
                "phone": "13800138000",
                "age": random.randint(18, 65),
            },
            "boundary_min_age": {
                "username": self.fake.user_name()[:20],
                "email": self.fake.email(),
                "password": "Test@123456",
                "phone": "13800138001",
                "age": 0,  # 边界：最小年龄
            },
            "xss_attack": {
                "username": "<script>alert('xss')</script>",
                "email": self.fake.email(),
                "password": "Test@123456",
                "phone": "13800138002",
                "age": 25,
            },
            "sql_injection": {
                "username": "test' OR '1'='1",
                "email": self.fake.email(),
                "password": "Test@123456",
                "phone": "13800138003",
                "age": 25,
            },
            "unicode_special": {
                "username": "测试用户🎉😀",
                "email": f"test{self.fake.random_int()}@test.cn",
                "password": "Test@123456",
                "phone": "13800138004",
                "age": 25,
            },
        }
        return scenarios.get(scenario, scenarios["normal"])

# 使用示例
gen = SmartTestDataGenerator()
for s in ["normal", "boundary_min_age", "xss_attack", "unicode_special"]:
    data = gen.generate_user_registration_data(s)
    print(f"\\n[{s}] {data}")
```

## AI辅助测试用例评审检查清单

- [ ] 覆盖完整性：AI生成的用例是否覆盖所有AC？是否存在遗漏？
- [ ] 逻辑正确性：测试步骤与预期结果的因果关系是否正确？
- [ ] 前置条件合理性：前置条件是否与系统当前状态兼容？
- [ ] 数据真实性：测试数据的边界值、异常值是否合理？
- [ ] 无矛盾性：多条用例之间是否存在逻辑矛盾？
- [ ] 可执行性：用例在现有测试框架中是否可以直接执行？
- [ ] 优先级合理性：AI分配的优先级是否符合业务风险评估？
- [ ] 去LLM幻觉：检查AI是否编造了系统中不存在的功能或字段

## 本节小结

AI辅助测试用例生成不是要替代测试工程师的思考，而是提供"快速草稿"能力。组合测试（尤其是Pairwise）是测试工程师应掌握的数学方法，能在保证高缺陷检出率的前提下将用例数量从指数级降到对数级。将AI生成广度与工程师审查深度相结合，才能真正实现"又快又好"的测试设计。"""
})

# Section 4: ML缺陷预测
path17_sections.append({
    "title": "第4节：基于机器学习的缺陷预测与风险评估",
    "sort_order": 4, "knowledge_point": "ML缺陷预测", "time_estimate": 30,
    "content": """## 缺陷预测的定义与价值

基于机器学习的缺陷预测（Defect Prediction）是通过分析历史项目数据（代码变更、缺陷记录、测试结果等），训练ML模型预测当前版本中哪些模块/文件/提交最可能包含缺陷。核心价值：将有限的测试资源聚焦在最高风险区域，实现风险导向的精准测试。

缺陷预测基于统计学规律——复杂度高的代码、频繁变更的模块、历史缺陷密集的区域，往往也是新缺陷的高发地带。

## 缺陷预测的数据维度与特征工程

```
+--------------------------------------------------------------+
|                      缺陷预测的特征体系                        |
+---------------+---------------+---------------+--------------+
|   代码特征     |   过程特征     |   历史特征     |   组织特征    |
+---------------+---------------+---------------+--------------+
| . 圈复杂度     | . 变更频率     | . 历史缺陷密度  | . 开发者数量   |
| . 代码行数     | . 提交次数     | . 缺陷修复率   | . 开发者经验   |
| . 嵌套深度     | . 变更散度     | . 回归缺陷比率 | . 代码所有权   |
| . 耦合度       | . 修改的代码行 | . 平均存活时间 | . 地理分布     |
| . 注释率       | . 评审轮次     | . 严重等级分布 | . 团队变更率   |
| . 方法数/类    | . 代码Churn    | . 引入阶段     |               |
+---------------+---------------+---------------+--------------+
```

关键指标解读：
- **代码Churn（搅动度）** = 近期新增行数 + 删除行数。Churn越高越不稳定
- **变更散度** = 变更涉及的文件数量。散度越大越容易引入集成缺陷
- **代码所有权** = 主力开发者占比。多人共同维护的文件更容易出Bug

## 缺陷预测模型构建实战

```python
# 基于scikit-learn的缺陷预测模型
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, roc_auc_score

def build_defect_prediction_model():
    np.random.seed(42)
    n_samples = 1000

    data = pd.DataFrame({
        "cyclomatic_complexity": np.random.randint(1, 50, n_samples),
        "lines_of_code": np.random.randint(10, 5000, n_samples),
        "nesting_depth": np.random.randint(0, 10, n_samples),
        "change_frequency": np.random.randint(0, 30, n_samples),
        "num_developers": np.random.randint(1, 8, n_samples),
        "code_review_rounds": np.random.randint(0, 5, n_samples),
        "historical_bug_density": np.random.uniform(0, 0.2, n_samples),
        "code_churn": np.random.randint(0, 500, n_samples),
        "coupling_degree": np.random.uniform(0, 1, n_samples),
    })

    # 标签：基于规则模拟缺陷标记
    def label_defect(row):
        score = (
            row["cyclomatic_complexity"] / 50 * 0.20 +
            row["code_churn"] / 500 * 0.25 +
            row["historical_bug_density"] / 0.2 * 0.25 +
            row["change_frequency"] / 30 * 0.15 +
            row["coupling_degree"] * 0.10 +
            row["nesting_depth"] / 10 * 0.05
        )
        return 1 if score > 0.5 else 0

    data["has_defect"] = data.apply(label_defect, axis=1)

    X = data.drop("has_defect", axis=1)
    y = data["has_defect"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y)

    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)

    model = RandomForestClassifier(
        n_estimators=100, max_depth=10, random_state=42,
        class_weight="balanced")
    model.fit(X_train_s, y_train)

    y_pred = model.predict(X_test_s)
    y_proba = model.predict_proba(X_test_s)[:, 1]

    print(f"ROC-AUC: {roc_auc_score(y_test, y_proba):.3f}")
    print(f"\\n{classification_report(y_test, y_pred)}")

    # 特征重要性
    importance = pd.DataFrame({
        "feature": X.columns,
        "importance": model.feature_importances_
    }).sort_values("importance", ascending=False)
    print("\\n特征重要性排名:")
    for _, row in importance.iterrows():
        print(f"  {row['feature']:<25} {row['importance']:.3f}")

    return model, scaler

model, scaler = build_defect_prediction_model()
```

## 风险评估矩阵

| 风险等级 | 判定条件 | 测试策略 | 资源分配建议 |
|----------|----------|----------|-------------|
| 极高风险 | 预测概率>=0.7 + 历史缺陷密度高 | 全量测试+代码审查+压测 | 分配40%资源 |
| 高风险 | 预测概率0.4-0.7 或 代码Churn高 | 重点功能回归+边界值测试 | 分配30%资源 |
| 中风险 | 预测概率0.15-0.4 | 冒烟测试+关键路径回归 | 分配20%资源 |
| 低风险 | 预测概率<0.15 且 变更次数少 | 基本冒烟测试 | 分配10%资源 |

## 缺陷预测落地的关键成功因素

1. **数据质量是关键**：Garbage In, Garbage Out。确保历史缺陷数据记录的完整性和准确性
2. **模型需要持续训练**：缺陷模式随项目阶段和团队成熟度变化，需要定期重新训练
3. **不要迷信模型**：ML预测是概率，不是确定性结论。始终保留人工判断的干预空间
4. **从简单模型开始**：先从逻辑回归、决策树等可解释模型起步，再逐步尝试复杂模型
5. **与开发流程集成**：将预测结果集成到CI/CD流水线中，作为自动化的风险门禁

## 本节小结

基于机器学习的缺陷预测是现代软件质量保障的"风险雷达"——它不是替代测试，而是为测试决策提供数据驱动的洞察。一个好的缺陷预测系统能帮助团队在正确的时间、正确的模块上投入正确的测试资源，最终实现"用更少的测试发现更多的缺陷"。"""
})

# Section 5: NLP测试应用
path17_sections.append({
    "title": "第5节：NLP在测试需求分析与测试设计中的应用",
    "sort_order": 5, "knowledge_point": "NLP测试应用", "time_estimate": 25,
    "content": """## NLP在软件测试中的应用全景

自然语言处理（NLP）在软件测试中的应用是AI测试的一个重要分支。软件需求文档、用户故事、缺陷报告、测试用例等大量测试工件以自然语言形式存在，NLP技术可帮助自动理解和结构化这些文本数据，实现测试流程的智能化。

## NLP在需求分析中的应用

### 1. 需求质量自动评估

需求文档是测试的起点，但需求质量往往参差不齐。NLP可以帮助自动评估需求文档质量。

```python
import re

class RequirementQualityAnalyzer:
    # 好需求的特征词（SMART原则）
    SMART_INDICATORS = [
        "必须", "应当", "最多", "最少", "不超过", "至少",
        "当...时", "如果...则", "百分比", "秒", "分钟", "并发", "TPS"
    ]
    # 坏需求的特征（模糊表达）
    VAGUE_INDICATORS = [
        "尽可能", "大概", "差不多", "可能", "也许",
        "快", "友好", "易用", "美观", "流畅", "应该", "最好", "尽量"
    ]

    def analyze(self, text: str) -> dict:
        result = {
            "has_quantification": bool(re.search(r'\\d+', text)),
            "has_condition": bool(re.search(r'(当|如果|若|一旦)', text)),
            "has_expected": bool(re.search(
                r'(则|那么|系统应|显示|返回|跳转)', text)),
            "vague_words": [w for w in self.VAGUE_INDICATORS if w in text],
            "quality_score": 5.0
        }
        result["quality_score"] += result["has_quantification"] * 2
        result["quality_score"] += result["has_condition"] * 1.5
        result["quality_score"] += result["has_expected"] * 1.5
        result["quality_score"] -= min(len(result["vague_words"]), 3) * 1.5
        result["quality_score"] = max(0, min(10, result["quality_score"]))
        return result

# 使用示例
analyzer = RequirementQualityAnalyzer()
good = "当用户连续5次输入错误密码时，系统应在30分钟内锁定该账户"
bad = "用户登录失败后应该提示一下，尽量友好一些"
print(f"好需求评分: {analyzer.analyze(good)['quality_score']:.1f}")
print(f"差需求评分: {analyzer.analyze(bad)['quality_score']:.1f}")
```

### 2. 需求与测试用例的追溯性分析

| NLP任务 | 技术手段 | 应用场景 |
|---------|----------|----------|
| 语义相似度计算 | Word2Vec/BERT/Sentence-BERT | 建立需求到用例的追溯关系 |
| 命名实体识别(NER) | BiLSTM-CRF/BERT-NER | 提取需求中的角色、操作、对象 |
| 文本分类 | FastText/BERT分类 | 需求类型识别（功能/性能/安全） |
| 关系抽取 | 依存句法分析/开放IE | 提取业务规则和约束条件 |
| 文本摘要 | BART/T5/Pegasus | 长需求的自动摘要生成 |

## NLP驱动的测试设计

用户故事到测试场景的转化流水线：

```
用户故事（自然语言）
    │
    ▼
[分词+词性标注]      → 识别主语（角色）、谓语（操作）、宾语（对象）
    │
    ▼
[依存句法分析]        → 识别条件从句、约束条件
    │
    ▼
[语义角色标注]        → 提取施事者、受事者、时间、地点
    │
    ▼
[模式匹配+模板填充]   → 生成测试场景骨架
    │
    ▼
测试场景（结构化JSON） → Given-When-Then格式
```

```python
# NLP驱动的BDD测试场景生成
class NLToBDDGenerator:
    def __init__(self):
        self.patterns = [
            (r'(.+?)登录\\s*(.+)',
             "用户已注册且未登录",
             "用户输入{1}的凭证并点击登录",
             "系统应{2}"),
            (r'(.+?)搜索\\s*(.+)',
             "用户已登录系统",
             "用户在搜索框输入{1}",
             "系统应{2}"),
        ]

    def generate(self, requirement: str) -> str:
        for pattern, given, when, then in self.patterns:
            match = re.match(pattern, requirement)
            if match:
                g = match.groups()
                return (
                    f"Scenario: {requirement}\\n"
                    f"  Given {given.format(*g)}\\n"
                    f"  When {when.format(*g)}\\n"
                    f"  Then {then.format(*g)}\\n"
                )
        return f"Scenario: {requirement}\\n  # 无法自动匹配，请手动设计"

gen = NLToBDDGenerator()
print(gen.generate("用户使用手机号+验证码登录成功后跳转到首页"))
```

## NLP辅助缺陷分析

- **缺陷自动分类**：根据Bug描述文本自动打标签（功能缺陷/性能/安全/UI）
- **相似缺陷检测**：计算Bug文本的语义相似度，自动检测重复Bug
- **缺陷严重等级推荐**：基于关键词（崩溃/数据丢失/阻塞）推荐严重等级
- **自动分配建议**：基于历史修复数据，推荐最合适的修复者

## 本节小结

NLP技术让测试团队能更高效地处理大规模的自然语言测试工件。从需求质量的自动评估到测试场景的智能生成，再到缺陷的自动分析和分类，NLP正在成为测试工程师的"第二大脑"。需要注意的是，NLP工具是辅助手段，测试工程师仍需结合业务上下文做出最终判断。"""
})

# Section 6: 自愈自动化测试
path17_sections.append({
    "title": "第6节：自愈自动化测试(Self-Healing)原理与实践",
    "sort_order": 6, "knowledge_point": "自愈自动化测试", "time_estimate": 30,
    "content": """## 自愈自动化测试的概念

自愈自动化测试（Self-Healing Automation）是指自动化测试框架在UI元素定位器（XPath、CSS选择器、ID等）失效时，自动检测失效原因并自动修复定位策略，使测试脚本无需人工干预即可继续执行。

据统计，中等规模的UI自动化测试套件（200-500条用例）每轮迭代约有15%-30%的用例因UI变更而失败，其中大部分是元素定位失效导致的假阳性。

## 元素定位失效的常见原因

| 失效类型 | 原因 | 示例 |
|----------|------|------|
| ID变更 | 前端重构时修改了HTML ID | id="login-btn" → id="login-button" |
| Class变更 | CSS重构或框架升级 | class="btn-primary" → class="MuiButton-root" |
| 结构变更 | DOM结构重新组织 | 从div移到section内 |
| 框架替换 | 前端框架迁移 | jQuery → React → Vue |
| A/B测试 | 动态渲染的不同版本UI | 实验组和对照组结构不同 |
| 动态属性 | 每次渲染生成随机ID | id="comp-abc123" → id="comp-def456" |

## 自愈策略的技术架构

```
+-----------------------------------------------------------------+
|                      自愈自动化测试架构                            |
|                                                                 |
|  +----------+    +----------+    +--------------+                |
|  | 测试执行  |--->| 元素查找  |--->| 定位器选择器  |                |
|  | 引擎      |    | 引擎      |    | (多重策略)    |                |
|  +----------+    +----------+    +--------------+                |
|                         |              |                          |
|                         v              v                          |
|                   +----------+   +--------------+                |
|                   | 失败检测  |-->| 失败类型分类  |                |
|                   +----------+   +--------------+                |
|                                        |                          |
|                          +-------------+-------------+           |
|                          v             v             v           |
|                    +----------+ +----------+ +----------+       |
|                    | 属性分析  | | 结构分析  | | 视觉分析  |       |
|                    | (智能匹配) | | (上下文)  | | (截图/OCR)|       |
|                    +----------+ +----------+ +----------+       |
|                          |             |             |           |
|                          +-------------+-------------+           |
|                                        v                          |
|                                  +----------+                    |
|                                  | 候选定位器|                    |
|                                  | 评分与排序|                    |
|                                  +----------+                    |
|                                        |                          |
|                                        v                          |
|                                  +----------+                    |
|                                  | 定位器更新|                    |
|                                  | 与持久化  |                    |
|                                  +----------+                    |
+-----------------------------------------------------------------+
```

## 多定位器降级策略实战

```python
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

class SelfHealingElementFinder:
    def __init__(self, driver):
        self.driver = driver
        self.healing_cache = {}

    def find_element_healable(self, name, primary, fallbacks=None):
        all_locators = [("primary", primary)]
        if fallbacks:
            all_locators.extend(fallbacks)

        for strategy_name, (by, value) in all_locators:
            try:
                element = self.driver.find_element(by, value)
                if strategy_name != "primary":
                    print(f"[Self-Healing] '{name}': "
                          f"{primary} -> ({by}, {value})")
                    self.healing_cache[name] = (by, value)
                return element
            except NoSuchElementException:
                continue

        raise NoSuchElementException(
            f"元素 '{name}' 所有定位策略均失效")

# 使用示例
# finder = SelfHealingElementFinder(driver)
# login_locators = [
#     ("fallback_text", (By.XPATH, "//button[contains(text(),'登录')]")),
#     ("fallback_type", (By.CSS_SELECTOR, "button[type='submit']")),
# ]
# el = finder.find_element_healable(
#     "登录按钮", (By.ID, "login-btn"), login_locators)
```

## 四种核心技术

**策略1：多定位器降级** — 预定义多个备用定位器，按优先级尝试
**策略2：AI属性相似度匹配** — 利用文本内容、邻近标签、ARIA属性、祖先结构计算相似度找到最佳候选
**策略3：上下文感知定位** — 利用周围"锚点"（相邻Label、表格列头、卡片标题）重建定位
**策略4：视觉AI辅助定位** — 当DOM定位全部失效时使用截图+OCR/模板匹配定位

## 自愈测试成熟度模型

| 等级 | 能力 | 描述 |
|------|------|------|
| L1: 基础 | 手动维护 | 测试人员手工修复所有定位器失效 |
| L2: 感知 | 失败告警 | 自动检测定位器失效并告警，但需人工修复 |
| L3: 降级 | 多策略降级 | 自动尝试多个预定义备用定位器 |
| L4: 学习 | AI辅助修复 | 基于AI的相似度分析，自动推荐候选定位器 |
| L5: 自适应 | 完全自愈 | 自动检测、修复、验证、持久化 |

## 实施自愈测试的注意事项

- [ ] 记录所有自愈事件，建立自愈日志便于事后审查
- [ ] 对于高风险的自动修复（涉及支付/权限），增加人工确认环节
- [ ] 不盲目信任AI修复，自愈后需验证元素确实正确执行了预期操作
- [ ] 平衡降级策略与性能，过多备用定位器会增加查找时间
- [ ] 产品大版本UI重构时，清空历史缓存避免误导

## 本节小结

自愈自动化测试是解决UI测试脚本维护成本过高问题的关键突破口。它不是一个"银弹"，但在UI变动频繁的项目中能显著降低维护ROI。建议从L3（多策略降级）开始实践，在有数据基础后再升级到L4/L5的AI辅助模式。"""
})

# Section 7: LLM测试生成
path17_sections.append({
    "title": "第7节：大语言模型(LLM)在测试代码生成中的应用",
    "sort_order": 7, "knowledge_point": "LLM测试生成", "time_estimate": 30,
    "content": """## LLM如何改变测试代码编写

2024年，大语言模型在测试领域的应用已从"尝鲜"走向"生产级应用"。LLM能在秒级时间生成测试工程师需要数十分钟甚至数小时才能完成的测试代码。

LLM在测试代码生成中的核心优势：
- 速度极快：数秒内生成完整测试类
- 模式识别强：能模仿项目已有的测试代码风格
- 覆盖面广：自动生成边界值/异常/空值等容易被人工遗漏的场景
- 多语言/多框架支持：Python/pytest、Java/JUnit、JavaScript/Jest、Go/testing等

## LLM测试代码生成的实际能力矩阵

| 任务类型 | LLM完成度 | 人工介入需求 | 典型场景 |
|----------|-----------|-------------|----------|
| 单元测试生成 | ★★★★★ | 低 | 纯逻辑函数、工具类 |
| 接口测试生成 | ★★★★☆ | 低-中 | REST API参数校验、响应断言 |
| Mock/Stub编写 | ★★★★☆ | 低 | 外部依赖的模拟数据生成 |
| UI自动化脚本 | ★★★☆☆ | 中 | 元素定位、页面对象模式 |
| 性能测试脚本 | ★★★☆☆ | 中 | JMeter/Locust脚本 |
| 复杂业务场景 | ★★☆☆☆ | 高 | 多步骤业务流程、状态机 |
| 安全渗透测试 | ★★☆☆☆ | 高 | 需要专业安全知识 |

## 实战：LLM生成pytest测试代码

```python
# LLM驱动的测试代码生成
def llm_generate_test(api_spec: dict) -> str:
    endpoint = api_spec.get("endpoint", "")
    method = api_spec.get("method", "GET")
    params = api_spec.get("params", [])
    tests = []

    # 正常场景
    tests.append(f'''
@pytest.mark.smoke
def test_{endpoint.replace("/", "_").strip("_")}_success(api_client):
    # 验证正常请求返回200
    response = api_client.{method.lower()}("{endpoint}")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
''')

    # 参数校验
    for param in params:
        if param.get("required"):
            pname = param["name"]
            tests.append(f'''
def test_{endpoint.replace("/", "_").strip("_")}_missing_{pname}(
        api_client):
    # 验证缺少必要参数时返回400
    response = api_client.{method.lower()}(
        "{endpoint}", params={{{"{pname}": None}}})
    assert response.status_code == 400
''')

    # 边界值参数化
    tests.append(f'''
@pytest.mark.parametrize("page,size,expected", [
    (0, 10, 200), (1, 0, 200), (1, 1000, 200),
    (-1, 10, 400), (1, -1, 400),
])
def test_{endpoint.replace("/", "_").strip("_")}_boundary(
        api_client, page, size, expected):
    # 验证分页参数边界值处理
    response = api_client.{method.lower()}(
        "{endpoint}", params={{"page": page, "size": size}})
    assert response.status_code == expected
''')

    return "\\n".join(tests)
```

## LLM测试生成的最佳Prompt设计

好的Prompt是LLM生成高质量测试代码的前提。推荐模板结构：

```
你是一名资深软件测试工程师。

【上下文信息】
- 编程语言：{language}
- 测试框架：{framework}
- 项目测试代码风格参考：{sample_test_code}

【任务】
根据以下代码/接口规格，生成完整的测试代码。

【被测试代码】
{source_code_or_api_spec}

【要求】
1. 遵循项目已有的测试代码风格
2. 覆盖：正常路径、边界值、异常输入、依赖失败
3. 每个测试方法使用清晰的命名和注释
4. 使用参数化测试减少重复代码
5. Mock所有外部依赖
6. 避免实现细节的过度耦合

请直接输出可执行的测试代码，不要输出解释性文字。
```

## LLM测试生成的陷阱与应对

| 陷阱 | 表现 | 应对策略 |
|------|------|----------|
| 幻觉 | 生成不存在的API/方法 | 人工审查所有LLM生成的API调用 |
| 过度Mock | Mock掉所有依赖导致测试无价值 | 明确区分"应Mock"和"应真实调用" |
| 复制粘贴错误 | 批量生成时参数错乱 | 逐条Review参数值和预期结果 |
| 缺少边界值 | LLM倾向生成Happy Path用例 | Prompt中显式要求边界值覆盖 |
| 语言不匹配 | 生成Python但项目用Java | Prompt中明确指定语言和框架 |
| 断言不充分 | 只检查状态码 | Prompt中提供完整Response Schema |
| 忽略异步逻辑 | async代码生成同步测试 | Prompt中指明代码的异步特性 |

## LLM测试代码质量评估维度

```
+---------------------------------------------------+
|            LLM生成测试代码质量评估维度               |
+----------------+----------------------------------+
| 语法正确性      | 代码能否直接编译/解释执行？        |
| 逻辑正确性      | 测试逻辑是否正确？断言是否有意义？  |
| 覆盖充分性      | 是否覆盖正/反向/边界/异常场景？     |
| 风格一致性      | 是否符合项目已有的测试代码规范？    |
| 独立性          | 测试间是否互相依赖？数据是否隔离？   |
| 可维护性        | 测试代码是否简洁、清晰、易于修改？  |
| 真实性          | Mock数据是否真实合理？              |
+----------------+----------------------------------+
```

## 人机协作的工作流

```
Step 1: 测试工程师提供源代码/API规格 + 高质量Prompt
    │
Step 2: LLM生成测试代码初稿（通常5-30秒）
    │
Step 3: 测试工程师审查：
    ├── 语法检查（直接运行看能否编译/执行）
    ├── 逻辑审查（断言是否正确、场景是否覆盖）
    ├── Mock审查（Mock是否合理）
    └── 风格审查（命名、注释、结构是否一致）
    │
Step 4: 工程师补充LLM遗漏的场景（特别是业务特有逻辑）
    │
Step 5: 合并到代码库，通过CI/CD验证
    │
Step 6: 持续优化Prompt模板，提高后续生成质量
```

## 本节小结

LLM已成为测试工程师效率提升的"超级引擎"。它能将编写测试代码的时间从小时级压缩到分钟级，让测试人员将更多精力投入到测试策略设计和探索性测试上。最佳实践是"LLM生成初稿 + 人工审查优化 + 持续积累Prompt模板"的人机协作模式。"""
})

# ============================================================
# Path 18: 测试架构设计与质量度量 (8 sections, abbreviated)
# ============================================================

path18_content = []

path18_content.append({
    "title": "第1节：测试架构师角色、能力模型与成长路径",
    "sort_order": 1, "knowledge_point": "测试架构师概述", "time_estimate": 25,
    "content": """## 测试架构师的定义与定位

测试架构师（Test Architect）是测试团队中级别最高的技术岗位，负责制定测试策略、设计测试架构、选型测试工具链、建立质量标准。他不是"高级测试工程师的升级版"，而是一个角色定位完全不同的岗位——测试工程师关注"如何测好一个功能"，测试架构师关注"如何构建一个能持续产出高质量软件的测试体系"。

## 测试架构师的能力模型（T型人才）

```
+--------------------------------------------------------------------+
|                    测试架构师能力模型（T型人才）                      |
|                                                                    |
|  +--------------------------------------------------------------+  |
|  |                    业务理解与战略视野                         |  |
|  |   行业知识 | 商业模式理解 | 产品规划 | 技术趋势判断            |  |
|  +--------------------------------------------------------------+  |
|  +--------------------------------------------------------------+  |
|  |         深度专业能力（T型的竖线——核心竞争力）                |  |
|  |                                                              |  |
|  |  测试架构设计 | 自动化框架设计 | 性能工程 | 质量度量体系       |  |
|  |  测试策略制定 | CI/CD流水线设计 | 安全测试架构 | 测试数据管理   |  |
|  +--------------------------------------------------------------+  |
|  +--------------------------------------------------------------+  |
|  |         广度横向能力（T型的横线——支撑能力）                   |  |
|  |                                                              |  |
|  |  编程能力 | DevOps | 分布式系统 | 数据库 | 网络协议 | AI/ML    |  |
|  |  沟通协作 | 技术写作 | 项目管理 | 团队领导力 | 培训赋能       |  |
|  +--------------------------------------------------------------+  |
+--------------------------------------------------------------------+
```

## 测试架构师 vs 高级测试工程师

| 维度 | 高级测试工程师 | 测试架构师 |
|------|---------------|-----------|
| 关注范围 | 单个/多个功能模块 | 整个产品/组织的测试体系 |
| 时间视野 | 当前迭代/版本 | 未来3-12个月的技术规划 |
| 技术深度 | 特定技术领域深入 | 多技术领域广且深 |
| 影响力 | 影响团队内的测试质量 | 影响整个组织的测试文化和技术方向 |
| 产出 | 测试用例、缺陷报告、自动化脚本 | 测试策略、架构设计、技术规范、平台 |
| 决策层级 | 执行决策（如何测） | 战略决策（测什么、用什么测、何时测） |
| 沟通对象 | 开发团队、产品经理 | CTO、架构委员会、技术总监 |

## 测试架构师的成长路径

```
+-------------+    +-------------+    +-------------+    +-------------+
| 初级测试     |--->| 中级测试     |--->| 高级测试     |--->|  测试架构师  |
| (0-2年)     |    | (2-5年)     |    | (5-8年)     |    | (8年+)      |
+-------------+    +-------------+    +-------------+    +-------------+
| . 执行用例   |    | . 独立设计   |    | . 模块策略   |    | . 整体架构   |
| . 提交Bug    |    | . 自动化脚本 |    | . 框架主导   |    | . 技术选型   |
| . 学习工具   |    | . 性能入门   |    | . 团队指导   |    | . 组织影响   |
| . 了解业务   |    | . 安全入门   |    | . 跨团队协作 |    | . 技术布道   |
+-------------+    +-------------+    +-------------+    +-------------+
```

## 各阶段的能力积累重点

**初级→中级（0-2年→2-5年）**：从"执行测试"到"设计测试"，掌握至少一门编程语言，熟练使用2-3种测试框架，理解被测系统架构。

**中级→高级（2-5年→5-8年）**：从"测试模块"到"主导产品质量"，深入自动化框架架构设计，掌握性能和安全的专项测试技能。

**高级→架构师（5-8年→8年+）**：从"技术深度"拓展到"技术广度+业务理解+战略视野"，具备从0到1搭建测试体系的能力，做出数据支撑的技术选型决策。

## 测试架构师的技术知识图谱

- [ ] 测试方法论：测试金字塔、敏捷测试、分层测试、风险导向测试
- [ ] 自动化框架：数据驱动、关键字驱动、BDD、页面对象模型
- [ ] 编程语言：至少精通1门（Python/Java），熟悉2-3门
- [ ] CI/CD：Jenkins/GitLab CI/GitHub Actions，流水线即代码
- [ ] 容器技术：Docker/Kubernetes基础的测试环境管理
- [ ] 测试平台：测试管理平台、自动化执行平台、测试数据平台
- [ ] 性能测试：JMeter/Locust/K6，性能调优基础
- [ ] 安全测试：OWASP Top 10，SAST/DAST工具链
- [ ] 测试数据：数据脱敏、数据生成、数据子集化
- [ ] 质量度量：覆盖率、缺陷密度、缺陷逃逸率、MTTR/MTBF
- [ ] 系统设计：微服务架构、消息队列、缓存、数据库分库分表

## 本节小结

测试架构师不是一个靠年资就能晋升的岗位——需要刻意构建T型能力模型。成长路径没有捷径，但可以通过"主动承担技术难题→主导测试体系建设→输出技术影响力"的路径加速成长。"""
})

path18_content.append({
    "title": "第2节：可测试性设计(DFT)与测试架构模式",
    "sort_order": 2, "knowledge_point": "可测试性设计", "time_estimate": 30,
    "content": """## 可测试性设计（DFT）的概念

可测试性设计（Design for Testability, DFT）的核心思想：在系统设计阶段就充分考虑测试的便利性，使系统天然具备易于测试的特性。

可测试性好的系统具备：
- **可控性**：可方便地将系统置于特定状态以测试特定场景
- **可观察性**：可方便地观察系统内部状态和输出
- **可隔离性**：可独立测试各个组件而不依赖完整系统环境

## 可测试性差的常见反模式

| 反模式 | 具体表现 | 对测试的影响 |
|--------|---------|-------------|
| 硬编码依赖 | new DatabaseConnection()直接写在业务代码中 | 无法Mock，必须连接真实数据库 |
| 上帝类 | 单个类承担过多职责（>500行） | 单元测试复杂，Mock成本高 |
| 全局状态 | 大量使用static变量/单例模式 | 测试间互相干扰，无法并行 |
| 私有方法复杂逻辑 | 关键业务逻辑藏在private方法中 | 只能间接覆盖 |
| 紧耦合 | 组件间强依赖，无法独立部署 | 集成环境搭建困难 |
| 时间/随机依赖 | 直接调用new Date()或Math.random() | 测试结果不可重复 |
| 缺乏接口抽象 | 直接依赖具体实现而非接口 | 无法替换为Mock/Stub |

## 可测试性设计核心原则

1. **依赖注入（DI）**：通过构造函数/方法参数注入依赖，而非内部创建
2. **接口隔离**：面向接口编程，每个接口职责单一且清晰
3. **显式状态**：避免隐式的全局状态，状态变更通过显式方法调用完成
4. **纯函数优先**：尽量写纯函数（相同输入→相同输出，无副作用）
5. **关注点分离**：业务逻辑与基础设施逻辑分离（如数据库访问与业务规则）
6. **配置外部化**：环境配置、开关、阈值等通过配置文件/环境变量注入
7. **时间抽象**：通过Clock/TimeProvider接口抽象时间获取
8. **日志结构化**：输出结构化日志而非自由文本，便于自动化验证

## 可测试性重构实战

```python
# ===== 重构前：不可测试的代码 =====
import datetime, random, requests

class OrderService_UnTestable:
    def create_order(self, user_id, product_id, quantity):
        # 问题1: 直接依赖datetime.now()
        if datetime.datetime.now().hour < 8:
            raise Exception("非营业时间")
        # 问题2: 硬编码数据库连接
        import pymysql
        conn = pymysql.connect(host="localhost", user="root", password="123456")
        # 问题3: 随机数导致结果不可重复
        order_id = f"ORD-{random.randint(1000, 9999)}"
        # 问题4: HTTP请求无法Mock
        inventory = requests.get(
            f"http://inventory-service/api/stock/{product_id}").json()
        # 问题5: print输出无法自动化验证
        print(f"订单创建成功: {order_id}")

# ===== 重构后：可测试的代码 =====
from abc import ABC, abstractmethod

class Clock(ABC):
    @abstractmethod
    def now(self) -> datetime.datetime: ...

class IDGenerator(ABC):
    @abstractmethod
    def generate(self, prefix: str, date: datetime.datetime) -> str: ...

class InventoryClient(ABC):
    @abstractmethod
    def check_stock(self, product_id: str) -> dict: ...

class OrderRepository(ABC):
    @abstractmethod
    def save(self, order: dict) -> str: ...

class OrderService_Testable:
    def __init__(self, clock: Clock, id_gen: IDGenerator,
                 inventory: InventoryClient, repo: OrderRepository):
        self._clock = clock
        self._id_gen = id_gen
        self._inventory = inventory
        self._repo = repo

    def create_order(self, user_id: str, product_id: str,
                     quantity: int) -> dict:
        now = self._clock.now()
        if now.hour < 8 or now.hour > 22:
            raise ValueError("非营业时间")
        stock = self._inventory.check_stock(product_id)
        if stock["available"] < quantity:
            raise ValueError("库存不足")
        order_id = self._id_gen.generate("ORD", now)
        order = {"order_id": order_id, "user_id": user_id,
                 "product_id": product_id, "quantity": quantity,
                 "created_at": now.isoformat()}
        self._repo.save(order)
        return order  # 返回结构化数据，便于自动化验证
```

## 测试架构模式

| 模式 | 描述 | 适用场景 | 优点 | 缺点 |
|------|------|----------|------|------|
| 测试金字塔 | 单元>集成>E2E三角形 | 通用分层测试 | 反馈快成本低 | 集成缺陷可能遗漏 |
| 测试蜂巢 | 强调集成测试权重 | 微服务架构 | 服务契约覆盖好 | 单元测试不足 |
| 测试钻石 | 平衡各层+专项测试 | 复杂系统 | 全方位覆盖 | 维护成本高 |
| 消费者驱动契约 | 消费者定义期望驱动 | 微服务交互 | 精准避免过度 | 需团队协作 |
| 测试夹具 | 预定义测试数据工厂 | 所有项目 | 数据复用 | 数据维护成本 |
| 页面对象(POM) | UI元素封装为对象 | UI自动化 | 降低UI变更影响 | 初始成本 |

## 可测试性评估检查清单

- [ ] 核心业务逻辑是否可以独立于框架（如Spring/Django）测试？
- [ ] 数据库/缓存/消息队列等外部依赖是否有明确的接口抽象？
- [ ] 时间相关逻辑是否通过Clock/TimeProvider注入？
- [ ] 随机数/ID生成是否有可替换的实现？
- [ ] 第三方API调用是否通过适配器模式隔离？
- [ ] 配置项是否外部化，能否在不同环境间切换？
- [ ] 是否避免在构造函数中执行副作用操作？
- [ ] 异步逻辑是否支持同步模式的可测试性？
- [ ] 是否支持测试数据隔离（每个测试独立的数据上下文）？

## 本节小结

可测试性是衡量软件架构质量的重要维度。一个好的测试架构师应在设计评审阶段就识别可测试性风险。记住："如果一个功能很难测试，那它很可能也很难维护、很难扩展"。可测试性设计的投资将在项目的整个生命周期中持续产生回报。"""
})

path18_content.append({
    "title": "第3节：微服务测试策略(服务间契约测试/端到端测试)",
    "sort_order": 3, "knowledge_point": "微服务测试", "time_estimate": 30,
    "content": """## 微服务测试的独特挑战

微服务架构将大型单体应用拆分为多个独立部署、独立演进的微服务，带来了部署灵活性和团队自治性，同时也给测试带来了前所未有的挑战。

| 挑战维度 | 单体架构 | 微服务架构 |
|----------|---------|-----------|
| 测试环境 | 一个应用，环境简单 | N个服务+中间件，环境复杂 |
| 集成测试 | 模块间调用，同步简单 | 服务间网络通信，异步复杂 |
| 数据一致性 | 单数据库事务 | 分布式事务/最终一致性 |
| 测试数据管理 | 单一数据库 | 跨多个独立数据库 |
| 依赖管理 | 编译时依赖 | 运行时依赖，服务可能随时更新 |
| 错误隔离 | 局部异常 | 级联故障风险 |

## 微服务测试策略全景

```
                        +--------------+
                        |  E2E测试      |
                        |   (少量)       |
                        +------+-------+
                               |
                  +------------+-----------+
                  |            |            |
          +-------v------+ +--v------+ +---v-------+
          | 契约测试       | |集成测试  | | 组件测试  |
          |(Consumer      | |(DB/Cache| |(独立部署   |
          | Driven)       | | /MQ)    | | 验证)     |
          +-------+------+ +--+------+ +---+-------+
                  |            |            |
                  +------------+------------+
                               |
                        +------v-------+
                        |  单元测试      |
                        |   (大量)       |
                        +--------------+
```

## 消费者驱动契约测试（Consumer-Driven Contract Testing）

契约测试是微服务测试中最具特色的测试类型。核心假设：每个服务消费者定义自己对提供者的期望，测试确保Provider满足所有Consumer的期望。

### Pact框架实战

```python
# 消费者端：定义对Provider的期望
from pact import Consumer, Provider

pact = Consumer("UserService").has_pact_with(
    Provider("OrderService"), host_name="localhost", port=1234)
pact.start_service()

# UserService期望OrderService的行为
expected_response = {
    "orders": [{
        "order_id": "ORD-001", "status": "shipped",
        "total_amount": 299.00,
        "items": [{"product_id": "P001", "name": "iPhone 15", "quantity": 1}]
    }]
}

(pact
 .given("用户存在且有一个已发货订单")
 .upon_receiving("查询用户订单的请求")
 .with_request("GET", "/api/v1/orders")
 .with_query("user_id", "U12345")
 .will_respond_with(200, body=expected_response))

# 提供者端验证
from pact import Verifier
verifier = Verifier(provider="OrderService",
                     provider_base_url="http://localhost:8080")
success, logs = verifier.verify_pacts(
    "pacts/UserService-OrderService.json",
    provider_states_setup_url="http://localhost:8080/_pact/provider_states")
assert success, f"契约验证失败: {logs}"
```

## 契约测试的适用场景

| 场景 | 是否适合 | 原因 |
|------|---------|------|
| 同步REST API | 非常适合 | 请求-响应模式天然适合契约测试 |
| 异步消息队列 | 适合 | 可用Pact Message验证消息格式 |
| gRPC接口 | 适合 | Protocol Buffer天然跨语言 |
| GraphQL | 适合 | Schema即契约 |
| 第三方外部API | 不适合 | 无法控制第三方，用Mock即可 |
| 内部非关键服务 | 可选 | 投入产出比需评估 |

## 微服务E2E测试策略

E2E测试应采用关键路径导向策略：

- 高业务价值 + 高频率：必测（如支付流程、用户注册）
- 高业务价值 + 低频率：必测（如核心业务流程）
- 低业务价值 + 高频率：可选（如非核心API）
- 低业务价值 + 低频率：可选（如管理后台）

## 微服务测试数据管理策略

三种核心模式：

**数据工厂模式**：为每个测试场景预定义数据构建器 → 适用于服务级测试
**数据快照模式**：定期从生产环境脱敏导出数据集 → 适用于E2E测试
**数据生成模式**：使用Faker等工具动态生成 → 适用于单元测试

```python
class TestDataFactory:
    @staticmethod
    def create_user(role="normal", **overrides):
        defaults = {
            "user_id": f"test-user-{random.randint(10000, 99999)}",
            "username": f"testuser_{random.randint(1000, 9999)}",
            "email": f"test_{random.randint(1000, 9999)}@example.com",
            "role": role, "status": "active",
        }
        defaults.update(overrides)
        return defaults

    @staticmethod
    def create_order(user_id, status="pending", item_count=1, **overrides):
        items = [{"product_id": f"PROD-{random.randint(100, 999)}",
                  "product_name": f"商品-{i+1}",
                  "quantity": random.randint(1, 5),
                  "unit_price": round(random.uniform(10, 1000), 2)}
                 for i in range(item_count)]
        defaults = {
            "order_id": f"ORD-TEST-{random.randint(100000, 999999)}",
            "user_id": user_id, "status": status, "items": items,
        }
        defaults.update(overrides)
        return defaults
```

## 本节小结

微服务测试的核心难点在于服务间交互的测试——如何高效、可靠地验证服务间的契约。消费者驱动契约测试（如Pact）是解决这一问题的最佳实践。黄金法则：尽可能多使用单元测试和契约测试（反馈快成本低），谨慎选择E2E测试（只覆盖关键业务路径），永远不要让E2E测试成为CI/CD的瓶颈。"""
})

path18_content.append({
    "title": "第4节：分层测试体系与测试金字塔实践",
    "sort_order": 4, "knowledge_point": "分层测试体系", "time_estimate": 25,
    "content": """## 分层测试体系的核心理念

分层测试体系（Layered Testing Architecture）将测试按不同粒度和目的划分为多个层次，每层有明确的职责边界。其中最著名的是Mike Cohn的测试金字塔——回答了"应该写多少单元测试、集成测试、E2E测试？"

## 经典测试金字塔

```
                        /\\
                       /E2E\\         数量：少（5%-10%）
                      /------\\       反馈：慢（分钟-小时级）
                     / 集成    \\     成本：高
                    /----------\\     维护：复杂
                   /  UI组件    \\   稳定性：脆弱
                  /--------------\\
                 /    API测试      \\  数量：中（15%-25%）
                /------------------\\ 反馈：中（秒-分钟级）
               /      集成测试       \\ 成本：中
              /----------------------\\
             /        单元测试         \\ 数量：多（60%-70%）
            /--------------------------\\ 反馈：快（毫秒-秒级）
           /____________________________\\ 成本：低
```

**金字塔的核心法则：**
1. 越底层越多：单元测试应占60%-70%
2. 越上层越少：E2E只覆盖最重要场景，占5%-10%
3. 越底层越快：单元测试秒级完成，E2E分钟级
4. 越上层越脆弱：E2E易因UI变化、网络等非代码原因失败

## 反模式

**冰淇淋甜筒**：大量手动测试在上，极少单元测试在下——最常见的反模式
**沙漏型**：单元和E2E多但集成测试缺失——中间断层导致服务交互缺陷遗漏

## 各层测试的职责与策略

| 层次 | 测试目标 | 工具 | Mock策略 | 失败处理 |
|------|---------|------|---------|---------|
| 单元测试 | 函数/方法逻辑 | pytest/JUnit/Jest | Mock所有外部依赖 | 立即修复 |
| API测试 | 接口契约 | pytest+requests | Mock外部服务 | 合入前修复 |
| UI组件测试 | 渲染与交互 | Jest+Testing Library | Mock API | 合入前修复 |
| 集成测试 | 模块协作 | pytest+Testcontainers | 真实DB/MQ | Sprint内修复 |
| E2E测试 | 核心业务流程 | Playwright/Cypress | 真实部署 | 紧急修复或回滚 |

## CI/CD流水线中的分层执行策略

```
PR提交 -> 静态分析(秒级) -> 单元测试(秒级) -> 构建镜像(分钟级)
                                                  |
                              +-------------------+-------------------+
                              v                   v                   v
                          API测试             UI组件测试           契约测试
                         (分钟级)             (分钟级)             (分钟级)
                              |                   |                   |
                              +-------------------+-------------------+
                                                  v
                                    部署到staging环境
                                                  |
                              +-------------------+-------------------+
                              v                   v                   v
                          集成测试             性能测试             E2E测试
                         (分钟级)             (分钟级)            (分钟级)
                                                  |
                                                  v
                                             部署到生产
```

## 分层测试实战案例

```python
# 电商订单模块分层测试示例
# ==================== 单元测试（70%） ====================
class TestOrderCalculator:
    def test_calculate_subtotal_single_item(self):
        items = [{"unit_price": 100, "quantity": 3, "discount_rate": 0.1}]
        assert OrderCalculator.calculate_subtotal(items) == 270.0

    def test_empty_cart(self):
        assert OrderCalculator.calculate_subtotal([]) == 0.0

    @pytest.mark.parametrize("price,qty,discount,expected", [
        (100, 3, 0, 300), (100, 0, 0, 0),
        (100, 1, 0.5, 50), (0.01, 9999, 0, 99.99),
    ])
    def test_calculate_parametrized(self, price, qty, discount, expected):
        items = [{"unit_price": price, "quantity": qty,
                  "discount_rate": discount}]
        assert abs(OrderCalculator.calculate_subtotal(items) - expected) < 0.01

# ==================== API测试（20%） ====================
class TestOrderAPI:
    def test_create_order_success(self, api_client, db_session):
        payload = {"user_id": "U001",
                   "items": [{"product_id": "P001", "quantity": 1}]}
        res = api_client.post("/api/orders", json=payload)
        assert res.status_code == 201
        data = res.json()
        assert "order_id" in data

    def test_create_order_insufficient_stock(self, api_client):
        payload = {"user_id": "U001",
                   "items": [{"product_id": "P001", "quantity": 99999}]}
        res = api_client.post("/api/orders", json=payload)
        assert res.status_code == 409

# ==================== E2E测试（10%） ====================
class TestOrderE2E:
    def test_complete_order_flow(self, browser):
        page = browser.new_page()
        page.goto("https://shop.example.com/login")
        page.fill("#username", "testuser")
        page.fill("#password", "Test@123")
        page.click("button[type='submit']")
        # ... 加购、结算、支付、验证
        assert "支付成功" in page.locator(".success-message").inner_text()
```

## 分层测试的度量与优化

| 度量指标 | 健康阈值 |
|----------|---------|
| 测试分层比例 | 单元60-70%, 集成20-30%, E2E 5-10% |
| 各层执行时间 | 单元<30s, API<3min, E2E<15min |
| 各层稳定性 | 单元>=99%, API>=95%, E2E>=90% |
| 缺陷发现分布 | 单元>=60%, 集成>=25%, E2E>=10% |

## 本节小结

测试金字塔是指导测试投资分配的实践框架。核心洞察：将投资集中在反馈最快、成本最低的层次，用少量高价值的E2E作为"安全网"。如果体系呈现冰淇淋甜筒反模式，需要渐进迁而非一夜重构。"""
})

path18_content.append({
    "title": "第5节：软件质量度量模型(GQM/ISO 25010/DORA)",
    "sort_order": 5, "knowledge_point": "质量度量模型", "time_estimate": 30,
    "content": """## 软件质量度量的重要性

"如果你不能度量它，你就不能改进它。"质量度量能让主观的质量感受转变为客观数据，为决策提供事实依据。好的度量体系回答三个问题：质量水平如何？趋势变好还是变坏？应优先改进什么？

## GQM模型（Goal-Question-Metric）

GQM是Victor Basili提出的经典度量框架，采用自上而下的方法从目标推导度量指标。

```
概念层（Goal）：我们要达成什么目标？
  例：提高回归测试的效率和质量
       │
操作层（Question）：
  Q1: 回归是否充分覆盖关键功能？
  Q2: 回归执行效率是否持续提升？
  Q3: 回归缺陷逃逸是否下降？
       │
量化层（Metric）：
  M1: 回归覆盖率 = 覆盖需求数 / 总需求数
  M2: 回归执行时间 = 全量回归总耗时
  M3: 缺陷逃逸率 = 线上缺陷 / 总缺陷数
  M4: 自动化通过率 = 自动通过数 / 总自动化数
```

### GQM实战

```python
class RegressionTestMetrics:
    def __init__(self, data):
        self.data = data

    def measure(self) -> dict:
        return {
            "goal": "提高回归测试的效率和质量",
            "questions": [{
                "question": "回归是否充分覆盖关键功能？",
                "metrics": {
                    "coverage_rate": f"{self._coverage():.1f}%",
                    "critical_path_covered": f"{self._critical():.1f}%",
                }
            }, {
                "question": "回归缺陷逃逸是否下降？",
                "metrics": {
                    "defect_escape_rate":
                        f"{self._escape_rate():.2f}%",
                    "mttd_hours": self._mttd(),
                }
            }]
        }

    def _coverage(self):
        covered = sum(1 for r in self.data.requirements
                      if r.covered_by_regression)
        return covered / len(self.data.requirements) * 100

    def _escape_rate(self):
        return (self.data.prod_defects /
                max(self.data.total_defects, 1)) * 100

    def _mttd(self):
        return self.data.total_detection_time / max(self.data.prod_defects, 1)
```

## ISO 25010软件质量模型

ISO 25010将软件质量分为8个核心特性：

- **功能适用性**：功能完整性、正确性、适当性
- **性能效率**：时间行为、资源利用率、容量
- **兼容性**：共存性、互操作性
- **易用性**：可辨识性、易学性、可操作性、用户错误保护、界面美观、无障碍性
- **可靠性**：成熟性、可用性、容错性、可恢复性
- **信息安全性**：保密性、完整性、抗抵赖性、可追溯性、真实性
- **维护性**：模块化、可重用性、易分析性、易修改性、易测试性
- **可移植性**：适应性、易安装性、易替换性

## DORA度量模型

DORA是衡量DevOps效能的事实标准，包含四个关键指标：

| DORA指标 | 精英级 | 高级 | 中级 | 低级 |
|----------|--------|------|------|------|
| 部署频率(DF) | 按需(每天多次) | 每天-每周 | 每周-每月 | 每月以上 |
| 变更前置时间(LT) | <1小时 | 一天-一周 | 一周-一月 | 一月以上 |
| 变更失败率(CFR) | 0-15% | 0-15% | 0-15% | 16-30% |
| 恢复时间(MTTR) | <1小时 | <1天 | <1天 | 一天-一周 |

### DORA与测试的关联

| DORA指标 | 测试如何贡献 |
|----------|-------------|
| 部署频率 | 自动化覆盖率高→信心足→频繁部署 |
| 变更前置时间 | 测试左移→提早发现→减少返工 |
| 变更失败率 | 质量门禁→拦截缺陷→降低失败率 |
| 恢复时间 | 快速回归→快速验证修复→缩短MTTR |

## 质量度量仪表盘

```python
class QualityDashboard:
    def generate(self) -> dict:
        return {
            "delivery": {
                "deployment_frequency": "每日3次",
                "lead_time": "2.5小时",
                "change_failure_rate": "8.2%",
                "mttr": "35分钟",
            },
            "testing": {
                "unit_coverage": "78%",
                "e2e_count": 45,
                "automation_rate": "85%",
                "regression_duration": "12分钟",
            },
            "quality": {
                "defect_density": "0.8/KLOC",
                "defect_escape_rate": "5.2%",
                "critical_bugs_open": 2,
            },
            "reliability": {
                "uptime_sla": "99.95%",
                "p99_latency": "320ms",
                "error_rate": "0.15%",
            },
        }
```

## 度量指标选择原则

- [ ] 与业务目标对齐：每个指标回答一个业务关心的问题
- [ ] 可操作：指标反映的问题团队能采取行动改进
- [ ] 可比较：能在不同时间段、项目间比较
- [ ] 防作弊：指标不易被人为操纵
- [ ] 少而精：聚焦5-8个核心指标
- [ ] 趋势优于绝对值：关注变化趋势而非瞬间值

## 本节小结

质量度量是测试架构师的"仪表盘"。GQM帮你从目标出发建立度量体系，ISO 25010提供全面的质量维度框架，DORA将质量与交付效能关联。记住古德哈特定律："当一个度量成为目标时，它就不再是一个好的度量。" 度量的目的是洞察和改进，而非考核和排名。"""
})

path18_content.append({
    "title": "第6节：缺陷分析与根因分析(RCA)方法论",
    "sort_order": 6, "knowledge_point": "缺陷分析与RCA", "time_estimate": 30,
    "content": """## 缺陷分析的三个层次

```
第一层：缺陷管理（Bug Tracking）
  └── 记录、分配、跟踪、关闭 → 确保每个Bug得到妥善处理

第二层：缺陷分析（Defect Analysis）
  └── 分类、统计、趋势、模式识别 → 识别质量热点和趋势

第三层：根因分析（Root Cause Analysis）
  └── 追问为什么、识别根本原因 → 制定预防措施
```

## 缺陷分类法（ODC - Orthogonal Defect Classification）

IBM提出的正交缺陷分类法，从多个独立维度分类：

| 维度 | 分类选项 | 用途 |
|------|---------|------|
| 缺陷类型 | 功能缺失/赋值错误/接口错误/检查错误/时序错误/算法错误 | 识别薄弱环节 |
| 触发条件 | 评审发现/单元测试/集成测试/系统测试/客户发现 | 评估检出能力 |
| 影响范围 | 单个模块/跨模块/系统级/数据影响 | 评估影响广度 |
| 严重等级 | 致命/严重/一般/轻微/建议 | 优先级排序 |
| 缺陷来源 | 需求/设计/编码/测试环境/第三方 | 识别引入阶段 |
| 缺陷年龄 | 本版本引入/上版本遗留/多版本遗留 | 技术债务评估 |

## RCA的经典方法

### 5-Whys（五问法）

```
问题：用户支付时报错"系统繁忙，请稍后再试"

Why 1: 为什么报"系统繁忙"？
  → 支付网关返回了超时错误

Why 2: 为什么支付网关超时？
  → 请求在300ms内没有收到响应

Why 3: 为什么300ms内无响应？
  → 风控接口响应速度从50ms降到了800ms

Why 4: 为什么风控接口变慢？
  → 风控规则升级引入了复杂查询，未做索引优化

Why 5: 为什么没做索引优化就上线？
  → 【根因】风控系统变更评审未包含DBA参与，无性能回归测试

纠正措施：
1. 风控变更评审增加DBA参与
2. 建立第三方依赖性能监控
3. 支付网关增加熔断降级
```

### 鱼骨图（因果分析图）

```
                    鱼骨图：线上缺陷逃逸（缺陷逃逸率超8%）

  人员                 流程                  技术/工具
   │                    │                      │
   │ . 新人经验不足      │ . 缺少代码审查       │ . 环境不一致
   │ . 测试人员流失高    │ . 需求评审不充分     │ . 自动化覆盖不足
   │ . 开发者未自测      │ . 上线审批形同虚设   │ . 缺乏静态分析
   │                    │                      │
   └────────────────────┼──────────────────────┘
                        │
                     ◀  问题  ▶
                        │
   ┌────────────────────┼──────────────────────┐
   │                    │                      │
   │ . SDK频繁变更      │ . 用例未及时更新     │ . 时间压力大
   │ . 外部API不稳定    │ . 无回归用例基线     │ . 并行需求多
   │ . 依赖库有漏洞     │ . 历史用例失效率高   │ . KPI偏重速度
   │                    │                      │
 环境/依赖            测试资产                组织/文化
```

### 故障树分析（FTA）

```
                    TOP事件："系统支付功能不可用"
                              │
              +---------------+---------------+
              │               │               │
            AND门           AND门           OR门
              │               │               │
      +-------+--+      +----+-----+      +---+-----+
      |          |      |          |      |         |
  "支付网关  "数据库    "账户服务  "网络    "证书    "业务规则
   超时"    连接池耗尽"  不可用"    分区    过期"     配置错误"
  (0.01)   (0.005)    (0.02)    故障"    (0.005)   (0.02)
                                 (0.01)

P(支付不可用) ≈ 0.035%/年
```

## RCA实战工作流

```
Step 1: 问题定义 → 发生了什么？在哪里？什么时候？影响多大？
Step 2: 数据收集 → 日志/监控/时间线/访谈
Step 3: 原因分析 → 5-Whys/鱼骨图/区分近因和根因
Step 4: CAPA → 纠正措施(修复当前)+预防措施(防止复发)
Step 5: 跟踪验证 → 验证修复有效性+预防措施落地
```

## 缺陷趋势分析工具

```python
from datetime import datetime, timedelta
from collections import defaultdict, Counter

class DefectTrendAnalyzer:
    def __init__(self, defects: list):
        self.defects = defects

    def analyze(self, days: int = 90) -> dict:
        cutoff = datetime.now() - timedelta(days=days)
        recent = [d for d in self.defects
                  if d["created_at"] >= cutoff]

        weekly = defaultdict(
            lambda: {"total": 0, "critical": 0, "resolved": 0})
        for d in recent:
            wk = d["created_at"].strftime("%Y-W%W")
            weekly[wk]["total"] += 1
            if d["severity"] in ("致命", "严重"):
                weekly[wk]["critical"] += 1
            if d["status"] == "closed":
                weekly[wk]["resolved"] += 1

        return {
            "weekly_trend": dict(sorted(weekly.items())),
            "source_dist": dict(Counter(
                d["source"] for d in recent).most_common()),
            "type_dist": dict(Counter(
                d["type"] for d in recent).most_common()),
            "burndown_rate":
                sum(1 for d in recent if d["status"] == "closed")
                / max(len(recent), 1) * 100,
        }
```

## RCA的质量文化要求

- [ ] 不追责（Blameless）：RCA目标是找系统性问题而非追究个人
- [ ] 全员参与：开发、测试、运维、产品共同参与
- [ ] 闭环管理：每个RCA产出可执行Action Item并跟踪到完成
- [ ] 知识沉淀：RCA结果共享全团队，避免重复踩坑
- [ ] 持续改进：定期回顾RCA实施效果

## 本节小结

缺陷分析和根因分析是测试团队从"发现Bug"走向"预防Bug"的关键跨越。5-Whys深挖根本原因，鱼骨图多维度可视化，故障树分析量化评估风险。记住：RCA的最高境界不是找到"谁犯了错"，而是找到"什么流程/系统/工具让这个错误得以发生"。"""
})

path18_content.append({
    "title": "第7节：TMMi测试成熟度模型与实践",
    "sort_order": 7, "knowledge_point": "TMMi成熟度模型", "time_estimate": 30,
    "content": """## TMMi测试成熟度模型概述

TMMi（Test Maturity Model integration）是由TMMi基金会开发的测试过程改进框架，专注于测试过程的评估和改进，是国际公认的测试过程能力评估标准。

TMMi不是"考核"测试团队的工具，而是提供结构化的改进路线图，帮助组织系统地提升测试能力。

## TMMi的五个成熟度等级

```
+--------------------------------------------------------------------+
|                    TMMi成熟度等级递进模型                             |
|                                                                    |
|                                    +---------------------------+   |
|                                    |  Level 5: 优化级           |   |
|                                    | . 缺陷预防                 |   |
|                                    | . 测试过程优化             |   |
|                                    | . 质量控制                 |   |
|                                    +-------------+-------------+   |
|                                                  |                 |
|                              +-------------------+-------------+   |
|                              |  Level 4: 已度量级               |   |
|                              | . 测试度量                      |   |
|                              | . 产品质量评估                  |   |
|                              | . 高级评审                      |   |
|                              +---------------+-----------------+   |
|                                              |                     |
|                        +---------------------+-----------------+   |
|                        |  Level 3: 已定义级                     |   |
|                        | . 测试组织        . 非功能测试         |   |
|                        | . 测试培训计划    . 同行评审           |   |
|                        | . 测试生命周期与集成                   |   |
|                        +---------------------+-----------------+   |
|                                              |                     |
|            +---------------------------------+-----------------+   |
|            |  Level 2: 已管理级                                |   |
|            | . 测试方针与策略  . 测试监督与控制  . 测试环境     |   |
|            | . 测试计划        . 测试设计与执行                 |   |
|            +---------------------------------------------------+   |
|                                                                    |
|            +---------------------------------------------------+   |
|            |  Level 1: 初始级                                   |   |
|            | . 测试是混乱、临时、无章可循的                      |   |
|            | . 成功依赖于英雄式人物                              |   |
|            +---------------------------------------------------+   |
+--------------------------------------------------------------------+
```

## 各等级关键过程域（KPA）

### Level 2: 已管理级 —— 从混乱到有序

| 过程域 | 目标 | 关键实践 |
|--------|------|----------|
| 测试方针与策略 | 建立测试方向和战略 | 制定方针文档、管理层批准、全员传达 |
| 测试计划 | 有计划地开展测试活动 | 制定计划、识别风险、估算工作量 |
| 测试监督与控制 | 按计划执行及时纠偏 | 跟踪进度、收集度量、定期报告 |
| 测试设计与执行 | 系统化设计并执行 | 使用设计技术、建立用例库、规范执行 |
| 测试环境 | 环境可用且与生产一致 | 环境需求分析、管理、问题跟踪 |

### Level 3: 已定义级 —— 从个人经验到组织标准

| 过程域 | 目标 | 关键实践 |
|--------|------|----------|
| 测试组织 | 建立专业测试团队 | 定义角色、建立职能、独立测试 |
| 测试培训计划 | 系统化培养能力 | 能力评估、培训计划、知识库 |
| 测试生命周期与集成 | 测试集成到SDLC | 阶段对齐、测试左移、准入准出 |
| 非功能测试 | 建立非功能体系 | 性能、安全、可靠性、易用性测试 |
| 同行评审 | 规范化评审机制 | 评审类型定义、评审度量 |

### Level 4: 已度量级 —— 从定性到数据驱动

测试度量：建立全面度量体系 | 产品质量评估：数据驱动决策 | 高级评审：量化评审流程

### Level 5: 优化级 —— 从被动响应到主动预防

缺陷预防：系统性预防缺陷 | 测试过程优化：持续改进 | 质量控制：统计过程控制

## TMMi评估方法

| 评估类型 | 目的 | 适用范围 | 产出物 |
|----------|------|---------|--------|
| 正式评估 | 获得官方认证 | 对外展示/招标 | 认证报告和证书 |
| 自我评估 | 了解成熟度 | 内部诊断 | 改进路线图 |

## TMMi自我评估工具

```python
class TMMiSelfAssessment:
    QUESTIONS = {
        "测试方针与策略": [
            "是否有经管理层批准的测试方针文档？",
            "测试方针是否明确了使命、目标和战略方向？",
            "测试方针是否在组织内充分沟通？",
        ],
        "测试计划": [
            "是否在项目早期就开始制定测试计划？",
            "测试计划是否包含风险识别和应对？",
            "测试计划是否基于估算的工作量编制？",
        ],
        "非功能测试": [
            "是否有明确的性能测试策略和计划？",
            "是否有安全测试活动（SAST或DAST）？",
        ],
    }

    def __init__(self):
        self.answers = {}

    def answer(self, area, q_idx, score):
        # 评分: 0=未实施, 1=部分, 2=大部, 3=完全
        self.answers[f"{area}:{q_idx}"] = score

    def calculate(self) -> dict:
        scores = {}
        for area, questions in self.QUESTIONS.items():
            vals = [self.answers.get(f"{area}:{i}", 0)
                    for i in range(len(questions))]
            avg = sum(vals) / len(vals)
            level = ("成熟" if avg >= 2.5 else
                     "发展中" if avg >= 1.5 else "初始")
            scores[area] = {"average": round(avg, 1), "level": level}
        return scores

# 使用示例
a = TMMiSelfAssessment()
a.answer("测试方针与策略", 0, 2)
a.answer("测试方针与策略", 1, 3)
a.answer("非功能测试", 0, 1)
scores = a.calculate()
for area, data in scores.items():
    print(f"{area}: {data['level']} ({data['average']}分)")
```

## TMMi实施路径

```
第一年：补短板 → Level 2
  重点：建立测试流程规范、测试计划制度、测试用例库

第二年：建体系 → Level 3
  重点：建立独立测试组织、规范化评审、引入非功能测试

第三年：量化驱动 → Level 4
  重点：建立测试度量体系、数据驱动的质量评估

长期：持续优化 → Level 5
  重点：缺陷预防、统计过程控制、新技术引入
```

## 本节小结

TMMi不是"荣誉证书"，而是"体检报告"和"改进路线图"。大多数国内企业停留在Level 2-3之间。TMMi的核心精神：持续改进比追求高级别认证更重要。"""
})

path18_content.append({
    "title": "第8节：测试团队建设、技术选型与工具链规划",
    "sort_order": 8, "knowledge_point": "测试团队与工具链", "time_estimate": 30,
    "content": """## 测试团队建设的方法论

测试团队建设是测试架构师的重要职责。好的团队不是简单堆人，而是根据业务特征、技术栈和发展阶段，构建有梯度的、可持续成长的团队结构。

## 测试团队的组织模型

| 模型 | 结构 | 优点 | 缺点 | 适用场景 |
|------|------|------|------|----------|
| 独立测试团队 | 测试与开发分开 | 视角独立、把关强 | 沟通成本高 | 传统/大型项目 |
| 嵌入式测试 | 测试编入开发团队 | 效率高、左移好 | 独立性弱 | 敏捷/Scrum |
| 测试中台 | 平台+工具+业务 | 效率高、复用 | 组织复杂 | 中大型互联网 |
| 质量工程(QE) | 开发+测试融合 | 全员质量 | 对个人要求高 | 技术驱动型 |

## 测试团队梯度结构

```
                          +----------+
                          | 测试架构师 |     1人 (8年+)
                          | (TA)      |
                          +-----+----+
                                |
                    +-----------+-----------+
                    |           |           |
              +-----v----+ +---v---+ +-----v----+
              |高级测试   | |性能专家| |安全专家  |  2-3人 (5-8年)
              |工程师     | |       | |         |
              +-----+----+ +-------+ +----------+
                    |
        +-----------+-----------+
        |           |           |
  +-----v----+ +---v----+ +---v----+
  |中级测试   | |中级测试 | |中级测试 |  3-5人 (2-5年)
  |(API/UI)  | |(后端)   | |(数据)   |
  +-----+----+ +---+----+ +---+----+
        |           |           |
        +-----------+-----------+
                    |
              +-----v----+
              |初级测试   |  3-5人 (0-2年)
              |工程师     |
              +----------+
```

## 团队能力矩阵

| 能力 | 初级 | 中级 | 高级 | 架构师 |
|------|------|------|------|--------|
| 测试设计 | 遵循模板 | 独立设计+评审 | 主导策略+培训 | 方法论体系 |
| 自动化 | 维护脚本 | 框架扩展 | 架构设计 | 平台化+决策 |
| 编程 | 基础脚本 | 工具开发 | 系统开发 | 架构设计 |
| 性能测试 | 执行场景 | 设计+分析 | 全链路调优 | 性能架构 |
| 安全测试 | 用例执行 | 扫描+分析 | 渗透测试 | 安全架构 |
| CI/CD | 理解流水线 | 维护 | 设计 | 工具链架构 |

## 测试技术选型决策框架

```
Step 1: 技术需求识别
  . 被测系统技术栈？ . 团队技能储备？ . 测试场景特点？ . 预算限制？

Step 2: 候选工具调研
  . 社区活跃度（Stars/Issues/更新频率）
  . 学习曲线与文档质量
  . 生态系统与集成能力
  . 性能与可扩展性
  . 许可证模式与TCO

Step 3: POC验证
  . 选1-2个代表场景 . 搭建最小可行环境 . 评估实际易用性 . 收集团队反馈

Step 4: 决策与推广
  . 输出评估报告 . 制定推广路线图 . 建立最佳实践和培训计划
```

## 测试技术选型矩阵

```python
class ToolSelectionMatrix:
    CRITERIA_WEIGHTS = {
        "功能满足度": 0.25, "易用性": 0.15,
        "社区活跃度": 0.10, "CI/CD集成": 0.10,
        "学习成本": 0.10, "性能与扩展": 0.10,
        "许可证成本": 0.10, "团队技能匹配": 0.10,
    }

    def __init__(self):
        self.candidates = {}

    def add(self, name, scores):
        self.candidates[name] = scores

    def evaluate(self):
        results = []
        for name, scores in self.candidates.items():
            score = sum(
                scores.get(c, 0) * self.CRITERIA_WEIGHTS.get(c, 0)
                for c in self.CRITERIA_WEIGHTS)
            results.append({"tool": name, "score": round(score, 2)})
        return sorted(results, key=lambda x: x["score"], reverse=True)

# 示例：API测试工具选型
m = ToolSelectionMatrix()
m.add("pytest+requests", {
    "功能满足度": 5, "易用性": 5, "社区活跃度": 5,
    "CI/CD集成": 5, "学习成本": 4, "性能与扩展": 5,
    "许可证成本": 5, "团队技能匹配": 5})
m.add("Postman/Newman", {
    "功能满足度": 4, "易用性": 5, "社区活跃度": 5,
    "CI/CD集成": 4, "学习成本": 5, "性能与扩展": 3,
    "许可证成本": 4, "团队技能匹配": 4})
for r in m.evaluate():
    print(f"{r['tool']:<20} {r['score']:.2f}")
```

## 测试工具链全景

```
项目管理    -->  测试管理    -->  自动化测试  -->  性能测试
Jira/Linear     TestLink/       pytest/        JMeter/
Trello          Zephyr/Xray     Playwright     Locust/k6

安全测试    -->  测试报告    -->  CI/CD       -->  测试数据
OWASP ZAP/      Allure/         Jenkins/       Faker/
SonarQube       ReportPortal    GH Actions     Testcontainers

基础设施层: Docker | K8s | Terraform | Selenium Grid
```

## 工具链选型关键原则

1. **一致性优先**：围绕统一语言和框架生态，减少上下文切换
2. **渐进式引入**：每次引入1-2个新工具，熟练掌握后再引入下一个
3. **集成优于独立**：选择无缝集成的工具组合
4. **开源优先**：除非明确商业需求，优先选择活跃开源工具
5. **团队共识**：通过民主讨论和技术POC获得认可

## 测试团队建设核心策略

### 能力梯度建设

- 初级(0-2年)：校招为主，看重学习能力和态度
- 中级(2-5年)：社招为主，看重项目经验和独立解决问题能力
- 高级(5-8年)：定向猎聘，看重专项深度和技术视野
- 架构师(8年+)：内部培养，从高级中选拔有架构思维者

### 技术氛围营造

- [ ] 每两周一次技术分享会（内部轮值+外部嘉宾）
- [ ] 鼓励技术博客输出，建立团队技术品牌
- [ ] 季度Hackathon，自由组队攻克技术难题
- [ ] 测试代码也要Code Review
- [ ] 对重大事故和测试遗漏进行无责复盘

### 职业发展双通道

```
管理通道                  技术通道
测试总监              首席测试架构师
测试经理              资深测试架构师
测试主管              测试架构师
               高级测试工程师（分叉点）
              中级测试工程师
              初级测试工程师
```

## 工具链演进路线图

```
第1阶段（0-6月）：基础工具链
  测试管理上线 | CI/CD集成 | 测试框架统一 | 报告平台搭建

第2阶段（6-12月）：自动化与效率
  API自动化框架 | UI自动化框架 | 性能工具引入 | 测试数据MVP

第3阶段（12-24月）：智能化与平台化
  统一执行平台 | 视觉回归测试 | AI用例生成试点 | 覆盖率可视化

第4阶段（24月+）：持续优化
  ML缺陷预测 | 质量度量仪表盘 | LLM代码生成 | 测试中台
```

## 本节小结

测试团队建设和工具链规划是测试架构师最具挑战也最有成就感的工作。它不仅关乎"选什么工具"和"招什么人"，更是一门平衡技术理想与现实约束、短期交付与长期能力建设的管理艺术。好的测试架构师能画出清晰的技术路线图，团结团队朝共同目标前进，持续为组织的质量文化注入活力。"""
})

# ============================================================
# Write output
# ============================================================

content = HEADER + "\n"
content += make_path_sections("AI测试与智能化", path17_sections) + "\n"
content += make_path_sections("测试架构设计与质量度量", path18_content) + "\n"

with open("fastapi_backend/seed_lessons_p5.py", "w", encoding="utf-8") as f:
    f.write(content)

print(f"Done! File written with {len(path17_sections)} + {len(path18_content)} sections.")