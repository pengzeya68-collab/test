<template>
  <div class="vrt-container">
    <div class="vrt-left-col">
      <div class="vrt-toolbar">
        <span class="vrt-toolbar-label">查找:</span>
        <el-input
          v-model="localSearchQuery"
          size="small"
          clearable
          style="width:150px"
          @keyup.enter="handleSearch"
        />
        <el-checkbox v-model="localCaseSensitive" size="small">区分大小写</el-checkbox>
        <el-checkbox v-model="localRegex" size="small">正则表达式</el-checkbox>
        <el-button size="small" type="primary" plain @click="handleSearch">查找</el-button>
        <el-button size="small" @click="handleResetSearch">重置</el-button>
        <el-select
          v-model="localStatusFilter"
          size="small"
          clearable
          placeholder="全部"
          style="width:85px;margin-left:auto"
        >
          <el-option label="成功" value="success" />
          <el-option label="失败" value="error" />
          <el-option label="异常" value="exception" />
        </el-select>
      </div>
      <div class="vrt-sample-list">
        <div
          v-for="(s, si) in filteredSamples"
          :key="si"
          class="vrt-sample-item"
          :class="{ active: localSelectedIdx === si }"
          @click="handleSelectSample(si)"
        >
          <el-tag
            :type="s.status >= 200 && s.status < 400 ? 'success' : s.status === 0 ? 'danger' : 'warning'"
            size="small"
          >{{ s.status || 'ERR' }}</el-tag>
          <span class="vrt-time">{{ s.elapsed_ms }}ms</span>
          <span class="vrt-name" :title="s.name || s.url">{{ s.name || shortUrl(s.url) }}</span>
          <span v-if="s.error" class="vrt-err" title="有错误">⚠</span>
        </div>
        <div v-if="filteredSamples.length === 0" style="padding:12px;text-align:center;color:#94a3b8;font-size:12px">
          无匹配结果
        </div>
      </div>
    </div>

    <div v-if="selectedSample" class="vrt-detail-panel">
      <el-tabs v-model="localSampleTab" size="small" class="vrt-tabs">
        <el-tab-pane label="采样器结果" name="sampler">
          <table class="vrt-table">
            <tr><td class="vrt-label">Thread Name</td><td>{{ selectedSample.thread_name || '线程组 1-' + (localSelectedIdx + 1) }}</td></tr>
            <tr><td class="vrt-label">Sample Start</td><td>{{ selectedSample.start_time || '-' }}</td></tr>
            <tr><td class="vrt-label">Load time</td><td><b>{{ selectedSample.elapsed_ms || 0 }}</b> ms</td></tr>
            <tr><td class="vrt-label">Connect Time</td><td>{{ selectedSample.connect_time_ms ?? '-' }} ms</td></tr>
            <tr><td class="vrt-label">Latency</td><td>{{ (selectedSample.latency_ms ?? selectedSample.elapsed_ms) }} ms</td></tr>
            <tr><td class="vrt-label">Size in bytes</td><td>{{ selectedSample.body_size || 0 }}</td></tr>
            <tr><td class="vrt-label">Sent bytes</td><td>{{ selectedSample.sent_bytes || 0 }}</td></tr>
            <tr><td class="vrt-label">Headers size in bytes</td><td>{{ selectedSample.headers_size || 0 }}</td></tr>
            <tr><td class="vrt-label">Body size in bytes</td><td>{{ selectedSample.body_size || 0 }}</td></tr>
            <tr><td class="vrt-label">Sample Count</td><td>1</td></tr>
            <tr><td class="vrt-label">Error Count</td><td :style="{ color: selectedSample.error ? 'var(--el-color-danger)' : 'var(--el-color-success)' }">{{ selectedSample.error ? '1' : '0' }}</td></tr>
            <tr><td class="vrt-label">Data type</td><td>{{ selectedSample.data_type || 'text' }}</td></tr>
            <tr><td class="vrt-label">Response code</td><td><el-tag :type="selectedSample.status >= 200 && selectedSample.status < 400 ? 'success' : 'danger'" size="small">{{ selectedSample.status || 'ERR' }}</el-tag></td></tr>
            <tr><td class="vrt-label">Response message</td><td>{{ selectedSample.response_message || (selectedSample.status >= 200 && selectedSample.status < 400 ? 'OK' : 'Error') }}</td></tr>
            <template v-if="selectedSample.http_fields">
              <tr class="vrt-subheader"><td colspan="2"><b>HTTPSamplerResult fields:</b></td></tr>
              <tr><td class="vrt-label indent1">ContentType</td><td>{{ selectedSample.http_fields.content_type || '-' }}</td></tr>
              <tr><td class="vrt-label indent1">DataEncoding</td><td>{{ selectedSample.http_fields.encoding || 'null' }}</td></tr>
            </template>
          </table>
        </el-tab-pane>

        <el-tab-pane label="请求" name="request">
          <el-tabs v-model="localRequestTab" size="small" class="vrt-inner-tabs">
            <el-tab-pane label="Request Body" name="rbody">
              <pre class="vrt-code">{{ selectedSample.request_body || '(无请求体)' }}</pre>
            </el-tab-pane>
            <el-tab-pane label="Request Headers" name="rheaders">
              <pre class="vrt-code">
                <template v-if="selectedSample.request_headers">{{ formatHeaders(selectedSample.request_headers) }}</template>
                <template v-else>(无请求头信息)</template>
              </pre>
            </el-tab-pane>
          </el-tabs>
          <div v-if="selectedSample.method" class="vrt-http-line">
            <code>{{ selectedSample.method }} {{ selectedSample.url }}</code>
          </div>
        </el-tab-pane>

        <el-tab-pane label="响应数据" name="response">
          <el-tabs v-model="localResponseTab" size="small" class="vrt-inner-tabs">
            <el-tab-pane label="Response Body" name="resbody">
              <pre class="vrt-code" :class="{ 'vrt-error-body': selectedSample.error }">{{ selectedSample.response_body || selectedSample.error || '(空响应)' }}</pre>
            </el-tab-pane>
            <el-tab-pane label="Response headers" name="resheaders">
              <pre class="vrt-code">
                <template v-if="selectedSample.response_headers">{{ formatHeaders(selectedSample.response_headers) }}</template>
                <template v-else>(无响应头信息)</template>
              </pre>
            </el-tab-pane>
          </el-tabs>
        </el-tab-pane>
      </el-tabs>
    </div>
    <div v-else class="vrt-empty-detail">
      👆 点击上方样本查看详情
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'

