<template>
  <div class="case-tree-sidebar" v-loading="loadingGroups">
    <!-- 顶部标题与操作 -->
    <div class="sidebar-header">
      <span class="sidebar-title">📁 接口分组</span>
      <el-button type="primary" size="small" plain :icon="Plus" @click="openCreateRoot" title="新建根分组" />
    </div>

    <!-- 🔥 体验4：分组树搜索框 -->
    <div class="sidebar-search">
      <el-input
        v-model="groupFilterText"
        placeholder="搜索分组名称"
        size="small"
        clearable
        :prefix-icon="Search"
      />
    </div>

    <!-- 工具条：展开/折叠 + 刷新 -->
    <div class="sidebar-toolbar">
      <el-button text size="small" @click="expandAll">展开全部</el-button>
      <el-button text size="small" @click="collapseAll">折叠全部</el-button>
      <el-button text size="small" :icon="Refresh" @click="loadGroups" title="刷新">刷新</el-button>
    </div>

    <!-- 分组树 -->
    <div class="tree-wrapper" @contextmenu.prevent>
      <el-tree
        ref="treeRef"
        :data="groupTreeData"
        :props="treeProps"
        node-key="id"
        highlight-current
        draggable
        default-expand-all
        :expand-on-click-node="false"
        :allow-drop="allowDrop"
        :filter-node-method="filterNode"
        @node-click="handleGroupSelect"
        @node-drop="handleNodeDrop"
        @node-contextmenu="handleContextMenu"
      >
        <template #default="{ node, data }">
          <span class="tree-node" :class="{ 'is-selected': data.id === props.currentGroupId }">
            <span class="node-icon">{{ data.children?.length ? '📂' : '📁' }}</span>
            <span class="node-label" :title="data.name">{{ node.label }}</span>
            <span class="node-count">{{ data.case_count || 0 }}</span>
          </span>
        </template>
      </el-tree>

      <!-- 空状态 -->
      <div v-if="!loadingGroups && groupTreeData.length === 0" class="empty-tree">
        <span>暂无分组</span>
        <el-button type="primary" text size="small" @click="openCreateRoot">立即创建</el-button>
      </div>
    </div>

    <!-- 右键菜单 -->
    <div
      v-show="contextMenu.visible"
      class="context-menu"
      :style="{ left: contextMenu.x + 'px', top: contextMenu.y + 'px' }"
    >
      <div class="context-menu-item" @click="handleMenuCommand('createChild')">
        <el-icon><Plus /></el-icon> 新建子分组
      </div>
      <div class="context-menu-item" @click="handleMenuCommand('rename')">
        <el-icon><Edit /></el-icon> 重命名
      </div>
      <div class="context-menu-item" @click="handleMenuCommand('move')">
        <el-icon><Rank /></el-icon> 移动到...
      </div>
      <div class="context-menu-item danger" @click="handleMenuCommand('delete')">
        <el-icon><Delete /></el-icon> 删除
      </div>
    </div>

    <!-- 新建/编辑分组弹窗 -->
    <el-dialog
      v-model="groupDialog.visible"
      :title="groupDialog.title"
      width="420px"
      append-to-body
    >
      <el-form :model="groupForm" label-width="70px">
        <el-form-item label="名称" required>
          <el-input v-model="groupForm.name" placeholder="输入分组名称" maxlength="200" show-word-limit />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="groupForm.description" type="textarea" :rows="2" placeholder="可选描述" />
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="groupForm.sort_order" :min="0" :max="9999" controls-position="right" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="groupDialog.visible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleGroupSave">确定</el-button>
      </template>
    </el-dialog>

    <!-- 移动分组弹窗 -->
    <el-dialog v-model="moveDialog.visible" title="移动分组到" width="420px" append-to-body>
      <el-form label-width="80px">
        <el-form-item label="目标父级">
          <el-cascader
            v-model="moveTarget"
            :options="moveOptions"
            :props="cascaderProps"
            placeholder="不选则移到根分组"
            clearable
            filterable
            style="width: 100%"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="moveDialog.visible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleMoveConfirm">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Edit, Delete, Rank, Refresh, Search } from '@element-plus/icons-vue'
import autoTestRequest from '@/utils/autoTestRequest'

const props = defineProps({
  // v-model 控制显隐
  modelValue: {
    type: Boolean,
    default: true
  },
  // 当前选中的分组 ID
  currentGroupId: {
    type: [Number, String],
    default: null
  }
})

