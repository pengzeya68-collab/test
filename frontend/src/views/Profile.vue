<template>
  <div class="profile-container">
    <section class="profile-hero">
      <div class="hero-left">
        <div class="avatar-ring">
          <div class="avatar-text">{{ (userInfo?.username || '?')[0].toUpperCase() }}</div>
        </div>
        <div class="hero-info">
          <h1 class="hero-name">{{ userInfo?.username }}</h1>
          <div class="hero-meta">
            <span class="meta-badge" :class="levelClass">{{ levelText }}</span>
            <span class="meta-text">Lv.{{ userInfo?.level || 1 }}</span>
            <span class="meta-divider"></span>
            <span class="meta-text">{{ userInfo?.email }}</span>
          </div>
        </div>
      </div>
      <div class="hero-right">
        <div class="score-card">
          <div class="score-value">{{ userInfo?.score || 0 }}</div>
          <div class="score-label">综合得分</div>
        </div>
      </div>
    </section>

    <div class="profile-grid">
      <div class="main-col">
        <div class="panel" v-if="skillProfile">
          <div class="panel-header">
            <h3 class="panel-title">技能画像</h3>
            <div class="title-glow-line"></div>
          </div>
          <div class="skill-body">
            <div class="skill-ring-area">
              <svg class="ring-svg" viewBox="0 0 120 120">
                <circle class="ring-track" cx="60" cy="60" r="46" stroke-width="10" fill="none" />
                <circle
                  class="ring-progress"
                  cx="60" cy="60" r="46" stroke-width="10" fill="none"
                  :stroke-dasharray="289"
                  :stroke-dashoffset="289 - (289 * (skillProfile.overall_score || 0) / 100)"
                />
              </svg>
              <div class="ring-center">
                <div class="ring-score">{{ Math.round(skillProfile.overall_score || 0) }}</div>
                <div class="ring-unit">综合得分</div>
              </div>
            </div>
            <div class="skill-bars" v-if="skillProfile.dimension_scores">
              <div v-for="dim in skillProfile.dimension_scores" :key="dim.key" class="skill-row">
                <span class="skill-name">{{ dim.name }}</span>
                <div class="skill-track">
                  <div class="skill-fill" :style="{ width: dim.score + '%' }"></div>
                </div>
                <span class="skill-num">{{ dim.score }}</span>
              </div>
            </div>
            <button class="link-btn" @click="router.push('/skill-analysis')">查看详细分析 →</button>
          </div>
        </div>

        <div class="panel" v-else>
          <div class="panel-header">
            <h3 class="panel-title">技能画像</h3>
            <div class="title-glow-line"></div>
          </div>
          <div class="empty-block">
            <p>你还没有完成入学测评</p>
            <button class="primary-btn" @click="router.push('/assessment')">立即测评</button>
          </div>
        </div>

        <div class="panel">
          <div class="panel-header">
            <h3 class="panel-title">学习统计</h3>
            <div class="title-glow-line"></div>
          </div>
          <div class="stats-row">
            <div class="stat-block">
              <div class="stat-num">{{ stats.exercises_done }}</div>
              <div class="stat-label">完成习题</div>
            </div>
            <div class="stat-block">
              <div class="stat-num">{{ stats.exams_taken }}</div>
              <div class="stat-label">参加考试</div>
            </div>
            <div class="stat-block">
              <div class="stat-num">{{ stats.interviews_done }}</div>
              <div class="stat-label">模拟面试</div>
            </div>
            <div class="stat-block">
              <div class="stat-num">{{ stats.streak_days }}</div>
              <div class="stat-label">连续学习</div>
            </div>
          </div>
        </div>

        <div class="panel" v-if="recentActivities.length > 0">
          <div class="panel-header">
            <h3 class="panel-title">最近活动</h3>
            <div class="title-glow-line"></div>
          </div>
          <div class="activity-list">
            <div
              v-for="act in recentActivities"
              :key="act.id"
              class="activity-row"
              @click="router.push(`/exercises/${act.exercise_id}`)"
            >
              <div class="act-icon-box" :class="act.result === 'pass' ? 'pass' : 'fail'">
                {{ act.result === 'pass' ? '✓' : '✗' }}
              </div>
              <div class="act-body">
                <div class="act-title">{{ act.exercise_title }}</div>
                <div class="act-time">{{ act.created_at }}</div>
              </div>
              <div class="act-score" :class="act.result === 'pass' ? 'pass' : 'fail'">{{ act.score }}分</div>
            </div>
          </div>
        </div>

        <div class="panel" v-if="knowledgeMap.length > 0">
          <div class="panel-header">
            <h3 class="panel-title">知识点掌握度</h3>
            <div class="title-glow-line"></div>
          </div>
          <div class="km-header">
            <span class="km-tag mastered">已掌握 {{ knowledgeStats.mastered_points }}</span>
            <span class="km-tag learning">学习中 {{ knowledgeStats.learning_points }}</span>
            <span class="km-tag pending">未开始 {{ knowledgeStats.not_started_points }}</span>
          </div>
          <div class="km-list">
            <div
              v-for="kp in knowledgeMap"
              :key="kp.knowledge_point"
              class="km-row"
              :class="{
                'km-done': kp.mastery >= 80,
                'km-doing': kp.mastery > 0 && kp.mastery < 80,
                'km-new': kp.mastery === 0,
              }"
              @click="router.push('/exercises')"
            >
              <div class="km-bar-wrap">
                <div class="km-bar-inner" :style="{ width: kp.mastery + '%' }"></div>
              </div>
              <div class="km-mid">
                <span class="km-name">{{ kp.knowledge_point }}</span>
                <span class="km-pct">{{ kp.mastery }}%</span>
              </div>
              <span class="km-total">{{ kp.completed_exercises }}/{{ kp.total_exercises }}</span>
            </div>
          </div>
        </div>

        <div class="panel">
          <div class="panel-header">
            <h3 class="panel-title">学习热力图</h3>
            <div class="title-glow-line"></div>
          </div>
          <div class="hm-stats">
            <span class="hm-item">活跃 {{ heatmapData.total_days }} 天</span>
            <span class="hm-item">总计 {{ heatmapData.total_submissions }} 题</span>
            <span class="hm-item">最长连续 {{ heatmapData.longest_streak }} 天</span>
          </div>
          <div class="hm-grid">
            <div
              v-for="day in heatmapData.days"
              :key="day.date"
              class="hm-cell"
              :class="'lvl-' + day.level"
              :title="day.date + ': ' + day.total + '题'"
            ></div>
          </div>
          <div class="hm-legend">
            <span class="lg-label">少</span>
            <div class="hm-cell lvl-0"></div>
            <div class="hm-cell lvl-1"></div>
            <div class="hm-cell lvl-2"></div>
            <div class="hm-cell lvl-3"></div>
            <div class="hm-cell lvl-4"></div>
            <span class="lg-label">多</span>
          </div>
        </div>

        <div class="panel">
          <div class="panel-header">
            <h3 class="panel-title">成就徽章</h3>
            <span class="ach-tally">{{ achievementStats.unlocked_count }}/{{ achievementStats.total_count }}</span>
            <div class="title-glow-line"></div>
          </div>
          <div class="ach-list">
            <div
              v-for="ach in achievements"
              :key="ach.id"
              class="ach-row"
              :class="{ 'ach-on': ach.unlocked, 'ach-off': !ach.unlocked }"
            >
              <div class="ach-emoji">{{ ach.unlocked ? ach.icon : '🔒' }}</div>
              <div class="ach-mid">
                <div class="ach-name">{{ ach.name }}</div>
                <div class="ach-desc">{{ ach.description }}</div>
              </div>
              <div class="ach-xp" v-if="ach.unlocked">+{{ ach.exp_reward }}exp</div>
            </div>
          </div>
        </div>
      </div>

      <div class="side-col">
        <div class="panel">
          <div class="panel-header">
            <h3 class="panel-title">基本信息</h3>
            <div class="title-glow-line"></div>
          </div>
          <div class="info-list">
            <div class="info-row">
              <span class="info-k">用户名</span>
              <span class="info-v">{{ userInfo?.username }}</span>
            </div>
            <div class="info-row">
              <span class="info-k">邮箱</span>
              <span class="info-v">{{ userInfo?.email }}</span>
            </div>
            <div class="info-row">
              <span class="info-k">手机号</span>
              <span class="info-v">{{ userInfo?.phone || '未绑定' }}</span>
            </div>
            <div class="info-row">
              <span class="info-k">等级</span>
              <span class="info-v">Lv.{{ userInfo?.level || 1 }}</span>
            </div>
            <div class="info-row">
              <span class="info-k">积分</span>
              <span class="info-v">{{ userInfo?.score || 0 }}</span>
            </div>
            <div class="info-row">
              <span class="info-k">注册时间</span>
              <span class="info-v">{{ formatDate(userInfo?.created_at) }}</span>
            </div>
          </div>
        </div>

        <div class="panel">
          <div class="panel-header">
            <h3 class="panel-title">修改密码</h3>
            <div class="title-glow-line"></div>
          </div>
          <form class="pwd-form" @submit.prevent="handleChangePassword">
            <div class="field">
              <label class="field-label">旧密码</label>
              <input v-model="passwordForm.old_password" type="password" class="field-input" placeholder="请输入旧密码" required />
            </div>
            <div class="field">
              <label class="field-label">新密码</label>
              <input v-model="passwordForm.new_password" type="password" class="field-input" placeholder="请输入新密码（6-32位）" required minlength="6" maxlength="32" />
            </div>
            <div class="field">
              <label class="field-label">确认密码</label>
              <input v-model="passwordForm.confirm_password" type="password" class="field-input" placeholder="再次输入新密码" required />
            </div>
            <p v-if="passwordForm.confirm_password && passwordForm.confirm_password !== passwordForm.new_password" class="field-error">两次输入的密码不一致</p>
            <button type="submit" class="primary-btn submit-btn" :disabled="loading || (passwordForm.confirm_password && passwordForm.confirm_password !== passwordForm.new_password)">
              {{ loading ? '修改中...' : '修改密码' }}
            </button>
          </form>
        </div>

        <div class="panel">
          <div class="panel-header">
            <h3 class="panel-title">快捷入口</h3>
            <div class="title-glow-line"></div>
          </div>
          <div class="quick-grid">
            <div class="quick-item" @click="router.push('/skill-analysis')">
              <span class="quick-emoji">📊</span>
              <span class="quick-txt">技能分析</span>
            </div>
            <div class="quick-item" @click="router.push('/learning-paths')">
              <span class="quick-emoji">📚</span>
              <span class="quick-txt">学习路径</span>
            </div>
            <div class="quick-item" @click="router.push('/exercises')">
              <span class="quick-emoji">✏️</span>
              <span class="quick-txt">习题练习</span>
            </div>
            <div class="quick-item" @click="router.push('/interview')">
              <span class="quick-emoji">🎤</span>
              <span class="quick-txt">模拟面试</span>
            </div>
            <div class="quick-item" @click="router.push('/assessment')">
              <span class="quick-emoji">🎯</span>
              <span class="quick-txt">重新测评</span>
            </div>
            <div class="quick-item" @click="router.push('/ai-tutor')">
              <span class="quick-emoji">🤖</span>
              <span class="quick-txt">AI 导师</span>
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

