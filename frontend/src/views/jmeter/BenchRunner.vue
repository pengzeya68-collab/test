<template>
  <div class="bench-control-panel" :class="{ expanded: benchPanelExpanded, running: benching }">
    <!-- Header: 始终显示,但运行时简化 -->
    <div class="bcp-header" @click="benchPanelExpanded = !benchPanelExpanded">
      <div class="bcp-header-left">
        <span class="bcp-plan-name">{{ planName }}</span>
        <el-tag size="small" type="info">{{ totalSamplers }} 请求 · {{ totalNodes }} 元素</el-tag>
        <el-tag v-if="totalThreads" size="small" effect="plain">👥 {{ totalThreads }} 线程</el-tag>
      </div>

      <!-- 配置项: 仅在未运行时显示 -->
      <div v-if="!benching && !benchResult" class="bcp-header-center">
        <div class="bcp-config-item">
          <label>并发数</label>
          <el-input-number v-model="benchConcurrency" :min="1" :max="200" size="small" controls-position="right" style="width:90px" />
        </div>
        <div class="bcp-config-item">
          <label>持续(秒)</label>
          <el-input-number v-model="benchDuration" :min="3" :max="60" size="small" controls-position="right" style="width:90px" />
        </div>
        <div class="bcp-config-item">
          <label>预热(秒)</label>
          <el-input-number v-model="benchRampUp" :min="0" :max="10" size="small" controls-position="right" style="width:90px" />
        </div>
      </div>

      <!-- 运行中: 显示进度 -->
      <div v-if="benching" class="bcp-header-center">
        <div class="bcp-progress-inline">
          <el-progress :percentage="benchPercent" :stroke-width="6" :status="benchPercent >= 100 ? 'success' : ''" style="width:200px" />
          <span class="bcp-progress-text">{{ benchProgress }} {{ benchEta }}</span>
        </div>
      </div>

      <div class="bcp-header-right">
        <el-button v-if="!benching" type="danger" @click.stop="startBench" size="default" class="bcp-start-btn">
          ⚡ 启动压测（{{ benchConcurrency }}并发 × {{ benchDuration }}秒）
        </el-button>
        <el-button v-else :icon="SwitchButton" @click.stop="stopBench" size="default" type="danger">停止</el-button>

        <!-- 结果操作按钮 -->
        <el-button v-if="benchResult && !analyzing" size="small" type="primary" plain @click.stop="analyzeBenchResult">🤖 AI 分析</el-button>
        <span v-if="getCostText('bench_ai_analysis')" class="ai-cost-hint">{{ getCostText('bench_ai_analysis') }}</span>
        <el-button v-if="analyzing" size="small" type="warning" plain loading @click.stop>分析中...</el-button>
        <el-button v-if="benchResult" size="small" type="success" plain @click.stop="exportReport">📄 导出报告</el-button>

        <el-button size="default" @click.stop="showBenchHistory = !showBenchHistory">
          📋 历史{{ benchHistory.length > 0 ? '(' + benchHistory.length + ')' : '' }}
        </el-button>
        <el-icon class="bcp-toggle-icon" :class="{ rotate: benchPanelExpanded }"><ArrowDown /></el-icon>
      </div>
    </div>

    <!-- 展开内容区 -->
    <div class="bcp-body" v-show="benchPanelExpanded">
      <!-- 压测接口标签 -->
      <div class="bcp-requests" v-if="allSamplers.length > 0">
        <span class="bcp-requests-label">压测接口：</span>
        <el-tag v-for="(s, si) in allSamplers" :key="si" size="small" effect="plain" type="info" class="bcp-req-tag" :title="s.url">
          <b>{{ s.method }}</b> {{ s.name }}
        </el-tag>
      </div>

      <!-- 实时图表(运行中显示) -->
      <div v-if="benchSnapshots.length > 0" class="bcp-charts">
        <div class="bcp-charts-row">
          <div class="bcp-chart-card"><div class="bpu-header"> TPS/QPS 实时曲线</div><div ref="benchChartRef" class="bcp-chart-box"></div></div>
          <div class="bcp-chart-card"><div class="bpu-header">️ 响应时间趋势</div><div ref="benchChartRef2" class="bcp-chart-box"></div></div>
        </div>
        <div class="bcp-charts-row">
          <div class="bcp-chart-card"><div class="bpu-header">📊 状态码分布</div><div ref="benchChartRef3" class="bcp-chart-box"></div></div>
          <div class="bcp-chart-card"><div class="bpu-header">🎯 各接口成功率</div><div ref="benchChartRef4" class="bcp-chart-box"></div></div>
        </div>
      </div>

      <!-- AI分析横幅 -->
      <el-alert v-if="analyzing" title="🤖 AI 正在深度分析性能数据..." type="info" :closable="false" show-icon class="bcp-analyze-banner">
        <template #default><p style="margin:0;font-size:12px;color:#94a3b8;">正在分析性能数据，请耐心等待...</p></template>
      </el-alert>

      <!-- 压测结果区域(完成后显示) -->
      <div v-if="benchResult" class="bcp-report-section">
        <!-- 统计指标栏 -->
        <div class="bcp-quick-stats">
          <div class="bcp-stat" :class="benchResult.failed > 0 ? 'bcp-stat-err' : 'bcp-stat-ok'">
            <span class="bcp-stat-val">{{ benchResult.total }}</span>
            <span class="bcp-stat-lbl">总请求</span>
          </div>
          <div class="bcp-stat bcp-stat-ok">
            <span class="bcp-stat-val">{{ benchResult.success }}</span>
            <span class="bcp-stat-lbl">成功</span>
          </div>
          <div class="bcp-stat" :class="benchResult.failed > 0 ? 'bcp-stat-err' : ''">
            <span class="bcp-stat-val">{{ benchResult.failed }}</span>
            <span class="bcp-stat-lbl">失败</span>
          </div>
          <div class="bcp-stat">
            <span class="bcp-stat-val">{{ benchResult.tps }}</span>
            <span class="bcp-stat-lbl">TPS</span>
          </div>
          <div class="bcp-stat">
            <span class="bcp-stat-val">{{ benchResult.avg_ms }}ms</span>
            <span class="bcp-stat-lbl">平均</span>
          </div>
          <div class="bcp-stat">
            <span class="bcp-stat-val">{{ benchResult.min_ms || '-' }}ms</span>
            <span class="bcp-stat-lbl">最小</span>
          </div>
          <div class="bcp-stat">
            <span class="bcp-stat-val">{{ benchResult.max_ms || '-' }}ms</span>
            <span class="bcp-stat-lbl">最大</span>
          </div>
          <div class="bcp-stat">
            <span class="bcp-stat-val">{{ benchResult.p50_ms || '-' }}ms</span>
            <span class="bcp-stat-lbl">P50</span>
          </div>
          <div class="bcp-stat">
            <span class="bcp-stat-val">{{ benchResult.p90_ms || '-' }}ms</span>
            <span class="bcp-stat-lbl">P90</span>
          </div>
          <div class="bcp-stat">
            <span class="bcp-stat-val">{{ benchResult.p95_ms }}ms</span>
            <span class="bcp-stat-lbl">P95</span>
          </div>
          <div class="bcp-stat">
            <span class="bcp-stat-val">{{ benchResult.p99_ms }}ms</span>
            <span class="bcp-stat-lbl">P99</span>
          </div>
          <div class="bcp-stat">
            <span class="bcp-stat-val">{{ benchResult.stddev_ms || '-' }}ms</span>
            <span class="bcp-stat-lbl">标准差</span>
          </div>
        </div>

        <!-- 按接口统计表格 -->
        <div v-if="benchResult.per_url && benchResult.per_url.length > 0" class="bcp-per-url">
          <div class="bpu-header">📊 按接口统计</div>
          <div class="bpu-table-wrapper">
            <table class="bpu-table">
              <thead><tr><th>接口</th><th>总次数</th><th>成功</th><th>失败</th><th>成功率</th><th>平均(ms)</th><th>P95(ms)</th><th>P99(ms)</th><th>最小(ms)</th><th>最大(ms)</th></tr></thead>
              <tbody>
                <tr v-for="(pu, pi) in benchResult.per_url" :key="pi" :class="pu.failed > 0 ? 'bpu-row-err' : ''">
                  <td class="bpu-url" :title="pu.url"><b>{{ pu.method || 'GET' }}</b> {{ pu.name || pu.url }}</td>
                  <td>{{ pu.count }}</td><td class="bpu-ok">{{ pu.success }}</td>
                  <td :class="pu.failed > 0 ? 'bpu-err' : ''">{{ pu.failed }}</td>
                  <td><span :class="pu.success_rate < 100 ? 'bpu-err' : 'bpu-ok'">{{ pu.success_rate }}%</span></td>
                  <td>{{ pu.avg_ms }}</td><td>{{ pu.p95_ms }}</td><td>{{ pu.p99_ms }}</td>
                  <td>{{ pu.min_ms || '-' }}</td><td>{{ pu.max_ms || '-' }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- 状态码分布 -->
        <div v-if="benchResult.status_distribution" class="bcp-status-dist">
          <div class="bpu-header">状态码分布</div>
          <div class="bsd-tags">
            <el-tag v-for="(count, code) in benchResult.status_distribution" :key="code" :type="code >= 200 && code < 400 ? 'success' : 'danger'" size="small" effect="plain">{{ code }}: {{ count }}次</el-tag>
          </div>
        </div>

        <!-- 响应时间分布 -->
        <div v-if="benchResult.rt_distribution" class="bcp-rt-dist">
          <div class="bpu-header">响应时间分布</div>
          <div class="rt-dist-bars">
            <div v-for="(count, range) in benchResult.rt_distribution" :key="range" class="rt-dist-bar">
              <div class="rt-dist-label">{{ range }}</div>
              <div class="rt-dist-track"><div class="rt-dist-fill" :style="{ width: (count / Math.max(...Object.values(benchResult.rt_distribution), 1) * 100) + '%' }"></div></div>
              <div class="rt-dist-count">{{ count }}</div>
            </div>
          </div>
        </div>

        <!-- 吞吐量趋势 -->
        <div v-if="benchResult.throughput_trend && benchResult.throughput_trend.length > 0" class="bcp-throughput">
          <div class="bpu-header">吞吐量趋势 (5秒窗口)</div>
          <div class="tp-table">
            <table><thead><tr><th>时间(s)</th><th>TPS</th><th>请求数</th><th>趋势</th></tr></thead>
              <tbody><tr v-for="(tp, ti) in benchResult.throughput_trend" :key="ti">
                <td>{{ tp.t }}-{{ tp.t + 5 }}</td><td>{{ tp.tps }}</td><td>{{ tp.count }}</td>
                <td><div class="tp-bar"><div class="tp-fill" :style="{ width: (tp.tps / Math.max(...benchResult.throughput_trend.map(t => t.tps), 1) * 100) + '%' }"></div></div></td>
              </tr></tbody>
            </table>
          </div>
        </div>

        <!-- 响应体采样 -->
        <div v-if="benchResult.body_samples && benchResult.body_samples.length > 0" class="bcp-body-samples">
          <div class="bpu-header">📄 响应体采样 (前 {{ Math.min(benchResult.body_samples.length, 10) }} 条)
            <span style="font-size:11px;font-weight:400;color:var(--tm-text-secondary)">最多 1000 字符</span>
          </div>
          <div class="bcp-samples-scroll">
            <div v-for="(bs, bi) in benchResult.body_samples.slice(0, 10)" :key="bi" class="bcp-sample-card">
              <div class="bcp-sample-header">
                <el-tag :type="bs.status >= 200 && bs.status < 400 ? 'success' : 'danger'" size="small">{{ bs.status }}</el-tag>
                <span class="bcp-sample-url" :title="bs.url">{{ shortUrl(bs.url) }}</span>
              </div>
              <pre class="bcp-sample-body">{{ bs.body }}</pre>
            </div>
          </div>
        </div>

        <!-- 错误详情 -->
        <div v-if="benchResult.errors && benchResult.errors.length > 0" class="bcp-errors-section">
          <el-collapse v-model="errorCollapseActive">
            <el-collapse-item name="errors">
              <template #title>
                <span class="bcp-errors-title"> 错误详情 ({{ benchResult.errors.length }})</span>
              </template>
              <div class="bcp-errors-list">
                <div v-for="(err, ei) in benchResult.errors.slice(0, 20)" :key="ei" class="bcp-error-item">
                  <div class="bcp-error-header">
                    <span class="bcp-error-name">{{ err.name || err.url || '未知接口' }}</span>
                    <el-tag size="small" type="danger">{{ err.method || 'GET' }}</el-tag>
                    <span class="bcp-error-status">状态: {{ err.status || 0 }}</span>
                    <span class="bcp-error-time">{{ err.elapsed_ms || 0 }}ms</span>
                  </div>
                  <div class="bcp-error-msg">{{ err.error || err.response_message || err }}</div>
                  <div v-if="err.request_body" class="bcp-error-req"><details><summary>📤 请求体</summary><pre>{{ err.request_body.substring(0, 500) }}</pre></details></div>
                  <div v-if="err.response_body" class="bcp-error-res"><details><summary>📥 响应体</summary><pre>{{ err.response_body.substring(0, 1000) }}</pre></details></div>
                </div>
                <div v-if="benchResult.errors.length > 20" class="bcp-error-more">... 还有 {{ benchResult.errors.length - 20 }} 条错误</div>
              </div>
            </el-collapse-item>
          </el-collapse>
        </div>
      </div>
    </div>
  </div>

  <!-- 历史面板 -->
  <div v-if="showBenchHistory && benchHistory.length > 0" class="bench-history-panel">
    <div class="bh-header">
      <span>📋 执行历史 ({{ benchHistory.length }})</span>
      <el-button link size="small" @click="benchHistory = []; showBenchHistory = false">清空全部</el-button>
    </div>
    <div class="bh-list">
      <div v-for="(h, hi) in benchHistory" :key="hi" class="bh-item" @click="restoreHistoryResult(h)">
        <span class="bh-time">{{ h.time }}</span><span class="bh-name">{{ h.planName }}</span>
        <span class="bh-total">{{ h.total }}次</span><span class="bh-tps">{{ h.tps }}TPS</span>
        <span :class="h.failed > 0 ? 'bh-err' : 'bh-ok'">{{ h.failed }}失败</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, onBeforeUnmount, onMounted, shallowRef } from 'vue'
