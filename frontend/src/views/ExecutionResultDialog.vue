<template>
  <el-dialog
    :model-value="modelValue"
    @update:model-value="emit('update:modelValue', $event)"
    title="执行结果"
    width="75%"
    destroy-on-close
    custom-class="dark-dialog"
  >
    <div class="result-content">
      <div class="result-summary">
        <el-tag :type="result.passed ? 'success' : 'danger'" size="large" class="result-tag">
          {{ result.passed ? '✓ 通过' : '✗ 失败' }}
        </el-tag>
        <span class="summary-info">
          耗时: {{ result.time }}ms | 断言: {{ result.passedAssertions }}/{{ result.totalAssertions }}
        </span>
      </div>
      <el-divider class="dark-divider" />
      <div class="result-detail">
        <h4>请求信息</h4>
        <div class="request-info">
          <div class="info-item">
            <span class="info-label">请求方法:</span>
            <el-tag type="info" size="small">{{ result.request.method }}</el-tag>
          </div>
          <div class="info-item">
            <span class="info-label">请求地址:</span>
            <span class="info-value">{{ result.request.url }}</span>
          </div>
          <div class="info-item collapsible-item">
            <div class="collapsible-header" @click="showReqHeaders = !showReqHeaders">
              <span class="info-label">请求头:</span>
              <el-icon class="collapse-icon" :class="{ 'is-expanded': showReqHeaders }"><ArrowRight /></el-icon>
            </div>
            <div v-show="showReqHeaders" class="collapsible-body">
              <pre class="info-pre">{{ typeof result.request.headers === 'object' ? JSON.stringify(result.request.headers, null, 2) : result.request.headers }}</pre>
            </div>
          </div>
          <div class="info-item">
            <span class="info-label">请求参数:</span>
            <pre class="info-pre">{{ result.request.params && Object.keys(result.request.params).length ? JSON.stringify(result.request.params, null, 2) : '无' }}</pre>
          </div>
          <div class="info-item">
            <span class="info-label">请求体:</span>
            <pre class="info-pre">{{ result.request.body || '无' }}</pre>
          </div>
        </div>
        <el-divider class="dark-divider" />
        <h4>响应信息</h4>
        <div class="response-info">
          <div class="info-item">
            <span class="info-label">状态码:</span>
            <el-tag v-if="result.hasError" type="warning" size="small">
              连接失败
            </el-tag>
            <el-tag v-else :type="result.status >= 200 && result.status < 300 ? 'success' : 'danger'" size="small">
              {{ result.status || '无' }}
            </el-tag>
          </div>
          <div class="info-item">
            <span class="info-label">耗时:</span>
            <span>{{ result.time }}ms</span>
          </div>
          <div class="info-item collapsible-item">
            <div class="collapsible-header" @click="showResHeaders = !showResHeaders">
              <span class="info-label">响应头:</span>
              <el-icon class="collapse-icon" :class="{ 'is-expanded': showResHeaders }"><ArrowRight /></el-icon>
            </div>
            <div v-show="showResHeaders" class="collapsible-body">
              <pre class="info-pre">{{ result.response?.headers ? (typeof result.response.headers === 'object' ? JSON.stringify(result.response.headers, null, 2) : result.response.headers) : '无' }}</pre>
            </div>
          </div>
        </div>
        <div v-if="result.errorMessage" class="error-message">
          <el-alert type="error" :title="result.errorMessage" :closable="false" show-icon />
        </div>
        <div class="response-body-header">
          <h4>响应体</h4>
          <el-button size="small" text type="primary" @click="copyResponseBody" class="copy-btn">
            <el-icon><DocumentCopy /></el-icon> 复制
          </el-button>
        </div>
        <pre class="response-display" v-html="formattedHighlightedBody"></pre>
        <h4 v-if="result.assertionResults?.length">断言结果</h4>
        <el-table
          v-if="result.assertionResults?.length"
          :data="result.assertionResults"
          border
          size="small"
          class="dark-table"
          row-key="_rowKey"
        >
          <el-table-column prop="field" label="字段" width="150" />
          <el-table-column prop="operator" label="比较" width="80" />
          <el-table-column prop="expected" label="预期值" />
          <el-table-column prop="actual" label="实际值" />
          <el-table-column label="结果" width="80" align="center">
            <template #default="{ row }">
              <el-tag :type="row.passed ? 'success' : 'danger'" size="small">
                {{ row.passed ? '通过' : '失败' }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
        <div v-if="failedAssertions.length" class="assertion-fail-detail">
          <div class="fail-detail-header" @click="showFailDetail = !showFailDetail">
            <span class="fail-detail-title">
              <el-icon><WarningFilled /></el-icon>
              断言失败详情 ({{ failedAssertions.length }} 项)
            </span>
            <el-icon class="collapse-icon" :class="{ 'is-expanded': showFailDetail }"><ArrowRight /></el-icon>
          </div>
          <div v-show="showFailDetail" class="fail-detail-body">
            <div v-for="(item, idx) in failedAssertions" :key="idx" class="fail-item">
              <div class="fail-item-header">
                <el-tag type="danger" size="small">失败</el-tag>
                <span class="fail-field">{{ item.field }}</span>
                <span class="fail-operator">{{ item.operator }}</span>
              </div>
              <div class="fail-compare">
                <div class="compare-row">
                  <span class="compare-label">期望值:</span>
                  <code class="compare-value expected">{{ item.expected }}</code>
                </div>
                <div class="compare-row">
                  <span class="compare-label">实际值:</span>
                  <code class="compare-value actual">{{ item.actual }}</code>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </el-dialog>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { ArrowRight, DocumentCopy, WarningFilled } from '@element-plus/icons-vue'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  result: {
    type: Object,
    default: () => ({
      passed: false,
      status: 200,
      time: 0,
      request: {
        method: 'GET',
        url: '',
        headers: {},
        body: ''
      },
      response: {
        data: ''
      },
      passedAssertions: 0,
      totalAssertions: 0,
      assertionResults: [],
      hasError: false,
      errorMessage: null
    })
  }
})

