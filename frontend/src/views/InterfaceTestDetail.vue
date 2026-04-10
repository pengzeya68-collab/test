<template>
  <div class="interface-test-detail">
    <div class="container">
      <!-- 返回按钮 -->
      <div class="back-bar">
        <el-button link @click="goBack">
          <el-icon><ArrowLeft /></el-icon>
          返回用例列表
        </el-button>

        <el-button
          type="primary"
          :disabled="!canRerun"
          :loading="rerunning"
          @click="handleOneClickRerun"
        >
          <el-icon><RefreshRight /></el-icon>
          再次运行
        </el-button>
      </div>

      <!-- 基本信息 -->
      <el-card class="info-card" shadow="never">
        <el-form :model="formData" label-width="100px">
          <el-form-item label="用例名称" required>
            <el-input v-model="formData.name" placeholder="给你的接口测试起个名字" />
          </el-form-item>
          <el-form-item label="描述">
            <el-input 
              v-model="formData.description" 
              type="textarea" 
              :rows="2"
              placeholder="对这个接口测试的描述（可选）"
            />
          </el-form-item>
        </el-form>
      </el-card>

      <!-- 请求配置 -->
      <el-card class="request-card" shadow="never" header="请求配置">
        <el-row :gutter="16">
          <el-col :span="6">
            <el-form-item label="请求方法" label-width="80px">
              <el-select v-model="formData.method" style="width: 100%;">
                <el-option label="GET" value="GET" />
                <el-option label="POST" value="POST" />
                <el-option label="PUT" value="PUT" />
                <el-option label="DELETE" value="DELETE" />
                <el-option label="PATCH" value="PATCH" />
                <el-option label="HEAD" value="HEAD" />
                <el-option label="OPTIONS" value="OPTIONS" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="18">
            <el-form-item label="请求 URL" label-width="80px">
              <el-autocomplete
                v-model="formData.url"
                :fetch-suggestions="querySearchVars"
                placeholder="https://example.com/api/v1/xxx 或者 {{base_url}}/api/v1/xxx"
                style="width: 100%"
                clearable
                :trigger-on-focus="false"
                @select="handleSelectVar($event, 'url')"
              >
                <template #default="{ item }">
                  <div class="var-suggestion">
                    <span class="var-name">&#123;&#123; {{ item.value }} &#125;&#125;</span>
                    <span class="var-val">{{ item.actualValue }}</span>
                  </div>
                </template>
              </el-autocomplete>
            </el-form-item>
          </el-col>
        </el-row>

        <!-- 请求头 -->
        <div class="section-title">
          <span>请求头</span>
          <el-button link type="primary" size="small" @click="addHeader">
            <el-icon><Plus /></el-icon> 添加
          </el-button>
        </div>
        <div class="headers-list">
          <div class="header-item" v-for="(header, index) in headers" :key="index">
            <el-input 
              v-model="header.key" 
              placeholder="Key" 
              style="width: 200px; margin-right: 8px;"
            />
            <el-autocomplete
              v-model="header.value"
              :fetch-suggestions="querySearchVars"
              placeholder="Value"
              style="flex: 1; margin-right: 8px;"
              :trigger-on-focus="false"
              @select="handleSelectVar($event, header, 'value')"
            >
              <template #default="{ item }">
                <div class="var-suggestion">
                  <span class="var-name">&#123;&#123; {{ item.value }} &#125;&#125;</span>
                  <span class="var-val">{{ item.actualValue }}</span>
                </div>
              </template>
            </el-autocomplete>
            <el-button 
              type="danger" 
              icon="Delete" 
              circle 
              size="small"
              @click="removeHeader(index)"
            />
          </div>
        </div>

        <!-- 请求体 -->
        <div class="section-title">
          <span>请求体</span>
          <el-radio-group v-model="formData.body_type" size="small" style="margin-left: 20px;">
            <el-radio-button value="json">JSON</el-radio-button>
            <el-radio-button value="text">纯文本</el-radio-button>
            <el-radio-button value="form">表单数据</el-radio-button>
          </el-radio-group>
        </div>
        <el-input 
          v-model="formData.body" 
          type="textarea" 
          :rows="12"
          placeholder="在此输入请求体内容..."
          class="body-editor"
        />
      </el-card>

      <!-- 环境选择 -->
      <el-card class="env-card" shadow="never" header="环境变量">
        <div class="env-selector">
          <el-select
            v-model="selectedEnvId"
            placeholder="选择环境"
            clearable
            style="width: 250px; margin-right: 16px;"
            @change="onEnvChange"
          >
            <el-option
              v-for="env in environments"
              :key="env.id"
              :label="`${env.name} - ${env.base_url}`"
              :value="env.id"
            />
          </el-select>
          <el-button type="primary" link @click="openEnvManager" style="margin-left: 10px;"><el-icon><Setting /></el-icon> 环境管理</el-button>
        </div>
        <div v-if="selectedEnv" class="env-variables">
          <div class="env-base-url">
            <span class="label">基础URL：</span>
            <code>{{ selectedEnv.base_url }}</code>
          </div>
          <div class="var-list" v-if="Object.keys(selectedEnv.variables || {}).length > 0">
            <div class="var-item" v-for="(value, key) in selectedEnv.variables" :key="key">
              <span class="var-key">{{ key }}</span>
              <span class="var-value">{{ value }}</span>
            </div>
          </div>
          <div class="tip" v-if="Object.keys(selectedEnv.variables || {}).length === 0">
            暂无自定义变量，使用 <code v-text="'{{变量名}}'"></code> 语法在URL/请求头/请求体中引用变量
          </div>
        </div>
        <div v-else class="tip">
          不选择环境则使用默认变量，建议创建环境区分开发/测试/生产
        </div>
      </el-card>

      <!-- 操作按钮 -->
      <div class="action-bar">
        <el-checkbox v-model="formData.is_public">公开用例</el-checkbox>
        <div class="buttons">
          <el-button @click="saveCase" :loading="saving">
            <el-icon><Document /></el-icon>
            保存用例
          </el-button>
          <el-button
            type="primary"
            @click="sendRequest"
            :loading="sending"
          >
            <el-icon><VideoPlay /></el-icon>
            发送请求
          </el-button>
        </div>
      </div>

      <!-- 响应结果 -->
      <el-card 
        v-if="response !== null" 
        class="response-card" 
        shadow="never"
        header="响应结果"
      >
        <div class="response-info">
          <div class="info-item">
            <span class="label">状态码：</span>
            <el-tag :type="getStatusCodeType(response.status_code)">
              {{ response.status_code }}
            </el-tag>
          </div>
          <div class="info-item">
            <span class="label">耗时：</span>
            <el-tag type="info">{{ response.elapsed_ms }}ms</el-tag>
          </div>
          <div class="info-item">
            <span class="label">Content-Type：</span>
            <span class="value">{{ response.content_type || '-' }}</span>
          </div>
        </div>

        <div class="section-title" style="margin-top: 16px;">响应内容</div>
        <pre class="response-body">{{ response.response_content }}</pre>
      </el-card>

      <!-- 错误信息 -->
      <el-alert 
        v-if="error" 
        :title="error" 
        type="error" 
        show-icon
        class="error-alert"
      />
    </div>
  </div>

  <!-- 环境管理抽屉 -->
  <EnvironmentManager v-model:visible="envManagerVisible" @close="handleEnvManagerClose" />
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ArrowLeft, Plus, Document, VideoPlay, Setting, RefreshRight } from '@element-plus/icons-vue'
import EnvironmentManager from '@/components/EnvironmentManager.vue'
import request from '@/utils/request'
import { ElMessage } from 'element-plus'

