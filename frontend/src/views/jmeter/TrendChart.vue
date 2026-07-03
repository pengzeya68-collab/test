<template>
  <el-dialog v-model="visible" title="📊 压测趋势对比" width="90%" top="3vh" destroy-on-close @close="$emit('close')">
    <div class="trend-toolbar">
      <div class="trend-toolbar-left">
        <span class="trend-label">选择对比的运行:</span>
        <el-select v-model="selectedRunIds" multiple :multiple-limit="6" placeholder="选择 1-6 个历史运行" filterable size="small" style="min-width:380px;">
          <el-option v-for="r in historyRuns" :key="r.id" :value="r.id" :label="`#${r.id} ${r.plan_name} (${formatTime(r.created_at)})`">
            <span style="float:left;">#{{ r.id }} {{ r.plan_name }}</span>
            <span style="float:right;color:var(--tm-text-secondary);font-size:12px;">{{ formatTime(r.created_at) }} · {{ r.engine_type }}</span>
          </el-option>
        </el-select>
        <el-button size="small" type="primary" @click="loadCompare" :loading="loading" :disabled="selectedRunIds.length === 0">加载对比</el-button>
        <el-button size="small" @click="loadBaselines" :loading="loadingBaselines">🏷️ 加载基线</el-button>
      </div>
      <div class="trend-toolbar-right">
        <el-radio-group v-model="metric" size="small" @change="renderChart">
          <el-radio-button label="tps">TPS</el-radio-button>
          <el-radio-button label="avg_ms">平均响应时间</el-radio-button>
          <el-radio-button label="p95_ms">P95</el-radio-button>
          <el-radio-button label="p99_ms">P99</el-radio-button>
          <el-radio-button label="error_rate">错误率</el-radio-button>
        </el-radio-group>
      </div>
    </div>

    <div v-if="error" class="trend-error">{{ error }}</div>

    <div v-if="compareData.length > 0" class="trend-summary">
      <el-table :data="summaryTable" size="small" stripe>
        <el-table-column prop="id" label="#" width="60" />
        <el-table-column prop="plan_name" label="运行名称" min-width="160" show-overflow-tooltip />
        <el-table-column prop="engine_type" label="引擎" width="100" />
        <el-table-column prop="tps" label="TPS" width="90" align="right" />
        <el-table-column prop="avg_ms" label="平均(ms)" width="100" align="right" />
        <el-table-column prop="p95_ms" label="P95(ms)" width="100" align="right" />
        <el-table-column prop="p99_ms" label="P99(ms)" width="100" align="right" />
        <el-table-column prop="error_rate" label="错误率" width="90" align="right" />
        <el-table-column prop="regression" label="回归" width="80" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.regression" type="danger" size="small">⚠️ 回归</el-tag>
            <el-tag v-else type="success" size="small">正常</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="时间" width="160" />
      </el-table>
    </div>

    <div ref="chartRef" class="trend-chart-box" v-loading="loading"></div>

    <div v-if="baselines.length > 0" class="trend-baselines">
      <div class="trend-section-title">🏷️ 已叠加基线</div>
      <el-tag v-for="b in baselines" :key="b.id" closable @close="removeBaseline(b.id)" size="small" type="warning" effect="plain" style="margin-right:6px;">
        {{ b.name }} (P95≤{{ b.p95_threshold_ms || '-' }}ms)
      </el-tag>
    </div>
  </el-dialog>
</template>

