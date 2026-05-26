<template>
  <div class="notifications-page">
    <div class="container">
      <div class="page-header">
        <h2>通知消息</h2>
        <el-button v-if="unreadTotal > 0" type="primary" size="small" @click="readAll">全部已读</el-button>
      </div>

      <div class="notif-list" v-loading="loading">
        <template v-if="notifications.length > 0">
          <div
            v-for="item in notifications"
            :key="item.id"
            class="notif-card"
            :class="{ unread: !item.is_read }"
            @click="handleClick(item)"
          >
            <el-tag :type="tagType(item.type)" size="small" effect="plain">{{ item.type_label }}</el-tag>
            <div class="notif-body">
              <div class="notif-title">{{ item.title }}</div>
              <div class="notif-text" v-if="item.content">{{ item.content }}</div>
              <div class="notif-time">{{ formatTime(item.created_at) }}</div>
            </div>
            <div v-if="!item.is_read" class="unread-dot"></div>
          </div>
        </template>
        <el-empty v-else description="暂无通知" />
      </div>

      <div class="pagination-wrap" v-if="total > pageSize">
        <el-pagination
          v-model:current-page="page"
          :page-size="pageSize"
          :total="total"
          layout="prev, pager, next"
          @current-change="load"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import autoTestRequest from '@/utils/autoTestRequest'

const router = useRouter()
const loading = ref(false)
const notifications = ref([])
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const unreadTotal = ref(0)

const load = async () => {
  loading.value = true
  try {
    const res = await autoTestRequest.get('/v1/notifications', { params: { page: page.value, page_size: pageSize.value } })
    notifications.value = res.notifications || []
    total.value = res.total || 0
    unreadTotal.value = (res.notifications || []).filter(n => !n.is_read).length
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const readAll = async () => {
  try {
    await autoTestRequest.post('/v1/notifications/read-all')
    notifications.value.forEach(n => n.is_read = true)
    unreadTotal.value = 0
    ElMessage.success('已全部标记为已读')
  } catch (e) {
    ElMessage.error('操作失败')
  }
}

const handleClick = async (item) => {
  if (!item.is_read) {
    try {
      await autoTestRequest.post(`/v1/notifications/${item.id}/read`)
      item.is_read = true
      unreadTotal.value = Math.max(0, unreadTotal.value - 1)
    } catch (e) { /* silent */ }
  }
  if (item.link) router.push(item.link)
}

const tagType = (t) => {
  const m = { reply: '', exam_start: 'warning', exam_deadline: 'danger', project_feedback: 'success', achievement: 'success', system: 'info' }
  return m[t] || 'info'
}

const formatTime = (t) => {
  if (!t) return ''
  const d = new Date(t), now = new Date(), diff = now - d
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
  return d.toLocaleDateString()
}

onMounted(() => load())
</script>

<style scoped>
.notifications-page { min-height: 80vh; padding: 40px 0; background: var(--tm-bg); }
.container { max-width: 800px; margin: 0 auto; padding: 0 20px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; }
.page-header h2 { font-size: 22px; color: var(--tm-text-primary); }
.notif-list { display: flex; flex-direction: column; gap: 8px; }
.notif-card {
  display: flex; align-items: flex-start; gap: 14px;
  padding: 16px; background: var(--tm-card-bg); border-radius: 8px;
  cursor: pointer; position: relative; border: 1px solid var(--tm-border);
  transition: all .2s;
}
.notif-card:hover { box-shadow: 0 2px 8px rgba(0,0,0,.06); }
.notif-card.unread { border-left: 3px solid #409EFF; background: #ecf5ff; }
.notif-body { flex: 1; min-width: 0; }
.notif-title { font-size: 14px; font-weight: 600; color: var(--tm-text-primary); }
.notif-text { font-size: 13px; color: var(--tm-text-secondary); margin-top: 4px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.notif-time { font-size: 12px; color: #c0c4cc; margin-top: 6px; }
.unread-dot { width: 10px; height: 10px; border-radius: 50%; background: #f56c6c; flex-shrink: 0; margin-top: 5px; }
.pagination-wrap { display: flex; justify-content: center; margin-top: 24px; }
</style>
