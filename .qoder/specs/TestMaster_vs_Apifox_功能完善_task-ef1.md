# TestMaster 功能完善 — 对标 Apifox（代码复用优化版）

## Context
TestMaster 在 AI 测试生成、学习平台等方面有独特优势，但在流程编排（无 If/For/脚本）和 Mock 数据丰富度方面与 Apifox 差距明显。本计划聚焦最高 ROI 的功能补齐，**最大化复用现有代码**。

## 实施范围
- **Phase 1 核心**: 流程控制组件 + JS 脚本引擎
- **Phase 2 核心**: 智能 Mock + JSON Schema 校验 + 会话变量 + 多服务 URL + 数据库操作
- **不做**: 内置压测引擎（工作量大，现有 JMeter 集成可覆盖）、gRPC/WebSocket 协议

## 技术决策
- JS 引擎: **dukpy**（Duktape 绑定，ES5，轻量跨平台）
- 条件表达式: **复用断言引擎 `compare_values()`**，不重复实现操作符
- 数据库迁移: 运行时 `_migrate_columns` + Alembic 双轨

## 代码复用原则（关键约束）

| 需求 | 复用现有代码 | 避免重复 |
|------|-------------|----------|
| 变量替换 | `parser.py` 的 `replace_variables()` 全部复用，session vars 合并到 dict 即可 | **不新建** parser 或替换函数 |
| 条件表达式 | 复用 `autotest_assertion_engine.py` 的 `compare_values()` + `get_field_value()` | **不新建** 操作符比较逻辑 |
| 变量提取 | 复用 `extract_variables_from_response()`（jsonpath/regex/header） | **不新建** 提取器 |
| 动态数据生成 | 复用 `autotest_data_factory_service.py` 的 phone/email/uuid/timestamp 生成规则 | **不重复实现** 已有的数据生成逻辑 |
| Mock Schema 生成 | 复用 `mock_service.py` 的 `_mock_value()` 并增强 | **不新建** Schema mock 引擎 |
| 加密 | 复用 `utils/encryption.py` 的 `encrypt()`/`decrypt()` | **不新建** 加密模块 |
| JSONPath | 复用 `autotest_helpers.py` 的 `extract_jsonpath_value()` | **不新建** JSONPath 解析 |
| 变量序列化 | 复用 `autotest_variable_service.py` 的 `serialize/deserialize_var_value()` | **不新建** 序列化逻辑 |
| Celery 调度 | 复用 `tasks.py` 的任务模板 + fallback 模式 | **不新建** 调度框架 |
| 前端 CodeEditor | 复用 `components/CodeEditor.vue` 组件 | **不新建** 编辑器基础组件 |

---

## Task 1: 数据库模型扩展

**修改文件**: `fastapi_backend/models/autotest.py`

### 1.1 AutoTestScenarioStep 新增字段
```python
step_type = Column(String(20), default="api_request", comment="步骤类型: api_request/if_condition/for_loop/for_each/wait/group/scenario_ref/db_query")
step_config = Column(JSON, nullable=True, comment="类型专属配置")
parent_step_id = Column(Integer, ForeignKey("scenario_steps.id"), nullable=True, comment="父步骤ID(嵌套)")
pre_script = Column(Text, nullable=True, comment="前置JS脚本")
post_script = Column(Text, nullable=True, comment="后置JS脚本")
```

### 1.2 AutoTestCase 新增字段
```python
pre_script = Column(Text, nullable=True, comment="前置JS脚本")
post_script = Column(Text, nullable=True, comment="后置JS脚本")
response_schema = Column(JSON, nullable=True, comment="响应JSON Schema")
```

### 1.3 AutoTestEnvironment 新增字段
```python
services = Column(JSON, nullable=True, comment="多服务URL配置列表")
```

### 1.4 新增 AutoTestDBConnection 模型
```python
class AutoTestDBConnection(Base):
    __tablename__ = "autotest_db_connections"
    # id, name, user_id, db_type(mysql/pg/mongo/redis), host, port, database_name, username, password_encrypted, is_active
```

### 1.5 运行时迁移
**修改文件**: `fastapi_backend/core/autotest_database.py`
- 在 `_migrate_columns` 中为 `scenario_steps` 添加 `step_type`, `step_config`, `parent_step_id`, `pre_script`, `post_script`
- 为 `api_cases` 添加 `pre_script`, `post_script`, `response_schema`
- 为 `environments` 添加 `services`
- 创建 `autotest_db_connections` 表

