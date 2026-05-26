<template>
  <div class="lesson-page">
    <div class="lesson-navbar">
      <button class="back-btn" @click="goBack">← {{ pathTitle }}</button>
      <div class="lesson-nav-info" v-if="lesson">
        <span>{{ lesson.current_index }} / {{ lesson.total_lessons }} 节</span>
        <span class="time-badge">{{ lesson.time_estimate }}分钟</span>
      </div>
    </div>

    <div class="lesson-layout" v-if="lesson">
      <aside class="lesson-sidebar">
        <div class="sidebar-header">
          📖 课程目录
        </div>
        <nav class="sidebar-list">
          <div
            v-for="s in sections"
            :key="s.id"
            class="sidebar-item"
            :class="{ active: s.id === lesson.id }"
            @click="switchLesson(s.id)"
          >
            <span class="sidebar-order">{{ s.sort_order }}</span>
            <span class="sidebar-title">{{ s.title }}</span>
            <span class="sidebar-time">{{ s.time_estimate }}min</span>
          </div>
        </nav>
      </aside>

      <main class="lesson-content-wrapper">
        <article class="lesson-content markdown-body">
          <div class="lesson-header">
            <h1 class="lesson-title">{{ lesson.title }}</h1>
            <div class="lesson-meta">
              <span v-if="lesson.knowledge_point">🏷️ {{ lesson.knowledge_point }}</span>
            </div>
          </div>
          <div class="lesson-body" v-html="renderedContent"></div>
        </article>

        <div class="lesson-footer">
          <button class="outline-btn" @click="goToExercises" title="做配套练习题巩固知识">
            ✏️ 做配套练习
          </button>
          <div class="lesson-footer-right">
            <button class="outline-btn" @click="prevLesson" :disabled="!lesson?.prev_lesson">
              ← 上一节
            </button>
            <button class="primary-btn" @click="nextLesson">
              {{ lesson?.next_lesson ? '下一节 →' : '✅ 已完成全部课程' }}
            </button>
          </div>
        </div>
      </main>
    </div>

    <div class="lesson-loading" v-if="loading">
      <div class="spinner">⏳</div>
      <p>加载课程内容中...</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { renderMarkdown } from '@/utils/markdown'
import request from '@/utils/request'
import { ElMessage } from 'element-plus'

const router = useRouter()
const route = useRoute()

const pathId = computed(() => route.params.pathId)
const lessonId = computed(() => route.params.lessonId)

const loading = ref(false)
const lesson = ref(null)
const sections = ref([])
const pathTitle = ref('')

const renderedContent = computed(() => renderMarkdown(lesson.value?.content || ''))

const fetchLesson = async () => {
  loading.value = true
  try {
    const [lessonRes, sectionsRes] = await Promise.all([
      request.get(`/learning-paths/${pathId.value}/lessons/${lessonId.value}`),
      request.get(`/learning-paths/${pathId.value}/lessons`),
    ])
    lesson.value = lessonRes
    pathTitle.value = sectionsRes.path_title
    sections.value = sectionsRes.lessons || []
  } catch (error) {
    ElMessage.error('加载课程内容失败')
  } finally {
    loading.value = false
  }
}

const switchLesson = (id) => {
  if (id === lesson.value?.id) return
  router.push(`/learning-paths/${pathId.value}/lessons/${id}`)
}

const prevLesson = () => {
  if (lesson.value?.prev_lesson?.id) switchLesson(lesson.value.prev_lesson.id)
}
const nextLesson = () => {
  if (lesson.value?.next_lesson?.id) switchLesson(lesson.value.next_lesson.id)
}
const goBack = () => router.push(`/learning-paths/${pathId.value}`)
const goToExercises = () => router.push(`/exercises?pathId=${pathId.value}`)

watch(() => route.params.lessonId, (newId) => {
  if (newId) fetchLesson()
})

onMounted(() => fetchLesson())
</script>

<style scoped>
.lesson-page {
  min-height: 100vh;
  background: var(--tm-bg-page);
  display: flex;
  flex-direction: column;
}

.lesson-navbar {
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  background: var(--tm-card-bg);
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  position: sticky;
  top: 0;
  z-index: 100;
}

.back-btn {
  background: none;
  border: none;
  font-size: 15px;
  font-weight: 500;
  color: var(--tm-text-primary);
  cursor: pointer;
  padding: 8px 12px;
  border-radius: 8px;
  transition: background 0.2s;
}
.back-btn:hover { background: rgba(255, 255, 255, 0.06); }

.lesson-nav-info {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 14px;
  color: var(--tm-text-regular);
}

.time-badge {
  font-size: 11px;
  font-weight: 600;
  padding: 2px 10px;
  border-radius: 10px;
  background: rgba(139, 92, 246, 0.12);
  color: var(--tm-color-primary);
}

.lesson-layout {
  display: flex;
  flex: 1;
  height: calc(100vh - 56px);
}

.lesson-sidebar {
  width: 280px;
  min-width: 280px;
  background: var(--tm-card-bg);
  border-right: 1px solid rgba(255, 255, 255, 0.06);
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 20px 20px 16px;
  font-size: 16px;
  font-weight: 700;
  color: var(--tm-text-primary);
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.sidebar-list {
  padding: 8px;
  flex: 1;
  overflow-y: auto;
}

.sidebar-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  color: var(--tm-text-regular);
  font-size: 14px;
}

