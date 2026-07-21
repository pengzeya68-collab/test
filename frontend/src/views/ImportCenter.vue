<template>
  <div class="import-center">
    <header class="page-header">
      <div>
        <el-button text :icon="ArrowLeft" @click="router.back()">返回</el-button>
        <h1>导入中心</h1>
      </div>
      <el-radio-group v-model="sourceMode" @change="resetSelection">
        <el-radio-button label="capture">浏览器抓包</el-radio-button>
        <el-radio-button label="file">文件 / cURL</el-radio-button>
      </el-radio-group>
    </header>

    <section v-if="sourceMode === 'capture'" class="content-band">
      <div class="control-row">
        <el-select v-model="selectedCaptureId" filterable placeholder="选择已完成的抓包会话" :loading="loadingSessions" style="width: min(680px, 100%)">
          <el-option v-for="item in captureSessions" :key="item.id" :label="captureLabel(item)" :value="item.id" :disabled="item.status !== 'completed'" />
        </el-select>
        <el-button :icon="Refresh" :loading="loadingSessions" @click="loadCaptureSessions">刷新</el-button>
        <el-button :icon="Download" :disabled="!selectedCaptureId" :loading="exportingCapture" @click="exportCapture">导出已脱敏 HAR</el-button>
      </div>

      <el-table ref="captureTable" :data="captureCandidates" row-key="id" @selection-change="onCaptureSelectionChange" v-loading="loadingCandidates" max-height="420">
        <el-table-column type="selection" width="48" reserve-selection />
        <el-table-column prop="method" label="方法" width="90"><template #default="{ row }"><el-tag size="small">{{ row.method }}</el-tag></template></el-table-column>
        <el-table-column prop="name" label="接口" min-width="200" />
        <el-table-column prop="url" label="URL" min-width="360" show-overflow-tooltip />
        <el-table-column prop="response_status" label="状态" width="90" />
        <el-table-column prop="timing_ms" label="耗时" width="100"><template #default="{ row }">{{ row.timing_ms == null ? '-' : `${row.timing_ms} ms` }}</template></el-table-column>
      </el-table>

      <div class="conversion-grid">
        <el-form label-position="top" class="conversion-form">
          <el-form-item label="目标接口分组 ID"><el-input-number v-model="targetGroupId" :min="1" controls-position="right" placeholder="可留空" /></el-form-item>
          <el-form-item label="冲突处理"><el-radio-group v-model="conflictStrategy"><el-radio label="skip">跳过相同请求</el-radio><el-radio label="copy">创建副本</el-radio><el-radio label="update">更新已有用例</el-radio></el-radio-group></el-form-item>
          <el-form-item><el-checkbox v-model="createScenario">同时生成接口场景</el-checkbox></el-form-item>
          <el-form-item v-if="createScenario" label="场景名称"><el-input v-model="scenarioName" maxlength="200" show-word-limit /></el-form-item>
          <el-form-item v-if="createScenario"><el-checkbox v-model="dependencyReviewConfirmed">我已确认以下调用顺序和变量依赖</el-checkbox></el-form-item>
        </el-form>
        <div class="mapping-area">
          <div class="mapping-title"><strong>变量映射</strong><el-button text type="primary" :icon="Plus" @click="addMapping">添加</el-button></div>
          <div v-if="!variableMappings.length" class="empty-mapping">未配置变量映射</div>
          <div v-for="(mapping, index) in variableMappings" :key="index" class="mapping-row">
            <el-select v-model="mapping.source_exchange_id" placeholder="来源请求"><el-option v-for="row in captureSelectedRows" :key="row.id" :label="row.name" :value="row.id" /></el-select>
            <el-input v-model="mapping.variable_name" placeholder="变量名" />
            <el-input v-model="mapping.json_path" placeholder="JSONPath，例如 $.data.token" />
            <el-select v-model="mapping.target_exchange_id" placeholder="目标请求"><el-option v-for="row in captureSelectedRows" :key="row.id" :label="row.name" :value="row.id" /></el-select>
            <el-select v-model="mapping.location"><el-option label="请求头" value="headers.Authorization" /><el-option label="查询参数" value="params.id" /><el-option label="JSON 请求体" value="payload.id" /></el-select>
            <el-button text type="danger" :icon="Delete" @click="variableMappings.splice(index, 1)" />
          </div>
        </div>
      </div>
      <section v-if="createScenario && captureSelectedRows.length" class="dependency-preview">
        <div class="mapping-title"><strong>场景依赖预览</strong><span class="assertion-hint">变量只能从前序请求传递到后续请求</span></div>
        <ol>
          <li v-for="(row, index) in captureSelectedRows" :key="row.id"><el-tag size="small">{{ index + 1 }}</el-tag> {{ row.method }} {{ row.name }} <span v-if="dependencySources(row.id).length" class="dependency-source">依赖：{{ dependencySources(row.id).join('、') }}</span><span v-else class="dependency-source">无显式变量依赖</span></li>
        </ol>
      </section>
      <section v-if="captureSelectedRows.length" class="assertion-area">
        <div class="mapping-title"><strong>请求断言</strong><span class="assertion-hint">在生成前确认每个接口的成功标准</span></div>
        <el-collapse>
          <el-collapse-item v-for="row in captureSelectedRows" :key="row.id" :name="row.id">
            <template #title><span>{{ row.method }} {{ row.name }} <el-tag size="small" effect="plain">{{ captureAssertions[row.id]?.length || 0 }} 条断言</el-tag></span></template>
            <div v-for="(rule, index) in captureAssertions[row.id]" :key="index" class="assertion-row">
              <el-select v-model="rule.field" aria-label="断言对象" @change="normalizeAssertionRule(rule)">
                <el-option label="状态码" value="status_code" />
                <el-option label="响应 JSONPath" value="json_body" />
                <el-option label="JSON Schema" value="json_schema" />
                <el-option label="响应耗时（毫秒）" value="response_time" />
              </el-select>
              <el-input v-if="rule.field === 'json_body'" v-model="rule.expression" placeholder="JSONPath，例如 $.data.code" aria-label="JSONPath" />
              <el-select v-model="rule.operator" aria-label="比较方式">
                <el-option label="等于" value="equals" />
                <el-option label="不等于" value="not_equals" />
                <el-option label="包含" value="contains" />
                <el-option label="存在" value="json_exists" />
                <el-option label="大于等于" value="gte" />
                <el-option label="小于等于" value="lte" />
                <el-option v-if="rule.field === 'json_schema'" label="符合 Schema" value="matches" />
              </el-select>
              <el-input v-if="rule.operator !== 'json_exists'" v-model="rule.expected" :type="rule.field === 'json_schema' ? 'textarea' : 'text'" :rows="rule.field === 'json_schema' ? 2 : 1" :placeholder="rule.field === 'json_schema' ? '输入 JSON Schema' : '期望值'" aria-label="期望值" />
              <el-button text type="danger" :icon="Delete" aria-label="删除断言" @click="captureAssertions[row.id].splice(index, 1)" />
            </div>
            <el-button text type="primary" :icon="Plus" @click="addAssertion(row.id)">添加断言</el-button>
          </el-collapse-item>
        </el-collapse>
      </section>
      <div class="action-row"><el-button type="primary" :icon="Promotion" :disabled="!captureSelectedRows.length" :loading="converting" @click="convertCapture">生成接口用例{{ createScenario ? '与场景' : '' }}</el-button></div>
    </section>

    <section v-else class="content-band">
      <div class="control-row">
        <el-select v-model="fileSourceType" style="width: 190px" aria-label="导入来源类型">
          <el-option label="自动识别" value="auto" />
          <el-option label="Postman Collection v2.1" value="postman" />
          <el-option label="OpenAPI 3.x" value="openapi" />
          <el-option label="Swagger 2.0" value="swagger" />
          <el-option label="HAR 1.2" value="har" />
          <el-option label="Apipost 导出" value="apipost" />
          <el-option label="cURL 命令" value="curl" />
        </el-select>
        <el-upload v-if="fileSourceType !== 'curl'" :auto-upload="false" :show-file-list="true" accept=".har,.json,.yaml,.yml,.txt,application/json,text/plain" :limit="1" :on-change="file => importFile = file.raw" :on-remove="resetImportFile">
          <el-button :icon="Upload">选择导入文件</el-button>
        </el-upload>
        <el-button type="primary" :loading="loadingImport" @click="previewImport">解析预览</el-button>
      </div>
      <el-input v-if="fileSourceType === 'curl'" v-model="curlText" type="textarea" :rows="5" resize="vertical" placeholder="粘贴单个 cURL 请求命令" class="curl-input" />
      <el-table ref="importTable" :data="importCandidates" row-key="id" @selection-change="rows => importSelectedRows = rows" v-loading="loadingImport" max-height="420">
        <el-table-column type="selection" width="48" reserve-selection />
        <el-table-column prop="method" label="方法" width="90"><template #default="{ row }"><el-tag size="small">{{ row.method }}</el-tag></template></el-table-column>
        <el-table-column prop="source_type" label="来源" width="115"><template #default="{ row }"><el-tag size="small" effect="plain">{{ sourceLabel(row.source_type) }}</el-tag></template></el-table-column>
        <el-table-column prop="name" label="接口" min-width="220" />
        <el-table-column prop="url" label="URL" min-width="400" show-overflow-tooltip />
        <el-table-column prop="response_status" label="状态" width="90" />
        <el-table-column label="冲突" width="110"><template #default="{ row }"><el-tag v-if="row.conflict_count" type="warning" size="small">{{ row.conflict_count }} 个</el-tag><span v-else>-</span></template></el-table-column>
      </el-table>
      <div class="action-row">
        <el-input-number v-model="targetGroupId" :min="1" controls-position="right" placeholder="目标接口分组 ID（可选）" />
        <el-radio-group v-model="conflictStrategy"><el-radio label="skip">跳过结构相同请求</el-radio><el-radio label="copy">创建副本</el-radio><el-radio label="update">更新已有用例</el-radio></el-radio-group>
        <el-button type="primary" :disabled="!importSelectedRows.length" :loading="committingImport" @click="commitImport">导入选中接口</el-button>
      </div>
    </section>

    <el-result v-if="result" icon="success" title="导入完成" :sub-title="importResultSummary">
      <template #extra><el-button v-if="result.scenario_id && result.requires_preview" type="warning" :loading="previewingScenario" @click="previewScenario">预览并验证场景</el-button><el-button v-if="result.scenario_id" type="primary" @click="openScenario">打开接口场景</el-button><el-button @click="router.push('/auto-test?tab=interfaces')">打开接口库</el-button></template>
    </el-result>
    <el-alert v-if="previewStatus" :type="previewStatus === 'passed' ? 'success' : 'error'" :title="previewStatus === 'passed' ? '预览通过，场景已启用' : '预览未通过，场景保持停用'" show-icon class="preview-alert" />
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, Delete, Download, Plus, Promotion, Refresh, Upload } from '@element-plus/icons-vue'
import autoTestRequest from '@/utils/autoTestRequest'

