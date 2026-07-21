<template>
  <div class="suite-manager-page">
    <div class="page-header">
      <div>
        <h2>测试套件管理</h2>
        <p class="subtitle">创建和管理测试套件，批量执行用例</p>
      </div>
      <div class="header-actions">
        <el-select
          v-model="selectedEnvId"
          placeholder="选择执行环境"
          clearable
          style="width: 180px"
        >
          <el-option
            v-for="env in environments"
            :key="env.id"
            :label="env.name || env.env_name"
            :value="env.id"
          />
        </el-select>
        <el-button @click="showHelp = true">❓ 使用说明</el-button>
      </div>
    </div>

    <!-- 套件列表 -->
    <div class="section">
      <div class="section-header">
        <el-button type="primary" @click="openCreateDialog">
          <el-icon><Plus /></el-icon> 新建套件
        </el-button>
      </div>

      <el-table :data="suites" v-loading="loading" stripe>
        <el-table-column prop="name" label="套件名称" min-width="200" />
        <el-table-column prop="description" label="描述" min-width="200" />
        <el-table-column prop="case_count" label="用例数" width="100" align="center" />
        <el-table-column prop="last_status" label="最近状态" width="120" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.last_status === 'passed'" type="success" size="small">通过</el-tag>
            <el-tag v-else-if="row.last_status === 'failed'" type="danger" size="small">失败</el-tag>
            <el-tag v-else-if="row.last_status === 'running'" type="warning" size="small">运行中</el-tag>
            <el-tag v-else-if="row.last_status" :type="executionStatusType(row.last_status)" size="small">{{ executionStatusLabel(row.last_status) }}</el-tag>
            <span v-else class="text-muted">未执行</span>
          </template>
        </el-table-column>
        <el-table-column prop="last_run_at" label="最近执行时间" width="180">
          <template #default="{ row }">{{ row.last_run_at ? formatDate(row.last_run_at) : '-' }}</template>
        </el-table-column>
        <el-table-column label="操作" width="430" fixed="right">
          <template #default="{ row }">
            <el-button text size="small" @click="viewSuite(row)">查看</el-button>
            <el-button text size="small" @click="openRunsDialog(row)">记录</el-button>
            <el-button text size="small" type="primary" @click="runSuite(row)" :loading="row.running">
              执行
            </el-button>
            <el-button text size="small" @click="openScheduleDialog(row)">定时</el-button>
            <el-button text size="small" @click="openWebhookDialog(row)">Webhook</el-button>
            <el-button text size="small" @click="editSuite(row)">编辑</el-button>
            <el-button text size="small" type="danger" @click="deleteSuite(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div v-if="total > 0" class="pagination">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          @size-change="handlePageSizeChange"
          @current-change="loadSuites"
        />
      </div>
    </div>

    <!-- 套件详情对话框 -->
    <el-dialog v-model="showDetailDialog" title="套件详情" width="800px">
      <div v-if="currentSuite">
        <h3>{{ currentSuite.name }}</h3>
        <p class="description">{{ currentSuite.description || '暂无描述' }}</p>

        <h4>关联用例</h4>
        <el-table :data="currentSuite.scenarios || currentSuite.cases || []" stripe size="small">
          <el-table-column prop="case_name" label="场景名称" min-width="200" />
          <el-table-column prop="active" label="可执行" width="90"><template #default="{ row }"><el-tag :type="row.active ? 'success' : 'info'" size="small">{{ row.active ? '是' : '否' }}</el-tag></template></el-table-column>
          <el-table-column prop="method" label="方法" width="100">
            <template #default="{ row }">
              <el-tag :type="getMethodType(row.method)" size="small">{{ row.method }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="url" label="URL" min-width="200"><template #default="{ row }">{{ row.url || '-' }}</template></el-table-column>
          <el-table-column prop="sort_order" label="顺序" width="80" align="center" />
        </el-table>
      </div>
    </el-dialog>

    <el-dialog v-model="showScheduleDialog" title="服务端定时执行" width="580px" destroy-on-close>
      <el-form :model="scheduleForm" label-width="110px">
        <el-form-item label="Cron 表达式" required><el-input v-model="scheduleForm.cron_expression" placeholder="例如：0 9 * * 1-5" /></el-form-item>
        <el-form-item label="时区"><el-select v-model="scheduleForm.timezone_name" style="width:100%"><el-option label="中国标准时间" value="Asia/Shanghai" /><el-option label="协调世界时" value="UTC" /><el-option label="美国太平洋时间" value="America/Los_Angeles" /></el-select></el-form-item>
        <el-form-item label="执行环境"><el-select v-model="scheduleForm.env_id" clearable style="width:100%"><el-option v-for="env in environments" :key="env.id" :label="env.name || env.env_name" :value="env.id" /></el-select></el-form-item>
        <el-form-item label="错过触发"><el-radio-group v-model="scheduleForm.misfire_policy"><el-radio label="coalesce">合并为一次</el-radio><el-radio label="skip">跳过</el-radio></el-radio-group></el-form-item>
        <el-form-item label="最大并发"><el-input-number v-model="scheduleForm.max_concurrent" :min="1" :max="10" /></el-form-item>
        <el-form-item label="执行超时"><el-input-number v-model="scheduleForm.execution_timeout_seconds" :min="30" :max="86400" /><span class="form-tip">秒</span></el-form-item>
        <el-form-item label="失败重试"><el-input-number v-model="scheduleForm.max_retries" :min="0" :max="5" /><span class="form-tip">次；每次都会生成独立执行记录</span></el-form-item>
        <el-form-item label="结果通知"><el-input v-model="scheduleForm.notification_config.webhook_url" type="password" show-password :placeholder="scheduleForm.notification_config.webhook_configured ? `已配置 ${scheduleForm.notification_config.provider_host}，留空保持不变` : '飞书、钉钉或企业微信机器人 HTTPS 地址'" /></el-form-item>
        <el-form-item label="通知状态"><el-checkbox-group v-model="scheduleForm.notification_config.notify_on"><el-checkbox label="passed">通过</el-checkbox><el-checkbox label="failed">失败</el-checkbox><el-checkbox label="timed_out">超时</el-checkbox><el-checkbox label="infra_error">基础设施异常</el-checkbox><el-checkbox label="cancelled">取消</el-checkbox></el-checkbox-group></el-form-item>
        <el-form-item label="启用通知"><el-switch v-model="scheduleForm.notification_config.enabled" /></el-form-item>
        <el-form-item label="启用"><el-switch v-model="scheduleForm.is_active" /></el-form-item>
        <el-descriptions v-if="scheduleMeta" :column="1" border size="small"><el-descriptions-item label="下次执行">{{ scheduleMeta.next_run_at ? formatDate(scheduleMeta.next_run_at) : '-' }}</el-descriptions-item><el-descriptions-item label="最近入队">{{ scheduleMeta.last_enqueued_at ? formatDate(scheduleMeta.last_enqueued_at) : '-' }}</el-descriptions-item></el-descriptions>
      </el-form>
      <template #footer><el-button v-if="scheduleMeta" type="danger" plain @click="removeSchedule">删除定时</el-button><el-button @click="showScheduleDialog=false">取消</el-button><el-button type="primary" :loading="savingSchedule" @click="saveSchedule">保存</el-button></template>
    </el-dialog>

    <el-dialog v-model="showWebhookDialog" title="外部触发 Webhook" width="760px" destroy-on-close>
      <el-alert v-if="webhookSecret" type="warning" :closable="false" show-icon class="secret-alert">
        <template #title>新签名密钥（仅本次显示）</template>
        <el-input :model-value="webhookSecret" readonly />
      </el-alert>
      <el-form :inline="true" :model="webhookForm" class="webhook-create-form">
        <el-form-item label="名称"><el-input v-model="webhookForm.name" maxlength="200" placeholder="例如：主干回归" /></el-form-item>
        <el-form-item label="时间偏差"><el-input-number v-model="webhookForm.allowed_clock_skew_seconds" :min="30" :max="3600" /><span class="form-tip">秒</span></el-form-item>
        <el-form-item><el-button type="primary" :loading="savingWebhook" @click="createWebhook">创建</el-button></el-form-item>
      </el-form>
      <el-table :data="webhooks" v-loading="loadingWebhooks" size="small" empty-text="当前套件还没有外部触发器">
        <el-table-column prop="name" label="名称" min-width="120" />
        <el-table-column prop="inbound_url" label="接收地址" min-width="270"><template #default="{ row }"><code>{{ row.inbound_url }}</code></template></el-table-column>
        <el-table-column label="状态" width="90"><template #default="{ row }"><el-tag :type="row.is_active ? 'success' : 'info'" size="small">{{ row.is_active ? '启用' : '停用' }}</el-tag></template></el-table-column>
        <el-table-column prop="allowed_clock_skew_seconds" label="时间偏差" width="100"><template #default="{ row }">{{ row.allowed_clock_skew_seconds }} 秒</template></el-table-column>
        <el-table-column label="操作" width="205"><template #default="{ row }"><el-button text size="small" @click="showWebhookIntegration(row)">接入信息</el-button><el-button text size="small" @click="toggleWebhook(row)">{{ row.is_active ? '停用' : '启用' }}</el-button><el-button text size="small" @click="rotateWebhookSecret(row)">轮换密钥</el-button></template></el-table-column>
      </el-table>
    </el-dialog>

    <el-dialog v-model="showWebhookIntegrationDialog" title="Webhook 接入信息" width="760px">
      <el-descriptions v-if="webhookIntegration" :column="1" border>
        <el-descriptions-item label="接收地址"><el-input :model-value="absoluteWebhookUrl(webhookIntegration.inbound_url)" readonly><template #append><el-button @click="copyText(absoluteWebhookUrl(webhookIntegration.inbound_url))">复制</el-button></template></el-input></el-descriptions-item>
        <el-descriptions-item label="状态查询"><el-input :model-value="absoluteWebhookUrl(webhookIntegration.status_url_template)" readonly><template #append><el-button @click="copyText(absoluteWebhookUrl(webhookIntegration.status_url_template))">复制</el-button></template></el-input></el-descriptions-item>
        <el-descriptions-item label="签名算法"><code>{{ webhookIntegration.signature_headers?.algorithm }}</code></el-descriptions-item>
        <el-descriptions-item label="请求头"><code>{{ webhookIntegration.signature_headers?.timestamp }}</code> · <code>{{ webhookIntegration.signature_headers?.signature }}</code> · <code>{{ webhookIntegration.signature_headers?.event_id }}</code></el-descriptions-item>
      </el-descriptions>
    </el-dialog>

    <!-- 创建/编辑套件对话框 -->
    <el-dialog v-model="showCreateDialog" :title="editingSuite ? '编辑套件' : '新建套件'" width="600px">
      <el-form :model="suiteForm" label-width="100px">
        <el-form-item label="套件名称" required>
          <el-input v-model="suiteForm.name" placeholder="请输入套件名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="suiteForm.description" type="textarea" :rows="3" placeholder="请输入套件描述" />
        </el-form-item>
        <el-form-item label="默认环境" required><el-select v-model="suiteForm.env_id" placeholder="请选择 Webhook 和定时执行使用的环境" style="width:100%"><el-option v-for="env in environments" :key="env.id" :label="env.name || env.env_name" :value="env.id" /></el-select></el-form-item>
        <el-form-item label="关联用例">
          <el-select
            v-model="suiteForm.scenario_ids"
            multiple
            filterable
            remote
            :remote-method="searchScenarios"
            placeholder="搜索并选择场景"
            style="width: 100%"
          >
            <el-option
              v-for="c in availableCases"
              :key="c.id"
              :label="c.name"
              :value="c.id"
            />
          </el-select>
        </el-form-item>
        <el-alert type="info" :closable="false" show-icon>只会执行启用的场景；停用场景会在详情和执行日志中明确标记。</el-alert>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="saveSuite" :loading="saving">保存</el-button>
      </template>
    </el-dialog>

    <!-- 执行结果对话框 -->
    <el-dialog v-model="showResultDialog" title="执行结果" width="700px">
      <div v-if="executionResult">
        <el-alert v-if="executionResult.status === 'queued' || executionResult.status === 'running' || executionResult.status === 'cancel_requested'" type="info" :closable="false" show-icon>
          <template #title><span>执行正在后台进行，可关闭窗口；稍后可从套件的最近执行记录查看结果。</span><el-button v-if="executionResult.execution_id" text type="danger" @click="cancelExecution(executionResult)">取消执行</el-button></template>
        </el-alert>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="总用例数">{{ executionResult.total_cases }}</el-descriptions-item>
          <el-descriptions-item label="通过数">
            <span class="text-success">{{ executionResult.passed_cases }}</span>
          </el-descriptions-item>
          <el-descriptions-item label="失败数">
            <span class="text-danger">{{ executionResult.failed_cases }}</span>
          </el-descriptions-item>
          <el-descriptions-item label="执行时间">{{ executionResult.duration_ms }}ms</el-descriptions-item>
        </el-descriptions>

        <h4 style="margin-top: 20px;">执行详情</h4>
        <el-table :data="executionResult.case_results || []" stripe size="small">
          <el-table-column prop="case_name" label="用例" min-width="200" />
          <el-table-column prop="status" label="状态" width="100" align="center">
            <template #default="{ row }">
              <el-tag :type="executionStatusType(row.status)" size="small">
                {{ executionStatusLabel(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="duration_ms" label="耗时(ms)" width="100" />
          <el-table-column prop="error" label="错误信息" min-width="200" />
        </el-table>
        <h4 style="margin-top: 20px;">执行事件</h4>
        <el-table :data="executionEvents" size="small" max-height="240" empty-text="暂无执行事件">
          <el-table-column prop="sequence" label="#" width="55" />
          <el-table-column label="时间" width="175"><template #default="{ row }">{{ formatDate(row.created_at) }}</template></el-table-column>
          <el-table-column prop="type" label="事件" min-width="190" />
          <el-table-column prop="level" label="级别" width="80" />
          <el-table-column label="内容" min-width="260" show-overflow-tooltip><template #default="{ row }"><code>{{ JSON.stringify(row.payload || {}) }}</code></template></el-table-column>
        </el-table>
      </div>
    </el-dialog>

    <el-dialog v-model="showRunsDialog" :title="`${runsSuite?.name || ''} · 执行记录`" width="920px">
      <el-table :data="suiteRuns" v-loading="loadingRuns" size="small" max-height="440">
        <el-table-column prop="execution_id" label="执行编号" min-width="215" show-overflow-tooltip />
        <el-table-column label="来源" width="90"><template #default="{ row }">{{ triggerLabel(row.trigger) }}</template></el-table-column>
        <el-table-column label="状态" width="105"><template #default="{ row }"><el-tag :type="executionStatusType(row.status)" size="small">{{ executionStatusLabel(row.status) }}</el-tag></template></el-table-column>
        <el-table-column prop="attempt" label="尝试" width="65" />
        <el-table-column label="开始时间" width="175"><template #default="{ row }">{{ formatDate(row.started_at || row.queued_at) }}</template></el-table-column>
        <el-table-column prop="duration_ms" label="耗时(ms)" width="100" />
        <el-table-column label="操作" width="145"><template #default="{ row }"><el-button text size="small" @click="openRunDetails(row)">详情</el-button><el-button v-if="['queued','running','cancel_requested'].includes(row.status)" text size="small" type="danger" @click="cancelExecution(row)">取消</el-button></template></el-table-column>
      </el-table>
    </el-dialog>
    <HelpDrawer v-model="showHelp" :title="helpData.title" :intro="helpData.intro" :sections="helpData.sections" />
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import autoTestRequest from '@/utils/autoTestRequest'
import { getServerUrl } from '@/utils/server-config'
import HelpDrawer from '@/components/HelpDrawer.vue'
import { helpContent } from '@/utils/help-content'

const API_BASE = '/auto-test/suites'
const SCENARIOS_API = '/auto-test/scenarios'

// 状态
const loading = ref(false)
const saving = ref(false)
const suites = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)

// 对话框状态
const showCreateDialog = ref(false)
const showDetailDialog = ref(false)
const showResultDialog = ref(false)
const editingSuite = ref(null)
const currentSuite = ref(null)
const executionResult = ref(null)
const availableCases = ref([])
const showHelp = ref(false)
const helpData = helpContent.suiteManager
const selectedEnvId = ref(null)
const environments = ref([])
const showScheduleDialog = ref(false)
const savingSchedule = ref(false)
const schedulingSuite = ref(null)
const scheduleMeta = ref(null)
const emptyNotificationConfig = () => ({ enabled: true, webhook_url: '', notify_on: ['failed', 'timed_out', 'infra_error'], webhook_configured: false, provider_host: '' })
const scheduleForm = ref({ cron_expression: '0 9 * * 1-5', timezone_name: 'Asia/Shanghai', env_id: null, misfire_policy: 'coalesce', max_concurrent: 1, execution_timeout_seconds: 1800, max_retries: 0, is_active: true, notification_config: emptyNotificationConfig() })
const showWebhookDialog = ref(false)
const loadingWebhooks = ref(false)
const savingWebhook = ref(false)
const webhookSuite = ref(null)
const webhooks = ref([])
const webhookSecret = ref('')
const webhookForm = ref({ name: '', allowed_clock_skew_seconds: 300 })
const showWebhookIntegrationDialog = ref(false)
const webhookIntegration = ref(null)
const showRunsDialog = ref(false)
const loadingRuns = ref(false)
const runsSuite = ref(null)
const suiteRuns = ref([])
const executionEvents = ref([])
let executionPollingStopped = false
const executionPollTimers = new Map()
let scheduleRequestToken = 0
let webhookRequestToken = 0

// 表单数据
const suiteForm = ref({
  name: '',
  description: '',
  env_id: null,
  scenario_ids: []
})

// 加载套件列表
const loadSuites = async () => {
  loading.value = true
  try {
    const res = await autoTestRequest.get(API_BASE, {
      params: { page: currentPage.value, size: pageSize.value }
    })
    suites.value = res.list || []
    total.value = res.total || 0
  } catch (err) {
    ElMessage.error('加载套件失败: ' + (err.response?.data?.detail || err.message))
  } finally {
    loading.value = false
  }
}

const handlePageSizeChange = () => {
  currentPage.value = 1
  loadSuites()
}

// 搜索场景
const searchScenarios = async (query) => {
  try {
    const res = await autoTestRequest.get(SCENARIOS_API, { params: { keyword: query, page_size: 100 } })
    availableCases.value = Array.isArray(res) ? res : (res.items || [])
  } catch (err) {
    console.error('搜索场景失败:', err)
    availableCases.value = []
  }
}

// 加载环境列表
const loadEnvironments = async () => {
  try {
    const res = await autoTestRequest.get('/auto-test/environments')
    environments.value = Array.isArray(res) ? res : []
    if (selectedEnvId.value == null) selectedEnvId.value = environments.value.find(item => item.is_default)?.id || null
  } catch (err) {
    console.error('加载环境列表失败:', err)
  }
}

// 打开新建对话框（重置表单）
const openCreateDialog = () => {
  editingSuite.value = null
  suiteForm.value = { name: '', description: '', env_id: selectedEnvId.value || environments.value.find(item => item.is_default)?.id || null, scenario_ids: [] }
  showCreateDialog.value = true
}

// 查看套件详情
const viewSuite = async (suite) => {
  try {
    const res = await autoTestRequest.get(`${API_BASE}/${suite.id}`)
    currentSuite.value = res
    showDetailDialog.value = true
  } catch (err) {
    ElMessage.error('获取套件详情失败')
  }
}

// 编辑套件
const editSuite = async (suite) => {
  editingSuite.value = suite
  try {
    const res = await autoTestRequest.get(`${API_BASE}/${suite.id}`)
    const detail = res
    suiteForm.value = {
      name: detail.name,
      description: detail.description,
      env_id: detail.env_id || null,
      scenario_ids: (detail.scenarios || detail.cases || []).map(c => c.scenario_id || c.case_id || c.id)
    }
    // 加载场景选项
    await searchScenarios('')
    showCreateDialog.value = true
  } catch (err) {
    ElMessage.error('获取套件详情失败')
  }
}

const openScheduleDialog = async (suite) => {
  const requestToken = ++scheduleRequestToken
  schedulingSuite.value = suite
  scheduleMeta.value = null
  scheduleForm.value = { cron_expression: '0 9 * * 1-5', timezone_name: 'Asia/Shanghai', env_id: suite.env_id || null, misfire_policy: 'coalesce', max_concurrent: 1, execution_timeout_seconds: 1800, max_retries: 0, is_active: true, notification_config: emptyNotificationConfig() }
  try {
    const res = await autoTestRequest.get(`${API_BASE}/${suite.id}/schedule`)
    if (requestToken !== scheduleRequestToken || schedulingSuite.value?.id !== suite.id) return
    if (res.schedule) {
      scheduleMeta.value = res.schedule
      scheduleForm.value = { ...scheduleForm.value, ...res.schedule, notification_config: { ...emptyNotificationConfig(), ...(res.schedule.notification_config || {}) } }
    }
    showScheduleDialog.value = true
  } catch (err) {
    ElMessage.error('加载定时配置失败: ' + (err.response?.data?.detail || err.message))
  }
}

const saveSchedule = async () => {
  if (!schedulingSuite.value) return
  savingSchedule.value = true
  try {
    const payload = { ...scheduleForm.value, notification_config: { ...scheduleForm.value.notification_config } }
    const notificationWasConfigured = payload.notification_config.webhook_configured
    delete payload.notification_config.webhook_configured
    delete payload.notification_config.provider_host
    if (!payload.notification_config.webhook_url && !notificationWasConfigured) delete payload.notification_config
    const res = await autoTestRequest.put(`${API_BASE}/${schedulingSuite.value.id}/schedule`, payload)
    scheduleMeta.value = res.schedule
    scheduleForm.value = { ...scheduleForm.value, ...res.schedule, notification_config: { ...emptyNotificationConfig(), ...(res.schedule.notification_config || {}) } }
    ElMessage.success('定时配置已保存')
  } catch (err) {
    ElMessage.error('保存定时配置失败: ' + (err.response?.data?.detail || err.message))
  } finally {
    savingSchedule.value = false
  }
}

const removeSchedule = async () => {
  if (!schedulingSuite.value) return
  try {
    await ElMessageBox.confirm('删除后不会再自动执行该套件，确定继续吗？', '删除定时', { type: 'warning' })
    await autoTestRequest.delete(`${API_BASE}/${schedulingSuite.value.id}/schedule`)
    scheduleMeta.value = null
    ElMessage.success('定时配置已删除')
  } catch (err) {
    if (err !== 'cancel') ElMessage.error('删除定时配置失败: ' + (err.response?.data?.detail || err.message))
  }
}

const loadWebhooks = async (expectedSuite = webhookSuite.value) => {
  if (!expectedSuite) return
  const requestToken = ++webhookRequestToken
  loadingWebhooks.value = true
  try {
    const response = await autoTestRequest.get('/auto-test/webhooks', { params: { suite_id: expectedSuite.id } })
    if (requestToken !== webhookRequestToken || webhookSuite.value?.id !== expectedSuite.id) return
    webhooks.value = response.items || []
  } catch (err) {
    ElMessage.error('加载 Webhook 失败: ' + (err.response?.data?.detail || err.message))
  } finally {
    if (requestToken === webhookRequestToken) loadingWebhooks.value = false
  }
}

const openWebhookDialog = async (suite) => {
  webhookSuite.value = suite
  webhookSecret.value = ''
  webhookForm.value = { name: `${suite.name} 外部触发`, allowed_clock_skew_seconds: 300 }
  showWebhookDialog.value = true
  await loadWebhooks(suite)
}

const createWebhook = async () => {
  if (!webhookSuite.value || !webhookForm.value.name.trim()) {
    ElMessage.warning('请填写 Webhook 名称')
    return
  }
  savingWebhook.value = true
  try {
    const created = await autoTestRequest.post('/auto-test/webhooks', {
      suite_id: webhookSuite.value.id,
      name: webhookForm.value.name.trim(),
      allowed_clock_skew_seconds: webhookForm.value.allowed_clock_skew_seconds,
    })
    webhookSecret.value = created.signing_secret || ''
    webhookIntegration.value = created
    await loadWebhooks()
    ElMessage.success('Webhook 已创建')
  } catch (err) {
    ElMessage.error('创建 Webhook 失败: ' + (err.response?.data?.detail || err.message))
  } finally {
    savingWebhook.value = false
  }
}

const absoluteWebhookUrl = (path) => {
  if (!path) return ''
  if (/^https?:\/\//i.test(path)) return path
  const origin = import.meta.env.VITE_DESKTOP_BUILD === 'true' ? getServerUrl() : window.location.origin
  return new URL(path, `${origin.replace(/\/$/, '')}/`).toString()
}

const copyText = async (value) => {
  try {
    if (navigator.clipboard?.writeText) await navigator.clipboard.writeText(value)
    else {
      const input = document.createElement('textarea')
      input.value = value
      input.style.position = 'fixed'
      input.style.opacity = '0'
      document.body.appendChild(input)
      input.select()
      document.execCommand('copy')
      input.remove()
    }
    ElMessage.success('已复制')
  } catch {
    ElMessage.error('复制失败，请手工选择文本')
  }
}

const showWebhookIntegration = (webhook) => {
  webhookIntegration.value = webhook
  showWebhookIntegrationDialog.value = true
}

const toggleWebhook = async (webhook) => {
  try {
    await autoTestRequest.patch(`/auto-test/webhooks/${webhook.id}`, { is_active: !webhook.is_active })
    await loadWebhooks()
  } catch (err) {
    ElMessage.error('更新 Webhook 失败: ' + (err.response?.data?.detail || err.message))
  }
}

const rotateWebhookSecret = async (webhook) => {
  try {
    await ElMessageBox.confirm('轮换后旧密钥会立即失效，确定继续吗？', '轮换签名密钥', { type: 'warning' })
    const response = await autoTestRequest.post(`/auto-test/webhooks/${webhook.id}/rotate-secret`)
    webhookSecret.value = response.signing_secret || ''
    webhookIntegration.value = response
    await loadWebhooks()
    ElMessage.success('签名密钥已轮换')
  } catch (err) {
    if (err !== 'cancel') ElMessage.error('轮换密钥失败: ' + (err.response?.data?.detail || err.message))
  }
}

// 保存套件
const saveSuite = async () => {
    if (!suiteForm.value.name) {
    ElMessage.warning('请输入套件名称')
      return
    }
  if (!suiteForm.value.env_id) {
    ElMessage.warning('请选择默认执行环境')
    return
  }
  saving.value = true
  try {
    if (editingSuite.value) {
      await autoTestRequest.put(`${API_BASE}/${editingSuite.value.id}`, {
        name: suiteForm.value.name,
        description: suiteForm.value.description,
        env_id: suiteForm.value.env_id,
        scenario_ids: suiteForm.value.scenario_ids
      })
      ElMessage.success('套件更新成功')
    } else {
      await autoTestRequest.post(API_BASE, suiteForm.value)
      ElMessage.success('套件创建成功')
    }
    showCreateDialog.value = false
    editingSuite.value = null
    suiteForm.value = { name: '', description: '', env_id: null, scenario_ids: [] }
    await loadSuites()
  } catch (err) {
    ElMessage.error('保存失败: ' + (err.response?.data?.detail || err.message))
  } finally {
    saving.value = false
  }
}

// 执行套件
const terminalExecutionStatuses = new Set(['passed', 'failed', 'cancelled', 'timed_out', 'infra_error'])

const executionStatusLabel = (status) => ({
  passed: '通过', failed: '失败', cancelled: '已取消', timed_out: '已超时', infra_error: '基础设施异常',
  queued: '排队中', running: '运行中', cancel_requested: '取消中'
}[status] || status || '-')

const executionStatusType = (status) => ({
  passed: 'success', failed: 'danger', cancelled: 'info', timed_out: 'warning', infra_error: 'danger',
  queued: 'info', running: 'warning', cancel_requested: 'warning'
}[status] || 'info')

const triggerLabel = (trigger) => ({ manual: '手工', schedule: '定时', webhook: 'Webhook', retry: '重试' }[trigger] || trigger || '-')

const loadExecutionEvents = async (executionId) => {
  if (!executionId) { executionEvents.value = []; return }
  try {
    const response = await autoTestRequest.get(`${API_BASE}/executions/${executionId}/events`, { params: { limit: 500 } })
    executionEvents.value = response.events || []
  } catch (err) {
    executionEvents.value = []
    ElMessage.error('加载执行事件失败: ' + (err.response?.data?.detail || err.message))
  }
}

const openRunsDialog = async (suite) => {
  runsSuite.value = suite
  suiteRuns.value = []
  showRunsDialog.value = true
  loadingRuns.value = true
  try {
    const response = await autoTestRequest.get(`${API_BASE}/${suite.id}/runs`)
    if (runsSuite.value?.id === suite.id) suiteRuns.value = response.runs || []
  } catch (err) {
    ElMessage.error('加载执行记录失败: ' + (err.response?.data?.detail || err.message))
  } finally {
    if (runsSuite.value?.id === suite.id) loadingRuns.value = false
  }
}

const openRunDetails = async (run) => {
  try {
    executionResult.value = await autoTestRequest.get(`${API_BASE}/executions/${run.execution_id}`)
    await loadExecutionEvents(run.execution_id)
    showResultDialog.value = true
  } catch (err) {
    ElMessage.error('加载执行详情失败: ' + (err.response?.data?.detail || err.message))
  }
}

const cancelExecution = async (execution) => {
  if (!execution?.execution_id) return
  try {
    await ElMessageBox.confirm('确定取消当前执行吗？已经完成的步骤不会回滚。', '取消执行', { type: 'warning' })
    executionResult.value = await autoTestRequest.post(`/auto-test/suites/executions/${execution.execution_id}/cancel`)
    await loadExecutionEvents(execution.execution_id)
    if (runsSuite.value) await openRunsDialog(runsSuite.value)
    ElMessage.success('取消请求已提交')
  } catch (err) {
    if (err !== 'cancel' && err !== 'close') ElMessage.error('取消执行失败: ' + (err.response?.data?.detail || err.message))
  }
}

const waitForExecution = async (executionId) => {
  const deadline = Date.now() + 30 * 60 * 1000
  let result = null
  while (Date.now() < deadline) {
    result = await autoTestRequest.get(`${API_BASE}/executions/${executionId}`)
    if (terminalExecutionStatuses.has(result.status)) return result
    await new Promise(resolve => {
      const timer = window.setTimeout(() => {
        executionPollTimers.delete(timer)
        resolve()
      }, 1000)
      executionPollTimers.set(timer, resolve)
    })
    if (executionPollingStopped) throw new Error('页面已离开，已停止等待执行结果')
  }
  throw new Error('执行等待超时，请在执行记录中查看最终状态')
}

const runSuite = async (suite) => {
  if (!selectedEnvId.value) {
    ElMessage.warning('请先选择执行环境')
    return
  }
  suite.running = true
  let monitoring = false
  try {
    const payload = { env_id: selectedEnvId.value }
    const res = await autoTestRequest.post(`${API_BASE}/${suite.id}/run`, payload)
    executionResult.value = res
    executionEvents.value = []
    showResultDialog.value = true
    await loadSuites()
    if (res.execution_id) {
      monitoring = true
      void monitorExecution(suite, res.execution_id)
    }
  } catch (err) {
    ElMessage.error('执行失败: ' + (err.response?.data?.detail || err.message))
  } finally {
    if (!monitoring) suite.running = false
  }
}

const monitorExecution = async (suite, executionId) => {
  try {
    const result = await waitForExecution(executionId)
    if (executionResult.value?.execution_id === executionId) executionResult.value = result
    await loadExecutionEvents(executionId)
    await loadSuites()
  } catch (err) {
    if (!executionPollingStopped) ElMessage.error('执行状态更新失败: ' + (err.response?.data?.detail || err.message))
  } finally {
    suite.running = false
  }
}

// 删除套件
const deleteSuite = async (suite) => {
  try {
    await ElMessageBox.confirm('确定要删除该套件吗？', '确认删除', { type: 'warning' })
    await autoTestRequest.delete(`${API_BASE}/${suite.id}`)
    ElMessage.success('删除成功')
    await loadSuites()
  } catch (err) {
    if (err !== 'cancel') {
      ElMessage.error('删除失败: ' + (err.response?.data?.detail || err.message))
    }
  }
}

// 工具函数
const getMethodType = (method) => {
  const types = { GET: 'success', POST: 'primary', PUT: 'warning', DELETE: 'danger', PATCH: 'info' }
  return types[method] || 'info'
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN')
}

// 初始化
onMounted(() => {
  executionPollingStopped = false
  loadSuites()
  searchScenarios('')
  loadEnvironments()
})

onUnmounted(() => {
  executionPollingStopped = true
  executionPollTimers.forEach((resolve, timer) => {
    window.clearTimeout(timer)
    resolve()
  })
  executionPollTimers.clear()
})
</script>

<style scoped>
.suite-manager-page {
  padding: 20px;
  width: 100%;
}
.secret-alert { margin-bottom: 16px; }
.webhook-create-form { margin-bottom: 10px; }
.form-tip { margin-left: 8px; color: var(--el-text-color-secondary); font-size: 12px; }

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
}

.page-header h2 {
  margin: 0 0 8px 0;
  font-size: 24px;
  color: var(--tm-text-primary);
}

.page-header .subtitle {
  margin: 0;
  color: var(--tm-text-secondary);
  font-size: 14px;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.section {
  margin-bottom: 30px;
  background: var(--tm-card-bg);
  border: 1px solid var(--tm-border-light);
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
}

.section-header {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  margin-bottom: 20px;
}

.section-header h3 {
  margin: 0;
  font-size: 18px;
  color: var(--tm-text-primary);
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

:deep(.el-table__header-wrapper th.el-table__cell) {
  color: var(--tm-text-primary);
  background: var(--bg-surface-hover);
}

.description {
  color: var(--tm-text-secondary);
  margin-bottom: 20px;
}

.text-muted {
  color: var(--tm-text-secondary);
}

.text-success {
  color: #67c23a;
  font-weight: bold;
}

.text-danger {
  color: #f56c6c;
  font-weight: bold;
}
</style>
