"""
TestMaster 全套教程内容填充脚本
为每个学习路径创建完整可阅读的教程章节
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

LESSON_CONTENT = {}

# ============================================================
# 软件测试基础理论
# ============================================================
LESSON_CONTENT["软件测试基础理论"] = [
    {
        "title": "第1节：软件测试的定义与目的",
        "sort_order": 1,
        "knowledge_point": "测试基础概念",
        "time_estimate": 20,
        "content": """## 软件测试的定义

软件测试（Software Testing）是使用人工或自动手段来运行或测定某个系统的过程，其目的在于检验它是否满足规定的需求，或弄清预期结果与实际结果之间的差别。

换句话说，软件测试就是**验证软件的正确性、完整性和质量**的过程。

## 测试的核心目的

**1. 发现缺陷（Find Bugs）**

这是测试最直接的目的。通过执行测试用例，尽可能多地发现软件中存在的缺陷和问题。一个著名的测试原则是：**测试只能证明缺陷存在，而不能证明缺陷不存在。**

**2. 验证需求（Verify Requirements）**

确保软件的功能、性能、安全性等方面符合需求规格说明书中定义的要求。每一个需求都应该有对应的测试用例来验证。

**3. 评估质量（Assess Quality）**

测试为项目干系人提供关于软件质量的客观信息，帮助做出发布决策。测试报告中的缺陷密度、通过率等指标是质量评估的重要依据。

**4. 预防缺陷（Prevent Defects）**

通过早期介入测试（如需求评审、设计评审），在缺陷产生之前就发现并纠正问题，降低修复成本。

## 验证 vs 确认

- **验证（Verification）**：我们正确地建造产品了吗？关注过程，如评审、走查。
- **确认（Validation）**：我们建造了正确的产品吗？关注结果，如系统测试、验收测试。

## 测试与调试的区别

| 方面 | 测试 | 调试 |
|------|------|------|
| 目的 | 发现缺陷 | 定位并修复缺陷 |
| 执行者 | 测试人员 | 开发人员 |
| 阶段 | 贯穿整个开发过程 | 主要在编码阶段 |
| 方式 | 运行程序或静态检查 | 分析代码、断点跟踪 |

> 测试是发现错误的过程，而调试是修复错误的过程。两者相辅相成。

## 小结

软件测试是软件质量保障的核心活动。一个好的测试工程师不仅要有发现问题的敏锐嗅觉，还要理解测试在整个软件工程中的定位和价值。接下来的章节中，我们将深入学习测试的原则、方法和技术。""",
    },
    {
        "title": "第2节：测试的七大原则",
        "sort_order": 2,
        "knowledge_point": "测试原则",
        "time_estimate": 25,
        "content": """## ISTQB定义的测试七大原则

### 原则1：测试说明存在缺陷（Testing shows the presence of defects）

测试可以证明缺陷存在，但不能证明没有缺陷。即使测试没有发现任何问题，也不能说明软件是完美的。**测试降低了软件中存在未发现缺陷的概率，但即使没有找到缺陷，也不能证明软件100%正确。**

### 原则2：穷尽测试是不可能的（Exhaustive testing is impossible）

除了极其简单的小程序，想测试所有输入组合和前置条件是不可能的。我们需要使用风险评估和测试设计技术来确定测试的重点和范围，而不是试图测试所有东西。

**举例**：一个接受两个32位整数相加的函数，输入组合是2^64种，即超过184亿亿种组合，穷尽测试显然不可能。

### 原则3：早期测试（Early testing）

测试活动应尽早开始。缺陷发现得越早，修复成本越低。测试左移（Shift-Left Testing）就是这个原则的体现——在需求阶段就开始测试分析和评审。

**修复成本递增规律**：
- 需求阶段发现缺陷：修复成本 = 1x
- 设计阶段发现缺陷：修复成本 = 10x
- 编码阶段发现缺陷：修复成本 = 50x
- 测试阶段发现缺陷：修复成本 = 100x
- 生产环境发现缺陷：修复成本 = 1000x

### 原则4：缺陷集群性（Defect clustering）

大部分缺陷往往集中在少部分模块中。遵循**帕累托法则（二八定律）**：80%的缺陷通常只存在于20%的模块中。识别这些高风险模块并重点测试是提高测试效率的关键。

### 原则5：杀虫剂悖论（Pesticide Paradox）

如果反复使用相同的测试用例集，最终将无法发现新的缺陷。就像杀虫剂用久了虫子会产生抗药性一样。**解决方法是定期审查和修订测试用例，增加新的、不同的测试用例。**

### 原则6：测试依赖于上下文（Testing is context dependent）

不同类型的软件需要不同的测试方法。电商网站和航空控制系统的测试策略完全不同：
- 电商网站：侧重并发、支付安全、用户体验
- 医疗设备：侧重安全性、合规性、精确性
- 游戏：侧重娱乐性、流畅度、兼容性

### 原则7：没有缺陷就是好用？（Absence-of-errors fallacy）

即使软件没有缺陷，也不代表它满足用户需求。一个技术上完美但不符合用户期望的系统仍然是失败的。**测试不仅要找Bug，还要验证需求。**

## 小结

这七大原则是每个测试工程师必须牢记的准则。它们指导我们如何高效地规划测试、设计用例和评估风险。""",
    },
    {
        "title": "第3节：软件开发生命周期与测试模型",
        "sort_order": 3,
        "knowledge_point": "开发模型",
        "time_estimate": 25,
        "content": """## 常见的软件开发模型

### 瀑布模型（Waterfall Model）

瀑布模型是最经典的软件开发模型，将开发过程分为线性顺序的阶段：

```
需求分析 → 设计 → 编码 → 测试 → 维护
```

**在瀑布模型中的测试**：测试只在编码完成后进行，发现问题后返工成本很高。这种方式现在已很少单独使用。

### V模型（V-Model）

V模型是瀑布模型的改进版，强调了测试活动与开发活动的对应关系：

```
需求分析 ←→ 验收测试
   ↓           ↑
概要设计 ←→ 系统测试
   ↓           ↑
详细设计 ←→ 集成测试
   ↓           ↑
  编码   ←→ 单元测试
```

**V模型的优点**：
- 左侧开发，右侧测试，一一对应
- 测试活动与开发活动并行规划
- 每个阶段都有明确的测试目标

**V模型的缺点**：
- 仍然是线性模型，不够灵活
- 需求变更困难
- 不适合敏捷开发

### W模型（W-Model）

W模型在V模型基础上强调：**测试应该伴随着整个开发过程**，不仅要对代码进行测试，还要对需求和设计进行测试。

### 敏捷开发中的测试

在敏捷开发（Scrum/Kanban）中，测试不再是独立的阶段，而是融入每个迭代：

- **持续测试**：每天都在进行测试
- **自动化优先**：自动化测试是敏捷的基石
- **测试驱动开发（TDD）**：先写测试再写代码
- **行为驱动开发（BDD）**：用自然语言描述测试场景
- **全员质量意识**：质量是团队的责任，不仅限于测试人员

### TDD的"红-绿-重构"循环

```
1. 红（Red）：编写一个失败的测试用例
2. 绿（Green）：编写最少的代码让测试通过
3. 重构（Refactor）：优化代码结构，保持测试通过
4. 重复循环...
```

## 小结

理解各种开发模型对测试策略的选择至关重要。在实际工作中，你需要根据项目类型选择合适的测试策略。""",
    },
    {
        "title": "第4节：测试分类体系",
        "sort_order": 4,
        "knowledge_point": "测试分类",
        "time_estimate": 25,
        "content": """## 按测试阶段分类

### 单元测试（Unit Testing）

对软件的最小可测试单元（函数、方法、类）进行测试。通常由开发人员编写和执行。

**特点**：
- 粒度最小，执行速度快
- 通常使用白盒测试方法
- 是自动化测试的基础
- 常用框架：JUnit（Java）、pytest（Python）、Jest（JavaScript）

### 集成测试（Integration Testing）

测试多个单元/模块之间的交互是否正确。

**集成策略**：
- **自顶向下**：从顶层模块开始，使用桩模块
- **自底向上**：从底层模块开始，使用驱动模块
- **三明治集成**：结合两种方式
- **大爆炸集成**：一次性集成所有模块（不推荐）

### 系统测试（System Testing）

将整个软件系统作为一个整体进行测试，验证其是否满足需求规格。

**系统测试类型包括**：
- 功能测试
- 性能测试
- 安全性测试
- 兼容性测试
- 易用性测试
- 可靠性测试

### 验收测试（Acceptance Testing）

由用户或客户进行的测试，确认系统满足业务需求。

- **Alpha测试**：在开发环境中由用户进行
- **Beta测试**：在用户实际环境中由用户进行
- **UAT（用户验收测试）**：正式的业务验收

## 按测试方法分类

### 黑盒测试（Black-box Testing）

不关心内部结构，只关注输入和输出。测试者不需要了解代码。

**方法**：等价类划分、边界值分析、因果图、判定表、场景法、错误推测法

### 白盒测试（White-box Testing）

基于代码内部逻辑的测试。测试者需要了解代码结构。

**覆盖标准**：语句覆盖、判定覆盖、条件覆盖、判定-条件覆盖、路径覆盖

### 灰盒测试（Gray-box Testing）

介于黑盒和白盒之间，了解部分内部结构但主要从外部测试。

## 按是否执行分类

- **静态测试**：不运行程序，通过审查、走查、静态分析工具检查
- **动态测试**：实际运行程序，输入测试数据，观察输出结果

## 按测试目的分类

- **功能测试**：验证功能是否正确
- **非功能测试**：性能、安全性、可用性、兼容性等
- **回归测试**：验证修改后原有功能未受影响
- **冒烟测试**：验证基本功能是否可用
- **探索性测试**：基于经验和直觉的自由测试""",
    },
    {
        "title": "第5节：缺陷管理",
        "sort_order": 5,
        "knowledge_point": "缺陷管理",
        "time_estimate": 20,
        "content": """## 什么是软件缺陷（Bug）？

软件缺陷是指软件产品中存在的、导致系统不能正常工作的问题。广义上也包括：
- 功能未按需求实现
- 需求规格说明书中要求的功能未实现
- 出现了需求规格说明书中不应该出现的问题
- 难以理解、不易使用或运行缓慢

## 缺陷的生命周期

一个缺陷从发现到关闭经历的典型生命周期：

```
New（新建） → Open（打开/分配） → Fixed（已修复） → Verified（已验证） → Closed（关闭）
                                     ↓
                                Reopened（重新打开）
                                     ↓
                                Rejected（拒绝/不是bug）
```

**各状态说明**：
| 状态 | 说明 | 负责人 |
|------|------|--------|
| New | 测试人员刚提交的缺陷 | 测试人员 |
| Open | 已确认是bug，分配给开发 | 开发经理 |
| Fixed | 开发人员已修复 | 开发人员 |
| Verified | 测试人员验证修复通过 | 测试人员 |
| Closed | 缺陷已解决并关闭 | 测试经理 |
| Reopened | 修复未通过，重新打开 | 测试人员 |
| Rejected | 不是bug或重复提交 | 开发人员 |

## 缺陷的重要属性

### 严重程度（Severity）

衡量缺陷对系统功能的影响程度：

- **Blocker/Critical（致命）**：系统崩溃、数据丢失、核心功能无法使用
- **Major（严重）**：主要功能错误，严重影响使用
- **Minor（一般）**：次要功能错误，有替代方案
- **Trivial（轻微）**：界面错字、排版问题等

### 优先级（Priority）

衡量缺陷需要被修复的紧急程度：

- **P0-立即**：必须立即修复，阻塞测试或发布
- **P1-高**：应尽快在下一个版本中修复
- **P2-中**：按正常排期修复
- **P3-低**：可以在资源允许时修复

> 严重程度是技术评估，优先级是业务决策。一个导致公司Logo显示不正确的bug，严重程度低但优先级可能很高。

## 缺陷报告（Bug Report）

一份好的缺陷报告应该包含：
1. **标题**：简短准确地描述问题
2. **复现步骤**：详细的、可重复的操作步骤
3. **实际结果**：执行操作后的实际现象
4. **预期结果**：按照需求应该出现的结果
5. **环境信息**：操作系统、浏览器、版本等
6. **附件**：截图、日志、录屏等

## 常用缺陷管理工具

- **JIRA**：最流行的商业项目管理工具
- **禅道**：国产开源项目管理工具
- **Bugzilla**：经典的开源缺陷管理工具
- **GitHub Issues**：适合小团队的轻量级方案
- **TAPD**：腾讯敏捷协作平台""",
    },
    {
        "title": "第6节：测试用例设计基础",
        "sort_order": 6,
        "knowledge_point": "测试用例要素",
        "time_estimate": 20,
        "content": """## 什么是测试用例？

测试用例（Test Case）是为特定测试目标而设计的一组输入、执行条件和预期结果的集合。它是测试执行的最小单位。

## 测试用例的八大要素

| 要素 | 说明 | 是否必须 |
|------|------|----------|
| 用例编号 | 唯一标识，如TC_LOGIN_001 | 必须 |
| 测试模块 | 所属功能模块 | 必须 |
| 用例标题 | 简述测试内容 | 必须 |
| 前置条件 | 执行前需要满足的条件 | 可选 |
| 测试步骤 | 详细的操作步骤 | 必须 |
| 测试数据 | 输入的具体数据 | 必须 |
| 预期结果 | 期望看到的输出/现象 | 必须 |
| 后置处理 | 测试后的清理操作 | 可选 |

