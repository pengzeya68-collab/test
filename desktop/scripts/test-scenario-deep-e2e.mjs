import { chromium } from 'playwright'
import { createServer } from 'node:http'

const pause = (page, milliseconds = 650) => page.waitForTimeout(milliseconds)
const serverRequests = []
const server = createServer(async (request, response) => {
  let body = ''
  for await (const chunk of request) body += chunk
  const payload = body ? JSON.parse(body) : {}
  serverRequests.push({ url: request.url, body: payload })
  response.setHeader('content-type', 'application/json; charset=utf-8')
  if (request.url?.startsWith('/seed/')) {
    const username = decodeURIComponent(request.url.slice('/seed/'.length))
    response.end(JSON.stringify({ token: `token-${username}`, username }))
    return
  }
  if (request.url === '/verify') {
    const valid = payload.token === `token-${payload.username}`
    response.statusCode = valid ? 200 : 400
    response.end(JSON.stringify({ ok: valid, username: payload.username }))
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
  page.on('pageerror', error => errors.push(error.message))
  page.on('console', message => {
    if (message.type() === 'error') errors.push(message.text())
  })

  fixture = await page.evaluate(async origin => {
    const headers = {
      Authorization: `Bearer ${localStorage.getItem('token')}`,
      'Content-Type': 'application/json',
    }
    const api = async (path, options = {}) => {
      const response = await fetch(`http://127.0.0.1:5001/api/auto-test${path}`, { ...options, headers })
      const data = await response.json().catch(() => null)
      if (!response.ok) throw new Error(`${path}:${response.status}:${JSON.stringify(data)}`)
      return data
    }
    const suffix = Date.now()
    const group = await api('/groups', { method: 'POST', body: JSON.stringify({ name: `场景深度验收分组-${suffix}` }) })
    const seed = await api('/cases', {
      method: 'POST',
      body: JSON.stringify({
        name: `提取令牌-${suffix}`, method: 'GET', url: '/seed/{{username}}', group_id: group.id,
        assertions: [{ field: 'status_code', operator: 'equals', expected: 200 }],
        extractors: [{ extractorType: 'jsonpath', expression: '$.token', variableName: 'flow_token', defaultValue: '' }],
      }),
    })
    const verify = await api('/cases', {
      method: 'POST',
      body: JSON.stringify({
        name: `验证跨接口变量-${suffix}`, method: 'POST', url: '/verify', group_id: group.id,
        body_type: 'raw', content_type: 'application/json', payload: '{"token":"{{flow_token}}","username":"{{username}}"}',
        assertions: [{ field: '$.ok', operator: 'equals', expected: true }],
      }),
    })
    const environment = await api('/environments', {
      method: 'POST',
      body: JSON.stringify({ name: `场景深度环境-${suffix}`, base_url: origin, variables: { username: 'alice' }, is_default: true }),
    })
    const scenario = await api('/scenarios', {
      method: 'POST',
      body: JSON.stringify({ name: `场景深度验收-${suffix}`, description: '验证接口关联、变量提取与数据驱动', is_active: true }),
    })
    const first = await api(`/scenarios/${scenario.id}/steps`, {
      method: 'POST', body: JSON.stringify({ api_case_id: seed.id, step_order: 0, is_active: true }),
    })
    const second = await api(`/scenarios/${scenario.id}/steps`, {
      method: 'POST', body: JSON.stringify({ api_case_id: verify.id, step_order: 1, is_active: true }),
    })
    await api(`/scenarios/${scenario.id}/dataset`, {
      method: 'POST',
      body: JSON.stringify({ name: `数据集-${suffix}`, data_matrix: { columns: ['username'], rows: [['alice'], ['bob']] } }),
    })
    return { groupId: group.id, caseIds: [seed.id, verify.id], environmentId: environment.id, environmentName: environment.name, scenarioId: scenario.id, firstStepId: first.id, secondStepId: second.id, scenarioName: scenario.name }
  }, origin)

  await page.evaluate(id => { location.hash = `#/scenarios/${id}` }, fixture.scenarioId)
  const scenarioNameInput = page.locator('.scenario-name-input input')
  await scenarioNameInput.waitFor({ timeout: 15000 })
  await page.waitForFunction(name => document.querySelector('.scenario-name-input input')?.value === name, fixture.scenarioName, { timeout: 15000 })
  await page.getByText('提取令牌-', { exact: false }).waitFor({ timeout: 15000 })
  await page.getByText('验证跨接口变量-', { exact: false }).waitFor({ timeout: 15000 })
  await pause(page)

  const environmentSelect = page.locator('.editor-header .el-select').first()
  await environmentSelect.click()
  await page.locator('.el-select-dropdown:visible').getByText(fixture.environmentName, { exact: true }).click()
  await pause(page)
  await page.getByRole('button', { name: '运行场景', exact: true }).click()
  const runDialog = page.getByRole('dialog', { name: '场景执行结果' })
  await runDialog.getByText('全部通过', { exact: false }).waitFor({ timeout: 60000 })
  await runDialog.getByText('总步骤: 2', { exact: false }).waitFor({ timeout: 15000 })
  await runDialog.locator('.step-header').first().click()
  await runDialog.getByText('提取的变量', { exact: true }).waitFor({ timeout: 15000 })
  await runDialog.getByText('flow_token: token-alice', { exact: true }).first().waitFor({ timeout: 15000 })
  await runDialog.getByText('执行后的全局变量', { exact: true }).waitFor({ timeout: 15000 })
  await runDialog.getByRole('button', { name: '关闭', exact: true }).click()

  await page.getByRole('tab', { name: '数据驱动', exact: true }).click()
  await page.getByText('2 行数据', { exact: true }).waitFor({ timeout: 15000 })
  await page.getByRole('button', { name: '数据驱动执行', exact: true }).click()
  const dataDialog = page.getByRole('dialog', { name: '数据驱动执行结果' })
  await dataDialog.getByText('总迭代次数', { exact: true }).waitFor({ timeout: 60000 })
  await dataDialog.getByText('2', { exact: true }).first().waitFor({ timeout: 15000 })
  await dataDialog.getByRole('button', { name: /迭代 #1 username=alice 成功/ }).waitFor({ timeout: 15000 })
  await dataDialog.getByRole('button', { name: /迭代 #2 username=bob 成功/ }).waitFor({ timeout: 15000 })

  const verifyRequests = serverRequests.filter(item => item.url === '/verify')
  if (verifyRequests.length !== 3 || verifyRequests.some(item => item.body.token !== `token-${item.body.username}`)) {
    throw new Error(`VARIABLE_CHAIN_NOT_APPLIED:${JSON.stringify(serverRequests)}`)
  }
  if (errors.length) throw new Error(`RENDERER_ERRORS:${errors.join(' | ')}`)
  console.log(JSON.stringify({ passed: true, checks: ['scenario-editor-step-render', 'scenario-variable-extraction-chain', 'scenario-result-details', 'data-driven-task-polling', 'data-driven-two-iterations'], requests: serverRequests.length, slowUserPauses: true }))
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
