import { ref } from 'vue'
import request from '@/utils/request'

const costsMap = ref(null) // null = not loaded yet
const lastFetchTime = ref(0)
const CACHE_TTL = 5 * 60 * 1000 // 5 minutes

export function useAICosts() {
  const fetchCosts = async (force = false) => {
    const now = Date.now()
    if (!force && costsMap.value !== null && now - lastFetchTime.value < CACHE_TTL) return
    try {
      const res = await request.get('/user/points/costs')
      const list = res?.data || res || []
      const map = {}
      for (const item of list) {
        map[item.feature] = item.points_cost
      }
      costsMap.value = map
      lastFetchTime.value = now
    } catch (e) {
      // 静默失败，保留旧数据
    }
  }

  /**
   * 获取功能积分消耗
   * 返回 null = 未加载或未配置, 0 = 免费, >0 = 实际消耗
   */
  const getCost = (feature) => {
    if (costsMap.value === null) return null
    const val = costsMap.value[feature]
    return val !== undefined ? val : null
  }

  /**
   * 获取功能积分显示文本
   * 返回 null = 未加载(不显示), "免费" = 0积分, "X 积分" = 实际消耗
   */
  const getCostText = (feature) => {
    const cost = getCost(feature)
    if (cost === null) return null
    if (cost <= 0) return '免费'
    return `${cost} 积分`
  }

  return { costsMap, fetchCosts, getCost, getCostText }
}
