<template>
  <div class="settings-page-dark">
    <div class="page-header">
      <h1 class="page-title">系统设置</h1>
    </div>

    <el-tabs v-model="activeTab" type="card" class="dark-tabs">
      <el-tab-pane label="基础设置" name="basic">
        <div class="settings-card">
          <el-form :model="basicSettings" label-width="120px">
            <el-form-item label="站点名称">
              <el-input v-model="basicSettings.siteName" class="dark-input" />
            </el-form-item>
            <el-form-item label="站点描述">
              <el-input v-model="basicSettings.siteDescription" type="textarea" :rows="3" class="dark-input" />
            </el-form-item>
            <el-form-item label="站点LOGO">
              <el-upload
                class="avatar-uploader"
                action="https://run.mocky.io/v3/9d059bf9-4660-45f2-925d-ce80ad6c4d15"
                :show-file-list="false"
                :on-success="handleLogoSuccess"
                :before-upload="beforeLogoUpload"
              >
                <img v-if="basicSettings.siteLogo" :src="basicSettings.siteLogo" class="avatar" />
                <el-icon v-else class="avatar-uploader-icon"><Plus /></el-icon>
              </el-upload>
            </el-form-item>
            <el-form-item label="联系邮箱">
              <el-input v-model="basicSettings.contactEmail" class="dark-input" />
            </el-form-item>
            <el-form-item label="备案号">
              <el-input v-model="basicSettings.icp" class="dark-input" />
            </el-form-item>
            <el-form-item label="是否开放注册">
              <el-switch v-model="basicSettings.allowRegister" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="saveBasicSettings" class="btn-primary">保存设置</el-button>
            </el-form-item>
          </el-form>
        </div>
      </el-tab-pane>

      <el-tab-pane label="邮件通知" name="email">
        <div class="settings-card">
          <el-alert
            title="邮件通知配置"
            type="info"
            description="配置 SMTP 邮件发送，自动化测试场景执行完成后会自动发送测试结果通知邮件"
            :closable="false"
            style="margin-bottom: 20px"
          />
          <el-form :model="emailSettings" label-width="140px">
            <el-form-item label="启用邮件通知">
              <el-switch v-model="emailSettings.enabled" />
            </el-form-item>
            <el-form-item label="SMTP服务器地址">
              <el-input v-model="emailSettings.smtpHost" placeholder="例如: smtp.gmail.com 或 smtp.qq.com" class="dark-input" />
            </el-form-item>
            <el-form-item label="SMTP端口">
              <el-input v-model.number="emailSettings.smtpPort" type="number" placeholder="通常 465(SSL) 或 587(TLS)" class="dark-input" />
            </el-form-item>
            <el-form-item label="SMTP用户名">
              <el-input v-model="emailSettings.smtpUser" placeholder="通常就是你的邮箱地址" class="dark-input" />
            </el-form-item>
            <el-form-item label="SMTP密码/授权码">
              <el-input v-model="emailSettings.smtpPassword" type="password" placeholder="邮箱密码或第三方客户端授权码" class="dark-input" />
            </el-form-item>
            <el-form-item label="发件人邮箱">
              <el-input v-model="emailSettings.fromEmail" placeholder="显示的发件人邮箱" class="dark-input" />
            </el-form-item>
            <el-form-item label="管理员收件邮箱">
              <el-input v-model="emailSettings.adminToEmail" placeholder="场景执行结果发送到此邮箱" class="dark-input" />
            </el-form-item>
            <el-form-item label="启用SSL">
              <el-switch v-model="emailSettings.enableSSL" />
              <div class="form-hint">大部分公共邮箱服务商通常启用 SSL，端口一般为 465</div>
            </el-form-item>
            <el-form-item label="站点基础URL">
              <el-input v-model="emailSettings.baseUrl" placeholder="用于生成完整的报告链接，例如 http://your-domain.com" class="dark-input" />
            </el-form-item>
            <el-form-item label="测试收件邮箱">
              <el-input v-model="emailSettings.testToEmail" placeholder="输入你的邮箱来接收测试邮件" class="dark-input" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="saveEmailSettings" :loading="emailSaving" class="btn-primary">
                保存配置
              </el-button>
              <el-button style="margin-left: 10px;" @click="testEmail" :loading="emailTesting" class="btn-outline">
                发送测试邮件
              </el-button>
            </el-form-item>
          </el-form>
        </div>
      </el-tab-pane>

      <el-tab-pane label="存储设置" name="storage">
        <div class="settings-card">
          <el-form :model="storageSettings" label-width="120px">
            <el-form-item label="存储方式">
              <el-radio-group v-model="storageSettings.storageType" class="dark-radio">
                <el-radio value="local" label="local">本地存储</el-radio>
                <el-radio value="oss" label="oss">阿里云OSS</el-radio>
                <el-radio value="cos" label="cos">腾讯云COS</el-radio>
              </el-radio-group>
            </el-form-item>
            <template v-if="storageSettings.storageType !== 'local'">
              <el-form-item label="AccessKey">
                <el-input v-model="storageSettings.accessKey" class="dark-input" />
              </el-form-item>
              <el-form-item label="SecretKey">
                <el-input v-model="storageSettings.secretKey" type="password" class="dark-input" />
              </el-form-item>
              <el-form-item label="Bucket名称">
                <el-input v-model="storageSettings.bucket" class="dark-input" />
              </el-form-item>
              <el-form-item label="区域">
                <el-input v-model="storageSettings.region" class="dark-input" />
              </el-form-item>
              <el-form-item label="访问域名">
                <el-input v-model="storageSettings.domain" class="dark-input" />
              </el-form-item>
            </template>
            <el-form-item>
              <el-button type="primary" @click="saveStorageSettings" class="btn-primary">保存设置</el-button>
            </el-form-item>
          </el-form>
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import axios from 'axios'

