﻿<template>
  <div class="profile-page">
    <div class="container">
      <div class="profile-header-section">
        <div class="user-card">
          <div class="avatar">
            <div class="avatar-text">{{ (userInfo?.username || '?')[0].toUpperCase() }}</div>
          </div>
          <div class="user-meta">
            <h1 class="username">{{ userInfo?.username }}</h1>
            <div class="meta-row">
              <el-tag :type="levelTagType" effect="dark" size="large">{{ levelText }}</el-tag>
              <span class="meta-item">Lv.{{ userInfo?.level || 1 }}</span>
              <span class="meta-item">{{ userInfo?.email }}</span>
            </div>
          </div>
          <div class="score-badge">
            <div class="badge-value">{{ userInfo?.score || 0 }}</div>
            <div class="badge-label">综合得分</div>
          </div>
        </div>
      </div>

      <div class="content-grid">
        <div class="left-col">
          <div class="card">
            <h3 class="card-title"><span class="title-icon">◈</span>技能画像</h3>
            <div v-if="skillProfile" class="skill-portrait">
              <div class="portrait-score">
                <svg class="portrait-svg" viewBox="0 0 100 100">
                  <circle class="ring-bg" cx="50" cy="50" r="40" stroke-width="8" fill="none" />
                  <circle
                    class="ring-fill"
                    cx="50" cy="50" r="40" stroke-width="8" fill="none"
                    :stroke-dasharray="251.2"
                    :stroke-dashoffset="251.2 - (251.2 * (skillProfile.overall_score || 0) / 100)"
                  />
                </svg>
                <div class="portrait-inner">
                  <div class="portrait-value">{{ Math.round(skillProfile.overall_score || 0) }}</div>
                  <div class="portrait-label">综合得分</div>
                </div>
              </div>
              <div class="dimension-bars" v-if="skillProfile.dimension_scores">
                <div v-for="dim in skillProfile.dimension_scores" :key="dim.key" class="dim-row">
                  <span class="dim-name">{{ dim.name }}</span>
                  <div class="dim-bar">
                    <div class="dim-fill" :style="{ width: dim.score + '%' }"></div>
                  </div>
                  <span class="dim-score">{{ dim.score }}</span>
                </div>
              </div>
              <el-button type="primary" text @click="router.push('/skill-analysis')">
                查看详细分析 →
              </el-button>
            </div>
            <div v-else class="empty-portrait">
              <p>你还没有完成入学测评</p>
              <el-button type="primary" @click="router.push('/assessment')">立即测评</el-button>
            </div>
          </div>

          <div class="card">
            <h3 class="card-title"><span class="title-icon">◈</span>学习统计</h3>
            <div class="stats-grid">
              <div class="stat-item">
                <div class="stat-value">{{ stats.exercises_done }}</div>
                <div class="stat-label">完成习题</div>
              </div>
              <div class="stat-item">
                <div class="stat-value">{{ stats.exams_taken }}</div>
                <div class="stat-label">参加考试</div>
              </div>
              <div class="stat-item">
                <div class="stat-value">{{ stats.interviews_done }}</div>
                <div class="stat-label">模拟面试</div>
              </div>
              <div class="stat-item">
                <div class="stat-value">{{ stats.streak_days }}</div>
                <div class="stat-label">连续学习</div>
              </div>
            </div>
          </div>

          <div class="card" v-if="recentActivities.length > 0">
            <h3 class="card-title"><span class="title-icon">◈</span>最近活动</h3>
            <div class="activity-list">
              <div
                v-for="act in recentActivities"
                :key="act.id"
                class="activity-item"
                @click="router.push(`/exercises/${act.exercise_id}`)"
              >
                <div class="activity-icon" :class="act.result === 'pass' ? 'act-pass' : 'act-fail'">
                  {{ act.result === 'pass' ? '✓' : '✗' }}
                </div>
                <div class="activity-content">
                  <div class="activity-title">{{ act.exercise_title }}</div>
                  <div class="activity-time">{{ act.created_at }}</div>
                </div>
                <div class="activity-score" :class="act.result === 'pass' ? 'score-pass' : 'score-fail'">
                  {{ act.score }}分
                </div>
              </div>
            </div>
          </div>

          <div class="card" v-if="knowledgeMap.length > 0">
            <h3 class="card-title"><span class="title-icon">◈</span>知识点掌握度</h3>
            <div class="knowledge-map">
              <div class="km-summary">
                <span class="km-stat mastered">已掌握 {{ knowledgeStats.mastered_points }}</span>
                <span class="km-stat learning">学习中 {{ knowledgeStats.learning_points }}</span>
                <span class="km-stat not-started">未开始 {{ knowledgeStats.not_started_points }}</span>
              </div>
              <div class="km-grid">
                <div
                  v-for="kp in knowledgeMap"
                  :key="kp.knowledge_point"
                  class="km-item"
                  :class="{
                    'km-mastered': kp.mastery >= 80,
                    'km-learning': kp.mastery > 0 && kp.mastery < 80,
                    'km-not-started': kp.mastery === 0,
                  }"
                  @click="router.push('/exercises')"
                >
                  <div class="km-bar">
                    <div class="km-bar-fill" :style="{ width: kp.mastery + '%' }"></div>
                  </div>
                  <div class="km-info">
                    <span class="kp-name">{{ kp.knowledge_point }}</span>
                    <span class="kp-mastery">{{ kp.mastery }}%</span>
                  </div>
                  <span class="kp-count">{{ kp.completed_exercises }}/{{ kp.total_exercises }}</span>
                </div>
              </div>
            </div>
          </div>

          <div class="card">
            <h3 class="card-title"><span class="title-icon">◈</span>学习热力图</h3>
            <div class="heatmap-stats">
              <span class="hm-stat">活跃 {{ heatmapData.total_days }} 天</span>
              <span class="hm-stat">总计 {{ heatmapData.total_submissions }} 题</span>
              <span class="hm-stat">最长连续 {{ heatmapData.longest_streak }} 天</span>
            </div>
            <div class="heatmap-grid">
              <div
                v-for="day in heatmapData.days"
                :key="day.date"
                class="heatmap-cell"
                :class="'level-' + day.level"
                :title="day.date + ': ' + day.total + '题'"
              ></div>
            </div>
            <div class="heatmap-legend">
              <span class="legend-label">少</span>
              <div class="heatmap-cell level-0"></div>
              <div class="heatmap-cell level-1"></div>
              <div class="heatmap-cell level-2"></div>
              <div class="heatmap-cell level-3"></div>
              <div class="heatmap-cell level-4"></div>
              <span class="legend-label">多</span>
            </div>
          </div>

          <div class="card">
            <h3 class="card-title">
              <span class="title-icon">◈</span>成就徽章
              <span class="achievement-count">{{ achievementStats.unlocked_count }}/{{ achievementStats.total_count }}</span>
            </h3>
            <div class="achievement-grid">
              <div
                v-for="ach in achievements"
                :key="ach.id"
                class="achievement-item"
                :class="{ unlocked: ach.unlocked, locked: !ach.unlocked }"
              >
                <div class="ach-icon">{{ ach.unlocked ? ach.icon : '🔒' }}</div>
                <div class="ach-info">
                  <div class="ach-name">{{ ach.name }}</div>
                  <div class="ach-desc">{{ ach.description }}</div>
                </div>
                <div class="ach-exp" v-if="ach.unlocked">+{{ ach.exp_reward }}exp</div>
              </div>
            </div>
          </div>
        </div>

        <div class="right-col">
          <div class="card">
            <h3 class="card-title"><span class="title-icon">◈</span>基本信息</h3>
            <div class="info-list">
              <div class="info-row">
                <span class="info-label">用户名</span>
                <span class="info-value">{{ userInfo?.username }}</span>
              </div>
              <div class="info-row">
                <span class="info-label">邮箱</span>
                <span class="info-value">{{ userInfo?.email }}</span>
              </div>
              <div class="info-row">
                <span class="info-label">手机号</span>
                <span class="info-value">{{ userInfo?.phone || '未绑定' }}</span>
              </div>
              <div class="info-row">
                <span class="info-label">等级</span>
                <span class="info-value">Lv.{{ userInfo?.level || 1 }}</span>
              </div>
              <div class="info-row">
                <span class="info-label">积分</span>
                <span class="info-value">{{ userInfo?.score || 0 }}</span>
              </div>
              <div class="info-row">
                <span class="info-label">注册时间</span>
                <span class="info-value">{{ formatDate(userInfo?.created_at) }}</span>
              </div>
            </div>
          </div>

          <div class="card">
            <h3 class="card-title"><span class="title-icon">◈</span>修改密码</h3>
            <el-form
              ref="passwordFormRef"
              :model="passwordForm"
              label-width="100px"
              style="max-width: 400px;"
            >
              <el-form-item
                label="旧密码"
                prop="old_password"
                :rules="[{ required: true, message: '请输入旧密码', trigger: 'blur' }]"
              >
                <el-input v-model="passwordForm.old_password" type="password" placeholder="请输入旧密码" />
              </el-form-item>
              <el-form-item
                label="新密码"
                prop="new_password"
                :rules="[
                  { required: true, message: '请输入新密码', trigger: 'blur' },
                  { min: 6, max: 32, message: '密码长度 6-32 个字符', trigger: 'blur' }
                ]"
              >
                <el-input v-model="passwordForm.new_password" type="password" placeholder="请输入新密码" />
              </el-form-item>
              <el-form-item
                label="确认密码"
                prop="confirm_password"
                :rules="[
                  { required: true, message: '请确认新密码', trigger: 'blur' },
                  { validator: validateConfirmPassword, trigger: 'blur' }
                ]"
              >
                <el-input v-model="passwordForm.confirm_password" type="password" placeholder="再次输入新密码" />
              </el-form-item>
              <el-form-item>
                <el-button type="primary" @click="handleChangePassword" :loading="loading">修改密码</el-button>
              </el-form-item>
            </el-form>
          </div>

          <div class="card">
            <h3 class="card-title"><span class="title-icon">◈</span>快捷入口</h3>
            <div class="quick-links">
              <div class="quick-link" @click="router.push('/skill-analysis')">
                <span class="ql-icon">📊</span>
                <span>技能分析</span>
              </div>
              <div class="quick-link" @click="router.push('/learning-paths')">
                <span class="ql-icon">📚</span>
                <span>学习路径</span>
              </div>
              <div class="quick-link" @click="router.push('/exercises')">
                <span class="ql-icon">✏️</span>
                <span>习题练习</span>
              </div>
              <div class="quick-link" @click="router.push('/interview')">
                <span class="ql-icon">🎤</span>
                <span>模拟面试</span>
              </div>
              <div class="quick-link" @click="router.push('/assessment')">
                <span class="ql-icon">🎯</span>
                <span>重新测评</span>
              </div>
              <div class="quick-link" @click="router.push('/ai-tutor')">
                <span class="ql-icon">🤖</span>
                <span>AI 导师</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import request from '@/utils/request'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()
