import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/store/auth'
import { getToken } from '@/utils/storage'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue'),
      meta: { guest: true },
    },
    {
      path: '/register',
      name: 'register',
      component: () => import('@/views/RegisterView.vue'),
      meta: { guest: true },
    },
    {
      path: '/',
      component: () => import('@/layouts/MainLayout.vue'),
      meta: { requiresAuth: true },
      children: [
        {
          path: '',
          name: 'home',
          component: () => import('@/views/ChatView.vue'),
        },
        {
          path: 'session/:id',
          name: 'chat',
          component: () => import('@/views/ChatView.vue'),
        },
      ],
    },
  ],
})

// 全局前置守卫
router.beforeEach(async (to, _from, next) => {
  const auth = useAuthStore()
  const hasToken = !!getToken()

  // 需要登录的页面 → 没 token 拦到 /login
  if (to.meta.requiresAuth) {
    if (!hasToken) {
      return next('/login')
    }
    // 有 token 但还没 user（刷新页面） → 拉取用户信息
    if (!auth.user) {
      try {
        await auth.fetchMe()
      } catch {
        auth.logout()
        return next('/login')
      }
    }
    return next()
  }

  // 游客页面（login/register） → 已登录就跳首页
  if (to.meta.guest && hasToken) {
    return next('/')
  }

  next()
})

export default router
