<template>
  <div class="interview-question-bank">
    <div class="container">
      <div class="page-header">
        <div>
          <h1 class="page-title">面试题库</h1>
          <p class="page-subtitle">海量测试工程师面试真题，助力Offer收割</p>
        </div>
        <el-button-group>
          <el-button type="primary" @click="$router.push('/interview/simulate')">
            <el-icon><VideoPlay /></el-icon>
            模拟面试
          </el-button>
          <el-button @click="$router.push('/interview/my')">
            <el-icon><Document /></el-icon>
            我的面试
          </el-button>
        </el-button-group>
      </div>

      <div class="filter-bar">
        <el-row :gutter="16">
          <el-col :span="5">
            <el-select 
              v-model="filters.category" 
              placeholder="分类" 
              @change="fetchQuestions"
              style="width: 100%;"
              clearable
            >
              <el-option 
                v-for="cat in categories" 
                :key="cat.value" 
                :label="cat.label" 
                :value="cat.value"
              />
            </el-select>
          </el-col>
          <el-col :span="4">
            <el-select 
              v-model="filters.difficulty" 
              placeholder="难度" 
              @change="fetchQuestions"
              style="width: 100%;"
              clearable
            >
              <el-option label="简单" value="easy" />
              <el-option label="中等" value="medium" />
              <el-option label="困难" value="hard" />
            </el-select>
          </el-col>
          <el-col :span="4">
            <el-select 
              v-model="filters.level" 
              placeholder="级别" 
              @change="fetchQuestions"
              style="width: 100%;"
              clearable
            >
              <el-option label="初级" value="初级" />
              <el-option label="中级" value="中级" />
              <el-option label="高级" value="高级" />
              <el-option label="专家" value="专家" />
            </el-select>
          </el-col>
          <el-col :span="7">
            <el-input
              v-model="filters.search"
              placeholder="搜索题目..."
              @keyup.enter="fetchQuestions"
              style="width: 100%;"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
          </el-col>
          <el-col :span="4">
            <el-button type="primary" @click="fetchQuestions" style="width: 100%;">
              <el-icon><Search /></el-icon>
              搜索
            </el-button>
          </el-col>
        </el-row>
      </div>

      <div class="tabs-container">
        <el-tabs v-model="activeTab" @tab-change="fetchQuestions">
          <el-tab-pane label="全部题目" name="all" />
          <el-tab-pane label="我的收藏" name="collected" />
        </el-tabs>
      </div>

      <div class="question-list">
        <div 
          class="question-card" 
          v-for="question in questions" 
          :key="question.id"
          @click="viewQuestion(question)"
        >
          <div class="card-header">
            <div class="question-title">{{ question.title }}</div>
            <el-button 
              type="text" 
              :icon="question.is_collected ? StarFilled : Star"
              @click.stop="toggleCollect(question)"
              :style="{ color: question.is_collected ? '#e6a23c' : '#909399' }"
            />
          </div>
          
          <div class="card-body">
            <div class="question-meta">
              <el-tag size="small" type="primary">{{ question.category }}</el-tag>
              <el-tag size="small" :type="getDifficultyTagType(question.difficulty)">
                {{ question.difficulty === 'easy' ? '简单' : question.difficulty === 'medium' ? '中等' : '困难' }}
              </el-tag>
              <el-tag size="small" type="info">{{ question.position_level }}</el-tag>
              <span class="meta-item">
                <el-icon size="14"><View /></el-icon>
                {{ question.view_count }}
              </span>
              <span class="meta-item">
                <el-icon size="14"><Star /></el-icon>
                {{ question.collect_count }}
              </span>
              <span class="company" v-if="question.company">
                {{ question.company }}
              </span>
            </div>
            <div class="tags" v-if="question.tags && question.tags.length > 0">
              <el-tag size="small" v-for="tag in question.tags" :key="tag" type="info" effect="plain">
                {{ tag }}
              </el-tag>
            </div>
          </div>
        </div>
      </div>

      <div class="pagination-container" v-if="total > 0">
        <el-pagination
          v-model:current-page="currentPage"
          :page-size="perPage"
          :total="total"
          layout="prev, pager, next, total"
          @current-change="fetchQuestions"
        />
      </div>

      <div class="empty-state" v-if="questions.length === 0 && !loading">
        <el-empty description="暂无题目" />
      </div>

      <div class="loading-state" v-if="loading">
        <el-skeleton :rows="10" animated />
      </div>

      <!-- 题目详情弹窗 -->
      <el-dialog 
        v-model="showDetailDialog" 
        title="题目详情"
        width="800px"
        class="question-detail-dialog"
      >
        <div v-if="currentQuestion" class="detail-content">
          <div class="detail-header">
            <div class="detail-title">{{ currentQuestion.title }}</div>
            <div class="detail-meta">
              <el-tag size="small" type="primary">{{ currentQuestion.category }}</el-tag>
              <el-tag size="small" :type="getDifficultyTagType(currentQuestion.difficulty)">
                {{ currentQuestion.difficulty === 'easy' ? '简单' : currentQuestion.difficulty === 'medium' ? '中等' : '困难' }}
              </el-tag>
              <span>浏览：{{ currentQuestion.view_count }}</span>
              <span>收藏：{{ currentQuestion.collect_count }}</span>
            </div>
          </div>
          
          <div class="detail-section" v-if="currentQuestion.content">
            <h4>题目描述</h4>
            <div v-html="renderMarkdown(currentQuestion.content)"></div>
          </div>
          
          <div class="detail-section">
            <h4>参考答案</h4>
            <div class="answer-content" v-html="renderMarkdown(currentQuestion.answer)"></div>
          </div>
        </div>
        <template #footer>
          <el-button @click="showDetailDialog = false">关闭</el-button>
          <el-button 
            type="primary" 
            :icon="currentQuestion?.is_collected ? StarFilled : Star"
            @click="toggleCollect(currentQuestion)"
          >
            {{ currentQuestion?.is_collected ? '取消收藏' : '收藏' }}
          </el-button>
        </template>
      </el-dialog>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { 
  VideoPlay, Document, Search, Star, StarFilled, View 
} from '@element-plus/icons-vue'
import request from '@/utils/request'
import { marked } from 'marked'

