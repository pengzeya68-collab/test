<template>
  <div class="upgrade-page">
    <header class="page-header">
      <div>
        <h1>评审与需求覆盖</h1>
        <p>用例评审流、需求追溯与覆盖矩阵、报告模板渲染。</p>
      </div>
      <div class="actions">
        <el-button @click="load">刷新</el-button>
        <el-button type="primary" @click="showReview = true">提交评审</el-button>
        <el-button @click="showReq = true">新建需求</el-button>
      </div>
    </header>

    <el-tabs v-model="tab">
      <el-tab-pane label="评审" name="reviews">
        <el-table :data="reviews" v-loading="loading" stripe>
          <el-table-column prop="id" label="ID" width="70" />
          <el-table-column prop="case_type" label="类型" width="90" />
          <el-table-column prop="case_id" label="用例" width="90" />
          <el-table-column prop="state" label="状态" width="140" />
          <el-table-column label="审批" width="120">
            <template #default="{ row }">{{ row.current_approvals || 0 }}/{{ row.required_approvals || 1 }}</template>
          </el-table-column>
          <el-table-column prop="submitted_at" label="提交时间" min-width="160" />
          <el-table-column label="操作" width="220" fixed="right">
            <template #default="{ row }">
              <el-button link type="success" @click="act(row, 'approve')">通过</el-button>
              <el-button link type="danger" @click="act(row, 'reject')">驳回</el-button>
              <el-button link @click="openComments(row)">评论</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
      <el-tab-pane label="需求" name="requirements">
        <el-table :data="requirements" stripe>
          <el-table-column prop="external_id" label="外部 ID" width="120" />
          <el-table-column prop="title" label="标题" min-width="200" />
          <el-table-column prop="priority" label="优先级" width="100" />
          <el-table-column prop="status" label="状态" width="100" />
          <el-table-column prop="sprint" label="迭代" width="120" />
          <el-table-column label="操作" width="120">
            <template #default="{ row }">
              <el-button link type="primary" @click="openLink(row)">关联用例</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
      <el-tab-pane label="覆盖矩阵" name="coverage">
        <el-row :gutter="12" class="stat-row" v-if="coverage">
          <el-col :span="6"><el-statistic title="需求数" :value="coverage.requirement_count || coverageStats.requirements" /></el-col>
          <el-col :span="6"><el-statistic title="已覆盖" :value="coverage.covered_count || coverageStats.covered" /></el-col>
          <el-col :span="6"><el-statistic title="未覆盖" :value="coverage.uncovered_count || coverageStats.uncovered" /></el-col>
          <el-col :span="6"><el-statistic title="覆盖率%" :value="Number(coverage.coverage_rate || coverageStats.rate || 0)" :precision="1" /></el-col>
        </el-row>
        <el-table :data="coverageRows" stripe max-height="420">
          <el-table-column prop="requirement_id" label="需求ID" width="90" />
          <el-table-column prop="external_id" label="外部ID" width="120" />
          <el-table-column prop="title" label="标题" min-width="180" show-overflow-tooltip />
          <el-table-column prop="case_count" label="关联用例" width="100" />
          <el-table-column prop="status" label="状态" width="100" />
          <el-table-column prop="priority" label="优先级" width="90" />
        </el-table>
        <el-collapse class="mt-12">
          <el-collapse-item title="原始 JSON">
            <pre class="result-box">{{ JSON.stringify(coverage, null, 2) }}</pre>
          </el-collapse-item>
        </el-collapse>
      </el-tab-pane>
      <el-tab-pane label="报告模板" name="reports">
        <div class="toolbar">
          <el-button size="small" type="primary" @click="saveTemplate">保存默认模板</el-button>
          <el-button size="small" @click="renderSample">预览渲染</el-button>
        </div>
        <el-table :data="templates" stripe>
          <el-table-column prop="id" label="ID" width="70" />
          <el-table-column prop="name" label="名称" min-width="160" />
          <el-table-column prop="company_name" label="公司" min-width="140" />
          <el-table-column prop="is_default" label="默认" width="80" />
        </el-table>
        <div v-if="reportHtml" class="report-preview" v-html="reportHtml" />
      </el-tab-pane>
    </el-tabs>

    <el-dialog v-model="showReview" title="提交用例评审" width="420px">
      <el-form label-width="100px">
        <el-form-item label="类型">
          <el-select v-model="reviewForm.case_type" style="width: 100%">
            <el-option label="UI" value="ui" />
            <el-option label="接口" value="api" />
          </el-select>
        </el-form-item>
        <el-form-item label="用例 ID"><el-input-number v-model="reviewForm.case_id" :min="1" style="width: 100%" /></el-form-item>
        <el-form-item label="所需审批"><el-input-number v-model="reviewForm.required_approvals" :min="1" :max="10" style="width: 100%" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showReview = false">取消</el-button>
        <el-button type="primary" @click="createReview">提交</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showReq" title="新建需求" width="480px">
      <el-form label-width="100px">
        <el-form-item label="标题"><el-input v-model="reqForm.title" /></el-form-item>
        <el-form-item label="外部 ID"><el-input v-model="reqForm.external_id" /></el-form-item>
        <el-form-item label="优先级"><el-input v-model="reqForm.priority" placeholder="P1" /></el-form-item>
        <el-form-item label="迭代"><el-input v-model="reqForm.sprint" /></el-form-item>
        <el-form-item label="描述"><el-input v-model="reqForm.description" type="textarea" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showReq = false">取消</el-button>
        <el-button type="primary" @click="createReq">创建</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showLink" title="关联用例" width="420px">
      <el-form label-width="100px">
        <el-form-item label="用例类型">
          <el-select v-model="linkForm.case_type" style="width: 100%">
            <el-option label="UI" value="ui" />
            <el-option label="接口" value="api" />
          </el-select>
        </el-form-item>
        <el-form-item label="用例 ID"><el-input-number v-model="linkForm.case_id" :min="1" style="width: 100%" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showLink = false">取消</el-button>
        <el-button type="primary" @click="linkCase">关联</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showComments" title="评审评论" width="560px">
      <el-timeline>
        <el-timeline-item v-for="c in comments" :key="c.id" :timestamp="c.created_at">{{ c.content }}</el-timeline-item>
      </el-timeline>
      <el-input v-model="commentText" type="textarea" :rows="3" placeholder="添加评论" />
      <template #footer>
        <el-button type="primary" @click="addComment">发送</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { storeToRefs } from 'pinia'