const emit = defineEmits(['update:modelValue'])

const showReqHeaders = ref(false)
const showResHeaders = ref(false)
const showFailDetail = ref(true)

const failedAssertions = computed(() => {
  return (props.result.assertionResults || []).filter(a => !a.passed)
})

const rawResponseBody = computed(() => {
  return props.result.response?.data || '无响应体'
})

const formattedHighlightedBody = computed(() => {
  const raw = rawResponseBody.value
  if (raw === '无响应体') return '<span class="json-empty">无响应体</span>'
  try {
    const parsed = typeof raw === 'string' ? JSON.parse(raw) : raw
    const formatted = JSON.stringify(parsed, null, 2)
    return syntaxHighlight(formatted)
  } catch {
    return escapeHtml(String(raw))
  }
})

const escapeHtml = (str) => {
  return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
}

const syntaxHighlight = (json) => {
  json = escapeHtml(json)
  return json.replace(
    /("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g,
    (match) => {
      let cls = 'json-number'
      if (/^"/.test(match)) {
        if (/:$/.test(match)) {
          cls = 'json-key'
        } else {
          cls = 'json-string'
        }
      } else if (/true|false/.test(match)) {
        cls = 'json-boolean'
      } else if (/null/.test(match)) {
        cls = 'json-null'
      }
      return `<span class="${cls}">${match}</span>`
    }
  )
}

const copyResponseBody = () => {
  const raw = rawResponseBody.value
  let textToCopy = raw
  try {
    const parsed = typeof raw === 'string' ? JSON.parse(raw) : raw
    textToCopy = JSON.stringify(parsed, null, 2)
  } catch {
    textToCopy = String(raw)
  }
  navigator.clipboard.writeText(textToCopy)
    .then(() => ElMessage.success('响应体已复制到剪贴板'))
    .catch(() => ElMessage.error('复制失败'))
}
</script>

<style scoped>
.result-content {
  max-height: 70vh;
  overflow: auto;
}

.result-summary {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 20px;
  padding: 16px;
  background: var(--tm-bg-card);
  border-radius: 10px;
  border: 1px solid var(--tm-border-light);
}

.summary-info {
  color: var(--tm-text-secondary);
  font-size: 15px;
}

.result-detail h4 {
  margin: 24px 0 16px;
  color: var(--tm-text-primary);
  font-size: 16px;
  font-weight: 600;
  text-shadow: 0 0 5px rgba(var(--tm-color-primary-rgb), 0.3);
}

.response-info {
  display: flex;
  gap: 24px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 16px;
  background: var(--tm-bg-card);
  border-radius: 8px;
  border: 1px solid var(--tm-border-light);
}

.info-label {
  color: var(--tm-text-secondary);
  font-size: 14px;
  font-weight: 500;
}

.error-message {
  margin-bottom: 20px;
}

.response-body-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.response-body-header h4 {
  margin: 24px 0 16px;
}

.copy-btn {
  margin-top: 10px;
}

.response-display {
  background: var(--tm-bg-card);
  color: var(--tm-color-primary);
  padding: 20px;
  border-radius: 10px;
  max-height: 320px;
  overflow: auto;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 14px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-all;
  margin: 0;
  box-shadow: inset 0 2px 8px rgba(0, 0, 0, 0.08);
  border: 1px solid rgba(var(--tm-color-primary-rgb), 0.3);
}

.response-display :deep(.json-key) {
  color: #e06c75;
}

.response-display :deep(.json-string) {
  color: #98c379;
}

.response-display :deep(.json-number) {
  color: #d19a66;
}

.response-display :deep(.json-boolean) {
  color: #c678dd;
}

.response-display :deep(.json-null) {
  color: #c678dd;
  font-style: italic;
}

.response-display :deep(.json-empty) {
  color: var(--tm-text-secondary);
  font-style: italic;
}

.collapsible-item {
  flex-direction: column;
  align-items: flex-start;
  width: 100%;
  cursor: pointer;
}

.collapsible-header {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  cursor: pointer;
  user-select: none;
}

.collapse-icon {
  transition: transform 0.2s;
  color: var(--tm-text-secondary);
  font-size: 14px;
}

.collapse-icon.is-expanded {
  transform: rotate(90deg);
}

.collapsible-body {
  width: 100%;
  margin-top: 8px;
}

.assertion-fail-detail {
  margin-top: 16px;
  border: 1px solid rgba(245, 108, 108, 0.3);
  border-radius: 8px;
  overflow: hidden;
}

.fail-detail-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 16px;
  background: rgba(245, 108, 108, 0.08);
  cursor: pointer;
  user-select: none;
}

