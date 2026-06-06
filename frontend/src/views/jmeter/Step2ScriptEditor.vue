<template>
  <div class="step2-layout">
    <!-- 自然语言概要 Banner -->
    <div class="summary-banner" v-if="scriptTree.children.length > 0">
      <div class="summary-banner-icon">{{ summaryEmoji }}</div>
      <div class="summary-banner-body">
        <div class="summary-banner-title">{{ summaryTitle }}</div>
        <div class="summary-banner-text">{{ naturalLanguageSummary }}</div>
        <div class="summary-banner-stats">
          <el-tag size="small" effect="plain">👥 {{ totalThreads }} 线程</el-tag>
          <el-tag size="small" effect="plain">🌐 {{ totalSamplers }} 请求</el-tag>
          <el-tag v-if="totalAssertions > 0" size="small" effect="plain">✅ {{ totalAssertions }} 断言</el-tag>
          <el-tag v-if="totalExtractors > 0" size="small" effect="plain">🔍 {{ totalExtractors }} 提取器</el-tag>
          <el-tag v-if="totalTimers > 0" size="small" effect="plain">⏰ {{ totalTimers }} 定时器</el-tag>
          <el-tag v-if="totalListeners > 0" size="small" effect="plain">👁️ {{ totalListeners }} 监听器</el-tag>
        </div>
      </div>
    </div>
    <div class="summary-banner summary-banner-empty" v-else>
      <div class="summary-banner-icon">💡</div>
      <div class="summary-banner-body">
        <div class="summary-banner-text">当前脚本是空的，去「选择接口」步骤导入接口，或点击左侧「+ 添加线程组」从零开始创建</div>
      </div>
    </div>

    <!-- 压测控制面板 -->
    <BenchRunner
      ref="benchRunnerRef"
      :script-tree="scriptTree"
      :plan-name="scriptTree.name"
      :total-samplers="totalSamplers"
      :total-nodes="totalNodes"
      :total-threads="totalThreads"
      :all-samplers="allSamplers"
    />

    <!-- 两栏布局：树 + 编辑器 -->
    <div class="step2-editor-layout">
      <!-- 左：树 -->
      <TreeEditor
        v-model="scriptTree"
        :selected-uid="selectedUid"
        :total-samplers="totalSamplers"
        :total-nodes="totalNodes"
        :tree-width="treeWidth"
        @select-node="$emit('select-node', $event)"
        @add-root-element="$emit('add-root-element')"
        @add-child="(uid, type) => $emit('add-child', uid, type)"
        @remove-node="$emit('remove-node', $event)"
        @duplicate-node="$emit('duplicate-node', $event)"
      />
      <div class="drag-handle drag-handle-tree" @mousedown="onDragStart('tree', $event)" :class="{ active: draggingCol === 'tree' }"></div>

      <!-- 中：编辑器 -->
      <div class="panel editor-panel" style="flex:1;min-width:0">
        <div class="panel-title">
          <span>✏️ {{ selectedNode ? selectedNode.name : '元素编辑器' }}</span>
          <el-tag v-if="selectedNode" size="small">{{ NODE_TYPES[selectedNode.type]?.label || selectedNode.type }}</el-tag>
        </div>
        <NodeEditorPanel
          ref="nodeEditorRef"
          :selected-node="selectedNode"
          :node-types="NODE_TYPES"
          :bench-result="benchResult"
          :project-variables="projectVariables"
          :debug-loading="debugLoading"
          :saving-to-case="savingToCase"
          :ai-generating="aiGenerating"
          :ai-validating="aiValidating"
          :ai-validation-result="aiValidationResult"
          @add-var="$emit('add-var')"
          @add-header="$emit('add-header')"
          @add-child-to-current="$emit('add-child-to-current', $event)"
          @add-root-element="$emit('add-root-element')"
          @go-to-step1="$emit('go-to-step1')"
          @debug-request="$emit('debug-request', $event)"
          @save-to-case="$emit('save-to-case', $event)"
          @ai-generate-assert="$emit('ai-generate-assert', $event)"
          @ai-generate-script="$emit('ai-generate-script', $event)"
          @ai-validate-script="$emit('ai-validate-script', $event)"
          @insert-variable="$emit('insert-variable', $event)"
          @do-vrt-search="doVrtSearch"
          @reset-vrt-search="resetVrtSearch"
          @select-sample="onSelectSample"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onBeforeUnmount } from 'vue'
