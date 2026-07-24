import { chromium } from 'playwright'
import { createServer } from 'node:http'

const received = []
const server = createServer(async (request, response) => {
  const body = await new Promise(resolve => {
    let value = ''
    request.setEncoding('utf8')
    request.on('data', chunk => { value += chunk })
    request.on('end', () => resolve(value))
  })
  const url = new URL(request.url, 'http://127.0.0.1')
  received.push({ method: request.method, path: url.pathname, query: Object.fromEntries(url.searchParams), headers: request.headers, body })
  response.setHeader('content-type', 'application/json; charset=utf-8')
  if (url.pathname === '/slow') {
    setTimeout(() => response.end(JSON.stringify({ late: true })), 2200)
    return
  }
  if (url.pathname === '/error') {
    response.statusCode = 503
    response.end(JSON.stringify({ error: 'service unavailable' }))
    return
  }
  response.end(JSON.stringify({ route: url.pathname, query: Object.fromEntries(url.searchParams), method: request.method, header: request.headers['x-acceptance-id'] || null, body }))
})

await new Promise(resolve => server.listen(0, '127.0.0.1', resolve))
const origin = `http://127.0.0.1:${server.address().port}`
const browser = await chromium.connectOverCDP('http://127.0.0.1:9333')

const expectJson = async (page, expected) => {
  await page.locator('.response-body-pre').first().waitFor({ state: 'visible', timeout: 15000 })
  await page.getByText(expected, { exact: false }).first().waitFor({ timeout: 15000 })
}

const send = async page => {
  await page.getByRole('button', { name: '发送', exact: true }).click()
  await page.getByRole('button', { name: '发送', exact: true }).waitFor({ state: 'visible' })
  await page.waitForTimeout(150)
}

