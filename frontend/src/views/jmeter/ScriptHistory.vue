<template>
  <div class="script-history">
    <el-dialog :model-value="visible" @update:model-value="$emit('update:visible', $event)" title="脚本历史" width="70%">
      <div v-if="!scriptHistory || scriptHistory.length === 0" style="text-align:center;padding:40px 0">
        <el-empty description="暂无脚本历史记录" />
      </div>
      <el-table v-else :data="scriptHistory" stripe style="width:100%" max-height="60vh">
        <el-table-column prop="name" label="脚本名称" min-width="200" show-overflow-tooltip />
        <el-table-column prop="time" label="时间" width="180" />
        <el-table-column prop="nodes" label="元素数" width="90" align="center" />
        <el-table-column label="操作" width="160" align="center">
          <template #default="{ row }">
            <el-button size="small" type="primary" @click="$emit('load-script', row)">加载</el-button>
            <el-button size="small" type="danger" @click="$emit('delete-script', row.name)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup>
defineProps({
  visible: { type: Boolean, default: false },
  scriptHistory: { type: Array, default: () => [] }
})
defineEmits(['update:visible', 'load-script', 'delete-script'])
</script>

<style scoped>
.script-history :deep(.el-dialog__body) { padding: 16px 20px; }
</style>
