/**
 * One-shot: replace common hardcoded palette colors with --tm-* tokens
 * so multi-skin switching works across the whole frontend.
 */
const fs = require('fs')
const path = require('path')

const ROOT = path.resolve(__dirname, '..')
const SRC = path.join(ROOT, 'src')

const SKIP = new Set([
  path.join(SRC, 'styles', 'global.css'),
  path.join(SRC, 'styles', 'variables.scss'),
  path.join(SRC, 'utils', 'ThemeConfig.js'),
])

function walk(dir, out = []) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, entry.name)
    if (entry.isDirectory()) {
      if (!['node_modules', 'dist'].includes(entry.name)) walk(p, out)
    } else if (/\.(vue|scss|css)$/.test(entry.name) && !entry.name.endsWith('.map')) {
      if (!SKIP.has(p)) out.push(p)
    }
  }
  return out
}

// Longer / more specific first
const REPLACEMENTS = [
  // Brand / primary
  [/#409eff/gi, 'var(--tm-color-primary)'],
  [/#3b82f6/gi, 'var(--tm-color-primary)'],
  [/#6366f1/gi, 'var(--tm-color-primary)'],
  [/#7c3aed/gi, 'var(--tm-color-primary)'],
  [/#8b5cf6/gi, 'var(--tm-color-primary)'],
  [/#a78bfa/gi, 'var(--tm-color-primary-light)'],
  [/#6d28d9/gi, 'var(--tm-color-primary-dark)'],
  [/#818cf8/gi, 'var(--tm-color-primary-light)'],
  [/#a5b4fc/gi, 'var(--tm-color-primary-light)'],
  [/#c084fc/gi, 'var(--tm-color-primary-light)'],
  [/#4f46e5/gi, 'var(--tm-color-primary-dark)'],
  [/#667eea/gi, 'var(--tm-color-primary)'],
  [/#764ba2/gi, 'var(--tm-color-primary-dark)'],

  // Success
  [/#67c23a/gi, 'var(--tm-color-success)'],
  [/#34d399/gi, 'var(--tm-color-success)'],
  [/#4ade80/gi, 'var(--tm-color-success)'],
  [/#16a34a/gi, 'var(--tm-color-success)'],
  [/#22c55e/gi, 'var(--tm-color-success)'],
  [/#10b981/gi, 'var(--tm-color-success)'],
  [/#059669/gi, 'var(--tm-color-success)'],
  [/#6ee7b7/gi, 'var(--tm-color-success)'],
  [/#84cc16/gi, 'var(--tm-color-success)'],
  [/#a6e3a1/gi, 'var(--tm-color-success)'],

  // Danger
  [/#f56c6c/gi, 'var(--tm-color-danger)'],
  [/#f87171/gi, 'var(--tm-color-danger)'],
  [/#ef4444/gi, 'var(--tm-color-danger)'],
  [/#dc2626/gi, 'var(--tm-color-danger)'],
  [/#ff4757/gi, 'var(--tm-color-danger)'],
  [/#f38ba8/gi, 'var(--tm-color-danger)'],

  // Warning
  [/#e6a23c/gi, 'var(--tm-color-warning)'],
  [/#fbbf24/gi, 'var(--tm-color-warning)'],
  [/#facc15/gi, 'var(--tm-color-warning)'],
  [/#f59e0b/gi, 'var(--tm-color-warning)'],
  [/#eab308/gi, 'var(--tm-color-warning)'],
  [/#d97706/gi, 'var(--tm-color-warning)'],
  [/#ffa502/gi, 'var(--tm-color-warning)'],
  [/#fcd34d/gi, 'var(--tm-color-warning)'],

  // Info / muted
  [/#909399/gi, 'var(--tm-color-info)'],
  [/#71717a/gi, 'var(--tm-text-muted)'],
  [/#94a3b8/gi, 'var(--tm-text-secondary)'],
  [/#64748b/gi, 'var(--tm-text-muted)'],
  [/#a1a1aa/gi, 'var(--tm-text-secondary)'],
  [/#52525b/gi, 'var(--tm-text-muted)'],
  [/#606266/gi, 'var(--tm-text-regular)'],
  [/#303133/gi, 'var(--tm-text-primary)'],
  [/#c0c4cc/gi, 'var(--tm-text-muted)'],
  [/#dcdfe6/gi, 'var(--tm-border-light)'],
  [/#e4e7ed/gi, 'var(--tm-border-light)'],
  [/#ebeef5/gi, 'var(--tm-border-light)'],
  [/#f5f7fa/gi, 'var(--tm-bg-elevated)'],
  [/#f0f2f5/gi, 'var(--tm-bg-page)'],
  [/#e0e0e0/gi, 'var(--tm-border-light)'],
  [/#d4d4d4/gi, 'var(--tm-border-light)'],

  // Surfaces
  [/#0b0f1a/gi, 'var(--tm-bg-page)'],
  [/#0a0f1c/gi, 'var(--tm-bg-page)'],
  [/#09090b/gi, 'var(--tm-bg-page)'],
  [/#1a1a2e/gi, 'var(--tm-bg-card-solid)'],
  [/#12121f/gi, 'var(--tm-bg-card-solid)'],
  [/#161e2e/gi, 'var(--tm-bg-card-solid)'],
  [/#1c2740/gi, 'var(--tm-bg-elevated)'],
  [/#27272a/gi, 'var(--tm-bg-elevated)'],
  [/#1e293b/gi, 'var(--tm-bg-elevated)'],
  [/#1e1e1e/gi, 'var(--tm-bg-elevated)'],
  [/#111827/gi, 'var(--tm-bg-card-solid)'],
  [/#0f172a/gi, 'var(--tm-bg-page)'],
  [/#18181b/gi, 'var(--tm-bg-card-solid)'],
  [/#181822/gi, 'var(--tm-bg-card-solid)'],

  // Text
  [/#f1f5f9/gi, 'var(--tm-text-primary)'],
  [/#f8fafc/gi, 'var(--tm-text-primary)'],
  [/#fafafa/gi, 'var(--tm-text-primary)'],
  [/#e2e8f0/gi, 'var(--tm-text-regular)'],
  [/#cbd5e1/gi, 'var(--tm-text-regular)'],
  [/#334155/gi, 'var(--tm-text-regular)'],

  // Cyan / pink accents
  [/#22d3ee/gi, 'var(--tm-neon-cyan)'],
  [/#00d9c0/gi, 'var(--tm-neon-cyan)'],
  [/#06b6d4/gi, 'var(--tm-neon-cyan)'],
  [/#0891b2/gi, 'var(--tm-neon-cyan)'],
  [/#60a5fa/gi, 'var(--tm-neon-cyan)'],
  [/#ec4899/gi, 'var(--tm-neon-pink)'],
  [/#d946ef/gi, 'var(--tm-neon-pink)'],

  // rgba brand patterns -> primary rgb token
  [/rgba\(\s*64\s*,\s*158\s*,\s*255\s*,/gi, 'rgba(var(--tm-color-primary-rgb),'],
  [/rgba\(\s*99\s*,\s*102\s*,\s*241\s*,/gi, 'rgba(var(--tm-color-primary-rgb),'],
  [/rgba\(\s*124\s*,\s*58\s*,\s*237\s*,/gi, 'rgba(var(--tm-color-primary-rgb),'],
  [/rgba\(\s*139\s*,\s*92\s*,\s*246\s*,/gi, 'rgba(var(--tm-color-primary-rgb),'],
  [/rgba\(\s*79\s*,\s*70\s*,\s*229\s*,/gi, 'rgba(var(--tm-color-primary-rgb),'],
  [/rgba\(\s*109\s*,\s*40\s*,\s*217\s*,/gi, 'rgba(var(--tm-color-primary-rgb),'],

  // rgba semantic -> color-mix (browser-safe)
  [/rgba\(\s*103\s*,\s*194\s*,\s*58\s*,\s*([0-9.]+)\s*\)/gi, 'color-mix(in srgb, var(--tm-color-success) $1pct, transparent)'],
  [/rgba\(\s*52\s*,\s*211\s*,\s*153\s*,\s*([0-9.]+)\s*\)/gi, 'color-mix(in srgb, var(--tm-color-success) $1pct, transparent)'],
  [/rgba\(\s*74\s*,\s*222\s*,\s*128\s*,\s*([0-9.]+)\s*\)/gi, 'color-mix(in srgb, var(--tm-color-success) $1pct, transparent)'],
  [/rgba\(\s*245\s*,\s*108\s*,\s*108\s*,\s*([0-9.]+)\s*\)/gi, 'color-mix(in srgb, var(--tm-color-danger) $1pct, transparent)'],
  [/rgba\(\s*248\s*,\s*113\s*,\s*113\s*,\s*([0-9.]+)\s*\)/gi, 'color-mix(in srgb, var(--tm-color-danger) $1pct, transparent)'],
  [/rgba\(\s*239\s*,\s*68\s*,\s*68\s*,\s*([0-9.]+)\s*\)/gi, 'color-mix(in srgb, var(--tm-color-danger) $1pct, transparent)'],
  [/rgba\(\s*230\s*,\s*162\s*,\s*60\s*,\s*([0-9.]+)\s*\)/gi, 'color-mix(in srgb, var(--tm-color-warning) $1pct, transparent)'],
  [/rgba\(\s*251\s*,\s*191\s*,\s*36\s*,\s*([0-9.]+)\s*\)/gi, 'color-mix(in srgb, var(--tm-color-warning) $1pct, transparent)'],
  [/rgba\(\s*250\s*,\s*204\s*,\s*21\s*,\s*([0-9.]+)\s*\)/gi, 'color-mix(in srgb, var(--tm-color-warning) $1pct, transparent)'],
  [/rgba\(\s*245\s*,\s*158\s*,\s*11\s*,\s*([0-9.]+)\s*\)/gi, 'color-mix(in srgb, var(--tm-color-warning) $1pct, transparent)'],
  [/rgba\(\s*34\s*,\s*211\s*,\s*238\s*,\s*([0-9.]+)\s*\)/gi, 'color-mix(in srgb, var(--tm-neon-cyan) $1pct, transparent)'],
  [/rgba\(\s*0\s*,\s*217\s*,\s*192\s*,\s*([0-9.]+)\s*\)/gi, 'color-mix(in srgb, var(--tm-neon-cyan) $1pct, transparent)'],
  [/rgba\(\s*236\s*,\s*72\s*,\s*153\s*,\s*([0-9.]+)\s*\)/gi, 'color-mix(in srgb, var(--tm-neon-pink) $1pct, transparent)'],
]

function fixPctPlaceholder(text) {
  // color-mix(... 0.15pct ...) -> color-mix(... 15% ...)
  return text.replace(
    /color-mix\(in srgb,\s*(var\(--[a-z0-9-]+\))\s+([0-9.]+)pct/gi,
    (_, v, a) => {
      const pct = Math.round(parseFloat(a) * 100)
      return `color-mix(in srgb, ${v} ${pct}%`
    }
  )
}

function main() {
  const files = walk(SRC)
  let changed = 0
  let totalHits = 0
  const report = []

  for (const file of files) {
    let text = fs.readFileSync(file, 'utf8')
    const orig = text
    let hits = 0

    for (const [re, to] of REPLACEMENTS) {
      const matches = text.match(re)
      if (matches) {
        hits += matches.length
        text = text.replace(re, to)
      }
    }
    text = fixPctPlaceholder(text)

    if (text !== orig) {
      fs.writeFileSync(file, text, 'utf8')
      changed++
      totalHits += hits
      report.push({ hits, file: path.relative(ROOT, file) })
    }
  }

  report.sort((a, b) => b.hits - a.hits)
  console.log(`changed files: ${changed}, approx hits: ${totalHits}`)
  report.slice(0, 30).forEach((r) => console.log(`${r.hits}\t${r.file}`))
}

main()
