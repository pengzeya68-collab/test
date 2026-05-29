import { ref, onBeforeUnmount } from 'vue'
import { autoTestRequest } from '@/utils/request'

export function useTaskPolling() {
  const currentTaskId = ref(null)
  const taskStatus = ref(null)
  const taskResult = ref(null)
  let pollTimer = null

  const startPolling = async (taskId, options = {}) => {
    const { interval = 2000, maxAttempts = 150, onComplete, onError } = options
    currentTaskId.value = taskId
    let attempts = 0

    const poll = async () => {
      try {
        const res = await autoTestRequest.get(`/auto-test/tasks/${taskId}`)
        taskStatus.value = res.status || res.state
        taskResult.value = res

        if (['SUCCESS', 'success', 'FAILURE', 'failure', 'REVOKED', 'revoked'].includes(taskStatus.value)) {
          stopPolling()
          if (onComplete) onComplete(res)
          return
        }

        attempts++
        if (attempts >= maxAttempts) {
          stopPolling()
          if (onError) onError('timeout')
          return
        }

        pollTimer = setTimeout(poll, interval)
      } catch (e) {
        stopPolling()
        if (onError) onError(e)
      }
    }

    poll()
  }

  const stopPolling = () => {
    if (pollTimer) {
      clearTimeout(pollTimer)
      pollTimer = null
    }
    currentTaskId.value = null
  }

  const cancelTask = async (taskId) => {
    if (!taskId) return
    try {
      await autoTestRequest.post(`/auto-test/tasks/${taskId}/cancel`)
    } catch (e) {
      console.error('Cancel task failed:', e)
    }
    stopPolling()
  }

  onBeforeUnmount(() => {
    stopPolling()
  })

  return { currentTaskId, taskStatus, taskResult, startPolling, stopPolling, cancelTask }
}