const router = useRouter()
const route = useRoute()
const caseId = route.params.id

const loading = ref(false)
const saving = ref(false)
const sending = ref(false)
const rerunning = ref(false)
const error = ref(null)
const response = ref(null)
const envManagerVisible = ref(false)

// 环境变量
const environments = ref([])
const availableVariables = ref([])
const selectedEnvId = ref(null)
const selectedEnv = computed(() => {
  return environments.value.find(e => e.id === selectedEnvId.value) || null
})

const canRerun = computed(() => {
  return Boolean(caseId && caseId !== '0' && caseId !== 'new')
})

// 获取环境变量列表
const fetchEnvironments = async () => {
  try {
    const res = await request.get('/interface-test/environments')
    environments.value = res.data || res

    // 更新自动补全变量池
    updateAvailableVariables()

    // 选中默认环境
    if (!selectedEnvId.value) {
        const defaultEnv = environments.value.find(e => e.is_default)
        if (defaultEnv) {
        selectedEnvId.value = defaultEnv.id
        }
    }
  } catch (err) {
    console.error('获取环境列表失败:', err)
  }
}

// 更新自动补全的变量池
const updateAvailableVariables = () => {
  const varMap = new Map()
  const envToUse = selectedEnv.value || (environments.value.find(e => e.is_default)) || environments.value[0]

  if (envToUse) {
      if (envToUse.base_url) {
          varMap.set('base_url', { value: 'base_url', actualValue: envToUse.base_url })
      }
      if (envToUse.variables) {
          let vars = typeof envToUse.variables === 'string' ? JSON.parse(envToUse.variables) : envToUse.variables
          Object.entries(vars).forEach(([k, v]) => {
              varMap.set(k, { value: k, actualValue: String(v) })
          })
      }
  }

  // 也加入其他环境的变量供参考
  environments.value.forEach(env => {
      if (env.base_url && !varMap.has('base_url')) {
          varMap.set('base_url', { value: 'base_url', actualValue: env.base_url })
      }
      if (env.variables) {
          let vars = typeof env.variables === 'string' ? JSON.parse(env.variables) : env.variables
          Object.entries(vars).forEach(([k, v]) => {
              if (!varMap.has(k)) {
                  varMap.set(k, { value: k, actualValue: String(v) })
              }
          })
      }
  })

  availableVariables.value = Array.from(varMap.values())
}