import { ElMessage } from 'element-plus'
import { featureUpgradesApi } from '@/api/feature-upgrades'
import { useProjectStore } from '@/stores/project'

const { projectId } = storeToRefs(useProjectStore())
const loading = ref(false)
const tab = ref('reviews')
const reviews = ref([])
const requirements = ref([])
const coverage = ref({})
const templates = ref([])
const comments = ref([])
const reportHtml = ref('')
const showReview = ref(false)
const showReq = ref(false)
const showLink = ref(false)
const showComments = ref(false)
const commentText = ref('')
const activeReviewId = ref(null)
const reviewForm = reactive({ case_type: 'ui', case_id: 1, required_approvals: 1 })
const reqForm = reactive({ title: '', external_id: '', priority: 'P2', sprint: '', description: '' })
const linkForm = reactive({ requirement_id: null, case_type: 'ui', case_id: 1, coverage_type: 'functional' })

const coverageRows = computed(() => {
  const data = coverage.value || {}
  if (Array.isArray(data.items)) return data.items
  if (Array.isArray(data.rows)) return data.rows
  if (Array.isArray(data.requirements)) return data.requirements
  if (Array.isArray(data)) return data
  return requirements.value.map((item) => ({
    requirement_id: item.id,
    external_id: item.external_id,
    title: item.title,
    case_count: item.case_count || item.linked_cases || 0,
    status: item.status,
    priority: item.priority,
  }))
})

