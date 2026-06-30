/**
 * 权限指令 v-permission
 *
 * 用法：
 *   v-permission="'case:create'"              // 拥有该权限才显示
 *   v-permission.any="['case:create','case:import']"  // 满足任一权限
 *   v-permission.all="['case:create','case:delete']"  // 需全部权限
 *
 * 无权限时元素将从 DOM 中移除（通过 parentNode.removeChild）。
 * 通配符 "*" 视为拥有全部权限（管理员）。
 */

import { usePermissionStore } from '@/stores/permission'

function evaluate(el, binding) {
  const store = usePermissionStore()
  let allowed = false

  if (binding.modifiers.any || (binding.arg && binding.arg === 'any')) {
    const codes = Array.isArray(binding.value) ? binding.value : [binding.value]
    allowed = store.hasAnyPermission(codes)
  } else if (binding.modifiers.all || (binding.arg && binding.arg === 'all')) {
    const codes = Array.isArray(binding.value) ? binding.value : [binding.value]
    allowed = store.hasAllPermissions(codes)
  } else {
    // 默认：单个权限码（字符串）
    allowed = store.hasPermission(binding.value)
  }

  if (!allowed) {
    el.parentNode && el.parentNode.removeChild(el)
  }
}

export const permissionDirective = {
  mounted(el, binding) {
    evaluate(el, binding)
  },
  // 支持权限动态更新后重新评估
  updated(el, binding) {
    // 元素可能已被移除，updated 仍会触发；若仍在 DOM 中则重新评估
    if (el.parentNode) {
      evaluate(el, binding)
    }
  },
}

export default permissionDirective
