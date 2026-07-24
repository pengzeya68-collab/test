import { chromium } from 'playwright'
import { createServer } from 'node:http'

const pause = (page, milliseconds = 750) => page.waitForTimeout(milliseconds)
const serverRequests = []
const server = createServer((request, response) => {
  serverRequests.push({ url: request.url, headers: request.headers })
  response.setHeader('content-type', 'application/json; charset=utf-8')
  response.end(JSON.stringify({ route: request.url, environmentHeader: request.headers['x-environment-token'] || null }))
})
await new Promise(resolve => server.listen(0, '127.0.0.1', resolve))
const origin = `http://127.0.0.1:${server.address().port}`
const browser = await chromium.connectOverCDP('http://127.0.0.1:9333')
let environmentName = ''
let environmentId = null

try {
  const page = browser.contexts()[0].pages()[0]
  const errors = []
  page.on('pageerror', error => errors.push(error.message))
  page.on('console', message => {
    if (message.type() === 'error') errors.push(message.text())
  })

  environmentName = `桌面环境验收-${Date.now()}`
  await page.evaluate(() => { location.hash = '#/cases' })
  await page.getByRole('heading', { name: '接口用例', exact: true }).waitFor({ timeout: 15000 })
  await page.getByTitle('环境管理').click()
  const drawer = page.getByRole('dialog', { name: /环境管理/ })
  await drawer.waitFor({ timeout: 15000 })
  await pause(page)
  await drawer.getByRole('button', { name: '新建环境', exact: true }).click()
  const dialog = page.getByRole('dialog', { name: '新建环境' })
  await dialog.locator('.el-form-item').filter({ hasText: '环境名称' }).locator('input').fill(environmentName)
  await dialog.locator('.el-form-item').filter({ hasText: '基础URL' }).locator('input').fill(origin)
  await dialog.getByRole('button', { name: '添加变量', exact: true }).click()
  const variableRow = dialog.locator('.var-item-editor').last()
  await variableRow.locator('input').nth(0).fill('env_token')
  await variableRow.locator('input').nth(1).fill('environment-secret')
  await pause(page)
  await dialog.getByRole('button', { name: '创建', exact: true }).click()
  await page.getByText('创建成功', { exact: true }).waitFor({ timeout: 15000 })
  await drawer.getByText(environmentName, { exact: true }).waitFor({ timeout: 15000 })

  environmentId = await page.evaluate(async name => {
    const response = await fetch('http://127.0.0.1:5001/api/auto-test/environments', {
      headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
    })
    const environments = await response.json()
    return environments.find(item => item.name === name)?.id ?? null
  }, environmentName)
  if (!environmentId) throw new Error('ENVIRONMENT_NOT_PERSISTED')
  const persisted = await page.evaluate(async id => {
    const response = await fetch(`http://127.0.0.1:5001/api/auto-test/environments/${id}`, {
      headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
    })
    return response.json()
  }, environmentId)
  // Sensitive names are deliberately masked by the read API. The real request below
  // verifies the unmasked value is retained and applied without exposing it in the UI.
  if (persisted.base_url !== origin || persisted.variables?.env_token !== '****') throw new Error(`ENVIRONMENT_DATA_INVALID:${JSON.stringify(persisted)}`)

  await page.keyboard.press('Escape')
  await page.evaluate(() => { location.hash = '#/api-debugger' })
  await page.getByRole('heading', { name: '接口调试', exact: true }).waitFor({ timeout: 15000 })
  await pause(page, 1200)
  const environmentSelect = page.locator('.debug-toolbar .el-select').first()
  await environmentSelect.click()
  await page.locator('.el-select-dropdown:visible').getByText(environmentName, { exact: true }).click()
  const urlInput = page.locator('.request-line .url-input input')
  await urlInput.fill('{{base_url}}/env-check')
  await page.getByRole('tab', { name: '请求头', exact: true }).click()
  await page.getByRole('button', { name: '添加请求头', exact: true }).click()
  const headerRow = page.locator('.el-tab-pane:visible .kv-row').last()
  await headerRow.locator('input').nth(0).fill('X-Environment-Token')
  await headerRow.locator('input').nth(1).fill('{{env_token}}')
  await pause(page)
  const sendResponse = page.waitForResponse(response => response.url().includes('/api/auto-test/send') && response.request().method() === 'POST', { timeout: 15000 })
  await page.getByRole('button', { name: '发送', exact: true }).click()
  const sent = await sendResponse
  const sentBody = await sent.json().catch(() => null)
  if (!sent.ok() || !sentBody?.success) {
    throw new Error(`ENVIRONMENT_DEBUG_REQUEST_FAILED:${sent.status()}:${JSON.stringify(sentBody)}`)
  }
  await page.getByText('environment-secret', { exact: false }).first().waitFor({ timeout: 15000 })
  if (!serverRequests.some(item => item.url === '/env-check' && item.headers['x-environment-token'] === 'environment-secret')) {
    throw new Error(`ENVIRONMENT_VARIABLES_NOT_APPLIED:${JSON.stringify(serverRequests)}`)
  }

  await page.evaluate(() => { location.hash = '#/cases' })
  await page.getByRole('heading', { name: '接口用例', exact: true }).waitFor({ timeout: 15000 })
  await page.getByTitle('环境管理').click()
  const deleteDrawer = page.getByRole('dialog', { name: /环境管理/ })
  const environmentCard = deleteDrawer.locator('.env-card').filter({ hasText: environmentName })
  await environmentCard.getByRole('button', { name: '删除', exact: true }).click()
  const confirm = page.locator('.el-message-box')
  await confirm.getByRole('button', { name: '删除', exact: true }).click()
  await page.getByText('删除成功', { exact: true }).waitFor({ timeout: 15000 })
  await environmentCard.waitFor({ state: 'detached', timeout: 15000 })
  environmentId = null

  if (errors.length) throw new Error(`RENDERER_ERRORS:${errors.join(' | ')}`)
  console.log(JSON.stringify({ passed: true, checks: ['environment-create-ui-persistence', 'environment-variable-substitution', 'environment-base-url-resolution', 'environment-delete-ui'], slowUserPauses: true }))
} finally {
  const page = browser.contexts()[0].pages()[0]
  if (environmentId) {
    await page.evaluate(async id => fetch(`http://127.0.0.1:5001/api/auto-test/environments/${id}`, {
      method: 'DELETE', headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
    }), environmentId).catch(() => {})
  }
  await browser.close()
  await new Promise(resolve => server.close(resolve))
}
