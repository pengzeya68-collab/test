<template>
  <div class="code-playground">
    <!-- 椤甸潰澶撮儴 -->
    <div class="page-header">
      <div class="header-left">
        <div class="header-icon">
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="16 18 22 12 16 6"></polyline>
            <polyline points="8 6 2 12 8 18"></polyline>
          </svg>
        </div>
        <div>
          <h1 class="page-title">鍦ㄧ嚎浠ｇ爜缁冧範瀹</h1>
          <p class="page-subtitle">鍦ㄧ嚎缂栧啓銆佽繍琛屻€佽皟璇曚唬鐮侊紝鏀寔 Python / SQL / Shell</p>
        </div>
      </div>
      <div class="header-stats">
        <div class="stat-chip">
          <span class="stat-num">{{ exercises.length }}</span>
          <span class="stat-label">閬撲範棰</span>
        </div>
        <div class="stat-chip">
          <span class="stat-num">{{ filteredExercises.length }}</span>
          <span class="stat-label">褰撳墠绛涢€</span>
        </div>
        <LayoutPresetDropdown size="small" @change="applyLayoutPreset" />
      </div>
    </div>

    <div class="playground-container">
      <!-- 宸︿晶棰樼洰鍒楄〃 -->
      <div class="left-panel" :style="{ width: leftPanelWidth + 'px', flex: 'none' }">
        <!-- 璇█绛涢€夋爣绛?-->
        <div class="filter-tabs">
          <button
            class="filter-tab"
            :class="{ active: currentLanguageFilter === '' }"
            @click="currentLanguageFilter = ''"
          >
            <span class="tab-icon">&#x1f4cb;</span> 鍏ㄩ儴
          </button>
          <button
            class="filter-tab"
            :class="{ active: currentLanguageFilter === 'Python' }"
            @click="currentLanguageFilter = currentLanguageFilter === 'Python' ? '' : 'Python'"
          >
            <span class="tab-icon">&#x1f40d;</span> Python
          </button>
          <button
            class="filter-tab"
            :class="{ active: currentLanguageFilter === 'SQL' }"
            @click="currentLanguageFilter = currentLanguageFilter === 'SQL' ? '' : 'SQL'"
          >
            <span class="tab-icon">&#x1f4be;</span> SQL
          </button>
          <button
            class="filter-tab"
            :class="{ active: currentLanguageFilter === 'Shell' }"
            @click="currentLanguageFilter = currentLanguageFilter === 'Shell' ? '' : 'Shell'"
          >
            <span class="tab-icon">&#x1f4bb;</span> Shell
          </button>
        </div>

        <!-- 涔犻鍒楄〃 -->
        <div class="exercise-list">
          <div
            class="exercise-item"
            v-for="exercise in filteredExercises"
            :key="exercise.id"
            :class="{ active: selectedExercise?.id === exercise.id }"
            @click="selectExercise(exercise)"
          >
            <div class="exercise-item-top">
              <span class="exercise-lang-badge" :class="'lang-' + getEffectiveLanguage(exercise)">
                {{ getDisplayLanguage(exercise) }}
              </span>
              <span class="exercise-difficulty" :class="'diff-' + exercise.difficulty">
                {{ getDifficultyText(exercise.difficulty) }}
              </span>
            </div>
            <div class="exercise-title">{{ exercise.title }}</div>
            <div class="exercise-item-bottom">
              <span class="exercise-kp">{{ exercise.knowledge_point }}</span>
              <span class="exercise-time">{{ exercise.time_estimate }}min</span>
            </div>
          </div>
        </div>

        <!-- 绌虹姸鎬?-->
        <div class="empty-state" v-if="filteredExercises.length === 0 && !loading">
          <div class="empty-icon">&#x1f50d;</div>
          <p>鏆傛棤{{ currentLanguageFilter ? getDisplayLanguage({language: currentLanguageFilter, exercise_type: ''}) : '' }}涔犻</p>
          <button class="empty-reset-btn" @click="currentLanguageFilter = ''">鏌ョ湅鍏ㄩ儴涔犻</button>
        </div>
      </div>

      <!-- 鎷栨嫿鍒嗛殧鏉★細棰樼洰鍒楄〃 鈫?缂栫▼鍖哄煙 -->
      <BaseSplitter
        v-model:size="leftPanelWidth"
        direction="horizontal"
        :min-size="220"
        :max-size="560"
        storage-key="tm-codeplayground-sidebar-width"
        container-selector=".playground-container"
      />

      <!-- 鍙充晶缂栫▼鍖哄煙 -->
      <div class="right-panel">
        <!-- 鏈€夋嫨涔犻 -->
        <div class="welcome-state" v-if="!selectedExercise">
          <div class="welcome-icon">
            <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
              <polyline points="16 18 22 12 16 6"></polyline>
              <polyline points="8 6 2 12 8 18"></polyline>
            </svg>
          </div>
          <h2>閫夋嫨涓€閬撲範棰樺紑濮嬬粌涔</h2>
          <p>浠庡乏渚у垪琛ㄤ腑閫夋嫨涔犻锛屽湪绾跨紪鍐欎唬鐮佸苟杩愯</p>
          <div class="welcome-features">
            <div class="feature-item">
              <span class="feature-icon">&#x26a1;</span>
              <span>鍗虫椂杩愯</span>
            </div>
            <div class="feature-item">
              <span class="feature-icon">&#x1f916;</span>
              <span>AI鐐硅瘎</span>
            </div>
            <div class="feature-item">
              <span class="feature-icon">&#x1f6e1;&#xfe0f;</span>
              <span>瀹夊叏娌欑</span>
            </div>
          </div>
        </div>

        <!-- 棰樼洰鎻忚堪 -->
        <div class="problem-section" v-if="selectedExercise">
          <div class="problem-header">
            <div class="problem-title-row">
              <h2>{{ selectedExercise.title }}</h2>
              <span class="problem-lang-badge" :class="'lang-' + getEffectiveLanguage(selectedExercise)">
                {{ getDisplayLanguage(selectedExercise) }}
              </span>
            </div>
            <div class="problem-tags">
              <span class="problem-tag diff-tag" :class="'diff-' + selectedExercise.difficulty">
                {{ getDifficultyText(selectedExercise.difficulty) }}
              </span>
              <span class="problem-tag" v-if="selectedExercise.knowledge_point">
                {{ selectedExercise.knowledge_point }}
              </span>
              <span class="problem-tag time-tag" v-if="selectedExercise.time_estimate">
                {{ selectedExercise.time_estimate }} 鍒嗛挓
              </span>
            </div>
          </div>
          <div class="problem-body">
            <div class="problem-description" v-html="renderDescription(selectedExercise.description)"></div>
            <div class="problem-instructions" v-if="selectedExercise.instructions">
              <div class="section-label">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line></svg>
                瑕佹眰
              </div>
              <pre>{{ selectedExercise.instructions }}</pre>
            </div>
            <div class="problem-testcases" v-if="selectedExercise.test_cases">
              <div class="section-label">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 11l3 3L22 4"></path><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"></path></svg>
                娴嬭瘯鐢ㄤ緥
              </div>
              <pre>{{ selectedExercise.test_cases }}</pre>
            </div>
          </div>
        </div>

        <!-- 浠ｇ爜缂栬緫鍣?-->
        <div class="editor-section" v-if="selectedExercise">
          <CodeEditor
            v-model="userCode"
            :language="currentLanguage"
            :submitting="submitLoading"
            :aiEvaluating="aiLoading"
            ref="editorRef"
            @run="handleCodeRun"
            @submit="submitCode"
            @aiEvaluate="getAIEvaluation"
          />
        </div>

        <!-- 鎵ц缁撴灉 -->
        <div class="result-section" v-if="submitResult">
          <div class="result-card" :class="submitResult.success ? 'result-success' : 'result-error'">
            <div class="result-header">
              <div class="result-status">
                <span class="status-dot" :class="submitResult.success ? 'dot-success' : 'dot-error'"></span>
                <span class="status-text">{{ submitResult.success ? '鎵ц鎴愬姛' : '鎵ц澶辫触' }}</span>
              </div>
              <span class="result-time" v-if="submitResult.execution_time_ms">
                鈴?{{ submitResult.execution_time_ms }}ms
              </span>
            </div>
            <div class="result-body">
              <!-- 鏃犺緭鍑烘椂鏄剧ず鎻愮ず -->
              <div v-if="!submitResult.stdout && !submitResult.stderr" class="result-block no-output-block">
                <div class="result-label">杈撳嚭</div>
                <div class="no-output-msg">
                  <span class="no-output-icon">鉁</span>
                  浠ｇ爜鎵ц鎴愬姛锛屾棤杈撳嚭鍐呭
                  <div class="no-output-hint">馃挕 鎻愮ず锛氬嚱鏁板畾涔変笉浼氳嚜鍔ㄨ緭鍑猴紝璇峰湪浠ｇ爜涓坊鍔?<code>print()</code> 璋冪敤鎴栫偣鍑?鎻愪氦鍒ら"楠岃瘉姝ｇ‘鎬</div>
                </div>
              </div>
              <!-- 鏈夎緭鍑烘椂姝ｅ父鏄剧ず -->
              <div v-if="submitResult.stdout" class="result-block">
                <div class="result-label">杈撳嚭</div>
                <pre class="result-output">{{ submitResult.stdout }}</pre>
              </div>
              <!-- 鏈夐敊璇椂鏄剧ず -->
              <div v-if="submitResult.stderr" class="result-block">
                <div class="result-label error-label">閿欒</div>
                <pre class="result-output error-output">{{ submitResult.stderr }}</pre>
              </div>
            </div>
            <!-- 鎿嶄綔鎸夐挳 -->
            <div class="result-actions">
              <button class="submit-btn" @click="submitCode" :disabled="submitLoading">
                <span v-if="submitLoading" class="submit-btn-running"></span>
                <span v-else>&#x1f4dd;</span>
                {{ submitLoading ? '鎻愪氦鍒ら涓?..' : '鎻愪氦鍒ら' }}
              </button>
              <button class="ai-btn" @click="getAIEvaluation" :disabled="aiLoading || !submitResult.success">
                <span v-if="aiLoading" class="ai-btn-loading"></span>
                <span v-else>&#x1f916;</span>
                {{ aiLoading ? 'AI璇勪及涓?..' : '鑾峰彇AI鐐硅瘎' }}
              </button>
            </div>
          </div>
        </div>

        <!-- 鍒ら缁撴灉 -->
        <div class="result-section" v-if="submissionResult">
          <div class="submit-card" :class="submissionResult.judge_result?.all_passed ? 'result-success' : 'result-error'">
            <div class="submit-header">
              <div class="submit-status">
                <span class="submit-dot" :class="submissionResult.judge_result?.all_passed ? 'dot-success' : 'dot-error'"></span>
                <span class="submit-text">
                  {{ submissionResult.judge_result?.all_passed ? '鍏ㄩ儴閫氳繃' : submissionResult.judge_result?.summary || '閮ㄥ垎閫氳繃' }}
                </span>
              </div>
              <span class="submit-time">
                {{ submissionResult.judge_result?.passed_count || 0 }}/{{ submissionResult.judge_result?.total_cases || 0 }} 閫氳繃
              </span>
            </div>
            <div class="submit-body">
              <!-- 娴嬭瘯鐢ㄤ緥鍒楄〃 -->
              <div v-if="submissionResult.judge_result?.details?.length" class="submit-result-block">
                <div class="testcase-list">
                  <div
                    v-for="tc in submissionResult.judge_result.details"
                    :key="tc.case_index"
                    class="testcase-item"
                    :class="tc.passed ? 'tc-pass' : 'tc-fail'"
                  >
                    <span class="testcase-icon">{{ tc.passed ? '通过' : '失败' }}</span>
                    <span class="testcase-label">娴嬭瘯鐢ㄤ緥 #{{ tc.case_index }}</span>
                    <span class="testcase-detail">{{ tc.passed ? '閫氳繃' : '澶辫触' }}</span>
                  </div>
                </div>
              </div>
              <!-- 閫氳繃鐜囪繘搴︽潯 -->
              <div v-if="submissionResult.judge_result?.total_cases > 1" class="submit-result-block">
                <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
                  <span style="font-size: 12px; color: var(--tm-text-secondary);">閫氳繃鐜</span>
                  <span style="font-size: 12px; color: var(--tm-text-primary); font-weight: 600;">{{ (submissionResult.judge_result.pass_rate || 0).toFixed(0) }}%</span>
                </div>
                <div class="score-bar-track">
                  <div
                    class="score-bar-fill"
                    :style="{ width: (submissionResult.judge_result.pass_rate || 0) + '%' }"
                    :class="getScoreClass(submissionResult.judge_result.pass_rate || 0)"
                  ></div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- AI璇勪及缁撴灉 -->
        <div class="result-section" v-if="aiEvaluationResult">
          <div class="ai-result-card">
            <div class="ai-result-header">
              <span class="ai-avatar">&#x1f916;</span>
              <span class="ai-title">AI瀵煎笀鐐硅瘎</span>
              <div class="ai-score-badge" :class="getScoreClass(aiEvaluationResult.score)">
                {{ aiEvaluationResult.score }}鍒?              </div>
            </div>
            <div class="ai-score-bar">
              <div class="score-bar-track">
                <div
                  class="score-bar-fill"
                  :style="{ width: aiEvaluationResult.score + '%' }"
                  :class="getScoreClass(aiEvaluationResult.score)"
                ></div>
              </div>
            </div>
            <div class="ai-feedback-text" v-if="aiEvaluationResult.feedback">
              {{ aiEvaluationResult.feedback }}
            </div>
            <div class="ai-optimized" v-if="aiEvaluationResult.optimized_code">
              <div class="section-label">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 20h9"></path><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"></path></svg>
                浼樺寲寤鸿
              </div>
              <pre>{{ aiEvaluationResult.optimized_code }}</pre>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import CodeEditor from '@/components/CodeEditor.vue'
