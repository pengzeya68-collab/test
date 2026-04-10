import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAdminStore = defineStore('admin', () => {
  const adminInfo = ref(JSON.parse(localStorage.getItem('adminInfo') || 'null'))
  const adminToken = ref(localStorage.getItem('adminToken') || '')

  const setAdminInfo = (info, token) => {
    adminInfo.value = info
    adminToken.value = token
    localStorage.setItem('adminInfo', JSON.stringify(info))
    localStorage.setItem('adminToken', token)
  }

  const clearAdminInfo = () => {
    adminInfo.value = null
    adminToken.value = ''
    localStorage.removeItem('adminInfo')
    localStorage.removeItem('adminToken')
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
