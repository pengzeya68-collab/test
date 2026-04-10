<template>
  <div class="exam-management-dark">
    <h1 class="page-title">考试管理</h1>

    <!-- 操作栏 -->
    <div class="toolbar-card">
      <div class="toolbar-left">
        <el-button type="primary" @click="handleAdd" class="btn-primary">
          <el-icon><Plus /></el-icon>
          新增考试
        </el-button>
      </div>
      <div class="toolbar-right">
        <el-input
          v-model="keyword"
          placeholder="搜索考试标题"
          class="search-input"
          clearable
          @clear="fetchList"
          @keyup.enter="fetchList"
        />
        <el-select v-model="filterType" placeholder="考试类型" class="filter-select" clearable @change="fetchList">
          <el-option label="模拟考试" value="模拟考试" />
          <el-option label="正式考试" value="正式考试" />
          <el-option label="专项练习" value="专项练习" />
        </el-select>
        <el-select v-model="filterPublished" placeholder="发布状态" class="filter-select" clearable @change="fetchList">
          <el-option label="已发布" value="true" />
          <el-option label="未发布" value="false" />
        </el-select>
        <el-button @click="fetchList" class="btn-search">搜索</el-button>
      </div>
    </div>

    <!-- 列表 -->
    <div class="list-card">
      <el-table :data="list" border stripe v-loading="loading" class="dark-table">
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="title" label="标题" min-width="180" show-overflow-tooltip />
        <el-table-column prop="exam_type" label="类型" width="100" />
        <el-table-column prop="difficulty" label="难度" width="80">
          <template #default="{ row }">
            <el-tag :type="difficultyTag(row.difficulty)" size="small">{{ difficultyText(row.difficulty) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="duration" label="时长(分)" width="90" />
        <el-table-column prop="question_count" label="题目数" width="80" />
        <el-table-column prop="total_score" label="总分" width="70" />
        <el-table-column prop="pass_score" label="及格分" width="80" />
        <el-table-column prop="attempt_count" label="参考人数" width="90" />
        <el-table-column prop="pass_rate" label="通过率" width="100">
          <template #default="{ row }">
            <div class="pass-rate-bar">
              <div class="bar-bg">
                <div class="bar-fill" :style="{ width: (row.pass_rate || 0) + '%' }"></div>
              </div>
              <span class="rate-text">{{ row.pass_rate }}%</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="is_published" label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="row.is_published ? 'success' : 'info'" size="small">
              {{ row.is_published ? '已发布' : '未发布' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="160" />
        <el-table-column label="操作" width="230" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="handleEdit(row)" class="btn-edit">编辑</el-button>
            <el-button
              size="small"
              :type="row.is_published ? 'warning' : 'success'"
              @click="togglePublish(row)"
            >{{ row.is_published ? '取消发布' : '发布' }}</el-button>
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
      :title="isEdit ? '编辑考试' : '新增考试'"
      width="900px"
      :close-on-click-modal="false"
      @closed="resetForm"
      custom-class="dark-dialog"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="考试标题" prop="title">
              <el-input v-model="form.title" placeholder="请输入考试标题" class="dark-input" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="考试类型" prop="exam_type">
              <el-select v-model="form.exam_type" style="width: 100%;" class="dark-select">
                <el-option label="模拟考试" value="模拟考试" />
                <el-option label="正式考试" value="正式考试" />
                <el-option label="专项练习" value="专项练习" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="难度" prop="difficulty">
              <el-select v-model="form.difficulty" style="width: 100%;" class="dark-select">
                <el-option label="简单" value="easy" />
                <el-option label="中等" value="medium" />
                <el-option label="困难" value="hard" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="考试时长" prop="duration">
              <el-input-number v-model="form.duration" :min="1" :max="300" style="width: 100%;" />
              <span style="margin-left: 8px; color: var(--tm-text-secondary); font-size: 12px;">分钟</span>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="总分" prop="total_score">
              <el-input-number v-model="form.total_score" :min="1" :max="1000" style="width: 100%;" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="及格分" prop="pass_score">
              <el-input-number v-model="form.pass_score" :min="1" :max="1000" style="width: 100%;" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="开始时间">
              <el-date-picker
                v-model="form.start_time"
                type="datetime"
                placeholder="选择开始时间"
                style="width: 100%;"
                value-format="YYYY-MM-DD HH:mm:ss"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="结束时间">
              <el-date-picker
                v-model="form.end_time"
                type="datetime"
                placeholder="选择结束时间"
                style="width: 100%;"
                value-format="YYYY-MM-DD HH:mm:ss"
              />
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="描述">
              <el-input v-model="form.description" type="textarea" :rows="2" placeholder="考试描述（选填）" class="dark-input" />
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="直接发布">
              <el-switch v-model="form.is_published" />
            </el-form-item>
          </el-col>
        </el-row>

        <!-- 题目管理 -->
        <div style="margin-top: 10px;">
          <div class="question-toolbar">
            <span class="question-title">题目列表（{{ form.questions.length }} 道）</span>
            <el-button type="primary" size="small" @click="addQuestion" class="btn-primary">+ 添加题目</el-button>
          </div>

          <div
            v-for="(q, idx) in form.questions"
            :key="idx"
            class="question-card"
          >
            <div class="question-header">
              <span class="question-number">第 {{ idx + 1 }} 题</span>
              <el-button type="danger" size="small" plain @click="removeQuestion(idx)">删除</el-button>
            </div>
            <el-row :gutter="12">
              <el-col :span="8">
                <el-form-item label="题型" :prop="`questions.${idx}.question_type`" style="margin-bottom: 8px;">
                  <el-select v-model="q.question_type" size="small" style="width: 100%;" @change="onQuestionTypeChange(q)">
                    <el-option label="单选题" value="single_choice" />
                    <el-option label="多选题" value="multiple_choice" />
                    <el-option label="判断题" value="true_false" />
                    <el-option label="简答题" value="short_answer" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="4">
                <el-form-item label="分值" style="margin-bottom: 8px;">
                  <el-input-number v-model="q.score" :min="1" :max="100" size="small" style="width: 100%;" />
                </el-form-item>
              </el-col>
              <el-col :span="24">
                <el-form-item label="题目内容" style="margin-bottom: 8px;">
                  <el-input v-model="q.content" type="textarea" :rows="2" size="small" placeholder="请输入题目内容" class="dark-input" />
                </el-form-item>
              </el-col>

              <!-- 选择题选项 -->
              <el-col :span="24" v-if="['single_choice', 'multiple_choice'].includes(q.question_type)">
                <el-form-item label="选项" style="margin-bottom: 8px;">
                  <div v-for="(opt, oi) in q.options" :key="oi" class="option-row">
                    <span class="option-letter">{{ String.fromCharCode(65 + oi) }}.</span>
                    <el-input v-model="q.options[oi]" size="small" placeholder="选项内容" class="option-input" />
                    <el-button size="small" plain type="danger" @click="q.options.splice(oi, 1)">×</el-button>
                  </div>
                  <el-button size="small" @click="q.options.push('')">+ 添加选项</el-button>
                </el-form-item>
              </el-col>

              <el-col :span="24">
                <el-form-item label="正确答案">
                  <!-- 判断题 -->
                  <el-radio-group v-if="q.question_type === 'true_false'" v-model="q.correct_answer" size="small">
                    <el-radio value="true" label="true">正确</el-radio>
                    <el-radio value="false" label="false">错误</el-radio>
                  </el-radio-group>
                  <!-- 单选题 -->
                  <el-select v-else-if="q.question_type === 'single_choice'" v-model="q.correct_answer" size="small" style="width: 200px;">
                    <el-option
                      v-for="(opt, oi) in q.options"
                      :key="oi"
                      :label="`${String.fromCharCode(65+oi)}. ${opt}`"
                      :value="String.fromCharCode(65+oi)"
                    />
                  </el-select>
                  <!-- 多选题 -->
                  <el-checkbox-group v-else-if="q.question_type === 'multiple_choice'" v-model="q.correctAnswerArr" size="small">
                    <el-checkbox v-for="(opt, oi) in q.options" :key="oi" :label="String.fromCharCode(65+oi)">
                      {{ String.fromCharCode(65+oi) }}. {{ opt }}
                    </el-checkbox>
                  </el-checkbox-group>
                  <!-- 简答题 -->
                  <el-input v-else v-model="q.correct_answer" type="textarea" :rows="2" size="small" placeholder="参考答案" class="dark-input" />
                </el-form-item>
              </el-col>

              <el-col :span="24">
                <el-form-item label="题目解析">
                  <el-input v-model="q.analysis" type="textarea" :rows="2" size="small" placeholder="解析（选填）" class="dark-input" />
                </el-form-item>
              </el-col>
            </el-row>
          </div>

          <el-empty v-if="form.questions.length === 0" description="暂无题目，点击上方按钮添加" :image-size="60" class="dark-empty" />
        </div>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false" class="btn-cancel">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit" class="btn-primary">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import request from '@/utils/request'

// ---- 列表状态 ----
const list = ref([])
const total = ref(0)
const page = ref(1)
const size = ref(10)
const loading = ref(false)
const keyword = ref('')
const filterType = ref('')
const filterPublished = ref('')

const fetchList = async () => {
  loading.value = true
  try {
    const params = { page: page.value, size: size.value }
    if (keyword.value) params.keyword = keyword.value
    if (filterType.value) params.exam_type = filterType.value
    if (filterPublished.value !== '') params.is_published = filterPublished.value
    const res = await request.get('/admin/exams', { params })
    list.value = res?.list || []
    total.value = res?.total || 0
  } catch (e) {
    ElMessage.error('获取考试列表失败')
  } finally {
    loading.value = false
  }
}

onMounted(fetchList)

// ---- 状态辅助 ----
const difficultyText = d => ({ easy: '简单', medium: '中等', hard: '困难' }[d] || d)
const difficultyTag = d => ({ easy: 'success', medium: 'warning', hard: 'danger' }[d] || 'info')

// ---- 发布切换 ----
const togglePublish = async (row) => {
  try {
    await request.put(`/admin/exams/${row.id}/publish`, { is_published: !row.is_published })
    ElMessage.success(row.is_published ? '已取消发布' : '已发布')
    fetchList()
  } catch (e) {
    ElMessage.error('操作失败')
  }
}

// ---- 删除 ----
const handleDelete = async (row) => {
  await ElMessageBox.confirm(`确定删除考试「${row.title}」吗？该操作不可撤销。`, '删除确认', {
    confirmButtonText: '确定删除',
    cancelButtonText: '取消',
    type: 'warning'
  })
  try {
    await request.delete(`/admin/exams/${row.id}`)
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
  exam_type: '模拟考试',
  difficulty: 'medium',
  duration: 60,
  total_score: 100,
  pass_score: 60,
  description: '',
  is_published: false,
  start_time: null,
  end_time: null,
  questions: []
})

const form = reactive(defaultForm())

const rules = {
  title: [{ required: true, message: '请输入考试标题', trigger: 'blur' }],
  exam_type: [{ required: true, message: '请选择考试类型', trigger: 'change' }],
  duration: [{ required: true, message: '请填写时长', trigger: 'blur' }],
  total_score: [{ required: true, message: '请填写总分', trigger: 'blur' }],
  pass_score: [{ required: true, message: '请填写及格分', trigger: 'blur' }],
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
    const res = await request.get(`/admin/exams/${row.id}`)
    const d = res
    Object.assign(form, {
      id: d.id,
      title: d.title,
      exam_type: d.exam_type,
      difficulty: d.difficulty,
      duration: d.duration,
      total_score: d.total_score,
      pass_score: d.pass_score,
      description: d.description,
      is_published: d.is_published,
      start_time: d.start_time,
      end_time: d.end_time,
      questions: (d.questions || []).map(q => ({
        ...q,
        options: q.options || [],
        correctAnswerArr: q.question_type === 'multiple_choice'
          ? (q.correct_answer || '').split('') : []
      }))
    })
    dialogVisible.value = true
  } catch (e) {
    ElMessage.error('获取考试详情失败')
  }
}

const addQuestion = () => {
  form.questions.push({
    question_type: 'single_choice',
    content: '',
    options: ['', '', '', ''],
    correct_answer: '',
    correctAnswerArr: [],
    score: 10,
    analysis: ''
  })
}

const removeQuestion = (idx) => {
  form.questions.splice(idx, 1)
}

const onQuestionTypeChange = (q) => {
  if (q.question_type === 'true_false') {
    q.options = []
    q.correct_answer = 'true'
    q.correctAnswerArr = []
  } else if (['single_choice', 'multiple_choice'].includes(q.question_type)) {
    if (!q.options.length) q.options = ['', '', '', '']
    q.correct_answer = ''
    q.correctAnswerArr = []
  } else {
    q.options = []
    q.correct_answer = ''
    q.correctAnswerArr = []
  }
}

const handleSubmit = async () => {
  await formRef.value.validate()
  submitting.value = true
  try {
    // 整理多选题答案
    const questions = form.questions.map(q => {
      const item = { ...q }
      if (q.question_type === 'multiple_choice') {
        item.correct_answer = q.correctAnswerArr.sort().join('')
      }
      delete item.correctAnswerArr
      return item
    })

    const payload = {
      title: form.title,
      exam_type: form.exam_type,
      difficulty: form.difficulty,
      duration: form.duration,
      total_score: form.total_score,
      pass_score: form.pass_score,
      description: form.description,
      is_published: form.is_published,
      start_time: form.start_time || null,
      end_time: form.end_time || null,
      questions
    }

    if (isEdit.value) {
      await request.put(`/admin/exams/${form.id}`, payload)
      ElMessage.success('考试更新成功')
    } else {
      await request.post('/admin/exams', payload)
      ElMessage.success('考试创建成功')
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
.exam-management-dark {
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
  width: 220px;
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

.pass-rate-bar {
  display: flex;
  align-items: center;
  gap: 8px;
}

.bar-bg {
  flex: 1;
  width: 50px;
  height: 8px;
  background: var(--tm-card-bg);
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
  min-width: 40px;
}

.pagination-wrapper {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.question-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.question-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--tm-text-primary);
}

.question-card {
  background: rgba(var(--tm-bg-page-rgb), 0.5);
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 12px;
  border: 1px solid var(--tm-border-light);
}

.question-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.question-number {
  font-weight: 500;
  color: var(--tm-color-primary);
}

.option-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.option-letter {
  width: 26px;
  color: var(--tm-color-primary);
  font-weight: 600;
}

.option-input {
  flex: 1;
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

.dark-empty :deep(.el-empty__description) {
  color: var(--tm-text-secondary);
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
