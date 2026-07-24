<template>
  <div class="upgrade-page">
    <header class="page-header">
      <div>
        <h1>Trace Viewer</h1>
        <p>Playwright Trace 时间轴、网络瀑布、截图与 DOM 快照。</p>
      </div>
      <div class="actions">
        <el-input v-model="runIdFilter" clearable placeholder="按 Run ID 过滤" style="width: 160px" @keyup.enter="load" />
        <el-button type="primary" @click="load">刷新</el-button>
      </div>
    </header>

    <el-row :gutter="16">
      <el-col :span="8">
        <el-card shadow="never">
          <template #header>Trace 会话</template>
          <el-table :data="traces" v-loading="loading" height="640" highlight-current-row @current-change="onSelect">
            <el-table-column prop="id" label="ID" width="70" />
            <el-table-column prop="run_id" label="Run" width="90" />
            <el-table-column prop="status" label="状态" width="100" />
            <el-table-column prop="created_at" label="创建时间" min-width="140" show-overflow-tooltip />
          </el-table>
        </el-card>
      </el-col>

      <el-col :span="16">
        <el-card shadow="never" v-loading="detailLoading">
          <template #header>
            <div class="panel-title">
              <span>详情 {{ selected?.id ? `#${selected.id}` : '' }}</span>
              <el-tag v-if="detail" size="small">
                动作 {{ detail.action_count || 0 }} · {{ detail.duration_ms || 0 }}ms
                <template v-if="detail.browser_version"> · {{ detail.browser_version }}</template>
              </el-tag>
            </div>
          </template>

          <el-empty v-if="!detail" description="选择左侧会话" :image-size="64" />

          <template v-else>
            <el-alert v-if="detail.parse_errors?.length" type="warning" :closable="false" show-icon class="mb-12">
              {{ detail.parse_errors.join('; ') }}
            </el-alert>

            <div class="timeline-card mb-12">
              <div class="timeline-header">
                <strong>动作时间轴</strong>
                <span class="muted">总时长 {{ timelineDuration }}ms · 点击条块查看详情</span>
              </div>
              <div class="timeline-track" ref="trackEl">
                <div
                  v-for="action in detail.actions || []"
                  :key="action.id"
                  class="timeline-bar"
                  :class="{ active: activeAction?.id === action.id, error: !!action.error }"
                  :style="barStyle(action)"
                  :title="`${action.title || action.method} (${action.duration_ms || 0}ms)`"
                  @click="selectAction(action)"
                >
                  <span>{{ shortTitle(action) }}</span>
                </div>
                <div v-if="!(detail.actions || []).length" class="muted empty-track">无动作事件</div>
              </div>
            </div>

            <el-row :gutter="12" class="mb-12" v-if="activeAction">
              <el-col :span="12">
                <el-card shadow="never" class="inner-card">
                  <template #header>动作详情</template>
                  <dl class="kv">
                    <div><dt>标题</dt><dd>{{ activeAction.title || activeAction.method }}</dd></div>
                    <div><dt>选择器</dt><dd><code>{{ activeAction.selector || '-' }}</code></dd></div>
                    <div><dt>起点</dt><dd>{{ activeAction.start_ms || 0 }}ms</dd></div>
                    <div><dt>耗时</dt><dd>{{ activeAction.duration_ms || 0 }}ms</dd></div>
                    <div v-if="activeAction.error"><dt>错误</dt><dd class="danger">{{ formatError(activeAction.error) }}</dd></div>
                  </dl>
                  <pre v-if="activeAction.params" class="params-box">{{ pretty(activeAction.params) }}</pre>
                </el-card>
              </el-col>
              <el-col :span="12">
                <el-card shadow="never" class="inner-card">
                  <template #header>
                    <div class="panel-title">
                      <span>截图 / DOM</span>
                      <el-button size="small" @click="loadSnapshot">加载 DOM 快照</el-button>
                    </div>
                  </template>
                  <img v-if="actionShotUrl" :src="actionShotUrl" alt="action screenshot" class="shot-img" />
                  <el-empty v-else description="无动作截图" :image-size="48" />
                  <div v-if="snapshotHtml" class="snapshot-box" v-html="sanitizedSnapshot" />
                </el-card>
              </el-col>
            </el-row>

            <el-tabs v-model="detailTab">
              <el-tab-pane label="动作表" name="actions">
                <el-table :data="detail.actions || []" size="small" max-height="320" highlight-current-row @current-change="selectAction">
                  <el-table-column prop="title" label="动作" min-width="160">
                    <template #default="{ row }">{{ row.title || row.method }}</template>
                  </el-table-column>
                  <el-table-column prop="selector" label="选择器" min-width="160" show-overflow-tooltip />
                  <el-table-column prop="duration_ms" label="耗时" width="90" />
                  <el-table-column prop="start_ms" label="起点" width="90" />
                </el-table>
              </el-tab-pane>

              <el-tab-pane label="网络瀑布" name="network">
                <div class="waterfall mb-12">
                  <div
                    v-for="(net, idx) in detail.network || []"
                    :key="idx"
                    class="water-row"
                  >
                    <span class="water-label" :title="net.url">{{ net.method || 'GET' }} {{ shortUrl(net.url) }}</span>
                    <div class="water-track">
                      <div class="water-bar" :style="networkBarStyle(net)" :class="statusClass(net.status)" />
                    </div>
                    <span class="water-meta">{{ net.status || '-' }} · {{ net.duration_ms || 0 }}ms</span>
                  </div>
                  <el-empty v-if="!(detail.network || []).length" description="无网络事件" :image-size="48" />
                </div>
                <el-table :data="detail.network || []" size="small" max-height="240">
                  <el-table-column prop="method" label="方法" width="80" />
                  <el-table-column prop="url" label="URL" min-width="220" show-overflow-tooltip />
                  <el-table-column prop="status" label="状态" width="80" />
                  <el-table-column prop="duration_ms" label="耗时" width="90" />
                  <el-table-column prop="start_ms" label="起点" width="90" />
                </el-table>
              </el-tab-pane>

              <el-tab-pane label="控制台" name="console">
                <el-table :data="detail.console || []" size="small" max-height="420">
                  <el-table-column prop="level" label="级别" width="90" />
                  <el-table-column prop="text" label="内容" min-width="260" show-overflow-tooltip />
                </el-table>
              </el-tab-pane>

              <el-tab-pane label="截图资源" name="shots">
                <div class="shot-grid">
                  <div v-for="(shot, idx) in detail.screenshots || []" :key="idx" class="shot-item" @click="openShot(shot)">
                    <img v-if="shotBlobMap[shot.path || shot.name]" :src="shotBlobMap[shot.path || shot.name]" alt="shot" />
                    <code>{{ shot.name || shot.path || `shot-${idx}` }}</code>
                  </div>
                  <el-empty v-if="!(detail.screenshots || []).length" description="无截图元数据" :image-size="48" />
                </div>
              </el-tab-pane>
            </el-tabs>
          </template>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import { storeToRefs } from 'pinia'
