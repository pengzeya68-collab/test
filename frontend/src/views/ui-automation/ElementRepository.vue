<template>
  <div class="upgrade-page">
    <header class="page-header">
      <div>
        <h1>元素仓库</h1>
        <p>集中管理页面对象与定位器，支持步骤绑定与 AI 自愈。</p>
      </div>
      <div class="actions">
        <el-button @click="load">刷新</el-button>
        <el-button type="primary" @click="showCreatePage = true">新建页面</el-button>
        <el-button type="success" :disabled="!selectedPageId" @click="showCreateElement = true">新建元素</el-button>
      </div>
    </header>

    <div class="layout">
      <el-card class="panel" shadow="never">
        <template #header>页面</template>
        <el-menu :default-active="String(selectedPageId || '')" @select="onSelectPage">
          <el-menu-item v-for="page in pages" :key="page.id" :index="String(page.id)">
            {{ page.name }}
          </el-menu-item>
        </el-menu>
        <el-empty v-if="!pages.length" description="暂无页面" :image-size="64" />
      </el-card>

      <el-card class="panel grow" shadow="never">
        <template #header>
          <div class="panel-title">
            <span>元素列表</span>
            <el-tag size="small">project #{{ projectId }}</el-tag>
          </div>
        </template>
        <el-table :data="elements" v-loading="loading" height="100%">
          <el-table-column prop="name" label="名称" min-width="140" />
          <el-table-column label="主定位器" min-width="220">
            <template #default="{ row }">
              <code v-if="row.locators?.length">{{ row.locators[0].strategy }}={{ row.locators[0].value }}</code>
            </template>
          </el-table-column>
          <el-table-column prop="usage_count" label="引用" width="80" />
          <el-table-column prop="heal_count" label="自愈" width="80" />
          <el-table-column prop="updated_at" label="更新时间" min-width="160" />
        </el-table>
      </el-card>
    </div>

    <el-dialog v-model="showCreatePage" title="新建页面" width="480px">
      <el-form label-width="90px">
        <el-form-item label="名称"><el-input v-model="pageForm.name" /></el-form-item>
        <el-form-item label="URL 模式"><el-input v-model="pageForm.url_pattern" placeholder="/login*" /></el-form-item>
        <el-form-item label="描述"><el-input v-model="pageForm.description" type="textarea" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreatePage = false">取消</el-button>
        <el-button type="primary" @click="createPage">创建</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showCreateElement" title="新建元素" width="560px">
      <el-form label-width="90px">
        <el-form-item label="名称"><el-input v-model="elementForm.name" /></el-form-item>
        <el-form-item label="策略">
          <el-select v-model="elementForm.strategy" style="width: 100%">
            <el-option v-for="s in strategies" :key="s" :label="s" :value="s" />
          </el-select>
        </el-form-item>
        <el-form-item label="值"><el-input v-model="elementForm.value" /></el-form-item>
        <el-form-item label="描述"><el-input v-model="elementForm.description" type="textarea" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateElement = false">取消</el-button>
        <el-button type="primary" @click="createElement">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { featureUpgradesApi } from '@/api/feature-upgrades'
import { useProjectStore } from '@/stores/project'
import { storeToRefs } from 'pinia'

const projectStore = useProjectStore()
const { projectId } = storeToRefs(projectStore)
const loading = ref(false)
const pages = ref([])
const elements = ref([])
const selectedPageId = ref(null)
const showCreatePage = ref(false)
const showCreateElement = ref(false)
const strategies = ['test_id', 'role', 'label', 'placeholder', 'text', 'css', 'xpath']
const pageForm = reactive({ name: '', url_pattern: '', description: '' })
const elementForm = reactive({ name: '', strategy: 'test_id', value: '', description: '' })

async function load() {
  loading.value = true
  try {
    const pageRes = await featureUpgradesApi.listPages(projectId.value)
    pages.value = pageRes.items || []
    if (!selectedPageId.value && pages.value.length) selectedPageId.value = pages.value[0].id
    if (selectedPageId.value) await loadElements()
  } catch (error) {
    ElMessage.error(error.message || '加载失败')
  } finally {
    loading.value = false
  }
}

async function loadElements() {
  try {
    const res = await featureUpgradesApi.listElements(projectId.value, selectedPageId.value)
    elements.value = res.items || []
  } catch (error) {
    elements.value = []
    ElMessage.error(error.message || '加载元素失败')
  }
}

async function onSelectPage(id) {
  selectedPageId.value = Number(id)
  await loadElements()
}

async function createPage() {
  if (!pageForm.name.trim()) return ElMessage.warning('请输入页面名称')
  try {
    await featureUpgradesApi.createPage({ project_id: projectId.value, ...pageForm })
    showCreatePage.value = false
    pageForm.name = ''
    pageForm.url_pattern = ''
    pageForm.description = ''
    ElMessage.success('页面已创建')
    await load()
  } catch (error) {
    ElMessage.error(error.message || '创建页面失败')
  }
}

async function createElement() {
  if (!selectedPageId.value) return
  if (!elementForm.name.trim() || !elementForm.value.trim()) return ElMessage.warning('请完善元素信息')
  try {
    await featureUpgradesApi.createElement({
      project_id: projectId.value,
      page_id: selectedPageId.value,
      name: elementForm.name,
      description: elementForm.description,
      locators: [{ strategy: elementForm.strategy, value: elementForm.value, options: {}, fallbacks: [], framePath: [] }],
    })
    showCreateElement.value = false
    elementForm.name = ''
    elementForm.value = ''
    elementForm.description = ''
    ElMessage.success('元素已创建')
    await loadElements()
  } catch (error) {
    ElMessage.error(error.message || '创建元素失败')
  }
}

onMounted(load)
</script>

<style scoped>
.upgrade-page { padding: 20px; height: 100%; box-sizing: border-box; display: flex; flex-direction: column; gap: 16px; }
.page-header { display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; }
.page-header h1 { margin: 0 0 6px; font-size: 22px; }
.page-header p { margin: 0; color: #64748b; }
.actions { display: flex; gap: 8px; }
.layout { flex: 1; min-height: 0; display: grid; grid-template-columns: 260px 1fr; gap: 16px; }
.panel { min-height: 0; overflow: auto; }
.panel.grow { display: flex; flex-direction: column; }
.panel-title { display: flex; justify-content: space-between; align-items: center; }
code { font-size: 12px; color: #0f766e; }
</style>
