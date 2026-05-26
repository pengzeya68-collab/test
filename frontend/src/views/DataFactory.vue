<template>
  <div class="data-factory">
    <div class="df-toolbar">
      <div class="toolbar-left">
        <h3 class="df-title">🧪 测试数据工厂</h3>
        <span class="df-subtitle">基于规则自动生成测试数据集，支持数据驱动执行</span>
      </div>
      <div class="toolbar-right">
        <el-button type="primary" @click="openCreateDialog">
          <el-icon><Plus /></el-icon>
          新建模板
        </el-button>
      </div>
    </div>

    <div class="df-body">
      <div class="df-sidebar" :class="{ collapsed: sidebarCollapsed }">
        <div class="sidebar-header">
          <span v-if="!sidebarCollapsed">📋 数据模板</span>
          <el-button text size="small" @click="sidebarCollapsed = !sidebarCollapsed">
            {{ sidebarCollapsed ? '▶' : '◀' }}
          </el-button>
        </div>
        <div class="template-list" v-if="!sidebarCollapsed">
          <div
            v-for="tpl in templates"
            :key="tpl.id"
            class="template-item"
            :class="{ active: selectedTemplate?.id === tpl.id }"
            @click="selectTemplate(tpl)"
          >
            <div class="ti-name">{{ tpl.name }}</div>
            <div class="ti-meta">
              <span>{{ tpl.fields?.length || 0 }}字段</span>
              <span>{{ tpl.row_count }}行</span>
            </div>
          </div>
          <div class="empty-hint" v-if="templates.length === 0 && !loading">
            暂无模板，点击"新建模板"开始
          </div>
        </div>
      </div>

      <div class="df-main">
        <div v-if="!selectedTemplate" class="empty-state">
          <div class="empty-icon">📦</div>
          <p>选择一个模板或创建新模板来生成测试数据</p>
        </div>

        <div v-else class="template-detail">
          <div class="detail-header">
            <div class="dh-info">
              <h4>{{ selectedTemplate.name }}</h4>
              <p v-if="selectedTemplate.description">{{ selectedTemplate.description }}</p>
            </div>
            <div class="dh-actions">
              <el-button size="small" @click="editTemplate(selectedTemplate)" :loading="detailLoading" :disabled="detailLoading">编辑</el-button>
              <el-button size="small" type="primary" @click="previewTemplate" :loading="previewLoading" :disabled="previewLoading || generateLoading || runLoading">预览</el-button>
              <el-button size="small" type="success" @click="generateData" :loading="generateLoading" :disabled="generateLoading || previewLoading || runLoading">生成数据</el-button>
              <el-button size="small" type="danger" @click="deleteTemplate(selectedTemplate)" :loading="deleteLoading" :disabled="deleteLoading">删除</el-button>
            </div>
          </div>

          <div class="detail-body">
            <div class="db-section">
              <h5>字段规则</h5>
              <el-table :data="selectedTemplate.fields" border size="small" class="dark-table">
                <el-table-column prop="field_name" label="字段名" width="140" />
                <el-table-column prop="field_label" label="标签" width="120" />
                <el-table-column label="规则类型" width="120">
                  <template #default="{ row }">
                    <el-tag size="small" type="info">{{ getRuleLabel(row.rule_type) }}</el-tag>
                  </template>
                </el-table-column>
                <el-table-column label="配置" min-width="200">
                  <template #default="{ row }">
                    <code class="config-code">{{ formatConfig(row.rule_config) }}</code>
                  </template>
                </el-table-column>
              </el-table>
            </div>

            <div class="db-section" v-if="previewData">
              <h5>数据预览 (前20行)</h5>
              <el-table :data="previewData.rows" border size="small" class="dark-table" max-height="300">
              <el-table-column
                v-for="(col, idx) in previewData.columns"
                :key="idx"
                :label="col"
                :prop="String(idx)"
                min-width="120"
              />
              </el-table>
              <div class="preview-info">
                共 {{ previewData.row_count }} 行 · {{ previewData.columns.length }} 列
              </div>
            </div>

            <div class="db-section" v-if="previewError">
              <div class="error-banner">
                <span>⚠️ {{ previewError }}</span>
                <el-button size="small" type="primary" @click="previewTemplate" :loading="previewLoading">重试预览</el-button>
              </div>
            </div>

            <div class="db-section" v-if="generatedDataset">
              <h5>✅ 数据集已生成</h5>
              <div class="dataset-info-card">
                <div class="dic-item">
                  <span class="dic-label">数据集名称</span>
                  <span class="dic-value">{{ generatedDataset.name }}</span>
                </div>
                <div class="dic-item">
                  <span class="dic-label">数据量</span>
                  <span class="dic-value">{{ generatedDataset.row_count }} 行 × {{ generatedDataset.columns.length }} 列</span>
                </div>
                <div class="dic-actions">
                  <el-button size="small" type="primary" @click="bindToScenario" :loading="bindLoading" :disabled="bindLoading || runLoading">绑定到场景</el-button>
                  <el-button size="small" type="success" @click="runDataDriven" :loading="runLoading" :disabled="runLoading || bindLoading">一键数据驱动执行</el-button>
                </div>
              </div>
            </div>

            <div class="db-section" v-if="generateError">
              <div class="error-banner">
                <span>⚠️ {{ generateError }}</span>
                <el-button size="small" type="primary" @click="generateData" :loading="generateLoading">重试生成</el-button>
              </div>
            </div>

            <div class="db-section" v-if="bindError">
              <div class="error-banner">
                <span>⚠️ {{ bindError }}</span>
                <el-button size="small" type="primary" @click="bindToScenario" :loading="bindLoading">重试绑定</el-button>
              </div>
            </div>

            <div class="db-section" v-if="runResult">
              <h5>执行结果</h5>
              <div class="run-result-card" :class="{ success: runResult.success, failed: !runResult.success }">
                <div class="rrc-status">{{ runResult.success ? '✅ 全部通过' : '❌ 存在失败' }}</div>
                <div class="rrc-stats">
                  <span>总迭代: {{ runResult.total_iterations }}</span>
                  <span>成功: {{ runResult.success_iterations }}</span>
                  <span>失败: {{ runResult.failed_iterations }}</span>
                  <span>耗时: {{ runResult.total_duration }}ms</span>
                </div>
              </div>
            </div>

            <div class="db-section" v-if="runError">
              <div class="error-banner">
                <span>⚠️ {{ runError }}</span>
                <el-button size="small" type="primary" @click="runDataDriven" :loading="runLoading">重试执行</el-button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <el-dialog
      v-model="dialogVisible"
      :title="dialogMode === 'create' ? '新建数据模板' : '编辑数据模板'"
      width="700px"
      custom-class="dark-dialog"
      destroy-on-close
    >
      <el-form :model="form" label-width="80px">
        <el-form-item label="模板名称">
          <el-input v-model="form.name" placeholder="如：用户注册测试数据" class="dark-input" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" placeholder="模板用途说明" class="dark-input" />
        </el-form-item>
        <el-form-item label="关联场景">
          <el-select v-model="form.scenario_id" placeholder="可选" clearable class="dark-select" style="width:100%">
            <el-option
              v-for="s in scenarios"
              :key="s.id"
              :label="s.name"
              :value="s.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="生成行数">
          <el-input-number v-model="form.row_count" :min="1" :max="100" class="dark-input" />
        </el-form-item>

        <el-divider>字段规则</el-divider>
        <div class="fields-editor">
          <div v-for="(field, idx) in form.fields" :key="idx" class="field-row">
            <el-input v-model="field.field_name" placeholder="字段名" size="small" style="width:120px" class="dark-input" :class="{ 'is-error': fieldErrors[idx]?.field_name }" />
            <el-input v-model="field.field_label" placeholder="标签" size="small" style="width:100px" class="dark-input" />
            <el-select v-model="field.rule_type" placeholder="规则" size="small" style="width:120px" class="dark-select" @change="onRuleTypeChange(field)">
              <el-option v-for="rt in ruleTypes" :key="rt.type" :label="rt.label" :value="rt.type" />
            </el-select>
            <el-input
              v-if="field.rule_type === 'fixed'"
              v-model="field.rule_config.value"
              placeholder="值"
              size="small"
              style="width:140px"
              class="dark-input"
            />
            <el-input
              v-else-if="field.rule_type === 'enum'"
              v-model="field.configInput"
              placeholder="选项,逗号分隔"
              size="small"
              style="width:180px"
              class="dark-input"
              @change="updateEnumOptions(field)"
            />
            <el-input
              v-else-if="field.rule_type === 'increment'"
              v-model="field.configInput"
              placeholder="prefix,start,step"
              size="small"
              style="width:160px"
              class="dark-input"
              @change="updateIncrementConfig(field)"
            />
            <el-input
              v-else-if="field.rule_type === 'date_offset'"
              v-model="field.configInput"
              placeholder="offset_days"
              size="small"
              style="width:100px"
              class="dark-input"
              @change="updateDateOffset(field)"
            />
            <el-input
              v-else-if="field.rule_type === 'env_ref'"
              v-model="field.configInput"
              placeholder="变量名"
              size="small"
              style="width:120px"
              class="dark-input"
              @change="updateEnvRef(field)"
            />
            <el-input
              v-else-if="field.rule_type === 'uuid'"
              v-model="field.configInput"
              placeholder="版本(1/4)"
              size="small"
              style="width:100px"
              class="dark-input"
              @change="updateUuidConfig(field)"
            />
            <el-input
              v-else-if="field.rule_type === 'timestamp'"
              v-model="field.configInput"
              placeholder="格式(秒/毫秒/日期)"
              size="small"
              style="width:140px"
              class="dark-input"
              @change="updateTimestampConfig(field)"
            />
            <el-input
              v-else-if="field.rule_type === 'phone'"
              v-model="field.configInput"
              placeholder="前缀"
              size="small"
              style="width:120px"
              class="dark-input"
              @change="updatePhoneConfig(field)"
            />
            <el-input
              v-else-if="field.rule_type === 'email'"
              v-model="field.configInput"
              placeholder="域名,前缀"
              size="small"
              style="width:160px"
              class="dark-input"
              @change="updateEmailConfig(field)"
            />
            <el-input
              v-else-if="field.rule_type === 'username'"
              v-model="field.configInput"
              placeholder="前缀,后缀长度"
              size="small"
              style="width:140px"
              class="dark-input"
              @change="updateUsernameConfig(field)"
            />
            <el-tag size="small" type="info" v-if="field.rule_type">{{ getRuleLabel(field.rule_type) }}</el-tag>
            <el-button text type="danger" size="small" @click="removeField(idx)">✕</el-button>
          </div>
          <el-button text type="primary" size="small" @click="addField" style="margin-top:8px">
            + 添加字段
          </el-button>
        </div>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false" class="btn-cancel">取消</el-button>
        <el-button type="primary" @click="saveTemplate" class="btn-primary" :loading="saveLoading" :disabled="saveLoading">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="bindDialogVisible" title="绑定场景" width="450px" custom-class="dark-dialog">
      <el-select v-model="bindScenarioId" placeholder="选择场景" class="dark-select" style="width:100%">
        <el-option v-for="s in scenarios" :key="s.id" :label="s.name" :value="s.id" />
      </el-select>
      <template #footer>
        <el-button @click="bindDialogVisible = false" class="btn-cancel">取消</el-button>
        <el-button type="primary" @click="doBindScenario" class="btn-primary" :disabled="!bindScenarioId" :loading="bindLoading">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import autoTestRequest from '@/utils/autoTestRequest'

