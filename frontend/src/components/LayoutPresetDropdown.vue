<template>
  <el-dropdown trigger="click" @command="$emit('change', $event)" :class="$attrs.class">
    <el-button :size="size" plain :title="title">
      <el-icon><Operation /></el-icon>
      <span v-if="showText" class="layout-text-hide">{{ text }}</span>
      <el-icon class="el-icon--right"><ArrowDown /></el-icon>
    </el-button>
    <template #dropdown>
      <el-dropdown-menu>
        <el-dropdown-item command="compact">
          <el-icon><Files /></el-icon> 紧凑布局
        </el-dropdown-item>
        <el-dropdown-item command="default">
          <el-icon><Grid /></el-icon> 默认布局
        </el-dropdown-item>
        <el-dropdown-item command="wide">
          <el-icon><FullScreen /></el-icon> 宽屏布局
        </el-dropdown-item>
        <el-dropdown-item divided command="editor-focus">
          <el-icon><EditPen /></el-icon> 编辑器专注
        </el-dropdown-item>
        <el-dropdown-item command="reset">
          <el-icon><RefreshRight /></el-icon> 重置为默认
        </el-dropdown-item>
      </el-dropdown-menu>
    </template>
  </el-dropdown>
</template>

<script setup>
import { Operation, ArrowDown, Files, Grid, FullScreen, EditPen, RefreshRight } from '@element-plus/icons-vue'

defineProps({
  text: { type: String, default: '布局' },
  title: { type: String, default: '布局预设' },
  size: { type: String, default: 'default' },
  showText: { type: Boolean, default: true }
})

defineEmits(['change'])
</script>

<style scoped>
.layout-text-hide {
  margin-left: 4px;
}
@media (max-width: 1280px) {
  .layout-text-hide {
    display: none;
  }
}
</style>
