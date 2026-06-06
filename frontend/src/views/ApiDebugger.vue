<template>
  <div class="debug-container" :class="{ 'is-fullscreen': isFullscreen }">
    <div class="debug-toolbar">
      <div class="toolbar-left">
        <h2 class="debug-title">⚡ 接口调试</h2>
      </div>
      <div class="toolbar-right">
        <el-select v-model="debugEnvId" placeholder="选择环境" clearable size="small" style="width: 160px">
          <el-option v-for="env in environmentList" :key="env.id" :label="env.name" :value="env.id" />
        </el-select>
        <el-button size="small" @click="clearDebugForm">
          <el-icon><Delete /></el-icon>
          清空
        </el-button>
        <el-button size="small" @click="showHistory = !showHistory">
          <el-icon><Clock /></el-icon>
          历史
        </el-button>
        <el-button size="small" @click="toggleFullscreen">
          <el-icon><FullScreen /></el-icon>
          {{ isFullscreen ? '退出全屏' : '全屏' }}
        </el-button>
        <el-button size="small" @click="showCurlImport = true">
          <el-icon><Upload /></el-icon>
          导入cURL
        </el-button>
        <el-button size="small" @click="showHelp = true">
          ❓ 使用说明
        </el-button>
      </div>
    </div>

    <div class="debug-body">
      <div class="debug-panels" :class="{ 'panels-horizontal': !isFullscreen }">
        <div class="panel panel-request" tabindex="0" @keydown.ctrl.enter="sendDebugRequest" @keydown.meta.enter="sendDebugRequest">
          <div class="panel-header">
            <span class="panel-title">请求</span>
          </div>
          <div class="panel-content">
            <div class="request-line">
              <el-select v-model="debugForm.method" class="method-select" size="default">
                <el-option v-for="m in ['GET','POST','PUT','PATCH','DELETE']" :key="m" :label="m" :value="m" />
              </el-select>
              <el-input
                v-model="debugForm.url"
                placeholder="请求URL，如 https://api.example.com/users"
                clearable
                class="url-input"
              >
                <template #append>
                  <el-button @click="insertVariable('url')">
                    <el-icon><DataAnalysis /></el-icon>
                  </el-button>
                </template>
              </el-input>
              <el-input-number v-model="debugForm.timeout" :min="1" :max="60" size="default" style="width: 90px" />
              <span class="timeout-label">s</span>
              <el-button type="primary" @click="sendDebugRequest" :loading="debugLoading" class="send-btn">
                <el-icon><Right /></el-icon>
                发送
              </el-button>
            </div>

            <el-tabs v-model="debugReqTab" class="req-tabs">
              <el-tab-pane label="请求体" name="body">
                <div class="body-type-row">
                  <el-radio-group v-model="debugForm.bodyType" size="small">
                    <el-radio-button value="json">JSON</el-radio-button>
                    <el-radio-button value="form-data">Form</el-radio-button>
                    <el-radio-button value="text">Text</el-radio-button>
                    <el-radio-button value="xml">XML</el-radio-button>
                  </el-radio-group>
                  <div class="body-actions-inline">
                    <el-button size="small" text type="primary" @click="formatJson('body')" v-if="debugForm.bodyType === 'json'">
                      <el-icon><MagicStick /></el-icon> 格式化
                    </el-button>
                    <el-button size="small" text type="primary" @click="insertVariable('body')" v-if="debugForm.bodyType !== 'form-data'">
                      <el-icon><DataAnalysis /></el-icon> 变量
                    </el-button>
                  </div>
                </div>
                <template v-if="debugForm.bodyType === 'form-data'">
                  <div class="kv-list">
                    <div v-for="(item, idx) in debugForm.formData" :key="idx" class="kv-row">
                      <el-input v-model="item.key" placeholder="字段名" size="small" />
                      <el-input v-model="item.value" placeholder="字段值" size="small" />
                      <el-button text type="danger" size="small" @click="debugForm.formData.splice(idx, 1)">
                        <el-icon><Delete /></el-icon>
                      </el-button>
                    </div>
                    <el-button size="small" text type="primary" @click="debugForm.formData.push({ key: '', value: '' })">
                      <el-icon><Plus /></el-icon> 添加字段
                    </el-button>
                  </div>
                </template>
                <el-input
                  v-else
                  v-model="debugForm.body"
                  type="textarea"
                  :rows="6"
                  placeholder="请求体内容"
                  class="body-textarea"
                />
              </el-tab-pane>
              <el-tab-pane label="请求头" name="headers">
                <div class="kv-list">
                  <div v-for="(item, idx) in debugForm.headers" :key="idx" class="kv-row">
                    <el-input v-model="item.key" placeholder="键名" size="small" />
                    <el-input v-model="item.value" placeholder="键值" size="small" />
                    <el-button text type="danger" size="small" @click="debugForm.headers.splice(idx, 1)">
                      <el-icon><Delete /></el-icon>
                    </el-button>
                  </div>
                  <el-button size="small" text type="primary" @click="debugForm.headers.push({ key: '', value: '' })">
                    <el-icon><Plus /></el-icon> 添加请求头
                  </el-button>
                </div>
              </el-tab-pane>
              <el-tab-pane label="参数" name="params">
                <div class="kv-list">
                  <div v-for="(item, idx) in debugForm.params" :key="idx" class="kv-row">
                    <el-input v-model="item.key" placeholder="参数名" size="small" />
                    <el-input v-model="item.value" placeholder="参数值" size="small" />
                    <el-button text type="danger" size="small" @click="debugForm.params.splice(idx, 1)">
                      <el-icon><Delete /></el-icon>
                    </el-button>
                  </div>
                  <el-button size="small" text type="primary" @click="debugForm.params.push({ key: '', value: '' })">
                    <el-icon><Plus /></el-icon> 添加参数
                  </el-button>
                </div>
              </el-tab-pane>
            </el-tabs>
          </div>
        </div>

        <div class="panel panel-response">
          <div class="panel-header">
            <span class="panel-title">响应</span>
            <div class="response-badges" v-if="debugResponse">
              <el-tag :type="getHttpStatusTagType(debugResponse.status_code)" size="small" effect="dark">
                {{ formatStatusCode(debugResponse.status_code) }}
              </el-tag>
              <el-tag type="info" size="small" effect="plain">
                {{ getExecutionTime(debugResponse) }}ms
              </el-tag>
              <el-tag type="info" size="small" effect="plain" v-if="getContentLength(debugResponse)">
                {{ getContentLength(debugResponse) }}B
              </el-tag>
            </div>
          </div>
          <div class="panel-content">
            <div v-if="!debugResponse" class="response-empty">
              <div class="re-icon">📡</div>
              <p>发送请求后查看响应结果</p>
            </div>
            <template v-else>
              <div class="response-actions">
                <el-button size="small" text @click="copyResponse">
                  <el-icon><DocumentCopy /></el-icon> 复制
                </el-button>
                <el-button size="small" text type="primary" @click="saveToApiLibrary">
                  <el-icon><Plus /></el-icon> 保存到接口库
                </el-button>
              </div>
              <el-tabs v-model="debugResTab" class="res-tabs">
                <el-tab-pane label="响应体" name="body">
                  <pre class="response-body-pre">{{ formattedResponse }}</pre>
                </el-tab-pane>
                <el-tab-pane label="响应头" name="headers">
                  <pre class="response-body-pre">{{ JSON.stringify(debugResponse.headers, null, 2) }}</pre>
                </el-tab-pane>
                <el-tab-pane label="请求详情" name="request">
                  <pre class="response-body-pre">{{ JSON.stringify(debugRequestDetails, null, 2) }}</pre>
                </el-tab-pane>
              </el-tabs>
              <div v-if="debugResponse.error" class="error-message">
                <el-alert :title="debugResponse.error" type="error" show-icon :closable="false" />
              </div>
            </template>
          </div>
        </div>
      </div>
    </div>

    <el-drawer v-model="showHistory" title="📋 请求历史" size="500px" direction="rtl">
      <div class="history-container">
        <el-empty v-if="debugHistory.length === 0" description="暂无历史记录" />
        <el-timeline v-else>
          <el-timeline-item
            v-for="(item, index) in debugHistory"
            :key="index"
            :timestamp="item.timestamp"
            :type="getHttpStatusTagType(item.status_code)"
          >
            <div class="history-item">
              <div class="history-header">
                <span class="history-method">{{ item.method }}</span>
                <span class="history-url">{{ item.url }}</span>
                <el-tag :type="getHttpStatusTagType(item.status_code)" size="small" style="margin-left: 8px;">
                  {{ formatStatusCode(item.status_code) }}
                </el-tag>
              </div>
              <div class="history-actions">
                <el-button size="small" type="primary" @click="resendHistoryRequest(item)">
                  <el-icon><Right /></el-icon> 再次请求
                </el-button>
                <el-button size="small" @click="loadHistoryItem(item)">
                  <el-icon><Edit /></el-icon> 加载
                </el-button>
                <el-button size="small" type="danger" @click="debugHistory.splice(debugHistory.indexOf(item), 1)">
                  <el-icon><Delete /></el-icon>
                </el-button>
              </div>
            </div>
          </el-timeline-item>
        </el-timeline>
        <el-button type="danger" size="small" @click="clearHistory" v-if="debugHistory.length > 0" style="margin-top: 16px;">
          <el-icon><Delete /></el-icon> 清空历史
        </el-button>
      </div>
    </el-drawer>

    <el-dialog v-model="showVariableDialog" title="插入变量" width="500px" append-to-body destroy-on-close>
      <div class="variable-dialog">
        <el-input v-model="variableSearch" placeholder="搜索变量" style="margin-bottom: 16px;">
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>
        <div class="variable-list">
          <el-tag
            v-for="varItem in filteredVariables"
            :key="varItem.id"
            :type="varItem.is_encrypted ? 'warning' : 'info'"
            effect="plain"
            class="variable-tag"
            @click="insertVariableValue(varItem.name)"
          >
            <span v-text="varItem.name"></span>
            <span class="var-value" v-if="varItem.value && !varItem.is_encrypted"><span v-text="'(' + varItem.value + ')'"></span></span>
            <span class="var-value" v-else-if="varItem.is_encrypted">(加密)</span>
            <span class="var-value" v-else-if="varItem.description"><span v-text="'(' + varItem.description + ')'"></span></span>
          </el-tag>
        </div>
        <el-empty v-if="filteredVariables.length === 0" description="暂无变量" style="margin-top: 32px;" />
      </div>
      <template #footer>
        <el-button @click="showVariableDialog = false">取消</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="saveToApiLibraryDialog" title="保存到接口库" width="500px" append-to-body destroy-on-close>
      <el-form :model="apiLibraryForm" label-width="80px">
        <el-form-item label="接口名称" required>
          <el-input v-model="apiLibraryForm.name" placeholder="请输入接口名称" />
        </el-form-item>
        <el-form-item label="所属分组" required>
          <el-select v-model="apiLibraryForm.group_id" placeholder="请选择分组" style="width:100%">
            <el-option v-for="group in apiGroups" :key="group.id" :label="group.name" :value="group.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="接口描述">
          <el-input v-model="apiLibraryForm.description" type="textarea" placeholder="请输入接口描述" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="saveToApiLibraryDialog = false">取消</el-button>
        <el-button type="primary" @click="confirmSaveToApiLibrary">确定</el-button>
      </template>
    </el-dialog>

    <HelpDrawer
      v-model="showHelp"
      :title="helpData.title"
      :intro="helpData.intro"
      :sections="helpData.sections"
    />

    <CurlImportDialog v-model="showCurlImport" @import="handleCurlImport" />
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Right, Delete, Clock, Timer, MagicStick, DocumentCopy, DataAnalysis, Document, Plus, Search, Edit, FullScreen, Upload } from '@element-plus/icons-vue'
import autoTestRequest from '@/utils/autoTestRequest'
import HelpDrawer from '@/components/HelpDrawer.vue'
import { helpContent } from '@/utils/help-content'
import CurlImportDialog from './CurlImportDialog.vue'

