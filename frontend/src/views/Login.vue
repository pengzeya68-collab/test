<template>
  <div class="login-container" ref="containerRef" @mousemove="onContainerMove">
    <AuroraBackground />

    <div class="login-card" ref="cardRef" @mousemove="onCardMove" @mouseleave="onCardLeave">
      <div class="login-header">
        <div class="logo-mark">
          <svg width="44" height="44" viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">
            <defs>
              <linearGradient id="loginLogoGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stop-color="var(--tm-color-primary)"/>
                <stop offset="50%" stop-color="#ec4899"/>
                <stop offset="100%" stop-color="#00f2fe"/>
              </linearGradient>
            </defs>
            <path d="M14 22 L50 22 L50 28 L38 28 L38 50 L26 50 L26 28 L14 28 Z" fill="url(#loginLogoGrad)"/>
          </svg>
        </div>
        <h1 class="title">TestMaster</h1>
        <p class="subtitle">测试工程师成长平台 · 2026</p>
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
          :rules="[{ required: true, message: '请输入用户名', trigger: 'blur' }]"
        >
          <el-input v-model="loginForm.username" placeholder="用户名" size="large">
            <template #prefix><el-icon><User /></el-icon></template>
          </el-input>
        </el-form-item>

        <el-form-item
          prop="password"
          :rules="[{ required: true, message: '请输入密码', trigger: 'blur' }]"
        >
          <el-input
            v-model="loginForm.password"
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
            type="primary"
            size="large"
            :loading="loading"
            class="login-btn"
            @click="handleLogin"
          >
            <span class="btn-text">登 录</span>
            <span class="btn-arrow">→</span>
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
        <div class="account-item"><span>普通用户：testuser / password123</span></div>
        <div class="account-item"><span>管理员：admin / admin123</span></div>
      </div>
    </div>

    <div class="brand-strip">
      <span>© 2026 TestMaster</span>
      <span class="dot">·</span>
      <span>Cyberpunk Edition</span>
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
const loading = ref(false)
const isDev = import.meta.env.DEV
const cardRef = ref(null)
const containerRef = ref(null)

const loginForm = ref({ username: '', password: '' })

const onCardMove = (e) => {
  if (!cardRef.value) return
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return
  const rect = cardRef.value.getBoundingClientRect()
  const x = (e.clientX - rect.left) / rect.width - 0.5
  const y = (e.clientY - rect.top) / rect.height - 0.5
  cardRef.value.style.transform = `perspective(1200px) rotateY(${x * 6}deg) rotateX(${-y * 6}deg) translateZ(0)`
}

const onCardLeave = () => {
  if (!cardRef.value) return
  cardRef.value.style.transform = ''
}

const onContainerMove = () => {}

