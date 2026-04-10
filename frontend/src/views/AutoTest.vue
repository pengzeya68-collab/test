<template>
  <div class="auto-test-page">
    <!-- 顶部导航 -->
    <div class="page-tabs">
      <div class="nav-buttons" style="display: flex; gap: 15px;">
        <el-button
          type="primary"
          :plain="activeTab !== 'interfaces'"
          @click="activeTab = 'interfaces'; handleTabChange('interfaces')"
        >
          <el-icon><Document /></el-icon>
          <span>接口库</span>
        </el-button>
        <el-button
          type="primary"
          :plain="activeTab !== 'scenarios'"
          @click="activeTab = 'scenarios'; handleTabChange('scenarios')"
        >
          <el-icon><FolderOpened /></el-icon>
          <span>场景管理</span>
        </el-button>
      </div>
    </div>

    <!-- 接口库 Tab -->
    <div v-show="activeTab === 'interfaces'" class="tab-content">
      <div class="page-layout">
        <!-- 左侧：分组树 -->
        <div class="left-panel">
          <div class="panel-header">
            <span class="panel-title">📁 接口分组</span>
            <el-dropdown trigger="click" @command="handleFolderCommand">
              <el-button type="primary" size="small" class="btn-more">
                <el-icon><MoreFilled /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="createRoot">新建根分组</el-dropdown-item>
                  <el-dropdown-item command="createChild" :disabled="!currentGroup">新建子分组</el-dropdown-item>
                  <el-dropdown-item command="editGroup" :disabled="!currentGroup">编辑分组</el-dropdown-item>
                  <el-dropdown-item command="deleteGroup" :disabled="!currentGroup" divided>删除分组</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>

          <div class="folder-tree" v-loading="loadingGroups">
            <el-tree
              ref="folderTreeRef"
              :data="groupTreeData"
              :props="{ children: 'children', label: 'name' }"
              node-key="id"
              default-expand-all
              highlight-current
              @node-click="handleGroupSelect"
            >
              <template #default="{ node, data }">
                <span class="tree-node">
                  <span class="node-icon">{{ data.children?.length ? '📂' : '📁' }}</span>
                  <span class="node-label">{{ node.label }}</span>
                  <span class="node-count">({{ data.caseCount || 0 }})</span>
                </span>
              </template>
            </el-tree>
            <el-empty v-if="!loadingGroups && groupTreeData.length === 0" description="暂无分组" class="dark-empty" />
          </div>
        </div>

        <!-- 右侧：用例列表 -->
        <div class="right-panel">
          <CaseList
            ref="caseListRef"
            :group-id="currentGroupId"
            :environment-list="environmentList"
            @run="handleRunCases"
          />
        </div>
      </div>
    </div>

    <!-- 场景管理 Tab -->
    <div v-show="activeTab === 'scenarios'" class="tab-content">
      <div class="scenario-container">
        <ScenarioList
          v-if="!currentScenarioId"
          ref="scenarioListRef"
          @edit="handleEditScenario"
        />

        <!-- 场景编排详情 -->
        <ScenarioEditor
          v-else
          :scenario-id="currentScenarioId"
          @back="currentScenarioId = null"
        />
      </div>
    </div>

    <!-- 新建/编辑分组对话框 -->
    <el-dialog
      v-model="folderDialogVisible"
      :title="folderDialogType === 'edit' ? '编辑分组' : '新建分组'"
      width="420px"
      custom-class="dark-dialog"
    >
      <el-form :model="folderForm" label-width="60px">
        <el-form-item label="名称">
          <el-input v-model="folderForm.name" placeholder="输入分组名称" class="dark-input" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="folderForm.description" placeholder="可选描述" class="dark-input" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="folderDialogVisible = false" class="btn-cancel">取消</el-button>
        <el-button type="primary" @click="handleFolderSave" class="btn-primary">确定</el-button>
      </template>
    </el-dialog>

    <!-- 执行结果对话框 -->
    <el-dialog
      v-model="resultDialogVisible"
      title="执行结果"
      width="75%"
      destroy-on-close
      custom-class="dark-dialog"
    >
      <div class="result-content">
        <div class="result-summary">
          <el-tag :type="runResult.passed ? 'success' : 'danger'" size="large" class="result-tag">
            {{ runResult.passed ? '✓ 通过' : '✗ 失败' }}
          </el-tag>
          <span class="summary-info">
            耗时: {{ runResult.duration }}ms | 断言: {{ runResult.passedAssertions }}/{{ runResult.totalAssertions }}
          </span>
        </div>
        <el-divider class="dark-divider" />
        <div class="result-detail">
          <h4>响应信息</h4>
          <div class="response-info">
            <div class="info-item">
              <span class="info-label">状态码:</span>
              <el-tag v-if="runResult.hasError" type="warning" size="small">
                连接失败
              </el-tag>
              <el-tag v-else :type="runResult.statusCode === 200 ? 'success' : 'danger'" size="small">
                {{ runResult.statusCode || '无' }}
              </el-tag>
            </div>
            <div class="info-item">
              <span class="info-label">耗时:</span>
              <span>{{ runResult.duration }}ms</span>
            </div>
          </div>
          <div v-if="runResult.errorMessage" class="error-message">
            <el-alert type="error" :title="runResult.errorMessage" :closable="false" show-icon />
          </div>
          <h4>响应体</h4>
          <pre class="response-display">{{ runResult.responseBody || '无响应体' }}</pre>
          <h4 v-if="runResult.assertionResults?.length">断言结果</h4>
          <el-table
            v-if="runResult.assertionResults?.length"
            :data="runResult.assertionResults"
            border
            size="small"
            class="dark-table"
          >
            <el-table-column prop="field" label="字段" width="150" />
            <el-table-column prop="operator" label="比较" width="80" />
            <el-table-column prop="expected" label="预期值" />
            <el-table-column prop="actual" label="实际值" />
            <el-table-column label="结果" width="80" align="center">
              <template #default="{ row }">
                <el-tag :type="row.passed ? 'success' : 'danger'" size="small">
                  {{ row.passed ? '通过' : '失败' }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { MoreFilled, Document, FolderOpened } from '@element-plus/icons-vue'
import CaseList from './CaseList.vue'
import ScenarioList from './ScenarioList.vue'
import ScenarioEditor from './ScenarioEditor.vue'
import axios from 'axios'

const autoTestRequest = axios.create({
  baseURL: '',
  timeout: 30000
})

// 添加请求拦截器，自动带上 token（支持前台用户 token 和后台 admin token）
autoTestRequest.interceptors.request.use(
  config => {
    const token = localStorage.getItem('admin_token') || localStorage.getItem('token')
    if (token && token !== 'undefined' && token !== 'null' && token !== '[object Object]') {
      config.headers['Authorization'] = `Bearer ${token}`
    }
    return config
  },
  error => Promise.reject(error)
)

// 添加响应拦截器，统一返回 response.data
autoTestRequest.interceptors.response.use(
  response => response.data,
  error => Promise.reject(error)
)

const activeTab = ref('interfaces')
const currentScenarioId = ref(null)

// 分组相关
const folderTreeRef = ref(null)
const groupTreeData = ref([])
const currentGroup = ref(null)
const currentGroupId = ref(null)
const loadingGroups = ref(false)
const folderDialogVisible = ref(false)
const folderDialogType = ref('create')
const folderForm = ref({ name: '', description: '', parentId: null })

// 环境相关
const environmentList = ref([])

// 执行结果
const resultDialogVisible = ref(false)
const runResult = ref({
  passed: false,
  statusCode: 200,
  duration: 0,
  responseBody: '',
  passedAssertions: 0,
  totalAssertions: 0,
  assertionResults: []
})

// 场景列表引用
const scenarioListRef = ref(null)

// 加载分组树
const loadGroups = async () => {
  loadingGroups.value = true
  try {
    const res = await autoTestRequest.get('/api/auto-test/groups')
    groupTreeData.value = buildTree(res || [])
  } catch (error) {
    console.error('加载分组失败:', error)
    ElMessage.error('加载分组失败')
  } finally {
    loadingGroups.value = false
  }
}

// 构建树形结构
const buildTree = (list, parentId = null) => {
  return list
    .filter(item => item.parent_id === parentId)
    .map(item => ({
      ...item,
      children: buildTree(list, item.id),
      caseCount: item.caseCount
    }))
}

// 选择分组
const handleGroupSelect = (data) => {
  currentGroup.value = data
  currentGroupId.value = data.id
}

// Tab 切换
const handleTabChange = (val) => {
  if (val === 'scenarios' && scenarioListRef.value) {
    scenarioListRef.value.loadScenarios()
  }
}

// 分组操作
const handleFolderCommand = (command) => {
  switch (command) {
    case 'createRoot':
      folderDialogType.value = 'create'
      folderForm.value = { name: '', description: '', parentId: null }
      folderDialogVisible.value = true
      break
    case 'createChild':
      folderDialogType.value = 'create'
      folderForm.value = { name: '', description: '', parentId: currentGroup.value?.id }
      folderDialogVisible.value = true
      break
    case 'editGroup':
      folderDialogType.value = 'edit'
      folderForm.value = {
        id: currentGroup.value?.id,
        name: currentGroup.value?.name,
        description: currentGroup.value?.description
      }
      folderDialogVisible.value = true
      break
    case 'deleteGroup':
      handleDeleteFolder()
      break
  }
}

// 保存分组
const handleFolderSave = async () => {
  console.log('--- [AutoTest] 触发 handleFolderSave 保存分组 ---')
  console.log('--- folderForm 数据:', folderForm.value)
  if (!folderForm.value.name) {
    ElMessage.warning('请输入分组名称')
    return
  }
  try {
    if (folderDialogType.value === 'edit') {
      await autoTestRequest.put(`/api/auto-test/groups/${folderForm.value.id}`, {
        name: folderForm.value.name,
        description: folderForm.value.description
      })
      ElMessage.success('更新成功')
    } else {
      await autoTestRequest.post('/api/auto-test/groups', {
        name: folderForm.value.name,
        description: folderForm.value.description,
        parent_id: folderForm.value.parentId
      })
      ElMessage.success('创建成功')
    }
    folderDialogVisible.value = false
    loadGroups()
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

// 删除分组
const handleDeleteFolder = async () => {
  if (!currentGroup.value) return
  try {
    await ElMessageBox.confirm(
      `确定要删除分组 "${currentGroup.value.name}" 吗？分组下的用例将被删除。`,
      '删除确认',
      { type: 'warning' }
    )
    await autoTestRequest.delete(`/api/auto-test/groups/${currentGroup.value.id}`)
    ElMessage.success('删除成功')
    currentGroup.value = null
    currentGroupId.value = null
    loadGroups()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

// 加载环境列表
const loadEnvironments = async () => {
  try {
    const res = await autoTestRequest.get('/api/interface-test/environments')
    environmentList.value = res || []
  } catch (error) {
    console.error('加载环境失败:', error)
  }
}

// 变量替换函数：替换 {{varname}} 格式的占位符，支持任意变量名
const replaceVariables = (template, vars) => {
  if (!template || !vars || typeof template !== 'string') {
    return template
  }
  return template.replace(/\{\{(.*?)\}\}/g, (match, varName) => {
    varName = varName.trim()
    return vars[varName] !== undefined ? vars[varName] : match
  })
}

// 运行用例
const handleRunCases = async (caseData, envId) => {
  try {
    // 1. 先获取用例详情
    const detailRes = await autoTestRequest.get(`/api/auto-test/cases/${caseData.id}`)
    const detail = detailRes

    // 2. 解析请求信息
    let headers = {}
    try {
      if (detail.headers) {
        headers = JSON.parse(detail.headers)
      }
    } catch(e) {
      headers = {}
    }

    // 3. 收集环境变量
    let envVars = {}
    let finalUrl = detail.url

    // 如果指定了环境，应用环境变量
    if (envId) {
      try {
        const env = environmentList.value.find(e => e.id === envId)
        if (env) {
          // 后端已经解析好了 variables，直接使用即可
          if (env.variables && typeof env.variables === 'object') {
            envVars = { ...env.variables }
          }
          // 如果有 base_url 添加到环境变量中
          if (env.base_url && !('base_url' in envVars)) {
            envVars.base_url = env.base_url
          }
        }
      } catch(e) {
        console.warn('应用环境变量失败:', e)
      }
    }

    // 4. 对 URL、Headers、Body 进行变量替换
    if (Object.keys(envVars).length > 0) {
      finalUrl = replaceVariables(finalUrl, envVars)
      // 替换 headers 中的变量
      Object.keys(headers).forEach(key => {
        if (typeof headers[key] === 'string') {
          headers[key] = replaceVariables(headers[key], envVars)
        }
      })
    }

    // 处理 body 变量替换
    let finalBody = detail.body || ''
    if (Object.keys(envVars).length > 0 && typeof finalBody === 'string') {
      finalBody = replaceVariables(finalBody, envVars)
    }

    // 5. 通过 interface-test/send 端点执行请求
    const requestData = {
      method: detail.method,
      url: detail.url,
      url_after_replace: finalUrl,
      headers: headers,
      body: finalBody,
      body_type: detail.body_type || 'json',
      env_id: envId,
      variables: envVars
    }

    const res = await autoTestRequest.post('/api/interface-test/send', requestData)

    // 处理响应体
    let responseBody = ''
    if (res.response_content) {
      responseBody = typeof res.response_content === 'string'
        ? res.response_content
        : JSON.stringify(res.response_content, null, 2)
    }

    const hasError = !res.status_code && res.error

    runResult.value = {
      passed: res.status_code >= 200 && res.status_code < 300,
      statusCode: res.status_code,
      hasError: hasError,
      errorMessage: res.error || null,
      duration: res.elapsed_ms || 0,
      responseBody: responseBody,
      passedAssertions: 0,
      totalAssertions: 0,
      assertionResults: []
    }
    resultDialogVisible.value = true
  } catch (error) {
    // 尝试提取后端返回的具体错误信息
    let errorMsg = '执行失败'
    if (error.response?.data) {
      if (error.response.data.msg) {
        errorMsg = error.response.data.msg
      } else if (error.response.data.error) {
        errorMsg = error.response.data.error
      } else if (error.response.data.detail) {
        errorMsg = error.response.data.detail
      } else {
        errorMsg = error.message
      }
    } else {
      errorMsg = error.message
    }
    ElMessage.error(errorMsg)
  }
}

// 编辑场景
const handleEditScenario = (scenario) => {
  currentScenarioId.value = scenario.id
}

onMounted(() => {
  loadGroups()
  loadEnvironments()
})
</script>

<style scoped>
.auto-test-page {
  padding: 30px 0;
  min-height: calc(100vh - 60px);
  background-color: var(--tm-bg-color);
  background-image: var(--tm-bg-image);
  background-size: cover;
  background-position: center;
  font-family: 'Inter', 'Roboto', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}

/* 页面标签页 */
.page-tabs {
  width: 100%;
  max-width: 100%;
  padding: 20px 32px;
  margin: 0 auto 16px;
  box-sizing: border-box;
  background: var(--tm-card-bg);
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 150, 136, 0.15);
  border: var(--tm-card-border);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
}

.tab-group :deep(.el-radio-button__inner) {
  display: flex;
  align-items: center;
  gap: 8px;
  border-radius: 8px;
  background: rgba(var(--tm-bg-page-rgb), 0.5);
  border: 1px solid var(--tm-border-light);
  color: var(--tm-text-secondary);
  transition: all 0.3s ease;
}

.tab-group :deep(.el-radio-button__inner:hover) {
  color: var(--tm-color-primary);
}

.tab-group :deep(.el-radio-button.is-active .el-radio-button__inner) {
  background: linear-gradient(135deg, var(--tm-color-primary), var(--tm-color-primary-dark));
  border-color: var(--tm-color-primary);
  color: white;
  box-shadow: var(--tm-glow-effect);
}

.tab-content {
  width: 100%;
  max-width: 100%;
  padding: 0 32px;
  margin: 0 auto;
  box-sizing: border-box;
  flex: 1;
  overflow: hidden;
}

.scenario-container {
  background: var(--tm-card-bg);
  border-radius: 12px;
  padding: 20px;
  border: var(--tm-card-border);
  box-shadow: 0 4px 20px rgba(0, 150, 136, 0.15);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  min-height: calc(100vh - 200px);
}

/* 双栏布局 */
.page-layout {
  display: flex;
  height: calc(100vh - 220px);
  gap: 16px;
}

.left-panel {
  width: 280px;
  background: var(--tm-card-bg);
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 150, 136, 0.15);
  border: var(--tm-card-border);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border-bottom: var(--tm-card-border);
  flex-shrink: 0;
}

.panel-title {
  font-weight: 600;
  font-size: 16px;
  color: var(--tm-text-primary);
}

.btn-more {
  background: transparent;
  border: 1px solid var(--tm-color-primary);
  color: var(--tm-color-primary);
  border-radius: 6px;
}

.btn-more:hover {
  background: rgba(var(--tm-color-primary), 0.1);
}

.folder-tree {
  flex: 1;
  overflow: auto;
  padding: 12px;
}

.tree-node {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 4px;
  color: var(--tm-text-secondary);
}

.node-icon {
  font-size: 14px;
}

.node-label {
  flex: 1;
  font-size: 14px;
  color: var(--tm-text-primary);
}

.node-count {
  color: var(--tm-color-primary);
  font-size: 12px;
  background: rgba(var(--tm-color-primary), 0.15);
  padding: 2px 8px;
  border-radius: 10px;
  border: 1px solid rgba(var(--tm-color-primary), 0.3);
}

.right-panel {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  background: var(--tm-card-bg);
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 150, 136, 0.15);
  border: var(--tm-card-border);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
}

.dark-empty {
  color: var(--tm-text-secondary);
}

.dark-empty :deep(.el-empty__description) {
  color: var(--tm-text-secondary);
}

/* 结果对话框 */
.result-content {
  max-height: 70vh;
  overflow: auto;
}

.result-summary {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
}

.summary-info {
  color: var(--tm-text-secondary);
  font-size: 15px;
}

.result-detail h4 {
  margin: 20px 0 12px;
  color: var(--tm-text-primary);
  font-size: 16px;
  font-weight: 600;
}

.response-info {
  display: flex;
  gap: 24px;
  margin-bottom: 12px;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.info-label {
  color: var(--tm-text-secondary);
  font-size: 14px;
}

.error-message {
  margin-bottom: 16px;
}

.response-display {
  background: rgba(0, 0, 0, 0.3);
  color: var(--tm-color-primary);
  padding: 16px;
  border-radius: 8px;
  max-height: 320px;
  overflow: auto;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 13px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-all;
  margin: 0;
  box-shadow: inset 0 2px 8px rgba(0, 0, 0, 0.4);
  border: var(--tm-card-border);
}

/* 暗黑对话框样式覆盖 */
:deep(.dark-dialog) {
  background: var(--tm-card-bg);
  color: var(--tm-text-primary);
}

.dark-dialog :deep(.el-dialog__header) {
  border-bottom: var(--tm-card-border);
}

.dark-dialog :deep(.el-dialog__title) {
  color: var(--tm-text-primary);
}

.dark-dialog :deep(.el-dialog__body) {
  color: var(--tm-text-primary);
}

.dark-input :deep(.el-input__wrapper) {
  background: var(--tm-card-bg);
  box-shadow: 0 0 0 1px var(--tm-border-light) inset;
  border-radius: 6px;
}

.dark-input :deep(.el-input__inner) {
  color: var(--tm-text-primary);
}

.dark-input :deep(.el-input__inner::placeholder) {
  color: var(--tm-text-secondary);
}

.dark-input :deep(.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px var(--tm-color-primary) inset, var(--tm-glow-effect);
}

.dark-divider {
  --el-divider-color: var(--tm-border-light);
}

.btn-primary {
  background: linear-gradient(135deg, var(--tm-color-primary), var(--tm-color-primary-dark));
  border: none;
  box-shadow: 0 2px 10px rgba(var(--tm-color-primary), 0.3);
}

.btn-primary:hover {
  background: linear-gradient(135deg, var(--tm-color-primary), var(--tm-color-primary-dark));
  box-shadow: 0 4px 15px rgba(var(--tm-color-primary), 0.4);
}

.btn-cancel {
  color: var(--tm-text-secondary);
  background: transparent;
  border: 1px solid var(--tm-border-light);
}

.btn-cancel:hover {
  color: var(--tm-text-primary);
  border-color: var(--tm-color-primary);
}

.dark-table :deep(.el-table) {
  background: transparent;
  color: var(--tm-text-primary);
}

.dark-table :deep(.el-table tr) {
  background: var(--tm-card-bg);
}

.dark-table :deep(.el-table th) {
  background: rgba(var(--tm-text-primary), 0.05);
  color: var(--tm-text-secondary);
}

.dark-table :deep(.el-table td) {
  border-bottom: 1px solid var(--tm-border-light);
  color: var(--tm-text-primary);
}

.dark-table :deep(.el-table--border) {
  border-color: var(--tm-border-light);
}

.dark-table :deep(.el-table__row:hover > td) {
  background-color: rgba(var(--tm-color-primary), 0.1);
}

/* 响应式 */
@media (max-width: 768px) {
  .page-layout {
    flex-direction: column;
  }

  .left-panel {
    width: 100%;
    max-height: 300px;
  }
}
</style>
