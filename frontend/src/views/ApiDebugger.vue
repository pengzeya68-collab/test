<template>
  <div class="debug-container">
    <div class="debug-toolbar">
      <div class="toolbar-left">
        <h2 class="debug-title">⚡ 接口调试</h2>
      </div>
      <div class="toolbar-right">
        <el-select v-model="debugEnvId" placeholder="选择环境" clearable style="width: 200px; margin-right: 12px;">
          <el-option v-for="env in environmentList" :key="env.id" :label="env.name" :value="env.id" />
        </el-select>
        <el-button type="info" size="small" @click="clearDebugForm">
          <el-icon><Delete /></el-icon>
          清空
        </el-button>
        <el-button type="info" size="small" @click="showHistory = !showHistory">
          <el-icon><Clock /></el-icon>
          历史
        </el-button>
      </div>
    </div>

    <el-card class="debug-card request-card">
      <div class="request-line">
        <el-select v-model="debugForm.method" class="method-select" size="large">
          <el-option v-for="m in ['GET','POST','PUT','PATCH','DELETE']" :key="m" :label="m" :value="m" />
        </el-select>
        <el-input
          v-model="debugForm.url"
          placeholder="请求URL，如 https://api.example.com/users"
          size="large"
          clearable
          class="url-input"
        >
          <template #append>
            <el-button size="large" @click="insertVariable('url')">
              <el-icon><DataAnalysis /></el-icon>
            </el-button>
          </template>
        </el-input>
        <div class="request-actions">
          <el-input-number v-model="debugForm.timeout" :min="1" :max="60" size="large" placeholder="超时" style="width: 100px; margin-right: 12px;">
            <template #append>s</template>
          </el-input-number>
          <el-button type="primary" size="large" @click="sendDebugRequest" :loading="debugLoading" class="send-button">
            <el-icon><Right /></el-icon>
            发送
          </el-button>
        </div>
      </div>

      <el-tabs v-model="debugReqTab" class="request-tabs">
        <el-tab-pane label="请求头" name="headers">
          <div class="tab-content">
            <el-table :data="debugForm.headers" border size="small">
              <el-table-column prop="key" label="键名" min-width="120">
                <template #default="{ row }">
                  <el-input v-model="row.key" placeholder="键名" />
                </template>
              </el-table-column>
              <el-table-column prop="value" label="键值" min-width="200">
                <template #default="{ row }">
                  <el-input v-model="row.value" placeholder="键值" />
                </template>
              </el-table-column>
              <el-table-column label="操作" width="80" align="center">
                <template #default="{ $index }">
                  <el-button type="danger" size="small" @click="debugForm.headers.splice($index, 1)">
                    <el-icon><Delete /></el-icon>
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
            <el-button size="small" type="primary" @click="debugForm.headers.push({ key: '', value: '' })" style="margin-top: 8px;">
              <el-icon><Plus /></el-icon>
              添加请求头
            </el-button>
          </div>
        </el-tab-pane>
        <el-tab-pane label="请求体" name="body">
          <div class="tab-content">
            <div class="body-type-selector">
              <el-radio-group v-model="debugForm.bodyType" size="small">
                <el-radio-button value="json">JSON</el-radio-button>
                <el-radio-button value="form-data">Form-Data</el-radio-button>
                <el-radio-button value="text">Text</el-radio-button>
                <el-radio-button value="xml">XML</el-radio-button>
                <el-radio-button value="html">HTML</el-radio-button>
              </el-radio-group>
            </div>
            <template v-if="debugForm.bodyType === 'form-data'">
              <el-table :data="debugForm.formData" border size="small">
                <el-table-column prop="key" label="字段名" min-width="140">
                  <template #default="{ row }">
                    <el-input v-model="row.key" placeholder="字段名" />
                  </template>
                </el-table-column>
                <el-table-column prop="value" label="字段值" min-width="220">
                  <template #default="{ row }">
                    <el-input v-model="row.value" placeholder="字段值，可使用 {{变量}}" />
                  </template>
                </el-table-column>
                <el-table-column label="操作" width="80" align="center">
                  <template #default="{ $index }">
                    <el-button type="danger" size="small" @click="debugForm.formData.splice($index, 1)">
                      <el-icon><Delete /></el-icon>
                    </el-button>
                  </template>
                </el-table-column>
              </el-table>
              <el-button size="small" type="primary" @click="debugForm.formData.push({ key: '', value: '' })" style="margin-top: 8px;">
                <el-icon><Plus /></el-icon>
                添加字段
              </el-button>
            </template>
            <el-input
              v-else
              v-model="debugForm.body"
              type="textarea"
              :rows="8"
              placeholder="请求体内容"
              class="json-input"
            />
            <div class="body-actions">
              <el-button size="small" type="info" @click="formatJson('body')" v-if="debugForm.bodyType === 'json'">
                <el-icon><MagicStick /></el-icon>
                格式化
              </el-button>
              <el-button size="small" type="info" @click="insertVariable('body')" style="margin-left: 8px;" v-if="debugForm.bodyType !== 'form-data'">
                <el-icon><DataAnalysis /></el-icon>
                插入变量
              </el-button>
            </div>
          </div>
        </el-tab-pane>
        <el-tab-pane label="参数" name="params">
          <div class="tab-content">
            <el-table :data="debugForm.params" border size="small">
              <el-table-column prop="key" label="参数名" min-width="120">
                <template #default="{ row }">
                  <el-input v-model="row.key" placeholder="参数名" />
                </template>
              </el-table-column>
              <el-table-column prop="value" label="参数值" min-width="200">
                <template #default="{ row }">
                  <el-input v-model="row.value" placeholder="参数值" />
                </template>
              </el-table-column>
              <el-table-column label="操作" width="80" align="center">
                <template #default="{ $index }">
                  <el-button type="danger" size="small" @click="debugForm.params.splice($index, 1)">
                    <el-icon><Delete /></el-icon>
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
            <el-button size="small" type="primary" @click="debugForm.params.push({ key: '', value: '' })" style="margin-top: 8px;">
              <el-icon><Plus /></el-icon>
              添加参数
            </el-button>
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <el-card v-if="debugResponse" class="debug-card response-card" style="margin-top: 16px;">
      <template #header>
        <div class="response-header">
          <h3 class="response-title">📊 响应结果</h3>
          <div class="response-meta">
            <el-tag :type="getHttpStatusTagType(debugResponse.status_code)" size="small" class="status-code">
              {{ formatStatusCode(debugResponse.status_code) }}
            </el-tag>
            <el-tag type="info" size="small" class="response-time">
              <el-icon><Timer /></el-icon>
              {{ getExecutionTime(debugResponse) }}ms
            </el-tag>
            <el-tag type="info" size="small" class="content-length" v-if="getContentLength(debugResponse)">
              <el-icon><Document /></el-icon>
              {{ getContentLength(debugResponse) }}B
            </el-tag>
            <el-button size="small" type="info" @click="copyResponse" style="margin-left: 8px;">
              <el-icon><DocumentCopy /></el-icon>
              复制
            </el-button>
            <el-button size="small" type="primary" @click="saveToApiLibrary" style="margin-left: 8px;">
              <el-icon><Plus /></el-icon>
              保存到接口库
            </el-button>
          </div>
        </div>
      </template>
      <el-tabs v-model="debugResTab" class="response-tabs">
        <el-tab-pane label="响应体" name="body">
          <div class="response-body">
            <pre class="debug-response-body">{{ formattedResponse }}</pre>
          </div>
        </el-tab-pane>
        <el-tab-pane label="响应头" name="headers">
          <div class="response-body">
            <pre class="debug-response-body">{{ JSON.stringify(debugResponse.headers, null, 2) }}</pre>
          </div>
        </el-tab-pane>
        <el-tab-pane label="请求详情" name="request">
          <div class="response-body">
            <pre class="debug-response-body">{{ JSON.stringify(debugRequestDetails, null, 2) }}</pre>
          </div>
        </el-tab-pane>
      </el-tabs>
      <div v-if="debugResponse.error" class="error-message">
        <el-alert :title="debugResponse.error" type="error" show-icon :closable="false" />
      </div>
    </el-card>

    <el-drawer
      v-model="showHistory"
      title="📋 请求历史"
      size="600px"
      direction="rtl"
    >
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
                  <el-icon><Right /></el-icon>
                  再次请求
                </el-button>
                <el-button size="small" @click="loadHistoryItem(item)">
                  <el-icon><Edit /></el-icon>
                  加载
                </el-button>
                <el-button size="small" type="danger" @click="debugHistory.splice(index, 1)">
                  <el-icon><Delete /></el-icon>
                  删除
                </el-button>
              </div>
            </div>
          </el-timeline-item>
        </el-timeline>
        <el-button type="danger" size="small" @click="clearHistory" v-if="debugHistory.length > 0" style="margin-top: 16px;">
          <el-icon><Delete /></el-icon>
          清空历史
        </el-button>
      </div>
    </el-drawer>

    <el-dialog
      v-model="showVariableDialog"
      title="插入变量"
      width="500px"
      append-to-body
      destroy-on-close
    >
      <div class="variable-dialog">
        <el-input v-model="variableSearch" placeholder="搜索变量" style="margin-bottom: 16px;">
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
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
        <span class="dialog-footer">
          <el-button @click="showVariableDialog = false">取消</el-button>
        </span>
      </template>
    </el-dialog>

    <el-dialog
      v-model="saveToApiLibraryDialog"
      title="保存到接口库"
      width="500px"
      append-to-body
      destroy-on-close
    >
      <el-form :model="apiLibraryForm" label-width="80px">
        <el-form-item label="接口名称" required>
          <el-input v-model="apiLibraryForm.name" placeholder="请输入接口名称" />
        </el-form-item>
        <el-form-item label="所属分组" required>
          <el-select v-model="apiLibraryForm.group_id" placeholder="请选择分组">
            <el-option
              v-for="group in apiGroups"
              :key="group.id"
              :label="group.name"
              :value="group.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="接口描述">
          <el-input
            v-model="apiLibraryForm.description"
            type="textarea"
            placeholder="请输入接口描述"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="saveToApiLibraryDialog = false">取消</el-button>
          <el-button type="primary" @click="confirmSaveToApiLibrary">确定</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Right, Delete, Clock, Timer, MagicStick, DocumentCopy, DataAnalysis, Document, Plus, Search, Edit } from '@element-plus/icons-vue'
