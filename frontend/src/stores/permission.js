/**
 * 权限 Pinia Store
 *
 * 维护当前登录用户的权限列表，提供权限检查方法：
 * - hasPermission(code)      检查单个权限
 * - hasAnyPermission(codes)  满足任一
 * - hasAllPermissions(codes) 全部满足
 * - fetchPermissions()       从后端拉取当前用户权限
 *
 * 通配符 "*" 视为拥有全部权限（管理员）。
 */

import { defineStore } from 'pinia'
import { ref } from 'vue'
import request from '@/utils/request'

export const usePermissionStore = defineStore('permission', () => {
  // 当前用户权限代码列表
  const permissions = ref([])
  // 当前用户角色代码列表
  const roles = ref([])
  // 是否管理员（短路放行）
  const isAdmin = ref(false)
  // 当前用户ID
  const userId = ref(null)
  const username = ref('')
  // 是否已加载过（避免重复请求）
  const loaded = ref(false)

  const WILDCARD = '*'

  /** 是否拥有指定权限（通配符 * 视为全部通过） */
  const hasPermission = (code) => {
    if (!code) return true
    if (isAdmin.value) return true
    if (permissions.value.includes(WILDCARD)) return true
    if (permissions.value.includes(code)) return true
    // 模块通配：case:* 覆盖 case:create 等
    const moduleWildcard = String(code).split(':')[0] + ':*'
    return permissions.value.includes(moduleWildcard)
  }

  /** 满足任一权限即可 */
  const hasAnyPermission = (codes) => {
    if (!codes || codes.length === 0) return true
    return codes.some((c) => hasPermission(c))
  }

  /** 需全部满足 */
  const hasAllPermissions = (codes) => {
    if (!codes || codes.length === 0) return true
    return codes.every((c) => hasPermission(c))
  }

  /** 从后端拉取当前用户权限 */
  const fetchPermissions = async () => {
    try {
      const res = await request.get('/admin/rbac/users/me/permissions')
      permissions.value = res.permissions || []
      roles.value = res.roles || []
      isAdmin.value = !!res.is_admin
      userId.value = res.user_id || null
      username.value = res.username || ''
      loaded.value = true
      return res
    } catch (error) {
      console.warn('[permission] 获取用户权限失败:', error)
      // 失败时不清空，保留上次结果；标记未加载以便重试
      loaded.value = false
      return null
    }
  }

  /** 重置（登出时调用） */
  const reset = () => {
    permissions.value = []
    roles.value = []
    isAdmin.value = false
    userId.value = null
    username.value = ''
    loaded.value = false
  }

  return {
    permissions,
    roles,
    isAdmin,
    userId,
    username,
    loaded,
    hasPermission,
    hasAnyPermission,
    hasAllPermissions,
    fetchPermissions,
    reset,
  }
})
