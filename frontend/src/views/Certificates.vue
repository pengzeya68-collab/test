<template>
  <div class="certificates-page">
    <div class="container">
      <div class="page-header">
        <h1 class="page-title">🎓 技能证书</h1>
        <p class="page-desc">证明你的测试技能，解锁更多认证</p>
      </div>

      <div class="cert-stats">
        <div class="cert-stat">
          <span class="cert-stat-value">{{ certData.unlocked_count }}</span>
          <span class="cert-stat-label">已解锁</span>
        </div>
        <div class="cert-stat">
          <span class="cert-stat-value">{{ certData.total_count }}</span>
          <span class="cert-stat-label">总认证</span>
        </div>
        <div class="cert-progress-bar">
          <div class="cert-progress-fill" :style="{ width: (certData.unlocked_count / certData.total_count * 100) + '%' }"></div>
        </div>
      </div>

      <div class="cert-grid">
        <div
          v-for="cert in certData.certificates"
          :key="cert.key"
          class="cert-card"
          :class="{ unlocked: cert.unlocked, locked: !cert.unlocked }"
        >
          <div class="cert-icon">{{ cert.unlocked ? cert.icon : '🔒' }}</div>
          <div class="cert-body">
            <div class="cert-name">{{ cert.name }}</div>
            <div class="cert-level">
              <el-tag :type="getLevelType(cert.level)" size="small">{{ cert.level }}</el-tag>
            </div>
            <div class="cert-desc">{{ cert.description }}</div>
            <div class="cert-score-bar" v-if="!cert.unlocked">
              <div class="score-track">
                <div class="score-fill" :style="{ width: Math.min(cert.current_score / cert.required_score * 100, 100) + '%' }"></div>
              </div>
              <span class="score-text">{{ cert.current_score }}/{{ cert.required_score }}</span>
            </div>
          </div>
          <div class="cert-footer" v-if="cert.unlocked">
            <div class="cert-id">编号: {{ cert.cert_id }}</div>
            <div class="cert-date">{{ cert.issued_at }}</div>
          </div>
          <div class="cert-footer locked-footer" v-else>
            <span class="unlock-hint">技能分数达到 {{ cert.required_score }} 解锁</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import request from '@/utils/request'

const certData = ref({
  certificates: [],
  unlocked_count: 0,
  total_count: 0,
  username: '',
  overall_score: 0,
})

onMounted(() => {
  fetchCertificates()
})

const fetchCertificates = async () => {
  try {
    const res = await request.get('/certificates/')
    certData.value = res
  } catch (error) {
    console.error('获取证书失败:', error)
  }
}

const getLevelType = (level) => {
  const map = { '初级': 'success', '中级': 'warning', '高级': 'danger', '专家': '' }
  return map[level] || 'info'
}
</script>

<style scoped>
.certificates-page {
  padding: 40px 0;
  min-height: calc(100vh - 60px);
  background: #09090B;
}

.container {
  max-width: 1000px;
  margin: 0 auto;
  padding: 0 20px;
}

.page-header {
  margin-bottom: 30px;
}

.page-title {
  font-size: 32px;
  font-weight: 800;
  color: var(--tm-text-primary, #1e293b);
  margin: 0 0 8px;
}

.page-desc {
  font-size: 16px;
  color: var(--tm-text-secondary, #64748b);
  margin: 0;
}

.cert-stats {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 30px;
  padding: 20px 28px;
  background: var(--tm-bg-card, white);
  border-radius: 14px;
  border: 1px solid var(--tm-border-light, #e2e8f0);
}

.cert-stat {
  text-align: center;
}

.cert-stat-value {
  display: block;
  font-size: 28px;
  font-weight: 900;
  color: #8b5cf6;
}

.cert-stat-label {
  font-size: 13px;
  color: var(--tm-text-secondary);
}

.cert-progress-bar {
  flex: 1;
  height: 8px;
  border-radius: 4px;
  background: rgba(0, 0, 0, 0.04);
  overflow: hidden;
}

.cert-progress-fill {
  height: 100%;
  border-radius: 4px;
  background: linear-gradient(90deg, #8b5cf6, #d946ef);
  transition: width 0.5s ease;
}

.cert-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
}

.cert-card {
  padding: 24px;
  background: var(--tm-bg-card, white);
  border-radius: 14px;
  border: 2px solid var(--tm-border-light, #e2e8f0);
  transition: all 0.3s ease;
}

.cert-card.unlocked {
  border-color: rgba(139, 92, 246, 0.3);
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.03), rgba(217, 70, 239, 0.03));
}

.cert-card.unlocked:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(139, 92, 246, 0.15);
}

.cert-card.locked {
  opacity: 0.65;
}

.cert-icon {
  font-size: 40px;
  margin-bottom: 12px;
}

.cert-name {
  font-size: 18px;
  font-weight: 700;
  color: var(--tm-text-primary);
  margin-bottom: 6px;
}

.cert-level {
  margin-bottom: 8px;
}

.cert-desc {
  font-size: 13px;
  color: var(--tm-text-secondary);
  line-height: 1.6;
  margin-bottom: 12px;
}

.cert-score-bar {
  display: flex;
  align-items: center;
  gap: 10px;
}

.score-track {
  flex: 1;
  height: 6px;
  border-radius: 3px;
  background: rgba(0, 0, 0, 0.06);
  overflow: hidden;
}

.score-fill {
  height: 100%;
  border-radius: 3px;
  background: linear-gradient(90deg, #8b5cf6, #d946ef);
  transition: width 0.5s ease;
}

.score-text {
  font-size: 12px;
  color: var(--tm-text-secondary);
  font-variant-numeric: tabular-nums;
  min-width: 60px;
  text-align: right;
}

.cert-footer {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid rgba(139, 92, 246, 0.1);
  display: flex;
  justify-content: space-between;
}

.cert-id {
  font-size: 12px;
  color: #8b5cf6;
  font-family: monospace;
}

.cert-date {
  font-size: 12px;
  color: var(--tm-text-secondary);
}

.locked-footer {
  border-top: 1px solid var(--tm-border-light);
}

.unlock-hint {
  font-size: 12px;
  color: var(--tm-text-secondary);
}
</style>