import autoTestRequest from '@/utils/autoTestRequest'

const props = defineProps({
  environmentList: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['case-saved'])

const debugEnvId = ref(null)
const debugForm = ref({
  method: 'GET',
  url: '',
  headers: [],
  body: '',
  formData: [],
  bodyType: 'json',
  timeout: 5,
  params: []
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
const apiLibraryForm = ref({
  name: '',
  group_id: '',
  description: ''
})
const apiGroups = ref([])

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
    const payload =
      debugResponse.value.response_content ??
      debugResponse.value.data ??
      debugResponse.value.body
    if (typeof payload === 'object' && payload !== null) {
      return JSON.stringify(payload, null, 2)
    } else if (payload) {
      return payload
    }
    return JSON.stringify(debugResponse.value, null, 2)
  } catch (error) {
    return String(debugResponse.value)
  }
})

const replaceVariables = (template, vars) => {
  if (!template || typeof template !== 'string') {
    return template
  }
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
  if (!debugForm.value.url.trim()) {
    ElMessage.warning('请输入请求URL')
    return
  }
  debugLoading.value = true
  debugResponse.value = null
  try {
    const varsArray = variables.value || []

    const headersObj = {}
    debugForm.value.headers.forEach(item => {
      if (item.key) {
        headersObj[replaceVariables(item.key, varsArray)] = replaceVariables(item.value, varsArray)
      }
    })

    const paramsObj = {}
    debugForm.value.params.forEach(item => {
      if (item.key) {
        paramsObj[replaceVariables(item.key, varsArray)] = replaceVariables(item.value, varsArray)
      }
    })

    const payload = {
      method: debugForm.value.method,
      url: replaceVariables(debugForm.value.url, varsArray),
      headers: headersObj,
      params: paramsObj,
      body: debugForm.value.bodyType === 'form-data'
        ? Object.fromEntries(
            (debugForm.value.formData || [])
              .filter(item => item.key)
              .map(item => [replaceVariables(item.key, varsArray), replaceVariables(item.value, varsArray)])
          )
        : replaceVariables(debugForm.value.body || '', varsArray),
      body_type: debugForm.value.bodyType
    }
    if (debugEnvId.value) {
      payload.env_id = debugEnvId.value
    }

    debugRequestDetails.value = {
      method: debugForm.value.method,
      url: replaceVariables(debugForm.value.url, varsArray),
      headers: headersObj,
      params: paramsObj,
      body: debugForm.value.bodyType === 'form-data'
        ? Object.fromEntries(
            (debugForm.value.formData || [])
              .filter(item => item.key)
              .map(item => [replaceVariables(item.key, varsArray), replaceVariables(item.value, varsArray)])
          )
        : replaceVariables(debugForm.value.body || '', varsArray),
      bodyType: debugForm.value.bodyType,
      timeout: debugForm.value.timeout
    }

    const res = await autoTestRequest.post('/auto-test/send', payload)
    debugResponse.value = res
    if (debugResponse.value.error && !debugResponse.value.status_code) {
      ElMessage.error(debugResponse.value.error)
    }
  } catch (err) {
    debugResponse.value = {
      error: err.response?.data?.detail || err.response?.data?.error || err.message || '请求发送失败',
      status_code: typeof err.response?.status === 'number' ? err.response.status : null,
      success: false
    }
    ElMessage.error('请求发送失败')
  } finally {
    debugLoading.value = false
    addToHistory()
  }
}