import { ElMessage } from 'element-plus'
import { SwitchButton, ArrowDown } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import autoTestRequest from '@/utils/autoTestRequest'
import { useAICosts } from '@/composables/useAICosts'
import { useUserStore } from '@/stores/user'

const props = defineProps({
  scriptTree: { type: Object, required: true },
  planName: { type: String, default: '' },
  totalSamplers: { type: Number, default: 0 },
  totalNodes: { type: Number, default: 0 },
  totalThreads: { type: Number, default: 0 },
  allSamplers: { type: Array, default: () => [] },
})

const benchConcurrency = ref(10)
const benchDuration = ref(10)
const benchRampUp = ref(2)
const benchResult = ref(null)
const benchProgress = ref('')
const benchPercent = ref(0)
const benchEta = computed(() => {
  if (!benchPercent.value || benchPercent.value >= 100) return ''
  const remainingSec = Math.ceil(benchDuration.value * (100 - benchPercent.value) / 100)
  return remainingSec > 0 ? `剩余约${remainingSec}秒` : ''
})
const benchTaskId = ref(null)
const benching = ref(false)
const runStatus = ref('idle')
const showBenchHistory = ref(false)
const userStore = useUserStore()
const { fetchCosts, getCostText, getCost } = useAICosts()
const _uid = computed(() => userStore.userId || 'anon')
const BENCH_HISTORY_KEY = computed(() => `benchHistory_${_uid.value}`)
const benchHistory = ref(JSON.parse(localStorage.getItem(BENCH_HISTORY_KEY.value) || '[]'))
const analyzing = ref(false)
const aiAnalysisText = ref('')
const aiAnalysisDialogVisible = ref(false)
const errorCollapseActive = ref([])
const benchPanelExpanded = ref(false)
const benchChartRef = ref(null)
const benchChartRef2 = ref(null)
const benchChartRef3 = ref(null)
const benchChartRef4 = ref(null)
const benchChartInstance = shallowRef(null)
const benchChartInstance2 = shallowRef(null)
const benchChartInstance3 = shallowRef(null)
const benchChartInstance4 = shallowRef(null)
const benchSnapshots = ref([])
const benchStartTime = ref(null)
let benchPollTimer = null
let benchRetryCount = 0

