<template>
  <el-drawer
    v-model="visible"
    title="运行结果"
    size="60%"
    :before-close="handleClose"
  >
    <div class="run-result-view">
      <el-alert
        v-if="runRecord?.id"
        type="info"
        :closable="false"
        class="run-banner"
      >
        <template #title>
          运行记录已保存
        </template>
      </el-alert>

      <el-card class="summary-card" shadow="never" v-if="result">
        <div class="summary-row">
          <div class="summary-item">
            <span class="summary-label">状态</span>
            <el-tag :type="statusTagType(result.status)" size="large">
              {{ statusLabel(result.status) }}
            </el-tag>
          </div>
          <div class="summary-item">
            <span class="summary-label">总步骤</span>
            <span class="summary-value">{{ result.totalSteps }}</span>
          </div>
          <div class="summary-item">
            <span class="summary-label">通过</span>
            <span class="summary-value text-success">{{ result.passedSteps }}</span>
          </div>
          <div class="summary-item">
            <span class="summary-label">失败</span>
            <span class="summary-value text-danger">{{ result.failedSteps }}</span>
          </div>
          <div class="summary-item">
            <span class="summary-label">耗时</span>
            <span class="summary-value">{{ (result.durationMs / 1000).toFixed(2) }}s</span>
          </div>
        </div>
      </el-card>

      <el-card class="events-card" shadow="never" v-if="running || events.length">
        <template #header>
          <div class="events-header">
            <span>执行过程</span>
            <div class="run-controls">
  <el-tag v-if="paused" type="warning" size="small">已暂停：{{ pausedStep?.stepName }}</el-tag><span v-if="paused" class="paused-location" :title="pausedStep?.url">{{ pausedStep?.title || pausedStep?.url || '当前页面' }}</span><el-button v-if="pausedStep?.screenshotPath" size="small" @click="viewScreenshot(pausedStep.screenshotPath)">查看当前画面</el-button>
  <el-tag v-else-if="running" type="warning" size="small">正在运行</el-tag>
  <el-button v-if="running && !paused" size="small" @click="pauseRun">暂停</el-button>
  <el-button v-if="paused" size="small" type="primary" @click="resumeRun('step')">单步执行</el-button>
  <el-button v-if="paused" size="small" type="success" @click="resumeRun('continue')">继续运行</el-button>
  <el-button v-if="running" size="small" type="danger" plain @click="cancelRun">停止运行</el-button>