// Add token interceptor
const apiRequest = axios.create({
  baseURL: '/api',
  timeout: 10000
})

apiRequest.interceptors.request.use(
  config => {
    const token = localStorage.getItem('admin_token') || localStorage.getItem('token')
    if (token && token !== 'undefined' && token !== 'null' && token !== '[object Object]') {
      config.headers['Authorization'] = `Bearer ${token}`
    }
    return config
  },
  error => Promise.reject(error)
)

const activeTab = ref('basic')
const emailSaving = ref(false)
const emailTesting = ref(false)

const basicSettings = reactive({
  siteName: 'TestMaster 测试工程师成长平台',
  siteDescription: '从小白到测试架构师的完整学习路径，一站式提升测试能力',
  siteLogo: '',
  contactEmail: 'contact@testmaster.com',
  icp: '粤ICP备12345678号',
  allowRegister: true
})

const emailSettings = reactive({
  enabled: false,
  smtpHost: 'smtp.gmail.com',
  smtpPort: 465,
  smtpUser: '',
  smtpPassword: '',
  fromEmail: '',
  adminToEmail: '',
  enableSSL: true,
  baseUrl: '',
  testToEmail: ''
})

const storageSettings = reactive({
  storageType: 'local',
  accessKey: '',
  secretKey: '',
  bucket: '',
  region: '',
  domain: ''
})

const handleLogoSuccess = (res) => {
  basicSettings.siteLogo = res.data.url
  ElMessage.success('LOGO上传成功')
}

const beforeLogoUpload = (file) => {
  const isImage = file.type.startsWith('image/')
  const isLt2M = file.size / 1024 / 1024 < 2

  if (!isImage) {
    ElMessage.error('上传的图片只能是 JPG/PNG 格式!')
    return false
  }
  if (!isLt2M) {
    ElMessage.error('上传的图片大小不能超过 2MB!')
    return false
  }
  return true
}

const saveBasicSettings = () => {
  ElMessage.success('基础设置保存成功')
}

