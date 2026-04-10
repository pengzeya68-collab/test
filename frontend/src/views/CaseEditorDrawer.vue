<template>
  <el-drawer
    :model-value="modelValue"
    :title="isEdit ? '编辑用例' : '新建用例'"
    direction="rtl"
    size="75%"
    :before-close="handleClose"
  >
    <div class="drawer-content">
      <!-- 顶部：Method + Name + URL -->
      <div class="drawer-header">
        <div class="top-row">
          <el-select v-model="caseForm.method" style="width: 120px;">
            <el-option label="GET" value="GET" />
            <el-option label="POST" value="POST" />
            <el-option label="PUT" value="PUT" />
            <el-option label="DELETE" value="DELETE" />
            <el-option label="PATCH" value="PATCH" />
            <el-option label="HEAD" value="HEAD" />
            <el-option label="OPTIONS" value="OPTIONS" />
          </el-select>
          <el-input
            v-model="caseForm.name"
            placeholder="用例名称"
            style="width: 200px; margin-left: 10px;"
          />
          <el-autocomplete
            v-model="caseForm.url"
            :fetch-suggestions="querySearchVars"
            placeholder="输入请求 URL，例如：{{base_url}}/api/login"
            style="flex: 1; margin-left: 10px;"
            :trigger-on-focus="false"
            @select="handleSelectVar($event, 'url')"
            @input="handleUrlInput"
          >
            <template #default="{ item }">
              <div class="var-suggestion">
                <span class="var-name">&#123;&#123; {{ item.value }} &#125;&#125;</span>
                <span class="var-val">{{ item.actualValue }}</span>
              </div>
            </template>
          </el-autocomplete>
        </div>
      </div>

      <!-- 描述 -->
      <div class="description-bar">
        <el-input
          v-model="caseForm.description"
          type="textarea"
          :rows="2"
          placeholder="用例描述（可选）"
        />
      </div>

      <!-- Tabs -->
      <el-tabs v-model="activeTab" class="case-tabs">
        <!-- Headers -->
        <el-tab-pane label="Headers" name="headers">
          <div class="tab-content">
            <div class="table-toolbar">
              <span class="toolbar-title">请求头</span>
              <el-button size="small" @click="addHeader">
                <el-icon><Plus /></el-icon>
                添加
              </el-button>
            </div>
            <el-table :data="caseForm.headers" border size="small">
              <el-table-column label="Key" min-width="150">
                <template #default="{ row }">
                  <el-input v-model="row.key" placeholder="Header key" />
                </template>
              </el-table-column>
              <el-table-column label="Value" min-width="200">
                <template #default="{ row }">
                  <el-autocomplete
                    v-model="row.value"
                    :fetch-suggestions="querySearchVars"
                    placeholder="Header value"
                    :trigger-on-focus="false"
                    @select="handleSelectVar($event, row, 'value')"
                    @input="handleTableInput(row, 'value', $event)"
                    style="width: 100%"
                  >
                    <template #default="{ item }">
                      <div class="var-suggestion">
                        <span class="var-name">&#123;&#123; {{ item.value }} &#125;&#125;</span>
                        <span class="var-val">{{ item.actualValue }}</span>
                      </div>
                    </template>
                  </el-autocomplete>
                </template>
              </el-table-column>
              <el-table-column label="描述" min-width="150">
                <template #default="{ row }">
                  <el-input v-model="row.description" placeholder="描述（可选）" />
                </template>
              </el-table-column>
              <el-table-column label="操作" width="60" align="center">
                <template #default="{ row, $index }">
                  <el-button type="danger" size="small" text @click="removeHeader($index)">
                    <el-icon><Delete /></el-icon>
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-tab-pane>

        <!-- Body -->
        <el-tab-pane label="Body" name="body">
          <div class="tab-content">
            <div class="body-type-selector">
              <el-radio-group v-model="caseForm.bodyType">
                <el-radio value="none" label="none">none</el-radio>
                <el-radio value="raw" label="raw">raw</el-radio>
                <el-radio value="form-data" label="form-data">form-data</el-radio>
              </el-radio-group>
            </div>

            <!-- Raw Body -->
            <div v-if="caseForm.bodyType === 'raw'" class="raw-editor">
              <div class="content-type-selector">
                <el-select v-model="caseForm.contentType" style="width: 150px">
                  <el-option label="JSON" value="application/json" />
                  <el-option label="XML" value="application/xml" />
                  <el-option label="Text" value="text/plain" />
                  <el-option label="HTML" value="text/html" />
                </el-select>
              </div>
              <JsonEditor
                v-model="caseForm.payload"
                :content-type="caseForm.contentType"
              />
            </div>

            <!-- Form Data -->
            <div v-if="caseForm.bodyType === 'form-data'" class="form-data-editor">
              <el-table :data="caseForm.formData" border size="small">
                <el-table-column label="Key" min-width="150">
                  <template #default="{ row }">
                    <el-input v-model="row.key" placeholder="参数名" />
                  </template>
                </el-table-column>
                <el-table-column label="Value" min-width="200">
                  <template #default="{ row }">
                    <el-autocomplete
                      v-model="row.value"
                      :fetch-suggestions="querySearchVars"
                      placeholder="参数值"
                      :trigger-on-focus="false"
                      @select="handleSelectVar($event, row, 'value')"
                      @input="handleTableInput(row, 'value', $event)"
                      style="width: 100%"
                    >
                      <template #default="{ item }">
                        <div class="var-suggestion">
                          <span class="var-name">&#123;&#123; {{ item.value }} &#125;&#125;</span>
                          <span class="var-val">{{ item.actualValue }}</span>
                        </div>
                      </template>
                    </el-autocomplete>
                  </template>
                </el-table-column>
                <el-table-column label="操作" width="60" align="center">
                  <template #default="{ row, $index }">
                    <el-button type="danger" size="small" text @click="removeFormData($index)">
                      <el-icon><Delete /></el-icon>
                    </el-button>
                  </template>
                </el-table-column>
              </el-table>
              <el-button size="small" style="margin-top: 12px" @click="addFormData">
                <el-icon><Plus /></el-icon>
                添加参数
              </el-button>
            </div>
          </div>
        </el-tab-pane>

        <!-- Extractors -->
        <el-tab-pane label="Extractors" name="extractors">
          <div class="tab-content">
            <div class="table-toolbar">
              <span class="toolbar-title">变量提取</span>
              <el-button size="small" @click="addExtractor">
                <el-icon><Plus /></el-icon>
                添加
              </el-button>
            </div>
            <el-table :data="caseForm.extractors" border size="small">
              <el-table-column label="变量名" min-width="120">
                <template #default="{ row }">
                  <el-input v-model="row.variableName" placeholder="变量名" />
                </template>
              </el-table-column>
              <el-table-column label="提取类型" width="130">
                <template #default="{ row }">
                  <el-select v-model="row.extractorType">
                    <el-option label="JSONPath" value="jsonpath" />
                    <el-option label="Regex" value="regex" />
                    <el-option label="CSS Selector" value="css" />
                  </el-select>
                </template>
              </el-table-column>
              <el-table-column label="表达式" min-width="200">
                <template #default="{ row }">
                  <el-input v-model="row.expression" placeholder="提取表达式" />
                </template>
              </el-table-column>
              <el-table-column label="默认值" min-width="120">
                <template #default="{ row }">
                  <el-input v-model="row.defaultValue" placeholder="默认值（可选）" />
                </template>
              </el-table-column>
              <el-table-column label="操作" width="60" align="center">
                <template #default="{ row, $index }">
                  <el-button type="danger" size="small" text @click="removeExtractor($index)">
                    <el-icon><Delete /></el-icon>
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-tab-pane>

        <!-- Assertions -->
        <el-tab-pane label="Assertions" name="assertions">
          <div class="tab-content">
            <div class="table-toolbar">
              <span class="toolbar-title">断言规则 (支持拖拽排序)</span>
              <el-button size="small" @click="addAssertion">
                <el-icon><Plus /></el-icon>
                添加断言
              </el-button>
            </div>
            <div class="assertions-hint">
              <el-alert type="info" :closable="false" show-icon>
                <template #title>
                  期望值支持变量替换，可使用 &#123;&#123;变量名&#125;&#125; 引用上下文变量（提取变量或数据驱动变量）
                </template>
              </el-alert>
            </div>
            <!-- 使用 el-table-draggable 实现拖拽 -->
            <ElTableDraggable>
              <el-table :data="caseForm.assertions" border size="small" style="margin-top: 16px;" row-key="id">
                <el-table-column width="50" align="center">
                  <template #default>
                    <el-icon style="cursor: move; color: #909399;"><Rank /></el-icon>
                  </template>
                </el-table-column>
                <el-table-column label="断言目标" min-width="140">
                  <template #default="{ row }">
                    <el-select v-model="row.target" style="width: 100%;">
                      <el-option label="状态码" value="status_code" />
                      <el-option label="JSON体" value="json_body" />
                      <el-option label="响应时间(ms)" value="response_time" />
                    </el-select>
                  </template>
                </el-table-column>
                <el-table-column label="JSONPath" min-width="200" v-if="showExpressionColumn">
                  <template #default="{ row }">
                    <el-input
                      v-if="row.target === 'json_body'"
                      v-model="row.expression"
                      placeholder="JSONPath 表达式，例如 $.data.code"
                    />
                  </template>
                </el-table-column>
                <el-table-column label="操作符" width="100">
                  <template #default="{ row }">
                    <el-select v-model="row.operator" style="width: 100%;">
                      <el-option label="等于" value="==" />
                      <el-option label="不等于" value="!=" />
                      <el-option label="包含" value="contains" />
                      <el-option label="小于" value="<" />
                      <el-option label="大于" value=">" />
                    </el-select>
                  </template>
                </el-table-column>
                <el-table-column label="期望值" min-width="180">
                  <template #default="{ row }">
                    <el-autocomplete
                      v-model="row.expected"
                      :fetch-suggestions="querySearchVars"
                      placeholder="期望值，支持 &#123;&#123;var&#125;&#125;"
                      :trigger-on-focus="false"
                      @select="handleSelectVar($event, row, 'expected')"
                      @input="handleTableInput(row, 'expected', $event)"
                      style="width: 100%"
                    >
                      <template #default="{ item }">
                        <div class="var-suggestion">
                          <span class="var-name">&#123;&#123; {{ item.value }} &#125;&#125;</span>
                          <span class="var-val">{{ item.actualValue }}</span>
                        </div>
                      </template>
                    </el-autocomplete>
                  </template>
                </el-table-column>
                <el-table-column label="操作" width="60" align="center">
                  <template #default="{ row, $index }">
                    <el-button type="danger" size="small" text @click="removeAssertion($index)">
                      <el-icon><Delete /></el-icon>
                    </el-button>
                  </template>
                </el-table-column>
              </el-table>
            </ElTableDraggable>
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>

    <!-- 悬浮按钮，用于打开变量字典 -->
    <div class="var-dictionary-btn" @click="showVarDrawer = true" title="打开变量字典">
      <el-icon><Reading /></el-icon>
    </div>

    <!-- 变量字典抽屉 (内部) -->
    <el-drawer
      v-model="showVarDrawer"
      title="环境变量字典"
      direction="rtl"
      size="300px"
      append-to-body
      :z-index="3000"
    >
      <div class="var-drawer-content">
        <el-input
          v-model="varSearchQuery"
          placeholder="搜索变量名..."
          prefix-icon="Search"
          clearable
          style="margin-bottom: 16px;"
        />

        <div v-if="filteredVars.length === 0" class="empty-vars">
          <el-empty description="未找到匹配的变量" :image-size="60" />
        </div>

        <div class="var-list" v-else>
          <div
            v-for="v in filteredVars"
            :key="v.value"
            class="var-item"
            @click="copyVarToClipboard(v.value)"
          >
            <div class="var-item-left">
              <div class="var-name-bold">&#123;&#123; {{ v.value }} &#125;&#125;</div>
              <div class="var-val-preview">{{ v.actualValue }}</div>
            </div>
            <el-icon class="copy-icon"><DocumentCopy /></el-icon>
          </div>
        </div>
      </div>
    </el-drawer>

    <!-- 底部按钮 -->
    <template #footer>
      <div class="drawer-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button type="info" @click="handleSave">仅保存</el-button>
        <el-button type="primary" @click="handleSaveAndRun">
          <el-icon><VideoPlay /></el-icon>
          保存并运行
        </el-button>
      </div>
    </template>
  </el-drawer>
