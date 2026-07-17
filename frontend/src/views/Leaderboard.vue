<template>
  <div class="leaderboard-page">
    <header class="page-header">
      <div class="header-titles">
        <h1 class="page-title">馃弳 鎺掕姒</h1>
        <p class="page-desc">涓庡叏绔欏涔犺€呬竴杈冮珮涓嬶紝浜夊ず鑽ｈ€€鎺掑悕</p>
      </div>
    </header>

    <div class="my-rank-bar" v-if="myRank">
      <div class="rank-bar-left">
        <span class="rank-bar-label">鎴戠殑鎺掑悕</span>
        <span class="rank-bar-number">#{{ myRank }}</span>
      </div>
      <div class="rank-bar-right">
        <span class="rank-bar-metric">{{ currentTab === 'score' ? '绉垎' : currentTab === 'weekly' ? '鏈懆绛斿' : '杩炵画澶╂暟' }}</span>
        <span class="rank-bar-value">{{ myScore }}</span>
      </div>
    </div>

    <div class="tabs-container">
      <div
        class="tab-item"
        :class="{ active: currentTab === 'score' }"
        @click="switchTab('score')"
      >馃弲 绉垎姒</div>
      <div
        class="tab-item"
        :class="{ active: currentTab === 'weekly' }"
        @click="switchTab('weekly')"
      >馃搮 鏈懆娲昏穬</div>
      <div
        class="tab-item"
        :class="{ active: currentTab === 'streak' }"
        @click="switchTab('streak')"
      >馃敟 杩炵画绛惧埌</div>
    </div>

    <div class="tab-content">
      <template v-if="currentTab === 'score'">
        <div class="podium" v-if="scoreList.length >= 3">
          <div class="podium-item second" @click="viewProfile(scoreList[1])">
            <div class="podium-medal">馃</div>
            <div class="podium-name">{{ scoreList[1].username }}</div>
            <div class="podium-score">{{ scoreList[1].score }}<span class="podium-unit"> 鍒</span></div>
            <div class="podium-bar bar-silver">2</div>
          </div>
          <div class="podium-item first" @click="viewProfile(scoreList[0])">
            <div class="podium-crown">馃憫</div>
            <div class="podium-medal">馃</div>
            <div class="podium-name">{{ scoreList[0].username }}</div>
            <div class="podium-score">{{ scoreList[0].score }}<span class="podium-unit"> 鍒</span></div>
            <div class="podium-bar bar-gold">1</div>
          </div>
          <div class="podium-item third" @click="viewProfile(scoreList[2])">
            <div class="podium-medal">馃</div>
            <div class="podium-name">{{ scoreList[2].username }}</div>
            <div class="podium-score">{{ scoreList[2].score }}<span class="podium-unit"> 鍒</span></div>
            <div class="podium-bar bar-bronze">3</div>
          </div>
        </div>

        <div class="rank-list">
          <div
            v-for="item in scoreList.slice(3)"
            :key="item.rank"
            class="rank-item"
            :class="{ 'is-me': item.is_me }"
          >
            <span class="rank-num" :class="getRankClass(item.rank)">{{ item.rank }}</span>
            <span class="rank-avatar-emoji">{{ item.rank <= 3 ? ['馃','馃','馃'][item.rank-1] : '馃懁' }}</span>
            <span class="rank-username">{{ item.username }}</span>
            <span class="rank-score">{{ item.score }} 鍒</span>
            <span class="me-badge" v-if="item.is_me">鎴</span>
          </div>
        </div>
      </template>

      <template v-if="currentTab === 'weekly'">
        <div class="rank-list" v-if="weeklyList.length > 0">
          <div
            v-for="item in weeklyList"
            :key="item.rank"
            class="rank-item"
            :class="{ 'is-me': item.is_me }"
          >
            <span class="rank-num" :class="getRankClass(item.rank)">{{ item.rank }}</span>
            <span class="rank-avatar-emoji">{{ item.rank <= 3 ? ['馃','馃','馃'][item.rank-1] : '馃懁' }}</span>
            <span class="rank-username">{{ item.username }}</span>
            <span class="rank-score">{{ item.weekly_correct }}/{{ item.weekly_total }} 棰</span>
            <span class="me-badge" v-if="item.is_me">鎴</span>
          </div>
        </div>
        <div class="empty-state" v-else>
          <div class="empty-icon">馃摥</div>
          <p class="empty-text">鏈懆杩樻病鏈変汉鍋氶</p>
        </div>
      </template>

      <template v-if="currentTab === 'streak'">
        <div class="rank-list" v-if="streakList.length > 0">
          <div
            v-for="item in streakList"
            :key="item.rank"
            class="rank-item"
            :class="{ 'is-me': item.is_me }"
          >
            <span class="rank-num" :class="getRankClass(item.rank)">{{ item.rank }}</span>
            <span class="rank-avatar-emoji">{{ item.rank <= 3 ? ['馃','馃','馃'][item.rank-1] : '馃懁' }}</span>
            <span class="rank-username">{{ item.username }}</span>
            <span class="rank-score">{{ item.streak }} 澶</span>
            <span class="me-badge" v-if="item.is_me">鎴</span>
          </div>
        </div>
        <div class="empty-state" v-else>
          <div class="empty-icon">馃摥</div>
          <p class="empty-text">杩樻病鏈変汉绛惧埌</p>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import request from '@/utils/request'

