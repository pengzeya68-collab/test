/**
 * 后台管理系统API接口
 */

import request from '@/utils/request'

/**
 * 管理员登录
 */
export const login = (data) => {
  return request({
    url: '/api/admin/login',
    method: 'post',
    data
  })
}

/**
 * 获取管理员信息
 */
export const getAdminInfo = () => {
  return request({
    url: '/api/admin/info',
    method: 'get'
  })
}

/**
 * 退出登录
 */
export const logout = () => {
  return request({
    url: '/api/admin/logout',
    method: 'post'
  })
}

/**
 * 仪表盘统计数据
 */
export const getDashboardStats = () => {
  return request({
    url: '/api/admin/dashboard/stats',
    method: 'get'
  })
}

/**
 * 习题管理API
 */
export const exerciseApi = {
  // 获取习题列表
  list: (params) => {
    return request({
      url: '/api/admin/exercises',
      method: 'get',
      params
    })
  },
  
  // 获取习题详情
  detail: (id) => {
    return request({
      url: `/api/admin/exercises/${id}`,
      method: 'get'
    })
  },
  
  // 创建习题
  create: (data) => {
    return request({
      url: '/api/admin/exercises',
      method: 'post',
      data
    })
  },
  
  // 更新习题
  update: (id, data) => {
    return request({
      url: `/api/admin/exercises/${id}`,
      method: 'put',
      data
    })
  },
  
  // 删除习题
  delete: (id) => {
    return request({
      url: `/api/admin/exercises/${id}`,
      method: 'delete'
    })
  }
}

/**
 * 学习路径API
 */
export const learningPathApi = {
  // 获取路径列表
  list: (params) => {
    return request({
      url: '/api/admin/paths',
      method: 'get',
      params
    })
  },
  
  // 获取路径详情
  detail: (id) => {
    return request({
      url: `/api/admin/paths/${id}`,
      method: 'get'
    })
  },
  
  // 创建路径
  create: (data) => {
    return request({
      url: '/api/admin/paths',
      method: 'post',
      data
    })
  },
  
  // 更新路径
  update: (id, data) => {
    return request({
      url: `/api/admin/paths/${id}`,
      method: 'put',
      data
    })
  },
  
  // 删除路径
  delete: (id) => {
    return request({
      url: `/api/admin/paths/${id}`,
      method: 'delete'
    })
  },
  
  // 获取习题选项
  getExerciseOptions: () => {
    return request({
      url: '/api/admin/paths/exercises',
      method: 'get'
    })
  }
}

/**
 * 用户管理API
 */
export const userApi = {
  // 获取用户列表
  list: (params) => {
    return request({
      url: '/api/admin/users',
      method: 'get',
      params
    })
  },
  
  // 获取用户详情
  detail: (id) => {
    return request({
      url: `/api/admin/users/${id}`,
      method: 'get'
    })
  },
  
  // 创建用户
  create: (data) => {
    return request({
      url: '/api/admin/users',
      method: 'post',
      data
    })
  },
  
  // 更新用户
  update: (id, data) => {
    return request({
      url: `/api/admin/users/${id}`,
      method: 'put',
      data
    })
  },
  
  // 删除用户
  delete: (id) => {
    return request({
      url: `/api/admin/users/${id}`,
      method: 'delete'
    })
  },
  
  // 切换用户状态
  toggleStatus: (id, status) => {
    return request({
      url: `/api/admin/users/${id}/status`,
      method: 'put',
      data: { status }
    })
  }
}
