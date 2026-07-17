<template>
  <div class="dashboard-page">
    <!-- 缁熻鍗＄墖 -->
    <el-row :gutter="16" class="stats-row">
      <el-col :xs="12" :sm="6" v-for="item in stats" :key="item.title">
        <div class="stat-card" :style="{ '--accent': getColor(item.title) }">
          <div class="stat-content">
            <p class="stat-label">{{ item.title }}</p>
            <p class="stat-value">{{ item.value }}</p>
          </div>
          <div class="stat-icon">{{ getIcon(item.title) }}</div>
        </div>
      </el-col>
    </el-row>

    <!-- 鍔犺浇楠ㄦ灦 -->
    <template v-if="loading">
      <el-row :gutter="16">
        <el-col :span="12"><el-skeleton :rows="5" animated /></el-col>
        <el-col :span="12"><el-skeleton :rows="5" animated /></el-col>
      </el-row>
    </template>

    <!-- 鏁版嵁琛ㄦ牸 -->
    <template v-else>
      <el-row :gutter="16" class="tables-row">
        <el-col :xs="24" :lg="12">
          <div class="admin-card">
            <h3 class="card-title">最近注册用户</h3>
            <el-table :data="recentUsers" stripe class="admin-table" empty-text="暂无数据">
              <el-table-column prop="id" label="ID" width="70" />
              <el-table-column prop="username" label="用户名" />
              <el-table-column prop="email" label="邮箱" show-overflow-tooltip />
              <el-table-column prop="registerTime" label="注册时间" width="160" />
            </el-table>
          </div>
        </el-col>
        <el-col :xs="24" :lg="12">
          <div class="admin-card">
            <h3 class="card-title">鏈€杩戞坊鍔犱範棰</h3>
            <el-table :data="recentExercises" stripe class="admin-table" empty-text="鏆傛棤鏁版嵁">
              <el-table-column prop="id" label="ID" width="70" />
              <el-table-column prop="title" label="涔犻鏍囬" show-overflow-tooltip />
              <el-table-column prop="difficulty" label="闅惧害" width="80">
                <template #default="{ row }">
                  <el-tag :type="diffType(row.difficulty)" size="small">{{ diffText(row.difficulty) }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="createTime" label="鍒涘缓鏃堕棿" width="160" />
            </el-table>
          </div>
        </el-col>
      </el-row>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import request from '@/utils/request'

const stats = ref([])
const recentUsers = ref([])
const recentExercises = ref([])
const loading = ref(true)

const getIcon = (title) => {
  const map = { '总用户数': 'U', '习题总数': 'Q', '学习路径': 'L', '社区帖子': 'P' }
  return map[title] || 'D'
}
const getColor = (title) => {
  const map = { '总用户数': '#409EFF', '习题总数': '#67C23A', '学习路径': '#E6A23C', '社区帖子': '#F56C6C' }
  return map[title] || '#409EFF'
}
const diffType = d => ({ easy: 'success', medium: 'warning', hard: 'danger' }[d] || 'info')
const diffText = d => ({ easy: '简单', medium: '中等', hard: '困难' }[d] || d)

const fetchData = async () => {
  loading.value = true
  try {
    const res = await request.get('/admin/dashboard/stats')
    if (res?.stats) stats.value = res.stats
    if (res?.recentUsers) recentUsers.value = res.recentUsers
    if (res?.recentExercises) recentExercises.value = res.recentExercises
  } catch (e) {
    console.error('鑾峰彇缁熻鏁版嵁澶辫触:', e)
    ElMessage.error('鑾峰彇缁熻鏁版嵁澶辫触')
  } finally {
    loading.value = false
  }
}

onMounted(fetchData)
</script>

<style scoped>
@import '../../admin-common.css';

.dashboard-page {
  width: 100%;
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  background: var(--tm-card-bg);
  border-radius: 12px;
  padding: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border: var(--tm-card-border);
  transition: all 0.2s ease;
  margin-bottom: 16px;
}
.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
  border-color: var(--accent);
}
.stat-content { flex: 1; }
.stat-label {
  margin: 0 0 6px;
  color: var(--tm-text-secondary);
  font-size: 13px;
}
.stat-value {
  margin: 0;
  font-size: 28px;
  font-weight: 700;
  color: var(--tm-text-primary);
}
.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  background: rgba(var(--tm-color-primary-rgb), 0.08);
}

.tables-row {
  margin-bottom: 20px;
}
.card-title {
  margin: 0 0 16px;
  font-size: 16px;
  font-weight: 600;
  color: var(--tm-text-primary);
}

@media (max-width: 768px) {
  .stat-value { font-size: 22px; }
  .stat-icon { width: 40px; height: 40px; font-size: 20px; }
}
</style>