## 测试用例设计原则

### 单一原则
每个测试用例只测试一个场景或功能点。如果一个用例测试多个功能，当它失败时你无法快速定位是哪个功能出了问题。

### 独立性
测试用例之间应该相互独立，一个用例的执行不应依赖另一个用例的结果。

### 可重复性
任何人按照测试用例描述的步骤执行，都应该得到相同的测试结果。

### 清晰性
步骤和预期结果要清晰明确，避免歧义。新人也能看懂并执行。

## 好的测试用例 vs 差的测试用例

**差的测试用例**：
> 测试登录功能，输入一些账号密码，看看能不能登录成功。

**好的测试用例**：
> **用例编号**：TC_LOGIN_001
> **标题**：验证正确账号密码可以成功登录
> **前置条件**：已注册账号admin/Test@123
> **步骤**：
> 1. 打开登录页面
> 2. 输入用户名：admin
> 3. 输入密码：Test@123
> 4. 点击"登录"按钮
> **预期结果**：
> 1. 页面跳转到首页
> 2. 右上角显示用户名"admin"
> 3. 登录成功提示出现

## 测试用例的管理

- 定期审查和更新测试用例
- 建立测试用例与需求的追溯矩阵
- 维护测试用例的版本
- 标记用例的执行状态（通过/失败/阻塞/跳过）""",
    },
    {
        "title": "第7节：测试级别详解",
        "sort_order": 7,
        "knowledge_point": "测试级别",
        "time_estimate": 25,
        "content": """## 测试金字塔

测试金字塔是Mike Cohn提出的测试策略模型，描述了不同级别测试的合理比例：

```
        ╱  E2E  ╲
       ╱  (少量)  ╲
      ╱─────────────╲
     ╱   集成测试    ╲
    ╱   (中等数量)   ╲
   ╱─────────────────╲
  ╱     单元测试       ╲
 ╱     (最多数量)       ╲
╱─────────────────────────╲
```

**核心思想**：
- 底层（单元测试）数量最多，执行最快，成本最低
- 中层（集成测试）数量适中
- 顶层（E2E/UI测试）数量最少，执行最慢，维护成本最高

## 单元测试深入

### 什么是好的单元测试？

**FIRST原则**：
- **F**ast（快速）：每个单元测试应快速执行
- **I**solate（隔离）：测试之间相互独立
- **R**epeatable（可重复）：任何环境下都能重复运行
- **S**elf-validating（自验证）：测试结果明确（通过/失败）
- **T**imely（及时）：在编码时同步编写

### 单元测试示例（Python + pytest）

```python
# 待测试的函数
def calculator_add(a, b):
    return a + b

# 单元测试
def test_calculator_add_positive():
    assert calculator_add(2, 3) == 5

def test_calculator_add_negative():
    assert calculator_add(-1, -1) == -2

def test_calculator_add_zero():
    assert calculator_add(5, 0) == 5
```

## 集成测试深入

### 常见集成问题

- 模块间接口不匹配
- 数据在模块间传递时丢失或变形
- 全局数据结构被异常修改
- 模块间的时序问题
- 错误累积

### 集成测试策略选择

| 策略 | 优点 | 缺点 |
|------|------|------|
| 自顶向下 | 早期验证主流程 | 桩模块工作量大 |
| 自底向上 | 驱动模块简单 | 最后才能看到完整系统 |
| 三明治 | 兼顾两者 | 设计和协调复杂 |

## E2E（端到端）测试

E2E测试模拟真实用户场景，测试整个系统从开始到结束的完整流程。

**典型的E2E测试场景——用户购物流程**：
1. 用户登录 → 2. 搜索商品 → 3. 加入购物车 → 4. 填写地址 → 5. 支付 → 6. 查看订单

**常用工具**：Selenium、Cypress、Playwright

## 小结

测试金字塔是指导测试策略的核心模型。投入比例应该是：单元测试 > 集成测试 > E2E测试。""",
    },
    {
        "title": "第8节：敏捷测试与持续测试",
        "sort_order": 8,
        "knowledge_point": "敏捷测试",
        "time_estimate": 25,
        "content": """## 敏捷测试的核心概念

在传统的瀑布模型中，测试是一个独立的阶段。而在敏捷开发中，**测试是持续进行的活动**，贯穿每个Sprint的始终。

### 敏捷测试的特点

**1. 全团队对质量负责**
不只是测试人员关心质量，开发、产品、设计都需要为质量负责。

**2. 测试左移（Shift-Left）**
把测试活动提前到开发的最早期阶段。测试人员在需求评审时就参与进来，识别潜在的测试场景和风险。

**3. 持续测试（Continuous Testing）**
每一次代码提交都会触发自动化测试，问题在第一时间被发现和修复。

**4. 自动化是基石**
没有自动化测试，敏捷的快速迭代就无法保证质量。至少要实现：
- 单元测试自动化
- 接口测试自动化
- 关键流程的UI自动化

**5. 探索性测试**
自动化覆盖不了所有场景，探索性测试发挥测试人员的创造性和直觉。

## Scrum中的测试角色

在Scrum框架下，测试人员的日常工作：

### Sprint开始
- 参与Sprint Planning，评估测试工作量
- 评审User Story，编写测试用例
- 准备测试数据和测试环境

### Sprint进行中
- 每日站会汇报测试进展和阻塞问题
- 执行新功能的测试
- 执行回归测试
- 与开发人员沟通发现的缺陷

### Sprint结束
- 参与Sprint Review，展示测试成果
- Sprint Retrospective中提出改进建议
- 更新和维护测试用例库

## 行为驱动开发（BDD）

BDD用自然语言描述系统的行为，让技术团队和业务团队共同理解需求。

### Gherkin语法示例

```gherkin
Feature: 用户登录

  Scenario: 使用正确的账号密码登录
    Given 用户在登录页面
    When 输入用户名 "admin" 和密码 "123456"
    And 点击登录按钮
    Then 页面跳转到首页
    And 显示欢迎信息 "欢迎回来，admin"

  Scenario: 使用错误密码登录
    Given 用户在登录页面
    When 输入用户名 "admin" 和密码 "wrong"
    And 点击登录按钮
    Then 显示错误提示 "用户名或密码错误"
    And 停留在登录页面
```

## 持续集成/持续交付（CI/CD）

CI/CD是现代软件开发的核心实践：

**CI（持续集成）**：
开发者频繁将代码合并到主干，每次合并自动触发构建和测试。

**CD（持续交付）**：
代码经过测试后，自动部署到类生产环境，随时可以发布。

**典型的CI/CD Pipeline**：
```
代码提交 → 编译 → 单元测试 → 代码扫描 → 集成测试 → 构建镜像 → 部署到测试环境 → 自动化测试 → 部署到生产
```

## 小结

敏捷测试要求测试人员具备更全面的技能：编程能力、自动化能力、沟通能力和分析能力。这是从"找Bug的人"到"质量保障者"的转变。""",
    },
]

# ============================================================
# SQL数据库基础
# ============================================================
LESSON_CONTENT["SQL数据库基础"] = [
    {
        "title": "第1节：数据库基础概念",
        "sort_order": 1,
        "knowledge_point": "数据库概述",
        "time_estimate": 20,
        "content": """## 什么是数据库？

数据库（Database）是按照数据结构来组织、存储和管理数据的"仓库"。简单来说，就是把数据按照一定规则存储起来，方便以后查找、修改和删除。

## 为什么需要数据库？

在没有数据库的时候，数据存储在文件里。但随着数据量增大，文件存储的问题就暴露了：
- 查询效率低
- 数据容易不一致
- 并发访问困难
- 安全性无法保障

数据库解决了这些问题，提供了**高效的数据存取、数据安全、并发控制和数据一致性**。

## 关系型数据库（RDBMS）

关系型数据库是目前使用最广泛的数据库类型。它将数据组织成**表（Table）**，表之间通过**关系（Relation）**来关联。

### 核心概念

| 概念 | 说明 | 类比 |
|------|------|------|
| 数据库（Database） | 存放所有数据的容器 | 一个文件夹 |
| 表（Table） | 某种类型数据的集合 | 一个Excel表格 |
| 行（Row/Record） | 一条完整的数据记录 | 表格中的一行 |
| 列（Column/Field） | 数据的一个属性 | 表格中的一列 |
| 主键（Primary Key） | 唯一标识一条记录的字段 | 身份证号 |
| 外键（Foreign Key） | 关联其他表的字段 | 引用关系 |

### 常见的关系型数据库

| 数据库 | 特点 | 适用场景 |
|--------|------|----------|
| MySQL | 开源免费，社区庞大 | Web应用、中小型系统 |
| PostgreSQL | 功能强大，支持高级特性 | 复杂查询、数据分析 |
| Oracle | 商业数据库，企业级 | 大型企业系统 |
| SQL Server | 微软出品，与.NET集成好 | Windows生态 |
| SQLite | 轻量级，嵌入式 | 移动应用、小型项目 |

## SQL语言简介

**SQL（Structured Query Language，结构化查询语言）** 是操作关系型数据库的标准语言。

SQL语句分类：

| 类别 | 作用 | 常用语句 |
|------|------|----------|
| DDL（数据定义语言） | 定义数据库结构 | CREATE、ALTER、DROP |
| DML（数据操纵语言） | 操作数据 | SELECT、INSERT、UPDATE、DELETE |
| DCL（数据控制语言） | 控制访问权限 | GRANT、REVOKE |
| TCL（事务控制语言） | 管理事务 | COMMIT、ROLLBACK |

## 数据库设计基础

### 范式（Normalization）

范式是数据库设计时减少数据冗余的方法：

- **第一范式（1NF）**：每个字段不可再分（原子性）
- **第二范式（2NF）**：非主键字段完全依赖于主键（消除部分依赖）
- **第三范式（3NF）**：非主键字段不依赖于其他非主键字段（消除传递依赖）

### 一个简单的数据库设计示例

**学生选课系统**：

```
students 表：id、name、age、class_id
courses 表：id、name、teacher、credit
classes 表：id、name、grade
enrollments 表：id、student_id、course_id、score
```

这里 `enrollments` 表通过 `student_id` 和 `course_id` 关联了学生和课程，形成了一个**多对多关系**。

## 小结

理解数据库的基本概念是学习SQL的第一步。接下来的章节中，我们将通过大量实例，逐步掌握SQL的数据操作。""",
    },
    {
        "title": "第2节：SQL数据类型与建表",
        "sort_order": 2,
        "knowledge_point": "DDL建表",
        "time_estimate": 25,
        "content": """## MySQL常用数据类型

### 数值类型

| 类型 | 大小 | 范围 | 用途 |
|------|------|------|------|
| TINYINT | 1字节 | -128~127 | 年龄、状态码 |
| INT/INTEGER | 4字节 | -21亿~21亿 | 主键、数量 |
| BIGINT | 8字节 | 极大 | 大数据量ID |
| DECIMAL(M,D) | 变长 | 精确小数 | 金额 |
| FLOAT | 4字节 | 单精度 | 科学计算 |

### 字符串类型

| 类型 | 说明 | 使用场景 |
|------|------|----------|
| CHAR(N) | 定长字符串，N≤255 | 性别、状态码 |
| VARCHAR(N) | 变长字符串，N≤65535 | 用户名、邮箱 |
| TEXT | 长文本，最大65535字符 | 文章内容 |
| LONGTEXT | 超长文本 | 富文本、日志 |

### 日期时间类型

| 类型 | 格式 | 说明 |
|------|------|------|
| DATE | YYYY-MM-DD | 日期 |
| TIME | HH:MM:SS | 时间 |
| DATETIME | YYYY-MM-DD HH:MM:SS | 日期时间 |
| TIMESTAMP | 时间戳 | 自动更新 |

## CREATE TABLE 详解

### 基本语法

```sql
CREATE TABLE 表名 (
    列名1 数据类型 [约束],
    列名2 数据类型 [约束],
    ...
    [表级约束]
);
```

### 常用列级约束

| 约束 | 说明 | 示例 |
|------|------|------|
| NOT NULL | 不能为空 | `username VARCHAR(50) NOT NULL` |
| UNIQUE | 值唯一 | `email VARCHAR(100) UNIQUE` |
| PRIMARY KEY | 主键 | `id INT PRIMARY KEY` |
| AUTO_INCREMENT | 自增 | `id INT AUTO_INCREMENT` |
| DEFAULT | 默认值 | `status INT DEFAULT 1` |

### 实际建表示例

**创建用户表**：

```sql
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '用户ID',
    username VARCHAR(50) NOT NULL COMMENT '用户名',
    email VARCHAR(100) UNIQUE NOT NULL COMMENT '邮箱',
    password_hash VARCHAR(128) NOT NULL COMMENT '密码哈希',
    age INT COMMENT '年龄',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否激活',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户表';
```

**创建订单表（含外键）**：

```sql
CREATE TABLE orders (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    product_name VARCHAR(200) NOT NULL,
    amount DECIMAL(10, 2) NOT NULL COMMENT '金额',
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

## ALTER TABLE 修改表结构

```sql
-- 添加列
ALTER TABLE users ADD COLUMN phone VARCHAR(20);

-- 修改列类型
ALTER TABLE users MODIFY COLUMN age TINYINT;

