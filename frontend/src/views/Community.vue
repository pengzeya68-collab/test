<template>
  <div class="community">
    <div class="container">
      <div class="page-header">
        <h1 class="page-title">测试学习社区</h1>
        <p class="page-subtitle">分享经验、交流问题、共同成长</p>
        <el-button type="primary" @click="createPost">
          <el-icon><Edit /></el-icon>
          发布帖子
        </el-button>
      </div>

      <div class="content-container">
        <!-- 左侧筛选栏 -->
        <div class="left-sidebar">
          <div class="filter-card">
            <h3 class="card-title">分类筛选</h3>
            <div class="category-list">
              <div 
                class="category-item" 
                :class="{ active: currentCategory === '' }"
                @click="filterCategory('')"
              >
                <span>全部</span>
              </div>
              <div 
                class="category-item" 
                v-for="cat in categories" 
                :key="cat.value"
                :class="{ active: currentCategory === cat.value }"
                @click="filterCategory(cat.value)"
              >
                <span class="category-dot" :style="{ backgroundColor: cat.color }"></span>
                <span>{{ cat.label }}</span>
              </div>
            </div>
          </div>

          <div class="filter-card">
            <h3 class="card-title">排序方式</h3>
            <div class="sort-list">
              <div 
                class="sort-item" 
                :class="{ active: currentSort === 'latest' }"
                @click="currentSort = 'latest'; fetchPosts()"
              >
                <el-icon size="16"><Timer /></el-icon>
                <span>最新发布</span>
              </div>
              <div 
                class="sort-item" 
                :class="{ active: currentSort === 'hot' }"
                @click="currentSort = 'hot'; fetchPosts()"
              >
                <el-icon size="16"><Promotion /></el-icon>
                <span>热门推荐</span>
              </div>
              <div 
                class="sort-item" 
                :class="{ active: currentSort === 'essence' }"
                @click="currentSort = 'essence'; fetchPosts()"
              >
                <el-icon size="16"><Star /></el-icon>
                <span>精华内容</span>
              </div>
            </div>
          </div>

          <div class="filter-card">
            <h3 class="card-title">热门标签</h3>
            <div class="tag-list">
              <el-tag 
                v-for="tag in hotTags" 
                :key="tag"
                size="small"
                :type="currentTag === tag ? 'primary' : 'info'"
                @click="filterTag(tag)"
                effect="plain"
              >
                {{ tag }}
              </el-tag>
            </div>
          </div>
        </div>

        <!-- 中间帖子列表 -->
        <div class="main-content">
          <div class="search-bar">
            <el-input
              v-model="searchKeyword"
              placeholder="搜索帖子标题或内容..."
              @keyup.enter="fetchPosts"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
          </div>

          <div class="post-list">
            <div 
              class="post-item" 
              v-for="post in posts" 
              :key="post.id"
              @click="viewPostDetail(post.id)"
            >
              <div class="post-header">
                <div class="post-meta">
                  <el-avatar :size="32" style="margin-right: 12px;">
                    {{ post.author.username.charAt(0).toUpperCase() }}
                  </el-avatar>
                  <div>
                    <div class="author-name">{{ post.author.username }}</div>
                    <div class="post-time">{{ post.created_at }}</div>
                  </div>
                </div>
                <div class="post-badges">
                  <el-tag 
                    size="small" 
                    :color="post.category.color"
                    effect="light"
                  >
                    {{ post.category.label }}
                  </el-tag>
                  <el-tag size="small" type="warning" v-if="post.is_top" effect="light">
                    置顶
                  </el-tag>
                  <el-tag size="small" type="success" v-if="post.is_essence" effect="light">
                    精华
                  </el-tag>
                </div>
              </div>
              
              <h3 class="post-title">
                {{ post.title }}
              </h3>
              
              <p class="post-summary">
                {{ post.summary }}
              </p>
              
              <div class="post-tags" v-if="post.tags.length > 0">
                <el-tag 
                  v-for="tag in post.tags" 
                  :key="tag" 
                  size="small" 
                  type="info" 
                  effect="plain"
                >
                  {{ tag }}
                </el-tag>
              </div>
              
              <div class="post-stats">
                <div class="stat-item">
                  <el-icon size="14"><View /></el-icon>
                  <span>{{ post.view_count }}</span>
                </div>
                <div class="stat-item" :class="{ active: post.is_liked }" @click.stop="toggleLike(post)">
                  <el-icon size="14"><StarFilled /></el-icon>
                  <span>{{ post.like_count }}</span>
                </div>
                <div class="stat-item">
                  <el-icon size="14"><ChatDotRound /></el-icon>
                  <span>{{ post.comment_count }}</span>
                </div>
                <div class="stat-item" :class="{ active: post.is_favorited }" @click.stop="toggleFavorite(post)">
                  <el-icon size="14"><StarFilled /></el-icon>
                </div>
              </div>
            </div>
          </div>

          <div class="pagination-container" v-if="total > 0">
            <el-pagination
              v-model:current-page="currentPage"
              :page-size="perPage"
              :total="total"
              layout="prev, pager, next, total"
              @current-change="fetchPosts"
            />
          </div>

          <div class="empty-state" v-if="posts.length === 0 && !loading">
            <el-empty description="暂无帖子，快来发布第一个帖子吧~" />
          </div>

          <div class="loading-state" v-if="loading">
            <el-skeleton :rows="5" animated />
          </div>
        </div>

        <!-- 右侧统计栏 -->
        <div class="right-sidebar">
          <div class="stats-card">
            <h3 class="card-title">社区统计</h3>
            <div class="stats-grid">
              <div class="stat-card">
                <div class="stat-number">{{ stats.total_posts }}</div>
                <div class="stat-label">帖子总数</div>
              </div>
              <div class="stat-card">
                <div class="stat-number">{{ stats.total_users }}</div>
                <div class="stat-label">用户总数</div>
              </div>
              <div class="stat-card">
                <div class="stat-number">{{ stats.today_posts }}</div>
                <div class="stat-label">今日新帖</div>
              </div>
              <div class="stat-card">
                <div class="stat-number">{{ stats.online_users }}</div>
                <div class="stat-label">在线用户</div>
              </div>
            </div>
          </div>

          <div class="stats-card">
            <h3 class="card-title">活跃用户</h3>
            <div class="user-list">
              <div class="user-item" v-for="user in activeUsers" :key="user.id">
                <el-avatar :size="36">
                  {{ user.username.charAt(0).toUpperCase() }}
                </el-avatar>
                <div class="user-info">
                  <div class="username">{{ user.username }}</div>
                  <div class="user-desc">{{ user.post_count }}篇帖子</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 发布帖子弹窗 -->
      <el-dialog 
        v-model="showCreateDialog" 
        title="发布新帖子"
        width="700px"
        :close-on-click-modal="false"
      >
        <el-form :model="postForm" label-width="80px">
          <el-form-item label="标题" required>
            <el-input 
              v-model="postForm.title" 
              placeholder="请输入帖子标题"
              maxlength="200"
              show-word-limit
            />
          </el-form-item>
          <el-form-item label="分类" required>
            <el-select v-model="postForm.category" placeholder="请选择分类" style="width: 200px;">
              <el-option 
                v-for="cat in categories" 
                :key="cat.value" 
                :label="cat.label" 
                :value="cat.value"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="标签">
            <el-select 
              v-model="postForm.tags" 
              multiple
              placeholder="选择或输入标签（最多5个）"
              style="width: 100%;"
              filterable
              allow-create
              :max="5"
            >
              <el-option v-for="tag in hotTags" :key="tag" :label="tag" :value="tag" />
            </el-select>
          </el-form-item>
          <el-form-item label="内容" required>
            <el-input
              v-model="postForm.content"
              type="textarea"
              :rows="12"
              placeholder="请输入帖子内容，支持Markdown格式..."
              maxlength="10000"
              show-word-limit
            />
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="showCreateDialog = false">取消</el-button>
          <el-button type="primary" @click="submitPost" :loading="submitting">发布</el-button>
        </template>
      </el-dialog>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Edit, Star, Search, View,
  ChatDotRound, StarFilled, Timer, Promotion
} from '@element-plus/icons-vue'
import request from '@/utils/request'

