<template>
  <div class="community-admin-dark">
    <h1 class="page-title">社区管理</h1>

    <!-- Tab 切换 -->
    <div class="tabs-card">
      <el-tabs v-model="activeTab" @tab-change="onTabChange" class="dark-tabs">
        <el-tab-pane label="帖子管理" name="posts" />
        <el-tab-pane label="评论管理" name="comments" />
      </el-tabs>
    </div>

    <!-- ====== 帖子列表 ====== -->
    <div v-show="activeTab === 'posts'" class="content-card">
      <div class="toolbar">
        <div class="toolbar-left">
          <el-input
            v-model="postKeyword"
            placeholder="搜索标题/内容"
            class="search-input"
            clearable
            @clear="fetchPosts"
            @keyup.enter="fetchPosts"
          />
          <el-select v-model="postCategory" placeholder="按分类筛选" class="filter-select" clearable @change="fetchPosts">
            <el-option v-for="c in categories" :key="c.value" :label="c.label" :value="c.value" />
          </el-select>
          <el-select v-model="postEssence" placeholder="精华状态" class="filter-select" clearable @change="fetchPosts">
            <el-option label="精华帖" value="true" />
            <el-option label="普通帖" value="false" />
          </el-select>
          <el-select v-model="postTop" placeholder="置顶状态" class="filter-select" clearable @change="fetchPosts">
            <el-option label="已置顶" value="true" />
            <el-option label="未置顶" value="false" />
          </el-select>
          <el-button @click="fetchPosts" class="btn-search">搜索</el-button>
        </div>
      </div>

      <el-table :data="postList" border stripe v-loading="postLoading" class="dark-table">
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="title" label="标题" min-width="240" show-overflow-tooltip />
        <el-table-column prop="author" label="作者" width="110" />
        <el-table-column prop="category" label="分类" width="100">
          <template #default="{ row }">
            <el-tag size="small" type="info">{{ getCategoryLabel(row.category) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="view_count" label="浏览" width="70" />
        <el-table-column prop="like_count" label="点赞" width="70" />
        <el-table-column prop="comment_count" label="评论" width="70" />
        <el-table-column prop="is_essence" label="精华" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_essence ? 'warning' : 'info'" size="small">
              {{ row.is_essence ? '✨精华' : '普通' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="is_top" label="置顶" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_top ? 'danger' : 'info'" size="small">
              {{ row.is_top ? '📌置顶' : '普通' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="发布时间" width="160" />
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button
              size="small"
              :type="row.is_essence ? 'info' : 'warning'"
              @click="toggleEssence(row)"
            >{{ row.is_essence ? '取消精华' : '设为精华' }}</el-button>
            <el-button
              size="small"
              :type="row.is_top ? 'info' : 'danger'"
              @click="toggleTop(row)"
            >{{ row.is_top ? '取消置顶' : '置顶' }}</el-button>
            <el-button size="small" type="danger" plain @click="deletePost(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="postPage"
          v-model:page-size="postSize"
          :total="postTotal"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          @size-change="fetchPosts"
          @current-change="fetchPosts"
          class="dark-pagination"
        />
      </div>
    </div>

    <!-- ====== 评论列表 ====== -->
    <div v-show="activeTab === 'comments'" class="content-card">
      <div class="toolbar">
        <div class="toolbar-left">
          <el-input
            v-model="commentPostId"
            placeholder="按帖子ID筛选"
            class="search-input"
            clearable
            @clear="fetchComments"
            @keyup.enter="fetchComments"
            type="number"
          />
          <el-button @click="fetchComments" class="btn-search">查询</el-button>
        </div>
      </div>

      <el-table :data="commentList" border stripe v-loading="commentLoading" class="dark-table">
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="content" label="评论内容" min-width="300" show-overflow-tooltip />
        <el-table-column prop="author" label="评论者" width="110" />
        <el-table-column prop="post_title" label="所属帖子" width="200" show-overflow-tooltip />
        <el-table-column prop="like_count" label="点赞" width="70" />
        <el-table-column prop="created_at" label="评论时间" width="160" />
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="danger" @click="deleteComment(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="commentPage"
          v-model:page-size="commentSize"
          :total="commentTotal"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          @size-change="fetchComments"
          @current-change="fetchComments"
          class="dark-pagination"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '@/utils/request'

const activeTab = ref('posts')

const categories = [
  { value: 'experience', label: '经验分享' },
  { value: 'question', label: '问题求助' },
  { value: 'resource', label: '资源分享' },
  { value: 'job', label: '求职交流' },
  { value: 'other', label: '其他' }
]
const getCategoryLabel = (val) => categories.find(c => c.value === val)?.label || val

const onTabChange = (tab) => {
  if (tab === 'posts') fetchPosts()
  else fetchComments()
}

// ======== 帖子 ========
const postList = ref([])
const postTotal = ref(0)
const postPage = ref(1)
const postSize = ref(10)
const postLoading = ref(false)
const postKeyword = ref('')
const postCategory = ref('')
const postEssence = ref('')
const postTop = ref('')

const fetchPosts = async () => {
  postLoading.value = true
  try {
    const params = { page: postPage.value, size: postSize.value }
    if (postKeyword.value) params.keyword = postKeyword.value
    if (postCategory.value) params.category = postCategory.value
    if (postEssence.value !== '') params.is_essence = postEssence.value
    if (postTop.value !== '') params.is_top = postTop.value
    const res = await request.get('/admin/community/posts', { params })
    postList.value = res?.list || []
    postTotal.value = res?.total || 0
  } catch (e) {
    ElMessage.error('获取帖子列表失败')
  } finally {
    postLoading.value = false
  }
}

const toggleEssence = async (row) => {
  try {
    const res = await request.post(`/admin/community/posts/${row.id}/toggle-essence`)
    ElMessage.success(res.message || '操作成功')
    fetchPosts()
  } catch (e) {
    ElMessage.error('操作失败')
  }
}

const toggleTop = async (row) => {
  try {
    const res = await request.post(`/admin/community/posts/${row.id}/toggle-top`)
    ElMessage.success(res.message || '操作成功')
    fetchPosts()
  } catch (e) {
    ElMessage.error('操作失败')
  }
}

const deletePost = async (row) => {
  await ElMessageBox.confirm(`确定删除帖子「${row.title.slice(0, 20)}」吗？相关评论也会一并删除。`, '删除确认', {
    confirmButtonText: '确定删除', cancelButtonText: '取消', type: 'warning'
  })
  try {
    await request.delete(`/admin/community/posts/${row.id}`)
    ElMessage.success('帖子已删除')
    fetchPosts()
  } catch (e) {
    ElMessage.error('删除失败')
  }
}

// ======== 评论 ========
const commentList = ref([])
const commentTotal = ref(0)
const commentPage = ref(1)
const commentSize = ref(10)
const commentLoading = ref(false)
const commentPostId = ref('')

const fetchComments = async () => {
  commentLoading.value = true
  try {
    const params = { page: commentPage.value, size: commentSize.value }
    if (commentPostId.value) params.post_id = commentPostId.value
    const res = await request.get('/admin/community/comments', { params })
    commentList.value = res?.list || []
    commentTotal.value = res?.total || 0
  } catch (e) {
    ElMessage.error('获取评论列表失败')
  } finally {
    commentLoading.value = false
  }
}

const deleteComment = async (row) => {
  await ElMessageBox.confirm('确定删除该评论吗？', '删除确认', {
    confirmButtonText: '确定删除', cancelButtonText: '取消', type: 'warning'
  })
  try {
    await request.delete(`/admin/community/comments/${row.id}`)
    ElMessage.success('评论已删除')
    fetchComments()
  } catch (e) {
    ElMessage.error('删除失败')
  }
}

onMounted(fetchPosts)
</script>

<style scoped>
.community-admin-dark {
  width: 100%;
}

.page-title {
  margin: 0 0 20px 0;
  font-size: 28px;
  font-weight: 700;
  color: var(--tm-text-primary);
  letter-spacing: 0.5px;
}

.tabs-card {
  background: var(--tm-card-bg);
  border-radius: 12px;
  padding: 0 16px;
  margin-bottom: 20px;
  border: var(--tm-card-border);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
}

.dark-tabs :deep(.el-tabs__header) {
  border-bottom: 1px solid var(--tm-border-light);
}

.dark-tabs :deep(.el-tabs__nav-wrap::after) {
  background-color: var(--tm-border-light);
}

.dark-tabs :deep(.el-tabs__item) {
  color: var(--tm-text-secondary);
}

.dark-tabs :deep(.el-tabs__item.is-active) {
  color: var(--tm-color-primary);
}

.dark-tabs :deep(.el-tabs__active-bar) {
  background-color: var(--tm-color-primary);
}

.content-card {
  background: var(--tm-card-bg);
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 20px;
  border: var(--tm-card-border);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
}

.toolbar {
  margin-bottom: 16px;
}

.toolbar-left {
  display: flex;
  gap: 12px;
  align-items: center;
  flex-wrap: wrap;
}

.search-input {
  width: 220px;
}

.search-input :deep(.el-input__wrapper) {
  background: var(--tm-card-bg);
  box-shadow: 0 0 0 1px var(--tm-border-light) inset;
  border-radius: 8px;
}

.search-input :deep(.el-input__inner) {
  color: var(--tm-text-primary);
}

.filter-select {
  width: 140px;
}

.filter-select :deep(.el-input__wrapper) {
  background: var(--tm-card-bg);
  box-shadow: 0 0 0 1px var(--tm-border-light) inset;
}

.btn-search {
  color: var(--tm-color-primary);
  border: 1px solid var(--tm-color-primary);
  background: transparent;
}

.btn-search:hover {
  background: rgba(var(--tm-color-primary), 0.1);
}

.pagination-wrapper {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}

.dark-table :deep(.el-table) {
  background: transparent;
  color: var(--tm-text-primary);
}

.dark-table :deep(.el-table tr) {
  background: var(--tm-card-bg);
}

.dark-table :deep(.el-table th) {
  background: var(--tm-card-bg);
  color: var(--tm-text-secondary);
}

.dark-table :deep(.el-table td) {
  border-bottom: 1px solid var(--tm-border-light);
  color: var(--tm-text-primary);
}

.dark-table :deep(.el-table--border) {
  border-color: var(--tm-border-light);
}

.dark-table :deep(.el-table__row:hover > td) {
  background-color: rgba(var(--tm-color-primary), 0.08);
}

.dark-pagination :deep(.el-pagination) {
  color: var(--tm-text-secondary);
}

.dark-pagination :deep(.el-pagination button) {
  background: var(--tm-card-bg);
  border-color: var(--tm-border-light);
  color: var(--tm-text-secondary);
}

.dark-pagination :deep(.el-pagination .el-pager li) {
  color: var(--tm-text-secondary);
}

.dark-pagination :deep(.el-pagination .el-pager li.active) {
  color: var(--tm-color-primary);
  background: rgba(var(--tm-color-primary), 0.1);
}

.dark-pagination :deep(.el-pagination .el-pager li:hover) {
  color: var(--tm-color-primary);
}
</style>
