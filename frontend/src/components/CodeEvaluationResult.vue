﻿<template>
  <div class="code-evaluation-result">
    <!-- 状态指示器 -->
    <div class="status-indicator" :class="statusClass">
      <el-icon v-if="status === 'success'"><CircleCheck /></el-icon>
      <el-icon v-if="status === 'failed'"><CircleClose /></el-icon>
      <el-icon v-if="status === 'timeout'"><Clock /></el-icon>
      <span class="status-text">{{ statusText }}</span>
    </div>

    <!-- AI评分 -->
    <div v-if="score !== null" class="score-section">
      <div class="score-header">
        <h4>AI评分</h4>
        <span class="score-value" :class="scoreClass">{{ score }}/100</span>
      </div>
      <el-progress
        :percentage="score"
        :status="score >= 80 ? 'success' : score >= 60 ? 'warning' : 'exception'"
        :show-text="false"
      />
      <div class="score-feedback" v-if="feedback">{{ feedback }}</div>
    </div>

    <!-- 执行结果 -->
    <div v-if="hasExecutionResult" class="execution-section">
      <h4>代码执行结果</h4>

      <!-- 标准输出 -->
      <div v-if="stdout" class="output-section stdout">
        <div class="output-header">
          <span class="output-label">标准输出</span>
        </div>
        <pre class="output-content">{{ stdout }}</pre>
      </div>

      <!-- 错误输出 -->
      <div v-if="stderr" class="output-section stderr">
        <div class="output-header">
          <span class="output-label">错误输出</span>
        </div>
        <pre class="output-content">{{ stderr }}</pre>
      </div>

      <!-- 测试用例结果 -->
      <div v-if="testCaseResults && testCaseResults.length > 0" class="test-cases-section">
        <div class="test-cases-header">
          <h4>测试用例结果</h4>
          <span class="summary">
            通过 {{ passedCount }}/{{ totalCount }} ({{ passRate }}%)
          </span>
        </div>
        <div class="test-cases-list">
          <div
            v-for="(testCase, index) in testCaseResults"
            :key="index"
            class="test-case-item"
            :class="testCase.passed ? 'passed' : 'failed'"
          >
            <div class="test-case-info">
              <el-icon class="test-case-icon">
                <CircleCheck v-if="testCase.passed" />
                <CircleClose v-else />
              </el-icon>
              <span class="test-case-name">用例 {{ index + 1 }}</span>
              <span v-if="testCase.execution_time" class="execution-time">
                {{ testCase.execution_time }}ms
              </span>
            </div>
            <div v-if="testCase.error" class="test-case-error">
              {{ testCase.error }}
            </div>
            <div v-if="testCase.actual_output !== undefined" class="test-case-output">
              <span class="output-label">输出：</span>
              <code>{{ testCase.actual_output }}</code>
            </div>
          </div>
        </div>
      </div>

      <!-- 执行摘要 -->
      <div v-if="judgeSummary" class="judge-summary">
        <div class="summary-item">
          <span class="summary-label">总执行时间：</span>
          <span class="summary-value">{{ judgeSummary.total_execution_time_ms }}ms</span>
        </div>
        <div class="summary-item">
          <span class="summary-label">通过率：</span>
          <span class="summary-value">{{ judgeSummary.pass_rate }}%</span>
        </div>
        <div v-if="judgeSummary.summary" class="summary-text">
          {{ judgeSummary.summary }}
        </div>
      </div>
    </div>

    <!-- 优化建议 -->
    <div v-if="optimizationSuggestions" class="optimization-section">
      <h4>优化建议</h4>
      <div class="optimization-content" v-html="renderMarkdown(optimizationSuggestions)"></div>
    </div>

    <!-- 原始代码 -->
    <div v-if="sourceCode" class="source-code-section">
      <div class="source-code-header">
        <h4>提交的代码</h4>
        <el-tag size="small" type="info">{{ language || 'python' }}</el-tag>
      </div>
      <pre class="source-code"><code>{{ sourceCode }}</code></pre>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import {
  CircleCheck,
  CircleClose,
  Clock
} from '@element-plus/icons-vue'
import { renderMarkdown } from '@/utils/markdown'

