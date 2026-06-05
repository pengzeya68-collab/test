<template>
  <div class="steps-container">
    <draggable
      v-model="localSteps"
      item-key="id"
      handle=".drag-handle"
      @end="handleDragEnd"
      class="steps-list"
    >
      <template #item="{ element, index }">
        <div class="step-card" :class="{ 'is-inactive': !element.is_active }">
          <div class="drag-handle">
            <el-icon><Rank /></el-icon>
          </div>

          <div class="step-order">{{ index + 1 }}</div>

          <div class="step-info">
            <div class="step-main">
              <el-tag :type="getMethodType(element.api_case?.method)" effect="dark" size="small">
                {{ element.api_case?.method || 'GET' }}
              </el-tag>
              <span class="step-name">{{ element.api_case?.name || '未选择接口' }}</span>
            </div>
            <div class="step-url">{{ element.api_case?.url || '' }}</div>
          </div>

          <div class="step-actions-extend">
            <el-popover
              placement="bottom"
              :width="450"
              trigger="click"
              @show="loadExtractors(element)"
            >
              <template #reference>
                <el-button size="small" text>
                  <el-icon><Download /></el-icon>
                  提取变量
                  <el-badge v-if="getExtractorCount(element) > 0" :value="getExtractorCount(element)" />
                </el-button>
              </template>
              <div class="extractors-panel">
                <h4>响应提取变量</h4>
                <p class="extractors-hint">执行完成后从响应 JSON 提取变量，供给下游步骤使用 &#123;&#123;variable_name&#125;&#125;</p>

                <div class="extractors-list">
                  <div v-for="(ext, idx) in extractorForm" :key="idx" class="extractor-row">
                    <el-input
                      v-model="ext.variable_name"
                      placeholder="变量名称"
                      size="small"
                      style="width: 120px; margin-right: 8px;"
                    />
                    <el-input
                      v-model="ext.json_path"
                      placeholder="JSONPath 表达式，例如 $.data.token"
                      size="small"
                      style="flex: 1; margin-right: 8px;"
                    />
                    <el-button
                      type="danger"
                      size="small"
                      icon="Delete"
                      @click="removeExtractor(idx)"
                    />
                  </div>
                  <div class="extractor-actions">
                    <el-button size="small" type="primary" plain @click="addExtractor">
                      <el-icon><Plus /></el-icon> 添加规则
                    </el-button>
                    <el-button size="small" type="primary" @click="saveExtractors">
                      保存
                    </el-button>
                  </div>
                </div>
              </div>
            </el-popover>

            <el-popover
              placement="bottom"
              :width="400"
              trigger="click"
              @show="loadOverrides(element)"
            >
              <template #reference>
                <el-button size="small" text>
                  <el-icon><Setting /></el-icon>
                  局部覆盖
                  <el-badge v-if="getOverrideCount(element.variable_overrides) > 0" :value="getOverrideCount(element.variable_overrides)" />
                </el-button>
              </template>
              <div class="override-panel">
                <h4>局部变量覆盖</h4>
                <p class="override-hint">仅影响此场景中的此步骤，不修改接口库原始定义</p>

                <el-tabs>
                  <el-tab-pane label="URL 覆盖">
                    <el-input
                      v-model="overrideForm.url"
                      placeholder="可选：覆盖 URL"
                      @change="saveOverrides(element)"
                    />
                  </el-tab-pane>
                  <el-tab-pane label="Headers 覆盖">
                    <div class="override-table">
                      <el-table :data="overrideForm.headers" size="small">
                        <el-table-column label="Key" min-width="100">
                          <template #default="{ row }">
                            <el-input v-model="row.key" placeholder="Header key" />
                          </template>
                        </el-table-column>
                        <el-table-column label="Value" min-width="150">
                          <template #default="{ row }">
                            <el-input v-model="row.value" placeholder="Header value" />
                          </template>
                        </el-table-column>
                        <el-table-column width="50">
                          <template #default="{ $index }">
                            <el-button type="danger" size="small" text @click="removeOverrideHeader($index)">
                              <el-icon><Delete /></el-icon>
                            </el-button>
                          </template>
                        </el-table-column>
                      </el-table>
                      <el-button size="small" style="margin-top: 8px" @click="addOverrideHeader">
                        <el-icon><Plus /></el-icon> 添加
                      </el-button>
                    </div>
                  </el-tab-pane>
                  <el-tab-pane label="Payload 覆盖">
                    <div class="override-table">
                      <el-table :data="overrideForm.payloads" size="small">
                        <el-table-column label="Key" min-width="100">
                          <template #default="{ row }">
                            <el-input v-model="row.key" placeholder="参数名" />
                          </template>
                        </el-table-column>
                        <el-table-column label="Value" min-width="150">
                          <template #default="{ row }">
                            <el-input v-model="row.value" placeholder="参数值" />
                          </template>
                        </el-table-column>
                        <el-table-column width="50">
                          <template #default="{ $index }">
                            <el-button type="danger" size="small" text @click="removeOverridePayload($index)">
                              <el-icon><Delete /></el-icon>
                            </el-button>
                          </template>
                        </el-table-column>
                      </el-table>
                      <el-button size="small" style="margin-top: 8px" @click="addOverridePayload">
                        <el-icon><Plus /></el-icon> 添加
                      </el-button>
                    </div>
                  </el-tab-pane>
                </el-tabs>
              </div>
            </el-popover>
          </div>

          <div class="step-actions">
            <el-switch v-model="element.is_active" @change="handleStepActiveChange(element)" />
            <el-button type="danger" size="small" text @click="handleRemoveStep(element)">
              <el-icon><Delete /></el-icon>
            </el-button>
          </div>
        </div>
      </template>
    </draggable>

    <el-empty v-if="localSteps.length === 0" description="暂无步骤，点击上方添加步骤按钮添加">
      <el-button type="primary" @click="emit('add-step')">添加步骤</el-button>
    </el-empty>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Delete, Rank, Setting, Download } from '@element-plus/icons-vue'
