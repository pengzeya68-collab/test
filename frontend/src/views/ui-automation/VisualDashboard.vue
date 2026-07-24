<template>
  <div class="upgrade-page">
    <header class="page-header">
      <div>
        <h1>视觉回归</h1>
        <p>基线管理、三图 Diff 审核与项目统计。运行截图会自动进入对比流水线。</p>
      </div>
      <div class="actions">
        <el-select v-model="verdictFilter" clearable placeholder="判定筛选" style="width: 140px" @change="load">
          <el-option label="待审核" value="pending" />
          <el-option label="已通过" value="approved" />
          <el-option label="自动通过" value="auto_passed" />
          <el-option label="已拒绝" value="rejected" />
          <el-option label="无基线" value="no_baseline" />
        </el-select>
        <el-button type="primary" @click="load">刷新</el-button>
      </div>
    </header>

    <el-row :gutter="12" class="stat-row" v-if="stats">
      <el-col :span="6"><el-statistic title="对比次数" :value="stats.comparison_count || 0" /></el-col>
      <el-col :span="6"><el-statistic title="活跃基线" :value="stats.active_baselines || 0" /></el-col>
      <el-col :span="6"><el-statistic title="待审核" :value="stats.pending_reviews || 0" /></el-col>
      <el-col :span="6"><el-statistic title="基线总数" :value="stats.baseline_count || 0" /></el-col>
    </el-row>

    <el-tabs v-model="activeTab">
      <el-tab-pane label="基线" name="baselines">
        <el-table :data="baselines" v-loading="loading" stripe @row-click="previewBaseline">
          <el-table-column prop="id" label="ID" width="70" />
          <el-table-column prop="ui_step_id" label="步骤 ID" min-width="160" />
          <el-table-column prop="browser_engine" label="引擎" width="100" />
          <el-table-column label="视口" width="140">
            <template #default="{ row }">{{ row.viewport_width }}×{{ row.viewport_height }}</template>
          </el-table-column>
          <el-table-column prop="version" label="版本" width="80" />
          <el-table-column prop="status" label="状态" width="110">
            <template #default="{ row }">
              <el-tag :type="row.status === 'active' ? 'success' : 'info'">{{ row.status }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="image_hash" label="Hash" min-width="180">
            <template #default="{ row }"><code>{{ String(row.image_hash || '').slice(0, 16) }}</code></template>
          </el-table-column>
          <el-table-column label="预览" width="100">
            <template #default="{ row }">
              <el-button link type="primary" @click.stop="previewBaseline(row)">查看</el-button>
            </template>
          </el-table-column>
          <el-table-column prop="updated_at" label="更新时间" min-width="160" />
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="对比审核" name="comparisons">
        <el-row :gutter="16">
          <el-col :span="10">
            <el-table
              :data="comparisons"
              v-loading="loading"
              stripe
              height="560"
              highlight-current-row
              @current-change="openComparison"
            >
              <el-table-column prop="id" label="ID" width="70" />
              <el-table-column prop="run_id" label="Run" width="80" />
              <el-table-column prop="ui_step_id" label="步骤" min-width="120" show-overflow-tooltip />
              <el-table-column prop="diff_percentage" label="差异%" width="90">
                <template #default="{ row }">{{ Number(row.diff_percentage || 0).toFixed(3) }}</template>
              </el-table-column>
              <el-table-column prop="verdict" label="判定" width="110">
                <template #default="{ row }">
                  <el-tag :type="verdictType(row.verdict)">{{ row.verdict }}</el-tag>
                </template>
              </el-table-column>
            </el-table>
          </el-col>

          <el-col :span="14">
            <el-card shadow="never" v-loading="detailLoading" class="diff-card">
              <template #header>
                <div class="panel-title">
                  <span>Diff 审核 {{ selected?.id ? `#${selected.id}` : '' }}</span>
                  <div class="actions" v-if="selected">
                    <el-tag :type="verdictType(selected.verdict)" size="small">{{ selected.verdict }}</el-tag>
                    <el-tag size="small" type="info">差异 {{ Number(selected.diff_percentage || 0).toFixed(3) }}%</el-tag>
                  </div>
                </div>
              </template>

              <el-empty v-if="!selected" description="选择左侧对比记录查看三图 Diff" :image-size="64" />

              <template v-else>
                <div class="meta-row">
                  <span>Run #{{ selected.run_id }}</span>
                  <span>步骤 {{ selected.ui_step_id || '-' }}</span>
                  <span>像素 {{ selected.mismatched_pixels || 0 }}/{{ selected.total_pixels || 0 }}</span>
                  <span>阈值 {{ selected.threshold }}</span>
                </div>

                <div class="diff-toolbar">
                  <el-radio-group v-model="viewMode" size="small">
                    <el-radio-button label="side">并排</el-radio-button>
                    <el-radio-button label="overlay">叠加</el-radio-button>
                    <el-radio-button label="diff">仅 Diff</el-radio-button>
                  </el-radio-group>
                  <el-slider
                    v-if="viewMode === 'overlay'"
                    v-model="overlayOpacity"
                    :min="0"
                    :max="100"
                    style="width: 160px; margin-left: 12px"
                  />
                </div>

                <div v-if="viewMode === 'side'" class="diff-grid">
                  <figure class="diff-panel">
                    <figcaption>Baseline</figcaption>
                    <img v-if="blobUrls.baseline" :src="blobUrls.baseline" alt="baseline" />
                    <el-empty v-else description="无基线图" :image-size="40" />
                  </figure>
                  <figure class="diff-panel">
                    <figcaption>Actual</figcaption>
                    <img v-if="blobUrls.actual" :src="blobUrls.actual" alt="actual" />
                    <el-empty v-else description="无实际图" :image-size="40" />
                  </figure>
                  <figure class="diff-panel">
                    <figcaption>Diff Heatmap</figcaption>
                    <img v-if="blobUrls.diff" :src="blobUrls.diff" alt="diff" />
                    <el-empty v-else description="无差异图（可能完全一致）" :image-size="40" />
                  </figure>
                </div>

                <div v-else-if="viewMode === 'overlay'" class="overlay-wrap">
                  <div class="overlay-stage">
                    <img v-if="blobUrls.baseline" class="base" :src="blobUrls.baseline" alt="baseline" />
                    <img
                      v-if="blobUrls.actual"
                      class="top"
                      :src="blobUrls.actual"
                      alt="actual"
                      :style="{ opacity: overlayOpacity / 100 }"
                    />
                  </div>
                  <div class="muted">拖动滑块调节 Actual 透明度（0=仅基线，100=仅实际）</div>
                </div>

                <div v-else class="diff-single">
                  <img v-if="blobUrls.diff" :src="blobUrls.diff" alt="diff" />
                  <el-empty v-else description="无差异图" :image-size="48" />
                </div>

                <div class="verdict-bar" v-if="canReview">
                  <el-input v-model="reviewComment" placeholder="审核备注（可选）" clearable style="flex: 1" />
                  <el-checkbox v-model="promoteBaseline">通过后提升为新基线</el-checkbox>
                  <el-button type="success" :loading="verdictLoading" @click="setVerdict('approved')">通过</el-button>
                  <el-button type="danger" :loading="verdictLoading" @click="setVerdict('rejected')">拒绝</el-button>
                </div>
                <el-alert
                  v-else-if="selected.verdict_comment"
                  type="info"
                  :closable="false"
                  show-icon
                  :title="`备注：${selected.verdict_comment}`"
                />
              </template>
            </el-card>
          </el-col>
        </el-row>
      </el-tab-pane>

      <el-tab-pane label="阈值配置" name="config">
        <el-form label-width="160px" style="max-width: 520px" v-loading="configLoading">
          <el-form-item label="默认阈值 %">
            <el-input-number v-model="configForm.default_threshold" :min="0" :max="100" :step="0.01" />
          </el-form-item>
          <el-form-item label="自动通过低于 %">
            <el-input-number v-model="configForm.auto_approve_below" :min="0" :max="100" :step="0.01" />
          </el-form-item>
          <el-form-item label="自动拒绝高于 %">
            <el-input-number v-model="configForm.auto_reject_above" :min="0" :max="100" :step="0.1" />
          </el-form-item>
          <el-form-item label="默认引擎">
            <el-select v-model="configForm.default_engine" style="width: 200px">
              <el-option label="chromium" value="chromium" />
              <el-option label="firefox" value="firefox" />
              <el-option label="webkit" value="webkit" />
            </el-select>
          </el-form-item>
          <el-form-item label="全页截图">
            <el-switch v-model="configForm.capture_full_page" />
          </el-form-item>
          <el-button type="primary" :loading="configLoading" @click="saveConfig">保存配置</el-button>
        </el-form>
      </el-tab-pane>
    </el-tabs>

    <el-dialog v-model="baselineDialog" title="基线预览" width="720px" @closed="revokeBaselinePreview">
      <img v-if="baselinePreviewUrl" :src="baselinePreviewUrl" alt="baseline" class="dialog-img" />
      <el-empty v-else description="无法加载基线图" />
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { ElMessage } from 'element-plus'
import { featureUpgradesApi, fetchAuthBlobUrl } from '@/api/feature-upgrades'
import { useProjectStore } from '@/stores/project'

const { projectId } = storeToRefs(useProjectStore())
const loading = ref(false)
const detailLoading = ref(false)
const verdictLoading = ref(false)
const configLoading = ref(false)
const baselines = ref([])
const comparisons = ref([])
const stats = ref(null)
const activeTab = ref('comparisons')
const selected = ref(null)
const comparisonDetail = ref(null)
const verdictFilter = ref('')
const viewMode = ref('side')
const overlayOpacity = ref(55)
const reviewComment = ref('')
const promoteBaseline = ref(true)
const baselineDialog = ref(false)
const baselinePreviewUrl = ref('')
const blobUrls = reactive({ baseline: '', actual: '', diff: '' })
const configForm = reactive({
  default_threshold: 0.1,
  auto_approve_below: 0.01,
  auto_reject_above: 5,
  default_engine: 'chromium',
  capture_full_page: true,
})

const canReview = computed(() => selected.value && ['pending', 'no_baseline'].includes(selected.value.verdict))

function verdictType(verdict) {
  if (verdict === 'auto_passed' || verdict === 'approved') return 'success'
  if (verdict === 'rejected') return 'danger'
  if (verdict === 'no_baseline') return 'info'
  return 'warning'
}

function revokeBlobUrls() {
  for (const key of ['baseline', 'actual', 'diff']) {
    if (blobUrls[key]) {
      URL.revokeObjectURL(blobUrls[key])
      blobUrls[key] = ''
    }
  }
}

function revokeBaselinePreview() {
  if (baselinePreviewUrl.value) {
    URL.revokeObjectURL(baselinePreviewUrl.value)
    baselinePreviewUrl.value = ''
  }
}

async function loadImageBlobs(detail) {
  revokeBlobUrls()
  if (!detail?.id) return
  const images = detail.images || {}
  const tasks = [
    ['baseline', images.baseline_url],
    ['actual', images.actual_url || `/api/feature-upgrades/visual/comparisons/${detail.id}/image/actual`],
    ['diff', images.diff_url],
  ]
  await Promise.all(tasks.map(async ([key, path]) => {
    if (!path) return
    try {
      blobUrls[key] = await fetchAuthBlobUrl(path)
    } catch {
      blobUrls[key] = ''
    }
  }))
}

async function load() {
  loading.value = true
  try {
    const [baseRes, cmpRes, statRes, cfg] = await Promise.all([
      featureUpgradesApi.listBaselines({ project_id: projectId.value }),
      featureUpgradesApi.listComparisons({
        project_id: projectId.value,
        verdict: verdictFilter.value || undefined,
      }),
      featureUpgradesApi.visualStats(projectId.value),
      featureUpgradesApi.getVisualConfig(projectId.value).catch(() => null),
    ])
    baselines.value = baseRes.items || []
    comparisons.value = cmpRes.items || []
    stats.value = statRes
    if (cfg) {
      configForm.default_threshold = cfg.default_threshold ?? 0.1
      configForm.auto_approve_below = cfg.auto_approve_below ?? 0.01
      configForm.auto_reject_above = cfg.auto_reject_above ?? 5
      configForm.default_engine = cfg.default_engine || 'chromium'
      configForm.capture_full_page = cfg.capture_full_page !== false
    }
    if (selected.value) {
      const still = comparisons.value.find((item) => item.id === selected.value.id)
      if (still) await openComparison(still)
      else {
        selected.value = null
        comparisonDetail.value = null
        revokeBlobUrls()
      }
    } else if (comparisons.value.length) {
      const pending = comparisons.value.find((item) => item.verdict === 'pending' || item.verdict === 'no_baseline')
      await openComparison(pending || comparisons.value[0])
    }
  } catch (error) {
    ElMessage.error(error.message || '加载失败')
  } finally {
    loading.value = false
  }
}

async function openComparison(row) {
  selected.value = row || null
  comparisonDetail.value = null
  reviewComment.value = ''
  revokeBlobUrls()
  if (!row?.id) return
  detailLoading.value = true
  try {
    comparisonDetail.value = await featureUpgradesApi.getComparison(row.id)
    selected.value = { ...row, ...comparisonDetail.value }
    await loadImageBlobs(comparisonDetail.value)
  } catch (error) {
    ElMessage.error(error.message || '加载对比详情失败')
  } finally {
    detailLoading.value = false
  }
}

async function setVerdict(verdict) {
  if (!selected.value?.id) return
  verdictLoading.value = true
  try {
    await featureUpgradesApi.setVisualVerdict(selected.value.id, {
      verdict,
      promote_baseline: verdict === 'approved' ? promoteBaseline.value : false,
      comment: reviewComment.value || (verdict === 'approved' ? '前端 Diff 审核通过' : '前端 Diff 审核拒绝'),
    })
    ElMessage.success('已更新判定')
    await load()
  } catch (error) {
    ElMessage.error(error.message || '判定失败')
  } finally {
    verdictLoading.value = false
  }
}

async function previewBaseline(row) {
  if (!row?.id) return
  revokeBaselinePreview()
  try {
    baselinePreviewUrl.value = await fetchAuthBlobUrl(`/api/feature-upgrades/visual/baselines/${row.id}/image`)
    baselineDialog.value = true
  } catch (error) {
    ElMessage.error(error.message || '基线图片加载失败')
  }
}

async function saveConfig() {
  configLoading.value = true
  try {
    await featureUpgradesApi.updateVisualConfig(projectId.value, { ...configForm })
    ElMessage.success('配置已保存')
  } catch (error) {
    ElMessage.error(error.message || '保存失败')
  } finally {
    configLoading.value = false
  }
}

watch(projectId, () => {
  selected.value = null
  comparisonDetail.value = null
  revokeBlobUrls()
  load()
})

onMounted(load)
onBeforeUnmount(() => {
  revokeBlobUrls()
  revokeBaselinePreview()
})
</script>

<style scoped>
.upgrade-page { padding: 20px; display: flex; flex-direction: column; gap: 16px; }
.page-header { display: flex; justify-content: space-between; gap: 12px; align-items: flex-start; }
.page-header h1 { margin: 0 0 6px; font-size: 22px; }
.page-header p { margin: 0; color: #64748b; }
.actions { display: flex; gap: 8px; align-items: center; }
.panel-title { display: flex; justify-content: space-between; align-items: center; gap: 12px; }
.diff-card { min-height: 560px; }
.meta-row { display: flex; flex-wrap: wrap; gap: 12px; color: #64748b; font-size: 12px; margin-bottom: 10px; }
.diff-toolbar { display: flex; align-items: center; margin-bottom: 12px; }
.diff-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px; }
.diff-panel { margin: 0; border: 1px solid #e2e8f0; border-radius: 10px; background: #0b1220; overflow: hidden; }
.diff-panel figcaption { background: #111827; color: #e5e7eb; font-size: 12px; padding: 6px 10px; }
.diff-panel img, .diff-single img, .dialog-img, .overlay-stage img { width: 100%; display: block; object-fit: contain; max-height: 360px; background: repeating-conic-gradient(#1f2937 0% 25%, #111827 0% 50%) 50% / 16px 16px; }
.overlay-wrap { display: flex; flex-direction: column; gap: 8px; }
.overlay-stage { position: relative; border: 1px solid #e2e8f0; border-radius: 10px; overflow: hidden; background: #0b1220; min-height: 280px; }
.overlay-stage .base, .overlay-stage .top { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: contain; }
.overlay-stage .base { position: relative; }
.verdict-bar { display: flex; flex-wrap: wrap; gap: 10px; align-items: center; margin-top: 14px; }
.muted { color: #64748b; font-size: 12px; }
code { color: #0f766e; font-size: 12px; }
@media (max-width: 1200px) {
  .diff-grid { grid-template-columns: 1fr; }
}
</style>