const addToHistory = () => {
  const varsArray = variables.value || []
  const headersObj = {}
  debugForm.value.headers.forEach(item => {
    if (item.key) {
      headersObj[replaceVariables(item.key, varsArray)] = replaceVariables(item.value, varsArray)
    }
  })

  const paramsObj = {}
  debugForm.value.params.forEach(item => {
    if (item.key) {
      paramsObj[replaceVariables(item.key, varsArray)] = replaceVariables(item.value, varsArray)
    }
  })

  const historyItem = {
    method: debugForm.value.method,
    url: replaceVariables(debugForm.value.url, varsArray),
    headers: headersObj,
    params: paramsObj,
    body: replaceVariables(debugForm.value.body || '', varsArray),
    body_type: debugForm.value.bodyType,
    form_data: debugForm.value.bodyType === 'form-data'
      ? [...(debugForm.value.formData || [])]
      : [],
    status_code: typeof debugResponse.value?.status_code === 'number'
      ? debugResponse.value.status_code
      : null,
    error: debugResponse.value?.error || '',
    timestamp: new Date().toLocaleString('zh-CN'),
    env_id: debugEnvId.value
  }
  debugHistory.value.unshift(historyItem)
  if (debugHistory.value.length > 50) {
    debugHistory.value = debugHistory.value.slice(0, 50)
  }
}

