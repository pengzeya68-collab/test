import { _electron as electron } from 'playwright'
import { mkdir, rm } from 'node:fs/promises'
import path from 'node:path'

const root = path.resolve(import.meta.dirname, '..')
const profile = path.join(root, '.smoke-profile')
const artifacts = path.join(root, 'test-artifacts', 'desktop-shell')
const smokeUser = process.env.TESTMASTER_SMOKE_USER
const smokePassword = process.env.TESTMASTER_SMOKE_PASSWORD
if (!smokeUser || !smokePassword) throw new Error('Set TESTMASTER_SMOKE_USER and TESTMASTER_SMOKE_PASSWORD before running the desktop smoke test')
await rm(profile, { recursive: true, force: true })
await mkdir(artifacts, { recursive: true })

const packagedExe = process.env.TESTMASTER_PACKAGED_EXE
const app = await electron.launch(packagedExe
  ? { executablePath: packagedExe, args: [`--user-data-dir=${profile}`] }
  : { args: [root, `--user-data-dir=${profile}`] })
const page = await app.firstWindow()
const errors = []
page.on('pageerror', error => errors.push(error.message))
let healthReady = false
for (let attempt = 0; attempt < 90; attempt += 1) {
  try {
    const health = await fetch('http://127.0.0.1:5001/api/ui-automation/health')
    if (health.ok) { healthReady = true; break }
  } catch {}
  await new Promise(resolve => setTimeout(resolve, 500))
}
if (!healthReady) throw new Error('Desktop managed backend did not become healthy')
const loginResponse = await fetch('http://127.0.0.1:5001/api/v1/auth/login', {
  method: 'POST', headers: { 'content-type': 'application/json' },
  body: JSON.stringify({ username: smokeUser, password: smokePassword }),
})
if (!loginResponse.ok) throw new Error(`Smoke login failed: ${loginResponse.status}`)
const login = await loginResponse.json()
await page.evaluate(({ token, user }) => {
  localStorage.setItem('token', token)
  localStorage.setItem('user', JSON.stringify(user))
  localStorage.setItem('testmaster-theme', 'apple-light')
}, { token: login.access_token, user: login.user })
await page.reload({ waitUntil: 'domcontentloaded' })

const routes = ['/auto-test', '/cases', '/scenarios', '/suites', '/data-factory', '/mock-service', '/ui-automation/cases', '/ui-automation/suites', '/jmeter-assistant', '/test-coverage', '/api-docs', '/backup-manager', '/tools']
const results = []
for (const route of routes) {
  await page.evaluate(hash => { location.hash = hash }, route)
  await page.waitForTimeout(900)
  const state = await page.evaluate(() => ({
    title: document.querySelector('.module-heading h1')?.textContent?.trim(),
    textLength: document.querySelector('.desktop-workspace')?.innerText?.trim().length || 0,
    shellVisible: Boolean(document.querySelector('.desktop-sidebar') && document.querySelector('.desktop-header')),
  }))
  results.push({ route, currentRoute: await page.evaluate(() => location.hash.slice(1)), ...state })
}
await page.evaluate(() => { location.hash = '/ui-automation/cases' })
await page.waitForTimeout(1000)
await page.screenshot({ path: path.join(artifacts, 'ui-automation-cases.png'), fullPage: true })
await page.evaluate(() => { location.hash = '/cases' })
await page.waitForTimeout(1000)
await page.screenshot({ path: path.join(artifacts, 'interface-cases.png'), fullPage: true })

console.log(JSON.stringify({ errors, results }, null, 2))
await app.close()
if (errors.length || results.some(item => !item.shellVisible || item.textLength < 10 || item.currentRoute !== item.route)) process.exitCode = 1
