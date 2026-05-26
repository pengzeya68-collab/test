<template>
  <div class="page-layout">
    <div class="left-panel">
      <div class="panel-header">
        <span class="panel-title">📁 接口分组</span>
        <el-dropdown trigger="click" @command="handleFolderCommand">
          <el-button type="primary" size="small" class="btn-more">
            <el-icon><MoreFilled /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="createRoot">新建根分组</el-dropdown-item>
              <el-dropdown-item command="createChild" :disabled="!currentGroup">新建子分组</el-dropdown-item>
              <el-dropdown-item command="editGroup" :disabled="!currentGroup">编辑分组</el-dropdown-item>
              <el-dropdown-item command="deleteGroup" :disabled="!currentGroup" divided>删除分组</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>

      <div class="folder-tree" v-loading="loadingGroups">
        <el-tree
          ref="folderTreeRef"
          :data="groupTreeData"
          :props="{ children: 'children', label: 'name' }"
          node-key="id"
          default-expand-all
          highlight-current
          @node-click="handleGroupSelect"
        >
          <template #default="{ node, data }">
            <span class="tree-node">
              <span class="node-icon">{{ data.children?.length ? '📂' : '📁' }}</span>
              <span class="node-label">{{ node.label }}</span>
              <span class="node-count">({{ data.case_count || 0 }})</span>
            </span>
          </template>
        </el-tree>
      </div>
    </div>

    <div class="right-panel">
      <CaseList
        ref="caseListRef"
        :group-id="currentGroupId"
        :environment-list="environmentList"
        @run="(caseData, envId) => emit('run-cases', caseData, envId)"
      />
    </div>
  </div>

  <el-dialog
    v-model="folderDialogVisible"
    :title="folderDialogType === 'edit' ? '编辑分组' : '新建分组'"
    width="420px"
    custom-class="dark-dialog"
  >
    <el-form :model="folderForm" label-width="60px">
      <el-form-item label="名称">
        <el-input v-model="folderForm.name" placeholder="输入分组名称" class="dark-input" />
      </el-form-item>
      <el-form-item label="描述">
        <el-input v-model="folderForm.description" placeholder="可选描述" class="dark-input" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="folderDialogVisible = false" class="btn-cancel">取消</el-button>
      <el-button type="primary" @click="handleFolderSave" class="btn-primary">确定</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { MoreFilled } from '@element-plus/icons-vue'
import CaseList from './CaseList.vue'
import autoTestRequest from '@/utils/autoTestRequest'

