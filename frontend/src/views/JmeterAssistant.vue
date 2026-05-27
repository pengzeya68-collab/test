<template>
  <div class="jmeter-ide">
    <!-- 顶部工具栏 -->
    <div class="ide-toolbar">
      <div class="toolbar-left">
        <h2 class="ide-title">JMeter 脚本 IDE</h2>
        <el-tag size="small" type="info">{{ scriptTree.children.length }} 个线程组</el-tag>
      </div>
      <div class="toolbar-center">
        <el-button-group>
          <el-tooltip content="从接口库导入接口"><el-button size="small" @click="showImportCases = true"><el-icon><Connection /></el-icon> 导入接口</el-button></el-tooltip>
          <el-tooltip content="使用模板快速创建脚本"><el-button size="small" @click="showTemplates = true"><el-icon><MagicStick /></el-icon> 模板库</el-button></el-tooltip>
          <el-tooltip content="从环境变量一键配置"><el-button size="small" @click="showImportEnv = true"><el-icon><Setting /></el-icon> 导入环境</el-button></el-tooltip>
          <el-tooltip content="从全局变量注入"><el-button size="small" @click="importGlobalVars"><el-icon><Coin /></el-icon> 全局变量</el-button></el-tooltip>
          <el-tooltip content="从数据工厂生成 CSV"><el-button size="small" @click="showImportDataFactory = true"><el-icon><Document /></el-icon> CSV数据</el-button></el-tooltip>
        </el-button-group>
      </div>
      <div class="toolbar-right">
        <el-button size="small" type="primary" @click="generatePreview" :loading="generating">
          <el-icon><Refresh /></el-icon> 生成预览
        </el-button>
        <el-button size="small" type="success" @click="downloadJmx" :disabled="!jmxContent">
          <el-icon><Download /></el-icon> 下载 .jmx
        </el-button>
        <el-button size="small" @click="showGuide = !showGuide" :type="showGuide ? 'warning' : ''">
          <el-icon><QuestionFilled /></el-icon> {{ showGuide ? '关闭引导' : '使用帮助' }}
        </el-button>
      </div>
    </div>

    <!-- 引导面板 - Quick Start Wizard -->
    <div v-if="showGuide" class="quick-start-wizard">
      <div class="wizard-header">
        <div class="wizard-title-row">
          <span class="wizard-icon">🧙</span>
          <div>
            <strong>JMeter 快速上手向导</strong>
            <p style="margin:2px 0 0;font-size:11px;color:var(--tm-text-secondary)">三步学会编写压测脚本，导出 .jmx 用 JMeter 执行</p>
          </div>
          <el-button text @click="showGuide = false" style="color:var(--tm-text-secondary)">跳过</el-button>
        </div>
      </div>
      <div class="wizard-steps">
        <div class="wizard-step" :class="{ active: wizardStep === 1, done: wizardStep > 1 }" @click="wizardStep = 1">
          <span class="wstep-num">{{ wizardStep > 1 ? '✓' : '①' }}</span>
          <span class="wstep-label"><strong>导入接口</strong><br/><small>从接口库选择API</small></span>
        </div>
        <div class="wstep-arrow">→</div>
        <div class="wizard-step" :class="{ active: wizardStep === 2, done: wizardStep > 2 }" @click="wizardStep = 2">
          <span class="wstep-num">{{ wizardStep > 2 ? '✓' : '②' }}</span>
          <span class="wstep-label"><strong>配置压测参数</strong><br/><small>线程/断言/提取器</small></span>
        </div>
        <div class="wstep-arrow">→</div>
        <div class="wizard-step" :class="{ active: wizardStep === 3, done: wizardStep > 3 }" @click="wizardStep = 3">
          <span class="wstep-num">③</span>
          <span class="wstep-label"><strong>调试并导出</strong><br/><small>验证请求→下载JMX</small></span>
        </div>
      </div>
      <div class="wizard-body">
        <div v-if="wizardStep === 1" class="wizard-card">
          <el-alert title="快速开始" type="info" :closable="false" show-icon style="margin-bottom:8px">
            <p style="margin:0">有 <strong>3 种方式</strong> 添加接口：</p>
          </el-alert>
          <div class="wizard-actions">
            <el-button type="primary" @click="showImportCases = true; wizardStep = 2" size="default">
              📋 从接口库导入（推荐）
            </el-button>
            <el-button @click="addSampleTemplate('simple')" size="default">
              ⚡ 使用模板快速创建
            </el-button>
            <el-button @click="wizardStep = 2" size="default">
              ✏️ 我手动添加请求
            </el-button>
          </div>
          <div class="wizard-tip" style="margin-top:8px;font-size:11px;color:var(--tm-text-secondary)">
            💡 推荐从接口库导入已有用例，一步到位！接口库没有的接口？<el-button link type="primary" size="small" @click="openInterfaceLib">先去接口库创建</el-button>
          </div>
        </div>
        <div v-if="wizardStep === 2" class="wizard-card">
          <div class="wizard-config">
            <div class="form-row">
              <div class="form-group"><label>并发线程数</label><el-input-number v-model="wizardThreads" :min="1" :max="10000" size="small" /></div>
              <div class="form-group"><label>循环次数</label><el-input-number v-model="wizardLoops" :min="1" :max="99999" size="small" /></div>
              <div class="form-group"><label>持续时间(秒)</label><el-input-number v-model="wizardDuration" :min="1" :max="86400" size="small" /></div>
            </div>
            <div class="wizard-tip" style="margin-top:8px;font-size:11px;color:var(--tm-text-secondary)">
              💡 并发线程=虚拟用户数 | Ramp-Up时间=启动间隔 | 建议从小并发开始(1-10线程)逐步增大
            </div>
            <el-button type="primary" size="small" @click="applyWizardConfig" style="margin-top:8px">✅ 应用配置</el-button>
            <el-button size="small" @click="wizardStep = 3" style="margin-top:8px;margin-left:4px">下一步 →</el-button>
          </div>
        </div>
        <div v-if="wizardStep === 3" class="wizard-card">
          <div class="wizard-final">
            <el-steps :active="3" finish-status="success" simple style="margin-bottom:12px">
              <el-step title="选中HTTP请求" />
              <el-step title="点击调试查看响应" />
              <el-step title="生成并下载JMX" />
            </el-steps>
            <div class="wizard-actions">
              <el-button type="primary" @click="generatePreview" :loading="generating" size="default">🔮 生成 JMX 预览</el-button>
              <el-button type="success" @click="downloadJmx" :disabled="!jmxContent" size="default">⬇ 下载 .jmx 文件</el-button>
            </div>
            <el-alert title="下载的 .jmx 文件用 JMeter 打开即可运行！" type="success" show-icon :closable="false" style="margin-top:8px" />
          </div>
        </div>
      </div>
    </div>

    <!-- 主体三栏 -->
    <div class="ide-body">
      <!-- 左栏: 脚本树 -->
      <div class="panel tree-panel">
        <div class="panel-header">
          <span>脚本结构</span>
          <div class="tree-actions">
            <el-tooltip content="添加线程组 (Thread Group)"><el-button link size="small" @click="addRootElement"><el-icon><Plus /></el-icon></el-button></el-tooltip>
          </div>
        </div>
        <div class="tree-body">
          <jmeter-tree-node
            v-for="(node, idx) in scriptTree.children"
            :key="node.uid"
            :node="node"
            :depth="0"
            :selected-uid="selectedUid"
            @select="selectNode"
            @remove="removeNode(idx, null)"
            @add-child="addChildNode"
            @duplicate="duplicateNode"
          />
          <div v-if="scriptTree.children.length === 0" class="tree-empty">
            <el-icon :size="32"><FolderDelete /></el-icon>
            <p>右键点击树节点添加元素<br/>或点击顶部 <el-tag size="small">导入接口</el-tag> 快速开始</p>
          </div>
        </div>
      </div>

      <!-- 中栏: 元素编辑 -->
      <div class="panel editor-panel">
        <div class="panel-header">
          <span>{{ selectedNode ? selectedNode.name : '元素编辑器' }}</span>
          <el-tag v-if="selectedNode" size="small">{{ NODE_TYPES[selectedNode.type]?.label || selectedNode.type }}</el-tag>
        </div>
        <div class="editor-body" v-if="selectedNode">
          <!-- 测试计划 -->
          <template v-if="selectedNode.type === 'TestPlan'">
            <div class="form-group"><label>测试计划名称</label><el-input v-model="selectedNode.props.name" placeholder="TestMaster Performance Test" /></div>
            <div class="form-group"><label>用户定义变量</label>
              <div v-for="(v, vi) in (selectedNode.props.variables || [])" :key="vi" class="var-row">
                <el-input v-model="v.name" placeholder="变量名" size="small" style="width:45%" />
                <el-input v-model="v.value" placeholder="值" size="small" style="width:45%" />
                <el-button link size="small" type="danger" @click="selectedNode.props.variables.splice(vi,1)">×</el-button>
              </div>
              <el-button size="small" @click="addVar">+ 添加变量</el-button>
            </div>
          </template>

          <!-- 线程组 -->
          <template v-if="selectedNode.type === 'ThreadGroup'">
            <div class="form-row"><div class="form-group"><label>线程数</label><el-input-number v-model="selectedNode.props.threads" :min="1" :max="10000" size="small" /></div><div class="form-group"><label>Ramp-Up (秒)</label><el-input-number v-model="selectedNode.props.rampUp" :min="0" :max="3600" size="small" /></div></div>
            <div class="form-row"><div class="form-group"><label>循环次数</label><el-input-number v-model="selectedNode.props.loops" :min="1" :max="99999" size="small" /></div><div class="form-group"><label>持续时间 (秒)</label><el-input-number v-model="selectedNode.props.duration" :min="0" :max="86400" size="small" /></div></div>
            <div class="form-group"><label>线程组名称</label><el-input v-model="selectedNode.name" size="small" /></div>
            <el-alert v-if="selectedNode.props.loops >= 99999 && !selectedNode.props.duration" title="此脚本将永久循环运行！请设置持续时间或减小循环次数" type="error" :closable="false" show-icon />
          </template>

          <!-- HTTP 请求 -->
          <template v-if="selectedNode.type === 'HttpSampler'">
            <div class="form-group"><label>请求名称</label><el-input v-model="selectedNode.name" size="small" /></div>
            <div class="form-row"><div class="form-group"><label>方法</label><el-select v-model="selectedNode.props.method" size="small"><el-option v-for="m in ['GET','POST','PUT','DELETE','PATCH']" :key="m" :label="m" :value="m" /></el-select></div><div class="form-group" style="flex:1"><label>URL</label><el-input v-model="selectedNode.props.url" size="small" placeholder="https://api.example.com/users" /></div></div>
            <div class="form-group"><label>请求头</label>
              <div v-for="(h, hi) in (selectedNode.props.headers || [])" :key="hi" class="var-row">
                <el-input v-model="h.key" placeholder="Header名" size="small" style="width:40%" />
                <el-input v-model="h.value" placeholder="值" size="small" style="width:50%" />
                <el-button link size="small" type="danger" @click="selectedNode.props.headers.splice(hi,1)">×</el-button>
              </div>
              <el-button size="small" @click="addHeader">+ 添加请求头</el-button>
            </div>
            <div class="form-group" v-if="selectedNode.props.method !== 'GET'"><label>请求体</label><el-input v-model="selectedNode.props.body" type="textarea" :rows="4" size="small" placeholder='{"key":"value"}' /></div>
            <div class="form-group"><label>Body 类型</label><el-select v-model="selectedNode.props.bodyType" size="small"><el-option v-for="b in ['none','json','form-data','x-www-form-urlencoded']" :key="b" :label="b" :value="b"/></el-select></div>
            <el-button size="small" type="primary" @click="debugRequest(selectedNode)" :loading="debugLoading" style="margin-top:8px">
              <el-icon><VideoPlay /></el-icon> 🐛 调试此请求
            </el-button>
            <el-button size="small" type="success" @click="saveSamplerToCase(selectedNode)" :loading="savingToCase" style="margin-top:8px;margin-left:4px">
              <el-icon><DocumentAdd /></el-icon> 保存到接口库
            </el-button>
          </template>

          <!-- 响应断言 -->
          <template v-if="selectedNode.type === 'ResponseAssertion'">
            <div class="form-group"><label>断言名称</label><el-input v-model="selectedNode.name" size="small" /></div>
            <div class="form-group"><label>断言类型</label><el-select v-model="selectedNode.props.assertType" size="small"><el-option label="状态码" value="status_code" /><el-option label="响应包含" value="contains" /><el-option label="响应匹配" value="matches" /><el-option label="JSON Path" value="jsonpath" /><el-option label="持续时间" value="duration" /></el-select></div>
            <div class="form-group" v-if="selectedNode.props.assertType === 'status_code'"><label>期望状态码</label><el-input-number v-model="selectedNode.props.expected" :min="100" :max="599" size="small" /></div>
            <div class="form-group" v-if="selectedNode.props.assertType === 'contains' || selectedNode.props.assertType === 'matches'"><label>期望值</label><el-input v-model="selectedNode.props.expected" size="small" /></div>
            <div class="form-group" v-if="selectedNode.props.assertType === 'jsonpath'"><label>JSON Path</label><el-input v-model="selectedNode.props.jsonPath" placeholder="$.data.token" size="small" /><label style="margin-top:4px">期望值</label><el-input v-model="selectedNode.props.expected" size="small" /></div>
            <div class="form-group" v-if="selectedNode.props.assertType === 'duration'"><label>最大响应时间 (ms)</label><el-input-number v-model="selectedNode.props.maxDuration" :min="1" :max="60000" size="small" /></div>
          </template>

          <!-- 提取器 -->
          <template v-if="selectedNode.type === 'RegexExtractor' || selectedNode.type === 'JsonExtractor'">
            <div class="form-group"><label>提取器名称</label><el-input v-model="selectedNode.name" size="small" /></div>
            <div class="form-group"><label>变量名</label><el-input v-model="selectedNode.props.varName" placeholder="token" size="small" /></div>
            <div class="form-hint">引用方式: {'$'}{'{token}'} 或 {'$'}{'{__P(token)}'}</div>
            <div class="form-group" v-if="selectedNode.type === 'RegexExtractor'"><label>正则表达式</label><el-input v-model="selectedNode.props.regex" placeholder='"token":"(.*?)"' size="small" /></div>
            <div class="form-group" v-if="selectedNode.type === 'JsonExtractor'"><label>JSON Path</label><el-input v-model="selectedNode.props.jsonPath" placeholder="$.data.token" size="small" /></div>
            <div class="form-group"><label>默认值</label><el-input v-model="selectedNode.props.defaultValue" placeholder="NOT_FOUND" size="small" /></div>
          </template>

          <!-- 定时器 -->
          <template v-if="selectedNode.type === 'ConstantTimer'">
            <div class="form-group"><label>延迟 (毫秒)</label><el-input-number v-model="selectedNode.props.delay" :min="0" :max="60000" size="small" /></div>
          </template>
          <template v-if="selectedNode.type === 'UniformRandomTimer'">
            <div class="form-row"><div class="form-group"><label>最小延迟 (ms)</label><el-input-number v-model="selectedNode.props.minDelay" :min="0" size="small" /></div><div class="form-group"><label>最大延迟 (ms)</label><el-input-number v-model="selectedNode.props.maxDelay" :min="1" size="small" /></div></div>
          </template>
          <template v-if="selectedNode.type === 'GaussianRandomTimer'">
            <div class="form-row"><div class="form-group"><label>偏差 (ms)</label><el-input-number v-model="selectedNode.props.deviation" :min="0" :max="60000" size="small" /></div><div class="form-group"><label>偏移 (ms)</label><el-input-number v-model="selectedNode.props.offset" :min="0" :max="60000" size="small" /></div></div>
          </template>
          <template v-if="selectedNode.type === 'SyncTimer'">
            <div class="form-group"><label>集合点并发数</label><el-input-number v-model="selectedNode.props.groupSize" :min="2" :max="10000" size="small" /></div>
          </template>

          <!-- CSV Data Set -->
          <template v-if="selectedNode.type === 'CSVDataSet'">
            <div class="form-group"><label>CSV 文件名</label><el-input v-model="selectedNode.props.filename" placeholder="users.csv" size="small" /></div>
            <div class="form-group"><label>变量名 (逗号分隔)</label><el-input v-model="selectedNode.props.variableNames" placeholder="username,password" size="small" /></div>
            <div class="form-row"><div class="form-group"><label>分隔符</label><el-input v-model="selectedNode.props.delimiter" size="small" style="width:60px" /></div><div class="form-group"><label>是否循环</label><el-switch v-model="selectedNode.props.recycle" size="small" /></div></div>
            <div class="form-group"><label>CSV 内容 (可选, 将随 .jmx 一并导出)</label><el-input v-model="selectedNode.props.csvContent" type="textarea" :rows="4" placeholder="username,password&#10;user1,pass1&#10;user2,pass2" size="small" /></div>
          </template>

          <!-- JDBC 数据库连接 -->
          <template v-if="selectedNode.type === 'JDBCConnection'">
            <div class="form-group"><label>连接名称</label><el-input v-model="selectedNode.name" size="small" /></div>
            <div class="form-group"><label>数据库 URL</label><el-input v-model="selectedNode.props.dbUrl" placeholder="jdbc:mysql://host:port/db" size="small" /></div>
            <div class="form-row"><div class="form-group"><label>驱动类</label><el-input v-model="selectedNode.props.driver" placeholder="com.mysql.cj.jdbc.Driver" size="small" /></div><div class="form-group"><label>用户名</label><el-input v-model="selectedNode.props.dbUser" size="small" /></div></div>
            <div class="form-group"><label>密码</label><el-input v-model="selectedNode.props.dbPass" type="password" size="small" show-password /></div>
          </template>
          <template v-if="selectedNode.type === 'JDBCSampler'">
            <div class="form-group"><label>SQL 查询</label><el-input v-model="selectedNode.props.sql" type="textarea" :rows="3" placeholder="SELECT * FROM users WHERE status = 'active'" size="small" /></div>
          </template>

          <!-- BeanShell -->
          <template v-if="selectedNode.type === 'BeanShellPreProcessor' || selectedNode.type === 'BeanShellPostProcessor'">
            <div class="form-group"><label>脚本名称</label><el-input v-model="selectedNode.name" size="small" /></div>
            <div class="form-group"><label>BeanShell 脚本</label><el-input v-model="selectedNode.props.script" type="textarea" :rows="6" placeholder="long ts = System.currentTimeMillis(); vars.put(&quot;ts&quot;,String.valueOf(ts));" size="small" /></div>
          </template>

          <!-- 监听器 -->
          <template v-if="selectedNode.type === 'ViewResultsTree' || selectedNode.type === 'SummaryReport' || selectedNode.type === 'AggregateGraph'">
            <div class="form-group"><label>监听器名称</label><el-input v-model="selectedNode.name" size="small" /></div>
          </template>
        </div>
        <div class="editor-empty" v-else>
          <el-icon :size="40"><EditPen /></el-icon>
          <p>选择左侧树中的一个元素<br/>开始编辑属性</p>
        </div>
      </div>

      <!-- 右栏: 调试 + 预览 -->
      <div class="panel debug-panel">
        <el-tabs v-model="rightTab" class="right-tabs">
          <el-tab-pane label="JMX 预览" name="jmx">
            <div class="code-preview"><pre v-if="jmxContent"><code>{{ jmxContent }}</code></pre><div v-else class="empty-hint">点击「生成预览」查看</div></div>
          </el-tab-pane>
          <el-tab-pane label="调试结果" name="debug">
            <div class="debug-area" v-if="debugResult">
              <div class="debug-meta">
                <el-tag :type="debugResult.response?.status_code === 200 ? 'success' : 'danger'" size="small">
                  {{ debugResult.response?.status_code || 'ERR' }}
                </el-tag>
                <span class="debug-elapsed">{{ debugResult.response?.elapsed_ms }}ms</span>
                <span class="debug-size">{{ (debugResult.response?.body_size || 0) }}B</span>
              </div>
              <el-collapse>
                <el-collapse-item title="响应头" name="headers">
                  <pre class="debug-json">{{ formatHeaders(debugResult.response?.headers) }}</pre>
                </el-collapse-item>
                <el-collapse-item title="响应体" name="body">
                  <pre class="debug-json">{{ formatBody(debugResult.response?.body) }}</pre>
                </el-collapse-item>
                <el-collapse-item title="请求详情" name="request">
                  <pre class="debug-json">{{ formatBody(debugResult.request) }}</pre>
                </el-collapse-item>
              </el-collapse>
              <div v-if="debugResult.response?.error" class="debug-error">
                <el-alert :title="debugResult.response.error" type="error" show-icon />
                <el-alert title="跨域问题？TestMaster 通过后端代理发请求，已自动解决跨域！" type="success" :closable="false" show-icon style="margin-top:4px" />
              </div>
            </div>
            <div v-else class="empty-hint">选择一个 HttpSampler 点击「调试此请求」</div>
          </el-tab-pane>
        </el-tabs>
      </div>
    </div>

    <!-- 导入接口对话框 -->
    <el-dialog v-model="showImportCases" title="从接口库导入接口" width="700px">
      <el-input v-model="caseSearch" placeholder="搜索接口..." size="small" clearable class="mb-8" />
      <div class="case-import-list">
        <el-checkbox-group v-model="selectedImportCases">
          <div v-for="c in filteredImportCases" :key="c.id" class="case-import-item">
            <el-checkbox :label="c.id">
              <span class="case-method" :class="'method-'+(c.method||'GET').toLowerCase()">{{ c.method }}</span>
              {{ c.name }}
            </el-checkbox>
          </div>
        </el-checkbox-group>
      </div>
      <template #footer>
        <el-button @click="showImportCases = false">取消</el-button>
        <el-button type="primary" @click="importSelectedCases" :disabled="selectedImportCases.length===0">导入 {{ selectedImportCases.length }} 个接口</el-button>
      </template>
    </el-dialog>

    <!-- 导入环境对话框 -->
    <el-dialog v-model="showImportEnv" title="从环境变量配置" width="500px">
      <div class="case-import-list">
        <el-radio-group v-model="selectedEnvId">
          <div v-for="env in environments" :key="env.id" class="env-item">
            <el-radio :label="env.id">{{ env.name }} <span class="env-url">{{ env.base_url }}</span></el-radio>
          </div>
        </el-radio-group>
      </div>
      <el-alert title="选择环境后会自动设置 HTTP Request Defaults 中的域名和协议" type="info" show-icon :closable="false" style="margin-top:8px" />
      <template #footer>
        <el-button @click="showImportEnv = false">取消</el-button>
        <el-button type="primary" @click="applyEnv">应用环境</el-button>
      </template>
    </el-dialog>

    <!-- 导入数据工厂模板 -->
    <el-dialog v-model="showImportDataFactory" title="从数据工厂生成 CSV" width="600px">
      <div class="form-group"><label>CSV 行数</label><el-input-number v-model="csvRowCount" :min="1" :max="10000" size="small" /></div>
      <div class="form-group"><label>字段定义 (每行一个: 字段名,类型,规则)</label>
        <el-input v-model="csvFieldsDef" type="textarea" :rows="5" placeholder="username,string,random&#10;password,string,random&#10;email,string,email&#10;age,number,1-100" size="small" />
      </div>
      <template #footer>
        <el-button @click="showImportDataFactory = false">取消</el-button>
        <el-button type="primary" @click="generateCsv">生成 CSV 并加入脚本</el-button>
      </template>
    </el-dialog>

    <!-- 模板库对话框 -->
    <el-dialog v-model="showTemplates" title="JMeter 模板库" width="750px">
      <el-alert title="选择一个模板自动生成完整脚本，支持后续自由修改" type="info" show-icon :closable="false" style="margin-bottom:12px" />
      <div class="template-grid">
        <div class="template-card" v-for="tpl in templates" :key="tpl.key" @click="applyTemplate(tpl)">
          <div class="tpl-icon">{{ tpl.icon }}</div>
          <div class="tpl-info">
            <strong>{{ tpl.name }}</strong>
            <p>{{ tpl.desc }}</p>
            <div class="tpl-tags">
              <el-tag size="small" v-for="tag in tpl.tags" :key="tag">{{ tag }}</el-tag>
            </div>
          </div>
        </div>
      </div>
    </el-dialog>

    <!-- 认证链助手对话框 -->
    <el-dialog v-model="showAuthChain" title="认证链自动生成" width="650px">
      <el-alert title="自动创建：登录请求 → 提取Token → 后续请求自动注入认证头" type="success" show-icon :closable="false" style="margin-bottom:12px" />
      <div class="form-group"><label>登录接口 URL</label><el-input v-model="authChain.loginUrl" placeholder="https://api.example.com/auth/login" size="small" /></div>
      <div class="form-group"><label>请求体 (JSON)</label><el-input v-model="authChain.loginBody" type="textarea" :rows="3" placeholder='{"username":"admin","password":"123456"}' size="small" /></div>
      <div class="form-row">
        <div class="form-group"><label>Token 提取方式</label><el-select v-model="authChain.extractType" size="small"><el-option label="JSON Path" value="JSONPath" /><el-option label="正则表达式" value="Regex" /></el-select></div>
        <div class="form-group" v-if="authChain.extractType === 'JSONPath'"><label>JSON Path 表达式</label><el-input v-model="authChain.extractExpr" placeholder="$.data.token" size="small" /></div>
        <div class="form-group" v-if="authChain.extractType === 'Regex'"><label>正则表达式</label><el-input v-model="authChain.extractExpr" placeholder='"token":"(.*?)"' size="small" /></div>
      </div>
      <div class="form-group"><label>Token 放在哪个 Header</label><el-select v-model="authChain.headerName" size="small" allow-create filterable><el-option value="Authorization" /><el-option value="X-Auth-Token" /><el-option value="Cookie" /></el-select></div>
      <div class="form-group"><label>测试接口 URL (添加到此线程组)</label><el-input v-model="authChain.testUrl" placeholder="https://api.example.com/users/me" size="small" /></div>
      <template #footer>
        <el-button @click="showAuthChain = false">取消</el-button>
        <el-button type="primary" @click="generateAuthChain">⚡ 生成认证链</el-button>
      </template>
    </el-dialog>

    <!-- 保存到接口库对话框 -->
    <el-dialog v-model="showSaveToCase" title="保存到接口库" width="450px">
      <div class="form-group"><label>用例名称</label><el-input v-model="saveCaseName" size="small" /></div>
      <div class="form-group"><label>保存到分组</label>
        <el-select v-model="saveGroupId" size="small" filterable placeholder="选择分组">
          <el-option v-for="g in caseGroups" :key="g.id" :label="g.name" :value="g.id" />
        </el-select>
      </div>
      <div class="form-group"><label>请求方法</label><el-input v-model="saveCaseMethod" size="small" disabled /></div>
      <div class="form-group"><label>URL</label><el-input v-model="saveCaseUrl" size="small" disabled /></div>
      <template #footer>
        <el-button @click="showSaveToCase = false">取消</el-button>
        <el-button type="primary" @click="confirmSaveToCase" :loading="savingToCase">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, nextTick, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Refresh, Download, Connection, Setting, Coin, Document, QuestionFilled, VideoPlay, EditPen, FolderDelete, MagicStick, DocumentAdd } from '@element-plus/icons-vue'
