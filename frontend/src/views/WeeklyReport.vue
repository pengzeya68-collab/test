<template>
  <div class="weekly-report-page">
    <div class="container">
      <div class="page-header">
        <h1 class="page-title">📊 学习周报</h1>
        <p class="page-desc">{{ report.period?.start }} ~ {{ report.period?.end }}</p>
      </div>

      <div class="report-grid">
        <div class="report-card summary-card">
          <h3 class="card-title">本周概览</h3>
          <div class="summary-grid">
            <div class="summary-item">
              <div class="summary-value">{{ report.summary?.total_submissions || 0 }}</div>
              <div class="summary-label">做题数</div>
            </div>
            <div class="summary-item correct">
              <div class="summary-value">{{ report.summary?.correct_count || 0 }}</div>
              <div class="summary-label">答对</div>
            </div>
            <div class="summary-item wrong">
              <div class="summary-value">{{ report.summary?.wrong_count || 0 }}</div>
              <div class="summary-label">答错</div>
            </div>
            <div class="summary-item rate">
              <div class="summary-value">{{ report.summary?.correct_rate || 0 }}%</div>
              <div class="summary-label">正确率</div>
            </div>
          </div>
        </div>

        <div class="report-card compare-card">
          <h3 class="card-title">环比变化</h3>
          <div class="compare-list">
            <div class="compare-item">
              <span class="compare-label">做题数</span>
              <span class="compare-value" :class="report.comparison?.total_change_percent >= 0 ? 'up' : 'down'">
                {{ report.comparison?.total_change_percent >= 0 ? '↑' : '↓' }}
                {{ Math.abs(report.comparison?.total_change_percent || 0) }}%
              </span>
            </div>
            <div class="compare-item">
              <span class="compare-label">上周做题</span>
              <span class="compare-value">{{ report.comparison?.last_week_total || 0 }} 题</span>
            </div>
            <div class="compare-item">
              <span class="compare-label">上周正确率</span>
              <span class="compare-value">{{ report.comparison?.last_correct_rate || 0 }}%</span>
            </div>
          </div>
        </div>

        <div class="report-card checkin-card">
          <h3 class="card-title">签到记录</h3>
          <div class="checkin-stats">
            <div class="checkin-item">
              <span class="checkin-value">{{ report.summary?.checkin_count || 0 }}/7</span>
              <span class="checkin-label">本周签到</span>
            </div>
            <div class="checkin-item">
              <span class="checkin-value">{{ report.summary?.max_streak || 0 }} 天</span>
              <span class="checkin-label">最长连续</span>
            </div>
          </div>
        </div>
      </div>

      <div class="report-card daily-card">
        <h3 class="card-title">每日学习分布</h3>
        <div class="daily-chart">
          <div
            v-for="day in report.daily_data"
            :key="day.date"
            class="daily-bar-group"
          >
            <div class="daily-bars">
              <div
                class="daily-bar bar-correct"
                :style="{ height: getBarHeight(day.correct) + 'px' }"
                :title="`正确: ${day.correct}`"
              ></div>
              <div
                class="daily-bar bar-wrong"
                :style="{ height: getBarHeight(day.total - day.correct) + 'px' }"
                :title="`错误: ${day.total - day.correct}`"
              ></div>
            </div>
            <div class="daily-label">{{ day.day_name }}</div>
            <div class="daily-count">{{ day.total }}</div>
          </div>
        </div>
        <div class="chart-legend">
          <span class="legend-item"><span class="legend-dot correct"></span>正确</span>
          <span class="legend-item"><span class="legend-dot wrong"></span>错误</span>
        </div>
      </div>

      <div class="report-card category-card" v-if="Object.keys(report.category_distribution || {}).length > 0">
        <h3 class="card-title">知识点分布</h3>
        <div class="category-list">
          <div
            v-for="(count, cat) in report.category_distribution"
            :key="cat"
            class="category-item"
          >
            <span class="cat-name">{{ cat }}</span>
            <div class="cat-bar-wrap">
              <div class="cat-bar" :style="{ width: (count / maxCatCount * 100) + '%' }"></div>
            </div>
            <span class="cat-count">{{ count }} 题</span>
          </div>
        </div>
      </div>

      <div class="report-card suggest-card">
        <h3 class="card-title">💡 学习建议</h3>
        <div class="suggest-list">
          <div v-for="(s, i) in report.suggestions" :key="i" class="suggest-item">
            {{ s }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import request from '@/utils/request'

const report = ref({
  period: { start: '', end: '' },
  summary: {},
  comparison: {},
  daily_data: [],
  category_distribution: {},
  suggestions: [],
})

onMounted(() => {
  fetchReport()
})

const fetchReport = async () => {
  try {
    const res = await request.get('/report/weekly')
    report.value = res
  } catch (error) {
    console.error('获取周报失败:', error)
  }
}

const maxCatCount = computed(() => {
  const vals = Object.values(report.value.category_distribution || {})
  return Math.max(...vals, 1)
})

const getBarHeight = (count) => {
  const maxVal = Math.max(...(report.value.daily_data || []).map(d => d.total), 1)
  return Math.max((count / maxVal) * 120, 2)
}
</script>

<style scoped>
.weekly-report-page {
  padding: 40px 0;
  min-height: calc(100vh - 60px);
  background: #09090B;
}

.container {
  max-width: 900px;
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

.report-grid {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 16px;
  margin-bottom: 20px;
}

.report-card {
  background: var(--tm-bg-card, white);
  border-radius: 14px;
  padding: 24px;
  border: 1px solid var(--tm-border-light, #e2e8f0);
  margin-bottom: 16px;
}

.card-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--tm-text-primary);
  margin: 0 0 16px;
}

.summary-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.summary-item {
  text-align: center;
}

.summary-value {
  font-size: 28px;
  font-weight: 900;
  color: var(--tm-text-primary);
}

.summary-item.correct .summary-value {
  color: #67c23a;
}

.summary-item.wrong .summary-value {
  color: #f56c6c;
}

.summary-item.rate .summary-value {
  color: #8b5cf6;
}

.summary-label {
  font-size: 13px;
  color: var(--tm-text-secondary);
  margin-top: 4px;
}

.compare-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.compare-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.compare-label {
  font-size: 14px;
  color: var(--tm-text-secondary);
}

.compare-value {
  font-size: 15px;
  font-weight: 700;
}

.compare-value.up {
  color: #67c23a;
}

.compare-value.down {
  color: #f56c6c;
}

.checkin-stats {
  display: flex;
  flex-direction: column;
  gap: 16px;
  align-items: center;
}

.checkin-item {
  text-align: center;
}

.checkin-value {
  font-size: 24px;
  font-weight: 800;
  color: #8b5cf6;
}

.checkin-label {
  font-size: 13px;
  color: var(--tm-text-secondary);
}

.daily-chart {
  display: flex;
  justify-content: space-around;
  align-items: flex-end;
  height: 160px;
  padding: 0 10px;
}

.daily-bar-group {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
}

.daily-bars {
  display: flex;
  align-items: flex-end;
  gap: 3px;
  height: 120px;
}

.daily-bar {
  width: 16px;
  border-radius: 4px 4px 0 0;
  transition: height 0.5s ease;
  min-height: 2px;
}

.bar-correct {
  background: linear-gradient(180deg, #8b5cf6, #a78bfa);
}

.bar-wrong {
  background: rgba(245, 108, 108, 0.4);
}

.daily-label {
  font-size: 12px;
  color: var(--tm-text-secondary);
}

.daily-count {
  font-size: 11px;
  color: var(--tm-text-secondary);
  font-weight: 600;
}

.chart-legend {
  display: flex;
  justify-content: center;
  gap: 20px;
  margin-top: 12px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--tm-text-secondary);
}

.legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 2px;
}

.legend-dot.correct {
  background: #8b5cf6;
}

.legend-dot.wrong {
  background: rgba(245, 108, 108, 0.4);
}

.category-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.category-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.cat-name {
  font-size: 14px;
  color: var(--tm-text-primary);
  min-width: 80px;
}

.cat-bar-wrap {
  flex: 1;
  height: 8px;
  border-radius: 4px;
  background: rgba(0, 0, 0, 0.04);
  overflow: hidden;
}

.cat-bar {
  height: 100%;
  border-radius: 4px;
  background: linear-gradient(90deg, #8b5cf6, #d946ef);
  transition: width 0.5s ease;
}

.cat-count {
  font-size: 13px;
  color: var(--tm-text-secondary);
  min-width: 50px;
  text-align: right;
}

.suggest-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.suggest-item {
  padding: 12px 16px;
  background: rgba(139, 92, 246, 0.04);
  border-radius: 8px;
  border-left: 3px solid #8b5cf6;
  font-size: 14px;
  color: var(--tm-text-primary);
  line-height: 1.6;
}

@media (max-width: 768px) {
  .report-grid {
    grid-template-columns: 1fr;
  }
}
</style>
