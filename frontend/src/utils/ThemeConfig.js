/**
 * TestMaster 主题配置系统
 * 五套高颜值主题模板
 */

export const themes = [
  {
    id: 'sakura',
    name: '粉色樱落',
    description: '极致温柔，透光质感',
    primary: '#ffb7c5',
    primaryDark: '#ff8fa3',
    bg: "url('https://source.unsplash.com/featured/1920x1080/?sakura,pink,flower')",
    bgColor: 'rgba(255, 235, 240, 0.5)',
    cardBg: 'rgba(255, 255, 255, 0.7)',
    cardBorder: '1px solid rgba(255, 255, 255, 0.8)',
    textPrimary: '#2d2d2d',
    textSecondary: '#666666',
    sidebarBg: 'rgba(255, 240, 245, 0.85)',
    isDark: false
  },
  {
    id: 'cyberpunk',
    name: '赛博魅紫',
    description: '黑金底色搭配粉紫霓虹',
    primary: '#bd00ff',
    primaryDark: '#9d00cc',
    bg: "url('https://source.unsplash.com/featured/1920x1080/?cyberpunk,night,purple')",
    bgColor: 'rgba(10, 10, 20, 0.85)',
    cardBg: 'rgba(25, 25, 40, 0.7)',
    cardBorder: '1px solid rgba(189, 0, 255, 0.5)',
    textPrimary: '#e0e0e0',
    textSecondary: '#a0a0a0',
    sidebarBg: 'rgba(20, 10, 30, 0.9)',
    glow: '0 0 15px rgba(189, 0, 255, 0.5)',
    isDark: true
  },
  {
    id: 'mojito-green',
    name: '莫兰迪绿',
    description: '护眼、高级、治愈',
    primary: '#86a697',
    primaryDark: '#6d8a7f',
    bg: 'linear-gradient(135deg, #e8f5e9 0%, #dcedc8 100%)',
    bgColor: 'rgba(232, 245, 233, 0.6)',
    cardBg: 'rgba(255, 255, 255, 0.75)',
    cardBorder: '1px solid rgba(134, 166, 151, 0.3)',
    textPrimary: '#2d3d35',
    textSecondary: '#5a6a60',
    sidebarBg: 'rgba(240, 248, 240, 0.85)',
    isDark: false
  },
  {
    id: 'apple-light',
    name: '极简明亮',
    description: 'Apple 工业风，大留白',
    primary: '#007aff',
    primaryDark: '#0066cc',
    bg: '#f5f5f7',
    bgColor: 'transparent',
    cardBg: 'rgba(255, 255, 255, 0.8)',
    cardBorder: '1px solid rgba(0, 0, 0, 0.08)',
    textPrimary: '#1d1d1f',
    textSecondary: '#6e6e73',
    sidebarBg: 'rgba(255, 255, 255, 0.9)',
    isDark: false
  },
  {
    id: 'deep-ocean',
    name: '深邃之海',
    description: 'Vercel风格高级深色质感',
    primary: '#3b82f6',
    primaryDark: '#2563eb',
    bg: "url('https://source.unsplash.com/featured/1920x1080/?ocean,dark,blue')",
    bgColor: '#09090b',
    cardBg: '#141415',
    cardBorder: '1px solid rgba(255, 255, 255, 0.08)',
    textPrimary: '#fafafa',
    textSecondary: '#a1a1aa',
    sidebarBg: '#141415',
    glow: '0 0 15px rgba(59, 130, 246, 0.15)',
    isDark: true
  }
]

// 默认主题
export const defaultThemeId = 'cyberpunk'

// 从localStorage读取保存的主题
export function loadSavedTheme() {
  try {
    const saved = localStorage.getItem('testmaster-theme')
    if (saved) {
      return saved
    }
  } catch (e) {
    console.warn('Failed to load theme:', e)
  }
  return defaultThemeId
}

// 保存主题到localStorage
export function saveTheme(themeId) {
  try {
    localStorage.setItem('testmaster-theme', themeId)
  } catch (e) {
    console.warn('Failed to save theme:', e)
  }
}

// 十六进制颜色转 RGB 数值
function hexToRgb(hex) {
  // 移除 # 号
  hex = hex.replace('#', '')
  // 处理短格式
  if (hex.length === 3) {
    hex = hex[0] + hex[0] + hex[1] + hex[1] + hex[2] + hex[2]
  }
  const r = parseInt(hex.substring(0, 2), 16)
  const g = parseInt(hex.substring(2, 4), 16)
  const b = parseInt(hex.substring(4, 6), 16)
  return `${r}, ${g}, ${b}`
}