const router = useRouter()

const posts = ref([])
const categories = ref([])
const currentCategory = ref('')
const currentSort = ref('latest')
const currentTag = ref('')
const searchKeyword = ref('')
const currentPage = ref(1)
const perPage = ref(10)
const total = ref(0)
const loading = ref(false)
const showCreateDialog = ref(false)
const submitting = ref(false)

const hotTags = ref([
  '功能测试', '接口测试', '自动化测试', '性能测试', '安全测试',
  'Python', 'SQL', 'Linux', 'Jmeter', 'Selenium', 'Postman',
  '面试经验', '简历优化', '职业发展'
])

const stats = ref({
  total_posts: 0,
  total_users: 0,
  today_posts: 0,
  online_users: 0
})

const activeUsers = ref([
  { id: 1, username: '测试老司机', post_count: 128 },
  { id: 2, username: '自动化大神', post_count: 96 },
  { id: 3, username: '性能测试专家', post_count: 78 },
  { id: 4, username: '职场老阿姨', post_count: 65 },
  { id: 5, username: '刚入行的小白', post_count: 42 }
])

const postForm = ref({
  title: '',
  content: '',
  category: '',
  tags: []
})

const fetchStats = async () => {
  try {
    const res = await request.get('/community/stats')
    stats.value = res
  } catch (error) {
    console.error('获取统计数据失败:', error)
  }
}

