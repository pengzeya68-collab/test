<template>
  <div class="leaderboard-page">
    <div class="container">
      <div class="page-header">
        <h1 class="page-title">🏆 排行榜</h1>
        <p class="page-desc">与全站学习者一较高下</p>
      </div>

      <div class="my-rank-bar" v-if="myRank">
        <div class="my-rank-info">
          <span class="my-rank-label">我的排名</span>
          <span class="my-rank-number">#{{ myRank }}</span>
        </div>
        <div class="my-rank-score">
          <span class="score-label">{{ currentTab === 'score' ? '积分' : currentTab === 'weekly' ? '本周答对' : '连续天数' }}</span>
          <span class="score-value">{{ myScore }}</span>
        </div>
      </div>

      <el-tabs v-model="currentTab" @tab-change="handleTabChange">
        <el-tab-pane label="🏅 积分榜" name="score">
          <div class="podium" v-if="scoreList.length >= 3">
            <div class="podium-item second" @click="viewProfile(scoreList[1])">
              <div class="podium-avatar">🥈</div>
              <div class="podium-name">{{ scoreList[1].username }}</div>
              <div class="podium-score">{{ scoreList[1].score }}</div>
              <div class="podium-bar bar-2">2</div>
            </div>
            <div class="podium-item first" @click="viewProfile(scoreList[0])">
              <div class="podium-crown">👑</div>
              <div class="podium-avatar">🥇</div>
              <div class="podium-name">{{ scoreList[0].username }}</div>
              <div class="podium-score">{{ scoreList[0].score }}</div>
              <div class="podium-bar bar-1">1</div>
            </div>
            <div class="podium-item third" @click="viewProfile(scoreList[2])">
              <div class="podium-avatar">🥉</div>
              <div class="podium-name">{{ scoreList[2].username }}</div>
              <div class="podium-score">{{ scoreList[2].score }}</div>
              <div class="podium-bar bar-3">3</div>
            </div>
          </div>

          <div class="rank-list">
            <div
              v-for="item in scoreList"
              :key="item.rank"
              class="rank-item"
              :class="{ 'is-me': item.is_me }"
            >
              <span class="rank-number" :class="getRankClass(item.rank)">{{ item.rank }}</span>
              <span class="rank-username">{{ item.username }}</span>
              <span class="rank-score">{{ item.score }} 分</span>
              <el-tag v-if="item.is_me" type="primary" size="small" effect="dark">我</el-tag>
            </div>
          </div>
        </el-tab-pane>

        <el-tab-pane label="📅 本周活跃" name="weekly">
          <div class="rank-list">
            <div
              v-for="item in weeklyList"
              :key="item.rank"
              class="rank-item"
              :class="{ 'is-me': item.is_me }"
            >
              <span class="rank-number" :class="getRankClass(item.rank)">{{ item.rank }}</span>
              <span class="rank-username">{{ item.username }}</span>
              <span class="rank-score">{{ item.weekly_correct }}/{{ item.weekly_total }} 题</span>
              <el-tag v-if="item.is_me" type="primary" size="small" effect="dark">我</el-tag>
            </div>
          </div>
          <el-empty v-if="weeklyList.length === 0" description="本周还没有人做题" />
        </el-tab-pane>

        <el-tab-pane label="🔥 连续签到" name="streak">
          <div class="rank-list">
            <div
              v-for="item in streakList"
              :key="item.rank"
              class="rank-item"
              :class="{ 'is-me': item.is_me }"
            >
              <span class="rank-number" :class="getRankClass(item.rank)">{{ item.rank }}</span>
              <span class="rank-username">{{ item.username }}</span>
              <span class="rank-score">{{ item.streak }} 天</span>
              <el-tag v-if="item.is_me" type="primary" size="small" effect="dark">我</el-tag>
            </div>
          </div>
          <el-empty v-if="streakList.length === 0" description="还没有人签到" />
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
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

const fetchScoreLeaderboard = async () => {
  try {
    const res = await request.get('/leaderboard/score')
    scoreList.value = res.leaderboard || []
    myRank.value = res.my_rank
    myScore.value = res.my_score
  } catch (error) {
    console.error('获取积分排行失败:', error)
  }
}

const fetchWeeklyLeaderboard = async () => {
  try {
    const res = await request.get('/leaderboard/weekly')
    weeklyList.value = res.leaderboard || []
    myRank.value = 0
    myScore.value = res.my_weekly_correct
  } catch (error) {
    console.error('获取周排行失败:', error)
  }
}

