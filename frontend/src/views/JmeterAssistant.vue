<template>
  <!-- v20260528-multichart-4panel-fullscreen -->
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
        <el-button size="small" type="success" @click="downloadJmx" :disabled="!jmxContent" title="兼容 JMeter 5.1.1 / 5.2 / 5.3 / 5.4 / 5.5 / 5.6">
          <el-icon><Download /></el-icon> 下载 .jmx
        </el-button>
        <el-button size="small" @click="showScriptHistory = !showScriptHistory">
          <el-icon><FolderOpened /></el-icon> 脚本历史{{ scriptHistory.length > 0 ? '(' + scriptHistory.length + ')' : '' }}
        </el-button>
        <el-button size="small" @click="showGuide = !showGuide">
          <el-icon><QuestionFilled /></el-icon> 帮助
        </el-button>
        <el-button size="small" @click="showHelp = true">❓ 使用说明</el-button>
        <LayoutPresetDropdown size="small" @change="applyLayoutPreset" />
      </div>
    </div>

    <!-- 快速帮助面板 -->
    <el-collapse-transition>
      <div v-if="showGuide" class="guide-panel">
        <el-alert title="JMeter 压测脚本三步搞定" type="info" :closable="false" show-icon>
          <template #default>
            <p style="margin:4px 0;"><strong>第1步 · 选择接口</strong> — 从接口库导入 API（推荐），或用模板快速创建脚本</p>
            <p style="margin:4px 0;"><strong>第2步 · 配置压测参数</strong> — 设置并发线程数、循环次数、断言、提取器等</p>
            <p style="margin:4px 0;"><strong>第3步 · 导出 JMX</strong> — 生成预览并下载 .jmx 文件，兼容 JMeter 5.1.1+</p>
          </template>
        </el-alert>
      </div>
    </el-collapse-transition>

    <!-- 脚本历史面板 -->
    <ScriptHistory
      :visible="showScriptHistory"
      :script-history="scriptHistory"
      @load-script="loadScriptFromHistory"
      @create-new="createNewScript"
      @update:script-history="scriptHistory = $event"
    />

    <!-- ==================== Step 1: 选择接口 ==================== -->
    <div v-show="currentStep === 1" class="step-body">
      <div class="step1-layout">
        <!-- 左侧：模板 + 导入JMX（可拖拽调整宽度）
             拖到 < 50px 自动折叠（step1LeftCollapsed=true），浮动按钮接管展开。 -->
        <div v-show="!step1LeftCollapsed" class="step1-left" :style="{ width: step1LeftWidth + 'px', flex: 'none' }">
          <div class="panel step1-templates">
            <div class="panel-title">📦 模板快速创建</div>
            <div class="template-grid">
              <div class="tpl-card" v-for="tpl in templates" :key="tpl.key" @click="applyTemplate(tpl)">
                <div class="tpl-icon">{{ tpl.icon }}</div>
                <div class="tpl-text">
                  <div class="tpl-name">{{ tpl.name }}</div>
                  <div class="tpl-desc">{{ tpl.desc }}</div>
                </div>
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
              <el-icon size="20" style="color:var(--tm-text-secondary);"><Right /></el-icon>
            </div>
          </div>
        </div>
        <!-- 浮动按钮：step1 左侧折叠后显示在左上角 -->
        <el-button
          v-if="step1LeftCollapsed && currentStep === 1"
          class="panel-expand-fab"
          type="primary"
          plain
          :icon="ArrowRight"
          title="展开模板区"
          @click="expandStep1Left"
        />
        <!-- 拖拽分隔条：左侧模板区 ↔ 右侧导入区
             target=left 表示 size 解读为"左侧面板"宽度。
             min=0 支持完全折叠（浮动按钮接管"展开"操作）。 -->
        <BaseSplitter
          v-show="!step1LeftCollapsed"
          v-model:size="step1LeftWidth"
          target="left"
          direction="horizontal"
          :min-size="STEP1_LEFT_MIN"
          :max-size="STEP1_LEFT_MAX"
          storage-key="tm-jmeter-step1-left-width"
          container-selector=".step1-layout"
        />
        <!-- 右侧：从接口库导入 -->
        <div class="panel step1-import">
          <div class="panel-title">📋 从接口库导入</div>
          <div class="section-hint"><el-icon><InfoFilled /></el-icon> 勾选已有的 API 接口，点击「导入到脚本」自动创建 HTTP 请求和线程组</div>
          <div class="import-controls">
            <el-select v-model="importGroupFilter" placeholder="按分组筛选" size="default" clearable filterable style="width:240px;">
              <el-option v-for="g in importGroups" :key="g.id" :label="g.name" :value="g.id" />
            </el-select>
            <el-input v-model="caseSearch" placeholder="搜索接口名称或URL..." size="default" clearable prefix-icon="Search" style="flex:1;" />
          </div>
          <div class="import-case-list">
            <div v-if="allCases.length === 0" class="empty-state">
              <el-icon size="32"><FolderDelete /></el-icon>
              <p style="margin:8px 0;">当前分组没有接口用例</p>
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
            <el-button type="primary" size="large" :disabled="selectedImportCases.length === 0" @click="importSelectedCases" style="font-weight:700;">
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
        <!-- 压测控制面板 -->
        <BenchRunner
          ref="benchRunnerRef"
          :script-tree="scriptTree"
          :plan-name="scriptTree.name"
          :total-samplers="totalSamplers"
          :total-nodes="totalNodes"
          :total-threads="totalThreads"
          :all-samplers="allSamplers"
        />

        <!-- 两栏布局：树 + 编辑器 -->
        <div class="step2-editor-layout">
          <!-- 左：树（可拖拽到 0 完全折叠，浮动按钮接管展开） -->
          <TreeEditor
            v-show="!treeCollapsed"
            v-model="scriptTree"
            :selected-uid="selectedUid"
            :total-samplers="totalSamplers"
            :total-nodes="totalNodes"
            :tree-width="treeWidth"
            :clipboard-node="jmeterClipboard.node"
            @select-node="selectNode"
            @add-root-element="addRootElement"
            @add-child="addChildNode"
            @remove-node="removeNodeByUid"
            @duplicate-node="(uid) => duplicateNode(uid)"
            @cut-node="handleCutNode"
            @copy-node="handleCopyNode"
            @paste-node="handlePasteNode"
            @move-to="openMoveToDialog"
            @toggle-enabled="handleToggleEnabled"
            @move-node="handleMoveNode"
            @tree-changed="handleTreeChanged"
          />
          <BaseSplitter
            v-show="!treeCollapsed"
            v-model:size="treeWidth"
            target="left"
            direction="horizontal"
            :min-size="TREE_MIN"
            :max-size="TREE_MAX"
            storage-key="tm-jmeter-tree-width"
            container-selector=".step2-editor-layout"
          />
          <!-- 浮动按钮：tree 折叠后显示 -->
          <el-button
            v-if="treeCollapsed && currentStep === 2"
            class="panel-expand-fab"
            type="primary"
            plain
            :icon="ArrowRight"
            title="展开脚本树"
            @click="expandTree"
          />

        <!-- 中：编辑器 -->
        <div class="panel editor-panel" style="flex:1;min-width:0;">
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
                    <el-input v-model="v.name" placeholder="变量名" size="small" style="width:42%;" />
                    <el-input v-model="v.value" placeholder="值" size="small" style="width:42%;" />
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
                <div style="display:flex;gap:6px;flex-wrap:wrap;">
                  <el-button size="small" @click="addChildToCurrent('HttpSampler')">🌐 HTTP 请求</el-button>
                  <el-button size="small" @click="addChildToCurrent('ViewResultsTree')">👁️ 查看结果树</el-button>
                  <el-button size="small" @click="addChildToCurrent('SummaryReport')">📈 聚合报告</el-button>
                  <el-button size="small" @click="addChildToCurrent('AggregateReport')">📊 聚合报告(高级)</el-button>
                  <el-button size="small" @click="addChildToCurrent('ResponseTimeGraph')">📉 响应时间图</el-button>
                  <el-button size="small" @click="addChildToCurrent('CsvDataSource')">📄 CSV 数据源</el-button>
                  <el-button size="small" @click="addChildToCurrent('JDBCSampler')">🗄️ JDBC 请求</el-button>
                </div>
              </div>
              <div class="form-section">
                <div class="section-hint"><el-icon><Lollipop /></el-icon> 逻辑控制器：控制请求的执行顺序和条件</div>
                <div style="display:flex;gap:6px;flex-wrap:wrap;">
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
                <div style="display:flex;gap:6px;flex-wrap:wrap;">
                  <el-button size="small" @click="addChildToCurrent('HTTPRequestDefaults')">🎯 HTTP 请求默认值</el-button>
                  <el-button size="small" @click="addChildToCurrent('HttpHeaderManager')">📨 HTTP 信息头管理器</el-button>
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
                  <div class="form-group" style="flex:0 0 120px;"><label>方法</label>
                    <el-select v-model="selectedNode.props.method" size="small">
                      <el-option v-for="m in ['GET','POST','PUT','DELETE','PATCH']" :key="m" :label="m" :value="m" />
                    </el-select>
                  </div>
                  <div class="form-group" style="flex:1;"><label>URL</label><el-input v-model="selectedNode.props.url" size="small" placeholder="https://api.example.com/users" /></div>
                </div>
                <el-collapse>
                  <el-collapse-item title="请求头 (Headers)" name="headers">
                    <div class="section-hint" style="margin-bottom:6px;">添加请求头，如 Content-Type: application/json、Authorization: Bearer xxx</div>
                    <div v-for="(h, hi) in (selectedNode.props.headers || [])" :key="hi" class="kv-row">
                      <el-input v-model="h.key" placeholder="Header名" size="small" style="width:40%;" />
                      <el-input v-model="h.value" placeholder="值" size="small" style="width:50%;" />
                      <el-button link size="small" type="danger" @click="selectedNode.props.headers.splice(hi,1)">×</el-button>
                    </div>
                    <el-button size="small" @click="addHeader">+ 添加请求头</el-button>
                  </el-collapse-item>
                  <el-collapse-item v-if="selectedNode.props.method !== 'GET'" title="请求体 (Body)" name="body">
                    <div class="form-row">
                      <div class="form-group" style="flex:1;"><label>Body 类型</label>
                        <el-select v-model="selectedNode.props.bodyType" size="small">
                          <el-option v-for="b in ['none','json','form-data','x-www-form-urlencoded','raw']" :key="b" :label="b" :value="b" />
                        </el-select>
                      </div>
                      <div class="form-group" style="flex:1;"><label>内容编码</label>
                        <el-input v-model="selectedNode.props.contentEncoding" placeholder="UTF-8" size="small" />
                      </div>
                    </div>
                    <el-input v-if="selectedNode.props.bodyType !== 'form-data' && selectedNode.props.bodyType !== 'none'" v-model="selectedNode.props.body" type="textarea" :rows="4" size="small" placeholder='{"key":"value"}' />
                  </el-collapse-item>
                  <el-collapse-item title="Parameters (URL/表单参数)" name="params">
                    <div class="section-hint" style="margin-bottom:6px;">URL 查询参数或 x-www-form-urlencoded 表单参数(自动 URL 编码)</div>
                    <div v-for="(p, pi) in (selectedNode.props.parameters || [])" :key="pi" class="kv-row">
                      <el-input v-model="p.name" placeholder="参数名" size="small" style="width:35%;" />
                      <el-input v-model="p.value" placeholder="值" size="small" style="width:40%;" />
                      <el-checkbox v-model="p.encoded" size="small">编码</el-checkbox>
                      <el-button link size="small" type="danger" @click="selectedNode.props.parameters.splice(pi,1)">×</el-button>
                    </div>
                    <el-button size="small" @click="(selectedNode.props.parameters = selectedNode.props.parameters || []).push({name:'',value:'',encoded:false})">+ 添加参数</el-button>
                  </el-collapse-item>
                  <el-collapse-item v-if="selectedNode.props.bodyType === 'form-data'" title="文件上传" name="files">
                    <div class="section-hint" style="margin-bottom:6px;">multipart/form-data 模式下的文件列表</div>
                    <div v-for="(f, fi) in (selectedNode.props.files || [])" :key="fi" class="kv-row">
                      <el-input v-model="f.path" placeholder="文件路径(D:/test.jpg)" size="small" style="width:36%;" />
                      <el-input v-model="f.paramname" placeholder="参数名(file)" size="small" style="width:24%;" />
                      <el-input v-model="f.mimetype" placeholder="MIME(image/jpeg)" size="small" style="width:28%;" />
                      <el-button link size="small" type="danger" @click="selectedNode.props.files.splice(fi,1)">×</el-button>
                    </div>
                    <el-button size="small" @click="(selectedNode.props.files = selectedNode.props.files || []).push({path:'',paramname:'file',mimetype:''})">+ 添加文件</el-button>
                  </el-collapse-item>
                  <el-collapse-item title="代理服务器 (高级)" name="proxy">
                    <div class="section-hint" style="margin-bottom:6px;">通过代理服务器发送请求,适合抓包调试或内网代理场景</div>
                    <div class="form-row">
                      <div class="form-group" style="flex:2;"><label>代理主机</label><el-input v-model="selectedNode.props.proxyHost" placeholder="127.0.0.1" size="small" /></div>
                      <div class="form-group" style="flex:1;"><label>代理端口</label><el-input-number v-model="selectedNode.props.proxyPort" :min="1" :max="65535" size="small" /></div>
                    </div>
                    <div class="form-row">
                      <div class="form-group" style="flex:1;"><label>代理用户名</label><el-input v-model="selectedNode.props.proxyUser" placeholder="可选" size="small" /></div>
                      <div class="form-group" style="flex:1;"><label>代理密码</label><el-input v-model="selectedNode.props.proxyPass" type="password" show-password placeholder="可选" size="small" /></div>
                    </div>
                  </el-collapse-item>
                </el-collapse>
              </div>
              <div class="form-section">
                <div class="section-hint"><el-icon><Coin /></el-icon> 断言：验证返回结果是否正确（点击展开更多类型）</div>
                <div style="display:flex;gap:4px;flex-wrap:wrap;">
                  <el-button size="small" @click="addChildToCurrent('ResponseAssertion')">✅ 响应断言</el-button>
                  <el-button size="small" @click="addChildToCurrent('JSONPathAssertion')">📋 JSON断言</el-button>
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
                <div style="display:flex;gap:6px;flex-wrap:wrap;">
                  <el-button size="small" @click="addChildToCurrent('JSONExtractor')">📤 JSON 提取器</el-button>
                  <el-button size="small" @click="addChildToCurrent('RegexExtractor')">🔍 正则提取器</el-button>
                </div>
              </div>
              <div class="form-section">
                <div class="section-hint"><el-icon><Coin /></el-icon> 定时器与处理器</div>
                <div style="display:flex;gap:6px;flex-wrap:wrap;">
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
                <el-button size="small" type="warning" plain @click="aiParameterize(selectedNode)" :loading="aiParamLoading">
                  🤖 AI 参数化
                </el-button>
              </div>
            </template>

            <!-- ===== 断言编辑器（支持7种断言类型+AI辅助） ===== -->
            <template v-if="selectedNode.type === 'ResponseAssertion'">
              <div class="form-section">
                <div class="form-group"><label>断言名称</label><el-input v-model="selectedNode.name" size="small" /></div>
                <div class="form-group"><label>断言范围</label>
                  <el-radio-group v-model="selectedNode.props.scope" size="small">
                    <el-radio-button label="all">主+子样本</el-radio-button>
                    <el-radio-button label="main">仅主样本</el-radio-button>
                    <el-radio-button label="sub">仅子样本</el-radio-button>
                    <el-radio-button label="jmeter_variable">变量</el-radio-button>
                  </el-radio-group>
                  <el-input v-if="selectedNode.props.scope === 'jmeter_variable'" v-model="selectedNode.props.variable" placeholder="变量名" size="small" style="margin-top:6px;" />
                </div>
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
                <div class="form-group" v-if="selectedNode.props.assertType === 'jsonpath'"><label>JSON Path</label><el-input v-model="selectedNode.props.jsonPath" placeholder="$.data.token" size="small" /><label style="margin-top:4px;">期望值</label><el-input v-model="selectedNode.props.expected" size="small" /></div>
                <div class="form-group" v-if="selectedNode.props.assertType === 'duration'"><label>最大响应时间 (ms)</label><el-input-number v-model="selectedNode.props.maxDuration" :min="1" :max="60000" size="small" /></div>
              </div>
              <div class="form-section">
                <div class="section-hint"><el-icon><InfoFilled /></el-icon> 💡 小白提示：状态码断言最常用，只需填期望的状态码如200。响应包含用于检查返回内容中是否有特定文字</div>
              </div>
            </template>

            <template v-if="selectedNode.type === 'JSONPathAssertion'">
              <div class="form-section">
                <div class="form-group"><label>断言名称</label><el-input v-model="selectedNode.name" size="small" /></div>
                <div class="form-group"><label>断言范围</label>
                  <el-radio-group v-model="selectedNode.props.scope" size="small">
                    <el-radio-button label="all">主+子样本</el-radio-button>
                    <el-radio-button label="main">仅主样本</el-radio-button>
                    <el-radio-button label="sub">仅子样本</el-radio-button>
                    <el-radio-button label="jmeter_variable">变量</el-radio-button>
                  </el-radio-group>
                  <el-input v-if="selectedNode.props.scope === 'jmeter_variable'" v-model="selectedNode.props.variable" placeholder="变量名" size="small" style="margin-top:6px;" />
                </div>
                <div class="form-group"><label>JSON Path</label><el-input v-model="selectedNode.props.jsonPath" placeholder="$.data.token" size="small" /></div>
                <div class="form-group"><label>期望值</label><el-input v-model="selectedNode.props.expected" placeholder="12345" size="small" /></div>
                <div class="form-row">
                  <div class="form-group"><label>期望为null</label><el-switch v-model="selectedNode.props.expectNull" size="small" /></div>
                  <div class="form-group"><label>取反</label><el-switch v-model="selectedNode.props.invert" size="small" /></div>
                </div>
              </div>
              <div class="form-section">
                <div class="section-hint"><el-icon><InfoFilled /></el-icon> 💡 小白提示：用于断言JSON响应中的某个字段值。例：$.data.status 期望值 "ok"</div>
                <el-button size="small" @click="aiGenerateAssert('Json')" :loading="aiGenerating" style="margin-top:4px;">
                  🤖 AI 帮写
                </el-button>
                <span v-if="getCostText('jmeter_ai_assertions')" class="ai-cost-hint">{{ getCostText('jmeter_ai_assertions') }}</span>
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
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">
                  <label>BeanShell 脚本</label>
                  <div style="display:flex;gap:6px;">
                    <el-button size="small" type="warning" @click="aiValidateScript('BeanShell')" :loading="aiValidating" plain>🔍 AI 校验</el-button>
                    <el-button size="small" type="primary" @click="aiGenerateAssert('BeanShell')" :loading="aiGenerating" plain>
                      🤖 AI 帮写断言
                    </el-button>
                  </div>
                </div>
                <el-input v-model="selectedNode.props.script" type="textarea" :rows="8" placeholder="// 写你的断言逻辑..." size="small" style="font-family:Consolas,monospace;font-size:12px;" />
              </div>
              <div class="form-row">
                <div class="form-group"><label>外部BeanShell文件</label><el-input v-model="selectedNode.props.filename" placeholder="可选" size="small" /></div>
                <div class="form-group"><label>参数</label><el-input v-model="selectedNode.props.parameters" placeholder="可选" size="small" /></div>
              </div>
              <div class="form-group"><label>每次重置解释器</label><el-switch v-model="selectedNode.props.resetInterpreter" size="small" /></div>
              <div class="form-section" v-if="projectVariables.length > 0">
                <div class="vars-panel">
                  <div class="vars-panel-title">🔗 项目可用变量（点击插入）</div>
                  <div class="vars-chips">
                    <span v-for="v in projectVariables" :key="v.name" class="var-chip" @click="insertVariable(v.name)" :title="v.source">{{ v.name }}</span>
                  </div>
                </div>
              </div>
              <div class="form-section" v-if="aiValidationResult">
                <div class="ai-validation" :class="aiValidationResult.ok ? 'ai-validation-ok' : 'ai-validation-err'">
                  <div class="ai-validation-header">{{ aiValidationResult.ok ? '✅ 校验通过' : '⚠️ 发现问题' }}</div>
                  <div class="ai-validation-body">{{ aiValidationResult.message }}</div>
                </div>
              </div>
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
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">
                  <label>脚本代码</label>
                  <div style="display:flex;gap:6px;">
                    <el-button size="small" type="warning" @click="aiValidateScript('JSR223')" :loading="aiValidating" plain>🔍 AI 校验</el-button>
                    <el-button size="small" type="primary" @click="aiGenerateAssert('JSR223')" :loading="aiGenerating" plain>
                      🤖 AI 帮写断言
                    </el-button>
                  </div>
                </div>
                <el-input v-model="selectedNode.props.script" type="textarea" :rows="8" placeholder='// Groovy脚本...' size="small" style="font-family:Consolas,monospace;font-size:12px;" />
              </div>
              <div class="form-section" v-if="projectVariables.length > 0">
                <div class="vars-panel">
                  <div class="vars-panel-title">🔗 项目可用变量（点击插入）</div>
                  <div class="vars-chips">
                    <span v-for="v in projectVariables" :key="v.name" class="var-chip" @click="insertVariable(v.name)" :title="v.source">{{ v.name }}</span>
                  </div>
                </div>
              </div>
              <div class="form-section" v-if="aiValidationResult">
                <div class="ai-validation" :class="aiValidationResult.ok ? 'ai-validation-ok' : 'ai-validation-err'">
                  <div class="ai-validation-header">{{ aiValidationResult.ok ? '✅ 校验通过' : '⚠️ 发现问题' }}</div>
                  <div class="ai-validation-body">{{ aiValidationResult.message }}</div>
                </div>
              </div>
            </template>

            <!-- ===== 响应大小断言 ===== -->
            <template v-if="selectedNode.type === 'SizeAssertion'">
              <div class="form-section">
                <div class="form-group"><label>断言名称</label><el-input v-model="selectedNode.name" size="small" /></div>
                <div class="form-group"><label>断言范围</label>
                  <el-radio-group v-model="selectedNode.props.scope" size="small">
                    <el-radio-button label="all">主+子样本</el-radio-button>
                    <el-radio-button label="main">仅主样本</el-radio-button>
                    <el-radio-button label="sub">仅子样本</el-radio-button>
                    <el-radio-button label="jmeter_variable">变量</el-radio-button>
                  </el-radio-group>
                  <el-input v-if="selectedNode.props.scope === 'jmeter_variable'" v-model="selectedNode.props.variable" placeholder="变量名" size="small" style="margin-top:6px;" />
                </div>
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
                <div class="form-group"><label>断言范围</label>
                  <el-radio-group v-model="selectedNode.props.scope" size="small">
                    <el-radio-button label="all">主+子样本</el-radio-button>
                    <el-radio-button label="main">仅主样本</el-radio-button>
                    <el-radio-button label="sub">仅子样本</el-radio-button>
                    <el-radio-button label="jmeter_variable">变量</el-radio-button>
                  </el-radio-group>
                  <el-input v-if="selectedNode.props.scope === 'jmeter_variable'" v-model="selectedNode.props.variable" placeholder="变量名" size="small" style="margin-top:6px;" />
                </div>
                <div class="form-group"><label>XPath 表达式</label><el-input v-model="selectedNode.props.xpath" placeholder="/html/body/h1 或 //result[@status='ok']" size="small" /></div>
                <div class="form-group"><label>取反（不存在才通过）</label><el-switch v-model="selectedNode.props.negate" size="small" /></div>
              </div>
              <div class="section-hint"><el-icon><InfoFilled /></el-icon> 💡 小白提示：用于断言XML/HTML响应中某个节点存在。如 //result[@status='ok'] 表示检查是否存在status为ok的result节点</div>
            </template>

            <!-- ===== 比较断言 ===== -->
            <template v-if="selectedNode.type === 'CompareAssertion'">
              <div class="form-section">
                <div class="form-group"><label>断言名称</label><el-input v-model="selectedNode.name" size="small" /></div>
                <div class="form-group"><label>断言范围</label>
                  <el-radio-group v-model="selectedNode.props.scope" size="small">
                    <el-radio-button label="all">主+子样本</el-radio-button>
                    <el-radio-button label="main">仅主样本</el-radio-button>
                    <el-radio-button label="sub">仅子样本</el-radio-button>
                    <el-radio-button label="jmeter_variable">变量</el-radio-button>
                  </el-radio-group>
                  <el-input v-if="selectedNode.props.scope === 'jmeter_variable'" v-model="selectedNode.props.variable" placeholder="变量名" size="small" style="margin-top:6px;" />
                </div>
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
            <template v-if="selectedNode.type === 'RegexExtractor' || selectedNode.type === 'JSONExtractor'">
              <div class="form-section">
                <div class="form-group"><label>提取器名称</label><el-input v-model="selectedNode.name" size="small" /></div>
                <div class="form-group"><label>变量名</label><el-input v-model="selectedNode.props.varName" placeholder="token" size="small" /></div>
                <div class="form-hint">后续请求中用 <code>{'{'+'$'+'{'+'}'+'}变量名'}</code> 引用</div>
                <div class="form-group" v-if="selectedNode.type === 'RegexExtractor'"><label>正则表达式</label><el-input v-model="selectedNode.props.regex" placeholder='"token":"(.*?)"' size="small" /></div>
                <div class="form-group" v-if="selectedNode.type === 'JSONExtractor'"><label>JSON Path</label><el-input v-model="selectedNode.props.jsonPath" placeholder="$.data.token" size="small" /></div>
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
            <template v-if="selectedNode.type === 'SynchronizingTimer'">
              <div class="form-section">
                <div class="form-group"><label>定时器名称</label><el-input v-model="selectedNode.name" size="small" /></div>
                <div class="form-row">
                  <div class="form-group"><label>集合点并发数</label><el-input-number v-model="selectedNode.props.groupSize" :min="2" :max="10000" size="small" /></div>
                  <div class="form-group"><label>超时 (ms)</label><el-input-number v-model="selectedNode.props.timeoutInMs" :min="0" :max="600000" size="small" /></div>
                </div>
                <div class="section-hint"><el-icon><InfoFilled /></el-icon> 💡 模拟真实用户同时到达场景:集合 N 个线程后统一释放,实现"集合点"效果</div>
              </div>
            </template>
            <template v-if="selectedNode.type === 'CsvDataSource'">
              <div class="form-section">
                <div class="form-group"><label>配置名称</label><el-input v-model="selectedNode.name" size="small" /></div>
                <div class="form-group"><label>CSV 文件名</label><el-input v-model="selectedNode.props.filename" placeholder="users.csv" size="small" /></div>
                <div class="form-group"><label>变量名 (逗号分隔)</label><el-input v-model="selectedNode.props.variableNames" placeholder="username,password" size="small" /></div>
                <div class="form-row">
                  <div class="form-group"><label>分隔符</label><el-input v-model="selectedNode.props.delimiter" size="small" style="width:60px;" placeholder="," /></div>
                  <div class="form-group"><label>是否循环</label><el-switch v-model="selectedNode.props.recycle" size="small" /></div>
                </div>
                <div class="form-row">
                  <div class="form-group"><label>忽略首行</label><el-switch v-model="selectedNode.props.ignoreFirstLine" size="small" /></div>
                  <div class="form-group"><label>允许引号</label><el-switch v-model="selectedNode.props.quotedData" size="small" /></div>
                  <div class="form-group"><label>遇 EOF 停线程</label><el-switch v-model="selectedNode.props.stopThread" size="small" /></div>
                </div>
                <div class="form-group"><label>共享模式</label>
                  <el-select v-model="selectedNode.props.shareMode" size="small">
                    <el-option label="所有线程共享" value="shareMode.all" />
                    <el-option label="线程组共享" value="shareMode.group" />
                    <el-option label="每线程独立" value="shareMode.thread" />
                  </el-select>
                </div>
                <div class="form-group"><label>CSV 内容 (随 .jmx 导出)</label><el-input v-model="selectedNode.props.csvContent" type="textarea" :rows="4" placeholder="username,password&#10;user1,pass1" size="small" /></div>
              </div>
              <div class="section-hint"><el-icon><InfoFilled /></el-icon> 💡 小白提示:CSV 数据文件用于参数化测试,每行数据轮流给每个虚拟用户使用。建议把 CSV 文件放在脚本同目录</div>
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
              </div>
              <div class="section-hint assertion-teaching">
                <div class="teaching-title">📖 BeanShell {{ selectedNode.type === 'BeanShellPreProcessor' ? '前置' : '后置' }}处理器教学</div>
                <div class="teaching-body">
                  <p><strong>{{ selectedNode.type === 'BeanShellPreProcessor' ? '前置处理器' : '后置处理器' }}是什么？</strong> {{ selectedNode.type === 'BeanShellPreProcessor' ? '在请求发送前执行，用于修改请求参数、添加签名等' : '在请求返回后执行，用于提取数据、修改变量等' }}</p>
                  <p><strong>📌 核心变量速查：</strong></p>
                  <table class="teaching-table">
                    <tr><td><code>vars</code></td><td>JMeter变量字典，vars.put("k","v") 存 / vars.get("k") 取</td></tr>
                    <tr><td><code>prev</code></td><td>上一个采样结果（后置可用），prev.getResponseDataAsString()</td></tr>
                    <tr><td><code>log</code></td><td>日志对象，log.info("xxx") 打印日志</td></tr>
                    <tr><td><code>ctx</code></td><td>JMeter上下文，ctx.getCurrentSampler() 获取当前采样器</td></tr>
                    <tr v-if="selectedNode.type === 'BeanShellPostProcessor'"><td><code>ResponseData</code></td><td>响应体字节数组，new String(ResponseData) 转字符串</td></tr>
                    <tr v-if="selectedNode.type === 'BeanShellPostProcessor'"><td><code>ResponseCode</code></td><td>HTTP状态码，如 "200"</td></tr>
                  </table>
                </div>
              </div>
              <div class="form-section">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">
                  <label>BeanShell 脚本</label>
                  <div style="display:flex;gap:6px;">
                    <el-button size="small" type="warning" @click="aiValidateScript('BeanShell')" :loading="aiValidating" plain>🔍 AI 校验</el-button>
                    <el-button size="small" type="primary" @click="aiGenerateScript('BeanShellProcessor')" :loading="aiGenerating" plain>🤖 AI 帮写</el-button>
                  </div>
                </div>
                <el-input v-model="selectedNode.props.script" type="textarea" :rows="8" placeholder='long ts = System.currentTimeMillis(); vars.put("ts",String.valueOf(ts));' size="small" style="font-family:Consolas,monospace;font-size:12px;" />
              </div>
              <div class="form-section" v-if="projectVariables.length > 0">
                <div class="vars-panel">
                  <div class="vars-panel-title">🔗 项目可用变量（点击插入）</div>
                  <div class="vars-chips">
                    <span v-for="v in projectVariables" :key="v.name" class="var-chip" @click="insertVariable(v.name)" :title="v.source">{{ v.name }}</span>
                  </div>
                </div>
              </div>
              <div class="form-section" v-if="aiValidationResult">
                <div class="ai-validation" :class="aiValidationResult.ok ? 'ai-validation-ok' : 'ai-validation-err'">
                  <div class="ai-validation-header">{{ aiValidationResult.ok ? '✅ 校验通过' : '⚠️ 发现问题' }}</div>
                  <div class="ai-validation-body">{{ aiValidationResult.message }}</div>
                </div>
              </div>
            </template>
            <template v-if="selectedNode.type === 'JSR223PreProcessor' || selectedNode.type === 'JSR223PostProcessor'">
              <div class="form-section">
                <div class="form-group"><label>脚本名称</label><el-input v-model="selectedNode.name" size="small" /></div>
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
                <div class="teaching-title">📖 JSR223 {{ selectedNode.type === 'JSR223PreProcessor' ? '前置' : '后置' }}处理器教学</div>
                <div class="teaching-body">
                  <p><strong>推荐用 Groovy</strong>，比 BeanShell 快 10 倍。核心变量：</p>
                  <table class="teaching-table">
                    <tr><td><code>vars</code></td><td>JMeter变量字典，vars.put("k","v") / vars.get("k")</td></tr>
                    <tr><td><code>prev</code></td><td>SampleResult，可调用 getResponseDataAsString()、getTime()</td></tr>
                    <tr><td><code>log</code></td><td>日志对象，log.info("xxx")</td></tr>
                    <tr><td><code>ctx</code></td><td>JMeter上下文</td></tr>
                    <tr><td><code>out</code></td><td>System.out，调试用</td></tr>
                  </table>
                </div>
              </div>
              <div class="form-section">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">
                  <label>脚本代码</label>
                  <div style="display:flex;gap:6px;">
                    <el-button size="small" type="warning" @click="aiValidateScript('JSR223')" :loading="aiValidating" plain>🔍 AI 校验</el-button>
                    <el-button size="small" type="primary" @click="aiGenerateScript('JSR223Processor')" :loading="aiGenerating" plain>🤖 AI 帮写</el-button>
                  </div>
                </div>
                <el-input v-model="selectedNode.props.script" type="textarea" :rows="8" placeholder='def ts = System.currentTimeMillis(); vars.put("ts", ts.toString())' size="small" style="font-family:Consolas,monospace;font-size:12px;" />
              </div>
              <div class="form-section" v-if="projectVariables.length > 0">
                <div class="vars-panel">
                  <div class="vars-panel-title">🔗 项目可用变量（点击插入）</div>
                  <div class="vars-chips">
                    <span v-for="v in projectVariables" :key="v.name" class="var-chip" @click="insertVariable(v.name)" :title="v.source">{{ v.name }}</span>
                  </div>
                </div>
              </div>
              <div class="form-section" v-if="aiValidationResult">
                <div class="ai-validation" :class="aiValidationResult.ok ? 'ai-validation-ok' : 'ai-validation-err'">
                  <div class="ai-validation-header">{{ aiValidationResult.ok ? '✅ 校验通过' : '⚠️ 发现问题' }}</div>
                  <div class="ai-validation-body">{{ aiValidationResult.message }}</div>
                </div>
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
                  <div style="display:flex;gap:4px;flex-wrap:wrap;">
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
                  <div style="display:flex;gap:4px;flex-wrap:wrap;">
                    <el-button size="small" @click="addChildToCurrent('HttpSampler')">🌐 HTTP 请求</el-button>
                  </div>
                </div>
              </div>
            </template>
            <template v-if="selectedNode.type === 'HttpHeaderManager'">
              <div class="form-section">
                <div class="section-hint"><el-icon><InfoFilled /></el-icon> 为所有 HTTP 请求统一添加请求头，自动继承到子元素</div>
                <div class="form-group"><label>管理器名称</label><el-input v-model="selectedNode.name" size="small" /></div>
                <div class="form-group"><label>请求头</label>
                  <div v-for="(h, hi) in (selectedNode.props.headers || [])" :key="hi" class="kv-row">
                    <el-input v-model="h.key" placeholder="Header名" size="small" style="width:40%;" />
                    <el-input v-model="h.value" placeholder="值" size="small" style="width:50%;" />
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
            <template v-if="selectedNode.type === 'ViewResultsTree'">
              <div class="form-section">
                <div class="form-group"><label>监听器名称</label><el-input v-model="selectedNode.name" size="small" /></div>
              </div>
              <div v-if="benchResult && benchResult.samples && benchResult.samples.length > 0" class="form-section vrt-inline-section">
                <div class="section-hint" style="margin-bottom:8px;"><el-icon><InfoFilled /></el-icon> 以下是最近一次运行的结果数据</div>
                <div class="vrt-container">
                  <div class="vrt-left-col">
                    <div class="vrt-toolbar">
                      <span class="vrt-toolbar-label">查找:</span>
                      <el-input v-model="sampleSearchQuery" size="small" clearable style="width:150px;" @keyup.enter="doVrtSearch" />
                      <el-checkbox v-model="searchCaseSensitive" size="small">区分大小写</el-checkbox>
                      <el-checkbox v-model="searchRegex" size="small">正则表达式</el-checkbox>
                      <el-button size="small" type="primary" plain @click="doVrtSearch">查找</el-button>
                      <el-button size="small" @click="resetVrtSearch">重置</el-button>
                      <el-select v-model="sampleStatusFilter" size="small" clearable placeholder="全部" style="width:85px;margin-left:auto;">
                        <el-option label="成功" value="success" />
                        <el-option label="失败" value="error" />
                        <el-option label="异常" value="exception" />
                      </el-select>
                    </div>
                    <div class="vrt-sample-list">
                      <div v-for="(s, si) in filteredSamples" :key="si"
                        class="vrt-sample-item" :class="{ active: selectedSampleIdx === si }" @click="selectSample(si)">
                        <el-tag :type="s.status >= 200 && s.status < 400 ? 'success' : s.status === 0 ? 'danger' : 'warning'" size="small">{{ s.status || 'ERR' }}</el-tag>
                        <span class="vrt-time">{{ s.elapsed_ms }}ms</span>
                        <span class="vrt-name" :title="s.name || s.url">{{ s.name || shortUrl(s.url) }}</span>
                        <span v-if="s.error" class="vrt-err" title="有错误">⚠</span>
                      </div>
                      <div v-if="filteredSamples.length === 0" style="padding:12px;text-align:center;color:var(--tm-text-secondary);font-size:12px;">无匹配结果</div>
                    </div>
                  </div>
                  <div v-if="selectedSample" class="vrt-detail-panel">
                    <el-tabs v-model="selectedSampleTab" size="small" class="vrt-tabs">
                      <el-tab-pane label="采样器结果" name="sampler">
                        <table class="vrt-table">
                          <tr><td class="vrt-label">Thread Name</td><td>{{ selectedSample.thread_name || '线程组 1-' + (selectedSampleIdx + 1) }}</td></tr>
                          <tr><td class="vrt-label">Sample Start</td><td>{{ selectedSample.start_time || '-' }}</td></tr>
                          <tr><td class="vrt-label">Load time</td><td><b>{{ selectedSample.elapsed_ms || 0 }}</b> ms</td></tr>
                          <tr><td class="vrt-label">Connect Time</td><td>{{ selectedSample.connect_time_ms ?? '-' }} ms</td></tr>
                          <tr><td class="vrt-label">Latency</td><td>{{ (selectedSample.latency_ms ?? selectedSample.elapsed_ms) }} ms</td></tr>
                          <tr><td class="vrt-label">Size in bytes</td><td>{{ selectedSample.body_size || 0 }}</td></tr>
                          <tr><td class="vrt-label">Sent bytes</td><td>{{ selectedSample.sent_bytes || 0 }}</td></tr>
                          <tr><td class="vrt-label">Headers size in bytes</td><td>{{ selectedSample.headers_size || 0 }}</td></tr>
                          <tr><td class="vrt-label">Error Count</td><td :style="{ color: selectedSample.error ? 'var(--el-color-danger)' : 'var(--el-color-success)' }">{{ selectedSample.error ? '1' : '0' }}</td></tr>
                          <tr><td class="vrt-label">Data type</td><td>{{ selectedSample.data_type || 'text' }}</td></tr>
                          <tr><td class="vrt-label">Response code</td><td><el-tag :type="selectedSample.status >= 200 && selectedSample.status < 400 ? 'success' : 'danger'" size="small">{{ selectedSample.status || 'ERR' }}</el-tag></td></tr>
                          <tr><td class="vrt-label">Response message</td><td>{{ selectedSample.response_message || (selectedSample.status >= 200 && selectedSample.status < 400 ? 'OK' : 'Error') }}</td></tr>
                        </table>
                      </el-tab-pane>
                      <el-tab-pane label="请求" name="request">
                        <div v-if="selectedSample.method || selectedSample.url" class="vrt-http-line">
                          <code>{{ selectedSample.method || '?' }} {{ selectedSample.url || '' }}</code>
                        </div>
                        <el-tabs v-model="selectedRequestTab" size="small" class="vrt-inner-tabs">
                          <el-tab-pane label="Request Body" name="rbody">
                            <pre class="vrt-code">{{ selectedSample.request_body || '(无请求体)' }}</pre>
                          </el-tab-pane>
                          <el-tab-pane label="Request Headers" name="rheaders">
                            <pre class="vrt-code"><template v-if="selectedSample.request_headers">{{ formatHeaders(selectedSample.request_headers) }}</template><template v-else>(无请求头信息)</template></pre>
                          </el-tab-pane>
                        </el-tabs>
                      </el-tab-pane>
                      <el-tab-pane label="响应数据" name="response">
                        <el-tabs v-model="selectedResponseTab" size="small" class="vrt-inner-tabs">
                          <el-tab-pane label="Response Body" name="resbody">
                            <pre class="vrt-code" :class="{ 'vrt-error-body': selectedSample.error }">{{ selectedSample.response_body || selectedSample.error || '(空响应)' }}</pre>
                          </el-tab-pane>
                          <el-tab-pane label="Response Headers" name="resheaders">
                            <pre class="vrt-code"><template v-if="selectedSample.response_headers">{{ formatHeaders(selectedSample.response_headers) }}</template><template v-else>(无响应头信息)</template></pre>
                          </el-tab-pane>
                        </el-tabs>
                      </el-tab-pane>
                    </el-tabs>
                  </div>
                  <div v-else class="vrt-empty-detail">👆 点击上方样本查看详情</div>
                </div>
              </div>
              <div v-else class="form-section">
                <div class="empty-state" style="padding:24px 0;">尚未运行测试<br/><small style="color:var(--tm-text-secondary);">点击上方「启动」运行测试后，结果将在此处显示</small></div>
              </div>
            </template>
            <template v-if="selectedNode.type === 'SummaryReport' || selectedNode.type === 'AggregateGraph' || selectedNode.type === 'AggregateReport' || selectedNode.type === 'ResponseTimeGraph'">
              <div class="form-section">
                <div class="form-group"><label>监听器名称</label><el-input v-model="selectedNode.name" size="small" /></div>
                <div v-if="benchResult && benchResult.per_url && benchResult.per_url.length > 0" style="margin-top:12px;">
                  <div class="section-hint" style="margin-bottom:8px;"><el-icon><InfoFilled /></el-icon> 以下是最近一次运行的聚合数据</div>
                  <table class="per-url-table theme-table">
                    <thead><tr><th>URL</th><th>次数</th><th>成功</th><th>失败</th><th>平均(ms)</th><th>P95(ms)</th></tr></thead>
                    <tbody><tr v-for="pu in benchResult.per_url" :key="pu.url"><td class="col-url" :title="pu.url">{{ pu.url }}</td><td class="col-num">{{ pu.count }}</td><td class="col-num text-success">{{ pu.success }}</td><td class="col-num" :class="pu.failed > 0 ? 'text-danger' : 'text-success'">{{ pu.failed }}</td><td class="col-num">{{ pu.avg_ms }}</td><td class="col-num">{{ pu.p95_ms }}</td></tr></tbody>
                  </table>
                </div>
                <div v-else class="empty-state" style="padding:24px 0;">尚未运行测试<br/><small style="color:var(--tm-text-secondary);">运行测试后，聚合数据将在此处显示</small></div>
              </div>
            </template>

            <template v-if="selectedNode.type === 'InfluxDBBackendListener'">
              <div class="form-section">
                <div class="section-hint"><el-icon><InfoFilled /></el-icon> 将 JMeter 测试指标实时推送到 InfluxDB 时序数据库，配合 Grafana 做可视化监控大屏。真实压测必备！</div>
                <div class="form-group"><label>监听器名称</label><el-input v-model="selectedNode.name" size="small" /></div>
                <div class="form-group"><label>InfluxDB URL</label><el-input v-model="selectedNode.props.influxdbUrl" placeholder="http://localhost:8086/write?db=jmeter" size="small" /></div>
                <div class="form-row">
                  <div class="form-group"><label>应用名</label><el-input v-model="selectedNode.props.application" placeholder="test" size="small" /></div>
                  <div class="form-group"><label>测量名称</label><el-input v-model="selectedNode.props.measurement" placeholder="jmeter" size="small" /></div>
                </div>
                <div class="form-row">
                  <div class="form-group"><label>仅汇总结果</label><el-switch v-model="selectedNode.props.summaryOnly" size="small" /></div>
                  <div class="form-group"><label>采样器正则过滤</label><el-input v-model="selectedNode.props.samplersRegex" placeholder="留空=全部" size="small" /></div>
                </div>
                <div class="form-row">
                  <div class="form-group"><label>百分位(分号分隔)</label><el-input v-model="selectedNode.props.percentiles" placeholder="50;90;95;99" size="small" /></div>
                  <div class="form-group"><label>测试标题</label><el-input v-model="selectedNode.props.testTitle" placeholder="" size="small" /></div>
                </div>
                <div class="form-group"><label>事件标签</label><el-input v-model="selectedNode.props.eventTags" placeholder="TAG_Random=${__Random(0,999999999)}" size="small" /></div>
              </div>
            </template>

            <template v-if="selectedNode.type === 'UserParameters'">
              <div class="form-section">
                <div class="section-hint"><el-icon><InfoFilled /></el-icon> 真实场景：多账号并发测试。每个线程使用不同的用户凭证，模拟真实多用户访问。比 CSV 数据源更直观地管理账号</div>
                <div class="form-group"><label>参数名称（每行一个）</label>
                  <div style="display:flex;flex-direction:column;gap:4px;">
                    <div v-for="(name, ni) in selectedNode.props.names" :key="ni" style="display:flex;gap:4px;">
                      <el-input v-model="selectedNode.props.names[ni]" placeholder="如 sid, password" size="small" />
                      <el-button link size="small" type="danger" @click="selectedNode.props.names.splice(ni,1); selectedNode.props.users.forEach(u=>u.splice(ni,1))">×</el-button>
                    </div>
                    <el-button size="small" @click="selectedNode.props.names.push(''); selectedNode.props.users.forEach(u=>u.push(''))">+ 添加参数列</el-button>
                  </div>
                </div>
                <div class="form-group"><label>用户数据（每行一个用户）</label>
                  <div style="max-height:200px;overflow-y:auto;border: 1px solid var(--tm-border-light);border-radius:8px;padding:8px;background: var(--bg-surface);">
                    <table style="width:100%;font-size:11.5px;border-collapse:collapse;">
                      <tr style="background: rgba(var(--tm-color-primary-rgb), 0.06);">
                        <th style="padding:3px 6px;text-align:left;font-size:10px;color: var(--tm-color-primary);">用户#</th>
                        <th v-for="(n, ni) in selectedNode.props.names" :key="'h'+ni" style="padding:3px 6px;text-align:left;font-size:10px;color: var(--tm-color-primary);">{{ n || '参数'+(ni+1) }}</th>
                      </tr>
                      <tr v-for="(user, ui) in selectedNode.props.users" :key="ui" style="border-top: 1px solid var(--tm-border-light);">
                        <td style="padding:3px 6px;font-weight:700;color:var(--tm-text-secondary);font-size:10px;">{{ ui+1 }}</td>
                        <td v-for="(val, vi) in user" :key="vi" style="padding:2px;">
                          <el-input v-model="selectedNode.props.users[ui][vi]" size="small" style="width:100%;" />
                        </td>
                        <td style="padding:2px;">
                          <el-button link size="small" type="danger" @click="selectedNode.props.users.splice(ui,1)" style="font-size:11px;">×</el-button>
                        </td>
                      </tr>
                    </table>
                    <el-button size="small" @click="selectedNode.props.users.push(selectedNode.props.names.map(()=>''))" style="margin-top:6px;width:100%;">+ 添加用户</el-button>
                    <el-button size="small" @click="selectedNode.props.users = []" type="danger" plain style="margin-top:4px;width:100%;">清空全部</el-button>
                  </div>
                </div>
                <div class="form-group"><label>每次迭代取下一个</label><el-switch v-model="selectedNode.props.perIteration" size="small" /></div>
              </div>
            </template>

            <template v-if="selectedNode.type === 'DebugSampler'">
              <div class="form-section">
                <div class="form-group"><label>采样器名称</label><el-input v-model="selectedNode.name" size="small" /></div>
              </div>
              <div class="section-hint"><el-icon><InfoFilled /></el-icon> 调试神器！运行时输出所有 JMeter 变量值到「查看结果树」中。排查变量是否正确设置时必用</div>
            </template>

            <template v-if="selectedNode.type === 'ForEachController'">
              <div class="form-section">
                <div class="section-hint"><el-icon><InfoFilled /></el-icon> 遍历一组变量。如变量前缀为 item_ 则遍历 item_1, item_2, item_3... 常用于批量处理提取的数据</div>
                <div class="form-group"><label>控制器名称</label><el-input v-model="selectedNode.name" size="small" /></div>
                <div class="form-group"><label>输入变量前缀</label><el-input v-model="selectedNode.props.inputVar" placeholder="item_" size="small" /><span class="form-hint">会遍历 item_1, item_2, ...</span></div>
                <div class="form-group"><label>输出变量名</label><el-input v-model="selectedNode.props.outputVar" placeholder="currentItem" size="small" /><span class="form-hint">循环体内用 ${currentItem} 引用当前值</span></div>
                <div class="form-row">
                  <div class="form-group"><label>使用分隔符 "_"</label><el-switch v-model="selectedNode.props.useSeparator" size="small" /></div>
                  <div class="form-group"><label>分隔符</label><el-input v-model="selectedNode.props.separator" placeholder="_" size="small" style="width:60px;" /></div>
                </div>
              </div>
            </template>

            <template v-if="selectedNode.type === 'SwitchController'">
              <div class="form-section">
                <div class="section-hint"><el-icon><InfoFilled /></el-icon> 根据表达式值选择执行哪个子元素。类似 Java switch-case，支持默认分支</div>
                <div class="form-group"><label>控制器名称</label><el-input v-model="selectedNode.name" size="small" /></div>
                <div class="form-group"><label>Switch 值（表达式或数字）</label><el-input v-model="selectedNode.props.switchValue" placeholder="${status}" size="small" /></div>
                <div class="form-group"><label>添加子元素</label>
                  <div style="display:flex;gap:4px;flex-wrap:wrap;">
                    <el-button size="small" @click="addChildToCurrent('HttpSampler')">🌐 HTTP 请求</el-button>
                    <el-button size="small" @click="addChildToCurrent('IfController')">🔀 如果控制器</el-button>
                  </div>
                </div>
              </div>
            </template>

            <template v-if="selectedNode.type === 'RandomController' || selectedNode.type === 'InterleaveController'">
              <div class="form-section">
                <div class="section-hint"><el-icon><InfoFilled /></el-icon> {{ selectedNode.type === 'RandomController' ? '每次随机选择一个子元素执行，模拟用户随机行为' : '按顺序轮换子元素执行，每个子元素轮流被选中一次' }}</div>
                <div class="form-group"><label>控制器名称</label><el-input v-model="selectedNode.name" size="small" /></div>
                <div class="form-group"><label>添加子元素</label>
                  <div style="display:flex;gap:4px;flex-wrap:wrap;">
                    <el-button size="small" @click="addChildToCurrent('HttpSampler')">🌐 HTTP 请求</el-button>
                    <el-button size="small" @click="addChildToCurrent('IfController')">🔀 如果控制器</el-button>
                  </div>
                </div>
              </div>
            </template>

            <template v-if="selectedNode.type === 'IncludeController'">
              <div class="form-section">
                <div class="section-hint"><el-icon><InfoFilled /></el-icon> 引入外部 .jmx 文件片段，实现模块化脚本复用。适合把公共逻辑（登录、公共请求头等）抽取为独立文件</div>
                <div class="form-group"><label>控制器名称</label><el-input v-model="selectedNode.name" size="small" /></div>
                <div class="form-group"><label>.jmx 文件路径</label><el-input v-model="selectedNode.props.includePath" placeholder="common/login.jmx" size="small" /></div>
              </div>
            </template>

            <!-- ===== 边界提取器 ===== -->
            <template v-if="selectedNode.type === 'BoundaryExtractor'">
              <div class="form-section">
                <div class="section-hint"><el-icon><InfoFilled /></el-icon> 通过左右边界字符提取内容,适合非结构化响应(HTML/纯文本),比正则更快更简单</div>
                <div class="form-group"><label>提取器名称</label><el-input v-model="selectedNode.name" size="small" /></div>
                <div class="form-group"><label>变量名 (引用名)</label><el-input v-model="selectedNode.props.referenceName" placeholder="token" size="small" /></div>
                <div class="form-group"><label>左边界</label><el-input v-model="selectedNode.props.leftBoundary" placeholder='&lt;token&gt;' size="small" /></div>
                <div class="form-group"><label>右边界</label><el-input v-model="selectedNode.props.rightBoundary" placeholder='&lt;/token&gt;' size="small" /></div>
                <div class="form-row">
                  <div class="form-group"><label>匹配序号</label><el-input-number v-model="selectedNode.props.matchNumber" :min="-1" :max="9999" size="small" /></div>
                  <div class="form-group"><label>默认值</label><el-input v-model="selectedNode.props.defaultValue" placeholder="NOT_FOUND" size="small" /></div>
                </div>
                <div class="form-hint">匹配序号: 0=随机, 1=第一个, -1=全部(逗号分隔)</div>
              </div>
            </template>

            <!-- ===== CSS 选择器提取器 ===== -->
            <template v-if="selectedNode.type === 'CSSSelectorExtractor'">
              <div class="form-section">
                <div class="section-hint"><el-icon><InfoFilled /></el-icon> 通过 CSS 选择器从 HTML 响应中提取数据,适合网页爬虫场景</div>
                <div class="form-group"><label>提取器名称</label><el-input v-model="selectedNode.name" size="small" /></div>
                <div class="form-group"><label>变量名</label><el-input v-model="selectedNode.props.referenceName" placeholder="title" size="small" /></div>
                <div class="form-group"><label>CSS 选择器</label><el-input v-model="selectedNode.props.selector" placeholder="h1.title" size="small" /></div>
                <div class="form-group"><label>属性 (空=取文本)</label><el-input v-model="selectedNode.props.attribute" placeholder="href 或留空" size="small" /></div>
                <div class="form-row">
                  <div class="form-group"><label>匹配序号</label><el-input-number v-model="selectedNode.props.matchNumber" :min="-1" :max="9999" size="small" /></div>
                  <div class="form-group"><label>默认值</label><el-input v-model="selectedNode.props.defaultValue" placeholder="NOT_FOUND" size="small" /></div>
                </div>
              </div>
            </template>

            <!-- ===== XPath 提取器 ===== -->
            <template v-if="selectedNode.type === 'XPathExtractor'">
              <div class="form-section">
                <div class="section-hint"><el-icon><InfoFilled /></el-icon> 通过 XPath 从 XML/HTML 响应中提取数据,适合 Web Service 接口</div>
                <div class="form-group"><label>提取器名称</label><el-input v-model="selectedNode.name" size="small" /></div>
                <div class="form-group"><label>变量名</label><el-input v-model="selectedNode.props.referenceName" placeholder="userId" size="small" /></div>
                <div class="form-group"><label>XPath 表达式</label><el-input v-model="selectedNode.props.xPath" placeholder="//user/@id" size="small" /></div>
                <div class="form-row">
                  <div class="form-group"><label>匹配序号</label><el-input-number v-model="selectedNode.props.matchNumber" :min="-1" :max="9999" size="small" /></div>
                  <div class="form-group"><label>默认值</label><el-input v-model="selectedNode.props.defaultValue" placeholder="NOT_FOUND" size="small" /></div>
                </div>
              </div>
            </template>

            <!-- ===== 恒定吞吐量定时器 ===== -->
            <template v-if="selectedNode.type === 'ConstantThroughputTimer'">
              <div class="form-section">
                <div class="section-hint"><el-icon><InfoFilled /></el-icon> 控制测试吞吐量恒定(每分钟采样数),适合 SLA 验证场景</div>
                <div class="form-group"><label>定时器名称</label><el-input v-model="selectedNode.name" size="small" /></div>
                <div class="form-row">
                  <div class="form-group"><label>吞吐量 (每分钟)</label><el-input-number v-model="selectedNode.props.throughput" :min="1" :max="600000" size="small" /></div>
                  <div class="form-group"><label>计算模式</label>
                    <el-select v-model="selectedNode.props.calcMode" size="small">
                      <el-option label="每线程" value="1" />
                      <el-option label="所有线程(活跃)" value="2" />
                      <el-option label="所有线程(全部)" value="3" />
                    </el-select>
                  </div>
                </div>
              </div>
            </template>

            <!-- ===== 泊松随机定时器 ===== -->
            <template v-if="selectedNode.type === 'PoissonRandomTimer'">
              <div class="form-section">
                <div class="section-hint"><el-icon><InfoFilled /></el-icon> 基于泊松分布的随机延迟,模拟真实用户操作间隔(更接近自然行为)</div>
                <div class="form-group"><label>定时器名称</label><el-input v-model="selectedNode.name" size="small" /></div>
                <div class="form-row">
                  <div class="form-group"><label>固定延迟 (ms)</label><el-input-number v-model="selectedNode.props.delay" :min="0" :max="60000" size="small" /></div>
                  <div class="form-group"><label>随机范围 (ms)</label><el-input-number v-model="selectedNode.props.range" :min="0" :max="60000" size="small" /></div>
                </div>
                <div class="form-group"><label>随机因子</label><el-input-number v-model="selectedNode.props.factor" :min="0.1" :max="10" :step="0.1" size="small" /></div>
              </div>
            </template>

            <!-- ===== HTTP 缓存管理器 ===== -->
            <template v-if="selectedNode.type === 'HttpCacheManager'">
              <div class="form-section">
                <div class="section-hint"><el-icon><InfoFilled /></el-icon> 模拟浏览器缓存行为,自动处理 ETag/Last-Modified 等缓存控制头</div>
                <div class="form-group"><label>管理器名称</label><el-input v-model="selectedNode.name" size="small" /></div>
                <div class="form-row">
                  <div class="form-group"><label>每次循环清空缓存</label><el-switch v-model="selectedNode.props.clearEachIteration" size="small" /></div>
                  <div class="form-group"><label>使用 Expires 头</label><el-switch v-model="selectedNode.props.useExpires" size="small" /></div>
                </div>
                <div class="form-group"><label>最大缓存条目数</label><el-input-number v-model="selectedNode.props.maxSize" :min="0" :max="10000" size="small" /></div>
              </div>
            </template>

            <!-- ===== HTTP 授权管理器 ===== -->
            <template v-if="selectedNode.type === 'HttpAuthManager'">
              <div class="form-section">
                <div class="section-hint"><el-icon><InfoFilled /></el-icon> 自动为匹配 URL 的请求添加 Basic/Digest 认证头,适合测试受保护接口</div>
                <div class="form-group"><label>管理器名称</label><el-input v-model="selectedNode.name" size="small" /></div>
                <div class="form-group"><label>授权用户列表</label>
                  <div v-for="(u, ui) in (selectedNode.props.users || [])" :key="ui" class="kv-row">
                    <el-input v-model="u.name" placeholder="用户名" size="small" style="width:22%;" />
                    <el-input v-model="u.user" placeholder="账号" size="small" style="width:22%;" />
                    <el-input v-model="u.pass" type="password" show-password placeholder="密码" size="small" style="width:22%;" />
                    <el-input v-model="u.url" placeholder="URL(前缀,如 http://api.com)" size="small" style="width:26%;" />
                    <el-button link size="small" type="danger" @click="selectedNode.props.users.splice(ui,1)">×</el-button>
                  </div>
                  <el-button size="small" @click="(selectedNode.props.users = selectedNode.props.users || []).push({name:'',user:'',pass:'',url:''})">+ 添加授权</el-button>
                </div>
              </div>
            </template>

            <!-- ===== 模块控制器 ===== -->
            <template v-if="selectedNode.type === 'ModuleController'">
              <div class="form-section">
                <div class="section-hint"><el-icon><InfoFilled /></el-icon> 引用并执行另一个控制器模块,实现测试片段复用(类似 IncludeController,但调用当前测试计划内的片段)</div>
                <div class="form-group"><label>控制器名称</label><el-input v-model="selectedNode.name" size="small" /></div>
                <div class="form-group"><label>目标模块路径</label>
                  <el-input v-model="selectedNode.props.nodePath" placeholder="Test Plan / 登录线程组 / 登录请求" size="small" />
                  <div class="form-hint">输入要调用的控制器在树中的路径,用 / 分隔</div>
                </div>
              </div>
            </template>

            <!-- ===== 运行时控制器 ===== -->
            <template v-if="selectedNode.type === 'RunTimeController'">
              <div class="form-section">
                <div class="section-hint"><el-icon><InfoFilled /></el-icon> 在指定秒数内循环执行子元素,时间到自动停止(与 LoopController 的次数控制不同,这里是按时间)</div>
                <div class="form-group"><label>控制器名称</label><el-input v-model="selectedNode.name" size="small" /></div>
                <div class="form-group"><label>运行时长 (秒)</label><el-input-number v-model="selectedNode.props.runtime" :min="1" :max="86400" size="small" /></div>
                <div class="form-hint">子元素将在设定的秒数内重复执行,模拟"持续 N 秒"的并发场景</div>
              </div>
            </template>

            <!-- ===== 汇总器 (Summariser) ===== -->
            <template v-if="selectedNode.type === 'Summariser'">
              <div class="form-section">
                <div class="section-hint"><el-icon><InfoFilled /></el-icon> 周期性输出汇总信息到控制台/日志,便于运行时监控测试进度(无需打开 HTML 报告)</div>
                <div class="form-group"><label>汇总器名称</label><el-input v-model="selectedNode.name" size="small" /></div>
                <div class="form-row">
                  <div class="form-group"><label>汇总间隔 (秒)</label><el-input-number v-model="selectedNode.props.interval" :min="1" :max="3600" size="small" /></div>
                  <div class="form-group"><label>忽略事务控制器</label><el-switch v-model="selectedNode.props.ignoreTCGA" size="small" /></div>
                </div>
              </div>
            </template>

            <!-- ===== 随机变量配置 ===== -->
            <template v-if="selectedNode.type === 'RandomVariableConfig'">
              <div class="form-section">
                <div class="section-hint"><el-icon><InfoFilled /></el-icon> 生成随机数并写入变量,用于模拟随机用户ID、订单号等场景</div>
                <div class="form-group"><label>配置名称</label><el-input v-model="selectedNode.name" size="small" /></div>
                <div class="form-group"><label>变量名</label><el-input v-model="selectedNode.props.variableName" placeholder="userId" size="small" /></div>
                <div class="form-row">
                  <div class="form-group"><label>最小值</label><el-input-number v-model="selectedNode.props.minimumValue" :min="0" size="small" /></div>
                  <div class="form-group"><label>最大值</label><el-input-number v-model="selectedNode.props.maximumValue" :min="0" size="small" /></div>
                </div>
                <div class="form-row">
                  <div class="form-group"><label>输出格式</label><el-input v-model="selectedNode.props.outputFormat" placeholder="000000 (零填充 6 位)" size="small" /></div>
                  <div class="form-group"><label>随机种子 (空=随机)</label><el-input v-model="selectedNode.props.randomSeed" placeholder="留空" size="small" /></div>
                </div>
                <div class="form-group"><label>每次迭代重新生成</label><el-switch v-model="selectedNode.props.perIteration" size="small" /></div>
              </div>
            </template>
          </div>
          <div class="editor-empty" v-else>
            <el-icon size="36"><EditPen /></el-icon>
            <p>选择左侧树中的元素<br/>开始编辑属性</p>
            <div class="editor-empty-tips">
              <div class="empty-tip" @click="addRootElement">➕ 添加线程组</div>
              <div class="empty-tip" @click="currentStep = 1">📥 导入接口用例</div>
            </div>
          </div>
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
                <el-button v-if="!benching" type="danger" size="large" @click="startBench" style="width:100%;margin-bottom:8px;font-size:15px;font-weight:700;">
                  ⚡ 开始并发测试（{{ benchConcurrency }} 虚拟用户 × {{ benchDuration }}秒）
                </el-button>
                <el-button v-else type="warning" size="large" @click="stopBench" style="width:100%;margin-bottom:8px;font-size:15px;font-weight:700;">
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
                  <div v-if="benchResult.status_distribution" style="margin-top:8px;display:flex;gap:6px;flex-wrap:wrap;align-items:center;">
                    <span style="font-size:11px;color:var(--tm-text-secondary);">状态码：</span>
                    <el-tag v-for="(count, code) in benchResult.status_distribution" :key="code" :type="Number(code) >= 200 && Number(code) < 400 ? 'success' : Number(code) >= 400 || Number(code) === 0 ? 'danger' : 'warning'" size="small">
                      HTTP {{ code }}: {{ count }}
                    </el-tag>
                  </div>

                  <!-- 错误信息 -->
                  <div v-if="benchResult.errors && benchResult.errors.length > 0" style="margin-top:6px;">
                    <el-alert v-for="(err, ei) in benchResult.errors.slice(0,5)" :key="ei" :title="err" type="error" :closable="false" show-icon style="margin-bottom:2px;font-size:11px;" />
                  </div>

                  <!-- ===== 按接口统计（聚合报告）直接展开 ===== -->
                  <div v-if="benchResult.per_url && benchResult.per_url.length > 0" class="bench-data-block">
                    <h4 class="bench-section-title" style="display:flex;justify-content:space-between;align-items:center;">
                      📊 按接口统计（聚合报告）
                      <span style="font-size:11px;font-weight:400;color:var(--tm-text-secondary);">共 {{ benchResult.per_url.length }} 个接口</span>
                    </h4>
                    <div class="per-url-table">
                      <div class="per-url-header">
                        <span class="col-url">接口 URL</span>
                        <span class="col-num">请求数</span>
                        <span class="col-num">成功</span>
                        <span class="col-num">失败</span>
                        <span class="col-num">平均耗时</span>
                        <span class="col-num">P95 耗时</span>
                        <span class="col-num">P99 耗时</span>
                        <span class="col-num">最慢耗时</span>
                        <span class="col-num">标准差</span>
                      </div>
                      <div v-for="pu in benchResult.per_url" :key="pu.url" class="per-url-row">
                        <span class="col-url" :title="pu.url">{{ shortUrl(pu.url) }}</span>
                        <span class="col-num">{{ pu.count }}</span>
                        <span class="col-num text-success">{{ pu.success }}</span>
                        <span class="col-num" :class="pu.failed > 0 ? 'text-danger' : ''">{{ pu.failed }}</span>
                        <span class="col-num">{{ pu.avg_ms }}ms</span>
                        <span class="col-num">{{ pu.p95_ms }}ms</span>
                        <span class="col-num">{{ pu.p99_ms || '-' }}ms</span>
                        <span class="col-num">{{ pu.max_ms }}ms</span>
                        <span class="col-num">{{ pu.stddev_ms || '-' }}ms</span>
                      </div>
                    </div>
                  </div>

                  <!-- ===== 请求详情（查看结果树）三标签页 ===== -->
                  <div v-if="benchResult.samples && benchResult.samples.length > 0" class="bench-data-block">
                    <h4 class="bench-section-title" style="display:flex;justify-content:space-between;align-items:center;">
                      🔍 查看结果树
                      <span style="font-size:11px;font-weight:400;color:var(--tm-text-secondary);">共 {{ benchResult.samples.length }} 条样本</span>
                    </h4>
                    <div class="vrt-container">
                      <div class="vrt-left-col">
                        <div class="vrt-toolbar">
                          <span class="vrt-toolbar-label">查找:</span>
                          <el-input v-model="sampleSearchQuery" size="small" clearable style="width:150px;" @keyup.enter="doVrtSearch" />
                          <el-checkbox v-model="searchCaseSensitive" size="small">区分大小写</el-checkbox>
                          <el-checkbox v-model="searchRegex" size="small">正则表达式</el-checkbox>
                          <el-button size="small" type="primary" plain @click="doVrtSearch">查找</el-button>
                          <el-button size="small" @click="resetVrtSearch">重置</el-button>
                          <el-select v-model="sampleStatusFilter" size="small" clearable placeholder="全部" style="width:85px;margin-left:auto;">
                            <el-option label="成功" value="success" />
                            <el-option label="失败" value="error" />
                            <el-option label="异常" value="exception" />
                          </el-select>
                        </div>
                        <div class="vrt-sample-list">
                          <div v-for="(s, si) in filteredSamples" :key="si"
                            class="vrt-sample-item" :class="{ active: selectedSampleIdx === si }" @click="selectSample(si)">
                            <el-tag :type="s.status >= 200 && s.status < 400 ? 'success' : s.status === 0 ? 'danger' : 'warning'" size="small">{{ s.status || 'ERR' }}</el-tag>
                            <span class="vrt-time">{{ s.elapsed_ms }}ms</span>
                            <span class="vrt-name" :title="s.name || s.url">{{ s.name || shortUrl(s.url) }}</span>
                            <span v-if="s.error" class="vrt-err" title="有错误">⚠</span>
                          </div>
                          <div v-if="filteredSamples.length === 0" style="padding:12px;text-align:center;color:var(--tm-text-secondary);font-size:12px;">无匹配结果</div>
                        </div>
                      </div>
                      <div v-if="selectedSample" class="vrt-detail-panel">
                        <el-tabs v-model="selectedSampleTab" size="small" class="vrt-tabs">
                          <!-- 采样器结果 -->
                          <el-tab-pane label="采样器结果" name="sampler">
                            <table class="vrt-table">
                              <tr><td class="vrt-label">Thread Name</td><td>{{ selectedSample.thread_name || '线程组 1-' + (selectedSampleIdx + 1) }}</td></tr>
                              <tr><td class="vrt-label">Sample Start</td><td>{{ selectedSample.start_time || '-' }}</td></tr>
                              <tr><td class="vrt-label">Load time</td><td><b>{{ selectedSample.elapsed_ms || 0 }}</b> ms</td></tr>
                              <tr><td class="vrt-label">Connect Time</td><td>{{ selectedSample.connect_time_ms ?? '-' }} ms</td></tr>
                              <tr><td class="vrt-label">Latency</td><td>{{ (selectedSample.latency_ms ?? selectedSample.elapsed_ms) }} ms</td></tr>
                              <tr><td class="vrt-label">Size in bytes</td><td>{{ selectedSample.body_size || 0 }}</td></tr>
                              <tr><td class="vrt-label">Sent bytes</td><td>{{ selectedSample.sent_bytes || 0 }}</td></tr>
                              <tr><td class="vrt-label">Headers size in bytes</td><td>{{ selectedSample.headers_size || 0 }}</td></tr>
                              <tr><td class="vrt-label">Body size in bytes</td><td>{{ selectedSample.body_size || 0 }}</td></tr>
                              <tr><td class="vrt-label">Sample Count</td><td>1</td></tr>
                              <tr><td class="vrt-label">Error Count</td><td :style="{ color: selectedSample.error ? 'var(--el-color-danger)' : 'var(--el-color-success)' }">{{ selectedSample.error ? '1' : '0' }}</td></tr>
                              <tr><td class="vrt-label">Data type</td><td>{{ selectedSample.data_type || 'text' }}</td></tr>
                              <tr><td class="vrt-label">Response code</td><td><el-tag :type="selectedSample.status >= 200 && selectedSample.status < 400 ? 'success' : 'danger'" size="small">{{ selectedSample.status || 'ERR' }}</el-tag></td></tr>
                              <tr><td class="vrt-label">Response message</td><td>{{ selectedSample.response_message || (selectedSample.status >= 200 && selectedSample.status < 400 ? 'OK' : 'Error') }}</td></tr>
                              <template v-if="selectedSample.http_fields">
                                <tr class="vrt-subheader"><td colspan="2"><b>HTTPSamplerResult fields:</b></td></tr>
                                <tr><td class="vrt-label indent1">ContentType</td><td>{{ selectedSample.http_fields.content_type || '-' }}</td></tr>
                                <tr><td class="vrt-label indent1">DataEncoding</td><td>{{ selectedSample.http_fields.encoding || 'null' }}</td></tr>
                              </template>
                            </table>
                          </el-tab-pane>
                          <!-- 请求 -->
                          <el-tab-pane label="请求" name="request">
                            <el-tabs v-model="selectedRequestTab" size="small" class="vrt-inner-tabs">
                              <el-tab-pane label="Request Body" name="rbody">
                                <pre class="vrt-code">{{ selectedSample.request_body || '(无请求体)' }}</pre>
                              </el-tab-pane>
                              <el-tab-pane label="Request Headers" name="rheaders">
                                <pre class="vrt-code"><template v-if="selectedSample.request_headers">{{ formatHeaders(selectedSample.request_headers) }}</template><template v-else>(无请求头信息)</template></pre>
                              </el-tab-pane>
                            </el-tabs>
                            <div v-if="selectedSample.method" class="vrt-http-line">
                              <code>{{ selectedSample.method }} {{ selectedSample.url }}</code>
                            </div>
                          </el-tab-pane>
                          <!-- 响应数据 -->
                          <el-tab-pane label="响应数据" name="response">
                            <el-tabs v-model="selectedResponseTab" size="small" class="vrt-inner-tabs">
                              <el-tab-pane label="Response Body" name="resbody">
                                <pre class="vrt-code" :class="{ 'vrt-error-body': selectedSample.error }">{{ selectedSample.response_body || selectedSample.error || '(空响应)' }}</pre>
                              </el-tab-pane>
                              <el-tab-pane label="Response headers" name="resheaders">
                                <pre class="vrt-code"><template v-if="selectedSample.response_headers">{{ formatHeaders(selectedSample.response_headers) }}</template><template v-else>(无响应头信息)</template></pre>
                              </el-tab-pane>
                            </el-tabs>
                          </el-tab-pane>
                        </el-tabs>
                      </div>
                      <div v-else class="vrt-empty-detail">
                        👆 点击上方样本查看详情
                      </div>
                    </div>
                  </div>

                  <!-- ===== 响应体采样 直接展开 ===== -->
                  <div v-if="benchResult.body_samples && benchResult.body_samples.length > 0" class="bench-data-block">
                    <h4 class="bench-section-title" style="display:flex;justify-content:space-between;align-items:center;">
                      📄 响应体采样
                      <span style="font-size:11px;font-weight:400;color:var(--tm-text-secondary);">每个接口前 3 条响应内容，最多 1000 字符</span>
                    </h4>
                    <div v-for="(bs, bi) in benchResult.body_samples" :key="bi" style="margin-bottom:6px;">
                      <div style="display:flex;align-items:center;gap:6px;font-size:11px;color:var(--tm-text-secondary);margin-bottom:3px;">
                        <el-tag :type="bs.status >= 200 && bs.status < 400 ? 'success' : 'danger'" size="small">{{ bs.status }}</el-tag>
                        <span style="word-break:break-all;">{{ shortUrl(bs.url) }}</span>
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
                <div v-if="debugResult" class="vrt-container">
                  <div class="vrt-detail-panel">
                    <el-tabs v-model="debugTab" size="small" class="vrt-tabs">
                      <el-tab-pane label="采样器结果" name="dsampler">
                        <table class="vrt-table">
                          <tr><td class="vrt-label">Thread Name</td><td>Debug-1</td></tr>
                          <tr><td class="vrt-label">Sample Start</td><td>{{ new Date().toLocaleString() }}</td></tr>
                          <tr><td class="vrt-label">Load time</td><td><b>{{ debugResult.response?.elapsed_ms || 0 }}</b> ms</td></tr>
                          <tr><td class="vrt-label">Connect Time</td><td>{{ debugResult.response?.connect_time_ms ?? '-' }} ms</td></tr>
                          <tr><td class="vrt-label">Latency</td><td>{{ (debugResult.response?.latency_ms ?? debugResult.response?.elapsed_ms) }} ms</td></tr>
                          <tr><td class="vrt-label">Size in bytes</td><td>{{ debugResult.response?.body_size || 0 }}</td></tr>
                          <tr><td class="vrt-label">Sent bytes</td><td>{{ debugResult.request?.body_size || (debugResult.request?.body ? new Blob([JSON.stringify(debugResult.request.body)]).size : 0) }}</td></tr>
                          <tr><td class="vrt-label">Headers size in bytes</td><td>-</td></tr>
                          <tr><td class="vrt-label">Body size in bytes</td><td>{{ debugResult.response?.body_size || 0 }}</td></tr>
                          <tr><td class="vrt-label">Sample Count</td><td>1</td></tr>
                          <tr><td class="vrt-label">Error Count</td><td :style="{ color: debugResult.response?.error ? 'var(--el-color-danger)' : 'var(--el-color-success)' }">{{ debugResult.response?.error ? '1' : '0' }}</td></tr>
                          <tr><td class="vrt-label">Data type</td><td>text</td></tr>
                          <tr><td class="vrt-label">Response code</td><td><el-tag :type="debugResult.response?.status_code === 200 ? 'success' : 'danger'" size="small">{{ debugResult.response?.status_code || 'ERR' }}</el-tag></td></tr>
                          <tr><td class="vrt-label">Response message</td><td>{{ debugResult.response?.status_code === 200 ? 'OK' : 'Error' }}</td></tr>
                        </table>
                      </el-tab-pane>
                      <el-tab-pane label="请求" name="drequest">
                        <el-tabs v-model="debugReqTab" size="small" class="vrt-inner-tabs">
                          <el-tab-pane label="Request Body" name="drbody">
                            <pre class="vrt-code">{{ formatBody(debugResult.request?.body) || '(无请求体)' }}</pre>
                          </el-tab-pane>
                          <el-tab-pane label="Request Headers" name="drheaders">
                            <pre class="vrt-code">{{ formatHeaders(debugResult.request?.headers) || '(无请求头信息)' }}</pre>
                          </el-tab-pane>
                        </el-tabs>
                        <div v-if="debugResult.request?.url || debugResult.request?.method" class="vrt-http-line">
                          <code>{{ debugResult.request?.method || '?' }} {{ debugResult.request?.url || '' }}</code>
                        </div>
                      </el-tab-pane>
                      <el-tab-pane label="响应数据" name="dresponse">
                        <el-tabs v-model="debugResTab" size="small" class="vrt-inner-tabs">
                          <el-tab-pane label="Response Body" name="drsbody">
                            <pre class="vrt-code" :class="{ 'vrt-error-body': debugResult.response?.error }">{{ formatBody(debugResult.response?.body) || debugResult.response?.error || '(空响应)' }}</pre>
                          </el-tab-pane>
                          <el-tab-pane label="Response headers" name="drsheaders">
                            <pre class="vrt-code">{{ formatHeaders(debugResult.response?.headers) || '(无响应头信息)' }}</pre>
                          </el-tab-pane>
                        </el-tabs>
                      </el-tab-pane>
                    </el-tabs>
                  </div>
                </div>
                <div v-else class="empty-hint">
                  <p>在「配置参数」步骤中<br/>选中一个 HTTP 请求点击「调试」</p>
                </div>
              </div>
            </el-tab-pane>
          </el-tabs>
        </div>

        <!-- 拖拽分隔条：主区域 ↔ JMX 预览侧边栏
             target=right 明确 size 控制的是"右侧 JMX 预览"宽度。
             min=0 支持完全折叠 JMX 预览（浮动按钮接管展开）。 -->
        <BaseSplitter
          v-show="!step3SidebarCollapsed"
          v-model:size="step3SidebarWidth"
          target="right"
          direction="horizontal"
          :min-size="STEP3_SIDEBAR_MIN"
          :max-size="STEP3_SIDEBAR_MAX"
          storage-key="tm-jmeter-step3-sidebar-width"
          container-selector=".step3-layout"
        />
        <!-- 浮动按钮：step3 sidebar 折叠后显示在右上角 -->
        <el-button
          v-if="step3SidebarCollapsed && currentStep === 3"
          class="panel-expand-fab panel-expand-fab--right"
          type="primary"
          plain
          :icon="ArrowLeft"
          title="展开 JMX 预览"
          @click="expandStep3Sidebar"
        />

        <!-- 侧边栏：JMX 预览（compact） -->
        <div v-show="!step3SidebarCollapsed" class="step3-sidebar" :style="{ width: step3SidebarWidth + 'px', flex: 'none' }">
          <div class="panel-title" @click="showJmxPreview = !showJmxPreview" style="cursor:pointer;user-select:none;">
            <span>📦 JMX 导出 {{ showJmxPreview ? '▲' : '▼' }}</span>
          </div>
          <div v-if="showJmxPreview" class="jmx-preview-compact">
            <div style="display:flex;gap:6px;margin-bottom:6px;flex-wrap:wrap;">
              <el-button size="small" @click="generatePreview" :loading="generating">
                🔮 生成预览
              </el-button>
              <el-button size="small" type="success" @click="downloadJmx" :disabled="!jmxContent" title="兼容 JMeter 5.1.1 / 5.2 / 5.3 / 5.4 / 5.5 / 5.6">
                <el-icon><Download /></el-icon> 下载 .jmx
              </el-button>
            </div>
            <pre v-if="jmxContent" class="xml-preview-compact"><code>{{ jmxContent }}</code></pre>
            <div v-else class="empty-hint" style="padding:16px;font-size:12px;">
              <p>点击「生成预览」<br/>查看 JMX 内容<br/><span style="color:var(--tm-text-secondary);font-size:11px;">导出后可导入 JMeter 运行</span></p>
            </div>
          </div>
          <div v-else style="padding:12px;font-size:12px;color:var(--tm-text-secondary);">
            📦 JMX 导出功能：生成 .jmx 文件，兼容 <strong>JMeter 5.1.1+</strong>
            <div style="margin-top:8px;display:flex;gap:6px;">
              <el-button size="small" @click="downloadJmx" :disabled="!jmxContent" type="success" title="兼容 JMeter 5.1.1 / 5.2 / 5.3 / 5.4 / 5.5 / 5.6">
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
        <div style="margin-top:8px;">将 .jmx 文件拖到此处，或点击选择</div>
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

  <!-- AI 分析结果弹窗 -->
  <el-dialog
    v-model="aiAnalysisDialogVisible"
    title="🤖 AI 分析报告"
    width="65%"
    :close-on-click-modal="false"
    destroy-on-close
    class="ai-analysis-dialog"
  >
    <div class="ai-analysis-body" style="white-space: pre-wrap; max-height: 70vh; overflow-y: auto; padding: 16px; background: var(--bg-surface); border-radius: 8px; line-height: 1.8; font-size: 14px;">
      {{ aiAnalysisText }}
    </div>
    <template #footer>
      <el-button @click="aiAnalysisDialogVisible = false">关闭</el-button>
      <el-button type="primary" @click="copyAiAnalysis">📋 复制结果</el-button>
    </template>
  </el-dialog>

  <!-- AI 参数化结果弹窗(Stage E.4) -->
  <el-dialog v-model="aiParamDialogVisible" title="🤖 AI 参数化结果" width="720px" destroy-on-close>
    <el-alert v-if="aiParamResult?.extracted_vars?.length > 0" type="success" :closable="false" show-icon
      :title="`已识别 ${aiParamResult.extracted_vars.length} 个变量`" style="margin-bottom:12px;" />
    <el-form label-width="140px" size="small">
      <el-form-item label="参数化后 URL">
        <el-input v-model="aiParamResult.parameterized_url" type="textarea" :rows="2" readonly />
      </el-form-item>
      <el-form-item v-if="aiParamResult.parameterized_body" label="参数化后 Body">
        <el-input v-model="aiParamResult.parameterized_body" type="textarea" :rows="4" readonly />
      </el-form-item>
      <el-form-item v-if="aiParamResult.extracted_vars?.length > 0" label="提取的变量">
        <el-table :data="aiParamResult.extracted_vars" size="small" stripe border>
          <el-table-column prop="name" label="变量名" width="120" />
          <el-table-column prop="source" label="来源" width="80" />
          <el-table-column prop="original_value" label="原始值" />
        </el-table>
      </el-form-item>
      <el-form-item v-if="aiParamResult.suggested_extractions?.length > 0" label="建议的提取器">
        <el-table :data="aiParamResult.suggested_extractions" size="small" stripe border>
          <el-table-column prop="varName" label="变量名" width="120" />
          <el-table-column prop="jsonPath" label="JSONPath" width="220" />
          <el-table-column prop="description" label="说明" />
        </el-table>
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="aiParamDialogVisible = false">关闭</el-button>
      <el-button type="primary" @click="applyParameterization">应用参数化</el-button>
      <el-button type="success" @click="applyParameterizationAndAddExtractors">应用并添加提取器</el-button>
    </template>
  </el-dialog>
  <HelpDrawer v-model="showHelp" :title="helpData.title" :intro="helpData.intro" :sections="helpData.sections" />

  <!-- 移动到...对话框(跨线程组移动节点) -->
  <el-dialog v-model="moveToDialog.visible" title="📤 移动节点到..." width="520px" append-to-body>
    <div v-if="moveToDialog.sourceUid" style="margin-bottom: 12px;">
      <span style="color: var(--tm-text-secondary); font-size: 12px;">将被移动的节点:</span>
      <span style="margin-left: 8px; font-weight: 500;">
        {{ findNode(scriptTree, moveToDialog.sourceUid)?.name || '(未知)' }}
        <span style="color: var(--tm-text-secondary); font-size: 11px;">
          ({{ nodeTypeInfo(findNode(scriptTree, moveToDialog.sourceUid)?.type)?.label || findNode(scriptTree, moveToDialog.sourceUid)?.type }})
        </span>
      </span>
    </div>
    <el-form label-position="top">
      <el-form-item label="选择目标父节点">
        <el-tree-select
          v-model="moveToDialog.targetUid"
          :data="treeSelectData"
          :props="{ label: 'label', value: 'value', children: 'children' }"
          :filterable="true"
          :check-strictly="true"
          placeholder="请选择目标父节点"
          style="width: 100%;"
          empty-text="无可选节点"
        />
        <div v-if="moveToDialog.targetUid && moveToDialog.sourceUid && !canMoveTo(moveToDialog.sourceUid, moveToDialog.targetUid)" style="color: #F87171; font-size: 12px; margin-top: 6px;">
          ⚠ 该目标不可用(类型不匹配或为自身子节点)
        </div>
        <div v-else-if="moveToDialog.targetUid && moveToDialog.sourceUid && canMoveTo(moveToDialog.sourceUid, moveToDialog.targetUid)" style="color: #67C23A; font-size: 12px; margin-top: 6px;">
          ✓ 目标可用
        </div>
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="moveToDialog.visible = false">取消</el-button>
      <el-button
        type="primary"
        :disabled="!moveToDialog.targetUid || (moveToDialog.sourceUid && !canMoveTo(moveToDialog.sourceUid, moveToDialog.targetUid))"
        @click="confirmMoveTo"
      >
        确定移动
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Refresh, Download, Right, ArrowRight, ArrowLeft, QuestionFilled, VideoPlay, EditPen, FolderDelete, UploadFilled, InfoFilled, Monitor, Connection, Coin, Lollipop, Setting } from '@element-plus/icons-vue'
import autoTestRequest from '@/utils/autoTestRequest'
import { useAICosts } from '@/composables/useAICosts'
import request from '@/utils/request'
import { useUserStore } from '@/stores/user'
import BenchRunner from '@/views/jmeter/BenchRunner.vue'
import ScriptHistory from '@/views/jmeter/ScriptHistory.vue'
import TreeEditor from '@/views/jmeter/TreeEditor.vue'
import HelpDrawer from '@/components/HelpDrawer.vue'
import BaseSplitter from '@/components/base/BaseSplitter.vue'
import LayoutPresetDropdown from '@/components/LayoutPresetDropdown.vue'
import { helpContent } from '@/utils/help-content'
import { NODE_TYPES as _SHARED_NODE_TYPES, TYPE_ALIASES, nodeTypeInfo, isValidParentChild, reassignUids, newUid as sharedNewUid } from './jmeter/shared/nodeTypes'
import { findNode, findParent, isDescendant, deepCopyWithNewUids } from './jmeter/shared/useJmeterTreeOps'
import { useJmeterClipboard } from './jmeter/shared/useJmeterClipboard'