-- 删除列
ALTER TABLE users DROP COLUMN phone;

-- 添加索引
ALTER TABLE users ADD INDEX idx_username (username);
CREATE INDEX idx_email ON users(email);

-- 添加外键
ALTER TABLE orders ADD CONSTRAINT fk_user
    FOREIGN KEY (user_id) REFERENCES users(id);
```

## DROP TABLE 删除表

```sql
-- 删除表（不可恢复！）
DROP TABLE orders;
DROP TABLE IF EXISTS orders;
```

## 小结

创建表时要注意：
1. 选择合适的数据类型（不要都用VARCHAR）
2. 给重要的列加上NOT NULL约束
3. 主键最好用自增INT或BIGINT
4. 添加COMMENT方便维护
5. 使用InnoDB引擎和utf8mb4字符集""",
    },
    {
        "title": "第3节：数据查询SELECT（上）",
        "sort_order": 3,
        "knowledge_point": "SQL基础查询",
        "time_estimate": 25,
        "content": """## SELECT 基本语法

```sql
SELECT 列名1, 列名2, ...
FROM 表名
WHERE 条件
ORDER BY 排序列
LIMIT 数量;
```

### 查询所有列

```sql
SELECT * FROM users;
```

> `SELECT *` 方便但性能不佳。在实际开发中，应该明确指定需要的列名。

### 查询指定列

```sql
SELECT username, email FROM users;
```

### 给列起别名（AS）

```sql
SELECT
    username AS '用户名',
    email AS '邮箱',
    age AS '年龄'
FROM users;
```

## WHERE 条件过滤

WHERE子句用于筛选符合条件的行。

### 比较运算符

```sql
-- 等于
SELECT * FROM users WHERE age = 25;

-- 不等于（两种写法）
SELECT * FROM users WHERE age != 18;
SELECT * FROM users WHERE age <> 18;

-- 大于、小于
SELECT * FROM users WHERE age > 18;
SELECT * FROM users WHERE age <= 30;
```

### BETWEEN 区间查询

```sql
-- 查询年龄在18到30之间的用户（包含边界）
SELECT * FROM users WHERE age BETWEEN 18 AND 30;
```

### IN 集合查询

```sql
-- 查询指定ID的用户
SELECT * FROM users WHERE id IN (1, 3, 5, 7);

-- IN的子查询用法
SELECT * FROM users WHERE id IN (
    SELECT user_id FROM orders WHERE amount > 1000
);
```

### LIKE 模糊查询

```sql
-- 以'张'开头的用户名
SELECT * FROM users WHERE username LIKE '张%';

-- 包含'test'的邮箱
SELECT * FROM users WHERE email LIKE '%test%';

-- 第二个字是'小'的三个字名字
SELECT * FROM users WHERE username LIKE '_小_';
```

> `%` 匹配任意多个字符，`_` 匹配单个字符。

### IS NULL / IS NOT NULL

```sql
-- 查询没有填写年龄的用户
SELECT * FROM users WHERE age IS NULL;

-- 查询已填写年龄的用户
SELECT * FROM users WHERE age IS NOT NULL;
```

> 注意：不能用 `age = NULL`，必须用 `IS NULL`。

## 逻辑运算符

### AND（与）

```sql
SELECT * FROM users
WHERE age >= 18 AND age <= 30 AND is_active = TRUE;
```

### OR（或）

```sql
SELECT * FROM users
WHERE age < 18 OR age > 60;
```

### NOT（非）

```sql
SELECT * FROM users
WHERE NOT (age BETWEEN 18 AND 30);
```

### 复杂条件组合（注意括号！）

```sql
SELECT * FROM users
WHERE (age >= 18 AND age <= 30)
   OR (is_vip = TRUE AND status = 'active');
```

## ORDER BY 排序

```sql
-- 按年龄升序排列
SELECT * FROM users ORDER BY age ASC;

-- 按年龄降序排列
SELECT * FROM users ORDER BY age DESC;

-- 多字段排序（先按年龄，年龄相同按创建时间）
SELECT * FROM users ORDER BY age DESC, created_at ASC;
```

## LIMIT 限制返回数量

```sql
-- 返回前10条
SELECT * FROM users LIMIT 10;

-- 跳过前20条，返回10条（分页）
SELECT * FROM users LIMIT 20, 10;

-- 另一种分页写法（更易读）
SELECT * FROM users LIMIT 10 OFFSET 20;
```

## 小结

WHERE、ORDER BY和LIMIT是SELECT最常用的三个子句。记住这个顺序：

```
SELECT → FROM → WHERE → ORDER BY → LIMIT
```

下一节我们继续学习聚合函数、分组和高级查询。""",
    },
    {
        "title": "第4节：数据查询SELECT（下）",
        "sort_order": 4,
        "knowledge_point": "高级查询",
        "time_estimate": 30,
        "content": """## 聚合函数

聚合函数对一组值进行计算并返回单个值。

### 常用聚合函数

| 函数 | 说明 | 示例 |
|------|------|------|
| COUNT() | 计数 | `COUNT(*)` 计数所有行 |
| SUM() | 求和 | `SUM(amount)` 总金额 |
| AVG() | 平均值 | `AVG(score)` 平均分 |
| MAX() | 最大值 | `MAX(salary)` 最高薪资 |
| MIN() | 最小值 | `MIN(age)` 最小年龄 |

### COUNT 详解

```sql
-- 统计用户总数
SELECT COUNT(*) FROM users;

-- 统计有年龄信息的用户数（忽略NULL）
SELECT COUNT(age) FROM users;

-- 统计不同的城市数量（去重计数）
SELECT COUNT(DISTINCT city) FROM users;
```

### SUM/AVG/MAX/MIN 示例

```sql
-- 订单总额、平均金额、最高金额、最低金额
SELECT
    SUM(amount) AS total_amount,
    AVG(amount) AS avg_amount,
    MAX(amount) AS max_amount,
    MIN(amount) AS min_amount
FROM orders
WHERE status = 'completed';
```

## GROUP BY 分组

### 基本用法

```sql
-- 按部门分组统计员工人数
SELECT department_id, COUNT(*) AS emp_count
FROM employees
GROUP BY department_id;
```

### GROUP BY 的执行顺序

```
FROM → WHERE → GROUP BY → HAVING → SELECT → ORDER BY → LIMIT
```

**重点**：WHERE 在 GROUP BY 之前过滤行，HAVING 在 GROUP BY 之后过滤分组。

### 分组与聚合的配合

```sql
-- 每个客户的订单数、总金额、平均金额
SELECT
    customer_id,
    COUNT(*) AS order_count,
    SUM(amount) AS total_amount,
    AVG(amount) AS avg_amount
FROM orders
GROUP BY customer_id;
```

## HAVING 过滤分组

```sql
-- 只显示订单总金额超过1000的客户
SELECT
    customer_id,
    SUM(amount) AS total_amount
FROM orders
GROUP BY customer_id
HAVING SUM(amount) > 1000;
```

### WHERE 与 HAVING 的区别

```sql
-- WHERE 过滤行，HAVING 过滤分组
SELECT
    department_id,
    AVG(salary) AS avg_salary
FROM employees
WHERE hire_date >= '2020-01-01'   -- 先过滤：只看2020年后入职的
GROUP BY department_id
HAVING AVG(salary) > 8000;         -- 再过滤：只看平均薪资>8000的部门
```

## DISTINCT 去重

```sql
-- 查询所有不同的城市
SELECT DISTINCT city FROM users;

-- 查询不同的城市和状态组合
SELECT DISTINCT city, status FROM users;
```

## CASE WHEN 条件表达式

```sql
SELECT
    name,
    score,
    CASE
        WHEN score >= 90 THEN '优秀'
        WHEN score >= 80 THEN '良好'
        WHEN score >= 60 THEN '及格'
        ELSE '不及格'
    END AS grade
FROM students;
```

## 综合查询示例

```sql
-- 查询每个分类下的商品数量和平均价格，
-- 只显示商品数量大于3的分类，按平均价格降序排列
SELECT
    category,
    COUNT(*) AS product_count,
    AVG(price) AS avg_price,
    MAX(price) AS max_price,
    MIN(price) AS min_price
FROM products
WHERE is_active = TRUE
GROUP BY category
HAVING COUNT(*) > 3
ORDER BY avg_price DESC
LIMIT 10;
```

## 小结

聚合查询是数据分析的基础。记住执行顺序：WHERE（过滤行）→ GROUP BY（分组）→ HAVING（过滤分组）→ ORDER BY（排序）。""",
    },
    {
        "title": "第5节：数据操作 INSERT UPDATE DELETE",
        "sort_order": 5,
        "knowledge_point": "DML操作",
        "time_estimate": 20,
        "content": """## INSERT 插入数据

### 插入单行

```sql
INSERT INTO users (username, email, age)
VALUES ('zhangsan', 'zhangsan@test.com', 25);
```

### 插入多行

```sql
INSERT INTO users (username, email, age) VALUES
    ('lisi', 'lisi@test.com', 30),
    ('wangwu', 'wangwu@test.com', 28),
    ('zhaoliu', 'zhaoliu@test.com', 22);
```

### 插入所有列（省略列名）

```sql
INSERT INTO users VALUES
    (NULL, 'sunqi', 'sunqi@test.com', 26, TRUE, NOW(), NOW());
```

> 省略列名时，必须按表定义顺序提供所有字段的值。

### INSERT IGNORE（忽略错误）

```sql
INSERT IGNORE INTO users (username, email)
VALUES ('admin', 'admin@test.com');
```

当插入可能违反唯一约束时，`INSERT IGNORE` 会静默跳过而不是报错。

### ON DUPLICATE KEY UPDATE（有则更新）

```sql
INSERT INTO users (username, email, age)
VALUES ('zhangsan', 'zhangsan_new@test.com', 26)
ON DUPLICATE KEY UPDATE email = VALUES(email), age = VALUES(age);
```

如果username已存在，则更新邮箱和年龄；否则插入新记录。

## UPDATE 更新数据

### 基本语法

```sql
UPDATE 表名
SET 列1 = 值1, 列2 = 值2
WHERE 条件;
```

### 更新单列

```sql
UPDATE users SET age = 26 WHERE username = 'zhangsan';
```

### 更新多列

```sql
UPDATE users
SET age = 27, is_active = FALSE
WHERE id = 5;
```

### 使用表达式更新

```sql
-- 所有商品涨价10%
UPDATE products SET price = price * 1.1;

-- 续费会员到期时间延长30天
UPDATE users SET vip_expire = DATE_ADD(vip_expire, INTERVAL 30 DAY)
WHERE is_vip = TRUE;
```

> **危险提示**：不带WHERE的UPDATE会更新**所有行**！执行前务必确认WHERE条件正确。

## DELETE 删除数据

### 基本语法

```sql
DELETE FROM 表名
WHERE 条件;
```

### 删除指定记录

```sql
DELETE FROM orders WHERE status = 'cancelled';
DELETE FROM users WHERE id = 10;
```

### 删除全部记录

```sql
-- 删除表中所有数据（表结构保留）
DELETE FROM orders;

-- 更快地清空表（相当于DROP+CREATE）
TRUNCATE TABLE orders;
```

**DELETE vs TRUNCATE**：
- DELETE：逐行删除，支持WHERE，会触发触发器，可回滚
- TRUNCATE：直接清空，不可回滚，速度更快，重置自增计数器

> **安全第一**：在生产环境执行DELETE/UPDATE前，先 `SELECT` 检查WHERE条件是否正确。

## 数据操作最佳实践

1. **先SELECT后UPDATE/DELETE**：`SELECT * FROM users WHERE id = 10;` 确认后再 `DELETE`
2. **使用事务**：多次操作放在事务中，出错可回滚
3. **备份重要数据**：大批量操作前做好备份
4. **WHERE条件尽量精确**：用主键更新最安全
5. **避免在循环中执行SQL**：批量操作优于逐条操作""",
    },
    {
        "title": "第6节：多表连接查询",
        "sort_order": 6,
        "knowledge_point": "多表连接",
        "time_estimate": 30,
        "content": """## 为什么需要连接查询？

在实际应用中，数据通常分布在多个表中。例如订单信息在orders表，用户信息在users表。要查询"张三的所有订单"，就需要把两个表连接起来。

## 连接的分类

| 连接类型 | 说明 |
|----------|------|
| INNER JOIN | 只返回匹配的行 |
| LEFT JOIN | 返回左表所有行，右表不匹配填NULL |
| RIGHT JOIN | 返回右表所有行，左表不匹配填NULL |
| FULL JOIN | 返回两表所有行（MySQL不直接支持） |
| CROSS JOIN | 笛卡尔积（每行×每行） |
| SELF JOIN | 表自连接 |

## INNER JOIN（内连接）

只返回两表中匹配的行。

```sql
-- 查询用户及其订单
SELECT u.username, o.product_name, o.amount
FROM users u
INNER JOIN orders o ON u.id = o.user_id;

-- 三表连接
SELECT u.username, o.product_name, p.category
FROM users u
INNER JOIN orders o ON u.id = o.user_id
INNER JOIN products p ON o.product_id = p.id;
```

## LEFT JOIN（左外连接）

返回左表中的所有行，右表无匹配的行用NULL填充。

```sql
-- 查询所有用户及其订单（包括没有订单的用户）
SELECT u.username, o.product_name, o.amount
FROM users u
LEFT JOIN orders o ON u.id = o.user_id;

