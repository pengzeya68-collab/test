<template>
  <div class="exercise-detail-container">
    <div class="exercise-header-panel" v-if="!loading && exercise">
      <div class="tag-group">
        <span class="tag-badge type">{{ getModuleName(exercise.module) }}</span>
        <span class="tag-badge stage">阶段{{ exercise.stage }}</span>
        <span class="tag-badge level">{{ getDifficultyText(exercise.difficulty) }}</span>
        <span class="tag-badge subject" v-if="exercise.knowledge_point">{{ exercise.knowledge_point }}</span>
      </div>
      <h1 class="exercise-main-title">{{ exercise.title }}</h1>
      <div class="meta-info">
        <span>⏱️ 预计 {{ exercise.time_estimate }} 分钟</span>
        <span>📁 {{ exercise.category }}</span>
        <span>📅 更新于 {{ formatDate(exercise.updated_at) }}</span>
      </div>
    </div>

    <div class="loading-center" v-if="loading">
      ⏳ 加载中...
    </div>

    <div class="empty-center" v-if="!loading && !exercise">
      <p>习题不存在</p>
      <button class="btn-purple-glow" @click="goBack">返回列表</button>
    </div>

    <template v-if="!loading && exercise">
      <section class="exercise-content-section">
        <div class="section-title-bar">
          <h3>📝 题目描述</h3>
        </div>
        <div class="info-box-fallback">
          <p style="white-space: pre-wrap;">{{ exercise.description }}</p>
        </div>
      </section>

      <section class="exercise-content-section" v-if="exercise.instructions">
        <div class="section-title-bar">
          <h3>📋 答题要求</h3>
        </div>
        <div class="info-box-fallback">
          <pre class="instructions-text">{{ exercise.instructions }}</pre>
        </div>
      </section>

      <section class="exercise-content-section">
        <div class="section-title-bar">
          <h3>✍️ 我的答案</h3>
        </div>

        <div class="answer-block">
          <CodeEditor
            v-if="exercise?.exercise_type === 'code'"
            v-model="userCode"
            :language="exercise.language?.toLowerCase() || 'python'"
            :template="exercise.code_template"
            @run="onCodeRun"
          />

          <div v-else-if="isChoiceType" class="options-wrapper">
            <div
              v-for="opt in choiceOptions"
              :key="opt.key"
              class="option-item"
              :class="{ active: userAnswer === opt.key }"
              @click="userAnswer = opt.key"
            >
              <span class="option-radio">{{ opt.key }}.</span>
              <span class="option-text">{{ opt.text }}</span>
            </div>
          </div>

          <div v-else-if="exercise?.language?.toLowerCase() === 'sql'" class="sql-block">
            <CodeEditor
              v-model="userSql"
              language="sql"
              :template="''"
              @run="runSql"
            />
            <div class="sql-result-panel" v-if="sqlResult">
              <div class="sql-result-header">
                <span>执行结果 ({{ sqlResult.elapsed_ms }}ms)</span>
                <span class="sql-result-tag" :class="sqlResult.success ? 'success' : 'fail'">
                  {{ sqlResult.success ? '成功' : '失败' }}
                </span>
              </div>
              <div v-if="!sqlResult.success" class="sql-result-error">{{ sqlResult.error }}</div>
              <div v-if="sqlResult.success && sqlResult.columns?.length" class="sql-result-table-wrap">
                <table class="sql-result-table">
                  <thead>
                    <tr>
                      <th v-for="col in sqlResult.columns" :key="col">{{ col }}</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="(row, ri) in sqlResult.rows" :key="ri">
                      <td v-for="col in sqlResult.columns" :key="col">{{ row[col] }}</td>
                    </tr>
                  </tbody>
                </table>
                <div class="sql-result-count">返回 {{ sqlResult.row_count }} 行记录</div>
              </div>
              <div v-if="sqlResult.success && sqlResult.message" class="sql-result-msg">{{ sqlResult.message }}</div>
            </div>

            <div class="action-button-group" style="margin-top: 16px;">
              <button class="btn-purple-glow" @click="runSql" :disabled="sqlRunning">
                {{ sqlRunning ? '运行中...' : '运行SQL' }}
              </button>
              <button class="btn-outline" @click="showSolution = true">查看答案</button>
              <button class="btn-green-glow" @click="submitAnswer" :disabled="submitting">
                {{ submitting ? '判题中...' : '提交答案' }}
              </button>
            </div>
          </div>

          <textarea
            v-else
            v-model="userAnswer"
            class="answer-textarea"
            placeholder="请在此输入你的答案..."
            rows="8"
          ></textarea>
        </div>

        <div class="action-button-group" v-if="!isChoiceType && exercise?.language?.toLowerCase() !== 'sql' && exercise?.exercise_type !== 'code'">
          <button class="btn-purple-glow" @click="showSolution = true">查看答案</button>
          <button class="btn-green-glow" @click="submitAnswer" :disabled="submitting">
            {{ submitting ? '判题中...' : '提交答案' }}
          </button>
        </div>
        <div class="action-button-group" v-if="isChoiceType">
          <button class="btn-purple-glow" @click="showSolution = true">查看答案</button>
          <button class="btn-green-glow" @click="submitAnswer" :disabled="submitting">
            {{ submitting ? '判题中...' : '提交答案' }}
          </button>
        </div>
      </section>

      <section class="exercise-content-section" v-if="submitResult">
        <div class="section-title-bar">
          <h3>✅ 判题结果</h3>
        </div>
        <div class="judge-panel" :class="{ 'judge-pass': submitResult.correct, 'judge-fail': !submitResult.correct }">
          <div class="judge-status-row">
            <span class="judge-tag" :class="submitResult.correct ? 'success' : 'fail'">
              {{ submitResult.correct ? '✓ 通过' : '✗ 未通过' }}
            </span>
            <span class="judge-msg">{{ submitResult.message }}</span>
          </div>
          <div v-if="submitResult.judge_result" class="judge-body">
            <div class="judge-stats-row">
              <span>通过 {{ submitResult.judge_result.passed_count }}/{{ submitResult.judge_result.total_cases }} 个测试用例</span>
              <span>通过率 {{ submitResult.judge_result.pass_rate }}%</span>
            </div>
            <div v-if="submitResult.judge_result.details?.length" class="judge-case-list">
              <div
                v-for="detail in submitResult.judge_result.details"
                :key="detail.case_index"
                class="judge-case-item"
                :class="detail.passed ? 'case-ok' : 'case-ng'"
              >
                <span class="case-index">用例 {{ detail.case_index }}</span>
                <span class="case-badge" :class="detail.passed ? 'success' : 'fail'">{{ detail.passed ? '通过' : '未通过' }}</span>
                <div v-if="!detail.passed" class="case-fail-detail">
                  <div><span>预期：</span><code>{{ detail.expected }}</code></div>
                  <div><span>实际：</span><code>{{ detail.actual }}</code></div>
                  <div v-if="detail.error"><span>错误：</span><code class="code-warn">{{ detail.error }}</code></div>
                </div>
              </div>
            </div>
            <div class="judge-footer">{{ submitResult.judge_result.summary }}</div>
          </div>
        </div>
      </section>

      <section class="exercise-content-section" v-if="submitResult?.correct && submitResult.skill_change?.length">
        <div class="section-title-bar">
          <h3>📈 技能提升</h3>
        </div>
        <div class="skill-panel">
          <div class="skill-item" v-for="sc in submitResult.skill_change" :key="sc.key">
            <span class="skill-name">{{ sc.name }}</span>
            <div class="skill-bar-wrap">
              <div class="skill-bar-bg">
                <div class="skill-bar-before" :style="{ width: sc.before + '%' }"></div>
                <div class="skill-bar-after" :style="{ width: sc.after + '%' }"></div>
              </div>
            </div>
            <span class="skill-score">{{ sc.before }} → {{ sc.after }}</span>
            <span class="skill-gain">+{{ sc.change }}</span>
          </div>
        </div>
      </section>

      <section class="exercise-content-section" v-if="showSolution">
        <div class="section-title-bar">
          <h3>💡 参考答案</h3>
        </div>
        <div class="solution-card">
          <pre class="solution-text">{{ exercise.solution }}</pre>
        </div>
      </section>

      <section class="exercise-content-section">
        <div class="section-title-bar">
          <h3>📖 学习笔记</h3>
        </div>
        <div class="notebook-container">
          <div class="note-list" v-if="exerciseNotes.length > 0">
            <div v-for="note in exerciseNotes" :key="note.id" class="note-entry">
              <div class="note-entry-header">
                <span class="note-entry-title">{{ note.title }}</span>
                <span class="note-entry-time">{{ note.updated_at }}</span>
                <button class="note-delete-btn" @click="deleteNote(note.id)">删除</button>
              </div>
              <div class="note-entry-body">{{ note.content }}</div>
            </div>
          </div>
          <input v-model="newNoteTitle" type="text" class="note-title-input" placeholder="笔记标题（如：关键知识点）" />
          <textarea v-model="newNoteContent" class="note-content-textarea" placeholder="记录你的理解、思路、易错点..." rows="3"></textarea>
          <button class="btn-save-note" @click="saveNote" :disabled="noteSaving">
            {{ noteSaving ? '保存中...' : '保存笔记' }}
          </button>
        </div>
      </section>

      <section class="exercise-content-section" v-if="relatedExercises.length > 0">
        <div class="section-title-bar">
          <h3>📊 相关推荐</h3>
        </div>
        <div class="recommend-grid">
          <div
            v-for="rel in relatedExercises"
            :key="rel.id"
            class="recommend-card"
            :class="{ 'rec-done': rel.completed }"
            @click="goToExercise(rel.id)"
          >
            <span class="rec-status-icon">{{ rel.completed ? '✅' : '⬜' }}</span>
            <h4 class="rec-card-title">{{ rel.title }}</h4>
            <div class="rec-card-meta">
              <span class="rec-badge-diff" :class="'diff-' + rel.difficulty">{{ getDifficultyText(rel.difficulty) }}</span>
              <span class="rec-subject-text" v-if="rel.knowledge_point">{{ rel.knowledge_point }}</span>
            </div>
          </div>
        </div>
      </section>

      <div class="bottom-navigation-bar">
        <button class="btn-outline" @click="goBack">返回列表</button>
        <button class="btn-purple-glow" v-if="nextExerciseId" @click="nextExercise">下一题</button>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import request from '@/utils/request'
