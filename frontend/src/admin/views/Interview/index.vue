<template>
  <div class="interview-management-dark">
    <h1 class="page-title">面试题库管理</h1>

    <!-- 操作栏 -->
    <div class="toolbar-card">
      <div class="toolbar-left">
        <el-button type="primary" @click="handleAdd" class="btn-primary">
          <el-icon><Plus /></el-icon>
          新增题目
        </el-button>
        <el-button type="warning" @click="handleGenerateAnswers" :loading="generating" class="btn-warning">
          🤖 AI生成参考答案
        </el-button>
      </div>
      <div class="toolbar-right">
        <el-input
          v-model="keyword"
          placeholder="搜索题目标题/内容"
          class="search-input"
          clearable
          @clear="fetchList"
          @keyup.enter="fetchList"
        />
        <el-select v-model="filterCategory" placeholder="按分类筛选" class="filter-select" clearable @change="fetchList">
          <el-option v-for="c in categories" :key="c" :label="c" :value="c" />
        </el-select>
        <el-select v-model="filterDifficulty" placeholder="按难度筛选" class="filter-select" clearable @change="fetchList">
          <el-option label="简单" value="easy" />
          <el-option label="中等" value="medium" />
          <el-option label="困难" value="hard" />
        </el-select>
        <el-button @click="fetchList" class="btn-search">搜索</el-button>
      </div>
    </div>

    <!-- 列表 -->
    <div class="list-card">
      <el-table :data="list" border stripe v-loading="loading" class="dark-table">
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="title" label="题目标题" min-width="260" show-overflow-tooltip />
        <el-table-column prop="category" label="分类" width="110" />
        <el-table-column prop="difficulty" label="难度" width="80">
          <template #default="{ row }">
            <el-tag :type="difficultyTag(row.difficulty)" size="small">{{ difficultyText(row.difficulty) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="position_level" label="适用岗位" width="100" />
        <el-table-column prop="company" label="来源公司" width="110" show-overflow-tooltip />
        <el-table-column prop="view_count" label="浏览" width="70" />
        <el-table-column prop="collect_count" label="收藏" width="70" />
        <el-table-column prop="created_at" label="创建时间" width="160" />
        <el-table-column label="操作" width="140" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="handleEdit(row)" class="btn-edit">编辑</el-button>
            <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="size"
          :total="total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          @size-change="fetchList"
          @current-change="fetchList"
          class="dark-pagination"
        />
      </div>
    </div>

    <!-- 新增/编辑弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑面试题' : '新增面试题'"
      width="800px"
      :close-on-click-modal="false"
      @closed="resetForm"
      custom-class="dark-dialog"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
        <el-form-item label="题目标题" prop="title">
          <el-input v-model="form.title" placeholder="请输入题目标题（简洁描述问题）" class="dark-input" />
        </el-form-item>
        <el-form-item label="补充描述">
          <el-input v-model="form.content" type="textarea" :rows="2" placeholder="题目补充说明（选填）" class="dark-input" />
        </el-form-item>
        <el-form-item label="参考答案" prop="answer">
          <el-input v-model="form.answer" type="textarea" :rows="5" placeholder="请输入参考答案" class="dark-input" />
        </el-form-item>
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="分类" prop="category">
              <el-select v-model="form.category" allow-create filterable style="width: 100%;" class="dark-select">
                <el-option v-for="c in categories" :key="c" :label="c" :value="c" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="难度" prop="difficulty">
              <el-select v-model="form.difficulty" style="width: 100%;" class="dark-select">
                <el-option label="简单" value="easy" />
                <el-option label="中等" value="medium" />
                <el-option label="困难" value="hard" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="适用岗位">
              <el-select v-model="form.position_level" style="width: 100%;" clearable class="dark-select">
                <el-option label="初级" value="初级" />
                <el-option label="中级" value="中级" />
                <el-option label="高级" value="高级" />
                <el-option label="专家" value="专家" />
                <el-option label="通用" value="通用" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="来源公司">
              <el-input v-model="form.company" placeholder="如：阿里巴巴、腾讯（选填）" class="dark-input" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="标签">
              <el-input v-model="form.tags" placeholder="多个标签用英文逗号分隔（选填）" class="dark-input" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false" class="btn-cancel">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit" class="btn-primary">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import request from '@/utils/request'
import { generateInterviewAnswers } from '@/api/admin'

// 分类列表
const categories = ['基础测试', '自动化测试', '性能测试', '接口测试', '数据库', '编程', 'HR面试', '安全测试', '其他']

// ---- 列表状态 ----
const list = ref([])
const total = ref(0)
const page = ref(1)
const size = ref(10)
const loading = ref(false)
const generating = ref(false)
const keyword = ref('')
const filterCategory = ref('')
const filterDifficulty = ref('')

const fetchList = async () => {
  loading.value = true
  try {
    const params = { page: page.value, size: size.value }
    if (keyword.value) params.keyword = keyword.value
    if (filterCategory.value) params.category = filterCategory.value
    if (filterDifficulty.value) params.difficulty = filterDifficulty.value
    const res = await request.get('/admin/interview/questions', { params })
    const data = res?.data || res
    list.value = data?.items || data?.list || []
    total.value = data?.total || 0
  } catch (e) {
    ElMessage.error('获取面试题列表失败')
  } finally {
    loading.value = false
  }
}

const handleGenerateAnswers = async () => {
  await ElMessageBox.confirm(
    '将使用AI为所有没有参考答案的面试题生成参考答案，可能需要几分钟时间。是否继续？',
    'AI生成参考答案',
    { confirmButtonText: '开始生成', cancelButtonText: '取消', type: 'warning' }
  )
  generating.value = true
  try {
    const res = await generateInterviewAnswers(20)
    const data = res?.data || res
    ElMessage.success(data.message || `生成完成：成功 ${data.generated} 个，跳过 ${data.skipped} 个`)
    if (data.errors?.length) {
      console.warn('生成错误:', data.errors)
    }
    fetchList()
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || '生成失败，请检查AI配置')
  } finally {
    generating.value = false
  }
}

onMounted(fetchList)

// ---- 辅助 ----
const difficultyText = d => ({ easy: '简单', medium: '中等', hard: '困难' }[d] || d)
const difficultyTag = d => ({ easy: 'success', medium: 'warning', hard: 'danger' }[d] || 'info')

// ---- 删除 ----
const handleDelete = async (row) => {
  await ElMessageBox.confirm(`确定删除题目「${row.title.slice(0, 20)}...」吗？`, '删除确认', {
    confirmButtonText: '确定删除', cancelButtonText: '取消', type: 'warning'
  })
  try {
    await request.delete(`/admin/interview/questions/${row.id}`)
    ElMessage.success('删除成功')
    fetchList()
  } catch (e) {
    ElMessage.error('删除失败')
  }
}

// ---- 弹窗 ----
const dialogVisible = ref(false)
const isEdit = ref(false)
const submitting = ref(false)
const formRef = ref(null)

const defaultForm = () => ({
  id: null,
  title: '',
  content: '',
  answer: '',
  category: '基础测试',
  difficulty: 'medium',
  position_level: '通用',
  tags: '',
  company: ''
})

const form = reactive(defaultForm())
const rules = {
  title: [{ required: true, message: '请输入题目标题', trigger: 'blur' }],
  answer: [{ required: true, message: '请输入参考答案', trigger: 'blur' }],
  category: [{ required: true, message: '请选择分类', trigger: 'change' }],
}

const resetForm = () => {
  Object.assign(form, defaultForm())
  formRef.value?.clearValidate()
}

const handleAdd = () => {
  isEdit.value = false
  resetForm()
  dialogVisible.value = true
}

const handleEdit = async (row) => {
  isEdit.value = true
  resetForm()
  try {
    const res = await request.get(`/admin/interview/questions/${row.id}`)
    const detail = res?.data || res
    Object.assign(form, {
      id: detail.id,
      title: detail.title || '',
      content: detail.content || detail.description || '',
      answer: detail.answer || detail.reference_solution || '',
      category: detail.category || '',
      difficulty: detail.difficulty || 'medium',
      position_level: detail.position_level || '通用',
      tags: detail.tags || '',
      company: detail.company || ''
    })
    dialogVisible.value = true
  } catch (e) {
    ElMessage.error('获取题目详情失败')
  }
}

const handleSubmit = async () => {
  await formRef.value.validate()
  submitting.value = true
  try {
    if (isEdit.value) {
      await request.put(`/admin/interview/questions/${form.id}`, form)
      ElMessage.success('面试题更新成功')
    } else {
      await request.post('/admin/interview/questions', form)
      ElMessage.success('面试题新增成功')
    }
    dialogVisible.value = false
    fetchList()
  } catch (e) {
    ElMessage.error(e?.response?.data?.error || '保存失败')
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.interview-management-dark {
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
  flex-wrap: wrap;
  gap: 12px;
}

.toolbar-left {
  display: flex;
  gap: 12px;
  align-items: center;
}

.toolbar-right {
  display: flex;
  gap: 12px;
  align-items: center;
  flex-wrap: wrap;
}

.search-input {
  width: 240px;
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
  width: 150px;
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

.btn-warning {
  background: linear-gradient(135deg, #E6A23C, #F56C6C);
  border: none;
  color: #fff;
  box-shadow: 0 2px 10px rgba(230, 162, 60, 0.3);
}
.btn-warning:hover {
  background: linear-gradient(135deg, #F56C6C, #E6A23C);
  box-shadow: 0 4px 15px rgba(245, 108, 108, 0.4);
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
  display: flex;
  justify-content: flex-end;
}

.dark-table :deep(.el-table) {
  background: transparent;
  color: var(--tm-text-primary);
}

.dark-table :deep(.el-table tr) {
  background: var(--tm-card-bg);
}

.dark-table :deep(.el-table th) {
  background: var(--tm-card-bg);
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

.btn-edit {
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
  border-color: var(--tm-color-primary);
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
