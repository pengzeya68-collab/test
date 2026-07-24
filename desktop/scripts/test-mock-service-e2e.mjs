import { chromium } from 'playwright'

const pause = (page, milliseconds = 750) => page.waitForTimeout(milliseconds)
const browser = await chromium.connectOverCDP('http://127.0.0.1:9333')
let projectName = ''
let projectSlug = ''
let projectId = null

const formItem = (dialog, label) => dialog.locator('.el-form-item').filter({ hasText: label })

try {
  const page = browser.contexts()[0].pages()[0]
  const errors = []
  page.on('pageerror', error => errors.push(error.message))
  page.on('console', message => {
    if (message.type() === 'error') errors.push(message.text())
  })

  projectName = `桌面Mock验收-${Date.now()}`
  projectSlug = `desktop-mock-${Date.now()}`
  const normalRuleName = `正常规则-${Date.now()}`
  const faultRuleName = `故障响应头规则-${Date.now()}`

  await page.evaluate(() => { location.hash = '#/mock-service' })
  await page.getByRole('heading', { name: 'Mock 服务管理', exact: true }).waitFor({ timeout: 15000 })
  await pause(page)

  await page.getByRole('button', { name: '新建项目', exact: true }).click()
  const projectDialog = page.getByRole('dialog', { name: '新建项目' })
  await formItem(projectDialog, '项目名称').locator('input').fill(projectName)
  await formItem(projectDialog, 'URL标识').locator('input').fill(projectSlug)
  await formItem(projectDialog, '描述').locator('textarea').fill('桌面端真实 Mock 服务验收，完成后清理')
  await pause(page)
  await projectDialog.getByRole('button', { name: '保存', exact: true }).click()
  await page.getByText('项目创建成功', { exact: true }).waitFor({ timeout: 15000 })
  const card = page.locator('.project-card').filter({ hasText: projectName })
  await card.waitFor({ timeout: 15000 })

  projectId = await page.evaluate(async name => {
    const response = await fetch('http://127.0.0.1:5001/api/mock/projects', {
      headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
    })
    const body = await response.json()
    return body.list?.find(item => item.name === name)?.id ?? null
  }, projectName)
  if (!projectId) throw new Error('MOCK_PROJECT_NOT_PERSISTED')

  await card.click()
  await page.getByRole('heading', { name: `Mock 规则 - ${projectName}`, exact: true }).waitFor({ timeout: 15000 })
  await pause(page)

  await page.getByRole('button', { name: '新建规则', exact: true }).click()
  const normalDialog = page.getByRole('dialog', { name: '新建规则' })
  await formItem(normalDialog, '规则名称').locator('input').fill(normalRuleName)
  await formItem(normalDialog, '请求路径').locator('input').fill('/orders')
  await formItem(normalDialog, '响应头').locator('textarea').fill('{"X-Acceptance":"normal"}')
  await formItem(normalDialog, '响应体').locator('textarea').fill('{"source":"desktop-mock","order":"@integer(7,7)"}')
  await pause(page)
  await normalDialog.getByRole('button', { name: '保存', exact: true }).click()
  await page.getByText('规则创建成功', { exact: true }).waitFor({ timeout: 15000 })
  await page.getByText(normalRuleName, { exact: true }).waitFor({ timeout: 15000 })

  const normalResponse = await page.evaluate(async slug => {
    const response = await fetch(`http://127.0.0.1:5001/api/mock/${slug}/orders`)
    return { status: response.status, header: response.headers.get('x-acceptance'), body: await response.json() }
  }, projectSlug)
  if (normalResponse.status !== 200 || normalResponse.header !== 'normal' || normalResponse.body.source !== 'desktop-mock' || normalResponse.body.order !== 7) {
    throw new Error(`MOCK_NORMAL_RESPONSE_INVALID:${JSON.stringify(normalResponse)}`)
  }
  await pause(page, 1000)
  await page.getByRole('button', { name: '刷新', exact: true }).click()
  await page.getByText(normalRuleName, { exact: true }).last().waitFor({ timeout: 15000 })

  await page.getByRole('button', { name: '新建规则', exact: true }).click()
  const faultDialog = page.getByRole('dialog', { name: '新建规则' })
  await formItem(faultDialog, '规则名称').locator('input').fill(faultRuleName)
  await formItem(faultDialog, '请求路径').locator('input').fill('/degraded')
  await formItem(faultDialog, '响应体').locator('textarea').fill('{"source":"fault-rule"}')
  await formItem(faultDialog, '故障类型').locator('.el-select').click()
  await page.locator('.el-select-dropdown:visible').getByText('注入自定义响应头', { exact: true }).click()
  await formItem(faultDialog, '注入响应头').locator('textarea').fill('{"X-Feature-Flag":"degraded"}')
  await pause(page)
  await faultDialog.getByRole('button', { name: '保存', exact: true }).click()
  await page.getByText('规则创建成功', { exact: true }).waitFor({ timeout: 15000 })
  await page.getByText(faultRuleName, { exact: true }).waitFor({ timeout: 15000 })

  const faultResponse = await page.evaluate(async slug => {
    const response = await fetch(`http://127.0.0.1:5001/api/mock/${slug}/degraded`)
    return {
      status: response.status,
      feature: response.headers.get('x-feature-flag'),
      fault: response.headers.get('x-testmaster-fault'),
      body: await response.json(),
    }
  }, projectSlug)
  if (faultResponse.status !== 200 || faultResponse.feature !== 'degraded' || faultResponse.fault !== 'custom_headers' || faultResponse.body.source !== 'fault-rule') {
    throw new Error(`MOCK_FAULT_RESPONSE_INVALID:${JSON.stringify(faultResponse)}`)
  }
  await pause(page, 1000)
  await page.getByRole('button', { name: '刷新', exact: true }).click()
  // The fault label is also present in hidden Element Plus select overlays.
  // Wait for the visible log table to finish rendering rather than matching those hidden options.
  await page.locator('.el-table').last().locator('tbody tr').first().waitFor({ timeout: 15000 })

  const logs = await page.evaluate(async id => {
    const response = await fetch(`http://127.0.0.1:5001/api/mock/projects/${id}/logs`, {
      headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
    })
    return response.json()
  }, projectId)
  const normalLog = logs.list?.find(item => item.path === '/orders')
  const faultLog = logs.list?.find(item => item.path === '/degraded')
  if (normalLog?.matched_rule_name !== normalRuleName || faultLog?.fault_type !== 'custom_headers' || !faultLog?.fault_triggered || faultLog.fault_random_value === null || faultLog.fault_random_value === undefined) {
    throw new Error(`MOCK_LOGGING_INCOMPLETE:${JSON.stringify({ normalLog, faultLog })}`)
  }

  await card.locator('.project-actions .el-button--danger').click()
  const confirm = page.locator('.el-message-box')
  await confirm.getByRole('button', { name: '确定', exact: true }).click()
  await page.getByText('删除成功', { exact: true }).waitFor({ timeout: 15000 })
  await card.waitFor({ state: 'detached', timeout: 15000 })
  projectId = null

  if (errors.length) throw new Error(`RENDERER_ERRORS:${errors.join(' | ')}`)
  console.log(JSON.stringify({ passed: true, checks: ['project-create-persistence', 'normal-rule-real-response', 'request-log-ui-and-api', 'custom-header-fault-real-response', 'fault-decision-log', 'project-cascade-delete'], slowUserPauses: true }))
} finally {
  const page = browser.contexts()[0].pages()[0]
  if (projectId) {
    await page.evaluate(async id => fetch(`http://127.0.0.1:5001/api/mock/projects/${id}`, {
      method: 'DELETE', headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
    }), projectId).catch(() => {})
  }
  await browser.close()
}
