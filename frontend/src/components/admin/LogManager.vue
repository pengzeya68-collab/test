<template>
  <div class="log-manager">
    <el-row :gutter="20">
      <!-- 日志统计 -->
      <el-col :span="8">
        <el-card>
          <template #header>日志统计</template>
          <el-descriptions :column="1" border>
            <el-descriptions-item label="总行数">{{ logStats.total_lines || 0 }}</el-descriptions-item>
            <el-descriptions-item label="文件大小">{{ logStats.file_size_mb || 0 }} MB</el-descriptions-item>
            <el-descriptions-item label="DEBUG">{{ logStats.level_counts?.DEBUG || 0 }}</el-descriptions-item>
            <el-descriptions-item label="INFO">{{ logStats.level_counts?.INFO || 0 }}</el-descriptions-item>
            <el-descriptions-item label="WARNING">{{ logStats.level_counts?.WARNING || 0 }}</el-descriptions-item>
            <el-descriptions-item label="ERROR">{{ logStats.level_counts?.ERROR || 0 }}</el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>

      <!-- 日志文件列表 -->
      <el-col :span="8">
        <el-card>
          <template #header>日志文件</template>
          <el-table :data="logFiles" style="width: 100%">
            <el-table-column prop="name" label="文件名" />
            <el-table-column prop="size_mb" label="大小(MB)" />
            <el-table-column label="操作">
              <template #default="{ row }">
                <el-button size="small" @click="selectFile(row.name)">查看</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <!-- 日志级别设置 -->
      <el-col :span="8">
        <el-card>
          <template #header>日志级别</template>
          <el-radio-group v-model="currentLevel" @change="changeLogLevel">
            <el-radio-button label="DEBUG" />
            <el-radio-button label="INFO" />
            <el-radio-button label="WARNING" />
            <el-radio-button label="ERROR" />
          </el-radio-group>
          <div style="margin-top: 16px">
            <el-button type="danger" @click="clearOldLogs">清理30天前日志</el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 日志内容 -->
    <el-card style="margin-top: 20px">
      <template #header>
        <div class="flex justify-between items-center">
          <span>日志内容: {{ selectedFile }}</span>
          <div class="flex gap-2">
            <el-input v-model="filterKeyword" placeholder="关键词过滤" style="width: 200px" />
            <el-select v-model="filterLevel" placeholder="级别过滤" style="width: 120px" clearable>
              <el-option label="DEBUG" value="DEBUG" />
              <el-option label="INFO" value="INFO" />
              <el-option label="WARNING" value="WARNING" />
              <el-option label="ERROR" value="ERROR" />
            </el-select>
            <el-input-number v-model="lineCount" :min="10" :max="1000" :step="10" />
            <el-button @click="loadLogs">刷新</el-button>
          </div>
        </div>
      </template>
      <el-input v-model="logContent" type="textarea" :rows="20" readonly />
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '../../utils/request'

const loading = ref(false)
const currentLevel = ref('INFO')
const selectedFile = ref('app.log')
const filterKeyword = ref('')
const filterLevel = ref('')
const lineCount = ref(100)
const logContent = ref('')
const logFiles = ref([])
const logStats = reactive({
  total_lines: 0,
  file_size_mb: 0,
  level_counts: {},
})

function getLevelType(level) {
  const types = {
    'DEBUG': 'info',
    'INFO': '',
    'WARNING': 'warning',
    'ERROR': 'danger',
  }
  return types[level] || ''
}

async function loadLogStats() {
  try {
    const res = await request.get('/admin/system/logs/stats')
    Object.assign(logStats, res)
  } catch (e) {
    console.error('加载日志统计失败', e)
  }
}

async function loadLogFiles() {
  try {
    const res = await request.get('/admin/system/logs/files')
    logFiles.value = res.files
  } catch (e) {
    console.error('加载日志文件列表失败', e)
  }
}

async function loadLogs() {
  loading.value = true
  try {
    const res = await request.get('/admin/system/logs/content', {
      params: {
        filename: selectedFile.value,
        lines: lineCount.value,
        level: filterLevel.value || undefined,
        keyword: filterKeyword.value || undefined,
      },
    })
    logContent.value = (res.logs || []).join('\n')
  } catch (e) {
    ElMessage.error('加载日志内容失败')
  } finally {
    loading.value = false
  }
}

function selectFile(filename) {
  selectedFile.value = filename
  loadLogs()
}

async function changeLogLevel(level) {
  try {
    await request.put('/admin/system/logs/level', { level })
    ElMessage.success(`日志级别已设置为 ${level}`)
  } catch (e) {
    ElMessage.error('设置日志级别失败')
  }
}

async function clearOldLogs() {
  try {
    await ElMessageBox.confirm('确定要清理 30 天前的日志吗？此操作不可恢复。', '警告', {
      type: 'warning',
    })
    const res = await request.post('/admin/system/logs/clear', { days: 30 })
    ElMessage.success(res.message)
    await loadLogFiles()
    await loadLogStats()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('清理日志失败')
    }
  }
}

onMounted(() => {
  Promise.all([
    loadLogStats(),
    loadLogFiles(),
    loadLogs(),
  ]).catch(err => {
    console.error('加载日志数据失败:', err)
  })
  
  request.get('/admin/system/logs/level').then(levelRes => {
    currentLevel.value = levelRes.level
  }).catch(err => {
    console.error('获取日志级别失败:', err)
  })
})
</script>

<style scoped>
.flex { display: flex; }
.justify-between { justify-content: space-between; }
.items-center { align-items: center; }
.gap-2 { gap: 8px; }
</style>
