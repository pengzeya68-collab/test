<template>
  <div class="points-page">
    <div class="points-header">
      <button class="back-btn" @click="router.push('/profile')">鈫?杩斿洖</button>
      <h1>鎴戠殑绉垎</h1>
    </div>

    <!-- 绉垎姒傝 -->
    <div class="overview-cards">
      <div class="overview-card main-card">
        <div class="card-icon">馃挵</div>
        <div class="card-info">
          <div class="card-value">{{ balance }}</div>
          <div class="card-label">褰撳墠绉垎</div>
        </div>
      </div>
      <div class="overview-card">
        <div class="card-icon">馃搳</div>
        <div class="card-info">
          <div class="card-value">{{ totalUsed }}</div>
          <div class="card-label">绱娑堣€</div>
        </div>
      </div>
      <div class="overview-card">
        <div class="card-icon">馃</div>
        <div class="card-info">
          <div class="card-value">{{ totalCalls }}</div>
          <div class="card-label">AI 璋冪敤娆℃暟</div>
        </div>
      </div>
    </div>

    <!-- Tab 鍒囨崲 -->
    <div class="tab-bar">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        class="tab-btn"
        :class="{ active: activeTab === tab.key }"
        @click="activeTab = tab.key"
      >{{ tab.label }}</button>
    </div>

    <!-- 绉垎娴佹按 -->
    <div v-if="activeTab === 'transactions'" class="tab-content">
      <div class="filter-row">
        <select v-model="txFilter.txType" class="filter-select" @change="fetchTransactions">
          <option value="">鍏ㄩ儴绫诲瀷</option>
          <option value="checkin">姣忔棩绛惧埌</option>
          <option value="project">椤圭洰瀹炴垬</option>
          <option value="purchase">绉垎璐拱</option>
          <option value="admin_grant">绠＄悊鍛樺厖鍊</option>
          <option value="ai_usage">AI 浣跨敤</option>
          <option value="refund">绉垎閫€杩</option>
        </select>
      </div>
      <div v-if="transactions.length === 0" class="empty-hint">鏆傛棤绉垎娴佹按璁板綍</div>
      <div v-else class="tx-list">
        <div v-for="tx in transactions" :key="tx.id" class="tx-item">
          <div class="tx-left">
            <div class="tx-icon" :class="tx.amount > 0 ? 'income' : 'expense'">
              {{ tx.amount > 0 ? '+' : '-' }}
            </div>
            <div class="tx-info">
              <div class="tx-title">{{ tx.source || tx.tx_type_name }}</div>
              <div class="tx-time">{{ formatTime(tx.created_at) }}</div>
            </div>
          </div>
          <div class="tx-right">
            <div class="tx-amount" :class="tx.amount > 0 ? 'income' : 'expense'">
              {{ tx.amount > 0 ? '+' : '' }}{{ tx.amount }}
            </div>
            <div class="tx-balance">浣欓 {{ tx.balance_after }}</div>
          </div>
        </div>
      </div>
      <div v-if="txTotal > 0" class="pagination">
        <button :disabled="txFilter.page <= 1" @click="txFilter.page--; fetchTransactions()">涓婁竴椤</button>
        <span>{{ txFilter.page }} / {{ Math.ceil(txTotal / txFilter.pageSize) }}</span>
        <button :disabled="txFilter.page >= Math.ceil(txTotal / txFilter.pageSize)" @click="txFilter.page++; fetchTransactions()">涓嬩竴椤</button>
      </div>
    </div>

    <!-- AI 浣跨敤缁熻 -->
    <div v-if="activeTab === 'usage'" class="tab-content">
      <div v-if="usageStats.length === 0" class="empty-hint">鏆傛棤 AI 浣跨敤璁板綍</div>
      <div v-else class="usage-list">
        <div v-for="stat in usageStats" :key="stat.feature" class="usage-item">
          <div class="usage-name">{{ stat.display_name }}</div>
          <div class="usage-bar">
            <div class="usage-fill" :style="{ width: usagePercent(stat.total_cost) + '%' }"></div>
          </div>
          <div class="usage-num">{{ stat.count }} 娆?/ {{ stat.total_cost }} 绉垎</div>
        </div>
      </div>
    </div>

    <!-- AI 鍔熻兘绉垎浠锋牸琛?-->
    <div v-if="activeTab === 'costs'" class="tab-content">
      <div class="cost-list">
        <div v-for="cost in aiCosts" :key="cost.feature" class="cost-item">
          <div class="cost-name">{{ cost.display_name }}</div>
          <div class="cost-desc">{{ cost.description || '-' }}</div>
          <div class="cost-points">{{ cost.points_cost == null ? '未配置' : (cost.points_cost <= 0 ? '免费' : cost.points_cost + ' 积分') }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import request from '@/utils/request'

const router = useRouter()

const balance = ref(0)
const totalUsed = ref(0)
const totalCalls = ref(0)

const activeTab = ref('transactions')
const tabs = [
  { key: 'transactions', label: '绉垎娴佹按' },
  { key: 'usage', label: 'AI 浣跨敤缁熻' },
  { key: 'costs', label: '积分价格表' },
]

// 鈹€鈹€ 绉垎浣欓 鈹€鈹€
const fetchBalance = async () => {
  try {
    const res = await request.get('/user/points')
    balance.value = res?.data?.points ?? res?.points ?? 0
  } catch (e) {
    console.warn('鑾峰彇绉垎浣欓澶辫触', e)
  }
}

// 鈹€鈹€ 绉垎娴佹按 鈹€鈹€
const transactions = ref([])
const txTotal = ref(0)
const txFilter = reactive({ page: 1, pageSize: 20, txType: '' })

const fetchTransactions = async () => {
  try {
    const params = { page: txFilter.page, page_size: txFilter.pageSize }
    if (txFilter.txType) params.tx_type = txFilter.txType
    const res = await request.get('/user/points/transactions', { params })
    const data = res?.data || res || {}
    transactions.value = data.items || []
    txTotal.value = data.total || 0
  } catch (e) {
    console.warn('鑾峰彇绉垎娴佹按澶辫触', e)
  }
}

// 鈹€鈹€ AI 浣跨敤缁熻 鈹€鈹€
const usageStats = ref([])

const fetchUsageStats = async () => {
  try {
    const res = await request.get('/user/points/usage-stats')
    const data = res?.data || res || {}
    usageStats.value = data.items || []
    totalUsed.value = data.total_points_used || 0
    totalCalls.value = usageStats.value.reduce((sum, s) => sum + s.count, 0)
  } catch (e) {
    console.warn('鑾峰彇浣跨敤缁熻澶辫触', e)
  }
}

const usagePercent = (cost) => {
  if (!totalUsed.value) return 0
  return Math.min((cost / totalUsed.value) * 100, 100)
}

// 鈹€鈹€ AI 绉垎浠锋牸琛?鈹€鈹€
const aiCosts = ref([])

const fetchCosts = async () => {
  try {
    const res = await request.get('/user/points/costs')
    aiCosts.value = res?.data || res || []
  } catch (e) {
    console.warn('获取积分价格表失败', e)
  }
}

// 鈹€鈹€ 宸ュ叿 鈹€鈹€
const formatTime = (t) => {
  if (!t) return ''
  return new Date(t).toLocaleString('zh-CN', {
    year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit',
  })
}

onMounted(() => {
  fetchBalance()
  fetchTransactions()
  fetchUsageStats()
  fetchCosts()
})
</script>

<style scoped>
.points-page {
  max-width: 800px;
  margin: 0 auto;
  padding: 24px 16px;
  color: var(--tm-text-primary, #e0e0e0);
}
.points-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
}
.points-header h1 {
  margin: 0;
  font-size: 24px;
  font-weight: 700;
}
.back-btn {
  background: none;
  border: 1px solid var(--tm-border-light, #333);
  color: var(--tm-text-secondary, #aaa);
  padding: 6px 14px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
}
.back-btn:hover {
  border-color: var(--tm-color-primary, #00D9C0);
  color: var(--tm-color-primary, #00D9C0);
}

/* 姒傝鍗＄墖 */
.overview-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 14px;
  margin-bottom: 24px;
}
.overview-card {
  background: var(--tm-card-bg, #12121f);
  border: 1px solid var(--tm-border-light, rgba(255,255,255,0.06));
  border-radius: 12px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
}
.overview-card.main-card {
  border-color: rgba(0,217,192,0.3);
  background: linear-gradient(135deg, rgba(0,217,192,0.08), transparent);
}
.card-icon { font-size: 32px; }
.card-value {
  font-size: 28px;
  font-weight: 800;
  color: var(--tm-text-primary, #fff);
}
.card-label {
  font-size: 12px;
  color: var(--tm-text-secondary, #888);
  margin-top: 2px;
}

/* Tab */
.tab-bar {
  display: flex;
  gap: 4px;
  margin-bottom: 16px;
  border-bottom: 1px solid var(--tm-border-light, #222);
  padding-bottom: 4px;
}
.tab-btn {
  background: none;
  border: none;
  color: var(--tm-text-secondary, #888);
  padding: 8px 16px;
  font-size: 14px;
  cursor: pointer;
  border-radius: 6px 6px 0 0;
  transition: all 0.2s;
}
.tab-btn.active {
  color: var(--tm-color-primary, #00D9C0);
  background: rgba(0,217,192,0.08);
  border-bottom: 2px solid var(--tm-color-primary, #00D9C0);
}
.tab-btn:hover:not(.active) {
  color: var(--tm-text-primary, #ddd);
}

.tab-content {
  min-height: 200px;
}
.empty-hint {
  text-align: center;
  color: var(--tm-text-secondary, #666);
  padding: 40px 0;
  font-size: 14px;
}

/* 绛涢€?*/
.filter-row {
  margin-bottom: 14px;
}
.filter-select {
  background: var(--tm-card-bg, #1a1a2e);
  border: 1px solid var(--tm-border-light, #333);
  color: var(--tm-text-primary, #e0e0e0);
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 13px;
}

/* 娴佹按鍒楄〃 */
.tx-list { display: flex; flex-direction: column; gap: 8px; }
.tx-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: var(--tm-card-bg, #12121f);
  border: 1px solid var(--tm-border-light, rgba(255,255,255,0.04));
  border-radius: 10px;
}
.tx-left { display: flex; align-items: center; gap: 12px; }
.tx-icon {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 700;
}
.tx-icon.income { background: rgba(103,194,58,0.12); color: #67c23a; }
.tx-icon.expense { background: rgba(245,108,108,0.12); color: #f56c6c; }
.tx-title { font-size: 14px; color: var(--tm-text-primary, #ddd); }
.tx-time { font-size: 11px; color: var(--tm-text-secondary, #666); margin-top: 2px; }
.tx-right { text-align: right; }
.tx-amount { font-size: 16px; font-weight: 700; }
.tx-amount.income { color: #67c23a; }
.tx-amount.expense { color: #f56c6c; }
.tx-balance { font-size: 11px; color: var(--tm-text-secondary, #666); margin-top: 2px; }

/* 鍒嗛〉 */
.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 16px;
  margin-top: 16px;
}
.pagination button {
  background: var(--tm-card-bg, #1a1a2e);
  border: 1px solid var(--tm-border-light, #333);
  color: var(--tm-text-primary, #ddd);
  padding: 6px 14px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
}
.pagination button:disabled { opacity: 0.4; cursor: not-allowed; }
.pagination span { font-size: 13px; color: var(--tm-text-secondary, #888); }

/* 浣跨敤缁熻 */
.usage-list { display: flex; flex-direction: column; gap: 12px; }
.usage-item {
  padding: 14px 16px;
  background: var(--tm-card-bg, #12121f);
  border: 1px solid var(--tm-border-light, rgba(255,255,255,0.04));
  border-radius: 10px;
}
.usage-name { font-size: 14px; font-weight: 600; margin-bottom: 8px; }
.usage-bar {
  height: 6px;
  background: rgba(255,255,255,0.06);
  border-radius: 3px;
  overflow: hidden;
  margin-bottom: 6px;
}
.usage-fill {
  height: 100%;
  background: linear-gradient(90deg, #00D9C0, #00b89c);
  border-radius: 3px;
  transition: width 0.3s ease;
}
.usage-num { font-size: 12px; color: var(--tm-text-secondary, #888); }

/* 绉垎浠锋牸琛?*/
.cost-list { display: flex; flex-direction: column; gap: 8px; }
.cost-item {
  display: flex;
  align-items: center;
  padding: 14px 16px;
  background: var(--tm-card-bg, #12121f);
  border: 1px solid var(--tm-border-light, rgba(255,255,255,0.04));
  border-radius: 10px;
  gap: 16px;
}
.cost-name { font-size: 14px; font-weight: 600; min-width: 140px; }
.cost-desc { flex: 1; font-size: 12px; color: var(--tm-text-secondary, #888); }
.cost-points {
  font-size: 15px;
  font-weight: 700;
  color: var(--tm-color-primary, #00D9C0);
  white-space: nowrap;
}

@media (max-width: 600px) {
  .overview-cards { grid-template-columns: 1fr; }
  .cost-item { flex-direction: column; align-items: flex-start; gap: 4px; }
}
</style>

