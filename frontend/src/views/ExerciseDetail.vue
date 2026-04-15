﻿<template>
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
            <p class="description" style="white-space: pre-wrap;">{{ exercise.description }}</p>
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

            <!-- 选择题 -->
            <div v-else-if="isChoiceType" class="choice-area">
              <el-radio-group v-model="userAnswer" class="choice-group">
                <el-radio
                  v-for="opt in choiceOptions"
                  :key="opt.key"
                  :value="opt.key"
                  class="choice-option"
                  size="large"
                >
                  <span class="choice-label">{{ opt.key }}.</span>
                  <span class="choice-text">{{ opt.text }}</span>
                </el-radio>
              </el-radio-group>
              <div class="answer-actions">
                <el-button type="primary" @click="showSolution = true">
                  查看答案
                </el-button>
                <el-button type="success" @click="submitAnswer" :loading="submitting">
                  {{ submitting ? '判题中...' : '提交答案' }}
                </el-button>
              </div>
            </div>
            
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
                <el-button type="success" @click="submitAnswer" :loading="submitting">
                  {{ submitting ? '判题中...' : '提交答案' }}
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
              <el-button type="success" @click="submitAnswer" :loading="submitting">
                {{ submitting ? '判题中...' : '提交答案' }}
              </el-button>
            </div>
          </div>
        </div>

        <!-- 判题结果 -->
        <div class="section" v-if="submitResult">
          <h2 class="section-title">
            <el-icon size="24"><Check /></el-icon>
            判题结果
          </h2>
          <div class="content-card judge-card" :class="{ 'judge-pass': submitResult.correct, 'judge-fail': !submitResult.correct }">
            <div class="judge-header">
              <el-tag :type="submitResult.correct ? 'success' : 'danger'" size="large" effect="dark">
                {{ submitResult.correct ? '✓ 通过' : '✗ 未通过' }}
              </el-tag>
              <span class="judge-message">{{ submitResult.message }}</span>
            </div>
            <div v-if="submitResult.judge_result" class="judge-details">
              <div class="judge-stats">
                <span>通过 {{ submitResult.judge_result.passed_count }}/{{ submitResult.judge_result.total_cases }} 个测试用例</span>
                <span>通过率 {{ submitResult.judge_result.pass_rate }}%</span>
              </div>
              <div v-if="submitResult.judge_result.details?.length" class="case-list">
                <div
                  v-for="detail in submitResult.judge_result.details"
                  :key="detail.case_index"
                  class="case-item"
                  :class="{ 'case-pass': detail.passed, 'case-fail': !detail.passed }"
                >
                  <span class="case-label">用例 {{ detail.case_index }}</span>
                  <el-tag :type="detail.passed ? 'success' : 'danger'" size="small">
                    {{ detail.passed ? '通过' : '未通过' }}
                  </el-tag>
                  <div v-if="!detail.passed" class="case-detail">
                    <div class="case-row"><span>预期：</span><code>{{ detail.expected }}</code></div>
                    <div class="case-row"><span>实际：</span><code>{{ detail.actual }}</code></div>
                    <div v-if="detail.error" class="case-row case-error"><span>错误：</span><code>{{ detail.error }}</code></div>
                  </div>
                </div>
              </div>
              <div class="judge-summary">{{ submitResult.judge_result.summary }}</div>
            </div>
          </div>
        </div>

        <!-- 技能分数变化 -->
        <div class="section" v-if="submitResult?.correct && submitResult.skill_change?.length">
          <h2 class="section-title">
            <el-icon size="24"><TrendCharts /></el-icon>
            技能提升
          </h2>
          <div class="content-card skill-change-card">
            <div class="skill-change-list">
              <div
                v-for="sc in submitResult.skill_change"
                :key="sc.key"
                class="skill-change-item"
              >
                <span class="sc-name">{{ sc.name }}</span>
                <div class="sc-bar-wrap">
                  <div class="sc-bar-bg">
                    <div class="sc-bar-before" :style="{ width: sc.before + '%' }"></div>
                    <div class="sc-bar-after" :style="{ width: sc.after + '%' }"></div>
                  </div>
                </div>
                <span class="sc-scores">{{ sc.before }} → {{ sc.after }}</span>
                <span class="sc-change">+{{ sc.change }}</span>
              </div>
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

        <!-- 学习笔记 -->
        <div class="section">
          <h2 class="section-title">
            <el-icon size="24"><Edit /></el-icon>
            学习笔记
          </h2>
          <div class="content-card notes-card">
            <div class="notes-list" v-if="exerciseNotes.length > 0">
              <div v-for="note in exerciseNotes" :key="note.id" class="note-item">
                <div class="note-header">
                  <span class="note-title">{{ note.title }}</span>
                  <span class="note-time">{{ note.updated_at }}</span>
                  <el-button type="danger" size="small" link @click="deleteNote(note.id)">删除</el-button>
                </div>
                <div class="note-content">{{ note.content }}</div>
              </div>
            </div>
            <div class="note-form">
              <el-input
                v-model="newNoteTitle"
                placeholder="笔记标题（如：关键知识点）"
                size="small"
                style="margin-bottom: 8px;"
              />
              <el-input
                v-model="newNoteContent"
                type="textarea"
                placeholder="记录你的理解、思路、易错点..."
                :rows="3"
                size="small"
              />
              <el-button
                type="primary"
                size="small"
                @click="saveNote"
                :loading="noteSaving"
                style="margin-top: 8px;"
              >
                保存笔记
              </el-button>
            </div>
          </div>
        </div>

        <!-- 推荐习题 -->
        <div class="section" v-if="relatedExercises.length > 0">
          <h2 class="section-title">
            <el-icon size="24"><List /></el-icon>
            相关推荐
          </h2>
          <div class="related-grid">
            <div
              v-for="rel in relatedExercises"
              :key="rel.id"
              class="related-card"
              :class="{ 'related-done': rel.completed }"
              @click="goToExercise(rel.id)"
            >
              <div class="related-header">
                <span class="related-status">{{ rel.completed ? '✅' : '⬜' }}</span>
                <h4 class="related-title">{{ rel.title }}</h4>
              </div>
              <div class="related-meta">
                <el-tag :type="getDifficultyType(rel.difficulty)" size="small">
                  {{ getDifficultyText(rel.difficulty) }}
                </el-tag>
                <span v-if="rel.knowledge_point" class="related-kp">{{ rel.knowledge_point }}</span>
              </div>
            </div>
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
import { ref, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { Timer, Collection, Calendar, Document, List, Edit, Check, Loading, VideoPlay, TrendCharts } from '@element-plus/icons-vue'
import request from '@/utils/request'
import { ElMessage, ElMessageBox } from 'element-plus'
import CodeEditor from '@/components/CodeEditor.vue'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const exercise = ref(null)
const loading = ref(false)
const submitting = ref(false)
const userAnswer = ref('')
const userCode = ref('')
const userSql = ref('')
const showSolution = ref(false)
const nextExerciseId = ref(null)
const submitResult = ref(null)
const relatedExercises = ref([])
const exerciseNotes = ref([])
const newNoteTitle = ref('')
const newNoteContent = ref('')
const noteSaving = ref(false)
const sqlRunning = ref(false)
const sqlResult = ref(null)
const exerciseId = route.params.id

const isChoiceType = computed(() => {
  const t = exercise.value?.exercise_type
  return t === 'choice' || t === 'multiple_choice' || t === 'true_false'
})

const choiceOptions = computed(() => {
  if (!exercise.value || !isChoiceType.value) return []
  const desc = exercise.value.description || ''
  const options = []
  const keys = ['A', 'B', 'C', 'D', 'E', 'F']
  for (const key of keys) {
    const regex = new RegExp(`^${key}[.．、:：]\\s*(.+)$`, 'm')
    const match = desc.match(regex)
    if (match) {
      options.push({ key, text: match[1].trim() })
    }
  }
  if (options.length === 0) {
    return keys.slice(0, 4).map(key => ({ key, text: '' }))
  }
  return options
})

onMounted(() => {
  fetchExerciseDetail()
  fetchRelatedExercises()
  fetchNotes()
})

const fetchRelatedExercises = async () => {
  try {
    const res = await request.get(`/exercise/${exerciseId}/related`)
    relatedExercises.value = res.related || []
  } catch {
    // silently fail
  }
}

const fetchNotes = async () => {
  try {
    const res = await request.get('/notes/', { params: { exercise_id: exerciseId } })
    exerciseNotes.value = res.notes || []
  } catch {
    // silently fail
  }
}

const saveNote = async () => {
  if (!newNoteTitle.value.trim()) {
    ElMessage.warning('请输入笔记标题')
    return
  }
  noteSaving.value = true
  try {
    await request.post('/notes/', {
      title: newNoteTitle.value,
      content: newNoteContent.value,
      exercise_id: parseInt(exerciseId),
    })
    ElMessage.success('笔记保存成功')
    newNoteTitle.value = ''
    newNoteContent.value = ''
    await fetchNotes()
  } catch {
    ElMessage.error('保存失败')
  } finally {
    noteSaving.value = false
  }
}

const deleteNote = async (noteId) => {
  try {
    await request.delete(`/notes/${noteId}`)
    ElMessage.success('笔记已删除')
    await fetchNotes()
  } catch {
    ElMessage.error('删除失败')
  }
}

const goToExercise = (id) => {
  router.push(`/exercises/${id}`)
}

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
    hard: '困难',
    beginner: '初级',
    intermediate: '中级',
    advanced: '高级',
  }
  return map[difficulty] || difficulty
}

