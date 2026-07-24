<template>
  <div class="upgrade-page">
    <header class="page-header">
      <div>
        <h1>协议调试</h1>
        <p>gRPC / WebSocket / SSE / MQTT 真实执行 + Proto 文件管理（依赖缺失时返回明确错误，不伪造成功）。</p>
      </div>
      <el-button @click="loadProtos">刷新 Proto</el-button>
    </header>

    <el-tabs v-model="tab">
      <el-tab-pane label="执行调试" name="exec">
        <el-card shadow="never">
          <el-form label-width="120px" style="max-width: 760px">
            <el-form-item label="协议">
              <el-select v-model="protocol" style="width: 100%">
                <el-option label="gRPC" value="grpc" />
                <el-option label="WebSocket" value="websocket" />
                <el-option label="SSE" value="sse" />
                <el-option label="MQTT" value="mqtt" />
              </el-select>
            </el-form-item>

            <template v-if="protocol === 'grpc'">
              <el-form-item label="目标"><el-input v-model="grpc.target" placeholder="localhost:50051" /></el-form-item>
              <el-form-item label="托管 Proto">
                <el-select v-model="grpc.proto_file_id" clearable filterable placeholder="可选：选择已上传 proto" style="width: 100%" @change="onProtoSelect">
                  <el-option
                    v-for="p in protos"
                    :key="p.id"
                    :label="`${p.name} (v${p.version})`"
                    :value="p.id"
                  />
                </el-select>
              </el-form-item>
              <el-form-item label="服务">
                <el-select v-if="serviceOptions.length" v-model="grpc.service" filterable allow-create style="width: 100%">
                  <el-option v-for="s in serviceOptions" :key="s" :label="s" :value="s" />
                </el-select>
                <el-input v-else v-model="grpc.service" placeholder="helloworld.Greeter" />
              </el-form-item>
              <el-form-item label="方法">
                <el-select v-if="methodOptions.length" v-model="grpc.method" filterable allow-create style="width: 100%">
                  <el-option v-for="m in methodOptions" :key="m" :label="m" :value="m" />
                </el-select>
                <el-input v-else v-model="grpc.method" placeholder="SayHello" />
              </el-form-item>
              <el-form-item label="请求 JSON"><el-input v-model="grpc.request_json" type="textarea" :rows="5" /></el-form-item>
              <el-form-item label="使用反射"><el-switch v-model="grpc.use_reflection" /></el-form-item>
              <el-form-item label="Proto 路径"><el-input v-model="grpc.proto_path" placeholder="可选，服务端本地路径" /></el-form-item>
            </template>

            <template v-else-if="protocol === 'websocket'">
              <el-form-item label="URL"><el-input v-model="ws.url" placeholder="ws://localhost:8080/ws" /></el-form-item>
              <el-form-item label="发送消息"><el-input v-model="ws.message" type="textarea" :rows="4" /></el-form-item>
              <el-form-item label="接收条数"><el-input-number v-model="ws.receive_count" :min="1" :max="100" /></el-form-item>
              <el-form-item label="超时 ms"><el-input-number v-model="ws.timeout_ms" :min="100" :max="120000" /></el-form-item>
            </template>

            <template v-else-if="protocol === 'mqtt'">
              <el-form-item label="Broker 主机"><el-input v-model="mqtt.host" placeholder="broker.example.com" /></el-form-item>
              <el-form-item label="端口"><el-input-number v-model="mqtt.port" :min="1" :max="65535" /></el-form-item>
              <el-form-item label="发布主题"><el-input v-model="mqtt.publish_topic" placeholder="orders/created" /></el-form-item>
              <el-form-item label="订阅主题"><el-input v-model="mqtt.subscribe_topic" placeholder="orders/created（可选）" /></el-form-item>
              <el-form-item label="消息内容"><el-input v-model="mqtt.payload" type="textarea" :rows="4" /></el-form-item>
              <el-form-item label="QoS"><el-select v-model="mqtt.qos" style="width: 160px"><el-option :value="0" label="0 - 至多一次" /><el-option :value="1" label="1 - 至少一次" /><el-option :value="2" label="2 - 恰好一次" /></el-select></el-form-item>
              <el-form-item label="等待消息数"><el-input-number v-model="mqtt.receive_count" :min="1" :max="100" /></el-form-item>
              <el-form-item label="TLS"><el-switch v-model="mqtt.tls_enabled" /></el-form-item>
              <el-form-item label="超时 ms"><el-input-number v-model="mqtt.timeout_ms" :min="100" :max="120000" /></el-form-item>
            </template>

            <template v-else>
              <el-form-item label="URL"><el-input v-model="sse.url" placeholder="http://localhost:8080/events" /></el-form-item>
              <el-form-item label="最大事件"><el-input-number v-model="sse.max_events" :min="1" :max="500" /></el-form-item>
              <el-form-item label="超时 ms"><el-input-number v-model="sse.timeout_ms" :min="100" :max="120000" /></el-form-item>
            </template>

            <el-button type="primary" :loading="running" @click="execute">执行</el-button>
          </el-form>
        </el-card>

        <el-card v-if="result" shadow="never" class="mt-12">
          <template #header>
            <div class="panel-title">
              <span>结果</span>
              <el-tag :type="result.status === 'ok' || result.status === 'passed' || result.status === 'OK' || result.status === 'completed' ? 'success' : 'danger'">
                {{ result.status }}
              </el-tag>
            </div>
          </template>
          <pre class="result-box">{{ JSON.stringify(result, null, 2) }}</pre>
        </el-card>
      </el-tab-pane>

      <el-tab-pane label="Proto 管理" name="proto">
        <el-row :gutter="16">
          <el-col :span="10">
            <el-table :data="protos" v-loading="protoLoading" height="480" highlight-current-row @current-change="selectProto">
              <el-table-column prop="id" label="ID" width="70" />
              <el-table-column prop="name" label="名称" min-width="140" />
              <el-table-column prop="package_name" label="package" min-width="120" show-overflow-tooltip />
              <el-table-column prop="version" label="版本" width="70" />
              <el-table-column label="操作" width="90">
                <template #default="{ row }">
                  <el-button link type="danger" @click.stop="removeProto(row)">删除</el-button>
                </template>
              </el-table-column>
            </el-table>
          </el-col>
          <el-col :span="14">
            <el-card shadow="never">
              <template #header>上传 / 更新 Proto</template>
              <el-form label-width="90px">
                <el-form-item label="名称"><el-input v-model="protoForm.name" placeholder="hello.proto" /></el-form-item>
                <el-form-item label="内容">
                  <el-input v-model="protoForm.content" type="textarea" :rows="16" placeholder="syntax = &quot;proto3&quot;; ..." />
                </el-form-item>
                <el-button type="primary" :loading="protoSaving" @click="saveProto">保存 Proto</el-button>
                <el-button @click="fillSample">填入示例</el-button>
              </el-form>
              <div v-if="selectedProto?.services?.length" class="services mt-12">
                <div class="muted">解析到的服务：</div>
                <el-tag v-for="s in selectedProto.services" :key="s.name" class="mr-6" type="info">
                  {{ s.name }} ({{ (s.methods || []).length }} methods)
                </el-tag>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { storeToRefs } from 'pinia'