import autoTestRequest from '@/utils/autoTestRequest'
import JmeterTreeNode from '@/components/JmeterTreeNode.vue'

// ===== 类型标签映射 =====
const NODE_TYPES = {
  TestPlan: { label: '测试计划', icon: '📋' },
  ThreadGroup: { label: '线程组', icon: '👥', parent: 'TestPlan' },
  HttpSampler: { label: 'HTTP 请求', icon: '🌐', parent: 'ThreadGroup' },
  ResponseAssertion: { label: '响应断言', icon: '✅', parent: 'HttpSampler' },
  DurationAssertion: { label: '持续时间断言', icon: '⏱️', parent: 'HttpSampler' },
  JsonAssertion: { label: 'JSON 断言', icon: '📋', parent: 'HttpSampler' },
  RegexExtractor: { label: '正则提取器', icon: '🔍', parent: 'HttpSampler' },
  JsonExtractor: { label: 'JSON 提取器', icon: '📤', parent: 'HttpSampler' },
  ConstantTimer: { label: '固定定时器', icon: '⏰', parent: 'HttpSampler' },
  UniformRandomTimer: { label: '均匀随机定时器', icon: '🎲', parent: 'HttpSampler' },
  GaussianRandomTimer: { label: '高斯随机定时器', icon: '📊', parent: 'HttpSampler' },
  SyncTimer: { label: '同步定时器(集合点)', icon: '🔄', parent: 'HttpSampler' },
  CSVDataSet: { label: 'CSV 数据源', icon: '📄', parent: 'ThreadGroup' },
  BeanShellPreProcessor: { label: 'BeanShell 前置处理', icon: '⚙️', parent: 'HttpSampler' },
  BeanShellPostProcessor: { label: 'BeanShell 后置处理', icon: '⚙️', parent: 'HttpSampler' },
  JDBCConnection: { label: 'JDBC 数据库连接', icon: '🗄️', parent: 'TestPlan' },
  JDBCSampler: { label: 'JDBC 请求', icon: '🗄️', parent: 'ThreadGroup' },
  ViewResultsTree: { label: '查看结果树', icon: '👁️', parent: 'ThreadGroup' },
  SummaryReport: { label: '聚合报告', icon: '📈', parent: 'ThreadGroup' },
  AggregateGraph: { label: '聚合图表', icon: '📉', parent: 'ThreadGroup' },
}

