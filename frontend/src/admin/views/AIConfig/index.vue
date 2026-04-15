<template>
  <div class="ai-dashboard">
    <div class="dashboard-header">
      <div class="header-left">
        <div class="logo-icon">
          <svg viewBox="0 0 24 24" fill="none" width="28" height="28">
            <rect x="3" y="3" width="18" height="18" rx="4" fill="#00D9C0" opacity="0.15"/>
            <path d="M8 12L11 15L16 9" stroke="#00D9C0" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </div>
        <h1 class="header-title">AI 大模型监控中心</h1>
        <span class="header-sub">实时监控 API 使用情况及配置状态</span>
      </div>
      <div class="header-right">
        <span v-if="activeConfig" class="active-model-badge">{{ activeConfig.model }}</span>
        <el-button type="primary" @click="handleAdd" class="add-btn">
          <el-icon><Plus /></el-icon> 添加配置
        </el-button>
      </div>
    </div>

    <div class="dashboard-body">
      <div class="left-panel">
        <div class="gauge-card">
          <div class="gauge-ring">
            <svg viewBox="0 0 120 120" class="gauge-svg">
              <circle cx="60" cy="60" r="52" fill="none" stroke="#1a1a2e" stroke-width="10"/>
              <circle cx="60" cy="60" r="52" fill="none"
                :stroke="quotaColor(activeConfig)"
                stroke-width="10"
                :stroke-dasharray="`${quotaPercent * 3.27} 327`"
                stroke-linecap="round"
                transform="rotate(-90 60 60)"/>
            </svg>
            <div class="gauge-center">
              <span class="gauge-value">{{ quotaPercent.toFixed(1) }}%</span>
              <span class="gauge-label">已用额度</span>
            </div>
          </div>
        </div>

        <div class="stat-cards-vertical">
          <div class="stat-mini-card">
            <span class="stat-label">总额度</span>
            <span class="stat-value cyan">{{ formatQuota(activeConfig?.quota_total) }}</span>
          </div>
          <div class="stat-mini-card">
            <span class="stat-label">已使用</span>
            <span class="stat-value green">{{ formatQuota(activeConfig?.quota_used) }}</span>
          </div>
          <div class="stat-mini-card">
            <span class="stat-label">剩余额度</span>
            <span class="stat-value yellow">{{ formatQuota(remainingQuota) }}</span>
          </div>
          <div class="stat-mini-card">
            <span class="stat-label">连接状态</span>
            <span class="stat-value" :class="connectionStatusClass">{{ connectionStatusText }}</span>
          </div>
          <div class="stat-mini-card" v-if="activeConfig?.quota_updated_at">
            <span class="stat-label">更新时间</span>
            <span class="stat-value small">{{ formatTimeShort(activeConfig.quota_updated_at) }}</span>
          </div>
        </div>

        <div class="action-btns-vertical">
          <button v-if="activeConfig" class="action-pill primary" @click="handleTestConnection(activeConfig)" :disabled="testingId === activeConfig.id">
            {{ testingId === activeConfig.id ? '测试中...' : '连接测试' }}
          </button>
          <button v-if="activeConfig && activeConfig.provider === 'minimax'" class="action-pill warning" @click="handleQueryQuota(activeConfig)" :disabled="quotaLoadingId === activeConfig.id">
            {{ quotaLoadingId === activeConfig.id ? '查询中...' : '刷新额度' }}
          </button>
          <button class="action-pill default" @click="dialogVisible = true; handleAdd()">
            配置管理
          </button>
        </div>
      </div>

      <div class="center-panel">
        <div class="panel-title-row">
          <span class="panel-icon">&#128203;</span>
          <span class="panel-title">模型配置列表</span>
          <span class="panel-count">{{ configs.length }} 个配置</span>
        </div>
        <div class="config-grid">
          <div v-for="cfg in configs" :key="cfg.id"
               class="model-card"
               :class="{ 'card-active': cfg.is_active, 'card-success': cfg.last_test_result === 'success', 'card-error': cfg.last_test_result === 'failed' }">
            <div class="card-top">
              <div class="card-name-row">
                <span class="card-model-name">{{ cfg.name }}</span>
                <el-tag v-if="cfg.is_active" size="small" effect="dark" type="success">运行中</el-tag>
                <el-tag v-else size="small" effect="dark" type="info">待机</el-tag>
              </div>
              <div class="card-provider">{{ providerLabel(cfg.provider) }}</div>
            </div>
            <div class="card-body-info">
              <div class="info-row">
                <span class="info-k">模型</span>
                <span class="info-v mono">{{ cfg.model }}</span>
              </div>
              <div class="info-row">
                <span class="info-k">时间</span>
                <span class="info-v">{{ formatTimeShort(cfg.created_at) }}</span>
              </div>
              <div class="info-row">
                <span class="info-k">温度</span>
                <span class="info-v">{{ cfg.temperature }}</span>
              </div>
              <div class="info-row">
                <span class="info-k">Token限制</span>
                <span class="info-v">{{ cfg.max_tokens }}</span>
              </div>
              <div class="info-row">
                <span class="info-k">API Key</span>
                <span class="info-v mono small">{{ cfg.api_key_preview }}</span>
              </div>
              <div class="info-row" v-if="cfg.group_id">
                <span class="info-k">Group ID</span>
                <span class="info-v mono small">{{ cfg.group_id }}</span>
              </div>
            </div>
            <div class="card-bottom">
              <div class="usage-bar-wrap">
                <span class="bar-label">测试状态</span>
                <div class="mini-bar" :class="cfg.last_test_result || 'unknown'"></div>
                <span class="bar-text">{{ cfg.last_test_result === 'success' ? '通过' : cfg.last_test_result === 'failed' ? '失败' : '未测试' }}</span>
              </div>
              <div class="card-actions">
                <button class="card-btn test" @click="handleTestConnection(cfg)" :disabled="testingId === cfg.id">
                  {{ testingId === cfg.id ? '...' : '测试' }}
                </button>
                <button v-if="!cfg.is_active" class="card-btn activate" @click="handleActivate(cfg)">激活</button>
                <button class="card-btn edit" @click="handleEdit(cfg)">编辑</button>
                <button class="card-btn del" @click="handleDelete(cfg)" :disabled="cfg.is_active">删除</button>
              </div>
            </div>
          </div>

          <div v-if="configs.length === 0" class="empty-grid-slot" @click="handleAdd">
            <span class="empty-plus">+</span>
            <span class="empty-text">添加AI配置</span>
          </div>
        </div>
      </div>

      <div class="right-panel">
        <div class="info-card" v-if="activeConfig">
          <div class="info-card-header">
            <span class="info-bolt">&#9889;</span>
            <span class="info-title">{{ activeConfig.model }} 套餐信息</span>
          </div>
          <div class="info-body">
            <div class="info-item-large">
              <span class="ilabel">提供商</span>
              <span class="ivalue">{{ providerLabel(activeConfig.provider) }}</span>
            </div>
            <div class="info-item-large">
              <span class="ilabel">Base URL</span>
              <span class="ivalue mono-sm">{{ activeConfig.base_url || '默认' }}</span>
            </div>
            <div class="info-item-large">
              <span class="ilabel">Group ID</span>
              <span class="ivalue mono-sm">{{ activeConfig.group_id || '未设置' }}</span>
            </div>
            <div class="info-item-large">
              <span class="ilabel">最后测试</span>
              <span class="ivalue">{{ activeConfig.last_test_at ? formatTimeShort(activeConfig.last_test_at) : '从未' }}</span>
            </div>
          </div>
        </div>

        <div class="metric-card" v-if="testResultData">
          <div class="metric-title">测试结果</div>
          <div class="metric-body">
            <div class="metric-big-num" :class="testResultData.status === 'success' ? 'success-color' : 'error-color'">
              {{ testResultData.status === 'success' ? 'OK' : 'FAIL' }}
            </div>
            <div class="metric-detail" v-if="testResultData.reply">
              <p>回复: {{ testResultData.reply.slice(0, 80) }}</p>
            </div>
            <div class="metric-detail error-detail" v-if="testResultData.error">
              <p>{{ testResultData.error.slice(0, 100) }}</p>
            </div>
          </div>
        </div>

        <div class="metric-card" v-if="quotaResultData">
          <div class="metric-title">额度详情</div>
          <div class="metric-body">
            <div class="metric-big-num success-color">{{ formatQuota(quotaResultData.total_balance) }}</div>
            <div class="metric-sub">总余额</div>
            <div class="metric-row-s">
              <span>已用: <b>{{ formatQuota(quotaResultData.used_balance) }}</b></span>
            </div>
          </div>
        </div>

        <div class="config-test-area" v-if="activeConfig">
          <div class="cta-title">快速操作</div>
          <button class="cta-btn primary-cta" @click="handleTestConnection(activeConfig)">
            &#9889; 连接测试
          </button>
          <button v-if="activeConfig.provider === 'minimax'" class="cta-btn warn-cta" @click="handleQueryQuota(activeConfig)">
            &#128200; 刷新额度
          </button>
        </div>

        <div class="no-active-hint" v-if="!activeConfig">
          <p>当前没有激活的AI配置</p>
          <button class="cta-btn primary-cta" @click="handleAdd">添加并激活配置</button>
        </div>
      </div>
    </div>

    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑AI配置' : '添加AI配置'" width="620px" :close-on-click-modal="false" @closed="resetForm" custom-class="mm-dialog">
      <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
        <el-form-item label="配置名称" prop="name">
          <el-input v-model="form.name" placeholder="如: MiniMax Coding Plan" class="mm-input" />
        </el-form-item>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="提供商" prop="provider">
              <el-select v-model="form.provider" style="width:100%" class="mm-select" @change="onProviderChange">
                <el-option label="MiniMax" value="minimax" />
                <el-option label="OpenAI" value="openai" />
                <el-option label="火山方舟(Ark)" value="ark" />
                <el-option label="自定义(OpenAI兼容)" value="custom" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="模型名称" prop="model">
              <el-input v-model="form.model" :placeholder="modelPlaceholder" class="mm-input" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="API Key" prop="api_key">
          <el-input v-model="form.api_key" type="password" show-password placeholder="输入API密钥" class="mm-input" />
        </el-form-item>
        <el-form-item v-if="form.provider === 'minimax'" label="Group ID">
          <el-input v-model="form.group_id" placeholder="MiniMax Group ID（在控制台获取）" class="mm-input" />
        </el-form-item>
        <el-form-item label="Base URL">
          <el-input v-model="form.base_url" :placeholder="baseUrlPlaceholder" class="mm-input" />
        </el-form-item>
        <el-row :gutter="16">
          <el-col :span="8">
            <el-form-item label="Max Tokens">
              <el-input-number v-model="form.max_tokens" :min="100" :max="32000" :step="500" style="width:100%" controls-position="right" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="Temperature">
              <el-slider v-model="form.temperature" :min="0" :max="2" :step="0.1" :show-tooltip="true" style="padding: 0 5px;" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="超时(秒)">
              <el-input-number v-model="form.timeout_seconds" :min="5" :max="300" :step="5" style="width:100%" controls-position="right" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false" class="mm-cancel">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit" class="mm-save">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="testResultVisible" title="连接测试结果" width="480px" custom-class="mm-dialog">
      <div v-if="testResult" class="result-display">
        <el-result :icon="testResult.status === 'success' ? 'success' : 'error'"
                   :title="testResult.status === 'success' ? '连接成功' : '连接失败'">
          <template #sub-title>
            <div v-if="testResult.status === 'success'" class="result-success-body">
              <p><b>模型:</b> {{ testResult.model }}</p>
              <p><b>提供商:</b> {{ testResult.provider }}</p>
              <p><b>AI回复:</b> {{ testResult.reply }}</p>
            </div>
            <div v-else class="result-error-body">
              <p class="err-msg">{{ testResult.error }}</p>
            </div>
          </template>
        </el-result>
      </div>
    </el-dialog>

    <el-dialog v-model="quotaResultVisible" title="额度查询结果" width="480px" custom-class="mm-dialog">
      <div v-if="quotaResult" class="result-display">
        <div v-if="quotaResult.total_balance !== undefined" class="quota-result-body">
          <div class="qr-big">
            <span class="qr-label">总余额</span>
            <span class="qr-val">{{ quotaResult.total_balance }}</span>
          </div>
          <div class="qr-big">
            <span class="qr-label">已使用</span>
            <span class="qr-val used">{{ quotaResult.used_balance }}</span>
          </div>
        </div>
        <div v-else-if="quotaResult.error" class="result-error-body">
          <p class="err-msg">{{ quotaResult.error }}</p>
        </div>
        <div v-else class="result-neutral-body">
          <p>{{ quotaResult.message || '该提供商暂不支持额度查询' }}</p>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import request from '@/utils/request'