import BaseSplitter from '@/components/base/BaseSplitter.vue'
import LayoutPresetDropdown from '@/components/LayoutPresetDropdown.vue'
import request from '@/utils/request'

// 宸︿晶棰樼洰鍒楄〃瀹藉害锛堝甫 localStorage 鎸佷箙鍖栵級
const leftPanelWidth = ref(320)

// 布局预设：调整左侧题目列表宽度
const applyLayoutPreset = (preset) => {
  const presets = {
    compact: 260,
    default: 320,
    wide: 480,
    'editor-focus': 220,
    reset: 320
  }
  const width = presets[preset] ?? 320
  leftPanelWidth.value = Math.max(220, Math.min(560, width))
  try { localStorage.setItem('tm-codeplayground-sidebar-width', String(leftPanelWidth.value)) } catch {}
  ElMessage?.success?.(`甯冨眬宸插垏鎹細棰樼洰鍒楄〃 ${leftPanelWidth.value}px`)
}

const exercises = ref([])
const loading = ref(false)
const selectedExercise = ref(null)
const userCode = ref('')
const currentLanguageFilter = ref('')
const submitResult = ref(null)
const submitLoading = ref(false)
const submissionResult = ref(null)
const editorRef = ref(null)
const aiEvaluationResult = ref(null)
const aiLoading = ref(false)

