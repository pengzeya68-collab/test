import request from '@/utils/request'

export function getFavorites() {
  return request.get('/favorites')
}

export function toggleFavorite(data) {
  return request.post('/favorites/toggle', data)
}

export function search(params) {
  return request.get('/search', { params })
}

export function getToolCategories() {
  return request.get('/tools/categories')
}

export function getNotifications(params) {
  return request.get('/notifications', { params })
}

export function readAllNotifications() {
  return request.post('/notifications/read-all')
}

export function readNotification(id) {
  return request.post(`/notifications/${id}/read`)
}

export function getAssertTemplates(params) {
  return request.get('/assert-templates', { params })
}

export function getAssertTemplateCategories() {
  return request.get('/assert-templates/categories')
}
