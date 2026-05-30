<template>
  <div class="script-history">
    <el-dialog :model-value="visible" @update:model-value="$emit('update:visible', $event)" title="脚本历史" width="70%">
      <el-empty description="暂无脚本历史记录" />
    </el-dialog>
  </div>
</template>

<script setup>
defineProps({
  visible: { type: Boolean, default: false },
})
defineEmits(['update:visible'])
</script>