const route = useRoute()
const router = useRouter()
const sourceMode = ref('capture')
const captureSessions = ref([])
const selectedCaptureId = ref(route.query.captureId || '')
const captureCandidates = ref([])
const captureSelectedRows = ref([])
const captureTable = ref(null)
const loadingSessions = ref(false)
const loadingCandidates = ref(false)
const exportingCapture = ref(false)
const targetGroupId = ref(null)
const conflictStrategy = ref('skip')
const createScenario = ref(true)
const scenarioName = ref('')
const dependencyReviewConfirmed = ref(false)
const variableMappings = ref([])
const captureAssertions = ref({})
const converting = ref(false)
const result = ref(null)
const importFile = ref(null)
const fileSourceType = ref('auto')
const curlText = ref('')
const importCandidates = ref([])
const importSelectedRows = ref([])
const importTable = ref(null)
const loadingImport = ref(false)
const committingImport = ref(false)
const previewingScenario = ref(false)
const previewStatus = ref('')

const captureLabel = item => `${item.source_url || '未命名地址'} · ${item.status === 'completed' ? '已完成' : '采集中'} · ${new Date(item.started_at).toLocaleString('zh-CN')}`

function resetSelection () {
  result.value = null
}

const importResultSummary = computed(() => `新建 ${result.value?.imported_count || 0} 个，更新 ${result.value?.updated_count || 0} 个，跳过 ${result.value?.skipped_count || 0} 个接口用例`)

