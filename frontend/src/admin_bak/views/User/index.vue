<template>
  <div class="user-manage-page">
    <el-page-header content="用户管理" />
    
    <!-- 操作栏 -->
    <div class="action-bar">
      <el-row :gutter="20">
        <el-col :xs="24" :sm="8">
          <el-input
            v-model="searchQuery"
            placeholder="搜索用户名/邮箱/ID"
            prefix-icon="Search"
            clearable
            @keyup.enter="handleSearch"
          />
        </el-col>
        <el-col :xs="24" :sm="6">
          <el-select v-model="statusFilter" placeholder="状态筛选" clearable>
            <el-option label="正常" value="active" />
            <el-option label="禁用" value="disabled" />
            <el-option label="未激活" value="inactive" />
          </el-select>
        </el-col>
        <el-col :xs="24" :sm="6">
          <el-select v-model="levelFilter" placeholder="等级筛选" clearable>
            <el-option label="初级" value="1" />
            <el-option label="中级" value="2" />
            <el-option label="高级" value="3" />
            <el-option label="专家" value="4" />
          </el-select>
        </el-col>
        <el-col :xs="24" :sm="4">
          <el-button type="primary" @click="handleAdd">
            <el-icon><Plus /></el-icon>
            新增用户
          </el-button>
        </el-col>
      </el-row>
    </div>
    
    <!-- 表格 -->
    <el-card shadow="hover">
      <el-table
        :data="tableData"
        border
        stripe
        v-loading="loading"
      >
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column label="头像" width="80">
          <template #default="scope">
            <el-avatar :size="40" :src="scope.row.avatar">
              <el-icon><User /></el-icon>
            </el-avatar>
          </template>
        </el-table-column>
        <el-table-column prop="username" label="用户名" width="120" />
        <el-table-column prop="email" label="邮箱" min-width="180" />
        <el-table-column prop="level" label="等级" width="100">
          <template #default="scope">
            <el-tag :type="getLevelTag(scope.row.level)">
              Lv.{{ scope.row.level }} {{ getLevelText(scope.row.level) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="score" label="积分" width="80" />
        <el-table-column prop="completedExercises" label="完成习题" width="100" />
        <el-table-column prop="studyTime" label="学习时长(h)" width="120" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="scope">
            <el-tag :type="scope.row.status === 'active' ? 'success' : 'danger'">
              {{ scope.row.status === 'active' ? '正常' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="registerTime" label="注册时间" width="180" />
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="scope">
            <el-button
              size="small"
              type="primary"
              @click="handleEdit(scope.row)"
            >
              编辑
            </el-button>
            <el-button
              size="small"
              :type="scope.row.status === 'active' ? 'warning' : 'success'"
              @click="handleToggleStatus(scope.row)"
            >
              {{ scope.row.status === 'active' ? '禁用' : '启用' }}
            </el-button>
            <el-button
              size="small"
              type="danger"
              @click="handleDelete(scope.row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.size"
          :total="pagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>
    
    <!-- 新增/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="600px"
      destroy-on-close
    >
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="100px"
      >
        <el-form-item label="用户名" prop="username">
          <el-input v-model="formData.username" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="formData.email" placeholder="请输入邮箱" />
        </el-form-item>
        <el-form-item label="密码" prop="password" v-if="!isEdit">
          <el-input
            v-model="formData.password"
            type="password"
            placeholder="请输入初始密码"
            show-password
          />
        </el-form-item>
        <el-form-item label="等级" prop="level">
          <el-select v-model="formData.level" placeholder="请选择用户等级">
            <el-option label="Lv.1 初级" :value="1" />
            <el-option label="Lv.2 中级" :value="2" />
            <el-option label="Lv.3 高级" :value="3" />
            <el-option label="Lv.4 专家" :value="4" />
          </el-select>
        </el-form-item>
        <el-form-item label="积分" prop="score">
          <el-input-number v-model="formData.score" :min="0" :max="99999" />
        </el-form-item>
        <el-form-item label="头像" prop="avatar">
          <el-input v-model="formData.avatar" placeholder="请输入头像URL" />
        </el-form-item>
        <el-form-item label="用户状态" prop="status">
          <el-radio-group v-model="formData.status">
            <el-radio value="active" label="active">正常</el-radio>
            <el-radio value="disabled" label="disabled">禁用</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="管理员权限">
          <el-switch
            v-model="formData.is_admin"
            active-text="是"
            inactive-text="否"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleSubmit" :loading="submitLoading">
            确定
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, User } from '@element-plus/icons-vue'
import { userApi } from '@/admin/api'

const loading = ref(false)
const submitLoading = ref(false)
const dialogVisible = ref(false)
const isEdit = ref(false)

const searchQuery = ref('')
const statusFilter = ref('')
const levelFilter = ref('')

// 分页
const pagination = reactive({
  page: 1,
  size: 10,
  total: 1234
})

// 表格数据
const tableData = ref([
  {
    id: 1,
    username: 'zhangsan',
    email: 'zhangsan@example.com',
    avatar: '',
    level: 2,
    score: 1250,
    completedExercises: 42,
    studyTime: 86,
    status: 'active',
    is_admin: false,
    registerTime: '2026-01-15 10:30:00'
  },
  {
    id: 2,
    username: 'lisi',
    email: 'lisi@example.com',
    avatar: '',
    level: 3,
    score: 3480,
    completedExercises: 128,
    studyTime: 245,
    status: 'active',
    is_admin: true,
    registerTime: '2026-01-20 14:20:00'
  },
  {
    id: 3,
    username: 'wangwu',
    email: 'wangwu@example.com',
    avatar: '',
    level: 1,
    score: 320,
    completedExercises: 15,
    studyTime: 28,
    status: 'disabled',
    is_admin: false,
    registerTime: '2026-02-05 09:15:00'
  },
  {
    id: 4,
    username: 'zhaoliu',
    email: 'zhaoliu@example.com',
    avatar: '',
    level: 4,
    score: 8950,
    completedExercises: 356,
    studyTime: 620,
    status: 'active',
    is_admin: false,
    registerTime: '2026-02-10 16:45:00'
  }
])

// 表单数据
const formRef = ref()
const formData = reactive({
  username: '',
  email: '',
  password: '',
  level: 1,
  score: 0,
  avatar: '',
  status: 'active',
  is_admin: false
})

const formRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度在3到20个字符', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于6个字符', trigger: 'blur' }
  ],
  level: [
    { required: true, message: '请选择用户等级', trigger: 'change' }
  ]
}

