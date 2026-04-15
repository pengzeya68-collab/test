<template>
  <el-drawer
    v-model="visible"
    title="🌐 环境管理"
    size="700px"
    :with-header="true"
    class="environment-manager-drawer"
  >
    <div class="env-manager-content">
      <!-- 头部操作栏 -->
      <div class="actions-bar">
        <el-button type="primary" @click="handleCreate">
          <el-icon><Plus /></el-icon>
          新建环境
        </el-button>
        <el-button type="info" @click="handleExportEnvironments">
          <el-icon><Download /></el-icon>
          导出环境
        </el-button>
        <el-upload
          class="upload-btn"
          action=""
          :auto-upload="false"
          :on-change="handleImportEnvironments"
          :show-file-list="false"
          accept=".json"
        >
          <el-button type="info">
            <el-icon><Upload /></el-icon>
            导入环境
          </el-button>
        </el-upload>
      </div>

      <!-- 环境变量说明 -->
      <el-alert
        title="环境变量说明"
        type="info"
        :closable="false"
        show-icon
        style="margin-bottom: 16px"
      >
        <template #default>
          <div class="environment-description">
            <p><strong>什么是环境变量？</strong> 环境变量是特定环境下的变量，例如开发环境、测试环境、生产环境等。</p>
            <p><strong>如何使用？</strong> 在URL、Headers、Form Data等输入框中使用 {{变量名}} 格式引用变量。</p>
            <p><strong>变量优先级：</strong> 环境变量 > 全局变量。当环境变量和全局变量同名时，环境变量会覆盖全局变量。</p>
            <p><strong>基础URL：</strong> 环境的基础URL会被自动设置为 base_url 变量，可在URL中引用。</p>
            <p><strong>执行时加载：</strong> 执行用例时，系统会自动加载当前环境的变量，并替换用例中的变量占位符。</p>
          </div>
        </template>
      </el-alert>

      <!-- 环境列表 -->
      <div class="env-list">
        <el-card
          v-for="env in environments"
          :key="env.id"
          class="env-card"
          shadow="hover"
        >
          <div class="env-header">
            <div class="env-name">
              {{ env.env_name || env.name }}
              <el-tag v-if="env.is_default" type="success" size="small">默认</el-tag>
            </div>
            <el-button-group>
              <el-button size="small" @click="handleEdit(env)">编辑</el-button>
              <el-button size="small" type="danger" @click="handleDelete(env)">删除</el-button>
            </el-button-group>
          </div>
          <div class="env-base-url">
            <span class="label">基础URL：</span>
            <code>{{ env.base_url || '(空)' }}</code>
          </div>
          <div v-if="Object.keys(env.variables || {}).length > 0" class="variables">
            <div class="label">自定义变量：</div>
            <div class="var-list">
              <div class="var-item" v-for="(value, key) in env.variables" :key="key">
                <span class="var-key">{{ key }}</span>
                <span class="var-value">{{ value }}</span>
              </div>
            </div>
          </div>
          <div v-else class="no-vars">暂无自定义变量</div>
        </el-card>
      </div>

      <!-- 空状态 -->
      <div v-if="environments.length === 0 && !loading" class="empty-state">
        <div class="empty-icon">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z" fill="currentColor"/>
          </svg>
        </div>
        <div class="empty-text">暂无环境，点击上方按钮创建</div>
      </div>
    </div>

    <!-- 创建/编辑弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑环境' : '新建环境'"
      width="550px"
      custom-class="environment-dialog"
    >
      <el-form :model="formData" label-width="80px">
        <el-form-item label="环境名称" required>
          <el-input v-model="formData.env_name" placeholder="例如：开发环境" />
        </el-form-item>
        <el-form-item label="基础URL">
          <el-input v-model="formData.base_url" placeholder="例如：http://api.example.com" />
        </el-form-item>
        <el-form-item label="设为默认">
          <el-switch v-model="formData.is_default" />
        </el-form-item>
        <div class="section-title">自定义变量</div>
        <div class="var-editor">
          <div class="var-item-editor" v-for="(item, index) in vars" :key="index">
            <el-input
              v-model="item.key"
              placeholder="变量名"
              style="width: 150px; margin-right: 8px;"
            />
            <el-input
              v-model="item.value"
              placeholder="变量值"
              style="flex: 1; margin-right: 8px;"
            />
            <el-button
              type="danger"
              icon="Delete"
              circle
              size="small"
              @click="removeVar(index)"
            />
          </div>
          <el-button type="primary" plain size="small" @click="addVar">
            <el-icon><Plus /></el-icon>
            添加变量
          </el-button>
        </div>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleSave">
            {{ isEdit ? '保存修改' : '创建' }}
          </el-button>
        </span>
      </template>
    </el-dialog>
  </el-drawer>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { Plus, Download, Upload } from '@element-plus/icons-vue'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'

