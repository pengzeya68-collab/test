import { _electron as electron } from 'playwright'
import { spawn } from 'node:child_process'
import { mkdir, rm, writeFile } from 'node:fs/promises'
import path from 'node:path'

const root = path.resolve(import.meta.dirname, '..')
const profile = path.join(root, '.business-acceptance-profile')
const resultPath = path.join(root, 'test-artifacts', 'business-acceptance.json')
await rm(profile, { recursive: true, force: true })
await mkdir(path.dirname(resultPath), { recursive: true })

const app = await electron.launch({ args: [root, '--remote-debugging-port=9333', `--user-data-dir=${profile}`] })
const page = await app.firstWindow()
const pageErrors = []
page.on('pageerror', error => pageErrors.push(error.message))

try {
  await page.getByLabel('用户名').fill('admin')
  await page.getByLabel('密码').fill('admin123')
  const loginButton = page.getByRole('button', { name: '登录', exact: true })
  await loginButton.waitFor({ state: 'visible', timeout: 45000 })
  await page.getByText('服务连接正常', { exact: true }).waitFor({ timeout: 45000 })
  await loginButton.click()
  await page.locator('.desktop-sidebar').waitFor({ timeout: 30000 })

  const scripts = [
    'test-suite-e2e.mjs',
    'test-failure-report-e2e.mjs',
    'test-run-history-artifacts.mjs',
    'test-auth-state-e2e.mjs',
  ]
  const completed = []
  for (const script of scripts) {
    await new Promise((resolve, reject) => {
      const child = spawn(process.execPath, [path.join(import.meta.dirname, script)], { cwd: root, stdio: 'inherit' })
      child.once('exit', code => code === 0 ? resolve() : reject(new Error(`${script} failed with ${code}`)))
      child.once('error', reject)
    })
    completed.push(script)
    await writeFile(resultPath, JSON.stringify({ passed: false, running: true, completed, pageErrors }, null, 2))
  }
  if (pageErrors.length) throw new Error(`Renderer errors: ${pageErrors.join(' | ')}`)
  const result = { passed: true, scripts, rendererErrors: 0 }
  await writeFile(resultPath, JSON.stringify(result, null, 2))
  console.log(JSON.stringify(result))
} catch (error) {
  await writeFile(resultPath, JSON.stringify({ passed: false, error: error?.stack || String(error), pageErrors }, null, 2))
  throw error
} finally {
  await app.close()
}
