<template>
  <div class="admin-layout admin-page" style="height: 100vh; width: 100%;">
    <el-container style="height: 100%;">
      <!-- 侧边栏 -->
      <el-aside :width="isCollapse ? '64px' : '220px'" class="admin-aside">
        <div class="logo-container">
          <span v-if="!isCollapse" class="logo-text">TestMaster</span>
          <el-icon size="32"><DataAnalysis /></el-icon>
        </div>
        
        <el-menu
          :default-active="activeMenu"
          :collapse="isCollapse"
          background-color="#304156"
          text-color="#bfcbd9"
          active-text-color="#409EFF"
          router
          class="admin-menu"
        >
          <el-menu-item index="/admin/dashboard">
            <el-icon><DataAnalysis /></el-icon>
            <template #title>数据统计</template>
          </el-menu-item>
          
          <el-menu-item index="/admin/exercises">
            <el-icon><Document /></el-icon>
            <template #title>习题管理</template>
          </el-menu-item>
          
          <el-menu-item index="/admin/paths">
            <el-icon><Guide /></el-icon>
            <template #title>学习路径</template>
          </el-menu-item>
          
          <el-menu-item index="/admin/users">
            <el-icon><User /></el-icon>
            <template #title>用户管理</template>
          </el-menu-item>
        </el-menu>
      </el-aside>
      
      <el-container>
        <!-- 顶部导航栏 -->
        <el-header class="admin-header">
          <div class="header-left">
            <el-icon class="collapse-btn" @click="toggleCollapse">
              <Fold v-if="!isCollapse" />
              <Expand v-else />
            </el-icon>
            <el-breadcrumb separator="/">
              <el-breadcrumb-item :to="{ path: '/admin/dashboard' }">首页</el-breadcrumb-item>
              <el-breadcrumb-item v-if="currentRoute">{{ currentRoute }}</el-breadcrumb-item>
            </el-breadcrumb>
          </div>
          
          <div class="header-right">
            <el-dropdown @command="handleCommand">
              <span class="user-info">
                <el-avatar :size="32" :src="adminAvatar">
                  <el-icon><User /></el-icon>
                </el-avatar>
                <span class="username">{{ adminName }}</span>
              </span>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="profile">个人中心</el-dropdown-item>
                  <el-dropdown-item command="settings">系统设置</el-dropdown-item>
                  <el-dropdown-item divided command="logout">退出登录</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </el-header>
        
        <!-- 主内容区域 -->
        <el-main class="admin-main">
          <router-view />
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  DataAnalysis,
  Document,
  Guide,
  User,
  Fold,
  Expand
} from '@element-plus/icons-vue'
import { ElMessageBox, ElMessage } from 'element-plus'
import { getAdminInfo, logout as logoutApi } from '@/admin/api'
import { logout as clearAuth } from '@/admin/utils/permission'

const route = useRoute()
const router = useRouter()

// 侧边栏折叠状态
const isCollapse = ref(false)

const toggleCollapse = () => {
  isCollapse.value = !isCollapse.value
}

// 当前激活的菜单
const activeMenu = computed(() => route.path)

// 当前路由标题
const currentRoute = computed(() => route.meta?.title || '')

// 管理员信息
const adminName = ref('管理员')
const adminAvatar = ref('')

// 获取管理员信息
const fetchAdminInfo = async () => {
  try {
    const response = await getAdminInfo()
    adminName.value = response.data.name
    adminAvatar.value = response.data.avatar
  } catch (error) {
    ElMessage.error('获取管理员信息失败')
  }
}

onMounted(() => {
  fetchAdminInfo()
})

// 处理下拉菜单命令
const handleCommand = async (command) => {
  switch (command) {
    case 'logout':
      await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      })
      
      // 调用退出登录 API
      try {
        await logoutApi()
      } catch (error) {
        // 忽略退出接口错误，直接清除本地状态
      }
      
      // 清除本地认证信息
      clearAuth()
      
      ElMessage.success('退出登录成功')
      router.push('/admin/login')
      break
    case 'profile':
      ElMessage.info('个人中心功能开发中')
      break
    case 'settings':
      ElMessage.info('系统设置功能开发中')
      break
  }
}
</script>

<style scoped lang="scss">
.admin-layout {
  height: 100vh !important;
  width: 100% !important;
  min-height: 100vh !important;
  overflow: hidden !important;
  
  .el-container {
    height: 100% !important;
    min-height: 100% !important;
  }
  
  // 侧边栏
  .admin-aside {
    background-color: #304156;
    transition: width 0.3s;
    overflow: hidden;
    
    .logo-container {
      height: 60px;
      display: flex;
      align-items: center;
      justify-content: center;
      background-color: #2b3a4b;
      
      .logo {
        height: 32px;
        width: 32px;
      }
      
      .logo-text {
        margin-left: 12px;
        color: #fff;
        font-size: 20px;
        font-weight: 600;
      }
    }
    
    .admin-menu {
      border-right: none;
      overflow-x: hidden;
      
      :deep(.el-menu-item) {
        &:hover {
          background-color: rgba(255, 255, 255, 0.1);
        }
        
        &.is-active {
          background-color: #409EFF;
        }
      }
    }
  }
  
  // 顶部导航栏
  .admin-header {
    background-color: #fff;
    border-bottom: 1px solid #e6e6e6;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 20px;
    box-shadow: 0 1px 4px rgba(0, 21, 41, 0.08);
    
    .header-left {
      display: flex;
      align-items: center;
      
      .collapse-btn {
        font-size: 20px;
        cursor: pointer;
        margin-right: 16px;
        transition: color 0.3s;
        
        &:hover {
          color: #409EFF;
        }
      }
    }
    
    .header-right {
      .user-info {
        display: flex;
        align-items: center;
        cursor: pointer;
        
        .username {
          margin-left: 12px;
          color: #606266;
          font-size: 14px;
        }
      }
    }
  }
  
  // 主内容区域
  .admin-main {
    background-color: #f0f2f5;
    padding: 20px;
    overflow-y: auto;
  }
}
</style>
