<template>
  <div class="notification-center page-shell">
    <section class="page-header">
      <div><h2>任务通知中心</h2><p>长时间执行完成后，结果会可靠投递到已启用的通知渠道。</p></div>
      <el-button type="primary" :icon="Plus" @click="openCreate">新增通知渠道</el-button>
    </section>
    <el-alert title="支持钉钉、企业微信、飞书机器人、SMTP 邮件和通用 HTTPS Webhook。个人微信没有稳定的官方机器人投递接口，不作为自动推送渠道。" type="info" :closable="false" show-icon />

    <section class="content-band">
      <div class="section-title"><h3>通知渠道</h3><el-button text :icon="Refresh" @click="load">刷新</el-button></div>
      <el-table :data="channels" v-loading="loading" empty-text="还没有通知渠道，添加后手工、定时和 CI 触发的套件执行都可复用。">
        <el-table-column prop="name" label="名称" min-width="160" />
        <el-table-column label="类型" width="110"><template #default="{ row }"><el-tag>{{ typeLabel(row.channel_type) }}</el-tag></template></el-table-column>
        <el-table-column prop="destination" label="接收位置" min-width="200" show-overflow-tooltip />
        <el-table-column label="通知时机" min-width="220"><template #default="{ row }">{{ (row.notify_on || []).map(statusLabel).join('、') }}</template></el-table-column>
        <el-table-column label="状态" width="100"><template #default="{ row }"><el-tag :type="row.is_active ? 'success' : 'info'">{{ row.is_active ? '启用' : '停用' }}</el-tag></template></el-table-column>
        <el-table-column label="操作" width="190" fixed="right"><template #default="{ row }"><el-button text type="primary" @click="testChannel(row)">测试</el-button><el-button text @click="openEdit(row)">编辑</el-button><el-button text type="danger" @click="remove(row)">删除</el-button></template></el-table-column>
      </el-table>
    </section>

    <section class="content-band">
      <div class="section-title"><h3>投递记录</h3><span class="section-hint">失败会自动指数退避重试，最多 5 次。</span></div>
      <el-table :data="deliveries" size="small" max-height="360" empty-text="暂无投递记录">
        <el-table-column label="时间" width="175"><template #default="{ row }">{{ formatTime(row.created_at) }}</template></el-table-column>
        <el-table-column prop="payload.execution_id" label="任务" min-width="160" show-overflow-tooltip />
        <el-table-column prop="channel_type" label="渠道" width="100"><template #default="{ row }">{{ typeLabel(row.channel_type) }}</template></el-table-column>
        <el-table-column label="结果" width="105"><template #default="{ row }"><el-tag :type="deliveryType(row.status)">{{ deliveryLabel(row.status) }}</el-tag></template></el-table-column>
        <el-table-column prop="attempts" label="尝试" width="70" />
        <el-table-column prop="last_error" label="说明" min-width="260" show-overflow-tooltip><template #default="{ row }">{{ row.last_error || (row.delivered_at ? '已成功投递' : '-') }}</template></el-table-column>
      </el-table>
    </section>

    <el-dialog v-model="visible" :title="editing ? '编辑通知渠道' : '新增通知渠道'" width="560px" destroy-on-close>
      <el-form label-position="top" :model="form">
        <el-form-item label="渠道名称" required><el-input v-model="form.name" maxlength="120" placeholder="例如：生产回归失败告警" /></el-form-item>
        <el-form-item label="通知渠道" required><el-select v-model="form.channel_type" style="width:100%"><el-option label="钉钉机器人" value="dingtalk" /><el-option label="企业微信机器人" value="wecom" /><el-option label="飞书机器人" value="feishu" /><el-option label="邮件" value="email" /><el-option label="通用 Webhook" value="webhook" /></el-select></el-form-item>
        <el-form-item v-if="form.channel_type === 'email'" label="收件人" required><el-input v-model="form.config.recipients" placeholder="多个邮箱使用英文逗号分隔" /></el-form-item>
        <template v-else><el-form-item label="机器人 / Webhook HTTPS 地址" required><el-input v-model="form.config.webhook_url" type="password" show-password placeholder="https://..." /></el-form-item><el-form-item v-if="form.channel_type === 'dingtalk'" label="钉钉加签密钥（可选）"><el-input v-model="form.config.secret" type="password" show-password /></el-form-item></template>
        <el-form-item label="通知时机"><el-checkbox-group v-model="form.notify_on"><el-checkbox label="passed">通过</el-checkbox><el-checkbox label="failed">失败</el-checkbox><el-checkbox label="timed_out">超时</el-checkbox><el-checkbox label="infra_error">执行器异常</el-checkbox><el-checkbox label="cancelled">取消</el-checkbox></el-checkbox-group></el-form-item>
        <el-form-item label="启用"><el-switch v-model="form.is_active" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="visible = false">取消</el-button><el-button type="primary" :loading="saving" @click="save">保存</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Refresh } from '@element-plus/icons-vue'
