<template>
  <div class="mock-service-page">
    <div class="page-header">
      <h2>Mock 服务管理</h2>
      <p class="subtitle">创建和管理 Mock API，支持条件响应和请求日志</p>
    </div>

    <!-- Mock 项目列表 -->
    <div class="section">
      <div class="section-header">
        <h3>Mock 项目</h3>
        <el-button type="primary" @click="showCreateProject = true">
          <el-icon><Plus /></el-icon> 新建项目
        </el-button>
      </div>

      <div v-if="loading" class="loading-container">
        <el-icon class="is-loading"><Loading /></el-icon> 加载中...
      </div>

      <div v-else-if="projects.length === 0" class="empty-state">
        <el-empty description="暂无 Mock 项目">
          <el-button type="primary" @click="showCreateProject = true">创建第一个项目</el-button>
        </el-empty>
      </div>

      <div v-else class="project-grid">
        <div
          v-for="project in projects"
          :key="project.id"
          class="project-card"
          :class="{ active: currentProject?.id === project.id }"
          @click="selectProject(project)"
        >
          <div class="project-info">
            <h4>{{ project.name }}</h4>
            <p>{{ project.description || '暂无描述' }}</p>
            <div class="project-meta">
              <el-tag size="small">{{ project.rule_count || 0 }} 条规则</el-tag>
              <span class="time">{{ formatDate(project.created_at) }}</span>
            </div>
          </div>
          <div class="project-actions">
            <el-button text @click.stop="editProject(project)">
              <el-icon><Edit /></el-icon>
            </el-button>
            <el-button text type="danger" @click.stop="deleteProject(project)">
              <el-icon><Delete /></el-icon>
            </el-button>
          </div>
        </div>
      </div>
    </div>

    <!-- Mock 规则管理 -->
    <div v-if="currentProject" class="section">
      <div class="section-header">
        <h3>Mock 规则 - {{ currentProject.name }}</h3>
        <div class="header-actions">
          <el-button @click="importFromSwagger">
            <el-icon><Upload /></el-icon> 从 Swagger 导入
          </el-button>
          <el-button type="primary" @click="showCreateRule = true">
            <el-icon><Plus /></el-icon> 新建规则
          </el-button>
        </div>
      </div>

      <el-table :data="rules" v-loading="rulesLoading" stripe>
        <el-table-column prop="name" label="规则名称" width="180" />
        <el-table-column prop="method" label="方法" width="100">
          <template #default="{ row }">
            <el-tag :type="getMethodType(row.method)" size="small">{{ row.method }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="path" label="路径" min-width="200" />
        <el-table-column prop="response_status" label="状态码" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.response_status)" size="small">{{ row.response_status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="delay_ms" label="延迟(ms)" width="100" />
        <el-table-column prop="is_active" label="状态" width="80">
          <template #default="{ row }">
            <el-switch v-model="row.is_active" @change="toggleRule(row)" />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button text size="small" @click="editRule(row)">编辑</el-button>
            <el-button text size="small" type="danger" @click="deleteRule(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 请求日志 -->
    <div v-if="currentProject" class="section">
      <div class="section-header">
        <h3>请求日志</h3>
        <el-button @click="refreshLogs">
          <el-icon><Refresh /></el-icon> 刷新
        </el-button>
      </div>

      <el-table :data="logs" v-loading="logsLoading" stripe>
        <el-table-column prop="created_at" label="时间" width="180">
          <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
        </el-table-column>
        <el-table-column prop="method" label="方法" width="100">
          <template #default="{ row }">
            <el-tag :type="getMethodType(row.method)" size="small">{{ row.method }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="path" label="路径" min-width="200" />
        <el-table-column prop="response_status" label="状态码" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.response_status)" size="small">{{ row.response_status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="response_time_ms" label="耗时(ms)" width="100" />
        <el-table-column prop="matched_rule_name" label="匹配规则" width="150" />
      </el-table>
    </div>

    <!-- 创建/编辑项目对话框 -->
    <el-dialog v-model="showCreateProject" :title="editingProject ? '编辑项目' : '新建项目'" width="500px">
      <el-form :model="projectForm" label-width="100px">
        <el-form-item label="项目名称" required>
          <el-input v-model="projectForm.name" placeholder="请输入项目名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="projectForm.description" type="textarea" :rows="3" placeholder="请输入项目描述" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateProject = false">取消</el-button>
        <el-button type="primary" @click="saveProject" :loading="saving">保存</el-button>
      </template>
    </el-dialog>

    <!-- 创建/编辑规则对话框 -->
    <el-dialog v-model="showCreateRule" :title="editingRule ? '编辑规则' : '新建规则'" width="600px">
      <el-form :model="ruleForm" label-width="100px">
        <el-form-item label="规则名称" required>
          <el-input v-model="ruleForm.name" placeholder="请输入规则名称" />
        </el-form-item>
        <el-form-item label="请求方法" required>
          <el-select v-model="ruleForm.method" placeholder="选择方法">
            <el-option label="GET" value="GET" />
            <el-option label="POST" value="POST" />
            <el-option label="PUT" value="PUT" />
            <el-option label="DELETE" value="DELETE" />
            <el-option label="PATCH" value="PATCH" />
          </el-select>
        </el-form-item>
        <el-form-item label="请求路径" required>
          <el-input v-model="ruleForm.path" placeholder="例如: /api/users/:id" />
        </el-form-item>
        <el-form-item label="响应状态码">
          <el-input-number v-model="ruleForm.response_status" :min="100" :max="599" />
        </el-form-item>
        <el-form-item label="响应头">
          <el-input v-model="ruleForm.response_headers_str" type="textarea" :rows="3" placeholder='JSON 格式，例如: {"Content-Type": "application/json"}' />
        </el-form-item>
        <el-form-item label="响应体">
          <el-input v-model="ruleForm.response_body_str" type="textarea" :rows="5" placeholder='JSON 格式，例如: {"code": 200, "data": {}}' />
        </el-form-item>
        <el-form-item label="延迟(ms)">
          <el-input-number v-model="ruleForm.delay_ms" :min="0" :max="30000" />
        </el-form-item>
        <el-form-item label="优先级">
          <el-input-number v-model="ruleForm.priority" :min="0" :max="100" />
          <span class="form-tip">数字越大优先级越高</span>
        </el-form-item>
        <el-form-item label="启用">
          <el-switch v-model="ruleForm.is_active" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateRule = false">取消</el-button>
        <el-button type="primary" @click="saveRule" :loading="saving">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Edit, Delete, Refresh, Upload, Loading } from '@element-plus/icons-vue'