const shortUrl = (url) => {
  try { const u = new URL(url); return u.pathname + u.search || '/' } catch { return url.length > 50 ? url.substring(0, 50) + '...' : url }
}

const startBench = async () => {
  const samplers = []
  const walk = (node) => {
    if (node.type === 'HttpSampler') {
      const headers = {}
      ;(node.props.headers || []).forEach(h => { if (h.key) headers[h.key] = h.value })
      samplers.push({ name: node.name, method: node.props.method || 'GET', url: node.props.url, headers, body: node.props.method !== 'GET' ? (node.props.body || '') : '' })
    }
    ;(node.children || []).forEach(walk)
  }
  walk(props.scriptTree)
  if (samplers.length === 0) { ElMessage.warning('脚本中没有 HTTP 请求'); return }
  if (benchPollTimer) { clearInterval(benchPollTimer); benchPollTimer = null }
  benching.value = true; runStatus.value = 'running'; benchStartTime.value = new Date()
  benchResult.value = null; benchProgress.value = '提交任务...'; benchPercent.value = 0
  benchTaskId.value = null; benchRetryCount = 0; benchSnapshots.value = []
  try {
    const res = await autoTestRequest.post('/auto-test/jmeter/quick-bench', { requests: samplers, concurrency: benchConcurrency.value, duration: benchDuration.value, ramp_up: benchRampUp.value })
    benchTaskId.value = res.task_id; benchProgress.value = '任务已提交，正在执行...'
    benchPollTimer = setInterval(pollBench, 1500)
  } catch (e) {
    ElMessage.error('提交失败: ' + (e.response?.data?.detail || e.message))
    benchProgress.value = ''; benchPercent.value = 0; runStatus.value = ''; benching.value = false; benchResult.value = null
  }
}

