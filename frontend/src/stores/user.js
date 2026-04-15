import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import request from '@/utils/request'
import { ElNotification } from 'element-plus'

function safeJsonParse(str, fallback = null) {
  try {
    return JSON.parse(str)
  } catch {
    return fallback
  }
}

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem('token') || '')
  const userInfo = ref(safeJsonParse(localStorage.getItem('user') || 'null'))
  const assessmentCompleted = ref(localStorage.getItem('assessment_completed') === 'true')
  const skillProfile = ref(safeJsonParse(localStorage.getItem('skill_profile') || 'null'))

  const isLoggedIn = computed(() => !!token.value)
  const username = computed(() => userInfo.value?.username || '')
  const userId = computed(() => userInfo.value?.id || null)
  const userScore = computed(() => userInfo.value?.score || 0)

  const setLogin = (newToken, user) => {
    token.value = newToken
    userInfo.value = user
    localStorage.setItem('token', newToken)
    localStorage.setItem('user', JSON.stringify(user))
  }

  const setAssessmentCompleted = (profile) => {
    assessmentCompleted.value = true
    skillProfile.value = profile
    localStorage.setItem('assessment_completed', 'true')
    if (profile) {
      localStorage.setItem('skill_profile', JSON.stringify(profile))
    }
  }

  const checkAssessmentStatus = async () => {
    if (!isLoggedIn.value) return false
    try {
      const res = await request.get('/assessment/status')
      const completed = res.has_completed_assessment
      assessmentCompleted.value = completed
      localStorage.setItem('assessment_completed', String(completed))
      if (completed && res.overall_score) {
        skillProfile.value = {
          overall_score: res.overall_score,
          overall_level: res.overall_level,
        }
        localStorage.setItem('skill_profile', JSON.stringify(skillProfile.value))
      }
      return completed
    } catch {
      return false
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
    } catch {
      // silently ignore
    }
  }

  const logout = () => {
    token.value = ''
    userInfo.value = null
    assessmentCompleted.value = false
    skillProfile.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    localStorage.removeItem('assessment_completed')
    localStorage.removeItem('skill_profile')
  }

  return {
    token,
    userInfo,
    assessmentCompleted,
    skillProfile,
    isLoggedIn,
    username,
    userId,
    userScore,
    setLogin,
    setAssessmentCompleted,
    checkAssessmentStatus,
    checkNewAchievements,
    logout,
  }
})
