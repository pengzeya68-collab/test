<template>
  <el-dialog :model-value="visible" @update:model-value="$emit('update:visible', $event)" title="数据驱动" width="70%">
    <el-empty description="数据驱动配置功能开发中" />
  </el-dialog>
</template>

<script setup>
defineProps({
  visible: { type: Boolean, default: false },
  scenario: { type: Object, default: () => ({}) },
})
defineEmits(['update:visible'])
</script>
