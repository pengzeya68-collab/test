import { chromium } from 'playwright'
import { createServer } from 'node:http'

const pause = (page, milliseconds = 650) => page.waitForTimeout(milliseconds)
const browser = await chromium.connectOverCDP('http://127.0.0.1:9333')
const server = createServer((request, response) => {
  if (request.url === '/slow') return setTimeout(() => { response.writeHead(200, { 'content-type': 'application/json' }); response.end('{"ok":true}') }, 12000)
  if (request.url === '/after') return response.end('{"unexpected":true}')
  response.writeHead(404).end()
})
await new Promise(resolve => server.listen(0, '127.0.0.1', resolve))
let fixture

try {
  const page = browser.contexts()[0].pages()[0]
  const origin = `http://127.0.0.1:${server.address().port}`
  fixture = await page.evaluate(async origin => {
    const headers = { Authorization: `Bearer ${localStorage.getItem('token')}`, 'Content-Type': 'application/json' }
    const api = async (path, options = {}) => { const r = await fetch(`http://127.0.0.1:5001/api/auto-test${path}`, { ...options, headers }); const data = await r.json(); if (!r.ok) throw new Error(`${path}:${JSON.stringify(data)}`); return data }
    const stamp = Date.now()
    const group = await api('/groups', { method: 'POST', body: JSON.stringify({ name: `取消验收分组-${stamp}` }) })
    const slow = await api('/cases', { method: 'POST', body: JSON.stringify({ name: `取消慢接口-${stamp}`, group_id: group.id, method: 'GET', url: '/slow', assertions: [{ field: 'status_code', operator: 'equals', expected: 200 }] }) })
    const after = await api('/cases', { method: 'POST', body: JSON.stringify({ name: `取消后接口-${stamp}`, group_id: group.id, method: 'GET', url: '/after', assertions: [{ field: 'status_code', operator: 'equals', expected: 200 }] }) })
    const env = await api('/environments', { method: 'POST', body: JSON.stringify({ name: `取消环境-${stamp}`, base_url: origin, is_default: true, variables: {} }) })
    const scenario = await api('/scenarios', { method: 'POST', body: JSON.stringify({ name: `取消场景-${stamp}`, is_active: true }) })
    await api(`/scenarios/${scenario.id}/steps`, { method: 'POST', body: JSON.stringify({ api_case_id: slow.id, step_order: 0, is_active: true }) })
    await api(`/scenarios/${scenario.id}/steps`, { method: 'POST', body: JSON.stringify({ api_case_id: after.id, step_order: 1, is_active: true }) })
    return { group, slow, after, env, scenario }
  }, origin)
  await page.evaluate(id => { location.hash = `#/scenarios/${id}` }, fixture.scenario.id)
  await page.locator('.scenario-name-input input').waitFor({ timeout: 30000 })
  const select = page.locator('.editor-header .el-select').first(); await select.click(); await page.locator('.el-select-dropdown:visible').getByText(fixture.env.name, { exact: true }).click()
  await page.getByRole('button', { name: '运行场景', exact: true }).click()
  const dialog = page.getByRole('dialog', { name: '场景执行结果' })
  await dialog.getByRole('button', { name: /停止执行/ }).waitFor({ timeout: 30000 })
  await pause(page, 1100)
  await dialog.getByRole('button', { name: /停止执行/ }).click()
  await page.getByText('任务已被用户强制终止', { exact: false }).waitFor({ timeout: 15000 })
  const cancelled = await page.waitForFunction(async id => {
    const r = await fetch(`http://127.0.0.1:5001/api/auto-test/scenarios/${id}/execution-history`, { headers: { Authorization: `Bearer ${localStorage.getItem('token')}` } }); const d = await r.json(); return d.items?.some(item => item.status === 'cancelled') || false
  }, fixture.scenario.id, { timeout: 20000 })
  if (!cancelled) throw new Error('CANCEL_HISTORY_NOT_RECORDED')
  console.log(JSON.stringify({ passed: true, checks: ['scenario-start', 'visible-stop-control', 'task-cancel', 'cancel-history-record'], slowUserPauses: true }))
} finally {
  const page = browser.contexts()[0]?.pages()[0]
  if (page && fixture) await page.evaluate(async f => { const h = { Authorization: `Bearer ${localStorage.getItem('token')}` }; const b = 'http://127.0.0.1:5001/api/auto-test'; await fetch(`${b}/scenarios/${f.scenario.id}`, { method: 'DELETE', headers: h }); await fetch(`${b}/environments/${f.env.id}`, { method: 'DELETE', headers: h }); await fetch(`${b}/cases/${f.slow.id}`, { method: 'DELETE', headers: h }); await fetch(`${b}/cases/${f.after.id}`, { method: 'DELETE', headers: h }); await fetch(`${b}/groups/${f.group.id}`, { method: 'DELETE', headers: h }) }, fixture).catch(() => {})
  await browser.close(); await new Promise(resolve => server.close(resolve))
}