const RULE_LABELS = {
  fixed: '固定值', enum: '枚举值', increment: '递增数字',
  uuid: 'UUID', timestamp: '时间戳', date_offset: '日期偏移',
  phone: '随机手机号', email: '随机邮箱', username: '随机用户名',
  env_ref: '引用环境变量'
}

const ruleTypes = ref([])
const templates = ref([])
const scenarios = ref([])
const selectedTemplate = ref(null)
const loading = ref(false)
const sidebarCollapsed = ref(false)

const dialogVisible = ref(false)
const dialogMode = ref('create')
const editingId = ref(null)
const form = ref({
  name: '',
  description: '',
  scenario_id: null,
  row_count: 10,
  fields: []
})

const previewData = ref(null)
const generatedDataset = ref(null)
const runResult = ref(null)
const bindDialogVisible = ref(false)
const bindScenarioId = ref(null)

const previewLoading = ref(false)
const generateLoading = ref(false)
const bindLoading = ref(false)
const runLoading = ref(false)
const saveLoading = ref(false)
const deleteLoading = ref(false)
const detailLoading = ref(false)
const retryAction = ref(null)

const previewError = ref('')
const generateError = ref('')
const bindError = ref('')
const runError = ref('')
const fieldErrors = ref({})

const resetForm = () => {
  form.value = {
    name: '',
    description: '',
    scenario_id: null,
    row_count: 10,
    fields: []
  }
}

