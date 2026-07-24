import { chromium } from 'playwright'
import { createServer } from 'node:http'

const pause = (page, milliseconds = 1000) => page.waitForTimeout(milliseconds)
const requests = []
const server = createServer((request, response) => {
  requests.push({ url: request.url, headers: request.headers })
  if (request.url === '/') {
    response.setHeader('content-type', 'text/html; charset=utf-8')
    response.end(`<!doctype html><meta charset="utf-8"><title>Capture acceptance</title><button data-testid="start">开始</button><script>setTimeout(async()=>{const login=await fetch('/api/login',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({username:'capture-user',password:'should-not-leak'})});const auth=await login.json();await fetch('/api/orders',{headers:{authorization:'Bearer '+auth.token}});document.body.dataset.done='yes'},700)</script>`)
    return
  }
  response.setHeader('content-type', 'application/json; charset=utf-8')
  if (request.url === '/api/login') {
    response.end(JSON.stringify({ token: 'sensitive-capture-token', order_id: 'capture-order-1' }))
    return
  }
  if (request.url === '/api/orders') {
    response.end(JSON.stringify({ status: 'ok', order_id: 'capture-order-1' }))
    return
  }
  response.statusCode = 404
  response.end(JSON.stringify({ error: 'not-found' }))
})
await new Promise(resolve => server.listen(0, '127.0.0.1', resolve))
const origin = `http://127.0.0.1:${server.address().port}`
const browser = await chromium.connectOverCDP('http://127.0.0.1:9333')
let caseId = null
let captureId = null
let generatedCaseIds = []
let generatedScenarioId = null

