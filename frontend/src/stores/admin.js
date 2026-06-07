import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import request, { clearTokenHeader, restoreActiveTokenHeader } from '@/utils/request'
import { setAdminToken, setAdminInfo as saveAdminInfo, clearAdminAuth, ADMIN_TOKEN_KEY, ADMIN_INFO_KEY, safeJsonParse, isValidTokenFormat } from '@/utils/auth'

export const useAdminStore = defineStore('admin', () => {
  const adminInfo = ref(safeJsonParse(localStorage.getItem(ADMIN_INFO_KEY) || 'null'))
  const adminToken = ref(
    (localStorage.getItem(ADMIN_TOKEN_KEY) && isValidTokenFormat(localStorage.getItem(ADMIN_TOKEN_KEY)))
      ? localStorage.getItem(ADMIN_TOKEN_KEY) : ''
  )

  const setAdminInfo = (info, token) => {
    adminInfo.value = info
    adminToken.value = token
    saveAdminInfo(info)
    setAdminToken(token)
  }

  const clearAdminInfo = async () => {
    try {
      await request.post('/admin/logout', {})
    } catch (error) {
      console.warn('管理员退出登录请求失败:', error)
    }
    adminInfo.value = null
    adminToken.value = ''
    clearTokenHeader()
    clearAdminAuth()
    // 管理员登出后恢复用户token（如果用户仍登录）
    restoreActiveTokenHeader()
  }

  const resetSession = () => {
    adminInfo.value = null
    adminToken.value = ''
    clearTokenHeader()
    clearAdminAuth()
    restoreActiveTokenHeader()
  }

  const isLoggedIn = computed(() => !!adminToken.value && isValidTokenFormat(adminToken.value))
  const getAdminToken = () => adminToken.value

  return {
    adminInfo,
    isLoggedIn,
    getAdminToken,
    setAdminInfo,
    clearAdminInfo,
    resetSession
  }
})