const getDifficultyType = (difficulty) => {
  const map = {
    easy: 'success',
    medium: 'warning',
    hard: 'danger',
    beginner: 'success',
    intermediate: 'warning',
    advanced: 'danger',
  }
  return map[difficulty] || 'info'
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

const submitAnswer = async () => {
  let answerContent = exercise.value?.exercise_type === 'code' ? userCode.value : userAnswer.value
  if (exercise.value?.language?.toLowerCase() === 'sql') {
    answerContent = userSql.value
  }

  if (!answerContent || !answerContent.trim()) {
    ElMessage.warning('请输入答案后再提交')
    return
  }

  submitting.value = true
  try {
    const res = await request.post('/exercise/submit', {
      exercise_id: parseInt(exerciseId),
      solution: answerContent,
      exercise_type: exercise.value?.exercise_type || 'text',
      language: exercise.value?.language || 'python',
    })

    submitResult.value = res

    if (res.correct) {
      ElMessage.success('答案正确！技能分数已更新')
      userStore.checkNewAchievements()
    } else {
      ElMessage.warning('答案不正确，再试试看！')
    }
  } catch (error) {
    console.error('提交答案失败:', error)
    ElMessage.error('提交失败，请稍后重试')
  } finally {
    submitting.value = false
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
  background-color: var(--tm-bg-elevated);
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
  background: #18181B;
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
  color: var(--tm-text-primary);
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
  color: var(--tm-text-secondary);
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
  color: var(--tm-text-primary);
  margin-bottom: 16px;
}

.content-card {
  background: #18181B;
  border-radius: 12px;
  padding: 30px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.description {
  font-size: 16px;
  line-height: 1.8;
  color: var(--tm-text-primary);
  margin: 0;
}

.instructions {
  font-size: 14px;
  line-height: 1.8;
  color: var(--tm-text-regular);
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
  background-color: var(--tm-bg-elevated);
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
  color: var(--tm-text-primary);
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
  border: 1px solid var(--tm-border-color);
  border-radius: 8px;
  overflow: hidden;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background-color: var(--tm-bg-elevated);
  border-bottom: 1px solid var(--tm-border-color);
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
  background-color: var(--tm-bg-elevated);
  color: var(--tm-text-secondary);
  font-size: 13px;
  text-align: right;
}

.result-message {
  padding: 16px;
  background-color: #f0f9eb;
  color: #67c23a;
}

.judge-card {
  border-radius: 12px;
  padding: 24px;
}

.judge-pass {
  border: 1px solid rgba(103, 194, 58, 0.3);
  background: rgba(103, 194, 58, 0.05);
}

.judge-fail {
  border: 1px solid rgba(245, 108, 108, 0.3);
  background: rgba(245, 108, 108, 0.05);
}

.judge-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
}

.judge-message {
  font-size: 16px;
  font-weight: 600;
  color: var(--tm-text-primary);
}

.judge-stats {
  display: flex;
  gap: 24px;
  font-size: 14px;
  color: var(--tm-text-secondary);
  margin-bottom: 16px;
}

.case-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 16px;
}

.case-item {
  padding: 12px 16px;
  border-radius: 8px;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
}

.case-pass {
  background: rgba(103, 194, 58, 0.06);
  border: 1px solid rgba(103, 194, 58, 0.15);
}

.case-fail {
  background: rgba(245, 108, 108, 0.06);
  border: 1px solid rgba(245, 108, 108, 0.15);
}

.case-label {
  font-size: 14px;
  font-weight: 600;
  color: var(--tm-text-primary);
  min-width: 60px;
}

.case-detail {
  width: 100%;
  margin-top: 8px;
  padding: 10px 12px;
  background: rgba(0, 0, 0, 0.15);
  border-radius: 6px;
  font-size: 13px;
}

.case-row {
  display: flex;
  gap: 8px;
  margin-bottom: 4px;
  color: var(--tm-text-secondary);
}

.case-row code {
  color: #f56c6c;
  font-family: 'Courier New', monospace;
  font-size: 12px;
  word-break: break-all;
}

.case-error code {
  color: #e6a23c;
}

.judge-summary {
  font-size: 14px;
  color: var(--tm-text-secondary);
  padding-top: 12px;
  border-top: 1px solid var(--tm-border-light);
}

.skill-change-card {
  border: 1px solid rgba(139, 92, 246, 0.2);
  background: rgba(139, 92, 246, 0.03);
}

.skill-change-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.skill-change-item {
  display: flex;
  align-items: center;
  gap: 16px;
}

.sc-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--tm-text-primary);
  min-width: 80px;
}

