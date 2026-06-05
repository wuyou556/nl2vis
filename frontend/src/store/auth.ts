import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as authApi from '@/api/auth'
import { getToken, setToken, removeToken } from '@/utils/storage'
import type { UserResponse } from '@/types/api'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(getToken())
  const user = ref<UserResponse | null>(null)

  const isLoggedIn = computed(() => !!token.value)

  async function login(username: string, password: string) {
    const res = await authApi.login({ username, password })
    token.value = res.access_token
    user.value = res.user
    setToken(res.access_token)
  }

  async function register(username: string, email: string, password: string) {
    const res = await authApi.register({ username, email, password })
    token.value = res.access_token
    user.value = res.user
    setToken(res.access_token)
  }

  async function fetchMe() {
    user.value = await authApi.getMe()
  }

  function logout() {
    token.value = null
    user.value = null
    removeToken()
  }

  return { token, user, isLoggedIn, login, register, fetchMe, logout }
})