import BenchRunner from '@/views/jmeter/BenchRunner.vue'
import TreeEditor from '@/views/jmeter/TreeEditor.vue'
import NodeEditorPanel from '@/views/jmeter/NodeEditorPanel.vue'

const props = defineProps({
  scriptTree: { type: Object, required: true },
  selectedUid: { type: String, default: null },
  selectedNode: { type: Object, default: null },
  NODE_TYPES: { type: Object, default: () => ({}) },
  projectVariables: { type: Array, default: () => [] },
  debugLoading: { type: Boolean, default: false },
  savingToCase: { type: Boolean, default: false },
  aiGenerating: { type: Boolean, default: false },
  aiValidating: { type: Boolean, default: false },
  aiValidationResult: { type: Object, default: null },
})

const emit = defineEmits([
  'select-node',
  'add-root-element',
  'add-child',
  'remove-node',
  'duplicate-node',
  'add-var',
  'add-header',
  'add-child-to-current',
  'go-to-step1',
  'debug-request',
  'save-to-case',
  'ai-generate-assert',
  'ai-generate-script',
  'ai-validate-script',
  'insert-variable',
])

const benchRunnerRef = ref(null)
const nodeEditorRef = ref(null)

const benchResult = computed(() => benchRunnerRef.value?.benchResult)

const totalThreads = computed(() => {
  let count = 0
  const walk = (node) => {
    if (node.type === 'ThreadGroup') count += (node.props.threads || 10)
    ;(node.children || []).forEach(walk)
  }
  walk(props.scriptTree)
  return count
})

const allSamplers = computed(() => {
  const list = []
  const walk = (node) => {
    if (node.type === 'HttpSampler') {
      list.push({
        name: node.name || '',
        method: node.props?.method || 'GET',
        url: node.props?.url || node.props?.path || ''
      })
    }
    ;(node.children || []).forEach(walk)
  }
  walk(props.scriptTree)
  return list
})

const totalSamplers = computed(() => {
  let count = 0
  const walk = (node) => {
    if (node.type === 'HttpSampler') count++
    ;(node.children || []).forEach(walk)
  }
  walk(props.scriptTree)
  return count
})

const totalAssertions = computed(() => {
  let count = 0
  const walk = (node) => {
    if (['ResponseAssertion','DurationAssertion','JsonAssertion','BeanShellAssertion','JSR223Assertion','SizeAssertion','XPathAssertion','CompareAssertion','XMLAssertion'].includes(node.type)) count++
    ;(node.children || []).forEach(walk)
  }
  walk(props.scriptTree)
  return count
})

const totalExtractors = computed(() => {
  let count = 0
  const walk = (node) => {
    if (['RegexExtractor','JsonExtractor'].includes(node.type)) count++
    ;(node.children || []).forEach(walk)
  }
  walk(props.scriptTree)
  return count
})

const totalTimers = computed(() => {
  let count = 0
  const walk = (node) => {
    if (['ConstantTimer','UniformRandomTimer','GaussianRandomTimer','SyncTimer'].includes(node.type)) count++
    ;(node.children || []).forEach(walk)
  }
  walk(props.scriptTree)
  return count
})

const totalListeners = computed(() => {
  let count = 0
  const walk = (node) => {
    if (['ViewResultsTree','SummaryReport','AggregateGraph','AggregateReport','ResponseTimeGraph','InfluxDBBackendListener'].includes(node.type)) count++
    ;(node.children || []).forEach(walk)
  }
  walk(props.scriptTree)
  return count
})

const totalNodes = computed(() => {
  let count = 0
  const walk = (node) => {
    count++
    ;(node.children || []).forEach(walk)
  }
  walk(props.scriptTree)
  return count
})

const summaryEmoji = computed(() => {
  if (totalSamplers.value === 0) return '📭'
  if (totalAssertions.value === 0) return '🧪'
  return '🚀'
})

const summaryTitle = computed(() => {
  if (totalSamplers.value === 0) return '还没有添加请求'
  if (totalAssertions.value === 0) return '脚本已就绪，建议添加断言验证结果'
  return '测试脚本已配置完整，可以去第3步验证并发或导出 .jmx'
})

