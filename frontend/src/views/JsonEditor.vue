<template>
  <div class="json-editor">
    <div class="editor-toolbar">
      <span class="toolbar-hint">鏀寔 JSON 璇硶楂樹寒</span>
      <div class="toolbar-actions">
        <el-button size="small" text @click="formatJson">鏍煎紡鍖</el-button>
        <el-button size="small" text @click="compressJson">鍘嬬缉</el-button>
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
      <span v-else class="status-ok">鉁?JSON 鏍煎紡姝ｇ‘</span>
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
    default: '杈撳叆 JSON 鏁版嵁...'
  }
})

const emit = defineEmits(['update:modelValue'])

const textareaRef = ref(null)
const content = ref('')
const error = ref('')

// 鍚屾澶栭儴鍊?
watch(() => props.modelValue, (val) => {
  if (val !== content.value) {
    content.value = typeof val === 'object' ? JSON.stringify(val, null, 2) : val || ''
    // 娓呴櫎閿欒鐘舵€佸苟閲嶆柊楠岃瘉
    error.value = ''
    try {
      if (content.value.trim()) {
        JSON.parse(content.value)
      }
    } catch (e) {
      error.value = 'JSON 鏍煎紡閿欒'
    }
  }
}, { immediate: true })

// 澶勭悊杈撳叆
const handleInput = () => {
  error.value = ''
  try {
    if (content.value.trim()) {
      JSON.parse(content.value)
    }
  } catch (e) {
    error.value = 'JSON 鏍煎紡閿欒'
  }
  emit('update:modelValue', content.value)
}

// 鏍煎紡鍖?
const formatJson = () => {
  try {
    const parsed = JSON.parse(content.value)
    content.value = JSON.stringify(parsed, null, 2)
    error.value = ''
  } catch (e) {
    error.value = '鏃犳硶鏍煎紡鍖栵細JSON 鏍煎紡閿欒'
  }
}

// 鍘嬬缉
const compressJson = () => {
  try {
    const parsed = JSON.parse(content.value)
    content.value = JSON.stringify(parsed)
    error.value = ''
  } catch (e) {
    error.value = '鏃犳硶鍘嬬缉锛欽SON 鏍煎紡閿欒'
  }
}

// 澶勭悊 Tab 閿?
const handleTab = (e) => {
  const textarea = textareaRef.value
  const start = textarea.selectionStart
  const end = textarea.selectionEnd
  content.value = content.value.substring(0, start) + '  ' + content.value.substring(end)
  // 璁剧疆鍏夋爣浣嶇疆
  setTimeout(() => {
    textarea.selectionStart = textarea.selectionEnd = start + 2
  }, 0)
}

// 璇硶楂樹寒
const highlightedContent = computed(() => {
  if (!content.value || props.contentType !== 'application/json') return ''
  try {
    const json = JSON.parse(content.value)
    return syntaxHighlight(JSON.stringify(json, null, 2))
  } catch {
    return syntaxHighlight(content.value)
  }
})

// JSON 璇硶楂樹寒
const syntaxHighlight = (json) => {
  if (!json) return ''
  // 鍏堣浆涔塇TML瀹炰綋
  const escaped = json
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
  // 浣跨敤鍗曚竴姝ｅ垯浜ゆ浛鍖归厤锛岄伩鍏嶅弻閲嶅寘瑁?
  return escaped.replace(
    /("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+\.?\d*([eE][+-]?\d+)?)/g,
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
  background: var(--tm-card-bg);
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
  background: var(--tm-card-bg);
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

/* 璇硶楂樹寒棰滆壊 */
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

