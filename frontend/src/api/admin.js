import request from '@/utils/request'

// 管理员登录
export function adminLogin(data) {
  return request.post('/admin/login', data)
}

// 获取管理员信息
export function getAdminInfo() {
  return request.get('/admin/info')
}

// 获取统计数据
export function getDashboardStats() {
  return request.get('/admin/dashboard/stats')
}

// 习题相关
export function getExercises(params) {
  return request.get('/admin/exercises', { params })
}

export function getExercise(id) {
  return request.get(`/admin/exercises/${id}`)
}

export function createExercise(data) {
  return request.post('/admin/exercises', data)
}

export function updateExercise(id, data) {
  return request.put(`/admin/exercises/${id}`, data)
}

export function deleteExercise(id) {
  return request.delete(`/admin/exercises/${id}`)
}

export function batchImportExercises(data) {
  return request.post('/admin/exercises/batch-import', data)
}

// 学习路径相关
export function getLearningPaths(params) {
  return request.get('/admin/learning-paths', { params })
}

export function getLearningPath(id) {
  return request.get(`/admin/learning-paths/${id}`)
}

export function createLearningPath(data) {
  return request.post('/admin/learning-paths', data)
}

export function updateLearningPath(id, data) {
  return request.put(`/admin/learning-paths/${id}`, data)
}

export function deleteLearningPath(id) {
  return request.delete(`/admin/learning-paths/${id}`)
}

// 用户相关
export function getUsers(params) {
  return request.get('/admin/users', { params })
}

export function getUser(id) {
  return request.get(`/admin/users/${id}`)
}

export function updateUser(id, data) {
  return request.put(`/admin/users/${id}`, data)
}

export function deleteUser(id) {
  return request.delete(`/admin/users/${id}`)
}

export function updateUserStatus(id, data) {
  return request.patch(`/admin/users/${id}/status`, data)
}

// 考试相关
export function getExams(params) {
  return request.get('/admin/exams', { params })
}

export function getExam(id) {
  return request.get(`/admin/exams/${id}`)
}

export function createExam(data) {
  return request.post('/admin/exams', data)
}

export function updateExam(id, data) {
  return request.put(`/admin/exams/${id}`, data)
}

export function deleteExam(id) {
  return request.delete(`/admin/exams/${id}`)
}

// AI配置相关
export function getAIConfigs() {
  return request.get('/admin/ai-configs')
}

export function getAIConfig(id) {
  return request.get(`/admin/ai-configs/${id}`)
}

export function createAIConfig(data) {
  return request.post('/admin/ai-configs', data)
}

export function updateAIConfig(id, data) {
  return request.put(`/admin/ai-configs/${id}`, data)
}

export function deleteAIConfig(id) {
  return request.delete(`/admin/ai-configs/${id}`)
}

export function activateAIConfig(id) {
  return request.post(`/admin/ai-configs/${id}/activate`)
}

export function testAIConfig(id) {
  return request.post(`/admin/ai-configs/${id}/test`)
}

export function getAIConfigQuota(id) {
  return request.get(`/admin/ai-configs/${id}/quota`)
}

export function getActiveAIConfig() {
  return request.get('/admin/ai-configs/active')
}
