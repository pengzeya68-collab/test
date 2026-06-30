<template>
  <component
    :is="embedded ? 'div' : ElDrawer"
    v-bind="embedded ? {} : drawerBindings"
    :class="embedded ? 'case-editor-embedded' : ''"
    ref="mainDrawerRef"
    @close="handleClose"
  >
    <div class="drawer-content">
      <!-- 顶部：Method + Name + URL -->
      <div class="drawer-header">
        <div class="top-row">
          <el-select v-model="caseForm.method" style="width: 120px;">
            <el-option label="GET" value="GET" />
            <el-option label="POST" value="POST" />
            <el-option label="PUT" value="PUT" />
            <el-option label="DELETE" value="DELETE" />
            <el-option label="PATCH" value="PATCH" />
            <el-option label="HEAD" value="HEAD" />
            <el-option label="OPTIONS" value="OPTIONS" />
          </el-select>
          <el-input
            v-model="caseForm.name"
            placeholder="用例名称"
            style="width: 200px; margin-left: 10px;"
          />
          <el-autocomplete
            v-model="caseForm.url"
            :fetch-suggestions="querySearchVars"
            placeholder="输入请求 URL，例如：{{base_url}}/api/login"
            style="flex: 1; margin-left: 10px;"
            :trigger-on-focus="false"
            @select="handleSelectVar($event, 'url')"
          >
            <template #default="{ item }">
              <div class="var-suggestion">
                <span class="var-name">&#123;&#123; {{ item.value }} &#125;&#125;</span>
                <span class="var-val">{{ item.actualValue }}</span>
              </div>
            </template>
          </el-autocomplete>
          <el-button size="small" @click="showHelp = true" style="margin-left: 10px;">❓ 使用说明</el-button>
          <el-button v-if="isEdit" size="small" @click="openVersionManager" style="margin-left: 8px;">
            <el-icon><Clock /></el-icon>
            版本管理
          </el-button>
        </div>
      </div>

      <!-- 描述 -->
      <div class="description-bar">
        <el-input
          v-model="caseForm.description"
          type="textarea"
          :rows="2"
          placeholder="用例描述（可选）"
        />
      </div>

      <!-- Tabs -->
      <el-tabs v-model="activeTab" class="case-tabs">
        <!-- Headers -->
        <el-tab-pane label="Headers" name="headers">
          <div class="tab-content">
            <div class="table-toolbar">
              <span class="toolbar-title">请求头</span>
              <el-button size="small" @click="addHeader">
                <el-icon><Plus /></el-icon>
                添加
              </el-button>
            </div>
            <el-table :data="caseForm.headers" border size="small">
              <el-table-column label="Key" min-width="150">
                <template #default="{ row }">
                  <el-input v-model="row.key" placeholder="Header key" />
                </template>
              </el-table-column>
              <el-table-column label="Value" min-width="200">
                <template #default="{ row }">
                  <el-autocomplete
                    v-model="row.value"
                    :fetch-suggestions="querySearchVars"
                    placeholder="Header value"
                    :trigger-on-focus="false"
                    @select="handleSelectVar($event, row, 'value')"
                    @input="handleTableInput(row, 'value', $event)"
                    style="width: 100%"
                  >
                    <template #default="{ item }">
                      <div class="var-suggestion">
                        <span class="var-name">&#123;&#123; {{ item.value }} &#125;&#125;</span>
                        <span class="var-val">{{ item.actualValue }}</span>
                      </div>
                    </template>
                  </el-autocomplete>
                </template>
              </el-table-column>
              <el-table-column label="描述" min-width="150">
                <template #default="{ row }">
                  <el-input v-model="row.description" placeholder="描述（可选）" />
                </template>
              </el-table-column>
              <el-table-column label="操作" width="60" align="center">
                <template #default="{ row, $index }">
                  <el-button type="danger" size="small" text @click="removeHeader($index)">
                    <el-icon><Delete /></el-icon>
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-tab-pane>

        <!-- Params -->
        <el-tab-pane label="Params" name="params">
          <div class="tab-content">
            <div class="table-toolbar">
              <span class="toolbar-title">请求参数</span>
              <el-button size="small" @click="addParam">
                <el-icon><Plus /></el-icon>
                添加
              </el-button>
            </div>
            <el-table :data="caseForm.params" border size="small">
              <el-table-column label="Key" min-width="150">
                <template #default="{ row }">
                  <el-input v-model="row.key" placeholder="Param key" />
                </template>
              </el-table-column>
              <el-table-column label="Value" min-width="200">
                <template #default="{ row }">
                  <el-autocomplete
                    v-model="row.value"
                    :fetch-suggestions="querySearchVars"
                    placeholder="Param value"
                    :trigger-on-focus="false"
                    @select="handleSelectVar($event, row, 'value')"
                    @input="handleTableInput(row, 'value', $event)"
                    style="width: 100%"
                  >
                    <template #default="{ item }">
                      <div class="var-suggestion">
                        <span class="var-name">&#123;&#123; {{ item.value }} &#125;&#125;</span>
                        <span class="var-val">{{ item.actualValue }}</span>
                      </div>
                    </template>
                  </el-autocomplete>
                </template>
              </el-table-column>
              <el-table-column label="描述" min-width="150">
                <template #default="{ row }">
                  <el-input v-model="row.description" placeholder="描述（可选）" />
                </template>
              </el-table-column>
              <el-table-column label="操作" width="60" align="center">
                <template #default="{ row, $index }">
                  <el-button type="danger" size="small" text @click="removeParam($index)">
                    <el-icon><Delete /></el-icon>
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-tab-pane>

        <!-- Body -->
        <el-tab-pane label="Body" name="body">
          <div class="tab-content">
            <div class="body-type-selector">
              <el-radio-group v-model="caseForm.bodyType">
                <el-radio value="none">none</el-radio>
                <el-radio value="raw">raw</el-radio>
                <el-radio value="form-data">form-data</el-radio>
              </el-radio-group>
            </div>

            <!-- Raw Body -->
            <div v-if="caseForm.bodyType === 'raw'" class="raw-editor">
              <div class="content-type-selector">
                <el-select v-model="caseForm.contentType" style="width: 150px">
                  <el-option label="JSON" value="application/json" />
                  <el-option label="XML" value="application/xml" />
                  <el-option label="Text" value="text/plain" />
                  <el-option label="HTML" value="text/html" />
                </el-select>
              </div>
              <JsonEditor
                v-model="caseForm.payload"
                :content-type="caseForm.contentType"
              />
            </div>

            <!-- Form Data -->
            <div v-if="caseForm.bodyType === 'form-data'" class="form-data-editor">
              <el-table :data="caseForm.formData" border size="small">
                <el-table-column label="Key" min-width="150">
                  <template #default="{ row }">
                    <el-input v-model="row.key" placeholder="参数名" />
                  </template>
                </el-table-column>
                <el-table-column label="Value" min-width="200">
                  <template #default="{ row }">
                    <el-autocomplete
                      v-model="row.value"
                      :fetch-suggestions="querySearchVars"
                      placeholder="参数值"
                      :trigger-on-focus="false"
                      @select="handleSelectVar($event, row, 'value')"
                      @input="handleTableInput(row, 'value', $event)"
                      style="width: 100%"
                    >
                      <template #default="{ item }">
                        <div class="var-suggestion">
                          <span class="var-name">&#123;&#123; {{ item.value }} &#125;&#125;</span>
                          <span class="var-val">{{ item.actualValue }}</span>
                        </div>
                      </template>
                    </el-autocomplete>
                  </template>
                </el-table-column>
                <el-table-column label="操作" width="60" align="center">
                  <template #default="{ row, $index }">
                    <el-button type="danger" size="small" text @click="removeFormData($index)">
                      <el-icon><Delete /></el-icon>
                    </el-button>
                  </template>
                </el-table-column>
              </el-table>
              <el-button size="small" style="margin-top: 12px" @click="addFormData">
                <el-icon><Plus /></el-icon>
                添加参数
              </el-button>
            </div>
          </div>
        </el-tab-pane>

        <!-- Extractors -->
        <el-tab-pane label="Extractors" name="extractors">
          <div class="tab-content">
            <div class="table-toolbar">
              <span class="toolbar-title">变量提取</span>
              <el-button size="small" @click="addExtractor">
                <el-icon><Plus /></el-icon>
                添加
              </el-button>
            </div>
            <el-table :data="caseForm.extractors" border size="small">
              <el-table-column label="变量名" min-width="120">
                <template #default="{ row }">
                  <el-input v-model="row.variableName" placeholder="变量名" />
                </template>
              </el-table-column>
              <el-table-column label="提取类型" width="130">
                <template #default="{ row }">
                  <el-select v-model="row.extractorType">
                    <el-option label="JSONPath" value="jsonpath" />
                    <el-option label="Regex" value="regex" />
                    <el-option label="CSS Selector" value="css" />
                  </el-select>
                </template>
              </el-table-column>
              <el-table-column label="表达式" min-width="200">
                <template #default="{ row }">
                  <el-input v-model="row.expression" placeholder="提取表达式" />
                </template>
              </el-table-column>
              <el-table-column label="默认值" min-width="120">
                <template #default="{ row }">
                  <el-input v-model="row.defaultValue" placeholder="默认值（可选）" />
                </template>
              </el-table-column>
              <el-table-column label="操作" width="60" align="center">
                <template #default="{ row, $index }">
                  <el-button type="danger" size="small" text @click="removeExtractor($index)">
                    <el-icon><Delete /></el-icon>
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-tab-pane>

        <!-- Assertions -->
        <el-tab-pane label="Assertions" name="assertions">
          <div class="tab-content">
            <div class="table-toolbar">
              <span class="toolbar-title">断言规则 (支持拖拽排序)</span>
              <el-button size="small" @click="addAssertion">
                <el-icon><Plus /></el-icon>
                添加断言
              </el-button>
              <el-button size="small" type="success" @click="openAssertTemplateDialog" style="margin-left: 8px;">
                <el-icon><Collection /></el-icon>
                模板
              </el-button>
            </div>
            <div class="assertions-hint">
              <el-alert type="info" :closable="false" show-icon>
                <template #title>
                  期望值支持变量替换，可使用 &#123;&#123;变量名&#125;&#125; 引用上下文变量（提取变量或数据驱动变量）
                </template>
              </el-alert>
            </div>
              <draggable
                v-model="caseForm.assertions"
                item-key="id"
                handle=".drag-handle"
                class="assertions-draggable"
              >
                <template #item="{ element, index }">
                  <div class="assertion-row" :key="element.id">
                    <div class="drag-handle">
                      <el-icon><Rank /></el-icon>
                    </div>
                    <div class="assertion-cell">
                      <el-select v-model="element.target" style="width: 100%;">
                        <el-option label="状态码" value="status_code" />
                        <el-option label="JSON体" value="response_body" />
                        <el-option label="响应头" value="response_header" />
                        <el-option label="响应时间(ms)" value="response_time" />
                      </el-select>
                    </div>
                    <div class="assertion-cell" v-show="showExpressionColumn">
                      <el-input
                        v-if="element.target === 'response_body'"
                        v-model="element.expression"
                        placeholder="JSONPath 表达式，例如 $.data.code"
                        style="width: 100%"
                      />
                    </div>
                    <div class="assertion-cell">
                      <el-select v-model="element.operator" style="width: 100%;">
                        <el-option label="等于" value="==" />
                        <el-option label="不等于" value="!=" />
                        <el-option label="包含" value="contains" />
                        <el-option label="不包含" value="not_contains" />
                        <el-option label="小于" value="<" />
                        <el-option label="大于" value=">" />
                        <el-option label="小于等于" value="<=" />
                        <el-option label="大于等于" value=">=" />
                        <el-option label="范围匹配" value="range" />
                        <el-option label="正则匹配" value="regex" />
                        <el-option label="不为空" value="not_empty" />
                        <el-option label="为空" value="empty" />
                        <el-option label="存在" value="exists" />
                        <el-option label="不存在" value="not_exists" />
                      </el-select>
                    </div>
                    <div class="assertion-cell">
                      <el-autocomplete
                        v-model="element.expected"
                        :fetch-suggestions="querySearchVars"
                        placeholder="期望值，支持 &#123;&#123;var&#125;&#125;"
                        :trigger-on-focus="false"
                        @select="handleSelectVar($event, element, 'expected')"
                        @input="handleTableInput(element, 'expected', $event)"
                        style="width: 100%"
                      >
                        <template #default="{ item }">
                          <div class="var-suggestion">
                            <span class="var-name">&#123;&#123; {{ item.value }} &#125;&#125;</span>
                            <span class="var-val">{{ item.actualValue }}</span>
                          </div>
                        </template>
                      </el-autocomplete>
                    </div>
                    <div class="assertion-cell">
                      <el-button type="danger" size="small" text @click="removeAssertion(index)">
                        <el-icon><Delete /></el-icon>
                      </el-button>
                    </div>
                  </div>
                </template>
              </draggable>
          </div>
        </el-tab-pane>

        <!-- 前置脚本 -->
        <el-tab-pane label="前置脚本" name="pre_script">
          <div class="tab-content">
            <div class="table-toolbar">
              <span class="toolbar-title">前置脚本 (请求前执行)</span>
              <el-select
                v-model="caseForm.pre_script_language"
                size="small"
                style="width: 130px;"
                placeholder="脚本语言"
              >
                <el-option label="JavaScript" value="javascript" />
                <el-option label="Python" value="python" />
              </el-select>
            </div>
            <p class="script-hint">支持 pm.* API: pm.environment.get/set, pm.globals.get/set, pm.sessionVariables.get/set</p>
            <CodeEditor v-model="caseForm.pre_script" :language="caseForm.pre_script_language || 'javascript'" :hide-run="true" />
          </div>
        </el-tab-pane>

        <!-- 后置脚本 -->
        <el-tab-pane label="后置脚本" name="post_script">
          <div class="tab-content">
            <div class="table-toolbar">
              <span class="toolbar-title">后置脚本 (请求后执行)</span>
              <el-select
                v-model="caseForm.post_script_language"
                size="small"
                style="width: 130px;"
                placeholder="脚本语言"
              >
                <el-option label="JavaScript" value="javascript" />
                <el-option label="Python" value="python" />
              </el-select>
            </div>
            <p class="script-hint">支持 pm.* API: pm.response.json(), pm.response.status, pm.test(), pm.expect()</p>
            <CodeEditor v-model="caseForm.post_script" :language="caseForm.post_script_language || 'javascript'" :hide-run="true" />
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>

    <!-- 悬浮按钮，用于打开变量字典 -->
    <div class="var-dictionary-btn" @click="handleOpenVarDrawer" title="打开变量字典">
      <el-icon><Reading /></el-icon>
      <span class="btn-text">变量</span>
    </div>

    <!-- 变量字典抽屉 (内部) -->
    <el-drawer
      v-model="showVarDrawer"
      title="环境变量字典"
      direction="rtl"
      size="300px"
      append-to-body
      :z-index="3000"
    >
      <div class="var-drawer-content">
        <el-input
          v-model="varSearchQuery"
          placeholder="搜索变量名..."
          prefix-icon="Search"
          clearable
          style="margin-bottom: 16px;"
        />

        <div v-if="filteredVars.length === 0" class="empty-vars">
          <el-empty description="未找到匹配的变量" :image-size="60" />
        </div>

        <div class="var-list" v-else>
          <div
            v-for="v in filteredVars"
            :key="v.value"
            class="var-item"
            @click="copyVarToClipboard(v.value)"
          >
            <div class="var-item-left">
              <div class="var-name-bold">&#123;&#123; {{ v.value }} &#125;&#125;</div>
              <div class="var-val-preview">{{ v.actualValue }}</div>
            </div>
            <el-icon class="copy-icon"><DocumentCopy /></el-icon>
          </div>
        </div>
      </div>
    </el-drawer>

    <!-- 底部按钮 -->
    <div v-if="embedded" class="drawer-footer embedded-footer">
      <el-button @click="handleClose">取消</el-button>
      <el-button type="info" @click="handleSave" :loading="saving" :disabled="saving">仅保存</el-button>
      <el-button type="primary" @click="handleSaveAndRun" :loading="saving" :disabled="saving">
        <el-icon><VideoPlay /></el-icon>
        保存并运行
      </el-button>
    </div>
    <template v-if="!embedded" #footer>
      <div class="drawer-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button type="info" @click="handleSave" :loading="saving" :disabled="saving">仅保存</el-button>
        <el-button type="primary" @click="handleSaveAndRun" :loading="saving" :disabled="saving">
          <el-icon><VideoPlay /></el-icon>
          保存并运行
        </el-button>
      </div>
    </template>
    <HelpDrawer v-model="showHelp" :title="helpData.title" :intro="helpData.intro" :sections="helpData.sections" />
    <!-- 用例版本管理面板 -->
    <CaseVersionManager
      v-model="showVersionManager"
      :case-id="versionCaseId"
      @restored="handleVersionRestored"
    />
  </component>

  <!-- 断言模板选择对话框 -->
  <el-dialog v-model="assertTemplateDialogVisible" title="选择断言模板" width="650px" destroy-on-close>
    <div v-loading="assertTemplatesLoading">
      <el-radio-group v-model="assertTemplateCategory" size="small" @change="loadAssertTemplates">
        <el-radio-button label="">全部</el-radio-button>
        <el-radio-button v-for="cat in assertTemplateCategories" :key="cat" :label="cat">{{ cat }}</el-radio-button>
      </el-radio-group>

      <div class="template-grid" style="margin-top: 16px;">
        <div
          v-for="tpl in assertTemplates"
          :key="tpl.id"
          class="template-card"
          @click="applyAssertTemplate(tpl)"
        >
          <div class="template-header">
            <el-tag size="small">{{ tpl.category }}</el-tag>
            <span class="template-name">{{ tpl.name }}</span>
          </div>
          <p class="template-desc">{{ tpl.description }}</p>
          <pre class="template-code">{{ tpl.code_snippet }}</pre>
        </div>
      </div>
    </div>
  </el-dialog>
