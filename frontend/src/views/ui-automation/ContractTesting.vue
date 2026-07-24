<template>
  <div class="upgrade-page">
    <header class="page-header">
      <div>
        <h1>契约测试</h1>
        <p>OpenAPI 快照、Schema 变更、响应校验与客户端代码生成。</p>
      </div>
      <div class="actions">
        <el-button @click="load">刷新</el-button>
        <el-button type="primary" @click="showSnapshot = true">导入 Spec</el-button>
      </div>
    </header>

    <el-row :gutter="12" class="stat-row">
      <el-col :span="8"><el-statistic title="快照数" :value="snapshots.length" /></el-col>
      <el-col :span="8"><el-statistic title="Schema 变更" :value="changes.length" /></el-col>
      <el-col :span="8"><el-statistic title="校验规则" :value="rules.length" /></el-col>
    </el-row>

    <el-tabs v-model="tab">
      <el-tab-pane label="快照" name="snapshots">
        <el-table :data="snapshots" v-loading="loading" stripe>
          <el-table-column prop="id" label="ID" width="70" />
          <el-table-column prop="source_type" label="来源" width="100" />
          <el-table-column prop="source_url" label="URL" min-width="180" show-overflow-tooltip />
          <el-table-column prop="created_at" label="时间" min-width="160" />
          <el-table-column label="操作" width="160">
            <template #default="{ row }">
              <el-button link type="primary" @click="openCodegen(row)">生成代码</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
      <el-tab-pane label="变更" name="changes">
        <el-table :data="changes" stripe>
          <el-table-column prop="change_type" label="类型" width="120" />
          <el-table-column prop="path" label="路径" min-width="180" />
          <el-table-column prop="method" label="方法" width="90" />
          <el-table-column prop="summary" label="摘要" min-width="220" show-overflow-tooltip />
          <el-table-column prop="created_at" label="时间" min-width="160" />
        </el-table>
      </el-tab-pane>
      <el-tab-pane label="规则" name="rules">
        <div class="toolbar">
          <el-button type="success" size="small" @click="showRule = true">新增规则</el-button>
        </div>
        <el-table :data="rules" stripe>
          <el-table-column prop="case_id" label="用例" width="90" />
          <el-table-column prop="snapshot_id" label="快照" width="90" />
          <el-table-column prop="method" label="方法" width="90" />
          <el-table-column prop="endpoint_path" label="路径" min-width="180" />
          <el-table-column prop="strict_mode" label="严格" width="80" />
        </el-table>
      </el-tab-pane>
      <el-tab-pane label="校验" name="validate">
        <el-form label-width="100px" style="max-width: 640px">
          <el-form-item label="用例 ID"><el-input-number v-model="validateForm.case_id" :min="1" /></el-form-item>
          <el-form-item label="方法"><el-input v-model="validateForm.method" placeholder="GET" /></el-form-item>
          <el-form-item label="路径"><el-input v-model="validateForm.path" placeholder="/api/users" /></el-form-item>
          <el-form-item label="状态码"><el-input-number v-model="validateForm.status_code" :min="100" :max="599" /></el-form-item>
          <el-form-item label="响应 JSON"><el-input v-model="validateBody" type="textarea" :rows="6" /></el-form-item>
          <el-button type="primary" @click="runValidate">校验</el-button>
        </el-form>
        <pre v-if="validateResult" class="result-box">{{ JSON.stringify(validateResult, null, 2) }}</pre>
      </el-tab-pane>
    </el-tabs>

    <el-dialog v-model="showSnapshot" title="导入 OpenAPI Spec" width="640px">
      <el-input v-model="specContent" type="textarea" :rows="14" placeholder="粘贴 OpenAPI JSON/YAML" />
      <template #footer>
        <el-button @click="showSnapshot = false">取消</el-button>
        <el-button type="primary" @click="createSnapshot">导入</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showRule" title="契约规则" width="480px">
      <el-form label-width="100px">
        <el-form-item label="用例 ID"><el-input-number v-model="ruleForm.case_id" :min="1" style="width: 100%" /></el-form-item>
        <el-form-item label="快照 ID"><el-input-number v-model="ruleForm.snapshot_id" :min="1" style="width: 100%" /></el-form-item>
        <el-form-item label="方法"><el-input v-model="ruleForm.method" /></el-form-item>
        <el-form-item label="路径"><el-input v-model="ruleForm.endpoint_path" /></el-form-item>
        <el-form-item label="严格模式"><el-switch v-model="ruleForm.strict_mode" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showRule = false">取消</el-button>
        <el-button type="primary" @click="saveRule">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showCodegen" title="代码生成" width="720px">
      <el-form inline>
        <el-form-item label="语言">
          <el-select v-model="codegen.language" style="width: 140px">
            <el-option v-for="lang in languages" :key="lang" :label="lang" :value="lang" />
          </el-select>
        </el-form-item>
        <el-form-item label="Base URL"><el-input v-model="codegen.base_url" style="width: 260px" /></el-form-item>
        <el-button type="primary" @click="doCodegen">生成</el-button>
      </el-form>
      <el-input v-model="codegenOutput" type="textarea" :rows="16" readonly />
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { storeToRefs } from 'pinia'
import { ElMessage } from 'element-plus'
import { featureUpgradesApi } from '@/api/feature-upgrades'
import { useProjectStore } from '@/stores/project'

