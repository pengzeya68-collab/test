import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

function safeJsonParse(str, fallback = null) {
  try {
    return JSON.parse(str)
  } catch {
    return fallback
  }
}

export const useAdminStore = defineStore('admin', () => {
  const adminInfo = ref(safeJsonParse(localStorage.getItem('admin_info') || 'null'))
  const adminToken = ref(localStorage.getItem('admin_token') || '')

  const setAdminInfo = (info, token) => {
    adminInfo.value = info
    adminToken.value = token
    localStorage.setItem('admin_info', JSON.stringify(info))
    localStorage.setItem('admin_token', token)
  }

  const clearAdminInfo = () => {
    adminInfo.value = null
    adminToken.value = ''
    localStorage.removeItem('admin_info')
    localStorage.removeItem('admin_token')
  }

  const isLoggedIn = computed(() => !!adminToken.value)

  return {
    adminInfo,
    adminToken,
    isLoggedIn,
    setAdminInfo,
    clearAdminInfo
  }
})
