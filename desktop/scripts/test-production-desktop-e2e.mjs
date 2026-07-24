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
let groupId = null
let caseId = null
let scenarioId = null
let app

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
  const projectName = `公网桌面验收项目-${stamp}`
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

  await page.evaluate(id => { location.hash = `#/scenarios/${id}` }, scenarioId)
  await page.getByRole('button', { name: '运行场景', exact: true }).waitFor({ timeout: 20000 })
  await page.screenshot({ path: path.join(artifactDir, 'desktop-production-acceptance.png'), fullPage: true })
  if (rendererErrors.length) throw new Error(`DESKTOP_RENDERER_ERRORS:${rendererErrors.join(' | ')}`)

  console.log(JSON.stringify({
    passed: true,
    checks: ['remote-registration', 'desktop-remote-login', 'desktop-api-debugger-public-health', 'desktop-project-create-activate', 'remote-case-run', 'remote-scenario-run', 'desktop-scenario-route'],
    projectId, caseId, scenarioId,
  }))
} finally {
  if (token && projectId) {
    if (scenarioId) await fetch(api(`/api/auto-test/scenarios/${scenarioId}`), { method: 'DELETE', headers: headers(true) }).catch(() => {})
    if (caseId) await fetch(api(`/api/auto-test/cases/${caseId}`), { method: 'DELETE', headers: headers(true) }).catch(() => {})
    if (groupId) await fetch(api(`/api/auto-test/groups/${groupId}`), { method: 'DELETE', headers: headers(true) }).catch(() => {})
    await fetch(api(`/api/workspace/projects/${projectId}`), { method: 'DELETE', headers: headers() }).catch(() => {})
  }
  if (app) await app.close().catch(() => {})
}
