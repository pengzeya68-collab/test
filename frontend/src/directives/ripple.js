const ripple = {
  mounted(el, binding) {
    if (typeof window === 'undefined') return
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return
    const color = (binding.value && binding.value.color) || 'rgba(255, 255, 255, 0.4)'

    const onClick = (e) => {
      const rect = el.getBoundingClientRect()
      const size = Math.max(rect.width, rect.height)
      const x = e.clientX - rect.left - size / 2
      const y = e.clientY - rect.top - size / 2
      const span = document.createElement('span')
      span.className = 'ripple-effect'
      span.style.width = span.style.height = `${size}px`
      span.style.left = `${x}px`
      span.style.top = `${y}px`
      span.style.background = color
      el.classList.add('ripple-host')
      el.appendChild(span)
      setTimeout(() => span.remove(), 600)
    }
    el._ripple = onClick
    el.addEventListener('click', onClick)
  },
  unmounted(el) {
    if (!el._ripple) return
    el.removeEventListener('click', el._ripple)
    delete el._ripple
  }
}

export default ripple