const resendHistoryRequest = async (item) => {
  debugForm.value.method = item.method
  debugForm.value.url = item.url
  const headersArray = []
  if (item.headers && typeof item.headers === 'object') {
    for (const [key, value] of Object.entries(item.headers)) {
      headersArray.push({ key, value })
    }
  }
  debugForm.value.headers = headersArray
  const paramsArray = []
  if (item.params && typeof item.params === 'object') {
    for (const [key, value] of Object.entries(item.params)) {
      paramsArray.push({ key, value })
    }
  }
  debugForm.value.params = paramsArray
  debugForm.value.body = item.body
  debugForm.value.bodyType = item.body_type
  debugForm.value.formData = Array.isArray(item.form_data)
    ? item.form_data.map(row => ({ key: row.key || '', value: row.value || '' }))
    : []
  debugEnvId.value = item.env_id
  showHistory.value = false
  await sendDebugRequest()
}

const loadHistoryItem = (item) => {
  debugForm.value.method = item.method
  debugForm.value.url = item.url
  const headersArray = []
  if (item.headers && typeof item.headers === 'object') {
    for (const [key, value] of Object.entries(item.headers)) {
      headersArray.push({ key, value })
    }
  }
  debugForm.value.headers = headersArray
  const paramsArray = []
  if (item.params && typeof item.params === 'object') {
    for (const [key, value] of Object.entries(item.params)) {
      paramsArray.push({ key, value })
    }
  }
  debugForm.value.params = paramsArray
  debugForm.value.body = item.body
  debugForm.value.bodyType = item.body_type
  debugForm.value.formData = Array.isArray(item.form_data)
    ? item.form_data.map(row => ({ key: row.key || '', value: row.value || '' }))
    : []
  debugEnvId.value = item.env_id
  showHistory.value = false
  ElMessage.success('已加载历史请求参数')
}

