import { afterEach, describe, expect, it } from 'vitest'
import fs from 'fs'
import os from 'os'
import path from 'path'
import { CaseExecutionEngine, CaseSnapshot, safeArtifactFilename, uniqueArtifactPath } from '../src/worker/execution-engine'

const tempUpload = path.join(os.tmpdir(), 'testmaster-upload-fixture.txt')
const artifactRoot = path.join(os.tmpdir(), 'testmaster-file-workflow-artifacts')
const downloaded = path.join(artifactRoot, 'downloads', 'report.txt')

afterEach(() => {
  fs.rmSync(tempUpload, { force: true })
  fs.rmSync(artifactRoot, { recursive: true, force: true })
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
    const result = await engine.execute(snapshot, null, { headless: true, screenshotsOnFailure: true, traceOnFailure: false, artifactRootDir: artifactRoot }, () => {})
    expect(result.status).toBe('passed')
    expect(result.passedSteps).toBe(3)
    expect(fs.readFileSync(downloaded, 'utf8')).toBe('download-ok')
  })

  it('sanitizes traversal, control characters and Windows reserved filenames', () => {
    expect(safeArtifactFilename('..\\..\\CON.txt')).toBe('_CON.txt')
    expect(safeArtifactFilename('../bad\u0000name?.txt')).toBe('bad_name_.txt')
    const first = uniqueArtifactPath(path.join(artifactRoot, 'downloads'), '../../report.txt')
    fs.writeFileSync(first, 'one')
    const second = uniqueArtifactPath(path.join(artifactRoot, 'downloads'), '../../report.txt')
    expect(path.dirname(first)).toBe(path.join(artifactRoot, 'downloads'))
    expect(path.basename(first)).toBe('report.txt')
    expect(path.basename(second)).toBe('report-1.txt')
  })

  it('keeps screenshots with hostile step IDs under the artifact root', async () => {
    const malicious = '..\\..\\outside'
    const snapshot: CaseSnapshot = {
      case_id: 1001, name: 'safe screenshot path', base_url: null, default_timeout_ms: 500,
      navigation_timeout_ms: 1000,
      steps: [
        { id: 'open', order: 10, name: 'open', type: 'goto', enabled: true, breakpoint: false, locator: null, input: { url: 'data:text/html,<body>ready</body>' }, timeout_ms: 1000, retry: { count: 0, delay_ms: 0 }, continue_on_failure: false, screenshot: 'never', condition: null, children: [] },
        { id: malicious, order: 20, name: 'fail', type: 'assert_visible', enabled: true, breakpoint: false, locator: { strategy: 'css', value: '#missing', options: {}, fallbacks: [], framePath: [] }, input: null, timeout_ms: 200, retry: { count: 0, delay_ms: 0 }, continue_on_failure: false, screenshot: 'on-failure', condition: null, children: [] },
      ],
    }
    const result = await new CaseExecutionEngine().execute(
      snapshot, null,
      { headless: true, screenshotsOnFailure: true, traceOnFailure: false, artifactRootDir: artifactRoot },
      () => {},
    )
    const screenshot = result.stepResults.find(item => item.stepId === malicious)?.screenshotPath
    expect(screenshot).toBeTruthy()
    expect(path.resolve(screenshot!).startsWith(`${path.resolve(artifactRoot, 'screenshots')}${path.sep}`)).toBe(true)
    expect(path.basename(screenshot!)).not.toContain('..')
  })
})
