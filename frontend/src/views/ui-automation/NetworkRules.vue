<template>
  <div class="upgrade-page">
    <header class="page-header">
      <div>
        <h1>网络拦截规则</h1>
        <p>配置 fulfill / abort / delay / modify_headers，可绑定到用例或套件。</p>
      </div>
      <div class="actions">
        <el-button @click="load">刷新</el-button>
        <el-button type="primary" @click="openCreate">新建规则</el-button>
      </div>
    </header>

    <el-table :data="items" v-loading="loading" stripe>
      <el-table-column prop="name" label="名称" min-width="140" />
      <el-table-column prop="url_pattern" label="URL 模式" min-width="200" show-overflow-tooltip />
      <el-table-column prop="action" label="动作" width="120" />
      <el-table-column prop="method_filter" label="方法" width="90" />
      <el-table-column label="启用" width="90">
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'info'">{{ row.is_active ? '是' : '否' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="220" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openAssign(row)">绑定</el-button>
          <el-button link type="danger" @click="remove(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="showForm" title="新建网络规则" width="560px">
      <el-form label-width="110px">
        <el-form-item label="名称"><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="URL 模式"><el-input v-model="form.url_pattern" placeholder="**/api/orders*" /></el-form-item>
        <el-form-item label="动作">
          <el-select v-model="form.action" style="width: 100%">
            <el-option label="fulfill" value="fulfill" />
            <el-option label="abort" value="abort" />
            <el-option label="delay" value="delay" />
            <el-option label="modify_headers" value="modify_headers" />
          </el-select>
        </el-form-item>
        <el-form-item label="方法过滤"><el-input v-model="form.method_filter" placeholder="GET / POST / 空=全部" /></el-form-item>
        <el-form-item v-if="form.action === 'fulfill'" label="状态码">
          <el-input-number v-model="form.fulfill_status" :min="100" :max="599" />
        </el-form-item>
        <el-form-item v-if="form.action === 'fulfill'" label="响应体">
          <el-input v-model="form.fulfill_body" type="textarea" :rows="4" />
        </el-form-item>
        <el-form-item v-if="form.action === 'delay'" label="延迟 ms">
          <el-input-number v-model="form.delay_ms" :min="0" :max="120000" />
        </el-form-item>
        <el-form-item v-if="form.action === 'abort'" label="原因">
          <el-input v-model="form.abort_reason" placeholder="failed" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showForm = false">取消</el-button>
        <el-button type="primary" @click="create">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showAssign" title="绑定规则" width="420px">
      <el-form label-width="100px">
        <el-form-item label="目标类型">
          <el-select v-model="assignForm.target_type" style="width: 100%">
            <el-option label="UI 用例" value="ui_case" />
            <el-option label="UI 套件" value="ui_suite" />
            <el-option label="接口场景" value="scenario" />
          </el-select>
        </el-form-item>
        <el-form-item label="目标 ID"><el-input-number v-model="assignForm.target_id" :min="1" style="width: 100%" /></el-form-item>
        <el-form-item label="优先级"><el-input-number v-model="assignForm.priority" :min="0" :max="1000" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAssign = false">取消</el-button>
        <el-button type="primary" @click="assign">绑定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { storeToRefs } from 'pinia'
import { ElMessage, ElMessageBox } from 'element-plus'
import { featureUpgradesApi } from '@/api/feature-upgrades'
import { useProjectStore } from '@/stores/project'

const { projectId } = storeToRefs(useProjectStore())
const loading = ref(false)
const items = ref([])
const showForm = ref(false)
const showAssign = ref(false)
const form = reactive({
  name: '',
  url_pattern: '',
  action: 'fulfill',
  method_filter: '',
  fulfill_status: 200,
  fulfill_body: '{}',
  delay_ms: 1000,
  abort_reason: 'failed',
  is_active: true,
})
const assignForm = reactive({ rule_id: null, target_type: 'ui_case', target_id: 1, priority: 0 })

async function load() {
  loading.value = true
  try {
    const res = await featureUpgradesApi.listNetworkRules(projectId.value)
    items.value = res.items || []
  } catch (error) {
    ElMessage.error(error.message || '加载失败')
  } finally {
    loading.value = false
  }
}

function openCreate() {
  form.name = ''
  form.url_pattern = ''
  form.action = 'fulfill'
  showForm.value = true
}

async function create() {
  if (!form.name.trim() || !form.url_pattern.trim()) return ElMessage.warning('请填写名称与 URL 模式')
  try {
    await featureUpgradesApi.createNetworkRule(projectId.value, { ...form })
    showForm.value = false
    ElMessage.success('规则已创建')
    await load()
  } catch (error) {
    ElMessage.error(error.message || '创建规则失败')
  }
}

function openAssign(row) {
  assignForm.rule_id = row.id
  showAssign.value = true
}

async function assign() {
  try {
    await featureUpgradesApi.assignNetworkRule({ ...assignForm })
    showAssign.value = false
    ElMessage.success('已绑定')
  } catch (error) {
    ElMessage.error(error.message || '绑定失败')
  }
}

async function remove(row) {
  try {
    await ElMessageBox.confirm(`删除规则「${row.name}」？`, '确认', { type: 'warning' })
  } catch {
    return
  }
  try {
    await featureUpgradesApi.deleteNetworkRule(row.id)
    ElMessage.success('已删除')
    await load()
  } catch (error) {
    ElMessage.error(error.message || '删除失败')
  }
}

onMounted(load)
</script>

<style scoped>
.upgrade-page { padding: 20px; display: flex; flex-direction: column; gap: 16px; }
.page-header { display: flex; justify-content: space-between; gap: 12px; }
.page-header h1 { margin: 0 0 6px; font-size: 22px; }
.page-header p { margin: 0; color: #64748b; }
.actions { display: flex; gap: 8px; }
</style>