### 1.6 Schema 同步
**修改文件**: `fastapi_backend/schemas/autotest.py`
- ScenarioStep 系列 Schema 增加 `step_type`, `step_config`, `parent_step_id`, `pre_script`, `post_script`
- AutoTestCase 系列增加 `pre_script`, `post_script`, `response_schema`
- Environment 系列增加 `services`
- 新增 `DBConnectionCreate/Update/Response`

---

## Task 2: 流程控制执行引擎

**修改文件**: `fastapi_backend/services/autotest_scenario_runner.py`

### 2.1 步骤分发器
将 `execute()` 中现有的线性步骤遍历改为按 `step_type` 分发。**将现有 `_execute_step()` 重命名为 `_execute_api_request()`**，其他类型新增 handler：
```python
handlers = {
    "api_request": self._execute_api_request,  # 现有逻辑重命名
    "if_condition": self._execute_if,
    "for_loop": self._execute_for,
    "for_each": self._execute_for_each,
    "wait": self._execute_wait,
    "group": self._execute_group,
    "scenario_ref": self._execute_scenario_ref,
    "db_query": self._execute_db_query,
}
```

### 2.2 新增执行方法
- `_execute_if()`: **复用 `compare_values()`** 评估条件 → 执行 then/else 分支步骤
- `_execute_for()`: 按 count 循环，注入循环变量 `{{i}}`（复用 `replace_variables`）
- `_execute_for_each()`: 遍历 `{{collection}}` 数组，注入 `{{item}}`
- `_execute_wait()`: `asyncio.sleep(duration_ms/1000)`
- `_execute_group()`: 执行 children 步骤列表
- `_execute_scenario_ref()`: 实例化子引擎执行引用场景（防循环引用）
- `_evaluate_condition()`: **直接调用 `compare_values()` from `autotest_assertion_engine`**，复用已有的 15 种操作符（==, !=, >, <, contains, exists, empty 等），无需新建解析器

### 2.3 步骤预加载扩展
`execute()` 中预加载步骤数据时增加 `step_type`, `step_config`, `parent_step_id` 字段。

### 2.4 安全防护
- 最大嵌套深度: 5 层
- 单次执行最大步骤数: 10000
- 循环最大迭代次数: 1000

---

## Task 3: JS 脚本引擎

### 3.1 安装依赖
`fastapi_backend/requirements.txt` 添加 `dukpy>=0.4.0`

### 3.2 新建脚本引擎（合并 context 到同一文件，减少文件数）
**新建文件**: `fastapi_backend/services/script_engine.py`

`ScriptEngine` 类，内含 `ScriptContext` dataclass + 核心方法：
- `ScriptContext` dataclass: 封装 env_vars, global_vars, session_vars, request_info, response_info
- `run_pre_script(code, context)` → 返回修改后的 context
- `run_post_script(code, context)` → 返回断言结果 + 修改后的 context

pm.* API 实现（**复用现有变量系统**）：
- `pm.environment.get/set` → 直接操作 context.env_vars（与 `env.variables` 同源）
- `pm.globals.get/set` → 调用 `autotest_variable_service.save_variables_to_db()` 持久化
- `pm.sessionVariables.get/set` → context.session_vars（内存字典，执行结束丢弃）
- `pm.response.json()` → JSON.parse(response_body)
- `pm.response.status` → status_code
- `pm.response.headers.get(name)` → headers[name]
- `pm.test(name, fn)` → 执行 fn 并记录结果
- `pm.expect(val).to.equal(x)` → 断言（**复用 `compare_values` 逻辑**）

### 3.3 集成到执行引擎
**修改文件**: `fastapi_backend/services/autotest_scenario_runner.py`
- 将现有 `_execute_step()` 重命名为 `_execute_api_request()`
- 请求前：若有 `pre_script` 则调用 `ScriptEngine.run_pre_script()`
- 请求后：若有 `post_script` 则调用 `ScriptEngine.run_post_script()`
- post_script 中的 `pm.test()` 结果合并到现有断言结果列表（复用 `execute_assertions()` 的数据结构）

---

## Task 4: 会话变量 (Session Variables)

