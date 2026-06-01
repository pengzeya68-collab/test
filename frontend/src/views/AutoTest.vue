<template>
  <div class="auto-test-page">
    <div class="beginner-guide-banner" v-if="showGuide">
      <div class="guide-content">
        <div class="guide-icon">🚀</div>
        <div class="guide-text">
          <h3>欢迎使用自动化测试工作台</h3>
          <p>跟随引导，快速上手接口测试全流程</p>
        </div>
        <div class="guide-steps">
          <div
            class="guide-step"
            :class="{ active: guideStep >= 1, done: guideStep > 1 }"
            @click="goToGuideStep(1)"
          >
            <span class="step-num">1</span>
            <span class="step-label">接口调试</span>
          </div>
          <div class="guide-arrow">→</div>
          <div
            class="guide-step"
            :class="{ active: guideStep >= 2, done: guideStep > 2 }"
            @click="goToGuideStep(2)"
          >
            <span class="step-num">2</span>
            <span class="step-label">创建用例</span>
          </div>
          <div class="guide-arrow">→</div>
          <div
            class="guide-step"
            :class="{ active: guideStep >= 3, done: guideStep > 3 }"
            @click="goToGuideStep(3)"
          >
            <span class="step-num">3</span>
            <span class="step-label">场景编排</span>
          </div>
          <div class="guide-arrow">→</div>
          <div
            class="guide-step"
            :class="{ active: guideStep >= 4, done: guideStep > 4 }"
            @click="goToGuideStep(4)"
          >
            <span class="step-num">4</span>
            <span class="step-label">批量执行</span>
          </div>
          <div class="guide-arrow">→</div>
          <div
            class="guide-step"
            :class="{ active: guideStep >= 5, done: guideStep > 5 }"
            @click="goToGuideStep(5)"
          >
            <span class="step-num">5</span>
            <span class="step-label">JMeter压测</span>
          </div>
        </div>
        <el-button text @click="dismissGuide" class="guide-close">✕</el-button>
      </div>
    </div>

    <div class="guide-tip-card" v-if="showGuide && guideTip">
      <div class="tip-header">
        <span class="tip-icon">💡</span>
        <strong>{{ guideTip.title }}</strong>
      </div>
      <p class="tip-desc">{{ guideTip.desc }}</p>
      <div class="tip-actions">
        <el-button type="primary" size="small" @click="guideTip.action" v-if="guideTip.actionLabel">
          {{ guideTip.actionLabel }}
        </el-button>
        <el-button size="small" @click="nextGuideStep">下一步</el-button>
      </div>
    </div>

    <div class="page-tabs">
      <div class="tab-nav">
        <div
          class="tab-item"
          :class="{ 'active': activeTab === 'debug' }"
          @click="activeTab = 'debug'; handleTabChange('debug')"
        >
          <el-icon><Position /></el-icon>
          <span>接口调试</span>
        </div>
        <div
          class="tab-item"
          :class="{ 'active': activeTab === 'interfaces' }"
          @click="activeTab = 'interfaces'; handleTabChange('interfaces')"
        >
          <el-icon><Document /></el-icon>
          <span>接口库</span>
        </div>
        <div
          class="tab-item"
          :class="{ 'active': activeTab === 'scenarios' }"
          @click="activeTab = 'scenarios'; handleTabChange('scenarios')"
        >
          <el-icon><FolderOpened /></el-icon>
          <span>场景管理</span>
        </div>
        <div
          class="tab-item"
          :class="{ 'active': activeTab === 'variables' }"
          @click="activeTab = 'variables'; handleTabChange('variables')"
        >
          <el-icon><DataAnalysis /></el-icon>
          <span>变量管理</span>
        </div>
        <div
          class="tab-item"
          :class="{ 'active': activeTab === 'dataFactory' }"
          @click="activeTab = 'dataFactory'; handleTabChange('dataFactory')"
        >
          <el-icon><Coin /></el-icon>
          <span>测试数据工厂</span>
        </div>
        <div
          class="tab-item jmeter-tab"
          :class="{ 'active': activeTab === 'jmeter' }"
          @click="activeTab = 'jmeter'; handleTabChange('jmeter')"
        >
          <el-icon><Connection /></el-icon>
          <span>JMeter 助手 <el-tag size="small" type="danger" class="new-tag">新</el-tag></span>
        </div>
        <div class="tab-item ai-tab" @click="$router.push('/ai-generate-cases')">
          <span>🧪 AI生成用例</span>
          <el-tag size="small" type="warning" class="new-tag">新</el-tag>
        </div>
        <div class="tab-item coverage-tab" @click="$router.push('/test-coverage')">
          <span>📐 覆盖率看板</span>
          <el-tag size="small" type="warning" class="new-tag">新</el-tag>
        </div>
        <div
          class="tab-item"
          :class="{ 'active': activeTab === 'mock' }"
          @click="activeTab = 'mock'; handleTabChange('mock')"
        >
          <el-icon><Monitor /></el-icon>
          <span>Mock 服务 <el-tag size="small" type="warning" class="new-tag">新</el-tag></span>
        </div>
        <div
          class="tab-item"
          :class="{ 'active': activeTab === 'suites' }"
          @click="activeTab = 'suites'; handleTabChange('suites')"
        >
          <el-icon><Collection /></el-icon>
          <span>测试套件 <el-tag size="small" type="warning" class="new-tag">新</el-tag></span>
        </div>
        <div class="tab-item" @click="showCurlImport = true">
          <el-icon><Upload /></el-icon>
          <span>导入 cURL</span>
        </div>
      </div>
    </div>

    <div v-if="activeTab === 'interfaces' || visitedTabs.has('interfaces')" v-show="activeTab === 'interfaces'" class="tab-content">
      <InterfaceLibrary
        ref="interfaceLibraryRef"
        :environment-list="environmentList"
        :curl-data="curlImportData"
        @run-cases="handleRunCases"
      />
    </div>

    <div v-if="activeTab === 'scenarios' || visitedTabs.has('scenarios')" v-show="activeTab === 'scenarios'" class="tab-content">
      <div class="scenario-container">
        <ScenarioList
          v-if="!currentScenarioId"
          ref="scenarioListRef"
          @edit="handleEditScenario"
        />
        <ScenarioEditor
          v-else
          :key="currentScenarioId"
          :scenario-id="currentScenarioId"
          @back="handleScenarioBack"
        />
      </div>
    </div>

    <div v-if="activeTab === 'debug' || visitedTabs.has('debug')" v-show="activeTab === 'debug'" class="tab-content">
      <ApiDebugger
        :environment-list="environmentList"
        @case-saved="onCaseSaved"
      />
    </div>

    <div v-if="activeTab === 'variables' || visitedTabs.has('variables')" v-show="activeTab === 'variables'" class="tab-content">
      <GlobalVariableManager />
    </div>

    <div v-if="activeTab === 'dataFactory' || visitedTabs.has('dataFactory')" v-show="activeTab === 'dataFactory'" class="tab-content">
      <DataFactory />
    </div>

    <div v-if="activeTab === 'jmeter' || visitedTabs.has('jmeter')" v-show="activeTab === 'jmeter'" class="tab-content">
      <JmeterAssistant :environment-list="environmentList" />
    </div>

    <div v-if="activeTab === 'mock' || visitedTabs.has('mock')" v-show="activeTab === 'mock'" class="tab-content">
      <MockService />
    </div>

    <div v-if="activeTab === 'suites' || visitedTabs.has('suites')" v-show="activeTab === 'suites'" class="tab-content">
      <SuiteManager />
    </div>

    <CurlImportDialog v-model="showCurlImport" @import="handleCurlImport" />

    <ExecutionResultDialog
      v-model="resultDialogVisible"
      :result="runResult"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Document, FolderOpened, Position, DataAnalysis, Coin, Connection, Monitor, Collection, Upload } from '@element-plus/icons-vue'