function resetImportFile () {
  importFile.value = null
  importCandidates.value = []
  importSelectedRows.value = []
}

function sourceLabel (type) {
  return ({ har: 'HAR', postman: 'Postman', openapi: 'OpenAPI', swagger: 'Swagger', curl: 'cURL', apipost: 'Apipost' })[type] || type || '-'
}

function sourceFile () {
  if (fileSourceType.value !== 'curl') return importFile.value
  if (!curlText.value.trim()) return null
  return new File([curlText.value], 'request.curl', { type: 'text/plain' })
}

async function loadCaptureSessions () {
  loadingSessions.value = true
  try {
    const response = await autoTestRequest.get('/auto-test/import/captures')
    captureSessions.value = response.captures || []
    if (!selectedCaptureId.value) selectedCaptureId.value = captureSessions.value.find(item => item.status === 'completed')?.id || ''
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '加载抓包会话失败')
  } finally {
    loadingSessions.value = false
  }
}

async function loadCaptureCandidates () {
  if (!selectedCaptureId.value) { captureCandidates.value = []; return }
  loadingCandidates.value = true
  try {
    const response = await autoTestRequest.get(`/auto-test/import/captures/${selectedCaptureId.value}`)
    captureCandidates.value = response.candidates || []
    captureAssertions.value = Object.fromEntries(captureCandidates.value.map(row => [row.id, structuredClone(row.assert_rules || [])]))
    captureSelectedRows.value = captureCandidates.value.filter(item => item.selected)
    scenarioName.value = scenarioName.value || `抓包场景 ${selectedCaptureId.value.slice(0, 8)}`
    await nextTick()
    captureSelectedRows.value.forEach(row => captureTable.value?.toggleRowSelection(row, true))
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '加载抓包候选失败')
  } finally {
    loadingCandidates.value = false
  }
}

