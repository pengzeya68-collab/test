<template>
  <div class="login-container">
    <div class="login-box">
      <div class="login-header">
        <el-icon size="48" color="#409EFF"><Platform /></el-icon>
        <h2 class="login-title">TestMaster 后台管理系统</h2>
        <p class="login-subtitle">请使用管理员账号登录</p>
      </div>
      
      <el-form
        ref="loginFormRef"
        :model="loginForm"
        :rules="loginRules"
        class="login-form"
        size="large"
      >
        <el-form-item prop="username">
          <el-input
            v-model="loginForm.username"
            placeholder="请输入用户名"
            prefix-icon="User"
            clearable
          />
        </el-form-item>
        
        <el-form-item prop="password">
          <el-input
            v-model="loginForm.password"
            type="password"
            placeholder="请输入密码"
            prefix-icon="Lock"
            show-password
            @keyup.enter="handleLogin"
          />
        </el-form-item>
        
        <el-form-item>
          <el-checkbox v-model="loginForm.remember">记住我</el-checkbox>
        </el-form-item>
        
        <el-form-item>
          <el-button
            type="primary"
            :loading="loading"
            class="login-btn"
            @click="handleLogin"
          >
            {{ loading ? '登录中...' : '登录' }}
          </el-button>
        </el-form-item>
      </el-form>
      
      <div class="login-footer">
        <el-link type="primary" :underline="false">忘记密码？</el-link>
        <el-link type="primary" :underline="false" @click="goToHome">返回首页</el-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Platform } from '@element-plus/icons-vue'
import request from '@/utils/request'
import { setAdminToken } from '@/admin/utils/permission'

const router = useRouter()
const route = useRoute()
const loginFormRef = ref()
const loading = ref(false)

// 登录表单数据
const loginForm = reactive({
  username: '',
  password: '',
  remember: false
})

// 表单验证规则
const loginRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度在 3 到 20 个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于 6 个字符', trigger: 'blur' }
  ]
}

const goToHome = () => {
  router.push('/')
}

// 处理登录
const handleLogin = async () => {
  if (!loginFormRef.value) return
  
  await loginFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      
      try {
        // 调用真实登录API
        const response = await request.post('/admin/login', loginForm)
        
        // 存储token和用户信息
        setAdminToken(response.data.token)
        localStorage.setItem('admin_info', JSON.stringify(response.data.admin_info))
        
        ElMessage.success('登录成功')
        
        // 跳转到登录前的页面或后台首页
        const redirect = route.query.redirect || '/admin/dashboard'
        console.log('登录成功，跳转到:', redirect)
        router.push(redirect).catch(err => {
          console.error('跳转失败:', err)
          // 跳转失败时强制刷新
          window.location.href = '/#/admin/dashboard'
        })
      } catch (error) {
        ElMessage.error((error.response && error.response.data && error.response.data.msg) || '登录失败，请检查账号密码')
      } finally {
        loading.value = false
      }
    }
  })
}
</script>

<style scoped lang="scss">
.login-container {
  height: 100vh;
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  
  .login-box {
    width: 420px;
    padding: 40px;
    background: #fff;
    border-radius: 12px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
    
    .login-header {
      text-align: center;
      margin-bottom: 32px;
      
      .login-title {
        margin: 16px 0 8px;
        color: #303133;
        font-size: 24px;
        font-weight: 600;
      }
      
      .login-subtitle {
        color: #909399;
        font-size: 14px;
      }
    }
    
    .login-form {
      .el-form-item {
        margin-bottom: 24px;
      }
      
      .login-btn {
        width: 100%;
        height: 44px;
        font-size: 16px;
      }
    }
    
    .login-footer {
      display: flex;
      justify-content: space-between;
      margin-top: 16px;
      
      .el-link {
        font-size: 14px;
      }
    }
  }
}
</style>
