import { _electron as electron } from 'playwright'
import { spawn } from 'node:child_process'
import { access, mkdir, readFile, rm, writeFile } from 'node:fs/promises'
import path from 'node:path'

const root = path.resolve(import.meta.dirname, '..')
const profile = process.env.TESTMASTER_ACCEPTANCE_DATA_DIR || 'D:\\TestMasterAcceptance\\runs\\business-acceptance'
const resultPath = path.join(root, 'test-artifacts', 'business-acceptance.json')
await rm(profile, { recursive: true, force: true })
await mkdir(path.dirname(resultPath), { recursive: true })

const packagedExe = process.env.TESTMASTER_PACKAGED_EXE
const localBackendPort = Number(process.env.TESTMASTER_DESKTOP_BACKEND_PORT || '5001')
const localBackendUrl = `http://127.0.0.1:${localBackendPort}`
const launchOptions = packagedExe
  ? { executablePath: packagedExe, args: ['--remote-debugging-port=9333', `--user-data-dir=${profile}`] }
  : { args: [root, '--remote-debugging-port=9333', `--user-data-dir=${profile}`] }
const app = await electron.launch({
  ...launchOptions,
  // Only the isolated acceptance profile permits loopback targets. This lets the
  // script use a deterministic local HTTP server while release builds retain
  // their default SSRF protections.
  env: { ...process.env, TESTMASTER_DESKTOP_DATA_DIR: profile, DISABLE_SSRF_GUARD: 'true' },
})
const page = await app.firstWindow()
const pageErrors = []
page.on('pageerror', error => pageErrors.push(error.message))

try {
  // firstWindow() resolves as soon as Electron creates the BrowserWindow, not
  // when Vue has mounted the login form. Wait for the rendered page boundary
  // before locating form controls so a slow cold start cannot make acceptance
  // results flaky.
  await page.getByTestId('desktop-login-page').waitFor({ state: 'visible', timeout: 45000 })
  // An isolated packaged run must connect to its own bundled backend rather
  // than silently reusing a normal desktop instance on the default port.
  const serverInput = page.getByLabel('服务地址')
  await serverInput.fill(localBackendUrl)
  await serverInput.press('Tab')
  await page.getByLabel('用户名').fill('admin')
  const loginButton = page.getByRole('button', { name: '登录', exact: true })
  await loginButton.waitFor({ state: 'visible', timeout: 45000 })
  await page.getByText('服务连接正常', { exact: true }).waitFor({ timeout: 90000 })
  const passwordPath = path.join(profile, 'service', '.desktop-admin-password')
  let password
  try {
    password = (await readFile(passwordPath, 'utf8')).trim()
  } catch (error) {
    throw new Error(`Desktop local administrator password was not created at ${passwordPath}: ${error?.message || error}`)
  }
  if (password.length < 16) throw new Error(`Desktop local administrator password is invalid at ${passwordPath}`)
  await page.getByLabel('密码').fill(password)
  await loginButton.click()
  await page.locator('.desktop-sidebar').waitFor({ timeout: 30000 })

  const manifestPath = path.join(root, 'acceptance', 'suites.json')
  const manifest = JSON.parse(await readFile(manifestPath, 'utf8'))
  const allScripts = [...new Set(Object.values(manifest.groups || {}).flat())]
  if (!allScripts.length) throw new Error(`No acceptance scripts defined in ${manifestPath}`)
  const selectedScripts = new Set((process.env.TESTMASTER_ACCEPTANCE_ONLY || '').split(',').map(value => value.trim()).filter(Boolean))
  const scripts = selectedScripts.size ? allScripts.filter(script => selectedScripts.has(script)) : allScripts
  if (!scripts.length) throw new Error('No acceptance script matched TESTMASTER_ACCEPTANCE_ONLY')
  const unknownScripts = [...selectedScripts].filter(script => !allScripts.includes(script))
  if (unknownScripts.length) throw new Error(`Acceptance scripts are not registered: ${unknownScripts.join(', ')}`)
  for (const script of scripts) {
    try {
      await access(path.join(import.meta.dirname, script))
    } catch {
      throw new Error(`Acceptance script declared but missing: ${script}`)
    }
  }
  const completed = []
  const failures = []
  for (const script of scripts) {
    const outcome = await new Promise(resolve => {
      const child = spawn(process.execPath, [path.join(import.meta.dirname, script)], { cwd: root, stdio: 'inherit' })
      child.once('exit', code => resolve({ code }))
      child.once('error', error => resolve({ error: error.message }))
    })
    completed.push({ script, ...outcome })
    if (outcome.code !== 0 || outcome.error) failures.push({ script, ...outcome })
    await writeFile(resultPath, JSON.stringify({ passed: false, running: true, completed, failures, pageErrors }, null, 2))
    // Each workflow shares one Electron renderer. Reset transient dialogs,
    // drawers and route state so one failed flow cannot mask later findings.
    await page.reload({ waitUntil: 'domcontentloaded' })
    await page.locator('.desktop-sidebar').waitFor({ timeout: 15000 })
    // Element Plus mounts messages and notifications outside the routed view.
    // They can outlive a page reload while their leave transition is pending,
    // so remove only those completed transient containers before the next
    // independent workflow begins.  Functional errors remain asserted inside
    // the workflow that triggered them.
    await page.locator('.el-message, .el-notification').evaluateAll(nodes => nodes.forEach(node => node.remove()))
  }
  if (pageErrors.length) throw new Error(`Renderer errors: ${pageErrors.join(' | ')}`)
  const result = { passed: failures.length === 0, scripts, completed, failures, rendererErrors: 0 }
  await writeFile(resultPath, JSON.stringify(result, null, 2))
  console.log(JSON.stringify(result))
  if (failures.length) process.exitCode = 1
} catch (error) {
  await writeFile(resultPath, JSON.stringify({ passed: false, error: error?.stack || String(error), pageErrors }, null, 2))
  throw error
} finally {
  await app.close()
}