async function exportCapture () {
  if (!selectedCaptureId.value) return
  exportingCapture.value = true
  try {
    const blob = await autoTestRequest.get(`/auto-test/import/captures/${selectedCaptureId.value}/export`, { responseType: 'blob' })
    const href = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = href
    link.download = `capture-${selectedCaptureId.value}.har`
    link.click()
    URL.revokeObjectURL(href)
    ElMessage.success('已导出脱敏 HAR 文件')
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '导出抓包失败')
  } finally {
    exportingCapture.value = false
  }
}

function addMapping () {
  dependencyReviewConfirmed.value = false
  variableMappings.value.push({ source_exchange_id: null, variable_name: '', json_path: '$.', target_exchange_id: null, location: 'headers.Authorization' })
}

function onCaptureSelectionChange (rows) {
  captureSelectedRows.value = rows
  dependencyReviewConfirmed.value = false
}

function dependencySources (targetExchangeId) {
  return variableMappings.value
    .filter(item => item.target_exchange_id === targetExchangeId && item.variable_name)
    .map(item => item.variable_name)
}

function buildMappings () {
  return variableMappings.value.map(item => ({
    source_exchange_id: item.source_exchange_id,
    variable_name: item.variable_name,
    json_path: item.json_path,
    targets: [{ exchange_id: item.target_exchange_id, location: item.location }]
  }))
}

function addAssertion (exchangeId) {
  captureAssertions.value[exchangeId].push({ field: 'status_code', operator: 'equals', expected: 200 })
}

function normalizeAssertionRule (rule) {
  if (rule.field === 'json_schema') rule.operator = 'matches'
  if (rule.field === 'json_body' && !rule.expression) rule.expression = '$.'
  if (rule.operator === 'json_exists') rule.expected = ''
}

function buildCandidateOverrides () {
  return captureSelectedRows.value.map(row => ({ exchange_id: row.id, assert_rules: captureAssertions.value[row.id] || [] }))
}

async function convertCapture () {
  if (!selectedCaptureId.value || !captureSelectedRows.value.length) return
  if (createScenario.value && !dependencyReviewConfirmed.value) {
    ElMessage.warning('请确认场景调用顺序和变量依赖后再生成')
    return
  }
  if (conflictStrategy.value === 'update') {
    try {
      await ElMessageBox.confirm(
        '将覆盖当前账号下与选中抓包请求完全匹配的用例内容。前后置脚本、执行策略和版本记录会保留，是否继续？',
        '确认更新已有用例',
        { confirmButtonText: '确认更新', cancelButtonText: '取消', type: 'warning' }
      )
    } catch {
      return
    }
  }
  converting.value = true
  try {
    const response = await autoTestRequest.post(`/auto-test/import/captures/${selectedCaptureId.value}/convert`, {
      exchange_ids: captureSelectedRows.value.map(item => item.id),
      target_group_id: targetGroupId.value || null,
      conflict_strategy: conflictStrategy.value,
      confirm_update: conflictStrategy.value === 'update',
      create_scenario: createScenario.value,
      confirm_dependency_review: !createScenario.value || dependencyReviewConfirmed.value,
      scenario_name: scenarioName.value,
      variable_mappings: buildMappings(),
      candidate_overrides: buildCandidateOverrides()
    })
    result.value = response
    previewStatus.value = ''
    ElMessage.success('接口资产已生成，请先执行预览验证场景')
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '生成接口资产失败')
  } finally {
    converting.value = false
  }
}

