import { chromium } from 'playwright'

const browser = await chromium.connectOverCDP('http://127.0.0.1:9333')
const pause = (page, ms = 500) => page.waitForTimeout(ms)
let primaryChannelId = null
let emailChannelId = null

async function api(page, path, options = {}) {
  return page.evaluate(async ({ path, options }) => {
    const headers = {
      Authorization: `Bearer ${localStorage.getItem('token')}`,
      ...(options.body ? { 'content-type': 'application/json' } : {}),
    }
    const projectId = localStorage.getItem('desktop-active-project-id')
    if (projectId && Number(projectId) > 0) headers['X-Project-Id'] = projectId
    const response = await fetch(`http://127.0.0.1:5001${path}`, { ...options, headers })
    const text = await response.text()
    let body = null
    try { body = text ? JSON.parse(text) : null } catch { body = text }
    return { status: response.status, body }
  }, { path, options })
}

async function assertVisibleError(page, pattern) {
  const message = page.locator('.el-message--error').last()
  await message.waitFor({ state: 'visible', timeout: 10000 })
  const text = (await message.innerText()).trim()
  if (!text || (pattern && !pattern.test(text))) throw new Error(`EXPECTED_ERROR_FEEDBACK_MISSING:${text}`)
}

async function clearErrors(page) {
  await page.locator('.el-message--error').evaluateAll(nodes => nodes.forEach(node => node.remove()))
}

