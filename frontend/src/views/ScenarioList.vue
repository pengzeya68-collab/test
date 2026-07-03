<template>
  <div class="scenario-list-container">
    <!-- 顶部工具栏 -->
    <div class="list-toolbar">
      <div class="toolbar-left">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索场景名称"
          size="default"
          style="width: 240px"
          clearable
          @input="handleSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
      </div>
      <div class="toolbar-right">
        <!-- 环境选择 -->
        <div class="env-select-wrapper">
          <span class="env-label">执行环境：</span>
          <el-select
            v-model="selectedEnvId"
            placeholder="选择环境"
            size="default"
            clearable
            @change="handleEnvChange"
            style="width: 160px"
          >
            <el-option
              v-for="env in environments"
              :key="env.id"
              :label="env.name"
              :value="env.id"
            />
          </el-select>
        </div>
        <el-tooltip content="环境管理" placement="top" popper-class="action-tooltip">
          <el-button :icon="Setting" title="环境管理" @click="openEnvManager" />
        </el-tooltip>
        <el-button type="primary" class="btn-create-scenario" @click="handleCreate">
          <el-icon><Plus /></el-icon>
          新建场景
        </el-button>
        <el-button class="btn-help" @click="showHelp = true">
          <span class="help-icon">❓</span>
          <span class="help-text">使用说明</span>
        </el-button>
      </div>
    </div>

    <!-- 场景列表 -->
    <div class="scenario-grid" v-loading="loading">
      <div
        v-for="(scenario, idx) in filteredScenarios"
        :key="scenario.id"
        class="scenario-card standard-card"
        v-spotlight
        v-fade-in="{ stagger: idx * 60 }"
        @click="handleEdit(scenario)"
      >
        <div class="card-header">
          <h3 class="card-title" :title="scenario.name">{{ scenario.name }}</h3>
          <span :class="['status-badge', scenario.is_active ? 'active' : 'inactive']">
            {{ scenario.is_active ? '启用' : '停用' }}
          </span>
        </div>
        <p class="card-desc">{{ scenario.description || '暂无描述' }}</p>
        <div class="card-meta">
          <span class="meta-chip">
            <el-icon><Coin /></el-icon>
            {{ scenario.step_count ?? (scenario.steps ? scenario.steps.length : 0) }} 步骤
          </span>
          <span class="meta-chip" v-if="scenario.schedule">
            <el-icon><Clock /></el-icon>
            {{ scenario.schedule }}
          </span>
        </div>
        <div class="card-actions" @click.stop>
          <el-tooltip content="运行场景" placement="top" popper-class="action-tooltip">
            <el-button
              class="action-btn action-run"
              size="small"
              :icon="VideoPlay"
              @click.stop="handleRun(scenario)"
            >运行</el-button>
          </el-tooltip>
          <el-tooltip content="编辑场景" placement="top" popper-class="action-tooltip">
            <el-button
              class="action-btn action-edit"
              size="small"
              :icon="Edit"
              @click.stop="handleEdit(scenario)"
            >编辑</el-button>
          </el-tooltip>
          <el-tooltip content="执行历史" placement="top" popper-class="action-tooltip">
            <el-button
              class="action-btn action-history"
              size="small"
              :icon="Timer"
              @click.stop="openHistoryDrawer(scenario)"
            >历史</el-button>
          </el-tooltip>
          <el-dropdown trigger="click" class="action-more-dropdown" @command="(cmd) => handleMoreAction(cmd, scenario)">
            <el-button class="action-btn action-more" size="small" :icon="MoreFilled">
              更多<el-icon class="el-icon--right"><ArrowDown /></el-icon>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="cicd"><el-icon><Link /></el-icon> CI/CD 集成</el-dropdown-item>
                <el-dropdown-item command="schedule"><el-icon><Clock /></el-icon> 定时计划</el-dropdown-item>
                <el-dropdown-item command="toggle">
                  <el-icon><component :is="scenario.is_active ? TurnOff : Open" /></el-icon>
                  {{ scenario.is_active ? '停用场景' : '启用场景' }}
                </el-dropdown-item>
                <el-dropdown-item divided command="delete"><el-icon><Delete /></el-icon> 删除场景</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>
      <BaseEmpty
        v-if="!loading && filteredScenarios.length === 0"
        title="暂无场景"
        description="点击「新建场景」开始编排你的第一个测试场景"
      />
    </div>

    <!-- 新建/编辑场景对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑场景' : '新建场景'"
      width="500px"
    >
      <el-form :model="scenarioForm" label-width="80px">
        <el-form-item label="场景名称" required>
          <el-input v-model="scenarioForm.name" placeholder="请输入场景名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="scenarioForm.description"
            type="textarea"
            :rows="3"
            placeholder="场景描述（可选）"
          />
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="scenarioForm.is_active" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSave">确定</el-button>
      </template>
    </el-dialog>

    <ScenarioExecutionDialog ref="executionDialogRef" v-model="resultDialogVisible" @completed="handleExecutionCompleted" />

    <!-- 定时计划配置对话框 -->
    <ScheduleDialog
      v-model:visible="scheduleDialogVisible"
      :scenario-id="scheduleRow?.id ?? null"
      :scenario-name="scheduleRow?.name ?? ''"
      :cron-expression="scheduleRow?.schedule_cron ?? ''"
      :webhook-url="scheduleRow?.webhook_url ?? ''"
      :environments="environments"
      @schedule-changed="handleScheduleChanged"
    />

    <!-- CI/CD Webhook 配置对话框 -->
    <el-dialog v-model="ciCdDialogVisible" title="CI/CD Webhook 触发配置" width="580px">
      <div class="ci-cd-info">
        <p class="ci-cd-tip">
          请将以下 cURL 命令复制到您的 <strong>GitLab CI / Jenkins Pipeline</strong> 中。<br>
          每次代码部署完成后，会自动触发该场景进行回归测试。
        </p>
        <div class="curl-command-box">
          <template v-if="curlCommand">
            {{ curlCommand }}
          </template>
          <template v-else>
            <span class="curl-command-tip">该场景尚未生成 Webhook Token，请先编辑保存场景以生成。</span>
          </template>
        </div>
        <el-button type="primary" @click="copyCurlCommand">
          <el-icon><DocumentCopy /></el-icon> 复制命令
        </el-button>
      </div>
      <template #footer>
        <el-button @click="ciCdDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 执行历史抽屉 -->
    <ExecutionHistoryDrawer
      v-model:visible="historyDrawerVisible"
      :scenario-id="historyRow?.id ?? null"
      @re-run="handleHistoryReRun"
    />

    <!-- 环境管理抽屉 - 和接口库页面保持一致 -->
    <EnvironmentManager
      v-model="envManagerDrawerVisible"
      @close="handleEnvManagerClose"
    />

    <HelpDrawer
      v-model="showHelp"
      :title="helpData.title"
      :intro="helpData.intro"
      :sections="helpData.sections"
      @close="showHelp = false"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, VideoPlay, Delete, Search, Link, DocumentCopy, Clock, Edit, Timer, Setting, Open, TurnOff, Coin, MoreFilled, ArrowDown } from '@element-plus/icons-vue'
