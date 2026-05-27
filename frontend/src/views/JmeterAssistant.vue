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
        <!-- 左侧：模板 + 导入JMX -->
        <div class="step1-left">
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
          <div class="step1-import-jmx">
            <div class="import-jmx-card" @click="showImportJmxDialog = true">
              <div class="import-jmx-icon">📂</div>
              <div class="import-jmx-body">
                <div class="import-jmx-title">导入 .jmx 文件</div>
                <div class="import-jmx-desc">已有 JMeter 脚本？直接导入 .jmx 文件解析为接口</div>
              </div>
              <el-icon size="20" style="color:var(--tm-text-secondary)"><Right /></el-icon>
            </div>
          </div>
        </div>
        <!-- 右侧：从接口库导入 -->
        <div class="panel step1-import">
          <div class="panel-title">📋 从接口库导入</div>
          <div class="section-hint"><el-icon><InfoFilled /></el-icon> 勾选已有的 API 接口，点击「导入到脚本」自动创建 HTTP 请求和线程组</div>
          <div class="import-controls">
            <el-select v-model="importGroupFilter" placeholder="按分组筛选" size="default" clearable filterable style="width:240px">
              <el-option v-for="g in importGroups" :key="g.id" :label="g.name" :value="g.id" />
            </el-select>
            <el-input v-model="caseSearch" placeholder="搜索接口名称或URL..." size="default" clearable prefix-icon="Search" style="flex:1" />
          </div>
          <div class="import-case-list">
            <div v-if="allCases.length === 0" class="empty-state">
              <el-icon size="32"><FolderDelete /></el-icon>
              <p style="margin:8px 0">当前分组没有接口用例</p>
              <el-button type="primary" size="small" @click="openInterfaceLib">📝 去接口库创建</el-button>
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
            <el-button type="primary" size="large" :disabled="selectedImportCases.length === 0" @click="importSelectedCases" style="font-weight:700">
              🚀 导入到脚本 <el-icon><Right /></el-icon>
            </el-button>
          </div>
        </div>
      </div>
    </div>

    <!-- ==================== Step 2: 配置压测参数 ==================== -->
    <div v-show="currentStep === 2" class="step-body">

      <!-- ⭐ 自然语言概要提示 - 顶部大 banner -->
      <div class="summary-banner" v-if="scriptTree.children.length > 0">
        <div class="summary-banner-icon">{{ summaryEmoji }}</div>
        <div class="summary-banner-body">
          <div class="summary-banner-title">{{ summaryTitle }}</div>
          <div class="summary-banner-text">{{ naturalLanguageSummary }}</div>
          <div class="summary-banner-stats">
            <el-tag size="small" effect="plain">👥 {{ totalThreads }} 线程</el-tag>
            <el-tag size="small" effect="plain">🌐 {{ totalSamplers }} 请求</el-tag>
            <el-tag v-if="totalAssertions > 0" size="small" effect="plain">✅ {{ totalAssertions }} 断言</el-tag>
            <el-tag v-if="totalExtractors > 0" size="small" effect="plain">🔍 {{ totalExtractors }} 提取器</el-tag>
            <el-tag v-if="totalTimers > 0" size="small" effect="plain">⏰ {{ totalTimers }} 定时器</el-tag>
            <el-tag v-if="totalListeners > 0" size="small" effect="plain">👁️ {{ totalListeners }} 监听器</el-tag>
          </div>
        </div>
      </div>
      <div class="summary-banner summary-banner-empty" v-else>
        <div class="summary-banner-icon">💡</div>
        <div class="summary-banner-body">
          <div class="summary-banner-text">当前脚本是空的，去「选择接口」步骤导入接口，或点击左侧「+ 添加线程组」从零开始创建</div>
        </div>
      </div>

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
                <div class="section-hint"><el-icon><InfoFilled /></el-icon> 虚拟用户数 = 模拟多少人同时访问；Ramp-Up = 多少秒内逐步启动完；持续时间 = 总共跑多久</div>
                <div class="form-group"><label>线程组名称</label><el-input v-model="selectedNode.name" size="small" /></div>
                <div class="form-row">
                  <div class="form-group"><label>并发线程数</label><el-tooltip content="模拟多少个用户同时访问系统，50 = 50个虚拟用户" placement="top"><el-input-number v-model="selectedNode.props.threads" :min="1" :max="10000" size="small" /></el-tooltip></div>
                  <div class="form-group"><label>Ramp-Up (秒)</label><el-tooltip content="多少秒内逐步启动完所有用户。5秒=5秒内逐步启动50个用户" placement="top"><el-input-number v-model="selectedNode.props.rampUp" :min="0" :max="3600" size="small" /></el-tooltip></div>
                </div>
                <div class="form-row">
                  <div class="form-group"><label>循环次数</label><el-tooltip content="每个用户跑完一遍后重复跑的次数。1=每人只跑1遍" placement="top"><el-input-number v-model="selectedNode.props.loops" :min="1" :max="99999" size="small" /></el-tooltip></div>
                  <div class="form-group"><label>持续时间 (秒)</label><el-tooltip content="设置后循环次数不生效，到时间自动停止。60=跑60秒" placement="top"><el-input-number v-model="selectedNode.props.duration" :min="0" :max="86400" size="small" /></el-tooltip></div>
                </div>
                <el-alert v-if="selectedNode.props.loops >= 99999 && !selectedNode.props.duration"
                  title="⚠️ 此脚本将永久循环运行！请设置持续时间" type="error" :closable="false" show-icon />
              </div>
              <div class="form-section">
                <div class="section-hint"><el-icon><Monitor /></el-icon> 监听器用于查看测试结果，建议添加「查看结果树」和「聚合报告」</div>
                <div style="display:flex;gap:6px;flex-wrap:wrap">
                  <el-button size="small" @click="addChildToCurrent('HttpSampler')">🌐 HTTP 请求</el-button>
                  <el-button size="small" @click="addChildToCurrent('ViewResultsTree')">👁️ 查看结果树</el-button>
                  <el-button size="small" @click="addChildToCurrent('SummaryReport')">📈 聚合报告</el-button>
                  <el-button size="small" @click="addChildToCurrent('AggregateReport')">📊 聚合报告(高级)</el-button>
                  <el-button size="small" @click="addChildToCurrent('ResponseTimeGraph')">📉 响应时间图</el-button>
                  <el-button size="small" @click="addChildToCurrent('CSVDataSet')">📄 CSV 数据源</el-button>
                  <el-button size="small" @click="addChildToCurrent('JDBCSampler')">🗄️ JDBC 请求</el-button>
                </div>
              </div>
              <div class="form-section">
                <div class="section-hint"><el-icon><Lollipop /></el-icon> 逻辑控制器：控制请求的执行顺序和条件</div>
                <div style="display:flex;gap:6px;flex-wrap:wrap">
                  <el-button size="small" @click="addChildToCurrent('IfController')">🔀 如果控制器</el-button>
                  <el-button size="small" @click="addChildToCurrent('LoopController')">🔄 循环控制器</el-button>
                  <el-button size="small" @click="addChildToCurrent('WhileController')">🔁 While 控制器</el-button>
                  <el-button size="small" @click="addChildToCurrent('TransactionController')">📦 事务控制器</el-button>
                  <el-button size="small" @click="addChildToCurrent('ThroughputController')">⏱️ 吞吐量控制器</el-button>
                  <el-button size="small" @click="addChildToCurrent('OnceOnlyController')">1️⃣ 仅一次控制器</el-button>
                </div>
              </div>
              <div class="form-section">
                <div class="section-hint"><el-icon><Setting /></el-icon> 配置元件：全局设置 HTTP 默认值、请求头、Cookie 等</div>
                <div style="display:flex;gap:6px;flex-wrap:wrap">
                  <el-button size="small" @click="addChildToCurrent('HTTPRequestDefaults')">🎯 HTTP 请求默认值</el-button>
                  <el-button size="small" @click="addChildToCurrent('HTTPHeaderManager')">📨 HTTP 信息头管理器</el-button>
                  <el-button size="small" @click="addChildToCurrent('HTTPCookieManager')">🍪 HTTP Cookie 管理器</el-button>
                </div>
              </div>
            </template>

            <!-- HTTP 请求 -->
            <template v-if="selectedNode.type === 'HttpSampler'">
              <div class="form-section">
                <div class="section-hint"><el-icon><Connection /></el-icon> 配置要压测的接口：选择方法、填写地址、添加请求头和请求体</div>
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
                    <div class="section-hint" style="margin-bottom:6px">添加请求头，如 Content-Type: application/json、Authorization: Bearer xxx</div>
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
                <div class="section-hint"><el-icon><Coin /></el-icon> 断言：验证返回结果是否正确（点击展开更多类型）</div>
                <div style="display:flex;gap:4px;flex-wrap:wrap">
                  <el-button size="small" @click="addChildToCurrent('ResponseAssertion')">✅ 响应断言</el-button>
                  <el-button size="small" @click="addChildToCurrent('JsonAssertion')">📋 JSON断言</el-button>
                  <el-button size="small" @click="addChildToCurrent('DurationAssertion')">⏱️ 持续时间</el-button>
                  <el-button size="small" @click="addChildToCurrent('BeanShellAssertion')">💻 BeanShell</el-button>
                  <el-button size="small" @click="addChildToCurrent('JSR223Assertion')">🔥 JSR223</el-button>
                  <el-button size="small" @click="addChildToCurrent('SizeAssertion')">📏 大小</el-button>
                  <el-button size="small" @click="addChildToCurrent('XPathAssertion')">🗂️ XPath</el-button>
                  <el-button size="small" @click="addChildToCurrent('CompareAssertion')">⚖️ 比较</el-button>
                  <el-button size="small" @click="addChildToCurrent('XMLAssertion')">📜 XML</el-button>
                </div>
              </div>
              <div class="form-section">
                <div class="section-hint"><el-icon><Coin /></el-icon> 提取器：从响应中提取数据传给下一个请求</div>
                <div style="display:flex;gap:6px;flex-wrap:wrap">
                  <el-button size="small" @click="addChildToCurrent('JsonExtractor')">📤 JSON 提取器</el-button>
                  <el-button size="small" @click="addChildToCurrent('RegexExtractor')">🔍 正则提取器</el-button>
                </div>
              </div>
              <div class="form-section">
                <div class="section-hint"><el-icon><Coin /></el-icon> 定时器与处理器</div>
                <div style="display:flex;gap:6px;flex-wrap:wrap">
                  <el-button size="small" @click="addChildToCurrent('ConstantTimer')">⏰ 固定定时器</el-button>
                  <el-button size="small" @click="addChildToCurrent('UniformRandomTimer')">🎲 随机定时器</el-button>
                  <el-button size="small" @click="addChildToCurrent('BeanShellPreProcessor')">⚙️ BeanShell前置</el-button>
                  <el-button size="small" @click="addChildToCurrent('JSR223PreProcessor')">🔥 JSR223前置</el-button>
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

            <!-- ===== 断言编辑器（支持7种断言类型+AI辅助） ===== -->
            <template v-if="selectedNode.type === 'ResponseAssertion'">
              <div class="form-section">
                <div class="form-group"><label>断言名称</label><el-input v-model="selectedNode.name" size="small" /></div>
                <div class="form-group"><label>断言类型</label>
                  <el-select v-model="selectedNode.props.assertType" size="small">
                    <el-option label="状态码" value="status_code" />
                    <el-option label="响应包含" value="contains" />
                    <el-option label="响应匹配(正则)" value="matches" />
                    <el-option label="JSON Path" value="jsonpath" />
                    <el-option label="持续时间" value="duration" />
                  </el-select>
                </div>
                <div class="form-group" v-if="selectedNode.props.assertType === 'status_code'"><label>期望状态码</label><el-input-number v-model="selectedNode.props.expected" :min="100" :max="599" size="small" /></div>
                <div class="form-group" v-if="selectedNode.props.assertType === 'contains' || selectedNode.props.assertType === 'matches'"><label>期望值</label><el-input v-model="selectedNode.props.expected" size="small" placeholder="200或success" /></div>
                <div class="form-group" v-if="selectedNode.props.assertType === 'jsonpath'"><label>JSON Path</label><el-input v-model="selectedNode.props.jsonPath" placeholder="$.data.token" size="small" /><label style="margin-top:4px">期望值</label><el-input v-model="selectedNode.props.expected" size="small" /></div>
                <div class="form-group" v-if="selectedNode.props.assertType === 'duration'"><label>最大响应时间 (ms)</label><el-input-number v-model="selectedNode.props.maxDuration" :min="1" :max="60000" size="small" /></div>
              </div>
              <div class="form-section">
                <div class="section-hint"><el-icon><InfoFilled /></el-icon> 💡 小白提示：状态码断言最常用，只需填期望的状态码如200。响应包含用于检查返回内容中是否有特定文字</div>
              </div>
            </template>

            <template v-if="selectedNode.type === 'JsonAssertion'">
              <div class="form-section">
                <div class="form-group"><label>断言名称</label><el-input v-model="selectedNode.name" size="small" /></div>
                <div class="form-group"><label>JSON Path</label><el-input v-model="selectedNode.props.jsonPath" placeholder="$.data.token" size="small" /></div>
                <div class="form-group"><label>期望值</label><el-input v-model="selectedNode.props.expected" placeholder="12345" size="small" /></div>
                <div class="form-row">
                  <div class="form-group"><label>期望为null</label><el-switch v-model="selectedNode.props.expectNull" size="small" /></div>
                  <div class="form-group"><label>取反</label><el-switch v-model="selectedNode.props.invert" size="small" /></div>
                </div>
              </div>
              <div class="form-section">
                <div class="section-hint"><el-icon><InfoFilled /></el-icon> 💡 小白提示：用于断言JSON响应中的某个字段值。例：$.data.status 期望值 "ok"</div>
                <el-button size="small" @click="aiGenerateAssert('Json')" :loading="aiGenerating" style="margin-top:4px">
                  🤖 AI 帮写
                </el-button>
              </div>
            </template>

            <template v-if="selectedNode.type === 'DurationAssertion'">
              <div class="form-section">
                <div class="form-group"><label>断言名称</label><el-input v-model="selectedNode.name" size="small" /></div>
                <div class="form-group"><label>最大响应时间 (ms)</label><el-input-number v-model="selectedNode.props.maxDuration" :min="1" :max="60000" size="small" /></div>
              </div>
              <div class="section-hint"><el-icon><InfoFilled /></el-icon> 💡 小白提示：如果接口响应太慢就报错。如设置1000ms=超过1秒就失败</div>
            </template>

            <!-- ===== BeanShell 断言（核心！） ===== -->
            <template v-if="selectedNode.type === 'BeanShellAssertion'">
              <div class="form-section">
                <div class="form-group"><label>断言名称</label><el-input v-model="selectedNode.name" size="small" /></div>
              </div>
              <div class="section-hint assertion-teaching">
                <div class="teaching-title">📖 BeanShell 断言教学 — 小白也能写</div>
                <div class="teaching-body">
                  <p><strong>什么是 BeanShell 断言？</strong> 用 Java 代码自定义判断规则，只要你会写 if/else 就能用</p>
                  <p><strong>📌 核心变量速查：</strong></p>
                  <table class="teaching-table">
                    <tr><td><code>ResponseCode</code></td><td>HTTP 状态码（字符串），如 "200"</td></tr>
                    <tr><td><code>ResponseMessage</code></td><td>HTTP 消息，如 "OK"</td></tr>
                    <tr><td><code>ResponseData</code></td><td>响应体（字节数组），转字符串用 <code>new String(ResponseData)</code></td></tr>
                    <tr><td><code>SampleResult</code></td><td>采样结果对象</td></tr>
                    <tr><td><code>Failure</code></td><td>设为 <code>true</code> 表示断言失败</td></tr>
                    <tr><td><code>FailureMessage</code></td><td>失败时的错误描述</td></tr>
                    <tr><td><code>prev</code></td><td>等同于 SampleResult（类型: SampleResult）</td></tr>
                  </table>
                  <p><strong>📌 常用示例：</strong></p>
                  <table class="teaching-table">
                    <tr><td>状态码断言</td><td><code>if (!ResponseCode.equals("200")) { Failure=true; FailureMessage="状态码不是200"; }</code></td></tr>
                    <tr><td>响应包含</td><td><code>if (!new String(ResponseData).contains("success")) { Failure=true; FailureMessage="响应无success"; }</code></td></tr>
                    <tr><td>响应时间</td><td><code>if (prev.getTime() > 3000) { Failure=true; FailureMessage="超过3秒"; }</code></td></tr>
                    <tr><td>JSON断言</td><td><code>import org.json.*; JSONObject j=new JSONObject(new String(ResponseData)); if (!j.has("token")) { Failure=true; FailureMessage="缺少token"; }</code></td></tr>
                  </table>
                </div>
              </div>
              <div class="form-section">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px">
                  <label>BeanShell 脚本</label>
                  <el-button size="small" type="primary" @click="aiGenerateAssert('BeanShell')" :loading="aiGenerating" plain>
                    🤖 AI 帮写断言
                  </el-button>
                </div>
                <el-input v-model="selectedNode.props.script" type="textarea" :rows="8" placeholder="// 写你的断言逻辑..." size="small" style="font-family:Consolas,monospace;font-size:12px" />
              </div>
              <div class="form-row">
                <div class="form-group"><label>外部BeanShell文件</label><el-input v-model="selectedNode.props.filename" placeholder="可选" size="small" /></div>
                <div class="form-group"><label>参数</label><el-input v-model="selectedNode.props.parameters" placeholder="可选" size="small" /></div>
              </div>
              <div class="form-group"><label>每次重置解释器</label><el-switch v-model="selectedNode.props.resetInterpreter" size="small" /></div>
            </template>

            <!-- ===== JSR223 断言 ===== -->
            <template v-if="selectedNode.type === 'JSR223Assertion'">
              <div class="form-section">
                <div class="form-group"><label>断言名称</label><el-input v-model="selectedNode.name" size="small" /></div>
                <div class="form-group"><label>脚本语言</label>
                  <el-select v-model="selectedNode.props.language" size="small">
                    <el-option label="Groovy（推荐，性能最好）" value="groovy" />
                    <el-option label="JavaScript" value="javascript" />
                    <el-option label="Python (Jython)" value="python" />
                    <el-option label="BeanShell" value="beanshell" />
                  </el-select>
                </div>
              </div>
              <div class="section-hint assertion-teaching">
                <div class="teaching-title">📖 JSR223 断言教学</div>
                <div class="teaching-body">
                  <p><strong>推荐用 Groovy</strong>，比 BeanShell 快 10 倍。核心变量：</p>
                  <table class="teaching-table">
                    <tr><td><code>prev</code></td><td>SampleResult，可调用 getResponseDataAsString()、getTime()等</td></tr>
                    <tr><td><code>log</code></td><td>日志对象，log.info("xxx") 打印日志</td></tr>
                    <tr><td><code>AssertionResult</code></td><td>断言结果，.setFailure(true) 标记失败</td></tr>
                  </table>
                </div>
              </div>
              <div class="form-section">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px">
                  <label>脚本代码</label>
                  <el-button size="small" type="primary" @click="aiGenerateAssert('JSR223')" :loading="aiGenerating" plain>
                    🤖 AI 帮写断言
                  </el-button>
                </div>
                <el-input v-model="selectedNode.props.script" type="textarea" :rows="8" placeholder='// Groovy脚本...' size="small" style="font-family:Consolas,monospace;font-size:12px" />
              </div>
            </template>

            <!-- ===== 响应大小断言 ===== -->
            <template v-if="selectedNode.type === 'SizeAssertion'">
              <div class="form-section">
                <div class="form-group"><label>断言名称</label><el-input v-model="selectedNode.name" size="small" /></div>
                <div class="form-row">
                  <div class="form-group">
                    <label>比较方式</label>
                    <el-select v-model="selectedNode.props.operator" size="small">
                      <el-option label="响应大小 &gt; 指定值" value=">" />
                      <el-option label="响应大小 &lt; 指定值" value="<" />
                      <el-option label="响应大小 = 指定值" value="=" />
                      <el-option label="响应大小 ≠ 指定值" value="≠" />
                    </el-select>
                  </div>
                  <div class="form-group"><label>大小 (字节)</label><el-input-number v-model="selectedNode.props.size" :min="1" :max="99999999" size="small" /></div>
                </div>
              </div>
              <div class="section-hint"><el-icon><InfoFilled /></el-icon> 💡 小白提示：检查响应体大小。如 &gt; 5000 字节 → 确保接口返回了足够的数据</div>
            </template>

            <!-- ===== XPath 断言 ===== -->
            <template v-if="selectedNode.type === 'XPathAssertion'">
              <div class="form-section">
                <div class="form-group"><label>断言名称</label><el-input v-model="selectedNode.name" size="small" /></div>
                <div class="form-group"><label>XPath 表达式</label><el-input v-model="selectedNode.props.xpath" placeholder="/html/body/h1 或 //result[@status='ok']" size="small" /></div>
                <div class="form-group"><label>取反（不存在才通过）</label><el-switch v-model="selectedNode.props.negate" size="small" /></div>
              </div>
              <div class="section-hint"><el-icon><InfoFilled /></el-icon> 💡 小白提示：用于断言XML/HTML响应中某个节点存在。如 //result[@status='ok'] 表示检查是否存在status为ok的result节点</div>
            </template>

            <!-- ===== 比较断言 ===== -->
            <template v-if="selectedNode.type === 'CompareAssertion'">
              <div class="form-section">
                <div class="form-group"><label>断言名称</label><el-input v-model="selectedNode.name" size="small" /></div>
                <div class="form-group"><label>检查范围</label>
                  <el-select v-model="selectedNode.props.testField" size="small">
                    <el-option label="响应数据" value="Assertion.response_data" />
                    <el-option label="响应代码" value="Assertion.response_code" />
                    <el-option label="响应消息" value="Assertion.response_message" />
                    <el-option label="请求头" value="Assertion.response_headers" />
                    <el-option label="URL" value="Assertion.sample_label" />
                  </el-select>
                </div>
                <div class="form-group"><label>比较规则</label>
                  <el-select v-model="selectedNode.props.compareType" size="small">
                    <el-option label="包含" value="contains" />
                    <el-option label="等于" value="==" />
                    <el-option label="匹配(正则)" value="matches" />
                    <el-option label="不等于" value="≠" />
                    <el-option label="子串" value="substring" />
                  </el-select>
                </div>
                <div class="form-group"><label>期望值</label><el-input v-model="selectedNode.props.expected" placeholder="要匹配的值" size="small" /></div>
              </div>
              <div class="section-hint"><el-icon><InfoFilled /></el-icon> 💡 小白提示：灵活的比较断言，可以选择检查响应体/状态码/请求头等不同部位</div>
            </template>

            <!-- ===== XML 断言 ===== -->
            <template v-if="selectedNode.type === 'XMLAssertion'">
              <div class="form-section">
                <div class="form-group"><label>断言名称</label><el-input v-model="selectedNode.name" size="small" /></div>
              </div>
              <div class="section-hint"><el-icon><InfoFilled /></el-icon> 💡 小白提示：自动验证响应体是否为合法XML。如果接口返回XML格式数据，加上这个断言确保格式正确</div>
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
            <template v-if="selectedNode.type === 'JSR223PreProcessor' || selectedNode.type === 'JSR223PostProcessor'">
              <div class="form-section">
                <div class="form-group"><label>脚本名称</label><el-input v-model="selectedNode.name" size="small" /></div>
                <div class="form-group"><label>脚本语言</label>
                  <el-select v-model="selectedNode.props.language" size="small">
                    <el-option label="Groovy" value="groovy" />
                    <el-option label="JavaScript" value="javascript" />
                    <el-option label="Python (Jython)" value="python" />
                    <el-option label="BeanShell" value="beanshell" />
                  </el-select>
                </div>
                <div class="form-group"><label>脚本代码</label><el-input v-model="selectedNode.props.script" type="textarea" :rows="6" placeholder='log.info("Hello JMeter")' size="small" /></div>
              </div>
            </template>
            <template v-if="selectedNode.type === 'IfController'">
              <div class="form-section">
                <div class="section-hint"><el-icon><InfoFilled /></el-icon> 条件成立时才执行子元素。如 <code>${JMeterThread.last_sample_ok}</code> 表示上一个请求成功才执行</div>
                <div class="form-group"><label>控制器名称</label><el-input v-model="selectedNode.name" size="small" /></div>
                <div class="form-group"><label>条件表达式</label><el-input v-model="selectedNode.props.condition" size="small" placeholder="${JMeterThread.last_sample_ok}" /></div>
                <div class="form-row">
                  <div class="form-group"><label>解释为变量表达式</label><el-switch v-model="selectedNode.props.useExpression" size="small" /></div>
                  <div class="form-group"><label>对所有子级求值</label><el-switch v-model="selectedNode.props.evaluateAll" size="small" /></div>
                </div>
                <div class="form-group"><label>添加子元素到控制器中</label>
                  <div style="display:flex;gap:4px;flex-wrap:wrap">
                    <el-button size="small" @click="addChildToCurrent('HttpSampler')">🌐 HTTP 请求</el-button>
                    <el-button size="small" @click="addChildToCurrent('LoopController')">🔄 循环</el-button>
                    <el-button size="small" @click="addChildToCurrent('IfController')">🔀 如果</el-button>
                  </div>
                </div>
              </div>
            </template>
            <template v-if="selectedNode.type === 'LoopController'">
              <div class="form-section">
                <div class="section-hint"><el-icon><InfoFilled /></el-icon> 将子元素重复执行指定次数。如循环 3 次 = 子元素执行 3 遍</div>
                <div class="form-group"><label>控制器名称</label><el-input v-model="selectedNode.name" size="small" /></div>
                <div class="form-row">
                  <div class="form-group"><label>循环次数</label><el-input-number v-model="selectedNode.props.loops" :min="1" :max="99999" size="small" /></div>
                  <div class="form-group"><label>永久循环</label><el-switch v-model="selectedNode.props.forever" size="small" /></div>
                </div>
              </div>
            </template>
            <template v-if="selectedNode.type === 'WhileController'">
              <div class="form-section">
                <div class="section-hint"><el-icon><InfoFilled /></el-icon> 条件为真时不断循环子元素。如 <code>${__javaScript(${counter} < 5)}</code></div>
                <div class="form-group"><label>控制器名称</label><el-input v-model="selectedNode.name" size="small" /></div>
                <div class="form-group"><label>条件</label><el-input v-model="selectedNode.props.condition" size="small" placeholder="${__javaScript(vars.get('counter') < 5)}" /></div>
              </div>
            </template>
            <template v-if="selectedNode.type === 'TransactionController'">
              <div class="form-section">
                <div class="section-hint"><el-icon><InfoFilled /></el-icon> 将子元素视为一个事务，统计总耗时作为该事务的响应时间</div>
                <div class="form-group"><label>控制器名称</label><el-input v-model="selectedNode.name" size="small" /></div>
                <div class="form-row">
                  <div class="form-group"><label>包含定时器时间</label><el-switch v-model="selectedNode.props.includeTimers" size="small" /></div>
                  <div class="form-group"><label>生成父样本</label><el-switch v-model="selectedNode.props.parent" size="small" /></div>
                </div>
              </div>
            </template>
            <template v-if="selectedNode.type === 'ThroughputController'">
              <div class="form-section">
                <div class="section-hint"><el-icon><InfoFilled /></el-icon> 控制子元素执行的频率/比例。如 50% = 一半线程执行、一半跳过</div>
                <div class="form-group"><label>控制器名称</label><el-input v-model="selectedNode.name" size="small" /></div>
                <div class="form-group"><label>控制方式</label>
                  <el-select v-model="selectedNode.props.style" size="small">
                    <el-option label="按百分比" value="percent" />
                    <el-option label="按总执行次数" value="total" />
                    <el-option label="按每分钟执行次数" value="perMinute" />
                  </el-select>
                </div>
                <div class="form-group" v-if="selectedNode.props.style === 'percent'"><label>百分比 (%)</label><el-input-number v-model="selectedNode.props.percent" :min="0" :max="100" size="small" /></div>
                <div class="form-group" v-else><label>最大吞吐量</label><el-input-number v-model="selectedNode.props.maxThroughput" :min="1" :max="99999" size="small" /></div>
                <div class="form-group"><label>按用户独立计算</label><el-switch v-model="selectedNode.props.perThread" size="small" /></div>
              </div>
            </template>
            <template v-if="selectedNode.type === 'OnceOnlyController'">
              <div class="form-section">
                <div class="section-hint"><el-icon><InfoFilled /></el-icon> 不管循环多少次，子元素只执行一次。常用于登录等只需执行一次的场景</div>
                <div class="form-group"><label>控制器名称</label><el-input v-model="selectedNode.name" size="small" /></div>
                <div class="form-group"><label>添加子元素到控制器中</label>
                  <div style="display:flex;gap:4px;flex-wrap:wrap">
                    <el-button size="small" @click="addChildToCurrent('HttpSampler')">🌐 HTTP 请求</el-button>
                  </div>
                </div>
              </div>
            </template>
            <template v-if="selectedNode.type === 'HTTPHeaderManager'">
              <div class="form-section">
                <div class="section-hint"><el-icon><InfoFilled /></el-icon> 为所有 HTTP 请求统一添加请求头，自动继承到子元素</div>
                <div class="form-group"><label>管理器名称</label><el-input v-model="selectedNode.name" size="small" /></div>
                <div class="form-group"><label>请求头</label>
                  <div v-for="(h, hi) in (selectedNode.props.headers || [])" :key="hi" class="kv-row">
                    <el-input v-model="h.key" placeholder="Header名" size="small" style="width:40%" />
                    <el-input v-model="h.value" placeholder="值" size="small" style="width:50%" />
                    <el-button link size="small" type="danger" @click="selectedNode.props.headers.splice(hi,1)">×</el-button>
                  </div>
                  <el-button size="small" @click="selectedNode.props.headers.push({key:'',value:''})">+ 添加请求头</el-button>
                </div>
              </div>
            </template>
            <template v-if="selectedNode.type === 'HTTPCookieManager'">
              <div class="form-section">
                <div class="section-hint"><el-icon><InfoFilled /></el-icon> 自动管理 HTTP Cookie，模拟真实浏览器行为</div>
                <div class="form-group"><label>管理器名称</label><el-input v-model="selectedNode.name" size="small" /></div>
                <div class="form-group"><label>每次循环清空</label><el-switch v-model="selectedNode.props.clearEachIteration" size="small" /></div>
              </div>
            </template>
            <template v-if="selectedNode.type === 'HTTPRequestDefaults'">
              <div class="form-section">
                <div class="section-hint"><el-icon><InfoFilled /></el-icon> 设置默认的协议、域名、端口和请求头，子元素可继承或覆盖这些配置</div>
                <div class="form-group"><label>默认值名称</label><el-input v-model="selectedNode.name" size="small" /></div>
                <div class="form-group"><label>默认 URL 前缀</label><el-input v-model="selectedNode.props.url" size="small" placeholder="https://api.example.com" /></div>
                <div class="form-group"><label>默认方法</label>
                  <el-select v-model="selectedNode.props.method" size="small">
                    <el-option v-for="m in ['GET','POST']" :key="m" :label="m" :value="m" />
                  </el-select>
                </div>
              </div>
            </template>
            <template v-if="selectedNode.type === 'ViewResultsTree' || selectedNode.type === 'SummaryReport' || selectedNode.type === 'AggregateGraph' || selectedNode.type === 'AggregateReport' || selectedNode.type === 'ResponseTimeGraph'">
              <div class="form-section"><div class="form-group"><label>监听器名称</label><el-input v-model="selectedNode.name" size="small" /></div></div>
            </template>
          </div>
          <div class="editor-empty" v-else>
            <el-icon size="36"><EditPen /></el-icon>
            <p>选择左侧树中的元素<br/>开始编辑属性</p>
          </div>
        </div>
      </div>
    </div>

    <!-- ==================== Step 3: 验证 & 导出 ==================== -->
    <div v-show="currentStep === 3" class="step-body">
      <div class="step3-layout">

        <!-- 主区域：并发验证 + 调试 -->
        <div class="step3-main">
          <el-tabs v-model="rightTab3" class="right-tabs">
            <el-tab-pane label="⚡ 并发验证" name="bench">
              <div class="bench-body">
                <div class="section-hint"><el-icon><InfoFilled /></el-icon> 不依赖 JMeter，直接在平台内验证多个并发能否跑通。设置并发数、持续时间、预热时间，点击下方按钮开始</div>
                <div class="bench-controls">
                  <div class="form-group"><label>并发数</label><el-tooltip content="模拟多少个用户同时访问，如 50 = 50 个虚拟用户同时跑" placement="top"><el-input-number v-model="benchConcurrency" :min="1" :max="200" size="small" /></el-tooltip></div>
                  <div class="form-group"><label>持续(秒)</label><el-tooltip content="总共跑多长时间，如 60 = 持续压测 60 秒" placement="top"><el-input-number v-model="benchDuration" :min="3" :max="60" size="small" /></el-tooltip></div>
                  <div class="form-group"><label>预热(秒)</label><el-tooltip content="逐步启动的时间，避免瞬间压垮服务。如 5 = 5 秒内逐步启动完所有并发用户" placement="top"><el-input-number v-model="benchRampUp" :min="0" :max="10" size="small" /></el-tooltip></div>
                </div>
                <el-button v-if="!benching" type="danger" size="large" @click="startBench" style="width:100%;margin-bottom:8px;font-size:15px;font-weight:700">
                  ⚡ 开始并发测试（{{ benchConcurrency }} 虚拟用户 × {{ benchDuration }}秒）
                </el-button>
                <el-button v-else type="warning" size="large" @click="stopBench" style="width:100%;margin-bottom:8px;font-size:15px;font-weight:700">
                  ⏹ 停止轮询（测试仍在后台执行）
                </el-button>
                <div v-if="benching || benchProgress" class="bench-progress">
                  <el-progress :percentage="benchPercent" :stroke-width="10" :status="benchPercent >= 100 ? 'success' : ''" />
                  <span class="bench-progress-text">{{ benchProgress }}</span>
                </div>

                <!-- ===== 并发结果 ===== -->
                <div v-if="benchResult" class="bench-result">
                  <h4 class="bench-section-title">📊 总体统计</h4>
                  <div class="bench-stats">
                    <div class="bench-stat">
                      <span class="bench-stat-value" :class="benchResult.failed > 0 ? 'text-danger' : 'text-success'">{{ benchResult.total }}</span>
                      <span class="bench-stat-label">总请求数</span>
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
                      <span class="bench-stat-label">TPS（每秒请求数）</span>
                    </div>
                    <div class="bench-stat">
                      <span class="bench-stat-value">{{ benchResult.avg_ms }}ms</span>
                      <span class="bench-stat-label">平均响应时间</span>
                    </div>
                    <div class="bench-stat">
                      <span class="bench-stat-value">{{ benchResult.p50_ms }}ms</span>
                      <span class="bench-stat-label">P50（中位数）</span>
                    </div>
                    <div class="bench-stat">
                      <span class="bench-stat-value">{{ benchResult.p95_ms }}ms</span>
                      <span class="bench-stat-label">P95（95%的请求快于此）</span>
                    </div>
                    <div class="bench-stat">
                      <span class="bench-stat-value">{{ benchResult.p99_ms }}ms</span>
                      <span class="bench-stat-label">P99（99%的请求快于此）</span>
                    </div>
                  </div>

                  <!-- 状态码分布 -->
                  <div v-if="benchResult.status_distribution" style="margin-top:8px;display:flex;gap:6px;flex-wrap:wrap;align-items:center">
                    <span style="font-size:11px;color:var(--tm-text-secondary)">状态码：</span>
                    <el-tag v-for="(count, code) in benchResult.status_distribution" :key="code" :type="code === '200' ? 'success' : code >= '400' ? 'danger' : 'warning'" size="small">
                      HTTP {{ code }}: {{ count }}
                    </el-tag>
                  </div>

                  <!-- 错误信息 -->
                  <div v-if="benchResult.errors && benchResult.errors.length > 0" style="margin-top:6px">
                    <el-alert v-for="(err, ei) in benchResult.errors.slice(0,5)" :key="ei" :title="err" type="error" :closable="false" show-icon style="margin-bottom:2px;font-size:11px" />
                  </div>

                  <!-- ===== 按接口统计（聚合报告）直接展开 ===== -->
                  <div v-if="benchResult.per_url && benchResult.per_url.length > 0" class="bench-data-block">
                    <h4 class="bench-section-title" style="display:flex;justify-content:space-between;align-items:center">
                      📊 按接口统计（聚合报告）
                      <span style="font-size:11px;font-weight:400;color:var(--tm-text-secondary)">共 {{ benchResult.per_url.length }} 个接口</span>
                    </h4>
                    <div class="per-url-table">
                      <div class="per-url-header">
                        <span class="col-url">接口 URL</span>
                        <span class="col-num">请求数</span>
                        <span class="col-num">成功</span>
                        <span class="col-num">失败</span>
                        <span class="col-num">平均耗时</span>
                        <span class="col-num">P95 耗时</span>
                        <span class="col-num">最慢耗时</span>
                      </div>
                      <div v-for="pu in benchResult.per_url" :key="pu.url" class="per-url-row">
                        <span class="col-url" :title="pu.url">{{ shortUrl(pu.url) }}</span>
                        <span class="col-num">{{ pu.count }}</span>
                        <span class="col-num text-success">{{ pu.success }}</span>
                        <span class="col-num" :class="pu.failed > 0 ? 'text-danger' : ''">{{ pu.failed }}</span>
                        <span class="col-num">{{ pu.avg_ms }}ms</span>
                        <span class="col-num">{{ pu.p95_ms }}ms</span>
                        <span class="col-num">{{ pu.max_ms }}ms</span>
                      </div>
                    </div>
                  </div>

                  <!-- ===== 请求详情列表（查看结果树）直接展开 ===== -->
                  <div v-if="benchResult.samples && benchResult.samples.length > 0" class="bench-data-block">
                    <h4 class="bench-section-title" style="display:flex;justify-content:space-between;align-items:center">
                      🔍 请求详情（查看结果树）
                      <span style="font-size:11px;font-weight:400;color:var(--tm-text-secondary)">共 {{ benchResult.samples.length }} 条样本，点击展开查看详情</span>
                    </h4>
                    <div class="sample-list" style="max-height:320px;overflow-y:auto">
                      <div v-for="(s, si) in benchResult.samples" :key="si" class="sample-item" @click="toggleSample(si)">
                        <div class="sample-summary">
                          <el-tag :type="s.status >= 200 && s.status < 400 ? 'success' : s.status === 0 ? 'danger' : 'warning'" size="small">{{ s.status || 'ERR' }}</el-tag>
                          <span class="sample-time">{{ s.elapsed_ms }}ms</span>
                          <span class="sample-url" style="flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{{ s.method ? s.method + ' ' : '' }}{{ shortUrl(s.url) }}</span>
                          <span v-if="s.error" class="sample-err" :title="s.error">⚠ {{ s.error.substring(0,50) }}</span>
                        </div>
                        <div v-if="expandedSamples[si]" class="sample-detail">
                          <div class="sample-detail-row"><span class="sample-detail-label">完整 URL：</span>{{ s.url }}</div>
                          <div class="sample-detail-row"><span class="sample-detail-label">HTTP 方法：</span>{{ s.method || '-' }}</div>
                          <div class="sample-detail-row"><span class="sample-detail-label">状态码：</span><el-tag :type="s.status >= 200 && s.status < 400 ? 'success' : 'danger'" size="small">{{ s.status || 'ERR' }}</el-tag></div>
                          <div class="sample-detail-row"><span class="sample-detail-label">耗时：</span>{{ s.elapsed_ms }}ms</div>
                          <div class="sample-detail-row"><span class="sample-detail-label">响应大小：</span>{{ s.body_size || 0 }}B</div>
                          <div v-if="s.error" class="sample-detail-row"><span class="sample-detail-label">错误信息：</span><span style="color:var(--el-color-danger)">{{ s.error }}</span></div>
                        </div>
                      </div>
                    </div>
                  </div>

                  <!-- ===== 响应体采样 直接展开 ===== -->
                  <div v-if="benchResult.body_samples && benchResult.body_samples.length > 0" class="bench-data-block">
                    <h4 class="bench-section-title" style="display:flex;justify-content:space-between;align-items:center">
                      📄 响应体采样
                      <span style="font-size:11px;font-weight:400;color:var(--tm-text-secondary)">每个接口前 3 条响应内容，最多 1000 字符</span>
                    </h4>
                    <div v-for="(bs, bi) in benchResult.body_samples" :key="bi" style="margin-bottom:6px">
                      <div style="display:flex;align-items:center;gap:6px;font-size:11px;color:var(--tm-text-secondary);margin-bottom:3px">
                        <el-tag :type="bs.status >= 200 && bs.status < 400 ? 'success' : 'danger'" size="small">{{ bs.status }}</el-tag>
                        <span style="word-break:break-all">{{ shortUrl(bs.url) }}</span>
                      </div>
                      <pre class="bench-body-preview">{{ bs.body }}</pre>
                    </div>
                  </div>
                </div>

                <!-- 还没跑过并发 -->
                <div v-if="!benchResult && !benching && !benchProgress" class="bench-empty-hint">
                  <el-icon size="40"><VideoPlay /></el-icon>
                  <p>点击上方「⚡ 开始并发测试」按钮<br/>不依赖 JMeter，直接在平台内验证并发效果</p>
                </div>
              </div>
            </el-tab-pane>

            <el-tab-pane label="🐛 单请求调试" name="debug">
              <div class="debug-body">
                <div class="section-hint"><el-icon><InfoFilled /></el-icon> 在「配置参数」步骤选中一个 HTTP 请求点击「调试」，在此查看请求/响应详情</div>
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
          </el-tabs>
        </div>

        <!-- 侧边栏：JMX 预览（compact） -->
        <div class="step3-sidebar">
          <div class="panel-title" @click="showJmxPreview = !showJmxPreview" style="cursor:pointer;user-select:none">
            <span>📦 JMX 导出 {{ showJmxPreview ? '▲' : '▼' }}</span>
          </div>
          <div v-if="showJmxPreview" class="jmx-preview-compact">
            <div style="display:flex;gap:6px;margin-bottom:6px;flex-wrap:wrap">
              <el-button size="small" @click="generatePreview" :loading="generating">
                🔮 生成预览
              </el-button>
              <el-button size="small" type="success" @click="downloadJmx" :disabled="!jmxContent">
                <el-icon><Download /></el-icon> 下载 .jmx
              </el-button>
            </div>
            <pre v-if="jmxContent" class="xml-preview-compact"><code>{{ jmxContent }}</code></pre>
            <div v-else class="empty-hint" style="padding:16px;font-size:12px">
              <p>点击「生成预览」<br/>查看 JMX 内容<br/><span style="color:var(--tm-text-secondary);font-size:11px">导出后可导入 JMeter 运行</span></p>
            </div>
          </div>
          <div v-else style="padding:12px;font-size:12px;color:var(--tm-text-secondary)">
            📦 JMX 导出功能：生成 .jmx 文件，可用于 JMeter 或 CI/CD 中运行
            <div style="margin-top:8px;display:flex;gap:6px">
              <el-button size="small" @click="downloadJmx" :disabled="!jmxContent" type="success">
                <el-icon><Download /></el-icon> 直接下载 .jmx
              </el-button>
              <el-button size="small" @click="showJmxPreview = true; generatePreview()">🔮 预览</el-button>
            </div>
          </div>
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
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Plus, Refresh, Download, Right, QuestionFilled, VideoPlay, EditPen, FolderDelete, Search, UploadFilled, InfoFilled, Monitor, Connection, Coin, Lollipop, Setting, Document } from '@element-plus/icons-vue'
import autoTestRequest from '@/utils/autoTestRequest'
import request from '@/utils/request'
import JmeterTreeNode from '@/components/JmeterTreeNode.vue'

