<template>
  <div class="step-list">
    <el-empty description="步骤列表功能开发中" />
  </div>
</template>

<script setup>
defineProps({
  steps: { type: Array, default: () => [] },
  readonly: { type: Boolean, default: false },
})
defineEmits(['update:steps'])
</script>
