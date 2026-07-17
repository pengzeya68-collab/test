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
      <img v-if="artifactPreviewData" :src="artifactPreviewData" alt="运行截图" style="display:block;max-width:100%;max-height:72vh;margin:0 auto" />
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
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
const artifactPreviewVisible = ref(false)
const artifactPreviewData = ref('')
const artifactPreviewName = ref('')
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

async function openArtifact(artifact) {
  if (!selectedRun.value?.id) return
  try {
    const file = await uiAutomationApi.getRunArtifactContent(selectedRun.value.id, artifact.id)
    if (artifact.type === 'screenshot' || file.mime_type?.startsWith('image/')) {
      artifactPreviewName.value = file.filename
      artifactPreviewData.value = `data:${file.mime_type};base64,${file.content_base64}`
      artifactPreviewVisible.value = true
      return
    }
    const bytes = Uint8Array.from(atob(file.content_base64), ch => ch.charCodeAt(0))
    const url = URL.createObjectURL(new Blob([bytes], { type: file.mime_type }))
    const link = document.createElement('a')
    link.href = url
    link.download = file.filename
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
  const map = { queued: '排队中', assigned: '已分配', starting: '启动中', running: '运行中', passed: '通过', failed: '失败', cancelled: '已取消', error: '错误', orphaned: '孤儿任务' }
  return map[status] || status
}

function runStatusTagType(status) {
  const map = { queued: 'info', assigned: 'info', starting: 'warning', running: 'warning', passed: 'success', failed: 'danger', cancelled: 'info', error: 'danger', orphaned: 'warning' }
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
</style>