const props = defineProps({
  samples: {
    type: Array,
    default: () => []
  },
  searchQuery: {
    type: String,
    default: ''
  },
  caseSensitive: {
    type: Boolean,
    default: false
  },
  useRegex: {
    type: Boolean,
    default: false
  },
  statusFilter: {
    type: String,
    default: ''
  },
  sampleTab: {
    type: String,
    default: 'sampler'
  },
  requestTab: {
    type: String,
    default: 'rbody'
  },
  responseTab: {
    type: String,
    default: 'resbody'
  }
})

const emit = defineEmits([
  'update:searchQuery',
  'update:caseSensitive',
  'update:useRegex',
  'update:statusFilter',
  'update:sampleTab',
  'update:requestTab',
  'update:responseTab',
  'sample-select',
  'search'
])

const localSearchQuery = ref(props.searchQuery)
const localCaseSensitive = ref(props.caseSensitive)
const localRegex = ref(props.useRegex)
const localStatusFilter = ref(props.statusFilter)
const localSelectedIdx = ref(-1)
const localSampleTab = ref(props.sampleTab)
const localRequestTab = ref(props.requestTab)
const localResponseTab = ref(props.responseTab)

watch(() => props.searchQuery, (val) => { localSearchQuery.value = val })
watch(() => props.caseSensitive, (val) => { localCaseSensitive.value = val })
watch(() => props.useRegex, (val) => { localRegex.value = val })
watch(() => props.statusFilter, (val) => { localStatusFilter.value = val })
watch(() => props.sampleTab, (val) => { localSampleTab.value = val })
watch(() => props.requestTab, (val) => { localRequestTab.value = val })
watch(() => props.responseTab, (val) => { localResponseTab.value = val })

watch(localSearchQuery, (val) => { emit('update:searchQuery', val) })
watch(localCaseSensitive, (val) => { emit('update:caseSensitive', val) })
watch(localRegex, (val) => { emit('update:useRegex', val) })
watch(localStatusFilter, (val) => { emit('update:statusFilter', val) })
watch(localSampleTab, (val) => { emit('update:sampleTab', val) })
watch(localRequestTab, (val) => { emit('update:requestTab', val) })
watch(localResponseTab, (val) => { emit('update:responseTab', val) })

const filteredSamples = computed(() => {
  let result = props.samples || []

  if (localStatusFilter.value) {
    const filter = localStatusFilter.value
    result = result.filter(s => {
      if (filter === 'success') return s.status >= 200 && s.status < 400
      if (filter === 'error') return s.status === 0 || s.status >= 400
      if (filter === 'exception') return !!s.error
      return true
    })
  }

  if (localSearchQuery.value) {
    const query = localSearchQuery.value
    const caseSensitive = localCaseSensitive.value
    const isRegex = localRegex.value

    let regex
    if (isRegex) {
      try {
        regex = new RegExp(query, caseSensitive ? '' : 'i')
      } catch (e) {
        regex = null
      }
    }

    result = result.filter(s => {
      const text = [s.name, s.url, s.request_body, s.response_body, s.error]
        .filter(Boolean)
        .join(' ')

      if (regex) {
        return regex.test(text)
      }

      return caseSensitive
        ? text.includes(query)
        : text.toLowerCase().includes(query.toLowerCase())
    })
  }

  return result
})

const selectedSample = computed(() => {
  if (localSelectedIdx.value >= 0 && localSelectedIdx.value < filteredSamples.value.length) {
    return filteredSamples.value[localSelectedIdx.value]
  }
  return null
})

