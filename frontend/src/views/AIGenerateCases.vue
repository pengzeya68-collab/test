<template>
  <div class="ai-generate-page">
    <div class="page-header">
      <div class="header-left">
        <el-button link @click="$router.push('/auto-test')">
          <el-icon><ArrowLeft /></el-icon> 返回工作台
        </el-button>
        <h2>AI 智能生成测试用例</h2>
        <p class="subtitle">上传 Swagger/OpenAPI 文档，AI 自动生成带断言、变量提取、场景链的完整用例</p>
      </div>
      <div class="header-right">
        <el-button @click="showHelp = true">❓ 使用说明</el-button>
      </div>
    </div>

    <!-- 步骤条 -->
    <el-steps :active="currentStep" finish-status="success" class="steps-bar">
      <el-step title="上传文档" />
      <el-step title="配置选项" />
      <el-step title="AI 生成" />
      <el-step title="预览 & 导入" />
    </el-steps>

    <!-- 步骤1: 上传 -->
    <div v-if="currentStep === 0" class="step-content">
      <div class="upload-area">
        <el-upload
          ref="uploadRef"
          :auto-upload="false"
          :limit="1"
          :on-change="handleFileChange"
          :on-remove="() => { swaggerFile = null }"
          accept=".json,.yaml,.yml"
          drag
        >
          <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
          <div class="el-upload__text">拖拽文件到此处，或 <em>点击上传</em></div>
          <template #tip>
            <div class="el-upload__tip">支持 Swagger 2.0 / OpenAPI 3.0 JSON 格式</div>
          </template>
        </el-upload>

        <div class="divider-or"><span>或者</span></div>

        <el-input
          v-model="swaggerUrl"
          placeholder="输入 Swagger 文档 URL（如 http://localhost:8080/v3/api-docs）"
          clearable
          size="large"
        >
          <template #prepend>URL</template>
        </el-input>

        <el-button
          type="primary"
          size="large"
          :disabled="!swaggerFile && !swaggerUrl"
          @click="currentStep = 1"
          style="margin-top: 20px; width: 100%;"
        >
          下一步：配置选项
        </el-button>
      </div>
    </div>

    <!-- 步骤2: 配置 -->
    <div v-if="currentStep === 1" class="step-content">
      <el-card class="config-card">
        <el-form label-width="160px" size="large">
          <el-form-item label="每接口最大用例数">
            <el-slider v-model="options.max_cases_per_api" :min="1" :max="10" :step="1" show-input />
          </el-form-item>
          <el-form-item label="生成边界测试">
            <el-switch v-model="options.include_boundary" />
            <span class="form-tip">空值、超长字符串、类型错误等</span>
          </el-form-item>
          <el-form-item label="生成鉴权测试">
            <el-switch v-model="options.include_auth" />
            <span class="form-tip">无 Token、过期 Token 等</span>
          </el-form-item>
          <el-form-item label="生成场景链">
            <el-switch v-model="options.include_chain" />
            <span class="form-tip">自动识别 CRUD 关系，生成 创建→查询→修改→删除 流程</span>
          </el-form-item>
        </el-form>

        <div class="config-actions">
          <el-button @click="currentStep = 0">上一步</el-button>
          <el-button type="primary" @click="startGenerate" :loading="generating">
            {{ generating ? 'AI 生成中...' : '开始生成' }}
          </el-button>
        </div>
      </el-card>
    </div>

    <!-- 步骤3: 生成中 -->
    <div v-if="currentStep === 2" class="step-content generating-content">
      <div class="generating-animation">
        <el-icon class="spin-icon" :size="48"><Loading /></el-icon>
        <h3>AI 正在分析接口文档...</h3>
        <p>正在为每个接口生成正向用例、边界用例、鉴权用例和场景链</p>
      </div>
    </div>

    <!-- 步骤4: 预览 & 导入 -->
    <div v-if="currentStep === 3" class="step-content">
      <div class="result-header">
        <el-alert
          :title="generateResult.message"
          type="success"
          show-icon
          :closable="false"
        />
        <div class="result-stats">
          <el-tag type="primary" size="large">用例: {{ generateResult.cases?.length || 0 }}</el-tag>
          <el-tag type="warning" size="large">场景: {{ generateResult.scenarios?.length || 0 }}</el-tag>
        </div>
      </div>

      <!-- 用例列表 -->
      <el-tabs v-model="previewTab" class="preview-tabs">
        <el-tab-pane label="测试用例" name="cases">
          <div class="case-list">
            <el-collapse v-model="expandedCases">
              <el-collapse-item
                v-for="(c, idx) in generateResult.cases"
                :key="idx"
                :title="`${c.method} ${c.name}`"
                :name="idx"
              >
                <template #title>
                  <div class="case-title">
                    <el-tag :type="methodTagType(c.method)" size="small">{{ c.method }}</el-tag>
                    <span>{{ c.name }}</span>
                    <el-tag v-if="c.name?.includes('鉴权')" type="warning" size="small">鉴权</el-tag>
                    <el-tag v-if="c.name?.includes('边界')" type="danger" size="small">边界</el-tag>
                  </div>
                </template>
                <div class="case-detail">
                  <div class="detail-row">
                    <span class="label">URL:</span>
                    <code>{{ c.url }}</code>
                  </div>
                  <div class="detail-row" v-if="c.payload">
                    <span class="label">请求体:</span>
                    <pre>{{ JSON.stringify(c.payload, null, 2) }}</pre>
                  </div>
                  <div class="detail-row" v-if="c.assert_rules?.length">
                    <span class="label">断言 ({{ c.assert_rules.length }}):</span>
                    <div v-for="(rule, ri) in c.assert_rules" :key="ri" class="assert-item">
                      <el-tag size="small" type="info">{{ rule.operator }}</el-tag>
                      <code>{{ rule.field }}</code>
                      <span v-if="rule.expected"> = {{ rule.expected }}</span>
                      <span class="assert-desc">{{ rule.description }}</span>
                    </div>
                  </div>
                  <div class="detail-row" v-if="c.extractors?.length">
                    <span class="label">变量提取 ({{ c.extractors.length }}):</span>
                    <div v-for="(ext, ei) in c.extractors" :key="ei" class="extractor-item">
                      <el-tag size="small" type="success">{{ ext.type }}</el-tag>
                      <code>{{ ext.expression }}</code>
                      → <strong>{{ ext.variable }}</strong>
                    </div>
                  </div>
                  <div class="detail-row" v-if="c.description">
                    <span class="label">描述:</span>
                    <span>{{ c.description }}</span>
                  </div>
                </div>
              </el-collapse-item>
            </el-collapse>
          </div>
        </el-tab-pane>

        <el-tab-pane label="场景链" name="scenarios">
          <div v-if="!generateResult.scenarios?.length" class="empty-tip">
            <el-empty description="未生成场景链" />
          </div>
          <div v-else class="scenario-list">
            <el-card v-for="(s, idx) in generateResult.scenarios" :key="idx" class="scenario-card">
              <template #header>
                <div class="scenario-header">
                  <span class="scenario-name">{{ s.name }}</span>
                  <el-tag size="small">{{ s.steps?.length || 0 }} 步</el-tag>
                </div>
              </template>
              <p class="scenario-desc">{{ s.description }}</p>
              <div class="scenario-steps">
                <div v-for="(step, si) in s.steps" :key="si" class="scenario-step">
                  <span class="step-num">{{ si + 1 }}</span>
                  <span class="step-desc">{{ step.description }}</span>
                  <el-tag size="small" type="info">
                    {{ getCaseName(step.api_index) }}
                  </el-tag>
                </div>
              </div>
            </el-card>
          </div>
        </el-tab-pane>
      </el-tabs>

      <!-- 导入操作 -->
      <div class="import-actions">
        <el-button @click="currentStep = 1" size="large">重新生成</el-button>
        <el-input v-model="groupName" placeholder="导入分组名" style="width: 200px; margin: 0 12px;" size="large" />
        <el-button type="primary" size="large" :loading="importing" @click="confirmImport">
          {{ importing ? '导入中...' : '确认导入到用例库' }}
        </el-button>
      </div>
    </div>
    <HelpDrawer v-model="showHelp" :title="helpData.title" :intro="helpData.intro" :sections="helpData.sections" />
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, UploadFilled, Loading } from '@element-plus/icons-vue'
import autoTestRequest from '@/utils/autoTestRequest'
import HelpDrawer from '@/components/HelpDrawer.vue'
import { helpContent } from '@/utils/help-content'

