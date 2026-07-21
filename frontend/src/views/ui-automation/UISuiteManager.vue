<template>
<div class="suite-page">
<header><div class="title"><el-button text @click="router.push('/ui-automation/cases')">返回用例</el-button><div><h1>回归套件</h1><span>多用例顺序执行与业务数据迭代</span></div></div><el-button type="primary" @click="createNew">新建套件</el-button></header>
<el-table v-loading="loading" :data="suites" stripe><el-table-column prop="name" label="套件名称" min-width="220"/><el-table-column label="用例" width="90"><template #default="{row}">{{ row.items?.filter(x=>x.enabled).length||0 }}</template></el-table-column><el-table-column label="失败策略" width="140"><template #default="{row}">{{ row.stop_on_first_failure?'首个失败即停止':'失败后继续' }}</template></el-table-column><el-table-column prop="updated_at" label="更新时间" width="180"><template #default="{row}">{{ date(row.updated_at) }}</template></el-table-column><el-table-column label="操作" width="280" fixed="right"><template #default="{row}"><el-button size="small" @click="edit(row)">编辑</el-button><el-button size="small" type="primary" :loading="runningId===row.id" @click="prepareRun(row)">运行</el-button><el-button size="small" @click="history(row)">记录</el-button><el-button size="small" type="danger" plain @click="remove(row)">删除</el-button></template></el-table-column></el-table><el-empty v-if="!loading&&!suites.length" description="暂无回归套件"/>
<el-dialog v-model="editVisible" :title="editingId?'编辑套件':'新建套件'" width="900px"><el-form label-position="top"><div class="grid"><el-form-item label="套件名称"><el-input v-model="form.name"/></el-form-item><el-form-item label="失败策略"><el-switch v-model="form.stop" active-text="首个失败即停止" inactive-text="失败后继续"/></el-form-item></div><el-form-item label="描述"><el-input v-model="form.description" type="textarea" :rows="2"/></el-form-item></el-form><div class="items-head"><strong>执行顺序</strong><el-button size="small" @click="addItem">添加用例</el-button></div>
<div v-for="(item,i) in form.items" :key="item.key" class="suite-item"><div class="item-line"><b>{{ i+1 }}</b><el-select v-model="item.case_id" filterable placeholder="选择 UI 用例" class="case-select"><el-option v-for="c in cases" :key="c.id" :label="c.name" :value="c.id"/></el-select><el-switch v-model="item.enabled" active-text="启用"/><el-button text :disabled="i===0" @click="move(i,-1)">上移</el-button><el-button text :disabled="i===form.items.length-1" @click="move(i,1)">下移</el-button><el-button text type="danger" @click="form.items.splice(i,1)">删除</el-button></div><div class="grid data"><el-form-item label="数据行（JSON 数组）"><el-input v-model="item.rows" type="textarea" :rows="3" placeholder='[{"username":"user1"}]'/></el-form-item><el-form-item label="固定变量（JSON 对象）"><el-input v-model="item.overrides" type="textarea" :rows="3" placeholder='{"tenant":"test"}'/></el-form-item></div></div>
<template #footer><el-button @click="editVisible=false">取消</el-button><el-button type="primary" :loading="saving" @click="save">保存</el-button></template></el-dialog>
<el-dialog v-model="runVisible" title="运行回归套件" width="620px"><el-form label-position="top"><el-form-item label="测试环境"><el-select v-model="run.environmentId" clearable placeholder="不使用环境" style="width:100%"><el-option v-for="e in environments" :key="e.id" :label="e.env_name||e.name" :value="e.id"/></el-select></el-form-item><el-form-item label="登录态"><el-select v-model="run.authStateId" clearable placeholder="每个用例重新登录" style="width:100%"><el-option v-for="s in authStates" :key="s.id" :label="s.name" :value="s.id"/></el-select></el-form-item></el-form><div v-if="progress.total" class="progress"><el-progress :percentage="Math.round(progress.done/progress.total*100)"/><p>{{ progress.message }}</p></div><template #footer><el-button @click="runVisible=false" :disabled="runningId!==null">关闭</el-button><el-button v-if="runningId!==null" type="danger" plain @click="cancelSuiteRun">停止运行</el-button><el-button v-else type="primary" @click="execute">开始运行</el-button></template></el-dialog>
<el-drawer v-model="historyVisible" title="套件运行记录" size="65%"><el-table v-loading="historyLoading" :data="runs" stripe><el-table-column prop="status" label="状态" width="100"><template #default="{row}"><el-tag :type="tag(row.status)">{{ label(row.status) }}</el-tag></template></el-table-column><el-table-column label="统计"><template #default="{row}">{{ row.passed_steps }}/{{ row.total_steps }} 通过，{{ row.failed_steps }} 失败，{{ row.skipped_steps }} 跳过</template></el-table-column><el-table-column label="开始时间" width="190"><template #default="{row}">{{ date(row.started_at||row.queued_at) }}</template></el-table-column><el-table-column label="结束时间" width="190"><template #default="{row}">{{ date(row.finished_at) }}</template></el-table-column></el-table></el-drawer>
</div>
</template>
<script setup>
import{onMounted,reactive,ref}from'vue'
import{useRouter}from'vue-router'
import{ElMessage,ElMessageBox}from'element-plus'
import api from'@/api/ui-automation'
import autoTestRequest from'@/utils/autoTestRequest'
import{getServerUrl}from'@/utils/server-config'
const router=useRouter(),loading=ref(false),saving=ref(false),suites=ref([]),cases=ref([]),environments=ref([]),authStates=ref([]),editVisible=ref(false),editingId=ref(null),runVisible=ref(false),selected=ref(null),runningId=ref(null),historyVisible=ref(false),historyLoading=ref(false),runs=ref([]),activeCorrelationId=ref(''),cancelRequested=ref(false)
const form=reactive({name:'',description:'',stop:false,items:[]}),run=reactive({environmentId:null,authStateId:null}),progress=reactive({total:0,done:0,message:''})
const date=v=>v?new Date(v).toLocaleString('zh-CN'):'—',label=v=>({queued:'排队中',running:'运行中',passed:'通过',failed:'失败',error:'错误'})[v]||v,tag=v=>({passed:'success',failed:'danger',error:'danger',running:'warning'})[v]||'info'
const item=()=>({key:crypto.randomUUID(),case_id:null,enabled:true,rows:'[{}]',overrides:'{}'})
function createNew(){editingId.value=null;Object.assign(form,{name:'',description:'',stop:false,items:[item()]});editVisible.value=true}
function addItem(){form.items.push(item())}
function move(i,d){const j=i+d;if(j<0||j>=form.items.length)return;[form.items[i],form.items[j]]=[form.items[j],form.items[i]]}
async function load(){loading.value=true;try{const[s,c,e,a]=await Promise.all([api.listSuites(),api.listCases({page_size:1000}),autoTestRequest.get('/auto-test/environments'),window.testmaster?.authStates?.list?.()||Promise.resolve([])]);suites.value=s.items||[];cases.value=c.items||[];environments.value=Array.isArray(e)?e:[];authStates.value=a||[];if(run.environmentId==null)run.environmentId=environments.value.find(x=>x.is_default)?.id||null}catch(e){ElMessage.error(e.message)}finally{loading.value=false}}
async function edit(row){const s=await api.getSuite(row.id);editingId.value=s.id;form.name=s.name;form.description=s.description||'';form.stop=s.stop_on_first_failure;form.items=(s.items||[]).map(x=>({key:crypto.randomUUID(),case_id:x.case_id,enabled:x.enabled,rows:JSON.stringify(x.data_source?.rows||[{}],null,2),overrides:JSON.stringify(x.overrides||{},null,2)}));if(!form.items.length)addItem();editVisible.value=true}
async function save(){if(!form.name.trim()){ElMessage.warning('请输入套件名称');return}let values;try{values=form.items.map((x,i)=>{const rows=JSON.parse(x.rows||'[{}]'),overrides=JSON.parse(x.overrides||'{}');if(!x.case_id)throw Error('第 '+(i+1)+' 项未选择用例');if(!Array.isArray(rows)||!rows.length)throw Error('第 '+(i+1)+' 项数据必须是非空数组');return{case_id:x.case_id,order:(i+1)*10,enabled:x.enabled,data_source:{rows},overrides}})}catch(e){ElMessage.error(e.message);return}saving.value=true;try{const s=editingId.value?await api.updateSuite(editingId.value,{name:form.name,description:form.description,stop_on_first_failure:form.stop}):await api.createSuite({name:form.name,description:form.description,stop_on_first_failure:form.stop});await api.replaceSuiteItems(s.id,values);ElMessage.success('套件已保存');editVisible.value=false;await load()}catch(e){ElMessage.error(e.message)}finally{saving.value=false}}
async function remove(row){try{await ElMessageBox.confirm('确认删除套件“'+row.name+'”？','删除套件',{type:'warning'});await api.deleteSuite(row.id);await load()}catch(e){if(e!=='cancel')ElMessage.error(e.message)}}
function prepareRun(row){selected.value=row;Object.assign(progress,{total:0,done:0,message:''});runVisible.value=true}
async function upload(runRecord,result){const paths=[...(result.stepResults||[]).map(x=>x.screenshotPath).filter(Boolean),result.tracePath,result.videoPath].filter(Boolean);for(const p of[...new Set(paths)]){const f=await window.testmaster.artifacts.read(p),type=p.endsWith('.zip')?'trace':p.endsWith('.webm')?'video':'screenshot',mime=type==='trace'?'application/zip':type==='video'?'video/webm':'image/png';await api.uploadSharedArtifact(runRecord,f,type,mime)}}
function authValidationUrl(snapshot){const first=(snapshot.steps||[]).find(step=>step.enabled!==false&&step.type==='goto')?.input?.url||'';if(/^https?:\/\//i.test(first))return first;if(snapshot.base_url&&first){try{return new URL(first,snapshot.base_url).toString()}catch{}}return /^https?:\/\//i.test(snapshot.base_url||'')?snapshot.base_url:''}
async function validateSuiteAuth(plan){if(!run.authStateId)return;const checked=new Set();for(const entry of plan.entries){const url=authValidationUrl(entry.snapshot);if(!url||checked.has(url))continue;checked.add(url);const result=await window.testmaster.authStates.validate(run.authStateId,url);if(result.valid===false)throw Error('用例“'+entry.case_name+'”登录态不可用：'+result.reason+'。请先更新登录态')}}
async function execute(){
  if(!selected.value||runningId.value!==null)return
  runningId.value=selected.value.id
  cancelRequested.value=false
  activeCorrelationId.value=''
  let record=null,seq=1,passed=0,failed=0,terminalSent=false
  const send=async events=>{
    if(!record)return
    await api.appendRunEvents(record.id,events.map(x=>({...x,sequence:seq++})))
  }
  const finish=async(status,error)=>{
    if(!record||terminalSent)return
    terminalSent=true
    await send([{type:'run:finish',status,passedSteps:passed,failedSteps:failed,error}])
  }
  try{
    const plan=await api.getSuiteExecutionPlan(selected.value.id)
    await validateSuiteAuth(plan)
    record=await api.createRun({suite_id:plan.suite_id,environment_id:run.environmentId,trigger_type:'manual',client_run_key:crypto.randomUUID()})
    await send([{type:'run:start',totalSteps:record.total_steps}])
    progress.total=plan.entries.length
    for(let i=0;i<plan.entries.length;i++){
      if(cancelRequested.value)break
      const e=plan.entries[i],captured=[]
      progress.message='正在执行：'+e.case_name+'（数据 '+(e.iteration+1)+'）'
      const opts={headless:false,traceOnFailure:true,screenshotsOnFailure:true,authStateId:run.authStateId,variables:e.variables,onEvent:x=>captured.push(x)}
      if(run.environmentId!=null)opts.runtimeConfigRequest={serverUrl:getServerUrl(),token:localStorage.getItem('token')||'',environmentId:run.environmentId}
      const execution=window.testmaster.execution.runCase(e.snapshot,opts)
      activeCorrelationId.value=execution.correlationId
      const result=await execution.promise
      activeCorrelationId.value=''
      const prefix=e.case_id+':'+e.iteration+':'
      const events=captured.filter(x=>!['run:start','run:finish','run:paused','run:resumed'].includes(x.type)).map(x=>x.stepId?{...x,stepId:prefix+x.stepId}:x)
      if(events.length)await send(events)
      await upload(record.id,result)
      passed+=result.passedSteps
      failed+=result.failedSteps
      progress.done=i+1
      if(cancelRequested.value||result.status==='cancelled')break
      if(result.status!=='passed'&&plan.stop_on_first_failure)break
    }
    const status=cancelRequested.value?'cancelled':failed?'failed':'passed'
    await finish(status)
    progress.message=status==='passed'?'套件运行通过':'套件运行失败'
    ElMessage[status==='passed'?'success':'error'](progress.message)
    await load()
  }catch(e){
    await finish('infra_error',e?.message||'Desktop suite execution failed').catch(()=>{})
    ElMessage.error('套件运行失败：'+e.message)
  }finally{activeCorrelationId.value='';runningId.value=null}
}
async function cancelSuiteRun(){
  cancelRequested.value=true
  progress.message='正在停止当前用例，后续用例不会执行'
  if(!activeCorrelationId.value)return
  try{await window.testmaster.execution.cancel(activeCorrelationId.value)}catch(e){ElMessage.error('停止运行失败：'+e.message)}
}
async function history(row){historyVisible.value=true;historyLoading.value=true;try{runs.value=(await api.listRuns({suite_id:row.id,page_size:100})).items||[]}catch(e){ElMessage.error(e.message)}finally{historyLoading.value=false}}
onMounted(load)
</script>
<style scoped>
.suite-page{padding:20px}header,.title,.items-head,.item-line{display:flex;align-items:center}header{justify-content:space-between;margin-bottom:20px}.title{gap:12px}.title h1{margin:0;font-size:20px}.title span{font-size:12px;color:#69756e}.grid{display:grid;grid-template-columns:1fr 1fr;gap:14px}.items-head{justify-content:space-between;margin:10px 0}.suite-item{padding:12px;margin-bottom:10px;border:1px solid #dbe3de;border-radius:6px;background:#f8faf9}.item-line{gap:8px}.item-line b{width:26px;height:26px;display:grid;place-items:center;border-radius:50%;background:#e8f3ec;color:#28724f}.case-select{flex:1}.data{margin:10px 34px 0}.progress{padding:12px;border:1px solid #dbe3de;border-radius:6px;background:#f8faf9}.progress p{margin:8px 0 0}
</style>

