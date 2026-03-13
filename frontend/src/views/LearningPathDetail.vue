<template>
  <div class="learning-path-detail">
    <el-page-header @back="goBack" :content="path.title"></el-page-header>
    <el-divider></el-divider>

    <el-row gutter="20">
      <el-col :span="16">
        <el-card>
          <template #header>
            <div class="header-info">
              <h2>{{ path.title }}</h2>
              <el-tag :type="getDifficultyTag(path.difficulty)" size="large">
                {{ getDifficultyText(path.difficulty) }}
              </el-tag>
            </div>
          </template>
          
          <div class="path-meta">
            <el-descriptions :column="3" border size="small">
              <el-descriptions-item label="编程语言">
                <span>{{ path.language }}</span>
              </el-descriptions-item>
              <el-descriptions-item label="预计时长">
                <span>⏱️ {{ path.estimated_hours }}小时</span>
              </el-descriptions-item>
              <el-descriptions-item label="练习数量">
                <span>📝 {{ path.exercise_count }}个练习</span>
              </el-descriptions-item>
            </el-descriptions>
          </div>

          <div class="path-description" style="margin: 20px 0;">
            <h3>路径介绍</h3>
            <p>{{ path.description }}</p>
          </div>

          <div class="path-content">
            <h3>学习内容</h3>
            <el-timeline style="margin-top: 20px;">
              <el-timeline-item
                v-for="(item, index) in path.content"
                :key="index"
                :timestamp="item.duration"
              >
                <template #icon>
                  <el-icon><Reading /></el-icon>
                </template>
                <h4>{{ item.title }}</h4>
                <p>{{ item.description }}</p>
              </el-timeline-item>
            </el-timeline>
          </div>

          <div style="margin-top: 30px;">
            <el-button type="primary" size="large" @click="startLearning">
              开始学习
            </el-button>
          </div>
        </el-card>
      </el-col>

      <el-col :span="8">
        <el-card>
          <template #header>
            <span>📊 学习进度</span>
          </template>
          <el-progress :percentage="progress" :status="progress === 100 ? 'success' : ''" />
          <p style="margin-top: 15px; text-align: center; color: #666;">
            已完成 {{ completedExercises }} / {{ path.exercise_count }} 个练习
          </p>
        </el-card>

        <el-card style="margin-top: 20px;">
          <template #header>
            <span>🎯 推荐练习</span>
          </template>
          <el-list>
            <el-list-item v-for="exercise in recommendedExercises" :key="exercise.id">
              <div style="width: 100%;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                  <span>{{ exercise.title }}</span>
                  <el-button type="text" @click="goToExercise(exercise.id)">
                    去练习
                  </el-button>
                </div>
                <el-tag size="small" :type="getDifficultyTag(exercise.difficulty)" style="margin-top: 5px;">
                  {{ getDifficultyText(exercise.difficulty) }}
                </el-tag>
              </div>
            </el-list-item>
          </el-list>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Reading } from '@element-plus/icons-vue'
import request from '@/utils/request'

const router = useRouter()
const route = useRoute()
const pathId = route.params.id

const path = ref({
  title: '',
  description: '',
  difficulty: 'beginner',
  language: '',
  estimated_hours: 0,
  exercise_count: 0,
  content: []
})

const progress = ref(0)
const completedExercises = ref(0)
const recommendedExercises = ref([])

const getDifficultyTag = (difficulty) => {
  const tags = {
    beginner: 'success',
    intermediate: 'warning',
    advanced: 'danger'
  }
  return tags[difficulty] || 'info'
}

const getDifficultyText = (difficulty) => {
  const texts = {
    beginner: '初级',
    intermediate: '中级',
    advanced: '高级'
  }
  return texts[difficulty] || difficulty
}

const goBack = () => {
  router.go(-1)
}

const startLearning = () => {
  if (recommendedExercises.value.length > 0) {
    goToExercise(recommendedExercises.value[0].id)
  } else {
    ElMessage.success('已开始学习！')
  }
}

const goToExercise = (exerciseId) => {
  router.push(`/exercises/${exerciseId}`)
}

const fetchPathDetail = async () => {
  try {
    const res = await request.get(`/learning-paths/${pathId}`)
    path.value = res.path
    progress.value = res.progress
    completedExercises.value = res.completed_exercises
    recommendedExercises.value = res.recommended_exercises
  } catch (error) {
    console.error('Failed to fetch path detail:', error)
    // 模拟数据
    path.value = {
      title: 'Python 入门到精通',
      description: '本路径将带领你从零基础开始学习Python编程，掌握Python核心语法、常用库和实战项目开发能力。适合完全没有编程经验的初学者。',
      difficulty: 'beginner',
      language: 'Python',
      estimated_hours: 40,
      exercise_count: 120,
      content: [
        { title: 'Python基础语法', description: '学习变量、数据类型、运算符、流程控制等基础语法', duration: '8小时' },
        { title: '函数与模块', description: '掌握函数定义、参数传递、模块导入与使用', duration: '6小时' },
        { title: '面向对象编程', description: '学习类与对象、继承、多态等面向对象概念', duration: '10小时' },
        { title: '常用标准库', description: '掌握Python常用标准库的使用方法', duration: '8小时' },
        { title: '实战项目开发', description: '通过实际项目巩固所学知识', duration: '8小时' }
      ]
    }
    progress.value = 25
    completedExercises.value = 30
    recommendedExercises.value = [
      { id: 1, title: '变量与数据类型练习', difficulty: 'beginner' },
      { id: 2, title: '条件判断练习', difficulty: 'beginner' },
      { id: 3, title: '循环结构练习', difficulty: 'beginner' }
    ]
  }
}

onMounted(() => {
  fetchPathDetail()
})
</script>

<style scoped>
.header-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-info h2 {
  margin: 0;
}

.path-meta {
  margin: 20px 0;
}

.path-description h3,
.path-content h3 {
  margin: 0 0 10px 0;
  color: #303133;
}

.path-description p {
  line-height: 1.8;
  color: #606266;
}
</style>