import autoTestRequest from '@/utils/autoTestRequest'

const api = '/auto-test/notification-channels'
const channels = ref([]); const deliveries = ref([]); const loading = ref(false); const saving = ref(false); const visible = ref(false); const editing = ref(null)
const emptyForm = () => ({ name: '', channel_type: 'dingtalk', config: { webhook_url: '', secret: '', recipients: '' }, notify_on: ['failed', 'timed_out', 'infra_error'], is_active: true })
const form = ref(emptyForm())
const typeLabel = value => ({ dingtalk: '钉钉', wecom: '企业微信', feishu: '飞书', email: '邮件', webhook: 'Webhook' })[value] || value
const statusLabel = value => ({ passed: '通过', failed: '失败', timed_out: '超时', infra_error: '执行器异常', cancelled: '取消' })[value] || value
const deliveryLabel = value => ({ queued: '待投递', retrying: '重试中', delivered: '已投递', failed: '已失败' })[value] || value
const deliveryType = value => ({ delivered: 'success', failed: 'danger', retrying: 'warning' })[value] || 'info'
const formatTime = value => value ? new Date(value).toLocaleString('zh-CN', { hour12: false }) : '-'
async function load () { loading.value = true; try { const [channelRes, deliveryRes] = await Promise.all([autoTestRequest.get(api), autoTestRequest.get(`${api}/deliveries/history`)]); channels.value = channelRes.channels || []; deliveries.value = deliveryRes.deliveries || [] } catch (error) { ElMessage.error(error.response?.data?.detail || '加载通知中心失败') } finally { loading.value = false } }
function openCreate () { editing.value = null; form.value = emptyForm(); visible.value = true }
function openEdit (row) { editing.value = row; form.value = { name: row.name, channel_type: row.channel_type, config: { webhook_url: '', secret: '', recipients: row.channel_type === 'email' ? String(row.destination || '').split('、').join(', ') : '' }, notify_on: [...(row.notify_on || [])], is_active: row.is_active }; visible.value = true }
async function save () { saving.value = true; try { const body = JSON.parse(JSON.stringify(form.value)); if (body.channel_type === 'email') body.config.recipients = body.config.recipients.split(',').map(item => item.trim()).filter(Boolean); await autoTestRequest[editing.value ? 'put' : 'post'](editing.value ? `${api}/${editing.value.id}` : api, body); ElMessage.success('通知渠道已保存'); visible.value = false; await load() } catch (error) { ElMessage.error(error.response?.data?.detail || '保存失败') } finally { saving.value = false } }
async function testChannel (row) { try { await autoTestRequest.post(`${api}/${row.id}/test`); ElMessage.success('测试通知已提交') } catch (error) { ElMessage.error(error.response?.data?.detail || '测试通知失败') } }
async function remove (row) { try { await ElMessageBox.confirm(`删除“${row.name}”后不会影响已有执行记录，确定继续吗？`, '删除通知渠道', { type: 'warning' }); await autoTestRequest.delete(`${api}/${row.id}`); ElMessage.success('已删除'); await load() } catch (error) { if (error !== 'cancel') ElMessage.error(error.response?.data?.detail || '删除失败') } }
onMounted(load)
</script>

<style scoped>
.page-shell{display:grid;gap:16px}.page-header,.content-band{background:var(--tm-surface,#fff);border:1px solid var(--tm-border,#e5e7eb);padding:20px}.page-header{display:flex;justify-content:space-between;align-items:center}.page-header h2,.section-title h3{margin:0;color:var(--tm-text,#1f2937)}.page-header p,.section-hint{margin:6px 0 0;color:var(--tm-text-secondary,#667085);font-size:13px}.section-title{display:flex;align-items:center;justify-content:space-between;margin-bottom:14px}@media(max-width:720px){.page-header{align-items:flex-start;gap:12px;flex-direction:column}}
</style>