const router = useRouter()

const showHelp = ref(false)
const helpData = helpContent.aiGenerateCases

const currentStep = ref(0)
const swaggerFile = ref(null)
const swaggerUrl = ref('')
const generating = ref(false)
const importing = ref(false)
const previewTab = ref('cases')
const expandedCases = ref([0])
const groupName = ref('AI生成用例')

const options = reactive({
  max_cases_per_api: 3,
  include_boundary: true,
  include_auth: true,
  include_chain: true,
})

const generateResult = reactive({
  cases: [],
  scenarios: [],
  message: '',
  total: 0,
})

const handleFileChange = (file) => {
  swaggerFile.value = file.raw
}

const startGenerate = async () => {
  generating.value = true
  currentStep.value = 2

  try {
    const formData = new FormData()
    formData.append('max_cases_per_api', options.max_cases_per_api)
    formData.append('include_boundary', options.include_boundary)
    formData.append('include_auth', options.include_auth)
    formData.append('include_chain', options.include_chain)

    let resp
    if (swaggerFile.value) {
      formData.append('file', swaggerFile.value)
      resp = await autoTestRequest.post('/auto-test/ai-generate/from-swagger', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 120000,
      })
    } else if (swaggerUrl.value) {
      formData.append('url', swaggerUrl.value)
      resp = await autoTestRequest.post('/auto-test/ai-generate/from-swagger-url', formData, {
        timeout: 120000,
      })
    }

    generateResult.cases = resp?.cases || []
    generateResult.scenarios = resp?.scenarios || []
    generateResult.message = resp?.message || '生成完成'
    generateResult.total = resp?.total || 0
    currentStep.value = 3
  } catch (e) {
    ElMessage.error('生成失败: ' + (e.response?.data?.detail || e.message))
    currentStep.value = 1
  } finally {
    generating.value = false
  }
}