**设计原则**：不新建表，不修改 parser.py，纯内存方案。

### 4.1 引擎层
**修改文件**: `fastapi_backend/services/autotest_scenario_runner.py`
- `ScenarioExecutionEngine.__init__()` 新增 `self.session_vars: Dict[str, Any] = {}`
- 在现有 `execute()` 方法的变量加载阶段，将 session_vars 合并到 `self.context_vars`（高优先级覆盖）
- 每次调用 `replace_variables()` 前，合并优先级：session_vars > context_vars > env.variables > global_vars > 内置变量
- **无需修改 `parser.py`**：session_vars 直接合入 variables dict 后传入即可

### 4.2 脚本引擎集成
- `pm.sessionVariables.set(key, val)` → 写入 `engine.session_vars`
- `pm.sessionVariables.get(key)` → 读取 `engine.session_vars`
- 执行结束后 session_vars 自动随引擎实例销毁

---

## Task 5: 智能 Mock 数据生成

**复用策略**：不新建独立 dynamic_value_generator 文件，直接在 `mock_service.py` 的 `_mock_value()` 方法中增强，并复用 `DataFactoryEngine` 中已有的 phone/email/uuid 生成逻辑。

### 5.1 安装依赖
`fastapi_backend/requirements.txt` 添加 `faker>=18.0.0`

### 5.2 增强现有 Mock 引擎
**修改文件**: `fastapi_backend/services/mock_service.py`

在 `MockEngine` 类中：
- `_mock_value()` 方法增强（复用 DataFactory 的生成模式）：
  - `string` + `format: email` → 复用 `DataFactoryEngine` 的 email 生成逻辑
  - `string` + `format: phone` → 复用 DataFactory 的 phone 生成逻辑
  - `integer`/`number` → 根据 `minimum`/`maximum` 范围随机（替代当前固定返回 minimum）
  - `string` + `x-mock-expression` → 支持 `@name`、`@datetime` 等动态表达式

- `generate_response()` 方法增加动态值替换：
  - 新增 `_resolve_dynamic_values(body)` 方法，递归替换响应体中的 `@表达式`
  - **复用 DataFactoryEngine 的 `_generate_value()` 方法** 处理 @name→随机姓名, @phone→手机号 等

### 5.3 @ 表达式映射（复用现有 DataFactory 规则）
| 表达式 | 复用来源 |
|--------|----------|
| `@phone` | `DataFactoryEngine._generate_phone()` |
| `@email` | `DataFactoryEngine._generate_email()` |
| `@uuid` | `DataFactoryEngine._generate_uuid()` |
| `@timestamp` | `DataFactoryEngine._generate_timestamp()` |
| `@datetime` | `DataFactoryEngine._generate_date_offset()` |
| `@name` / `@address` / `@id_card` | 新增（使用 faker 库） |

---

## Task 6: JSON Schema 响应校验

**复用策略**：在现有断言引擎中新增操作符，不新建独立验证模块。

### 6.1 安装依赖
`fastapi_backend/requirements.txt` 添加 `jsonschema>=4.20.0`

### 6.2 断言引擎扩展（复用现有架构）
**修改文件**: `fastapi_backend/services/autotest_assertion_engine.py`
- 在 `compare_values()` 函数中新增 `json_schema` 操作符分支
- 复用已有的 `get_field_value()` 获取响应 body
- 复用已有的断言结果格式（field/operator/expected/actual/passed/message）
- 无需新建文件，只扩展一个 `elif` 分支

### 6.3 执行引擎集成
**修改文件**: `fastapi_backend/services/autotest_scenario_runner.py`
- `_execute_api_request()` 中：断言执行后，若 `api_case.response_schema` 存在，自动追加一条 `json_schema` 断言规则
- 复用现有 `execute_assertions()` 调用链路

---

## Task 7: 多服务 URL 环境

**复用策略**：复用现有 `base_url` + `replace_variables` 机制，只增加服务名解析层。

### 7.1 执行引擎 URL 解析
**修改文件**: `fastapi_backend/services/autotest_scenario_runner.py`
- 在现有 URL 构建逻辑前增加一层服务名解析：
  - 若 URL 格式为 `service-name:/path`，从 `env.services` 查找对应 `base_url`
  - 若未匹配到服务名，**回退到现有的 `self.base_url`（即 env.base_url）逻辑**，零改动
