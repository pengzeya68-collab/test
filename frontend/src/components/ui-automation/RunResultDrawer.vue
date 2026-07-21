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

      <el-card v-if="runRecord?.id && nonPassingRun" class="analysis-card" shadow="never">
        <template #header><div class="analysis-header"><span>失败归因建议</span><el-button size="small" :loading="analysisLoading" @click="analyzeFailure">生成建议</el-button></div></template>
        <el-empty v-if="!failureAnalysis" :image-size="42" description="尚未生成归因建议" />
        <div v-else class="analysis-content">
          <div><el-tag type="warning">{{ categoryLabel(failureAnalysis.category) }}</el-tag><span class="confidence">置信度 {{ Math.round((failureAnalysis.confidence || 0) * 100) }}%</span></div>
          <div class="analysis-block"><strong>证据</strong><ul><li v-for="item in failureAnalysis.evidence" :key="item">{{ item }}</li></ul></div>
          <div class="analysis-block"><strong>待确认项</strong><ul><li v-for="item in failureAnalysis.unknowns" :key="item">{{ item }}</li></ul></div>
          <div class="analysis-block"><strong>建议动作</strong><ol><li v-for="item in failureAnalysis.next_actions" :key="item">{{ item }}</li></ol></div>
          <div class="analysis-feedback">
            <el-radio-group v-model="analysisFeedbackAccepted" size="small">
              <el-radio-button :label="true">归因正确</el-radio-button>
              <el-radio-button :label="false">需要纠正</el-radio-button>
            </el-radio-group>
            <el-select v-if="analysisFeedbackAccepted === false" v-model="analysisCorrectedCategory" size="small" placeholder="选择正确类别">
              <el-option label="环境问题" value="environment" />
              <el-option label="测试数据问题" value="data" />
              <el-option label="产品缺陷" value="product_defect" />
              <el-option label="自动化脚本问题" value="script" />
              <el-option label="暂时未知" value="unknown" />
            </el-select>
            <el-button type="primary" size="small" :loading="analysisFeedbackSaving" @click="submitAnalysisFeedback">提交复核</el-button>
          </div>
        </div>
      </el-card>

      <el-card v-if="runRecord?.id && nonPassingRun" class="report-card" shadow="never">
        <template #header>
          <div class="analysis-header">
            <span>缺陷报告与运行产物</span>
            <el-button size="small" type="primary" :loading="reportLoading" @click="openDefectReport">查看报告</el-button>
          </div>
        </template>
        <span class="report-hint">报告基于已保存的执行版本、脱敏环境摘要、失败步骤和已上传产物生成。</span>
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
    </el-dialog>
    <el-dialog v-model="reportVisible" title="缺陷报告" width="min(1080px, 92vw)" append-to-body>
      <div v-loading="reportLoading" class="defect-report">
        <template v-if="defectReport">
          <div class="report-meta">
            <el-tag :type="statusTagType(defectReport.status)">{{ statusLabel(defectReport.status) }}</el-tag>
            <span>执行标识：{{ defectReport.execution_id || '未生成' }}</span>
            <span>环境：{{ defectReport.environment?.name || '未指定' }}</span>
            <span>浏览器：{{ defectReport.reproduction?.browser || 'chromium' }}</span>
          </div>
          <el-descriptions title="复现前提" :column="2" border size="small">
            <el-descriptions-item label="用例版本">{{ defectReport.execution_version?.case_version_id || '未指定' }}</el-descriptions-item>
            <el-descriptions-item label="登录态">{{ defectReport.reproduction?.requires_login_state ? '需要已保存登录态' : '不需要' }}</el-descriptions-item>
            <el-descriptions-item label="桌面端版本">{{ defectReport.reproduction?.desktop_version || '未记录' }}</el-descriptions-item>
            <el-descriptions-item label="尝试次数">{{ defectReport.execution_version?.attempt || 1 }}</el-descriptions-item>
          </el-descriptions>
          <h4>失败步骤</h4>
          <el-table :data="defectReport.failed_steps || []" size="small" border>
            <el-table-column prop="step_name" label="步骤" min-width="180" />
            <el-table-column prop="error_message" label="失败原因" min-width="280" show-overflow-tooltip />
            <el-table-column prop="duration_ms" label="耗时" width="100"><template #default="{ row }">{{ row.duration_ms || 0 }}ms</template></el-table-column>
          </el-table>
          <h4>产物</h4>
          <div v-if="!(defectReport.artifacts || []).length" class="text-muted">本次运行没有可用产物。</div>
          <div v-else class="artifact-list">
            <div v-for="artifact in defectReport.artifacts" :key="artifact.id" class="artifact-row">
              <span><el-tag size="small">{{ artifact.kind }}</el-tag> {{ artifact.filename }}</span>
              <span class="artifact-actions">
                <el-button size="small" @click="downloadReportArtifact(artifact)">下载</el-button>
                <el-button v-if="artifact.kind === 'screenshot' && artifact.artifact_manifest_id" size="small" type="primary" @click="openAnnotationDialog(artifact)">查看与标注</el-button>
              </span>
            </div>
          </div>
          <h4>执行时间线</h4>
          <el-timeline class="report-timeline">
            <el-timeline-item v-for="item in defectReport.timeline || []" :key="item.sequence" :type="item.level === 'error' ? 'danger' : item.level === 'warning' ? 'warning' : 'primary'" :timestamp="formatDateTime(item.created_at)">
              <strong>{{ item.type }}</strong><span v-if="Object.keys(item.payload || {}).length"> {{ formatPayload(item.payload) }}</span>
            </el-timeline-item>
          </el-timeline>
        </template>
      </div>
    </el-dialog>
    <el-dialog v-model="annotationVisible" title="截图标注" width="min(1180px, 94vw)" append-to-body @closed="releaseAnnotationImage">
      <div v-loading="annotationLoading" class="annotation-editor">
        <div class="annotation-toolbar">
          <span>在图片上拖动以框选问题区域，标注会作为独立图层保存。</span>
          <el-button size="small" :disabled="!annotationImageUrl" @click="downloadAnnotatedScreenshot">导出标注副本</el-button>
          <el-button size="small" type="primary" :loading="annotationSaving" :disabled="!annotationArtifact" @click="saveAnnotations">保存标注</el-button>
        </div>
        <div v-if="annotationImageUrl" ref="annotationCanvas" class="annotation-canvas" @pointerdown="startAnnotation" @pointerup="finishAnnotation">
          <img :src="annotationImageUrl" alt="失败截图标注" draggable="false" />
          <div v-for="(annotation, index) in annotations" :key="annotation.id || index" class="annotation-box" :style="annotationStyle(annotation)">
            <span>{{ index + 1 }}</span>
          </div>
        </div>
        <el-empty v-else description="截图不可用" />
        <div v-if="annotations.length" class="annotation-notes">
          <div v-for="(annotation, index) in annotations" :key="annotation.id || index" class="annotation-note-row">
            <el-tag size="small">标注 {{ index + 1 }}</el-tag>
            <el-input v-model="annotation.note" maxlength="500" show-word-limit placeholder="填写问题说明" />
            <el-button text type="danger" @click="annotations.splice(index, 1)">删除</el-button>
          </div>
        </div>
      </div>
    </el-dialog>
  </el-drawer>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch, nextTick } from 'vue'
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
const failureAnalysis = ref(null)
const analysisLoading = ref(false)
const analysisFeedbackAccepted = ref(true)
const analysisCorrectedCategory = ref('')
const analysisFeedbackSaving = ref(false)
const defectReport = ref(null)
const reportVisible = ref(false)
const reportLoading = ref(false)
const annotationVisible = ref(false)
const annotationLoading = ref(false)
const annotationSaving = ref(false)
const annotationArtifact = ref(null)
const annotationImageUrl = ref('')
const annotations = ref([])
const annotationStart = ref(null)
let deferredTerminalEvent = null
let heartbeatTimer = null
let backendEventOutbox = []
let backendFlushPromise = null
let recoveryTimer = null
let recoveringPersistedEvents = false
let onlineRecoveryHandler = null