import { ElMessage } from 'element-plus'
import { featureUpgradesApi, fetchAuthBlobUrl } from '@/api/feature-upgrades'
import { useProjectStore } from '@/stores/project'

const route = useRoute()
const { projectId } = storeToRefs(useProjectStore())
const loading = ref(false)
const detailLoading = ref(false)
const traces = ref([])
const selected = ref(null)
const detail = ref(null)
const activeAction = ref(null)
const actionShotUrl = ref('')
const snapshotHtml = ref('')
const detailTab = ref('actions')
const runIdFilter = ref(route.query.runId ? String(route.query.runId) : '')
const shotBlobMap = reactive({})
const objectUrls = []

const timelineDuration = computed(() => {
  const d = detail.value?.timeline?.duration_ms || detail.value?.duration_ms || 0
  if (d > 0) return d
  const actions = detail.value?.actions || []
  let max = 0
  for (const a of actions) {
    max = Math.max(max, (a.start_ms || 0) + (a.duration_ms || 20))
  }
  return max || 1
})

const sanitizedSnapshot = computed(() => {
  // Basic strip of scripts for display safety.
  return String(snapshotHtml.value || '')
    .replace(/<script[\s\S]*?>[\s\S]*?<\/script>/gi, '')
    .replace(/\son\w+="[^"]*"/gi, '')
    .replace(/\son\w+='[^']*'/gi, '')
})