const router = useRouter()
const currentTab = ref('score')
const scoreList = ref([])
const weeklyList = ref([])
const streakList = ref([])
const myRank = ref(0)
const myScore = ref(0)

onMounted(() => {
  fetchScoreLeaderboard()
})

const switchTab = (tab) => {
  currentTab.value = tab
  if (tab === 'score') fetchScoreLeaderboard()
  else if (tab === 'weekly') fetchWeeklyLeaderboard()
  else if (tab === 'streak') fetchStreakLeaderboard()
}

const fetchScoreLeaderboard = async () => {
  try {
    const res = await request.get('/leaderboard/score')
    scoreList.value = res.leaderboard || []
    myRank.value = res.my_rank
    myScore.value = res.my_score
  } catch (error) {
    console.error('鑾峰彇绉垎鎺掕澶辫触:', error)
    ElMessage.error('鑾峰彇绉垎鎺掕澶辫触锛岃绋嶅悗閲嶈瘯')
  }
}

const fetchWeeklyLeaderboard = async () => {
  try {
    const res = await request.get('/leaderboard/weekly')
    weeklyList.value = res.leaderboard || []
    myRank.value = res.my_rank || 0
    myScore.value = res.my_weekly_correct
  } catch (error) {
    console.error('获取周排行榜失败', error)
    ElMessage.error('获取周排行榜失败，请稍后重试')
  }
}

const fetchStreakLeaderboard = async () => {
  try {
    const res = await request.get('/leaderboard/streak')
    streakList.value = res.leaderboard || []
    myRank.value = res.my_rank || 0
    myScore.value = res.my_streak
  } catch (error) {
    console.error('鑾峰彇绛惧埌鎺掕澶辫触:', error)
    ElMessage.error('鑾峰彇绛惧埌鎺掕澶辫触锛岃绋嶅悗閲嶈瘯')
  }
}

const getRankClass = (rank) => {
  if (rank === 1) return 'gold'
  if (rank === 2) return 'silver'
  if (rank === 3) return 'bronze'
  return ''
}

const viewProfile = (item) => {
  if (item?.is_me) {
    router.push('/profile')
  }
}
</script>

<style scoped>
.leaderboard-page {
  width: 100%;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  padding: 40px 60px;
  box-sizing: border-box;
  background-color: var(--tm-bg-page);
  color: var(--tm-text-primary);
}

