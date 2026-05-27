<template>
  <div class="jmeter-workspace">
    <!-- 步骤导航 -->
    <div class="step-nav">
      <div class="step" :class="{active: currentStep >= 1, done: currentStep > 1}" @click="currentStep = 1">
        <span class="step-num">{{ currentStep > 1 ? '✓' : '1' }}</span>
        <span class="step-label">选择接口</span>
      </div>
      <span class="step-arrow">→</span>
      <div class="step" :class="{active: currentStep >= 2, done: currentStep > 2}" @click="currentStep >= 2 ? currentStep = 2 : null">
        <span class="step-num">{{ currentStep > 2 ? '✓' : '2' }}</span>
        <span class="step-label">配置压测参数</span>
      </div>
      <span class="step-arrow">→</span>
      <div class="step" :class="{active: currentStep >= 3}" @click="currentStep >= 3 ? currentStep = 3 : null">
        <span class="step-num">3</span>
        <span class="step-label">导出 JMX</span>
      </div>
      <div class="step-actions">
        <el-button size="small" type="primary" @click="generatePreview" :loading="generating">
          <el-icon><Refresh /></el-icon> 生成预览
        </el-button>
        <el-button size="small" type="success" @click="downloadJmx" :disabled="!jmxContent">
          <el-icon><Download /></el-icon> 下载 .jmx
        </el-button>
        <el-button size="small" @click="showGuide = !showGuide">
          <el-icon><QuestionFilled /></el-icon> 帮助
        </el-button>
      </div>
    </div>

    <!-- 快速帮助面板 -->
    <el-collapse-transition>
      <div v-if="showGuide" class="guide-panel">
        <el-alert title="JMeter 压测脚本三步搞定" type="info" :closable="false" show-icon>
          <template #default>
            <p style="margin:4px 0"><strong>第1步 · 选择接口</strong> — 从接口库导入 API（推荐），或用模板快速创建脚本</p>
            <p style="margin:4px 0"><strong>第2步 · 配置压测参数</strong> — 设置并发线程数、循环次数、断言、提取器等</p>
            <p style="margin:4px 0"><strong>第3步 · 导出 JMX</strong> — 生成预览并下载 .jmx 文件，用 JMeter 直接运行</p>
          </template>
        </el-alert>
      </div>
    </el-collapse-transition>

    <!-- ==================== Step 1: 选择接口 ==================== -->
    <div v-show="currentStep === 1" class="step-body">
      <div class="step1-layout">
        <div class="panel step1-templates">
          <div class="panel-title">📦 模板快速创建</div>
          <div class="template-grid">
            <div class="tpl-card" v-for="tpl in templates" :key="tpl.key" @click="applyTemplate(tpl)">
              <div class="tpl-icon">{{ tpl.icon }}</div>
              <div class="tpl-name">{{ tpl.name }}</div>
              <div class="tpl-desc">{{ tpl.desc }}</div>
            </div>
          </div>
        </div>
        <div class="panel step1-import">
          <div class="panel-title">📋 从接口库导入</div>
          <div class="import-controls">
            <el-select v-model="importGroupFilter" placeholder="按分组筛选" size="default" clearable filterable style="width:240px">
              <el-option v-for="g in importGroups" :key="g.id" :label="g.name" :value="g.id" />
            </el-select>
            <el-input v-model="caseSearch" placeholder="搜索接口名称或URL..." size="default" clearable prefix-icon="Search" style="flex:1" />
          </div>
          <div class="import-case-list">
            <div v-if="allCases.length === 0" class="empty-state">
              <el-icon size="28"><FolderDelete /></el-icon>
              <p>当前分组没有接口用例</p>
              <el-button link type="primary" size="small" @click="openInterfaceLib">去接口库创建</el-button>
            </div>
            <el-checkbox-group v-model="selectedImportCases" v-else>
              <div v-for="c in filteredImportCases" :key="c.id" class="import-case-item" @click="toggleCase(c.id)">
                <el-checkbox :label="c.id" @click.stop>
                  <span class="case-method" :class="'m-' + (c.method||'GET').toLowerCase()">{{ c.method }}</span>
                  <span class="case-name">{{ c.name }}</span>
                  <span class="case-url">{{ c.url }}</span>
                </el-checkbox>
              </div>
            </el-checkbox-group>
            <div v-if="filteredImportCases.length === 0 && allCases.length > 0" class="empty-state">
              无匹配结果
            </div>
          </div>
          <div class="import-footer">
            <span class="import-count">已选 {{ selectedImportCases.length }} 个接口</span>
            <div>
              <el-button @click="showImportJmxDialog = true">📂 导入 .jmx 文件</el-button>
              <el-button type="primary" :disabled="selectedImportCases.length === 0" @click="importSelectedCases">
                导入到脚本 → <el-icon><Right /></el-icon>
              </el-button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ==================== Step 2: 配置参数 ==================== -->
    <div v-show="currentStep === 2" class="step-body">
      <div class="step2-layout">
        <div class="panel tree-panel">
          <div class="panel-title">
            <span>📋 脚本结构</span>
            <el-tag size="small" type="info">{{ totalSamplers }} 个请求</el-tag>
          </div>
          <div class="tree-body">
            <div class="tree-root-label" @click="selectNode(scriptTree.uid)">
              <span class="root-icon">📋</span>
              <span>{{ scriptTree.name }}</span>
              <el-button link size="small" @click.stop="addRootElement" style="margin-left:auto">
                <el-icon><Plus /></el-icon> 添加线程组
              </el-button>
            </div>
            <jmeter-tree-node
              v-for="(node, idx) in scriptTree.children"
              :key="node.uid"
              :node="node"
              :depth="0"
              :selected-uid="selectedUid"
              @select="selectNode"
              @remove="removeNodeByUid"
              @add-child="addChildNode"
              @duplicate="duplicateNode"
            />
            <div v-if="scriptTree.children.length === 0" class="tree-empty">
              还没有线程组，点击上方「添加线程组」或返回第1步导入接口
            </div>
          </div>
        </div>

        <div class="panel editor-panel">
          <div class="panel-title">
            <span>✏️ {{ selectedNode ? selectedNode.name : '元素编辑器' }}</span>
            <el-tag v-if="selectedNode" size="small">{{ NODE_TYPES[selectedNode.type]?.label || selectedNode.type }}</el-tag>
          </div>
          <div class="editor-body" v-if="selectedNode">
            <!-- 测试计划 -->
            <template v-if="selectedNode.type === 'TestPlan'">
              <div class="form-section">
                <div class="form-group"><label>测试计划名称</label><el-input v-model="selectedNode.name" /></div>
                <div class="form-group"><label>用户定义变量</label>
                  <div v-for="(v, vi) in (selectedNode.props.variables || [])" :key="vi" class="kv-row">
                    <el-input v-model="v.name" placeholder="变量名" size="small" style="width:42%" />
                    <el-input v-model="v.value" placeholder="值" size="small" style="width:42%" />
                    <el-button link size="small" type="danger" @click="selectedNode.props.variables.splice(vi,1)">×</el-button>
                  </div>
                  <el-button size="small" @click="addVar">+ 添加变量</el-button>
                </div>
              </div>
            </template>

            <!-- 线程组 -->
            <template v-if="selectedNode.type === 'ThreadGroup'">
              <div class="form-section">
                <div class="section-hint">配置虚拟用户数、启动方式和运行时长</div>
                <div class="form-group"><label>线程组名称</label><el-input v-model="selectedNode.name" size="small" /></div>
                <div class="form-row">
                  <div class="form-group"><label>并发线程数</label><el-input-number v-model="selectedNode.props.threads" :min="1" :max="10000" size="small" /></div>
                  <div class="form-group"><label>Ramp-Up (秒)</label><el-input-number v-model="selectedNode.props.rampUp" :min="0" :max="3600" size="small" /></div>
                </div>
                <div class="form-row">
                  <div class="form-group"><label>循环次数</label><el-input-number v-model="selectedNode.props.loops" :min="1" :max="99999" size="small" /></div>
                  <div class="form-group"><label>持续时间 (秒)</label><el-input-number v-model="selectedNode.props.duration" :min="0" :max="86400" size="small" /></div>
                </div>
                <el-alert v-if="selectedNode.props.loops >= 99999 && !selectedNode.props.duration"
                  title="⚠️ 此脚本将永久循环运行！请设置持续时间" type="error" :closable="false" show-icon />
              </div>
              <div class="form-section">
                <div class="section-hint">添加监听器来查看测试结果</div>
                <div style="display:flex;gap:6px;flex-wrap:wrap">
                  <el-button size="small" @click="addChildToCurrent('ViewResultsTree')">👁️ 查看结果树</el-button>
                  <el-button size="small" @click="addChildToCurrent('SummaryReport')">📈 聚合报告</el-button>
                  <el-button size="small" @click="addChildToCurrent('CSVDataSet')">📄 CSV 数据源</el-button>
                  <el-button size="small" @click="addChildToCurrent('JDBCSampler')">🗄️ JDBC 请求</el-button>
                </div>
              </div>
            </template>

            <!-- HTTP 请求 -->
            <template v-if="selectedNode.type === 'HttpSampler'">
              <div class="form-section">
                <div class="section-hint">配置要压测的接口地址和参数</div>
                <div class="form-group"><label>请求名称</label><el-input v-model="selectedNode.name" size="small" /></div>
                <div class="form-row">
                  <div class="form-group" style="flex:0 0 120px"><label>方法</label>
                    <el-select v-model="selectedNode.props.method" size="small">
                      <el-option v-for="m in ['GET','POST','PUT','DELETE','PATCH']" :key="m" :label="m" :value="m" />
                    </el-select>
                  </div>
                  <div class="form-group" style="flex:1"><label>URL</label><el-input v-model="selectedNode.props.url" size="small" placeholder="https://api.example.com/users" /></div>
                </div>
                <el-collapse>
                  <el-collapse-item title="请求头 (Headers)" name="headers">
                    <div v-for="(h, hi) in (selectedNode.props.headers || [])" :key="hi" class="kv-row">
                      <el-input v-model="h.key" placeholder="Header名" size="small" style="width:40%" />
                      <el-input v-model="h.value" placeholder="值" size="small" style="width:50%" />
                      <el-button link size="small" type="danger" @click="selectedNode.props.headers.splice(hi,1)">×</el-button>
                    </div>
                    <el-button size="small" @click="addHeader">+ 添加请求头</el-button>
                  </el-collapse-item>
                  <el-collapse-item v-if="selectedNode.props.method !== 'GET'" title="请求体 (Body)" name="body">
                    <div class="form-group"><label>Body 类型</label>
                      <el-select v-model="selectedNode.props.bodyType" size="small">
                        <el-option v-for="b in ['none','json','form-data','x-www-form-urlencoded']" :key="b" :label="b" :value="b" />
                      </el-select>
                    </div>
                    <el-input v-model="selectedNode.props.body" type="textarea" :rows="4" size="small" placeholder='{"key":"value"}' />
                  </el-collapse-item>
                </el-collapse>
              </div>
              <div class="form-section">
                <div class="section-hint">添加子元素：断言验证结果、提取器传递数据、定时器控制节奏</div>
                <div style="display:flex;gap:6px;flex-wrap:wrap">
                  <el-button size="small" @click="addChildToCurrent('ResponseAssertion')">✅ 响应断言</el-button>
                  <el-button size="small" @click="addChildToCurrent('JsonExtractor')">📤 JSON 提取器</el-button>
                  <el-button size="small" @click="addChildToCurrent('RegexExtractor')">🔍 正则提取器</el-button>
                  <el-button size="small" @click="addChildToCurrent('ConstantTimer')">⏰ 固定定时器</el-button>
                  <el-button size="small" @click="addChildToCurrent('BeanShellPreProcessor')">⚙️ BeanShell</el-button>
                </div>
              </div>
              <div class="form-section">
                <el-button type="primary" size="small" @click="debugRequest(selectedNode)" :loading="debugLoading">
                  <el-icon><VideoPlay /></el-icon> 🐛 调试此请求
                </el-button>
                <el-button size="small" @click="saveSamplerToCase(selectedNode)" :loading="savingToCase">
                  💾 保存到接口库
                </el-button>
              </div>
            </template>

            <!-- 子元素编辑器：断言 / 提取器 / 定时器 / CSV / JDBC / BeanShell / 监听器 -->
            <template v-if="selectedNode.type === 'ResponseAssertion'">
              <div class="form-section">
                <div class="form-group"><label>断言名称</label><el-input v-model="selectedNode.name" size="small" /></div>
                <div class="form-group"><label>断言类型</label>
                  <el-select v-model="selectedNode.props.assertType" size="small">
                    <el-option label="状态码" value="status_code" />
                    <el-option label="响应包含" value="contains" />
                    <el-option label="响应匹配" value="matches" />
                    <el-option label="JSON Path" value="jsonpath" />
                    <el-option label="持续时间" value="duration" />
                  </el-select>
                </div>
                <div class="form-group" v-if="selectedNode.props.assertType === 'status_code'"><label>期望状态码</label><el-input-number v-model="selectedNode.props.expected" :min="100" :max="599" size="small" /></div>
                <div class="form-group" v-if="selectedNode.props.assertType === 'contains' || selectedNode.props.assertType === 'matches'"><label>期望值</label><el-input v-model="selectedNode.props.expected" size="small" /></div>
                <div class="form-group" v-if="selectedNode.props.assertType === 'jsonpath'"><label>JSON Path</label><el-input v-model="selectedNode.props.jsonPath" placeholder="$.data.token" size="small" /><label style="margin-top:4px">期望值</label><el-input v-model="selectedNode.props.expected" size="small" /></div>
                <div class="form-group" v-if="selectedNode.props.assertType === 'duration'"><label>最大响应时间 (ms)</label><el-input-number v-model="selectedNode.props.maxDuration" :min="1" :max="60000" size="small" /></div>
              </div>
            </template>
            <template v-if="selectedNode.type === 'RegexExtractor' || selectedNode.type === 'JsonExtractor'">
              <div class="form-section">
                <div class="form-group"><label>提取器名称</label><el-input v-model="selectedNode.name" size="small" /></div>
                <div class="form-group"><label>变量名</label><el-input v-model="selectedNode.props.varName" placeholder="token" size="small" /></div>
                <div class="form-hint">后续请求中用 <code>{'{'+'$'+'{'+'}'+'}变量名'}</code> 引用</div>
                <div class="form-group" v-if="selectedNode.type === 'RegexExtractor'"><label>正则表达式</label><el-input v-model="selectedNode.props.regex" placeholder='"token":"(.*?)"' size="small" /></div>
                <div class="form-group" v-if="selectedNode.type === 'JsonExtractor'"><label>JSON Path</label><el-input v-model="selectedNode.props.jsonPath" placeholder="$.data.token" size="small" /></div>
                <div class="form-group"><label>默认值</label><el-input v-model="selectedNode.props.defaultValue" placeholder="NOT_FOUND" size="small" /></div>
              </div>
            </template>
            <template v-if="selectedNode.type === 'ConstantTimer'">
              <div class="form-section"><div class="form-group"><label>延迟 (毫秒)</label><el-input-number v-model="selectedNode.props.delay" :min="0" :max="60000" size="small" /></div></div>
            </template>
            <template v-if="selectedNode.type === 'UniformRandomTimer'">
              <div class="form-section"><div class="form-row"><div class="form-group"><label>最小延迟 (ms)</label><el-input-number v-model="selectedNode.props.minDelay" :min="0" size="small" /></div><div class="form-group"><label>最大延迟 (ms)</label><el-input-number v-model="selectedNode.props.maxDelay" :min="1" size="small" /></div></div></div>
            </template>
            <template v-if="selectedNode.type === 'GaussianRandomTimer'">
              <div class="form-section"><div class="form-row"><div class="form-group"><label>偏差 (ms)</label><el-input-number v-model="selectedNode.props.deviation" :min="0" :max="60000" size="small" /></div><div class="form-group"><label>偏移 (ms)</label><el-input-number v-model="selectedNode.props.offset" :min="0" :max="60000" size="small" /></div></div></div>
            </template>
            <template v-if="selectedNode.type === 'SyncTimer'">
              <div class="form-section"><div class="form-group"><label>集合点并发数</label><el-input-number v-model="selectedNode.props.groupSize" :min="2" :max="10000" size="small" /></div></div>
            </template>
            <template v-if="selectedNode.type === 'CSVDataSet'">
              <div class="form-section">
                <div class="form-group"><label>CSV 文件名</label><el-input v-model="selectedNode.props.filename" placeholder="users.csv" size="small" /></div>
                <div class="form-group"><label>变量名 (逗号分隔)</label><el-input v-model="selectedNode.props.variableNames" placeholder="username,password" size="small" /></div>
                <div class="form-row"><div class="form-group"><label>分隔符</label><el-input v-model="selectedNode.props.delimiter" size="small" style="width:60px" /></div><div class="form-group"><label>循环</label><el-switch v-model="selectedNode.props.recycle" size="small" /></div></div>
                <div class="form-group"><label>CSV 内容 (随 .jmx 导出)</label><el-input v-model="selectedNode.props.csvContent" type="textarea" :rows="4" placeholder="username,password&#10;user1,pass1" size="small" /></div>
              </div>
            </template>
            <template v-if="selectedNode.type === 'JDBCConnection'">
              <div class="form-section">
                <div class="form-group"><label>连接名称</label><el-input v-model="selectedNode.name" size="small" /></div>
                <div class="form-group"><label>数据库 URL</label><el-input v-model="selectedNode.props.dbUrl" placeholder="jdbc:mysql://host:port/db" size="small" /></div>
                <div class="form-row"><div class="form-group"><label>驱动类</label><el-input v-model="selectedNode.props.driver" placeholder="com.mysql.cj.jdbc.Driver" size="small" /></div><div class="form-group"><label>用户名</label><el-input v-model="selectedNode.props.dbUser" size="small" /></div></div>
                <div class="form-group"><label>密码</label><el-input v-model="selectedNode.props.dbPass" type="password" size="small" show-password /></div>
              </div>
            </template>
            <template v-if="selectedNode.type === 'JDBCSampler'">
              <div class="form-section"><div class="form-group"><label>SQL 查询</label><el-input v-model="selectedNode.props.sql" type="textarea" :rows="3" placeholder="SELECT * FROM users WHERE status = 'active'" size="small" /></div></div>
            </template>
            <template v-if="selectedNode.type === 'BeanShellPreProcessor' || selectedNode.type === 'BeanShellPostProcessor'">
              <div class="form-section">
                <div class="form-group"><label>脚本名称</label><el-input v-model="selectedNode.name" size="small" /></div>
                <div class="form-group"><label>BeanShell 脚本</label><el-input v-model="selectedNode.props.script" type="textarea" :rows="6" placeholder='long ts = System.currentTimeMillis(); vars.put("ts",String.valueOf(ts));' size="small" /></div>
              </div>
            </template>
            <template v-if="selectedNode.type === 'ViewResultsTree' || selectedNode.type === 'SummaryReport' || selectedNode.type === 'AggregateGraph'">
              <div class="form-section"><div class="form-group"><label>监听器名称</label><el-input v-model="selectedNode.name" size="small" /></div></div>
            </template>
          </div>
          <div class="editor-empty" v-else>
            <el-icon size="36"><EditPen /></el-icon>
            <p>选择左侧树中的元素<br/>开始编辑属性</p>
          </div>
          <!-- 自然语言描述 -->
          <div class="summary-bar" v-if="scriptTree.children.length > 0">
            <span class="summary-icon">💡</span>
            <span class="summary-text">{{ naturalLanguageSummary }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- ==================== Step 3: 导出 ==================== -->
    <div v-show="currentStep === 3" class="step-body">
      <div class="step3-layout">
        <div class="panel export-preview">
          <div class="panel-title">
            <span>🔮 JMX 预览</span>
            <div>
              <el-button size="small" @click="generatePreview" :loading="generating">
                <el-icon><Refresh /></el-icon> 刷新
              </el-button>
              <el-button size="small" type="success" @click="downloadJmx" :disabled="!jmxContent">
                <el-icon><Download /></el-icon> 下载 .jmx 文件
              </el-button>
            </div>
          </div>
          <div class="preview-body">
            <pre v-if="jmxContent" class="xml-preview"><code>{{ jmxContent }}</code></pre>
            <div v-else class="empty-hint">
              <el-icon size="36"><Document /></el-icon>
              <p>点击「生成预览」查看 JMX 内容</p>
              <el-button type="primary" @click="generatePreview" :loading="generating">🔮 生成预览</el-button>
            </div>
          </div>
        </div>
        <div class="panel export-debug">
          <el-tabs v-model="rightTab3" class="right-tabs">
            <el-tab-pane label="🐛 调试" name="debug">
              <div class="debug-body">
                <div v-if="debugResult" class="debug-content">
                  <div class="debug-meta">
                    <el-tag :type="debugResult.response?.status_code === 200 ? 'success' : 'danger'" size="small">
                      {{ debugResult.response?.status_code || 'ERR' }}
                    </el-tag>
                    <span class="debug-elapsed">{{ debugResult.response?.elapsed_ms || 0 }}ms</span>
                    <span class="debug-size">{{ (debugResult.response?.body_size || 0) }}B</span>
                  </div>
                  <el-collapse>
                    <el-collapse-item title="响应体" name="body">
                      <pre class="debug-json">{{ formatBody(debugResult.response?.body) }}</pre>
                    </el-collapse-item>
                    <el-collapse-item title="响应头" name="headers">
                      <pre class="debug-json">{{ formatHeaders(debugResult.response?.headers) }}</pre>
                    </el-collapse-item>
                    <el-collapse-item title="请求详情" name="request">
                      <pre class="debug-json">{{ formatBody(debugResult.request) }}</pre>
                    </el-collapse-item>
                  </el-collapse>
                  <div v-if="debugResult.response?.error" class="debug-error">
                    <el-alert :title="debugResult.response.error" type="error" show-icon />
                  </div>
                </div>
                <div v-else class="empty-hint">
                  <p>在「配置参数」步骤中<br/>选中一个 HTTP 请求点击「调试」</p>
                </div>
              </div>
            </el-tab-pane>
            <el-tab-pane label="⚡ 并发验证" name="bench">
              <div class="bench-body">
                <el-alert title="在线快速并发验证：不下 .jmx，不打开 JMeter，直接测试 N 个并发能否跑通" type="info" :closable="false" show-icon style="margin-bottom:8px;font-size:11px" />
                <div class="bench-controls">
                  <div class="form-group"><label>并发数</label><el-input-number v-model="benchConcurrency" :min="1" :max="200" size="small" /></div>
                  <div class="form-group"><label>持续(秒)</label><el-input-number v-model="benchDuration" :min="3" :max="60" size="small" /></div>
                  <div class="form-group"><label>预热(秒)</label><el-input-number v-model="benchRampUp" :min="0" :max="10" size="small" /></div>
                </div>
                <el-button v-if="!benching" type="danger" @click="startBench" style="width:100%;margin-bottom:8px">
                  ⚡ 开始测试（{{ benchConcurrency }} 并发 × {{ benchDuration }}秒）
                </el-button>
                <el-button v-else type="warning" @click="stopBench" style="width:100%;margin-bottom:8px">
                  ⏹ 停止轮询（测试仍在后台执行）
                </el-button>
                <div v-if="benching || benchProgress" class="bench-progress">
                  <el-progress :percentage="benchPercent" :stroke-width="8" :status="benchPercent >= 100 ? 'success' : ''" />
                  <span class="bench-progress-text">{{ benchProgress }}</span>
                </div>
                <div v-if="benchResult" class="bench-result">
                  <div class="bench-stats">
                    <div class="bench-stat">
                      <span class="bench-stat-value" :class="benchResult.failed > 0 ? 'text-danger' : 'text-success'">{{ benchResult.total }}</span>
                      <span class="bench-stat-label">总请求</span>
                    </div>
                    <div class="bench-stat">
                      <span class="bench-stat-value text-success">{{ benchResult.success }}</span>
                      <span class="bench-stat-label">成功</span>
                    </div>
                    <div class="bench-stat">
                      <span class="bench-stat-value" :class="benchResult.failed > 0 ? 'text-danger' : ''">{{ benchResult.failed }}</span>
                      <span class="bench-stat-label">失败</span>
                    </div>
                    <div class="bench-stat">
                      <span class="bench-stat-value">{{ benchResult.tps }}</span>
                      <span class="bench-stat-label">TPS</span>
                    </div>
                    <div class="bench-stat">
                      <span class="bench-stat-value">{{ benchResult.avg_ms }}ms</span>
                      <span class="bench-stat-label">平均</span>
                    </div>
                    <div class="bench-stat">
                      <span class="bench-stat-value">{{ benchResult.p95_ms }}ms</span>
                      <span class="bench-stat-label">P95</span>
                    </div>
                    <div class="bench-stat">
                      <span class="bench-stat-value">{{ benchResult.p99_ms }}ms</span>
                      <span class="bench-stat-label">P99</span>
                    </div>
                    <div class="bench-stat">
                      <span class="bench-stat-value">{{ benchResult.min_ms }}ms</span>
                      <span class="bench-stat-label">最慢</span>
                    </div>
                  </div>
                  <div style="margin-top:8px">
                    <div style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:4px">
                      <el-tag v-for="(count, code) in benchResult.status_distribution" :key="code" :type="code === '200' ? 'success' : code >= '400' ? 'danger' : 'warning'" size="small">
                        HTTP {{ code }}: {{ count }}
                      </el-tag>
                    </div>
                    <div v-if="benchResult.errors && benchResult.errors.length > 0" style="margin-top:4px">
                      <el-alert v-for="(err, ei) in benchResult.errors.slice(0,5)" :key="ei" :title="err" type="error" :closable="false" show-icon style="margin-bottom:2px;font-size:11px" />
                    </div>
                  </div>
                </div>
              </div>
            </el-tab-pane>
          </el-tabs>
        </div>
      </div>
    </div>

    <!-- ===== 导入 .jmx 对话框 ===== -->
    <el-dialog v-model="showImportJmxDialog" title="导入 .jmx 文件" width="500px">
      <el-upload drag accept=".jmx" :auto-upload="false" :on-change="handleJmxFileChange" :limit="1">
        <el-icon size="40"><UploadFilled /></el-icon>
        <div style="margin-top:8px">将 .jmx 文件拖到此处，或点击选择</div>
      </el-upload>
      <template #footer>
        <el-button @click="showImportJmxDialog = false">取消</el-button>
        <el-button type="primary" :disabled="!jmxImportFile" :loading="jmxImporting" @click="confirmImportJmx">导入</el-button>
      </template>
    </el-dialog>

    <!-- ===== 保存到接口库对话框 ===== -->
    <el-dialog v-model="showSaveToCase" title="保存到接口库" width="450px">
      <div class="form-group"><label>用例名称</label><el-input v-model="saveCaseName" size="small" /></div>
      <div class="form-group"><label>保存到分组</label>
        <el-select v-model="saveGroupId" size="small" filterable placeholder="选择分组">
          <el-option v-for="g in caseGroups" :key="g.id" :label="g.name" :value="g.id" />
        </el-select>
      </div>
      <template #footer>
        <el-button @click="showSaveToCase = false">取消</el-button>
        <el-button type="primary" @click="confirmSaveToCase" :loading="savingToCase">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, Refresh, Download, Right, QuestionFilled, VideoPlay, EditPen, FolderDelete, Search, UploadFilled } from '@element-plus/icons-vue'
