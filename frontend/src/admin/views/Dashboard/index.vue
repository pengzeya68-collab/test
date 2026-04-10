<template>
  <div class="dashboard-dark">
    <h1 class="page-title">数据统计</h1>

    <!-- 数据卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6" v-for="item in stats" :key="item.title">
        <div class="stat-card" :style="{ '--card-color': getColor(item.title) }">
          <div class="stat-info">
            <p class="stat-label">{{ item.title }}</p>
            <p class="stat-value">{{ item.value }}</p>
          </div>
          <div class="stat-icon">
            {{ getIcon(item.title) }}
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 数据表格区域 -->
    <el-row :gutter="20" class="tables-row">
      <el-col :span="12">
        <div class="data-card">
          <h3 class="card-title">最近注册用户</h3>
          <el-table :data="recentUsers" border stripe class="dark-table">
            <el-table-column prop="id" label="ID" width="80" />
            <el-table-column prop="username" label="用户名" />
            <el-table-column prop="email" label="邮箱" />
            <el-table-column prop="registerTime" label="注册时间" />
          </el-table>
        </div>
      </el-col>
      <el-col :span="12">
        <div class="data-card">
          <h3 class="card-title">最近添加习题</h3>
          <el-table :data="recentExercises" border stripe class="dark-table">
            <el-table-column prop="id" label="ID" width="80" />
            <el-table-column prop="title" label="习题标题" />
            <el-table-column prop="difficulty" label="难度" width="80" />
            <el-table-column prop="createTime" label="创建时间" />
          </el-table>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import request from '@/utils/request'
import { ElMessage } from 'element-plus'

const stats = ref([])
const recentUsers = ref([])
const recentExercises = ref([])

const getIcon = (title) => {
  const iconMap = {
    '总用户数': '👥',
    '习题总数': '📝',
    '学习路径': '📚',
    '社区帖子': '💬'
  }
  return iconMap[title] || '📊'
}

const getColor = (title) => {
  const colorMap = {
    '总用户数': '#409EFF',
    '习题总数': '#67C23A',
    '学习路径': '#E6A23C',
    '社区帖子': '#F56C6C'
  }
  return colorMap[title] || '#409EFF'
}

const fetchData = async () => {
  try {
    const res = await request.get('/admin/dashboard/stats')
    if (res && res.stats) {
      stats.value = res.stats
    }
    if (res && res.recentUsers) {
      recentUsers.value = res.recentUsers
    }
    if (res && res.recentExercises) {
      recentExercises.value = res.recentExercises
    }
    ElMessage.success('数据加载成功')
  } catch (e) {
    console.error('获取统计数据失败:', e)
    ElMessage.error('获取统计数据失败')
  }
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.dashboard-dark {
  width: 100%;
  padding: 0;
}

.page-title {
  margin: 0 0 24px 0;
  font-size: 28px;
  font-weight: 700;
  color: var(--tm-text-primary);
  letter-spacing: 0.5px;
}

.stats-row {
  margin-bottom: 24px;
}

.stat-card {
  background: var(--tm-card-bg);
  border-radius: 16px;
  padding: 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border: var(--tm-card-border);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3), var(--tm-glow-effect);
  transition: all 0.3s ease;
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.4), 0 0 15px rgba(0, 180, 216, 0.2);
  border-color: var(--card-color);
}

.stat-info {
  flex: 1;
}

.stat-label {
  margin: 0 0 8px 0;
  color: var(--tm-text-secondary);
  font-size: 14px;
  font-weight: 400;
}

.stat-value {
  margin: 0;
  font-size: 36px;
  font-weight: 700;
  color: var(--tm-text-primary);
  line-height: 1.2;
}

.stat-icon {
  width: 64px;
  height: 64px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32px;
  background: linear-gradient(135deg, var(--card-color), rgba(var(--card-color), 0.7));
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.tables-row {
  margin-bottom: 24px;
}

.data-card {
  background: var(--tm-card-bg);
  border-radius: 16px;
  padding: 24px;
  border: var(--tm-card-border);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
}

.card-title {
  margin: 0 0 16px 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--tm-text-primary);
}

/* Dark Table */
.dark-table :deep(.el-table) {
  background: transparent;
  color: var(--tm-text-primary);
}

.dark-table :deep(.el-table tr) {
  background: var(--tm-card-bg);
}

.dark-table :deep(.el-table th) {
  background: rgba(var(--tm-text-primary), 0.05);
  color: var(--tm-text-secondary);
}

.dark-table :deep(.el-table td) {
  border-bottom: 1px solid rgba(var(--tm-text-primary), 0.1);
  color: var(--tm-text-primary);
}

.dark-table :deep(.el-table__row:hover > td) {
  background-color: rgba(0, 180, 216, 0.08);
}
</style>
