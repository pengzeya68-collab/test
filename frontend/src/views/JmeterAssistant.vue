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
      </div>
    </div>

    <!-- 快速帮助面板 -->
    <el-collapse-transition>
      <div v-if="showGuide" class="guide-panel">
        <el-alert title="JMeter 压测脚本三步搞定" type="info" :closable="false" show-icon>
          <template #default>
            <p style="margin:4px 0"><strong>第1步 · 选择接口</strong> — 从接口库导入 API（推荐），或用模板快速创建脚本</p>
            <p style="margin:4px 0"><strong>第2步 · 配置压测参数</strong> — 设置并发线程数、循环次数、断言、提取器等</p>
            <p style="margin:4px 0"><strong>第3步 · 导出 JMX</strong> — 生成预览并下载 .jmx 文件，兼容 JMeter 5.1.1+</p>
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
      <Step1InterfaceSelector
        :all-cases="allCases"
        :import-groups="importGroups"
        :selected-import-cases="selectedImportCases"
        @apply-template="applyTemplate"
        @open-import-jmx="showImportJmxDialog = true"
        @open-interface-lib="openInterfaceLib"
        @import-selected="importSelectedCases"
        @update:selected-import-cases="selectedImportCases = $event"
        @load-cases="loadCases"
      />
    </div>

    <!-- ==================== Step 2: 配置压测参数 ==================== -->
    <div v-show="currentStep === 2" class="step-body">

      <SummaryBanner
        :script-tree="scriptTree.children"
        :summary-emoji="summaryEmoji"
        :summary-title="summaryTitle"
        :natural-language-summary="naturalLanguageSummary"
        :total-threads="totalThreads"
        :total-samplers="totalSamplers"
        :total-assertions="totalAssertions"
        :total-extractors="totalExtractors"
        :total-timers="totalTimers"
        :total-listeners="totalListeners"
      />

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
          <!-- 左：树 -->
          <TreeEditor
            v-model="scriptTree"
            :selected-uid="selectedUid"
            :total-samplers="totalSamplers"
            :total-nodes="totalNodes"
            :tree-width="treeWidth"
            @select-node="selectNode"
            @add-root-element="addRootElement"
            @add-child="addChildNode"
            @remove-node="removeNodeByUid"
            @duplicate-node="duplicateNode"
          />
          <div class="drag-handle drag-handle-tree" @mousedown="onDragStart('tree', $event)" :class="{ active: draggingCol === 'tree' }"></div>

        <NodeEditor
          :selected-node="selectedNode"
          :node-types="NODE_TYPES"
          :bench-result="benchResult"
          :project-variables="projectVariables"
          :ai-validation-result="aiValidationResult"
          :ai-validating="aiValidating"
          :ai-generating="aiGenerating"
          :debug-loading="debugLoading"
          :saving-to-case="savingToCase"
          :sample-search-query="sampleSearchQuery"
          :search-case-sensitive="searchCaseSensitive"
          :search-regex="searchRegex"
          :sample-status-filter="sampleStatusFilter"
          :selected-sample-idx="selectedSampleIdx"
          :selected-sample-tab="selectedSampleTab"
          :selected-request-tab="selectedRequestTab"
          :selected-response-tab="selectedResponseTab"
          @add-var="addVar"
          @add-header="addHeader"
          @add-child-to-current="addChildToCurrent"
          @add-child-node="addChildNode"
          @debug-request="debugRequest"
          @save-sampler-to-case="saveSamplerToCase"
          @ai-generate-assert="aiGenerateAssert"
          @ai-validate-script="aiValidateScript"
          @insert-variable="insertVariable"
          @add-root-element="addRootElement"
          @goto-step1="currentStep = 1"
          @select-sample="selectedSampleIdx = $event"
          @do-vrt-search="doVrtSearch"
          @reset-vrt-search="resetVrtSearch"
          @update:sample-search-query="sampleSearchQuery = $event"
          @update:search-case-sensitive="searchCaseSensitive = $event"
          @update:search-regex="searchRegex = $event"
          @update:sample-status-filter="sampleStatusFilter = $event"
          @update:selected-sample-tab="selectedSampleTab = $event"
          @update:selected-request-tab="selectedRequestTab = $event"
          @update:selected-response-tab="selectedResponseTab = $event"
        />
        <div class="drag-handle drag-handle-editor" @mousedown="onDragStart('editor', $event)" :class="{ active: draggingCol === 'editor' }"></div>
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
                    <el-tag v-for="(count, code) in benchResult.status_distribution" :key="code" :type="Number(code) >= 200 && Number(code) < 400 ? 'success' : Number(code) >= 400 || Number(code) === 0 ? 'danger' : 'warning'" size="small">
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
                    <h4 class="bench-section-title" style="display:flex;justify-content:space-between;align-items:center">
                      🔍 查看结果树
                      <span style="font-size:11px;font-weight:400;color:var(--tm-text-secondary)">共 {{ benchResult.samples.length }} 条样本</span>
                    </h4>
                    <div class="vrt-container">
                      <div class="vrt-left-col">
                        <div class="vrt-toolbar">
                          <span class="vrt-toolbar-label">查找:</span>
                          <el-input v-model="sampleSearchQuery" size="small" clearable style="width:150px" @keyup.enter="doVrtSearch" />
                          <el-checkbox v-model="searchCaseSensitive" size="small">区分大小写</el-checkbox>
                          <el-checkbox v-model="searchRegex" size="small">正则表达式</el-checkbox>
                          <el-button size="small" type="primary" plain @click="doVrtSearch">查找</el-button>
                          <el-button size="small" @click="resetVrtSearch">重置</el-button>
                          <el-select v-model="sampleStatusFilter" size="small" clearable placeholder="全部" style="width:85px;margin-left:auto">
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
                          <div v-if="filteredSamples.length === 0" style="padding:12px;text-align:center;color:#94a3b8;font-size:12px">无匹配结果</div>
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
              <el-button size="small" type="success" @click="downloadJmx" :disabled="!jmxContent" title="兼容 JMeter 5.1.1 / 5.2 / 5.3 / 5.4 / 5.5 / 5.6">
                <el-icon><Download /></el-icon> 下载 .jmx
              </el-button>
            </div>
            <pre v-if="jmxContent" class="xml-preview-compact"><code>{{ jmxContent }}</code></pre>
            <div v-else class="empty-hint" style="padding:16px;font-size:12px">
              <p>点击「生成预览」<br/>查看 JMX 内容<br/><span style="color:var(--tm-text-secondary);font-size:11px">导出后可导入 JMeter 运行</span></p>
            </div>
          </div>
          <div v-else style="padding:12px;font-size:12px;color:var(--tm-text-secondary)">
            📦 JMX 导出功能：生成 .jmx 文件，兼容 <strong>JMeter 5.1.1+</strong>
            <div style="margin-top:8px;display:flex;gap:6px">
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

  <!-- AI 分析结果弹窗 -->
  <el-dialog
    v-model="aiAnalysisDialogVisible"
    title="🤖 AI 分析报告"
    width="65%"
    :close-on-click-modal="false"
    destroy-on-close
    class="ai-analysis-dialog"
  >
    <div class="ai-analysis-body" style="white-space: pre-wrap; max-height: 70vh; overflow-y: auto; padding: 16px; background: #f8fafc; border-radius: 8px; line-height: 1.8; font-size: 14px;">
      {{ aiAnalysisText }}
    </div>
    <template #footer>
      <el-button @click="aiAnalysisDialogVisible = false">关闭</el-button>
      <el-button type="primary" @click="copyAiAnalysis">📋 复制结果</el-button>
    </template>
  </el-dialog>
  <HelpDrawer v-model="showHelp" :title="helpData.title" :intro="helpData.intro" :sections="helpData.sections" />
