<template>
  <div class="ai-generate-page">
    <div class="page-header">
      <div class="header-left">
        <el-button link @click="$router.push('/auto-test')">
          <el-icon><ArrowLeft /></el-icon> 返回工作台
        </el-button>
        <h2>AI 智能生成测试用例</h2>
        <p class="subtitle">上传 Swagger/OpenAPI 文档，AI 自动生成带断言、变量提取、场景链的完整用例</p>
      </div>
      <div class="header-right">
        <el-button @click="showHelp = true">❓ 使用说明</el-button>
      </div>
    </div>

    <!-- 步骤条 -->
    <el-steps :active="currentStep" finish-status="success" class="steps-bar">
      <el-step title="上传文档" />
      <el-step title="配置选项" />
      <el-step title="AI 生成" />
      <el-step title="预览 & 导入" />
    </el-steps>

    <!-- 步骤1: 上传 -->
    <div v-if="currentStep === 0" class="step-content">
      <div class="upload-area">
        <el-upload
          ref="uploadRef"
          :auto-upload="false"
          :limit="1"
          :on-change="handleFileChange"
          :on-remove="() => { swaggerFile = null }"
          accept=".json,.yaml,.yml"
          drag
        >
          <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
          <div class="el-upload__text">拖拽文件到此处，或 <em>点击上传</em></div>
          <template #tip>
            <div class="el-upload__tip">支持 Swagger 2.0 / OpenAPI 3.0 JSON 格式</div>
          </template>
        </el-upload>

        <div class="divider-or"><span>或者</span></div>

        <el-input
          v-model="swaggerUrl"
          placeholder="输入 Swagger 文档 URL（如 http://localhost:8080/v3/api-docs）"
          clearable
          size="large"
        >
          <template #prepend>URL</template>
        </el-input>

        <el-button
          type="primary"
          size="large"
          :disabled="!swaggerFile && !swaggerUrl"
          @click="currentStep = 1"
          style="margin-top: 20px; width: 100%;"
        >
          下一步：配置选项
        </el-button>
      </div>
    </div>

    <!-- 步骤2: 配置 -->
    <div v-if="currentStep === 1" class="step-content">
      <el-card class="config-card">
        <el-form label-width="160px" size="large">
          <el-form-item label="每接口最大用例数">
            <el-slider v-model="options.max_cases_per_api" :min="1" :max="10" :step="1" show-input />
          </el-form-item>
          <el-form-item label="生成边界测试">
            <el-switch v-model="options.include_boundary" />
            <span class="form-tip">空值、超长字符串、类型错误等</span>
          </el-form-item>
          <el-form-item label="生成鉴权测试">
            <el-switch v-model="options.include_auth" />
            <span class="form-tip">无 Token、过期 Token 等</span>
          </el-form-item>
          <el-form-item label="生成场景链">
            <el-switch v-model="options.include_chain" />
            <span class="form-tip">自动识别 CRUD 关系，生成 创建→查询→修改→删除 流程</span>
          </el-form-item>
        </el-form>

        <div class="config-actions">
          <el-button @click="currentStep = 0">上一步</el-button>
          <el-button type="primary" @click="startGenerate" :loading="submitting">
            {{ submitting ? '提交中...' : '开始生成' }}
          </el-button>
          <span v-if="getCostText('ai_generate_cases')" class="ai-cost-hint">{{ getCostText('ai_generate_cases') }}{{ getCost('ai_generate_cases') > 0 ? '/批次' : '' }}</span>
        </div>
      </el-card>
    </div>

    <!-- 步骤3: 生成中 - 轮询进度 -->
    <div v-if="currentStep === 2" class="step-content generating-content">
      <div class="progress-panel">
        <!-- 总进度条 -->
        <div class="progress-bar-section">
          <el-progress
            :percentage="progressPercent"
            :stroke-width="20"
            :text-inside="true"
            :format="() => `${progressPercent}%`"
          />
        </div>

        <!-- 阶段指示器 + 计时器 -->
        <div class="phase-indicator">
          <div class="phase-icon">{{ phaseIcon }}</div>
          <div class="phase-text">
            <span class="phase-label">{{ phaseLabel }}</span>
            <span v-if="taskProgress.phase === 'generating_cases' && taskProgress.total_batches" class="phase-batch">
              批次 {{ taskProgress.current_batch || 0 }}/{{ taskProgress.total_batches }}
            </span>
          </div>
          <div class="elapsed-timer">
            <el-icon><Timer /></el-icon>
            <span>{{ elapsedDisplay }}</span>
          </div>
        </div>

        <!-- 实时统计 -->
        <div class="live-stats">
          <div class="stat-item">
            <span class="stat-label">已分析接口</span>
            <span class="stat-value">{{ taskProgress.processed_apis || 0 }}/{{ taskProgress.total_apis || '-' }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">已生成用例</span>
            <span class="stat-value">{{ generateResult.cases?.length || 0 }} 个</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">已生成场景</span>
            <span class="stat-value">{{ generateResult.scenarios?.length || 0 }} 个</span>
          </div>
        </div>

        <!-- 安全提示 -->
        <el-alert
          type="info"
          :closable="false"
          class="safety-tip"
        >
          <template #title>
            已生成的用例会实时保存，切换页面或中断不会丢失已生成的用例
          </template>
        </el-alert>

        <!-- 实时用例预览 -->
        <div v-if="generateResult.cases?.length" class="live-preview">
          <div class="live-preview-header">
            <span>实时用例预览</span>
            <el-tag size="small" type="info">{{ generateResult.cases.length }} 个</el-tag>
          </div>
          <div class="live-case-list">
            <div v-for="(c, idx) in generateResult.cases" :key="idx" class="live-case-card">
              <el-tag :type="methodTagType(c.method)" size="small">{{ c.method }}</el-tag>
              <span class="live-case-name">{{ c.name }}</span>
            </div>
          </div>
        </div>

        <!-- 操作按钮 -->
        <div class="generation-actions">
          <el-button type="danger" :loading="cancelling" @click="handleCancel">
            <el-icon><Close /></el-icon>
            {{ cancelling ? '中止中...' : '中止生成' }}
          </el-button>
          <span class="cancel-hint">中止后已生成的用例会保留，可在预览页查看并导入</span>
        </div>
      </div>
    </div>

    <!-- 步骤4: 预览 & 导入 -->
    <div v-if="currentStep === 3" class="step-content">
      <div class="result-header">
        <el-alert
          :title="generateResult.message || 'AI 生成完成'"
          type="success"
          show-icon
          :closable="false"
        />
        <div class="result-stats">
          <el-tag type="primary" size="large">用例: {{ generateResult.cases?.length || 0 }}</el-tag>
          <el-tag type="warning" size="large">场景: {{ generateResult.scenarios?.length || 0 }}</el-tag>
          <el-tag v-if="elapsedDisplay" type="info" size="large">耗时: {{ elapsedDisplay }}</el-tag>
        </div>
      </div>

      <!-- 用例列表 -->
      <el-tabs v-model="previewTab" class="preview-tabs">
        <el-tab-pane label="测试用例" name="cases">
          <div v-if="!generateResult.cases?.length" class="empty-tip">
            <el-empty description="未生成测试用例" />
          </div>
          <div v-else class="case-list">
            <el-collapse v-model="expandedCases">
              <el-collapse-item
                v-for="(c, idx) in generateResult.cases"
                :key="idx"
                :title="`${c.method} ${c.name}`"
                :name="idx"
              >
                <template #title>
                  <div class="case-title">
                    <el-tag :type="methodTagType(c.method)" size="small">{{ c.method }}</el-tag>
                    <span>{{ c.name }}</span>
                    <el-tag v-if="c.name?.includes('鉴权')" type="warning" size="small">鉴权</el-tag>
                    <el-tag v-if="c.name?.includes('边界')" type="danger" size="small">边界</el-tag>
                  </div>
                </template>
                <div class="case-detail">
                  <div class="detail-row">
                    <span class="label">URL:</span>
                    <code>{{ c.url }}</code>
                  </div>
                  <div class="detail-row" v-if="c.payload">
                    <span class="label">请求体:</span>
                    <pre>{{ JSON.stringify(c.payload, null, 2) }}</pre>
                  </div>
                  <div class="detail-row" v-if="c.assert_rules?.length">
                    <span class="label">断言 ({{ c.assert_rules.length }}):</span>
                    <div v-for="(rule, ri) in c.assert_rules" :key="ri" class="assert-item">
                      <el-tag size="small" type="info">{{ rule.operator }}</el-tag>
                      <code>{{ rule.field }}</code>
                      <span v-if="rule.expected"> = {{ rule.expected }}</span>
                      <span class="assert-desc">{{ rule.description }}</span>
                    </div>
                  </div>
                  <div class="detail-row" v-if="c.extractors?.length">
                    <span class="label">变量提取 ({{ c.extractors.length }}):</span>
                    <div v-for="(ext, ei) in c.extractors" :key="ei" class="extractor-item">
                      <el-tag size="small" type="success">{{ ext.type }}</el-tag>
                      <code>{{ ext.expression }}</code>
                      → <strong>{{ ext.variable }}</strong>
                    </div>
                  </div>
                  <div class="detail-row" v-if="c.description">
                    <span class="label">描述:</span>
                    <span>{{ c.description }}</span>
                  </div>
                </div>
              </el-collapse-item>
            </el-collapse>
          </div>
        </el-tab-pane>

        <el-tab-pane label="场景链" name="scenarios">
          <div v-if="!generateResult.scenarios?.length" class="empty-tip">
            <el-empty description="未生成场景链" />
          </div>
          <div v-else class="scenario-list">
            <el-card v-for="(s, idx) in generateResult.scenarios" :key="idx" class="scenario-card">
              <template #header>
                <div class="scenario-header">
                  <span class="scenario-name">{{ s.name }}</span>
                  <el-tag size="small">{{ s.steps?.length || 0 }} 步</el-tag>
                </div>
              </template>
              <p class="scenario-desc">{{ s.description }}</p>
              <div class="scenario-steps">
                <div v-for="(step, si) in s.steps" :key="si" class="scenario-step">
                  <span class="step-num">{{ si + 1 }}</span>
                  <span class="step-desc">{{ step.description }}</span>
                  <el-tag size="small" type="info">
                    {{ getCaseName(step.api_index) }}
                  </el-tag>
                </div>
              </div>
            </el-card>
          </div>
        </el-tab-pane>
      </el-tabs>

      <!-- 导入操作 -->
      <div class="import-actions">
        <el-button @click="currentStep = 1" size="large">重新生成</el-button>
        <el-input v-model="groupName" placeholder="导入分组名" style="width: 200px; margin: 0 12px;" size="large" />
        <el-button type="primary" size="large" :loading="importing" @click="confirmImport">
          {{ importing ? '导入中...' : '确认导入到用例库' }}
        </el-button>
      </div>
    </div>
    <HelpDrawer v-model="showHelp" :title="helpData.title" :intro="helpData.intro" :sections="helpData.sections" />
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, UploadFilled, Timer, Close } from '@element-plus/icons-vue'
import autoTestRequest from '@/utils/autoTestRequest'
import { useAICosts } from '@/composables/useAICosts'
import { useUserStore } from '@/stores/user'
import HelpDrawer from '@/components/HelpDrawer.vue'
import { helpContent } from '@/utils/help-content'

