<template>
  <div class="editor-tab-container">
    <!-- Tab 栏 -->
    <div class="tab-bar">
      <draggable
        v-model="tabList"
        :item-key="(tab) => tab.id"
        handle=".tab-item"
        animation="180"
        class="tab-list"
        ref="tabListRef"
        @end="handleDragEnd"
      >
        <template #item="{ element }">
          <div
            class="tab-item"
            :class="{ active: element.id === tabs.activeTabId }"
            :data-tab-id="element.id"
            :title="element.title"
            @click="handleTabClick(element)"
            @mousedown.middle.prevent="handleCloseTab(element)"
          >
            <el-icon v-if="element.type === 'case'" size="13" class="tab-type-icon"><Document /></el-icon>
            <el-icon v-else-if="element.type === 'scenario'" size="13" class="tab-type-icon"><Connection /></el-icon>
            <el-icon v-else size="13" class="tab-type-icon"><FolderOpened /></el-icon>
            <span class="tab-title">{{ element.title }}</span>
            <span v-if="element.dirty" class="dirty-dot" />
            <el-icon class="tab-close" @click.stop="handleCloseTab(element)"><Close /></el-icon>
          </div>
        </template>
      </draggable>
      <div class="tab-actions" v-if="tabs.tabs.length">
        <el-dropdown trigger="click" @command="handleBatchClose">
          <span class="action-trigger"><el-icon><ArrowDown /></el-icon></span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="closeOther" :disabled="tabs.tabs.length <= 1">关闭其他</el-dropdown-item>
              <el-dropdown-item command="closeAll" :disabled="!tabs.tabs.length">关闭全部</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>

    <!-- Tab 内容区：使用 keep-alive 缓存已打开 tab 的编辑状态 -->
    <div class="tab-content">
      <keep-alive :max="EDITOR_TAB_MAX">
        <component
          v-if="tabs.activeTab"
          :is="currentComponent"
          :key="tabs.activeTabId"
          embedded
          :model-value="true"
          :case-data="editorCaseData"
          :is-edit="editorIsEdit"
          :group-id="editorGroupId"
          :env-id="envId"
          @close="handleEditorClose"
          @dirty-change="handleDirtyChange"
          @title-change="handleTitleChange"
          @success="handleEditorSuccess"
          @run="handleEditorRun"
          @version-restored="handleEditorVersionRestored"
        />
      </keep-alive>
      <div v-if="!tabs.activeTab" class="empty-state">
        <el-empty description="从左侧用例列表双击接口，在此处多开编辑" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch, nextTick, h, defineComponent } from 'vue'
import { ElMessageBox } from 'element-plus'
import { Document, Connection, FolderOpened, Close, ArrowDown } from '@element-plus/icons-vue'
import draggable from 'vuedraggable'
import { useEditorTabsStore, EDITOR_TAB_MAX } from '@/stores/editorTabs'
import CaseEditorDrawer from '@/views/CaseEditorDrawer.vue'

const props = defineProps({
  // 当前选择的环境 ID（用于编辑器变量自动补全）
  envId: { type: [Number, String], default: null },
  // 新建用例时回退使用的分组 ID
  groupId: { type: [Number, String], default: null },
})

const emit = defineEmits(['saved', 'run'])

const tabs = useEditorTabsStore()
const tabListRef = ref(null)

// 暴露给 vuedraggable 的双向绑定列表：直接复用 store 内的 tabs 数组引用
const tabList = computed({
  get: () => tabs.tabs,
  set: (val) => { tabs.tabs = val },
})

const handleDragEnd = () => {
  // 拖拽排序后无需调用后端，顺序已写入 store
}

// 暂不支持的 Tab 类型占位组件
const UnsupportedTab = defineComponent({
  name: 'UnsupportedTab',
  render() {
    return h('div', { class: 'unsupported-tab' }, '该类型的 Tab 暂未实现')
  },
})

// 根据当前 tab 类型决定渲染的编辑器组件
const currentComponent = computed(() => {
  const t = tabs.activeTab
  if (!t) return null
  if (t.type === 'case') return CaseEditorDrawer
  return UnsupportedTab
})

// 传给编辑器的用例数据（保持引用稳定，配合 keep-alive 不丢失编辑状态）
const editorCaseData = computed(() => tabs.activeTab?.data ?? null)
const editorIsEdit = computed(() => !!(tabs.activeTab?.data && tabs.activeTab.data.id))
const editorGroupId = computed(() => tabs.activeTab?.data?.group_id ?? props.groupId)

