<template>
  <el-popover
    :visible="visible"
    placement="bottom-end"
    :width="380"
    trigger="click"
    @show="fetchNotifications"
    @hide="visible = false"
  >
    <template #reference>
      <el-badge :value="unreadCount" :hidden="unreadCount === 0" :max="99" class="notification-bell">
        <el-button link @click="visible = !visible" class="bell-btn">
          <el-icon :size="20"><Bell /></el-icon>
        </el-button>
      </el-badge>
    </template>

    <div class="notification-panel">
      <div class="panel-header">
        <span class="panel-title">通知消息</span>
        <el-button
          v-if="unreadCount > 0"
          type="primary"
          link
          size="small"
          @click="readAll"
        >全部已读</el-button>
      </div>

      <div class="panel-body" v-loading="loading">
        <template v-if="notifications.length > 0">
          <div
            v-for="item in notifications"
            :key="item.id"
            class="notif-item"
            :class="{ unread: !item.is_read }"
            @click="handleClick(item)"
          >
            <div class="notif-icon">
              <el-tag :type="getIconType(item.type)" size="small" effect="plain">
                {{ item.type_label }}
              </el-tag>
            </div>
            <div class="notif-content">
              <div class="notif-title">{{ item.title }}</div>
              <div class="notif-text" v-if="item.content">{{ item.content }}</div>
              <div class="notif-time">{{ formatTime(item.created_at) }}</div>
            </div>
            <div v-if="!item.is_read" class="unread-dot"></div>
          </div>
        </template>
        <el-empty v-else description="暂无通知" :image-size="60" />
      </div>

      <div class="panel-footer" v-if="total > notifications.length">
        <el-button type="primary" link size="small" @click="$router.push('/notifications')">
          查看全部 {{ total }} 条通知
        </el-button>
      </div>
    </div>
  </el-popover>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { Bell } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import autoTestRequest from '@/utils/autoTestRequest'

const router = useRouter()
const visible = ref(false)
const loading = ref(false)
const notifications = ref([])
const unreadCount = ref(0)
const total = ref(0)

const fetchNotifications = async () => {
  loading.value = true
  try {
    const res = await autoTestRequest.get('/v1/notifications', { params: { page_size: 5 } })
    notifications.value = res.notifications || []
    total.value = res.total || 0
  } catch (e) {
    console.error('获取通知失败', e)
  } finally {
    loading.value = false
  }
}

const fetchUnreadCount = async () => {
  try {
    const res = await autoTestRequest.get('/v1/notifications/unread-count')
    unreadCount.value = res.unread_count || 0
  } catch (e) {
    // silent
  }
}

const readAll = async () => {
  try {
    await autoTestRequest.post('/v1/notifications/read-all')
    unreadCount.value = 0
    notifications.value.forEach(n => n.is_read = true)
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
      unreadCount.value = Math.max(0, unreadCount.value - 1)
    } catch (e) { /* silent */ }
  }
  if (item.link) {
    visible.value = false
    router.push(item.link)
  }
}

const getIconType = (type) => {
  const map = { reply: '', exam_start: 'warning', exam_deadline: 'danger', project_feedback: 'success', achievement: 'success', system: 'info', learning_reminder: 'warning' }
  return map[type] || 'info'
}

const formatTime = (t) => {
  if (!t) return ''
  const d = new Date(t)
  const now = new Date()
  const diff = now - d
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
  if (diff < 604800000) return `${Math.floor(diff / 86400000)}天前`
  return d.toLocaleDateString()
}

let pollTimer = null

onMounted(() => {
  fetchUnreadCount()
  pollTimer = setInterval(fetchUnreadCount, 30000)
})

onBeforeUnmount(() => {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
})
</script>

<style scoped>
.notification-bell { cursor: pointer; }
.bell-btn { font-size: 20px; color: #606266; padding: 4px; }
.bell-btn:hover { color: #409EFF; }

.notification-panel { max-height: 480px; display: flex; flex-direction: column; }
.panel-header {
  display: flex; justify-content: space-between; align-items: center;
  padding-bottom: 12px; border-bottom: 1px solid #ebeef5; margin-bottom: 8px;
}
.panel-title { font-size: 15px; font-weight: 600; }

.panel-body { flex: 1; overflow-y: auto; max-height: 360px; }

.notif-item {
  display: flex; align-items: flex-start; gap: 10px;
  padding: 10px 8px; border-radius: 6px; cursor: pointer;
  position: relative; transition: background .2s;
}
.notif-item:hover { background: #f5f7fa; }
.notif-item.unread { background: #ecf5ff; }
.notif-icon { flex-shrink: 0; margin-top: 2px; }
.notif-content { flex: 1; min-width: 0; }
.notif-title { font-size: 13px; font-weight: 500; color: #303133; }
.notif-text { font-size: 12px; color: #909399; margin-top: 3px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.notif-time { font-size: 11px; color: #c0c4cc; margin-top: 4px; }
.unread-dot { width: 8px; height: 8px; border-radius: 50%; background: #f56c6c; flex-shrink: 0; margin-top: 6px; }

.panel-footer { text-align: center; padding-top: 10px; border-top: 1px solid #ebeef5; margin-top: 8px; }
</style>
