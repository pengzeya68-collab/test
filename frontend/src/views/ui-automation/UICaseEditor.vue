<template>
  <div class="automation-studio" v-loading="loading">
    <header class="studio-toolbar">
      <div class="case-heading"><el-button text :icon="ArrowLeft" @click="goBack">用例列表</el-button><div><h1>{{ caseData?.name || 'UI 自动化用例' }}</h1><span :class="['engine-state',{ready:desktopReady}]"><i></i>{{ desktopReady ? '桌面引擎已连接' : '桌面引擎未连接' }}</span></div></div>
      <div class="toolbar-actions">
        <el-button :icon="FolderChecked" :loading="saving" @click="saveAll">保存</el-button>
        <el-button :icon="Search" :disabled="!recording || !selectedStep?.locator || authCaptureMode" :loading="locatorSuggestionLoading" @click="requestLocatorSuggestions">定位建议</el-button>
        <el-button :icon="Aim" :disabled="!desktopReady || recording" :loading="running" @click="executeCase(true)">调试运行</el-button><el-button type="primary" :icon="VideoPlay" :disabled="!desktopReady || recording" :loading="running" @click="executeCase(false)">运行完整流程</el-button>
      </div>
    </header>

    <section class="recording-bar" :class="{ active: recording }">
      <div class="record-address"><el-input v-model="recorderUrl" :disabled="recording" placeholder="输入被测系统地址，例如：https://test.example.com"><template #prepend>录制地址</template></el-input></div>
      <el-popover v-if="!recording" trigger="click" placement="bottom-end" :width="440">
        <template #reference><el-button :icon="Setting">接口采集范围</el-button></template>
        <el-form label-position="top">
          <el-form-item label="域名白名单"><el-input v-model="captureConfig.domain_allowlist_text" type="textarea" :rows="3" placeholder="每行一个域名，例如 api.example.com 或 *.example.com" /></el-form-item>
          <el-form-item label="排除路径"><el-input v-model="captureConfig.path_exclude_text" type="textarea" :rows="3" placeholder="每行一个路径，例如 /health 或 /static/*" /></el-form-item>
        </el-form>
      </el-popover>
      <template v-if="!recording"><el-button type="danger" :icon="VideoCamera" :disabled="!desktopReady" @click="startRecording">开始录制</el-button><el-button v-if="captureSyncFailed" type="warning" :loading="captureSyncing" @click="retryPendingCapture">{{ captureRetryLabel }}</el-button><el-button v-if="activeCaptureId && captureSyncFailed" type="danger" plain @click="discardPendingCapture">放弃未同步抓包</el-button><el-button v-if="completedCaptureId" type="primary" plain @click="openCaptureImport">接口候选 {{ capturedExchangeCount }}</el-button></template>
      <template v-else>
        <span class="recording-indicator"><i></i>{{ authCaptureMode ? '等待人工登录' : (capturePaused ? '接口采集已暂停' : '正在录制') }}</span>
        <template v-if="authCaptureMode"><span class="auth-capture-tip">请在打开的浏览器中完成账号、短信或验证码登录；登录成功后回到这里保存。</span></template>
        <template v-else>
          <el-button :type="recorderMode === 'assert-visible' ? 'primary' : 'default'" :icon="View" @click="setRecorderMode('assert-visible')">添加可见断言</el-button>
          <el-button :type="recorderMode === 'assert-text' ? 'primary' : 'default'" :icon="CircleCheck" @click="setRecorderMode('assert-text')">添加文字断言</el-button>
          <el-button v-if="activeCaptureId" @click="toggleCapturePaused">{{ capturePaused ? '恢复接口采集' : '暂停接口采集' }}</el-button>
          <el-button type="danger" plain :icon="VideoPause" @click="stopRecording">停止录制</el-button>
        </template>
      </template>
    </section>

    <section v-if="caseData" class="case-context">
      <label>测试环境</label><el-select v-model="selectedEnvironmentId" clearable placeholder="不使用环境" style="width:180px"><el-option v-for="env in environments" :key="env.id" :label="env.env_name || env.name" :value="env.id" /></el-select>
      <label>登录态</label><el-select v-model="selectedAuthStateId" clearable placeholder="每次重新登录" style="width:220px"><el-option v-for="item in authStates" :key="item.id" :label="item.name" :value="item.id" /></el-select>
      <el-button v-if="!authCaptureMode" type="primary" plain @click="startAuthCapture(false)">人工登录并保存</el-button>
      <el-button v-if="selectedAuthStateId && !authCaptureMode" @click="startAuthCapture(true)">更新登录态</el-button>
      <el-button v-if="authCaptureMode" type="success" @click="saveCurrentAuthState">登录完成，保存状态</el-button>
      <el-button v-if="authCaptureMode" @click="cancelAuthCapture">取消</el-button>
      <el-button text :disabled="authCaptureMode" @click="loadExecutionProfiles">刷新</el-button>
      <el-popover trigger="click" placement="bottom-start" :width="460"><template #reference><el-button :disabled="authCaptureMode">管理登录态</el-button></template><div class="auth-state-manager"><div v-if="!authStates.length" class="auth-empty">暂无已保存登录态</div><div v-for="item in authStates" :key="item.id" class="auth-row"><div><strong>{{ item.name }}</strong><small>更新于 {{ formatAuthTime(item.updatedAt) }}</small><span v-if="authCheckResults[item.id]" :class="['auth-health',authCheckResults[item.id].valid?'ok':'bad']">{{ authCheckResults[item.id].valid?'可用':'失效' }} · {{ authCheckResults[item.id].reason }}</span></div><el-button size="small" :loading="checkingAuthId===item.id" @click="checkAuthState(item)">验活</el-button><el-button size="small" type="danger" plain @click="removeAuthState(item)">删除</el-button></div></div></el-popover>
      <el-popover trigger="click" placement="bottom-end" :width="360"><template #reference><el-button :icon="Setting">地址与超时</el-button></template><el-form label-position="top"><el-form-item label="基础地址（环境未配置时使用）"><el-input v-model="caseData.base_url" placeholder="例如：https://test.example.com" /></el-form-item><el-form-item label="普通步骤超时"><el-input-number v-model="caseData.default_timeout_ms" :min="1000" :max="120000" :step="1000" /> ms</el-form-item><el-form-item label="页面跳转超时"><el-input-number v-model="caseData.navigation_timeout_ms" :min="1000" :max="120000" :step="1000" /> ms</el-form-item></el-form></el-popover>
      <el-popover trigger="click" placement="bottom-end" :width="340"><template #reference><el-button :icon="Setting">运行设置</el-button></template><el-form label-position="top"><el-form-item label="普通步骤超时"><el-input-number v-model="caseData.default_timeout_ms" :min="1000" :max="120000" :step="1000" /> ms</el-form-item><el-form-item label="页面跳转超时"><el-input-number v-model="caseData.navigation_timeout_ms" :min="1000" :max="120000" :step="1000" /> ms</el-form-item></el-form></el-popover>
    </section>

    <div class="studio-workspace">
      <main class="flow-canvas">
        <div class="canvas-header"><div><h2>用户操作流程</h2><span>{{ steps.length }} 个步骤</span></div><div><el-button :icon="Search" @click="openPicker(steps.length)">搜索并添加</el-button><el-button v-if="steps.length" text type="danger" @click="clearSteps">清空</el-button></div></div>
        <div v-if="!steps.length" class="empty-flow"><el-icon><VideoCamera /></el-icon><h3>录制真实操作，快速生成用例</h3><p>输入地址后点击“开始录制”，在打开的浏览器中完成登录、搜索、上传或下单。也可以手工添加步骤。</p><div><el-button type="danger" :icon="VideoCamera" @click="startRecording">开始录制</el-button><el-button @click="openPicker(0)">手工添加</el-button></div></div>
        <div v-else class="flow-list">
          <button class="insert-step first" type="button" @click="openPicker(0)"><el-icon><Plus /></el-icon><span>在开头添加</span></button>
          <template v-for="(step,index) in steps" :key="step.id">
            <article :class="['flow-step',{selected:selectedStepId===step.id,invalid:errors[step.id],disabled:!step.enabled}]" @click="selectStep(step.id)">
              <div class="step-sequence">{{ index + 1 }}</div>
              <div class="step-icon"><el-icon><component :is="actionIcon(step.type)" /></el-icon></div>
              <div class="step-summary"><strong>{{ step.name || actionLabel(step.type) }}</strong><span>{{ stepDescription(step) }}</span><small v-if="errors[step.id]">{{ errors[step.id] }}</small></div>
              <div class="step-badges"><el-tag v-if="step.breakpoint" type="warning" size="small">断点</el-tag><el-tag v-if="!step.enabled" type="info" size="small">停用</el-tag></div>
              <div class="step-tools"><el-button text :icon="ArrowUp" :disabled="index===0" title="上移" @click.stop="moveStep(index,-1)"/><el-button text :icon="ArrowDown" :disabled="index===steps.length-1" title="下移" @click.stop="moveStep(index,1)"/></div>
            </article>
            <button class="insert-step" type="button" @click="openPicker(index+1)"><el-icon><Plus /></el-icon><span>在此添加步骤</span></button>
          </template>
        </div>
      </main>
      <StepInspector :step="selectedStep" :index="selectedIndex" @delete="deleteSelected" @duplicate="duplicateSelected" @validate-locator="validateSelectedLocator" />
    </div>

    <section class="debug-console">
      <el-tabs v-model="debugTab">
        <el-tab-pane :label="`运行日志 (${executionLogs.length})`" name="execution"><div class="debug-list"><div v-for="(item,index) in executionLogs" :key="index" :class="['debug-line',item.level]"><span>{{ item.time }}</span><strong>{{ item.message }}</strong></div><el-empty v-if="!executionLogs.length" description="运行后显示步骤日志" :image-size="48" /></div></el-tab-pane>
        <el-tab-pane :label="`浏览器控制台 (${consoleLogs.length})`" name="console"><div class="debug-list"><div v-for="(item,index) in consoleLogs" :key="index" :class="['debug-line',item.level]"><span>{{ item.time }}</span><strong>{{ item.text }}</strong></div><el-empty v-if="!consoleLogs.length" description="录制时显示浏览器控制台" :image-size="48" /></div></el-tab-pane>
        <el-tab-pane :label="`变量 (${Object.keys(variableSnapshot).length})`" name="variables"><div class="debug-list"><div v-for="(value,name) in variableSnapshot" :key="name" class="debug-line"><span>{{ name }}</span><strong>{{ value }}</strong></div><el-empty v-if="!Object.keys(variableSnapshot).length" description="调试暂停时显示变量" :image-size="48" /></div></el-tab-pane><el-tab-pane :label="`网络请求 (${networkLogs.length})`" name="network"><div class="debug-list"><div v-for="(item,index) in networkLogs" :key="index" :class="['debug-line',{error:item.failed}]"><span>{{ item.status || '失败' }}</span><strong>{{ item.method }} {{ item.url }}</strong></div><el-empty v-if="!networkLogs.length" description="没有可捕获的接口请求" :image-size="48" /></div></el-tab-pane>
      </el-tabs>
    </section>

    <ActionPicker v-model="pickerVisible" @select="insertAction" />
    <RunResultDrawer ref="runResultDrawer" v-model="showRunResult" @run-finished="running=false" />
    <el-dialog v-model="locatorSuggestionVisible" title="定位器建议" width="760px">
      <el-table :data="locatorSuggestions" row-key="locator.value">
        <el-table-column label="策略" width="120"><template #default="{ row }">{{ locatorLabel(row.locator.strategy) }}</template></el-table-column>
        <el-table-column prop="locator.value" label="定位值" min-width="300" show-overflow-tooltip />
        <el-table-column label="置信度" width="100"><template #default="{ row }">{{ Math.round(row.confidence * 100) }}%</template></el-table-column>
        <el-table-column label="验证" width="100"><template #default><el-tag type="success" size="small">已通过</el-tag></template></el-table-column>
        <el-table-column label="操作" width="90"><template #default="{ row }"><el-button text type="primary" @click="applyLocatorSuggestion(row)">采用</el-button></template></el-table-column>
      </el-table>
      <el-empty v-if="!locatorSuggestions.length" description="没有通过全部校验的候选定位器" />
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowDown, ArrowLeft, ArrowUp, CircleCheck, FolderChecked, Plus, Search, Setting, VideoCamera, VideoPause, VideoPlay, View } from '@element-plus/icons-vue'
import uiAutomationApi from '@/api/ui-automation'
import autoTestRequest from '@/utils/autoTestRequest'
import ActionPicker from '@/components/ui-automation/ActionPicker.vue'
import StepInspector from '@/components/ui-automation/StepInspector.vue'
import RunResultDrawer from '@/components/ui-automation/RunResultDrawer.vue'
import { ACTION_MAP, actionLabel, inputKind, needsLocator } from '@/components/ui-automation/action-catalog'

