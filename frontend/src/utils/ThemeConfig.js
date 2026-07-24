/**
 * TestMaster 主题配置系统
 * 多皮肤可切换 · 登录页玻璃质感视觉语言 · 全站 --tm-* token
 */

export const themes = [
  {
    id: 'professional-dark',
    name: '专业深色',
    description: '深色玻璃质感，紫/靛蓝品牌色（默认）',
    primary: '#7C3AED',
    primaryDark: '#6D28D9',
    primaryLight: '#A78BFA',
    bg: 'radial-gradient(ellipse 80% 50% at 20% 0%, rgba(124, 58, 237, 0.18), transparent 55%), radial-gradient(ellipse 60% 40% at 100% 100%, rgba(6, 182, 212, 0.08), transparent 50%), #0B0F1A',
    bgColor: '#0B0F1A',
    bgPageRgb: '11, 15, 26',
    cardBg: 'rgba(22, 30, 46, 0.88)',
    cardSolid: '#161E2E',
    elevated: '#1C2740',
    hover: 'rgba(255, 255, 255, 0.04)',
    cardBorder: '1px solid rgba(124, 58, 237, 0.22)',
    textPrimary: '#F1F5F9',
    textRegular: '#CBD5E1',
    textSecondary: '#94A3B8',
    textMuted: '#64748B',
    sidebarBg: 'rgba(11, 15, 26, 0.94)',
    glow: '0 4px 24px rgba(124, 58, 237, 0.18)',
    accentCyan: '#22D3EE',
    isDark: true
  },
  {
    id: 'cyberpunk',
    name: '赛博魅紫',
    description: '黑金底色搭配粉紫霓虹',
    primary: '#BD00FF',
    primaryDark: '#9D00CC',
    primaryLight: '#E879F9',
    bg: 'radial-gradient(ellipse 70% 50% at 15% 10%, rgba(189, 0, 255, 0.22), transparent 55%), radial-gradient(ellipse 50% 40% at 90% 90%, rgba(236, 72, 153, 0.1), transparent 50%), #0A0A14',
    bgColor: '#0A0A14',
    bgPageRgb: '10, 10, 20',
    cardBg: 'rgba(25, 25, 40, 0.88)',
    cardSolid: '#191928',
    elevated: '#221F35',
    hover: 'rgba(189, 0, 255, 0.08)',
    cardBorder: '1px solid rgba(189, 0, 255, 0.45)',
    textPrimary: '#F5F3FF',
    textRegular: '#E0E0E0',
    textSecondary: '#A0A0B8',
    textMuted: '#71718A',
    sidebarBg: 'rgba(20, 10, 30, 0.94)',
    glow: '0 0 18px rgba(189, 0, 255, 0.45)',
    accentCyan: '#22D3EE',
    isDark: true
  },
  {
    id: 'deep-ocean',
    name: '深邃之海',
    description: '偏蓝专业深色，适合长时间工作',
    primary: '#3B82F6',
    primaryDark: '#2563EB',
    primaryLight: '#60A5FA',
    bg: 'radial-gradient(ellipse 70% 45% at 80% 0%, rgba(59, 130, 246, 0.16), transparent 55%), #09090B',
    bgColor: '#09090B',
    bgPageRgb: '9, 9, 11',
    cardBg: 'rgba(20, 20, 21, 0.92)',
    cardSolid: '#141415',
    elevated: '#1C1C1F',
    hover: 'rgba(255, 255, 255, 0.05)',
    cardBorder: '1px solid rgba(59, 130, 246, 0.22)',
    textPrimary: '#FAFAFA',
    textRegular: '#E4E4E7',
    textSecondary: '#A1A1AA',
    textMuted: '#71717A',
    sidebarBg: 'rgba(20, 20, 21, 0.96)',
    glow: '0 4px 20px rgba(59, 130, 246, 0.2)',
    accentCyan: '#22D3EE',
    isDark: true
  },
  {
    id: 'sakura',
    name: '粉色樱落',
    description: '温柔透光的浅色粉系',
    primary: '#DB2777',
    primaryDark: '#BE185D',
    primaryLight: '#F472B6',
    bg: 'radial-gradient(ellipse 70% 45% at 20% 0%, rgba(219, 39, 119, 0.16), transparent 55%), linear-gradient(160deg, #FFF1F5 0%, #FFE4E9 45%, #FFD6E0 100%)',
    bgColor: '#FFF1F5',
    bgPageRgb: '255, 241, 245',
    cardBg: 'rgba(255, 255, 255, 0.82)',
    cardSolid: '#FFFFFF',
    elevated: '#FFFFFF',
    hover: 'rgba(244, 114, 182, 0.08)',
    cardBorder: '1px solid rgba(244, 114, 182, 0.28)',
    textPrimary: '#2D2D2D',
    textRegular: '#4A4A4A',
    textSecondary: '#6B6B6B',
    textMuted: '#9A9A9A',
    sidebarBg: 'rgba(255, 240, 245, 0.94)',
    glow: '0 4px 20px rgba(244, 114, 182, 0.18)',
    accentCyan: '#0891B2',
    isDark: false
  },
  {
    id: 'mojito-green',
    name: '莫兰迪绿',
    description: '护眼高级的浅色绿系',
    primary: '#557A6C',
    primaryDark: '#3F5F53',
    primaryLight: '#6B9B88',
    bg: 'radial-gradient(ellipse 70% 45% at 15% 0%, rgba(85, 122, 108, 0.15), transparent 55%), linear-gradient(160deg, #F0F7F2 0%, #E8F5E9 50%, #DCEFD8 100%)',
    bgColor: '#F0F7F2',
    bgPageRgb: '240, 247, 242',
    cardBg: 'rgba(255, 255, 255, 0.84)',
    cardSolid: '#FFFFFF',
    elevated: '#FFFFFF',
    hover: 'rgba(107, 155, 136, 0.08)',
    cardBorder: '1px solid rgba(107, 155, 136, 0.28)',
    textPrimary: '#2D3D35',
    textRegular: '#3F5348',
    textSecondary: '#5A6A60',
    textMuted: '#84948A',
    sidebarBg: 'rgba(240, 248, 240, 0.95)',
    glow: '0 4px 18px rgba(107, 155, 136, 0.16)',
    accentCyan: '#0D9488',
    isDark: false
  },
  {
    id: 'apple-light',
    name: '极简明亮',
    description: '高留白浅色，克制蓝强调',
    primary: '#0066CC',
    primaryDark: '#004F9E',
    primaryLight: '#3385D6',
    bg: 'radial-gradient(ellipse 60% 40% at 50% 0%, rgba(0, 102, 204, 0.06), transparent 55%), #F5F5F7',
    bgColor: '#F5F5F7',
    bgPageRgb: '245, 245, 247',
    cardBg: 'rgba(255, 255, 255, 0.9)',
    cardSolid: '#FFFFFF',
    elevated: '#FFFFFF',
    hover: 'rgba(0, 0, 0, 0.04)',
    cardBorder: '1px solid rgba(0, 0, 0, 0.08)',
    textPrimary: '#1D1D1F',
    textRegular: '#3F3F46',
    textSecondary: '#6E6E73',
    textMuted: '#A1A1AA',
    sidebarBg: 'rgba(255, 255, 255, 0.96)',
    glow: '0 2px 14px rgba(0, 122, 255, 0.12)',
    accentCyan: '#0891B2',
    isDark: false
  },
  {
    id: 'professional-light',
    name: '专业浅色',
    description: '浅色工作台，保持品牌紫强调',
    primary: '#7C3AED',
    primaryDark: '#6D28D9',
    primaryLight: '#8B5CF6',
    bg: 'radial-gradient(ellipse 70% 40% at 20% 0%, rgba(124, 58, 237, 0.08), transparent 55%), #F4F6FB',
    bgColor: '#F4F6FB',
    bgPageRgb: '244, 246, 251',
    cardBg: '#FFFFFF',
    cardSolid: '#FFFFFF',
    elevated: '#FFFFFF',
    hover: 'rgba(15, 23, 42, 0.04)',
    cardBorder: '1px solid rgba(15, 23, 42, 0.08)',
    textPrimary: '#0F172A',
    textRegular: '#334155',
    textSecondary: '#64748B',
    textMuted: '#94A3B8',
    sidebarBg: 'rgba(255, 255, 255, 0.96)',
    glow: '0 4px 16px rgba(124, 58, 237, 0.12)',
    accentCyan: '#0891B2',
    isDark: false
  }
]

