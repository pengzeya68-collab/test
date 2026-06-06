import DOMPurify from 'dompurify'

/**
 * 消毒 HTML 内容，防止 XSS 攻击
 * 允许安全的 HTML 标签和样式，移除脚本和事件处理器
 */
export function sanitizeHtml(html) {
  if (!html || typeof html !== 'string') return ''
  return DOMPurify.sanitize(html, {
    ALLOWED_TAGS: [
      'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
      'p', 'br', 'hr',
      'strong', 'em', 'u', 's', 'del', 'mark', 'sub', 'sup',
      'ul', 'ol', 'li',
      'table', 'thead', 'tbody', 'tr', 'th', 'td',
      'a', 'img',
      'blockquote', 'pre', 'code', 'span', 'div',
      'label',
      'details', 'summary',
    ],
    ALLOWED_ATTR: [
      'href', 'src', 'alt', 'title', 'class', 'id',
      'target', 'rel', 'type', 'checked', 'disabled',
      'colspan', 'rowspan', 'align', 'valign',
      'width', 'height',
    ],
    ALLOW_DATA_ATTR: false,
  })
}
