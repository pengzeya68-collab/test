<template>
  <div class="register">
    <el-row justify="center" align="middle" style="height: 100%;">
      <el-col :span="8">
        <el-card class="register-card">
          <template #header>
            <h2 style="text-align: center; margin: 0;">用户注册</h2>
          </template>
          <el-form ref="registerFormRef" :model="registerForm" label-width="80px">
            <el-form-item label="用户名" prop="username" :rules="[{ required: true, message: '请输入用户名' }]">
              <el-input v-model="registerForm.username" placeholder="请输入用户名" />
            </el-form-item>
            <el-form-item label="邮箱" prop="email" :rules="[{ required: true, message: '请输入邮箱' }, { type: 'email', message: '请输入有效的邮箱地址' }]">
              <el-input v-model="registerForm.email" placeholder="请输入邮箱" />
            </el-form-item>
            <el-form-item label="密码" prop="password" :rules="[{ required: true, message: '请输入密码' }, { min: 6, message: '密码长度不能少于6位' }]">
              <el-input v-model="registerForm.password" type="password" placeholder="请输入密码" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" style="width: 100%;" @click="handleRegister">注册</el-button>
            </el-form-item>
            <div style="text-align: center;">
              <span>已有账号？</span>
              <el-button type="text" @click="$router.push('/login')">立即登录</el-button>
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
const registerFormRef = ref()
const registerForm = reactive({
  username: '',
  email: '',
  password: ''
})

const handleRegister = async () => {
  try {
    const res = await request.post('/register', registerForm)
    localStorage.setItem('token', res.access_token)
    localStorage.setItem('user', JSON.stringify(res.user))
    ElMessage.success('注册成功')
    router.push('/')
  } catch (error) {
    console.error('Registration failed:', error)
  }
}
</script>

<style scoped>
.register {
  height: 100%;
  background-color: #f5f7fa;
}

.register-card {
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}
</style>