</template>

<script setup>
import { ref, watch, toRaw, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox, ElDrawer } from 'element-plus'
import { Plus, VideoPlay, Delete, Rank, Reading, Search, DocumentCopy, Collection, Clock } from '@element-plus/icons-vue'
import JsonEditor from './JsonEditor.vue'
import CodeEditor from '@/components/CodeEditor.vue'
import draggable from 'vuedraggable'
import autoTestRequest from '@/utils/autoTestRequest'
import HelpDrawer from '@/components/HelpDrawer.vue'
import CaseVersionManager from '@/components/CaseVersionManager.vue'
import { helpContent } from '@/utils/help-content'

const props = defineProps({
  modelValue: Boolean,
  caseData: Object,
  groupId: [Number, String],
  isEdit: Boolean,
  envId: [Number, String],
  // 内嵌模式：渲染为面板（用于 Tab 编辑器），而非 el-drawer 对话框
  embedded: { type: Boolean, default: false }
})

const emit = defineEmits(['update:modelValue', 'success', 'run', 'close', 'dirty-change', 'title-change', 'version-restored'])

// 非内嵌模式下传给 el-drawer 的属性绑定（内嵌模式下不使用）
const drawerBindings = computed(() => props.embedded ? {} : {
  modelValue: props.modelValue,
  title: props.isEdit ? '编辑用例' : '新建用例',
  direction: 'rtl',
  size: drawerSize.value,
  closeOnClickModal: true,
  closeOnPressEscape: true,
})

