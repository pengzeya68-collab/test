<template>
  <div class="upgrade-page">
    <header class="page-header">
      <div>
        <h1>流程编排</h1>
        <p>可视化拖拽节点、连线与保存。支持场景流程图编辑。</p>
      </div>
      <div class="actions">
        <el-input-number v-model="scenarioId" :min="1" />
        <el-button @click="load">加载</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </div>
    </header>

    <el-row :gutter="16">
      <el-col :span="5">
        <el-card shadow="never" class="palette-card">
          <template #header>节点库</template>
          <div class="palette">
            <button
              v-for="item in palette"
              :key="item.type"
              type="button"
              class="palette-item"
              draggable="true"
              @dragstart="onPaletteDragStart($event, item)"
            >
              <strong>{{ item.label }}</strong>
              <span>{{ item.type }}</span>
            </button>
          </div>
          <el-divider />
          <el-button size="small" @click="addNode('ui', 'UI 步骤')">+ UI 节点</el-button>
          <el-button size="small" @click="addNode('api', 'API 步骤')">+ API 节点</el-button>
          <el-button size="small" type="danger" plain :disabled="!selectedNode" @click="removeSelected">删除选中</el-button>
          <el-divider />
          <div class="muted">version {{ version }} · 节点 {{ nodes.length }} · 边 {{ edges.length }}</div>
          <el-button class="mt-8" size="small" @click="showJson = !showJson">{{ showJson ? '隐藏' : '显示' }} JSON</el-button>
        </el-card>
      </el-col>

      <el-col :span="14">
        <el-card shadow="never" class="canvas-card">
          <template #header>
            <div class="panel-title">
              <span>画布</span>
              <div class="actions">
                <el-tag size="small" type="info">拖节点移动 · 点「连线」后选目标</el-tag>
                <el-button size="small" :disabled="!linkSource" @click="cancelLink">取消连线</el-button>
              </div>
            </div>
          </template>
          <div
            ref="canvasEl"
            class="flow-canvas"
            @dragover.prevent
            @drop="onCanvasDrop"
            @click="onCanvasClick"
          >
            <svg class="edges-layer" :width="canvasSize.w" :height="canvasSize.h">
              <defs>
                <marker id="arrow" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto" markerUnits="strokeWidth">
                  <path d="M0,0 L6,3 L0,6 Z" fill="#64748b" />
                </marker>
              </defs>
              <path
                v-for="edge in edgePaths"
                :key="edge.id"
                :d="edge.d"
                class="edge-path"
                :class="{ active: selectedEdgeId === edge.id }"
                marker-end="url(#arrow)"
                @click.stop="selectEdge(edge.id)"
              />
            </svg>

            <div
              v-for="node in nodes"
              :key="node.id"
              class="flow-node"
              :class="[`type-${node.type || 'step'}`, { selected: selectedNodeId === node.id, linking: linkSource === node.id }]"
              :style="{ left: `${node.x || 40}px`, top: `${node.y || 40}px` }"
              @mousedown.stop="startDrag($event, node)"
              @click.stop="selectNode(node)"
            >
              <div class="node-head">
                <span class="badge">{{ node.type || 'step' }}</span>
                <button type="button" class="link-btn" @click.stop="beginLink(node)">连线</button>
              </div>
              <input v-model="node.label" class="node-label" @mousedown.stop @click.stop />
              <div class="node-id muted">{{ node.id }}</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="5">
        <el-card shadow="never">
          <template #header>属性</template>
          <template v-if="selectedNode">
            <el-form label-width="70px" size="small">
              <el-form-item label="ID"><el-input v-model="selectedNode.id" disabled /></el-form-item>
              <el-form-item label="标签"><el-input v-model="selectedNode.label" /></el-form-item>
              <el-form-item label="类型">
                <el-select v-model="selectedNode.type" style="width: 100%">
                  <el-option v-for="p in palette" :key="p.type" :label="p.label" :value="p.type" />
                </el-select>
              </el-form-item>
              <el-form-item label="X"><el-input-number v-model="selectedNode.x" :step="10" /></el-form-item>
              <el-form-item label="Y"><el-input-number v-model="selectedNode.y" :step="10" /></el-form-item>
              <el-form-item label="备注"><el-input v-model="selectedNode.note" type="textarea" :rows="3" /></el-form-item>
            </el-form>
          </template>
          <template v-else-if="selectedEdge">
            <el-form label-width="70px" size="small">
              <el-form-item label="边 ID"><el-input :model-value="selectedEdge.id" disabled /></el-form-item>
              <el-form-item label="From"><el-input :model-value="selectedEdge.source" disabled /></el-form-item>
              <el-form-item label="To"><el-input :model-value="selectedEdge.target" disabled /></el-form-item>
              <el-form-item label="条件"><el-input v-model="selectedEdge.label" placeholder="可选条件表达式" /></el-form-item>
              <el-button type="danger" plain size="small" @click="removeEdge(selectedEdge.id)">删除边</el-button>
            </el-form>
          </template>
          <el-empty v-else description="选中节点或边" :image-size="48" />
        </el-card>
      </el-col>
    </el-row>

    <el-card v-if="showJson" shadow="never">
      <template #header>JSON</template>
      <el-row :gutter="12">
        <el-col :span="12"><el-input v-model="nodesText" type="textarea" :rows="10" @change="syncFromJson" /></el-col>
        <el-col :span="12"><el-input v-model="edgesText" type="textarea" :rows="10" @change="syncFromJson" /></el-col>
      </el-row>
    </el-card>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { featureUpgradesApi } from '@/api/feature-upgrades'