import { ElMessage, ElMessageBox } from 'element-plus'
import { featureUpgradesApi } from '@/api/feature-upgrades'
import { useProjectStore } from '@/stores/project'

const { projectId } = storeToRefs(useProjectStore())
const tab = ref('exec')
const protocol = ref('grpc')
const running = ref(false)
const result = ref(null)
const protos = ref([])
const protoLoading = ref(false)
const protoSaving = ref(false)
const selectedProto = ref(null)
const grpc = reactive({
  target: 'localhost:50051',
  service: '',
  method: '',
  request_json: '{"name":"TestMaster"}',
  use_reflection: true,
  proto_path: '',
  proto_file_id: null,
})
const ws = reactive({
  url: 'ws://localhost:8080/ws',
  message: 'ping',
  receive_count: 1,
  timeout_ms: 5000,
})
const sse = reactive({
  url: 'http://localhost:8080/events',
  max_events: 5,
  timeout_ms: 10000,
})
const mqtt = reactive({
  host: '',
  port: 1883,
  publish_topic: '',
  subscribe_topic: '',
  payload: '{"source":"TestMaster"}',
  qos: 0,
  receive_count: 1,
  tls_enabled: false,
  timeout_ms: 10000,
})
const protoForm = reactive({
  name: 'hello.proto',
  content: '',
})

const serviceOptions = computed(() => {
  const services = selectedProto.value?.services || []
  const pkg = selectedProto.value?.package_name
  return services.map((s) => (pkg ? `${pkg}.${s.name}` : s.name))
})