const activeTab = ref('headers')
const showHelp = ref(false)
const helpData = helpContent.caseEditor
// 版本管理面板状态
const showVersionManager = ref(false)
const versionCaseId = ref(null)
const availableVariables = ref([]) // 用于存储当前所有可用变量

// 动态抽屉宽度：根据屏幕宽度自适应，全屏时更大
const mainDrawerRef = ref(null)
const drawerSize = ref('50%')
const updateDrawerSize = () => {
  if (typeof window === 'undefined') { drawerSize.value = '50%'; return }
  const w = window.innerWidth
  if (w >= 1600) drawerSize.value = '70%'
  else if (w >= 1200) drawerSize.value = '60%'
  else drawerSize.value = '50%'
}
onMounted(() => {
  updateDrawerSize()
  window.addEventListener('resize', updateDrawerSize)
  document.addEventListener('fullscreenchange', updateDrawerSize)
})
onUnmounted(() => {
  window.removeEventListener('resize', updateDrawerSize)
  document.removeEventListener('fullscreenchange', updateDrawerSize)
})
// 绕过 Element Plus 内部缓存，直接强制更新 DOM 宽度（仅非内嵌模式需要）
watch([drawerSize, () => props.modelValue], async ([size, visible]) => {
  if (props.embedded) return
  if (!visible) return
  await nextTick()
  await nextTick() // 等 teleport 渲染完成
  const el = mainDrawerRef.value?.$el?.querySelector?.('.el-drawer.rtl')
  if (el) el.style.setProperty('width', size, 'important')
})

// 变量字典抽屉相关
const showVarDrawer = ref(false)
const varSearchQuery = ref('')

// 记载环境变量字典（用于自动补全）
const loadVariables = async () => {
  try {
    const varMap = new Map()
    
    // 1. 加载全局变量
    try {
      const globalVarsRes = await autoTestRequest.get('/auto-test/global-variables')
      const globalVars = Array.isArray(globalVarsRes) ? globalVarsRes : []
      globalVars.forEach(varItem => {
        varMap.set(varItem.name, { 
          value: varItem.name, 
          actualValue: varItem.is_encrypted ? '******' : varItem.value 
        })
      })
    } catch (globalError) {
      console.error('加载全局变量失败:', globalError)
    }
    
    // 2. 加载环境变量（会覆盖全局变量）
    // 如果有当前选中的环境 ID，只加载该环境的变量；否则加载全部环境
    let envs = []
    if (props.envId) {
      try {
        const env = await autoTestRequest.get(`/auto-test/environments/${props.envId}`)
        envs = env ? [env] : []
      } catch (envError) {
        console.error('加载选中环境变量失败，降级加载全部:', envError)
        const res = await autoTestRequest.get('/auto-test/environments')
        envs = Array.isArray(res) ? res : []
      }
    } else {
      const res = await autoTestRequest.get('/auto-test/environments')
      envs = Array.isArray(res) ? res : []
    }
    envs.forEach(env => {
      // 获取 base_url
      if (env.base_url) {
        varMap.set('base_url', { value: 'base_url', actualValue: env.base_url })
      }
      // 获取 variables
      if (env.variables) {
        Object.entries(env.variables).forEach(([k, v]) => {
          varMap.set(k, { value: k, actualValue: v })
        })
      }
    })

    // 如果后端没返回任何变量，显示空列表而非模拟数据
    // 避免用户误以为模拟变量是真实可用的

    availableVariables.value = Array.from(varMap.values())
  } catch (error) {
    console.error('加载环境变量失败:', error)
    // 降级：显示空列表而非模拟数据
    availableVariables.value = []
  }
}