import ScenarioList from './ScenarioList.vue'
import ScenarioEditor from './ScenarioEditor.vue'
import GlobalVariableManager from '../components/GlobalVariableManager.vue'
import DataFactory from './DataFactory.vue'
import ApiDebugger from './ApiDebugger.vue'
import InterfaceLibrary from './InterfaceLibrary.vue'
import JmeterAssistant from './JmeterAssistant.vue'
import MockService from './MockService.vue'
import SuiteManager from './SuiteManager.vue'
import CurlImportDialog from './CurlImportDialog.vue'
import ExecutionResultDialog from './ExecutionResultDialog.vue'
import autoTestRequest from '@/utils/autoTestRequest'

const route = useRoute()
const router = useRouter()
const activeTab = ref(route.query.tab || 'debug')
const visitedTabs = ref(new Set([route.query.tab || 'debug']))
const parseScenarioId = (value) => {
  if (value === undefined || value === null || value === '') return null
  const parsed = Number(value)
  return Number.isNaN(parsed) ? value : parsed
}
const currentScenarioId = ref(parseScenarioId(route.query.scenarioId))

const environmentList = ref([])
const scenarioListRef = ref(null)
const interfaceLibraryRef = ref(null)

const showCurlImport = ref(false)
const curlImportData = ref(null)