// 从 rgba 提取 RGB 数值
function rgbaToRgb(rgbaStr) {
  const match = rgbaStr.match(/rgba?\((\d+)\s*,\s*(\d+)\s*,\s*(\d+)/)
  return match ? `${match[1]}, ${match[2]}, ${match[3]}` : null
}

// 应用主题到document根节点 - 完整全局CSS变量池
export function applyTheme(themeId) {
  const theme = themes.find(t => t.id === themeId) || themes[0]

  const root = document.documentElement
  
  // 设置data-theme属性，用于CSS选择器
  root.setAttribute('data-theme', theme.id)

  // ========== 核心主题颜色变量 ==========
  // 主色调
  root.style.setProperty('--tm-primary-color', theme.primary)
  root.style.setProperty('--tm-primary-dark', theme.primaryDark || theme.primary)
  root.style.setProperty('--tm-color-primary', theme.primary)
  root.style.setProperty('--tm-color-primary-dark', theme.primaryDark || theme.primary)
  // 添加 RGB 版本用于透明混合
  if (theme.primary.startsWith('#')) {
    root.style.setProperty('--tm-color-primary-rgb', hexToRgb(theme.primary))
  }

  // 背景
  root.style.setProperty('--tm-bg-image', theme.bg)
  root.style.setProperty('--tm-bg-color', theme.bgColor)
  root.style.setProperty('--tm-bg-page', theme.bgColor)
  // 尝试提取 RGB 从 bgColor
  const bgRgb = rgbaToRgb(theme.bgColor)
  if (bgRgb) {
    root.style.setProperty('--tm-bg-page-rgb', bgRgb)
  }

  // 卡片
  root.style.setProperty('--tm-card-bg', theme.cardBg)
  root.style.setProperty('--tm-bg-card', theme.cardBg)
  root.style.setProperty('--tm-card-border', theme.cardBorder)
  root.style.setProperty('--tm-border-light', extractBorderColor(theme.cardBorder))

  // 文字
  root.style.setProperty('--tm-text-primary', theme.textPrimary)
  root.style.setProperty('--tm-text-secondary', theme.textSecondary)
  root.style.setProperty('--tm-text-regular', theme.textPrimary)
  root.style.setProperty('--tm-color-text-primary', theme.textPrimary)
  // 按钮文字颜色
  root.style.setProperty('--tm-button-text-color', theme.isDark ? '#ffffff' : '#333333')

  // 侧边栏
  root.style.setProperty('--tm-sidebar-bg', theme.sidebarBg)

  // 发光效果
  if (theme.glow) {
    root.style.setProperty('--tm-glow-effect', theme.glow)
    root.style.setProperty('--tm-shadow-base', theme.glow)
  } else {
    root.style.setProperty('--tm-glow-effect', 'none')
    root.style.setProperty('--tm-shadow-base', '0 2px 8px rgba(0, 0, 0, 0.15)')
  }

  // 边框颜色
  function extractBorderColor(borderStr) {
    // 从 '1px solid rgba(r,g,b,a)' 提取rgba
    const match = borderStr.match(/rgba?\([^)]+\)/)
    return match ? match[0] : 'rgba(120, 120, 120, 0.2)'
  }

  // ========== Vercel/Shadcn UI 高级深色质感系统 ==========
  // 根据主题类型（深色/浅色）设置新变量
  if (theme.isDark) {
    // 深色主题变量
    root.style.setProperty('--bg-base', '#09090b');
    root.style.setProperty('--bg-surface', '#141415');
    root.style.setProperty('--bg-surface-hover', '#27272a');
    root.style.setProperty('--bg-elevated', '#18181b');
    root.style.setProperty('--border-subtle', 'rgba(255, 255, 255, 0.08)');
    root.style.setProperty('--border-focus', 'rgba(255, 255, 255, 0.2)');
    root.style.setProperty('--text-primary', '#fafafa');
    root.style.setProperty('--text-secondary', '#a1a1aa');
    root.style.setProperty('--text-muted', '#52525b');
    root.style.setProperty('--accent-primary', theme.primary);
    root.style.setProperty('--accent-hover', theme.primaryDark || theme.primary);
    root.style.setProperty('--accent-glow', `rgba(${hexToRgb(theme.primary)}, 0.15)`);
  } else {
    // 浅色主题变量
    root.style.setProperty('--bg-base', '#ffffff');
    root.style.setProperty('--bg-surface', '#fafafa');
    root.style.setProperty('--bg-surface-hover', '#f0f0f0');
    root.style.setProperty('--bg-elevated', '#ffffff');
    root.style.setProperty('--border-subtle', 'rgba(0, 0, 0, 0.08)');
    root.style.setProperty('--border-focus', 'rgba(0, 0, 0, 0.2)');
    root.style.setProperty('--text-primary', '#18181b');
    root.style.setProperty('--text-secondary', '#52525b');
    root.style.setProperty('--text-muted', '#a1a1aa');
    root.style.setProperty('--accent-primary', theme.primary);
    root.style.setProperty('--accent-hover', theme.primaryDark || theme.primary);
    root.style.setProperty('--accent-glow', `rgba(${hexToRgb(theme.primary)}, 0.1)`);
  }

  // 圆角规范
  root.style.setProperty('--radius-sm', '4px');
  root.style.setProperty('--radius-md', '8px');
  root.style.setProperty('--radius-lg', '12px');

  // 保存
  saveTheme(themeId)

  return theme
}
