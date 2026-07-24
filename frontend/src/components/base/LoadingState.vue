<template>
  <div class="tm-loading-state" role="status" aria-live="polite">
    <el-icon class="tm-loading-state__spin" :size="28"><Loading /></el-icon>
    <p class="tm-loading-state__text">{{ text }}</p>
  </div>
</template>

<script setup>
import { Loading } from '@element-plus/icons-vue'

defineProps({
  text: { type: String, default: '加载中…' }
})
</script>

<style scoped>
.tm-loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  min-height: 180px;
  padding: 32px;
  color: var(--tm-text-secondary);
}
.tm-loading-state__spin {
  color: var(--tm-color-primary);
  animation: tm-spin 0.9s linear infinite;
}
.tm-loading-state__text {
  margin: 0;
  font-size: 13px;
}
@keyframes tm-spin {
  to { transform: rotate(360deg); }
}
@media (prefers-reduced-motion: reduce) {
  .tm-loading-state__spin { animation: none; }
}
</style>
