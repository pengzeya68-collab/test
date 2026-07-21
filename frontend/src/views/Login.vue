<template>
  <div class="login-page">
    <div class="login-card">
      <div class="login-header">
        <div class="brand">TestMaster</div>
        <h1>{{ isDesktopBuild ? '桌面版登录' : '用户登录' }}</h1>
        <p>{{ isDesktopBuild ? '登录后直接进入自动化测试工作台' : '登录后继续你的测试学习与实践' }}</p>
      </div>

      <el-form ref="formRef" :model="form" label-position="top" @submit.prevent="handleLogin">
        <el-form-item v-if="isDesktopBuild" label="服务地址" prop="serverUrl" :rules="[{ required: true, message: '请输入服务地址', trigger: 'blur' }]">
          <el-input v-model="form.serverUrl" placeholder="http://127.0.0.1:5001" size="large" @change="checkService" />
          <div class="server-hint">填写服务根地址即可；粘贴“/api/health”等检测地址时会自动识别。</div>
          <div class="service-state" :class="serviceState">
            <i></i>{{ serviceText }}
            <el-button v-if="serviceState !== 'online'" link type="primary" :loading="serviceState === 'checking'" @click="checkService">重新检测</el-button>
          </div>
        </el-form-item>
        <el-form-item label="用户名" prop="username" :rules="[{ required: true, message: '请输入用户名', trigger: 'blur' }]">
          <el-input v-model="form.username" placeholder="例如：admin" size="large" />
        </el-form-item>

        <el-form-item label="密码" prop="password" :rules="[{ required: true, message: '请输入密码', trigger: 'blur' }]">
          <el-input v-model="form.password" type="password" show-password placeholder="请输入密码" size="large" @keyup.enter="handleLogin" />
        </el-form-item>

        <el-button type="primary" size="large" class="submit-btn" :loading="loading" :disabled="isDesktopBuild && serviceState !== 'online'" @click="handleLogin">
          登录
        </el-button>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import request, { setToken } from '@/utils/request'
import { useUserStore } from '@/stores/user'
import { getServerUrl, setServerUrl } from '@/utils/server-config'
import { isDesktopBuild } from '@/utils/build-target'

const router = useRouter()
const userStore = useUserStore()
const formRef = ref()
const loading = ref(false)
const serviceState = ref('checking')
const form = ref({ serverUrl: getServerUrl(), username: '', password: '' })
let servicePollTimer = null
const serviceDetail = ref('')
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
    if (isDesktopBuild) {
      const serverUrl = setServerUrl(form.value.serverUrl)
      form.value.serverUrl = serverUrl
    }
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
  if (isDesktopBuild) waitForLocalService()
})
onBeforeUnmount(() => { if (servicePollTimer) clearTimeout(servicePollTimer) })
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #eef3f0;
  padding: 24px;
}
.login-card {
  width: 100%;
  max-width: 460px;
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid rgba(203, 213, 225, 0.7);
  border-radius: 6px;
  padding: 32px;
  box-shadow: 0 24px 60px rgba(15, 23, 42, 0.12);
}
.login-header {
  margin-bottom: 20px;
}
.brand {
  font-size: 28px;
  font-weight: 800;
  color: #28724f;
  margin-bottom: 12px;
}
.login-header h1 {
  margin: 0 0 8px;
  font-size: 28px;
}
.login-header p {
  margin: 0;
  color: #64748b;
}
.submit-btn {
  width: 100%;
  margin-top: 8px;
}
.server-hint { margin-top: 5px; color: #76827b; font-size: 12px; line-height: 1.5; }
.service-state { display: flex; align-items: center; gap: 7px; width: 100%; margin-top: 8px; color: #64748b; font-size: 12px; }
.service-state i { width: 7px; height: 7px; border-radius: 50%; background: #d97706; }
.service-state.online { color: #15803d; }
.service-state.online i { background: #16a34a; }
.service-state.offline { color: #b91c1c; }
.service-state.offline i { background: #dc2626; }
</style>