const scenarioId = ref(1)
const version = ref(0)
const nodes = ref([
  { id: 'start', label: '开始', type: 'start', x: 60, y: 120 },
  { id: 'step1', label: '登录', type: 'ui', x: 260, y: 120 },
  { id: 'end', label: '结束', type: 'end', x: 460, y: 120 },
])
const edges = ref([
  { id: 'e1', source: 'start', target: 'step1' },
  { id: 'e2', source: 'step1', target: 'end' },
])
const selectedNodeId = ref(null)
const selectedEdgeId = ref(null)
const linkSource = ref(null)
const showJson = ref(false)
const canvasEl = ref(null)
const canvasSize = ref({ w: 900, h: 560 })
const nodesText = ref('')
const edgesText = ref('')

const palette = [
  { type: 'start', label: '开始' },
  { type: 'ui', label: 'UI 步骤' },
  { type: 'api', label: 'API 步骤' },
  { type: 'assert', label: '断言' },
  { type: 'branch', label: '分支' },
  { type: 'end', label: '结束' },
]

const selectedNode = computed(() => nodes.value.find((n) => n.id === selectedNodeId.value) || null)
const selectedEdge = computed(() => edges.value.find((e) => e.id === selectedEdgeId.value) || null)

const edgePaths = computed(() => {
  const byId = Object.fromEntries(nodes.value.map((n) => [n.id, n]))
  return edges.value.map((edge) => {
    const s = byId[edge.source]
    const t = byId[edge.target]
    if (!s || !t) return { id: edge.id, d: '' }
    const x1 = (s.x || 0) + 120
    const y1 = (s.y || 0) + 36
    const x2 = t.x || 0
    const y2 = (t.y || 0) + 36
    const mid = (x1 + x2) / 2
    return { id: edge.id, d: `M ${x1} ${y1} C ${mid} ${y1}, ${mid} ${y2}, ${x2} ${y2}` }
  }).filter((e) => e.d)
})

let dragState = null
let nodeSeq = 1

function syncText() {
  nodesText.value = JSON.stringify(nodes.value, null, 2)
  edgesText.value = JSON.stringify(edges.value, null, 2)
}

function syncFromJson() {
  try {
    nodes.value = JSON.parse(nodesText.value || '[]')
    edges.value = JSON.parse(edgesText.value || '[]')
  } catch {
    ElMessage.warning('JSON 无效')
  }
}

