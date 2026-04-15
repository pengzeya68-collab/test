<template>
  <div class="dashboard">
    <div class="stats-grid">
      <div v-for="stat in statsData" :key="stat.title" class="stat-card">
        <div class="stat-icon" :class="getStatIconClass(stat.title)">
          <el-icon v-if="stat.title === '总用户数'" size="28"><User /></el-icon>
          <el-icon v-else-if="stat.title === '习题总数'" size="28"><Document /></el-icon>
          <el-icon v-else-if="stat.title === '学习路径'" size="28"><Guide /></el-icon>
          <el-icon v-else-if="stat.title === '社区帖子'" size="28"><DataAnalysis /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ stat.value }}</div>
          <div class="stat-label">{{ stat.title }}</div>
        </div>
      </div>
    </div>

    <div class="chart-grid">
      <div class="chart-card">
        <h3 class="chart-title">学习趋势</h3>
        <el-empty description="图表功能开发中" :image-size="100" />
      </div>
      <div class="chart-card">
        <h3 class="chart-title">热门知识点</h3>
        <el-empty description="图表功能开发中" :image-size="100" />
      </div>
    </div>

    <div class="recent-section">
      <div class="recent-card">
        <h3 class="card-title">最新注册用户</h3>
        <el-table :data="recentUsers" border style="width: 100%">
          <el-table-column prop="id" label="ID" width="80" />
          <el-table-column prop="username" label="用户名" />
          <el-table-column prop="registerTime" label="注册时间" />
          <el-table-column label="状态" width="80">
            <template #default>
              <el-tag type="success" size="small">正常</el-tag>
            </template>
          </el-table-column>
        </el-table>
      </div>
      <div class="recent-card">
        <h3 class="card-title">最新添加习题</h3>
        <el-table :data="recentExercises" border style="width: 100%">
          <el-table-column prop="id" label="ID" width="60" />
          <el-table-column prop="title" label="习题名称" />
          <el-table-column prop="difficulty" label="难度" width="60" />
          <el-table-column prop="createTime" label="添加时间" />
        </el-table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { User, Document, Guide, DataAnalysis } from '@element-plus/icons-vue'
import request from '@/utils/request'

const statsData = ref([])
const recentUsers = ref([])
const recentExercises = ref([])

const getStatIconClass = (title) => {
  const classMap = {
    '总用户数': 'blue',
    '习题总数': 'green',
    '学习路径': 'orange',
    '社区帖子': 'purple'
  }
  return classMap[title] || 'blue'
}

const loadDashboardStats = async () => {
  try {
    const res = await request.get('/admin/dashboard/stats')
    statsData.value = res.stats || []
    recentUsers.value = res.recentUsers || []
    recentExercises.value = res.recentExercises || []
  } catch (error) {
    console.error('加载仪表盘数据失败:', error)
  }
}

onMounted(() => {
  loadDashboardStats()
})
</script>

<style scoped>
.dashboard {
  width: 100%;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.stat-card {
  background: #18181B;
  border-radius: 12px;
  padding: 24px;
  display: flex;
  align-items: center;
  gap: 20px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.stat-icon.blue {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.stat-icon.green {
  background: linear-gradient(135deg, #84fab0 0%, #8fd3f4 100%);
}

.stat-icon.orange {
  background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
}

.stat-icon.purple {
  background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: var(--tm-text-primary);
  margin-bottom: 4px;
}

.stat-label {
  font-size: 14px;
  color: var(--tm-text-secondary);
  margin-bottom: 4px;
}

.stat-change {
  font-size: 12px;
}

.stat-change.increase {
  color: #67c23a;
}

.stat-change.decrease {
  color: #f56c6c;
}

.chart-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-bottom: 30px;
}

.chart-card {
  background: #18181B;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  min-height: 300px;
}

.chart-title {
  margin: 0 0 20px 0;
  font-size: 18px;
  font-weight: bold;
  color: var(--tm-text-primary);
}

.recent-section {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.recent-card {
  background: #18181B;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.card-title {
  margin: 0 0 20px 0;
  font-size: 18px;
  font-weight: bold;
  color: var(--tm-text-primary);
}

@media (max-width: 1200px) {
  .chart-grid,
  .recent-section {
    grid-template-columns: 1fr;
  }
}
</style>