-- 查找没有订单的用户
SELECT u.username
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
WHERE o.id IS NULL;
```

## 连接查询的执行过程

以 `A LEFT JOIN B ON A.id = B.a_id` 为例：

1. 从A表取第一行
2. 扫描B表，找所有 B.a_id = A.id 的行
3. 如果有匹配：返回 A行+B行
4. 如果无匹配：返回 A行+NULL（因为是LEFT JOIN）
5. 继续下一行A...

## 连接查询 vs 子查询

**连接查询**（JOIN）：

```sql
SELECT u.username, o.product_name
FROM users u
INNER JOIN orders o ON u.id = o.user_id
WHERE o.amount > 100;
```

**子查询**：

```sql
SELECT username
FROM users
WHERE id IN (
    SELECT user_id FROM orders WHERE amount > 100
);
```

**如何选择**：
- 需要显示两个表的字段 → **用JOIN**
- 只需要一个表的字段，用另一个表做筛选 → **两者都可以**，视情况而定
- 子查询分为相关子查询和非相关子查询，后者通常更高效

## 连接查询最佳实践

1. **使用表别名**：`FROM users u` 而不是 `FROM users`
2. **ON条件明确**：`ON u.id = o.user_id`
3. **INNER JOIN优先**：如果不需要NULL行
4. **避免笛卡尔积**：FROM多表不加ON会产生所有组合

```sql
-- 错误：笛卡尔积！1000个用户 × 5000个订单 = 500万行
SELECT * FROM users, orders;

-- 正确：加连接条件
SELECT * FROM users u INNER JOIN orders o ON u.id = o.user_id;
```

5. **用EXPLAIN分析查询**：

```sql
EXPLAIN SELECT u.username, o.product_name
FROM users u
LEFT JOIN orders o ON u.id = o.user_id;
```

## 小结

- 取交集用INNER JOIN
- 以某表为基准用LEFT/RIGHT JOIN
- 需要两个表的数据显示在一起用JOIN
- 筛选条件用子查询""",
    },
    {
        "title": "第7节：子查询",
        "sort_order": 7,
        "knowledge_point": "子查询",
        "time_estimate": 25,
        "content": """## 什么是子查询？

子查询是嵌套在另一个SQL语句内部的查询。子查询的结果被外层查询使用。

```sql
SELECT username
FROM users
WHERE id IN (
    SELECT user_id FROM orders WHERE amount > 1000
);
```

内层 `SELECT user_id FROM orders WHERE amount > 1000` 先执行，返回高消费用户的ID列表，外层再用这个列表筛选用户。

## 子查询的分类

### 按位置分类

| 位置 | 示例 |
|------|------|
| WHERE子句中 | `WHERE id IN (SELECT ...)` |
| SELECT子句中 | `SELECT name, (SELECT ...) AS cnt` |
| FROM子句中 | `FROM (SELECT ...) AS sub` |

### 按与外部查询的关系分类

| 类型 | 说明 |
|------|------|
| 非相关子查询 | 子查询独立执行，不依赖外部查询 |
| 相关子查询 | 子查询引用外部查询的列，外部每行都要执行子查询 |

## 非相关子查询

### 标量子查询（返回单个值）

```sql
-- 查询薪资高于平均薪资的员工
SELECT name, salary
FROM employees
WHERE salary > (SELECT AVG(salary) FROM employees);
```

### 列子查询（返回一列多行）

```sql
-- IN
SELECT name FROM employees
WHERE department_id IN (
    SELECT id FROM departments WHERE location = '北京'
);

-- NOT IN
SELECT name FROM employees
WHERE department_id NOT IN (
    SELECT id FROM departments WHERE is_active = FALSE
);

-- ANY/ALL
SELECT name, salary FROM employees
WHERE salary > ALL (SELECT salary FROM employees WHERE department_id = 3);
-- 比3号部门所有人的薪资都高
```

## 相关子查询

相关子查询引用外部查询的列，对外部查询的每一行都要执行一次子查询。

```sql
-- 查询薪资高于本部门平均薪资的员工
SELECT name, salary, department_id
FROM employees e
WHERE salary > (
    SELECT AVG(salary)
    FROM employees
    WHERE department_id = e.department_id  -- 引用了外部e的department_id
);
```

执行过程：
1. 取employees表第1行（如张三，部门1，薪资8000）
2. 执行子查询：SELECT AVG(salary) FROM employees WHERE department_id = 1（得到7000）
3. 比较：8000 > 7000，张三入选
4. 取第2行，重复2-3...

## EXISTS / NOT EXISTS

```sql
-- 查询有订单的用户
SELECT username
FROM users u
WHERE EXISTS (
    SELECT 1 FROM orders o WHERE o.user_id = u.id
);

-- 查询没有订单的用户
SELECT username
FROM users u
WHERE NOT EXISTS (
    SELECT 1 FROM orders o WHERE o.user_id = u.id
);
```

> EXISTS只检查子查询是否有结果，不关心返回值，所以子查询中 `SELECT 1` 或 `SELECT *` 都可以。

## FROM中的子查询（派生表）

```sql
SELECT dept_name, avg_salary
FROM (
    SELECT d.name AS dept_name, AVG(e.salary) AS avg_salary
    FROM employees e
    INNER JOIN departments d ON e.department_id = d.id
    GROUP BY d.id, d.name
) AS dept_stats
WHERE avg_salary > 8000;
```

## 子查询的性能注意事项

1. **非相关子查询通常比相关子查询快**（因为只执行一次）
2. **IN + 子查询**可能很慢，改用JOIN或EXISTS
3. **避免在SELECT中使用子查询**（每行执行一次）
4. **使用EXPLAIN查看执行计划**

```sql
-- 慢（每行执行子查询）
SELECT name, (SELECT COUNT(*) FROM orders WHERE user_id = u.id) AS order_cnt
FROM users u;

-- 快（用JOIN替代）
SELECT u.name, COUNT(o.id) AS order_cnt
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
GROUP BY u.id, u.name;
```

## 小结

子查询是SQL中强大的工具，但要谨慎使用。优先考虑：
1. JOIN 替代 子查询
2. 非相关子查询 替代 相关子查询
3. EXISTS 替代 IN（特别是大数据量时）""",
    },
    {
        "title": "第8节：索引与事务",
        "sort_order": 8,
        "knowledge_point": "索引与事务",
        "time_estimate": 25,
        "content": """## 索引（Index）

索引就像一本书的目录，能帮助数据库快速定位到需要的数据，而不必扫描整张表。

### 没有索引 vs 有索引

```
没有索引（全表扫描）：
查询 id=999 的记录 → 从第1行扫描到第999行 → O(n)

有索引（B+Tree）：
查询 id=999 的记录 → 通过索引树快速定位 → O(log n)
```

### 创建索引

```sql
-- 普通索引
CREATE INDEX idx_username ON users(username);

-- 唯一索引（值不能重复）
CREATE UNIQUE INDEX idx_email ON users(email);

-- 联合索引
CREATE INDEX idx_name_age ON users(username, age);

-- 建表时创建
CREATE TABLE users (
    id INT PRIMARY KEY,
    username VARCHAR(50),
    INDEX idx_username (username)
);
```

### 索引的使用原则

**应该创建索引的场景**：
- WHERE条件中频繁使用的列
- JOIN连接的列
- ORDER BY和GROUP BY的列
- 区分度高的列（如邮箱、手机号）

**不应该创建索引的场景**：
- 区分度低的列（如性别只有男/女）
- 频繁更新的列（维护索引有开销）
- 小表（全表扫描可能更快）
- TEXT/BLOB大字段

### 查看索引使用情况

```sql
-- 查看查询是否使用了索引
EXPLAIN SELECT * FROM users WHERE email = 'test@test.com';

-- 查看表上所有索引
SHOW INDEX FROM users;
```

### 索引优化口诀

> **最左前缀原则**：对于联合索引 `(a, b, c)`，查询条件必须从a开始才能使用索引。`WHERE a=1 AND b=2` 可以用索引，`WHERE b=2 AND c=3` 不能用。

## 事务（Transaction）

事务是一组不可分割的数据库操作，要么全部成功，要么全部失败回滚。

### ACID特性

| 特性 | 说明 | 举例 |
|------|------|------|
| **A**tomacity（原子性） | 操作不可分割 | 转账：扣钱+加钱必须同时成功 |
| **C**onsistency（一致性） | 数据前后一致 | 转账后总金额不变 |
| **I**solation（隔离性） | 事务间不干扰 | 两人同时转账不互相影响 |
| **D**urability（持久性） | 提交后永久保存 | 断电后数据不丢失 |

### 事务的基本操作

```sql
-- 开始事务
START TRANSACTION;
-- 或
BEGIN;

-- 执行操作
UPDATE accounts SET balance = balance - 100 WHERE id = 1;
UPDATE accounts SET balance = balance + 100 WHERE id = 2;

-- 提交（确认操作）
COMMIT;

-- 或回滚（撤销操作）
ROLLBACK;
```

### 转账示例

```sql
START TRANSACTION;

-- 检查余额是否足够
SELECT balance INTO @bal FROM accounts WHERE id = 1;
IF @bal < 100 THEN
    ROLLBACK;
END IF;

-- 扣钱
UPDATE accounts SET balance = balance - 100 WHERE id = 1;

-- 加钱
UPDATE accounts SET balance = balance + 100 WHERE id = 2;

-- 确认
COMMIT;
```

### 事务隔离级别

| 级别 | 脏读 | 不可重复读 | 幻读 |
|------|------|-----------|------|
| READ UNCOMMITTED | 可能 | 可能 | 可能 |
| READ COMMITTED | 不会 | 可能 | 可能 |
| REPEATABLE READ（MySQL默认） | 不会 | 不会 | 可能 |
| SERIALIZABLE | 不会 | 不会 | 不会 |

```sql
-- 查看当前隔离级别
SELECT @@transaction_isolation;

-- 设置隔离级别
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
```

## 小结

- **索引**：为WHERE/JOIN/ORDER BY的列创建，提高查询速度
- **事务**：保证数据一致性，用COMMIT确认，用ROLLBACK撤销
- **隔离级别**：越高越安全但性能越差，默认REPEATABLE READ即可""",
    },
]

# ============================================================
# Python编程基础
# ============================================================
LESSON_CONTENT["Python编程基础"] = [
    {
        "title": "第1节：Python环境搭建与基础语法",
        "sort_order": 1,
        "knowledge_point": "Python环境",
        "time_estimate": 20,
        "content": """## Python简介

Python是一种**解释型、面向对象、动态类型**的高级编程语言。由Guido van Rossum于1991年创建。

### Python的特点

| 特点 | 说明 |
|------|------|
| 简洁易读 | 语法清晰，使用缩进定义代码块 |
| 解释型 | 逐行执行，无需编译 |
| 动态类型 | 变量无需声明类型 |
| 丰富的库 | "Batteries Included"（自带电池）理念 |
| 跨平台 | Windows/Linux/Mac都能运行 |

### Python版本选择

目前主要使用Python 3.x。Python 2已于2020年停止维护。

```
Python 3.10+ ← 推荐使用
Python 3.8/3.9 ← 稳定版本
Python 2.7 ← 已废弃，不要用
```

## 安装Python

### Windows

1. 访问 https://www.python.org/downloads/
2. 下载最新版安装包
3. **重要**：勾选 "Add Python to PATH"
4. 点击 Install Now

验证安装：
```bash
python --version
# Python 3.10.x
```

### pip包管理器

pip是Python的包管理器，用来安装第三方库：

```bash
# 安装包
pip install requests
pip install pytest

# 查看已安装的包
pip list

# 卸载包
pip uninstall requests

# 安装指定版本
pip install django==4.2.0
```

## 第一个Python程序

创建文件 `hello.py`：
```python
# 这是我的第一个Python程序
print("Hello, World!")
print("欢迎来到Python世界！")
```

运行：
```bash
python hello.py
```

## Python基础语法

### 注释

```python
# 这是单行注释

'''
这是多行注释（docstring）
可以写多行内容
'''

'''
这也是多行注释
用单引号的版本
'''
```

### 缩进

Python使用**缩进**定义代码块，通常用4个空格。

```python
if True:
    print("这行有缩进，属于if块")
    print("这行也是if块的内容")
print("这行没有缩进，不属于if块")
```

> 混用Tab和空格会导致 `IndentationError`，建议统一使用4个空格。

### 标识符命名规则

- 由字母、数字、下划线组成
- 不能以数字开头
- 区分大小写（name 和 Name 不同）
- 不能使用关键字（如 if、for、class 等）

### 命名规范（PEP 8）

```python
my_variable = 10        # 变量：蛇形命名法（snake_case）
MY_CONSTANT = 100       # 常量：全大写
my_function()           # 函数：蛇形命名法
MyClass                 # 类：驼峰命名（PascalCase）
__private_var           # 私有：双下划线前缀
```

### print() 函数

```python
# 基本用法
print("Hello")

# 打印多个值
print("姓名：", "张三", "年龄：", 25)

# 自定义分隔符
print("a", "b", "c", sep="-")  # 输出：a-b-c

# 不换行
print("Loading...", end="")
print("Done!")  # 输出：Loading...Done!

