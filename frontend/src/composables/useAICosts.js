import { ref } from 'vue'
import request from '@/utils/request'

const costsMap = ref(null) // null = not loaded yet
const lastFetchTime = ref(0)
const CACHE_TTL = 5 * 60 * 1000 // 5 minutes
let fetchPromise = null // 请求去重

export function resetAICostsCache() {
  costsMap.value = null
  lastFetchTime.value = 0
  fetchPromise = null
}

export function useAICosts() {
  const fetchCosts = async (force = false) => {
    const now = Date.now()
    if (!force && costsMap.value !== null && now - lastFetchTime.value < CACHE_TTL) return
    if (fetchPromise && !force) return fetchPromise

    const thisPromise = fetchPromise = (async () => {
      try {
        const res = await request.get('/user/points/costs')
        const list = res?.data || res || []
        const map = {}
        for (const item of list) {
          map[item.feature] = item.points_cost
        }
        costsMap.value = map
        // 使用请求完成时间而非发起时间，确保缓存有效期准确
        lastFetchTime.value = Date.now()
      } catch (e) {
        // 失败时也更新缓存时间，防止后端故障时请求风暴
        lastFetchTime.value = Date.now()
        console.warn('获取积分配置失败:', e)
      } finally {
        // 仅在没有新的fetchPromise时清空，避免force刷新时覆盖新promise
        if (fetchPromise === thisPromise) {
          fetchPromise = null
        }
      }
    })()

    return fetchPromise
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