/** 旧主题 id 兼容 */
const THEME_ALIASES = {
  // 保留历史别名映射
}

export const defaultThemeId = 'professional-dark'

export function resolveThemeId(themeId) {
  if (!themeId) return defaultThemeId
  if (themes.some((t) => t.id === themeId)) return themeId
  return THEME_ALIASES[themeId] || defaultThemeId
}

export function loadSavedTheme() {
  try {
    const saved = localStorage.getItem('testmaster-theme')
    if (saved) return resolveThemeId(saved)
  } catch (e) {
    console.warn('Failed to load theme:', e)
  }
  return defaultThemeId
}

export function saveTheme(themeId) {
  try {
    localStorage.setItem('testmaster-theme', resolveThemeId(themeId))
  } catch (e) {
    console.warn('Failed to save theme:', e)
  }
}

function hexToRgb(hex) {
  if (!hex || !hex.startsWith('#')) return '124, 58, 237'
  let h = hex.replace('#', '')
  if (h.length === 3) h = h[0] + h[0] + h[1] + h[1] + h[2] + h[2]
  const r = parseInt(h.substring(0, 2), 16)
  const g = parseInt(h.substring(2, 4), 16)
  const b = parseInt(h.substring(4, 6), 16)
  return `${r}, ${g}, ${b}`
}