const emit = defineEmits(['update:modelValue', 'select-group', 'edit-case'])

const treeRef = ref(null)
const groupTreeData = ref([])
const loadingGroups = ref(false)
const submitting = ref(false)
const treeProps = { children: 'children', label: 'name' }
// 🔥 体验4：分组树搜索关键字
const groupFilterText = ref('')

// el-tree 过滤函数：匹配分组名称（含子分组时也保留父节点）
const filterNode = (value, data) => {
  if (!value) return true
  return (data.name || '').toLowerCase().includes(value.toLowerCase())
}

// 搜索关键字变化时调用 el-tree 的 filter 方法
watch(groupFilterText, (val) => {
  treeRef.value?.filter?.(val)
})

// ===== 右键菜单状态 =====
const contextMenu = reactive({
  visible: false,
  x: 0,
  y: 0,
  groupData: null
})

// ===== 分组表单弹窗 =====
const groupDialog = reactive({
  visible: false,
  title: '新建分组',
  mode: 'create' // create | edit
})
const groupForm = ref({ id: null, name: '', description: '', sort_order: 0, parent_id: null })

// ===== 移动弹窗 =====
const moveDialog = reactive({ visible: false })
const moveTarget = ref(null)
const moveTargetGroup = ref(null)
const cascaderProps = {
  checkStrictly: true,
  emitPath: false,
  value: 'id',
  label: 'name',
  children: 'children'
}

// ===== 加载分组树 =====
const loadGroups = async () => {
  loadingGroups.value = true
  try {
    const res = await autoTestRequest.get('/auto-test/groups/tree')
    groupTreeData.value = res || []
    // 选中态恢复
    await nextTick()
    if (props.currentGroupId && treeRef.value) {
      treeRef.value.setCurrentKey(props.currentGroupId)
    }
  } catch (error) {
    console.error('加载分组失败:', error)
    ElMessage.error('加载分组失败')
  } finally {
    loadingGroups.value = false
  }
}

// ===== 选中分组 =====
const handleGroupSelect = (data) => {
  emit('select-group', data.id)
}

// ===== 展开/折叠 =====
const expandAll = () => {
  const tree = treeRef.value
  if (!tree) return
  const expand = (nodes) => {
    nodes.forEach((n) => {
      tree.store.nodesMap[n.id]?.expand()
      if (n.children?.length) expand(n.children)
    })
  }
  expand(groupTreeData.value)
}

const collapseAll = () => {
  const tree = treeRef.value
  if (!tree) return
  Object.values(tree.store.nodesMap).forEach((n) => n.collapse())
}

// ===== 拖拽控制 =====
const allowDrop = (draggingNode, dropNode, type) => {
  // 禁止将父节点拖入自身后代（el-tree 已基本处理，这里额外兜底）
  if (type === 'inner') {
    return !isDescendant(draggingNode.data.id, dropNode.data)
  }
  return true
}

const isDescendant = (parentId, node) => {
  if (!node.children?.length) return false
  return node.children.some((c) => c.id === parentId || isDescendant(parentId, c))
}

// 拖拽结束后调用 move 接口
const handleNodeDrop = async (draggingNode, dropNode, dropType) => {
  const dragData = draggingNode.data
  let newParentId = dragData.parent_id
  let newSortOrder = dragData.sort_order || 0

  try {
    if (dropType === 'inner') {
      // 拖入 dropNode 内部，成为其子分组
      newParentId = dropNode.data.id
    } else {
      // 'before' / 'after'：与 dropNode 同级
      newParentId = dropNode.data.parent_id
    }
    // 计算新排序：同级中的位置
    const siblings = getSiblings(newParentId)
    const idx = siblings.findIndex((s) => s.id === dragData.id)
    newSortOrder = idx >= 0 ? idx : 0

    await autoTestRequest.put(`/auto-test/groups/${dragData.id}/move`, {
      parent_id: newParentId,
      sort_order: newSortOrder
    })
    ElMessage.success('分组已移动')
    await loadGroups()
  } catch (error) {
    ElMessage.error('移动失败：' + (error.response?.data?.detail || error.message))
    // 回滚视图
    await loadGroups()
  }
}

const getSiblings = (parentId) => {
  if (parentId === null || parentId === undefined) return groupTreeData.value
  const find = (nodes) => {
    for (const n of nodes) {
      if (n.id === parentId) return n.children || []
      if (n.children?.length) {
        const r = find(n.children)
        if (r) return r
      }
    }
    return null
  }
  return find(groupTreeData.value) || []
}

