<template>
  <el-dialog v-model="dialogVisible" title="定时计划配置" width="500px">
    <el-form :model="scheduleForm" label-position="top">

      <el-row :gutter="12">
        <el-col :span="12">
          <el-form-item label="场景名称">
            <span>{{ scheduleForm.scenario_name }}</span>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="执行环境">
            <el-select v-model="scheduleForm.env_id" placeholder="选择执行环境" clearable style="width: 100%">
              <el-option
                v-for="env in environments"
                :key="env.id"
                :label="env.name"
                :value="env.id"
              />
            </el-select>
            <div class="form-tip">
              留空使用默认环境
            </div>
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="12">
        <el-col :span="12">
          <el-form-item label="快速选择" required>
            <el-select v-model="scheduleForm.cron_expression" placeholder="选择执行频率" style="width: 100%">
              <el-option
                v-for="preset in schedulePresets"
                :key="preset.value"
                :label="preset.label"
                :value="preset.value"
              />
            </el-select>
          </el-form-item>
          <el-form-item>
            <template #label>
              <span>Cron 表达式</span>
              <el-tooltip content="格式：分 时 日 月 周&#10;常用：&#10;每天凌晨2点 → 0 2 * * *&#10;每小时 → 0 * * * *&#10;每周一早上9点 → 0 9 * * 1" placement="top">
                <el-icon :size="14" style="margin-left: 4px; color: var(--tm-text-secondary); cursor: help;"><QuestionFilled /></el-icon>
              </el-tooltip>
            </template>
            <el-input v-model="scheduleForm.cron_expression" placeholder="分 时 日 月 周" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="任务状态">
            <el-switch
              v-model="scheduleForm.is_active"
              active-color="#13ce66"
              inactive-color="#8e8e93"
              active-text="立即启用"
              inactive-text="暂不启用"
              inline-prompt
            />
            <div class="form-tip">
              禁用 = 调度器挂起
            </div>
          </el-form-item>
        </el-col>
      </el-row>

      <el-row>
        <el-col :span="24">
          <el-form-item label="Webhook 告警">
            <el-input v-model="scheduleForm.webhook_url" placeholder="钉钉/飞书/企业微信机器人 Webhook 地址（可选）" />
            <div class="form-tip">
              测试执行完成后自动发送测试报告
            </div>
          </el-form-item>
        </el-col>
      </el-row>

      <el-collapse>
        <el-collapse-item title="📋 查看常用 Cron 示例">
          <div class="cron-help">
            <ul>
              <li><code>0 2 * * *</code> - 每天凌晨2点</li>
              <li><code>0 9 * * 1</code> - 每周一早上9点</li>
              <li><code>0 */6 * * *</code> - 每6小时</li>
              <li><code>0 0 1 * *</code> - 每月1号凌晨</li>
            </ul>
          </div>
        </el-collapse-item>
      </el-collapse>

      <div v-if="currentExistingTasks.length > 0" class="existing-tasks">
        <div class="section-title">当前已有定时任务</div>
        <el-table :data="currentExistingTasks" style="width: 100%; margin-top: 8px" size="small">
          <el-table-column prop="task_id" label="ID" width="60" align="center" />
          <el-table-column prop="name" label="名称" width="120" />
          <el-table-column prop="cron_expression" label="Cron" width="120" />
          <el-table-column prop="is_active" label="状态" width="100" align="center">
            <template #default="{ row }">
              <el-switch
                v-model="row.is_active"
                :loading="row.statusLoading"
                active-color="#13ce66"
                inactive-color="#8e8e93"
                active-text="调度中"
                inactive-text="已挂起"
                inline-prompt
                @change="handleToggleTaskStatus(row)"
              />
            </template>
          </el-table-column>
          <el-table-column prop="last_run" label="上次执行" width="130" />
        </el-table>
      </div>

    </el-form>
    <template #footer>
      <el-button @click="dialogVisible = false">取消</el-button>
      <el-button type="danger" @click="handleDeleteSchedule(scheduleForm.scenario_id)" v-if="scheduleTasks[scheduleForm.scenario_id]?.length">
        删除定时任务
      </el-button>
      <el-button type="primary" @click="handleScheduleSubmit">保存</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { QuestionFilled } from '@element-plus/icons-vue'
