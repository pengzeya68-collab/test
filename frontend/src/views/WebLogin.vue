<template>
  <div class="login-container" data-testid="login-page">
    <AuroraBackground />

    <div
      ref="cardRef"
      class="login-card"
      @mousemove="onCardMove"
      @mouseleave="onCardLeave"
    >
      <div class="login-header">
        <div class="logo-mark" aria-hidden="true">
          <svg width="44" height="44" viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">
            <defs>
              <linearGradient id="loginLogoGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stop-color="#6366F1" />
                <stop offset="100%" stop-color="#8B5CF6" />
              </linearGradient>
            </defs>
            <path d="M14 22 L50 22 L50 28 L38 28 L38 50 L26 50 L26 28 L14 28 Z" fill="url(#loginLogoGrad)" />
          </svg>
        </div>
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
        <el-form-item prop="username" :rules="[{ required: true, message: '请输入用户名', trigger: 'blur' }]">
          <el-input v-model="loginForm.username" data-testid="login-username-input" placeholder="用户名" size="large">
            <template #prefix><el-icon><User /></el-icon></template>
          </el-input>
        </el-form-item>

        <el-form-item prop="password" :rules="[{ required: true, message: '请输入密码', trigger: 'blur' }]">
          <el-input
            v-model="loginForm.password"
            data-testid="login-password-input"
            type="password"
            placeholder="密码"
            size="large"
            @keyup.enter="handleLogin"
          >
            <template #prefix><el-icon><Lock /></el-icon></template>
          </el-input>
        </el-form-item>

        <el-form-item>
          <el-button
            v-ripple
            data-testid="login-submit-button"
            type="primary"
            size="large"
            :loading="loading"
            class="login-btn"
            @click="handleLogin"
          >
            <span>登 录</span>
            <span class="btn-arrow" aria-hidden="true">&rarr;</span>
          </el-button>
        </el-form-item>
      </el-form>

      <div class="login-footer">
        <span>还没有账号？</span>
        <router-link to="/register" class="footer-link">立即注册</router-link>
        <span class="footer-divider">·</span>
        <router-link to="/forgot-password" class="footer-link">忘记密码？</router-link>
      </div>

      <div v-if="isDev" class="demo-account">
        <el-divider content-position="center">测试账号</el-divider>
        <div class="account-item">普通用户：testuser / password123</div>
        <div class="account-item">管理员：admin / admin123</div>
      </div>
    </div>

    <div class="brand-strip">
      <span>© 2026 TestMaster</span>
      <span class="dot">·</span>
      <span>专业测试学习平台</span>
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
import AuroraBackground from '@/components/base/AuroraBackground.vue'

const router = useRouter()
const userStore = useUserStore()
const loginFormRef = ref(null)
const cardRef = ref(null)
const loading = ref(false)
const isDev = import.meta.env.DEV
const loginForm = ref({ username: '', password: '' })

const onCardMove = (event) => {
  if (!cardRef.value || window.matchMedia('(prefers-reduced-motion: reduce)').matches) return
  const rect = cardRef.value.getBoundingClientRect()
  const x = (event.clientX - rect.left) / rect.width - 0.5
  const y = (event.clientY - rect.top) / rect.height - 0.5
  cardRef.value.style.transform = `perspective(1200px) rotateY(${x * 6}deg) rotateX(${-y * 6}deg) translateZ(0)`
}

const onCardLeave = () => {
  if (cardRef.value) cardRef.value.style.transform = ''
}

