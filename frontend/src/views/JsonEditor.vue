<template>
  <div class="json-editor">
    <div class="editor-toolbar">
      <span class="toolbar-hint">支持 JSON 语法高亮</span>
      <div class="toolbar-actions">
        <el-button size="small" text @click="formatJson">格式化</el-button>
        <el-button size="small" text @click="compressJson">压缩</el-button>
      </div>
    </div>
    <div class="editor-wrapper">
      <textarea
        ref="textareaRef"
        v-model="content"
        class="editor-textarea"
        :placeholder="placeholder"
        spellcheck="false"
        @input="handleInput"
        @keydown.tab.prevent="handleTab"
      />
      <pre v-if="highlightedContent" class="editor-highlight" v-html="highlightedContent" />
    </div>
    <div class="editor-status">
      <span v-if="error" class="status-error">{{ error }}</span>
      <span v-else class="status-ok">✓ JSON 格式正确</span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'

const props = defineProps({
  modelValue: [String, Object],
  contentType: {
    type: String,
    default: 'application/json'
  },
  placeholder: {
    type: String,
    default: '输入 JSON 数据...'
  }
})

const emit = defineEmits(['update:modelValue'])

const textareaRef = ref(null)
const content = ref('')
const error = ref('')

// 同步外部值
watch(() => props.modelValue, (val) => {
  if (val !== content.value) {
    content.value = typeof val === 'object' ? JSON.stringify(val, null, 2) : val || ''
  }
}, { immediate: true })

// 处理输入
const handleInput = () => {
  error.value = ''
  try {
    if (content.value.trim()) {
      JSON.parse(content.value)
    }
  } catch (e) {
    error.value = 'JSON 格式错误'
  }
  emit('update:modelValue', content.value)
}

// 格式化
const formatJson = () => {
  try {
    const parsed = JSON.parse(content.value)
    content.value = JSON.stringify(parsed, null, 2)
    error.value = ''
  } catch (e) {
    error.value = '无法格式化：JSON 格式错误'
  }
}

// 压缩
const compressJson = () => {
  try {
    const parsed = JSON.parse(content.value)
    content.value = JSON.stringify(parsed)
    error.value = ''
  } catch (e) {
    error.value = '无法压缩：JSON 格式错误'
  }
}

// 处理 Tab 键
const handleTab = (e) => {
  const textarea = textareaRef.value
  const start = textarea.selectionStart
  const end = textarea.selectionEnd
  content.value = content.value.substring(0, start) + '  ' + content.value.substring(end)
  // 设置光标位置
  setTimeout(() => {
    textarea.selectionStart = textarea.selectionEnd = start + 2
  }, 0)
}

// 语法高亮
const highlightedContent = computed(() => {
  if (!content.value || props.contentType !== 'application/json') return ''
  try {
    const json = JSON.parse(content.value)
    return syntaxHighlight(JSON.stringify(json, null, 2))
  } catch {
    return syntaxHighlight(content.value)
  }
})

// JSON 语法高亮
const syntaxHighlight = (json) => {
  if (!json) return ''
  return json
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?)/g, (match) => {
      if (/:$/.test(match)) {
        // key
        return `<span class="json-key">${match}</span>`
      }
      // string value
      return `<span class="json-string">${match}</span>`
    })
    .replace(/\b(true|false)\b/g, '<span class="json-boolean">$1</span>')
    .replace(/\b(null)\b/g, '<span class="json-null">$1</span>')
    .replace(/\b(-?\d+\.?\d*([eE][+-]?\d+)?)\b/g, '<span class="json-number">$1</span>')
}

defineExpose({
  formatJson,
  compressJson,
  validate: () => {
    try {
      JSON.parse(content.value)
      return true
    } catch {
      return false
    }
  }
})
</script>

<style scoped>
.json-editor {
  display: flex;
  flex-direction: column;
  border: 1px solid var(--tm-border-color);
  border-radius: 4px;
  background: #1e1e1e;
}

.editor-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: #252526;
  border-bottom: 1px solid #3c3c3c;
}

.toolbar-hint {
  font-size: 12px;
  color: #858585;
}

.toolbar-actions {
  display: flex;
  gap: 8px;
}

.editor-wrapper {
  position: relative;
  min-height: 200px;
  max-height: 400px;
  overflow: auto;
}

.editor-textarea {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  min-height: 200px;
  padding: 12px;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 13px;
  line-height: 1.5;
  color: #d4d4d4;
  background: transparent;
  border: none;
  resize: none;
  outline: none;
  tab-size: 2;
  white-space: pre;
  overflow: auto;
  z-index: 2;
  caret-color: #d4d4d4;
}

.editor-highlight {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  min-height: 200px;
  padding: 12px;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 13px;
  line-height: 1.5;
  color: #d4d4d4;
  background: #1e1e1e;
  border: none;
  margin: 0;
  pointer-events: none;
  white-space: pre;
  overflow: hidden;
  z-index: 1;
}

.editor-status {
  padding: 6px 12px;
  background: #252526;
  border-top: 1px solid #3c3c3c;
  font-size: 12px;
}

.status-ok {
  color: #4ec9b0;
}

.status-error {
  color: #f14c4c;
}

/* 语法高亮颜色 */
:deep(.json-key) {
  color: #9cdcfe;
}

:deep(.json-string) {
  color: #ce9178;
}

:deep(.json-number) {
  color: #b5cea8;
}

:deep(.json-boolean) {
  color: #569cd6;
}

:deep(.json-null) {
  color: #569cd6;
}
</style>