// The renderer can be restarted while Chromium keeps executing. Persist only
// the safe event envelope required to preserve the server sequence; request
// URLs, error text and other diagnostic values remain memory-only.
const OUTBOX_STORAGE_PREFIX = 'testmaster.ui-run-event-outbox:'
const TERMINAL_RUN_STATUSES = new Set(['passed', 'failed', 'cancelled', 'timed_out', 'infra_error'])

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
  failureAnalysis.value = null
  analysisFeedbackAccepted.value = true
  analysisCorrectedCategory.value = ''
  defectReport.value = null
  running.value = true
  visible.value = true
  runRecord.value = null
  eventSequence.value = 0
  backendEventOutbox = []
  backendFlushPromise = null
  backendSyncWarningShown.value = false
  deferredTerminalEvent = null
  runCreateKey.value = window.crypto?.randomUUID?.() || ('run-' + Date.now() + '-' + Math.random().toString(16).slice(2))
  try {
    runRecord.value = await uiAutomationApi.createRun({
      case_id: runContext.caseId,
      case_version_id: runContext.caseVersionId,
      client_run_key: runCreateKey.value,
      trigger_type: 'manual',
      environment_id: environmentId,
    })
    heartbeatTimer = window.setInterval(() => {
      flushBackendEvents().catch(maybeWarnBackendSync)
      uiAutomationApi.heartbeatRun(runRecord.value.id).catch(maybeWarnBackendSync)
    }, 10_000)
  } catch (error) {
    maybeWarnBackendSync(error)
  }

  try {
    const { correlationId, promise } = window.testmaster.execution.runCase(caseSnapshot, {
      headless: false,
      screenshotsOnFailure: true,
      traceOnFailure: true,
      videoOnFailure: true,
      debugMode,
      authStateId,
      runtimeConfigRequest: environmentId == null ? null : { serverUrl: getServerUrl(), token: localStorage.getItem('token') || '', environmentId },
      onEvent: async (event) => {
        events.value.push(event)
        if (event.type === 'run:paused') { paused.value = true; pausedStep.value = event }
        if (event.type === 'run:resumed') { paused.value = false }
        onEvent?.(event)
        // Playwright emits run:finish before its promise resolves. Artifacts
        // become stable only after that promise, so keep the terminal event
        // local until screenshots/trace/video have been uploaded and linked.
        if (event.type === 'run:finish') deferredTerminalEvent = event
        else await syncEventToBackend(event)
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
    await syncTerminalResult(result.value)
    await refreshRunDetails()
  } catch (error) {
    const failureEvent = {
      type: 'log',
      level: 'error',
      message: `运行失败: ${error.message}`,
    }
    events.value.push(failureEvent)
    await syncEventToBackend(failureEvent)
    await syncTerminalResult({ status: 'infra_error', passedSteps: 0, failedSteps: 0, error: error?.message || 'Desktop execution failed' })
    maybeWarnBackendSync(error)
  } finally {
    if (heartbeatTimer) {
      window.clearInterval(heartbeatTimer)
      heartbeatTimer = null
    }
    running.value = false
    paused.value = false
    pausedStep.value = null
    currentCorrelationId.value = ''
    emit('run-finished')
  }
}

async function syncEventToBackend(event) {
  if (!runRecord.value?.id) {
    return false
  }

  // Complete any recoverable previous delivery before allocating a new run.
  // This prevents a new run from obscuring an interrupted run in the drawer.
  await recoverPersistedBackendEvents()

  eventSequence.value += 1
  backendEventOutbox.push({
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
  })
  persistBackendEventOutbox()

  try {
    await flushBackendEvents()
    return true
  } catch (error) {
    maybeWarnBackendSync(error)
    return false
  }
}

const retryDelay = (ms) => new Promise(resolve => window.setTimeout(resolve, ms))

async function flushBackendEvents() {
  if (!runRecord.value?.id || !backendEventOutbox.length) return
  if (backendFlushPromise) return backendFlushPromise
  let completed = false
  backendFlushPromise = (async () => {
    while (backendEventOutbox.length) {
      const event = backendEventOutbox[0]
      let delivered = false
      let lastError
      for (let attempt = 0; attempt < 3; attempt += 1) {
        try {
          await uiAutomationApi.appendRunEvents(runRecord.value.id, [event])
          delivered = true
          break
        } catch (error) {
          lastError = error
          if (attempt < 2) await retryDelay(300 * (attempt + 1))
        }
      }
      if (!delivered) throw lastError || new Error('运行事件同步失败')
      backendEventOutbox.shift()
      persistBackendEventOutbox()
    }
    completed = true
  })().finally(() => {
    backendFlushPromise = null
    // An event may have been queued between the final empty check and this
    // cleanup. Schedule another pass rather than leaving it unsent.
    if (completed && backendEventOutbox.length) void flushBackendEvents().catch(maybeWarnBackendSync)
  })
  return backendFlushPromise
}

function outboxStorageKey(runId) {
  return `${OUTBOX_STORAGE_PREFIX}${runId}`
}

function safePersistentEvent(event) {
  return {
    sequence: event.sequence,
    type: event.type,
    stepId: event.stepId,
    stepName: event.stepName,
    stepType: event.stepType,
    durationMs: event.durationMs,
    totalSteps: event.totalSteps,
    passedSteps: event.passedSteps,
    failedSteps: event.failedSteps,
    status: event.status,
    httpStatus: event.httpStatus,
    method: event.method,
    level: event.level,
  }
}

function persistBackendEventOutbox() {
  const runId = runRecord.value?.id
  if (!Number.isInteger(runId)) return
  const key = outboxStorageKey(runId)
  try {
    if (!backendEventOutbox.length) {
      window.localStorage.removeItem(key)
      return
    }
    window.localStorage.setItem(key, JSON.stringify({
      version: 1,
      runId,
      events: backendEventOutbox.map(safePersistentEvent),
    }))
  } catch {
    // Storage can be disabled by enterprise policy. Live delivery still has
    // bounded retries and the server watchdog prevents a false running state.
  }
}

function readPersistedOutbox(key) {
  try {
    const parsed = JSON.parse(window.localStorage.getItem(key) || '')
    if (!Number.isInteger(parsed?.runId) || !Array.isArray(parsed.events)) return null
    const events = parsed.events.filter(event => (
      Number.isInteger(event?.sequence) && event.sequence > 0 && typeof event.type === 'string'
    )).sort((left, right) => left.sequence - right.sequence)
    if (!events.length) {
      window.localStorage.removeItem(key)
      return null
    }
    return { runId: parsed.runId, events }
  } catch {
    try { window.localStorage.removeItem(key) } catch {}
    return null
  }
}

async function recoverPersistedBackendEvents() {
  if (recoveringPersistedEvents || running.value || backendFlushPromise) return
  recoveringPersistedEvents = true
  try {
    const keys = []
    for (let index = 0; index < window.localStorage.length; index += 1) {
      const key = window.localStorage.key(index)
      if (key?.startsWith(OUTBOX_STORAGE_PREFIX)) keys.push(key)
    }
    for (const key of keys) {
      const persisted = readPersistedOutbox(key)
      if (!persisted) continue
      try {
        const existingRun = await uiAutomationApi.getRun(persisted.runId)
        if (TERMINAL_RUN_STATUSES.has(existingRun.status)) continue
        runRecord.value = existingRun
        eventSequence.value = Math.max(...persisted.events.map(event => event.sequence))
        backendEventOutbox = persisted.events
        await uiAutomationApi.heartbeatRun(existingRun.id)
        await flushBackendEvents()
      } catch {
        // Keep the redacted envelope for the next online/restart attempt.
      } finally {
        if (!backendEventOutbox.length) runRecord.value = null
      }
    }
  } finally {
    recoveringPersistedEvents = false
  }
}

onMounted(() => {
  onlineRecoveryHandler = () => { void recoverPersistedBackendEvents() }
  window.addEventListener('online', onlineRecoveryHandler)
  recoveryTimer = window.setInterval(onlineRecoveryHandler, 10_000)
  onlineRecoveryHandler()
})

onBeforeUnmount(() => {
  if (onlineRecoveryHandler) window.removeEventListener('online', onlineRecoveryHandler)
  onlineRecoveryHandler = null
  if (recoveryTimer) window.clearInterval(recoveryTimer)
  recoveryTimer = null
  releaseAnnotationImage()
})

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
        await uiAutomationApi.uploadSharedArtifact(runRecord.value, artifactFile, 'screenshot', 'image/png')
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
      await uiAutomationApi.uploadSharedArtifact(runRecord.value, artifactFile, 'trace', 'application/zip')
    } catch (error) {
      maybeWarnBackendSync(error)
    }
  }
  if (runResult.videoPath) {
    try {
      const artifactFile = await window.testmaster.artifacts.read(runResult.videoPath)
      await uiAutomationApi.uploadSharedArtifact(runRecord.value, artifactFile, 'video', 'video/webm')
    } catch (error) {
      maybeWarnBackendSync(error)
    }
  }
}

