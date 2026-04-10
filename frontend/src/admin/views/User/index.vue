<template>
  <div class="user-management-theme">
    <h1 class="page-title">用户管理</h1>

    <!-- 操作栏 -->
    <div class="toolbar-card">
      <div class="toolbar-left">
        <el-button type="primary" @click="handleAdd" class="btn-primary">
          <el-icon><Plus /></el-icon>
          新增用户
        </el-button>
      </div>
      <div class="toolbar-right">
        <el-input
          v-model="keyword"
          placeholder="搜索用户名/邮箱"
          class="search-input"
        />
        <el-select v-model="statusFilter" placeholder="状态筛选" class="filter-select">
          <el-option label="全部" value="" />
          <el-option label="正常" value="active" />
          <el-option label="禁用" value="disabled" />
        </el-select>
        <el-button @click="handleSearch" class="btn-search">
          搜索
        </el-button>
      </div>
    </div>

    <!-- 用户列表 -->
    <div class="list-card">
      <el-table :data="list" border stripe class="dark-table">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="username" label="用户名" min-width="120" />
        <el-table-column prop="email" label="邮箱" min-width="200" />
        <el-table-column prop="level" label="等级" width="80" />
        <el-table-column prop="score" label="积分" width="100" />
        <el-table-column prop="completedExercises" label="完成习题" width="100" />
        <el-table-column prop="studyTime" label="学习时长(h)" width="120" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'danger'">
              {{ row.status === 'active' ? '正常' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="is_admin" label="管理员" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_admin ? 'primary' : 'info'">
              {{ row.is_admin ? '是' : '否' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="registerTime" label="注册时间" width="160" />
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-dropdown trigger="click">
              <el-button type="primary" size="small" plain class="btn-operation">
                操作 <el-icon class="el-icon--right"><ArrowDown /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item @click="handleEdit(row)">
                    <el-icon><Edit /></el-icon> 编辑
                  </el-dropdown-item>
                  <el-dropdown-item @click="handleResetPassword(row)">
                    🔑 重置密码
                  </el-dropdown-item>
                  <el-dropdown-item
                    @click="toggleStatus(row)"
                    :style="{ color: row.status === 'active' ? '#E6A23C' : '#67C23A' }"
                  >
                    <el-icon :color="row.status === 'active' ? '#E6A23C' : '#67C23A'">
                      {{ row.status === 'active' ? '🔴' : '🟢' }}
                    </el-icon>
                    {{ row.status === 'active' ? '禁用用户' : '启用用户' }}
                  </el-dropdown-item>
                  <el-dropdown-item
                    @click="toggleAdmin(row)"
                    :style="{ color: row.is_admin ? '#909399' : '#409EFF' }"
                    :disabled="row.id === currentAdminId"
                  >
                    <el-icon :color="row.is_admin ? '#909399' : '#409EFF'">
                      {{ row.is_admin ? '👤' : '👑' }}
                    </el-icon>
                    {{ row.is_admin ? '取消管理员' : '设为管理员' }}
                  </el-dropdown-item>
                  <el-dropdown-item divided @click="handleDelete(row)" style="color: #F56C6C;">
                    <el-icon color="#F56C6C"><Delete /></el-icon> 删除
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="size"
          :total="total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="fetchList"
          @current-change="fetchList"
          class="dark-pagination"
        />
      </div>
    </div>

    <!-- 编辑弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑用户' : '新增用户'"
      width="520px"
      custom-class="dark-dialog"
    >
      <el-form :model="form" label-width="100px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" placeholder="请输入用户名" class="dark-input" />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="form.email" placeholder="请输入邮箱" class="dark-input" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="form.password" type="password" placeholder="请输入密码" class="dark-input" />
          <div style="font-size: 12px; color: #888; margin-top: 6px;">编辑时不填则保持原密码</div>
        </el-form-item>
        <el-form-item label="等级" prop="level">
          <el-input-number v-model="form.level" :min="1" :max="10" />
        </el-form-item>
        <el-form-item label="积分" prop="score">
          <el-input-number v-model="form.score" :min="0" />
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-radio-group v-model="form.status">
            <el-radio value="active" label="active" class="dark-radio">正常</el-radio>
            <el-radio value="disabled" label="disabled" class="dark-radio">禁用</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="管理员" prop="is_admin">
          <el-switch v-model="form.is_admin" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false" class="btn-cancel">取消</el-button>
        <el-button type="primary" @click="handleSubmit" class="btn-primary">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowDown, Edit, Delete, Plus } from '@element-plus/icons-vue'
import request from '@/utils/request'

const keyword = ref('')
const statusFilter = ref('')
const page = ref(1)
const size = ref(10)
const total = ref(0)
const list = ref([])
const dialogVisible = ref(false)
const isEdit = ref(false)
const currentAdminId = computed(() => {
  const user = localStorage.getItem('user')
  return user ? JSON.parse(user).id : 0
})

const form = reactive({
  id: null,
  username: '',
  email: '',
  password: '',
  level: 1,
  score: 0,
  status: 'active',
  is_admin: false
})

const fetchList = async () => {
  try {
    const res = await request.get('/admin/users', {
      params: {
        page: page.value,
        size: size.value,
        keyword: keyword.value,
        status: statusFilter.value
      }
    })
    if (res && res.list) {
      list.value = res.list
      total.value = res.total
    } else {
      list.value = []
      total.value = 0
    }
  } catch (e) {
    console.error('获取用户列表失败:', e)
    ElMessage.error('获取列表失败')
  }
}

const handleSearch = () => {
  page.value = 1
  fetchList()
}

const handleAdd = () => {
  isEdit.value = false
  Object.keys(form).forEach(key => {
    form[key] = key === 'id' ? null :
               key === 'level' ? 1 :
               key === 'score' ? 0 :
               key === 'status' ? 'active' :
               key === 'is_admin' ? false : ''
  })
  dialogVisible.value = true
}

const handleEdit = (row) => {
  isEdit.value = true
  Object.assign(form, row)
  dialogVisible.value = true
}

const handleSubmit = async () => {
  try {
    if (isEdit.value) {
      await request.put(`/admin/users/${form.id}`, form)
      ElMessage.success('更新成功')
    } else {
      await request.post('/admin/users', form)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    fetchList()
  } catch (e) {
    console.error('提交失败:', e)
    ElMessage.error('操作失败：' + (e.response?.data?.error || e.message))
  }
}

const toggleStatus = async (row) => {
  const newStatus = row.status === 'active' ? 'disabled' : 'active'
  const actionText = newStatus === 'active' ? '启用' : '禁用'

  try {
    await ElMessageBox.confirm(
      `确定要${actionText}用户【${row.username}】吗？`,
      '提示',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await request.post(`/admin/users/${row.id}/toggle-status`)

    ElMessage.success(`用户已${actionText}`)
    fetchList()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('操作失败：' + (e.response?.data?.error || e.message))
    }
  }
}

const toggleAdmin = async (row) => {
  const newAdminStatus = !row.is_admin
  const actionText = newAdminStatus ? '设置为管理员' : '取消管理员权限'

  try {
    await ElMessageBox.confirm(
      `确定要${actionText}【${row.username}】吗？`,
      '提示',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await request.post(`/admin/users/${row.id}/toggle-admin`)

    ElMessage.success(`用户已${actionText}`)
    fetchList()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('操作失败：' + (e.response?.data?.error || e.message))
    }
  }
}

const handleResetPassword = async (row) => {
  try {
    const { value: newPassword } = await ElMessageBox.prompt(
      `请输入用户【${row.username}】的新密码`,
      '重置密码',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        inputPattern: /^.{6,}$/,
        inputErrorMessage: '密码长度不能少于6位'
      }
    )

    if (newPassword) {
      await request.put(`/admin/users/${row.id}/reset-password`, {
        new_password: newPassword
      })
      ElMessage.success('密码重置成功')
    }
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('重置失败：' + (e.response?.data?.error || e.message))
    }
  }
}

const handleDelete = async (row) => {
  if (row.id === currentAdminId.value) {
    ElMessage.error('不能删除自己的账号')
    return
  }

  try {
    await ElMessageBox.confirm(
      `确定要删除用户【${row.username}】吗？删除后无法恢复！`,
      '提示',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'danger'
      }
    )

    await request.delete(`/admin/users/${row.id}`)
    ElMessage.success('删除成功')
    fetchList()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('删除失败：' + (e.response?.data?.error || e.message))
    }
  }
}

