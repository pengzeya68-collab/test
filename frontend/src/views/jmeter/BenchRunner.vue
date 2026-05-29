<template>
  <div class="bench-runner">
    <el-dialog :model-value="visible" @update:model-value="$emit('update:visible', $event)" title="性能测试" width="80%">
      <el-empty description="性能测试功能开发中" />
    </el-dialog>
  </div>
</template>

<script setup>
defineProps({
  visible: { type: Boolean, default: false },
  scenario: { type: Object, default: () => ({}) },
})
defineEmits(['update:visible'])
</script>