const insertVariable = (target) => {
  variableTarget.value = target
  showVariableDialog.value = true
  loadVariables()
}

const insertVariableValue = (variableValue) => {
  if (variableTarget.value && debugForm.value[variableTarget.value] !== undefined) {
    const currentValue = debugForm.value[variableTarget.value] || ''
    const newValue = currentValue + `{{${variableValue}}}`
    debugForm.value = {
      ...debugForm.value,
      [variableTarget.value]: newValue
    }
  }
  showVariableDialog.value = false
}

const saveToApiLibrary = async () => {
  try {
    const isDebugSuccessful = debugResponse.value &&
                              (debugResponse.value.status_code >= 200 && debugResponse.value.status_code < 300) &&
                              debugResponse.value.success !== false

    if (!isDebugSuccessful) {
      try {
        await ElMessageBox.confirm(
          '该接口当前未调试通过，直接保存可能导致用例执行失败。是否确认强制保存？',
          '确认保存',
          {
            confirmButtonText: '强制保存',
            cancelButtonText: '重新调试',
            type: 'warning'
          }
        )
      } catch {
        return
      }
    }

    await loadApiGroups()
    const url = debugForm.value.url
    const urlParts = url.split('/')
    const lastPart = urlParts[urlParts.length - 1]
    const apiName = lastPart || url
    apiLibraryForm.value.name = `${debugForm.value.method} ${apiName}`
    saveToApiLibraryDialog.value = true
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('加载接口分组失败')
    }
  }
}

const loadApiGroups = async () => {
  try {
    const res = await autoTestRequest.get('/auto-test/groups')
    apiGroups.value = res || []
  } catch (error) {
    throw error
  }
}