onMounted(() => {
  fetchCategories()
  fetchPosts()
  fetchStats()
})

const fetchCategories = async () => {
  try {
    const res = await request.get('/community/categories')
    categories.value = res
  } catch (error) {
    console.error('获取分类失败:', error)
  }
}

const fetchPosts = async () => {
  loading.value = true
  try {
    const params = {
      page: currentPage.value,
      per_page: perPage.value,
      sort: currentSort.value
    }
    
    if (currentCategory.value) {
      params.category = currentCategory.value
    }
    if (currentTag.value) {
      params.tag = currentTag.value
    }
    if (searchKeyword.value.trim()) {
      params.search = searchKeyword.value.trim()
    }
    
    const res = await request.get('/community/posts', { params })
    posts.value = res.list
    total.value = res.total
  } catch (error) {
    console.error('获取帖子列表失败:', error)
    ElMessage.error('获取帖子列表失败')
  } finally {
    loading.value = false
  }
}

const filterCategory = (category) => {
  currentCategory.value = category
  currentPage.value = 1
  fetchPosts()
}

const filterTag = (tag) => {
  currentTag.value = currentTag.value === tag ? '' : tag
  currentPage.value = 1
  fetchPosts()
}

const viewPostDetail = (postId) => {
  router.push(`/community/post/${postId}`)
}

const toggleLike = async (post) => {
  // 检查是否登录
  const token = localStorage.getItem('token')
  const user = localStorage.getItem('user')
  
  if (!token || !user) {
    ElMessage.warning('你当前未登录，请登录后点赞')
    router.push({
      path: '/login',
      query: { redirect: '/community' }
    })
    return
  }
  
  try {
    const res = await request.post(`/community/posts/${post.id}/like`)
    post.like_count = res.like_count
    post.is_liked = res.action === 'liked'
    ElMessage.success(res.message)
  } catch (error) {
    console.error('点赞失败:', error)
    ElMessage.error('操作失败')
  }
}

const toggleFavorite = async (post) => {
  // 检查是否登录
  const token = localStorage.getItem('token')
  const user = localStorage.getItem('user')
  
  if (!token || !user) {
    ElMessage.warning('你当前未登录，请登录后收藏')
    router.push({
      path: '/login',
      query: { redirect: '/community' }
    })
    return
  }
  
  try {
    const res = await request.post(`/community/posts/${post.id}/favorite`)
    post.is_favorited = res.action === 'favorited'
    ElMessage.success(res.message)
  } catch (error) {
    console.error('收藏失败:', error)
    ElMessage.error('操作失败')
  }
}

const createPost = () => {
  // 检查是否登录
  const token = localStorage.getItem('token')
  const user = localStorage.getItem('user')
  
  if (!token || !user) {
    ElMessage.warning('你当前未登录，请登录后发布帖子')
    router.push({
      path: '/login',
      query: { redirect: '/community' }
    })
    return
  }
  
  // 已经登录才显示发布弹窗
  showCreateDialog.value = true
}

