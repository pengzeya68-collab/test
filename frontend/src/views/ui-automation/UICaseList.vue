<template>
  <div class="ui-case-list">
    <div class="page-header">
      <div class="header-left">
        <h2>UI 自动化用例</h2>
        <span class="page-subtitle">管理、编辑和查看 UI 自动化用例</span>
      </div>
      <div class="header-right">
        <el-input
          v-model="keyword"
          placeholder="搜索用例名称..."
          style="width: 240px"
          clearable
          @clear="loadCases"
          @keyup.enter="loadCases"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-button @click="openAiMetrics">AI 评估指标</el-button>
        <el-button @click="router.push('/ui-automation/ai-design')">需求测试设计</el-button>
        <el-button @click="router.push('/ui-automation/suites')">回归套件</el-button>
        <el-button type="primary" @click="showCreateDialog = true">
          <el-icon><Plus /></el-icon>
          新建用例
        </el-button>
      </div>
    </div>

    <el-table v-loading="loading" :data="cases" stripe style="width: 100%" @row-click="handleRowClick">
      <el-table-column prop="name" label="用例名称" min-width="200">
        <template #default="{ row }">
          <span class="case-name">{{ row.name }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="statusTagType(row.status)" size="small">
            {{ statusLabel(row.status) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="priority" label="优先级" width="100">
        <template #default="{ row }">
          <el-tag :type="priorityTagType(row.priority)" size="small" effect="plain">
            {{ priorityLabel(row.priority) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="base_url" label="基础URL" min-width="220" show-overflow-tooltip>
        <template #default="{ row }">
          {{ row.base_url || '—' }}
        </template>
      </el-table-column>
      <el-table-column prop="updated_at" label="更新时间" width="180">
        <template #default="{ row }">
          {{ formatDate(row.updated_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="260" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click.stop="goToEditor(row.id)">编辑</el-button>
          <el-button size="small" type="primary" plain @click.stop="openRunHistory(row)">运行记录</el-button>
          <el-button size="small" type="danger" plain @click.stop="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pagination-wrapper">
      <el-pagination
        v-model:current-page="page"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next"
        @size-change="loadCases"
        @current-change="loadCases"
      />
    </div>

    <el-dialog v-model="showCreateDialog" title="新建 UI 用例" width="500px">
      <el-form :model="newCase" label-width="100px">
        <el-form-item label="用例名称" required>
          <el-input v-model="newCase.name" placeholder="请输入用例名称" maxlength="200" />
        </el-form-item>
        <el-form-item label="基础URL">
          <el-input v-model="newCase.base_url" placeholder="https://example.com" />
        </el-form-item>
        <el-form-item label="优先级">
          <el-select v-model="newCase.priority" style="width: 100%">
            <el-option label="低" value="low" />
            <el-option label="中" value="medium" />
            <el-option label="高" value="high" />
            <el-option label="紧急" value="critical" />
          </el-select>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="newCase.description" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" :loading="creating" @click="handleCreate">创建</el-button>
      </template>
    </el-dialog>

    <el-drawer v-model="showRunDrawer" title="运行记录" size="65%">
      <div class="run-history-drawer">
        <div class="drawer-header" v-if="runHistoryCase">
          <span class="drawer-title">{{ runHistoryCase.name }}</span>
          <el-button size="small" @click="loadRuns(runHistoryCase.id)">刷新</el-button>
        </div>

        <div class="run-layout">
          <div class="run-list-panel">
            <el-table
              v-loading="runsLoading"
              :data="runs"
              stripe
              highlight-current-row
              :current-row-key="selectedRun?.id"
              row-key="id"
              @row-click="selectRun"
            >
              
              <el-table-column prop="status" label="状态" width="100">
                <template #default="{ row }">
                  <el-tag :type="runStatusTagType(row.status)" size="small">{{ runStatusLabel(row.status) }}</el-tag>
                </template>
              </el-table-column>
              
              <el-table-column label="统计" min-width="150">
                <template #default="{ row }">
                  {{ row.passed_steps }}/{{ row.total_steps }} 通过，{{ row.failed_steps }} 失败
                </template>
              </el-table-column>
              <el-table-column prop="queued_at" label="开始时间" width="180">
                <template #default="{ row }">
                  {{ formatDate(row.started_at || row.queued_at) }}
                </template>
              </el-table-column>
            </el-table>

            <el-empty v-if="!runsLoading && !runs.length" description="暂无运行记录" />
          </div>

          <div class="run-detail-panel" v-loading="runDetailLoading">
            <template v-if="selectedRun">
              <div class="detail-actions">
                <el-button v-if="canCancelRun(selectedRun)" type="warning" plain :loading="cancellingRun" @click="cancelSelectedRun">取消运行</el-button>
                <el-button v-if="['failed','infra_error','timed_out','cancelled'].includes(selectedRun.status)" :loading="failureAnalysisLoading" @click="openFailureAnalysis">失败归因</el-button>
                <el-button v-if="['failed','infra_error','timed_out','cancelled'].includes(selectedRun.status)" type="danger" plain :loading="defectReportLoading" @click="openDefectReport">缺陷报告</el-button>
              </div>
              <el-card shadow="never" class="detail-summary-card">
                <div class="detail-summary-grid">
                  <div class="summary-item">
                    <span class="summary-label">Run ID</span>
                    <span class="summary-value">{{ selectedRun.id }}</span>
                  </div>
                  <div class="summary-item">
                    <span class="summary-label">状态</span>
                    <el-tag :type="runStatusTagType(selectedRun.status)" size="small">{{ runStatusLabel(selectedRun.status) }}</el-tag>
                  </div>
                  <div class="summary-item">
                    <span class="summary-label">版本</span>
                    <span class="summary-value">{{ selectedRun.case_version_id || '—' }}</span>
                  </div>
                  <div class="summary-item">
                    <span class="summary-label">触发方式</span>
                    <span class="summary-value">{{ selectedRun.trigger_type || '—' }}</span>
                  </div>
                  <div class="summary-item">
                    <span class="summary-label">开始时间</span>
                    <span class="summary-value">{{ formatDate(selectedRun.started_at || selectedRun.queued_at) }}</span>
                  </div>
                  <div class="summary-item">
                    <span class="summary-label">结束时间</span>
                    <span class="summary-value">{{ formatDate(selectedRun.finished_at) }}</span>
                  </div>
                  <div class="summary-item">
                    <span class="summary-label">步骤统计</span>
                    <span class="summary-value">{{ selectedRun.passed_steps }}/{{ selectedRun.total_steps }} 通过，{{ selectedRun.failed_steps }} 失败</span>
                  </div>
                  <div class="summary-item">
                    <span class="summary-label">产物数</span>
                    <span class="summary-value">{{ selectedRunArtifacts.length }}</span>
                  </div>
                  <div class="summary-item summary-item-full" v-if="selectedRun.error_summary || selectedRun.error_code">
                    <span class="summary-label">错误摘要</span>
                    <span class="summary-value error-text">{{ selectedRun.error_summary || selectedRun.error_code }}</span>
                  </div>
                </div>
              </el-card>

              <el-tabs v-model="activeRunTab" class="detail-tabs">
                <el-tab-pane label="步骤结果" name="steps">
                  <el-table :data="selectedRunStepResults" stripe size="small">
                    <el-table-column prop="step_id" label="步骤ID" min-width="120" show-overflow-tooltip />
                    <el-table-column prop="status" label="状态" width="100">
                      <template #default="{ row }">
                        <el-tag :type="stepStatusTagType(row.status)" size="small">{{ stepStatusLabel(row.status) }}</el-tag>
                      </template>
                    </el-table-column>
                    <el-table-column prop="duration_ms" label="耗时" width="90">
                      <template #default="{ row }">
                        {{ row.duration_ms ? `${row.duration_ms}ms` : '—' }}
                      </template>
                    </el-table-column>
                    <el-table-column prop="error_message" label="错误信息" min-width="220" show-overflow-tooltip>
                      <template #default="{ row }">
                        <span :class="{ 'error-text': row.error_message }">{{ row.error_message || '—' }}</span>
                      </template>
                    </el-table-column>
                  </el-table>
                  <el-empty v-if="!selectedRunStepResults.length" description="暂无步骤结果" />
                </el-tab-pane>

                <el-tab-pane label="产物" name="artifacts">
                  <el-table :data="selectedRunArtifacts" stripe size="small">
                    <el-table-column prop="type" label="类型" width="120" />
                    <el-table-column prop="filename" label="文件名" min-width="180" show-overflow-tooltip />
                    <el-table-column prop="size_bytes" label="大小" width="100">
                      <template #default="{ row }">
                        {{ formatBytes(row.size_bytes) }}
                      </template>
                    </el-table-column>
                    <el-table-column prop="storage_type" label="存储" width="90" />
                    <el-table-column prop="storage_path" label="服务端路径" min-width="220" show-overflow-tooltip /><el-table-column label="操作" width="90"><template #default="{ row }"><el-button size="small" text type="primary" @click="openArtifact(row)">{{ row.type === 'screenshot' ? '查看' : '保存' }}</el-button></template></el-table-column>
                  </el-table>
                  <el-empty v-if="!selectedRunArtifacts.length" description="暂无产物" />
                </el-tab-pane>
              </el-tabs>
            </template>

            <el-empty v-else description="请选择一条运行记录查看详情" />
          </div>
        </div>
      </div>
    </el-drawer>
    <el-dialog v-model="artifactPreviewVisible" :title="artifactPreviewName" width="80%">
      <div v-if="artifactPreviewData" class="annotation-canvas" @click="addArtifactAnnotation">
        <img :src="artifactPreviewData" alt="运行截图" />
        <button v-for="(annotation,index) in artifactAnnotations" :key="annotation.id || index" class="annotation-marker" type="button" :style="{left:`${annotation.x_percent}%`,top:`${annotation.y_percent}%`}" :title="annotation.note" @click.stop="removeArtifactAnnotation(index)">{{ index + 1 }}</button>
      </div>
      <div v-if="selectedArtifact?.artifact_manifest_id" class="annotation-toolbar"><span>{{ artifactAnnotations.length }} 个标注</span><el-button :loading="savingAnnotations" type="primary" @click="saveArtifactAnnotations">保存标注</el-button></div>
    </el-dialog>
    <el-dialog v-model="defectReportVisible" title="UI 自动化缺陷报告" width="900px">
      <template v-if="defectReport">
        <el-descriptions :column="2" border><el-descriptions-item label="运行编号">{{ defectReport.run_id }}</el-descriptions-item><el-descriptions-item label="状态">{{ runStatusLabel(defectReport.status) }}</el-descriptions-item><el-descriptions-item label="环境">{{ defectReport.environment?.name || '-' }}</el-descriptions-item><el-descriptions-item label="浏览器">{{ defectReport.reproduction?.browser }} {{ defectReport.reproduction?.browser_version || '' }}</el-descriptions-item></el-descriptions>
        <h4>失败步骤</h4><el-table :data="defectReport.failed_steps || []" size="small"><el-table-column prop="step_id" label="步骤" min-width="150" /><el-table-column prop="error_message" label="错误" min-width="360" show-overflow-tooltip /><el-table-column prop="duration_ms" label="耗时(ms)" width="100" /></el-table>
        <h4>事件时间线</h4><el-table :data="defectReport.timeline || []" size="small" max-height="260"><el-table-column prop="sequence" label="#" width="55" /><el-table-column prop="type" label="事件" min-width="180" /><el-table-column prop="level" label="级别" width="80" /><el-table-column label="时间" width="180"><template #default="{ row }">{{ formatDate(row.created_at) }}</template></el-table-column></el-table>
      </template>
    </el-dialog>
    <el-dialog v-model="failureAnalysisVisible" title="失败归因建议" width="760px">
      <template v-if="failureAnalysis">
        <el-alert title="该结果是辅助建议，需由测试工程师确认后才计入评估。" type="warning" :closable="false" show-icon />
        <el-descriptions :column="2" border class="analysis-summary">
          <el-descriptions-item label="建议类别">{{ failureCategoryLabel(failureAnalysis.category) }}</el-descriptions-item>
          <el-descriptions-item label="置信度">{{ formatPercent(failureAnalysis.confidence) }}</el-descriptions-item>
        </el-descriptions>
        <section class="analysis-section">
          <h4>判断证据</h4>
          <ul><li v-for="(item, index) in failureAnalysis.evidence || []" :key="`evidence-${index}`">{{ item }}</li></ul>
          <el-empty v-if="!(failureAnalysis.evidence || []).length" description="暂无充分证据" :image-size="48" />
        </section>
        <section class="analysis-section" v-if="(failureAnalysis.unknowns || []).length">
          <h4>待确认信息</h4>
          <ul><li v-for="(item, index) in failureAnalysis.unknowns" :key="`unknown-${index}`">{{ item }}</li></ul>
        </section>
        <section class="analysis-section" v-if="(failureAnalysis.next_actions || []).length">
          <h4>建议排查动作</h4>
          <ol><li v-for="(item, index) in failureAnalysis.next_actions" :key="`action-${index}`">{{ item }}</li></ol>
        </section>
        <el-divider content-position="left">人工复核</el-divider>
        <el-form label-width="100px">
          <el-form-item label="复核结果">
            <el-radio-group v-model="failureFeedback.accepted">
              <el-radio-button :label="true">归因正确</el-radio-button>
              <el-radio-button :label="false">需要纠正</el-radio-button>
            </el-radio-group>
          </el-form-item>
          <el-form-item v-if="failureFeedback.accepted === false" label="正确类别" required>
            <el-select v-model="failureFeedback.corrected_category" style="width: 100%">
              <el-option v-for="item in failureCategories" :key="item.value" :label="item.label" :value="item.value" />
            </el-select>
          </el-form-item>
          <el-form-item label="复核说明">
            <el-input v-model="failureFeedback.comment" type="textarea" :rows="3" maxlength="1000" show-word-limit />
          </el-form-item>
        </el-form>
      </template>
      <template #footer>
        <el-button @click="failureAnalysisVisible = false">关闭</el-button>
        <el-button type="primary" :loading="failureFeedbackSaving" @click="submitFailureFeedback">提交复核</el-button>
      </template>
    </el-dialog>
    <el-dialog v-model="aiMetricsVisible" title="AI 失败归因评估" width="680px">
      <div v-loading="aiMetricsLoading">
        <el-descriptions v-if="aiMetrics" :column="2" border>
          <el-descriptions-item label="已复核样本">{{ aiMetrics.total_feedback ?? 0 }}</el-descriptions-item>
          <el-descriptions-item label="确认正确">{{ aiMetrics.accepted_count ?? 0 }}</el-descriptions-item>
          <el-descriptions-item label="人工纠正">{{ aiMetrics.corrected_count ?? 0 }}</el-descriptions-item>
          <el-descriptions-item label="归因准确率">{{ formatPercent(aiMetrics.accuracy_rate) }}</el-descriptions-item>
          <el-descriptions-item label="人工纠正率">{{ formatPercent(aiMetrics.correction_rate) }}</el-descriptions-item>
        </el-descriptions>
        <el-empty v-if="!aiMetricsLoading && !aiMetrics" description="暂无评估数据" />
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onBeforeUnmount, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Plus } from '@element-plus/icons-vue'
import uiAutomationApi from '@/api/ui-automation'

const router = useRouter()
const loading = ref(false)
const cases = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const keyword = ref('')
const showCreateDialog = ref(false)
const creating = ref(false)
const showRunDrawer = ref(false)
const runsLoading = ref(false)
const runs = ref([])
const runHistoryCase = ref(null)
const selectedRun = ref(null)
const selectedRunStepResults = ref([])
const selectedRunArtifacts = ref([])
const runDetailLoading = ref(false)
const activeRunTab = ref('steps')
const cancellingRun = ref(false)
const artifactPreviewVisible = ref(false)
const artifactPreviewData = ref('')
const artifactPreviewName = ref('')
let artifactPreviewObjectUrl = ''
const selectedArtifact = ref(null)
const artifactAnnotations = ref([])
const savingAnnotations = ref(false)
const defectReportVisible = ref(false)
const defectReportLoading = ref(false)
const defectReport = ref(null)
const failureAnalysisVisible = ref(false)
const failureAnalysisLoading = ref(false)
const failureAnalysis = ref(null)
const failureFeedbackSaving = ref(false)
const failureFeedback = ref({ accepted: true, corrected_category: '', comment: '' })
const aiMetricsVisible = ref(false)
const aiMetricsLoading = ref(false)
const aiMetrics = ref(null)
const failureCategories = [
  { value: 'environment', label: '环境问题' },
  { value: 'data', label: '测试数据问题' },
  { value: 'product_defect', label: '产品缺陷' },
  { value: 'script', label: '自动化脚本问题' },
  { value: 'unknown', label: '暂时未知' },
]
const newCase = ref({
  name: '',
  base_url: '',
  priority: 'medium',
  description: '',
})

async function loadCases() {
  loading.value = true
  try {
    const data = await uiAutomationApi.listCases({
      page: page.value,
      page_size: pageSize.value,
      keyword: keyword.value || undefined,
    })
    cases.value = data.items || []
    total.value = data.total || 0
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    loading.value = false
  }
}

async function loadRuns(caseId) {
  runsLoading.value = true
  selectedRun.value = null
  selectedRunStepResults.value = []
  selectedRunArtifacts.value = []
  try {
    const data = await uiAutomationApi.listRuns({ case_id: caseId, page_size: 50 })
    runs.value = data.items || []
    if (runs.value.length) {
      await selectRun(runs.value[0])
    }
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    runsLoading.value = false
  }
}

async function selectRun(row) {
  if (!row?.id) return
  runDetailLoading.value = true
  activeRunTab.value = 'steps'
  try {
    const [run, stepResults, artifacts] = await Promise.all([
      uiAutomationApi.getRun(row.id),
      uiAutomationApi.listRunStepResults(row.id),
      uiAutomationApi.listRunArtifacts(row.id),
    ])
    selectedRun.value = run
    selectedRunStepResults.value = stepResults.items || []
    selectedRunArtifacts.value = artifacts.items || []
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    runDetailLoading.value = false
  }
}

function canCancelRun(run) {
  return ['queued', 'waiting_for_agent', 'assigned', 'starting', 'running'].includes(run?.status)
}

async function cancelSelectedRun() {
  if (!selectedRun.value?.id) return
  try {
    await ElMessageBox.confirm('将请求停止当前运行。已在执行的步骤会在桌面 Agent 收到指令后安全结束。', '取消运行', { type: 'warning' })
    cancellingRun.value = true
    const updated = await uiAutomationApi.cancelRun(selectedRun.value.id)
    selectedRun.value = updated
    const index = runs.value.findIndex(item => item.id === updated.id)
    if (index >= 0) runs.value.splice(index, 1, updated)
    ElMessage.success(updated.status === 'cancelled' ? '运行已取消' : '已向桌面 Agent 发送取消指令')
  } catch (error) {
    if (error !== 'cancel' && error !== 'close') ElMessage.error(error.message || '取消运行失败')
  } finally {
    cancellingRun.value = false
  }
}

async function openArtifact(artifact) {
  if (!selectedRun.value?.id) return
  try {
    const file = await uiAutomationApi.getRunArtifactContent(selectedRun.value.id, artifact.id)
    const blob = file instanceof Blob ? file : new Blob([file], { type: artifact.mime_type || 'application/octet-stream' })
    if (artifact.type === 'screenshot' || blob.type.startsWith('image/')) {
      if (artifactPreviewObjectUrl) URL.revokeObjectURL(artifactPreviewObjectUrl)
      artifactPreviewObjectUrl = URL.createObjectURL(blob)
      artifactPreviewName.value = artifact.filename
      artifactPreviewData.value = artifactPreviewObjectUrl
      selectedArtifact.value = artifact
      artifactAnnotations.value = []
      if (artifact.artifact_manifest_id) {
        const layer = await uiAutomationApi.getArtifactAnnotations(artifact.artifact_manifest_id)
        artifactAnnotations.value = layer.annotations || []
      }
      artifactPreviewVisible.value = true
      return
    }
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = artifact.filename
    link.click()
    setTimeout(() => URL.revokeObjectURL(url), 1000)
  } catch (error) {
    ElMessage.error(error.message || '读取运行产物失败')
  }
}
async function handleCreate() {
  if (!newCase.value.name.trim()) {
    ElMessage.warning('请输入用例名称')
    return
  }
  creating.value = true
  try {
    const created = await uiAutomationApi.createCase(newCase.value)
    ElMessage.success('创建成功')
    showCreateDialog.value = false
    newCase.value = { name: '', base_url: '', priority: 'medium', description: '' }
    await loadCases()
    router.push(`/ui-automation/cases/${created.id}`)
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    creating.value = false
  }
}

async function addArtifactAnnotation(event) {
  if (!selectedArtifact.value?.artifact_manifest_id || event.target?.tagName !== 'IMG') return
  const rect = event.currentTarget.getBoundingClientRect()
  const x = Math.max(0, Math.min(100, ((event.clientX - rect.left) / rect.width) * 100))
  const y = Math.max(0, Math.min(100, ((event.clientY - rect.top) / rect.height) * 100))
  try {
    const answer = await ElMessageBox.prompt('请输入标注说明', '添加截图标注', { inputPattern: /\S+/, inputErrorMessage: '请输入说明' })
    artifactAnnotations.value.push({ id: crypto.randomUUID(), x_percent: Number(x.toFixed(3)), y_percent: Number(y.toFixed(3)), note: answer.value.trim() })
  } catch {}
}

async function removeArtifactAnnotation(index) {
  try {
    await ElMessageBox.confirm(`删除标注 ${index + 1}？`, '删除标注', { type: 'warning' })
    artifactAnnotations.value.splice(index, 1)
  } catch {}
}

async function saveArtifactAnnotations() {
  if (!selectedArtifact.value?.artifact_manifest_id) return
  savingAnnotations.value = true
  try {
    await uiAutomationApi.saveArtifactAnnotations(selectedArtifact.value.artifact_manifest_id, artifactAnnotations.value)
    ElMessage.success('截图标注已保存')
  } catch (error) {
    ElMessage.error(error.message || '保存标注失败')
  } finally {
    savingAnnotations.value = false
  }
}

async function openDefectReport() {
  if (!selectedRun.value?.id) return
  defectReportLoading.value = true
  try {
    defectReport.value = await uiAutomationApi.getRunDefectReport(selectedRun.value.id)
    defectReportVisible.value = true
  } catch (error) {
    ElMessage.error(error.message || '生成缺陷报告失败')
  } finally {
    defectReportLoading.value = false
  }
}

async function openFailureAnalysis() {
  if (!selectedRun.value?.id) return
  failureAnalysisLoading.value = true
  try {
    failureAnalysis.value = await uiAutomationApi.analyzeFailure(selectedRun.value.id)
    failureFeedback.value = { accepted: true, corrected_category: '', comment: '' }
    failureAnalysisVisible.value = true
  } catch (error) {
    ElMessage.error(error.message || '失败归因生成失败')
  } finally {
    failureAnalysisLoading.value = false
  }
}

async function submitFailureFeedback() {
  const analysisId = failureAnalysis.value?.analysis_id || failureAnalysis.value?.id
  if (!analysisId) {
    ElMessage.error('归因记录缺少标识，无法提交复核')
    return
  }
  if (failureFeedback.value.accepted === false && !failureFeedback.value.corrected_category) {
    ElMessage.warning('请选择纠正后的失败类别')
    return
  }
  failureFeedbackSaving.value = true
  try {
    await uiAutomationApi.submitAiAnalysisFeedback(analysisId, {
      accepted: failureFeedback.value.accepted,
      corrected_category: failureFeedback.value.accepted ? null : failureFeedback.value.corrected_category,
      comment: failureFeedback.value.comment.trim() || null,
    })
    ElMessage.success('人工复核已记录')
    failureAnalysisVisible.value = false
  } catch (error) {
    ElMessage.error(error.message || '提交人工复核失败')
  } finally {
    failureFeedbackSaving.value = false
  }
}

async function openAiMetrics() {
  aiMetricsVisible.value = true
  aiMetricsLoading.value = true
  aiMetrics.value = null
  try {
    aiMetrics.value = await uiAutomationApi.getAiAnalysisMetrics({ analysis_type: 'failure_attribution' })
  } catch (error) {
    ElMessage.error(error.message || '读取 AI 评估指标失败')
  } finally {
    aiMetricsLoading.value = false
  }
}

watch(artifactPreviewVisible, visible => {
  if (!visible && artifactPreviewObjectUrl) {
    URL.revokeObjectURL(artifactPreviewObjectUrl)
    artifactPreviewObjectUrl = ''
    artifactPreviewData.value = ''
    selectedArtifact.value = null
    artifactAnnotations.value = []
  }
})

onBeforeUnmount(() => {
  if (artifactPreviewObjectUrl) URL.revokeObjectURL(artifactPreviewObjectUrl)
})

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(`确认删除用例 “${row.name}”？`, '提示', { type: 'warning' })
    await uiAutomationApi.deleteCase(row.id)
    ElMessage.success('已删除')
    await loadCases()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.message)
    }
  }
}

function openRunHistory(row) {
  runHistoryCase.value = row
  showRunDrawer.value = true
  loadRuns(row.id)
}

function goToEditor(caseId) {
  router.push(`/ui-automation/cases/${caseId}`)
}

function handleRowClick(row) {
  goToEditor(row.id)
}

function statusLabel(status) {
  const map = { draft: '草稿', active: '活跃', deprecated: '已废弃', archived: '已归档' }
  return map[status] || status
}

function statusTagType(status) {
  const map = { draft: 'info', active: 'success', deprecated: 'warning', archived: 'info' }
  return map[status] || 'info'
}

function priorityLabel(priority) {
  const map = { low: '低', medium: '中', high: '高', critical: '紧急' }
  return map[priority] || priority
}

function priorityTagType(priority) {
  const map = { low: 'info', medium: '', high: 'warning', critical: 'danger' }
  return map[priority] || ''
}

function runStatusLabel(status) {
  const map = { queued: '排队中', waiting_for_agent: '等待桌面 Agent', assigned: '已分配', starting: '启动中', running: '运行中', cancel_requested: '取消中', passed: '通过', failed: '失败', cancelled: '已取消', timed_out: '执行超时', infra_error: '基础设施异常', error: '错误', orphaned: '异常中断' }
  return map[status] || status
}

function runStatusTagType(status) {
  const map = { queued: 'info', waiting_for_agent: 'warning', assigned: 'info', starting: 'warning', running: 'warning', cancel_requested: 'warning', passed: 'success', failed: 'danger', cancelled: 'info', timed_out: 'danger', infra_error: 'danger', error: 'danger', orphaned: 'warning' }
  return map[status] || 'info'
}

function stepStatusLabel(status) {
  const map = { passed: '通过', failed: '失败', skipped: '跳过', cancelled: '已取消', pending: '进行中' }
  return map[status] || status
}

function stepStatusTagType(status) {
  const map = { passed: 'success', failed: 'danger', skipped: 'info', cancelled: 'warning', pending: 'warning' }
  return map[status] || 'info'
}

function formatDate(dt) {
  if (!dt) return '—'
  return new Date(dt).toLocaleString('zh-CN')
}

function formatBytes(size) {
  if (size === null || size === undefined) return '—'
  if (size < 1024) return `${size} B`
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`
  return `${(size / (1024 * 1024)).toFixed(1)} MB`
}

function failureCategoryLabel(category) {
  return failureCategories.find(item => item.value === category)?.label || category || '暂时未知'
}

function formatPercent(value) {
  const number = Number(value)
  if (!Number.isFinite(number)) return '—'
  return `${(number <= 1 ? number * 100 : number).toFixed(1)}%`
}

onMounted(() => {
  loadCases()
})
</script>

<style scoped lang="scss">
.ui-case-list {
  padding: 20px;

  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;

    .header-left {
      display: flex;
      align-items: center;
      gap: 12px;

      h2 {
        margin: 0;
        font-size: 20px;
      }
    }

    .header-right {
      display: flex;
      gap: 12px;
    }
  }

  .case-name {
    cursor: pointer;
    color: var(--el-color-primary);
    font-weight: 500;

    &:hover {
      text-decoration: underline;
    }
  }

  .pagination-wrapper {
    margin-top: 20px;
    display: flex;
    justify-content: flex-end;
  }

  .run-history-drawer {
    display: flex;
    flex-direction: column;
    gap: 16px;
    height: 100%;

    .drawer-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .drawer-title {
      font-size: 16px;
      font-weight: 600;
    }

    .run-layout {
      display: grid;
      grid-template-columns: minmax(0, 1.15fr) minmax(0, 1fr);
      gap: 16px;
      min-height: 0;
      flex: 1;
    }

    .run-list-panel,
    .run-detail-panel {
      min-height: 0;
    }

    .detail-summary-card {
      margin-bottom: 12px;
    }

    .detail-summary-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 12px 16px;
    }

    .summary-item {
      display: flex;
      flex-direction: column;
      gap: 4px;
    }

    .summary-item-full {
      grid-column: 1 / -1;
    }

    .summary-label {
      font-size: 12px;
      color: var(--el-text-color-secondary);
    }

    .summary-value {
      font-size: 13px;
      word-break: break-word;
    }

    .detail-tabs {
      height: calc(100% - 140px);
    }

    .error-text {
      color: var(--el-color-danger);
    }
  }
}

.detail-actions { display:flex; justify-content:flex-end; margin-bottom:8px; }
.annotation-canvas { position:relative; width:fit-content; max-width:100%; margin:0 auto; cursor:crosshair; }
.annotation-canvas img { display:block; max-width:100%; max-height:68vh; }
.annotation-marker { position:absolute; width:24px; height:24px; transform:translate(-50%,-50%); border:2px solid #fff; border-radius:50%; background:#c52b32; color:#fff; font-weight:700; cursor:pointer; box-shadow:0 1px 5px rgba(0,0,0,.35); }
.annotation-toolbar { display:flex; justify-content:flex-end; align-items:center; gap:12px; margin-top:12px; }
.analysis-summary { margin-top: 16px; }
.analysis-section { margin-top: 16px; }
.analysis-section h4 { margin: 0 0 8px; font-size: 14px; }
.analysis-section ul, .analysis-section ol { margin: 0; padding-left: 22px; line-height: 1.8; }
</style>