const fetchStreakLeaderboard = async () => {
  try {
    const res = await request.get('/leaderboard/streak')
    streakList.value = res.leaderboard || []
    myRank.value = 0
    myScore.value = res.my_streak
  } catch (error) {
    console.error('获取签到排行失败:', error)
  }
}

const handleTabChange = (tab) => {
  if (tab === 'score') fetchScoreLeaderboard()
  else if (tab === 'weekly') fetchWeeklyLeaderboard()
  else if (tab === 'streak') fetchStreakLeaderboard()
}

const getRankClass = (rank) => {
  if (rank === 1) return 'rank-gold'
  if (rank === 2) return 'rank-silver'
  if (rank === 3) return 'rank-bronze'
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
  padding: 40px 0;
  min-height: calc(100vh - 60px);
  background: #09090B;
}

.container {
  max-width: 800px;
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

.my-rank-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 28px;
  background: linear-gradient(to right, #EC4899, #9333EA);
  border-radius: 14px;
  margin-bottom: 30px;
  color: white;
  box-shadow: 0 0 20px rgba(236, 72, 153, 0.3);
}

.my-rank-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.my-rank-label {
  font-size: 14px;
  opacity: 0.85;
}

.my-rank-number {
  font-size: 28px;
  font-weight: 900;
}

.my-rank-score {
  display: flex;
  align-items: center;
  gap: 8px;
}

.score-label {
  font-size: 13px;
  opacity: 0.85;
}

.score-value {
  font-size: 24px;
  font-weight: 800;
}

.podium {
  display: flex;
  justify-content: center;
  align-items: flex-end;
  gap: 16px;
  margin-bottom: 40px;
  padding: 20px 0;
}

.podium-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  cursor: pointer;
  transition: transform 0.2s;
}

.podium-item:hover {
  transform: scale(1.05);
}

.podium-crown {
  font-size: 28px;
  margin-bottom: 4px;
  display: none;
}

.podium-avatar {
  font-size: 36px;
  margin-bottom: 8px;
  display: none;
}

.podium-name {
  font-size: 15px;
  font-weight: 700;
  color: var(--tm-text-primary);
  margin-bottom: 4px;
}

.podium-score {
  font-size: 20px;
  font-weight: 800;
  color: #EC4899;
  margin-bottom: 8px;
}

.podium-bar {
  width: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  font-weight: 900;
  color: white;
  border-radius: 8px 8px 0 0;
}

.bar-1 {
  height: 100px;
  background: linear-gradient(180deg, #FBBF24, #D97706);
  box-shadow: 0 -8px 24px rgba(251, 191, 36, 0.3);
}

.bar-2 {
  height: 70px;
  background: linear-gradient(180deg, #CBD5E1, #64748B);
  box-shadow: 0 -6px 20px rgba(203, 213, 225, 0.2);
}

.bar-3 {
  height: 50px;
  background: linear-gradient(180deg, #D97706, #92400E);
  box-shadow: 0 -4px 16px rgba(217, 119, 6, 0.2);
}

.rank-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.rank-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 14px 20px;
  background: #18181B;
  border-radius: 10px;
  border: 1px solid rgba(255, 255, 255, 0.05);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.rank-item:hover {
  background: #1E1E24;
  border-color: rgba(255, 255, 255, 0.1);
}

.rank-item.is-me {
  background: rgba(236, 72, 153, 0.06);
  border-color: rgba(236, 72, 153, 0.2);
}

.rank-number {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 700;
  background: rgba(255, 255, 255, 0.05);
  color: #71717A;
  flex-shrink: 0;
}

.rank-gold {
  background: linear-gradient(135deg, #FBBF24, #D97706);
  color: white;
  box-shadow: 0 0 12px rgba(251, 191, 36, 0.3);
}

.rank-silver {
  background: linear-gradient(135deg, #CBD5E1, #64748B);
  color: white;
  box-shadow: 0 0 12px rgba(203, 213, 225, 0.2);
}

.rank-bronze {
  background: linear-gradient(135deg, #D97706, #92400E);
  color: white;
  box-shadow: 0 0 12px rgba(217, 119, 6, 0.2);
}

.rank-username {
  flex: 1;
  font-size: 15px;
  font-weight: 600;
  color: #FAFAFA;
}

.rank-score {
  font-size: 15px;
  font-weight: 700;
  color: #EC4899;
}
</style>
