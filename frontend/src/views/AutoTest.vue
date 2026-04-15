<template>
  <div class="auto-test-page">
    <!-- 新手引导横幅 -->
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
        </div>
        <el-button text @click="dismissGuide" class="guide-close">✕</el-button>
      </div>
    </div>

    <!-- 步骤提示卡片 -->
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

    <!-- 顶部导航 -->
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
      </div>
    </div>

    <!-- 接口库 Tab -->
    <div v-show="activeTab === 'interfaces'" class="tab-content">
      <div class="page-layout">
        <!-- 左侧：分组树 -->
        <div class="left-panel">
          <div class="panel-header">
            <span class="panel-title">📁 接口分组</span>
            <el-dropdown trigger="click" @command="handleFolderCommand">
              <el-button type="primary" size="small" class="btn-more">
                <el-icon><MoreFilled /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="createRoot">新建根分组</el-dropdown-item>
                  <el-dropdown-item command="createChild" :disabled="!currentGroup">新建子分组</el-dropdown-item>
                  <el-dropdown-item command="editGroup" :disabled="!currentGroup">编辑分组</el-dropdown-item>
                  <el-dropdown-item command="deleteGroup" :disabled="!currentGroup" divided>删除分组</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>

          <div class="folder-tree" v-loading="loadingGroups">
            <el-tree
              ref="folderTreeRef"
              :data="groupTreeData"
              :props="{ children: 'children', label: 'name' }"
              node-key="id"
              default-expand-all
              highlight-current
              @node-click="handleGroupSelect"
            >
              <template #default="{ node, data }">
                <span class="tree-node">
                  <span class="node-icon">{{ data.children?.length ? '📂' : '📁' }}</span>
                  <span class="node-label">{{ node.label }}</span>
                  <span class="node-count">({{ data.case_count || 0 }})</span>
                </span>
              </template>
            </el-tree>
            <el-empty v-if="!loadingGroups && groupTreeData.length === 0" description="暂无分组" class="dark-empty" />
          </div>
        </div>

        <!-- 右侧：用例列表 -->
        <div class="right-panel">
          <CaseList
            ref="caseListRef"
            :group-id="currentGroupId"
            :environment-list="environmentList"
            @run="handleRunCases"
          />
        </div>
      </div>
    </div>

    <!-- 场景管理 Tab -->
    <div v-show="activeTab === 'scenarios'" class="tab-content">
      <div class="scenario-container">
        <ScenarioList
          v-if="!currentScenarioId"
          ref="scenarioListRef"
          @edit="handleEditScenario"
        />

        <!-- 场景编排详情 -->
        <ScenarioEditor
          v-else
          :scenario-id="currentScenarioId"
          @back="currentScenarioId = null"
        />
      </div>
    </div>

    <!-- 接口调试 Tab -->
    <div v-show="activeTab === 'debug'" class="tab-content">
      <div class="debug-container">
        <!-- 调试工具栏 -->
        <div class="debug-toolbar">
          <div class="toolbar-left">
            <h2 class="debug-title">⚡ 接口调试</h2>
          </div>
          <div class="toolbar-right">
            <el-select v-model="debugEnvId" placeholder="选择环境" clearable style="width: 200px; margin-right: 12px;">
              <el-option v-for="env in environmentList" :key="env.id" :label="env.name" :value="env.id" />
            </el-select>
            <el-button type="info" size="small" @click="clearDebugForm">
              <el-icon><Delete /></el-icon>
              清空
            </el-button>
            <el-button type="info" size="small" @click="showHistory = !showHistory">
              <el-icon><Clock /></el-icon>
              历史
            </el-button>
          </div>
        </div>

        <!-- 请求配置卡片 -->
        <el-card class="debug-card request-card">
          <!-- 请求行 -->
          <div class="request-line">
            <el-select v-model="debugForm.method" class="method-select" size="large">
              <el-option v-for="m in ['GET','POST','PUT','PATCH','DELETE']" :key="m" :label="m" :value="m" />
            </el-select>
            <el-input
              v-model="debugForm.url"
              placeholder="请求URL，如 https://api.example.com/users"
              size="large"
              clearable
              class="url-input"
            >
              <template #append>
                <el-button size="large" @click="insertVariable('url')">
                  <el-icon><DataAnalysis /></el-icon>
                </el-button>
              </template>
            </el-input>
            <div class="request-actions">
              <el-input-number v-model="debugForm.timeout" :min="1" :max="60" size="large" placeholder="超时" style="width: 100px; margin-right: 12px;">
                <template #append>s</template>
              </el-input-number>
              <el-button type="primary" size="large" @click="sendDebugRequest" :loading="debugLoading" class="send-button">
                <el-icon><Right /></el-icon>
                发送
              </el-button>
            </div>
          </div>

          <!-- 请求配置 Tabs -->
          <el-tabs v-model="debugReqTab" class="request-tabs">
            <el-tab-pane label="请求头" name="headers">
              <div class="tab-content">
                <el-table :data="debugForm.headers" border size="small">
                  <el-table-column prop="key" label="键名" min-width="120">
                    <template #default="{ row }">
                      <el-input v-model="row.key" placeholder="键名" />
                    </template>
                  </el-table-column>
                  <el-table-column prop="value" label="键值" min-width="200">
                    <template #default="{ row }">
                      <el-input v-model="row.value" placeholder="键值" />
                    </template>
                  </el-table-column>
                  <el-table-column label="操作" width="80" align="center">
                    <template #default="{ $index }">
                      <el-button type="danger" size="small" @click="debugForm.headers.splice($index, 1)">
                        <el-icon><Delete /></el-icon>
                      </el-button>
                    </template>
                  </el-table-column>
                </el-table>
                <el-button size="small" type="primary" @click="debugForm.headers.push({ key: '', value: '' })" style="margin-top: 8px;">
                  <el-icon><Plus /></el-icon>
                  添加请求头
                </el-button>
              </div>
            </el-tab-pane>
            <el-tab-pane label="请求体" name="body">
              <div class="tab-content">
                <div class="body-type-selector">
                  <el-radio-group v-model="debugForm.bodyType" size="small">
                    <el-radio-button value="json">JSON</el-radio-button>
                    <el-radio-button value="form">Form</el-radio-button>
                    <el-radio-button value="text">Text</el-radio-button>
                    <el-radio-button value="xml">XML</el-radio-button>
                    <el-radio-button value="html">HTML</el-radio-button>
                  </el-radio-group>
                </div>
                <el-input
                  v-model="debugForm.body"
                  type="textarea"
                  :rows="8"
                  placeholder="请求体内容"
                  class="json-input"
                />
                <div class="body-actions">
                  <el-button size="small" type="info" @click="formatJson('body')" v-if="debugForm.bodyType === 'json'">
                    <el-icon><MagicStick /></el-icon>
                    格式化
                  </el-button>
                  <el-button size="small" type="info" @click="insertVariable('body')" style="margin-left: 8px;">
                    <el-icon><DataAnalysis /></el-icon>
                    插入变量
                  </el-button>
                </div>
              </div>
            </el-tab-pane>
            <el-tab-pane label="参数" name="params">
              <div class="tab-content">
                <el-table :data="debugForm.params" border size="small">
                  <el-table-column prop="key" label="参数名" min-width="120">
                    <template #default="{ row }">
                      <el-input v-model="row.key" placeholder="参数名" />
                    </template>
                  </el-table-column>
                  <el-table-column prop="value" label="参数值" min-width="200">
                    <template #default="{ row }">
                      <el-input v-model="row.value" placeholder="参数值" />
                    </template>
                  </el-table-column>
                  <el-table-column label="操作" width="80" align="center">
                    <template #default="{ $index }">
                      <el-button type="danger" size="small" @click="debugForm.params.splice($index, 1)">
                        <el-icon><Delete /></el-icon>
                      </el-button>
                    </template>
                  </el-table-column>
                </el-table>
                <el-button size="small" type="primary" @click="debugForm.params.push({ key: '', value: '' })" style="margin-top: 8px;">
                  <el-icon><Plus /></el-icon>
                  添加参数
                </el-button>
              </div>
            </el-tab-pane>
          </el-tabs>
        </el-card>

        <!-- 响应结果 -->
        <el-card v-if="debugResponse" class="debug-card response-card" style="margin-top: 16px;">
          <template #header>
            <div class="response-header">
              <h3 class="response-title">📊 响应结果</h3>
              <div class="response-meta">
                <el-tag :type="debugResponse.status_code < 400 ? 'success' : 'danger'" size="small" class="status-code">
                  {{ debugResponse.status_code }}
                </el-tag>
                <el-tag type="info" size="small" class="response-time">
                  <el-icon><Timer /></el-icon>
                  {{ debugResponse.elapsed_ms }}ms
                </el-tag>
                <el-tag type="info" size="small" class="content-length" v-if="debugResponse.content_length">
                  <el-icon><Document /></el-icon>
                  {{ debugResponse.content_length }}B
                </el-tag>
                <el-button size="small" type="info" @click="copyResponse" style="margin-left: 8px;">
                  <el-icon><DocumentCopy /></el-icon>
                  复制
                </el-button>
                <el-button size="small" type="primary" @click="saveToApiLibrary" style="margin-left: 8px;">
                  <el-icon><Plus /></el-icon>
                  保存到接口库
                </el-button>
              </div>
            </div>
          </template>
          <el-tabs v-model="debugResTab" class="response-tabs">
            <el-tab-pane label="响应体" name="body">
              <div class="response-body">
                <pre class="debug-response-body">{{ formattedResponse }}</pre>
              </div>
            </el-tab-pane>
            <el-tab-pane label="响应头" name="headers">
              <div class="response-body">
                <pre class="debug-response-body">{{ JSON.stringify(debugResponse.headers, null, 2) }}</pre>
              </div>
            </el-tab-pane>
            <el-tab-pane label="请求详情" name="request">
              <div class="response-body">
                <pre class="debug-response-body">{{ JSON.stringify(debugRequestDetails, null, 2) }}</pre>
              </div>
            </el-tab-pane>
          </el-tabs>
          <div v-if="debugResponse.error" class="error-message">
            <el-alert :title="debugResponse.error" type="error" show-icon :closable="false" />
          </div>
        </el-card>

        <!-- 历史记录 -->
        <el-drawer
          v-model="showHistory"
          title="📋 请求历史"
          size="600px"
          direction="rtl"
        >
          <div class="history-container">
            <el-empty v-if="debugHistory.length === 0" description="暂无历史记录" />
            <el-timeline v-else>
              <el-timeline-item
                v-for="(item, index) in debugHistory"
                :key="index"
                :timestamp="item.timestamp"
                :type="item.status_code < 400 ? 'success' : 'danger'"
              >
                <div class="history-item">
                  <div class="history-header">
                    <span class="history-method">{{ item.method }}</span>
                    <span class="history-url">{{ item.url }}</span>
                    <el-tag :type="item.status_code < 400 ? 'success' : 'danger'" size="small" style="margin-left: 8px;">
                      {{ item.status_code }}
                    </el-tag>
                  </div>
                  <div class="history-actions">
                    <el-button size="small" type="primary" @click="resendHistoryRequest(item)">
                      <el-icon><Right /></el-icon>
                      再次请求
                    </el-button>
                    <el-button size="small" @click="loadHistoryItem(item)">
                      <el-icon><Edit /></el-icon>
                      加载
                    </el-button>
                    <el-button size="small" type="danger" @click="debugHistory.splice(index, 1)">
                      <el-icon><Delete /></el-icon>
                      删除
                    </el-button>
                  </div>
                </div>
              </el-timeline-item>
            </el-timeline>
            <el-button type="danger" size="small" @click="clearHistory" v-if="debugHistory.length > 0" style="margin-top: 16px;">
              <el-icon><Delete /></el-icon>
              清空历史
            </el-button>
          </div>
        </el-drawer>

        <!-- 变量选择弹窗 -->
        <el-dialog
          v-model="showVariableDialog"
          title="插入变量"
          width="500px"
        >
          <div class="variable-dialog">
            <el-input v-model="variableSearch" placeholder="搜索变量" style="margin-bottom: 16px;">
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
            <div class="variable-list">
              <el-tag
                v-for="varItem in filteredVariables"
                :key="varItem.id"
                :type="varItem.is_encrypted ? 'warning' : 'info'"
                effect="plain"
                class="variable-tag"
                @click="insertVariableValue(varItem.name)"
              >
                <span v-text="varItem.name"></span>
                <span class="var-value" v-if="varItem.value && !varItem.is_encrypted"><span v-text="'(' + varItem.value + ')'"></span></span>
                <span class="var-value" v-else-if="varItem.is_encrypted">(加密)</span>
                <span class="var-value" v-else-if="varItem.description"><span v-text="'(' + varItem.description + ')'"></span></span>
              </el-tag>
            </div>
            <el-empty v-if="filteredVariables.length === 0" description="暂无变量" style="margin-top: 32px;" />
          </div>
          <template #footer>
            <span class="dialog-footer">
              <el-button @click="showVariableDialog = false">取消</el-button>
            </span>
          </template>
        </el-dialog>

        <!-- 保存到接口库对话框 -->
        <el-dialog
          v-model="saveToApiLibraryDialog"
          title="保存到接口库"
          width="500px"
        >
          <el-form :model="apiLibraryForm" label-width="80px">
            <el-form-item label="接口名称" required>
              <el-input v-model="apiLibraryForm.name" placeholder="请输入接口名称" />
            </el-form-item>
            <el-form-item label="所属分组" required>
              <el-select v-model="apiLibraryForm.group_id" placeholder="请选择分组">
                <el-option
                  v-for="group in apiGroups"
                  :key="group.id"
                  :label="group.name"
                  :value="group.id"
                />
              </el-select>
            </el-form-item>
            <el-form-item label="接口描述">
              <el-input
                v-model="apiLibraryForm.description"
                type="textarea"
                placeholder="请输入接口描述"
              />
            </el-form-item>
          </el-form>
          <template #footer>
            <span class="dialog-footer">
              <el-button @click="saveToApiLibraryDialog = false">取消</el-button>
              <el-button type="primary" @click="confirmSaveToApiLibrary">确定</el-button>
            </span>
          </template>
        </el-dialog>
      </div>
    </div>

    <!-- 变量管理 Tab -->
    <div v-show="activeTab === 'variables'" class="tab-content">
      <GlobalVariableManager />
    </div>

    <!-- 新建/编辑分组对话框 -->
    <el-dialog
      v-model="folderDialogVisible"
      :title="folderDialogType === 'edit' ? '编辑分组' : '新建分组'"
      width="420px"
      custom-class="dark-dialog"
    >
      <el-form :model="folderForm" label-width="60px">
        <el-form-item label="名称">
          <el-input v-model="folderForm.name" placeholder="输入分组名称" class="dark-input" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="folderForm.description" placeholder="可选描述" class="dark-input" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="folderDialogVisible = false" class="btn-cancel">取消</el-button>
        <el-button type="primary" @click="handleFolderSave" class="btn-primary">确定</el-button>
      </template>
    </el-dialog>

    <!-- 执行结果对话框 -->
    <el-dialog
      v-model="resultDialogVisible"
      title="执行结果"
      width="75%"
      destroy-on-close
      custom-class="dark-dialog"
    >
      <div class="result-content">
        <div class="result-summary">
          <el-tag :type="runResult.passed ? 'success' : 'danger'" size="large" class="result-tag">
            {{ runResult.passed ? '✓ 通过' : '✗ 失败' }}
          </el-tag>
          <span class="summary-info">
            耗时: {{ runResult.time }}ms | 断言: {{ runResult.passedAssertions }}/{{ runResult.totalAssertions }}
          </span>
        </div>
        <el-divider class="dark-divider" />
        <div class="result-detail">
          <!-- 请求信息 -->
          <h4>请求信息</h4>
          <div class="request-info">
            <div class="info-item">
              <span class="info-label">请求方法:</span>
              <el-tag type="info" size="small">{{ runResult.request.method }}</el-tag>
            </div>
            <div class="info-item">
              <span class="info-label">请求地址:</span>
              <span class="info-value">{{ runResult.request.url }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">请求头:</span>
              <pre class="info-pre">{{ typeof runResult.request.headers === 'object' ? JSON.stringify(runResult.request.headers, null, 2) : runResult.request.headers }}</pre>
            </div>
            <div class="info-item">
              <span class="info-label">请求参数:</span>
              <pre class="info-pre">{{ runResult.request.params && Object.keys(runResult.request.params).length ? JSON.stringify(runResult.request.params, null, 2) : '无' }}</pre>
            </div>
            <div class="info-item">
              <span class="info-label">请求体:</span>
              <pre class="info-pre">{{ runResult.request.body || '无' }}</pre>
            </div>
          </div>
          <el-divider class="dark-divider" />
          <!-- 响应信息 -->
          <h4>响应信息</h4>
          <div class="response-info">
            <div class="info-item">
              <span class="info-label">状态码:</span>
              <el-tag v-if="runResult.hasError" type="warning" size="small">
                连接失败
              </el-tag>
              <el-tag v-else :type="runResult.status >= 200 && runResult.status < 300 ? 'success' : 'danger'" size="small">
                {{ runResult.status || '无' }}
              </el-tag>
            </div>
            <div class="info-item">
              <span class="info-label">耗时:</span>
              <span>{{ runResult.time }}ms</span>
            </div>
          </div>
          <div v-if="runResult.errorMessage" class="error-message">
            <el-alert type="error" :title="runResult.errorMessage" :closable="false" show-icon />
          </div>
          <h4>响应体</h4>
          <pre class="response-display">{{ runResult.response.data || '无响应体' }}</pre>
          <h4 v-if="runResult.assertionResults?.length">断言结果</h4>
          <el-table
            v-if="runResult.assertionResults?.length"
            :data="runResult.assertionResults"
            border
            size="small"
            class="dark-table"
          >
            <el-table-column prop="field" label="字段" width="150" />
            <el-table-column prop="operator" label="比较" width="80" />
            <el-table-column prop="expected" label="预期值" />
            <el-table-column prop="actual" label="实际值" />
            <el-table-column label="结果" width="80" align="center">
              <template #default="{ row }">
                <el-tag :type="row.passed ? 'success' : 'danger'" size="small">
                  {{ row.passed ? '通过' : '失败' }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { MoreFilled, Document, FolderOpened, Position, DataAnalysis, Right, Delete, Clock, Timer, MagicStick, DocumentCopy } from '@element-plus/icons-vue'
import CaseList from './CaseList.vue'
import ScenarioList from './ScenarioList.vue'
import ScenarioEditor from './ScenarioEditor.vue'
import GlobalVariableManager from '../components/GlobalVariableManager.vue'
import axios from 'axios'

const autoTestRequest = axios.create({
  baseURL: '',
  timeout: 30000
})

// 添加请求拦截器，自动带上 token（支持前台用户 token 和后台 admin token）
autoTestRequest.interceptors.request.use(
  config => {
    const token = localStorage.getItem('admin_token') || localStorage.getItem('token')
    if (token && token !== 'undefined' && token !== 'null' && token !== '[object Object]') {
      config.headers['Authorization'] = `Bearer ${token}`
    }
    return config
  },
  error => Promise.reject(error)
)

// 添加响应拦截器，统一返回 response.data
autoTestRequest.interceptors.response.use(
  response => response.data,
  error => Promise.reject(error)
)

const route = useRoute()
const activeTab = ref(route.query.tab || 'debug')
const currentScenarioId = ref(null)

// 分组相关
const folderTreeRef = ref(null)
const groupTreeData = ref([])
const currentGroup = ref(null)
const currentGroupId = ref(null)
const loadingGroups = ref(false)
const folderDialogVisible = ref(false)
const folderDialogType = ref('create')
const folderForm = ref({ name: '', description: '', parentId: null })

// 环境相关
const environmentList = ref([])

// 执行结果
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

// 场景列表引用
const scenarioListRef = ref(null)
// 用例列表引用
const caseListRef = ref(null)

// ========== 接口调试相关 ==========
const debugEnvId = ref(null)
const debugForm = ref({
  method: 'GET',
  url: '',
  headers: [],
  body: '',
  bodyType: 'json',
  timeout: 5,
  params: []
})
const debugLoading = ref(false)
const debugResponse = ref(null)
const debugReqTab = ref('body')
const debugResTab = ref('body')
const debugRequestDetails = ref({})
const showVariableDialog = ref(false)
const variableTarget = ref('')
const variables = ref([])
const filteredVariables = ref([])
const variableSearch = ref('')
const debugHistory = ref([])
const showHistory = ref(false)

// 保存到接口库
const saveToApiLibraryDialog = ref(false)
const apiLibraryForm = ref({
  name: '',
  group_id: '',
  description: ''
})
const apiGroups = ref([])

// 格式化响应体
const formattedResponse = computed(() => {
  if (!debugResponse.value) return ''
  try {
    if (typeof debugResponse.value.data === 'object') {
      return JSON.stringify(debugResponse.value.data, null, 2)
    } else if (debugResponse.value.data) {
      return debugResponse.value.data
    } else if (debugResponse.value.body) {
      return typeof debugResponse.value.body === 'object' 
        ? JSON.stringify(debugResponse.value.body, null, 2) 
        : debugResponse.value.body
    }
    return JSON.stringify(debugResponse.value, null, 2)
  } catch (error) {
    return String(debugResponse.value)
  }
})

// 请求详情
// const debugRequestDetails = computed(() => {
//   let headers = {}
//   try {
//     headers = JSON.parse(debugForm.value.headers || '{}')
//   } catch (e) {
//     console.error('解析headers失败:', e)
//     headers = {}
//   }
//   return {
//     method: debugForm.value.method,
//     url: debugForm.value.url,
//     headers: headers,
//     body: debugForm.value.body,
//     bodyType: debugForm.value.bodyType,
//     timeout: debugForm.value.timeout
//   }
// })

const sendDebugRequest = async () => {
  if (!debugForm.value.url.trim()) {
    ElMessage.warning('请输入请求URL')
    return
  }
  debugLoading.value = true
  debugResponse.value = null
  try {
    // 🔥 变量解析：URL / Headers / Params / Body 中的 {{key}} 占位符全部替换为真实值
    const varsArray = variables.value || []

    // 将 headers 数组转换为对象，并解析变量
    const headersObj = {}
    debugForm.value.headers.forEach(item => {
      if (item.key) {
        headersObj[replaceVariables(item.key, varsArray)] = replaceVariables(item.value, varsArray)
      }
    })

    // 将 params 数组转换为对象，并解析变量
    const paramsObj = {}
    debugForm.value.params.forEach(item => {
      if (item.key) {
        paramsObj[replaceVariables(item.key, varsArray)] = replaceVariables(item.value, varsArray)
      }
    })

    const payload = {
      method: debugForm.value.method,
      url: replaceVariables(debugForm.value.url, varsArray),
      headers: headersObj,
      params: paramsObj,
      body: replaceVariables(debugForm.value.body || '', varsArray),
      body_type: debugForm.value.bodyType
    }
    if (debugEnvId.value) {
      payload.env_id = debugEnvId.value
    }
    
    // 更新请求详情（展示已解析的真实数据）
    debugRequestDetails.value = {
      method: debugForm.value.method,
      url: replaceVariables(debugForm.value.url, varsArray),
      headers: headersObj,
      params: paramsObj,
      body: replaceVariables(debugForm.value.body || '', varsArray),
      bodyType: debugForm.value.bodyType,
      timeout: debugForm.value.timeout
    }
    
    const res = await autoTestRequest.post('/api/auto-test/send', payload)
    debugResponse.value = res.data || res
    if (debugResponse.value.error && !debugResponse.value.status_code) {
      ElMessage.error(debugResponse.value.error)
    }
  } catch (err) {
    debugResponse.value = { error: err.response?.data?.error || err.message || '请求发送失败' }
    ElMessage.error('请求发送失败')
  } finally {
    debugLoading.value = false
    // 添加到历史记录
    addToHistory()
  }
}

// 添加到历史记录
const addToHistory = () => {
  const varsArray = variables.value || []
  // 将 headers 数组转换为对象（并解析变量）
  const headersObj = {}
  debugForm.value.headers.forEach(item => {
    if (item.key) {
      headersObj[replaceVariables(item.key, varsArray)] = replaceVariables(item.value, varsArray)
    }
  })

  // 将 params 数组转换为对象（并解析变量）
  const paramsObj = {}
  debugForm.value.params.forEach(item => {
    if (item.key) {
      paramsObj[replaceVariables(item.key, varsArray)] = replaceVariables(item.value, varsArray)
    }
  })

  const historyItem = {
    method: debugForm.value.method,
    url: replaceVariables(debugForm.value.url, varsArray),
    headers: headersObj,
    params: paramsObj,
    body: replaceVariables(debugForm.value.body || '', varsArray),
    body_type: debugForm.value.bodyType,
    status_code: debugResponse.value?.status_code || 0,
    error: debugResponse.value?.error || '',
    timestamp: new Date().toLocaleString('zh-CN'),
    env_id: debugEnvId.value
  }
  // 添加到历史记录的开头
  debugHistory.value.unshift(historyItem)
  // 限制历史记录数量
  if (debugHistory.value.length > 50) {
    debugHistory.value = debugHistory.value.slice(0, 50)
  }
}

// 再次发送历史请求
const resendHistoryRequest = async (item) => {
  // 加载历史请求的参数
  debugForm.value.method = item.method
  debugForm.value.url = item.url
  // 将 headers 对象转换为数组
  const headersArray = []
  if (item.headers && typeof item.headers === 'object') {
    for (const [key, value] of Object.entries(item.headers)) {
      headersArray.push({ key, value })
    }
  }
  debugForm.value.headers = headersArray
  // 将 params 对象转换为数组
  const paramsArray = []
  if (item.params && typeof item.params === 'object') {
    for (const [key, value] of Object.entries(item.params)) {
      paramsArray.push({ key, value })
    }
  }
  debugForm.value.params = paramsArray
  debugForm.value.body = item.body
  debugForm.value.bodyType = item.body_type
  debugEnvId.value = item.env_id
  // 关闭历史记录抽屉
  showHistory.value = false
  // 发送请求
  await sendDebugRequest()
}

// 加载历史记录到表单
const loadHistoryItem = (item) => {
  // 加载历史请求的参数到表单
  debugForm.value.method = item.method
  debugForm.value.url = item.url
  // 将 headers 对象转换为数组
  const headersArray = []
  if (item.headers && typeof item.headers === 'object') {
    for (const [key, value] of Object.entries(item.headers)) {
      headersArray.push({ key, value })
    }
  }
  debugForm.value.headers = headersArray
  // 将 params 对象转换为数组
  const paramsArray = []
  if (item.params && typeof item.params === 'object') {
    for (const [key, value] of Object.entries(item.params)) {
      paramsArray.push({ key, value })
    }
  }
  debugForm.value.params = paramsArray
  debugForm.value.body = item.body
  debugForm.value.bodyType = item.body_type
  debugEnvId.value = item.env_id
  // 关闭历史记录抽屉
  showHistory.value = false
  // 提示用户
  ElMessage.success('已加载历史请求参数')
}

// 加载分组树
const loadGroups = async () => {
  loadingGroups.value = true
  try {
    const res = await autoTestRequest.get('/api/auto-test/groups/tree')
    groupTreeData.value = res || []
  } catch (error) {
    console.error('加载分组失败:', error)
    ElMessage.error('加载分组失败')
  } finally {
    loadingGroups.value = false
  }
}

// 构建树形结构
const buildTree = (list, parentId = null) => {
  return list
    .filter(item => item.parent_id === parentId)
    .map(item => ({
      ...item,
      children: buildTree(list, item.id),
      caseCount: item.caseCount
    }))
}

// 选择分组
const handleGroupSelect = (data) => {
  currentGroup.value = data
  currentGroupId.value = data.id
}

// Tab 切换
const router = useRouter()
const handleTabChange = (val) => {
  // 更新URL查询参数
  router.replace({ query: { tab: val } })

  if (val === 'scenarios' && scenarioListRef.value) {
    scenarioListRef.value.loadScenarios()
  }
}

// 分组操作
const handleFolderCommand = (command) => {
  switch (command) {
    case 'createRoot':
      folderDialogType.value = 'create'
      folderForm.value = { name: '', description: '', parentId: null }
      folderDialogVisible.value = true
      break
    case 'createChild':
      folderDialogType.value = 'create'
      folderForm.value = { name: '', description: '', parentId: currentGroup.value?.id }
      folderDialogVisible.value = true
      break
    case 'editGroup':
      folderDialogType.value = 'edit'
      folderForm.value = {
        id: currentGroup.value?.id,
        name: currentGroup.value?.name,
        description: currentGroup.value?.description
      }
      folderDialogVisible.value = true
      break
    case 'deleteGroup':
      handleDeleteFolder()
      break
  }
}

// 保存分组
const handleFolderSave = async () => {
  console.log('--- [AutoTest] 触发 handleFolderSave 保存分组 ---')
  console.log('--- folderForm 数据:', folderForm.value)
  if (!folderForm.value.name) {
    ElMessage.warning('请输入分组名称')
    return
  }
  try {
    if (folderDialogType.value === 'edit') {
      await autoTestRequest.put(`/api/auto-test/groups/${folderForm.value.id}`, {
        name: folderForm.value.name,
        description: folderForm.value.description
      })
      ElMessage.success('更新成功')
    } else {
      await autoTestRequest.post('/api/auto-test/groups', {
        name: folderForm.value.name,
        description: folderForm.value.description,
        parent_id: folderForm.value.parentId
      })
      ElMessage.success('创建成功')
    }
    folderDialogVisible.value = false
    loadGroups()
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

// 删除分组
const handleDeleteFolder = async () => {
  if (!currentGroup.value) return
  try {
    await ElMessageBox.confirm(
      `确定要删除分组 "${currentGroup.value.name}" 吗？分组下的用例将被删除。`,
      '删除确认',
      { type: 'warning' }
    )
    await autoTestRequest.delete(`/api/auto-test/groups/${currentGroup.value.id}`)
    ElMessage.success('删除成功')
    currentGroup.value = null
    currentGroupId.value = null
    loadGroups()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

// 加载环境列表
const loadEnvironments = async () => {
  try {
    const res = await autoTestRequest.get('/api/auto-test/environments')
    environmentList.value = res || []
  } catch (error) {
    console.error('加载环境失败:', error)
  }
}

// 变量替换函数：替换 {{varname}} 格式的占位符，同时支持数组和对象两种变量格式
const replaceVariables = (template, vars) => {
  if (!template || typeof template !== 'string') {
    return template
  }
  return template.replace(/\{\{(.*?)\}\}/g, (match, varName) => {
    varName = varName.trim()
    // 兼容 varsArray（数组，每个元素有 name/value）or varObj（键值对对象）
    if (Array.isArray(vars)) {
      const found = vars.find(v => v && v.name === varName)
      return found && found.value !== undefined ? found.value : match
    } else if (vars && typeof vars === 'object') {
      return vars[varName] !== undefined ? vars[varName] : match
    }
    return match
  })
}

// 运行用例
const handleRunCases = async (caseData, envId) => {
  try {
    const runRes = await autoTestRequest.post(`/api/auto-test/cases/${caseData.id}/run`, {
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

    if (caseListRef.value) {
      caseListRef.value.loadCases()
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

// 编辑场景
const handleEditScenario = (scenario) => {
  currentScenarioId.value = scenario.id
}

// 处理URL输入
const handleUrlInput = (value) => {
  // 可以在这里添加URL输入的处理逻辑
  console.log('URL输入:', value)
}

// 打开变量选择对话框
const insertVariable = (target) => {
  variableTarget.value = target
  showVariableDialog.value = true
  // 加载变量列表
  loadVariables()
}

// 插入变量值
const insertVariableValue = (variableValue) => {
  console.log('插入变量:', variableValue)
  console.log('目标字段:', variableTarget.value)
  console.log('表单字段:', debugForm.value[variableTarget.value])
  if (variableTarget.value && debugForm.value[variableTarget.value] !== undefined) {
    console.log('准备插入变量到字段:', variableTarget.value)
    // 使用Vue的响应式更新方式
    const currentValue = debugForm.value[variableTarget.value] || ''
    const newValue = currentValue + `{{${variableValue}}}`
    console.log('新值:', newValue)
    // 重新赋值以触发响应式更新
    debugForm.value = {
      ...debugForm.value,
      [variableTarget.value]: newValue
    }
    console.log('插入后的值:', debugForm.value[variableTarget.value])
  } else {
    console.error('目标字段不存在或未定义:', variableTarget.value)
  }
  showVariableDialog.value = false
}

// 保存到接口库
const saveToApiLibrary = async () => {
  try {
    // 检查接口调试状态
    const isDebugSuccessful = debugResponse.value && 
                              (debugResponse.value.status_code >= 200 && debugResponse.value.status_code < 300) && 
                              debugResponse.value.success !== false
    
    // 如果调试未通过或尚未调试，显示确认框
    if (!isDebugSuccessful) {
      try {
        await ElMessageBox.confirm(
          '该接口当前未调试通过，直接保存可能导致用例执行失败。是否确认强制保存？',
          '确认保存',
          {
            confirmButtonText: '强制保存',
            cancelButtonText: '重新调试',
            type: 'warning'
          }
        )
        // 用户点击了"强制保存"，继续执行保存流程
      } catch {
        // 用户点击了"重新调试"或关闭了弹窗，停留在当前页面
        return
      }
    }
    
    // 加载接口分组
    await loadApiGroups()
    // 自动填充接口名称（从URL中提取）
    const url = debugForm.value.url
    const urlParts = url.split('/')
    const lastPart = urlParts[urlParts.length - 1]
    const apiName = lastPart || url
    apiLibraryForm.value.name = `${debugForm.value.method} ${apiName}`
    // 打开对话框
    saveToApiLibraryDialog.value = true
  } catch (error) {
    if (error !== 'cancel') {
      console.error('加载接口分组失败:', error)
      ElMessage.error('加载接口分组失败')
    }
  }
}

// 加载接口分组
const loadApiGroups = async () => {
  try {
    const res = await autoTestRequest.get('/api/auto-test/groups')
    apiGroups.value = res || []
  } catch (error) {
    console.error('加载接口分组失败:', error)
    throw error
  }
}

// 确认保存到接口库
const confirmSaveToApiLibrary = async () => {
  if (!apiLibraryForm.value.name) {
    ElMessage.warning('请输入接口名称')
    return
  }
  if (!apiLibraryForm.value.group_id) {
    ElMessage.warning('请选择所属分组')
    return
  }

  try {
    // 处理headers，将数组转换为对象
    let headers = {}
    if (Array.isArray(debugForm.value.headers)) {
      debugForm.value.headers.forEach(item => {
        if (item.key) {
          headers[item.key] = item.value
        }
      })
    } else if (debugForm.value.headers && typeof debugForm.value.headers === 'object') {
      headers = debugForm.value.headers
    }
    
    // 处理params，将数组转换为对象
    let params = {}
    if (Array.isArray(debugForm.value.params)) {
      debugForm.value.params.forEach(item => {
        if (item.key) {
          params[item.key] = item.value
        }
      })
    } else if (debugForm.value.params && typeof debugForm.value.params === 'object') {
      params = debugForm.value.params
    }

    // 处理body/payload：如果是JSON类型，需要解析为对象
    let requestPayload = null
    const rawBodyType = debugForm.value.bodyType || 'none'
    // 🔥 映射：调试面板的 'json' 对应接口库/Drawer 的 'raw'
    const bodyTypeMapping = { 'json': 'raw', 'raw': 'raw', 'form-data': 'form-data', 'none': 'none' }
    const bodyType = bodyTypeMapping[rawBodyType] || rawBodyType
    const bodyContent = debugForm.value.body || ''

    if (bodyType === 'raw' || rawBodyType === 'json') {
      // JSON类型需要解析为对象
      if (bodyContent && bodyContent.trim()) {
        try {
          requestPayload = JSON.parse(bodyContent)
        } catch (e) {
          ElMessage.error('请求体 JSON 格式错误，请检查！')
          return
        }
      } else {
        // 空内容默认为空对象
        requestPayload = {}
      }
    } else if (bodyType === 'form-data') {
      // form-data类型保持对象格式
      requestPayload = {}
      if (Array.isArray(debugForm.value.formData)) {
        debugForm.value.formData.forEach(item => {
          if (item.key) {
            requestPayload[item.key] = item.value
          }
        })
      }
    }
    // none类型requestPayload保持null

    // 🔥 根据 bodyType 映射 content_type
    let contentType = debugForm.value.contentType || 'application/json'
    if (rawBodyType === 'json') contentType = 'application/json'

    const payload = {
      name: apiLibraryForm.value.name,
      group_id: apiLibraryForm.value.group_id,
      method: debugForm.value.method,
      url: debugForm.value.url,
      headers: headers,
      params: params,
      body_type: bodyType,       // 🔥 已映射：'json' → 'raw'
      content_type: contentType,
      payload: requestPayload,
      description: apiLibraryForm.value.description
    }
    
    const res = await autoTestRequest.post('/api/auto-test/cases', payload)
    ElMessage.success('保存到接口库成功')
    saveToApiLibraryDialog.value = false
    
    // 保存成功后，刷新接口库列表，确保新保存的接口能够显示出来
    if (caseListRef.value) {
      caseListRef.value.loadCases()
    }
  } catch (error) {
    console.error('保存到接口库失败:', error)
    ElMessage.error(error.response?.data?.detail || '保存到接口库失败')
  }
}

// 加载变量列表
const loadVariables = async () => {
  try {
    console.log('开始加载变量...')
    const res = await autoTestRequest.get('/api/auto-test/global-variables')
    console.log('API响应:', res)
    const globalVariables = Array.isArray(res) ? res : []
    console.log('全局变量:', globalVariables)
    
    // 添加动态变量
    const dynamicVariables = [
      { id: 'dynamic-1', name: '$timestamp', value: '', description: '当前时间戳', is_encrypted: false },
      { id: 'dynamic-2', name: '$random_int', value: '', description: '随机整数', is_encrypted: false },
      { id: 'dynamic-3', name: '$random_string', value: '', description: '随机字符串', is_encrypted: false },
      { id: 'dynamic-4', name: '$uuid', value: '', description: 'UUID', is_encrypted: false },
      { id: 'dynamic-5', name: '$datetime', value: '', description: '当前日期时间', is_encrypted: false }
    ]
    console.log('动态变量:', dynamicVariables)
    
    variables.value = [...globalVariables, ...dynamicVariables]
    console.log('合并后的变量:', variables.value)
    filteredVariables.value = variables.value
    console.log('过滤后的变量:', filteredVariables.value)
  } catch (error) {
    console.error('加载变量失败:', error)
    // 即使API失败，也显示动态变量
    variables.value = [
      { id: 'dynamic-1', name: '$timestamp', value: '', description: '当前时间戳', is_encrypted: false },
      { id: 'dynamic-2', name: '$random_int', value: '', description: '随机整数', is_encrypted: false },
      { id: 'dynamic-3', name: '$random_string', value: '', description: '随机字符串', is_encrypted: false },
      { id: 'dynamic-4', name: '$uuid', value: '', description: 'UUID', is_encrypted: false },
      { id: 'dynamic-5', name: '$datetime', value: '', description: '当前日期时间', is_encrypted: false }
    ]
    filteredVariables.value = variables.value
  }
}

// 清空调试表单
const clearDebugForm = () => {
  debugForm.value = {
    method: 'GET',
    url: '',
    headers: [],
    body: '',
    bodyType: 'json',
    timeout: 5,
    params: []
  }
  debugResponse.value = null
}

// 清空历史记录
const clearHistory = () => {
  debugHistory.value = []
}

// 复制响应
const copyResponse = () => {
  if (debugResponse.value) {
    const responseText = JSON.stringify(debugResponse.value, null, 2)
    navigator.clipboard.writeText(responseText)
      .then(() => {
        ElMessage.success('响应已复制到剪贴板')
      })
      .catch(err => {
        console.error('复制失败:', err)
        ElMessage.error('复制失败')
      })
  }
}

// 格式化 JSON
const formatJson = (field) => {
  try {
    const value = debugForm.value[field]
    if (value) {
      const parsed = JSON.parse(value)
      const formatted = JSON.stringify(parsed, null, 2)
      debugForm.value[field] = formatted
      ElMessage.success('JSON 格式化成功')
    }
  } catch (error) {
    ElMessage.error('JSON 格式错误')
  }
}

onMounted(() => {
  loadGroups()
  loadEnvironments()
  initGuide()
})

const showGuide = ref(false)
const guideStep = ref(1)

const guideTips = {
  1: {
    title: '第一步：接口调试',
    desc: '在「接口调试」标签页中，输入一个 API 地址（如 https://httpbin.org/get），选择请求方式，点击「发送请求」查看返回结果。这是接口测试最基本的操作。',
    actionLabel: '去调试',
    action: () => { activeTab.value = 'debug' },
  },
  2: {
    title: '第二步：创建用例',
    desc: '调试成功的接口可以保存为用例。切换到「接口库」标签页，在左侧创建分组，然后添加接口用例，设置断言规则来验证返回数据。',
    actionLabel: '去接口库',
    action: () => { activeTab.value = 'interfaces' },
  },
  3: {
    title: '第三步：场景编排',
    desc: '多个接口用例可以编排成测试场景，模拟用户完整操作流程（如：登录→查询→下单→支付）。场景支持步骤间数据传递和条件执行。',
    actionLabel: '去场景管理',
    action: () => { activeTab.value = 'scenarios' },
  },
  4: {
    title: '第四步：批量执行',
    desc: '创建好场景后，可以一键批量执行所有测试用例，生成测试报告。还可以设置定时任务，让测试自动运行。',
    actionLabel: '完成引导',
    action: () => { dismissGuide() },
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
  if (guideStep.value < 4) {
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

// 监视debugForm的变化
watch(() => debugForm.value.method, (newMethod, oldMethod) => {
  console.log('请求方式变化:', oldMethod, '→', newMethod)
  try {
    // 这里可以添加任何需要在请求方式变化时执行的逻辑
  } catch (error) {
    console.error('请求方式变化时出错:', error)
  }
})
</script>

<style scoped>
.beginner-guide-banner {
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.15), rgba(217, 70, 239, 0.1));
  border-bottom: 1px solid rgba(139, 92, 246, 0.2);
  padding: 16px 24px;
}

.guide-content {
  display: flex;
  align-items: center;
  gap: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.guide-icon {
  font-size: 36px;
  flex-shrink: 0;
}

.guide-text h3 {
  font-size: 16px;
  font-weight: 700;
  color: #e2e8f0;
  margin: 0 0 2px 0;
}

.guide-text p {
  font-size: 13px;
  color: #94a3b8;
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
  transition: all 0.25s ease;
  background: rgba(139, 92, 246, 0.06);
  border: 1px solid rgba(139, 92, 246, 0.1);
}

.guide-step.active {
  background: rgba(139, 92, 246, 0.15);
  border-color: rgba(139, 92, 246, 0.3);
}

.guide-step.done {
  background: rgba(139, 92, 246, 0.1);
  border-color: rgba(139, 92, 246, 0.2);
}

.step-num {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: rgba(139, 92, 246, 0.2);
  color: #c084fc;
  font-size: 12px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
}

.guide-step.active .step-num {
  background: linear-gradient(135deg, #8b5cf6, #d946ef);
  color: white;
}

.guide-step.done .step-num {
  background: #8b5cf6;
  color: white;
}

.step-label {
  font-size: 13px;
  color: #94a3b8;
  font-weight: 500;
}

.guide-step.active .step-label {
  color: #e2e8f0;
}

.guide-arrow {
  color: rgba(139, 92, 246, 0.3);
  font-size: 14px;
}

.guide-close {
  color: #94a3b8 !important;
  font-size: 16px;
  flex-shrink: 0;
}

.guide-tip-card {
  max-width: 1200px;
  margin: 16px auto;
  padding: 16px 20px;
  background: rgba(139, 92, 246, 0.08);
  border: 1px solid rgba(139, 92, 246, 0.15);
  border-radius: 12px;
}

.tip-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  color: #e2e8f0;
  font-size: 15px;
}

.tip-icon {
  font-size: 20px;
}

.tip-desc {
  font-size: 14px;
  color: #94a3b8;
  line-height: 1.6;
  margin: 0 0 12px 0;
}

.tip-actions {
  display: flex;
  gap: 8px;
}

/* 接口调试面板样式 */
.debug-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px;
}
.debug-card {
  border-radius: 12px !important;
  border: 1px solid var(--tm-border-light) !important;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15) !important;
  backdrop-filter: blur(10px) !important;
  -webkit-backdrop-filter: blur(10px) !important;
}
.debug-card :deep(.el-card__header) {
  padding: 16px 24px;
  border-bottom: 1px solid var(--tm-border-light) !important;
  background: var(--tm-bg-card) !important;
}
.debug-response-body {
  background: var(--tm-bg-card);
  color: var(--tm-text-primary);
  padding: 20px;
  border-radius: 10px;
  font-size: 14px;
  line-height: 1.6;
  max-height: 500px;
  overflow: auto;
  white-space: pre-wrap;
  word-break: break-all;
  margin: 0;
  border: 1px solid rgba(189, 0, 255, 0.3);
  box-shadow: inset 0 2px 8px rgba(0, 0, 0, 0.5);
}
.auto-test-page {
  padding: 30px 0;
  min-height: calc(100vh - 60px);
  background-color: #09090B;
  font-family: 'Inter', 'Roboto', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  position: relative;
}

.auto-test-page::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, rgba(10, 10, 20, 0.8) 0%, rgba(20, 10, 30, 0.9) 100%);
  z-index: 1;
  pointer-events: none;
}

.auto-test-page > * {
  position: relative;
  z-index: 2;
}

/* 页面标签页 */
.page-tabs {
  width: 100%;
  max-width: 100%;
  padding: 0 32px;
  margin: 0 auto 20px;
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
  background: rgba(0, 0, 0, 0.1);
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
  box-shadow: 0 0 10px rgba(189, 0, 255, 0.3);
}

.tab-group :deep(.el-radio-button.is-active .el-radio-button__inner) {
  background: linear-gradient(135deg, var(--tm-color-primary), var(--tm-color-primary-dark));
  border-color: var(--tm-color-primary);
  color: white;
  box-shadow: 0 0 15px rgba(189, 0, 255, 0.5);
  transform: translateY(-1px);
}

.tab-content {
  width: 100%;
  max-width: 100%;
  padding: 0 32px;
  margin: 0 auto;
  box-sizing: border-box;
  flex: 1;
  overflow: hidden;
}

.scenario-container {
  background: var(--tm-bg-card);
  border-radius: 12px;
  padding: 24px;
  min-height: calc(100vh - 200px);
  border: 1px solid var(--tm-border-light);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
}

/* 双栏布局 */
.page-layout {
  display: flex;
  height: calc(100vh - 220px);
  gap: 20px;
}

.left-panel {
  width: 300px;
  background: var(--tm-bg-card);
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border: 1px solid var(--tm-border-light);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 18px 20px;
  border-bottom: 1px solid var(--border-subtle);
  flex-shrink: 0;
  background: var(--tm-bg-card);
}

.panel-title {
  font-weight: 600;
  font-size: 16px;
  color: var(--tm-text-primary);
  text-shadow: 0 0 10px rgba(189, 0, 255, 0.3);
}

.btn-more {
  background: transparent;
  border: 1px solid var(--tm-color-primary);
  color: var(--tm-color-primary);
  border-radius: 8px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.btn-more:hover {
  background: rgba(var(--tm-color-primary-rgb), 0.2);
  box-shadow: 0 0 15px rgba(189, 0, 255, 0.4);
  transform: translateY(-1px);
}

.folder-tree {
  flex: 1;
  overflow: auto;
  padding: 16px;
}

.tree-node {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  color: var(--text-secondary);
  border-radius: 8px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  margin-bottom: 4px;
}

:deep(.el-tree .el-tree-node.is-current > .el-tree-node__content) {
  background-color: rgba(189, 0, 255, 0.15) !important;
  border-radius: 8px;
}

:deep(.el-tree .el-tree-node__content:hover) {
  background-color: rgba(189, 0, 255, 0.1) !important;
  border-radius: 8px;
}

:deep(.el-tree .el-tree-node.is-current > .el-tree-node__content .tree-node) {
  color: var(--text-primary);
}

.node-icon {
  font-size: 16px;
  text-shadow: 0 0 5px rgba(189, 0, 255, 0.5);
}

.node-label {
  flex: 1;
  font-size: 14px;
  color: var(--tm-text-primary);
  transition: color 0.3s ease;
}

.tree-node:hover .node-label {
  color: var(--tm-color-primary);
  text-shadow: 0 0 5px rgba(189, 0, 255, 0.5);
}

.node-count {
  color: var(--tm-color-primary);
  font-size: 12px;
  background: rgba(var(--tm-color-primary-rgb), 0.2);
  padding: 4px 10px;
  border-radius: 12px;
  border: 1px solid rgba(189, 0, 255, 0.4);
  box-shadow: 0 0 8px rgba(189, 0, 255, 0.3);
}

.right-panel {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  background: var(--tm-bg-card);
  border-radius: 12px;
  border: 1px solid var(--tm-border-light);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
}

.dark-empty {
  color: var(--tm-text-secondary);
}

.dark-empty :deep(.el-empty__description) {
  color: var(--tm-text-secondary);
}

/* 结果对话框 */
.result-content {
  max-height: 70vh;
  overflow: auto;
}

.result-summary {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 20px;
  padding: 16px;
  background: var(--tm-bg-card);
  border-radius: 10px;
  border: 1px solid var(--tm-border-light);
}

.summary-info {
  color: var(--tm-text-secondary);
  font-size: 15px;
}

.result-detail h4 {
  margin: 24px 0 16px;
  color: var(--tm-text-primary);
  font-size: 16px;
  font-weight: 600;
  text-shadow: 0 0 5px rgba(189, 0, 255, 0.3);
}

.response-info {
  display: flex;
  gap: 24px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 16px;
  background: var(--tm-bg-card);
  border-radius: 8px;
  border: 1px solid var(--tm-border-light);
}

.info-label {
  color: var(--tm-text-secondary);
  font-size: 14px;
  font-weight: 500;
}

.error-message {
  margin-bottom: 20px;
}

.response-display {
  background: var(--tm-bg-card);
  color: var(--tm-color-primary);
  padding: 20px;
  border-radius: 10px;
  max-height: 320px;
  overflow: auto;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 14px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-all;
  margin: 0;
  box-shadow: inset 0 2px 8px rgba(0, 0, 0, 0.5);
  border: 1px solid rgba(189, 0, 255, 0.3);
  text-shadow: 0 0 5px rgba(189, 0, 255, 0.3);
}

/* 暗黑对话框样式覆盖 */
:deep(.dark-dialog) {
  background: var(--tm-bg-card);
  color: var(--tm-text-primary);
  border-radius: 12px !important;
  border: 1px solid var(--tm-border-light) !important;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4) !important;
  backdrop-filter: blur(15px) !important;
  -webkit-backdrop-filter: blur(15px) !important;
}

.dark-dialog :deep(.el-dialog__header) {
  border-bottom: 1px solid var(--tm-border-light) !important;
  background: var(--tm-bg-card) !important;
}

.dark-dialog :deep(.el-dialog__title) {
  color: var(--tm-text-primary) !important;
  font-weight: 600 !important;
  text-shadow: 0 0 5px rgba(189, 0, 255, 0.3) !important;
}

.dark-dialog :deep(.el-dialog__body) {
  color: var(--tm-text-primary) !important;
}

.dark-input :deep(.el-input__wrapper) {
  background: var(--tm-bg-card) !important;
  box-shadow: 0 0 0 1px var(--tm-border-light) inset !important;
  border-radius: 8px !important;
  backdrop-filter: blur(4px) !important;
  -webkit-backdrop-filter: blur(4px) !important;
}

.dark-input :deep(.el-input__inner) {
  color: var(--tm-text-primary) !important;
}

.dark-input :deep(.el-input__inner::placeholder) {
  color: var(--tm-text-secondary) !important;
}

.dark-input :deep(.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px var(--tm-color-primary) inset, 0 0 15px rgba(189, 0, 255, 0.4) !important;
}

.dark-divider {
  --el-divider-color: var(--tm-border-light);
}

.btn-primary {
  background: linear-gradient(135deg, var(--tm-color-primary), var(--tm-color-primary-dark)) !important;
  border: none !important;
  box-shadow: 0 4px 15px rgba(189, 0, 255, 0.4) !important;
  border-radius: 8px !important;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
}

.btn-primary:hover {
  background: linear-gradient(135deg, var(--tm-color-primary), var(--tm-color-primary-dark)) !important;
  box-shadow: 0 6px 20px rgba(189, 0, 255, 0.6) !important;
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
  box-shadow: 0 0 15px rgba(189, 0, 255, 0.3) !important;
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
  background-color: rgba(189, 0, 255, 0.15) !important;
}

/* 响应式 */
@media (max-width: 768px) {
  .page-layout {
    flex-direction: column;
    height: auto;
    min-height: 80vh;
  }

  .left-panel {
    width: 100%;
    max-height: 300px;
    margin-bottom: 20px;
  }

  .debug-container {
    padding: 16px;
  }

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

  .request-line {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }

  .method-select,
  .url-input,
  .request-actions {
    width: 100%;
    min-width: unset;
  }

  .request-actions {
    justify-content: space-between;
  }

  .send-button {
    flex: 1;
    margin-left: 12px;
  }

  .toolbar-right {
    flex-wrap: wrap;
    gap: 8px;
  }

  .response-meta {
    flex-wrap: wrap;
    gap: 8px;
  }

  .history-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }

  .history-url {
    width: 100%;
  }

  .history-actions {
    width: 100%;
    justify-content: flex-start;
  }
}

/* 平板设备响应式 */
@media (min-width: 769px) and (max-width: 1024px) {
  .debug-container {
    max-width: 900px;
    padding: 20px;
  }

  .left-panel {
    width: 250px;
  }

  .request-line {
    flex-wrap: wrap;
  }

  .url-input {
    flex: 1;
    min-width: 250px;
  }
}

/* 大屏设备优化 */
@media (min-width: 1200px) {
  .debug-container {
    max-width: 1400px;
  }

  .left-panel {
    width: 320px;
  }

  .right-panel {
    flex: 1;
  }
}

/* 调试工具栏样式 */
.debug-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  background: var(--tm-bg-card);
  border-radius: 12px;
  margin-bottom: 20px;
  border: 1px solid var(--tm-border-light);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
}

.debug-title {
  font-size: 20px;
  font-weight: 700;
  color: var(--tm-text-primary);
  margin: 0;
  text-shadow: 0 0 10px rgba(189, 0, 255, 0.5);
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

/* 请求行样式 */
.request-line {
  display: flex;
  gap: 12px;
  align-items: center;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.method-select {
  min-width: 120px;
  flex-shrink: 0;
}

.url-input {
  flex: 1;
  min-width: 300px;
}

.request-actions {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-shrink: 0;
  padding: 0 4px;
}

.send-button {
  min-width: 140px;
  font-weight: 600;
  letter-spacing: 1px;
  padding: 12px 20px;
}

/* 优化URL输入框和按钮的布局 */
.url-input {
  flex: 1;
  min-width: 300px;
  position: relative;
}

.url-input :deep(.el-input__wrapper) {
  border-radius: 8px !important;
  overflow: hidden;
}

.url-input :deep(.el-input__append) {
  padding: 0 12px;
  background: rgba(var(--tm-color-primary-rgb), 0.1);
  border-left: 1px solid var(--tm-border-light);
}

.url-input :deep(.el-input__append .el-button) {
  margin: 0;
  border: none;
  background: transparent;
  color: var(--tm-color-primary);
  transition: all 0.3s ease;
}

.url-input :deep(.el-input__append .el-button:hover) {
  color: var(--tm-color-primary);
  transform: scale(1.05);
}

/* 超时输入框样式 */
.request-actions .el-input-number {
  width: 120px !important;
  border-radius: 8px;
  overflow: hidden;
}

.request-actions .el-input-number :deep(.el-input__wrapper) {
  border-radius: 8px;
}

.request-actions .el-input-number :deep(.el-input-number__decrease),
.request-actions .el-input-number :deep(.el-input-number__increase) {
  background: rgba(var(--tm-color-primary-rgb), 0.1);
  border-left: 1px solid var(--tm-border-light);
  color: var(--tm-color-primary);
  transition: all 0.3s ease;
}

.request-actions .el-input-number :deep(.el-input-number__decrease:hover),
.request-actions .el-input-number :deep(.el-input-number__increase:hover) {
  background: rgba(var(--tm-color-primary-rgb), 0.2);
  color: var(--tm-color-primary);
}

/* 响应式优化 */
@media (max-width: 768px) {
  .request-actions {
    width: 100%;
    justify-content: space-between;
  }
  
  .send-button {
    flex: 1;
    margin-left: 16px;
  }
  
  .request-actions .el-input-number {
    flex: 0 0 120px;
  }
}

/* 响应结果样式 */
.response-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.response-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--tm-text-primary);
  margin: 0;
  text-shadow: 0 0 5px rgba(189, 0, 255, 0.3);
}

.response-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.status-code {
  font-weight: 600;
  padding: 4px 12px;
  border-radius: 12px;
}

.response-time,
.content-length {
  font-size: 12px;
  padding: 4px 10px;
  border-radius: 8px;
  background: var(--tm-bg-card);
  border: 1px solid var(--tm-border-light);
}

/* 历史记录样式 */
.history-container {
  padding: 20px;
  max-height: 70vh;
  overflow: auto;
  background: var(--tm-bg-page);
}

.history-item {
  background: var(--tm-bg-card);
  border: 1px solid var(--tm-border-light);
  border-radius: 10px;
  padding: 16px;
  margin-bottom: 12px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.history-item:hover {
  border-color: var(--tm-color-primary);
  box-shadow: var(--tm-shadow-base);
  transform: translateY(-1px);
}

.history-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}

.history-method {
  font-weight: 600;
  font-size: 12px;
  padding: 4px 8px;
  border-radius: 6px;
  background: rgba(var(--tm-color-primary-rgb), 0.2);
  color: var(--tm-color-primary);
  border: 1px solid rgba(189, 0, 255, 0.4);
}

.history-url {
  flex: 1;
  font-size: 14px;
  color: var(--tm-text-primary);
  word-break: break-all;
}

.history-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

/* 变量选择对话框样式 */
.variable-dialog {
  padding: 20px;
}

.variable-list {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 20px;
  max-height: 400px;
  overflow-y: auto;
}

.variable-tag {
  padding: 8px 16px;
  border-radius: 20px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border: 1px solid var(--tm-border-light);
  background: var(--tm-bg-card);
}

.variable-tag:hover {
  border-color: var(--tm-color-primary);
  box-shadow: 0 0 15px rgba(189, 0, 255, 0.3);
  transform: translateY(-1px);
}

.var-value {
  font-size: 12px;
  opacity: 0.7;
  margin-left: 8px;
}

/* 滚动条美化 */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

::-webkit-scrollbar-track {
  background: var(--tm-bg-card);
  border-radius: 3px;
}

::-webkit-scrollbar-thumb {
  background: rgba(var(--tm-color-primary-rgb), 0.3)0.5);
  border-radius: 3px;
  transition: background 0.3s ease;
}

::-webkit-scrollbar-thumb:hover {
  background: rgba(var(--tm-color-primary-rgb), 0.3)0.8);
  box-shadow: 0 0 10px rgba(189, 0, 255, 0.5);
}

/* 输入框和选择器样式 */
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
  box-shadow: 0 0 0 1px var(--tm-color-primary) inset, 0 0 15px rgba(189, 0, 255, 0.3) !important;
}

:deep(.el-select-dropdown) {
  background: var(--tm-bg-card) !important;
  border: 1px solid var(--tm-border-light) !important;
  border-radius: 10px !important;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4) !important;
  backdrop-filter: blur(15px) !important;
  -webkit-backdrop-filter: blur(15px) !important;
}

:deep(.el-select-dropdown__item) {
  color: var(--tm-text-primary) !important;
  transition: all 0.3s ease !important;
}

:deep(.el-select-dropdown__item:hover) {
  background: rgba(var(--tm-color-primary-rgb), 0.3)0.15) !important;
  color: var(--tm-color-primary) !important;
}

:deep(.el-select-dropdown__item.selected) {
  background: rgba(var(--tm-color-primary-rgb), 0.3)0.25) !important;
  color: var(--tm-color-primary) !important;
}
</style>