import autoTestRequest from '@/utils/autoTestRequest'

const API_BASE = '/mock'

// 状态
const loading = ref(false)
const rulesLoading = ref(false)
const logsLoading = ref(false)
const saving = ref(false)
const projects = ref([])
const rules = ref([])
const logs = ref([])
const currentProject = ref(null)

// 对话框状态
const showCreateProject = ref(false)
const showCreateRule = ref(false)
const editingProject = ref(null)
const editingRule = ref(null)

// 表单数据
const projectForm = ref({ name: '', description: '' })
const ruleForm = ref({
  name: '',
  method: 'GET',
  path: '',
  response_status: 200,
  response_headers_str: '{"Content-Type": "application/json"}',
  response_body_str: '{}',
  delay_ms: 0,
  priority: 0,
  is_active: true
})

// 加载项目列表
const loadProjects = async () => {
  loading.value = true
  try {
    const res = await autoTestRequest.get(`${API_BASE}/projects`)
    projects.value = res.data
  } catch (err) {
    ElMessage.error('加载项目失败: ' + (err.response?.data?.detail || err.message))
  } finally {
    loading.value = false
  }
}

// 选择项目
const selectProject = async (project) => {
  currentProject.value = project
  await loadRules(project.id)
  await loadLogs(project.id)
}

// 加载规则
const loadRules = async (projectId) => {
  rulesLoading.value = true
  try {
    const res = await autoTestRequest.get(`${API_BASE}/projects/${projectId}/rules`)
    rules.value = res.data
  } catch (err) {
    ElMessage.error('加载规则失败: ' + (err.response?.data?.detail || err.message))
  } finally {
    rulesLoading.value = false
  }
}

// 加载日志
const loadLogs = async (projectId) => {
  logsLoading.value = true
  try {
    const res = await autoTestRequest.get(`${API_BASE}/projects/${projectId}/logs`)
    logs.value = res.data
  } catch (err) {
    ElMessage.error('加载日志失败: ' + (err.response?.data?.detail || err.message))
  } finally {
    logsLoading.value = false
  }
}

// 刷新日志
const refreshLogs = () => {
  if (currentProject.value) {
    loadLogs(currentProject.value.id)
  }
}

// 保存项目
const saveProject = async () => {
  if (!projectForm.value.name) {
    ElMessage.warning('请输入项目名称')
    return
  }
  saving.value = true
  try {
    if (editingProject.value) {
      await autoTestRequest.put(`${API_BASE}/projects/${editingProject.value.id}`, projectForm.value)
      ElMessage.success('项目更新成功')
    } else {
      await autoTestRequest.post(`${API_BASE}/projects`, projectForm.value)
      ElMessage.success('项目创建成功')
    }
    showCreateProject.value = false
    editingProject.value = null
    projectForm.value = { name: '', description: '' }
    await loadProjects()
  } catch (err) {
    ElMessage.error('保存失败: ' + (err.response?.data?.detail || err.message))
  } finally {
    saving.value = false
  }
}

// 编辑项目
const editProject = (project) => {
  editingProject.value = project
  projectForm.value = { name: project.name, description: project.description }
  showCreateProject.value = true
}

// 删除项目
const deleteProject = async (project) => {
  try {
    await ElMessageBox.confirm('确定要删除该项目及其所有规则吗？', '确认删除', { type: 'warning' })
    await autoTestRequest.delete(`${API_BASE}/projects/${project.id}`)
    ElMessage.success('删除成功')
    if (currentProject.value?.id === project.id) {
      currentProject.value = null
      rules.value = []
      logs.value = []
    }
    await loadProjects()
  } catch (err) {
    if (err !== 'cancel') {
      ElMessage.error('删除失败: ' + (err.response?.data?.detail || err.message))
    }
  }
}