async function previewScenario () {
  if (!selectedCaptureId.value || !result.value?.scenario_id) return
  previewingScenario.value = true
  try {
    const response = await autoTestRequest.post(`/auto-test/import/captures/${selectedCaptureId.value}/preview`, { scenario_id: result.value.scenario_id, env_id: null })
    previewStatus.value = response.status
    result.value = { ...result.value, preview_status: response.status }
    ElMessage[response.status === 'passed' ? 'success' : 'warning'](response.status === 'passed' ? '预览通过，场景已启用' : '预览未通过，请修正接口变量或断言后重试')
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '场景预览失败')
  } finally {
    previewingScenario.value = false
  }
}

async function previewImport () {
  const file = sourceFile()
  if (!file) { ElMessage.warning(fileSourceType.value === 'curl' ? '请输入 cURL 命令' : '请选择导入文件'); return }
  loadingImport.value = true
  try {
    const form = new FormData()
    form.append('file', file)
    form.append('source_type', fileSourceType.value)
    const response = await autoTestRequest.post('/auto-test/import/preview', form, { headers: { 'Content-Type': 'multipart/form-data' } })
    importCandidates.value = response.candidates || []
    importSelectedRows.value = []
    await nextTick()
    importCandidates.value.forEach(row => importTable.value?.toggleRowSelection(row, true))
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '导入文件解析失败')
  } finally {
    loadingImport.value = false
  }
}

async function commitImport () {
  const file = sourceFile()
  if (!file || !importSelectedRows.value.length) return
  committingImport.value = true
  try {
    const form = new FormData()
    form.append('file', file)
    form.append('source_type', fileSourceType.value)
    form.append('selected_ids', JSON.stringify(importSelectedRows.value.map(item => item.id)))
    form.append('conflict_strategy', conflictStrategy.value)
    if (targetGroupId.value) form.append('target_group_id', String(targetGroupId.value))
      result.value = await autoTestRequest.post('/auto-test/import/commit', form, { headers: { 'Content-Type': 'multipart/form-data' } })
      previewStatus.value = ''
    ElMessage.success('接口资产已导入')
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '接口导入失败')
  } finally {
    committingImport.value = false
  }
}

function openScenario () {
  router.push({ path: '/auto-test', query: { tab: 'scenarios', scenarioId: String(result.value.scenario_id) } })
}

watch(selectedCaptureId, loadCaptureCandidates)
onMounted(loadCaptureSessions)
</script>

<style scoped>
.import-center{padding:20px;max-width:1440px;margin:0 auto;color:var(--tm-text-primary)}
.page-header,.control-row,.action-row,.mapping-title{display:flex;align-items:center;gap:12px}.page-header{justify-content:space-between;border-bottom:1px solid var(--tm-border-light);padding-bottom:16px}.page-header h1{font-size:22px;margin:0}.page-header>div{display:flex;align-items:center;gap:10px}.content-band{padding:20px 0;border-bottom:1px solid var(--tm-border-light)}.control-row{margin-bottom:16px;flex-wrap:wrap}.conversion-grid{display:grid;grid-template-columns:minmax(280px,.75fr) minmax(520px,1.5fr);gap:22px;padding-top:18px}.conversion-form{padding-right:22px;border-right:1px solid var(--tm-border-light)}.mapping-title{justify-content:space-between;margin-bottom:10px}.mapping-row{display:grid;grid-template-columns:1.2fr .9fr 1.3fr 1.2fr 1fr 34px;gap:8px;align-items:center;margin-bottom:8px}.assertion-area{padding-top:20px}.assertion-hint{color:var(--tm-text-secondary);font-size:13px}.assertion-row{display:grid;grid-template-columns:180px minmax(180px,1fr) 160px minmax(180px,1fr) 34px;gap:8px;align-items:center;margin-bottom:8px}.empty-mapping{padding:20px 0;color:var(--tm-text-secondary);font-size:13px}.action-row{justify-content:flex-end;padding-top:16px;flex-wrap:wrap}.curl-input{margin-bottom:16px}.preview-alert{margin-top:18px}@media(max-width:960px){.page-header{align-items:flex-start;flex-direction:column}.conversion-grid{grid-template-columns:1fr}.conversion-form{border-right:0;padding-right:0}.mapping-row,.assertion-row{grid-template-columns:1fr 1fr}.import-center{padding:14px}}
.dependency-preview{padding-top:20px}.dependency-preview ol{margin:0;padding:0;list-style:none;display:grid;gap:8px}.dependency-preview li{display:flex;gap:8px;align-items:center;flex-wrap:wrap;padding:8px 10px;background:var(--tm-bg-tertiary);border:1px solid var(--tm-border-light)}.dependency-source{color:var(--tm-text-secondary);font-size:13px}
</style>
