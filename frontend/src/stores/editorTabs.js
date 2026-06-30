import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

/**
 * 接口编辑器多 Tab 管理 Store
 * 对标 Apifox 的多 Tab 页面，负责 Tab 的新增、关闭、激活、脏数据标记等
 * 每个 tab 结构：{ id, title, type: 'case'|'scenario'|'group', dirty, data, lastAccessedAt }
 */
// keep-alive 上限：与 EditorTabContainer.vue 中的 <keep-alive :max> 保持一致
export const EDITOR_TAB_MAX = 15

export const useEditorTabsStore = defineStore('editorTabs', () => {
  const tabs = ref([])
  const activeTabId = ref(null)

  // 当前激活的 tab
  const activeTab = computed(() => tabs.value.find(t => t.id === activeTabId.value))
  // 是否存在未保存的修改（用于关闭页面时拦截）
  const hasUnsavedChanges = computed(() => tabs.value.some(t => t.dirty))

  /**
   * 打开一个 tab：若同 id 已存在则仅激活，否则新建并激活
   * 超过 EDITOR_TAB_MAX 时优先淘汰最久未访问的非脏 Tab
   * @param {Object} tab { id, title, type, data }
   */
  function openTab(tab) {
    const existing = tabs.value.find(t => t.id === tab.id)
    if (existing) {
      existing.lastAccessedAt = Date.now()
      activeTabId.value = existing.id
      return
    }
    tabs.value.push({ dirty: false, lastAccessedAt: Date.now(), ...tab })
    activeTabId.value = tab.id

    // 超出上限：淘汰最久未访问的非脏 Tab，若全部都是脏 Tab 则保留上限数量的最新 Tab
    if (tabs.value.length > EDITOR_TAB_MAX) {
      const nonDirty = tabs.value.filter(t => !t.dirty && t.id !== activeTabId.value)
      if (nonDirty.length > 0) {
        // 按 lastAccessedAt 升序，淘汰最旧的
        nonDirty.sort((a, b) => (a.lastAccessedAt || 0) - (b.lastAccessedAt || 0))
        const victimId = nonDirty[0].id
        const idx = tabs.value.findIndex(t => t.id === victimId)
        if (idx !== -1) tabs.value.splice(idx, 1)
      } else {
        // 全部都是脏的，按 lastAccessedAt 升序淘汰最旧的一个（不淘汰当前激活的）
        const candidates = tabs.value.filter(t => t.id !== activeTabId.value)
        candidates.sort((a, b) => (a.lastAccessedAt || 0) - (b.lastAccessedAt || 0))
        if (candidates.length > 0) {
          const victimId = candidates[0].id
          const idx = tabs.value.findIndex(t => t.id === victimId)
          if (idx !== -1) tabs.value.splice(idx, 1)
        }
      }
    }
  }

  /**
   * 关闭指定 tab（脏数据拦截应由组件层先行确认）
   * 关闭后自动选择相邻 tab 激活
   */
  function closeTab(id) {
    const idx = tabs.value.findIndex(t => t.id === id)
    if (idx === -1) return
    tabs.value.splice(idx, 1)
    if (activeTabId.value === id) {
      if (tabs.value.length === 0) {
        activeTabId.value = null
      } else if (idx >= tabs.value.length) {
        activeTabId.value = tabs.value[tabs.value.length - 1].id
      } else {
        activeTabId.value = tabs.value[idx].id
      }
    }
  }

  /** 关闭除指定 tab 外的所有 tab */
  function closeOtherTabs(id) {
    tabs.value = tabs.value.filter(t => t.id === id)
    activeTabId.value = id
  }

  /** 关闭全部 tab */
  function closeAllTabs() {
    tabs.value = []
    activeTabId.value = null
  }

  /** 标记某个 tab 的脏状态 */
  function markDirty(id, dirty = true) {
    const tab = tabs.value.find(t => t.id === id)
    if (tab) tab.dirty = dirty
  }

  /** 更新某个 tab 的标题 */
  function updateTabTitle(id, title) {
    const tab = tabs.value.find(t => t.id === id)
    if (tab) tab.title = title
  }

  /** 更新某个 tab 的数据（如保存后回写 id） */
  function updateTabData(id, data) {
    const tab = tabs.value.find(t => t.id === id)
    if (tab) {
      tab.data = data
      tab.lastAccessedAt = Date.now()
    }
  }

  /**
   * 重命名 Tab ID（如新建用例保存成功后，将 case-new-xxx 改为 case-{createdCaseId}）
   * 若目标 ID 已存在（罕见情况），保留旧 tab 并合并数据
   * @returns {string} 实际生效的 Tab ID
   */
  function renameTabId(oldId, newId) {
    if (oldId === newId) return newId
    const idx = tabs.value.findIndex(t => t.id === oldId)
    if (idx === -1) return oldId
    const existing = tabs.value.find(t => t.id === newId)
    if (existing) {
      // 合并到已存在的 tab，删除旧 tab
      existing.data = tabs.value[idx].data ?? existing.data
      existing.dirty = tabs.value[idx].dirty ?? existing.dirty
      tabs.value.splice(idx, 1)
      if (activeTabId.value === oldId) activeTabId.value = newId
      return newId
    }
    tabs.value[idx].id = newId
    if (activeTabId.value === oldId) activeTabId.value = newId
    return newId
  }

  /** 更新当前激活 Tab 的最近访问时间（切换 Tab 时由容器调用） */
  function touchActiveTab() {
    if (!activeTabId.value) return
    const tab = tabs.value.find(t => t.id === activeTabId.value)
    if (tab) tab.lastAccessedAt = Date.now()
  }

  return {
    tabs,
    activeTabId,
    activeTab,
    hasUnsavedChanges,
    openTab,
    closeTab,
    closeOtherTabs,
    closeAllTabs,
    markDirty,
    updateTabTitle,
    updateTabData,
    renameTabId,
    touchActiveTab,
  }
})
