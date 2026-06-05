<template>
  <div class="weekly-report-page">
    <header class="page-header">
      <div class="header-titles">
        <h1 class="page-title">📊 学习周报</h1>
        <p class="page-desc">{{ report.period?.start }} ~ {{ report.period?.end }}</p>
      </div>
    </header>

    <div class="report-grid">
      <div class="report-card summary-card">
        <div class="section-header">
          <h3 class="card-title">本周概览</h3>
          <div class="title-glow-line"></div>
        </div>
        <div class="summary-grid">
          <div class="summary-item">
            <div class="summary-value">{{ report.summary?.total_submissions || 0 }}<span class="summary-unit">题</span></div>
            <div class="summary-label">做题数</div>
          </div>
          <div class="summary-item correct">
            <div class="summary-value">{{ report.summary?.correct_count || 0 }}<span class="summary-unit">题</span></div>
            <div class="summary-label">答对</div>
          </div>
          <div class="summary-item wrong">
            <div class="summary-value">{{ report.summary?.wrong_count || 0 }}<span class="summary-unit">题</span></div>
            <div class="summary-label">答错</div>
          </div>
          <div class="summary-item rate">
            <div class="summary-value">{{ report.summary?.correct_rate || 0 }}<span class="summary-unit">%</span></div>
            <div class="summary-label">正确率</div>
          </div>
        </div>
      </div>

      <div class="report-card compare-card">
        <div class="section-header">
          <h3 class="card-title">环比变化</h3>
          <div class="title-glow-line"></div>
        </div>
        <div class="compare-list">
          <div class="compare-item">
            <span class="compare-label">做题数变化</span>
            <span class="compare-value" :class="report.comparison?.total_change_percent >= 0 ? 'up' : 'down'">
              <span class="compare-arrow">{{ report.comparison?.total_change_percent >= 0 ? '↑' : '↓' }}</span>
              {{ Math.abs(report.comparison?.total_change_percent || 0) }}%
            </span>
          </div>
          <div class="compare-item">
            <span class="compare-label">上周做题</span>
            <span class="compare-value-neutral">{{ report.comparison?.last_week_total || 0 }} 题</span>
          </div>
          <div class="compare-item">
            <span class="compare-label">上周正确率</span>
            <span class="compare-value-neutral">{{ report.comparison?.last_correct_rate || 0 }}%</span>
          </div>
        </div>
      </div>

      <div class="report-card checkin-card">
        <div class="section-header">
          <h3 class="card-title">签到记录</h3>
          <div class="title-glow-line"></div>
        </div>
        <div class="checkin-stats">
          <div class="checkin-item">
            <div class="checkin-value">{{ report.summary?.checkin_count || 0 }}<span class="checkin-unit"> / 7</span></div>
            <div class="checkin-label">本周签到</div>
            <div class="checkin-progress">
              <div class="checkin-progress-fill" :style="{ width: ((report.summary?.checkin_count || 0) / 7 * 100) + '%' }"></div>
            </div>
          </div>
          <div class="checkin-item">
            <div class="checkin-value checkin-streak">{{ report.summary?.max_streak || 0 }}<span class="checkin-unit"> 天</span></div>
            <div class="checkin-label">最长连续</div>
          </div>
        </div>
      </div>
    </div>

    <div class="report-card daily-card">
      <div class="section-header">
        <h3 class="card-title">每日学习分布</h3>
        <div class="title-glow-line"></div>
      </div>
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
          <div class="daily-count">{{ day.total }}题</div>
        </div>
      </div>
      <div class="chart-legend">
        <span class="legend-item"><span class="legend-dot correct"></span>正确</span>
        <span class="legend-item"><span class="legend-dot wrong"></span>错误</span>
      </div>
    </div>

    <div class="report-card category-card" v-if="Object.keys(report.category_distribution || {}).length > 0">
      <div class="section-header">
        <h3 class="card-title">知识点分布</h3>
        <div class="title-glow-line"></div>
      </div>
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
      <div class="section-header">
        <h3 class="card-title">💡 学习建议</h3>
        <div class="title-glow-line"></div>
      </div>
      <div class="suggest-list">
        <div v-for="(s, i) in report.suggestions" :key="i" class="suggest-item">
          <span class="suggest-num">{{ String(i + 1).padStart(2, '0') }}</span>
          <span class="suggest-text">{{ s }}</span>
        </div>
      </div>
      <div class="suggest-empty" v-if="!report.suggestions?.length">
        <p>暂无建议，继续努力学习吧！</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
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
    ElMessage.error('获取周报失败，请稍后重试')
  }
}

const maxCatCount = computed(() => {
  const vals = Object.values(report.value.category_distribution || {})
  return Math.max(...vals, 1)
})

const getBarHeight = (count) => {
  const maxVal = Math.max(...(report.value.daily_data || []).map(d => d.total || 0), 1)
  return Math.max((count / maxVal) * 120, 2)
}
</script>

<style scoped>
.weekly-report-page {
  width: 100%;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  padding: 40px 60px;
  box-sizing: border-box;
  background-color: var(--tm-bg-page);
  color: var(--tm-text-primary);
  gap: 24px;
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

.section-header {
  margin-bottom: 18px;
}
.card-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--tm-text-primary);
  margin: 0 0 8px 0;
}
.title-glow-line {
  width: 36px;
  height: 2px;
  background: linear-gradient(90deg, var(--tm-color-primary), var(--tm-color-primary-dark));
  border-radius: 1px;
}

/* Top 3-column grid */
.report-grid {
  display: grid;
  grid-template-columns: 1.2fr 1fr 0.8fr;
  gap: 20px;
}

