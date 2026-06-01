<template>
  <div class="coverage-page">
    <div class="page-header">
      <h2>测试覆盖率看板</h2>
      <p class="subtitle">接口 × 用例 × 执行 热力图，一目了然掌握测试覆盖情况</p>
      <el-button class="help-btn" @click="showHelp = true">❓ 使用说明</el-button>
    </div>

    <!-- 汇总卡片 -->
    <div class="summary-cards">
      <el-card class="stat-card" shadow="hover">
        <div class="stat-value">{{ summary.total_apis || 0 }}</div>
        <div class="stat-label">接口总数</div>
      </el-card>
      <el-card class="stat-card" shadow="hover">
        <div class="stat-value">{{ summary.total_cases || 0 }}</div>
        <div class="stat-label">用例总数</div>
      </el-card>
      <el-card class="stat-card" shadow="hover">
        <div class="stat-value">{{ summary.total_executions_30d || 0 }}</div>
        <div class="stat-label">30天执行次数</div>
      </el-card>
      <el-card class="stat-card highlight" shadow="hover">
        <div class="stat-value">{{ summary.pass_rate_30d || 0 }}%</div>
        <div class="stat-label">通过率</div>
      </el-card>
    </div>

    <!-- 控制栏 -->
    <div class="controls">
      <el-radio-group v-model="selectedDays" @change="loadHeatmap">
        <el-radio-button :value="7">7天</el-radio-button>
        <el-radio-button :value="14">14天</el-radio-button>
        <el-radio-button :value="30">30天</el-radio-button>
        <el-radio-button :value="90">90天</el-radio-button>
      </el-radio-group>
      <el-input
        v-model="searchKeyword"
        placeholder="搜索接口..."
        clearable
        style="width: 240px; margin-left: 16px;"
        :prefix-icon="Search"
      />
    </div>

    <!-- 热力图 -->
    <el-card class="heatmap-card" v-loading="loading">
      <div v-if="!heatmapData.apis?.length" class="empty-state">
        <el-empty description="暂无测试数据">
          <el-button type="primary" @click="$router.push('/auto-test')">去创建用例</el-button>
        </el-empty>
      </div>

      <div v-else class="heatmap-container">
        <!-- 图例 -->
        <div class="heatmap-legend">
          <span class="legend-item"><span class="legend-dot none"></span>未执行</span>
          <span class="legend-item"><span class="legend-dot passed"></span>通过</span>
          <span class="legend-item"><span class="legend-dot failed"></span>失败</span>
          <span class="legend-item"><span class="legend-dot unknown"></span>未知</span>
        </div>

        <!-- 热力图表格 -->
        <div class="heatmap-scroll">
          <table class="heatmap-table">
            <thead>
              <tr>
                <th class="api-col">接口</th>
                <th v-for="date in displayDates" :key="date" class="date-col" :title="date">
                  {{ formatDateShort(date) }}
                </th>
                <th class="stat-col">通过率</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(api, apiIdx) in filteredApis" :key="apiIdx">
                <td class="api-cell" :title="`${api.method} ${api.url}`">
                  <el-tag :type="methodType(api.method)" size="small" class="method-tag">{{ api.method }}</el-tag>
                  <span class="api-name">{{ api.name || api.url }}</span>
                </td>
                <td
                  v-for="(date, dateIdx) in displayDates"
                  :key="dateIdx"
                  class="heat-cell"
                  :class="getCellClass(api, dateIdx)"
                  @click="showDetail(api, date)"
                >
                  <span class="cell-tooltip">{{ api.method }} {{ api.url }}<br/>{{ date }}: {{ getCellStatus(api, dateIdx) }}</span>
                </td>
                <td class="stat-cell">
                  <el-progress
                    :percentage="api.pass_rate || 0"
                    :color="api.pass_rate >= 80 ? '#67c23a' : api.pass_rate >= 50 ? '#e6a23c' : '#f56c6c'"
                    :stroke-width="8"
                    :text-inside="false"
                    style="width: 80px;"
                  />
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </el-card>

    <!-- 接口分组统计 -->
    <el-card class="group-stats-card" v-if="groupStats.length">
      <template #header>
        <span>分组统计</span>
      </template>
      <div class="group-stats-grid">
        <div v-for="group in groupStats" :key="group.name" class="group-stat-item">
          <div class="group-name">{{ group.name }}</div>
          <div class="group-count">{{ group.count }} 个接口</div>
          <el-progress
            :percentage="group.avg_pass_rate"
            :color="group.avg_pass_rate >= 80 ? '#67c23a' : '#e6a23c'"
            :stroke-width="6"
          />
        </div>
      </div>
    </el-card>

    <!-- 执行详情弹窗 -->
    <el-dialog v-model="detailVisible" :title="detailTitle" width="700px">
      <div v-loading="detailLoading">
        <el-table :data="detailRecords" stripe max-height="400">
          <el-table-column prop="id" label="ID" width="60" />
          <el-table-column prop="status" label="状态" width="80">
            <template #default="{ row }">
              <el-tag :type="row.status === 'passed' ? 'success' : 'danger'" size="small">
                {{ row.status === 'passed' ? '通过' : '失败' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="response_time" label="响应时间" width="100">
            <template #default="{ row }">
              {{ row.response_time ? `${row.response_time}ms` : '-' }}
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="执行时间">
            <template #default="{ row }">
              {{ formatTime(row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column prop="error_message" label="错误信息" show-overflow-tooltip />
        </el-table>
      </div>
    </el-dialog>

    <HelpDrawer v-model="showHelp" :title="helpData.title" :intro="helpData.intro" :sections="helpData.sections" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { Search } from '@element-plus/icons-vue'
import autoTestRequest from '@/utils/autoTestRequest'
import HelpDrawer from '@/components/HelpDrawer.vue'
import { helpContent } from '@/utils/help-content'

const loading = ref(false)
const detailLoading = ref(false)
const detailVisible = ref(false)
const detailTitle = ref('')
const selectedDays = ref(30)
const searchKeyword = ref('')
const showHelp = ref(false)
const helpData = helpContent.testCoverage

const summary = ref({})
const heatmapData = ref({ apis: [], dates: [], matrix: [] })
const detailRecords = ref([])

// 计算要显示的日期（最多显示 31 列）
const displayDates = computed(() => {
  const dates = heatmapData.value.dates || []
  return dates.slice(-31)
})

// 过滤接口
const filteredApis = computed(() => {
  const apis = heatmapData.value.apis || []
  if (!searchKeyword.value) return apis
  const kw = searchKeyword.value.toLowerCase()
  return apis.filter(a =>
    (a.name || '').toLowerCase().includes(kw) ||
    (a.url || '').toLowerCase().includes(kw) ||
    (a.method || '').toLowerCase().includes(kw)
  )
})

// 分组统计
const groupStats = computed(() => {
  const apis = heatmapData.value.apis || []
  const groups = {}
  for (const api of apis) {
    const g = api.group || '未分组'
    if (!groups[g]) groups[g] = { name: g, count: 0, total_pass_rate: 0 }
    groups[g].count++
    groups[g].total_pass_rate += api.pass_rate || 0
  }
  return Object.values(groups).map(g => ({
    ...g,
    avg_pass_rate: Math.round(g.total_pass_rate / g.count),
  })).sort((a, b) => b.count - a.count)
})

const getCellClass = (api, dateIdx) => {
  const allApis = heatmapData.value.apis || []
  const apiIdx = allApis.indexOf(api)
  if (apiIdx < 0) return 'none'
  const matrix = heatmapData.value.matrix || []
  const row = matrix[apiIdx]
  if (!row) return 'none'
  const offset = (heatmapData.value.dates || []).length - displayDates.value.length
  const val = row[dateIdx + offset]
  return val || 'none'
}

const getCellStatus = (api, dateIdx) => {
  const allApis = heatmapData.value.apis || []
  const apiIdx = allApis.indexOf(api)
  if (apiIdx < 0) return '未执行'
  const matrix = heatmapData.value.matrix || []
  const row = matrix[apiIdx]
  if (!row) return '未执行'
  const offset = (heatmapData.value.dates || []).length - displayDates.value.length
  const val = row[dateIdx + offset]
  const map = { passed: '通过', failed: '失败', none: '未执行', unknown: '未知' }
  return map[val] || val || '未执行'
}

const methodType = (m) => {
  const map = { GET: 'success', POST: '', PUT: 'warning', DELETE: 'danger', PATCH: 'info' }
  return map[m] || 'info'
}

const formatDateShort = (dateStr) => {
  const d = new Date(dateStr)
  return `${d.getMonth() + 1}/${d.getDate()}`
}

const formatTime = (isoStr) => {
  if (!isoStr) return '-'
  const d = new Date(isoStr)
  return d.toLocaleString('zh-CN')
}

const loadSummary = async () => {
  try {
    summary.value = await autoTestRequest.get('/auto-test/coverage/summary')
  } catch (e) {
    console.error('加载汇总失败', e)
  }
}

const loadHeatmap = async () => {
  loading.value = true
  try {
    heatmapData.value = await autoTestRequest.get(`/auto-test/coverage/heatmap?days=${selectedDays.value}`)
  } catch (e) {
    console.error('加载热力图失败', e)
  } finally {
    loading.value = false
  }
}

const showDetail = async (api, date) => {
  detailTitle.value = `${api.method} ${api.name || api.url} - ${date} 执行详情`
  detailVisible.value = true
  detailLoading.value = true
  try {
    const ids = (api.case_ids || [api.id]).join(',')
    const resp = await autoTestRequest.get(`/auto-test/coverage/detail?case_ids=${ids}&days=${selectedDays.value}`)
    detailRecords.value = resp?.records || []
  } catch (e) {
    detailRecords.value = []
  } finally {
    detailLoading.value = false
  }
}

onMounted(() => {
  loadSummary()
  loadHeatmap()
})
</script>

<style scoped>
.coverage-page {
  max-width: 1400px;
  margin: 0 auto;
  padding: 24px;
}
.page-header {
  margin-bottom: 24px;
}
.page-header h2 {
  margin: 0 0 4px;
  font-size: 22px;
}
.subtitle {
  color: var(--el-text-color-secondary);
  font-size: 14px;
}
.summary-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}
.stat-card {
  text-align: center;
  padding: 8px 0;
}
.stat-card.highlight {
  border-color: var(--el-color-primary);
}
.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: var(--el-text-color-primary);
}
.stat-card.highlight .stat-value {
  color: var(--el-color-primary);
}
.stat-label {
  font-size: 13px;
  color: var(--el-text-color-secondary);
  margin-top: 4px;
}
.controls {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
}
.heatmap-card {
  margin-bottom: 24px;
}
.heatmap-legend {
  display: flex;
  gap: 16px;
  margin-bottom: 12px;
  font-size: 13px;
}
.legend-item {
  display: flex;
  align-items: center;
  gap: 4px;
}
.legend-dot {
  width: 14px;
  height: 14px;
  border-radius: 3px;
}
.legend-dot.none { background: #ebedf0; }
.legend-dot.passed { background: #67c23a; }
.legend-dot.failed { background: #f56c6c; }
.legend-dot.unknown { background: #e6a23c; }
.heatmap-scroll {
  overflow-x: auto;
}
.heatmap-table {
  border-collapse: collapse;
  width: 100%;
  font-size: 12px;
}
.heatmap-table th, .heatmap-table td {
  border: 1px solid var(--el-border-color-lighter);
  padding: 0;
  text-align: center;
}
.heatmap-table thead th {
  background: var(--el-fill-color-light);
  padding: 6px 4px;
  font-weight: 600;
  position: sticky;
  top: 0;
  z-index: 1;
}
.api-col {
  text-align: left !important;
  min-width: 200px;
  max-width: 300px;
}
.date-col {
  min-width: 32px;
  max-width: 36px;
  font-size: 10px;
}
.stat-col {
  min-width: 90px;
}
.api-cell {
  text-align: left !important;
  padding: 4px 8px !important;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 300px;
}
.method-tag {
  margin-right: 4px;
  font-size: 10px;
}
.api-name {
  font-size: 12px;
}
.heat-cell {
  width: 32px;
  height: 28px;
  cursor: pointer;
  position: relative;
  transition: transform 0.1s;
}
.heat-cell:hover {
  transform: scale(1.3);
  z-index: 2;
}
.heat-cell .cell-tooltip {
  display: none;
  position: absolute;
  bottom: 100%;
  left: 50%;
  transform: translateX(-50%);
  background: #333;
  color: white;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 11px;
  white-space: nowrap;
  z-index: 10;
  pointer-events: none;
}
.heat-cell:hover .cell-tooltip {
  display: block;
}
.heat-cell.none { background: #ebedf0; }
.heat-cell.passed { background: #67c23a; }
.heat-cell.failed { background: #f56c6c; }
.heat-cell.unknown { background: #e6a23c; }
.stat-cell {
  padding: 4px 8px !important;
}
.group-stats-card {
  margin-bottom: 24px;
}
.group-stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 16px;
}
.group-stat-item {
  padding: 12px;
  background: var(--el-fill-color-lighter);
  border-radius: 8px;
}
.group-name {
  font-weight: 600;
  font-size: 14px;
  margin-bottom: 4px;
}
.group-count {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-bottom: 8px;
}
.empty-state {
  padding: 60px 0;
}
@media (max-width: 768px) {
  .summary-cards {
    grid-template-columns: repeat(2, 1fr);
  }
  .controls {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
}
</style>
