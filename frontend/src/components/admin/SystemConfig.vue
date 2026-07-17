<template>
  <div class="system-config">
    <el-tabs v-model="activeSection">
      <el-tab-pane label="缂撳瓨绠＄悊" name="cache">
        <el-card>
          <template #header>
            <div class="flex justify-between items-center">
              <span>缂撳瓨缁熻</span>
              <el-button type="danger" @click="clearAllCache">娓呯┖鎵€鏈夌紦瀛</el-button>
            </div>
          </template>
          <el-table :data="cacheStats" style="width: 100%">
            <el-table-column prop="name" label="缂撳瓨鍚嶇О" />
            <el-table-column prop="count" label="鏉＄洰鏁? />
            <el-table-column prop="size_mb" label="澶у皬(MB)" />
            <el-table-column label="鎿嶄綔">
              <template #default="{ row }">
                <el-button size="small" type="danger" @click="clearCache(row.name)">娓呯┖</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-tab-pane>

      <el-tab-pane label="绯荤粺璁剧疆" name="settings">
        <el-form :model="systemSettings" label-width="120px">
          <el-form-item label="鏈€澶у苟鍙戞暟">
            <el-input-number v-model="systemSettings.max_concurrent" :min="1" :max="100" />
          </el-form-item>
          <el-form-item label="璇锋眰瓒呮椂(绉?">
            <el-input-number v-model="systemSettings.request_timeout" :min="1" :max="300" />
          </el-form-item>
          <el-form-item label="鏃ュ織绾у埆">
            <el-select v-model="systemSettings.log_level">
              <el-option label="DEBUG" value="DEBUG" />
              <el-option label="INFO" value="INFO" />
              <el-option label="WARNING" value="WARNING" />
              <el-option label="ERROR" value="ERROR" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="saveSettings">淇濆瓨璁剧疆</el-button>
          </el-form-item>
        </el-form>
      </el-tab-pane>

      <el-tab-pane label="鏁版嵁搴? name="database">
        <el-card>
          <template #header>鏁版嵁搴撹繛鎺</template>
          <el-descriptions :column="1" border>
            <el-descriptions-item label="鏁版嵁搴撶被鍨?>{{ dbInfo.type }}</el-descriptions-item>
            <el-descriptions-item label="杩炴帴鐘舵€?>
              <el-tag :type="dbInfo.connected ? 'success' : 'danger'">
                {{ dbInfo.connected ? '宸茶繛鎺? : '鏈繛鎺? }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="琛ㄦ暟閲?>{{ dbInfo.table_count }}</el-descriptions-item>
            <el-descriptions-item label="璁板綍鎬绘暟">{{ dbInfo.record_count }}</el-descriptions-item>
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
    console.error('鍔犺浇缂撳瓨缁熻澶辫触', e)
  }
}

async function clearCache(name) {
  try {
    await request.post(`/admin/system/cache/clear/${name}`)
    ElMessage.success('缂撳瓨宸叉竻绌?)
    await loadCacheStats()
  } catch (e) {
    ElMessage.error('娓呯┖缂撳瓨澶辫触')
  }
}

async function clearAllCache() {
  try {
    await ElMessageBox.confirm('纭畾瑕佹竻绌烘墍鏈夌紦瀛樺悧锛?, '璀﹀憡', { type: 'warning' })
    await request.post('/admin/system/cache/clear-all')
    ElMessage.success('鎵€鏈夌紦瀛樺凡娓呯┖')
    await loadCacheStats()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('娓呯┖缂撳瓨澶辫触')
    }
  }
}

async function saveSettings() {
  saving.value = true
  try {
    await request.put('/admin/system/settings', systemSettings)
    ElMessage.success('璁剧疆宸蹭繚瀛?)
  } catch (e) {
    ElMessage.error('淇濆瓨璁剧疆澶辫触')
  } finally {
    saving.value = false
  }
}

async function loadDbInfo() {
  try {
    const res = await request.get('/admin/system/database/info')
    Object.assign(dbInfo, res)
  } catch (e) {
    console.error('鍔犺浇鏁版嵁搴撲俊鎭け璐?, e)
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

