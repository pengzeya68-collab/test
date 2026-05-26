<template>
  <div class="code-playground" style="position: relative; z-index: 1;">
    <!-- 背景特效 -->
    <div class="cyber-grid-bg" style="position: absolute; top: 0; left: 0; right: 0; bottom: 0; z-index: -1;"></div>
    <div class="glow-orb" style="position: absolute; top: 5%; right: 5%; width: 400px; height: 400px; background: radial-gradient(circle, rgba(59,130,246,0.12), transparent 70%); border-radius: 50%; z-index: -1; pointer-events: none;"></div>

    <!-- 原始结构恢复 -->
    <div class="page-header">
      <h1 class="page-title">在线代码练习室</h1>
      <p class="page-subtitle">Python / SQL / Shell 在线编程，随时练习</p>
    </div>

    <div class="playground-container">
      <!-- 左侧题目列表 -->
      <div class="left-panel">
        <div class="panel-header">
          <h3>代码习题</h3>
          <el-select 
            v-model="currentLanguageFilter" 
            placeholder="筛选语言" 
            size="small"
            style="width: 100px;"
          >
            <el-option label="全部" value="" />
            <el-option label="Python" value="Python" />
            <el-option label="SQL" value="SQL" />
            <el-option label="Shell" value="Shell" />
          </el-select>
        </div>
        <div class="exercise-list">
          <div 
            class="exercise-item" 
            v-for="exercise in filteredExercises" 
            :key="exercise.id"
            :class="{ active: selectedExercise?.id === exercise.id }"
            @click="selectExercise(exercise)"
          >
            <el-tag :type="getDifficultyTagType(exercise.difficulty)" size="small">
              {{ getDifficultyText(exercise.difficulty) }}
            </el-tag>
            <div class="exercise-info">
              <div class="exercise-title">{{ exercise.title }}</div>
              <div class="exercise-meta">
                <span>{{ exercise.language }}</span>
                <span>{{ exercise.time_estimate }}分钟</span>
              </div>
            </div>
          </div>
        </div>
        <div class="empty-state" v-if="filteredExercises.length === 0 && !loading">
          <el-empty description="暂无习题" :image-size="60" />
        </div>
      </div>

      <!-- 右侧编程区域 -->
      <div class="right-panel">
        <!-- 题目描述 -->
        <div class="problem-section" v-if="selectedExercise">
          <div class="section-header">
            <h2>{{ selectedExercise.title }}</h2>
            <div class="section-meta">
              <el-tag size="small">{{ selectedExercise.language }}</el-tag>
              <el-tag size="small">{{ selectedExercise.knowledge_point }}</el-tag>
              <span>难度：{{ getDifficultyText(selectedExercise.difficulty) }}</span>
            </div>
          </div>
          <div class="problem-content">
            <p class="description">{{ selectedExercise.description }}</p>
            <div class="instructions" v-if="selectedExercise.instructions">
              <h4>要求：</h4>
              <pre>{{ selectedExercise.instructions }}</pre>
            </div>
            <div class="test-cases" v-if="selectedExercise.test_cases">
              <h4>测试用例：</h4>
              <pre>{{ selectedExercise.test_cases }}</pre>
            </div>
          </div>
        </div>

        <!-- 代码编辑器 -->
        <div class="editor-section" v-if="selectedExercise">
          <CodeEditor
            v-model="userCode"
            :language="currentLanguage"
            ref="editorRef"
            @run="handleCodeRun"
          />
        </div>

        <!-- 执行结果 -->
        <div class="result-section" v-if="submitResult">
          <el-alert
            :title="submitResult.success ? '🎉 执行成功！' : '❌ 执行失败'"
            :type="submitResult.success ? 'success' : 'error'"
            show-icon
            :closable="false"
          >
            <template #default>
              <div v-if="submitResult.stdout" class="execution-result">
                <p><strong>运行输出：</strong></p>
                <pre>{{ submitResult.stdout }}</pre>
              </div>
              <div v-if="submitResult.stderr" class="execution-result">
                <p><strong>错误输出：</strong></p>
                <pre class="error">{{ submitResult.stderr }}</pre>
              </div>

              <!-- AI评估按钮 -->
              <div class="ai-evaluation-section" v-if="submitResult.success">
                <el-button
                  type="primary"
                  size="small"
                  @click="getAIEvaluation"
                  :loading="aiLoading"
                  :disabled="aiLoading"
                >
                  <el-icon><ChatLineRound /></el-icon>
                  {{ aiLoading ? 'AI评估中...' : '获取AI点评' }}
                </el-button>
              </div>
            </template>
          </el-alert>
        </div>

        <!-- AI评估结果 -->
        <div class="result-section" v-if="aiEvaluationResult">
          <el-alert
            title="🤖 AI导师点评"
            type="info"
            show-icon
            :closable="false"
          >
            <template #default>
              <div class="ai-evaluation-result">
                <div class="ai-score">
                  <strong>评分：</strong>
                  <span class="score-text">{{ aiEvaluationResult.score }}分 / 100分</span>
                  <el-progress
                    :percentage="aiEvaluationResult.score"
                    :stroke-width="12"
                    :width="120"
                    :show-text="false"
                    style="margin-left: 12px;"
                  />
                </div>
                <div class="ai-feedback">
                  <strong>反馈：</strong>
                  <p>{{ aiEvaluationResult.feedback }}</p>
                </div>
                <div v-if="aiEvaluationResult.optimized_code" class="ai-optimized-code">
                  <strong>优化建议：</strong>
                  <pre>{{ aiEvaluationResult.optimized_code }}</pre>
                </div>
              </div>
            </template>
          </el-alert>
        </div>

        <!-- 无习题选择提示 -->
        <div class="empty-state" v-if="!selectedExercise">
          <el-empty description="请选择一道习题开始练习" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { ChatLineRound } from '@element-plus/icons-vue'