function selectNode(node) {
  selectedNodeId.value = node.id
  selectedEdgeId.value = null
  if (linkSource.value && linkSource.value !== node.id) {
    const id = `e_${linkSource.value}_${node.id}_${Date.now().toString(36)}`
    if (!edges.value.some((e) => e.source === linkSource.value && e.target === node.id)) {
      edges.value.push({ id, source: linkSource.value, target: node.id })
    }
    linkSource.value = null
    syncText()
  }
}

function selectEdge(id) {
  selectedEdgeId.value = id
  selectedNodeId.value = null
}

function beginLink(node) {
  linkSource.value = node.id
  ElMessage.info(`从 ${node.label || node.id} 连线：请点击目标节点`)
}

function cancelLink() {
  linkSource.value = null
}

function addNode(type, label) {
  const id = `${type}_${nodeSeq++}`
  nodes.value.push({
    id,
    label: label || type,
    type,
    x: 80 + (nodes.value.length % 4) * 40,
    y: 80 + (nodes.value.length % 5) * 30,
  })
  selectedNodeId.value = id
  syncText()
}

function removeSelected() {
  if (!selectedNode.value) return
  const id = selectedNode.value.id
  nodes.value = nodes.value.filter((n) => n.id !== id)
  edges.value = edges.value.filter((e) => e.source !== id && e.target !== id)
  selectedNodeId.value = null
  syncText()
}

function removeEdge(id) {
  edges.value = edges.value.filter((e) => e.id !== id)
  selectedEdgeId.value = null
  syncText()
}

function onPaletteDragStart(event, item) {
  event.dataTransfer.setData('application/x-flow-type', item.type)
  event.dataTransfer.setData('text/plain', item.label)
}

function onCanvasDrop(event) {
  const type = event.dataTransfer.getData('application/x-flow-type') || 'ui'
  const label = event.dataTransfer.getData('text/plain') || type
  const rect = canvasEl.value.getBoundingClientRect()
  const x = event.clientX - rect.left - 60
  const y = event.clientY - rect.top - 24
  const id = `${type}_${nodeSeq++}`
  nodes.value.push({ id, label, type, x: Math.max(8, x), y: Math.max(8, y) })
  selectedNodeId.value = id
  syncText()
}

function onCanvasClick() {
  selectedNodeId.value = null
  selectedEdgeId.value = null
}

function startDrag(event, node) {
  if (event.button !== 0) return
  dragState = {
    id: node.id,
    ox: event.clientX,
    oy: event.clientY,
    sx: node.x || 0,
    sy: node.y || 0,
  }
  window.addEventListener('mousemove', onDragMove)
  window.addEventListener('mouseup', onDragEnd)
}

function onDragMove(event) {
  if (!dragState) return
  const node = nodes.value.find((n) => n.id === dragState.id)
  if (!node) return
  node.x = Math.max(0, dragState.sx + (event.clientX - dragState.ox))
  node.y = Math.max(0, dragState.sy + (event.clientY - dragState.oy))
}

function onDragEnd() {
  dragState = null
  window.removeEventListener('mousemove', onDragMove)
  window.removeEventListener('mouseup', onDragEnd)
  syncText()
}

function measureCanvas() {
  if (!canvasEl.value) return
  canvasSize.value = {
    w: canvasEl.value.clientWidth || 900,
    h: canvasEl.value.clientHeight || 560,
  }
}

async function load() {
  try {
    const res = await featureUpgradesApi.getFlow(scenarioId.value)
    nodes.value = (res.nodes || []).map((n) => ({
      ...n,
      x: n.x ?? n.position?.x ?? 40,
      y: n.y ?? n.position?.y ?? 40,
    }))
    edges.value = res.edges || []
    version.value = res.version || 0
    syncText()
    ElMessage.success('已加载')
  } catch (error) {
    ElMessage.error(error.message || '加载失败')
  }
}

