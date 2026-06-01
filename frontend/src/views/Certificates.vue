<template>
  <div class="certificates-page">
    <header class="page-header">
      <div class="header-titles">
        <h1 class="page-title">🎓 技能证书</h1>
        <p class="page-desc">证明你的测试技能，解锁更多认证</p>
      </div>
    </header>

    <div class="cert-stats">
      <div class="cert-stat">
        <div class="cert-stat-value unlocked-val">{{ certData.unlocked_count }}</div>
        <div class="cert-stat-label">已解锁</div>
      </div>
      <div class="cert-stat-separator">
        <span>/</span>
      </div>
      <div class="cert-stat">
        <div class="cert-stat-value total-val">{{ certData.total_count }}</div>
        <div class="cert-stat-label">总认证</div>
      </div>
      <div class="cert-progress-bar">
        <div class="cert-progress-fill" :style="{ width: (certData.unlocked_count / (certData.total_count || 1) * 100) + '%' }"></div>
      </div>
      <span class="cert-progress-label">{{ Math.round(certData.unlocked_count / (certData.total_count || 1) * 100) }}%</span>
    </div>

    <div class="section-header">
      <h2 class="section-title">
        <span class="title-dot">◈</span>
        认证列表
      </h2>
      <div class="title-glow-line"></div>
    </div>

    <div class="cert-grid">
      <div
        v-for="cert in certData.certificates"
        :key="cert.key"
        class="cert-card"
        :class="{ unlocked: cert.unlocked, locked: !cert.unlocked }"
      >
        <div class="cert-card-top">
          <div class="cert-icon-wrap">
            <span class="cert-icon">{{ cert.unlocked ? cert.icon : '🔒' }}</span>
          </div>
          <div class="cert-badges">
            <span class="cert-level-tag" :class="'lv-' + getLevelClass(cert.level)">{{ cert.level }}</span>
            <span class="cert-status-tag" v-if="cert.unlocked">已认证</span>
            <span class="cert-status-tag locked-tag" v-else>未解锁</span>
          </div>
        </div>

        <div class="cert-body">
          <h3 class="cert-name">{{ cert.name }}</h3>
          <p class="cert-desc">{{ cert.description }}</p>
        </div>

        <div class="cert-score-bar" v-if="!cert.unlocked">
          <div class="score-track">
            <div class="score-fill" :style="{ width: Math.min(cert.current_score / cert.required_score * 100, 100) + '%' }"></div>
          </div>
          <span class="score-text">{{ cert.current_score }}<span class="score-divider">/</span>{{ cert.required_score }}</span>
        </div>

        <div class="cert-footer" v-if="cert.unlocked">
          <span class="cert-id">#{{ cert.cert_id }}</span>
          <span class="cert-date">{{ cert.issued_at }}</span>
        </div>
        <div class="cert-footer locked-footer" v-else>
          <span class="unlock-hint">🔒 技能分数达到 {{ cert.required_score }} 解锁</span>
        </div>
      </div>
    </div>

    <div class="empty-state" v-if="!certData.certificates?.length">
      <div class="empty-icon">📭</div>
      <p class="empty-text">暂无认证数据</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
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
    ElMessage.error('获取证书失败，请稍后重试')
  }
}

const getLevelClass = (level) => {
  const map = { '初级': 'beginner', '中级': 'medium', '高级': 'advanced', '专家': 'expert' }
  return map[level] || 'medium'
}
</script>

<style scoped>
.certificates-page {
  width: 100%;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  padding: 40px 60px;
  box-sizing: border-box;
  background-color: var(--tm-bg-page);
  color: var(--tm-text-primary);
  gap: 28px;
}

.page-header {
  padding-bottom: 20px;
  border-bottom: 1px solid #27272a;
}
.header-titles {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.page-title {
  font-size: 28px;
  font-weight: 800;
  color: var(--tm-text-primary);
  margin: 0;
}
.page-desc {
  font-size: 14px;
  color: var(--tm-text-regular);
  margin: 0;
}

/* Stats Bar */
.cert-stats {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 22px 30px;
  background: var(--tm-card-bg);
  border: 1px solid var(--tm-border-light);
  border-radius: 14px;
}
.cert-stat {
  text-align: center;
  flex-shrink: 0;
}
.cert-stat-value {
  font-size: 34px;
  font-weight: 900;
  line-height: 1;
}
.unlocked-val {
  background: linear-gradient(135deg, var(--tm-color-primary), var(--tm-color-primary-dark));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
.total-val { color: var(--tm-text-regular); }
.cert-stat-label {
  font-size: 12px;
  color: var(--tm-text-secondary);
  margin-top: 4px;
}
.cert-stat-separator {
  font-size: 28px;
  color: var(--tm-text-secondary);
  font-weight: 300;
}
.cert-progress-bar {
  flex: 1;
  height: 8px;
  border-radius: 4px;
  background: var(--tm-border-light);
  overflow: hidden;
}
.cert-progress-fill {
  height: 100%;
  border-radius: 4px;
  background: linear-gradient(90deg, var(--tm-color-primary), var(--tm-color-primary-dark));
  transition: width 0.8s ease;
}
.cert-progress-label {
  font-size: 14px;
  font-weight: 700;
  color: var(--tm-color-primary);
  min-width: 40px;
  text-align: right;
}

/* Section Header */
.section-header {
  margin-bottom: 4px;
}
.section-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--tm-text-primary);
  margin: 0 0 8px 0;
  display: flex;
  align-items: center;
  gap: 8px;
}
.title-dot {
  color: var(--tm-color-primary);
  font-size: 12px;
  text-shadow: 0 0 8px rgba(var(--tm-color-primary-rgb), 0.4);
}
.title-glow-line {
  width: 36px;
  height: 2px;
  background: linear-gradient(90deg, var(--tm-color-primary), var(--tm-color-primary-dark));
  border-radius: 1px;
}

