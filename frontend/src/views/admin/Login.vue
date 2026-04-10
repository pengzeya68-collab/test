<template>
  <div class="admin-login">
    <div class="login-card">
      <div class="login-header">
        <h1>管理员登录</h1>
        <p>TestMaster 后台管理系统</p>
      </div>
      <el-form
        ref="loginFormRef"
        :model="loginForm"
        label-width="0px"
        class="login-form"
      >
        <el-form-item
          prop="username"
          :rules="[
            { required: true, message: '请输入管理员账号', trigger: 'blur' }
          ]"
        >
          <el-input
            v-model="loginForm.username"
            placeholder="管理员账号"
            size="large"
            prefix-icon="User"
          />
        </el-form-item>
        <el-form-item
          prop="password"
          :rules="[
            { required: true, message: '请输入密码', trigger: 'blur' }
          ]"
        >
          <el-input
            v-model="loginForm.password"
            type="password"
            placeholder="密码"
            size="large"
            prefix-icon="Lock"
            @keyup.enter="handleLogin"
          />
        </el-form-item>
        <el-form-item>
          <el-button
            type="primary"
            size="large"
            style="width: 100%"
            :loading="loading"
            @click="handleLogin"
          >
            登录
          </el-button>
        </el-form-item>
      </el-form>
      <div class="login-footer">
        <el-button type="text" @click="goToFront">返回前台首页</el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'
import request from '@/utils/request'

const router = useRouter()
const route = useRoute()
const loginFormRef = ref()
const loading = ref(false)

const loginForm = ref({
  username: '',
  password: ''
})

const handleLogin = async () => {
  if (!loginFormRef.value) return

  await loginFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true

      try {
        // 真实请求后端登录接口（baseURL 已经是 /api，不需要重复）
        const res = await request.post('/login', {
          username: loginForm.value.username,
          password: loginForm.value.password
        });

        // 严厉核对字段：后端返回的是 access_token！兼容不同响应结构
        const token = res.access_token || (res.data && res.data.access_token);
        const user = res.user || (res.data && res.data.user);

        console.error("真实的响应体:", res);

        if (!token) {
          ElMessage.error('登录失败：未找到 access_token 字段，请看控制台打印！');
          loading.value = false;
          return;
        }

        // 检查是否是管理员
        if (!user || !user.is_admin) {
          ElMessage.error('该账号不是管理员，无权访问后台');
          loading.value = false;
          return;
        }

        // 存储管理员token和信息 - 确保存入的是真实有效的字符串
        localStorage.setItem('admin_token', token);
        localStorage.setItem('admin_info', JSON.stringify(user));
        console.log('已成功存入 localStorage.admin_token =', token.substring(0, 20) + '...');

        ElMessage.success('登录成功');

        // 跳转到管理员页面，用window.location.href强制刷新，避免路由缓存问题
        const redirect = route.query.redirect || '/admin/dashboard';
        window.location.href = '#' + redirect;
      } catch (error) {
        console.error('登录异常:', error);
        // 错误信息已经被拦截器处理了
        loading.value = false;
      }
    }
  })
}

const goToFront = () => {
  router.push('/')
}
</script>

<style scoped>
.admin-login {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
}

.login-card {
  background: white;
  border-radius: 16px;
  padding: 48px;
  width: 100%;
  max-width: 400px;
  box-shadow: 0 20px 60px 0 rgba(0, 0, 0, 0.3);
}

.login-header {
  text-align: center;
  margin-bottom: 40px;
}

.login-header h1 {
  margin: 0 0 10px 0;
  font-size: 28px;
  color: #303133;
}

.login-header p {
  margin: 0;
  color: #909399;
  font-size: 14px;
}

.login-form {
  margin-bottom: 24px;
}

.login-footer {
  text-align: center;
}
</style>
