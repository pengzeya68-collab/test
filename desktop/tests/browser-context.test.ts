import { describe, expect, it } from 'vitest'
import { CaseExecutionEngine, CaseSnapshot } from '../src/worker/execution-engine'

const locator = (value: string) => ({ strategy: 'test_id' as const, value, options: {}, fallbacks: [], framePath: [] })
const step = (id: string, type: string, target: any = null, input: any = null) => ({ id, order: 10, name: id, type, enabled: true, breakpoint: false, locator: target, input, timeout_ms: 10000, retry: { count: 0, delay_ms: 0 }, continue_on_failure: false, screenshot: 'on-failure' as const, condition: null, children: [] })
const run = async (steps: any[]) => {
  const snapshot: CaseSnapshot = { case_id: 998, name: 'browser context', base_url: null, default_timeout_ms: 10000, navigation_timeout_ms: 30000, steps }
  return new CaseExecutionEngine().execute(snapshot, null, { headless: true, screenshotsOnFailure: true, traceOnFailure: false }, () => {})
}

describe('multi-page and dialog workflows', () => {
  it('pre-registers dialog acceptance before the triggering click', async () => {
    const url = `data:text/html,${encodeURIComponent('<button data-testid="confirm" onclick="alert(\'saved\')">保存</button>')}`
    const result = await run([step('open','goto',null,{url}),step('dialog','accept_dialog'),step('click','click',locator('confirm'))])
    if (result.status !== 'passed') console.error(JSON.stringify(result, null, 2))
    expect(result.status).toBe('passed')
    expect(result.passedSteps).toBe(3)
  })

  it('switches to a popup and closes it', async () => {
    const sourceHtml = `<meta charset="utf-8"><button data-testid="details" onclick="const popup=window.open('about:blank');popup.document.title='订单详情'">查看订单</button>`
    const source = 'data:text/html,' + encodeURIComponent(sourceHtml)
    const result = await run([
      step('open','goto',null,{url:source}),
      step('popup','click',locator('details')),
      step('switch','switch_page',null,{index:'last'}),
      step('title','assert_title',null,{expected:'订单详情'}),
      step('close','close_page'),
    ])
    if (result.status !== 'passed') console.error(JSON.stringify(result, null, 2))
    expect(result.status).toBe('passed')
    expect(result.passedSteps).toBe(5)
  })
})






