<template>
  <div v-show="currentStep === 3" class="step-body">
    <div class="step3-layout">

      <!-- 主区域：并发验证 + 调试 -->
      <div class="step3-main">
        <el-tabs v-model="localRightTab3" class="right-tabs">
          <el-tab-pane label="⚡ 并发验证" name="bench">
            <div class="bench-body">
              <div class="section-hint"><el-icon><InfoFilled /></el-icon> 不依赖 JMeter，直接在平台内验证多个并发能否跑通。设置并发数、持续时间、预热时间，点击下方按钮开始</div>

              <div class="bench-controls">
                <div class="form-group">
                  <label>并发数</label>
                  <el-tooltip content="模拟多少个用户同时访问，如 50 = 50 个虚拟用户同时跑" placement="top">
                    <el-input-number v-model="localBenchConcurrency" :min="1" :max="200" size="small" />
                  </el-tooltip>
                </div>
                <div class="form-group">
                  <label>持续(秒)</label>
                  <el-tooltip content="总共跑多长时间，如 60 = 持续压测 60 秒" placement="top">
                    <el-input-number v-model="localBenchDuration" :min="3" :max="60" size="small" />
                  </el-tooltip>
                </div>
                <div class="form-group">
                  <label>预热(秒)</label>
                  <el-tooltip content="逐步启动的时间，避免瞬间压垮服务。如 5 = 5 秒内逐步启动完所有并发用户" placement="top">
                    <el-input-number v-model="localBenchRampUp" :min="0" :max="10" size="small" />
                  </el-tooltip>
                </div>
              </div>

              <el-button
                v-if="!localBenching"
                type="danger"
                size="large"
                @click="$emit('startBench')"
                style="width:100%;margin-bottom:8px;font-size:15px;font-weight:700"
              >
                ⚡ 开始并发测试（{{ localBenchConcurrency }} 虚拟用户 × {{ localBenchDuration }}秒）
              </el-button>
              <el-button
                v-else
                type="warning"
                size="large"
                @click="$emit('stopBench')"
                style="width:100%;margin-bottom:8px;font-size:15px;font-weight:700"
              >
                ⏹ 停止轮询（测试仍在后台执行）
              </el-button>

              <div v-if="localBenching || benchProgress" class="bench-progress">
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
                  <el-tag
                    v-for="(count, code) in benchResult.status_distribution"
                    :key="code"
                    :type="Number(code) >= 200 && Number(code) < 400 ? 'success' : Number(code) >= 400 || Number(code) === 0 ? 'danger' : 'warning'"
                    size="small"
                  >
                    HTTP {{ code }}: {{ count }}
                  </el-tag>
                </div>

                <!-- 错误信息 -->
                <div v-if="benchResult.errors && benchResult.errors.length > 0" style="margin-top:6px">
                  <el-alert
                    v-for="(err, ei) in benchResult.errors.slice(0, 5)"
                    :key="ei"
                    :title="err"
                    type="error"
                    :closable="false"
                    show-icon
                    style="margin-bottom:2px;font-size:11px"
                  />
                </div>

                <!-- ===== 按接口统计（聚合报告） ===== -->
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

                <!-- ===== 请求详情（查看结果树） ===== -->
                <div v-if="benchResult.samples && benchResult.samples.length > 0" class="bench-data-block">
                  <h4 class="bench-section-title" style="display:flex;justify-content:space-between;align-items:center">
                    🔍 查看结果树
                    <span style="font-size:11px;font-weight:400;color:var(--tm-text-secondary)">共 {{ benchResult.samples.length }} 条样本</span>
                  </h4>
                  <ViewResultsTreePanel
                    :samples="benchResult.samples"
                    v-model:search-query="localSearchQuery"
                    v-model:case-sensitive="localCaseSensitive"
                    v-model:use-regex="localRegex"
                    v-model:status-filter="localStatusFilter"
                    v-model:sample-tab="localSampleTab"
                    v-model:request-tab="localRequestTab"
                    v-model:response-tab="localResponseTab"
                    @sample-select="onSampleSelect"
                    @search="onVrtSearch"
                  />
                </div>

                <!-- ===== 响应体采样 ===== -->
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
              <div v-if="!benchResult && !localBenching && !benchProgress" class="bench-empty-hint">
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
                  <el-tabs v-model="localDebugTab" size="small" class="vrt-tabs">
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
                      <el-tabs v-model="localDebugReqTab" size="small" class="vrt-inner-tabs">
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
                      <el-tabs v-model="localDebugResTab" size="small" class="vrt-inner-tabs">
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
        <div class="panel-title" @click="localShowJmxPreview = !localShowJmxPreview" style="cursor:pointer;user-select:none">
          <span>📦 JMX 导出 {{ localShowJmxPreview ? '▲' : '▼' }}</span>
        </div>
        <div v-if="localShowJmxPreview" class="jmx-preview-compact">
          <div style="display:flex;gap:6px;margin-bottom:6px;flex-wrap:wrap">
            <el-button size="small" @click="$emit('generatePreview')" :loading="generating">
              🔮 生成预览
            </el-button>
            <el-button
              size="small"
              type="success"
              @click="$emit('downloadJmx')"
              :disabled="!jmxContent"
              title="兼容 JMeter 5.1.1 / 5.2 / 5.3 / 5.4 / 5.5 / 5.6"
            >
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
            <el-button size="small" @click="$emit('downloadJmx')" :disabled="!jmxContent" type="success" title="兼容 JMeter 5.1.1 / 5.2 / 5.3 / 5.4 / 5.5 / 5.6">
              <el-icon><Download /></el-icon> 直接下载 .jmx
            </el-button>
            <el-button size="small" @click="localShowJmxPreview = true; $emit('generatePreview')">🔮 预览</el-button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { VideoPlay, InfoFilled, Download } from '@element-plus/icons-vue'