const passwordFormRef = ref(null)
const loading = ref(false)
const userInfo = ref(null)
const skillProfile = ref(null)

const stats = ref({
  exercises_done: 0,
  exams_taken: 0,
  interviews_done: 0,
  streak_days: 0,
})

const achievements = ref([])
const achievementStats = ref({ unlocked_count: 0, total_count: 0, total_exp: 0 })
const recentActivities = ref([])
const knowledgeMap = ref([])
const knowledgeStats = ref({ mastered_points: 0, learning_points: 0, not_started_points: 0 })
const heatmapData = ref({ days: [], total_days: 0, total_submissions: 0, longest_streak: 0 })

const passwordForm = ref({
  old_password: '',
  new_password: '',
  confirm_password: '',
})

const levelText = computed(() => {
  const score = userInfo.value?.score || 0
  if (score >= 90) return '专家'
  if (score >= 80) return '精通'
  if (score >= 70) return '熟练'
  if (score >= 60) return '掌握'
  if (score >= 40) return '了解'
  return '入门'
})

const levelTagType = computed(() => {
  const score = userInfo.value?.score || 0
  if (score >= 80) return 'danger'
  if (score >= 60) return 'warning'
  return 'info'
})

const validateConfirmPassword = (rule, value, callback) => {
  if (value !== passwordForm.value.new_password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const formatDate = (dateStr) => {
  if (!dateStr) return '—'
  try {
    return new Date(dateStr).toLocaleDateString('zh-CN')
  } catch {
    return dateStr
  }
}

const fetchUserInfo = async () => {
  try {
    const res = await request.get('/auth/profile')
    userInfo.value = res.user
  } catch (e) {
    userInfo.value = userStore.userInfo
  }
}

const fetchSkillProfile = async () => {
  try {
    const res = await request.get('/skills/radar')
    skillProfile.value = {
      overall_score: res.overall_score,
      overall_level: res.overall_level,
      dimension_scores: res.skills?.map(s => ({
        key: s.key,
        name: s.name,
        score: s.score,
      })),
    }
  } catch (e) {
    if (userStore.skillProfile) {
      skillProfile.value = userStore.skillProfile
    }
  }
}

const fetchStats = async () => {
  try {
    const [exercises, exams, interviews] = await Promise.allSettled([
      request.get('/exercises?limit=1'),
      request.get('/exams?limit=1'),
      request.get('/interview/sessions?limit=1'),
    ])
    if (exercises.status === 'fulfilled') {
      stats.value.exercises_done = exercises.value.total || exercises.value.items?.length || 0
    }
    if (exams.status === 'fulfilled') {
      stats.value.exams_taken = exams.value.total || exams.value.items?.length || 0
    }
    if (interviews.status === 'fulfilled') {
      stats.value.interviews_done = interviews.value.total || interviews.value.items?.length || 0
    }
  } catch {
    // silently fail
  }
}

const fetchAchievements = async () => {
  try {
    const res = await request.get('/achievements')
    achievements.value = res.achievements || []
    achievementStats.value = {
      unlocked_count: res.unlocked_count || 0,
      total_count: res.total_count || 0,
      total_exp: res.total_exp || 0,
    }
  } catch {
    // silently fail
  }
}

const handleChangePassword = async () => {
  if (!passwordFormRef.value) return
  await passwordFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      try {
        await request.post('/auth/change-password', {
          old_password: passwordForm.value.old_password,
          new_password: passwordForm.value.new_password,
        })
        ElMessage.success('密码修改成功！请重新登录')
        userStore.logout()
        router.push('/login')
      } catch (error) {
        ElMessage.error(error.response?.data?.error || '密码修改失败')
      } finally {
        loading.value = false
        passwordForm.value = { old_password: '', new_password: '', confirm_password: '' }
      }
    }
  })
}