import autoTestRequest from '@/utils/autoTestRequest'

const props = defineProps({
  scenarioId: { type: Number, default: null },
  scenarioName: { type: String, default: '' },
  visible: { type: Boolean, default: false },
  environments: { type: Array, default: () => [] },
  cronExpression: { type: String, default: '' },
  webhookUrl: { type: String, default: '' },
})

const emit = defineEmits(['update:visible', 'schedule-changed'])

const dialogVisible = computed({
  get: () => props.visible,
  set: (val) => emit('update:visible', val)
})

const scheduleForm = ref({
  scenario_id: null,
  scenario_name: '',
  name: '',
  cron_expression: '0 2 * * *',
  env_id: null,
  webhook_url: '',
  is_active: true,
})

const scheduleTasks = ref({})
const schedulePresets = [
  { label: '每天凌晨2点', value: '0 2 * * *' },
  { label: '每天上午9点', value: '0 9 * * *' },
  { label: '每天下午6点', value: '0 18 * * *' },
  { label: '每6小时', value: '0 */6 * * *' },
  { label: '每周一早上9点', value: '0 9 * * 1' },
  { label: '每月1号凌晨', value: '0 0 1 * *' }
]

const currentExistingTasks = computed(() => {
  const sid = scheduleForm.value.scenario_id
  if (!sid) return []
  return scheduleTasks.value[sid] || []
})

const loadScheduleTasks = async () => {
  try {
    const res = await autoTestRequest.get('/auto-test/scheduler/tasks')
    const grouped = {}
    for (const task of res || []) {
      const sid = task.scenario_id
      if (!grouped[sid]) grouped[sid] = []
      task.statusLoading = false
      grouped[sid].push(task)
    }
    scheduleTasks.value = grouped
  } catch (error) {
    console.error('加载定时任务失败:', error)
  }
}

const handleToggleTaskStatus = async (task) => {
  // v-model 已将 is_active 切换为新值，这里保存的是切换后的值
  const toggledStatus = task.is_active
  task.statusLoading = true
  try {
    await autoTestRequest.post(`/auto-test/scheduler/tasks/${task.task_id}/toggle`)
    ElMessage.success(`任务已${toggledStatus ? '启用' : '暂停'}`)
    await loadScheduleTasks()
  } catch (error) {
    // 恢复为切换前的值
    task.is_active = !toggledStatus
    ElMessage.error('状态切换失败: ' + (error.response?.data?.error || error.message))
    console.error('切换状态失败:', error)
  } finally {
    task.statusLoading = false
  }
}

const cronToHuman = (cron) => {
  const parts = (cron || '').split(' ')
  if (parts.length !== 5) return cron || ''
  const [minute, hour, day, month, dow] = parts

  const formatHour = (h) => {
    if (h === '*') return '每小时'
    if (h.startsWith('*/')) return `每${h.slice(2)}小时`
    return h
  }

  if (day === '*' && month === '*' && dow === '*') {
    if (hour === '*' && minute === '*') return '每分钟执行'
    if (hour === '*') return `每小时第${minute}分钟执行`
    if (hour.startsWith('*/')) return `${formatHour(hour)}的${minute.padStart(2, '0')}分执行`
    return `每天 ${hour}:${minute.padStart(2, '0')}`
  }
  if (dow === '1' && day === '*') return `每周一 ${hour}:${minute.padStart(2, '0')}`
  if (day === '1' && month === '*') return `每月1号 ${hour}:${minute.padStart(2, '0')}`
  return cron
}

