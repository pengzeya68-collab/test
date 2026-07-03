<template>
  <div class="data-factory">
    <div class="df-header">
      <div class="df-header-left">
        <h3 class="df-title">🧪 测试数据工厂</h3>
        <span class="df-subtitle">定义规则，一键生成测试数据</span>
      </div>
      <div class="df-header-right">
        <el-button @click="showHelp = true">❓ 使用说明</el-button>
        <el-button @click="showPresetDialog = true">
          <el-icon><MagicStick /></el-icon>
          从预设创建
        </el-button>
        <el-button type="primary" @click="startCreate">
          <el-icon><Plus /></el-icon>
          新建模板
        </el-button>
      </div>
    </div>

    <div class="df-body">
      <div class="df-sidebar" :style="{ width: sidebarWidth + 'px', flex: 'none' }">
        <div class="sidebar-title">模板列表</div>
        <div class="template-list">
          <div
            v-for="tpl in templates"
            :key="tpl.id"
            class="tpl-item"
            :class="{ active: currentId === tpl.id }"
            @click="loadTemplate(tpl.id)"
          >
            <div class="tpl-name">{{ tpl.name }}</div>
            <div class="tpl-meta">{{ tpl.fields?.length || 0 }} 字段 · {{ tpl.row_count }} 行</div>
          </div>
          <div v-if="templates.length === 0" class="tpl-empty">
            <p>暂无模板</p>
            <p class="tpl-empty-hint">点击「从预设创建」快速开始</p>
          </div>
        </div>
      </div>

      <!-- 拖拽分隔条：模板列表 ↔ 主区域 -->
      <BaseSplitter
        v-model:size="sidebarWidth"
        direction="horizontal"
        :min-size="200"
        :max-size="520"
        storage-key="tm-datafactory-sidebar-width"
        container-selector=".df-body"
      />

      <div class="df-main">
        <div v-if="!currentId && !creating" class="welcome">
          <div class="welcome-icon">🧪</div>
          <h3>测试数据工厂</h3>
          <p>快速生成各种测试数据，支持数据驱动测试执行</p>
          <div class="welcome-features">
            <div class="wf-item">
              <span class="wf-icon">📋</span>
              <span>9种数据规则</span>
            </div>
            <div class="wf-item">
              <span class="wf-icon">⚡</span>
              <span>实时预览</span>
            </div>
            <div class="wf-item">
              <span class="wf-icon">🔄</span>
              <span>数据驱动执行</span>
            </div>
          </div>
        </div>

        <div v-else class="editor">
          <div class="editor-top">
            <div class="editor-info">
              <el-input
                v-if="creating"
                v-model="form.name"
                placeholder="输入模板名称，如：用户注册测试数据"
                size="large"
                class="name-input"
              />
              <h3 v-else class="editor-name">{{ form.name }}</h3>
              <el-input
                v-model="form.description"
                placeholder="添加描述（可选）"
                size="small"
                class="desc-input"
              />
            </div>
            <div class="editor-actions">
              <template v-if="creating">
                <el-button @click="cancelCreate">取消</el-button>
                <el-button type="primary" @click="saveTemplate" :loading="saving">保存模板</el-button>
              </template>
              <template v-else>
                <el-button @click="editing = !editing">
                  {{ editing ? '完成编辑' : '编辑' }}
                </el-button>
                <el-button v-if="editing" type="primary" @click="saveTemplate" :loading="saving">保存</el-button>
                <el-button type="danger" plain @click="deleteTemplate">删除</el-button>
              </template>
            </div>
          </div>

          <div class="editor-config" v-if="creating || editing">
            <div class="config-row">
              <div class="config-item">
                <label>生成行数</label>
                <el-input-number v-model="form.row_count" :min="1" :max="1000" size="small" />
              </div>
              <div class="config-item">
                <label>关联场景</label>
                <el-select v-model="form.scenario_id" placeholder="可选" clearable size="small" style="width:200px">
                  <el-option v-for="s in scenarios" :key="s.id" :label="s.name" :value="s.id" />
                </el-select>
              </div>
            </div>
          </div>

          <div class="editor-fields" v-if="creating || editing">
            <div class="fields-header">
              <span class="fields-title">字段规则</span>
              <el-button type="primary" text size="small" @click="addField">
                <el-icon><Plus /></el-icon> 添加字段
              </el-button>
            </div>

            <div v-if="form.fields.length === 0" class="fields-empty">
              <p>还没有字段，点击「添加字段」或选择下方快捷添加</p>
              <div class="quick-add">
                <el-tag
                  v-for="q in quickFields"
                  :key="q.name"
                  class="quick-tag"
                  @click="addQuickField(q)"
                >
                  {{ q.icon }} {{ q.label }}
                </el-tag>
              </div>
            </div>

            <div v-else class="fields-list">
              <div v-for="(field, idx) in form.fields" :key="idx" class="field-card">
                <div class="fc-top">
                  <div class="fc-name-row">
                    <el-input
                      v-model="field.field_name"
                      placeholder="字段名 (英文)"
                      size="small"
                      style="width:150px"
                      :class="{ 'is-error': !field.field_name?.trim() }"
                    />
                    <el-input
                      v-model="field.field_label"
                      placeholder="中文名 (可选)"
                      size="small"
                      style="width:120px"
                    />
                  </div>
                  <div class="fc-actions">
                    <el-button v-if="idx > 0" text size="small" @click="moveField(idx, -1)">↑</el-button>
                    <el-button v-if="idx < form.fields.length - 1" text size="small" @click="moveField(idx, 1)">↓</el-button>
                    <el-button text type="danger" size="small" @click="removeField(idx)">
                      <el-icon><Delete /></el-icon>
                    </el-button>
                  </div>
                </div>
                <div class="fc-rule">
                  <el-select v-model="field.rule_type" size="small" style="width:140px" @change="onRuleTypeChange(field)">
                    <el-option-group label="常用规则">
                      <el-option v-for="rt in commonRules" :key="rt.type" :label="rt.icon + ' ' + rt.label" :value="rt.type" />
                    </el-option-group>
                    <el-option-group label="高级规则">
                      <el-option v-for="rt in advancedRules" :key="rt.type" :label="rt.icon + ' ' + rt.label" :value="rt.type" />
                    </el-option-group>
                  </el-select>
                  <div class="fc-config">
                    <template v-if="field.rule_type === 'fixed'">
                      <el-input v-model="field.rule_config.value" placeholder="输入固定值" size="small" />
                    </template>
                    <template v-else-if="field.rule_type === 'enum'">
                      <el-select
                        v-model="field.rule_config.options"
                        multiple
                        filterable
                        allow-create
                        default-first-option
                        placeholder="输入后回车添加"
                        size="small"
                        style="width:100%"
                      />
                    </template>
                    <template v-else-if="field.rule_type === 'increment'">
                      <el-input v-model="field.rule_config.prefix" placeholder="前缀" size="small" style="width:80px" />
                      <el-input-number v-model="field.rule_config.start" :min="0" placeholder="起始" size="small" style="width:100px" />
                      <el-input-number v-model="field.rule_config.step" :min="1" placeholder="步长" size="small" style="width:90px" />
                    </template>
                    <template v-else-if="field.rule_type === 'uuid'">
                      <el-radio-group v-model="field.rule_config.version" size="small">
                        <el-radio-button value="4">标准UUID</el-radio-button>
                        <el-radio-button value="simple">短UUID</el-radio-button>
                      </el-radio-group>
                    </template>
                    <template v-else-if="field.rule_type === 'timestamp'">
                      <el-select v-model="field.rule_config.format" size="small" style="width:140px">
                        <el-option label="秒级时间戳" value="seconds" />
                        <el-option label="毫秒时间戳" value="milliseconds" />
                        <el-option label="日期时间" value="datetime" />
                        <el-option label="ISO格式" value="iso" />
                      </el-select>
                    </template>
                    <template v-else-if="field.rule_type === 'date_offset'">
                      <el-input-number v-model="field.rule_config.offset_days" size="small" style="width:120px" />
                      <span class="fc-hint">天 (负数=过去)</span>
                      <el-select v-model="field.rule_config.format" size="small" style="width:120px">
                        <el-option label="YYYY-MM-DD" value="date" />
                        <el-option label="日期时间" value="datetime" />
                      </el-select>
                    </template>
                    <template v-else-if="field.rule_type === 'phone'">
                      <el-select v-model="field.rule_config.prefix" size="small" style="width:120px">
                        <el-option v-for="p in phonePrefixes" :key="p" :label="p" :value="p" />
                      </el-select>
                      <span class="fc-hint">号段</span>
                    </template>
                    <template v-else-if="field.rule_type === 'email'">
                      <el-input v-model="field.rule_config.username_prefix" placeholder="用户名前缀" size="small" style="width:120px" />
                      <span class="fc-hint">@</span>
                      <el-select
                        v-model="field.rule_config.domain"
                        size="small"
                        style="width:140px"
                        filterable
                        allow-create
                      >
                        <el-option v-for="d in emailDomains" :key="d" :label="d" :value="d" />
                      </el-select>
                    </template>
                    <template v-else-if="field.rule_type === 'username'">
                      <el-input v-model="field.rule_config.prefix" placeholder="前缀" size="small" style="width:100px" />
                      <el-input-number v-model="field.rule_config.suffix_length" :min="2" :max="8" size="small" style="width:100px" />
                      <span class="fc-hint">位随机后缀</span>
                    </template>
                    <template v-else-if="field.rule_type === 'env_ref'">
                      <el-input v-model="field.rule_config.variable_name" placeholder="变量名" size="small" style="width:150px" />
                      <el-input v-model="field.rule_config.default" placeholder="默认值 (可选)" size="small" style="width:120px" />
                    </template>
                  </div>
                </div>
                <div class="fc-preview" v-if="field.rule_type">
                  <span class="fc-preview-label">示例:</span>
                  <code class="fc-preview-val">{{ getPreviewValue(field) }}</code>
                </div>
              </div>

              <div class="quick-add" style="margin-top:12px">
                <span class="quick-add-label">快捷添加:</span>
                <el-tag
                  v-for="q in quickFields"
                  :key="q.name"
                  class="quick-tag"
                  size="small"
                  @click="addQuickField(q)"
                >
                  {{ q.icon }} {{ q.label }}
                </el-tag>
              </div>
            </div>
          </div>

          <div class="editor-preview" v-if="!creating && currentId">
            <div class="preview-header">
              <span class="preview-title">数据预览</span>
              <div class="preview-actions">
                <el-button size="small" @click="doPreview" :loading="previewLoading">
                  <el-icon><Refresh /></el-icon> 刷新预览
                </el-button>
                <el-button size="small" type="success" @click="doGenerate" :loading="generateLoading">
                  <el-icon><Download /></el-icon> 生成数据集
                </el-button>
                <el-button size="small" type="info" @click="exportCSV" :disabled="!previewData">
                  <el-icon><Download /></el-icon> 导出 CSV
                </el-button>
                <el-button size="small" type="info" @click="exportJSON" :disabled="!previewData">
                  <el-icon><Download /></el-icon> 导出 JSON
                </el-button>
                <el-button
                  v-if="generatedDataset"
                  size="small"
                  type="primary"
                  @click="doRun"
                  :loading="runLoading"
                  :disabled="!form.scenario_id"
                >
                  <el-icon><VideoPlay /></el-icon> 数据驱动执行
                </el-button>
              </div>
            </div>

            <div v-if="previewData" class="preview-table-wrap">
              <el-table :data="previewData.rows" border size="small" max-height="320">
                <el-table-column
                  v-for="(col, idx) in previewData.columns"
                  :key="idx"
                  :label="col"
                  :prop="String(idx)"
                  min-width="130"
                />
              </el-table>
              <div class="preview-meta">
                共 {{ previewData.row_count }} 行 · {{ previewData.columns.length }} 列
              </div>
            </div>
            <div v-else-if="previewLoading" class="preview-loading">
              <el-icon class="is-loading"><Loading /></el-icon> 正在生成预览...
            </div>
            <div v-else class="preview-empty">
              点击「刷新预览」查看生成的数据
            </div>

            <div v-if="generatedDataset" class="result-card success">
              <div class="rc-icon">✅</div>
              <div class="rc-info">
                <div class="rc-title">数据集已生成</div>
                <div class="rc-detail">{{ generatedDataset.row_count }} 行 × {{ generatedDataset.columns?.length || 0 }} 列</div>
              </div>
              <div class="rc-actions" v-if="!form.scenario_id">
                <el-button size="small" @click="showBindDialog = true">绑定场景</el-button>
              </div>
            </div>

            <div v-if="runResult" class="result-card" :class="runResult.success ? 'success' : 'failed'">
              <div class="rc-icon">{{ runResult.success ? '✅' : '❌' }}</div>
              <div class="rc-info">
                <div class="rc-title">{{ runResult.success ? '全部通过' : '存在失败' }}</div>
                <div class="rc-detail">
                  迭代 {{ runResult.total_iterations }} 次 ·
                  成功 {{ runResult.success_iterations }} ·
                  失败 {{ runResult.failed_iterations }} ·
                  耗时 {{ runResult.total_duration }}ms
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <el-dialog v-model="showPresetDialog" title="选择预设模板" width="640px" custom-class="dark-dialog" destroy-on-close>
      <div class="preset-grid">
        <div
          v-for="p in presets"
          :key="p.name"
          class="preset-card"
          @click="applyPreset(p)"
        >
          <div class="pc-icon">{{ p.icon }}</div>
          <div class="pc-name">{{ p.name }}</div>
          <div class="pc-desc">{{ p.desc }}</div>
          <div class="pc-fields">{{ p.fields.length }} 个字段</div>
        </div>
      </div>
    </el-dialog>

    <el-dialog v-model="showBindDialog" title="绑定到测试场景" width="420px" custom-class="dark-dialog">
      <el-select v-model="bindScenarioId" placeholder="选择要绑定的场景" style="width:100%">
        <el-option v-for="s in scenarios" :key="s.id" :label="s.name" :value="s.id" />
      </el-select>
      <template #footer>
        <el-button @click="showBindDialog = false">取消</el-button>
        <el-button type="primary" @click="doBind" :loading="bindLoading" :disabled="!bindScenarioId">绑定</el-button>
      </template>
    </el-dialog>

    <HelpDrawer v-model="showHelp" :title="helpData.title" :intro="helpData.intro" :sections="helpData.sections" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Delete, Refresh, Download, VideoPlay, MagicStick, Loading } from '@element-plus/icons-vue'