const configs = ref([])
const loading = ref(false)
const activeConfig = computed(() => configs.value.find(c => c.is_active))
const testingId = ref(null)
const quotaLoadingId = ref(null)
const testResult = ref(null)
const testResultVisible = ref(false)
const testResultData = ref(null)
const quotaResult = ref(null)
const quotaResultVisible = ref(false)
const quotaResultData = ref(null)

const fetchConfigs = async () => {
  loading.value = true
  try {
    const res = await request.get('/admin/ai-configs')
    configs.value = res?.data || []
  } catch (e) {
    ElMessage.error('获取AI配置失败')
  } finally {
    loading.value = false
  }
}

onMounted(fetchConfigs)

const providerLabel = p => ({ minimax: 'MiniMax', openai: 'OpenAI', ark: '火山方舟', custom: '自定义' }[p] || p)
const formatTimeShort = t => t ? new Date(t).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' }) : ''
const formatQuota = v => v != null ? Number(v).toLocaleString() : '--'

const quotaPercent = computed(() => {
  if (!activeConfig.value || activeConfig.value.quota_total == null) return 0
  return Math.min((activeConfig.value.quota_used / activeConfig.value.quota_total) * 100, 99.9)
})

const remainingQuota = computed(() => {
  if (!activeConfig.value) return null
  const t = activeConfig.value.quota_total
  const u = activeConfig.value.quota_used
  if (t == null || u == null) return null
  return Math.max(t - u, 0)
})

