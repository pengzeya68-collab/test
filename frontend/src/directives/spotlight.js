const spotlight = {
  mounted(el, binding) {
    if (typeof window === 'undefined') return
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return
    const enabled = binding.value !== false
    if (!enabled) return
    let rafId = null

    const onMove = (e) => {
      const rect = el.getBoundingClientRect()
      const x = ((e.clientX - rect.left) / rect.width) * 100
      const y = ((e.clientY - rect.top) / rect.height) * 100
      if (rafId) cancelAnimationFrame(rafId)
      rafId = requestAnimationFrame(() => {
        el.style.setProperty('--mx', `${x}%`)
        el.style.setProperty('--my', `${y}%`)
      })
    }
    const onLeave = () => {
      el.style.setProperty('--mx', '50%')
      el.style.setProperty('--my', '50%')
    }
    el._spotlight = { onMove, onLeave }
    el.classList.add('spotlight-host')
    el.addEventListener('mousemove', onMove)
    el.addEventListener('mouseleave', onLeave)
  },
  unmounted(el) {
    if (!el._spotlight) return
    el.removeEventListener('mousemove', el._spotlight.onMove)
    el.removeEventListener('mouseleave', el._spotlight.onLeave)
    delete el._spotlight
  }
}

export default spotlight