const token = localStorage.getItem('token') || ''
const autoTestRequest = axios.create({
  timeout: 30000,
  headers: token ? { Authorization: `Bearer ${token}` } : {}
})

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue', 'changed'])

const visible = computed({
  get: () => props.modelValue,
  set: val => emit('update:modelValue', val)
})

const environments = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const isEdit = ref(false)
const editingId = ref(null)

const formData = ref({
  env_name: '',
  base_url: '',
  is_default: false,
  variables: {}
})

const vars = ref([{ key: '', value: '' }])

const addVar = () => {
  vars.value.push({ key: '', value: '' })
}

const removeVar = (index) => {
  vars.value.splice(index, 1)
}

const collectVars = () => {
  const obj = {}
  vars.value.forEach(v => {
    if (v.key && v.key.trim()) {
      obj[v.key.trim()] = v.value || ''
    }
  })
  formData.value.variables = obj
}

const fetchEnvs = async () => {
  loading.value = true
  try {
    const res = await autoTestRequest.get('/api/auto-test/environments')
    environments.value = res.data || res
    emit('changed', environments.value)
  } catch (err) {
    console.error('获取环境列表失败:', err)
    ElMessage.error('获取环境列表失败')
  } finally {
    loading.value = false
  }
}

const handleCreate = () => {
  isEdit.value = false
  editingId.value = null
  formData.value = {
    env_name: '',
    base_url: '',
    is_default: false,
    variables: {}
  }
  vars.value = [{ key: '', value: '' }]
  dialogVisible.value = true
}

const handleEdit = (env) => {
  isEdit.value = true
  editingId.value = env.id
  formData.value = {
    env_name: env.env_name || env.name || '',
    base_url: env.base_url || '',
    is_default: env.is_default,
    variables: { ...(env.variables || {}) }
  }
  // 转换为数组
  const entries = Object.entries(formData.value.variables)
  if (entries.length === 0) {
    vars.value = [{ key: '', value: '' }]
  } else {
    vars.value = entries.map(([key, value]) => ({ key, value }))
  }
  dialogVisible.value = true
}