import ViewResultsTreePanel from './ViewResultsTreePanel.vue'

const props = defineProps({
  currentStep: { type: Number, default: 3 },
  benchResult: { type: Object, default: null },
  benching: { type: Boolean, default: false },
  benchProgress: { type: String, default: '' },
  benchPercent: { type: Number, default: 0 },
  benchConcurrency: { type: Number, default: 10 },
  benchDuration: { type: Number, default: 30 },
  benchRampUp: { type: Number, default: 5 },
  jmxContent: { type: String, default: '' },
  generating: { type: Boolean, default: false },
  allSamplers: { type: Array, default: () => [] },
  benchSnapshots: { type: Array, default: () => [] },
  benchHistory: { type: Array, default: () => [] },
  analyzing: { type: Boolean, default: false },
  rightTab3: { type: String, default: 'bench' }
})

const emit = defineEmits([
  'startBench',
  'stopBench',
  'update:benchConcurrency',
  'update:benchDuration',
  'update:benchRampUp',
  'update:rightTab3',
  'doVrtSearch',
  'resetVrtSearch',
  'selectSample',
  'generatePreview',
  'downloadJmx'
])

const localBenchConcurrency = ref(props.benchConcurrency)
const localBenchDuration = ref(props.benchDuration)
const localBenchRampUp = ref(props.benchRampUp)
const localRightTab3 = ref(props.rightTab3)
const localBenching = ref(props.benching)

watch(() => props.benchConcurrency, (val) => { localBenchConcurrency.value = val })
watch(() => props.benchDuration, (val) => { localBenchDuration.value = val })
watch(() => props.benchRampUp, (val) => { localBenchRampUp.value = val })
watch(() => props.rightTab3, (val) => { localRightTab3.value = val })
watch(() => props.benching, (val) => { localBenching.value = val })

watch(localBenchConcurrency, (val) => { emit('update:benchConcurrency', val) })
watch(localBenchDuration, (val) => { emit('update:benchDuration', val) })
watch(localBenchRampUp, (val) => { emit('update:benchRampUp', val) })
watch(localRightTab3, (val) => { emit('update:rightTab3', val) })

const localSearchQuery = ref('')
const localCaseSensitive = ref(false)
const localRegex = ref(false)
const localStatusFilter = ref('')
const localSampleTab = ref('sampler')
const localRequestTab = ref('rbody')
const localResponseTab = ref('resbody')

const localDebugTab = ref('dsampler')
const localDebugReqTab = ref('drbody')
const localDebugResTab = ref('drsbody')
const debugResult = ref(null)

const localShowJmxPreview = ref(false)

function shortUrl(url) {
  try {
    const u = new URL(url)
    return u.pathname + u.search || '/'
  } catch {
    return url.length > 50 ? url.substring(0, 50) + '...' : url
  }
}

