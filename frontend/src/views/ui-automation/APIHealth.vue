<template>
  <div class="upgrade-page">
    <header class="page-header">
      <div>
        <h1>API 健康监控</h1>
        <p>周期性探测接口可用性、状态码与响应时间。</p>
      </div>
      <div class="actions">
        <el-button @click="load">刷新</el-button>
        <el-button type="primary" @click="showCreate = true">新建监控</el-button>
      </div>
    </header>

    <el-table :data="monitors" v-loading="loading" stripe>
      <el-table-column prop="name" label="名称" min-width="160" />
      <el-table-column prop="case_id" label="用例" width="90" />
      <el-table-column prop="environment_id" label="环境" width="90" />
      <el-table-column prop="interval_seconds" label="间隔(s)" width="100" />
      <el-table-column prop="expected_status" label="期望状态" width="100" />
      <el-table-column prop="is_active" label="启用" width="80">
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'info'">{{ row.is_active ? '是' : '否' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="last_status" label="最近状态" width="110" />
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="runCheck(row)">立即检查</el-button>
          <el-button link @click="viewResults(row)">结果</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="showCreate" title="新建健康监控" width="480px">
      <el-form label-width="120px">
        <el-form-item label="名称"><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="用例 ID"><el-input-number v-model="form.case_id" :min="1" style="width: 100%" /></el-form-item>
        <el-form-item label="环境 ID"><el-input-number v-model="form.environment_id" :min="1" style="width: 100%" /></el-form-item>
        <el-form-item label="间隔秒"><el-input-number v-model="form.interval_seconds" :min="30" :max="86400" style="width: 100%" /></el-form-item>
        <el-form-item label="期望状态码"><el-input-number v-model="form.expected_status" :min="100" :max="599" style="width: 100%" /></el-form-item>
        <el-form-item label="最大响应 ms"><el-input-number v-model="form.max_response_time_ms" :min="0" style="width: 100%" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreate = false">取消</el-button>
        <el-button type="primary" @click="create">创建</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showResults" :title="`检查结果 #${activeMonitorId}`" width="720px">
      <el-table :data="results" height="400">
        <el-table-column prop="status" label="状态" width="100" />
        <el-table-column prop="http_status" label="HTTP" width="90" />
        <el-table-column prop="duration_ms" label="耗时" width="100" />
        <el-table-column prop="error" label="错误" min-width="200" show-overflow-tooltip />
        <el-table-column prop="checked_at" label="时间" min-width="160" />
      </el-table>
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
const monitors = ref([])
const results = ref([])
const showCreate = ref(false)
const showResults = ref(false)
const activeMonitorId = ref(null)
const form = reactive({
  name: '',
  case_id: 1,
  environment_id: 1,
  interval_seconds: 300,
  expected_status: 200,
  max_response_time_ms: 5000,
  is_active: true,
})

async function load() {
  loading.value = true
  try {
    const res = await featureUpgradesApi.listHealthMonitors(projectId.value)
    monitors.value = res.items || []
  } catch (error) {
    ElMessage.error(error.message || '加载失败')
  } finally {
    loading.value = false
  }
}

async function create() {
  if (!form.name.trim()) return ElMessage.warning('请填写名称')
  try {
    await featureUpgradesApi.createHealthMonitor(projectId.value, { ...form })
    showCreate.value = false
    ElMessage.success('监控已创建')
    await load()
  } catch (error) {
    ElMessage.error(error.message || '创建监控失败')
  }
}

async function runCheck(row) {
  try {
    await featureUpgradesApi.runHealthCheck(row.id, {})
    ElMessage.success('检查完成')
    await load()
  } catch (error) {
    ElMessage.error(error.message || '检查失败')
  }
}

async function viewResults(row) {
  try {
    activeMonitorId.value = row.id
    const res = await featureUpgradesApi.listHealthResults(row.id)
    results.value = res.items || []
    showResults.value = true
  } catch (error) {
    ElMessage.error(error.message || '加载检查结果失败')
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
</style>