import autoTestRequest from '@/utils/autoTestRequest'
import { helpContent } from '@/utils/help-content'
import HelpDrawer from '@/components/HelpDrawer.vue'
import BaseEmpty from '@/components/base/BaseEmpty.vue'

const helpData = helpContent.scenarioList
import EnvironmentManager from '@/components/EnvironmentManager.vue'
import ScenarioExecutionDialog from '@/components/ScenarioExecutionDialog.vue'
import ScheduleDialog from '@/views/scenario/ScheduleDialog.vue'
import ExecutionHistoryDrawer from '@/views/scenario/ExecutionHistoryDrawer.vue'

const loading = ref(false)
const showHelp = ref(false)
const scenarios = ref([])
const totalScenarios = ref(0)
const searchKeyword = ref('')
const dialogVisible = ref(false)
const isEdit = ref(false)
const scenarioForm = ref({
  name: '',
  description: '',
  is_active: true
})
const currentScenarioId = ref(null)
const resultDialogVisible = ref(false)
const executionDialogRef = ref(null)
const runResult = ref(null)
const expandedSteps = ref([])
let pollingTimer = null
let pollingAbortController = null
let currentTaskId = null
let fakeProgressTimer = null
const isRunning = ref(false)
const isCanceling = ref(false)
const runningTaskProgress = ref(null)

// 定时计划相关
const scheduleDialogVisible = ref(false)
const scheduleRow = ref(null)