const submitPost = async () => {
  if (!postForm.value.title.trim()) {
    ElMessage.warning('请输入帖子标题')
    return
  }
  if (!postForm.value.category) {
    ElMessage.warning('请选择帖子分类')
    return
  }
  if (!postForm.value.content.trim()) {
    ElMessage.warning('请输入帖子内容')
    return
  }
  
  submitting.value = true
  try {
    await request.post('/community/posts', postForm.value)
    ElMessage.success('帖子发布成功')
    showCreateDialog.value = false
    // 重置表单
    postForm.value = { title: '', content: '', category: '', tags: [] }
    // 刷新列表
    fetchPosts()
  } catch (error) {
    console.error('发布帖子失败:', error)
    ElMessage.error('发布失败，请稍后重试')
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.community {
  padding: 30px 0;
  min-height: calc(100vh - 60px);
  background-color: #09090B;
}

.container {
  width: 100%;
  max-width: 1440px;
  padding: 0 24px;
  margin: 0 auto;
  box-sizing: border-box;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
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

.content-container {
  display: grid;
  grid-template-columns: 240px 1fr 280px;
  gap: 24px;
}

.filter-card {
  background: var(--tm-card-bg);
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  border: var(--tm-card-border);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  margin-bottom: 24px;
}

.card-title {
  font-size: 16px;
  font-weight: bold;
  color: var(--tm-text-primary);
  margin: 0 0 16px 0;
}

.category-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.category-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 14px;
  color: var(--tm-text-secondary);
}

.category-item:hover {
  background: rgba(var(--tm-primary-color), 0.1);
  color: var(--tm-primary-color);
}

.category-item.active {
  background: rgba(var(--tm-primary-color), 0.15);
  color: var(--tm-primary-color);
}

.category-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.sort-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.sort-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 14px;
  color: var(--tm-text-secondary);
}

.sort-item:hover {
  background: rgba(var(--tm-primary-color), 0.1);
  color: var(--tm-primary-color);
}

.sort-item.active {
  background: rgba(var(--tm-primary-color), 0.15);
  color: var(--tm-primary-color);
}

.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.main-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.search-bar {
  background: var(--tm-card-bg);
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  border: var(--tm-card-border);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
}

.post-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.post-item {
  background: var(--tm-card-bg);
  padding: 24px;
  border-radius: 12px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  border: var(--tm-card-border);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  cursor: pointer;
  transition: all 0.3s ease;
}

.post-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px 0 rgba(0, 0, 0, 0.15);
}

.post-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.post-meta {
  display: flex;
  align-items: center;
}

.author-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--tm-text-primary);
  margin-bottom: 2px;
}

.post-time {
  font-size: 12px;
  color: var(--tm-text-secondary);
}

.post-badges {
  display: flex;
  gap: 8px;
}

.post-title {
  font-size: 18px;
  font-weight: bold;
  color: var(--tm-text-primary);
  margin: 0 0 12px 0;
  line-height: 1.5;
}

.post-summary {
  font-size: 14px;
  color: var(--tm-text-secondary);
  line-height: 1.8;
  margin: 0 0 16px 0;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.post-tags {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.post-stats {
  display: flex;
  gap: 24px;
  align-items: center;
  border-top: 1px solid var(--tm-border-light);
  padding-top: 16px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--tm-text-secondary);
  cursor: pointer;
  transition: all 0.3s ease;
}

.stat-item:hover {
  color: var(--tm-primary-color);
}

.stat-item.active {
  color: #f56c6c;
}

.stat-item:nth-child(4).active {
  color: #e6a23c;
}

.right-sidebar {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.stats-card {
  background: #18181B;
  border-radius: 12px;
  padding: 20px;
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.stats-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.stat-card {
  text-align: center;
  padding: 16px 8px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 8px;
}

.stat-number {
  font-size: 24px;
  font-weight: bold;
  color: #C084FC;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 12px;
  color: #71717A;
}

.user-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.user-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-info .username {
  font-size: 14px;
  font-weight: 500;
  color: #FAFAFA;
  margin-bottom: 2px;
}

.user-info .user-desc {
  font-size: 12px;
  color: #71717A;
}

.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}

.empty-state, .loading-state {
  background: #18181B;
  padding: 60px 20px;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.05);
}

@media (max-width: 1200px) {
  .content-container {
    grid-template-columns: 1fr;
  }
  
  .left-sidebar, .right-sidebar {
    order: 2;
  }
  
  .main-content {
    order: 1;
  }
  
  .category-list {
    flex-direction: row;
    overflow-x: auto;
    padding-bottom: 8px;
  }
  
  .category-item {
    flex-shrink: 0;
  }
  
  .sort-list {
    flex-direction: row;
    overflow-x: auto;
    padding-bottom: 8px;
  }
  
  .sort-item {
    flex-shrink: 0;
  }
}
</style>