async function syncTerminalResult(runResult) {
  if (!runRecord.value?.id) return
  const terminal = deferredTerminalEvent || {
    type: 'run:finish',
    status: runResult?.status || 'infra_error',
    passedSteps: runResult?.passedSteps || 0,
    failedSteps: runResult?.failedSteps || 0,
    error: runResult?.error,
  }
  deferredTerminalEvent = null
  await syncEventToBackend(terminal)
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

const nonPassingRun = computed(() => ['failed', 'infra_error', 'timed_out', 'cancelled'].includes(runRecord.value?.status || result.value?.status))

async function analyzeFailure () {
  if (!runRecord.value?.id) return
  analysisLoading.value = true
  try {
    failureAnalysis.value = await uiAutomationApi.analyzeFailure(runRecord.value.id)
  } catch (error) {
    ElMessage.error(error?.message || '失败归因生成失败')
  } finally {
    analysisLoading.value = false
  }
}

async function submitAnalysisFeedback () {
  const analysisId = failureAnalysis.value?.analysis_id || failureAnalysis.value?.id
  if (!analysisId) {
    ElMessage.error('归因记录缺少标识，无法提交复核')
    return
  }
  if (analysisFeedbackAccepted.value === false && !analysisCorrectedCategory.value) {
    ElMessage.warning('请选择纠正后的失败类别')
    return
  }
  analysisFeedbackSaving.value = true
  try {
    await uiAutomationApi.submitAiAnalysisFeedback(analysisId, {
      accepted: analysisFeedbackAccepted.value,
      corrected_category: analysisFeedbackAccepted.value ? null : analysisCorrectedCategory.value,
    })
    ElMessage.success('人工复核已记录')
  } catch (error) {
    ElMessage.error(error?.message || '提交人工复核失败')
  } finally {
    analysisFeedbackSaving.value = false
  }
}

async function openDefectReport () {
  if (!runRecord.value?.id) return
  reportVisible.value = true
  reportLoading.value = true
  try {
    defectReport.value = await uiAutomationApi.getRunDefectReport(runRecord.value.id)
  } catch (error) {
    ElMessage.error(error?.message || '缺陷报告生成失败')
  } finally {
    reportLoading.value = false
  }
}

async function reportArtifactBlob (artifact) {
  if (!runRecord.value?.id || !artifact?.id) throw new Error('运行产物信息不完整')
  const blob = await uiAutomationApi.getRunArtifactContent(runRecord.value.id, artifact.id)
  if (!(blob instanceof Blob)) throw new Error('运行产物读取失败')
  return blob
}

async function downloadReportArtifact (artifact) {
  try {
    const blob = await reportArtifactBlob(artifact)
    const url = URL.createObjectURL(blob)
    const anchor = document.createElement('a')
    anchor.href = url
    anchor.download = artifact.filename || 'testmaster-artifact'
    anchor.click()
    window.setTimeout(() => URL.revokeObjectURL(url), 0)
  } catch (error) {
    ElMessage.error(error?.message || '产物下载失败')
  }
}

async function openAnnotationDialog (artifact) {
  annotationArtifact.value = artifact
  annotationVisible.value = true
  annotationLoading.value = true
  annotations.value = []
  releaseAnnotationImage()
  annotationArtifact.value = artifact
  try {
    const [blob, layer] = await Promise.all([
      reportArtifactBlob(artifact),
      uiAutomationApi.getArtifactAnnotations(artifact.artifact_manifest_id),
    ])
    annotationImageUrl.value = URL.createObjectURL(blob)
    annotations.value = Array.isArray(layer.annotations)
      ? layer.annotations.filter(item => item?.type === 'rectangle').map(item => ({ ...item }))
      : []
  } catch (error) {
    ElMessage.error(error?.message || '截图标注加载失败')
  } finally {
    annotationLoading.value = false
  }
}

function releaseAnnotationImage () {
  if (annotationImageUrl.value) URL.revokeObjectURL(annotationImageUrl.value)
  annotationImageUrl.value = ''
  annotationArtifact.value = null
  annotationStart.value = null
}

function startAnnotation (event) {
  if (event.button !== 0 || !annotationImageUrl.value) return
  const box = event.currentTarget.getBoundingClientRect()
  annotationStart.value = {
    x: Math.max(0, Math.min(100, ((event.clientX - box.left) / box.width) * 100)),
    y: Math.max(0, Math.min(100, ((event.clientY - box.top) / box.height) * 100)),
  }
  event.currentTarget.setPointerCapture?.(event.pointerId)
}

function finishAnnotation (event) {
  if (!annotationStart.value) return
  const box = event.currentTarget.getBoundingClientRect()
  const endX = Math.max(0, Math.min(100, ((event.clientX - box.left) / box.width) * 100))
  const endY = Math.max(0, Math.min(100, ((event.clientY - box.top) / box.height) * 100))
  const x = Math.min(annotationStart.value.x, endX)
  const y = Math.min(annotationStart.value.y, endY)
  const width = Math.abs(endX - annotationStart.value.x)
  const height = Math.abs(endY - annotationStart.value.y)
  annotationStart.value = null
  if (width < 0.5 || height < 0.5) return
  annotations.value.push({
    id: window.crypto?.randomUUID?.() || `annotation-${Date.now()}-${annotations.value.length}`,
    type: 'rectangle', x, y, width, height, note: '',
  })
}

function annotationStyle (annotation) {
  return {
    left: `${Number(annotation.x) || 0}%`, top: `${Number(annotation.y) || 0}%`,
    width: `${Number(annotation.width) || 0}%`, height: `${Number(annotation.height) || 0}%`,
  }
}

async function saveAnnotations () {
  const manifestId = annotationArtifact.value?.artifact_manifest_id
  if (!manifestId) return
  annotationSaving.value = true
  try {
    await uiAutomationApi.saveArtifactAnnotations(manifestId, annotations.value)
    ElMessage.success('截图标注已保存')
  } catch (error) {
    ElMessage.error(error?.message || '截图标注保存失败')
  } finally {
    annotationSaving.value = false
  }
}

async function downloadAnnotatedScreenshot () {
  if (!annotationImageUrl.value || !annotationArtifact.value) return
  try {
    const image = new Image()
    image.src = annotationImageUrl.value
    await new Promise((resolve, reject) => { image.onload = resolve; image.onerror = reject })
    const canvas = document.createElement('canvas')
    canvas.width = image.naturalWidth
    canvas.height = image.naturalHeight
    const context = canvas.getContext('2d')
    if (!context) throw new Error('浏览器不支持图片标注导出')
    context.drawImage(image, 0, 0)
    context.strokeStyle = '#dc2626'
    context.fillStyle = '#dc2626'
    context.lineWidth = Math.max(2, Math.round(image.naturalWidth / 500))
    context.font = `${Math.max(14, Math.round(image.naturalWidth / 48))}px sans-serif`
    annotations.value.forEach((annotation, index) => {
      const x = (Number(annotation.x) / 100) * image.naturalWidth
      const y = (Number(annotation.y) / 100) * image.naturalHeight
      const width = (Number(annotation.width) / 100) * image.naturalWidth
      const height = (Number(annotation.height) / 100) * image.naturalHeight
      context.strokeRect(x, y, width, height)
      context.fillText(`${index + 1}${annotation.note ? ` ${annotation.note}` : ''}`, x + 4, Math.max(16, y - 6))
    })
    const blob = await new Promise(resolve => canvas.toBlob(resolve, 'image/png'))
    if (!blob) throw new Error('标注图片生成失败')
    const url = URL.createObjectURL(blob)
    const anchor = document.createElement('a')
    anchor.href = url
    anchor.download = `${String(annotationArtifact.value.filename || 'screenshot').replace(/\.[^.]+$/, '')}-annotated.png`
    anchor.click()
    window.setTimeout(() => URL.revokeObjectURL(url), 0)
  } catch (error) {
    ElMessage.error(error?.message || '标注图片导出失败')
  }
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

function formatDateTime (value) {
  if (!value) return '未记录'
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? String(value) : date.toLocaleString('zh-CN')
}

function formatPayload (payload) {
  try { return JSON.stringify(payload) } catch { return '附加信息不可序列化' }
}

function statusLabel(status) {
  const map = { queued: '排队中', waiting_for_agent: '等待桌面 Agent', assigned: '已分配', starting: '启动中', running: '运行中', cancel_requested: '取消中', passed: '通过', failed: '失败', cancelled: '已取消', timed_out: '执行超时', infra_error: '基础设施异常', error: '错误', orphaned: '异常中断' }
  return map[status] || status
}

function statusTagType(status) {
  const map = { queued: 'info', waiting_for_agent: 'warning', assigned: 'info', starting: 'warning', running: 'warning', cancel_requested: 'warning', passed: 'success', failed: 'danger', cancelled: 'info', timed_out: 'danger', infra_error: 'danger', error: 'danger', orphaned: 'warning' }
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

function categoryLabel (category) {
  return ({ environment: '环境问题', data: '数据问题', product_defect: '产品缺陷', script: '脚本问题', unknown: '待确认' })[category] || '待确认'
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
.analysis-card { margin-bottom: 16px; }
.analysis-header { display: flex; align-items: center; justify-content: space-between; }
.analysis-content { display: flex; flex-direction: column; gap: 12px; font-size: 13px; line-height: 1.55; }
.analysis-content ul, .analysis-content ol { margin: 6px 0 0; padding-left: 20px; }
.analysis-feedback { display: flex; align-items: center; flex-wrap: wrap; gap: 8px; padding-top: 4px; }
.analysis-feedback .el-select { width: 180px; }
.confidence { margin-left: 8px; color: var(--el-text-color-secondary); font-size: 12px; }
.report-card { margin-bottom: 16px; }
.report-hint { color: var(--el-text-color-secondary); font-size: 13px; }
.defect-report { display: flex; flex-direction: column; gap: 14px; min-height: 160px; }
.defect-report h4 { margin: 6px 0 -4px; font-size: 14px; }
.report-meta { display: flex; align-items: center; flex-wrap: wrap; gap: 10px 16px; color: var(--el-text-color-secondary); font-size: 13px; }
.artifact-list { display: flex; flex-direction: column; gap: 8px; }
.artifact-row { display: flex; justify-content: space-between; align-items: center; gap: 12px; padding: 8px 10px; border: 1px solid var(--el-border-color-lighter); }
.artifact-actions { display: flex; gap: 8px; flex-wrap: wrap; }
.report-timeline { max-height: 280px; overflow: auto; margin: 0; padding-top: 6px; font-size: 12px; }
.annotation-editor { display: flex; flex-direction: column; gap: 12px; min-height: 180px; }
.annotation-toolbar { display: flex; align-items: center; justify-content: space-between; gap: 8px; flex-wrap: wrap; color: var(--el-text-color-secondary); font-size: 13px; }
.annotation-canvas { position: relative; align-self: center; max-width: 100%; line-height: 0; cursor: crosshair; touch-action: none; user-select: none; }
.annotation-canvas img { display: block; max-width: 100%; max-height: 62vh; object-fit: contain; }
.annotation-box { position: absolute; border: 2px solid #dc2626; box-sizing: border-box; pointer-events: none; }
.annotation-box span { position: absolute; top: -12px; left: -2px; min-width: 18px; height: 18px; padding: 0 4px; border-radius: 9px; background: #dc2626; color: #fff; font-size: 11px; line-height: 18px; text-align: center; }
.annotation-notes { display: flex; flex-direction: column; gap: 8px; }
.annotation-note-row { display: grid; grid-template-columns: auto minmax(0, 1fr) auto; align-items: center; gap: 8px; }
@media (max-width: 640px) { .artifact-row { align-items: flex-start; flex-direction: column; } .annotation-note-row { grid-template-columns: 1fr auto; } .annotation-note-row .el-input { grid-column: 1 / -1; grid-row: 2; } }
</style>














