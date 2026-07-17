import { chromium } from 'playwright';
const browser=await chromium.connectOverCDP('http://127.0.0.1:9333');
let suiteId=null,caseIds=[];
try{
 const page=browser.contexts()[0].pages()[0];await page.waitForTimeout(1200);
 const setup=await page.evaluate(async()=>{
  const headers={Authorization:'Bearer '+localStorage.getItem('token'),'Content-Type':'application/json'},base='http://127.0.0.1:5001/api/ui-automation';
  const req=async(path,options={})=>{const r=await fetch(base+path,{...options,headers});if(!r.ok)throw Error(path+':'+r.status+':'+await r.text());return r.json()};
  const make=async(name,titleTemplate,suffix)=>{const c=await req('/cases',{method:'POST',body:JSON.stringify({name})});const common={enabled:true,breakpoint:false,timeout_ms:3000,retry:{count:0,delay_ms:0},continue_on_failure:false,screenshot:'never',condition:null,children:[]};await req('/cases/'+c.id+'/steps',{method:'PUT',body:JSON.stringify({steps:[{...common,id:'suite-e2e-'+suffix+'-open-'+crypto.randomUUID(),order:10,name:'打开数据页',type:'goto',locator:null,input:{url:'data:text/html,<meta charset=utf-8><title>'+titleTemplate+'</title><h1>'+titleTemplate+'</h1>'}},{...common,id:'suite-e2e-'+suffix+'-assert-'+crypto.randomUUID(),order:20,name:'检查标题',type:'assert_title',locator:null,input:{expected:titleTemplate}}]})});const v=await req('/cases/'+c.id+'/versions',{method:'POST',body:'{}'});return{c,v}};
  const a=await make('套件数据验收用例','{{title}}','a'),b=await make('套件结算验收用例','Checkout','b');
  const name='桌面数据驱动套件-'+Date.now(),s=await req('/suites',{method:'POST',body:JSON.stringify({name,stop_on_first_failure:true})});
  await req('/suites/'+s.id+'/items',{method:'PUT',body:JSON.stringify([{case_id:a.c.id,pinned_version_id:a.v.id,order:10,enabled:true,data_source:{rows:[{title:'ProductOne'},{title:'ProductTwo'}]},overrides:{}},{case_id:b.c.id,pinned_version_id:b.v.id,order:20,enabled:true,data_source:{rows:[{}]},overrides:{}}])});
  return{suiteId:s.id,caseIds:[a.c.id,b.c.id],name};
 });
 suiteId=setup.suiteId;caseIds=setup.caseIds;
 await page.evaluate(()=>{location.hash='#/ui-automation/suites'});await page.reload();
 const row=page.getByRole('row').filter({hasText:setup.name});await row.waitFor({timeout:15000});await row.getByRole('button',{name:'运行'}).click();
 const dialog=page.getByRole('dialog',{name:'运行回归套件'});await dialog.getByRole('button',{name:'开始运行'}).click();
 await dialog.getByText('套件运行通过',{exact:true}).waitFor({timeout:60000});
 await dialog.getByRole('button',{name:'关闭',exact:true}).click();
 await row.getByRole('button',{name:'记录'}).click();
 await page.getByText('6/6 通过，0 失败，0 跳过',{exact:true}).first().waitFor({timeout:15000});
 const report=await page.evaluate(async id=>{const h={Authorization:'Bearer '+localStorage.getItem('token')},base='http://127.0.0.1:5001/api/ui-automation';const runs=await(await fetch(base+'/runs?suite_id='+id,{headers:h})).json(),run=runs.items[0],steps=await(await fetch(base+'/runs/'+run.id+'/step-results',{headers:h})).json();return{run,steps}},suiteId);
 if(report.run.status!=='passed'||report.run.passed_steps!==6||report.steps.total!==6)throw Error('SUITE_REPORT_FAILED_'+JSON.stringify(report));
 console.log(JSON.stringify({passed:true,status:report.run.status,passedSteps:report.run.passed_steps,dataIterations:3,stepResults:report.steps.total}));
}finally{
 const page=browser.contexts()[0].pages()[0];if(suiteId)await page.evaluate(async({suiteId,caseIds})=>{const h={Authorization:'Bearer '+localStorage.getItem('token')},base='http://127.0.0.1:5001/api/ui-automation';await fetch(base+'/suites/'+suiteId,{method:'DELETE',headers:h});for(const id of caseIds)await fetch(base+'/cases/'+id,{method:'DELETE',headers:h})},{suiteId,caseIds}).catch(()=>{});await browser.close();
}


