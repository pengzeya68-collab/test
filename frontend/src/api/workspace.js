import { autoTestRequest } from '@/utils/request'

export const workspaceApi = {
  listProjects: () => autoTestRequest.get('/workspace/projects'),
  createProject: (data) => autoTestRequest.post('/workspace/projects', data),
  getProject: (id) => autoTestRequest.get(`/workspace/projects/${id}`),
  deleteProject: (id) => autoTestRequest.delete(`/workspace/projects/${id}`),
  purgeProject: (id, confirmationName) => autoTestRequest.post(`/workspace/projects/${id}/purge`, {
    confirmation_name: confirmationName,
  }),
  listMembers: (id) => autoTestRequest.get(`/workspace/projects/${id}/members`),
  addMember: (id, data) => autoTestRequest.post(`/workspace/projects/${id}/members`, data),
  removeMember: (id, userId) => autoTestRequest.delete(`/workspace/projects/${id}/members/${userId}`),
}

export function getActiveProjectId() {
  const raw = localStorage.getItem('desktop-active-project-id')
  if (!raw) return null
  const n = Number(raw)
  return Number.isFinite(n) && n > 0 ? n : null
}

export function setActiveProjectId(id) {
  if (id == null) localStorage.removeItem('desktop-active-project-id')
  else localStorage.setItem('desktop-active-project-id', String(id))
}