const getRuleLabel = (type) => RULE_LABELS[type] || type

const formatConfig = (config) => {
  if (!config) return '-'
  if (config.value !== undefined) return config.value
  if (config.options) return Array.isArray(config.options) ? config.options.join(', ') : config.options
  if (config.prefix !== undefined && config.start !== undefined) return `前缀:${config.prefix || ''} 起始:${config.start} 步长:${config.step || 1}`
  if (config.variable_name) return `\${${config.variable_name}}`
  if (config.offset_days !== undefined) return `偏移:${config.offset_days}天`
  if (config.version) return `UUID v${config.version}`
  if (config.format) return `格式:${config.format}`
  if (config.domains || config.username_prefix) return `域名:${(config.domains || []).join(';')} 前缀:${config.username_prefix || ''}`
  if (config.prefixes || config.suffix_length) return `前缀:${(config.prefixes || []).join(';')} 后缀长度:${config.suffix_length || 4}`
  if (config.prefix && !config.start) return `前缀:${config.prefix}`
  return JSON.stringify(config)
}

const updateEnumOptions = (field) => {
  field.rule_config = { options: (field.configInput || '').split(',').map(s => s.trim()).filter(Boolean) }
}

const updateIncrementConfig = (field) => {
  const parts = (field.configInput || '').split(',')
  field.rule_config = {
    prefix: (parts[0] || '').trim(),
    start: parseInt(parts[1]) || 1,
    step: parseInt(parts[2]) || 1
  }
}