onMounted(() => {
  fetchList()
})
</script>

<style scoped>
.user-management-dark {
  width: 100%;
}

.page-title {
  margin: 0 0 20px 0;
  font-size: 28px;
  font-weight: 700;
  color: var(--tm-text-primary);
  letter-spacing: 0.5px;
}

.toolbar-card {
  background: var(--tm-card-bg);
  border-radius: 12px;
  padding: 16px 20px;
  margin-bottom: 20px;
  border: var(--tm-card-border);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.toolbar-left {
  display: flex;
  gap: 12px;
}

.toolbar-right {
  display: flex;
  gap: 12px;
  align-items: center;
}

.search-input {
  width: 250px;
}

.search-input :deep(.el-input__wrapper) {
  background: var(--tm-card-bg);
  box-shadow: 0 0 0 1px var(--tm-border-light) inset;
  border-radius: 8px;
}

.search-input :deep(.el-input__inner) {
  color: var(--tm-text-primary);
}

.filter-select {
  width: 140px;
}

.filter-select :deep(.el-input__wrapper) {
  background: var(--tm-card-bg);
  box-shadow: 0 0 0 1px var(--tm-border-light) inset;
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

.btn-search {
  color: var(--tm-color-primary);
  border: 1px solid var(--tm-color-primary);
  background: transparent;
}

.btn-search:hover {
  background: rgba(var(--tm-color-primary), 0.1);
}

.list-card {
  background: var(--tm-card-bg);
  border-radius: 12px;
  padding: 20px;
  border: var(--tm-card-border);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
}

.pagination-wrapper {
  margin-top: 20px;
  text-align: right;
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
  background-color: rgba(var(--tm-color-primary), 0.08);
}

.btn-operation {
  border-color: var(--tm-color-primary);
  color: var(--tm-color-primary);
}

.dark-input :deep(.el-input__wrapper) {
  background: var(--tm-card-bg);
  box-shadow: 0 0 0 1px var(--tm-border-light) inset;
  border-radius: 6px;
}

.dark-input :deep(.el-input__inner) {
  color: var(--tm-text-primary);
}

.btn-cancel {
  color: var(--tm-text-secondary);
  background: transparent;
  border: 1px solid var(--tm-border-light);
}

.btn-cancel:hover {
  color: var(--tm-text-primary);
  border-color: var(--tm-primary-color);
}

.dark-pagination :deep(.el-pagination) {
  color: var(--tm-text-secondary);
}

.dark-pagination :deep(.el-pagination button) {
  background: var(--tm-card-bg);
  border-color: var(--tm-border-light);
  color: var(--tm-text-secondary);
}

.dark-pagination :deep(.el-pagination .el-pager li) {
  color: var(--tm-text-secondary);
}

.dark-pagination :deep(.el-pagination .el-pager li.active) {
  color: var(--tm-color-primary);
  background: rgba(var(--tm-color-primary), 0.1);
}

.dark-pagination :deep(.el-pagination .el-pager li:hover) {
  color: var(--tm-color-primary);
}
</style>
