<template>
  <div class="system-config">
    <el-tabs v-model="activeSection">
      <el-tab-pane label="缓存管理" name="cache">
        <el-card>
          <template #header>
            <div class="flex justify-between items-center">
              <span>缓存统计</span>
              <el-button type="danger" @click="clearAllCache">清空所有缓存</el-button>
            </div>
          </template>
          <el-table :data="cacheStats" style="width: 100%">
            <el-table-column prop="name" label="缓存名称" />
            <el-table-column prop="count" label="条目数" />
            <el-table-column prop="size_mb" label="大小(MB)" />
            <el-table-column label="操作">
              <template #default="{ row }">
                <el-button size="small" type="danger" @click="clearCache(row.name)">清空</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-tab-pane>

      <el-tab-pane label="系统设置" name="settings">
        <el-form :model="systemSettings" label-width="120px">
          <el-form-item label="最大并发数">
            <el-input-number v-model="systemSettings.max_concurrent" :min="1" :max="100" />
          </el-form-item>
          <el-form-item label="请求超时(秒)">
            <el-input-number v-model="systemSettings.request_timeout" :min="1" :max="300" />
          </el-form-item>
          <el-form-item label="日志级别">
            <el-select v-model="systemSettings.log_level">
              <el-option label="DEBUG" value="DEBUG" />
              <el-option label="INFO" value="INFO" />
              <el-option label="WARNING" value="WARNING" />
              <el-option label="ERROR" value="ERROR" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="saveSettings">保存设置</el-button>
          </el-form-item>
        </el-form>
      </el-tab-pane>

      <el-tab-pane label="数据库" name="database">
        <el-card>
          <template #header>数据库连接</template>
          <el-descriptions :column="1" border>
            <el-descriptions-item label="数据库类型">{{ dbInfo.type }}</el-descriptions-item>
            <el-descriptions-item label="连接状态">
              <el-tag :type="dbInfo.connected ? 'success' : 'danger'">
                {{ dbInfo.connected ? '已连接' : '未连接' }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="表数量">{{ dbInfo.table_count }}</el-descriptions-item>
            <el-descriptions-item label="记录总数">{{ dbInfo.record_count }}</el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '../../utils/request'

const loading = ref(false)
const saving = ref(false)
const activeSection = ref('cache')
const cacheStats = ref([])
const systemSettings = reactive({
  max_concurrent: 10,
  request_timeout: 30,
  log_level: 'INFO',
})
const dbInfo = reactive({
  type: '',
  connected: false,
  table_count: 0,
  record_count: 0,
})

async function loadCacheStats() {
  try {
    const res = await request.get('/admin/system/cache/stats')
    cacheStats.value = res.caches
  } catch (e) {
    console.error('加载缓存统计失败', e)
  }
}

async function clearCache(name) {
  try {
    await request.post(`/admin/system/cache/clear/${name}`)
    ElMessage.success('缓存已清空')
    await loadCacheStats()
  } catch (e) {
    ElMessage.error('清空缓存失败')
  }
}

async function clearAllCache() {
  try {
    await ElMessageBox.confirm('确定要清空所有缓存吗？', '警告', { type: 'warning' })
    await request.post('/admin/system/cache/clear-all')
    ElMessage.success('所有缓存已清空')
    await loadCacheStats()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('清空缓存失败')
    }
  }
}

async function saveSettings() {
  saving.value = true
  try {
    await request.put('/admin/system/settings', systemSettings)
    ElMessage.success('设置已保存')
  } catch (e) {
    ElMessage.error('保存设置失败')
  } finally {
    saving.value = false
  }
}

async function loadDbInfo() {
  try {
    const res = await request.get('/admin/system/database/info')
    Object.assign(dbInfo, res)
  } catch (e) {
    console.error('加载数据库信息失败', e)
  }
}

onMounted(() => {
  loadCacheStats()
  loadDbInfo()
})
</script>

<style scoped>
.flex { display: flex; }
.justify-between { justify-content: space-between; }
.items-center { align-items: center; }
</style>
