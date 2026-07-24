import { _electron as electron } from 'playwright'
import { mkdir, rm } from 'node:fs/promises'
import path from 'node:path'

const baseUrl = String(process.env.PRODUCTION_BASE_URL || '').replace(/\/$/, '')
const executablePath = process.env.TESTMASTER_PACKAGED_EXE

if (!/^https?:\/\//.test(baseUrl)) throw new Error('PRODUCTION_BASE_URL is required')
if (!executablePath) throw new Error('TESTMASTER_PACKAGED_EXE is required')

const stamp = `${Date.now()}${Math.floor(Math.random() * 10000)}`
const username = `desktopqa${stamp}`.slice(0, 20)
const password = `Qa${stamp}x9`
const profile = process.env.TESTMASTER_PRODUCTION_DESKTOP_DATA_DIR
  || path.join(path.dirname(executablePath), '..', '..', 'test-artifacts', 'production-desktop-profile')
const artifactDir = path.join(path.dirname(profile), 'production-desktop-artifacts')
let token = ''
let projectId = null
let projectName = ''
let groupId = null
let caseId = null
let scenarioId = null
let uiCaseId = null
let captureId = null
let capturedCaseIds = []
let capturedScenarioId = null
let environmentId = null
let app
let artifactDirReady = false
let completedResult = null
let workflowPassed = false
let cleanupFailure = null

const api = suffix => `${baseUrl}${suffix}`
const json = async (response, label) => {
  const body = await response.json().catch(() => null)
  if (!response.ok) throw new Error(`${label}: HTTP ${response.status} ${JSON.stringify(body)}`)
  return body
}
const headers = (project = false) => ({
  Authorization: `Bearer ${token}`,
  ...(project && projectId ? { 'X-Project-Id': String(projectId) } : {}),
})
const request = async (suffix, options = {}, project = false) => {
  const response = await fetch(api(suffix), {
    ...options,
    headers: { ...headers(project), ...(options.headers || {}) },
  })
  return json(response, suffix)
}

try {
  await rm(profile, { recursive: true, force: true })
  await mkdir(artifactDir, { recursive: true })
  artifactDirReady = true

  const registered = await json(await fetch(api('/api/v1/auth/register'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, email: `${username}@example.test`, password }),
  }), 'register production desktop user')
  token = registered.access_token
  if (!token) throw new Error('REGISTER_DID_NOT_RETURN_TOKEN')

  app = await electron.launch({
    executablePath,
    args: ['--remote-debugging-port=9340', `--user-data-dir=${profile}`],
    env: { ...process.env, TESTMASTER_DESKTOP_DATA_DIR: profile },
  })
  const page = await app.firstWindow()
  const rendererErrors = []
  const requestStartedAfterRemoteConfig = new WeakMap()
  let remoteServiceConfigured = false
  page.on('pageerror', error => rendererErrors.push(error.message))
  page.on('console', message => {
    // Chromium emits this generic console error for every requestfailed event;
    // retain actionable console errors and classify network failures below.
    if (message.type() === 'error' && !message.text().includes('Failed to load resource')) {
      rendererErrors.push(`${message.location().url || 'renderer'}: ${message.text()}`)
    }
  })
  page.on('request', request => requestStartedAfterRemoteConfig.set(request, remoteServiceConfigured))
  page.on('requestfailed', request => {
    if (requestStartedAfterRemoteConfig.get(request)) {
      rendererErrors.push(`${request.url()}: ${request.failure()?.errorText || 'REQUEST_FAILED'}`)
    }
  })

  await page.getByTestId('desktop-login-page').waitFor({ timeout: 45000 })
  const serverInput = page.getByLabel('服务地址')
  await serverInput.fill(baseUrl)
  await serverInput.press('Tab')
  remoteServiceConfigured = true
  await page.getByText('服务连接正常', { exact: true }).waitFor({ timeout: 20000 })
  await page.getByLabel('用户名').fill(username)
  await page.getByLabel('密码').fill(password)
  await page.getByRole('button', { name: '登录', exact: true }).click()
  await page.locator('.desktop-sidebar').waitFor({ timeout: 30000 })

  // This is a desktop UI action against the public server. The server must
  // proxy the request and render a usable response back into the desktop UI.
  await page.evaluate(() => { location.hash = '#/api-debugger' })
  await page.getByRole('heading', { name: '接口调试', exact: true }).waitFor({ timeout: 20000 })
  const urlInput = page.locator('.request-line .url-input input')
  await urlInput.fill(api('/api/health'))
  const debuggerResponse = page.waitForResponse(response =>
    response.url().includes('/api/auto-test/send') && response.request().method() === 'POST',
    { timeout: 20000 },
  )
  await page.getByRole('button', { name: '发送', exact: true }).click()
  const debuggerResult = await debuggerResponse
  if (!debuggerResult.ok()) throw new Error(`DESKTOP_DEBUGGER_HTTP_${debuggerResult.status()}`)
  await page.getByText('200', { exact: false }).first().waitFor({ timeout: 20000 })

  // Create the workspace in the desktop UI, then prove server-side data
  // execution and isolation using the same token/project context.
  projectName = `公网桌面验收项目-${stamp}`
  await page.evaluate(() => { location.hash = '#/workspace-projects' })
  await page.getByRole('heading', { name: '工作区项目', exact: true }).waitFor({ timeout: 20000 })
  await page.getByRole('button', { name: '新建项目', exact: true }).click()
  const projectDialog = page.locator('.el-message-box')
  await projectDialog.locator('input').fill(projectName)
  const createdProjectResponse = page.waitForResponse(response =>
    response.url().includes('/api/workspace/projects') && response.request().method() === 'POST',
    { timeout: 20000 },
  )
  await projectDialog.getByRole('button', { name: '创建', exact: true }).click()
  const createdProject = await json(await createdProjectResponse, 'create project from desktop')
  projectId = Number(createdProject.id)
  if (!projectId) throw new Error('DESKTOP_PROJECT_ID_MISSING')
  await page.getByRole('row', { name: new RegExp(projectName) }).waitFor({ timeout: 20000 })
  if (Number(await page.evaluate(() => localStorage.getItem('desktop-active-project-id'))) !== projectId) {
    throw new Error('DESKTOP_PROJECT_NOT_ACTIVATED')
  }

  const group = await request('/api/auto-test/groups', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name: `公网桌面验收分组-${stamp}`, description: 'desktop production acceptance', sort_order: 0 }),
  }, true)
  groupId = Number(group.id)
  const testCase = await request('/api/auto-test/cases', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      group_id: groupId, name: `公网桌面健康用例-${stamp}`, method: 'GET', url: api('/api/health'),
      body_type: 'none', assertions: [{ target: 'status_code', operator: 'equals', expected: 200 }],
    }),
  }, true)
  caseId = Number(testCase.id)
  const quickRun = await request(`/api/auto-test/cases/${caseId}/quick-run`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' }, true)
  if (!(quickRun.success || quickRun.status === 'passed')) throw new Error(`REMOTE_CASE_RUN_FAILED:${JSON.stringify(quickRun)}`)

  const scenario = await request('/api/auto-test/scenarios', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name: `公网桌面验收场景-${stamp}`, description: 'desktop-to-production closed loop', is_active: true }),
  }, true)
  scenarioId = Number(scenario.id)
  await request(`/api/auto-test/scenarios/${scenarioId}/steps`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ api_case_id: caseId, step_order: 1, is_active: true, step_type: 'api_request' }),
  }, true)
  const scenarioRun = await request(`/api/auto-test/scenarios/${scenarioId}/debug`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' }, true)
  if (!(scenarioRun.success || scenarioRun.status === 'passed')) throw new Error(`REMOTE_SCENARIO_RUN_FAILED:${JSON.stringify(scenarioRun)}`)

  // Create a real remote environment through the desktop UI.  The stored
  // bearer token is intentionally masked on read, then resolved only while
  // the debugger sends an authenticated request to the public application.
  const environmentName = `公网认证环境-${stamp}`
  await page.evaluate(() => { location.hash = '#/cases' })
  await page.getByRole('heading', { name: '接口用例', exact: true }).waitFor({ timeout: 20000 })
  await page.getByTitle('环境管理').click()
  const environmentDrawer = page.getByRole('dialog', { name: /环境管理/ })
  await environmentDrawer.getByRole('button', { name: '新建环境', exact: true }).click()
  const environmentDialog = page.getByRole('dialog', { name: '新建环境' })
  await environmentDialog.locator('.el-form-item').filter({ hasText: '环境名称' }).locator('input').fill(environmentName)
  await environmentDialog.locator('.el-form-item').filter({ hasText: '基础URL' }).locator('input').fill(baseUrl)
  await environmentDialog.getByRole('button', { name: '添加变量', exact: true }).click()
  const tokenVariable = environmentDialog.locator('.var-item-editor').last()
  await tokenVariable.locator('input').nth(0).fill('auth_token')
  await tokenVariable.locator('input').nth(1).fill(token)
  await environmentDialog.getByRole('button', { name: '创建', exact: true }).click()
  await page.getByText('创建成功', { exact: true }).waitFor({ timeout: 20000 })
  environmentId = await page.evaluate(async name => {
    const response = await fetch(`${localStorage.getItem('testmaster_server_url')}/api/auto-test/environments`, {
      headers: { Authorization: `Bearer ${localStorage.getItem('token')}`, 'X-Project-Id': localStorage.getItem('desktop-active-project-id') || '' },
    })
    const entries = await response.json()
    return entries.find(item => item.name === name)?.id ?? null
  }, environmentName)
  if (!environmentId) throw new Error('PUBLIC_ENVIRONMENT_NOT_PERSISTED')
  const storedEnvironment = await request(`/api/auto-test/environments/${environmentId}`, { method: 'GET' }, true)
  if (storedEnvironment.variables?.auth_token !== '****') throw new Error('PUBLIC_ENVIRONMENT_SECRET_WAS_NOT_MASKED')
  await page.keyboard.press('Escape')
  await page.evaluate(() => { location.hash = '#/api-debugger' })
  await page.getByRole('heading', { name: '接口调试', exact: true }).waitFor({ timeout: 20000 })
  const environmentSelect = page.locator('.debug-toolbar .el-select').first()
  await environmentSelect.click()
  await page.locator('.el-select-dropdown:visible').getByText(environmentName, { exact: true }).click()
  const environmentUrl = page.locator('.request-line .url-input input')
  await environmentUrl.fill('{{base_url}}/api/v1/auth/me')
  await page.getByRole('tab', { name: '请求头', exact: true }).click()
  await page.getByRole('button', { name: '添加请求头', exact: true }).click()
  const authorizationHeader = page.locator('.el-tab-pane:visible .kv-row').last()
  await authorizationHeader.locator('input').nth(0).fill('Authorization')
  await authorizationHeader.locator('input').nth(1).fill('Bearer {{auth_token}}')
  const environmentDebugRequest = page.waitForResponse(response =>
    response.url().includes('/api/auto-test/send') && response.request().method() === 'POST', { timeout: 20000 },
  )
  await page.getByRole('button', { name: '发送', exact: true }).click()
  const environmentDebugResponse = await environmentDebugRequest
  const environmentDebugBody = await json(await environmentDebugResponse, 'public environment debugger request')
  if (!environmentDebugBody.success || environmentDebugBody.response_content?.username !== username) {
    throw new Error(`PUBLIC_ENVIRONMENT_VARIABLE_RESOLUTION_FAILED:${JSON.stringify(environmentDebugBody)}`)
  }

  await page.evaluate(id => { location.hash = `#/scenarios/${id}` }, scenarioId)
  await page.getByRole('button', { name: '运行场景', exact: true }).waitFor({ timeout: 20000 })

  // Exercise the desktop's local Playwright runtime against the real public
  // TestMaster web application.  This is intentionally not a data: fixture:
  // the browser must load the deployed login view and persist a usable UI
  // case/run on the public service.
  const uiCaseName = `公网桌面UI登录页-${stamp}`
  await page.evaluate(() => { location.hash = '#/ui-automation/cases' })
  await page.locator('.ui-case-list .page-header h2').waitFor({ timeout: 20000 })
  await page.getByRole('button', { name: '新建用例', exact: true }).click()
  const createUiCase = page.getByRole('dialog', { name: '新建 UI 用例' })
  await createUiCase.locator('.el-form-item').filter({ hasText: '用例名称' }).locator('input').fill(uiCaseName)
  await createUiCase.locator('.el-form-item').filter({ hasText: '基础URL' }).locator('input').fill(baseUrl)
  await createUiCase.getByRole('button', { name: '创建', exact: true }).click()
  await page.getByText('创建成功', { exact: true }).waitFor({ timeout: 20000 })
  await page.waitForURL(/#\/ui-automation\/cases\/\d+$/, { timeout: 20000 })
  uiCaseId = Number((await page.evaluate(() => location.hash)).split('/').pop())
  if (!Number.isInteger(uiCaseId)) throw new Error('PUBLIC_UI_CASE_ID_MISSING')
  await page.getByText('用户操作流程', { exact: true }).waitFor({ timeout: 20000 })

  await page.getByRole('button', { name: '手工添加', exact: true }).click()
  const actionDialog = page.getByRole('dialog', { name: '添加测试步骤' })
  await actionDialog.getByRole('button', { name: '打开网页', exact: true }).click()
  const inspector = page.locator('aside.inspector')
  await inspector.getByRole('heading', { name: '打开网页', exact: true }).waitFor({ timeout: 15000 })
  await inspector.locator('.el-form-item').filter({ hasText: '页面地址' }).locator('input').fill(`${baseUrl}/#/login`)
  await page.getByRole('button', { name: '搜索并添加', exact: true }).click()
  const assertionDialog = page.getByRole('dialog', { name: '添加测试步骤' })
  await assertionDialog.getByRole('button', { name: '检查页面标题', exact: true }).click()
  await inspector.getByRole('heading', { name: '检查页面标题', exact: true }).waitFor({ timeout: 15000 })
  // The deployed SPA replaces the static HTML title after it mounts.  Assert
  // the actual browser title observed by a user, rather than the server-side
  // fallback title in index.html.
  await inspector.locator('.el-form-item').filter({ hasText: '预期结果' }).locator('input').fill('TestMaster')
  await page.getByRole('button', { name: '保存', exact: true }).click()
  await page.getByText('用例已保存', { exact: true }).waitFor({ timeout: 20000 })
  await page.getByRole('button', { name: '运行完整流程', exact: true }).click()
  await page.getByText('运行结束：通过', { exact: false }).waitFor({ timeout: 60000 })
  const uiRun = await request(`/api/ui-automation/runs?case_id=${uiCaseId}`, { method: 'GET' }, true)
  const latestUiRun = uiRun.items?.[0]
  if (latestUiRun?.status !== 'passed' || latestUiRun.passed_steps !== 2) {
    throw new Error(`PUBLIC_UI_RUN_FAILED:${JSON.stringify(latestUiRun)}`)
  }

  // Model two requests that a real user made against the public TestMaster
  // service.  The values come from real responses, while the capture API is
  // responsible for redacting credential fields before any desktop view sees
  // them.  This avoids claiming a synthetic local endpoint as production
  // traffic coverage.
  const loginCaptureResponse = await json(await fetch(api('/api/v1/auth/login'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  }), 'login request for public traffic capture')
  const currentUser = await request('/api/v1/auth/me', { method: 'GET' })
  const capture = await request('/api/auto-test/import/captures', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      origin: 'desktop_browser',
      source_url: `${baseUrl}/#/login`,
      capture_config: { domain_allowlist: ['35.194.164.151'], path_exclude: [] },
    }),
  }, true)
  captureId = capture.id
  await request(`/api/auto-test/import/captures/${captureId}/exchanges`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ exchanges: [
      {
        captureEventId: `public-login-${stamp}`,
        resourceType: 'fetch', method: 'POST', url: api('/api/v1/auth/login'),
        requestHeaders: { 'content-type': 'application/json' },
        requestBody: { username, password }, status: 200,
        responseHeaders: { 'content-type': 'application/json' }, responseBody: loginCaptureResponse, timingMs: 120,
        pageUrl: `${baseUrl}/#/login`,
      },
      {
        captureEventId: `public-me-${stamp}`,
        resourceType: 'fetch', method: 'GET', url: api('/api/v1/auth/me'),
        requestHeaders: { authorization: `Bearer ${token}` }, status: 200,
        responseHeaders: { 'content-type': 'application/json' }, responseBody: currentUser, timingMs: 65,
        pageUrl: `${baseUrl}/#/dashboard`,
      },
    ] }),
  }, true)
  await request(`/api/auto-test/import/captures/${captureId}/complete`, { method: 'POST' }, true)

  await page.evaluate(id => { location.hash = `#/traffic-workbench?captureId=${encodeURIComponent(id)}` }, captureId)
  await page.locator('.traffic-workbench h2').waitFor({ timeout: 20000 })
  // Capture metadata deliberately strips the URL fragment before persistence.
  const captureSource = page.getByText(`${baseUrl}/`, { exact: true }).first()
  await captureSource.waitFor({ timeout: 20000 })
  await captureSource.click()
  const trafficRows = page.locator('.traffic-workbench .el-table tbody tr')
  await trafficRows.first().waitFor({ timeout: 20000 })
  if (await trafficRows.count() !== 2) throw new Error(`PUBLIC_TRAFFIC_ROW_COUNT:${await trafficRows.count()}`)
  await trafficRows.first().click()
  const captureDetails = await page.locator('.traffic-workbench .inspector').innerText()
  if (captureDetails.includes(password) || captureDetails.includes(token) || captureDetails.includes(loginCaptureResponse.access_token || '')) {
    throw new Error('PUBLIC_TRAFFIC_SECRET_LEAK')
  }

  await page.evaluate(id => { location.hash = `#/import-center?captureId=${encodeURIComponent(id)}` }, captureId)
  await page.getByRole('heading', { name: '导入中心', exact: true }).waitFor({ timeout: 20000 })
  const importRows = page.locator('.import-center .el-table tbody tr')
  await importRows.first().waitFor({ timeout: 20000 })
  if (await importRows.count() !== 2) throw new Error(`PUBLIC_CAPTURE_IMPORT_ROW_COUNT:${await importRows.count()}`)
  for (let index = 0; index < 2; index += 1) {
    const checkbox = importRows.nth(index).locator('.el-checkbox').first()
    const selected = await checkbox.locator('input').evaluate(input => input.checked)
    if (!selected) await checkbox.click()
  }
  await page.getByText('我已确认以下调用顺序和变量依赖', { exact: true }).click()
  const conversionResponse = page.waitForResponse(response =>
    response.url().includes(`/api/auto-test/import/captures/${captureId}/convert`) && response.request().method() === 'POST',
    { timeout: 20000 },
  )
  await page.getByRole('button', { name: '生成接口用例与场景', exact: true }).click()
  const conversion = await json(await conversionResponse, 'convert public captured traffic')
  capturedCaseIds = conversion.case_ids || []
  capturedScenarioId = conversion.scenario_id || null
  if (capturedCaseIds.length !== 2 || !capturedScenarioId) throw new Error(`PUBLIC_CAPTURE_CONVERSION_INVALID:${JSON.stringify(conversion)}`)
  await page.getByText('导入完成', { exact: true }).waitFor({ timeout: 20000 })
  // Credential redaction is intentional: without explicit runtime variables,
  // preview must fail and must never silently activate the generated suite.
  await page.getByRole('button', { name: '预览并验证场景', exact: true }).click()
  await page.getByText('预览未通过，场景保持停用', { exact: true }).waitFor({ timeout: 60000 })
  const capturedScenario = await request(`/api/auto-test/scenarios/${capturedScenarioId}`, { method: 'GET' }, true)
  if (capturedScenario.is_active !== false) throw new Error('PUBLIC_CAPTURE_FAILED_PREVIEW_ACTIVATED_SCENARIO')
  await page.screenshot({ path: path.join(artifactDir, 'desktop-production-acceptance.png'), fullPage: true })
  if (rendererErrors.length) throw new Error(`DESKTOP_RENDERER_ERRORS:${rendererErrors.join(' | ')}`)

  completedResult = {
    passed: true,
    checks: ['remote-registration', 'desktop-remote-login', 'desktop-api-debugger-public-health', 'desktop-project-create-activate', 'remote-case-run', 'remote-scenario-run', 'desktop-scenario-route', 'environment-secret-mask', 'environment-variable-real-request', 'desktop-ui-case-create', 'public-login-page-browser-run', 'public-ui-run-history', 'public-traffic-capture-redaction', 'desktop-traffic-workbench', 'desktop-capture-to-assets', 'redacted-capture-preview-gate'],
    projectId, caseId, scenarioId, uiCaseId, captureId, capturedCaseIds, capturedScenarioId,
  }
  workflowPassed = true
} finally {
  if (app && artifactDirReady) {
    // Preserve a small failure snapshot for production acceptance.  The
    // installation package can lag the source tree, so its actual rendered
    // route and error state are more useful than a bare Playwright timeout.
    const page = app.context?.().pages?.()[0]
    if (page) {
      await page.screenshot({ path: path.join(artifactDir, 'desktop-production-final-state.png'), fullPage: true }).catch(() => {})
      const state = await page.evaluate(() => ({ hash: location.hash, text: document.body?.innerText?.slice(0, 12000) || '' })).catch(() => null)
      if (state) await import('node:fs/promises').then(({ writeFile }) => writeFile(path.join(artifactDir, 'desktop-production-final-state.json'), JSON.stringify(state, null, 2))).catch(() => {})
    }
  }
  if (token && projectId) {
    const cleanupFailures = []
    // A real user must be able to clean a project that contains completed
    // captures, runs and import jobs. Exercise that desktop UI instead of
    // bypassing the product with a direct cleanup API call.
    try {
      const page = app.context?.().pages?.()[0]
      if (!page) throw new Error('DESKTOP_WINDOW_UNAVAILABLE_FOR_PROJECT_PURGE')
      await page.evaluate(() => { location.hash = '#/workspace-projects' })
      await page.getByRole('heading', { name: '工作区项目', exact: true }).waitFor({ timeout: 20000 })
      const projectRow = page.getByRole('row', { name: new RegExp(projectName) })
      await projectRow.getByRole('button', { name: '清理并删除', exact: true }).click()
      const purgeDialog = page.locator('.el-message-box')
      await purgeDialog.locator('input').fill(projectName)
      const purgeResponse = page.waitForResponse(response =>
        response.url().includes(`/api/workspace/projects/${projectId}/purge`) && response.request().method() === 'POST',
        { timeout: 20000 },
      )
      await purgeDialog.getByRole('button', { name: '永久删除', exact: true }).click()
      const purgeResult = await json(await purgeResponse, 'purge project from desktop')
      if (!purgeResult.ok) throw new Error(`DESKTOP_PROJECT_PURGE_INVALID:${JSON.stringify(purgeResult)}`)
      await projectRow.waitFor({ state: 'detached', timeout: 20000 })
      const verifyDeleted = await fetch(api(`/api/workspace/projects/${projectId}`), { headers: headers(false) })
      if (verifyDeleted.status !== 404) throw new Error(`DESKTOP_PROJECT_PURGE_NOT_PERSISTED:${verifyDeleted.status}`)
    } catch (error) {
      cleanupFailures.push(`desktop-project-purge:${error?.message || error}`)
    }
    if (workflowPassed && cleanupFailures.length) {
      cleanupFailure = new Error(`PUBLIC_ACCEPTANCE_CLEANUP_FAILED:${cleanupFailures.join(' | ')}`)
    }
  }
  if (app) await app.close().catch(() => {})
  if (cleanupFailure) throw cleanupFailure
}

if (completedResult) console.log(JSON.stringify(completedResult))