.sidebar-item:hover {
  background: rgba(var(--tm-color-primary-rgb), 0.08);
  color: var(--tm-text-primary);
}

.sidebar-item.active {
  background: linear-gradient(135deg, var(--tm-color-primary), var(--tm-color-primary-dark));
  color: #ffffff;
}

.sidebar-item.active .sidebar-time {
  color: rgba(255, 255, 255, 0.7);
}

.sidebar-order {
  width: 22px;
  height: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: rgba(var(--tm-color-primary-rgb), 0.1);
  font-size: 12px;
  flex-shrink: 0;
}

.sidebar-item.active .sidebar-order {
  background: rgba(255, 255, 255, 0.25);
}

.sidebar-title {
  flex: 1;
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.sidebar-time {
  font-size: 11px;
  color: var(--tm-text-secondary);
  flex-shrink: 0;
}

.lesson-content-wrapper {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.lesson-content {
  max-width: 820px;
  width: 100%;
  padding: 48px 48px 32px;
}

.markdown-body {
  color: var(--tm-text-primary);
  font-size: 16px;
  line-height: 1.85;
}

.markdown-body :deep(h2) {
  font-size: 26px;
  font-weight: 700;
  color: var(--tm-text-primary);
  margin: 40px 0 20px;
  padding-bottom: 10px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.markdown-body :deep(h3) {
  font-size: 20px;
  font-weight: 600;
  color: var(--tm-text-primary);
  margin: 32px 0 14px;
}

.markdown-body :deep(h4) {
  font-size: 17px;
  font-weight: 600;
  color: var(--tm-text-primary);
  margin: 24px 0 10px;
}

.markdown-body :deep(p) { margin: 12px 0; }

.markdown-body :deep(ul), .markdown-body :deep(ol) {
  padding-left: 24px;
  margin: 12px 0;
}

.markdown-body :deep(li) { margin: 6px 0; }

.markdown-body :deep(strong) {
  color: var(--tm-text-primary);
  font-weight: 600;
}

.markdown-body :deep(code) {
  background: rgba(var(--tm-bg-page-rgb), 0.5);
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 14px;
  font-family: Consolas, Monaco, 'Courier New', monospace;
  color: var(--tm-color-primary-dark);
}

.markdown-body :deep(pre) {
  background: var(--tm-card-bg);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 10px;
  padding: 20px 24px;
  overflow-x: auto;
  margin: 20px 0;
}

.markdown-body :deep(pre code) {
  background: none;
  padding: 0;
  color: var(--tm-text-primary);
  font-size: 14px;
  line-height: 1.7;
}

.markdown-body :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 16px 0;
  font-size: 15px;
}

.markdown-body :deep(th) {
  background: rgba(var(--tm-bg-page-rgb), 0.4);
  color: var(--tm-text-primary);
  font-weight: 600;
  padding: 10px 16px;
  text-align: left;
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.markdown-body :deep(td) {
  padding: 10px 16px;
  border: 1px solid rgba(255, 255, 255, 0.06);
  color: var(--tm-text-regular);
}

.markdown-body :deep(tr:nth-child(even) td) {
  background: rgba(var(--tm-bg-page-rgb), 0.04);
}

.markdown-body :deep(blockquote) {
  border-left: 4px solid var(--tm-color-primary);
  padding: 12px 20px;
  margin: 16px 0;
  background: rgba(var(--tm-color-primary-rgb), 0.05);
  border-radius: 0 8px 8px 0;
  color: var(--tm-text-regular);
}

.markdown-body :deep(blockquote p) { margin: 0; }

.markdown-body :deep(hr) {
  border: none;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  margin: 32px 0;
}

.lesson-header {
  margin-bottom: 32px;
  padding-bottom: 24px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.lesson-title {
  font-size: 30px;
  font-weight: 800;
  color: var(--tm-text-primary);
  margin: 0 0 12px;
}

.lesson-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 14px;
  color: var(--tm-text-regular);
}

.lesson-footer {
  max-width: 820px;
  width: 100%;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px 48px 48px;
}

.lesson-footer-right {
  display: flex;
  gap: 12px;
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
  transition: opacity 0.2s;
}
.primary-btn:hover { opacity: 0.9; }
.primary-btn:disabled { opacity: 0.4; cursor: not-allowed; }

.outline-btn {
  background: transparent;
  color: var(--tm-text-primary);
  border: 1px solid rgba(255, 255, 255, 0.12);
  padding: 10px 24px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}
.outline-btn:hover { border-color: var(--tm-color-primary); }
.outline-btn:disabled { opacity: 0.4; cursor: not-allowed; }

.lesson-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: calc(100vh - 200px);
  gap: 16px;
  color: var(--tm-text-regular);
  font-size: 15px;
}
.spinner { font-size: 40px; animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

@media (max-width: 900px) {
  .lesson-sidebar { display: none; }
  .lesson-content { padding: 32px 20px 20px; }
  .lesson-footer { padding: 20px 20px 32px; }
  .lesson-title { font-size: 24px; }
}
</style>