<template>
  <div class="favorites-page">
    <div class="container">
      <h2>我的收藏</h2>
      <el-tabs v-model="activeTab" @tab-change="load">
        <el-tab-pane label="全部" name="" />
        <el-tab-pane label="帖子" name="post" />
        <el-tab-pane label="习题" name="exercise" />
        <el-tab-pane label="笔记" name="note" />
      </el-tabs>

      <div class="fav-list" v-loading="loading">
        <template v-if="items.length > 0">
          <div
            v-for="item in items"
            :key="item.id"
            class="fav-item"
            @click="goTo(item)"
          >
            <el-tag size="small" :type="typeTag(item.type)">{{ typeLabel(item.type) }}</el-tag>
            <span class="title">{{ item.data?.title }}</span>
            <span class="meta">{{ item.data?.summary || '' }}</span>
            <el-button link type="danger" size="small" @click.stop="removeFav(item)">取消收藏</el-button>
          </div>
        </template>
        <el-empty v-else description="暂无收藏" />
      </div>

      <div class="pagination-wrap" v-if="total > 20">
        <el-pagination v-model:current-page="page" :page-size="20" :total="total" @current-change="load" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import autoTestRequest from '@/utils/autoTestRequest'

const router = useRouter()
const activeTab = ref('')
const loading = ref(false)
const items = ref([])
const total = ref(0)
const page = ref(1)

const load = async () => {
  loading.value = true
  try {
    const params = { page: page.value, page_size: 20 }
    if (activeTab.value) params.item_type = activeTab.value
    const res = await autoTestRequest.get('/v1/favorites', { params })
    items.value = res.items || []
    total.value = res.total || 0
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const typeLabel = (t) => ({ post: '帖子', exercise: '习题', note: '笔记' }[t] || t)
const typeTag = (t) => ({ post: 'success', exercise: 'primary', note: 'warning' }[t] || 'info')

const goTo = (item) => {
  const routes = { post: `/community/post/${item.data?.id}`, exercise: `/exercises/${item.data?.id}`, note: '' }
  const path = routes[item.type]
  if (path) router.push(path)
}

const removeFav = async (item) => {
  try {
    await autoTestRequest.post('/v1/favorites/toggle', { type: item.type, item_id: item.data?.id })
    ElMessage.success('已取消收藏')
    load()
  } catch (e) {
    ElMessage.error('操作失败')
  }
}

load()
</script>

<style scoped>
.favorites-page { min-height: 80vh; padding: 40px 0; background: var(--tm-bg); }
.container { max-width: 800px; margin: 0 auto; padding: 0 20px; }
h2 { color: var(--tm-text-primary); margin-bottom: 16px; }
.fav-item {
  display: flex; align-items: center; gap: 12px;
  padding: 14px 16px; background: var(--tm-card-bg); border: 1px solid var(--tm-border);
  border-radius: 8px; margin-bottom: 8px; cursor: pointer; transition: all .2s;
}
.fav-item:hover { box-shadow: 0 2px 8px rgba(0,0,0,.06); border-color: #409EFF; }
.fav-item .title { flex: 1; font-size: 14px; font-weight: 500; color: var(--tm-text-primary); }
.fav-item .meta { font-size: 12px; color: #909399; max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.pagination-wrap { display: flex; justify-content: center; margin-top: 20px; }
</style>