import autoTestRequest from '@/utils/autoTestRequest'
import HelpDrawer from '@/components/HelpDrawer.vue'
import BaseSplitter from '@/components/base/BaseSplitter.vue'
import { helpContent } from '@/utils/help-content'

// 左侧模板列表宽度（带 localStorage 持久化）
const sidebarWidth = ref(280)

const commonRules = [
  { type: 'fixed', label: '固定值', icon: '📌' },
  { type: 'enum', label: '枚举值', icon: '🎲' },
  { type: 'increment', label: '递增数字', icon: '🔢' },
  { type: 'phone', label: '随机手机号', icon: '📱' },
  { type: 'email', label: '随机邮箱', icon: '📧' },
  { type: 'username', label: '随机用户名', icon: '👤' },
]

const advancedRules = [
  { type: 'uuid', label: 'UUID', icon: '🔑' },
  { type: 'timestamp', label: '时间戳', icon: '⏱️' },
  { type: 'date_offset', label: '日期偏移', icon: '📅' },
  { type: 'env_ref', label: '环境变量', icon: '🌐' },
]

const phonePrefixes = ['130', '131', '132', '133', '135', '136', '137', '138', '139', '150', '151', '152', '155', '156', '157', '158', '159', '170', '176', '177', '178', '180', '181', '182', '183', '185', '186', '187', '188', '189']