const naturalLanguageSummary = computed(() => {
  const tgs = props.scriptTree.children.filter(c => c.type === 'ThreadGroup')
  if (tgs.length === 0) return '还没有线程组，请添加线程组或导入接口'
  const parts = []
  for (const tg of tgs) {
    const threads = tg.props.threads || 10
    const ramp = tg.props.rampUp || 5
    const loops = tg.props.loops || 1
    const duration = tg.props.duration || 0
    const items = []
    const walk = (node) => {
      if (node.type === 'HttpSampler') {
        items.push((node.props.method || 'GET') + ' ' + (node.name || node.props.url || ''))
      }
      (node.children || []).forEach(walk)
    }
    walk(tg)
    let desc = `用 ${ramp} 秒逐步启动 ${threads} 个虚拟用户`
    if (duration > 0) {
      desc += `，持续运行 ${duration} 秒`
    } else {
      desc += `，每个用户循环执行 ${loops} 次`
    }
    if (items.length > 0) {
      desc += `，共 ${items.length} 个请求：${items.join('、')}`
    }
    const extras = []
    const countExtras = (node) => {
      if (['ResponseAssertion','DurationAssertion','JsonAssertion','BeanShellAssertion','JSR223Assertion','SizeAssertion','XPathAssertion','CompareAssertion','XMLAssertion'].includes(node.type)) { if (!extras.includes('断言')) extras.push('断言') }
      if (['RegexExtractor','JsonExtractor'].includes(node.type)) { if (!extras.includes('提取器')) extras.push('提取器') }
      if (['ConstantTimer','UniformRandomTimer','GaussianRandomTimer'].includes(node.type)) { if (!extras.includes('定时器')) extras.push('定时器') }
      if (node.type === 'SyncTimer') { if (!extras.includes('集合点')) extras.push('集合点') }
      if (node.type === 'CSVDataSet') { if (!extras.includes('CSV数据驱动')) extras.push('CSV数据驱动') }
      if (['ViewResultsTree','SummaryReport','AggregateGraph'].includes(node.type)) { if (!extras.includes('报告')) extras.push('报告') }
      (node.children || []).forEach(countExtras)
    }
    countExtras(tg)
    if (extras.length > 0) {
      desc += `（含 ${extras.join('、')}）`
    }
    parts.push(desc)
  }
  return parts.join('；')
})

const treeWidth = ref(280)
const draggingCol = ref(null)
const dragStartX = ref(0)
const dragStartW = ref(0)

const onDragStart = (col, e) => {
  draggingCol.value = col
  dragStartX.value = e.clientX
  if (col === 'tree') dragStartW.value = treeWidth.value
  document.addEventListener('mousemove', onDragMove)
  document.addEventListener('mouseup', onDragEnd)
  e.preventDefault()
}
const onDragMove = (e) => {
  if (!draggingCol.value) return
  const delta = e.clientX - dragStartX.value
  if (draggingCol.value === 'tree') {
    treeWidth.value = Math.max(180, Math.min(window.innerWidth * 0.55, dragStartW.value + delta))
  }
}
const onDragEnd = () => {
  draggingCol.value = null
  document.removeEventListener('mousemove', onDragMove)
  document.removeEventListener('mouseup', onDragEnd)
}

// 组件卸载时清理拖拽事件监听器，防止泄漏
onBeforeUnmount(() => {
  if (draggingCol.value) {
    document.removeEventListener('mousemove', onDragMove)
    document.removeEventListener('mouseup', onDragEnd)
    draggingCol.value = null
  }
})

const doVrtSearch = () => {
  if (nodeEditorRef.value) {
    nodeEditorRef.value.sampleSearchActive = nodeEditorRef.value.sampleSearchQuery
  }
}

const resetVrtSearch = () => {
  if (nodeEditorRef.value) {
    nodeEditorRef.value.sampleSearchQuery = ''
    nodeEditorRef.value.sampleSearchActive = ''
  }
}

const onSelectSample = (idx) => {
  if (nodeEditorRef.value) {
    nodeEditorRef.value.selectedSampleIdx = idx
    nodeEditorRef.value.selectedSampleTab = 'sampler'
  }
}

const resizeAllBenchCharts = () => benchRunnerRef.value?.resizeAllBenchCharts()

const startBench = () => {
  if (nodeEditorRef.value) nodeEditorRef.value.selectedSampleIdx = -1
  benchRunnerRef.value?.startBench()
}