import CodeEditor from '@/components/CodeEditor.vue'
import request from '@/utils/request'

const exercises = ref([])
const loading = ref(false)
const selectedExercise = ref(null)
const userCode = ref('')
const currentLanguageFilter = ref('')
const submitResult = ref(null)
const editorRef = ref(null)
const aiEvaluationResult = ref(null)
const aiLoading = ref(false)

const filteredExercises = computed(() => {
  let result = exercises.value
  if (currentLanguageFilter.value) {
    result = result.filter(item => item.language === currentLanguageFilter.value)
  }
  return result
})

const currentLanguage = computed(() => {
  return selectedExercise.value?.language?.toLowerCase() || 'python'
})

onMounted(() => {
  fetchExercises()
})

const fetchExercises = async () => {
  loading.value = true
  try {
    const res = await request.get('/exercises')
    const exerciseList = Array.isArray(res) ? res : (res.data || [])
    exercises.value = exerciseList.filter(ex => ex.exercise_type === 'code' || ex.category?.includes('代码') || ex.category?.includes('编程'))
  } catch (error) {
    console.error('获取习题失败:', error)
    ElMessage.error('获取习题失败')
  } finally {
    loading.value = false
  }
}

const selectExercise = (exercise) => {
  selectedExercise.value = exercise
  submitResult.value = null
  aiEvaluationResult.value = null
  userCode.value = exercise.code_template || ''
}

const handleCodeRun = (event) => {
  submitResult.value = event.result
  aiEvaluationResult.value = null
}

const getAIEvaluation = async () => {
  if (!selectedExercise.value || !userCode.value.trim()) {
    ElMessage.warning('请先执行代码')
    return
  }

  aiLoading.value = true
  try {
    const res = await request.post('/exercise/evaluate', {
      exercise_id: selectedExercise.value.id.toString(),
      language: currentLanguage.value,
      source_code: userCode.value,
      exercise_description: selectedExercise.value.description,
      test_cases: selectedExercise.value.test_cases,
      expected_output: selectedExercise.value.expected_output
    })

    aiEvaluationResult.value = res.data || res
    ElMessage.success('AI评估完成')
  } catch (error) {
    console.error('AI评估失败:', error)
    ElMessage.error('AI评估失败，请稍后重试')
  } finally {
    aiLoading.value = false
  }
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
</script>

<style scoped>
.code-playground {
  padding: 20px 0;
  min-height: 100%;
  width: 100%;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
}

.page-header {
  margin-bottom: 20px;
  flex-shrink: 0;
}

.page-title {
  font-size: 28px;
  font-weight: bold;
  color: var(--tm-text-primary);
  margin: 0 0 8px 0;
}

.page-subtitle {
  font-size: 14px;
  color: var(--tm-text-secondary);
  margin: 0;
}

.playground-container {
  display: grid;
  grid-template-columns: 300px 1fr;
  gap: 20px;
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

.left-panel {
  background: var(--tm-card-bg);
  border-radius: 12px;
  box-shadow: var(--tm-shadow-card);
  border: var(--tm-card-border);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  height: 100%;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid var(--tm-border-light);
  flex-shrink: 0;
}

.panel-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: bold;
  color: var(--tm-text-primary);
}

.exercise-list {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
  min-height: 0;
}

.exercise-item {
  padding: 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  margin-bottom: 8px;
  border: 1px solid transparent;
}

.exercise-item:hover {
  background-color: var(--tm-bg-hover);
  border-color: var(--tm-border-light);
}

.exercise-item.active {
  background-color: rgba(var(--tm-color-primary-rgb), 0.1);
  border-color: var(--tm-color-primary);
}

.exercise-info {
  margin-top: 8px;
}

.exercise-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--tm-text-primary);
  margin-bottom: 4px;
  line-height: 1.4;
}