let uidCounter = 1
const newUid = () => `el_${uidCounter++}`

const createElement = (type, overrides = {}) => {
  const defaultProps = {
    HttpSampler: { method: 'GET', url: '', headers: [{ key: 'Content-Type', value: 'application/json' }], body: '', bodyType: 'json' },
    ThreadGroup: { threads: 10, rampUp: 5, loops: 1, duration: 60 },
    TestPlan: { variables: [] },
    ResponseAssertion: { assertType: 'status_code', expected: 200, jsonPath: '', maxDuration: 1000 },
    RegexExtractor: { varName: 'token', regex: '"token":"(.*?)"', defaultValue: 'NOT_FOUND', jsonPath: '' },
    JsonExtractor: { varName: 'token', jsonPath: '$.data.token', defaultValue: 'NOT_FOUND', regex: '' },
    ConstantTimer: { delay: 1000 },
    UniformRandomTimer: { minDelay: 500, maxDelay: 2000 },
    GaussianRandomTimer: { deviation: 100, offset: 300 },
    SyncTimer: { groupSize: 100 },
    CSVDataSet: { filename: 'data.csv', variableNames: '', delimiter: ',', recycle: true, csvContent: '' },
    JDBCConnection: { dbUrl: '', driver: 'com.mysql.cj.jdbc.Driver', dbUser: '', dbPass: '' },
    JDBCSampler: { sql: '' },
    BeanShellPreProcessor: { script: '' },
    BeanShellPostProcessor: { script: '' },
    ViewResultsTree: {},
    SummaryReport: {},
    AggregateGraph: {},
  }
  const baseProps = { ...(defaultProps[type] || {}) }
  const extraProps = overrides.props || {}
  return reactive({
    uid: newUid(),
    type,
    name: overrides.name || (NODE_TYPES[type]?.label || type),
    props: { ...baseProps, ...extraProps },
    children: [],
  })
}

