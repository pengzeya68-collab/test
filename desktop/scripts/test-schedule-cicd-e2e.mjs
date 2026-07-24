import { chromium } from 'playwright'

const pause = (page, milliseconds = 650) => page.waitForTimeout(milliseconds)
const browser = await chromium.connectOverCDP('http://127.0.0.1:9333')
let scenarioId = null
let taskId = null

try {
  const page = browser.contexts()[0].pages()[0]
  const errors = []
  page.on('pageerror', error => errors.push(error.message))
  page.on('console', message => { if (message.type() === 'error') errors.push(message.text()) })

  const fixture = await page.evaluate(async () => {
    const headers = { Authorization: `Bearer ${localStorage.getItem('token')}`, 'Content-Type': 'application/json' }
    const response = await fetch('http://127.0.0.1:5001/api/auto-test/scenarios', {
      method: 'POST', headers,
      body: JSON.stringify({ name: `调度与CI验收-${Date.now()}`, description: 'desktop acceptance', is_active: true }),
    })
    const scenario = await response.json()
    if (!response.ok || !scenario.id || !scenario.webhook_token) throw new Error(`SCENARIO_FIXTURE_FAILED:${JSON.stringify(scenario)}`)
    return scenario
  })
  scenarioId = fixture.id

  // The shared acceptance renderer may already be on this route. Leave it
  // first so the list remounts and fetches the fixture created above.
  await page.evaluate(() => { location.hash = '#/dashboard' })
  await page.getByText('今天的测试工作', { exact: true }).waitFor({ timeout: 15000 })
  await page.evaluate(() => { location.hash = '#/scenarios' })
  const card = page.locator('.scenario-card').filter({ hasText: fixture.name })
  await card.waitFor({ timeout: 30000 })
  await card.getByRole('button', { name: /^更多/ }).click()
  await page.locator('.el-dropdown-menu:visible').getByText('定时计划', { exact: true }).click()
  const scheduleDialog = page.getByRole('dialog', { name: '定时计划配置' })
  await scheduleDialog.waitFor({ timeout: 15000 })
  await scheduleDialog.getByRole('button', { name: '保存', exact: true }).click()
  await pause(page)

  const task = await page.evaluate(async id => {
    const response = await fetch('http://127.0.0.1:5001/api/auto-test/scheduler/tasks', { headers: { Authorization: `Bearer ${localStorage.getItem('token')}` } })
    const tasks = await response.json()
    return Array.isArray(tasks) ? tasks.find(item => item.scenario_id === id) : null
  }, scenarioId)
  if (!task?.task_id || task.is_active !== true) throw new Error(`SCHEDULE_NOT_PERSISTED:${JSON.stringify(task)}`)
  taskId = task.task_id

  await card.getByRole('button', { name: /^更多/ }).click()
  await page.locator('.el-dropdown-menu:visible').getByText('定时计划', { exact: true }).click()
  await scheduleDialog.waitFor({ timeout: 15000 })
  const toggle = scheduleDialog.locator('.existing-tasks .el-switch').first()
  await toggle.click()
  await pause(page, 900)
  const paused = await page.evaluate(async id => {
    const response = await fetch('http://127.0.0.1:5001/api/auto-test/scheduler/tasks', { headers: { Authorization: `Bearer ${localStorage.getItem('token')}` } })
    const tasks = await response.json()
    return Array.isArray(tasks) ? tasks.find(item => item.task_id === id) : null
  }, taskId)
  if (!paused || paused.is_active !== false) throw new Error(`SCHEDULE_TOGGLE_NOT_PERSISTED:${JSON.stringify(paused)}`)

  const immediate = await page.evaluate(async id => {
    const response = await fetch(`http://127.0.0.1:5001/api/auto-test/scheduler/tasks/${id}/run`, {
      method: 'POST', headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
    })
    return { status: response.status, body: await response.json().catch(() => null) }
  }, taskId)
  if (immediate.status !== 200 || !immediate.body?.celery_task_id) throw new Error(`SCHEDULE_RUN_NOW_FAILED:${JSON.stringify(immediate)}`)

  await page.keyboard.press('Escape')
  await card.getByRole('button', { name: /^更多/ }).click()
  await page.locator('.el-dropdown-menu:visible').getByText('CI/CD 集成', { exact: true }).click()
  const ciDialog = page.getByRole('dialog', { name: 'CI/CD Webhook 触发配置' })
  await ciDialog.waitFor({ timeout: 15000 })
  const endpointInput = ciDialog.getByLabel('可被 CI 访问的 TestMaster 服务地址')
  await endpointInput.fill('https://testmaster.example.com/')
  const command = await ciDialog.locator('.curl-command-box').innerText()
  const expectedPath = `/api/auto-test/scenarios/webhook/${fixture.webhook_token}`
  if (!command.includes(`https://testmaster.example.com${expectedPath}`) || command.includes('file://')) {
    throw new Error(`CICD_COMMAND_INVALID:${command}`)
  }
  if (errors.length) throw new Error(`RENDERER_ERRORS:${errors.join(' | ')}`)
  console.log(JSON.stringify({ passed: true, checks: ['schedule-create-ui', 'schedule-persistence', 'schedule-toggle', 'schedule-run-now', 'cicd-public-base-url', 'cicd-api-path'], slowUserPauses: true }))
} finally {
  const page = browser.contexts()[0]?.pages()[0]
  if (page && taskId) await page.evaluate(async id => fetch(`http://127.0.0.1:5001/api/auto-test/scheduler/tasks/${id}`, { method: 'DELETE', headers: { Authorization: `Bearer ${localStorage.getItem('token')}` } }), taskId).catch(() => {})
  if (page && scenarioId) await page.evaluate(async id => fetch(`http://127.0.0.1:5001/api/auto-test/scenarios/${id}`, { method: 'DELETE', headers: { Authorization: `Bearer ${localStorage.getItem('token')}` } }), scenarioId).catch(() => {})
  await browser.close()
}
