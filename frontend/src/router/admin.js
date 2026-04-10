/**
 * 后台管理系统路由配置
 */

import Layout from '@/admin/layout/index.vue'

// 登录页面路由
const adminLoginRoute = {
  path: '/admin/login',
  name: 'AdminLogin',
  component: () => import('@/admin/views/Login/index.vue'),
  meta: {
    title: '后台登录',
    requiresAuth: false
  }
}

// 后台路由
const adminRoutes = {
  path: '/admin',
  name: 'Admin',
  component: Layout,
  redirect: '/admin/dashboard',
  meta: {
    title: '后台管理',
    requiresAuth: true
  },
  children: [
    {
      path: 'dashboard',
      name: 'AdminDashboard',
      component: () => import('@/admin/views/Dashboard/index.vue'),
      meta: {
        title: '数据统计'
      }
    },
    {
      path: 'exercises',
      name: 'ExerciseManage',
      component: () => import('@/admin/views/Exercise/index.vue'),
      meta: {
        title: '习题管理'
      }
    },
    {
      path: 'paths',
      name: 'PathManage',
      component: () => import('@/admin/views/LearningPath/index.vue'),
      meta: {
        title: '学习路径'
      }
    },
    {
      path: 'users',
      name: 'UserManage',
      component: () => import('@/admin/views/User/index.vue'),
      meta: {
        title: '用户管理'
      }
    },
    {
      path: 'exams',
      name: 'ExamManage',
      component: () => import('@/admin/views/Exam/index.vue'),
      meta: {
        title: '考试管理'
      }
    },
    {
      path: 'interview',
      name: 'InterviewManage',
      component: () => import('@/admin/views/Interview/index.vue'),
      meta: {
        title: '面试题库'
      }
    },
    {
      path: 'community',
      name: 'CommunityManage',
      component: () => import('@/admin/views/Community/index.vue'),
      meta: {
        title: '社区管理'
      }
    },
    {
      path: 'backup',
      name: 'BackupManage',
      component: () => import('@/views/BackupManager.vue'),
      meta: {
        title: '备份管理'
      }
    },
    {
      path: 'settings',
      name: 'SystemSettings',
      component: () => import('@/views/admin/Settings.vue'),
      meta: {
        title: '系统设置'
      }
    }
  ]
}

export { adminLoginRoute, adminRoutes }
export default [adminLoginRoute, adminRoutes]

