﻿<template>
  <div class="post-detail">
    <div class="container">
      <div class="back-btn" @click="goBack">
        <el-icon><ArrowLeft /></el-icon>
        返回列表
      </div>

      <div v-if="post" class="post-container">
        <!-- 帖子内容 -->
        <div class="post-content">
          <div class="post-header">
            <h1 class="post-title">{{ post.title }}</h1>
            <div class="post-meta">
              <div class="meta-left">
                <el-avatar :size="40" style="margin-right: 12px;">
                  {{ post.author.username.charAt(0).toUpperCase() }}
                </el-avatar>
                <div>
                  <div class="author-name">{{ post.author.username }}</div>
                  <div class="post-time">{{ post.created_at }}</div>
                </div>
              </div>
              <div class="meta-right">
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
          </div>
          
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
          
          <div class="post-body">
            <div class="markdown-content" v-html="renderMarkdown(post.content)"></div>
          </div>
          
          <div class="post-actions">
            <el-button 
              :type="post.is_liked ? 'danger' : 'default'" 
              @click="toggleLike"
              :icon="StarFilled"
            >
              {{ post.like_count }} 点赞
            </el-button>
            <el-button 
              :type="post.is_favorited ? 'warning' : 'default'" 
              @click="toggleFavorite"
              :icon="StarFilled"
            >
              {{ post.is_favorited ? '已收藏' : '收藏' }}
            </el-button>
            <el-button type="default" @click="scrollToComment" :icon="ChatDotRound">
              {{ post.comment_count }} 评论
            </el-button>
            <el-button type="default" :icon="Share">
              分享
            </el-button>
          </div>
        </div>

        <!-- 评论区域 -->
        <div class="comment-section" id="comment-section">
          <h3 class="section-title">评论 ({{ post.comment_count }})</h3>
          
          <!-- 发表评论 -->
          <div class="comment-input">
            <el-avatar :size="36" style="margin-right: 12px;">
              U
            </el-avatar>
            <div class="input-area">
              <el-input
                v-model="commentContent"
                type="textarea"
                :rows="3"
                placeholder="写下你的评论..."
                maxlength="1000"
                show-word-limit
              />
              <div class="input-actions">
                <el-button 
                  type="primary" 
                  @click="submitComment" 
                  :loading="submittingComment"
                  size="small"
                >
                  发表评论
                </el-button>
              </div>
            </div>
          </div>

          <!-- 评论列表 -->
          <div class="comment-list">
            <div class="comment-item" v-for="comment in comments" :key="comment.id">
              <div class="comment-header">
                <el-avatar :size="36" style="margin-right: 12px;">
                  {{ comment.author.username.charAt(0).toUpperCase() }}
                </el-avatar>
                <div class="comment-info">
                  <div class="comment-author">{{ comment.author.username }}</div>
                  <div class="comment-time">{{ comment.created_at }}</div>
                </div>
                <div class="comment-actions">
                  <div 
                    class="action-item" 
                    :class="{ active: comment.is_liked }"
                    @click="toggleCommentLike(comment)"
                  >
                    <el-icon size="14"><StarFilled /></el-icon>
                    <span>{{ comment.like_count }}</span>
                  </div>
                  <div class="action-item" @click="showReplyBox(comment)">
                    <el-icon size="14"><ChatDotRound /></el-icon>
                    <span>回复</span>
                  </div>
                </div>
              </div>
              
              <div class="comment-content">
                <p>{{ comment.content }}</p>
              </div>
              
              <!-- 回复输入�?-->
              <div class="reply-input" v-if="replyToComment === comment.id">
                <el-input
                  v-model="replyContent"
                  type="textarea"
                  :rows="2"
                  placeholder="写下你的回复..."
                  size="small"
                />
                <div class="reply-actions">
                  <el-button size="small" @click="replyToComment = null">取消</el-button>
                  <el-button 
                    type="primary" 
                    size="small" 
                    @click="submitReply(comment)"
                    :loading="submittingReply"
                  >
                    回复
                  </el-button>
                </div>
              </div>
              
              <!-- 回复列表 -->
              <div class="reply-list" v-if="comment.replies.length > 0">
                <div class="reply-item" v-for="reply in comment.replies" :key="reply.id">
                  <div class="reply-header">
                    <el-avatar :size="28" style="margin-right: 8px;">
                      {{ reply.author.username.charAt(0).toUpperCase() }}
                    </el-avatar>
                    <div class="reply-info">
                      <span class="reply-author">{{ reply.author.username }}</span>
                      <span class="reply-time">{{ reply.created_at }}</span>
                    </div>
                    <div class="reply-actions">
                      <div 
                        class="action-item" 
                        :class="{ active: reply.is_liked }"
                        @click="toggleCommentLike(reply)"
                      >
                        <el-icon size="12"><StarFilled /></el-icon>
                        <span>{{ reply.like_count }}</span>
                      </div>
                    </div>
                  </div>
                  <div class="reply-content">
                    <p>{{ reply.content }}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div class="empty-state" v-if="comments.length === 0 && !loadingComments">
            <el-empty description="暂无评论，快来抢沙发吧~" :image-size="80" />
          </div>
        </div>
      </div>

      <div class="loading-state" v-if="loading">
        <el-skeleton :rows="10" animated />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { 
  ArrowLeft, StarFilled, ChatDotRound, Share 
} from '@element-plus/icons-vue'
import request from '@/utils/request'
import { renderMarkdown } from '@/utils/markdown'