const router = useRouter()

// ===== 组件类型定义 =====
const NODE_TYPES = {
  TestPlan: { label: '测试计划', icon: '📋' },
  ThreadGroup: { label: '线程组', icon: '👥', parent: 'TestPlan' },
  HttpSampler: { label: 'HTTP 请求', icon: '🌐', parent: 'ThreadGroup' },
  IfController: { label: '如果(If)控制器', icon: '🔀', parent: 'ThreadGroup' },
  LoopController: { label: '循环控制器', icon: '🔄', parent: 'ThreadGroup' },
  WhileController: { label: 'While 控制器', icon: '🔁', parent: 'ThreadGroup' },
  TransactionController: { label: '事务控制器', icon: '📦', parent: 'ThreadGroup' },
  ThroughputController: { label: '吞吐量控制器', icon: '⏱️', parent: 'ThreadGroup' },
  OnceOnlyController: { label: '仅一次控制器', icon: '1️⃣', parent: 'ThreadGroup' },
  ResponseAssertion: { label: '响应断言', icon: '✅', parent: 'HttpSampler' },
  DurationAssertion: { label: '持续时间断言', icon: '⏱️', parent: 'HttpSampler' },
  JsonAssertion: { label: 'JSON 断言', icon: '📋', parent: 'HttpSampler' },
  BeanShellAssertion: { label: 'BeanShell 断言', icon: '💻', parent: 'HttpSampler' },
  JSR223Assertion: { label: 'JSR223 断言', icon: '🔥', parent: 'HttpSampler' },
  SizeAssertion: { label: '响应大小断言', icon: '📏', parent: 'HttpSampler' },
  XPathAssertion: { label: 'XPath 断言', icon: '🗂️', parent: 'HttpSampler' },
  CompareAssertion: { label: '比较断言', icon: '⚖️', parent: 'HttpSampler' },
  XMLAssertion: { label: 'XML 断言', icon: '📜', parent: 'HttpSampler' },
  RegexExtractor: { label: '正则提取器', icon: '🔍', parent: 'HttpSampler' },
  JsonExtractor: { label: 'JSON 提取器', icon: '📤', parent: 'HttpSampler' },
  ConstantTimer: { label: '固定定时器', icon: '⏰', parent: 'HttpSampler' },
  UniformRandomTimer: { label: '均匀随机定时器', icon: '🎲', parent: 'HttpSampler' },
  GaussianRandomTimer: { label: '高斯随机定时器', icon: '📊', parent: 'HttpSampler' },
  SyncTimer: { label: '同步定时器(集合点)', icon: '🔄', parent: 'HttpSampler' },
  BeanShellPreProcessor: { label: 'BeanShell 前置', icon: '⚙️', parent: 'HttpSampler' },
  BeanShellPostProcessor: { label: 'BeanShell 后置', icon: '⚙️', parent: 'HttpSampler' },
  JSR223PreProcessor: { label: 'JSR223 前置处理器', icon: '🔥', parent: 'HttpSampler' },
  JSR223PostProcessor: { label: 'JSR223 后置处理器', icon: '🔥', parent: 'HttpSampler' },
  CSVDataSet: { label: 'CSV 数据源', icon: '📄', parent: 'ThreadGroup' },
  JDBCConnection: { label: 'JDBC 连接', icon: '🗄️', parent: 'TestPlan' },
  JDBCSampler: { label: 'JDBC 请求', icon: '🗄️', parent: 'ThreadGroup' },
  HTTPHeaderManager: { label: 'HTTP 信息头管理器', icon: '📨', parent: 'ThreadGroup' },
  HTTPCookieManager: { label: 'HTTP Cookie 管理器', icon: '🍪', parent: 'ThreadGroup' },
  HTTPRequestDefaults: { label: 'HTTP 请求默认值', icon: '🎯', parent: 'ThreadGroup' },
  ViewResultsTree: { label: '查看结果树', icon: '👁️', parent: 'ThreadGroup' },
  SummaryReport: { label: '聚合报告', icon: '📈', parent: 'ThreadGroup' },
  AggregateGraph: { label: '聚合图表', icon: '📉', parent: 'ThreadGroup' },
  AggregateReport: { label: '聚合报告(高级)', icon: '📊', parent: 'ThreadGroup' },
  ResponseTimeGraph: { label: '响应时间图', icon: '📉', parent: 'ThreadGroup' },
}