try {
  const page = browser.contexts()[0].pages()[0]
  const errors = []
  page.on('pageerror', error => errors.push(error.message))
  page.on('console', message => { if (message.type() === 'error') errors.push(message.text()) })
  await page.evaluate(() => { location.hash = '#/api-debugger' })
  await page.getByRole('heading', { name: '接口调试', exact: true }).waitFor({ timeout: 15000 })

  const urlInput = page.locator('.request-line .url-input input')
  const timeoutInput = page.locator('.request-line .el-input-number input')

  // GET + query is a real request through the debugger UI and the packaged backend.
  await urlInput.fill(`${origin}/echo`)
  await page.getByRole('tab', { name: '参数', exact: true }).click()
  await page.getByRole('button', { name: '添加参数', exact: true }).click()
  const parameterRow = page.locator('.el-tab-pane:visible .kv-row').last()
  await parameterRow.locator('input').nth(0).fill('user')
  await parameterRow.locator('input').nth(1).fill('alice')
  await send(page)
  await expectJson(page, '"route": "/echo"')
  if (!received.some(item => item.method === 'GET' && item.query.user === 'alice')) throw new Error('GET_QUERY_NOT_RECEIVED')

  // POST JSON and custom header must cross the renderer -> backend -> target boundary unchanged.
  await page.locator('.method-select').click()
  await page.locator('.el-select-dropdown:visible').getByText('POST', { exact: true }).click()
  await page.getByRole('tab', { name: '请求头', exact: true }).click()
  await page.getByRole('button', { name: '添加请求头', exact: true }).click()
  const headerRow = page.locator('.el-tab-pane:visible .kv-row').last()
  await headerRow.locator('input').nth(0).fill('X-Acceptance-Id')
  await headerRow.locator('input').nth(1).fill('desktop-e2e')
  await page.getByRole('tab', { name: '请求体', exact: true }).click()
  await page.locator('.body-textarea textarea').fill('{"orderId":"A-100","items":[1,2]}')
  await send(page)
  await expectJson(page, 'desktop-e2e')
  if (!received.some(item => item.method === 'POST' && item.headers['x-acceptance-id'] === 'desktop-e2e' && item.body.includes('A-100'))) throw new Error('POST_HEADER_OR_BODY_NOT_RECEIVED')

  // Multipart form fields are separate from raw JSON and commonly regress independently.
  await page.locator('.body-type-group .el-radio-button').filter({ hasText: 'Form' }).click()
  await page.getByRole('button', { name: '添加字段', exact: true }).click()
  const formRow = page.locator('.el-tab-pane:visible .kv-row').last()
  await formRow.locator('input').nth(0).fill('comment')
  await formRow.locator('input').nth(1).fill('created-in-desktop')
  await send(page)
  if (!received.some(item => item.method === 'POST' && item.body.includes('created-in-desktop'))) throw new Error('FORM_DATA_NOT_RECEIVED')

  // Failure response has to render a usable status/body rather than leave a blank panel.
  await urlInput.fill(`${origin}/error`)
  await send(page)
  await page.getByText('503', { exact: false }).first().waitFor({ timeout: 15000 })
  await expectJson(page, 'service unavailable')

  // Regression for the timeout control: the UI value must reach request_config.timeout_ms.
  await urlInput.fill(`${origin}/slow`)
  await timeoutInput.fill('1')
  const timeoutStarted = Date.now()
  await send(page)
  await page.getByText(/超时|timeout/i).first().waitFor({ timeout: 6000 })
  if (Date.now() - timeoutStarted > 1900) throw new Error('DEBUGGER_TIMEOUT_WAS_NOT_APPLIED')

  // cURL import takes a separate parser endpoint, then applies parameters back to the visible form.
  await page.getByRole('button', { name: '导入cURL', exact: true }).click()
  const curlDialog = page.getByRole('dialog', { name: '导入 cURL' })
  await curlDialog.locator('textarea').fill(`curl -X POST ${origin}/curl -H "X-Acceptance-Id: curl-flow" -d '{"from":"curl"}'`)
  await curlDialog.getByRole('button', { name: '解析', exact: true }).click()
  await curlDialog.getByText('解析结果', { exact: true }).waitFor({ timeout: 15000 })
  await curlDialog.getByRole('button', { name: '应用', exact: true }).click()
  await send(page)
  if (!received.some(item => item.path === '/curl' && item.headers['x-acceptance-id'] === 'curl-flow' && item.body.includes('curl'))) throw new Error('CURL_IMPORT_NOT_EXECUTED')

  // A user can replay, load, delete and clear history; validate actual button paths, not component state.
  await page.getByRole('button', { name: '历史', exact: true }).click()
  const historyDrawer = page.getByRole('dialog', { name: /请求历史/ })
  await historyDrawer.getByRole('button', { name: '再次请求', exact: true }).first().click()
  await page.getByText('"route": "/curl"', { exact: false }).first().waitFor({ timeout: 15000 })
  await page.getByRole('button', { name: '历史', exact: true }).click()
  await historyDrawer.getByRole('button', { name: '加载', exact: true }).first().click()
  await urlInput.inputValue().then(value => { if (!value.includes('/curl')) throw new Error('HISTORY_LOAD_FAILED') })
  await page.getByRole('button', { name: '历史', exact: true }).click()
  await historyDrawer.getByRole('button', { name: '清空历史', exact: true }).click()
  await page.getByText('暂无历史记录', { exact: true }).waitFor({ timeout: 10000 })
  await page.keyboard.press('Escape')
  await historyDrawer.waitFor({ state: 'hidden', timeout: 10000 })

  await page.getByRole('button', { name: '清空', exact: true }).click()
  if (await urlInput.inputValue()) throw new Error('CLEAR_FORM_FAILED')
  if (errors.length) throw new Error(`RENDERER_ERRORS:${errors.join(' | ')}`)
  console.log(JSON.stringify({ passed: true, checks: ['get-query', 'post-json-header', 'form-data', 'http-error', 'timeout', 'curl-import', 'history-replay-load-clear', 'clear-form'], received: received.length }))
} finally {
  await browser.close()
  await new Promise(resolve => server.close(resolve))
}