# f-string格式化（Python 3.6+）
name = "张三"
age = 25
print(f"我叫{name}，今年{age}岁")
```

## 交互式编程（REPL）

在命令行输入 `python` 进入交互模式：

```python
>>> 2 + 3
5
>>> print("Hello")
Hello
>>> name = "Python"
>>> len(name)
6
>>> exit()  # 退出
```

## 小结

环境搭建好后，你可以在命令行用 `python` 交互式学习，也可以写 `.py` 文件运行。多动手实践是最好的学习方式！""",
    },
    {
        "title": "第2节：变量与数据类型",
        "sort_order": 2,
        "knowledge_point": "变量与数据类型",
        "time_estimate": 25,
        "content": """## 变量

Python中变量不需要声明类型，直接赋值即可。

```python
name = "张三"       # 字符串
age = 25             # 整数
height = 1.75        # 浮点数
is_student = True    # 布尔值
```

### 变量的本质

Python中的变量是**对象的引用**（标签），而不是存储数据的容器。

```python
a = [1, 2, 3]
b = a           # b和a指向同一个列表对象
b.append(4)
print(a)        # [1, 2, 3, 4]  ← a也变了！
```

### 多重赋值

```python
# 同时给多个变量赋值
x, y, z = 1, 2, 3

# 交换变量的值（不需要中间变量！）
a, b = b, a
```

## 数值类型

### 整数（int）

Python 3中整数无大小限制（只受内存限制）。

```python
a = 10
b = -5
c = 0
d = 1_000_000     # 下划线增强可读性（Python 3.6+）
e = 0xFF          # 十六进制 = 255
f = 0o77          # 八进制 = 63
g = 0b1010        # 二进制 = 10
```

### 浮点数（float）

```python
pi = 3.14159
e = 2.71828
negative = -1.5
scientific = 1.5e3  # 1500.0
```

> 浮点数精度问题：`0.1 + 0.2` 不等于 `0.3`，这是所有编程语言的共同问题，不是Python的bug。

### 数值运算

```python
5 + 3    # 加法：8
5 - 3    # 减法：2
5 * 3    # 乘法：15
5 / 3    # 除法：1.666...
5 // 3   # 整除：1
5 % 3    # 取余：2
5 ** 3   # 幂运算：125
```

## 字符串（str）

字符串是不可变的字符序列。

```python
# 创建字符串
s1 = '单引号'
s2 = "双引号"     
s3 = '''三引号可以
跨多行'''
```

### 字符串操作

```python
s = "Hello, Python"

# 索引（从0开始）
s[0]     # 'H'
s[-1]    # 'n'（倒数第一个）
s[-2]    # 'o'（倒数第二个）

# 切片 [start:end:step]
s[0:5]   # 'Hello'（不包括索引5）
s[7:]    # 'Python'（从7到末尾）
s[:5]    # 'Hello'（从开头到5）
s[::2]   # 'Hlo yhn'（步长为2）
s[::-1]  # 'nohtyP ,olleH'（反转）

# 长度
len(s)   # 14

# 包含判断
'Py' in s       # True
'Java' in s     # False
'Java' not in s # True
```

### 常用字符串方法

```python
s = "  Hello, World!  "

s.strip()            # 去首尾空格 → 'Hello, World!'
s.upper()            # 全大写 → '  HELLO, WORLD!  '
s.lower()            # 全小写 → '  hello, world!  '
s.replace('World', 'Python')  # 替换 → '  Hello, Python!  '
s.split(',')         # 分割 → ['  Hello', ' World!  ']
'-'.join(['a','b'])  # 连接 → 'a-b'
s.find('World')      # 查找位置 → 9
s.count('l')         # 计数 → 3
s.startswith('  H')  # 以...开头 → True
```

### f-string 格式化

```python
name = "张三"
age = 25
score = 92.5

print(f"姓名：{name}，年龄：{age}，成绩：{score}")
print(f"成绩：{score:.1f}")     # 保留1位小数 → 成绩：92.5
print(f"进度：{3/7:.1%}")       # 百分比 → 进度：42.9%
```

## 布尔类型（bool）

```python
is_active = True
is_deleted = False

# 布尔运算
True and False   # False
True or False    # True
not True         # False

# 比较运算
5 > 3            # True
5 == 5           # True
5 != 3           # True
5 >= 5           # True
```

### 真值测试

以下值在布尔上下文中被视为 `False`：
- `None`
- `False`
- `0`、`0.0`、`0j`
- `''`（空字符串）
- `[]`（空列表）
- `{}`（空字典）
- `()`（空元组）

其他所有值都视为 `True`。

## 类型转换

```python
int('123')       # 字符串→整数：123
str(123)         # 整数→字符串：'123'
float('3.14')    # 字符串→浮点数：3.14
bool(1)          # 整数→布尔：True
bool(0)          # 整数→布尔：False
bool('hello')    # 非空字符串→布尔：True
```

## 小结

Python有四大基本数据类型：**int、float、str、bool**。变量是动态类型的，不需要声明。下节课我们将学习列表、字典等复合数据类型。""",
    },
    {
        "title": "第3节：条件判断与循环",
        "sort_order": 3,
        "knowledge_point": "流程控制",
        "time_estimate": 25,
        "content": """## if 条件判断

### 基本语法

```python
if 条件:
    代码块
elif 其他条件:
    代码块
else:
    代码块
```

### 示例

```python
score = 85

if score >= 90:
    grade = 'A'
elif score >= 80:
    grade = 'B'
elif score >= 70:
    grade = 'C'
elif score >= 60:
    grade = 'D'
else:
    grade = 'F'

print(f"成绩等级：{grade}")  # 成绩等级：B
```

### 三元表达式（条件表达式）

```python
# 如果score>=60，result='及格'，否则='不及格'
result = '及格' if score >= 60 else '不及格'

# 等价于
if score >= 60:
    result = '及格'
else:
    result = '不及格'
```

### 条件组合

```python
age = 25
is_vip = True

# and：两个条件都满足
if age >= 18 and is_vip:
    print("VIP成年用户")

# or：任一条件满足
if age < 18 or age > 60:
    print("特殊年龄段")

# not：条件取反
if not is_vip:
    print("非VIP用户")

# 链式比较（Python独有）
if 18 <= age <= 30:
    print("青年用户")
```

## for 循环

Python的for循环用于遍历**可迭代对象**（列表、字符串、range等）。

### 遍历列表

```python
fruits = ['apple', 'banana', 'orange']

for fruit in fruits:
    print(fruit)
# apple
# banana
# orange
```

### range() 生成数字序列

```python
# range(stop)：0 到 stop-1
for i in range(5):
    print(i, end=' ')   # 0 1 2 3 4

# range(start, stop)
for i in range(1, 5):
    print(i, end=' ')   # 1 2 3 4

# range(start, stop, step)
for i in range(1, 10, 2):
    print(i, end=' ')   # 1 3 5 7 9

# 倒序
for i in range(10, 0, -1):
    print(i, end=' ')   # 10 9 8 7 6 5 4 3 2 1
```

### enumerate() 同时获取索引和值

```python
fruits = ['apple', 'banana', 'orange']

for index, fruit in enumerate(fruits):
    print(f"{index}: {fruit}")
# 0: apple
# 1: banana
# 2: orange

# 指定起始索引
for index, fruit in enumerate(fruits, start=1):
    print(f"{index}: {fruit}")
# 1: apple
# 2: banana
# 3: orange
```

### zip() 并行遍历

```python
names = ['张三', '李四', '王五']
scores = [85, 92, 78]

for name, score in zip(names, scores):
    print(f"{name}: {score}")
# 张三: 85
# 李四: 92
# 王五: 78
```

## while 循环

```python
# 基本用法
count = 0
while count < 5:
    print(count, end=' ')
    count += 1
# 0 1 2 3 4
```

### while True（无限循环）

```python
while True:
    user_input = input("请输入 'quit' 退出：")
    if user_input == 'quit':
        break
    print(f"你输入了：{user_input}")
```

## break 和 continue

```python
# break：跳出整个循环
for i in range(10):
    if i == 5:
        break
    print(i, end=' ')
# 0 1 2 3 4

# continue：跳过当前迭代，继续下一次
for i in range(10):
    if i % 2 == 0:  # 跳过偶数
        continue
    print(i, end=' ')
# 1 3 5 7 9
```

## 循环的 else 子句（Python特有）

当循环**正常结束**（没有被break中断）时执行else块：

```python
# 查找是否存在
for i in range(10):
    if i == 20:
        print("找到了")
        break
else:
    print("循环正常结束，没找到")  # 会被执行
```

## 综合示例：九九乘法表

```python
for i in range(1, 10):
    for j in range(1, i + 1):
        print(f"{j}×{i}={i*j}", end='\t')
    print()  # 换行
```

## 小结

- **if/elif/else** 用于条件分支
- **for** 用于遍历可迭代对象（最常用）
- **while** 用于条件循环
- **break** 跳出循环，**continue** 跳过当前迭代
- **range** 生成数字序列，**enumerate** 获取索引""",
    },
    {
        "title": "第4节：列表与元组",
        "sort_order": 4,
        "knowledge_point": "列表元组",
        "time_estimate": 25,
        "content": """## 列表（List）

列表是Python中最常用的数据结构，用于存储**有序的、可变的**元素集合。

```python
# 创建列表
empty_list = []
numbers = [1, 2, 3, 4, 5]
mixed = [1, "hello", 3.14, True]  # 可以混合不同类型
nested = [1, [2, 3], [4, 5, 6]]   # 可以嵌套
```

### 列表的基本操作

```python
fruits = ['apple', 'banana', 'orange']

# 索引（从0开始）
fruits[0]      # 'apple'
fruits[-1]     # 'orange'

# 切片（返回新列表）
fruits[0:2]    # ['apple', 'banana']
fruits[1:]     # ['banana', 'orange']

# 长度
len(fruits)    # 3

# 判断元素是否存在
'apple' in fruits      # True
'grape' not in fruits  # True
```

### 修改列表

```python
fruits = ['apple', 'banana', 'orange']

fruits[1] = 'grape'        # 修改 → ['apple', 'grape', 'orange']

fruits.append('melon')     # 末尾添加 → ['apple', 'grape', 'orange', 'melon']

fruits.insert(1, 'kiwi')   # 指定位置插入 → [...'kiwi', 'grape'...]

fruits.remove('grape')     # 删除指定元素（只删第一个）

popped = fruits.pop()      # 删除并返回最后一个元素
popped = fruits.pop(0)     # 删除并返回指定位置元素

del fruits[0]              # 删除指定位置元素

fruits.clear()             # 清空列表
```

### 列表的高级操作

```python
a = [1, 2, 3]
b = [4, 5, 6]

# 拼接
c = a + b              # [1, 2, 3, 4, 5, 6]

# 重复
d = a * 3              # [1, 2, 3, 1, 2, 3, 1, 2, 3]

# extend：将b的元素添加到a
a.extend(b)            # a变成 [1, 2, 3, 4, 5, 6]

# 排序
numbers = [3, 1, 4, 1, 5, 9]
numbers.sort()                    # 原地排序 → [1, 1, 3, 4, 5, 9]
numbers.sort(reverse=True)        # 降序 → [9, 5, 4, 3, 1, 1]

sorted_numbers = sorted(numbers)  # 返回新排序列表（不改变原列表）

# 反转
numbers.reverse()                 # 原地反转

# 查找索引
numbers.index(4)                  # 元素的索引位置

# 计数
numbers.count(1)                  # 1出现了几次 → 2
```

### 列表推导式（List Comprehension）

这是Python最强大的特性之一：

```python
# 基本形式：[表达式 for 变量 in 可迭代对象]

squares = [x**2 for x in range(10)]
# [0, 1, 4, 9, 16, 25, 36, 49, 64, 81]

# 带条件过滤
evens = [x for x in range(20) if x % 2 == 0]
# [0, 2, 4, 6, 8, 10, 12, 14, 16, 18]

# 嵌套循环
pairs = [(x, y) for x in range(3) for y in range(2)]
# [(0,0), (0,1), (1,0), (1,1), (2,0), (2,1)]
```

> 列表推导式不仅简洁，通常还比传统for循环快。

## 元组（Tuple）

元组和列表类似，但元组是**不可变的**（创建后不能修改）。

```python
# 创建元组
t1 = (1, 2, 3)
t2 = 1, 2, 3          # 括号可以省略
t3 = (1,)             # 单元素元组（逗号不能省略！）
t4 = ()               # 空元组

# 元组支持的操作
t1[0]                 # 索引 → 1
t1[1:]                # 切片 → (2, 3)
len(t1)               # 长度 → 3
1 in t1               # 判断 → True
t1 + t2               # 拼接 → (1,2,3,1,2,3)

# 元组不能修改！
# t1[0] = 5  ← 错误！TypeError
```

### 什么时候用元组？

| 场景 | 用列表还是元组？ |
|------|-----------------|
| 数据会改变 | 列表 |
| 数据不变 | 元组 |
| 函数返回多个值 | 元组 |
| 字典的键 | 元组（列表可变不能作为键） |
| 坐标、RGB颜色等 | 元组 |

### 元组解包

```python
# 基本解包
point = (3, 4)
x, y = point
print(x)  # 3
print(y)  # 4

# 交换变量（前面提过）
a, b = b, a

