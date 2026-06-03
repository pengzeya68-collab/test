<template>
  <div class="ai-points-page">
    <div class="page-header">
      <h2>AI 积分管理</h2>
      <el-button type="primary" @click="showGrantDialog = true">充值积分</el-button>
    </div>

    <el-tabs v-model="activeTab" @tab-change="onTabChange">
      <!-- 积分配置 -->
      <el-tab-pane label="积分配置" name="config">
        <el-table :data="configs" v-loading="configLoading" stripe>
          <el-table-column prop="feature" label="功能标识" width="200" />
          <el-table-column prop="display_name" label="显示名称" width="180" />
          <el-table-column prop="points_cost" label="积分消耗" width="140">
            <template #default="{ row }">
              <el-input-number
                v-model="row.points_cost"
                :min="0"
                :max="9999"
                size="small"
                @change="handleCostChange(row)"
              />
            </template>
          </el-table-column>
          <el-table-column prop="description" label="说明" />
        </el-table>
      </el-tab-pane>

      <!-- 使用日志 -->
      <el-tab-pane label="使用日志" name="logs">
        <div class="filter-bar">
          <el-input v-model="logsFilter.userId" placeholder="用户ID" clearable style="width:140px" @clear="fetchLogs" />
          <el-select v-model="logsFilter.feature" placeholder="功能" clearable style="width:200px" @change="fetchLogs">
            <el-option v-for="c in configs" :key="c.feature" :label="c.display_name" :value="c.feature" />
          </el-select>
          <el-button @click="fetchLogs">查询</el-button>
        </div>
        <el-table :data="logs" v-loading="logsLoading" stripe>
          <el-table-column prop="id" label="ID" width="80" />
          <el-table-column prop="user_id" label="用户ID" width="90" />
          <el-table-column prop="username" label="用户名" width="120" />
          <el-table-column prop="feature_name" label="功能" width="160" />
          <el-table-column prop="points_cost" label="消耗积分" width="100" />
          <el-table-column prop="created_at" label="时间" width="180">
            <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
          </el-table-column>
        </el-table>
        <el-pagination
          v-if="logsTotal > 0"
          :current-page="logsFilter.page"
          :page-size="logsFilter.pageSize"
          :total="logsTotal"
          layout="total, prev, pager, next"
          @current-change="p => { logsFilter.page = p; fetchLogs() }"
          style="margin-top:12px;justify-content:flex-end"
        />
      </el-tab-pane>

      <!-- 积分流水 -->
      <el-tab-pane label="积分流水" name="transactions">
        <div class="filter-bar">
          <el-input v-model="txFilter.userId" placeholder="用户ID" clearable style="width:140px" @clear="fetchTransactions" />
          <el-select v-model="txFilter.txType" placeholder="类型" clearable style="width:180px" @change="fetchTransactions">
            <el-option label="每日签到" value="checkin" />
            <el-option label="项目实战" value="project" />
            <el-option label="积分购买" value="purchase" />
            <el-option label="管理员充值" value="admin_grant" />
            <el-option label="管理员扣减" value="admin_deduct" />
            <el-option label="AI 使用" value="ai_usage" />
            <el-option label="积分退还" value="refund" />
          </el-select>
          <el-button @click="fetchTransactions">查询</el-button>
        </div>
        <el-table :data="transactions" v-loading="txLoading" stripe>
          <el-table-column prop="id" label="ID" width="70" />
          <el-table-column prop="user_id" label="用户ID" width="80" />
          <el-table-column prop="username" label="用户名" width="110" />
          <el-table-column prop="amount" label="变动" width="90">
            <template #default="{ row }">
              <span :style="{ color: row.amount > 0 ? '#67c23a' : '#f56c6c' }">
                {{ row.amount > 0 ? '+' : '' }}{{ row.amount }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="balance_after" label="变动后余额" width="100" />
          <el-table-column prop="tx_type_name" label="类型" width="110" />
          <el-table-column prop="source" label="来源" width="140" />
          <el-table-column prop="related_feature" label="关联功能" width="140" />
          <el-table-column prop="note" label="备注" />
          <el-table-column prop="created_at" label="时间" width="170">
            <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
          </el-table-column>
        </el-table>
        <el-pagination
          v-if="txTotal > 0"
          :current-page="txFilter.page"
          :page-size="txFilter.pageSize"
          :total="txTotal"
          layout="total, prev, pager, next"
          @current-change="p => { txFilter.page = p; fetchTransactions() }"
          style="margin-top:12px;justify-content:flex-end"
        />
      </el-tab-pane>

      <!-- 使用统计 -->
      <el-tab-pane label="使用统计" name="stats">
        <el-table :data="usageStats" v-loading="statsLoading" stripe>
          <el-table-column prop="feature" label="功能标识" width="200" />
          <el-table-column prop="display_name" label="显示名称" width="180" />
          <el-table-column prop="total_calls" label="调用次数" width="120" />
          <el-table-column prop="total_points" label="总消耗积分" width="140" />
        </el-table>
      </el-tab-pane>
    </el-tabs>

    <!-- 充值弹窗 -->
    <el-dialog v-model="showGrantDialog" title="管理员充值积分" width="440px">
      <el-form :model="grantForm" label-width="80px">
        <el-form-item label="用户ID">
          <el-input-number v-model="grantForm.userId" :min="1" style="width:100%" />
        </el-form-item>
        <el-form-item label="积分数量">
          <el-input-number v-model="grantForm.amount" :min="1" :max="999999" style="width:100%" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="grantForm.note" placeholder="可选" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showGrantDialog = false">取消</el-button>
        <el-button type="danger" @click="handleDeduct">扣减</el-button>
        <el-button type="primary" @click="handleGrant">充值</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '@/utils/request'

const activeTab = ref('config')

// ── 积分配置 ──
const configs = ref([])
const configLoading = ref(false)

const fetchConfigs = async () => {
  configLoading.value = true
  try {
    const res = await request.get('/admin/ai-points/config')
    configs.value = res?.data || res || []
  } catch (e) {
    ElMessage.error('获取积分配置失败')
  } finally {
    configLoading.value = false
  }
}

const handleCostChange = async (row) => {
  try {
    await request.put(`/admin/ai-points/config/${row.feature}`, { points_cost: row.points_cost })
    ElMessage.success(`${row.display_name} 积分已更新为 ${row.points_cost}`)
  } catch (e) {
    ElMessage.error('更新失败')
    fetchConfigs()
  }
}

// ── 使用日志 ──
const logs = ref([])
const logsTotal = ref(0)
const logsLoading = ref(false)
const logsFilter = reactive({ userId: '', feature: '', page: 1, pageSize: 20 })

const fetchLogs = async () => {
  logsLoading.value = true
  try {
    const params = { page: logsFilter.page, page_size: logsFilter.pageSize }
    if (logsFilter.userId) params.user_id = logsFilter.userId
    if (logsFilter.feature) params.feature = logsFilter.feature
    const res = await request.get('/admin/ai-points/logs', { params })
    const data = res?.data || res || {}
    logs.value = data.items || []
    logsTotal.value = data.total || 0
  } catch (e) {
    ElMessage.error('获取日志失败')
  } finally {
    logsLoading.value = false
  }
}

// ── 积分流水 ──
const transactions = ref([])
const txTotal = ref(0)
const txLoading = ref(false)
const txFilter = reactive({ userId: '', txType: '', page: 1, pageSize: 20 })

const fetchTransactions = async () => {
  txLoading.value = true
  try {
    const params = { page: txFilter.page, page_size: txFilter.pageSize }
    if (txFilter.userId) params.user_id = txFilter.userId
    if (txFilter.txType) params.tx_type = txFilter.txType
    const res = await request.get('/admin/ai-points/transactions', { params })
    const data = res?.data || res || {}
    transactions.value = data.items || []
    txTotal.value = data.total || 0
  } catch (e) {
    ElMessage.error('获取流水失败')
  } finally {
    txLoading.value = false
  }
}

// ── 使用统计 ──
const usageStats = ref([])
const statsLoading = ref(false)

const fetchStats = async () => {
  statsLoading.value = true
  try {
    const res = await request.get('/admin/ai-points/logs/stats')
    usageStats.value = res?.data || res || []
  } catch (e) {
    ElMessage.error('获取统计失败')
  } finally {
    statsLoading.value = false
  }
}

// ── 充值/扣减 ──
const showGrantDialog = ref(false)
const grantForm = reactive({ userId: null, amount: 100, note: '' })

const handleGrant = async () => {
  if (!grantForm.userId) return ElMessage.warning('请输入用户ID')
  try {
    const res = await request.post('/admin/ai-points/grant', {
      user_id: grantForm.userId,
      amount: grantForm.amount,
      note: grantForm.note || undefined,
    })
    ElMessage.success(res?.data?.message || res?.message || '充值成功')
    showGrantDialog.value = false
    if (activeTab.value === 'transactions') fetchTransactions()
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || '充值失败')
  }
}

