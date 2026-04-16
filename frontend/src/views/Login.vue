﻿﻿﻿<template>
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
import request, { setToken } from '@/utils/request'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()
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
        const res = await request.post('/auth/login', loginForm.value)
        userStore.setLogin(res.access_token, res.user)
        setToken(res.access_token)
        
        ElMessage.success('登录成功！')
        
        const completed = await userStore.checkAssessmentStatus()
        const redirect = router.currentRoute.value?.query?.redirect
        
        if (redirect) {
          router.push(decodeURIComponent(redirect)).catch(() => router.push('/'))
        } else if (!completed) {
          router.push('/assessment')
        } else {
          router.push('/')
        }
      } catch (error) {
        console.error('登录失败:', error)
        ElMessage.error(error.response?.data?.detail || '登录失败，请检查用户名和密码')
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
  background: var(--tm-bg-page);
  padding: 20px;
}

.login-card {
  background: var(--tm-bg-card);
  border-radius: 16px;
  padding: 48px;
  width: 100%;
  max-width: 400px;
  box-shadow: 0 20px 60px 0 rgba(0, 0, 0, 0.3);
  border: 1px solid var(--tm-border-primary);
}

.login-header {
  text-align: center;
  margin-bottom: 40px;
}

.title {
  font-size: 36px;
  font-weight: bold;
  color: var(--tm-text-primary);
  margin: 0 0 10px 0;
  background: var(--tm-gradient-brand, linear-gradient(135deg, #EC4899, #9333EA));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.subtitle {
  font-size: 14px;
  color: var(--tm-text-secondary);
  margin: 0;
}

.login-form {
  margin-bottom: 24px;
}

.login-footer {
  text-align: center;
  font-size: 14px;
  color: var(--tm-text-tertiary);
}

.demo-account {
  margin-top: 24px;
}

.account-item {
  text-align: center;
  font-size: 13px;
  color: var(--tm-text-secondary);
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
