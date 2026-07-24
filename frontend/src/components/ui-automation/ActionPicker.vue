<template>
  <el-dialog v-model="visible" title="添加测试步骤" width="720px" append-to-body @opened="focusSearch">
    <el-input ref="searchRef" v-model="keyword" :prefix-icon="Search" placeholder="搜索动作，例如：点击、断言、等待" clearable />
    <div class="action-groups">
      <section v-for="group in filteredGroups" :key="group.name">
        <h3>{{ group.name }}</h3>
        <div class="action-grid">
          <button v-for="action in group.actions" :key="action.type" type="button" @click="choose(action.type)">
            <el-icon><component :is="action.icon" /></el-icon><span>{{ action.label }}</span>
          </button>
        </div>
      </section>
      <el-empty v-if="!filteredGroups.length" description="没有匹配的动作" />
    </div>
  </el-dialog>
</template>
<script setup>
import { computed, nextTick, ref } from 'vue'
import { Search } from '@element-plus/icons-vue'
import { ACTION_GROUPS } from './action-catalog'
const props = defineProps({ modelValue: Boolean })
const emit = defineEmits(['update:modelValue', 'select'])
const keyword = ref('')
const searchRef = ref()
const visible = computed({ get: () => props.modelValue, set: value => emit('update:modelValue', value) })
const filteredGroups = computed(() => {
  const query = keyword.value.trim().toLowerCase()
  if (!query) return ACTION_GROUPS
  return ACTION_GROUPS.map(group => ({ ...group, actions: group.actions.filter(action => action.label.includes(query) || action.type.includes(query)) })).filter(group => group.actions.length)
})
function choose(type) { emit('select', type); visible.value = false; keyword.value = '' }
function focusSearch() { nextTick(() => searchRef.value?.focus()) }
</script>
<style scoped>
.action-groups { max-height: 62vh; overflow: auto; padding: 4px 2px 0; }
.action-groups section { margin-top: 18px; }
.action-groups h3 { margin: 0 0 8px; color: var(--tm-text-secondary); font-size: 12px; }
.action-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; }
.action-grid button {
  height: 42px;
  border: 1px solid var(--border-subtle);
  border-radius: var(--tm-radius-small, 8px);
  background: var(--tm-bg-elevated);
  display: flex;
  align-items: center;
  gap: 9px;
  padding: 0 12px;
  color: var(--tm-text-primary);
  cursor: pointer;
  text-align: left;
}
.action-grid button:hover {
  border-color: rgba(var(--tm-color-primary-rgb), 0.45);
  background: rgba(var(--tm-color-primary-rgb), 0.1);
  color: var(--tm-color-primary);
}
.action-grid button:focus-visible {
  outline: 2px solid rgba(var(--tm-color-primary-rgb), 0.5);
  outline-offset: 1px;
}
@media (max-width: 640px) {
  .action-grid { grid-template-columns: 1fr 1fr; }
}
</style>