const stopBench = () => benchRunnerRef.value?.stopBench()

defineExpose({
  benchRunnerRef,
  benchResult,
  treeWidth,
  totalThreads,
  totalSamplers,
  totalNodes,
  allSamplers,
  resizeAllBenchCharts,
  startBench,
  stopBench,
})
</script>

<style scoped>
.step2-layout {
  display: flex; flex-direction: column;
  flex: 1; min-height: 0; overflow: hidden;
}
.step2-layout > .bench-control-panel {
  margin: 0; border-radius: 0; border-left: none; border-right: none;
  flex-shrink: 0;
}
.step2-layout > .bench-control-panel.expanded {
  height: auto; flex: 1; min-height: 0;
}
.step2-editor-layout {
  display: flex; flex: 1; min-height: 0; overflow: hidden;
}
.drag-handle {
  width: 6px; flex-shrink: 0; cursor: col-resize;
  background: transparent; transition: background .2s; position: relative;
}
.drag-handle::after {
  content: ''; position: absolute; top: 50%; left: 50%;
  transform: translate(-50%, -50%); width: 2px; height: 32px;
  background: rgba(148,163,184,0.2); border-radius: 2px; transition: background .2s;
}
.drag-handle:hover, .drag-handle.active { background: rgba(99,102,241,0.06); }
.drag-handle:hover::after, .drag-handle.active::after { background: rgba(99,102,241,0.5); height: 48px; }
.editor-panel { display: flex; flex-direction: column; overflow: hidden; min-height: 0; }

.panel {
  background: linear-gradient(180deg, #ffffff 0%, #fafbff 100%);
  border: 1px solid rgba(148,163,184,0.18);
  border-radius: 14px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.03), 0 4px 16px rgba(0,0,0,0.03);
  overflow: hidden;
  display: flex; flex-direction: column;
}
.panel-title {
  display: flex; justify-content: space-between; align-items: center;
  padding: 12px 16px;
  font-weight: 700; font-size: 13px;
  background: linear-gradient(180deg, rgba(248,250,252,0.8) 0%, transparent 100%);
  border-bottom: 1px solid rgba(148,163,184,0.12);
  letter-spacing: 0.01em;
}

.summary-banner {
  display: flex; align-items: flex-start; gap: 14px;
  padding: 12px 16px; margin: 0 18px 8px;
  border-radius: 12px;
  background: linear-gradient(135deg, rgba(99,102,241,0.09) 0%, rgba(139,92,246,0.06) 40%, rgba(168,85,247,0.04) 100%);
  border: 1px solid rgba(99,102,241,0.18);
  box-shadow: 0 4px 16px rgba(99,102,241,0.06), inset 0 1px 0 rgba(255,255,255,0.5);
  position: relative; overflow: hidden;
  flex-shrink: 0;
}
.summary-banner::before {
  content: ''; position: absolute; top: -30px; right: -30px;
  width: 120px; height: 120px; border-radius: 50%;
  background: radial-gradient(circle, rgba(99,102,241,0.1) 0%, transparent 70%);
}
.summary-banner-empty {
  background: linear-gradient(135deg, rgba(241,245,249,0.9), rgba(248,250,252,0.8));
  border-color: rgba(148,163,184,0.18);
  box-shadow: none;
}
.summary-banner-empty::before { display: none; }
.summary-banner-icon { font-size: 28px; line-height: 1; flex-shrink: 0; margin-top: 2px; filter: drop-shadow(0 2px 4px rgba(0,0,0,0.08)); z-index: 1; }
.summary-banner-body { flex: 1; min-width: 0; z-index: 1; }
.summary-banner-title { font-size: 13px; font-weight: 700; color: #1e293b; margin-bottom: 3px; }
.summary-banner-text { font-size: 12.5px; line-height: 1.55; color: #475569; font-weight: 500; }
.summary-banner-empty .summary-banner-text { font-size: 12.5px; font-weight: 400; color: #64748b; }
.summary-banner-stats { display: flex; gap: 6px; flex-wrap: wrap; margin-top: 6px; }
.summary-banner-stats :deep(.el-tag) {
  font-size: 11.5px; padding: 3px 10px; border-radius: 7px;
  font-weight: 600; border: 1px solid rgba(99,102,241,0.15);
  background: rgba(255,255,255,0.7);
}
</style>