// ===== 脚本树 =====
const scriptTree = reactive(createElement('TestPlan', { name: 'TestMaster 性能测试' }))
const selectedUid = ref(null)
const selectedNode = ref(null)

const selectNode = (uid) => {
  selectedUid.value = uid
  selectedNode.value = findNode(scriptTree, uid)
}

const findNode = (parent, uid) => {
  if (parent.uid === uid) return parent
  for (const child of parent.children || []) {
    const found = findNode(child, uid)
    if (found) return found
  }
  return null
}

const findParent = (parent, uid) => {
  for (const child of parent.children || []) {
    if (child.uid === uid) return { parent, index: parent.children.indexOf(child) }
    const found = findParent(child, uid)
    if (found) return found
  }
  return null
}

const addRootElement = () => {
  const tg = createElement('ThreadGroup')
  tg.name = `线程组 ${scriptTree.children.length + 1}`
  // 默认加一个 HttpSampler 作为示例
  const sampler = createElement('HttpSampler')
  sampler.name = 'HTTP 请求 1'
  tg.children.push(sampler)
  scriptTree.children.push(tg)
  selectedUid.value = tg.uid
  selectedNode.value = tg
}

const addChildNode = (parentUid, childType) => {
  const parent = findNode(scriptTree, parentUid)
  if (!parent) return
  const child = createElement(childType)
  parent.children.push(child)
  selectedUid.value = child.uid
  selectedNode.value = child
}

