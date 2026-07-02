<template>
  <div
    class="base-card glass-card gradient-border"
    :class="{ 'magnetic-host': magnetic, 'spotlight-host': spotlight }"
  >
    <slot />
  </div>
</template>

<script setup>
defineProps({
  magnetic: { type: Boolean, default: false },
  spotlight: { type: Boolean, default: true }
})
</script>

<style scoped>
.base-card {
  position: relative;
  padding: 24px;
  border-radius: 16px;
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1),
              box-shadow 0.3s,
              border-color 0.3s;
  overflow: hidden;
}

.base-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 16px 48px rgba(0, 0, 0, 0.5),
              0 0 24px rgba(var(--tm-color-primary-rgb), 0.18);
}
</style>
