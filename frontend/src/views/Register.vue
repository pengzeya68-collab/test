<template>
  <div class="register-container" @mousemove="onContainerMove">
    <AuroraBackground />

    <div class="register-card" ref="cardRef" @mousemove="onCardMove" @mouseleave="onCardLeave">
      <div class="register-header">
        <div class="logo-mark">
          <svg width="44" height="44" viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">
            <defs>
              <linearGradient id="regLogoGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stop-color="var(--tm-color-primary)"/>
                <stop offset="50%" stop-color="#ec4899"/>
                <stop offset="100%" stop-color="#00f2fe"/>
              </linearGradient>
            </defs>
            <path d="M14 22 L50 22 L50 28 L38 28 L38 50 L26 50 L26 28 L14 28 Z" fill="url(#regLogoGrad)"/>
          </svg>
        </div>
        <h1 class="title">创建账号</h1>
        <p class="subtitle">加入 TestMaster，开启测试工程师成长之路</p>
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
          <el-input v-model="registerForm.username" placeholder="用户名" size="large">
            <template #prefix><el-icon><User /></el-icon></template>
          </el-input>
        </el-form-item>

        <el-form-item
          prop="email"
          :rules="[
            { required: true, message: '请输入邮箱', trigger: 'blur' },
            { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
          ]"
        >
          <el-input v-model="registerForm.email" placeholder="邮箱" size="large">
            <template #prefix><el-icon><Message /></el-icon></template>
          </el-input>
        </el-form-item>

        <el-form-item
          prop="phone"
          :rules="[{ pattern: /^1[3-9]\d{9}$/, message: '请输入正确的11位手机号', trigger: 'blur' }]"
        >
          <el-input v-model="registerForm.phone" placeholder="手机号（可选）" size="large">
            <template #prefix><el-icon><Phone /></el-icon></template>
          </el-input>
        </el-form-item>

        <el-form-item
          prop="password"
          :rules="[
            { required: true, message: '请输入密码', trigger: 'blur' },
            { min: 8, max: 32, message: '密码长度在 8 到 32 个字符', trigger: 'blur' },
            { validator: validatePasswordStrength, trigger: 'blur' }
          ]"
        >
          <el-input
            v-model="registerForm.password"
            type="password"
            placeholder="密码（至少8位，需含字母和数字）"
            size="large"
            @input="onPasswordInput"
          >
            <template #prefix><el-icon><Lock /></el-icon></template>
          </el-input>
        </el-form-item>

        <div class="password-strength" v-if="registerForm.password">
          <div class="strength-bars">
            <span v-for="i in 4" :key="i" class="bar" :class="{ active: i <= passwordStrength.score, [`level-${passwordStrength.level}`]: i <= passwordStrength.score }"></span>
          </div>
          <span class="strength-label" :class="`level-${passwordStrength.level}`">{{ passwordStrength.text }}</span>
        </div>

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
            <template #prefix><el-icon><Lock /></el-icon></template>
          </el-input>
        </el-form-item>

        <el-form-item>
          <el-button
            v-ripple
            type="primary"
            size="large"
            :loading="loading"
            class="register-btn"
            @click="handleRegister"
          >
            <span class="btn-text">创建账号</span>
            <span class="btn-arrow">→</span>
          </el-button>
        </el-form-item>
      </el-form>

      <div class="register-footer">
        <span>已有账号？</span>
        <el-link type="primary" @click="goToLogin" class="footer-link">立即登录</el-link>
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
import { ref, reactive, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { User, Lock, Message, Phone } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import request, { setToken } from '@/utils/request'
import { useUserStore } from '@/stores/user'
import AuroraBackground from '@/components/base/AuroraBackground.vue'

const router = useRouter()
const userStore = useUserStore()
const registerFormRef = ref(null)
const loading = ref(false)
const cardRef = ref(null)

const registerForm = ref({
  username: '',
  email: '',
  phone: '',
  password: '',
  confirmPassword: ''
})

const passwordStrength = reactive({
  score: 0,
  level: 'weak',
  text: ''
})

const onPasswordInput = (val) => {
  let score = 0
  if (!val) {
    passwordStrength.score = 0
    passwordStrength.level = 'weak'
    passwordStrength.text = ''
    return
  }
  if (val.length >= 8) score++
  if (val.length >= 12) score++
  if (/[A-Z]/.test(val) && /[a-z]/.test(val)) score++
  if (/\d/.test(val) && /[!@#$%^&*(),.?":{}|<>_]/.test(val)) score++

  passwordStrength.score = score
  if (score <= 1) {
    passwordStrength.level = 'weak'
    passwordStrength.text = '弱'
  } else if (score === 2) {
    passwordStrength.level = 'medium'
    passwordStrength.text = '中'
  } else if (score === 3) {
    passwordStrength.level = 'strong'
    passwordStrength.text = '强'
  } else {
    passwordStrength.level = 'excellent'
    passwordStrength.text = '极强'
  }
}

const codeCountdown = ref(0)
let codeTimer = null

const sendCode = () => {
  if (codeCountdown.value > 0) return
  if (!registerForm.value.phone) {
    ElMessage.warning('请先输入手机号')
    return
  }
  if (!/^1[3-9]\d{9}$/.test(registerForm.value.phone)) {
    ElMessage.warning('请输入正确的手机号')
    return
  }
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

onBeforeUnmount(() => {
  if (codeTimer) {
    clearInterval(codeTimer)
    codeTimer = null
  }
})

const onCardMove = (e) => {
  if (!cardRef.value) return
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return
  const rect = cardRef.value.getBoundingClientRect()
  const x = (e.clientX - rect.left) / rect.width - 0.5
  const y = (e.clientY - rect.top) / rect.height - 0.5
  cardRef.value.style.transform = `perspective(1200px) rotateY(${x * 5}deg) rotateX(${-y * 5}deg) translateZ(0)`
}

const onCardLeave = () => {
  if (!cardRef.value) return
  cardRef.value.style.transform = ''
}

const onContainerMove = () => {}

const validateConfirmPassword = (rule, value, callback) => {
  if (value !== registerForm.value.password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const validatePasswordStrength = (rule, value, callback) => {
  if (!value) return callback()
  if (!/[A-Za-z]/.test(value) || !/\d/.test(value)) {
    callback(new Error('密码必须同时包含字母和数字'))
  } else {
    callback()
  }
}

const handleRegister = async () => {
  if (!registerFormRef.value) return
  try {
    await registerFormRef.value.validate()
  } catch {
    return
  }
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

const goToLogin = () => {
  router.push('/login')
}
</script>

<style scoped lang="scss">
.register-container {
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

.register-card {
  position: relative;
  z-index: 2;
  background: var(--tm-glass-bg, rgba(24, 24, 27, 0.75));
  backdrop-filter: blur(24px) saturate(180%);
  -webkit-backdrop-filter: blur(24px) saturate(180%);
  border-radius: 24px;
  padding: 44px 44px;
  width: 100%;
  max-width: 480px;
  box-shadow:
    0 24px 80px rgba(0, 0, 0, 0.5),
    0 0 0 1px rgba(255, 255, 255, 0.06),
    inset 0 1px 0 rgba(255, 255, 255, 0.08);
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1), box-shadow 0.3s ease;
  transform-style: preserve-3d;
  will-change: transform;
}

.register-card::before {
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

.register-card:focus-within {
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

.register-header {
  text-align: center;
  margin-bottom: 32px;
}

.title {
  font-size: 30px;
  font-weight: 800;
  letter-spacing: -0.02em;
  color: var(--tm-text-primary, #fafafa);
  margin: 0 0 8px 0;
  background: linear-gradient(135deg, var(--tm-color-primary), #ec4899 50%, var(--tm-color-primary-dark));
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

.register-form {
  margin-bottom: 20px;

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

.password-strength {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: -4px 0 14px;
  padding: 0 2px;
}

.strength-bars {
  display: flex;
  gap: 4px;
  flex: 1;
}

.bar {
  height: 4px;
  flex: 1;
  border-radius: 2px;
  background: rgba(255, 255, 255, 0.08);
  transition: all 0.3s ease;
}

.bar.active.level-weak { background: #ef4444; box-shadow: 0 0 8px rgba(239, 68, 68, 0.5); }
.bar.active.level-medium { background: #f59e0b; box-shadow: 0 0 8px rgba(245, 158, 11, 0.5); }
.bar.active.level-strong { background: #10b981; box-shadow: 0 0 8px rgba(16, 185, 129, 0.5); }
.bar.active.level-excellent { background: var(--tm-color-primary); box-shadow: 0 0 8px rgba(var(--tm-color-primary-rgb), 0.6); }

.strength-label {
  font-size: 11px;
  font-weight: 600;
  min-width: 32px;
  text-align: right;
}

.strength-label.level-weak { color: #ef4444; }
.strength-label.level-medium { color: #f59e0b; }
.strength-label.level-strong { color: #10b981; }
.strength-label.level-excellent { color: var(--tm-color-primary); }

.register-btn {
  width: 100%;
  height: 48px;
  border-radius: 12px !important;
  font-size: 15px;
  font-weight: 600;
  letter-spacing: 0.08em;
  background: linear-gradient(135deg, var(--tm-color-primary), var(--tm-color-primary-dark)) !important;
  border: none !important;
  box-shadow: 0 8px 24px rgba(var(--tm-color-primary-rgb), 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.2) !important;
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

  &:active { transform: translateY(0); }
}

.btn-arrow {
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.register-btn:hover .btn-arrow {
  transform: translateX(4px);
}

.register-footer {
  text-align: center;
  font-size: 13px;
  color: var(--tm-text-secondary);
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 8px;

  :deep(.footer-link) {
    color: var(--tm-color-primary);
    font-weight: 500;
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
  .register-card {
    padding: 32px 22px;
    border-radius: 18px;
  }
  .title { font-size: 24px; }
  .brand-strip { font-size: 10px; }
}

@media (prefers-reduced-motion: reduce) {
  .register-card,
  .logo-mark {
    animation: none !important;
    transition: none !important;
  }
}
</style>