</template>

<script setup>
import { ref, reactive, computed, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Refresh, Download, Right, QuestionFilled, VideoPlay, EditPen, FolderDelete, UploadFilled, InfoFilled, Monitor, Connection, Coin, Lollipop, Setting } from '@element-plus/icons-vue'
import autoTestRequest from '@/utils/autoTestRequest'
import request from '@/utils/request'
import BenchRunner from '@/views/jmeter/BenchRunner.vue'
import ScriptHistory from '@/views/jmeter/ScriptHistory.vue'
import TreeEditor from '@/views/jmeter/TreeEditor.vue'
import NodeEditor from '@/components/jmeter/NodeEditor.vue'
import SummaryBanner from '@/components/jmeter/SummaryBanner.vue'
import HelpDrawer from '@/components/HelpDrawer.vue'
import { helpContent } from '@/utils/help-content'

const router = useRouter()

const showHelp = ref(false)
const helpData = helpContent.jmeterAssistant

const benchRunnerRef = ref(null)

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
  InfluxDBBackendListener: { label: 'InfluxDB 后端监听器', icon: '📡', parent: 'TestPlan' },
  UserParameters: { label: '用户参数(多账号)', icon: '👤', parent: 'ThreadGroup' },
  DebugSampler: { label: '调试采样器', icon: '🐛', parent: 'ThreadGroup' },
  ForEachController: { label: 'ForEach 控制器', icon: '🔁', parent: 'ThreadGroup' },
  IncludeController: { label: 'Include 控制器', icon: '📂', parent: 'ThreadGroup' },
  SwitchController: { label: 'Switch 控制器', icon: '🔀', parent: 'ThreadGroup' },
  RandomController: { label: '随机控制器', icon: '🎲', parent: 'ThreadGroup' },
  InterleaveController: { label: '交替控制器', icon: '🔃', parent: 'ThreadGroup' },
  JSONPathAssertion: { label: 'JSON Path 断言', icon: '📋', parent: 'HttpSampler' },
  BoundaryExtractor: { label: '边界提取器', icon: '📐', parent: 'HttpSampler' },
  CSSSelectorExtractor: { label: 'CSS 选择器提取器', icon: '🎨', parent: 'HttpSampler' },
  XPathExtractor: { label: 'XPath 提取器', icon: '🗂️', parent: 'HttpSampler' },
  HttpHeaderManager: { label: 'HTTP 信息头管理器', icon: '📨', parent: 'ThreadGroup' },
  HTTPCookieManager: { label: 'HTTP Cookie 管理器', icon: '🍪', parent: 'ThreadGroup' },
  HttpCacheManager: { label: 'HTTP 缓存管理器', icon: '💾', parent: 'ThreadGroup' },
  HttpAuthManager: { label: 'HTTP 授权管理器', icon: '🔐', parent: 'ThreadGroup' },
  CsvDataSource: { label: 'CSV 数据文件', icon: '📄', parent: 'ThreadGroup' },
  RandomVariableConfig: { label: '随机变量', icon: '🎲', parent: 'ThreadGroup' },
  ModuleController: { label: '模块控制器', icon: '🧩', parent: 'ThreadGroup' },
  RunTimeController: { label: '运行时间控制器', icon: '⏱️', parent: 'ThreadGroup' },
  Summariser: { label: '汇总器', icon: '📊', parent: 'TestPlan' },
  ConstantThroughputTimer: { label: '常数吞吐量定时器', icon: '📈', parent: 'HttpSampler' },
  SynchronizingTimer: { label: '同步定时器', icon: '🔄', parent: 'HttpSampler' },
  PoissonRandomTimer: { label: '泊松随机定时器', icon: '📊', parent: 'HttpSampler' },
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

