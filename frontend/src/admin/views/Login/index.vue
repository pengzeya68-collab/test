<template>
  <div class="admin-login-theme">
    <div class="login-card">
      <div class="login-header">
        <h2>TestMaster</h2>
        <p>管理员后台登录</p>
      </div>

      <el-form :model="form" :rules="rules" ref="formRef" label-width="0">
        <el-form-item prop="username">
          <el-input
            v-model="form.username"
            placeholder="用户名"
            size="large"
            class="dark-input"
          >
            <template #prefix>
              <el-icon><User /></el-icon>
            </template>
          </el-input>
        </el-form-item>
        <el-form-item prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="密码"
            size="large"
            class="dark-input"
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
            style="width: 100%;"
            :loading="loading"
            @click="handleLogin"
            class="btn-login"
          >
            登录
          </el-button>
        </el-form-item>
      </el-form>

      <div class="login-footer">
        <span>默认账号: admin / admin123</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'
import request from '@/utils/request'
import { loadSavedTheme, applyTheme } from '@/utils/ThemeConfig'

const router = useRouter()
const route = useRoute()
const formRef = ref()
const loading = ref(false)

const form = ref({
  username: '',
  password: ''
})

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

onMounted(() => {
  const savedThemeId = loadSavedTheme()
  applyTheme(savedThemeId)
})

const handleLogin = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true

      try {
        const res = await request.post('/login', {
          username: form.value.username,
          password: form.value.password
        })

        // 后端返回结构: { code: 0, data: { access_token, user }, msg: '登录成功' }
        // 兼容: 从 res 或 res.data 获取 access_token
        const access_token = res.access_token || (res.data && res.data.access_token)
        const user = res.user || (res.data && res.data.user)

        if (!access_token || access_token === 'undefined' || access_token === 'null') {
          ElMessage.error('登录失败：服务器未返回有效Token')
          loading.value = false
          return
        }

        // 检查是否是管理员
        if (!user.is_admin) {
          ElMessage.error('该账号不是管理员，无权访问后台')
          loading.value = false
          return
        }

        localStorage.setItem('admin_token', access_token)
        localStorage.setItem('admin_info', JSON.stringify(user))

        ElMessage.success('登录成功')

        const redirect = route.query.redirect || '/admin/dashboard'
        // 使用 router.push 进行单页应用跳转，避免页面刷新
        router.push(redirect).catch(err => {
          console.error('路由跳转失败:', err)
          // 如果跳转失败，直接跳后台首页
          router.push('/admin/dashboard')
        })
      } catch (error) {
        console.error('登录异常:', error)
        loading.value = false
      }
    }
  })
}
</script>

<style scoped>
.admin-login-theme {
  height: 100vh;
  background: var(--tm-bg-color);
  background-image: var(--tm-bg-image);
  background-size: cover;
  background-position: center;
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
}

.login-card {
  width: 420px;
  background: var(--tm-card-bg);
  padding: 48px 40px;
  border-radius: 16px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.4), var(--tm-glow-effect);
  border: var(--tm-card-border);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
}

.login-header {
  text-align: center;
  margin-bottom: 36px;
}

.login-header h2 {
  margin: 0 0 10px 0;
  font-size: 32px;
  font-weight: 700;
  background: linear-gradient(135deg, var(--tm-color-primary), var(--tm-color-primary-dark));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.login-header p {
  margin: 0;
  color: var(--tm-text-secondary);
  font-size: 14px;
}

.dark-input :deep(.el-input__wrapper) {
  background: var(--tm-card-bg);
  box-shadow: 0 0 0 1px var(--tm-border-light) inset;
  border-radius: 8px;
}

.dark-input :deep(.el-input__inner) {
  color: var(--tm-text-primary);
}

.btn-login {
  background: linear-gradient(135deg, var(--tm-color-primary), var(--tm-color-primary-dark));
  border: none;
  box-shadow: 0 4px 15px rgba(var(--tm-color-primary), 0.3);
  font-size: 16px;
  padding: 12px 0;
}

.btn-login:hover {
  background: linear-gradient(135deg, var(--tm-color-primary), var(--tm-color-primary-dark));
  box-shadow: 0 6px 20px rgba(var(--tm-color-primary), 0.4);
}

.login-footer {
  text-align: center;
  margin-top: 16px;
}

.login-footer span {
  color: var(--tm-text-secondary);
  font-size: 12px;
}
</style>