const connectionStatusText = computed(() => {
  if (!activeConfig.value) return '未配置'
  if (activeConfig.value.last_test_result === 'success') return '正常'
  if (activeConfig.value.last_test_result === 'failed') return '异常'
  return '未测试'
})

const connectionStatusClass = computed(() => {
  if (!activeConfig.value) return 'gray'
  if (activeConfig.value.last_test_result === 'success') return 'green'
  if (activeConfig.value.last_test_result === 'failed') return 'red'
  return 'yellow'
})

const quotaColor = (cfg) => {
  if (!cfg || cfg.quota_total == null) return '#333'
  const pct = (cfg.quota_used / cfg.quota_total) * 100
  if (pct > 90) return '#ff4757'
  if (pct > 70) return '#ffa502'
  return '#00d9c0'
}

const handleTestConnection = async (cfg) => {
  testingId.value = cfg.id
  try {
    const res = await request.post(`/admin/ai-configs/${cfg.id}/test`)
    testResult.value = res?.data || res
    testResultData.value = res?.data || res
    testResultVisible.value = true
    if (res?.data?.status === 'success') ElMessage.success('连接成功')
    else ElMessage.warning('连接失败')
    fetchConfigs()
  } catch (e) {
    ElMessage.error('测试请求异常')
  } finally {
    testingId.value = null
  }
}

