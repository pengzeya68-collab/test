<template>
  <span class="tm-status-badge" :class="tone" :title="label">
    <i v-if="dot" class="tm-status-badge__dot" aria-hidden="true" />
    <slot>{{ label }}</slot>
  </span>
</template>

<script setup>
defineProps({
  label: { type: String, default: '' },
  tone: {
    type: String,
    default: 'neutral',
    validator: (v) => ['neutral', 'success', 'warning', 'danger', 'info', 'primary', 'running'].includes(v)
  },
  dot: { type: Boolean, default: true }
})
</script>

<style scoped>
.tm-status-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 24px;
  padding: 0 10px;
  border-radius: 999px;
  border: 1px solid var(--border-subtle);
  background: var(--tm-bg-elevated);
  color: var(--tm-text-secondary);
  font-size: 12px;
  font-weight: 500;
  line-height: 1;
  white-space: nowrap;
}
.tm-status-badge__dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
  flex: none;
}
.tm-status-badge.success { color: var(--tm-color-success); background: color-mix(in srgb, var(--tm-color-success) 12%, transparent); border-color: color-mix(in srgb, var(--tm-color-success) 30%, transparent); }
.tm-status-badge.warning { color: var(--tm-color-warning); background: color-mix(in srgb, var(--tm-color-warning) 12%, transparent); border-color: color-mix(in srgb, var(--tm-color-warning) 30%, transparent); }
.tm-status-badge.danger { color: var(--tm-color-danger); background: color-mix(in srgb, var(--tm-color-danger) 12%, transparent); border-color: color-mix(in srgb, var(--tm-color-danger) 30%, transparent); }
.tm-status-badge.info { color: var(--tm-neon-cyan); background: color-mix(in srgb, var(--tm-neon-cyan) 12%, transparent); border-color: color-mix(in srgb, var(--tm-neon-cyan) 30%, transparent); }
.tm-status-badge.primary,
.tm-status-badge.running { color: var(--tm-color-primary); background: rgba(var(--tm-color-primary-rgb), 0.12); border-color: rgba(var(--tm-color-primary-rgb), 0.3); }
</style>
