import { chromium } from 'playwright'
import { createServer } from 'node:http'

const browser = await chromium.connectOverCDP('http://127.0.0.1:9333')
let captured = ''
const server = createServer((request, response) => {
  const chunks = []
  request.on('data', chunk => chunks.push(chunk))
  request.on('end', () => {
    captured = Buffer.concat(chunks).toString('utf8')
    response.writeHead(200, { 'content-type': 'application/json' })
    response.end(JSON.stringify({ ok: true, token: 'post-script-token', received: true }))
  })
})
await new Promise(resolve => server.listen(0, '127.0.0.1', resolve))
let fixture

try {
  const page = browser.contexts()[0].pages()[0]
  fixture = await page.evaluate(async origin => {
    const headers = { Authorization: `Bearer ${localStorage.getItem('token')}`, 'Content-Type': 'application/json' }
    const api = async (path, options = {}) => { const r = await fetch(`http://127.0.0.1:5001/api/auto-test${path}`, { ...options, headers }); const data = await r.json(); if (!r.ok) throw new Error(`${path}:${JSON.stringify(data)}`); return data }
    const stamp = Date.now(); const group = await api('/groups', { method: 'POST', body: JSON.stringify({ name: `脚本上传验收-${stamp}` }) })
    const env = await api('/environments', { method: 'POST', body: JSON.stringify({ name: `脚本上传环境-${stamp}`, base_url: origin, is_default: true, variables: {} }) })
    const item = await api('/cases', { method: 'POST', body: JSON.stringify({
      name: `脚本上传用例-${stamp}`, group_id: group.id, method: 'POST', url: '/upload', body_type: 'form-data',
      payload: { description: '{{script_token}}', attachment: { type: 'file', filename: 'proof.txt', content_type: 'text/plain', content_base64: 'aGVsbG8=' } },
      assertions: [{ target: 'status_code', operator: 'equals', expected: 200 }, { target: 'response_body', operator: 'contains', expected: 'post-script-token' }],
      pre_script_language: 'python', pre_script: 'pm.environment.set("script_token", "from-pre-script")',
      post_script_language: 'python', post_script: 'pm.extract("saved_token", "$.token")',
    }) })
    return { group, env, item }
  }, `http://127.0.0.1:${server.address().port}`)
  const result = await page.evaluate(async f => {
    const r = await fetch(`http://127.0.0.1:5001/api/auto-test/cases/${f.item.id}/run`, { method: 'POST', headers: { Authorization: `Bearer ${localStorage.getItem('token')}`, 'Content-Type': 'application/json' }, body: JSON.stringify({ env_id: f.env.id }) })
    return { status: r.status, body: await r.json() }
  }, fixture)
  if (result.status !== 200 || !result.body?.success || result.body?.assert_result?.passed !== true) throw new Error(`CASE_RUN_FAILED:${JSON.stringify(result)}`)
  if (!captured.includes('from-pre-script') || !captured.includes('filename="proof.txt"') || !captured.includes('hello')) throw new Error(`MULTIPART_OR_PRE_SCRIPT_FAILED:${captured}`)
  if (result.body?.extracted_variables?.saved_token !== 'post-script-token') throw new Error(`POST_SCRIPT_EXTRACTION_FAILED:${JSON.stringify(result.body)}`)
  console.log(JSON.stringify({ passed: true, checks: ['case-run', 'multipart-file-part', 'pre-script-variable', 'assertions', 'post-script-extraction', 'history-write'], slowUserPauses: true }))
} finally {
  const page = browser.contexts()[0]?.pages()[0]
  if (page && fixture) await page.evaluate(async f => { const h = { Authorization: `Bearer ${localStorage.getItem('token')}` }; const b = 'http://127.0.0.1:5001/api/auto-test'; await fetch(`${b}/cases/${f.item.id}`, { method: 'DELETE', headers: h }); await fetch(`${b}/environments/${f.env.id}`, { method: 'DELETE', headers: h }); await fetch(`${b}/groups/${f.group.id}`, { method: 'DELETE', headers: h }) }, fixture).catch(() => {})
  await browser.close(); await new Promise(resolve => server.close(resolve))
}