const levelClass = computed(() => {
  const score = userInfo.value?.score || 0
  if (score >= 90) return 'lv-expert'
  if (score >= 80) return 'lv-advanced'
  if (score >= 60) return 'lv-medium'
  return 'lv-beginner'
})

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
    const res = await request.get('/skills/radar', { skipAuthError: true })
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
      request.get('/exercises?limit=1', { skipAuthError: true }),
      request.get('/exams?limit=1', { skipAuthError: true }),
      request.get('/interview/sessions?limit=1', { skipAuthError: true }),
    ])
    if (exercises.status === 'fulfilled') {
      stats.value.exercises_done = exercises.value.total || 0
    }
    if (exams.status === 'fulfilled') {
      stats.value.exams_taken = exams.value.total || 0
    }
    if (interviews.status === 'fulfilled') {
      stats.value.interviews_done = interviews.value.total || 0
    }
  } catch {
    // silently fail
  }
}

const fetchAchievements = async () => {
  try {
    const res = await request.get('/achievements', { skipAuthError: true })
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
  if (!passwordForm.value.old_password) {
    ElMessage.warning('请输入旧密码')
    return
  }
  if (!passwordForm.value.new_password || passwordForm.value.new_password.length < 6) {
    ElMessage.warning('新密码至少需要6个字符')
    return
  }
  if (passwordForm.value.new_password !== passwordForm.value.confirm_password) {
    ElMessage.warning('两次输入的密码不一致')
    return
  }
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

const fetchRecentActivity = async () => {
  try {
    const res = await request.get('/exercise/recent-activity', { skipAuthError: true })
    recentActivities.value = res.activities || []
  } catch {
    // silently fail
  }
}

const fetchKnowledgeMap = async () => {
  try {
    const res = await request.get('/skills/knowledge-map', { skipAuthError: true })
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
    const res = await request.get('/report/heatmap', { skipAuthError: true })
    heatmapData.value = res
  } catch {
    // silently fail
  }
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
</script>

<style scoped>
.profile-container {
  width: 100%;
  padding: 40px 60px;
  box-sizing: border-box;
}

.profile-hero {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 36px 40px;
  background: var(--tm-card-bg);
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.06);
  margin-bottom: 36px;
}

.hero-left {
  display: flex;
  align-items: center;
  gap: 24px;
}

.avatar-ring {
  width: 72px;
  height: 72px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--tm-color-primary), var(--tm-color-primary-dark));
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.avatar-text {
  font-size: 30px;
  font-weight: 800;
  color: #fff;
}

.hero-name {
  font-size: 26px;
  font-weight: 800;
  color: var(--tm-text-primary);
  margin: 0 0 8px 0;
  letter-spacing: -0.5px;
}

.hero-meta {
  display: flex;
  align-items: center;
  gap: 14px;
}

.meta-badge {
  font-size: 12px;
  font-weight: 700;
  padding: 3px 12px;
  border-radius: 20px;
  letter-spacing: 0.5px;
}

.meta-badge.lv-expert {
  background: rgba(239, 68, 68, 0.15);
  color: #ef4444;
  border: 1px solid rgba(239, 68, 68, 0.25);
}

.meta-badge.lv-advanced {
  background: rgba(245, 158, 11, 0.15);
  color: #f59e0b;
  border: 1px solid rgba(245, 158, 11, 0.25);
}

.meta-badge.lv-medium {
  background: rgba(59, 130, 246, 0.15);
  color: #3b82f6;
  border: 1px solid rgba(59, 130, 246, 0.25);
}

.meta-badge.lv-beginner {
  background: rgba(34, 211, 238, 0.15);
  color: #22d3ee;
  border: 1px solid rgba(34, 211, 238, 0.25);
}

.meta-text {
  font-size: 13px;
  color: var(--tm-text-regular);
}

.meta-divider {
  width: 1px;
  height: 16px;
  background: rgba(255, 255, 255, 0.1);
}

.score-card {
  text-align: center;
  padding: 18px 28px;
  background: rgba(139, 92, 246, 0.08);
  border-radius: 14px;
  border: 1px solid rgba(139, 92, 246, 0.15);
}

.score-value {
  font-size: 34px;
  font-weight: 900;
  background: linear-gradient(135deg, var(--tm-color-primary), var(--tm-color-primary-dark));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  line-height: 1;
}

.score-label {
  font-size: 12px;
  color: var(--tm-text-regular);
  margin-top: 4px;
  letter-spacing: 1px;
}

.profile-grid {
  display: grid;
  grid-template-columns: 1.2fr 0.8fr;
  gap: 28px;
  align-items: start;
}

.main-col,
.side-col {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.panel {
  background: var(--tm-card-bg);
  border-radius: 14px;
  padding: 28px 30px;
  border: 1px solid rgba(255, 255, 255, 0.06);
}

.panel-header {
  margin-bottom: 4px;
}

.panel-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--tm-text-primary);
  margin: 0 0 12px 0;
  display: inline-block;
}

