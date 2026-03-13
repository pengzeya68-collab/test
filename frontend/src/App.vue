<template>
  <div id="app">
    <el-container style="height: 100%">
      <el-header class="header">
        <div class="logo">
          <h1>🚀 TestMaster</h1>
        </div>
        <div class="nav">
          <el-button type="text" @click="$router.push('/')" :class="{ active: $route.path === '/' }">
            首页
          </el-button>
          <el-button type="text" @click="$router.push('/learning-paths')" :class="{ active: $route.path === '/learning-paths' }">
            学习路径
          </el-button>
          <el-button type="text" @click="$router.push('/exercises')" :class="{ active: $route.path === '/exercises' }">
            练习题库
          </el-button>
          <el-button v-if="!isLoggedIn" type="primary" @click="$router.push('/login')">
            登录
          </el-button>
          <el-button v-else type="text" @click="logout">
            退出
          </el-button>
        </div>
      </el-header>
      
      <el-main class="main">
        <router-view />
      </el-main>
      
      <el-footer class="footer">
        <p>© 2026 TestMaster 在线编程学习平台</p>
      </el-footer>
    </el-container>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

const router = useRouter()
const isLoggedIn = ref(!!localStorage.getItem('token'))

const logout = () => {
  localStorage.removeItem('token')
  localStorage.removeItem('user')
  isLoggedIn.value = false
  ElMessage.success('退出成功')
  router.push('/login')
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body, #app {
  height: 100vh;
  width: 100%;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background-color: #2385bb;
  color: white;
  padding: 0 20px;
}

.logo h1 {
  margin: 0;
  font-size: 24px;
}

.nav .active {
  color: #ffd700 !important;
  font-weight: bold;
}

.main {
  background-color: #f5f7fa;
  padding: 20px;
  overflow-y: auto;
}

.footer {
  text-align: center;
  background-color: #f0f2f5;
  color: #909399;
  line-height: 60px;
}
</style>