const removeNode = (index, parentUid) => {
  const container = parentUid ? findNode(scriptTree, parentUid) : scriptTree
  if (!container) return
  container.children.splice(index, 1)
  if (selectedUid.value && !findNode(scriptTree, selectedUid.value)) {
    selectedUid.value = null; selectedNode.value = null
  }
}

const duplicateNode = (uid) => {
  const source = findNode(scriptTree, uid)
  if (!source) return
  const pInfo = findParent(scriptTree, uid)
  if (!pInfo) return
  const copy = JSON.parse(JSON.stringify(source))
  copy.uid = newUid()
  pInfo.parent.children.splice(pInfo.index + 1, 0, reactive(copy))
}

// ===== 导入接口库 =====
const showImportCases = ref(false)
const caseSearch = ref('')
const selectedImportCases = ref([])
const allCases = ref([])

const openInterfaceLib = () => {
  window.open('/auto-test?tab=interfaces', '_blank')
}

const filteredImportCases = computed(() => {
  if (!caseSearch.value) return allCases.value
  const kw = caseSearch.value.toLowerCase()
  return allCases.value.filter(c => c.name.toLowerCase().includes(kw) || (c.url||'').toLowerCase().includes(kw))
})

const loadCases = async () => {
  try {
    const res = await autoTestRequest.get('/auto-test/cases/all')
    allCases.value = (Array.isArray(res) ? res : (res.items || res.data || [])).map(c => ({ id: c.id, name: c.name, method: c.method || 'GET', url: c.url || '' }))
  } catch (e) { console.error('加载接口用例失败:', e) }
}

const importSelectedCases = async () => {
  if (selectedImportCases.value.length === 0) return
  // 创建或找到第一个线程组
  let tg = scriptTree.children.find(c => c.type === 'ThreadGroup')
  if (!tg) {
    tg = createElement('ThreadGroup')
    scriptTree.children.push(tg)
  }
  for (const cid of selectedImportCases.value) {
    const c = allCases.value.find(x => x.id === cid)
    if (!c) continue
    const sampler = createElement('HttpSampler')
    sampler.name = c.name
    sampler.props.method = c.method
    sampler.props.url = c.url
    tg.children.push(sampler)
  }
  showImportCases.value = false
  ElMessage.success(`已导入 ${selectedImportCases.value.length} 个接口`)
  selectedImportCases.value = []
}

// ===== 环境变量 =====
const showImportEnv = ref(false)
const selectedEnvId = ref(null)
const environments = ref([])

const loadEnvironments = async () => {
  try {
    const res = await autoTestRequest.get('/auto-test/environments')
    const arr = Array.isArray(res) ? res : (res.data || res.environments || [])
    environments.value = arr.slice(0, 20)
  } catch (e) { console.error('加载环境失败:', e) }
}

const applyEnv = () => {
  const env = environments.value.find(e => e.id === selectedEnvId.value)
  if (!env || !env.base_url) return
  const parsed = env.base_url.replace(/\/$/, '')
  // 更新所有 HttpSampler 的 URL（如果为空则自动填充）
  const walk = (node) => {
    if (node.type === 'HttpSampler' && !node.props.url) {
      node.props.url = parsed + '/'
    }
    (node.children || []).forEach(walk)
  }
  walk(scriptTree)
  showImportEnv.value = false
  ElMessage.success(`已应用环境: ${env.name}`)
}

// ===== 全局变量 =====
const importGlobalVars = async () => {
  try {
    const res = await autoTestRequest.get('/auto-test/global-variables')
    const vars = Array.isArray(res) ? res : (res.data || res.variables || [])
    if (vars.length === 0) { ElMessage.warning('暂无全局变量，请先在变量管理中创建'); return }
    if (!scriptTree.props.variables) scriptTree.props.variables = []
    for (const v of vars) {
      if (!scriptTree.props.variables.find(x => x.name === v.name)) {
        scriptTree.props.variables.push({ name: v.name, value: v.value || '' })
      }
    }
    ElMessage.success(`已导入 ${vars.length} 个全局变量`)
  } catch (e) { ElMessage.error('导入失败') }
}

