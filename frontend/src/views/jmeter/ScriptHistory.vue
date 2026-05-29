<template>
  <el-collapse-transition>
    <div v-if="visible" class="script-history-panel">
      <div class="shp-header">
        <span>📂 脚本历史 ({{ scriptHistory.length }})</span>
        <div>
          <el-button size="small" type="primary" @click="$emit('create-new')">
            <el-icon><Plus /></el-icon> 新建脚本
          </el-button>
          <el-button size="small" @click="clearAllHistory" v-if="scriptHistory.length > 0">
            清空全部
          </el-button>
        </div>
      </div>
      <div class="shp-list" v-if="scriptHistory.length > 0">
        <div v-for="(h, hi) in scriptHistory" :key="hi" class="shp-item" @click="$emit('load-script', h)">
          <div class="shp-item-main">
            <span class="shp-name">{{ h.name }}</span>
            <span class="shp-time">{{ h.time }}</span>
          </div>
          <div class="shp-item-actions">
            <el-tag size="small" type="info">{{ h.tree?.children?.length || 0 }} 线程组</el-tag>
            <el-button link size="small" type="danger" @click.stop="deleteScript(h.name)">删除</el-button>
          </div>
        </div>
      </div>
      <div v-else class="shp-empty">
        <p>暂无历史脚本</p>
        <p style="font-size:12px;color:var(--tm-text-secondary)">脚本会自动保存，切换页面也不会丢失</p>
      </div>
    </div>
  </el-collapse-transition>
</template>

<script setup>
import { ref, watch } from 'vue'
import { Plus } from '@element-plus/icons-vue'

const STORAGE_KEY = 'jmeter_scripts'

const props = defineProps({
  visible: { type: Boolean, default: false },
  scriptHistory: { type: Array, default: () => [] },
})

const emit = defineEmits(['load-script', 'create-new', 'update:scriptHistory'])

const loadScriptsList = () => {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? JSON.parse(raw) : []
  } catch { return [] }
}

const saveScriptsList = (list) => {
  try { localStorage.setItem(STORAGE_KEY, JSON.stringify(list)) } catch {}
}

const deleteScript = (name) => {
  const list = loadScriptsList().filter(s => s.name !== name)
  saveScriptsList(list)
  emit('update:scriptHistory', list)
}

const clearAllHistory = () => {
  saveScriptsList([])
  localStorage.removeItem('jmeter_current_script')
  emit('update:scriptHistory', [])
}
</script>

<style scoped>
.script-history-panel {
  margin: 8px 20px;
  background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
  border: 1px solid rgba(148,163,184,0.18);
  border-radius: 14px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.03), 0 4px 16px rgba(0,0,0,0.03);
  overflow: hidden;
}
.shp-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  font-weight: 700;
  font-size: 14px;
  border-bottom: 1px solid #e5e7eb;
}
.shp-list {
  max-height: 320px;
  overflow-y: auto;
}
.shp-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 16px;
  cursor: pointer;
  transition: background 0.15s;
  border-bottom: 1px solid #f3f4f6;
}
.shp-item:hover { background: #f0f4ff; }
.shp-item-main { display: flex; align-items: center; gap: 12px; }
.shp-name { font-weight: 600; font-size: 13px; }
.shp-time { font-size: 11px; color: var(--tm-text-secondary); }
.shp-item-actions { display: flex; align-items: center; gap: 8px; }
.shp-empty {
  text-align: center;
  padding: 32px 16px;
  color: var(--tm-text-secondary);
  font-size: 13px;
}
</style>