const handleSave = async () => {
  if (!formData.value.env_name.trim()) {
    ElMessage.warning('请输入环境名称')
    return
  }
  collectVars()

  try {
    if (isEdit.value) {
      await autoTestRequest.put(`/api/auto-test/environments/${editingId.value}`, formData.value)
      ElMessage.success('修改成功')
    } else {
      await autoTestRequest.post('/api/auto-test/environments', formData.value)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    fetchEnvs()
  } catch (err) {
    console.error('保存失败:', err)
    const errorMsg = err.response?.data?.detail || err.response?.data?.message || '保存失败'
    ElMessage.error(`保存失败: ${errorMsg}`)
  }
}

const handleDelete = async (env) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除环境 "${env.env_name || env.name}" 吗？`,
      '确认删除',
      { confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning' }
    )
    await autoTestRequest.delete(`/api/auto-test/environments/${env.id}`)
    ElMessage.success('删除成功')
    fetchEnvs()
  } catch {
    // 取消
  }
}

// 导出环境
const handleExportEnvironments = () => {
  const dataStr = JSON.stringify(environments.value, null, 2)
  const dataBlob = new Blob([dataStr], { type: 'application/json' })
  const url = URL.createObjectURL(dataBlob)
  const link = document.createElement('a')
  link.href = url
  link.download = `environments-${new Date().toISOString().slice(0, 10)}.json`
  link.click()
  URL.revokeObjectURL(url)
  ElMessage.success('导出成功')
}

// 导入环境
const handleImportEnvironments = async (file) => {
  const reader = new FileReader()
  reader.onload = async (e) => {
    try {
      const data = JSON.parse(e.target.result)
      if (!Array.isArray(data)) {
        ElMessage.error('导入文件格式错误')
        return
      }

      let importedCount = 0
      for (const envData of data) {
        try {
          // 检查环境名称是否已存在
          const existingEnv = environments.value.find(env => env.env_name === envData.env_name)
          if (existingEnv) {
            // 如果存在，更新
            await autoTestRequest.put(`/api/auto-test/environments/${existingEnv.id}`, envData)
          } else {
            // 如果不存在，创建
            await autoTestRequest.post('/api/auto-test/environments/', envData)
          }
          importedCount++
        } catch (error) {
          console.error(`导入环境 "${envData.env_name}" 失败:`, error)
        }
      }

      ElMessage.success(`成功导入 ${importedCount} 个环境`)
      fetchEnvs()
    } catch (error) {
      console.error('导入环境失败:', error)
      ElMessage.error('导入环境失败')
    }
  }
  reader.readAsText(file.raw)
}

onMounted(() => {
  if (visible.value) {
    fetchEnvs()
  }
})

watch(() => props.modelValue, (newVal) => {
  if (newVal) {
    fetchEnvs()
  }
})
</script>

<style scoped>
.env-manager-drawer {
  background: var(--tm-bg-color);
}

.env-manager-content {
  min-height: 100%;
}

.actions-bar {
  margin-bottom: 20px;
  text-align: right;
}

.env-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.env-card {
  background: var(--tm-card-bg);
  border: var(--tm-card-border);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);

  .env-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
  }

  .env-name {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 18px;
    font-weight: 600;
    color: var(--tm-text-primary);
  }
}

.env-base-url {
  margin-bottom: 12px;
}

.label {
  font-weight: 600;
  color: var(--tm-text-secondary);
}

.env-base-url code {
  background: var(--tm-bg-soft);
  padding: 2px 6px;
  border-radius: 4px;
  color: var(--tm-color-primary);
  font-size: 13px;
}

.variables {
  margin-top: 12px;
}

.var-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 8px;
}

.var-item {
  background: var(--tm-bg-soft);
  padding: 4px 10px;
  border-radius: 4px;
}

.var-key {
  font-weight: 600;
  color: var(--tm-text-primary);
}

.var-value {
  margin-left: 4px;
  color: var(--tm-text-secondary);
}

.no-vars {
  color: var(--tm-text-placeholder);
  font-size: 14px;
  margin-top: 8px;
}

.section-title {
  font-weight: 600;
  margin-bottom: 12px;
  color: var(--tm-text-primary);
}

.var-editor {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 16px;
}

.var-item-editor {
  display: flex;
  align-items: center;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
}

/* 环境对话框自定义样式 */
:deep(.environment-dialog) {
  --bg-elevated: var(--tm-card-bg);
  --border-subtle: var(--tm-border-light);
  --radius-lg: var(--tm-radius-base);
  --accent-primary: var(--tm-color-primary);
  --accent-glow-color: rgba(0, 210, 255, 0.4);

  background: var(--bg-elevated) !important;
  border: 1px solid var(--border-subtle) !important;
  border-radius: var(--radius-lg) !important;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5) !important;
  backdrop-filter: blur(10px) !important;
  -webkit-backdrop-filter: blur(10px) !important;
}

/* 表单项间距 */
:deep(.environment-dialog .el-form-item) {
  margin-bottom: 24px;
}

/* 输入框样式 */
:deep(.environment-dialog .el-input__wrapper) {
  background: rgba(0, 0, 0, 0.2) !important;
  border: 1px solid var(--border-subtle) !important;
  border-radius: 6px;
  transition: all 0.2s;
}

:deep(.environment-dialog .el-input__wrapper:hover) {
  border-color: var(--tm-color-primary-light) !important;
}

:deep(.environment-dialog .el-input__wrapper.is-focus) {
  border-color: var(--tm-color-primary) !important;
  box-shadow: 0 0 0 2px var(--accent-glow-color) !important;
}

/* 主操作按钮 */
:deep(.environment-dialog .el-button--primary) {
  background: var(--accent-primary) !important;
  color: white !important;
  border: none !important;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.2), 0 4px 12px var(--accent-glow-color) !important;
  font-weight: 500;
  transition: all 0.2s;
}

:deep(.environment-dialog .el-button--primary:hover) {
  transform: translateY(-1px);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.3), 0 6px 16px rgba(0, 210, 255, 0.5) !important;
}

:deep(.environment-dialog .el-button--primary:active) {
  transform: translateY(0);
}

/* 对话框标题和内容 */
:deep(.environment-dialog .el-dialog__header) {
  border-bottom: 1px solid var(--border-subtle);
  padding: 20px 24px;
}

:deep(.environment-dialog .el-dialog__body) {
  padding: 24px;
}

:deep(.environment-dialog .el-dialog__footer) {
  border-top: 1px solid var(--border-subtle);
  padding: 16px 24px;
}

/* 变量编辑器间距 */
:deep(.environment-dialog .var-editor) {
  margin-top: 8px;
}

:deep(.environment-dialog .var-item-editor) {
  margin-bottom: 12px;
}
</style>
