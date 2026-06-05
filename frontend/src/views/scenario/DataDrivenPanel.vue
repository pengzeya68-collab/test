<template>
  <div class="data-driven-panel">
    <div class="panel-header">
      <div class="panel-title">
        <el-icon><Grid /></el-icon>
        <span>数据驱动</span>
        <el-tag v-if="datasetColumns.length > 0" type="success" size="small">
          {{ datasetRows.length }} 行数据
        </el-tag>
      </div>
      <div class="panel-actions">
        <el-button size="small" @click="handleRunDataDriven" :disabled="datasetRows.length === 0">
          <el-icon><VideoPlay /></el-icon>
          数据驱动执行
        </el-button>
      </div>
    </div>

    <div class="data-matrix-container">
      <div class="matrix-toolbar">
        <el-button size="small" type="primary" @click="addDataRow">
          <el-icon><Plus /></el-icon> 添加行
        </el-button>
        <el-button size="small" @click="addDataColumn">
          <el-icon><Plus /></el-icon> 添加变量
        </el-button>
        <input
          ref="fileInputRef"
          type="file"
          accept=".csv,.xlsx,.xls"
          style="display: none"
          @change="handleFileChange"
        />
        <el-button size="small" @click="triggerFileImport">
          <el-icon><Upload /></el-icon> 导入 CSV/Excel
        </el-button>
        <el-button size="small" @click="clearDataset">
          <el-icon><Delete /></el-icon> 清空
        </el-button>
      </div>

      <div class="matrix-table-wrapper" v-if="datasetColumns.length > 0">
        <table class="matrix-table">
          <thead>
            <tr>
              <th class="row-index-col">#</th>
              <th v-for="(col, colIndex) in datasetColumns" :key="'header-' + colIndex">
                <el-input
                  v-model="datasetColumns[colIndex]"
                  size="small"
                  placeholder="变量名"
                  @change="handleDatasetChange"
                />
              </th>
              <th class="action-col">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(row, rowIndex) in datasetRows" :key="'row-' + rowIndex">
              <td class="row-index-col">{{ rowIndex + 1 }}</td>
              <td v-for="(col, colIndex) in datasetColumns" :key="'cell-' + rowIndex + '-' + colIndex">
                <el-input
                  v-model="datasetRows[rowIndex][colIndex]"
                  size="small"
                  placeholder="值"
                  @change="handleDatasetChange"
                />
              </td>
              <td class="action-col">
                <el-button type="danger" size="small" text @click="removeDataRow(rowIndex)">
                  <el-icon><Delete /></el-icon>
                </el-button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <el-empty v-else description="暂无数据，请添加变量名和数据行" />

      <div class="matrix-hint">
        <el-alert type="info" :closable="false" show-icon>
          <template #title>
            <span>使用提示：在场景中的 URL、Headers、Payload 中使用&#123;&#123;变量名&#125;&#125;引用数据变量，如&#123;&#123;username&#125;&#125;、&#123;&#123;token&#125;&#125;</span>
          </template>
        </el-alert>
      </div>
    </div>
  </div>

  <el-dialog v-model="dataDrivenResultDialogVisible" title="数据驱动执行结果" width="90%" destroy-on-close>
    <div v-if="dataDrivenResult" class="dd-result-content">
      <el-descriptions :column="4" border class="result-summary">
        <el-descriptions-item label="场景名称">{{ dataDrivenResult.scenario_name }}</el-descriptions-item>
        <el-descriptions-item label="数据集">{{ dataDrivenResult.dataset_name }}</el-descriptions-item>
        <el-descriptions-item label="总迭代次数">{{ dataDrivenResult.total_iterations }}</el-descriptions-item>
        <el-descriptions-item label="总耗时">{{ dataDrivenResult.total_duration }} ms</el-descriptions-item>
        <el-descriptions-item label="成功">
          <el-tag type="success">{{ dataDrivenResult.success_iterations }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="失败">
          <el-tag type="danger">{{ dataDrivenResult.failed_iterations }}</el-tag>
        </el-descriptions-item>
      </el-descriptions>

      <el-divider>迭代详情</el-divider>
      <div class="iteration-list">
        <el-collapse>
          <el-collapse-item
            v-for="iteration in dataDrivenResult.iterations"
            :key="iteration.iteration_index"
            :name="iteration.iteration_index"
          >
            <template #title>
              <div class="iteration-header">
                <span>迭代 #{{ iteration.iteration_index + 1 }}</span>
                <span class="iteration-data">{{ formatDataRow(iteration.data_row) }}</span>
                <el-tag :type="iteration.success ? 'success' : 'danger'" size="small">
                  {{ iteration.success ? '成功' : '失败' }}
                </el-tag>
                <span class="iteration-duration">{{ iteration.duration }} ms</span>
              </div>
            </template>
            <div class="iteration-detail">
              <p v-if="iteration.error" class="error-msg">
                <el-alert type="error" :title="iteration.error" :closable="false" />
              </p>
              <p v-if="Object.keys(iteration.context_vars || {}).length > 0" class="context-vars">
                <strong>上下文变量：</strong>
                <el-tag v-for="(value, key) in iteration.context_vars" :key="key" size="small" style="margin-right: 4px">
                  {{ key }}: {{ value }}
                </el-tag>
              </p>
              <div v-if="iteration.step_results && iteration.step_results.length > 0" class="step-results">
                <strong>步骤结果：</strong>
                <div v-for="step in iteration.step_results" :key="step.step_id" class="step-result-item">
                  <el-tag :type="getMethodType(step.method)" size="small">{{ step.method }}</el-tag>
                  <span>{{ step.api_case_name }}</span>
                  <el-tag :type="step.success ? 'success' : 'danger'" size="small">
                    {{ step.status_code || 'Error' }}
                  </el-tag>
                </div>
              </div>
            </div>
          </el-collapse-item>
        </el-collapse>
      </div>
    </div>
  </el-dialog>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, VideoPlay, Delete, Grid, Upload } from '@element-plus/icons-vue'
