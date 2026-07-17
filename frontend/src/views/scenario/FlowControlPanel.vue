<template>
  <div class="flow-control-panel">
    <h4>{{ panelTitle }}</h4>

    <!-- If 条件 -->
    <template v-if="stepType === 'if_condition'">
      <el-form :model="config" label-width="80px" size="small">
        <el-form-item label="字段">
          <el-input v-model="config.field" placeholder="变量名或JSONPath，如 {{token}} 或 $.data.code" />
        </el-form-item>
        <el-form-item label="操作符">
          <el-select v-model="config.operator" style="width: 100%">
            <el-option label="等于 ==" value="==" />
            <el-option label="不等于 !=" value="!=" />
            <el-option label="包含 contains" value="contains" />
            <el-option label="大于 >" value=">" />
            <el-option label="小于 <" value="<" />
            <el-option label="存在 exists" value="exists" />
            <el-option label="不存在 not_exists" value="not_exists" />
            <el-option label="为空 empty" value="empty" />
            <el-option label="不为空 not_empty" value="not_empty" />
            <el-option label="正则 regex" value="regex" />
          </el-select>
        </el-form-item>
        <el-form-item label="期望值" v-if="!['exists', 'not_exists', 'empty', 'not_empty'].includes(config.operator)">
          <el-input v-model="config.value" placeholder="期望值" />
        </el-form-item>
        <el-form-item label="满足时">
          <el-select v-model="config.then_branch" multiple filterable placeholder="选择要执行的步骤" style="width:100%">
            <el-option v-for="step in availableSteps" :key="step.id" :label="step.label" :value="step.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="不满足时">
          <el-select v-model="config.else_branch" multiple filterable placeholder="选择要执行的步骤" style="width:100%">
            <el-option v-for="step in availableSteps" :key="step.id" :label="step.label" :value="step.id" />
          </el-select>
        </el-form-item>
      </el-form>
    </template>

    <!-- For 循环 -->
    <template v-else-if="stepType === 'for_loop'">
      <el-form :model="config" label-width="80px" size="small">
        <el-form-item label="循环次数">
          <el-input-number v-model="config.count" :min="1" :max="1000" />
        </el-form-item>
        <el-form-item label="循环变量">
          <el-input v-model="config.var_name" placeholder="默认为 i" />
        </el-form-item>
        <el-form-item label="循环步骤">
          <el-select v-model="config.body" multiple filterable placeholder="选择循环执行的步骤" style="width:100%">
            <el-option v-for="step in availableSteps" :key="step.id" :label="step.label" :value="step.id" />
          </el-select>
        </el-form-item>
      </el-form>
    </template>

    <!-- ForEach 遍历 -->
    <template v-else-if="stepType === 'for_each'">
      <el-form :model="config" label-width="80px" size="small">
        <el-form-item label="集合变量">
          <el-input v-model="config.collection" placeholder="集合变量名，如 users（不含 {{ }}）" />
        </el-form-item>
        <el-form-item label="元素变量">
          <el-input v-model="config.item_var" placeholder="默认为 item" />
        </el-form-item>
        <el-form-item label="索引变量">
          <el-input v-model="config.index_var" placeholder="默认为 index" />
        </el-form-item>
        <el-form-item label="循环步骤">
          <el-select v-model="config.body" multiple filterable placeholder="选择循环执行的步骤" style="width:100%">
            <el-option v-for="step in availableSteps" :key="step.id" :label="step.label" :value="step.id" />
          </el-select>
        </el-form-item>
      </el-form>
    </template>

    <!-- 等待 -->
    <template v-else-if="stepType === 'wait'">
      <el-form :model="config" label-width="80px" size="small">
        <el-form-item label="延迟毫秒">
          <el-input-number v-model="config.duration_ms" :min="100" :max="60000" :step="500" />
        </el-form-item>
      </el-form>
    </template>

    <!-- 分组 -->
    <template v-else-if="stepType === 'group'">
      <el-form :model="config" label-width="80px" size="small">
        <el-form-item label="分组名称">
          <el-input v-model="config.name" placeholder="分组名称" />
        </el-form-item>
        <el-form-item label="包含步骤">
          <el-select v-model="config.children" multiple filterable placeholder="选择分组内步骤" style="width:100%">
            <el-option v-for="step in availableSteps" :key="step.id" :label="step.label" :value="step.id" />
          </el-select>
        </el-form-item>
      </el-form>
    </template>

    <!-- 数据库查询 -->
    <template v-else-if="stepType === 'db_query'">
      <el-form :model="config" label-width="80px" size="small">
        <el-form-item label="数据库连接">
          <el-select v-model="config.connection_id" placeholder="选择连接" style="width: 100%" @visible-change="loadConnections">
            <el-option v-for="conn in dbConnections" :key="conn.id" :label="conn.name" :value="conn.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="SQL 查询">
          <CodeEditor v-model="config.query" language="sql" :hide-run="true" style="min-height: 120px;" />
        </el-form-item>
        <el-form-item label="结果变量">
          <el-input v-model="config.extract_to" placeholder="查询结果保存到的变量名（可选）" />
        </el-form-item>
      </el-form>
    </template>

    <!-- 引用场景 -->
    <template v-else-if="stepType === 'scenario_ref'">
      <el-form :model="config" label-width="80px" size="small">
        <el-form-item label="场景">
          <el-select v-model="config.scenario_id" placeholder="选择场景" style="width: 100%" filterable @visible-change="loadScenarios">
            <el-option v-for="s in scenarios" :key="s.id" :label="s.name" :value="s.id" />
          </el-select>
        </el-form-item>
      </el-form>
    </template>

    <div style="text-align: right; margin-top: 12px;">
      <el-button size="small" type="primary" @click="handleSave">保存配置</el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import autoTestRequest from '@/utils/autoTestRequest'
