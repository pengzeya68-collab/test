import { chromium } from 'playwright'
const browser = await chromium.connectOverCDP('http://127.0.0.1:9333')
try {
  const page = browser.contexts()[0].pages()[0]
  const html = `<meta charset="utf-8"><label for="username">用户名</label><input id="username" data-testid="username"><label for="password">密码</label><input id="password" data-testid="password" type="password"><button data-testid="login">登录</button><script>setTimeout(() => { const el = document.querySelector('[data-testid=username]'); el.value = 'tester'; el.dispatchEvent(new Event('input', { bubbles: true })) }, 500);setTimeout(() => { const el = document.querySelector('[data-testid=password]'); el.value = 'secret123'; el.dispatchEvent(new Event('input', { bubbles: true })) }, 1000);setTimeout(() => document.querySelector('[data-testid=login]').click(), 1600)<\/script>`
  const url = `data:text/html,${encodeURIComponent(html)}`
  const result = await page.evaluate(async targetUrl => {
    window.__recorderAcceptanceEvents = []
    const started = await window.testmaster.recorder.start({ url: targetUrl }, event => window.__recorderAcceptanceEvents.push(event))
    await new Promise(resolve => setTimeout(resolve, 2800))
    const events = window.__recorderAcceptanceEvents
    const locatorCheck = await window.testmaster.recorder.validateLocator({ strategy: 'test_id', value: 'login', options: {}, fallbacks: [], framePath: [] })
    await window.testmaster.recorder.stop()
    return { started, events, locatorCheck }
  }, url)
  const actions = result.events.filter(event => event.type === 'action').map(event => event.step)
  if (!actions.some(step => step.type === 'goto')) throw new Error('Recorder did not capture navigation')
  if (!actions.some(step => step.type === 'fill' && step.input?.value === 'tester')) throw new Error('Recorder did not capture text input')
  if (!actions.some(step => step.type === 'fill' && step.input?.value === '{{PASSWORD}}' && step.input?.secret === true)) throw new Error('Recorder did not mask password input')
  if (!actions.some(step => step.type === 'click' && step.locator?.strategy === 'test_id' && step.locator?.value === 'login')) throw new Error('Recorder did not capture stable click locator')
  if (result.locatorCheck?.count !== 1) throw new Error('Locator validation did not find exactly one element')
    const assertionHtml = `<meta charset="utf-8"><button data-testid="success">订单已创建</button><script>setTimeout(() => document.querySelector('[data-testid=success]').click(), 900)<\/script>`
  const assertionResult = await page.evaluate(async targetUrl => {
    window.__assertionEvents = []
    await window.testmaster.recorder.start({ url: targetUrl }, event => window.__assertionEvents.push(event))
    await window.testmaster.recorder.setMode('assert-text')
    await new Promise(resolve => setTimeout(resolve, 1600))
    const events = window.__assertionEvents
    await window.testmaster.recorder.stop()
    return events
  }, `data:text/html,${encodeURIComponent(assertionHtml)}`)
  const assertion = assertionResult.find(event => event.type === 'action' && event.step?.type === 'assert_text_contains')
  if (!assertion || assertion.step.input?.expected !== '订单已创建') { console.error(JSON.stringify(assertionResult, null, 2)); throw new Error('Assertion mode did not capture text assertion') }
  const popupHtml = `<meta charset="utf-8"><button data-testid="open" onclick="const popup=window.open('about:blank');popup.document.title='详情'">打开详情</button><script>setTimeout(()=>document.querySelector('[data-testid=open]').click(),700)<\/script>`
  const popupEvents = await page.evaluate(async targetUrl => {
    window.__popupEvents = []
    await window.testmaster.recorder.start({ url: targetUrl }, event => window.__popupEvents.push(event))
    await new Promise(resolve => setTimeout(resolve, 1600))
    const events = window.__popupEvents
    await window.testmaster.recorder.stop()
    return events
  }, `data:text/html,${encodeURIComponent(popupHtml)}`)
  const popupTypes = popupEvents.filter(event => event.type === 'action').map(event => event.step.type)
  if (!popupTypes.includes('click') || !popupTypes.includes('switch_page') || popupTypes.indexOf('click') > popupTypes.indexOf('switch_page')) throw new Error('Popup recording order is invalid')

  const frameInner = `<meta charset="utf-8"><button data-testid="pay">支付</button><script>setTimeout(()=>document.querySelector('[data-testid=pay]').click(),700)<\/script>`
  const frameOuter = `<iframe id="checkout" srcdoc="${frameInner.replaceAll('&','&amp;').replaceAll('"','&quot;')}"></iframe>`
  const frameEvents = await page.evaluate(async targetUrl => {
    window.__frameEvents = []
    await window.testmaster.recorder.start({ url: targetUrl }, event => window.__frameEvents.push(event))
    await new Promise(resolve => setTimeout(resolve, 1600))
    const events = window.__frameEvents
    await window.testmaster.recorder.stop()
    return events
  }, `data:text/html,${encodeURIComponent(frameOuter)}`)
  const frameClick = frameEvents.find(event => event.type === 'action' && event.step?.type === 'click' && event.step?.locator?.value === 'pay')
  if (!frameClick || frameClick.step.locator.framePath?.[0] !== '#checkout') throw new Error('Iframe path was not recorded')

  console.log(JSON.stringify({ passed: true, actionTypes: actions.map(step => step.type), locatorCheck: result.locatorCheck, assertion: assertion.step.type, popupTypes, framePath: frameClick.step.locator.framePath }, null, 2))
} finally { await browser.close() }



