<template>
  <div class="exercises">
    <el-page-header @back="goBack" content="练习题库"></el-page-header>
    <el-divider></el-divider>

    <!-- 筛选区 -->
    <el-card style="margin-bottom: 20px;">
      <el-row gutter="20">
        <el-col :span="6">
          <el-select v-model="filters.difficulty" placeholder="难度筛选" clearable @change="fetchExercises">
            <el-option label="全部" value="" />
            <el-option label="初级" value="beginner" />
            <el-option label="中级" value="intermediate" />
            <el-option label="高级" value="advanced" />
          </el-select>
        </el-col>
        <el-col :span="6">
          <el-select v-model="filters.language" placeholder="语言筛选" clearable @change="fetchExercises">
            <el-option label="全部" value="" />
            <el-option label="Python" value="Python" />
            <el-option label="JavaScript" value="JavaScript" />
            <el-option label="Java" value="Java" />
            <el-option label="C++" value="C++" />
          </el-select>
        </el-col>
        <el-col :span="6">
          <el-select v-model="filters.status" placeholder="状态筛选" clearable @change="fetchExercises">
            <el-option label="全部" value="" />
            <el-option label="未完成" value="uncompleted" />
            <el-option label="已完成" value="completed" />
          </el-select>
        </el-col>
        <el-col :span="6">
          <el-input v-model="filters.keyword" placeholder="搜索题目" clearable @keyup.enter="fetchExercises">
            <template #append>
              <el-button icon="Search" @click="fetchExercises" />
            </template>
          </el-input>
        </el-col>
      </el-row>
    </el-card>

    <!-- 练习列表 -->
    <el-row gutter="20">
      <el-col :span="8" v-for="exercise in exercises" :key="exercise.id">
        <el-card class="exercise-card" shadow="hover" @click="viewExercise(exercise.id)">
          <template #header>
            <div class="card-header">
              <span class="exercise-title">{{ exercise.title }}</span>
              <el-tag :type="getDifficultyTag(exercise.difficulty)" size="small">
                {{ getDifficultyText(exercise.difficulty)
              </el-tag>
            </div>
          </template>
          
          <div class="exercise-info">
            <span class="language-tag">{{ exercise.language }}</span>
            <span v-if="exercise.completed" class="completed-tag">
              <el-icon :size="12"><Check /></el-icon> 已完成
            </span>
            <span class="score">得分: {{ exercise.passed_count }}/{{ exercise.total_count }}</span>
          </div>

          <p class="exercise-description">{{ exercise.description }}</p>

          <div class="exercise-footer">
            <el-progress :percentage="Math.round(exercise.passed_count / exercise.total_count * 100)" :show-text="false" />
            <span class="pass-rate">通过率 {{ getPassRate(exercise) }}%</span>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-empty v-if="exercises.length === 0" description="暂无练习题"></el-empty>

    <!-- 分页 -->
    <div style="text-align: center; margin-top: 30px;">
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.page_size"
        :total="pagination.total"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="fetchExercises"
        @current-change="fetchExercises"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Check, Search } from '@element-plus/icons-vue'
import request from '@/utils/request'

const router = useRouter()

const exercises = ref([])
const filters = ref({
  difficulty: '',
  language: '',
  status: '',
  keyword: ''
})

const pagination = ref({
  page: 1,
  page_size: 12,
  total: 0
})

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

const getPassRate = (exercise) => {
  return Math.round(exercise.passed_count / exercise.total_count * 100)
}

const goBack = () => {
  router.go(-1)
}

const viewExercise = (id) => {
  router.push(`/exercises/${id}`)
}

const fetchExercises = async () => {
  try {
    const params = {
      ...filters.value,
      page: pagination.value.page,
      page_size: pagination.value.page_size
    }
    const res = await request.get('/exercises', { params })
    exercises.value = res.exercises
    pagination.value.total = res.total
  } catch (error) {
    console.error('Failed to fetch exercises:', error)
    // 模拟数据
    exercises.value = [
      {
        id: 1,
        title: '两数之和',
        description: '给定一个整数数组 nums 和一个整数目标值 target，请你在该数组中找出 和为目标值 target 的那 两个 整数，并返回它们的数组下标。',
        difficulty: 'beginner',
        language: 'Python',
        completed: true,
        passed_count: 1200,
        total_count: 1500
      },
      {
        id: 2,
        title: '回文数',
        description: '给你一个整数 x ，如果 x 是一个回文整数，返回 true ；否则，返回 false 。',
        difficulty: 'beginner',
        language: 'Python',
        completed: false,
        passed_count: 980,
        total_count: 1200
      },
      {
        id: 3,
        title: '最长公共前缀',
        description: '编写一个函数来查找字符串数组中的最长公共前缀。如果不存在公共前缀，返回空字符串 ""。',
        difficulty: 'beginner',
        language: 'Python',
        completed: true,
        passed_count: 850,
        total_count: 1100
      },
      {
        id: 4,
        title: '有效的括号',
        description: '给定一个只包括 \'(\',\')\',\'{\',\'}\',\'[\',\']\' 的字符串 s ，判断字符串是否有效。',
        difficulty: 'intermediate',
        language: 'JavaScript',
        completed: false,
        passed_count: 760,
        total_count: 1300
      },
      {
        id: 5,
        title: '合并两个有序链表',
        description: '将两个升序链表合并为一个新的 升序 链表并返回。新链表是通过拼接给定的两个链表的所有节点组成的。',
        difficulty: 'intermediate',
        language: 'Java',
        completed: false,
        passed_count: 650,
        total_count: 1000
      },
      {
        id: 6,
        title: '最大子数组和',
        description: '给你一个整数数组 nums ，请你找出一个具有最大和的连续子数组（子数组最少包含一个元素），返回其最大和。',
        difficulty: 'intermediate',
        language: 'C++',
        completed: true,
        passed_count: 580,
        total_count: 950
      }
    ]
    pagination.value.total = 6
  }
}

onMounted(() => {
  fetchExercises()
})
</script>

<style scoped>
.exercise-card {
  margin-bottom: 20px;
  cursor: pointer;
  transition: all 0.3s;
}

.exercise-card:hover {
  transform: translateY(-3px);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.exercise-title {
  font-weight: bold;
  font-size: 16px;
}

.exercise-info {
  display: flex;
  gap: 10px;
  margin-bottom: 10px;
}

.language-tag {
  background-color: #ecf5ff;
  color: #409eff;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.completed-tag {
  background-color: #f0f9ff;
  color: #67c23a;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  display: flex;
  align-items: center;
  gap: 2px;
}

.score {
  color: #909399;
  font-size: 12px;
  margin-left: auto;
}

.exercise-description {
  color: #606266;
  font-size: 14px;
  line-height: 1.6;
  margin-bottom: 15px;
  height: 60px;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
}

.exercise-footer {
  display: flex;
  align-items: center;
  gap: 10px;
}

.exercise-footer .el-progress {
  flex: 1;
}

.pass-rate {
  font-size: 12px;
  color: #909399;
  width: 50px;
  text-align: right;
}
</style>