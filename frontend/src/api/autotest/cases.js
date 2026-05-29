import { autoTestRequest } from '@/utils/request'

export function getCases(params) {
  return autoTestRequest.get('/auto-test/cases', { params })
}

export function getAllCases() {
  return autoTestRequest.get('/auto-test/cases/all')
}

export function getCase(id) {
  return autoTestRequest.get(`/auto-test/cases/${id}`)
}

export function createCase(data) {
  return autoTestRequest.post('/auto-test/cases', data)
}

export function updateCase(id, data) {
  return autoTestRequest.put(`/auto-test/cases/${id}`, data)
}

export function deleteCase(id) {
  return autoTestRequest.delete(`/auto-test/cases/${id}`)
}

export function runCase(id, envId) {
  return autoTestRequest.post(`/auto-test/cases/${id}/run`, null, { params: { env_id: envId } })
}

export function exportJmxCases(caseIds) {
  return autoTestRequest.post('/auto-test/export/jmeter/cases', { case_ids: caseIds })
}

export function exportJmxCase(id) {
  return autoTestRequest.get(`/auto-test/export/jmeter/case/${id}`)
}

export function importJmeter(data) {
  return autoTestRequest.post('/auto-test/import/jmeter', data)
}

export function importPostman(data) {
  return autoTestRequest.post('/auto-test/import/postman', data)
}

export function importSwagger(data) {
  return autoTestRequest.post('/auto-test/import/swagger', data)
}

export function getHistory(params) {
  return autoTestRequest.get('/auto-test/history', { params })
}