// ===== 右键菜单 =====
const handleContextMenu = (event, data) => {
  contextMenu.visible = true
  contextMenu.x = event.clientX
  contextMenu.y = event.clientY
  contextMenu.groupData = data
}

const closeContextMenu = () => {
  contextMenu.visible = false
}

const handleMenuCommand = (command) => {
  const data = contextMenu.groupData
  contextMenu.visible = false
  if (!data) return
  switch (command) {
    case 'createChild':
      openCreate(data.id)
      break
    case 'rename':
      openEdit(data)
      break
    case 'move':
      openMove(data)
      break
    case 'delete':
      handleDelete(data)
      break
  }
}

// ===== 新建根/子分组 =====
const openCreateRoot = () => openCreate(null)

const openCreate = (parentId) => {
  groupDialog.title = parentId ? '新建子分组' : '新建根分组'
  groupDialog.mode = 'create'
  groupForm.value = { id: null, name: '', description: '', sort_order: 0, parent_id: parentId }
  groupDialog.visible = true
}

// ===== 编辑分组 =====
const openEdit = (data) => {
  groupDialog.title = '编辑分组'
  groupDialog.mode = 'edit'
  groupForm.value = {
    id: data.id,
    name: data.name,
    description: data.description || '',
    sort_order: data.sort_order || 0,
    parent_id: data.parent_id
  }
  groupDialog.visible = true
}

const handleGroupSave = async () => {
  if (!groupForm.value.name?.trim()) {
    ElMessage.warning('请输入分组名称')
    return
  }
  submitting.value = true
  try {
    const payload = {
      name: groupForm.value.name.trim(),
      description: groupForm.value.description || null,
      sort_order: groupForm.value.sort_order ?? 0
    }
    if (groupDialog.mode === 'edit') {
      await autoTestRequest.put(`/auto-test/groups/${groupForm.value.id}`, payload)
      ElMessage.success('更新成功')
    } else {
      await autoTestRequest.post('/auto-test/groups', {
        ...payload,
        parent_id: groupForm.value.parent_id
      })
      ElMessage.success('创建成功')
    }
    groupDialog.visible = false
    await loadGroups()
  } catch (error) {
    ElMessage.error('操作失败：' + (error.response?.data?.detail || error.message))
  } finally {
    submitting.value = false
  }
}

// ===== 移动分组 =====
const openMove = (data) => {
  moveTargetGroup.value = data
  // 构建可选目标树（排除自身及其后代，避免循环）
  moveOptions.value = filterSelfAndDescendants(groupTreeData.value, data.id)
  moveTarget.value = data.parent_id
  moveDialog.visible = true
}

const moveOptions = ref([])

const filterSelfAndDescendants = (nodes, excludeId) => {
  return nodes
    .filter((n) => n.id !== excludeId)
    .map((n) => ({
      id: n.id,
      name: n.name,
      children: n.children?.length ? filterSelfAndDescendants(n.children, excludeId) : undefined
    }))
}

const handleMoveConfirm = async () => {
  const group = moveTargetGroup.value
  if (!group) return
  submitting.value = true
  try {
    await autoTestRequest.put(`/auto-test/groups/${group.id}/move`, {
      parent_id: moveTarget.value ?? null
    })
    ElMessage.success('移动成功')
    moveDialog.visible = false
    await loadGroups()
  } catch (error) {
    ElMessage.error('移动失败：' + (error.response?.data?.detail || error.message))
  } finally {
    submitting.value = false
  }
}