- 将解析出的 service base_url 也注入 `context_vars["base_url"]`，后续步骤可复用 `{{base_url}}`

---

## Task 8: 数据库连接管理

**复用策略**：加密用 `utils/encryption.py`，CRUD 路由模式复用现有 `autotest_environments.py` 结构。

### 8.1 新建路由（复用 environments 路由的 CRUD 模式）
**新建文件**: `fastapi_backend/routers/autotest_db_connections.py`
- CRUD: POST/GET/PUT/DELETE `/api/auto-test/db-connections`
- 测试连接: POST `/api/auto-test/db-connections/{id}/test`
- **密码加密**：复用 `utils/encryption.py` 的 `encrypt()`/`decrypt()`
- **路由结构**：参照 `autotest_environments.py` 的 CRUD + 敏感字段脱敏模式

### 8.2 新建服务
**新建文件**: `fastapi_backend/services/db_operation_service.py`
- 支持 MySQL(aiomysql), PostgreSQL(asyncpg), Redis(redis.asyncio)
- `execute_query()`: 执行 SQL 并提取结果
- **结果提取**：复用 `extract_jsonpath_value()` from `autotest_helpers.py`
- **变量保存**：复用 `autotest_variable_service.save_variables_to_db()` 持久化提取的变量

### 8.3 注册路由
**修改文件**: `fastapi_backend/core/router_registry.py`
- autotest 列表添加 `autotest_db_connections`

---

## Task 9: 前端改造

**复用策略**：复用现有 `CodeEditor.vue` 组件，不新建基础编辑器；步骤编辑复用 StepList 的拖拽+卡片模式。

### 9.1 步骤列表多类型支持
**修改文件**: `frontend/src/views/scenario/StepList.vue`
- 添加步骤按钮改为 `el-dropdown` 下拉菜单（API请求/If条件/For循环/ForEach/等待/分组/数据库查询/引用场景）
- 不同类型显示不同图标和 `el-tag` 颜色标签
- 流控步骤（if/for/group）显示为可展开的容器卡片，**复用现有 `vuedraggable` 拖拽**
- 每个步骤卡片新增折叠区域：前置脚本/后置脚本（仅 api_request 类型）

### 9.2 新建流控配置面板
**新建文件**: `frontend/src/views/scenario/FlowControlPanel.vue`
- If: 条件表达式输入（**复用断言引擎的操作符列表**作为下拉选项）
- For: 循环次数 + 变量名
- ForEach: 集合变量 + 元素变量名
- Wait: 延迟毫秒数
- Group: 分组名称
- DB Query: 连接选择 + SQL 编辑（**复用 `CodeEditor.vue` 并设 language=sql**）

### 9.3 脚本编辑器（复用 CodeEditor.vue，不新建文件）
- 在 StepList.vue 步骤卡片的折叠面板中嵌入 `<CodeEditor language="javascript" />`
- 在 CaseEditorDrawer.vue 的前置/后置脚本 Tab 中嵌入 `<CodeEditor language="javascript" />`

### 9.4 修改 CodeEditor.vue 支持 JavaScript
**修改文件**: `frontend/src/components/CodeEditor.vue`
- 新增 `@codemirror/lang-javascript` 的语言映射分支

### 9.5 场景编辑器适配
**修改文件**: `frontend/src/views/ScenarioEditor.vue`
- 步骤添加逻辑适配新的 step_type

### 9.6 环境管理多服务
**修改文件**: `frontend/src/components/EnvironmentManager.vue`
- 在现有 base_url 下方新增"多服务配置"折叠区域
- 使用 `el-table` 内嵌 `el-input` 编辑服务名+URL 键值对
- **复用现有的环境表单结构和保存逻辑**

### 9.7 用例编辑器脚本 Tab
**修改文件**: `frontend/src/views/CaseEditorDrawer.vue`
- 在现有 Tab 列表中新增"前置脚本"和"后置脚本"两个 Tab
- 嵌入 `<CodeEditor language="javascript" />`（复用现有组件）
- **复用 CaseEditorDrawer 现有的 Tab 切换和保存逻辑**

### 9.8 Mock 服务增强
**修改文件**: `frontend/src/views/MockService.vue`
- 在响应体编辑器旁增加"动态值表达式"提示面板（@name, @email 等列表）
- **复用现有的 JSON 编辑器**