const dialogTitle = computed(() => isEdit.value ? '编辑用户' : '新增用户')

const getLevelTag = (level) => {
  const map = {
    1: 'success',
    2: 'warning',
    3: 'danger',
    4: 'info'
  }
  return map[level] || 'info'
}

const getLevelText = (level) => {
  const map = {
    1: '初级',
    2: '中级',
    3: '高级',
    4: '专家'
  }
  return map[level] || '未知'
}

const handleSearch = async () => {
  loading.value = true
  try {
    // 调用搜索API
    // const res = await userApi.list({
    //   page: pagination.page,
    //   size: pagination.size,
    //   keyword: searchQuery.value,
    //   status: statusFilter.value,
    //   level: levelFilter.value
    // })
    // tableData.value = res.data.list
    // pagination.total = res.data.total
    
    ElMessage.success('搜索完成')
  } catch (error) {
    ElMessage.error('搜索失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

const handleAdd = () => {
  isEdit.value = false
  Object.assign(formData, {
    username: '',
    email: '',
    password: '',
    level: 1,
    score: 0,
    avatar: '',
    status: 'active',
    is_admin: false
  })
  dialogVisible.value = true
}

const handleEdit = (row) => {
  isEdit.value = true
  Object.assign(formData, row)
  dialogVisible.value = true
}

const handleToggleStatus = async (row) => {
  const action = row.status === 'active' ? '禁用' : '启用'
  await ElMessageBox.confirm(
    `确定要${action}用户「${row.username}」吗？`,
    '提示',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  )
  
  try {
    // 调用状态切换API
    // await userApi.toggleStatus(row.id, row.status === 'active' ? 'disabled' : 'active')
    
    row.status = row.status === 'active' ? 'disabled' : 'active'
    ElMessage.success(`${action}成功`)
  } catch (error) {
    ElMessage.error('操作失败，请稍后重试')
  }
}

const handleDelete = async (row) => {
  await ElMessageBox.confirm(
    `确定要删除用户「${row.username}」吗？删除后无法恢复！`,
    '提示',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  )
  
  try {
    // 调用删除API
    // await userApi.delete(row.id)
    
    const index = tableData.value.findIndex(item => item.id === row.id)
    if (index > -1) {
      tableData.value.splice(index, 1)
    }
    ElMessage.success('删除成功')
  } catch (error) {
    ElMessage.error('删除失败，请稍后重试')
  }
}

const handleSubmit = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (valid) {
      submitLoading.value = true
      
      try {
        if (isEdit.value) {
          // 调用编辑API
          // await userApi.update(formData.id, formData)
          
          const index = tableData.value.findIndex(item => item.id === formData.id)
          if (index > -1) {
            tableData.value[index] = { ...tableData.value[index], ...formData }
          }
          ElMessage.success('编辑成功')
        } else {
          // 调用新增API
          // const res = await userApi.create(formData)
          
          const newItem = {
            ...formData,
            id: tableData.value.length + 1,
            completedExercises: 0,
            studyTime: 0,
            registerTime: new Date().toISOString().slice(0, 19).replace('T', ' ')
          }
          tableData.value.unshift(newItem)
          ElMessage.success('新增成功')
        }
        
        dialogVisible.value = false
      } catch (error) {
        ElMessage.error('操作失败，请稍后重试')
      } finally {
        submitLoading.value = false
      }
    }
  })
}

const handleSizeChange = (size) => {
  pagination.size = size
  handleSearch()
}

const handlePageChange = (page) => {
  pagination.page = page
  handleSearch()
}
</script>

<style scoped lang="scss">
.user-manage-page {
  .action-bar {
    margin: 20px 0;
  }
  
  .pagination-container {
    display: flex;
    justify-content: flex-end;
    margin-top: 20px;
  }
}
</style>