.ach-tally {
  font-size: 14px;
  color: var(--tm-text-regular);
  float: right;
  margin-top: 2px;
}

.title-glow-line {
  width: 36px;
  height: 3px;
  border-radius: 2px;
  background: linear-gradient(90deg, var(--tm-color-primary), var(--tm-color-primary-dark));
  margin-bottom: 24px;
}

.skill-body {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 24px;
}

.skill-ring-area {
  position: relative;
  width: 140px;
  height: 140px;
}

.ring-svg {
  width: 100%;
  height: 100%;
  transform: rotate(-90deg);
}

.ring-track {
  stroke: rgba(255, 255, 255, 0.06);
}

.ring-progress {
  stroke: var(--tm-color-primary);
  stroke-linecap: round;
  filter: drop-shadow(0 0 8px rgba(139, 92, 246, 0.4));
}

.ring-center {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
}

.ring-score {
  font-size: 36px;
  font-weight: 900;
  background: linear-gradient(135deg, var(--tm-color-primary), var(--tm-color-primary-dark));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  line-height: 1;
}

.ring-unit {
  font-size: 12px;
  color: var(--tm-text-regular);
  letter-spacing: 1px;
  margin-top: 2px;
}

.skill-bars {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.skill-row {
  display: flex;
  align-items: center;
  gap: 14px;
}

.skill-name {
  font-size: 13px;
  color: var(--tm-text-regular);
  width: 90px;
  flex-shrink: 0;
  text-align: right;
}

.skill-track {
  flex: 1;
  height: 6px;
  background: rgba(255, 255, 255, 0.06);
  border-radius: 3px;
  overflow: hidden;
}

.skill-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--tm-color-primary), var(--tm-color-primary-dark));
  border-radius: 3px;
  transition: width 1s cubic-bezier(0.4, 0, 0.2, 1);
}