const confirmSaveToApiLibrary = async () => {
  if (!apiLibraryForm.value.name) {
    ElMessage.warning('请输入接口名称')
    return
  }
  if (!apiLibraryForm.value.group_id) {
    ElMessage.warning('请选择所属分组')
    return
  }

  try {
    let headers = {}
    if (Array.isArray(debugForm.value.headers)) {
      debugForm.value.headers.forEach(item => {
        if (item.key) {
          headers[item.key] = item.value
        }
      })
    } else if (debugForm.value.headers && typeof debugForm.value.headers === 'object') {
      headers = debugForm.value.headers
    }

    let params = {}
    if (Array.isArray(debugForm.value.params)) {
      debugForm.value.params.forEach(item => {
        if (item.key) {
          params[item.key] = item.value
        }
      })
    } else if (debugForm.value.params && typeof debugForm.value.params === 'object') {
      params = debugForm.value.params
    }

    let requestPayload = null
    const rawBodyType = debugForm.value.bodyType || 'none'
    const bodyTypeMapping = { 'json': 'raw', 'raw': 'raw', 'form-data': 'form-data', 'none': 'none', 'text': 'raw', 'xml': 'raw', 'html': 'raw' }
    const bodyType = bodyTypeMapping[rawBodyType] || rawBodyType
    const bodyContent = debugForm.value.body || ''

    if (bodyType === 'raw' || rawBodyType === 'json') {
      if (bodyContent && bodyContent.trim()) {
        try {
          requestPayload = JSON.parse(bodyContent)
        } catch (e) {
          ElMessage.error('请求体 JSON 格式错误，请检查！')
          return
        }
      } else {
        requestPayload = {}
      }
    } else if (bodyType === 'form-data') {
      requestPayload = {}
      if (Array.isArray(debugForm.value.formData)) {
        debugForm.value.formData.forEach(item => {
          if (item.key) {
            requestPayload[item.key] = item.value
          }
        })
      }
    }

    let contentType = 'application/json'
    if (rawBodyType === 'xml') contentType = 'application/xml'
    else if (rawBodyType === 'html') contentType = 'text/html'
    else if (rawBodyType === 'text') contentType = 'text/plain'
    else if (rawBodyType === 'form-data') contentType = 'multipart/form-data'
    else if (rawBodyType === 'json') contentType = 'application/json'

    const payload = {
      name: apiLibraryForm.value.name,
      group_id: apiLibraryForm.value.group_id,
      method: debugForm.value.method,
      url: debugForm.value.url,
      headers: headers,
      params: params,
      body_type: bodyType,
      content_type: contentType,
      payload: requestPayload,
      description: apiLibraryForm.value.description
    }

    await autoTestRequest.post('/auto-test/cases/', payload)
    ElMessage.success('保存到接口库成功')
    saveToApiLibraryDialog.value = false

    emit('case-saved')
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '保存到接口库失败')
  }
}

const loadVariables = async () => {
  try {
    const res = await autoTestRequest.get('/auto-test/global-variables')
    const globalVariables = Array.isArray(res) ? res : []

    const dynamicVariables = [
      { id: 'dynamic-1', name: '$timestamp', value: '', description: '当前时间戳', is_encrypted: false },
      { id: 'dynamic-2', name: '$random_int', value: '', description: '随机整数', is_encrypted: false },
      { id: 'dynamic-3', name: '$random_string', value: '', description: '随机字符串', is_encrypted: false },
      { id: 'dynamic-4', name: '$uuid', value: '', description: 'UUID', is_encrypted: false },
      { id: 'dynamic-5', name: '$datetime', value: '', description: '当前日期时间', is_encrypted: false }
    ]

    variables.value = [...globalVariables, ...dynamicVariables]
    filteredVariables.value = variables.value
  } catch (error) {
    variables.value = [
      { id: 'dynamic-1', name: '$timestamp', value: '', description: '当前时间戳', is_encrypted: false },
      { id: 'dynamic-2', name: '$random_int', value: '', description: '随机整数', is_encrypted: false },
      { id: 'dynamic-3', name: '$random_string', value: '', description: '随机字符串', is_encrypted: false },
      { id: 'dynamic-4', name: '$uuid', value: '', description: 'UUID', is_encrypted: false },
      { id: 'dynamic-5', name: '$datetime', value: '', description: '当前日期时间', is_encrypted: false }
    ]
    filteredVariables.value = variables.value
  }
}

