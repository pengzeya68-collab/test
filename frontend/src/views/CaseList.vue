<template>
  <el-card class="case-list-card" shadow="never">
    <div class="case-list-container">
      <!-- 顶部工具栏 -->
      <div class="list-toolbar">
        <div class="toolbar-left">
          <el-select v-model="selectedEnvId" placeholder="选择环境" size="default" style="width: 200px" @change="handleEnvChange">
            <el-option
              v-for="env in environmentList"
              :key="env.id"
              :label="env.name"
              :value="env.id"
            />
          </el-select>
          <el-button type="primary" plain icon="Setting" @click="openEnvManager" />
        </div>
        <div class="toolbar-right">
          <el-input
            v-model="searchKeyword"
            placeholder="搜索用例名称或URL"
            size="default"
            style="width: 240px"
            clearable
            @input="handleSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
          <!-- 批量导入下拉菜单 -->
          <el-dropdown trigger="click" @command="handleImportCommand">
            <el-button type="success" plain>
              <el-icon><Upload /></el-icon>
              导入用例
              <el-icon class="el-icon--right"><ArrowDown /></el-icon>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="postman">Postman</el-dropdown-item>
                <el-dropdown-item command="swagger">Swagger/OpenAPI</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
          <el-button type="primary" @click="handleCreate">
            <el-icon><Plus /></el-icon>
            新建用例
          </el-button>
        </div>
      </div>

      <!-- 用例列表表格 -->
      <div class="case-table">
        <el-table
          :data="paginatedCases"
          style="width: 100%"
          stripe
          highlight-current-row
          row-key="id"
          class="modern-table"
          @row-dblclick="handleRowDblClick"
        >
          <el-table-column prop="method" label="请求方法" width="100">
            <template #default="{ row }">
              <span :class="['api-method-tag', (row.method || '').toLowerCase()]">{{ row.method }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="name" label="用例名称" min-width="180" />
          <el-table-column prop="url" label="URL" min-width="280" show-overflow-tooltip />
          <el-table-column label="最后执行" width="120" align="center">
            <template #default="{ row }">
              <el-tag v-if="row.lastRunStatus" :type="getStatusCodeType(row.lastRunStatus)" size="small">
                {{ formatStatus(row.lastRunStatus) }}
              </el-tag>
              <span v-else class="no-run">未执行</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="160" fixed="right">
            <template #default="{ row }">
              <div style="display: flex; gap: 12px; align-items: center;">
                <el-tooltip content="运行用例" placement="top" popper-class="action-tooltip">
                  <span><el-button type="primary" link :icon="VideoPlay" @click="handleRun(row)" /></span>
                </el-tooltip>

                <el-tooltip content="编辑用例" placement="top" popper-class="action-tooltip">
                  <span><el-button type="primary" link :icon="Edit" @click="handleEdit(row)" /></span>
                </el-tooltip>

                <el-tooltip content="删除用例" placement="top" popper-class="action-tooltip">
                  <span><el-button type="danger" link :icon="Delete" @click="handleDelete(row.id)" /></span>
                </el-tooltip>
              </div>
            </template>
          </el-table-column>
        </el-table>

        <div v-if="!loading && filteredCases.length === 0" class="empty-state">
          <div class="empty-icon">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm5 11h-4v4h-2v-4H7v-2h4V7h2v4h4v2z" fill="currentColor"/>
            </svg>
          </div>
          <div class="empty-text">暂无用例</div>
        </div>
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

    <!-- 编辑抽屉 -->
    <CaseEditorDrawer
      v-model="drawerVisible"
      :case-data="currentCase"
      :group-id="currentGroupId"
      :is-edit="isEdit"
      @success="handleDrawerSuccess"
      @run="handleRunCase"
    />

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

          <el-form-item label="默认分组" v-if="!props.groupId">
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
  </el-card>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
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
  UploadFilled
} from '@element-plus/icons-vue'
import CaseEditorDrawer from './CaseEditorDrawer.vue'
import EnvironmentManager from '@/components/EnvironmentManager.vue'
import axios from 'axios'

