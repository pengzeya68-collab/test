import { createRouter, createWebHashHistory } from 'vue-router'
import { ElMessage } from 'element-plus'
import { adminLoginRoute, adminRoutes } from './admin'

const routes = [
  // 测试路由
  {
    path: '/test',
    name: 'Test',
    component: () => import('@/test.vue')
  },
  adminLoginRoute,
  adminRoutes,
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/Home.vue')
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue')
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/Register.vue')
  },
  {
    path: '/forgot-password',
    name: 'ForgotPassword',
    component: () => import('@/views/ForgotPassword.vue')
  },
  {
    path: '/learning-paths',
    name: 'LearningPaths',
    component: () => import('@/views/LearningPaths.vue')
  },
  {
    path: '/learning-paths/:id',
    name: 'LearningPathDetail',
    component: () => import('@/views/LearningPathDetail.vue')
  },
  {
    path: '/exercises',
    name: 'Exercises',
    component: () => import('@/views/Exercises.vue')
  },
  {
    path: '/exercises/:id',
    name: 'ExerciseDetail',
    component: () => import('@/views/ExerciseDetail.vue')
  },
  {
    path: '/profile',
    name: 'Profile',
    component: () => import('@/views/Profile.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/code-playground',
    name: 'CodePlayground',
    component: () => import('@/views/CodePlayground.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/skill-analysis',
    name: 'SkillAnalysis',
    component: () => import('@/views/SkillAnalysis.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/ai-tutor',
    name: 'AITutor',
    component: () => import('@/views/AITutor.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/community',
    name: 'Community',
    component: () => import('@/views/Community.vue')
  },
  {
    path: '/community/post/:id',
    name: 'PostDetail',
    component: () => import('@/views/PostDetail.vue')
  },
  {
    path: '/exams',
    name: 'ExamList',
    component: () => import('@/views/ExamList.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/exam/:id',
    name: 'Exam',
    component: () => import('@/views/Exam.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/exam/result/:id',
    name: 'ExamResult',
    component: () => import('@/views/ExamResult.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/interview',
    name: 'InterviewQuestionBank',
    component: () => import('@/views/InterviewQuestionBank.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/interview/simulate',
    name: 'InterviewSimulate',
    component: () => import('@/views/InterviewSimulate.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/interview/my',
    name: 'InterviewMy',
    component: () => import('@/views/InterviewMy.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/interview/detail/:id',
    name: 'InterviewDetail',
    component: () => import('@/views/InterviewDetail.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/interface-test',
    name: 'InterfaceTestList',
    component: () => import('@/views/InterfaceTestList.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/interface-test/new',
    name: 'InterfaceTestNew',
    component: () => import('@/views/InterfaceTestDetail.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/interface-test/:id',
    name: 'InterfaceTestDetail',
    component: () => import('@/views/InterfaceTestDetail.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/interface-test/environments',
    name: 'InterfaceEnvManager',
    component: () => import('@/views/InterfaceEnvManager.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/auto-test',
    name: 'AutoTest',
    component: () => import('@/views/AutoTest.vue'),
    meta: { requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
  // 启用严格模式，调试路由
  strict: true,
})

// 全局路由守卫
router.beforeEach((to, from, next) => {
  // 检查是否需要登录权限
  if (to.meta.requiresAuth) {
    // 管理员页面判断管理员token
    if (to.path.startsWith('/admin')) {
      const adminToken = localStorage.getItem('admin_token')
      const adminInfo = localStorage.getItem('admin_info')
      
      if (!adminToken || !adminInfo) {
        ElMessage.warning('请先登录管理员账号')
        next({
          path: '/admin/login',
          query: { redirect: to.fullPath }
        })
        return
      }
    } else {
      // 普通页面判断普通用户token
      const token = localStorage.getItem('token')
      const user = localStorage.getItem('user')
      
      if (!token || !user) {
        ElMessage.warning('你当前未登录，请登录后操作')
        // 跳转到登录页，携带跳转前的路径
        next({
          path: '/login',
          query: { redirect: to.fullPath }
        })
        return
      }
    }
  }
  
  next()
})

router.afterEach((to, from) => {
  // 路由跳转后处理
})

export default router