import draggable from 'vuedraggable'
import autoTestRequest from '@/utils/autoTestRequest'

const props = defineProps({
  steps: {
    type: Array,
    required: true
  },
  scenarioId: {
    type: [Number, String],
    required: true
  }
})

const emit = defineEmits(['reorder', 'toggle-active', 'remove', 'edit-overrides', 'add-step'])

const localSteps = ref([])

watch(
  () => props.steps,
  (newVal) => {
    localSteps.value = [...newVal]
  },
  { immediate: true }
)

const overrideForm = ref({
  url: '',
  headers: [],
  payloads: []
})
const currentOverrideStep = ref(null)

const extractorForm = ref([])
const currentExtractorStep = ref(null)

const getMethodType = (method) => {
  const types = { GET: 'success', POST: 'warning', PUT: 'primary', DELETE: 'danger', PATCH: 'info' }
  return types[method] || 'info'
}

const getOverrideCount = (overrides) => {
  if (!overrides) return 0
  let count = 0
  if (overrides.url) count++
  if (overrides.headers) count += Object.keys(overrides.headers).length
  if (overrides.payload) count += Object.keys(overrides.payload).length
  return count
}

const loadOverrides = (step) => {
  currentOverrideStep.value = step
  const overrides = step.variable_overrides || {}
  overrideForm.value = {
    url: overrides.url || '',
    headers: Object.entries(overrides.headers || {}).map(([key, value]) => ({ key, value })),
    payloads: Object.entries(overrides.payload || {}).map(([key, value]) => ({ key, value }))
  }
}

const addOverrideHeader = () => {
  overrideForm.value.headers.push({ key: '', value: '' })
}

const removeOverrideHeader = (index) => {
  overrideForm.value.headers.splice(index, 1)
}

const addOverridePayload = () => {
  overrideForm.value.payloads.push({ key: '', value: '' })
}

const removeOverridePayload = (index) => {
  overrideForm.value.payloads.splice(index, 1)
}