// 执行历史相关
const historyDrawerVisible = ref(false)
const historyRow = ref(null)

// CI/CD Webhook 配置对话框
const ciCdDialogVisible = ref(false)
const currentCiCdScene = ref(null)
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

const curlCommand = computed(() => {
  if (!currentCiCdScene.value || !currentCiCdScene.value.webhook_token) {
    return ''
  }
  const baseUrl = window.location.origin
  return `curl -X POST "${baseUrl}/auto-test/scenarios/webhook/${currentCiCdScene.value.webhook_token}" \\
     -H "Content-Type: application/json" \\
     -d '{"env_id": 替换为实际环境ID}'`
})

const openCiCdDialog = (row) => {
  currentCiCdScene.value = row
  ciCdDialogVisible.value = true
}

const handleMoreAction = (cmd, row) => {
  if (cmd === 'cicd') openCiCdDialog(row)
  else if (cmd === 'schedule') openScheduleDialog(row)
  else if (cmd === 'toggle') handleToggleStatus(row, !row.is_active)
  else if (cmd === 'delete') handleDelete(row.id)
}

const copyCurlCommand = async () => {
  if (!curlCommand.value) {
    ElMessage.warning('没有生成命令，该场景尚未生成 Webhook Token，请先编辑保存场景以生成')
    return
  }
  try {
    await navigator.clipboard.writeText(curlCommand.value)
    ElMessage.success('cURL 命令已复制到剪贴板')
  } catch (error) {
    ElMessage.error('复制失败，请手动复制')
  }
}

// 环境选择相关
const envManagerDrawerVisible = ref(false)
const selectedEnvId = ref(null)
const environments = ref([])

const loadEnvironments = async () => {
  try {
    const res = await autoTestRequest.get('/auto-test/environments')
    environments.value = res || []
  } catch (error) {
    console.error('加载环境列表失败:', error)
  }
}

const handleEnvChange = () => {
}

const openEnvManager = () => {
  envManagerDrawerVisible.value = true
}

const handleEnvManagerClose = () => {
  envManagerDrawerVisible.value = false
  loadEnvironments()
}

const filteredScenarios = computed(() => {
  if (!searchKeyword.value) return scenarios.value
  const keyword = searchKeyword.value.toLowerCase()
  return scenarios.value.filter(s =>
    s.name.toLowerCase().includes(keyword) ||
    (s.description && s.description.toLowerCase().includes(keyword))
  )
})

const formatTotalTime = (ms) => {
  if (!ms && ms !== 0) return '0ms'
  if (ms < 1000) return ms + 'ms'
  return (ms / 1000).toFixed(2) + 's'
}

const toggleStepDetail = (index) => {
  const idx = expandedSteps.value.indexOf(index)
  if (idx >= 0) {
    expandedSteps.value.splice(idx, 1)
  } else {
    expandedSteps.value.push(index)
  }
}