import autoTestRequest from '@/utils/autoTestRequest'
import Papa from 'papaparse'
import * as XLSX from 'xlsx'

const props = defineProps({
  scenarioId: {
    type: [Number, String],
    required: true
  },
  dataset: {
    type: Object,
    default: () => ({ columns: [], rows: [] })
  },
  envId: {
    type: [Number, String],
    default: null
  }
})

const emit = defineEmits(['save-dataset', 'run-data-driven', 'dataset-changed'])

const datasetColumns = ref([])
const datasetRows = ref([])
const fileInputRef = ref(null)
const dataDrivenResultDialogVisible = ref(false)
const dataDrivenResult = ref(null)
let datasetSaveTimer = null
let datasetDirty = false

const getMethodType = (method) => {
  const types = { GET: 'success', POST: 'warning', PUT: 'primary', DELETE: 'danger', PATCH: 'info' }
  return types[method] || 'info'
}

watch(
  () => props.dataset,
  (newVal) => {
    if (newVal && newVal.columns && newVal.columns.length > 0) {
      datasetColumns.value = [...newVal.columns]
      datasetRows.value = (newVal.rows || []).map(row => [...row])
    }
  },
  { immediate: true }
)

watch(
  () => props.scenarioId,
  async () => {
    if (datasetSaveTimer) {
      clearTimeout(datasetSaveTimer)
      datasetSaveTimer = null
    }
    datasetDirty = false
    datasetColumns.value = []
    datasetRows.value = []
    await loadDataset()
  },
  { immediate: true }
)

const loadDataset = async () => {
  try {
    const res = await autoTestRequest.get(`/auto-test/scenarios/${props.scenarioId}/dataset`)
    if (res && res.data_matrix) {
      datasetColumns.value = res.data_matrix.columns || []
      datasetRows.value = res.data_matrix.rows || []
    } else {
      datasetColumns.value = []
      datasetRows.value = []
    }
  } catch (error) {
    console.error('加载数据集失败:', error)
    datasetColumns.value = []
    datasetRows.value = []
  }
}

