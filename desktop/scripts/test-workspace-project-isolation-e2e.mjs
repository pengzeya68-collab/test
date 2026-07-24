import { chromium } from 'playwright'

const browser = await chromium.connectOverCDP('http://127.0.0.1:9333')
const pause = (page, ms = 450) => page.waitForTimeout(ms)

async function listPages(page, projectId) {
  return page.evaluate(async ({ projectId }) => {
    const response = await fetch(`http://127.0.0.1:5001/api/feature-upgrades/pages?project_id=${projectId}`, {
      headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
    })
    return { status: response.status, body: await response.json() }
  }, { projectId })
}

try {
  const page = browser.contexts()[0].pages()[0]
  const errors = []
  page.on('pageerror', error => errors.push(error.message))
  page.on('console', message => {
    if (message.type() === 'error' && !/Failed to load resource: the server responded with a status of 422/.test(message.text())) errors.push(message.text())
  })
  page.on('response', response => { if (response.status() >= 500) errors.push(`${response.status()} ${response.url()}`) })

  const suffix = Date.now()
  const projectA = `项目隔离验收 A ${suffix}`
  const projectB = `项目隔离验收 B ${suffix}`
  const objectPage = `结算页面-${suffix}`
  const elementName = `提交订单-${suffix}`

  await page.evaluate(() => { location.hash = '#/workspace-projects' })
  await page.getByRole('heading', { name: '工作区项目', exact: true }).waitFor({ timeout: 15000 })
  await page.getByRole('button', { name: '新建项目', exact: true }).click()
  let prompt = page.locator('.el-message-box')
  await prompt.getByRole('button', { name: '取消', exact: true }).click()
  await page.getByRole('button', { name: '新建项目', exact: true }).click()
  prompt = page.locator('.el-message-box')
  await prompt.getByRole('button', { name: '创建', exact: true }).click()
  await page.getByText('名称不能为空', { exact: true }).waitFor({ timeout: 10000 })
  await prompt.locator('input').fill(projectA)
  const createAResponse = page.waitForResponse(response => response.url().includes('/api/workspace/projects') && response.request().method() === 'POST', { timeout: 15000 })
  await prompt.getByRole('button', { name: '创建', exact: true }).click()
  const createA = await createAResponse
  if (!createA.ok()) throw new Error(`PROJECT_A_CREATE_HTTP_${createA.status()}:${await createA.text()}`)
  const rowA = page.getByRole('row', { name: new RegExp(projectA) })
  await rowA.waitFor({ timeout: 15000 })
  const activeA = await page.evaluate(() => localStorage.getItem('desktop-active-project-id'))
  if (!activeA || Number(activeA) <= 0) throw new Error('PROJECT_A_NOT_ACTIVATED')

  await page.evaluate(() => { location.hash = '#/ui-automation/elements' })
  await page.getByRole('heading', { name: '元素仓库', exact: true }).first().waitFor({ timeout: 15000 })
  await page.getByRole('button', { name: '新建页面', exact: true }).click()
  let dialog = page.getByRole('dialog', { name: '新建页面' })
  await dialog.getByRole('button', { name: '创建', exact: true }).click()
  await page.getByText('请输入页面名称', { exact: true }).waitFor({ timeout: 10000 })
  await dialog.locator('.el-form-item').filter({ hasText: '名称' }).locator('input').fill(objectPage)
  await dialog.locator('.el-form-item').filter({ hasText: 'URL 模式' }).locator('input').fill('/checkout*')
  await dialog.getByRole('button', { name: '创建', exact: true }).click()
  await page.getByText('页面已创建', { exact: true }).waitFor({ timeout: 15000 })
  await page.getByText(objectPage, { exact: true }).waitFor({ timeout: 15000 })
  await page.getByText(objectPage, { exact: true }).click()
  await page.getByRole('button', { name: '新建元素', exact: true }).click()
  dialog = page.getByRole('dialog', { name: '新建元素' })
  await dialog.getByRole('button', { name: '创建', exact: true }).click()
  await page.getByText('请完善元素信息', { exact: true }).waitFor({ timeout: 10000 })
  await dialog.locator('.el-form-item').filter({ hasText: '名称' }).locator('input').fill(elementName)
  await dialog.locator('.el-form-item').filter({ hasText: '值' }).locator('input').fill('submit-order')
  await dialog.getByRole('button', { name: '创建', exact: true }).click()
  await page.getByText('元素已创建', { exact: true }).waitFor({ timeout: 15000 })
  await page.getByText(elementName, { exact: true }).waitFor({ timeout: 15000 })
  const pagesA = await listPages(page, Number(activeA))
  if (pagesA.status !== 200 || !pagesA.body.items?.some(item => item.name === objectPage)) throw new Error('PROJECT_A_PAGE_NOT_PERSISTED')

  await page.evaluate(() => { location.hash = '#/workspace-projects' })
  await page.getByRole('button', { name: '新建项目', exact: true }).click()
  prompt = page.locator('.el-message-box')
  await prompt.locator('input').fill(projectB)
  const createBResponse = page.waitForResponse(response => response.url().includes('/api/workspace/projects') && response.request().method() === 'POST', { timeout: 15000 })
  await prompt.getByRole('button', { name: '创建', exact: true }).click()
  const createB = await createBResponse
  if (!createB.ok()) throw new Error(`PROJECT_B_CREATE_HTTP_${createB.status()}:${await createB.text()}`)
  await page.getByRole('row', { name: new RegExp(projectB) }).waitFor({ timeout: 15000 })
  const activeB = await page.evaluate(() => localStorage.getItem('desktop-active-project-id'))
  if (!activeB || activeB === activeA) throw new Error('PROJECT_B_NOT_ACTIVATED')
  await page.evaluate(() => { location.hash = '#/ui-automation/elements' })
  await page.getByRole('heading', { name: '元素仓库', exact: true }).first().waitFor({ timeout: 15000 })
  await pause(page)
  if (await page.getByText(objectPage, { exact: true }).count()) throw new Error('PROJECT_ASSET_LEAKED_TO_PROJECT_B')
  const pagesB = await listPages(page, Number(activeB))
  if (pagesB.status !== 200 || pagesB.body.items?.some(item => item.name === objectPage)) throw new Error('PROJECT_B_API_ASSET_LEAK')

  const headerSelect = page.locator('.project-switcher')
  await headerSelect.click()
  await page.locator('.el-select-dropdown:visible').getByText(projectA, { exact: true }).click()
  await page.getByText(objectPage, { exact: true }).waitFor({ timeout: 15000 })
  if ((await page.evaluate(() => localStorage.getItem('desktop-active-project-id'))) !== activeA) throw new Error('HEADER_PROJECT_SWITCH_NOT_PERSISTED')

  if (errors.length) throw new Error(`RENDERER_ERRORS:${errors.join(' | ')}`)
  console.log(JSON.stringify({ passed: true, checks: ['project-cancel', 'project-required-validation', 'project-create-activate', 'page-object-create', 'element-create', 'project-api-isolation', 'project-ui-isolation', 'header-switch-remount'] }))
} finally {
  // Workspace projects intentionally have no user delete endpoint. This runs
  // only in the isolated acceptance profile, which the runner removes on exit.
  await browser.close()
}
