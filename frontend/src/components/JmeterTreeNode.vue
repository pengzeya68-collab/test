<template>
  <div
    class="tree-node"
    data-testid="jmeter-tree-node"
    :data-node-uid="node.uid"
    :data-node-type="node.type"
    :class="{ selected: node.uid === selectedUid, disabled: node.enabled === false }"
  >
    <div class="node-row" data-testid="jmeter-tree-node-row" @click="$emit('select', node.uid)" :style="{ paddingLeft: depth * 18 + 4 + 'px' }" :class="{ 'search-match': isMatched }">
      <span class="node-toggle" v-if="node.children && node.children.length > 0" @click.stop="expanded = !expanded">
        {{ expanded ? '▼' : '▶' }}
      </span>
      <span class="node-toggle" v-else style="visibility:hidden">▶</span>
      <span class="node-icon">{{ typeIcon }}</span>
      <span class="node-name">{{ node.name }}</span>
      <span class="node-type-tag">{{ typeLabel }}</span>
      <div class="node-actions" @click.stop>
        <el-dropdown trigger="click" size="small">
          <el-button link size="small" data-testid="jmeter-tree-node-actions">⋯</el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <template v-if="node.type === 'TestPlan'">
                <el-dropdown-item @click="$emit('add-child', node.uid, 'ThreadGroup')">👥 添加线程组</el-dropdown-item>
                <el-dropdown-item divided @click="$emit('add-child', node.uid, 'HttpHeaderManager')">📨 HTTP 信息头管理器</el-dropdown-item>
                <el-dropdown-item @click="$emit('add-child', node.uid, 'HttpCacheManager')">💾 HTTP 缓存管理器</el-dropdown-item>
                <el-dropdown-item @click="$emit('add-child', node.uid, 'HttpAuthManager')">🔐 HTTP 授权管理器</el-dropdown-item>
                <el-dropdown-item @click="$emit('add-child', node.uid, 'Summariser')">📝 摘要报告生成器</el-dropdown-item>
                <el-dropdown-item @click="$emit('add-child', node.uid, 'RandomVariableConfig')">🎲 随机变量配置</el-dropdown-item>
              </template>
              <template v-if="node.type === 'ThreadGroup'">
                <el-dropdown-item @click="$emit('add-child', node.uid, 'HttpSampler')">🌐 添加 HTTP 请求</el-dropdown-item>
                <el-dropdown-item divided @click="$emit('add-child', node.uid, 'IfController')">🔀 如果(If)控制器</el-dropdown-item>
                <el-dropdown-item @click="$emit('add-child', node.uid, 'LoopController')">🔄 循环控制器</el-dropdown-item>
                <el-dropdown-item @click="$emit('add-child', node.uid, 'WhileController')">🔁 While 控制器</el-dropdown-item>
                <el-dropdown-item @click="$emit('add-child', node.uid, 'TransactionController')">📦 事务控制器</el-dropdown-item>
                <el-dropdown-item @click="$emit('add-child', node.uid, 'ThroughputController')">⏱️ 吞吐量控制器</el-dropdown-item>
                <el-dropdown-item @click="$emit('add-child', node.uid, 'OnceOnlyController')">1️⃣ 仅一次控制器</el-dropdown-item>
                <el-dropdown-item @click="$emit('add-child', node.uid, 'ForEachController')">🔁 ForEach 控制器</el-dropdown-item>
                <el-dropdown-item @click="$emit('add-child', node.uid, 'SwitchController')">🔀 Switch 控制器</el-dropdown-item>
                <el-dropdown-item @click="$emit('add-child', node.uid, 'RandomController')">🎲 随机控制器</el-dropdown-item>
                <el-dropdown-item @click="$emit('add-child', node.uid, 'InterleaveController')">🔃 交替控制器</el-dropdown-item>
                <el-dropdown-item @click="$emit('add-child', node.uid, 'ModuleController')">🧩 模块控制器</el-dropdown-item>
                <el-dropdown-item @click="$emit('add-child', node.uid, 'RunTimeController')">⏱️ 运行时控制器</el-dropdown-item>
                <el-dropdown-item divided @click="$emit('add-child', node.uid, 'CsvDataSource')">📄 CSV 数据源</el-dropdown-item>
                <el-dropdown-item @click="$emit('add-child', node.uid, 'RandomVariableConfig')">🎲 随机变量配置</el-dropdown-item>
                <el-dropdown-item @click="$emit('add-child', node.uid, 'JDBCSampler')">🗄️ JDBC 请求</el-dropdown-item>
                <el-dropdown-item divided @click="$emit('add-child', node.uid, 'HTTPRequestDefaults')">🎯 HTTP 请求默认值</el-dropdown-item>
                <el-dropdown-item @click="$emit('add-child', node.uid, 'HttpHeaderManager')">📨 HTTP 信息头管理器</el-dropdown-item>
                <el-dropdown-item @click="$emit('add-child', node.uid, 'HTTPCookieManager')">🍪 HTTP Cookie 管理器</el-dropdown-item>
                <el-dropdown-item @click="$emit('add-child', node.uid, 'HttpCacheManager')">💾 HTTP 缓存管理器</el-dropdown-item>
                <el-dropdown-item @click="$emit('add-child', node.uid, 'HttpAuthManager')">🔐 HTTP 授权管理器</el-dropdown-item>
                <el-dropdown-item @click="$emit('add-child', node.uid, 'Summariser')">📝 摘要报告生成器</el-dropdown-item>
              </template>
              <template v-if="node.type === 'HttpSampler'">
                <el-dropdown-item @click="$emit('add-child', node.uid, 'ResponseAssertion')">✅ 响应断言</el-dropdown-item>
                <el-dropdown-item @click="$emit('add-child', node.uid, 'DurationAssertion')">⏱️ 持续时间断言</el-dropdown-item>
                <el-dropdown-item @click="$emit('add-child', node.uid, 'JSONPathAssertion')">📋 JSON 路径断言</el-dropdown-item>
                <el-dropdown-item @click="$emit('add-child', node.uid, 'BeanShellAssertion')">💻 BeanShell 断言</el-dropdown-item>
                <el-dropdown-item @click="$emit('add-child', node.uid, 'JSR223Assertion')">🔥 JSR223 断言</el-dropdown-item>
                <el-dropdown-item @click="$emit('add-child', node.uid, 'SizeAssertion')">📏 响应大小断言</el-dropdown-item>
                <el-dropdown-item @click="$emit('add-child', node.uid, 'XPathAssertion')">🗂️ XPath 断言</el-dropdown-item>
                <el-dropdown-item @click="$emit('add-child', node.uid, 'CompareAssertion')">⚖️ 比较断言</el-dropdown-item>
                <el-dropdown-item @click="$emit('add-child', node.uid, 'XMLAssertion')">📜 XML 断言</el-dropdown-item>
                <el-dropdown-item divided @click="$emit('add-child', node.uid, 'RegexExtractor')">🔍 正则提取器</el-dropdown-item>
                <el-dropdown-item @click="$emit('add-child', node.uid, 'JSONExtractor')">📤 JSON 提取器</el-dropdown-item>
                <el-dropdown-item @click="$emit('add-child', node.uid, 'BoundaryExtractor')">🚧 边界提取器</el-dropdown-item>
                <el-dropdown-item @click="$emit('add-child', node.uid, 'CSSSelectorExtractor')">🎨 CSS 选择器提取器</el-dropdown-item>
                <el-dropdown-item @click="$emit('add-child', node.uid, 'XPathExtractor')">🗂️ XPath 提取器</el-dropdown-item>
                <el-dropdown-item divided @click="$emit('add-child', node.uid, 'ConstantTimer')">⏰ 固定定时器</el-dropdown-item>
                <el-dropdown-item @click="$emit('add-child', node.uid, 'UniformRandomTimer')">🎲 均匀随机定时器</el-dropdown-item>
                <el-dropdown-item @click="$emit('add-child', node.uid, 'GaussianRandomTimer')">📊 高斯随机定时器</el-dropdown-item>
                <el-dropdown-item @click="$emit('add-child', node.uid, 'SynchronizingTimer')">🔄 同步定时器(集合点)</el-dropdown-item>
                <el-dropdown-item @click="$emit('add-child', node.uid, 'ConstantThroughputTimer')">📈 恒定吞吐量定时器</el-dropdown-item>
                <el-dropdown-item @click="$emit('add-child', node.uid, 'PoissonRandomTimer')">📊 泊松随机定时器</el-dropdown-item>
                <el-dropdown-item divided @click="$emit('add-child', node.uid, 'BeanShellPreProcessor')">⚙️ BeanShell 前置处理</el-dropdown-item>
                <el-dropdown-item @click="$emit('add-child', node.uid, 'BeanShellPostProcessor')">⚙️ BeanShell 后置处理</el-dropdown-item>
                <el-dropdown-item @click="$emit('add-child', node.uid, 'JSR223PreProcessor')">🔥 JSR223 前置处理</el-dropdown-item>
                <el-dropdown-item @click="$emit('add-child', node.uid, 'JSR223PostProcessor')">🔥 JSR223 后置处理</el-dropdown-item>
              </template>
              <template v-if="node.type === 'IfController' || node.type === 'LoopController' || node.type === 'WhileController' || node.type === 'TransactionController' || node.type === 'ThroughputController' || node.type === 'OnceOnlyController' || node.type === 'ModuleController' || node.type === 'RunTimeController'">
                <el-dropdown-item @click="$emit('add-child', node.uid, 'HttpSampler')">🌐 HTTP 请求</el-dropdown-item>
                <el-dropdown-item @click="$emit('add-child', node.uid, 'IfController')">🔀 如果控制器</el-dropdown-item>
                <el-dropdown-item @click="$emit('add-child', node.uid, 'LoopController')">🔄 循环控制器</el-dropdown-item>
              </template>
              <template v-if="node.type === 'TestPlan' || node.type === 'ThreadGroup'">
                <el-dropdown-item @click="$emit('add-child', node.uid, 'JDBCConnection')">🗄️ JDBC 数据库连接</el-dropdown-item>
                <el-dropdown-item @click="$emit('add-child', node.uid, 'InfluxDBBackendListener')">📡 InfluxDB 后端监听器</el-dropdown-item>
                <el-dropdown-item divided @click="$emit('add-child', node.uid, 'ViewResultsTree')">👁️ 查看结果树</el-dropdown-item>
                <el-dropdown-item @click="$emit('add-child', node.uid, 'SummaryReport')">📈 聚合报告</el-dropdown-item>
                <el-dropdown-item @click="$emit('add-child', node.uid, 'AggregateGraph')">📉 聚合图表</el-dropdown-item>
                <el-dropdown-item @click="$emit('add-child', node.uid, 'AggregateReport')">📊 聚合报告(高级)</el-dropdown-item>
                <el-dropdown-item @click="$emit('add-child', node.uid, 'ResponseTimeGraph')">📉 响应时间图</el-dropdown-item>
                <el-dropdown-item divided v-if="node.type === 'ThreadGroup'" @click="$emit('add-child', node.uid, 'UserParameters')">👤 用户参数(多账号)</el-dropdown-item>
                <el-dropdown-item v-if="node.type === 'ThreadGroup'" @click="$emit('add-child', node.uid, 'DebugSampler')">🐛 调试采样器</el-dropdown-item>
              </template>
              <el-dropdown-item divided @click="$emit('cut', node.uid)">✂️ 剪切</el-dropdown-item>
              <el-dropdown-item @click="$emit('copy', node.uid)">📋 复制到剪贴板</el-dropdown-item>
              <el-dropdown-item @click="$emit('paste', node.uid)" :disabled="!clipboardNode">📎 粘贴</el-dropdown-item>
              <el-dropdown-item @click="$emit('duplicate', node.uid)">📑 原地副本</el-dropdown-item>
              <el-dropdown-item divided @click="$emit('move-to', node.uid)">📤 移动到...</el-dropdown-item>
              <el-dropdown-item @click="$emit('toggle-enabled', node.uid)">
                {{ node.enabled === false ? '✅ 启用' : '🚫 禁用' }}
              </el-dropdown-item>
              <el-dropdown-item divided @click="$emit('remove', node.uid)" style="color:#F87171">🗑️ 删除</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>
    <draggable
      v-model="node.children"
      :group="{ name: 'jmeter-tree', pull: true, put: checkPut }"
      :item-key="(c) => c.uid"
      ghost-class="drag-ghost"
      handle=".node-row"
      :force-fallback="true"
      fallback-class="drag-fallback"
      @change="onDragChange"
      v-if="expanded && node.children && node.children.length > 0"
    >
      <template #item="{ element: child }">
        <jmeter-tree-node
          :node="child"
          :depth="depth + 1"
          :selected-uid="selectedUid"
          :clipboard-node="clipboardNode"
          :search-query="searchQuery"
          @select="$emit('select', $event)"
          @remove="(uid) => $emit('remove', uid)"
          @add-child="$emit('add-child', $event[0], $event[1])"
          @duplicate="$emit('duplicate', $event)"
          @cut="$emit('cut', $event)"
          @copy="$emit('copy', $event)"
          @paste="$emit('paste', $event)"
          @move-to="$emit('move-to', $event)"
          @toggle-enabled="$emit('toggle-enabled', $event)"
          @move-node="(uid, parentUid, idx) => $emit('move-node', uid, parentUid, idx)"
          @tree-changed="$emit('tree-changed', $event)"
        />
      </template>
    </draggable>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, watch } from 'vue'