// 保存规则
const saveRule = async () => {
  if (!ruleForm.value.name || !ruleForm.value.path) {
    ElMessage.warning('请填写规则名称和路径')
    return
  }
  saving.value = true
  try {
    const data = {
      ...ruleForm.value,
      response_headers: JSON.parse(ruleForm.value.response_headers_str || '{}'),
      response_body: JSON.parse(ruleForm.value.response_body_str || '{}')
    }
    delete data.response_headers_str
    delete data.response_body_str

    if (editingRule.value) {
      await autoTestRequest.put(`${API_BASE}/projects/${currentProject.value.id}/rules/${editingRule.value.id}`, data)
      ElMessage.success('规则更新成功')
    } else {
      await autoTestRequest.post(`${API_BASE}/projects/${currentProject.value.id}/rules`, data)
      ElMessage.success('规则创建成功')
    }
    showCreateRule.value = false
    editingRule.value = null
    resetRuleForm()
    await loadRules(currentProject.value.id)
  } catch (err) {
    ElMessage.error('保存失败: ' + (err.response?.data?.detail || err.message))
  } finally {
    saving.value = false
  }
}

// 编辑规则
const editRule = (rule) => {
  editingRule.value = rule
  ruleForm.value = {
    name: rule.name,
    method: rule.method,
    path: rule.path,
    response_status: rule.response_status,
    response_headers_str: JSON.stringify(rule.response_headers || {}, null, 2),
    response_body_str: JSON.stringify(rule.response_body || {}, null, 2),
    delay_ms: rule.delay_ms || 0,
    priority: rule.priority || 0,
    is_active: rule.is_active !== false
  }
  showCreateRule.value = true
}

// 删除规则
const deleteRule = async (rule) => {
  try {
    await ElMessageBox.confirm('确定要删除该规则吗？', '确认删除', { type: 'warning' })
    await autoTestRequest.delete(`${API_BASE}/projects/${currentProject.value.id}/rules/${rule.id}`)
    ElMessage.success('删除成功')
    await loadRules(currentProject.value.id)
  } catch (err) {
    if (err !== 'cancel') {
      ElMessage.error('删除失败: ' + (err.response?.data?.detail || err.message))
    }
  }
}

// 切换规则状态
const toggleRule = async (rule) => {
  try {
    await autoTestRequest.put(`${API_BASE}/projects/${currentProject.value.id}/rules/${rule.id}`, {
      is_active: rule.is_active
    })
  } catch (err) {
    rule.is_active = !rule.is_active
    ElMessage.error('更新失败')
  }
}

// 从 Swagger 导入
const importFromSwagger = async () => {
  ElMessage.info('Swagger 导入功能开发中...')
}

// 重置规则表单
const resetRuleForm = () => {
  ruleForm.value = {
    name: '',
    method: 'GET',
    path: '',
    response_status: 200,
    response_headers_str: '{"Content-Type": "application/json"}',
    response_body_str: '{}',
    delay_ms: 0,
    priority: 0,
    is_active: true
  }
}

// 工具函数
const getMethodType = (method) => {
  const types = { GET: 'success', POST: 'primary', PUT: 'warning', DELETE: 'danger', PATCH: 'info' }
  return types[method] || 'info'
}

const getStatusType = (status) => {
  if (status >= 200 && status < 300) return 'success'
  if (status >= 300 && status < 400) return 'warning'
  if (status >= 400) return 'danger'
  return 'info'
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN')
}

// 初始化
onMounted(() => {
  loadProjects()
})
</script>

<style scoped>
.mock-service-page {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 30px;
}

.page-header h2 {
  margin: 0 0 8px 0;
  font-size: 24px;
  color: #303133;
}

.page-header .subtitle {
  margin: 0;
  color: #909399;
  font-size: 14px;
}

.section {
  margin-bottom: 30px;
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.section-header h3 {
  margin: 0;
  font-size: 18px;
  color: #303133;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.project-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
}

.project-card {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 16px;
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.project-card:hover {
  border-color: #409eff;
  box-shadow: 0 2px 12px rgba(64, 158, 255, 0.1);
}

.project-card.active {
  border-color: #409eff;
  background: #f0f7ff;
}

.project-info h4 {
  margin: 0 0 8px 0;
  font-size: 16px;
  color: #303133;
}

.project-info p {
  margin: 0 0 12px 0;
  color: #606266;
  font-size: 14px;
}

.project-meta {
  display: flex;
  align-items: center;
  gap: 12px;
}

.project-meta .time {
  color: #909399;
  font-size: 12px;
}

.project-actions {
  display: flex;
  gap: 4px;
}

.loading-container {
  text-align: center;
  padding: 40px;
  color: #909399;
}

.empty-state {
  padding: 40px;
}

.form-tip {
  margin-left: 10px;
  color: #909399;
  font-size: 12px;
}
</style>
