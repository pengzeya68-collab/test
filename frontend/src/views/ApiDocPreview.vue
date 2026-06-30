<template>
  <div class="doc-preview-container">
    <!-- 顶部工具栏 -->
    <div class="doc-header">
      <div class="header-left">
        <el-icon class="back-icon" @click="goBack"><ArrowLeft /></el-icon>
        <h2>API 文档预览</h2>
        <el-tag type="success" size="small">文档即用例</el-tag>
      </div>
      <div class="header-right">
        <el-radio-group v-model="currentFormat" size="small" @change="handleFormatChange">
          <el-radio-button label="openapi">OpenAPI</el-radio-button>
          <el-radio-button label="markdown">Markdown</el-radio-button>
          <el-radio-button label="html">HTML</el-radio-button>
        </el-radio-group>
        <el-button type="primary" @click="generateDoc" :loading="loading">
          <el-icon><Refresh /></el-icon>
          生成文档
        </el-button>
        <el-button @click="handleExport" :disabled="!docContent">
          <el-icon><Download /></el-icon>
          导出
        </el-button>
        <el-button type="warning" @click="showShareDialog = true" :disabled="!selectedCaseIds.length">
          <el-icon><Share /></el-icon>
          分享
        </el-button>
      </div>
    </div>

    <div class="doc-body">
      <!-- 左侧：分组树（可勾选） -->
      <div class="doc-sidebar">
        <div class="sidebar-header">
          <span>选择接口</span>
          <el-button text size="small" @click="selectAllCases">全选</el-button>
          <el-button text size="small" @click="clearSelection">清空</el-button>
        </div>
        <div class="sidebar-stats" v-if="groupTree.length">
          <span>已选 {{ selectedCaseIds.length }} 个接口</span>
        </div>
        <el-tree
          ref="treeRef"
          :data="groupTree"
          :props="treeProps"
          node-key="key"
          show-checkbox
          default-expand-all
          :default-checked-keys="[]"
          class="case-tree"
          @check="handleCheckChange"
        >
          <template #default="{ node, data }">
            <span class="tree-node">
              <el-icon v-if="data.isGroup"><Folder /></el-icon>
              <el-icon v-else><Link /></el-icon>
              <span class="node-label" :title="node.label">{{ node.label }}</span>
              <el-tag
                v-if="data.method"
                :type="getMethodType(data.method)"
                size="small"
                class="method-tag"
              >
                {{ data.method.toUpperCase() }}
              </el-tag>
            </span>
          </template>
        </el-tree>
        <el-empty v-if="!groupTree.length && !loading" description="暂无用例数据" />
      </div>

      <!-- 右侧：预览区 -->
      <div class="doc-content">
        <!-- OpenAPI 预览 -->
        <div v-if="currentFormat === 'openapi'" class="preview-area">
          <div class="preview-toolbar">
            <span class="preview-title">OpenAPI 3.0 规范</span>
            <el-button text size="small" @click="copyJson">
              <el-icon><CopyDocument /></el-icon>
              复制 JSON
            </el-button>
          </div>
          <pre class="json-viewer" v-if="docContent"><code>{{ formattedJson }}</code></pre>
          <el-empty v-else description="点击「生成文档」按钮预览 OpenAPI 规范" />
        </div>

        <!-- Markdown 预览 -->
        <div v-else-if="currentFormat === 'markdown'" class="preview-area">
          <div class="preview-toolbar">
            <span class="preview-title">Markdown 文档</span>
            <el-button text size="small" @click="copyMarkdown">
              <el-icon><CopyDocument /></el-icon>
              复制
            </el-button>
          </div>
          <div
            v-if="docContent"
            class="markdown-body"
            v-html="renderedMarkdown"
          ></div>
          <el-empty v-else description="点击「生成文档」按钮预览 Markdown 文档" />
        </div>

        <!-- HTML 预览 -->
        <div v-else class="preview-area">
          <div class="preview-toolbar">
            <span class="preview-title">HTML 文档（可离线查看）</span>
            <el-button text size="small" @click="openInNewTab" :disabled="!docContent">
              <el-icon><FullScreen /></el-icon>
              新窗口打开
            </el-button>
          </div>
          <iframe
            v-if="docContent"
            :srcdoc="docContent"
            class="html-iframe"
            sandbox="allow-scripts"
          ></iframe>
          <el-empty v-else description="点击「生成文档」按钮预览 HTML 文档" />
        </div>
      </div>
    </div>

    <!-- 分享对话框 -->
    <el-dialog v-model="showShareDialog" title="生成分享链接" width="500px">
      <el-form :model="shareForm" label-width="100px">
        <el-form-item label="文档标题">
          <el-input v-model="shareForm.title" placeholder="TestMaster API 文档" />
        </el-form-item>
        <el-form-item label="文档格式">
          <el-select v-model="shareForm.format" style="width: 100%">
            <el-option label="HTML（在线浏览）" value="html" />
            <el-option label="OpenAPI JSON" value="openapi" />
            <el-option label="Markdown" value="markdown" />
          </el-select>
        </el-form-item>
        <el-form-item label="有效期">
          <el-select v-model="shareForm.expiresHours" style="width: 100%">
            <el-option label="1 小时" :value="1" />
            <el-option label="24 小时" :value="24" />
            <el-option label="7 天" :value="168" />
            <el-option label="30 天" :value="720" />
          </el-select>
        </el-form-item>
      </el-form>
      <div v-if="shareResult" class="share-result">
        <el-alert title="分享链接已生成" type="success" :closable="false" show-icon />
        <el-input :model-value="shareResult.fullUrl" readonly class="share-url-input">
          <template #append>
            <el-button @click="copyShareUrl">复制</el-button>
          </template>
        </el-input>
        <p class="share-info">
          接口数: {{ shareResult.case_count }} · 格式: {{ shareResult.format }} ·
          有效期: {{ shareResult.expires_hours }} 小时
        </p>
      </div>
      <template #footer>
        <el-button @click="showShareDialog = false">关闭</el-button>
        <el-button type="primary" @click="handleShare" :loading="sharing" v-if="!shareResult">
          生成链接
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  ArrowLeft, Refresh, Share, Download, Folder, Link,
  CopyDocument, FullScreen,
} from '@element-plus/icons-vue'
import { autoTestRequest } from '@/utils/request'
import { marked } from 'marked'
import DOMPurify from 'dompurify'

