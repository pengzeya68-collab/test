<template>
  <div class="exercises-manage">
    <div class="page-header">
      <h1 class="page-title">习题管理</h1>
      <div class="header-actions">
        <el-button type="primary" @click="handleCreate">
          <el-icon><Plus /></el-icon>
          新增习题
        </el-button>
        <el-button type="success" @click="handleImport">
          <el-icon><Upload /></el-icon>
          批量导入
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
            <el-option label="简单" value="easy" />
            <el-option label="中等" value="medium" />
            <el-option label="困难" value="hard" />
          </el-select>
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="filters.type" placeholder="全部类型" clearable>
            <el-option label="文本题" value="text" />
            <el-option label="代码题" value="code" />
          </el-select>
        </el-form-item>
        <el-form-item label="关键词">
          <el-input v-model="filters.keyword" placeholder="搜索习题名称" clearable />
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
        <el-table-column prop="title" label="习题名称" min-width="200" />
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
        <el-table-column prop="type" label="类型" width="100">
          <template #default="{ row }">
            <el-tag size="small">{{ row.exercise_type === 'code' ? '代码题' : '文本题' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="knowledge_point" label="知识点" min-width="150" />
        <el-table-column prop="created_at" label="创建时间" width="180" />
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
    <el-dialog v-model="dialogVisible" title="编辑习题" width="800px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="习题标题" prop="title" :rules="[
          { required: true, message: '请输入习题标题', trigger: 'blur' }
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
            <el-option label="简单" value="easy" />
            <el-option label="中等" value="medium" />
            <el-option label="困难" value="hard" />
          </el-select>
        </el-form-item>
        <el-form-item label="类型" prop="exercise_type" :rules="[
          { required: true, message: '请选择类型', trigger: 'change' }
        ]">
          <el-select v-model="form.exercise_type">
            <el-option label="文本题" value="text" />
            <el-option label="代码题" value="code" />
          </el-select>
        </el-form-item>
        <el-form-item label="知识点" prop="knowledge_point">
          <el-input v-model="form.knowledge_point" />
        </el-form-item>
        <el-form-item label="题目描述" prop="description" :rules="[
          { required: true, message: '请输入题目描述', trigger: 'blur' }
        ]">
          <el-input v-model="form.description" type="textarea" :rows="4" />
        </el-form-item>
        <el-form-item label="参考答案" prop="solution" :rules="[
          { required: true, message: '请输入参考答案', trigger: 'blur' }
        ]">
          <el-input v-model="form.solution" type="textarea" :rows="6" />
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
import { Plus, Upload } from '@element-plus/icons-vue'

const loading = ref(false)
const dialogVisible = ref(false)
const isEdit = ref(false)

const filters = reactive({
  stage: '',
  difficulty: '',
  type: '',
  keyword: ''
})

const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 100
})

const tableData = ref([
  {
    id: 1,
    title: 'SQL基础查询',
    stage: 1,
    difficulty: 'easy',
    exercise_type: 'code',
    knowledge_point: 'SQL基础',
    created_at: '2026-03-10 10:00:00'
  },
  {
    id: 2,
    title: '测试用例设计方法',
    stage: 2,
    difficulty: 'medium',
    exercise_type: 'text',
    knowledge_point: '功能测试',
    created_at: '2026-03-11 14:30:00'
  }
])

const form = ref({
  id: null,
  title: '',
  stage: null,
  difficulty: '',
  exercise_type: '',
  knowledge_point: '',
  description: '',
  solution: ''
})

const getDifficultyTagType = (difficulty) => {
  const map = {
    easy: 'success',
    medium: 'warning',
    hard: 'danger'
  }
  return map[difficulty] || 'info'
}

const getDifficultyText = (difficulty) => {
  const map = {
    easy: '简单',
    medium: '中等',
    hard: '困难'
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
    type: '',
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
    exercise_type: '',
    knowledge_point: '',
    description: '',
    solution: ''
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
    `确定要删除习题"${row.title}"吗？`,
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

const handleImport = () => {
  ElMessage.info('批量导入功能开发中')
}
</script>

<style scoped>
.exercises-manage {
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