</template>

<script setup>
import { ref, watch, toRaw, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, VideoPlay, Delete, Rank, Reading, Search, DocumentCopy } from '@element-plus/icons-vue'
import JsonEditor from './JsonEditor.vue'
import axios from 'axios'

const props = defineProps({
  modelValue: Boolean,
  caseData: Object,
  groupId: [Number, String],
  isEdit: Boolean
})

const emit = defineEmits(['update:modelValue', 'success', 'run'])

const activeTab = ref('headers')
const availableVariables = ref([]) // 用于存储当前所有可用变量

// 变量字典抽屉相关
const showVarDrawer = ref(false)
const varSearchQuery = ref('')

const autoTestRequest = axios.create({
  baseURL: '',
  timeout: 30000
})

// 添加请求拦截器，自动带上 token
autoTestRequest.interceptors.request.use(
  config => {
    const token = localStorage.getItem('admin_token') || localStorage.getItem('token');
    if (token && token !== 'undefined' && token !== 'null' && token !== '[object Object]') {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  error => {
    return Promise.reject(error);
  }
)

// 添加响应拦截器，统一返回 response.data
autoTestRequest.interceptors.response.use(
  response => response.data,
  error => Promise.reject(error)
)

// 记载环境变量字典（用于自动补全）
const loadVariables = async () => {
  try {
    const res = await autoTestRequest.get('/api/auto-test/environments')
    const envs = res.data || res || []
    const varMap = new Map()
    envs.forEach(env => {
      // 获取 base_url
      if (env.base_url) {
        varMap.set('base_url', { value: 'base_url', actualValue: env.base_url })
      }
      // 获取 variables
      if (env.variables) {
        Object.entries(env.variables).forEach(([k, v]) => {
          varMap.set(k, { value: k, actualValue: v })
        })
      }
    })

    // 如果后端没返回，为了演示效果，添加一些模拟变量
    if (varMap.size === 0) {
      varMap.set('base_url', { value: 'base_url', actualValue: 'http://api.example.com' })
      varMap.set('token', { value: 'token', actualValue: 'eyJhbGciOiJIUzI1...' })
      varMap.set('user_id', { value: 'user_id', actualValue: '10001' })
      varMap.set('current_date', { value: 'current_date', actualValue: '2023-10-25' })
      varMap.set('random_email', { value: 'random_email', actualValue: 'test_8df2@demo.com' })
    }

    availableVariables.value = Array.from(varMap.values())
  } catch (error) {
    console.error('加载环境变量失败:', error)
    // 降级：模拟变量
    availableVariables.value = [
      { value: 'base_url', actualValue: 'http://api.example.com' },
      { value: 'token', actualValue: 'eyJhbGciOiJIUzI1...' },
      { value: 'user_id', actualValue: '10001' },
      { value: 'current_date', actualValue: '2023-10-25' },
      { value: 'random_email', actualValue: 'test_8df2@demo.com' }
    ]
  }
}

onMounted(() => {
  loadVariables()
})

// === 变量字典抽屉逻辑 ===
const filteredVars = computed(() => {
  if (!varSearchQuery.value) return availableVariables.value
  const query = varSearchQuery.value.toLowerCase()
  return availableVariables.value.filter(v =>
    v.value.toLowerCase().includes(query) ||
    (v.actualValue && v.actualValue.toString().toLowerCase().includes(query))
  )
})

const copyVarToClipboard = async (varName) => {
  const textToCopy = `{{${varName}}}`
  try {
    await navigator.clipboard.writeText(textToCopy)
    ElMessage.success(`已复制 ${textToCopy} 到剪贴板`)
    showVarDrawer.value = false // 复制后自动收起抽屉
  } catch (err) {
    // 降级方案
    const textArea = document.createElement("textarea")
    textArea.value = textToCopy
    document.body.appendChild(textArea)
    textArea.focus()
    textArea.select()
    try {
      document.execCommand('copy')
      ElMessage.success(`已复制 ${textToCopy} 到剪贴板`)
      showVarDrawer.value = false
    } catch (err2) {
      ElMessage.error('复制失败，请手动输入')
    }
    document.body.removeChild(textArea)
  }
}

// 表单数据
const caseForm = ref({
  method: 'GET',
  name: '',
  url: '',
  description: '',
  headers: [],
  bodyType: 'none',
  contentType: 'application/json',
  payload: '',
  formData: [],
  extractors: [],
  assertions: []
})

// === 变量补全逻辑 ===
let currentInputPos = 0
let isTriggeringVars = false

const querySearchVars = (queryString, cb) => {
  // 如果输入包含 {{，则触发补全
  const lastIndex = queryString.lastIndexOf('{{')
  if (lastIndex !== -1) {
    // 提取 {{ 之后的字符串作为搜索词
    const searchKey = queryString.substring(lastIndex + 2).trim()
    // 如果还没闭合 }}
    if (!searchKey.includes('}')) {
      const results = searchKey
        ? availableVariables.value.filter(v => v.value.toLowerCase().includes(searchKey.toLowerCase()))
        : availableVariables.value
      cb(results)
      return
    }
  }
  cb([])
}

const handleSelectVar = (item, targetObj, targetProp) => {
  // 处理选中事件
  let currentVal = ''
  if (typeof targetObj === 'string') {
    // 处理 url
    currentVal = caseForm.value[targetObj] || ''
  } else {
    // 处理 row 里的属性
    currentVal = targetObj[targetProp] || ''
  }

  const lastIndex = currentVal.lastIndexOf('{{')
  if (lastIndex !== -1) {
    // 替换为 {{varName}}
    const newVal = currentVal.substring(0, lastIndex) + '{{' + item.value + '}}'
    if (typeof targetObj === 'string') {
      caseForm.value[targetObj] = newVal
    } else {
      targetObj[targetProp] = newVal
    }
  }
}

const handleUrlInput = (val) => {
  // 仅在输入 {{ 时可能有需要，实际 el-autocomplete 在 input 时自动处理
}

const handleTableInput = (row, prop, val) => {
  row[prop] = val
}
// ====================

// 初始化表单数据
const initFormData = (data) => {
  if (data) {
    // 编辑模式：从传入的完整数据初始化
    caseForm.value = {
      method: data.method || 'GET',
      name: data.name || '',
      url: data.url || '',
      description: data.description || '',
      headers: parseJson(data.headers) || [],
      bodyType: data.body_type || 'none',
      contentType: data.content_type || 'application/json',
      payload: parseJson(data.payload) || '',
      formData: parseJson(data.form_data) || [],
      extractors: parseJson(data.extractors) || [],
      assertions: parseJson(data.assertions ?? data.assert_rules, true) || []
    }
  } else {
    // 新建模式
    caseForm.value = {
      method: 'GET',
      name: '',
      url: '',
      description: '',
      headers: [],
      bodyType: 'none',
      contentType: 'application/json',
      payload: '',
      formData: [],
      extractors: [],
      assertions: []
    }
  }
}

// 🔥 抽屉打开时，如果是编辑模式，强制从后端获取完整数据
watch(() => props.modelValue, async (visible) => {
  if (visible) {
    loadVariables() // 每次打开重新加载一下变量
    if (props.isEdit && props.caseData?.id) {
      // 编辑模式：先获取完整用例详情
      try {
        const res = await autoTestRequest.get(`/api/auto-test/cases/${props.caseData.id}`)
        initFormData(res)
      } catch (e) {
        console.error('获取用例详情失败', e)
        // 降级：用列表数据初始化
        initFormData(props.caseData)
      }
    } else {
      // 新建模式
      initFormData(null)
    }
  }
})

// 🔧 通用 JSON 解析工具
const parseJson = (str, isAssertRules = false) => {
  if (!str) return []
  if (Array.isArray(str)) {
    // 自动为数据添加一个唯一 id 用于拖拽
    const processArray = (arr) => arr.map((item, index) => ({ ...item, id: item.id || `item_${Date.now()}_${index}` }))

    if (isAssertRules && str.length > 0) {
      return processArray(str.map(item => {
        if (item.target) return item
        const newItem = {
          target: item.field === 'body' ? 'json_body' : (item.field || 'status_code'),
          operator: mapOldOperator(item.operator),
          expected: item.expectedValue || '',
          expression: ''
        }
        return newItem
      }))
    }
    return processArray(str)
  }

  if (typeof str === 'object') {
    if (isAssertRules) {
      const assertions = []
      if (Array.isArray(str)) {
        return str.map((item, index) => {
          if (item.target) return { ...item, id: `ast_${Date.now()}_${index}` }
          return {
            id: `ast_${Date.now()}_${index}`,
            target: item.field === 'body' ? 'json_body' : (item.field || 'status_code'),
            operator: mapOldOperator(item.operator),
            expected: item.expectedValue || '',
            expression: ''
          }
        })
      }
      let idx = 0
      for (const [field, value] of Object.entries(str)) {
        const newItem = {
          id: `ast_${Date.now()}_${idx++}`,
          target: field === 'body' ? 'json_body' : field,
          operator: '==',
          expected: '',
          expression: ''
        }
        if (value && typeof value === 'object') {
          newItem.operator = mapOldOperator(value.operator || 'equals')
          newItem.expected = value.expectedValue || value.eq || ''
        } else {
          newItem.expected = String(value)
        }
        assertions.push(newItem)
      }
      return assertions
    }
    return str
  }

  try {
    const parsed = JSON.parse(str)
    if (isAssertRules && parsed && typeof parsed === 'object') {
      if (Array.isArray(parsed)) {
        return parsed.map((item, index) => {
          if (item.target) return { ...item, id: `ast_${Date.now()}_${index}` }
          return {
            id: `ast_${Date.now()}_${index}`,
            target: item.field === 'body' ? 'json_body' : (item.field || 'status_code'),
            operator: mapOldOperator(item.operator),
            expected: item.expectedValue || '',
            expression: ''
          }
        })
      } else {
        const assertions = []
        let idx = 0
        for (const [field, value] of Object.entries(parsed)) {
          const newItem = {
            id: `ast_${Date.now()}_${idx++}`,
            target: field === 'body' ? 'json_body' : field,
            operator: '==',
            expected: '',
            expression: ''
          }
          if (value && typeof value === 'object') {
            newItem.operator = mapOldOperator(value.operator || 'equals')
            newItem.expected = value.expectedValue || value.eq || ''
          } else {
            newItem.expected = String(value)
          }
          assertions.push(newItem)
        }
        return assertions
      }
    }
    if (Array.isArray(parsed)) {
        return parsed.map((item, index) => ({ ...item, id: item.id || `item_${Date.now()}_${index}` }))
    }
    return parsed
  } catch {
    return []
  }
}

// 映射旧操作符到新操作符
const mapOldOperator = (oldOp) => {
  const mapping = {
    'equals': '==',
    'not_equals': '!=',
    'contains': 'contains',
    'gt': '>',
    'lt': '<'
  }
  return mapping[oldOp] || oldOp || '=='
}

// 监听打开
watch(() => props.modelValue, (val) => {
  if (val) {
    initFormData()
  }
})

// Headers
const addHeader = () => {
  caseForm.value.headers.push({ key: '', value: '', description: '', id: `hdr_${Date.now()}` })
}

const removeHeader = (index) => {
  caseForm.value.headers.splice(index, 1)
}

// Form Data
const addFormData = () => {
  caseForm.value.formData.push({ key: '', value: '', id: `fd_${Date.now()}` })
}

const removeFormData = (index) => {
  caseForm.value.formData.splice(index, 1)
}

// Extractors
const addExtractor = () => {
  caseForm.value.extractors.push({
    id: `ext_${Date.now()}`,
    variableName: '',
    extractorType: 'jsonpath',
    expression: '',
    defaultValue: ''
  })
}

const removeExtractor = (index) => {
  caseForm.value.extractors.splice(index, 1)
}

// Assertions
const addAssertion = () => {
  caseForm.value.assertions.push({
    id: `ast_${Date.now()}`,
    target: 'status_code',
    operator: '==',
    expected: '200',
    expression: ''
  })
}

const removeAssertion = (index) => {
  caseForm.value.assertions.splice(index, 1)
}

// 检查是否需要显示表达式列（只要有一个断言目标是 json_body 就显示
const showExpressionColumn = computed(() => {
  return caseForm.value.assertions.some(a => a.target === 'json_body')
})

// 关闭
const handleClose = () => {
  emit('update:modelValue', false)
}

// 保存
const handleSave = async () => {
  console.log('--- [CaseEditorDrawer] 触发 handleSave 保存函数 ---')
  if (!caseForm.value.name) {
    ElMessage.warning('请输入用例名称')
    return
  }
  if (!caseForm.value.url) {
    ElMessage.warning('请输入请求 URL')
    return
  }
  // 🔥 防御修复：必须选择所属分组
  if (!props.groupId) {
    ElMessage.warning('请先从左侧分组树选择一个分组再保存')
    return
  }

  console.log('--- [CaseEditorDrawer] 开始构建 payload ---')
  try {
    // 🔥 强制深度拷贝，确保拿到响应式对象的真实原生数据
    const rawForm = JSON.parse(JSON.stringify(toRaw(caseForm.value)))

    // 🔥 防御性空数组检查，确保任何情况下都不会发送 undefined
    if (!rawForm.headers) rawForm.headers = []
    if (!rawForm.formData) rawForm.formData = []
    if (!rawForm.extractors) rawForm.extractors = []
    if (!rawForm.assertions) rawForm.assertions = []

    // 构建 headers 对象
    const headersObj = {}
    rawForm.headers.forEach(h => {
      if (h.key) headersObj[h.key] = h.value || ''
    })

    // 构建 payload
    let payloadData = null
    if (rawForm.bodyType === 'raw' && rawForm.payload) {
      // raw 模式，尝试解析 JSON
      try {
        payloadData = JSON.parse(rawForm.payload)
      } catch {
        payloadData = rawForm.payload
      }
    } else if (rawForm.bodyType === 'form-data') {
      // form-data 模式，转为对象
      payloadData = {}
      rawForm.formData.forEach(item => {
        if (item.key) payloadData[item.key] = item.value || ''
      })
    }

    // 构建提取规则 - 传递完整的 extractors 数组
    const extractorsList = rawForm.extractors
      .filter(e => e.variableName && e.expression)
      .map(e => ({
        variableName: e.variableName,
        extractorType: e.extractorType,
        expression: e.expression,
        defaultValue: e.defaultValue || ''
      }))

    // 构建断言规则 - 只保留有效的断言，新格式：[{"target": "status_code", "operator": "==", "expected": "200", "expression": ""}, ...]
    const assertRules = rawForm.assertions
      .filter(a => a.target && a.operator && a.expected !== '')
      .map(a => ({
        target: a.target,
        operator: a.operator,
        expected: a.expected,
        expression: a.expression || ''
      }))

    const payload = {
      group_id: props.groupId,
      method: rawForm.method,
      name: rawForm.name,
      url: rawForm.url,
      description: rawForm.description,
      body_type: rawForm.bodyType,
      content_type: rawForm.contentType,
      payload: payloadData,
      form_data: rawForm.formData,
      headers: rawForm.headers,
      extractors: extractorsList,
      assertions: assertRules
    }

    // 🔥 调试日志：打印准备发送给后端的真实 payload
    console.log('🔥 准备发送给后端的真实 Payload:', payload)

    if (props.isEdit) {
      await autoTestRequest.put(`/api/auto-test/cases/${props.caseData.id}`, payload)
      ElMessage.success('更新成功')
    } else {
      await autoTestRequest.post('/api/auto-test/cases', payload)
      ElMessage.success('创建成功')
    }

    emit('success')
    handleClose()
  } catch (error) {
    console.error('保存用例失败:', error)
    ElMessage.error(props.isEdit ? '更新失败' : '创建失败')
  }
}

// 保存并运行
const handleSaveAndRun = async () => {
  await handleSave()
  if (caseForm.value.name && caseForm.value.url) {
    // 🔥 确保传递真实数据，避免响应式问题
    const data = JSON.parse(JSON.stringify(toRaw(caseForm.value)))
    emit('run', { ...data, id: props.caseData?.id })
  }
}
</script>

<style scoped>
.drawer-content {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--tm-bg-page);
}

.drawer-header {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 20px;
  background: var(--tm-bg-card);
  border-bottom: 1px solid var(--tm-border-light);
  flex-shrink: 0;
}

.top-row {
  display: flex;
  gap: 10px;
  align-items: center;
  width: 100%;
}

.description-bar {
  padding: 12px 16px;
  background: var(--tm-bg-card);
  border-bottom: 1px solid var(--tm-border-light);
  flex-shrink: 0;
}

.case-tabs {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: var(--tm-bg-card);
}

.case-tabs :deep(.el-tabs__header) {
  padding: 0 20px;
  margin: 0;
  background: var(--tm-bg-card);
  border-bottom: 1px solid var(--tm-border-light);
}

.case-tabs :deep(.el-tabs__content) {
  flex: 1;
  overflow: auto;
}

.tab-content {
  padding: 20px;
}

.table-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.toolbar-title {
  font-weight: 600;
  font-size: 14px;
  color: var(--tm-text-primary);
}

.body-type-selector {
  margin-bottom: 16px;
}

.raw-editor {
  border: 1px solid var(--tm-border-color);
  border-radius: var(--tm-radius-small);
  overflow: hidden;
}

.content-type-selector {
  padding: 12px;
  border-bottom: 1px solid var(--tm-border-light);
  background: var(--tm-bg-page);
}

.form-data-editor {
  margin-top: 16px;
}

.drawer-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 20px;
  background: var(--tm-bg-card);
  border-top: 1px solid var(--tm-border-light);
  flex-shrink: 0;
}

