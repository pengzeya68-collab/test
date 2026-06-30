<template>
  <div class="shared-doc-container">
    <!-- 加载中 -->
    <div v-if="loading" class="loading-state">
      <el-icon class="is-loading" :size="40"><Loading /></el-icon>
      <p>正在加载文档...</p>
    </div>

    <!-- 错误状态 -->
    <div v-else-if="error" class="error-state">
      <el-result :icon="errorIcon" :title="errorTitle" :sub-title="errorMessage">
        <template #extra>
          <el-button type="primary" @click="goHome">返回首页</el-button>
        </template>
      </el-result>
    </div>

    <!-- 文档内容 -->
    <template v-else>
      <!-- HTML 格式：直接在 iframe 中渲染 -->
      <div v-if="docFormat === 'html'" class="html-doc-wrapper">
        <iframe :srcdoc="docContent" class="html-iframe" sandbox="allow-scripts"></iframe>
      </div>

      <!-- OpenAPI 格式：展示 JSON + 元信息 -->
      <div v-else-if="docFormat === 'openapi'" class="json-doc-wrapper">
        <div class="doc-meta-bar">
          <div class="meta-left">
            <h2>{{ docTitle }}</h2>
            <el-tag type="success" size="small">OpenAPI 3.0</el-tag>
          </div>
          <div class="meta-right">
            <span class="meta-item">
              <el-icon><View /></el-icon>
              浏览 {{ viewCount }} 次
            </span>
            <el-button text size="small" @click="copyJson">
              <el-icon><CopyDocument /></el-icon>
              复制 JSON
            </el-button>
            <el-button text size="small" @click="downloadJson">
              <el-icon><Download /></el-icon>
              下载
            </el-button>
          </div>
        </div>
        <pre class="json-viewer"><code>{{ formattedJson }}</code></pre>
      </div>

      <!-- Markdown 格式：渲染 Markdown + 元信息 -->
      <div v-else-if="docFormat === 'markdown'" class="markdown-doc-wrapper">
        <div class="doc-meta-bar">
          <div class="meta-left">
            <h2>{{ docTitle }}</h2>
            <el-tag type="info" size="small">Markdown</el-tag>
          </div>
          <div class="meta-right">
            <span class="meta-item">
              <el-icon><View /></el-icon>
              浏览 {{ viewCount }} 次
            </span>
            <el-button text size="small" @click="copyMarkdown">
              <el-icon><CopyDocument /></el-icon>
              复制
            </el-button>
            <el-button text size="small" @click="downloadMarkdown">
              <el-icon><Download /></el-icon>
              下载
            </el-button>
          </div>
        </div>
        <div class="markdown-body" v-html="renderedMarkdown"></div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Loading, View, CopyDocument, Download,
} from '@element-plus/icons-vue'
import { autoTestRequest } from '@/utils/request'
import { marked } from 'marked'
import DOMPurify from 'dompurify'

const route = useRoute()
const router = useRouter()

// ========== 状态 ==========
const loading = ref(true)
const error = ref(false)
const errorIcon = ref('warning')
const errorTitle = ref('')
const errorMessage = ref('')
const docContent = ref(null) // html: str, openapi: dict, markdown: str
const docFormat = ref('')
const docTitle = ref('')
const viewCount = ref(0)

// ========== 计算属性 ==========
const formattedJson = computed(() => {
  if (!docContent.value || docFormat.value !== 'openapi') return ''
  try {
    return JSON.stringify(docContent.value, null, 2)
  } catch {
    return String(docContent.value)
  }
})

const renderedMarkdown = computed(() => {
  if (!docContent.value || docFormat.value !== 'markdown') return ''
  try {
    const html = marked(docContent.value)
    return DOMPurify.sanitize(html)
  } catch {
    return docContent.value
  }
})

// ========== 方法 ==========
const goHome = () => router.push('/')

