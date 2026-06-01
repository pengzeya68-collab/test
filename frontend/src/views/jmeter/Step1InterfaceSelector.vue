<template>
  <div class="step1-layout">
    <div class="step1-left">
      <div class="panel step1-templates">
        <div class="panel-title">📦 模板快速创建</div>
        <div class="template-grid">
          <div class="tpl-card" v-for="tpl in templates" :key="tpl.key" @click="$emit('apply-template', tpl)">
            <div class="tpl-icon">{{ tpl.icon }}</div>
            <div class="tpl-name">{{ tpl.name }}</div>
            <div class="tpl-desc">{{ tpl.desc }}</div>
          </div>
        </div>
      </div>
      <div class="step1-import-jmx">
        <div class="import-jmx-card" @click="$emit('open-import-jmx')">
          <div class="import-jmx-icon">📂</div>
          <div class="import-jmx-body">
            <div class="import-jmx-title">导入 .jmx 文件</div>
            <div class="import-jmx-desc">已有 JMeter 脚本？直接导入 .jmx 文件解析为接口</div>
          </div>
          <el-icon size="20" style="color:var(--tm-text-secondary)"><Right /></el-icon>
        </div>
      </div>
    </div>
    <div class="panel step1-import">
      <div class="panel-title">📋 从接口库导入</div>
      <div class="section-hint"><el-icon><InfoFilled /></el-icon> 勾选已有的 API 接口，点击「导入到脚本」自动创建 HTTP 请求和线程组</div>
      <div class="import-controls">
        <el-select v-model="importGroupFilter" placeholder="按分组筛选" size="default" clearable filterable style="width:240px">
          <el-option v-for="g in importGroups" :key="g.id" :label="g.name" :value="g.id" />
        </el-select>
        <el-input v-model="caseSearch" placeholder="搜索接口名称或URL..." size="default" clearable prefix-icon="Search" style="flex:1" />
      </div>
      <div class="import-case-list">
        <div v-if="allCases.length === 0" class="empty-state">
          <el-icon size="32"><FolderDelete /></el-icon>
          <p style="margin:8px 0">当前分组没有接口用例</p>
          <el-button type="primary" size="small" @click="$emit('open-interface-lib')">📝 去接口库创建</el-button>
        </div>
        <el-checkbox-group v-model="selectedImportCases" v-else>
          <div v-for="c in filteredImportCases" :key="c.id" class="import-case-item" @click="toggleCase(c.id)">
            <el-checkbox :label="c.id" @click.stop>
              <span class="case-method" :class="'m-' + (c.method||'GET').toLowerCase()">{{ c.method }}</span>
              <span class="case-name">{{ c.name }}</span>
              <span class="case-url">{{ c.url }}</span>
            </el-checkbox>
          </div>
        </el-checkbox-group>
        <div v-if="filteredImportCases.length === 0 && allCases.length > 0" class="empty-state">
          无匹配结果
        </div>
      </div>
      <div class="import-footer">
        <span class="import-count">已选 {{ selectedImportCases.length }} 个接口</span>
        <el-button type="primary" size="large" :disabled="selectedImportCases.length === 0" @click="$emit('import-selected')" style="font-weight:700">
          🚀 导入到脚本 <el-icon><Right /></el-icon>
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Right, InfoFilled, FolderDelete } from '@element-plus/icons-vue'
import autoTestRequest from '@/utils/autoTestRequest'

const router = useRouter()

const props = defineProps({
  allCases: { type: Array, default: () => [] },
  importGroups: { type: Array, default: () => [] },
  selectedImportCases: { type: Array, default: () => [] },
})

const emit = defineEmits([
  'apply-template',
  'open-import-jmx',
  'open-interface-lib',
  'import-selected',
  'update:selectedImportCases',
  'load-cases',
])

const templates = [
  { key: 'simple', name: '简单 API 验证', icon: '🌐', desc: '单接口 GET 请求 + 断言 + 结果树', tags: ['入门'] },
  { key: 'login-flow', name: '登录认证流程', icon: '🔐', desc: '登录 → 提取 Token → 带 Token 请求', tags: ['常用', '认证'] },
  { key: 'crud', name: 'CRUD 全流程', icon: '📦', desc: '增删改查四个请求按顺序执行', tags: ['完整流程'] },
  { key: 'data-driven', name: 'CSV 数据驱动', icon: '📊', desc: 'CSV 参数化多组用户名密码登录', tags: ['参数化'] },
  { key: 'jdbc', name: '数据库压测', icon: '🗄️', desc: 'JDBC 连接 + SQL 查询 + 聚合报告', tags: ['数据库'] },
]

const importGroupFilter = ref(null)
const caseSearch = ref('')
const selectedImportCases = computed({
  get: () => props.selectedImportCases,
  set: (v) => emit('update:selectedImportCases', v),
})

const filteredImportCases = computed(() => {
  if (!caseSearch.value) return props.allCases
  const kw = caseSearch.value.toLowerCase()
  return props.allCases.filter(c => c.name.toLowerCase().includes(kw) || (c.url||'').toLowerCase().includes(kw))
})

const toggleCase = (id) => {
  const idx = selectedImportCases.value.indexOf(id)
  if (idx >= 0) selectedImportCases.value.splice(idx, 1)
  else selectedImportCases.value.push(id)
}

watch(importGroupFilter, () => {
  selectedImportCases.value = []
  emit('load-cases', importGroupFilter.value)
})

defineExpose({ importGroupFilter, caseSearch })
</script>

