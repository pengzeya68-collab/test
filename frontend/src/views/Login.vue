<template>
  <div class="login-page" data-testid="desktop-login-page">
    <AuroraBackground />

    <div class="login-card">
      <div class="login-header">
        <div class="logo-mark" aria-hidden="true">
          <svg width="40" height="40" viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">
            <defs>
              <linearGradient id="desktopLoginLogo" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stop-color="var(--tm-color-primary)" />
                <stop offset="100%" stop-color="var(--tm-color-primary-dark)" />
              </linearGradient>
            </defs>
            <path d="M14 22 L50 22 L50 28 L38 28 L38 50 L26 50 L26 28 L14 28 Z" fill="url(#desktopLoginLogo)" />
          </svg>
        </div>
        <div class="brand">TestMaster</div>
        <h1>桌面版登录</h1>
        <p>登录后进入自动化测试工作台，保留本地服务检测与执行引擎能力</p>
      </div>

      <el-form ref="formRef" :model="form" label-position="top" class="login-form" @submit.prevent="handleLogin">
        <el-form-item
          label="服务地址"
          prop="serverUrl"
          :rules="[{ required: true, message: '请输入服务地址', trigger: 'blur' }]"
        >
          <el-input
            v-model="form.serverUrl"
            placeholder="http://127.0.0.1:5001"
            size="large"
            aria-label="服务地址"
            @change="checkService"
          />
          <div class="server-hint">填写服务根地址即可；粘贴“/api/health”等检测地址时会自动识别。</div>
          <div class="service-state" :class="serviceState" role="status">
            <i aria-hidden="true"></i>
            <span>{{ serviceText }}</span>
            <el-button
              v-if="serviceState !== 'online'"
              link
              type="primary"
              :loading="serviceState === 'checking'"
              @click="checkService"
            >
              重新检测
            </el-button>
          </div>
          <div v-if="localCredentialsReady" class="local-credentials-hint">
            已检测到本机托管服务的初始管理员凭据。
            <el-button link type="primary" @click="fillLocalCredentials">填入本机凭据</el-button>
          </div>
        </el-form-item>

        <el-form-item
          label="用户名"
          prop="username"
          :rules="[{ required: true, message: '请输入用户名', trigger: 'blur' }]"
        >
          <el-input
            v-model="form.username"
            placeholder="请输入用户名"
            size="large"
            aria-label="用户名"
            autocomplete="username"
          >
            <template #prefix><el-icon><User /></el-icon></template>
          </el-input>
        </el-form-item>

        <el-form-item
          label="密码"
          prop="password"
          :rules="[{ required: true, message: '请输入密码', trigger: 'blur' }]"
        >
          <el-input
            v-model="form.password"
            type="password"
            show-password
            placeholder="请输入密码"
            size="large"
            aria-label="密码"
            autocomplete="current-password"
            @keyup.enter="handleLogin"
          >
            <template #prefix><el-icon><Lock /></el-icon></template>
          </el-input>
        </el-form-item>

        <el-button
          type="primary"
          size="large"
          class="submit-btn"
          :loading="loading"
          :disabled="serviceState !== 'online'"
          @click="handleLogin"
        >
          登录
        </el-button>
      </el-form>
    </div>

    <div class="brand-strip">
      <span>© 2026 TestMaster Desktop</span>
      <span class="dot">·</span>
      <span>自动化测试工作台</span>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'
import request, { setToken } from '@/utils/request'
import { useUserStore } from '@/stores/user'
import { getServerUrl, setServerUrl } from '@/utils/server-config'
import AuroraBackground from '@/components/base/AuroraBackground.vue'

const router = useRouter()
const userStore = useUserStore()
const formRef = ref()
const loading = ref(false)
const serviceState = ref('checking')
const form = ref({ serverUrl: getServerUrl(), username: '', password: '' })
let servicePollTimer = null
const serviceDetail = ref('')
const localCredentials = ref(null)
const localCredentialsReady = computed(() => !!localCredentials.value)
const serviceText = computed(() => ({
  checking: '正在检测服务…',
  online: '服务连接正常',
  offline: serviceDetail.value || '服务暂时无法连接，请确认地址和网络后重试',
}[serviceState.value]))

const checkService = async () => {
  serviceState.value = 'checking'
  serviceDetail.value = ''
  let serverUrl
  try {
    serverUrl = setServerUrl(form.value.serverUrl)
    form.value.serverUrl = serverUrl
    const response = await fetch(`${serverUrl}/api/ui-automation/health`, { signal: AbortSignal.timeout(2500) })
    const body = response.ok ? await response.json() : null
    if (body?.status === 'ok' && body?.enabled === true) {
      serviceState.value = 'online'
      await loadLocalCredentials()
    } else {
      serviceDetail.value = response.ok ? '服务未启用 UI 自动化模块' : `服务响应异常（HTTP ${response.status}）`
      serviceState.value = 'offline'
    }
  } catch (error) {
    console.warn('[DesktopLogin] Service check failed:', error)
    serviceDetail.value = error?.name === 'TimeoutError'
      ? '检测超时，请确认服务地址和网络'
      : (error?.message || '服务暂时无法连接，请确认地址和网络后重试')
    serviceState.value = 'offline'
  }
  return serviceState.value === 'online'
}

