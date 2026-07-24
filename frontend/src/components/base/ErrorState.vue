<template>
  <div class="tm-error-state" role="alert">
    <div class="tm-error-state__icon" aria-hidden="true">
      <el-icon :size="36"><WarningFilled /></el-icon>
    </div>
    <h3 class="tm-error-state__title">{{ title }}</h3>
    <p class="tm-error-state__desc">{{ description || message }}</p>
    <div class="tm-error-state__action">
      <slot name="action">
        <el-button v-if="showRetry" type="primary" @click="$emit('retry')">重试</el-button>
      </slot>
    </div>
  </div>
</template>

<script setup>
import { WarningFilled } from '@element-plus/icons-vue'

defineProps({
  title: { type: String, default: '加载失败' },
  description: { type: String, default: '' },
  message: { type: String, default: '请检查网络后重试，或联系管理员。' },
  showRetry: { type: Boolean, default: true }
})
defineEmits(['retry'])
</script>

<style scoped>
.tm-error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 220px;
  padding: 40px 24px;
  text-align: center;
}
.tm-error-state__icon {
  color: var(--tm-color-danger);
  margin-bottom: 12px;
}
.tm-error-state__title {
  margin: 0;
  color: var(--tm-text-primary);
  font-size: 15px;
  font-weight: 600;
}
.tm-error-state__desc {
  margin: 8px 0 0;
  max-width: 420px;
  color: var(--tm-text-secondary);
  font-size: 13px;
  line-height: 1.6;
}
.tm-error-state__action {
  margin-top: 16px;
}
</style>
