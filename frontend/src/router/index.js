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
    component: () => import(/* webpackChunkName: "learning" */ '@/views/LearningPaths.vue')
  },
  {
    path: '/learning-paths/:id',
    name: 'LearningPathDetail',
    component: () => import(/* webpackChunkName: "learning" */ '@/views/LearningPathDetail.vue')
  },
  {
    path: '/learning-paths/:pathId/lessons/:lessonId',
    name: 'LearningPathLesson',
    component: () => import(/* webpackChunkName: "learning" */ '@/views/LearningPathLesson.vue')
  },
  {
    path: '/exercises',
    name: 'Exercises',
    component: () => import(/* webpackChunkName: "learning" */ '@/views/Exercises.vue')
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
  },
  {
    path: '/tools',
    name: 'TestingTools',
    component: () => import('@/views/TestingTools.vue'),
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

  // 1. 检查管理员路由权限
  if (to.path.startsWith('/admin')) {
    if (to.meta.requiresAuth) {
      if (!adminStore.isLoggedIn) {
        ElMessage.warning('请先登录管理员账号')
        next({
          path: '/admin/login',
          query: { redirect: to.fullPath }
        })
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
  if (to.meta.requiresAuth) {
    if (!userStore.isLoggedIn) {
      ElMessage.warning('你当前未登录，请登录后操作')
      next({
        path: '/login',
        query: { redirect: to.fullPath }
      })
      return
    }
    
    // 3. 检查测评状态
    if (!to.meta.isAssessment) {
      try {
        if (!userStore.assessmentCompleted) {
          const completed = await userStore.checkAssessmentStatus()
          if (!completed) {
            ElMessage.info('请先完成入学测评，我们将为你定制学习计划')
            next({ path: '/assessment' })
            return
          }
        }
      } catch (error) {
        console.warn('路由守卫: 检查测评状态失败，放行导航', error)
      }
    }
  }
  
  next()
})

router.afterEach((to, from) => {
  // 路由跳转后处理
})

export default router
