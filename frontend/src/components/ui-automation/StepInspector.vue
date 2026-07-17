<template>
  <aside class="inspector">
    <template v-if="step">
      <div class="inspector-heading"><div><span>步骤 {{ index + 1 }}</span><h2>{{ actionLabel(step.type) }}</h2></div><el-switch v-model="step.enabled" /></div>
      <el-form label-position="top">
        <el-form-item label="步骤名称"><el-input v-model="step.name" /></el-form-item>

        <template v-if="needsLocator(step.type)">
          <div class="section-title">目标元素</div>
          <el-form-item label="定位方式">
            <el-select v-model="step.locator.strategy" style="width:100%" @change="resetLocatorOptions">
              <el-option label="测试标识（最稳定）" value="test_id" />
              <el-option label="表单标签" value="label" />
              <el-option label="控件角色和名称" value="role" />
              <el-option label="输入框提示文字" value="placeholder" />
              <el-option label="页面文字" value="text" />
              <el-option label="CSS 选择器" value="css" />
              <el-option label="XPath" value="xpath" />
            </el-select>
          </el-form-item>
          <template v-if="step.locator.strategy === 'role'">
            <el-form-item label="控件角色"><el-select v-model="step.locator.value" style="width:100%"><el-option v-for="role in roles" :key="role" :label="roleLabels[role]" :value="role" /></el-select></el-form-item>
            <el-form-item label="控件名称"><el-input v-model="step.locator.options.name" placeholder="例如：登录" /></el-form-item>
          </template>
          <el-form-item v-else label="定位值"><el-input v-model="step.locator.value" :placeholder="locatorPlaceholder(step.locator.strategy)" /></el-form-item>
          <div class="locator-actions"><el-button size="small" @click="$emit('validate-locator')">验证定位</el-button><span>应精确匹配 1 个元素</span></div>
        </template>

        <template v-if="inputKind(step.type)">
          <div class="section-title">输入数据</div>
                              <template v-if="inputKind(step.type) === 'viewport'">
            <div class="viewport-fields"><el-form-item label="宽度"><el-input-number :model-value="step.input?.width" :min="320" :max="3840" @update:model-value="setInput('width',$event)" /></el-form-item><el-form-item label="高度"><el-input-number :model-value="step.input?.height" :min="240" :max="2160" @update:model-value="setInput('height',$event)" /></el-form-item></div>
          </template>
          <template v-else-if="inputKind(step.type) === 'downloadOptions'">
            <el-form-item label="文件名正则"><el-input :model-value="step.input?.expectedFilename" @update:model-value="setInput('expectedFilename',$event)" placeholder="例如：order-.*\.txt" /></el-form-item>
            <el-form-item label="最小字节数"><el-input-number :model-value="step.input?.minBytes" :min="0" @update:model-value="setInput('minBytes',$event)" /></el-form-item>
            <el-form-item label="必须包含文字"><el-input :model-value="step.input?.containsText" @update:model-value="setInput('containsText',$event)" placeholder="适用于文本文件" /></el-form-item>
            <el-form-item label="保存路径变量"><el-input :model-value="step.input?.variable" @update:model-value="setInput('variable',$event)" placeholder="downloadPath" /></el-form-item>
          </template>          <template v-else-if="inputKind(step.type) === 'targetLocator'">
            <el-form-item label="目标定位方式"><el-select :model-value="step.input?.targetLocator?.strategy" style="width:100%" @update:model-value="setTargetLocator('strategy',$event)"><el-option label="测试标识" value="test_id" /><el-option label="页面文字" value="text" /><el-option label="CSS 选择器" value="css" /><el-option label="XPath" value="xpath" /></el-select></el-form-item>
            <el-form-item label="目标定位值"><el-input :model-value="step.input?.targetLocator?.value" @update:model-value="setTargetLocator('value',$event)" placeholder="拖拽释放区域的定位值" /></el-form-item>
          </template>          <template v-else-if="inputKind(step.type) === 'files'">
            <el-form-item label="测试文件">
              <div class="file-picker"><el-input :model-value="(step.input?.paths || []).join('; ')" readonly placeholder="请选择回放时上传的文件" /><el-button @click="chooseFiles">选择文件</el-button></div>
              <div v-if="step.input?.filenames?.length && !step.input?.paths?.length" class="recorded-files">录制时选择：{{ step.input.filenames.join('、') }}，请重新绑定本机测试文件。</div>
            </el-form-item>
          </template>
          <template v-else-if="inputKind(step.type) === 'variable'">
            <el-form-item label="变量名"><el-input :model-value="step.input?.name" @update:model-value="setInput('name', $event)" placeholder="例如：orderId" /></el-form-item>
            <el-form-item label="变量值"><el-input :model-value="step.input?.value" @update:model-value="setInput('value', $event)" placeholder="支持 {{变量名}}" /></el-form-item>
          </template>
          <el-form-item v-else :label="inputLabel(inputKind(step.type))">
            <el-select v-if="inputKind(step.type) === 'state'" :model-value="step.input?.state" style="width:100%" @update:model-value="setInput('state', $event)"><el-option label="页面完成加载" value="load" /><el-option label="DOM 已就绪" value="domcontentloaded" /><el-option label="网络空闲" value="networkidle" /></el-select>
            <el-input v-else :model-value="inputValue" @update:model-value="setInput(inputKind(step.type), $event)" :type="step.input?.secret ? 'password' : 'text'" :placeholder="inputPlaceholder(inputKind(step.type))" />
          </el-form-item>
        </template>

        <el-collapse class="advanced"><el-collapse-item title="等待、重试与失败策略" name="advanced">
          <el-form-item label="步骤超时（毫秒）"><el-input-number v-model="step.timeout_ms" :min="100" :max="120000" :step="500" controls-position="right" /></el-form-item>
          <el-form-item label="失败重试次数"><el-input-number v-model="step.retry.count" :min="0" :max="10" controls-position="right" /></el-form-item>
          <el-form-item label="重试间隔（毫秒）"><el-input-number v-model="step.retry.delay_ms" :min="0" :max="60000" :step="500" controls-position="right" /></el-form-item>
          <el-form-item label="失败后继续"><el-switch v-model="step.continue_on_failure" /></el-form-item>
          <el-form-item label="截图"><el-select v-model="step.screenshot" style="width:100%"><el-option label="失败时截图" value="on-failure" /><el-option label="总是截图" value="always" /><el-option label="不截图" value="never" /></el-select></el-form-item>
          <el-form-item label="调试断点"><el-switch v-model="step.breakpoint" /></el-form-item>
        </el-collapse-item></el-collapse>
      </el-form>
      <div class="inspector-footer"><el-button @click="$emit('duplicate')">复制</el-button><el-button type="danger" plain @click="$emit('delete')">删除</el-button></div>
    </template>
    <div v-else class="no-selection"><el-icon><EditPen /></el-icon><strong>选择一个步骤</strong><span>在这里配置目标元素、输入数据、等待和失败策略。</span></div>
  </aside>
