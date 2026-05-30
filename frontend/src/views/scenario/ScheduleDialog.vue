<template>
  <el-dialog :model-value="visible" @update:model-value="$emit('update:visible', $event)" title="定时任务" width="500px">
    <el-empty description="定时任务配置功能开发中" />
  </el-dialog>
</template>

<script setup>
defineProps({
  visible: { type: Boolean, default: false },
  scenarioId: { type: [Number, String], default: null },
})
defineEmits(['update:visible', 'saved'])
</script>
