<template>
  <div class="tools-page">
    <div class="container">
      <h2>测试工具导航</h2>
      <p class="subtitle">精选软件测试常用工具，按分类整理</p>

      <div class="categories">
        <div v-for="cat in categories" :key="cat.id" class="category-card">
          <div class="cat-header">
            <span class="cat-name">{{ cat.name }}</span>
            <span class="cat-count">{{ cat.tools.length }} 个工具</span>
          </div>
          <div class="tools-grid">
            <a
              v-for="tool in cat.tools"
              :key="tool.name"
              :href="tool.url"
              target="_blank"
              class="tool-card"
              rel="noopener"
            >
              <div class="tool-header">
                <span class="tool-name">{{ tool.name }}</span>
                <el-tag size="small" :type="levelType(tool.level)">{{ tool.level }}</el-tag>
              </div>
              <p class="tool-desc">{{ tool.desc }}</p>
            </a>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import autoTestRequest from '@/utils/autoTestRequest'

const categories = ref([])

const levelType = (level) => {
  const map = { '入门': 'success', '进阶': 'warning', '专家': 'danger' }
  return map[level] || 'info'
}

onMounted(async () => {
  try {
    const res = await autoTestRequest.get('/v1/tools/categories')
    categories.value = res.categories || []
  } catch (e) {
    console.error(e)
  }
})
</script>

<style scoped>
.tools-page { min-height: 80vh; padding: 40px 0; background: var(--tm-bg); }
.container { max-width: 1100px; margin: 0 auto; padding: 0 20px; }
h2 { color: var(--tm-text-primary); margin-bottom: 8px; }
.subtitle { color: #909399; margin-bottom: 30px; }
.categories { display: flex; flex-direction: column; gap: 24px; }
.category-card { background: var(--tm-card-bg); border: 1px solid var(--tm-border); border-radius: 10px; padding: 20px; }
.cat-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.cat-name { font-size: 17px; font-weight: 600; color: var(--tm-text-primary); }
.cat-count { font-size: 13px; color: #909399; }
.tools-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 12px; }
.tool-card {
  display: block; padding: 14px; border: 1px solid #ebeef5; border-radius: 8px;
  text-decoration: none; color: inherit; transition: all .2s;
}
.tool-card:hover { border-color: #409EFF; box-shadow: 0 2px 8px rgba(64,158,255,.1); transform: translateY(-1px); }
.tool-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.tool-name { font-weight: 600; font-size: 14px; color: var(--tm-text-primary); }
.tool-desc { font-size: 12px; color: #909399; line-height: 1.5; margin: 0; }
</style>
