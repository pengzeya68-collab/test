<template>
  <div class="scenario-editor">
    <!-- 顶部信息栏 -->
    <div class="editor-header">
      <div class="header-left">
        <el-button @click="handleBack">
          <el-icon><Back /></el-icon>
          返回
        </el-button>
        <el-input
          v-model="scenarioForm.name"
          class="scenario-name-input"
          placeholder="场景名称"
          @blur="handleSaveBasic"
        />
      </div>
      <div class="header-right">
        <el-select
          v-model="selectedEnvId"
          placeholder="选择执行环境"
          clearable
          style="width: 160px; margin-right: 12px;"
        >
          <el-option
            v-for="env in environments"
            :key="env.id"
            :label="env.name"
            :value="env.id"
          />
        </el-select>
        <el-button type="primary" @click="handleSave" :loading="saving">
          <el-icon><DocumentCopy /></el-icon>
          保存
        </el-button>
        <el-button @click="handleAddStep">
          <el-icon><Plus /></el-icon>
          添加步骤
        </el-button>
        <el-button type="primary" @click="handleRun" :loading="isRunning">
          <el-icon><VideoPlay /></el-icon>
          运行场景
        </el-button>
        <el-button @click="showHelp = true">❓ 使用说明</el-button>
      </div>
    </div>

    <!-- 主内容区带标签页 -->
    <el-tabs v-model="activeTab" class="scenario-tabs">
      <el-tab-pane label="步骤编排" name="steps">
        <StepList
          :steps="steps"
          :scenario-id="scenarioId"
          @reorder="handleDragEnd"
          @toggle-active="handleStepActiveChange"
          @remove="handleRemoveStep"
          @edit-overrides="handleEditOverrides"
          @add-step="handleAddStep"
        />
      </el-tab-pane>

      <el-tab-pane label="数据驱动" name="data-driven">
        <DataDrivenPanel
          ref="dataDrivenPanelRef"
          :scenario-id="scenarioId"
          :dataset="dataset"
          :env-id="selectedEnvId"
          @save-dataset="onDatasetSave"
          @run-data-driven="onRunDataDriven"
          @dataset-changed="onDatasetChanged"
        />
      </el-tab-pane>

      <el-tab-pane label="执行历史" name="history">
        <!-- 执行历史面板 -->
        <div class="history-panel">
          <div class="history-toolbar">
            <el-button size="small" @click="refreshExecutionHistory">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
            <span class="history-summary">
              共 {{ executionHistory.total }} 次执行，
              成功: {{ executionHistory.success_count }} 次，
              失败: {{ executionHistory.failed_count }} 次
            </span>
          </div>

          <el-table :data="executionHistory.items" style="width: 100%" v-loading="historyLoading">
            <el-table-column prop="id" label="ID" width="80" align="center" />
            <el-table-column prop="status" label="状态" width="100" align="center">
              <template #default="{ row }">
                <el-tag :type="getStatusType(row.status)" size="small">
                  {{ getStatusText(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="total_steps" label="总步骤" width="80" align="center" />
            <el-table-column prop="success_steps" label="成功" width="80" align="center">
              <template #default="{ row }">
                <span class="success-text">{{ row.success_steps }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="failed_steps" label="失败" width="80" align="center">
              <template #default="{ row }">
                <span class="failed-text">{{ row.failed_steps }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="total_time" label="耗时" width="100" align="center">
              <template #default="{ row }">
                {{ (row.total_time / 1000).toFixed(2) }}s
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="执行时间" width="180" />
            <el-table-column label="操作" width="180" align="center" fixed="right">
              <template #default="{ row }">
                <el-button
                  v-if="row.report_url"
                  size="small"
                  type="primary"
                  link
                  @click="openReport(row.report_url)"
                >
                  查看报告
                </el-button>
              </template>
            </el-table-column>
          </el-table>

          <el-empty v-if="executionHistory.items.length === 0 && !historyLoading" description="暂无执行记录" />
        </div>
      </el-tab-pane>
    </el-tabs>

    <!-- 添加步骤对话框 -->
    <el-dialog v-model="addStepDialogVisible" title="添加步骤" width="70%" destroy-on-close append-to-body>
      <div class="add-step-content">
        <el-input
          v-model="caseSearchKeyword"
          placeholder="搜索接口名称"
          size="default"
          style="width: 300px; margin-bottom: 16px"
          clearable
          @input="handleSearchCases"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>

        <el-table
          ref="caseTableRef"
          :data="availableCases"
          style="width: 100%"
          @selection-change="handleCaseSelectionChange"
        >
          <el-table-column type="selection" width="50" />
          <el-table-column label="请求方法" width="100" align="center">
            <template #default="{ row }">
              <el-tag :type="getMethodType(row.method)" effect="dark" size="small">
                {{ row.method }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="name" label="接口名称" min-width="180" />
          <el-table-column prop="url" label="URL" min-width="280" show-overflow-tooltip />
        </el-table>
      </div>
      <template #footer>
        <el-button @click="addStepDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleConfirmAddSteps">确定添加</el-button>
      </template>
    </el-dialog>

    <ScenarioExecutionDialog ref="executionDialogRef" v-model="resultDialogVisible" @completed="handleExecutionCompleted" />

    <HelpDrawer
      v-model="showHelp"
      :title="helpData.title"
      :intro="helpData.intro"
      :sections="helpData.sections"
    />
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted } from 'vue'
import { onBeforeRouteLeave } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Plus, VideoPlay, Back, Search, Refresh, DocumentCopy } from '@element-plus/icons-vue'
import autoTestRequest from '@/utils/autoTestRequest'
import { helpContent } from '@/utils/help-content'
import HelpDrawer from '@/components/HelpDrawer.vue'

const helpData = helpContent.scenarioEditor
import ScenarioExecutionDialog from '@/components/ScenarioExecutionDialog.vue'
import DataDrivenPanel from '@/views/scenario/DataDrivenPanel.vue'
import StepList from '@/views/scenario/StepList.vue'

const props = defineProps({
  scenarioId: {
    type: [Number, String],
    required: true
  }
})

const emit = defineEmits(['back'])

const scenarioForm = ref({
  name: '',
  description: '',
  is_active: true
})

const steps = ref([])
const addStepDialogVisible = ref(false)
const availableCases = ref([])
const caseSearchKeyword = ref('')
const selectedCases = ref([])
const caseTableRef = ref(null)
const resultDialogVisible = ref(false)
const executionDialogRef = ref(null)
let pollingTimer = null
let pollingAbortController = null

const dataDrivenPanelRef = ref(null)
const dataset = ref({ columns: [], rows: [] })

const activeTab = ref('steps')

const historyLoading = ref(false)
const executionHistory = ref({
  total: 0,
  success_count: 0,
  failed_count: 0,
  items: []
})

const environments = ref([])
const selectedEnvId = ref(null)

const isRunning = ref(false)
const saving = ref(false)
const showHelp = ref(false)

const getMethodType = (method) => {
  const types = { GET: 'success', POST: 'warning', PUT: 'primary', DELETE: 'danger', PATCH: 'info' }
  return types[method] || 'info'
}

const resetEditorState = () => {
  scenarioForm.value = {
    name: '',
    description: '',
    is_active: true
  }
  steps.value = []
  dataset.value = { columns: [], rows: [] }
  executionHistory.value = {
    total: 0,
    success_count: 0,
    failed_count: 0,
    items: []
  }
}

const loadScenario = async () => {
  try {
    const res = await autoTestRequest.get(`/auto-test/scenarios/${props.scenarioId}`)
    scenarioForm.value = {
      name: res.name,
      description: res.description,
      is_active: res.is_active
    }
    steps.value = res.steps || []
  } catch (error) {
    ElMessage.error('加载场景失败')
  }
}

const handleSaveBasic = async () => {
  if (!scenarioForm.value.name?.trim()) return
  try {
    await autoTestRequest.put(`/auto-test/scenarios/${props.scenarioId}`, scenarioForm.value)
  } catch (error) {
    ElMessage.error('保存失败')
  }
}

const handleSave = async () => {
  saving.value = true
  try {
    await autoTestRequest.put(`/auto-test/scenarios/${props.scenarioId}`, scenarioForm.value)
    ElMessage.success('保存成功')
  } catch (error) {
    ElMessage.error('保存失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    saving.value = false
  }
}

const handleBack = () => {
  emit('back')
}

const handleAddStep = async () => {
  addStepDialogVisible.value = true
  caseSearchKeyword.value = ''
  selectedCases.value = []
  await loadAvailableCases()
}

const loadAvailableCases = async () => {
  try {
    const params = {}
    if (caseSearchKeyword.value) {
      params.keyword = caseSearchKeyword.value
    }
    const res = await autoTestRequest.get('/auto-test/scenarios/available-cases', { params })
    availableCases.value = res || []
  } catch (error) {
    console.error('加载接口列表失败:', error)
  }
}

const handleSearchCases = () => {
  loadAvailableCases()
}

const handleCaseSelectionChange = (selection) => {
  selectedCases.value = selection
}

const handleConfirmAddSteps = async () => {
  if (selectedCases.value.length === 0) {
    ElMessage.warning('请选择至少一个接口')
    return
  }

  const currentMaxOrder = steps.value.length > 0
    ? Math.max(...steps.value.map(step => Number(step.step_order) || 0))
    : -1
  let failCount = 0
  for (let i = 0; i < selectedCases.value.length; i++) {
    const caseItem = selectedCases.value[i]
    try {
      await autoTestRequest.post(`/auto-test/scenarios/${props.scenarioId}/steps`, {
        api_case_id: caseItem.id,
        step_order: currentMaxOrder + i + 1,
        is_active: true
      })
    } catch {
      failCount++
    }
  }
  addStepDialogVisible.value = false
  await loadScenario()
  if (failCount > 0) {
    ElMessage.warning(`${failCount} 个步骤添加失败，其余已成功`)
  } else {
    ElMessage.success('添加成功')
  }
}

const handleRemoveStep = async (step) => {
  try {
    await autoTestRequest.delete(`/auto-test/scenarios/${props.scenarioId}/steps/${step.id}`)
    ElMessage.success('移除成功')
    await loadScenario()
  } catch (error) {
    ElMessage.error('移除失败')
  }
}

const handleStepActiveChange = async (step) => {
  const oldActive = step.is_active
  // 注意：此时 step.is_active 已被 switch 组件改为新值
  try {
    await autoTestRequest.put(`/auto-test/scenarios/${props.scenarioId}/steps/${step.id}`, {
      is_active: step.is_active
    })
  } catch (error) {
    step.is_active = !step.is_active  // 回滚 UI 状态
    ElMessage.error('更新失败')
  }
}

const handleDragEnd = async (stepOrders) => {
  try {
    await autoTestRequest.put(`/auto-test/scenarios/${props.scenarioId}/steps/reorder`, stepOrders)
  } catch (error) {
    ElMessage.error('保存排序失败')
    await loadScenario()
  }
}

const handleEditOverrides = () => {
}

const onDatasetSave = () => {
}

const onRunDataDriven = () => {
}

const onDatasetChanged = (data) => {
  dataset.value = { columns: data.columns, rows: data.rows }
}

const stopPolling = () => {
  if (pollingTimer) {
    clearInterval(pollingTimer)
    pollingTimer = null
  }
  if (pollingAbortController) {
    pollingAbortController.abort()
    pollingAbortController = null
  }
}

const handleRun = async () => {
  if (!selectedEnvId.value) {
    ElMessage.warning('请先选择执行环境！')
    return
  }
  if (scenarioForm.value && !scenarioForm.value.is_active) {
    ElMessage.warning('该场景已停用，无法运行！')
    return
  }
  isRunning.value = true
  try {
    const stepCount = steps.value ? steps.value.length : 0
    await executionDialogRef.value?.startExecution(props.scenarioId, selectedEnvId.value, stepCount)
  } catch {
    isRunning.value = false
  }
}

const handleExecutionCompleted = () => {
  isRunning.value = false
  loadExecutionHistory()
}

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

const loadExecutionHistory = async () => {
  historyLoading.value = true
  try {
    const res = await autoTestRequest.get(`/auto-test/scenarios/${props.scenarioId}/history`)
    const items = res.items || []
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

const refreshExecutionHistory = () => {
  loadExecutionHistory()
}

const getStatusType = (status) => {
  const types = { success: 'success', completed: 'success', failed: 'danger', error: 'warning', running: 'primary', cancelled: 'info' }
  return types[status] || 'info'
}

const getStatusText = (status) => {
  const texts = { success: '成功', completed: '成功', failed: '失败', error: '异常', running: '运行中', cancelled: '已取消' }
  return texts[status] || status
}

const openReport = (reportUrl) => {
  const fullUrl = resolveReportUrl(reportUrl)
  window.open(fullUrl, '_blank')
}

const loadEnvironments = async () => {
  try {
    const res = await autoTestRequest.get('/auto-test/environments')
    environments.value = res || []
    if (environments.value.length > 0) {
      const defaultEnv = environments.value.find(e => e.is_default)
      if (defaultEnv) {
        selectedEnvId.value = defaultEnv.id
      } else {
        selectedEnvId.value = environments.value[0].id
      }
    }
  } catch (error) {
    console.error('加载环境列表失败:', error)
  }
}

onMounted(() => {
  loadEnvironments()
})

watch(
  () => props.scenarioId,
  async () => {
    stopPolling()
    resetEditorState()
    await loadScenario()
    await loadExecutionHistory()
  },
  { immediate: true }
)

onUnmounted(() => {
  stopPolling()
})

onBeforeRouteLeave(async () => {
  await dataDrivenPanelRef.value?.flushSave()
})
</script>

<style scoped>
.scenario-editor {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--tm-card-bg);
  border-radius: 12px;
  border: var(--tm-card-border);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
}

.editor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  background: rgba(var(--tm-bg-page-rgb), 0.5);
  border-bottom: 1px solid var(--tm-border-light);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-right {
  display: flex;
  gap: 12px;
}

.scenario-name-input {
  width: 300px;
  font-size: 18px;
  font-weight: 500;
}

.scenario-name-input :deep(.el-input__inner) {
  border: none;
  background: transparent;
}

.add-step-content {
  max-height: 60vh;
  overflow: auto;
}

.result-content {
  max-height: 70vh;
  overflow: auto;
}

.result-summary {
  display: flex;
  align-items: center;
  gap: 16px;
}

.summary-info {
  color: var(--tm-text-regular);
}

.step-result-card {
  padding: 12px;
  margin-bottom: 12px;
  border: 1px solid var(--tm-border-light);
  border-radius: 4px;
  background: rgba(var(--tm-bg-page-rgb), 0.5);
}

.step-result-card.is-failed {
  border-color: rgba(245, 108, 108, 0.6);
  background: rgba(245, 108, 108, 0.05);
}

.step-header {
  display: flex;
  align-items: center;
  gap: 10px;
}

.step-detail {
  margin-top: 8px;
  padding-left: 38px;
}

.info-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.info-label {
  color: var(--tm-text-secondary);
}

.context-vars h4 {
  margin: 0 0 12px;
  color: var(--tm-text-primary);
}

.vars-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.var-tag {
  font-size: 12px;
}

/* 标签页样式 */
.scenario-tabs {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: var(--tm-card-bg);
  overflow: hidden;
  border-radius: 0 0 12px 12px;
}

:deep(.el-tabs__content) {
  flex: 1;
  overflow: auto;
  padding: 16px;
}

:deep(.el-tabs__header) {
  background: rgba(var(--tm-bg-page-rgb), 0.5);
  margin: 0;
  border-bottom: 1px solid var(--tm-border-light);
}

/* 执行历史面板 */
.history-panel {
  background: var(--tm-card-bg);
  border-radius: 4px;
  border: 1px solid var(--tm-border-light);
  padding: 16px;
}

.step-error .error-block {
  background: rgba(245, 108, 108, 0.1);
  color: #f56c6c;
  border: 1px solid rgba(245, 108, 108, 0.3);
  border-radius: 6px;
  padding: 12px;
  font-family: 'Courier New', monospace;
  white-space: pre-wrap;
  word-break: break-all;
  margin: 0;
  line-height: 1.5;
}

.history-toolbar {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
}

.history-summary {
  color: var(--tm-text-secondary);
  font-size: 14px;
}

.success-text {
  color: #67c23a;
  font-weight: 500;
}

.failed-text {
  color: #f56c6c;
  font-weight: 500;
}
</style>