# 星号解包
first, *middle, last = [1, 2, 3, 4, 5]
print(first)   # 1
print(middle)  # [2, 3, 4]
print(last)    # 5
```

## 小结

- **列表**：[1, 2, 3] 可变，用于存储会变化的数据
- **元组**：(1, 2, 3) 不可变，用于存储不会变化的数据
- **列表推导式**：[x for x in range(10)] 是Python的特色语法，推荐掌握

下节课学习字典（dict）和集合（set）。""",
    },
    {
        "title": "第5节：字典与集合",
        "sort_order": 5,
        "knowledge_point": "字典集合",
        "time_estimate": 25,
        "content": """## 字典（Dictionary）

字典是Python中的键值对（key-value）数据结构，用于存储关联数据。

```python
# 创建字典
empty_dict = {}
user = {
    'name': '张三',
    'age': 25,
    'email': 'zhangsan@test.com'
}

# 使用dict()创建
user2 = dict(name='李四', age=30)
```

### 字典的基本操作

```python
user = {'name': '张三', 'age': 25}

# 取值
user['name']           # '张三'
user.get('name')       # '张三'
user.get('phone', 'N/A')  # 不存在返回默认值 → 'N/A'

# 修改/添加
user['age'] = 26                    # 修改
user['phone'] = '13800138000'       # 添加新键

# 删除
del user['phone']       # 删除指定键
popped = user.pop('age') # 删除并返回值
user.popitem()           # 删除并返回最后一个键值对（Python 3.7+）
user.clear()             # 清空
```

### 字典的遍历

```python
user = {'name': '张三', 'age': 25, 'email': 'zhangsan@test.com'}

# 遍历键
for key in user:
    print(key)

# 遍历值
for value in user.values():
    print(value)

# 遍历键值对
for key, value in user.items():
    print(f"{key}: {value}")

# 用解包遍历
for item in user.items():
    key, value = item
    print(f"{key}: {value}")
```

### 字典推导式

```python
# 键值对互换
original = {'a': 1, 'b': 2, 'c': 3}
swapped = {v: k for k, v in original.items()}
# {1: 'a', 2: 'b', 3: 'c'}

# 过滤
scores = {'张三': 85, '李四': 92, '王五': 58, '赵六': 73}
passed = {k: v for k, v in scores.items() if v >= 60}
# {'张三': 85, '李四': 92, '赵六': 73}
```

### 字典的高级用法

```python
# 合并字典（Python 3.9+）
d1 = {'a': 1, 'b': 2}
d2 = {'b': 3, 'c': 4}
merged = d1 | d2  # {'a': 1, 'b': 3, 'c': 4}

# setdefault（设置默认值）
user = {'name': '张三'}
user.setdefault('level', 1)  # user变成 {'name': '张三', 'level': 1}
user.setdefault('level', 5)  # level已经存在，不改变

# 用字典实现switch-case
def handle_a():
    return "处理A"

def handle_b():
    return "处理B"

actions = {
    'A': handle_a,
    'B': handle_b,
}

result = actions.get(input_type, handle_default)()
```

## 集合（Set）

集合是**无序的、不重复的**元素集合。

```python
# 创建集合
empty_set = set()        # 重要：不能用{}，那是字典！
numbers = {1, 2, 3, 4}   # 集合字面量
chars = set('hello')     # {'h', 'e', 'l', 'o'} 注意去重了
```

### 集合操作

```python
# 添加和删除
numbers.add(5)           # 添加一个
numbers.remove(3)        # 删除（不存在会报错）
numbers.discard(10)      # 删除（不存在不报错）
numbers.pop()            # 随机删除一个（因为无序）

# 成员检查（O(1)时间复杂度！）
3 in numbers             # True（比列表快得多）
```

### 集合运算（数学集合操作）

```python
a = {1, 2, 3, 4}
b = {3, 4, 5, 6}

# 交集
a & b           # {3, 4}
a.intersection(b)

# 并集
a | b           # {1, 2, 3, 4, 5, 6}
a.union(b)

# 差集
a - b           # {1, 2}（a中有b中没有的）
a.difference(b)

# 对称差集
a ^ b           # {1, 2, 5, 6}（各自独有的）
a.symmetric_difference(b)

# 子集/超集
{1, 2}.issubset(a)       # True
a.issuperset({1, 2})     # True
```

### 集合推导式

```python
# 与列表推导式类似，用{}即可
squares = {x**2 for x in range(10)}
# {0, 1, 64, 4, 36, 9, 16, 49, 81, 25}（无序）

# 去重
numbers = [1, 2, 2, 3, 3, 3, 4]
unique = list(set(numbers))  # [1, 2, 3, 4]

# 但要保留顺序的去重：
unique_ordered = list(dict.fromkeys(numbers))
```

### 何时用集合？

- **去重**：`list(set(my_list))`
- **成员检查**：`if item in my_set:`（比列表快100倍）
- **集合运算**：交集、并集、差集
- **统计不重复元素**

## 小结

| 数据类型 | 符号 | 有序？ | 可变？ | 可重复？ |
|----------|------|--------|--------|----------|
| list | [] | 有序 | 可变 | 可重复 |
| tuple | () | 有序 | 不可变 | 可重复 |
| dict | {:} | 有序（3.7+）| 可变 | 键不可重复 |
| set | {} | 无序 | 可变 | 不可重复 |

选择经验：有对应关系用**字典**，要顺序用**列表**，要唯一性用**集合**，不变的数据用**元组**。""",
    },
    {
        "title": "第6节：函数",
        "sort_order": 6,
        "knowledge_point": "函数",
        "time_estimate": 30,
        "content": """## 函数的定义

函数是组织好的、可重复使用的代码块，用于实现单一功能。

```python
def 函数名(参数1, 参数2, ...):
    '''文档字符串（docstring）'''
    函数体
    return 返回值
```

### 最简单的函数

```python
def greet():
    print("Hello, World!")

# 调用函数
greet()  # Hello, World!
```

### 带参数和返回值的函数

```python
def add(a, b):
    '''返回两个数的和'''
    return a + b

result = add(3, 5)   # result = 8
print(add(10, 20))   # 30
```

## 参数类型

### 位置参数

```python
def describe(name, age):
    print(f"{name}今年{age}岁")

describe('张三', 25)   # 张三今年25岁
# describe(25, '张三') ← 错误的顺序！
```

### 关键字参数

```python
def describe(name, age):
    print(f"{name}今年{age}岁")

describe(age=25, name='张三')  # 不依赖顺序
```

### 默认参数

```python
def greet(name, greeting='Hello'):
    print(f"{greeting}, {name}!")

greet('张三')                    # Hello, 张三!
greet('李四', greeting='你好')   # 你好, 李四!

# 默认参数陷阱：不要用可变对象作为默认值
def bad_append(item, lst=[]):   # 危险！
    lst.append(item)
    return lst

print(bad_append(1))  # [1]
print(bad_append(2))  # [1, 2] ← 累积了！

def good_append(item, lst=None):  # 正确的做法
    if lst is None:
        lst = []
    lst.append(item)
    return lst
```

### 可变参数（*args）

```python
def sum_all(*numbers):
    '''接收任意数量的参数'''
    return sum(numbers)

print(sum_all(1, 2, 3))          # 6
print(sum_all(1, 2, 3, 4, 5))    # 15

# *args 收集多余的位置参数为元组
def func(a, b, *args):
    print(f"a={a}, b={b}, args={args}")

func(1, 2, 3, 4, 5)  # a=1, b=2, args=(3, 4, 5)
```

### 关键字可变参数（**kwargs）

```python
def print_info(**kwargs):
    '''接收任意数量的关键字参数'''
    for key, value in kwargs.items():
        print(f"{key}: {value}")

print_info(name='张三', age=25, city='北京')
# name: 张三
# age: 25
# city: 北京
```

### 参数顺序规则

```python
def func(普通参数, *args, 默认参数=值, **kwargs):
    pass

# 调用时也要遵循：
func(arg1, arg2, *list, kwarg1=val, **dict)
```

## 返回值

```python
# 单返回值
def square(x):
    return x ** 2

# 多返回值（实际返回元组）
def min_max(numbers):
    return min(numbers), max(numbers)

low, high = min_max([3, 1, 4, 1, 5])  # low=1, high=5

# 无return → 返回None
def do_nothing():
    pass

result = do_nothing()   # result is None
```

## 作用域（Scope）

```python
# LEGB 规则：Local → Enclosing → Global → Built-in

x = 'global'  # 全局变量

def outer():
    x = 'enclosing'  # 外部函数的局部变量
    
    def inner():
        x = 'local'  # 内部函数的局部变量
        print(x)     # local
    
    inner()
    print(x)         # enclosing

outer()
print(x)             # global
```

### global 和 nonlocal

```python
count = 0

def increment():
    global count   # 声明使用全局变量
    count += 1

def outer():
    x = 10
    def inner():
        nonlocal x  # 声明使用外层函数的变量
        x += 1
    inner()
    print(x)  # 11
```

## lambda 匿名函数

```python
# lambda 参数: 表达式
square = lambda x: x ** 2
print(square(5))  # 25

# lambda 的常见用途
numbers = [3, 1, 4, 1, 5]

# sorted的key参数
sorted_users = sorted(users, key=lambda u: u['age'])

# map/filter
doubled = list(map(lambda x: x * 2, numbers))
evens = list(filter(lambda x: x % 2 == 0, numbers))
```

## docstring

```python
def calculate_bmi(weight, height):
    '''
    计算BMI指数。
    
    Args:
        weight: 体重（千克）
        height: 身高（米）
    
    Returns:
        BMI值（浮点数）
    
    Raises:
        ValueError: 如果身高或体重为非正值
    '''
    if weight <= 0 or height <= 0:
        raise ValueError("体重和身高必须为正数")
    return weight / (height ** 2)

# 查看文档
help(calculate_bmi)
print(calculate_bmi.__doc__)
```

## 小结

- **def** 定义函数，**return** 返回值
- **参数类型**：位置、关键字、默认、*args、**kwargs
- **lambda** 用于简短的匿名函数
- 默认参数不要用可变对象
- 写好 **docstring** 是个好习惯""",
    },
    {
        "title": "第7节：面向对象编程",
        "sort_order": 7,
        "knowledge_point": "面向对象",
        "time_estimate": 30,
        "content": """## 面向对象编程概述

面向对象编程（OOP）是一种将**数据（属性）**和**行为（方法）**封装在一起组织代码的编程范式。

### 为什么需要OOP？

```python
# 面向过程的方式
def calculate_area_rectangle(width, height):
    return width * height

def calculate_perimeter_rectangle(width, height):
    return 2 * (width + height)

# 面向对象的方式
class Rectangle:
    def __init__(self, width, height):
        self.width = width
        self.height = height
    
    def area(self):
        return self.width * self.height
    
    def perimeter(self):
        return 2 * (self.width + self.height)

# 使用
rect = Rectangle(5, 3)
print(rect.area())       # 15
print(rect.perimeter())  # 16
```

## 类的定义

```python
class 类名:
    '''类的文档字符串'''
    
    # 类属性（所有实例共享）
    类属性 = 值
    
    # 构造方法
    def __init__(self, 参数...):
        self.实例属性 = 值  # 实例属性（每个实例独有）
    
    # 实例方法
    def 方法名(self, 参数...):
        # self 指向当前实例
        pass
```

### 实际示例：TestCase类

```python
class TestCase:
    '''测试用例类'''
    
    total_cases = 0  # 类属性：统计总用例数
    
    def __init__(self, name, description):
        self.name = name
        self.description = description
        self.status = 'pending'
        self.result = None
        TestCase.total_cases += 1
    
    def run(self):
        '''执行测试'''
        self.status = 'running'
        # 模拟测试逻辑
        self.status = 'passed' if self._execute() else 'failed'
        return self.status
    
    def _execute(self):
        '''私有方法（下划线前缀约定）'''
        return True
    
    def get_report(self):
        '''获取测试报告'''
        return {
            'name': self.name,
            'status': self.status,
            'result': self.result
        }

# 使用
tc = TestCase('登录测试', '验证正常登录流程')
print(tc.name)          # 登录测试
print(TestCase.total_cases)  # 1
tc.run()
print(tc.status)        # passed
```

## 继承（Inheritance）

继承允许子类获得父类的属性和方法，实现代码复用。

```python
# 父类（基类）
class Animal:
    def __init__(self, name):
        self.name = name
    
    def speak(self):
        pass  # 子类来实现

# 子类（派生类）
class Dog(Animal):
    def speak(self):
        return f"{self.name}说：汪汪！"

class Cat(Animal):
    def speak(self):
        return f"{self.name}说：喵喵！"

# 多态：不同对象对同一方法有不同表现
animals = [Dog('旺财'), Cat('咪咪')]
for animal in animals:
    print(animal.speak())
# 旺财说：汪汪！
# 咪咪说：喵喵！
```

### super() 调用父类方法

```python
class TestRunner:
    def __init__(self, name):
        self.name = name
        self.start_time = None
    
    def prepare(self):
        print(f"[{self.name}] 准备测试环境...")

class APITestRunner(TestRunner):
    def __init__(self, name, base_url):
        super().__init__(name)  # 调用父类的__init__
        self.base_url = base_url
    
    def prepare(self):
        super().prepare()  # 先执行父类的prepare
        print(f"[{self.name}] 设置API地址: {self.base_url}")