function extractBorderColor(borderStr) {
  const match = String(borderStr || '').match(/rgba?\([^)]+\)/)
  return match ? match[0] : 'rgba(124, 58, 237, 0.22)'
}

/**
 * 应用主题：写入完整 CSS 变量池（业务页应只读 var(--tm-*)）
 */
export function applyTheme(themeId) {
  const id = resolveThemeId(themeId)
  const theme = themes.find((t) => t.id === id) || themes[0]
  const root = document.documentElement
  const primaryRgb = hexToRgb(theme.primary)
  const borderColor = extractBorderColor(theme.cardBorder)
  const inputBackground = theme.isDark ? 'rgba(4, 8, 16, 0.42)' : theme.cardSolid
  const inputHoverBackground = theme.isDark ? 'rgba(4, 8, 16, 0.56)' : theme.elevated
  const overlayColor = theme.isDark ? 'rgba(0,0,0,0.55)' : 'rgba(15,23,42,0.35)'
  const primaryLight = (percentage) => `color-mix(in srgb, ${theme.primary} ${percentage}%, white)`

  root.setAttribute('data-theme', theme.id)
  root.setAttribute('data-color-scheme', theme.isDark ? 'dark' : 'light')
  root.style.colorScheme = theme.isDark ? 'dark' : 'light'

  // 品牌
  root.style.setProperty('--tm-primary-color', theme.primary)
  root.style.setProperty('--tm-primary-dark', theme.primaryDark || theme.primary)
  root.style.setProperty('--tm-color-primary', theme.primary)
  root.style.setProperty('--tm-color-primary-dark', theme.primaryDark || theme.primary)
  root.style.setProperty('--tm-color-primary-light', theme.primaryLight || theme.primary)
  root.style.setProperty('--tm-color-primary-rgb', primaryRgb)
  root.style.setProperty('--tm-color-secondary', theme.primaryLight || theme.primary)
  root.style.setProperty('--accent-primary', theme.primary)
  root.style.setProperty('--accent-hover', theme.primaryLight || theme.primary)
  root.style.setProperty('--accent-purple', theme.primaryDark || theme.primary)
  root.style.setProperty('--accent-glow', `rgba(${primaryRgb}, 0.18)`)
  root.style.setProperty('--accent-primary-rgb', primaryRgb)
  root.style.setProperty('--tm-gradient-brand', `linear-gradient(135deg, ${theme.primary}, ${theme.primaryDark || theme.primary})`)
  root.style.setProperty('--tm-gradient-brand-hover', `linear-gradient(135deg, ${theme.primaryLight || theme.primary}, ${theme.primary})`)
  root.style.setProperty('--tm-gradient-brand-glow', `0 4px 24px rgba(${primaryRgb}, 0.28)`)

  // 背景
  root.style.setProperty('--tm-bg-image', theme.bg)
  root.style.setProperty('--tm-bg-color', theme.bgColor)
  root.style.setProperty('--tm-bg-page', theme.bgColor)
  root.style.setProperty('--tm-bg-page-rgb', theme.bgPageRgb || (theme.isDark ? '11, 15, 26' : '244, 246, 251'))
  root.style.setProperty('--tm-bg-card', theme.cardBg)
  root.style.setProperty('--tm-card-bg', theme.cardBg)
  root.style.setProperty('--tm-bg-card-solid', theme.cardSolid || theme.cardBg)
  root.style.setProperty('--tm-bg-elevated', theme.elevated || theme.cardSolid)
  root.style.setProperty('--tm-bg-hover', theme.hover)
  root.style.setProperty('--bg-base', theme.bgColor)
  root.style.setProperty('--bg-surface', theme.cardSolid || theme.cardBg)
  root.style.setProperty('--bg-surface-hover', theme.hover || (theme.isDark ? 'rgba(255,255,255,0.05)' : 'rgba(15,23,42,0.04)'))
  root.style.setProperty('--bg-elevated', theme.elevated || theme.cardSolid)

  // 边框 / 玻璃
  root.style.setProperty('--tm-card-border', theme.cardBorder)
  root.style.setProperty('--tm-border-light', borderColor)
  root.style.setProperty('--tm-border-color', borderColor)
  root.style.setProperty('--tm-border-focus', `rgba(${primaryRgb}, 0.55)`)
  root.style.setProperty('--border-subtle', theme.isDark ? 'rgba(255,255,255,0.08)' : 'rgba(15,23,42,0.08)')
  root.style.setProperty('--border-focus', `rgba(${primaryRgb}, 0.5)`)
  root.style.setProperty('--border-neon', `1px solid ${theme.isDark ? 'rgba(255,255,255,0.08)' : 'rgba(15,23,42,0.08)'}`)
  root.style.setProperty('--tm-glass-bg', theme.isDark ? 'rgba(22, 30, 46, 0.82)' : 'rgba(255,255,255,0.88)')
  root.style.setProperty('--tm-glass-border', `1px solid ${borderColor}`)
  root.style.setProperty('--tm-glass-blur', 'blur(18px)')

  // 文字
  root.style.setProperty('--tm-text-primary', theme.textPrimary)
  root.style.setProperty('--tm-text-regular', theme.textRegular || theme.textPrimary)
  root.style.setProperty('--tm-text-secondary', theme.textSecondary)
  root.style.setProperty('--tm-text-muted', theme.textMuted || theme.textSecondary)
  root.style.setProperty('--tm-color-text-primary', theme.textPrimary)
  root.style.setProperty('--text-primary', theme.textPrimary)
  root.style.setProperty('--text-secondary', theme.textRegular || theme.textSecondary)
  root.style.setProperty('--text-muted', theme.textSecondary)
  root.style.setProperty('--tm-button-text-color', '#FFFFFF')
  root.style.setProperty('--tm-on-warning', '#1F2937')
  root.style.setProperty('--tm-input-bg', inputBackground)
  root.style.setProperty('--tm-input-bg-hover', inputHoverBackground)
  root.style.setProperty('--tm-input-border', borderColor)
  root.style.setProperty('--tm-input-text', theme.textPrimary)
  root.style.setProperty('--tm-input-placeholder', theme.textMuted || theme.textSecondary)

  // 侧栏 / 阴影
  root.style.setProperty('--tm-sidebar-bg', theme.sidebarBg)
  root.style.setProperty('--tm-glow-effect', theme.glow || 'none')
  root.style.setProperty('--tm-shadow-base', theme.isDark ? '0 4px 16px rgba(0,0,0,0.35)' : '0 2px 12px rgba(15,23,42,0.08)')
  root.style.setProperty('--tm-shadow-card', theme.isDark ? '0 8px 32px rgba(0,0,0,0.4)' : '0 4px 20px rgba(15,23,42,0.08)')
  root.style.setProperty('--tm-shadow-hover', theme.isDark ? '0 12px 36px rgba(0,0,0,0.45)' : '0 8px 28px rgba(15,23,42,0.12)')
  root.style.setProperty('--tm-shadow-glow', `0 0 24px rgba(${primaryRgb}, 0.2)`)

  // 语义色（深浅均可读）
  root.style.setProperty('--tm-color-success', theme.isDark ? '#4ADE80' : '#16A34A')
  root.style.setProperty('--tm-color-warning', theme.isDark ? '#FACC15' : '#CA8A04')
  root.style.setProperty('--tm-color-danger', theme.isDark ? '#F87171' : '#DC2626')
  root.style.setProperty('--tm-color-info', theme.isDark ? '#94A3B8' : '#64748B')
  root.style.setProperty('--tm-neon-cyan', theme.accentCyan || '#22D3EE')
  root.style.setProperty('--tm-neon-purple', theme.primaryDark || theme.primary)
  root.style.setProperty('--tm-neon-green', theme.isDark ? '#4ADE80' : '#16A34A')
  root.style.setProperty('--tm-neon-yellow', theme.isDark ? '#FACC15' : '#CA8A04')
  root.style.setProperty('--tm-neon-pink', theme.primaryLight || theme.primary)

  // 滚动条（随皮肤）
  root.style.setProperty(
    '--tm-scrollbar-thumb',
    theme.isDark ? 'rgba(255, 255, 255, 0.14)' : 'rgba(15, 23, 42, 0.18)'
  )
  root.style.setProperty('--tm-scrollbar-thumb-hover', `rgba(${primaryRgb}, 0.5)`)

  // 布局 token
  root.style.setProperty('--tm-radius-base', '12px')
  root.style.setProperty('--tm-radius-small', '8px')
  root.style.setProperty('--radius-sm', '6px')
  root.style.setProperty('--radius-md', '10px')
  root.style.setProperty('--radius-lg', '14px')
  root.style.setProperty('--tm-navbar-height', '60px')
  root.style.setProperty('--tm-sidebar-width', '240px')
  root.style.setProperty('--tm-sidebar-collapsed-width', '68px')
  root.style.setProperty('--tm-control-height', '36px')
  root.style.setProperty('--tm-control-height-lg', '44px')
  root.style.setProperty('--tm-page-max-width', '1440px')
  root.style.setProperty('--tm-space-xs', '4px')
  root.style.setProperty('--tm-space-sm', '8px')
  root.style.setProperty('--tm-space-md', '16px')
  root.style.setProperty('--tm-space-lg', '24px')
  root.style.setProperty('--tm-space-xl', '32px')
  root.style.setProperty('--tm-table-row-height', '48px')
  root.style.setProperty('--tm-font-xs', '11px')
  root.style.setProperty('--tm-font-sm', '12px')
  root.style.setProperty('--tm-font-md', '14px')
  root.style.setProperty('--tm-font-lg', '16px')
  root.style.setProperty('--tm-font-xl', '20px')
  root.style.setProperty('--tm-font-2xl', '28px')

  // Element Plus 桥接
  root.style.setProperty('--el-color-primary', theme.primary)
  root.style.setProperty('--el-color-primary-light-3', theme.primaryLight || theme.primary)
  root.style.setProperty('--el-color-primary-light-5', primaryLight(50))
  root.style.setProperty('--el-color-primary-light-7', primaryLight(30))
  root.style.setProperty('--el-color-primary-light-8', primaryLight(20))
  root.style.setProperty('--el-color-primary-light-9', primaryLight(10))
  root.style.setProperty('--el-color-primary-dark-2', theme.primaryDark || theme.primary)
  root.style.setProperty('--el-color-success', theme.isDark ? '#4ADE80' : '#16A34A')
  root.style.setProperty('--el-color-warning', theme.isDark ? '#FACC15' : '#CA8A04')
  root.style.setProperty('--el-color-danger', theme.isDark ? '#F87171' : '#DC2626')
  root.style.setProperty('--el-color-info', theme.isDark ? '#94A3B8' : '#64748B')
  root.style.setProperty('--el-bg-color', theme.cardSolid || theme.bgColor)
  root.style.setProperty('--el-bg-color-page', theme.bgColor)
  root.style.setProperty('--el-bg-color-overlay', theme.elevated || theme.cardSolid)
  root.style.setProperty('--el-text-color-primary', theme.textPrimary)
  root.style.setProperty('--el-text-color-regular', theme.textRegular || theme.textPrimary)
  root.style.setProperty('--el-text-color-secondary', theme.textSecondary)
  root.style.setProperty('--el-text-color-placeholder', theme.textMuted || theme.textSecondary)
  root.style.setProperty('--el-border-color', borderColor)
  root.style.setProperty('--el-border-color-light', theme.isDark ? 'rgba(255,255,255,0.08)' : 'rgba(15,23,42,0.08)')
  root.style.setProperty('--el-border-color-lighter', theme.isDark ? 'rgba(255,255,255,0.05)' : 'rgba(15,23,42,0.06)')
  root.style.setProperty('--el-border-color-extra-light', theme.isDark ? 'rgba(255,255,255,0.03)' : 'rgba(15,23,42,0.04)')
  root.style.setProperty('--el-fill-color', theme.hover)
  root.style.setProperty('--el-fill-color-light', theme.hover)
  root.style.setProperty('--el-fill-color-lighter', theme.isDark ? 'rgba(255,255,255,0.03)' : 'rgba(15,23,42,0.025)')
  root.style.setProperty('--el-fill-color-dark', theme.isDark ? 'rgba(0,0,0,0.22)' : 'rgba(15,23,42,0.08)')
  root.style.setProperty('--el-fill-color-blank', theme.elevated || theme.cardSolid)
  root.style.setProperty('--el-disabled-bg-color', theme.isDark ? 'rgba(255,255,255,0.06)' : 'rgba(15,23,42,0.06)')
  root.style.setProperty('--el-disabled-text-color', theme.textMuted || theme.textSecondary)
  root.style.setProperty('--el-mask-color', overlayColor)

  saveTheme(theme.id)
  return theme
}