const loadScenarios = async () => {
  loading.value = true
  try {
    const res = await autoTestRequest.get('/auto-test/scenarios')
    if (res && res.items) {
      scenarios.value = res.items || []
      totalScenarios.value = res.total || 0
    } else {
      scenarios.value = res || []
      totalScenarios.value = scenarios.value.length
    }
  } catch (error) {
    console.error('加载场景失败:', error)
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
}

const handleCreate = () => {
  isEdit.value = false
  scenarioForm.value = { name: '', description: '', is_active: true }
  dialogVisible.value = true
}

const handleEdit = (row) => {
  emit('edit', row)
}

const handleSave = async () => {
  if (!scenarioForm.value.name) {
    ElMessage.warning('请输入场景名称')
    return
  }
  try {
    if (isEdit.value) {
      await autoTestRequest.put(`/auto-test/scenarios/${currentScenarioId.value}`, scenarioForm.value)
      ElMessage.success('更新成功')
    } else {
      await autoTestRequest.post('/auto-test/scenarios', scenarioForm.value)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    loadScenarios()
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

const handleDelete = async (id) => {
  try {
    await ElMessageBox.confirm(
      '确定要彻底删除该场景及其所有关联记录吗？此操作不可逆！',
      '高危操作警告',
      {
        confirmButtonText: '坚决删除',
        cancelButtonText: '点错了',
        type: 'warning',
      }
    )
  } catch {
    return
  }

  try {
    await autoTestRequest.delete(`/auto-test/scenarios/${id}`)
    ElMessage.success('清理完毕！')
    loadScenarios()
  } catch (error) {
    const msg = error.response?.data?.message || error.response?.data?.error || '删除遭遇异常，请检查关联数据！'
    ElMessage.error(msg)
  }
}

const openScheduleDialog = (row) => {
  scheduleRow.value = row
  scheduleDialogVisible.value = true
}

const handleScheduleChanged = () => {
  loadScenarios()
}

const openHistoryDrawer = (row) => {
  historyRow.value = row
  historyDrawerVisible.value = true
}

const handleHistoryReRun = ({ scenarioId, envId, stepCount }) => {
  const finalEnvId = envId ?? selectedEnvId.value
  if (finalEnvId) {
    selectedEnvId.value = finalEnvId
  }
  executionDialogRef.value?.startExecution(scenarioId, finalEnvId, stepCount)
}

// 停止轮询
const stopPolling = () => {
  if (pollingTimer) {
    clearInterval(pollingTimer)
    pollingTimer = null
  }
  if (pollingAbortController) {
    pollingAbortController.abort()
    pollingAbortController = null
  }
  stopFakeProgress()
}

const pollTaskStatus = async (taskId, scenarioName) => {
  currentTaskId = taskId
  stopPolling()
  pollingAbortController = new AbortController()
  const signal = pollingAbortController.signal
  let pollInFlight = false
  pollingTimer = setInterval(async () => {
    if (pollInFlight) return
    pollInFlight = true
    try {
      const res = await autoTestRequest.get(`/auto-test/tasks/${taskId}`, { signal })
      const state = res.status

      if (state === 'PROGRESS') {
        stopFakeProgress()
        const progress = res.progress || {}
        runningTaskProgress.value = {
          percent: progress.percent || 10,
          current: progress.current || 0,
          total: progress.total || runningTaskProgress.value?.total || 0,
          current_api: progress.current_api || '执行中...'
        }
      }

      if (state === 'completed' || state === 'SUCCESS') {
        stopPolling()
        stopFakeProgress()
        isRunning.value = false
        const resultData = res.result || res
        runningTaskProgress.value = {
          percent: 100,
          current: resultData.total_steps || 0,
          total: resultData.total_steps || 0,
          current_api: '执行完成'
        }
        runResult.value = resultData
        expandedSteps.value = []
        if (resultData && resultData.step_results) {
          const failedIndex = resultData.step_results.findIndex(s => !s.success)
          if (failedIndex >= 0) expandedSteps.value = [failedIndex]
        }
        resultDialogVisible.value = true
        ElMessage.success('执行完成')
      } else if (state === 'failed' || state === 'FAILURE' || state === 'REVOKED') {
        stopPolling()
        stopFakeProgress()
        isRunning.value = false
        if (state === 'REVOKED') {
          ElMessage.warning('⛔ 任务已被终止')
          resultDialogVisible.value = false
        } else {
          ElMessage.error('执行失败: ' + (res.error || '未知错误'))
        }
      }
    } catch (error) {
      if (error?.name === 'CanceledError' || error?.code === 'ERR_CANCELED') return
      stopPolling()
      stopFakeProgress()
      isRunning.value = false
      ElMessage.error('查询任务状态失败: ' + (error.response?.data?.detail || error.message))
    } finally {
      pollInFlight = false
    }
  }, 2000)
}

const handleToggleStatus = async (row, val) => {
  const oldVal = row.is_active
  try {
    await autoTestRequest.put(`/auto-test/scenarios/${row.id}/status`, {
      is_active: val
    })
    row.is_active = val
    ElMessage.success(val ? '场景已启用' : '场景已停用')
  } catch (error) {
    row.is_active = oldVal
    ElMessage.error('状态切换失败: ' + (error.response?.data?.detail || error.message))
  }
}

const handleRun = async (row) => {
  if (!selectedEnvId.value) {
    ElMessage.warning('请先选择执行环境！')
    return
  }
  if (!row.is_active) {
    ElMessage.warning('该场景已停用，无法运行！')
    return
  }
  const stepCount = row.step_count ?? (row.steps ? row.steps.length : 0)
  executionDialogRef.value?.startExecution(row.id, selectedEnvId.value, stepCount)
}

const handleExecutionCompleted = () => {
  loadScenarios()
}

const startFakeProgress = (totalSteps) => {
  stopFakeProgress()
  let fakePercent = 5
  fakeProgressTimer = setInterval(() => {
    if (fakePercent < 85) {
      fakePercent += Math.random() * 3
      if (fakePercent > 85) fakePercent = 85
      runningTaskProgress.value = {
        percent: Math.round(fakePercent),
        current: Math.floor((fakePercent / 100) * totalSteps),
        total: totalSteps,
        current_api: '正在执行步骤...'
      }
    }
  }, 1500)
}

const stopFakeProgress = () => {
  if (fakeProgressTimer) {
    clearInterval(fakeProgressTimer)
    fakeProgressTimer = null
  }
}

const handleCancelTask = async () => {
  if (!currentTaskId) {
    ElMessage.warning('没有正在执行的任务')
    return
  }

  try {
    isCanceling.value = true
    await autoTestRequest.post(`/auto-test/tasks/${currentTaskId}/cancel`)
    stopPolling()
    isRunning.value = false
    isCanceling.value = false
    runningTaskProgress.value = null
    ElMessage.warning('⛔ 任务已被用户强制终止')
    resultDialogVisible.value = false
    currentTaskId = null
  } catch (error) {
    isCanceling.value = false
    ElMessage.error('终止任务失败: ' + (error.response?.data?.detail || error.message))
  }
}

const openAllureReport = () => {
  const resultData = runResult.value || {};
  const url = resultData.report_url;

  if (url) {
    window.open(resolveReportUrl(url), '_blank');
  } else {
    ElMessage.warning('Allure 报告未生成（可能未安装 allure 命令行工具）。请检查后端日志。');
  }
};

const emit = defineEmits(['edit'])

defineExpose({
  loadScenarios
})

onMounted(() => {
  loadScenarios()
  loadEnvironments()
})

onUnmounted(() => {
  stopPolling()
  stopFakeProgress()
})
</script>

<style scoped>
.scenario-list-container {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--tm-bg-page);
}

.list-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
  padding: 16px 20px;
  background: var(--tm-bg-card);
  border-bottom: 1px solid var(--tm-border-light);
  flex-shrink: 0;
}

.toolbar-left,
.toolbar-right {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
  min-width: 0;
}

.toolbar-right > .el-button,
.toolbar-right > .env-select-wrapper {
  flex-shrink: 0;
}

.env-select-wrapper {
  display: flex;
  align-items: center;
  gap: 4px;
}

.env-label {
  color: var(--tm-text-regular);
  font-size: 14px;
  white-space: nowrap;
}

.scenario-grid {
  flex: 1;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
  grid-auto-rows: min-content;
  gap: 20px;
  padding: 20px;
  overflow: auto;
  min-height: 200px;
  align-content: start;
}

.scenario-card {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 22px 24px;
  background: var(--tm-card-bg);
  border: 1px solid var(--tm-border-light);
  border-radius: 14px;
  transition: all 0.3s ease;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  min-height: min-content;
}
.scenario-card::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, rgba(var(--tm-color-primary-rgb), 0.04) 0%, transparent 60%);
  opacity: 0;
  transition: opacity 0.3s;
  pointer-events: none;
}
.scenario-card:hover {
  transform: translateY(-3px);
  border-color: rgba(var(--tm-color-primary-rgb), 0.4);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.4), 0 0 24px rgba(var(--tm-color-primary-rgb), 0.15);
}
.scenario-card:hover::before {
  opacity: 1;
}
.scenario-card:active {
  transform: translateY(-1px);
}