const props = defineProps({
  environmentList: { type: Array, default: () => [] }
})
const emit = defineEmits(['case-saved'])

const isFullscreen = ref(false)
const debugEnvId = ref(null)
const debugForm = ref({
  method: 'GET', url: '', headers: [], body: '', formData: [],
  bodyType: 'json', timeout: 5, params: []
})
const debugLoading = ref(false)
const debugResponse = ref(null)
const debugReqTab = ref('body')
const debugResTab = ref('body')
const debugRequestDetails = ref({})
const showVariableDialog = ref(false)
const variableTarget = ref('')
const variables = ref([])
const filteredVariables = ref([])
const variableSearch = ref('')
const debugHistory = ref([])
const showHistory = ref(false)
const saveToApiLibraryDialog = ref(false)
const apiLibraryForm = ref({ name: '', group_id: '', description: '' })
const apiGroups = ref([])
const showHelp = ref(false)
const helpData = helpContent.apiDebugger
const showCurlImport = ref(false)

const handleCurlImport = (parsedData) => {
  if (!parsedData) return
  debugForm.value.method = parsedData.method || 'GET'
  debugForm.value.url = parsedData.url || ''
  debugForm.value.body = parsedData.body || ''
  debugForm.value.bodyType = 'json'
  if (parsedData.headers && typeof parsedData.headers === 'object') {
    debugForm.value.headers = Object.entries(parsedData.headers).map(([key, value]) => ({ key, value: String(value) }))
  }
  showCurlImport.value = false
  ElMessage.success('cURL 已解析，可点击发送进行调试')
}

