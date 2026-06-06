<template>
  <div class="code-editor-container">
    <!-- 工具栏 -->
    <div class="editor-toolbar">
      <div class="toolbar-left">
        <span class="lang-tag">{{ langLabel }}</span>
      </div>
      <div class="toolbar-right">
        <el-button 
          v-if="!hideRun"
          type="primary" 
          size="small" 
          @click="runCode" 
          :loading="running"
        >
          <el-icon><VideoPlay /></el-icon>
          运行代码
        </el-button>
        <el-button 
          size="small" 
          @click="resetCode"
        >
          <el-icon><Refresh /></el-icon>
          重置
        </el-button>
      </div>
    </div>
    
    <!-- 编辑器区域 -->
    <div ref="editorRef" class="code-editor"></div>
    
    <!-- 输出区域 -->
    <div class="output-container" v-if="showOutput">
      <div class="output-header">
        <div class="output-status">
          <span class="status-indicator" :class="outputResult?.returncode === 0 ? 'status-ok' : 'status-err'"></span>
          <span class="output-title">运行结果</span>
          <span v-if="outputResult?.returncode === 0" class="status-badge badge-ok">成功</span>
          <span v-else-if="outputResult" class="status-badge badge-err">失败</span>
        </div>
        <el-button 
          link 
          size="small" 
          @click="showOutput = false"
        >
          关闭
        </el-button>
      </div>
      <div class="output-content" :class="{ 'error': outputResult?.returncode !== 0 }">
        <!-- 加载中 -->
        <div v-if="!outputResult && running" class="loading">
          <el-icon class="is-loading" size="20"><Loading /></el-icon>
          <span>代码执行中...</span>
        </div>
        <!-- 有输出 -->
        <template v-else-if="outputResult">
          <pre v-if="outputResult.stdout" class="stdout">{{ outputResult.stdout }}</pre>
          <pre v-if="outputResult.stderr" class="stderr">{{ outputResult.stderr }}</pre>
          <!-- 无输出提示 -->
          <div v-if="!outputResult.stdout && !outputResult.stderr" class="no-output">
            <div class="no-output-main">
              <span class="no-output-check">&#x2713;</span>
              代码执行成功，但没有产生输出
            </div>
            <div class="no-output-hint">
              函数定义不会自动输出结果。你可以：<br>
              &bull; 在代码中添加 <code>print()</code> 来查看运行结果<br>
              &bull; 点击下方「提交判题」按钮验证代码正确性
            </div>
          </div>
        </template>
      </div>
      <!-- 操作按钮 -->
      <div class="output-actions" v-if="outputResult && !running">
        <button class="action-btn submit-action" @click="$emit('submit')" :disabled="submitting">
          <span v-if="submitting" class="btn-spinner"></span>
          <span v-else>&#x1f4dd;</span>
          {{ submitting ? '判题中...' : '提交判题' }}
        </button>
        <button class="action-btn ai-action" @click="$emit('aiEvaluate')" :disabled="aiEvaluating || outputResult?.returncode !== 0">
          <span v-if="aiEvaluating" class="btn-spinner"></span>
          <span v-else>&#x1f916;</span>
          {{ aiEvaluating ? 'AI评估中...' : 'AI点评' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch, computed } from 'vue'
import { EditorState } from '@codemirror/state'
import { EditorView, keymap, lineNumbers, highlightActiveLineGutter, highlightSpecialChars, drawSelection, dropCursor, rectangularSelection, crosshairCursor, highlightActiveLine } from '@codemirror/view'
import { defaultKeymap } from '@codemirror/commands'
import { python } from '@codemirror/lang-python'
import { sql } from '@codemirror/lang-sql'
import { syntaxHighlighting, defaultHighlightStyle } from '@codemirror/language'

let _jsExtension = null
try {
  const jsMod = await import('@codemirror/lang-javascript')
  _jsExtension = jsMod.javascript()
} catch(e) { console.warn('JavaScript lang not loaded, install @codemirror/lang-javascript') }
import { VideoPlay, Refresh, Loading } from '@element-plus/icons-vue'
import request from '@/utils/request'
import { ElMessage } from 'element-plus'

const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  },
  language: {
    type: String,
    default: 'python'
  },
  readOnly: {
    type: Boolean,
    default: false
  },
  template: {
    type: String,
    default: ''
  },
  setupSql: {
    type: String,
    default: ''
  },
  hideRun: {
    type: Boolean,
    default: false
  },
  submitting: {
    type: Boolean,
    default: false
  },
  aiEvaluating: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue', 'run', 'submit', 'aiEvaluate'])

const editorRef = ref(null)
const currentLanguage = ref(props.language)
const editorView = ref(null)
const running = ref(false)
const showOutput = ref(false)
const outputResult = ref(null)

const langLabel = computed(() => {
  const map = { python: 'Python', sql: 'SQL', shell: 'Shell', javascript: 'JavaScript', '中文': 'Python' }
  return map[currentLanguage.value] || 'Python'
})

