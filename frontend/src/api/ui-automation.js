/**
 * UI Automation API module.
 */

import axios from 'axios'
import { getServerUrl } from '@/utils/server-config'
import autoTestRequest from '@/utils/autoTestRequest'

const uiAxios = axios.create({
  baseURL: (import.meta.env.VITE_AUTO_TEST_BASE_URL || '/api') + '/ui-automation',
  timeout: 30000,
})

const sleep = (ms) => new Promise(resolve => window.setTimeout(resolve, ms))

async function retryUpload (operation, attempts = 3) {
  let lastError
  for (let attempt = 0; attempt < attempts; attempt += 1) {
    try { return await operation() } catch (error) {
      lastError = error
      if (attempt + 1 < attempts) await sleep(300 * (attempt + 1))
    }
  }
  throw lastError
}

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
    return uiAxios.get(`/runs/${runId}/artifacts/${artifactId}/content`, { responseType: 'blob' })
  },

  registerRunArtifact(runId, data) {
    return uiAxios.post(`/runs/${runId}/artifacts`, data)
  },

  getRunDefectReport(runId) {
    return uiAxios.get(`/runs/${runId}/defect-report`)
  },

  getArtifactAnnotations(artifactManifestId) {
    return uiAxios.get(`/artifacts/${artifactManifestId}/annotations`)
  },

  saveArtifactAnnotations(artifactManifestId, annotations) {
    return uiAxios.put(`/artifacts/${artifactManifestId}/annotations`, { annotations })
  },

  linkRunArtifact(runId, artifactManifestId) {
    return uiAxios.post(`/runs/${runId}/artifacts/link`, { artifact_manifest_id: artifactManifestId })
  },

  heartbeatRun(runId) {
    return uiAxios.post(`/runs/${runId}/heartbeat`)
  },

  cancelRun(runId) {
    return uiAxios.post(`/runs/${runId}/cancel`)
  },

  analyzeFailure(runId) {
    return uiAxios.post(`/runs/${runId}/ai/failure-analysis`)
  },

  suggestLocators(caseId, data) {
    return uiAxios.post(`/cases/${caseId}/ai/locator-suggestions`, data)
  },

  generateRequirementTestPoints(data) {
    return uiAxios.post('/requirements/test-points', data)
  },

  generateRequirementCaseDrafts(data) {
    return uiAxios.post('/requirements/case-drafts', data)
  },

  getAiAnalysis(analysisId) {
    return uiAxios.get(`/ai-analysis/${analysisId}`)
  },

  submitAiAnalysisFeedback(analysisId, data) {
    return uiAxios.post(`/ai-analysis/${analysisId}/feedback`, data)
  },

  getAiAnalysisMetrics(params = {}) {
    return uiAxios.get('/ai-analysis/metrics', { params })
  },

  async uploadSharedArtifact(run, artifactFile, type, mimeType) {
    if (!run?.execution_id) throw new Error('运行记录缺少统一执行标识，无法上传产物')
    const base64 = String(artifactFile?.contentBase64 || '')
    if (!base64) throw new Error('产物文件为空')
    const binary = Uint8Array.from(atob(base64), char => char.charCodeAt(0))
    const digest = await crypto.subtle.digest('SHA-256', binary)
    const sha256 = Array.from(new Uint8Array(digest), byte => byte.toString(16).padStart(2, '0')).join('')
    const session = await autoTestRequest.post('/auto-test/artifacts/upload-sessions', {
      execution_id: run.execution_id,
      kind: type,
      filename: artifactFile.filename,
      content_type: mimeType,
      size_bytes: binary.byteLength,
      sha256,
    })
    const chunkSize = 4 * 1024 * 1024
    let offset = Number(session.offset || 0)
    while (offset < binary.byteLength) {
      const end = Math.min(offset + chunkSize, binary.byteLength)
      const start = offset
      try {
        await retryUpload(() => autoTestRequest.put(session.chunk_endpoint, binary.slice(start, end), {
          headers: {
            'Content-Type': 'application/octet-stream',
            'Content-Range': `bytes ${start}-${end - 1}/${binary.byteLength}`,
          },
        }))
        offset = end
      } catch (error) {
        // A response can be lost after the server has committed a chunk. Read
        // its offset and continue instead of replaying bytes at the old offset.
        const progress = await retryUpload(() => autoTestRequest.get(`/auto-test/artifacts/upload-sessions/${session.upload_id}`))
        if (progress.status !== 'open' || Number(progress.received_bytes) <= start) throw error
        offset = Number(progress.received_bytes)
      }
    }
    const completed = await retryUpload(() => autoTestRequest.post(`/auto-test/artifacts/upload-sessions/${session.upload_id}/complete`))
    return this.linkRunArtifact(run.id, completed.artifact_id)
  },

  async uploadRunArtifact(runId, artifactFile) {
    const run = await this.getRun(runId)
    return this.uploadSharedArtifact(run, artifactFile, artifactFile.type, artifactFile.mime_type || artifactFile.mimeType || 'application/octet-stream')
  },

  health() {
    return uiAxios.get('/health')
  },
}

export default uiAutomationApi










