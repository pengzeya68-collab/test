import { chromium } from 'playwright'

const browser = await chromium.connectOverCDP('http://127.0.0.1:9333')
const page = browser.contexts()[0].pages()[0]
const pageErrors = []
page.on('pageerror', error => pageErrors.push(error.message))

const openRoute = async (route, heading) => {
  await page.evaluate(target => { location.hash = `#${target}` }, route)
  await page.locator('h1, h2').filter({ hasText: new RegExp(`^${heading}$`) }).first().waitFor({ timeout: 20000 })
  await page.waitForTimeout(300)
}

const expectFeedback = async text => {
  await page.getByText(text, { exact: false }).last().waitFor({ state: 'visible', timeout: 15000 })
}

try {
  // AI generation: empty input must be blocked, help must close, and a rejected
  // submission must leave the user on the configuration step instead of stuck loading.
  await openRoute('/ai-generate-cases', 'AI 智能生成测试用例')
  const nextButton = page.getByRole('button', { name: /下一步：配置选项/ })
  if (!(await nextButton.isDisabled())) throw new Error('AI_EMPTY_INPUT_WAS_NOT_BLOCKED')
  await page.getByRole('button', { name: /使用说明/ }).click()
  await page.locator('.el-drawer:visible, .el-dialog:visible').first().waitFor({ timeout: 10000 })
  await page.keyboard.press('Escape')
  await page.locator('.el-drawer:visible, .el-dialog:visible').waitFor({ state: 'hidden', timeout: 10000 })
  await page.locator('input[placeholder*="Swagger"]').fill('not-a-url')
  await nextButton.click()
  await expectFeedback('请输入有效的 HTTP 或 HTTPS Swagger 文档地址')
  await page.route('**/api/auto-test/ai-generate/from-swagger-url', route => route.fulfill({ status: 503, contentType: 'application/json', body: JSON.stringify({ detail: '验收模拟的生成服务不可用' }) }))
  await page.locator('input[placeholder*="Swagger"]').fill('https://example.invalid/openapi.json')
  await nextButton.click()
  await page.getByRole('button', { name: '开始生成', exact: true }).click()
  await expectFeedback('提交失败')
  await page.getByRole('button', { name: '开始生成', exact: true }).waitFor({ state: 'visible', timeout: 10000 })
  await page.unroute('**/api/auto-test/ai-generate/from-swagger-url')

  let cancelRequests = 0
  await page.route('**/api/auto-test/ai-generate/from-swagger-url', route => route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ task_id: 'exploratory-cancel-task', status: 'PENDING' }) }))
  await page.route('**/api/auto-test/ai-generate/tasks/**', route => {
    if (route.request().method() === 'POST') {
      cancelRequests += 1
      return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ status: 'cancel_requested' }) })
    }
    return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ status: cancelRequests ? 'cancelled' : 'running', progress: 10, cases: [], scenarios: [] }) })
  })
  await page.getByRole('button', { name: '开始生成', exact: true }).click()
  await page.getByRole('button', { name: /中止生成/ }).waitFor({ timeout: 10000 })
  await page.getByRole('button', { name: /中止生成/ }).click()
  await page.getByRole('button', { name: '继续生成', exact: true }).click()
  if (cancelRequests !== 0) throw new Error(`AI_CANCELLED_AFTER_DISMISS:${cancelRequests}`)
  await page.getByRole('button', { name: /中止生成/ }).click()
  await page.getByRole('button', { name: '确定中止', exact: true }).click()
  await expectFeedback('任务已标记为中止')
  await page.getByText('生成已中止', { exact: false }).waitFor({ timeout: 6000 })
  if (cancelRequests !== 1) throw new Error(`AI_CANCEL_REQUEST_COUNT:${cancelRequests}`)
  await page.unroute('**/api/auto-test/ai-generate/from-swagger-url')
  await page.unroute('**/api/auto-test/ai-generate/tasks/**')

  // Import center: a basic invalid action has to explain what the user needs to do.
  await openRoute('/import-center', '导入中心')
  await page.getByText('文件 / cURL', { exact: true }).click()
  await page.locator('.control-row .el-select').first().click()
  await page.locator('.el-select-dropdown:visible').getByText('cURL 命令', { exact: true }).click()
  await page.getByRole('button', { name: '解析预览', exact: true }).click()
  await expectFeedback('请输入 cURL 命令')

  // A coverage request failure used to look exactly like an empty workspace.
  // It now needs a persistent, actionable error state and a retry control.
  await page.route('**/api/auto-test/coverage/**', route => route.fulfill({ status: 503, contentType: 'application/json', body: JSON.stringify({ detail: '验收模拟的覆盖率服务不可用' }) }))
  await openRoute('/test-coverage', '测试覆盖率看板')
  await expectFeedback('测试覆盖率')
  await page.getByRole('button', { name: '重新加载', exact: true }).click()
  await expectFeedback('测试覆盖率')
  await page.unroute('**/api/auto-test/coverage/**')

  // The tools page gets the same treatment: no silent blank page on a failed request.
  await page.route('**/api/v1/tools/categories', route => route.fulfill({ status: 503, contentType: 'application/json', body: JSON.stringify({ detail: '验收模拟的工具目录不可用' }) }))
  await openRoute('/tools', '测试工具导航')
  await expectFeedback('测试工具加载失败')
  await page.getByRole('button', { name: '重新加载', exact: true }).click()
  await expectFeedback('测试工具加载失败')
  await page.unroute('**/api/v1/tools/categories')

  // A core orchestration page also must distinguish a failed load from a truly
  // empty workspace, otherwise users can accidentally create duplicate flows.
  await page.route('**/api/auto-test/scenarios', route => route.fulfill({ status: 503, contentType: 'application/json', body: JSON.stringify({ detail: '验收模拟的场景服务不可用' }) }))
  await openRoute('/scenarios', '业务场景')
  await expectFeedback('场景列表加载失败')
  await page.getByRole('button', { name: '重新加载', exact: true }).click()
  await expectFeedback('场景列表加载失败')
  await page.unroute('**/api/auto-test/scenarios')

  // Creation is a write operation: blank input stays in the dialog, and a
  // slow failing request must not be sent twice by an impatient double click.
  await openRoute('/scenarios', '业务场景')
  await page.getByRole('button', { name: '新建场景', exact: true }).click()
  const scenarioDialog = page.getByRole('dialog', { name: '新建场景' })
  await scenarioDialog.getByRole('button', { name: '确定', exact: true }).click()
  await expectFeedback('请输入场景名称')
  await scenarioDialog.getByPlaceholder('请输入场景名称').fill('   ')
  await scenarioDialog.getByRole('button', { name: '确定', exact: true }).click()
  await expectFeedback('请输入场景名称')
  await scenarioDialog.getByPlaceholder('请输入场景名称').fill('重复提交验收场景')
  let createRequests = 0
  await page.route('**/api/auto-test/scenarios', route => {
    if (route.request().method() !== 'POST') return route.continue()
    createRequests += 1
    return new Promise(resolve => setTimeout(() => resolve(route.fulfill({ status: 503, contentType: 'application/json', body: JSON.stringify({ detail: '验收模拟写入失败' }) })), 350))
  })
  await scenarioDialog.getByRole('button', { name: '确定', exact: true }).dblclick()
  await expectFeedback('操作失败')
  if (createRequests !== 1) throw new Error(`SCENARIO_DUPLICATE_CREATE:${createRequests}`)
  await page.keyboard.press('Escape')
  await scenarioDialog.waitFor({ state: 'hidden', timeout: 10000 })
  await page.unroute('**/api/auto-test/scenarios')

  // A bookmarked scenario may have been deleted by another user. The editor
  // must stop dependent loaders, explain the problem and land on a usable page.
  const staleConsoleErrors = []
  const staleConsoleListener = message => {
    if (message.type() === 'error' && !/Failed to load resource:.*404/i.test(message.text())) staleConsoleErrors.push(message.text())
  }
  page.on('console', staleConsoleListener)
  await page.evaluate(() => { location.hash = '#/scenarios/987654' })
  await page.waitForURL(/#\/scenarios$/, { timeout: 15000 })
  await expectFeedback('场景不存在或已被删除')
  await page.waitForTimeout(600)
  page.off('console', staleConsoleListener)
  if (staleConsoleErrors.length) throw new Error(`STALE_SCENARIO_RENDERER_ERRORS:${staleConsoleErrors.join(' | ')}`)

  if (pageErrors.length) throw new Error(`RENDERER_ERRORS:${pageErrors.join(' | ')}`)
  console.log(JSON.stringify({ passed: true, checks: ['ai-empty-help-failure', 'ai-cancel-confirmation-and-deduplication', 'import-empty-curl', 'coverage-failure-retry', 'tools-failure-retry', 'scenario-list-failure-retry', 'scenario-create-validation-and-dedupe', 'stale-scenario-redirect'] }))
} finally {
  await browser.close()
}
