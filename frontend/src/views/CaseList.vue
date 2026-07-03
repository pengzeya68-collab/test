<template>
  <div class="case-list-layout">
    <!-- 左侧分组树侧边栏
         宽度由 splitter1 target=left 直接控制（所见即所得：拖动 → sidebar 变宽/窄），
         拖到 min=180 时自动隐藏，拖到 min=180+ 时恢复显示（用户体验：完全可调） -->
    <div class="case-list-sidebar" :style="{ width: sidebarWidth + 'px', flex: 'none' }">
      <CaseTreeSidebar
        ref="sidebarRef"
        :current-group-id="currentGroupId"
        @select-group="handleSelectGroup"
      />
    </div>
    <!-- 拖拽分隔条 1：侧边栏 ↔ 列表
         target=left 表示 size 解读为"左侧面板（侧边栏）"的宽度。
         拖动时所见即所得：向右拖 → sidebar 变宽；向左拖 → sidebar 变窄。
         list/editor 弹性填充剩余空间（保持总和 = 视口 - sidebar）。 -->
    <BaseSplitter
      v-model:size="sidebarWidth"
      target="left"
      direction="horizontal"
      :min-size="SIDEBAR_MIN"
      :max-size="SIDEBAR_MAX"
      storage-key="tm-caselist-sidebar-width"
      container-selector=".case-list-layout"
    />
    <!-- 中间：用例列表表格
         width = listMaxWidth（由 splitter2 直接控制，target=right），
         max-width = listMaxAllowed（视口 - sidebar - editor_min - 2 splitter，防止挤压 editor），
         min-width = LIST_MIN_WIDTH（保证表格可读）。
         拖动 splitter1 (sidebar) 时，listMaxAllowed 自动变化 → list 弹性调整；
         拖动 splitter2 时，listMaxWidth 变化 → list 直接变化 → editor flex:1 反向让位。 -->
    <el-card class="case-list-card" shadow="never" :style="{ width: listMaxWidth + 'px', maxWidth: listMaxLimit + 'px', minWidth: LIST_MIN_WIDTH + 'px', flex: 'none' }">
    <div class="case-list-container">
      <!-- 顶部工具栏 -->
      <div class="list-toolbar">
        <div class="toolbar-left">
          <el-select v-model="selectedEnvId" placeholder="选择环境" size="default" style="width: 180px" @change="handleEnvChange">
            <el-option
              v-for="env in environmentList"
              :key="env.id"
              :label="env.name"
              :value="env.id"
            />
          </el-select>
          <el-tooltip content="环境管理" placement="top" popper-class="action-tooltip">
            <el-button type="primary" plain :icon="Setting" title="环境管理" @click="openEnvManager" />
          </el-tooltip>
          <el-button size="default" @click="showHelp = true">❓ 使用说明</el-button>
          <el-button type="primary" plain :icon="FolderAdd" @click="handleCreateGroup" class="toolbar-btn-icon">
            <span class="toolbar-text-hide">新建分组</span>
          </el-button>
        </div>
        <div class="toolbar-right">
          <el-input
            v-model="searchKeyword"
            placeholder="搜索用例名称或URL"
            size="default"
            style="width: 200px"
            clearable
            @input="handleSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
          <!-- 批量导入下拉菜单 -->
          <el-dropdown trigger="click" @command="handleImportCommand" class="toolbar-btn-icon">
            <el-button type="success" plain>
              <el-icon><Upload /></el-icon>
              <span class="toolbar-text-hide">导入用例</span>
              <el-icon class="el-icon--right"><ArrowDown /></el-icon>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="postman">Postman</el-dropdown-item>
                <el-dropdown-item command="swagger">Swagger/OpenAPI</el-dropdown-item>
                <el-dropdown-item command="jmeter">JMeter (.jmx)</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>

          <el-button v-if="!exportSelectMode" type="warning" plain @click="startExportSelect" :disabled="filteredCases.length === 0" class="toolbar-btn-icon">
            <el-icon><Download /></el-icon>
            <span class="toolbar-text-hide">导出 JMX</span>
          </el-button>
          <template v-else>
            <el-button type="warning" @click="handleExportJmx" :loading="jmeterExporting" :disabled="selectedCaseIds.length === 0" class="toolbar-btn-icon">
              <el-icon><Download /></el-icon>
              <span class="toolbar-text-hide">导出选中</span>
              <span>({{ selectedCaseIds.length }})</span>
            </el-button>
            <el-button plain @click="handleExportAllJmx" :loading="jmeterExporting" class="toolbar-btn-icon">
              <span class="toolbar-text-hide">导出全部</span>
            </el-button>
            <el-button plain @click="cancelExportSelect">
              取消
            </el-button>
          </template>

          <el-button type="primary" @click="handleCreate" class="toolbar-btn-icon">
            <el-icon><Plus /></el-icon>
            <span class="toolbar-text-hide">新建用例</span>
          </el-button>
          <!-- 布局预设下拉（快速调整三栏比例） -->
          <el-dropdown trigger="click" @command="applyLayoutPreset" class="toolbar-btn-icon">
            <el-button plain title="布局预设">
              <el-icon><Operation /></el-icon>
              <span class="toolbar-text-hide">布局</span>
              <el-icon class="el-icon--right"><ArrowDown /></el-icon>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="compact">
                  <el-icon><Files /></el-icon> 紧凑布局（侧边 180 / 列表 400）
                </el-dropdown-item>
                <el-dropdown-item command="default">
                  <el-icon><Grid /></el-icon> 默认布局（侧边 220 / 列表 720）
                </el-dropdown-item>
                <el-dropdown-item command="wide">
                  <el-icon><FullScreen /></el-icon> 宽屏布局（侧边 280 / 列表 1080）
                </el-dropdown-item>
                <el-dropdown-item divided command="editor-focus">
                  <el-icon><EditPen /></el-icon> 编辑器专注（侧边 180 / 列表 320）
                </el-dropdown-item>
                <el-dropdown-item command="reset">
                  <el-icon><RefreshRight /></el-icon> 重置为默认
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>

      <!-- 🔥 体验7：批量操作工具栏（有选中时显示） -->
      <div v-if="selectedCaseRows.length > 0" class="batch-toolbar">
        <span class="batch-info">已选 {{ selectedCaseRows.length }} 项</span>
        <el-button size="small" type="primary" plain :icon="VideoPlay" @click="handleBatchRun" :loading="batchRunning">
          批量运行
        </el-button>
        <el-button size="small" type="warning" plain :icon="Rank" @click="handleBatchMove">
          移动到分组
        </el-button>
        <el-button size="small" type="danger" plain :icon="Delete" @click="handleBatchDelete">
          批量删除
        </el-button>
        <el-button size="small" text @click="clearSelection">取消选择</el-button>
      </div>

      <!-- 用例列表表格 -->
      <div class="case-table">
        <el-table
          ref="caseTableRef"
          :data="filteredCases"
          style="width: 100%"
          stripe
          highlight-current-row
          row-key="id"
          class="modern-table"
          @row-dblclick="handleRowDblClick"
          @selection-change="handleSelectionChange"
        >
          <el-table-column type="selection" width="40" />
          <el-table-column prop="method" label="方法" width="84">
            <template #default="{ row }">
              <span :class="['api-method-tag', (row.method || '').toLowerCase()]">{{ row.method }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="name" label="用例名称" min-width="160" show-overflow-tooltip />
          <el-table-column prop="url" label="URL" min-width="240" show-overflow-tooltip />
          <el-table-column label="最后执行" width="100" align="center">
            <template #default="{ row }">
              <el-tag v-if="row.lastRunStatus" :type="getStatusCodeType(row.lastRunStatus)" size="small">
                {{ formatStatus(row.lastRunStatus) }}
              </el-tag>
              <span v-else class="no-run">未执行</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" :width="actionColWidth" :fixed="actionColFixed">
            <template #default="{ row }">
              <div class="action-cell">
                <el-tooltip content="运行用例" placement="top" popper-class="action-tooltip">
                  <span><el-button type="primary" link :icon="VideoPlay" @click="handleRun(row)" /></span>
                </el-tooltip>

                <el-tooltip content="编辑用例" placement="top" popper-class="action-tooltip">
                  <span><el-button type="primary" link :icon="Edit" @click="handleEdit(row)" /></span>
                </el-tooltip>

                <el-tooltip content="执行历史" placement="top" popper-class="action-tooltip">
                  <span><el-button type="warning" link :icon="Timer" @click="handleShowHistory(row)" /></span>
                </el-tooltip>

                <el-tooltip content="删除用例" placement="top" popper-class="action-tooltip">
                  <span><el-button type="danger" link :icon="Delete" @click="handleDelete(row.id)" /></span>
                </el-tooltip>

                <el-dropdown trigger="click" class="action-more" @command="(cmd) => handleMoreAction(cmd, row)">
                  <span class="action-more-trigger"><el-icon><MoreFilled /></el-icon></span>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item command="copy"><el-icon><DocumentCopy /></el-icon> 复制用例</el-dropdown-item>
                      <el-dropdown-item command="export"><el-icon><Download /></el-icon> 导出 JMX</el-dropdown-item>
                      <el-dropdown-item command="jmeter"><el-icon><Connection /></el-icon> 打开 JMeter IDE</el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
              </div>
            </template>
          </el-table-column>
        </el-table>

        <BaseEmpty
          v-if="!loading && filteredCases.length === 0"
          title="暂无用例"
          description="点击「新建用例」开始你的第一个测试，或从 Postman / Swagger / JMeter 导入"
        />
      </div>

      <!-- 分页 -->
      <div class="pagination-wrapper" v-if="total > 0">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next"
          @size-change="handlePageSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </div>

    <!-- 环境管理抽屉 -->
    <EnvironmentManager v-model="envManagerVisible" @changed="handleEnvListChange" />

    <!-- 导入弹窗 -->
    <el-dialog
      v-model="importDialogVisible"
      :title="importType === 'postman' ? '导入 Postman Collection' : '导入 Swagger/OpenAPI'"
      width="600px"
      :before-close="handleImportClose"
    >
      <div class="import-container" v-loading="importing">
        <el-alert
          :title="importType === 'postman' ? '请选择导出的 Postman Collection v2.1 JSON 文件' : '请选择 Swagger/OpenAPI 的 JSON 文件'"
          type="info"
          show-icon
          style="margin-bottom: 20px"
        />

        <el-form label-width="100px">
          <!-- 统一的文件上传框 -->
          <el-form-item v-show="importType === 'postman' || importType === 'swagger'" label="选择文件">
            <el-upload
              class="upload-demo"
              drag
              action=""
              :auto-upload="false"
              :limit="1"
              :on-change="handleFileChange"
              :on-remove="handleFileRemove"
              accept=".json"
            >
              <el-icon class="el-icon--upload"><upload-filled /></el-icon>
              <div class="el-upload__text">
                将文件拖到此处，或 <em>点击上传</em>
              </div>
              <template #tip>
                <div class="el-upload__tip">只能上传 json 格式文件，且不超过 10MB</div>
              </template>
            </el-upload>
          </el-form-item>

          <el-form-item label="默认分组" v-if="!currentGroupId">
            <el-alert title="如果在根目录导入，将自动创建与文件结构对应的根分组" type="warning" :closable="false"/>
          </el-form-item>

        </el-form>
      </div>

      <!-- 解析结果预览区 (Conflict Detection) -->
      <div v-if="parsedData && parsedData.length > 0" class="import-preview">
        <h4>解析预览 (共解析到 {{ parsedData.length }} 个接口)</h4>
        <el-table :data="parsedData || []" max-height="300" size="small" border row-key="url">
          <el-table-column type="selection" width="55" />
          <el-table-column prop="method" label="Method" width="80">
            <template #default="{ row }">
              <el-tag :type="getMethodTagType(row.method)" size="small">{{ row.method }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="name" label="接口名称" show-overflow-tooltip />
          <el-table-column prop="url" label="URL" show-overflow-tooltip />
          <el-table-column prop="conflict" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="row.conflict ? 'warning' : 'success'" size="small">
                {{ row.conflict ? '覆盖' : '新增' }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="handleImportClose">取消</el-button>
          <el-button v-if="!parsedData" type="primary" @click="handleParseFile">解析文件</el-button>
          <el-button v-else type="success" @click="handleConfirmImport">确认导入</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- JMeter 导入弹窗 -->
    <el-dialog
      v-model="jmeterImportDialogVisible"
      title="导入 JMeter 脚本 (.jmx)"
      width="600px"
      :before-close="handleJMeterImportClose"
    >
      <div class="import-container" v-loading="jmeterImporting">
        <el-alert
          title="请选择 JMeter .jmx 文件，系统将解析并导入接口用例"
          type="info"
          show-icon
          style="margin-bottom: 20px"
        />

        <el-form label-width="100px">
          <el-form-item label="选择文件">
            <el-upload
              class="upload-demo"
              drag
              :auto-upload="false"
              :limit="1"
              :on-change="handleJMeterFileChange"
              :on-remove="handleJMeterFileRemove"
              accept=".jmx"
            >
              <el-icon class="el-icon--upload"><upload-filled /></el-icon>
              <div class="el-upload__text">
                将文件拖到此处，或 <em>点击上传</em>
              </div>
              <template #tip>
                <div class="el-upload__tip">只能上传 .jmx 格式文件，且不超过 10MB</div>
              </template>
            </el-upload>
          </el-form-item>

          <el-form-item label="目标分组" v-if="!props.groupId">
            <el-alert title="将导入到默认分组（可在左侧分组树中创建新分组）" type="warning" :closable="false" />
          </el-form-item>
        </el-form>
      </div>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="handleJMeterImportClose">取消</el-button>
          <el-button type="primary" @click="handleJMeterImport" :loading="jmeterImporting">
            确认导入
          </el-button>
        </span>
      </template>
    </el-dialog>

    <el-dialog v-model="historyDialogVisible" :title="`执行历史 - ${historyCaseName}`" width="800px" destroy-on-close>
      <div v-loading="historyLoading">
        <el-table :data="historyList" stripe size="small" max-height="400" empty-text="暂无执行记录">
          <el-table-column prop="execution_time" label="执行时间" width="90">
            <template #default="{ row }">
              <span>{{ (row.execution_time || 0).toFixed(0) }}ms</span>
            </template>
          </el-table-column>
          <el-table-column label="状态" width="90">
            <template #default="{ row }">
              <el-tag v-if="row.status === 'success'" type="success" size="small">成功</el-tag>
              <el-tag v-else-if="row.status === 'failed'" type="danger" size="small">失败</el-tag>
              <el-tag v-else type="info" size="small">{{ row.status }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="error_message" label="错误信息" min-width="200" show-overflow-tooltip />
          <el-table-column label="创建时间" width="170">
            <template #default="{ row }">
              {{ row.created_at ? new Date(row.created_at).toLocaleString() : '-' }}
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-dialog>

    <HelpDrawer
      v-model="showHelp"
      :title="helpData.title"
      :intro="helpData.intro"
      :sections="helpData.sections"
    />
  </el-card>

  <!-- 拖拽分隔条 2：列表 ↔ 编辑器
       target=right 表示 size 解读为"右侧面板（中间列表）的最大宽度"。
       拖动时所见即所得：向右拖 → listMaxWidth 增大，列表变宽；向左拖 → listMaxWidth 减小，列表变窄。
       列表使用 flex:1 弹性布局，max-width 受 listMaxWidth 限制，editor 反向让位（flex:1 占满剩余）。 -->
  <BaseSplitter
    v-model:size="listMaxWidth"
    target="right"
    direction="horizontal"
    :min-size="LIST_MIN_WIDTH"
    :max-size="listMaxLimit"
    storage-key="tm-caselist-list-max-width"
    container-selector=".case-list-layout"
  />

  <!-- 右侧：多 Tab 接口编辑器（常驻面板，对标 Apifox）
       改为 flex:1 弹性占满中间列表让出的空间，min-width 400px 保证可读性。 -->
  <div class="editor-panel" :style="{ flex: '1 1 0%', minWidth: '400px' }">
    <EditorTabContainer
      :env-id="selectedEnvId"
      :group-id="currentGroupId"
      @saved="handleTabSaved"
      @run="handleTabRun"
    />
  </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, onUnmounted } from 'vue'
import { onBeforeRouteLeave } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus,
  Search,
  VideoPlay,
  Edit,
  Delete,
  Setting,
  Upload,
  ArrowDown,
  UploadFilled,
  Download,
  Timer,
  Connection,
  FolderAdd,
  DocumentCopy,
  Rank,
  MoreFilled,
  Operation,
  Files,
  Grid,
  FullScreen,
  EditPen,
  RefreshRight
} from '@element-plus/icons-vue'
import CaseTreeSidebar from '@/components/CaseTreeSidebar.vue'
import EditorTabContainer from '@/components/EditorTabContainer.vue'
import { useEditorTabsStore } from '@/stores/editorTabs'
import EnvironmentManager from '@/components/EnvironmentManager.vue'
import HelpDrawer from '@/components/HelpDrawer.vue'
import BaseEmpty from '@/components/base/BaseEmpty.vue'
import BaseSplitter from '@/components/base/BaseSplitter.vue'
import { helpContent } from '@/utils/help-content'
import autoTestRequest from '@/utils/autoTestRequest'

// 三栏可拖拽布局（完全对称、所见即所得）：
// - splitter1 (target=left)  拖动 → sidebarWidth 变化 → 左侧分组树宽度
// - splitter2 (target=right) 拖动 → listMaxWidth 变化 → 中间列表的最大宽度（实际宽度受 flex:1 弹性影响）
// - 右侧编辑器：flex:1 自动占满剩余空间（min-width: 400px 保证可读性）
// 用户可以从两个方向自由调整三栏比例；editor 反向被挤压（list 变宽时 editor 自动让位）
const SIDEBAR_MIN = 180           // 侧边栏最小宽度（保留可识别的分组树）
const SIDEBAR_MAX = 500           // 侧边栏最大宽度（避免挤压列表）
const EDITOR_MIN_WIDTH = 400      // 编辑器最小可读宽度
const LIST_MIN_WIDTH = 280        // 列表最小宽度（保证表格列可读）
const SPLITTER_WIDTH = 12         // 单个分隔条宽度
// 根据窗口宽度计算合理默认布局（宽屏给更多展示空间）
const getDefaultLayout = () => {
  if (typeof window === 'undefined') return { sidebar: 220, listMaxWidth: 720 }
  const w = window.innerWidth
  if (w >= 1920) return { sidebar: 240, listMaxWidth: 960 }
  if (w >= 1600) return { sidebar: 240, listMaxWidth: 800 }
  if (w >= 1440) return { sidebar: 220, listMaxWidth: 720 }
  if (w >= 1280) return { sidebar: 200, listMaxWidth: 560 }
  return { sidebar: 180, listMaxWidth: 400 }
}
const _initialLayout = getDefaultLayout()
const sidebarWidth = ref(_initialLayout.sidebar)
const listMaxWidth = ref(_initialLayout.listMaxWidth)

// listMaxLimit = 视口 - sidebar - 编辑器最小宽 - 2 个 splitter 宽
// 这是中间列表在不挤压编辑器（min=400）情况下能取到的最大宽度
// 依赖 viewportWidth 确保视口缩放时能重新计算
const listMaxLimit = computed(() => {
  const vw = viewportWidth.value
  return Math.max(LIST_MIN_WIDTH, vw - sidebarWidth.value - EDITOR_MIN_WIDTH - SPLITTER_WIDTH * 2 - 20)
})

const props = defineProps({
  groupId: {
    type: [Number, String],
    default: null
  },
  environmentList: {
    type: Array,
    default: () => []
  },
  curlData: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['run', 'refresh-groups'])

const loading = ref(false)
const cases = ref([])
const searchKeyword = ref('')
const showHelp = ref(false)
const helpData = helpContent.caseList
const searchTimer = ref(null)
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const selectedEnvId = ref(null)
const envManagerVisible = ref(false)
// 多 Tab 编辑器 store（与 EditorTabContainer 共享同一 Pinia 实例）
const editorTabs = useEditorTabsStore()
const currentGroupId = ref(null)
const sidebarRef = ref(null)

// 响应式操作列宽度：宽屏 220（仅保留核心操作+更多菜单），中屏 180，窄屏固定右侧
const viewportWidth = ref(typeof window !== 'undefined' ? window.innerWidth : 1920)
const updateViewportWidth = () => { viewportWidth.value = window.innerWidth }
if (typeof window !== 'undefined') {
  window.addEventListener('resize', updateViewportWidth)
}
const actionColWidth = computed(() => {
  const w = viewportWidth.value
  if (w >= 1440) return 220
  if (w >= 1280) return 180
  return 160
})
const actionColFixed = computed(() => viewportWidth.value < 1280 ? 'right' : undefined)

// 视口缩放时,listMaxWidth 不能超过 listMaxLimit,也不能低于 LIST_MIN_WIDTH
watch(listMaxLimit, (newLimit) => {
  if (listMaxWidth.value > newLimit) listMaxWidth.value = newLimit
  if (listMaxWidth.value < LIST_MIN_WIDTH) listMaxWidth.value = LIST_MIN_WIDTH
})
// 视口缩放时,sidebarWidth 也不能超过新的合理范围
watch(viewportWidth, () => {
  const newMaxSidebar = Math.min(SIDEBAR_MAX, Math.max(SIDEBAR_MIN, viewportWidth.value - LIST_MIN_WIDTH - EDITOR_MIN_WIDTH - 40))
  if (sidebarWidth.value > newMaxSidebar) sidebarWidth.value = newMaxSidebar
})

// 布局预设：用户从下拉菜单选择，瞬时切换到对应尺寸
// 比纯拖拽更高效，适合"快速调出大屏列表"或"折叠侧边栏"等场景
const LAYOUT_PRESETS = {
  compact:        { sidebar: 180, listMaxWidth: 400 },
  default:        { sidebar: 220, listMaxWidth: 720 },
  wide:           { sidebar: 280, listMaxWidth: 1080 },
  'editor-focus': { sidebar: 180, listMaxWidth: 320 },
}
const applyLayoutPreset = (preset) => {
  // 'reset' 走视口自适应
  let target = preset === 'reset' ? getDefaultLayout() : LAYOUT_PRESETS[preset]
  if (!target) return
  sidebarWidth.value = Math.max(SIDEBAR_MIN, Math.min(SIDEBAR_MAX, target.sidebar))
  listMaxWidth.value = Math.max(LIST_MIN_WIDTH, Math.min(listMaxLimit.value, target.listMaxWidth))
  // 持久化（让 BaseSplitter 的 storageKey 行为一致）
  try {
    localStorage.setItem('tm-caselist-sidebar-width', String(sidebarWidth.value))
    localStorage.setItem('tm-caselist-list-max-width', String(listMaxWidth.value))
  } catch {}
  ElMessage?.success?.(`布局已切换：侧边 ${sidebarWidth.value}px / 列表最大 ${listMaxWidth.value}px`)
}

// 选中分组时触发（由侧边栏 emit），更新当前分组并重新加载用例
const handleSelectGroup = (groupId) => {
  currentGroupId.value = groupId
  currentPage.value = 1
  loadCases()
}

// 顶部工具栏"新建分组"按钮：委托给侧边栏组件打开新建根分组弹窗
const handleCreateGroup = () => {
  if (sidebarRef.value?.openCreateRoot) {
    sidebarRef.value.openCreateRoot()
  } else {
    ElMessage.info('请使用左侧分组树顶部按钮或右键菜单创建分组')
  }
}

// ===== 导入相关变量 =====
const importDialogVisible = ref(false)
const importType = ref('') // 'postman' or 'swagger'
const importFile = ref(null)
const importing = ref(false)
const parsedData = ref(null) // 解析后的预览数据

// ===== JMeter 导入/导出相关变量 =====
const jmeterImportDialogVisible = ref(false)
const jmeterImportFile = ref(null)
const jmeterImporting = ref(false)
const jmeterExporting = ref(false)
const jmeterImportGroupId = ref(null) // JMeter 导入目标分组ID

const historyDialogVisible = ref(false)
const historyCaseName = ref('')
const historyList = ref([])
const historyLoading = ref(false)

const handleShowHistory = async (row) => {
  historyDialogVisible.value = true
  historyCaseName.value = row.name
  historyLoading.value = true
  try {
    const res = await autoTestRequest.get('/auto-test/history', { params: { case_id: row.id, page_size: 20 } })
    historyList.value = Array.isArray(res) ? res : (res.items || [])
  } catch (e) {
    console.error('加载历史失败', e)
    historyList.value = []
  } finally {
    historyLoading.value = false
  }
}

// 打开环境管理弹窗
const openEnvManager = () => {
  envManagerVisible.value = true
}

// 环境列表变化
const handleEnvListChange = (envs) => {
  // 环境列表变化时，若当前选中的环境已不存在则重置，并刷新用例列表
  if (selectedEnvId.value && Array.isArray(envs) && !envs.some(e => e.id === selectedEnvId.value)) {
    selectedEnvId.value = null
  }
  loadCases()
}

// 过滤后的用例（前端按搜索关键字过滤）
const filteredCases = computed(() => {
  if (!searchKeyword.value) return cases.value
  const keyword = searchKeyword.value.toLowerCase()
  return cases.value.filter(c =>
    c.name?.toLowerCase().includes(keyword) ||
    c.url?.toLowerCase().includes(keyword) ||
    c.method?.toLowerCase().includes(keyword)
  )
})

// 获取状态对应的 Tag 类型
const getStatusCodeType = (status) => {
  if (!status) return 'info'
  const types = {
    passed: 'success',
    success: 'success',
    failed: 'danger',
    error: 'warning'
  }
  return types[status] || 'info'
}

const getMethodTagType = (method) => {
  const m = (method || '').toLowerCase()
  if (m === 'get') return 'success'
  if (m === 'post') return 'primary'
  if (m === 'put') return 'warning'
  if (m === 'delete') return 'danger'
  return 'info'
}

// 格式化状态文本
const formatStatus = (status) => {
  const labels = {
    passed: '通过',
    success: '通过',
    failed: '失败',
    error: '错误'
  }
  return labels[status] || status
}



// 加载用例
const loadCases = async () => {
  loading.value = true
  try {
    const params = {
      page: currentPage.value,
      page_size: pageSize.value
    }
    if (currentGroupId.value) {
      params.group_id = currentGroupId.value
    }
    if (searchKeyword.value) {
      params.keyword = searchKeyword.value
    }
    const res = await autoTestRequest.get('/auto-test/cases', { params })
    // 后端直接返回数组，或者返回 {items, total}
    if (Array.isArray(res)) {
      cases.value = res
      total.value = res.length
    } else {
      cases.value = Array.isArray(res.items) ? res.items : (Array.isArray(res) ? res : [])
      total.value = res.total || cases.value.length
    }
  } catch (error) {
    console.error('加载用例失败:', error)
    ElMessage.error('加载用例失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    loading.value = false
  }
}

// 监听外部传入的 groupId 变化（向后兼容），同步到内部状态并重新加载
watch(() => props.groupId, (newVal) => {
  currentGroupId.value = newVal
  currentPage.value = 1
  loadCases()
}, { immediate: true })

// 监听 curlData 变化，自动在新 Tab 中打开 cURL 转换的用例
watch(() => props.curlData, (newVal) => {
  if (newVal && newVal.method) {
    const caseData = {
      name: `${newVal.method} ${newVal.url || ''}`,
      method: newVal.method || 'GET',
      url: newVal.url || '',
      headers: newVal.headers || {},
      payload: newVal.body || null,
      body_type: newVal.body ? 'json' : 'none',
      group_id: currentGroupId.value
    }
    editorTabs.openTab({
      id: `case-new-${Date.now()}`,
      title: caseData.name,
      type: 'case',
      data: caseData
    })
  }
})

// 搜索
const handleSearch = () => {
  if (searchTimer.value) clearTimeout(searchTimer.value)
  searchTimer.value = setTimeout(() => {
    currentPage.value = 1
    loadCases()
  }, 300)
}

onUnmounted(() => {
  if (searchTimer.value) clearTimeout(searchTimer.value)
})

// 分页大小变化
const handlePageSizeChange = () => {
  currentPage.value = 1
  loadCases()
}

// 页码变化
const handlePageChange = () => {
  loadCases()
}

// 环境变化
const handleEnvChange = () => {
  // 环境变化不需要重新加载列表，运行时会用到
}

// 新建用例：在多 Tab 编辑器中打开一个新建 Tab
const handleCreate = () => {
  if (!currentGroupId.value) {
    ElMessage.warning('请先从左侧分组树选择一个分组再创建用例')
    return
  }
  editorTabs.openTab({
    id: `case-new-${Date.now()}`,
    title: '新建用例',
    type: 'case',
    data: { group_id: currentGroupId.value, new: true }
  })
}

// 编辑用例：在多 Tab 编辑器中打开（同一用例重复点击仅激活已有 Tab）
const handleEdit = (row) => {
  // 保留后端原始结构，避免对象型 headers/assert_rules 在编辑时被误清空
  const safeRow = JSON.parse(JSON.stringify(row))
  editorTabs.openTab({
    id: `case-${safeRow.id}`,
    title: safeRow.name || '未命名用例',
    type: 'case',
    data: { ...safeRow }
  })
}

// 双击行编辑
const handleRowDblClick = (row) => {
  handleEdit(row)
}

// 🔥 体验6：复制用例 — 深拷贝用例数据后在新 Tab 中打开"新建"模式，去掉 id 让保存走 POST
const handleCopyCase = async (row) => {
  try {
    // 优先从后端拉取完整数据，保证 headers/assertions/extractors 等完整
    let fullCase
    try {
      fullCase = await autoTestRequest.get(`/auto-test/cases/${row.id}`)
    } catch (e) {
      console.warn('拉取用例详情失败，使用列表数据兜底', e)
      fullCase = JSON.parse(JSON.stringify(row))
    }
    // 深拷贝并清除 id，使其成为新建用例
    const cloned = JSON.parse(JSON.stringify(fullCase))
    delete cloned.id
    cloned.name = `${cloned.name || '未命名用例'} (副本)`
    cloned.group_id = cloned.group_id || currentGroupId.value
    editorTabs.openTab({
      id: `case-new-${Date.now()}`,
      title: cloned.name,
      type: 'case',
      data: { ...cloned, new: true }
    })
    ElMessage.success('已复制用例，请在 Tab 中保存以创建新用例')
  } catch (error) {
    console.error('复制用例失败:', error)
    ElMessage.error('复制用例失败: ' + (error.response?.data?.detail || error.message))
  }
}

// 运行用例
const handleRun = (row) => {
  emit('run', row, selectedEnvId.value)
}

// 删除用例
const handleDelete = async (id) => {
  try {
    await ElMessageBox.confirm(
      '确定要彻底删除该接口吗？此操作不可逆，如果该接口已被场景引用，请先在场景中移除引用！',
      '高危操作警告',
      {
        confirmButtonText: '坚决删除',
        cancelButtonText: '点错了',
        type: 'warning',
      }
    )
  } catch {
    return
  }

  try {
    await autoTestRequest.delete(`/auto-test/cases/${id}`)
    ElMessage.success('清理完毕！')
    loadCases()
    sidebarRef.value?.loadGroups?.()
  } catch (error) {
    const realError = error.response?.data?.message || error.response?.data?.error || error.message || '删除遭遇异常'
    console.error('👉 删除接口失败详情:', error.response?.data)
    ElMessage.error(`❌ 删除失败原因: ${realError}`)
  }
}

// 多 Tab 编辑器保存成功后刷新用例列表与分组树
const handleTabSaved = () => {
  loadCases()
  // 用例增删后刷新分组树的 case_count
  sidebarRef.value?.loadGroups?.()
}

// 多 Tab 编辑器中“保存并运行”：复用列表运行链路，转发给父组件执行
const handleTabRun = (caseData) => {
  emit('run', caseData, selectedEnvId.value)
}

// ===== 导入逻辑 =====

const handleImportCommand = (command) => {
  if (command === 'jmeter') {
    // 打开 JMeter 导入对话框
    jmeterImportDialogVisible.value = true
    jmeterImportFile.value = null
  } else {
    // Postman 或 Swagger 导入
    importType.value = command
    importFile.value = null
    parsedData.value = null
    importDialogVisible.value = true
  }
}

// ===== JMeter 导入逻辑 =====

const handleJMeterFileChange = (file) => {
  jmeterImportFile.value = file.raw
}

const handleJMeterFileRemove = () => {
  jmeterImportFile.value = null
}

const handleJMeterImportClose = () => {
  jmeterImportDialogVisible.value = false
  jmeterImportFile.value = null
}

const handleJMeterImport = async () => {
  if (!jmeterImportFile.value) {
    ElMessage.warning('请先选择 JMeter .jmx 文件')
    return
  }

  jmeterImporting.value = true
  try {
    const formData = new FormData()
    formData.append('file', jmeterImportFile.value)
    if (currentGroupId.value) {
      formData.append('group_id', currentGroupId.value)
    }

    const res = await autoTestRequest.post('/auto-test/import/jmeter', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })

    ElMessage.success(res.message || '导入成功')
    jmeterImportDialogVisible.value = false
    loadCases() // 重新加载用例列表
    emit('refresh-groups') // 通知父组件刷新分组树
  } catch (error) {
    console.error('JMeter 导入失败:', error)
    ElMessage.error('导入失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    jmeterImporting.value = false
  }
}

// ===== JMeter 导出逻辑 =====

const exportSelectMode = ref(false)
const selectedCaseIds = ref([])
// 🔥 体验7：批量操作相关状态（保留选中行的完整数据，便于批量运行/移动）
const selectedCaseRows = ref([])
const caseTableRef = ref(null)
const batchRunning = ref(false)

const startExportSelect = () => {
  exportSelectMode.value = true
  selectedCaseIds.value = []
}

const cancelExportSelect = () => {
  exportSelectMode.value = false
  selectedCaseIds.value = []
}

const handleSelectionChange = (selection) => {
  selectedCaseIds.value = selection.map(item => item.id)
  selectedCaseRows.value = selection
}

// 清空表格选择
const clearSelection = () => {
  caseTableRef.value?.clearSelection?.()
  selectedCaseRows.value = []
  selectedCaseIds.value = []
}

// 🔥 体验7：批量运行（顺序执行，逐条调用运行接口；结果汇总在最终提示）
const handleBatchRun = async () => {
  if (selectedCaseRows.value.length === 0) {
    ElMessage.warning('请先勾选要运行的用例')
    return
  }
  if (!selectedEnvId.value) {
    ElMessage.warning('请先在顶部选择环境后再批量运行')
    return
  }
  batchRunning.value = true
  let successCount = 0
  let failCount = 0
  try {
    for (const row of selectedCaseRows.value) {
      try {
        await autoTestRequest.post(`/auto-test/cases/${row.id}/run`, { env_id: selectedEnvId.value })
        successCount++
      } catch (e) {
        failCount++
        console.error(`用例 ${row.name} 运行失败:`, e)
      }
    }
    ElMessage.success(`批量运行完成：成功 ${successCount} 个，失败 ${failCount} 个`)
  } finally {
    batchRunning.value = false
    loadCases()
  }
}

// 🔥 体验7：批量删除
const handleBatchDelete = async () => {
  if (selectedCaseIds.value.length === 0) {
    ElMessage.warning('请先勾选要删除的用例')
    return
  }
  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedCaseIds.value.length} 个用例吗？此操作不可逆。`,
      '批量删除确认',
      { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' }
    )
  } catch {
    return
  }
  let okCount = 0
  let failCount = 0
  for (const id of selectedCaseIds.value) {
    try {
      await autoTestRequest.delete(`/auto-test/cases/${id}`)
      okCount++
    } catch (e) {
      failCount++
      console.error(`删除用例 ${id} 失败:`, e)
    }
  }
  ElMessage.success(`批量删除完成：成功 ${okCount} 个，失败 ${failCount} 个`)
  clearSelection()
  loadCases()
  sidebarRef.value?.loadGroups?.()
}

// 🔥 体验7：批量移动到分组
const handleBatchMove = async () => {
  if (selectedCaseIds.value.length === 0) {
    ElMessage.warning('请先勾选要移动的用例')
    return
  }
  // 拉取分组树作为目标选项
  let groupTree = []
  try {
    groupTree = await autoTestRequest.get('/auto-test/groups/tree') || []
  } catch (e) {
    ElMessage.error('加载分组树失败：' + (e.response?.data?.detail || e.message))
    return
  }
  // 用 ElMessageBox.prompt 不适合树形选择，这里用 ElMessageBox + 自定义内容较复杂，
  // 简化方案：用 window.prompt 让用户输入分组 ID（或留空移到根级）
  let targetGroupId = null
  try {
    const flat = []
    const walk = (nodes, depth) => {
      nodes.forEach(n => {
        flat.push({ id: n.id, label: '  '.repeat(depth) + n.name })
        if (n.children?.length) walk(n.children, depth + 1)
      })
    }
    walk(groupTree, 0)
    const { value } = await ElMessageBox.prompt(
      `可选分组：\n${flat.map(f => `${f.id}: ${f.label}`).join('\n')}\n\n请输入目标分组 ID（留空则移到根级）：`,
      '移动到分组',
      { confirmButtonText: '移动', cancelButtonText: '取消', inputPlaceholder: '目标分组 ID（可留空）' }
    )
    targetGroupId = value ? Number(value) : null
  } catch {
    return
  }
  let okCount = 0
  let failCount = 0
  for (const id of selectedCaseIds.value) {
    try {
      // 复用用例的 PUT 接口更新 group_id（先 GET 再 PUT，避免覆盖其他字段）
      const caseData = await autoTestRequest.get(`/auto-test/cases/${id}`)
      caseData.group_id = targetGroupId
      // 后端 PUT 接收的是 snake_case 字段，但 caseData 已是后端结构，直接 PUT
      await autoTestRequest.put(`/auto-test/cases/${id}`, {
        group_id: targetGroupId,
        method: caseData.method,
        name: caseData.name,
        url: caseData.url,
        description: caseData.description || '',
        body_type: caseData.body_type || 'none',
        content_type: caseData.content_type || 'application/json',
        payload: caseData.payload,
        form_data: caseData.form_data || {},
        headers: caseData.headers || {},
        params: caseData.params || {},
        extractors: caseData.extractors || [],
        assertions: caseData.assertions || caseData.assert_rules || [],
        pre_script: caseData.pre_script || null,
        post_script: caseData.post_script || null,
        pre_script_language: caseData.pre_script_language || 'javascript',
        post_script_language: caseData.post_script_language || 'javascript',
        response_schema: caseData.response_schema || null,
      })
      okCount++
    } catch (e) {
      failCount++
      console.error(`移动用例 ${id} 失败:`, e)
    }
  }
  ElMessage.success(`批量移动完成：成功 ${okCount} 个，失败 ${failCount} 个`)
  clearSelection()
  loadCases()
}

const doExportJmx = async (caseIds) => {
  jmeterExporting.value = true
  try {
    const res = await autoTestRequest.post('/auto-test/export/jmeter/cases', {
      case_ids: caseIds,
    }, { responseType: 'blob' })

    const blob = new Blob([res], { type: 'application/octet-stream' })
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = `TestMaster_Export_${caseIds.length}cases_${new Date().getTime()}.jmx`
    link.click()
    URL.revokeObjectURL(link.href)

    ElMessage.success(`已导出 ${caseIds.length} 个用例`)
    exportSelectMode.value = false
    selectedCaseIds.value = []
  } catch (error) {
    console.error('JMeter 导出失败:', error)
    ElMessage.error('导出失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    jmeterExporting.value = false
  }
}

const handleExportJmx = () => {
  if (selectedCaseIds.value.length === 0) {
    ElMessage.warning('请先勾选要导出的用例')
    return
  }
  doExportJmx(selectedCaseIds.value)
}

const handleExportAllJmx = async () => {
  // 收集所有当前过滤后的用例 ID，复用 doExportJmx 进行导出
  const caseIds = filteredCases.value.map(c => c.id)
  if (caseIds.length === 0) {
    ElMessage.warning('没有可导出的用例')
    return
  }
  await doExportJmx(caseIds)
}

// 导出单个用例到 JMeter
const openJmeterIde = () => {
  window.open('/#/auto-test?tab=jmeter', '_blank')
}

const handleExportSingleCase = async (row) => {
  jmeterExporting.value = true
  try {
    const res = await autoTestRequest.get(`/auto-test/export/jmeter/case/${row.id}`, {
      responseType: 'blob'
    })

    // 下载文件
    const blob = new Blob([res], { type: 'application/octet-stream' })
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = `${row.name.replace(/[\/\\:*?"<>|]/g, '_')}.jmx`
    link.click()
    URL.revokeObjectURL(link.href)

    ElMessage.success('导出成功')
  } catch (error) {
    console.error('JMeter 导出失败:', error)
    ElMessage.error('导出失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    jmeterExporting.value = false
  }
}

// 操作列「更多」下拉菜单
const handleMoreAction = (cmd, row) => {
  if (cmd === 'copy') handleCopyCase(row)
  else if (cmd === 'export') handleExportSingleCase(row)
  else if (cmd === 'jmeter') openJmeterIde()
}

const handleFileChange = (file) => {
  importFile.value = file.raw
}

const handleFileRemove = () => {
  importFile.value = null
  parsedData.value = null
}

const handleImportClose = () => {
  importDialogVisible.value = false
  importFile.value = null
  parsedData.value = null
  importing.value = false
}

// 读取文件并发送给后端解析
const handleParseFile = async () => {
  importing.value = true
  parsedData.value = null

  try {
    const formData = new FormData()
    if (currentGroupId.value) {
      formData.append('target_group_id', currentGroupId.value)
    }

    if (!importFile.value) {
      ElMessage.warning('请选择文件')
      importing.value = false
      return
    }
    formData.append('file', importFile.value)

    const endpoint = importType.value === 'postman' ? '/auto-test/import/postman' : '/auto-test/import/swagger'

    // 告诉后端只解析，不入库 (dry_run)
    formData.append('dry_run', 'true')

    const res = await autoTestRequest.post(endpoint, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })

    if (res && Array.isArray(res.cases)) {
      // 组装冲突检测数据
      parsedData.value = res.cases.map(c => ({
        ...c,
        conflict: false // 默认全部为新增 (后续可以调用另一个接口做真实冲突检测)
      }))
      ElMessage.success(`成功解析 ${res.cases.length} 个接口`)
    } else {
      ElMessage.error('解析失败，返回数据格式不正确')
      parsedData.value = [] // 确保 parsedData 始终是一个数组
    }

  } catch (error) {
    console.error('解析失败', error)
    ElMessage.error('解析失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    importing.value = false
  }
}

// 确认导入入库
const handleConfirmImport = async () => {
  importing.value = true
  try {
    const formData = new FormData()
    if (currentGroupId.value) {
      formData.append('target_group_id', currentGroupId.value)
    }

    formData.append('file', importFile.value)

    const endpoint = importType.value === 'postman' ? '/auto-test/import/postman' : '/auto-test/import/swagger'

    // 真实导入 (dry_run=false)
    formData.append('dry_run', 'false')

    const res = await autoTestRequest.post(endpoint, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })

    ElMessage.success(`导入成功，共导入 ${res?.imported_count || res?.cases?.length || 0} 个接口`)
    handleImportClose()

    // 刷新用例列表
    loadCases()
    // 刷新左侧树 (如果后端生成了新分组)
    emit('refresh-groups')

  } catch (error) {
    console.error('导入失败', error)
    ElMessage.error('导入失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    importing.value = false
  }
}

onMounted(() => {
  // loadCases 已由 watch immediate 触发，无需重复调用
  // 🔥 Bug 3 修复：刷新页面时若有未保存 Tab，提示用户
  window.addEventListener('beforeunload', handleBeforeUnload)
})

onUnmounted(() => {
  window.removeEventListener('beforeunload', handleBeforeUnload)
  window.removeEventListener('resize', updateViewportWidth)
})

const handleBeforeUnload = (e) => {
  if (editorTabs.hasUnsavedChanges) {
    // 现代浏览器会忽略自定义文案，仅展示通用提示
    e.preventDefault()
    e.returnValue = '存在未保存的修改，确定离开吗？'
    return e.returnValue
  }
}

// 🔥 Bug 3 修复：路由切换时若有未保存 Tab，弹确认框拦截
onBeforeRouteLeave(async (to, from, next) => {
  if (!editorTabs.hasUnsavedChanges) {
    next()
    return
  }
  try {
    await ElMessageBox.confirm(
      '存在未保存的修改，离开将丢失这些修改，确定离开吗？',
      '未保存的修改',
      { type: 'warning', confirmButtonText: '离开', cancelButtonText: '留下' }
    )
    next()
  } catch {
    next(false)
  }
})

// 暴露方法给父组件
defineExpose({
  loadCases,
  // 刷新分组树（用例增删后调用以更新 case_count）
  refreshGroups: () => sidebarRef.value?.loadGroups?.(),
  // 选中指定分组
  selectGroup: (groupId) => handleSelectGroup(groupId)
})
</script>

<style scoped>
/* 左右布局：侧边栏固定 + 列表弹性 + 编辑器可调 */
.case-list-layout {
  display: flex;
  gap: 0;
  height: 100%;
  min-height: 0;
  overflow: hidden; /* 防止 splitter 拖到极端时三栏总宽溢出 */
}

.case-list-sidebar {
  flex-shrink: 0;
  min-height: 0;
  overflow: hidden;
}

.case-list-card {
  flex: 1 1 0%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: var(--tm-card-bg);
  box-shadow: 0 1px 4px rgba(0, 21, 41, 0.08);
  border-radius: 8px;
  border: 1px solid var(--tm-border-light);
}

/* 右侧多 Tab 编辑器面板（常驻） */
.editor-panel {
  flex-shrink: 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.case-list-card :deep(.el-card__body) {
  flex: 1;
  min-height: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.case-list-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  color: var(--tm-text-primary);
}

/* 工具栏 */
.list-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: nowrap;
  gap: 10px;
  padding: 10px 14px;
  margin-bottom: 12px;
  background: linear-gradient(135deg, rgba(var(--tm-color-primary-rgb), 0.04), transparent 70%);
  border-bottom: 1px solid var(--tm-border-light);
  border-radius: 12px 12px 0 0;
  position: relative;
  min-height: 52px;
}

.list-toolbar::before {
  content: '';
  position: absolute;
  left: 16px;
  right: 16px;
  bottom: -1px;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(var(--tm-color-primary-rgb), 0.4), transparent);
}

.toolbar-left,
.toolbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: nowrap;
  min-width: 0;
}

.toolbar-left .el-button,
.toolbar-right .el-button,
.toolbar-left .el-dropdown,
.toolbar-right .el-dropdown {
  white-space: nowrap;
  flex-shrink: 0;
}

/* 工具栏按钮文字在紧凑模式下隐藏，仅保留图标 */
.toolbar-btn-icon :deep(.el-icon) + span,
.toolbar-btn-icon span:not(.el-icon) {
  margin-left: 4px;
}

@media (max-width: 1600px) {
  .list-toolbar {
    flex-wrap: wrap;
    gap: 8px;
  }
  .toolbar-left,
  .toolbar-right {
    flex-wrap: wrap;
  }
}

@media (max-width: 1600px) {
  .toolbar-text-hide {
    display: none;
  }
  .toolbar-right .el-input {
    width: 140px !important;
  }
}

@media (max-width: 1366px) {
  .list-toolbar {
    gap: 6px;
    padding: 8px 10px;
  }
  .toolbar-left,
  .toolbar-right {
    gap: 5px;
  }
  .toolbar-right .el-input {
    width: 120px !important;
  }
  .toolbar-left .el-button,
  .toolbar-right .el-button {
    padding-left: 10px;
    padding-right: 10px;
  }
}



.case-table {
  flex: 1;
  padding: 0 12px 16px;
  overflow: auto;
  min-width: 0;
}

/* 表格强制横向滚动，避免列被无限压缩 */
.case-table :deep(.el-table) {
  min-width: 700px;
}
@media (max-width: 1366px) {
  .case-table :deep(.el-table) { min-width: 560px; }
}
@media (max-width: 1024px) {
  .case-table :deep(.el-table) { min-width: 0; }
}

/* 表头文字不换行 */
.case-table :deep(.el-table__header th) {
  white-space: nowrap;
}

/* 表格内容行垂直居中 */
.case-table :deep(.el-table__cell) {
  padding: 8px 0 !important;
}

/* 🔥 体验7：批量操作工具栏（玻璃拟态强化） */
.batch-toolbar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  margin: 0 12px 8px;
  background: rgba(var(--tm-color-primary-rgb), 0.08);
  backdrop-filter: blur(20px) saturate(180%);
  -webkit-backdrop-filter: blur(20px) saturate(180%);
  border: 1px solid rgba(var(--tm-color-primary-rgb), 0.25);
  border-radius: 12px;
  flex-shrink: 0;
  box-shadow: 0 4px 16px rgba(var(--tm-color-primary-rgb), 0.12),
              inset 0 1px 0 rgba(255, 255, 255, 0.06);
  animation: batch-slide-in 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

@keyframes batch-slide-in {
  from { opacity: 0; transform: translateY(-8px); }
  to { opacity: 1; transform: translateY(0); }
}
.batch-info {
  color: var(--tm-text-primary);
  font-size: 13px;
  font-weight: 600;
  margin-right: 4px;
}

/* 操作图标按钮 */
.action-icons {
  display: flex;
  gap: 15px;
  justify-content: center;
  align-items: center;
}

/* 操作列单元格：flex-wrap 让按钮在窄屏自动换行 */
.action-cell {
  display: flex;
  flex-wrap: nowrap;
  gap: 4px;
  align-items: center;
  justify-content: flex-end;
}

.action-more-trigger {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: 4px;
  color: var(--tm-text-secondary);
  cursor: pointer;
  transition: all 0.2s ease;
}
.action-more-trigger:hover {
  background: rgba(var(--tm-color-primary-rgb), 0.1);
  color: var(--tm-color-primary);
}

/* 分页 */
.pagination-wrapper {
  padding: 16px 20px;
  border-top: 1px solid var(--tm-border-light);
  display: flex;
  justify-content: flex-end;
  flex-shrink: 0;
}

/* 未执行文字 */
.no-run {
  color: var(--tm-text-secondary);
  font-size: 12px;
}

.import-preview {
  margin-top: 20px;
  border-top: 1px solid var(--tm-border-light);
  padding-top: 15px;
}

.import-preview h4 {
  margin-top: 0;
  margin-bottom: 12px;
  color: var(--tm-text-primary);
}

/* 响应式：1366 以下限制中间列表最小宽度，避免列表被无限压缩 */
@media (max-width: 1366px) {
  .case-list-card {
    min-width: 320px;
  }
}

/* 响应式：1366 以下编辑器面板下沉到第二行，三栏转两栏+堆叠，保证表格有足够宽度 */
@media (max-width: 1366px) {
  .editor-panel {
    width: 100% !important;
    flex: 1 1 100% !important;
    order: 3;
    min-width: 0 !important;
    height: 460px;
  }
  /* 编辑器下沉时隐藏列表↔编辑器之间的拖拽手柄 */
  .case-list-card + :deep(.base-splitter) {
    display: none;
  }
  .case-list-layout {
    flex-wrap: wrap;
    gap: 10px;
  }
}

/* 响应式：1024 以下编辑器面板下沉到第二行，三栏转两栏+堆叠 */
@media (max-width: 1024px) {
  .editor-panel {
    width: 100% !important;
    flex: 1 1 100% !important;
    order: 3;
    min-width: 0 !important;
    height: 500px;
  }
  /* 编辑器下沉时隐藏列表↔编辑器之间的拖拽手柄（紧跟在 card 后的 splitter） */
  .case-list-card + :deep(.base-splitter) {
    display: none;
  }
  .case-list-layout {
    flex-wrap: wrap;
    gap: 12px;
  }
  .case-list-sidebar {
    width: 100% !important;
    max-height: 200px;
  }
  /* 纵向堆叠时隐藏所有横向拖拽手柄 */
  .case-list-layout > :deep(.base-splitter) {
    display: none;
  }
  .case-list-card {
    min-width: 0;
    width: 100%;
  }
}

@media (max-width: 768px) {
  .list-toolbar {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
  }

  .toolbar-left,
  .toolbar-right {
    justify-content: center;
  }
}

.api-method-tag {
  display: inline-block;
  width: 64px;
  text-align: center;
  border-radius: 6px;
  font-weight: 700;
  font-size: 11px;
  letter-spacing: 0.06em;
  padding: 5px 0;
  transition: all 0.25s ease;
  font-family: 'JetBrains Mono', monospace;
}
.api-method-tag.get { background: rgba(var(--tm-method-get-rgb, 74, 222, 128), 0.15) !important; color: var(--tm-method-get, #4ade80) !important; border: 1px solid rgba(var(--tm-method-get-rgb, 74, 222, 128), 0.4) !important; box-shadow: 0 0 12px rgba(var(--tm-method-get-rgb, 74, 222, 128), 0.25), inset 0 0 8px rgba(var(--tm-method-get-rgb, 74, 222, 128), 0.1); }
.api-method-tag.post { background: rgba(var(--tm-method-post-rgb, 236, 72, 153), 0.15) !important; color: var(--tm-method-post, #ec4899) !important; border: 1px solid rgba(var(--tm-method-post-rgb, 236, 72, 153), 0.4) !important; box-shadow: 0 0 12px rgba(var(--tm-method-post-rgb, 236, 72, 153), 0.25), inset 0 0 8px rgba(var(--tm-method-post-rgb, 236, 72, 153), 0.1); }
.api-method-tag.put { background: rgba(var(--tm-method-put-rgb, 250, 204, 21), 0.15) !important; color: var(--tm-method-put, #facc15) !important; border: 1px solid rgba(var(--tm-method-put-rgb, 250, 204, 21), 0.4) !important; box-shadow: 0 0 12px rgba(var(--tm-method-put-rgb, 250, 204, 21), 0.25), inset 0 0 8px rgba(var(--tm-method-put-rgb, 250, 204, 21), 0.1); }
.api-method-tag.delete { background: rgba(var(--tm-method-delete-rgb, 248, 113, 113), 0.15) !important; color: var(--tm-method-delete, #f87171) !important; border: 1px solid rgba(var(--tm-method-delete-rgb, 248, 113, 113), 0.4) !important; box-shadow: 0 0 12px rgba(var(--tm-method-delete-rgb, 248, 113, 113), 0.25), inset 0 0 8px rgba(var(--tm-method-delete-rgb, 248, 113, 113), 0.1); }
.api-method-tag.patch { background: rgba(var(--tm-method-patch-rgb, 113, 113, 122), 0.15) !important; color: var(--tm-method-patch, #71717a) !important; border: 1px solid rgba(var(--tm-method-patch-rgb, 113, 113, 122), 0.4) !important; box-shadow: 0 0 12px rgba(var(--tm-method-patch-rgb, 113, 113, 122), 0.25), inset 0 0 8px rgba(var(--tm-method-patch-rgb, 113, 113, 122), 0.1); }
.api-method-tag.head { background: rgba(var(--tm-method-patch-rgb, 113, 113, 122), 0.15) !important; color: var(--tm-method-patch, #71717a) !important; border: 1px solid rgba(var(--tm-method-patch-rgb, 113, 113, 122), 0.4) !important; }
.api-method-tag.options { background: rgba(var(--tm-method-patch-rgb, 113, 113, 122), 0.15) !important; color: var(--tm-method-patch, #71717a) !important; border: 1px solid rgba(var(--tm-method-patch-rgb, 113, 113, 122), 0.4) !important; }

.api-method-tag:hover {
  transform: translateY(-1px);
  filter: brightness(1.15);
}

/* 表格行 stagger 入场动画 */
:deep(.el-table__row) {
  animation: row-stagger-in 0.4s cubic-bezier(0.4, 0, 0.2, 1) backwards;
}
:deep(.el-table__row:nth-child(1)) { animation-delay: 0.02s; }
:deep(.el-table__row:nth-child(2)) { animation-delay: 0.05s; }
:deep(.el-table__row:nth-child(3)) { animation-delay: 0.08s; }
:deep(.el-table__row:nth-child(4)) { animation-delay: 0.11s; }
:deep(.el-table__row:nth-child(5)) { animation-delay: 0.14s; }
:deep(.el-table__row:nth-child(6)) { animation-delay: 0.17s; }
:deep(.el-table__row:nth-child(7)) { animation-delay: 0.2s; }
:deep(.el-table__row:nth-child(8)) { animation-delay: 0.23s; }
:deep(.el-table__row:nth-child(n+9)) { animation-delay: 0.26s; }

@keyframes row-stagger-in {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

@media (prefers-reduced-motion: reduce) {
  :deep(.el-table__row),
  .batch-toolbar {
    animation: none !important;
  }
}

/* 现代化表格样式 */
.modern-table {
  border-collapse: separate;
  border-spacing: 0;
}

.modern-table :deep(.el-table__header-wrapper th) {
  font-size: 12px !important;
  font-weight: 500 !important;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-secondary) !important;
  background-color: var(--bg-surface) !important;
  border-bottom: 1px solid var(--border-subtle) !important;
}

.modern-table :deep(.el-table__row td) {
  border-bottom: 1px solid var(--border-subtle);
}

.modern-table :deep(.el-table__row:hover) {
  background-color: var(--bg-surface-hover, rgba(var(--tm-color-primary-rgb), 0.04));
}

/* 现代化空状态样式 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  text-align: center;
  min-height: 240px;
}

.empty-icon {
  color: var(--text-muted);
  margin-bottom: 12px;
}

.empty-icon svg {
  opacity: 0.5;
  width: 40px;
  height: 40px;
}

.empty-text {
  color: var(--text-muted);
  font-size: 13px;
  line-height: 18px;
  letter-spacing: -0.01em;
  font-weight: 400;
  margin-top: 6px;
}
</style>