const route=useRoute(), router=useRouter()
let caseId=Number(route.params.id)
const caseData=ref(null),steps=ref([]),loading=ref(false),saving=ref(false),running=ref(false)
const selectedStepId=ref(''),pickerVisible=ref(false),insertIndex=ref(0),errors=ref({})
const recording=ref(false),authCaptureMode=ref(false),refreshAuthStateId=ref(null),recorderMode=ref('record'),recorderUrl=ref(''),consoleLogs=ref([]),networkLogs=ref([]),executionLogs=ref([]),variableSnapshot=ref({}),debugTab=ref('execution')
const activeCaptureId=ref(null),completedCaptureId=ref(null),capturedExchangeCount=ref(0)
const capturePaused=ref(false),captureConfig=ref({domain_allowlist_text:'',path_exclude_text:''})
const capturePendingCount=ref(0),captureSyncFailed=ref(false),captureSyncing=ref(false)
let captureQueue=[],captureFlushTimer=null,captureFlushInFlight=null,captureWarningShown=false
const showRunResult=ref(false),runResultDrawer=ref(null)
const locatorSuggestionVisible=ref(false),locatorSuggestionLoading=ref(false),locatorSuggestions=ref([])
const environments=ref([]),selectedEnvironmentId=ref(null),authStates=ref([]),selectedAuthStateId=ref(null),authCheckResults=ref({}),checkingAuthId=ref(null)
const desktopReady=computed(()=>typeof window!=='undefined'&&typeof window.testmaster?.execution?.runCase==='function'&&typeof window.testmaster?.recorder?.start==='function')
const captureRetryLabel=computed(()=>capturePendingCount.value?`重试同步 ${capturePendingCount.value} 条接口记录`:'重试完成抓包')
const selectedIndex=computed(()=>steps.value.findIndex(step=>step.id===selectedStepId.value))
const selectedStep=computed(()=>selectedIndex.value>=0?steps.value[selectedIndex.value]:null)