const props = defineProps({
  // 执行状态
  executionStatus: {
    type: String,
    default: 'pending' // pending, running, success, failed, timeout
  },
  // AI评估状态
  aiEvaluationStatus: {
    type: String,
    default: 'pending' // pending, running, completed, failed
  },
  // AI评分
  score: {
    type: Number,
    default: null
  },
  // AI反馈
  feedback: {
    type: String,
    default: ''
  },
  // 优化建议
  optimizationSuggestions: {
    type: String,
    default: ''
  },
  // 执行结果数据
  executionResult: {
    type: [Object, String],
    default: null
  },
  // 源代码
  sourceCode: {
    type: String,
    default: ''
  },
  // 编程语言
  language: {
    type: String,
    default: 'python'
  }
})

// 解析执行结果
const parsedExecutionResult = computed(() => {
  if (!props.executionResult) return null
  if (typeof props.executionResult === 'string') {
    try {
      return JSON.parse(props.executionResult)
    } catch (e) {
      console.error('解析执行结果失败:', e)
      return null
    }
  }
  return props.executionResult
})

// 状态判断
const status = computed(() => {
  if (props.executionStatus === 'timeout') return 'timeout'
  if (props.executionStatus === 'failed') return 'failed'
  if (props.executionStatus === 'success') return 'success'
  return 'pending'
})

const statusClass = computed(() => {
  return {
    'success': status.value === 'success',
    'failed': status.value === 'failed',
    'timeout': status.value === 'timeout',
    'pending': status.value === 'pending'
  }
})

const statusText = computed(() => {
  const texts = {
    'success': '执行成功',
    'failed': '执行失败',
    'timeout': '执行超时',
    'pending': '等待执行'
  }
  return texts[status.value] || '未知状态'
})

// 评分样式
const scoreClass = computed(() => {
  if (props.score === null) return ''
  if (props.score >= 80) return 'score-high'
  if (props.score >= 60) return 'score-medium'
  return 'score-low'
})

// 是否有执行结果
const hasExecutionResult = computed(() => {
  return parsedExecutionResult.value !== null
})

// 标准输出
const stdout = computed(() => {
  if (!parsedExecutionResult.value) return ''
  return parsedExecutionResult.value.stdout || ''
})

// 错误输出
const stderr = computed(() => {
  if (!parsedExecutionResult.value) return ''
  return parsedExecutionResult.value.stderr || ''
})

// 测试用例结果
const testCaseResults = computed(() => {
  if (!parsedExecutionResult.value) return []
  const judgeResult = parsedExecutionResult.value.judge_result
  if (!judgeResult) return []
  return judgeResult.case_results || []
})

// 测试用例统计
const passedCount = computed(() => {
  return testCaseResults.value.filter(tc => tc.passed).length
})

const totalCount = computed(() => {
  return testCaseResults.value.length
})

const passRate = computed(() => {
  if (totalCount.value === 0) return 0
  return Math.round((passedCount.value / totalCount.value) * 100)
})

// 判题摘要
const judgeSummary = computed(() => {
  if (!parsedExecutionResult.value) return null
  const judgeResult = parsedExecutionResult.value.judge_result
  if (!judgeResult) return null
  return {
    passed_count: judgeResult.passed_count,
    failed_count: judgeResult.failed_count,
    total_cases: judgeResult.total_cases,
    pass_rate: judgeResult.pass_rate,
    all_passed: judgeResult.all_passed,
    summary: judgeResult.summary,
    total_execution_time_ms: judgeResult.total_execution_time_ms
  }
})

// Markdown渲染
</script>

<style scoped>
.code-evaluation-result {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 20px;
  background: var(--tm-card-bg);
  border-radius: 8px;
  border: 1px solid var(--tm-border-light);
}

/* 状态指示器 */
.status-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 6px;
  font-weight: 600;
}

.status-indicator.success {
  background: rgba(103, 194, 58, 0.1);
  color: #67c23a;
  border-left: 4px solid #67c23a;
}

.status-indicator.failed {
  background: rgba(245, 108, 108, 0.1);
  color: #f56c6c;
  border-left: 4px solid #f56c6c;
}

.status-indicator.timeout {
  background: rgba(230, 162, 60, 0.1);
  color: #e6a23c;
  border-left: 4px solid #e6a23c;
}

.status-indicator.pending {
  background: rgba(144, 147, 153, 0.1);
  color: var(--tm-text-secondary);
  border-left: 4px solid var(--tm-text-secondary);
}

.status-text {
  font-size: 14px;
}

/* 评分部分 */
.score-section {
  padding: 16px;
  background: rgba(var(--tm-bg-page-rgb), 0.5);
  border-radius: 8px;
}

.score-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.score-header h4 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--tm-text-primary);
}

