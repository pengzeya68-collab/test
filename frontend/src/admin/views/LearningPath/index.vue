<template>
  <div class="learning-path-management-dark">
    <h1 class="page-title">学习路径管理</h1>

    <!-- 操作栏 -->
    <div class="toolbar-card">
      <div class="toolbar-left">
        <el-button type="primary" @click="handleAdd" class="btn-primary">
          <el-icon><Plus /></el-icon>
          新增路径
        </el-button>
      </div>
      <div class="toolbar-right">
        <el-input
          v-model="keyword"
          placeholder="搜索路径标题"
          class="search-input"
        />
        <el-select v-model="level" placeholder="难度筛选" class="filter-select">
          <el-option label="全部" value="" />
          <el-option label="入门" value="beginner" />
          <el-option label="进阶" value="intermediate" />
          <el-option label="高级" value="advanced" />
        </el-select>
        <el-button @click="handleSearch" class="btn-search">搜索</el-button>
      </div>
    </div>

    <!-- 卡片列表 -->
    <el-row :gutter="20" class="paths-grid">
      <el-col :span="8" v-for="item in list" :key="item.id" class="path-col">
        <div class="path-card">
          <div class="card-header">
            <h3 class="card-title">{{ item.title }}</h3>
            <el-tag :type="getLevelType(item.level)">{{ getLevelText(item.level) }}</el-tag>
          </div>
          <p class="card-description">{{ item.description }}</p>
          <div class="card-stats">
            <div class="stat-item">
              <span class="stat-label">习题</span>
              <span class="stat-value">{{ item.exerciseCount }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">学习</span>
              <span class="stat-value">{{ item.learnCount }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">完成率</span>
              <span class="stat-value">{{ item.completionRate }}%</span>
            </div>
          </div>
          <div class="card-actions">
            <el-button size="small" @click="handleEdit(item)" class="btn-edit">编辑</el-button>
            <el-button size="small" type="danger" @click="handleDelete(item)">删除</el-button>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 分页 -->
    <div class="pagination-wrapper">
      <el-pagination
        v-model:current-page="page"
        v-model:page-size="size"
        :total="total"
        :page-sizes="[9, 18, 36]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="fetchList"
        @current-change="fetchList"
        class="dark-pagination"
      />
    </div>

    <!-- 编辑弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑学习路径' : '新增学习路径'"
      width="700px"
      custom-class="dark-dialog"
    >
      <el-form :model="form" label-width="100px">
        <el-form-item label="路径标题" prop="title">
          <el-input v-model="form.title" placeholder="请输入路径标题" class="dark-input" />
        </el-form-item>
        <el-form-item label="难度等级" prop="level">
          <el-select v-model="form.level" style="width: 100%;" class="dark-select">
            <el-option label="入门" value="beginner" />
            <el-option label="进阶" value="intermediate" />
            <el-option label="高级" value="advanced" />
          </el-select>
        </el-form-item>
        <el-form-item label="路径描述" prop="description">
          <el-input v-model="form.description" type="textarea" :rows="3" placeholder="请输入路径描述" class="dark-input" />
        </el-form-item>
        <el-form-item label="关联习题">
          <el-transfer
            v-model="form.exerciseIds"
            :data="exerciseOptions"
            :props="{ key: 'key', label: 'label' }"
            :titles="['可选习题', '已选习题']"
          />
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
import { Plus } from '@element-plus/icons-vue'
import request from '@/utils/request'

const keyword = ref('')
const level = ref('')
const page = ref(1)
const size = ref(9)
const total = ref(0)
const list = ref([])
const dialogVisible = ref(false)
const isEdit = ref(false)
const exerciseOptions = ref([])

const form = reactive({
  id: null,
  title: '',
  level: 'beginner',
  description: '',
  exerciseIds: []
})

const getLevelType = (val) => {
  const map = { beginner: 'success', intermediate: 'warning', advanced: 'danger' }
  return map[val] || 'info'
}

const getLevelText = (val) => {
  const map = { beginner: '入门', intermediate: '进阶', advanced: '高级' }
  return map[val] || val
}

const fetchList = async () => {
  try {
    const res = await request.get('/admin/paths', {
      params: {
        page: page.value,
        size: size.value,
        keyword: keyword.value,
        level: level.value
      }
    })
    if (res && res.list) {
      list.value = res.list
      total.value = res.total
    }
  } catch (e) {
    console.error('获取学习路径失败:', e)
    ElMessage.error('获取列表失败')
  }
}

const fetchExerciseOptions = async () => {
  try {
    const res = await request.get('/admin/paths/exercises')
    if (res) {
      exerciseOptions.value = res
    }
  } catch (e) {
    console.error('获取习题选项失败:', e)
  }
}

const handleSearch = () => {
  page.value = 1
  fetchList()
}

const handleAdd = () => {
  isEdit.value = false
  Object.keys(form).forEach(key => {
    form[key] = key === 'id' ? null : key === 'level' ? 'beginner' : key === 'exerciseIds' ? [] : ''
  })
  fetchExerciseOptions()
  dialogVisible.value = true
}

const handleEdit = async (row) => {
  isEdit.value = true
  // 先获取路径详情获取已关联的习题ID
  const res = await request.get(`/admin/paths/${row.id}`)
  Object.assign(form, row)
  if (res && res.exerciseIds) {
    form.exerciseIds = res.exerciseIds
  }
  fetchExerciseOptions()
  dialogVisible.value = true
}

const handleSubmit = async () => {
  try {
    if (isEdit.value) {
      await request.put(`/admin/paths/${form.id}`, form)
      ElMessage.success('更新成功')
    } else {
      await request.post('/admin/paths', form)
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
  await ElMessageBox.confirm('确定要删除这个学习路径吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  })

  try {
    await request.delete(`/admin/paths/${row.id}`)
    ElMessage.success('删除成功')
    fetchList()
  } catch (e) {
    console.error('删除失败:', e)
    ElMessage.error('删除失败：' + (e.response?.data?.error || e.message))
  }
}

onMounted(() => {
  fetchList()
})
</script>

<style scoped>
.learning-path-management-dark {
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
  margin-bottom: 24px;
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

.paths-grid {
  margin-bottom: 24px;
}

.path-col {
  margin-bottom: 20px;
}

.path-card {
  background: var(--tm-card-bg);
  border-radius: 16px;
  padding: 20px;
  border: var(--tm-card-border);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
  transition: all 0.3s ease;
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
}

.path-card:hover {
  transform: translateY(-6px);
  box-shadow: 0 12px 30px rgba(0, 0, 0, 0.4), var(--tm-glow-effect);
  border-color: var(--tm-primary-color);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.card-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--tm-text-primary);
  line-height: 1.5;
}

.card-description {
  color: var(--tm-text-secondary);
  font-size: 14px;
  margin: 0 0 16px 0;
  line-height: 1.6;
  min-height: 45px;
}

.card-stats {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  margin-bottom: 16px;
  border-top: 1px solid var(--tm-border-light);
  border-bottom: 1px solid var(--tm-border-light);
}

.stat-item {
  text-align: center;
}

.stat-label {
  display: block;
  color: var(--tm-text-secondary);
  font-size: 12px;
  margin-bottom: 2px;
}

.stat-value {
  color: var(--tm-color-primary);
  font-size: 18px;
  font-weight: 600;
}

.card-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

.btn-edit {
  border-color: var(--tm-color-primary);
  color: var(--tm-color-primary);
}

.pagination-wrapper {
  text-align: right;
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