function now(){return new Date().toLocaleTimeString('zh-CN',{hour12:false})}
function actionIcon(type){return ACTION_MAP[type]?.icon||CircleCheck}
function newLocator(){return{strategy:'test_id',value:'',options:{},fallbacks:[],framePath:[]}}
function createStep(type){const action=ACTION_MAP[type];const input=action?.input?(action.input==='viewport'?{width:1280,height:720}:action.input==='targetLocator'?{targetLocator:newLocator()}:action.input==='downloadOptions'?{expectedFilename:'',minBytes:1,containsText:'',variable:'downloadPath'}:{[action.input]:action.input==='state'?'load':action.input==='ms'?1000:action.input==='index'?'last':''}):null;return{id:crypto.randomUUID(),order:Date.now(),name:actionLabel(type),type,enabled:true,breakpoint:false,locator:needsLocator(type)?newLocator():null,input,timeout_ms:null,retry:{count:0,delay_ms:0},continue_on_failure:false,screenshot:'on-failure',condition:null,children:[]}}
function normalizeStep(step){const copy=JSON.parse(JSON.stringify(step));copy.id=copy.id||crypto.randomUUID();copy.name=copy.name||actionLabel(copy.type);copy.retry=copy.retry||{count:0,delay_ms:0};copy.screenshot=copy.screenshot||'on-failure';if(needsLocator(copy.type)&&!copy.locator)copy.locator=newLocator();if(copy.inputValue!==undefined&&!copy.input){const kind=inputKind(copy.type);if(kind)copy.input={[kind]:copy.inputValue};delete copy.inputValue}return copy}
function openPicker(index){insertIndex.value=index;pickerVisible.value=true}
function insertAction(type){const step=createStep(type);steps.value.splice(insertIndex.value,0,step);selectedStepId.value=step.id}
function selectStep(id){selectedStepId.value=id}
function moveStep(index,direction){const target=index+direction;if(target<0||target>=steps.value.length)return;[steps.value[index],steps.value[target]]=[steps.value[target],steps.value[index]]}
function handleStepCommand(command,index){if(command==='delete')steps.value.splice(index,1)}
function deleteSelected(){if(selectedIndex.value<0)return;steps.value.splice(selectedIndex.value,1);selectedStepId.value=steps.value[Math.min(selectedIndex.value,steps.value.length-1)]?.id||''}
function duplicateSelected(){if(!selectedStep.value)return;const copy=JSON.parse(JSON.stringify(selectedStep.value));copy.id=crypto.randomUUID();copy.name=`${copy.name} - 副本`;steps.value.splice(selectedIndex.value+1,0,copy);selectedStepId.value=copy.id}
async function clearSteps(){try{await ElMessageBox.confirm('确认清空全部步骤？','清空流程',{type:'warning'});steps.value=[];selectedStepId.value=''}catch{}}
function stepDescription(step){if(step.type==='goto')return step.input?.url||'未填写页面地址';if(step.locator){const loc=step.locator;return loc.strategy==='role'?`${loc.value} · ${loc.options?.name||''}`:`${locatorLabel(loc.strategy)} · ${loc.value||'未填写'}`}const kind=inputKind(step.type);return kind&&step.input?.[kind]!==undefined?String(step.input[kind]):actionLabel(step.type)}
function locatorLabel(strategy){return({test_id:'测试标识',role:'控件角色',label:'表单标签',placeholder:'提示文字',text:'页面文字',css:'CSS',xpath:'XPath'})[strategy]||strategy}