import draggable from 'vuedraggable'
import { ElMessage } from 'element-plus'
import {
  NODE_TYPES,
  nodeTypeInfo,
  resolveType,
  isValidParentChild,
  reassignUids,
} from '../views/jmeter/shared/nodeTypes'

const props = defineProps({
  node: Object,
  depth: Number,
  selectedUid: String,
  searchQuery: String,
  clipboardNode: { type: Object, default: null },
})
const emit = defineEmits([
  'select', 'remove', 'add-child', 'duplicate',
  'cut', 'copy', 'paste', 'move-to', 'toggle-enabled',
  'move-node', 'tree-changed',
])

// 展开/折叠状态(与 node._expanded 双向同步,便于 TreeEditor 批量控制)
const expanded = ref(props.node._expanded !== undefined ? props.node._expanded : true)
watch(expanded, (newVal) => { props.node._expanded = newVal })
watch(() => props.node._expanded, (newVal) => {
  if (newVal !== undefined && newVal !== expanded.value) expanded.value = newVal
})

// 节点类型信息(用于显示图标和标签,自动解析别名)
const typeInfo = computed(() => nodeTypeInfo(props.node.type) || {})
const typeLabel = computed(() => typeInfo.value.label || props.node.type)
const typeIcon = computed(() => typeInfo.value.icon || '📌')