.scenario-card .card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}
.scenario-card .card-title {
  margin: 0;
  font-size: 17px;
  font-weight: 700;
  color: var(--tm-text-primary);
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.scenario-card .card-desc {
  margin: 0;
  font-size: 13px;
  color: var(--tm-text-secondary);
  line-height: 1.6;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  min-height: 42px;
}
.scenario-card .card-meta {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
.scenario-card .meta-chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  background: rgba(var(--tm-color-primary-rgb), 0.04);
  border: 1px solid var(--tm-border-light);
  border-radius: 999px;
  font-size: 12px;
  color: var(--tm-text-secondary);
}
.scenario-card .card-actions {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
  margin-top: 4px;
  padding-top: 12px;
  border-top: 1px solid var(--tm-border-light);
}
.scenario-card .card-actions .action-btn {
  width: 100%;
  justify-content: center;
  font-size: 12px;
  border-radius: 8px;
  transition: all 0.2s ease;
}
.scenario-card .card-actions .action-btn:hover {
  transform: translateY(-1px);
}
.scenario-card .card-actions .action-run {
  color: var(--el-color-primary);
  background: rgba(var(--el-color-primary-rgb), 0.08);
  border: 1px solid rgba(var(--el-color-primary-rgb), 0.2);
}
.scenario-card .card-actions .action-run:hover {
  background: rgba(var(--el-color-primary-rgb), 0.16);
  border-color: rgba(var(--el-color-primary-rgb), 0.4);
}
.scenario-card .card-actions .action-edit {
  color: var(--tm-text-secondary);
  background: rgba(var(--tm-text-secondary-rgb), 0.06);
  border: 1px solid rgba(var(--tm-text-secondary-rgb), 0.15);
}
.scenario-card .card-actions .action-edit:hover {
  background: rgba(var(--tm-text-secondary-rgb), 0.12);
  border-color: rgba(var(--tm-text-secondary-rgb), 0.3);
}
.scenario-card .card-actions .action-history {
  color: var(--el-color-info);
  background: rgba(var(--el-color-info-rgb), 0.08);
  border: 1px solid rgba(var(--el-color-info-rgb), 0.2);
}
.scenario-card .card-actions .action-history:hover {
  background: rgba(var(--el-color-info-rgb), 0.16);
  border-color: rgba(var(--el-color-info-rgb), 0.4);
}
.scenario-card .action-more-dropdown {
  width: 100%;
}
.scenario-card .action-more-dropdown .el-button {
  width: 100%;
}
.scenario-card .card-actions .action-more {
  color: var(--tm-text-secondary);
  background: rgba(var(--tm-text-secondary-rgb), 0.06);
  border: 1px solid rgba(var(--tm-text-secondary-rgb), 0.15);
}
.scenario-card .card-actions .action-more:hover {
  background: rgba(var(--tm-text-secondary-rgb), 0.12);
  border-color: rgba(var(--tm-text-secondary-rgb), 0.3);
}

.status-badge {
  display: inline-flex;
  align-items: center;
  padding: 3px 10px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.02em;
  white-space: nowrap;
}
.status-badge.active {
  background: rgba(var(--el-color-success-rgb), 0.15);
  color: var(--el-color-success);
  border: 1px solid rgba(var(--el-color-success-rgb), 0.3);
  box-shadow: 0 0 12px rgba(var(--el-color-success-rgb), 0.25);
}
.status-badge.inactive {
  background: rgba(var(--tm-text-secondary-rgb), 0.12);
  color: var(--tm-text-secondary);
  border: 1px solid rgba(var(--tm-text-secondary-rgb), 0.25);
}

.running-status {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  text-align: center;
}

.ci-cd-info .ci-cd-tip {
  margin-bottom: 16px;
  color: var(--tm-text-regular);
  line-height: 1.6;
}

.ci-cd-info .curl-command-box {
  background: var(--tm-card-bg);
  padding: 15px;
  border-radius: 6px;
  color: var(--tm-text-regular);
  font-family: 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.6;
  word-break: break-all;
  margin-bottom: 16px;
  border: 1px solid var(--tm-border-light);
}

.ci-cd-info .curl-command-tip {
  color: var(--el-color-warning);
}

.btn-create-scenario {
  flex-shrink: 0;
}

.btn-help {
  flex-shrink: 0;
}

@media (max-width: 1024px) {
  .env-label {
    display: none;
  }

  .env-select-wrapper :deep(.el-select) {
    width: 120px !important;
  }

  .env-select-wrapper .el-select {
    width: 120px !important;
  }

  .btn-help .help-text {
    display: none;
  }

  .btn-help .help-icon {
    margin: 0;
  }
}

@media (max-width: 768px) {
  .list-toolbar {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
  }

  .toolbar-left,
  .toolbar-right {
    justify-content: center;
  }

  .scenario-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 480px) {
  .scenario-card .card-actions {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 640px) {
  :deep(.el-dialog) {
    width: 92vw !important;
    max-width: 580px;
  }
}
</style>
