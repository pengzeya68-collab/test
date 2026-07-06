<template>
  <div class="panel tree-panel" data-testid="jmeter-tree-panel" :style="{ width: treeWidth + 'px', minWidth: treeWidth + 'px' }">
    <div class="panel-title">
      <span>📋 脚本结构</span>
      <div class="tree-toolbar">
        <el-tag size="small" type="info">{{ totalSamplers }} / {{ totalNodes }}</el-tag>
        <el-button link size="small" @click="expandAllNodes">📂 展开</el-button>
        <el-button link size="small" @click="collapseAllNodes">📁 折叠</el-button>
      </div>
    </div>
    <div class="tree-search-bar">
      <el-input v-model="treeSearchQuery" data-testid="jmeter-tree-search-input" placeholder="🔍 搜索节点名称..." size="small" clearable prefix-icon="Search" />
    </div>
    <div class="tree-body">
      <div class="tree-root-label" data-testid="jmeter-tree-root-node" @click="$emit('select-node', modelValue.uid)">
        <span class="root-icon">📋</span>
        <span>{{ modelValue.name }}</span>
        <el-button link size="small" data-testid="jmeter-tree-add-threadgroup-button" @click.stop="$emit('add-root-element')" style="margin-left:auto">
          <el-icon><Plus /></el-icon> 添加线程组
        </el-button>
      </div>
      <jmeter-tree-node
        v-for="(node, idx) in filteredTreeChildren"
        :key="node.uid"
        :node="node"
        :depth="0"
        :selected-uid="selectedUid"
        :search-query="treeSearchQuery"
        :clipboard-node="clipboardNode"
        @select="(uid) => $emit('select-node', uid)"
        @remove="(uid) => $emit('remove-node', uid)"
        @add-child="(uid, type) => $emit('add-child', uid, type)"
        @duplicate="(uid) => $emit('duplicate-node', uid)"
        @cut="(uid) => $emit('cut-node', uid)"
        @copy="(uid) => $emit('copy-node', uid)"
        @paste="(uid) => $emit('paste-node', uid)"
        @move-to="(uid) => $emit('move-to', uid)"
        @toggle-enabled="(uid) => $emit('toggle-enabled', uid)"
        @move-node="(movedUid, parentUid, idx) => $emit('move-node', movedUid, parentUid, idx)"
        @tree-changed="() => $emit('tree-changed')"
      />
      <div v-if="modelValue.children.length === 0" class="tree-empty">
        还没有线程组，点击上方「添加线程组」或返回第1步导入接口
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { Plus } from '@element-plus/icons-vue'
import JmeterTreeNode from '@/components/JmeterTreeNode.vue'

const props = defineProps({
  modelValue: { type: Object, required: true },
  selectedUid: { type: String, default: null },
  totalSamplers: { type: Number, default: 0 },
  totalNodes: { type: Number, default: 0 },
  treeWidth: { type: Number, default: 280 },
  clipboardNode: { type: Object, default: null },
})

const emit = defineEmits([
  'update:modelValue', 'select-node', 'add-root-element', 'add-child',
  'remove-node', 'duplicate-node',
  'cut-node', 'copy-node', 'paste-node', 'move-to', 'toggle-enabled',
  'move-node', 'tree-changed',
])

const treeSearchQuery = ref('')

// 搜索时保留树结构:仅标记匹配节点(_matched=true),由 JmeterTreeNode 高亮显示
// 当有搜索词时,自动展开所有节点(便于查看匹配项的层级归属)
const filteredTreeChildren = computed(() => {
  const q = (treeSearchQuery.value || '').toLowerCase().trim()
  if (!q) {
    // 清空搜索时清除所有 _matched 标记
    const clearMatched = (nodes) => {
      nodes.forEach(n => {
        n._matched = false
        if (n.children) clearMatched(n.children)
      })
    }
    clearMatched(props.modelValue.children || [])
    return props.modelValue.children
  }
  // 标记匹配项,但不改变树结构
  const markMatches = (nodes) => {
    nodes.forEach(n => {
      n._matched = (n.name || '').toLowerCase().includes(q)
      // 搜索时自动展开节点,便于查看匹配项的层级
      n._expanded = true
      if (n.children) markMatches(n.children)
    })
  }
  markMatches(props.modelValue.children || [])
  return props.modelValue.children
})

const expandAllNodes = () => {
  const setExpanded = (node) => { node._expanded = true; (node.children || []).forEach(setExpanded) }
  setExpanded(props.modelValue)
}

const collapseAllNodes = () => {
  const setCollapsed = (node) => { node._expanded = false; (node.children || []).forEach(setCollapsed) }
  setCollapsed(props.modelValue)
}
</script>

<style scoped>
.tree-panel { display: flex; flex-direction: column; overflow: hidden; min-height: 0; border-right: 1px solid rgba(148,163,184,0.1); }
.tree-toolbar { display: flex; align-items: center; gap: 6px; margin-left: auto; }
.tree-search-bar { padding: 6px 10px 4px; }
.tree-search-bar :deep(.el-input__wrapper) { border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.06); }
.tree-body {
  flex: 1; overflow-y: auto; padding: 6px;
  scrollbar-width: thin; scrollbar-color: rgba(148,163,184,0.2) transparent;
}
.tree-body::-webkit-scrollbar { width: 5px; }
.tree-body::-webkit-scrollbar-thumb { background: rgba(148,163,184,0.25); border-radius: 3px; }
.tree-root-label {
  display: flex; align-items: center; gap: 8px; padding: 10px 12px;
  border-radius: 9px; font-weight: 700; font-size: 13px; cursor: pointer;
  transition: all .2s; color: var(--tm-text-primary);
}
.tree-root-label:hover { background: linear-gradient(90deg, rgba(99,102,241,0.07), transparent); }
.root-icon { font-size: 17px; }
.tree-empty {
  padding: 32px 16px; text-align: center; font-size: 12.5px; color: var(--tm-text-secondary);
  line-height: 1.7;
}
</style>