```

## 封装（Encapsulation）

Python通过命名约定来控制访问权限：

```python
class BankAccount:
    def __init__(self, owner, balance=0):
        self.owner = owner          # 公开属性
        self._bank = 'ICBC'         # 受保护属性（约定：不要外部访问）
        self.__balance = balance    # 私有属性（名称改编为 _类名__balance）
    
    def deposit(self, amount):
        '''存款'''
        if amount > 0:
            self.__balance += amount
            return True
        return False
    
    def withdraw(self, amount):
        '''取款'''
        if 0 < amount <= self.__balance:
            self.__balance -= amount
            return True
        return False
    
    def get_balance(self):
        '''查看余额（不能直接修改）'''
        return self.__balance

# 使用
account = BankAccount('张三', 1000)
account.deposit(500)
print(account.get_balance())  # 1500
# account.__balance = 9999  ← 无效！会创建一个新属性
```

## 特殊方法（魔术方法）

```python
class TestResult:
    def __init__(self, case_name, passed, duration):
        self.case_name = case_name
        self.passed = passed
        self.duration = duration
    
    def __str__(self):
        '''print() 时的显示'''
        status = '✓' if self.passed else '✗'
        return f"{status} {self.case_name} ({self.duration:.2f}s)"
    
    def __repr__(self):
        '''repr() 和开发调试时的显示'''
        return f"TestResult('{self.case_name}', {self.passed}, {self.duration})"
    
    def __eq__(self, other):
        '''== 比较'''
        return self.case_name == other.case_name
    
    def __lt__(self, other):
        '''< 比较'''
        return self.duration < other.duration

result = TestResult('登录测试', True, 0.35)
print(result)      # ✓ 登录测试 (0.35s)
print(repr(result))  # TestResult('登录测试', True, 0.35)
```

## @property 装饰器

```python
class Rectangle:
    def __init__(self, width, height):
        self._width = width
        self._height = height
    
    @property
    def area(self):
        '''面积（像属性一样访问，实际是方法）'''
        return self._width * self._height
    
    @property
    def width(self):
        return self._width
    
    @width.setter
    def width(self, value):
        if value <= 0:
            raise ValueError("宽度必须为正数")
        self._width = value

rect = Rectangle(5, 3)
print(rect.area)    # 15（不用括号！）
rect.width = 10     # 触发setter验证
```

## 小结

- **类（class）** 是创建对象的模板
- **__init__** 是构造方法，**self** 指向实例
- **继承** 实现代码复用和层级关系
- **封装** 隐藏实现细节，保护数据
- **多态** 让不同对象对同一消息做出不同响应""",
    },
    {
        "title": "第8节：文件操作",
        "sort_order": 8,
        "knowledge_point": "文件操作",
        "time_estimate": 20,
        "content": """## 文件操作基础

Python提供了简洁的文件操作API。核心函数是 `open()`。

### 打开文件

```python
file = open('文件名', '模式', encoding='编码')
```

### 文件模式

| 模式 | 说明 |
|------|------|
| 'r' | 只读（默认），文件必须存在 |
| 'w' | 只写，文件不存在则创建，存在则清空 |
| 'a' | 追加，在文件末尾添加内容 |
| 'x' | 创建新文件，文件已存在则报错 |
| 'r+' | 读写 |
| 'b' | 二进制模式（如 'rb', 'wb'） |

## 推荐的打开方式（with语句）

使用 `with` 语句，文件会在代码块结束后**自动关闭**，即使发生异常也会关闭。

```python
# 推荐：with语句
with open('data.txt', 'r', encoding='utf-8') as f:
    content = f.read()
    print(content)
# 文件在这里自动关闭，不需要f.close()

# 不推荐：手动关闭
f = open('data.txt', 'r', encoding='utf-8')
content = f.read()
f.close()  # 如果中间抛异常，close可能不会执行
```

## 读取文件

### read() - 读取全部内容

```python
with open('data.txt', 'r', encoding='utf-8') as f:
    content = f.read()      # 读取整个文件为一个大字符串
    print(content)
```

### readline() - 逐行读取

```python
with open('data.txt', 'r', encoding='utf-8') as f:
    line = f.readline()     # 读取一行（包含换行符）
    while line:
        print(line.strip())  # strip()去除行尾换行符
        line = f.readline()
```

### readlines() - 读取所有行为列表

```python
with open('data.txt', 'r', encoding='utf-8') as f:
    lines = f.readlines()   # ['第一行\n', '第二行\n', ...]
    for line in lines:
        print(line.strip())
```

### 直接遍历文件对象（最佳实践）

```python
with open('data.txt', 'r', encoding='utf-8') as f:
    for line in f:           # 逐行迭代，内存友好
        print(line.strip())
```

## 写入文件

```python
# 写入文本
with open('output.txt', 'w', encoding='utf-8') as f:
    f.write('Hello, World!\n')
    f.write('第二行内容\n')

# 追加内容
with open('output.txt', 'a', encoding='utf-8') as f:
    f.write('追加的一行\n')
```

## 综合示例：处理CSV文件

```python
# 读取CSV并处理
def read_csv(filename):
    '''读取CSV文件，返回列表的列表'''
    with open(filename, 'r', encoding='utf-8') as f:
        rows = []
        for line in f:
            row = line.strip().split(',')
            rows.append(row)
        return rows

# 写入CSV
def write_csv(filename, data):
    '''将数据写入CSV文件'''
    with open(filename, 'w', encoding='utf-8', newline='') as f:
        for row in data:
            f.write(','.join(str(cell) for cell in row) + '\n')

# 使用
data = read_csv('students.csv')
for row in data:
    print(f"姓名：{row[0]}，年龄：{row[1]}")
```

## 处理JSON文件

```python
import json

# 读取JSON
with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)
    print(config['database']['host'])

