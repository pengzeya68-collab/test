<template>
  <div
    class="base-splitter"
    :class="[
      `base-splitter--${direction}`,
      { 'base-splitter--dragging': isDragging, 'base-splitter--reduced': prefersReducedMotion }
    ]"
    role="separator"
    :aria-orientation="direction === 'horizontal' ? 'vertical' : 'horizontal'"
    aria-label="拖动调整面板大小"
    tabindex="0"
    @mousedown="onPointerDown"
    @touchstart.passive="onPointerDown"
    @keydown.left.prevent="onArrowKey(-step, 'x')"
    @keydown.right.prevent="onArrowKey(step, 'x')"
    @keydown.up.prevent="onArrowKey(-step, 'y')"
    @keydown.down.prevent="onArrowKey(step, 'y')"
  >
    <div class="base-splitter__grip">
      <span class="base-splitter__dot"></span>
      <span class="base-splitter__dot"></span>
      <span class="base-splitter__dot"></span>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'

const props = defineProps({
  // 双向绑定的尺寸（px）：horizontal 时为左侧面板宽度，vertical 时为上方面板高度
  size: {
    type: Number,
    default: null
  },
  // 方向：horizontal = 左右分栏（分隔条垂直），vertical = 上下分栏（分隔条水平）
  direction: {
    type: String,
    default: 'horizontal'
  },
  // 最小尺寸（px）
  minSize: {
    type: Number,
    default: 200
  },
  // 最大尺寸（px），传 0 表示自动取容器宽度 - minSize - 200
  maxSize: {
    type: Number,
    default: 0
  },
  // localStorage 持久化 key，传空字符串则不持久化
  storageKey: {
    type: String,
    default: ''
  },
  // 键盘调整步长（px）
  step: {
    type: Number,
    default: 16
  },
  // size 控制的是"哪一侧"面板的尺寸
  // - 'left'（默认）：size 表示 splitter 左侧（horizontal）/ 上方（vertical）面板
  //                  向光标方向拖动 → size 增大 → 该侧面板变宽
  // - 'right'：     size 表示 splitter 右侧（horizontal）/ 下方（vertical）面板
  //                  向光标方向拖动 → size 增大 → 该侧面板变宽
  // 两种模式下，光标移动方向始终和 size 变化方向一致（所见即所得）
  target: {
    type: String,
    default: 'left',
    validator: (v) => ['left', 'right'].includes(v)
  },
  // 容器选择器，用于计算 maxSize 自动值；不传则使用父元素
  containerSelector: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['update:size', 'drag-start', 'drag-end'])

const isDragging = ref(false)
const prefersReducedMotion = ref(false)
let startX = 0
let startY = 0
let startSize = 0

const getContainer = () => {
  if (props.containerSelector) {
    return document.querySelector(props.containerSelector)
  }
  return null
}

const computeMaxSize = () => {
  if (props.maxSize > 0) return props.maxSize
  const container = getContainer()
  if (!container) return window.innerWidth - props.minSize - 200
  const rect = container.getBoundingClientRect()
  const total = props.direction === 'horizontal' ? rect.width : rect.height
  return Math.max(props.minSize + 100, total - props.minSize - 200)
}

const clamp = (v) => Math.max(props.minSize, Math.min(computeMaxSize(), v))

const loadStoredSize = () => {
  if (!props.storageKey) return null
  try {
    const raw = localStorage.getItem(props.storageKey)
    if (raw == null) return null
    const n = Number(raw)
    return Number.isFinite(n) ? n : null
  } catch {
    return null
  }
}

const persistSize = (v) => {
  if (!props.storageKey) return
  try {
    localStorage.setItem(props.storageKey, String(v))
  } catch {
    // ignore quota errors
  }
}

// 同步恢复持久化尺寸（在 setup 顶层执行，避免 onMounted 导致的首屏闪烁）
// 使用 clamp 约束，避免存储值超出当前视口范围
;(() => {
  const stored = loadStoredSize()
  if (stored != null) {
    emit('update:size', clamp(stored))
  }
})()

const onPointerDown = (e) => {
  e.preventDefault()
  isDragging.value = true
  emit('drag-start')
  const point = e.touches ? e.touches[0] : e
  startX = point.clientX
  startY = point.clientY
  startSize = props.size ?? 0

  document.body.style.cursor = props.direction === 'horizontal' ? 'col-resize' : 'row-resize'
  document.body.style.userSelect = 'none'
  document.body.style.webkitUserSelect = 'none'

  document.addEventListener('mousemove', onPointerMove)
  document.addEventListener('mouseup', onPointerUp)
  document.addEventListener('touchmove', onPointerMove, { passive: false })
  document.addEventListener('touchend', onPointerUp)
  document.addEventListener('touchcancel', onPointerUp)
}

const onPointerMove = (e) => {
  if (!isDragging.value) return
  if (e.cancelable) e.preventDefault()
  const point = e.touches ? e.touches[0] : e
  const dx = point.clientX - startX
  const dy = point.clientY - startY
  let next
  if (props.direction === 'horizontal') {
    // target=right 时，光标右移对应"右侧面板被推开"——但 size 仍取 +dx，
    // 父组件把 size 解释为右侧面板宽度即可自然变宽。
    // 视觉上：光标右移，size 增大 = size 指向的面板变宽。
    next = clamp(startSize + dx)
  } else {
    next = clamp(startSize + dy)
  }
  emit('update:size', next)
}

const onPointerUp = () => {
  if (!isDragging.value) return
  isDragging.value = false
  document.body.style.cursor = ''
  document.body.style.userSelect = ''
  document.body.style.webkitUserSelect = ''
  document.removeEventListener('mousemove', onPointerMove)
  document.removeEventListener('mouseup', onPointerUp)
  document.removeEventListener('touchmove', onPointerMove)
  document.removeEventListener('touchend', onPointerUp)
  document.removeEventListener('touchcancel', onPointerUp)
  persistSize(props.size)
  emit('drag-end')
}

const onArrowKey = (delta) => {
  const next = clamp((props.size ?? 0) + delta)
  emit('update:size', next)
  persistSize(next)
}

onMounted(() => {
  try {
    prefersReducedMotion.value = window.matchMedia('(prefers-reduced-motion: reduce)').matches
  } catch {
    prefersReducedMotion.value = false
  }
})

onBeforeUnmount(() => {
  onPointerUp()
})
</script>

<style scoped>
.base-splitter {
  flex-shrink: 0;
  position: relative;
  z-index: 5;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  user-select: none;
  outline: none;
}

.base-splitter--horizontal {
  width: 12px;
  height: 100%;
  cursor: col-resize;
}

.base-splitter--vertical {
  width: 100%;
  height: 12px;
  cursor: row-resize;
}

.base-splitter__grip {
  display: flex;
  flex-direction: column;
  gap: 4px;
  align-items: center;
  justify-content: center;
  width: 4px;
  min-height: 48px;
  border-radius: 4px;
  background: var(--tm-border-light, rgba(128, 128, 128, 0.25));
  transition: background 0.2s ease, min-height 0.2s ease;
}

.base-splitter--vertical .base-splitter__grip {
  flex-direction: row;
  width: 48px;
  min-height: 4px;
  min-width: 48px;
}

.base-splitter__dot {
  width: 3px;
  height: 3px;
  border-radius: 50%;
  background: var(--tm-text-secondary, rgba(128, 128, 128, 0.6));
  transition: background 0.2s ease;
}

.base-splitter:hover {
  background: rgba(var(--tm-color-primary-rgb, 99, 102, 241), 0.06);
}

.base-splitter:hover .base-splitter__grip,
.base-splitter--dragging .base-splitter__grip {
  background: rgba(var(--tm-color-primary-rgb, 99, 102, 241), 0.3);
  min-height: 64px;
}

.base-splitter--vertical:hover .base-splitter__grip,
.base-splitter--vertical.base-splitter--dragging .base-splitter__grip {
  min-width: 64px;
}

.base-splitter:hover .base-splitter__dot,
.base-splitter--dragging .base-splitter__dot {
  background: var(--tm-color-primary, #6366f1);
}

.base-splitter--dragging {
  background: rgba(var(--tm-color-primary-rgb, 99, 102, 241), 0.1);
}

/* 拖拽进行中禁用过渡，避免视觉延迟 */
.base-splitter--dragging .base-splitter__grip,
.base-splitter--dragging .base-splitter__dot {
  transition: none;
}

.base-splitter--reduced .base-splitter__grip,
.base-splitter--reduced .base-splitter__dot {
  transition: none;
}

.base-splitter:focus-visible {
  outline: 2px solid var(--tm-color-primary, #6366f1);
  outline-offset: -1px;
}
</style>