// 搜索匹配高亮(支持 TreeEditor 设置的 _matched 标记 或 searchQuery 直接匹配)
const isMatched = computed(() => {
  if (props.node._matched === true) return true
  const q = (props.searchQuery || '').toLowerCase().trim()
  if (!q) return false
  return (props.node.name || '').toLowerCase().includes(q)
})

// 拖拽放置校验:返回 true 允许放置,false 拒绝
const checkPut = (to, from, item) => {
  // 获取目标父节点类型(当前节点)
  const targetType = props.node.type
  // 获取被拖拽节点类型(优先从 element 取)
  let draggedType = null
  if (item) {
    if (item.type) {
      draggedType = item.type
    } else if (item.__vueComponent?.props?.node?.value?.type) {
      draggedType = item.__vueComponent.props.node.value.type
    } else if (item.element?.type) {
      draggedType = item.element.type
    }
  }
  if (!draggedType) return true // 拿不到类型时不阻断
  return isValidParentChild(targetType, draggedType)
}

// 拖拽变更处理
const onDragChange = (evt) => {
  // evt.moved: 同级移动; evt.added: 跨级添加; evt.removed: 跨级移除
  if (evt.added) {
    const movedNode = evt.added.element
    // 跨父节点拖入:重新分配 UID 避免冲突
    reassignUids(movedNode)
    // 通知父组件更新状态(选中等)
    emit('move-node', movedNode.uid, props.node.uid, evt.added.newIndex)
  }
  // 任何变更都触发持久化
  emit('tree-changed')
  // 触发 reactivity
  nextTick(() => {})
}
</script>

