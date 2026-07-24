import { chromium } from 'playwright'
import { createServer } from 'node:http'

const pause = (page, milliseconds = 650) => page.waitForTimeout(milliseconds)
const browser = await chromium.connectOverCDP('http://127.0.0.1:9333')
const received = []
let server
let groupId = null
let caseId = null

try {
  server = createServer((request, response) => {
    received.push({ method: request.method, url: request.url })
    response.writeHead(200, { 'content-type': 'application/json; charset=utf-8' })
    response.end(JSON.stringify({ service: 'jmeter-acceptance', ok: true, path: request.url }))
  })
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve))
  const origin = `http://127.0.0.1:${server.address().port}`
  const page = browser.contexts()[0].pages()[0]
  const errors = []
  const quickPolls = []
  page.on('pageerror', error => errors.push(error.message))
  page.on('console', message => { if (message.type() === 'error') errors.push(message.text()) })
  page.on('response', response => {
    if (response.url().includes('/jmeter/quick-bench/') && response.request().method() === 'GET') quickPolls.push(response.status())
  })

  // The fixture is deliberately created through the same authenticated API used by
  // the product. The acceptance target is the desktop user's JMeter import/run flow.
  const fixture = await page.evaluate(async ({ origin }) => {
    const headers = {
      Authorization: `Bearer ${localStorage.getItem('token')}`,
      'Content-Type': 'application/json',
    }
    const stamp = Date.now()
    const groupResponse = await fetch('http://127.0.0.1:5001/api/auto-test/groups', {
      method: 'POST', headers, body: JSON.stringify({ name: `性能验收分组-${stamp}`, parent_id: null, description: 'desktop acceptance', sort_order: 0 }),
    })
    const group = await groupResponse.json()
    if (!groupResponse.ok || !group.id) throw new Error(`FIXTURE_GROUP_CREATE_FAILED:${JSON.stringify(group)}`)
    const caseResponse = await fetch('http://127.0.0.1:5001/api/auto-test/cases', {
      method: 'POST', headers,
      body: JSON.stringify({ name: `性能验收接口-${stamp}`, group_id: group.id, method: 'GET', url: `${origin}/health`, headers: {}, params: {}, body_type: 'none', payload: null, assertions: [{ target: 'status_code', operator: 'equals', expected: 200 }], description: 'JMeter acceptance fixture' }),
    })
    const apiCase = await caseResponse.json()
    if (!caseResponse.ok || !apiCase.id) throw new Error(`FIXTURE_CASE_CREATE_FAILED:${JSON.stringify(apiCase)}`)
    return { groupId: group.id, caseId: apiCase.id, name: apiCase.name }
  }, { origin })
  groupId = fixture.groupId
  caseId = fixture.caseId

  await page.evaluate(() => { location.hash = '#/jmeter-assistant' })
  await page.getByTestId('jmeter-page').waitFor({ timeout: 20000 })
  await page.getByText(fixture.name, { exact: true }).waitFor({ timeout: 20000 })
  await pause(page)

  const importItem = page.locator('.import-case-item').filter({ hasText: fixture.name })
  await importItem.click()
  await page.getByTestId('jmeter-import-selected-button').click()
  await page.getByText('已导入 1 个接口', { exact: true }).waitFor({ timeout: 15000 })
  await page.getByTestId('jmeter-bench-panel').waitFor({ timeout: 15000 })
  await pause(page)

  // Fast preview has its own request scheduler, result aggregation and local history.
  await page.getByTestId('jmeter-bench-concurrency-input').locator('input').fill('1')
  await page.getByTestId('jmeter-bench-duration-input').locator('input').fill('3')
  await page.getByTestId('jmeter-bench-duration-input').locator('input').press('Tab')
  const quickSubmitResponse = page.waitForResponse(response => response.url().includes('/jmeter/quick-bench') && response.request().method() === 'POST', { timeout: 15000 })
  await page.getByTestId('jmeter-bench-start-button').click()
  const quickSubmit = await quickSubmitResponse
  const quickBody = await quickSubmit.json().catch(() => null)
  if (!quickSubmit.ok() || !quickBody?.task_id) throw new Error(`QUICK_BENCH_SUBMIT_FAILED:${quickSubmit.status()}:${JSON.stringify(quickBody)}`)
  await pause(page, 7000)
  const quickStatus = await page.evaluate(async taskId => {
    const response = await fetch(`http://127.0.0.1:5001/api/auto-test/jmeter/quick-bench/${taskId}`, { headers: { Authorization: `Bearer ${localStorage.getItem('token')}` } })
    return { status: response.status, body: await response.json().catch(() => null) }
  }, quickBody.task_id)
  if (quickStatus.status !== 200 || quickStatus.body?.status !== 'done') throw new Error(`QUICK_BENCH_DID_NOT_COMPLETE:${JSON.stringify(quickStatus)}`)
  if (!quickStatus.body?.result) throw new Error(`QUICK_BENCH_RESULT_MISSING:${JSON.stringify(quickStatus)}`)
  await pause(page, 4000)
  if (!await page.getByTestId('jmeter-bench-result-section').isVisible()) {
    throw new Error(`QUICK_BENCH_UI_RESULT_NOT_RENDERED:polls=${JSON.stringify(quickPolls)}:status=${JSON.stringify(quickStatus.body)}`)
  }
  if (!received.some(item => item.url === '/health')) throw new Error('QUICK_BENCH_DID_NOT_REACH_TARGET')
  await page.getByTestId('jmeter-view-results-tree').waitFor({ timeout: 15000 })
  await page.getByTestId('jmeter-vrt-sample-node').first().click()
  await page.getByTestId('jmeter-vrt-detail-content').waitFor({ timeout: 15000 })
  await page.getByTestId('jmeter-vrt-response-body').getByText('jmeter-acceptance', { exact: false }).waitFor({ timeout: 15000 })
  await page.getByRole('button', { name: /^📋 历史/ }).click()
  const historyDialog = page.getByRole('dialog', { name: '📋 JMeter 压测历史' })
  await historyDialog.waitFor({ timeout: 15000 })
  await historyDialog.getByText(/本地 1/).waitFor({ timeout: 15000 })
  await page.keyboard.press('Escape')

  // A long quick preview must stop promptly and retain its stopped server state.
  await page.getByTestId('jmeter-bench-reset-button').click()
  await page.getByTestId('jmeter-bench-duration-input').locator('input').fill('60')
  await page.getByTestId('jmeter-bench-duration-input').locator('input').press('Tab')
  const stopSubmitResponse = page.waitForResponse(response => response.url().includes('/jmeter/quick-bench') && response.request().method() === 'POST', { timeout: 15000 })
  await page.getByTestId('jmeter-bench-start-button').click()
  const stopSubmit = await stopSubmitResponse
  const stopTask = await stopSubmit.json()
  if (!stopTask?.task_id) throw new Error(`STOP_FIXTURE_SUBMIT_FAILED:${JSON.stringify(stopTask)}`)
  await page.getByTestId('jmeter-bench-progress').waitFor({ timeout: 15000 })
  await pause(page, 1100)
  await page.getByRole('button', { name: '停止', exact: true }).click()
  await page.getByTestId('jmeter-bench-start-button').waitFor({ timeout: 15000 })
  const stopped = await page.evaluate(async taskId => {
    const response = await fetch(`http://127.0.0.1:5001/api/auto-test/jmeter/quick-bench/${taskId}`, { headers: { Authorization: `Bearer ${localStorage.getItem('token')}` } })
    return { status: response.status, body: await response.json().catch(() => null) }
  }, stopTask.task_id)
  if (stopped.status !== 200 || stopped.body?.status !== 'stopped') throw new Error(`QUICK_BENCH_STOP_FAILED:${JSON.stringify(stopped)}`)

  // The real engine must be both exposed by the desktop UI and submit a persistent run.
  const engine = await page.evaluate(async () => {
    const response = await fetch('http://127.0.0.1:5001/api/auto-test/jmeter/engine-status', { headers: { Authorization: `Bearer ${localStorage.getItem('token')}` } })
    return { status: response.status, body: await response.json().catch(() => null) }
  })
  if (engine.status !== 200 || !engine.body?.enabled) throw new Error(`JMETER_ENGINE_NOT_AVAILABLE:${JSON.stringify(engine)}`)
  await page.getByTestId('jmeter-bench-engine-select').click()
  await page.locator('.el-select-dropdown:visible').getByText('🎯 JMeter 引擎', { exact: true }).click()
  await pause(page)
  await page.getByTestId('jmeter-bench-start-button').click()
  // A real run must leave the pending state and settle within the low-load timeout.
  await page.getByTestId('jmeter-bench-result-section').waitFor({ timeout: 90000 })
  await page.getByTestId('jmeter-view-results-tree').waitFor({ timeout: 15000 })
  await page.getByTestId('jmeter-vrt-sample-node').first().click()
  await page.getByTestId('jmeter-vrt-response-body').getByText('jmeter-acceptance', { exact: false }).waitFor({ timeout: 15000 })

  const reportResponse = page.waitForResponse(response => response.url().includes('/auto-test/report/generate') && response.request().method() === 'POST', { timeout: 30000 })
  await page.getByRole('button', { name: '📄 导出报告', exact: true }).click()
  if (!(await reportResponse).ok()) throw new Error('PERFORMANCE_REPORT_EXPORT_FAILED')
  await page.getByText('Word 报告已导出', { exact: false }).waitFor({ timeout: 30000 })

  await page.getByRole('button', { name: '🏷️ 基线管理', exact: true }).click()
  const baselineDialog = page.getByRole('dialog', { name: '🏷️ 性能基线管理' })
  await baselineDialog.waitFor({ timeout: 15000 })
  await baselineDialog.getByRole('button', { name: /新建基线/ }).click()
  const createBaselineDialog = page.getByRole('dialog', { name: '➕ 新建性能基线' })
  const baselineName = `性能验收基线-${Date.now()}`
  await createBaselineDialog.getByLabel('名称').fill(baselineName)
  await createBaselineDialog.getByRole('button', { name: '创建', exact: true }).click()
  await page.getByText('基线创建成功', { exact: true }).waitFor({ timeout: 15000 })
  const baseline = await page.evaluate(async name => {
    const response = await fetch('http://127.0.0.1:5001/api/auto-test/jmeter/baselines', { headers: { Authorization: `Bearer ${localStorage.getItem('token')}` } })
    const values = await response.json()
    return Array.isArray(values) ? values.find(item => item.name === name) : null
  }, baselineName)
  if (!baseline?.id) throw new Error(`BASELINE_NOT_PERSISTED:${JSON.stringify(baseline)}`)
  await page.evaluate(async id => fetch(`http://127.0.0.1:5001/api/auto-test/jmeter/baselines/${id}`, { method: 'DELETE', headers: { Authorization: `Bearer ${localStorage.getItem('token')}` } }), baseline.id)

  if (errors.length) throw new Error(`RENDERER_ERRORS:${errors.join(' | ')}`)
  console.log(JSON.stringify({ passed: true, checks: ['fixture-create', 'desktop-import', 'quick-bench', 'quick-result-tree', 'quick-history', 'quick-stop', 'real-engine-status', 'real-engine-run', 'real-sample-details', 'word-report-export', 'baseline-create-delete'], requests: received.length, slowUserPauses: true }))
} finally {
  const page = browser.contexts()[0]?.pages()[0]
  if (page && caseId) await page.evaluate(async id => fetch(`http://127.0.0.1:5001/api/auto-test/cases/${id}`, { method: 'DELETE', headers: { Authorization: `Bearer ${localStorage.getItem('token')}` } }), caseId).catch(() => {})
  if (page && groupId) await page.evaluate(async id => fetch(`http://127.0.0.1:5001/api/auto-test/groups/${id}`, { method: 'DELETE', headers: { Authorization: `Bearer ${localStorage.getItem('token')}` } }), groupId).catch(() => {})
  await browser.close()
  if (server) await new Promise(resolve => server.close(resolve))
}