const { projectId } = storeToRefs(useProjectStore())
const loading = ref(false)
const tab = ref('snapshots')
const snapshots = ref([])
const changes = ref([])
const rules = ref([])
const showSnapshot = ref(false)
const showRule = ref(false)
const showCodegen = ref(false)
const specContent = ref('')
const validateBody = ref('{}')
const validateResult = ref(null)
const codegenOutput = ref('')
const languages = [
  'python', 'javascript', 'typescript', 'java', 'go', 'curl',
  'csharp', 'php', 'ruby', 'kotlin', 'swift', 'rust',
]
const validateForm = reactive({ case_id: 1, method: 'GET', path: '/', status_code: 200 })
const ruleForm = reactive({ case_id: 1, snapshot_id: 1, method: 'GET', endpoint_path: '/', strict_mode: false })
const codegen = reactive({ snapshot_id: null, language: 'python', base_url: 'https://api.example.com', class_name: 'ApiClient' })

async function load() {
  loading.value = true
  try {
    const [s, c, r] = await Promise.all([
      featureUpgradesApi.listSnapshots(projectId.value),
      featureUpgradesApi.listSchemaChanges(projectId.value),
      featureUpgradesApi.listContractRules(projectId.value),
    ])
    snapshots.value = s.items || []
    changes.value = c.items || []
    rules.value = r.items || []
  } catch (error) {
    ElMessage.error(error.message || '加载失败')
  } finally {
    loading.value = false
  }
}

async function createSnapshot() {
  if (!specContent.value.trim()) return ElMessage.warning('请粘贴 Spec')
  try {
    await featureUpgradesApi.createSnapshot({
      project_id: projectId.value,
      spec_content: specContent.value,
      source_type: 'upload',
    })
    showSnapshot.value = false
    specContent.value = ''
    ElMessage.success('快照已创建')
    await load()
  } catch (error) {
    ElMessage.error(error.message || '导入 Spec 失败')
  }
}

async function saveRule() {
  try {
    await featureUpgradesApi.upsertContractRule(projectId.value, { ...ruleForm })
    showRule.value = false
    ElMessage.success('规则已保存')
    await load()
  } catch (error) {
    ElMessage.error(error.message || '保存规则失败')
  }
}

async function runValidate() {
  let body
  try {
    body = validateBody.value ? JSON.parse(validateBody.value) : null
  } catch {
    return ElMessage.warning('响应 JSON 无效')
  }
  try {
    validateResult.value = await featureUpgradesApi.validateContract({
      project_id: projectId.value,
      ...validateForm,
      response_body: body,
    })
  } catch (error) {
    validateResult.value = null
    ElMessage.error(error.message || '契约校验失败')
  }
}

function openCodegen(row) {
  codegen.snapshot_id = row.id
  codegenOutput.value = ''
  showCodegen.value = true
}

async function doCodegen() {
  try {
    const res = await featureUpgradesApi.generateCode({ ...codegen })
    codegenOutput.value = res.code || res.content || JSON.stringify(res, null, 2)
  } catch (error) {
    codegenOutput.value = ''
    ElMessage.error(error.message || '生成代码失败')
  }
}

onMounted(load)
</script>

<style scoped>
.upgrade-page { padding: 20px; display: flex; flex-direction: column; gap: 16px; }
.page-header { display: flex; justify-content: space-between; gap: 12px; }
.page-header h1 { margin: 0 0 6px; font-size: 22px; }
.page-header p { margin: 0; color: #64748b; }
.actions { display: flex; gap: 8px; }
.toolbar { margin-bottom: 10px; }
.result-box { margin-top: 12px; background: #0f172a; color: #e2e8f0; padding: 12px; border-radius: 8px; overflow: auto; }
</style>