const coverageStats = computed(() => {
  const rows = coverageRows.value
  const requirementsCount = rows.length || requirements.value.length || 0
  const covered = rows.filter((r) => Number(r.case_count || r.linked_count || 0) > 0).length
  const uncovered = Math.max(0, requirementsCount - covered)
  const rate = requirementsCount ? (covered / requirementsCount) * 100 : 0
  return { requirements: requirementsCount, covered, uncovered, rate }
})

async function load() {
  loading.value = true
  try {
    const [r, q, c, t] = await Promise.all([
      featureUpgradesApi.listReviews(projectId.value),
      featureUpgradesApi.listRequirements(projectId.value),
      featureUpgradesApi.requirementCoverage(projectId.value),
      featureUpgradesApi.listReportTemplates(projectId.value),
    ])
    reviews.value = r.items || []
    requirements.value = q.items || []
    coverage.value = c || {}
    templates.value = t.items || []
  } catch (error) {
    ElMessage.error(error.message || '加载失败')
  } finally {
    loading.value = false
  }
}

async function createReview() {
  await featureUpgradesApi.createReview({ project_id: projectId.value, ...reviewForm })
  showReview.value = false
  ElMessage.success('已提交评审')
  await load()
}

async function act(row, action) {
  await featureUpgradesApi.reviewAction(row.id, { action })
  ElMessage.success('已更新')
  await load()
}

async function openComments(row) {
  activeReviewId.value = row.id
  const res = await featureUpgradesApi.listReviewComments(row.id)
  comments.value = res.items || []
  showComments.value = true
}

async function addComment() {
  if (!commentText.value.trim()) return
  await featureUpgradesApi.addReviewComment(activeReviewId.value, { content: commentText.value })
  commentText.value = ''
  const res = await featureUpgradesApi.listReviewComments(activeReviewId.value)
  comments.value = res.items || []
}

async function createReq() {
  if (!reqForm.title.trim()) return ElMessage.warning('请填写标题')
  await featureUpgradesApi.createRequirement(projectId.value, { ...reqForm })
  showReq.value = false
  ElMessage.success('需求已创建')
  await load()
}

function openLink(row) {
  linkForm.requirement_id = row.id
  showLink.value = true
}

async function linkCase() {
  await featureUpgradesApi.linkRequirement({ ...linkForm })
  showLink.value = false
  ElMessage.success('已关联')
  await load()
}

async function saveTemplate() {
  await featureUpgradesApi.upsertReportTemplate(projectId.value, {
    name: 'Default',
    company_name: 'TestMaster',
    is_default: true,
    sections: ['summary', 'failures', 'coverage'],
  })
  ElMessage.success('模板已保存')
  await load()
}

async function renderSample() {
  const tpl = templates.value[0]
  if (!tpl) return ElMessage.warning('请先保存模板')
  const res = await featureUpgradesApi.renderReport({
    template_id: tpl.id,
    context: {
      title: '回归测试报告',
      passed: 10,
      failed: 1,
      duration: '12m',
      project: `project #${projectId.value}`,
    },
  })
  reportHtml.value = res.html || ''
}

onMounted(load)
</script>

<style scoped>
.upgrade-page { padding: 20px; display: flex; flex-direction: column; gap: 16px; }
.page-header { display: flex; justify-content: space-between; gap: 12px; }
.page-header h1 { margin: 0 0 6px; font-size: 22px; }
.page-header p { margin: 0; color: #64748b; }
.actions { display: flex; gap: 8px; flex-wrap: wrap; }
.toolbar { margin-bottom: 10px; display: flex; gap: 8px; }
.result-box { background: #0f172a; color: #e2e8f0; padding: 12px; border-radius: 8px; overflow: auto; max-height: 480px; }
.report-preview { margin-top: 12px; border: 1px solid #e2e8f0; padding: 16px; border-radius: 8px; background: #fff; }
.stat-row { margin-bottom: 12px; }
.mt-12 { margin-top: 12px; }
</style>
