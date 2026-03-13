import { createRouter, createWebHistory } from 'vue-router'

const routes = [
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
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Route guard
router.beforeEach((to, from, next) => {
  const publicPages = ['/login', '/register', '/']
  const authRequired = !publicPages.includes(to.path)
  const loggedIn = localStorage.getItem('token')

  if (authRequired && !loggedIn) {
    return next('/login')
  }

  next()
})

export default router