.page-header {
  margin-bottom: 28px;
}
.header-titles {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.page-title {
  font-size: 28px;
  font-weight: 800;
  margin: 0;
  color: #fff;
}
.page-desc {
  font-size: 14px;
  color: var(--tm-text-regular);
  margin: 0;
}

/* My Rank Bar */
.my-rank-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 22px 32px;
  background: linear-gradient(135deg, rgba(var(--tm-color-primary-rgb), 0.15), rgba(var(--tm-color-primary-rgb), 0.15));
  border: 1px solid rgba(var(--tm-color-primary-rgb), 0.2);
  border-radius: 14px;
  margin-bottom: 32px;
}
.rank-bar-left {
  display: flex;
  align-items: center;
  gap: 14px;
}
.rank-bar-label {
  font-size: 14px;
  color: var(--tm-text-regular);
}
.rank-bar-number {
  font-size: 30px;
  font-weight: 900;
  background: linear-gradient(135deg, var(--tm-color-primary), var(--tm-color-primary-dark));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
.rank-bar-right {
  display: flex;
  align-items: center;
  gap: 10px;
}
.rank-bar-metric {
  font-size: 13px;
  color: var(--tm-text-regular);
}
.rank-bar-value {
  font-size: 26px;
  font-weight: 800;
  color: var(--tm-color-primary);
}

/* Custom Tabs */
.tabs-container {
  display: flex;
  gap: 28px;
  border-bottom: 1px solid #27272a;
  margin-bottom: 32px;
}
.tab-item {
  padding: 14px 0;
  color: var(--tm-text-secondary);
  cursor: pointer;
  position: relative;
  font-size: 15px;
  font-weight: 500;
  transition: color 0.2s;
}
.tab-item:hover { color: var(--tm-text-regular); }
.tab-item.active {
  color: var(--tm-color-primary);
  font-weight: 600;
}
.tab-item.active::after {
  content: '';
  position: absolute;
  bottom: -1px;
  left: 0;
  width: 100%;
  height: 2px;
  background: var(--tm-color-primary);
  border-radius: 1px;
}

.tab-content {
  width: 100%;
}

/* Podium */
.podium {
  display: flex;
  justify-content: center;
  align-items: flex-end;
  gap: 20px;
  margin-bottom: 40px;
  padding: 30px 0 10px;
}
.podium-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  cursor: pointer;
  transition: transform 0.25s;
  min-width: 110px;
}
.podium-item:hover {
  transform: translateY(-6px);
}
.podium-crown {
  font-size: 32px;
  margin-bottom: 2px;
  animation: crownBounce 2s ease-in-out infinite;
}
@keyframes crownBounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-6px); }
}
.podium-medal {
  font-size: 40px;
  margin-bottom: 10px;
}
.podium-name {
  font-size: 15px;
  font-weight: 700;
  color: var(--tm-text-primary);
  margin-bottom: 6px;
  max-width: 110px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.podium-score {
  font-size: 22px;
  font-weight: 800;
  color: var(--tm-color-primary);
  margin-bottom: 12px;
}
.podium-unit {
  font-size: 13px;
  font-weight: 500;
  color: var(--tm-text-regular);
}
.podium-bar {
  width: 90px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 26px;
  font-weight: 900;
  color: #fff;
  border-radius: 10px 10px 0 0;
  padding-top: 14px;
}
.bar-gold {
  height: 110px;
  background: linear-gradient(180deg, #fbbf24, #d97706);
  box-shadow: 0 -8px 24px rgba(251, 191, 36, 0.3);
}
.bar-silver {
  height: 80px;
  background: linear-gradient(180deg, #cbd5e1, #64748b);
  box-shadow: 0 -6px 20px rgba(203, 213, 225, 0.2);
}
.bar-bronze {
  height: 60px;
  background: linear-gradient(180deg, #d97706, #92400e);
  box-shadow: 0 -4px 16px rgba(217, 119, 6, 0.2);
}

/* Rank List */
.rank-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.rank-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 22px;
  background: var(--tm-card-bg);
  border-radius: 12px;
  border: 1px solid var(--tm-border-light);
  transition: all 0.25s;
}
.rank-item:hover {
  background: rgba(30, 30, 36, 0.8);
  border-color: var(--border-subtle);
  transform: translateX(4px);
}
.rank-item.is-me {
  background: rgba(var(--tm-color-primary-rgb), 0.06);
  border-color: rgba(var(--tm-color-primary-rgb), 0.2);
}

.rank-num {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 700;
  background: var(--tm-border-light);
  color: var(--tm-text-secondary);
  flex-shrink: 0;
}
.rank-num.gold {
  background: linear-gradient(135deg, #fbbf24, #d97706);
  color: #fff;
  box-shadow: 0 0 14px rgba(251, 191, 36, 0.3);
}
.rank-num.silver {
  background: linear-gradient(135deg, #cbd5e1, #64748b);
  color: #fff;
  box-shadow: 0 0 12px rgba(203, 213, 225, 0.2);
}
.rank-num.bronze {
  background: linear-gradient(135deg, #d97706, #92400e);
  color: #fff;
  box-shadow: 0 0 10px rgba(217, 119, 6, 0.2);
}

.rank-avatar-emoji {
  font-size: 22px;
  flex-shrink: 0;
}
.rank-username {
  flex: 1;
  font-size: 15px;
  font-weight: 600;
  color: var(--tm-text-primary);
}
.rank-score {
  font-size: 15px;
  font-weight: 700;
  color: var(--tm-color-primary);
}
.me-badge {
  padding: 2px 10px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
  background: rgba(var(--tm-color-primary-rgb), 0.15);
  color: var(--tm-color-primary);
}

/* Empty State */
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
.empty-icon {
  font-size: 56px;
  margin-bottom: 16px;
}
.empty-text {
  font-size: 14px;
  color: var(--tm-text-secondary);
  margin: 0;
}

@media (max-width: 768px) {
  .leaderboard-page { padding: 24px 16px; }
  .podium { gap: 10px; }
  .podium-item { min-width: 80px; }
  .podium-bar { width: 70px; }
  .bar-gold { height: 90px; }
  .bar-silver { height: 65px; }
  .bar-bronze { height: 50px; }
  .my-rank-bar { flex-direction: column; gap: 12px; align-items: flex-start; }
}
</style>