const router = useRouter()
const route = useRoute()
const postId = route.params.id

const post = ref(null)
const comments = ref([])
const loading = ref(false)
const loadingComments = ref(false)
const commentContent = ref('')
const replyContent = ref('')
const submittingComment = ref(false)
const submittingReply = ref(false)
const replyToComment = ref(null)


onMounted(() => {
  fetchPostDetail()
  fetchComments()
})

const fetchPostDetail = async () => {
  loading.value = true
  try {
    const res = await request.get(`/community/posts/${postId}`)
    post.value = res
  } catch (error) {
    console.error('获取帖子详情失败:', error)
    ElMessage.error('获取帖子详情失败')
  } finally {
    loading.value = false
  }
}

const fetchComments = async () => {
  loadingComments.value = true
  try {
    const res = await request.get(`/community/posts/${postId}/comments`)
    comments.value = res
  } catch (error) {
    console.error('获取评论失败:', error)
  } finally {
    loadingComments.value = false
  }
}

const goBack = () => {
  router.back()
}

const toggleLike = async () => {
  if (!post.value) return
  
  try {
    const res = await request.post(`/community/posts/${post.value.id}/like`)
    post.value.like_count = res.like_count
    post.value.is_liked = res.action === 'liked'
    ElMessage.success(res.message)
  } catch (error) {
    console.error('点赞失败:', error)
    ElMessage.error('操作失败')
  }
}

const toggleFavorite = async () => {
  if (!post.value) return
  
  try {
    const res = await request.post(`/community/posts/${post.value.id}/favorite`)
    post.value.is_favorited = res.action === 'favorited'
    ElMessage.success(res.message)
  } catch (error) {
    console.error('收藏失败:', error)
    ElMessage.error('操作失败')
  }
}

const scrollToComment = () => {
  document.getElementById('comment-section')?.scrollIntoView({ behavior: 'smooth' })
}

const submitComment = async () => {
  if (!commentContent.value.trim()) {
    ElMessage.warning('请输入评论内容')
    return
  }
  
  submittingComment.value = true
  try {
    await request.post(`/community/posts/${postId}/comments`, {
      content: commentContent.value.trim()
    })
    ElMessage.success('评论发表成功')
    commentContent.value = ''
    post.value.comment_count += 1
    // 刷新评论列表
    fetchComments()
  } catch (error) {
    console.error('发表评论失败:', error)
    ElMessage.error('发表失败，请稍后重试')
  } finally {
    submittingComment.value = false
  }
}

const showReplyBox = (comment) => {
  replyToComment.value = replyToComment.value === comment.id ? null : comment.id
  replyContent.value = ''
}

const submitReply = async (comment) => {
  if (!replyContent.value.trim()) {
    ElMessage.warning('请输入回复内容')
    return
  }
  
  submittingReply.value = true
  try {
    await request.post(`/community/posts/${postId}/comments`, {
      content: replyContent.value.trim(),
      parent_id: comment.id
    })
    ElMessage.success('回复成功')
    replyToComment.value = null
    replyContent.value = ''
    post.value.comment_count += 1
    // 刷新评论列表
    fetchComments()
  } catch (error) {
    console.error('回复失败:', error)
    ElMessage.error('回复失败，请稍后重试')
  } finally {
    submittingReply.value = false
  }
}

const toggleCommentLike = async (comment) => {
  try {
    const res = await request.post(`/community/comments/${comment.id}/like`)
    comment.like_count = res.like_count
    comment.is_liked = res.action === 'liked'
  } catch (error) {
    console.error('点赞失败:', error)
    ElMessage.error('操作失败')
  }
}
</script>

<style scoped>
.post-detail {
  padding: 30px 0;
  min-height: calc(100vh - 60px);
  background-color: var(--tm-bg-elevated);
}

.container {
  max-width: 1000px;
  margin: 0 auto;
  padding: 0 20px;
}

.back-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: #18181B;
  border-radius: 8px;
  margin-bottom: 20px;
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 14px;
  color: var(--tm-text-regular);
  box-shadow: 0 2px 8px 0 rgba(0, 0, 0, 0.08);
}

.back-btn:hover {
  color: #409eff;
  transform: translateX(-4px);
}

.post-container {
  background: #18181B;
  border-radius: 12px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.post-content {
  padding: 40px;
  border-bottom: 1px solid #f0f2f5;
}

.post-header {
  margin-bottom: 24px;
}

.post-title {
  font-size: 28px;
  font-weight: bold;
  color: var(--tm-text-primary);
  margin: 0 0 20px 0;
  line-height: 1.6;
}

.post-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 20px;
  border-bottom: 1px solid #f0f2f5;
}