const saveOverrides = async (step) => {
  const overrides = {}
  if (overrideForm.value.url) overrides.url = overrideForm.value.url
  if (overrideForm.value.headers.length > 0) {
    const headers = {}
    overrideForm.value.headers.forEach(h => { if (h.key) headers[h.key] = h.value })
    if (Object.keys(headers).length > 0) overrides.headers = headers
  }
  if (overrideForm.value.payloads.length > 0) {
    const payloads = {}
    overrideForm.value.payloads.forEach(p => { if (p.key) payloads[p.key] = p.value })
    if (Object.keys(payloads).length > 0) overrides.payload = payloads
  }

  try {
    await autoTestRequest.put(`/auto-test/scenarios/${props.scenarioId}/steps/${step.id}`, {
      variable_overrides: Object.keys(overrides).length > 0 ? overrides : null
    })
    step.variable_overrides = Object.keys(overrides).length > 0 ? overrides : null
    ElMessage.success('保存成功')
    emit('edit-overrides', { step, overrides: step.variable_overrides })
  } catch (error) {
    ElMessage.error('保存失败')
  }
}

const getExtractorCount = (step) => {
  const extractors = step?.api_case?.extractors || step?.extractors || []
  return Array.isArray(extractors) ? extractors.length : 0
}

const loadExtractors = (step) => {
  currentExtractorStep.value = step
  const extractors = step.api_case?.extractors || step.extractors || []
  if (extractors.length > 0) {
    extractorForm.value = extractors.map(e => ({ ...e }))
  } else {
    extractorForm.value = []
  }
}

const addExtractor = () => {
  extractorForm.value.push({
    variable_name: '',
    json_path: ''
  })
}

const removeExtractor = (index) => {
  extractorForm.value.splice(index, 1)
}

const saveExtractors = async () => {
  if (!currentExtractorStep.value) return

  const validExtractors = extractorForm.value.filter(
    ext => ext.variable_name?.trim() && ext.json_path?.trim()
  )

  try {
    await autoTestRequest.put(`/auto-test/cases/${currentExtractorStep.value.api_case_id}`, {
      extractors: validExtractors.length > 0 ? validExtractors : null
    })
    if (currentExtractorStep.value.api_case) {
      currentExtractorStep.value.api_case.extractors = validExtractors.length > 0 ? validExtractors : null
    } else {
      currentExtractorStep.value.extractors = validExtractors.length > 0 ? validExtractors : null
    }
    ElMessage.success('保存成功')
    emit('edit-overrides', { step: currentExtractorStep.value, extractors: validExtractors })
  } catch (error) {
    ElMessage.error('保存失败')
  }
}

const handleDragEnd = () => {
  const stepOrders = localSteps.value.map((step, index) => ({
    step_id: step.id,
    step_order: index
  }))
  emit('reorder', stepOrders)
}

const handleStepActiveChange = (step) => {
  emit('toggle-active', step)
}

const handleRemoveStep = async (step) => {
  try {
    await ElMessageBox.confirm('确定要移除此步骤吗？', '提示', { type: 'warning' })
    emit('remove', step)
  } catch (error) {
    // user cancelled
  }
}
</script>

<style scoped>
.steps-container {
  padding: 0;
  overflow: visible;
}

.steps-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.step-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: var(--tm-card-bg);
  border: 1px solid var(--tm-border-light);
  border-radius: 4px;
  transition: all 0.3s;
}

.step-card:hover {
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.step-card.is-inactive {
  opacity: 0.5;
  background: rgba(var(--tm-bg-page-rgb), 0.5);
}

.drag-handle {
  cursor: move;
  color: var(--tm-text-secondary);
  font-size: 18px;
}

.step-order {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--tm-color-primary);
  color: var(--tm-text-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 500;
}

.step-info {
  flex: 1;
  min-width: 0;
}

.step-main {
  display: flex;
  align-items: center;
  gap: 8px;
}

.step-name {
  font-weight: 500;
  color: var(--tm-text-primary);
}

.step-url {
  margin-top: 4px;
  font-size: 12px;
  color: var(--tm-text-secondary);
  font-family: monospace;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.step-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.step-actions-extend {
  display: flex;
  gap: 8px;
}

.override-panel h4 {
  margin: 0 0 8px;
  color: var(--tm-text-primary);
}

.override-hint {
  margin: 0 0 16px;
  color: var(--tm-text-secondary);
  font-size: 12px;
}

.extractors-panel h4 {
  margin: 0 0 8px;
  color: var(--tm-text-primary);
}

.extractors-hint {
  margin: 0 0 16px;
  color: var(--tm-text-secondary);
  font-size: 12px;
}

.extractors-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.extractor-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.extractor-actions {
  display: flex;
  gap: 8px;
  margin-top: 8px;
}
</style>
