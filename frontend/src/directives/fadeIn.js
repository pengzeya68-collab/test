const observers = new WeakMap()

const fadeIn = {
  mounted(el, binding) {
    if (typeof window === 'undefined' || !('IntersectionObserver' in window)) {
      el.classList.add('in-view')
      return
    }
    const delay = (binding.value && binding.value.delay) || 0
    const stagger = (binding.value && binding.value.stagger) || 0
    if (delay) el.style.transitionDelay = `${delay}ms`
    if (stagger) el.style.transitionDelay = `${stagger}ms`

    el.classList.add('stagger-in')
    const io = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          el.classList.add('in-view')
          io.unobserve(el)
        }
      })
    }, { threshold: 0.1, rootMargin: '0px 0px -50px 0px' })
    io.observe(el)
    observers.set(el, io)
  },
  unmounted(el) {
    const io = observers.get(el)
    if (io) {
      io.disconnect()
      observers.delete(el)
    }
  }
}

export default fadeIn