import CodeEditor from '@/components/CodeEditor.vue'

const props = defineProps({
  stepType: { type: String, required: true },
  stepConfig: { type: Object, default: () => ({}) },
  availableSteps: { type: Array, default: () => [] }
})

const emit = defineEmits(['save'])

const config = ref({ ...props.stepConfig })

watch(() => props.stepConfig, (val) => {
  config.value = { ...val }
}, { deep: true })

const panelTitle = computed(() => {
  const map = {
    if_condition: 'If 条件配置',
    for_loop: 'For 循环配置',
    for_each: 'ForEach 遍历配置',
    wait: '等待配置',
    group: '分组配置',
    db_query: '数据库查询配置',
    scenario_ref: '引用场景配置',
  }
  return map[props.stepType] || '配置'
})

const dbConnections = ref([])
const scenarios = ref([])

const loadConnections = async (visible) => {
  if (!visible) return
  try {
    const res = await autoTestRequest.get('/auto-test/db-connections')
    dbConnections.value = Array.isArray(res) ? res : []
  } catch (e) {
    console.error('加载数据库连接失败:', e)
  }
}

const loadScenarios = async (visible) => {
  if (!visible) return
  try {
    const res = await autoTestRequest.get('/auto-test/scenarios')
    scenarios.value = Array.isArray(res) ? res : (res.items || [])
  } catch (e) {
    console.error('加载场景列表失败:', e)
  }
}

const handleSave = () => {
  const output = { ...config.value }
  if (['if_condition', 'for_loop', 'for_each', 'group'].includes(props.stepType)) {
    output.reference_mode = 'id'
  }
  if (props.stepType === 'if_condition') {
    // 同时保留 field 字段（前端显示用）和 condition 对象（后端使用）
    output.field = config.value.field || ''
    output.operator = config.value.operator || '=='
    output.value = config.value.value || ''
    output.condition = {
      variable: config.value.field || '',
      operator: config.value.operator || '==',
      value: config.value.value || '',
    }
  }
  emit('save', output)
}
</script>

<style scoped>
.flow-control-panel h4 {
  margin: 0 0 12px;
  color: var(--tm-text-primary);
}
</style>
