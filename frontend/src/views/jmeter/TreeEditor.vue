<template>
  <div class="tree-editor">
    <el-dialog :model-value="visible" @update:model-value="$emit('update:visible', $event)" title="脚本编辑器" width="80%">
      <el-empty description="脚本编辑功能开发中" />
    </el-dialog>
  </div>
</template>

<script setup>
defineProps({
  visible: { type: Boolean, default: false },
  scenario: { type: Object, default: () => ({}) },
})
defineEmits(['update:visible', 'save'])
</script>