const toggleFullscreen = () => {
  const el = document.querySelector('.debug-container')
  if (!document.fullscreenElement) {
    el?.requestFullscreen?.().then(() => { isFullscreen.value = true }).catch(() => { isFullscreen.value = !isFullscreen.value })
  } else {
    document.exitFullscreen?.().then(() => { isFullscreen.value = false }).catch(() => { isFullscreen.value = !isFullscreen.value })
  }
}

const handleFullscreenChange = () => {
  isFullscreen.value = !!document.fullscreenElement
}

const getHttpStatusTagType = (statusCode) => {
  if (typeof statusCode !== 'number') return 'info'
  return statusCode < 400 ? 'success' : 'danger'
}

const formatStatusCode = (statusCode) => {
  return typeof statusCode === 'number' ? statusCode : '未返回'
}

const getExecutionTime = (response) => {
  return response?.execution_time ?? response?.elapsed_ms ?? 0
}

const getContentLength = (response) => {
  return response?.content_length ?? 0
}

const formattedResponse = computed(() => {
  if (!debugResponse.value) return ''
  try {
    const payload = debugResponse.value.response_content ?? debugResponse.value.data ?? debugResponse.value.body
    if (typeof payload === 'object' && payload !== null) return JSON.stringify(payload, null, 2)
    else if (payload) return payload
    return JSON.stringify(debugResponse.value, null, 2)
  } catch (error) {
    return String(debugResponse.value)
  }
})