onMounted(() => {
  fetchUserInfo()
  fetchSkillProfile()
  fetchStats()
  fetchAchievements()
  fetchRecentActivity()
  fetchKnowledgeMap()
  fetchHeatmap()
})

const fetchRecentActivity = async () => {
  try {
    const res = await request.get('/exercise/recent-activity')
    recentActivities.value = res.activities || []
  } catch {
    // silently fail
  }
}

const fetchKnowledgeMap = async () => {
  try {
    const res = await request.get('/skills/knowledge-map')
    knowledgeMap.value = res.knowledge_points || []
    knowledgeStats.value = {
      mastered_points: res.mastered_points || 0,
      learning_points: res.learning_points || 0,
      not_started_points: res.not_started_points || 0,
    }
  } catch {
    // silently fail
  }
}

const fetchHeatmap = async () => {
  try {
    const res = await request.get('/report/heatmap')
    heatmapData.value = res
  } catch {
    // silently fail
  }
}
</script>

<style scoped>
.profile-page {
  padding: 30px 0;
  min-height: calc(100vh - 60px);
  background: #0a0a14;
  background-image: radial-gradient(ellipse at 20% 50%, rgba(139, 92, 246, 0.06) 0%, transparent 50%);
}

.container {
  width: 100%;
  max-width: none;
  margin: 0 auto;
  padding: 0 20px;
  box-sizing: border-box;
}