const resultDialogVisible = ref(false)
const runResult = ref({
  passed: false,
  status: 200,
  time: 0,
  request: {
    method: 'GET',
    url: '',
    headers: {},
    body: ''
  },
  response: {
    data: ''
  },
  passedAssertions: 0,
  totalAssertions: 0,
  assertionResults: [],
  hasError: false,
  errorMessage: null
})

const loadEnvironments = async () => {
  try {
    const res = await autoTestRequest.get('/auto-test/environments')
    environmentList.value = res || []
  } catch (error) {
    console.error('加载环境失败:', error)
  }
}

const syncRouteState = (tab = activeTab.value, scenarioId = currentScenarioId.value) => {
  const nextQuery = { ...route.query, tab }
  if (scenarioId) {
    nextQuery.scenarioId = String(scenarioId)
  } else {
    delete nextQuery.scenarioId
  }
  router.replace({ query: nextQuery })
}

const handleTabChange = (val) => {
  visitedTabs.value = new Set([...visitedTabs.value, val])
  activeTab.value = val
  syncRouteState(val, val === 'scenarios' ? currentScenarioId.value : null)
  if (val === 'scenarios' && scenarioListRef.value) {
    scenarioListRef.value.loadScenarios()
  }
}

const handleRunCases = async (caseData, envId) => {
  try {
    const runRes = await autoTestRequest.post(`/auto-test/cases/${caseData.id}/run`, {
      env_id: envId
    })

    const finalUrl = runRes.request_url || caseData.url || ''
    const finalHeaders = runRes.request_headers || caseData.headers || {}
    const finalParams = runRes.request_params || caseData.params || {}
    const finalBody = runRes.request_body !== undefined ? runRes.request_body : caseData.payload || ''

    const responseData = runRes.response
      ? (typeof runRes.response === 'string' ? runRes.response : JSON.stringify(runRes.response, null, 2))
      : ''

    runResult.value = {
      passed: runRes.success,
      status: runRes.status_code || 0,
      time: runRes.execution_time || 0,
      request: {
        method: runRes.request_method || caseData.method || 'GET',
        url: finalUrl,
        headers: finalHeaders,
        params: finalParams,
        body: typeof finalBody === 'string' ? finalBody : JSON.stringify(finalBody || '')
      },
      response: {
        data: responseData
      },
      hasError: !runRes.success,
      errorMessage: runRes.error || null,
      passedAssertions: runRes.assert_result?.passed ? 1 : 0,
      totalAssertions: 1,
      assertionResults: runRes.assert_result?.details || []
    }
    resultDialogVisible.value = true

    if (interfaceLibraryRef.value) {
      interfaceLibraryRef.value.refreshCaseList()
    }
  } catch (error) {
    let errorMsg = '执行失败'
    if (error.response?.data) {
      if (error.response.data.msg) {
        errorMsg = error.response.data.msg
      } else if (error.response.data.error) {
        errorMsg = error.response.data.error
      } else if (error.response.data.detail) {
        errorMsg = error.response.data.detail
      } else {
        errorMsg = error.message
      }
    } else {
      errorMsg = error.message
    }
    ElMessage.error(errorMsg)
  }
}

const onCaseSaved = () => {
  if (interfaceLibraryRef.value) {
    interfaceLibraryRef.value.refreshCaseList()
  }
}

const handleCurlImport = (parsedData) => {
  // 将解析的 cURL 数据传递给接口库
  curlImportData.value = parsedData
  ElMessage.success('cURL 已解析，请在接口库中创建用例')
  // 切换到接口库标签页
  handleTabChange('interfaces')
}

const handleEditScenario = (scenario) => {
  currentScenarioId.value = Number(scenario?.id) || scenario?.id || null
  activeTab.value = 'scenarios'
  syncRouteState('scenarios', currentScenarioId.value)
}

const handleScenarioBack = () => {
  currentScenarioId.value = null
  syncRouteState('scenarios', null)
}

const showGuide = ref(false)
const guideStep = ref(1)