const props = defineProps({
  environmentList: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['run-cases'])

const folderTreeRef = ref(null)
const groupTreeData = ref([])
const currentGroup = ref(null)
const currentGroupId = ref(null)
const loadingGroups = ref(false)
const folderDialogVisible = ref(false)
const folderDialogType = ref('create')
const folderForm = ref({ name: '', description: '', parentId: null })
const caseListRef = ref(null)

const loadGroups = async () => {
  loadingGroups.value = true
  try {
    const res = await autoTestRequest.get('/auto-test/groups/tree')
    groupTreeData.value = res || []
  } catch (error) {
    console.error('加载分组失败:', error)
    ElMessage.error('加载分组失败')
  } finally {
    loadingGroups.value = false
  }
}

const handleGroupSelect = (data) => {
  currentGroup.value = data
  currentGroupId.value = data.id
  refreshCaseList()
}

const handleFolderCommand = (command) => {
  switch (command) {
    case 'createRoot':
      folderDialogType.value = 'create'
      folderForm.value = { name: '', description: '', parentId: null }
      folderDialogVisible.value = true
      break
    case 'createChild':
      folderDialogType.value = 'create'
      folderForm.value = { name: '', description: '', parentId: currentGroup.value?.id }
      folderDialogVisible.value = true
      break
    case 'editGroup':
      folderDialogType.value = 'edit'
      folderForm.value = {
        id: currentGroup.value?.id,
        name: currentGroup.value?.name,
        description: currentGroup.value?.description
      }
      folderDialogVisible.value = true
      break
    case 'deleteGroup':
      handleDeleteFolder()
      break
  }
}

const handleFolderSave = async () => {
  if (!folderForm.value.name) {
    ElMessage.warning('请输入分组名称')
    return
  }
  try {
    if (folderDialogType.value === 'edit') {
      await autoTestRequest.put(`/auto-test/groups/${folderForm.value.id}`, {
        name: folderForm.value.name,
        description: folderForm.value.description
      })
      ElMessage.success('更新成功')
    } else {
      await autoTestRequest.post('/auto-test/groups', {
        name: folderForm.value.name,
        description: folderForm.value.description,
        parent_id: folderForm.value.parentId
      })
      ElMessage.success('创建成功')
    }
    folderDialogVisible.value = false
    loadGroups()
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

const handleDeleteFolder = async () => {
  if (!currentGroup.value) return
  try {
    await ElMessageBox.confirm(
      `确定要删除分组 "${currentGroup.value.name}" 吗？分组下的用例将被删除。`,
      '删除确认',
      { type: 'warning' }
    )
    await autoTestRequest.delete(`/auto-test/groups/${currentGroup.value.id}`)
    ElMessage.success('删除成功')
    currentGroup.value = null
    currentGroupId.value = null
    refreshCaseList()
    loadGroups()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const refreshCaseList = () => {
  if (caseListRef.value) {
    caseListRef.value.loadCases()
  }
}

onMounted(() => {
  loadGroups()
})

defineExpose({ refreshCaseList })
</script>

<style scoped>
.page-layout {
  display: flex;
  height: calc(100vh - 220px);
  gap: 20px;
}

.left-panel {
  width: 300px;
  background: var(--tm-bg-card);
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border: 1px solid var(--tm-border-light);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 18px 20px;
  border-bottom: 1px solid var(--border-subtle);
  flex-shrink: 0;
  background: var(--tm-bg-card);
}

.panel-title {
  font-weight: 600;
  font-size: 16px;
  color: var(--tm-text-primary);
  text-shadow: 0 0 10px rgba(var(--tm-color-primary-rgb), 0.3);
}

.btn-more {
  background: transparent;
  border: 1px solid var(--tm-color-primary);
  color: var(--tm-color-primary);
  border-radius: 8px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.btn-more:hover {
  background: rgba(var(--tm-color-primary-rgb), 0.2);
  box-shadow: 0 0 15px rgba(var(--tm-color-primary-rgb), 0.4);
  transform: translateY(-1px);
}

.folder-tree {
  flex: 1;
  overflow: auto;
  padding: 16px;
}

.tree-node {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  color: var(--text-secondary);
  border-radius: 8px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  margin-bottom: 4px;
}

:deep(.el-tree .el-tree-node.is-current > .el-tree-node__content) {
  background-color: rgba(var(--tm-color-primary-rgb), 0.15) !important;
  border-radius: 8px;
}

:deep(.el-tree .el-tree-node__content:hover) {
  background-color: rgba(var(--tm-color-primary-rgb), 0.1) !important;
  border-radius: 8px;
}

:deep(.el-tree .el-tree-node.is-current > .el-tree-node__content .tree-node) {
  color: var(--text-primary);
}

.node-icon {
  font-size: 16px;
  text-shadow: 0 0 5px rgba(var(--tm-color-primary-rgb), 0.5);
}

.node-label {
  flex: 1;
  font-size: 14px;
  color: var(--tm-text-primary);
  transition: color 0.3s ease;
}

.tree-node:hover .node-label {
  color: var(--tm-color-primary);
  text-shadow: 0 0 5px rgba(var(--tm-color-primary-rgb), 0.5);
}

.node-count {
  color: var(--tm-color-primary);
  font-size: 12px;
  background: rgba(var(--tm-color-primary-rgb), 0.2);
  padding: 4px 10px;
  border-radius: 12px;
  border: 1px solid rgba(var(--tm-color-primary-rgb), 0.4);
  box-shadow: 0 0 8px rgba(var(--tm-color-primary-rgb), 0.3);
}

.right-panel {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  background: var(--tm-bg-card);
  border-radius: 12px;
  border: 1px solid var(--tm-border-light);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
}

.dark-empty {
  color: var(--tm-text-secondary);
}

.dark-empty :deep(.el-empty__description) {
  color: var(--tm-text-secondary);
}

@media (max-width: 768px) {
  .page-layout {
    flex-direction: column;
    height: auto;
    min-height: 80vh;
  }

  .left-panel {
    width: 100%;
    max-height: 300px;
    margin-bottom: 20px;
  }
}

@media (min-width: 769px) and (max-width: 1024px) {
  .left-panel {
    width: 250px;
  }
}

@media (min-width: 1200px) {
  .left-panel {
    width: 320px;
  }

  .right-panel {
    flex: 1;
  }
}
</style>