// 点击 tab：切换激活并刷新访问时间
const handleTabClick = (tab) => {
  tabs.activeTabId = tab.id
  tabs.touchActiveTab?.()
}

// 保存未确认时弹三按钮：保存 / 不保存 / 取消
const confirmCloseDirtyTab = (tab) => new Promise((resolve) => {
  ElMessageBox.confirm(
    `"${tab.title}" 有未保存的修改，是否在关闭前保存？`,
    '未保存的修改',
    {
      type: 'warning',
      distinguishCancelAndClose: true,
      confirmButtonText: '保存',
      cancelButtonText: '不保存',
      showClose: true,
    },
  )
    .then(() => resolve('save'))
    .catch((action) => {
      // 'cancel' → 不保存；'close' → 取消
      if (action === 'cancel') resolve('discard')
      else resolve('cancel')
    })
})

// 关闭单个 tab（脏数据时弹三按钮：保存 / 不保存 / 取消）
const handleCloseTab = async (tab) => {
  if (tab.dirty) {
    const choice = await confirmCloseDirtyTab(tab)
    if (choice === 'cancel') return
    if (choice === 'save') {
      // 通过当前激活的编辑器组件触发保存：先激活该 tab 再触发其保存逻辑
      // 这里无法直接调用子组件方法，依赖子组件通过 key 切换后调用 handleSave
      // 简化方案：激活该 tab 后，借助全局事件总线 / ref 不便，转而通过 window 自定义事件通知编辑器保存
      // 但为最小改动，采用：激活 tab → 等待组件切换 → 派发快捷键事件
      tabs.activeTabId = tab.id
      tabs.touchActiveTab?.()
      await nextTick()
      await new Promise((r) => setTimeout(r, 0))
      // 派发 Ctrl+S 风格的自定义事件，由 CaseEditorDrawer 监听并执行保存
      window.dispatchEvent(new CustomEvent('editor-tabs:save-active', { detail: { tabId: tab.id } }))
      // 保存流程是异步的，这里不再 await，由编辑器成功后再调用 closeTab
      // 为兼容旧流程，若仍存在脏标记则不强制关闭
      return
    }
    // choice === 'discard' 直接关闭
  }
  tabs.closeTab(tab.id)
}

// 编辑器主动请求关闭（取消按钮）
const handleEditorClose = () => {
  const t = tabs.activeTab
  if (t) handleCloseTab(t)
}

const handleDirtyChange = (val) => {
  if (tabs.activeTabId) tabs.markDirty(tabs.activeTabId, val)
}

const handleTitleChange = (val) => {
  if (tabs.activeTabId) tabs.updateTabTitle(tabs.activeTabId, val)
}

/**
 * 处理用例保存成功事件：
 * - 接收 createdCaseId 与 wasEdit 参数
 * - 新建场景下将 tab.id 由 case-new-xxx 改写为 case-${id}，避免重复打开
 * - 回写 tab.data.id 让编辑器进入"编辑模式"
 * - 清除脏标记
 */
const handleEditorSuccess = (createdCaseId, wasEdit) => {
  const activeTabId = tabs.activeTabId
  if (!activeTabId) {
    emit('saved')
    return
  }
  if (!wasEdit && createdCaseId) {
    // 新建→已保存：回写 id 并重命名 tab id
    const currentData = tabs.activeTab?.data || {}
    const nextData = { ...currentData, id: createdCaseId, new: false }
    tabs.updateTabData(activeTabId, nextData)
    const newTabId = `case-${createdCaseId}`
    tabs.renameTabId(activeTabId, newTabId)
    tabs.markDirty(newTabId, false)
  } else {
    // 编辑保存：仅清除脏标记
    tabs.markDirty(activeTabId, false)
  }
  emit('saved', createdCaseId, wasEdit)
}

/**
 * 处理版本恢复成功事件：把最新后端数据写回当前 tab.data
 * @param {Object} latestCaseData 后端返回的最新用例数据
 */
const handleEditorVersionRestored = (latestCaseData) => {
  const activeTabId = tabs.activeTabId
  if (!activeTabId || !latestCaseData) return
  const currentData = tabs.activeTab?.data || {}
  tabs.updateTabData(activeTabId, { ...currentData, ...latestCaseData })
  tabs.markDirty(activeTabId, false)
}

const handleEditorRun = (data) => {
  emit('run', data)
}