const guideTips = {
  1: {
    title: '第一步：接口调试',
    desc: '在「接口调试」标签页中，输入一个 API 地址（如 https://httpbin.org/get），选择请求方式，点击「发送请求」查看返回结果。这是接口测试最基本的操作。',
    actionLabel: '去调试',
    action: () => { handleTabChange('debug') },
  },
  2: {
    title: '第二步：创建用例',
    desc: '调试成功的接口可以保存为用例。切换到「接口库」标签页，在左侧创建分组，然后添加接口用例，设置断言规则来验证返回数据。',
    actionLabel: '去接口库',
    action: () => { handleTabChange('interfaces') },
  },
  3: {
    title: '第三步：场景编排',
    desc: '多个接口用例可以编排成测试场景，模拟用户完整操作流程（如：登录→查询→下单→支付）。场景支持步骤间数据传递和条件执行。',
    actionLabel: '去场景管理',
    action: () => { handleTabChange('scenarios') },
  },
  4: {
    title: '第四步：批量执行',
    desc: '创建好场景后，可以一键批量执行所有测试用例，生成测试报告。还可以设置定时任务，让测试自动运行。',
    actionLabel: '去场景管理',
    action: () => { handleTabChange('scenarios') },
  },
  5: {
    title: '第五步：JMeter 压测助手',
    desc: '用可视化 IDE 生成 JMeter 脚本！支持线程组配置、断言、提取器、CSV数据驱动、JDBC等。不会写 JMX？让助手帮你自动生成，还可以从接口库一键导入~',
    actionLabel: '打开助手',
    action: () => { handleTabChange('jmeter') },
  },
}

const guideTip = computed(() => guideTips[guideStep.value])

const initGuide = () => {
  const dismissed = localStorage.getItem('autotest_guide_dismissed')
  if (!dismissed) {
    showGuide.value = true
  }
}

const nextGuideStep = () => {
  if (guideStep.value < 5) {
    guideStep.value++
    const tip = guideTips[guideStep.value]
    if (tip?.action) {
      tip.action()
    }
  } else {
    dismissGuide()
  }
}

const goToGuideStep = (step) => {
  guideStep.value = step
  const tip = guideTips[step]
  if (tip?.action) {
    tip.action()
  }
}

const dismissGuide = () => {
  showGuide.value = false
  localStorage.setItem('autotest_guide_dismissed', 'true')
}

onMounted(() => {
  loadEnvironments()
  if (route.query.tab === 'scenarios' && route.query.scenarioId) {
    currentScenarioId.value = parseScenarioId(route.query.scenarioId)
  }
  initGuide()
})

watch(
  () => route.query.tab,
  (tab) => {
    if (typeof tab === 'string' && tab) {
      activeTab.value = tab
    }
  }
)

watch(
  () => route.query.scenarioId,
  (scenarioId) => {
    currentScenarioId.value = parseScenarioId(scenarioId)
  }
)
</script>

<style scoped>
.beginner-guide-banner {
  background: linear-gradient(135deg, rgba(var(--tm-color-primary-rgb), 0.15), rgba(217, 70, 239, 0.1));
  border-bottom: 1px solid rgba(var(--tm-color-primary-rgb), 0.2);
  padding: 16px 24px;
}

.guide-content {
  display: flex;
  align-items: center;
  gap: 20px;
  max-width: 100%;
  margin: 0;
}

.guide-icon {
  font-size: 36px;
  flex-shrink: 0;
}

.guide-text h3 {
  font-size: 16px;
  font-weight: 700;
  color: var(--tm-text-primary);
  margin: 0 0 2px 0;
}

.guide-text p {
  font-size: 13px;
  color: var(--tm-text-regular);
  margin: 0;
}

.guide-steps {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-left: auto;
}

.guide-step {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border-radius: 20px;
  cursor: pointer;
  transition: all 0.3s ease;
  border: 1px solid rgba(var(--tm-color-primary-rgb), 0.2);
}

.guide-step:hover {
  border-color: rgba(var(--tm-color-primary-rgb), 0.2);
}

.step-num {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: rgba(var(--tm-color-primary-rgb), 0.2);
  color: var(--tm-color-primary);
  font-size: 12px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
}

.guide-step.active .step-num {
  background: linear-gradient(135deg, var(--tm-color-primary), var(--tm-color-primary-dark));
  color: white;
}

.guide-step.done .step-num {
  background: var(--tm-color-primary);
  color: white;
}

.step-label {
  font-size: 13px;
  color: var(--tm-text-regular);
  font-weight: 500;
}

