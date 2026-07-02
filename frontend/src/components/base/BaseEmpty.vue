<template>
  <div class="base-empty">
    <div class="empty-orbit">
      <svg width="120" height="120" viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <linearGradient :id="gradId" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="var(--tm-color-primary)" />
            <stop offset="50%" stop-color="var(--tm-color-primary-dark)" />
            <stop offset="100%" stop-color="#00f2fe" />
          </linearGradient>
          <filter :id="glowId" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="3" result="b" />
            <feMerge>
              <feMergeNode in="b" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>
        <circle cx="60" cy="60" r="50" fill="none" :stroke="`url(#${gradId})`" stroke-width="2" stroke-dasharray="6 8" opacity="0.5" class="orbit-dashed" />
        <circle cx="60" cy="60" r="38" fill="none" :stroke="`url(#${gradId})`" stroke-width="1.5" opacity="0.7" class="orbit-inner" />
        <g :filter="`url(#${glowId})`">
          <circle cx="60" cy="60" r="14" fill="none" :stroke="`url(#${gradId})`" stroke-width="2" class="orbit-core" />
          <circle cx="60" cy="60" r="6" fill="none" :stroke="`url(#${gradId})`" stroke-width="1.5" opacity="0.8" />
        </g>
        <circle cx="60" cy="10" r="2.5" fill="var(--tm-color-primary)" class="orbit-dot dot-top" />
        <circle cx="110" cy="60" r="2" fill="var(--tm-color-primary-dark)" class="orbit-dot dot-right" />
        <circle cx="60" cy="110" r="2" fill="#00f2fe" class="orbit-dot dot-bottom" />
        <circle cx="10" cy="60" r="1.5" fill="var(--tm-color-primary)" class="orbit-dot dot-left" />
      </svg>
    </div>
    <div class="empty-title">{{ title }}</div>
    <div v-if="description" class="empty-desc">{{ description }}</div>
    <div v-if="$slots.action" class="empty-action">
      <slot name="action" />
    </div>
  </div>
</template>

<script setup>
import { useId } from 'vue'

defineProps({
  title: { type: String, default: '暂无数据' },
  description: { type: String, default: '' }
})

const gradId = `tm-grad-${useId().replace(/[^a-zA-Z0-9]/g, '')}`
const glowId = `tm-glow-${useId().replace(/[^a-zA-Z0-9]/g, '')}`
</script>

<style scoped>
.base-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 64px 24px;
  text-align: center;
  min-height: 280px;
  width: 100%;
}

.empty-orbit {
  animation: empty-float 6s ease-in-out infinite;
}

.orbit-dashed {
  animation: empty-rotate 30s linear infinite;
  transform-origin: 60px 60px;
}

.orbit-inner {
  animation: empty-rotate-reverse 25s linear infinite;
  transform-origin: 60px 60px;
}

.orbit-core {
  animation: empty-pulse 2.5s ease-in-out infinite;
  transform-origin: 60px 60px;
}

.orbit-dot {
  animation: empty-twinkle 3s ease-in-out infinite;
}
.dot-top { animation-delay: 0s; }
.dot-right { animation-delay: 0.75s; }
.dot-bottom { animation-delay: 1.5s; }
.dot-left { animation-delay: 2.25s; }

@keyframes empty-float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-8px); }
}
@keyframes empty-rotate {
  to { transform: rotate(360deg); }
}
@keyframes empty-rotate-reverse {
  to { transform: rotate(-360deg); }
}
@keyframes empty-pulse {
  0%, 100% { opacity: 0.7; transform: scale(1); }
  50% { opacity: 1; transform: scale(1.08); }
}
@keyframes empty-twinkle {
  0%, 100% { opacity: 0.3; }
  50% { opacity: 1; }
}

.empty-title {
  margin-top: 24px;
  font-size: 16px;
  font-weight: 600;
  color: var(--tm-text-primary);
  letter-spacing: 0.02em;
}

.empty-desc {
  margin-top: 8px;
  font-size: 13px;
  color: var(--tm-text-secondary);
  line-height: 1.6;
}

.empty-action {
  margin-top: 20px;
}

@media (prefers-reduced-motion: reduce) {
  .empty-orbit,
  .orbit-dashed,
  .orbit-inner,
  .orbit-core,
  .orbit-dot {
    animation: none !important;
  }
}
</style>