const getEffectiveLanguage = (exercise) => {
  if (!exercise) return 'python'
  const lang = exercise.language?.toLowerCase() || ''
  if (['python', 'sql', 'shell', 'javascript'].includes(lang)) return lang
  if (exercise.exercise_type === 'sql') return 'sql'
  if (exercise.exercise_type === 'code') return 'python'
  const cat = (exercise.category || '').toLowerCase()
  const kp = (exercise.knowledge_point || '').toLowerCase()
  if (cat.includes('database') || cat.includes('sql') || kp.includes('sql')) return 'sql'
  if (cat.includes('linux') || cat.includes('shell') || kp.includes('shell') || kp.includes('鍛戒护')) return 'shell'
  if (cat.includes('programming') || cat.includes('python') || kp.includes('python')) return 'python'
  return 'python'
}

const getDisplayLanguage = (exercise) => {
  const lang = exercise.language || ''
  if (lang === '涓枃') {
    const effective = getEffectiveLanguage(exercise)
    const map = { python: 'Python', sql: 'SQL', shell: 'Shell' }
    return map[effective] || 'Python'
  }
  return lang
}

const filteredExercises = computed(() => {
  let result = exercises.value
  if (currentLanguageFilter.value) {
    const filterLang = currentLanguageFilter.value.toLowerCase()
    result = result.filter(item => {
      const effectiveLang = getEffectiveLanguage(item)
      return effectiveLang === filterLang
    })
  }
  return result
})