// 语言配置
const languageExtensions = {}
try { languageExtensions.python = python() } catch(e) { console.warn('Python lang not loaded') }
try { languageExtensions.sql = sql() } catch(e) { console.warn('SQL lang not loaded') }
if (_jsExtension) { languageExtensions.javascript = _jsExtension }
// shell 使用 Python 语法高亮作为回退，但保持 shell 标识
languageExtensions.shell = languageExtensions.python

// 创建编辑器
const createEditor = () => {
  if (!editorRef.value) return
  
  const extList = [
    lineNumbers(),
    highlightActiveLineGutter(),
    highlightSpecialChars(),
    drawSelection(),
    dropCursor(),
    rectangularSelection(),
    crosshairCursor(),
    highlightActiveLine(),
    syntaxHighlighting(defaultHighlightStyle, { fallback: true }),
    keymap.of([
      ...defaultKeymap,
      {
        key: 'Ctrl-Enter',
        run: () => {
          runCode()
          return true
        }
      }
    ]),
    languageExtensions[currentLanguage.value] || languageExtensions.python,
    EditorState.readOnly.of(props.readOnly),
    EditorView.updateListener.of(update => {
      if (update.docChanged) {
        const content = update.state.doc.toString()
        emit('update:modelValue', content)
      }
    })
  ].filter(Boolean)

  const startDoc = props.modelValue || props.template || getDefaultTemplate(currentLanguage.value)
  const startState = EditorState.create({
    doc: startDoc,
    extensions: extList
  })

  editorView.value = new EditorView({
    state: startState,
    parent: editorRef.value
  })
}

// 获取默认代码模板
const getDefaultTemplate = (lang) => {
  const templates = {
    python: '# 在这里写你的Python代码\nprint("Hello World!")',
    sql: '-- 在这里写你的SQL查询语句\nSELECT * FROM users LIMIT 10;',
    shell: '# 在这里写你的Shell脚本\necho "Hello World!"',
    javascript: '// 在这里写你的JavaScript脚本\n// 可用 API: pm.environment.get/set, pm.response.json(), pm.test()\nconsole.log("Hello from TestMaster!");'
  }
  return templates[lang] || ''
}

const onLanguageChange = () => {
  if (editorView.value) {
    editorView.value.destroy()
    editorView.value = null
  }
  createEditor()
}

// 运行代码
const runCode = async () => {
  if (!editorView.value || running.value) return
  
  const code = editorView.value.state.doc.toString()
  if (!code.trim()) {
    ElMessage.warning('请先写代码再运行')
    return
  }
  
  running.value = true
  showOutput.value = true
  outputResult.value = null
  
  try {
    const payload = {
      code,
      language: currentLanguage.value,
      timeout: 5
    }
    if (currentLanguage.value === 'sql' && props.setupSql) {
      payload.setup_sql = props.setupSql
    }
    const res = await request.post('/sandbox/execute', payload)
    const result = res.data || res
    outputResult.value = {
      stdout: result.stdout || '',
      stderr: result.stderr || '',
      returncode: result.exit_code !== undefined ? result.exit_code : (result.returncode !== undefined ? result.returncode : 0)
    }

    emit('run', { 
      code, 
      result: {
        ...outputResult.value,
        success: outputResult.value.returncode === 0,
        execution_time_ms: result.execution_time_ms
      }
    })
  } catch (error) {
    console.error('代码执行失败:', error)
    ElMessage.error('代码执行失败')
  } finally {
    running.value = false
  }
}

// 重置代码
const resetCode = () => {
  if (!editorView.value) return
  
  const template = props.template || getDefaultTemplate(currentLanguage.value)
  editorView.value.dispatch({
    changes: {
      from: 0,
      to: editorView.value.state.doc.length,
      insert: template
    }
  })
  emit('update:modelValue', template)
}

// 监听外部modelValue变化
watch(() => props.modelValue, (newVal) => {
  if (editorView.value && newVal !== editorView.value.state.doc.toString()) {
    // 保存当前光标位置
    const pos = Math.min(editorView.value.state.selection.main.head, newVal?.length || 0)
    editorView.value.dispatch({
      changes: {
        from: 0,
        to: editorView.value.state.doc.length,
        insert: newVal
      },
      selection: { anchor: pos }
    })
  }
})

// 监听语言变化
watch(() => props.language, (newVal) => {
  if (newVal !== currentLanguage.value) {
    currentLanguage.value = newVal
    onLanguageChange()
  }
})

onMounted(() => {
  createEditor()
})

onBeforeUnmount(() => {
  if (editorView.value) {
    editorView.value.destroy()
  }
})
</script>

<style scoped>
.code-editor-container {
  border: 1px solid var(--tm-border-light, rgba(255,255,255,0.08));
  border-radius: 12px;
  overflow: hidden;
  background: #1e1e2e;
}

.editor-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: var(--tm-card-bg, #1a1a2e);
  border-bottom: 1px solid var(--tm-border-light, rgba(255,255,255,0.08));
}