function track(url) {
  if (url) objectUrls.push(url)
  return url
}

function revokeAll() {
  while (objectUrls.length) {
    const u = objectUrls.pop()
    try { URL.revokeObjectURL(u) } catch { /* ignore */ }
  }
  for (const key of Object.keys(shotBlobMap)) delete shotBlobMap[key]
  actionShotUrl.value = ''
}

function shortTitle(action) {
  const t = String(action.title || action.method || action.id || '')
  return t.length > 18 ? `${t.slice(0, 16)}…` : t
}

function shortUrl(url) {
  const s = String(url || '')
  return s.length > 42 ? `${s.slice(0, 40)}…` : s
}

function pretty(value) {
  try { return JSON.stringify(value, null, 2) } catch { return String(value) }
}

function formatError(error) {
  if (!error) return ''
  if (typeof error === 'string') return error
  return pretty(error)
}

function barStyle(action) {
  const total = timelineDuration.value || 1
  const start = Number(action.start_ms || 0)
  const dur = Math.max(8, Number(action.duration_ms || 20))
  const left = Math.min(98, (start / total) * 100)
  const width = Math.max(1.2, Math.min(100 - left, (dur / total) * 100))
  return { left: `${left}%`, width: `${width}%` }
}

function networkBarStyle(net) {
  const total = timelineDuration.value || 1
  const start = Number(net.start_ms || 0)
  const dur = Math.max(6, Number(net.duration_ms || 20))
  const left = Math.min(98, (start / total) * 100)
  const width = Math.max(1, Math.min(100 - left, (dur / total) * 100))
  return { left: `${left}%`, width: `${width}%` }
}

function statusClass(status) {
  const n = Number(status)
  if (!n) return ''
  if (n >= 500) return 's5'
  if (n >= 400) return 's4'
  if (n >= 300) return 's3'
  return 's2'
}

async function selectAction(action) {
  activeAction.value = action || null
  snapshotHtml.value = ''
  if (actionShotUrl.value) {
    // keep in objectUrls list; just clear display pointer
    actionShotUrl.value = ''
  }
  if (!action || !selected.value?.id) return
  try {
    const url = await fetchAuthBlobUrl(
      `/api/feature-upgrades/traces/${selected.value.id}/actions/${encodeURIComponent(action.id)}/screenshot`,
    )
    actionShotUrl.value = track(url)
  } catch {
    actionShotUrl.value = ''
  }
}

async function loadSnapshot() {
  if (!activeAction.value || !selected.value?.id) return
  try {
    const res = await featureUpgradesApi.getTraceActionSnapshot(selected.value.id, activeAction.value.id)
    snapshotHtml.value = res.html || ''
    if (!snapshotHtml.value) ElMessage.info('该动作无 DOM 快照')
  } catch (error) {
    ElMessage.error(error.message || '加载 DOM 失败')
  }
}

async function openShot(shot) {
  const name = shot.path || shot.name
  if (!name || !selected.value?.id) return
  if (shotBlobMap[name]) return
  try {
    const url = await fetchAuthBlobUrl(
      shot.url || `/api/feature-upgrades/traces/${selected.value.id}/resources/${encodeURIComponent(name)}`,
    )
    shotBlobMap[name] = track(url)
  } catch (error) {
    ElMessage.error(error.message || '截图加载失败')
  }
}

async function onSelect(row) {
  selected.value = row
  detail.value = null
  activeAction.value = null
  snapshotHtml.value = ''
  revokeAll()
  if (!row?.id) return
  detailLoading.value = true
  try {
    detail.value = await featureUpgradesApi.getTrace(row.id)
    if ((detail.value.actions || []).length) {
      await selectAction(detail.value.actions[0])
    }
    // Prefetch first few screenshots
    for (const shot of (detail.value.screenshots || []).slice(0, 6)) {
      openShot(shot)
    }
  } catch (error) {
    ElMessage.error(error.message || '解析 Trace 失败')
  } finally {
    detailLoading.value = false
  }
}

