﻿﻿<template>
  <div class="code-editor-container">
    <!-- 工具栏 -->
    <div class="editor-toolbar">
      <div class="toolbar-left">
        <el-select v-model="currentLanguage" @change="onLanguageChange" size="small" style="width: 120px;">
          <el-option label="Python" value="python" />
          <el-option label="SQL" value="sql" />
          <el-option label="Shell" value="shell" />
        </el-select>
      </div>
      <div class="toolbar-right">
        <el-button 
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
        <span class="output-title">运行结果</span>
        <el-button 
          link 
          size="small" 
          @click="showOutput = false"
        >
          关闭
        </el-button>
      </div>
      <div class="output-content" :class="{ 'error': outputResult?.returncode !== 0 }">
        <pre v-if="outputResult?.stdout">{{ outputResult.stdout }}</pre>
        <pre v-if="outputResult?.stderr" class="stderr">{{ outputResult.stderr }}</pre>
        <div v-if="!outputResult && running" class="loading">
          <el-icon class="is-loading" size="20"><Loading /></el-icon>
          <span>代码执行中...</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import { EditorState } from '@codemirror/state'
import { EditorView, keymap, lineNumbers, highlightActiveLineGutter, highlightSpecialChars, drawSelection, dropCursor, rectangularSelection, crosshairCursor, highlightActiveLine } from '@codemirror/view'
import { defaultKeymap } from '@codemirror/commands'
import { python } from '@codemirror/lang-python'
import { sql } from '@codemirror/lang-sql'
import { syntaxHighlighting, defaultHighlightStyle } from '@codemirror/language'
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
  }
})

const emit = defineEmits(['update:modelValue', 'run'])

const editorRef = ref(null)
const currentLanguage = ref(props.language)
const editorView = ref(null)
const running = ref(false)
const showOutput = ref(false)
const outputResult = ref(null)

// 语言配置
const languageExtensions = {}
try { languageExtensions.python = python() } catch(e) { console.warn('Python lang not loaded') }
try { languageExtensions.sql = sql() } catch(e) { console.warn('SQL lang not loaded') }
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
    languageExtensions[currentLanguage.value],
    EditorState.readOnly.of(props.readOnly),
    EditorView.updateListener.of(update => {
      if (update.docChanged) {
        const content = update.state.doc.toString()
        emit('update:modelValue', content)
      }
    })
  ].filter(Boolean)

  const startState = EditorState.create({
    doc: props.modelValue || props.template || getDefaultTemplate(currentLanguage.value),
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
    sql: '-- 在这里写你的SQL语句\nSELECT * FROM users WHERE age > 18;',
    shell: '# 在这里写你的Shell脚本\necho "Hello World!"'
  }
  return templates[lang] || ''
}

// 切换语言
const onLanguageChange = () => {
  if (editorView.value) {
    const currentContent = editorView.value.state.doc.toString()
    editorView.value.destroy()
    editorView.value = null
  }
  createEditor()
}

// 运行代码
const runCode = async () => {
  if (!editorView.value) return
  
  const code = editorView.value.state.doc.toString()
  if (!code.trim()) {
    ElMessage.warning('请先写代码再运行')
    return
  }
  
  running.value = true
  showOutput.value = true
  outputResult.value = null
  
  try {
    const res = await request.post('/sandbox/execute', {
      code,
      language: currentLanguage.value,
      timeout: 5
    })
    // FastAPI 返回 {success, data, message}，data 包含 {stdout, stderr, exit_code, ...}
    const result = res.data || res
    // 统一字段名：FastAPI 用 exit_code，前端用 returncode
    outputResult.value = {
      stdout: result.stdout || '',
      stderr: result.stderr || '',
      returncode: result.exit_code !== undefined ? result.exit_code : (result.returncode !== undefined ? result.returncode : 0)
    }

    if (res.success) {
      emit('run', { code, result: outputResult.value })
    }
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
    editorView.value.dispatch({
      changes: {
        from: 0,
        to: editorView.value.state.doc.length,
        insert: newVal
      }
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
  border-radius: 8px;
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

.output-container {
  border-top: 1px solid var(--tm-border-light, rgba(255,255,255,0.08));
}

.output-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 16px;
  background: var(--tm-card-bg, #1a1a2e);
  border-bottom: 1px solid var(--tm-border-light, rgba(255,255,255,0.08));
}

.output-title {
  font-weight: 500;
  color: var(--tm-text-primary, #cdd6f4);
  font-size: 14px;
}

.output-content {
  padding: 16px;
  background: #11111b;
  max-height: 200px;
  overflow-y: auto;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.6;
  color: #a6e3a1;
}

.output-content.error {
  background: rgba(243, 139, 168, 0.06);
}

.stderr {
  color: #f38ba8;
  margin-top: 8px;
}

.loading {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--tm-text-secondary);
}

pre {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
}
</style>