const emailDomains = ['qq.com', '163.com', 'gmail.com', 'outlook.com', 'test.com', 'example.com']

const quickFields = [
  { name: 'phone', label: '手机号', icon: '📱', rule_type: 'phone', rule_config: { prefix: '138' } },
  { name: 'email', label: '邮箱', icon: '📧', rule_type: 'email', rule_config: { username_prefix: 'user', domain: 'test.com' } },
  { name: 'username', label: '用户名', icon: '👤', rule_type: 'username', rule_config: { prefix: 'test', suffix_length: 4 } },
  { name: 'id', label: 'ID', icon: '🔑', rule_type: 'uuid', rule_config: { version: '4' } },
  { name: 'age', label: '年龄', icon: '🎲', rule_type: 'enum', rule_config: { options: ['18', '22', '25', '30', '35', '40'] } },
  { name: 'gender', label: '性别', icon: '🎲', rule_type: 'enum', rule_config: { options: ['男', '女'] } },
  { name: 'timestamp', label: '时间戳', icon: '⏱️', rule_type: 'timestamp', rule_config: { format: 'seconds' } },
  { name: 'date', label: '日期', icon: '📅', rule_type: 'date_offset', rule_config: { offset_days: 0, format: 'date' } },
  { name: 'status', label: '状态', icon: '🎲', rule_type: 'enum', rule_config: { options: ['active', 'inactive', 'pending'] } },
  { name: 'index', label: '序号', icon: '🔢', rule_type: 'increment', rule_config: { prefix: '', start: 1, step: 1 } },
]