.toolbar-left, .toolbar-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.lang-tag {
  padding: 4px 12px;
  background: rgba(137, 180, 250, 0.12);
  border: 1px solid rgba(137, 180, 250, 0.2);
  border-radius: 4px;
  color: #89b4fa;
  font-size: 13px;
  font-weight: 600;
}

.code-editor {
  min-height: 300px;
  font-size: 14px;
}

:deep(.cm-editor) {
  height: 100%;
  min-height: 300px;
  background: #1e1e2e;
  color: #cdd6f4;
}

:deep(.cm-scroller) {
  overflow: auto;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
}

:deep(.cm-gutters) {
  background: #181825;
  border-right: 1px solid rgba(255,255,255,0.06);
  color: #6c7086;
}

:deep(.cm-activeLineGutter) {
  background: rgba(137, 180, 250, 0.08);
  color: #89b4fa;
}

:deep(.cm-activeLine) {
  background: rgba(137, 180, 250, 0.06);
}

:deep(.cm-cursor) {
  border-left-color: #89b4fa;
}

:deep(.cm-selectionBackground) {
  background: rgba(137, 180, 250, 0.18) !important;
}

:deep(.cm-focused .cm-selectionBackground) {
  background: rgba(137, 180, 250, 0.25) !important;
}

:deep(.cm-matchingBracket) {
  background: rgba(166, 227, 161, 0.2);
  outline: 1px solid rgba(166, 227, 161, 0.4);
}

:deep(.cm-content) {
  caret-color: #89b4fa;
}

/* ===== 输出区域 ===== */
.output-container {
  border-top: 1px solid var(--tm-border-light, rgba(255,255,255,0.08));
}

.output-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 16px;
  background: var(--tm-card-bg, #1a1a2e);
  border-bottom: 1px solid var(--tm-border-light, rgba(255,255,255,0.08));
}

.output-status {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.status-indicator.status-ok {
  background: #4ade80;
  box-shadow: 0 0 6px rgba(74, 222, 128, 0.5);
}

.status-indicator.status-err {
  background: #f87171;
  box-shadow: 0 0 6px rgba(248, 113, 113, 0.5);
}

.output-title {
  font-weight: 600;
  color: var(--tm-text-primary, #cdd6f4);
  font-size: 14px;
}

.status-badge {
  font-size: 11px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 4px;
}

.badge-ok {
  background: rgba(74, 222, 128, 0.12);
  color: #4ade80;
}

.badge-err {
  background: rgba(248, 113, 113, 0.12);
  color: #f87171;
}

.output-content {
  padding: 16px;
  background: #11111b;
  max-height: 250px;
  overflow-y: auto;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.6;
  color: #a6e3a1;
}

.output-content.error {
  background: rgba(243, 139, 168, 0.04);
}

.stdout {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.stderr {
  color: #f38ba8;
  margin-top: 8px;
  margin-bottom: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.loading {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--tm-text-secondary);
}

/* 无输出提示 */
.no-output {
  text-align: left;
}

.no-output-main {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #4ade80;
  margin-bottom: 10px;
}

.no-output-check {
  font-size: 18px;
  font-weight: 700;
}

.no-output-hint {
  font-size: 12px;
  color: var(--tm-text-secondary, #6c7086);
  line-height: 1.8;
  padding: 10px 14px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 6px;
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.no-output-hint code {
  background: rgba(137, 180, 250, 0.12);
  color: #89b4fa;
  padding: 1px 5px;
  border-radius: 3px;
  font-size: 12px;
  font-family: 'Consolas', 'Monaco', monospace;
}

/* 操作按钮 */
.output-actions {
  display: flex;
  gap: 10px;
  padding: 10px 16px;
  background: var(--tm-card-bg, #1a1a2e);
  border-top: 1px solid var(--tm-border-light, rgba(255,255,255,0.08));
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 7px 16px;
  border-radius: 6px;
  border: 1px solid;
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  transition: all 0.2s;
  background: transparent;
}

.action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.submit-action {
  border-color: rgba(139, 92, 246, 0.3);
  color: #a78bfa;
  background: rgba(139, 92, 246, 0.1);
}

.submit-action:hover:not(:disabled) {
  background: rgba(139, 92, 246, 0.2);
  border-color: rgba(139, 92, 246, 0.5);
  box-shadow: 0 0 10px rgba(139, 92, 246, 0.15);
}

.ai-action {
  border-color: rgba(236, 72, 153, 0.3);
  color: var(--tm-color-primary, #ec4899);
  background: rgba(236, 72, 153, 0.1);
}

.ai-action:hover:not(:disabled) {
  background: rgba(236, 72, 153, 0.2);
  border-color: rgba(236, 72, 153, 0.5);
  box-shadow: 0 0 10px rgba(236, 72, 153, 0.15);
}

.btn-spinner {
  display: inline-block;
  width: 14px;
  height: 14px;
  border: 2px solid rgba(255, 255, 255, 0.2);
  border-top-color: currentColor;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
