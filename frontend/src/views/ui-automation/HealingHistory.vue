<template>
  <div class="upgrade-page">
    <header class="page-header">
      <div>
        <h1>自愈历史</h1>
        <p>审核 AI / 启发式定位器自愈建议，仅 auto_applied 会在运行时生效。</p>
      </div>
      <div class="actions">
        <el-select v-model="status" clearable placeholder="状态" style="width: 160px" @change="load">
          <el-option label="建议中" value="suggested" />
          <el-option label="已自动应用" value="auto_applied" />
          <el-option label="已接受" value="accepted" />
          <el-option label="已拒绝" value="rejected" />
        </el-select>
        <el-button type="primary" @click="load">刷新</el-button>
      </div>
    </header>

    <el-table :data="items" v-loading="loading" stripe>
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="element_id" label="元素" width="90" />
      <el-table-column prop="status" label="状态" width="120">
        <template #default="{ row }">
          <el-tag :type="statusType(row.status)">{{ row.status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="strategy_used" label="策略" width="120" />
      <el-table-column prop="confidence" label="置信度" width="100">
        <template #default="{ row }">{{ Number(row.confidence || 0).toFixed(2) }}</template>
      </el-table-column>
      <el-table-column label="原定位器" min-width="180">
        <template #default="{ row }">
          <code>{{ formatLocator(row.original_locator) }}</code>
        </template>
      </el-table-column>
      <el-table-column label="自愈定位器" min-width="180">
        <template #default="{ row }">
          <code>{{ formatLocator(row.healed_locator) }}</code>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="时间" min-width="160" />
      <el-table-column label="操作" width="180" fixed="right">
        <template #default="{ row }">
          <el-button v-if="row.status === 'suggested'" link type="success" @click="review(row, 'accept')">接受</el-button>
          <el-button v-if="row.status === 'suggested'" link type="danger" @click="review(row, 'reject')">拒绝</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { storeToRefs } from 'pinia'
import { ElMessage } from 'element-plus'
import { featureUpgradesApi } from '@/api/feature-upgrades'
import { useProjectStore } from '@/stores/project'

const { projectId } = storeToRefs(useProjectStore())
const loading = ref(false)
const items = ref([])
const status = ref()

function statusType(s) {
  if (s === 'auto_applied' || s === 'accepted') return 'success'
  if (s === 'rejected') return 'danger'
  return 'warning'
}

function formatLocator(loc) {
  if (!loc) return '—'
  if (typeof loc === 'string') return loc
  return `${loc.strategy || '?'}=${loc.value || ''}`
}

async function load() {
  loading.value = true
  try {
    const res = await featureUpgradesApi.listHealing(projectId.value, {
      status: status.value || undefined,
    })
    items.value = res.items || []
  } catch (error) {
    ElMessage.error(error.message || '加载失败')
  } finally {
    loading.value = false
  }
}

async function review(row, action) {
  try {
    await featureUpgradesApi.reviewHealing(row.id, action)
    ElMessage.success(action === 'accept' ? '已接受' : '已拒绝')
    await load()
  } catch (error) {
    ElMessage.error(error.message || '审核失败')
  }
}

onMounted(load)
</script>

<style scoped>
.upgrade-page { padding: 20px; display: flex; flex-direction: column; gap: 16px; }
.page-header { display: flex; justify-content: space-between; gap: 12px; }
.page-header h1 { margin: 0 0 6px; font-size: 22px; }
.page-header p { margin: 0; color: #64748b; }
.actions { display: flex; gap: 8px; align-items: center; }
code { font-size: 12px; color: #0f766e; word-break: break-all; }
</style>