.score-value {
  font-size: 20px;
  font-weight: 700;
}

.score-high {
  color: #67c23a;
}

.score-medium {
  color: #e6a23c;
}

.score-low {
  color: #f56c6c;
}

.score-feedback {
  margin-top: 12px;
  padding: 12px;
  background: rgba(var(--tm-color-primary), 0.05);
  border-radius: 6px;
  font-size: 14px;
  line-height: 1.6;
  color: var(--tm-text-primary);
}

/* 输出部分 */
.execution-section h4 {
  margin: 0 0 16px 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--tm-text-primary);
}

.output-section {
  margin-bottom: 16px;
  border-radius: 6px;
  overflow: hidden;
}

.output-header {
  padding: 8px 12px;
  background: rgba(var(--tm-bg-page-rgb), 0.8);
  border-bottom: 1px solid var(--tm-border-light);
  font-size: 12px;
  font-weight: 600;
  color: var(--tm-text-secondary);
}

.output-content {
  margin: 0;
  padding: 12px;
  background: rgba(var(--tm-bg-page-rgb), 0.5);
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.5;
  white-space: pre-wrap;
  overflow-x: auto;
  max-height: 300px;
  overflow-y: auto;
}

.stdout .output-header {
  color: #67c23a;
}

.stderr .output-header {
  color: #f56c6c;
}

/* 测试用例部分 */
.test-cases-section {
  margin-top: 16px;
}

.test-cases-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.test-cases-header h4 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--tm-text-primary);
}

.test-cases-header .summary {
  font-size: 12px;
  color: var(--tm-text-secondary);
}

.test-cases-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.test-case-item {
  padding: 12px;
  border-radius: 6px;
  border: 1px solid var(--tm-border-light);
}

.test-case-item.passed {
  background: rgba(103, 194, 58, 0.05);
  border-color: rgba(103, 194, 58, 0.3);
}

.test-case-item.failed {
  background: rgba(245, 108, 108, 0.05);
  border-color: rgba(245, 108, 108, 0.3);
}

.test-case-info {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.test-case-icon {
  font-size: 14px;
}

.test-case-item.passed .test-case-icon {
  color: #67c23a;
}

.test-case-item.failed .test-case-icon {
  color: #f56c6c;
}

.test-case-name {
  flex: 1;
  font-size: 13px;
  font-weight: 600;
  color: var(--tm-text-primary);
}

.execution-time {
  font-size: 11px;
  color: var(--tm-text-secondary);
}

.test-case-error {
  padding: 8px;
  background: rgba(245, 108, 108, 0.1);
  border-radius: 4px;
  font-size: 12px;
  color: #f56c6c;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
}

.test-case-output {
  margin-top: 8px;
  font-size: 12px;
  color: var(--tm-text-secondary);
}

.test-case-output .output-label {
  font-weight: 600;
}

.test-case-output code {
  background: rgba(var(--tm-bg-page-rgb), 0.5);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  color: var(--tm-text-primary);
}

/* 判题摘要 */
.judge-summary {
  padding: 12px;
  background: rgba(var(--tm-bg-page-rgb), 0.5);
  border-radius: 6px;
  font-size: 13px;
}

.summary-item {
  display: flex;
  justify-content: space-between;
  margin-bottom: 6px;
  color: var(--tm-text-primary);
}

.summary-label {
  color: var(--tm-text-secondary);
}

.summary-value {
  font-weight: 600;
}

.summary-text {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid var(--tm-border-light);
  color: var(--tm-text-primary);
  line-height: 1.5;
}

/* 优化建议 */
.optimization-section h4 {
  margin: 0 0 12px 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--tm-text-primary);
}

.optimization-content {
  padding: 16px;
  background: rgba(230, 162, 60, 0.1);
  border-radius: 8px;
  border-left: 4px solid #e6a23c;
  font-size: 14px;
  line-height: 1.8;
  color: var(--tm-text-primary);
}

/* 源代码部分 */
.source-code-section {
  margin-top: 8px;
}

.source-code-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.source-code-header h4 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--tm-text-primary);
}

.source-code {
  margin: 0;
  padding: 16px;
  background: rgba(var(--tm-bg-page-rgb), 0.5);
  border-radius: 8px;
  border: 1px solid var(--tm-border-light);
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.5;
  white-space: pre-wrap;
  overflow-x: auto;
  max-height: 400px;
  overflow-y: auto;
}

.source-code code {
  color: var(--tm-text-primary);
}
</style>