const currentLanguage = computed(() => {
  return getEffectiveLanguage(selectedExercise.value)
})

onMounted(() => {
  fetchExercises()
})

const fetchExercises = async () => {
  loading.value = true
  try {
    const res = await request.get('/exercises')
    const exerciseList = Array.isArray(res) ? res : (res.data || [])
    exercises.value = exerciseList.filter(ex =>
      ex.exercise_type === 'code' || ex.exercise_type === 'sql' ||
      ex.category?.includes('浠ｇ爜') || ex.category?.includes('缂栫▼')
    )
  } catch (error) {
    console.error('鑾峰彇涔犻澶辫触:', error)
    ElMessage.error('鑾峰彇涔犻澶辫触')
  } finally {
    loading.value = false
  }
}

const selectExercise = (exercise) => {
  selectedExercise.value = exercise
  submitResult.value = null
  submissionResult.value = null
  aiEvaluationResult.value = null
  userCode.value = exercise.code_template || ''
}

const handleCodeRun = (event) => {
  submitResult.value = event.result
  aiEvaluationResult.value = null
}

const getAIEvaluation = async () => {
  if (!selectedExercise.value || !userCode.value.trim()) {
    ElMessage.warning('璇峰厛鎵ц浠ｇ爜')
    return
  }

  aiLoading.value = true
  try {
    const res = await request.post('/exercise/evaluate', {
      exercise_id: selectedExercise.value.id,
      language: currentLanguage.value,
      source_code: userCode.value,
      exercise_description: selectedExercise.value.description,
      test_cases: selectedExercise.value.test_cases,
      expected_output: selectedExercise.value.expected_output
    })

    aiEvaluationResult.value = res
    ElMessage.success('AI璇勪及瀹屾垚')
  } catch (error) {
    console.error('AI璇勪及澶辫触:', error)
    ElMessage.error('AI璇勪及澶辫触锛岃绋嶅悗閲嶈瘯')
  } finally {
    aiLoading.value = false
  }
}

const submitCode = async () => {
  if (!selectedExercise.value || !userCode.value.trim()) {
    ElMessage.warning('璇峰厛缂栧啓浠ｇ爜')
    return
  }

  submitLoading.value = true
  try {
    const res = await request.post('/exercise/submit', {
      exercise_id: selectedExercise.value.id,
      solution: userCode.value,
      language: currentLanguage.value,
      exercise_type: selectedExercise.value.exercise_type || 'code'
    })

    submissionResult.value = res
    ElMessage.success(res.message || (res.judge_result?.all_passed ? '全部通过' : '提交完成'))
  } catch (error) {
    console.error('鎻愪氦鍒ら澶辫触:', error)
    ElMessage.error(error.response?.data?.detail || '鎻愪氦鍒ら澶辫触')
  } finally {
    submitLoading.value = false
  }
}

const getDifficultyText = (difficulty) => {
  const map = { easy: '简单', medium: '中等', hard: '困难', beginner: '入门', intermediate: '进阶', advanced: '高级' }
  return map[difficulty] || difficulty
}

const getScoreClass = (score) => {
  if (score >= 80) return 'score-high'
  if (score >= 60) return 'score-mid'
  return 'score-low'
}