# 写入JSON
data = {
    'users': [
        {'name': '张三', 'age': 25},
        {'name': '李四', 'age': 30},
    ],
    'total': 2
}
with open('users.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
```

## 文件操作的最佳实践

1. **始终使用with语句**：自动关闭文件
2. **指定encoding**：处理中文时用 `encoding='utf-8'`
3. **大文件逐行读取**：不要用read()一次性加载
4. **使用正确的路径**：
```python
import os

# 获取当前脚本所在目录
current_dir = os.path.dirname(__file__)

# 拼接路径
file_path = os.path.join(current_dir, 'data', 'config.json')

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()
```

## 小结

| 操作 | 方法 |
|------|------|
| 读取全部 | `f.read()` |
| 读取一行 | `f.readline()` |
| 读取所有行 | `f.readlines()` |
| 逐行遍历 | `for line in f:` |
| 写入 | `f.write(str)` |
| 多行写入 | `f.writelines(list)` |""",
    },
    {
        "title": "第9节：异常处理",
        "sort_order": 9,
        "knowledge_point": "异常处理",
        "time_estimate": 20,
        "content": """## 什么是异常？

异常是程序运行时发生的错误。如果不处理，程序会崩溃并显示Traceback。

```python
# 除零错误
print(10 / 0)  # ZeroDivisionError: division by zero

# 类型错误
print('hello' + 5)  # TypeError

# 文件不存在
open('不存在的文件.txt')  # FileNotFoundError

# 字典键不存在
d = {'a': 1}
print(d['b'])  # KeyError
```

## try-except 捕获异常

### 基本结构

```python
try:
    # 可能出错的代码
    result = 10 / 0
except ZeroDivisionError:
    # 处理特定异常
    print("不能除以零！")
```

### 捕获多种异常

```python
try:
    value = int(input("请输入一个数字: "))
    result = 100 / value
    print(f"结果: {result}")
except ValueError:
    print("请输入有效的数字！")
except ZeroDivisionError:
    print("不能除以零！")
except Exception as e:
    print(f"未知错误: {e}")
```

### 捕获所有异常

```python
try:
    risky_operation()
except Exception as e:
    print(f"发生错误: {e}")
    print(f"错误类型: {type(e).__name__}")
```

> 不要用空的 `except:` 捕获所有异常（包括KeyboardInterrupt等），会掩盖真正的bug。

### else 和 finally

```python
try:
    file = open('data.txt', 'r')
    content = file.read()
except FileNotFoundError:
    print("文件不存在")
else:
    # try成功时执行
    print(f"读取了{len(content)}个字符")
finally:
    # 无论是否异常都执行（清理资源）
    print("执行清理操作")
    file.close()  # 关闭文件
```

## 手动抛出异常（raise）

```python
def validate_age(age):
    if age < 0:
        raise ValueError("年龄不能为负数")
    if age > 150:
        raise ValueError("年龄不能超过150岁")
    return age

try:
    validate_age(-5)
except ValueError as e:
    print(e)  # 年龄不能为负数
```

## 自定义异常

```python
class TestExecutionError(Exception):
    '''测试执行异常'''
    def __init__(self, case_name, message):
        self.case_name = case_name
        self.message = message
        super().__init__(f"[{case_name}] {message}")

class AssertionError(TestExecutionError):
    '''断言失败异常'''
    pass

class TimeoutError(TestExecutionError):
    '''超时异常'''
    pass

# 使用
def run_test(case):
    if case['duration'] > case['timeout']:
        raise TimeoutError(case['name'], f"超时: {case['duration']}s")
    if not case['passed']:
        raise AssertionError(case['name'], "断言失败")

try:
    run_test({'name': '登录测试', 'duration': 15, 'timeout': 10, 'passed': True})
except TestExecutionError as e:
    print(e)
```

## 异常处理最佳实践

### 测试中的异常处理

```python
import requests

def api_call(url, timeout=30):
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()  # 4xx/5xx抛出异常
        return response.json()
    except requests.exceptions.Timeout:
        print(f"请求超时: {url}")
        return None
    except requests.exceptions.ConnectionError:
        print(f"连接失败: {url}")
        return None
    except requests.exceptions.HTTPError as e:
        print(f"HTTP错误: {e.response.status_code}")
        return None
    except ValueError as e:
        print(f"JSON解析失败: {e}")
        return None
```

### 原则

1. **具体优于笼统**：捕获具体异常类型
2. **尽早捕获**：异常发生后尽快处理
3. **不要吞异常**：至少要记录日志
4. **清理资源**：使用finally或with
5. **传播异常**：处理不了的异常继续raise

```python
# 错误示范
try:
    do_something()
except:
    pass  # 吞掉了所有异常！

# 正确示范
try:
    do_something()
except SpecificError as e:
    logger.error(f"操作失败: {e}")
    raise  # 或者根据情况处理
```

## 小结

| 关键字 | 用途 |
|--------|------|
| try | 尝试执行的代码块 |
| except | 捕获并处理异常 |
| else | try成功时执行 |
| finally | 无论是否异常都执行 |
| raise | 抛出异常 |

测试工程师日常会大量用到异常处理，特别是在编写自动化测试脚本和接口测试时。""",
    },
    {
        "title": "第10节：常用标准库与实战技巧",
        "sort_order": 10,
        "knowledge_point": "标准库",
        "time_estimate": 25,
        "content": """## datetime - 日期时间处理

```python
from datetime import datetime, timedelta, date

# 获取当前日期时间
now = datetime.now()
print(now)  # 2024-01-15 10:30:00.123456

# 创建指定日期
d = datetime(2024, 1, 15, 10, 30, 0)
print(d.strftime("%Y-%m-%d %H:%M:%S"))  # 2024-01-15 10:30:00

# 解析日期字符串
d = datetime.strptime("2024-01-15", "%Y-%m-%d")

# 时间加减
tomorrow = now + timedelta(days=1)
one_hour_later = now + timedelta(hours=1)
three_days_ago = now - timedelta(days=3)

# 日期差
diff = datetime(2024, 2, 1) - datetime(2024, 1, 15)
print(diff.days)  # 17

# 常用格式
print(now.strftime("%Y-%m-%d"))       # 2024-01-15
print(now.strftime("%Y年%m月%d日"))    # 2024年01月15日
print(now.strftime("%H:%M:%S"))       # 10:30:00
```

## os - 操作系统接口

```python
import os

# 当前工作目录
print(os.getcwd())

# 切换目录
os.chdir('/path/to/dir')

# 列出目录内容
files = os.listdir('.')
for f in files:
    print(f)

# 判断路径
os.path.exists('file.txt')   # 文件/目录是否存在
os.path.isfile('file.txt')   # 是否是文件
os.path.isdir('mydir')       # 是否是目录

# 创建目录
os.makedirs('a/b/c', exist_ok=True)  # 递归创建

# 路径拼接（跨平台）
path = os.path.join('data', 'config', 'settings.json')
# Windows: data\\config\\settings.json
# Linux: data/config/settings.json

# 获取文件名和扩展名
os.path.basename('/path/to/file.txt')    # 'file.txt'
os.path.splitext('file.txt')             # ('file', '.txt')

# 执行系统命令
os.system('dir')      # Windows
os.system('ls -la')   # Linux/Mac
```

## json - JSON数据处理

```python
import json

# Python → JSON字符串
data = {'name': '张三', 'age': 25, 'skills': ['Python', 'SQL']}
json_str = json.dumps(data, ensure_ascii=False, indent=2)
print(json_str)
'''
{
  "name": "张三",
  "age": 25,
  "skills": ["Python", "SQL"]
}
'''

# JSON字符串 → Python
data = json.loads('{"name": "张三", "age": 25}')
print(data['name'])  # 张三

# 自定义JSON编码器
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

data = {'time': datetime.now()}
print(json.dumps(data, cls=DateTimeEncoder))
```

## random - 随机数

```python
import random

random.random()          # [0, 1)随机浮点数
random.randint(1, 10)    # [1, 10]随机整数
random.choice([1,3,5])   # 随机选择一个元素
random.sample(range(10), 3)  # 不放回抽样3个

# 打乱列表（原地操作）
lst = [1, 2, 3, 4, 5]
random.shuffle(lst)

# 设置随机种子（使结果可重现）
random.seed(42)
print(random.randint(1, 100))  # 每次都一样
```

## collections - 高级数据结构

```python
from collections import Counter, defaultdict, namedtuple

# Counter：计数器
words = ['a', 'b', 'c', 'a', 'a', 'b']
counter = Counter(words)
print(counter)                # Counter({'a': 3, 'b': 2, 'c': 1})
print(counter.most_common(2)) # [('a', 3), ('b', 2)]

# defaultdict：带默认值的字典
dd = defaultdict(list)
dd['users'].append('张三')     # 不用检查key是否存在

dd2 = defaultdict(int)
text = 'hello world'
for ch in text:
    dd2[ch] += 1              # 不用先初始化

# namedtuple：带名字的元组
Point = namedtuple('Point', ['x', 'y'])
p = Point(3, 4)
print(p.x, p.y)  # 3 4

TestCase = namedtuple('TestCase', ['id', 'name', 'status'])
tc = TestCase(1, '登录测试', 'passed')
print(f"{tc.name}: {tc.status}")
```

## 测试工程师实用脚本模板

```python
import requests
import json
import time
from datetime import datetime

def api_test(url, method='GET', headers=None, data=None, expected_status=200):
    '''通用接口测试函数'''
    start = time.time()
    try:
        if method.upper() == 'GET':
            resp = requests.get(url, headers=headers, timeout=30)
        elif method.upper() == 'POST':
            resp = requests.post(url, headers=headers, json=data, timeout=30)
        else:
            raise ValueError(f"不支持的方法: {method}")
        
        elapsed = time.time() - start
        passed = resp.status_code == expected_status
        
        return {
            'url': url,
            'method': method,
            'status_code': resp.status_code,
            'expected_status': expected_status,
            'passed': passed,
            'elapsed': round(elapsed, 3),
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        return {
            'url': url,
            'method': method,
            'passed': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

# 批量测试
test_cases = [
    {'url': 'https://api.example.com/health', 'method': 'GET', 'expected_status': 200},
    {'url': 'https://api.example.com/users', 'method': 'GET', 'expected_status': 200},
    {'url': 'https://api.example.com/login', 'method': 'POST', 'expected_status': 200,
     'data': {'username': 'admin', 'password': '123456'}},
]

results = []
for case in test_cases:
    result = api_test(**case)
    results.append(result)
    status = '✓' if result['passed'] else '✗'
    print(f"  {status} {case['method']} {case['url']}")

# 统计
passed = sum(1 for r in results if r['passed'])
print(f"通过: {passed}/{len(results)}")
```

## 小结

Python拥有丰富的标准库，是"自带电池"的语言。测试工程师特别需要掌握：**datetime**（时间处理）、**json**（数据交换）、**os**（文件系统）、**random**（生成测试数据）、**collections**（高效数据结构）。""",
    },
]

# ============================================================
# 其他路径的精简教程
# ============================================================
LESSON_CONTENT["Linux基础命令"] = [
    {
        "title": "第1节：Linux文件系统与基本操作",
        "sort_order": 1,
        "knowledge_point": "文件操作",
        "time_estimate": 20,
        "content": """## Linux目录结构

```
/          根目录
├── bin/    基础命令
├── etc/    配置文件
├── home/   用户目录
├── var/    日志、缓存
├── tmp/    临时文件
├── usr/    用户程序
└── opt/    第三方软件
```

## 基础文件命令

```bash
ls          查看目录内容
ls -l       显示详细信息
ls -la      显示所有文件（含隐藏文件）

cd /path    切换目录
cd ..       返回上级目录
cd ~        回到用户主目录

pwd         显示当前路径

mkdir dir   创建目录
mkdir -p a/b/c  递归创建

cp src dst  复制文件
cp -r src dst   复制目录

mv src dst  移动/重命名

rm file     删除文件
rm -r dir   删除目录（递归）
rm -rf dir  强制删除（危险！）

cat file    查看文件内容
less file   分页查看（q退出）

touch file  创建空文件或更新修改时间
```

## 文件权限

```bash
ls -l  # -rwxr-xr-- 1 user group 1024 Jan 15 file.txt
#      ^^^\________/
#      类型 权限     所有者 组

# r=4, w=2, x=1
chmod 755 file   # rwxr-xr-x (可执行文件)
chmod 644 file   # rw-r--r-- (普通文件)
chmod +x script  # 添加执行权限
```

## 查看日志

```bash
tail -f error.log    # 实时查看日志
tail -n 100 app.log  # 查看最后100行
head -n 20 app.log   # 查看前20行
grep "ERROR" app.log # 搜索包含ERROR的行
grep -n "ERROR" app.log  # 显示行号
grep -rn "ERROR" logs/   # 递归搜索目录
```""",
    },
    {
        "title": "第2节：文本处理三剑客",
        "sort_order": 2,
        "knowledge_point": "grep/sed/awk",
        "time_estimate": 25,
        "content": """## grep - 文本搜索

```bash
grep "pattern" file        # 搜索包含pattern的行
grep -i "error" app.log    # 不区分大小写
grep -v "DEBUG" app.log    # 反向匹配（排除DEBUG）
grep -c "ERROR" app.log    # 统计匹配行数
grep -rn "TODO" src/       # 递归搜索目录
grep -A 3 "ERROR" log      # 显示匹配行及后3行
grep -B 2 "ERROR" log      # 显示匹配行及前2行
grep -C 5 "ERROR" log      # 显示匹配行及前后5行
```

## sed - 流编辑器

```bash
# 替换（s/查找/替换/标志）
sed 's/localhost/192.168.1.100/' file     # 替换第一个
sed 's/localhost/192.168.1.100/g' file    # 全局替换
sed -i 's/old/new/g' file                 # 直接修改文件

# 删除行
sed '5d' file              # 删除第5行
sed '/DEBUG/d' file        # 删除包含DEBUG的行

# 提取行
sed -n '10,20p' file       # 显示10-20行
```

## awk - 文本分析工具

```bash
# 基本结构：awk 'pattern {action}' file
awk '{print $1}' file           # 打印第1列
awk '{print $1, $NF}' file      # 打印第1列和最后一列
awk -F: '{print $1}' /etc/passwd  # 指定分隔符为:
awk -F',' '{print $2}' data.csv

# 条件过滤
awk '$3 > 100' file             # 第3列大于100的行
awk '/ERROR/ {print $1, $4}' log  # 含ERROR的行，打印第1和第4列

# 统计
awk '{sum+=$3} END {print sum}' data  # 第3列求和
awk '{count[$1]++} END {for(k in count) print k, count[k]}' log
```

## 管道与组合

```bash
# | 将一个命令的输出作为另一个命令的输入
cat access.log | grep "404" | wc -l  # 统计404错误数量
ps aux | grep python | awk '{print $2}'  # 提取Python进程PID
history | awk '{print $2}' | sort | uniq -c | sort -rn | head -10  # 最常用的10个命令
```""",
    },
    {
        "title": "第3节：进程管理与系统监控",
        "sort_order": 3,
        "knowledge_point": "进程管理",
        "time_estimate": 15,
        "content": """## 进程管理

```bash
ps aux                     # 查看所有进程
ps aux | grep python       # 查找Python进程

top                        # 实时进程监控（q退出）
htop                       # 更友好的top（需安装）

kill PID                   # 终止进程（优雅）
kill -9 PID                # 强制终止
killall process_name       # 按名称终止

# 后台运行
nohup python app.py &      # 后台运行，忽略挂断信号
nohup python app.py > log.txt 2>&1 &  # 重定向输出
```

## 系统信息

```bash
df -h                      # 磁盘使用情况
du -sh *                   # 当前目录下各文件/文件夹大小
free -h                    # 内存使用情况
uname -a                   # 系统信息
uptime                     # 运行时间
w                          # 当前登录用户
```

## 网络命令

```bash
netstat -tlnp              # 查看监听端口
lsof -i :5001              # 查看5001端口占用
curl http://localhost:5001 # HTTP请求测试
ping -c 4 google.com       # 连通性测试
```""",
    },
]

LESSON_CONTENT["计算机基础与网络知识"] = [
    {
        "title": "第1节：HTTP协议深度解析",
        "sort_order": 1,
        "knowledge_point": "HTTP协议",
        "time_estimate": 25,
        "content": """## HTTP请求结构

```
POST /api/login HTTP/1.1          ← 请求行（方法 URL 版本）
Host: www.example.com             ← 请求头
Content-Type: application/json
Authorization: Bearer token123

{"username":"admin","password":"123"}  ← 请求体
```

## HTTP响应结构

```
HTTP/1.1 200 OK                   ← 状态行（版本 状态码 描述）
Content-Type: application/json    ← 响应头
Content-Length: 42

{"status":"success","token":"..."} ← 响应体
```

## HTTP方法

| 方法 | 用途 | 幂等 | 安全 |
|------|------|------|------|
| GET | 获取资源 | 是 | 是 |
| POST | 创建资源 | 否 | 否 |
| PUT | 完整更新 | 是 | 否 |
| PATCH | 部分更新 | 否 | 否 |
| DELETE | 删除资源 | 是 | 否 |
| HEAD | 获取头部 | 是 | 是 |
| OPTIONS | 查看支持的方法 | 是 | 是 |

## HTTP状态码速查

- **2xx 成功**：200 OK、201 Created、204 No Content
- **3xx 重定向**：301 永久重定向、302 临时重定向、304 Not Modified
- **4xx 客户端错误**：400 Bad Request、401 Unauthorized、403 Forbidden、404 Not Found、405 Method Not Allowed、429 Too Many Requests
- **5xx 服务器错误**：500 Internal Server Error、502 Bad Gateway、503 Service Unavailable、504 Gateway Timeout

## HTTPS

HTTPS = HTTP + SSL/TLS。数据在传输过程中被加密。

验证证书：
```bash
openssl s_client -connect example.com:443 -servername example.com
```""",
    },
    {
        "title": "第2节：TCP/IP与网络基础",
        "sort_order": 2,
        "knowledge_point": "TCP/IP",
        "time_estimate": 20,
        "content": """## TCP/IP四层模型

| 层 | 协议 | 说明 |
|-----|------|------|
| 应用层 | HTTP/DNS/FTP | 应用程序间通信 |
| 传输层 | TCP/UDP | 端到端数据传输 |
| 网络层 | IP/ICMP | 路由和寻址 |
| 链路层 | Ethernet/WiFi | 物理网络 |

## TCP三次握手

```
客户端                    服务器
  |-------SYN------->|    1. 客户端请求建立连接
  |<---SYN+ACK-------|    2. 服务器确认+请求连接
  |-------ACK------->|    3. 客户端确认
  |                  |
  |<====连接建立====>|
```

## TCP四次挥手

```
客户端                    服务器
  |-------FIN------->|    1. 客户端：我没有数据要发了
  |<------ACK---------|    2. 服务器：知道了
  |<------FIN---------|    3. 服务器：我也没有了
  |-------ACK------->|    4. 客户端：知道了
  |                  |
  |<====连接关闭====>|
```

## TCP vs UDP

| 对比 | TCP | UDP |
|------|-----|-----|
| 连接 | 面向连接 | 无连接 |
| 可靠性 | 可靠（确认重传） | 不可靠 |
| 速度 | 较慢 | 较快 |
| 场景 | HTTP、数据库、文件传输 | 视频直播、游戏、DNS |

## 常用网络调试命令

```bash
# 连通性测试
ping google.com

# 路由追踪
tracert google.com     # Windows
traceroute google.com  # Linux

# DNS查询
nslookup example.com

# 查看网络连接
netstat -an
```""",
    },
]

# ================================================================
# 主逻辑
# ================================================================


async def seed_lessons():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        total_added = 0
        stats = {}

        for path_title, lessons in LESSON_CONTENT.items():
            stmt = select(LearningPath).where(LearningPath.title == path_title)
            result = await session.execute(stmt)
            path = result.scalar_one_or_none()

            if not path:
                print(f"  [SKIP] Learning path not found: {path_title}")
                continue

            added = 0
            for lesson_data in lessons:
                existing_stmt = select(LessonSection).where(
                    LessonSection.title == lesson_data["title"],
                    LessonSection.learning_path_id == path.id,
                )
                existing_result = await session.execute(existing_stmt)
                if existing_result.scalar_one_or_none():
                    continue
                lesson = LessonSection(**lesson_data, learning_path_id=path.id)
                session.add(lesson)
                added += 1

            stats[path_title] = added
            total_added += added
            print(f"  [OK] '{path_title}': +{added} lessons")

        await session.commit()

        print("\n" + "=" * 60)
        print(f"[DONE] Added {total_added} lessons across {len(stats)} paths")
        print("=" * 60)


if __name__ == "__main__":
    print("=" * 60)
    print("[START] Seeding learning content (lesson sections)...")
    print("=" * 60)
    asyncio.run(seed_lessons())