const loadSharedDoc = async () => {
  const token = route.params.token
  if (!token) {
    error.value = true
    errorIcon.value = 'error'
    errorTitle.value = '无效的分享链接'
    errorMessage.value = '分享链接缺少必要的 token 参数'
    loading.value = false
    return
  }

  loading.value = true
  error.value = false

  try {
    // 以 text 方式获取，手动判断 HTML 或 JSON
    const resp = await autoTestRequest.get(
      `/auto-test/api-docs/shared/${token}`,
      {
        responseType: 'text',
        transformResponse: [(data) => data], // 阻止 axios 自动解析 JSON
        // 公开接口即使 token 过期也不触发 401 跳转
        skipAuthError: true,
      }
    )

    // 判断是 HTML 还是 JSON
    const trimmed = (typeof resp === 'string' ? resp : '').trim()
    if (trimmed.startsWith('<!DOCTYPE') || trimmed.startsWith('<html')) {
      // HTML 格式：后端直接返回 HTML 页面
      docFormat.value = 'html'
      docContent.value = resp
      docTitle.value = 'API 文档'
      viewCount.value = 0
    } else {
      // JSON 格式：解析为对象
      try {
        const payload = JSON.parse(resp)
        docFormat.value = payload.format || 'html'
        docTitle.value = payload.title || 'API 文档'
        viewCount.value = payload.view_count || 0
        docContent.value = payload.content
      } catch (parseErr) {
        // 既不是 HTML 也不是 JSON，直接当文本展示
        docFormat.value = 'markdown'
        docContent.value = resp
        docTitle.value = 'API 文档'
      }
    }
  } catch (err) {
    error.value = true
    const status = err.response?.status
    // transformResponse 阻止了 axios 自动解析，需手动解析 JSON 错误体
    let detail = err.response?.data
    if (typeof detail === 'string') {
      try {
        const parsed = JSON.parse(detail)
        detail = parsed.detail || parsed.message || detail
      } catch {
        // 非 JSON 字符串，保留原始内容
      }
    } else if (detail && typeof detail === 'object') {
      detail = detail.detail || detail.message || JSON.stringify(detail)
    }
    if (status === 404) {
      errorIcon.value = 'warning'
      errorTitle.value = '分享链接不存在'
      errorMessage.value = typeof detail === 'string' && detail ? detail : '该分享链接可能已被删除'
    } else if (status === 410) {
      errorIcon.value = 'info'
      errorTitle.value = '分享链接已过期'
      errorMessage.value = typeof detail === 'string' && detail ? detail : '请联系文档分享者获取新的链接'
    } else {
      errorIcon.value = 'error'
      errorTitle.value = '加载失败'
      errorMessage.value = typeof detail === 'string' && detail ? detail : (err.message || '未知错误')
    }
  } finally {
    loading.value = false
  }
}

const copyJson = () => {
  navigator.clipboard.writeText(formattedJson.value).then(() => {
    ElMessage.success('已复制到剪贴板')
  })
}

const copyMarkdown = () => {
  navigator.clipboard.writeText(docContent.value).then(() => {
    ElMessage.success('已复制到剪贴板')
  })
}

const downloadJson = () => {
  const blob = new Blob([formattedJson.value], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${docTitle.value || 'api-doc'}.json`
  a.click()
  URL.revokeObjectURL(url)
}

const downloadMarkdown = () => {
  const blob = new Blob([docContent.value], { type: 'text/markdown' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${docTitle.value || 'api-doc'}.md`
  a.click()
  URL.revokeObjectURL(url)
}

// ========== 初始化 ==========
onMounted(() => {
  loadSharedDoc()
})
</script>

<style scoped>
.shared-doc-container {
  min-height: 100vh;
  background: #f5f7fa;
  display: flex;
  flex-direction: column;
}

/* 加载状态 */
.loading-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  color: #909399;
}

.loading-state p {
  font-size: 14px;
}

/* 错误状态 */
.error-state {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* HTML 文档 */
.html-doc-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.html-iframe {
  flex: 1;
  border: none;
  width: 100%;
  min-height: 100vh;
  background: #fff;
}

/* JSON / Markdown 文档 */
.json-doc-wrapper,
.markdown-doc-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  height: 100vh;
}

.doc-meta-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 24px;
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
  flex-shrink: 0;
}

.meta-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.meta-left h2 {
  font-size: 18px;
  margin: 0;
  color: #303133;
}

.meta-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: #909399;
}

.json-viewer {
  flex: 1;
  overflow: auto;
  padding: 16px 24px;
  margin: 0;
  background: #1e1e1e;
  color: #d4d4d4;
  font-family: Consolas, Monaco, 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.6;
}

.json-viewer code {
  color: inherit;
  font-family: inherit;
}

.markdown-body {
  flex: 1;
  overflow-y: auto;
  padding: 24px 32px;
  background: #fff;
  line-height: 1.8;
  font-size: 14px;
  max-width: 960px;
  margin: 0 auto;
}

.markdown-body :deep(h1) {
  font-size: 24px;
  margin: 16px 0 12px;
  border-bottom: 2px solid #e4e7ed;
  padding-bottom: 8px;
}

.markdown-body :deep(h2) {
  font-size: 20px;
  margin: 14px 0 10px;
}

.markdown-body :deep(h3) {
  font-size: 16px;
  margin: 12px 0 8px;
}

.markdown-body :deep(h4) {
  font-size: 14px;
  margin: 10px 0 6px;
  border-left: 3px solid #409eff;
  padding-left: 8px;
}

.markdown-body :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 10px 0;
  font-size: 13px;
}

.markdown-body :deep(th),
.markdown-body :deep(td) {
  border: 1px solid #ebeef5;
  padding: 8px 10px;
  text-align: left;
}

.markdown-body :deep(th) {
  background: #f5f7fa;
  font-weight: 500;
}

.markdown-body :deep(pre) {
  background: #1e1e1e;
  color: #d4d4d4;
  padding: 14px;
  border-radius: 4px;
  overflow-x: auto;
  font-size: 13px;
}

.markdown-body :deep(code) {
  font-family: Consolas, Monaco, monospace;
}

.markdown-body :deep(p code),
.markdown-body :deep(li code) {
  background: #f5f7fa;
  padding: 1px 6px;
  border-radius: 3px;
  color: #e6a23c;
}
</style>
