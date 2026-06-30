<template>
  <div class="system-monitor">
    <el-row :gutter="20">
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="flex justify-between items-center">
              <span>系统信息</span>
              <el-button size="small" @click="refreshSystemInfo">刷新</el-button>
            </div>
          </template>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="主机名">{{ systemInfo.hostname }}</el-descriptions-item>
            <el-descriptions-item label="操作系统">{{ systemInfo.platform }}</el-descriptions-item>
            <el-descriptions-item label="Python版本">{{ systemInfo.python_version }}</el-descriptions-item>
            <el-descriptions-item label="CPU核心数">{{ systemInfo.cpu_count }}</el-descriptions-item>
            <el-descriptions-item label="内存总量">{{ systemInfo.memory_total }}</el-descriptions-item>
            <el-descriptions-item label="磁盘总量">{{ systemInfo.disk_total }}</el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="flex justify-between items-center">
              <span>进程信息</span>
              <el-button size="small" @click="refreshProcessInfo">刷新</el-button>
            </div>
          </template>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="PID">{{ processInfo.pid }}</el-descriptions-item>
            <el-descriptions-item label="CPU使用率">{{ processInfo.cpu_percent }}%</el-descriptions-item>
            <el-descriptions-item label="内存使用">{{ processInfo.memory_mb }} MB</el-descriptions-item>
            <el-descriptions-item label="线程数">{{ processInfo.thread_count }}</el-descriptions-item>
            <el-descriptions-item label="启动时间">{{ processInfo.start_time }}</el-descriptions-item>
            <el-descriptions-item label="运行时长">{{ processInfo.uptime }}</el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>
    </el-row>

    <el-card style="margin-top: 20px">
      <template #header>
        <div class="flex justify-between items-center">
          <span>实时资源监控</span>
          <el-switch v-model="autoRefresh" active-text="自动刷新" />
        </div>
      </template>
      <div ref="chartRef" style="height: 300px" />
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import request from '../../utils/request'

const loading = ref(false)
const systemInfo = ref({})
const processInfo = ref({})
const autoRefresh = ref(false)
const chartRef = ref(null)

async function refreshSystemInfo() {
  try {
    const res = await request.get('/admin/system/system-info')
    // 后端返回嵌套结构：cpu/memory/disk/boot_time，这里映射为前端扁平字段
    systemInfo.value = {
      hostname: res.hostname || 'unknown',
      platform: res.platform || 'unknown',
      python_version: res.python_version || 'unknown',
      cpu_count: res.cpu?.cores ?? 'unknown',
      memory_total: res.memory?.total_gb != null ? res.memory.total_gb + ' GB' : 'unknown',
      disk_total: res.disk?.total_gb != null ? res.disk.total_gb + ' GB' : 'unknown',
      cpu_percent: res.cpu?.percent ?? 0,
      memory_percent: res.memory?.percent ?? 0,
      disk_percent: res.disk?.percent ?? 0,
      boot_time: res.boot_time,
    }
  } catch (e) {
    console.error('获取系统信息失败', e)
  }
}

function formatUptime(createTimeIso) {
  if (!createTimeIso) return '-'
  const start = new Date(createTimeIso).getTime()
  if (isNaN(start)) return '-'
  const seconds = Math.floor((Date.now() - start) / 1000)
  if (seconds < 0) return '-'
  const d = Math.floor(seconds / 86400)
  const h = Math.floor((seconds % 86400) / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const parts = []
  if (d > 0) parts.push(`${d}天`)
  if (h > 0) parts.push(`${h}小时`)
  parts.push(`${m}分钟`)
  return parts.join(' ')
}

async function refreshProcessInfo() {
  try {
    const res = await request.get('/admin/system/process-info')
    // 后端返回 memory_info.rss_mb / threads / create_time，映射为前端字段
    processInfo.value = {
      pid: res.pid,
      cpu_percent: res.cpu_percent,
      memory_mb: res.memory_info?.rss_mb ?? 0,
      thread_count: res.threads ?? 0,
      start_time: res.create_time || '-',
      uptime: formatUptime(res.create_time),
    }
  } catch (e) {
    console.error('获取进程信息失败', e)
  }
}

let timer = null

watch(autoRefresh, (val) => {
  if (timer) {
    clearInterval(timer)
    timer = null
  }
  if (val) {
    refreshSystemInfo()
    refreshProcessInfo()
    timer = setInterval(() => {
      refreshSystemInfo()
      refreshProcessInfo()
    }, 5000)
  }
})

onMounted(() => {
  refreshSystemInfo()
  refreshProcessInfo()
})

onUnmounted(() => {
  if (timer) {
    clearInterval(timer)
  }
})
</script>

<style scoped>
.flex { display: flex; }
.justify-between { justify-content: space-between; }
.items-center { align-items: center; }
</style>
