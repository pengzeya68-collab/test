const seen = new WeakSet()

const easeOutQuart = (t) => 1 - Math.pow(1 - t, 4)

const animateNumber = (el, target, duration = 1500) => {
  if (typeof window === 'undefined' || seen.has(el)) {
    el.textContent = formatNumber(target, el)
    return
  }
  seen.add(el)
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    el.textContent = formatNumber(target, el)
    return
  }
  const start = performance.now()
  const startValue = 0

  const tick = (now) => {
    const elapsed = now - start
    const progress = Math.min(elapsed / duration, 1)
    const eased = easeOutQuart(progress)
    const current = Math.round(startValue + (target - startValue) * eased)
    el.textContent = formatNumber(current, el)
    if (progress < 1) {
      requestAnimationFrame(tick)
    } else {
      el.textContent = formatNumber(target, el)
    }
  }
  requestAnimationFrame(tick)
}

const formatNumber = (n, el) => {
  const suffix = el.dataset.suffix || ''
  const prefix = el.dataset.prefix || ''
  if (typeof n === 'string' && isNaN(Number(n))) return n
  const num = Number(n)
  if (num >= 1000) {
    return prefix + num.toLocaleString('en-US') + suffix
  }
  return prefix + num + suffix
}

const countUp = {
  mounted(el, binding) {
    const target = binding.value !== undefined ? binding.value : parseFloat(el.textContent)
    if (isNaN(Number(target))) return
    el.classList.add('count-up')
    if (!('IntersectionObserver' in window)) {
      animateNumber(el, Number(target))
      return
    }
    const io = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          animateNumber(el, Number(target))
          io.unobserve(el)
        }
      })
    }, { threshold: 0.5 })
    io.observe(el)
    el._countUpObserver = io
  },
  unmounted(el) {
    if (el._countUpObserver) {
      el._countUpObserver.disconnect()
      delete el._countUpObserver
    }
  }
}

export default countUp
