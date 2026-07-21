<template>
  <div class="requirement-design">
    <header class="page-header">
      <div class="title-row"><el-button text :icon="ArrowLeft" @click="router.push('/ui-automation/cases')">UI 用例</el-button><h1>需求测试设计</h1></div>
      <el-tag v-if="traceabilityId" effect="plain">{{ traceabilityId }}</el-tag>
    </header>

    <section class="input-band">
      <el-form label-position="top">
        <div class="meta-row">
          <el-form-item label="需求追踪编号"><el-input v-model="traceabilityInput" maxlength="100" placeholder="可留空自动生成" /></el-form-item>
          <el-form-item label="业务上下文"><el-input v-model="context" maxlength="4000" placeholder="项目、角色、环境" /></el-form-item>
        </div>
        <el-form-item label="需求内容"><el-input v-model="requirementText" type="textarea" :rows="7" maxlength="12000" show-word-limit /></el-form-item>
        <div class="actions"><el-button type="primary" :loading="generatingPoints" :disabled="requirementText.trim().length < 4" @click="generatePoints">生成测试点</el-button></div>
      </el-form>
    </section>

    <section v-if="testPoints.length" class="points-band">
      <div class="section-heading"><h2>测试点</h2><el-button type="primary" :loading="generatingDrafts" :disabled="!selectedPointIds.length" @click="generateDrafts">生成用例草稿</el-button></div>
      <div class="point-list">
        <article v-for="point in testPoints" :key="point.id" class="point-row">
          <el-checkbox v-model="point.selected" :aria-label="`选择 ${point.id}`" />
          <div class="point-content">
            <span class="point-id">{{ point.id }}</span>
            <el-input v-model="point.title" maxlength="200" />
            <el-input v-model="point.source_requirement" type="textarea" :rows="2" maxlength="1000" />
            <div class="point-meta"><el-tag v-for="item in point.test_design" :key="item" size="small" effect="plain">{{ item }}</el-tag></div>
          </div>
        </article>
      </div>
    </section>

    <section v-if="caseDrafts.length" class="drafts-band">
      <div class="section-heading"><h2>用例草稿</h2><span>{{ caseDrafts.length }} 项</span></div>
      <el-table :data="caseDrafts" row-key="source_test_point_id" max-height="560">
        <el-table-column prop="source_test_point_id" label="来源测试点" min-width="210" />
        <el-table-column prop="name" label="用例名称" min-width="260" />
        <el-table-column prop="description" label="需求来源" min-width="300" show-overflow-tooltip />
        <el-table-column label="待补充" min-width="240"><template #default="{ row }">{{ row.missing_information.join('；') }}</template></el-table-column>
        <el-table-column label="状态" width="110"><template #default><el-tag type="warning" size="small">待人工确认</el-tag></template></el-table-column>
      </el-table>
    </section>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft } from '@element-plus/icons-vue'
import uiAutomationApi from '@/api/ui-automation'

const router = useRouter()
const requirementText = ref('')
const traceabilityInput = ref('')
const traceabilityId = ref('')
const context = ref('')
const analysisId = ref('')
const testPoints = ref([])
const caseDrafts = ref([])
const generatingPoints = ref(false)
const generatingDrafts = ref(false)

const selectedPointIds = computed(() => testPoints.value.filter(point => point.selected).map(point => point.id))

async function generatePoints () {
  generatingPoints.value = true
  try {
    const response = await uiAutomationApi.generateRequirementTestPoints({
      requirement_text: requirementText.value,
      traceability_id: traceabilityInput.value || null,
      context: context.value || null
    })
    analysisId.value = response.analysis_id
    traceabilityId.value = response.traceability_id
    testPoints.value = (response.test_points || []).map(point => ({ ...point, selected: true }))
    caseDrafts.value = []
  } catch (error) {
    ElMessage.error(error?.message || '测试点生成失败')
  } finally {
    generatingPoints.value = false
  }
}

async function generateDrafts () {
  generatingDrafts.value = true
  try {
    const selected = testPoints.value.filter(point => point.selected)
    const response = await uiAutomationApi.generateRequirementCaseDrafts({
      analysis_id: analysisId.value,
      point_ids: selected.map(point => point.id),
      point_overrides: selected.map(point => ({ id: point.id, title: point.title, source_requirement: point.source_requirement }))
    })
    caseDrafts.value = response.case_drafts || []
  } catch (error) {
    ElMessage.error(error?.message || '用例草稿生成失败')
  } finally {
    generatingDrafts.value = false
  }
}
</script>

<style scoped>
.requirement-design{max-width:1400px;margin:0 auto;padding:20px;color:var(--tm-text-primary)}
.page-header,.title-row,.section-heading,.actions,.point-meta{display:flex;align-items:center}.page-header{justify-content:space-between;padding-bottom:16px;border-bottom:1px solid var(--tm-border-light)}.title-row{gap:10px}.title-row h1,.section-heading h2{margin:0;font-size:22px}.input-band,.points-band,.drafts-band{padding:20px 0;border-bottom:1px solid var(--tm-border-light)}.meta-row{display:grid;grid-template-columns:minmax(240px,.55fr) minmax(320px,1.45fr);gap:18px}.actions{justify-content:flex-end}.section-heading{justify-content:space-between;margin-bottom:14px}.section-heading h2{font-size:17px}.section-heading span{font-size:13px;color:var(--tm-text-secondary)}.point-list{display:flex;flex-direction:column;border-top:1px solid var(--tm-border-light)}.point-row{display:grid;grid-template-columns:32px 1fr;gap:8px;padding:14px 4px;border-bottom:1px solid var(--tm-border-light)}.point-content{display:grid;grid-template-columns:minmax(180px,.5fr) minmax(260px,1fr) minmax(300px,1.4fr);gap:10px;align-items:start}.point-id{font-family:Consolas,monospace;font-size:12px;color:var(--tm-text-secondary);padding-top:9px}.point-meta{grid-column:2/-1;gap:6px;flex-wrap:wrap}@media(max-width:900px){.requirement-design{padding:14px}.meta-row,.point-content{grid-template-columns:1fr}.point-meta{grid-column:auto}.page-header{align-items:flex-start;gap:10px;flex-direction:column}}
</style>