// ===== 状态持久化 =====
const STORAGE_KEY = 'jmeter_scripts'
const CURRENT_KEY = 'jmeter_current_script'
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

const treeWidth = ref(280)
const draggingCol = ref(null)
const dragStartX = ref(0)
const dragStartW = ref(0)

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

const onDragStart = (col, e) => {
  draggingCol.value = col
  dragStartX.value = e.clientX
  if (col === 'tree') dragStartW.value = treeWidth.value
  document.addEventListener('mousemove', onDragMove)
  document.addEventListener('mouseup', onDragEnd)
  e.preventDefault()
}
const onDragMove = (e) => {
  if (!draggingCol.value) return
  const delta = e.clientX - dragStartX.value
  if (draggingCol.value === 'tree') {
    treeWidth.value = Math.max(180, Math.min(window.innerWidth * 0.55, dragStartW.value + delta))
  }
}
const onDragEnd = () => {
  draggingCol.value = null
  document.removeEventListener('mousemove', onDragMove)
  document.removeEventListener('mouseup', onDragEnd)
}

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
    if (node.type === 'JsonExtractor' || node.type === 'RegexExtractor') {
      if (node.props.varName) vars.push({ name: node.props.varName, source: `${node.name} (${node.type === 'JsonExtractor' ? 'JSON提取' : '正则提取'})` })
    }
    if (node.type === 'CSVDataSet' && node.props.variableNames) {
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
  background: linear-gradient(145deg, #f8fafc 0%, #f1f5f9 50%, #eef2ff 100%);
  color: var(--tm-text-primary);
}

/* ===== 步骤导航 ===== */
.step-nav {
  display: flex; align-items: center; gap: 8px;
  padding: 14px 20px; background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
  border-bottom: 1px solid rgba(148,163,184,0.2);
  box-shadow: 0 1px 3px rgba(0,0,0,0.04), 0 1px 2px rgba(0,0,0,0.06);
  position: sticky; top: 0; z-index: 100;
  flex-shrink: 0;
}
.step { display: flex; align-items: center; gap: 6px; cursor: pointer; padding: 7px 14px; border-radius: 10px; font-size: 13px; color: #64748b; border: 1.5px solid transparent; transition: all .25s ease; font-weight: 500; }
.step:hover { background: rgba(99,102,241,0.05); color: #475569; }
.step.active { color: #4f46e5; border-color: rgba(79,70,229,0.35); background: linear-gradient(135deg, rgba(99,102,241,0.08), rgba(139,92,246,0.06)); box-shadow: 0 2px 8px rgba(79,70,229,0.1); }
.step.done { color: #059669; border-color: rgba(5,150,105,0.25); background: linear-gradient(135deg, rgba(16,185,129,0.08), rgba(5,150,105,0.05)); }
.step-num { width: 26px; height: 26px; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 700; background: linear-gradient(135deg, #e2e8f0, #cbd5e1); color: #64748b; box-shadow: inset 0 -1px 0 rgba(0,0,0,0.06); transition: all .25s ease; }
.step.active .step-num { background: linear-gradient(135deg, #6366f1, #8b5cf6); color: #fff; box-shadow: 0 2px 6px rgba(99,102,241,0.3), inset 0 1px 0 rgba(255,255,255,0.15); }
.step.done .step-num { background: linear-gradient(135deg, #10b981, #059669); color: #fff; box-shadow: 0 2px 6px rgba(16,185,129,0.25), inset 0 1px 0 rgba(255,255,255,0.15); }
.step-arrow { color: #cbd5e1; font-weight: 700; font-size: 13px; }
.step-actions { margin-left: auto; display: flex; gap: 8px; }

/* ===== 引导面板 ===== */
.guide-panel { padding: 8px 20px; }

/* ===== Step 1 布局 ===== */
.step1-layout { display: grid; grid-template-columns: 300px 1fr; gap: 18px; padding: 18px; flex: 1; min-height: 0; overflow: hidden; }
.step1-left { display: flex; flex-direction: column; gap: 12px; overflow-y: auto; }
.step1-templates { overflow: visible; }
.step1-import-jmx { }

/* ===== 面板通用（核心视觉升级） ===== */
.panel {
  background: linear-gradient(180deg, #ffffff 0%, #fafbff 100%);
  border: 1px solid rgba(148,163,184,0.18);
  border-radius: 14px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.03), 0 4px 16px rgba(0,0,0,0.03);
  overflow: hidden;
  display: flex; flex-direction: column;
}
.panel-title {
  display: flex; justify-content: space-between; align-items: center;
  padding: 12px 16px;
  font-weight: 700; font-size: 13px;
  background: linear-gradient(180deg, rgba(248,250,252,0.8) 0%, transparent 100%);
  border-bottom: 1px solid rgba(148,163,184,0.12);
  letter-spacing: 0.01em;
}

.import-jmx-card {
  display: flex; align-items: center; gap: 14px; padding: 16px 18px;
  background: linear-gradient(135deg, #eef2ff 0%, #ede9fe 50%, #fdf4ff 100%);
  border: 1.5px dashed rgba(99,102,241,0.4);
  border-radius: 12px; cursor: pointer; transition: all .3s cubic-bezier(.4,0,.2,1);
  position: relative; overflow: hidden;
}
.import-jmx-card::before {
  content: ''; position: absolute; top: 0; left: 0; right: 0; bottom: 0;
  background: radial-gradient(circle at top right, rgba(99,102,241,0.08) 0%, transparent 60%);
  opacity: 0; transition: opacity .3s;
}
.import-jmx-card:hover::before { opacity: 1; }
.import-jmx-card:hover {
  border-color: #6366f1; border-style: solid;
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(99,102,241,0.15), 0 2px 6px rgba(99,102,241,0.08);
}
.import-jmx-icon { font-size: 30px; flex-shrink: 0; filter: drop-shadow(0 2px 4px rgba(0,0,0,0.1)); }
.import-jmx-body { flex: 1; z-index: 1; }
.import-jmx-title { font-size: 14px; font-weight: 700; color: #334155; }
.import-jmx-desc { font-size: 11.5px; color: #64748b; margin-top: 3px; line-height: 1.5; }
.step1-import { display: flex; flex-direction: column; overflow: hidden; }

.template-grid { display: grid; grid-template-columns: 1fr; gap: 7px; }
.tpl-card {
  padding: 14px 16px;
  border: 1px solid rgba(148,163,184,0.15);
  border-radius: 11px; cursor: pointer; transition: all .28s cubic-bezier(.4,0,.2,1);
  background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
  display: flex; align-items: center; gap: 12px;
  position: relative; overflow: hidden;
}
.tpl-card::after {
  content: ''; position: absolute; left: 0; top: 0; bottom: 0; width: 3px;
  background: linear-gradient(180deg, #6366f1, #8b5cf6);
  border-radius: 0 3px 3px 0; opacity: 0; transition: opacity .25s;
}
.tpl-card:hover {
  border-color: rgba(99,102,241,0.35);
  background: linear-gradient(135deg, #ffffff 0%, #eef2ff 100%);
  transform: translateX(4px);
  box-shadow: 0 4px 14px rgba(99,102,241,0.1);
}
.tpl-card:hover::after { opacity: 1; }
.tpl-icon { font-size: 26px; flex-shrink: 0; filter: drop-shadow(0 2px 3px rgba(0,0,0,0.08)); }
.tpl-name { font-weight: 700; font-size: 13px; margin: 0; color: #1e293b; }
.tpl-desc { font-size: 11px; color: #94a3b8; margin-top: 2px; line-height: 1.4; }

.import-controls { display: flex; gap: 10px; margin-bottom: 14px; }
.import-case-list { flex: 1; overflow-y: auto; padding: 0 4px; }
.import-case-item { padding: 5px 8px; border-radius: 8px; cursor: pointer; transition: all .2s; }
.import-case-item:hover { background: linear-gradient(90deg, rgba(99,102,241,0.06), transparent); }
.case-method { font-size: 11px; font-weight: 800; padding: 2px 7px; border-radius: 5px; margin-right: 8px; letter-spacing: 0.02em; }
.m-get { background: linear-gradient(135deg, rgba(16,185,129,0.15), rgba(5,150,105,0.1)); color: #059669; }
.m-post { background: linear-gradient(135deg, rgba(236,72,153,0.15), rgba(219,39,119,0.1)); color: #db2777; }
.m-put { background: linear-gradient(135deg, rgba(245,158,11,0.15), rgba(217,119,6,0.1)); color: #d97706; }
.m-delete { background: linear-gradient(135deg, rgba(239,68,68,0.15), rgba(220,38,38,0.1)); color: #dc2626; }
.m-patch { background: linear-gradient(135deg, rgba(129,140,248,0.15), rgba(99,102,241,0.1)); color: #6366f1; }
.case-name { font-size: 13px; font-weight: 600; color: #334155; }
.case-url { font-size: 11px; color: #94a3b8; margin-left: 8px; }

.import-footer {
  display: flex; justify-content: space-between; align-items: center;
  padding: 14px 16px 0; border-top: 1px solid rgba(148,163,184,0.12); margin-top: 10px;
}
.import-count { font-size: 12.5px; color: #64748b; font-weight: 500; }

/* ===== Step 2 布局 ===== */
.step2-layout {
  display: flex; flex-direction: column;
  flex: 1; min-height: 0; overflow: hidden;
}
.step2-layout > .bench-control-panel {
  margin: 0; border-radius: 0; border-left: none; border-right: none;
  flex-shrink: 0;
}
.step2-layout > .bench-control-panel.expanded {
  height: auto; flex: 1; min-height: 0;
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
  background: rgba(148,163,184,0.2); border-radius: 2px; transition: background .2s;
}
.drag-handle:hover, .drag-handle.active { background: rgba(99,102,241,0.06); }
.drag-handle:hover::after, .drag-handle.active::after { background: rgba(99,102,241,0.5); height: 48px; }
.editor-panel { display: flex; flex-direction: column; overflow: hidden; min-height: 0; }
.editor-body {
  flex: 1; overflow-y: auto; padding: 16px 18px;
  scrollbar-width: thin; scrollbar-color: rgba(148,163,184,0.2) transparent;
}
.editor-body::-webkit-scrollbar { width: 6px; }
.editor-body::-webkit-scrollbar-thumb { background: rgba(148,163,184,0.2); border-radius: 3px; }
.editor-empty {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  flex: 1; color: #94a3b8; gap: 12px;
}
.editor-empty p { font-size: 13.5px; line-height: 1.6; max-width: 200px; text-align: center; }
.editor-empty .el-icon { color: #cbd5e1; filter: drop-shadow(0 2px 4px rgba(0,0,0,0.06)); }
.editor-empty-tips { display: flex; gap: 10px; margin-top: 8px; }
.empty-tip { padding: 6px 14px; border-radius: 8px; font-size: 12px; font-weight: 600; cursor: pointer; background: rgba(99,102,241,0.06); border: 1px solid rgba(99,102,241,0.15); color: #6366f1; transition: all .2s; }
.empty-tip:hover { background: rgba(99,102,241,0.12); transform: translateY(-1px); box-shadow: 0 2px 8px rgba(99,102,241,0.1); }

/* ===== 底部运行结果面板 ===== */
.bottom-result-panel {
  background: #fff;
  border-top: 1px solid rgba(148,163,184,0.2);
  transition: height 0.2s ease;
  display: flex; flex-direction: column;
  flex-shrink: 0;
}
.bottom-result-panel.collapsed { height: 36px; }
.brp-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 6px 16px; cursor: pointer; user-select: none;
  background: linear-gradient(180deg, #f8fafc, #f1f5f9);
  border-bottom: 1px solid rgba(148,163,184,0.12);
  flex-shrink: 0;
}
.brp-header:hover { background: #eef2ff; }
.brp-title { font-weight: 700; font-size: 13px; color: #1e293b; }
.brp-header-right { display: flex; align-items: center; gap: 10px; }
.brp-badge { font-size: 11px; color: #64748b; background: #f1f5f9; padding: 2px 8px; border-radius: 10px; }
.brp-badge.brp-running { color: #f59e0b; background: #fef3c7; animation: pulse 2s infinite; }
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
  width: 40px; height: 3px; background: rgba(148,163,184,0.3); border-radius: 2px;
}
.brp-resize-handle:hover::after { background: rgba(99,102,241,0.5); }

/* 底部面板内的 VRT 布局 */
.vrt-bottom-container {
  display: flex; gap: 0; height: calc(100% - 40px);
  overflow: hidden;
}
.vrt-bottom-left {
  width: 320px; flex-shrink: 0; border-right: 1px solid rgba(148,163,184,0.12);
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
  color: #94a3b8; font-size: 13px;
}

/* 底部面板统计 */
.bottom-result-panel .mini-stats { display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 10px; padding: 8px 10px; background: linear-gradient(135deg, rgba(99,102,241,0.04), rgba(139,92,246,0.02)); border-radius: 8px; border: 1px solid rgba(148,163,184,0.1); }
.bottom-result-panel .mini-stats > div { display: flex; flex-direction: column; align-items: center; gap: 2px; min-width: 40px; }
.bottom-result-panel .mini-stats b { font-size: 14px; color: #1e293b; }
.bottom-result-panel .mini-stats small { font-size: 10px; color: #94a3b8; }
.bottom-result-panel .bench-progress-inline { margin-bottom: 10px; font-size: 11px; color: #64748b; }

/* ===== 自然语言概要 Banner（Step 2 顶部） ===== */
.summary-banner {
  display: flex; align-items: flex-start; gap: 14px;
  padding: 12px 16px; margin: 0 18px 8px;
  border-radius: 12px;
  background: linear-gradient(135deg, rgba(99,102,241,0.09) 0%, rgba(139,92,246,0.06) 40%, rgba(168,85,247,0.04) 100%);
  border: 1px solid rgba(99,102,241,0.18);
  box-shadow: 0 4px 16px rgba(99,102,241,0.06), inset 0 1px 0 rgba(255,255,255,0.5);
  position: relative; overflow: hidden;
  flex-shrink: 0;
}
.summary-banner::before {
  content: ''; position: absolute; top: -30px; right: -30px;
  width: 120px; height: 120px; border-radius: 50%;
  background: radial-gradient(circle, rgba(99,102,241,0.1) 0%, transparent 70%);
}
.summary-banner-empty {
  background: linear-gradient(135deg, rgba(241,245,249,0.9), rgba(248,250,252,0.8));
  border-color: rgba(148,163,184,0.18);
  box-shadow: none;
}
.summary-banner-empty::before { display: none; }
.summary-banner-icon { font-size: 28px; line-height: 1; flex-shrink: 0; margin-top: 2px; filter: drop-shadow(0 2px 4px rgba(0,0,0,0.08)); z-index: 1; }
.summary-banner-body { flex: 1; min-width: 0; z-index: 1; }
.summary-banner-title { font-size: 13px; font-weight: 700; color: #1e293b; margin-bottom: 3px; }
.summary-banner-text { font-size: 12.5px; line-height: 1.55; color: #475569; font-weight: 500; }
.summary-banner-empty .summary-banner-text { font-size: 12.5px; font-weight: 400; color: #64748b; }
.summary-banner-stats { display: flex; gap: 6px; flex-wrap: wrap; margin-top: 6px; }
.summary-banner-stats :deep(.el-tag) {
  font-size: 11.5px; padding: 3px 10px; border-radius: 7px;
  font-weight: 600; border: 1px solid rgba(99,102,241,0.15);
  background: rgba(255,255,255,0.7);
}

/* ===== 编辑器表单（核心美化） ===== */
.form-section {
  padding: 12px 0;
  border-bottom: 1px dashed rgba(148,163,184,0.12);
}
.form-section:last-child { border-bottom: none; }
.section-hint {
  font-size: 11.5px; color: #64748b; margin-bottom: 10px;
  display: flex; align-items: flex-start; gap: 5px;
  line-height: 1.55; padding: 8px 10px;
  background: linear-gradient(90deg, rgba(99,102,241,0.04), transparent);
  border-radius: 7px; border-left: 3px solid rgba(99,102,241,0.25);
}
.section-hint .el-icon { font-size: 14px; flex-shrink: 0; margin-top: 1px; color: #6366f1; }
.form-group { margin-bottom: 12px; }
.form-group label {
  display: block; font-size: 12px; font-weight: 700; margin-bottom: 5px;
  color: #374151; letter-spacing: 0.01em;
}
.form-row { display: flex; gap: 10px; }
.form-row .form-group { flex: 1; }
.kv-row { display: flex; gap: 6px; align-items: center; margin-bottom: 6px; }
.form-hint { font-size: 11px; color: #6b7280; margin-bottom: 8px; }
.form-hint code {
  background: linear-gradient(135deg, rgba(99,102,241,0.1), rgba(139,92,246,0.08));
  padding: 2px 6px; border-radius: 4px; font-family: 'Consolas','Monaco',monospace;
  font-size: 10.5px; color: #6366f1; font-weight: 600;
}
.assertion-teaching {
  padding: 14px 16px;
  background: linear-gradient(135deg, rgba(99,102,241,0.04) 0%, rgba(139,92,246,0.03) 100%);
  border: 1px solid rgba(99,102,241,0.14);
  border-radius: 11px; margin-bottom: 10px;
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.5);
}
.teaching-title { font-size: 13px; font-weight: 800; color: #4f46e5; margin-bottom: 8px; }
.teaching-body { font-size: 11.5px; color: #475569; line-height: 1.75; }
.teaching-body p { margin: 5px 0; }
.teaching-body strong { color: #1e293b; }
.teaching-table { width: 100%; border-collapse: collapse; margin: 8px 0; font-size: 10.5px; }
.teaching-table td {
  padding: 5px 8px; border: 1px solid rgba(148,163,184,0.12);
  vertical-align: top; background: rgba(255,255,255,0.4);
}
.teaching-table td:first-child { color: #4f46e5; white-space: nowrap; width: 95px; font-weight: 700; }
.teaching-table code {
  background: linear-gradient(135deg, rgba(30,41,59,0.06), rgba(51,65,85,0.04));
  padding: 2px 5px; border-radius: 4px;
  font-family: 'Consolas', monospace; font-size: 10.5px; color: #dc2626;
  font-weight: 600;
}

/* ===== Step 3 布局：主区域 + 窄侧边栏 ===== */
.step3-layout { display: grid; grid-template-columns: 1fr 340px; gap: 18px; padding: 18px; flex: 1; min-height: 0; overflow: hidden; }
.step3-main { display: flex; flex-direction: column; overflow: hidden; min-width: 0; }
.step3-sidebar {
  display: flex; flex-direction: column; overflow: hidden;
  border: 1px solid rgba(148,163,184,0.18); border-radius: 14px;
  background: linear-gradient(180deg, #ffffff 0%, #fafbff 100%);
  box-shadow: 0 2px 12px rgba(0,0,0,0.04);
}
.step3-sidebar .panel-title { border-bottom: 1px solid rgba(148,163,184,0.12); }

.jmx-preview-compact { flex: 1; overflow-y: auto; padding: 12px; }
.xml-preview-compact {
  background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
  border-radius: 8px; padding: 12px; font-size: 10.5px; line-height: 1.5;
  margin: 0; overflow: auto; max-height: 400px;
  color: #e2e8f0; font-family: 'Consolas','Monaco',monospace;
  white-space: pre-wrap; word-break: break-all;
  border: 1px solid rgba(148,163,184,0.1);
  box-shadow: inset 0 2px 8px rgba(0,0,0,0.2);
}
.xml-preview-compact code { font-size: 10.5px; }

.debug-body { flex: 1; overflow-y: auto; padding: 10px; }
.debug-meta {
  display: flex; gap: 14px; align-items: center; margin-bottom: 10px; padding: 10px 14px;
  background: linear-gradient(90deg, rgba(16,185,129,0.06), transparent);
  border-radius: 9px; border: 1px solid rgba(16,185,129,0.12);
}
.debug-elapsed { font-size: 14px; font-weight: 800; color: #059669; }
.debug-size { font-size: 12px; color: #64748b; }
.debug-json {
  background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
  padding: 12px; border-radius: 8px; font-size: 11.5px; color: #e2e8f0;
  font-family: 'Consolas','Monaco',monospace; max-height: 220px; overflow: auto; margin: 0;
  border: 1px solid rgba(148,163,184,0.1);
  box-shadow: inset 0 2px 6px rgba(0,0,0,0.15);
}
.debug-error { margin-top: 10px; }
.empty-hint {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  height: 240px; color: #94a3b8; gap: 10px; font-size: 13px; text-align: center;
  line-height: 1.6;
}

/* ===== 并发验证（大幅美化） ===== */
.bench-body { padding: 12px; overflow-y: auto; flex: 1; }
.bench-controls { display: flex; gap: 12px; margin-bottom: 14px; }
.bench-controls .form-group { flex: 1; }
.bench-controls .form-group label { display: block; font-size: 12px; font-weight: 700; color: #374151; margin-bottom: 4px; }
.bench-controls :deep(.el-input-number) { width: 100%; }
.bench-result { margin-top: 8px; }
.bench-progress { margin-bottom: 14px; text-align: center; }
.bench-progress-text { font-size: 12px; color: #64748b; margin-top: 6px; display: inline-block; font-weight: 500; }

.bench-stats {
  display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin: 10px 0;
}
.bench-stat {
  background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
  border-radius: 12px; padding: 14px 10px; text-align: center;
  border: 1px solid rgba(148,163,184,0.15);
  box-shadow: 0 2px 8px rgba(0,0,0,0.03);
  position: relative; overflow: hidden;
  transition: transform .2s, box-shadow .2s;
}
.bench-stat:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(0,0,0,0.06); }
.bench-stat::before {
  content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px;
  border-radius: 12px 12px 0 0;
}
.bench-stat:nth-child(1)::before { background: linear-gradient(90deg, #6366f1, #8b5cf6); }
.bench-stat:nth-child(2)::before { background: linear-gradient(90deg, #10b981, #34d399); }
.bench-stat:nth-child(3)::before { background: linear-gradient(90deg, #f59e0b, #fbbf24); }
.bench-stat:nth-child(4)::before { background: linear-gradient(90deg, #ec4899, #f472b6); }
.bench-stat:nth-child(5)::before { background: linear-gradient(90deg, #06b6d4, #22d3ee); }
.bench-stat:nth-child(6)::before { background: linear-gradient(90deg, #8b5cf6, #a78bfa); }
.bench-stat:nth-child(7)::before { background: linear-gradient(90deg, #f97316, #fb923c); }
.bench-stat:nth-child(8)::before { background: linear-gradient(90deg, #14b8a6, #2dd4bf); }
.bench-stat-value { display: block; font-size: 22px; font-weight: 800; color: #1e293b; margin-top: 4px; }
.bench-stat-label { display: block; font-size: 10.5px; color: #64748b; margin-top: 4px; font-weight: 600; }

.bench-section-title {
  font-size: 14px; font-weight: 800; margin: 16px 0 10px; padding-bottom: 6px;
  border-bottom: 2px solid rgba(99,102,241,0.12);
  color: #1e293b;
  display: flex; align-items: center; gap: 6px;
}
.bench-data-block { margin-top: 12px; }
.bench-empty-hint {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  padding: 50px 24px; color: #94a3b8; gap: 14px; text-align: center; font-size: 13.5px;
  line-height: 1.6;
}
.text-success { color: #059669; font-weight: 700; }
.text-danger { color: #dc2626; font-weight: 700; }

.right-tabs :deep(.el-tabs__content) { overflow: hidden; flex: 1; min-height: 0; }
.right-tabs :deep(.el-tab-pane) { height: 100%; display: flex; flex-direction: column; overflow: hidden; }
.right-tabs :deep(.el-tabs__header) { margin-bottom: 6px; flex-shrink: 0; }

/* ===== 按接口统计（聚合报告） ===== */
.per-url-table { font-size: 12px; }
.per-url-header, .per-url-row {
  display: flex; gap: 6px; padding: 7px 8px;
  border-bottom: 1px solid rgba(148,163,184,0.1);
  border-radius: 6px; margin-bottom: 3px;
  transition: background .15s;
}
.per-url-header { font-weight: 800; color: #64748b; font-size: 11px; background: rgba(248,250,252,0.8); }
.per-url-row:hover { background: rgba(99,102,241,0.04); }
.col-url { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-weight: 500; color: #334155; }
.col-num { width: 60px; text-align: right; flex-shrink: 0; font-weight: 600; font-size: 11.5px; }

/* ===== 查看结果树 (VRT) ===== */
.vrt-container { display: flex; gap: 0; border: 1px solid #d1d5db; border-radius: 6px; overflow: hidden; background: #fff; flex: 1; min-height: 300px; min-height: 0; }
.vrt-inline-section .vrt-container { min-height: 260px; }
.vrt-inline-section .vrt-left-col { width: 220px; }
.vrt-left-col { display: flex; flex-direction: column; flex-shrink: 0; width: 280px; border-right: 1px solid #ccc; background: #f5f5f5; overflow: hidden; min-height: 0; }
.vrt-sample-list { flex: 1; overflow-y: auto; min-height: 0; }
.vrt-sample-item { display: flex; align-items: center; gap: 6px; padding: 4px 8px; cursor: pointer; transition: background .1s; font-size: 11px; border-bottom: 1px solid #f3f4f6; }
.vrt-sample-item:hover { background: #eff6ff; }
.vrt-sample-item.active { background: #dbeafe; border-left: 3px solid #3b82f6; }
.vrt-time { font-weight: 700; width: 52px; flex-shrink: 0; color: #374151; font-size: 11px; }
.vrt-url { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: #6b7280; font-size: 10px; }
.vrt-name { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: #1f2937; font-size: 11px; font-weight: 500; }
.vrt-err { color: #dc2626; font-size: 10px; flex-shrink: 0; }
.vrt-toolbar { display: flex; flex-wrap: wrap; gap: 4px; padding: 4px 6px; background: #e8eaed; border-bottom: 1px solid #ccc; align-items: center; flex-shrink: 0; position: sticky; top: 0; z-index: 10; }
.vrt-toolbar-label { font-size: 12px; color: #333; white-space: nowrap; flex-shrink: 0; }
.vrt-toolbar .el-checkbox { margin-right: 0; font-size: 11px; height: 24px; }
.vrt-toolbar .el-checkbox__label { font-size: 11px; padding-left: 3px; }
.vrt-detail-panel { flex: 1; display: flex; flex-direction: column; overflow: hidden; min-width: 0; }
.vrt-empty-detail { display: none; }
.vrt-tabs { height: 100%; display: flex; flex-direction: column; }
.vrt-tabs :deep(.el-tabs__header) { margin-bottom: 0; background: #f9fafb; border-bottom: 1px solid #e5e7eb; padding: 0 8px; }
.vrt-tabs :deep(.el-tabs__content) { flex: 1; overflow-y: auto; padding: 8px 12px; }
.vrt-inner-tabs :deep(.el-tabs__header) { margin-bottom: 4px; }
.vrt-inner-tabs :deep(.el-tabs__content) { max-height: calc(100% - 36px); overflow-y: auto; }
.vrt-table { width: 100%; border-collapse: collapse; font-size: 12px; line-height: 1.8; }
.vrt-table td { padding: 2px 8px; border-bottom: 1px solid #f3f4f6; vertical-align: top; }
.vrt-label { color: #6b7280; font-weight: 600; white-space: nowrap; width: 150px; font-family: 'Consolas','Monaco',monospace; font-size: 11px; }
.vrt-subheader td { background: #f9fafb; padding: 4px 8px !important; font-size: 11px; }
.indent1 { padding-left: 28px !important; }
.vrt-code { background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%); padding: 12px; border-radius: 8px; font-size: 11.5px; color: #e2e8f0; font-family: 'Consolas','Monaco',monospace; max-height: 300px; overflow: auto; margin: 0; white-space: pre-wrap; word-break: break-all; border: 1px solid rgba(148,163,184,0.1); box-shadow: inset 0 2px 6px rgba(0,0,0,0.12); }
.vrt-error-body { color: #fca5a5; }
.vrt-http-line { padding: 8px 12px; background: rgba(99,102,241,0.04); border-radius: 6px; margin-top: 6px; font-family: 'Consolas','Monaco',monospace; font-size: 11.5px; word-break: break-all; }
.bench-body-preview {
  background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
  padding: 12px; border-radius: 8px; font-size: 11.5px; color: #e2e8f0;
  font-family: 'Consolas','Monaco',monospace; max-height: 160px; overflow: auto; margin: 0;
  white-space: pre-wrap; word-break: break-all;
  border: 1px solid rgba(148,163,184,0.1);
  box-shadow: inset 0 2px 6px rgba(0,0,0,0.15);
}

.empty-state { text-align: center; padding: 36px; color: #94a3b8; font-size: 13px; line-height: 1.6; }

.step-body { flex: 1; min-height: 0; overflow: hidden; display: flex; flex-direction: column; }

/* ===== Element Plus 覆盖增强 ===== */
:deep(.el-button--primary) { font-weight: 600; border-radius: 8px; }
:deep(.el-button--success) { font-weight: 600; border-radius: 8px; }
:deep(.el-button--danger) { font-weight: 700; border-radius: 10px; letter-spacing: 0.02em; }
:deep(.el-input__wrapper) { border-radius: 8px; transition: box-shadow .2s; }
:deep(.el-input__wrapper:focus-within) { box-shadow: 0 0 0 2px rgba(99,102,241,0.2), 0 2px 8px rgba(99,102,241,0.08) !important; }
:deep(.el-select .el-input__wrapper) { border-radius: 8px; }
:deep(.el-textarea__inner) { border-radius: 8px; font-family: 'Consolas','Monaco',monospace !important; }
:deep(.el-collapse-item__header) { font-weight: 600; font-size: 12.5px; color: #374151; border-radius: 8px; }
:deep(.el-collapse-item__wrap) { border-radius: 0 0 8px 8px; }
:deep(.el-alert) { border-radius: 10px; border: none; }
:deep(.el-progress-bar__outer) { border-radius: 6px; }
:deep(.el-progress-bar__inner) { border-radius: 6px; }
:deep(.el-tag) { border-radius: 6px; font-weight: 500; }

.vars-panel { padding: 10px 12px; background: linear-gradient(135deg, rgba(16,185,129,0.04), rgba(5,150,105,0.02)); border: 1px solid rgba(16,185,129,0.15); border-radius: 10px; }
.vars-panel-title { font-size: 12px; font-weight: 700; color: #059669; margin-bottom: 8px; }
.vars-chips { display: flex; flex-wrap: wrap; gap: 6px; }
.var-chip { display: inline-flex; align-items: center; padding: 3px 10px; background: rgba(255,255,255,0.8); border: 1px solid rgba(16,185,129,0.2); border-radius: 6px; font-size: 11.5px; font-weight: 600; color: #059669; cursor: pointer; transition: all .2s; font-family: 'Consolas','Monaco',monospace; }
.var-chip:hover { background: rgba(16,185,129,0.1); border-color: #059669; transform: translateY(-1px); box-shadow: 0 2px 6px rgba(16,185,129,0.15); }
.ai-validation { padding: 12px 14px; border-radius: 10px; margin-top: 4px; }
.ai-validation-ok { background: linear-gradient(135deg, rgba(16,185,129,0.06), rgba(5,150,105,0.03)); border: 1px solid rgba(16,185,129,0.2); }
.ai-validation-err { background: linear-gradient(135deg, rgba(239,68,68,0.06), rgba(220,38,38,0.03)); border: 1px solid rgba(239,68,68,0.2); }
.ai-validation-header { font-size: 13px; font-weight: 800; margin-bottom: 4px; }
.ai-validation-ok .ai-validation-header { color: #059669; }
.ai-validation-err .ai-validation-header { color: #dc2626; }
.ai-validation-body { font-size: 12px; color: #475569; line-height: 1.7; white-space: pre-wrap; }
</style>
