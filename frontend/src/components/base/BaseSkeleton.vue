<template>
  <div class="base-skeleton">
    <div v-for="i in lines" :key="i" class="skeleton-line" :style="{ width: getLineWidth(i) }"></div>
  </div>
</template>

<script setup>
defineProps({
  lines: { type: Number, default: 3 }
})

const getLineWidth = (i) => {
  const widths = ['100%', '85%', '70%', '92%', '60%']
  return widths[(i - 1) % widths.length]
}
</script>

<style scoped>
.base-skeleton {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 12px 0;
}

.skeleton-line {
  height: 14px;
  background: linear-gradient(
    90deg,
    rgba(255, 255, 255, 0.04) 0%,
    rgba(255, 255, 255, 0.1) 20%,
    rgba(255, 255, 255, 0.04) 40%,
    rgba(255, 255, 255, 0.04) 100%
  );
  background-size: 200% 100%;
  animation: skeleton-line-shimmer 1.5s ease-in-out infinite;
  border-radius: 6px;
}

@keyframes skeleton-line-shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

@media (prefers-reduced-motion: reduce) {
  .skeleton-line {
    animation: none !important;
  }
}
</style>