// ===== 数据工厂 =====
const showImportDataFactory = ref(false)
const csvRowCount = ref(100)
const csvFieldsDef = ref('username,string,random\npassword,string,random\nemail,string,email')

const generateCsv = () => {
  const fields = csvFieldsDef.value.split('\n').filter(l => l.trim()).map(l => {
    const [name, type, rule] = l.split(',')
    return { name: (name||'').trim(), type: (type||'string').trim(), rule: (rule||'').trim() }
  })
  // 生成 CSV 内容
  const header = fields.map(f => f.name).join(',')
  const rows = []
  for (let i = 0; i < csvRowCount.value; i++) {
    rows.push(fields.map(f => {
      if (f.type === 'number') return Math.floor(Math.random() * 100)
      if (f.type === 'email') return `user${i}@test.com`
      return `${f.name}_${i}`
    }).join(','))
  }
  const csv = [header, ...rows].join('\n')

  // 添加 CSVDataSet 到脚本树
  let tg = scriptTree.children.find(c => c.type === 'ThreadGroup')
  if (!tg) { tg = createElement('ThreadGroup'); scriptTree.children.push(tg) }
  const csvNode = createElement('CSVDataSet')
  csvNode.props.csvContent = csv
  csvNode.props.filename = 'testdata.csv'
  csvNode.props.variableNames = fields.map(f => f.name).join(',')
  tg.children.unshift(csvNode)
  showImportDataFactory.value = false
  ElMessage.success(`已生成 ${csvRowCount.value} 行 CSV 数据`)
}

// ===== 变量管理 =====
const addVar = () => { if (!scriptTree.props.variables) scriptTree.props.variables = []; scriptTree.props.variables.push({ name: '', value: '' }) }
const addHeader = () => { if (!selectedNode.value.props.headers) selectedNode.value.props.headers = []; selectedNode.value.props.headers.push({ key: '', value: '' }) }

// ===== 调试执行 =====
const debugResult = ref(null)
const debugLoading = ref(false)
const rightTab = ref('jmx')

const debugRequest = async (node) => {
  if (!node || node.type !== 'HttpSampler') return
  rightTab.value = 'debug'
  debugLoading.value = true
  try {
    // 构建请求头
    const headers = {}
    ;(node.props.headers || []).forEach(h => { if (h.key) headers[h.key] = h.value })
    // 变量替换
    let url = node.props.url
    let body = node.props.body || ''
    ;(scriptTree.props.variables || []).forEach(v => {
      const placeholder = '${' + v.name + '}'
      url = url.replace(placeholder, v.value)
      body = body.replace(placeholder, v.value)
    })
    const res = await autoTestRequest.post('/auto-test/debug/execute', {
      method: node.props.method || 'GET',
      url,
      headers,
      body: node.props.method !== 'GET' ? body : '',
      timeout: 30,
    })
    debugResult.value = res
    if (res.response?.error) {
      ElMessage.warning('请求执行完成但有错误')
    } else {
      ElMessage.success(`${res.response?.status_code} | ${res.response?.elapsed_ms}ms`)
    }
  } catch (e) {
    ElMessage.error('调试请求失败: ' + (e.message || '未知错误'))
  } finally {
    debugLoading.value = false
  }
}

const formatHeaders = (h) => h ? JSON.stringify(h, null, 2) : ''
const formatBody = (b) => {
  if (!b) return ''
  if (typeof b === 'object') return JSON.stringify(b, null, 2)
  try { return JSON.stringify(JSON.parse(b), null, 2) } catch { return String(b) }
}

// ===== JMX 生成 + 下载 =====
const jmxContent = ref('')
const generating = ref(false)
const downloading = ref(false)

const serializeTree = () => {
  const walk = (node) => {
    return {
      type: node.type,
      name: node.name,
      props: JSON.parse(JSON.stringify(node.props)),
      children: (node.children || []).map(walk),
    }
  }
  return scriptTree.children.map(walk)
}

const generatePreview = async () => {
  const serialized = serializeTree()
  generating.value = true
  try {
    const res = await autoTestRequest.post('/auto-test/export/jmeter/tree', {
      tree: serialized,
      plan_name: scriptTree.name,
      plan_variables: scriptTree.props.variables || [],
    })
    jmxContent.value = res.jmx_content || ''
    rightTab.value = 'jmx'
    ElMessage.success('JMX 已生成')
  } catch (e) {
    ElMessage.error('生成失败: ' + (e.response?.data?.detail || e.message))
  } finally { generating.value = false }
}

const downloadJmx = () => {
  if (!jmxContent.value) return
  const blob = new Blob([jmxContent.value], { type: 'application/octet-stream' })
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  const ts = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19)
  a.download = `${scriptTree.name || 'testplan'}_${ts}.jmx`
  a.click()
  ElMessage.success('下载成功！用 JMeter 打开 .jmx 即可运行')
}

// ===== 引导 =====
const showGuide = ref(true)
const wizardStep = ref(1)
const wizardThreads = ref(10)
const wizardLoops = ref(1)
const wizardDuration = ref(60)

const applyWizardConfig = () => {
  scriptTree.children.forEach(tg => {
    if (tg.type === 'ThreadGroup') {
      tg.props.threads = wizardThreads.value
      tg.props.loops = wizardLoops.value
      tg.props.duration = wizardDuration.value
    }
  })
  ElMessage.success('参数已应用到所有线程组')
  wizardStep.value = 3
}

const showTemplates = ref(false)
const templates = [
  {
    key: 'simple', name: '简单 API 测试', icon: '🌐',
    desc: '单接口 GET/POST 请求 + 响应断言 + 查看结果树',
    tags: ['入门', '单接口']
  },
  {
    key: 'login-flow', name: '登录认证流程', icon: '🔐',
    desc: '登录提取 Token → 后续请求自动携带认证头',
    tags: ['常用', '认证', '提取器']
  },
  {
    key: 'crud', name: 'CRUD 全流程', icon: '📦',
    desc: '创建→查询→更新→删除，含数据提取和断言',
    tags: ['完整流程', '数据传递']
  },
  {
    key: 'data-driven', name: 'CSV 数据驱动', icon: '📊',
    desc: '用 CSV 文件参数化测试数据（用户名/密码等）',
    tags: ['参数化', '批量测试']
  },
  {
    key: 'jdbc', name: '数据库压测', icon: '🗄️',
    desc: 'JDBC 连接配置 + SQL 查询 + 聚合报告',
    tags: ['数据库', '高级']
  },
  {
    key: 'auth-chain', name: '认证链向导', icon: '🔗',
    desc: '可视化配置 登录→提取Token→自动注入',
    tags: ['向导', '认证']
  }
]

const addSampleTemplate = (key) => {
  const tpl = templates.find(t => t.key === key)
  if (tpl) applyTemplate(tpl)
}

