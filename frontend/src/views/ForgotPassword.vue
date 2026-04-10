<template>
  <div class="forgot-password-container">
    <div class="forgot-password-card">
      <div class="forgot-password-header">
        <h1 class="title">重置密码</h1>
        <p class="subtitle">通过手机号重置你的账号密码</p>
      </div>
      
      <el-form 
        ref="forgotPasswordFormRef" 
        :model="forgotPasswordForm" 
        label-width="0"
        class="forgot-password-form"
        @submit.prevent="handleSubmit"
      >
        <el-form-item
          prop="phone"
          :rules="[
            { required: true, message: '请输入手机号', trigger: 'blur' },
            { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号格式', trigger: 'blur' }
          ]"
        >
          <el-input 
            v-model="forgotPasswordForm.phone" 
            placeholder="手机号" 
            size="large"
          >
            <template #prefix>
              <el-icon>📱</el-icon>
            </template>
          </el-input>
        </el-form-item>
        
        <el-form-item
          prop="code"
          :rules="[
            { required: true, message: '请输入验证码', trigger: 'blur' },
            { len: 6, message: '验证码长度为6位', trigger: 'blur' }
          ]"
        >
          <div style="display: flex; gap: 10px;">
            <el-input 
              v-model="forgotPasswordForm.code" 
              placeholder="验证码" 
              size="large"
              style="flex: 1;"
            >
              <template #prefix>
                <el-icon>🔒</el-icon>
              </template>
            </el-input>
            <el-button 
              size="large" 
              @click="sendCode" 
              :disabled="codeCountdown > 0 || !forgotPasswordForm.phone || !/^1[3-9]\d{9}$/.test(forgotPasswordForm.phone)"
            >
              {{ codeCountdown > 0 ? `${codeCountdown}s后重新发送` : '发送验证码' }}
            </el-button>
          </div>
          <p style="font-size: 12px; color: #999; margin: 5px 0 0 0;">测试验证码：123456</p>
        </el-form-item>
        
        <el-form-item
          prop="new_password"
          :rules="[
            { required: true, message: '请输入新密码', trigger: 'blur' },
            { min: 6, max: 32, message: '密码长度在 6 到 32 个字符', trigger: 'blur' }
          ]"
        >
          <el-input 
            v-model="forgotPasswordForm.new_password" 
            type="password" 
            placeholder="新密码" 
            size="large"
          >
            <template #prefix>
              <el-icon>🔑</el-icon>
            </template>
          </el-input>
        </el-form-item>
        
        <el-form-item
          prop="confirm_password"
          :rules="[
            { required: true, message: '请确认新密码', trigger: 'blur' },
            { validator: validateConfirmPassword, trigger: 'blur' }
          ]"
        >
          <el-input 
            v-model="forgotPasswordForm.confirm_password" 
            type="password" 
            placeholder="确认新密码" 
            size="large"
            :disabled="!forgotPasswordForm.new_password"
            @keyup.enter="handleSubmit"
          >
            <template #prefix>
              <el-icon>🔑</el-icon>
            </template>
          </el-input>
        </el-form-item>
        
        <el-form-item>
          <el-button 
            type="primary" 
            size="large" 
            :loading="loading"
            @click="handleSubmit"
            style="width: 100%;"
          >
            重置密码
          </el-button>
        </el-form-item>
      </el-form>
      
      <div class="forgot-password-footer">
        <el-link type="primary" @click="goToLogin">返回登录</el-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import request from '@/utils/request'

const router = useRouter()
const forgotPasswordFormRef = ref(null)
const loading = ref(false)
const codeCountdown = ref(0)

const forgotPasswordForm = ref({
  phone: '',
  code: '',
  new_password: '',
  confirm_password: ''
})

const validateConfirmPassword = (rule, value, callback) => {
  if (value !== forgotPasswordForm.value.new_password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const sendCode = () => {
  if (!forgotPasswordForm.value.phone) {
    ElMessage.warning('请先输入手机号')
    return
  }
  if (!/^1[3-9]\d{9}$/.test(forgotPasswordForm.value.phone)) {
    ElMessage.warning('请输入正确的手机号')
    return
  }
  
  // 模拟发送验证码
  ElMessage.success('验证码已发送')
  codeCountdown.value = 60
  const timer = setInterval(() => {
    codeCountdown.value--
    if (codeCountdown.value <= 0) {
      clearInterval(timer)
    }
  }, 1000)
}

const handleSubmit = async () => {
  if (!forgotPasswordFormRef.value) return
  
  await forgotPasswordFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      try {
        await request.post('/forgot-password', {
          phone: forgotPasswordForm.value.phone,
          code: forgotPasswordForm.value.code,
          new_password: forgotPasswordForm.value.new_password
        })
        
        ElMessage.success('密码重置成功！请使用新密码登录')
        
        // 跳转到登录页
        router.push('/login')
      } catch (error) {
        console.error('密码重置失败:', error)
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
.forgot-password-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.forgot-password-card {
  background: white;
  border-radius: 16px;
  padding: 48px;
  width: 100%;
  max-width: 450px;
  box-shadow: 0 20px 60px 0 rgba(0, 0, 0, 0.3);
}

.forgot-password-header {
  text-align: center;
  margin-bottom: 40px;
}

.title {
  font-size: 32px;
  font-weight: bold;
  color: #303133;
  margin: 0 0 10px 0;
}

.subtitle {
  font-size: 14px;
  color: #909399;
  margin: 0;
}

.forgot-password-form {
  margin-bottom: 24px;
}

.forgot-password-footer {
  text-align: center;
  font-size: 14px;
  color: #606266;
}

@media (max-width: 768px) {
  .forgot-password-card {
    padding: 32px 24px;
  }
  
  .title {
    font-size: 24px;
  }
}
</style>