onMounted(() => {
  loadVariables()
  // 🔥 体验1：注册 Ctrl+S（保存）和 Ctrl+Enter（保存并运行）快捷键
  window.addEventListener('keydown', handleGlobalKeydown)
  // 监听 Tab 容器派发的"保存当前激活 Tab"自定义事件（关闭未保存 Tab 时选择"保存"触发）
  window.addEventListener('editor-tabs:save-active', handleSaveActiveTab)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleGlobalKeydown)
  window.removeEventListener('editor-tabs:save-active', handleSaveActiveTab)
})

// 全局快捷键处理（仅在嵌入式/抽屉可见时生效，避免影响其他页面输入）
const handleGlobalKeydown = (e) => {
  // 只在当前组件可见时响应：内嵌模式或抽屉打开
  const visible = props.embedded || props.modelValue
  if (!visible) return
  const isCtrl = e.ctrlKey || e.metaKey
  if (!isCtrl) return
  // Ctrl+S / Cmd+S
  if (e.key === 's' || e.key === 'S') {
    e.preventDefault()
    handleSave({ skipVersionPrompt: true })
    return
  }
  // Ctrl+Enter / Cmd+Enter
  if (e.key === 'Enter') {
    e.preventDefault()
    handleSaveAndRun()
    return
  }
}

// 处理 Tab 容器请求保存当前 Tab 的事件
const handleSaveActiveTab = (e) => {
  // 只在嵌入式模式下响应（避免抽屉模式重复保存）
  if (!props.embedded) return
  handleSave({ skipVersionPrompt: true })
}

// 🔥 体验2：环境切换后重新加载变量字典
watch(() => props.envId, () => {
  loadVariables()
})

// 打开变量字典抽屉
const handleOpenVarDrawer = () => {
  // 确保 availableVariables 已经加载
  if (availableVariables.value.length === 0) {
    loadVariables().then(() => {
      showVarDrawer.value = true
    })
  } else {
    showVarDrawer.value = true
  }
}

// === 变量字典抽屉逻辑 ===
const filteredVars = computed(() => {
  if (!varSearchQuery.value) return availableVariables.value
  const query = varSearchQuery.value.toLowerCase()
  return availableVariables.value.filter(v =>
    v.value.toLowerCase().includes(query) ||
    (v.actualValue && v.actualValue.toString().toLowerCase().includes(query))
  )
})

const copyVarToClipboard = async (varName) => {
  const textToCopy = `{{${varName}}}`
  try {
    await navigator.clipboard.writeText(textToCopy)
    ElMessage.success(`已复制 ${textToCopy} 到剪贴板`)
    showVarDrawer.value = false // 复制后自动收起抽屉
  } catch (err) {
    // 降级方案
    const textArea = document.createElement("textarea")
    textArea.value = textToCopy
    document.body.appendChild(textArea)
    textArea.focus()
    textArea.select()
    try {
      document.execCommand('copy')
      ElMessage.success(`已复制 ${textToCopy} 到剪贴板`)
      showVarDrawer.value = false
    } catch (err2) {
      ElMessage.error('复制失败，请手动输入')
    }
    document.body.removeChild(textArea)
  }
}

