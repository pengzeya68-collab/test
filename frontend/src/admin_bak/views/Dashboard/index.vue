<template>
  <div class="dashboard-page">
    <el-page-header content="数据统计" />
    
    <!-- 数据卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :xs="12" :sm="6" v-for="item in statsCards" :key="item.title">
        <el-card class="stats-card" shadow="hover">
          <div class="stats-content">
            <div class="stats-info">
              <p class="stats-value">{{ item.value }}</p>
              <p class="stats-title">{{ item.title }}</p>
              <p class="stats-desc" :class="item.trend === 'up' ? 'text-success' : 'text-danger'">
                <el-icon>
                  <ArrowUp v-if="item.trend === 'up'" />
                  <ArrowDown v-else />
                </el-icon>
                {{ item.change }} 较昨日
              </p>
            </div>
            <div class="stats-icon" :style="{ backgroundColor: item.color }">
              <el-icon size="28" color="#fff">
                <component :is="item.icon" />
              </el-icon>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 图表区域 -->
    <el-row :gutter="20">
      <el-col :xs="24" :sm="16">
        <el-card title="学习数据趋势" shadow="hover" class="chart-card">
          <div class="chart-container" ref="lineChartRef"></div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="8">
        <el-card title="用户分布" shadow="hover" class="chart-card">
          <div class="chart-container" ref="pieChartRef"></div>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 最近活动 -->
    <el-row :gutter="20" class="activity-row">
      <el-col :xs="24" :sm="12">
        <el-card title="最近注册用户" shadow="hover">
          <el-table :data="recentUsers" border stripe>
            <el-table-column prop="username" label="用户名" />
            <el-table-column prop="email" label="邮箱" />
            <el-table-column prop="registerTime" label="注册时间" />
          </el-table>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12">
        <el-card title="最新习题" shadow="hover">
          <el-table :data="recentExercises" border stripe>
            <el-table-column prop="title" label="习题标题" />
            <el-table-column prop="difficulty" label="难度">
              <template #default="scope">
                <el-tag :type="getDifficultyTag(scope.row.difficulty)">{{ scope.row.difficulty }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="createTime" label="创建时间" />
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import * as echarts from 'echarts'
import {
  User,
  Document,
  Guide,
  Clock,
  ArrowUp,
  ArrowDown
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { getDashboardStats } from '@/admin/api'

// 统计卡片数据
const statsCards = ref([
  {
    title: '总用户数',
    value: '1,234',
    change: '12.5%',
    trend: 'up',
    color: '#409EFF',
    icon: User
  },
  {
    title: '习题总数',
    value: '3,567',
    change: '8.2%',
    trend: 'up',
    color: '#67C23A',
    icon: Document
  },
  {
    title: '学习路径',
    value: '45',
    change: '3.1%',
    trend: 'up',
    color: '#E6A23C',
    icon: Guide
  },
  {
    title: '今日学习时长',
    value: '128h',
    change: '5.7%',
    trend: 'down',
    color: '#F56C6C',
    icon: Clock
  }
])

// 最近用户数据
const recentUsers = ref([
  { username: 'user001', email: 'user001@example.com', registerTime: '2026-03-14 15:30' },
  { username: 'user002', email: 'user002@example.com', registerTime: '2026-03-14 14:20' },
  { username: 'user003', email: 'user003@example.com', registerTime: '2026-03-14 13:15' },
  { username: 'user004', email: 'user004@example.com', registerTime: '2026-03-14 11:45' },
  { username: 'user005', email: 'user005@example.com', registerTime: '2026-03-14 10:30' }
])

// 最近习题数据
const recentExercises = ref([
  { title: 'JavaScript基础语法', difficulty: '简单', createTime: '2026-03-14 16:00' },
  { title: 'Vue3组合式API', difficulty: '中等', createTime: '2026-03-14 15:00' },
  { title: '算法复杂度分析', difficulty: '困难', createTime: '2026-03-14 14:00' },
  { title: 'CSS布局技巧', difficulty: '简单', createTime: '2026-03-14 13:00' },
  { title: 'React状态管理', difficulty: '中等', createTime: '2026-03-14 12:00' }
])

const lineChartRef = ref()
const pieChartRef = ref()

const getDifficultyTag = (difficulty) => {
  const map = {
    '简单': 'success',
    '中等': 'warning',
    '困难': 'danger'
  }
  return map[difficulty] || 'info'
}

const initLineChart = () => {
  if (!lineChartRef.value) return
  
  const chart = echarts.init(lineChartRef.value)
  const option = {
    tooltip: {
      trigger: 'axis'
    },
    legend: {
      data: ['学习人数', '完成习题']
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
    },
    yAxis: {
      type: 'value'
    },
    series: [
      {
        name: '学习人数',
        type: 'line',
        data: [120, 132, 101, 134, 90, 230, 210],
        smooth: true
      },
      {
        name: '完成习题',
        type: 'line',
        data: [220, 182, 191, 234, 290, 330, 310],
        smooth: true
      }
    ]
  }
  
  chart.setOption(option)
  
  window.addEventListener('resize', () => chart.resize())
}

const initPieChart = () => {
  if (!pieChartRef.value) return
  
  const chart = echarts.init(pieChartRef.value)
  const option = {
    tooltip: {
      trigger: 'item'
    },
    legend: {
      orient: 'vertical',
      left: 'left'
    },
    series: [
      {
        name: '用户等级',
        type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 10,
          borderColor: '#fff',
          borderWidth: 2
        },
        label: {
          show: false,
          position: 'center'
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 16,
            fontWeight: 'bold'
          }
        },
        labelLine: {
          show: false
        },
        data: [
          { value: 1048, name: '初级' },
          { value: 735, name: '中级' },
          { value: 580, name: '高级' },
          { value: 484, name: '专家' }
        ]
      }
    ]
  }
  
  chart.setOption(option)
  
  window.addEventListener('resize', () => chart.resize())
}

const fetchDashboardData = async () => {
  try {
    // 调用真实的仪表盘API接口
    const res = await getDashboardStats()
    // statsCards.value = res.data.stats
    // recentUsers.value = res.data.recentUsers
    // recentExercises.value = res.data.recentExercises
    
    ElMessage.success('数据加载完成')
  } catch (error) {
    ElMessage.error('数据加载失败，请稍后重试')
  }
}

onMounted(() => {
  initLineChart()
  initPieChart()
  fetchDashboardData()
})
</script>

<style scoped lang="scss">
.dashboard-page {
  .stats-row {
    margin: 20px 0;
  }
  
  .stats-card {
    .stats-content {
      display: flex;
      justify-content: space-between;
      align-items: center;
      
      .stats-info {
        .stats-value {
          font-size: 32px;
          font-weight: 700;
          color: #303133;
          margin: 0 0 8px;
        }
        
        .stats-title {
          font-size: 14px;
          color: #909399;
          margin: 0 0 8px;
        }
        
        .stats-desc {
          font-size: 12px;
          margin: 0;
          display: flex;
          align-items: center;
          gap: 4px;
          
          &.text-success {
            color: #67C23A;
          }
          
          &.text-danger {
            color: #F56C6C;
          }
        }
      }
      
      .stats-icon {
        width: 60px;
        height: 60px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
      }
    }
  }
  
  .chart-card {
    margin-bottom: 20px;
    
    .chart-container {
      height: 300px;
      width: 100%;
    }
  }
  
  .activity-row {
    margin-top: 20px;
  }
}
</style>