try {
  const page = browser.contexts()[0].pages()[0]
  const errors = []
  const expectedFailures = new Set()
  page.on('pageerror', error => errors.push(`pageerror:${error.message}`))
  page.on('console', message => {
    // Axios surfaces expected 4xx/502 validation paths as browser resource
    // errors. The matching UI feedback and response listener below assert
    // those cases explicitly; retain all other renderer errors.
    if (message.type() === 'error' && !/Failed to load resource: the server responded with a status of (422|502)/.test(message.text())) {
      errors.push(`console:${message.text()}`)
    }
  })
  page.on('response', response => {
    if (response.status() >= 500 && !expectedFailures.has(response.url())) errors.push(`http:${response.status()} ${response.url()}`)
  })

  const suffix = Date.now()
  const name = `通知验收机器人-${suffix}`
  const editedName = `${name}-已编辑`
  const emailName = `通知验收邮件-${suffix}`
  await page.evaluate(() => { location.hash = '#/notification-center' })
  await page.getByRole('heading', { name: '任务通知中心', exact: true }).first().waitFor({ timeout: 15000 })

  // A cancelled dialog and a required-field failure must not create ghost records.
  await page.getByRole('button', { name: '新增通知渠道', exact: true }).click()
  let dialog = page.getByRole('dialog', { name: '新增通知渠道' })
  await dialog.getByRole('button', { name: '取消', exact: true }).click()
  await dialog.waitFor({ state: 'hidden', timeout: 5000 })
  await page.getByRole('button', { name: '新增通知渠道', exact: true }).click()
  dialog = page.getByRole('dialog', { name: '新增通知渠道' })
  await clearErrors(page)
  await dialog.getByRole('button', { name: '保存', exact: true }).click()
  await assertVisibleError(page)
  await dialog.locator('.el-form-item').filter({ hasText: '渠道名称' }).locator('input').fill(name)
  await dialog.locator('.el-form-item').filter({ hasText: '机器人 / Webhook HTTPS 地址' }).locator('input').fill('http://not-secure.example.test/hook')
  await clearErrors(page)
  await dialog.getByRole('button', { name: '保存', exact: true }).click()
  await assertVisibleError(page, /HTTPS/)
  await dialog.locator('.el-form-item').filter({ hasText: '机器人 / Webhook HTTPS 地址' }).locator('input').fill('https://example.invalid/testmaster-acceptance')
  await dialog.getByRole('button', { name: '保存', exact: true }).click()
  await page.getByText('通知渠道已保存', { exact: true }).last().waitFor({ timeout: 15000 })
  const row = page.locator('tr').filter({ hasText: name })
  await row.waitFor({ timeout: 15000 })

  let channels = await api(page, '/api/auto-test/notification-channels')
  const created = channels.body?.channels?.find(item => item.name === name)
  primaryChannelId = created?.id ?? null
  if (!primaryChannelId || created.destination !== 'example.invalid' || created.configured !== true) throw new Error(`NOTIFICATION_CHANNEL_NOT_PERSISTED_OR_REDACTED_INCORRECTLY:${JSON.stringify({ created, channels: channels.body })}`)

  // Editing without exposing the encrypted address must preserve it server-side.
  await row.getByRole('button', { name: '编辑', exact: true }).click()
  dialog = page.getByRole('dialog', { name: '编辑通知渠道' })
  await dialog.locator('.el-form-item').filter({ hasText: '渠道名称' }).locator('input').fill(editedName)
  await dialog.getByRole('button', { name: '保存', exact: true }).click()
  await page.getByText('通知渠道已保存', { exact: true }).last().waitFor({ timeout: 15000 })
  await page.locator('tr').filter({ hasText: editedName }).waitFor({ timeout: 15000 })
  channels = await api(page, '/api/auto-test/notification-channels')
  const edited = channels.body?.channels?.find(item => item.id === primaryChannelId)
  if (edited?.name !== editedName || edited.destination !== 'example.invalid' || edited.configured !== true) throw new Error('NOTIFICATION_EDIT_DROPPED_SAVED_SECRET')

  // Verify the channel-type switch and email validation rather than only the default webhook form.
  await page.getByRole('button', { name: '新增通知渠道', exact: true }).click()
  dialog = page.getByRole('dialog', { name: '新增通知渠道' })
  await dialog.locator('.el-form-item').filter({ hasText: '渠道名称' }).locator('input').fill(emailName)
  await dialog.locator('.el-form-item').filter({ hasText: '通知渠道' }).locator('.el-select').click()
  await page.locator('.el-select-dropdown:visible').getByText('邮件', { exact: true }).click()
  await dialog.getByText('收件人', { exact: true }).waitFor({ timeout: 5000 })
  await dialog.locator('.el-form-item').filter({ hasText: '收件人' }).locator('input').fill('not-an-email')
  await clearErrors(page)
  await dialog.getByRole('button', { name: '保存', exact: true }).click()
  await assertVisibleError(page)
  await dialog.locator('.el-form-item').filter({ hasText: '收件人' }).locator('input').fill(`qa-${suffix}@example.com, dev-${suffix}@example.com`)
  await dialog.getByRole('button', { name: '保存', exact: true }).click()
  await page.getByText('通知渠道已保存', { exact: true }).last().waitFor({ timeout: 15000 })
  channels = await api(page, '/api/auto-test/notification-channels')
  const email = channels.body?.channels?.find(item => item.name === emailName)
  emailChannelId = email?.id ?? null
  if (!emailChannelId || !String(email.destination).includes(`qa-${suffix}@example.com`)) throw new Error('EMAIL_CHANNEL_NOT_PERSISTED')

  // The UI must show a concrete failure when a delivery cannot be made. The
  // isolated desktop backend has no SMTP transport, making this deterministic
  // without relying on an external endpoint or DNS timeout.
  const testUrl = `http://127.0.0.1:5001/api/auto-test/notification-channels/${emailChannelId}/test`
  expectedFailures.add(testUrl)
  await clearErrors(page)
  await page.locator('tr').filter({ hasText: emailName }).getByRole('button', { name: '测试', exact: true }).click()
  await assertVisibleError(page)

  // Deletion requires confirmation; cancellation keeps data, confirmation removes it.
  const emailRow = page.locator('tr').filter({ hasText: emailName })
  await emailRow.getByRole('button', { name: '删除', exact: true }).click()
  await page.locator('.el-message-box').getByRole('button', { name: '取消', exact: true }).click()
  await emailRow.waitFor({ timeout: 5000 })
  await emailRow.getByRole('button', { name: '删除', exact: true }).click()
  await page.locator('.el-message-box').getByRole('button', { name: '确定', exact: true }).click()
  await page.getByText('已删除', { exact: true }).last().waitFor({ timeout: 15000 })
  await emailRow.waitFor({ state: 'detached', timeout: 15000 })
  emailChannelId = null
  const primaryRow = page.locator('tr').filter({ hasText: editedName })
  await primaryRow.getByRole('button', { name: '删除', exact: true }).click()
  await page.locator('.el-message-box').getByRole('button', { name: '确定', exact: true }).click()
  await page.getByText('已删除', { exact: true }).last().waitFor({ timeout: 15000 })
  await primaryRow.waitFor({ state: 'detached', timeout: 15000 })
  primaryChannelId = null

  await pause(page)
  if (errors.length) throw new Error(`RENDERER_ERRORS:${errors.join(' | ')}`)
  console.log(JSON.stringify({ passed: true, checks: ['cancel', 'required-validation', 'https-validation', 'webhook-create', 'secret-preserving-edit', 'email-type-validation', 'delivery-failure-feedback', 'delete-cancel', 'delete-confirm'] }))
} finally {
  const page = browser.contexts()[0]?.pages()[0]
  if (page && primaryChannelId) await api(page, `/api/auto-test/notification-channels/${primaryChannelId}`, { method: 'DELETE' }).catch(() => {})
  if (page && emailChannelId) await api(page, `/api/auto-test/notification-channels/${emailChannelId}`, { method: 'DELETE' }).catch(() => {})
  await browser.close()
}