const router = useRouter()
const userStore = useUserStore()
const { fetchCosts, getCostText, getCost } = useAICosts()
const _uid = computed(() => userStore.userId || 'anon')

const showHelp = ref(false)
const helpData = helpContent.aiGenerateCases

const currentStep = ref(0)
const swaggerFile = ref(null)
const swaggerUrl = ref('')
const submitting = ref(false)
const importing = ref(false)
const previewTab = ref('cases')
const expandedCases = ref([0])
const groupName = ref('AI生成用例')
const cancelling = ref(false)

let pollTimer = null
let clockTimer = null

const options = reactive({
  max_cases_per_api: 3,
  include_boundary: true,
  include_auth: true,
  include_chain: true,
})

const generateResult = reactive({
  cases: [],
  scenarios: [],
  message: '',
  total: 0,
})

const taskProgress = reactive({
  task_id: '',
  status: '',
  progress: 0,
  phase: '',
  phase_label: '',
  total_apis: 0,
  processed_apis: 0,
  total_batches: 0,
  current_batch: 0,
  message: '',
  error: null,
  start_time: null,
})

// 计时器相关
const elapsedSeconds = ref(0)

const elapsedDisplay = computed(() => {
  const s = elapsedSeconds.value
  if (s <= 0) return ''
  const m = Math.floor(s / 60)
  const sec = s % 60
  if (m > 0) return `${m}分${sec}秒`
  return `${sec}秒`
})

