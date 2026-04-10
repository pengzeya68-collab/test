<template>
  <div class="skill-analysis">
    <div class="container">
      <div class="page-header">
        <h1 class="page-title">技能分析中心</h1>
        <p class="page-subtitle">全面了解你的技能掌握情况，针对性提升</p>
      </div>

      <!-- 总体得分卡片 -->
      <div class="overview-card">
        <div class="score-section">
          <div class="score-circle">
            <svg class="circle-svg" viewBox="0 0 100 100">
              <circle 
                class="circle-bg" 
                cx="50" 
                cy="50" 
                r="40" 
                stroke-width="8" 
                fill="none"
              />
              <circle 
                class="circle-progress" 
                cx="50" 
                cy="50" 
                r="40" 
                stroke-width="8" 
                fill="none"
                :stroke-dasharray="251.2" 
                :stroke-dashoffset="251.2 - (251.2 * overallScore / 100)"
              />
            </svg>
            <div class="score-content">
              <div class="score-number">{{ overallScore }}</div>
              <div class="score-label">综合得分</div>
              <div class="score-level">{{ overallLevel }}</div>
            </div>
          </div>
          <div class="score-info">
            <h2>能力评估</h2>
            <p class="level-desc">{{ levelDescription }}</p>
            <div class="improvement-tip">
              <el-icon size="20" color="#e6a23c"><Warning /></el-icon>
              <span>{{ improvementTip }}</span>
            </div>
          </div>
        </div>
      </div>

      <div class="content-grid">
        <!-- 左侧雷达图 -->
        <div class="left-section">
          <div class="card">
            <h3 class="card-title">技能雷达图</h3>
            <SkillRadar :radar-data="radarData" v-if="radarData" />
          </div>
          
          <!-- 技能提升进度 -->
          <div class="card">
            <h3 class="card-title">技能提升进度</h3>
            <div class="progress-list">
              <div class="progress-item" v-for="item in skillProgress" :key="item.skill">
                <div class="progress-header">
                  <span class="skill-name">{{ item.skill }}</span>
                  <span class="progress-value">{{ item.current }}/{{ item.target }} 分</span>
                </div>
                <el-progress 
                  :percentage="Math.round(item.current / item.target * 100)" 
                  :show-text="false"
                  stroke-width="8"
                />
                <div class="progress-footer">
                  <span class="growth-rate">月增长：{{ item.monthly_growth }} 分</span>
                  <span class="time-needed" v-if="item.months_needed">
                    预计{{ item.months_needed }}个月达到目标
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 右侧技能详情 -->
        <div class="right-section">
          <div class="card">
            <h3 class="card-title">技能详情</h3>
            <div class="skills-list">
              <div 
                class="skill-item" 
                v-for="skill in skills" 
                :key="skill.key"
                @click="viewSkillDetail(skill)"
              >
                <div class="skill-header">
                  <div class="skill-info">
                    <h4 class="skill-name">{{ skill.name }}</h4>
                    <p class="skill-desc">{{ skill.description }}</p>
                  </div>
                  <div class="skill-score">
                    <div class="score-badge" :class="getScoreClass(skill.score)">
                      {{ skill.score }}分
                    </div>
                    <el-tag :type="getLevelTagType(skill.level)" size="small">
                      {{ skill.level }}
                    </el-tag>
                  </div>
                </div>
                <el-progress 
                  :percentage="skill.score" 
                  :show-text="false"
                  :color="getScoreColor(skill.score)"
                  stroke-width="6"
                />
                <p class="skill-suggestion">
                  <el-icon size="14" color="#409eff"><InfoFilled /></el-icon>
                  {{ skill.suggestion }}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 技能详情弹窗 -->
      <el-dialog 
        v-model="detailVisible" 
        title="技能详情"
        width="600px"
      >
        <div v-if="selectedSkill" class="skill-detail-content">
          <div class="detail-header">
            <div class="detail-score">
              <div class="score-number-lg">{{ selectedSkill.score }}</div>
              <div class="score-unit">分</div>
            </div>
            <div class="detail-info">
              <h3>{{ selectedSkill.name }}</h3>
              <p>{{ selectedSkill.description }}</p>
              <el-tag :type="getLevelTagType(selectedSkill.level)" size="large">
                {{ selectedSkill.level }}
              </el-tag>
            </div>
          </div>
          
          <div class="detail-section">
            <h4>提升建议</h4>
            <p class="suggestion-text">{{ selectedSkill.suggestion }}</p>
          </div>
          
          <div class="detail-section" v-if="selectedSkill.recommended_exercises?.length > 0">
            <h4>推荐练习</h4>
            <div class="exercise-list">
              <div 
                class="exercise-item" 
                v-for="ex in selectedSkill.recommended_exercises" 
                :key="ex.id"
                @click="goToExercise(ex.id)"
              >
                <div class="exercise-info">
                  <span class="exercise-title">{{ ex.title }}</span>
                  <el-tag size="small" :type="getDifficultyTagType(ex.difficulty)">
                    {{ getDifficultyText(ex.difficulty) }}
                  </el-tag>
                </div>
                <span class="exercise-time">{{ ex.time_estimate }}分钟</span>
              </div>
            </div>
          </div>
        </div>
      </el-dialog>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Warning, InfoFilled } from '@element-plus/icons-vue'
