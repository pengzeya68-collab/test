﻿<template>
  <div class="global-variable-manager">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>全局变量管理</span>
          <div class="header-actions">
            <el-button type="primary" size="small" @click="handleAddVariable">
              <el-icon><Plus /></el-icon>
              添加变量
            </el-button>
            <el-button 
              type="danger" 
              size="small" 
              @click="handleBatchDelete"
              :disabled="selectedVariables.length === 0"
            >
              <el-icon><Delete /></el-icon>
              批量删除
            </el-button>
            <el-button type="info" size="small" @click="handleDebugVariables">
              <el-icon><View /></el-icon>
              变量调试
            </el-button>
          </div>
        </div>
      </template>

      <!-- 全局变量说明 -->
      <el-alert
        title="全局变量说明"
        type="info"
        :closable="false"
        show-icon
        style="margin-bottom: 16px"
      >
        <template #default>
          <div class="variable-description">
            <p><strong>什么是全局变量？</strong> 全局变量是在所有环境中都可用的变量，可在多个用例和场景中共享使用。</p>
            <p><strong>如何使用？</strong> 在URL、Headers、Form Data等输入框中使用 <span v-text="'{{变量名}}'"></span> 格式引用变量。</p>
            <p><strong>变量优先级：</strong> 环境变量 > 全局变量。当环境变量和全局变量同名时，环境变量会覆盖全局变量。</p>
            <p><strong>加密变量：</strong> 标记为加密的变量会在存储时加密，显示时会被替换为 ******，保护敏感信息。</p>
            <p><strong>动态变量：</strong> 支持使用 <span v-text="'{{$timestamp}}'"></span>、<span v-text="'{{$random_int}}'"></span>、<span v-text="'{{$random_string}}'"></span>、<span v-text="'{{$uuid}}'"></span>、<span v-text="'{{$datetime}}'"></span> 等动态变量。</p>
          </div>
        </template>
      </el-alert>

      <el-table 
        :data="variables" 
        style="width: 100%"
        :row-key="row => row.id"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="name" label="变量名" width="180" />
        <el-table-column prop="value" label="变量值">
          <template #default="{ row }">
            <el-input
              v-if="editingRowId === row.id"
              v-model="editForm.value"
              :type="row.is_encrypted ? 'password' : 'text'"
              placeholder="变量值"
              @blur="handleSaveEdit(row.id)"
            />
            <span v-else>{{ row.is_encrypted ? '******' : row.value }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" width="200">
          <template #default="{ row }">
            <el-input
              v-if="editingRowId === row.id"
              v-model="editForm.description"
              placeholder="描述"
              @blur="handleSaveEdit(row.id)"
            />
            <span v-else>{{ row.description || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="is_encrypted" label="是否加密" width="100" align="center">
          <template #default="{ row }">
            <el-switch
              v-if="editingRowId === row.id"
              v-model="editForm.is_encrypted"
            />
            <el-tag v-else :type="row.is_encrypted ? 'warning' : 'info'" size="small">
              {{ row.is_encrypted ? '是' : '否' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="editingRowId !== row.id"
              type="primary" 
              link 
              size="small"
              @click="handleEdit(row)"
            >
              编辑
            </el-button>
            <el-button
              v-if="editingRowId === row.id"
              type="success" 
              link 
              size="small"
              @click="handleSaveEdit(row.id)"
            >
              保存
            </el-button>
            <el-button
              v-if="editingRowId === row.id"
              type="info" 
              link 
              size="small"
              @click="editingRowId = null"
            >
              取消
            </el-button>
            <el-button
              type="danger" 
              link 
              size="small"
              @click="handleDelete(row.id)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 添加变量对话框 -->
      <el-dialog
        v-model="dialogVisible"
        title="添加全局变量"
        width="500px"
      >
        <el-form :model="form" label-width="80px">
          <el-form-item label="变量名" required>
            <el-input v-model="form.name" placeholder="请输入变量名" />
          </el-form-item>
          <el-form-item label="变量值" required>
            <el-input
              v-model="form.value"
              :type="form.is_encrypted ? 'password' : 'text'"
              placeholder="请输入变量值"
            />
          </el-form-item>
          <el-form-item label="描述">
            <el-input
              v-model="form.description"
              type="textarea"
              placeholder="请输入变量描述"
            />
          </el-form-item>
          <el-form-item label="是否加密">
            <el-switch v-model="form.is_encrypted" />
          </el-form-item>
        </el-form>
        <template #footer>
          <span class="dialog-footer">
            <el-button @click="dialogVisible = false">取消</el-button>
            <el-button type="primary" @click="handleSubmit">确定</el-button>
          </span>
        </template>
      </el-dialog>

      <!-- 导入导出功能 -->
      <div class="import-export">
        <el-button type="info" size="small" @click="handleExport">
          <el-icon><Download /></el-icon>
          导出变量
        </el-button>
        <el-upload
          class="upload-btn"
          action=""
          :auto-upload="false"
          :on-change="handleImport"
          :show-file-list="false"
          accept=".json"
        >
          <el-button type="info" size="small">
            <el-icon><Upload /></el-icon>
            导入变量
          </el-button>
        </el-upload>
      </div>

      <!-- 变量调试对话框 -->
      <el-dialog
        v-model="debugDialogVisible"
        title="变量调试"
        width="600px"
      >
        <div class="debug-content">
          <div class="debug-section">
            <h4>测试文本</h4>
            <el-input
              v-model="debugForm.testText"
              type="textarea"
              :rows="3"
              placeholder="输入包含变量的文本，例如：{{base_url}}/api/login?token={{token}}"
            />
          </div>
          <el-divider />
          <div class="debug-section">
            <h4>替换结果</h4>
            <div class="result-box">{{ debugForm.result || '点击下方按钮进行替换' }}</div>
          </div>
          <el-divider />
          <div class="debug-section">
            <h4>可用变量</h4>
            <div class="variable-list">
              <el-tag
                v-for="varItem in variables"
                :key="varItem.id"
                :type="varItem.is_encrypted ? 'warning' : 'info'"
                effect="plain"
                class="variable-tag"
                @click="insertVariable(varItem.name)"
              >
                <span v-text="varItem.name"></span>
              </el-tag>
            </div>
          </div>
        </div>
        <template #footer>
          <span class="dialog-footer">
            <el-button @click="debugDialogVisible = false">取消</el-button>
            <el-button type="primary" @click="handleReplaceVariables">替换变量</el-button>
          </span>
        </template>
      </el-dialog>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox, ElDialog, ElInput, ElButton, ElDivider, ElTag } from 'element-plus'
import { Plus, Download, Upload, Delete, View } from '@element-plus/icons-vue'
import axios from 'axios'

const token = localStorage.getItem('token') || ''
const autoTestRequest = axios.create({
  timeout: 30000,
  headers: token ? { Authorization: `Bearer ${token}` } : {}
})

const variables = ref([])
const dialogVisible = ref(false)
const editingRowId = ref(null)
const selectedVariables = ref([])
const debugDialogVisible = ref(false)
const form = ref({
  name: '',
  value: '',
  description: '',
  is_encrypted: false
})
const editForm = ref({
  value: '',
  description: '',
  is_encrypted: false
})
const debugForm = ref({
  testText: '{{base_url}}/api/login?token={{token}}',
  result: ''
})

// 加载全局变量
const loadVariables = async () => {
  try {
    const res = await autoTestRequest.get('/api/auto-test/global-variables')
    variables.value = res.data || []
  } catch (error) {
    console.error('加载全局变量失败:', error)
    ElMessage.error('加载全局变量失败')
  }
}

// 添加变量
const handleAddVariable = () => {
  form.value = {
    name: '',
    value: '',
    description: '',
    is_encrypted: false
  }
  dialogVisible.value = true
}

// 提交添加
const handleSubmit = async () => {
  if (!form.value.name) {
    ElMessage.warning('请输入变量名')
    return
  }
  if (!form.value.value) {
    ElMessage.warning('请输入变量值')
    return
  }

  try {
    const res = await autoTestRequest.post('/api/auto-test/global-variables', form.value)
    variables.value.push(res.data)
    dialogVisible.value = false
    ElMessage.success('添加成功')
  } catch (error) {
    console.error('添加变量失败:', error)
    ElMessage.error(error.response?.data?.detail || '添加变量失败')
  }
}

// 编辑变量
const handleEdit = (row) => {
  editingRowId.value = row.id
  editForm.value = {
    value: row.value,
    description: row.description,
    is_encrypted: row.is_encrypted
  }
}

// 保存编辑
const handleSaveEdit = async (id) => {
  try {
    const res = await autoTestRequest.put(`/api/auto-test/global-variables/${id}`, editForm.value)
    const index = variables.value.findIndex(v => v.id === id)
    if (index !== -1) {
      variables.value[index] = res.data
    }
    editingRowId.value = null
    ElMessage.success('更新成功')
  } catch (error) {
    console.error('更新变量失败:', error)
    ElMessage.error(error.response?.data?.detail || '更新变量失败')
  }
}

// 删除变量
const handleDelete = async (id) => {
  try {
    await autoTestRequest.delete(`/api/auto-test/global-variables/${id}`)
    variables.value = variables.value.filter(v => v.id !== id)
    ElMessage.success('删除成功')
  } catch (error) {
    console.error('删除变量失败:', error)
    ElMessage.error(error.response?.data?.detail || '删除变量失败')
  }
}

// 导出变量
const handleExport = () => {
  const dataStr = JSON.stringify(variables.value, null, 2)
  const dataBlob = new Blob([dataStr], { type: 'application/json' })
  const url = URL.createObjectURL(dataBlob)
  const link = document.createElement('a')
  link.href = url
  link.download = `global-variables-${new Date().toISOString().slice(0, 10)}.json`
  link.click()
  URL.revokeObjectURL(url)
  ElMessage.success('导出成功')
}

// 导入变量
const handleImport = async (file) => {
  const reader = new FileReader()
  reader.onload = async (e) => {
    try {
      const data = JSON.parse(e.target.result)
      if (!Array.isArray(data)) {
        ElMessage.error('导入文件格式错误')
        return
      }

      const variablesToImport = data.map(item => ({
        name: item.name,
        value: item.value,
        description: item.description || '',
        is_encrypted: item.is_encrypted || false
      }))

      const res = await autoTestRequest.post('/api/auto-test/global-variables/batch', variablesToImport)
      variables.value = [...variables.value, ...res.data]
      ElMessage.success(`成功导入 ${res.data.length} 个变量`)
    } catch (error) {
      console.error('导入变量失败:', error)
      ElMessage.error('导入变量失败')
    }
  }
  reader.readAsText(file.raw)
}

// 处理选择变化
const handleSelectionChange = (selection) => {
  selectedVariables.value = selection
}

// 批量删除
const handleBatchDelete = async () => {
  if (selectedVariables.value.length === 0) {
    ElMessage.warning('请选择要删除的变量')
    return
  }

  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedVariables.value.length} 个变量吗？`,
      '确认删除',
      { confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning' }
    )

    const ids = selectedVariables.value.map(v => v.id)
    await autoTestRequest.delete('/api/auto-test/global-variables/batch', {
      data: ids
    })

    variables.value = variables.value.filter(v => !ids.includes(v.id))
    selectedVariables.value = []
    ElMessage.success('批量删除成功')
  } catch (error) {
    if (error !== 'cancel') {
      console.error('批量删除失败:', error)
      ElMessage.error('批量删除失败')
    }
  }
}

// 组件挂载时加载变量
onMounted(() => {
  loadVariables()
})

// 打开变量调试对话框
const handleDebugVariables = () => {
  debugDialogVisible.value = true
}

// 替换变量
const handleReplaceVariables = () => {
  let result = debugForm.value.testText
  const varMap = new Map()
  
  // 构建变量映射
  variables.value.forEach(varItem => {
    varMap.set(varItem.name, varItem.value)
  })
  
  // 替换变量
  result = result.replace(/\{\{\s*(\w+)\s*\}\}/g, (match, varName) => {
    return varMap.get(varName) || match
  })
  
  debugForm.value.result = result
}

// 插入变量到测试文本
const insertVariable = (varName) => {
  // 直接使用传入的varName，避免Vue将$开头的变量名视为实例属性
  debugForm.value.testText += `{{${varName}}}`
}
</script>

<style scoped>
.global-variable-manager {
  margin: 20px 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.import-export {
  margin-top: 20px;
  display: flex;
  gap: 10px;
}

.upload-btn {
  display: inline-block;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.debug-content {
  padding: 10px 0;
}

.debug-section {
  margin-bottom: 15px;
}

.debug-section h4 {
  margin: 0 0 10px 0;
  font-size: 14px;
  font-weight: 600;
}

.result-box {
  padding: 12px;
  border: 1px solid var(--tm-border-color);
  border-radius: 4px;
  background-color: var(--tm-bg-elevated);
  min-height: 60px;
  white-space: pre-wrap;
  word-break: break-all;
}

.variable-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.variable-tag {
  cursor: pointer;
}

.variable-tag:hover {
  transform: translateY(-2px);
  transition: transform 0.2s;
}
</style>