.exercise-meta {
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: var(--tm-text-secondary);
}

.right-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
  overflow-y: auto;
  height: 100%;
  min-height: 0;
}

.problem-section {
  background: var(--tm-card-bg);
  border-radius: 12px;
  padding: 20px;
  box-shadow: var(--tm-shadow-card);
  border: var(--tm-card-border);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  flex-shrink: 0;
}

.section-header {
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--tm-border-light);
}

.section-header h2 {
  margin: 0 0 12px 0;
  font-size: 18px;
  font-weight: bold;
  color: var(--tm-text-primary);
}

.section-meta {
  display: flex;
  gap: 12px;
  align-items: center;
  flex-wrap: wrap;
}

.section-meta span {
  font-size: 13px;
  color: var(--tm-text-secondary);
}

.problem-content .description {
  font-size: 15px;
  line-height: 1.8;
  color: var(--tm-text-primary);
  margin-bottom: 16px;
}

.problem-content h4 {
  font-size: 14px;
  font-weight: bold;
  color: var(--tm-text-primary);
  margin: 0 0 8px 0;
}

.instructions, .test-cases {
  margin-bottom: 16px;
}

.instructions pre, .test-cases pre {
  background: rgba(var(--tm-bg-page-rgb), 0.5);
  padding: 12px;
  border-radius: 8px;
  font-size: 13px;
  line-height: 1.6;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  white-space: pre-wrap;
  word-wrap: break-word;
  margin: 0;
}

.editor-section {
  flex: 1;
  min-height: 300px;
  display: flex;
  flex-direction: column;
}

.editor-section :deep(.code-editor) {
  flex: 1;
  min-height: 300px;
}

.result-section {
  flex-shrink: 0;
}

.execution-result {
  margin-top: 12px;
}

.execution-result pre {
  background: rgba(var(--tm-bg-page-rgb), 0.5);
  padding: 12px;
  border-radius: 6px;
  font-size: 13px;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  margin: 4px 0;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.execution-result pre.error {
  color: #f56c6c;
  background: rgba(245, 108, 108, 0.1);
}

.empty-state {
  background: var(--tm-card-bg);
  border-radius: 12px;
  padding: 60px 20px;
  box-shadow: var(--tm-shadow-card);
  border: var(--tm-card-border);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.ai-evaluation-section {
  margin-top: 16px;
  padding-top: 12px;
  border-top: 1px dashed var(--tm-border-light);
}

.ai-evaluation-result {
  margin-top: 12px;
}

.ai-score {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.score-text {
  font-weight: bold;
  color: var(--tm-color-primary);
}

.ai-feedback {
  margin-bottom: 16px;
}

.ai-feedback p {
  margin: 8px 0 0 0;
  padding: 12px;
  background: rgba(var(--tm-bg-page-rgb), 0.5);
  border-radius: 6px;
  line-height: 1.6;
}

.ai-optimized-code {
  margin-top: 16px;
}

.ai-optimized-code pre {
  background: rgba(var(--tm-bg-page-rgb), 0.5);
  padding: 12px;
  border-radius: 6px;
  font-size: 13px;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  white-space: pre-wrap;
  word-wrap: break-word;
  margin: 4px 0;
}

.cyber-grid-bg {
  background-image: 
    linear-gradient(rgba(0, 242, 254, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0, 242, 254, 0.03) 1px, transparent 1px);
  background-size: 30px 30px;
  pointer-events: none;
}

@media (max-width: 1200px) {
  .playground-container {
    grid-template-columns: 1fr;
    height: auto;
    overflow: visible;
  }

  .left-panel {
    max-height: 400px;
    height: auto;
  }
  
  .right-panel {
    height: auto;
    overflow: visible;
  }
}
</style>