.sc-bar-wrap {
  flex: 1;
}

.sc-bar-bg {
  height: 12px;
  border-radius: 6px;
  background: rgba(0, 0, 0, 0.06);
  position: relative;
  overflow: hidden;
}

.sc-bar-before {
  position: absolute;
  top: 0;
  left: 0;
  height: 100%;
  background: rgba(139, 92, 246, 0.2);
  border-radius: 6px;
  transition: width 0.5s ease;
}

.sc-bar-after {
  position: absolute;
  top: 0;
  left: 0;
  height: 100%;
  background: linear-gradient(90deg, #8b5cf6, #d946ef);
  border-radius: 6px;
  transition: width 0.8s ease;
  animation: scBarGrow 0.8s ease-out;
}

@keyframes scBarGrow {
  from { width: 0 !important; }
}

.sc-scores {
  font-size: 13px;
  color: var(--tm-text-secondary);
  min-width: 80px;
  text-align: center;
  font-variant-numeric: tabular-nums;
}

.sc-change {
  font-size: 16px;
  font-weight: 800;
  color: #67c23a;
  min-width: 40px;
  text-align: right;
}

.related-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 12px;
}

.related-card {
  padding: 16px;
  background: var(--tm-bg-card);
  border-radius: 10px;
  border: 1px solid var(--tm-border-light);
  cursor: pointer;
  transition: all 0.2s ease;
}