</div>
          </div>
        </template>
        <div class="events-list" ref="eventsList">
          <div
            v-for="(event, index) in events"
            :key="index"
            class="event-item"
            :class="`event-${event.type.replace(':', '-')}`"
          >
            <span class="event-time">{{ formatTime(event) }}</span>
            <span class="event-icon">{{ eventIcon(event) }}</span>
            <span class="event-text">{{ formatEvent(event) }}</span>
          </div>
        </div>
      </el-card>

      <el-card class="steps-result-card" shadow="never" v-if="result">
        <template #header>
          <span>步骤结果</span>
        </template>
        <el-table :data="result.stepResults" stripe size="small">
          <el-table-column label="#" width="50" type="index" />
          <el-table-column prop="stepId" label="测试步骤" min-width="160" show-overflow-tooltip><template #default="{ row }">{{ stepNames[row.stepId] || '未命名步骤' }}</template></el-table-column>
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="stepStatusTagType(row.status)" size="small">
                {{ stepStatusLabel(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="durationMs" label="耗时" width="100">
            <template #default="{ row }">
              {{ row.durationMs > 0 ? `${row.durationMs}ms` : '—' }}
            </template>
          </el-table-column>
          <el-table-column prop="error" label="错误信息" min-width="300" show-overflow-tooltip>
            <template #default="{ row }">
              <span v-if="row.error" class="error-text">{{ row.error }}</span>
              <span v-else class="text-muted">—</span>
            </template>
          </el-table-column>
          <el-table-column label="截图" width="100">
            <template #default="{ row }">
              <el-link
                v-if="row.screenshotPath"
                type="primary"
                :underline="false"
                @click="viewScreenshot(row.screenshotPath)"
              >
                查看截图
              </el-link>
              <span v-else class="text-muted">—</span>
            </template>
          </el-table-column>
        </el-table>
      </el-card>

      <el-empty v-if="!result && !running" description="点击“运行”按钮执行用例" />
    </div>
    <el-dialog v-model="screenshotVisible" title="失败截图" width="80%" append-to-body>
      <img v-if="screenshotData" :src="screenshotData" class="screenshot-preview" alt="失败步骤截图" />
    </el-dialog>  </el-drawer>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import uiAutomationApi from '@/api/ui-automation'
import { getServerUrl } from '@/utils/server-config'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
})
const emit = defineEmits(['update:modelValue', 'run-finished'])

const visible = ref(props.modelValue)
const running = ref(false)
const events = ref([])
const result = ref(null)
const eventsList = ref(null)
const runRecord = ref(null)
const eventSequence = ref(0)
const backendSyncWarningShown = ref(false)
const runCreateKey = ref('')
const currentCorrelationId = ref('')
const stepNames = ref({})
const screenshotVisible = ref(false)
const screenshotData = ref('')
const paused = ref(false)
const pausedStep = ref(null)

watch(() => props.modelValue, (val) => {
  visible.value = val
})

watch(visible, (val) => {
  emit('update:modelValue', val)
})

function authValidationUrl(snapshot) {
  const firstGoto=(snapshot.steps||[]).find(step=>step.enabled!==false&&step.type==='goto')?.input?.url||''
  if(/^https?:\/\//i.test(firstGoto))return firstGoto
  if(snapshot.base_url&&firstGoto){try{return new URL(firstGoto,snapshot.base_url).toString()}catch{}}
  return /^https?:\/\//i.test(snapshot.base_url||'')?snapshot.base_url:''
}
async function ensureAuthStateReady(authStateId,caseSnapshot) {
  if(!authStateId)return
  const check=await window.testmaster.authStates.validate(authStateId,authValidationUrl(caseSnapshot))
  if(check.valid===false)throw new Error('登录态不可用：'+check.reason+'。请返回用例编辑器点击“更新登录态”后再运行')
}

async function startRun({ caseSnapshot, runContext, onEvent, debugMode = false, environmentId = null, authStateId = null }) {
  if (!window.testmaster) {
    ElMessage.warning('当前是网页预览模式，不能直接执行 UI 自动化。请打开桌面版 TestMaster 后再运行。')
    return
  }

  await ensureAuthStateReady(authStateId,caseSnapshot)
  stepNames.value = Object.fromEntries((caseSnapshot.steps || []).map(step => [step.id, step.name || step.type]))
  paused.value = false
  pausedStep.value = null
  events.value = []
  result.value = null
  running.value = true
  visible.value = true
  runRecord.value = null
  eventSequence.value = 0
  backendSyncWarningShown.value = false
  runCreateKey.value = window.crypto?.randomUUID?.() || ('run-' + Date.now() + '-' + Math.random().toString(16).slice(2))
  try {
    runRecord.value = await uiAutomationApi.createRun({
      case_id: runContext.caseId,
      case_version_id: runContext.caseVersionId,
      client_run_key: runCreateKey.value,
      trigger_type: 'manual',
      environment_id: environmentId,
    })
  } catch (error) {
    maybeWarnBackendSync(error)
  }

  try {
    const { correlationId, promise } = window.testmaster.execution.runCase(caseSnapshot, {
      headless: false,
      screenshotsOnFailure: true,
      traceOnFailure: true,
      debugMode,
      authStateId,
      runtimeConfigRequest: environmentId == null ? null : { serverUrl: getServerUrl(), token: localStorage.getItem('token') || '', environmentId },
      onEvent: async (event) => {
        events.value.push(event)
        if (event.type === 'run:paused') { paused.value = true; pausedStep.value = event }
        if (event.type === 'run:resumed') { paused.value = false }
        onEvent?.(event)
        await syncEventToBackend(event)
        nextTick(() => {
          if (eventsList.value) {
            eventsList.value.scrollTop = eventsList.value.scrollHeight
          }
        })
      },
    })

    currentCorrelationId.value = correlationId
    result.value = await promise
    await registerArtifactsFromResult(result.value)
    await refreshRunDetails()
  } catch (error) {
    const failureEvent = {
      type: 'log',
      level: 'error',
      message: `运行失败: ${error.message}`,
    }
    events.value.push(failureEvent)
    await syncEventToBackend(failureEvent)
    maybeWarnBackendSync(error)
  } finally {
    running.value = false
    paused.value = false
    pausedStep.value = null
    currentCorrelationId.value = ''
    emit('run-finished')
  }
}

async function syncEventToBackend(event) {
  if (!runRecord.value?.id) {
    return
  }

  eventSequence.value += 1
  const payload = {
    sequence: eventSequence.value,
    type: event.type,
    stepId: event.stepId,
    stepName: event.stepName,
    stepType: event.stepType,
    durationMs: event.durationMs,
    totalSteps: event.totalSteps,
    passedSteps: event.passedSteps,
    failedSteps: event.failedSteps,
    status: event.type === 'network' ? undefined : event.status,
    httpStatus: event.type === 'network' ? event.status : undefined,
    text: event.text,
    url: event.url,
    method: event.method,
    reason: event.reason,
    error: event.error,
    screenshotPath: event.screenshotPath,
    level: event.level,
    message: event.message,
  }

  try {
    await uiAutomationApi.appendRunEvents(runRecord.value.id, [payload])
  } catch (error) {
    maybeWarnBackendSync(error)
  }
}

async function registerArtifactsFromResult(runResult) {
  if (!runRecord.value?.id || !runResult?.stepResults?.length) {
    return
  }

  const screenshotPaths = [...new Set(
    runResult.stepResults
      .map((stepResult) => stepResult.screenshotPath)
      .filter(Boolean)
  )]

  for (const screenshotPath of screenshotPaths) {
    try {
      if (window.testmaster?.artifacts?.read) {
        const artifactFile = await window.testmaster.artifacts.read(screenshotPath)
        await uiAutomationApi.uploadRunArtifact(runRecord.value.id, {
          type: 'screenshot',
          filename: artifactFile.filename,
          mime_type: 'image/png',
          size_bytes: artifactFile.sizeBytes,
          content_base64: artifactFile.contentBase64,
        })
      } else {
        await uiAutomationApi.registerRunArtifact(runRecord.value.id, {
          type: 'screenshot',
          filename: screenshotPath.split(/[/\\]/).pop(),
          mime_type: 'image/png',
        })
      }
    } catch (error) {
      maybeWarnBackendSync(error)
      break
    }
  }
  if (runResult.tracePath) {
    try {
      const artifactFile = await window.testmaster.artifacts.read(runResult.tracePath)
      await uiAutomationApi.uploadRunArtifact(runRecord.value.id, {
        type: 'trace',
        filename: artifactFile.filename,
        mime_type: 'application/zip',
        size_bytes: artifactFile.sizeBytes,
        content_base64: artifactFile.contentBase64,
      })
    } catch (error) {
      maybeWarnBackendSync(error)
    }
  }
}

async function refreshRunDetails() {
  if (!runRecord.value?.id) {
    return
  }

  try {
    const [run, stepResults, artifacts] = await Promise.all([
      uiAutomationApi.getRun(runRecord.value.id),
      uiAutomationApi.listRunStepResults(runRecord.value.id),
      uiAutomationApi.listRunArtifacts(runRecord.value.id),
    ])
    runRecord.value = {
      ...run,
      stepResults: stepResults.items || [],
      artifacts: artifacts.items || [],
    }
  } catch (error) {
    maybeWarnBackendSync(error)
  }
}

function maybeWarnBackendSync(error) {
  if (backendSyncWarningShown.value) {
    return
  }
  backendSyncWarningShown.value = true
  ElMessage.warning(error?.message || '运行结果已本地完成，但同步到服务端时出现问题。')
}

function handleClose(done) {
  if (running.value) {
    ElMessage.warning('运行进行中，请等待完成后再关闭。')
    return
  }
  done()
}

async function pauseRun() {
  if (!currentCorrelationId.value) return
  try { await window.testmaster.execution.pause(currentCorrelationId.value) }
  catch (error) { ElMessage.error(error?.message || '暂停失败') }
}

async function resumeRun(mode) {
  if (!currentCorrelationId.value) return
  try { await window.testmaster.execution.resume(currentCorrelationId.value, mode); paused.value = false }
  catch (error) { ElMessage.error(error?.message || '继续运行失败') }
}
async function cancelRun() {
  if (!currentCorrelationId.value) return
  try {
    await window.testmaster.execution.cancel(currentCorrelationId.value)
    ElMessage.info('正在停止本次运行')
  } catch (error) {
    ElMessage.error(error?.message || '停止失败')
  }
}

async function viewScreenshot(path) {
  try {
    const file = await window.testmaster.artifacts.read(path)
    screenshotData.value = `data:image/png;base64,${file.contentBase64}`
    screenshotVisible.value = true
  } catch (error) {
    ElMessage.error(error?.message || '截图读取失败')
  }
}

function statusLabel(status) {
  const map = { passed: '通过', failed: '失败', cancelled: '已取消', error: '错误' }
  return map[status] || status
}

function statusTagType(status) {
  const map = { passed: 'success', failed: 'danger', cancelled: 'info', error: 'danger' }
  return map[status] || 'info'
}

function stepStatusLabel(status) {
  const map = { passed: '通过', failed: '失败', skipped: '跳过', cancelled: '已取消' }
  return map[status] || status
}

function stepStatusTagType(status) {
  const map = { passed: 'success', failed: 'danger', skipped: 'info', cancelled: 'warning' }
  return map[status] || 'info'
}

function formatTime() {
  return new Date().toLocaleTimeString('zh-CN')
}

function eventIcon(event) {
  const map = {
    'run:start': '▶',
    'run:finish': '■',
    'step:start': '•',
    'step:pass': '✓',
    'step:fail': '✕',
    'step:skip': '○',
    log: 'i',
  }
  return map[event.type] || '·'
}

function formatEvent(event) {
  switch (event.type) {
    case 'run:start':
      return `开始运行，共 ${event.totalSteps} 个步骤`
    case 'run:finish':
      return `运行结束：${statusLabel(event.status)}，通过 ${event.passedSteps}，失败 ${event.failedSteps}，耗时 ${(event.durationMs / 1000).toFixed(2)} 秒`
    case 'step:start':
      return `开始执行：${event.stepName || stepNames.value[event.stepId] || '未命名步骤'}`
    case 'step:pass':
      return `步骤通过 (${event.durationMs}ms)`
    case 'step:fail':
      return `步骤失败: ${event.error} (${event.durationMs}ms)`
    case 'step:skip':
      return `步骤跳过: ${event.reason}`
    case 'log':
      if (event.message?.startsWith('Trace saved:')) return '运行诊断文件已保存'
      return event.message || '执行信息'
    default:
      return JSON.stringify(event)
  }
}

defineExpose({ startRun })
</script>

<style scoped lang="scss">
.run-result-view {
  display: flex;
  flex-direction: column;
  gap: 16px;

  .run-banner {
    margin-bottom: 4px;
  }

  .summary-card {
    .summary-row {
      display: flex;
      gap: 32px;
      justify-content: space-around;
      flex-wrap: wrap;
    }

    .summary-item {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 8px;

      .summary-label {
        font-size: 12px;
        color: var(--el-text-color-secondary);
      }

      .summary-value {
        font-size: 24px;
        font-weight: 600;

        &.text-success { color: var(--el-color-success); }
        &.text-danger { color: var(--el-color-danger); }
      }
    }
  }

  .events-card {
    .events-header {
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .events-list {
      max-height: 300px;
      overflow-y: auto;
      font-family: 'Consolas', 'Monaco', monospace;
      font-size: 13px;
    }

    .event-item {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 4px 0;
      border-bottom: 1px solid var(--el-border-color-lighter);

      .event-time {
        color: var(--el-text-color-secondary);
        font-size: 11px;
        flex-shrink: 0;
      }

      .event-icon {
        width: 18px;
        text-align: center;
        flex-shrink: 0;
      }

      .event-text {
        flex: 1;
      }

      &.event-step-fail .event-text {
        color: var(--el-color-danger);
      }

      &.event-step-pass .event-text {
        color: var(--el-color-success);
      }
    }
  }

  .error-text {
    color: var(--el-color-danger);
    font-size: 12px;
  }

  .text-muted {
    color: var(--el-text-color-placeholder);
  }

  .step-id {
    font-family: monospace;
    font-size: 12px;
    color: var(--el-text-color-secondary);
  }
}
.run-controls { display: flex; align-items: center; gap: 8px; }
.screenshot-preview { display: block; max-width: 100%; max-height: 72vh; margin: 0 auto; }
</style>