const replaceVariables = (template, vars) => {
  if (!template || typeof template !== 'string') return template
  return template.replace(/\{\{(.*?)\}\}/g, (match, varName) => {
    varName = varName.trim()
    if (Array.isArray(vars)) {
      const found = vars.find(v => v && v.name === varName)
      return found && found.value !== undefined ? found.value : match
    } else if (vars && typeof vars === 'object') {
      return vars[varName] !== undefined ? vars[varName] : match
    }
    return match
  })
}

const sendDebugRequest = async () => {
  if (!debugForm.value.url.trim()) { ElMessage.warning('请输入请求URL'); return }
  debugLoading.value = true
  debugResponse.value = null
  try {
    const varsArray = variables.value || []
    const headersObj = {}
    debugForm.value.headers.forEach(item => { if (item.key) headersObj[replaceVariables(item.key, varsArray)] = replaceVariables(item.value, varsArray) })
    const paramsObj = {}
    debugForm.value.params.forEach(item => { if (item.key) paramsObj[replaceVariables(item.key, varsArray)] = replaceVariables(item.value, varsArray) })
    const payload = {
      method: debugForm.value.method,
      url: replaceVariables(debugForm.value.url, varsArray),
      headers: headersObj, params: paramsObj,
      body: debugForm.value.bodyType === 'form-data'
        ? Object.fromEntries((debugForm.value.formData || []).filter(item => item.key).map(item => [replaceVariables(item.key, varsArray), replaceVariables(item.value, varsArray)]))
        : replaceVariables(debugForm.value.body || '', varsArray),
      body_type: debugForm.value.bodyType
    }
    if (debugEnvId.value) payload.env_id = debugEnvId.value
    debugRequestDetails.value = { method: debugForm.value.method, url: replaceVariables(debugForm.value.url, varsArray), headers: headersObj, params: paramsObj, body: payload.body, bodyType: debugForm.value.bodyType, timeout: debugForm.value.timeout }
    const res = await autoTestRequest.post('/auto-test/send', payload)
    debugResponse.value = res
    if (debugResponse.value.error && !debugResponse.value.status_code) ElMessage.error(debugResponse.value.error)
  } catch (err) {
    debugResponse.value = { error: err.response?.data?.detail || err.response?.data?.error || err.message || '请求发送失败', status_code: typeof err.response?.status === 'number' ? err.response.status : null, success: false }
    ElMessage.error('请求发送失败')
  } finally {
    debugLoading.value = false
    addToHistory()
  }
}