const router = useRouter()

// ========== 状态 ==========
const loading = ref(false)
const sharing = ref(false)
const currentFormat = ref('openapi')
const docContent = ref(null) // openapi: dict, markdown: str, html: str
const groupTree = ref([])
const selectedCaseIds = ref([])
const treeRef = ref(null)
const showShareDialog = ref(false)
const shareResult = ref(null)
const shareForm = ref({
  title: 'TestMaster API 文档',
  format: 'html',
  expiresHours: 24,
})

const treeProps = {
  children: 'children',
  label: 'label',
}

// ========== 计算属性 ==========
const formattedJson = computed(() => {
  if (!docContent.value || currentFormat.value !== 'openapi') return ''
  try {
    return JSON.stringify(docContent.value, null, 2)
  } catch {
    return String(docContent.value)
  }
})

const renderedMarkdown = computed(() => {
  if (!docContent.value || currentFormat.value !== 'markdown') return ''
  try {
    const html = marked(docContent.value)
    return DOMPurify.sanitize(html)
  } catch {
    return docContent.value
  }
})

// ========== 方法 ==========
const getMethodType = (method) => {
  const map = { GET: 'success', POST: 'primary', PUT: 'warning', DELETE: 'danger', PATCH: 'info' }
  return map[(method || '').toUpperCase()] || 'info'
}

const goBack = () => router.push('/auto-test')