const props = defineProps({
  groupId: {
    type: [Number, String],
    default: null
  },
  environmentList: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['run', 'refresh-groups'])

const loading = ref(false)
const cases = ref([])
const searchKeyword = ref('')
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const selectedEnvId = ref(null)
const drawerVisible = ref(false)
const envManagerVisible = ref(false)
const currentCase = ref(null)
const isEdit = ref(false)
const currentGroupId = ref(null)

// ===== 导入相关变量 =====
const importDialogVisible = ref(false)
const importType = ref('') // 'postman' or 'swagger'
const importFile = ref(null)
const importing = ref(false)
const parsedData = ref(null) // 解析后的预览数据

// 打开环境管理弹窗
const openEnvManager = () => {
  envManagerVisible.value = true
}

// 环境列表变化
const handleEnvListChange = (envs) => {
  // props.environmentList 是父组件传入的，这里不需要处理，父组件会重新加载
}

// 过滤后的用例（搜索分页）
const filteredCases = computed(() => {
  let result = cases.value
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    result = result.filter(c =>
      c.name.toLowerCase().includes(keyword) ||
      (c.url && c.url.toLowerCase().includes(keyword))
    )
  }
  return result
})

// 分页后的用例 - 只返回当前页需要显示的数据
const paginatedCases = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filteredCases.value.slice(start, end)
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

// 创建独立的请求实例
const autoTestRequest = axios.create({
  baseURL: '',
  timeout: 30000
})