const router = useRouter()
const userStore = useUserStore()
const { fetchCosts, getCostText } = useAICosts()

const showHelp = ref(false)
const helpData = helpContent.jmeterAssistant

const benchRunnerRef = ref(null)

// ===== 组件类型定义(从共享模块导入,并合并别名以保证向后兼容) =====
// 共享 nodeTypes.js 只含规范类型名;此处合并别名(NODE_TYPES['JSONPathAssertion'] 仍可访问)
const NODE_TYPES = { ..._SHARED_NODE_TYPES }
Object.entries(TYPE_ALIASES).forEach(([alias, canonical]) => {
  if (NODE_TYPES[canonical] && !NODE_TYPES[alias]) {
    NODE_TYPES[alias] = NODE_TYPES[canonical]
  }
})

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
  BeanShellPreProcessor: { script: '// 常用场景：修改请求参数、添加签名、设置时间戳\n// 示例：添加请求时间戳\nlong ts = System.currentTimeMillis();\nvars.put("requestTime", String.valueOf(ts));' },
  BeanShellPostProcessor: { script: '// 常用场景：提取响应数据、写文件、修改变量\n// 示例：提取数据并写入CSV文件\nString data = prev.getResponseDataAsString();\n// FileWriter fstream = new FileWriter("D:/result.csv", true);\n// BufferedWriter out = new BufferedWriter(fstream);\n// out.write(vars.get("uniqueid") + "," + vars.get("token"));\n// out.write("\\r\\n");\n// out.close(); fstream.close();' },
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
  InfluxDBBackendListener: { influxdbUrl: 'http://localhost:8086/write?db=jmeter', application: 'test', measurement: 'jmeter', summaryOnly: false, samplersRegex: '', percentiles: '50;90;95;99', testTitle: '', eventTags: '', tagRandom: '' },
  UserParameters: { names: ['sid', 'sid2'], users: [['user1_pass1', 'user2_pass2']], perIteration: false },
  DebugSampler: {},
  ForEachController: { inputVar: '', outputVar: '', useSeparator: true, separator: '_' },
  IncludeController: { includePath: '' },
  SwitchController: { switchValue: '' },
  RandomController: {},
  InterleaveController: {},
  JSONPathAssertion: { jsonPath: '$', expected: '', jsonValidation: true, expectNull: false, invert: false },
  BoundaryExtractor: { referenceName: '', leftBoundary: '', rightBoundary: '', matchNumber: '1', defaultValue: '' },
  CSSSelectorExtractor: { referenceName: '', cssSelector: '', attribute: '', matchNumber: '1', defaultValue: '' },
  XPathExtractor: { referenceName: '', xpathQuery: '', matchNumber: '1', defaultValue: '' },
  HttpHeaderManager: { headers: [{ key: 'Content-Type', value: 'application/json' }] },
  HttpCacheManager: { clearEachIteration: false, useCacheControlHeaders: true },
  HttpAuthManager: { authList: [] },
  CsvDataSource: { filePath: '', variableNames: '', delimiter: ',', shareMode: 'allThreads', recycle: true, stopThread: false, ignoreFirstLine: true },
  RandomVariableConfig: { variableName: '', minValue: '', maxValue: '', perThread: false },
  ModuleController: {},
  RunTimeController: { seconds: 60 },
  Summariser: {},
  ConstantThroughputTimer: { throughput: '60.0' },
  SynchronizingTimer: { virtualUsers: 0, timeout: 0 },
  PoissonRandomTimer: { delay: '0', range: '100' },
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