const saveDataset = async () => {
  try {
    await autoTestRequest.post(`/auto-test/scenarios/${props.scenarioId}/dataset`, {
      name: '默认数据集',
      data_matrix: {
        columns: datasetColumns.value,
        rows: datasetRows.value
      }
    })
    datasetDirty = false
    emit('save-dataset')
  } catch (error) {
    console.error('保存数据集失败:', error)
  }
}

const flushDatasetSave = async () => {
  if (datasetSaveTimer) {
    clearTimeout(datasetSaveTimer)
    datasetSaveTimer = null
  }
  if (!datasetDirty) return
  await saveDataset()
}

const handleDatasetChange = () => {
  datasetDirty = true
  clearTimeout(datasetSaveTimer)
  datasetSaveTimer = setTimeout(() => {
    saveDataset()
  }, 300)
  emit('dataset-changed', {
    columns: datasetColumns.value,
    rows: datasetRows.value
  })
}

const addDataRow = () => {
  const newRow = datasetColumns.value.map(() => '')
  datasetRows.value.push(newRow)
  handleDatasetChange()
}

const addDataColumn = () => {
  datasetColumns.value.push(`var_${datasetColumns.value.length + 1}`)
  datasetRows.value.forEach(row => row.push(''))
  handleDatasetChange()
}

const removeDataRow = (index) => {
  datasetRows.value.splice(index, 1)
  handleDatasetChange()
}

const clearDataset = async () => {
  try {
    await ElMessageBox.confirm('确定要清空所有数据吗？', '提示', { type: 'warning' })
    datasetColumns.value = []
    datasetRows.value = []
    await autoTestRequest.delete(`/auto-test/scenarios/${props.scenarioId}/dataset`)
    ElMessage.success('已清空')
  } catch (error) {
    if (error !== 'cancel') console.error('清空数据集失败:', error)
  }
}

const triggerFileImport = () => {
  fileInputRef.value?.click()
}

const handleFileChange = (event) => {
  const file = event.target.files?.[0]
  if (!file) return

  const fileName = file.name.toLowerCase()

  if (fileName.endsWith('.csv')) {
    parseCSVFile(file)
  } else if (fileName.endsWith('.xlsx') || fileName.endsWith('.xls')) {
    parseExcelFile(file)
  } else {
    ElMessage.error('仅支持 .csv 或 .xlsx/.xls 文件')
  }

  event.target.value = ''
}

const parseCSVFile = (file) => {
  Papa.parse(file, {
    header: false,
    skipEmptyLines: true,
    complete: (results) => {
      processFileData(results.data)
    },
    error: (error) => {
      console.error('CSV 解析失败:', error)
      ElMessage.error('CSV 解析失败: ' + error.message)
    }
  })
}

const parseExcelFile = (file) => {
  const reader = new FileReader()

  reader.onload = (e) => {
    try {
      const data = new Uint8Array(e.target.result)
      const workbook = XLSX.read(data, { type: 'array', cellDates: true })

      const firstSheetName = workbook.SheetNames[0]
      const worksheet = workbook.Sheets[firstSheetName]

      const jsonData = XLSX.utils.sheet_to_json(worksheet, { header: 1, defval: '' })

      processFileData(jsonData)
    } catch (error) {
      console.error('Excel 解析失败:', error)
      ElMessage.error('Excel 解析失败: ' + error.message)
    }
  }

  reader.onerror = () => {
    ElMessage.error('文件读取失败')
  }

  reader.readAsArrayBuffer(file)
}

