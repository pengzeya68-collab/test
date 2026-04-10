<template>
  <div class="exercise-detail">
    <div class="container">
      <!-- 加载状态 -->
      <div class="loading" v-if="loading">
        <el-icon class="is-loading" size="40"><Loading /></el-icon>
      </div>

      <!-- 习题详情 -->
      <div v-if="!loading && exercise" class="exercise-content">
        <!-- 头部信息 -->
        <div class="exercise-header">
          <div class="exercise-basic">
            <div class="exercise-tags">
              <el-tag :type="getModuleTagType(exercise.module)" size="large">
                {{ getModuleName(exercise.module) }}
              </el-tag>
              <el-tag :type="getStageTagType(exercise.stage)" size="large">
                阶段{{ exercise.stage }}
              </el-tag>
              <el-tag :type="getDifficultyTagType(exercise.difficulty)" size="large">
                {{ getDifficultyText(exercise.difficulty) }}
              </el-tag>
              <el-tag type="info" size="large" v-if="exercise.knowledge_point">
                {{ exercise.knowledge_point }}
              </el-tag>
            </div>
            <h1 class="exercise-title">{{ exercise.title }}</h1>
            <div class="exercise-meta">
              <div class="meta-item">
                <el-icon size="16"><Timer /></el-icon>
                <span>预计 {{ exercise.time_estimate }} 分钟</span>
              </div>
              <div class="meta-item">
                <el-icon size="16"><Collection /></el-icon>
                <span>{{ exercise.category }}</span>
              </div>
              <div class="meta-item">
                <el-icon size="16"><Calendar /></el-icon>
                <span>更新于 {{ formatDate(exercise.updated_at) }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 题目描述 -->
        <div class="section">
          <h2 class="section-title">
            <el-icon size="24"><Document /></el-icon>
            题目描述
          </h2>
          <div class="content-card">
            <p class="description">{{ exercise.description }}</p>
          </div>
        </div>

        <!-- 答题要求 -->
        <div class="section" v-if="exercise.instructions">
          <h2 class="section-title">
            <el-icon size="24"><List /></el-icon>
            答题要求
          </h2>
          <div class="content-card">
            <pre class="instructions">{{ exercise.instructions }}</pre>
          </div>
        </div>

        <!-- 答题区域 -->
        <div class="section">
          <h2 class="section-title">
            <el-icon size="24"><Edit /></el-icon>
            我的答案
          </h2>
          <div class="content-card">
            <!-- 代码习题 -->
            <CodeEditor 
              v-if="exercise?.exercise_type === 'code'"
              v-model="userCode"
              :language="exercise.language?.toLowerCase() || 'python'"
              :template="exercise.code_template"
              @run="onCodeRun"
            />
            
            <!-- SQL习题 - 支持在线运行 -->
            <div v-else-if="exercise?.language?.toLowerCase() === 'sql'">
              <CodeEditor 
                v-model="userSql"
                language="sql"
                :template="''"
                @run="runSql"
              />
              <div class="sql-actions">
                <el-button type="success" @click="runSql" :loading="sqlRunning">
                  <el-icon><VideoPlay /></el-icon>
                  运行SQL
                </el-button>
                <el-button type="primary" @click="showSolution = true">
                  查看答案
                </el-button>
                <el-button type="success" @click="submitAnswer">
                  提交答案
                </el-button>
              </div>
              
              <!-- SQL执行结果 -->
              <div v-if="sqlResult" class="sql-result">
                <div class="result-header">
                  <span>执行结果 ({{ sqlResult.elapsed_ms }}ms)</span>
                  <el-tag :type="sqlResult.success ? 'success' : 'danger'">
                    {{ sqlResult.success ? '成功' : '失败' }}
                  </el-tag>
                </div>
                <!-- 错误信息 -->
                <div v-if="!sqlResult.success" class="result-error">
                  {{ sqlResult.error }}
                </div>
                <!-- 查询结果表格 -->
                <div v-if="sqlResult.success && sqlResult.columns && sqlResult.columns.length > 0" class="result-table">
                  <el-table :data="sqlResult.rows" border stripe>
                    <el-table-column 
                      v-for="col in sqlResult.columns" 
                      :key="col" 
                      :prop="col" 
                      :label="col"
                      min-width="120"
                    />
                  </el-table>
                  <div class="result-summary">
                    返回 {{ sqlResult.row_count }} 行记录
                  </div>
                </div>
                <!-- 非查询执行结果 -->
                <div v-if="sqlResult.success && sqlResult.message" class="result-message">
                  {{ sqlResult.message }}
                </div>
              </div>
            </div>
            
            <!-- 普通文本习题 -->
            <el-input
              v-else
              v-model="userAnswer"
              type="textarea"
              :rows="8"
              placeholder="请在此输入你的答案..."
            />
            
            <div class="answer-actions" v-if="exercise?.language?.toLowerCase() !== 'sql'">
              <el-button type="primary" @click="showSolution = true">
                查看答案
              </el-button>
              <el-button type="success" @click="submitAnswer">
                提交答案
              </el-button>
            </div>
          </div>
        </div>

        <!-- 答案解析 -->
        <div class="section" v-if="showSolution">
          <h2 class="section-title">
            <el-icon size="24"><Check /></el-icon>
            参考答案
          </h2>
          <div class="content-card solution-card">
            <pre class="solution">{{ exercise.solution }}</pre>
          </div>
        </div>

        <!-- 操作按钮 -->
        <div class="bottom-actions">
          <el-button @click="goBack">
            返回列表
          </el-button>
          <el-button type="primary" @click="nextExercise" v-if="nextExerciseId">
            下一题
          </el-button>
        </div>
      </div>

      <!-- 不存在 -->
      <div class="empty-state" v-if="!loading && !exercise">
        <el-empty description="习题不存在" />
        <el-button type="primary" @click="goBack" style="margin-top: 20px;">
          返回列表
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { Timer, Collection, Calendar, Document, List, Edit, Check, Loading, VideoPlay } from '@element-plus/icons-vue'
import request from '@/utils/request'
import { ElMessage, ElMessageBox } from 'element-plus'
import CodeEditor from '@/components/CodeEditor.vue'

const router = useRouter()
const route = useRoute()

const exercise = ref(null)
const loading = ref(false)
const userAnswer = ref('')
const userCode = ref('')
const userSql = ref('')
const showSolution = ref(false)
const nextExerciseId = ref(null)
const submitted = ref(false)
const sqlRunning = ref(false)
const sqlResult = ref(null)
const exerciseId = route.params.id

onMounted(() => {
  fetchExerciseDetail()
})

const fetchExerciseDetail = async () => {
  loading.value = true
  try {
    const res = await request.get(`/exercises/${exerciseId}`)
    exercise.value = res
    // 模拟下一题ID，实际项目中从后端获取
    const currentId = parseInt(exerciseId)
    // 只有小于等于7题的时候才显示下一题按钮
    if (currentId < 7) {
      nextExerciseId.value = currentId + 1
    } else {
      nextExerciseId.value = null
    }
  } catch (error) {
    console.error('获取习题详情失败:', error)
    ElMessage.error('获取习题详情失败')
    exercise.value = null
  } finally {
    loading.value = false
  }
}

const getStageTagType = (stage) => {
  const types = ['', 'primary', 'success', 'warning', 'danger', 'info']
  return types[stage] || 'info'
}

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

const getModuleTagType = (module) => {
  const map = {
    normal: 'info',
    automation: 'warning',
    api: 'primary'
  }
  return map[module] || 'info'
}

const getModuleName = (module) => {
  const map = {
    normal: '普通习题',
    automation: '自动化测试',
    api: '接口测试'
  }
  return map[module] || module
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN')
}

const submitAnswer = () => {
  // 判断是代码题还是普通题
  let answerContent = exercise.value?.exercise_type === 'code' ? userCode.value : userAnswer.value
  
  if (!answerContent || !answerContent.trim()) {
    ElMessage.warning('请输入答案后再提交')
    return
  }
  console.log('提交答案按钮被点击了！')
  console.log('当前习题ID:', exerciseId)
  console.log('答案内容:', answerContent.substring(0, 100) + '...')
  
  ElMessage.success('答案提交成功！')
  submitted.value = true
  
  // 跳转到下一题，先判断是否存在下一题
  const nextId = parseInt(exerciseId) + 1
  // 目前总题数是7题，超过7题就提示完成
  if (nextId <= 7) {
    try {
      console.log('尝试路由跳转到下一题:', nextId)
      router.push(`/exercises/${nextId}`)
    } catch (e) {
      console.log('路由跳转失败，使用强制跳转:', e)
      window.location.href = `#/exercises/${nextId}`
    }
  } else {
    // 已经完成所有题目
    ElMessageBox.alert('太棒了！你已经完成了本阶段所有练习。', '恭喜完成', {
      confirmButtonText: '返回学习路径',
      callback: () => {
        router.push('/learning-paths')
      }
    })
  }
}

const goBack = () => {
  router.back()
}

const onCodeRun = (result) => {
  console.log('代码运行结果:', result)
}

// 运行SQL验证
const runSql = async () => {
  if (!userSql.value || !userSql.value.trim()) {
    ElMessage.warning('请输入SQL语句')
    return
  }
  
  sqlRunning.value = true
  sqlResult.value = null
  
  try {
    const res = await request.post('/exercises/execute-sql', {
      setup_sql: exercise.value.test_cases || '',
      user_sql: userSql.value
    })
    sqlResult.value = res
    if (res.success) {
      ElMessage.success(`SQL执行成功，耗时 ${res.elapsed_ms}ms`)
    } else {
      ElMessage.error('SQL执行失败，请检查语法')
    }
  } catch (err) {
    console.error('执行SQL失败:', err)
    ElMessage.error('执行请求失败，请稍后重试')
  } finally {
    sqlRunning.value = false
  }
}

const nextExercise = () => {
  if (nextExerciseId.value) {
    router.push(`/exercises/${nextExerciseId.value}`)
  }
}
</script>

<style scoped>
.exercise-detail {
  padding: 40px 0;
  min-height: calc(100vh - 60px);
  background-color: #f5f7fa;
}

.container {
  max-width: 900px;
  margin: 0 auto;
  padding: 0 20px;
}

.loading {
  text-align: center;
  padding: 100px 0;
}

.exercise-header {
  background: white;
  border-radius: 12px;
  padding: 40px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  margin-bottom: 30px;
}

.exercise-tags {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.exercise-title {
  font-size: 28px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 20px;
  line-height: 1.4;
}

.exercise-meta {
  display: flex;
  gap: 30px;
  flex-wrap: wrap;
  padding-top: 20px;
  border-top: 1px solid #ebeef5;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #909399;
}

.section {
  margin-bottom: 30px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 20px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 16px;
}

.content-card {
  background: white;
  border-radius: 12px;
  padding: 30px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.description {
  font-size: 16px;
  line-height: 1.8;
  color: #303133;
  margin: 0;
}

.instructions {
  font-size: 14px;
  line-height: 1.8;
  color: #606266;
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
  background-color: #f5f7fa;
  padding: 16px;
  border-radius: 8px;
  font-family: monospace;
}

.answer-actions {
  display: flex;
  justify-content: flex-end;
  gap: 16px;
  margin-top: 20px;
}

.solution-card {
  border-left: 4px solid #67c23a;
}

.solution {
  font-size: 15px;
  line-height: 1.8;
  color: #303133;
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
  background-color: #f0f9ff;
  padding: 20px;
  border-radius: 8px;
  font-family: monospace;
}

.bottom-actions {
  display: flex;
  justify-content: space-between;
  margin-top: 40px;
}

.empty-state {
  padding: 80px 0;
  text-align: center;
}

@media (max-width: 768px) {
  .exercise-header,
  .content-card {
    padding: 24px;
  }
  
  .exercise-title {
    font-size: 22px;
  }
  
  .exercise-meta {
    gap: 20px;
  }
  
  .section-title {
    font-size: 18px;
  }
}

.sql-actions {
  display: flex;
  justify-content: flex-start;
  gap: 16px;
  margin-top: 16px;
  margin-bottom: 20px;
}

.sql-result {
  margin-top: 20px;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  overflow: hidden;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background-color: #f5f7fa;
  border-bottom: 1px solid #e4e7ed;
  font-weight: 600;
}

.result-error {
  padding: 16px;
  background-color: #fef0f0;
  color: #f56c6c;
  font-family: monospace;
  white-space: pre-wrap;
}

.result-table {
  padding: 16px;
}

.result-summary {
  padding: 12px 16px;
  background-color: #f5f7fa;
  color: #909399;
  font-size: 13px;
  text-align: right;
}

.result-message {
  padding: 16px;
  background-color: #f0f9eb;
  color: #67c23a;
}
</style>
