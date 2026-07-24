<template>
  <div class="upgrade-page">
    <header class="page-header">
      <div>
        <h1>缺陷中心</h1>
        <p>从失败运行一键建缺陷，并同步到 Jira / 禅道 / GitHub / Webhook（本地 stub 可替换为真实连接器）。</p>
      </div>
      <div class="actions">
        <el-button @click="load">刷新</el-button>
        <el-button type="primary" @click="showTracker = true">配置 Tracker</el-button>
      </div>
    </header>

    <el-row :gutter="16">
      <el-col :span="8">
        <el-card shadow="never">
          <template #header>Tracker</template>
          <el-empty v-if="!trackers.length" description="尚未配置" :image-size="56" />
          <div v-for="item in trackers" :key="item.id" class="tracker-item">
            <strong>{{ item.tracker_type }}</strong>
            <div class="muted">{{ item.base_url }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="16">
        <el-card shadow="never">
          <template #header>缺陷列表</template>
          <el-table :data="defects" v-loading="loading" height="480">
            <el-table-column prop="title" label="标题" min-width="220" />
            <el-table-column prop="status" label="状态" width="100" />
            <el-table-column prop="priority" label="优先级" width="90" />
            <el-table-column prop="external_id" label="外部 ID" width="140" />
            <el-table-column prop="created_at" label="创建时间" min-width="160" />
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <el-dialog v-model="showTracker" title="配置缺陷 Tracker" width="520px">
      <el-form label-width="100px">
        <el-form-item label="类型">
          <el-select v-model="trackerForm.tracker_type" style="width: 100%">
            <el-option label="Jira" value="jira" />
            <el-option label="禅道" value="zentao" />
            <el-option label="GitHub" value="github" />
            <el-option label="Webhook" value="webhook" />
          </el-select>
        </el-form-item>
        <el-form-item label="Base URL"><el-input v-model="trackerForm.base_url" placeholder="https://jira.example.com" /></el-form-item>
        <el-form-item label="Project Key"><el-input v-model="trackerForm.project_key" placeholder="TM" /></el-form-item>
        <el-form-item label="默认优先级"><el-input v-model="trackerForm.default_priority" placeholder="Medium" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showTracker = false">取消</el-button>
        <el-button type="primary" @click="saveTracker">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { storeToRefs } from 'pinia'
import { ElMessage } from 'element-plus'
import { featureUpgradesApi } from '@/api/feature-upgrades'
import { useProjectStore } from '@/stores/project'

const { projectId } = storeToRefs(useProjectStore())
const loading = ref(false)
const trackers = ref([])
const defects = ref([])
const showTracker = ref(false)
const trackerForm = reactive({
  tracker_type: 'jira',
  base_url: '',
  project_key: 'TM',
  default_priority: 'Medium',
})

async function load() {
  loading.value = true
  try {
    const [trackerRes, defectRes] = await Promise.all([
      featureUpgradesApi.listTrackers(projectId.value),
      featureUpgradesApi.listDefects(projectId.value),
    ])
    trackers.value = trackerRes.items || []
    defects.value = defectRes.items || []
  } catch (error) {
    ElMessage.error(error.message || '加载失败')
  } finally {
    loading.value = false
  }
}

async function saveTracker() {
  if (!trackerForm.base_url.trim()) return ElMessage.warning('请填写 Base URL')
  try {
    await featureUpgradesApi.upsertTracker(projectId.value, { ...trackerForm })
    showTracker.value = false
    ElMessage.success('Tracker 已保存')
    await load()
  } catch (error) {
    ElMessage.error(error.message || '保存 Tracker 失败')
  }
}

onMounted(load)
</script>

<style scoped>
.upgrade-page { padding: 20px; display: flex; flex-direction: column; gap: 16px; }
.page-header { display: flex; justify-content: space-between; gap: 12px; }
.page-header h1 { margin: 0 0 6px; font-size: 22px; }
.page-header p { margin: 0; color: #64748b; }
.actions { display: flex; gap: 8px; }
.tracker-item { padding: 10px 0; border-bottom: 1px solid #eef2f7; }
.muted { color: #64748b; font-size: 12px; margin-top: 4px; word-break: break-all; }
</style>