.related-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(139, 92, 246, 0.1);
  border-color: rgba(139, 92, 246, 0.2);
}

.related-card.related-done {
  border-left: 3px solid #67c23a;
  opacity: 0.75;
}

.related-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.related-status {
  font-size: 14px;
  flex-shrink: 0;
}

.related-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--tm-text-primary);
  margin: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.related-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}

.related-kp {
  font-size: 12px;
  color: var(--tm-text-secondary);
}

.notes-card {
  padding: 20px;
}

.notes-list {
  margin-bottom: 16px;
}

.note-item {
  padding: 12px 16px;
  background: rgba(139, 92, 246, 0.03);
  border-radius: 8px;
  border: 1px solid rgba(139, 92, 246, 0.08);
  margin-bottom: 8px;
}

.note-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 6px;
}

.note-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--tm-text-primary);
}

.note-time {
  font-size: 12px;
  color: var(--tm-text-secondary);
}

.note-content {
  font-size: 13px;
  color: var(--tm-text-secondary);
  line-height: 1.6;
  white-space: pre-wrap;
}

.note-form {
  border-top: 1px solid var(--tm-border-light);
  padding-top: 16px;
}

.choice-area {
  padding: 8px 0;
}

.choice-group {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.choice-option {
  padding: 14px 20px;
  border-radius: 10px;
  border: 2px solid var(--tm-border-light);
  transition: all 0.2s ease;
  margin: 0;
}

.choice-option:hover {
  border-color: rgba(139, 92, 246, 0.3);
  background: rgba(139, 92, 246, 0.03);
}

.choice-option.is-active {
  border-color: #8b5cf6;
  background: rgba(139, 92, 246, 0.06);
}

.choice-label {
  font-weight: 700;
  color: #8b5cf6;
  margin-right: 8px;
}

.choice-text {
  color: var(--tm-text-primary);
  line-height: 1.6;
}
</style>
