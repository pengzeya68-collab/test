import { autoTestRequest } from '@/utils/request'

export function getGroups() {
  return autoTestRequest.get('/auto-test/groups')
}

export function getGroupsTree() {
  return autoTestRequest.get('/auto-test/groups/tree')
}

export function createGroup(data) {
  return autoTestRequest.post('/auto-test/groups', data)
}

export function updateGroup(id, data) {
  return autoTestRequest.put(`/auto-test/groups/${id}`, data)
}

export function deleteGroup(id) {
  return autoTestRequest.delete(`/auto-test/groups/${id}`)
}