function formatHeaders(h) {
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

function formatBody(b) {
  if (!b) return ''
  if (typeof b === 'object') return JSON.stringify(b, null, 2)
  try { return JSON.stringify(JSON.parse(b), null, 2) } catch { return String(b) }
}

function onSampleSelect({ index, sample }) {
  emit('selectSample', { index, sample })
}

function onVrtSearch({ query, caseSensitive, regex }) {
  emit('doVrtSearch', { query, caseSensitive, regex })
}

function doVrtSearch() {
  emit('doVrtSearch', {
    query: localSearchQuery.value,
    caseSensitive: localCaseSensitive.value,
    regex: localRegex.value
  })
}

function resetVrtSearch() {
  localSearchQuery.value = ''
  localCaseSensitive.value = false
  localRegex.value = false
  localStatusFilter.value = ''
  emit('resetVrtSearch')
}

defineExpose({
  debugResult,
  doVrtSearch,
  resetVrtSearch
})
</script>

<style scoped>
.step-body {
  flex: 1;
  min-height: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.step3-layout {
  display: grid;
  grid-template-columns: 1fr 340px;
  gap: 18px;
  padding: 18px;
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

.step3-main {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-width: 0;
}

.step3-sidebar {
  background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
  border: 1px solid rgba(148, 163, 184, 0.12);
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-height: 0;
}

.step3-sidebar .panel-title {
  border-bottom: 1px solid rgba(148, 163, 184, 0.12);
}

.jmx-preview-compact {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
}

.xml-preview-compact {
  background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
  padding: 12px;
  border-radius: 8px;
  max-height: calc(100% - 50px);
  overflow: auto;
  margin: 0;
  font-family: 'Consolas', 'Monaco', monospace;
  white-space: pre-wrap;
  word-break: break-all;
  border: 1px solid rgba(148, 163, 184, 0.1);
  box-shadow: inset 0 2px 6px rgba(0, 0, 0, 0.12);
  font-size: 10.5px;
  color: #e2e8f0;
}

.xml-preview-compact code {
  font-size: 10.5px;
}

.debug-body {
  flex: 1;
  overflow-y: auto;
  padding: 10px;
}

.bench-body {
  padding: 12px;
  overflow-y: auto;
  flex: 1;
}

.bench-controls {
  display: flex;
  gap: 12px;
  margin-bottom: 14px;
}

.bench-controls .form-group {
  flex: 1;
}

.bench-controls .form-group label {
  display: block;
  font-size: 12px;
  font-weight: 700;
  color: #374151;
  margin-bottom: 4px;
}

.bench-controls :deep(.el-input-number) {
  width: 100%;
}

.bench-result {
  margin-top: 8px;
}

.bench-progress {
  margin-bottom: 14px;
  text-align: center;
}

.bench-progress-text {
  font-size: 12px;
  color: #64748b;
  margin-top: 6px;
  display: inline-block;
  font-weight: 500;
}

.bench-stats {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 12px;
  margin-top: 10px;
}

.bench-stat {
  position: relative;
  background: #fff;
  border-radius: 12px;
  padding: 14px 12px;
  text-align: center;
  border: 1px solid #e2e8f0;
  transition: all 0.2s;
}

.bench-stat:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.06);
}

.bench-stat::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  border-radius: 12px 12px 0 0;
}

