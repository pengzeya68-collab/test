<template>
  <!--
    接口库：CaseList 已内置分组树侧边栏（左侧 25% + 列表 75%），
    此组件作为薄包装层保留，以维持 AutoTest.vue 的引用不变。
  -->
  <div class="interface-library">
    <CaseList
      ref="caseListRef"
      :environment-list="environmentList"
      :curl-data="curlData"
      @run="(caseData, envId) => emit('run-cases', caseData, envId)"
    />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import CaseList from './CaseList.vue'

defineProps({
  environmentList: {
    type: Array,
    default: () => []
  },
  curlData: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['run-cases'])

const caseListRef = ref(null)

// 供父组件刷新用例列表（保持向后兼容）
const refreshCaseList = () => {
  caseListRef.value?.loadCases?.()
}

defineExpose({ refreshCaseList })
</script>

<style scoped>
.interface-library {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: var(--tm-bg-page);
}
</style>