// 添加请求拦截器，自动带上 token
autoTestRequest.interceptors.request.use(
  config => {
    const token = localStorage.getItem('admin_token') || localStorage.getItem('token');
    if (token && token !== 'undefined' && token !== 'null' && token !== '[object Object]') {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  error => {
    return Promise.reject(error);
  }
)

// 添加响应拦截器，统一返回 response.data
autoTestRequest.interceptors.response.use(
  response => response.data,
  error => Promise.reject(error)
)

// 加载用例
const loadCases = async () => {
  loading.value = true
  try {
    const params = {
      page: currentPage.value,
      page_size: pageSize.value
    }
    if (props.groupId) {
      params.group_id = props.groupId
    }
    if (searchKeyword.value) {
      params.keyword = searchKeyword.value
    }
    const res = await autoTestRequest.get('/api/auto-test/cases', { params })
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

// 监听 groupId 变化，重新加载
watch(() => props.groupId, (newVal) => {
  currentGroupId.value = newVal
  currentPage.value = 1
  loadCases()
}, { immediate: true })

// 搜索
const handleSearch = () => {
  currentPage.value = 1
  loadCases()
}

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

// 新建用例
const handleCreate = () => {
  console.log('新建用例按钮被点击，当前分组ID:', props.groupId)
  if (!props.groupId) {
    ElMessage.warning('请先从左侧分组树选择一个分组再创建用例')
    return
  }
  currentCase.value = null
  isEdit.value = false
  currentGroupId.value = props.groupId
  drawerVisible.value = true
  console.log('抽屉已打开')
}

// 编辑用例
const handleEdit = (row) => {
  // 🔥 核心修复：对所有数组字段做安全兜底，防止老数据/脏数据缺少字段导致 .map() 崩溃
  const safeRow = JSON.parse(JSON.stringify(row))

  currentCase.value = {
    ...safeRow,
    // 如果后端返回 null/undefined，强制给一个空数组 []，防止 .map() 崩溃！
    headers: Array.isArray(safeRow.headers) ? safeRow.headers : [],
    form_data: Array.isArray(safeRow.form_data) ? safeRow.form_data : [],
    extractors: Array.isArray(safeRow.extractors) ? safeRow.extractors : [],
    assert_rules: Array.isArray(safeRow.assert_rules) ? safeRow.assert_rules : [],
  }
  isEdit.value = true
  currentGroupId.value = props.groupId
  drawerVisible.value = true
}

// 双击行编辑
const handleRowDblClick = (row) => {
  handleEdit(row)
}

// 运行用例
const handleRun = (row) => {
  emit('run', row, selectedEnvId.value)
}

// 删除用例
const handleDelete = async (id) => {
  try {
    // 弹出强阻断确认框，绝对不会点不动！
    await ElMessageBox.confirm(
      '确定要彻底删除该接口吗？此操作不可逆，如果该接口已被场景引用，请先在场景中移除引用！',
      '高危操作警告',
      {
        confirmButtonText: '坚决删除',
        cancelButtonText: '点错了',
        type: 'warning',
      }
    );

    // 发送删除请求
    await autoTestRequest.delete(`/api/auto-test/cases/${id}`);

    ElMessage.success('清理完毕！');
    // 重新加载列表数据
    loadCases();

  } catch (error) {
    // 如果是点击了取消，不报错；如果是后端返回错误，则弹出后端信息
    if (error !== 'cancel') {
      const realError = error.response?.data?.message || error.response?.data?.error || error.message || '删除遭遇异常';
      console.error('👉 删除接口失败详情:', error.response?.data);
      ElMessage.error(`❌ 删除失败原因: ${realError}`);
    }
  }
};

// 抽屉成功后刷新
const handleDrawerSuccess = () => {
  loadCases()
}

// 从抽屉运行
const handleRunCase = (caseData) => {
  handleRun(caseData)
}

// ===== 导入逻辑 =====

const handleImportCommand = (command) => {
  importType.value = command
  importFile.value = null
  parsedData.value = null
  importDialogVisible.value = true
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
    if (props.groupId) {
      formData.append('target_group_id', props.groupId)
    }

    if (!importFile.value) {
      ElMessage.warning('请选择文件')
      importing.value = false
      return
    }
    formData.append('file', importFile.value)

    const endpoint = importType.value === 'postman' ? '/api/auto-test/import/postman' : '/api/auto-test/import/swagger'

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
    if (props.groupId) {
      formData.append('target_group_id', props.groupId)
    }

    formData.append('file', importFile.value)

    const endpoint = importType.value === 'postman' ? '/api/auto-test/import/postman' : '/api/auto-test/import/swagger'

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
  loadCases()
})

// 暴露方法给父组件
defineExpose({
  loadCases
})
</script>

<style scoped>
.case-list-card {
  box-shadow: 0 1px 4px rgba(0, 21, 41, 0.08);
  border-radius: 8px;
  border: 1px solid var(--tm-border-light);
}

.case-list-container {
  display: flex;
  flex-direction: column;
  height: 100%;
}

/* 工具栏 */
.list-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  margin-bottom: 20px;
}

.toolbar-left,
.toolbar-right {
  display: flex;
  align-items: center;
  gap: 12px;
}



/* 表格区域 */
.case-table {
  flex: 1;
  padding: 0 12px 16px;
  overflow: auto;
}

/* 操作图标按钮 */
.action-icons {
  display: flex;
  gap: 15px;
  justify-content: center;
  align-items: center;
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

/* 响应式 */
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
  width: 60px;
  text-align: center;
  border-radius: 4px;
  font-weight: bold;
  font-size: 12px;
  padding: 4px 0;
}
.api-method-tag.get { background: rgba(82, 196, 26, 0.15) !important; color: #52c41a !important; border: 1px solid rgba(82, 196, 26, 0.3) !important; }
.api-method-tag.post { background: rgba(24, 144, 255, 0.15) !important; color: #1890ff !important; border: 1px solid rgba(24, 144, 255, 0.3) !important; }
.api-method-tag.put { background: rgba(250, 140, 22, 0.15) !important; color: #fa8c16 !important; border: 1px solid rgba(250, 140, 22, 0.3) !important; }
.api-method-tag.delete { background: rgba(245, 34, 45, 0.15) !important; color: #f5222d !important; border: 1px solid rgba(245, 34, 45, 0.3) !important; }

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
  background-color: rgba(255, 255, 255, 0.03);
}

/* 现代化空状态样式 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 64px 24px;
  text-align: center;
  min-height: 320px;
}

.empty-icon {
  color: var(--text-muted);
  margin-bottom: 16px;
}

.empty-icon svg {
  opacity: 0.6;
}

.empty-text {
  color: var(--text-muted);
  font-size: 14px;
  line-height: 20px;
  letter-spacing: -0.01em;
  font-weight: 400;
  margin-top: 8px;
}
</style>
