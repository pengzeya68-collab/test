import { afterEach, describe, expect, it } from 'vitest'
import fs from 'fs'
import os from 'os'
import path from 'path'
import { CaseExecutionEngine, CaseSnapshot } from '../src/worker/execution-engine'

const tempUpload = path.join(os.tmpdir(), 'testmaster-upload-fixture.txt')
const downloaded = path.join(os.tmpdir(), 'testmaster-downloads', 'report.txt')

afterEach(() => {
  fs.rmSync(tempUpload, { force: true })
  fs.rmSync(downloaded, { force: true })
})

describe('enterprise file workflows', () => {
  it('uploads a selected file and downloads an artifact', async () => {
    fs.writeFileSync(tempUpload, 'TestMaster upload fixture', 'utf8')
    const html = `<input data-testid="upload" type="file"><a data-testid="download" download="report.txt" href="data:text/plain,download-ok">下载</a>`
    const url = `data:text/html,${encodeURIComponent(html)}`
    const step = (id: string, type: string, locator: any, input: any) => ({
      id, order: 10, name: id, type, enabled: true, breakpoint: false, locator, input,
      timeout_ms: 10000, retry: { count: 0, delay_ms: 0 }, continue_on_failure: false,
      screenshot: 'on-failure' as const, condition: null, children: [],
    })
    const snapshot: CaseSnapshot = {
      case_id: 999, name: 'file workflow', base_url: null, default_timeout_ms: 10000,
      navigation_timeout_ms: 30000,
      steps: [
        step('open', 'goto', null, { url }),
        step('upload', 'upload_file', { strategy: 'test_id', value: 'upload', options: {}, fallbacks: [], framePath: [] }, { paths: [tempUpload] }),
        step('download', 'download', { strategy: 'test_id', value: 'download', options: {}, fallbacks: [], framePath: [] }, {}),
      ],
    }
    const engine = new CaseExecutionEngine()
    const result = await engine.execute(snapshot, null, { headless: true, screenshotsOnFailure: true, traceOnFailure: false }, () => {})
    expect(result.status).toBe('passed')
    expect(result.passedSteps).toBe(3)
    expect(fs.readFileSync(downloaded, 'utf8')).toBe('download-ok')
  })
})