const loadLocalCredentials = async () => {
  if (!window.testmaster?.appInfo?.localCredentials || localCredentials.value) return
  try {
    localCredentials.value = await window.testmaster.appInfo.localCredentials()
    // Do not replace values that an operator has already entered.
    if (!form.value.username) form.value.username = localCredentials.value.username
    if (!form.value.password) form.value.password = localCredentials.value.password
  } catch {
    // A remote service or a service that is still starting has no local
    // credential capability. The ordinary login flow remains available.
  }
}

const fillLocalCredentials = () => {
  if (!localCredentials.value) return
  form.value.username = localCredentials.value.username
  form.value.password = localCredentials.value.password
}

const waitForLocalService = async () => {
  const deadline = Date.now() + 45000
  while (Date.now() < deadline && serviceState.value !== 'online') {
    await checkService()
    if (serviceState.value === 'online') return
    await new Promise(resolve => { servicePollTimer = setTimeout(resolve, 800) })
  }
}

const handleLogin = async () => {
  try {
    await formRef.value?.validate()
  } catch {
    return
  }

  loading.value = true
  try {
    const serverUrl = setServerUrl(form.value.serverUrl)
    form.value.serverUrl = serverUrl
    const res = await request.post('/auth/login', { username: form.value.username, password: form.value.password })
    userStore.setLogin(res.access_token, res.user)
    setToken(res.access_token)
    ElMessage.success('登录成功')
    router.push('/')
  } catch (error) {
    ElMessage.error(error.message || '登录失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  waitForLocalService()
})
onBeforeUnmount(() => { if (servicePollTimer) clearTimeout(servicePollTimer) })
</script>

<style scoped lang="scss">
.login-page {
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
  max-width: 460px;
  padding: 40px 36px;
  background: var(--tm-glass-bg, rgba(22, 30, 46, 0.88));
  border: 1px solid rgba(var(--tm-color-primary-rgb), 0.28);
  border-radius: 14px;
  box-shadow: var(--tm-shadow-card), 0 0 0 1px rgba(255, 255, 255, 0.04) inset;
  backdrop-filter: blur(18px) saturate(150%);
  -webkit-backdrop-filter: blur(18px) saturate(150%);
}

.login-header {
  margin-bottom: 24px;
  text-align: center;
}

.logo-mark {
  display: flex;
  justify-content: center;
  margin-bottom: 10px;
}

.brand {
  margin-bottom: 8px;
  font-size: 28px;
  font-weight: 800;
  letter-spacing: -0.02em;
  background: var(--tm-gradient-brand);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}

.login-header h1 {
  margin: 0 0 8px;
  color: var(--tm-text-primary);
  font-size: 20px;
  font-weight: 700;
}

.login-header p {
  margin: 0;
  color: var(--tm-text-secondary);
  font-size: 13px;
  line-height: 1.6;
}

.login-form :deep(.el-form-item__label) {
  color: var(--tm-text-secondary);
  font-weight: 500;
}

.login-form :deep(.el-input__wrapper) {
  background: var(--tm-input-bg) !important;
  border: 1px solid var(--tm-input-border) !important;
  border-radius: 10px !important;
}

.submit-btn {
  width: 100%;
  height: 46px;
  margin-top: 4px;
  border-radius: 10px !important;
  font-weight: 600;
}

.server-hint {
  margin-top: 6px;
  color: var(--tm-text-muted, var(--tm-text-secondary));
  font-size: 12px;
  line-height: 1.5;
}

.service-state {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  width: 100%;
  margin-top: 10px;
  color: var(--tm-text-secondary);
  font-size: 12px;
}

.service-state i {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--tm-color-warning);
}

.service-state.online {
  color: var(--tm-color-success);
}
.service-state.online i {
  background: var(--tm-color-success);
}
.service-state.offline {
  color: var(--tm-color-danger);
}
.service-state.offline i {
  background: var(--tm-color-danger);
}
.service-state.checking i {
  background: var(--tm-color-warning);
}

.local-credentials-hint {
  margin-top: 8px;
  color: var(--tm-text-secondary);
  font-size: 12px;
  line-height: 1.5;
}

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
  opacity: 0.55;
  transform: translateX(-50%);
}

.dot { opacity: 0.6; }

@media (max-width: 480px) {
  .login-card {
    padding: 28px 20px;
  }
}
</style>
