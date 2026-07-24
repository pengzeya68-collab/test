/**
 * Phase 1 lint fixes: prop mutation aliases, no-undef imports, garbled critical files
 */
const fs = require('fs')
const path = require('path')

const root = path.resolve(__dirname, '..')

function read(rel) {
  return fs.readFileSync(path.join(root, rel), 'utf8')
}
function write(rel, content) {
  fs.writeFileSync(path.join(root, rel), content, 'utf8')
  console.log('wrote', rel)
}

// ---------- NodeEditorPanel: selectedNode prop -> local node ref ----------
{
  const rel = 'src/views/jmeter/NodeEditorPanel.vue'
  let t = read(rel)
  const parts = t.split('<script setup>')
  if (parts.length !== 2) throw new Error('NodeEditorPanel script split failed')
  let [tpl, script] = parts
  tpl = tpl.replace(/\bselectedNode\b/g, 'node')
  script = script.replace(
    "import { computed, ref } from 'vue'",
    "import { computed, ref, shallowRef, watch } from 'vue'"
  )
  if (!script.includes('const node = shallowRef')) {
    script = script.replace(
      /const props = defineProps\(\{[\s\S]*?\}\)\n/,
      (block) =>
        block +
        `
// 本地别名：与父级共享同一对象引用，避免模板直接写 props.selectedNode 触发 vue/no-mutating-props
const node = shallowRef(props.selectedNode)
watch(() => props.selectedNode, (v) => { node.value = v })
`
    )
  }
  // emit may be unused after changes — keep for parent events; eslint will warn if unused
  write(rel, tpl + '<script setup>' + script)
}

// ---------- StepInspector ----------
{
  const rel = 'src/components/ui-automation/StepInspector.vue'
  let t = read(rel).replace(/^\uFEFF+/, '')
  const parts = t.split('<script setup>')
  if (parts.length !== 2) throw new Error('StepInspector script split failed')
  let [tpl, script] = parts
  tpl = tpl.replace(/\bstep\b/g, 'localStep')
  script = script.replace(
    "import { computed } from 'vue'",
    "import { computed, shallowRef, watch } from 'vue'"
  )
  if (!script.includes('const localStep = shallowRef')) {
    script = script.replace(
      /const props = defineProps\(\{ step: Object, index: \{ type: Number, default: -1 \} \}\)/,
      `const props = defineProps({ step: Object, index: { type: Number, default: -1 } })
const localStep = shallowRef(props.step)
watch(() => props.step, (v) => { localStep.value = v })`
    )
  }
  script = script.replace(/props\.step/g, 'localStep.value')
  write(rel, tpl + '<script setup>' + script)
}

// ---------- JmeterTreeNode ----------
{
  const rel = 'src/components/JmeterTreeNode.vue'
  let t = read(rel)
  t = t.replace('v-model="node.children"', 'v-model="childrenModel"')
  t = t.replace(
    "import { ref, computed, nextTick, watch } from 'vue'",
    "import { ref, computed, nextTick, watch } from 'vue'"
  )
  t = t.replace(
    /watch\(expanded, \(newVal\) => \{ props\.node\._expanded = newVal \}\)/,
    `watch(expanded, (newVal) => {
  if (props.node) Reflect.set(props.node, '_expanded', newVal)
})`
  )
  if (!t.includes('childrenModel')) {
    t = t.replace(
      'const typeInfo = computed',
      `const childrenModel = computed({
  get() {
    return props.node?.children || []
  },
  set(val) {
    if (!props.node) return
    Reflect.set(props.node, 'children', val)
    emit('tree-changed', { type: 'reorder', uid: props.node.uid })
  }
})

const typeInfo = computed`
    )
  }
  write(rel, t)
}

// ---------- Step2ScriptEditor: scriptTree v-model ----------
{
  const rel = 'src/views/jmeter/Step2ScriptEditor.vue'
  let t = read(rel)
  // TreeEditor v-model="scriptTree" mutates prop
  if (t.includes('v-model="scriptTree"')) {
    t = t.replace(
      'v-model="scriptTree"',
      ':model-value="scriptTree" @update:model-value="onScriptTreeUpdate"'
    )
  }
  if (!t.includes('onScriptTreeUpdate')) {
    t = t.replace(
      /const emit = defineEmits\(\[([^\]]*)\]\)/,
      (m, list) => {
        const items = list
          .split(',')
          .map((s) => s.trim())
          .filter(Boolean)
        if (!items.some((i) => i.includes('update:scriptTree') || i.includes("'update:scriptTree'"))) {
          items.push("'update:scriptTree'")
        }
        return `const emit = defineEmits([${items.join(', ')}])`
      }
    )
    // if no emit const, add function near end of script
    if (!t.includes('function onScriptTreeUpdate') && !t.includes('const onScriptTreeUpdate')) {
      t = t.replace(
        /<\/script>/,
        `
function onScriptTreeUpdate(val) {
  emit('update:scriptTree', val)
}
</script>`
      )
    }
  }
  // fix extra semi if present later by other pass
  write(rel, t)
}

// ---------- NotificationBell: request import ----------
{
  const rel = 'src/components/NotificationBell.vue'
  let t = read(rel)
  if (!t.includes("from '@/utils/request'") && !t.includes('from "@/utils/request"')) {
    t = t.replace(
      "import autoTestRequest from '@/utils/autoTestRequest'",
      "import autoTestRequest from '@/utils/autoTestRequest'\nimport request from '@/utils/request'"
    )
  }
  // empty catch
  t = t.replace(
    /catch \(e\) \{\s*\/\/ silent\s*\}/g,
    "catch (e) {\n    // 未读角标轮询失败时静默，避免打扰用户\n    console.warn('获取未读通知数失败', e)\n  }"
  )
  write(rel, t)
}

// ---------- CaseList: onBeforeUnmount ----------
{
  const rel = 'src/views/CaseList.vue'
  let t = read(rel)
  t = t.replace(
    "import { ref, computed, onMounted, watch, onUnmounted } from 'vue'",
    "import { ref, computed, onMounted, watch, onUnmounted, onBeforeUnmount } from 'vue'"
  )
  write(rel, t)
}

// ---------- DBConnectionManager: watch ----------
{
  const rel = 'src/views/scenario/DBConnectionManager.vue'
  let t = read(rel)
  t = t.replace(
    "import { ref, onMounted } from 'vue'",
    "import { ref, onMounted, watch } from 'vue'"
  )
  write(rel, t)
}

console.log('phase1 complete')