// === 变量补全逻辑 ===
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
  let currentVal = ''
  if (typeof targetObj === 'string') {
    currentVal = formData[targetObj] || ''
  } else {
    currentVal = targetObj[targetProp] || ''
  }

  const lastIndex = currentVal.lastIndexOf('{{')
  if (lastIndex !== -1) {
    const newVal = currentVal.substring(0, lastIndex) + '{{' + item.value + '}}'
    if (typeof targetObj === 'string') {
      formData[targetObj] = newVal
    } else {
      targetObj[targetProp] = newVal
    }
  }
}
// ====================

// 环境切换
const onEnvChange = () => {
  updateAvailableVariables()
}

// 打开环境管理弹窗
const openEnvManager = () => {
  envManagerVisible.value = true
}

const handleEnvManagerClose = () => {
  envManagerVisible.value = false
  fetchEnvironments()
}

// 组装最终请求变量
const getCurrentVariables = () => {
  if (!selectedEnv.value) {
    return {}
  }
  return selectedEnv.value.variables || {}
}

// 表单数据
const formData = reactive({
  name: '',
  description: '',
  folder_id: null,
  url: '',
  method: 'GET',
  body: '',
  body_type: 'json',
  is_public: false
})

// 请求头数组
const headers = ref([
  { key: 'Content-Type', value: 'application/json' }
])

// 转换headers数组为JSON字符串
const headersToJson = () => {
  const obj = {}
  headers.value.forEach(h => {
    if (h.key && h.key.trim()) {
      obj[h.key.trim()] = h.value || ''
    }
  })
  return JSON.stringify(obj, null, 2)
}

// 从JSON解析到headers数组
const jsonToHeaders = (jsonStr) => {
  try {
    const obj = JSON.parse(jsonStr || '{}')
    const result = Object.entries(obj).map(([key, value]) => ({
      key,
      value: String(value)
    }))
    return result.length > 0 ? result : [{ key: '', value: '' }]
  } catch {
    return [{ key: '', value: '' }]
  }
}

const addHeader = () => {
  headers.value.push({ key: '', value: '' })
}

const removeHeader = (index) => {
  headers.value.splice(index, 1)
}

const getStatusCodeType = (code) => {
  if (code >= 200 && code < 300) return 'success'
  if (code >= 300 && code < 400) return 'info'
  if (code >= 400 && code < 500) return 'warning'
  if (code >= 500) return 'danger'
  return 'info'
}

const fetchCase = async () => {
  if (!caseId || caseId === '0' || caseId === 'new') return // 新建用例，不需要获取

  loading.value = true
  try {
    const res = await request.get(`/interface-test/cases/${caseId}`)
    const data = res.data || res
    formData.name = data.name
    formData.description = data.description || ''
    formData.folder_id = data.folder_id || null
    formData.url = data.url
    formData.method = data.method
    formData.body = data.body || ''
    formData.body_type = data.body_type || 'json'
    formData.is_public = data.is_public || false

    // 解析headers
    if (data.headers) {
      headers.value = jsonToHeaders(data.headers)
    }
  } catch (err) {
    console.error('获取用例失败:', err)
    ElMessage.error('获取用例失败')
  } finally {
    loading.value = false
  }
}

