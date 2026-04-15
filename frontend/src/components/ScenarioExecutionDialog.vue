<template>
  <el-dialog
    v-model="dialogVisible"
    title="场景执行结果"
    width="80%"
    append-to-body
    destroy-on-close
    @close="handleClose"
  >
    <div v-if="isRunning && !runResult" style="padding: 40px 20px; text-align: center;">
      <el-progress
        :percentage="progress?.percent || 0"
        :text-inside="true"
        :stroke-width="24"
        status="success"
        style="margin: 0 auto 20px; max-width: 80%;"
      ></el-progress>
      <p style="margin-top: 15px; color: var(--tm-text-secondary); font-size: 14px;">
        正在执行: {{ progress?.current_api || '初始化中...' }}
      </p>
      <p style="margin-top: 5px; color: var(--tm-text-secondary); font-size: 13px;">
        {{ progress?.current || 0 }} / {{ progress?.total || 0 }} 步骤
      </p>
      <el-button
        type="danger"
        style="margin-top: 20px;"
        :loading="isCanceling"
        @click="handleCancel"
      >
        🛑 停止执行
      </el-button>
    </div>

    <div class="result-content" v-else-if="runResult">
      <div class="result-header-stats">
        <el-tag :type="(runResult.failed_count || runResult.failed_steps || 0) > 0 ? 'danger' : 'success'" size="large">
          {{ (runResult.failed_count || runResult.failed_steps || 0) > 0 ? '❌ 有步骤失败' : '✅ 全部通过' }}
        </el-tag>
        <span style="margin-left: 15px; color: var(--tm-text-regular);">
          总步骤: {{ runResult.total_steps || 0 }} |
          成功: <span style="color: #67c23a">{{ runResult.success_count || runResult.success_steps || 0 }}</span> |
          失败: <span style="color: #f56c6c">{{ runResult.failed_count || runResult.failed_steps || 0 }}</span> |
          跳过: <span style="color: var(--tm-text-secondary)">{{ runResult.skipped_count || runResult.skipped_steps || 0 }}</span> |
          总耗时: {{ formatTotalTime(runResult.total_time) }}
        </span>
      </div>

      <el-divider />

      <div class="step-results">
        <div
          v-for="(step, index) in runResult.step_results"
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

          <div v-else class="step-header" @click="toggleStep(index)">
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
              {{ step.response_time || step.duration || 0 }}ms
            </span>
            <el-icon class="toggle-icon" :class="{ 'is-expanded': expandedSteps.includes(index) }">
              <ArrowRight />
            </el-icon>
          </div>

          <div class="step-detail" v-if="expandedSteps.includes(index) && step.status !== 'skipped'">
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
                <span class="info-label">状态码:</span>
                <el-tag :type="getStatusCodeType(step.status_code)" size="small">
                  {{ step.status_code || '无' }}
                </el-tag>
              </div>
              <div class="response-body">
                <h5>响应体</h5>
                <pre class="body-display">{{ formatResponseBody(step.response) }}</pre>
              </div>
            </div>

            <div class="detail-section" v-if="step.assertions">
              <h5>断言结果</h5>
              <div class="assertion-summary">
                <el-tag type="success" size="small">通过: {{ step.assertions.passed || 0 }}</el-tag>
                <el-tag type="danger" size="small">失败: {{ step.assertions.failed?.length || 0 }}</el-tag>
              </div>
              <div v-if="step.assertions.failed?.length" class="assertion-errors">
                <el-alert
                  v-for="(fail, idx) in step.assertions.failed"
                  :key="idx"
                  type="error"
                  :title="fail.reason || formatExpectedValue(fail.assertion)"
                  :closable="false"
                  show-icon
                />
              </div>
            </div>

            <div class="detail-section" v-if="step.extracted_vars && Object.keys(step.extracted_vars).length > 0">
              <h5>提取的变量</h5>
              <el-tag
                v-for="(value, key) in step.extracted_vars"
                :key="key"
                class="var-tag"
                type="info"
              >
                {{ key }}: {{ typeof value === 'object' ? JSON.stringify(value) : value }}
              </el-tag>
            </div>
          </div>
        </div>
      </div>

      <el-divider />
      <div class="context-vars">
        <h4>执行后的全局变量</h4>
        <el-empty v-if="Object.keys(runResult.context_vars || {}).length === 0" description="无提取的变量" />
        <el-tag
          v-for="(value, key) in runResult.context_vars"
          :key="key"
          class="var-tag"
          type="info"
        >
          {{ key }}: {{ typeof value === 'object' ? JSON.stringify(value) : value }}
        </el-tag>
      </div>
    </div>

    <template #footer>
      <span class="dialog-footer">
        <el-button
          v-show="!isRunning && runResult"
          type="primary"
          @click="openAllureReport"
        >
          📊 查看 Allure 详细报告
        </el-button>
        <el-button @click="dialogVisible = false">关闭</el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { ArrowRight } from '@element-plus/icons-vue'