const methodOptions = computed(() => {
  const services = selectedProto.value?.services || []
  const current = services.find((s) => {
    const full = selectedProto.value?.package_name ? `${selectedProto.value.package_name}.${s.name}` : s.name
    return full === grpc.service || s.name === grpc.service
  })
  return (current?.methods || []).map((m) => m.name)
})

function onProtoSelect(id) {
  selectedProto.value = protos.value.find((p) => p.id === id) || null
  if (selectedProto.value?.services?.length) {
    const s = selectedProto.value.services[0]
    const pkg = selectedProto.value.package_name
    grpc.service = pkg ? `${pkg}.${s.name}` : s.name
    grpc.method = s.methods?.[0]?.name || ''
  }
}

async function loadProtos() {
  protoLoading.value = true
  try {
    const res = await featureUpgradesApi.listProtos(projectId.value)
    protos.value = res.items || []
  } catch (error) {
    ElMessage.error(error.message || '加载 Proto 失败')
  } finally {
    protoLoading.value = false
  }
}

async function selectProto(row) {
  selectedProto.value = row
  if (!row?.id) return
  try {
    const detail = await featureUpgradesApi.getProto(row.id)
    selectedProto.value = detail
    protoForm.name = detail.name || protoForm.name
    protoForm.content = detail.content || ''
    grpc.proto_file_id = detail.id
    onProtoSelect(detail.id)
  } catch (error) {
    ElMessage.error(error.message || '读取 Proto 失败')
  }
}

async function saveProto() {
  if (!protoForm.name || !protoForm.content) return ElMessage.warning('名称与内容必填')
  protoSaving.value = true
  try {
    const res = await featureUpgradesApi.upsertProto({
      project_id: projectId.value,
      name: protoForm.name,
      content: protoForm.content,
    })
    ElMessage.success('Proto 已保存')
    await loadProtos()
    selectedProto.value = res
    grpc.proto_file_id = res.id
  } catch (error) {
    ElMessage.error(error.message || '保存失败')
  } finally {
    protoSaving.value = false
  }
}

async function removeProto(row) {
  try {
    await ElMessageBox.confirm(`删除 Proto ${row.name}?`, '确认', { type: 'warning' })
    await featureUpgradesApi.deleteProto(row.id)
    ElMessage.success('已删除')
    if (grpc.proto_file_id === row.id) grpc.proto_file_id = null
    await loadProtos()
  } catch (error) {
    if (error !== 'cancel') ElMessage.error(error.message || '删除失败')
  }
}

function fillSample() {
  protoForm.name = 'helloworld.proto'
  protoForm.content = `syntax = "proto3";
package helloworld;

service Greeter {
  rpc SayHello (HelloRequest) returns (HelloReply);
}

message HelloRequest {
  string name = 1;
}

message HelloReply {
  string message = 1;
}
`
}

async function execute() {
  running.value = true
  result.value = null
  try {
    let config = {}
    if (protocol.value === 'grpc') {
      let request = {}
      try { request = JSON.parse(grpc.request_json || '{}') } catch { return ElMessage.warning('gRPC 请求 JSON 无效') }
      config = {
        target: grpc.target,
        service: grpc.service,
        method: grpc.method,
        request,
        use_reflection: grpc.use_reflection,
        proto_path: grpc.proto_path || undefined,
        proto_file_id: grpc.proto_file_id || undefined,
      }
    } else if (protocol.value === 'websocket') {
      config = { ...ws }
    } else if (protocol.value === 'mqtt') {
      config = { ...mqtt }
    } else {
      config = { ...sse }
    }
    result.value = await featureUpgradesApi.executeProtocol({ protocol: protocol.value, config })
  } catch (error) {
    ElMessage.error(error.message || '执行失败')
  } finally {
    running.value = false
  }
}

onMounted(loadProtos)
</script>

<style scoped>
.upgrade-page { padding: 20px; display: flex; flex-direction: column; gap: 16px; }
.page-header { display: flex; justify-content: space-between; gap: 12px; }
.page-header h1 { margin: 0 0 6px; font-size: 22px; }
.page-header p { margin: 0; color: #64748b; }
.panel-title { display: flex; justify-content: space-between; align-items: center; }
.result-box { background: #0f172a; color: #e2e8f0; padding: 12px; border-radius: 8px; overflow: auto; max-height: 480px; }
.mt-12 { margin-top: 12px; }
.mr-6 { margin-right: 6px; margin-top: 6px; }
.muted { color: #64748b; font-size: 12px; margin-bottom: 6px; }
</style>