const addToHistory = () => {
  const varsArray = variables.value || []
  const headersObj = {}
  debugForm.value.headers.forEach(item => { if (item.key) headersObj[replaceVariables(item.key, varsArray)] = replaceVariables(item.value, varsArray) })
  const paramsObj = {}
  debugForm.value.params.forEach(item => { if (item.key) paramsObj[replaceVariables(item.key, varsArray)] = replaceVariables(item.value, varsArray) })
  const historyItem = {
    id: Date.now() + Math.random(),
    method: debugForm.value.method, url: replaceVariables(debugForm.value.url, varsArray),
    headers: headersObj, params: paramsObj, body: replaceVariables(debugForm.value.body || '', varsArray),
    body_type: debugForm.value.bodyType,
    form_data: debugForm.value.bodyType === 'form-data' ? [...(debugForm.value.formData || [])] : [],
    status_code: typeof debugResponse.value?.status_code === 'number' ? debugResponse.value.status_code : null,
    error: debugResponse.value?.error || '', timestamp: new Date().toLocaleString('zh-CN'), env_id: debugEnvId.value
  }
  debugHistory.value.unshift(historyItem)
  if (debugHistory.value.length > 50) debugHistory.value = debugHistory.value.slice(0, 50)
}

const resendHistoryRequest = async (item) => {
  debugForm.value.method = item.method; debugForm.value.url = item.url
  debugForm.value.headers = item.headers && typeof item.headers === 'object' ? Object.entries(item.headers).map(([key, value]) => ({ key, value })) : []
  debugForm.value.params = item.params && typeof item.params === 'object' ? Object.entries(item.params).map(([key, value]) => ({ key, value })) : []
  debugForm.value.body = item.body; debugForm.value.bodyType = item.body_type
  debugForm.value.formData = Array.isArray(item.form_data) ? item.form_data.map(row => ({ key: row.key || '', value: row.value || '' })) : []
  debugEnvId.value = item.env_id; showHistory.value = false
  await sendDebugRequest()
}