function startClock(startTime) {
  stopClock()
  const base = startTime ? startTime * 1000 : Date.now()
  const updateElapsed = () => {
    elapsedSeconds.value = Math.floor((Date.now() - base) / 1000)
  }
  updateElapsed()
  clockTimer = setInterval(updateElapsed, 1000)
}

function stopClock() {
  if (clockTimer) {
    clearInterval(clockTimer)
    clockTimer = null
  }
}

const progressPercent = computed(() => {
  return Math.round((taskProgress.progress || 0) * 100)
})

const phaseIcon = computed(() => {
  const map = {
    analyzing: '🔍',
    generating_cases: '🧪',
    generating_scenarios: '🔗',
  }
  return map[taskProgress.phase] || '⏳'
})

const phaseLabel = computed(() => {
  if (taskProgress.phase_label) return taskProgress.phase_label
  const map = {
    analyzing: '分析接口文档...',
    generating_cases: '生成测试用例...',
    generating_scenarios: '生成场景链...',
  }
  return map[taskProgress.phase] || '准备中...'
})

const handleFileChange = (file) => {
  swaggerFile.value = file.raw
}

// 保存当前任务到 localStorage，页面切换后可恢复
const AI_TASK_ID_KEY = computed(() => `ai_generate_task_id_${_uid.value}`)
const AI_TASK_TIME_KEY = computed(() => `ai_generate_task_time_${_uid.value}`)

