/**
 * 从接口响应生成断言建议
 *
 * 输入: { status, time, headers, body }
 *   - status: HTTP 状态码 (number)
 *   - time:   响应耗时 (ms, number)
 *   - headers: 响应头对象 (Record<string, string>)
 *   - body:    已解析的响应体对象 (object | null)
 *
 * 输出: Array<{
 *   target: 'status_code' | 'response_body' | 'response_header' | 'response_time',
 *   operator: string,
 *   expected: string,
 *   expression: string,
 *   label: string,
 *   checked: boolean
 * }>
 *
 * 断言引擎已支持的 operator:
 *   ==/!=/contains/not_contains/</>/<=/>=/range/regex/not_empty/empty/exists/not_exists
 */

const COMMON_FIELDS = ['code', 'message', 'msg', 'data', 'success', 'total', 'list', 'id', 'result']
const MAX_TOP_FIELDS = 8
const MAX_NESTED_FIELDS = 5

function isObject(v) {
  return v !== null && typeof v === 'object' && !Array.isArray(v)
}

function findHeader(headers, name) {
  if (!headers) return undefined
  // 直接命中
  if (headers[name] !== undefined) return headers[name]
  // 大小写不敏感查找
  const lower = String(name).toLowerCase()
  for (const k of Object.keys(headers)) {
    if (String(k).toLowerCase() === lower) return headers[k]
  }
  return undefined
}

function ceilTo(n, step) {
  return Math.ceil(n / step) * step
}

/**
 * 为单个字段生成断言建议
 */
function buildFieldAssertions(field, value, parentPath = '') {
  const suggestions = []
  const expr = parentPath ? `$.${parentPath}.${field}` : `$.${field}`
  const labelPrefix = parentPath ? `${parentPath}.${field}` : field

  if (value === null || value === undefined) {
    suggestions.push({
      target: 'response_body',
      operator: 'exists',
      expected: '',
      expression: expr,
      label: `字段 ${labelPrefix} 存在`,
      checked: true,
    })
    return suggestions
  }

  if (Array.isArray(value)) {
    suggestions.push({
      target: 'response_body',
      operator: 'exists',
      expected: '',
      expression: expr,
      label: `字段 ${labelPrefix} 存在`,
      checked: true,
    })
    suggestions.push({
      target: 'response_body',
      operator: 'not_empty',
      expected: '',
      expression: expr,
      label: `列表 ${labelPrefix} 非空`,
      checked: value.length > 0,
    })
    return suggestions
  }

  if (isObject(value)) {
    suggestions.push({
      target: 'response_body',
      operator: 'exists',
      expected: '',
      expression: expr,
      label: `字段 ${labelPrefix} 存在`,
      checked: true,
    })
    return suggestions
  }

  // 基础类型: string / number / boolean
  let expected = ''
  if (typeof value === 'string') {
    expected = value.length > 50 ? value.slice(0, 50) + '...' : value
  } else if (typeof value === 'boolean') {
    expected = String(value)
  } else {
    expected = String(value)
  }
  suggestions.push({
    target: 'response_body',
    operator: '==',
    expected,
    expression: expr,
    label: `${labelPrefix} == ${expected}`,
    checked: typeof value !== 'string' || value.length <= 30,
  })
  return suggestions
}

/**
 * 主函数：从响应生成断言建议
 */
export function generateAssertionsFromResponse({ status, time, headers, body } = {}) {
  const suggestions = []

  // 1. 状态码断言
  if (status !== undefined && status !== null && status > 0) {
    suggestions.push({
      target: 'status_code',
      operator: '==',
      expected: String(status),
      expression: '',
      label: `状态码等于 ${status}`,
      checked: true,
    })
  }

  // 2. 响应时间断言（向上取整到 100ms 倍数）
  if (time !== undefined && time !== null && time > 0) {
    const threshold = Math.max(ceilTo(time, 100), 100)
    suggestions.push({
      target: 'response_time',
      operator: '<',
      expected: String(threshold),
      expression: '',
      label: `响应时间 < ${threshold}ms`,
      checked: true,
    })
  }

  // 3. Content-Type 响应头断言
  const ct = findHeader(headers, 'Content-Type')
  if (ct && String(ct).includes('application/json')) {
    suggestions.push({
      target: 'response_header',
      operator: 'contains',
      expected: 'application/json',
      expression: 'Content-Type',
      label: '响应头 Content-Type 包含 application/json',
      checked: true,
    })
  }

  // 4. 遍历 body 字段
  if (!isObject(body)) {
    return suggestions
  }

  const entries = Object.entries(body)
  // 常见字段优先
  const sorted = entries.sort((a, b) => {
    const ai = COMMON_FIELDS.indexOf(a[0])
    const bi = COMMON_FIELDS.indexOf(b[0])
    if (ai !== -1 && bi !== -1) return ai - bi
    if (ai !== -1) return -1
    if (bi !== -1) return 1
    return 0
  })

  let count = 0
  for (const [field, value] of sorted) {
    if (count >= MAX_TOP_FIELDS) break
    count++
    // 顶层字段断言
    const fieldSuggestions = buildFieldAssertions(field, value)
    for (const s of fieldSuggestions) {
      suggestions.push(s)
    }
    // 对象字段递归一层
    if (isObject(value) && field !== 'data') {
      let nestedCount = 0
      for (const [subField, subValue] of Object.entries(value)) {
        if (nestedCount >= MAX_NESTED_FIELDS) break
        nestedCount++
        const nested = buildFieldAssertions(subField, subValue, field)
        for (const s of nested) {
          suggestions.push(s)
        }
      }
    }
  }

  return suggestions
}

/**
 * 将建议列表转换为前端用例断言结构
 * 输入建议: { target, operator, expected, expression, checked }
 * 输出断言: { id, target, operator, expected, expression }
 */
export function suggestionsToAssertions(suggestions) {
  return (suggestions || [])
    .filter(s => s.checked)
    .map(s => ({
      target: s.target,
      operator: s.operator,
      expected: String(s.expected ?? ''),
      expression: s.expression || '',
    }))
}

/**
 * 将前端断言结构转换为后端模板 rules 结构
 * 输入断言: { target, operator, expected, expression }
 * 输出规则: { type, operator, expected, expression }
 */
export function assertionsToRules(assertions) {
  return (assertions || []).map(a => ({
    type: a.target,
    operator: a.operator,
    expected: String(a.expected ?? ''),
    expression: a.expression || '',
  }))
}
