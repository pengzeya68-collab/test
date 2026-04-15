<template>
  <div class="not-found">
    <div class="not-found-content">
      <h1 class="error-code">404</h1>
      <p class="error-message">页面未找到</p>
      <p class="error-detail">你访问的页面不存在或已被移除</p>
      <el-button type="primary" @click="router.push('/')">返回首页</el-button>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
const router = useRouter()
</script>

<style scoped>
.not-found {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: var(--tm-bg-page);
}

.not-found-content {
  text-align: center;
}

.error-code {
  font-size: 120px;
  font-weight: 700;
  background: var(--tm-gradient-brand, linear-gradient(to right, #EC4899, #9333EA));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  line-height: 1;
  margin: 0 0 16px;
}

.error-message {
  font-size: 24px;
  color: var(--tm-text-primary);
  margin: 0 0 8px;
}

.error-detail {
  font-size: 14px;
  color: var(--tm-text-secondary);
  margin: 0 0 32px;
}
</style>
