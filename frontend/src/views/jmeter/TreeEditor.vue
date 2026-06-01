<template>
  <div class="panel tree-panel" :style="{ width: treeWidth + 'px', minWidth: treeWidth + 'px' }">
    <div class="panel-title">
      <span>📋 脚本结构</span>
      <div class="tree-toolbar">
        <el-tag size="small" type="info">{{ totalSamplers }} / {{ totalNodes }}</el-tag>
        <el-button link size="small" @click="expandAllNodes">📂 展开</el-button>
        <el-button link size="small" @click="collapseAllNodes">📁 折叠</el-button>
      </div>
    </div>
    <div class="tree-search-bar">
      <el-input v-model="treeSearchQuery" placeholder="🔍 搜索节点名称..." size="small" clearable prefix-icon="Search" />
    </div>
    <div class="tree-body">
      <div class="tree-root-label" @click="$emit('select-node', modelValue.uid)">
        <span class="root-icon">📋</span>
        <span>{{ modelValue.name }}</span>
        <el-button link size="small" @click.stop="$emit('add-root-element')" style="margin-left:auto">
          <el-icon><Plus /></el-icon> 添加线程组
        </el-button>
      </div>
      <jmeter-tree-node
        v-for="(node, idx) in filteredTreeChildren"
        :key="node.uid"
        :node="node"
        :depth="node._depth || 0"
        :selected-uid="selectedUid"
        :search-query="treeSearchQuery"
        @select="(uid) => $emit('select-node', uid)"
        @remove="(uid) => $emit('remove-node', uid)"
        @add-child="(uid, type) => $emit('add-child', uid, type)"
        @duplicate="(uid) => $emit('duplicate-node', uid)"
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
})

const emit = defineEmits(['update:modelValue', 'select-node', 'add-root-element', 'add-child', 'remove-node', 'duplicate-node'])

const treeSearchQuery = ref('')

const filteredTreeChildren = computed(() => {
  const q = (treeSearchQuery.value || '').toLowerCase().trim()
  if (!q) return props.modelValue.children
  const matches = []
  const search = (nodes, depth = 0) => {
    nodes.forEach(node => {
      if ((node.name || '').toLowerCase().includes(q)) {
        matches.push(node)
        node._depth = depth
      }
      if (node.children) search(node.children, depth + 1)
    })
  }
  search(props.modelValue.children)
  return matches
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
  transition: all .2s; color: #1e293b;
}
.tree-root-label:hover { background: linear-gradient(90deg, rgba(99,102,241,0.07), transparent); }
.root-icon { font-size: 17px; }
.tree-empty {
  padding: 32px 16px; text-align: center; font-size: 12.5px; color: #94a3b8;
  line-height: 1.7;
}
</style>