// ===== 删除分组 =====
// 🔥 Bug 7 修复：先检查是否存在子分组，若有则禁止删除并提示先清空；
// 文案与实际行为对齐：明确"用例会移动到父分组"仅在无子分组时执行
const handleDelete = async (data) => {
  // 1. 先在前端树中检查是否有子分组（快速失败，避免无谓网络请求）
  if (data.children && data.children.length > 0) {
    ElMessage.warning(`分组 "${data.name}" 下还有 ${data.children.length} 个子分组，请先删除或移动子分组后再删除。`)
    return
  }
  // 2. 再向后端确认（防止前端树未及时同步），GET 子分组树
  try {
    const subtree = await autoTestRequest.get(`/auto-test/groups/${data.id}/children`)
    const childCount = Array.isArray(subtree) ? subtree.length : (subtree?.children?.length || subtree?.count || 0)
    if (childCount > 0) {
      ElMessage.warning(`分组 "${data.name}" 下还有 ${childCount} 个子分组，请先删除或移动子分组后再删除。`)
      return
    }
  } catch (e) {
    // 接口不存在或失败时，回退到信任前端树数据，不阻断删除流程
    console.warn('检查子分组失败，回退到前端树判断', e)
  }
  try {
    await ElMessageBox.confirm(
      `确定删除分组 "${data.name}" 吗？\n该分组下的用例将移动到父分组（无父分组则用例保留为根级，不删除用例）。`,
      '删除确认',
      { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' }
    )
    await autoTestRequest.delete(`/auto-test/groups/${data.id}`)
    ElMessage.success('删除成功')
    // 若删除的是当前选中分组，回到全部
    if (data.id === props.currentGroupId) {
      emit('select-group', null)
    }
    await loadGroups()
  } catch (error) {
    if (error === 'cancel') return
    // 后端返回"存在子分组"等业务错误时，把真实错误展示给用户
    const detail = error?.response?.data?.detail || error?.response?.data?.message || error.message
    ElMessage.error('删除失败：' + detail)
  }
}

// 点击其他区域关闭右键菜单
const onDocumentClick = () => {
  if (contextMenu.visible) contextMenu.visible = false
}

onMounted(() => {
  loadGroups()
  document.addEventListener('click', onDocumentClick)
})

onUnmounted(() => {
  document.removeEventListener('click', onDocumentClick)
})

// 暴露刷新方法供父组件调用
defineExpose({ loadGroups, refresh: loadGroups, openCreateRoot })
</script>

<style scoped>
.case-tree-sidebar {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--tm-bg-card);
  border-radius: 12px;
  border: 1px solid var(--tm-border-light);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
  overflow: hidden;
}

.sidebar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 16px;
  border-bottom: 1px solid var(--border-subtle);
  flex-shrink: 0;
}

.sidebar-title {
  font-weight: 600;
  font-size: 15px;
  color: var(--tm-text-primary);
}

.sidebar-toolbar {
  display: flex;
  gap: 4px;
  padding: 6px 10px;
  border-bottom: 1px solid var(--border-subtle);
  flex-shrink: 0;
}

.sidebar-search {
  padding: 8px 10px;
  border-bottom: 1px solid var(--border-subtle);
  flex-shrink: 0;
}

.tree-wrapper {
  flex: 1;
  overflow: auto;
  padding: 10px;
  position: relative;
}

.tree-node {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  padding: 4px 6px;
  border-radius: 6px;
  transition: background 0.2s ease;
}

.tree-node.is-selected {
  background: rgba(var(--tm-color-primary-rgb), 0.12);
}

.node-icon {
  font-size: 15px;
  flex-shrink: 0;
}

.node-label {
  flex: 1;
  font-size: 13px;
  color: var(--tm-text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.node-count {
  color: var(--tm-color-primary);
  font-size: 11px;
  background: rgba(var(--tm-color-primary-rgb), 0.15);
  padding: 1px 8px;
  border-radius: 10px;
  flex-shrink: 0;
}

.empty-tree {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 40px 0;
  color: var(--tm-text-secondary);
  font-size: 13px;
}

:deep(.el-tree) {
  background: transparent;
  --el-tree-node-hover-bg-color: rgba(var(--tm-color-primary-rgb), 0.08);
}

:deep(.el-tree .el-tree-node.is-current > .el-tree-node__content) {
  background-color: rgba(var(--tm-color-primary-rgb), 0.15) !important;
  border-radius: 6px;
}

:deep(.el-tree .el-tree-node__content) {
  height: 32px;
  border-radius: 6px;
}

:deep(.el-tree .el-tree-node__content:hover) {
  background-color: rgba(var(--tm-color-primary-rgb), 0.1) !important;
}

/* 右键菜单 */
.context-menu {
  position: fixed;
  z-index: 9999;
  background: var(--tm-bg-card);
  border: 1px solid var(--tm-border-light);
  border-radius: 8px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
  padding: 4px 0;
  min-width: 140px;
}

.context-menu-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 14px;
  font-size: 13px;
  color: var(--tm-text-primary);
  cursor: pointer;
  transition: background 0.15s ease;
}

.context-menu-item:hover {
  background: rgba(var(--tm-color-primary-rgb), 0.12);
}

.context-menu-item.danger {
  color: var(--el-color-danger);
}

.context-menu-item.danger:hover {
  background: rgba(var(--el-color-danger-rgb), 0.1);
}
</style>