async function load() {
  loading.value = true
  try {
    const res = await featureUpgradesApi.listTraces(projectId.value, {
      run_id: runIdFilter.value ? Number(runIdFilter.value) : undefined,
    })
    traces.value = res.items || []
    if (traces.value.length === 1) await onSelect(traces.value[0])
  } catch (error) {
    ElMessage.error(error.message || '加载失败')
  } finally {
    loading.value = false
  }
}

onMounted(load)
onBeforeUnmount(revokeAll)
</script>

<style scoped>
.upgrade-page { padding: 20px; display: flex; flex-direction: column; gap: 16px; }
.page-header { display: flex; justify-content: space-between; gap: 12px; }
.page-header h1 { margin: 0 0 6px; font-size: 22px; }
.page-header p { margin: 0; color: #64748b; }
.actions { display: flex; gap: 8px; align-items: center; }
.panel-title { display: flex; justify-content: space-between; align-items: center; gap: 8px; }
.mb-12 { margin-bottom: 12px; }
.muted { color: #64748b; font-size: 12px; }
.danger { color: #b91c1c; }
.timeline-card { border: 1px solid #e2e8f0; border-radius: 10px; padding: 10px 12px; background: #f8fafc; }
.timeline-header { display: flex; justify-content: space-between; margin-bottom: 8px; }
.timeline-track { position: relative; height: 56px; background: linear-gradient(90deg, #e2e8f0 1px, transparent 1px) 0 0 / 10% 100%, #fff; border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden; }
.timeline-bar { position: absolute; top: 12px; height: 32px; border-radius: 6px; background: #3b82f6; color: #fff; font-size: 11px; display: flex; align-items: center; padding: 0 6px; cursor: pointer; overflow: hidden; white-space: nowrap; box-shadow: 0 1px 2px rgba(15, 23, 42, 0.15); }
.timeline-bar.active { outline: 2px solid #0f172a; z-index: 2; }
.timeline-bar.error { background: #ef4444; }
.empty-track { padding: 18px; }
.inner-card { min-height: 220px; }
.kv { margin: 0; display: grid; gap: 6px; }
.kv > div { display: grid; grid-template-columns: 70px 1fr; gap: 8px; font-size: 13px; }
.kv dt { color: #64748b; }
.kv dd { margin: 0; word-break: break-all; }
.params-box, .snapshot-box { margin-top: 8px; max-height: 160px; overflow: auto; background: #0b1220; color: #e2e8f0; border-radius: 8px; padding: 8px; font-size: 12px; }
.snapshot-box { background: #fff; color: #0f172a; border: 1px solid #e2e8f0; }
.shot-img { width: 100%; max-height: 180px; object-fit: contain; background: #0b1220; border-radius: 8px; }
.waterfall { display: flex; flex-direction: column; gap: 6px; max-height: 220px; overflow: auto; }
.water-row { display: grid; grid-template-columns: 220px 1fr 110px; gap: 8px; align-items: center; font-size: 12px; }
.water-label { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.water-track { position: relative; height: 12px; background: #f1f5f9; border-radius: 999px; overflow: hidden; }
.water-bar { position: absolute; top: 0; bottom: 0; border-radius: 999px; background: #38bdf8; }
.water-bar.s2 { background: #22c55e; }
.water-bar.s3 { background: #eab308; }
.water-bar.s4 { background: #f97316; }
.water-bar.s5 { background: #ef4444; }
.water-meta { color: #64748b; text-align: right; }
.shot-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 10px; }
.shot-item { border: 1px solid #e2e8f0; border-radius: 8px; padding: 8px; cursor: pointer; background: #fff; display: flex; flex-direction: column; gap: 6px; }
.shot-item img { width: 100%; height: 100px; object-fit: contain; background: #0b1220; border-radius: 6px; }
.shot-item code { font-size: 11px; color: #0f766e; word-break: break-all; }
code { color: #0f766e; font-size: 12px; }
</style>