const handleQueryQuota = async (cfg) => {
  quotaLoadingId.value = cfg.id
  try {
    const res = await request.get(`/admin/ai-configs/${cfg.id}/quota`)
    quotaResult.value = res?.data || res
    quotaResultData.value = res?.data || res
    quotaResultVisible.value = true
    fetchConfigs()
  } catch (e) {
    ElMessage.error('额度查询异常')
  } finally {
    quotaLoadingId.value = null
  }
}

const handleActivate = async (cfg) => {
  try {
    await request.post(`/admin/ai-configs/${cfg.id}/activate`)
    ElMessage.success(`已激活: ${cfg.name}`)
    fetchConfigs()
  } catch (e) {
    ElMessage.error('激活失败')
  }
}

const handleDelete = async (cfg) => {
  await ElMessageBox.confirm(`确定删除「${cfg.name}」?`, '确认', { confirmButtonText: '删除', cancelButtonType: 'cancel', type: 'warning' })
  try {
    await request.delete(`/admin/ai-configs/${cfg.id}`)
    ElMessage.success('已删除')
    fetchConfigs()
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || '删除失败')
  }
}

const dialogVisible = ref(false)
const isEdit = ref(false)
const submitting = ref(false)
const formRef = ref(null)

const defaultForm = () => ({
  id: null, name: '', provider: 'minimax', api_key: '',
  base_url: '', model: '', max_tokens: 2000,
  temperature: 0.7, timeout_seconds: 60, group_id: ''
})
const form = reactive(defaultForm())
const rules = {
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
  provider: [{ required: true, message: '请选择提供商', trigger: 'change' }],
  api_key: [{ required: true, message: '请输入API Key', trigger: 'blur' }],
  model: [{ required: true, message: '请输入模型名', trigger: 'blur' }],
}
const baseUrlPlaceholder = computed(() => ({ minimax: 'https://api.minimax.chat/v1', openai: 'https://api.openai.com/v1', ark: 'https://ark.cn-beijing.volces.com/api/v3', custom: '输入兼容OpenAI的API地址' }[form.provider] || ''))
const modelPlaceholder = computed(() => ({ minimax: '如: MiniMax-M2.7', openai: '如: gpt-4o', ark: '如: doubao-pro-32k', custom: '输入模型名称' }[form.provider] || ''))