const saveCase = async () => {
  if (!formData.name.trim()) {
    ElMessage.warning('请输入用例名称')
    return
  }
  if (!formData.url.trim()) {
    ElMessage.warning('请输入请求URL')
    return
  }
  // 🔥 防御修复：必须选择所属分组
  if (!formData.folder_id) {
    ElMessage.warning('请先从左侧分组列表选择一个分组再保存')
    return
  }

  saving.value = true
  error.value = null
  
  try {
    const data = {
      ...formData,
      headers: headersToJson()
    }
    
    if (caseId === '0') {
      await request.post('/interface-test/cases', data)
      ElMessage.success('创建成功')
      router.push('/interface-test')
    } else {
      await request.put(`/interface-test/cases/${caseId}`, data)
      ElMessage.success('保存成功')
    }
  } catch (err) {
    console.error('保存失败:', err)
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

const sendRequest = async () => {
  if (!formData.url.trim()) {
    ElMessage.warning('请输入请求URL')
    return
  }

  sending.value = true
  error.value = null
  response.value = null

  try {
    const data = {
      url: formData.url,
      method: formData.method,
      headers: headersToJson(),
      body: formData.body,
      body_type: formData.body_type,
      variables: getCurrentVariables()
    }

    const res = await request.post('/interface-test/send', data)
    response.value = res.data || res
    ElMessage.success('请求完成')
  } catch (err) {
    console.error('请求失败:', err)
    if (err.response && err.response.data && err.response.data.error) {
      error.value = err.response.data.error
    } else {
      error.value = '请求发送失败，请检查URL和网络'
    }
  } finally {
    sending.value = false
  }
}

const handleOneClickRerun = async () => {
  if (!canRerun.value) {
    ElMessage.warning('请先保存用例后再运行')
    return
  }
  if (!selectedEnvId.value) {
    ElMessage.warning('请先选择环境')
    return
  }
  if (sending.value || rerunning.value) return

  rerunning.value = true
  error.value = null
  response.value = null
  ElMessage.success('已触发再次运行，执行中...')

  try {
    await sendRequest()
  } finally {
    rerunning.value = false
  }
}

const goBack = () => {
  router.push('/interface-test')
}

onMounted(async () => {
  // 从 URL 参数读取 folder_id，如果是从某个分组点击新建，自动带上
  const folderIdFromRoute = route.query.folder_id
  if (folderIdFromRoute) {
    formData.folder_id = parseInt(folderIdFromRoute)
  }
  await fetchEnvironments()
  fetchCase()
})
</script>

<style scoped>
.interface-test-detail {
  padding: 20px 0 40px;
  min-height: calc(100vh - 60px);
  background-color: #f5f7fa;
}

.container {
  width: 100%;
  max-width: none;
  margin: 0 auto;
  padding: 0 20px;
  box-sizing: border-box;
}

.back-bar {
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.info-card {
  margin-bottom: 16px;
}

.request-card {
  margin-bottom: 16px;
}

.section-title {
  display: flex;
  align-items: center;
  font-weight: 600;
  margin-bottom: 12px;
}

.headers-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 16px;
}

.header-item {
  display: flex;
  align-items: center;
}

.body-editor {
  font-family: 'Courier New', monospace;
}

.action-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: white;
  border-radius: 8px;
  margin-bottom: 16px;
}

.action-bar .buttons {
  display: flex;
  gap: 12px;
}

.response-info {
  display: flex;
  gap: 24px;
  flex-wrap: wrap;
}

.response-info .info-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.response-info .label {
  color: #606266;
  font-size: 14px;
}

.response-info .value {
  color: #303133;
  font-size: 14px;
  word-break: break-all;
}

.response-body {
  background: #1e1e1e;
  color: #d4d4d4;
  padding: 16px;
  border-radius: 4px;
  max-height: 500px;
  overflow: auto;
  white-space: pre-wrap;
  word-break: break-all;
  margin: 0;
}

.response-card {
  margin-bottom: 16px;
}

.env-card {
  margin-bottom: 16px;
}

.env-selector {
  margin-bottom: 12px;
  display: flex;
  align-items: center;
}

.env-variables {
  margin-top: 12px;
}

.env-base-url {
  margin-bottom: 8px;
}

.env-base-url .label {
  font-weight: 600;
  color: #606266;
}

.env-base-url code {
  background: #f5f7fa;
  padding: 2px 6px;
  border-radius: 4px;
  color: #409eff;
}

.var-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 8px;
}

.var-item {
  background: #f5f7fa;
  padding: 4px 10px;
  border-radius: 4px;
}

.var-key {
  font-weight: 600;
  color: #303133;
}

.var-value {
  margin-left: 4px;
  color: #606266;
}

.tip {
  color: #909399;
  font-size: 13px;
  margin-top: 8px;
}

.error-alert {
  margin-bottom: 16px;
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

@media (max-width: 768px) {
  .action-bar {
    flex-direction: column;
    gap: 12px;
    align-items: flex-start;
  }

  .response-info {
    flex-direction: column;
    gap: 8px;
  }
}
</style>