import { ElMessage } from 'element-plus'
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
  return t === 'choice' || t === 'single_choice' || t === 'multiple_choice' || t === 'true_false'
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
    if (relatedExercises.value.length > 0) {
      nextExerciseId.value = relatedExercises.value[0].id
    }
  } catch {}
}

const fetchNotes = async () => {
  try {
    const res = await request.get('/notes', { params: { exercise_id: exerciseId } })
    exerciseNotes.value = res.notes || []
  } catch {}
}

const saveNote = async () => {
  if (!newNoteTitle.value.trim()) {
    ElMessage.warning('请输入笔记标题')
    return
  }
  noteSaving.value = true
  try {
    await request.post('/notes', {
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
  } catch (error) {
    console.error('获取习题详情失败:', error)
    ElMessage.error('获取习题详情失败')
    exercise.value = null
  } finally {
    loading.value = false
  }
}

const getDifficultyText = (difficulty) => {
  const map = {
    easy: '简单', medium: '中等', hard: '困难',
    beginner: '初级', intermediate: '中级', advanced: '高级',
  }
  return map[difficulty] || difficulty
}

const getModuleName = (module) => {
  const map = { normal: '普通习题', automation: '自动化测试', api: '接口测试' }
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
  } catch {
    ElMessage.error('提交失败，请稍后重试')
  } finally {
    submitting.value = false
  }
}

const goBack = () => { router.back() }
const onCodeRun = (result) => { console.log('代码运行结果:', result) }

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
  } catch {
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
.exercise-detail-container {
  width: 100%;
  min-height: 100vh;
  background-color: var(--tm-bg-page);
  color: var(--tm-text-primary);
  padding: 40px;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  gap: 36px;
}

/* ========== Header ========== */
.exercise-header-panel {
  background: var(--tm-card-bg);
  border: 1px solid #27272a;
  border-radius: 12px;
  padding: 28px;
  width: 100%;
  box-sizing: border-box;
}
.tag-group { display: flex; gap: 8px; margin-bottom: 16px; flex-wrap: wrap; }
.tag-badge {
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
  background: var(--bg-surface-hover);
  color: var(--tm-text-regular);
}
.tag-badge.type { background: rgba(99, 102, 241, 0.15); color: #a5b4fc; }
.tag-badge.stage { background: rgba(52, 211, 153, 0.12); color: #6ee7b7; }
.tag-badge.level { background: rgba(251, 191, 36, 0.12); color: #fcd34d; }
.tag-badge.subject { background: rgba(var(--tm-color-primary-rgb), 0.12); color: var(--tm-color-primary); }

.exercise-main-title {
  font-size: 26px;
  font-weight: 700;
  color: var(--tm-text-primary);
  margin: 0 0 14px;
  line-height: 1.4;
}
.meta-info {
  display: flex;
  gap: 24px;
  flex-wrap: wrap;
  font-size: 13px;
  color: var(--tm-text-secondary);
}

.loading-center, .empty-center {
  text-align: center;
  padding: 80px 0;
  color: #52525b;
}

/* ========== Sections ========== */
.exercise-content-section {
  width: 100%;
}
.section-title-bar {
  width: 100%;
  margin-bottom: 14px;
}
.section-title-bar h3 {
  font-size: 18px;
  font-weight: 700;
  color: var(--tm-text-primary);
  margin: 0;
}
.info-box-fallback {
  background: var(--tm-card-bg);
  border: 1px solid #27272a;
  border-radius: 10px;
  padding: 24px;
  width: 100%;
  box-sizing: border-box;
}
.info-box-fallback p {
  margin: 0;
  color: var(--tm-text-regular);
  line-height: 1.8;
  font-size: 15px;
}
.instructions-text {
  margin: 0;
  color: var(--tm-text-regular);
  font-family: 'Courier New', monospace;
  font-size: 14px;
  line-height: 1.8;
  white-space: pre-wrap;
}

/* ========== Answer Block ========== */
.answer-block {
  width: 100%;
}
.answer-textarea {
  width: 100%;
  box-sizing: border-box;
  background: var(--tm-card-bg);
  border: 1px solid #27272a;
  border-radius: 10px;
  color: var(--tm-text-regular);
  padding: 16px;
  font-size: 15px;
  line-height: 1.8;
  resize: vertical;
  outline: none;
  font-family: 'Courier New', monospace;
}
.answer-textarea:focus {
  border-color: rgba(var(--tm-color-primary-rgb), 0.4);
}

/* ========== Options - FULL WIDTH ROWS ========== */
.options-wrapper {
  display: flex;
  flex-direction: column;
  gap: 12px;
  width: 100%;
}
.option-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  width: 100%;
  box-sizing: border-box;
  padding: 16px 20px;
  background: var(--tm-card-bg);
  border: 2px solid #27272a;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s ease;
}
.option-item:hover {
  border-color: rgba(var(--tm-color-primary-rgb), 0.3);
  background: rgba(var(--tm-color-primary-rgb), 0.06);
}
.option-item.active {
  border-color: var(--tm-color-primary);
  background: rgba(var(--tm-color-primary-rgb), 0.1);
}
.option-radio {
  font-size: 16px;
  font-weight: 700;
  color: var(--tm-color-primary);
  flex-shrink: 0;
  min-width: 24px;
  line-height: 1.6;
}
.option-text {
  font-size: 15px;
  color: var(--tm-text-regular);
  line-height: 1.6;
}

/* ========== Action Buttons - LEFT ALIGNED ========== */
.action-button-group {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-top: 20px;
  justify-content: flex-start;
}

.btn-purple-glow {
  padding: 10px 28px;
  background: linear-gradient(135deg, var(--tm-color-primary), var(--tm-color-primary-dark));
  border: none;
  border-radius: 8px;
  color: #fff;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  box-shadow: 0 2px 14px rgba(var(--tm-color-primary-rgb), 0.3);
  transition: all 0.3s ease;
}
.btn-purple-glow:hover { transform: translateY(-2px); box-shadow: 0 6px 24px rgba(var(--tm-color-primary-rgb), 0.45); }
.btn-purple-glow:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }

.btn-green-glow {
  padding: 10px 28px;
  background: linear-gradient(135deg, #34d399, #059669);
  border: none;
  border-radius: 8px;
  color: #fff;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  box-shadow: 0 2px 14px rgba(52, 211, 153, 0.3);
  transition: all 0.3s ease;
}
.btn-green-glow:hover { transform: translateY(-2px); box-shadow: 0 6px 24px rgba(52, 211, 153, 0.45); }
.btn-green-glow:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }

.btn-outline {
  padding: 10px 24px;
  background: transparent;
  border: 1px solid var(--tm-border-light);
  border-radius: 8px;
  color: var(--tm-text-regular);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}
.btn-outline:hover { border-color: var(--tm-color-primary); color: var(--tm-color-primary); }

/* ========== SQL ========== */
.sql-block { width: 100%; }
.sql-result-panel {
  margin-top: 16px;
  border: 1px solid #27272a;
  border-radius: 10px;
  overflow: hidden;
}
.sql-result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: rgba(255, 255, 255, 0.03);
  border-bottom: 1px solid #27272a;
  font-size: 14px;
  color: var(--tm-text-regular);
  font-weight: 600;
}
.sql-result-tag {
  padding: 2px 10px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
}
.sql-result-tag.success { background: rgba(52, 211, 153, 0.15); color: #34d399; }
.sql-result-tag.fail { background: rgba(248, 113, 113, 0.15); color: #f87171; }
.sql-result-error {
  padding: 14px 16px;
  background: rgba(248, 113, 113, 0.06);
  color: #f87171;
  font-family: monospace;
  font-size: 13px;
  white-space: pre-wrap;
}
.sql-result-table-wrap { padding: 12px; }
.sql-result-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
.sql-result-table th, .sql-result-table td {
  border: 1px solid #27272a;
  padding: 8px 12px;
  text-align: left;
  color: var(--tm-text-regular);
}
.sql-result-table th {
  background: rgba(255, 255, 255, 0.04);
  font-weight: 600;
  color: var(--tm-text-primary);
}
.sql-result-count {
  text-align: right;
  padding: 10px 12px;
  font-size: 12px;
  color: var(--tm-text-secondary);
}
.sql-result-msg {
  padding: 14px 16px;
  background: rgba(52, 211, 153, 0.06);
  color: #34d399;
  font-size: 14px;
}

/* ========== Judge Panel ========== */
.judge-panel {
  padding: 24px;
  border-radius: 10px;
  border: 1px solid #27272a;
  width: 100%;
  box-sizing: border-box;
}
.judge-panel.judge-pass { border-color: rgba(52, 211, 153, 0.25); background: rgba(52, 211, 153, 0.04); }
.judge-panel.judge-fail { border-color: rgba(248, 113, 113, 0.25); background: rgba(248, 113, 113, 0.04); }
.judge-status-row {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 14px;
}
.judge-tag {
  padding: 4px 14px;
  border-radius: 4px;
  font-size: 14px;
  font-weight: 700;
}
.judge-tag.success { background: rgba(52, 211, 153, 0.18); color: #34d399; }
.judge-tag.fail { background: rgba(248, 113, 113, 0.18); color: #f87171; }
.judge-msg { font-size: 15px; font-weight: 600; color: var(--tm-text-primary); }
.judge-stats-row {
  display: flex;
  gap: 24px;
  font-size: 13px;
  color: var(--tm-text-regular);
  margin-bottom: 14px;
}
.judge-case-list { display: flex; flex-direction: column; gap: 10px; margin-bottom: 14px; }
.judge-case-item {
  padding: 12px 16px;
  border-radius: 8px;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
}
.judge-case-item.case-ok { background: rgba(52, 211, 153, 0.06); border: 1px solid rgba(52, 211, 153, 0.12); }
.judge-case-item.case-ng { background: rgba(248, 113, 113, 0.06); border: 1px solid rgba(248, 113, 113, 0.12); }
.case-index { font-size: 14px; font-weight: 600; color: var(--tm-text-primary); min-width: 60px; }
.case-badge {
  padding: 2px 10px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
}
.case-badge.success { background: rgba(52, 211, 153, 0.15); color: #34d399; }
.case-badge.fail { background: rgba(248, 113, 113, 0.15); color: #f87171; }
.case-fail-detail {
  width: 100%;
  margin-top: 6px;
  padding: 10px 12px;
  background: rgba(var(--tm-bg-page-rgb), 0.5);
  border-radius: 6px;
  font-size: 13px;
  color: var(--tm-text-regular);
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.case-fail-detail code {
  color: #f87171;
  font-family: 'Courier New', monospace;
  font-size: 12px;
  background: rgba(var(--tm-bg-page-rgb), 0.5);
  padding: 2px 6px;
  border-radius: 4px;
}
.code-warn { color: #fbbf24 !important; }
.judge-footer {
  font-size: 14px;
  color: var(--tm-text-regular);
  padding-top: 12px;
  border-top: 1px solid #27272a;
}

/* ========== Skill Panel ========== */
.skill-panel {
  background: rgba(var(--tm-color-primary-rgb), 0.04);
  border: 1px solid rgba(var(--tm-color-primary-rgb), 0.12);
  border-radius: 10px;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  width: 100%;
  box-sizing: border-box;
}
.skill-item {
  display: flex;
  align-items: center;
  gap: 16px;
}
.skill-name { font-size: 14px; font-weight: 600; color: var(--tm-text-primary); min-width: 80px; }
.skill-bar-wrap { flex: 1; }
.skill-bar-bg {
  height: 12px;
  border-radius: 6px;
  background: var(--tm-border-light);
  position: relative;
  overflow: hidden;
}
.skill-bar-before {
  position: absolute; top: 0; left: 0;
  height: 100%;
  background: rgba(var(--tm-color-primary-rgb), 0.2);
  border-radius: 6px;
  transition: width 0.5s ease;
}
.skill-bar-after {
  position: absolute; top: 0; left: 0;
  height: 100%;
  background: linear-gradient(90deg, var(--tm-color-primary), var(--tm-color-primary-dark));
  border-radius: 6px;
  transition: width 0.8s ease;
  animation: barAnim 0.8s ease-out;
}
@keyframes barAnim { from { width: 0 !important; } }
.skill-score { font-size: 13px; color: var(--tm-text-regular); min-width: 80px; text-align: center; font-variant-numeric: tabular-nums; }
.skill-gain { font-size: 16px; font-weight: 800; color: #34d399; min-width: 40px; text-align: right; }

/* ========== Solution ========== */
.solution-card {
  border-left: 4px solid #34d399;
  padding: 20px 24px;
  background: rgba(52, 211, 153, 0.04);
  border-radius: 0 10px 10px 0;
  width: 100%;
  box-sizing: border-box;
}
.solution-text {
  margin: 0;
  font-family: 'Courier New', monospace;
  font-size: 15px;
  color: var(--tm-text-regular);
  line-height: 1.8;
  white-space: pre-wrap;
}

/* ========== Notes ========== */
.notebook-container {
  width: 100%;
}
.note-list { margin-bottom: 16px; display: flex; flex-direction: column; gap: 10px; }
.note-entry {
  padding: 14px 16px;
  background: rgba(var(--tm-color-primary-rgb), 0.04);
  border: 1px solid rgba(var(--tm-color-primary-rgb), 0.08);
  border-radius: 10px;
}
.note-entry-header { display: flex; align-items: center; gap: 12px; margin-bottom: 6px; }
.note-entry-title { font-size: 14px; font-weight: 600; color: var(--tm-text-primary); }
.note-entry-time { font-size: 12px; color: var(--tm-text-secondary); }
.note-delete-btn {
  background: none;
  border: none;
  color: #f87171;
  font-size: 12px;
  cursor: pointer;
}
.note-entry-body { font-size: 13px; color: var(--tm-text-regular); line-height: 1.6; white-space: pre-wrap; }
.note-title-input, .note-content-textarea {
  width: 100%;
  box-sizing: border-box;
  background: var(--tm-card-bg);
  border: 1px solid #27272a;
  border-radius: 8px;
  color: var(--tm-text-regular);
  padding: 10px 14px;
  font-size: 14px;
  outline: none;
  margin-bottom: 10px;
}
.note-content-textarea { resize: vertical; font-family: inherit; min-height: 80px; }
.note-title-input:focus, .note-content-textarea:focus { border-color: rgba(var(--tm-color-primary-rgb), 0.4); }
.btn-save-note {
  padding: 8px 22px;
  background: linear-gradient(135deg, var(--tm-color-primary), var(--tm-color-primary-dark));
  border: none;
  border-radius: 8px;
  color: #fff;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}
.btn-save-note:hover { transform: translateY(-1px); box-shadow: 0 4px 16px rgba(var(--tm-color-primary-rgb), 0.3); }

/* ========== Recommend Grid - 3 COLS ========== */
.recommend-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  width: 100%;
}
.recommend-card {
  padding: 20px;
  background: var(--tm-card-bg);
  border: 1px solid #27272a;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.3s ease;
}
.recommend-card:hover {
  transform: translateY(-3px);
  border-color: rgba(var(--tm-color-primary-rgb), 0.25);
  box-shadow: 0 6px 20px rgba(var(--tm-color-primary-rgb), 0.1);
}
.recommend-card.rec-done {
  border-left: 3px solid #34d399;
  opacity: 0.75;
}
.rec-status-icon { font-size: 14px; margin-right: 6px; }
.rec-card-title {
  font-size: 15px;
  font-weight: 700;
  color: var(--tm-text-primary);
  margin: 8px 0 10px;
  line-height: 1.4;
}
.rec-card-meta { display: flex; align-items: center; gap: 8px; }
.rec-badge-diff {
  padding: 3px 10px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
}
.rec-badge-diff.diff-easy, .rec-badge-diff.diff-beginner { background: rgba(52, 211, 153, 0.12); color: #34d399; }
.rec-badge-diff.diff-medium, .rec-badge-diff.diff-intermediate { background: rgba(251, 191, 36, 0.12); color: #fbbf24; }
.rec-badge-diff.diff-hard, .rec-badge-diff.diff-advanced { background: rgba(248, 113, 113, 0.12); color: #f87171; }
.rec-subject-text { font-size: 12px; color: var(--tm-text-secondary); }

/* ========== Bottom Bar ========== */
.bottom-navigation-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 8px;
  padding-top: 24px;
  border-top: 1px solid #27272a;
}

/* ========== Responsive ========== */
@media (max-width: 1000px) {
  .recommend-grid { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 640px) {
  .exercise-detail-container { padding: 20px; gap: 24px; }
  .recommend-grid { grid-template-columns: 1fr; }
  .exercise-main-title { font-size: 20px; }
  .meta-info { gap: 14px; }
}
</style>