// findNode / findParent 已从共享模块 ./jmeter/shared/useJmeterTreeOps 导入,此处不再重复定义

const serializeTree = () => {
  const walk = (node) => ({
    type: node.type,
    name: node.name,
    props: JSON.parse(JSON.stringify(node.props)),
    children: (node.children || []).map(walk),
  })
  return scriptTree.children.map(walk)
}

// ===== 状态持久化（按用户隔离） =====
const _uid = computed(() => userStore.userId || 'anon')
const STORAGE_KEY = computed(() => `jmeter_scripts_${_uid.value}`)
const CURRENT_KEY = computed(() => `jmeter_current_script_${_uid.value}`)
const MAX_SCRIPTS = 20

const loadScriptsList = () => {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? JSON.parse(raw) : []
  } catch { return [] }
}

const saveScriptsList = (list) => {
  try { localStorage.setItem(STORAGE_KEY, JSON.stringify(list)) } catch {}
}

const loadCurrentScript = () => {
  try {
    const raw = localStorage.getItem(CURRENT_KEY)
    return raw ? JSON.parse(raw) : null
  } catch { return null }
}

const saveCurrentScript = () => {
  try {
    const data = {
      tree: JSON.parse(JSON.stringify(scriptTree)),
      step: currentStep.value,
      time: new Date().toLocaleString(),
    }
    localStorage.setItem(CURRENT_KEY, JSON.stringify(data))
    // 同时保存到历史记录
    const list = loadScriptsList()
    const idx = list.findIndex(s => s.tree.name === scriptTree.name)
    const entry = { tree: JSON.parse(JSON.stringify(scriptTree)), time: new Date().toLocaleString(), name: scriptTree.name }
    if (idx >= 0) list.splice(idx, 1)
    list.unshift(entry)
    if (list.length > MAX_SCRIPTS) list.length = MAX_SCRIPTS
    saveScriptsList(list)
  } catch {}
}

