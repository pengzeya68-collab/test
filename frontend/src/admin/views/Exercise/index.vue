<template>
  <div class="exercise-management-dark">
    <h1 class="page-title">习题管理</h1>

    <!-- 操作栏 -->
    <div class="toolbar-card">
      <div class="toolbar-left">
        <el-button type="primary" @click="handleAdd" class="btn-primary">
          <el-icon><Plus /></el-icon>
          新增习题
        </el-button>
        <el-button type="success" @click="handleImport" class="btn-success">
          <el-icon><Upload /></el-icon>
          批量导入
        </el-button>
        <el-button @click="downloadTemplate" class="btn-outline">
          <el-icon><Download /></el-icon>
          下载模板
        </el-button>
      </div>
      <div class="toolbar-right">
        <el-input
          v-model="keyword"
          placeholder="搜索习题标题"
          class="search-input"
        />
        <el-select v-model="difficulty" placeholder="难度筛选" class="filter-select">
          <el-option label="全部" value="" />
          <el-option label="简单" value="easy" />
          <el-option label="中等" value="medium" />
          <el-option label="困难" value="hard" />
        </el-select>
        <el-button @click="handleSearch" class="btn-search">搜索</el-button>
      </div>
    </div>

    <!-- 批量导入对话框 -->
    <el-dialog
      v-model="importDialogVisible"
      title="批量导入习题"
      width="520px"
      custom-class="dark-dialog"
    >
      <div style="padding: 20px 0;">
        <el-upload
          ref="uploadRef"
          action="/api/admin/exercises/import"
          :headers="headers"
          :show-file-list="true"
          :limit="1"
          :auto-upload="false"
          accept=".json,.csv,.xlsx,.xls"
          :on-success="handleImportSuccess"
          :on-error="handleImportError"
        >
          <el-button type="primary">选择文件</el-button>
          <template #tip>
            <div class="el-upload__tip">
              支持JSON/CSV/Excel格式，<a @click="downloadTemplate" class="link-text">下载导入模板</a>
            </div>
          </template>
        </el-upload>

        <!-- 导入结果 -->
        <div v-if="importResult" style="margin-top: 20px;">
          <el-alert
            :title="`导入完成，成功${importResult.success_count}条，失败${importResult.fail_count}条`"
            :type="importResult.fail_count > 0 ? 'warning' : 'success'"
            show-icon
          />
          <div v-if="importResult.fail_reasons.length > 0" style="margin-top: 10px; max-height: 200px; overflow-y: auto;">
            <p style="font-weight: bold; margin-bottom: 5px; color: #e0e0e0;">失败原因：</p>
            <ul>
              <li v-for="(reason, index) in importResult.fail_reasons" :key="index" style="color: #f56c6c; font-size: 12px;">
                {{ reason }}
              </li>
            </ul>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="importDialogVisible = false" class="btn-cancel">取消</el-button>
        <el-button type="primary" @click="submitImport" :loading="importLoading" class="btn-primary">开始导入</el-button>
      </template>
    </el-dialog>

    <!-- 列表 -->
    <div class="list-card">
      <el-table :data="list" border stripe class="dark-table">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="title" label="习题标题" min-width="200" />
        <el-table-column prop="category" label="分类" width="120" />
        <el-table-column prop="difficulty" label="难度" width="100">
          <template #default="{ row }">
            <el-tag :type="getDifficultyType(row.difficulty)">
              {{ getDifficultyText(row.difficulty) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="passRate" label="通过率" width="100">
          <template #default="{ row }">
            <div class="pass-rate-bar">
              <div class="bar-bg">
                <div class="bar-fill" :style="{ width: (row.passRate || 0) + '%' }"></div>
              </div>
              <span class="rate-text">{{ row.passRate || 0 }}%</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="createTime" label="创建时间" width="160" />
        <el-table-column label="操作" width="180" fixed="right">
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
      :title="isEdit ? '编辑习题' : '新增习题'"
      width="600px"
      custom-class="dark-dialog"
    >
      <el-form :model="form" label-width="80px">
        <el-form-item label="标题" prop="title">
          <el-input v-model="form.title" placeholder="请输入习题标题" class="dark-input" />
        </el-form-item>
        <el-form-item label="分类" prop="category">
          <el-input v-model="form.category" placeholder="请输入分类" class="dark-input" />
        </el-form-item>
        <el-form-item label="难度" prop="difficulty">
          <el-select v-model="form.difficulty" style="width: 100%;" class="dark-select">
            <el-option label="简单" value="easy" />
            <el-option label="中等" value="medium" />
            <el-option label="困难" value="hard" />
          </el-select>
        </el-form-item>
        <el-form-item label="内容" prop="content">
          <el-input v-model="form.content" type="textarea" :rows="6" placeholder="请输入习题内容" class="dark-input" />
        </el-form-item>
        <el-form-item label="答案" prop="answer">
          <el-input v-model="form.answer" type="textarea" :rows="4" placeholder="请输入参考答案" class="dark-input" />
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
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Upload, Download } from '@element-plus/icons-vue'
import request from '@/utils/request'

const keyword = ref('')
const difficulty = ref('')
const page = ref(1)
const size = ref(10)
const total = ref(0)
const list = ref([])
const dialogVisible = ref(false)
const isEdit = ref(false)

const form = reactive({
  id: null,
  title: '',
  category: '',
  difficulty: 'easy',
  content: '',
  answer: ''
})

// 批量导入相关
const importDialogVisible = ref(false)
const uploadRef = ref()
const importLoading = ref(false)
const importResult = ref(null)

// 请求头，添加token
const headers = {
  Authorization: `Bearer ${localStorage.getItem('admin_token') || ''}`
}

const getDifficultyType = (val) => {
  const map = { easy: 'success', medium: 'warning', hard: 'danger' }
  return map[val] || 'info'
}

const getDifficultyText = (val) => {
  const map = { easy: '简单', medium: '中等', hard: '困难' }
  return map[val] || val
}

const fetchList = async () => {
  try {
    const res = await request.get('/admin/exercises', {
      params: {
        page: page.value,
        size: size.value,
        keyword: keyword.value,
        difficulty: difficulty.value
      }
    })
    if (res && res.list) {
      list.value = res.list
      total.value = res.total
    }
  } catch (e) {
    console.error('获取习题列表失败:', e)
    ElMessage.error('获取列表失败')
  }
}

const handleSearch = () => {
  page.value = 1
  fetchList()
}

// 监听难度变化，自动搜索
const handleDifficultyChange = () => {
  page.value = 1
  fetchList()
}

const handleAdd = () => {
  isEdit.value = false
  Object.keys(form).forEach(key => {
    form[key] = key === 'id' ? null : key === 'difficulty' ? 'easy' : ''
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
      await request.put(`/admin/exercises/${form.id}`, form)
      ElMessage.success('更新成功')
    } else {
      await request.post('/admin/exercises', form)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    fetchList()
  } catch (e) {
    console.error('提交失败:', e)
    ElMessage.error('操作失败：' + (e.response?.data?.error || e.message))
  }
}

const handleDelete = async (row) => {
  await ElMessageBox.confirm('确定要删除这个习题吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  })

  try {
    await request.delete(`/admin/exercises/${row.id}`)
    ElMessage.success('删除成功')
    fetchList()
  } catch (e) {
    console.error('删除失败:', e)
    ElMessage.error('删除失败：' + (e.response?.data?.error || e.message))
  }
}

// 批量导入
const handleImport = () => {
  importDialogVisible.value = true
  importResult.value = null
  if (uploadRef.value) {
    uploadRef.value.clearFiles()
  }
}

// 下载导入模板
const downloadTemplate = () => {
  // 创建一个示例模板JSON文件下载
  const template = [
    {
      "title": "习题标题（必填）",
      "description": "习题描述",
      "instructions": "答题说明",
      "solution": "参考答案（必填）",
      "difficulty": "easy/medium/hard（可选，默认easy）",
      "language": "通用/Python/SQL/Linux（可选）",
      "category": "分类（可选）",
      "time_estimate": "预计耗时（分钟，可选）"
    }
  ]

  const blob = new Blob([JSON.stringify(template, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = '习题导入模板.json'
  a.click()
  URL.revokeObjectURL(url)

  ElMessage.success('模板下载成功')
}

// 提交导入
const submitImport = () => {
  if (!uploadRef.value || uploadRef.value.uploadFiles.length === 0) {
    ElMessage.warning('请先选择文件')
    return
  }

  importLoading.value = true
  uploadRef.value.submit()
}

// 导入成功
const handleImportSuccess = (response) => {
  importLoading.value = false
  importResult.value = response
  ElMessage.success(response.msg || '导入完成')
  fetchList() // 刷新列表
}

// 导入失败
const handleImportError = (error) => {
  importLoading.value = false
  ElMessage.error('导入失败：' + (error.response?.data?.error || error.message))
}

onMounted(() => {
  fetchList()
})
</script>

<style scoped>
.exercise-management-dark {
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
  align-items: center;
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

.btn-success {
  background: linear-gradient(135deg, #67c23a, #84cc16);
  border: none;
}

.btn-outline {
  color: var(--tm-color-primary);
  border: 1px solid var(--tm-color-primary);
  background: transparent;
}

.btn-outline:hover {
  background: rgba(var(--tm-color-primary), 0.1);
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

.pass-rate-bar {
  display: flex;
  align-items: center;
  gap: 8px;
}

.bar-bg {
  flex: 1;
  width: 60px;
  height: 8px;
  background: rgba(var(--tm-text-primary-rgb), 0.15);
  border-radius: 4px;
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #67c23a, #84cc16);
  border-radius: 4px;
  transition: width 0.3s ease;
}

.rate-text {
  color: var(--tm-text-secondary);
  font-size: 13px;
  min-width: 35px;
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

.link-text {
  color: var(--tm-color-primary);
  cursor: pointer;
}

.link-text:hover {
  text-decoration: underline;
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
