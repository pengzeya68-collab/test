<template>
  <el-drawer
    :model-value="modelValue"
    title="用例版本管理"
    direction="rtl"
    size="600px"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <div class="version-manager" v-loading="loading">
      <!-- 顶部操作栏 -->
      <div class="toolbar">
        <div class="toolbar-info">
          <span class="info-label">当前版本：</span>
          <el-tag v-if="currentVersion" type="success" size="small">{{ currentVersion }}</el-tag>
          <el-tag v-else type="info" size="small">未创建版本</el-tag>
          <span class="info-count">共 {{ versions.length }} 个版本</span>
        </div>
        <div class="toolbar-actions">
          <el-button
            v-if="versions.length >= 2"
            size="small"
            @click="openDiffDialog"
          >
            <el-icon><Connection /></el-icon>
            版本对比
          </el-button>
          <el-button type="primary" size="small" @click="openCreateDialog">
            <el-icon><Plus /></el-icon>
            保存为新版本
          </el-button>
        </div>
      </div>

      <!-- 版本时间线 -->
      <div class="version-timeline" v-if="versions.length > 0">
        <el-timeline>
          <el-timeline-item
            v-for="ver in versions"
            :key="ver.id"
            :timestamp="formatTime(ver.created_at)"
            placement="top"
            :type="ver.is_current ? 'success' : 'primary'"
            :hollow="!ver.is_current"
          >
            <el-card class="version-card" :class="{ 'is-current': ver.is_current }" shadow="hover">
              <div class="version-card-header">
                <div class="version-title">
                  <span class="version-number">{{ ver.version_number }}</span>
                  <el-tag v-if="ver.is_current" type="success" size="small">当前</el-tag>
                </div>
                <div class="version-label" v-if="ver.version_label">{{ ver.version_label }}</div>
              </div>
              <div class="version-card-body">
                <div class="version-meta">
                  <span class="meta-item">创建者：{{ ver.created_by || '未知' }}</span>
                </div>
              </div>
              <div class="version-card-actions">
                <el-button text size="small" @click="viewDetail(ver)">
                  <el-icon><View /></el-icon>
                  详情
                </el-button>
                <el-button
                  text
                  size="small"
                  type="primary"
                  :disabled="ver.is_current"
                  @click="confirmRestore(ver)"
                >
                  <el-icon><RefreshLeft /></el-icon>
                  恢复
                </el-button>
                <el-button
                  text
                  size="small"
                  type="danger"
                  :disabled="ver.is_current"
                  @click="confirmDelete(ver)"
                >
                  <el-icon><Delete /></el-icon>
                  删除
                </el-button>
              </div>
            </el-card>
          </el-timeline-item>
        </el-timeline>
      </div>

      <!-- 空状态 -->
      <el-empty v-else description="暂无版本记录，点击「保存为新版本」创建第一个版本" />
    </div>

    <!-- 创建版本对话框 -->
    <el-dialog v-model="createDialogVisible" title="保存为新版本" width="450px" append-to-body>
      <el-form :model="createForm" label-width="90px">
        <el-form-item label="版本号">
          <el-input
            v-model="createForm.version_number"
            placeholder="留空则自动递增（v1, v2, v3...）"
            clearable
          />
        </el-form-item>
        <el-form-item label="版本标签">
          <el-input
            v-model="createForm.version_label"
            placeholder="如：初始版本、修复登录Bug"
            clearable
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleCreate">保存版本</el-button>
      </template>
    </el-dialog>

    <!-- 版本详情对话框 -->
    <el-dialog v-model="detailDialogVisible" title="版本详情" width="700px" append-to-body>
      <div v-if="detailData" class="version-detail">
        <el-descriptions :column="2" border size="small">
          <el-descriptions-item label="版本号">{{ detailData.version_number }}</el-descriptions-item>
          <el-descriptions-item label="版本标签">{{ detailData.version_label || '-' }}</el-descriptions-item>
          <el-descriptions-item label="是否当前版本">
            <el-tag v-if="detailData.is_current" type="success" size="small">是</el-tag>
            <el-tag v-else type="info" size="small">否</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="创建者">{{ detailData.created_by || '-' }}</el-descriptions-item>
        </el-descriptions>
        <div class="snapshot-title">快照数据</div>
        <pre class="snapshot-content">{{ formatJson(detailData.snapshot) }}</pre>
      </div>
    </el-dialog>

    <!-- 版本对比对话框 -->
    <el-dialog v-model="diffDialogVisible" title="版本对比" width="850px" append-to-body>
      <div class="diff-selector" v-if="versions.length >= 2">
        <span>旧版本：</span>
        <el-select v-model="diffForm.v1" placeholder="选择旧版本" size="small" style="width: 200px;">
          <el-option
            v-for="ver in versions"
            :key="ver.id"
            :label="`${ver.version_number}${ver.version_label ? ' (' + ver.version_label + ')' : ''}`"
            :value="ver.id"
            :disabled="ver.id === diffForm.v2"
          />
        </el-select>
        <span style="margin: 0 10px;">→</span>
        <span>新版本：</span>
        <el-select v-model="diffForm.v2" placeholder="选择新版本" size="small" style="width: 200px;">
          <el-option
            v-for="ver in versions"
            :key="ver.id"
            :label="`${ver.version_number}${ver.version_label ? ' (' + ver.version_label + ')' : ''}`"
            :value="ver.id"
            :disabled="ver.id === diffForm.v1"
          />
        </el-select>
        <el-button type="primary" size="small" style="margin-left: 10px;" @click="loadDiff" :loading="diffLoading">
          对比
        </el-button>
      </div>

      <div class="diff-result" v-if="diffResult">
        <el-alert
          v-if="diffResult.is_identical"
          title="两个版本完全一致，无差异"
          type="success"
          :closable="false"
          show-icon
        />
        <template v-else>
          <div class="diff-summary">
            共发现 <strong>{{ diffResult.total_changes }}</strong> 处差异：
            <el-tag size="small" type="success">{{ changeTypeCount.added }} 新增</el-tag>
            <el-tag size="small" type="danger">{{ changeTypeCount.removed }} 删除</el-tag>
            <el-tag size="small" type="warning">{{ changeTypeCount.modified }} 修改</el-tag>
          </div>
          <el-table :data="diffResult.diffs" border size="small" style="margin-top: 10px;">
            <el-table-column label="字段" prop="field" width="220">
              <template #default="{ row }">
                <code>{{ row.field }}</code>
              </template>
            </el-table-column>
            <el-table-column label="变更类型" width="100">
              <template #default="{ row }">
                <el-tag
                  :type="changeTypeTag(row.change_type)"
                  size="small"
                >
                  {{ changeTypeText(row.change_type) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="旧值">
              <template #default="{ row }">
                <code class="diff-value old">{{ formatJson(row.old_value) }}</code>
              </template>
            </el-table-column>
            <el-table-column label="新值">
              <template #default="{ row }">
                <code class="diff-value new">{{ formatJson(row.new_value) }}</code>
              </template>
            </el-table-column>
          </el-table>
        </template>
      </div>
    </el-dialog>
  </el-drawer>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, View, RefreshLeft, Delete, Connection } from '@element-plus/icons-vue'
import autoTestRequest from '@/utils/autoTestRequest'

const props = defineProps({
  caseId: {
    type: [Number, String],
    default: null,
  },
  modelValue: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['update:modelValue', 'restored'])

const loading = ref(false)
const saving = ref(false)
const versions = ref([])
const currentVersion = ref(null)

// 创建版本对话框
const createDialogVisible = ref(false)
const createForm = ref({
  version_number: '',
  version_label: '',
})

// 版本详情对话框
const detailDialogVisible = ref(false)
const detailData = ref(null)

// 版本对比对话框
const diffDialogVisible = ref(false)
const diffForm = ref({ v1: null, v2: null })
const diffResult = ref(null)
const diffLoading = ref(false)

// 监听抽屉显隐与 caseId 变化，加载版本列表
watch(
  () => [props.modelValue, props.caseId],
  async ([visible, caseId]) => {
    if (visible && caseId) {
      await loadVersions()
    }
  }
)

// 加载版本列表
const loadVersions = async () => {
  if (!props.caseId) return
  loading.value = true
  try {
    const resp = await autoTestRequest.get(`/auto-test/cases/${props.caseId}/versions`)
    versions.value = resp.items || []
    currentVersion.value = resp.current_version
  } catch (error) {
    console.error('加载版本列表失败:', error)
    ElMessage.error('加载版本列表失败')
  } finally {
    loading.value = false
  }
}

// 打开创建版本对话框
const openCreateDialog = () => {
  createForm.value = { version_number: '', version_label: '' }
  createDialogVisible.value = true
}

// 创建版本
const handleCreate = async () => {
  if (!props.caseId) return
  saving.value = true
  try {
    const payload = {
      version_number: createForm.value.version_number || null,
      version_label: createForm.value.version_label || null,
    }
    await autoTestRequest.post(`/auto-test/cases/${props.caseId}/versions`, payload)
    ElMessage.success('版本保存成功')
    createDialogVisible.value = false
    await loadVersions()
  } catch (error) {
    console.error('保存版本失败:', error)
    ElMessage.error(error.response?.data?.detail || '保存版本失败')
  } finally {
    saving.value = false
  }
}

// 查看版本详情
const viewDetail = async (ver) => {
  try {
    const resp = await autoTestRequest.get(
      `/auto-test/cases/${props.caseId}/versions/${ver.id}`
    )
    detailData.value = resp
    detailDialogVisible.value = true
  } catch (error) {
    console.error('加载版本详情失败:', error)
    ElMessage.error('加载版本详情失败')
  }
}

// 确认恢复版本
const confirmRestore = (ver) => {
  ElMessageBox.confirm(
    `确定要将用例恢复到版本「${ver.version_number}」吗？当前用例数据将被覆盖。`,
    '恢复版本确认',
    {
      confirmButtonText: '确定恢复',
      cancelButtonText: '取消',
      type: 'warning',
    }
  )
    .then(async () => {
      try {
        await autoTestRequest.put(
          `/auto-test/cases/${props.caseId}/versions/${ver.id}/restore`
        )
        ElMessage.success(`已恢复到版本 ${ver.version_number}`)
        await loadVersions()
        emit('restored')
      } catch (error) {
        console.error('恢复版本失败:', error)
        ElMessage.error(error.response?.data?.detail || '恢复版本失败')
      }
    })
    .catch(() => {})
}

// 确认删除版本
const confirmDelete = (ver) => {
  ElMessageBox.confirm(
    `确定要删除版本「${ver.version_number}」吗？此操作不可撤销。`,
    '删除版本确认',
    {
      confirmButtonText: '确定删除',
      cancelButtonText: '取消',
      type: 'warning',
    }
  )
    .then(async () => {
      try {
        await autoTestRequest.delete(
          `/auto-test/cases/${props.caseId}/versions/${ver.id}`
        )
        ElMessage.success('版本已删除')
        await loadVersions()
      } catch (error) {
        console.error('删除版本失败:', error)
        ElMessage.error(error.response?.data?.detail || '删除版本失败')
      }
    })
    .catch(() => {})
}

// 打开版本对比对话框
const openDiffDialog = () => {
  diffForm.value = { v1: null, v2: null }
  diffResult.value = null
  // 默认选择最新两个版本（versions 按创建时间倒序，索引 0 最新）
  if (versions.value.length >= 2) {
    diffForm.value.v1 = versions.value[1].id
    diffForm.value.v2 = versions.value[0].id
  }
  diffDialogVisible.value = true
}

// 加载版本对比结果
const loadDiff = async () => {
  if (!diffForm.value.v1 || !diffForm.value.v2) {
    ElMessage.warning('请选择两个版本进行对比')
    return
  }
  diffLoading.value = true
  try {
    const resp = await autoTestRequest.get(
      `/auto-test/cases/${props.caseId}/versions/diff`,
      { params: { v1: diffForm.value.v1, v2: diffForm.value.v2 } }
    )
    diffResult.value = resp
  } catch (error) {
    console.error('版本对比失败:', error)
    ElMessage.error(error.response?.data?.detail || '版本对比失败')
  } finally {
    diffLoading.value = false
  }
}

// 变更类型统计
const changeTypeCount = computed(() => {
  if (!diffResult.value) return { added: 0, removed: 0, modified: 0 }
  const counts = { added: 0, removed: 0, modified: 0 }
  diffResult.value.diffs.forEach((d) => {
    counts[d.change_type] = (counts[d.change_type] || 0) + 1
  })
  return counts
})

// 变更类型对应的标签样式
const changeTypeTag = (type) => {
  const map = { added: 'success', removed: 'danger', modified: 'warning' }
  return map[type] || 'info'
}

// 变更类型对应的中文文案
const changeTypeText = (type) => {
  const map = { added: '新增', removed: '删除', modified: '修改' }
  return map[type] || type
}

// 格式化时间
const formatTime = (iso) => {
  if (!iso) return ''
  try {
    const d = new Date(iso)
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}:${String(d.getSeconds()).padStart(2, '0')}`
  } catch (e) {
    return iso
  }
}

// 格式化 JSON 输出
const formatJson = (val) => {
  if (val === null || val === undefined) return '-'
  if (typeof val === 'string') return val
  try {
    return JSON.stringify(val, null, 2)
  } catch (e) {
    return String(val)
  }
}

// 关闭抽屉
const handleClose = () => {
  emit('update:modelValue', false)
}
</script>

<style scoped>
.version-manager {
  padding: 16px;
  height: 100%;
  overflow-y: auto;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding: 10px 12px;
  background: var(--tm-bg-page, #f5f7fa);
  border-radius: 6px;
  flex-wrap: wrap;
  gap: 8px;
}

.toolbar-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.info-label {
  font-size: 13px;
  color: #606266;
}

.info-count {
  margin-left: 12px;
  font-size: 12px;
  color: #909399;
}

.toolbar-actions {
  display: flex;
  gap: 8px;
}

.version-timeline {
  margin-top: 8px;
}

.version-card {
  margin-bottom: 4px;
  transition: all 0.2s;
}

.version-card.is-current {
  border-left: 3px solid #67c23a;
}

.version-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.version-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.version-number {
  font-weight: 600;
  font-size: 14px;
  color: #303133;
}

.version-label {
  font-size: 13px;
  color: #606266;
  margin-top: 2px;
}

.version-meta {
  font-size: 12px;
  color: #909399;
  margin: 6px 0;
}

.version-card-actions {
  display: flex;
  gap: 4px;
  margin-top: 8px;
  border-top: 1px solid #ebeef5;
  padding-top: 8px;
}

.version-detail {
  padding: 0 4px;
}

.snapshot-title {
  margin: 16px 0 8px;
  font-weight: 600;
  font-size: 14px;
  color: #303133;
}

.snapshot-content {
  background: #f5f7fa;
  padding: 12px;
  border-radius: 4px;
  font-size: 12px;
  max-height: 400px;
  overflow-y: auto;
  white-space: pre-wrap;
  word-break: break-all;
}

.diff-selector {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
  font-size: 13px;
  flex-wrap: wrap;
  gap: 4px;
}

.diff-summary {
  margin: 8px 0;
  font-size: 13px;
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.diff-value {
  display: block;
  font-size: 12px;
  word-break: break-all;
  max-height: 100px;
  overflow-y: auto;
}

.diff-value.old {
  color: #f56c6c;
}

.diff-value.new {
  color: #67c23a;
}

:deep(.el-timeline-item__timestamp) {
  font-size: 12px;
}
</style>