function saveTaskToStorage(taskId) {
  try {
    localStorage.setItem(AI_TASK_ID_KEY.value, taskId)
    localStorage.setItem(AI_TASK_TIME_KEY.value, Date.now().toString())
  } catch (e) { /* ignore */ }
}

function clearTaskStorage() {
  try {
    localStorage.removeItem(AI_TASK_ID_KEY.value)
    localStorage.removeItem(AI_TASK_TIME_KEY.value)
  } catch (e) { /* ignore */ }
}

function getStoredTaskId() {
  try {
    const taskId = localStorage.getItem(AI_TASK_ID_KEY.value)
    const taskTime = parseInt(localStorage.getItem(AI_TASK_TIME_KEY.value) || '0')
    // 任务超过 2 小时视为过期
    if (taskId && taskTime && (Date.now() - taskTime) < 2 * 60 * 60 * 1000) {
      return taskId
    }
    clearTaskStorage()
    return null
  } catch (e) {
    return null
  }
}

// 恢复之前的任务
async function resumeTask(taskId) {
  try {
    const task = await autoTestRequest.get(`/auto-test/ai-generate/tasks/${taskId}`)
    if (!task) {
      clearTaskStorage()
      return
    }

    // 任务已完成或失败，直接显示结果
    if (task.status === 'completed') {
      Object.assign(taskProgress, {
        task_id: taskId,
        status: task.status,
        progress: task.progress || 0,
        phase: task.phase || '',
        phase_label: task.phase_label || '',
        total_apis: task.total_apis || 0,
        processed_apis: task.processed_apis || 0,
        total_batches: task.total_batches || 0,
        current_batch: task.current_batch || 0,
        message: task.message || '',
        error: task.error || null,
        start_time: task.start_time || null,
      })
      if (task.cases) generateResult.cases = task.cases
      if (task.scenarios) generateResult.scenarios = task.scenarios
      generateResult.message = task.message || '生成完成'
      generateResult.total = task.cases?.length || 0

      if (task.start_time) {
        startClock(task.start_time)
        // 已完成任务，停止计时
        setTimeout(() => stopClock(), 100)
      }
      currentStep.value = 3
      clearTaskStorage()
      return
    }

    if (task.status === 'failed') {
      ElMessage.error(task.error || '之前的生成任务失败')
      clearTaskStorage()
      return
    }

    if (task.status === 'cancelled') {
      // 之前的任务被取消
      Object.assign(taskProgress, {
        task_id: taskId,
        status: task.status,
        progress: task.progress || 0,
        phase: task.phase || '',
        phase_label: task.phase_label || '',
        total_apis: task.total_apis || 0,
        processed_apis: task.processed_apis || 0,
        total_batches: task.total_batches || 0,
        current_batch: task.current_batch || 0,
        message: task.message || '',
        error: task.error || null,
        start_time: task.start_time || null,
      })
      if (task.cases) generateResult.cases = task.cases
      if (task.scenarios) generateResult.scenarios = task.scenarios
      generateResult.message = task.message || '生成已中止'
      generateResult.total = task.cases?.length || 0
      ElMessage.warning(task.phase_label || '之前的生成任务已被中止')
      if (task.start_time) {
        startClock(task.start_time)
        setTimeout(() => stopClock(), 100)
      }
      currentStep.value = 3
      clearTaskStorage()
      return
    }

    // 任务仍在进行中，恢复轮询
    Object.assign(taskProgress, {
      task_id: taskId,
      status: task.status,
      progress: task.progress || 0,
      phase: task.phase || '',
      phase_label: task.phase_label || '',
      total_apis: task.total_apis || 0,
      processed_apis: task.processed_apis || 0,
      total_batches: task.total_batches || 0,
      current_batch: task.current_batch || 0,
      message: task.message || '',
      error: task.error || null,
      start_time: task.start_time || null,
    })
    if (task.cases) generateResult.cases = task.cases
    if (task.scenarios) generateResult.scenarios = task.scenarios

    // 恢复计时器
    if (task.start_time) {
      startClock(task.start_time)
    }

    currentStep.value = 2
    startPolling(taskId)
  } catch (e) {
    console.error('恢复任务失败:', e)
    clearTaskStorage()
  }
}

