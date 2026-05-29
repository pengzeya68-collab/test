import { ref } from 'vue'
import { autoTestRequest } from '@/utils/request'

const _cache = { data: null, timestamp: 0 }
const CACHE_TTL = 60000

export function useEnvironments() {
  const environments = ref([])
  const loading = ref(false)

  const loadEnvironments = async (force = false) => {
    const now = Date.now()
    if (!force && _cache.data && now - _cache.timestamp < CACHE_TTL) {
      environments.value = _cache.data
      return _cache.data
    }

    loading.value = true
    try {
      const res = await autoTestRequest.get('/auto-test/environments')
      const list = Array.isArray(res) ? res : (res.environments || [])
      environments.value = list
      _cache.data = list
      _cache.timestamp = now
      return list
    } catch (e) {
      console.error('Load environments failed:', e)
      return []
    } finally {
      loading.value = false
    }
  }

  return { environments, loading, loadEnvironments }
}