.bench-stat:nth-child(1)::before {
  background: linear-gradient(90deg, #6366f1, #8b5cf6);
}

.bench-stat:nth-child(2)::before {
  background: linear-gradient(90deg, #10b981, #34d399);
}

.bench-stat:nth-child(3)::before {
  background: linear-gradient(90deg, #f59e0b, #fbbf24);
}

.bench-stat:nth-child(4)::before {
  background: linear-gradient(90deg, #ec4899, #f472b6);
}

.bench-stat:nth-child(5)::before {
  background: linear-gradient(90deg, #06b6d4, #22d3ee);
}

.bench-stat:nth-child(6)::before {
  background: linear-gradient(90deg, #8b5cf6, #a78bfa);
}

.bench-stat:nth-child(7)::before {
  background: linear-gradient(90deg, #f97316, #fb923c);
}

.bench-stat:nth-child(8)::before {
  background: linear-gradient(90deg, #14b8a6, #2dd4bf);
}

.bench-stat-value {
  display: block;
  font-size: 22px;
  font-weight: 800;
  color: #1e293b;
  margin-top: 4px;
}

.bench-stat-label {
  display: block;
  font-size: 10.5px;
  color: #64748b;
  margin-top: 4px;
  font-weight: 600;
}

.bench-section-title {
  font-size: 13px;
  font-weight: 700;
  color: #1e293b;
  margin: 14px 0 6px;
  padding-bottom: 4px;
  border-bottom: 2px solid #e2e8f0;
}

.bench-data-block {
  margin-top: 12px;
}

.bench-empty-hint {
  text-align: center;
  padding: 40px 20px;
  color: #94a3b8;
  font-size: 13px;
  line-height: 1.8;
}

.bench-empty-hint .el-icon {
  color: #cbd5e1;
  margin-bottom: 8px;
}

.right-tabs :deep(.el-tabs__content) {
  overflow: hidden;
  flex: 1;
  min-height: 0;
}

.right-tabs :deep(.el-tab-pane) {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.right-tabs :deep(.el-tabs__header) {
  margin-bottom: 6px;
  flex-shrink: 0;
}

.section-hint {
  font-size: 11px;
  color: #64748b;
  margin-bottom: 10px;
  display: flex;
  align-items: center;
  gap: 4px;
}

.section-hint .el-icon {
  color: #f59e0b;
}

.per-url-table {
  font-size: 12px;
}

.per-url-header {
  display: grid;
  grid-template-columns: 2fr repeat(8, 1fr);
  gap: 4px;
  padding: 6px 8px;
  background: #f1f5f9;
  font-weight: 700;
  color: #475569;
  border-radius: 6px 6px 0 0;
  border-bottom: 2px solid #e2e8f0;
}

.per-url-row {
  display: grid;
  grid-template-columns: 2fr repeat(8, 1fr);
  gap: 4px;
  padding: 5px 8px;
  border-bottom: 1px solid #f1f5f9;
  transition: background 0.1s;
}

.per-url-row:hover {
  background: #f8fafc;
}

.col-url {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: #1e293b;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 11px;
}

.col-num {
  text-align: center;
  color: #374151;
  font-weight: 600;
  font-size: 11px;
}

.text-success {
  color: #10b981;
}

.text-danger {
  color: #ef4444;
}

.bench-body-preview {
  background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
  padding: 12px;
  border-radius: 8px;
  font-size: 11.5px;
  color: #e2e8f0;
  font-family: 'Consolas', 'Monaco', monospace;
  max-height: 160px;
  overflow: auto;
  margin: 0;
  white-space: pre-wrap;
  word-break: break-all;
  border: 1px solid rgba(148, 163, 184, 0.1);
  box-shadow: inset 0 2px 6px rgba(0, 0, 0, 0.15);
}

.empty-hint {
  text-align: center;
  padding: 40px 20px;
  color: #94a3b8;
  font-size: 13px;
  line-height: 1.8;
}

.vrt-container {
  display: flex;
  gap: 0;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  overflow: hidden;
  background: #fff;
  flex: 1;
  min-height: 300px;
  min-height: 0;
}

.vrt-detail-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-width: 0;
}

.vrt-tabs {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.vrt-tabs :deep(.el-tabs__header) {
  margin-bottom: 0;
  background: #f9fafb;
  border-bottom: 1px solid #e5e7eb;
  padding: 0 8px;
}

.vrt-tabs :deep(.el-tabs__content) {
  flex: 1;
  overflow-y: auto;
  padding: 8px 12px;
}

.vrt-inner-tabs :deep(.el-tabs__header) {
  margin-bottom: 4px;
}

.vrt-inner-tabs :deep(.el-tabs__content) {
  max-height: calc(100% - 36px);
  overflow-y: auto;
}

.vrt-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
  line-height: 1.8;
}

.vrt-table td {
  padding: 2px 8px;
  border-bottom: 1px solid #f3f4f6;
  vertical-align: top;
}

.vrt-label {
  color: #6b7280;
  font-weight: 600;
  white-space: nowrap;
  width: 150px;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 11px;
}

.vrt-subheader td {
  background: #f9fafb;
  padding: 4px 8px !important;
  font-size: 11px;
}

.indent1 {
  padding-left: 28px !important;
}

.vrt-code {
  background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
  padding: 12px;
  border-radius: 8px;
  font-size: 11.5px;
  color: #e2e8f0;
  font-family: 'Consolas', 'Monaco', monospace;
  max-height: 300px;
  overflow: auto;
  margin: 0;
  white-space: pre-wrap;
  word-break: break-all;
  border: 1px solid rgba(148, 163, 184, 0.1);
  box-shadow: inset 0 2px 6px rgba(0, 0, 0, 0.12);
}

.vrt-error-body {
  color: #fca5a5;
}

.vrt-http-line {
  padding: 8px 12px;
  background: rgba(99, 102, 241, 0.04);
  border-radius: 6px;
  margin-top: 6px;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 11.5px;
  word-break: break-all;
}

.form-group {
  margin-bottom: 12px;
}

.form-group label {
  display: block;
  font-size: 12px;
  font-weight: 700;
  color: #374151;
  margin-bottom: 4px;
}

:deep(.el-button--primary) {
  font-weight: 600;
  border-radius: 8px;
}

:deep(.el-button--success) {
  font-weight: 600;
  border-radius: 8px;
}

:deep(.el-button--danger) {
  font-weight: 700;
  border-radius: 10px;
  letter-spacing: 0.02em;
}

:deep(.el-input__wrapper) {
  border-radius: 8px;
  transition: box-shadow 0.2s;
}

:deep(.el-input__wrapper:focus-within) {
  box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2), 0 2px 8px rgba(99, 102, 241, 0.08) !important;
}

:deep(.el-select .el-input__wrapper) {
  border-radius: 8px;
}

:deep(.el-textarea__inner) {
  border-radius: 8px;
  font-family: 'Consolas', 'Monaco', monospace !important;
}

:deep(.el-alert) {
  border-radius: 10px;
  border: none;
}

:deep(.el-progress-bar__outer) {
  border-radius: 6px;
}

:deep(.el-progress-bar__inner) {
  border-radius: 6px;
}

:deep(.el-tag) {
  border-radius: 6px;
  font-weight: 500;
}
</style>