.report-card {
  background: var(--tm-card-bg);
  border: 1px solid var(--tm-border-light);
  border-radius: 14px;
  padding: 24px;
}

/* Summary */
.summary-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 18px;
}
.summary-item {
  text-align: center;
}
.summary-value {
  font-size: 30px;
  font-weight: 900;
  color: var(--tm-text-primary);
  line-height: 1.2;
}
.summary-unit {
  font-size: 15px;
  font-weight: 500;
  color: var(--tm-text-secondary);
  margin-left: 2px;
}
.summary-item.correct .summary-value { color: #34d399; }
.summary-item.wrong .summary-value { color: #f87171; }
.summary-item.rate .summary-value { color: var(--tm-color-primary); }
.summary-label {
  font-size: 12px;
  color: var(--tm-text-secondary);
  margin-top: 4px;
}

/* Compare */
.compare-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.compare-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.compare-label {
  font-size: 14px;
  color: var(--tm-text-regular);
}
.compare-value {
  font-size: 16px;
  font-weight: 700;
}
.compare-value.up { color: #34d399; }
.compare-value.down { color: #f87171; }
.compare-value-neutral { font-size: 15px; font-weight: 700; color: var(--tm-text-regular); }
.compare-arrow { font-size: 18px; }

/* Checkin */
.checkin-stats {
  display: flex;
  flex-direction: column;
  gap: 18px;
  align-items: center;
}
.checkin-item {
  text-align: center;
  width: 100%;
}
.checkin-value {
  font-size: 28px;
  font-weight: 800;
  color: var(--tm-color-primary);
}
.checkin-unit { font-size: 16px; font-weight: 500; color: var(--tm-text-regular); }
.checkin-streak { color: var(--tm-color-primary); }
.checkin-label {
  font-size: 12px;
  color: var(--tm-text-secondary);
  margin-top: 4px;
}
.checkin-progress {
  margin-top: 10px;
  height: 6px;
  background: var(--tm-border-light);
  border-radius: 3px;
  overflow: hidden;
}
.checkin-progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--tm-color-primary), var(--tm-color-primary-dark));
  border-radius: 3px;
  transition: width 0.8s ease;
}

/* Daily Chart */
.daily-chart {
  display: flex;
  justify-content: space-around;
  align-items: flex-end;
  height: 170px;
  padding: 10px 10px 0;
}
.daily-bar-group {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}
.daily-bars {
  display: flex;
  align-items: flex-end;
  gap: 4px;
  height: 125px;
}
.daily-bar {
  width: 20px;
  border-radius: 4px 4px 0 0;
  transition: height 0.6s ease;
  min-height: 2px;
}
.bar-correct {
  background: linear-gradient(180deg, var(--tm-color-primary), var(--tm-color-primary-dark));
  box-shadow: 0 0 8px rgba(var(--tm-color-primary-rgb), 0.3);
}
.bar-wrong {
  background: rgba(248, 113, 113, 0.5);
  box-shadow: 0 0 6px rgba(248, 113, 113, 0.15);
}
.daily-label {
  font-size: 12px;
  color: var(--tm-text-regular);
  font-weight: 500;
}
.daily-count {
  font-size: 12px;
  color: var(--tm-text-secondary);
  font-weight: 600;
}

.chart-legend {
  display: flex;
  justify-content: center;
  gap: 24px;
  margin-top: 14px;
}
.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--tm-text-regular);
}
.legend-dot {
  width: 12px;
  height: 12px;
  border-radius: 3px;
}
.legend-dot.correct { background: var(--tm-color-primary); }
.legend-dot.wrong { background: rgba(248, 113, 113, 0.5); }

/* Category */
.category-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.category-item {
  display: flex;
  align-items: center;
  gap: 14px;
}
.cat-name {
  font-size: 14px;
  color: var(--tm-text-regular);
  min-width: 90px;
  font-weight: 500;
}
.cat-bar-wrap {
  flex: 1;
  height: 8px;
  border-radius: 4px;
  background: var(--tm-border-light);
  overflow: hidden;
}
.cat-bar {
  height: 100%;
  border-radius: 4px;
  background: linear-gradient(90deg, var(--tm-color-primary), var(--tm-color-primary-dark));
  transition: width 0.6s ease;
}
.cat-count {
  font-size: 13px;
  color: var(--tm-text-secondary);
  min-width: 50px;
  text-align: right;
  font-weight: 600;
}

/* Suggestions */
.suggest-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.suggest-item {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  padding: 14px 18px;
  background: rgba(var(--tm-color-primary-rgb), 0.04);
  border: 1px solid rgba(var(--tm-color-primary-rgb), 0.08);
  border-radius: 10px;
  transition: all 0.25s;
}
.suggest-item:hover {
  background: rgba(var(--tm-color-primary-rgb), 0.08);
  border-color: rgba(var(--tm-color-primary-rgb), 0.2);
}
.suggest-num {
  font-size: 14px;
  font-weight: 800;
  color: var(--tm-color-primary);
  font-family: 'Courier New', monospace;
  flex-shrink: 0;
  padding-top: 2px;
}
.suggest-text {
  font-size: 14px;
  color: var(--tm-text-regular);
  line-height: 1.7;
}
.suggest-empty {
  text-align: center;
  padding: 20px 0;
  color: var(--tm-text-secondary);
  font-size: 14px;
}
.suggest-empty p { margin: 0; }

@media (max-width: 1000px) {
  .report-grid { grid-template-columns: 1fr 1fr; }
}
@media (max-width: 768px) {
  .weekly-report-page { padding: 24px 16px; }
  .report-grid { grid-template-columns: 1fr; }
  .summary-grid { gap: 12px; }
}
</style>