// 开始轮询
function startPolling(taskId) {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }

  let lastProgress = taskProgress.progress || 0
  const pollStartTime = Date.now()

  pollTimer = setInterval(async () => {
    try {
      const task = await autoTestRequest.get(`/auto-test/ai-generate/tasks/${taskId}`)

      // 更新进度状态
      Object.assign(taskProgress, {
        status: task.status,
        progress: task.progress || 0,
        phase: task.phase || '',
        phase_label: task.phase_label || '',
        total_apis: task.total_apis || 0,
        processed_apis: task.processed_apis || 0,
        total_batches: task.total_batches || 0,
        current_batch: task.current_batch || 0,
        message: task.message || '',
        error: task.error || null,
        start_time: task.start_time || null,
      })

      // 累积用例和场景
      if (task.cases) generateResult.cases = task.cases
      if (task.scenarios) generateResult.scenarios = task.scenarios

      // 超时检测
      if (task.progress > lastProgress) lastProgress = task.progress
      const elapsed = (Date.now() - pollStartTime) / 1000
      if (elapsed > 30 && lastProgress === 0 && task.status === 'PENDING') {
        taskProgress.phase_label = '任务启动较慢，请耐心等待...'
      }
      if (elapsed > 300 && lastProgress === 0) {
        clearInterval(pollTimer)
        pollTimer = null
        stopClock()
        clearTaskStorage()
        ElMessage.error('任务超时，后端可能未正确处理。请检查后端日志。')
        currentStep.value = 1
        return
      }

      if (task.status === 'completed') {
        clearInterval(pollTimer)
        pollTimer = null
        stopClock()
        clearTaskStorage()
        generateResult.message = task.message || '生成完成'
        generateResult.total = task.cases?.length || 0
        currentStep.value = 3
      } else if (task.status === 'cancelled') {
        // 任务被取消，保留已生成用例
        clearInterval(pollTimer)
        pollTimer = null
        stopClock()
        clearTaskStorage()
        generateResult.message = task.message || '生成已中止'
        generateResult.total = task.cases?.length || 0
        ElMessage.warning(task.phase_label || 'AI 生成已被中止，已保留已生成的用例')
        currentStep.value = 3
      } else if (task.status === 'failed') {
        clearInterval(pollTimer)
        pollTimer = null
        stopClock()
        clearTaskStorage()
        ElMessage.error(task.error || '生成失败')
        currentStep.value = 1
      }
    } catch (e) {
      // 轮询请求失败不立即中断，继续尝试
      console.error('轮询进度失败:', e)
    }
  }, 2000)
}

