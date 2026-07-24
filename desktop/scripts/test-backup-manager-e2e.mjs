import { chromium } from 'playwright'

const pause = (page, milliseconds = 700) => page.waitForTimeout(milliseconds)
const browser = await chromium.connectOverCDP('http://127.0.0.1:9333')
let backupName = null

try {
  const page = browser.contexts()[0].pages()[0]
  const errors = []
  page.on('pageerror', error => errors.push(error.message))
  page.on('console', message => { if (message.type() === 'error') errors.push(message.text()) })

  await page.evaluate(() => { location.hash = '#/backup-manager' })
  await page.getByRole('heading', { name: '🛡️ 数据安全指挥中心', exact: true }).waitFor({ timeout: 20000 })
  await pause(page)
  const beforeCount = await page.locator('.el-table__body-wrapper tbody tr').count()

  await page.getByRole('button', { name: '立即备份', exact: true }).click()
  const confirm = page.locator('.el-message-box')
  const createResponse = page.waitForResponse(response => response.url().endsWith('/api/v1/admin/backups') && response.request().method() === 'POST', { timeout: 15000 })
  await confirm.getByRole('button', { name: '立即执行备份', exact: true }).click()
  const created = await createResponse
  const createdBody = await created.json().catch(() => null)
  if (!created.ok()) throw new Error(`BACKUP_CREATE_REQUEST_FAILED:${created.status()}:${JSON.stringify(createdBody)}`)
  await page.getByText('备份创建成功', { exact: true }).waitFor({ timeout: 30000 })
  await pause(page, 1200)
  const rows = page.locator('.el-table__body-wrapper tbody tr')
  const afterCount = await rows.count()
  if (afterCount <= beforeCount) throw new Error(`BACKUP_LIST_DID_NOT_REFRESH:${beforeCount}->${afterCount}`)
  backupName = (await rows.first().locator('td').nth(1).innerText()).trim()
  if (!backupName) throw new Error('BACKUP_NAME_MISSING')

  // Restore the just-created consistent copy. It contains the same isolated
  // profile state, so this proves the restore path without risking user data.
  const createdRow = rows.filter({ hasText: backupName }).first()
  await createdRow.getByRole('button', { name: '恢复', exact: true }).click()
  const restoreConfirm = page.locator('.el-popconfirm:visible')
  await restoreConfirm.getByRole('button', { name: '确认恢复', exact: true }).click()
  await page.getByText(/SQLite 备份恢复成功|备份恢复成功/, { exact: false }).waitFor({ timeout: 30000 })
  await pause(page, 1000)

  await page.getByRole('tab', { name: '高危操作审计', exact: true }).click()
  await page.getByText(/备份/).first().waitFor({ timeout: 20000 })
  await pause(page)

  await page.getByRole('tab', { name: '主库备份管理', exact: true }).click()
  await createdRow.waitFor({ timeout: 20000 })
  await createdRow.getByRole('button', { name: '删除', exact: true }).click()
  const deleteBox = page.locator('.el-message-box')
  await deleteBox.getByRole('button', { name: /确定|删除/ }).last().click()
  await page.getByText('备份删除成功', { exact: true }).waitFor({ timeout: 20000 })
  await page.locator('.el-table:visible .el-table__body-wrapper tbody tr').filter({ hasText: backupName }).waitFor({ state: 'detached', timeout: 20000 })
  backupName = null

  if (errors.length) throw new Error(`RENDERER_ERRORS:${errors.join(' | ')}`)
  console.log(JSON.stringify({ passed: true, checks: ['desktop-admin-session', 'backup-create', 'backup-list-refresh', 'backup-restore', 'audit-log', 'backup-delete'], slowUserPauses: true }))
} finally {
  // The isolated profile makes backup deletion safe; no production data is touched.
  await browser.close()
}