const presets = [
  {
    name: '用户注册',
    icon: '👤',
    desc: '手机号、邮箱、用户名、密码等注册数据',
    fields: [
      { field_name: 'phone', field_label: '手机号', rule_type: 'phone', rule_config: { prefix: '138' } },
      { field_name: 'email', field_label: '邮箱', rule_type: 'email', rule_config: { username_prefix: 'user', domain: 'test.com' } },
      { field_name: 'username', field_label: '用户名', rule_type: 'username', rule_config: { prefix: 'test', suffix_length: 4 } },
      { field_name: 'password', field_label: '密码', rule_type: 'fixed', rule_config: { value: 'Test@123456' } },
      { field_name: 'nickname', field_label: '昵称', rule_type: 'username', rule_config: { prefix: 'nick', suffix_length: 6 } },
      { field_name: 'gender', field_label: '性别', rule_type: 'enum', rule_config: { options: ['男', '女'] } },
    ]
  },
  {
    name: '商品数据',
    icon: '🛒',
    desc: '商品名、价格、分类、库存等电商数据',
    fields: [
      { field_name: 'product_name', field_label: '商品名', rule_type: 'username', rule_config: { prefix: '商品', suffix_length: 4 } },
      { field_name: 'price', field_label: '价格', rule_type: 'enum', rule_config: { options: ['9.9', '19.9', '29.9', '49.9', '99', '199', '399'] } },
      { field_name: 'category', field_label: '分类', rule_type: 'enum', rule_config: { options: ['电子产品', '服装', '食品', '家居', '图书'] } },
      { field_name: 'stock', field_label: '库存', rule_type: 'increment', rule_config: { prefix: '', start: 100, step: 10 } },
      { field_name: 'sku', field_label: 'SKU', rule_type: 'uuid', rule_config: { version: 'simple' } },
      { field_name: 'status', field_label: '状态', rule_type: 'enum', rule_config: { options: ['上架', '下架', '预售'] } },
    ]
  },
  {
    name: '订单数据',
    icon: '📦',
    desc: '订单号、金额、状态、时间等订单信息',
    fields: [
      { field_name: 'order_no', field_label: '订单号', rule_type: 'increment', rule_config: { prefix: 'ORD', start: 10001, step: 1 } },
      { field_name: 'amount', field_label: '金额', rule_type: 'enum', rule_config: { options: ['0.01', '9.9', '29.9', '99', '199', '599', '1299'] } },
      { field_name: 'status', field_label: '状态', rule_type: 'enum', rule_config: { options: ['待支付', '已支付', '已发货', '已完成', '已取消'] } },
      { field_name: 'create_time', field_label: '创建时间', rule_type: 'timestamp', rule_config: { format: 'datetime' } },
      { field_name: 'user_id', field_label: '用户ID', rule_type: 'uuid', rule_config: { version: 'simple' } },
      { field_name: 'pay_method', field_label: '支付方式', rule_type: 'enum', rule_config: { options: ['微信', '支付宝', '银行卡'] } },
    ]
  },
  {
    name: '接口压测',
    icon: '⚡',
    desc: '大量随机数据用于接口压力测试',
    fields: [
      { field_name: 'request_id', field_label: '请求ID', rule_type: 'uuid', rule_config: { version: '4' } },
      { field_name: 'user_token', field_label: 'Token', rule_type: 'uuid', rule_config: { version: 'simple' } },
      { field_name: 'timestamp', field_label: '时间戳', rule_type: 'timestamp', rule_config: { format: 'milliseconds' } },
      { field_name: 'client_ip', field_label: '客户端IP', rule_type: 'fixed', rule_config: { value: '192.168.1.' } },
      { field_name: 'action', field_label: '操作', rule_type: 'enum', rule_config: { options: ['login', 'query', 'submit', 'delete'] } },
    ]
  },
  {
    name: '日期时间',
    icon: '📅',
    desc: '各种日期时间格式数据',
    fields: [
      { field_name: 'date', field_label: '日期', rule_type: 'date_offset', rule_config: { offset_days: 0, format: 'date' } },
      { field_name: 'yesterday', field_label: '昨天', rule_type: 'date_offset', rule_config: { offset_days: -1, format: 'date' } },
      { field_name: 'next_week', field_label: '下周', rule_type: 'date_offset', rule_config: { offset_days: 7, format: 'date' } },
      { field_name: 'timestamp_s', field_label: '时间戳(秒)', rule_type: 'timestamp', rule_config: { format: 'seconds' } },
      { field_name: 'timestamp_ms', field_label: '时间戳(毫秒)', rule_type: 'timestamp', rule_config: { format: 'milliseconds' } },
      { field_name: 'iso_time', field_label: 'ISO时间', rule_type: 'timestamp', rule_config: { format: 'iso' } },
    ]
  },
  {
    name: '空白模板',
    icon: '📝',
    desc: '从零开始自定义字段',
    fields: []
  },
]