/* Cert Grid */
.cert-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 20px;
}

/* Cert Card */
.cert-card {
  padding: 26px;
  background: var(--tm-card-bg);
  border-radius: 14px;
  border: 1px solid var(--tm-border-light);
  transition: all 0.3s ease;
  display: flex;
  flex-direction: column;
}
.cert-card.unlocked {
  border-color: rgba(var(--tm-color-primary-rgb), 0.2);
  background: linear-gradient(135deg, rgba(var(--tm-color-primary-rgb), 0.06), rgba(217, 70, 239, 0.03));
}
.cert-card.unlocked:hover {
  transform: translateY(-4px);
  box-shadow: 0 10px 36px rgba(var(--tm-color-primary-rgb), 0.12);
  border-color: rgba(var(--tm-color-primary-rgb), 0.35);
}
.cert-card.locked {
  opacity: 0.5;
}

.cert-card-top {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}
.cert-icon-wrap {
  width: 52px;
  height: 52px;
  border-radius: 14px;
  background: rgba(var(--tm-color-primary-rgb), 0.08);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.cert-card.locked .cert-icon-wrap {
  background: rgba(255, 255, 255, 0.04);
}
.cert-icon {
  font-size: 28px;
}
.cert-badges {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 6px;
}
.cert-level-tag {
  padding: 3px 10px;
  border-radius: 20px;
  font-size: 11px;
  font-weight: 700;
}
.lv-beginner { background: rgba(52,211,153,0.12); color: #34d399; }
.lv-medium { background: rgba(251,191,36,0.12); color: #fbbf24; }
.lv-advanced { background: rgba(248,113,113,0.12); color: #f87171; }
.lv-expert { background: rgba(139,92,246,0.15); color: var(--tm-color-primary); }

.cert-status-tag {
  padding: 2px 10px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
  background: rgba(var(--tm-color-primary-rgb), 0.12);
  color: var(--tm-color-primary);
}
.locked-tag {
  background: rgba(255, 255, 255, 0.04);
  color: #52525b;
}

.cert-body {
  flex: 1;
}
.cert-name {
  font-size: 17px;
  font-weight: 700;
  color: var(--tm-text-primary);
  margin: 0 0 10px 0;
}
.cert-desc {
  font-size: 13px;
  color: var(--tm-text-regular);
  line-height: 1.6;
  margin: 0;
}

.cert-score-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 16px;
}
.score-track {
  flex: 1;
  height: 6px;
  border-radius: 3px;
  background: var(--tm-border-light);
  overflow: hidden;
}
.score-fill {
  height: 100%;
  border-radius: 3px;
  background: linear-gradient(90deg, var(--tm-color-primary), var(--tm-color-primary-dark));
  transition: width 0.6s ease;
}
.score-text {
  font-size: 13px;
  color: var(--tm-text-regular);
  font-variant-numeric: tabular-nums;
  min-width: 64px;
  text-align: right;
  font-weight: 600;
}
.score-divider { color: #52525b; margin: 0 2px; }

.cert-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 16px;
  padding-top: 14px;
  border-top: 1px solid rgba(var(--tm-color-primary-rgb), 0.1);
}
.cert-id {
  font-size: 12px;
  color: var(--tm-color-primary);
  font-family: 'Courier New', monospace;
  font-weight: 600;
}
.cert-date {
  font-size: 12px;
  color: var(--tm-text-secondary);
}
.locked-footer {
  border-top-color: var(--tm-border-light);
}
.unlock-hint {
  font-size: 12px;
  color: #52525b;
}

/* Empty */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 0;
  background: var(--tm-card-bg);
  border: 1px dashed var(--tm-border-light);
  border-radius: 14px;
}
.empty-icon { font-size: 56px; margin-bottom: 16px; }
.empty-text { font-size: 14px; color: var(--tm-text-secondary); margin: 0; }

@media (max-width: 768px) {
  .certificates-page { padding: 24px 16px; }
  .cert-stats { flex-wrap: wrap; }
  .cert-grid { grid-template-columns: 1fr; }
}
</style>