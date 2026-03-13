<template>
  <div class="login">
    <el-row justify="center" align="middle" style="height: 100%;">
      <el-col :span="8">
        <el-card class="login-card">
          <template #header>
            <h2 style="text-align: center; margin: 0;">用户登录</h2>
          </template>
          <el-form ref="loginFormRef" :model="loginForm" label-width="80px">
            <el-form-item label="用户名" prop="username" :rules="[{ required: true, message: '请输入用户名' }]">
              <el-input v-model="loginForm.username" placeholder="请输入用户名" />
            </el-form-item>
            <el-form-item label="密码" prop="password" :rules="[{ required: true, message: '请输入密码' }]">
              <el-input v-model="loginForm.password" type="password" placeholder="请输入密码" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" style="width: 100%;" @click="handleLogin">登录</el-button>
            </el-form-item>
            <div style="text-align: center;">
              <span>还没有账号？</span>
              <el-button type="text" @click="$router.push('/register')">立即注册</el-button>
            </div>
          </el-form>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, toRefs } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import request from '@/utils/request'

const router = useRouter()
const loginFormRef = ref()
const loginForm = reactive({
  username: '',
  password: ''
})

const handleLogin = async () => {
  try {
    const res = await request.post('/login', loginForm)
    localStorage.setItem('token', res.access_token)
    localStorage.setItem('user', JSON.stringify(res.user))
    ElMessage.success('登录成功')
    router.push('/')
  } catch (error) {
    console.error('Login failed:', error)
  }
}
</script>

<style scoped>
.login {
  height: 100%;
  background-color: #f5f7fa;
}

.login-card {
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}
</style>