const templates = ref([])
const scenarios = ref([])
const currentId = ref(null)
const creating = ref(false)
const editing = ref(false)
const saving = ref(false)
const previewLoading = ref(false)
const generateLoading = ref(false)
const runLoading = ref(false)
const bindLoading = ref(false)

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

const showPresetDialog = ref(false)
const showBindDialog = ref(false)
const bindScenarioId = ref(null)
const showHelp = ref(false)
const helpData = helpContent.dataFactory

const addField = () => {
  form.value.fields.push({
    field_name: '',
    field_label: '',
    rule_type: 'fixed',
    rule_config: { value: '' },
    sort_order: form.value.fields.length
  })
}

const addQuickField = (q) => {
  form.value.fields.push({
    field_name: q.name,
    field_label: q.label,
    rule_type: q.rule_type,
    rule_config: JSON.parse(JSON.stringify(q.rule_config)),
    sort_order: form.value.fields.length
  })
}

const removeField = (idx) => {
  form.value.fields.splice(idx, 1)
}

const moveField = (idx, dir) => {
  const target = idx + dir
  const list = form.value.fields
  if (target < 0 || target >= list.length) return
  const temp = list[idx]
  list[idx] = list[target]
  list[target] = temp
  form.value.fields = [...list]
}

const onRuleTypeChange = (field) => {
  const defaults = {
    fixed: { value: '' },
    enum: { options: [] },
    increment: { prefix: '', start: 1, step: 1 },
    uuid: { version: '4' },
    timestamp: { format: 'seconds' },
    date_offset: { offset_days: 0, format: 'date' },
    phone: { prefix: '138' },
    email: { username_prefix: 'user', domain: 'test.com' },
    username: { prefix: 'test', suffix_length: 4 },
    env_ref: { variable_name: '', default: '' },
  }
  field.rule_config = defaults[field.rule_type] || {}
}

const getPreviewValue = (field) => {
  const c = field.rule_config || {}
  switch (field.rule_type) {
    case 'fixed': return c.value || '(空)'
    case 'enum': return c.options?.length ? c.options[0] + (c.options.length > 1 ? ` / ${c.options.length}个选项` : '') : '(未设置)'
    case 'increment': return `${c.prefix || ''}${c.start || 1}`
    case 'uuid': return c.version === 'simple' ? 'a3f2b1c4' : '550e8400-e29b-41d4-a716-446655440000'
    case 'timestamp':
      if (c.format === 'milliseconds') return '1748502000000'
      if (c.format === 'datetime') return '2026-05-29 10:30:00'
      if (c.format === 'iso') return '2026-05-29T10:30:00+08:00'
      return '1748502000'
    case 'date_offset': {
      const d = new Date()
      d.setDate(d.getDate() + (c.offset_days || 0))
      return d.toISOString().slice(0, 10)
    }
    case 'phone': return `${c.prefix || '138'}12345678`
    case 'email': return `${c.username_prefix || 'user'}123@${c.domain || 'test.com'}`
    case 'username': return `${c.prefix || 'test'}${Math.random().toString(36).slice(2, 2 + (c.suffix_length || 4))}`
    case 'env_ref': return c.variable_name ? `\${${c.variable_name}}` : '(未设置)'
    default: return ''
  }
}