const onProviderChange = (val) => {
  const defaults = {
    minimax: { base_url: 'https://api.minimax.chat/v1', model: 'MiniMax-M2.7' },
    openai: { base_url: 'https://api.openai.com/v1', model: 'gpt-4o' },
    ark: { base_url: 'https://ark.cn-beijing.volces.com/api/v3', model: 'doubao-pro-32k' },
    custom: { base_url: '', model: '' }
  }
  const d = defaults[val] || {}
  form.base_url = d.base_url || ''
  form.model = d.model || ''
}

const resetForm = () => { Object.assign(form, defaultForm()); formRef.value?.clearValidate() }

const handleAdd = () => { isEdit.value = false; resetForm(); dialogVisible.value = true }

const handleEdit = (cfg) => {
  isEdit.value = true; resetForm()
  Object.assign(form, {
    id: cfg.id, name: cfg.name, provider: cfg.provider, api_key: '',
    base_url: cfg.base_url || '', model: cfg.model,
    max_tokens: cfg.max_tokens, temperature: cfg.temperature,
    timeout_seconds: cfg.timeout_seconds, group_id: cfg.group_id || ''
  })
  dialogVisible.value = true
}

const handleSubmit = async () => {
  await formRef.value.validate()
  submitting.value = true
  try {
    const payload = { ...form }
    if (!payload.base_url) delete payload.base_url
    if (!payload.group_id) delete payload.group_id
    if (isEdit.value) { if (!payload.api_key) delete payload.api_key; await request.put(`/admin/ai-configs/${form.id}`, payload); ElMessage.success('更新成功') }
    else { await request.post('/admin/ai-configs', payload); ElMessage.success('创建成功') }
    dialogVisible.value = false; fetchConfigs()
  } catch (e) { ElMessage.error(e?.response?.data?.detail || '保存失败') }
  finally { submitting.value = false }
}
</script>

