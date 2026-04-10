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
      <el-empty v-if="environments.length === 0 && !loading" description="暂无环境，点击上方按钮创建" />
    </div>

    <!-- 创建/编辑弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑环境' : '新建环境'"
      width="550px"
    >
      <el-form :model="formData" label-width="80px">
        <el-form-item label="环境名称" required>
          <el-input v-model="formData.name" placeholder="例如：开发环境" />
        </el-form-item>
        <el-form-item label="基础URL">
          <el-input v-model="formData.base_url" placeholder="例如：http://localhost:5000" />
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
import { Plus } from '@element-plus/icons-vue'
import request from '@/utils/request'
import { ElMessage, ElMessageBox } from 'element-plus'

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
  formData.value.variables = obj
}

const fetchEnvs = async () => {
  loading.value = true
  try {
    const res = await request.get('/interface-test/environments')
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
    name: '',
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
    name: env.name,
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
  if (!formData.value.name.trim()) {
    ElMessage.warning('请输入环境名称')
    return
  }
  collectVars()

  try {
    if (isEdit.value) {
      await request.put(`/interface-test/environments/${editingId.value}`, formData.value)
      ElMessage.success('修改成功')
    } else {
      await request.post('/interface-test/environments', formData.value)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    fetchEnvs()
  } catch (err) {
    console.error('保存失败:', err)
    ElMessage.error('保存失败')
  }
}

const handleDelete = async (env) => {
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
    // 取消
  }
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
</style>
