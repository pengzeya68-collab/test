<template>
  <div class="summary-banner" v-if="scriptTree && scriptTree.length > 0">
    <div class="summary-banner-icon">{{ summaryEmoji }}</div>
    <div class="summary-banner-body">
      <div class="summary-banner-title">{{ summaryTitle }}</div>
      <div class="summary-banner-text">{{ naturalLanguageSummary }}</div>
      <div class="summary-banner-stats">
        <el-tag size="small" effect="plain">🧵 {{ totalThreads }} 线程</el-tag>
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
</template>

<script setup>
defineProps({
  scriptTree: {
    type: Array,
    default: () => []
  },
  summaryEmoji: {
    type: String,
    default: '📋'
  },
  summaryTitle: {
    type: String,
    default: '测试计划概览'
  },
  naturalLanguageSummary: {
    type: String,
    default: ''
  },
  totalThreads: {
    type: Number,
    default: 0
  },
  totalSamplers: {
    type: Number,
    default: 0
  },
  totalAssertions: {
    type: Number,
    default: 0
  },
  totalExtractors: {
    type: Number,
    default: 0
  },
  totalTimers: {
    type: Number,
    default: 0
  },
  totalListeners: {
    type: Number,
    default: 0
  }
})
</script>

<style scoped>
.summary-banner {
  background: #f0f9ff;
  border: 1px solid #bae6fd;
  border-radius: 8px;
  padding: 16px;
  display: flex;
  gap: 12px;
  align-items: flex-start;
  margin-bottom: 16px;
}

.summary-banner-icon {
  font-size: 32px;
  line-height: 1;
  flex-shrink: 0;
}

.summary-banner-body {
  flex: 1;
  min-width: 0;
}

.summary-banner-title {
  font-weight: 600;
  font-size: 14px;
  color: #0c4a6e;
  margin-bottom: 4px;
}

.summary-banner-text {
  font-size: 13px;
  color: #334155;
  line-height: 1.6;
  margin-bottom: 8px;
}

.summary-banner-stats {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.summary-banner-empty {
  background: #fefce8;
  border-color: #fde047;
}
</style>
