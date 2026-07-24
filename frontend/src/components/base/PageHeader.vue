<template>
  <header class="tm-page-header" :class="{ compact }">
    <div class="tm-page-header__main">
      <div class="tm-page-header__titles">
        <p v-if="eyebrow" class="tm-page-header__eyebrow">{{ eyebrow }}</p>
        <h1 class="tm-page-header__title">{{ title }}</h1>
        <p v-if="description || $slots.description" class="tm-page-header__desc">
          <slot name="description">{{ description }}</slot>
        </p>
      </div>
      <div v-if="status || $slots.status" class="tm-page-header__status">
        <slot name="status">
          <span class="tm-status-pill" :class="statusTone">
            <i class="tm-status-pill__dot" aria-hidden="true" />
            {{ status }}
          </span>
        </slot>
      </div>
    </div>
    <div v-if="$slots.actions" class="tm-page-header__actions">
      <slot name="actions" />
    </div>
  </header>
</template>

<script setup>
defineProps({
  title: { type: String, required: true },
  description: { type: String, default: '' },
  eyebrow: { type: String, default: '' },
  status: { type: String, default: '' },
  statusTone: {
    type: String,
    default: 'neutral',
    validator: (v) => ['neutral', 'success', 'warning', 'danger', 'info', 'running'].includes(v)
  },
  compact: { type: Boolean, default: false }
})
</script>

<style scoped lang="scss">
.tm-page-header {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--tm-space-md, 16px);
  margin-bottom: var(--tm-space-lg, 24px);
  padding-bottom: var(--tm-space-md, 16px);
  border-bottom: 1px solid var(--border-subtle, var(--tm-border-light));
}

.tm-page-header.compact {
  margin-bottom: var(--tm-space-md, 16px);
  padding-bottom: var(--tm-space-sm, 8px);
}

.tm-page-header__main {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  gap: 12px 20px;
  min-width: 0;
  flex: 1;
}

.tm-page-header__eyebrow {
  margin: 0 0 6px;
  color: var(--tm-color-primary);
  font-size: var(--tm-font-xs, 11px);
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.tm-page-header__title {
  margin: 0;
  color: var(--tm-text-primary);
  font-size: var(--tm-font-xl, 20px);
  font-weight: 700;
  line-height: 1.3;
  letter-spacing: -0.01em;
}

.tm-page-header__desc {
  margin: 6px 0 0;
  max-width: 720px;
  color: var(--tm-text-secondary);
  font-size: var(--tm-font-sm, 12px);
  line-height: 1.6;
}

.tm-page-header__actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  flex: none;
}

.tm-status-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: 999px;
  border: 1px solid var(--border-subtle);
  background: var(--tm-bg-elevated);
  color: var(--tm-text-secondary);
  font-size: 12px;
  white-space: nowrap;
}

.tm-status-pill__dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: currentColor;
}

.tm-status-pill.success { color: var(--tm-color-success); border-color: color-mix(in srgb, var(--tm-color-success) 35%, transparent); }
.tm-status-pill.warning { color: var(--tm-color-warning); border-color: color-mix(in srgb, var(--tm-color-warning) 35%, transparent); }
.tm-status-pill.danger { color: var(--tm-color-danger); border-color: color-mix(in srgb, var(--tm-color-danger) 35%, transparent); }
.tm-status-pill.info { color: var(--tm-neon-cyan); border-color: color-mix(in srgb, var(--tm-neon-cyan) 35%, transparent); }
.tm-status-pill.running { color: var(--tm-color-primary); border-color: color-mix(in srgb, var(--tm-color-primary) 40%, transparent); }

@media (max-width: 768px) {
  .tm-page-header {
    flex-direction: column;
    align-items: stretch;
  }
  .tm-page-header__actions {
    width: 100%;
  }
  .tm-page-header__actions :deep(.el-button) {
    flex: 1 1 auto;
  }
}
</style>