.guide-step.active .step-label {
  color: var(--tm-text-primary);
}

.guide-arrow {
  color: rgba(var(--tm-color-primary-rgb), 0.3);
  font-size: 14px;
}

.guide-close {
  color: var(--tm-text-regular) !important;
  font-size: 16px;
  flex-shrink: 0;
}

.guide-tip-card {
  max-width: 100%;
  margin: 16px 0;
  padding: 16px 20px;
  background: rgba(var(--tm-color-primary-rgb), 0.08);
  border: 1px solid rgba(var(--tm-color-primary-rgb), 0.15);
  border-radius: 12px;
}

.tip-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  color: var(--tm-text-primary);
  font-size: 15px;
}

.tip-icon {
  font-size: 20px;
}

.tip-desc {
  font-size: 14px;
  color: var(--tm-text-regular);
  line-height: 1.6;
  margin: 0 0 12px 0;
}

.tip-actions {
  display: flex;
  gap: 8px;
}

.auto-test-page {
  padding: 0;
  height: calc(100vh - 64px);
  font-family: 'Inter', 'Roboto', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  width: 100%;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.auto-test-page::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, var(--tm-bg-page) 0%, rgba(var(--tm-color-primary-rgb), 0.04) 50%, var(--tm-bg-page) 100%);
  z-index: 1;
  pointer-events: none;
}

.auto-test-page > * {
  position: relative;
  z-index: 2;
}

.page-tabs {
  width: 100%;
  padding: 0 16px;
  margin: 0 auto 12px;
  box-sizing: border-box;
  background: transparent;
  border-bottom: 1px solid var(--border-subtle);
}

.tab-nav {
  display: flex;
  gap: 12px;
  padding: 0 12px;
  border-bottom: 1px solid transparent;
}

.tab-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 20px;
  color: var(--text-secondary);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border-radius: 10px 10px 0 0;
  position: relative;
  bottom: -1px;
  background: var(--tm-card-bg);
  border: 1px solid var(--tm-border-light);
  border-bottom: none;
}

.tab-item:hover {
  color: var(--text-primary);
  background: rgba(var(--tm-color-primary-rgb), 0.1);
  transform: translateY(-2px);
}

.tab-item.active {
  color: var(--text-primary);
  background: rgba(var(--tm-color-primary-rgb), 0.2);
  border-color: var(--tm-color-primary);
}

.tab-item.active::after {
  content: '';
  position: absolute;
  bottom: -1px;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, var(--tm-color-primary), var(--tm-color-primary-dark));
  border-radius: 2px;
  box-shadow: 0 0 10px var(--tm-color-primary);
}

.new-tag { margin-left: 2px; vertical-align: super; font-size: 10px; transform: scale(0.85); }

.tab-group :deep(.el-radio-button__inner) {
  display: flex;
  align-items: center;
  gap: 8px;
  border-radius: 8px;
  background: var(--tm-bg-card);
  border: 1px solid var(--tm-border-light);
  color: var(--tm-text-secondary);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  backdrop-filter: blur(4px);
  -webkit-backdrop-filter: blur(4px);
}

.tab-group :deep(.el-radio-button__inner:hover) {
  color: var(--tm-color-primary);
  border-color: var(--tm-color-primary);
  box-shadow: 0 0 10px rgba(var(--tm-color-primary-rgb), 0.3);
}

.tab-group :deep(.el-radio-button.is-active .el-radio-button__inner) {
  background: linear-gradient(135deg, var(--tm-color-primary), var(--tm-color-primary-dark));
  border-color: var(--tm-color-primary);
  color: white;
  box-shadow: 0 0 15px rgba(var(--tm-color-primary-rgb), 0.5);
  transform: translateY(-1px);
}

.tab-content {
  width: 100%;
  padding: 0 16px;
  margin: 0 auto;
  box-sizing: border-box;
  flex: 1;
  min-height: 0;
  overflow: auto;
  display: flex;
  flex-direction: column;
}

.scenario-container {
  background: var(--tm-bg-card);
  border-radius: 12px;
  padding: 24px;
  min-height: 100%;
  border: 1px solid var(--tm-border-light);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
}

.dark-divider {
  --el-divider-color: var(--tm-border-light);
}

.btn-primary {
  background: linear-gradient(135deg, var(--tm-color-primary), var(--tm-color-primary-dark)) !important;
  border: none !important;
  box-shadow: 0 4px 15px rgba(var(--tm-color-primary-rgb), 0.4) !important;
  border-radius: 8px !important;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
}

