<template>
  <div class="env-manager">
    <div class="container">
      <!-- 返回按钮 -->
      <div class="back-bar">
        <el-button link @click="goBack">
          <el-icon><ArrowLeft /></el-icon>
          返回接口测试
        </el-button>
      </div>

      <!-- 头部 -->
      <div class="header-bar">
        <h1 class="page-title">环境管理</h1>
        <el-button type="primary" @click="createEnv">
          <el-icon><Plus /></el-icon>
          新建环境
        </el-button>
      </div>

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
              {{ env.name }}
              <el-tag v-if="env.is_default" type="success" size="small">默认</el-tag>
            </div>
            <el-button-group>
              <el-button size="small" @click="editEnv(env)">编辑</el-button>
              <el-button size="small" type="danger" @click="deleteEnv(env)">删除</el-button>
            </el-button-group>
          </div>
          <div class="env-base-url">
            <span class="label">基础URL：</span>
            <code>{{ env.base_url || '(空)' }}</code>
          </div>
          <div v-if="Object.keys(env.variables || {}).length > 0" class="variables">
            <div class="label">变量：</div>
            <div class="var-list">
              <div class="var-item" v-for="(value, key) in env.variables" :key="key">
                <span class="var-key">{{ key }}</span>
                <span class="var-value">{{ value }}</span>
              </div>
            </div>
          </div>
          <div v-else class="no-vars">暂无变量</div>
        </el-card>
      </div>

      <!-- 新建/编辑弹窗 -->
      <el-dialog
        v-model="dialogVisible"
        :title="isEdit ? '编辑环境' : '新建环境'"
        width="600px"
      >
        <el-form :model="formData" label-width="80px">
          <el-form-item label="环境名称" required>
            <el-input v-model="formData.name" placeholder="例如：开发环境" />
          </el-form-item>
          <el-form-item label="基础URL">
            <el-input v-model="formData.base_url" placeholder="例如：http://dev-api.example.com" />
          </el-form-item>
          <el-form-item label="设为默认">
            <el-switch v-model="formData.is_default" />
          </el-form-item>
          <div class="section-title">环境变量</div>
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
            <el-button type="primary" @click="saveEnv">
              {{ isEdit ? '保存修改' : '创建' }}
            </el-button>
          </span>
        </template>
      </el-dialog>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowLeft, Plus, Delete } from '@element-plus/icons-vue'
import request from '@/utils/request'
import { ElMessage, ElMessageBox } from 'element-plus'

const router = useRouter()
const environments = ref([])
const dialogVisible = ref(false)
const isEdit = ref(false)
const editingId = ref(null)

const formData = reactive({
  name: '',
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
  formData.variables = obj
}

const fetchEnvs = async () => {
  try {
    const res = await request.get('/interface-test/environments')
    environments.value = res.data || res
  } catch (err) {
    console.error('获取环境列表失败:', err)
    ElMessage.error('获取环境列表失败')
  }
}

const createEnv = () => {
  isEdit.value = false
  editingId.value = null
  formData.name = ''
  formData.base_url = ''
  formData.is_default = false
  formData.variables = {}
  vars.value = [{ key: '', value: '' }]
  dialogVisible.value = true
}

const editEnv = (env) => {
  isEdit.value = true
  editingId.value = env.id
  formData.name = env.name
  formData.base_url = env.base_url || ''
  formData.is_default = env.is_default
  formData.variables = { ...(env.variables || {}) }

  // 转换为数组
  const entries = Object.entries(formData.variables)
  if (entries.length === 0) {
    vars.value = [{ key: '', value: '' }]
  } else {
    vars.value = entries.map(([key, value]) => ({ key, value }))
  }
  dialogVisible.value = true
}

const saveEnv = async () => {
  if (!formData.name.trim()) {
    ElMessage.warning('请输入环境名称')
    return
  }
  collectVars()

  try {
    if (isEdit.value) {
      await request.put(`/interface-test/environments/${editingId.value}`, formData)
      ElMessage.success('修改成功')
    } else {
      await request.post('/interface-test/environments', formData)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    fetchEnvs()
  } catch (err) {
    console.error('保存失败:', err)
    ElMessage.error('保存失败')
  }
}

const deleteEnv = async (env) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除环境 "${env.name}" 吗？`,
      '确认删除',
      { confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning' }
    )
    await request.delete(`/interface-test/environments/${env.id}`)
    ElMessage.success('删除成功')
    fetchEnvs()
  } catch {
  }
}

const goBack = () => {
  router.push('/interface-test')
}

onMounted(() => {
  fetchEnvs()
})
</script>

<style scoped>
.env-manager {
  padding: 20px 0 40px;
  min-height: calc(100vh - 60px);
  background-color: #f5f7fa;
}

.container {
  max-width: 1000px;
  margin: 0 auto;
  padding: 0 20px;
}

.back-bar {
  margin-bottom: 16px;
}

.header-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-title {
  font-size: 28px;
  font-weight: bold;
  margin: 0;
}

.env-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: 16px;
}

.env-card {
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
  }
}

.env-base-url {
  margin-bottom: 12px;
}

.label {
  font-weight: 600;
  color: #606266;
}

.env-base-url code {
  background: #f5f7fa;
  padding: 2px 6px;
  border-radius: 4px;
  color: #409eff;
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

.no-vars {
  color: #909399;
  font-size: 14px;
  margin-top: 8px;
}

.section-title {
  font-weight: 600;
  margin-bottom: 12px;
  color: #303133;
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
</style>
