<template>
  <el-drawer
    v-model="visible"
    :title="title"
    direction="rtl"
    size="540px"
    :with-header="true"
    :destroy-on-close="false"
    custom-class="help-drawer"
  >
    <div class="help-drawer-content">
      <el-alert
        v-if="intro"
        :title="introTitle || '使用说明'"
        :type="introType || 'info'"
        :closable="false"
        show-icon
        class="help-intro"
      >
        <template #default>
          <div v-html="renderRich(intro)"></div>
        </template>
      </el-alert>

      <div
        v-for="(section, idx) in sections"
        :key="idx"
        class="help-section"
      >
        <h3 class="help-section-title">
          <span class="section-icon">{{ section.icon || '📘' }}</span>
          <span>{{ section.heading }}</span>
        </h3>
        <div class="help-section-body">
          <p v-if="section.text" class="help-paragraph" v-html="renderRich(section.text)"></p>
          <ul v-if="section.items && section.items.length" class="help-list">
            <li
              v-for="(item, i) in section.items"
              :key="i"
              v-html="renderRich(item)"
            ></li>
          </ul>
          <ol v-if="section.steps && section.steps.length" class="help-steps">
            <li
              v-for="(step, i) in section.steps"
              :key="i"
              v-html="renderRich(step)"
            ></li>
          </ol>
          <div v-if="section.code" class="help-code">
            <pre>{{ section.code }}</pre>
          </div>
          <el-table
            v-if="section.table && section.table.rows"
            :data="section.table.rows"
            border
            size="small"
            class="help-table"
          >
            <el-table-column
              v-for="col in section.table.cols"
              :key="col.key"
              :prop="col.key"
              :label="col.label"
              :min-width="col.width || 100"
            />
          </el-table>
        </div>
      </div>

      <div v-if="!sections || sections.length === 0" class="help-empty">
        暂无使用说明
      </div>
    </div>
  </el-drawer>
</template>

<script setup>
import { computed } from 'vue'
import DOMPurify from 'dompurify'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  title: { type: String, default: '📖 使用说明' },
  intro: { type: String, default: '' },
  introTitle: { type: String, default: '' },
  introType: { type: String, default: 'info' },
  sections: { type: Array, default: () => [] }
})

const emit = defineEmits(['update:modelValue'])

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const renderRich = (text) => {
  if (!text || typeof text !== 'string') return ''
  // 先转义HTML，再进行格式替换，最后用DOMPurify消毒
  const escaped = text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
  const formatted = escaped
    .replace(/\n/g, '<br/>')
    .replace(/`([^`]+)`/g, '<code class="help-inline-code">$1</code>')
    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
  return DOMPurify.sanitize(formatted, { ALLOWED_TAGS: ['br', 'code', 'strong'], ALLOWED_ATTR: ['class'] })
}
</script>

<style scoped>
.help-drawer-content {
  padding: 0 8px 24px;
}

.help-intro {
  margin-bottom: 18px;
}

.help-intro :deep(.el-alert__content) {
  line-height: 1.7;
}

.help-section {
  margin-bottom: 22px;
  padding: 16px 18px;
  background: var(--tm-bg-soft, rgba(255, 255, 255, 0.02));
  border: 1px solid var(--tm-border-light, rgba(255, 255, 255, 0.08));
  border-radius: 10px;
  transition: border-color 0.2s;
}

.help-section:hover {
  border-color: rgba(var(--tm-color-primary-rgb, 0, 210, 255), 0.3);
}

.help-section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 12px 0;
  font-size: 15px;
  font-weight: 600;
  color: var(--tm-text-primary, #e0e0e0);
}

.section-icon {
  font-size: 18px;
  filter: drop-shadow(0 0 4px rgba(var(--tm-color-primary-rgb, 0, 210, 255), 0.4));
}

.help-section-body {
  color: var(--tm-text-secondary, #b0b0b0);
  font-size: 13.5px;
  line-height: 1.75;
}

.help-paragraph {
  margin: 0 0 10px 0;
}

.help-list,
.help-steps {
  margin: 8px 0;
  padding-left: 22px;
}

.help-list li,
.help-steps li {
  margin-bottom: 6px;
}

.help-list li::marker {
  color: var(--tm-color-primary, #00d2ff);
}

.help-steps li::marker {
  color: var(--tm-color-primary, #00d2ff);
  font-weight: 600;
}

.help-code {
  margin: 10px 0;
  background: rgba(0, 0, 0, 0.35);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 6px;
  overflow: hidden;
}

.help-code pre {
  margin: 0;
  padding: 12px 14px;
  color: #98c379;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 12.5px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-all;
}

.help-inline-code {
  display: inline-block;
  padding: 1px 6px;
  background: rgba(var(--tm-color-primary-rgb, 0, 210, 255), 0.12);
  color: var(--tm-color-primary, #00d2ff);
  border-radius: 4px;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 12.5px;
  margin: 0 2px;
}

.help-table {
  margin-top: 10px;
  border-radius: 6px;
  overflow: hidden;
}

.help-empty {
  text-align: center;
  padding: 60px 0;
  color: var(--tm-text-placeholder, #888);
  font-size: 14px;
}

:deep(.help-drawer) {
  background: var(--tm-bg-color, #1a1a2e) !important;
}

:deep(.help-drawer .el-drawer__header) {
  margin-bottom: 0;
  padding: 18px 20px;
  border-bottom: 1px solid var(--tm-border-light, rgba(255, 255, 255, 0.08));
  font-size: 16px;
  font-weight: 600;
  color: var(--tm-text-primary, #e0e0e0);
}

:deep(.help-drawer .el-drawer__body) {
  padding: 18px 20px;
  overflow-y: auto;
}
</style>