.meta-left {
  display: flex;
  align-items: center;
}

.author-name {
  font-size: 16px;
  font-weight: 500;
  color: var(--tm-text-primary);
  margin-bottom: 4px;
}

.post-time {
  font-size: 12px;
  color: var(--tm-text-secondary);
}

.meta-right {
  display: flex;
  gap: 8px;
}

.post-tags {
  display: flex;
  gap: 8px;
  margin-bottom: 24px;
  flex-wrap: wrap;
}

.post-body {
  margin-bottom: 32px;
  line-height: 2;
  font-size: 15px;
  color: var(--tm-text-primary);
}

.post-actions {
  display: flex;
  gap: 16px;
  border-top: 1px solid #f0f2f5;
  padding-top: 24px;
}

.comment-section {
  padding: 40px;
}

.section-title {
  font-size: 20px;
  font-weight: bold;
  color: var(--tm-text-primary);
  margin: 0 0 24px 0;
}

.comment-input {
  display: flex;
  margin-bottom: 32px;
}

.input-area {
  flex: 1;
}

.input-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 12px;
}

.comment-list {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.comment-item {
  padding-bottom: 24px;
  border-bottom: 1px solid #f0f2f5;
}

.comment-item:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.comment-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.comment-info {
  flex: 1;
}

.comment-author {
  font-size: 14px;
  font-weight: 500;
  color: var(--tm-text-primary);
  margin-bottom: 4px;
}

.comment-time {
  font-size: 12px;
  color: var(--tm-text-secondary);
}

.comment-actions {
  display: flex;
  gap: 16px;
}

.action-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: var(--tm-text-secondary);
  cursor: pointer;
  transition: all 0.3s ease;
}

.action-item:hover {
  color: #f56c6c;
}

.action-item.active {
  color: #f56c6c;
}

.comment-content {
  margin-left: 48px;
  margin-bottom: 12px;
  line-height: 1.8;
  color: var(--tm-text-primary);
}

.reply-input {
  margin-left: 48px;
  margin-bottom: 12px;
}

.reply-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 8px;
}

.reply-list {
  margin-left: 48px;
  margin-top: 12px;
  padding-left: 16px;
  border-left: 2px solid #f0f2f5;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.reply-header {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
}

.reply-info {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 12px;
}

.reply-author {
  font-size: 13px;
  font-weight: 500;
  color: var(--tm-text-primary);
}

.reply-time {
  font-size: 11px;
  color: var(--tm-text-secondary);
}

.reply-actions {
  display: flex;
  gap: 12px;
}

.reply-content {
  font-size: 13px;
  line-height: 1.8;
  color: var(--tm-text-regular);
}

.empty-state {
  padding: 40px 0;
}

.loading-state {
  background: #18181B;
  padding: 40px;
  border-radius: 12px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

/* Markdown样式 */
.markdown-content {
  line-height: 2;
}

.markdown-content h1,
.markdown-content h2,
.markdown-content h3,
.markdown-content h4,
.markdown-content h5,
.markdown-content h6 {
  margin: 24px 0 16px 0;
  font-weight: bold;
  color: var(--tm-text-primary);
  line-height: 1.5;
}

.markdown-content h1 {
  font-size: 24px;
  border-bottom: 1px solid var(--tm-border-color);
  padding-bottom: 8px;
}

.markdown-content h2 {
  font-size: 20px;
  border-bottom: 1px solid var(--tm-border-color);
  padding-bottom: 8px;
}

.markdown-content h3 {
  font-size: 18px;
}

.markdown-content h4 {
  font-size: 16px;
}

.markdown-content p {
  margin: 12px 0;
}

.markdown-content ul,
.markdown-content ol {
  margin: 12px 0;
  padding-left: 24px;
}

.markdown-content li {
  margin: 8px 0;
}

.markdown-content code {
  background: var(--tm-bg-elevated);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 13px;
  color: #e6a23c;
}

.markdown-content pre {
  background: #282c34;
  padding: 16px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 16px 0;
}

.markdown-content pre code {
  background: none;
  padding: 0;
  color: #abb2bf;
  line-height: 1.6;
}

.markdown-content blockquote {
  border-left: 4px solid #409eff;
  padding-left: 16px;
  margin: 16px 0;
  color: var(--tm-text-regular);
  background: var(--tm-bg-elevated);
  padding: 12px 16px;
  border-radius: 0 8px 8px 0;
}

.markdown-content table {
  border-collapse: collapse;
  width: 100%;
  margin: 16px 0;
}

.markdown-content th,
.markdown-content td {
  border: 1px solid var(--tm-border-color);
  padding: 8px 12px;
  text-align: left;
}

.markdown-content th {
  background: var(--tm-bg-elevated);
  font-weight: bold;
}

.markdown-content img {
  max-width: 100%;
  border-radius: 8px;
  margin: 16px 0;
}

@media (max-width: 768px) {
  .post-content, .comment-section {
    padding: 20px;
  }
  
  .post-title {
    font-size: 22px;
  }
  
  .post-actions {
    flex-wrap: wrap;
  }
}
</style>