import SkillRadar from '@/components/SkillRadar.vue'
import request from '@/utils/request'

const router = useRouter()

const skills = ref([])
const radarData = ref(null)
const overallScore = ref(0)
const overallLevel = ref('')
const skillProgress = ref([])
const detailVisible = ref(false)
const selectedSkill = ref(null)
const loading = ref(false)

const levelDescription = computed(() => {
  const level = overallLevel.value
  const descriptions = {
    '入门': '你刚刚进入测试领域，还有很大的提升空间，加油！',
    '了解': '你已经掌握了基础的测试知识，可以尝试更多实战练习。',
    '掌握': '你的技能已经比较扎实，可以承担大部分测试工作。',
    '熟练': '你已经是一名优秀的测试工程师，能够独立负责项目测试。',
    '精通': '你在测试领域已经有很深的造诣，可以指导新人成长。',
    '专家': '你是测试领域的专家，在行业内有很高的水平。'
  }
  return descriptions[level] || '继续努力，你会越来越优秀！'
})

const improvementTip = computed(() => {
  const score = overallScore.value
  if (score < 60) {
    return '建议先巩固基础理论知识，多做基础练习。'
  } else if (score < 80) {
    return '你的基础不错，可以开始学习进阶技能，提升综合能力。'
  } else {
    return '你已经很优秀了，可以尝试更高难度的挑战，向专家方向发展。'
  }
})

onMounted(() => {
  fetchSkillData()
  fetchSkillProgress()
})

const fetchSkillData = async () => {
  loading.value = true
  try {
    const res = await request.get('/skills/radar')
    skills.value = res.skills
    radarData.value = res.radar_data
    overallScore.value = res.overall_score
    overallLevel.value = res.overall_level
  } catch (error) {
    console.error('获取技能数据失败:', error)
    ElMessage.error('获取技能数据失败')
  } finally {
    loading.value = false
  }
}

const fetchSkillProgress = async () => {
  try {
    const res = await request.get('/skills/progress')
    skillProgress.value = res.progress
  } catch (error) {
    console.error('获取技能进度失败:', error)
  }
}

const getScoreClass = (score) => {
  if (score >= 80) return 'high'
  if (score >= 60) return 'medium'
  return 'low'
}

const getScoreColor = (score) => {
  if (score >= 80) return '#67c23a'
  if (score >= 60) return '#e6a23c'
  return '#f56c6c'
}

const getLevelTagType = (level) => {
  const map = {
    '入门': 'info',
    '了解': 'warning',
    '掌握': 'success',
    '熟练': 'success',
    '精通': 'primary',
    '专家': 'danger'
  }
  return map[level] || 'info'
}

const getDifficultyTagType = (difficulty) => {
  const map = {
    'easy': 'success',
    'medium': 'warning',
    'hard': 'danger'
  }
  return map[difficulty] || 'info'
}

const getDifficultyText = (difficulty) => {
  const map = {
    'easy': '简单',
    'medium': '中等',
    'hard': '困难'
  }
  return map[difficulty] || difficulty
}

const viewSkillDetail = async (skill) => {
  try {
    const res = await request.get(`/skills/detail/${skill.key}`)
    selectedSkill.value = res
    detailVisible.value = true
  } catch (error) {
    console.error('获取技能详情失败:', error)
    ElMessage.error('获取技能详情失败')
  }
}

const goToExercise = (exerciseId) => {
  detailVisible.value = false
  router.push(`/exercises/${exerciseId}`)
}
</script>

<style scoped>
.skill-analysis {
  padding: 30px 0;
  min-height: calc(100vh - 60px);
  background-color: var(--tm-bg-color);
  background-image: var(--tm-bg-image);
  background-size: cover;
  background-position: center;
}

.container {
  width: 100%;
  max-width: none;
  margin: 0 auto;
  padding: 0 20px;
  box-sizing: border-box;
}

.page-header {
  margin-bottom: 30px;
}

.page-title {
  font-size: 32px;
  font-weight: bold;
  color: var(--tm-text-primary);
  margin: 0 0 8px 0;
}

.page-subtitle {
  font-size: 14px;
  color: var(--tm-text-secondary);
  margin: 0;
}

.overview-card {
  background: var(--tm-card-bg);
  border-radius: 12px;
  padding: 40px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  border: var(--tm-card-border);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  margin-bottom: 30px;
}

.score-section {
  display: flex;
  align-items: center;
  gap: 60px;
}

.score-circle {
  position: relative;
  width: 180px;
  height: 180px;
  flex-shrink: 0;
}

.circle-svg {
  width: 100%;
  height: 100%;
  transform: rotate(-90deg);
}

.circle-bg {
  stroke: var(--tm-border-light);
}

.circle-progress {
  stroke: var(--tm-color-primary);
  stroke-linecap: round;
  transition: stroke-dashoffset 1s ease;
}

