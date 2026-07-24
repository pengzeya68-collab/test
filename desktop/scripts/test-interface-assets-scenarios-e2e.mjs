import { chromium } from 'playwright'

const pause = (page, milliseconds = 550) => page.waitForTimeout(milliseconds)
const browser = await chromium.connectOverCDP('http://127.0.0.1:9333')
let groupName = ''
let scenarioName = ''
let scenarioId = null

try {
  const page = browser.contexts()[0].pages()[0]
  const errors = []
  page.on('pageerror', error => errors.push(error.message))
  page.on('console', message => { if (message.type() === 'error') errors.push(message.text()) })

  // Interface group: create through the user-facing dialog and verify server persistence.
  groupName = `桌面验收分组-${Date.now()}`
  await page.evaluate(() => { location.hash = '#/cases' })
  await page.getByRole('heading', { name: '接口用例', exact: true }).waitFor({ timeout: 15000 })
  await pause(page)
  await page.locator('.case-tree-sidebar [title="新建根分组"]').click()
  const groupDialog = page.getByRole('dialog', { name: '新建根分组' })
  await groupDialog.getByPlaceholder('输入分组名称').fill(groupName)
  await pause(page)
  await groupDialog.getByRole('button', { name: '确定', exact: true }).click()
  await page.getByText('创建成功', { exact: true }).waitFor({ timeout: 15000 })
  await pause(page)
  await page.getByText(groupName, { exact: true }).waitFor({ timeout: 15000 })

  const groupPersisted = await page.evaluate(async name => {
    const response = await fetch('http://127.0.0.1:5001/api/auto-test/groups/tree', {
      headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
    })
    const tree = await response.json()
    const visit = nodes => nodes.flatMap(item => [item, ...visit(item.children || [])])
    return visit(tree).find(item => item.name === name) || null
  }, groupName)
  if (!groupPersisted?.id) throw new Error('GROUP_NOT_PERSISTED')

  // Scenario CRUD is a separate module and must retain edits before its run guard is checked.
  scenarioName = `桌面验收场景-${Date.now()}`
  await page.evaluate(() => { location.hash = '#/scenarios' })
  await page.getByRole('heading', { name: '业务场景', exact: true }).waitFor({ timeout: 15000 })
  await pause(page)
  await page.getByRole('button', { name: '新建场景', exact: true }).click()
  const createScenario = page.getByRole('dialog', { name: '新建场景' })
  await createScenario.getByPlaceholder('请输入场景名称').fill(scenarioName)
  await createScenario.getByPlaceholder('场景描述（可选）').fill('真实桌面验收创建、编辑、运行保护与清理')
  await pause(page)
  await createScenario.getByRole('button', { name: '确定', exact: true }).click()
  await page.getByText('创建成功', { exact: true }).waitFor({ timeout: 15000 })
  await page.waitForURL(/#\/scenarios\/\d+$/, { timeout: 15000 })
  scenarioId = Number((await page.evaluate(() => location.hash)).split('/').pop())
  await pause(page)

  // An empty scenario must refuse to produce a false-success execution.
  await page.getByRole('button', { name: '运行场景', exact: true }).click()
  await page.getByText('当前场景没有可执行步骤。请先添加接口用例或流程控制步骤。', { exact: true }).waitFor({ timeout: 15000 })

  const scenarioPersisted = await page.evaluate(async id => {
    const response = await fetch(`http://127.0.0.1:5001/api/auto-test/scenarios/${id}`, {
      headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
    })
    return response.ok ? response.json() : null
  }, scenarioId)
  if (!scenarioPersisted || scenarioPersisted.name !== scenarioName) throw new Error('SCENARIO_CREATE_NOT_PERSISTED')

  await page.evaluate(() => { location.hash = '#/scenarios' })
  const card = page.locator('.scenario-card').filter({ hasText: scenarioName })
  await card.waitFor({ timeout: 15000 })
  await card.getByRole('button', { name: '更多', exact: true }).click()
  await page.getByRole('menuitem', { name: '删除场景', exact: true }).click()
  const deleteBox = page.locator('.el-message-box')
  await deleteBox.getByRole('button', { name: '坚决删除', exact: true }).click()
  await page.getByText('清理完毕！', { exact: true }).waitFor({ timeout: 15000 })
  await card.waitFor({ state: 'detached', timeout: 15000 })

  if (errors.length) throw new Error(`RENDERER_ERRORS:${errors.join(' | ')}`)
  console.log(JSON.stringify({ passed: true, checks: ['group-create-server-persistence', 'scenario-create-navigation-server-persistence', 'empty-scenario-run-guard', 'scenario-delete'], slowUserPauses: true }))
} finally {
  const page = browser.contexts()[0].pages()[0]
  if (scenarioId) await page.evaluate(async id => fetch(`http://127.0.0.1:5001/api/auto-test/scenarios/${id}`, { method: 'DELETE', headers: { Authorization: `Bearer ${localStorage.getItem('token')}` } }), scenarioId).catch(() => {})
  if (groupName) await page.evaluate(async name => {
    const headers = { Authorization: `Bearer ${localStorage.getItem('token')}` }
    const response = await fetch('http://127.0.0.1:5001/api/auto-test/groups/tree', { headers })
    const tree = await response.json()
    const visit = nodes => nodes.flatMap(item => [item, ...visit(item.children || [])])
    const group = visit(tree).find(item => item.name === name)
    if (group) await fetch(`http://127.0.0.1:5001/api/auto-test/groups/${group.id}`, { method: 'DELETE', headers })
  }, groupName).catch(() => {})
  await browser.close()
}