// 构建分组+用例的合并树
const buildCombinedTree = (groups, cases) => {
  // 将用例按 group_id 分组（null/undefined 归入未分组）
  const casesByGroup = {}
  for (const c of cases) {
    const gid = c.group_id ?? null
    if (!casesByGroup[gid]) casesByGroup[gid] = []
    casesByGroup[gid].push(c)
  }

  // 递归构建树
  const buildNode = (group) => {
    const children = []
    // 子分组
    for (const child of (group.children || [])) {
      children.push(buildNode(child))
    }
    // 该分组下的用例
    for (const c of (casesByGroup[group.id] || [])) {
      children.push({
        key: `case-${c.id}`,
        label: c.name || c.url,
        isCase: true,
        caseId: c.id,
        method: c.method,
      })
    }
    return {
      key: `group-${group.id}`,
      label: group.name,
      isGroup: true,
      groupId: group.id,
      children,
    }
  }

  const tree = groups.map(buildNode)

  // 没有分组的用例归入"未分组"虚拟节点
  const ungroupedCases = casesByGroup[null] || []
  if (ungroupedCases.length) {
    tree.push({
      key: 'group-ungrouped',
      label: '未分组',
      isGroup: true,
      groupId: null,
      children: ungroupedCases.map((c) => ({
        key: `case-${c.id}`,
        label: c.name || c.url,
        isCase: true,
        caseId: c.id,
        method: c.method,
      })),
    })
  }

  return tree
}