try {
  const page = browser.contexts()[0].pages()[0]
  const errors = []
  page.on('pageerror', error => errors.push(error.message))
  page.on('console', message => { if (message.type() === 'error') errors.push(message.text()) })

  const name = `桌面流量录制验收-${Date.now()}`
  await page.evaluate(() => { location.hash = '#/ui-automation/cases' })
  await page.locator('.ui-case-list .page-header h2').waitFor({ timeout: 15000 })
  await page.getByRole('button', { name: '新建用例', exact: true }).click()
  const create = page.getByRole('dialog', { name: '新建 UI 用例' })
  await create.locator('.el-form-item').filter({ hasText: '用例名称' }).locator('input').fill(name)
  await create.locator('.el-form-item').filter({ hasText: '基础URL' }).locator('input').fill(origin)
  await create.getByRole('button', { name: '创建', exact: true }).click()
  await page.getByText('创建成功', { exact: true }).waitFor({ timeout: 15000 })
  await page.waitForURL(/#\/ui-automation\/cases\/\d+$/, { timeout: 15000 })
  caseId = Number((await page.evaluate(() => location.hash)).split('/').pop())
  await page.getByText('用户操作流程', { exact: true }).waitFor({ timeout: 15000 })
  const recorderInput = page.locator('.record-address input')
  await recorderInput.fill(origin)
  await pause(page)
  await page.locator('.automation-studio .empty-flow').getByRole('button', { name: '开始录制', exact: true }).click()
  try {
    await page.getByText('正在录制', { exact: false }).waitFor({ timeout: 60000 })
  } catch (error) {
    throw new Error(`RECORDER_DID_NOT_START:${await page.locator('.automation-studio').innerText()}`)
  }
  // The recorder is deliberately allowed to observe login and follow-up API calls.
  await pause(page, 4500)
  await page.getByRole('button', { name: '停止录制', exact: true }).click()
  await page.getByText(/录制完成|接口记录等待同步/, { exact: false }).waitFor({ timeout: 20000 })
  if (!requests.some(item => item.url === '/api/login') || !requests.some(item => item.url === '/api/orders')) throw new Error(`RECORDER_TARGET_NOT_EXERCISED:${JSON.stringify(requests)}`)

  const captureLookup = await page.evaluate(async sourceUrl => {
    const response = await fetch('http://127.0.0.1:5001/api/auto-test/import/captures', {
      headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
    })
    const body = await response.json()
    const captures = body.captures || []
    return { capture: captures.find(item => item.source_url?.replace(/\/$/, '') === sourceUrl && item.status === 'completed') || null, captures }
  }, origin)
  const capture = captureLookup.capture
  if (!capture?.id) throw new Error(`CAPTURE_NOT_COMPLETED:${JSON.stringify(captureLookup)}`)
  captureId = capture.id
  const captureDetail = await page.evaluate(async id => {
    const response = await fetch(`http://127.0.0.1:5001/api/auto-test/import/captures/${id}`, {
      headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
    })
    return response.json()
  }, captureId)
  if (captureDetail.total < 2 || JSON.stringify(captureDetail).includes('sensitive-capture-token') || JSON.stringify(captureDetail).includes('should-not-leak')) {
    throw new Error(`CAPTURE_REDACTION_OR_COUNT_FAILED:${JSON.stringify(captureDetail)}`)
  }

  await page.evaluate(id => { location.hash = `#/import-center?captureId=${id}` }, captureId)
  await page.getByRole('heading', { name: '导入中心', exact: true }).waitFor({ timeout: 15000 })
  await page.getByText('POST /api/login', { exact: true }).waitFor({ timeout: 15000 })
  await pause(page)
  const rows = page.locator('.import-center .el-table tbody tr')
  const rowCount = await rows.count()
  if (rowCount < 2) throw new Error(`CAPTURE_IMPORT_ROWS_MISSING:${rowCount}`)
  for (let index = 0; index < rowCount; index += 1) {
    const checkbox = rows.nth(index).locator('.el-checkbox').first()
    const selected = await checkbox.locator('input').evaluate(input => input.checked)
    if (!selected) await checkbox.click()
  }
  await page.getByText('我已确认以下调用顺序和变量依赖', { exact: true }).click()
  await page.getByRole('button', { name: /生成接口用例与场景/ }).click()
  await page.getByText('导入完成', { exact: true }).waitFor({ timeout: 20000 })

  const generated = await page.evaluate(async id => {
    const response = await fetch(`http://127.0.0.1:5001/api/auto-test/import/captures/${id}`, {
      headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
    })
    return response.json()
  }, captureId)
  const candidates = generated.candidates || []
  if (candidates.length < 2 || candidates.some(item => JSON.stringify(item).includes('sensitive-capture-token'))) throw new Error('CAPTURE_CANDIDATES_EXPOSE_SECRET')
  const resultText = await page.locator('.import-center').innerText()
  if (!resultText.includes('新建 2 个')) throw new Error(`CAPTURE_CONVERT_UNEXPECTED:${resultText}`)
  // Read only the created assets for cleanup and persistence verification.
  const assets = await page.evaluate(async () => {
    const headers = { Authorization: `Bearer ${localStorage.getItem('token')}` }
    const [casesResponse, scenariosResponse] = await Promise.all([
      fetch('http://127.0.0.1:5001/api/auto-test/cases?page_size=100', { headers }),
      fetch('http://127.0.0.1:5001/api/auto-test/scenarios', { headers }),
    ])
    return { cases: await casesResponse.json(), scenarios: await scenariosResponse.json() }
  })
  const cases = Array.isArray(assets.cases) ? assets.cases : assets.cases.items || []
  const scenarios = Array.isArray(assets.scenarios) ? assets.scenarios : assets.scenarios.items || []
  generatedCaseIds = cases.filter(item => item.description?.includes('Created from a redacted browser capture')).map(item => item.id)
  const scenario = scenarios.find(item => item.description?.includes('Generated from selected browser capture exchanges'))
  generatedScenarioId = scenario?.id ?? null
  if (generatedCaseIds.length < 2 || !generatedScenarioId || scenario.is_active !== false) throw new Error(`CAPTURE_ASSET_PERSISTENCE_INVALID:${JSON.stringify({ generatedCaseIds, scenario })}`)

  if (errors.length) throw new Error(`RENDERER_ERRORS:${errors.join(' | ')}`)
  console.log(JSON.stringify({ passed: true, checks: ['desktop-recording', 'captured-xhr-fetch', 'capture-redaction', 'import-center-selection', 'capture-to-cases-and-scenario', 'scenario-preview-gate'], slowUserPauses: true }))
} finally {
  const page = browser.contexts()[0].pages()[0]
  await page.evaluate(async ({ caseId, generatedCaseIds, generatedScenarioId }) => {
    const headers = { Authorization: `Bearer ${localStorage.getItem('token')}` }
    if (generatedScenarioId) await fetch(`http://127.0.0.1:5001/api/auto-test/scenarios/${generatedScenarioId}`, { method: 'DELETE', headers })
    for (const id of generatedCaseIds) await fetch(`http://127.0.0.1:5001/api/auto-test/cases/${id}`, { method: 'DELETE', headers })
    if (caseId) await fetch(`http://127.0.0.1:5001/api/ui-automation/cases/${caseId}`, { method: 'DELETE', headers })
  }, { caseId, generatedCaseIds, generatedScenarioId }).catch(() => {})
  await browser.close()
  await new Promise(resolve => server.close(resolve))
}