const deleteScriptFromHistory = (name) => {
  const list = loadScriptsList().filter(s => s.name !== name)
  saveScriptsList(list)
  scriptHistory.value = list
}

// ===== 状态 =====
const currentStep = ref(1)
const showGuide = ref(false)
const showScriptHistory = ref(false)
const scriptHistory = ref(loadScriptsList())

const scriptTree = reactive(createElement('TestPlan', { name: 'TestMaster 性能测试' }))
const selectedUid = ref(null)
const selectedNode = ref(null)

// ===== 剪贴板与跨节点操作(从共享 composable 引入) =====
const {
  clipboard: jmeterClipboard,
  cutNode: _cutNode,
  copyToClipboard: _copyToClipboard,
  copyNodeTo: _copyNodeTo,
  pasteNode: _pasteNode,
  moveNode: _moveNode,
  toggleEnabled: _toggleEnabled,
} = useJmeterClipboard(scriptTree, {
  onTreeChanged: () => {
    // 树变更时触发持久化(复用现有 saveCurrentScript)
    if (typeof saveCurrentScript === 'function') saveCurrentScript()
  },
})

// "移动到..." 对话框状态
const moveToDialog = ref({
  visible: false,
  sourceUid: null,
  targetUid: null,
})

// 树选择器数据(供"移动到..."对话框使用)
const treeSelectData = computed(() => {
  const build = (node) => {
    const item = { value: node.uid, label: node.name || '(未命名)', children: [] }
    if (Array.isArray(node.children) && node.children.length > 0) {
      item.children = node.children.map(build)
    }
    return item
  }
  return [build(scriptTree)]
})