const loadHistoryItem = (item) => {
  debugForm.value.method = item.method; debugForm.value.url = item.url
  debugForm.value.headers = item.headers && typeof item.headers === 'object' ? Object.entries(item.headers).map(([key, value]) => ({ key, value })) : []
  debugForm.value.params = item.params && typeof item.params === 'object' ? Object.entries(item.params).map(([key, value]) => ({ key, value })) : []
  debugForm.value.body = item.body; debugForm.value.bodyType = item.body_type
  debugForm.value.formData = Array.isArray(item.form_data) ? item.form_data.map(row => ({ key: row.key || '', value: row.value || '' })) : []
  debugEnvId.value = item.env_id; showHistory.value = false
  ElMessage.success('已加载历史请求参数')
}

const insertVariable = (target) => { variableTarget.value = target; showVariableDialog.value = true; loadVariables() }

const insertVariableValue = (variableValue) => {
  if (variableTarget.value && debugForm.value[variableTarget.value] !== undefined) {
    const currentValue = debugForm.value[variableTarget.value] || ''
    debugForm.value = { ...debugForm.value, [variableTarget.value]: currentValue + `{{${variableValue}}}` }
  }
  showVariableDialog.value = false
}

const saveToApiLibrary = async () => {
  try {
    const isOk = debugResponse.value && (debugResponse.value.status_code >= 200 && debugResponse.value.status_code < 300) && debugResponse.value.success !== false
    if (!isOk) {
      try { await ElMessageBox.confirm('该接口当前未调试通过，直接保存可能导致用例执行失败。是否确认强制保存？', '确认保存', { confirmButtonText: '强制保存', cancelButtonText: '重新调试', type: 'warning' }) } catch { return }
    }
    await loadApiGroups()
    const url = debugForm.value.url; const urlParts = url.split('/'); const lastPart = urlParts[urlParts.length - 1]
    apiLibraryForm.value.name = `${debugForm.value.method} ${lastPart || url}`
    saveToApiLibraryDialog.value = true
  } catch (error) { if (error !== 'cancel') ElMessage.error('加载接口分组失败') }
}

const loadApiGroups = async () => { try { const res = await autoTestRequest.get('/auto-test/groups'); apiGroups.value = res || [] } catch (error) { console.error('加载分组失败', error) } }

const confirmSaveToApiLibrary = async () => {
  if (!apiLibraryForm.value.name) { ElMessage.warning('请输入接口名称'); return }
  if (!apiLibraryForm.value.group_id) { ElMessage.warning('请选择所属分组'); return }
  try {
    let headers = {}
    if (Array.isArray(debugForm.value.headers)) debugForm.value.headers.forEach(item => { if (item.key) headers[item.key] = item.value })
    else if (debugForm.value.headers && typeof debugForm.value.headers === 'object') headers = debugForm.value.headers
    let params = {}
    if (Array.isArray(debugForm.value.params)) debugForm.value.params.forEach(item => { if (item.key) params[item.key] = item.value })
    else if (debugForm.value.params && typeof debugForm.value.params === 'object') params = debugForm.value.params
    let requestPayload = null
    const rawBodyType = debugForm.value.bodyType || 'none'
    const bodyTypeMapping = { 'json': 'raw', 'raw': 'raw', 'form-data': 'form-data', 'none': 'none', 'text': 'raw', 'xml': 'raw', 'html': 'raw' }
    const bodyType = bodyTypeMapping[rawBodyType] || rawBodyType
    const bodyContent = debugForm.value.body || ''
    if (bodyType === 'raw' || rawBodyType === 'json') {
      if (bodyContent && bodyContent.trim()) { try { requestPayload = JSON.parse(bodyContent) } catch (e) { ElMessage.error('请求体 JSON 格式错误'); return } }
      else requestPayload = {}
    } else if (bodyType === 'form-data') {
      requestPayload = {}
      if (Array.isArray(debugForm.value.formData)) debugForm.value.formData.forEach(item => { if (item.key) requestPayload[item.key] = item.value })
    }
    let contentType = 'application/json'
    if (rawBodyType === 'xml') contentType = 'application/xml'
    else if (rawBodyType === 'html') contentType = 'text/html'
    else if (rawBodyType === 'text') contentType = 'text/plain'
    else if (rawBodyType === 'form-data') contentType = 'multipart/form-data'
    const payload = { name: apiLibraryForm.value.name, group_id: apiLibraryForm.value.group_id, method: debugForm.value.method, url: debugForm.value.url, headers, params, body_type: bodyType, content_type: contentType, payload: requestPayload, form_data: bodyType === 'form-data' ? requestPayload : {}, description: apiLibraryForm.value.description }
    await autoTestRequest.post('/auto-test/cases', payload)
    ElMessage.success('保存到接口库成功'); saveToApiLibraryDialog.value = false; emit('case-saved')
  } catch (error) { ElMessage.error(error.response?.data?.detail || '保存到接口库失败') }
}