const loadEmailSettings = async () => {
  try {
    const res = await apiRequest.get('/auto-test/email/config')
    if (res.data) {
      Object.assign(emailSettings, res.data)
    }
  } catch (error) {
    console.error('加载邮件配置失败:', error)
  }
}

const saveEmailSettings = async () => {
  emailSaving.value = true
  try {
    await apiRequest.post('/auto-test/email/config', emailSettings)
    ElMessage.success('邮件配置保存成功')
  } catch (error) {
    ElMessage.error('保存失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    emailSaving.value = false
  }
}

const testEmail = async () => {
  if (!emailSettings.testToEmail) {
    ElMessage.warning('请输入测试收件邮箱')
    return
  }
  emailTesting.value = true
  try {
    await apiRequest.post('/auto-test/email/test', {
      to_email: emailSettings.testToEmail
    })
    ElMessage.success('测试邮件发送成功，请查收')
  } catch (error) {
    ElMessage.error('发送失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    emailTesting.value = false
  }
}

const saveStorageSettings = () => {
  ElMessage.success('存储设置保存成功')
}

onMounted(() => {
  loadEmailSettings()
})
</script>

<style scoped>
.settings-page-dark {
  width: 100%;
}

.page-header {
  margin-bottom: 20px;
}

.page-title {
  margin: 0;
  font-size: 28px;
  font-weight: 700;
  color: var(--tm-text-primary);
  letter-spacing: 0.5px;
}

.dark-tabs :deep(.el-tabs__header) {
  border-bottom: 1px solid #444;
}

.dark-tabs :deep(.el-tabs__nav-wrap::after) {
  background-color: #444;
}

.dark-tabs :deep(.el-tabs__item) {
  color: #a0a0a0;
}

.dark-tabs :deep(.el-tabs__item.is-active) {
  color: #00b4d8;
}

.dark-tabs :deep(.el-tabs__active-bar) {
  background-color: #00b4d8;
}

.settings-card {
  background: var(--tm-card-bg);
  padding: 30px;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
  margin-top: 20px;
  border: var(--tm-card-border);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
}

.avatar-uploader {
  :deep(.el-upload) {
    border: 1px dashed #555;
    border-radius: 6px;
    cursor: pointer;
    position: relative;
    overflow: hidden;
    transition: all 0.3s;
    background: #363636;
  }

  :deep(.el-upload:hover) {
    border-color: #00b4d8;
  }

  .avatar-uploader-icon {
    font-size: 28px;
    color: #8c939d;
    width: 120px;
    height: 120px;
    text-align: center;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .avatar {
    width: 120px;
    height: 120px;
    display: block;
    object-fit: cover;
    border-radius: 6px;
  }
}

.form-hint {
  margin-top: 6px;
  font-size: 12px;
  color: #909399;
  line-height: 1.5;
  color: #a0a0a0;
}

.dark-input :deep(.el-input__wrapper) {
  background: #3d3d3d;
  box-shadow: 0 0 0 1px #4a4a4a inset;
  border-radius: 6px;
}

.dark-input :deep(.el-input__inner) {
  color: #e0e0e0;
}

.btn-primary {
  background: linear-gradient(135deg, #0f766e, #00b4d8);
  border: none;
  box-shadow: 0 2px 10px rgba(0, 180, 216, 0.3);
}

.btn-primary:hover {
  background: linear-gradient(135deg, #0d9488, #0096c7);
  box-shadow: 0 4px 15px rgba(0, 180, 216, 0.4);
}

.btn-outline {
  color: #00b4d8;
  border: 1px solid #00b4d8;
  background: transparent;
}

.btn-outline:hover {
  background: rgba(0, 180, 216, 0.1);
}

.dark-radio :deep(.el-radio__label) {
  color: #e0e0e0;
}

.dark-radio :deep(.el-radio__input.is-checked .el-radio__inner) {
  background: #00b4d8;
  border-color: #00b4d8;
}
</style>