.btn-primary:hover {
  background: linear-gradient(135deg, var(--tm-color-primary), var(--tm-color-primary-dark)) !important;
  box-shadow: 0 6px 20px rgba(var(--tm-color-primary-rgb), 0.6) !important;
  transform: translateY(-2px) !important;
}

.btn-cancel {
  color: var(--tm-text-secondary) !important;
  background: var(--tm-bg-card) !important;
  border: 1px solid var(--tm-border-light) !important;
  border-radius: 8px !important;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
  backdrop-filter: blur(4px) !important;
  -webkit-backdrop-filter: blur(4px) !important;
}

.btn-cancel:hover {
  color: var(--tm-text-primary) !important;
  border-color: var(--tm-color-primary) !important;
  box-shadow: 0 0 15px rgba(var(--tm-color-primary-rgb), 0.3) !important;
  transform: translateY(-1px) !important;
}

.dark-table :deep(.el-table) {
  background: transparent !important;
  color: var(--tm-text-primary) !important;
  border-radius: 10px !important;
  overflow: hidden !important;
}

.dark-table :deep(.el-table tr) {
  background: var(--tm-bg-card) !important;
  transition: all 0.3s ease !important;
}

.dark-table :deep(.el-table th) {
  background: rgba(var(--tm-color-primary-rgb), 0.1) !important;
  color: var(--tm-text-secondary) !important;
  font-weight: 600 !important;
  border-bottom: 1px solid var(--tm-border-light) !important;
}

.dark-table :deep(.el-table td) {
  border-bottom: 1px solid var(--tm-border-light) !important;
  color: var(--tm-text-primary) !important;
}

.dark-table :deep(.el-table--border) {
  border-color: var(--tm-border-light) !important;
}

.dark-table :deep(.el-table__row:hover > td) {
  background-color: rgba(var(--tm-color-primary-rgb), 0.15) !important;
}

@media (max-width: 768px) {
  .tab-nav {
    overflow-x: auto;
    padding-bottom: 10px;
    scrollbar-width: none;
    -ms-overflow-style: none;
  }

  .tab-nav::-webkit-scrollbar {
    display: none;
  }

  .tab-item {
    white-space: nowrap;
    padding: 12px 16px;
  }
}

::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

::-webkit-scrollbar-track {
  background: var(--tm-bg-card);
  border-radius: 3px;
}

::-webkit-scrollbar-thumb {
  background: rgba(var(--tm-color-primary-rgb), 0.5);
  border-radius: 3px;
  transition: background 0.3s ease;
}

::-webkit-scrollbar-thumb:hover {
  background: rgba(var(--tm-color-primary-rgb), 0.8);
  box-shadow: 0 0 10px rgba(var(--tm-color-primary-rgb), 0.5);
}

:deep(.el-input__wrapper),
:deep(.el-select__wrapper) {
  background: var(--tm-bg-card) !important;
  border: 1px solid var(--tm-border-light) !important;
  border-radius: 8px !important;
  backdrop-filter: blur(4px) !important;
  -webkit-backdrop-filter: blur(4px) !important;
}

:deep(.el-input__inner),
:deep(.el-select__input) {
  color: var(--tm-text-primary) !important;
}

:deep(.el-input__inner::placeholder),
:deep(.el-select__placeholder) {
  color: var(--tm-text-secondary) !important;
}

:deep(.el-input__wrapper:hover),
:deep(.el-select__wrapper:hover) {
  box-shadow: 0 0 0 1px var(--tm-color-primary) inset, 0 0 15px rgba(var(--tm-color-primary-rgb), 0.3) !important;
}

:deep(.el-select-dropdown) {
  background: var(--tm-bg-card) !important;
  border: 1px solid var(--tm-border-light) !important;
  border-radius: 10px !important;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.08) !important;
  backdrop-filter: blur(15px) !important;
  -webkit-backdrop-filter: blur(15px) !important;
}

:deep(.el-select-dropdown__item) {
  color: var(--tm-text-primary) !important;
  transition: all 0.3s ease !important;
}

:deep(.el-select-dropdown__item:hover) {
  background: rgba(var(--tm-color-primary-rgb), 0.15) !important;
  color: var(--tm-color-primary) !important;
}

:deep(.el-select-dropdown__item.selected) {
  background: rgba(var(--tm-color-primary-rgb), 0.25) !important;
  color: var(--tm-color-primary) !important;
}
</style>