// 加载分组树和用例列表
const loadData = async () => {
  loading.value = true
  try {
    const [treeResp, casesResp] = await Promise.all([
      autoTestRequest.get('/auto-test/groups/tree'),
      autoTestRequest.get('/auto-test/cases/all'),
    ])
    groupTree.value = buildCombinedTree(treeResp, casesResp)
  } catch (error) {
    ElMessage.error('加载数据失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    loading.value = false
  }
}

// 勾选变更：收集选中的 caseId
const handleCheckChange = () => {
  const tree = treeRef.value
  if (!tree) return
  const checked = tree.getCheckedNodes()
  selectedCaseIds.value = checked
    .filter((n) => n.isCase)
    .map((n) => n.caseId)
}

// 全选/清空
const selectAllCases = () => {
  const tree = treeRef.value
  if (!tree) return
  const allKeys = []
  const collect = (nodes) => {
    for (const n of nodes) {
      if (n.isCase) allKeys.push(n.key)
      if (n.children) collect(n.children)
    }
  }
  collect(groupTree.value)
  tree.setCheckedKeys(allKeys)
  handleCheckChange()
}

const clearSelection = () => {
  const tree = treeRef.value
  if (!tree) return
  tree.setCheckedKeys([])
  selectedCaseIds.value = []
}

// 生成文档
const generateDoc = async () => {
  if (!selectedCaseIds.value.length) {
    ElMessage.warning('请先在左侧选择要生成文档的接口')
    return
  }
  loading.value = true
  docContent.value = null
  try {
    const params = { case_ids: selectedCaseIds.value.join(',') }
    const fmt = currentFormat.value
    if (fmt === 'openapi') {
      const resp = await autoTestRequest.get('/auto-test/api-docs/openapi', { params })
      docContent.value = resp
    } else if (fmt === 'markdown') {
      const resp = await autoTestRequest.get('/auto-test/api-docs/markdown', {
        params,
        responseType: 'text',
        transformResponse: [(data) => data],
      })
      docContent.value = resp
    } else {
      const resp = await autoTestRequest.get('/auto-test/api-docs/html', {
        params,
        responseType: 'text',
        transformResponse: [(data) => data],
      })
      docContent.value = resp
    }
    ElMessage.success('文档生成成功')
  } catch (error) {
    ElMessage.error('文档生成失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    loading.value = false
  }
}

// 格式切换时重新生成文档
const handleFormatChange = () => {
  if (selectedCaseIds.value.length) {
    generateDoc()
  } else {
    // 没有选中用例时清空旧内容，避免不同格式间数据类型不匹配导致渲染异常
    docContent.value = null
  }
}

// 导出文档
const handleExport = () => {
  if (!docContent.value) return
  let content = ''
  let filename = ''
  let mime = ''
  if (currentFormat.value === 'openapi') {
    content = JSON.stringify(docContent.value, null, 2)
    filename = 'api-doc-openapi.json'
    mime = 'application/json'
  } else if (currentFormat.value === 'markdown') {
    content = docContent.value
    filename = 'api-doc.md'
    mime = 'text/markdown'
  } else {
    content = docContent.value
    filename = 'api-doc.html'
    mime = 'text/html'
  }
  const blob = new Blob([content], { type: mime })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
  ElMessage.success('文档已导出')
}

// 复制 JSON
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

// 新窗口打开 HTML
const openInNewTab = () => {
  if (!docContent.value) return
  const blob = new Blob([docContent.value], { type: 'text/html' })
  const url = URL.createObjectURL(blob)
  window.open(url, '_blank')
  setTimeout(() => URL.revokeObjectURL(url), 5000)
}

// 分享
const handleShare = async () => {
  if (!selectedCaseIds.value.length) {
    ElMessage.warning('请先选择接口')
    return
  }
  sharing.value = true
  shareResult.value = null
  try {
    const resp = await autoTestRequest.post('/auto-test/api-docs/share', {
      case_ids: selectedCaseIds.value,
      expires_hours: shareForm.value.expiresHours,
      format: shareForm.value.format,
      title: shareForm.value.title,
    })
    shareResult.value = {
      ...resp,
      fullUrl: window.location.origin + resp.url,
    }
    ElMessage.success('分享链接已生成')
  } catch (error) {
    ElMessage.error('分享失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    sharing.value = false
  }
}

const copyShareUrl = () => {
  if (!shareResult.value) return
  navigator.clipboard.writeText(shareResult.value.fullUrl).then(() => {
    ElMessage.success('链接已复制')
  })
}

// ========== 初始化 ==========
onMounted(() => {
  loadData()
})

// 分享对话框关闭时重置
watch(showShareDialog, (val) => {
  if (!val) {
    shareResult.value = null
  }
})
</script>

<style scoped>
.doc-preview-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f5f7fa;
}

.doc-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 20px;
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
  flex-shrink: 0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.header-left h2 {
  font-size: 18px;
  margin: 0;
  color: #303133;
}

.back-icon {
  cursor: pointer;
  font-size: 20px;
  color: #606266;
}

.back-icon:hover {
  color: #409eff;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.doc-body {
  display: flex;
  flex: 1;
  overflow: hidden;
}

/* 左侧分组树 */
.doc-sidebar {
  width: 300px;
  background: #fff;
  border-right: 1px solid #e4e7ed;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.sidebar-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  border-bottom: 1px solid #ebeef5;
  font-size: 14px;
  font-weight: 500;
  color: #303133;
}

.sidebar-header span:first-child {
  flex: 1;
}

.sidebar-stats {
  padding: 6px 16px;
  font-size: 12px;
  color: #909399;
  border-bottom: 1px solid #f0f0f0;
}

.case-tree {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.tree-node {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
}

.node-label {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.method-tag {
  flex-shrink: 0;
  transform: scale(0.85);
}

/* 右侧预览区 */
.doc-content {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.preview-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.preview-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 20px;
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
  flex-shrink: 0;
}

.preview-title {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
}

.json-viewer {
  flex: 1;
  overflow: auto;
  padding: 16px 20px;
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

.html-iframe {
  flex: 1;
  border: none;
  width: 100%;
  background: #fff;
}

/* 分享结果 */
.share-result {
  margin-top: 16px;
}

.share-url-input {
  margin-top: 12px;
}

.share-info {
  margin-top: 8px;
  font-size: 12px;
  color: #909399;
}
</style>