const updateDateOffset = (field) => {
  field.rule_config = { offset_days: parseInt(field.configInput) || 0 }
}

const updateEnvRef = (field) => {
  field.rule_config = { variable_name: (field.configInput || '').trim() }
}

const updateUuidConfig = (field) => {
  field.rule_config = { version: (field.configInput || '').trim() || '4' }
}

const updateTimestampConfig = (field) => {
  field.rule_config = { format: (field.configInput || '').trim() || 'seconds' }
}

const updatePhoneConfig = (field) => {
  field.rule_config = { prefix: (field.configInput || '').trim() }
}

const updateEmailConfig = (field) => {
  const parts = (field.configInput || '').split(',')
  field.rule_config = {
    domains: (parts[0] || 'test.com').split(';').map(s => s.trim()).filter(Boolean),
    username_prefix: (parts[1] || 'testuser').trim()
  }
}

const updateUsernameConfig = (field) => {
  const parts = (field.configInput || '').split(',')
  field.rule_config = {
    prefixes: (parts[0] || 'tester').split(';').map(s => s.trim()).filter(Boolean),
    suffix_length: parseInt(parts[1]) || 4
  }
}

const onRuleTypeChange = (field) => {
  field.configInput = ''
  if (field.rule_type === 'uuid' || field.rule_type === 'timestamp') {
    field.rule_config = {}
    field.configInput = field.rule_type === 'uuid' ? '4' : 'seconds'
  } else if (field.rule_type === 'phone') {
    field.rule_config = {}
    field.configInput = ''
  } else if (field.rule_type === 'email') {
    field.rule_config = { domains: ['test.com'], username_prefix: 'testuser' }
    field.configInput = 'test.com,testuser'
  } else if (field.rule_type === 'username') {
    field.rule_config = { prefixes: ['tester'], suffix_length: 4 }
    field.configInput = 'tester,4'
  } else {
    field.rule_config = {}
  }
}