### 9.9 安装前端依赖
```
npm install @codemirror/lang-javascript
```

### 9.10 路由更新
- **无需修改** `router/index.js`：所有新组件都嵌入现有页面，无需新增路由

---

## Task 10: 数据库连接管理前端

**复用策略**：复用 AutoTest.vue 的 Tab 容器模式，CRUD 列表复用 EnvironmentManager 的结构。

### 10.1 新建组件
**新建文件**: `frontend/src/views/scenario/DBConnectionManager.vue`
- **CRUD 列表**：复用 `EnvironmentManager.vue` 的抽屉+表单模式
- 连接配置表单：db_type 下拉 + host/port/database/username/password
- 测试连接按钮
- **密码字段**：复用现有的 `is_encrypted` 脱敏显示模式
- SQL 编辑器：复用 `<CodeEditor language="sql" />`（已安装 `@codemirror/lang-sql`）

### 10.2 集成到 AutoTest 主页面
**修改文件**: `frontend/src/views/AutoTest.vue`
- Tab 栏新增"数据库连接"Tab（**复用现有的 Tab 切换模式**）

---

## 依赖变更汇总

### Python (`fastapi_backend/requirements.txt`)
```
dukpy>=0.4.0      # JS 脚本引擎
faker>=18.0.0     # 智能 Mock（@name/@address/@id_card 等中文数据）
jsonschema>=4.20.0  # JSON Schema 响应校验（作为断言引擎新操作符）
```

### npm (`frontend/package.json`)
```
@codemirror/lang-javascript  # 复用现有 CodeEditor.vue 增加 JS 语法高亮
```

---

## 新建文件清单（最小化）

| 文件 | 说明 | 复用了什么 |
|------|------|------------|
| `services/script_engine.py` | JS 脚本引擎 + ScriptContext | 复用 compare_values, save_variables_to_db |
| `services/db_operation_service.py` | 数据库操作服务 | 复用 encrypt/decrypt, extract_jsonpath_value |
| `routers/autotest_db_connections.py` | DB 连接 CRUD 路由 | 复用 environments 路由模式, encrypt/decrypt |
| `views/scenario/FlowControlPanel.vue` | 流控配置面板 | 复用断言操作符列表, CodeEditor |
| `views/scenario/DBConnectionManager.vue` | DB 连接管理 | 复用 EnvironmentManager 模式, CodeEditor |

**不再新建的文件**（相比原计划精简）：
- ~~`services/script_context.py`~~ → 合并到 `script_engine.py`
- ~~`services/dynamic_value_generator.py`~~ → 直接增强 `mock_service.py`，复用 DataFactory
- ~~`views/scenario/ScriptEditor.vue`~~ → 复用现有 `CodeEditor.vue`
- ~~`views/scenario/ConditionEditor.vue`~~ → 合并到 `FlowControlPanel.vue`

---

## 向后兼容保证
- `step_type` DEFAULT 'api_request' → 现有步骤无需修改
- 所有新增字段 `nullable=True` → 不影响现有数据
- 旧前端无 `step_type` 字段时默认渲染为 API 请求
- 现有 `_execute_step()` 逻辑完全保留，仅重命名为 `_execute_api_request()`

---

## 验证方案
1. **流控组件**: 创建包含 If/For/Wait 步骤的场景 → 执行 → 检查执行日志中分支/循环是否正确
2. **JS 脚本**: 在步骤中添加 `pm.environment.set("token", pm.response.json().token)` → 执行 → 验证后续步骤能使用 `{{token}}`
3. **智能 Mock**: 创建 Mock 规则，响应体包含 `@name`/`@email` → 请求 Mock 端点 → 验证返回动态数据
4. **Schema 校验**: 给用例配置 response_schema → 执行场景 → 验证不符合 Schema 时报告错误
5. **会话变量**: 脚本中设置 `pm.sessionVariables.set("tmp", 123)` → 后续步骤使用 `{{tmp}}` → 执行结束后变量不存在
6. **多服务 URL**: 环境配置 services 列表 → 步骤 URL 使用 `service-name:/path` → 验证正确拼接
7. **数据库操作**: 配置 PG 连接 → 添加 db_query 步骤 → 执行 → 验证查询结果被提取到变量
