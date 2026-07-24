import { chromium } from 'playwright'

const browser = await chromium.connectOverCDP('http://127.0.0.1:9333')
const page = browser.contexts()[0].pages()[0]
const routes = [
  ['/dashboard', '今天的测试工作'],
  ['/api-debugger', '接口调试'],
  ['/cases', '接口用例'],
  ['/scenarios', '业务场景'],
  ['/suites', '接口回归套件'],
  ['/data-factory', '测试数据工厂'],
  ['/import-center', '导入中心'],
  ['/mock-service', 'Mock 服务'],
  ['/ui-automation/cases', 'UI 自动化用例'],
  ['/jmeter-assistant', 'JMeter 性能助手'],
]
const findings = []

try {
  await page.setViewportSize({ width: 1024, height: 700 })
  for (const [route, title] of routes) {
    await page.evaluate(target => { location.hash = `#${target}` }, route)
    await page.getByText(title, { exact: true }).first().waitFor({ timeout: 20000 })
    // A route is not considered stable merely because its title has rendered.
    // Wait for its real initial request to settle, then fail only if the mask
    // remains visible rather than racing a legitimate loading state.
    await page.locator('.el-loading-mask:visible').waitFor({ state: 'hidden', timeout: 15000 }).catch(() => {})
    await page.waitForTimeout(350)
    const layout = await page.evaluate(() => ({
      viewport: window.innerWidth,
      scrollWidth: document.documentElement.scrollWidth,
      visibleMasks: document.querySelectorAll('.el-loading-mask:not([style*="display: none"])').length,
      sidebar: document.querySelector('.desktop-sidebar')?.getBoundingClientRect().width || 0,
      main: document.querySelector('.desktop-main')?.getBoundingClientRect().width || 0,
    }))
    if (layout.scrollWidth > layout.viewport + 2) findings.push({ route, kind: 'page-horizontal-overflow', ...layout })
    if (layout.visibleMasks) findings.push({ route, kind: 'stuck-loading-mask', ...layout })
  }
  if (findings.length) throw new Error(`DESKTOP_LAYOUT_FINDINGS:${JSON.stringify(findings)}`)
  console.log(JSON.stringify({ passed: true, checks: routes.length, viewport: '1024x700' }))
} finally {
  await browser.close()
}
