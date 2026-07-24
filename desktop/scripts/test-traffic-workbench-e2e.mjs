import { chromium } from 'playwright'
import { createServer } from 'node:http'
import { mkdir, rm, writeFile } from 'node:fs/promises'
import path from 'node:path'

const profile = process.env.TESTMASTER_ACCEPTANCE_DATA_DIR || 'D:\\TestMasterAcceptance\\runs\\current'
const artifacts = path.join(profile, 'traffic-workbench-artifacts')
const errors = []
const server = createServer((request, response) => {
  response.setHeader('content-type', 'application/json; charset=utf-8')
  if (request.url === '/orders') {
    response.statusCode = 201
    response.end(JSON.stringify({ id: 'replayed-order', status: 'created', token: 'must-not-appear' }))
    return
  }
  response.statusCode = 404
  response.end(JSON.stringify({ error: 'not-found' }))
})
await new Promise(resolve => server.listen(0, '127.0.0.1', resolve))
const targetUrl = `http://127.0.0.1:${server.address().port}/orders`
let browser

try {
  await mkdir(artifacts, { recursive: true })
  browser = await chromium.connectOverCDP('http://127.0.0.1:9333')
  const page = browser.contexts()[0].pages()[0]
  page.on('pageerror', error => errors.push(error.message))
  page.on('console', message => { if (message.type() === 'error') errors.push(message.text()) })
  const authHeaders = await page.evaluate(() => ({ Authorization: `Bearer ${localStorage.getItem('token')}` }))
  const created = await page.evaluate(async ({ targetUrl, authHeaders }) => {
    const create = await fetch('http://127.0.0.1:5001/api/auto-test/import/captures', {
      method: 'POST', headers: { ...authHeaders, 'content-type': 'application/json' },
      body: JSON.stringify({ origin: 'desktop_browser', source_url: targetUrl }),
    })
    const session = await create.json()
    if (!create.ok) throw new Error(`CREATE_CAPTURE:${create.status}:${JSON.stringify(session)}`)
    const exchanges = [
      { captureEventId: `workbench-${Date.now()}-request`, resourceType: 'fetch', method: 'POST', url: targetUrl, requestHeaders: { 'content-type': 'application/json', authorization: 'Bearer capture-secret' }, requestBody: { sku: 'A-1', token: 'capture-secret' }, status: 201, responseHeaders: { 'content-type': 'application/json' }, responseBody: { id: 'baseline-order', status: 'created', token: 'capture-secret' }, timingMs: 18 },
      { captureEventId: `workbench-${Date.now()}-failure`, resourceType: 'document', method: 'GET', url: `${targetUrl}/checkout`, status: 0, failureReason: 'net::ERR_CONNECTION_RESET token=capture-secret' },
    ]
    const append = await fetch(`http://127.0.0.1:5001/api/auto-test/import/captures/${session.id}/exchanges`, { method: 'POST', headers: { ...authHeaders, 'content-type': 'application/json' }, body: JSON.stringify({ exchanges }) })
    if (!append.ok) throw new Error(`APPEND_CAPTURE:${append.status}:${await append.text()}`)
    const complete = await fetch(`http://127.0.0.1:5001/api/auto-test/import/captures/${session.id}/complete`, { method: 'POST', headers: authHeaders })
    if (!complete.ok) throw new Error(`COMPLETE_CAPTURE:${complete.status}:${await complete.text()}`)
    return session
  }, { targetUrl, authHeaders })

  await page.evaluate(() => { location.hash = '/traffic-workbench' })
  await page.locator('.traffic-workbench h2').waitFor({ timeout: 15000 })
  const apiCapture = await page.evaluate(async ({ id, authHeaders }) => {
    const response = await fetch(`http://127.0.0.1:5001/api/auto-test/import/captures/${id}`, { headers: authHeaders })
    return { status: response.status, body: await response.json() }
  }, { id: created.id, authHeaders })
  if (apiCapture.status !== 200 || apiCapture.body.total !== 2) throw new Error(`CAPTURE_API_INVALID:${JSON.stringify(apiCapture)}`)
  const sessionRow = page.getByText(targetUrl, { exact: false }).first()
  await sessionRow.waitFor({ timeout: 15000 })
  await sessionRow.click()
  const rows = page.locator('.traffic-workbench .el-table tbody tr')
  try { await rows.first().waitFor({ timeout: 15000 }) } catch (error) { throw new Error(`WORKBENCH_TABLE_NOT_RENDERED:${await page.locator('.traffic-workbench').innerText()}`) }
  if (await rows.count() < 2) throw new Error(`WORKBENCH_ROWS_MISSING:${await rows.count()}`)
  await rows.first().click()
  await page.getByText('流量详情 #', { exact: false }).waitFor({ timeout: 10000 })
  const detailText = await page.locator('.traffic-workbench .inspector').innerText()
  if (detailText.includes('capture-secret')) throw new Error('WORKBENCH_EXPOSED_CAPTURE_SECRET')
  await page.getByText('仅可转接口', { exact: true }).click()
  if (await rows.count() !== 1) throw new Error('CONVERTIBLE_FILTER_FAILED')
  await page.getByText('仅可转接口', { exact: true }).click()
  await page.getByRole('button', { name: '回放并对比', exact: true }).click()
  await page.getByRole('dialog', { name: '回放已捕获请求' }).waitFor({ timeout: 10000 })
  await page.getByRole('button', { name: '确认发送并对比', exact: true }).click()
  await page.getByRole('dialog', { name: '回放对比结果' }).waitFor({ timeout: 15000 })
  const comparison = await page.getByRole('dialog', { name: '回放对比结果' }).innerText()
  if (!comparison.includes('状态码一致') || comparison.includes('must-not-appear')) throw new Error(`REPLAY_COMPARISON_INVALID:${comparison}`)
  await page.keyboard.press('Escape')
  await page.getByRole('dialog', { name: '回放对比结果' }).waitFor({ state: 'hidden', timeout: 5000 })

  const harFile = path.join(artifacts, 'workbench-input.har')
  await writeFile(harFile, JSON.stringify({ log: { entries: [{ request: { method: 'GET', url: `${targetUrl}?token=har-secret`, headers: [] }, response: { status: 200, content: { mimeType: 'application/json', text: '{"ok":true,"token":"har-secret"}' } }, time: 11 }] } }), 'utf8')
  await page.locator('.traffic-workbench input[type=file]').setInputFiles(harFile)
  await page.getByText('HAR 已导入工作台', { exact: false }).waitFor({ timeout: 15000 })
  await page.screenshot({ path: path.join(artifacts, 'traffic-workbench.png'), fullPage: true })
  if (errors.length) throw new Error(`RENDERER_ERRORS:${errors.join(' | ')}`)
  console.log(JSON.stringify({ passed: true, checks: ['session-list', 'filters', 'redacted-detail', 'explicit-replay', 'semantic-diff', 'har-workbench-import'], sessionId: created.id }))
} finally {
  await browser?.close().catch(() => {})
  await new Promise(resolve => server.close(resolve))
  await rm(path.join(artifacts, 'workbench-input.har'), { force: true }).catch(() => {})
}
