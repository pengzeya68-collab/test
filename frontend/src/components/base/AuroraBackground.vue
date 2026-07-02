<template>
  <div class="aurora-bg" aria-hidden="true">
    <div class="aurora-blob blob-1"></div>
    <div class="aurora-blob blob-2"></div>
    <div class="aurora-blob blob-3"></div>
    <div class="aurora-blob blob-4"></div>
    <svg class="aurora-particles" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="xMidYMid slice">
      <g class="particles-group">
        <circle v-for="i in 24" :key="i" :cx="random(i, 100)" :cy="random(i + 50, 100)" :r="random(i + 100, 1, 3)" :class="`particle particle-${i}`" />
      </g>
    </svg>
    <div class="aurora-grid"></div>
  </div>
</template>

<script setup>
const random = (seed, max = 100, min = 0) => {
  const x = Math.sin(seed * 9999) * 10000
  const v = x - Math.floor(x)
  return (v * (max - min) + min).toFixed(2)
}
</script>

<style scoped lang="scss">
.aurora-bg {
  position: absolute;
  inset: 0;
  overflow: hidden;
  pointer-events: none;
  z-index: 0;
}

.aurora-blob {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.55;
  will-change: transform;
}

.blob-1 {
  width: 520px;
  height: 520px;
  top: -180px;
  left: -120px;
  background: radial-gradient(circle, var(--tm-color-primary), transparent 70%);
  animation: blob-float-1 18s ease-in-out infinite;
}

.blob-2 {
  width: 460px;
  height: 460px;
  bottom: -160px;
  right: -100px;
  background: radial-gradient(circle, var(--tm-color-primary-dark), transparent 70%);
  animation: blob-float-2 22s ease-in-out infinite;
}

.blob-3 {
  width: 380px;
  height: 380px;
  top: 40%;
  left: 55%;
  background: radial-gradient(circle, #00f2fe, transparent 70%);
  opacity: 0.35;
  animation: blob-float-3 26s ease-in-out infinite;
}

.blob-4 {
  width: 300px;
  height: 300px;
  top: 70%;
  left: 10%;
  background: radial-gradient(circle, #ec4899, transparent 70%);
  opacity: 0.3;
  animation: blob-float-4 20s ease-in-out infinite;
}

@keyframes blob-float-1 {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(60px, 80px) scale(1.1); }
  66% { transform: translate(-40px, 50px) scale(0.95); }
}
@keyframes blob-float-2 {
  0%, 100% { transform: translate(0, 0) scale(1); }
  50% { transform: translate(-80px, -60px) scale(1.15); }
}
@keyframes blob-float-3 {
  0%, 100% { transform: translate(0, 0) scale(1); }
  25% { transform: translate(-100px, 40px) scale(0.9); }
  75% { transform: translate(80px, -50px) scale(1.1); }
}
@keyframes blob-float-4 {
  0%, 100% { transform: translate(0, 0) scale(1); }
  50% { transform: translate(70px, -80px) scale(1.2); }
}

.aurora-particles {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}

.particle {
  fill: var(--tm-color-primary);
  opacity: 0;
  animation: particle-twinkle 4s ease-in-out infinite;
}

@for $i from 1 through 24 {
  .particle-#{$i} {
    animation-delay: #{$i * 0.18}s;
    animation-duration: #{3 + ($i % 4)}s;
  }
}

@keyframes particle-twinkle {
  0%, 100% { opacity: 0; }
  50% { opacity: 0.7; }
}

.aurora-grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(var(--tm-color-primary-rgb), 0.04) 1px, transparent 1px),
    linear-gradient(90deg, rgba(var(--tm-color-primary-rgb), 0.04) 1px, transparent 1px);
  background-size: 40px 40px;
  mask-image: radial-gradient(ellipse at center, black 30%, transparent 75%);
  -webkit-mask-image: radial-gradient(ellipse at center, black 30%, transparent 75%);
}

@media (prefers-reduced-motion: reduce) {
  .aurora-blob,
  .particle {
    animation: none !important;
  }
}

@media (max-width: 768px) {
  .aurora-blob {
    filter: blur(60px);
    opacity: 0.4;
  }
  .blob-1, .blob-2 { width: 320px; height: 320px; }
  .blob-3, .blob-4 { display: none; }
}
</style>
