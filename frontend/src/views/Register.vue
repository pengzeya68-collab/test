<template>
  <div class="register-container">
    <div class="register-card">
      <div class="register-header">
        <h1 class="title">创建账号</h1>
        <p class="subtitle">加入TestMaster，开启测试工程师成长之路</p>
      </div>
      
      <el-form 
        ref="registerFormRef" 
        :model="registerForm" 
        label-width="0"
        class="register-form"
        @submit.prevent="handleRegister"
      >
        <el-form-item
          prop="username"
          :rules="[
            { required: true, message: '请输入用户名', trigger: 'blur' },
            { min: 3, max: 20, message: '用户名长度在 3 到 20 个字符', trigger: 'blur' }
          ]"
        >
          <el-input 
          v-model="registerForm.username" 
          placeholder="用户名" 
          size="large"
          >
            <template #prefix>
              <el-icon><User /></el-icon>
            </template>
          </el-input>
        </el-form-item>
        
        <el-form-item
          prop="email"
          :rules="[
            { required: true, message: '请输入邮箱', trigger: 'blur' },
            { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
          ]"
        >
          <el-input 
          v-model="registerForm.email" 
          placeholder="邮箱" 
          size="large"
          >
            <template #prefix>
              <el-icon><Message /></el-icon>
            </template>
          </el-input>
        </el-form-item>

        <el-form-item
          prop="phone"
          :rules="[
            { required: true, message: '请输入手机号', trigger: 'blur' },
            { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的11位手机号', trigger: 'blur' }
          ]"
        >
          <el-input 
            v-model="registerForm.phone" 
            placeholder="手机号" 
            size="large"
          >
            <template #prefix>
              <el-icon><Phone /></el-icon>
            </template>
          </el-input>
        </el-form-item>
        
        <el-form-item
          prop="password"
          :rules="[
            { required: true, message: '请输入密码', trigger: 'blur' },
            { min: 6, max: 32, message: '密码长度在 6 到 32 个字符', trigger: 'blur' }
          ]"
        >
          <el-input 
            v-model="registerForm.password" 
            type="password" 
            placeholder="密码" 
            size="large"
          >
            <template #prefix>
              <el-icon><Lock /></el-icon>
            </template>
          </el-input>
        </el-form-item>
        
        <el-form-item
          prop="confirmPassword"
          :rules="[
            { required: true, message: '请确认密码', trigger: 'blur' },
            { validator: validateConfirmPassword, trigger: 'blur' }
          ]"
        >
          <el-input 
            v-model="registerForm.confirmPassword" 
            type="password" 
            placeholder="确认密码" 
            size="large"
            :disabled="!registerForm.password"
            @keyup.enter="handleRegister"
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
            @click="handleRegister"
            style="width: 100%;"
          >
            注册
          </el-button>
        </el-form-item>
      </el-form>
      
      <div class="register-footer">
        <span>已有账号？</span>
        <el-link type="primary" @click="goToLogin">立即登录</el-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { User, Lock, Message, Phone } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import request, { setToken } from '@/utils/request'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()
const registerFormRef = ref(null)
const loading = ref(false)

const registerForm = ref({
  username: '',
  email: '',
  phone: '',
  password: '',
  confirmPassword: ''
})

const codeCountdown = ref(0)

const sendCode = () => {
  if (!registerForm.value.phone) {
    ElMessage.warning('请先输入手机号')
    return
  }
  if (!/^1[3-9]\d{9}$/.test(registerForm.value.phone)) {
    ElMessage.warning('请输入正确的手机号')
    return
  }
  
  // 模拟发送验证码
  ElMessage.success('验证码已发送')
  codeCountdown.value = 60
  codeTimer = setInterval(() => {
    codeCountdown.value--
    if (codeCountdown.value <= 0) {
      clearInterval(codeTimer)
      codeTimer = null
    }
  }, 1000)
}

let codeTimer = null

onUnmounted(() => {
  if (codeTimer) {
    clearInterval(codeTimer)
    codeTimer = null
  }
})

const validateConfirmPassword = (rule, value, callback) => {
  if (value !== registerForm.value.password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const handleRegister = async () => {
  if (!registerFormRef.value) return
  
  await registerFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      try {
        const res = await request.post('/auth/register', {
          username: registerForm.value.username,
          email: registerForm.value.email,
          phone: registerForm.value.phone || '',
          password: registerForm.value.password
        })

        userStore.setLogin(res.access_token, res.user)
        setToken(res.access_token)
        localStorage.setItem('refresh_token', res.refresh_token)

        ElMessage.success('注册成功！')
        
        router.push('/')
      } catch (error) {
        console.error('注册失败:', error)
        const msg = error?.response?.data?.detail || error?.message || '注册失败，请稍后重试'
        ElMessage.error(msg)
      } finally {
        loading.value = false
      }
    }
  })
}

const goToLogin = () => {
  router.push('/login')
}
</script>

<style scoped>
.register-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #09090B;
  padding: 20px;
}

.register-card {
  background: #18181B;
  border-radius: 16px;
  padding: 48px;
  width: 100%;
  max-width: 450px;
  box-shadow: 0 20px 60px 0 rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.register-header {
  text-align: center;
  margin-bottom: 40px;
}

.title {
  font-size: 32px;
  font-weight: bold;
  color: #FAFAFA;
  margin: 0 0 10px 0;
}

.subtitle {
  font-size: 14px;
  color: #71717A;
  margin: 0;
}

.register-form {
  margin-bottom: 24px;
}

.register-footer {
  text-align: center;
  font-size: 14px;
  color: #A1A1AA;
}

@media (max-width: 768px) {
  .register-card {
    padding: 32px 24px;
  }
  
  .title {
    font-size: 24px;
  }
}
</style>
