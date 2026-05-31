<template>
  <div class="oj-page">
    <div class="oj-loading" v-if="loading">
      <div class="loading-spinner"></div>
      <p>加载中...</p>
    </div>

    <div class="oj-empty" v-if="!loading && !exercise">
      <p>习题不存在</p>
      <button class="btn-purple-glow" @click="goBack">返回列表</button>
    </div>

    <template v-if="!loading && exercise">
      <div class="oj-topbar">
        <div class="topbar-left">
          <button class="topbar-btn back-btn" @click="goBack" title="返回列表">
            <span class="tb-icon">←</span>
          </button>
          <div class="progress-indicator">
            <span class="progress-text">第 <strong>{{ currentIndex + 1 }}</strong> / {{ totalCount }} 题</span>
          </div>
          <button class="topbar-btn nav-arrow" :disabled="currentIndex <= 0" @click="prevExercise" title="上一题">‹</button>
          <button class="topbar-btn nav-arrow" :disabled="!hasNextExercise" @click="nextExercise" title="下一题">›</button>
        </div>
        <div class="topbar-center">
          <span class="topbar-title">{{ exercise.title }}</span>
          <span class="tag-badge type" style="margin-left:10px;">{{ getModuleName(exercise.module) }}</span>
          <span class="tag-badge level" :class="'level-' + exercise.difficulty">{{ getDifficultyText(exercise.difficulty) }}</span>
        </div>
        <div class="topbar-right">
          <div class="timer-display" :class="{ 'timer-warning': elapsedSeconds > 600 }">
            <span class="timer-icon">⏱</span>
            <span class="timer-text">{{ formattedTime }}</span>
          </div>
        </div>
      </div>

      <div class="oj-split-layout" v-if="isCodeOrSqlType">
        <div
          class="oj-left-panel"
          :style="hasResized ? { width: leftPanelWidth + 'px', flex: 'none' } : {}"
        >
          <div class="left-panel-tabs">
            <button
              :class="['left-tab', { active: leftTab === 'desc' }]"
              @click="leftTab = 'desc'"
            >题目</button>
            <button
              :class="['left-tab', { active: leftTab === 'result' }]"
              @click="leftTab = 'result'"
              v-if="submitResult"
            >
              结果
              <span class="tab-dot" :class="submitResult.correct ? 'dot-green' : 'dot-red'"></span>
            </button>
            <button
              :class="['left-tab', { active: leftTab === 'skill' }]"
              @click="leftTab = 'skill'"
              v-if="submitResult?.correct && submitResult.skill_change?.length"
            >技能</button>
            <button
              :class="['left-tab', { active: leftTab === 'solution' }]"
              @click="leftTab = 'solution'"
              v-if="showSolution"
            >答案</button>
            <button
              :class="['left-tab', { active: leftTab === 'notes' }]"
              @click="leftTab = 'notes'"
            >笔记</button>
            <button
              :class="['left-tab', { active: leftTab === 'related' }]"
              @click="leftTab = 'related'"
              v-if="relatedExercises.length > 0"
            >推荐</button>
          </div>

          <div class="left-panel-body">
            <div v-if="leftTab === 'desc'" class="tab-content">
              <h2 class="problem-title">{{ exercise.title }}</h2>
              <div class="problem-meta">
                <span>⏱ {{ exercise.time_estimate }} 分钟</span>
                <span>📁 {{ exercise.category }}</span>
                <span v-if="exercise.knowledge_point">📌 {{ exercise.knowledge_point }}</span>
                <span>📅 {{ formatDate(exercise.updated_at) }}</span>
              </div>
              <div class="problem-section">
                <h4 class="section-label">题目描述</h4>
                <div class="section-body desc-body">
                  <p style="white-space: pre-wrap;">{{ exercise.description }}</p>
                </div>
              </div>
              <div class="problem-section" v-if="exercise.instructions">
                <h4 class="section-label">答题要求</h4>
                <div class="section-body">
                  <pre class="instructions-pre">{{ exercise.instructions }}</pre>
                </div>
              </div>
              <div class="problem-section" v-if="exercise.hint">
                <button class="hint-inline-btn" @click="showHintDialog">💡 查看提示</button>
              </div>
            </div>

            <div v-if="leftTab === 'result' && submitResult" class="tab-content">
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
            </div>

            <div v-if="leftTab === 'skill' && submitResult?.correct && submitResult.skill_change?.length" class="tab-content">
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
            </div>

            <div v-if="leftTab === 'solution'" class="tab-content">
              <div class="solution-card">
                <pre class="solution-text">{{ exercise.solution }}</pre>
              </div>
            </div>

            <div v-if="leftTab === 'notes'" class="tab-content">
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
                <input v-model="newNoteTitle" type="text" class="note-title-input" placeholder="笔记标题" />
                <textarea v-model="newNoteContent" class="note-content-textarea" placeholder="记录你的理解..." rows="3"></textarea>
                <button class="btn-save-note" @click="saveNote" :disabled="noteSaving">
                  {{ noteSaving ? '保存中...' : '保存笔记' }}
                </button>
              </div>
            </div>

            <div v-if="leftTab === 'related'" class="tab-content">
              <div class="recommend-list">
                <div
                  v-for="rel in relatedExercises"
                  :key="rel.id"
                  class="recommend-item"
                  :class="{ 'rec-done': rel.completed }"
                  @click="goToExercise(rel.id)"
                >
                  <span class="rec-status">{{ rel.completed ? '✅' : '⬜' }}</span>
                  <div class="rec-info">
                    <h4 class="rec-title">{{ rel.title }}</h4>
                    <div class="rec-meta">
                      <span class="rec-badge-diff" :class="'diff-' + rel.difficulty">{{ getDifficultyText(rel.difficulty) }}</span>
                      <span class="rec-subject" v-if="rel.knowledge_point">{{ rel.knowledge_point }}</span>
                    </div>
                  </div>
                  <span class="rec-arrow">›</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="oj-divider" @mousedown="startResize">
          <div class="divider-line"></div>
        </div>

        <div class="oj-right-panel">
          <div class="editor-wrapper" v-if="exercise?.exercise_type === 'code'">
            <CodeEditor
              v-model="userCode"
              :language="exercise.language?.toLowerCase() || 'python'"
              :template="exercise.code_template"
              @run="onCodeRun"
            />
          </div>

          <div class="editor-wrapper sql-editor-wrapper" v-else-if="exercise?.language?.toLowerCase() === 'sql'">
            <CodeEditor
              v-model="userSql"
              language="sql"
              :template="''"
              @run="runSql"
            />
          </div>

          <div class="editor-action-bar">
            <div class="action-bar-left">
              <button class="btn-hint-sm" @click="showHintDialog" v-if="exercise?.hint">💡 提示</button>
              <button class="btn-outline-sm" @click="viewSolution" v-if="!showSolution">查看答案</button>
            </div>
            <div class="action-bar-right">
              <button
                class="btn-run-sm"
                @click="runSql"
                :disabled="sqlRunning"
                v-if="exercise?.language?.toLowerCase() === 'sql'"
              >
                {{ sqlRunning ? '运行中...' : '▶ 运行SQL' }}
              </button>
              <button
                class="btn-submit-sm"
                @click="submitAnswer"
                :disabled="submitting"
              >
                {{ submitting ? '判题中...' : '✓ 提交' }}
              </button>
            </div>
          </div>

          <div class="shortcut-hint-bar">
            Ctrl+Enter 提交 · Ctrl+Shift+R 运行
          </div>

          <div class="output-panel" v-if="exercise?.language?.toLowerCase() === 'sql' && sqlResult">
            <div class="output-header">
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

          <div class="output-panel judge-quick-view" v-if="submitResult && isCodeOrSqlType">
            <div class="output-header">
              <span>判题结果</span>
              <span class="judge-quick-tag" :class="submitResult?.correct ? 'pass' : 'fail'">
                {{ submitResult?.correct ? '✓ 通过' : '✗ 未通过' }}
              </span>
            </div>
            <div class="judge-quick-body" v-if="submitResult?.judge_result">
              <span>通过 {{ submitResult.judge_result.passed_count }}/{{ submitResult.judge_result.total_cases }}</span>
              <button class="link-btn" @click="leftTab = 'result'">查看详情 ›</button>
            </div>
          </div>
        </div>
      </div>

      <div class="oj-choice-layout" v-else-if="isChoiceType">
        <div class="choice-scroll">
          <div class="choice-question-card">
            <div class="choice-tags">
              <span class="tag-badge type">{{ getModuleName(exercise.module) }}</span>
              <span class="tag-badge stage">阶段{{ exercise.stage }}</span>
              <span class="tag-badge level" :class="'level-' + exercise.difficulty">{{ getDifficultyText(exercise.difficulty) }}</span>
              <span class="tag-badge subject" v-if="exercise.knowledge_point">{{ exercise.knowledge_point }}</span>
            </div>
            <h2 class="choice-title">{{ exercise.title }}</h2>
            <div class="choice-desc" v-if="exercise.description && choiceOptions.length">
              <p style="white-space: pre-wrap;">{{ exercise.description }}</p>
            </div>
            <div class="choice-desc" v-if="exercise.instructions">
              <pre class="instructions-pre">{{ exercise.instructions }}</pre>
            </div>
          </div>

          <div class="choice-options">
            <div
              v-for="opt in choiceOptions"
              :key="opt.key"
              class="choice-option-card"
              :class="{
                'selected': isChoiceSelected(opt.key),
                'correct-answer': submitResult && !submitResult?.correct && opt.key === submitResult?.correct_answer,
                'wrong-answer': submitResult && !submitResult?.correct && isChoiceSelected(opt.key) && opt.key !== submitResult?.correct_answer,
                'my-correct': submitResult && submitResult?.correct && isChoiceSelected(opt.key),
                'disabled': !!submitResult
              }"
              @click="!submitResult && (isMultipleChoice ? toggleChoice(opt.key) : userAnswer = opt.key)"
            >
              <span class="option-label">{{ opt.key }}</span>
              <span class="option-text">{{ opt.text }}</span>
              <span class="option-check" v-if="isChoiceSelected(opt.key)">
                <template v-if="submitResult && !submitResult?.correct && opt.key !== submitResult?.correct_answer">✗</template>
                <template v-else>✓</template>
              </span>
            </div>
          </div>

          <div class="choice-actions">
            <button class="btn-hint" @click="showHintDialog" v-if="exercise?.hint">💡 提示</button>
            <button class="btn-outline" @click="showSolution = true">查看答案</button>
            <button class="btn-green-glow" @click="submitAnswer" :disabled="submitting || !hasChoiceAnswer">
              {{ submitting ? '判题中...' : '提交答案' }}
            </button>
          </div>

          <div class="choice-result" v-if="submitResult" :class="submitResult?.correct ? 'result-pass' : 'result-fail'">
            <div class="result-status">
              <span class="result-icon">{{ submitResult?.correct ? '🎉' : '❌' }}</span>
              <span class="result-text">{{ submitResult?.correct ? '回答正确！' : '回答错误' }}</span>
              <span class="result-msg">{{ submitResult?.message }}</span>
            </div>
            <div v-if="!submitResult?.correct && submitResult?.correct_answer" class="correct-answer-hint">
              正确答案：<strong>{{ submitResult?.correct_answer }}</strong>
            </div>
          </div>

          <div class="choice-skill" v-if="submitResult?.correct && submitResult.skill_change?.length">
            <h4 class="section-label">📈 技能提升</h4>
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
          </div>

          <div class="choice-solution" v-if="showSolution">
            <h4 class="section-label">💡 参考答案</h4>
            <div class="solution-card">
              <pre class="solution-text">{{ exercise.solution }}</pre>
            </div>
          </div>

          <div class="choice-notes">
            <h4 class="section-label">📖 学习笔记</h4>
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
              <input v-model="newNoteTitle" type="text" class="note-title-input" placeholder="笔记标题" />
              <textarea v-model="newNoteContent" class="note-content-textarea" placeholder="记录你的理解..." rows="3"></textarea>
              <button class="btn-save-note" @click="saveNote" :disabled="noteSaving">
                {{ noteSaving ? '保存中...' : '保存笔记' }}
              </button>
            </div>
          </div>

          <div class="choice-related" v-if="relatedExercises.length > 0">
            <h4 class="section-label">📊 相关推荐</h4>
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
          </div>
        </div>
      </div>

      <div class="oj-text-layout" v-else>
        <div class="text-scroll">
          <div class="text-question-card">
            <div class="text-tags">
              <span class="tag-badge type">{{ getModuleName(exercise.module) }}</span>
              <span class="tag-badge stage">阶段{{ exercise.stage }}</span>
              <span class="tag-badge level" :class="'level-' + exercise.difficulty">{{ getDifficultyText(exercise.difficulty) }}</span>
            </div>
            <h2 class="text-title">{{ exercise.title }}</h2>
            <div class="text-desc">
              <p style="white-space: pre-wrap;">{{ exercise.description }}</p>
            </div>
            <div class="text-instructions" v-if="exercise.instructions">
              <h4 class="section-label">答题要求</h4>
              <pre class="instructions-pre">{{ exercise.instructions }}</pre>
            </div>
          </div>

          <div class="text-answer-area">
            <h4 class="section-label">✍️ 我的答案</h4>
            <textarea
              v-model="userAnswer"
              class="answer-textarea"
              placeholder="请在此输入你的答案..."
              rows="8"
            ></textarea>
          </div>

          <div class="text-actions">
            <button class="btn-hint" @click="showHintDialog" v-if="exercise?.hint">💡 提示</button>
            <button class="btn-outline" @click="showSolution = true">查看答案</button>
            <button class="btn-green-glow" @click="submitAnswer" :disabled="submitting">
              {{ submitting ? '判题中...' : '提交答案' }}
            </button>
          </div>

          <div class="text-result" v-if="submitResult">
            <div class="judge-panel" :class="{ 'judge-pass': submitResult?.correct, 'judge-fail': !submitResult?.correct }">
              <div class="judge-status-row">
                <span class="judge-tag" :class="submitResult?.correct ? 'success' : 'fail'">
                  {{ submitResult?.correct ? '✓ 通过' : '✗ 未通过' }}
                </span>
                <span class="judge-msg">{{ submitResult?.message }}</span>
              </div>
              <div v-if="submitResult?.judge_result" class="judge-body">
                <div class="judge-stats-row">
                  <span>通过 {{ submitResult.judge_result.passed_count }}/{{ submitResult.judge_result.total_cases }} 个测试用例</span>
                  <span>通过率 {{ submitResult.judge_result.pass_rate }}%</span>
                </div>
                <div class="judge-footer">{{ submitResult.judge_result.summary }}</div>
              </div>
            </div>
          </div>

          <div class="text-skill" v-if="submitResult?.correct && submitResult.skill_change?.length">
            <h4 class="section-label">📈 技能提升</h4>
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
          </div>

          <div class="text-solution" v-if="showSolution">
            <h4 class="section-label">💡 参考答案</h4>
            <div class="solution-card">
              <pre class="solution-text">{{ exercise.solution }}</pre>
            </div>
          </div>

          <div class="text-notes">
            <h4 class="section-label">📖 学习笔记</h4>
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
              <input v-model="newNoteTitle" type="text" class="note-title-input" placeholder="笔记标题" />
              <textarea v-model="newNoteContent" class="note-content-textarea" placeholder="记录你的理解..." rows="3"></textarea>
              <button class="btn-save-note" @click="saveNote" :disabled="noteSaving">
                {{ noteSaving ? '保存中...' : '保存笔记' }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, computed, watch, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
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
const selectedChoices = ref([])
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

const leftTab = ref('desc')
const leftPanelWidth = ref(null)
const hasResized = ref(false)
const elapsedSeconds = ref(0)
const timerInterval = ref(null)

const isChoiceType = computed(() => {
  const t = exercise.value?.exercise_type
  return t === 'choice' || t === 'single_choice' || t === 'multiple_choice' || t === 'true_false'
})

const isMultipleChoice = computed(() => {
  return exercise.value?.exercise_type === 'multiple_choice'
})

const isCodeOrSqlType = computed(() => {
  return exercise.value?.exercise_type === 'code' || exercise.value?.language?.toLowerCase() === 'sql'
})

const hasChoiceAnswer = computed(() => {
  if (isMultipleChoice.value) return selectedChoices.value.length > 0
  return !!userAnswer.value
})

const hasNextExercise = computed(() => !!nextExerciseId.value)

const totalCount = computed(() => 1 + relatedExercises.value.length)

const currentIndex = ref(0)

const formattedTime = computed(() => {
  const mins = Math.floor(elapsedSeconds.value / 60)
  const secs = elapsedSeconds.value % 60
  return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`
})

const toggleChoice = (key) => {
  const index = selectedChoices.value.indexOf(key)
  if (index > -1) {
    selectedChoices.value.splice(index, 1)
  } else {
    selectedChoices.value.push(key)
  }
}

const isChoiceSelected = (key) => {
  if (isMultipleChoice.value) {
    return selectedChoices.value.includes(key)
  }
  return userAnswer.value === key
}

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

watch(submitResult, (newVal) => {
  if (newVal && isCodeOrSqlType.value) {
    leftTab.value = 'result'
  }
})

onMounted(() => {
  fetchExerciseDetail()
  fetchRelatedExercises()
  fetchNotes()
  timerInterval.value = setInterval(() => {
    elapsedSeconds.value++
  }, 1000)
  document.addEventListener('keydown', handleKeydown)
})

onBeforeUnmount(() => {
  if (timerInterval.value) clearInterval(timerInterval.value)
  document.removeEventListener('keydown', handleKeydown)
})

const handleKeydown = (e) => {
  if (e.ctrlKey && e.key === 'Enter') {
    e.preventDefault()
    submitAnswer()
  }
  if (e.ctrlKey && e.shiftKey && (e.key === 'r' || e.key === 'R')) {
    e.preventDefault()
    if (exercise.value?.language?.toLowerCase() === 'sql') {
      runSql()
    }
  }
}

const startResize = (e) => {
  e.preventDefault()
  const container = document.querySelector('.oj-split-layout')
  if (!container) return

  const onMouseMove = (ev) => {
    const containerRect = container.getBoundingClientRect()
    const newWidth = ev.clientX - containerRect.left
    const minWidth = 320
    const maxWidth = containerRect.width - 360
    leftPanelWidth.value = Math.max(minWidth, Math.min(maxWidth, newWidth))
    hasResized.value = true
  }

  const onMouseUp = () => {
    document.removeEventListener('mousemove', onMouseMove)
    document.removeEventListener('mouseup', onMouseUp)
    document.body.style.cursor = ''
    document.body.style.userSelect = ''
  }

  document.body.style.cursor = 'col-resize'
  document.body.style.userSelect = 'none'
  document.addEventListener('mousemove', onMouseMove)
  document.addEventListener('mouseup', onMouseUp)
}

const viewSolution = () => {
  showSolution.value = true
  leftTab.value = 'solution'
}

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
    console.log('[ExerciseDetail] API response:', res)
    exercise.value = res
    if (!res || !res.id) {
      console.warn('[ExerciseDetail] Invalid response data:', res)
      ElMessage.warning('习题数据异常')
    }
  } catch (error) {
    console.error('获取习题详情失败:', error?.response?.status, error?.response?.data || error.message)
    ElMessage.error(`获取习题详情失败: ${error?.response?.data?.detail || error.message}`)
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
  if (exercise.value?.exercise_type === 'multiple_choice') {
    answerContent = selectedChoices.value.sort().join(',')
  }
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
      setup_sql: exercise.value.setup_sql || '',
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

const prevExercise = () => {
  router.back()
}

const showHintDialog = () => {
  if (!exercise.value?.hint) return
  ElMessageBox.alert(
    `<div style="color: #a5b4fc; font-size: 15px; line-height: 1.8; white-space: pre-wrap;">${exercise.value.hint}</div>`,
    '💡 提示',
    {
      dangerouslyUseHTMLString: true,
      confirmButtonText: '知道了',
      customClass: 'hint-dialog',
      center: true,
    }
  )
}
</script>

<style scoped>
.oj-page {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--tm-bg-page);
  color: var(--tm-text-primary);
  overflow: hidden;
}

.oj-loading,
.oj-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100vh;
  gap: 16px;
  color: var(--tm-text-secondary);
}

.loading-spinner {
  width: 36px;
  height: 36px;
  border: 3px solid var(--tm-border-light);
  border-top-color: var(--tm-color-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.oj-topbar {
  height: 48px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  background: var(--tm-card-bg);
  border-bottom: 1px solid var(--tm-border-light);
  z-index: 10;
}

.topbar-left,
.topbar-center,
.topbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.topbar-left {
  flex-shrink: 0;
}

.topbar-center {
  flex: 1;
  justify-content: center;
  overflow: hidden;
}

.topbar-right {
  flex-shrink: 0;
}

.topbar-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--tm-text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 400px;
}

.topbar-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: 1px solid var(--tm-border-light);
  border-radius: 6px;
  color: var(--tm-text-regular);
  cursor: pointer;
  transition: all 0.2s;
  font-size: 16px;
}

.topbar-btn:hover:not(:disabled) {
  border-color: var(--tm-color-primary);
  color: var(--tm-color-primary);
  background: rgba(var(--tm-color-primary-rgb), 0.08);
}

.topbar-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.back-btn {
  width: auto;
  padding: 0 10px;
  font-size: 13px;
  gap: 4px;
}

.nav-arrow {
  font-size: 20px;
  font-weight: 700;
  line-height: 1;
}

.progress-indicator {
  padding: 0 8px;
}

.progress-text {
  font-size: 13px;
  color: var(--tm-text-secondary);
}

.progress-text strong {
  color: var(--tm-color-primary);
  font-size: 15px;
}

.timer-display {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 12px;
  background: rgba(var(--tm-color-primary-rgb), 0.08);
  border: 1px solid rgba(var(--tm-color-primary-rgb), 0.15);
  border-radius: 6px;
  font-variant-numeric: tabular-nums;
}

.timer-icon {
  font-size: 14px;
}

.timer-text {
  font-size: 14px;
  font-weight: 600;
  color: var(--tm-color-primary);
  letter-spacing: 0.5px;
}

.timer-warning .timer-text {
  color: #f87171;
  animation: timerPulse 1s ease-in-out infinite;
}

@keyframes timerPulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.tag-badge {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 500;
  white-space: nowrap;
}

.tag-badge.type { background: rgba(99, 102, 241, 0.15); color: #a5b4fc; }
.tag-badge.stage { background: rgba(52, 211, 153, 0.12); color: #6ee7b7; }
.tag-badge.level { background: rgba(251, 191, 36, 0.12); color: #fcd34d; }
.tag-badge.level-easy, .tag-badge.level-beginner { background: rgba(52, 211, 153, 0.12); color: #34d399; }
.tag-badge.level-medium, .tag-badge.level-intermediate { background: rgba(251, 191, 36, 0.12); color: #fbbf24; }
.tag-badge.level-hard, .tag-badge.level-advanced { background: rgba(248, 113, 113, 0.12); color: #f87171; }
.tag-badge.subject { background: rgba(var(--tm-color-primary-rgb), 0.12); color: var(--tm-color-primary); }

.oj-split-layout {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.oj-left-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-width: 320px;
  background: var(--tm-card-bg);
}

.left-panel-tabs {
  display: flex;
  align-items: center;
  gap: 0;
  padding: 0 12px;
  border-bottom: 1px solid var(--tm-border-light);
  flex-shrink: 0;
  overflow-x: auto;
}

.left-tab {
  padding: 10px 14px;
  font-size: 13px;
  font-weight: 500;
  color: var(--tm-text-secondary);
  background: transparent;
  border: none;
  border-bottom: 2px solid transparent;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
  position: relative;
  display: flex;
  align-items: center;
  gap: 6px;
}

.left-tab:hover {
  color: var(--tm-text-primary);
}

.left-tab.active {
  color: var(--tm-color-primary);
  border-bottom-color: var(--tm-color-primary);
}

.tab-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  display: inline-block;
}

.dot-green { background: #34d399; }
.dot-red { background: #f87171; }

.left-panel-body {
  flex: 1;
  overflow-y: auto;
  padding: 0;
}

.tab-content {
  padding: 20px 24px;
}

.problem-title {
  font-size: 22px;
  font-weight: 700;
  color: var(--tm-text-primary);
  margin: 0 0 12px;
  line-height: 1.4;
}

.problem-meta {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
  font-size: 13px;
  color: var(--tm-text-secondary);
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--tm-border-light);
}

.problem-section {
  margin-bottom: 20px;
}

.section-label {
  font-size: 14px;
  font-weight: 700;
  color: var(--tm-text-primary);
  margin: 0 0 10px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.section-body {
  font-size: 14px;
  color: var(--tm-text-regular);
  line-height: 1.8;
}

.desc-body p {
  margin: 0;
}

.instructions-pre {
  margin: 0;
  color: var(--tm-text-regular);
  font-family: 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.8;
  white-space: pre-wrap;
  background: rgba(var(--tm-bg-page-rgb), 0.5);
  padding: 12px 16px;
  border-radius: 6px;
}

.hint-inline-btn {
  padding: 6px 14px;
  background: rgba(251, 191, 36, 0.1);
  border: 1px solid rgba(251, 191, 36, 0.2);
  border-radius: 6px;
  color: #fbbf24;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.hint-inline-btn:hover {
  background: rgba(251, 191, 36, 0.18);
  border-color: rgba(251, 191, 36, 0.35);
}

.oj-divider {
  width: 5px;
  flex-shrink: 0;
  cursor: col-resize;
  background: var(--tm-border-light);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s;
  position: relative;
}

.oj-divider:hover {
  background: rgba(var(--tm-color-primary-rgb), 0.3);
}

.divider-line {
  width: 2px;
  height: 32px;
  border-radius: 1px;
  background: rgba(255, 255, 255, 0.1);
}

.oj-divider:hover .divider-line {
  background: var(--tm-color-primary);
}

.oj-right-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-width: 360px;
  background: var(--tm-bg-page);
}

.editor-wrapper {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.editor-wrapper :deep(.code-editor-container) {
  flex: 1;
  display: flex;
  flex-direction: column;
  height: 100%;
  border: none;
  border-radius: 0;
}

.editor-wrapper :deep(.cm-editor) {
  flex: 1;
  min-height: 0;
}

.editor-wrapper :deep(.code-editor) {
  flex: 1;
  min-height: 0;
}

.editor-wrapper :deep(.output-container) {
  flex-shrink: 0;
  max-height: 180px;
}

.editor-action-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  background: var(--tm-card-bg);
  border-top: 1px solid var(--tm-border-light);
  flex-shrink: 0;
}

.action-bar-left,
.action-bar-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.btn-hint-sm {
  padding: 5px 12px;
  background: rgba(251, 191, 36, 0.1);
  border: 1px solid rgba(251, 191, 36, 0.2);
  border-radius: 5px;
  color: #fbbf24;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-hint-sm:hover {
  background: rgba(251, 191, 36, 0.18);
}

.btn-outline-sm {
  padding: 5px 12px;
  background: transparent;
  border: 1px solid var(--tm-border-light);
  border-radius: 5px;
  color: var(--tm-text-secondary);
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-outline-sm:hover {
  border-color: var(--tm-color-primary);
  color: var(--tm-color-primary);
}

.btn-run-sm {
  padding: 5px 14px;
  background: rgba(59, 130, 246, 0.12);
  border: 1px solid rgba(59, 130, 246, 0.25);
  border-radius: 5px;
  color: #60a5fa;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-run-sm:hover:not(:disabled) {
  background: rgba(59, 130, 246, 0.2);
}

.btn-run-sm:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-submit-sm {
  padding: 5px 16px;
  background: linear-gradient(135deg, #34d399, #059669);
  border: none;
  border-radius: 5px;
  color: #fff;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 2px 8px rgba(52, 211, 153, 0.25);
}

.btn-submit-sm:hover:not(:disabled) {
  box-shadow: 0 4px 14px rgba(52, 211, 153, 0.4);
  transform: translateY(-1px);
}

.btn-submit-sm:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

.shortcut-hint-bar {
  padding: 4px 12px;
  font-size: 11px;
  color: var(--tm-text-secondary);
  background: rgba(var(--tm-bg-page-rgb), 0.5);
  border-top: 1px solid var(--tm-border-light);
  flex-shrink: 0;
  opacity: 0.7;
}

.output-panel {
  flex-shrink: 0;
  max-height: 220px;
  overflow-y: auto;
  border-top: 1px solid var(--tm-border-light);
  background: var(--tm-card-bg);
}

.output-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: rgba(255, 255, 255, 0.02);
  border-bottom: 1px solid var(--tm-border-light);
  font-size: 13px;
  color: var(--tm-text-regular);
  font-weight: 600;
}

.sql-result-tag {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
}

.sql-result-tag.success { background: rgba(52, 211, 153, 0.15); color: #34d399; }
.sql-result-tag.fail { background: rgba(248, 113, 113, 0.15); color: #f87171; }

.sql-result-error {
  padding: 10px 12px;
  background: rgba(248, 113, 113, 0.06);
  color: #f87171;
  font-family: monospace;
  font-size: 12px;
  white-space: pre-wrap;
}

.sql-result-table-wrap { padding: 8px; }

.sql-result-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
}

.sql-result-table th, .sql-result-table td {
  border: 1px solid var(--tm-border-light);
  padding: 6px 10px;
  text-align: left;
  color: var(--tm-text-regular);
}

.sql-result-table th {
  background: rgba(255, 255, 255, 0.03);
  font-weight: 600;
  color: var(--tm-text-primary);
}

.sql-result-count {
  text-align: right;
  padding: 6px 10px;
  font-size: 11px;
  color: var(--tm-text-secondary);
}

.sql-result-msg {
  padding: 10px 12px;
  background: rgba(52, 211, 153, 0.06);
  color: #34d399;
  font-size: 13px;
}

.judge-quick-view .output-header {
  padding: 8px 12px;
}

.judge-quick-tag {
  padding: 2px 10px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 700;
}

.judge-quick-tag.pass { background: rgba(52, 211, 153, 0.15); color: #34d399; }
.judge-quick-tag.fail { background: rgba(248, 113, 113, 0.15); color: #f87171; }

.judge-quick-body {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  font-size: 13px;
  color: var(--tm-text-regular);
}

.link-btn {
  background: none;
  border: none;
  color: var(--tm-color-primary);
  font-size: 13px;
  cursor: pointer;
  padding: 2px 6px;
  transition: opacity 0.2s;
}

.link-btn:hover {
  opacity: 0.8;
}

.judge-panel {
  padding: 20px;
  border-radius: 8px;
  border: 1px solid var(--tm-border-light);
}

.judge-panel.judge-pass { border-color: rgba(52, 211, 153, 0.25); background: rgba(52, 211, 153, 0.04); }
.judge-panel.judge-fail { border-color: rgba(248, 113, 113, 0.25); background: rgba(248, 113, 113, 0.04); }

.judge-status-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.judge-tag {
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 13px;
  font-weight: 700;
}

.judge-tag.success { background: rgba(52, 211, 153, 0.18); color: #34d399; }
.judge-tag.fail { background: rgba(248, 113, 113, 0.18); color: #f87171; }

.judge-msg { font-size: 14px; font-weight: 600; color: var(--tm-text-primary); }

.judge-stats-row {
  display: flex;
  gap: 20px;
  font-size: 13px;
  color: var(--tm-text-regular);
  margin-bottom: 12px;
}

.judge-case-list { display: flex; flex-direction: column; gap: 8px; margin-bottom: 12px; }

.judge-case-item {
  padding: 10px 14px;
  border-radius: 6px;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
}

.judge-case-item.case-ok { background: rgba(52, 211, 153, 0.06); border: 1px solid rgba(52, 211, 153, 0.12); }
.judge-case-item.case-ng { background: rgba(248, 113, 113, 0.06); border: 1px solid rgba(248, 113, 113, 0.12); }

.case-index { font-size: 13px; font-weight: 600; color: var(--tm-text-primary); min-width: 56px; }

.case-badge {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
}

.case-badge.success { background: rgba(52, 211, 153, 0.15); color: #34d399; }
.case-badge.fail { background: rgba(248, 113, 113, 0.15); color: #f87171; }

.case-fail-detail {
  width: 100%;
  margin-top: 4px;
  padding: 8px 10px;
  background: rgba(var(--tm-bg-page-rgb), 0.5);
  border-radius: 4px;
  font-size: 12px;
  color: var(--tm-text-regular);
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.case-fail-detail code {
  color: #f87171;
  font-family: 'Courier New', monospace;
  font-size: 11px;
  background: rgba(var(--tm-bg-page-rgb), 0.5);
  padding: 1px 4px;
  border-radius: 3px;
}

.code-warn { color: #fbbf24 !important; }

.judge-footer {
  font-size: 13px;
  color: var(--tm-text-regular);
  padding-top: 10px;
  border-top: 1px solid var(--tm-border-light);
}

.skill-panel {
  background: rgba(var(--tm-color-primary-rgb), 0.04);
  border: 1px solid rgba(var(--tm-color-primary-rgb), 0.12);
  border-radius: 8px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.skill-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.skill-name { font-size: 13px; font-weight: 600; color: var(--tm-text-primary); min-width: 72px; }
.skill-bar-wrap { flex: 1; }

.skill-bar-bg {
  height: 10px;
  border-radius: 5px;
  background: var(--tm-border-light);
  position: relative;
  overflow: hidden;
}

.skill-bar-before {
  position: absolute; top: 0; left: 0;
  height: 100%;
  background: rgba(var(--tm-color-primary-rgb), 0.2);
  border-radius: 5px;
  transition: width 0.5s ease;
}

.skill-bar-after {
  position: absolute; top: 0; left: 0;
  height: 100%;
  background: linear-gradient(90deg, var(--tm-color-primary), var(--tm-color-primary-dark));
  border-radius: 5px;
  transition: width 0.8s ease;
  animation: barAnim 0.8s ease-out;
}

@keyframes barAnim { from { width: 0 !important; } }

.skill-score { font-size: 12px; color: var(--tm-text-regular); min-width: 72px; text-align: center; font-variant-numeric: tabular-nums; }
.skill-gain { font-size: 14px; font-weight: 800; color: #34d399; min-width: 36px; text-align: right; }

.solution-card {
  border-left: 3px solid #34d399;
  padding: 16px 20px;
  background: rgba(52, 211, 153, 0.04);
  border-radius: 0 8px 8px 0;
}

.solution-text {
  margin: 0;
  font-family: 'Courier New', monospace;
  font-size: 14px;
  color: var(--tm-text-regular);
  line-height: 1.8;
  white-space: pre-wrap;
}

.notebook-container {
  width: 100%;
}

.note-list { margin-bottom: 14px; display: flex; flex-direction: column; gap: 8px; }

.note-entry {
  padding: 12px 14px;
  background: rgba(var(--tm-color-primary-rgb), 0.04);
  border: 1px solid rgba(var(--tm-color-primary-rgb), 0.08);
  border-radius: 8px;
}

.note-entry-header { display: flex; align-items: center; gap: 10px; margin-bottom: 4px; }
.note-entry-title { font-size: 13px; font-weight: 600; color: var(--tm-text-primary); }
.note-entry-time { font-size: 11px; color: var(--tm-text-secondary); }

.note-delete-btn {
  background: none;
  border: none;
  color: #f87171;
  font-size: 11px;
  cursor: pointer;
  margin-left: auto;
}

.note-entry-body { font-size: 12px; color: var(--tm-text-regular); line-height: 1.6; white-space: pre-wrap; }

.note-title-input, .note-content-textarea {
  width: 100%;
  box-sizing: border-box;
  background: rgba(var(--tm-bg-page-rgb), 0.5);
  border: 1px solid var(--tm-border-light);
  border-radius: 6px;
  color: var(--tm-text-regular);
  padding: 8px 12px;
  font-size: 13px;
  outline: none;
  margin-bottom: 8px;
}

.note-content-textarea { resize: vertical; font-family: inherit; min-height: 60px; }
.note-title-input:focus, .note-content-textarea:focus { border-color: rgba(var(--tm-color-primary-rgb), 0.4); }

.btn-save-note {
  padding: 6px 18px;
  background: linear-gradient(135deg, var(--tm-color-primary), var(--tm-color-primary-dark));
  border: none;
  border-radius: 6px;
  color: #fff;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-save-note:hover { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(var(--tm-color-primary-rgb), 0.3); }
.btn-save-note:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }

.recommend-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.recommend-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  background: rgba(var(--tm-bg-page-rgb), 0.3);
  border: 1px solid var(--tm-border-light);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.recommend-item:hover {
  border-color: rgba(var(--tm-color-primary-rgb), 0.25);
  background: rgba(var(--tm-color-primary-rgb), 0.04);
}

.recommend-item.rec-done {
  border-left: 3px solid #34d399;
  opacity: 0.7;
}

.rec-status { font-size: 14px; flex-shrink: 0; }

.rec-info { flex: 1; min-width: 0; }

.rec-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--tm-text-primary);
  margin: 0 0 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.rec-meta { display: flex; align-items: center; gap: 8px; }

.rec-badge-diff {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 10px;
  font-weight: 600;
}

.rec-badge-diff.diff-easy, .rec-badge-diff.diff-beginner { background: rgba(52, 211, 153, 0.12); color: #34d399; }
.rec-badge-diff.diff-medium, .rec-badge-diff.diff-intermediate { background: rgba(251, 191, 36, 0.12); color: #fbbf24; }
.rec-badge-diff.diff-hard, .rec-badge-diff.diff-advanced { background: rgba(248, 113, 113, 0.12); color: #f87171; }

.rec-subject { font-size: 11px; color: var(--tm-text-secondary); }

.rec-arrow {
  font-size: 18px;
  color: var(--tm-text-secondary);
  flex-shrink: 0;
}

.oj-choice-layout,
.oj-text-layout {
  flex: 1;
  overflow-y: auto;
}

.choice-scroll,
.text-scroll {
  max-width: 800px;
  margin: 0 auto;
  padding: 32px 24px;
}

.choice-question-card,
.text-question-card {
  background: var(--tm-card-bg);
  border: 1px solid var(--tm-border-light);
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 24px;
}

.choice-tags,
.text-tags {
  display: flex;
  gap: 8px;
  margin-bottom: 14px;
  flex-wrap: wrap;
}

.choice-title,
.text-title {
  font-size: 22px;
  font-weight: 700;
  color: var(--tm-text-primary);
  margin: 0 0 14px;
  line-height: 1.4;
}

.choice-desc,
.text-desc {
  font-size: 15px;
  color: var(--tm-text-regular);
  line-height: 1.8;
  margin-bottom: 12px;
}

.choice-desc p,
.text-desc p {
  margin: 0;
}

.text-instructions {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid var(--tm-border-light);
}

.choice-options {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 24px;
}

.choice-option-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 18px 20px;
  background: var(--tm-card-bg);
  border: 2px solid var(--tm-border-light);
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.25s ease;
  position: relative;
}

.choice-option-card:hover:not(.disabled) {
  border-color: rgba(var(--tm-color-primary-rgb), 0.35);
  background: rgba(var(--tm-color-primary-rgb), 0.04);
}

.choice-option-card.selected {
  border-color: var(--tm-color-primary);
  background: rgba(var(--tm-color-primary-rgb), 0.08);
  box-shadow: 0 0 0 1px rgba(var(--tm-color-primary-rgb), 0.15);
}

.choice-option-card.correct-answer {
  border-color: #34d399 !important;
  background: rgba(52, 211, 153, 0.08) !important;
}

.choice-option-card.wrong-answer {
  border-color: #f87171 !important;
  background: rgba(248, 113, 113, 0.08) !important;
}

.choice-option-card.my-correct {
  border-color: #34d399 !important;
  background: rgba(52, 211, 153, 0.08) !important;
}

.choice-option-card.disabled {
  cursor: default;
}

.option-label {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 700;
  flex-shrink: 0;
  background: rgba(var(--tm-color-primary-rgb), 0.1);
  color: var(--tm-color-primary);
  transition: all 0.25s;
}

.choice-option-card.selected .option-label {
  background: var(--tm-color-primary);
  color: #fff;
}

.choice-option-card.correct-answer .option-label {
  background: #34d399 !important;
  color: #fff !important;
}

.choice-option-card.wrong-answer .option-label {
  background: #f87171 !important;
  color: #fff !important;
}

.option-text {
  flex: 1;
  font-size: 15px;
  color: var(--tm-text-regular);
  line-height: 1.6;
}

.option-check {
  font-size: 16px;
  font-weight: 700;
  flex-shrink: 0;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
}

.choice-option-card.selected .option-check {
  color: var(--tm-color-primary);
}

.choice-option-card.correct-answer .option-check {
  color: #34d399;
}

.choice-option-card.wrong-answer .option-check {
  color: #f87171;
}

.choice-actions,
.text-actions {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 24px;
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

.btn-hint {
  padding: 10px 24px;
  background: linear-gradient(135deg, #fbbf24, #f59e0b);
  border: none;
  border-radius: 8px;
  color: #1a1a2e;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  box-shadow: 0 2px 14px rgba(251, 191, 36, 0.3);
  transition: all 0.3s ease;
}

.btn-hint:hover { transform: translateY(-2px); box-shadow: 0 6px 24px rgba(251, 191, 36, 0.45); }

.choice-result {
  padding: 20px;
  border-radius: 10px;
  margin-bottom: 24px;
  animation: resultSlideIn 0.3s ease-out;
}

@keyframes resultSlideIn {
  from { opacity: 0; transform: translateY(-8px); }
  to { opacity: 1; transform: translateY(0); }
}

.choice-result.result-pass {
  background: rgba(52, 211, 153, 0.06);
  border: 1px solid rgba(52, 211, 153, 0.2);
}

.choice-result.result-fail {
  background: rgba(248, 113, 113, 0.06);
  border: 1px solid rgba(248, 113, 113, 0.2);
}

.result-status {
  display: flex;
  align-items: center;
  gap: 10px;
}

.result-icon { font-size: 22px; }

.result-text {
  font-size: 18px;
  font-weight: 700;
}

.result-pass .result-text { color: #34d399; }
.result-fail .result-text { color: #f87171; }

.result-msg {
  font-size: 14px;
  color: var(--tm-text-regular);
}

.correct-answer-hint {
  margin-top: 10px;
  padding: 10px 14px;
  background: rgba(52, 211, 153, 0.08);
  border-radius: 6px;
  font-size: 14px;
  color: var(--tm-text-regular);
}

.correct-answer-hint strong {
  color: #34d399;
  font-size: 16px;
}

.choice-skill,
.choice-solution,
.choice-notes,
.choice-related,
.text-result,
.text-skill,
.text-solution,
.text-notes {
  margin-bottom: 24px;
}

.text-answer-area {
  margin-bottom: 20px;
}

.answer-textarea {
  width: 100%;
  box-sizing: border-box;
  background: var(--tm-card-bg);
  border: 1px solid var(--tm-border-light);
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

.recommend-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.recommend-card {
  padding: 16px;
  background: var(--tm-card-bg);
  border: 1px solid var(--tm-border-light);
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.recommend-card:hover {
  transform: translateY(-2px);
  border-color: rgba(var(--tm-color-primary-rgb), 0.25);
  box-shadow: 0 4px 16px rgba(var(--tm-color-primary-rgb), 0.1);
}

.recommend-card.rec-done {
  border-left: 3px solid #34d399;
  opacity: 0.7;
}

.rec-status-icon { font-size: 13px; margin-right: 4px; }

.rec-card-title {
  font-size: 14px;
  font-weight: 700;
  color: var(--tm-text-primary);
  margin: 6px 0 8px;
  line-height: 1.4;
}

.rec-card-meta { display: flex; align-items: center; gap: 8px; }

.rec-subject-text { font-size: 11px; color: var(--tm-text-secondary); }

@media (max-width: 1000px) {
  .recommend-grid { grid-template-columns: repeat(2, 1fr); }
}

@media (max-width: 768px) {
  .oj-split-layout {
    flex-direction: column;
  }

  .oj-left-panel {
    min-width: unset;
    max-height: 45vh;
    flex: none !important;
    width: 100% !important;
  }

  .oj-divider {
    width: 100%;
    height: 5px;
    cursor: row-resize;
  }

  .divider-line {
    width: 32px;
    height: 2px;
  }

  .oj-right-panel {
    min-width: unset;
    flex: 1;
  }

  .topbar-center {
    display: none;
  }

  .choice-scroll,
  .text-scroll {
    padding: 20px 16px;
  }

  .recommend-grid { grid-template-columns: 1fr; }
}
</style>
