<template>
  <div class="upgrade-page">
    <header class="page-header">
      <div>
        <h1>Flaky 检测</h1>
        <p>根据状态翻转与失败熵识别不稳定用例，支持隔离（quarantine）。</p>
      </div>
      <div class="actions">
        <el-select v-model="classification" clearable placeholder="分类" style="width: 160px" @change="load">
          <el-option label="高风险 flaky" value="flaky_high" />
          <el-option label="低风险 flaky" value="flaky_low" />
          <el-option label="稳定失败" value="stable_fail" />
          <el-option label="稳定通过" value="stable_pass" />
        </el-select>
        <el-switch v-model="onlyQuarantined" active-text="仅隔离" @change="load" />
        <el-button type="primary" @click="load">刷新</el-button>
      </div>
    </header>

    <el-table :data="items" v-loading="loading" stripe>
      <el-table-column prop="case_name" label="用例" min-width="180" />
      <el-table-column prop="case_type" label="类型" width="90" />
      <el-table-column prop="flaky_score" label="分数" width="100">
        <template #default="{ row }">
          <el-tag :type="scoreType(row.flaky_score)">{{ Number(row.flaky_score || 0).toFixed(3) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="classification" label="分类" width="120" />
      <el-table-column label="通过/失败" width="120">
        <template #default="{ row }">{{ row.pass_count || 0 }} / {{ row.fail_count || 0 }}</template>
      </el-table-column>
      <el-table-column prop="status_changes" label="翻转" width="80" />
      <el-table-column label="隔离" width="100">
        <template #default="{ row }">
          <el-tag :type="row.is_quarantined ? 'danger' : 'info'">{{ row.is_quarantined ? '是' : '否' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="160" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="toggleQuarantine(row)">
            {{ row.is_quarantined ? '解除隔离' : '隔离' }}
          </el-button>
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
const classification = ref()
const onlyQuarantined = ref(false)

function scoreType(score) {
  if (score >= 0.6) return 'danger'
  if (score >= 0.3) return 'warning'
  return 'success'
}

async function load() {
  loading.value = true
  try {
    const res = await featureUpgradesApi.listFlaky(projectId.value, {
      classification: classification.value || undefined,
      quarantined: onlyQuarantined.value ? true : undefined,
    })
    items.value = res.items || []
  } catch (error) {
    ElMessage.error(error.message || '加载失败')
  } finally {
    loading.value = false
  }
}

async function toggleQuarantine(row) {
  try {
    await featureUpgradesApi.setQuarantine(row.id, !row.is_quarantined)
    ElMessage.success(row.is_quarantined ? '已解除隔离' : '已隔离')
    await load()
  } catch (error) {
    ElMessage.error(error.message || '操作失败')
  }
}

onMounted(load)
</script>

<style scoped>
.upgrade-page { padding: 20px; display: flex; flex-direction: column; gap: 16px; }
.page-header { display: flex; justify-content: space-between; gap: 12px; }
.page-header h1 { margin: 0 0 6px; font-size: 22px; }
.page-header p { margin: 0; color: #64748b; }
.actions { display: flex; gap: 10px; align-items: center; }
</style>