// 表单数据
// 🔥 Bug 8 修复：生成稳定且不碰撞的唯一 ID（断言/headers/extractors 行拖拽 key）
// 优先使用 crypto.randomUUID()，老浏览器降级到 Date.now()+随机串
const genUniqueId = (prefix = '') => {
  const rand = (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function')
    ? crypto.randomUUID()
    : `${Date.now()}_${Math.random().toString(36).slice(2, 11)}`
  return prefix ? `${prefix}_${rand}` : rand
}
const caseForm = ref({
  method: 'GET',
  name: '',
  url: '',
  description: '',
  headers: [],
  params: [],
  bodyType: 'none',
  contentType: 'application/json',
  payload: '',
  formData: [],
  extractors: [],
  assertions: [],
  pre_script: null,
  post_script: null,
  // 🔥 修复：保留脚本语言字段，否则前端无法触发 Python 脚本执行流程
  pre_script_language: 'javascript',
  post_script_language: 'javascript',
  response_schema: null,
})

// 断言模板相关
const assertTemplateDialogVisible = ref(false)
const assertTemplateCategory = ref('')
const assertTemplates = ref([])
const assertTemplateCategories = ref([])
const assertTemplatesLoading = ref(false)

// === 变量补全逻辑 ===
let currentInputPos = 0
let isTriggeringVars = false

const querySearchVars = (queryString, cb) => {
  // 如果输入包含 {{，则触发补全
  const lastIndex = queryString.lastIndexOf('{{')
  if (lastIndex !== -1) {
    // 提取 {{ 之后的字符串作为搜索词
    const searchKey = queryString.substring(lastIndex + 2).trim()
    // 如果还没闭合 }}
    if (!searchKey.includes('}')) {
      const results = searchKey
        ? availableVariables.value.filter(v => v.value.toLowerCase().includes(searchKey.toLowerCase()))
        : availableVariables.value
      cb(results)
      return
    }
  }
  cb([])
}

const handleSelectVar = (item, targetObj, targetProp) => {
  // 处理选中事件
  let currentVal = ''
  if (typeof targetObj === 'string') {
    // 处理 url
    currentVal = caseForm.value[targetObj] || ''
  } else {
    // 处理 row 里的属性
    currentVal = targetObj[targetProp] || ''
  }

  const lastIndex = currentVal.lastIndexOf('{{')
  if (lastIndex !== -1) {
    // 替换为 {{varName}}
    const newVal = currentVal.substring(0, lastIndex) + '{{' + item.value + '}}'
    if (typeof targetObj === 'string') {
      caseForm.value[targetObj] = newVal
    } else {
      targetObj[targetProp] = newVal
    }
  }
}

const handleTableInput = (row, prop, val) => {
  row[prop] = val
}
// ====================

// 初始化表单数据
const initFormData = (data) => {
  if (data) {
    // 编辑模式：从传入的完整数据初始化
    // 🔥 修复：使用深拷贝确保数据独立，避免引用问题
    const rawHeaders = data.headers
    const rawParams = data.params
    const rawFormData = data.form_data
    const rawExtractors = data.extractors
    const rawAssertions = data.assertions ?? data.assert_rules
    const rawPayload = data.payload
    
    // 🔥 深拷贝并解析 headers
    let parsedHeaders = []
    if (Array.isArray(rawHeaders)) {
      parsedHeaders = JSON.parse(JSON.stringify(rawHeaders))
    } else if (rawHeaders && typeof rawHeaders === 'object') {
      parsedHeaders = Object.entries(rawHeaders).map(([key, value], index) => ({
        id: `hdr_${Date.now()}_${index}`,
        key,
        value: value || '',
        description: ''
      }))
    }
    
    // 🔥 深拷贝并解析 params
    let parsedParams = []
    if (Array.isArray(rawParams)) {
      parsedParams = JSON.parse(JSON.stringify(rawParams))
    } else if (rawParams && typeof rawParams === 'object') {
      parsedParams = Object.entries(rawParams).map(([key, value], index) => ({
        id: `param_${Date.now()}_${index}`,
        key,
        value: value || '',
        description: ''
      }))
    }
    
    // 🔥 深拷贝并解析 form_data
    // 注意：后端 AutoTestCase 模型没有 form_data 列，form-data 模式下数据保存在 payload 中
    // 因此当 body_type='form-data' 且 form_data 字段缺失时，需要从 payload 回填
    let parsedFormData = []
    const rawBodyTypeForForm = data.body_type || 'none'
    let effectiveFormData = rawFormData
    if (!effectiveFormData && (rawBodyTypeForForm === 'form-data' || rawBodyTypeForForm === 'form_data') && data.payload && typeof data.payload === 'object' && !Array.isArray(data.payload)) {
      effectiveFormData = data.payload
    }
    if (Array.isArray(effectiveFormData)) {
      parsedFormData = JSON.parse(JSON.stringify(effectiveFormData))
    } else if (effectiveFormData && typeof effectiveFormData === 'object') {
      parsedFormData = Object.entries(effectiveFormData).map(([key, value], index) => ({
        id: `fd_${Date.now()}_${index}`,
        key,
        value: value || ''
      }))
    }
    
    // 🔥 关键修复：深拷贝 extractors，确保正确回显
    let parsedExtractors = []
    if (Array.isArray(rawExtractors)) {
      parsedExtractors = JSON.parse(JSON.stringify(rawExtractors)).map((item, index) => ({
        id: item.id || `ext_${Date.now()}_${index}`,
        variableName: item.variableName || item.var_name || item.variable || '',
        extractorType: item.extractorType || item.type || 'jsonpath',
        expression: item.expression || item.path || '',
        defaultValue: item.defaultValue || item.default || ''
      }))
    }
    
    // 🔥 深拷贝并解析 assertions/assert_rules
    let parsedAssertions = []
    if (Array.isArray(rawAssertions)) {
      parsedAssertions = JSON.parse(JSON.stringify(rawAssertions)).map((item, index) => {
        if (item.target) {
          // 兼容旧数据：json_body 映射为 response_body
          const normalizedTarget = item.target === 'json_body' ? 'response_body' : item.target
          return { ...item, target: normalizedTarget, id: item.id || `ast_${genUniqueId()}_${index}` }
        }
        return {
          id: `ast_${genUniqueId()}_${index}`,
          target: item.field === 'body' ? 'response_body' : (item.field || 'status_code'),
          operator: mapOldOperator(item.operator),
          expected: item.expectedValue || item.expected || '',
          expression: item.expression || ''
        }
      })
    }
    
    // 🔥 深拷贝 payload
    let parsedPayload = ''
    if (rawPayload !== null && rawPayload !== undefined) {
      if (typeof rawPayload === 'object') {
        parsedPayload = JSON.stringify(rawPayload, null, 2)
      } else {
        parsedPayload = String(rawPayload)
      }
    }
    
    // 🔥 bodyType 映射：后端可能存了 'json'，但 radio 只认 none/raw/form-data
    const rawBodyType = data.body_type || 'none'
    const bodyTypeMap = { 'json': 'raw', 'raw': 'raw', 'form-data': 'form-data', 'none': 'none' }
    const mappedBodyType = bodyTypeMap[rawBodyType] || rawBodyType

    // 🔥 content_type 映射：根据 bodyType 补全
    let mappedContentType = data.content_type || 'application/json'
    if (rawBodyType === 'json' && !data.content_type) {
      mappedContentType = 'application/json'
    }

    caseForm.value = {
      group_id: data.group_id || null,   // 🔥 保留用例自己的分组 ID，编辑模式下绝不丢失
      method: data.method || 'GET',
      name: data.name || '',
      url: data.url || '',
      description: data.description || '',
      headers: parsedHeaders,
      params: parsedParams,
      bodyType: mappedBodyType,
      contentType: mappedContentType,
      payload: parsedPayload,
      formData: parsedFormData,
      extractors: parsedExtractors,
      assertions: parsedAssertions,
      pre_script: data.pre_script || '',
      post_script: data.post_script || '',
      // 🔥 修复：回填脚本语言字段，否则编辑保存后语言丢失，Python 脚本退化为 JS 执行
      pre_script_language: data.pre_script_language || 'javascript',
      post_script_language: data.post_script_language || 'javascript',
      response_schema: data.response_schema || null,
    }
    
    // 🔥 如果有 body 内容，自动切到 Body Tab 让用户直接看到
    if (mappedBodyType !== 'none' || parsedPayload) {
      activeTab.value = 'body'
    }
    
  } else {
    // 新建模式
    caseForm.value = {
      method: 'GET',
      name: '',
      url: '',
      description: '',
      headers: [],
      params: [],
      bodyType: 'none',
      contentType: 'application/json',
      payload: '',
      formData: [],
      extractors: [],
      assertions: [],
      pre_script: '',
      post_script: '',
      pre_script_language: 'javascript',
      post_script_language: 'javascript',
      response_schema: null,
    }
  }
}

// 🔥 抽屉打开时，如果是编辑模式，强制从后端获取完整数据
let loadVersion = 0
watch(() => props.modelValue, async (visible) => {
  if (visible) {
    loadVariables() // 每次打开重新加载一下变量
    if (props.isEdit && props.caseData?.id) {
      // 编辑模式：先获取完整用例详情
      loadVersion++
      const currentVersion = loadVersion
      try {
        const res = await autoTestRequest.get(`/auto-test/cases/${props.caseData.id}`)
        if (loadVersion !== currentVersion) return
        initFormData(res)
      } catch (e) {
        if (loadVersion !== currentVersion) return
        console.error('获取用例详情失败', e)
        // 降级：用列表数据初始化
        initFormData(props.caseData)
      }
    } else {
      // 新建模式
      initFormData(null)
    }
  }
})

// ===== 内嵌模式（Tab 编辑器）专用逻辑 =====
// 内嵌模式下不依赖 modelValue，而是监听 caseData 变化来初始化表单
// 配合 keep-alive：每个 tab 拥有独立的组件实例，切换 tab 时 caseData 引用变化触发初始化
let skipDirty = false
const initFormDataWithDirtyReset = (data) => {
  skipDirty = true
  initFormData(data)
  // 等待表单赋值产生的响应式更新落地后再放开脏标记监听
  nextTick(() => { skipDirty = false })
}

watch(
  () => props.embedded ? props.caseData : null,
  async (data) => {
    if (!props.embedded) return
    // 变量字典由 onMounted 统一加载，此处不再重复请求
    if (props.isEdit && data?.id) {
      loadVersion++
      const currentVersion = loadVersion
      try {
        const res = await autoTestRequest.get(`/auto-test/cases/${data.id}`)
        if (loadVersion !== currentVersion) return
        initFormDataWithDirtyReset(res)
      } catch (e) {
        if (loadVersion !== currentVersion) return
        console.error('获取用例详情失败', e)
        initFormDataWithDirtyReset(data)
      }
    } else {
      initFormDataWithDirtyReset(data)
    }
  },
  { immediate: true }
)

// 内嵌模式下，表单变化时通知父组件标记脏（初始化赋值期间跳过）
watch(caseForm, () => {
  if (!props.embedded || skipDirty) return
  emit('dirty-change', true)
}, { deep: true })

// 内嵌模式下，用例名称变化时同步 tab 标题
watch(() => caseForm.value.name, (name) => {
  if (!props.embedded) return
  emit('title-change', name || '未命名用例')
})

// 🔧 通用 JSON 解析工具
const parseJson = (str, isAssertRules = false) => {
  if (!str) return []
  if (Array.isArray(str)) {
    // 自动为数据添加一个唯一 id 用于拖拽
    const processArray = (arr) => arr.map((item, index) => ({ ...item, id: item.id || `item_${Date.now()}_${index}` }))

    if (isAssertRules && str.length > 0) {
      return processArray(str.map(item => {
        if (item.target) return item
        const newItem = {
          target: item.field === 'body' ? 'json_body' : (item.field || 'status_code'),
          operator: mapOldOperator(item.operator),
          expected: item.expectedValue || '',
          expression: ''
        }
        return newItem
      }))
    }
    return processArray(str)
  }

  if (typeof str === 'object') {
    if (isAssertRules) {
      const assertions = []
      if (Array.isArray(str)) {
        return str.map((item, index) => {
          if (item.target) return { ...item, id: `ast_${genUniqueId()}_${index}` }
          return {
            id: `ast_${genUniqueId()}_${index}`,
            target: item.field === 'body' ? 'json_body' : (item.field || 'status_code'),
            operator: mapOldOperator(item.operator),
            expected: item.expectedValue || '',
            expression: ''
          }
        })
      }
      let idx = 0
      for (const [field, value] of Object.entries(str)) {
        const newItem = {
          id: `ast_${genUniqueId()}_${idx++}`,
          target: field === 'body' ? 'json_body' : field,
          operator: '==',
          expected: '',
          expression: ''
        }
        if (value && typeof value === 'object') {
          newItem.operator = mapOldOperator(value.operator || 'equals')
          newItem.expected = value.expectedValue || value.eq || ''
        } else {
          newItem.expected = String(value)
        }
        assertions.push(newItem)
      }
      return assertions
    }
    // 确保返回数组，即使输入是对象
    return Array.isArray(str) ? str : []
  }

  try {
    const parsed = JSON.parse(str)
    if (isAssertRules && parsed && typeof parsed === 'object') {
      if (Array.isArray(parsed)) {
        return parsed.map((item, index) => {
          if (item.target) return { ...item, id: `ast_${genUniqueId()}_${index}` }
          return {
            id: `ast_${genUniqueId()}_${index}`,
            target: item.field === 'body' ? 'json_body' : (item.field || 'status_code'),
            operator: mapOldOperator(item.operator),
            expected: item.expectedValue || '',
            expression: ''
          }
        })
      } else {
        const assertions = []
        let idx = 0
        for (const [field, value] of Object.entries(parsed)) {
          const newItem = {
            id: `ast_${genUniqueId()}_${idx++}`,
            target: field === 'body' ? 'json_body' : field,
            operator: '==',
            expected: '',
            expression: ''
          }
          if (value && typeof value === 'object') {
            newItem.operator = mapOldOperator(value.operator || 'equals')
            newItem.expected = value.expectedValue || value.eq || ''
          } else {
            newItem.expected = String(value)
          }
          assertions.push(newItem)
        }
        return assertions
      }
    }
    if (Array.isArray(parsed)) {
        return parsed.map((item, index) => ({ ...item, id: item.id || `item_${Date.now()}_${index}` }))
    }
    return parsed
  } catch {
    return []
  }
}

// 映射旧操作符到新操作符
const mapOldOperator = (oldOp) => {
  const mapping = {
    'equals': '==',
    'not_equals': '!=',
    'eq': '==',
    'ne': '!=',
    'contains': 'contains',
    'not_contains': 'not_contains',
    'gt': '>',
    'lt': '<',
    'gte': '>=',
    'lte': '<=',
    'range': 'range',
    'regex': 'regex',
    'match': 'regex',
    'not_empty': 'not_empty',
    'empty': 'empty',
    'exists': 'exists',
    'not_exists': 'not_exists',
    'json_exists': 'exists',
  }
  return mapping[oldOp] || oldOp || '=='
}

// Headers
const addHeader = () => {
  caseForm.value.headers.push({ key: '', value: '', description: '', id: `hdr_${Date.now()}` })
}

const removeHeader = (index) => {
  caseForm.value.headers.splice(index, 1)
}

// Params
const addParam = () => {
  caseForm.value.params.push({ key: '', value: '', description: '', id: `param_${Date.now()}` })
}

const removeParam = (index) => {
  caseForm.value.params.splice(index, 1)
}

// Form Data
const addFormData = () => {
  caseForm.value.formData.push({ key: '', value: '', id: `fd_${Date.now()}` })
}

const removeFormData = (index) => {
  caseForm.value.formData.splice(index, 1)
}

// Extractors
const addExtractor = () => {
  caseForm.value.extractors.push({
    id: `ext_${Date.now()}`,
    variableName: '',
    extractorType: 'jsonpath',
    expression: '',
    defaultValue: ''
  })
}

const removeExtractor = (index) => {
  caseForm.value.extractors.splice(index, 1)
}

// Assertions
const addAssertion = () => {
  caseForm.value.assertions.push({
    id: `ast_${genUniqueId()}`,
    target: 'status_code',
    operator: '==',
    expected: '200',
    expression: ''
  })
}

const openAssertTemplateDialog = async () => {
  assertTemplateDialogVisible.value = true
  await loadAssertTemplates()
}

const loadAssertTemplates = async () => {
  assertTemplatesLoading.value = true
  try {
    const params = assertTemplateCategory.value ? { category: assertTemplateCategory.value } : {}
    const res = await autoTestRequest.get('/v1/assert-templates', { params })
    assertTemplates.value = res.templates || []

    if (assertTemplateCategories.value.length === 0) {
      const catRes = await autoTestRequest.get('/v1/assert-templates/categories')
      assertTemplateCategories.value = catRes.categories || []
    }
  } catch (e) {
    console.error('加载断言模板失败', e)
  } finally {
    assertTemplatesLoading.value = false
  }
}

const applyAssertTemplate = (tpl) => {
  // 应用模板规则到用例
  for (const rule of (tpl.rules || [])) {
    caseForm.value.assertions.push({
      id: `ast_${genUniqueId()}`,
      target: rule.type || 'status_code',
      operator: rule.operator === 'eq' ? '==' : rule.operator === 'neq' ? '!=' : rule.operator === 'lt' ? '<' : rule.operator === 'gt' ? '>' : rule.operator === 'contains' ? 'contains' : rule.operator,
      expected: String(rule.expected || ''),
      expression: rule.expression || rule.json_path || ''
    })
  }
  assertTemplateDialogVisible.value = false
  ElMessage.success(`已应用断言模板: ${tpl.name}`)
}

const removeAssertion = (index) => {
  caseForm.value.assertions.splice(index, 1)
}

// 检查是否需要显示表达式列（只要有一个断言目标是 response_body 就显示
const showExpressionColumn = computed(() => {
  return caseForm.value.assertions.some(a => a.target === 'response_body')
})

// 打开版本管理面板（仅编辑模式可用）
const openVersionManager = () => {
  if (!props.isEdit || !props.caseData?.id) {
    ElMessage.warning('请先保存用例后再管理版本')
    return
  }
  versionCaseId.value = props.caseData.id
  showVersionManager.value = true
}

// 版本恢复后回调：重新拉取用例数据以反映恢复的快照内容
const handleVersionRestored = async () => {
  if (!props.caseData?.id) return
  try {
    const res = await autoTestRequest.get(`/auto-test/cases/${props.caseData.id}`)
    if (res) {
      // 复用现有初始化逻辑刷新表单
      // 内嵌模式下需通过 initFormDataWithDirtyReset 重置脏标记，避免 deep watch 误触发 dirty-change(true)
      initFormDataWithDirtyReset(res)
      // 🔥 Bug 6 修复：通知 Tab 容器把最新后端数据写回 tab.data，避免后续切换 Tab 时丢失恢复的内容
      emit('version-restored', res)
    }
  } catch (error) {
    console.error('恢复后刷新用例失败:', error)
  }
}

// 关闭
const handleClose = () => {
  // 内嵌模式下通过 close 事件交由 Tab 容器决定是否关闭（含脏数据确认）
  if (props.embedded) {
    emit('close')
    return
  }
  emit('update:modelValue', false)
}

// 保存
const saving = ref(false)
const handleSave = async (options = {}) => {
  // 🔥 Bug 4 修复：默认 skipVersionPrompt=true（不弹版本确认框，版本快照在版本管理面板主动触发）
  const { skipVersionPrompt = true } = options
  // 并发保护：防止 Ctrl+S 与"保存并运行"重复触发
  if (saving.value) return
  if (!caseForm.value.name) {
    ElMessage.warning('请输入用例名称')
    return
  }
  if (!caseForm.value.url) {
    ElMessage.warning('请输入请求 URL')
    return
  }
  // 🔥 优化：编辑模式下使用 caseForm 自带的 group_id（来自用例本身），新建模式下才需要 tree 的 groupId
  let groupIdToUse = caseForm.value.group_id || null   // 默认用用例自己的 group_id
  if (!groupIdToUse && !props.isEdit) {
    // 纯新建 + 表单没有 group_id → 才从左侧树取
    groupIdToUse = props.groupId
  }
  if (!groupIdToUse) {
    ElMessage.warning('请先从左侧分组树选择一个分组再保存')
    return
  }

  try {
    saving.value = true
    // 🔥 强制深度拷贝，确保拿到响应式对象的真实原生数据
    const rawForm = JSON.parse(JSON.stringify(toRaw(caseForm.value)))

    // 🔥 自动补全 URL 协议（跳过包含变量模板的URL，避免产生 http://{{base_url}} 错误）
    if (rawForm.url && !rawForm.url.includes('://') && !rawForm.url.includes('{{')) {
      rawForm.url = 'http://' + rawForm.url
    }

    // 🔥 防御性空数组检查，确保任何情况下都不会发送 undefined 且确保是数组类型
    if (!Array.isArray(rawForm.headers)) rawForm.headers = []
    if (!Array.isArray(rawForm.formData)) rawForm.formData = []
    if (!Array.isArray(rawForm.extractors)) rawForm.extractors = []
    if (!Array.isArray(rawForm.assertions)) rawForm.assertions = []

    // 构建 headers 对象
    const headersObj = {}
    rawForm.headers.forEach(h => {
      if (h.key) headersObj[h.key] = h.value || ''
    })

    // 构建 params 对象
    const paramsObj = {}
    rawForm.params.forEach(item => {
      if (item.key) paramsObj[item.key] = item.value || ''
    })

    // 构建 form-data 对象
    const formDataObj = {}
    rawForm.formData.forEach(item => {
      if (item.key) formDataObj[item.key] = item.value || ''
    })

    // 构建 payload
    let payloadData = null
    if (rawForm.bodyType === 'raw' || rawForm.bodyType === 'json') {
      if (rawForm.payload && rawForm.payload.trim()) {
        if (rawForm.contentType === 'application/json') {
          // JSON 类型，必须合法
          try {
            payloadData = JSON.parse(rawForm.payload)
          } catch (e) {
            ElMessage.error('请求体 JSON 格式错误，请检查！')
            return
          }
        } else {
          // XML, Text, HTML 等类型，直接传字符串
          payloadData = rawForm.payload
        }
      } else {
        payloadData = rawForm.contentType === 'application/json' ? {} : ''
      }
    } else if (rawForm.bodyType === 'form-data') {
      // form-data 模式
      payloadData = formDataObj
    }
    // none 模式 payloadData 保持 null

    // 构建提取规则 - 传递完整的 extractors 数组
    const extractorsList = rawForm.extractors
      .filter(e => e.variableName && e.expression)
      .map(e => ({
        variableName: e.variableName,
        extractorType: e.extractorType,
        expression: e.expression,
        defaultValue: e.defaultValue || ''
      }))

    // 构建断言规则 - 只保留有效的断言，新格式：[{"target": "status_code", "operator": "==", "expected": "200", "expression": ""}, ...]
    const noExpectedOperators = ['not_empty', 'empty', 'exists', 'not_exists']
    const assertRules = rawForm.assertions
      .filter(a => {
        if (!a.target || !a.operator) return false
        if (noExpectedOperators.includes(a.operator)) return true
        return a.expected !== ''
      })
      .map(a => ({
        target: a.target,
        operator: a.operator,
        expected: a.expected,
        expression: a.expression || ''
      }))

    const payload = {
      group_id: groupIdToUse,
      method: rawForm.method,
      name: rawForm.name,
      url: rawForm.url,
      description: rawForm.description,
      body_type: rawForm.bodyType,
      content_type: rawForm.contentType,
      payload: payloadData,
      form_data: formDataObj,
      headers: headersObj,
      params: paramsObj,
      extractors: extractorsList,
      assertions: assertRules,
      pre_script: rawForm.pre_script || null,
      post_script: rawForm.post_script || null,
      // 🔥 修复：发送脚本语言字段，否则后端默认按 javascript 执行，Python 脚本流程断裂
      pre_script_language: rawForm.pre_script_language || 'javascript',
      post_script_language: rawForm.post_script_language || 'javascript',
      response_schema: rawForm.response_schema || null,
    }

    let createdCaseId = null
    const wasEdit = !!props.isEdit
    if (wasEdit) {
      await autoTestRequest.put(`/auto-test/cases/${props.caseData.id}`, payload)
      ElMessage.success('更新成功')
      createdCaseId = props.caseData.id
    } else {
      const response = await autoTestRequest.post('/auto-test/cases', payload)
      ElMessage.success('创建成功')
      // 假设后端返回新建用例的ID
      createdCaseId = response.id || response.case_id
    }

    // 🔥 Bug 1 修复：把 createdCaseId 与 wasEdit 一并回传，由 Tab 容器回写 tab.data.id 与 tab.id
    emit('success', createdCaseId, wasEdit)
    if (props.embedded) {
      // 内嵌模式下保存后保持 Tab 打开，仅清除脏标记
      emit('dirty-change', false)
    } else {
      handleClose()
    }

    // 编辑模式下保存成功后，提示是否保存为新版本快照（保存并运行跳过，避免打断运行流程）
    if (props.isEdit && !skipVersionPrompt && createdCaseId) {
      let confirmSaveVersion = false
      try {
        await ElMessageBox.confirm(
          '用例已保存成功，是否同时保存为新版本快照？',
          '保存为新版本',
          {
            confirmButtonText: '保存为新版本',
            cancelButtonText: '暂不保存',
            type: 'success',
            distinguishCancelAndClose: true,
          }
        )
        confirmSaveVersion = true
      } catch {
        // 用户点击"暂不保存"或关闭对话框，静默处理
      }
      if (confirmSaveVersion) {
        try {
          await autoTestRequest.post(`/auto-test/cases/${createdCaseId}/versions`, {})
          ElMessage.success('已保存为新版本')
        } catch (err) {
          console.error('保存新版本失败:', err)
          ElMessage.warning('保存新版本失败，可在版本管理面板重试')
        }
      }
    }

    return createdCaseId
  } catch (error) {
    console.error('保存用例失败:', error)
    if (error.response?.data) {
      console.error('后端返回的详细错误信息:', error.response.data)
    }
    ElMessage.error(props.isEdit ? '更新失败' : '创建失败')
  } finally {
    saving.value = false
  }
}

// 保存并运行
const handleSaveAndRun = async () => {
  const savedCaseId = await handleSave({ skipVersionPrompt: true })
  // 保存失败时 savedCaseId 为 undefined，不应继续运行
  if (!savedCaseId) {
    return
  }
  if (caseForm.value.name && caseForm.value.url) {
    // 确保传递真实数据，避免响应式问题
    const data = JSON.parse(JSON.stringify(toRaw(caseForm.value)))
    if (data.url && !data.url.includes('://') && !data.url.includes('{{')) {
      data.url = 'http://' + data.url
    }
    emit('run', { ...data, id: savedCaseId })
  }
}
</script>

<style scoped>
:deep(.el-drawer__body) {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  padding: 0;
}

.drawer-content {
  display: flex;
  flex-direction: column;
  flex: 1;
  overflow: hidden;
  background: var(--tm-bg-page);
}

.drawer-header {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 20px;
  background: var(--tm-bg-card);
  border-bottom: 1px solid var(--tm-border-light);
  flex-shrink: 0;
}

.top-row {
  display: flex;
  gap: 10px;
  align-items: center;
  width: 100%;
}

.description-bar {
  padding: 12px 16px;
  background: var(--tm-bg-card);
  border-bottom: 1px solid var(--tm-border-light);
  flex-shrink: 0;
}

.case-tabs {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: var(--tm-bg-card);
}

.case-tabs :deep(.el-tabs__header) {
  padding: 0 20px;
  margin: 0;
  background: var(--tm-bg-card);
  border-bottom: 1px solid var(--tm-border-light);
}

.case-tabs :deep(.el-tabs__content) {
  flex: 1;
  overflow: auto;
}

.tab-content {
  padding: 20px;
  flex: 1;
  min-height: 0;
  overflow: auto;
}

.table-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.toolbar-title {
  font-weight: 600;
  font-size: 14px;
  color: var(--tm-text-primary);
}

.body-type-selector {
  margin-bottom: 16px;
}

.raw-editor {
  border: 1px solid var(--tm-border-color);
  border-radius: var(--tm-radius-small);
  overflow: hidden;
}

.content-type-selector {
  padding: 12px;
  border-bottom: 1px solid var(--tm-border-light);
  background: var(--tm-bg-page);
}

.form-data-editor {
  margin-top: 16px;
}

.drawer-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 20px;
  background: var(--tm-bg-card);
  border-top: 1px solid var(--tm-border-light);
  flex-shrink: 0;
}

