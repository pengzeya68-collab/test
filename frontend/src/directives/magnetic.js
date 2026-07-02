const magnetic = {
  mounted(el, binding) {
    if (typeof window === 'undefined') return
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return
    const strength = (binding.value && binding.value.strength) || 0.3
    let rafId = null

    const onMove = (e) => {
      const rect = el.getBoundingClientRect()
      const x = e.clientX - (rect.left + rect.width / 2)
      const y = e.clientY - (rect.top + rect.height / 2)
      if (rafId) cancelAnimationFrame(rafId)
      rafId = requestAnimationFrame(() => {
        el.style.transform = `translate3d(${x * strength}px, ${y * strength}px, 0)`
      })
    }
    const onLeave = () => {
      if (rafId) cancelAnimationFrame(rafId)
      el.style.transform = ''
    }
    el._magnetic = { onMove, onLeave }
    el.classList.add('magnetic-host')
    el.addEventListener('mousemove', onMove)
    el.addEventListener('mouseleave', onLeave)
  },
  unmounted(el) {
    if (!el._magnetic) return
    el.removeEventListener('mousemove', el._magnetic.onMove)
    el.removeEventListener('mouseleave', el._magnetic.onLeave)
    delete el._magnetic
  }
}

export default magnetic