.fail-detail-title {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #f56c6c;
  font-size: 14px;
  font-weight: 500;
}

.fail-detail-body {
  padding: 12px 16px;
}

.fail-item {
  padding: 10px 12px;
  margin-bottom: 8px;
  background: var(--tm-bg-card);
  border-radius: 6px;
  border: 1px solid var(--tm-border-light);
}

.fail-item:last-child {
  margin-bottom: 0;
}

.fail-item-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.fail-field {
  font-weight: 600;
  color: var(--tm-text-primary);
  font-size: 14px;
}

.fail-operator {
  color: var(--tm-text-secondary);
  font-size: 12px;
  padding: 2px 8px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 4px;
}

.fail-compare {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding-left: 12px;
}

.compare-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.compare-label {
  font-size: 12px;
  color: var(--tm-text-secondary);
  min-width: 56px;
}

.compare-value {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 13px;
  padding: 2px 8px;
  border-radius: 4px;
  word-break: break-all;
}

.compare-value.expected {
  background: rgba(103, 194, 58, 0.1);
  color: #67c23a;
  border: 1px solid rgba(103, 194, 58, 0.2);
}

.compare-value.actual {
  background: rgba(245, 108, 108, 0.1);
  color: #f56c6c;
  border: 1px solid rgba(245, 108, 108, 0.2);
}
</style>