const loadVariables = async () => {
  try {
    const res = await autoTestRequest.get('/auto-test/global-variables')
    const globalVariables = Array.isArray(res) ? res : []
    const dynamicVariables = [
      { id: 'd1', name: '$timestamp', value: '', description: '当前时间戳', is_encrypted: false },
      { id: 'd2', name: '$random_int', value: '', description: '随机整数', is_encrypted: false },
      { id: 'd3', name: '$random_string', value: '', description: '随机字符串', is_encrypted: false },
      { id: 'd4', name: '$uuid', value: '', description: 'UUID', is_encrypted: false },
      { id: 'd5', name: '$datetime', value: '', description: '当前日期时间', is_encrypted: false }
    ]
    variables.value = [...globalVariables, ...dynamicVariables]; filteredVariables.value = variables.value
  } catch (error) {
    variables.value = [
      { id: 'd1', name: '$timestamp', value: '', description: '当前时间戳', is_encrypted: false },
      { id: 'd2', name: '$random_int', value: '', description: '随机整数', is_encrypted: false },
      { id: 'd3', name: '$random_string', value: '', description: '随机字符串', is_encrypted: false },
      { id: 'd4', name: '$uuid', value: '', description: 'UUID', is_encrypted: false },
      { id: 'd5', name: '$datetime', value: '', description: '当前日期时间', is_encrypted: false }
    ]; filteredVariables.value = variables.value
  }
}

const clearDebugForm = () => {
  debugForm.value = { method: 'GET', url: '', headers: [], body: '', formData: [], bodyType: 'json', timeout: 5, params: [] }
  debugResponse.value = null
}

const clearHistory = () => { debugHistory.value = [] }

const copyResponse = () => {
  if (debugResponse.value) {
    navigator.clipboard.writeText(JSON.stringify(debugResponse.value, null, 2))
      .then(() => ElMessage.success('响应已复制到剪贴板'))
      .catch(() => ElMessage.error('复制失败'))
  }
}

const formatJson = (field) => {
  try {
    const value = debugForm.value[field]
    if (!value) return
    try {
      debugForm.value[field] = JSON.stringify(JSON.parse(value), null, 2)
      ElMessage.success('JSON 格式化成功')
    } catch {
      try {
        const fixed = value
          .replace(/(\w+)\s*:/g, '"$1":')
          .replace(/'/g, '"')
          .replace(/,\s*([}\]])/g, '$1')
        debugForm.value[field] = JSON.stringify(JSON.parse(fixed), null, 2)
        ElMessage.success('JSON 格式化成功（已自动修正格式）')
      } catch {
        ElMessage.error('JSON 格式错误，请检查输入是否为有效的 JSON 或 JS 对象格式')
      }
    }
  } catch (error) { ElMessage.error('JSON 格式错误') }
}

watch(() => variableSearch.value, (search) => {
  if (!search) filteredVariables.value = variables.value
  else filteredVariables.value = variables.value.filter(v => v.name.toLowerCase().includes(search.toLowerCase()) || (v.description && v.description.toLowerCase().includes(search.toLowerCase())))
})

onMounted(() => { document.addEventListener('fullscreenchange', handleFullscreenChange) })
onUnmounted(() => { document.removeEventListener('fullscreenchange', handleFullscreenChange) })
</script>