async function save() {
  try {
    const res = await featureUpgradesApi.saveFlow(scenarioId.value, {
      scenario_id: scenarioId.value,
      nodes: nodes.value.map((n) => ({
        id: n.id,
        label: n.label,
        type: n.type,
        x: n.x,
        y: n.y,
        note: n.note || '',
        position: { x: n.x, y: n.y },
      })),
      edges: edges.value.map((e) => ({
        id: e.id,
        source: e.source,
        target: e.target,
        label: e.label || '',
      })),
      viewport: { x: 0, y: 0, zoom: 1 },
    })
    version.value = res.version || version.value + 1
    ElMessage.success('流程已保存')
  } catch (error) {
    ElMessage.error(error.message || '保存失败')
  }
}

watch([nodes, edges], syncText, { deep: true, immediate: true })

onMounted(() => {
  measureCanvas()
  window.addEventListener('resize', measureCanvas)
})
onBeforeUnmount(() => {
  window.removeEventListener('resize', measureCanvas)
  window.removeEventListener('mousemove', onDragMove)
  window.removeEventListener('mouseup', onDragEnd)
})
</script>

<style scoped>
.upgrade-page { padding: 20px; display: flex; flex-direction: column; gap: 16px; }
.page-header { display: flex; justify-content: space-between; gap: 12px; }
.page-header h1 { margin: 0 0 6px; font-size: 22px; }
.page-header p { margin: 0; color: #64748b; }
.actions { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
.panel-title { display: flex; justify-content: space-between; align-items: center; gap: 8px; }
.palette-card, .canvas-card { min-height: 620px; }
.palette { display: flex; flex-direction: column; gap: 8px; }
.palette-item { text-align: left; border: 1px dashed #cbd5e1; background: #f8fafc; border-radius: 8px; padding: 8px 10px; cursor: grab; display: flex; flex-direction: column; gap: 2px; }
.palette-item span { color: #64748b; font-size: 12px; }
.flow-canvas { position: relative; height: 560px; border: 1px solid #e2e8f0; border-radius: 12px; background:
  linear-gradient(90deg, rgba(148,163,184,.15) 1px, transparent 1px) 0 0 / 24px 24px,
  linear-gradient(rgba(148,163,184,.15) 1px, transparent 1px) 0 0 / 24px 24px,
  #fff;
  overflow: auto;
}
.edges-layer { position: absolute; inset: 0; width: 100%; height: 100%; pointer-events: none; }
.edge-path { fill: none; stroke: #64748b; stroke-width: 2; pointer-events: stroke; cursor: pointer; }
.edge-path.active { stroke: #2563eb; stroke-width: 3; }
.flow-node {
  position: absolute; width: 140px; min-height: 72px; border: 1px solid #cbd5e1; border-radius: 12px;
  background: #fff; box-shadow: 0 4px 12px rgba(15,23,42,.06); padding: 8px; cursor: move; user-select: none;
}
.flow-node.selected { border-color: #2563eb; box-shadow: 0 0 0 2px rgba(37,99,235,.2); }
.flow-node.linking { border-color: #f59e0b; }
.flow-node.type-start { background: #ecfdf5; }
.flow-node.type-end { background: #fef2f2; }
.flow-node.type-api { background: #eff6ff; }
.flow-node.type-assert { background: #fff7ed; }
.flow-node.type-branch { background: #f5f3ff; }
.node-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; }
.badge { font-size: 11px; color: #475569; background: #e2e8f0; border-radius: 999px; padding: 1px 6px; }
.link-btn { border: none; background: transparent; color: #2563eb; font-size: 12px; cursor: pointer; }
.node-label { width: 100%; border: 1px solid transparent; border-radius: 6px; font-weight: 600; padding: 2px 4px; }
.node-label:focus { border-color: #93c5fd; outline: none; }
.node-id { font-size: 11px; margin-top: 2px; word-break: break-all; }
.muted { color: #64748b; font-size: 12px; }
.mt-8 { margin-top: 8px; }
</style>