const startGenerate = async () => {
  submitting.value = true

  try {
    const formData = new FormData()
    formData.append('max_cases_per_api', options.max_cases_per_api)
    formData.append('include_boundary', options.include_boundary)
    formData.append('include_auth', options.include_auth)
    formData.append('include_chain', options.include_chain)

    let resp
    if (swaggerFile.value) {
      formData.append('file', swaggerFile.value)
      resp = await autoTestRequest.post('/auto-test/ai-generate/from-swagger', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
    } else if (swaggerUrl.value) {
      formData.append('url', swaggerUrl.value)
      resp = await autoTestRequest.post('/auto-test/ai-generate/from-swagger-url', formData)
    }

    const taskId = resp?.task_id
    if (!taskId) {
      ElMessage.error('未获取到任务 ID')
      return
    }

    // 重置进度状态
    Object.assign(taskProgress, {
      task_id: taskId,
      status: resp?.status || 'PENDING',
      progress: 0,
      phase: '',
      phase_label: '',
      total_apis: 0,
      processed_apis: 0,
      total_batches: 0,
      current_batch: 0,
      message: '',
      error: null,
      start_time: null,
    })
    generateResult.cases = []
    generateResult.scenarios = []
    generateResult.message = ''
    generateResult.total = 0

    // 保存任务到 localStorage，支持页面切换后恢复
    saveTaskToStorage(taskId)

    currentStep.value = 2

    // 启动计时器
    startClock()

    // 开始轮询
    startPolling(taskId)
  } catch (e) {
    ElMessage.error('提交失败: ' + (e.response?.data?.detail || e.message))
    currentStep.value = 1
  } finally {
    submitting.value = false
  }
}

const confirmImport = async () => {
  if (!generateResult.cases?.length) {
    ElMessage.warning('没有要导入的用例')
    return
  }
  importing.value = true
  try {
    const resp = await autoTestRequest.post('/auto-test/ai-generate/confirm', {
      cases: generateResult.cases,
      scenarios: generateResult.scenarios,
      group_name: groupName.value || 'AI生成用例',
    })
    ElMessage.success(resp?.message || '导入成功')
    router.push('/auto-test')
  } catch (e) {
    ElMessage.error('导入失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    importing.value = false
  }
}

const handleCancel = async () => {
  if (!taskProgress.task_id) return
  try {
    await ElMessageBox.confirm('确定要中止生成吗？已生成的用例会保留，可在预览页查看并导入。', '中止生成', {
      confirmButtonText: '确定中止',
      cancelButtonText: '继续生成',
      type: 'warning',
    })
  } catch {
    return // 用户取消操作
  }

  cancelling.value = true
  try {
    await autoTestRequest.post(`/auto-test/ai-generate/tasks/${taskProgress.task_id}/cancel`)
    ElMessage.success('任务已标记为中止，后台将在当前批次完成后停止')
  } catch (e) {
    ElMessage.error('中止失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    cancelling.value = false
  }
}

const methodTagType = (method) => {
  const map = { GET: 'success', POST: 'primary', PUT: 'warning', DELETE: 'danger', PATCH: 'info' }
  return map[method] || 'info'
}

const getCaseName = (idx) => {
  return generateResult.cases?.[idx]?.name || `用例 ${idx + 1}`
}

// 组件挂载时检查是否有未完成的任务
onMounted(async () => {
  fetchCosts()
  const storedTaskId = getStoredTaskId()
  if (storedTaskId) {
    await resumeTask(storedTaskId)
  }
})

// 组件卸载时清理定时器（但不清除 localStorage，以便恢复）
onUnmounted(() => {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
  stopClock()
})
</script>

<style scoped>
.ai-generate-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px;
}
.page-header {
  margin-bottom: 24px;
}
.page-header h2 {
  margin: 8px 0 4px;
  font-size: 22px;
}
.subtitle {
  color: var(--el-text-color-secondary);
  font-size: 14px;
}
.steps-bar {
  margin-bottom: 32px;
}
.step-content {
  min-height: 400px;
}
.upload-area {
  max-width: 600px;
  margin: 0 auto;
}
.divider-or {
  text-align: center;
  margin: 20px 0;
  position: relative;
}
.divider-or::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 0;
  right: 0;
  border-top: 1px solid var(--el-border-color);
}
.divider-or span {
  background: var(--el-bg-color);
  padding: 0 16px;
  position: relative;
  color: var(--el-text-color-secondary);
}
.config-card {
  max-width: 600px;
  margin: 0 auto;
}
.form-tip {
  margin-left: 12px;
  color: var(--el-text-color-secondary);
  font-size: 13px;
}
.config-actions {
  text-align: center;
  margin-top: 24px;
}

/* 生成进度面板 */
.generating-content {
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding-top: 20px;
}
.progress-panel {
  max-width: 700px;
  width: 100%;
}
.progress-bar-section {
  margin-bottom: 24px;
}
.phase-indicator {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 24px;
  padding: 16px 20px;
  background: var(--el-fill-color-lighter);
  border-radius: 10px;
}
.phase-icon {
  font-size: 28px;
  line-height: 1;
}
.phase-text {
  display: flex;
  align-items: baseline;
  gap: 10px;
  flex: 1;
}
.phase-label {
  font-size: 16px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}
.phase-batch {
  font-size: 14px;
  color: var(--el-color-primary);
  font-weight: 500;
}
.elapsed-timer {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 16px;
  font-weight: 600;
  color: var(--el-color-primary);
  background: var(--el-color-primary-light-9);
  padding: 4px 12px;
  border-radius: 6px;
  white-space: nowrap;
}
.live-stats {
  display: flex;
  gap: 24px;
  margin-bottom: 16px;
}
.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
  padding: 12px 0;
  background: var(--el-fill-color-lighter);
  border-radius: 8px;
}
.stat-label {
  font-size: 13px;
  color: var(--el-text-color-secondary);
  margin-bottom: 6px;
}
.stat-value {
  font-size: 20px;
  font-weight: 700;
  color: var(--el-color-primary);
}
.safety-tip {
  margin-bottom: 16px;
}

