import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import request from '@/utils/request'
import { ElNotification } from 'element-plus'
import { setToken, setUserInfo, clearUserAuth, TOKEN_KEY, USER_KEY, ASSESSMENT_KEY, SKILL_PROFILE_KEY, safeJsonParse, isValidTokenFormat } from '@/utils/auth'

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem(TOKEN_KEY) || '')
  const userInfo = ref(safeJsonParse(localStorage.getItem(USER_KEY) || 'null'))
  const assessmentCompleted = ref(localStorage.getItem(ASSESSMENT_KEY) === 'true')
  const skillProfile = ref(safeJsonParse(localStorage.getItem(SKILL_PROFILE_KEY) || 'null'))
  const isLoading = ref(false)

  const isLoggedIn = computed(() => !!token.value && isValidTokenFormat(token.value))
  const getToken = () => token.value
  const username = computed(() => userInfo.value?.username || '')
  const userId = computed(() => userInfo.value?.id || null)
  const userScore = computed(() => userInfo.value?.score || 0)

  const setLogin = (newToken, user) => {
    token.value = newToken
    userInfo.value = user
    setToken(newToken)
    setUserInfo(user)
  }

  const setAssessmentCompleted = (profile) => {
    assessmentCompleted.value = true
    skillProfile.value = profile
    localStorage.setItem(ASSESSMENT_KEY, 'true')
    if (profile) {
      localStorage.setItem(SKILL_PROFILE_KEY, JSON.stringify(profile))
    }
  }

  const checkAssessmentStatus = async () => {
    if (!isLoggedIn.value) return false
    if (isLoading.value) return assessmentCompleted.value
    
    isLoading.value = true
    try {
      const res = await request.get('/assessment/status')
      const completed = res.has_completed_assessment
      assessmentCompleted.value = completed
      localStorage.setItem(ASSESSMENT_KEY, String(completed))
      if (completed && res.overall_score) {
        skillProfile.value = {
          overall_score: res.overall_score,
          overall_level: res.overall_level,
        }
        localStorage.setItem(SKILL_PROFILE_KEY, JSON.stringify(skillProfile.value))
      }
      return completed
    } catch (error) {
      console.warn('检查测评状态失败，使用本地缓存:', error)
      return assessmentCompleted.value
    } finally {
      isLoading.value = false
    }
  }

  const checkNewAchievements = async () => {
    if (!isLoggedIn.value) return
    try {
      const res = await request.post('/achievements/check')
      if (res.new_unlocks && res.new_unlocks.length > 0) {
        for (const ach of res.new_unlocks) {
          ElNotification({
            title: '🎉 成就解锁！',
            message: `${ach.icon} ${ach.name} — ${ach.description}（+${ach.exp_reward} 经验）`,
            type: 'success',
            duration: 5000,
            position: 'top-right',
          })
        }
      }
    } catch (error) {
      console.warn('检查成就失败:', error)
    }
  }

  const logout = async () => {
    try {
      await request.post('/auth/logout', {})
    } catch (error) {
      console.warn('退出登录请求失败（token可能已过期）:', error)
    }
    token.value = ''
    userInfo.value = null
    assessmentCompleted.value = false
    skillProfile.value = null
    clearUserAuth()
  }

  const resetSession = () => {
    token.value = ''
    userInfo.value = null
    assessmentCompleted.value = false
    skillProfile.value = null
    clearUserAuth()
  }

  return {
    userInfo,
    assessmentCompleted,
    skillProfile,
    isLoggedIn,
    getToken,
    username,
    userId,
    userScore,
    setLogin,
    setAssessmentCompleted,
    checkAssessmentStatus,
    checkNewAchievements,
    logout,
    resetSession,
  }
})