.assertions-hint {
  margin-top: 12px;
}

/* 变量补全下拉框样式 */
.var-suggestion {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}
.var-name {
  color: var(--tm-color-primary);
  font-weight: 600;
}
.var-val {
  color: var(--tm-text-secondary);
  font-size: 12px;
  max-width: 150px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 悬浮变量字典按钮 */
.var-dictionary-btn {
  position: absolute;
  right: -20px;
  top: 50%;
  transform: translateY(-50%);
  background: var(--tm-color-primary);
  color: white;
  width: 40px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px 0 0 8px;
  cursor: pointer;
  box-shadow: -2px 0 8px rgba(0, 0, 0, 0.15);
  z-index: 2000;
  transition: all 0.3s ease;
  font-size: 20px;
}

.var-dictionary-btn:hover {
  right: 0;
  width: 50px;
  background: var(--tm-color-primary-dark);
}

/* 变量字典抽屉内容 */
.var-drawer-content {
  padding: 16px;
  display: flex;
  flex-direction: column;
  height: 100%;
}

.var-list {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.var-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: var(--tm-bg-card);
  border: 1px solid var(--tm-border-light);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.var-item:hover {
  border-color: var(--tm-color-primary);
  background: rgba(var(--tm-color-primary), 0.05);
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.var-item:hover .copy-icon {
  color: var(--tm-color-primary);
  opacity: 1;
}

.var-item-left {
  flex: 1;
  overflow: hidden;
}

.var-name-bold {
  font-family: monospace;
  font-weight: 600;
  color: var(--tm-color-primary);
  margin-bottom: 4px;
}

.var-val-preview {
  font-size: 12px;
  color: var(--tm-text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.copy-icon {
  font-size: 16px;
  color: var(--tm-text-regular);
  opacity: 0.6;
  transition: all 0.2s;
  margin-left: 8px;
}

.empty-vars {
  display: flex;
  justify-content: center;
  align-items: center;
  flex: 1;
}
</style>
