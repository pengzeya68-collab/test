<template>
  <el-drawer
    v-model="drawerVisible"
    title="执行历史记录"
    size="85%"
  >
    <div class="history-content" v-loading="historyLoading">
      <el-row :gutter="16" class="stats-cards">
        <el-col :span="8">
          <el-card shadow="hover" class="stat-card">
            <div class="stat-content">
              <div class="stat-value">{{ historyStats.total_reports }}</div>
              <div class="stat-label">总报告数</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="8">
          <el-card shadow="hover" class="stat-card">
            <div class="stat-content">
              <div class="stat-value" style="color: #67c23a;">{{ historyStats.passed_reports }}</div>
              <div class="stat-label">通过报告数</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="8">
          <el-card shadow="hover" class="stat-card">
            <div class="stat-content">
              <div class="stat-value" :style="{ color: historyStats.pass_rate >= 80 ? '#67c23a' : (historyStats.pass_rate >= 60 ? '#e6a23c' : '#f56c6c') }">
                {{ historyStats.pass_rate }}%
              </div>
              <div class="stat-label">通过率</div>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <el-form :inline="true" class="history-filter-form">
        <el-form-item label="状态">
          <el-select v-model="historyFilterStatus" placeholder="全部状态" clearable style="width: 120px">
            <el-option label="全部" value="" />
            <el-option label="运行中" value="running" />
            <el-option label="已完成" value="completed" />
            <el-option label="已失败" value="failed" />
            <el-option label="已取消" value="cancelled" />
          </el-select>
        </el-form-item>
        <el-form-item label="日期范围">
          <el-date-picker
            v-model="historyFilterStartDate"
            type="date"
            placeholder="开始日期"
            value-format="YYYY-MM-DD"
            :disabled-date="disabledStartDate"
            style="width: 140px"
          />
          <span style="margin: 0 8px">至</span>
          <el-date-picker
            v-model="historyFilterEndDate"
            type="date"
            placeholder="结束日期"
            value-format="YYYY-MM-DD"
            :disabled-date="disabledEndDate"
            style="width: 140px"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadExecutionHistory" :loading="historyLoading">
            <el-icon><Search /></el-icon>
            查询
          </el-button>
          <el-button @click="resetHistoryFilters">
            <el-icon><RefreshRight /></el-icon>
            重置
          </el-button>
        </el-form-item>
      </el-form>

      <el-alert
        title="⚠️ 温馨提示"
        type="warning"
        description="为节省系统存储，执行报告仅保留最近 7 天，请及时查看或导出。"
        show-icon
        :closable="false"
        style="margin-bottom: 16px"
      />

      <div class="history-summary" v-if="executionHistory.total > 0">
        <el-tag type="info">共 {{ executionHistory.total }} 次执行</el-tag>
        <el-tag type="success">成功 {{ executionHistory.success_count }} 次</el-tag>
        <el-tag type="danger">失败 {{ executionHistory.failed_count }} 次</el-tag>
        <el-button size="small" @click="refreshExecutionHistory" style="margin-left: 12px">
          <el-icon><Refresh /></el-icon> 刷新
        </el-button>
      </div>

      <el-table :data="executionHistory.items" style="width: 100%; margin-top: 16px">
        <el-table-column prop="id" label="ID" width="60" align="center" />
        <el-table-column prop="status" label="状态" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="total_steps" label="总步骤" width="70" align="center" />
        <el-table-column prop="success_steps" label="成功" width="60" align="center">
          <template #default="{ row }">
            <span class="success-text">{{ row.success_steps }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="failed_steps" label="失败" width="60" align="center">
          <template #default="{ row }">
            <span class="failed-text">{{ row.failed_steps }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="total_time" label="耗时" width="80" align="center">
          <template #default="{ row }">
            {{ ((row.total_time || 0) / 1000).toFixed(2) }}s
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="执行时间" width="170" />
        <el-table-column label="操作" min-width="320" align="left">
          <template #default="{ row }">
            <div class="history-actions">
              <el-tooltip content="再次运行此场景" placement="top">
                <el-button size="small" type="warning" @click="reRunHistory(row)">
                  <el-icon><VideoPlay /></el-icon>
                  再次运行
                </el-button>
              </el-tooltip>
              <el-tooltip content="查看 Allure 详细报告" placement="top">
                <el-button
                  v-if="row.report_url"
                  size="small"
                  type="primary"
                  @click="openReport(row.report_url)"
                >
                  <el-icon><View /></el-icon>
                  Allure报告
                </el-button>
              </el-tooltip>
              <el-tooltip content="查看步骤详情（含请求/响应）" placement="top">
                <el-button size="small" type="info" @click="viewReportDetail(row.id)">
                  <el-icon><Document /></el-icon>
                  步骤详情
                </el-button>
              </el-tooltip>
              <el-tooltip content="删除此条历史记录" placement="top">
                <el-button size="small" type="danger" @click="deleteHistoryRecord(row.id)">
                  <el-icon><Delete /></el-icon>
                </el-button>
              </el-tooltip>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="!historyLoading && executionHistory.items.length === 0" description="暂无执行记录" />
    </div>
  </el-drawer>

  <el-dialog
    v-model="reportDetailVisible"
    title="执行报告详情"
    width="95%"
    append-to-body
    destroy-on-close
  >
    <div v-loading="reportDetailLoading" style="min-height: 200px;">
      <div v-if="reportDetailData" class="result-content">
        <div class="result-header-stats">
          <el-tag :type="reportDetailData.failed_steps > 0 ? 'danger' : 'success'" size="large">
            {{ reportDetailData.failed_steps > 0 ? '❌ 有步骤失败' : '✅ 全部通过' }}
          </el-tag>
          <span style="margin-left: 15px; color: var(--tm-text-regular);">
            总步骤: {{ reportDetailData.total_steps || 0 }} |
            成功: <span style="color: #67c23a">{{ reportDetailData.success_steps || 0 }}</span> |
            失败: <span style="color: #f56c6c">{{ reportDetailData.failed_steps || 0 }}</span> |
            总耗时: {{ (reportDetailData.total_time || 0) }}ms
          </span>
          <el-button
            :type="reportDetailData.failed_steps > 0 ? 'danger' : 'primary'"
            size="default"
            style="margin-left: 20px"
            :loading="isRunning"
            :disabled="isRunning"
            @click="reRunHistory(reportDetailData)"
          >
            <el-icon><VideoPlay /></el-icon>
            再次运行
          </el-button>
        </div>

        <el-divider />

        <div v-if="reportDetailData && reportDetailData.report_url" style="margin-bottom: 20px;">
          <el-alert
            title="Allure 报告为精准自动测试结果，支持导出邮件发送"
            type="info"
            :closable="false"
            show-icon
            style="margin-bottom: 10px"
          >
            <template #default>
              <el-button type="primary" size="small" @click="openReport(reportDetailData.report_url)">
                在新标签页打开 Allure 报告
              </el-button>
            </template>
          </el-alert>
          <div style="height: 70vh; width: 100%; border: 1px solid var(--tm-border-color); border-radius: 4px; overflow: hidden;">
            <iframe
              :src="resolveReportUrl(reportDetailData.report_url)"
              style="width: 100%; height: 100%; border: none;"
              title="Allure 报告"
            ></iframe>
          </div>
        </div>
        <el-empty v-else description="暂无 Allure 报告数据" />

        <el-divider>文本步骤详情</el-divider>

        <el-alert
          v-if="!reportDetailData.step_results?.length && !reportDetailData.step_detail_available"
          title="步骤详情不可用"
          description="该报告的步骤详情数据无法读取，可能已被清理或写入失败。统计信息仍然准确。"
          type="warning"
          :closable="false"
          show-icon
          style="margin-bottom: 16px;"
        />

        <div class="step-results">
          <div
            v-for="(step, index) in reportDetailData.step_results"
            :key="index"
            class="step-result-card"
            :class="{ 'is-failed': step.status === 'failed', 'is-skipped': step.status === 'skipped' }"
          >
            <div v-if="step.status === 'skipped'" class="step-header step-header-skipped">
              <span class="step-order">{{ index + 1 }}</span>
              <el-tag type="info" size="small">{{ step.method || 'N/A' }}</el-tag>
              <span class="step-name">{{ step.api_case_name }}</span>
              <el-tag type="info" size="small">未执行/跳过</el-tag>
              <span class="step-skipped-hint">因前置步骤失败，此步骤被跳过</span>
            </div>

            <div v-else class="step-header" @click="toggleDetailStep(index)">
              <span class="step-order">{{ index + 1 }}</span>
              <el-tag :type="getMethodType(step.method)" size="small">{{ step.method }}</el-tag>
              <span class="step-name">{{ step.api_case_name }}</span>
              <el-tag v-if="step.status_code" :type="getStatusCodeType(step.status_code)" size="small">
                {{ step.status_code }}
              </el-tag>
              <el-tag v-if="step.status === 'success'" type="success" effect="light">通过</el-tag>
              <el-tag v-else-if="step.status === 'failed'" type="danger" effect="light">失败</el-tag>
              <el-tag v-else-if="step.status === 'skipped'" type="info" effect="light">跳过</el-tag>
              <el-tag v-else type="warning" effect="light">未知</el-tag>

              <span style="margin-left: 10px; color: var(--tm-text-secondary); font-size: 13px;" v-if="step.status !== 'skipped'">
                {{ step.duration || 0 }}ms
              </span>
              <el-icon class="toggle-icon" :class="{ 'is-expanded': expandedDetailSteps.includes(index) }">
                <ArrowRight />
              </el-icon>
            </div>

            <div class="step-detail" v-if="expandedDetailSteps.includes(index) && step.status !== 'skipped'">
              <div class="detail-url">{{ step.url }}</div>

              <div class="detail-section" v-if="step.headers || step.payload">
                <h5>请求信息</h5>
                <div class="request-info">
                  <div class="info-row">
                    <span class="info-label">方法:</span>
                    <el-tag :type="getMethodType(step.method)" size="small">{{ step.method }}</el-tag>
                  </div>
                  <div class="info-row">
                    <span class="info-label">URL:</span>
                    <span class="info-value">{{ step.url }}</span>
                  </div>
                  <div class="info-row" v-if="step.headers && Object.keys(step.headers).length > 0">
                    <span class="info-label">请求头:</span>
                    <pre class="code-block">{{ formatResponseBody(step.headers) }}</pre>
                  </div>
                  <div class="info-row" v-if="step.payload && Object.keys(step.payload).length > 0">
                    <span class="info-label">请求体:</span>
                    <pre class="code-block">{{ formatResponseBody(step.payload) }}</pre>
                  </div>
                </div>
              </div>

              <div class="step-error" v-if="step.error">
                <el-alert type="error" :title="step.error" :closable="false" show-icon />
              </div>

              <div class="detail-section" v-if="step.response">
                <h5>响应信息</h5>
                <div class="response-info">
                  <div class="info-row">
                    <span class="info-label">状态码:</span>
                    <el-tag :type="getStatusCodeType(step.status_code)" size="small">
                      {{ step.status_code || '无' }}
                    </el-tag>
                  </div>
                  <div class="info-row" v-if="step.response.headers && Object.keys(step.response.headers).length > 0">
                    <span class="info-label">响应头:</span>
                    <pre class="code-block">{{ formatResponseBody(step.response.headers) }}</pre>
                  </div>
                  <div class="info-row" v-if="step.response.body">
                    <span class="info-label">响应体:</span>
                    <pre class="code-block">{{ step.response.body }}</pre>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <template #footer>
      <el-button @click="reportDetailVisible = false">关闭</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, RefreshRight, Refresh, VideoPlay, View, Document, Delete, ArrowRight } from '@element-plus/icons-vue'
import autoTestRequest from '@/utils/autoTestRequest'

const props = defineProps({
  scenarioId: { type: Number, default: null },
  visible: { type: Boolean, default: false },
})

const emit = defineEmits(['update:visible', 're-run'])

const drawerVisible = computed({
  get: () => props.visible,
  set: (val) => emit('update:visible', val)
})

const historyLoading = ref(false)
const executionHistory = ref({
  total: 0,
  success_count: 0,
  failed_count: 0,
  items: []
})

const historyFilterStatus = ref('')
const historyFilterStartDate = ref('')
const historyFilterEndDate = ref('')
const historyStats = ref({
  total_reports: 0,
  passed_reports: 0,
  pass_rate: 0
})

const reportDetailVisible = ref(false)
const reportDetailLoading = ref(false)
const reportDetailData = ref(null)
const expandedDetailSteps = ref([])
const isRunning = ref(false)

const resolveReportUrl = (reportUrl) => {
  if (!reportUrl) return ''
  if (/^https?:\/\//i.test(reportUrl)) return reportUrl

  const normalizedPath = reportUrl.startsWith('/') ? reportUrl : `/${reportUrl}`
  const configuredBase = import.meta.env.VITE_AUTO_TEST_API_BASE_URL?.trim()

  if (configuredBase) {
    return `${configuredBase.replace(/\/+$/, '')}${normalizedPath}`
  }

  return normalizedPath
}

const disabledStartDate = (time) => {
  if (time.getTime() > Date.now()) {
    return true
  }
  if (historyFilterEndDate.value) {
    const endDate = new Date(historyFilterEndDate.value)
    return time.getTime() > endDate.getTime()
  }
  return false
}

const disabledEndDate = (time) => {
  if (time.getTime() > Date.now()) {
    return true
  }
  if (historyFilterStartDate.value) {
    const startDate = new Date(historyFilterStartDate.value)
    return time.getTime() < startDate.getTime()
  }
  return false
}

const getStatusType = (status) => {
  const types = { success: 'success', completed: 'success', failed: 'danger', error: 'warning', running: 'primary', cancelled: 'info' }
  return types[status] || 'info'
}

const getStatusText = (status) => {
  const texts = { success: '成功', completed: '成功', failed: '失败', error: '异常', running: '运行中', cancelled: '已取消' }
  return texts[status] || status
}

const getMethodType = (method) => {
  const types = { GET: 'success', POST: 'warning', PUT: 'primary', DELETE: 'danger', PATCH: 'info' }
  return types[method] || 'info'
}

const getStatusCodeType = (statusCode) => {
  if (!statusCode) return 'info'
  if (statusCode >= 200 && statusCode < 300) return 'success'
  if (statusCode >= 300 && statusCode < 400) return 'warning'
  return 'danger'
}

const formatResponseBody = (response) => {
  if (!response) return '无响应'
  if (typeof response === 'object') {
    return JSON.stringify(response, null, 2)
  }
  try {
    const json = JSON.parse(response)
    return JSON.stringify(json, null, 2)
  } catch {
    return response
  }
}

const formatExpectedValue = (assertion) => {
  if (!assertion) return ''
  const field = assertion.field || ''
  const operator = assertion.operator || ''
  let expected = assertion.expectedValue

  if (expected && typeof expected === 'object') {
    expected = expected.expectedValue || expected.eq || JSON.stringify(expected)
  }

  return `${field} ${operator} ${expected}`
}

const loadExecutionHistory = async () => {
  if (!props.scenarioId) return
  historyLoading.value = true
  try {
    const params = {}

    if (historyFilterStatus.value) {
      params.status = historyFilterStatus.value
    }
    if (historyFilterStartDate.value) {
      params.start_date = historyFilterStartDate.value
    }
    if (historyFilterEndDate.value) {
      params.end_date = historyFilterEndDate.value
    }

    const res = await autoTestRequest.get(`/auto-test/scenarios/${props.scenarioId}/history`, { params })

    const items = res.items || []
    const total = res.total || items.length
    const passedCount = items.filter(item => item.status === 'success' || item.status === 'completed').length
    const passRate = total > 0 ? Math.round((passedCount / total) * 100) : 0

    historyStats.value = {
      total_reports: total,
      passed_reports: passedCount,
      pass_rate: passRate
    }

    const successCount = items.filter(item => item.status === 'success' || item.status === 'completed').length
    const failedCount = items.filter(item => item.status === 'failed' || item.status === 'error').length
    executionHistory.value = {
      total: res.total || 0,
      success_count: successCount,
      failed_count: failedCount,
      items: items
    }
  } catch (error) {
    console.error('加载执行历史失败:', error)
    ElMessage.error('加载执行历史失败')
  } finally {
    historyLoading.value = false
  }
}

const resetHistoryFilters = () => {
  historyFilterStatus.value = ''
  historyFilterStartDate.value = ''
  historyFilterEndDate.value = ''
  loadExecutionHistory()
}

const refreshExecutionHistory = () => {
  loadExecutionHistory()
}

const deleteHistoryRecord = async (historyId) => {
  try {
    await ElMessageBox.confirm('确定要删除这条执行记录吗？\n此操作会同时删除硬盘上的报告文件和数据库记录，无法恢复！', '确认删除', {
      confirmButtonText: '确定删除',
      cancelButtonText: '取消',
      type: 'warning'
    })

    if (!props.scenarioId) {
      throw new Error('未找到当前场景ID')
    }
    await autoTestRequest.delete(`/auto-test/scenarios/${props.scenarioId}/history/${historyId}`)
    ElMessage.success('删除成功')
    await loadExecutionHistory()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

const openReport = (reportUrl) => {
  const fullUrl = resolveReportUrl(reportUrl)
  window.open(fullUrl, '_blank')
}

const reRunHistory = (historyRow) => {
  const scenarioId = historyRow.scenario_id || props.scenarioId
  const envId = historyRow.env_id
  if (!scenarioId) {
    ElMessage.error('无法获取场景 ID，请从场景列表运行')
    return
  }
  isRunning.value = true
  reportDetailVisible.value = false
  emit('update:visible', false)
  emit('re-run', { scenarioId, envId, stepCount: historyRow.total_steps || 0 })
}

const viewReportDetail = async (reportId) => {
  try {
    reportDetailLoading.value = true
    reportDetailData.value = null
    expandedDetailSteps.value = []
    isRunning.value = false
    const res = await autoTestRequest.get(`/auto-test/reports/${reportId}`)
    reportDetailData.value = res
    if (res.step_results) {
      const failedIndex = res.step_results.findIndex(s => !s.success)
      if (failedIndex >= 0) {
        expandedDetailSteps.value = [failedIndex]
      }
    }
    reportDetailVisible.value = true
  } catch (error) {
    ElMessage.error('加载报告详情失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    reportDetailLoading.value = false
  }
}

const toggleDetailStep = (index) => {
  const idx = expandedDetailSteps.value.indexOf(index)
  if (idx >= 0) {
    expandedDetailSteps.value.splice(idx, 1)
  } else {
    expandedDetailSteps.value.push(index)
  }
}

watch(() => props.visible, async (newVal) => {
  if (newVal && props.scenarioId) {
    await loadExecutionHistory()
  }
})
</script>

<style scoped>
.history-content {
  height: 100%;
}

.history-summary {
  display: flex;
  align-items: center;
  gap: 12px;
}

.success-text {
  color: #67c23a;
  font-weight: 500;
}

.failed-text {
  color: #f56c6c;
  font-weight: 500;
}

.stats-cards {
  margin-bottom: 20px;
}

.stat-card {
  border-radius: 8px;
  transition: transform 0.2s;
}

.stat-card:hover {
  transform: translateY(-2px);
}

.stat-content {
  text-align: center;
  padding: 12px 0;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  line-height: 1.2;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 13px;
  color: var(--tm-text-secondary);
}

.history-filter-form {
  margin-bottom: 20px;
  padding: 16px;
  background: var(--tm-bg-card);
  border-radius: 8px;
  border: 1px solid var(--tm-border-light);
}

.history-filter-form .el-form-item {
  margin-bottom: 0;
  margin-right: 16px;
}

.history-filter-form .el-form-item:last-child {
  margin-right: 0;
}

.history-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.result-content {
  max-height: 70vh;
  overflow: auto;
}

.result-header-stats {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
}

.step-results {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.step-result-card {
  border: 1px solid var(--tm-border-light);
  border-radius: var(--tm-radius-base);
  padding: 16px;
  background: var(--tm-bg-card);
  transition: all 0.3s;
}

.step-result-card.is-failed {
  border-color: rgba($--color-danger, 0.4);
  background: rgba($--color-danger, 0.02);
}

.step-header {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: var(--tm-radius-small);
  transition: background-color 0.2s;
}

.step-header:hover {
  background: var(--tm-bg-hover);
}

.step-header-skipped {
  opacity: 0.6;
  cursor: default;
}

.step-skipped-hint {
  color: var(--tm-text-secondary);
  font-size: 12px;
  font-style: italic;
  margin-left: 8px;
}

.toggle-icon {
  margin-left: auto;
  transition: transform 0.3s;
}

.toggle-icon.is-expanded {
  transform: rotate(90deg);
}

.step-order {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--tm-color-primary);
  color: var(--tm-text-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
}

.step-name {
  font-weight: 500;
  flex: 1;
  color: var(--tm-text-primary);
}

.step-detail {
  margin-top: 16px;
  padding-left: 36px;
  border-top: 1px solid var(--tm-border-light);
  padding-top: 16px;
}

.detail-url {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 12px;
  color: var(--tm-text-regular);
  word-break: break-all;
  background: var(--tm-bg-page);
  padding: 8px 12px;
  border-radius: var(--tm-radius-small);
  margin-bottom: 12px;
}

.detail-section {
  margin-top: 16px;
}

.detail-section h5 {
  margin: 0 0 12px;
  color: var(--tm-color-primary);
  font-size: 13px;
  font-weight: 600;
}

.request-info {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.response-info {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.info-row {
  margin-bottom: 12px;
}

.info-row:last-child {
  margin-bottom: 0;
}

.info-label {
  display: inline-block;
  min-width: 60px;
  color: var(--tm-text-secondary);
  font-size: 13px;
  margin-right: 8px;
}

.info-value {
  color: var(--tm-text-primary);
  font-size: 13px;
  word-break: break-all;
}

.code-block {
  background: var(--tm-card-bg);
  color: #d4d4d4;
  padding: 12px;
  border-radius: var(--tm-radius-small);
  max-height: 300px;
  overflow: auto;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 12px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-all;
  margin: 8px 0 0 0;
  box-shadow: inset 0 2px 8px rgba(0, 0, 0, 0.2);
}

.step-error {
  margin-top: 12px;
}

.is-skipped {
  background-color: var(--tm-bg-page);
  border-left: 3px solid var(--tm-text-secondary);
}

@media (max-width: 768px) {
  .stats-cards {
    flex-direction: column;
    gap: 12px;
  }

  .stat-card {
    width: 100%;
  }

  .history-filter-form .el-form-item {
    margin-right: 0;
    margin-bottom: 12px;
  }

  .history-filter-form .el-form-item:last-child {
    margin-bottom: 0;
  }
}
</style>
