/**
 * UI Automation API module.
 */

import axios from 'axios'
import { getServerUrl } from '@/utils/server-config'

const uiAxios = axios.create({
  baseURL: (import.meta.env.VITE_AUTO_TEST_BASE_URL || '/api') + '/ui-automation',
  timeout: 30000,
})

uiAxios.interceptors.request.use((config) => {
  if (import.meta.env.VITE_DESKTOP_BUILD === 'true') {
    config.baseURL = `${getServerUrl()}/api/ui-automation`
  }
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

uiAxios.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const detail = error.response?.data?.detail
    const message = typeof detail === 'string'
      ? detail
      : detail?.message || error.message || '请求失败，请检查服务是否正常'
    return Promise.reject(new Error(message))
  }
)

export const uiAutomationApi = {
  listCases(params = {}) {
    return uiAxios.get('/cases', { params })
  },

  getCase(caseId) {
    return uiAxios.get(`/cases/${caseId}`)
  },

  createCase(data) {
    return uiAxios.post('/cases', data)
  },

  updateCase(caseId, data) {
    return uiAxios.put(`/cases/${caseId}`, data)
  },

  deleteCase(caseId) {
    return uiAxios.delete(`/cases/${caseId}`)
  },

  batchSaveSteps(caseId, steps) {
    return uiAxios.put(`/cases/${caseId}/steps`, { steps })
  },

  createVersion(caseId, changeSummary = null) {
    return uiAxios.post(`/cases/${caseId}/versions`, { change_summary: changeSummary })
  },

  listVersions(caseId) {
    return uiAxios.get(`/cases/${caseId}/versions`)
  },

  getVersion(caseId, versionId) {
    return uiAxios.get(`/cases/${caseId}/versions/${versionId}`)
  },

  restoreVersion(caseId, versionId) {
    return uiAxios.post(`/cases/${caseId}/versions/${versionId}/restore`)
  },

  listGroups() {
    return uiAxios.get('/groups')
  },

  createGroup(data) {
    return uiAxios.post('/groups', data)
  },

  updateGroup(groupId, data) {
    return uiAxios.put(`/groups/${groupId}`, data)
  },

  deleteGroup(groupId) {
    return uiAxios.delete(`/groups/${groupId}`)
  },

  listSuites() { return uiAxios.get('/suites') },
  getSuite(suiteId) { return uiAxios.get('/suites/' + suiteId) },
  createSuite(data) { return uiAxios.post('/suites', data) },
  updateSuite(suiteId, data) { return uiAxios.put('/suites/' + suiteId, data) },
  replaceSuiteItems(suiteId, items) { return uiAxios.put('/suites/' + suiteId + '/items', items) },
  getSuiteExecutionPlan(suiteId) { return uiAxios.get('/suites/' + suiteId + '/execution-plan') },
  deleteSuite(suiteId) { return uiAxios.delete('/suites/' + suiteId) },
  listRuns(params = {}) {
    return uiAxios.get('/runs', { params })
  },

  createRun(data) {
    return uiAxios.post('/runs', data)
  },

  getRun(runId) {
    return uiAxios.get(`/runs/${runId}`)
  },

  appendRunEvents(runId, events) {
    return uiAxios.post(`/runs/${runId}/events`, { events })
  },

  listRunStepResults(runId) {
    return uiAxios.get(`/runs/${runId}/step-results`)
  },

  listRunArtifacts(runId) {
    return uiAxios.get(`/runs/${runId}/artifacts`)
  },

  getRunArtifactContent(runId, artifactId) {
    return uiAxios.get(`/runs/${runId}/artifacts/${artifactId}/content`)
  },

  registerRunArtifact(runId, data) {
    return uiAxios.post(`/runs/${runId}/artifacts`, data)
  },

  uploadRunArtifact(runId, data) {
    return uiAxios.post(`/runs/${runId}/artifacts/upload`, data)
  },

  health() {
    return uiAxios.get('/health')
  },
}

export default uiAutomationApi