/* 中止按钮区域 */
.generation-actions {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid var(--el-border-color-lighter);
}

.cancel-hint {
  font-size: 13px;
  color: var(--el-text-color-secondary);
}

/* 实时用例预览 */
.live-preview {
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 10px;
  overflow: hidden;
}
.live-preview-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 16px;
  background: var(--el-fill-color-lighter);
  font-weight: 600;
  font-size: 14px;
}
.live-case-list {
  max-height: 300px;
  overflow-y: auto;
  padding: 8px 12px;
}
.live-case-card {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  border-radius: 6px;
  margin-bottom: 4px;
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color-extra-light);
  transition: background 0.2s;
}
.live-case-card:hover {
  background: var(--el-fill-color-lighter);
}
.live-case-name {
  font-size: 13px;
  color: var(--el-text-color-regular);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 结果预览 */
.result-header {
  margin-bottom: 20px;
}
.result-stats {
  margin-top: 12px;
  display: flex;
  gap: 12px;
}
.case-title {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
}
.case-detail {
  padding: 8px 0;
}
.detail-row {
  margin-bottom: 12px;
}
.detail-row .label {
  font-weight: 600;
  margin-right: 8px;
  color: var(--el-text-color-regular);
}
.detail-row pre {
  background: var(--el-fill-color-light);
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 12px;
  overflow-x: auto;
  margin-top: 4px;
}
.detail-row code {
  background: var(--el-fill-color-light);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 13px;
}
.assert-item, .extractor-item {
  display: flex;
  align-items: center;
  gap: 6px;
  margin: 4px 0;
  font-size: 13px;
}
.assert-desc {
  color: var(--el-text-color-secondary);
  margin-left: 8px;
}
.scenario-card {
  margin-bottom: 16px;
}
.scenario-header {
  display: flex;
  align-items: center;
  gap: 8px;
}
.scenario-name {
  font-weight: 600;
  font-size: 15px;
}
.scenario-desc {
  color: var(--el-text-color-secondary);
  margin-bottom: 12px;
}
.scenario-steps {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.scenario-step {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  background: var(--el-fill-color-lighter);
  border-radius: 6px;
}
.step-num {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--el-color-primary);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
  flex-shrink: 0;
}
.step-desc {
  flex: 1;
}
.import-actions {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid var(--el-border-color-lighter);
}
.empty-tip {
  padding: 40px 0;
}

.ai-cost-hint {
  font-size: 11px;
  color: #ffa502;
  margin-left: 8px;
  white-space: nowrap;
}
</style>
