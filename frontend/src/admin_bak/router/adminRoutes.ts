/**
 * 后台管理系统路由配置
 * 所有后台路由都以 /admin 为前缀
 */

import type { RouteRecordRaw } from 'vue-router'
import { Layout } from '@/admin/layout'

const adminRoutes: RouteRecordRaw = {
  path: '/admin',
  name: 'Admin',
  component: Layout,
  redirect: '/admin/dashboard',
  meta: {
    title: '后台管理',
    icon: 'Management',
    requiresAuth: true
  },
  children: [
    {
      path: 'dashboard',
      name: 'AdminDashboard',
      component: () => import('@/admin/views/Dashboard/index.vue'),
      meta: {
        title: '数据统计',
        icon: 'DataAnalysis'
      }
    },
    {
      path: 'exercises',
      name: 'ExerciseManage',
      component: () => import('@/admin/views/Exercise/index.vue'),
      meta: {
        title: '习题管理',
        icon: 'Document'
      }
    },
    {
      path: 'paths',
      name: 'PathManage',
      component: () => import('@/admin/views/LearningPath/index.vue'),
      meta: {
        title: '学习路径',
        icon: 'Guide'
      }
    },
    {
      path: 'users',
      name: 'UserManage',
      component: () => import('@/admin/views/User/index.vue'),
      meta: {
        title: '用户管理',
        icon: 'User'
      }
    }
  ]
}

// 登录页面路由（独立，不使用 Layout）
export const adminLoginRoute: RouteRecordRaw = {
  path: '/admin/login',
  name: 'AdminLogin',
  component: () => import('@/admin/views/Login/index.vue'),
  meta: {
    title: '后台登录',
    requiresAuth: false
  }
}

export { adminRoutes }
export default adminRoutes