<style scoped>
.tree-node { font-size: 12px; user-select: none; }
.node-row { display: flex; align-items: center; gap: 3px; padding: 5px 8px; border-radius: 4px; cursor: grab; transition: background .1s; }
.node-row:hover { background: rgba(255,255,255,0.04); }
.node-row:active { cursor: grabbing; }
.tree-node.selected > .node-row { background: rgba(64,158,255,0.12); color: #60a5fa; }
.tree-node.disabled > .node-row { opacity: 0.45; text-decoration: line-through; }
.node-row.search-match { background: rgba(250,204,21,0.15); border-left: 3px solid #f59e0b; }
.tree-node.selected > .node-row.search-match { background: rgba(64,158,255,0.15); border-left-color: #409eff; }
.node-toggle { font-size: 8px; width: 12px; color: var(--tm-text-secondary); cursor: pointer; }
.node-icon { font-size: 13px; flex-shrink: 0; }
.node-name { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: 12px; }
.node-type-tag { font-size: 10px; color: var(--tm-text-secondary); background: rgba(255,255,255,0.05); padding: 0 4px; border-radius: 2px; }
.node-actions { flex-shrink: 0; display: none; }
.node-row:hover .node-actions { display: block; }
.drag-ghost { opacity: 0.4; background: rgba(64,158,255,0.1); border: 1px dashed var(--tm-color-primary); border-radius: 4px; }
.drag-fallback { background: rgba(64,158,255,0.12); }
</style>
