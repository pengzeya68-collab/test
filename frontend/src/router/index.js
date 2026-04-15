import { createRouter, createWebHashHistory } from 'vue-router'
import { ElMessage } from 'element-plus'
import { adminLoginRoute, adminRoutes } from './admin'
import { useUserStore } from '@/stores/user'

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
    component: () => import('@/views/ExerciseDetail.vue'),
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
    component: () => import('@/views/Community.vue'),
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
    path: '/auto-test',
    name: 'AutoTest',
    component: () => import('@/views/AutoTest.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/assessment',
    name: 'OnboardingAssessment',
    component: () => import('@/views/OnboardingAssessment.vue'),
    meta: { requiresAuth: true, isAssessment: true }
  },
  {
    path: '/wrong-answers',
    name: 'WrongAnswers',
    component: () => import('@/views/WrongAnswers.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/leaderboard',
    name: 'Leaderboard',
    component: () => import('@/views/Leaderboard.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/weekly-report',
    name: 'WeeklyReport',
    component: () => import('@/views/WeeklyReport.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/certificates',
    name: 'Certificates',
    component: () => import('@/views/Certificates.vue'),
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
  if (to.meta.requiresAuth) {
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
      const token = localStorage.getItem('token')
      const user = localStorage.getItem('user')
      
      if (!token || !user) {
        ElMessage.warning('你当前未登录，请登录后操作')
        next({
          path: '/login',
          query: { redirect: to.fullPath }
        })
        return
      }

      if (!to.meta.isAssessment) {
        try {
          const userStore = useUserStore()
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
  }
  
  next()
})

router.afterEach((to, from) => {
  // 路由跳转后处理
})

export default router