import autoTestRequest from '@/utils/autoTestRequest'
import JmeterTreeNode from '@/components/JmeterTreeNode.vue'

// ===== 组件类型定义 =====
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
  BeanShellPreProcessor: { label: 'BeanShell 前置', icon: '⚙️', parent: 'HttpSampler' },
  BeanShellPostProcessor: { label: 'BeanShell 后置', icon: '⚙️', parent: 'HttpSampler' },
  JDBCConnection: { label: 'JDBC 连接', icon: '🗄️', parent: 'TestPlan' },
  JDBCSampler: { label: 'JDBC 请求', icon: '🗄️', parent: 'ThreadGroup' },
  ViewResultsTree: { label: '查看结果树', icon: '👁️', parent: 'ThreadGroup' },
  SummaryReport: { label: '聚合报告', icon: '📈', parent: 'ThreadGroup' },
  AggregateGraph: { label: '聚合图表', icon: '📉', parent: 'ThreadGroup' },
}

// ===== 工具函数 =====
let uidCounter = 1
const newUid = () => `el_${uidCounter++}`

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

const createElement = (type, overrides = {}) => {
  const baseProps = { ...(defaultProps[type] || {}) }
  return reactive({
    uid: newUid(),
    type,
    name: overrides.name || (NODE_TYPES[type]?.label || type),
    props: { ...baseProps, ...(overrides.props || {}) },
    children: [],
  })
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

const serializeTree = () => {
  const walk = (node) => ({
    type: node.type,
    name: node.name,
    props: JSON.parse(JSON.stringify(node.props)),
    children: (node.children || []).map(walk),
  })
  return scriptTree.children.map(walk)
}

// ===== 状态 =====
const currentStep = ref(1)
const showGuide = ref(false)

const scriptTree = reactive(createElement('TestPlan', { name: 'TestMaster 性能测试' }))
const selectedUid = ref(null)
const selectedNode = ref(null)

const selectNode = (uid) => {
  selectedUid.value = uid
  selectedNode.value = findNode(scriptTree, uid)
}

const totalSamplers = computed(() => {
  let count = 0
  const walk = (node) => {
    if (node.type === 'HttpSampler') count++
    ;(node.children || []).forEach(walk)
  }
  walk(scriptTree)
  return count
})

// ===== 自然语言描述 =====
const naturalLanguageSummary = computed(() => {
  const tgs = scriptTree.children.filter(c => c.type === 'ThreadGroup')
  if (tgs.length === 0) return '还没有线程组，请添加线程组或导入接口'
  const parts = []
  for (const tg of tgs) {
    const threads = tg.props.threads || 10
    const ramp = tg.props.rampUp || 5
    const loops = tg.props.loops || 1
    const duration = tg.props.duration || 0
    const samplers = []
    const walk = (node) => { if (node.type === 'HttpSampler') samplers.push(node.name); (node.children || []).forEach(walk) }
    walk(tg)
    let desc = `用 ${ramp} 秒逐步启动 ${threads} 个虚拟用户`
    if (duration > 0) {
      desc += `，持续运行 ${duration} 秒`
    } else {
      desc += `，每个用户循环执行 ${loops} 次`
    }
    if (samplers.length > 0) {
      desc += `，共 ${samplers.length} 个请求：${samplers.join('、')}`
    }
    parts.push(desc)
  }
  return parts.join('；')
})

// ===== 节点操作 =====
const addRootElement = () => {
  const tg = createElement('ThreadGroup')
  tg.name = `线程组 ${scriptTree.children.length + 1}`
  const sampler = createElement('HttpSampler')
  sampler.name = 'HTTP 请求 1'
  tg.children.push(sampler)
  const listener = createElement('ViewResultsTree')
  tg.children.push(listener)
  scriptTree.children.push(tg)
  selectedUid.value = tg.uid
  selectedNode.value = tg
  if (currentStep.value === 1) currentStep.value = 2
}

const addChildNode = (parentUid, childType) => {
  const parent = findNode(scriptTree, parentUid)
  if (!parent) return
  const child = createElement(childType)
  parent.children.push(child)
  selectedUid.value = child.uid
  selectedNode.value = child
}

const addChildToCurrent = (type) => {
  if (!selectedNode.value) return
  addChildNode(selectedNode.value.uid, type)
}

const removeNodeByUid = (uid) => {
  if (!uid) return
  const pInfo = findParent(scriptTree, uid)
  if (!pInfo) return
  pInfo.parent.children.splice(pInfo.index, 1)
  if (selectedUid.value === uid || !findNode(scriptTree, selectedUid.value)) {
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

const addVar = () => { if (!scriptTree.props.variables) scriptTree.props.variables = []; scriptTree.props.variables.push({ name: '', value: '' }) }
const addHeader = () => { if (!selectedNode.value?.props?.headers) { if (selectedNode.value) selectedNode.value.props.headers = [] } selectedNode.value?.props?.headers?.push({ key: '', value: '' }) }

// ===== Step 1: 导入接口 =====
const importGroupFilter = ref(null)
const caseSearch = ref('')
const selectedImportCases = ref([])
const allCases = ref([])
const importGroups = ref([])

const openInterfaceLib = () => { window.open('/auto-test?tab=interfaces', '_blank') }

const toggleCase = (id) => {
  const idx = selectedImportCases.value.indexOf(id)
  if (idx >= 0) selectedImportCases.value.splice(idx, 1)
  else selectedImportCases.value.push(id)
}

const filteredImportCases = computed(() => {
  if (!caseSearch.value) return allCases.value
  const kw = caseSearch.value.toLowerCase()
  return allCases.value.filter(c => c.name.toLowerCase().includes(kw) || (c.url||'').toLowerCase().includes(kw))
})

const loadImportGroups = async () => {
  try {
    const res = await autoTestRequest.get('/auto-test/groups')
    importGroups.value = Array.isArray(res) ? res : (res.groups || res.data || [])
  } catch (e) { console.error('加载分组失败:', e) }
}

const loadCases = async () => {
  try {
    const params = {}
    if (importGroupFilter.value) params.group_id = importGroupFilter.value
    const res = await autoTestRequest.get('/auto-test/cases/all', { params })
    allCases.value = (Array.isArray(res) ? res : (res.items || res.data || [])).map(c => ({ id: c.id, name: c.name, method: c.method || 'GET', url: c.url || '' }))
  } catch (e) { console.error('加载接口用例失败:', e) }
}

watch(importGroupFilter, () => { selectedImportCases.value = []; if (currentStep.value === 1) loadCases() })

const importSelectedCases = () => {
  if (selectedImportCases.value.length === 0) return
  let tg = scriptTree.children.find(c => c.type === 'ThreadGroup')
  if (!tg) {
    tg = createElement('ThreadGroup')
    tg.name = '线程组 1'
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
  // 自动添加监听器
  if (!tg.children.find(c => c.type === 'ViewResultsTree')) {
    tg.children.push(createElement('ViewResultsTree'))
  }
  ElMessage.success(`已导入 ${selectedImportCases.value.length} 个接口`)
  selectedImportCases.value = []
  currentStep.value = 2
}

// ===== 模板 =====
const templates = [
  { key: 'simple', name: '简单 API 验证', icon: '🌐', desc: '单接口 GET 请求 + 断言 + 结果树', tags: ['入门'] },
  { key: 'login-flow', name: '登录认证流程', icon: '🔐', desc: '登录 → 提取 Token → 带 Token 请求', tags: ['常用', '认证'] },
  { key: 'crud', name: 'CRUD 全流程', icon: '📦', desc: '增删改查四个请求按顺序执行', tags: ['完整流程'] },
  { key: 'data-driven', name: 'CSV 数据驱动', icon: '📊', desc: 'CSV 参数化多组用户名密码登录', tags: ['参数化'] },
  { key: 'jdbc', name: '数据库压测', icon: '🗄️', desc: 'JDBC 连接 + SQL 查询 + 聚合报告', tags: ['数据库'] },
]

const applyTemplate = (tpl) => {
  scriptTree.children = []
  scriptTree.props.variables = []

  if (tpl.key === 'simple') {
    const tg = createElement('ThreadGroup', { name: '线程组', props: { threads: 10, rampUp: 5, loops: 1, duration: 60 } })
    const req = createElement('HttpSampler', { name: 'API 请求', props: { method: 'GET', url: 'https://httpbin.org/get' } })
    tg.children.push(req, createElement('ViewResultsTree', { name: '查看结果树' }))
    scriptTree.children.push(tg)
  } else if (tpl.key === 'login-flow') {
    const tg = createElement('ThreadGroup', { name: '登录流程', props: { threads: 10, rampUp: 5, loops: 1, duration: 60 } })
    const login = createElement('HttpSampler', { name: '登录请求', props: { method: 'POST', url: 'https://api.example.com/auth/login', body: '{"username":"admin","password":"123456"}', bodyType: 'json', headers: [{ key: 'Content-Type', value: 'application/json' }] } })
    login.children.push(createElement('JsonExtractor', { name: '提取 Token', props: { varName: 'token', jsonPath: '$.data.token', defaultValue: 'NOT_FOUND' } }))
    const api = createElement('HttpSampler', { name: '业务请求', props: { method: 'GET', url: 'https://api.example.com/users/me', headers: [{ key: 'Authorization', value: 'Bearer ${token}' }] } })
    tg.children.push(login, api, createElement('ViewResultsTree'))
    scriptTree.children.push(tg)
  } else if (tpl.key === 'crud') {
    const tg = createElement('ThreadGroup', { name: 'CRUD 测试', props: { threads: 5, rampUp: 2, loops: 1, duration: 60 } })
    tg.children.push(
      createElement('HttpSampler', { name: '1-创建资源', props: { method: 'POST', url: 'https://api.example.com/items', body: '{"name":"test"}', bodyType: 'json' } }),
      createElement('HttpSampler', { name: '2-查询资源', props: { method: 'GET', url: 'https://api.example.com/items/1' } }),
      createElement('HttpSampler', { name: '3-更新资源', props: { method: 'PUT', url: 'https://api.example.com/items/1', body: '{"name":"updated"}', bodyType: 'json' } }),
      createElement('HttpSampler', { name: '4-删除资源', props: { method: 'DELETE', url: 'https://api.example.com/items/1' } }),
      createElement('SummaryReport', { name: '聚合报告' })
    )
    scriptTree.children.push(tg)
  } else if (tpl.key === 'data-driven') {
    const tg = createElement('ThreadGroup', { name: 'CSV 数据驱动', props: { threads: 5, rampUp: 2, loops: 3, duration: 120 } })
    tg.children.push(
      createElement('CSVDataSet', { name: '用户数据', props: { filename: 'users.csv', variableNames: 'username,password', delimiter: ',', recycle: true, csvContent: 'username,password\nuser1,pass1\nuser2,pass2' } }),
      createElement('HttpSampler', { name: '参数化登录', props: { method: 'POST', url: 'https://api.example.com/auth/login', body: '{"username":"${username}","password":"${password}"}', bodyType: 'json', headers: [{ key: 'Content-Type', value: 'application/json' }] } }),
      createElement('ViewResultsTree')
    )
    scriptTree.children.push(tg)
  } else if (tpl.key === 'jdbc') {
    const tg = createElement('ThreadGroup', { name: '数据库压测', props: { threads: 10, rampUp: 3, loops: 5, duration: 60 } })
    tg.children.push(
      createElement('JDBCConnection', { name: 'MySQL 连接', props: { dbUrl: 'jdbc:mysql://localhost:3306/testdb', driver: 'com.mysql.cj.jdbc.Driver', dbUser: 'root', dbPass: 'password' } }),
      createElement('JDBCSampler', { name: '查询语句', props: { sql: 'SELECT * FROM users WHERE status = "active"' } }),
      createElement('SummaryReport', { name: '聚合报告' })
    )
    scriptTree.children.push(tg)
  }

  selectedUid.value = null
  selectedNode.value = null
  currentStep.value = 2
  ElMessage.success(`已加载「${tpl.name}」模板`)
}

// ===== 导入 .jmx 文件 =====
const showImportJmxDialog = ref(false)
const jmxImportFile = ref(null)
const jmxImporting = ref(false)

const handleJmxFileChange = (file) => { jmxImportFile.value = file.raw; return false }

const confirmImportJmx = async () => {
  if (!jmxImportFile.value) return
  jmxImporting.value = true
  try {
    const form = new FormData()
    form.append('file', jmxImportFile.value)
    const res = await autoTestRequest.post('/auto-test/import/jmeter', form, { headers: { 'Content-Type': 'multipart/form-data' } })
    const cases = res.cases || []
    if (cases.length === 0) { ElMessage.warning('未解析出接口'); return }
    let tg = scriptTree.children.find(c => c.type === 'ThreadGroup')
    if (!tg) { tg = createElement('ThreadGroup'); scriptTree.children.push(tg) }
    for (const c of cases) {
      const sampler = createElement('HttpSampler')
      sampler.name = c.name
      sampler.props.method = c.method
      sampler.props.url = c.url
      tg.children.push(sampler)
    }
    ElMessage.success(`成功导入 ${cases.length} 个接口`)
    showImportJmxDialog.value = false
    currentStep.value = 2
  } catch (e) { ElMessage.error('导入失败: ' + (e.response?.data?.detail || e.message)) }
  finally { jmxImporting.value = false; jmxImportFile.value = null }
}

// ===== JMX 生成 + 下载 =====
const jmxContent = ref('')
const generating = ref(false)

const rightTab3 = ref('debug')

const generatePreview = async () => {
  if (scriptTree.children.length === 0) { ElMessage.warning('请先添加接口'); return }
  generating.value = true
  try {
    const res = await autoTestRequest.post('/auto-test/export/jmeter/tree', {
      tree: serializeTree(),
      plan_name: scriptTree.name,
      plan_variables: scriptTree.props.variables || [],
    })
    jmxContent.value = res.jmx_content || ''
    if (currentStep.value === 2) currentStep.value = 3
    ElMessage.success('JMX 已生成')
  } catch (e) { ElMessage.error('生成失败: ' + (e.response?.data?.detail || e.message)) }
  finally { generating.value = false }
}

const downloadJmx = () => {
  if (!jmxContent.value) return
  const blob = new Blob([jmxContent.value], { type: 'application/octet-stream' })
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  const ts = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19)
  a.download = `${scriptTree.name || 'testplan'}_${ts}.jmx`
  a.click()
  ElMessage.success('✅ 下载成功！用 JMeter 打开即可运行')
}

// ===== 快速并发压测验证 =====
const benchConcurrency = ref(10)
const benchDuration = ref(10)
const benchRampUp = ref(2)
const benchResult = ref(null)
const benchProgress = ref('')
const benchPercent = ref(0)
const benchTaskId = ref(null)
const benching = ref(false)
let benchPollTimer = null

const startBench = async () => {
  const samplers = []
  const walk = (node) => {
    if (node.type === 'HttpSampler') {
      const headers = {}
      ;(node.props.headers || []).forEach(h => { if (h.key) headers[h.key] = h.value })
      samplers.push({
        method: node.props.method || 'GET',
        url: node.props.url,
        headers,
        body: node.props.method !== 'GET' ? (node.props.body || '') : '',
      })
    }
    ;(node.children || []).forEach(walk)
  }
  walk(scriptTree)
  
  if (samplers.length === 0) { ElMessage.warning('脚本中没有 HTTP 请求'); return }
  
  // 清理旧轮询
  if (benchPollTimer) { clearInterval(benchPollTimer); benchPollTimer = null }
  
  benching.value = true
  benchResult.value = null
  benchProgress.value = '提交任务...'
  benchPercent.value = 0
  benchTaskId.value = null
  rightTab3.value = 'bench'
  
  try {
    const res = await autoTestRequest.post('/auto-test/jmeter/quick-bench', {
      requests: samplers,
      concurrency: benchConcurrency.value,
      duration: benchDuration.value,
      ramp_up: benchRampUp.value,
    })
    benchTaskId.value = res.task_id
    benchProgress.value = '任务已提交，正在执行...'
    
    // 开始轮询
    benchPollTimer = setInterval(pollBench, 1500)
  } catch (e) {
    ElMessage.error('提交失败: ' + (e.response?.data?.detail || e.message))
    benching.value = false
  }
}

const pollBench = async () => {
  if (!benchTaskId.value) return
  try {
    const res = await autoTestRequest.get(`/auto-test/jmeter/quick-bench/${benchTaskId.value}`)
    benchProgress.value = res.progress || ''
    benchPercent.value = res.percent || 0
    
    if (res.status === 'done') {
      if (benchPollTimer) { clearInterval(benchPollTimer); benchPollTimer = null }
      benchResult.value = res.result
      benching.value = false
      if (res.result.failed > 0) {
        ElMessage.warning(`并发测试完成：${res.result.total} 请求，${res.result.failed} 失败`)
      } else {
        ElMessage.success(`并发测试通过！${res.result.total} 请求全部成功，TPS ${res.result.tps}`)
      }
    }
  } catch (e) {
    if (benchPollTimer) { clearInterval(benchPollTimer); benchPollTimer = null }
    benching.value = false
    ElMessage.error('查询失败: ' + (e.response?.data?.detail || e.message))
  }
}

const stopBench = () => {
  if (benchPollTimer) { clearInterval(benchPollTimer); benchPollTimer = null }
  benching.value = false
  ElMessage.info('已停止轮询')
}

// ===== 调试 =====
const debugResult = ref(null)
const debugLoading = ref(false)

const debugRequest = async (node) => {
  if (!node || node.type !== 'HttpSampler') return
  debugLoading.value = true
  try {
    const headers = {}
    ;(node.props.headers || []).forEach(h => { if (h.key) headers[h.key] = h.value })
    let url = node.props.url, body = node.props.body || ''
    ;(scriptTree.props.variables || []).forEach(v => {
      url = url.replace('${' + v.name + '}', v.value)
      body = body.replace('${' + v.name + '}', v.value)
    })
    const res = await autoTestRequest.post('/auto-test/debug/execute', {
      method: node.props.method || 'GET', url, headers,
      body: node.props.method !== 'GET' ? body : '', timeout: 30,
    })
    debugResult.value = res
    if (currentStep.value === 2) currentStep.value = 3
    ElMessage.success(`调试完成: ${res.response?.status_code || 'ERR'} | ${res.response?.elapsed_ms || 0}ms`)
  } catch (e) { ElMessage.error('调试失败: ' + (e.message || '未知错误')) }
  finally { debugLoading.value = false }
}

const formatHeaders = (h) => h ? JSON.stringify(h, null, 2) : ''
const formatBody = (b) => {
  if (!b) return ''
  if (typeof b === 'object') return JSON.stringify(b, null, 2)
  try { return JSON.stringify(JSON.parse(b), null, 2) } catch { return String(b) }
}

// ===== 保存到接口库 =====
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
  if (caseGroups.value.length > 0 && !saveGroupId.value) saveGroupId.value = caseGroups.value[0].id
  showSaveToCase.value = true
}

const confirmSaveToCase = async () => {
  if (!saveCaseName.value) { ElMessage.warning('请输入用例名称'); return }
  if (!saveGroupId.value) { ElMessage.warning('请先选择一个分组'); return }
  savingToCase.value = true
  try {
    await autoTestRequest.post('/auto-test/cases', {
      group_id: saveGroupId.value, name: saveCaseName.value,
      method: saveCaseMethod.value, url: saveCaseUrl.value,
      headers: selectedNode.value?.props?.headers?.reduce((acc, h) => { if (h.key) acc[h.key] = h.value; return acc }, {}) || {},
      body_type: 'json',
      payload: (() => { try { return JSON.parse(selectedNode.value?.props?.body || '{}') } catch { return {} } })()
    })
    ElMessage.success('已保存到接口库')
    showSaveToCase.value = false
  } catch (e) { ElMessage.error('保存失败: ' + (e.response?.data?.detail || e.message)) }
  finally { savingToCase.value = false }
}

// ===== 初始化 =====
onMounted(() => {
  loadImportGroups()
  loadCases()
  loadCaseGroups()
  if (scriptTree.children.length === 0) {
    const tg = createElement('ThreadGroup')
    tg.name = '线程组 1'
    const sampler = createElement('HttpSampler', { name: '示例请求', props: { method: 'GET', url: 'https://httpbin.org/get' } })
    tg.children.push(sampler, createElement('ViewResultsTree'))
    scriptTree.children.push(tg)
  }
})
</script>

<style scoped>
/* ===== 全局布局 ===== */
.jmeter-workspace {
  display: flex; flex-direction: column; height: 100%;
  background: var(--tm-bg); color: var(--tm-text-primary);
}

/* ===== 步骤导航 ===== */
.step-nav {
  display: flex; align-items: center; gap: 8px;
  padding: 12px 16px; background: var(--tm-card-bg);
  border-bottom: 1px solid var(--tm-border);
}
.step { display: flex; align-items: center; gap: 6px; cursor: pointer; padding: 6px 12px; border-radius: 6px; font-size: 13px; color: var(--tm-text-secondary); border: 1px solid transparent; }
.step.active { color: var(--tm-color-primary); border-color: var(--tm-color-primary); background: rgba(64,158,255,0.06); }
.step.done { color: #4ADE80; }
.step-num { width: 22px; height: 22px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 700; background: var(--tm-bg-secondary); color: var(--tm-text-secondary); }
.step.active .step-num { background: var(--tm-color-primary); color: #fff; }
.step.done .step-num { background: #4ADE80; color: #fff; }
.step-arrow { color: var(--tm-text-secondary); font-weight: 700; }
.step-actions { margin-left: auto; display: flex; gap: 6px; }

/* ===== 引导面板 ===== */
.guide-panel { padding: 8px 16px; }

/* ===== Step 1 布局 ===== */
.step1-layout { display: grid; grid-template-columns: 320px 1fr; gap: 16px; padding: 16px; height: 100%; }
.step1-templates { overflow-y: auto; }
.step1-import { display: flex; flex-direction: column; overflow: hidden; }

.template-grid { display: grid; gap: 8px; }
.tpl-card { padding: 12px; border: 1px solid var(--tm-border); border-radius: 8px; cursor: pointer; transition: all .2s; }
.tpl-card:hover { border-color: var(--tm-color-primary); background: rgba(64,158,255,0.04); transform: translateY(-1px); }
.tpl-icon { font-size: 24px; }
.tpl-name { font-weight: 600; font-size: 13px; margin: 4px 0 2px; }
.tpl-desc { font-size: 11px; color: var(--tm-text-secondary); }

.import-controls { display: flex; gap: 8px; margin-bottom: 12px; }
.import-case-list { flex: 1; overflow-y: auto; }
.import-case-item { padding: 4px 0; }
.import-case-item:hover { background: rgba(255,255,255,0.03); border-radius: 4px; }
.case-method { font-size: 11px; font-weight: 700; padding: 1px 5px; border-radius: 3px; margin-right: 6px; }
.m-get { background: rgba(74,222,128,0.15); color: #4ADE80; }
.m-post { background: rgba(236,72,153,0.15); color: #EC4899; }
.m-put { background: rgba(250,204,21,0.15); color: #FACC15; }
.m-delete { background: rgba(248,113,113,0.15); color: #F87171; }
.m-patch { background: rgba(129,140,248,0.15); color: #818CF8; }
.case-name { font-size: 13px; }
.case-url { font-size: 11px; color: var(--tm-text-secondary); margin-left: 8px; }

.import-footer { display: flex; justify-content: space-between; align-items: center; padding: 12px 0 0; border-top: 1px solid var(--tm-border); margin-top: 8px; }
.import-count { font-size: 12px; color: var(--tm-text-secondary); }

/* ===== Step 2 布局 ===== */
.step2-layout { display: grid; grid-template-columns: 280px 1fr; gap: 16px; padding: 16px; height: 100%; overflow: hidden; }
.tree-panel { display: flex; flex-direction: column; overflow: hidden; }
.tree-body { flex: 1; overflow-y: auto; padding: 4px; }
.tree-root-label { display: flex; align-items: center; gap: 6px; padding: 8px; border-radius: 6px; font-weight: 600; font-size: 13px; cursor: pointer; }
.tree-root-label:hover { background: rgba(255,255,255,0.04); }
.root-icon { font-size: 16px; }
.tree-empty { padding: 20px; text-align: center; font-size: 12px; color: var(--tm-text-secondary); }

.editor-panel { display: flex; flex-direction: column; overflow: hidden; }
.editor-body { flex: 1; overflow-y: auto; padding: 12px; }
.editor-empty { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 200px; color: var(--tm-text-secondary); gap: 8px; }
.summary-bar { padding: 8px 12px; border-top: 1px solid var(--tm-border); font-size: 12px; color: var(--tm-text-secondary); display: flex; align-items: flex-start; gap: 6px; background: rgba(64,158,255,0.03); }
.summary-icon { flex-shrink: 0; }
.summary-text { line-height: 1.5; }

/* ===== 编辑器表单 ===== */
.form-section { padding: 8px 0; }
.section-hint { font-size: 11px; color: var(--tm-text-secondary); margin-bottom: 8px; }
.form-group { margin-bottom: 10px; }
.form-group label { display: block; font-size: 12px; font-weight: 600; margin-bottom: 3px; color: var(--tm-text-secondary); }
.form-row { display: flex; gap: 8px; }
.form-row .form-group { flex: 1; }
.kv-row { display: flex; gap: 4px; align-items: center; margin-bottom: 4px; }
.form-hint { font-size: 11px; color: #6b7280; margin-bottom: 8px; }
.form-hint code { background: rgba(255,255,255,0.06); padding: 1px 4px; border-radius: 3px; font-family: monospace; }

/* ===== Step 3 布局 ===== */
.step3-layout { display: grid; grid-template-columns: 1fr 380px; gap: 16px; padding: 16px; height: 100%; overflow: hidden; }
.export-preview { display: flex; flex-direction: column; overflow: hidden; }
.preview-body { flex: 1; overflow-y: auto; background: #0d1117; padding: 12px; }
.xml-preview { margin: 0; white-space: pre-wrap; font-size: 11px; font-family: 'Consolas', monospace; color: #c9d1d9; }
.export-debug { display: flex; flex-direction: column; overflow: hidden; }
.debug-body { flex: 1; overflow-y: auto; padding: 8px; }
.debug-content { }
.debug-meta { display: flex; gap: 12px; align-items: center; margin-bottom: 8px; padding: 8px; background: rgba(255,255,255,0.03); border-radius: 6px; }
.debug-elapsed { font-size: 13px; font-weight: 600; color: #4ADE80; }
.debug-size { font-size: 12px; color: var(--tm-text-secondary); }
.debug-json { background: #0d1117; padding: 8px; border-radius: 4px; font-size: 11px; color: #c9d1d9; font-family: 'Consolas', monospace; max-height: 200px; overflow: auto; margin: 0; }
.debug-error { margin-top: 8px; }
.empty-hint { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 200px; color: var(--tm-text-secondary); gap: 8px; font-size: 13px; text-align: center; }

/* ===== 并发压测 ===== */
.bench-body { padding: 8px; overflow-y: auto; flex: 1; }
.bench-controls { display: flex; gap: 8px; margin-bottom: 8px; }
.bench-controls .form-group { flex: 1; }
.bench-controls .form-group label { display: block; font-size: 11px; color: var(--tm-text-secondary); margin-bottom: 2px; }
.bench-controls .el-input-number { width: 100%; }
.bench-result { margin-top: 4px; }
.bench-progress { margin-bottom: 8px; text-align: center; }
.bench-progress-text { font-size: 11px; color: var(--tm-text-secondary); margin-top: 4px; display: inline-block; }
.bench-stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 6px; }
.bench-stat { background: rgba(255,255,255,0.03); border-radius: 6px; padding: 8px 4px; text-align: center; }
.bench-stat-value { display: block; font-size: 16px; font-weight: 700; }
.bench-stat-label { display: block; font-size: 10px; color: var(--tm-text-secondary); margin-top: 1px; }
.text-success { color: #4ADE80; }
.text-danger { color: #F87171; }
.right-tabs .el-tabs__content { overflow: visible; }
.right-tabs .el-tab-pane { height: 100%; display: flex; flex-direction: column; }
.right-tabs .el-tabs__header { margin-bottom: 4px; }

/* ===== 面板通用 ===== */
.panel { display: flex; flex-direction: column; background: var(--tm-card-bg); border: 1px solid var(--tm-border); border-radius: 10px; overflow: hidden; }
.panel-title { display: flex; justify-content: space-between; align-items: center; padding: 10px 12px; border-bottom: 1px solid var(--tm-border); font-weight: 600; font-size: 13px; }
.empty-state { text-align: center; padding: 30px; color: var(--tm-text-secondary); font-size: 13px; }

.step-body { flex: 1; overflow: hidden; }
</style>
