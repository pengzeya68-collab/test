import { describe, expect, it } from 'vitest'
import { CaseExecutionEngine, CaseSnapshot, StepEvent } from '../src/worker/execution-engine'

const baseStep = (id: string, type: string, input: any) => ({ id, order: 10, name: id, type, enabled: true, breakpoint: false, locator: null, input, timeout_ms: 5000, retry: { count: 0, delay_ms: 0 }, continue_on_failure: false, screenshot: 'on-failure' as const, condition: null, children: [] })

describe('interactive debugger', () => {
  it('pauses before every step, exposes variables, and resumes one step at a time', async () => {
    const engine = new CaseExecutionEngine()
    const snapshot: CaseSnapshot = { case_id: 997, name: 'debug', base_url: null, default_timeout_ms: 5000, navigation_timeout_ms: 10000, steps: [baseStep('set','set_variable',{name:'orderId',value:'A-100'}),baseStep('open','goto',{url:'data:text/html,<title>debug</title>'})] }
    const paused: Extract<StepEvent,{type:'run:paused'}>[] = []
    const events: StepEvent[] = []
    const resultPromise = engine.execute(snapshot, null, { headless: true, screenshotsOnFailure: true, traceOnFailure: false, debugMode: true }, event => {
      events.push(event)
      if (event.type === 'run:paused') {
        paused.push(event)
        setTimeout(() => engine.resume('step'), 10)
      }
    })
    const result = await resultPromise
    expect(result.status).toBe('passed')
    expect(paused.map(event => event.stepId)).toEqual(['set','open'])
    expect(paused[0].variables).toEqual({})
    expect(paused[1].variables).toEqual({ orderId: 'A-100' })
    expect(events.filter(event => event.type === 'step:pass')).toHaveLength(2)
  })

  it('stops at an explicit breakpoint during normal execution', async () => {
    const engine = new CaseExecutionEngine()
    const first = baseStep('first','set_variable',{name:'x',value:'1'})
    const second = { ...baseStep('second','set_variable',{name:'y',value:'2'}), breakpoint: true }
    const snapshot: CaseSnapshot = { case_id: 996, name: 'breakpoint', base_url: null, default_timeout_ms: 5000, navigation_timeout_ms: 10000, steps: [first,second] }
    let pausedAt = ''
    const result = await engine.execute(snapshot, null, { headless: true, screenshotsOnFailure: true, traceOnFailure: false }, event => { if(event.type==='run:paused'){pausedAt=event.stepId;setTimeout(()=>engine.resume('continue'),10)} })
    expect(result.status).toBe('passed')
    expect(pausedAt).toBe('second')
  })
})