.score-content {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
}

.score-number {
  font-size: 48px;
  font-weight: bold;
  color: var(--tm-color-primary);
  line-height: 1;
  margin-bottom: 4px;
}

.score-label {
  font-size: 14px;
  color: var(--tm-text-secondary);
  margin-bottom: 4px;
}

.score-level {
  font-size: 16px;
  font-weight: bold;
  color: var(--tm-text-primary);
}

.score-info h2 {
  font-size: 24px;
  font-weight: bold;
  color: var(--tm-text-primary);
  margin: 0 0 12px 0;
}

.level-desc {
  font-size: 16px;
  color: var(--tm-text-secondary);
  margin-bottom: 20px;
  line-height: 1.6;
}

.improvement-tip {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: rgba(230, 162, 60, 0.1);
  border-radius: 8px;
  font-size: 14px;
  color: #e6a23c;
}

.content-grid {
  display: grid;
  grid-template-columns: 500px 1fr;
  gap: 30px;
}

.card {
  background: var(--tm-card-bg);
  border-radius: 12px;
  padding: 30px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  border: var(--tm-card-border);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  margin-bottom: 30px;
}

.card-title {
  font-size: 18px;
  font-weight: bold;
  color: var(--tm-text-primary);
  margin: 0 0 20px 0;
}

.left-section {
  display: flex;
  flex-direction: column;
  gap: 30px;
}

.progress-list {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.progress-item {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.skill-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--tm-text-primary);
}

.progress-value {
  font-size: 14px;
  color: var(--tm-text-secondary);
}

.progress-footer {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: var(--tm-text-secondary);
  margin-top: 4px;
}

.growth-rate {
  color: #67c23a;
}

.time-needed {
  color: var(--tm-text-secondary);
}

.right-section {
  display: flex;
  flex-direction: column;
}

.skills-list {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.skill-item {
  padding: 20px;
  background: rgba(var(--tm-bg-page-rgb), 0.5);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  border: 1px solid transparent;
}

.skill-item:hover {
  background: var(--tm-bg-hover);
  border-color: var(--tm-border-light);
  transform: translateX(4px);
}

.skill-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.skill-info {
  flex: 1;
  margin-right: 20px;
}

.skill-name {
  font-size: 16px;
  font-weight: bold;
  color: var(--tm-text-primary);
  margin: 0 0 6px 0;
}

.skill-desc {
  font-size: 13px;
  color: var(--tm-text-secondary);
  margin: 0;
  line-height: 1.5;
}

.skill-score {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 8px;
  flex-shrink: 0;
}

.score-badge {
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 18px;
  font-weight: bold;
  color: white;
}

.score-badge.high {
  background: #67c23a;
}

.score-badge.medium {
  background: #e6a23c;
}

.score-badge.low {
  background: #f56c6c;
}

.skill-suggestion {
  font-size: 13px;
  color: var(--tm-text-secondary);
  margin: 10px 0 0 0;
  line-height: 1.6;
  display: flex;
  align-items: flex-start;
  gap: 6px;
}

/* 弹窗样式 */
.skill-detail-content {
  padding: 10px 0;
}

.detail-header {
  display: flex;
  align-items: center;
  gap: 24px;
  margin-bottom: 30px;
  padding-bottom: 20px;
  border-bottom: 1px solid var(--tm-border-light);
}

.detail-score {
  display: flex;
  align-items: baseline;
  flex-shrink: 0;
}

.score-number-lg {
  font-size: 64px;
  font-weight: bold;
  color: var(--tm-color-primary);
  line-height: 1;
}

.score-unit {
  font-size: 24px;
  color: var(--tm-text-secondary);
  margin-left: 4px;
}

.detail-info h3 {
  font-size: 24px;
  font-weight: bold;
  color: var(--tm-text-primary);
  margin: 0 0 8px 0;
}

.detail-info p {
  font-size: 14px;
  color: var(--tm-text-secondary);
  margin: 0 0 12px 0;
  line-height: 1.6;
}

.detail-section {
  margin-bottom: 24px;
}

.detail-section h4 {
  font-size: 16px;
  font-weight: bold;
  color: var(--tm-text-primary);
  margin: 0 0 12px 0;
}

.suggestion-text {
  padding: 16px;
  background: rgba(var(--tm-color-primary), 0.1);
  border-radius: 8px;
  line-height: 1.8;
  color: var(--tm-color-primary);
  margin: 0;
}

.exercise-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.exercise-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: rgba(var(--tm-bg-page-rgb), 0.5);
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.exercise-item:hover {
  background: rgba(var(--tm-color-primary), 0.08);
}

.exercise-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.exercise-title {
  font-size: 14px;
  color: var(--tm-text-primary);
}

.exercise-time {
  font-size: 12px;
  color: var(--tm-text-secondary);
}

@media (max-width: 1200px) {
  .content-grid {
    grid-template-columns: 1fr;
  }

  .score-section {
    flex-direction: column;
    gap: 30px;
    text-align: center;
  }

  .improvement-tip {
    justify-content: center;
  }
}
</style>