<style scoped>
.ai-dashboard {
  min-height: 100%;
  background: #0a0a14;
  color: #e0e0e0;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  background: linear-gradient(135deg, #0f1020 0%, #141428 100%);
  border-bottom: 1px solid rgba(0,217,192,0.15);
  border-radius: 12px 12px 0 0;
}
.header-left { display: flex; align-items: center; gap: 12px; }
.logo-icon { display: flex; align-items: center; }
.header-title { margin: 0; font-size: 22px; font-weight: 700; color: #fff; letter-spacing: 0.5px; }
.header-sub { font-size: 12px; color: #667; margin-left: 8px; padding-top: 6px; }
.header-right { display: flex; align-items: center; gap: 12px; }
.active-model-badge {
  background: rgba(0,217,192,0.12); color: #00D9C0; border: 1px solid rgba(0,217,192,0.3);
  padding: 4px 14px; border-radius: 20px; font-size: 13px; font-weight: 600;
}
.add-btn {
  background: linear-gradient(135deg, #00D9C0, #00b89c); border: none; color: #000;
  font-weight: 600; border-radius: 8px; padding: 8px 20px; font-size: 13px;
}
.add-btn:hover { background: linear-gradient(135deg, #00eecc, #00d9c0); }

.dashboard-body {
  display: grid;
  grid-template-columns: 240px 1fr 280px;
  gap: 16px;
  padding: 16px 24px 24px;
}

.left-panel { display: flex; flex-direction: column; gap: 12px; }

.gauge-card {
  background: #12121f; border: 1px solid rgba(255,255,255,0.06);
  border-radius: 16px; padding: 24px 16px; text-align: center;
}
.gauge-ring { position: relative; width: 140px; height: 140px; margin: 0 auto; }
.gauge-svg { width: 100%; height: 100%; transform: rotate(0deg); }
.gauge-center {
  position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
  text-align: center;
}
.gauge-value { display: block; font-size: 26px; font-weight: 800; color: #00D9C0; line-height: 1; }
.gauge-label { display: block; font-size: 11px; color: #667; margin-top: 4px; }

.stat-cards-vertical { display: flex; flex-direction: column; gap: 8px; }
.stat-mini-card {
  background: #12121f; border: 1px solid rgba(255,255,255,0.06);
  border-radius: 10px; padding: 10px 14px; display: flex; flex-direction: column; gap: 2px;
}
.stat-label { font-size: 11px; color: #667; text-transform: uppercase; letter-spacing: 0.5px; }
.stat-value { font-size: 17px; font-weight: 700; color: #e0e0e0; }
.stat-value.cyan { color: #00D9C0; }
.stat-value.green { color: #2ed573; }
.stat-value.yellow { color: #ffa502; }
.stat-value.red { color: #ff4757; }
.stat-value.small { font-size: 13px; }

.action-btns-vertical { display: flex; flex-direction: column; gap: 8px; margin-top: 4px; }
.action-pill {
  border: none; border-radius: 10px; padding: 10px; font-size: 13px; font-weight: 600;
  cursor: pointer; transition: all 0.2s;
}
.action-pill.primary { background: linear-gradient(135deg, #00D9C0, #00b89c); color: #000; }
.action-pill.primary:hover { box-shadow: 0 0 16px rgba(0,217,192,0.35); }
.action-pill.warning { background: linear-gradient(135deg, #ffa502, #ff7f50); color: #000; }
.action-pill.warning:hover { box-shadow: 0 0 16px rgba(255,165,2,0.35); }
.action-pill.default { background: #1a1a2e; color: #aaa; border: 1px solid rgba(255,255,255,0.08); }
.action-pill.default:hover { border-color: rgba(0,217,192,0.3); color: #00D9C0; }
.action-pill:disabled { opacity: 0.5; cursor: not-allowed; }

.center-panel { display: flex; flex-direction: column; gap: 12px; }
.panel-title-row { display: flex; align-items: center; gap: 8px; }
.panel-icon { font-size: 16px; }
.panel-title { font-size: 15px; font-weight: 700; color: #ddd; }
.panel-count { font-size: 12px; color: #556; margin-left: auto; }

.config-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 12px;
}

.model-card {
  background: #12121f; border: 1px solid rgba(255,255,255,0.06);
  border-radius: 12px; padding: 14px 16px;
  transition: all 0.25s ease;
  display: flex; flex-direction: column; gap: 10px;
}
.model-card:hover { border-color: rgba(0,217,192,0.25); transform: translateY(-2px); box-shadow: 0 6px 20px rgba(0,0,0,0.3); }
.card-active { border-color: rgba(0,217,192,0.4); box-shadow: 0 0 20px rgba(0,217,192,0.08); }
.card-success { border-left: 3px solid #2ed573; }
.card-error { border-left: 3px solid #ff4757; }

.card-top { display: flex; justify-content: space-between; align-items: flex-start; }
.card-name-row { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.card-model-name { font-size: 14px; font-weight: 700; color: #fff; }
.card-provider { font-size: 11px; color: #777; }

.card-body-info { display: flex; flex-direction: column; gap: 4px; }
.info-row { display: flex; justify-content: space-between; align-items: center; }
.info-k { font-size: 11px; color: #556; }
.info-v { font-size: 12px; color: #bbb; font-weight: 500; }
.info-v.mono { font-family: 'Consolas','Monaco',monospace; }
.info-v.mono.small { font-size: 11px; word-break: break-all; text-align: right; max-width: 130px; }

.card-bottom { display: flex; flex-direction: column; gap: 8px; }
.usage-bar-wrap { display: flex; align-items: center; gap: 8px; }
.bar-label { font-size: 11px; color: #556; white-space: nowrap; }
.mini-bar { height: 6px; flex: 1; border-radius: 3px; }
.mini-bar.success { background: linear-gradient(90deg, #2ed573, #00D9C0); }
.mini-bar.failed { background: linear-gradient(90deg, #ff4757, #ff6b81); }
.mini-bar.unknown { background: #333; }
.bar-text { font-size: 11px; color: #777; white-space: nowrap; }

.card-actions { display: flex; gap: 6px; flex-wrap: wrap; }
.card-btn {
  border: none; border-radius: 6px; padding: 4px 10px; font-size: 11px; font-weight: 600;
  cursor: pointer; transition: all 0.2s;
}
.card-btn.test { background: rgba(64,158,255,0.12); color: #409EFF; }
.card-btn.test:hover { background: rgba(64,158,255,0.25); }
.card-btn.activate { background: rgba(46,213,115,0.12); color: #2ed573; }
.card-btn.activate:hover { background: rgba(46,213,115,0.25); }
.card-btn.edit { background: rgba(0,217,192,0.12); color: #00D9C0; }
.card-btn.edit:hover { background: rgba(0,217,192,0.25); }
.card-btn.del { background: rgba(255,71,87,0.08); color: #ff6b81; }
.card-btn.del:hover { background: rgba(255,71,87,0.2); }
.card-btn:disabled { opacity: 0.4; cursor: not-allowed; }

.empty-grid-slot {
  background: rgba(255,255,255,0.02); border: 2px dashed rgba(255,255,255,0.08);
  border-radius: 12px; display: flex; flex-direction: column; align-items: center;
  justify-content: center; gap: 8px; min-height: 180px; cursor: pointer; transition: all 0.2s;
}
.empty-grid-slot:hover { border-color: rgba(0,217,192,0.3); background: rgba(0,217,192,0.03); }
.empty-plus { font-size: 36px; color: #444; line-height: 1; }
.empty-text { font-size: 13px; color: #556; }

.right-panel { display: flex; flex-direction: column; gap: 12px; }
.info-card {
  background: #12121f; border: 1px solid rgba(255,255,255,0.06);
  border-radius: 12px; overflow: hidden;
}
.info-card-header {
  display: flex; align-items: center; gap: 8px; padding: 12px 16px;
  background: rgba(0,217,192,0.05); border-bottom: 1px solid rgba(255,255,255,0.04);
}
.info-bolt { font-size: 14px; }
.info-title { font-size: 13px; font-weight: 700; color: #ddd; }
.info-body { padding: 12px 16px; display: flex; flex-direction: column; gap: 10px; }
.info-item-large { display: flex; flex-direction: column; gap: 2px; }
.ilabel { font-size: 11px; color: #556; }
.ivalue { font-size: 13px; color: #ccc; font-weight: 500; word-break: break-all; }
.ivalue.mono-sm { font-family: 'Consolas','Monaco',monospace; font-size: 12px; }

.metric-card {
  background: #12121f; border: 1px solid rgba(255,255,255,0.06);
  border-radius: 12px; padding: 14px 16px;
}
.metric-title { font-size: 13px; font-weight: 700; color: #999; margin-bottom: 10px; }
.metric-body { text-align: center; }
.metric-big-num { font-size: 32px; font-weight: 800; line-height: 1; }
.metric-big-num.success-color { color: #2ed573; }
.metric-big-num.error-color { color: #ff4757; }
.metric-sub { font-size: 12px; color: #667; margin-top: 6px; }
.metric-row-s { font-size: 12px; color: #888; margin-top: 8px; }
.metric-detail p { font-size: 12px; color: #aaa; margin: 6px 0; line-height: 1.5; }
.error-detail .err-msg { color: #ff6b81; word-break: break-word; }

.config-test-area { background: #12121f; border: 1px solid rgba(255,255,255,0.06); border-radius: 12px; padding: 16px; }
.cta-title { font-size: 13px; font-weight: 700; color: #999; margin-bottom: 12px; }
.cta-btn {
  width: 100%; border: none; border-radius: 8px; padding: 10px; font-size: 13px;
  font-weight: 600; cursor: pointer; margin-bottom: 8px; transition: all 0.2s;
}
.cta-btn:last-child { margin-bottom: 0; }
.primary-cta { background: linear-gradient(135deg, #00D9C0, #00b89c); color: #000; }
.primary-cta:hover { box-shadow: 0 0 16px rgba(0,217,192,0.3); }
.warn-cta { background: linear-gradient(135deg, #ffa502, #ff7f50); color: #000; }
.warn-cta:hover { box-shadow: 0 0 16px rgba(255,165,2,0.3); }

.no-active-hint {
  background: #12121f; border: 1px solid rgba(255,255,255,0.06);
  border-radius: 12px; padding: 24px 16px; text-align: center;
}
.no-active-hint p { font-size: 13px; color: #667; margin-bottom: 14px; }

.mm-input :deep(.el-input__wrapper) { background: #1a1a2e; box-shadow: 0 0 0 1px #2a2a40 inset; border-radius: 8px; }
.mm-input :deep(.el-input__inner) { color: #e0e0e0; }
.mm-select :deep(.el-input__wrapper) { background: #1a1a2e; box-shadow: 0 0 0 1px #2a2a40 inset; border-radius: 8px; }
.mm-cancel { background: transparent; color: #888; border: 1px solid #333; border-radius: 8px; }
.mm-cancel:hover { border-color: #555; color: #ccc; }
.mm-save { background: linear-gradient(135deg, #00D9C0, #00b89c); border: none; color: #000; border-radius: 8px; font-weight: 600; }
.result-display { padding: 10px 0; }
.result-success-body p, .result-error-body p, .result-neutral-body p { font-size: 13px; color: #bbb; line-height: 1.8; }
.err-msg { color: #ff6b81 !important; word-break: break-word; }
.quota-result-body { display: flex; flex-direction: column; gap: 16px; }
.qr-big { display: flex; justify-content: space-between; align-items: center; padding: 14px 18px; background: #1a1a2e; border-radius: 10px; border: 1px solid #2a2a40; }
.qr-label { font-size: 13px; color: #888; }
.qr-val { font-size: 24px; font-weight: 800; color: #00D9C0; }
.qr-val.used { color: #ffa502; }
</style>
