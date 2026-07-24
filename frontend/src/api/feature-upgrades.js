/**
 * Feature upgrade APIs (elements / visual / flaky / defects / shards / protocols / contracts / management).
 */

import axios from 'axios'
import { getServerUrl } from '@/utils/server-config'
import { isDesktopBuild } from '@/utils/build-target'

const client = axios.create({
  baseURL: (import.meta.env.VITE_AUTO_TEST_BASE_URL || '/api') + '/feature-upgrades',
  timeout: 60000,
})

client.interceptors.request.use((config) => {
  if (isDesktopBuild) {
    config.baseURL = `${getServerUrl()}/api/feature-upgrades`
  }
  config.headers = config.headers || {}
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  const projectId = localStorage.getItem('desktop-active-project-id')
  if (projectId && Number(projectId) > 0) {
    config.headers['X-Project-Id'] = String(projectId)
  } else {
    delete config.headers['X-Project-Id']
  }
  return config
})

client.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const detail = error.response?.data?.detail
    const message = typeof detail === 'string'
      ? detail
      : detail?.message || error.message || '请求失败'
    return Promise.reject(new Error(message))
  }
)

/** Resolve absolute API asset path (no auth). Prefer fetchAuthBlobUrl for <img>. */
export function featureUpgradeAssetUrl(pathOrUrl) {
  if (!pathOrUrl) return ''
  if (/^https?:\/\//i.test(pathOrUrl)) return pathOrUrl
  if (pathOrUrl.startsWith('/')) {
    if (isDesktopBuild) return `${getServerUrl()}${pathOrUrl}`
    if (typeof window !== 'undefined') return `${window.location.origin}${pathOrUrl}`
  }
  return pathOrUrl
}

/**
 * Fetch binary asset with Bearer token and return an object URL for <img>/<iframe>.
 * Caller should revokeObjectURL when done.
 */
export async function fetchAuthBlobUrl(pathOrUrl) {
  const absolute = featureUpgradeAssetUrl(pathOrUrl)
  if (!absolute) return ''
  const token = localStorage.getItem('token') || ''
  const headers = {}
  if (token) headers.Authorization = `Bearer ${token}`
  const response = await fetch(absolute, { headers })
  if (!response.ok) {
    const text = await response.text().catch(() => '')
    throw new Error(text || `asset load failed: ${response.status}`)
  }
  const blob = await response.blob()
  return URL.createObjectURL(blob)
}

export const featureUpgradesApi = {
  listPages(projectId) {
    return client.get('/pages', { params: { project_id: projectId } })
  },
  createPage(data) {
    return client.post('/pages', data)
  },
  listElements(projectId, pageId) {
    return client.get('/elements', { params: { project_id: projectId, page_id: pageId } })
  },
  createElement(data) {
    return client.post('/elements', data)
  },
  updateElement(elementId, data) {
    return client.patch(`/elements/${elementId}`, data)
  },
  bindStepElement(data) {
    return client.post('/elements/bind-step', data)
  },
  heal(data) {
    return client.post('/healing/heal', data)
  },
  listHealing(projectId, params = {}) {
    return client.get('/healing', { params: { project_id: projectId, ...params } })
  },
  reviewHealing(recordId, action) {
    return client.post(`/healing/${recordId}/review`, { action })
  },
  listBaselines(params = {}) {
    return client.get('/visual/baselines', { params })
  },
  createBaseline(data) {
    return client.post('/visual/baselines', data)
  },
  compareVisual(data) {
    return client.post('/visual/compare', data)
  },
  listComparisons(params = {}) {
    return client.get('/visual/comparisons', { params })
  },
  getComparison(comparisonId) {
    return client.get(`/visual/comparisons/${comparisonId}`)
  },
  setVisualVerdict(comparisonId, data) {
    return client.post(`/visual/comparisons/${comparisonId}/verdict`, data)
  },
  listMasks(baselineId) {
    return client.get(`/visual/baselines/${baselineId}/masks`)
  },
  addMask(baselineId, data) {
    return client.post(`/visual/baselines/${baselineId}/masks`, data)
  },
  getVisualConfig(projectId) {
    return client.get('/visual/config', { params: { project_id: projectId } })
  },
  updateVisualConfig(projectId, data) {
    return client.put('/visual/config', data, { params: { project_id: projectId } })
  },
  visualStats(projectId) {
    return client.get('/visual/stats', { params: { project_id: projectId } })
  },
  comparisonImageUrl(comparisonId, kind) {
    return featureUpgradeAssetUrl(`/api/feature-upgrades/visual/comparisons/${comparisonId}/image/${kind}`)
  },
  baselineImageUrl(baselineId) {
    return featureUpgradeAssetUrl(`/api/feature-upgrades/visual/baselines/${baselineId}/image`)
  },
  registerTrace(data) {
    return client.post('/traces/register', data)
  },
  listTraces(projectId, params = {}) {
    return client.get('/traces', { params: { project_id: projectId, ...params } })
  },
  getTrace(traceId) {
    return client.get(`/traces/${traceId}`)
  },
  getTraceActionSnapshot(traceId, actionId) {
    return client.get(`/traces/${traceId}/actions/${encodeURIComponent(actionId)}/snapshot`)
  },
  traceResourceUrl(traceId, resourceName) {
    return featureUpgradeAssetUrl(
      `/api/feature-upgrades/traces/${traceId}/resources/${encodeURIComponent(resourceName)}`,
    )
  },
  traceActionScreenshotUrl(traceId, actionId) {
    return featureUpgradeAssetUrl(
      `/api/feature-upgrades/traces/${traceId}/actions/${encodeURIComponent(actionId)}/screenshot`,
    )
  },
  listFlaky(projectId, params = {}) {
    return client.get('/flaky', { params: { project_id: projectId, ...params } })
  },
  setQuarantine(recordId, quarantined) {
    return client.post(`/flaky/${recordId}/quarantine`, { quarantined })
  },
  listTrackers(projectId) {
    return client.get('/defects/trackers', { params: { project_id: projectId } })
  },
  upsertTracker(projectId, data) {
    return client.post('/defects/trackers', data, { params: { project_id: projectId } })
  },
  listDefects(projectId, status) {
    return client.get('/defects', { params: { project_id: projectId, status } })
  },
  createDefectFromFailure(data) {
    return client.post('/defects/from-failure', data)
  },
  createShards(data) {
    return client.post('/shards', data)
  },
  getShardProgress(suiteExecutionId) {
    return client.get(`/shards/progress/${suiteExecutionId}`)
  },
  executeProtocol(data) {
    return client.post('/protocols/execute', data)
  },
  listProtos(projectId) {
    return client.get('/protocols/protos', { params: { project_id: projectId } })
  },
  upsertProto(data) {
    return client.post('/protocols/protos', data)
  },
  getProto(protoId) {
    return client.get(`/protocols/protos/${protoId}`)
  },
  deleteProto(protoId) {
    return client.delete(`/protocols/protos/${protoId}`)
  },
  listNetworkRules(projectId) {
    return client.get('/network/rules', { params: { project_id: projectId } })
  },
  createNetworkRule(projectId, data) {
    return client.post('/network/rules', data, { params: { project_id: projectId } })
  },
  updateNetworkRule(ruleId, data) {
    return client.patch(`/network/rules/${ruleId}`, data)
  },
  deleteNetworkRule(ruleId) {
    return client.delete(`/network/rules/${ruleId}`)
  },
  assignNetworkRule(data) {
    return client.post('/network/rules/assign', data)
  },
  rulesForTarget(projectId, targetType, targetId) {
    return client.get('/network/rules/for-target', {
      params: { project_id: projectId, target_type: targetType, target_id: targetId },
    })
  },
  listSnapshots(projectId) {
    return client.get('/contracts/snapshots', { params: { project_id: projectId } })
  },
  createSnapshot(data) {
    return client.post('/contracts/snapshots', data)
  },
  listSchemaChanges(projectId) {
    return client.get('/contracts/changes', { params: { project_id: projectId } })
  },
  listContractRules(projectId) {
    return client.get('/contracts/rules', { params: { project_id: projectId } })
  },
  upsertContractRule(projectId, data) {
    return client.post('/contracts/rules', data, { params: { project_id: projectId } })
  },
  validateContract(data) {
    return client.post('/contracts/validate', data)
  },
  listHealthMonitors(projectId) {
    return client.get('/health/monitors', { params: { project_id: projectId } })
  },
  createHealthMonitor(projectId, data) {
    return client.post('/health/monitors', data, { params: { project_id: projectId } })
  },
  runHealthCheck(monitorId, data = {}) {
    return client.post(`/health/monitors/${monitorId}/check`, data)
  },
  listHealthResults(monitorId) {
    return client.get(`/health/monitors/${monitorId}/results`)
  },
  generateCode(data) {
    return client.post('/codegen', data)
  },
  getFlow(scenarioId) {
    return client.get(`/flow/${scenarioId}`)
  },
  saveFlow(scenarioId, data) {
    return client.put(`/flow/${scenarioId}`, data)
  },
  listReviews(projectId, params = {}) {
    return client.get('/reviews', { params: { project_id: projectId, ...params } })
  },
  createReview(data) {
    return client.post('/reviews', data)
  },
  reviewAction(reviewId, data) {
    return client.post(`/reviews/${reviewId}/actions`, data)
  },
  listReviewComments(reviewId) {
    return client.get(`/reviews/${reviewId}/comments`)
  },
  addReviewComment(reviewId, data) {
    return client.post(`/reviews/${reviewId}/comments`, data)
  },
  listRequirements(projectId) {
    return client.get('/requirements', { params: { project_id: projectId } })
  },
  createRequirement(projectId, data) {
    return client.post('/requirements', data, { params: { project_id: projectId } })
  },
  linkRequirement(data) {
    return client.post('/requirements/link', data)
  },
  requirementCoverage(projectId) {
    return client.get('/requirements/coverage', { params: { project_id: projectId } })
  },
  listReportTemplates(projectId) {
    return client.get('/reports/templates', { params: { project_id: projectId } })
  },
  upsertReportTemplate(projectId, data) {
    return client.post('/reports/templates', data, { params: { project_id: projectId } })
  },
  renderReport(data) {
    return client.post('/reports/render', data)
  },
}

export default featureUpgradesApi