const startCreate = () => {
  creating.value = true
  editing.value = false
  currentId.value = null
  form.value = {
    name: '',
    description: '',
    scenario_id: null,
    row_count: 10,
    fields: []
  }
  previewData.value = null
  generatedDataset.value = null
  runResult.value = null
}

const cancelCreate = () => {
  creating.value = false
  if (templates.value.length > 0) {
    loadTemplate(templates.value[0].id)
  } else {
    currentId.value = null
  }
}

const applyPreset = (preset) => {
  showPresetDialog.value = false
  creating.value = true
  editing.value = false
  currentId.value = null
  form.value = {
    name: preset.name === '空白模板' ? '' : preset.name,
    description: preset.desc,
    scenario_id: null,
    row_count: 10,
    fields: preset.fields.map((f, i) => ({
      ...f,
      rule_config: JSON.parse(JSON.stringify(f.rule_config)),
      sort_order: i
    }))
  }
  previewData.value = null
  generatedDataset.value = null
  runResult.value = null
}

const saveTemplate = async () => {
  if (!form.value.name.trim()) {
    ElMessage.warning('请输入模板名称')
    return
  }
  const hasEmpty = form.value.fields.some(f => !f.field_name?.trim())
  if (hasEmpty) {
    ElMessage.warning('请填写所有字段名称')
    return
  }
  saving.value = true
  try {
    const payload = {
      name: form.value.name,
      description: form.value.description,
      scenario_id: form.value.scenario_id,
      row_count: form.value.row_count,
      fields: form.value.fields.map((f, i) => ({
        field_name: f.field_name,
        field_label: f.field_label,
        rule_type: f.rule_type,
        rule_config: f.rule_config,
        sort_order: i
      }))
    }
    if (creating.value) {
      const res = await autoTestRequest.post('/auto-test/data-factory/templates', payload)
      creating.value = false
      currentId.value = res.id
      ElMessage.success('模板创建成功')
    } else {
      await autoTestRequest.put(`/auto-test/data-factory/templates/${currentId.value}`, payload)
      ElMessage.success('模板更新成功')
    }
    await fetchTemplates()
    if (currentId.value) {
      await loadTemplate(currentId.value)
    }
  } catch (e) {
    ElMessage.error('保存失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    saving.value = false
  }
}

const loadTemplate = async (id) => {
  currentId.value = id
  creating.value = false
  editing.value = false
  previewData.value = null
  generatedDataset.value = null
  runResult.value = null
  try {
    const res = await autoTestRequest.get(`/auto-test/data-factory/templates/${id}`)
    form.value = {
      name: res.name || '',
      description: res.description || '',
      scenario_id: res.scenario_id || null,
      row_count: res.row_count || 10,
      fields: (res.fields || []).map((f, i) => ({
        ...f,
        rule_config: f.rule_config || {},
        sort_order: i
      }))
    }
    doPreview()
  } catch (e) {
    ElMessage.error('加载模板失败')
  }
}

const deleteTemplate = async () => {
  try {
    await ElMessageBox.confirm(`确定删除模板"${form.value.name}"吗？`, '确认', { type: 'warning' })
    await autoTestRequest.delete(`/auto-test/data-factory/templates/${currentId.value}`)
    ElMessage.success('已删除')
    currentId.value = null
    await fetchTemplates()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('删除失败')
  }
}

const doPreview = async () => {
  if (!currentId.value) return
  previewLoading.value = true
  try {
    const res = await autoTestRequest.post(`/auto-test/data-factory/templates/${currentId.value}/preview`)
    previewData.value = res
  } catch (e) {
    ElMessage.error('预览失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    previewLoading.value = false
  }
}

const doGenerate = async () => {
  if (!currentId.value) return
  generateLoading.value = true
  try {
    const res = await autoTestRequest.post(`/auto-test/data-factory/templates/${currentId.value}/generate`)
    generatedDataset.value = res
    runResult.value = null
    ElMessage.success('数据集已生成')
  } catch (e) {
    ElMessage.error('生成失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    generateLoading.value = false
  }
}

const doRun = async () => {
  if (!generatedDataset.value?.dataset_id) {
    ElMessage.warning('请先生成数据集')
    return
  }
  runLoading.value = true
  try {
    const res = await autoTestRequest.post(`/auto-test/data-factory/datasets/${generatedDataset.value.dataset_id}/run`)
    runResult.value = res
    ElMessage.success(res?.success ? '执行完成，全部通过' : '执行完成，存在失败')
  } catch (e) {
    ElMessage.error('执行失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    runLoading.value = false
  }
}

const doBind = async () => {
  if (!generatedDataset.value?.dataset_id || !bindScenarioId.value) return
  bindLoading.value = true
  try {
    await autoTestRequest.post(`/auto-test/data-factory/datasets/${generatedDataset.value.dataset_id}/bind-scenario/${bindScenarioId.value}`)
    ElMessage.success('绑定成功')
    showBindDialog.value = false
    form.value.scenario_id = bindScenarioId.value
  } catch (e) {
    ElMessage.error('绑定失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    bindLoading.value = false
  }
}

const exportCSV = () => {
  if (!previewData.value) return
  const { columns, rows } = previewData.value
  const csvRows = []
  csvRows.push(columns.map(escapeCSVField).join(','))
  for (const row of rows) {
    csvRows.push(columns.map((_, idx) => escapeCSVField(String(row[idx] ?? ''))).join(','))
  }
  const csvContent = '\uFEFF' + csvRows.join('\n')
  downloadFile(csvContent, `${form.value.name || 'data'}_${Date.now()}.csv`, 'text/csv;charset=utf-8')
  ElMessage.success('CSV 导出成功')
}

const exportJSON = () => {
  if (!previewData.value) return
  const { columns, rows } = previewData.value
  const jsonData = rows.map(row => {
    const obj = {}
    columns.forEach((col, idx) => {
      obj[col] = row[idx] ?? ''
    })
    return obj
  })
  const jsonContent = JSON.stringify(jsonData, null, 2)
  downloadFile(jsonContent, `${form.value.name || 'data'}_${Date.now()}.json`, 'application/json;charset=utf-8')
  ElMessage.success('JSON 导出成功')
}

const escapeCSVField = (field) => {
  const str = String(field)
  if (str.includes(',') || str.includes('"') || str.includes('\n')) {
    return '"' + str.replace(/"/g, '""') + '"'
  }
  return str
}

const downloadFile = (content, filename, mimeType) => {
  const blob = new Blob([content], { type: mimeType })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = filename
  link.click()
  URL.revokeObjectURL(link.href)
}

const fetchTemplates = async () => {
  try {
    const res = await autoTestRequest.get('/auto-test/data-factory/templates')
    templates.value = res || []
  } catch (e) {
    console.error('获取模板列表失败', e)
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

onMounted(() => {
  fetchTemplates()
  fetchScenarios()
})
</script>

<style scoped>
.data-factory {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.df-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 20px;
  border-bottom: 1px solid var(--border-color, var(--border-subtle));
}

.df-header-left {
  display: flex;
  align-items: baseline;
  gap: 12px;
}

.df-title {
  margin: 0;
  font-size: 18px;
  color: var(--text-primary);
}

.df-subtitle {
  font-size: 12px;
  color: var(--text-secondary);
}

.df-header-right {
  display: flex;
  gap: 8px;
}

.df-body {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.df-sidebar {
  flex-shrink: 0;
  border-right: 1px solid var(--border-color, var(--border-subtle));
  padding: 12px;
  overflow-y: auto;
}

.sidebar-title {
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.template-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.tpl-item {
  padding: 10px 12px;
  border-radius: 6px;
  cursor: pointer;
  border: 1px solid transparent;
  transition: all .15s;
}

.tpl-item:hover {
  background: rgba(var(--tm-color-primary-rgb), 0.08);
  border-color: rgba(var(--tm-color-primary-rgb), 0.2);
}

.tpl-item.active {
  background: rgba(var(--tm-color-primary-rgb), 0.12);
  border-color: var(--accent-primary);
}

.tpl-name {
  font-size: 14px;
  color: var(--text-primary);
  font-weight: 500;
}

.tpl-meta {
  font-size: 11px;
  color: var(--text-muted);
  margin-top: 4px;
}

.tpl-empty {
  text-align: center;
  padding: 30px 0;
  color: var(--text-muted);
  font-size: 13px;
}

.tpl-empty-hint {
  color: var(--accent-primary);
  margin-top: 4px;
  font-size: 12px;
}

.df-main {
  flex: 1 1 0;
  min-width: 0;
  overflow-y: auto;
  padding: 20px;
}

/* 响应式：768 以下纵向堆叠并隐藏拖拽手柄 */
@media (max-width: 768px) {
  .df-body {
    flex-direction: column;
    gap: 12px;
  }
  .df-sidebar {
    width: 100% !important;
    max-height: 240px;
    border-right: none;
    border-bottom: 1px solid var(--border-color, var(--border-subtle));
  }
  .df-body > :deep(.base-splitter) {
    display: none;
  }
}

.welcome {
  text-align: center;
  padding: 32px 0;
  color: var(--tm-text-regular, var(--text-secondary));
}

.welcome-icon {
  font-size: 40px;
  margin-bottom: 12px;
}

.welcome h3 {
  font-size: 18px;
  margin: 0 0 8px;
  color: var(--text-primary);
}

.welcome p {
  color: var(--text-secondary);
  margin: 0 0 20px;
}

.welcome-features {
  display: flex;
  justify-content: center;
  gap: 24px;
  flex-wrap: wrap;
}

.wf-item {
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--text-secondary);
  font-size: 13px;
}

.wf-icon {
  font-size: 16px;
}

.editor {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.editor-top {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border-color, var(--border-subtle));
}

.editor-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.name-input {
  font-size: 18px;
  font-weight: 600;
}

.name-input :deep(.el-input__inner) {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

.editor-name {
  margin: 0;
  font-size: 18px;
  color: var(--text-primary);
}

.desc-input :deep(.el-input__inner) {
  color: var(--text-secondary);
}

.editor-actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}

.editor-config {
  background: var(--bg-elevated);
  border: 1px solid var(--border-color, var(--border-subtle));
  border-radius: 8px;
  padding: 12px 16px;
}

.config-row {
  display: flex;
  gap: 24px;
  align-items: center;
}

.config-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.config-item label {
  font-size: 13px;
  color: var(--text-secondary);
  white-space: nowrap;
}

.editor-fields {
  background: var(--bg-surface);
  border: 1px solid var(--border-color, var(--border-subtle));
  border-radius: 8px;
  padding: 16px;
}

.fields-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.fields-title {
  font-size: 14px;
  color: var(--tm-text-regular, var(--text-primary));
  font-weight: 600;
}

.fields-empty {
  text-align: center;
  padding: 24px 0;
  color: var(--text-secondary);
}

.fields-empty p {
  margin: 0 0 12px;
}

.quick-add {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  justify-content: center;
}

.quick-tag {
  cursor: pointer;
  transition: all .15s;
}

.quick-tag:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(var(--tm-color-primary-rgb), 0.3);
}

.quick-add-label {
  font-size: 12px;
  color: var(--text-secondary);
  line-height: 24px;
  margin-right: 4px;
}

.fields-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.field-card {
  background: var(--bg-elevated);
  border: 1px solid var(--border-color, var(--border-subtle));
  border-radius: 8px;
  padding: 12px;
  transition: border-color .15s;
}

.field-card:hover {
  border-color: rgba(var(--tm-color-primary-rgb), 0.3);
}

.fc-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.fc-name-row {
  display: flex;
  gap: 8px;
}

.fc-actions {
  display: flex;
  gap: 2px;
}

.fc-rule {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.fc-config {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.fc-hint {
  font-size: 12px;
  color: var(--text-secondary);
  white-space: nowrap;
}

.fc-preview {
  margin-top: 6px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.fc-preview-label {
  font-size: 11px;
  color: var(--text-muted);
}

.fc-preview-val {
  font-size: 12px;
  color: var(--tm-color-primary, var(--accent-primary));
  background: rgba(var(--tm-color-primary-rgb), 0.08);
  padding: 1px 6px;
  border-radius: 3px;
}

.is-error :deep(.el-input__inner) {
  border-color: var(--el-color-danger) !important;
}

.editor-preview {
  background: var(--bg-surface);
  border: 1px solid var(--border-color, var(--border-subtle));
  border-radius: 8px;
  padding: 16px;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.preview-title {
  font-size: 14px;
  color: var(--tm-text-regular, var(--text-primary));
  font-weight: 600;
}

.preview-actions {
  display: flex;
  gap: 8px;
}

.preview-table-wrap {
  margin-bottom: 12px;
}

.preview-meta {
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 6px;
}

.preview-loading,
.preview-empty {
  text-align: center;
  padding: 24px 0;
  color: var(--text-secondary);
  font-size: 13px;
}

.result-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-radius: 8px;
  margin-top: 12px;
}

.result-card.success {
  background: rgba(var(--el-color-success-rgb), 0.08);
  border: 1px solid rgba(var(--el-color-success-rgb), 0.25);
}

.result-card.failed {
  background: rgba(var(--el-color-danger-rgb), 0.08);
  border: 1px solid rgba(var(--el-color-danger-rgb), 0.25);
}

.rc-icon {
  font-size: 24px;
}

.rc-info {
  flex: 1;
}

.rc-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.rc-detail {
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 2px;
}

.rc-actions {
  flex-shrink: 0;
}

.preset-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.preset-card {
  padding: 16px;
  border: 1px solid var(--border-color, var(--border-subtle));
  border-radius: 8px;
  cursor: pointer;
  transition: all .15s;
  text-align: center;
}

.preset-card:hover {
  border-color: var(--accent-primary);
  background: rgba(var(--tm-color-primary-rgb), 0.06);
  transform: translateY(-1px);
}

.pc-icon {
  font-size: 28px;
  margin-bottom: 8px;
}

.pc-name {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.pc-desc {
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: 6px;
}

.pc-fields {
  font-size: 11px;
  color: var(--text-muted);
}

.dark-dialog {
  background: var(--tm-bg-page, var(--bg-surface));
}

@media (max-width: 640px) {
  :deep(.el-dialog) {
    width: 92vw !important;
    max-width: 640px;
  }
}
</style>