const confirmImport = async () => {
  if (!generateResult.cases?.length) {
    ElMessage.warning('没有要导入的用例')
    return
  }
  importing.value = true
  try {
    const resp = await autoTestRequest.post('/auto-test/ai-generate/confirm', {
      cases: generateResult.cases,
      scenarios: generateResult.scenarios,
      group_name: groupName.value || 'AI生成用例',
    })
    ElMessage.success(resp?.message || '导入成功')
    router.push('/auto-test')
  } catch (e) {
    ElMessage.error('导入失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    importing.value = false
  }
}

const methodTagType = (method) => {
  const map = { GET: 'success', POST: 'primary', PUT: 'warning', DELETE: 'danger', PATCH: 'info' }
  return map[method] || 'info'
}

const getCaseName = (idx) => {
  return generateResult.cases?.[idx]?.name || `用例 ${idx + 1}`
}
</script>

<style scoped>
.ai-generate-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px;
}
.page-header {
  margin-bottom: 24px;
}
.page-header h2 {
  margin: 8px 0 4px;
  font-size: 22px;
}
.subtitle {
  color: var(--el-text-color-secondary);
  font-size: 14px;
}
.steps-bar {
  margin-bottom: 32px;
}
.step-content {
  min-height: 400px;
}
.upload-area {
  max-width: 600px;
  margin: 0 auto;
}
.divider-or {
  text-align: center;
  margin: 20px 0;
  position: relative;
}
.divider-or::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 0;
  right: 0;
  border-top: 1px solid var(--el-border-color);
}
.divider-or span {
  background: var(--el-bg-color);
  padding: 0 16px;
  position: relative;
  color: var(--el-text-color-secondary);
}
.config-card {
  max-width: 600px;
  margin: 0 auto;
}
.form-tip {
  margin-left: 12px;
  color: var(--el-text-color-secondary);
  font-size: 13px;
}
.config-actions {
  text-align: center;
  margin-top: 24px;
}
.generating-content {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 400px;
}
.generating-animation {
  text-align: center;
}
.spin-icon {
  animation: spin 1.5s linear infinite;
  color: var(--el-color-primary);
  margin-bottom: 16px;
}
@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
.result-header {
  margin-bottom: 20px;
}
.result-stats {
  margin-top: 12px;
  display: flex;
  gap: 12px;
}
.case-title {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
}
.case-detail {
  padding: 8px 0;
}
.detail-row {
  margin-bottom: 12px;
}
.detail-row .label {
  font-weight: 600;
  margin-right: 8px;
  color: var(--el-text-color-regular);
}
.detail-row pre {
  background: var(--el-fill-color-light);
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 12px;
  overflow-x: auto;
  margin-top: 4px;
}
.detail-row code {
  background: var(--el-fill-color-light);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 13px;
}
.assert-item, .extractor-item {
  display: flex;
  align-items: center;
  gap: 6px;
  margin: 4px 0;
  font-size: 13px;
}
.assert-desc {
  color: var(--el-text-color-secondary);
  margin-left: 8px;
}
.scenario-card {
  margin-bottom: 16px;
}
.scenario-header {
  display: flex;
  align-items: center;
  gap: 8px;
}
.scenario-name {
  font-weight: 600;
  font-size: 15px;
}
.scenario-desc {
  color: var(--el-text-color-secondary);
  margin-bottom: 12px;
}
.scenario-steps {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.scenario-step {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  background: var(--el-fill-color-lighter);
  border-radius: 6px;
}
.step-num {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--el-color-primary);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
  flex-shrink: 0;
}
.step-desc {
  flex: 1;
}
.import-actions {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid var(--el-border-color-lighter);
}
.empty-tip {
  padding: 40px 0;
}
</style>