const renderDescription = (text) => {
  if (!text) return ''
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/\n/g, '<br>')
    .replace(/`([^`]+)`/g, '<code>$1</code>')
}
</script>

<style scoped>
.code-playground {
  padding: 24px 0;
  min-height: 100%;
  width: 100%;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
}

/* ===== 椤甸潰澶撮儴 ===== */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  flex-shrink: 0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background: var(--tm-gradient-brand);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  box-shadow: 0 4px 16px rgba(var(--tm-color-primary-rgb), 0.3);
}

.page-title {
  font-size: 24px;
  font-weight: 700;
  color: var(--tm-text-primary);
  margin: 0 0 4px 0;
  letter-spacing: -0.5px;
}

.page-subtitle {
  font-size: 13px;
  color: var(--tm-text-secondary);
  margin: 0;
}

.header-stats {
  display: flex;
  gap: 12px;
}

.stat-chip {
  display: flex;
  align-items: baseline;
  gap: 4px;
  padding: 6px 14px;
  background: var(--tm-card-bg);
  border: 1px solid var(--tm-border-light);
  border-radius: 20px;
}

.stat-num {
  font-size: 18px;
  font-weight: 700;
  background: var(--tm-gradient-brand);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.stat-label {
  font-size: 12px;
  color: var(--tm-text-secondary);
}

/* ===== 涓诲竷灞€锛坓ap:0 鐢?BaseSplitter 鎻愪緵闂磋窛锛?===== */
.playground-container {
  display: flex;
  gap: 0;
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

/* ===== 宸︿晶闈㈡澘 ===== */
.left-panel {
  flex-shrink: 0;
  background: var(--tm-card-bg);
  border-radius: 16px;
  border: 1px solid var(--tm-border-light);
  box-shadow: var(--tm-shadow-card);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  height: 100%;
}

/* 璇█绛涢€夋爣绛?*/
.filter-tabs {
  display: flex;
  gap: 4px;
  padding: 12px 12px 0;
  flex-shrink: 0;
}

.filter-tab {
  flex: 1;
  padding: 8px 4px;
  border: 1px solid var(--tm-border-light);
  border-radius: 8px;
  background: transparent;
  color: var(--tm-text-secondary);
  font-size: 12px;
  cursor: pointer;
  transition: all 0.25s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 3px;
  white-space: nowrap;
}

.filter-tab:hover {
  background: var(--tm-bg-hover);
  color: var(--tm-text-primary);
  border-color: var(--tm-border-light);
}

.filter-tab.active {
  background: rgba(var(--tm-color-primary-rgb), 0.15);
  color: var(--tm-color-primary);
  border-color: rgba(var(--tm-color-primary-rgb), 0.4);
  font-weight: 600;
}

.tab-icon {
  font-size: 13px;
}

/* 涔犻鍒楄〃 */
.exercise-list {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
  min-height: 0;
}

.exercise-list::-webkit-scrollbar {
  width: 4px;
}

.exercise-list::-webkit-scrollbar-track {
  background: transparent;
}

.exercise-list::-webkit-scrollbar-thumb {
  background: var(--tm-border-light);
  border-radius: 4px;
}

.exercise-item {
  padding: 14px;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.25s ease;
  margin-bottom: 6px;
  border: 1px solid transparent;
  background: transparent;
}

.exercise-item:hover {
  background: var(--tm-bg-hover);
  border-color: var(--tm-border-light);
}

.exercise-item.active {
  background: rgba(var(--tm-color-primary-rgb), 0.08);
  border-color: rgba(var(--tm-color-primary-rgb), 0.3);
  box-shadow: 0 0 0 1px rgba(var(--tm-color-primary-rgb), 0.1);
}

.exercise-item-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.exercise-lang-badge {
  font-size: 11px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 4px;
  letter-spacing: 0.5px;
}

.exercise-lang-badge.lang-python {
  background: rgba(var(--tm-color-primary-rgb), 0.15);
  color: var(--tm-color-primary);
  border: 1px solid rgba(var(--tm-color-primary-rgb), 0.25);
}

.exercise-lang-badge.lang-sql {
  background: rgba(var(--el-color-warning-rgb), 0.15);
  color: var(--el-color-warning);
  border: 1px solid rgba(var(--el-color-warning-rgb), 0.25);
}

.exercise-lang-badge.lang-shell {
  background: rgba(var(--el-color-success-rgb), 0.15);
  color: var(--el-color-success);
  border: 1px solid rgba(var(--el-color-success-rgb), 0.25);
}

.exercise-difficulty {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 4px;
}

.exercise-difficulty.diff-easy,
.exercise-difficulty.diff-beginner {
  background: rgba(var(--el-color-success-rgb), 0.1);
  color: var(--el-color-success);
}

.exercise-difficulty.diff-medium,
.exercise-difficulty.diff-intermediate {
  background: rgba(var(--el-color-warning-rgb), 0.1);
  color: var(--el-color-warning);
}

.exercise-difficulty.diff-hard,
.exercise-difficulty.diff-advanced {
  background: rgba(var(--el-color-danger-rgb), 0.1);
  color: var(--el-color-danger);
}

.exercise-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--tm-text-primary);
  line-height: 1.5;
  margin-bottom: 8px;
}

.exercise-item.active .exercise-title {
  color: var(--tm-color-primary);
}

.exercise-item-bottom {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.exercise-kp {
  font-size: 11px;
  color: var(--tm-text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 160px;
}

.exercise-time {
  font-size: 11px;
  color: var(--tm-text-secondary);
  flex-shrink: 0;
}

/* 绌虹姸鎬?*/
.empty-state {
  padding: 40px 20px;
  text-align: center;
  color: var(--tm-text-secondary);
}

.empty-icon {
  font-size: 32px;
  margin-bottom: 8px;
}

.empty-state p {
  margin: 0 0 12px;
  font-size: 14px;
}

.empty-reset-btn {
  padding: 6px 16px;
  border-radius: 6px;
  border: 1px solid var(--tm-border-light);
  background: transparent;
  color: var(--tm-color-primary);
  cursor: pointer;
  font-size: 13px;
  transition: all 0.2s;
}

.empty-reset-btn:hover {
  background: rgba(var(--tm-color-primary-rgb), 0.1);
  border-color: rgba(var(--tm-color-primary-rgb), 0.3);
}

/* ===== 鍙充晶闈㈡澘 ===== */
.right-panel {
  flex: 1 1 0;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 16px;
  overflow-y: auto;
  height: 100%;
  min-height: 0;
}

.right-panel::-webkit-scrollbar {
  width: 4px;
}

.right-panel::-webkit-scrollbar-track {
  background: transparent;
}

.right-panel::-webkit-scrollbar-thumb {
  background: var(--tm-border-light);
  border-radius: 4px;
}

/* 娆㈣繋鐘舵€?*/
.welcome-state {
  background: var(--tm-card-bg);
  border-radius: 16px;
  border: 1px solid var(--tm-border-light);
  box-shadow: var(--tm-shadow-card);
  padding: 80px 40px;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex: 1;
}

.welcome-icon {
  color: var(--tm-text-secondary);
  opacity: 0.4;
  margin-bottom: 20px;
}

.welcome-state h2 {
  font-size: 20px;
  font-weight: 600;
  color: var(--tm-text-primary);
  margin: 0 0 8px;
}

.welcome-state p {
  font-size: 14px;
  color: var(--tm-text-secondary);
  margin: 0 0 32px;
}

.welcome-features {
  display: flex;
  gap: 32px;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: var(--tm-text-regular);
}

.feature-icon {
  font-size: 18px;
}

/* ===== 棰樼洰鍖哄煙 ===== */
.problem-section {
  background: var(--tm-card-bg);
  border-radius: 16px;
  border: 1px solid var(--tm-border-light);
  box-shadow: var(--tm-shadow-card);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  flex-shrink: 0;
  overflow: hidden;
}

.problem-header {
  padding: 20px 24px 16px;
  border-bottom: 1px solid var(--tm-border-light);
  background: rgba(var(--tm-color-primary-rgb), 0.02);
}

.problem-title-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.problem-title-row h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 700;
  color: var(--tm-text-primary);
  flex: 1;
}

.problem-lang-badge {
  font-size: 12px;
  font-weight: 600;
  padding: 3px 10px;
  border-radius: 6px;
  flex-shrink: 0;
}

.problem-lang-badge.lang-python {
  background: rgba(var(--tm-color-primary-rgb), 0.15);
  color: var(--tm-color-primary);
  border: 1px solid rgba(var(--tm-color-primary-rgb), 0.25);
}

.problem-lang-badge.lang-sql {
  background: rgba(var(--el-color-warning-rgb), 0.15);
  color: var(--el-color-warning);
  border: 1px solid rgba(var(--el-color-warning-rgb), 0.25);
}

.problem-lang-badge.lang-shell {
  background: rgba(var(--el-color-success-rgb), 0.15);
  color: var(--el-color-success);
  border: 1px solid rgba(var(--el-color-success-rgb), 0.25);
}

.problem-tags {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.problem-tag {
  font-size: 12px;
  padding: 3px 10px;
  border-radius: 6px;
  background: rgba(var(--tm-color-primary-rgb), 0.05);
  color: var(--tm-text-secondary);
  border: 1px solid var(--tm-border-light);
}

.problem-tag.diff-tag.diff-easy,
.problem-tag.diff-tag.diff-beginner {
  background: rgba(var(--el-color-success-rgb), 0.1);
  color: var(--el-color-success);
  border-color: rgba(var(--el-color-success-rgb), 0.2);
}

.problem-tag.diff-tag.diff-medium,
.problem-tag.diff-tag.diff-intermediate {
  background: rgba(var(--el-color-warning-rgb), 0.1);
  color: var(--el-color-warning);
  border-color: rgba(var(--el-color-warning-rgb), 0.2);
}

.problem-tag.diff-tag.diff-hard,
.problem-tag.diff-tag.diff-advanced {
  background: rgba(var(--el-color-danger-rgb), 0.1);
  color: var(--el-color-danger);
  border-color: rgba(var(--el-color-danger-rgb), 0.2);
}

.problem-tag.time-tag {
  background: rgba(var(--tm-color-primary-rgb), 0.1);
  color: var(--tm-color-primary);
  border-color: rgba(var(--tm-color-primary-rgb), 0.2);
}

.problem-body {
  padding: 20px 24px;
}

.problem-description {
  font-size: 14px;
  line-height: 1.8;
  color: var(--tm-text-primary);
  margin-bottom: 16px;
}

.problem-description :deep(code) {
  background: rgba(var(--tm-color-primary-rgb), 0.1);
  color: var(--tm-color-primary);
  padding: 1px 6px;
  border-radius: 4px;
  font-size: 13px;
  font-family: 'Consolas', 'Monaco', monospace;
}

.section-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 600;
  color: var(--tm-text-regular);
  margin-bottom: 8px;
}

.problem-instructions,
.problem-testcases {
  margin-bottom: 16px;
}

.problem-instructions pre,
.problem-testcases pre,
.ai-optimized pre {
  background: var(--bg-surface);
  padding: 14px 16px;
  border-radius: 10px;
  font-size: 13px;
  line-height: 1.6;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  white-space: pre-wrap;
  word-wrap: break-word;
  margin: 0;
  border: 1px solid var(--tm-border-light);
  color: var(--tm-text-regular);
}

/* ===== 缂栬緫鍣ㄥ尯鍩?===== */
.editor-section {
  flex: 1;
  min-height: 320px;
  display: flex;
  flex-direction: column;
}

.editor-section :deep(.code-editor) {
  flex: 1;
  min-height: 320px;
}

/* ===== 鎵ц缁撴灉 ===== */
.result-section {
  flex-shrink: 0;
}

.result-card {
  border-radius: 12px;
  border: 1px solid var(--tm-border-light);
  overflow: hidden;
}

.result-card.result-success {
  border-color: rgba(var(--el-color-success-rgb), 0.2);
}

.result-card.result-error {
  border-color: rgba(var(--el-color-danger-rgb), 0.2);
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid var(--tm-border-light);
}

.result-success .result-header {
  background: rgba(var(--el-color-success-rgb), 0.06);
}

.result-error .result-header {
  background: rgba(var(--el-color-danger-rgb), 0.06);
}

.result-status {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.dot-success {
  background: var(--el-color-success);
  box-shadow: 0 0 8px rgba(var(--el-color-success-rgb), 0.5);
}

.dot-error {
  background: var(--el-color-danger);
  box-shadow: 0 0 8px rgba(var(--el-color-danger-rgb), 0.5);
}

.status-text {
  font-size: 14px;
  font-weight: 600;
  color: var(--tm-text-primary);
}

.result-time {
  font-size: 12px;
  color: var(--tm-text-secondary);
  font-family: 'Consolas', monospace;
}

.result-body {
  padding: 12px 16px;
  background: var(--tm-card-bg);
}

.result-block {
  margin-bottom: 8px;
}

.result-block:last-child {
  margin-bottom: 0;
}

.result-label {
  font-size: 11px;
  font-weight: 600;
  color: var(--tm-text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 6px;
}

.error-label {
  color: var(--el-color-danger);
}

.result-output {
  background: var(--bg-surface);
  padding: 12px 14px;
  border-radius: 8px;
  font-size: 13px;
  font-family: 'Consolas', 'Monaco', monospace;
  white-space: pre-wrap;
  word-wrap: break-word;
  margin: 0;
  color: var(--el-color-success);
  border: 1px solid var(--tm-border-light);
}

.error-output {
  color: var(--el-color-danger);
  background: rgba(var(--el-color-danger-rgb), 0.04);
}

.no-output-block {
  .no-output-msg {
    display: flex;
    align-items: flex-start;
    gap: 10px;
    padding: 12px 14px;
    background: rgba(var(--el-color-success-rgb), 0.06);
    border: 1px solid rgba(var(--el-color-success-rgb), 0.15);
    border-radius: 8px;
    font-size: 13px;
    color: var(--tm-text-regular);
    line-height: 1.6;
  }

  .no-output-icon {
    color: var(--el-color-success);
    font-weight: 700;
    font-size: 16px;
    flex-shrink: 0;
    margin-top: 1px;
  }

  .no-output-hint {
    margin-top: 8px;
    font-size: 12px;
    color: var(--tm-text-secondary);
    line-height: 1.5;

    code {
      background: rgba(var(--tm-color-primary-rgb), 0.12);
      color: var(--tm-color-primary);
      padding: 1px 5px;
      border-radius: 3px;
      font-size: 12px;
      font-family: 'Consolas', 'Monaco', monospace;
    }
  }
}

/* ===== 鎻愪氦鍒ら鍖哄煙 ===== */
.submit-section {
  flex-shrink: 0;
}

.submit-card {
  border-radius: 12px;
  border: 1px solid var(--tm-border-light);
  overflow: hidden;
  background: var(--tm-card-bg);
}

.submit-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid var(--tm-border-light);
  background: rgba(var(--tm-color-primary-rgb), 0.06);
}

.submit-status {
  display: flex;
  align-items: center;
  gap: 8px;
}

.submit-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.dot-submitted {
  background: var(--tm-color-primary);
  box-shadow: 0 0 8px rgba(var(--tm-color-primary-rgb), 0.5);
}

.submit-text {
  font-size: 14px;
  font-weight: 600;
  color: var(--tm-text-primary);
}

.submit-time {
  font-size: 12px;
  color: var(--tm-text-secondary);
  font-family: 'Consolas', monospace;
}

.submit-body {
  padding: 16px;
}

.submit-result-block {
  margin-bottom: 12px;
}

.submit-result-block:last-child {
  margin-bottom: 0;
}

.testcase-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.testcase-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  border-radius: 8px;
  font-size: 13px;
}

.testcase-item.tc-pass {
  background: rgba(var(--el-color-success-rgb), 0.06);
  border: 1px solid rgba(var(--el-color-success-rgb), 0.15);
}

.testcase-item.tc-fail {
  background: rgba(var(--el-color-danger-rgb), 0.06);
  border: 1px solid rgba(var(--el-color-danger-rgb), 0.15);
}

.testcase-icon {
  font-size: 16px;
  flex-shrink: 0;
}

.testcase-label {
  flex: 1;
  font-weight: 500;
  color: var(--tm-text-primary);
}

.testcase-item.tc-pass .testcase-label {
  color: var(--el-color-success);
}

.testcase-item.tc-fail .testcase-label {
  color: var(--el-color-danger);
}

.testcase-detail {
  font-size: 11px;
  color: var(--tm-text-secondary);
  font-family: 'Consolas', monospace;
}

.submit-actions {
  padding: 12px 16px;
  border-top: 1px solid var(--tm-border-light);
  display: flex;
  gap: 10px;
  justify-content: flex-end;
}

.submit-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 20px;
  border-radius: 8px;
  border: 1px solid rgba(var(--tm-color-primary-rgb), 0.3);
  background: rgba(var(--tm-color-primary-rgb), 0.15);
  color: var(--tm-color-primary);
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
  transition: all 0.25s;
}

.submit-btn:hover:not(:disabled) {
  background: rgba(var(--tm-color-primary-rgb), 0.25);
  border-color: rgba(var(--tm-color-primary-rgb), 0.5);
  box-shadow: 0 0 12px rgba(var(--tm-color-primary-rgb), 0.2);
}

.submit-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.submit-btn-running {
  display: inline-block;
  width: 14px;
  height: 14px;
  border: 2px solid rgba(var(--tm-color-primary-rgb), 0.3);
  border-top-color: var(--tm-color-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.result-actions {
  padding: 12px 16px;
  border-top: 1px solid var(--tm-border-light);
  display: flex;
  justify-content: flex-end;
}

.ai-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: 8px;
  border: 1px solid rgba(var(--tm-color-primary-rgb), 0.3);
  background: rgba(var(--tm-color-primary-rgb), 0.1);
  color: var(--tm-color-primary);
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  transition: all 0.25s;
}

.ai-btn:hover:not(:disabled) {
  background: rgba(var(--tm-color-primary-rgb), 0.2);
  border-color: rgba(var(--tm-color-primary-rgb), 0.5);
  box-shadow: 0 0 12px rgba(var(--tm-color-primary-rgb), 0.2);
}

.ai-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.ai-btn-loading {
  display: inline-block;
  width: 14px;
  height: 14px;
  border: 2px solid rgba(var(--tm-color-primary-rgb), 0.3);
  border-top-color: var(--tm-color-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* ===== AI璇勪及缁撴灉 ===== */
.ai-result-card {
  border-radius: 12px;
  border: 1px solid rgba(var(--tm-color-primary-rgb), 0.2);
  background: var(--tm-card-bg);
  overflow: hidden;
}

.ai-result-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 16px;
  background: rgba(var(--tm-color-primary-rgb), 0.06);
  border-bottom: 1px solid rgba(var(--tm-color-primary-rgb), 0.1);
}

.ai-avatar {
  font-size: 20px;
}

.ai-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--tm-text-primary);
  flex: 1;
}

.ai-score-badge {
  font-size: 14px;
  font-weight: 700;
  padding: 3px 12px;
  border-radius: 6px;
}

.ai-score-badge.score-high {
  background: rgba(var(--el-color-success-rgb), 0.15);
  color: var(--el-color-success);
}

.ai-score-badge.score-mid {
  background: rgba(var(--el-color-warning-rgb), 0.15);
  color: var(--el-color-warning);
}

.ai-score-badge.score-low {
  background: rgba(var(--el-color-danger-rgb), 0.15);
  color: var(--el-color-danger);
}

.ai-score-bar {
  padding: 0 16px;
  margin-top: 12px;
}

.score-bar-track {
  height: 6px;
  background: rgba(var(--tm-text-secondary-rgb), 0.1);
  border-radius: 3px;
  overflow: hidden;
}

.score-bar-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 0.6s ease;
}

.score-bar-fill.score-high {
  background: linear-gradient(90deg, var(--el-color-success), rgba(var(--el-color-success-rgb), 0.7));
}

.score-bar-fill.score-mid {
  background: linear-gradient(90deg, var(--el-color-warning), rgba(var(--el-color-warning-rgb), 0.7));
}

.score-bar-fill.score-low {
  background: linear-gradient(90deg, var(--el-color-danger), rgba(var(--el-color-danger-rgb), 0.7));
}

.ai-feedback-text {
  padding: 16px;
  font-size: 14px;
  line-height: 1.7;
  color: var(--tm-text-regular);
}

.ai-optimized {
  padding: 0 16px 16px;
}

/* ===== 鍝嶅簲寮?===== */
@media (max-width: 1200px) {
  .playground-container {
    flex-direction: column;
    gap: 16px;
    height: auto;
    overflow: visible;
  }

  .left-panel {
    width: 100% !important;
    max-height: 400px;
    height: auto;
  }

  /* 绾靛悜鍫嗗彔鏃堕殣钘忔嫋鎷芥墜鏌勶紙鐢?:deep 绌块€?scoped 鏍峰紡锛?*/
  .playground-container > :deep(.base-splitter) {
    display: none;
  }

  .right-panel {
    height: auto;
    overflow: visible;
  }

  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .welcome-features {
    gap: 16px;
  }
}

@media (max-width: 768px) {
  .filter-tabs {
    flex-wrap: wrap;
  }

  .filter-tab {
    font-size: 11px;
    padding: 6px 3px;
  }

  .welcome-features {
    flex-direction: column;
    gap: 12px;
  }

  .header-stats {
    display: none;
  }
}
</style>


