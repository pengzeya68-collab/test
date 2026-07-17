<template>
  <div class="search-page">
    <div class="container">
      <h2>鎼滅储 TestMaster</h2>
      <el-input
        v-model="keyword"
        placeholder="鎼滅储涔犻銆佸笘瀛愩€佽€冭瘯銆佸涔犺矾寰?.."
        size="large"
        clearable
        @keyup.enter="doSearch"
      >
        <template #prefix><el-icon><Search /></el-icon></template>
        <template #append>
          <el-button type="primary" @click="doSearch" :loading="loading">鎼滅储</el-button>
        </template>
      </el-input>

      <div class="search-tabs" v-if="results">
        <el-radio-group v-model="activeTab" size="small">
          <el-radio-button label="all">鍏ㄩ儴 ({{ total }})</el-radio-button>
          <el-radio-button label="exercises">涔犻 ({{ (results.exercises||[]).length }})</el-radio-button>
          <el-radio-button label="posts">甯栧瓙 ({{ (results.posts||[]).length }})</el-radio-button>
          <el-radio-button label="exams">鑰冭瘯 ({{ (results.exams||[]).length }})</el-radio-button>
          <el-radio-button label="paths">瀛︿範璺緞 ({{ (results.paths||[]).length }})</el-radio-button>
        </el-radio-group>
      </div>

      <div class="results" v-loading="loading">
        <div v-if="!results && !loading" class="empty-hint">杈撳叆鍏抽敭璇嶅紑濮嬫悳绱</div>
        <div v-else-if="total === 0" class="empty-hint">鏈壘鍒扮浉鍏崇粨鏋</div>

        <template v-if="results">
          <template v-if="activeTab === 'all' || activeTab === 'exercises'">
            <div v-for="item in results.exercises" :key="'e'+item.id" class="result-item" @click="$router.push(`/exercises/${item.id}`)">
              <el-tag size="small" type="primary">涔犻</el-tag>
              <span class="title">{{ item.title }}</span>
              <span class="meta">闅惧害: {{ item.difficulty }} | {{ item.knowledge_point }}</span>
            </div>
          </template>
          <template v-if="activeTab === 'all' || activeTab === 'posts'">
            <div v-for="item in results.posts" :key="'p'+item.id" class="result-item" @click="$router.push(`/community/post/${item.id}`)">
              <el-tag size="small" type="success">甯栧瓙</el-tag>
              <span class="title">{{ item.title }}</span>
              <span class="meta">{{ item.summary || '' }}</span>
            </div>
          </template>
          <template v-if="activeTab === 'all' || activeTab === 'exams'">
            <div v-for="item in results.exams" :key="'ex'+item.id" class="result-item" @click="$router.push(`/exam/${item.id}`)">
              <el-tag size="small" type="warning">鑰冭瘯</el-tag>
              <span class="title">{{ item.title }}</span>
              <span class="meta">闅惧害: {{ item.difficulty }}</span>
            </div>
          </template>
          <template v-if="activeTab === 'all' || activeTab === 'paths'">
            <div v-for="item in results.paths" :key="'lp'+item.id" class="result-item" @click="$router.push(`/learning-paths/${item.id}`)">
              <el-tag size="small" type="danger">瀛︿範璺緞</el-tag>
              <span class="title">{{ item.title }}</span>
              <span class="meta">闅惧害: {{ item.difficulty }}</span>
            </div>
          </template>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import { Search } from '@element-plus/icons-vue'
import { useRoute, useRouter } from 'vue-router'
import autoTestRequest from '@/utils/autoTestRequest'

const route = useRoute()
const router = useRouter()
const keyword = ref(route.query.q || '')
const loading = ref(false)
const results = ref(null)
const total = ref(0)
const activeTab = ref('all')

const doSearch = async () => {
  if (!keyword.value.trim()) return
  loading.value = true
  try {
    const res = await autoTestRequest.get('/v1/search', { params: { q: keyword.value } })
    results.value = res.results
    total.value = res.total
    router.replace({ query: { q: keyword.value } })
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

onMounted(() => { if (keyword.value) doSearch() })
</script>

<style scoped>
.search-page { min-height: 80vh; padding: 40px 0; background: var(--tm-bg); }
.container { max-width: 800px; margin: 0 auto; padding: 0 20px; }
h2 { margin-bottom: 20px; color: var(--tm-text-primary); }
.search-tabs { margin: 20px 0; }
.results { margin-top: 16px; }
.result-item {
  display: flex; align-items: center; gap: 12px;
  padding: 14px 16px; background: var(--tm-card-bg); border: 1px solid var(--tm-border);
  border-radius: 8px; margin-bottom: 8px; cursor: pointer; transition: all .2s;
}
.result-item:hover { box-shadow: 0 2px 8px rgba(0,0,0,.06); border-color: #409EFF; }
.result-item .title { flex: 1; font-size: 14px; font-weight: 500; color: var(--tm-text-primary); }
.result-item .meta { font-size: 12px; color: #909399; white-space: nowrap; }
.empty-hint { text-align: center; color: #909399; margin-top: 80px; font-size: 15px; }
</style>

