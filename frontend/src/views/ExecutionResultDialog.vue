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
          <div class="info-item">
            <span class="info-label">请求头:</span>
            <pre class="info-pre">{{ typeof result.request.headers === 'object' ? JSON.stringify(result.request.headers, null, 2) : result.request.headers }}</pre>
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
        </div>
        <div v-if="result.errorMessage" class="error-message">
          <el-alert type="error" :title="result.errorMessage" :closable="false" show-icon />
        </div>
        <h4>响应体</h4>
        <pre class="response-display">{{ result.response.data || '无响应体' }}</pre>
        <h4 v-if="result.assertionResults?.length">断言结果</h4>
        <el-table
          v-if="result.assertionResults?.length"
          :data="result.assertionResults"
          border
          size="small"
          class="dark-table"
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
      </div>
    </div>
  </el-dialog>
</template>

<script setup>
defineProps({
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
  text-shadow: 0 0 5px rgba(var(--tm-color-primary-rgb), 0.3);
}
</style>