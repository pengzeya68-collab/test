import { chromium } from 'playwright'

const pause = (page, milliseconds = 600) => page.waitForTimeout(milliseconds)
const browser = await chromium.connectOverCDP('http://127.0.0.1:9333')
let templateId = null
let templateName = ''

try {
  const page = browser.contexts()[0].pages()[0]
  const errors = []
  page.on('pageerror', error => errors.push(error.message))
  page.on('console', message => { if (message.type() === 'error') errors.push(message.text()) })
  templateName = `桌面数据工厂验收-${Date.now()}`

  await page.evaluate(() => { location.hash = '#/data-factory' })
  await page.locator('.module-heading h1').filter({ hasText: '测试数据工厂' }).waitFor({ timeout: 15000 })
  await pause(page)
  await page.getByRole('button', { name: '新建模板', exact: true }).click()
  await page.locator('.name-input input').fill(templateName)
  await page.getByRole('button', { name: '添加字段', exact: true }).click()
  const field = page.locator('.field-card').first()
  await field.getByPlaceholder('字段名 (英文)').fill('account')
  await field.getByPlaceholder('中文名 (可选)').fill('验收账号')
  await field.getByPlaceholder('输入固定值').fill('desktop-acceptance-user')
  await pause(page)
  await page.getByRole('button', { name: '保存模板', exact: true }).click()
  await page.getByText('模板创建成功', { exact: true }).waitFor({ timeout: 15000 })
  await page.locator('.tpl-item').filter({ hasText: templateName }).waitFor({ timeout: 15000 })

  const template = await page.evaluate(async name => {
    const headers = { Authorization: `Bearer ${localStorage.getItem('token')}` }
    const response = await fetch('http://127.0.0.1:5001/api/auto-test/data-factory/templates', { headers })
    const items = await response.json()
    return (Array.isArray(items) ? items : items.items || []).find(item => item.name === name) || null
  }, templateName)
  templateId = template?.id ?? null
  if (!templateId) throw new Error('DATA_TEMPLATE_NOT_PERSISTED')

  await page.getByRole('button', { name: '刷新预览', exact: true }).click()
  await page.getByText('desktop-acceptance-user', { exact: true }).first().waitFor({ timeout: 15000 })
  await pause(page)
  await page.getByRole('button', { name: '生成数据集', exact: true }).click()
  await page.locator('.result-card .rc-title').getByText('数据集已生成', { exact: true }).waitFor({ timeout: 15000 })
  await page.getByRole('button', { name: '导出 CSV', exact: true }).isEnabled().then(enabled => { if (!enabled) throw new Error('CSV_EXPORT_NOT_ENABLED_AFTER_PREVIEW') })

  const generated = await page.evaluate(async id => {
    const headers = { Authorization: `Bearer ${localStorage.getItem('token')}` }
    const response = await fetch(`http://127.0.0.1:5001/api/auto-test/data-factory/templates/${id}/generate`, { method: 'POST', headers })
    return { status: response.status, body: await response.json() }
  }, templateId)
  if (generated.status !== 200 || generated.body.columns?.[0] !== 'account' || !generated.body.rows?.every(row => row[0] === 'desktop-acceptance-user')) throw new Error('GENERATED_DATA_DOES_NOT_MATCH_RULE')

  await page.getByRole('button', { name: '删除', exact: true }).click()
  const confirm = page.locator('.el-message-box')
  await confirm.getByRole('button', { name: '确定', exact: true }).click()
  await page.getByText('已删除', { exact: true }).waitFor({ timeout: 15000 })
  await page.locator('.tpl-item').filter({ hasText: templateName }).waitFor({ state: 'detached', timeout: 15000 })
  templateId = null
  if (errors.length) throw new Error(`RENDERER_ERRORS:${errors.join(' | ')}`)
  console.log(JSON.stringify({ passed: true, checks: ['template-create', 'fixed-rule-persistence', 'preview', 'generate', 'export-enabled', 'delete'], slowUserPauses: true }))
} finally {
  const page = browser.contexts()[0].pages()[0]
  if (templateId) await page.evaluate(async id => fetch(`http://127.0.0.1:5001/api/auto-test/data-factory/templates/${id}`, { method: 'DELETE', headers: { Authorization: `Bearer ${localStorage.getItem('token')}` } }), templateId).catch(() => {})
  await browser.close()
}