const getScheduleLabel = (scenarioId) => {
  const tasks = scheduleTasks.value[scenarioId]
  if (!tasks || tasks.length === 0) return ''
  const cron = tasks[0].cron_expression
  return cronToHuman(cron)
}

const handleScheduleSubmit = async () => {
  try {
    // 先删除旧任务，再创建新任务，避免重复
    const existingTasks = scheduleTasks.value[scheduleForm.value.scenario_id] || []
    const deleteErrors = []
    for (const task of existingTasks) {
      try {
        await autoTestRequest.delete(`/auto-test/scheduler/tasks/${task.task_id}`)
      } catch (e) {
        deleteErrors.push(task.task_id)
        console.warn('删除旧定时任务失败:', e)
      }
    }

    await autoTestRequest.post('/auto-test/scheduler/tasks', {
      scenario_id: scheduleForm.value.scenario_id,
      cron_expression: scheduleForm.value.cron_expression,
      env_id: scheduleForm.value.env_id,
      webhook_url: scheduleForm.value.webhook_url,
      name: scheduleForm.value.name,
      is_active: scheduleForm.value.is_active
    })

    if (deleteErrors.length > 0) {
      ElMessage.warning(`定时任务已创建，但${deleteErrors.length}个旧任务删除失败，请手动清理`)
    } else {
      ElMessage.success('定时任务设置成功')
    }
    dialogVisible.value = false
    emit('schedule-changed')
  } catch (error) {
    ElMessage.error('设置失败: ' + (error.response?.data?.detail || error.message))
  }
}

const handleDeleteSchedule = async (scenarioId) => {
  try {
    await ElMessageBox.confirm('确定要删除该场景的定时任务吗？', '删除确认', { type: 'warning' })
    const tasks = scheduleTasks.value[scenarioId] || []
    for (const task of tasks) {
      await autoTestRequest.delete(`/auto-test/scheduler/tasks/${task.task_id}`)
    }
    ElMessage.success('删除成功')
    dialogVisible.value = false
    emit('schedule-changed')
  } catch (error) {
    if (error !== 'cancel') ElMessage.error('删除失败')
  }
}

watch(() => props.visible, async (newVal) => {
  if (newVal && props.scenarioId) {
    scheduleForm.value = {
      scenario_id: props.scenarioId,
      scenario_name: props.scenarioName,
      cron_expression: props.cronExpression || '0 2 * * *',
      env_id: null,
      webhook_url: props.webhookUrl || '',
      is_active: true,
      name: props.scenarioName + ' 定时任务'
    }
    await loadScheduleTasks()
    const existingTasks = scheduleTasks.value[props.scenarioId] || []
    if (existingTasks.length > 0) {
      const existing = existingTasks[0]
      scheduleForm.value.cron_expression = existing.cron_expression || scheduleForm.value.cron_expression
      scheduleForm.value.env_id = existing.env_id || scheduleForm.value.env_id
      scheduleForm.value.webhook_url = existing.webhook_url || scheduleForm.value.webhook_url
      scheduleForm.value.is_active = existing.is_active !== undefined ? existing.is_active : true
      scheduleForm.value.name = existing.name || scheduleForm.value.name
    }
  }
})
</script>

<style scoped>
.existing-tasks {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #f0f0f0;
}

.section-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--tm-text-regular);
  margin-bottom: 8px;
}

.form-tip {
  font-size: 12px;
  color: var(--tm-text-secondary);
  margin-top: 8px;
}

.cron-help {
  font-size: 13px;
  color: var(--tm-text-regular);
  background: var(--tm-bg-page);
  padding: 12px;
  border-radius: var(--tm-radius-small);
}

.cron-help p {
  margin: 0 0 8px;
}

.cron-help ul {
  margin: 0;
  padding-left: 20px;
}

.cron-help li {
  margin: 4px 0;
}

.cron-help code {
  background: var(--tm-bg-card);
  padding: 2px 6px;
  border-radius: 3px;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  border: 1px solid var(--tm-border-light);
}
</style>