const addField = () => {
  form.value.fields.push({
    field_name: '',
    field_label: '',
    rule_type: 'fixed',
    rule_config: { value: '' },
    configInput: '',
    sort_order: form.value.fields.length
  })
}

const removeField = (idx) => {
  form.value.fields.splice(idx, 1)
}

const fetchTemplates = async () => {
  loading.value = true
  try {
    const res = await autoTestRequest.get('/auto-test/data-factory/templates')
    templates.value = res || []
  } catch (e) {
    console.error('获取模板列表失败', e)
  } finally {
    loading.value = false
  }
}

const fetchScenarios = async () => {
  try {
    const res = await autoTestRequest.get('/auto-test/data-factory/scenarios')
    scenarios.value = res || []
  } catch (e) {
    console.error('获取场景列表失败', e)
  }
}

const fetchRuleTypes = async () => {
  try {
    const res = await autoTestRequest.get('/auto-test/data-factory/rule-types')
    ruleTypes.value = res?.rule_types || []
  } catch (e) {
    console.error('获取规则类型失败', e)
  }
}

const selectTemplate = (tpl) => {
  selectedTemplate.value = tpl
  previewData.value = null
  generatedDataset.value = null
  runResult.value = null
  previewError.value = ''
  generateError.value = ''
  runError.value = ''
}

const openCreateDialog = () => {
  resetForm()
  dialogMode.value = 'create'
  editingId.value = null
  fieldErrors.value = {}
  dialogVisible.value = true
}

const editTemplate = async (tpl) => {
  dialogMode.value = 'edit'
  editingId.value = tpl.id
  detailLoading.value = true
  try {
    const res = await autoTestRequest.get(`/auto-test/data-factory/templates/${tpl.id}`)
    const fields = (res.fields || []).map(f => ({
      ...f,
      configInput: buildConfigInput(f),
    }))
    form.value = {
      name: res.name || '',
      description: res.description || '',
      scenario_id: res.scenario_id || null,
      row_count: res.row_count || 10,
      fields: fields,
    }
    fieldErrors.value = {}
    dialogVisible.value = true
  } catch (e) {
    ElMessage.error('获取模板详情失败，请重试')
  } finally {
    detailLoading.value = false
  }
}

const buildConfigInput = (field) => {
  const c = field.rule_config || {}
  if (field.rule_type === 'fixed') return c.value || ''
  if (field.rule_type === 'enum') return Array.isArray(c.options) ? c.options.join(', ') : ''
  if (field.rule_type === 'increment') return `${c.prefix || ''},${c.start || 1},${c.step || 1}`
  if (field.rule_type === 'date_offset') return String(c.offset_days ?? 0)
  if (field.rule_type === 'env_ref') return c.variable_name || ''
  if (field.rule_type === 'email') return `${Array.isArray(c.domains) ? c.domains.join(';') : (c.domains || 'test.com')},${c.username_prefix || 'testuser'}`
  if (field.rule_type === 'username') return `${Array.isArray(c.prefixes) ? c.prefixes.join(';') : (c.prefixes || 'tester')},${c.suffix_length || 4}`
  if (field.rule_type === 'phone') return c.prefix || ''
  if (field.rule_type === 'uuid') return c.version || '4'
  if (field.rule_type === 'timestamp') return c.format || 'seconds'
  return ''
}

const validateFields = () => {
  const errors = {}
  form.value.fields.forEach((field, idx) => {
    if (!field.field_name.trim()) {
      errors[idx] = { field_name: '字段名不能为空' }
    }
  })
  fieldErrors.value = errors
  return Object.keys(errors).length === 0
}