/* 内嵌模式（Tab 编辑器面板）：替代 el-drawer 外壳，撑满父容器 */
.case-editor-embedded {
  display: flex;
  flex-direction: column;
  height: 100%;
  width: 100%;
  overflow: hidden;
  background: var(--tm-bg-page);
}
.case-editor-embedded .drawer-content {
  flex: 1;
  min-height: 0;
}
.embedded-footer {
  border-top: 1px solid var(--tm-border-light);
}

.assertions-hint {
  margin-top: 12px;
}

.script-hint {
  margin: 0 0 12px;
  color: var(--tm-text-secondary);
  font-size: 12px;
}

/* 变量补全下拉框样式 */
.var-suggestion {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}
.var-name {
  color: var(--tm-color-primary);
  font-weight: 600;
}
.var-val {
  color: var(--tm-text-secondary);
  font-size: 12px;
  max-width: 150px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 悬浮变量字典按钮 */
.var-dictionary-btn {
  position: absolute;
  right: 20px;
  top: 20px;
  background: var(--tm-color-primary);
  color: var(--tm-text-primary);
  width: 80px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 20px;
  cursor: pointer;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
  z-index: 2000;
  transition: all 0.2s ease;
  font-size: 14px;
  gap: 5px;
}

.var-dictionary-btn:hover {
  background: var(--tm-color-primary-dark);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
}

.var-dictionary-btn .btn-text {
  font-weight: 500;
}

.var-dictionary-btn .el-icon {
  font-size: 16px;
}

/* 变量字典抽屉内容 */
.var-drawer-content {
  padding: 16px;
  display: flex;
  flex-direction: column;
  height: 100%;
}

.var-list {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.var-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: var(--tm-bg-card);
  border: 1px solid var(--tm-border-light);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.var-item:hover {
  border-color: var(--tm-color-primary);
  background: rgba(var(--tm-color-primary), 0.05);
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.var-item:hover .copy-icon {
  color: var(--tm-color-primary);
  opacity: 1;
}

.var-item-left {
  flex: 1;
  overflow: hidden;
}

.var-name-bold {
  font-family: monospace;
  font-weight: 600;
  color: var(--tm-color-primary);
  margin-bottom: 4px;
}

.var-val-preview {
  font-size: 12px;
  color: var(--tm-text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.copy-icon {
  font-size: 16px;
  color: var(--tm-text-regular);
  opacity: 0.6;
  transition: all 0.2s;
  margin-left: 8px;
}

.empty-vars {
  display: flex;
  justify-content: center;
  align-items: center;
  flex: 1;
}

/* 断言拖拽样式 */
.assertions-draggable {
  margin-top: 16px;
}

.assertion-row {
  display: flex;
  align-items: center;
  border: 1px solid var(--tm-border-color);
  border-bottom: none;
  background: var(--tm-bg-card);
}

.assertion-row:last-child {
  border-bottom: 1px solid var(--tm-border-color);
}

.drag-handle {
  width: 50px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: move;
  color: var(--tm-text-secondary);
  padding: 8px 0;
  flex-shrink: 0;
}

.assertion-cell {
  padding: 8px 12px;
  min-height: 40px;
  display: flex;
  align-items: center;
  border-left: 1px solid var(--tm-border-light);
  box-sizing: border-box;
}

/* 列宽设置 */
.assertion-cell:nth-child(2) { /* 断言目标 */
  min-width: 140px;
  flex: 1;
}

.assertion-cell:nth-child(3) { /* JSONPath */
  min-width: 200px;
  flex: 1;
}

.assertion-cell:nth-child(4) { /* 操作符 */
  width: 100px;
  flex-shrink: 0;
}

.assertion-cell:nth-child(5) { /* 期望值 */
  min-width: 180px;
  flex: 2;
}

.assertion-cell:nth-child(6) { /* 操作 */
  width: 60px;
  flex-shrink: 0;
  justify-content: center;
  border-left: 1px solid var(--tm-border-light);
}

.assertion-cell:first-child {
  border-left: none;
}

/* 断言模板卡片 */
.template-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(290px, 1fr)); gap: 12px; }
.template-card {
  border: 1px solid #e4e7ed; border-radius: 8px; padding: 14px; cursor: pointer;
  transition: all .2s; background: #fafafa;
}
.template-card:hover { border-color: #409EFF; box-shadow: 0 2px 8px rgba(64,158,255,.1); transform: translateY(-1px); background: #fff; }
.template-header { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }
.template-name { font-weight: 600; font-size: 13px; }
.template-desc { font-size: 12px; color: #909399; margin-bottom: 8px; }
.template-code {
  background: #2d3436; color: #dfe6e9; padding: 8px 10px; border-radius: 4px;
  font-size: 11px; overflow-x: auto; margin: 0; line-height: 1.5;
}
</style>
