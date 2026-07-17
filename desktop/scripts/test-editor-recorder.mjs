import { chromium } from 'playwright'
const browser = await chromium.connectOverCDP('http://127.0.0.1:9333')
try {
  const page = browser.contexts()[0].pages()[0]
  await page.evaluate(() => { location.hash = '#/ui-automation/cases/2' })
  await page.waitForTimeout(1200)
  const html = `<meta charset="utf-8"><input data-testid="search" placeholder="搜索商品"><button data-testid="submit">提交订单</button><script>setTimeout(()=>{const el=document.querySelector('[data-testid=search]');el.value='测试商品';el.dispatchEvent(new Event('input',{bubbles:true}))},650);setTimeout(()=>document.querySelector('[data-testid=submit]').click(),1300)<\/script>`
  const url = `data:text/html,${encodeURIComponent(html)}`
  await page.getByPlaceholder('输入被测系统地址，例如：https://test.example.com').fill(url)
  await page.getByRole('button', { name: '开始录制' }).first().click()
  await page.getByText('正在录制').waitFor({ timeout: 15000 })
  await page.waitForTimeout(2300)
  await page.getByRole('button', { name: '停止录制' }).click()
  await page.getByText('输入搜索商品', { exact: false }).waitFor({ timeout: 5000 })
  await page.getByText('点击“提交订单”', { exact: false }).waitFor({ timeout: 5000 })
  const text = await page.locator('body').innerText()
  if (!text.includes('用户操作流程') || !text.includes('搜索并添加') || !text.includes('浏览器控制台') || !text.includes('网络失败')) throw new Error('Studio layout is incomplete')
  await page.screenshot({ path: 'editor-recorder-acceptance.png', fullPage: true })
  console.log(JSON.stringify({ passed: true, hasRecorder: text.includes('开始录制'), hasFlowCanvas: text.includes('用户操作流程'), hasInspector: text.includes('目标元素'), hasDebug: text.includes('浏览器控制台') }))
  await page.reload()
} finally { await browser.close() }
