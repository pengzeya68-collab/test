import { chromium } from 'playwright'

const pause = (page, milliseconds = 650) => page.waitForTimeout(milliseconds)
const browser = await chromium.connectOverCDP('http://127.0.0.1:9333')
let groupId = null
let caseId = null

try {
  const page = browser.contexts()[0].pages()[0]
  const errors = []
  page.on('pageerror', error => errors.push(error.message))
  page.on('console', message => { if (message.type() === 'error') errors.push(message.text()) })
  const fixture = await page.evaluate(async () => {
    const headers = { Authorization: `Bearer ${localStorage.getItem('token')}`, 'Content-Type': 'application/json' }
    const stamp = Date.now()
    const groupResponse = await fetch('http://127.0.0.1:5001/api/auto-test/groups', { method: 'POST', headers, body: JSON.stringify({ name: `文档验收分组-${stamp}`, parent_id: null, description: 'desktop API docs acceptance', sort_order: 0 }) })
    const group = await groupResponse.json()
    const caseResponse = await fetch('http://127.0.0.1:5001/api/auto-test/cases', { method: 'POST', headers, body: JSON.stringify({ name: `文档验收接口-${stamp}`, group_id: group.id, method: 'POST', url: '/orders', headers: { 'Content-Type': 'application/json' }, params: { trace: 'true' }, body_type: 'raw', payload: { item: 'book', quantity: 1 }, assertions: [{ target: 'status_code', operator: 'equals', expected: 201 }], description: '用于桌面文档生成的验收接口' }) })
    const apiCase = await caseResponse.json()
    if (!groupResponse.ok || !caseResponse.ok) throw new Error(`DOC_FIXTURE_FAILED:${JSON.stringify({ group, apiCase })}`)
    return { groupId: group.id, caseId: apiCase.id, name: apiCase.name }
  })
  groupId = fixture.groupId
  caseId = fixture.caseId

  await page.evaluate(() => { location.hash = '#/api-doc-preview' })
  await page.locator('.doc-preview-container').waitFor({ timeout: 20000 })
  await page.getByText(fixture.name, { exact: true }).waitFor({ timeout: 20000 })
  await pause(page)
  await page.getByRole('button', { name: '全选', exact: true }).click()
  await page.getByRole('button', { name: '生成文档', exact: true }).click()
  await page.getByText('文档生成成功', { exact: true }).last().waitFor({ timeout: 20000 })
  await page.locator('.json-viewer').getByText(fixture.name, { exact: false }).waitFor({ timeout: 20000 })

  await page.locator('.doc-header .el-radio-button').filter({ hasText: 'Markdown' }).click()
  await page.getByText('文档生成成功', { exact: true }).last().waitFor({ timeout: 20000 })
  await page.locator('.markdown-body h3').filter({ hasText: fixture.name }).waitFor({ timeout: 20000 })
  await page.locator('.doc-header .el-radio-button').filter({ hasText: 'HTML' }).click()
  await page.getByText('文档生成成功', { exact: true }).last().waitFor({ timeout: 20000 })
  await page.locator('iframe.html-iframe').waitFor({ timeout: 20000 })
  const html = await page.locator('iframe.html-iframe').getAttribute('srcdoc')
  if (!html?.includes(fixture.name)) throw new Error('HTML_DOC_CONTENT_MISSING')

  await page.getByRole('button', { name: '分享', exact: true }).click()
  const shareDialog = page.getByRole('dialog', { name: '生成分享链接' })
  const offlineExport = page.waitForEvent('download', { timeout: 20000 })
  await shareDialog.getByRole('button', { name: '生成链接', exact: true }).click()
  const download = await offlineExport
  if (!download.suggestedFilename().endsWith('.html')) throw new Error(`OFFLINE_SHARE_EXPORT_INVALID:${download.suggestedFilename()}`)
  await shareDialog.getByText(/离线文档已导出/).waitFor({ timeout: 20000 })
  await shareDialog.getByText(/本机离线模式/).waitFor({ timeout: 20000 })
  if (await shareDialog.getByTestId('share-url-input').count()) {
    throw new Error('OFFLINE_SHARE_MUST_NOT_RENDER_A_FILE_URL')
  }

  if (errors.length) throw new Error(`RENDERER_ERRORS:${errors.join(' | ')}`)
  console.log(JSON.stringify({ passed: true, checks: ['fixture-create', 'openapi-generate', 'markdown-generate', 'html-generate', 'offline-share-export'], slowUserPauses: true }))
} finally {
  const page = browser.contexts()[0]?.pages()[0]
  if (page && caseId) await page.evaluate(async id => fetch(`http://127.0.0.1:5001/api/auto-test/cases/${id}`, { method: 'DELETE', headers: { Authorization: `Bearer ${localStorage.getItem('token')}` } }), caseId).catch(() => {})
  if (page && groupId) await page.evaluate(async id => fetch(`http://127.0.0.1:5001/api/auto-test/groups/${id}`, { method: 'DELETE', headers: { Authorization: `Bearer ${localStorage.getItem('token')}` } }), groupId).catch(() => {})
  await browser.close()
}
