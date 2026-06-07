<template>
  <div class="api-doc-container">
    <!-- 顶部工具栏 -->
    <div class="doc-header">
      <div class="header-left">
        <el-icon class="back-icon" @click="goBack"><ArrowLeft /></el-icon>
        <h2>接口文档</h2>
        <el-tag type="success" size="small">文档即用例</el-tag>
      </div>
      <div class="header-right">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索接口..."
          prefix-icon="Search"
          clearable
          class="search-input"
          @input="handleSearch"
        />
        <el-button type="primary" @click="refreshDoc" :loading="loading">
          <el-icon><Refresh /></el-icon>
          刷新文档
        </el-button>
        <el-button @click="showShareDialog = true">
          <el-icon><Share /></el-icon>
          分享
        </el-button>
        <el-dropdown @command="handleExport">
          <el-button>
            <el-icon><Download /></el-icon>
            导出
            <el-icon><ArrowDown /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="openapi">OpenAPI 3.0</el-dropdown-item>
              <el-dropdown-item command="python">Python 代码</el-dropdown-item>
              <el-dropdown-item command="curl">cURL 命令</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>

    <div class="doc-content">
      <!-- 左侧导航 -->
      <div class="doc-nav">
        <div class="nav-header">
          <span>接口分组</span>
          <el-badge :value="apiStats?.total || 0" class="item">
            <el-icon><Document /></el-icon>
          </el-badge>
        </div>
        
        <!-- 统计信息 -->
        <div class="nav-stats" v-if="apiStats">
          <div class="stat-item">
            <span class="stat-label">接口</span>
            <span class="stat-value">{{ apiStats.total }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">有执行数据</span>
            <span class="stat-value success">{{ apiStats.cases_with_history }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">有 Mock</span>
            <span class="stat-value warning">{{ apiStats.cases_with_mock }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">性能测试</span>
            <span class="stat-value info">{{ apiStats.cases_with_performance }}</span>
          </div>
        </div>

        <!-- 分组树 -->
        <el-tree
          ref="groupTreeRef"
          :data="groupTree"
          :props="treeProps"
          node-key="id"
          default-expand-all
          @node-click="handleNodeClick"
          class="group-tree"
        >
          <template #default="{ node, data }">
            <span class="custom-tree-node">
              <el-icon v-if="data.isGroup"><Folder /></el-icon>
              <el-icon v-else><Link /></el-icon>
              <span class="node-label">{{ node.label }}</span>
              <el-tag
                v-if="data.method"
                :type="getMethodType(data.method)"
                size="small"
                class="method-tag"
              >
                {{ data.method.toUpperCase() }}
              </el-tag>
            </span>
          </template>
        </el-tree>
      </div>

      <!-- 中间详情区 -->
      <div class="doc-detail">
        <template v-if="selectedApi">
          <!-- 基本信息 -->
          <div class="api-header">
            <div class="api-title">
              <el-tag :type="getMethodType(selectedApi.method)" effect="dark" size="large">
                {{ selectedApi.method.toUpperCase() }}
              </el-tag>
              <h3>{{ selectedApi.summary || selectedApi.path }}</h3>
            </div>
            <div class="api-actions">
              <el-button type="primary" @click="debugApi">
                <el-icon><Tools /></el-icon>
                一键调试
              </el-button>
              <el-button @click="copyUrl">
                <el-icon><CopyDocument /></el-icon>
                复制 URL
              </el-button>
            </div>
          </div>

          <el-descriptions :column="2" border class="api-meta">
            <el-descriptions-item label="路径">{{ selectedApi.path }}</el-descriptions-item>
            <el-descriptions-item label="方法">{{ selectedApi.method.toUpperCase() }}</el-descriptions-item>
            <el-descriptions-item label="分组" :span="2">{{ selectedApi.group_name }}</el-descriptions-item>
            <el-descriptions-item label="描述" :span="2">{{ selectedApi.description || '暂无描述' }}</el-descriptions-item>
          </el-descriptions>

          <!-- 标签页 -->
          <el-tabs v-model="activeTab" class="api-tabs">
            <!-- 请求参数 -->
            <el-tab-pane label="请求参数" name="request">
              <div v-if="selectedApi.parameters && selectedApi.parameters.length" class="param-section">
                <h4>Query 参数</h4>
                <el-table :data="queryParams" border stripe>
                  <el-table-column prop="name" label="参数名" width="200" />
                  <el-table-column prop="type" label="类型" width="120">
                    <template #default="{ row }">
                      <el-tag size="small">{{ row.type }}</el-tag>
                    </template>
                  </el-table-column>
                  <el-table-column prop="required" label="必填" width="80">
                    <template #default="{ row }">
                      <el-tag :type="row.required ? 'danger' : 'info'" size="small">
                        {{ row.required ? '是' : '否' }}
                      </el-tag>
                    </template>
                  </el-table-column>
                  <el-table-column prop="example" label="示例值" />
                  <el-table-column prop="description" label="说明" />
                </el-table>
              </div>

              <div v-if="selectedApi.requestBody" class="body-section">
                <h4>请求体</h4>
                <div class="content-type-label">
                  Content-Type: {{ getRequestBodyContentType }}
                </div>
                <JsonEditor
                  v-model="requestBodyJson"
                  class="doc-json-editor"
                />
              </div>
            </el-tab-pane>

            <!-- 响应示例（真实数据） -->
            <el-tab-pane name="response">
              <template #label>
                <span>
                  响应示例
                  <el-badge :value="responseExamples.length" class="badge" v-if="responseExamples.length" />
                </span>
              </template>

              <el-alert
                v-if="responseExamples.length"
                title="以下响应示例来自真实执行历史"
                type="success"
                :closable="false"
                show-icon
                class="real-data-alert"
              />

              <template v-if="responseExamples.length">
                <div v-for="(example, idx) in responseExamples" :key="idx" class="response-example">
                  <div class="example-header">
                    <el-tag :type="getStatusType(example.status_code)">{{ example.status_code }}</el-tag>
                    <span class="example-status">{{ example.status }}</span>
                    <span class="example-time" v-if="example.execution_time">
                      <el-icon><Timer /></el-icon>
                      {{ example.execution_time }}ms
                    </span>
                  </div>
                  <JsonEditor
                    v-model="example.response_data"
                    class="doc-json-editor"
                  />
                </div>
              </template>

              <el-empty v-else description="暂无执行历史，运行用例后可查看真实响应" />
            </el-tab-pane>

            <!-- 代码示例 -->
            <el-tab-pane label="代码示例" name="code">
              <el-radio-group v-model="codeLang" class="code-lang-selector">
                <el-radio-button label="python">Python</el-radio-button>
                <el-radio-button label="javascript">JavaScript</el-radio-button>
                <el-radio-button label="curl">cURL</el-radio-button>
                <el-radio-button label="java">Java</el-radio-button>
              </el-radio-group>
              
              <div class="code-block">
                <div class="code-header">
                  <span>{{ codeLang }}</span>
                  <el-button text @click="copyCode">
                    <el-icon><CopyDocument /></el-icon>
                    复制
                  </el-button>
                </div>
                <pre><code>{{ generatedCode }}</code></pre>
              </div>
            </el-tab-pane>

            <!-- 关联数据 -->
            <el-tab-pane name="related">
              <template #label>
                <span>
                  关联
                  <el-badge :value="relatedCount" class="badge" v-if="relatedCount" />
                </span>
              </template>

              <!-- Mock 服务 -->
              <div v-if="selectedApi['x-testmaster']?.mock" class="related-section">
                <h4><el-icon><Connection /></el-icon> Mock 服务</h4>
                <el-card shadow="never">
                  <div class="mock-info">
                    <p><strong>项目:</strong> {{ selectedApi['x-testmaster'].mock.project_name }}</p>
                    <p><strong>规则:</strong> {{ selectedApi['x-testmaster'].mock.rule_name }}</p>
                    <p><strong>Mock URL:</strong></p>
                    <code class="mock-url">{{ selectedApi['x-testmaster'].mock.mock_url }}</code>
                  </div>
                </el-card>
              </div>

              <!-- 场景流程 -->
              <div v-if="selectedApi['x-testmaster']?.scenarios?.length" class="related-section">
                <h4><el-icon><Share /></el-icon> 所属场景流程</h4>
                <el-card v-for="scenario in selectedApi['x-testmaster'].scenarios" :key="scenario.id" shadow="never" class="scenario-card">
                  <div class="scenario-header">
                    <strong>{{ scenario.name }}</strong>
                    <el-tag size="small">步骤 {{ scenario.step_order + 1 }}</el-tag>
                  </div>
                  <p v-if="scenario.description">{{ scenario.description }}</p>
                  <el-button text type="primary" @click="goToScenario(scenario.id)">
                    查看场景
                  </el-button>
                </el-card>
              </div>

              <!-- 性能指标 -->
              <div v-if="selectedApi['x-testmaster']?.performance" class="related-section">
                <h4><el-icon><TrendCharts /></el-icon> 性能指标</h4>
                <el-row :gutter="16">
                  <el-col :span="8" v-for="metric in performanceMetrics" :key="metric.label">
                    <el-card shadow="never" class="metric-card">
                      <div class="metric-value">{{ metric.value }}</div>
                      <div class="metric-label">{{ metric.label }}</div>
                    </el-card>
                  </el-col>
                </el-row>
              </div>

              <!-- 全局变量引用 -->
              <div v-if="selectedApi['x-testmaster']?.global_variables?.length" class="related-section">
                <h4><el-icon><Key /></el-icon> 引用的全局变量</h4>
                <el-table :data="selectedApi['x-testmaster'].global_variables" border>
                  <el-table-column prop="name" label="变量名" width="200">
                    <template #default="{ row }">
                      <code>${{ row.name }}</code>
                    </template>
                  </el-table-column>
                  <el-table-column prop="description" label="描述" />
                  <el-table-column prop="is_encrypted" label="类型" width="100">
                    <template #default="{ row }">
                      <el-tag :type="row.is_encrypted ? 'warning' : 'info'" size="small">
                        {{ row.is_encrypted ? '加密' : '明文' }}
                      </el-tag>
                    </template>
                  </el-table-column>
                </el-table>
              </div>

              <el-empty v-if="!relatedCount" description="暂无关联数据" />
            </el-tab-pane>
          </el-tabs>
        </template>

        <el-empty v-else description="请从左侧选择接口" />
      </div>

      <!-- 右侧快速导航 -->
      <div class="doc-toc" v-if="selectedApi">
        <div class="toc-title">快速导航</div>
        <ul class="toc-list">
          <li @click="scrollTo('request')" :class="{ active: activeTab === 'request' }">请求参数</li>
          <li @click="scrollTo('response')" :class="{ active: activeTab === 'response' }">响应示例</li>
          <li @click="scrollTo('code')" :class="{ active: activeTab === 'code' }">代码示例</li>
          <li @click="scrollTo('related')" :class="{ active: activeTab === 'related' }">关联数据</li>
        </ul>
      </div>
    </div>

    <!-- 分享对话框 -->
    <el-dialog v-model="showShareDialog" title="分享文档" width="500px">
      <el-form label-width="100px">
        <el-form-item label="有效期">
          <el-select v-model="shareExpires" style="width: 100%">
            <el-option label="1 小时" :value="1" />
            <el-option label="24 小时" :value="24" />
            <el-option label="3 天" :value="72" />
            <el-option label="7 天" :value="168" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showShareDialog = false">取消</el-button>
        <el-button type="primary" @click="handleShare" :loading="sharing">生成链接</el-button>
      </template>
    </el-dialog>

    <!-- 分享成功对话框 -->
    <el-dialog v-model="showShareResult" title="分享链接已生成" width="600px">
      <div class="share-result">
        <p>复制链接分享给他人：</p>
        <el-input v-model="shareUrl" readonly>
          <template #append>
            <el-button @click="copyShareUrl">复制</el-button>
          </template>
        </el-input>
        <p class="expire-info">链接将在 {{ shareExpires }} 小时后过期</p>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  ArrowLeft, Refresh, Share, Download, ArrowDown, Document,
  Folder, Link, Tools, CopyDocument, Timer, Connection,
  TrendCharts, Key, Search
} from '@element-plus/icons-vue'
import JsonEditor from '@/views/JsonEditor.vue'
import { autoTestRequest } from '@/utils/request'

const router = useRouter()

// 状态
const loading = ref(false)
const searchKeyword = ref('')
const selectedApi = ref(null)
const activeTab = ref('request')
const codeLang = ref('python')
const showShareDialog = ref(false)
const showShareResult = ref(false)
const sharing = ref(false)
const shareExpires = ref(24)
const shareUrl = ref('')
const apiDoc = ref(null)
const groupTree = ref([])
const originalGroupTree = ref([]) // 保存原始树数据，搜索时基于此过滤
const apiStats = ref(null)
const groupTreeRef = ref(null)

const treeProps = {
  children: 'children',
  label: 'label',
}

// 加载文档
const loadApiDoc = async () => {
  loading.value = true
  try {
    const response = await autoTestRequest.post('/auto-test/api-docs/enhanced', {})
    apiDoc.value = response.doc
    apiStats.value = response.stats
    
    // 构建树形导航
    buildGroupTree(response.doc)
    
    ElMessage.success('文档加载成功')
  } catch (error) {
    ElMessage.error('文档加载失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    loading.value = false
  }
}

const buildGroupTree = (doc) => {
  const groups = {}
  const paths = doc.paths || {}

  for (const [path, methods] of Object.entries(paths)) {
    for (const [method, operation] of Object.entries(methods)) {
      const groupName = operation.tags?.[0] || '其他'
      
      if (!groups[groupName]) {
        groups[groupName] = {
          id: `group-${groupName}`,
          label: groupName,
          isGroup: true,
          children: [],
        }
      }

      groups[groupName].children.push({
        id: `${method}-${path}`,
        label: operation.summary || path,
        method: method.toUpperCase(),
        path,
        url: path, // 文档中的路径作为 URL
        methodObj: { ...operation, method: method.toUpperCase(), path, url: path, group_name: groupName },
      })
    }
  }

  groupTree.value = Object.values(groups)
  originalGroupTree.value = JSON.parse(JSON.stringify(groupTree.value))
  
  // 数据更新后展开所有节点
  nextTick(() => {
    const tree = groupTreeRef.value
    if (tree) {
      const nodes = tree.store?.nodesMap || {}
      Object.values(nodes).forEach(node => {
        node.expanded = true
      })
    }
  })
}

// 选择接口
const handleNodeClick = (data) => {
  if (data.methodObj) {
    selectedApi.value = data.methodObj
    activeTab.value = 'request'
  }
}

// 搜索（基于原始树数据过滤，避免连续搜索丢失数据）
const handleSearch = () => {
  if (!searchKeyword.value) {
    groupTree.value = JSON.parse(JSON.stringify(originalGroupTree.value))
    return
  }
  
  const keyword = searchKeyword.value.toLowerCase()
  const filtered = originalGroupTree.value
    .map(group => ({
      ...group,
      children: group.children.filter(
        api => api.label.toLowerCase().includes(keyword) || 
               api.path.toLowerCase().includes(keyword)
      )
    }))
    .filter(group => group.children.length > 0)
  
  groupTree.value = filtered
}

// 刷新
const refreshDoc = () => loadApiDoc()

// 方法类型颜色
const getMethodType = (method) => {
  const map = { GET: 'success', POST: 'primary', PUT: 'warning', DELETE: 'danger', PATCH: 'info' }
  return map[method] || 'info'
}

// 状态码类型
const getStatusType = (code) => {
  if (code >= 200 && code < 300) return 'success'
  if (code >= 400 && code < 500) return 'warning'
  if (code >= 500) return 'danger'
  return 'info'
}

// 查询参数
const queryParams = computed(() => {
  if (!selectedApi.value?.parameters) return []
  return selectedApi.value.parameters
    .filter(p => p.in === 'query')
    .map(p => ({
      name: p.name,
      type: p.schema?.type || 'string',
      required: p.required || false,
      example: p.example,
      description: p.description || '',
    }))
})

// 请求体 Content-Type
const getRequestBodyContentType = computed(() => {
  if (!selectedApi.value?.requestBody?.content) return 'application/json'
  return Object.keys(selectedApi.value.requestBody.content)[0]
})

// 请求体 JSON（使用 ref 而非 computed，因为 JsonEditor 的 v-model 需要可写）
const requestBodyJson = ref(null)

// 监听 selectedApi 变化时更新 requestBodyJson
watch(() => selectedApi.value, (newVal) => {
  if (newVal?.requestBody?.content) {
    const contentType = getRequestBodyContentType.value
    const content = newVal.requestBody.content[contentType]
    requestBodyJson.value = content?.example || content?.schema || null
  } else {
    requestBodyJson.value = null
  }
}, { immediate: true })

// 响应示例
const responseExamples = computed(() => {
  if (!selectedApi.value?.responses) return []
  
  const examples = []
  for (const [code, response] of Object.entries(selectedApi.value.responses)) {
    if (response.content?.['application/json']) {
      let responseData = response.content['application/json'].example || response.content['application/json'].schema
      // 确保响应数据是对象或数组，字符串需要包装
      if (typeof responseData === 'string') {
        try {
          responseData = JSON.parse(responseData)
        } catch {
          responseData = { raw: responseData }
        }
      }
      examples.push({
        status_code: parseInt(code),
        status: response.description,
        response_data: responseData,
        execution_time: response['x-execution-time-ms'],
      })
    }
  }
  return examples
})

// 生成代码
const generatedCode = computed(() => {
  if (!selectedApi.value) return ''
  
  const { method, path } = selectedApi.value
  const url = path
  
  switch (codeLang.value) {
    case 'python':
      return generatePythonCode(method, url)
    case 'javascript':
      return generateJSCode(method, url)
    case 'curl':
      return generateCurlCode(method, url)
    case 'java':
      return generateJavaCode(method, url)
    default:
      return ''
  }
})

const generatePythonCode = (method, url) => {
  const headerParams = selectedApi.value.parameters?.filter(p => p.in === 'header') || []
  const queryParams = selectedApi.value.parameters?.filter(p => p.in === 'query') || []
  const hasHeaders = headerParams.length > 0
  const hasQuery = queryParams.length > 0
  const hasBody = !!selectedApi.value.requestBody
  
  let code = `import requests\n\n`
  code += `url = "${url}"\n`
  
  if (hasHeaders) {
    code += `headers = {\n`
    headerParams.forEach(h => {
      code += `    "${h.name}": "${h.example || ''}",\n`
    })
    code += `}\n`
  }
  
  if (hasQuery) {
    code += `params = {\n`
    queryParams.forEach(p => {
      code += `    "${p.name}": "${p.example || ''}",\n`
    })
    code += `}\n`
  }
  
  if (hasBody && requestBodyJson.value != null) {
    code += `payload = ${JSON.stringify(requestBodyJson.value, null, 4)}\n`
    code += `\nresponse = requests.${method.toLowerCase()}(\n`
    code += `    url,\n`
    if (hasHeaders) code += `    headers=headers,\n`
    code += `    json=payload\n`
    code += `)\n`
  } else {
    code += `\nresponse = requests.${method.toLowerCase()}(url`
    if (hasQuery) code += `, params=params`
    if (hasHeaders) code += `, headers=headers`
    code += `)\n`
  }
  
  code += `\nprint(response.status_code)\nprint(response.json())\n`
  return code
}

const generateJSCode = (method, url) => {
  const headerParams = selectedApi.value.parameters?.filter(p => p.in === 'header') || []
  const hasHeaders = headerParams.length > 0
  const hasBody = !!selectedApi.value.requestBody
  
  let code = `const url = "${url}";\n`
  code += `const options = {\n`
  code += `    method: "${method.toUpperCase()}",\n`
  
  if (hasHeaders || hasBody) {
    code += `    headers: {\n`
    headerParams.forEach(h => {
      code += `        "${h.name}": "${h.example || ''}",\n`
    })
    if (hasBody) {
      code += `        "Content-Type": "application/json"\n`
    }
    code += `    },\n`
  }
  
  if (hasBody) {
    code += `    body: JSON.stringify(${JSON.stringify(requestBodyJson.value, null, 4)})\n`
  }
  
  code += `};\n\n`
  code += `fetch(url, options)\n`
  code += `    .then(res => res.json())\n`
  code += `    .then(data => console.log(data))\n`
  code += `    .catch(err => console.error(err));\n`
  return code
}

const generateCurlCode = (method, url) => {
  const headerParams = selectedApi.value.parameters?.filter(p => p.in === 'header') || []
  const queryParams = selectedApi.value.parameters?.filter(p => p.in === 'query') || []
  const hasBody = !!selectedApi.value.requestBody
  
  // 拼接 query 参数到 URL
  let fullUrl = url
  if (queryParams.length > 0) {
    const qs = queryParams.map(p => `${encodeURIComponent(p.name)}=${encodeURIComponent(p.example || '')}`).join('&')
    fullUrl += (url.includes('?') ? '&' : '?') + qs
  }
  
  let code = `curl -X ${method.toUpperCase()} "${fullUrl}"`
  
  headerParams.forEach(h => {
    code += ` \\\n  -H "${h.name}: ${h.example || ''}"`
  })
  
  if (hasBody) {
    code += ` \\\n  -H "Content-Type: application/json"`
    code += ` \\\n  -d '${JSON.stringify(requestBodyJson.value)}'`
  }
  
  return code
}

const generateJavaCode = (method, url) => {
  const hasBody = !!selectedApi.value.requestBody
  let bodyArg = 'HttpRequest.BodyPublishers.noBody()'
  if (hasBody) {
    const bodyStr = JSON.stringify(requestBodyJson.value)
      .replace(/\\/g, '\\\\')
      .replace(/"/g, '\\"')
    bodyArg = `HttpRequest.BodyPublishers.ofString("${bodyStr}")`
  }
  return `// Java HttpClient 示例
HttpClient client = HttpClient.newHttpClient();
HttpRequest request = HttpRequest.newBuilder()
    .uri(URI.create("${url}"))
    .method("${method.toUpperCase()}", ${bodyArg})
    .header("Content-Type", "application/json")
    .build();

HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());
System.out.println(response.body());`
}

// 关联数据数量
const relatedCount = computed(() => {
  if (!selectedApi.value?.['x-testmaster']) return 0
  const xt = selectedApi.value['x-testmaster']
  return (xt.mock ? 1 : 0) + 
         (xt.scenarios?.length || 0) + 
         (xt.performance ? 1 : 0) + 
         (xt.global_variables?.length || 0)
})

// 性能指标
const performanceMetrics = computed(() => {
  if (!selectedApi.value?.['x-testmaster']?.performance) return []
  const perf = selectedApi.value['x-testmaster'].performance
  return [
    { label: '平均响应时间', value: perf.avg_response_time != null ? `${perf.avg_response_time}ms` : '-' },
    { label: 'P95 响应时间', value: perf.p95_response_time != null ? `${perf.p95_response_time}ms` : '-' },
    { label: 'P99 响应时间', value: perf.p99_response_time != null ? `${perf.p99_response_time}ms` : '-' },
    { label: 'QPS', value: perf.requests_per_second != null ? perf.requests_per_second : '-' },
    { label: '错误率', value: perf.error_rate != null ? `${perf.error_rate}%` : '-' },
  ]
})

// 操作
const goBack = () => router.push('/auto-test')

const debugApi = () => {
  // 跳转到调试器，带上接口信息
  // 使用完整 URL（如果有的话），否则使用 path
  const debugUrl = selectedApi.value.url || selectedApi.value.path
  router.push({
    path: '/auto-test',
    query: {
      tab: 'debug',
      method: selectedApi.value.method,
      url: debugUrl,
    }
  })
}

const goToScenario = (id) => {
  router.push({
    path: '/auto-test',
    query: { tab: 'scenario', id }
  })
}

// 剪贴板复制（兼容非 HTTPS 环境）
const copyToClipboard = (text) => {
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(text)
    ElMessage.success('已复制')
  } else {
    // fallback: 使用 textarea 复制
    const textarea = document.createElement('textarea')
    textarea.value = text
    textarea.style.position = 'fixed'
    textarea.style.opacity = '0'
    document.body.appendChild(textarea)
    textarea.select()
    try {
      document.execCommand('copy')
      ElMessage.success('已复制')
    } catch {
      ElMessage.error('复制失败，请手动复制')
    }
    document.body.removeChild(textarea)
  }
}

const copyUrl = () => {
  copyToClipboard(selectedApi.value.path)
}

const copyCode = () => {
  copyToClipboard(generatedCode.value)
}

const handleExport = (command) => {
  ElMessage.info(`导出为 ${command} 格式（功能开发中）`)
}

const handleShare = async () => {
  sharing.value = true
  try {
    // 分享当前文档（包含所有用例）
    const response = await autoTestRequest.post('/auto-test/api-docs/share', {
      case_ids: [],
      expires_hours: shareExpires.value
    })
    shareUrl.value = window.location.origin + response.url
    showShareDialog.value = false
    showShareResult.value = true
    ElMessage.success('分享链接已生成')
  } catch (error) {
    ElMessage.error('分享失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    sharing.value = false
  }
}

const copyShareUrl = () => {
  copyToClipboard(shareUrl.value)
}

const scrollTo = (tab) => {
  activeTab.value = tab
}

// 初始化
onMounted(() => {
  loadApiDoc()
})
</script>

<style scoped>
.api-doc-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f5f7fa;
}

.doc-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 20px;
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.back-icon {
  font-size: 20px;
  cursor: pointer;
  color: #606266;
}

.back-icon:hover {
  color: #409eff;
}

.header-left h2 {
  margin: 0;
  font-size: 18px;
  color: #303133;
}

.header-right {
  display: flex;
  gap: 12px;
  align-items: center;
}

.search-input {
  width: 250px;
}

.doc-content {
  flex: 1;
  display: flex;
  overflow: hidden;
}

/* 左侧导航 */
.doc-nav {
  width: 280px;
  background: #fff;
  border-right: 1px solid #e4e7ed;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.nav-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border-bottom: 1px solid #ebeef5;
  font-weight: 500;
  color: #303133;
}

.nav-stats {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
  padding: 12px;
  background: #f5f7fa;
  border-bottom: 1px solid #ebeef5;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  padding: 4px 8px;
  font-size: 12px;
}

.stat-label {
  color: #909399;
}

.stat-value {
  font-weight: 500;
}

.stat-value.success { color: #67c23a; }
.stat-value.warning { color: #e6a23c; }
.stat-value.info { color: #909399; }

.group-tree {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.custom-tree-node {
  display: flex;
  align-items: center;
  gap: 6px;
  flex: 1;
  font-size: 13px;
}

.method-tag {
  font-size: 10px !important;
  padding: 0 4px !important;
  height: 18px !important;
  line-height: 18px !important;
}

/* 中间详情 */
.doc-detail {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  background: #fff;
  margin: 0 1px;
}

.api-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.api-title {
  display: flex;
  align-items: center;
  gap: 12px;
}

.api-title h3 {
  margin: 0;
  font-size: 20px;
  color: #303133;
}

.api-actions {
  display: flex;
  gap: 8px;
}

.api-meta {
  margin-bottom: 20px;
}

.api-tabs {
  margin-top: 20px;
}

/* 参数表格 */
.param-section, .body-section {
  margin-bottom: 20px;
}

.param-section h4, .body-section h4 {
  margin: 0 0 12px 0;
  color: #303133;
}

.content-type-label {
  padding: 8px 12px;
  background: #f5f7fa;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  font-family: monospace;
  margin-bottom: 12px;
}

/* 响应示例 */
.real-data-alert {
  margin-bottom: 16px;
}

.response-example {
  margin-bottom: 20px;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  overflow: hidden;
}

.example-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: #f5f7fa;
  border-bottom: 1px solid #e4e7ed;
}

.example-status {
  flex: 1;
  color: #606266;
}

.example-time {
  display: flex;
  align-items: center;
  gap: 4px;
  color: #909399;
  font-size: 12px;
}

/* 代码示例 */
.code-lang-selector {
  margin-bottom: 12px;
}

.code-block {
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  overflow: hidden;
}

.code-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: #f5f7fa;
  border-bottom: 1px solid #e4e7ed;
  font-weight: 500;
}

.code-block pre {
  margin: 0;
  padding: 16px;
  background: #fafafa;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 13px;
  line-height: 1.5;
  overflow-x: auto;
}

/* 关联数据 */
.related-section {
  margin-bottom: 24px;
}

.related-section h4 {
  display: flex;
  align-items: center;
  gap: 6px;
  margin: 0 0 12px 0;
  color: #303133;
}

.mock-info p {
  margin: 8px 0;
}

.mock-url {
  display: block;
  padding: 8px 12px;
  background: #f5f7fa;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  margin-top: 8px;
  font-family: monospace;
}

.scenario-card {
  margin-bottom: 12px;
}

.scenario-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.metric-card {
  text-align: center;
  margin-bottom: 12px;
}

.metric-value {
  font-size: 24px;
  font-weight: 500;
  color: #409eff;
}

.metric-label {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

/* 右侧导航 */
.doc-toc {
  width: 160px;
  background: #fff;
  border-left: 1px solid #e4e7ed;
  padding: 16px;
  overflow-y: auto;
}

.toc-title {
  font-weight: 500;
  color: #303133;
  margin-bottom: 16px;
}

.toc-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.toc-list li {
  padding: 8px 12px;
  cursor: pointer;
  color: #606266;
  border-left: 2px solid transparent;
  transition: all 0.2s;
}

.toc-list li:hover {
  color: #409eff;
  background: #ecf5ff;
}

.toc-list li.active {
  color: #409eff;
  border-left-color: #409eff;
  background: #ecf5ff;
}

/* 分享对话框 */
.share-result p {
  margin: 8px 0;
}

.expire-info {
  color: #909399;
  font-size: 12px;
}

.badge {
  margin-left: 4px;
}

.doc-json-editor {
  max-height: 300px;
  overflow: auto;
}
</style>
