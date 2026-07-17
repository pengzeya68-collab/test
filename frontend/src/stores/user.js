import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import request, { clearTokenHeader, restoreActiveTokenHeader } from '@/utils/request'
import { setToken, setUserInfo, clearUserAuth, TOKEN_KEY, USER_KEY, safeJsonParse, isValidTokenFormat } from '@/utils/auth'

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem(TOKEN_KEY) || '')
  const userInfo = ref(safeJsonParse(localStorage.getItem(USER_KEY) || 'null'))

  const isLoggedIn = computed(() => !!token.value && isValidTokenFormat(token.value))

  const setLogin = (newToken, user) => {
    token.value = newToken
    userInfo.value = user
    setToken(newToken)
    setUserInfo(user)
    restoreActiveTokenHeader()
  }

  const resetSession = () => {
    token.value = ''
    userInfo.value = null
    clearUserAuth()
    clearTokenHeader()
  }

  const logout = async () => {
    try {
      await request.post('/auth/logout', {})
    } catch {
    }
    resetSession()
  }

  return {
    token,
    userInfo,
    isLoggedIn,
    setLogin,
    resetSession,
    logout,
  }
})
