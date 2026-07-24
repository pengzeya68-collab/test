import { chromium } from 'playwright'

const browser = await chromium.connectOverCDP('http://127.0.0.1:9333')
const page = browser.contexts()[0].pages()[0]
const findings = []
const expectedErrorPatterns = [/Failed to load resource:.*(404|net::ERR)/i]
const remember = (kind, detail) => findings.push({ kind, detail, at: new Date().toISOString() })
page.on('pageerror', error => remember('pageerror', error.message))
page.on('console', message => {
  if (message.type() !== 'error') return
  const text = message.text()
  if (!expectedErrorPatterns.some(pattern => pattern.test(text))) remember('console.error', text)
})
page.on('response', response => {
  if (response.status() >= 500) remember('http-5xx', `${response.status()} ${response.url()}`)
  if (response.url().includes('/auto-test/import/captures/') && response.status() >= 400) {
    void response.text().then(body => remember('capture-candidates-request-failed', `${response.status()} ${response.url()} ${body.slice(0, 500)}`))
  }
})
page.on('requestfailed', request => {
  if (request.url().includes('/auto-test/import/captures/')) {
    remember('capture-candidates-request-aborted', `${request.method()} ${request.url()} ${request.failure()?.errorText || ''}`)
  }
})

const routes = [
  ['/dashboard', '工作概览'],
  ['/api-debugger', '接口调试'],
  ['/cases', '接口用例'],
  ['/scenarios', '业务场景'],
  ['/suites', '接口回归套件'],
  ['/data-factory', '测试数据工厂'],
  ['/import-center', '流量导入中心'],
  ['/mock-service', 'Mock 服务'],
  ['/backup-manager', '资产备份'],
  ['/ui-automation/cases', 'UI 自动化用例'],
  ['/ui-automation/suites', 'UI 回归套件'],
  ['/jmeter-assistant', 'JMeter 性能助手'],
  ['/ai-generate-cases', 'AI 智能生成测试用例'],
  ['/test-coverage', '测试覆盖率看板'],
  ['/api-docs', 'API 文档'],
  ['/api-doc-preview', 'API 文档预览'],
  ['/tools', '测试工具导航'],
]

async function verifyNoTransientErrors(label) {
  await page.waitForTimeout(700)
  const messages = await page.locator('.el-message--error, .el-notification--error, [role="alert"].is-error').allTextContents()
  for (const message of messages.map(value => value.trim()).filter(Boolean)) remember('unasserted-error-feedback', `${label}: ${message}`)
  const masks = await page.locator('.el-loading-mask:visible').count()
  if (masks) remember('stuck-loading-mask', `${label}: ${masks}`)
}

try {
  for (const [route, heading] of routes) {
    await page.evaluate(target => { location.hash = `#${target}` }, route)
    await page.locator('h1, h2').filter({ hasText: new RegExp(`^${heading}$`) }).first().waitFor({ timeout: 30000 })
    await page.waitForTimeout(1200)
    await verifyNoTransientErrors(route)
    const dialogs = await page.locator('.el-overlay-dialog:visible, .el-drawer__container:visible').count()
    if (dialogs) remember('unexpected-overlay', `${route}: ${dialogs}`)
  }

  // The dashboard is a primary entry point; validate actual navigation, then return.
  await page.evaluate(() => { location.hash = '#/dashboard' })
  await page.getByRole('heading', { name: '今天的测试工作', exact: true }).waitFor({ timeout: 15000 })
  await page.locator('.workspace-entry').filter({ hasText: '接口调试' }).click()
  await page.getByRole('heading', { name: '接口调试', exact: true }).waitFor({ timeout: 15000 })
  await page.evaluate(() => { location.hash = '#/dashboard' })
  await page.getByRole('button', { name: /录制 UI 用例/ }).click()
  await page.locator('h1, h2').filter({ hasText: /^UI 自动化用例$/ }).first().waitFor({ timeout: 15000 })
  await verifyNoTransientErrors('dashboard-navigation')

  // Old shared-view links remain in several desktop pages. The desktop router
  // must preserve their intent instead of silently falling back to the debugger.
  await page.evaluate(() => { location.hash = '#/auto-test' })
  await page.locator('h1, h2').filter({ hasText: /^今天的测试工作$/ }).waitFor({ timeout: 15000 })
  await page.evaluate(() => { location.hash = '#/auto-test?tab=interfaces' })
  await page.locator('h1, h2').filter({ hasText: /^接口用例$/ }).first().waitFor({ timeout: 15000 })
  if (findings.length) throw new Error(`EXPLORATORY_ROUTE_SWEEP_FINDINGS:${JSON.stringify(findings)}`)
  console.log(JSON.stringify({ passed: true, checks: routes.length + 4 }))
} finally {
  await browser.close()
}
