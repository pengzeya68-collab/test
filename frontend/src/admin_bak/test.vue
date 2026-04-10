<template>
  <div style="height: 100vh; background: #f0f2f5; padding: 20px;">
    <h1>后台测试页面</h1>
    <p>如果能看到这个页面，说明路由是正常的！</p>
    <el-button type="primary" @click="test">测试Element">测试Element Plus</el-button>
  </div>
</template>

<script setup>
import { ElButton, ElMessage } from 'element-plus'

const test = () => {
  ElMessage.success('Element Plus正常工作！')
}
</script>
