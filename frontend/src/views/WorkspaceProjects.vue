<template>
  <section class="workspace-projects">
    <div class="page-head">
      <div>
        <h2>工作区项目</h2>
        <p>资产按项目隔离；新建第二项目后用例与执行互不可见。</p>
      </div>
      <el-button type="primary" :loading="creating" @click="createProject">新建项目</el-button>
    </div>

    <el-table v-loading="loading" :data="projects" stripe empty-text="暂无项目">
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="name" label="名称" min-width="160" />
      <el-table-column prop="key" label="Key" min-width="140" />
      <el-table-column prop="role" label="角色" width="100" />
      <el-table-column label="类型" width="120">
        <template #default="{ row }">{{ row.is_personal ? '个人项目' : '团队项目' }}</template>
      </el-table-column>
      <el-table-column label="操作" width="190">
        <template #default="{ row }">
          <el-button link type="primary" @click="activate(row)">设为当前</el-button>
          <el-button
            v-if="!row.is_personal"
            link
            type="danger"
            :loading="deletingId === row.id"
            @click="deleteProject(row)"
          >删除</el-button>
        </template>
      </el-table-column>
    </el-table>
  </section>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { workspaceApi, getActiveProjectId } from '@/api/workspace'
import { useProjectStore } from '@/stores/project'

const projectStore = useProjectStore()
const loading = ref(false)
const creating = ref(false)
const deletingId = ref(null)
const projects = ref([])
const activeId = ref(getActiveProjectId())

async function load() {
  loading.value = true
  try {
    const data = await workspaceApi.listProjects()
    projects.value = data?.items || []
    activeId.value = getActiveProjectId() || data?.active_project_id
    if (activeId.value) projectStore.setProjectId(activeId.value)
  } catch (error) {
    ElMessage.error(error.message || '加载项目失败')
  } finally {
    loading.value = false
  }
}

function activate(row) {
  projectStore.setProjectId(row.id)
  activeId.value = row.id
  ElMessage.success(`已切换到项目：${row.name}`)
}

async function createProject() {
  try {
    const { value } = await ElMessageBox.prompt('请输入新项目名称', '新建项目', {
      confirmButtonText: '创建',
      cancelButtonText: '取消',
      inputPattern: /.+/,
      inputErrorMessage: '名称不能为空',
    })
    creating.value = true
    const created = await workspaceApi.createProject({ name: value.trim() })
    ElMessage.success('项目已创建')
    await load()
    if (created?.id) activate(created)
    window.dispatchEvent(new Event('testmaster-projects-changed'))
  } catch (error) {
    if (error === 'cancel' || error === 'close') return
    ElMessage.error(error.message || '创建失败')
  } finally {
    creating.value = false
  }
}

async function deleteProject(row) {
  try {
    await ElMessageBox.confirm(
      `删除“${row.name}”前必须先清理该项目的成员和所有测试资产。确认继续？`,
      '删除团队项目',
      { confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning' },
    )
    deletingId.value = row.id
    await workspaceApi.deleteProject(row.id)
    if (Number(activeId.value) === Number(row.id)) {
      activeId.value = null
      projectStore.resetToUserWorkspace()
    }
    ElMessage.success('项目已删除')
    await load()
    window.dispatchEvent(new Event('testmaster-projects-changed'))
  } catch (error) {
    if (error === 'cancel' || error === 'close') return
    ElMessage.error(error?.response?.data?.detail?.message || error.message || '删除项目失败')
  } finally {
    deletingId.value = null
  }
}

onMounted(load)
</script>

<style scoped>
.workspace-projects { max-width: 960px; }
.page-head { display:flex; align-items:flex-start; justify-content:space-between; gap:16px; margin-bottom:16px; }
.page-head h2 { margin:0; font-size:18px; }
.page-head p { margin:6px 0 0; color:var(--text-secondary); font-size:13px; }
</style>
