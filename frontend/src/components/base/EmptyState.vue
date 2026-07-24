<template>
  <div class="tm-empty-state" role="status">
    <div class="tm-empty-state__icon" aria-hidden="true">
      <slot name="icon">
        <el-icon :size="40"><component :is="icon" /></el-icon>
      </slot>
    </div>
    <h3 class="tm-empty-state__title">{{ title }}</h3>
    <p v-if="description" class="tm-empty-state__desc">{{ description }}</p>
    <div v-if="$slots.action" class="tm-empty-state__action">
      <slot name="action" />
    </div>
  </div>
</template>

<script setup>
import { Box } from '@element-plus/icons-vue'

defineProps({
  title: { type: String, default: '暂无数据' },
  description: { type: String, default: '' },
  icon: { type: [Object, Function], default: () => Box }
})
</script>

<style scoped>
.tm-empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 220px;
  width: 100%;
  padding: 48px 24px;
  text-align: center;
}
.tm-empty-state__icon {
  display: grid;
  place-items: center;
  width: 72px;
  height: 72px;
  margin-bottom: 16px;
  border-radius: 16px;
  color: var(--tm-color-primary);
  background: rgba(var(--tm-color-primary-rgb), 0.12);
  border: 1px solid rgba(var(--tm-color-primary-rgb), 0.2);
}
.tm-empty-state__title {
  margin: 0;
  color: var(--tm-text-primary);
  font-size: 15px;
  font-weight: 600;
}
.tm-empty-state__desc {
  margin: 8px 0 0;
  max-width: 360px;
  color: var(--tm-text-secondary);
  font-size: 13px;
  line-height: 1.6;
}
.tm-empty-state__action {
  margin-top: 18px;
}
</style>
