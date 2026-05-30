<template>
  <el-drawer :model-value="visible" @update:model-value="$emit('update:visible', $event)" title="执行历史" size="50%">
    <el-empty description="暂无执行历史" />
  </el-drawer>
</template>

<script setup>
defineProps({
  visible: { type: Boolean, default: false },
  scenarioId: { type: [Number, String], default: null },
})
defineEmits(['update:visible'])
</script>