.skill-num {
  font-size: 14px;
  font-weight: 700;
  color: var(--tm-color-primary-dark);
  width: 30px;
  text-align: right;
}

.link-btn {
  background: none;
  border: none;
  color: var(--tm-color-primary);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  padding: 0;
  transition: opacity 0.2s;
}

.link-btn:hover {
  opacity: 0.8;
}

.empty-block {
  text-align: center;
  padding: 40px 0;
  color: var(--tm-text-regular);
}

.empty-block p {
  margin-bottom: 18px;
}

.primary-btn {
  background: linear-gradient(135deg, var(--tm-color-primary), var(--tm-color-primary-dark));
  color: #fff;
  border: none;
  padding: 10px 24px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.2s, transform 0.15s;
}

.primary-btn:hover {
  opacity: 0.9;
  transform: translateY(-1px);
}

.primary-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

.stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.stat-block {
  text-align: center;
  padding: 20px 12px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 10px;
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.stat-num {
  font-size: 30px;
  font-weight: 800;
  background: linear-gradient(135deg, var(--tm-color-primary), var(--tm-color-primary-dark));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  line-height: 1;
  margin-bottom: 6px;
}

.stat-label {
  font-size: 12px;
  color: var(--tm-text-regular);
}

.activity-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.activity-row {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px 16px;
  background: rgba(255, 255, 255, 0.02);
  border-radius: 10px;
  border: 1px solid rgba(255, 255, 255, 0.04);
  cursor: pointer;
  transition: background 0.2s, border-color 0.2s, transform 0.15s;
}

.activity-row:hover {
  background: rgba(255, 255, 255, 0.04);
  border-color: rgba(139, 92, 246, 0.2);
  transform: translateX(4px);
}

.act-icon-box {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 700;
  flex-shrink: 0;
}

.act-icon-box.pass {
  background: rgba(52, 211, 153, 0.15);
  color: #34d399;
}

.act-icon-box.fail {
  background: rgba(248, 113, 113, 0.15);
  color: #f87171;
}

.act-body {
  flex: 1;
  min-width: 0;
}

.act-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--tm-text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.act-time {
  font-size: 12px;
  color: var(--tm-text-secondary);
  margin-top: 2px;
}

.act-score {
  font-size: 14px;
  font-weight: 700;
  flex-shrink: 0;
}

.act-score.pass {
  color: #34d399;
}

.act-score.fail {
  color: #f87171;
}

.km-header {
  display: flex;
  gap: 18px;
  margin-bottom: 18px;
  padding-bottom: 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.km-tag {
  font-size: 13px;
  font-weight: 600;
}

.km-tag.mastered {
  color: #34d399;
}

.km-tag.learning {
  color: #f59e0b;
}

.km-tag.pending {
  color: var(--tm-text-secondary);
}

.km-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.km-row {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 10px 14px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
}

.km-row:hover {
  background: rgba(255, 255, 255, 0.03);
}

.km-bar-wrap {
  width: 70px;
  height: 6px;
  border-radius: 3px;
  background: rgba(255, 255, 255, 0.06);
  overflow: hidden;
  flex-shrink: 0;
}

.km-bar-inner {
  height: 100%;
  border-radius: 3px;
  transition: width 0.5s ease;
}

.km-done .km-bar-inner {
  background: #34d399;
}

.km-doing .km-bar-inner {
  background: var(--tm-color-primary);
}

.km-new .km-bar-inner {
  background: var(--tm-text-secondary);
}

.km-mid {
  flex: 1;
  display: flex;
  justify-content: space-between;
  min-width: 0;
}

.km-name {
  font-size: 14px;
  color: var(--tm-text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.km-pct {
  font-size: 14px;
  font-weight: 700;
  color: var(--tm-color-primary);
  margin-left: 10px;
  flex-shrink: 0;
}

.km-done .km-pct {
  color: #34d399;
}

.km-total {
  font-size: 12px;
  color: var(--tm-text-secondary);
  flex-shrink: 0;
}

.hm-stats {
  display: flex;
  gap: 22px;
  margin-bottom: 18px;
}

.hm-item {
  font-size: 13px;
  color: var(--tm-text-regular);
  font-weight: 600;
}

.hm-grid {
  display: grid;
  grid-template-rows: repeat(7, 1fr);
  grid-auto-flow: column;
  gap: 3px;
  overflow-x: auto;
  padding-bottom: 8px;
}

.hm-cell {
  width: 13px;
  height: 13px;
  border-radius: 2px;
  background: rgba(255, 255, 255, 0.04);
}

.hm-cell.lvl-1 {
  background: rgba(139, 92, 246, 0.2);
}

.hm-cell.lvl-2 {
  background: rgba(139, 92, 246, 0.4);
}

.hm-cell.lvl-3 {
  background: rgba(139, 92, 246, 0.65);
}

.hm-cell.lvl-4 {
  background: var(--tm-color-primary);
}

.hm-legend {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 10px;
  justify-content: flex-end;
}

.lg-label {
  font-size: 11px;
  color: var(--tm-text-secondary);
}

.hm-legend .hm-cell {
  width: 10px;
  height: 10px;
}

.ach-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.ach-row {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 12px 16px;
  border-radius: 10px;
  transition: all 0.25s ease;
}

.ach-row.ach-on {
  background: rgba(139, 92, 246, 0.06);
  border: 1px solid rgba(139, 92, 246, 0.12);
}

.ach-row.ach-off {
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.04);
  opacity: 0.5;
}

.ach-emoji {
  font-size: 26px;
  flex-shrink: 0;
  width: 38px;
  text-align: center;
}

.ach-mid {
  flex: 1;
}

.ach-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--tm-text-primary);
  margin-bottom: 2px;
}

.ach-desc {
  font-size: 12px;
  color: var(--tm-text-regular);
}

.ach-xp {
  font-size: 12px;
  font-weight: 700;
  color: var(--tm-color-primary-dark);
  flex-shrink: 0;
}

.info-list {
  display: flex;
  flex-direction: column;
}

.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.info-row:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.info-k {
  font-size: 14px;
  color: var(--tm-text-regular);
}

.info-v {
  font-size: 14px;
  color: var(--tm-text-primary);
  font-weight: 500;
}

.pwd-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.field-label {
  font-size: 13px;
  font-weight: 500;
  color: var(--tm-text-regular);
}

.field-input {
  width: 100%;
  padding: 10px 14px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 8px;
  color: var(--tm-text-primary);
  font-size: 14px;
  outline: none;
  transition: border-color 0.2s;
  box-sizing: border-box;
}

.field-input:focus {
  border-color: var(--tm-color-primary);
}

.field-input::placeholder {
  color: var(--tm-text-secondary);
}

.field-error {
  color: #f87171;
  font-size: 12px;
  margin: -8px 0 0 0;
}

.submit-btn {
  width: 100%;
  padding: 12px;
  font-size: 15px;
  margin-top: 4px;
}

.quick-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.quick-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 18px 8px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.25s ease;
}

.quick-item:hover {
  background: rgba(139, 92, 246, 0.08);
  border-color: rgba(139, 92, 246, 0.2);
  transform: translateY(-2px);
}

.quick-emoji {
  font-size: 24px;
}

.quick-txt {
  font-size: 13px;
  color: var(--tm-color-primary);
  font-weight: 500;
}

@media (max-width: 1200px) {
  .profile-container {
    padding: 24px 20px;
  }

  .profile-hero {
    padding: 24px 20px;
  }

  .profile-grid {
    grid-template-columns: 1fr;
  }

  .stats-row {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>