const handleLogin = async () => {
  if (!loginFormRef.value) return
  try {
    await loginFormRef.value.validate()
  } catch {
    return
  }

  loading.value = true
  try {
    const res = await request.post('/auth/login', loginForm.value)
    userStore.setLogin(res.access_token, res.user)
    setToken(res.access_token)
    ElMessage.success('登录成功！')
    const redirect = router.currentRoute.value?.query?.redirect
    if (redirect && !redirect.startsWith('http') && !redirect.startsWith('//')) {
      router.push(decodeURIComponent(redirect)).catch(() => router.push('/'))
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
</script>

<style scoped lang="scss">
.login-container {
  position: relative;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--tm-bg-page, #09090b);
  padding: 24px;
  overflow: hidden;
  perspective: 1200px;
}

.login-card {
  position: relative;
  z-index: 2;
  background: var(--tm-glass-bg, rgba(24, 24, 27, 0.75));
  backdrop-filter: blur(24px) saturate(180%);
  -webkit-backdrop-filter: blur(24px) saturate(180%);
  border-radius: 24px;
  padding: 48px 44px;
  width: 100%;
  max-width: 420px;
  box-shadow:
    0 24px 80px rgba(0, 0, 0, 0.5),
    0 0 0 1px rgba(255, 255, 255, 0.06),
    inset 0 1px 0 rgba(255, 255, 255, 0.08);
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1),
              box-shadow 0.3s ease;
  transform-style: preserve-3d;
  will-change: transform;
}

.login-card::before {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: inherit;
  padding: 1px;
  background: linear-gradient(135deg,
    rgba(var(--tm-color-primary-rgb), 0.6),
    rgba(236, 72, 153, 0.3) 50%,
    rgba(0, 242, 254, 0.5));
  -webkit-mask: linear-gradient(#000 0 0) content-box, linear-gradient(#000 0 0);
  -webkit-mask-composite: xor;
  mask-composite: exclude;
  pointer-events: none;
}

.login-card:focus-within {
  box-shadow:
    0 32px 96px rgba(0, 0, 0, 0.6),
    0 0 0 1px rgba(var(--tm-color-primary-rgb), 0.4),
    0 0 48px rgba(var(--tm-color-primary-rgb), 0.15),
    inset 0 1px 0 rgba(255, 255, 255, 0.12);
}

.logo-mark {
  display: flex;
  justify-content: center;
  margin-bottom: 12px;
  filter: drop-shadow(0 0 12px rgba(var(--tm-color-primary-rgb), 0.6));
  animation: logo-pulse 4s ease-in-out infinite;
}

@keyframes logo-pulse {
  0%, 100% { filter: drop-shadow(0 0 12px rgba(var(--tm-color-primary-rgb), 0.6)); }
  50% { filter: drop-shadow(0 0 20px rgba(var(--tm-color-primary-rgb), 0.9)); }
}

.login-header {
  text-align: center;
  margin-bottom: 36px;
}

.title {
  font-size: 34px;
  font-weight: 800;
  letter-spacing: -0.02em;
  color: var(--tm-text-primary, #fafafa);
  margin: 0 0 8px 0;
  background: linear-gradient(135deg,
    var(--tm-color-primary),
    #ec4899 50%,
    var(--tm-color-primary-dark));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  text-shadow: 0 0 40px rgba(var(--tm-color-primary-rgb), 0.4);
}

.subtitle {
  font-size: 13px;
  color: var(--tm-text-secondary, #71717a);
  margin: 0;
  letter-spacing: 0.04em;
}

.login-form {
  margin-bottom: 24px;

  :deep(.el-input__wrapper) {
    background: rgba(0, 0, 0, 0.3) !important;
    border-radius: 12px !important;
    padding: 4px 14px;
    transition: all 0.3s ease;
  }

  :deep(.el-input__wrapper.is-focus) {
    box-shadow: 0 0 0 1px var(--tm-color-primary),
                0 0 24px rgba(var(--tm-color-primary-rgb), 0.3) !important;
  }
}

.login-btn {
  width: 100%;
  height: 48px;
  border-radius: 12px !important;
  font-size: 15px;
  font-weight: 600;
  letter-spacing: 0.1em;
  background: linear-gradient(135deg,
    var(--tm-color-primary),
    var(--tm-color-primary-dark)) !important;
  border: none !important;
  box-shadow: 0 8px 24px rgba(var(--tm-color-primary-rgb), 0.4),
              inset 0 1px 0 rgba(255, 255, 255, 0.2) !important;
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 12px 32px rgba(var(--tm-color-primary-rgb), 0.55) !important;
  }

  &:active {
    transform: translateY(0);
  }
}

.btn-arrow {
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.login-btn:hover .btn-arrow {
  transform: translateX(4px);
}

.login-footer {
  text-align: center;
  font-size: 13px;
  color: var(--tm-text-secondary);
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 8px;
}

.footer-link {
  color: var(--tm-color-primary, #ec4899);
  text-decoration: none;
  font-weight: 500;
  transition: all 0.2s ease;
  position: relative;

  &::after {
    content: '';
    position: absolute;
    left: 0;
    bottom: -2px;
    width: 0;
    height: 1px;
    background: var(--tm-color-primary);
    transition: width 0.3s ease;
  }

  &:hover {
    opacity: 1;
    &::after { width: 100%; }
  }
}

.footer-divider {
  color: var(--tm-text-secondary);
  opacity: 0.4;
}

.demo-account {
  margin-top: 24px;

  .account-item {
    text-align: center;
    font-size: 12px;
    color: var(--tm-text-secondary);
    padding: 6px 0;
    font-family: 'JetBrains Mono', monospace;
  }
}

.brand-strip {
  position: absolute;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  font-size: 11px;
  color: var(--tm-text-secondary);
  opacity: 0.5;
  letter-spacing: 0.08em;
  display: flex;
  gap: 8px;
  align-items: center;
  z-index: 2;
}

.dot { opacity: 0.6; }

@media (max-width: 768px) {
  .login-card {
    padding: 36px 24px;
    border-radius: 18px;
  }
  .title { font-size: 28px; }
  .brand-strip { font-size: 10px; }
}

@media (prefers-reduced-motion: reduce) {
  .login-card,
  .logo-mark {
    animation: none !important;
    transition: none !important;
  }
}
</style>