const processFileData = (data) => {
  if (!data || data.length === 0) {
    ElMessage.warning('文件内容为空')
    return
  }

  if (data.length === 1) {
    ElMessage.warning('文件只有表头，没有数据')
    return
  }

  const columns = data[0].map((col, index) => {
    return String(col).trim() || `变量${index + 1}`
  })

  const rows = data.slice(1).map(row => {
    return columns.map((_, colIndex) => {
      const cellValue = row[colIndex]
      if (cellValue && typeof cellValue === 'object' && cellValue instanceof Date) {
        return cellValue.toISOString().slice(0, 10)
      }
      return String(cellValue ?? '')
    })
  })

  datasetColumns.value = columns
  datasetRows.value = rows

  saveDataset()

  ElMessage.success(`成功导入 ${rows.length} 行数据，共 ${columns.length} 个变量`)
}

const formatDataRow = (dataRow) => {
  if (!dataRow) return ''
  return Object.entries(dataRow).map(([k, v]) => `${k}=${v}`).join(', ')
}

const handleRunDataDriven = async () => {
  if (datasetRows.value.length === 0) {
    ElMessage.warning('请先添加数据')
    return
  }
  try {
    const payload = {}
    if (props.envId) payload.env_id = props.envId
    const res = await autoTestRequest.post(`/auto-test/scenarios/${props.scenarioId}/run-data-driven`, payload)
    dataDrivenResult.value = res
    dataDrivenResultDialogVisible.value = true
    emit('run-data-driven', res)
  } catch (error) {
    ElMessage.error('数据驱动执行失败: ' + (error.response?.data?.detail || error.message))
  }
}

defineExpose({
  flushSave: flushDatasetSave
})

onMounted(() => {
  window.addEventListener('pagehide', flushDatasetSave)
})

onUnmounted(() => {
  window.removeEventListener('pagehide', flushDatasetSave)
  flushDatasetSave()
})
</script>

<style scoped>
.data-driven-panel {
  background: var(--tm-card-bg);
  border: 1px solid var(--tm-border-light);
  border-radius: 4px;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid var(--tm-border-light);
  background: rgba(var(--tm-bg-page-rgb), 0.5);
}

.panel-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
  font-size: 14px;
}

.panel-actions {
  display: flex;
  gap: 8px;
}

.data-matrix-container {
  padding: 16px;
}

.matrix-toolbar {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.matrix-table-wrapper {
  overflow-x: auto;
  border: 1px solid var(--tm-border-color);
  border-radius: 4px;
}

.matrix-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.matrix-table th,
.matrix-table td {
  padding: 8px;
  border: 1px solid var(--tm-border-light);
  text-align: left;
}

.matrix-table th {
  background: rgba(var(--tm-bg-page-rgb), 0.5);
  font-weight: 500;
  color: var(--tm-text-primary);
}

.matrix-table .row-index-col {
  width: 50px;
  text-align: center;
  background: rgba(var(--tm-bg-page-rgb), 0.5);
  color: var(--tm-text-secondary);
}

.matrix-table .action-col {
  width: 60px;
  text-align: center;
}

.matrix-table td .el-input {
  width: 100%;
}

.matrix-table td .el-input__inner {
  border: none;
  padding: 0 8px;
}

.matrix-table td .el-input__inner:focus {
  border: 1px solid #409eff;
  border-radius: 4px;
}

.matrix-hint {
  margin-top: 12px;
}

.matrix-hint code {
  background: rgba(var(--tm-bg-page-rgb), 0.5);
  padding: 2px 6px;
  border-radius: 3px;
  font-family: monospace;
  color: var(--tm-color-primary);
  border: 1px solid var(--tm-border-light);
}

.dd-result-content {
  max-height: 70vh;
  overflow: auto;
}

.iteration-header {
  display: flex;
  align-items: center;
  gap: 12px;
}

.iteration-data {
  color: var(--tm-text-secondary);
  font-size: 12px;
}

.iteration-duration {
  color: var(--tm-text-secondary);
  font-size: 12px;
}

.iteration-detail {
  padding: 12px;
  background: rgba(var(--tm-bg-page-rgb), 0.5);
  border-radius: 4px;
}

.step-result-item {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 4px;
}
</style>