const pollBench = async () => {
  if (!benchTaskId.value) return
  try {
    const res = await autoTestRequest.get(`/auto-test/jmeter/quick-bench/${benchTaskId.value}`)
    benchRetryCount = 0; benchProgress.value = res.progress || ''; benchPercent.value = res.percent || 0
    if (res.snapshots && res.snapshots.length > 0) { benchSnapshots.value = res.snapshots; updateAllBenchCharts() }
    if (res.status === 'done') {
      if (benchPollTimer) { clearInterval(benchPollTimer); benchPollTimer = null }
      benchResult.value = res.result; benchSnapshots.value = res.snapshots || []; updateAllBenchCharts()
      benching.value = false; runStatus.value = 'idle'
      if (res.result.failed > 0) { ElMessage.warning(`并发测试完成：${res.result.total} 请求，${res.result.failed} 失败`) }
      else { ElMessage.success(`并发测试通过！${res.result.total} 请求全部成功，TPS ${res.result.tps}`) }
      saveBenchHistory(res.result)
    }
  } catch (e) {
    benchRetryCount++
    if (benchRetryCount >= 3) { if (benchPollTimer) { clearInterval(benchPollTimer); benchPollTimer = null }; benching.value = false; benchRetryCount = 0; ElMessage.error('查询失败: ' + (e.response?.data?.detail || e.message)) }
  }
}

const stopBench = async () => {
  if (benchPollTimer) { clearInterval(benchPollTimer); benchPollTimer = null }
  benching.value = false; runStatus.value = 'idle'
  if (benchTaskId.value) { try { await autoTestRequest.post('/auto-test/bench/stop', { task_id: benchTaskId.value }) } catch (e) { console.warn('停止压测任务失败:', e) } }
  ElMessage.info('已停止')
}

const saveBenchHistory = (result) => {
  const entry = { time: new Date().toLocaleString(), planName: props.planName || '未命名', concurrency: benchConcurrency.value, duration: benchDuration.value, total: result.total, success: result.success, failed: result.failed, tps: result.tps, avg_ms: result.avg_ms, p95_ms: result.p95_ms, p99_ms: result.p99_ms, min_ms: result.min_ms, max_ms: result.max_ms, p50_ms: result.p50_ms, p90_ms: result.p90_ms, stddev_ms: result.stddev_ms, rt_distribution: result.rt_distribution, throughput_trend: result.throughput_trend, body_samples: result.body_samples, statusDistribution: result.status_distribution, perUrl: result.per_url, errors: result.errors, samples: result.samples }
  benchHistory.value.unshift(entry)
  if (benchHistory.value.length > 50) benchHistory.value = benchHistory.value.slice(0, 50)
  try { localStorage.setItem(BENCH_HISTORY_KEY.value, JSON.stringify(benchHistory.value)) } catch (e) { benchHistory.value.pop(); try { localStorage.setItem(BENCH_HISTORY_KEY.value, JSON.stringify(benchHistory.value)) } catch (e2) {} }
}

const initAllBenchCharts = () => {
  const refs = [benchChartRef, benchChartRef2, benchChartRef3, benchChartRef4]
  const instances = [benchChartInstance, benchChartInstance2, benchChartInstance3, benchChartInstance4]
  refs.forEach((r, i) => { if (!r.value) return; if (instances[i].value) instances[i].value.dispose(); instances[i].value = echarts.init(r.value) })
}