const clearDebugForm = () => {
  debugForm.value = {
    method: 'GET',
    url: '',
    headers: [],
    body: '',
    formData: [],
    bodyType: 'json',
    timeout: 5,
    params: []
  }
  debugResponse.value = null
}

const clearHistory = () => {
  debugHistory.value = []
}

const copyResponse = () => {
  if (debugResponse.value) {
    const responseText = JSON.stringify(debugResponse.value, null, 2)
    navigator.clipboard.writeText(responseText)
      .then(() => {
        ElMessage.success('响应已复制到剪贴板')
      })
      .catch(err => {
        ElMessage.error('复制失败')
      })
  }
}

const formatJson = (field) => {
  try {
    const value = debugForm.value[field]
    if (value) {
      const parsed = JSON.parse(value)
      const formatted = JSON.stringify(parsed, null, 2)
      debugForm.value[field] = formatted
      ElMessage.success('JSON 格式化成功')
    }
  } catch (error) {
    ElMessage.error('JSON 格式错误')
  }
}



watch(() => variableSearch.value, (search) => {
  if (!search) {
    filteredVariables.value = variables.value
  } else {
    filteredVariables.value = variables.value.filter(v =>
      v.name.toLowerCase().includes(search.toLowerCase()) ||
      (v.description && v.description.toLowerCase().includes(search.toLowerCase()))
    )
  }
})
</script>

<style scoped>
.debug-container {
  width: 100%;
  margin: 0;
  padding: 16px;
}

.debug-card {
  border-radius: 12px !important;
  border: 1px solid var(--tm-border-light) !important;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08) !important;
  backdrop-filter: blur(10px) !important;
  -webkit-backdrop-filter: blur(10px) !important;
}

.debug-card :deep(.el-card__header) {
  padding: 16px 24px;
  border-bottom: 1px solid var(--tm-border-light) !important;
  background: var(--tm-bg-card) !important;
}

.debug-response-body {
  background: var(--tm-bg-card);
  color: var(--tm-text-primary);
  padding: 20px;
  border-radius: 10px;
  font-size: 14px;
  line-height: 1.6;
  max-height: 500px;
  overflow: auto;
  white-space: pre-wrap;
  word-break: break-all;
  margin: 0;
  border: 1px solid rgba(var(--tm-color-primary-rgb), 0.3);
  box-shadow: inset 0 2px 8px rgba(0, 0, 0, 0.08);
}

.debug-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  background: var(--tm-bg-card);
  border-radius: 12px;
  margin-bottom: 20px;
  border: 1px solid var(--tm-border-light);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
}

.debug-title {
  font-size: 20px;
  font-weight: 700;
  color: var(--tm-text-primary);
  margin: 0;
  text-shadow: 0 0 10px rgba(var(--tm-color-primary-rgb), 0.5);
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.request-line {
  display: flex;
  gap: 12px;
  align-items: center;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.method-select {
  min-width: 120px;
  flex-shrink: 0;
}

.url-input {
  flex: 1;
  min-width: 300px;
  position: relative;
}

.url-input :deep(.el-input__wrapper) {
  border-radius: 8px !important;
  overflow: hidden;
}

.url-input :deep(.el-input__append) {
  padding: 0 12px;
  background: rgba(var(--tm-color-primary-rgb), 0.1);
  border-left: 1px solid var(--tm-border-light);
}

.url-input :deep(.el-input__append .el-button) {
  margin: 0;
  border: none;
  background: transparent;
  color: var(--tm-color-primary);
  transition: all 0.3s ease;
}

.url-input :deep(.el-input__append .el-button:hover) {
  color: var(--tm-color-primary);
  transform: scale(1.05);
}

.request-actions {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-shrink: 0;
  padding: 0 4px;
}

.send-button {
  min-width: 140px;
  font-weight: 600;
  letter-spacing: 1px;
  padding: 12px 20px;
}

.request-actions .el-input-number {
  width: 120px !important;
  border-radius: 8px;
  overflow: hidden;
}

.request-actions .el-input-number :deep(.el-input__wrapper) {
  border-radius: 8px;
}

.request-actions .el-input-number :deep(.el-input-number__decrease),
.request-actions .el-input-number :deep(.el-input-number__increase) {
  background: rgba(var(--tm-color-primary-rgb), 0.1);
  border-left: 1px solid var(--tm-border-light);
  color: var(--tm-color-primary);
  transition: all 0.3s ease;
}

.request-actions .el-input-number :deep(.el-input-number__decrease:hover),
.request-actions .el-input-number :deep(.el-input-number__increase:hover) {
  background: rgba(var(--tm-color-primary-rgb), 0.2);
  color: var(--tm-color-primary);
}

.response-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.response-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--tm-text-primary);
  margin: 0;
  text-shadow: 0 0 5px rgba(var(--tm-color-primary-rgb), 0.3);
}

