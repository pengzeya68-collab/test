<template>
  <div class="profile-container">
    <div class="container">
      <div class="profile-card">
        <div class="profile-header">
          <h1 class="page-title">个人中心</h1>
        </div>
        
        <div class="profile-content">
          <!-- 基本信息 -->
          <el-card title="基本信息" style="margin-bottom: 20px;">
            <el-descriptions :column="2" border>
              <el-descriptions-item label="用户名">
                {{ userInfo?.username }}
              </el-descriptions-item>
              <el-descriptions-item label="邮箱">
                {{ userInfo?.email }}
              </el-descriptions-item>
              <el-descriptions-item label="手机号">
                {{ userInfo?.phone || '未绑定' }}
              </el-descriptions-item>
              <el-descriptions-item label="等级">
                Lv.{{ userInfo?.level || 1 }}
              </el-descriptions-item>
              <el-descriptions-item label="积分">
                {{ userInfo?.score || 0 }}
              </el-descriptions-item>
              <el-descriptions-item label="注册时间">
                {{ userInfo?.created_at || '' }}
              </el-descriptions-item>
            </el-descriptions>
          </el-card>
          
          <!-- 修改密码 -->
          <el-card title="修改密码">
            <el-form 
              ref="passwordFormRef" 
              :model="passwordForm" 
              label-width="120px"
              style="max-width: 500px;"
            >
              <el-form-item
                label="旧密码"
                prop="old_password"
                :rules="[
                  { required: true, message: '请输入旧密码', trigger: 'blur' }
                ]"
              >
                <el-input 
                  v-model="passwordForm.old_password" 
                  type="password" 
                  placeholder="请输入旧密码"
                />
              </el-form-item>
              
              <el-form-item
                label="新密码"
                prop="new_password"
                :rules="[
                  { required: true, message: '请输入新密码', trigger: 'blur' },
                  { min: 6, max: 32, message: '密码长度在 6 到 32 个字符', trigger: 'blur' }
                ]"
              >
                <el-input 
                  v-model="passwordForm.new_password" 
                  type="password" 
                  placeholder="请输入新密码"
                />
              </el-form-item>
              
              <el-form-item
                label="确认新密码"
                prop="confirm_password"
                :rules="[
                  { required: true, message: '请确认新密码', trigger: 'blur' },
                  { validator: validateConfirmPassword, trigger: 'blur' }
                ]"
              >
                <el-input 
                  v-model="passwordForm.confirm_password" 
                  type="password" 
                  placeholder="请再次输入新密码"
                  :disabled="!passwordForm.new_password"
                />
              </el-form-item>
              
              <el-form-item>
                <el-button type="primary" @click="handleChangePassword" :loading="loading">
                  修改密码
                </el-button>
              </el-form-item>
            </el-form>
          </el-card>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '@/utils/request'

const passwordFormRef = ref(null)
const loading = ref(false)
const userInfo = ref(null)

const passwordForm = ref({
  old_password: '',
  new_password: '',
  confirm_password: ''
})

const validateConfirmPassword = (rule, value, callback) => {
  if (value !== passwordForm.value.new_password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const fetchUserInfo = async () => {
  try {
    const res = await request.get('/profile')
    userInfo.value = res.user
  } catch (e) {
    console.error('获取用户信息失败:', e)
  }
}

const handleChangePassword = async () => {
  if (!passwordFormRef.value) return
  
  await passwordFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      try {
        await request.post('/change-password', {
          old_password: passwordForm.value.old_password,
          new_password: passwordForm.value.new_password
        })
        
        ElMessage.success('密码修改成功！请重新登录')
        
        // 清除登录信息，跳转到登录页
        localStorage.removeItem('token')
        localStorage.removeItem('user')
        window.location.href = '/#/login'
      } catch (error) {
        console.error('密码修改失败:', error)
        ElMessage.error(error.response?.data?.error || '密码修改失败')
      } finally {
        loading.value = false
        // 清空表单
        passwordForm.value = {
          old_password: '',
          new_password: '',
          confirm_password: ''
        }
      }
    }
  })
}

onMounted(() => {
  fetchUserInfo()
})
</script>

<style scoped>
.profile-container {
  padding: 40px 0;
  min-height: calc(100vh - 60px);
  background-color: #f5f7fa;
}

.container {
  width: 100%;
  max-width: none;
  margin: 0 auto;
  padding: 0 20px;
  box-sizing: border-box;
}

.profile-header {
  margin-bottom: 30px;
}

.page-title {
  font-size: 28px;
  font-weight: bold;
  color: #303133;
  margin: 0;
}

.profile-card {
  background: white;
  border-radius: 8px;
  padding: 30px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

@media (max-width: 768px) {
  .profile-container {
    padding: 20px 0;
  }
  
  .profile-card {
    padding: 20px;
  }
  
  .page-title {
    font-size: 24px;
  }
}
</style>
