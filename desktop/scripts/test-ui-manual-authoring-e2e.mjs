import { chromium } from 'playwright'

const pause = (page, milliseconds = 800) => page.waitForTimeout(milliseconds)
const browser = await chromium.connectOverCDP('http://127.0.0.1:9333')
let caseName = ''
let caseId = null

try {
  const page = browser.contexts()[0].pages()[0]
  const errors = []
  const validationFailures = []
  page.on('pageerror', error => errors.push(error.message))
  page.on('console', message => {
    if (message.type() === 'error') errors.push(message.text())
  })
  page.on('response', async response => {
    if (response.status() !== 422) return
    validationFailures.push({ url: response.url(), body: await response.text().catch(() => '') })
  })

  caseName = `桌面手工编排验收-${Date.now()}`
  const title = `manual-ui-${Date.now()}`
  await page.evaluate(() => { location.hash = '#/ui-automation/cases' })
  await page.locator('.ui-case-list .page-header h2').waitFor({ timeout: 15000 })
  await pause(page)
  await page.getByRole('button', { name: '新建用例', exact: true }).click()
  const createDialog = page.getByRole('dialog', { name: '新建 UI 用例' })
  await createDialog.locator('.el-form-item').filter({ hasText: '用例名称' }).locator('input').fill(caseName)
  await createDialog.locator('.el-form-item').filter({ hasText: '描述' }).locator('textarea').fill('验证桌面端手工添加 UI 自动化步骤、保存、运行与记录')
  await pause(page)
  await createDialog.getByRole('button', { name: '创建', exact: true }).click()
  await page.getByText('创建成功', { exact: true }).waitFor({ timeout: 15000 })
  await page.waitForURL(/#\/ui-automation\/cases\/\d+$/, { timeout: 15000 })
  caseId = Number((await page.evaluate(() => location.hash)).split('/').pop())
  if (!Number.isInteger(caseId)) throw new Error('UI_CASE_CREATE_NO_ID')
  await page.getByText('用户操作流程', { exact: true }).waitFor({ timeout: 15000 })
  await pause(page)

  await page.getByRole('button', { name: '手工添加', exact: true }).click()
  const actionDialog = page.getByRole('dialog', { name: '添加测试步骤' })
  await actionDialog.getByRole('button', { name: '打开网页', exact: true }).click()
  const inspector = page.locator('aside.inspector')
  await inspector.getByRole('heading', { name: '打开网页', exact: true }).waitFor({ timeout: 15000 })
  await inspector.locator('.el-form-item').filter({ hasText: '页面地址' }).locator('input').fill(`data:text/html,<title>${title}</title><main><h1>${title}</h1></main>`)
  await pause(page)

  await page.getByRole('button', { name: '搜索并添加', exact: true }).click()
  const assertDialog = page.getByRole('dialog', { name: '添加测试步骤' })
  await assertDialog.getByRole('button', { name: '检查页面标题', exact: true }).click()
  await inspector.getByRole('heading', { name: '检查页面标题', exact: true }).waitFor({ timeout: 15000 })
  await inspector.locator('.el-form-item').filter({ hasText: '预期结果' }).locator('input').fill(title)
  await pause(page)
  await page.getByRole('button', { name: '保存', exact: true }).click()
  await page.getByText('用例已保存', { exact: true }).waitFor({ timeout: 15000 })

  const persisted = await page.evaluate(async id => {
    const response = await fetch(`http://127.0.0.1:5001/api/ui-automation/cases/${id}`, {
      headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
    })
    return response.json()
  }, caseId)
  if (persisted.name !== caseName || persisted.steps?.length !== 2 || persisted.steps[0]?.type !== 'goto' || persisted.steps[1]?.type !== 'assert_title') {
    throw new Error(`UI_MANUAL_STEPS_NOT_PERSISTED:${JSON.stringify(persisted)}`)
  }

  await page.getByRole('button', { name: '运行完整流程', exact: true }).click()
  await page.getByText('运行结束：通过', { exact: false }).waitFor({ timeout: 45000 })
  await pause(page, 1200)
  const run = await page.evaluate(async id => {
    const response = await fetch(`http://127.0.0.1:5001/api/ui-automation/runs?case_id=${id}`, {
      headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
    })
    const result = await response.json()
    return result.items?.[0] ?? null
  }, caseId)
  if (run?.status !== 'passed' || run.passed_steps !== 2) throw new Error(`UI_MANUAL_RUN_NOT_PASSED:${JSON.stringify(run)}`)

  await page.keyboard.press('Escape')
  await page.getByRole('dialog', { name: '运行结果' }).waitFor({ state: 'hidden', timeout: 10000 })
  await page.getByRole('button', { name: '用例列表', exact: true }).click()
  const row = page.getByRole('row').filter({ hasText: caseName })
  await row.waitFor({ timeout: 15000 })
  await row.getByRole('button', { name: '运行记录', exact: true }).click()
  await page.getByText('2/2 通过，0 失败', { exact: true }).waitFor({ timeout: 15000 })
  await page.keyboard.press('Escape')
  await row.getByRole('button', { name: '删除', exact: true }).click()
  const confirm = page.locator('.el-message-box')
  await confirm.getByRole('button', { name: '确定', exact: true }).click()
  await page.getByText('已删除', { exact: true }).waitFor({ timeout: 15000 })
  await row.waitFor({ state: 'detached', timeout: 15000 })
  caseId = null

  if (errors.length) throw new Error(`RENDERER_ERRORS:${errors.join(' | ')}; VALIDATION_FAILURES:${JSON.stringify(validationFailures)}`)
  console.log(JSON.stringify({ passed: true, checks: ['ui-case-create', 'manual-goto-step', 'manual-title-assertion', 'step-persistence', 'desktop-execution', 'run-history', 'ui-case-delete'], slowUserPauses: true }))
} finally {
  const page = browser.contexts()[0].pages()[0]
  if (caseId) {
    await page.evaluate(async id => fetch(`http://127.0.0.1:5001/api/ui-automation/cases/${id}`, {
      method: 'DELETE', headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
    }), caseId).catch(() => {})
  }
  await browser.close()
}