import axios from 'axios'

const props = defineProps({
  modelValue: { type: Boolean, default: false }
})

const emit = defineEmits(['update:modelValue', 'completed'])

const dialogVisible = computed({
  get: () => props.modelValue,
  set: val => emit('update:modelValue', val)
})

const autoTestRequest = axios.create({
  baseURL: '',
  timeout: 30000
})

autoTestRequest.interceptors.request.use(config => {
  const token = localStorage.getItem('admin_token') || localStorage.getItem('token')
  if (token && token !== 'undefined' && token !== 'null' && token !== '[object Object]') {
    config.headers['Authorization'] = `Bearer ${token}`
  }
  return config
}, error => Promise.reject(error))

autoTestRequest.interceptors.response.use(
  response => response.data,
  error => Promise.reject(error)
)

const isRunning = ref(false)
const isCanceling = ref(false)
const runResult = ref(null)
const progress = ref(null)
const expandedSteps = ref([])

let pollingTimer = null
let pollingAbortController = null
let currentTaskId = null

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

const formatTotalTime = (ms) => {
  if (!ms && ms !== 0) return '0ms'
  if (ms < 1000) return ms + 'ms'
  return (ms / 1000).toFixed(2) + 's'
}

const formatResponseBody = (response) => {
  if (!response) return '无响应'
  if (typeof response === 'object') return JSON.stringify(response, null, 2)
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

const toggleStep = (index) => {
  const idx = expandedSteps.value.indexOf(index)
  if (idx >= 0) expandedSteps.value.splice(idx, 1)
  else expandedSteps.value.push(index)
}

const resolveReportUrl = (reportUrl) => {
  if (!reportUrl) return ''
  if (/^https?:\/\//i.test(reportUrl)) return reportUrl
  const normalizedPath = reportUrl.startsWith('/') ? reportUrl : `/${reportUrl}`
  const configuredBase = import.meta.env.VITE_AUTO_TEST_API_BASE_URL?.trim()
  if (configuredBase) return `${configuredBase.replace(/\/+$/, '')}${normalizedPath}`
  return normalizedPath
}

const openAllureReport = () => {
  const resultData = runResult.value || {}
  let url = resultData.report_url
  if (!url && resultData.execution_record_id) {
    url = `/reports/scenario_${resultData.scenario_id || 'unknown'}/index.html`
  }
  if (!url && resultData.report_id) {
    url = `/reports/${resultData.report_id}/index.html`
  }
  if (url) {
    window.open(resolveReportUrl(url), '_blank')
  } else {
    ElMessage.warning('Allure 报告未生成（可能未安装 allure 命令行工具）。请检查后端日志。')
  }
}

const stopPolling = () => {
  if (pollingTimer) { clearInterval(pollingTimer); pollingTimer = null }
  if (pollingAbortController) { pollingAbortController.abort(); pollingAbortController = null }
}

const pollTaskStatus = (taskId) => {
  stopPolling()
  pollingAbortController = new AbortController()
  const signal = pollingAbortController.signal
  pollingTimer = setInterval(async () => {
    try {
      const res = await autoTestRequest.get(`/api/auto-test/tasks/${taskId}`, { signal })
      const state = res.status

      if (state === 'PENDING') {
        progress.value = {
          percent: 0,
          current: 0,
          total: progress.value?.total || 0,
          current_api: '正在下发任务...',
          current_step: 0,
          total_steps: progress.value?.total || 0,
          step_name: '正在下发任务...'
        }
      } else if (state === 'STARTED') {
        progress.value = {
          percent: 0,
          current: 0,
          total: progress.value?.total || 0,
          current_api: '任务已启动，等待执行...',
          current_step: 0,
          total_steps: progress.value?.total || 0,
          step_name: '任务已启动'
        }
      } else if (state === 'PROGRESS') {
        const p = res.progress || {}
        const currentStep = p.current_step || p.current || 0
        const totalSteps = p.total_steps || p.total || progress.value?.total || 0
        const stepName = p.step_name || p.current_api || '执行中...'
        const percent = totalSteps > 0 ? Math.round((currentStep / totalSteps) * 100) : 0
        progress.value = {
          percent,
          current: currentStep,
          total: totalSteps,
          current_api: stepName,
          current_step: currentStep,
          total_steps: totalSteps,
          step_name: stepName
        }
      } else if (state === 'completed' || state === 'SUCCESS') {
        stopPolling()
        isRunning.value = false
        const resultData = res.result || res
        const totalSteps = resultData.total_steps || progress.value?.total || 0
        progress.value = {
          percent: 100,
          current: totalSteps,
          total: totalSteps,
          current_api: '执行完成',
          current_step: totalSteps,
          total_steps: totalSteps,
          step_name: '执行完成'
        }
        runResult.value = resultData
        expandedSteps.value = []
        if (resultData && resultData.step_results) {
          const failedIndex = resultData.step_results.findIndex(s => !s.success)
          if (failedIndex >= 0) expandedSteps.value = [failedIndex]
        }
        ElMessage.success('执行完成')
        emit('completed', resultData)
      } else if (state === 'failed' || state === 'FAILURE' || state === 'REVOKED') {
        stopPolling()
        isRunning.value = false
        if (state === 'REVOKED') {
          ElMessage.warning('⛔ 任务已被终止')
          dialogVisible.value = false
        } else {
          ElMessage.error('执行失败: ' + (res.error || '未知错误'))
        }
      }
    } catch (error) {
      if (axios.isCancel(error)) return
      stopPolling()
      isRunning.value = false
      ElMessage.error('查询任务状态失败: ' + (error.response?.data?.detail || error.message))
    }
  }, 2000)
}

const handleCancel = async () => {
  if (!currentTaskId) { ElMessage.warning('没有正在执行的任务'); return }
  try {
    isCanceling.value = true
    await autoTestRequest.post(`/api/auto-test/tasks/${currentTaskId}/cancel`)
    stopPolling()
    isRunning.value = false
    isCanceling.value = false
    progress.value = null
    ElMessage.warning('⛔ 任务已被用户强制终止')
    dialogVisible.value = false
    currentTaskId = null
  } catch (error) {
    isCanceling.value = false
    ElMessage.error('终止任务失败: ' + (error.response?.data?.detail || error.message))
  }
}

const handleClose = () => {
  stopPolling()
  isRunning.value = false
  runResult.value = null
  progress.value = null
  expandedSteps.value = []
  currentTaskId = null
}

const startExecution = async (scenarioId, envId, totalSteps) => {
  isRunning.value = true
  runResult.value = null
  expandedSteps.value = []
  progress.value = {
    percent: 0,
    current: 0,
    total: totalSteps || 0,
    current_api: '正在下发任务...',
    current_step: 0,
    total_steps: totalSteps || 0,
    step_name: '正在下发任务...'
  }
  dialogVisible.value = true

  try {
    const res = await autoTestRequest.post(
      `/api/auto-test/scenarios/${scenarioId}/run`,
      { env_id: envId }
    )
    const taskId = res?.task_id || res?.data?.task_id
    if (!taskId) {
      isRunning.value = false
      ElMessage.error('任务提交失败，未获取到 task_id')
      return
    }
    currentTaskId = taskId
    pollTaskStatus(taskId)
  } catch (error) {
    isRunning.value = false
    ElMessage.error('提交任务失败: ' + (error.response?.data?.detail || error.message))
  }
}

onUnmounted(() => {
  stopPolling()
})

defineExpose({ startExecution })
</script>

<style scoped>
.result-content { max-height: 70vh; overflow: auto; }
.result-header-stats { display: flex; align-items: center; flex-wrap: wrap; gap: 8px; }
.step-results { display: flex; flex-direction: column; gap: 12px; }
.step-result-card { border: 1px solid var(--tm-border-light); border-radius: var(--tm-radius-base); padding: 16px; background: var(--tm-bg-card); transition: all 0.3s; }
.step-result-card.is-failed { border-color: rgba(245,108,108,0.4); background: rgba(245,108,108,0.02); }
.step-result-card.is-skipped { opacity: 0.6; }
.step-header { display: flex; align-items: center; gap: 12px; cursor: pointer; padding: 4px 8px; border-radius: var(--tm-radius-small); transition: background-color 0.2s; }
.step-header:hover { background: var(--tm-bg-hover); }
.step-header-skipped { opacity: 0.6; cursor: default; }
.step-skipped-hint { color: var(--tm-text-secondary); font-size: 12px; font-style: italic; margin-left: 8px; }
.toggle-icon { margin-left: auto; transition: transform 0.3s; }
.toggle-icon.is-expanded { transform: rotate(90deg); }
.step-order { width: 24px; height: 24px; border-radius: 50%; background: var(--tm-color-primary); color: #fff; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 600; }
.step-name { font-weight: 500; flex: 1; color: var(--tm-text-primary); }
.step-detail { margin-top: 16px; padding-left: 36px; border-top: 1px solid var(--tm-border-light); padding-top: 16px; }
.detail-url { font-family: 'Monaco','Menlo','Ubuntu Mono',monospace; font-size: 12px; color: var(--tm-text-regular); word-break: break-all; background: var(--tm-bg-page); padding: 8px 12px; border-radius: var(--tm-radius-small); margin-bottom: 12px; }
.detail-section { margin-top: 16px; }
.detail-section h5 { margin: 0 0 12px; color: var(--tm-color-primary); font-size: 13px; font-weight: 600; }
.request-info { display: flex; flex-direction: column; gap: 8px; }
.info-row { margin-bottom: 8px; }
.info-label { display: inline-block; min-width: 60px; color: var(--tm-text-secondary); font-size: 13px; margin-right: 8px; }
.info-value { color: var(--tm-text-primary); font-size: 13px; word-break: break-all; }
.code-block { background: #1e1e1e; color: #d4d4d4; padding: 12px; border-radius: var(--tm-radius-small); max-height: 300px; overflow: auto; font-family: 'Monaco','Menlo','Ubuntu Mono',monospace; font-size: 12px; line-height: 1.6; white-space: pre-wrap; word-break: break-all; margin: 8px 0 0; }
.step-error { margin-top: 12px; }
.response-info { display: flex; align-items: center; gap: 12px; margin-bottom: 12px; }
.response-body h5 { margin: 12px 0 8px; color: var(--tm-color-primary); font-size: 13px; font-weight: 600; }
.body-display { background: #1e1e1e; color: #d4d4d4; padding: 16px; border-radius: var(--tm-radius-small); max-height: 200px; overflow: auto; font-family: 'Monaco','Menlo','Ubuntu Mono',monospace; font-size: 12px; line-height: 1.6; white-space: pre-wrap; word-break: break-all; margin: 0; box-shadow: inset 0 2px 8px rgba(0,0,0,0.2); }
.assertion-summary { display: flex; gap: 8px; margin-bottom: 12px; }
.assertion-errors { margin-top: 12px; display: flex; flex-direction: column; gap: 8px; }
.context-vars h4 { margin: 0 0 12px; color: var(--tm-text-primary); }
.var-tag { margin: 4px; }
</style>
