<template>
  <div class="backup-manager">
    <div class="layout-fluid">
      <div class="page-header">
        <div>
          <h2 class="page-title">🛡️ 数据安全指挥中心</h2>
          <p class="page-subtitle">数据库备份与恢复、系统安全审计一站式管理</p>
        </div>
      </div>

      <el-tabs v-model="activeTab" class="db-tabs">
        <el-tab-pane label="监控大屏" name="dashboard">
          <el-row :gutter="20">
            <el-col :span="6">
              <el-card shadow="hover">
                <div class="stat-card">
                  <div class="stat-label">主库状态</div>
                  <el-tag :type="systemMetrics?.database?.healthy ? 'success' : 'danger'" size="large">
                    {{ systemMetrics?.database?.healthy ? '健康' : '异常' }}
                  </el-tag>
                </div>
              </el-card>
            </el-col>
            <el-col :span="6">
              <el-card shadow="hover">
                <div class="stat-card">
                  <div class="stat-label">Redis 缓存</div>
                  <el-tag v-if="systemMetrics?.redis?.enabled" :type="systemMetrics?.redis?.healthy ? 'success' : 'danger'" size="large">
                    {{ systemMetrics?.redis?.healthy ? '运行中' : '异常' }}
                  </el-tag>
                  <el-tag v-else type="info" size="large">未配置</el-tag>
                </div>
              </el-card>
            </el-col>
            <el-col :span="6">
              <el-card shadow="hover">
                <div class="stat-card">
                  <div class="stat-label">总备份数</div>
                  <div class="stat-value">{{ systemMetrics?.backups?.count || 0 }}</div>
                </div>
              </el-card>
            </el-col>
            <el-col :span="6">
              <el-card shadow="hover">
                <div class="stat-card">
                  <div class="stat-label">存储占用</div>
                  <div class="stat-value">{{ totalSize }}</div>
                </div>
              </el-card>
            </el-col>
          </el-row>
          <el-row :gutter="20" style="margin-top: 20px;">
            <el-col :span="12">
              <el-card header="表空间占比">
                <div id="table-space-chart" class="chart-container" style="height: 350px;"></div>
              </el-card>
            </el-col>
            <el-col :span="12">
              <el-card header="近7日系统负载">
                <div id="system-load-chart" class="chart-container" style="height: 350px;"></div>
              </el-card>
            </el-col>
          </el-row>
        </el-tab-pane>

        <el-tab-pane label="主库备份管理" name="backup">
          <div class="backup-actions">
            <el-button type="primary" @click="createBackup" :loading="creating">
              <el-icon><Plus /></el-icon>
              立即备份
            </el-button>
            <el-button type="danger" size="small" @click="cleanOldBackups" :loading="cleaning">
              清理旧备份
            </el-button>
          </div>

          <el-table :data="backups" v-loading="loading" style="width: 100%">
            <el-table-column type="index" label="序号" width="80" />
            <el-table-column prop="name" label="文件名" min-width="200">
              <template #default="{ row }">
                <el-icon><Document /></el-icon>
                <span class="filename">{{ row.name }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="size" label="大小" width="120">
              <template #default="{ row }">
                {{ row.size.toFixed(2) }} MB
              </template>
            </el-table-column>
            <el-table-column prop="time" label="备份时间" width="180">
              <template #default="{ row }">
                {{ formatTime(row.time) }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="260" fixed="right">
              <template #default="{ row, $index }">
                <el-button
                  type="primary"
                  link
                  size="small"
                  @click="downloadBackup(row)"
                >
                  下载
                </el-button>
                <el-popconfirm 
                  title="确定要恢复此备份吗？当前运行数据将被彻底覆盖！" 
                  confirm-button-text="确认恢复" 
                  cancel-button-text="取消" 
                  confirm-button-type="danger"
                  @confirm="handleRestore(row)"
                >
                  <template #reference>
                    <el-button type="danger" link :loading="restoring === $index">恢复</el-button>
                  </template>
                </el-popconfirm>
                <el-button
                  type="danger"
                  size="small"
                  @click="deleteBackup(row, $index)"
                  :loading="deleting === $index"
                >
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>

          <el-empty v-if="backups.length === 0 && !loading" description="暂无备份文件" />

          <el-card class="usage-guide" style="margin-top: 20px;">
            <template #header>
              <span>使用说明</span>
            </template>
            <div class="guide-content">
              <h4>🔄 自动备份</h4>
              <p>系统每次启动时会自动创建数据库备份，保留最近10个备份文件。</p>

              <h4>💾 手动备份</h4>
              <p>点击"立即备份"按钮可随时创建备份，建议在重要操作前手动备份。</p>

              <h4>↩️ 恢复备份</h4>
              <p>如需恢复数据，点击对应备份的"恢复"按钮。恢复前会自动创建紧急备份。</p>

              <h4>⚠️ 注意事项</h4>
              <ul>
                <li>恢复备份会覆盖当前所有数据，请谨慎操作</li>
                <li>建议定期下载备份文件到本地或云端保存</li>
                <li>备份文件存储在项目根目录的 backups 文件夹中</li>
              </ul>
            </div>
          </el-card>
        </el-tab-pane>

        <el-tab-pane label="高危操作审计" name="audit">
          <el-table :data="auditLogs" empty-text="暂无高危操作记录" style="width: 100%">
            <el-table-column label="操作时间" prop="time" width="180" />
            <el-table-column label="操作人" prop="user" width="120" />
            <el-table-column prop="action" label="操作内容" show-overflow-tooltip>
              <template #default="scope">
                <el-tag :type="scope.row.action.includes('删除') || scope.row.action.includes('清理') ? 'warning' : 'info'">
                  {{ scope.row.action }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="120">
              <template #default="scope">
                <el-tag :type="scope.row.status === 'success' ? 'success' : 'danger'" effect="dark">
                  {{ scope.row.status === 'success' ? '成功' : '失败' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="IP 地址" prop="ip" width="150" />
          </el-table>
          <el-pagination
            v-model:current-page="auditPage"
            v-model:page-size="auditSize"
            :page-sizes="[10, 20, 50]"
            :total="auditTotal"
            layout="total, sizes, prev, pager, next, jumper"
            style="margin-top: 16px; justify-content: flex-end;"
            @current-change="handleAuditPageChange"
            @size-change="handleAuditPageChange"
          />
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, shallowRef, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Document } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import axios from 'axios'

// 单独创建 request 实例
const request = axios.create({
  baseURL: '/api',
  timeout: 15000
})

// 添加请求拦截器，自动带上 token
request.interceptors.request.use(
  config => {
    const token = localStorage.getItem('admin_token') || localStorage.getItem('token');
    if (token && token !== 'undefined' && token !== 'null' && token !== '[object Object]') {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  error => {
    return Promise.reject(error);
  }
)

const activeTab = ref('backup')
const backups = ref([])
const auditLogs = ref([])
const auditPage = ref(1)
const auditSize = ref(10)
const auditTotal = ref(0)
const loading = ref(false)
const loadingMetrics = ref(false)
const creating = ref(false)
const cleaning = ref(false)
const restoring = ref(-1)
const deleting = ref(-1)

// 系统指标 - 初始默认值防止 undefined 报错
const systemMetrics = ref({
  database: { healthy: false, status: 'unhealthy' },
  redis: { enabled: false, healthy: false, status: 'unhealthy' },
  backups: { count: 0, total_size_mb: 0 }
})

// ECharts 实例 - 使用 shallowRef 避免响应式代理死循环
const tableSpaceChart = shallowRef(null)
const systemLoadChart = shallowRef(null)

// 心跳刷新定时器
let refreshTimer = null

// 计算真实的总备份大小 - 防弹版本
const totalSize = computed(() => {
  const size = systemMetrics.value?.backups?.total_size_mb || 0
  return `${size.toFixed(2)} MB`
})

// 刷新图表大小当切换标签
watch(activeTab, (newTab) => {
  if (newTab === 'dashboard') {
    setTimeout(() => {
      if (tableSpaceChart.value) tableSpaceChart.value.resize()
      if (systemLoadChart.value) systemLoadChart.value.resize()
    }, 300)
  }
})

// 计算属性
const latestBackupTime = computed(() => {
  if (backups.value.length === 0) return '无'
  const latest = backups.value[0]
  const date = new Date(latest.time)
  const now = new Date()
  const diff = Math.floor((now - date) / 1000 / 60) // 分钟
  
  if (diff < 1) return '刚刚'
  if (diff < 60) return `${diff}分钟前`
  if (diff < 1440) return `${Math.floor(diff / 60)}小时前`
  return `${Math.floor(diff / 1440)}天前`
})

// 获取备份列表 - 防弹版本
const fetchBackups = async () => {
  loading.value = true
  try {
    const res = await request.get('/admin/backups')
    // 兼容：拦截器可能已经返回 res.data
    const data = res.data || res || {}
    backups.value = data.backups || []
  } catch (error) {
    console.error('获取备份列表失败:', error)
    ElMessage.error('获取备份列表失败')
  } finally {
    loading.value = false
  }
}

// 获取审计日志 - 支持分页
const fetchAuditLogs = async (page = 1) => {
  try {
    auditPage.value = page
    const res = await request.get(`/admin/audit-logs?page=${page}&size=${auditSize.value}`)
    const data = res.data || res || {}
    auditLogs.value = data.logs || []
    auditTotal.value = data.total || 0
  } catch (error) {
    console.error('获取审计日志失败:', error)
  }
}

// 创建备份 - 带确认框
const createBackup = async () => {
  try {
    await ElMessageBox.confirm(
      '正在进行全量数据物理备份，该操作可能导致数据库短暂拥塞，是否坚决执行？',
      '备份确认',
      {
        confirmButtonText: '立即执行备份',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    creating.value = true
    await request.post('/admin/backups')
    ElMessage.success('备份创建成功')
    // 全链路刷新：先获取最新备份列表，再刷新大屏统计
    fetchBackups()
    fetchSystemMetrics()
    fetchAuditLogs()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('创建备份失败:', error)
      ElMessage.error('创建备份失败')
    }
  } finally {
    creating.value = false
  }
}

// 清理旧备份
const cleanOldBackups = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要清理旧备份吗？只保留最新的10个备份文件。',
      '清理确认',
      {
        confirmButtonText: '确定清理',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    cleaning.value = true
    await request.delete('/admin/backups/old')
    ElMessage.success('旧备份清理成功')
    // 全链路刷新：先获取最新备份列表，再刷新大屏统计
    fetchBackups()
    fetchSystemMetrics()
    fetchAuditLogs()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('清理备份失败:', error)
      ElMessage.error('清理备份失败')
    }
  } finally {
    cleaning.value = false
  }
}

// 下载备份文件
const downloadBackup = (backup) => {
  // 构建下载 URL
  const token = localStorage.getItem('admin_token') || localStorage.getItem('token')
  const downloadUrl = `/api/admin/backups/download/${encodeURIComponent(backup.name)}`
  
  // 使用动态创建 a 标签的方式下载
  const link = document.createElement('a')
  link.href = downloadUrl
  link.download = backup.name
  // 添加 Authorization header
  link.target = '_blank'
  
  // 通过 fetch 获取文件 blob 然后触发下载（解决跨域和认证问题）
  fetch(downloadUrl, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  })
    .then(response => {
      if (!response.ok) {
        throw new Error('下载失败')
      }
      return response.blob()
    })
    .then(blob => {
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = backup.name
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
      ElMessage.success('下载成功')
    })
    .catch(error => {
      console.error('下载失败:', error)
      ElMessage.error('下载失败，请重试')
    })
}

// 恢复备份 - Popconfirm 触发（不再需要 MessageBox）
const handleRestore = async (backup) => {
  try {
    restoring.value = 0  // 标记正在恢复
    await request.post(`/admin/backups/${encodeURIComponent(backup.name)}/restore`)
    ElMessage.success('备份恢复成功，请刷新页面')
    fetchBackups()
    fetchSystemMetrics()
    fetchAuditLogs()
  } catch (error) {
    console.error('恢复备份失败:', error)
    ElMessage.error('恢复备份失败')
  } finally {
    restoring.value = -1
  }
}

// 保留原函数兼容（内部调用 handleRestore）
const restoreBackup = async (backup, index) => {
  restoring.value = index
  await handleRestore(backup)
  restoring.value = -1
}

// 删除备份
const deleteBackup = async (backup, index) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除备份 "${backup.name}" 吗？`,
      '删除确认',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    deleting.value = index
    await request.delete(`/admin/backups/${encodeURIComponent(backup.name)}`)
    ElMessage.success('备份删除成功')
    // 全链路刷新：先获取最新备份列表，再刷新大屏统计
    fetchBackups()
    fetchSystemMetrics()
    fetchAuditLogs()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除备份失败:', error)
      ElMessage.error('删除备份失败')
    }
  } finally {
    deleting.value = -1
  }
}

// 获取操作类型的标签颜色
const getActionTagType = (action) => {
  if (!action) return 'info'
  const actionStr = action.toLowerCase()
  // 删除/清理类操作 → 黄色警告
  if (actionStr.includes('删除') || actionStr.includes('清理')) {
    return 'warning'
  }
  // 创建/备份类操作 → 绿色成功
  if (actionStr.includes('创建') || actionStr.includes('备份')) {
    return 'success'
  }
  // 恢复操作 → 蓝色信息
  if (actionStr.includes('恢复')) {
    return ''
  }
  // 其他默认
  return 'info'
}

// 审计日志分页切换
const handleAuditPageChange = (page) => {
  fetchAuditLogs(page)
}

// 格式化时间 - 严格 YYYY-MM-DD HH:mm:ss（禁止斜杠）
const formatTime = (timeStr) => {
  if (!timeStr) return '-'
  const date = new Date(timeStr)
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  const h = String(date.getHours()).padStart(2, '0')
  const mi = String(date.getMinutes()).padStart(2, '0')
  const s = String(date.getSeconds()).padStart(2, '0')
  return `${y}-${m}-${d} ${h}:${mi}:${s}`
}

// 初始化图表 - 增强版：尺寸校验 + 防重复 + nextTick 等待
const initCharts = async (chartData) => {
  // 【核心补丁】必须等待 DOM 彻底渲染并完成布局计算
  await nextTick()

  // --- 1. 表空间饼图 ---
  const tableSpaceDom = document.getElementById('table-space-chart')
  // 增加判定：如果 DOM 不存在，或者高度为 0，坚决不初始化
  if (tableSpaceDom && tableSpaceDom.clientWidth > 0 && tableSpaceDom.clientHeight > 0) {
    let myChart = echarts.getInstanceByDom(tableSpaceDom)
    if (myChart) {
      myChart.dispose() // 彻底销毁旧实例
    }
    myChart = echarts.init(tableSpaceDom)
    tableSpaceChart.value = myChart // 存入 shallowRef

    const option = {
      tooltip: { trigger: 'item', formatter: '{b}: {c} MB ({d}%)' },
      legend: { orient: 'vertical', left: 'left' },
      series: [{
        name: '表空间',
        type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: false,
        itemStyle: { borderRadius: 10, borderColor: '#fff', borderWidth: 2 },
        label: { show: true, formatter: '{b}: {d}%' },
        emphasis: {
          label: {
            show: true,
            fontSize: 16,
            fontWeight: 'bold'
          }
        },
        data: chartData.table_space || []
      }]
    }
    myChart.setOption(option)
  }

  // --- 2. 系统负载折线图 ---
  const systemLoadDom = document.getElementById('system-load-chart')
  // 同样增加尺寸校验，防止 0px 报错
  if (systemLoadDom && systemLoadDom.clientWidth > 0 && systemLoadDom.clientHeight > 0) {
    let myChart = echarts.getInstanceByDom(systemLoadDom)
    if (myChart) {
      myChart.dispose()
    }
    myChart = echarts.init(systemLoadDom)
    systemLoadChart.value = myChart

    // 数据处理
    const dates = []
    const cpuData = []
    const memoryData = []
    const rawData = chartData.system_load_7d || []

    rawData.forEach((item, i) => {
      const d = new Date()
      d.setDate(d.getDate() - (rawData.length - 1 - i))
      dates.push(`${d.getMonth() + 1}/${d.getDate()}`)
      cpuData.push(item.cpu)
      memoryData.push(item.memory)
    })

    myChart.setOption({
      tooltip: { trigger: 'axis' },
      legend: { data: ['CPU 使用率', '内存使用率'] },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        containLabel: true
      },
      xAxis: { type: 'category', boundaryGap: false, data: dates },
      yAxis: { type: 'value', max: 100, name: '%' },
      series: [
        { name: 'CPU 使用率', type: 'line', data: cpuData, smooth: true, areaStyle: { opacity: 0.3 }, itemStyle: { color: '#409eff' } },
        { name: '内存使用率', type: 'line', data: memoryData, smooth: true, areaStyle: { opacity: 0.3 }, itemStyle: { color: '#67c23a' } }
      ]
    })
  }
}

// 处理窗口大小变化
const handleResize = () => {
  if (tableSpaceChart.value) tableSpaceChart.value.resize()
  if (systemLoadChart.value) systemLoadChart.value.resize()
}

window.addEventListener('resize', handleResize)

// 获取系统监控指标 - 防弹版本兼容拦截器解包
// silent: 是否静默刷新（心跳模式，不显示 loading，不闪烁）
const fetchSystemMetrics = async (silent = false) => {
  if (!silent) {
    loadingMetrics.value = true
  }
  try {
    const res = await request.get('/admin/system/metrics')
    // 兼容：拦截器可能已经返回 res.data，也可能还是完整 response
    const data = res.data || res || {}
    // 所有字段可选链式防护
    systemMetrics.value = {
      database: data.database || { healthy: false, status: 'unhealthy' },
      redis: data.redis || { enabled: false, healthy: false, status: 'unhealthy' },
      backups: data.backups || { count: 0, total_size_mb: 0 }
    }
    
    const chartsData = data.charts
    if (chartsData && chartsData.table_space && chartsData.system_load_7d) {
      if (silent) {
        // 心跳静默刷新：只更新数据，不闪烁
        updateChartsData(chartsData)
      } else {
        // 首次加载或手动刷新：等待 DOM 更新完成再初始化图表
        await nextTick()
        await initCharts(chartsData)
      }
    }
  } catch (error) {
    if (!silent) {
      console.error('获取系统指标失败:', error)
      ElMessage.error('获取系统指标失败')
    }
  } finally {
    if (!silent) {
      loadingMetrics.value = false
    }
  }
}

// 仅更新图表数据（心跳刷新用，不闪烁）
const updateChartsData = (chartData) => {
  // 更新表空间饼图
  if (tableSpaceChart.value && chartData.table_space) {
    tableSpaceChart.value.setOption({
      series: [{ data: chartData.table_space }]
    }, false) // false = 不合并，直接替换数据
  }
  
  // 更新系统负载折线图
  if (systemLoadChart.value && chartData.system_load_7d) {
    const dates = []
    const cpuData = []
    const memoryData = []
    const rawData = chartData.system_load_7d || []
    
    rawData.forEach((item, i) => {
      const d = new Date()
      d.setDate(d.getDate() - (rawData.length - 1 - i))
      dates.push(`${d.getMonth() + 1}/${d.getDate()}`)
      cpuData.push(item.cpu)
      memoryData.push(item.memory)
    })
    
    systemLoadChart.value.setOption({
      xAxis: { data: dates },
      series: [
        { data: cpuData },
        { data: memoryData }
      ]
    }, false)
  }
}

onMounted(() => {
  fetchSystemMetrics()
  fetchBackups()
  fetchAuditLogs()
  
  // 开启 15 秒心跳静默刷新
  refreshTimer = setInterval(() => {
    fetchSystemMetrics()
  }, 15000)
})

onUnmounted(() => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
  }
})
</script>

<style scoped>
.backup-manager {
  padding: 30px 0;
  min-height: calc(100vh - 60px);
  background-color: #f5f7fa;
}

.layout-fluid {
  width: 100%;
  max-width: 100%;
  padding: 20px 32px;
  margin: 0 auto;
  box-sizing: border-box;
}

.page-header {
  margin-bottom: 24px;
}

.page-title {
  font-size: 28px;
  font-weight: bold;
  color: #303133;
  margin: 0 0 8px 0;
}

.page-subtitle {
  font-size: 14px;
  color: #909399;
  margin: 0;
}

.db-tabs {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  padding: 0 20px;
}

.db-tabs :deep(.el-tabs__content) {
  padding-top: 20px;
}

.stat-card {
  padding: 20px;
}

.stat-card .stat-label {
  font-size: 14px;
  color: #909399;
  margin-bottom: 12px;
}

.stat-card .stat-value {
  font-size: 32px;
  font-weight: bold;
  color: #409eff;
}

.chart-container {
  height: 350px;
  width: 100%;
}

.chart-placeholder {
  padding: 60px 20px;
  text-align: center;
  color: #909399;
  font-size: 14px;
}

.backup-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-bottom: 16px;
}

.filename {
  margin-left: 8px;
  font-family: monospace;
}

.usage-guide {
  line-height: 1.8;
}

.guide-content {
  line-height: 1.8;
  color: #606266;
}

.guide-content h4 {
  margin: 20px 0 10px 0;
  color: #303133;
}

.guide-content p {
  margin: 0 0 10px 0;
}

.guide-content ul {
  margin: 10px 0;
  padding-left: 20px;
}

.guide-content li {
  margin: 5px 0;
}

@media (max-width: 768px) {
  .layout-fluid {
    padding: 12px;
  }
}
</style>
