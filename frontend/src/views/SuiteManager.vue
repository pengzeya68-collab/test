<template>
  <div class="suite-manager-page">
    <div class="page-header">
      <div>
        <h2>测试套件管理</h2>
        <p class="subtitle">创建和管理测试套件，批量执行用例</p>
      </div>
      <el-button @click="showHelp = true">❓ 使用说明</el-button>
    </div>

    <!-- 套件列表 -->
    <div class="section">
      <div class="section-header">
        <h3>测试套件</h3>
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
            <span v-else class="text-muted">未执行</span>
          </template>
        </el-table-column>
        <el-table-column prop="last_run_at" label="最近执行时间" width="180">
          <template #default="{ row }">{{ row.last_run_at ? formatDate(row.last_run_at) : '-' }}</template>
        </el-table-column>
        <el-table-column label="操作" width="250" fixed="right">
          <template #default="{ row }">
            <el-button text size="small" @click="viewSuite(row)">查看</el-button>
            <el-button text size="small" type="primary" @click="runSuite(row)" :loading="row.running">
              执行
            </el-button>
            <el-button text size="small" @click="editSuite(row)">编辑</el-button>
            <el-button text size="small" type="danger" @click="deleteSuite(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination">
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
        <el-table :data="currentSuite.cases || []" stripe size="small">
          <el-table-column prop="case_name" label="用例名称" min-width="200" />
          <el-table-column prop="method" label="方法" width="100">
            <template #default="{ row }">
              <el-tag :type="getMethodType(row.method)" size="small">{{ row.method }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="url" label="URL" min-width="200" />
          <el-table-column prop="sort_order" label="顺序" width="80" align="center" />
        </el-table>
      </div>
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
        <el-form-item label="关联用例">
          <el-select
            v-model="suiteForm.case_ids"
            multiple
            filterable
            remote
            :remote-method="searchCases"
            placeholder="搜索并选择用例"
            style="width: 100%"
          >
            <el-option
              v-for="c in availableCases"
              :key="c.id"
              :label="`${c.method} ${c.name}`"
              :value="c.id"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="saveSuite" :loading="saving">保存</el-button>
      </template>
    </el-dialog>

    <!-- 执行结果对话框 -->
    <el-dialog v-model="showResultDialog" title="执行结果" width="700px">
      <div v-if="executionResult">
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
              <el-tag :type="row.status === 'passed' ? 'success' : 'danger'" size="small">
                {{ row.status === 'passed' ? '通过' : '失败' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="execution_time" label="耗时(ms)" width="100" />
          <el-table-column prop="error" label="错误信息" min-width="200" />
        </el-table>
      </div>
    </el-dialog>
    <HelpDrawer v-model="showHelp" :title="helpData.title" :intro="helpData.intro" :sections="helpData.sections" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import autoTestRequest from '@/utils/autoTestRequest'
import HelpDrawer from '@/components/HelpDrawer.vue'
import { helpContent } from '@/utils/help-content'

const API_BASE = '/auto-test/suites'
const CASES_API = '/auto-test/cases'

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

// 表单数据
const suiteForm = ref({
  name: '',
  description: '',
  case_ids: []
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

// 搜索用例
const searchCases = async (query) => {
  try {
    const res = await autoTestRequest.get(CASES_API, { params: { keyword: query, page_size: 100 } })
    availableCases.value = Array.isArray(res) ? res : (res.items || [])
  } catch (err) {
    console.error('搜索用例失败:', err)
    availableCases.value = []
  }
}

// 打开新建对话框（重置表单）
const openCreateDialog = () => {
  editingSuite.value = null
  suiteForm.value = { name: '', description: '', case_ids: [] }
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
      case_ids: (detail.cases || []).map(c => c.case_id || c.id)
    }
    // 加载用例选项
    await searchCases('')
    showCreateDialog.value = true
  } catch (err) {
    ElMessage.error('获取套件详情失败')
  }
}

// 保存套件
const saveSuite = async () => {
  if (!suiteForm.value.name) {
    ElMessage.warning('请输入套件名称')
    return
  }
  saving.value = true
  try {
    if (editingSuite.value) {
      await autoTestRequest.put(`${API_BASE}/${editingSuite.value.id}`, {
        name: suiteForm.value.name,
        description: suiteForm.value.description,
        case_ids: suiteForm.value.case_ids
      })
      ElMessage.success('套件更新成功')
    } else {
      await autoTestRequest.post(API_BASE, suiteForm.value)
      ElMessage.success('套件创建成功')
    }
    showCreateDialog.value = false
    editingSuite.value = null
    suiteForm.value = { name: '', description: '', case_ids: [] }
    await loadSuites()
  } catch (err) {
    ElMessage.error('保存失败: ' + (err.response?.data?.detail || err.message))
  } finally {
    saving.value = false
  }
}

// 执行套件
const runSuite = async (suite) => {
  suite.running = true
  try {
    const res = await autoTestRequest.post(`${API_BASE}/${suite.id}/run`)
    executionResult.value = res
    showResultDialog.value = true
    await loadSuites() // 刷新状态
  } catch (err) {
    ElMessage.error('执行失败: ' + (err.response?.data?.detail || err.message))
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
  loadSuites()
  searchCases('')
})
</script>

<style scoped>
.suite-manager-page {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
}

.page-header h2 {
  margin: 0 0 8px 0;
  font-size: 24px;
  color: #303133;
}

.page-header .subtitle {
  margin: 0;
  color: #909399;
  font-size: 14px;
}

.section {
  margin-bottom: 30px;
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.section-header h3 {
  margin: 0;
  font-size: 18px;
  color: #303133;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.description {
  color: #606266;
  margin-bottom: 20px;
}

.text-muted {
  color: #909399;
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
