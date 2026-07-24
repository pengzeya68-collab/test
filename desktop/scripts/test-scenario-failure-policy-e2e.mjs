import { chromium } from 'playwright'
import { createServer } from 'node:http'

const pause = (page, milliseconds = 650) => page.waitForTimeout(milliseconds)
let afterFailureRequests = 0
const server = createServer((request, response) => {
  response.setHeader('content-type', 'application/json; charset=utf-8')
  if (request.url === '/forced-failure') {
    response.statusCode = 503
    response.end(JSON.stringify({ ok: false, reason: 'acceptance failure' }))
    return
  }
  if (request.url === '/after-failure') {
    afterFailureRequests += 1
    response.end(JSON.stringify({ ok: true }))
    return
  }
  response.statusCode = 404
  response.end(JSON.stringify({ ok: false }))
})
await new Promise(resolve => server.listen(0, '127.0.0.1', resolve))
const origin = `http://127.0.0.1:${server.address().port}`
const browser = await chromium.connectOverCDP('http://127.0.0.1:9333')
let fixture = null

try {
  const page = browser.contexts()[0].pages()[0]
  const errors = []
  const scenarioWrites = []
  page.on('pageerror', error => errors.push(error.message))
  page.on('console', message => { if (message.type() === 'error') errors.push(message.text()) })
  page.on('request', request => {
    if (request.url().includes('/api/auto-test/scenarios/') && request.method() === 'PUT') {
      scenarioWrites.push({ body: request.postData() })
    }
  })
  page.on('response', response => {
    if (response.url().includes('/api/auto-test/scenarios/') && response.request().method() === 'PUT') {
      scenarioWrites.push({ status: response.status() })
    }
  })

  fixture = await page.evaluate(async origin => {
    const headers = { Authorization: `Bearer ${localStorage.getItem('token')}`, 'Content-Type': 'application/json' }
    const api = async (path, options = {}) => {
      const response = await fetch(`http://127.0.0.1:5001/api/auto-test${path}`, { ...options, headers })
      const data = await response.json().catch(() => null)
      if (!response.ok) throw new Error(`${path}:${response.status}:${JSON.stringify(data)}`)
      return data
    }
    const suffix = Date.now()
    const group = await api('/groups', { method: 'POST', body: JSON.stringify({ name: `失败策略验收分组-${suffix}` }) })
    const failingCase = await api('/cases', { method: 'POST', body: JSON.stringify({
      name: `预期失败步骤-${suffix}`, method: 'GET', url: '/forced-failure', group_id: group.id,
      assertions: [{ field: 'status_code', operator: 'equals', expected: 200 }],
    }) })
    const trailingCase = await api('/cases', { method: 'POST', body: JSON.stringify({
      name: `失败后步骤-${suffix}`, method: 'GET', url: '/after-failure', group_id: group.id,
      assertions: [{ field: 'status_code', operator: 'equals', expected: 200 }],
    }) })
    const environment = await api('/environments', { method: 'POST', body: JSON.stringify({ name: `失败策略环境-${suffix}`, base_url: origin, is_default: true, variables: {} }) })
    const scenario = await api('/scenarios', { method: 'POST', body: JSON.stringify({ name: `失败策略场景-${suffix}`, is_active: true }) })
    await api(`/scenarios/${scenario.id}/steps`, { method: 'POST', body: JSON.stringify({ api_case_id: failingCase.id, step_order: 0, is_active: true }) })
    await api(`/scenarios/${scenario.id}/steps`, { method: 'POST', body: JSON.stringify({ api_case_id: trailingCase.id, step_order: 1, is_active: true }) })
    return { groupId: group.id, caseIds: [failingCase.id, trailingCase.id], environmentId: environment.id, environmentName: environment.name, scenarioId: scenario.id, scenarioName: scenario.name }
  }, origin)

  await page.evaluate(id => { location.hash = `#/scenarios/${id}` }, fixture.scenarioId)
  // Lazy-loaded routes can still be resolving after the previous workflow has
  // reloaded the shared desktop window.  A human would wait and retry the page
  // once; mirror that behavior instead of treating a routing race as a product
  // failure.
  const waitForScenarioEditor = () => page.waitForFunction(
    name => document.querySelector('.scenario-name-input input')?.value === name,
    fixture.scenarioName,
    { timeout: 30000 },
  )
  try {
    await waitForScenarioEditor()
  } catch {
    await page.reload({ waitUntil: 'domcontentloaded' })
    await pause(page, 900)
    await waitForScenarioEditor()
  }
  const policySwitch = page.locator('.editor-header .el-switch')
  await policySwitch.click()
  await page.waitForFunction(() => document.querySelector('.editor-header .el-switch input')?.checked === true, { timeout: 15000 })
  await pause(page, 1200)
  const storedPolicy = await page.evaluate(async id => {
    const response = await fetch(`http://127.0.0.1:5001/api/auto-test/scenarios/${id}`, { headers: { Authorization: `Bearer ${localStorage.getItem('token')}` } })
    return response.ok ? response.json() : null
  }, fixture.scenarioId)
  if (storedPolicy?.fail_fast !== true) throw new Error(`FAIL_FAST_NOT_PERSISTED:${JSON.stringify({ storedPolicy, scenarioWrites })}`)

  const environmentSelect = page.locator('.editor-header .el-select').first()
  await environmentSelect.click()
  await page.locator('.el-select-dropdown:visible').getByText(fixture.environmentName, { exact: true }).click()
  await page.getByRole('button', { name: '运行场景', exact: true }).click()
  const resultDialog = page.getByRole('dialog', { name: '场景执行结果' })
  await resultDialog.getByText('有步骤失败', { exact: false }).waitFor({ timeout: 60000 })
  await resultDialog.getByText('未执行/跳过', { exact: true }).waitFor({ timeout: 15000 })
  await resultDialog.getByText('因前置步骤失败且启用 fail_fast，跳过此步骤', { exact: true }).waitFor({ timeout: 15000 })
  if (afterFailureRequests !== 0) throw new Error(`FAIL_FAST_DID_NOT_STOP_REQUESTS:${afterFailureRequests}`)
  if (errors.length) throw new Error(`RENDERER_ERRORS:${errors.join(' | ')}`)
  console.log(JSON.stringify({ passed: true, checks: ['fail-fast-ui-config', 'fail-fast-api-persistence', 'failed-step-result', 'trailing-step-skipped', 'trailing-request-not-sent'], slowUserPauses: true }))
} finally {
  const page = browser.contexts()[0].pages()[0]
  if (fixture) {
    await page.evaluate(async fixture => {
      const headers = { Authorization: `Bearer ${localStorage.getItem('token')}` }
      const base = 'http://127.0.0.1:5001/api/auto-test'
      await fetch(`${base}/scenarios/${fixture.scenarioId}`, { method: 'DELETE', headers })
      await fetch(`${base}/environments/${fixture.environmentId}`, { method: 'DELETE', headers })
      for (const id of fixture.caseIds) await fetch(`${base}/cases/${id}`, { method: 'DELETE', headers })
      await fetch(`${base}/groups/${fixture.groupId}`, { method: 'DELETE', headers })
    }, fixture).catch(() => {})
  }
  await browser.close()
  await new Promise(resolve => server.close(resolve))
}