const questions = ref([])
const categories = ref([])
const filters = reactive({
  category: '',
  difficulty: '',
  level: '',
  search: ''
})
const activeTab = ref('all')
const currentPage = ref(1)
const perPage = ref(10)
const total = ref(0)
const loading = ref(false)
const showDetailDialog = ref(false)
const currentQuestion = ref(null)

onMounted(() => {
  fetchCategories()
  fetchQuestions()
})

const fetchCategories = async () => {
  try {
    const res = await request.get('/interview/categories')
    categories.value = res
  } catch (error) {
    console.error('获取分类失败:', error)
  }
}

const fetchQuestions = async () => {
  loading.value = true
  try {
    let params = {
      page: currentPage.value,
      per_page: perPage.value,
      category: filters.category,
      difficulty: filters.difficulty,
      level: filters.level,
      search: filters.search.trim()
    }
    
    let url = '/interview/questions'
    if (activeTab.value === 'collected') {
      url = '/interview/my-collections'
    }
    
    const res = await request.get(url, { params })
    questions.value = res.list
    total.value = res.total
  } catch (error) {
    console.error('获取题目列表失败:', error)
    ElMessage.error('获取题目列表失败')
  } finally {
    loading.value = false
  }
}

const getDifficultyTagType = (difficulty) => {
  const map = {
    'easy': 'success',
    'medium': 'warning',
    'hard': 'danger'
  }
  return map[difficulty] || 'info'
}

const viewQuestion = async (question) => {
  try {
    const res = await request.get(`/interview/questions/${question.id}`)
    currentQuestion.value = res
    showDetailDialog.value = true
  } catch (error) {
    console.error('获取题目详情失败:', error)
    ElMessage.error('获取题目详情失败')
  }
}

const toggleCollect = async (question) => {
  try {
    await request.post(`/interview/questions/${question.id}/toggle-collect`)
    question.is_collected = !question.is_collected
    if (question.is_collected) {
      question.collect_count += 1
      ElMessage.success('收藏成功')
    } else {
      question.collect_count = Math.max(0, question.collect_count - 1)
      ElMessage.success('取消收藏成功')
    }
    
    // 如果是收藏列表，取消收藏后刷新
    if (activeTab.value === 'collected' && !question.is_collected) {
      fetchQuestions()
    }
    
    // 更新弹窗中的收藏状态
    if (currentQuestion.value && currentQuestion.value.id === question.id) {
      currentQuestion.value.is_collected = question.is_collected
      currentQuestion.value.collect_count = question.collect_count
    }
  } catch (error) {
    console.error('收藏操作失败:', error)
    ElMessage.error('操作失败')
  }
}