.profile-header-section {
  margin-bottom: 30px;
}

.user-card {
  display: flex;
  align-items: center;
  gap: 24px;
  padding: 32px 40px;
  background: rgba(18, 18, 31, 0.8);
  border-radius: 16px;
  border: 1px solid rgba(139, 92, 246, 0.15);
  box-shadow: 0 4px 20px rgba(139, 92, 246, 0.1);
  backdrop-filter: blur(20px);
}

.avatar {
  width: 72px;
  height: 72px;
  border-radius: 50%;
  background: linear-gradient(135deg, #8b5cf6, #d946ef);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.avatar-text {
  font-size: 32px;
  font-weight: 800;
  color: white;
}

.user-meta {
  flex: 1;
}

.username {
  font-size: 28px;
  font-weight: 800;
  color: #e2e8f0;
  margin: 0 0 8px 0;
}

.meta-row {
  display: flex;
  align-items: center;
  gap: 16px;
}

.meta-item {
  font-size: 14px;
  color: #94a3b8;
}

.score-badge {
  text-align: center;
  padding: 16px 28px;
  background: rgba(139, 92, 246, 0.08);
  border-radius: 12px;
  border: 1px solid rgba(139, 92, 246, 0.15);
}

.badge-value {
  font-size: 36px;
  font-weight: 900;
  background: linear-gradient(135deg, #8b5cf6, #d946ef);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  line-height: 1;
}

.badge-label {
  font-size: 12px;
  color: #94a3b8;
  margin-top: 4px;
  letter-spacing: 1px;
}

.content-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 30px;
}

.left-col, .right-col {
  display: flex;
  flex-direction: column;
  gap: 30px;
}

.card {
  background: rgba(18, 18, 31, 0.8);
  border-radius: 16px;
  padding: 24px;
  border: 1px solid rgba(139, 92, 246, 0.12);
  box-shadow: 0 4px 20px rgba(139, 92, 246, 0.1);
  backdrop-filter: blur(20px);
}

.card-title {
  font-size: 18px;
  font-weight: bold;
  color: #e2e8f0;
  margin: 0 0 20px 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.title-icon {
  color: #8b5cf6;
  font-size: 14px;
  text-shadow: 0 0 8px rgba(139, 92, 246, 0.5);
}

.skill-portrait {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
}

.portrait-score {
  position: relative;
  width: 140px;
  height: 140px;
}

.portrait-svg {
  width: 100%;
  height: 100%;
  transform: rotate(-90deg);
}

.ring-bg {
  stroke: rgba(139, 92, 246, 0.1);
}

.ring-fill {
  stroke: #8b5cf6;
  stroke-linecap: round;
  filter: drop-shadow(0 0 6px rgba(139, 92, 246, 0.6));
}

.portrait-inner {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
}

.portrait-value {
  font-size: 36px;
  font-weight: 900;
  background: linear-gradient(135deg, #8b5cf6, #d946ef);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  line-height: 1;
  font-variant-numeric: tabular-nums;
}

.portrait-label {
  font-size: 12px;
  color: #94a3b8;
  letter-spacing: 1px;
  margin-top: 2px;
}

.dimension-bars {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.dim-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.dim-name {
  font-size: 13px;
  color: #94a3b8;
  width: 100px;
  flex-shrink: 0;
  text-align: right;
}

.dim-bar {
  flex: 1;
  height: 6px;
  background: rgba(139, 92, 246, 0.1);
  border-radius: 3px;
  overflow: hidden;
}

.dim-fill {
  height: 100%;
  background: linear-gradient(90deg, #8b5cf6, #d946ef);
  border-radius: 3px;
  box-shadow: 0 0 8px rgba(139, 92, 246, 0.3);
  transition: width 1s cubic-bezier(0.4, 0, 0.2, 1);
}

.dim-score {
  font-size: 14px;
  font-weight: 700;
  color: #d946ef;
  width: 30px;
  text-align: right;
}

.empty-portrait {
  text-align: center;
  padding: 30px 0;
  color: #94a3b8;
}

.empty-portrait p {
  margin-bottom: 16px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.stat-item {
  text-align: center;
  padding: 16px;
  background: rgba(139, 92, 246, 0.04);
  border-radius: 10px;
  border: 1px solid rgba(139, 92, 246, 0.08);
}

.stat-value {
  font-size: 28px;
  font-weight: 800;
  background: linear-gradient(135deg, #8b5cf6, #d946ef);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  line-height: 1;
  margin-bottom: 6px;
}

.stat-label {
  font-size: 12px;
  color: #94a3b8;
}

.activity-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.activity-item {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 12px 16px;
  background: rgba(139, 92, 246, 0.03);
  border-radius: 10px;
  border: 1px solid rgba(139, 92, 246, 0.06);
  cursor: pointer;
  transition: all 0.2s ease;
}

.activity-item:hover {
  background: rgba(139, 92, 246, 0.08);
  border-color: rgba(139, 92, 246, 0.15);
}

.activity-icon {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 700;
  flex-shrink: 0;
}

.act-pass {
  background: rgba(103, 194, 58, 0.15);
  color: #67c23a;
}

.act-fail {
  background: rgba(245, 108, 108, 0.15);
  color: #f56c6c;
}

.activity-content {
  flex: 1;
  min-width: 0;
}

.activity-title {
  font-size: 14px;
  font-weight: 500;
  color: #e2e8f0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.activity-time {
  font-size: 12px;
  color: #64748b;
  margin-top: 2px;
}

.activity-score {
  font-size: 14px;
  font-weight: 700;
  flex-shrink: 0;
}

.score-pass {
  color: #67c23a;
}

.score-fail {
  color: #f56c6c;
}

.knowledge-map {
  padding: 4px 0;
}

.km-summary {
  display: flex;
  gap: 20px;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.km-stat {
  font-size: 13px;
  font-weight: 600;
}

.km-stat.mastered {
  color: #67c23a;
}

.km-stat.learning {
  color: #e6a23c;
}

.km-stat.not-started {
  color: var(--tm-text-secondary);
}

.km-grid {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.km-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 14px;
  border-radius: 8px;
  background: rgba(0, 0, 0, 0.15);
  cursor: pointer;
  transition: all 0.2s ease;
}

.km-item:hover {
  background: rgba(139, 92, 246, 0.08);
}

.km-bar {
  width: 80px;
  height: 6px;
  border-radius: 3px;
  background: rgba(255, 255, 255, 0.06);
  overflow: hidden;
  flex-shrink: 0;
}

.km-bar-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 0.5s ease;
}

.km-mastered .km-bar-fill {
  background: #67c23a;
}

.km-learning .km-bar-fill {
  background: linear-gradient(90deg, #8b5cf6, #d946ef);
}

.km-not-started .km-bar-fill {
  background: var(--tm-text-secondary);
}

.km-info {
  flex: 1;
  display: flex;
  justify-content: space-between;
  min-width: 0;
}

.kp-name {
  font-size: 14px;
  color: #e2e8f0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.kp-mastery {
  font-size: 14px;
  font-weight: 700;
  color: #8b5cf6;
  margin-left: 8px;
  flex-shrink: 0;
}

.km-mastered .kp-mastery {
  color: #67c23a;
}

.kp-count {
  font-size: 12px;
  color: #64748b;
  flex-shrink: 0;
}

.heatmap-stats {
  display: flex;
  gap: 20px;
  margin-bottom: 16px;
}

.hm-stat {
  font-size: 13px;
  color: #94a3b8;
  font-weight: 600;
}

.heatmap-grid {
  display: grid;
  grid-template-rows: repeat(7, 1fr);
  grid-auto-flow: column;
  gap: 3px;
  overflow-x: auto;
  padding-bottom: 8px;
}

.heatmap-cell {
  width: 12px;
  height: 12px;
  border-radius: 2px;
  background: rgba(139, 92, 246, 0.06);
}

.heatmap-cell.level-1 {
  background: rgba(139, 92, 246, 0.2);
}

.heatmap-cell.level-2 {
  background: rgba(139, 92, 246, 0.4);
}

.heatmap-cell.level-3 {
  background: rgba(139, 92, 246, 0.65);
}

.heatmap-cell.level-4 {
  background: #8b5cf6;
}

.heatmap-legend {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 8px;
  justify-content: flex-end;
}

.legend-label {
  font-size: 11px;
  color: #64748b;
}

.heatmap-legend .heatmap-cell {
  width: 10px;
  height: 10px;
}

.info-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 14px;
  border-bottom: 1px solid rgba(139, 92, 246, 0.08);
}

.info-row:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.info-label {
  font-size: 14px;
  color: #94a3b8;
}

.info-value {
  font-size: 14px;
  color: #e2e8f0;
  font-weight: 500;
}

.quick-links {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.quick-link {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 16px 8px;
  background: rgba(139, 92, 246, 0.04);
  border: 1px solid rgba(139, 92, 246, 0.08);
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.25s ease;
  font-size: 13px;
  color: #c084fc;
}

.quick-link:hover {
  background: rgba(139, 92, 246, 0.1);
  border-color: rgba(139, 92, 246, 0.2);
  transform: translateY(-2px);
}

.ql-icon {
  font-size: 24px;
}

.achievement-count {
  font-size: 14px;
  font-weight: 400;
  color: #94a3b8;
  margin-left: auto;
}

.achievement-grid {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.achievement-item {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 12px 16px;
  border-radius: 10px;
  transition: all 0.25s ease;
}

.achievement-item.unlocked {
  background: rgba(139, 92, 246, 0.06);
  border: 1px solid rgba(139, 92, 246, 0.15);
}

.achievement-item.locked {
  background: rgba(100, 116, 139, 0.04);
  border: 1px solid rgba(100, 116, 139, 0.08);
  opacity: 0.6;
}

.ach-icon {
  font-size: 28px;
  flex-shrink: 0;
  width: 40px;
  text-align: center;
}

.ach-info {
  flex: 1;
}

.ach-name {
  font-size: 14px;
  font-weight: 600;
  color: #e2e8f0;
  margin-bottom: 2px;
}

.ach-desc {
  font-size: 12px;
  color: #94a3b8;
}

.ach-exp {
  font-size: 12px;
  font-weight: 700;
  color: #d946ef;
  flex-shrink: 0;
}

@media (max-width: 1200px) {
  .content-grid {
    grid-template-columns: 1fr;
  }

  .user-card {
    flex-direction: column;
    text-align: center;
  }

  .meta-row {
    justify-content: center;
  }
}
</style>
