import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import request from '@/utils/request'
import { setAdminToken, setAdminInfo as saveAdminInfo, clearAdminAuth, ADMIN_TOKEN_KEY, ADMIN_INFO_KEY } from '@/utils/auth'

function safeJsonParse(str, fallback = null) {
  try {
    return JSON.parse(str)
  } catch {
    return fallback
  }
}

export const useAdminStore = defineStore('admin', () => {
  const adminInfo = ref(safeJsonParse(localStorage.getItem(ADMIN_INFO_KEY) || 'null'))
  const adminToken = ref(localStorage.getItem(ADMIN_TOKEN_KEY) || '')

  const setAdminInfo = (info, token) => {
    adminInfo.value = info
    adminToken.value = token
    saveAdminInfo(info)
    setAdminToken(token)
  }

  const clearAdminInfo = async () => {
    try {
      await request.post('/auth/logout', {})
    } catch {
      // ignore
    }
    adminInfo.value = null
    adminToken.value = ''
    clearAdminAuth()
  }

  const resetSession = () => {
    adminInfo.value = null
    adminToken.value = ''
    clearAdminAuth()
  }

  const isLoggedIn = computed(() => !!adminToken.value)

  return {
    adminInfo,
    adminToken,
    isLoggedIn,
    setAdminInfo,
    clearAdminInfo,
    resetSession
  }
})
