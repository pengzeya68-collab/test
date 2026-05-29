import { autoTestRequest } from '@/utils/request'

export function getTemplates() {
  return autoTestRequest.get('/auto-test/data-factory/templates')
}

export function getTemplate(id) {
  return autoTestRequest.get(`/auto-test/data-factory/templates/${id}`)
}

export function createTemplate(data) {
  return autoTestRequest.post('/auto-test/data-factory/templates', data)
}

export function updateTemplate(id, data) {
  return autoTestRequest.put(`/auto-test/data-factory/templates/${id}`, data)
}

export function deleteTemplate(id) {
  return autoTestRequest.delete(`/auto-test/data-factory/templates/${id}`)
}

export function previewTemplate(id) {
  return autoTestRequest.post(`/auto-test/data-factory/templates/${id}/preview`)
}

export function generateFromTemplate(id, data) {
  return autoTestRequest.post(`/auto-test/data-factory/templates/${id}/generate`, data)
}

export function runDataset(datasetId) {
  return autoTestRequest.post(`/auto-test/data-factory/datasets/${datasetId}/run`)
}

export function bindDatasetToScenario(datasetId, scenarioId) {
  return autoTestRequest.post(`/auto-test/data-factory/datasets/${datasetId}/bind-scenario/${scenarioId}`)
}

export function getDataFactoryScenarios() {
  return autoTestRequest.get('/auto-test/data-factory/scenarios')
}