<style scoped>
.step1-layout { display: grid; grid-template-columns: 300px 1fr; gap: 18px; padding: 18px; flex: 1; min-height: 0; overflow: hidden; }
.step1-left { display: flex; flex-direction: column; gap: 12px; overflow-y: auto; }
.step1-templates { overflow: visible; }
.step1-import-jmx { }

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

.import-jmx-card {
  display: flex; align-items: center; gap: 14px; padding: 16px 18px;
  background: linear-gradient(135deg, #eef2ff 0%, #ede9fe 50%, #fdf4ff 100%);
  border: 1.5px dashed rgba(99,102,241,0.4);
  border-radius: 12px; cursor: pointer; transition: all .3s cubic-bezier(.4,0,.2,1);
  position: relative; overflow: hidden;
}
.import-jmx-card::before {
  content: ''; position: absolute; top: 0; left: 0; right: 0; bottom: 0;
  background: radial-gradient(circle at top right, rgba(99,102,241,0.08) 0%, transparent 60%);
  opacity: 0; transition: opacity .3s;
}
.import-jmx-card:hover::before { opacity: 1; }
.import-jmx-card:hover {
  border-color: #6366f1; border-style: solid;
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(99,102,241,0.15), 0 2px 6px rgba(99,102,241,0.08);
}
.import-jmx-icon { font-size: 30px; flex-shrink: 0; filter: drop-shadow(0 2px 4px rgba(0,0,0,0.1)); }
.import-jmx-body { flex: 1; z-index: 1; }
.import-jmx-title { font-size: 14px; font-weight: 700; color: #334155; }
.import-jmx-desc { font-size: 11.5px; color: #64748b; margin-top: 3px; line-height: 1.5; }
.step1-import { display: flex; flex-direction: column; overflow: hidden; }

.template-grid { display: grid; grid-template-columns: 1fr; gap: 7px; }
.tpl-card {
  padding: 14px 16px;
  border: 1px solid rgba(148,163,184,0.15);
  border-radius: 11px; cursor: pointer; transition: all .28s cubic-bezier(.4,0,.2,1);
  background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
  display: flex; align-items: center; gap: 12px;
  position: relative; overflow: hidden;
}
.tpl-card::after {
  content: ''; position: absolute; left: 0; top: 0; bottom: 0; width: 3px;
  background: linear-gradient(180deg, #6366f1, #8b5cf6);
  border-radius: 0 3px 3px 0; opacity: 0; transition: opacity .25s;
}
.tpl-card:hover {
  border-color: rgba(99,102,241,0.35);
  background: linear-gradient(135deg, #ffffff 0%, #eef2ff 100%);
  transform: translateX(4px);
  box-shadow: 0 4px 14px rgba(99,102,241,0.1);
}
.tpl-card:hover::after { opacity: 1; }
.tpl-icon { font-size: 26px; flex-shrink: 0; filter: drop-shadow(0 2px 3px rgba(0,0,0,0.08)); }
.tpl-name { font-weight: 700; font-size: 13px; margin: 0; color: #1e293b; }
.tpl-desc { font-size: 11px; color: #94a3b8; margin-top: 2px; line-height: 1.4; }

.import-controls { display: flex; gap: 10px; margin-bottom: 14px; }
.import-case-list { flex: 1; overflow-y: auto; padding: 0 4px; }
.import-case-item { padding: 5px 8px; border-radius: 8px; cursor: pointer; transition: all .2s; }
.import-case-item:hover { background: linear-gradient(90deg, rgba(99,102,241,0.06), transparent); }
.case-method { font-size: 11px; font-weight: 800; padding: 2px 7px; border-radius: 5px; margin-right: 8px; letter-spacing: 0.02em; }
.m-get { background: linear-gradient(135deg, rgba(16,185,129,0.15), rgba(5,150,105,0.1)); color: #059669; }
.m-post { background: linear-gradient(135deg, rgba(236,72,153,0.15), rgba(219,39,119,0.1)); color: #db2777; }
.m-put { background: linear-gradient(135deg, rgba(245,158,11,0.15), rgba(217,119,6,0.1)); color: #d97706; }
.m-delete { background: linear-gradient(135deg, rgba(239,68,68,0.15), rgba(220,38,38,0.1)); color: #dc2626; }
.m-patch { background: linear-gradient(135deg, rgba(129,140,248,0.15), rgba(99,102,241,0.1)); color: #6366f1; }
.case-name { font-size: 13px; font-weight: 600; color: #334155; }
.case-url { font-size: 11px; color: #94a3b8; margin-left: 8px; }

.import-footer {
  display: flex; justify-content: space-between; align-items: center;
  padding: 14px 16px 0; border-top: 1px solid rgba(148,163,184,0.12); margin-top: 10px;
}
.import-count { font-size: 12.5px; color: #64748b; font-weight: 500; }

.section-hint {
  font-size: 11.5px; color: #64748b; margin-bottom: 10px;
  display: flex; align-items: flex-start; gap: 5px;
  line-height: 1.55; padding: 8px 10px;
  background: linear-gradient(90deg, rgba(99,102,241,0.04), transparent);
  border-radius: 7px; border-left: 3px solid rgba(99,102,241,0.25);
}
.section-hint .el-icon { font-size: 14px; flex-shrink: 0; margin-top: 1px; color: #6366f1; }

.empty-state { text-align: center; padding: 36px; color: #94a3b8; font-size: 13px; line-height: 1.6; }
</style>
