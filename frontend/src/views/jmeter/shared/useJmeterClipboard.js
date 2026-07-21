// JMeter 剪贴板与跨节点操作 - 共享 composable
// 提供 moveNode/copyNodeTo/cutNode/pasteNode 等跨线程组操作
// 由 JmeterAssistant.vue 调用,内部使用 reassignUids/isValidParentChild 等共享工具

import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import {
  reassignUids,
  isValidParentChild,
  nodeTypeInfo,
} from './nodeTypes'
import {
  findNode,
  findParent,
  isDescendant,
  deepCopyWithNewUids,
} from './useJmeterTreeOps'

/**
 * JMeter 剪贴板与跨节点操作 composable
 *
 * @param {Ref<Object>} scriptTreeRef - 测试计划根节点的 ref
 * @param {Object} options - 配置项
 * @param {Function} options.onTreeChanged - 树变更回调(用于触发持久化等)
 * @returns {Object} - { clipboard, cutNode, copyNodeTo, pasteNode, moveNode, moveTo, toggleEnabled }
 */
export function useJmeterClipboard(scriptTreeRef, options = {}) {
  const { onTreeChanged } = options

  // 剪贴板状态:{ node, mode, originalUid }
  // mode: 'copy' | 'cut'
  const clipboard = ref({ node: null, mode: null, originalUid: null })

  // 触发树变更通知
  const notifyChanged = () => {
    if (typeof onTreeChanged === 'function') {
      onTreeChanged()
    }
  }

  // 校验移动/复制操作的合法性
  const validateMove = (sourceUid, targetParentUid) => {
    if (!sourceUid || !targetParentUid) {
      ElMessage.warning('参数缺失')
      return false
    }
    if (sourceUid === targetParentUid) {
      ElMessage.warning('不能将节点移动到自身下')
      return false
    }
    const tree = scriptTreeRef.value || scriptTreeRef
    const source = findNode(tree, sourceUid)
    if (!source) {
      ElMessage.warning('源节点不存在')
      return false
    }
    const targetParent = findNode(tree, targetParentUid)
    if (!targetParent) {
      ElMessage.warning('目标父节点不存在')
      return false
    }
    // 防止将节点移动到自己的子树下(会导致环)
    if (isDescendant(source, targetParentUid)) {
      ElMessage.warning('不能将节点移动到其子节点下')
      return false
    }
    // 校验父子关系合法性
    if (!isValidParentChild(targetParent.type, source.type)) {
      const sourceLabel = nodeTypeInfo(source.type)?.label || source.type
      const targetLabel = nodeTypeInfo(targetParent.type)?.label || targetParent.type
      ElMessage.warning(`${sourceLabel} 不能放在 ${targetLabel} 下`)
      return false
    }
    return true
  }

  /**
   * 移动节点到目标父节点
   * @param {string} uid - 被移动节点的 uid
   * @param {string} targetParentUid - 目标父节点 uid
   * @param {number} targetIndex - 插入位置,-1 表示末尾
   * @returns {boolean} 是否成功
   */
  const moveNode = (uid, targetParentUid, targetIndex = -1) => {
    if (!validateMove(uid, targetParentUid)) return false
    const tree = scriptTreeRef.value || scriptTreeRef
    const source = findNode(tree, uid)
    const targetParent = findNode(tree, targetParentUid)
    if (!targetParent.children) targetParent.children = []

    // 从原位置移除
    const pInfo = findParent(tree, uid)
    if (!pInfo) {
      ElMessage.warning('源节点父节点不存在')
      return false
    }
    pInfo.parent.children.splice(pInfo.index, 1)

    // 插入到目标位置
    const insertIndex = targetIndex < 0 || targetIndex > targetParent.children.length
      ? targetParent.children.length
      : targetIndex
    targetParent.children.splice(insertIndex, 0, source)

    notifyChanged()
    const sourceLabel = nodeTypeInfo(source.type)?.label || source.name
    const targetLabel = nodeTypeInfo(targetParent.type)?.label || targetParent.name
    ElMessage.success(`已移动 ${source.name}(${sourceLabel}) 到 ${targetLabel}`)
    return true
  }

  /**
   * 复制节点到目标父节点(保留原节点)
   * @param {string} uid - 被复制节点的 uid
   * @param {string} targetParentUid - 目标父节点 uid
   * @returns {boolean} 是否成功
   */
  const copyNodeTo = (uid, targetParentUid) => {
    if (!validateMove(uid, targetParentUid)) return false
    const tree = scriptTreeRef.value || scriptTreeRef
    const source = findNode(tree, uid)
    const targetParent = findNode(tree, targetParentUid)
    if (!targetParent.children) targetParent.children = []

    // 深拷贝并重新分配 UID
    const copy = deepCopyWithNewUids(source)
    targetParent.children.push(copy)

    notifyChanged()
    ElMessage.success(`已复制 ${source.name} 到 ${targetParent.name}`)
    return true
  }

  /**
   * 剪切节点(放入剪贴板,等待粘贴时移除)
   * @param {string} uid - 被剪切节点的 uid
   */
  const cutNode = (uid) => {
    const tree = scriptTreeRef.value || scriptTreeRef
    const source = findNode(tree, uid)
    if (!source) {
      ElMessage.warning('节点不存在')
      return
    }
    // 深拷贝到剪贴板(避免引用问题)
    const copy = JSON.parse(JSON.stringify(source))
    // 不重新分配 UID(粘贴时再分配,剪切模式下保持原 uid 用于移除)
    clipboard.value = { node: copy, mode: 'cut', originalUid: uid }
    ElMessage.success(`已剪切 ${source.name},请在目标位置粘贴`)
  }

  /**
   * 复制到剪贴板(原节点保留)
   * @param {string} uid - 被复制节点的 uid
   */
  const copyToClipboard = (uid) => {
    const tree = scriptTreeRef.value || scriptTreeRef
    const source = findNode(tree, uid)
    if (!source) {
      ElMessage.warning('节点不存在')
      return
    }
    const copy = JSON.parse(JSON.stringify(source))
    reassignUids(copy)
    clipboard.value = { node: copy, mode: 'copy', originalUid: null }
    ElMessage.success(`已复制 ${source.name} 到剪贴板,可在任意位置粘贴`)
  }

  /**
   * 粘贴剪贴板中的节点到目标父节点
   * @param {string} targetParentUid - 目标父节点 uid
   * @returns {boolean} 是否成功
   */
  const pasteNode = (targetParentUid) => {
    if (!clipboard.value.node) {
      ElMessage.warning('剪贴板为空')
      return false
    }
    const tree = scriptTreeRef.value || scriptTreeRef
    const targetParent = findNode(tree, targetParentUid)
    if (!targetParent) {
      ElMessage.warning('目标父节点不存在')
      return false
    }
    if (!isValidParentChild(targetParent.type, clipboard.value.node.type)) {
      const sourceLabel = nodeTypeInfo(clipboard.value.node.type)?.label || clipboard.value.node.type
      const targetLabel = nodeTypeInfo(targetParent.type)?.label || targetParent.type
      ElMessage.warning(`${sourceLabel} 不能放在 ${targetLabel} 下`)
      return false
    }
    if (!targetParent.children) targetParent.children = []

    // 深拷贝并重新分配 UID(每次粘贴都是新副本)
    const pasteCopy = deepCopyWithNewUids(clipboard.value.node)
    targetParent.children.push(pasteCopy)

    // 剪切模式:粘贴后从原位置移除原节点,并清空剪贴板
    if (clipboard.value.mode === 'cut' && clipboard.value.originalUid) {
      const pInfo = findParent(tree, clipboard.value.originalUid)
      if (pInfo) {
        pInfo.parent.children.splice(pInfo.index, 1)
      }
      clipboard.value = { node: null, mode: null, originalUid: null }
    }

    notifyChanged()
    ElMessage.success(`已粘贴到 ${targetParent.name}`)
    return true
  }

  /**
   * 切换节点启用/禁用状态
   * @param {string} uid - 节点 uid
   */
  const toggleEnabled = (uid) => {
    const tree = scriptTreeRef.value || scriptTreeRef
    const node = findNode(tree, uid)
    if (!node) return
    node.enabled = node.enabled === false
    notifyChanged()
    ElMessage.success(`${node.name} 已${node.enabled === false ? '禁用' : '启用'}`)
  }

  /**
   * 重排节点到目标位置(同父节点内重排,或跨父节点移动)
   * 用于响应 vuedraggable 的 change 事件
   * @param {string} movedUid - 被移动节点的 uid
   * @param {string} newParentUid - 新父节点 uid
   */
  const handleDragMove = (movedUid, newParentUid) => {
    const tree = scriptTreeRef.value || scriptTreeRef
    const targetParent = findNode(tree, newParentUid)
    if (!targetParent) return false
    const moved = findNode(tree, movedUid)
    if (!moved) return false

    // 校验父子关系合法性
    if (!isValidParentChild(targetParent.type, moved.type)) {
      const sourceLabel = nodeTypeInfo(moved.type)?.label || moved.type
      const targetLabel = nodeTypeInfo(targetParent.type)?.label || targetParent.type
      ElMessage.warning(`${sourceLabel} 不能放在 ${targetLabel} 下`)
      return false
    }
    notifyChanged()
    return true
  }

  return {
    clipboard,
    cutNode,
    copyToClipboard,
    copyNodeTo,
    pasteNode,
    moveNode,
    toggleEnabled,
    handleDragMove,
  }
}