// 批量关闭：关闭其他 / 关闭全部
const handleBatchClose = async (command) => {
  const current = tabs.activeTab
  if (command === 'closeOther') {
    const dirtyOthers = tabs.tabs.filter(t => t.id !== current?.id && t.dirty)
    if (dirtyOthers.length) {
      try {
        await ElMessageBox.confirm(
          `有 ${dirtyOthers.length} 个未保存的 Tab，确定关闭其他吗？`,
          '确认关闭',
          { type: 'warning', confirmButtonText: '关闭', cancelButtonText: '取消' }
        )
      } catch {
        return
      }
    }
    if (current) tabs.closeOtherTabs(current.id)
  } else if (command === 'closeAll') {
    if (tabs.hasUnsavedChanges) {
      try {
        await ElMessageBox.confirm(
          '存在未保存的修改，确定关闭全部 Tab 吗？',
          '确认关闭',
          { type: 'warning', confirmButtonText: '关闭', cancelButtonText: '取消' }
        )
      } catch {
        return
      }
    }
    tabs.closeAllTabs()
  }
}

// 切换 tab 时自动将激活项滚动到可见区域
watch(() => tabs.activeTabId, (id) => {
  if (!id) return
  tabs.touchActiveTab?.()
  nextTick(() => {
    const el = tabListRef.value?.$el?.querySelector?.(`[data-tab-id="${CSS.escape(String(id))}"]`)
    el?.scrollIntoView({ block: 'nearest', inline: 'nearest', behavior: 'smooth' })
  })
})
</script>

<style scoped>
.editor-tab-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  width: 100%;
  overflow: hidden;
  background: var(--tm-bg-card);
  border-radius: 12px;
  border: 1px solid var(--tm-border-light);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
}

/* Tab 栏 */
.tab-bar {
  display: flex;
  align-items: stretch;
  flex-shrink: 0;
  border-bottom: 1px solid var(--tm-border-light);
  background: var(--tm-bg-card);
  border-radius: 12px 12px 0 0;
}

.tab-list {
  display: flex;
  align-items: stretch;
  flex: 1;
  min-width: 0;
  overflow-x: auto;
  overflow-y: hidden;
  scrollbar-width: thin;
  scrollbar-height: 6px;
}
.tab-list::-webkit-scrollbar {
  height: 6px;
}
.tab-list::-webkit-scrollbar-thumb {
  background: rgba(var(--tm-color-primary-rgb), 0.4);
  border-radius: 3px;
}

.tab-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 14px;
  min-width: 120px;
  max-width: 240px;
  cursor: grab;
  color: var(--tm-text-secondary);
  font-size: 13px;
  border-right: 1px solid var(--tm-border-light);
  position: relative;
  white-space: nowrap;
  flex-shrink: 0;
  transition: background 0.2s ease, color 0.2s ease;
}
.tab-item:active {
  cursor: grabbing;
}
.tab-item:hover {
  background: rgba(var(--tm-color-primary-rgb), 0.08);
  color: var(--tm-text-primary);
}
.tab-item.active {
  color: var(--tm-color-primary);
  background: var(--tm-bg-card);
}
.tab-item.active::after {
  content: '';
  position: absolute;
  left: 0;
  right: 0;
  bottom: -1px;
  height: 2px;
  background: var(--tm-color-primary);
  border-radius: 2px;
}

.tab-type-icon {
  color: inherit;
  flex-shrink: 0;
}

.tab-title {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
  min-width: 0;
}

.dirty-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--el-color-warning, #fa8c16);
  flex-shrink: 0;
  box-shadow: 0 0 4px rgba(250, 140, 22, 0.6);
}

.tab-close {
  border-radius: 4px;
  padding: 1px;
  color: var(--tm-text-secondary);
  flex-shrink: 0;
  transition: background 0.2s ease, color 0.2s ease;
}
.tab-close:hover {
  background: rgba(245, 34, 45, 0.15);
  color: var(--el-color-danger, #f5222d);
}

.tab-actions {
  display: flex;
  align-items: center;
  padding: 0 10px;
  border-left: 1px solid var(--tm-border-light);
  flex-shrink: 0;
}
.action-trigger {
  display: inline-flex;
  align-items: center;
  cursor: pointer;
  color: var(--tm-text-secondary);
  padding: 4px;
  border-radius: 4px;
}
.action-trigger:hover {
  color: var(--tm-color-primary);
  background: rgba(var(--tm-color-primary-rgb), 0.1);
}

/* 内容区 */
.tab-content {
  flex: 1;
  min-height: 0;
  position: relative;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.tab-content > :deep(*) {
  flex: 1;
  min-height: 0;
}

.empty-state {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.unsupported-tab {
  padding: 32px;
  text-align: center;
  color: var(--tm-text-secondary);
}
</style>
