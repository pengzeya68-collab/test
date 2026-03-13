<template>
  <div class="learning-paths">
    <el-page-header @back="goBack" content="学习路径"></el-page-header>
    <el-divider></el-divider>
    
    <el-row gutter="20">
      <el-col :span="6" v-for="path in learningPaths" :key="path.id">
        <el-card class="path-card" @click="viewPath(path.id)" shadow="hover">
          <template #header>
            <div class="card-header">
              <span>{{ path.title }}</span>
              <el-tag :type="getDifficultyTag(path.difficulty)">{{ getDifficultyText(path.difficulty) }}</el-tag>
            </div>
          </template>
          <p class="description">{{ path.description || '暂无描述' }}</p>
          <div class="path-info">
            <span>🗣️ {{ path.language }}</span>
            <span>⏱️ {{ path.estimated_hours }}小时</span>
            <span>📝 {{ path.exercise_count }}个练习</span>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-empty v-if="learningPaths.length === 0" description="暂无学习路径"></el-empty>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import request from '@/utils/request'

const router = useRouter()
const learningPaths = ref([])

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

const viewPath = (id) => {
  router.push(`/learning-paths/${id}`)
}

const goBack = () => {
  router.go(-1)
}

const fetchLearningPaths = async () => {
  try {
    const res = await request.get('/learning-paths')
    learningPaths.value = res
  } catch (error) {
    console.error('Failed to fetch learning paths:', error)
  }
}

onMounted(() => {
  fetchLearningPaths()
})
</script>

<style scoped>
.path-card {
  margin-bottom: 20px;
  cursor: pointer;
  transition: all 0.3s;
}

.path-card:hover {
  transform: translateY(-5px);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.description {
  color: #666;
  margin: 10px 0;
  height: 60px;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
}

.path-info {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #909399;
  margin-top: 15px;
}
</style>