const updateAllBenchCharts = () => {
  if (!benchPanelExpanded.value) return
  const snaps = benchSnapshots.value
  if (!snaps || snaps.length === 0) return
  const times = snaps.map(s => s.t + 's')
  const tpsData = snaps.map(s => s.tps)
  const avgData = snaps.map(s => s.avg)
  const errData = snaps.map(s => s.errors)

  const chart1 = benchChartInstance.value
  if (chart1) {
    chart1.setOption({ tooltip: { trigger: 'axis', backgroundColor: 'rgba(15,23,42,0.9)', borderColor: '#334155', textStyle: { color: '#f1f5f9', fontSize: 12 }, formatter: (params) => { let tip = `<b style="color:#e2e8f0">${params[0]?.axisValue || ''}</b><br/>`; params.forEach(p => { tip += `${p.marker} ${p.seriesName}: <b>${p.value}</b><br/>` }); return tip } }, legend: { data: ['TPS', '累计错误'], bottom: 0, textStyle: { fontSize: 10, color: '#64748b' } }, grid: { top: 10, right: 50, bottom: 30, left: 50 }, xAxis: { type: 'category', data: times, axisLabel: { fontSize: 9, color: '#94a3b8', interval: Math.max(Math.floor(times.length / 10), 0) }, axisLine: { lineStyle: { color: '#e2e8f0' } } }, yAxis: [{ type: 'value', name: 'TPS', nameTextStyle: { fontSize: 10, color: '#3b82f6' }, axisLabel: { fontSize: 9, color: '#94a3b8' }, splitLine: { lineStyle: { color: '#f1f5f9' } } }, { type: 'value', name: '错误数', nameTextStyle: { fontSize: 10, color: '#ef4444' }, axisLabel: { fontSize: 9, color: '#94a3b8' }, splitLine: { show: false } }], series: [{ name: 'TPS', type: 'bar', data: tpsData, itemStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: '#60a5fa' }, { offset: 1, color: '#3b82f6' }]), borderRadius: [2, 2, 0, 0] }, barMaxWidth: 16 }, { name: '累计错误', type: 'line', yAxisIndex: 1, data: errData, step: 'end', lineStyle: { color: '#ef4444', width: 1.5, type: 'dashed' }, itemStyle: { color: '#ef4444' }, symbol: 'none' }] }, true)
  }
  const chart2 = benchChartInstance2.value
  if (chart2) {
    chart2.setOption({ tooltip: { trigger: 'axis', backgroundColor: 'rgba(15,23,42,0.9)', borderColor: '#334155', textStyle: { color: '#f1f5f9', fontSize: 12 }, formatter: (params) => { let tip = `<b style="color:#e2e8f0">${params[0]?.axisValue || ''}</b><br/>`; params.forEach(p => { tip += `${p.marker} ${p.seriesName}: <b>${p.value}ms</b><br/>` }); return tip } }, legend: { data: ['平均响应', 'P95响应', 'P99响应'], bottom: 0, textStyle: { fontSize: 10, color: '#64748b' } }, grid: { top: 10, right: 20, bottom: 30, left: 50 }, xAxis: { type: 'category', data: times, axisLabel: { fontSize: 9, color: '#94a3b8', interval: Math.max(Math.floor(times.length / 10), 0) }, axisLine: { lineStyle: { color: '#e2e8f0' } } }, yAxis: { type: 'value', name: 'ms', nameTextStyle: { fontSize: 10, color: '#64748b' }, axisLabel: { fontSize: 9, color: '#94a3b8' }, splitLine: { lineStyle: { color: '#f1f5f9' } } }, series: [{ name: '平均响应', type: 'line', data: avgData, smooth: true, lineStyle: { color: '#f59e0b', width: 2 }, itemStyle: { color: '#f59e0b' }, symbol: 'circle', symbolSize: 3, areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: 'rgba(245,158,11,0.3)' }, { offset: 1, color: 'rgba(245,158,11,0.02)' }]) } }, { name: 'P95响应', type: 'line', data: snaps.map(s => s.p95 || 0), smooth: true, lineStyle: { color: '#ef4444', width: 1.5, type: 'dashed' }, itemStyle: { color: '#ef4444' }, symbol: 'none' }, { name: 'P99响应', type: 'line', data: snaps.map(s => s.p99 || 0), smooth: true, lineStyle: { color: '#dc2626', width: 1, type: 'dotted' }, itemStyle: { color: '#dc2626' }, symbol: 'none' }] }, true)
  }
  const chart3 = benchChartInstance3.value
  if (chart3 && benchResult.value && benchResult.value.status_distribution) {
    const dist = benchResult.value.status_distribution
    const pieData = Object.entries(dist).map(([code, count]) => ({ name: `${code}`, value: count }))
    chart3.setOption({ tooltip: { trigger: 'item', backgroundColor: 'rgba(15,23,42,0.9)', borderColor: '#334155', textStyle: { color: '#f1f5f9', fontSize: 12 }, formatter: '{b}: {c}次 ({d}%)' }, legend: { orient: 'vertical', right: 10, top: 'center', textStyle: { fontSize: 10, color: '#64748b' } }, series: [{ type: 'pie', radius: ['40%', '70%'], center: ['40%', '50%'], avoidLabelOverlap: true, itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 }, label: { show: true, fontSize: 10, formatter: '{b}\n{d}%' }, emphasis: { label: { show: true, fontSize: 12, fontWeight: 'bold' }, itemStyle: { shadowBlur: 10, shadowOffsetX: 0, shadowColor: 'rgba(0,0,0,0.2)' } }, data: pieData, color: ['#10b981', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6', '#6b7280'] }] }, true)
  }
  const chart4 = benchChartInstance4.value
  if (chart4 && benchResult.value && benchResult.value.per_url && benchResult.value.per_url.length > 0) {
    const perUrl = benchResult.value.per_url; const names = perUrl.map(pu => pu.name || pu.url); const rates = perUrl.map(pu => pu.success_rate)
    chart4.setOption({ tooltip: { trigger: 'axis', backgroundColor: 'rgba(15,23,42,0.9)', borderColor: '#334155', textStyle: { color: '#f1f5f9', fontSize: 12 }, formatter: (params) => { const p = params[0]; return `${p.name}<br/>成功率: <b>${p.value}%</b>` } }, grid: { top: 5, right: 20, bottom: 5, left: 120 }, xAxis: { type: 'value', max: 100, axisLabel: { fontSize: 9, color: '#94a3b8', formatter: '{value}%' }, splitLine: { lineStyle: { color: '#f1f5f9' } } }, yAxis: { type: 'category', data: names, axisLabel: { fontSize: 9, color: '#64748b', width: 100, overflow: 'truncate' }, axisLine: { lineStyle: { color: '#e2e8f0' } } }, series: [{ type: 'bar', data: rates.map((r) => ({ value: r, itemStyle: { color: r >= 100 ? '#10b981' : r >= 90 ? '#f59e0b' : '#ef4444', borderRadius: [0, 4, 4, 0] } })), barMaxWidth: 20, label: { show: true, position: 'right', fontSize: 10, formatter: '{c}%', color: '#64748b' } }] }, true)
  }
}

const resizeAllBenchCharts = () => { [benchChartInstance, benchChartInstance2, benchChartInstance3, benchChartInstance4].forEach(inst => { if (inst.value && benchPanelExpanded.value) inst.value.resize() }) }

const restoreHistoryResult = (h) => {
  benchResult.value = { total: h.total, success: h.success, failed: h.failed, tps: h.tps, avg_ms: h.avg_ms, min_ms: h.min_ms || 0, max_ms: h.max_ms || 0, p50_ms: h.p50_ms || 0, p95_ms: h.p95_ms, p99_ms: h.p99_ms, status_distribution: h.statusDistribution, per_url: h.perUrl, errors: h.errors, samples: h.samples || [] }
  benching.value = false; showBenchHistory.value = false
}

let analyzingMsg = null
const analyzeBenchResult = async () => {
  if (!benchResult.value) return
  analyzing.value = true; aiAnalysisText.value = ''
  analyzingMsg = ElMessage({ message: '🤖 AI正在深度分析... 正在将性能数据发送给大模型', type: 'info', duration: 0, showClose: true, icon: 'Loading', customClass: 'analyzing-toast' })
  try {
    const res = await autoTestRequest.post('/auto-test/analyze-result', { plan_name: props.planName || '未命名', concurrency: benchConcurrency.value, duration: benchDuration.value, result: { total: benchResult.value.total, success: benchResult.value.success, failed: benchResult.value.failed, tps: benchResult.value.tps, avg_ms: benchResult.value.avg_ms, p50_ms: benchResult.value.p50_ms, p95_ms: benchResult.value.p95_ms, p99_ms: benchResult.value.p99_ms, min_ms: benchResult.value.min_ms, max_ms: benchResult.value.max_ms, status_distribution: benchResult.value.status_distribution, per_url: benchResult.value.per_url, errors: benchResult.value.errors } })
    aiAnalysisText.value = res.analysis || '分析完成，但无内容返回'; aiAnalysisDialogVisible.value = true; ElMessage.success('AI 分析完成')
  } catch (e) { ElMessage.error('AI 分析失败: ' + (e.response?.data?.detail || e.message)) }
  finally { analyzing.value = false; if (analyzingMsg) { analyzingMsg.close(); analyzingMsg = null } }
}

const exportReport = async () => {
  if (!benchResult.value) return
  const r = benchResult.value; const planName = props.planName || '未命名'; const now = new Date()
  const testStart = benchStartTime.value && benchStartTime.value < now ? benchStartTime.value : new Date(now.getTime() - benchDuration.value * 1000)
  const scenarios = (r.per_url || []).map(pu => ({ name: pu.name || pu.url || '未命名接口', url: pu.url || '', method: pu.method || 'GET', target_qps: 0, actual_qps: pu.count > 0 && benchDuration.value > 0 ? Math.round(pu.count / benchDuration.value * 10) / 10 : 0, concurrency: benchConcurrency.value, threads: benchConcurrency.value, ramp_up: benchRampUp.value, loops: 1, duration: benchDuration.value, avg_ms: pu.avg_ms || 0, p50_ms: pu.p50_ms || 0, p90_ms: pu.p90_ms || 0, p95_ms: pu.p95_ms || 0, p99_ms: pu.p99_ms || 0, stddev_ms: pu.stddev_ms || 0, max_ms: pu.max_ms || 0, min_ms: pu.min_ms || 0, error_rate: pu.count > 0 ? ((pu.failed || 0) / pu.count * 100) : 0, total_requests: pu.count || 0, failed_requests: pu.failed || 0, result: pu.failed === 0 ? '通过' : '失败', test_start: testStart.toLocaleString(), test_end: now.toLocaleString() }))
  if (scenarios.length === 0 || (scenarios.length === 1 && !scenarios[0].url)) { scenarios.push({ name: planName, url: '', method: 'GET', target_qps: 0, actual_qps: r.tps || 0, concurrency: benchConcurrency.value, threads: benchConcurrency.value, ramp_up: benchRampUp.value, loops: 1, duration: benchDuration.value, avg_ms: r.avg_ms || 0, p50_ms: r.p50_ms || 0, p90_ms: r.p90_ms || 0, p95_ms: r.p95_ms || 0, p99_ms: r.p99_ms || 0, stddev_ms: r.stddev_ms || 0, max_ms: r.max_ms || 0, min_ms: r.min_ms || 0, error_rate: r.total > 0 ? ((r.failed / r.total) * 100) : 0, total_requests: r.total || 0, failed_requests: r.failed || 0, result: r.failed === 0 ? '通过' : '失败', test_start: testStart.toLocaleString(), test_end: now.toLocaleString() }) }
  const errorTypes = {}
  if (r.errors && r.errors.length > 0) { r.errors.forEach(e => { let msg = typeof e === 'object' ? (e.response_message || e.message || e.error || '未知错误') : String(e); if (msg.includes('Cannot connect to host')) { const match = msg.match(/Cannot connect to host\s+([a-zA-Z0-9.-]+)/); if (match) { msg = `连接失败: ${match[1].split(':')[0]}` } else { msg = '连接失败' } } else if (msg.includes('ssl:default') || msg.includes('SSL')) { msg = 'SSL连接错误' } else if (msg.startsWith('https://') || msg.startsWith('http://')) { try { msg = `请求失败: ${new URL(msg).hostname}` } catch { const m = msg.match(/https?:\/\/([a-zA-Z0-9.-]+)/); msg = m ? `请求失败: ${m[1]}` : msg.substring(0, 40) + '...' } } else if (msg.includes('timeout') || msg.includes('Timeout')) { msg = '请求超时' } else if (msg.includes('500') || msg.includes('Internal Server Error')) { msg = '服务器错误 (500)' } else if (msg.includes('404') || msg.includes('Not Found')) { msg = '资源不存在 (404)' } else if (msg.includes('403') || msg.includes('Forbidden')) { msg = '权限拒绝 (403)' } else if (msg.includes('401') || msg.includes('Unauthorized')) { msg = '未授权 (401)' } else if (msg.includes('ECONNREFUSED') || msg.includes('Connection refused')) { msg = '连接被拒绝' } else if (msg.includes('ECONNRESET') || msg.includes('Connection reset')) { msg = '连接重置' } else if (msg.includes('ENOTFOUND') || msg.includes('Name or service not known')) { msg = 'DNS解析失败' }; const key = msg.length > 50 ? msg.substring(0, 47) + '...' : msg; errorTypes[key] = (errorTypes[key] || 0) + 1 }) }
  try {
    ElMessage.info('正在生成专业 Word 报告...')
    const res = await autoTestRequest.post('/auto-test/report/generate', { report_name: planName + '_性能测试报告', test_env: { domain: props.scriptTree.props?.variables?.find(v => v.name === 'HOST')?.value || '未指定', env_name: '压测环境' }, author: localStorage.getItem('tm_username') || 'TestMaster', env_config: { 'CPU': '8核', '内存': '16GB', '操作系统': 'Linux (Docker)', '压测工具': 'TestMaster (JMeter引擎)', '网络环境': '内网', '并发模型': `线程数: ${benchConcurrency.value}, 持续时间: ${benchDuration.value}s` }, scenarios, summary: { total_requests: r.total, total_failed: r.failed, overall_error_rate: r.total > 0 ? ((r.failed / r.total) * 100).toFixed(2) : '0', overall_result: r.failed === 0 ? '通过' : '失败', notes: aiAnalysisText.value ? aiAnalysisText.value.substring(0, 200) : '' }, error_types: errorTypes, rt_distribution: r.rt_distribution || {}, throughput_trend: r.throughput_trend || [], status_distribution: r.status_distribution || {} }, { responseType: 'blob' })
    const blob = res instanceof Blob ? res : (res && res.data instanceof Blob ? res.data : new Blob([res]))
    const url = URL.createObjectURL(blob); const a = document.createElement('a'); a.href = url; a.download = '压测报告_' + planName + '_' + Date.now() + '.docx'; a.click(); URL.revokeObjectURL(url)
    ElMessage.success('Word 报告已导出（含6张专业图表 + AI分析建议）')
  } catch (e) { console.error('报告生成失败', e); ElMessage.error('报告生成失败: ' + (e.response?.data?.detail || e.message)) }
}

watch(benchPanelExpanded, (v) => { if (v) { nextTick(() => { initAllBenchCharts(); updateAllBenchCharts() }) } })
watch(BENCH_HISTORY_KEY, (newKey) => {
  benchHistory.value = JSON.parse(localStorage.getItem(newKey) || '[]')
})
onMounted(() => {
  fetchCosts()
  window.addEventListener('resize', resizeAllBenchCharts)
})
onBeforeUnmount(() => {
  if (benchPollTimer) { clearInterval(benchPollTimer); benchPollTimer = null }
  window.removeEventListener('resize', resizeAllBenchCharts)
  ;[benchChartInstance, benchChartInstance2, benchChartInstance3, benchChartInstance4].forEach(inst => {
    if (inst.value) { inst.value.dispose(); inst.value = null }
  })
})

defineExpose({ benchResult, benching, benchProgress, benchPercent, benchConcurrency, benchDuration, benchRampUp, benchStartTime, aiAnalysisText, aiAnalysisDialogVisible, startBench, stopBench, shortUrl, resizeAllBenchCharts })
</script>

<style scoped>
.bench-control-panel { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; margin: 8px 12px; flex-shrink: 0; overflow: hidden; transition: all 0.3s ease; }
.bench-control-panel.expanded { height: calc(100vh - 48px); display: flex; flex-direction: column; }
.bench-control-panel.running .bcp-header { background: #fff; border-bottom: 2px solid #3b82f6; }

.bcp-header { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 10px 14px; flex-wrap: wrap; cursor: pointer; user-select: none; transition: background 0.15s; }
.bcp-header:hover { background: #f1f5f9; }
.bcp-header-left { display: flex; align-items: center; gap: 8px; flex-shrink: 0; }
.bcp-header-center { display: flex; gap: 12px; align-items: center; }
.bcp-header-right { display: flex; gap: 6px; align-items: center; flex-shrink: 0; }
.bcp-toggle-icon { font-size: 16px; color: #94a3b8; transition: transform 0.3s ease; flex-shrink: 0; }
.bcp-toggle-icon.rotate { transform: rotate(180deg); }
.bcp-plan-name { color: #1e293b; font-weight: 700; font-size: 14px; }
.bcp-config-item { display: flex; align-items: center; gap: 4px; }
.bcp-config-item label { font-size: 11px; color: #64748b; white-space: nowrap; }
.bcp-start-btn { font-weight: 700 !important; font-size: 14px !important; }

.bcp-progress-inline { display: flex; align-items: center; gap: 10px; }
.bcp-progress-text { font-size: 11px; color: #64748b; white-space: nowrap; }

.bcp-body { flex: 1; overflow-y: auto; min-height: 0; display: flex; flex-direction: column; }

.bcp-requests { display: flex; align-items: center; gap: 6px; padding: 8px 14px; flex-wrap: wrap; border-top: 1px solid #e2e8f0; background: #f8fafc; flex-shrink: 0; }
.bcp-requests-label { font-size: 11px; color: #64748b; white-space: nowrap; }
.bcp-req-tag { cursor: default; font-size: 11px !important; max-width: 180px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

.bcp-charts { padding: 8px 14px; border-top: 1px solid #e2e8f0; background: #fff; flex-shrink: 0; }
.bcp-charts-row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 12px; }
.bcp-charts-row:last-child { margin-bottom: 0; }
.bcp-chart-card { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 8px; }
.bcp-chart-box { width: 100%; height: 200px; }

.bcp-analyze-banner { margin: 12px 14px; border-radius: 10px; background: linear-gradient(135deg, #eff6ff, #dbeafe); border: 1px solid #93c5fd; animation: analyzePulse 2s ease-in-out infinite; }
@keyframes analyzePulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.85; } }
:deep(.analyzing-toast) { border-left: 4px solid #3b82f6 !important; }

/* 报告区域 - 纵向单页布局 */
.bcp-report-section { flex: 1; min-height: 0; overflow-y: auto; }

.bcp-quick-stats { display: flex; align-items: center; gap: 8px; padding: 8px 14px; flex-wrap: wrap; border-top: 1px solid #e2e8f0; background: #fff; flex-shrink: 0; }
.bcp-stat { text-align: center; padding: 2px 8px; border-radius: 4px; background: #f1f5f9; }
.bcp-stat-ok { border-left: 3px solid #10b981; }
.bcp-stat-err { border-left: 3px solid #ef4444; background: #fef2f2; }
.bcp-stat-val { font-size: 16px; font-weight: 700; display: block; color: #1e293b; }
.bcp-stat-lbl { font-size: 10px; color: #94a3b8; }

.bcp-per-url { padding: 8px 14px; border-top: 1px solid #e2e8f0; background: #fff; }
.bpu-header { font-weight: 600; font-size: 12px; color: #1e293b; margin-bottom: 6px; }
.bpu-table-wrapper { max-height: 250px; overflow-y: auto; }
.bpu-table { width: 100%; border-collapse: collapse; font-size: 11px; }
.bpu-table th { background: #f8fafc; padding: 4px 6px; text-align: left; font-weight: 600; color: #64748b; border-bottom: 1px solid #e2e8f0; white-space: nowrap; position: sticky; top: 0; z-index: 1; }
.bpu-table td { padding: 4px 6px; border-bottom: 1px solid #f1f5f9; white-space: nowrap; }
.bpu-table tr:hover { background: #f8fafc; }
.bpu-row-err { background: #fff5f5; }
.bpu-row-err:hover { background: #fef2f2; }
.bpu-url { max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.bpu-ok { color: #10b981; font-weight: 600; }
.bpu-err { color: #ef4444; font-weight: 600; }

.bcp-status-dist { padding: 8px 14px; border-top: 1px solid #e2e8f0; background: #fff; }
.bsd-tags { display: flex; gap: 6px; flex-wrap: wrap; }

.bcp-rt-dist { padding: 8px 14px; border-top: 1px solid #e2e8f0; background: #fff; }
.rt-dist-bars { display: flex; flex-direction: column; gap: 4px; }
.rt-dist-bar { display: flex; align-items: center; gap: 8px; }
.rt-dist-label { font-size: 11px; color: #64748b; width: 70px; flex-shrink: 0; }
.rt-dist-track { flex: 1; height: 16px; background: #f1f5f9; border-radius: 8px; overflow: hidden; }
.rt-dist-fill { height: 100%; background: linear-gradient(90deg, #6366f1, #8b5cf6); border-radius: 8px; transition: width 0.5s ease; }
.rt-dist-count { font-size: 11px; color: #1e293b; font-weight: 600; width: 40px; text-align: right; flex-shrink: 0; }

.bcp-throughput { padding: 8px 14px; border-top: 1px solid #e2e8f0; background: #fff; }
.tp-table table { width: 100%; border-collapse: collapse; font-size: 11px; }
.tp-table th { background: #f8fafc; padding: 4px 6px; text-align: left; font-weight: 600; color: #64748b; border-bottom: 1px solid #e2e8f0; }
.tp-table td { padding: 3px 6px; border-bottom: 1px solid #f1f5f9; }
.tp-bar { width: 100%; height: 12px; background: #f1f5f9; border-radius: 6px; overflow: hidden; }
.tp-fill { height: 100%; background: linear-gradient(90deg, #10b981, #34d399); border-radius: 6px; transition: width 0.5s ease; }

.bcp-body-samples { padding: 8px 14px; border-top: 1px solid #e2e8f0; background: #fff; }
.bcp-samples-scroll { max-height: 200px; overflow-y: auto; display: flex; flex-direction: column; gap: 6px; }
.bcp-sample-card { background: #f8fafc; border-radius: 8px; padding: 8px 10px; border: 1px solid #e2e8f0; }
.bcp-sample-header { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; font-size: 11px; }
.bcp-sample-url { flex: 1; color: #64748b; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.bcp-sample-body { background: #0f172a; color: #e2e8f0; font-family: 'Consolas','Monaco',monospace; font-size: 11px; padding: 10px; border-radius: 6px; max-height: 100px; overflow: auto; margin: 0; white-space: pre-wrap; word-break: break-all; border: 1px solid rgba(148,163,184,0.15); }

.bcp-errors-section { margin: 0 14px 8px; border-top: 1px solid #e2e8f0; background: #fff5f5; }
.bcp-errors-section :deep(.el-collapse-item__header) { background: #fff5f5; padding: 0 14px; }
.bcp-errors-title { font-weight: 600; font-size: 13px; }
.bcp-errors-list { max-height: 250px; overflow-y: auto; padding: 8px 0; }
.bcp-error-item { padding: 8px 12px; margin-bottom: 6px; background: #fff; border-radius: 6px; border: 1px solid #fee2e2; }
.bcp-error-header { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; }
.bcp-error-name { font-weight: 600; font-size: 12px; color: #1e293b; max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.bcp-error-status { font-size: 11px; color: #64748b; }
.bcp-error-time { font-size: 11px; color: #f59e0b; font-weight: 600; }
.bcp-error-msg { font-size: 11px; color: #dc2626; font-family: monospace; word-break: break-all; margin-bottom: 4px; }
.bcp-error-req, .bcp-error-res { margin-top: 4px; }
.bcp-error-req details, .bcp-error-res details { font-size: 11px; }
.bcp-error-req pre, .bcp-error-res pre { background: #f8fafc; padding: 6px 8px; border-radius: 4px; font-size: 10px; max-height: 100px; overflow-y: auto; margin: 4px 0 0; white-space: pre-wrap; word-break: break-all; }
.bcp-error-more { padding: 4px 0; font-size: 11px; color: #94a3b8; }

.bench-history-panel { margin: 0 12px 8px; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden; flex-shrink: 0; }
.bh-header { display: flex; justify-content: space-between; align-items: center; padding: 8px 14px; font-weight: 600; font-size: 13px; border-bottom: 1px solid #e2e8f0; }
.bh-list { max-height: 200px; overflow-y: auto; }
.bh-item { display: flex; align-items: center; gap: 10px; padding: 6px 14px; cursor: pointer; font-size: 12px; border-bottom: 1px solid #f1f5f9; transition: background 0.15s; }
.bh-item:hover { background: #e0f2fe; }
.bh-time { color: #94a3b8; font-size: 11px; width: 130px; flex-shrink: 0; }
.bh-name { flex: 1; color: #1e293b; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.bh-total { color: #334155; font-weight: 600; }
.bh-tps { color: #3b82f6; font-weight: 600; }
.bh-ok { color: #10b981; font-weight: 600; }
.bh-err { color: #ef4444; font-weight: 600; }

.bench-body-preview { background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%); padding: 12px; border-radius: 8px; font-size: 11.5px; color: #e2e8f0; font-family: 'Consolas','Monaco',monospace; max-height: 160px; overflow: auto; margin: 0; white-space: pre-wrap; word-break: break-all; border: 1px solid rgba(148,163,184,0.1); box-shadow: inset 0 2px 6px rgba(0,0,0,0.15); }

.ai-cost-hint {
  font-size: 11px;
  color: #ffa502;
  margin-left: 6px;
  white-space: nowrap;
}
</style>