<style scoped>
.debug-container {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.debug-container.is-fullscreen {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  z-index: 9999;
  background: #1a1a2e;
  padding: 0;
}

.debug-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 16px;
  border-bottom: 1px solid var(--border-color, #333);
  flex-shrink: 0;
}

.debug-title {
  margin: 0;
  font-size: 16px;
  color: #e0e0e0;
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.debug-body {
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

.debug-panels {
  display: flex;
  flex-direction: column;
  height: 100%;
  gap: 0;
}

.debug-panels.panels-horizontal {
  flex-direction: row;
}

.panel {
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
}

.panels-horizontal .panel {
  width: 50%;
}

.panels-horizontal .panel-request {
  border-right: 1px solid var(--border-color, #333);
}

.panel:not(.panels-horizontal .panel) {
  flex: 1;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 16px;
  border-bottom: 1px solid var(--border-color, #2a2a2a);
  background: rgba(255,255,255,.02);
  flex-shrink: 0;
}

.panel-title {
  font-size: 13px;
  font-weight: 600;
  color: #aaa;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.response-badges {
  display: flex;
  gap: 6px;
}

.panel-content {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 12px 16px;
}

.request-line {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-bottom: 12px;
  flex-wrap: wrap;
}

.method-select {
  width: 110px;
  flex-shrink: 0;
}

.url-input {
  flex: 1;
  min-width: 200px;
}

.timeout-label {
  font-size: 12px;
  color: #888;
  margin-left: -6px;
}

.send-btn {
  flex-shrink: 0;
}

.body-type-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.body-actions-inline {
  display: flex;
  gap: 4px;
}

.body-textarea :deep(.el-textarea__inner) {
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 13px;
  line-height: 1.5;
}

.kv-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.kv-row {
  display: flex;
  gap: 6px;
  align-items: center;
}

.kv-row .el-input {
  flex: 1;
}

.response-empty {
  text-align: center;
  padding: 40px 0;
  color: #666;
}

.re-icon {
  font-size: 40px;
  margin-bottom: 8px;
}

.response-actions {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
}

.response-body-pre {
  background: rgba(0,0,0,.3);
  color: #e0e0e0;
  padding: 12px;
  border-radius: 6px;
  font-size: 13px;
  line-height: 1.5;
  overflow: auto;
  max-height: calc(100vh - 400px);
  white-space: pre-wrap;
  word-break: break-all;
  margin: 0;
  font-family: 'Consolas', 'Monaco', monospace;
}

.is-fullscreen .response-body-pre {
  max-height: calc(100vh - 200px);
}

.error-message {
  margin-top: 8px;
}

.req-tabs :deep(.el-tabs__header) {
  margin-bottom: 8px;
}

.res-tabs :deep(.el-tabs__header) {
  margin-bottom: 8px;
}

.history-container {
  padding: 16px;
  max-height: 70vh;
  overflow: auto;
}

.history-item {
  background: rgba(255,255,255,.03);
  border: 1px solid var(--border-color, #333);
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 8px;
}

.history-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  flex-wrap: wrap;
}

.history-method {
  font-weight: 600;
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 4px;
  background: rgba(64,158,255,.15);
  color: #409eff;
}

.history-url {
  flex: 1;
  font-size: 13px;
  color: #ccc;
  word-break: break-all;
}

.history-actions {
  display: flex;
  gap: 6px;
}

.variable-dialog {
  padding: 16px;
}

.variable-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 16px;
  max-height: 400px;
  overflow-y: auto;
}

.variable-tag {
  cursor: pointer;
  transition: all .15s;
}

.variable-tag:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(64,158,255,.3);
}

.var-value {
  font-size: 11px;
  opacity: .7;
  margin-left: 6px;
}

@media (max-width: 900px) {
  .debug-panels.panels-horizontal {
    flex-direction: column;
  }
  .panels-horizontal .panel {
    width: 100%;
  }
  .panels-horizontal .panel-request {
    border-right: none;
    border-bottom: 1px solid var(--border-color, #333);
  }
  .request-line {
    flex-wrap: wrap;
  }
  .method-select, .url-input {
    min-width: unset;
  }
  .url-input {
    width: 100%;
    order: 10;
  }
}
</style>