// ===== 工具函数 =====
let uidCounter = 1
const newUid = () => `el_${uidCounter++}`

const defaultProps = {
  HttpSampler: { method: 'GET', url: '', headers: [{ key: 'Content-Type', value: 'application/json' }], body: '', bodyType: 'json' },
  ThreadGroup: { threads: 10, rampUp: 5, loops: 1, duration: 60 },
  TestPlan: { variables: [] },
  ResponseAssertion: { assertType: 'status_code', expected: 200, jsonPath: '', maxDuration: 1000 },
  DurationAssertion: { maxDuration: 1000 },
  JsonAssertion: { jsonPath: '$', expected: '', jsonValidation: true, expectNull: false, invert: false },
  BeanShellAssertion: { script: '// BeanShell脚本\n// 可用变量: ResponseCode, ResponseMessage, ResponseData, SampleResult, Failure\n// 示例: 检查状态码是否为200\nif (!ResponseCode.equals("200")) {\n    Failure = true;\n    FailureMessage = "期望200, 实际" + ResponseCode;\n}', filename: '', parameters: '', resetInterpreter: false },
  JSR223Assertion: { language: 'groovy', script: '// Groovy脚本\n// 可用变量: prev, log\n// 示例: 断言响应包含"success"\nif (!prev.getResponseDataAsString().contains("success")) {\n    AssertionResult.setFailure(true)\n    AssertionResult.setFailureMessage("响应中未找到 success")\n}' },
  SizeAssertion: { size: 5000, operator: '>' },
  XPathAssertion: { xpath: '/', negate: false },
  CompareAssertion: { compareType: 'contains', expected: '', compareContent: false, testField: 'Assertion.response_data' },
  XMLAssertion: {},
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
  JSR223PreProcessor: { language: 'groovy', script: '' },
  JSR223PostProcessor: { language: 'groovy', script: '' },
  IfController: { condition: '${JMeterThread.last_sample_ok}', evaluateAll: false, useExpression: true },
  LoopController: { loops: 3, forever: false },
  WhileController: { condition: '${__javaScript(${counter} < 5)}' },
  TransactionController: { includeTimers: false, parent: false },
  ThroughputController: { style: 'percent', percent: 50, maxThroughput: 1, perThread: false },
  OnceOnlyController: {},
  HTTPHeaderManager: { headers: [{ key: 'Content-Type', value: 'application/json' }] },
  HTTPCookieManager: { cookies: [], clearEachIteration: false },
  HTTPRequestDefaults: { method: 'GET', url: '', headers: [], body: '', bodyType: 'json' },
  ViewResultsTree: {},
  SummaryReport: {},
  AggregateGraph: {},
  AggregateReport: {},
  ResponseTimeGraph: {},
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

const totalThreads = computed(() => {
  let count = 0
  const walk = (node) => {
    if (node.type === 'ThreadGroup') count += (node.props.threads || 10)
    ;(node.children || []).forEach(walk)
  }
  walk(scriptTree)
  return count
})

const totalSamplers = computed(() => {
  let count = 0
  const walk = (node) => {
    if (node.type === 'HttpSampler') count++
    ;(node.children || []).forEach(walk)
  }
  walk(scriptTree)
  return count
})

const totalAssertions = computed(() => {
  let count = 0
  const walk = (node) => {
    if (['ResponseAssertion','DurationAssertion','JsonAssertion','BeanShellAssertion','JSR223Assertion','SizeAssertion','XPathAssertion','CompareAssertion','XMLAssertion'].includes(node.type)) count++
    ;(node.children || []).forEach(walk)
  }
  walk(scriptTree)
  return count
})

const totalExtractors = computed(() => {
  let count = 0
  const walk = (node) => {
    if (['RegexExtractor','JsonExtractor'].includes(node.type)) count++
    ;(node.children || []).forEach(walk)
  }
  walk(scriptTree)
  return count
})

const totalTimers = computed(() => {
  let count = 0
  const walk = (node) => {
    if (['ConstantTimer','UniformRandomTimer','GaussianRandomTimer','SyncTimer'].includes(node.type)) count++
    ;(node.children || []).forEach(walk)
  }
  walk(scriptTree)
  return count
})

const totalListeners = computed(() => {
  let count = 0
  const walk = (node) => {
    if (['ViewResultsTree','SummaryReport','AggregateGraph','AggregateReport','ResponseTimeGraph'].includes(node.type)) count++
    ;(node.children || []).forEach(walk)
  }
  walk(scriptTree)
  return count
})

const summaryEmoji = computed(() => {
  if (totalSamplers.value === 0) return '📭'
  if (totalAssertions.value === 0) return '🧪'
  return '🚀'
})

const summaryTitle = computed(() => {
  if (totalSamplers.value === 0) return '还没有添加请求'
  if (totalAssertions.value === 0) return '脚本已就绪，建议添加断言验证结果'
  return '测试脚本已配置完整，可以去第3步验证并发或导出 .jmx'
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
    const items = []
    const walk = (node) => {
      if (node.type === 'HttpSampler') {
        const tag = node.props.responseAssertion ? '✅' : ''
        items.push((node.props.method || 'GET') + ' ' + (node.name || node.props.url || ''))
      }
      (node.children || []).forEach(walk)
    }
    walk(tg)
    let desc = `用 ${ramp} 秒逐步启动 ${threads} 个虚拟用户`
    if (duration > 0) {
      desc += `，持续运行 ${duration} 秒`
    } else {
      desc += `，每个用户循环执行 ${loops} 次`
    }
    if (items.length > 0) {
      desc += `，共 ${items.length} 个请求：${items.join('、')}`
    }
    // 添加额外组件描述
    const extras = []
    const countExtras = (node) => {
      if (['ResponseAssertion','DurationAssertion','JsonAssertion','BeanShellAssertion','JSR223Assertion','SizeAssertion','XPathAssertion','CompareAssertion','XMLAssertion'].includes(node.type)) { if (!extras.includes('断言')) extras.push('断言') }
      if (['RegexExtractor','JsonExtractor'].includes(node.type)) { if (!extras.includes('提取器')) extras.push('提取器') }
      if (['ConstantTimer','UniformRandomTimer','GaussianRandomTimer'].includes(node.type)) { if (!extras.includes('定时器')) extras.push('定时器') }
      if (node.type === 'SyncTimer') { if (!extras.includes('集合点')) extras.push('集合点') }
      if (node.type === 'CSVDataSet') { if (!extras.includes('CSV数据驱动')) extras.push('CSV数据驱动') }
      if (['ViewResultsTree','SummaryReport','AggregateGraph'].includes(node.type)) { if (!extras.includes('报告')) extras.push('报告') }
      (node.children || []).forEach(countExtras)
    }
    countExtras(tg)
    if (extras.length > 0) {
      desc += `（含 ${extras.join('、')}）`
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

const openInterfaceLib = () => { router.push({ path: '/auto-test', query: { tab: 'interfaces' } }) }

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
const showJmxPreview = ref(false)

const rightTab3 = ref('bench')

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
const expandedSamples = ref({})
let benchPollTimer = null

const shortUrl = (url) => {
  try {
    const u = new URL(url)
    return u.pathname + u.search || '/'
  } catch { return url.length > 50 ? url.substring(0, 50) + '...' : url }
}

const toggleSample = (idx) => {
  expandedSamples.value[idx] = !expandedSamples.value[idx]
}

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
  expandedSamples.value = {}
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
const aiGenerating = ref(false)
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

const aiGenerateAssert = async (type) => {
  const parentSampler = findParentSampler(scriptTree, selectedNode.value?.uid)
  const method = parentSampler?.props?.method || 'GET'
  const url = parentSampler?.props?.url || ''
  const body = parentSampler?.props?.body || ''
  const headers = parentSampler?.props?.headers || []

  let prompt = ''
  if (type === 'BeanShell') {
    prompt = `你是一个JMeter专家。请为以下HTTP请求编写一个BeanShell断言脚本。\n\n请求信息：\n- 方法: ${method}\n- URL: ${url}\n${body ? '- 请求体: ' + body.substring(0, 300) : ''}\n${headers.length > 0 ? '- 请求头: ' + JSON.stringify(headers.slice(0, 3)) : ''}\n\n要求：\n1. 写一个完整的BeanShell断言（Java语法）\n2. 检查HTTP状态码是否为200\n3. 检查响应体是否包含"success"或类似成功标识\n4. 加上合理的中文FailureMessage\n5. 只输出代码，不要解释`
  } else if (type === 'JSR223') {
    prompt = `你是一个JMeter专家。请为以下HTTP请求编写一个Groovy语言的JSR223断言脚本。\n\n请求信息：\n- 方法: ${method}\n- URL: ${url}\n${body ? '- 请求体: ' + body.substring(0, 300) : ''}\n\n要求：\n1. 写一个完整的Groovy断言\n2. 检查HTTP状态码是否为200（prev.getResponseCode()）\n3. 检查响应体是否非空\n4. 加上合理的中文FailureMessage\n5. 只输出代码，不要解释`
  } else if (type === 'Json') {
    const suggestedPath = body && body.includes('{') ? '$.data' : '$.status'
    prompt = `你是一个API测试专家。请分析以下请求并建议合理的JSON断言。\n\n请求信息：\n- 方法: ${method}\n- URL: ${url}\n\n请输出JSON格式：{"jsonPath": "建议的JSONPath", "expected": "建议的期望值"}\n只输出JSON，不要解释`
  }

  aiGenerating.value = true
  try {
    const res = await request.post('/ai/chat', { question: prompt })
    const answer = res.answer || ''
    if (type === 'Json') {
      try {
        const jsonStart = answer.indexOf('{')
        const jsonEnd = answer.lastIndexOf('}') + 1
        if (jsonStart >= 0 && jsonEnd > jsonStart) {
          const parsed = JSON.parse(answer.substring(jsonStart, jsonEnd))
          if (parsed.jsonPath) selectedNode.value.props.jsonPath = parsed.jsonPath
          if (parsed.expected) selectedNode.value.props.expected = parsed.expected
        }
      } catch (e) { /* fall though */ }
    } else {
      const codeMatch = answer.match(/```(?:java|groovy|beanshell)?\n?([\s\S]*?)```/)
      const code = codeMatch ? codeMatch[1].trim() : answer.trim()
      selectedNode.value.props.script = code
    }
    ElMessage.success('🤖 AI 已为你生成断言，可自行微调')
  } catch (e) {
    ElMessage.error('AI 生成失败，请检查 AI 配置或稍后重试')
  }
  finally { aiGenerating.value = false }
}

const findParentSampler = (parent, uid) => {
  if (!uid) return null
  for (const child of parent.children || []) {
    if (child.uid === uid) return parent.type === 'HttpSampler' ? parent : null
    if (child.children?.length) {
      const found = findParentSampler(child, uid)
      if (found) return found
      if (child.type === 'HttpSampler' && child.children?.some(c => c.uid === uid)) return child
    }
  }
  return null
}
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
.step1-left { display: flex; flex-direction: column; gap: 12px; overflow-y: auto; }
.step1-templates { overflow: visible; }
.step1-import-jmx { }
.import-jmx-card { display: flex; align-items: center; gap: 12px; padding: 14px; background: var(--tm-card-bg); border: 1px dashed var(--tm-color-primary); border-radius: 10px; cursor: pointer; transition: all 0.2s; }
.import-jmx-card:hover { background: rgba(64,158,255,0.06); border-color: var(--tm-color-primary); border-style: solid; }
.import-jmx-icon { font-size: 28px; flex-shrink: 0; }
.import-jmx-body { flex: 1; }
.import-jmx-title { font-size: 13px; font-weight: 700; color: var(--tm-text-primary); }
.import-jmx-desc { font-size: 11px; color: var(--tm-text-secondary); margin-top: 2px; }
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
.step2-layout { display: grid; grid-template-columns: 330px 1fr; gap: 16px; padding: 0 16px 16px; height: calc(100% - 90px); overflow: hidden; }
.tree-panel { display: flex; flex-direction: column; overflow: hidden; }
.tree-body { flex: 1; overflow-y: auto; padding: 4px; }
.tree-root-label { display: flex; align-items: center; gap: 6px; padding: 8px; border-radius: 6px; font-weight: 600; font-size: 13px; cursor: pointer; }
.tree-root-label:hover { background: rgba(255,255,255,0.04); }
.root-icon { font-size: 16px; }
.tree-empty { padding: 20px; text-align: center; font-size: 12px; color: var(--tm-text-secondary); }

.editor-panel { display: flex; flex-direction: column; overflow: hidden; }
.editor-body { flex: 1; overflow-y: auto; padding: 12px; }
.editor-empty { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 200px; color: var(--tm-text-secondary); gap: 8px; }
/* ===== 自然语言概要 Banner（Step 2 顶部） ===== */
.summary-banner { display: flex; align-items: flex-start; gap: 14px; padding: 14px 18px; margin: 0 16px 8px; border-radius: 12px; background: linear-gradient(135deg, rgba(64,158,255,0.1), rgba(64,158,255,0.04)); border: 1px solid rgba(64,158,255,0.15); }
.summary-banner-empty { background: rgba(255,255,255,0.03); border-color: var(--tm-border); }
.summary-banner-icon { font-size: 32px; line-height: 1; flex-shrink: 0; margin-top: 2px; }
.summary-banner-body { flex: 1; min-width: 0; }
.summary-banner-title { font-size: 13px; font-weight: 700; color: var(--tm-text-primary); margin-bottom: 4px; }
.summary-banner-text { font-size: 14px; line-height: 1.6; color: var(--tm-text-primary); font-weight: 500; }
.summary-banner-empty .summary-banner-text { font-size: 13px; font-weight: 400; color: var(--tm-text-secondary); }
.summary-banner-stats { display: flex; gap: 6px; flex-wrap: wrap; margin-top: 8px; }
.summary-banner-stats .el-tag { font-size: 12px; padding: 0 8px; }

/* ===== 编辑器表单 ===== */
.form-section { padding: 8px 0; }
.section-hint { font-size: 11px; color: var(--tm-text-secondary); margin-bottom: 8px; display: flex; align-items: center; gap: 4px; }
.section-hint .el-icon { font-size: 13px; flex-shrink: 0; }
.form-group { margin-bottom: 10px; }
.form-group label { display: block; font-size: 12px; font-weight: 600; margin-bottom: 3px; color: var(--tm-text-secondary); }
.form-row { display: flex; gap: 8px; }
.form-row .form-group { flex: 1; }
.kv-row { display: flex; gap: 4px; align-items: center; margin-bottom: 4px; }
.form-hint { font-size: 11px; color: #6b7280; margin-bottom: 8px; }
.form-hint code { background: rgba(255,255,255,0.06); padding: 1px 4px; border-radius: 3px; font-family: monospace; }
.assertion-teaching { padding: 10px 12px; background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.06); border-radius: 8px; margin-bottom: 8px; }
.teaching-title { font-size: 13px; font-weight: 700; color: var(--tm-color-primary); margin-bottom: 6px; }
.teaching-body { font-size: 11px; color: var(--tm-text-secondary); line-height: 1.7; }
.teaching-body p { margin: 4px 0; }
.teaching-body strong { color: var(--tm-text-primary); }
.teaching-table { width: 100%; border-collapse: collapse; margin: 6px 0; font-size: 10px; }
.teaching-table td { padding: 3px 6px; border: 1px solid rgba(255,255,255,0.06); vertical-align: top; }
.teaching-table td:first-child { color: var(--tm-text-primary); white-space: nowrap; width: 90px; font-weight: 600; }
.teaching-table code { background: rgba(255,255,255,0.06); padding: 1px 3px; border-radius: 2px; font-family: Consolas, monospace; font-size: 10px; color: #c9d1d9; }

/* ===== Step 3 布局：主区域 + 窄侧边栏 ===== */
.step3-layout { display: grid; grid-template-columns: 1fr 300px; gap: 16px; padding: 16px; height: 100%; overflow: hidden; }
.step3-main { display: flex; flex-direction: column; overflow: hidden; min-width: 0; }
.step3-sidebar { display: flex; flex-direction: column; overflow: hidden; border: 1px solid var(--tm-border); border-radius: 10px; background: var(--tm-card-bg); }
.step3-sidebar .panel-title { border-bottom: 1px solid var(--tm-border); }

.jmx-preview-compact { flex: 1; overflow-y: auto; padding: 10px; }
.xml-preview-compact { background: #0d1117; border-radius: 4px; padding: 8px; font-size: 10px; line-height: 1.4; margin: 0; overflow: auto; max-height: 400px; color: #c9d1d9; font-family: 'Consolas', monospace; white-space: pre-wrap; word-break: break-all; }
.xml-preview-compact code { font-size: 10px; }

.debug-body { flex: 1; overflow-y: auto; padding: 8px; }
.debug-content { }
.debug-meta { display: flex; gap: 12px; align-items: center; margin-bottom: 8px; padding: 8px; background: rgba(255,255,255,0.03); border-radius: 6px; }
.debug-elapsed { font-size: 13px; font-weight: 600; color: #4ADE80; }
.debug-size { font-size: 12px; color: var(--tm-text-secondary); }
.debug-json { background: #0d1117; padding: 8px; border-radius: 4px; font-size: 11px; color: #c9d1d9; font-family: 'Consolas', monospace; max-height: 200px; overflow: auto; margin: 0; }
.debug-error { margin-top: 8px; }
.empty-hint { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 200px; color: var(--tm-text-secondary); gap: 8px; font-size: 13px; text-align: center; }

/* ===== 并发验证 ===== */
.bench-body { padding: 8px; overflow-y: auto; flex: 1; }
.bench-controls { display: flex; gap: 10px; margin-bottom: 10px; }
.bench-controls .form-group { flex: 1; }
.bench-controls .form-group label { display: block; font-size: 12px; font-weight: 600; color: var(--tm-text-secondary); margin-bottom: 3px; }
.bench-controls .el-input-number { width: 100%; }
.bench-result { margin-top: 6px; }
.bench-progress { margin-bottom: 10px; text-align: center; }
.bench-progress-text { font-size: 11px; color: var(--tm-text-secondary); margin-top: 4px; display: inline-block; }
.bench-stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; margin: 6px 0; }
.bench-stat { background: rgba(255,255,255,0.04); border-radius: 8px; padding: 10px 6px; text-align: center; }
.bench-stat-value { display: block; font-size: 18px; font-weight: 700; }
.bench-stat-label { display: block; font-size: 10px; color: var(--tm-text-secondary); margin-top: 2px; }
.bench-section-title { font-size: 13px; font-weight: 700; margin: 12px 0 6px; padding-bottom: 4px; border-bottom: 1px dashed var(--tm-border); }
.bench-data-block { margin-top: 10px; }
.bench-empty-hint { display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 40px 20px; color: var(--tm-text-secondary); gap: 12px; text-align: center; font-size: 13px; }
.text-success { color: #4ADE80; }
.text-danger { color: #F87171; }
.right-tabs .el-tabs__content { overflow: visible; }
.right-tabs .el-tab-pane { height: 100%; display: flex; flex-direction: column; }
.right-tabs .el-tabs__header { margin-bottom: 4px; }

/* ===== 按接口统计（聚合报告） ===== */
.per-url-table { font-size: 12px; }
.per-url-header, .per-url-row { display: flex; gap: 6px; padding: 5px 0; border-bottom: 1px solid rgba(255,255,255,0.06); }
.per-url-header { font-weight: 700; color: var(--tm-text-secondary); font-size: 11px; }
.col-url { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.col-num { width: 56px; text-align: right; flex-shrink: 0; }

/* ===== 请求详情（查看结果树） ===== */
.sample-list { font-size: 12px; }
.sample-item { cursor: pointer; padding: 4px 0; border-bottom: 1px solid rgba(255,255,255,0.04); }
.sample-item:hover { background: rgba(255,255,255,0.03); }
.sample-summary { display: flex; align-items: center; gap: 8px; }
.sample-time { font-weight: 700; width: 60px; flex-shrink: 0; font-size: 13px; }
.sample-url { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: var(--tm-text-secondary); }
.sample-err { font-size: 10px; color: #F87171; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 150px; }
.sample-detail { padding: 8px 10px; margin-top: 4px; background: rgba(255,255,255,0.04); border-radius: 6px; font-size: 12px; line-height: 1.8; word-break: break-all; }
.sample-detail-row { margin-bottom: 2px; }
.sample-detail-label { color: var(--tm-text-secondary); font-weight: 600; }
.bench-body-preview { background: #0d1117; padding: 8px; border-radius: 4px; font-size: 11px; color: #c9d1d9; font-family: 'Consolas', monospace; max-height: 150px; overflow: auto; margin: 0; white-space: pre-wrap; word-break: break-all; }

/* ===== 面板通用 ===== */
.panel-title { display: flex; justify-content: space-between; align-items: center; padding: 10px 12px; font-weight: 600; font-size: 13px; }
.empty-state { text-align: center; padding: 30px; color: var(--tm-text-secondary); font-size: 13px; }

.step-body { flex: 1; overflow: hidden; }
</style>
