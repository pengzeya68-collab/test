/**
 * 统一工作区项目上下文（WorkspaceProject）。
 * 唯一存储键：desktop-active-project-id（与 request / workspace API 一致）。
 * 禁止再回退到 user.id 伪装 project_id。
 */
import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'
import { getActiveProjectId, setActiveProjectId } from '@/api/workspace'

export const useProjectStore = defineStore('project', () => {
  const overrideId = ref(getActiveProjectId())

  const projectId = computed(() => {
    const n = Number(overrideId.value)
    return Number.isFinite(n) && n > 0 ? n : null
  })

  function setProjectId(id) {
    const n = Number(id)
    if (!Number.isFinite(n) || n <= 0) return
    overrideId.value = n
    setActiveProjectId(n)
  }

  function resetToUserWorkspace() {
    overrideId.value = null
    setActiveProjectId(null)
  }

  function syncFromStorage() {
    overrideId.value = getActiveProjectId()
  }

  if (typeof window !== 'undefined') {
    window.addEventListener('storage', (event) => {
      if (event.key === 'desktop-active-project-id') syncFromStorage()
    })
  }

  watch(overrideId, (val) => {
    if (val == null) setActiveProjectId(null)
  })

  return {
    projectId,
    setProjectId,
    resetToUserWorkspace,
    syncFromStorage,
  }
})

export default useProjectStore
