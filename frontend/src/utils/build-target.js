// The renderer build mode is the single source of truth. This prevents an
// inherited VITE_DESKTOP_BUILD variable from turning a web release into Electron.
export const isDesktopBuild = import.meta.env.MODE === 'desktop'
