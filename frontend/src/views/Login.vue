<template>
  <div class="login-container">
    <div class="login-card">
      <div class="login-header">
        <h1 class="title">TestMaster</h1>
        <p class="subtitle">测试工程师成长平台</p>
      </div>
      
      <el-form 
        ref="loginFormRef" 
        :model="loginForm" 
        label-width="0"
        class="login-form"
        @submit.prevent="handleLogin"
      >
        <el-form-item
          prop="username"
          :rules="[
            { required: true, message: '请输入用户名', trigger: 'blur' }
          ]"
        >
          <el-input 
          v-model="loginForm.username" 
          placeholder="用户名" 
          size="large"
          >
            <template #prefix>
              <el-icon><User /></el-icon>
            </template>
          </el-input>
        </el-form-item>
        
        <el-form-item
          prop="password"
          :rules="[
            { required: true, message: '请输入密码', trigger: 'blur' }
          ]"
        >
          <el-input 
            v-model="loginForm.password" 
            type="password" 
            placeholder="密码" 
            size="large"
            @keyup.enter="handleLogin"
          >
            <template #prefix>
              <el-icon><Lock /></el-icon>
            </template>
          </el-input>
        </el-form-item>
        
        <el-form-item>
          <el-button 
            type="primary" 
            size="large" 
            :loading="loading"
            @click="handleLogin"
            style="width: 100%;"
          >
            登录
          </el-button>
        </el-form-item>
      </el-form>
      
      <div class="login-footer" style="display: flex; justify-content: space-between;">
        <span>还没有账号？</span>
        <el-link type="primary" @click="goToRegister">立即注册</el-link>
        <el-link type="primary" @click="goToForgotPassword">忘记密码？</el-link>
      </div>
      
      <div class="demo-account">
        <el-divider content-position="center">测试账号</el-divider>
        <div class="account-item">
          <span>普通用户：testuser / password123</span>
        </div>
        <div class="account-item">
          <span>管理员：admin / admin123</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { User, Lock } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import request from '@/utils/request'

const router = useRouter()
const loginFormRef = ref(null)
const loading = ref(false)

const loginForm = ref({
  username: '',
  password: ''
})

const handleLogin = async () => {
  if (!loginFormRef.value) return
  
  await loginFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      try {
        const res = await request.post('/login', loginForm.value)
        // 保存token和用户信息
        // 后端返回格式: {code: 0, msg: '登录成功', data: {access_token, refresh_token, user}}
        localStorage.setItem('token', res.data.access_token)
        localStorage.setItem('user', JSON.stringify(res.data.user))
        
        ElMessage.success('登录成功！')
        
        // 跳转到redirect地址，没有的话跳转到首页
        const redirect = router.currentRoute.value?.query?.redirect || '/'
        if (redirect) {
          router.push(decodeURIComponent(redirect)).catch(err => {
            console.error('路由跳转失败:', err)
            // 如果跳转失败，直接跳首页
            router.push('/')
          })
        } else {
          router.push('/')
        }
      } catch (error) {
        console.error('登录失败:', error)
      } finally {
        loading.value = false
      }
    }
  })
}

const goToRegister = () => {
  router.push('/register')
}

const goToForgotPassword = () => {
  router.push('/forgot-password')
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.login-card {
  background: white;
  border-radius: 16px;
  padding: 48px;
  width: 100%;
  max-width: 400px;
  box-shadow: 0 20px 60px 0 rgba(0, 0, 0, 0.3);
}

.login-header {
  text-align: center;
  margin-bottom: 40px;
}

.title {
  font-size: 36px;
  font-weight: bold;
  color: #303133;
  margin: 0 0 10px 0;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.subtitle {
  font-size: 14px;
  color: #909399;
  margin: 0;
}

.login-form {
  margin-bottom: 24px;
}

.login-footer {
  text-align: center;
  font-size: 14px;
  color: #606266;
}

.demo-account {
  margin-top: 24px;
}

.account-item {
  text-align: center;
  font-size: 13px;
  color: #909399;
  padding: 8px 0;
}

@media (max-width: 768px) {
  .login-card {
    padding: 32px 24px;
  }
  
  .title {
    font-size: 28px;
  }
}
</style>