// 校验目标父节点是否可接收源节点
const canMoveTo = (sourceUid, targetUid) => {
  if (!sourceUid || !targetUid || sourceUid === targetUid) return false
  const source = findNode(scriptTree, sourceUid)
  const target = findNode(scriptTree, targetUid)
  if (!source || !target) return false
  if (isDescendant(source, targetUid)) return false
  return isValidParentChild(target.type, source.type)
}

// 打开"移动到..."对话框
const openMoveToDialog = (uid) => {
  moveToDialog.value = { visible: true, sourceUid: uid, targetUid: null }
}

// 确认移动
const confirmMoveTo = () => {
  if (!moveToDialog.value.sourceUid || !moveToDialog.value.targetUid) {
    ElMessage.warning('请选择目标父节点')
    return
  }
  const ok = _moveNode(moveToDialog.value.sourceUid, moveToDialog.value.targetUid, -1)
  if (ok) {
    moveToDialog.value.visible = false
  }
}

// 恢复上次会话
const restoreLastSession = () => {
  const saved = loadCurrentScript()
  if (saved && saved.tree && saved.tree.children && saved.tree.children.length > 0) {
    scriptTree.name = saved.tree.name || 'TestMaster 性能测试'
    scriptTree.props = saved.tree.props || {}
    scriptTree.children.splice(0, scriptTree.children.length)
    const rebuildNode = (n) => {
      const node = createElement(n.type, { name: n.name, props: n.props || {} })
      node.uid = n.uid || node.uid
      node.enabled = n.enabled !== false
      if (n.children && n.children.length > 0) {
        for (const child of n.children) {
          node.children.push(rebuildNode(child))
        }
      }
      return node
    }
    for (const child of saved.tree.children) {
      scriptTree.children.push(rebuildNode(child))
    }
    currentStep.value = saved.step || 2
    ElMessage.success(`已恢复上次会话：${scriptTree.name}`)
  }
}

// 从历史记录加载脚本
const loadScriptFromHistory = (h) => {
  if (!h.tree || !h.tree.children) return
  scriptTree.name = h.tree.name || 'TestMaster 性能测试'
  scriptTree.props = h.tree.props || {}
  scriptTree.children.splice(0, scriptTree.children.length)
  const rebuildNode = (n) => {
    const node = createElement(n.type, { name: n.name, props: n.props || {} })
    node.uid = n.uid || node.uid
    node.enabled = n.enabled !== false
    if (n.children && n.children.length > 0) {
      for (const child of n.children) {
        node.children.push(rebuildNode(child))
      }
    }
    return node
  }
  for (const child of h.tree.children) {
    scriptTree.children.push(rebuildNode(child))
  }
  selectedUid.value = null
  selectedNode.value = null
  currentStep.value = 2
  showScriptHistory.value = false
  ElMessage.success(`已加载脚本：${h.name}`)
}

// 新建脚本
const createNewScript = () => {
  scriptTree.name = 'TestMaster 性能测试'
  scriptTree.props = {}
  scriptTree.children.splice(0, scriptTree.children.length)
  selectedUid.value = null
  selectedNode.value = null
  currentStep.value = 1
  showScriptHistory.value = false
  ElMessage.success('已新建空白脚本')
}

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

const allSamplers = computed(() => {
  const list = []
  const walk = (node) => {
    if (node.type === 'HttpSampler') {
      list.push({
        name: node.name || '',
        method: node.props?.method || 'GET',
        url: node.props?.url || node.props?.path || ''
      })
    }
    ;(node.children || []).forEach(walk)
  }
  walk(scriptTree)
  return list
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
    if (['ResponseAssertion','DurationAssertion','JSONPathAssertion','BeanShellAssertion','JSR223Assertion','SizeAssertion','XPathAssertion','CompareAssertion','XMLAssertion'].includes(node.type)) count++
    ;(node.children || []).forEach(walk)
  }
  walk(scriptTree)
  return count
})

const totalExtractors = computed(() => {
  let count = 0
  const walk = (node) => {
    if (['RegexExtractor','JSONExtractor'].includes(node.type)) count++
    ;(node.children || []).forEach(walk)
  }
  walk(scriptTree)
  return count
})

const totalTimers = computed(() => {
  let count = 0
  const walk = (node) => {
    if (['ConstantTimer','UniformRandomTimer','GaussianRandomTimer','SynchronizingTimer'].includes(node.type)) count++
    ;(node.children || []).forEach(walk)
  }
  walk(scriptTree)
  return count
})

const totalListeners = computed(() => {
  let count = 0
  const walk = (node) => {
    if (['ViewResultsTree','SummaryReport','AggregateGraph','AggregateReport','ResponseTimeGraph','InfluxDBBackendListener'].includes(node.type)) count++
    ;(node.children || []).forEach(walk)
  }
  walk(scriptTree)
  return count
})

