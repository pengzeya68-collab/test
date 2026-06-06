import { createRouter, createWebHashHistory } from 'vue-router'
import { ElMessage } from 'element-plus'
import { adminLoginRoute, adminRoutes } from './admin'
import { useUserStore } from '@/stores/user'
import { useAdminStore } from '@/stores/admin'

const routes = [
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
    component: () => import(/* webpackChunkName: "learning" */ '@/views/LearningPaths.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/learning-paths/:id',
    name: 'LearningPathDetail',
    component: () => import(/* webpackChunkName: "learning" */ '@/views/LearningPathDetail.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/learning-paths/:pathId/lessons/:lessonId',
    name: 'LearningPathLesson',
    component: () => import(/* webpackChunkName: "learning" */ '@/views/LearningPathLesson.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/exercises',
    name: 'Exercises',
    component: () => import(/* webpackChunkName: "learning" */ '@/views/Exercises.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/exercises/:id',
    name: 'ExerciseDetail',
    component: () => import(/* webpackChunkName: "learning" */ '@/views/ExerciseDetail.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/profile',
    name: 'Profile',
    component: () => import('@/views/Profile.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/points',
    name: 'Points',
    component: () => import('@/views/Points.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/code-playground',
    name: 'CodePlayground',
    component: () => import(/* webpackChunkName: "ai" */ '@/views/CodePlayground.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/skill-analysis',
    name: 'SkillAnalysis',
    component: () => import(/* webpackChunkName: "learning" */ '@/views/SkillAnalysis.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/ai-tutor',
    name: 'AITutor',
    component: () => import(/* webpackChunkName: "ai" */ '@/views/AITutor.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/community',
    name: 'Community',
    component: () => import(/* webpackChunkName: "ai" */ '@/views/Community.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/community/post/:id',
    name: 'PostDetail',
    component: () => import('@/views/PostDetail.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/exams',
    name: 'ExamList',
    component: () => import(/* webpackChunkName: "exam" */ '@/views/ExamList.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/exam/:id',
    name: 'Exam',
    component: () => import(/* webpackChunkName: "exam" */ '@/views/Exam.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/exam/result/:id',
    name: 'ExamResult',
    component: () => import(/* webpackChunkName: "exam" */ '@/views/ExamResult.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/interview',
    name: 'InterviewQuestionBank',
    component: () => import(/* webpackChunkName: "ai" */ '@/views/InterviewQuestionBank.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/interview/simulate',
    name: 'InterviewSimulate',
    component: () => import(/* webpackChunkName: "ai" */ '@/views/InterviewSimulate.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/interview/my',
    name: 'InterviewMy',
    component: () => import(/* webpackChunkName: "ai" */ '@/views/InterviewMy.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/interview/detail/:id',
    name: 'InterviewDetail',
    component: () => import(/* webpackChunkName: "ai" */ '@/views/InterviewDetail.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/auto-test',
    name: 'AutoTest',
    component: () => import(/* webpackChunkName: "autotest" */ '@/views/AutoTest.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/jmeter-assistant',
    name: 'JmeterAssistant',
    component: () => import(/* webpackChunkName: "autotest" */ '@/views/JmeterAssistant.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/ai-generate-cases',
    name: 'AIGenerateCases',
    component: () => import(/* webpackChunkName: "autotest" */ '@/views/AIGenerateCases.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/test-coverage',
    name: 'TestCoverage',
    component: () => import(/* webpackChunkName: "autotest" */ '@/views/TestCoverage.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/api-docs',
    name: 'ApiDocs',
    component: () => import(/* webpackChunkName: "autotest" */ '@/views/ApiDocs.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/assessment',
    name: 'OnboardingAssessment',
    component: () => import(/* webpackChunkName: "learning" */ '@/views/OnboardingAssessment.vue'),
    meta: { requiresAuth: true, isAssessment: true }
  },
  {
    path: '/wrong-answers',
    name: 'WrongAnswers',
    component: () => import(/* webpackChunkName: "learning" */ '@/views/WrongAnswers.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/leaderboard',
    name: 'Leaderboard',
    component: () => import(/* webpackChunkName: "learning" */ '@/views/Leaderboard.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/weekly-report',
    name: 'WeeklyReport',
    component: () => import(/* webpackChunkName: "learning" */ '@/views/WeeklyReport.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/certificates',
    name: 'Certificates',
    component: () => import(/* webpackChunkName: "learning" */ '@/views/Certificates.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/notifications',
    name: 'Notifications',
    component: () => import('@/views/Notifications.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/search',
    name: 'SearchResults',
    component: () => import('@/views/SearchResults.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/tools',
    name: 'TestingTools',
    component: () => import('@/views/TestingTools.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/favorites',
    name: 'Favorites',
    component: () => import('@/views/Favorites.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/NotFound.vue')
  }
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
  strict: true,
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) {
      return savedPosition
    }
    return { top: 0 }
  }
})

// 全局路由守卫
router.beforeEach(async (to, from, next) => {
  const adminStore = useAdminStore()
  const userStore = useUserStore()

  // 1. 检查管理员路由权限（使用 matched 确保子路由继承父路由 meta）
  const requiresAuth = to.matched.some(record => record.meta.requiresAuth)
  if (to.path.startsWith('/admin')) {
    if (requiresAuth) {
      if (!adminStore.isLoggedIn) {
        ElMessage.warning('请先登录管理员账号')
        next({
          path: '/admin/login',
          query: { redirect: to.fullPath }
        })
        return
      }
      // 验证管理员角色，防止伪造token绕过
      if (!adminStore.adminInfo?.is_admin && !adminStore.adminInfo?.is_super_admin) {
        ElMessage.error('无管理员权限')
        adminStore.resetSession()
        next({ path: '/admin/login' })
        return
      }
    } else {
      if (adminStore.isLoggedIn && to.path === '/admin/login') {
        next({ path: '/admin/dashboard' })
        return
      }
    }
    next()
    return
  }
  
  // 2. 检查普通用户路由权限
  // 已登录用户访问登录/注册页时重定向到首页
  if (to.path === '/login' || to.path === '/register') {
    if (userStore.isLoggedIn) {
      next({ path: '/' })
      return
    }
  }

  if (requiresAuth) {
    if (!userStore.isLoggedIn) {
      ElMessage.warning('你当前未登录，请登录后操作')
      next({
        path: '/login',
        query: { redirect: to.fullPath }
      })
      return
    }
    
    // 3. 测评状态不再强制拦截，改为通知栏提示
  }
  
  next()
})

router.afterEach((to) => {
  const title = to.meta.title || 'TestMaster'
  document.title = title
})

export default router
