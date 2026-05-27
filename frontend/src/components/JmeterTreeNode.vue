<template>
  <div class="tree-node" :class="{ selected: node.uid === selectedUid }">
    <div class="node-row" @click="$emit('select', node.uid)" :style="{ paddingLeft: depth * 18 + 4 + 'px' }" :class="{ 'search-match': isMatched }">
      <span class="node-toggle" v-if="node.children && node.children.length > 0" @click.stop="expanded = !expanded">
        {{ expanded ? '▼' : '▶' }}
      </span>
      <span class="node-toggle" v-else style="visibility:hidden">▶</span>
      <span class="node-icon">{{ NODE_TYPES[node.type]?.icon || '📌' }}</span>
      <span class="node-name">{{ node.name }}</span>
      <span class="node-type-tag">{{ NODE_TYPES[node.type]?.label || node.type }}</span>
      <div class="node-actions" @click.stop>
        <el-dropdown trigger="click" size="small">
          <el-button link size="small">⋯</el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <template v-if="node.type === 'TestPlan'">
                <el-dropdown-item @click="$emit('add-child', node.uid, 'ThreadGroup')">👥 添加线程组</el-dropdown-item>
                <el-dropdown-item divided @click="$emit('add-child', node.uid, 'HTTPHeaderManager')">📨 HTTP 信息头管理器</el-dropdown-item>
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
                <el-dropdown-item divided @click="$emit('add-child', node.uid, 'CSVDataSet')">📄 CSV 数据源</el-dropdown-item>
                <el-dropdown-item @click="$emit('add-child', node.uid, 'JDBCSampler')">🗄️ JDBC 请求</el-dropdown-item>
                <el-dropdown-item divided @click="$emit('add-child', node.uid, 'HTTPRequestDefaults')">🎯 HTTP 请求默认值</el-dropdown-item>
                <el-dropdown-item @click="$emit('add-child', node.uid, 'HTTPHeaderManager')">📨 HTTP 信息头管理器</el-dropdown-item>
                <el-dropdown-item @click="$emit('add-child', node.uid, 'HTTPCookieManager')">🍪 HTTP Cookie 管理器</el-dropdown-item>
              </template>
              <template v-if="node.type === 'HttpSampler'">
                <el-dropdown-item @click="$emit('add-child', node.uid, 'ResponseAssertion')">✅ 响应断言</el-dropdown-item>
                <el-dropdown-item @click="$emit('add-child', node.uid, 'DurationAssertion')">⏱️ 持续时间断言</el-dropdown-item>
                <el-dropdown-item @click="$emit('add-child', node.uid, 'JsonAssertion')">📋 JSON 断言</el-dropdown-item>
                <el-dropdown-item @click="$emit('add-child', node.uid, 'BeanShellAssertion')">💻 BeanShell 断言</el-dropdown-item>
                <el-dropdown-item @click="$emit('add-child', node.uid, 'JSR223Assertion')">🔥 JSR223 断言</el-dropdown-item>
                <el-dropdown-item @click="$emit('add-child', node.uid, 'SizeAssertion')">📏 响应大小断言</el-dropdown-item>
                <el-dropdown-item @click="$emit('add-child', node.uid, 'XPathAssertion')">🗂️ XPath 断言</el-dropdown-item>
                <el-dropdown-item @click="$emit('add-child', node.uid, 'CompareAssertion')">⚖️ 比较断言</el-dropdown-item>
                <el-dropdown-item @click="$emit('add-child', node.uid, 'XMLAssertion')">📜 XML 断言</el-dropdown-item>
                <el-dropdown-item divided @click="$emit('add-child', node.uid, 'RegexExtractor')">🔍 正则提取器</el-dropdown-item>
                <el-dropdown-item @click="$emit('add-child', node.uid, 'JsonExtractor')">📤 JSON 提取器</el-dropdown-item>
                <el-dropdown-item divided @click="$emit('add-child', node.uid, 'ConstantTimer')">⏰ 固定定时器</el-dropdown-item>
                <el-dropdown-item @click="$emit('add-child', node.uid, 'UniformRandomTimer')">🎲 均匀随机定时器</el-dropdown-item>
                <el-dropdown-item @click="$emit('add-child', node.uid, 'GaussianRandomTimer')">📊 高斯随机定时器</el-dropdown-item>
                <el-dropdown-item @click="$emit('add-child', node.uid, 'SyncTimer')">🔄 同步定时器(集合点)</el-dropdown-item>
                <el-dropdown-item divided @click="$emit('add-child', node.uid, 'BeanShellPreProcessor')">⚙️ BeanShell 前置处理</el-dropdown-item>
                <el-dropdown-item @click="$emit('add-child', node.uid, 'BeanShellPostProcessor')">⚙️ BeanShell 后置处理</el-dropdown-item>
                <el-dropdown-item @click="$emit('add-child', node.uid, 'JSR223PreProcessor')">🔥 JSR223 前置处理</el-dropdown-item>
                <el-dropdown-item @click="$emit('add-child', node.uid, 'JSR223PostProcessor')">🔥 JSR223 后置处理</el-dropdown-item>
              </template>
              <template v-if="node.type === 'IfController' || node.type === 'LoopController' || node.type === 'WhileController' || node.type === 'TransactionController' || node.type === 'ThroughputController' || node.type === 'OnceOnlyController'">
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
              <el-dropdown-item divided @click="$emit('duplicate', node.uid)">📋 复制</el-dropdown-item>
              <el-dropdown-item @click="$emit('remove', node.uid)" style="color:#F87171">🗑️ 删除</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>
    <draggable
      v-model="node.children"
      :group="{ name: 'jmeter-tree', pull: false, put: true }"
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
          @select="$emit('select', $event)"
          @remove="(uid) => $emit('remove', uid)"
          @add-child="$emit('add-child', $event[0], $event[1])"
          @duplicate="$emit('duplicate', $event)"
        />
      </template>
    </draggable>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import draggable from 'vuedraggable'