const handleDeduct = async () => {
  if (!grantForm.userId) return ElMessage.warning('请输入用户ID')
  try {
    await ElMessageBox.confirm(
      `确定要扣减用户 ${grantForm.userId} 的 ${grantForm.amount} 积分吗？`,
      '确认扣减',
      { confirmButtonText: '确定扣减', cancelButtonText: '取消', type: 'warning' }
    )
  } catch {
    return // 用户取消
  }
  try {
    const res = await request.post('/admin/ai-points/deduct', {
      user_id: grantForm.userId,
      amount: grantForm.amount,
      note: grantForm.note || undefined,
    })
    ElMessage.success(res?.data?.message || res?.message || '扣减成功')
    showGrantDialog.value = false
    if (activeTab.value === 'transactions') fetchTransactions()
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || '扣减失败')
  }
}

// ── 工具 ──
const formatTime = (t) => {
  if (!t) return ''
  return new Date(t).toLocaleString('zh-CN', {
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit', second: '2-digit',
  })
}

const loadedTabs = ref(new Set(['config']))
const onTabChange = (tab) => {
  if (!loadedTabs.value.has(tab)) {
    loadedTabs.value.add(tab)
    if (tab === 'logs') fetchLogs()
    if (tab === 'transactions') fetchTransactions()
    if (tab === 'stats') fetchStats()
  }
}

onMounted(() => {
  fetchConfigs()
})
</script>

<style scoped>
.ai-points-page {
  padding: 0;
}
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.page-header h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: var(--tm-text-primary);
}
.filter-bar {
  display: flex;
  gap: 10px;
  margin-bottom: 14px;
  align-items: center;
}
</style>