async function loadCase(){loading.value=true;try{const data=await uiAutomationApi.getCase(caseId);caseData.value=data;recorderUrl.value=data.base_url||'';steps.value=(data.steps||[]).map(normalizeStep);selectedStepId.value=steps.value[0]?.id||''}catch(error){ElMessage.error(`用例加载失败：${friendlyError(error)}`)}finally{loading.value=false}}
function validate(){const next={};const enabled=steps.value.filter(step=>step.enabled);if(!enabled.length){ElMessage.warning('请至少添加一个启用的步骤');return false}for(const step of enabled){if(needsLocator(step.type)&&!step.locator?.value?.trim())next[step.id]='请配置目标元素';const kind=inputKind(step.type);if(kind==='viewport'&&(!step.input?.width||!step.input?.height))next[step.id]='请填写浏览器宽度和高度';else if(kind==='targetLocator'&&!step.input?.targetLocator?.value?.trim())next[step.id]='请配置拖拽目标元素';else if(kind==='files'&&!(step.input?.paths||[]).length)next[step.id]='请选择回放时上传的测试文件';else if(kind&&kind!=='state'&&kind!=='files'&&step.input?.[kind]!==0&&!String(step.input?.[kind]??'').trim())next[step.id]='请填写输入数据';if(step.locator?.strategy==='role'&&!step.locator?.options?.name)next[step.id]='请填写控件名称'}errors.value=next;const first=Object.keys(next)[0];if(first){selectedStepId.value=first;ElMessage.error('流程存在未完成步骤，请查看红色提示');return false}return true}
function snapshot(){return JSON.parse(JSON.stringify({case_id:caseId,name:caseData.value.name,base_url:caseData.value.base_url?.trim()||null,default_timeout_ms:caseData.value.default_timeout_ms||10000,navigation_timeout_ms:caseData.value.navigation_timeout_ms||30000,steps:steps.value.map((step,index)=>({...step,order:(index+1)*10}))}))}
async function persist(){await Promise.all([uiAutomationApi.updateCase(caseId,{base_url:caseData.value.base_url?.trim()||null,default_timeout_ms:caseData.value.default_timeout_ms,navigation_timeout_ms:caseData.value.navigation_timeout_ms}),uiAutomationApi.batchSaveSteps(caseId,snapshot().steps)])}
async function saveAll(){if(!validate())return false;saving.value=true;try{await persist();ElMessage.success('用例已保存');return true}catch(error){ElMessage.error(`保存失败：${friendlyError(error)}`);return false}finally{saving.value=false}}
async function loadExecutionProfiles(){
  try{
    const [envItems,stateItems]=await Promise.all([autoTestRequest.get('/auto-test/environments'),window.testmaster?.authStates?.list?.()||Promise.resolve([])])
    environments.value=Array.isArray(envItems)?envItems:[]
    authStates.value=Array.isArray(stateItems)?stateItems:[]
    const remembered=localStorage.getItem('testmaster:ui-auth-state:'+caseId)
    if(remembered&&authStates.value.some(item=>item.id===remembered))selectedAuthStateId.value=remembered
    else if(selectedAuthStateId.value&&!authStates.value.some(item=>item.id===selectedAuthStateId.value))selectedAuthStateId.value=null
    if(selectedEnvironmentId.value==null)selectedEnvironmentId.value=environments.value.find(item=>item.is_default)?.id||null
  }catch(error){ElMessage.warning('运行配置加载失败：'+friendlyError(error))}
}
function formatAuthTime(value){if(!value)return '未知';return new Date(value).toLocaleString('zh-CN',{hour12:false})}
function currentAuthValidationUrl(){const first=steps.value.find(step=>step.enabled!==false&&step.type==='goto')?.input?.url||'';if(/^https?:\/\//i.test(first))return first;if(caseData.value?.base_url&&first){try{return new URL(first,caseData.value.base_url).toString()}catch{}}return /^https?:\/\//i.test(caseData.value?.base_url||'')?caseData.value.base_url:''}
async function checkAuthState(item){checkingAuthId.value=item.id;try{const result=await window.testmaster.authStates.validate(item.id,currentAuthValidationUrl());authCheckResults.value={...authCheckResults.value,[item.id]:result};ElMessage[result.valid?'success':'error'](item.name+'：'+result.reason)}catch(error){ElMessage.error('登录态检查失败：'+friendlyError(error))}finally{checkingAuthId.value=null}}
async function removeAuthState(item){try{await ElMessageBox.confirm('删除登录态“'+item.name+'”？删除后使用它的用例需要重新选择。','删除登录态',{type:'warning'});await window.testmaster.authStates.delete(item.id);localStorage.removeItem('testmaster:ui-auth-state:'+caseId);if(selectedAuthStateId.value===item.id)selectedAuthStateId.value=null;const next={...authCheckResults.value};delete next[item.id];authCheckResults.value=next;await loadExecutionProfiles();ElMessage.success('登录态已删除')}catch(error){if(error!=='cancel'&&error!=='close')ElMessage.error(friendlyError(error))}}
async function startAuthCapture(refreshExisting=false){
  if(!desktopReady.value){ElMessage.error('请使用 TestMaster 桌面版管理登录态');return}
  const url=recorderUrl.value.trim()||caseData.value?.base_url?.trim()
  if(!/^https?:\/\//i.test(url)){ElMessage.warning('请先填写登录页面或被测系统的完整地址');return}
  try{
    refreshAuthStateId.value=refreshExisting?selectedAuthStateId.value:null
    await window.testmaster.recorder.start({url,slowMo:0,authStateId:refreshAuthStateId.value},()=>{})
    authCaptureMode.value=true;recording.value=true
    ElMessage.success(refreshExisting?'已载入原登录态，请完成验证码或重新登录后保存':'请在浏览器完成验证码登录，登录过程不会加入测试步骤')
  }catch(error){refreshAuthStateId.value=null;ElMessage.error(`登录窗口启动失败：${friendlyError(error)}`)}
}
async function cancelAuthCapture(){
  try{await window.testmaster.recorder.stop()}catch{}
  authCaptureMode.value=false;recording.value=false;refreshAuthStateId.value=null
}
async function saveCurrentAuthState(){
  if(!authCaptureMode.value)return
  try{
    let name=authStates.value.find(item=>item.id===refreshAuthStateId.value)?.name
    if(!name){const answer=await ElMessageBox.prompt('给这份登录态起一个名称，例如：商城测试账号','保存登录态',{inputPattern:/\S+/,inputErrorMessage:'请输入名称'});name=answer.value.trim()}
    const saved=await window.testmaster.authStates.saveCurrent(name,refreshAuthStateId.value||undefined)
    await window.testmaster.recorder.stop();authCaptureMode.value=false;recording.value=false;refreshAuthStateId.value=null
    await loadExecutionProfiles();selectedAuthStateId.value=saved.id
    ElMessage.success('登录态已加密保存。后续运行会直接复用，通常无需再次处理验证码')
  }catch(error){if(error!=='cancel'&&error!=='close')ElMessage.error(friendlyError(error))}
}
async function executeCase(debugMode=false){if(!validate()||!desktopReady.value)return;saving.value=true;running.value=true;executionLogs.value=[];try{await persist();const version=await uiAutomationApi.createVersion(caseId,'运行前自动保存');showRunResult.value=true;await runResultDrawer.value.startRun({caseSnapshot:snapshot(),runContext:{caseId,caseVersionId:version.id},debugMode,environmentId:selectedEnvironmentId.value,authStateId:selectedAuthStateId.value,onEvent:event=>{executionLogs.value.push({time:now(),level:event.type?.includes('fail')?'error':'info',message:formatExecutionEvent(event)});if(event.type==='run:paused'){variableSnapshot.value=event.variables||{};debugTab.value='execution'};if(event.type==='console')consoleLogs.value.push({...event,time:now()});if(event.type==='network')networkLogs.value.push({...event,time:now()})}})}catch(error){ElMessage.error(`运行失败：${friendlyError(error)}`)}finally{saving.value=false;running.value=false}}

async function startRecording(){
  if(authCaptureMode.value)return
  if(!desktopReady.value){ElMessage.error('请使用 TestMaster 桌面版录制');return}
  const url=recorderUrl.value.trim()||caseData.value?.base_url?.trim()
  if(!/^https?:\/\//i.test(url)&&!url?.startsWith('data:')){ElMessage.warning('请输入完整的 http:// 或 https:// 地址');return}
  consoleLogs.value=[];networkLogs.value=[];captureQueue=[];capturePendingCount.value=0;captureSyncFailed.value=false;activeCaptureId.value=null;completedCaptureId.value=null;capturedExchangeCount.value=0;captureWarningShown=false;capturePaused.value=false
  try{const capture=await autoTestRequest.post('/auto-test/import/captures',{origin:'desktop_browser',source_url:url,capture_config:{domain_allowlist:parseCaptureRules(captureConfig.value.domain_allowlist_text),path_exclude:parseCaptureRules(captureConfig.value.path_exclude_text)}});activeCaptureId.value=capture.id}catch(error){captureWarningShown=true;ElMessage.warning('接口流量不会保存：'+friendlyError(error))}
  try{await window.testmaster.recorder.start({url,slowMo:50,authStateId:selectedAuthStateId.value},handleRecorderEvent);recording.value=true;recorderMode.value='record';ElMessage.success('录制已开始，请在打开的浏览器中操作')}catch(error){if(activeCaptureId.value)await autoTestRequest.post(`/auto-test/import/captures/${activeCaptureId.value}/complete`).catch(()=>{});activeCaptureId.value=null;ElMessage.error(`录制启动失败：${friendlyError(error)}`)}
}
function queueCaptureExchange(event){
  if(!activeCaptureId.value||capturePaused.value||!['xhr','fetch'].includes(event.resourceType))return
  captureQueue.push({method:event.method,url:event.url,status:event.status,resourceType:event.resourceType,requestHeaders:event.requestHeaders,requestBody:event.requestBody,responseHeaders:event.responseHeaders,responseBody:event.responseBody,timingMs:event.durationMs,pageUrl:event.pageUrl});capturePendingCount.value=captureQueue.length
  if(captureQueue.length>=20)void flushCapturedExchanges();else if(!captureFlushTimer)captureFlushTimer=window.setTimeout(()=>{captureFlushTimer=null;void flushCapturedExchanges()},800)
}
async function flushCapturedExchanges(){
  if(captureFlushInFlight){await captureFlushInFlight;return flushCapturedExchanges()}
  if(!activeCaptureId.value||!captureQueue.length)return
  const sessionId=activeCaptureId.value
  const batch=captureQueue.splice(0,100)
  capturePendingCount.value=captureQueue.length
  let succeeded=false
  captureSyncing.value=true
  captureFlushInFlight=autoTestRequest.post(`/auto-test/import/captures/${sessionId}/exchanges`,{exchanges:batch}).then(result=>{capturedExchangeCount.value+=result.accepted||0;succeeded=true;captureSyncFailed.value=false}).catch(error=>{captureQueue.unshift(...batch);captureSyncFailed.value=true;if(!captureWarningShown){captureWarningShown=true;ElMessage.warning('接口流量暂未同步：'+friendlyError(error))}}).finally(()=>{capturePendingCount.value=captureQueue.length;captureSyncing.value=false;captureFlushInFlight=null})
  await captureFlushInFlight
  if(succeeded&&activeCaptureId.value===sessionId&&captureQueue.length)await flushCapturedExchanges()
}
function handleRecorderEvent(event){if(event.type==='action'){const step=normalizeStep(event.step);const last=steps.value[steps.value.length-1];if(event.replaceLast&&last?.type===step.type&&JSON.stringify(last.locator)===JSON.stringify(step.locator)){step.id=last.id;steps.value.splice(steps.value.length-1,1,step)}else if(event.insertBeforeLast&&steps.value.length){steps.value.splice(steps.value.length-1,0,step)}else{steps.value.push(step)}selectedStepId.value=step.id}if(event.type==='console')consoleLogs.value.push({...event,time:now()});if(event.type==='network'){networkLogs.value.push({...event,time:now()});queueCaptureExchange(event)}if(event.type==='mode')recorderMode.value=event.mode;if(event.type==='error')ElMessage.error(event.message)}
async function setRecorderMode(mode){try{await window.testmaster.recorder.setMode(mode);recorderMode.value=mode}catch(error){ElMessage.error(friendlyError(error))}}
function parseCaptureRules(value){return String(value||'').split(/[\n,]+/).map(item=>item.trim()).filter(Boolean)}
async function toggleCapturePaused(){if(!activeCaptureId.value)return;try{if(!capturePaused.value)await flushCapturedExchanges();const action=capturePaused.value?'resume':'pause';await autoTestRequest.post(`/auto-test/import/captures/${activeCaptureId.value}/${action}`);capturePaused.value=!capturePaused.value;ElMessage.success(capturePaused.value?'接口采集已暂停':'接口采集已恢复')}catch(error){ElMessage.error('切换采集状态失败：'+friendlyError(error))}}
async function finishCaptureSession(){
  if(!activeCaptureId.value)return true
  try{
    if(capturePaused.value){await autoTestRequest.post(`/auto-test/import/captures/${activeCaptureId.value}/resume`);capturePaused.value=false}
    await flushCapturedExchanges()
    if(captureQueue.length){captureSyncFailed.value=true;return false}
    const sessionId=activeCaptureId.value
    await autoTestRequest.post(`/auto-test/import/captures/${sessionId}/complete`)
    completedCaptureId.value=sessionId;activeCaptureId.value=null;capturePaused.value=false;captureSyncFailed.value=false
    return true
  }catch(error){captureSyncFailed.value=true;throw error}
}
async function retryPendingCapture(){
  try{const completed=await finishCaptureSession();if(completed)ElMessage.success('接口流量已同步并完成抓包')}catch(error){ElMessage.error('重试同步失败：'+friendlyError(error))}
}
async function discardPendingCapture(){
  if(!activeCaptureId.value)return
  try{await ElMessageBox.confirm('未同步的接口记录将不再保存，确定放弃本次抓包？','放弃未同步抓包',{type:'warning'});await autoTestRequest.post(`/auto-test/import/captures/${activeCaptureId.value}/cancel`,{reason:'browser capture ended before pending exchanges were synchronized'});captureQueue=[];capturePendingCount.value=0;captureSyncFailed.value=false;activeCaptureId.value=null;capturePaused.value=false;ElMessage.success('已放弃未同步抓包')}catch(error){if(error!=='cancel'&&error!=='close')ElMessage.error('放弃抓包失败：'+friendlyError(error))}
}
async function stopRecording(){let stopError=null;try{await window.testmaster.recorder.stop()}catch(error){stopError=error}recording.value=false;recorderMode.value='record';try{const completed=await finishCaptureSession();if(completed)ElMessage.success(`录制完成，已生成 ${steps.value.length} 个步骤`);else ElMessage.warning('浏览器已停止，但仍有接口记录等待同步；请恢复网络后重试，或明确放弃抓包')}catch(error){ElMessage.warning('浏览器已停止，接口抓包尚未完成：'+friendlyError(error))}if(stopError)ElMessage.error(friendlyError(stopError))}
function openCaptureImport(){if(completedCaptureId.value)router.push({path:'/import-center',query:{captureId:completedCaptureId.value}})}
async function validateSelectedLocator(){
  if(!selectedStep.value?.locator)return
  if(!recording.value){ElMessage.warning('请先开始录制并打开被测页面，再验证定位器');return}
  try{
    const result=await window.testmaster.recorder.validateLocator(JSON.parse(JSON.stringify(selectedStep.value.locator)))
    if(result.count===1) ElMessage.success('定位成功：精确匹配 1 个元素'+(result.preview?' · '+result.preview:''))
    else if(result.count===0) ElMessage.error('没有找到元素，请更换定位方式或定位值')
    else ElMessage.warning('定位不唯一：匹配到 '+result.count+' 个元素')
  }catch(error){ElMessage.error('定位验证失败：'+friendlyError(error))}
}
function locatorUrlMatches(currentUrl){
  const expected=currentAuthValidationUrl()||recorderUrl.value
  try{return new URL(currentUrl).origin===new URL(expected).origin}catch{return false}
}
async function requestLocatorSuggestions(){
  if(!selectedStep.value?.locator||!recording.value)return
  locatorSuggestionLoading.value=true
  try{
    const raw=[selectedStep.value.locator,...(selectedStep.value.locator.fallbacks||[])]
    const seen=new Set(),probes=[]
    let currentUrl=''
    for(const locator of raw){
      const key=JSON.stringify([locator.strategy,locator.value,locator.options||{},locator.framePath||[]])
      if(seen.has(key))continue
      seen.add(key)
      const validation=await window.testmaster.recorder.validateLocator(JSON.parse(JSON.stringify(locator)))
      currentUrl=currentUrl||validation.currentUrl||''
      probes.push({
        strategy:locator.strategy,value:locator.value,options:locator.options||{},
        match_count:validation.count,visible:validation.visible,actionable:validation.actionable,
        dry_run_passed:validation.dryRunPassed,url_matches:locatorUrlMatches(validation.currentUrl)
      })
    }
    const response=await uiAutomationApi.suggestLocators(caseId,{
      step_id:selectedStep.value.id,locator_probes:probes,
      current_url:currentUrl,
      login_state_matches:true
    })
    locatorSuggestions.value=response.suggestions||[]
    locatorSuggestionVisible.value=true
  }catch(error){ElMessage.error('定位建议生成失败：'+friendlyError(error))}finally{locatorSuggestionLoading.value=false}
}
async function applyLocatorSuggestion(suggestion){
  try{
    await ElMessageBox.confirm('采用该定位器并创建一个新的用例版本？','确认定位器建议',{type:'warning'})
    selectedStep.value.locator={...suggestion.locator,fallbacks:[],framePath:selectedStep.value.locator?.framePath||[]}
    await persist()
    await uiAutomationApi.createVersion(caseId,'人工确认并采用定位器建议')
    locatorSuggestionVisible.value=false
    ElMessage.success('定位器已更新并创建新版本')
  }catch(error){if(error!=='cancel'&&error!=='close')ElMessage.error(friendlyError(error))}
}
function formatExecutionEvent(event){if(event.type==='run:paused')return '已暂停在：'+event.stepName;if(event.type==='step:start')return '开始执行：'+event.stepName;if(event.type==='step:pass')return '步骤通过';if(event.type==='step:fail')return '步骤失败：'+event.error;if(event.type==='run:finish')return '运行结束：'+event.status;return event.message||event.type}
function friendlyError(error){const message=error?.message||'未知错误';if(/Network Error|Failed to fetch|ECONNREFUSED/i.test(message))return'后台服务未连接';if(/timeout/i.test(message))return'操作超时，请检查页面或定位器';return message}
function goBack(){router.push('/ui-automation/cases')}
watch(()=>route.params.id,async value=>{
  const nextCaseId=Number(value)
  if(!Number.isInteger(nextCaseId)||nextCaseId<=0||nextCaseId===caseId)return
  if(recording.value){await stopRecording();authCaptureMode.value=false;refreshAuthStateId.value=null}
  caseId=nextCaseId
  caseData.value=null;steps.value=[];selectedStepId.value='';errors.value={};selectedAuthStateId.value=null
  executionLogs.value=[];consoleLogs.value=[];networkLogs.value=[];variableSnapshot.value={}
  showRunResult.value=false
  await Promise.all([loadCase(),loadExecutionProfiles()])
})
watch(selectedAuthStateId,value=>{
  const key='testmaster:ui-auth-state:'+caseId
  if(value)localStorage.setItem(key,value);else localStorage.removeItem(key)
})
onMounted(async()=>{await Promise.all([loadCase(),loadExecutionProfiles()])})
onBeforeUnmount(()=>{if(recording.value)void stopRecording()})
</script>

<style scoped>
.automation-studio{display:flex;flex-direction:column;gap:12px;min-width:900px;color:#17212b}.studio-toolbar,.case-heading,.case-heading>div,.toolbar-actions,.recording-bar,.case-context,.canvas-header,.canvas-header>div,.step-tools,.recording-indicator{display:flex;align-items:center}.studio-toolbar{justify-content:space-between;padding-bottom:12px;border-bottom:1px solid #dbe3de}.case-heading{gap:12px}.case-heading>div{gap:12px}.case-heading h1{margin:0;font-size:20px}.engine-state{color:#b42318;font-size:12px}.engine-state.ready{color:#28724f}.engine-state i,.recording-indicator i{display:inline-block;width:7px;height:7px;border-radius:50%;background:currentColor;margin-right:5px}.toolbar-actions{gap:8px}.recording-bar{min-height:48px;gap:8px;padding:8px 12px;background:#fff;border:1px solid #dbe3de;border-radius:6px}.recording-bar.active{border-color:#e5484d;background:#fffafa}.record-address{flex:1}.recording-indicator{color:#c52b32;font-weight:700;font-size:12px}.auth-capture-tip{font-size:12px;color:#5f6b64;flex:1}.auth-state-manager{display:flex;flex-direction:column;gap:8px;max-height:340px;overflow:auto}.auth-row{display:grid;grid-template-columns:1fr auto auto;gap:8px;align-items:center;padding:8px;border-bottom:1px solid #edf0ee}.auth-row>div{display:flex;flex-direction:column;min-width:0}.auth-row small{color:#77827b;margin-top:2px}.auth-health{font-size:11px;margin-top:3px}.auth-health.ok{color:#28724f}.auth-health.bad{color:#b42318}.auth-empty{padding:18px;text-align:center;color:#77827b}.recording-indicator i{animation:pulse 1.2s infinite}.case-context{gap:10px;padding:10px 14px;background:#fff;border:1px solid #dbe3de;border-radius:6px}.case-context label{font-size:12px;font-weight:700}.case-context .el-input{max-width:640px}.studio-workspace{display:flex;min-height:570px;background:#fff;border:1px solid #dbe3de;border-radius:6px;overflow:hidden}.flow-canvas{flex:1;min-width:0;padding:18px 22px;background:#f8faf9}.canvas-header{justify-content:space-between;margin-bottom:18px}.canvas-header h2{margin:0;font-size:17px}.canvas-header span{color:#748078;font-size:12px}.canvas-header>div{gap:8px}.empty-flow{min-height:430px;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center}.empty-flow>.el-icon{font-size:38px;color:#c52b32}.empty-flow h3{margin:14px 0 6px}.empty-flow p{max-width:540px;margin:0 0 18px;color:#69756e;line-height:1.7}.flow-list{max-width:900px;margin:0 auto}.flow-step{display:grid;grid-template-columns:34px 34px minmax(0,1fr) auto auto;gap:10px;align-items:center;padding:11px 12px;background:#fff;border:1px solid #d8e1db;border-radius:6px;cursor:pointer}.flow-step:hover{border-color:#8bb39e}.flow-step.selected{border-color:#28724f;box-shadow:0 0 0 2px rgba(40,114,79,.1)}.flow-step.invalid{border-color:#d33d43}.flow-step.disabled{opacity:.55}.step-sequence{width:28px;height:28px;display:grid;place-items:center;border-radius:50%;background:#e8f3ec;color:#28724f;font-weight:700}.step-icon{color:#28724f}.step-summary{min-width:0;display:flex;flex-direction:column}.step-summary strong{font-size:13px}.step-summary span{overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:#6e7a72;font-size:11px;margin-top:3px}.step-summary small{color:#c52b32;margin-top:3px}.step-badges{display:flex;gap:4px}.step-tools{gap:0}.insert-step{width:100%;height:24px;border:0;background:transparent;display:flex;align-items:center;justify-content:center;gap:5px;color:#859188;font-size:11px;cursor:pointer;opacity:.25}.insert-step:hover,.insert-step.first{opacity:1;color:#28724f}.insert-step.first{margin-bottom:5px}.debug-console{height:210px;background:#fff;border:1px solid #dbe3de;border-radius:6px;padding:0 14px;overflow:hidden}.debug-list{height:140px;overflow:auto;font-family:Consolas,monospace;font-size:11px}.debug-line{display:grid;grid-template-columns:80px 1fr;gap:8px;padding:5px;border-bottom:1px solid #eef1ef}.debug-line span{color:#879189}.debug-line.error strong{color:#b42318}@keyframes pulse{50%{opacity:.25}}@media(max-width:1150px){.inspector{width:300px}.recording-bar{flex-wrap:wrap}.record-address{flex-basis:100%}}
</style>