const props = defineProps({ node: Object, depth: Number, selectedUid: String, searchQuery: String })
const emit = defineEmits(['select', 'remove', 'add-child', 'duplicate'])

const expanded = ref(props.node._expanded !== undefined ? props.node._expanded : true)

const isMatched = computed(() => {
  const q = (props.searchQuery || '').toLowerCase().trim()
  if (!q) return false
  return (props.node.name || '').toLowerCase().includes(q)
})

const onDragChange = () => {
  // 触发 reactivity
}

const NODE_TYPES = {
  TestPlan: { label: '测试计划', icon: '📋' },
  ThreadGroup: { label: '线程组', icon: '👥' },
  HttpSampler: { label: 'HTTP 请求', icon: '🌐' },
  ResponseAssertion: { label: '响应断言', icon: '✅' },
  DurationAssertion: { label: '持续时间断言', icon: '⏱️' },
  JsonAssertion: { label: 'JSON 断言', icon: '📋' },
  RegexExtractor: { label: '正则提取器', icon: '🔍' },
  JsonExtractor: { label: 'JSON 提取器', icon: '📤' },
  ConstantTimer: { label: '固定定时器', icon: '⏰' },
  UniformRandomTimer: { label: '均匀随机定时器', icon: '🎲' },
  GaussianRandomTimer: { label: '高斯随机定时器', icon: '📊' },
  SyncTimer: { label: '同步定时器', icon: '🔄' },
  CSVDataSet: { label: 'CSV 数据源', icon: '📄' },
  BeanShellPreProcessor: { label: 'BeanShell 前置', icon: '⚙️' },
  BeanShellPostProcessor: { label: 'BeanShell 后置', icon: '⚙️' },
  JDBCConnection: { label: 'JDBC 连接', icon: '🗄️' },
  JDBCSampler: { label: 'JDBC 请求', icon: '🗄️' },
  ViewResultsTree: { label: '查看结果树', icon: '👁️' },
  SummaryReport: { label: '聚合报告', icon: '📈' },
  AggregateGraph: { label: '聚合图表', icon: '📉' },
}
</script>

<style scoped>
.tree-node { font-size: 12px; user-select: none; }
.node-row { display: flex; align-items: center; gap: 3px; padding: 5px 8px; border-radius: 4px; cursor: grab; transition: background .1s; }
.node-row:hover { background: rgba(255,255,255,0.04); }
.node-row:active { cursor: grabbing; }
.tree-node.selected > .node-row { background: rgba(64,158,255,0.12); color: #60a5fa; }
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
