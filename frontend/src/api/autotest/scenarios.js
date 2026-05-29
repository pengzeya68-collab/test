import { autoTestRequest } from '@/utils/request'

export function getScenarios(params) {
  return autoTestRequest.get('/auto-test/scenarios', { params })
}

export function getScenario(id) {
  return autoTestRequest.get(`/auto-test/scenarios/${id}`)
}

export function createScenario(data) {
  return autoTestRequest.post('/auto-test/scenarios', data)
}

export function updateScenario(id, data) {
  return autoTestRequest.put(`/auto-test/scenarios/${id}`, data)
}

export function deleteScenario(id) {
  return autoTestRequest.delete(`/auto-test/scenarios/${id}`)
}

export function toggleScenarioStatus(id, is_active) {
  return autoTestRequest.put(`/auto-test/scenarios/${id}/status`, { is_active })
}

export function getAvailableCases() {
  return autoTestRequest.get('/auto-test/scenarios/available-cases')
}

export function addSteps(scenarioId, data) {
  return autoTestRequest.post(`/auto-test/scenarios/${scenarioId}/steps`, data)
}

export function updateStep(scenarioId, stepId, data) {
  return autoTestRequest.put(`/auto-test/scenarios/${scenarioId}/steps/${stepId}`, data)
}

export function removeStep(scenarioId, stepId) {
  return autoTestRequest.delete(`/auto-test/scenarios/${scenarioId}/steps/${stepId}`)
}

export function reorderSteps(scenarioId, data) {
  return autoTestRequest.put(`/auto-test/scenarios/${scenarioId}/steps/reorder`, data)
}

export function getDataset(scenarioId) {
  return autoTestRequest.get(`/auto-test/scenarios/${scenarioId}/dataset`)
}

export function saveDataset(scenarioId, data) {
  return autoTestRequest.post(`/auto-test/scenarios/${scenarioId}/dataset`, data)
}

export function clearDataset(scenarioId) {
  return autoTestRequest.delete(`/auto-test/scenarios/${scenarioId}/dataset`)
}

export function runDataDriven(scenarioId, data) {
  return autoTestRequest.post(`/auto-test/scenarios/${scenarioId}/run-data-driven`, data)
}

export function getExecutionHistory(scenarioId, params) {
  return autoTestRequest.get(`/auto-test/scenarios/${scenarioId}/history`, { params })
}

export function deleteHistory(scenarioId, historyId) {
  return autoTestRequest.delete(`/auto-test/scenarios/${scenarioId}/history/${historyId}`)
}