<script setup>
import { ref, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import * as echarts from 'echarts'
import request from '@/utils/request'

const props = defineProps({
  modelValue: Boolean,
  historyRuns: { type: Array, default: () => [] },
})
const emit = defineEmits(['close'])

const visible = ref(props.modelValue)
watch(() => props.modelValue, (v) => { visible.value = v })
watch(visible, (v) => { if (!v) emit('close') })

const selectedRunIds = ref([])
const metric = ref('tps')
const compareData = ref([])
const baselines = ref([])
const loading = ref(false)
const loadingBaselines = ref(false)
const error = ref('')
const chartRef = ref(null)
let chartInstance = null

const summaryTable = ref([])

const formatTime = (iso) => {
  if (!iso) return '-'
  const d = new Date(iso)
  return `${d.getMonth() + 1}/${d.getDate()} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

const loadCompare = async () => {
  if (selectedRunIds.value.length === 0) {
    error.value = '请至少选择 1 个运行'
    return
  }
  loading.value = true
  error.value = ''
  try {
    const res = await request.get(`/auto-test/jmeter/runs/compare`, { params: { ids: selectedRunIds.value.join(',') } })
    compareData.value = Array.isArray(res) ? res : (res?.data || [])
    summaryTable.value = compareData.value.map(r => ({
      id: r.id,
      plan_name: r.plan_name,
      engine_type: r.engine_type,
      tps: r.summary?.tps?.toFixed(1) || '-',
      avg_ms: r.summary?.avg_ms?.toFixed(0) || '-',
      p95_ms: r.summary?.p95_ms?.toFixed(0) || '-',
      p99_ms: r.summary?.p99_ms?.toFixed(0) || '-',
      error_rate: r.summary?.error_rate != null ? (r.summary.error_rate * 100).toFixed(2) + '%' : '-',
      regression: r.regression,
      created_at: formatTime(r.created_at),
    }))
    await nextTick()
    renderChart()
  } catch (e) {
    error.value = '加载对比数据失败: ' + (e?.message || e)
  } finally {
    loading.value = false
  }
}

const loadBaselines = async () => {
  loadingBaselines.value = true
  try {
    const res = await request.get('/auto-test/jmeter/baselines')
    baselines.value = Array.isArray(res) ? res : (res?.data || [])
  } catch (e) {
    error.value = '加载基线失败: ' + (e?.message || e)
  } finally {
    loadingBaselines.value = false
  }
}

const removeBaseline = (id) => {
  baselines.value = baselines.value.filter(b => b.id !== id)
  renderChart()
}

const renderChart = () => {
  if (!chartRef.value) return
  if (!chartInstance) {
    chartInstance = echarts.init(chartRef.value)
  }

  const metricLabels = {
    tps: 'TPS (次/秒)',
    avg_ms: '平均响应时间 (ms)',
    p95_ms: 'P95 响应时间 (ms)',
    p99_ms: 'P99 响应时间 (ms)',
    error_rate: '错误率 (%)',
  }

  const xData = compareData.value.map(r => `#${r.id} ${r.plan_name || ''}`)
  const yData = compareData.value.map(r => {
    const v = r.summary?.[metric.value]
    if (v == null) return null
    return metric.value === 'error_rate' ? +(v * 100).toFixed(2) : +v.toFixed(2)
  })

  // 基线参考线(P95/P99 阈值)
  const markLines = []
  if (metric.value === 'p95_ms') {
    baselines.value.forEach(b => {
      if (b.p95_threshold_ms != null) {
        markLines.push({ yAxis: b.p95_threshold_ms, name: b.name + ' P95阈值' })
      }
    })
  } else if (metric.value === 'p99_ms') {
    baselines.value.forEach(b => {
      if (b.p99_threshold_ms != null) {
        markLines.push({ yAxis: b.p99_threshold_ms, name: b.name + ' P99阈值' })
      }
    })
  }

  const series = [{
    name: metricLabels[metric.value],
    type: 'line',
    data: yData,
    smooth: true,
    symbol: 'circle',
    symbolSize: 8,
    lineStyle: { width: 3 },
    itemStyle: { color: '#409EFF' },
    areaStyle: { opacity: 0.15 },
    markLine: markLines.length > 0 ? {
      symbol: ['none', 'none'],
      data: markLines.map(m => ({
        yAxis: m.yAxis,
        name: m.name,
        label: { formatter: m.name, position: 'end' },
        lineStyle: { color: '#E6A23C', type: 'dashed', width: 2 },
      })),
    } : undefined,
  }]

  chartInstance.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: [metricLabels[metric.value]] },
    grid: { left: 60, right: 40, top: 50, bottom: 80 },
    xAxis: { type: 'category', data: xData, axisLabel: { rotate: 30 } },
    yAxis: { type: 'value', name: metricLabels[metric.value] },
    series,
  }, true)

  chartInstance.resize()
}

watch(() => props.modelValue, async (v) => {
  if (v) {
    visible.value = true
    await nextTick()
    renderChart()
  }
})

onMounted(() => {
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
})

const handleResize = () => {
  if (chartInstance) chartInstance.resize()
}

// 自动选中最近 3 个 run
watch(() => props.historyRuns, (runs) => {
  if (runs.length > 0 && selectedRunIds.value.length === 0) {
    selectedRunIds.value = runs.slice(0, Math.min(3, runs.length)).map(r => r.id)
  }
}, { immediate: true })
</script>

<style scoped>
.trend-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 12px;
}
.trend-toolbar-left { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.trend-toolbar-right { display: flex; align-items: center; }
.trend-label { font-size: 13px; color: var(--tm-text-secondary); }
.trend-error {
  padding: 10px 14px;
  background: var(--el-color-danger-light-9);
  color: var(--el-color-danger);
  border-radius: 4px;
  margin-bottom: 12px;
  font-size: 13px;
}
.trend-summary {
  margin-bottom: 16px;
  border: 1px solid var(--tm-border-color, #e4e7ed);
  border-radius: 4px;
}
.trend-chart-box {
  width: 100%;
  height: 420px;
  min-height: 300px;
}
.trend-baselines {
  margin-top: 12px;
  padding: 8px 12px;
  background: var(--el-fill-color-light);
  border-radius: 4px;
}
.trend-section-title {
  font-size: 13px;
  color: var(--tm-text-secondary);
  margin-bottom: 6px;
}
</style>
