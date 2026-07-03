// JMeter 树操作辅助函数 - 共享模块
// 提供 findNode/findParent/isDescendant/walkTree 等树遍历工具

import { reassignUids, resolveType, nodeTypeInfo } from './nodeTypes'

// 在树中按 uid 查找节点
export const findNode = (parent, uid) => {
  if (!parent || !uid) return null
  if (parent.uid === uid) return parent
  for (const child of parent.children || []) {
    const found = findNode(child, uid)
    if (found) return found
  }
  return null
}

// 查找节点的父节点及其在父 children 中的索引
export const findParent = (parent, uid) => {
  if (!parent || !uid) return null
  for (let i = 0; i < (parent.children || []).length; i++) {
    const child = parent.children[i]
    if (child.uid === uid) return { parent, index: i }
    const found = findParent(child, uid)
    if (found) return found
  }
  return null
}

// 检查 targetUid 是否为 node 的子孙节点(防止将节点移动到自己的子树下导致环)
export const isDescendant = (node, targetUid) => {
  if (!node || !targetUid) return false
  if (!Array.isArray(node.children)) return false
  for (const child of node.children) {
    if (child.uid === targetUid) return true
    if (isDescendant(child, targetUid)) return true
  }
  return false
}

// 深度优先遍历树
export const walkTree = (node, visitor, depth = 0, parent = null) => {
  if (!node) return
  visitor(node, depth, parent)
  if (Array.isArray(node.children)) {
    for (const child of node.children) {
      walkTree(child, visitor, depth + 1, node)
    }
  }
}

// 统计树中各类元素数量
export const countNodesByType = (root) => {
  const counts = {}
  walkTree(root, (n) => {
    const resolved = resolveType(n.type)
    counts[resolved] = (counts[resolved] || 0) + 1
  })
  return counts
}

// 统计树中各类别元素数量(sampler/assertion/extractor 等)
export const countNodesByCategory = (root) => {
  const counts = {}
  walkTree(root, (n) => {
    const info = nodeTypeInfo(n.type)
    const category = info?.category || 'other'
    counts[category] = (counts[category] || 0) + 1
  })
  return counts
}

// 深拷贝节点(含子树)并重新分配 UID
export const deepCopyWithNewUids = (node) => {
  const copy = JSON.parse(JSON.stringify(node))
  reassignUids(copy)
  return copy
}

// 默认导出:常用函数集合
export default {
  findNode,
  findParent,
  isDescendant,
  walkTree,
  countNodesByType,
  countNodesByCategory,
  deepCopyWithNewUids,
  reassignUids,
}
