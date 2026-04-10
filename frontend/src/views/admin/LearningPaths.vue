<template>
  <div class="learning-paths-manage">
    <div class="page-header">
      <h1 class="page-title">学习路径管理</h1>
      <div class="header-actions">
        <el-button type="primary" @click="handleCreate">
          <el-icon><Plus /></el-icon>
          新增路径
        </el-button>
      </div>
    </div>

    <!-- 筛选区域 -->
    <div class="filter-section">
      <el-form :model="filters" inline>
        <el-form-item label="阶段">
          <el-select v-model="filters.stage" placeholder="全部阶段" clearable>
            <el-option label="阶段1" :value="1" />
            <el-option label="阶段2" :value="2" />
            <el-option label="阶段3" :value="3" />
            <el-option label="阶段4" :value="4" />
            <el-option label="阶段5" :value="5" />
          </el-select>
        </el-form-item>
        <el-form-item label="难度">
          <el-select v-model="filters.difficulty" placeholder="全部难度" clearable>
            <el-option label="初级" value="beginner" />
            <el-option label="中级" value="intermediate" />
            <el-option label="高级" value="advanced" />
          </el-select>
        </el-form-item>
        <el-form-item label="关键词">
          <el-input v-model="filters.keyword" placeholder="搜索路径名称" clearable />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">搜索</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </div>

    <!-- 列表区域 -->
    <div class="table-section">
      <el-table :data="tableData" border style="width: 100%" v-loading="loading">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="title" label="路径名称" min-width="200" />
        <el-table-column prop="stage" label="阶段" width="100">
          <template #default="{ row }">
            <el-tag size="small">阶段{{ row.stage }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="difficulty" label="难度" width="100">
          <template #default="{ row }">
            <el-tag :type="getDifficultyTagType(row.difficulty)" size="small">
              {{ getDifficultyText(row.difficulty) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="estimated_hours" label="预计时长" width="120">
          <template #default="{ row }">
            {{ row.estimated_hours }}小时
          </template>
        </el-table-column>
        <el-table-column prop="exercise_count" label="习题数量" width="100" />
        <el-table-column prop="language" label="语言" width="100" />
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-switch v-model="row.status" active-text="启用" inactive-text="禁用" />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="handleEdit(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="pagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handlePageChange"
          @current-change="handlePageChange"
        />
      </div>
    </div>

    <!-- 编辑弹窗 -->
    <el-dialog v-model="dialogVisible" title="编辑学习路径" width="800px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="路径标题" prop="title" :rules="[
          { required: true, message: '请输入路径标题', trigger: 'blur' }
        ]">
          <el-input v-model="form.title" />
        </el-form-item>
        <el-form-item label="阶段" prop="stage" :rules="[
          { required: true, message: '请选择阶段', trigger: 'change' }
        ]">
          <el-select v-model="form.stage">
            <el-option label="阶段1" :value="1" />
            <el-option label="阶段2" :value="2" />
            <el-option label="阶段3" :value="3" />
            <el-option label="阶段4" :value="4" />
            <el-option label="阶段5" :value="5" />
          </el-select>
        </el-form-item>
        <el-form-item label="难度" prop="difficulty" :rules="[
          { required: true, message: '请选择难度', trigger: 'change' }
        ]">
          <el-select v-model="form.difficulty">
            <el-option label="初级" value="beginner" />
            <el-option label="中级" value="intermediate" />
            <el-option label="高级" value="advanced" />
          </el-select>
        </el-form-item>
        <el-form-item label="预计时长" prop="estimated_hours">
          <el-input v-model.number="form.estimated_hours" type="number" />
        </el-form-item>
        <el-form-item label="语言" prop="language">
          <el-input v-model="form.language" placeholder="例如：Python/Java/通用" />
        </el-form-item>
        <el-form-item label="路径描述" prop="description" :rules="[
          { required: true, message: '请输入路径描述', trigger: 'blur' }
        ]">
          <el-input v-model="form.description" type="textarea" :rows="4" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'

const loading = ref(false)
const dialogVisible = ref(false)
const isEdit = ref(false)

const filters = reactive({
  stage: '',
  difficulty: '',
  keyword: ''
})

const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 50
})

const tableData = ref([
  {
    id: 1,
    title: 'Python自动化测试入门',
    stage: 4,
    difficulty: 'intermediate',
    estimated_hours: 40,
    exercise_count: 20,
    language: 'Python',
    created_at: '2026-03-10 10:00:00',
    status: true
  },
  {
    id: 2,
    title: '接口测试实战',
    stage: 3,
    difficulty: 'beginner',
    estimated_hours: 24,
    exercise_count: 15,
    language: '通用',
    created_at: '2026-03-11 14:30:00',
    status: true
  }
])

const form = ref({
  id: null,
  title: '',
  stage: null,
  difficulty: '',
  estimated_hours: null,
  exercise_count: 0,
  language: '',
  description: '',
  status: true
})

const getDifficultyTagType = (difficulty) => {
  const map = {
    beginner: 'success',
    intermediate: 'warning',
    advanced: 'danger'
  }
  return map[difficulty] || 'info'
}

const getDifficultyText = (difficulty) => {
  const map = {
    beginner: '初级',
    intermediate: '中级',
    advanced: '高级'
  }
  return map[difficulty] || difficulty
}

const handleSearch = () => {
  loading.value = true
  // 实际项目中调用接口搜索
  setTimeout(() => {
    loading.value = false
  }, 500)
}

const handleReset = () => {
  Object.assign(filters, {
    stage: '',
    difficulty: '',
    keyword: ''
  })
  handleSearch()
}

const handlePageChange = () => {
  handleSearch()
}

const handleCreate = () => {
  isEdit.value = false
  form.value = {
    id: null,
    title: '',
    stage: null,
    difficulty: '',
    estimated_hours: null,
    exercise_count: 0,
    language: '',
    description: '',
    status: true
  }
  dialogVisible.value = true
}

const handleEdit = (row) => {
  isEdit.value = true
  form.value = { ...row }
  dialogVisible.value = true
}

const handleDelete = (row) => {
  ElMessageBox.confirm(
    `确定要删除学习路径"${row.title}"吗？`,
    '提示',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(() => {
    ElMessage.success('删除成功')
    handleSearch()
  })
}

const handleSubmit = () => {
  ElMessage.success(isEdit.value ? '更新成功' : '创建成功')
  dialogVisible.value = false
  handleSearch()
}
</script>

<style scoped>
.learning-paths-manage {
  width: 100%;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-title {
  margin: 0;
  font-size: 24px;
  font-weight: bold;
  color: #303133;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.filter-section {
  background: white;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 20px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.table-section {
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.pagination {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}
</style>
