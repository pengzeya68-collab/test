<template>
  <div class="upgrade-page">
    <header class="page-header">
      <div>
        <h1>分片进度</h1>
        <p>套件并行执行分片进度看板（suite_execution_id 通常等于 UI suite run id）。</p>
      </div>
      <div class="actions">
        <el-input-number v-model="suiteExecutionId" :min="1" />
        <el-button type="primary" @click="load">查询</el-button>
        <el-switch v-model="autoRefresh" active-text="自动刷新" />
      </div>
    </header>

    <el-row :gutter="12" v-if="progress">
      <el-col :span="6"><el-statistic title="分片数" :value="progress.shard_count || (progress.shards || []).length || 0" /></el-col>
      <el-col :span="6"><el-statistic title="已完成" :value="progress.completed || 0" /></el-col>
      <el-col :span="6"><el-statistic title="通过" :value="progress.passed || 0" /></el-col>
      <el-col :span="6"><el-statistic title="失败" :value="progress.failed || 0" /></el-col>
    </el-row>

    <el-table :data="shards" v-loading="loading" stripe>
      <el-table-column prop="id" label="分片 ID" width="90" />
      <el-table-column prop="shard_index" label="序号" width="80" />
      <el-table-column prop="status" label="状态" width="120" />
      <el-table-column prop="agent_id" label="Agent" width="100" />
      <el-table-column label="进度" min-width="180">
        <template #default="{ row }">
          {{ row.completed_cases || 0 }} / {{ (row.case_ids || []).length || row.total_cases || 0 }}
        </template>
      </el-table-column>
      <el-table-column prop="passed_cases" label="通过" width="80" />
      <el-table-column prop="failed_cases" label="失败" width="80" />
      <el-table-column label="用例" min-width="200">
        <template #default="{ row }">
          <code>{{ (row.case_ids || []).join(', ') }}</code>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { featureUpgradesApi } from '@/api/feature-upgrades'

const suiteExecutionId = ref(1)
const loading = ref(false)
const progress = ref(null)
const shards = ref([])
const autoRefresh = ref(false)
let timer = null

async function load() {
  loading.value = true
  try {
    const res = await featureUpgradesApi.getShardProgress(suiteExecutionId.value)
    progress.value = res
    shards.value = res.shards || res.items || []
  } catch (error) {
    ElMessage.error(error.message || '加载失败')
  } finally {
    loading.value = false
  }
}

watch(autoRefresh, (on) => {
  if (timer) {
    clearInterval(timer)
    timer = null
  }
  if (on) timer = setInterval(load, 5000)
})

onMounted(load)
onBeforeUnmount(() => {
  if (timer) clearInterval(timer)
})
</script>

<style scoped>
.upgrade-page { padding: 20px; display: flex; flex-direction: column; gap: 16px; }
.page-header { display: flex; justify-content: space-between; gap: 12px; }
.page-header h1 { margin: 0 0 6px; font-size: 22px; }
.page-header p { margin: 0; color: #64748b; }
.actions { display: flex; gap: 10px; align-items: center; }
code { font-size: 12px; color: #0f766e; }
</style>
