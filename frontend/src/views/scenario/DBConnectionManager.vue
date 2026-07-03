<template>
  <div class="db-connection-manager">
    <div class="actions-bar">
      <el-button type="primary" @click="handleCreate">
        <el-icon><Plus /></el-icon>
        新建连接
      </el-button>
    </div>

    <!-- 连接列表 -->
    <div class="connection-list">
      <el-card
        v-for="conn in connections"
        :key="conn.id"
        class="conn-card"
        shadow="hover"
      >
        <div class="conn-header">
          <div class="conn-name">
            <el-tag :type="getDbTypeTag(conn.db_type)" size="small" effect="dark">{{ conn.db_type.toUpperCase() }}</el-tag>
            {{ conn.name }}
            <el-tag v-if="!conn.is_active" type="info" size="small">停用</el-tag>
            <el-tag v-if="conn.has_password && conn.password_decryptable === false" type="danger" size="small" effect="plain">
              ⚠️ 密码需重新输入
            </el-tag>
          </div>
          <el-button-group>
            <el-button size="small" @click="handleTest(conn)" :loading="testingId === conn.id">测试</el-button>
            <el-button size="small" @click="handleEdit(conn)">编辑</el-button>
            <el-button size="small" type="danger" @click="handleDelete(conn)">删除</el-button>
          </el-button-group>
        </div>
        <div class="conn-info">
          <span>{{ conn.host }}:{{ conn.port }}</span>
          <span v-if="conn.database_name"> / {{ conn.database_name }}</span>
          <span v-if="conn.username"> ({{ conn.username }})</span>
        </div>
        <el-alert
          v-if="conn.has_password && conn.password_decryptable === false"
          type="warning"
          :closable="false"
          show-icon
          style="margin-top: 8px;"
          title="密码解密失败"
          description="该连接的密码可能因加密密钥更换而无法解密。请点击「编辑」重新输入密码后保存。"
        />
      </el-card>
    </div>

    <el-empty v-if="connections.length === 0 && !loading" description="暂无数据库连接" />

    <!-- 创建/编辑弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑连接' : '新建连接'"
      width="500px"
      append-to-body
      destroy-on-close
    >
      <el-form :model="formData" label-width="100px">
        <el-form-item label="连接名称" required>
          <el-input v-model="formData.name" placeholder="如：测试环境 PG" />
        </el-form-item>
        <el-form-item label="数据库类型" required>
          <el-select v-model="formData.db_type" style="width: 100%">
            <el-option label="PostgreSQL" value="postgresql" />
            <el-option label="MySQL" value="mysql" />
            <el-option label="Redis" value="redis" />
          </el-select>
        </el-form-item>
        <el-form-item label="主机地址" required>
          <el-input v-model="formData.host" placeholder="127.0.0.1" />
        </el-form-item>
        <el-form-item label="端口" required>
          <el-input-number v-model="formData.port" :min="1" :max="65535" style="width: 100%" />
        </el-form-item>
        <el-form-item label="数据库名" v-if="formData.db_type !== 'redis'">
          <el-input v-model="formData.database_name" placeholder="数据库名" />
        </el-form-item>
        <el-form-item label="用户名" v-if="formData.db_type !== 'redis'">
          <el-input v-model="formData.username" placeholder="用户名" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="formData.password" type="password" show-password placeholder="密码（编辑时留空表示不修改）" />
        </el-form-item>
        <el-form-item label="启用">
          <el-switch v-model="formData.is_active" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSave">
          {{ isEdit ? '保存修改' : '创建' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Plus } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import autoTestRequest from '@/utils/autoTestRequest'

const connections = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const isEdit = ref(false)
const editingId = ref(null)
const editingConn = ref(null)
const testingId = ref(null)

const DEFAULT_PORTS = { postgresql: 5432, mysql: 3306, redis: 6379 }

const formData = ref({
  name: '',
  db_type: 'postgresql',
  host: '127.0.0.1',
  port: 5432,
  database_name: '',
  username: '',
  password: '',
  is_active: true,
})

const getDbTypeTag = (type) => {
  const map = { postgresql: 'success', mysql: 'warning', redis: 'danger' }
  return map[type] || 'info'
}

// 监听 db_type 变化自动更新默认端口（仅在端口未被自定义时）
watch(() => formData.value.db_type, (newType) => {
  const allDefaultPorts = Object.values(DEFAULT_PORTS)
  if (allDefaultPorts.includes(formData.value.port)) {
    formData.value.port = DEFAULT_PORTS[newType] || 5432
  }
})

const fetchConnections = async () => {
  loading.value = true
  try {
    const res = await autoTestRequest.get('/auto-test/db-connections')
    connections.value = Array.isArray(res) ? res : []
  } catch (err) {
    console.error('获取数据库连接失败:', err)
  } finally {
    loading.value = false
  }
}

const handleCreate = () => {
  isEdit.value = false
  editingId.value = null
  formData.value = {
    name: '',
    db_type: 'postgresql',
    host: '127.0.0.1',
    port: 5432,
    database_name: '',
    username: '',
    password: '',
    is_active: true,
  }
  dialogVisible.value = true
}

const handleEdit = (conn) => {
  isEdit.value = true
  editingId.value = conn.id
  editingConn.value = conn
  formData.value = {
    name: conn.name,
    db_type: conn.db_type,
    host: conn.host,
    port: conn.port,
    database_name: conn.database_name || '',
    username: conn.username || '',
    password: '',
    is_active: conn.is_active,
  }
  dialogVisible.value = true
  if (conn.has_password && conn.password_decryptable === false) {
    ElMessage.warning('该连接密码解密失败,请重新输入密码后保存')
  }
}

const handleSave = async () => {
  if (!formData.value.name?.trim()) {
    ElMessage.warning('请输入连接名称')
    return
  }

  // 编辑模式下,如果原密码解密失败,必须输入新密码
  if (isEdit.value && editingConn.value?.has_password && editingConn.value?.password_decryptable === false && !formData.value.password) {
    ElMessage.warning('该连接密码已失效,必须重新输入密码')
    return
  }

  const payload = { ...formData.value }
  // 编辑模式下，密码为空表示不修改，移除 password 字段避免被后端当作新密码保存
  if (isEdit.value && !payload.password) {
    delete payload.password
  }

  try {
    if (isEdit.value) {
      await autoTestRequest.put(`/auto-test/db-connections/${editingId.value}`, payload)
      ElMessage.success('修改成功')
    } else {
      await autoTestRequest.post('/auto-test/db-connections', payload)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    fetchConnections()
  } catch (err) {
    ElMessage.error('保存失败: ' + (err.response?.data?.detail || err.message))
  }
}

const handleDelete = async (conn) => {
  try {
    await ElMessageBox.confirm(`确定删除连接 "${conn.name}" 吗？`, '确认', { type: 'warning' })
    await autoTestRequest.delete(`/auto-test/db-connections/${conn.id}`)
    ElMessage.success('删除成功')
    fetchConnections()
  } catch {
    // cancelled
  }
}

const handleTest = async (conn) => {
  testingId.value = conn.id
  try {
    const res = await autoTestRequest.post(`/auto-test/db-connections/${conn.id}/test`)
    if (res.success) {
      ElMessage.success(`连接成功 (${res.elapsed_ms}ms)`)
    } else {
      ElMessage.error(`连接失败: ${res.message}`)
    }
  } catch (err) {
    ElMessage.error('测试失败: ' + (err.response?.data?.detail || err.message))
  } finally {
    testingId.value = null
  }
}

onMounted(() => {
  fetchConnections()
})
</script>

<style scoped>
.db-connection-manager {
  padding: 0;
}

.actions-bar {
  margin-bottom: 16px;
  text-align: right;
}

.connection-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.conn-card {
  background: var(--tm-card-bg);
  border: var(--tm-card-border);
}

.conn-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.conn-name {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: var(--tm-text-primary);
}

.conn-info {
  margin-top: 8px;
  font-size: 13px;
  color: var(--tm-text-secondary);
  font-family: monospace;
}
</style>
