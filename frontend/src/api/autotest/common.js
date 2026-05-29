import { autoTestRequest } from '@/utils/request'

export function getEnvironments() {
  return autoTestRequest.get('/auto-test/environments')
}

export function getGlobalVariables() {
  return autoTestRequest.get('/auto-test/global-variables')
}

export function getTaskStatus(taskId) {
  return autoTestRequest.get(`/auto-test/tasks/${taskId}`)
}

export function cancelTask(taskId) {
  return autoTestRequest.post(`/auto-test/tasks/${taskId}/cancel`)
}

export function sendRequest(data) {
  return autoTestRequest.post('/auto-test/send', data)
}

export function getScheduleTasks() {
  return autoTestRequest.get('/auto-test/scheduler/tasks')
}

export function createScheduleTask(data) {
  return autoTestRequest.post('/auto-test/scheduler/tasks', data)
}

export function deleteScheduleTask(taskId) {
  return autoTestRequest.delete(`/auto-test/scheduler/tasks/${taskId}`)
}

export function toggleScheduleTask(taskId) {
  return autoTestRequest.post(`/auto-test/scheduler/tasks/${taskId}/toggle`)
}

export function getReport(reportId) {
  return autoTestRequest.get(`/auto-test/reports/${reportId}`)
}

export function analyzeResult(data) {
  return autoTestRequest.post('/auto-test/analyze-result', data)
}

export function generateReport(data) {
  return autoTestRequest.post('/auto-test/report/generate', data)
}

export function debugExecute(data) {
  return autoTestRequest.post('/auto-test/debug/execute', data)
}

export function importJmeterTree(data) {
  return autoTestRequest.post('/auto-test/import/jmeter/tree', data)
}

export function exportJmeterTree(data) {
  return autoTestRequest.post('/auto-test/export/jmeter/tree', data)
}

export function quickBench(data) {
  return autoTestRequest.post('/auto-test/jmeter/quick-bench', data)
}

export function getBenchStatus(taskId) {
  return autoTestRequest.get(`/auto-test/jmeter/quick-bench/${taskId}`)
}

export function stopBench() {
  return autoTestRequest.post('/auto-test/bench/stop')
}