const renderMarkdown = (content) => {
  return marked(content || '')
}
</script>

<style scoped>
.interview-question-bank {
  padding: 30px 0;
  min-height: calc(100vh - 60px);
  background-color: var(--tm-bg-color);
  background-image: var(--tm-bg-image);
  background-size: cover;
  background-position: center;
}

.container {
  width: 100%;
  max-width: 1440px;
  padding: 0 24px;
  margin: 0 auto;
  box-sizing: border-box;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
}

.page-title {
  font-size: 32px;
  font-weight: bold;
  color: var(--tm-text-primary);
  margin: 0 0 8px 0;
}

.page-subtitle {
  font-size: 14px;
  color: var(--tm-text-secondary);
  margin: 0;
}

.filter-bar {
  background: var(--tm-card-bg);
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  border: var(--tm-card-border);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  margin-bottom: 20px;
}

.tabs-container {
  background: var(--tm-card-bg);
  border-radius: 12px 12px 0 0;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  border: var(--tm-card-border);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
}

:deep(.el-tabs__header) {
  margin: 0 20px;
}

.question-list {
  background: var(--tm-card-bg);
  border-radius: 0 0 12px 12px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  border: var(--tm-card-border);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  padding: 0 20px 20px 20px;
}

.question-card {
  padding: 20px 0;
  border-bottom: 1px solid var(--tm-border-light);
  cursor: pointer;
  transition: all 0.3s ease;
}

.question-card:hover {
  background: var(--tm-bg-hover);
  margin: 0 -20px;
  padding-left: 20px;
  padding-right: 20px;
  border-radius: 8px;
}

.question-card:last-child {
  border-bottom: none;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.question-title {
  font-size: 16px;
  font-weight: 500;
  color: var(--tm-text-primary);
  line-height: 1.6;
  flex: 1;
  margin-right: 12px;
}

.question-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 12px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: var(--tm-text-secondary);
}

.company {
  font-size: 13px;
  color: var(--tm-color-primary);
  background: rgba(var(--tm-color-primary), 0.1);
  padding: 2px 8px;
  border-radius: 4px;
}

.tags {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 30px;
}

.empty-state, .loading-state {
  background: var(--tm-card-bg);
  padding: 60px 20px;
  border-radius: 12px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  border: var(--tm-card-border);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
}

/* 详情弹窗 */
.question-detail-dialog :deep(.el-dialog__body) {
  max-height: 70vh;
  overflow-y: auto;
}

.detail-content {
  line-height: 2;
}

.detail-header {
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--tm-border-light);
}

.detail-title {
  font-size: 20px;
  font-weight: bold;
  color: var(--tm-text-primary);
  margin-bottom: 12px;
  line-height: 1.6;
}

.detail-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  font-size: 14px;
  color: var(--tm-text-secondary);
}

.detail-section {
  margin-bottom: 24px;
}

.detail-section h4 {
  font-size: 16px;
  font-weight: bold;
  color: var(--tm-text-primary);
  margin: 0 0 12px 0;
}

.answer-content {
  background: rgba(var(--tm-bg-page-rgb), 0.5);
  padding: 20px;
  border-radius: 8px;
  border-left: 4px solid #67c23a;
}

/* Markdown样式 */
.detail-content p {
  margin: 12px 0;
  color: var(--tm-text-primary);
}

.detail-content ul,
.detail-content ol {
  margin: 12px 0;
  padding-left: 24px;
  color: var(--tm-text-primary);
}

.detail-content li {
  margin: 8px 0;
  color: var(--tm-text-primary);
}

.detail-content code {
  background: rgba(var(--tm-bg-page-rgb), 0.5);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 13px;
  color: #e6a23c;
}

.detail-content pre {
  background: #282c34;
  padding: 16px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 16px 0;
}

.detail-content pre code {
  background: none;
  padding: 0;
  color: #abb2bf;
  line-height: 1.6;
}

@media (max-width: 768px) {
  .filter-bar .el-col {
    margin-bottom: 16px;
  }

  .question-meta {
    gap: 8px;
  }
}
</style>
