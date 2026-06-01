<template>
  <el-dialog v-model="visible" title="导入 cURL" width="600px" @close="handleClose">
    <div class="curl-import">
      <p class="tip">粘贴 cURL 命令，自动解析为接口用例</p>
      <el-input
        v-model="curlString"
        type="textarea"
        :rows="8"
        placeholder="curl -X POST https://api.example.com/users -H Content-Type:application/json -d {name:test}"
      />

      <div v-if="parsedResult" class="parsed-result">
        <h4>解析结果</h4>
        <el-descriptions :column="1" border size="small">
          <el-descriptions-item label="方法">
            <el-tag :type="getMethodType(parsedResult.method)" size="small">{{ parsedResult.method }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="URL">{{ parsedResult.url }}</el-descriptions-item>
          <el-descriptions-item label="请求头">
            <div v-for="(value, key) in parsedResult.headers" :key="key" class="header-item">
              <strong>{{ key }}:</strong> {{ value }}
            </div>
          </el-descriptions-item>
          <el-descriptions-item label="请求体">
            <pre class="body-preview">{{ parsedResult.body || '(无)' }}</pre>
          </el-descriptions-item>
        </el-descriptions>
      </div>
    </div>

    <template #footer>
      <el-button @click="handleClose">取消</el-button>
      <el-button @click="parseCurl" :loading="parsing">解析</el-button>
      <el-button type="primary" @click="applyParsed" :disabled="!parsedResult">应用</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'

const props = defineProps({
  modelValue: Boolean
})

const emit = defineEmits(['update:modelValue', 'import'])

const visible = ref(false)
const curlString = ref('')
const parsing = ref(false)
const parsedResult = ref(null)

watch(() => props.modelValue, (val) => {
  visible.value = val
})

watch(visible, (val) => {
  emit('update:modelValue', val)
})

const handleClose = () => {
  visible.value = false
  curlString.value = ''
  parsedResult.value = null
}

const parseCurl = async () => {
  if (!curlString.value.trim()) {
    ElMessage.warning('请输入 cURL 命令')
    return
  }
  parsing.value = true
  try {
    const res = await axios.post('/api/auto-test/import/curl', {
      curl_string: curlString.value
    })
    parsedResult.value = res.data.data
    ElMessage.success('解析成功')
  } catch (err) {
    ElMessage.error('解析失败: ' + (err.response?.data?.detail || err.message))
  } finally {
    parsing.value = false
  }
}

const applyParsed = () => {
  if (!parsedResult.value) return
  emit('import', parsedResult.value)
  handleClose()
}

const getMethodType = (method) => {
  const types = { GET: 'success', POST: 'primary', PUT: 'warning', DELETE: 'danger', PATCH: 'info' }
  return types[method] || 'info'
}
</script>

<style scoped>
.curl-import {
  padding: 10px 0;
}

.tip {
  color: #909399;
  font-size: 14px;
  margin-bottom: 15px;
}

.parsed-result {
  margin-top: 20px;
  padding: 15px;
  background: #f5f7fa;
  border-radius: 8px;
}

.parsed-result h4 {
  margin: 0 0 15px 0;
  font-size: 16px;
  color: #303133;
}

.header-item {
  font-size: 13px;
  line-height: 1.8;
}

.body-preview {
  margin: 0;
  font-size: 12px;
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 150px;
  overflow-y: auto;
}
</style>