const saveTemplate = async () => {
  if (!form.value.name.trim()) {
    ElMessage.warning('请输入模板名称')
    return
  }
  if (!validateFields()) {
    ElMessage.warning('请填写所有字段名称')
    return
  }
  saveLoading.value = true
  try {
    if (dialogMode.value === 'create') {
      await autoTestRequest.post('/auto-test/data-factory/templates', form.value)
      ElMessage.success('模板创建成功')
    } else {
      await autoTestRequest.put(`/auto-test/data-factory/templates/${editingId.value}`, form.value)
      ElMessage.success('模板更新成功')
    }
    dialogVisible.value = false
    await fetchTemplates()
    if (editingId.value && selectedTemplate.value?.id === editingId.value) {
      const res = await autoTestRequest.get(`/auto-test/data-factory/templates/${editingId.value}`)
      selectedTemplate.value = res
    }
  } catch (e) {
    ElMessage.error('保存失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    saveLoading.value = false
  }
}

const deleteTemplate = async (tpl) => {
  try {
    await ElMessageBox.confirm(`确定删除模板"${tpl.name}"吗？`, '确认', { type: 'warning' })
    deleteLoading.value = true
    await autoTestRequest.delete(`/auto-test/data-factory/templates/${tpl.id}`)
    ElMessage.success('模板已删除')
    selectedTemplate.value = null
    await fetchTemplates()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('删除失败')
  } finally {
    deleteLoading.value = false
  }
}

const previewTemplate = async () => {
  previewLoading.value = true
  previewError.value = ''
  try {
    const res = await autoTestRequest.post(`/auto-test/data-factory/templates/${selectedTemplate.value.id}/preview`)
    previewData.value = res
    ElMessage.success('预览生成成功')
  } catch (e) {
    previewError.value = e.response?.data?.detail || '预览失败，请重试'
    ElMessage.error(previewError.value)
  } finally {
    previewLoading.value = false
  }
}

const generateData = async () => {
  generateLoading.value = true
  generateError.value = ''
  try {
    const res = await autoTestRequest.post(`/auto-test/data-factory/templates/${selectedTemplate.value.id}/generate`)
    generatedDataset.value = res
    ElMessage.success('数据集已生成')
  } catch (e) {
    generateError.value = e.response?.data?.detail || '生成失败，请重试'
    ElMessage.error(generateError.value)
  } finally {
    generateLoading.value = false
  }
}

const bindToScenario = () => {
  if (!generatedDataset.value) {
    ElMessage.warning('请先生成数据集')
    return
  }
  bindDialogVisible.value = true
  bindScenarioId.value = null
}

const doBindScenario = async () => {
  bindLoading.value = true
  bindError.value = ''
  try {
    if (generatedDataset.value.dataset_id > 0) {
      await autoTestRequest.post(`/auto-test/data-factory/datasets/${generatedDataset.value.dataset_id}/bind-scenario/${bindScenarioId.value}`)
      ElMessage.success('数据集已绑定到场景')
    } else {
      await autoTestRequest.put(`/auto-test/data-factory/templates/${selectedTemplate.value.id}`, {
        ...selectedTemplate.value,
        scenario_id: bindScenarioId.value,
        fields: selectedTemplate.value.fields || []
      })
      const updated = await autoTestRequest.get(`/auto-test/data-factory/templates/${selectedTemplate.value.id}`)
      selectedTemplate.value = updated
      const res = await autoTestRequest.post(`/auto-test/data-factory/templates/${selectedTemplate.value.id}/generate`)
      generatedDataset.value = res
      ElMessage.success('数据已生成并绑定到场景')
    }
    bindDialogVisible.value = false
  } catch (e) {
    bindError.value = e.response?.data?.detail || '绑定失败，请重试'
    ElMessage.error(bindError.value)
  } finally {
    bindLoading.value = false
  }
}

const runDataDriven = async () => {
  if (!generatedDataset.value) {
    ElMessage.warning('请先生成数据集')
    return
  }
  runLoading.value = true
  runError.value = ''
  try {
    const res = await autoTestRequest.post(`/auto-test/data-factory/datasets/${generatedDataset.value.dataset_id}/run`)
    runResult.value = res
    ElMessage.success(res?.success ? '执行完成，全部通过' : '执行完成，存在失败')
  } catch (e) {
    runError.value = e.response?.data?.detail || '执行失败，请重试'
    ElMessage.error(runError.value)
  } finally {
    runLoading.value = false
  }
}

onMounted(() => {
  fetchTemplates()
  fetchScenarios()
  fetchRuleTypes()
})
</script>

<style scoped>
.data-factory {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.df-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-color, #333);
}

.df-title {
  margin: 0;
  font-size: 18px;
  color: #e0e0e0;
}

.df-subtitle {
  font-size: 12px;
  color: #888;
  margin-left: 12px;
}

.df-body {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.df-sidebar {
  width: 240px;
  border-right: 1px solid var(--border-color, #333);
  padding: 12px;
  overflow-y: auto;
  transition: width .2s;
}

.df-sidebar.collapsed {
  width: 40px;
  padding: 12px 4px;
}

.sidebar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 14px;
  color: #ccc;
  margin-bottom: 8px;
}

.template-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.template-item {
  padding: 10px 12px;
  border-radius: 6px;
  cursor: pointer;
  border: 1px solid transparent;
  transition: all .15s;
}

.template-item:hover {
  background: rgba(64, 158, 255, .08);
  border-color: rgba(64, 158, 255, .2);
}

.template-item.active {
  background: rgba(64, 158, 255, .12);
  border-color: #409eff;
}

.ti-name {
  font-size: 14px;
  color: #e0e0e0;
  font-weight: 500;
}

.ti-meta {
  font-size: 11px;
  color: #777;
  margin-top: 4px;
  display: flex;
  gap: 12px;
}

.df-main {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
}

.empty-state {
  text-align: center;
  padding: 60px 0;
  color: #666;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 12px;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border-color, #333);
}

.dh-info h4 {
  margin: 0 0 4px;
  font-size: 18px;
  color: #e0e0e0;
}

.dh-info p {
  margin: 0;
  color: #888;
  font-size: 13px;
}

.dh-actions {
  display: flex;
  gap: 8px;
}

.db-section {
  margin-bottom: 24px;
}

.db-section h5 {
  margin: 0 0 8px;
  font-size: 14px;
  color: #ccc;
}

.config-code {
  font-size: 12px;
  color: #67c23a;
  background: rgba(103, 194, 58, .1);
  padding: 2px 6px;
  border-radius: 3px;
}

.preview-info {
  margin-top: 8px;
  font-size: 12px;
  color: #888;
}

.dataset-info-card {
  background: rgba(64, 158, 255, .06);
  border: 1px solid rgba(64, 158, 255, .2);
  border-radius: 8px;
  padding: 16px;
}

.dic-item {
  display: flex;
  gap: 12px;
  margin-bottom: 8px;
}

.dic-label {
  color: #888;
  width: 80px;
}

.dic-value {
  color: #e0e0e0;
  font-weight: 500;
}

.dic-actions {
  margin-top: 12px;
  display: flex;
  gap: 8px;
}

.run-result-card {
  border-radius: 8px;
  padding: 16px;
}

.run-result-card.success {
  background: rgba(103, 194, 58, .08);
  border: 1px solid rgba(103, 194, 58, .3);
}

.run-result-card.failed {
  background: rgba(245, 108, 108, .08);
  border: 1px solid rgba(245, 108, 108, .3);
}

.rrc-status {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 8px;
}

.rrc-stats {
  display: flex;
  gap: 20px;
  color: #aaa;
  font-size: 13px;
}

.fields-editor {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.field-row {
  display: flex;
  gap: 6px;
  align-items: center;
}

.empty-hint {
  text-align: center;
  color: #666;
  font-size: 13px;
  padding: 20px 0;
}

.dark-dialog {
  background: #1e1e1e;
}

.error-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 16px;
  background: rgba(245, 108, 108, .08);
  border: 1px solid rgba(245, 108, 108, .25);
  border-radius: 8px;
  color: #f89898;
  font-size: 13px;
}

.is-error :deep(.el-input__inner) {
  border-color: #f56c6c !important;
}
</style>