const applyTemplate = (tpl) => {
  showTemplates.value = false

  if (tpl.key === 'auth-chain') {
    showAuthChain.value = true
    return
  }

  scriptTree.children = []
  scriptTree.props.variables = []

  if (tpl.key === 'simple') {
    const tg = createElement('ThreadGroup', { name: '线程组 - ' + tpl.name, props: { threads: 10, rampUp: 5, loops: 1, duration: 60 } })
    const req = createElement('HttpSampler', { name: 'API 请求', props: { method: 'GET', url: 'https://httpbin.org/get' } })
    const assertion = createElement('ResponseAssertion', { name: '状态码断言', props: { assertType: 'status_code', expected: 200 } })
    const listener = createElement('ViewResultsTree', { name: '查看结果树' })
    req.children.push(assertion)
    tg.children.push(req)
    tg.children.push(listener)
    scriptTree.children.push(tg)
  } else if (tpl.key === 'login-flow') {
    const tg = createElement('ThreadGroup', { name: '线程组 - ' + tpl.name, props: { threads: 10, rampUp: 5, loops: 1, duration: 60 } })
    const login = createElement('HttpSampler', { name: '登录请求', props: { method: 'POST', url: 'https://api.example.com/auth/login', body: '{"username":"admin","password":"123456"}', bodyType: 'json' } })
    login.props.headers = [{ key: 'Content-Type', value: 'application/json' }]
    const extractor = createElement('JsonExtractor', { name: '提取 Token', props: { varName: 'token', jsonPath: '$.data.token', defaultValue: 'NOT_FOUND' } })
    const api = createElement('HttpSampler', { name: '业务请求 (携带Token)', props: { method: 'GET', url: 'https://api.example.com/users/me' } })
    api.props.headers = [{ key: 'Authorization', value: 'Bearer ${token}' }]
    const assertion = createElement('ResponseAssertion', { name: '状态码断言', props: { assertType: 'status_code', expected: 200 } })
    login.children.push(extractor)
    api.children.push(assertion)
    tg.children.push(login)
    tg.children.push(api)
    scriptTree.children.push(tg)
  } else if (tpl.key === 'crud') {
    const tg = createElement('ThreadGroup', { name: 'CRUD 测试', props: { threads: 5, rampUp: 2, loops: 1, duration: 60 } })
    const createReq = createElement('HttpSampler', { name: '1-创建资源', props: { method: 'POST', url: 'https://api.example.com/items', body: '{"name":"test"}', bodyType: 'json' } })
    const getReq = createElement('HttpSampler', { name: '2-查询资源', props: { method: 'GET', url: 'https://api.example.com/items/1' } })
    const updateReq = createElement('HttpSampler', { name: '3-更新资源', props: { method: 'PUT', url: 'https://api.example.com/items/1', body: '{"name":"updated"}', bodyType: 'json' } })
    const deleteReq = createElement('HttpSampler', { name: '4-删除资源', props: { method: 'DELETE', url: 'https://api.example.com/items/1' } })
    tg.children.push(createReq, getReq, updateReq, deleteReq)
    scriptTree.children.push(tg)
  } else if (tpl.key === 'data-driven') {
    const tg = createElement('ThreadGroup', { name: 'CSV 数据驱动测试', props: { threads: 5, rampUp: 2, loops: 3, duration: 120 } })
    const csv = createElement('CSVDataSet', { name: '用户数据', props: { filename: 'users.csv', variableNames: 'username,password', delimiter: ',', recycle: true, csvContent: 'username,password\nuser1,pass1\nuser2,pass2\nuser3,pass3' } })
    const login = createElement('HttpSampler', { name: '参数化登录', props: { method: 'POST', url: 'https://api.example.com/auth/login', body: '{"username":"${username}","password":"${password}"}', bodyType: 'json' } })
    login.props.headers = [{ key: 'Content-Type', value: 'application/json' }]
    const assertion = createElement('ResponseAssertion', { name: '登录成功断言', props: { assertType: 'status_code', expected: 200 } })
    login.children.push(assertion)
    tg.children.push(csv)
    tg.children.push(login)
    scriptTree.children.push(tg)
  } else if (tpl.key === 'jdbc') {
    const tg = createElement('ThreadGroup', { name: '数据库压测', props: { threads: 10, rampUp: 3, loops: 5, duration: 60 } })
    const conn = createElement('JDBCConnection', { name: 'MySQL 连接', props: { dbUrl: 'jdbc:mysql://localhost:3306/testdb', driver: 'com.mysql.cj.jdbc.Driver', dbUser: 'root', dbPass: 'password' } })
    const query = createElement('JDBCSampler', { name: '查询语句', props: { sql: 'SELECT * FROM users WHERE status = "active"' } })
    const listener = createElement('SummaryReport', { name: '聚合报告' })
    tg.children.push(conn)
    tg.children.push(query)
    tg.children.push(listener)
    scriptTree.children.push(tg)
  }

  selectedUid.value = null
  selectedNode.value = null
  ElMessage.success(`已加载「${tpl.name}」模板，请编辑 URL 和参数`)
}

// ===== 认证链 =====
const showAuthChain = ref(false)
const authChain = reactive({
  loginUrl: '',
  loginBody: '{"username":"admin","password":"123456"}',
  extractType: 'JSONPath',
  extractExpr: '$.data.token',
  headerName: 'Authorization',
  testUrl: ''
})

const generateAuthChain = () => {
  if (!authChain.loginUrl) { ElMessage.warning('请输入登录接口 URL'); return }

  const tg = scriptTree.children.find(c => c.type === 'ThreadGroup')
  const targetTg = tg || (() => { const t = createElement('ThreadGroup'); scriptTree.children.push(t); return t })()

  const login = createElement('HttpSampler', { name: '登录', props: { method: 'POST', url: authChain.loginUrl, body: authChain.loginBody, bodyType: 'json' } })
  login.props.headers = [{ key: 'Content-Type', value: 'application/json' }]

  const extractorType = authChain.extractType === 'JSONPath' ? 'JsonExtractor' : 'RegexExtractor'
  const extractor = createElement(extractorType, { name: '提取认证Token', props: { varName: 'auth_token', jsonPath: authChain.extractExpr, regex: authChain.extractExpr, defaultValue: 'NOT_FOUND' } })
  login.children.push(extractor)

  targetTg.children.push(login)

  if (authChain.testUrl) {
    const api = createElement('HttpSampler', { name: '测试请求 (携带Token)', props: { method: 'GET', url: authChain.testUrl } })
    const prefix = authChain.headerName === 'Authorization' ? 'Bearer ' : ''
    api.props.headers = [{ key: authChain.headerName, value: `${prefix}\${auth_token}` }]
    const assertion = createElement('ResponseAssertion', { name: '状态码断言', props: { assertType: 'status_code', expected: 200 } })
    api.children.push(assertion)
    targetTg.children.push(api)
  }

  showAuthChain.value = false
  ElMessage.success('认证链已生成！选中登录请求点击调试验证')
}

// ===== 保存采样器到接口库 =====
const showSaveToCase = ref(false)
const saveCaseName = ref('')
const saveCaseMethod = ref('')
const saveCaseUrl = ref('')
const saveGroupId = ref(null)
const savingToCase = ref(false)
const caseGroups = ref([])

const loadCaseGroups = async () => {
  try {
    const res = await autoTestRequest.get('/auto-test/groups')
    caseGroups.value = Array.isArray(res) ? res : (res.groups || res.data || [])
  } catch (e) { console.error('加载分组失败:', e) }
}

const saveSamplerToCase = (node) => {
  if (!node || node.type !== 'HttpSampler') return
  saveCaseName.value = node.name
  saveCaseMethod.value = node.props.method || 'GET'
  saveCaseUrl.value = node.props.url || ''
  if (caseGroups.value.length > 0 && !saveGroupId.value) {
    saveGroupId.value = caseGroups.value[0].id
  }
  showSaveToCase.value = true
}