function shortUrl(url) {
  if (!url) return '-'
  try {
    const u = new URL(url)
    return u.pathname || '/'
  } catch {
    return url.length > 50 ? url.slice(0, 50) + '...' : url
  }
}

function formatHeaders(headers) {
  if (!headers) return ''
  if (typeof headers === 'string') return headers
  if (typeof headers === 'object') {
    return Object.entries(headers)
      .map(([k, v]) => `${k}: ${v}`)
      .join('\n')
  }
  return String(headers)
}

function handleSelectSample(idx) {
  localSelectedIdx.value = idx
  emit('sample-select', {
    index: idx,
    sample: filteredSamples.value[idx]
  })
}

function handleSearch() {
  emit('search', {
    query: localSearchQuery.value,
    caseSensitive: localCaseSensitive.value,
    regex: localRegex.value
  })
}

function handleResetSearch() {
  localSearchQuery.value = ''
  localCaseSensitive.value = false
  localRegex.value = false
  localStatusFilter.value = ''
  emit('update:searchQuery', '')
  emit('update:caseSensitive', false)
  emit('update:useRegex', false)
  emit('update:statusFilter', '')
  emit('search', { query: '', caseSensitive: false, regex: false })
}
</script>

<style scoped>
.vrt-container {
  display: flex;
  gap: 0;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  overflow: hidden;
  background: #fff;
  flex: 1;
  min-height: 300px;
  min-height: 0;
}

.vrt-left-col {
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  width: 280px;
  border-right: 1px solid #ccc;
  background: #f5f5f5;
  overflow: hidden;
  min-height: 0;
}

.vrt-sample-list {
  flex: 1;
  overflow-y: auto;
  min-height: 0;
}

.vrt-sample-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 8px;
  cursor: pointer;
  transition: background 0.1s;
  font-size: 11px;
  border-bottom: 1px solid #f3f4f6;
}

.vrt-sample-item:hover {
  background: #eff6ff;
}

.vrt-sample-item.active {
  background: #dbeafe;
  border-left: 3px solid #3b82f6;
}

.vrt-time {
  font-weight: 700;
  width: 52px;
  flex-shrink: 0;
  color: #374151;
  font-size: 11px;
}

.vrt-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: #1f2937;
  font-size: 11px;
  font-weight: 500;
}

.vrt-err {
  color: #dc2626;
  font-size: 10px;
  flex-shrink: 0;
}

.vrt-toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  padding: 4px 6px;
  background: #e8eaed;
  border-bottom: 1px solid #ccc;
  align-items: center;
  flex-shrink: 0;
  position: sticky;
  top: 0;
  z-index: 10;
}

.vrt-toolbar-label {
  font-size: 12px;
  color: #333;
  white-space: nowrap;
  flex-shrink: 0;
}

.vrt-toolbar .el-checkbox {
  margin-right: 0;
  font-size: 11px;
  height: 24px;
}

.vrt-toolbar .el-checkbox__label {
  font-size: 11px;
  padding-left: 3px;
}

.vrt-detail-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-width: 0;
}

.vrt-empty-detail {
  display: flex;
  align-items: center;
  justify-content: center;
  flex: 1;
  color: #94a3b8;
  font-size: 13px;
}

.vrt-tabs {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.vrt-tabs :deep(.el-tabs__header) {
  margin-bottom: 0;
  background: #f9fafb;
  border-bottom: 1px solid #e5e7eb;
  padding: 0 8px;
}

.vrt-tabs :deep(.el-tabs__content) {
  flex: 1;
  overflow-y: auto;
  padding: 8px 12px;
}

.vrt-inner-tabs :deep(.el-tabs__header) {
  margin-bottom: 4px;
}

.vrt-inner-tabs :deep(.el-tabs__content) {
  max-height: calc(100% - 36px);
  overflow-y: auto;
}

.vrt-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
  line-height: 1.8;
}

.vrt-table td {
  padding: 2px 8px;
  border-bottom: 1px solid #f3f4f6;
  vertical-align: top;
}

.vrt-label {
  color: #6b7280;
  font-weight: 600;
  white-space: nowrap;
  width: 150px;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 11px;
}

.vrt-subheader td {
  background: #f9fafb;
  padding: 4px 8px !important;
  font-size: 11px;
}

.indent1 {
  padding-left: 28px !important;
}

.vrt-code {
  background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
  padding: 12px;
  border-radius: 8px;
  font-size: 11.5px;
  color: #e2e8f0;
  font-family: 'Consolas', 'Monaco', monospace;
  max-height: 300px;
  overflow: auto;
  margin: 0;
  white-space: pre-wrap;
  word-break: break-all;
  border: 1px solid rgba(148, 163, 184, 0.1);
  box-shadow: inset 0 2px 6px rgba(0, 0, 0, 0.12);
}

.vrt-error-body {
  color: #fca5a5;
}

.vrt-http-line {
  padding: 8px 12px;
  background: rgba(99, 102, 241, 0.04);
  border-radius: 6px;
  margin-top: 6px;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 11.5px;
  word-break: break-all;
}
</style>