const totalNodes = computed(() => {
  let count = 0
  const walk = (node) => {
    count++
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
      if (['ResponseAssertion','DurationAssertion','JSONPathAssertion','BeanShellAssertion','JSR223Assertion','SizeAssertion','XPathAssertion','CompareAssertion','XMLAssertion'].includes(node.type)) { if (!extras.includes('断言')) extras.push('断言') }
      if (['RegexExtractor','JSONExtractor'].includes(node.type)) { if (!extras.includes('提取器')) extras.push('提取器') }
      if (['ConstantTimer','UniformRandomTimer','GaussianRandomTimer'].includes(node.type)) { if (!extras.includes('定时器')) extras.push('定时器') }
      if (node.type === 'SynchronizingTimer') { if (!extras.includes('集合点')) extras.push('集合点') }
      if (node.type === 'CsvDataSource') { if (!extras.includes('CSV数据驱动')) extras.push('CSV数据驱动') }
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

const duplicateNode = (uid, targetParentUid = null) => {
  const source = findNode(scriptTree, uid)
  if (!source) return
  const copy = JSON.parse(JSON.stringify(source))
  // 使用共享的 reassignUids 递归重新分配 UID
  reassignUids(copy)

  if (targetParentUid) {
    // 复制到指定父节点
    const targetParent = findNode(scriptTree, targetParentUid)
    if (!targetParent) return
    if (!isValidParentChild(targetParent.type, source.type)) {
      const srcLabel = nodeTypeInfo(source.type)?.label || source.type
      const tgtLabel = nodeTypeInfo(targetParent.type)?.label || targetParent.type
      ElMessage.warning(`${srcLabel} 不能放在 ${tgtLabel} 下`)
      return
    }
    if (!targetParent.children) targetParent.children = []
    targetParent.children.push(reactive(copy))
    ElMessage.success(`已复制 ${source.name} 到 ${targetParent.name}`)
    if (typeof saveCurrentScript === 'function') saveCurrentScript()
  } else {
    // 原地复制(保持向后兼容)
    const pInfo = findParent(scriptTree, uid)
    if (!pInfo) return
    pInfo.parent.children.splice(pInfo.index + 1, 0, reactive(copy))
    if (typeof saveCurrentScript === 'function') saveCurrentScript()
  }
}

// ===== 跨线程组操作的事件处理(委托给共享 composable) =====
const handleCutNode = (uid) => _cutNode(uid)
const handleCopyNode = (uid) => _copyToClipboard(uid)
const handlePasteNode = (targetParentUid) => _pasteNode(targetParentUid)
const handleToggleEnabled = (uid) => _toggleEnabled(uid)
const handleMoveNode = (movedUid, newParentUid, newIndex) => {
  // 拖拽触发的移动:composable 中已校验,这里只需更新选中状态
  const moved = findNode(scriptTree, movedUid)
  if (moved) {
    selectedUid.value = movedUid
    selectedNode.value = moved
  }
  if (typeof saveCurrentScript === 'function') saveCurrentScript()
}
const handleTreeChanged = () => {
  if (typeof saveCurrentScript === 'function') saveCurrentScript()
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
  scriptTree.children.splice(0, scriptTree.children.length)
  scriptTree.props.variables = []

  if (tpl.key === 'simple') {
    const tg = createElement('ThreadGroup', { name: '线程组', props: { threads: 10, rampUp: 5, loops: 1, duration: 60 } })
    const req = createElement('HttpSampler', { name: 'API 请求', props: { method: 'GET', url: 'https://httpbin.org/get' } })
    tg.children.push(req, createElement('ViewResultsTree', { name: '查看结果树' }))
    scriptTree.children.push(tg)
  } else if (tpl.key === 'login-flow') {
    const tg = createElement('ThreadGroup', { name: '登录流程', props: { threads: 10, rampUp: 5, loops: 1, duration: 60 } })
    const login = createElement('HttpSampler', { name: '登录请求', props: { method: 'POST', url: 'https://api.example.com/auth/login', body: '{"username":"admin","password":"123456"}', bodyType: 'json', headers: [{ key: 'Content-Type', value: 'application/json' }] } })
    login.children.push(createElement('JSONExtractor', { name: '提取 Token', props: { varName: 'token', jsonPath: '$.data.token', defaultValue: 'NOT_FOUND' } }))
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
      createElement('CsvDataSource', { name: '用户数据', props: { filename: 'users.csv', variableNames: 'username,password', delimiter: ',', recycle: true, csvContent: 'username,password\nuser1,pass1\nuser2,pass2' } }),
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
    const res = await autoTestRequest.post('/auto-test/import/jmeter/tree', form, { headers: { 'Content-Type': 'multipart/form-data' } })
    const importedTree = res.tree
    if (!importedTree || !importedTree.children || importedTree.children.length === 0) { ElMessage.warning('未解析出节点'); return }
    const convertNode = (n) => {
      const node = createElement(n.type, { name: n.name, props: n.props || {} })
      node.enabled = n.enabled !== false
      if (n.children && n.children.length > 0) {
        for (const child of n.children) {
          node.children.push(convertNode(child))
        }
      }
      return node
    }
    scriptTree.name = importedTree.name || 'TestMaster 性能测试'
    if (importedTree.props) {
      Object.assign(scriptTree.props, importedTree.props)
    }
    scriptTree.children.splice(0, scriptTree.children.length)
    for (const child of importedTree.children) {
      scriptTree.children.push(convertNode(child))
    }
    selectedUid.value = null
    ElMessage.success(`成功导入完整脚本树（含 ${countAllNodes(importedTree)} 个节点）`)
    showImportJmxDialog.value = false
    currentStep.value = 2
  } catch (e) { ElMessage.error('导入失败: ' + (e.response?.data?.detail || e.message)) }
  finally { jmxImporting.value = false; jmxImportFile.value = null }
}

const countAllNodes = (node, depth = 0) => {
  let count = 1
  if (node.children) {
    for (const c of node.children) count += countAllNodes(c, depth + 1)
  }
  return count
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
  URL.revokeObjectURL(a.href)
  ElMessage.success('下载成功')
}

// ===== bench state delegation to BenchRunner =====
const benchResult = computed(() => benchRunnerRef.value?.benchResult)
const benching = computed(() => benchRunnerRef.value?.benching)
const benchProgress = computed(() => benchRunnerRef.value?.benchProgress)
const benchPercent = computed(() => benchRunnerRef.value?.benchPercent)
const benchConcurrency = computed({
  get: () => benchRunnerRef.value?.benchConcurrency ?? 10,
  set: (v) => { if (benchRunnerRef.value) benchRunnerRef.value.benchConcurrency = v }
})
const benchDuration = computed({
  get: () => benchRunnerRef.value?.benchDuration ?? 10,
  set: (v) => { if (benchRunnerRef.value) benchRunnerRef.value.benchDuration = v }
})
const benchRampUp = computed({
  get: () => benchRunnerRef.value?.benchRampUp ?? 2,
  set: (v) => { if (benchRunnerRef.value) benchRunnerRef.value.benchRampUp = v }
})
const aiAnalysisText = computed(() => benchRunnerRef.value?.aiAnalysisText)
const aiAnalysisDialogVisible = computed({
  get: () => benchRunnerRef.value?.aiAnalysisDialogVisible ?? false,
  set: (v) => { if (benchRunnerRef.value) benchRunnerRef.value.aiAnalysisDialogVisible = v }
})
const startBench = () => {
  selectedSampleIdx.value = -1
  benchRunnerRef.value?.startBench()
}
const stopBench = () => benchRunnerRef.value?.stopBench()
const shortUrl = (url) => {
  try {
    const u = new URL(url)
    return u.pathname + u.search || '/'
  } catch { return url.length > 50 ? url.substring(0, 50) + '...' : url }
}

// 根据视口动态计算各面板默认宽度，避免全屏/缩放时挤压
const getDefaultPanelWidth = (base, min, max) => {
  if (typeof window === 'undefined') return base
  const w = window.innerWidth
  const ratio = Math.min(1, Math.max(0.5, w / 1920))
  return Math.max(min, Math.min(max, Math.round(base * ratio)))
}

const treeWidth = ref(getDefaultPanelWidth(280, 200, 400))
const step1LeftWidth = ref(getDefaultPanelWidth(300, 220, 400))
const step3SidebarWidth = ref(getDefaultPanelWidth(320, 260, 420))

// === 面板可拖拽布局限制（支持完全折叠/展开）===
const TREE_MIN = 0              // Step2 左侧树最小 0（可完全折叠）
const TREE_MAX = 800            // Step2 左侧树最大 800
const STEP1_LEFT_MIN = 0        // Step1 左侧最小 0（可完全折叠）
const STEP1_LEFT_MAX = 800      // Step1 左侧最大 800
const STEP3_SIDEBAR_MIN = 0     // Step3 右侧 sidebar 最小 0（可完全折叠）
const STEP3_SIDEBAR_MAX = 800   // Step3 右侧 sidebar 最大 800
const PANEL_COLLAPSED = 50      // 拖到 < 50 视为折叠，浮动按钮接管展开

// 折叠状态：拖到 < 50px 时自动隐藏对应面板
const step1LeftCollapsed = ref(false)
const treeCollapsed = ref(false)
const step3SidebarCollapsed = ref(false)

const expandStep1Left = () => {
  step1LeftWidth.value = Math.max(PANEL_COLLAPSED + 10, 320)
  step1LeftCollapsed.value = false
  try { localStorage.setItem('tm-jmeter-step1-left-width', String(step1LeftWidth.value)) } catch {}
}
const expandTree = () => {
  treeWidth.value = Math.max(PANEL_COLLAPSED + 10, 280)
  treeCollapsed.value = false
  try { localStorage.setItem('tm-jmeter-tree-width', String(treeWidth.value)) } catch {}
}
const expandStep3Sidebar = () => {
  step3SidebarWidth.value = Math.max(PANEL_COLLAPSED + 10, 360)
  step3SidebarCollapsed.value = false
  try { localStorage.setItem('tm-jmeter-step3-sidebar-width', String(step3SidebarWidth.value)) } catch {}
}

// 监听宽度变化，自动判断折叠/展开
watch(step1LeftWidth, (v) => {
  step1LeftCollapsed.value = v < PANEL_COLLAPSED
})
watch(treeWidth, (v) => {
  treeCollapsed.value = v < PANEL_COLLAPSED
})
watch(step3SidebarWidth, (v) => {
  step3SidebarCollapsed.value = v < PANEL_COLLAPSED
})

// 布局预设：根据当前步骤调整对应侧面板宽度
const applyLayoutPreset = (preset) => {
  const isStep1 = currentStep.value === 1
  const isStep2 = currentStep.value === 2
  const isStep3 = currentStep.value === 3
  const presets = {
    compact: { step1: 220, tree: 200, step3: 240 },
    default: { step1: 300, tree: 280, step3: 320 },
    wide: { step1: 420, tree: 400, step3: 440 },
    'editor-focus': { step1: 0, tree: 0, step3: 0 },
    reset: { step1: getDefaultPanelWidth(300, 220, 400), tree: getDefaultPanelWidth(280, 200, 400), step3: getDefaultPanelWidth(320, 260, 420) }
  }
  const cfg = presets[preset] || presets.default
  if (isStep1 || preset === 'reset') {
    step1LeftWidth.value = cfg.step1
    step1LeftCollapsed.value = cfg.step1 < PANEL_COLLAPSED
  }
  if (isStep2 || preset === 'reset') {
    treeWidth.value = cfg.tree
    treeCollapsed.value = cfg.tree < PANEL_COLLAPSED
  }
  if (isStep3 || preset === 'reset') {
    step3SidebarWidth.value = cfg.step3
    step3SidebarCollapsed.value = cfg.step3 < PANEL_COLLAPSED
  }
  try {
    if (isStep1 || preset === 'reset') localStorage.setItem('tm-jmeter-step1-left-width', String(step1LeftWidth.value))
    if (isStep2 || preset === 'reset') localStorage.setItem('tm-jmeter-tree-width', String(treeWidth.value))
    if (isStep3 || preset === 'reset') localStorage.setItem('tm-jmeter-step3-sidebar-width', String(step3SidebarWidth.value))
  } catch {}
  ElMessage?.success?.(`布局已切换：${preset === 'compact' ? '紧凑' : preset === 'wide' ? '宽屏' : preset === 'editor-focus' ? '编辑器专注' : preset === 'reset' ? '默认' : '默认'}`)
}

const bottomPanelVisible = ref(true)
const bottomPanelHeight = ref(320)
const bottomResultTab = ref('samples')

const selectedSampleIdx = ref(-1)
const selectedSampleTab = ref('sampler')
const selectedRequestTab = ref('rbody')
const selectedResponseTab = ref('resbody')
const sampleSearchQuery = ref('')
const sampleSearchActive = ref('')
const searchCaseSensitive = ref(false)
const searchRegex = ref(false)
const sampleStatusFilter = ref('')

const selectedSample = computed(() => {
  if (selectedSampleIdx.value < 0) return null
  const list = filteredSamples.value
  if (selectedSampleIdx.value >= list.length) return null
  return list[selectedSampleIdx.value]
})

const doVrtSearch = () => {
  sampleSearchActive.value = sampleSearchQuery.value
}

const resetVrtSearch = () => {
  sampleSearchQuery.value = ''
  sampleSearchActive.value = ''
}

const filteredSamples = computed(() => {
  if (!benchResult.value?.samples) return []
  let list = benchResult.value.samples
  if (sampleStatusFilter.value) {
    if (sampleStatusFilter.value === 'success') list = list.filter(s => s.status >= 200 && s.status < 400)
    else if (sampleStatusFilter.value === 'error') list = list.filter(s => s.status >= 400 && s.status < 600)
    else if (sampleStatusFilter.value === 'exception') list = list.filter(s => !s.status || s.status === 0)
  }
  if (sampleSearchActive.value) {
    const q = sampleSearchActive.value
    if (searchRegex.value) {
      try {
        const re = new RegExp(q, searchCaseSensitive.value ? 'g' : 'gi')
        list = list.filter(s => re.test(s.name || '') || re.test(s.url || ''))
      } catch (e) { /* invalid regex, ignore */ }
    } else {
      const target = searchCaseSensitive.value ? q : q.toLowerCase()
      list = list.filter(s => {
        const val = searchCaseSensitive.value ? (s.name || '') + ' ' + (s.url || '') : ((s.name || '') + ' ' + (s.url || '')).toLowerCase()
        return val.includes(target)
      })
    }
  }
  return list
})

const onBottomResize = (e) => {
  e.preventDefault()
  const startY = e.clientY
  const startH = bottomPanelHeight.value
  const onMove = (ev) => {
    bottomPanelHeight.value = Math.max(200, Math.min(window.innerHeight * 0.8, startH + startY - ev.clientY))
  }
  const onEnd = () => {
    document.removeEventListener('mousemove', onMove)
    document.removeEventListener('mouseup', onEnd)
  }
  document.addEventListener('mousemove', onMove)
  document.addEventListener('mouseup', onEnd)
}

const selectSample = (idx) => {
  selectedSampleIdx.value = idx
  selectedSampleTab.value = 'sampler'
}

// ===== 调试 =====
const copyAiAnalysis = async () => {
  if (!aiAnalysisText.value) return
  try {
    await navigator.clipboard.writeText(aiAnalysisText.value)
    ElMessage.success('AI 分析结果已复制到剪贴板')
  } catch {
    const ta = document.createElement('textarea')
    ta.value = aiAnalysisText.value
    document.body.appendChild(ta)
    ta.select()
    document.execCommand('copy')
    document.body.removeChild(ta)
    ElMessage.success('AI 分析结果已复制到剪贴板')
  }
}

const debugResult = ref(null)
const debugLoading = ref(false)
const debugTab = ref('dsampler')
const debugReqTab = ref('drbody')
const debugResTab = ref('drsbody')

// AI 参数化(Stage E.4)
const aiParamLoading = ref(false)
const aiParamDialogVisible = ref(false)
const aiParamResult = ref({
  parameterized_url: '',
  parameterized_body: '',
  extracted_vars: [],
  suggested_extractions: [],
  raw_ai_answer: '',
})

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

// AI 参数化:调用 /ai/jmeter/parameterize 识别 URL/Body 中的变量并生成 ${var} 引用(Stage E.4)
const aiParameterize = async (node) => {
  if (!node || node.type !== 'HttpSampler') return
  aiParamLoading.value = true
  try {
    const headers = (node.props.headers || []).filter(h => h.key).map(h => ({ key: h.key, value: h.value }))
    const res = await autoTestRequest.post('/ai/jmeter/parameterize', {
      url: node.props.url || '',
      method: node.props.method || 'GET',
      body: node.props.method !== 'GET' ? (node.props.body || '') : '',
      headers,
    })
    aiParamResult.value = res
    aiParamDialogVisible.value = true
    ElMessage.success(`识别到 ${res.extracted_vars?.length || 0} 个变量,${res.suggested_extractions?.length || 0} 个建议提取器`)
  } catch (e) {
    ElMessage.error('AI 参数化失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    aiParamLoading.value = false
  }
}

const applyParameterization = () => {
  if (!selectedNode.value || selectedNode.value.type !== 'HttpSampler') return
  if (aiParamResult.value.parameterized_url) {
    selectedNode.value.props.url = aiParamResult.value.parameterized_url
  }
  if (aiParamResult.value.parameterized_body) {
    selectedNode.value.props.body = aiParamResult.value.parameterized_body
  }
  ElMessage.success('已应用参数化到当前节点')
  aiParamDialogVisible.value = false
}

const applyParameterizationAndAddExtractors = () => {
  applyParameterization()
  const suggestions = aiParamResult.value.suggested_extractions || []
  if (suggestions.length === 0) {
    ElMessage.info('没有建议的提取器')
    return
  }
  suggestions.forEach(s => {
    addChildToCurrent('JSONExtractor')
    if (selectedNode.value && selectedNode.value.children) {
      const lastChild = selectedNode.value.children[selectedNode.value.children.length - 1]
      if (lastChild && lastChild.type === 'JSONExtractor') {
        lastChild.props.referenceName = s.varName
        lastChild.props.jsonPath = s.jsonPath
      }
    }
  })
  ElMessage.success(`已添加 ${suggestions.length} 个 JSON 提取器`)
}

const formatHeaders = (h) => {
  if (!h) return ''
  if (typeof h === 'object' && !Array.isArray(h)) {
    return Object.entries(h).map(([k, v]) => `${k}: ${v}`).join('\n')
  }
  if (Array.isArray(h)) {
    return h.map(item => {
      if (typeof item === 'object') return `${item.key || item.name || ''}: ${item.value || ''}`
      return String(item)
    }).join('\n')
  }
  return String(h)
}
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
const aiValidating = ref(false)
const aiValidationResult = ref(null)
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
const resizeHandler = () => benchRunnerRef.value?.resizeAllBenchCharts()

onMounted(() => {
  fetchCosts()
  loadImportGroups()
  loadCases()
  loadCaseGroups()
  restoreLastSession()
  if (scriptTree.children.length === 0) {
    const tg = createElement('ThreadGroup')
    tg.name = '线程组 1'
    const sampler = createElement('HttpSampler', { name: '示例请求', props: { method: 'GET', url: 'https://httpbin.org/get' } })
    tg.children.push(sampler, createElement('ViewResultsTree'))
    scriptTree.children.push(tg)
  }
  window.addEventListener('resize', resizeHandler)
})

// 自动保存：脚本树变化时
let saveTimer = null
watch(() => JSON.stringify(scriptTree), () => {
  clearTimeout(saveTimer)
  saveTimer = setTimeout(() => {
    saveCurrentScript()
    scriptHistory.value = loadScriptsList()
  }, 1500)
})

// 自动保存：步骤变化时
watch(currentStep, () => {
  clearTimeout(saveTimer)
  saveTimer = setTimeout(() => {
    saveCurrentScript()
    scriptHistory.value = loadScriptsList()
  }, 500)
})

watch(benchResult, (newVal, oldVal) => {
  if (newVal && !oldVal) {
    const findVRT = (node) => {
      if (node.type === 'ViewResultsTree') return node
      for (const c of node.children || []) {
        const found = findVRT(c)
        if (found) return found
      }
      return null
    }
    const vrt = findVRT(scriptTree)
    if (vrt) selectNode(vrt.uid)
  }
})

const projectVariables = computed(() => {
  const vars = []
  const walk = (node) => {
    if (node.type === 'JSONExtractor' || node.type === 'RegexExtractor') {
      if (node.props.varName) vars.push({ name: node.props.varName, source: `${node.name} (${node.type === 'JSONExtractor' ? 'JSON提取' : '正则提取'})` })
    }
    if (node.type === 'CsvDataSource' && node.props.variableNames) {
      node.props.variableNames.split(',').forEach(n => {
        const trimmed = n.trim()
        if (trimmed) vars.push({ name: trimmed, source: `${node.name} (CSV数据源)` })
      })
    }
    if (node.type === 'TestPlan' && node.props.variables) {
      node.props.variables.forEach(v => {
        if (v.name) vars.push({ name: v.name, source: `测试计划变量` })
      })
    }
    ;(node.children || []).forEach(walk)
  }
  walk(scriptTree)
  return vars
})

const insertVariable = (varName) => {
  if (!selectedNode.value?.props?.script && selectedNode.value?.props?.script !== '') return
  const ref = '${' + varName + '}'
  const el = document.querySelector('.editor-body textarea')
  if (el) {
    const start = el.selectionStart
    const end = el.selectionEnd
    const script = selectedNode.value.props.script
    selectedNode.value.props.script = script.substring(0, start) + ref + script.substring(end)
    nextTick(() => { el.focus(); el.setSelectionRange(start + ref.length, start + ref.length) })
  } else {
    selectedNode.value.props.script += ref
  }
}

const aiGenerateScript = async (type) => {
  const parentSampler = findParentSampler(scriptTree, selectedNode.value?.uid)
  const method = parentSampler?.props?.method || 'GET'
  const url = parentSampler?.props?.url || ''
  const body = parentSampler?.props?.body || ''
  const isPre = selectedNode.value?.type?.includes('Pre')
  const varContext = projectVariables.value.length > 0 ? `\n\n项目中已有变量：${projectVariables.value.map(v => v.name).join(', ')}，可以在脚本中用 vars.get("变量名") 获取` : ''

  let prompt = ''
  if (type === 'BeanShellProcessor') {
    prompt = `你是一个JMeter专家。请为以下HTTP请求编写一个BeanShell${isPre ? '前置' : '后置'}处理器脚本。\n\n请求信息：\n- 方法: ${method}\n- URL: ${url}\n${body ? '- 请求体: ' + body.substring(0, 300) : ''}${varContext}\n\n要求（参考真实压测场景）：\n1. 写一个完整的BeanShell脚本（Java语法）\n2. ${isPre ? '前置常用：添加时间戳(vars.put("ts",...))、修改请求参数、计算签名、设置Cookie' : '后置常用：提取响应数据用正则/JSON解析、写CSV文件(FileWriter+BufferedWriter)、设置变量供后续引用、解析Cookie'}\n3. 使用 vars.put("变量名", 值) 设置变量，vars.get("变量名") 获取变量\n4. 后置处理器中可用: prev.getResponseDataAsString() 获取响应体，prev.getResponseCode() 获取状态码\n5. 写文件示例:\n   FileWriter fw = new FileWriter("D:/result.csv", true);\n   BufferedWriter bw = new BufferedWriter(fw);\n   bw.write(var1 + "," + var2); bw.write("\\r\\n"); bw.close(); fw.close();\n6. 只输出代码，不要解释`
  } else if (type === 'JSR223Processor') {
    const lang = selectedNode.value?.props?.language || 'groovy'
    prompt = `你是一个JMeter专家。请为以下HTTP请求编写一个${lang === 'groovy' ? 'Groovy' : lang}语言的JSR223${isPre ? '前置' : '后置'}处理器脚本。\n\n请求信息：\n- 方法: ${method}\n- URL: ${url}\n${body ? '- 请求体: ' + body.substring(0, 300) : ''}${varContext}\n\n要求：\n1. 写一个完整的${lang}脚本\n2. ${isPre ? '前置：修改请求参数、添加签名、设置时间戳' : '后置：提取响应数据、写文件、设置变量'}\n3. Groovy推荐用法: def json = new groovy.json.JsonSlurper().parseText(prev.getResponseDataAsString()) 解析JSON\n4. 使用 vars.put() 设置变量\n5. 只输出代码，不要解释`
  }

  aiGenerating.value = true
  try {
    const res = await request.post('/ai/chat', { question: prompt })
    const answer = res.answer || ''
    const codeMatch = answer.match(/```(?:java|groovy|beanshell|javascript|python)?\n?([\s\S]*?)```/)
    const code = codeMatch ? codeMatch[1].trim() : answer.trim()
    selectedNode.value.props.script = code
    ElMessage.success('🤖 AI 已为你生成脚本，可自行微调')
  } catch (e) {
    ElMessage.error('AI 生成失败，请检查 AI 配置或稍后重试')
  }
  finally { aiGenerating.value = false }
}

const aiValidateScript = async (type) => {
  const script = selectedNode.value?.props?.script
  if (!script || script.trim().length < 5) {
    ElMessage.warning('脚本内容太少，请先编写或用 AI 生成后再校验')
    return
  }
  const parentSampler = findParentSampler(scriptTree, selectedNode.value?.uid)
  const method = parentSampler?.props?.method || 'GET'
  const url = parentSampler?.props?.url || ''
  const nodeType = selectedNode.value?.type || ''
  const varContext = projectVariables.value.length > 0 ? `\n项目中已有变量：${projectVariables.value.map(v => v.name + '(' + v.source + ')').join(', ')}` : ''

  const prompt = `你是一个JMeter脚本专家。请校验以下${type}脚本是否有问题。\n\n节点类型: ${nodeType}\n关联请求: ${method} ${url}${varContext}\n\n脚本内容：\n\`\`\`\n${script}\n\`\`\`\n\n请检查：\n1. 语法是否有错误\n2. 变量引用是否正确（如vars.get/put是否配对）\n3. 是否有常见陷阱（如字符串比较用==而非equals、ResponseData未转字符串等）\n4. 逻辑是否合理\n\n请用JSON格式回复：{"ok": true/false, "message": "校验结果说明"}`

  aiValidating.value = true
  aiValidationResult.value = null
  try {
    const res = await request.post('/ai/chat', { question: prompt })
    const answer = res.answer || ''
    try {
      const jsonStart = answer.indexOf('{')
      const jsonEnd = answer.lastIndexOf('}') + 1
      if (jsonStart >= 0 && jsonEnd > jsonStart) {
        aiValidationResult.value = JSON.parse(answer.substring(jsonStart, jsonEnd))
      }
    } catch (e) {
      aiValidationResult.value = { ok: true, message: answer.trim().substring(0, 200) }
    }
    if (!aiValidationResult.value) aiValidationResult.value = { ok: true, message: '校验完成' }
  } catch (e) {
    aiValidationResult.value = { ok: false, message: 'AI 校验请求失败，请检查 AI 配置' }
  }
  finally { aiValidating.value = false }
}

const aiGenerateAssert = async (type) => {
  const parentSampler = findParentSampler(scriptTree, selectedNode.value?.uid)
  const method = parentSampler?.props?.method || 'GET'
  const url = parentSampler?.props?.url || ''
  const body = parentSampler?.props?.body || ''
  const headers = parentSampler?.props?.headers || []
  const vars = scriptTree.props?.variables || []
  const varContext = vars.length > 0 ? '\n- 变量: ' + vars.map(v => `${v.name}=${v.value}`).join(', ') : ''

  let prompt = ''
  if (type === 'BeanShell') {
    prompt = `你是一个JMeter专家。请为以下HTTP请求编写一个BeanShell断言脚本。\n\n请求信息：\n- 方法: ${method}\n- URL: ${url}\n${body ? '- 请求体: ' + body.substring(0, 300) : ''}\n${headers.length > 0 ? '- 请求头: ' + JSON.stringify(headers.slice(0, 3)) : ''}${varContext}\n\n要求（参考真实压测场景）：\n1. 写一个完整的BeanShell断言（Java语法）\n2. 检查HTTP状态码是否为200: if (!ResponseCode.equals("200")) { Failure = true; FailureMessage = "状态码异常: " + ResponseCode; }\n3. 检查响应体是否包含关键字或JSON字段\n4. 可用变量: ResponseCode(状态码), ResponseMessage, ResponseData(字节数组), prev(SampleResult)\n5. 设置失败: Failure=true; FailureMessage="原因";\n6. 只输出代码，不要解释`
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

onBeforeUnmount(() => {
  window.removeEventListener('resize', resizeHandler)
  if (saveTimer) { clearTimeout(saveTimer); saveTimer = null }
})
</script>

<style scoped>
/* ===== 全局布局 ===== */
.jmeter-workspace {
  display: flex; flex-direction: column; height: 100%;
  background: var(--tm-bg-page);
  color: var(--tm-text-primary);
  position: relative; /* 为浮动按钮提供定位上下文 */
}

/* 浮动按钮：panel 折叠后接管"展开"操作 */
.panel-expand-fab {
  position: absolute;
  top: 64px; /* 在 step-nav 下方 */
  left: 12px;
  z-index: 100;
  width: 36px;
  height: 36px;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  backdrop-filter: blur(8px);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.panel-expand-fab:hover {
  transform: translateX(2px);
  box-shadow: 0 4px 12px rgba(var(--tm-color-primary-rgb, 99, 102, 241), 0.3);
}
.panel-expand-fab--right {
  left: auto;
  right: 12px;
}
.panel-expand-fab--right:hover {
  transform: translateX(-2px);
}

/* ===== 步骤导航 ===== */
.step-nav {
  display: flex; align-items: center; gap: 8px;
  padding: 14px 20px; background: var(--tm-card-bg);
  border-bottom: 1px solid var(--tm-border-light);
  box-shadow: 0 1px 3px rgba(0,0,0,0.04), 0 1px 2px rgba(0,0,0,0.06);
  position: relative;
}
.step { display: flex; align-items: center; gap: 6px; cursor: pointer; padding: 7px 14px; border-radius: 10px; font-size: 13px; color: var(--tm-text-secondary); border: 1.5px solid transparent; transition: all .25s ease; font-weight: 500; }
.step:hover { background: rgba(var(--tm-color-primary-rgb), 0.05); color: var(--tm-text-primary); }
.step.active { color: var(--accent-primary); border-color: rgba(var(--tm-color-primary-rgb), 0.35); background: linear-gradient(135deg, rgba(var(--tm-color-primary-rgb), 0.08), rgba(var(--tm-color-primary-rgb), 0.06)); box-shadow: 0 2px 8px rgba(var(--tm-color-primary-rgb), 0.1); }
.step.done { color: var(--el-color-success); border-color: rgba(var(--el-color-success-rgb), 0.25); background: linear-gradient(135deg, rgba(var(--el-color-success-rgb), 0.08), rgba(var(--el-color-success-rgb), 0.05)); }
.step-num { width: 26px; height: 26px; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 700; background: var(--bg-surface-hover); color: var(--tm-text-secondary); box-shadow: inset 0 -1px 0 rgba(0,0,0,0.06); transition: all .25s ease; }
.step.active .step-num { background: linear-gradient(135deg, var(--tm-color-primary), var(--tm-color-primary)); color: var(--tm-text-primary); box-shadow: 0 2px 6px rgba(var(--tm-color-primary-rgb), 0.3), inset 0 1px 0 rgba(var(--text-primary-rgb), 0.15); }
.step.done .step-num { background: linear-gradient(135deg, var(--el-color-success), var(--el-color-success)); color: var(--tm-text-primary); box-shadow: 0 2px 6px rgba(var(--el-color-success-rgb), 0.25), inset 0 1px 0 rgba(var(--text-primary-rgb), 0.15); }
.step-arrow { color: var(--tm-text-secondary); font-weight: 700; font-size: 13px; }
.step-actions { margin-left: auto; display: flex; gap: 8px; }

/* ===== 引导面板 ===== */
.guide-panel { padding: 8px 20px; }

/* ===== Step 1 布局 ===== */
.step1-layout { display: flex; gap: 0; padding: 0; flex: 1; min-height: 0; overflow: hidden; }
.step1-left { display: flex; flex-direction: column; gap: 12px; overflow-y: auto; }
.step1-templates { overflow: visible; }
.step1-import-jmx { }

/* ===== 面板通用（核心视觉升级） ===== */
.panel {
  background: var(--tm-card-bg);
  border: 1px solid var(--tm-border-light);
  border-radius: 14px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.03), 0 4px 16px rgba(0,0,0,0.03);
  overflow: hidden;
  display: flex; flex-direction: column;
}
.panel-title {
  display: flex; justify-content: space-between; align-items: center;
  padding: 12px 16px;
  font-weight: 700; font-size: 13px;
  color: var(--tm-text-primary);
  background: var(--bg-surface-hover);
  border-bottom: 1px solid var(--tm-border-light);
  letter-spacing: 0.01em;
}

.import-jmx-card {
  display: flex; align-items: center; gap: 14px; padding: 16px 18px;
  background: var(--bg-surface);
  border: 1.5px dashed var(--accent-primary);
  border-radius: 12px; cursor: pointer; transition: all .3s cubic-bezier(.4,0,.2,1);
  position: relative; overflow: hidden;
}
.import-jmx-card::before {
  content: ''; position: absolute; top: 0; left: 0; right: 0; bottom: 0;
  background: radial-gradient(circle at top right, rgba(var(--tm-color-primary-rgb), 0.08) 0%, transparent 60%);
  opacity: 0; transition: opacity .3s;
}
.import-jmx-card:hover::before { opacity: 1; }
.import-jmx-card:hover {
  border-color: var(--accent-hover); border-style: solid;
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(var(--tm-color-primary-rgb), 0.15), 0 2px 6px rgba(var(--tm-color-primary-rgb), 0.08);
}
.import-jmx-icon { font-size: 30px; flex-shrink: 0; filter: drop-shadow(0 2px 4px rgba(0,0,0,0.1)); }
.import-jmx-body { flex: 1; z-index: 1; }
.import-jmx-title { font-size: 14px; font-weight: 700; color: var(--tm-text-primary); }
.import-jmx-desc { font-size: 11.5px; color: var(--tm-text-secondary); margin-top: 3px; line-height: 1.5; }
.step1-import { display: flex; flex-direction: column; overflow: hidden; flex: 1; min-width: 340px; }

.template-grid { display: grid; grid-template-columns: 1fr; gap: 7px; }
.tpl-card {
  padding: 14px 16px;
  border: 1px solid var(--tm-border-light);
  border-radius: 11px; cursor: pointer; transition: all .28s cubic-bezier(.4,0,.2,1);
  background: var(--tm-card-bg);
  display: flex; align-items: center; gap: 12px;
  position: relative; overflow: hidden;
}
.tpl-card::after {
  content: ''; position: absolute; left: 0; top: 0; bottom: 0; width: 3px;
  background: linear-gradient(180deg, var(--tm-color-primary), var(--tm-color-primary));
  border-radius: 0 3px 3px 0; opacity: 0; transition: opacity .25s;
}
.tpl-card:hover {
  border-color: var(--accent-primary);
  background: var(--bg-surface-hover);
  transform: translateX(4px);
  box-shadow: 0 4px 14px rgba(var(--tm-color-primary-rgb), 0.1);
}
.tpl-card:hover::after { opacity: 1; }
.tpl-icon { font-size: 26px; flex-shrink: 0; filter: drop-shadow(0 2px 3px rgba(0,0,0,0.08)); }
.tpl-text { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 2px; }
.tpl-name { font-weight: 700; font-size: 13px; margin: 0; color: var(--tm-text-primary); }
.tpl-desc { font-size: 11px; color: var(--tm-text-secondary); line-height: 1.45; white-space: normal; word-break: break-word; }

.import-controls { display: flex; gap: 10px; margin-bottom: 14px; }
.import-case-list { flex: 1; overflow-y: auto; padding: 0 4px; }
.import-case-item { padding: 5px 8px; border-radius: 8px; cursor: pointer; transition: all .2s; }
.import-case-item:hover { background: var(--bg-surface-hover); }
.case-method { font-size: 11px; font-weight: 800; padding: 2px 7px; border-radius: 5px; margin-right: 8px; letter-spacing: 0.02em; }
.m-get { background: linear-gradient(135deg, color-mix(in srgb, var(--tm-method-get) 15%, transparent), color-mix(in srgb, var(--tm-method-get) 10%, transparent)); color: var(--tm-method-get); }
.m-post { background: linear-gradient(135deg, color-mix(in srgb, var(--tm-method-post) 15%, transparent), color-mix(in srgb, var(--tm-method-post) 10%, transparent)); color: var(--tm-method-post); }
.m-put { background: linear-gradient(135deg, color-mix(in srgb, var(--tm-method-put) 15%, transparent), color-mix(in srgb, var(--tm-method-put) 10%, transparent)); color: var(--tm-method-put); }
.m-delete { background: linear-gradient(135deg, color-mix(in srgb, var(--tm-method-delete) 15%, transparent), color-mix(in srgb, var(--tm-method-delete) 10%, transparent)); color: var(--tm-method-delete); }
.m-patch { background: linear-gradient(135deg, color-mix(in srgb, var(--tm-method-patch) 15%, transparent), color-mix(in srgb, var(--tm-method-patch) 10%, transparent)); color: var(--tm-method-patch); }
.case-name { font-size: 13px; font-weight: 600; color: var(--tm-text-primary); }
.case-url { font-size: 11px; color: var(--tm-text-secondary); margin-left: 8px; }

.import-footer {
  display: flex; justify-content: space-between; align-items: center;
  padding: 14px 16px; border-top: 1px solid var(--tm-border-light); margin-top: 10px;
}
.import-count { font-size: 12.5px; color: var(--tm-text-secondary); font-weight: 500; }

/* ===== Step 2 布局 ===== */
.step2-layout {
  display: flex; flex-direction: column;
  padding: 0; flex: 1; min-height: 0; overflow: hidden;
}
.step2-editor-layout {
  display: flex; flex: 1; min-height: 0; overflow: hidden;
}
.drag-handle {
  width: 6px; flex-shrink: 0; cursor: col-resize;
  background: transparent; transition: background .2s; position: relative;
}
.drag-handle::after {
  content: ''; position: absolute; top: 50%; left: 50%;
  transform: translate(-50%, -50%); width: 2px; height: 32px;
  background: var(--bg-surface-hover); border-radius: 2px; transition: background .2s;
}
.drag-handle:hover, .drag-handle.active { background: rgba(var(--tm-color-primary-rgb), 0.06); }
.drag-handle:hover::after, .drag-handle.active::after { background: rgba(var(--tm-color-primary-rgb), 0.5); height: 48px; }
.editor-panel { display: flex; flex-direction: column; overflow: hidden; min-height: 0; }
.editor-body {
  flex: 1; overflow-y: auto; padding: 16px 18px;
  scrollbar-width: thin; scrollbar-color: var(--tm-text-secondary) transparent;
}
.editor-body::-webkit-scrollbar { width: 6px; }
.editor-body::-webkit-scrollbar-thumb { background: var(--bg-surface-hover); border-radius: 3px; }
.editor-empty {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  flex: 1; color: var(--tm-text-secondary); gap: 12px;
}
.editor-empty p { font-size: 13.5px; line-height: 1.6; max-width: 320px; text-align: center; }
.editor-empty .el-icon { color: var(--tm-text-secondary); filter: drop-shadow(0 2px 4px rgba(0,0,0,0.06)); }
.editor-empty-tips { display: flex; gap: 10px; margin-top: 8px; }
.empty-tip { padding: 6px 14px; border-radius: 8px; font-size: 12px; font-weight: 600; cursor: pointer; background: var(--bg-surface-hover); border: 1px solid var(--accent-primary); color: var(--accent-primary); transition: all .2s; }
.empty-tip:hover { background: var(--bg-surface); transform: translateY(-1px); box-shadow: 0 2px 8px rgba(var(--tm-color-primary-rgb), 0.1); }

/* ===== 底部运行结果面板 ===== */
.bottom-result-panel {
  background: var(--tm-card-bg);
  border-top: 1px solid var(--tm-border-light);
  transition: height 0.2s ease;
  display: flex; flex-direction: column;
  flex-shrink: 0;
}
.bottom-result-panel.collapsed { height: 36px; }
.brp-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 6px 16px; cursor: pointer; user-select: none;
  background: var(--bg-surface-hover);
  border-bottom: 1px solid var(--tm-border-light);
  flex-shrink: 0;
}
.brp-header:hover { background: var(--bg-surface); }
.brp-title { font-weight: 700; font-size: 13px; color: var(--tm-text-primary); }
.brp-header-right { display: flex; align-items: center; gap: 10px; }
.brp-badge { font-size: 11px; color: var(--tm-text-secondary); background: var(--bg-surface); padding: 2px 8px; border-radius: 10px; }
.brp-badge.brp-running { color: var(--el-color-warning); background: rgba(var(--el-color-warning-rgb), 0.15); animation: pulse 2s infinite; }
@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.7; } }
.brp-body {
  display: flex; flex-direction: column;
  overflow: hidden;
  transition: height 0.2s ease;
}
.brp-resize-handle {
  height: 6px; cursor: row-resize; position: absolute; top: -3px; left: 0; right: 0; z-index: 10;
  background: transparent;
}
.brp-resize-handle::after {
  content: ''; position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
  width: 40px; height: 3px; background: var(--bg-surface-hover); border-radius: 2px;
}
.brp-resize-handle:hover::after { background: rgba(var(--tm-color-primary-rgb), 0.5); }

/* 底部面板内的 VRT 布局 */
.vrt-bottom-container {
  display: flex; gap: 0; height: calc(100% - 40px);
  overflow: hidden;
}
.vrt-bottom-left {
  width: 320px; flex-shrink: 0; border-right: 1px solid var(--tm-border-light);
  display: flex; flex-direction: column; overflow: hidden;
}
.vrt-bottom-left .vrt-sample-list {
  flex: 1; overflow-y: auto; padding: 4px;
}
.vrt-bottom-container .vrt-detail-panel {
  flex: 1; min-width: 0; overflow-y: auto; padding: 8px 12px;
}
.vrt-bottom-container .vrt-empty-detail {
  flex: 1; display: flex; align-items: center; justify-content: center;
  color: var(--tm-text-secondary); font-size: 13px;
}

/* 底部面板统计 */
.bottom-result-panel .mini-stats { display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 10px; padding: 8px 10px; background: var(--bg-surface-hover); border-radius: 8px; border: 1px solid var(--tm-border-light); }
.bottom-result-panel .mini-stats > div { display: flex; flex-direction: column; align-items: center; gap: 2px; min-width: 40px; }
.bottom-result-panel .mini-stats b { font-size: 14px; color: var(--tm-text-primary); }
.bottom-result-panel .mini-stats small { font-size: 10px; color: var(--tm-text-secondary); }
.bottom-result-panel .bench-progress-inline { margin-bottom: 10px; font-size: 11px; color: var(--tm-text-secondary); }

/* ===== 自然语言概要 Banner（Step 2 顶部） ===== */
.summary-banner {
  display: flex; align-items: flex-start; gap: 14px;
  padding: 12px 16px; margin: 0 0 12px;
  border-radius: 12px;
  background: linear-gradient(135deg, rgba(var(--tm-color-primary-rgb), 0.09) 0%, rgba(var(--tm-color-primary-rgb), 0.06) 40%, rgba(var(--tm-color-primary-rgb), 0.04) 100%);
  border: 1px solid rgba(var(--tm-color-primary-rgb), 0.18);
  box-shadow: 0 4px 16px rgba(var(--tm-color-primary-rgb), 0.06), inset 0 1px 0 rgba(var(--text-primary-rgb), 0.5);
  position: relative; overflow: hidden;
}
.summary-banner::before {
  content: ''; position: absolute; top: -30px; right: -30px;
  width: 120px; height: 120px; border-radius: 50%;
  background: radial-gradient(circle, rgba(var(--tm-color-primary-rgb), 0.1) 0%, transparent 70%);
}
.summary-banner-empty {
  background: var(--bg-surface);
  border-color: var(--tm-border-light);
  box-shadow: none;
}
.summary-banner-empty::before { display: none; }
.summary-banner-icon { font-size: 28px; line-height: 1; flex-shrink: 0; margin-top: 2px; filter: drop-shadow(0 2px 4px rgba(0,0,0,0.08)); z-index: 1; }
.summary-banner-body { flex: 1; min-width: 0; z-index: 1; }
.summary-banner-title { font-size: 13px; font-weight: 700; color: var(--tm-text-primary); margin-bottom: 3px; }
.summary-banner-text { font-size: 12.5px; line-height: 1.55; color: var(--tm-text-secondary); font-weight: 500; }
.summary-banner-empty .summary-banner-text { font-size: 12.5px; font-weight: 400; color: var(--tm-text-secondary); }
.summary-banner-stats { display: flex; gap: 6px; flex-wrap: wrap; margin-top: 6px; }
.summary-banner-stats :deep(.el-tag) {
  font-size: 11.5px; padding: 3px 10px; border-radius: 7px;
  font-weight: 600; border: 1px solid var(--tm-border-light);
  background: var(--tm-card-bg);
}

/* ===== 编辑器表单（核心美化） ===== */
.form-section {
  padding: 12px 0;
  border-bottom: 1px dashed var(--tm-border-light);
}
.form-section:last-child { border-bottom: none; }
.section-hint {
  font-size: 11.5px; color: var(--tm-text-secondary); margin-bottom: 10px;
  display: flex; align-items: flex-start; gap: 5px;
  line-height: 1.55; padding: 8px 10px;
  background: var(--bg-surface-hover);
  border-radius: 7px; border-left: 3px solid var(--accent-primary);
}
.section-hint .el-icon { font-size: 14px; flex-shrink: 0; margin-top: 1px; color: var(--accent-primary); }
.form-group { margin-bottom: 12px; }
.form-group label {
  display: block; font-size: 12px; font-weight: 700; margin-bottom: 5px;
  color: var(--tm-text-primary); letter-spacing: 0.01em;
}
.form-row { display: flex; gap: 10px; }
.form-row .form-group { flex: 1; }
.kv-row { display: flex; gap: 6px; align-items: center; margin-bottom: 6px; }
.form-hint { font-size: 11px; color: var(--tm-text-secondary); margin-bottom: 8px; }
.form-hint code {
  background: linear-gradient(135deg, rgba(var(--tm-color-primary-rgb), 0.1), rgba(var(--tm-color-primary-rgb), 0.08));
  padding: 2px 6px; border-radius: 4px; font-family: 'Consolas','Monaco',monospace;
  font-size: 10.5px; color: var(--tm-color-primary); font-weight: 600;
}
.assertion-teaching {
  padding: 14px 16px;
  background: var(--bg-surface);
  border: 1px solid var(--tm-border-light);
  border-radius: 11px; margin-bottom: 10px;
  box-shadow: inset 0 1px 0 rgba(var(--text-primary-rgb), 0.05);
}
.teaching-title { font-size: 13px; font-weight: 800; color: var(--accent-primary); margin-bottom: 8px; }
.teaching-body { font-size: 11.5px; color: var(--tm-text-secondary); line-height: 1.75; }
.teaching-body p { margin: 5px 0; }
.teaching-body strong { color: var(--tm-text-primary); }
.teaching-table { width: 100%; border-collapse: collapse; margin: 8px 0; font-size: 10.5px; }
.teaching-table td {
  padding: 5px 8px; border: 1px solid var(--tm-border-light);
  vertical-align: top; background: var(--bg-surface-hover);
}
.teaching-table td:first-child { color: var(--accent-primary); white-space: nowrap; width: 95px; font-weight: 700; }
.teaching-table code {
  background: linear-gradient(135deg, rgba(var(--tm-text-secondary-rgb), 0.06), rgba(var(--tm-text-secondary-rgb), 0.04));
  padding: 2px 5px; border-radius: 4px;
  font-family: 'Consolas', monospace; font-size: 10.5px; color: var(--el-color-danger);
  font-weight: 600;
}

/* ===== Step 3 布局：主区域 + 窄侧边栏 ===== */
.step3-layout { display: flex; gap: 0; padding: 0; flex: 1; min-height: 0; overflow: hidden; }
.step3-main { display: flex; flex-direction: column; overflow: hidden; min-width: 0; flex: 1; }
.step3-sidebar {
  display: flex; flex-direction: column; overflow: hidden;
  border: 1px solid var(--tm-border-light); border-radius: 14px;
  background: var(--tm-card-bg);
  box-shadow: 0 2px 12px rgba(0,0,0,0.04);
  min-width: 260px;
}
.step3-sidebar .panel-title { border-bottom: 1px solid var(--tm-border-light); }

.jmx-preview-compact { flex: 1; overflow-y: auto; padding: 12px; }
.xml-preview-compact {
  background: var(--bg-surface);
  border-radius: 8px; padding: 12px; font-size: 10.5px; line-height: 1.5;
  margin: 0; overflow: auto; max-height: 400px;
  color: var(--tm-text-primary); font-family: 'Consolas','Monaco',monospace;
  white-space: pre-wrap; word-break: break-all;
  border: 1px solid var(--tm-border-light);
  box-shadow: inset 0 2px 8px rgba(0,0,0,0.2);
}
.xml-preview-compact code { font-size: 10.5px; }

.debug-body { flex: 1; overflow-y: auto; padding: 10px; }
.debug-meta {
  display: flex; gap: 14px; align-items: center; margin-bottom: 10px; padding: 10px 14px;
  background: linear-gradient(90deg, rgba(var(--el-color-success-rgb), 0.06), transparent);
  border-radius: 9px; border: 1px solid rgba(var(--el-color-success-rgb), 0.12);
}
.debug-elapsed { font-size: 14px; font-weight: 800; color: var(--el-color-success); }
.debug-size { font-size: 12px; color: var(--tm-text-secondary); }
.debug-json {
  background: var(--bg-surface);
  padding: 12px; border-radius: 8px; font-size: 11.5px; color: var(--tm-text-primary);
  font-family: 'Consolas','Monaco',monospace; max-height: 220px; overflow: auto; margin: 0;
  border: 1px solid var(--tm-border-light);
  box-shadow: inset 0 2px 6px rgba(0,0,0,0.15);
}
.debug-error { margin-top: 10px; }
.empty-hint {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  height: 240px; color: var(--tm-text-secondary); gap: 10px; font-size: 13px; text-align: center;
  line-height: 1.6;
}

/* ===== 并发验证（大幅美化） ===== */
.bench-body { padding: 12px; overflow-y: auto; flex: 1; }
.bench-controls { display: flex; gap: 12px; margin-bottom: 14px; }
.bench-controls .form-group { flex: 1; }
.bench-controls .form-group label { display: block; font-size: 12px; font-weight: 700; color: var(--tm-text-primary); margin-bottom: 4px; }
.bench-controls :deep(.el-input-number) { width: 100%; }
.bench-result { margin-top: 8px; }
.bench-progress { margin-bottom: 14px; text-align: center; }
.bench-progress-text { font-size: 12px; color: var(--tm-text-secondary); margin-top: 6px; display: inline-block; font-weight: 500; }

.bench-stats {
  display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin: 10px 0;
}
.bench-stat {
  background: var(--tm-card-bg);
  border-radius: 12px; padding: 14px 10px; text-align: center;
  border: 1px solid var(--tm-border-light);
  box-shadow: 0 2px 8px rgba(0,0,0,0.03);
  position: relative; overflow: hidden;
  transition: transform .2s, box-shadow .2s;
}
.bench-stat:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(0,0,0,0.06); }
.bench-stat::before {
  content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px;
  border-radius: 12px 12px 0 0;
}
.bench-stat:nth-child(1)::before { background: linear-gradient(90deg, var(--tm-color-primary), var(--tm-color-primary)); }
.bench-stat:nth-child(2)::before { background: linear-gradient(90deg, var(--el-color-success), var(--el-color-success)); }
.bench-stat:nth-child(3)::before { background: linear-gradient(90deg, var(--el-color-warning), var(--el-color-warning)); }
.bench-stat:nth-child(4)::before { background: linear-gradient(90deg, var(--tm-color-primary), var(--tm-color-primary)); }
.bench-stat:nth-child(5)::before { background: linear-gradient(90deg, var(--tm-color-primary), var(--tm-color-primary)); }
.bench-stat:nth-child(6)::before { background: linear-gradient(90deg, var(--tm-color-primary), var(--tm-color-primary)); }
.bench-stat:nth-child(7)::before { background: linear-gradient(90deg, var(--el-color-warning), var(--el-color-warning)); }
.bench-stat:nth-child(8)::before { background: linear-gradient(90deg, var(--el-color-success), var(--el-color-success)); }
.bench-stat-value { display: block; font-size: 22px; font-weight: 800; color: var(--tm-text-primary); margin-top: 4px; }
.bench-stat-label { display: block; font-size: 10.5px; color: var(--tm-text-secondary); margin-top: 4px; font-weight: 600; }

.bench-section-title {
  font-size: 14px; font-weight: 800; margin: 16px 0 10px; padding-bottom: 6px;
  border-bottom: 2px solid var(--tm-border-light);
  color: var(--tm-text-primary);
  display: flex; align-items: center; gap: 6px;
}
.bench-data-block { margin-top: 12px; }
.bench-empty-hint {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  padding: 50px 24px; color: var(--tm-text-secondary); gap: 14px; text-align: center; font-size: 13.5px;
  line-height: 1.6;
}
.text-success { color: var(--el-color-success); font-weight: 700; }
.text-danger { color: var(--el-color-danger); font-weight: 700; }

.right-tabs :deep(.el-tabs__content) { overflow: hidden; flex: 1; min-height: 0; }
.right-tabs :deep(.el-tab-pane) { height: 100%; display: flex; flex-direction: column; overflow: hidden; }
.right-tabs :deep(.el-tabs__header) { margin-bottom: 6px; flex-shrink: 0; }

/* ===== 按接口统计（聚合报告） ===== */
.per-url-table { font-size: 12px; }
.per-url-header, .per-url-row {
  display: flex; gap: 6px; padding: 7px 8px;
  border-bottom: 1px solid var(--tm-border-light);
  border-radius: 6px; margin-bottom: 3px;
  transition: background .15s;
}
.per-url-header { font-weight: 800; color: var(--tm-text-secondary); font-size: 11px; background: var(--bg-surface-hover); }
.per-url-row:hover { background: var(--bg-surface-hover); }
.col-url { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-weight: 500; color: var(--tm-text-primary); }
.col-num { width: 60px; text-align: right; flex-shrink: 0; font-weight: 600; font-size: 11.5px; color: var(--tm-text-secondary); }

/* 监听器里的聚合数据表格（兼容主题） */
.per-url-table.theme-table { width: 100%; font-size: 12px; border-collapse: collapse; }
.per-url-table.theme-table th,
.per-url-table.theme-table td { padding: 4px 8px; border-bottom: 1px solid var(--tm-border-light); }
.per-url-table.theme-table thead tr { background: var(--bg-surface-hover); }
.per-url-table.theme-table th { text-align: center; font-weight: 700; color: var(--tm-text-secondary); }
.per-url-table.theme-table td.col-url { max-width: 200px; text-align: left; }
.per-url-table.theme-table td.col-num { text-align: center; }

/* ===== 查看结果树 (VRT) ===== */
.vrt-container { display: flex; gap: 0; border: 1px solid var(--tm-border-light); border-radius: 6px; overflow: hidden; background: var(--tm-card-bg); flex: 1; min-height: 0; }
.vrt-inline-section .vrt-container { }
.vrt-inline-section .vrt-left-col { width: 220px; }
.vrt-left-col { display: flex; flex-direction: column; flex-shrink: 0; width: 280px; border-right: 1px solid var(--tm-border-light); background: var(--bg-surface); overflow: hidden; }
.vrt-sample-list { flex: 1; overflow-y: auto; min-height: 0; }
.vrt-sample-item { display: flex; align-items: center; gap: 6px; padding: 4px 8px; cursor: pointer; transition: background .1s; font-size: 11px; border-bottom: 1px solid var(--tm-border-light); }
.vrt-sample-item:hover { background: var(--bg-surface-hover); }
.vrt-sample-item.active { background: var(--bg-surface-hover); border-left: 3px solid var(--accent-primary); }
.vrt-time { font-weight: 700; width: 52px; flex-shrink: 0; color: var(--tm-text-primary); font-size: 11px; }
.vrt-url { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: var(--tm-text-secondary); font-size: 10px; }
.vrt-name { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: var(--tm-text-primary); font-size: 11px; font-weight: 500; }
.vrt-err { color: var(--el-color-danger); font-size: 10px; flex-shrink: 0; }
.vrt-toolbar { display: flex; flex-wrap: wrap; gap: 4px; padding: 4px 6px; background: var(--bg-surface-hover); border-bottom: 1px solid var(--tm-border-light); align-items: center; flex-shrink: 0; position: sticky; top: 0; z-index: 10; }
.vrt-toolbar-label { font-size: 12px; color: var(--tm-text-primary); white-space: nowrap; flex-shrink: 0; }
.vrt-toolbar .el-checkbox { margin-right: 0; font-size: 11px; height: 24px; }
.vrt-toolbar .el-checkbox__label { font-size: 11px; padding-left: 3px; }
.vrt-detail-panel { flex: 1; display: flex; flex-direction: column; overflow: hidden; min-width: 0; }
.vrt-empty-detail { display: none; color: var(--tm-text-secondary); }
.vrt-tabs { height: 100%; display: flex; flex-direction: column; }
.vrt-tabs :deep(.el-tabs__header) { margin-bottom: 0; background: var(--bg-surface); border-bottom: 1px solid var(--tm-border-light); padding: 0 8px; }
.vrt-tabs :deep(.el-tabs__content) { flex: 1; overflow-y: auto; padding: 8px 12px; }
.vrt-inner-tabs :deep(.el-tabs__header) { margin-bottom: 4px; }
.vrt-inner-tabs :deep(.el-tabs__content) { max-height: calc(100% - 36px); overflow-y: auto; }
.vrt-table { width: 100%; border-collapse: collapse; font-size: 12px; line-height: 1.8; }
.vrt-table td { padding: 2px 8px; border-bottom: 1px solid var(--tm-border-light); vertical-align: top; color: var(--tm-text-primary); }
.vrt-label { color: var(--tm-text-secondary); font-weight: 600; white-space: nowrap; width: 150px; font-family: 'Consolas','Monaco',monospace; font-size: 11px; }
.vrt-subheader td { background: var(--bg-surface-hover); padding: 4px 8px !important; font-size: 11px; }
.indent1 { padding-left: 28px !important; }
.vrt-code { background: var(--bg-surface); padding: 12px; border-radius: 8px; font-size: 11.5px; color: var(--tm-text-primary); font-family: 'Consolas','Monaco',monospace; max-height: 300px; overflow: auto; margin: 0; white-space: pre-wrap; word-break: break-all; border: 1px solid var(--tm-border-light); box-shadow: inset 0 2px 6px rgba(0,0,0,0.12); }
.vrt-error-body { color: var(--el-color-danger); }
.vrt-http-line { padding: 8px 12px; background: rgba(var(--tm-color-primary-rgb), 0.04); border-radius: 6px; margin-top: 6px; font-family: 'Consolas','Monaco',monospace; font-size: 11.5px; word-break: break-all; }
.bench-body-preview {
  background: var(--bg-surface);
  padding: 12px; border-radius: 8px; font-size: 11.5px; color: var(--tm-text-primary);
  font-family: 'Consolas','Monaco',monospace; max-height: 160px; overflow: auto; margin: 0;
  white-space: pre-wrap; word-break: break-all;
  border: 1px solid var(--tm-border-light);
  box-shadow: inset 0 2px 6px rgba(0,0,0,0.15);
}

.empty-state { text-align: center; padding: 36px; color: var(--tm-text-secondary); font-size: 13px; line-height: 1.6; }

.step-body {
  flex: 1; min-height: 0; overflow: hidden; display: flex; flex-direction: column;
  background: var(--bg-surface);
  border-radius: 0 0 14px 14px;
  margin: 0 16px 16px;
  padding: 16px;
}

/* ===== Element Plus 覆盖增强 ===== */
:deep(.el-button--primary) { font-weight: 600; border-radius: 8px; }
:deep(.el-button--success) { font-weight: 600; border-radius: 8px; }
:deep(.el-button--danger) { font-weight: 700; border-radius: 10px; letter-spacing: 0.02em; }
:deep(.el-input__wrapper) { border-radius: 8px; transition: box-shadow .2s; }
:deep(.el-input__wrapper:focus-within) { box-shadow: 0 0 0 2px rgba(var(--tm-color-primary-rgb), 0.2), 0 2px 8px rgba(var(--tm-color-primary-rgb), 0.08) !important; }
:deep(.el-select .el-input__wrapper) { border-radius: 8px; }
:deep(.el-textarea__inner) { border-radius: 8px; font-family: 'Consolas','Monaco',monospace !important; }
:deep(.el-collapse-item__header) { font-weight: 600; font-size: 12.5px; color: var(--tm-text-primary); border-radius: 8px; }
:deep(.el-collapse-item__wrap) { border-radius: 0 0 8px 8px; }
:deep(.el-alert) { border-radius: 10px; border: none; }
:deep(.el-progress-bar__outer) { border-radius: 6px; }
:deep(.el-progress-bar__inner) { border-radius: 6px; }
:deep(.el-tag) { border-radius: 6px; font-weight: 500; }

.vars-panel { padding: 10px 12px; background: var(--bg-surface); border: 1px solid var(--tm-border-light); border-radius: 10px; }
.vars-panel-title { font-size: 12px; font-weight: 700; color: var(--accent-primary); margin-bottom: 8px; }
.vars-chips { display: flex; flex-wrap: wrap; gap: 6px; }
.var-chip { display: inline-flex; align-items: center; padding: 3px 10px; background: var(--tm-card-bg); border: 1px solid var(--tm-border-light); border-radius: 6px; font-size: 11.5px; font-weight: 600; color: var(--accent-primary); cursor: pointer; transition: all .2s; font-family: 'Consolas','Monaco',monospace; }
.var-chip:hover { background: var(--bg-surface-hover); border-color: var(--accent-primary); transform: translateY(-1px); box-shadow: 0 2px 6px rgba(var(--el-color-success-rgb), 0.15); }
.ai-validation { padding: 12px 14px; border-radius: 10px; margin-top: 4px; }
.ai-validation-ok { background: linear-gradient(135deg, rgba(var(--el-color-success-rgb), 0.06), rgba(var(--el-color-success-rgb), 0.03)); border: 1px solid rgba(var(--el-color-success-rgb), 0.2); }
.ai-validation-err { background: linear-gradient(135deg, rgba(var(--el-color-danger-rgb), 0.06), rgba(var(--el-color-danger-rgb), 0.03)); border: 1px solid rgba(var(--el-color-danger-rgb), 0.2); }
.ai-validation-header { font-size: 13px; font-weight: 800; margin-bottom: 4px; }
.ai-validation-ok .ai-validation-header { color: var(--el-color-success); }
.ai-validation-err .ai-validation-header { color: var(--el-color-danger); }
.ai-validation-body { font-size: 12px; color: var(--tm-text-secondary); line-height: 1.7; white-space: pre-wrap; }

.ai-cost-hint {
  font-size: 11px;
  color: var(--accent-primary);
  margin-left: 6px;
  white-space: nowrap;
}

/* ===== 响应式布局优化 ===== */
.import-controls { flex-wrap: wrap; }
.import-controls .el-select { flex-shrink: 0; }
.form-row { flex-wrap: wrap; }
.form-row .form-group { flex: 1; min-width: 120px; }
.kv-row { flex-wrap: wrap; }
.kv-row .el-input { flex: 1; min-width: 80px; }

@media (max-width: 1600px) {
  .step-nav { padding: 12px 16px; gap: 6px; }
  .step { padding: 6px 12px; font-size: 12px; }
  .step-num { width: 24px; height: 24px; font-size: 11px; }
  .step-actions { gap: 6px; }
  .step-actions .el-button { padding-left: 10px; padding-right: 10px; }
  .step-actions .el-button span:not(.el-icon) { display: none; }
  .step-body { margin: 0 12px 12px; padding: 12px; }
  .editor-body { padding: 12px 14px; }
  .summary-banner { padding: 10px 14px; gap: 10px; }
  .summary-banner-icon { font-size: 24px; }
  .summary-banner-title { font-size: 12px; }
  .summary-banner-text { font-size: 11.5px; }
}

@media (max-width: 1366px) {
  .step-nav { flex-wrap: wrap; padding: 10px 14px; }
  .step-actions { margin-left: 0; width: 100%; justify-content: flex-end; padding-top: 8px; border-top: 1px solid var(--tm-border-light); }
  .step { padding: 5px 10px; }
  .step-arrow { font-size: 11px; }
  .step1-left { min-width: 220px; }
  .step1-import { min-width: 300px; }
  .step3-sidebar { min-width: 240px; }
  .bench-stats { grid-template-columns: repeat(2, 1fr); }
  .vrt-bottom-left { width: 260px; }
  .import-controls .el-select { width: 200px !important; }
}

@media (max-width: 1280px) {
  .step1-left { min-width: 200px; }
  .step1-import { min-width: 280px; }
  .step3-sidebar { min-width: 220px; }
  .form-row { gap: 8px; }
  .form-row .form-group { min-width: 100px; }
  .bench-controls { gap: 8px; flex-wrap: wrap; }
  .bench-controls .form-group { min-width: 90px; }
  .vrt-left-col { width: 240px; }
  .vrt-inline-section .vrt-left-col { width: 200px; }
}

@media (max-width: 1024px) {
  .step-body { margin: 0 8px 8px; padding: 10px; }
  .step-nav { padding: 8px 10px; gap: 4px; }
  .step { padding: 4px 8px; font-size: 11px; gap: 4px; }
  .step-num { width: 20px; height: 20px; font-size: 10px; border-radius: 6px; }
  .step-label { display: none; }
  .step-arrow { font-size: 10px; }
  .step-actions { gap: 4px; padding-top: 6px; }
  .step-actions .el-button { padding-left: 8px; padding-right: 8px; }
  .guide-panel { padding: 6px 10px; }

  .step1-layout { flex-direction: column; overflow-y: auto; }
  .step1-layout > .base-splitter--horizontal { display: none; }
  .step1-left { width: 100% !important; flex: none !important; max-height: 35%; min-width: 0 !important; overflow-y: auto; }
  .step1-import { min-width: 0; width: 100%; flex: 1; }

  .step2-editor-layout { flex-direction: column; overflow-y: auto; }
  .step2-editor-layout > .base-splitter--horizontal { display: none; }
  .step2-editor-layout > .tree-panel { width: 100% !important; min-width: 0 !important; max-height: 32%; border-right: none; border-bottom: 1px solid var(--tm-border-light); }
  .step2-editor-layout > .editor-panel { width: 100%; flex: 1; min-height: 0; }

  .step3-layout { flex-direction: column; overflow-y: auto; }
  .step3-layout > .base-splitter--horizontal { display: none; }
  .step3-main { width: 100%; flex: 1; min-height: 0; }
  .step3-sidebar { width: 100% !important; flex: none !important; min-width: 0 !important; max-height: 35%; border-radius: 12px; margin-top: 10px; }

  .vrt-bottom-container { flex-direction: column; height: auto; }
  .vrt-bottom-left { width: 100%; border-right: none; border-bottom: 1px solid var(--tm-border-light); max-height: 40%; }
  .vrt-left-col { width: 220px; }
}

@media (max-width: 768px) {
  .step-nav { padding: 8px; }
  .step-actions { justify-content: center; }
  .step-actions .el-button { padding-left: 6px; padding-right: 6px; }
  .summary-banner { flex-direction: column; align-items: flex-start; gap: 8px; }
  .summary-banner-stats { gap: 4px; }
  .bench-stats { grid-template-columns: 1fr; }
  .bench-controls .form-group { min-width: 80px; }
  .per-url-header, .per-url-row { flex-wrap: wrap; }
  .col-num { width: 50px; }
}
</style>