</template>
<script setup>
import { computed } from 'vue'
import { EditPen } from '@element-plus/icons-vue'
import { actionLabel, inputKind, needsLocator } from './action-catalog'
const props = defineProps({ step: Object, index: { type: Number, default: -1 } })
defineEmits(['delete', 'duplicate', 'validate-locator'])
const roles = ['button', 'link', 'textbox', 'checkbox', 'radio', 'combobox', 'option', 'heading', 'tab']
const roleLabels = { button: '按钮', link: '链接', textbox: '输入框', checkbox: '复选框', radio: '单选框', combobox: '下拉框', option: '选项', heading: '标题', tab: '标签页' }
const inputValue = computed(() => { const kind = props.step ? inputKind(props.step.type) : null; return kind ? String(props.step.input?.[kind] ?? '') : '' })
async function chooseFiles() { const result = await window.testmaster?.files?.choose({ multiple: true }); if (result && !result.cancelled) { if (!props.step.input) props.step.input = {}; props.step.input.paths = result.paths; props.step.input.requiresFileSelection = false } }
function setInput(key, value) { if (!props.step.input) props.step.input = {}; props.step.input[key] = key === 'ms' ? Number(value) : value }
function setTargetLocator(key, value) { if (!props.step.input) props.step.input = {}; if (!props.step.input.targetLocator) props.step.input.targetLocator = { strategy: 'css', value: '', options: {}, fallbacks: [], framePath: [] }; props.step.input.targetLocator[key] = value; if (key === 'strategy') props.step.input.targetLocator.options = {} }
function resetLocatorOptions(strategy) { props.step.locator.options = {}; props.step.locator.value = strategy === 'role' ? 'button' : '' }
function locatorPlaceholder(strategy) { return ({ test_id: '例如：login-button', label: '例如：用户名', placeholder: '例如：请输入用户名', text: '例如：立即登录', css: '例如：#login-button', xpath: '例如：//button[@type="submit"]' })[strategy] || '请输入定位值' }
function inputLabel(kind) { return ({ url: '页面地址', value: '输入值', key: '键盘按键', expected: '预期结果', ms: '等待毫秒数', state: '加载状态', name: '变量名', index: '页面序号' })[kind] || '输入数据' }
function inputPlaceholder(kind) { return ({ url: '支持完整地址或 /relative-path', value: '支持 {{变量名}}', key: '例如：Enter、Tab', expected: '期望页面出现的值', ms: '例如：1000', name: '例如：productName', index: '填写 last 表示最新页面' })[kind] || '' }
</script>
<style scoped>
.inspector { box-sizing: border-box; width: 330px; min-height: 560px; border-left: 1px solid #dbe3de; background: #fff; padding: 18px; overflow: auto; }.inspector-heading { display:flex; justify-content:space-between; align-items:center; margin-bottom:18px; }.inspector-heading span { color:#758179; font-size:11px; }.inspector-heading h2 { margin:3px 0 0; font-size:17px; }.section-title { margin:18px 0 12px; padding-top:16px; border-top:1px solid #e5ebe7; color:#28724f; font-size:12px; font-weight:700; }.locator-actions { display:flex; align-items:center; gap:8px; margin-top:-7px; color:#7a867e; font-size:11px; }.viewport-fields { display:grid; grid-template-columns:1fr 1fr; gap:8px; }.file-picker { display:flex; width:100%; gap:8px; }.recorded-files { margin-top:6px; color:#b26a00; font-size:11px; line-height:1.5; }
.advanced { margin-top:18px; }.inspector-footer { display:flex; gap:8px; padding-top:16px; border-top:1px solid #e5ebe7; }.no-selection { min-height:480px; display:flex; flex-direction:column; align-items:center; justify-content:center; text-align:center; color:#7a867e; gap:10px; }.no-selection .el-icon { font-size:28px; }.no-selection strong { color:#354139; }.no-selection span { max-width:230px; font-size:12px; line-height:1.6; }
</style>