.response-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.status-code {
  font-weight: 600;
  padding: 4px 12px;
  border-radius: 12px;
}

.response-time,
.content-length {
  font-size: 12px;
  padding: 4px 10px;
  border-radius: 8px;
  background: var(--tm-bg-card);
  border: 1px solid var(--tm-border-light);
}

.history-container {
  padding: 20px;
  max-height: 70vh;
  overflow: auto;
  background: var(--tm-bg-page);
}

.history-item {
  background: var(--tm-bg-card);
  border: 1px solid var(--tm-border-light);
  border-radius: 10px;
  padding: 16px;
  margin-bottom: 12px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.history-item:hover {
  border-color: var(--tm-color-primary);
  box-shadow: var(--tm-shadow-base);
  transform: translateY(-1px);
}

.history-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}

.history-method {
  font-weight: 600;
  font-size: 12px;
  padding: 4px 8px;
  border-radius: 6px;
  background: rgba(var(--tm-color-primary-rgb), 0.2);
  color: var(--tm-color-primary);
  border: 1px solid rgba(var(--tm-color-primary-rgb), 0.4);
}

.history-url {
  flex: 1;
  font-size: 14px;
  color: var(--tm-text-primary);
  word-break: break-all;
}

.history-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

.variable-dialog {
  padding: 20px;
}

.variable-list {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 20px;
  max-height: 400px;
  overflow-y: auto;
}

.variable-tag {
  padding: 8px 16px;
  border-radius: 20px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border: 1px solid var(--tm-border-light);
  background: var(--tm-bg-card);
}

.variable-tag:hover {
  border-color: var(--tm-color-primary);
  box-shadow: 0 0 15px rgba(var(--tm-color-primary-rgb), 0.3);
  transform: translateY(-1px);
}

.var-value {
  font-size: 12px;
  opacity: 0.7;
  margin-left: 8px;
}

.error-message {
  margin-bottom: 20px;
}

@media (max-width: 768px) {
  .debug-container {
    padding: 16px;
  }

  .request-line {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }

  .method-select,
  .url-input,
  .request-actions {
    width: 100%;
    min-width: unset;
  }

  .request-actions {
    justify-content: space-between;
  }

  .send-button {
    flex: 1;
    margin-left: 12px;
  }

  .toolbar-right {
    flex-wrap: wrap;
    gap: 8px;
  }

  .response-meta {
    flex-wrap: wrap;
    gap: 8px;
  }

  .history-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }

  .history-url {
    width: 100%;
  }

  .history-actions {
    width: 100%;
    justify-content: flex-start;
  }
}

@media (min-width: 769px) and (max-width: 1024px) {
  .debug-container {
    max-width: 900px;
    padding: 20px;
  }

  .request-line {
    flex-wrap: wrap;
  }

  .url-input {
    flex: 1;
    min-width: 250px;
  }
}

@media (min-width: 1200px) {
  .debug-container {
    max-width: 1400px;
  }
}
</style>