const handleLogin = async () => {
  try {
    await loginFormRef.value?.validate()
  } catch {
    return
  }

  loading.value = true
  try {
    const result = await request.post('/auth/login', loginForm.value)
    userStore.setLogin(result.access_token, result.user)
    setToken(result.access_token)
    ElMessage.success('登录成功！')
    const redirect = router.currentRoute.value.query.redirect
    if (redirect && !redirect.startsWith('http') && !redirect.startsWith('//')) {
      await router.push(decodeURIComponent(redirect))
    } else {
      await router.push('/')
    }
  } catch (error) {
    console.error('登录失败:', error)
    ElMessage.error(error.response?.data?.detail || error.message || '登录失败，请检查用户名和密码')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped lang="scss">
.login-container {
  position: relative;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  padding: 24px;
  background: var(--tm-bg-page);
}

.login-card {
  position: relative;
  z-index: 2;
  width: 100%;
  max-width: 420px;
  padding: 44px 40px;
  background: rgba(30, 41, 59, 0.85);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 20px;
  box-shadow: 0 24px 48px rgba(0, 0, 0, 0.35);
  backdrop-filter: blur(20px) saturate(160%);
  -webkit-backdrop-filter: blur(20px) saturate(160%);
  transition: transform 0.25s ease, box-shadow 0.25s ease;
}

.login-card::before {
  position: absolute;
  inset: 0;
  padding: 1px;
  pointer-events: none;
  content: '';
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.4), rgba(139, 92, 246, 0.2));
  border-radius: inherit;
  -webkit-mask: linear-gradient(#000 0 0) content-box, linear-gradient(#000 0 0);
  -webkit-mask-composite: xor;
  mask-composite: exclude;
}

.login-card:focus-within {
  box-shadow: 0 28px 56px rgba(0, 0, 0, 0.4), 0 0 0 1px rgba(99, 102, 241, 0.25);
}

.login-header {
  margin-bottom: 32px;
  text-align: center;
}

.logo-mark { display: flex; justify-content: center; margin-bottom: 12px; }

.title {
  margin: 0 0 8px;
  font-size: 32px;
  font-weight: 800;
  letter-spacing: 0;
  background: var(--tm-gradient-brand);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}

.subtitle { margin: 0; color: var(--tm-text-secondary, #a1a1aa); font-size: 13px; letter-spacing: 0; }
.login-form { margin-bottom: 24px; }

.login-form :deep(.el-input__wrapper) {
  padding: 4px 14px;
  background: rgba(0, 0, 0, 0.3) !important;
  border-radius: 12px !important;
  transition: all 0.3s ease;
}

.login-form :deep(.el-input__wrapper.is-focus) { box-shadow: 0 0 0 1px var(--tm-color-primary) !important; }

.login-btn {
  display: flex;
  width: 100%;
  height: 46px;
  align-items: center;
  justify-content: center;
  gap: 12px;
  overflow: hidden;
  border: 0 !important;
  border-radius: 10px !important;
  background: linear-gradient(135deg, var(--tm-color-primary), var(--tm-color-primary-dark)) !important;
  box-shadow: 0 4px 16px rgba(var(--tm-color-primary-rgb), 0.3) !important;
  font-size: 15px;
  font-weight: 600;
  letter-spacing: 0;
}

.login-btn:hover { transform: translateY(-1px); box-shadow: 0 8px 24px rgba(var(--tm-color-primary-rgb), 0.35) !important; }
.login-btn:active { transform: translateY(0); }
.btn-arrow { transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1); }
.login-btn:hover .btn-arrow { transform: translateX(4px); }

.login-footer {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: var(--tm-text-secondary);
  font-size: 13px;
}

.footer-link { position: relative; color: var(--tm-color-primary); font-weight: 500; text-decoration: none; }
.footer-link::after { position: absolute; bottom: -2px; left: 0; width: 0; height: 1px; content: ''; background: var(--tm-color-primary); transition: width 0.3s ease; }
.footer-link:hover::after { width: 100%; }
.footer-divider { opacity: 0.4; }

.demo-account { margin-top: 24px; }
.account-item { padding: 6px 0; color: var(--tm-text-secondary); font-family: 'JetBrains Mono', monospace; font-size: 12px; text-align: center; }

.brand-strip {
  position: absolute;
  z-index: 2;
  bottom: 20px;
  left: 50%;
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--tm-text-secondary);
  font-size: 11px;
  letter-spacing: 0;
  opacity: 0.5;
  transform: translateX(-50%);
}

.dot { opacity: 0.6; }

@media (max-width: 768px) {
  .login-card { padding: 36px 24px; border-radius: 18px; }
  .title { font-size: 28px; }
  .brand-strip { font-size: 10px; }
}

@media (prefers-reduced-motion: reduce) {
  .login-card { transition: none !important; }
}
</style>