const confirmSaveToCase = async () => {
  if (!saveCaseName.value) { ElMessage.warning('请输入用例名称'); return }
  if (!saveGroupId.value && caseGroups.value.length === 0) {
    try {
      await autoTestRequest.post('/auto-test/groups', { name: 'JMeter 导入', parent_id: null })
      await loadCaseGroups()
      if (caseGroups.value.length > 0) saveGroupId.value = caseGroups.value[0].id
    } catch { /* 忽略创建分组失败 */ }
  }
  if (!saveGroupId.value) { ElMessage.warning('请先选择一个分组'); return }
  savingToCase.value = true
  try {
    await autoTestRequest.post('/auto-test/cases', {
      group_id: saveGroupId.value,
      name: saveCaseName.value,
      method: saveCaseMethod.value,
      url: saveCaseUrl.value,
      headers: selectedNode.value?.props?.headers?.reduce((acc, h) => { if (h.key) acc[h.key] = h.value; return acc }, {}) || {},
      body_type: 'json',
      payload: (() => { try { return JSON.parse(selectedNode.value?.props?.body || '{}') } catch { return {} } })()
    })
    ElMessage.success('已保存到接口库')
    showSaveToCase.value = false
    loadCases()
  } catch (e) {
    ElMessage.error('保存失败: ' + (e.response?.data?.detail || e.message))
  } finally { savingToCase.value = false }
}

// ===== 初始化 =====
onMounted(() => {
  loadCases()
  loadEnvironments()
  loadCaseGroups()
  if (scriptTree.children.length === 0) {
    addRootElement()
  }
})
</script>

<style scoped>
.jmeter-ide { display: flex; flex-direction: column; height: calc(100vh - 60px); background: var(--tm-bg); color: var(--tm-text-primary); padding: 12px; }
.ide-toolbar { display: flex; justify-content: space-between; align-items: center; padding-bottom: 12px; border-bottom: 1px solid var(--tm-border); gap: 12px; flex-wrap: wrap; }
.toolbar-left { display: flex; align-items: center; gap: 8px; }
.ide-title { font-size: 18px; margin: 0; }
.toolbar-center { display: flex; gap: 4px; }
.toolbar-right { display: flex; gap: 6px; }
.guide-banner { margin: 8px 0; }
.ide-body { display: grid; grid-template-columns: 260px 1fr 1fr; gap: 12px; flex: 1; min-height: 0; margin-top: 8px; }

/* 面板通用 */
.panel { display: flex; flex-direction: column; background: var(--tm-card-bg); border: 1px solid var(--tm-border); border-radius: 10px; overflow: hidden; }
.panel-header { display: flex; justify-content: space-between; align-items: center; padding: 10px 12px; border-bottom: 1px solid var(--tm-border); font-weight: 600; font-size: 13px; }
.tree-body { flex: 1; overflow-y: auto; padding: 4px; }
.tree-empty { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 200px; color: var(--tm-text-secondary); gap: 8px; text-align: center; font-size: 13px; }

/* 编辑器 */
.editor-body { flex: 1; overflow-y: auto; padding: 12px; }
.editor-empty { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; color: var(--tm-text-secondary); gap: 8px; text-align: center; }
.form-group { margin-bottom: 12px; }
.form-group label { display: block; font-size: 12px; font-weight: 600; margin-bottom: 4px; color: var(--tm-text-secondary); }
.form-row { display: flex; gap: 8px; }
.form-row .form-group { flex: 1; }
.var-row { display: flex; gap: 4px; align-items: center; margin-bottom: 4px; }

/* 调试面板 */
.right-tabs { height: 100%; display: flex; flex-direction: column; }
.right-tabs :deep(.el-tabs__content) { flex: 1; overflow: hidden; }
.right-tabs :deep(.el-tab-pane) { height: 100%; overflow-y: auto; }
.code-preview { background: #0d1117; padding: 12px; font-size: 12px; font-family: 'Consolas', monospace; color: #c9d1d9; height: 100%; overflow: auto; }
.code-preview pre { margin: 0; white-space: pre-wrap; }
.empty-hint { display: flex; align-items: center; justify-content: center; height: 100%; color: var(--tm-text-secondary); font-size: 13px; text-align: center; }
.debug-meta { display: flex; gap: 12px; align-items: center; margin-bottom: 8px; padding: 8px; background: rgba(255,255,255,0.03); border-radius: 6px; }
.debug-elapsed { font-size: 13px; font-weight: 600; color: #4ADE80; }
.debug-size { font-size: 12px; color: var(--tm-text-secondary); }
.debug-json { background: #0d1117; padding: 8px; border-radius: 4px; font-size: 11px; color: #c9d1d9; font-family: 'Consolas', monospace; max-height: 300px; overflow: auto; margin: 0; }
.debug-error { margin-top: 8px; }
.debug-area { padding: 8px; }

/* 对话框 */
.case-import-list { max-height: 400px; overflow-y: auto; }
.case-import-item { padding: 4px 0; }
.case-method { font-size: 11px; font-weight: 700; padding: 1px 5px; border-radius: 3px; margin-right: 4px; }
.method-get { background: rgba(74,222,128,0.15); color: #4ADE80; }
.method-post { background: rgba(236,72,153,0.15); color: #EC4899; }
.method-put { background: rgba(250,204,21,0.15); color: #FACC15; }
.method-delete { background: rgba(248,113,113,0.15); color: #F87171; }
.env-item { padding: 6px 0; }
.env-url { font-size: 11px; color: var(--tm-text-secondary); margin-left: 8px; }
.form-hint { font-size: 11px; color: #6b7280; margin-bottom: 8px; font-family: monospace; }
.mb-8 { margin-bottom: 8px; }

/* Quick Start Wizard */
.quick-start-wizard { background: linear-gradient(135deg, rgba(64,158,255,0.06), rgba(139,92,246,0.06)); border: 1px solid var(--tm-border); border-radius: 12px; padding: 16px; margin-bottom: 12px; }
.wizard-header { margin-bottom: 12px; }
.wizard-title-row { display: flex; align-items: center; gap: 12px; }
.wizard-icon { font-size: 28px; }
.wizard-steps { display: flex; align-items: center; gap: 8px; margin-bottom: 12px; padding: 10px; background: var(--tm-bg-card); border-radius: 8px; flex-wrap: wrap; }
.wizard-step { display: flex; align-items: center; gap: 6px; padding: 6px 12px; border-radius: 6px; cursor: pointer; transition: all .2s; border: 1px solid transparent; }
.wizard-step.active { border-color: var(--tm-color-primary); background: rgba(64,158,255,0.08); }
.wizard-step.done { opacity: 0.7; }
.wstep-num { width: 22px; height: 22px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 700; background: var(--tm-bg-secondary); color: var(--tm-text-secondary); }
.wizard-step.active .wstep-num { background: var(--tm-color-primary); color: #fff; }
.wstep-arrow { color: var(--tm-text-secondary); font-weight: 700; }
.wstep-label small { font-size: 10px; color: var(--tm-text-secondary); }
.wizard-body { min-height: 80px; }
.wizard-card { padding: 8px 0; }
.wizard-actions { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 8px; }

/* Template Grid */
.template-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; }
.template-card { display: flex; gap: 10px; padding: 12px; background: var(--tm-bg-card); border: 1px solid var(--tm-border); border-radius: 10px; cursor: pointer; transition: all .2s; }
.template-card:hover { border-color: var(--tm-color-primary); background: rgba(64,158,255,0.05); transform: translateY(-1px); }
.tpl-icon { font-size: 28px; flex-shrink: 0; }
.tpl-info strong { font-size: 13px; display: block; margin-bottom: 4px; }
.tpl-info p { font-size: 11px; color: var(--tm-text-secondary); margin: 0 0 6px; }
.tpl-tags { display: flex; gap: 4px; flex-wrap: wrap; }
</style>
