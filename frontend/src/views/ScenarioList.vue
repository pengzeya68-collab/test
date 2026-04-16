<template>
  <div class="scenario-list-container">
    <!-- 顶部工具栏 -->
    <div class="list-toolbar">
      <div class="toolbar-left">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索场景名称"
          size="default"
          style="width: 240px"
          clearable
          @input="handleSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
      </div>
      <div class="toolbar-right">
        <!-- 环境选择 -->
        <div class="env-select-wrapper">
          <span class="env-label">执行环境：</span>
          <el-select
            v-model="selectedEnvId"
            placeholder="选择环境"
            size="default"
            clearable
            @change="handleEnvChange"
            style="width: 160px"
          >
            <el-option
              v-for="env in environments"
              :key="env.id"
              :label="env.name"
              :value="env.id"
            />
          </el-select>
        </div>
        <el-tooltip content="环境管理" placement="top" popper-class="action-tooltip">
          <el-button :icon="Setting" @click="openEnvManager" />
        </el-tooltip>
        <el-button type="primary" @click="handleCreate">
          <el-icon><Plus /></el-icon>
          新建场景
        </el-button>
      </div>
    </div>

    <!-- 场景列表 -->
    <div class="scenario-table" v-loading="loading">
      <el-table
        :data="filteredScenarios"
        style="width: 100%"
        stripe
        :header-cell-style="{ background: 'var(--tm-bg-card)', color: 'var(--tm-text-primary)' }"
      >
        <el-table-column prop="name" label="场景名称" min-width="180" />
        <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
        <el-table-column label="步骤数" width="100" align="center">
          <template #default="{ row }">
            <el-tag type="info" effect="plain" round>{{ row.steps ? row.steps.length : 0 }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-switch
              :model-value="row.is_active"
              active-text="启用"
              inactive-text="停用"
              inline-prompt
              @change="(val) => handleToggleStatus(row, val)"
            />
          </template>
        </el-table-column>
        <el-table-column label="定时计划" width="120" align="center">
          <template #default="{ row }">
            <el-tooltip content="设置定时计划" placement="top" popper-class="action-tooltip">
              <el-button type="warning" link :icon="Clock" @click="openScheduleDialog(row)">
                设置计划
              </el-button>
            </el-tooltip>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" align="center">
          <template #default="{ row }">
            <div class="action-buttons">
              <el-tooltip content="运行场景" placement="top" popper-class="action-tooltip">
                <span><el-button type="primary" link :icon="VideoPlay" @click="handleRun(row)" /></span>
              </el-tooltip>
              <el-tooltip content="CI/CD 集成" placement="top" popper-class="action-tooltip">
                <span><el-button type="success" link :icon="Link" @click="openCiCdDialog(row)" /></span>
              </el-tooltip>
              <el-tooltip content="执行历史" placement="top" popper-class="action-tooltip">
                <span><el-button type="info" link :icon="Timer" @click="openHistoryDrawer(row)" /></span>
              </el-tooltip>
              <el-tooltip content="编辑场景" placement="top" popper-class="action-tooltip">
                <span><el-button type="primary" link :icon="Edit" @click="handleEdit(row)" /></span>
              </el-tooltip>
              <el-tooltip content="删除场景" placement="top" popper-class="action-tooltip">
                <span><el-button type="danger" link :icon="Delete" @click="handleDelete(row.id)" /></span>
              </el-tooltip>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="!loading && filteredScenarios.length === 0" description="暂无场景" />
    </div>

    <!-- 新建/编辑场景对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑场景' : '新建场景'"
      width="500px"
    >
      <el-form :model="scenarioForm" label-width="80px">
        <el-form-item label="场景名称" required>
          <el-input v-model="scenarioForm.name" placeholder="请输入场景名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="scenarioForm.description"
            type="textarea"
            :rows="3"
            placeholder="场景描述（可选）"
          />
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="scenarioForm.is_active" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSave">确定</el-button>
      </template>
    </el-dialog>

    <ScenarioExecutionDialog ref="executionDialogRef" v-model="resultDialogVisible" @completed="handleExecutionCompleted" />

    <!-- 定时计划配置对话框 -->
    <el-dialog v-model="scheduleDialogVisible" title="定时计划配置" width="500px">
      <el-form :model="scheduleForm" label-position="top">

        <!-- 第一行：任务名称 + 执行环境 -->
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="场景名称">
              <span>{{ scheduleForm.scenario_name }}</span>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="执行环境">
              <el-select v-model="scheduleForm.env_id" placeholder="选择执行环境" clearable style="width: 100%">
                <el-option
                  v-for="env in environments"
                  :key="env.id"
                  :label="env.name"
                  :value="env.id"
                />
              </el-select>
              <div class="form-tip">
                留空使用默认环境
              </div>
            </el-form-item>
          </el-col>
        </el-row>

        <!-- 第二行：快速选择/Cron + 任务状态 -->
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="快速选择" required>
              <el-select v-model="scheduleForm.cron_expression" placeholder="选择执行频率" style="width: 100%">
                <el-option
                  v-for="preset in schedulePresets"
                  :key="preset.value"
                  :label="preset.label"
                  :value="preset.value"
                />
              </el-select>
            </el-form-item>
            <el-form-item>
              <template #label>
                <span>Cron 表达式</span>
                <el-tooltip content="格式：分 时 日 月 周&#10;常用：&#10;每天凌晨2点 → 0 2 * * *&#10;每小时 → 0 * * * *&#10;每周一早上9点 → 0 9 * * 1" placement="top">
                  <el-icon :size="14" style="margin-left: 4px; color: var(--tm-text-secondary); cursor: help;"><QuestionFilled /></el-icon>
                </el-tooltip>
              </template>
              <el-input v-model="scheduleForm.cron_expression" placeholder="分 时 日 月 周" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="任务状态">
              <el-switch
                v-model="scheduleForm.is_active"
                active-color="#13ce66"
                inactive-color="#8e8e93"
                active-text="立即启用"
                inactive-text="暂不启用"
                inline-prompt
              />
              <div class="form-tip">
                禁用 = 调度器挂起
              </div>
            </el-form-item>
          </el-col>
        </el-row>

        <!-- 第三行：Webhook 告警 -->
        <el-row>
          <el-col :span="24">
            <el-form-item label="Webhook 告警">
              <el-input v-model="scheduleForm.webhook_url" placeholder="钉钉/飞书/企业微信机器人 Webhook 地址（可选）" />
              <div class="form-tip">
                测试执行完成后自动发送测试报告
              </div>
            </el-form-item>
          </el-col>
        </el-row>

        <!-- 常用示例 - 折叠面板 -->
        <el-collapse>
          <el-collapse-item title="📋 查看常用 Cron 示例">
            <div class="cron-help">
              <ul>
                <li><code>0 2 * * *</code> - 每天凌晨2点</li>
                <li><code>0 9 * * 1</code> - 每周一早上9点</li>
                <li><code>0 */6 * * *</code> - 每6小时</li>
                <li><code>0 0 1 * *</code> - 每月1号凌晨</li>
              </ul>
            </div>
          </el-collapse-item>
        </el-collapse>

        <!-- 当前已有定时任务 -->
        <div v-if="currentExistingTasks.length > 0" class="existing-tasks">
          <div class="section-title">当前已有定时任务</div>
          <el-table :data="currentExistingTasks" style="width: 100%; margin-top: 8px" size="small">
            <el-table-column prop="task_id" label="ID" width="60" align="center" />
            <el-table-column prop="name" label="名称" width="120" />
            <el-table-column prop="cron_expression" label="Cron" width="120" />
            <el-table-column prop="is_active" label="状态" width="100" align="center">
              <template #default="{ row }">
                <el-switch
                  v-model="row.is_active"
                  :loading="row.statusLoading"
                  active-color="#13ce66"
                  inactive-color="#8e8e93"
                  active-text="调度中"
                  inactive-text="已挂起"
                  inline-prompt
                  @change="handleToggleTaskStatus(row)"
                />
              </template>
            </el-table-column>
            <el-table-column prop="last_run" label="上次执行" width="130" />
          </el-table>
        </div>

      </el-form>
      <template #footer>
        <el-button @click="scheduleDialogVisible = false">取消</el-button>
        <el-button type="danger" @click="handleDeleteSchedule(scheduleForm.scenario_id)" v-if="scheduleTasks[scheduleForm.scenario_id]?.length">
          删除定时任务
        </el-button>
        <el-button type="primary" @click="handleScheduleSubmit">保存</el-button>
      </template>
    </el-dialog>

    <!-- CI/CD Webhook 配置对话框 -->
    <el-dialog v-model="ciCdDialogVisible" title="CI/CD Webhook 触发配置" width="580px">
      <div class="ci-cd-info">
        <p style="margin-bottom: 16px;">
          请将以下 cURL 命令复制到您的 <strong>GitLab CI / Jenkins Pipeline</strong> 中。<br>
          每次代码部署完成后，会自动触发该场景进行回归测试。
        </p>
        <div style="background: #1e1e1e; padding: 15px; border-radius: 6px; color: #d4d4d4; font-family: 'Courier New', monospace; font-size: 13px; line-height: 1.6; word-break: break-all; margin-bottom: 16px;">
          <template v-if="curlCommand">
            {{ curlCommand }}
          </template>
          <template v-else style="color: #ff9800;">
            该场景尚未生成 Webhook Token，请先编辑保存场景以生成。
          </template>
        </div>
        <el-button type="primary" @click="copyCurlCommand">
          <el-icon><DocumentCopy /></el-icon> 复制命令
        </el-button>
      </div>
      <template #footer>
        <el-button @click="ciCdDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 执行历史抽屉 -->
    <el-drawer
      v-model="historyDrawerVisible"
      title="执行历史记录"
      size="70%"
    >
      <div class="history-content" v-loading="historyLoading">
        <!-- 统计卡片 -->
        <el-row :gutter="16" class="stats-cards">
          <el-col :span="8">
            <el-card shadow="hover" class="stat-card">
              <div class="stat-content">
                <div class="stat-value">{{ historyStats.total_reports }}</div>
                <div class="stat-label">总报告数</div>
              </div>
            </el-card>
          </el-col>
          <el-col :span="8">
            <el-card shadow="hover" class="stat-card">
              <div class="stat-content">
                <div class="stat-value" style="color: #67c23a;">{{ historyStats.passed_reports }}</div>
                <div class="stat-label">通过报告数</div>
              </div>
            </el-card>
          </el-col>
          <el-col :span="8">
            <el-card shadow="hover" class="stat-card">
              <div class="stat-content">
                <div class="stat-value" :style="{ color: historyStats.pass_rate >= 80 ? '#67c23a' : (historyStats.pass_rate >= 60 ? '#e6a23c' : '#f56c6c') }">
                  {{ historyStats.pass_rate }}%
                </div>
                <div class="stat-label">通过率</div>
              </div>
            </el-card>
          </el-col>
        </el-row>

        <!-- 筛选表单 -->
        <el-form :inline="true" class="history-filter-form">
          <el-form-item label="状态">
            <el-select v-model="historyFilterStatus" placeholder="全部状态" clearable style="width: 120px">
              <el-option label="全部" value="" />
              <el-option label="运行中" value="running" />
              <el-option label="已完成" value="completed" />
              <el-option label="已失败" value="failed" />
            </el-select>
          </el-form-item>
          <el-form-item label="日期范围">
            <el-date-picker
              v-model="historyFilterStartDate"
              type="date"
              placeholder="开始日期"
              value-format="YYYY-MM-DD"
              :disabled-date="disabledStartDate"
              style="width: 140px"
            />
            <span style="margin: 0 8px">至</span>
            <el-date-picker
              v-model="historyFilterEndDate"
              type="date"
              placeholder="结束日期"
              value-format="YYYY-MM-DD"
              :disabled-date="disabledEndDate"
              style="width: 140px"
            />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="loadExecutionHistory" :loading="historyLoading">
              <el-icon><Search /></el-icon>
              查询
            </el-button>
            <el-button @click="resetHistoryFilters">
              <el-icon><RefreshRight /></el-icon>
              重置
            </el-button>
          </el-form-item>
        </el-form>

        <!-- 温馨提示：自动清理 -->
        <el-alert
          title="⚠️ 温馨提示"
          type="warning"
          description="为节省系统存储，执行报告仅保留最近 7 天，请及时查看或导出。"
          show-icon
          :closable="false"
          style="margin-bottom: 16px"
        />

        <div class="history-summary" v-if="executionHistory.total > 0">
          <el-tag type="info">共 {{ executionHistory.total }} 次执行</el-tag>
          <el-tag type="success">成功 {{ executionHistory.success_count }} 次</el-tag>
          <el-tag type="danger">失败 {{ executionHistory.failed_count }} 次</el-tag>
          <el-button size="small" @click="refreshExecutionHistory" style="margin-left: 12px">
            <el-icon><Refresh /></el-icon> 刷新
          </el-button>
        </div>

        <el-table :data="executionHistory.items" style="width: 100%; margin-top: 16px">
          <el-table-column prop="id" label="ID" width="60" align="center" />
          <el-table-column prop="status" label="状态" width="80" align="center">
            <template #default="{ row }">
              <el-tag :type="getStatusType(row.status)" size="small">
                {{ getStatusText(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="total_steps" label="总步骤" width="70" align="center" />
          <el-table-column prop="success_steps" label="成功" width="60" align="center">
            <template #default="{ row }">
              <span class="success-text">{{ row.success_steps }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="failed_steps" label="失败" width="60" align="center">
            <template #default="{ row }">
              <span class="failed-text">{{ row.failed_steps }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="total_time" label="耗时" width="80" align="center">
            <template #default="{ row }">
              {{ (row.total_time / 1000).toFixed(2) }}s
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="执行时间" width="170" />
          <el-table-column label="操作" width="260" align="center">
            <template #default="{ row }">
              <el-button
                size="small"
                type="warning"
                link
                @click="reRunHistory(row)"
              >
                再次运行
              </el-button>
              <el-button
                size="small"
                type="primary"
                link
                @click="viewReportDetail(row.id)"
              >
                查看详情
              </el-button>
              <el-button
                v-if="row.report_url"
                size="small"
                type="success"
                link
                @click="openReport(row.report_url)"
              >
                Allure
              </el-button>
              <el-button
                size="small"
                type="danger"
                link
                @click="deleteHistoryRecord(row.id)"
              >
                <el-icon><Delete /></el-icon>
              </el-button>
            </template>
          </el-table-column>
        </el-table>

        <el-empty v-if="!historyLoading && executionHistory.items.length === 0" description="暂无执行记录" />
      </div>
    </el-drawer>

    <!-- 报告详情对话框 -->
    <el-dialog
      v-model="reportDetailVisible"
      title="执行报告详情"
      width="80%"
      append-to-body
      destroy-on-close
    >
      <div v-loading="reportDetailLoading" style="min-height: 200px;">
        <div v-if="reportDetailData" class="result-content">
          <div class="result-header-stats">
            <el-tag :type="reportDetailData.failed_steps > 0 ? 'danger' : 'success'" size="large">
              {{ reportDetailData.failed_steps > 0 ? '❌ 有步骤失败' : '✅ 全部通过' }}
            </el-tag>
            <span style="margin-left: 15px; color: var(--tm-text-regular);">
              总步骤: {{ reportDetailData.total_steps || 0 }} |
              成功: <span style="color: #67c23a">{{ reportDetailData.success_steps || 0 }}</span> |
              失败: <span style="color: #f56c6c">{{ reportDetailData.failed_steps || 0 }}</span> |
              总耗时: {{ (reportDetailData.total_time || 0) }}ms
            </span>
            <!-- 再次运行（失败报告更醒目） -->
            <el-button
              :type="reportDetailData.failed_steps > 0 ? 'danger' : 'primary'"
              size="default"
              style="margin-left: 20px"
              :loading="isRunning"
              :disabled="isRunning"
              @click="reRunHistory(reportDetailData)"
            >
              <el-icon><VideoPlay /></el-icon>
              再次运行
            </el-button>
          </div>

          <el-divider />

          <!-- 嵌入式 Allure 报告 -->
          <div style="height: 60vh; width: 100%; margin-bottom: 20px; border: 1px solid var(--tm-border-color); border-radius: 4px; overflow: hidden;">
            <iframe
              v-if="reportDetailData && reportDetailData.report_url"
              :src="resolveReportUrl(reportDetailData.report_url)"
              style="width: 100%; height: 100%; border: none;"
              title="Allure 报告"
            ></iframe>
            <el-empty v-else description="暂无报告数据" />
          </div>

          <el-divider>文本步骤详情</el-divider>

          <el-alert
            v-if="reportDetailData.step_results.length === 0 && !reportDetailData.step_detail_available"
            title="步骤详情不可用"
            description="该报告的步骤详情数据无法读取，可能已被清理或写入失败。统计信息仍然准确。"
            type="warning"
            :closable="false"
            show-icon
            style="margin-bottom: 16px;"
          />

          <!-- 步骤结果列表 -->
          <div class="step-results">
            <div
              v-for="(step, index) in reportDetailData.step_results"
              :key="index"
              class="step-result-card"
              :class="{ 'is-failed': step.status === 'failed', 'is-skipped': step.status === 'skipped' }"
            >
              <!-- 跳过状态的步骤头部（不可点击展开） -->
              <div v-if="step.status === 'skipped'" class="step-header step-header-skipped">
                <span class="step-order">{{ index + 1 }}</span>
                <el-tag type="info" size="small">{{ step.method || 'N/A' }}</el-tag>
                <span class="step-name">{{ step.api_case_name }}</span>
                <el-tag type="info" size="small">未执行/跳过</el-tag>
                <span class="step-skipped-hint">因前置步骤失败，此步骤被跳过</span>
              </div>

              <!-- 正常执行/失败状态的步骤头部 -->
              <div v-else class="step-header" @click="toggleDetailStep(index)">
                <span class="step-order">{{ index + 1 }}</span>
                <el-tag :type="getMethodType(step.method)" size="small">{{ step.method }}</el-tag>
                <span class="step-name">{{ step.api_case_name }}</span>
                <el-tag v-if="step.status_code" :type="getStatusCodeType(step.status_code)" size="small">
                  {{ step.status_code }}
                </el-tag>
                <el-tag v-if="step.status === 'success'" type="success" effect="light">通过</el-tag>
                <el-tag v-else-if="step.status === 'failed'" type="danger" effect="light">失败</el-tag>
                <el-tag v-else-if="step.status === 'skipped'" type="info" effect="light">跳过</el-tag>
                <el-tag v-else type="warning" effect="light">未知</el-tag>

                <span style="margin-left: 10px; color: var(--tm-text-secondary); font-size: 13px;" v-if="step.status !== 'skipped'">
                  {{ step.duration || 0 }}ms
                </span>
                <el-icon class="toggle-icon" :class="{ 'is-expanded': expandedDetailSteps.includes(index) }">
                  <ArrowRight />
                </el-icon>
              </div>

              <!-- 步骤详情（跳过状态不显示） -->
              <div class="step-detail" v-if="expandedDetailSteps.includes(index) && step.status !== 'skipped'">
                <div class="detail-url">{{ step.url }}</div>

                <!-- 请求信息 -->
                <div class="detail-section" v-if="step.headers || step.payload">
                  <h5>请求信息</h5>
                  <div class="request-info">
                    <div class="info-row">
                      <span class="info-label">方法:</span>
                      <el-tag :type="getMethodType(step.method)" size="small">{{ step.method }}</el-tag>
                    </div>
                    <div class="info-row">
                      <span class="info-label">URL:</span>
                      <span class="info-value">{{ step.url }}</span>
                    </div>
                    <div class="info-row" v-if="step.headers && Object.keys(step.headers).length > 0">
                      <span class="info-label">请求头:</span>
                      <pre class="code-block">{{ formatResponseBody(step.headers) }}</pre>
                    </div>
                    <div class="info-row" v-if="step.payload && Object.keys(step.payload).length > 0">
                      <span class="info-label">请求体:</span>
                      <pre class="code-block">{{ formatResponseBody(step.payload) }}</pre>
                    </div>
                  </div>
                </div>

                <!-- 错误信息 -->
                <div class="step-error" v-if="step.error">
                  <el-alert type="error" :title="step.error" :closable="false" show-icon />
                </div>

                <!-- 响应信息 -->
                <div class="detail-section" v-if="step.response">
                  <h5>响应信息</h5>
                  <div class="response-info">
                    <div class="info-row">
                      <span class="info-label">状态码:</span>
                      <el-tag :type="getStatusCodeType(step.status_code)" size="small">
                        {{ step.status_code || '无' }}
                      </el-tag>
                    </div>
                    <div class="info-row" v-if="step.response.headers && Object.keys(step.response.headers).length > 0">
                      <span class="info-label">响应头:</span>
                      <pre class="code-block">{{ formatResponseBody(step.response.headers) }}</pre>
                    </div>
                    <div class="info-row" v-if="step.response.body">
                      <span class="info-label">响应体:</span>
                      <pre class="code-block">{{ step.response.body }}</pre>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="reportDetailVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 环境管理抽屉 - 和接口库页面保持一致 -->
    <EnvironmentManager
      v-model="envManagerDrawerVisible"
      @close="handleEnvManagerClose"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, VideoPlay, Delete, Search, ArrowRight, Document, Link, DocumentCopy, Clock, DataAnalysis, Edit, Timer, Refresh, Loading, Setting, QuestionFilled } from '@element-plus/icons-vue'
import axios from 'axios'
import EnvironmentManager from '@/components/EnvironmentManager.vue'
import ScenarioExecutionDialog from '@/components/ScenarioExecutionDialog.vue'

const autoTestRequest = axios.create({
  baseURL: '',
  timeout: 30000
})

// 添加请求拦截器，自动带上 token
autoTestRequest.interceptors.request.use(
  config => {
    const token = localStorage.getItem('admin_token') || localStorage.getItem('token');
    if (token && token !== 'undefined' && token !== 'null' && token !== '[object Object]') {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  error => {
    return Promise.reject(error);
  }
)

// 添加响应拦截器，自动处理 response.data
autoTestRequest.interceptors.response.use(
  response => {
    return response.data;
  },
  error => {
    return Promise.reject(error);
  }
)

const loading = ref(false)
const scenarios = ref([])
const searchKeyword = ref('')
const dialogVisible = ref(false)
const isEdit = ref(false)
const scenarioForm = ref({
  name: '',
  description: '',
  is_active: true
})
const currentScenarioId = ref(null)
const resultDialogVisible = ref(false)
const executionDialogRef = ref(null)
const runResult = ref(null)
const expandedSteps = ref([])
let pollingTimer = null
let pollingAbortController = null
let currentTaskId = null
let fakeProgressTimer = null
const isRunning = ref(false)
const isCanceling = ref(false)
const runningTaskProgress = ref(null)

// 定时计划相关
const scheduleDialogVisible = ref(false)
const scheduleForm = ref({
  scenario_id: null,
  scenario_name: '',
  cron_expression: '0 2 * * *',
  env_id: null,
  webhook_url: '',
  is_active: true,
})

// CI/CD Webhook 配置对话框
const ciCdDialogVisible = ref(false)
const currentCiCdScene = ref(null)
const resolveReportUrl = (reportUrl) => {
  if (!reportUrl) return ''
  if (/^https?:\/\//i.test(reportUrl)) return reportUrl

  const normalizedPath = reportUrl.startsWith('/') ? reportUrl : `/${reportUrl}`
  const configuredBase = import.meta.env.VITE_AUTO_TEST_API_BASE_URL?.trim()

  if (configuredBase) {
    return `${configuredBase.replace(/\/+$/, '')}${normalizedPath}`
  }

  return normalizedPath
}

const curlCommand = computed(() => {
  if (!currentCiCdScene.value || !currentCiCdScene.value.webhook_token) {
    return ''
  }
  const baseUrl = window.location.origin
  return `curl -X POST "${baseUrl}/api/auto-test/scenarios/webhook/${currentCiCdScene.value.webhook_token}" \\
     -H "Content-Type: application/json" \\
     -d '{"env_id": 替换为实际环境ID}'`
})

const openCiCdDialog = (row) => {
  currentCiCdScene.value = row
  ciCdDialogVisible.value = true
}

const copyCurlCommand = async () => {
  if (!curlCommand.value) {
    ElMessage.warning('没有生成命令，该场景尚未生成 Webhook Token，请先编辑保存场景以生成')
    return
  }
  try {
    await navigator.clipboard.writeText(curlCommand.value)
    ElMessage.success('cURL 命令已复制到剪贴板')
  } catch (error) {
    ElMessage.error('复制失败，请手动复制')
  }
}
const scheduleTasks = ref({})  // { scenario_id: [tasks] }
const schedulePresets = [
  { label: '每天凌晨2点', value: '0 2 * * *' },
  { label: '每天上午9点', value: '0 9 * * *' },
  { label: '每天下午6点', value: '0 18 * * *' },
  { label: '每6小时', value: '0 */6 * * *' },
  { label: '每周一早上9点', value: '0 9 * * 1' },
  { label: '每月1号凌晨', value: '0 0 1 * *' }
]

// 执行历史抽屉相关
const historyDrawerVisible = ref(false)
const historyLoading = ref(false)
const currentHistoryScenarioId = ref(null)
const executionHistory = ref({
  total: 0,
  success_count: 0,
  failed_count: 0,
  items: []
})

// 执行历史筛选参数
const historyFilterStatus = ref('')
const historyFilterStartDate = ref('')
const historyFilterEndDate = ref('')
const historyStats = ref({
  total_reports: 0,
  passed_reports: 0,
  pass_rate: 0
})

// 禁用未来日期的函数
const disabledFutureDate = (time) => {
  return time.getTime() > Date.now()
}

// 开始日期选择器的禁用函数
const disabledStartDate = (time) => {
  // 禁用未来日期
  if (time.getTime() > Date.now()) {
    return true
  }
  // 如果结束日期已选择，开始日期不能大于结束日期
  if (historyFilterEndDate.value) {
    const endDate = new Date(historyFilterEndDate.value)
    return time.getTime() > endDate.getTime()
  }
  return false
}

// 结束日期选择器的禁用函数
const disabledEndDate = (time) => {
  // 禁用未来日期
  if (time.getTime() > Date.now()) {
    return true
  }
  // 如果开始日期已选择，结束日期不能小于开始日期
  if (historyFilterStartDate.value) {
    const startDate = new Date(historyFilterStartDate.value)
    return time.getTime() < startDate.getTime()
  }
  return false
}

// 报告详情对话框相关
const reportDetailVisible = ref(false)
const reportDetailLoading = ref(false)
const reportDetailData = ref(null)
const expandedDetailSteps = ref([])

// 环境选择相关
const envManagerDrawerVisible = ref(false)
const selectedEnvId = ref(null)
const environments = ref([])

// 加载环境列表 - 使用正确的 API 路径
const loadEnvironments = async () => {
  try {
    const res = await autoTestRequest.get('/api/auto-test/environments')
    environments.value = res || []
  } catch (error) {
    console.error('加载环境列表失败:', error)
  }
}

// 环境变化回调
const handleEnvChange = () => {
  // 用户切换环境后自动保存选择，不需要额外处理
}

// 打开环境管理抽屉
const openEnvManager = () => {
  envManagerDrawerVisible.value = true
}

// 环境管理关闭回调
const handleEnvManagerClose = () => {
  envManagerDrawerVisible.value = false
  // 刷新环境列表
  loadEnvironments()
}

const getStatusType = (status) => {
  const types = { success: 'success', completed: 'success', failed: 'danger', error: 'warning', running: 'primary' }
  return types[status] || 'info'
}

const getStatusText = (status) => {
  const texts = { success: '成功', completed: '成功', failed: '失败', error: '异常', running: '运行中' }
  return texts[status] || status
}

const openHistoryDrawer = async (row) => {
  currentHistoryScenarioId.value = row.id
  historyDrawerVisible.value = true
  await loadExecutionHistory()
}

const loadExecutionHistory = async () => {
  if (!currentHistoryScenarioId.value) return
  historyLoading.value = true
  try {
    const params = {}

    // 添加筛选参数
    if (historyFilterStatus.value) {
      params.status = historyFilterStatus.value
    }
    if (historyFilterStartDate.value) {
      params.start_date = historyFilterStartDate.value
    }
    if (historyFilterEndDate.value) {
      params.end_date = historyFilterEndDate.value
    }

    const res = await autoTestRequest.get(`/api/auto-test/scenarios/${currentHistoryScenarioId.value}/history`, { params })

    // 计算统计数据
    const items = res.items || []
    const total = items.length
    const passedCount = items.filter(item => item.status === 'success' || item.status === 'completed').length
    const passRate = total > 0 ? Math.round((passedCount / total) * 100) : 0

    historyStats.value = {
      total_reports: total,
      passed_reports: passedCount,
      pass_rate: passRate
    }

    const successCount = items.filter(item => item.status === 'success' || item.status === 'completed').length
    executionHistory.value = {
      total: res.total || 0,
      success_count: successCount,
      failed_count: items.length - successCount,
      items: items
    }
  } catch (error) {
    console.error('加载执行历史失败:', error)
    ElMessage.error('加载执行历史失败')
  } finally {
    historyLoading.value = false
  }
}

const resetHistoryFilters = () => {
  historyFilterStatus.value = ''
  historyFilterStartDate.value = ''
  historyFilterEndDate.value = ''
  loadExecutionHistory()
}

const refreshExecutionHistory = () => {
  loadExecutionHistory()
}

const deleteHistoryRecord = async (historyId) => {
  try {
    await ElMessageBox.confirm('确定要删除这条执行记录吗？\n此操作会同时删除硬盘上的报告文件和数据库记录，无法恢复！', '确认删除', {
      confirmButtonText: '确定删除',
      cancelButtonText: '取消',
      type: 'warning'
    })

    if (!currentHistoryScenarioId.value) {
      throw new Error('未找到当前场景ID')
    }
    await autoTestRequest.delete(`/api/auto-test/scenarios/${currentHistoryScenarioId.value}/history/${historyId}`)
    ElMessage.success('删除成功')
    await loadExecutionHistory()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

const openReport = (reportUrl) => {
  // 拼接完整 URL
  const fullUrl = resolveReportUrl(reportUrl)
  window.open(fullUrl, '_blank')
}

// 再次运行历史报告对应的场景
const reRunHistory = async (historyRow) => {
  const scenarioId = historyRow.scenario_id || currentHistoryScenarioId.value;
  const envId = historyRow.env_id || selectedEnvId.value;

  if (!scenarioId) {
      ElMessage.error('无法获取场景 ID，请从场景列表运行');
      return;
  }

  if (envId) {
      selectedEnvId.value = envId;
  }

  historyDrawerVisible.value = false;
  reportDetailVisible.value = false;

  const stepCount = historyRow.total_steps || 0
  executionDialogRef.value?.startExecution(scenarioId, envId, stepCount)
}

const filteredScenarios = computed(() => {
  if (!searchKeyword.value) return scenarios.value
  const keyword = searchKeyword.value.toLowerCase()
  return scenarios.value.filter(s =>
    s.name.toLowerCase().includes(keyword) ||
    (s.description && s.description.toLowerCase().includes(keyword))
  )
})

const getMethodType = (method) => {
  const types = { GET: 'success', POST: 'warning', PUT: 'primary', DELETE: 'danger', PATCH: 'info' }
  return types[method] || 'info'
}

const formatTotalTime = (ms) => {
  if (!ms && ms !== 0) return '0ms'
  if (ms < 1000) return ms + 'ms'
  return (ms / 1000).toFixed(2) + 's'
}

// 格式化断言预期值，处理对象格式
const formatExpectedValue = (assertion) => {
  if (!assertion) return ''
  const field = assertion.field || ''
  const operator = assertion.operator || ''
  let expected = assertion.expectedValue

  // 如果 expectedValue 是对象，提取其中的值
  if (expected && typeof expected === 'object') {
    expected = expected.expectedValue || expected.eq || JSON.stringify(expected)
  }

  return `${field} ${operator} ${expected}`
}

const getStatusCodeType = (statusCode) => {
  if (!statusCode) return 'info'
  if (statusCode >= 200 && statusCode < 300) return 'success'
  if (statusCode >= 300 && statusCode < 400) return 'warning'
  return 'danger'
}

const toggleStepDetail = (index) => {
  const idx = expandedSteps.value.indexOf(index)
  if (idx >= 0) {
    expandedSteps.value.splice(idx, 1)
  } else {
    expandedSteps.value.push(index)
  }
}

const formatResponseBody = (response) => {
  if (!response) return '无响应'
  // 如果 response 是对象，直接格式化
  if (typeof response === 'object') {
    return JSON.stringify(response, null, 2)
  }
  // 后端返回的响应体直接存在 response 字段（字符串）
  try {
    const json = JSON.parse(response)
    return JSON.stringify(json, null, 2)
  } catch {
    return response
  }
}

const loadScenarios = async () => {
  loading.value = true
  try {
    const res = await autoTestRequest.get('/api/auto-test/scenarios')
    scenarios.value = res || []
    // #region agent log
    // 注释掉这个调试请求，因为没有服务在 7444 端口运行
    // fetch('http://127.0.0.1:7444/ingest/5081c6b5-d6af-4e32-8f31-9f3bb44e7710',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'d60346'},body:JSON.stringify({sessionId:'d60346',runId:'run1',hypothesisId:'H4',location:'ScenarioList.vue:loadScenarios',message:'frontend_scenarios_shape',data:{count:(res||[]).length,sample:(res||[]).slice(0,3).map(s=>({id:s.id,step_count:s.step_count,steps_len:Array.isArray(s.steps)?s.steps.length:null,keys:Object.keys(s||{}).slice(0,10)}))},timestamp:Date.now()})}).catch(()=>{});
    // #endregion
  } catch (error) {
    console.error('加载场景失败:', error)
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  // 实时搜索，无需额外处理
}

const handleCreate = () => {
  isEdit.value = false
  scenarioForm.value = { name: '', description: '', is_active: true }
  dialogVisible.value = true
}

const handleEdit = (row) => {
  emit('edit', row)
}

const handleSave = async () => {
  if (!scenarioForm.value.name) {
    ElMessage.warning('请输入场景名称')
    return
  }
  try {
    if (isEdit.value) {
      await autoTestRequest.put(`/api/auto-test/scenarios/${currentScenarioId.value}`, scenarioForm.value)
      ElMessage.success('更新成功')
    } else {
      await autoTestRequest.post('/api/auto-test/scenarios', scenarioForm.value)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    loadScenarios()
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

const handleDelete = async (id) => {
  try {
    // 弹出强阻断确认框，绝对不会点不动！
    await ElMessageBox.confirm(
      '确定要彻底删除该场景及其所有关联记录吗？此操作不可逆！',
      '高危操作警告',
      {
        confirmButtonText: '坚决删除',
        cancelButtonText: '点错了',
        type: 'warning',
      }
    );

    // 发送删除请求
    await autoTestRequest.delete(`/api/auto-test/scenarios/${id}`);

    ElMessage.success('清理完毕！');
    // 重新加载列表数据
    loadScenarios();

  } catch (error) {
    // 如果是点击了取消，不报错；如果是后端返回错误，则弹出后端信息
    if (error !== 'cancel') {
      const msg = error.response?.data?.message || error.response?.data?.error || '删除遭遇异常，请检查关联数据！';
      ElMessage.error(msg);
    }
  }
};

// 定时计划相关方法
const loadScheduleTasks = async () => {
  try {
    const res = await autoTestRequest.get('/api/auto-test/scheduler/tasks')
    // 按场景 ID 分组，添加 statusLoading 字段
    const grouped = {}
    for (const task of res || []) {
      const sid = task.scenario_id
      if (!grouped[sid]) grouped[sid] = []
      // 添加 statusLoading 用于切换loading
      task.statusLoading = false
      grouped[sid].push(task)
    }
    scheduleTasks.value = grouped
  } catch (error) {
    console.error('加载定时任务失败:', error)
  }
}

// 当前对话框场景的已有任务
const currentExistingTasks = computed(() => {
  const sid = scheduleForm.value.scenario_id
  if (!sid) return []
  return scheduleTasks.value[sid] || []
})

// 切换任务状态
const handleToggleTaskStatus = async (task) => {
  const originalStatus = task.is_active
  task.statusLoading = true
  try {
    await autoTestRequest.post(`/api/auto-test/scheduler/tasks/${task.task_id}/toggle`)
    ElMessage.success(`任务已${task.is_active ? '启用' : '暂停'}`)
    // 重新加载任务列表
    await loadScheduleTasks()
  } catch (error) {
    // 失败回滚
    task.is_active = !originalStatus
    ElMessage.error('状态切换失败: ' + (error.response?.data?.error || error.message))
    console.error('切换状态失败:', error)
  } finally {
    task.statusLoading = false
  }
}

const getScheduleLabel = (scenarioId) => {
  const tasks = scheduleTasks.value[scenarioId]
  if (!tasks || tasks.length === 0) return ''
  // 显示第一个任务的 Cron 表达式
  const cron = tasks[0].cron_expression
  // 转换为易读格式
  return cronToHuman(cron)
}

const cronToHuman = (cron) => {
  const parts = (cron || '').split(' ')
  if (parts.length !== 5) return cron || ''
  const [minute, hour, day, month, dow] = parts

  if (day === '*' && month === '*' && dow === '*') {
    if (hour === '*') return `${minute}分钟执行`
    return `每天 ${hour}:${minute.padStart(2, '0')}`
  }
  if (dow === '1' && day === '*') return `每周一 ${hour}:${minute.padStart(2, '0')}`
  if (day === '1' && month === '*') return `每月1号 ${hour}:${minute.padStart(2, '0')}`
  return cron
}

const openScheduleDialog = async (row) => {
  scheduleForm.value = {
    scenario_id: row.id,
    scenario_name: row.name,
    cron_expression: '0 2 * * *',
    env_id: null,
    webhook_url: '',
    is_active: true,
    name: row.name + ' 定时任务'
  }
  // 如果场景本身已有 cron/webhook，回填
  if (row.cron_expression) {
    scheduleForm.value.cron_expression = row.cron_expression
  }
  if (row.webhook_url) {
    scheduleForm.value.webhook_url = row.webhook_url
  }
  // 加载该场景已有的定时任务
  try {
    const res = await autoTestRequest.get('/api/auto-test/scheduler/tasks')
    // 找到该场景下的任务
    const existingTasks = (res || []).filter(t => t.scenario_id === row.id)
    if (existingTasks.length > 0) {
      const existing = existingTasks[0]
      scheduleForm.value.cron_expression = existing.cron_expression || scheduleForm.value.cron_expression
      scheduleForm.value.env_id = existing.env_id || scheduleForm.value.env_id
      scheduleForm.value.webhook_url = existing.webhook_url || scheduleForm.value.webhook_url
      scheduleForm.value.is_active = existing.is_active !== undefined ? existing.is_active : true
      scheduleForm.value.name = existing.name || scheduleForm.value.name
    }
  } catch (error) {
    console.error('加载任务详情失败:', error)
  }
  scheduleDialogVisible.value = true
}

const handleScheduleSubmit = async () => {
  try {
    // 先删除该场景的所有现有任务
    const existingTasks = scheduleTasks.value[scheduleForm.value.scenario_id] || []
    for (const task of existingTasks) {
      await autoTestRequest.delete(`/api/auto-test/scheduler/tasks/${task.task_id}`)
    }

    // 创建新任务
    await autoTestRequest.post('/api/auto-test/scheduler/tasks', {
      scenario_id: scheduleForm.value.scenario_id,
      cron_expression: scheduleForm.value.cron_expression,
      env_id: scheduleForm.value.env_id,
      webhook_url: scheduleForm.value.webhook_url,
      name: scheduleForm.value.name,
      is_active: scheduleForm.value.is_active
    })

    ElMessage.success('定时任务设置成功')
    scheduleDialogVisible.value = false
    loadScheduleTasks()
  } catch (error) {
    ElMessage.error('设置失败: ' + (error.response?.data?.detail || error.message))
  }
}

const handleDeleteSchedule = async (scenarioId) => {
  try {
    await ElMessageBox.confirm('确定要删除该场景的定时任务吗？', '删除确认', { type: 'warning' })
    const tasks = scheduleTasks.value[scenarioId] || []
    console.log("[DEBUG] 准备删除定时任务，scenarioId=", scenarioId, "tasks=", tasks)
    for (const task of tasks) {
      console.log("[DEBUG] 删除任务ID:", task.task_id)
      await autoTestRequest.delete(`/api/auto-test/scheduler/tasks/${task.task_id}`)
    }
    ElMessage.success('删除成功')
    loadScheduleTasks()
  } catch (error) {
    if (error !== 'cancel') ElMessage.error('删除失败')
  }
}

// 停止轮询
const stopPolling = () => {
  if (pollingTimer) {
    clearInterval(pollingTimer)
    pollingTimer = null
  }
  if (pollingAbortController) {
    pollingAbortController.abort()
    pollingAbortController = null
  }
  stopFakeProgress()
}

const pollTaskStatus = async (taskId, scenarioName) => {
  stopPolling()
  pollingAbortController = new AbortController()
  const signal = pollingAbortController.signal
  pollingTimer = setInterval(async () => {
    try {
      const res = await autoTestRequest.get(`/api/auto-test/tasks/${taskId}`, { signal })
      const state = res.status

      if (state === 'PROGRESS') {
        stopFakeProgress()
        const progress = res.progress || {}
        runningTaskProgress.value = {
          percent: progress.percent || 10,
          current: progress.current || 0,
          total: progress.total || runningTaskProgress.value?.total || 0,
          current_api: progress.current_api || '执行中...'
        }
      }

      if (state === 'completed' || state === 'SUCCESS') {
        stopPolling()
        stopFakeProgress()
        isRunning.value = false
        const resultData = res.result || res
        runningTaskProgress.value = {
          percent: 100,
          current: resultData.total_steps || 0,
          total: resultData.total_steps || 0,
          current_api: '执行完成'
        }
        runResult.value = resultData
        expandedSteps.value = []
        if (resultData && resultData.step_results) {
          const failedIndex = resultData.step_results.findIndex(s => !s.success)
          if (failedIndex >= 0) expandedSteps.value = [failedIndex]
        }
        resultDialogVisible.value = true
        ElMessage.success('执行完成')
      } else if (state === 'failed' || state === 'FAILURE' || state === 'REVOKED') {
        stopPolling()
        stopFakeProgress()
        isRunning.value = false
        if (state === 'REVOKED') {
          ElMessage.warning('⛔ 任务已被终止')
          resultDialogVisible.value = false
        } else {
          ElMessage.error('执行失败: ' + (res.error || '未知错误'))
        }
      }
    } catch (error) {
      if (axios.isCancel(error)) return
      stopPolling()
      stopFakeProgress()
      isRunning.value = false
      ElMessage.error('查询任务状态失败: ' + (error.response?.data?.detail || error.message))
    }
  }, 2000)
}

const handleToggleStatus = async (row, val) => {
  const oldVal = row.is_active
  try {
    await autoTestRequest.put(`/api/auto-test/scenarios/${row.id}/status`, {
      is_active: val
    })
    row.is_active = val
    ElMessage.success(val ? '场景已启用' : '场景已停用')
  } catch (error) {
    row.is_active = oldVal
    ElMessage.error('状态切换失败: ' + (error.response?.data?.detail || error.message))
  }
}

const handleRun = async (row) => {
  if (!selectedEnvId.value) {
    ElMessage.warning('请先选择执行环境！')
    return
  }
  if (!row.is_active) {
    ElMessage.warning('该场景已停用，无法运行！')
    return
  }
  const stepCount = row.steps ? row.steps.length : 0
  executionDialogRef.value?.startExecution(row.id, selectedEnvId.value, stepCount)
}

const handleExecutionCompleted = () => {
  loadScenarios()
}

const startFakeProgress = (totalSteps) => {
  stopFakeProgress()
  let fakePercent = 5
  fakeProgressTimer = setInterval(() => {
    if (fakePercent < 85) {
      fakePercent += Math.random() * 3
      if (fakePercent > 85) fakePercent = 85
      runningTaskProgress.value = {
        percent: Math.round(fakePercent),
        current: Math.floor((fakePercent / 100) * totalSteps),
        total: totalSteps,
        current_api: '正在执行步骤...'
      }
    }
  }, 1500)
}

const stopFakeProgress = () => {
  if (fakeProgressTimer) {
    clearInterval(fakeProgressTimer)
    fakeProgressTimer = null
  }
}

// 强制取消当前任务
const handleCancelTask = async () => {
  if (!currentTaskId) {
    ElMessage.warning('没有正在执行的任务')
    return
  }

  try {
    isCanceling.value = true
    await autoTestRequest.post(`/api/auto-test/tasks/${currentTaskId}/cancel`)
    stopPolling()
    isRunning.value = false
    isCanceling.value = false
    runningTaskProgress.value = null
    ElMessage.warning('⛔ 任务已被用户强制终止')
    resultDialogVisible.value = false
    currentTaskId = null
  } catch (error) {
    isCanceling.value = false
    ElMessage.error('终止任务失败: ' + (error.response?.data?.detail || error.message))
  }
}

const openAllureReport = () => {
  const resultData = runResult.value || reportDetailData.value || {};

  let url = resultData.report_url;
  if (!url && resultData.execution_record_id) {
    url = `/reports/scenario_${resultData.scenario_id || 'unknown'}/index.html`;
  }
  if (!url && resultData.report_id) {
    url = `/reports/${resultData.report_id}/index.html`;
  }

  if (url) {
    window.open(resolveReportUrl(url), '_blank');
  } else {
    ElMessage.warning('Allure 报告未生成（可能未安装 allure 命令行工具）。请检查后端日志。');
  }
};

// 查看历史报告详情
const viewReportDetail = async (reportId) => {
  try {
    reportDetailLoading.value = true
    reportDetailData.value = null
    expandedDetailSteps.value = []
    const res = await autoTestRequest.get(`/api/auto-test/reports/${reportId}`)
    reportDetailData.value = res
    // 默认展开第一个失败步骤
    if (res.step_results) {
      const failedIndex = res.step_results.findIndex(s => !s.success)
      if (failedIndex >= 0) {
        expandedDetailSteps.value = [failedIndex]
      }
    }
    reportDetailVisible.value = true
  } catch (error) {
    ElMessage.error('加载报告详情失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    reportDetailLoading.value = false
  }
}

// 切换步骤详情展开/收起（报告详情对话框内）
const toggleDetailStep = (index) => {
  const idx = expandedDetailSteps.value.indexOf(index)
  if (idx >= 0) {
    expandedDetailSteps.value.splice(idx, 1)
  } else {
    expandedDetailSteps.value.push(index)
  }
}

const emit = defineEmits(['edit'])

defineExpose({
  loadScenarios
})

onMounted(() => {
  loadScenarios()
  loadScheduleTasks()
  loadEnvironments()
})

onUnmounted(() => {
  stopPolling()
})
</script>

<style scoped>
.scenario-list-container {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--tm-bg-page);
}

.list-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: var(--tm-bg-card);
  border-bottom: 1px solid var(--tm-border-light);
  flex-shrink: 0;
}

.toolbar-left,
.toolbar-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.env-select-wrapper {
  display: flex;
  align-items: center;
  gap: 8px;
}

.env-label {
  color: var(--tm-text-regular);
  font-size: 14px;
  white-space: nowrap;
}

.scenario-table {
  flex: 1;
  padding: 20px;
  overflow: auto;
}

.running-status {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  text-align: center;
}

.result-content {
  max-height: 70vh;
  overflow: auto;
}

.result-summary {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
}

.summary-info {
  color: var(--tm-text-regular);
  font-size: 14px;
}

.step-results {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.step-result-card {
  border: 1px solid var(--tm-border-light);
  border-radius: var(--tm-radius-base);
  padding: 16px;
  background: var(--tm-bg-card);
  transition: all 0.3s;
}

.step-result-card.is-failed {
  border-color: rgba($--color-danger, 0.4);
  background: rgba($--color-danger, 0.02);
}

.step-header {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: var(--tm-radius-small);
  transition: background-color 0.2s;
}

.step-header:hover {
  background: var(--tm-bg-hover);
}

.toggle-icon {
  margin-left: auto;
  transition: transform 0.3s;
}

.toggle-icon.is-expanded {
  transform: rotate(90deg);
}

.step-order {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--tm-color-primary);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
}

.step-name {
  font-weight: 500;
  flex: 1;
  color: var(--tm-text-primary);
}

.step-duration {
  color: var(--tm-text-secondary);
  font-size: 12px;
}

.step-detail {
  margin-top: 16px;
  padding-left: 36px;
  border-top: 1px solid var(--tm-border-light);
  padding-top: 16px;
}

.detail-url {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 12px;
  color: var(--tm-text-regular);
  word-break: break-all;
  background: var(--tm-bg-page);
  padding: 8px 12px;
  border-radius: var(--tm-radius-small);
  margin-bottom: 12px;
}

.step-error {
  margin-top: 12px;
}

/* 错误信息块 - 终端风格 */
.step-error .error-block {
  background: rgba(245, 108, 108, 0.1);
  color: #f56c6c;
  border: 1px solid rgba(245, 108, 108, 0.3);
  border-radius: 6px;
  padding: 12px;
  font-family: 'Courier New', monospace;
  white-space: pre-wrap;
  word-break: break-all;
  margin: 0;
  line-height: 1.5;
}

.detail-section {
  margin-top: 16px;
}

.detail-section h5 {
  margin: 0 0 12px;
  color: var(--tm-color-primary);
  font-size: 13px;
  font-weight: 600;
}

.request-info {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.info-tag {
  background: var(--tm-bg-page);
  padding: 6px 10px;
  border-radius: var(--tm-radius-small);
  font-size: 12px;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  border: 1px solid var(--tm-border-light);
}

.response-info {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.info-label {
  color: var(--tm-text-secondary);
  font-size: 13px;
}

.response-body h5 {
  margin: 12px 0 8px;
  color: var(--tm-color-primary);
  font-size: 13px;
  font-weight: 600;
}

.body-display {
  background: #1e1e1e;
  color: #d4d4d4;
  padding: 16px;
  border-radius: var(--tm-radius-small);
  max-height: 200px;
  overflow: auto;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 12px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-all;
  margin: 0;
  box-shadow: inset 0 2px 8px rgba(0, 0, 0, 0.2);
}

.assertion-summary {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.assertion-table {
  margin-top: 8px;
}

.assertion-errors {
  margin-top: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.context-vars h4 {
  margin: 0 0 12px;
  color: var(--tm-text-primary);
}

.var-tag {
  margin: 4px;
}

.report-actions {
  text-align: center;
  padding: 8px 0;
}

.allure-btn {
  background: linear-gradient(135deg, var(--tm-color-primary) 0%, #0066cc 100%);
  border: none;
  font-size: 15px;
}

/* 已有定时任务列表 */
.existing-tasks {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #f0f0f0;
}

.section-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--tm-text-regular);
  margin-bottom: 8px;
}

.allure-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, var(--tm-color-primary-light) 0%, var(--tm-color-primary) 100%);
}

.report-section {
  margin-top: 16px;
}

.report-tip {
  font-size: 12px;
  color: var(--tm-text-secondary);
  margin-top: 8px;
}

.step-header-skipped {
  opacity: 0.6;
  cursor: default;
}

.step-skipped-hint {
  color: var(--tm-text-secondary);
  font-size: 12px;
  font-style: italic;
  margin-left: 8px;
}

.result-dialog-footer {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 16px;
}

.is-skipped {
  background-color: var(--tm-bg-page);
  border-left: 3px solid var(--tm-text-secondary);
}

.schedule-tag {
  margin-right: 4px;
}

.action-buttons {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
}

.form-tip {
  font-size: 12px;
  color: var(--tm-text-secondary);
  margin-top: 8px;
}

.cron-help {
  font-size: 13px;
  color: var(--tm-text-regular);
  background: var(--tm-bg-page);
  padding: 12px;
  border-radius: var(--tm-radius-small);
}

.cron-help p {
  margin: 0 0 8px;
}

.cron-help ul {
  margin: 0;
  padding-left: 20px;
}

.cron-help li {
  margin: 4px 0;
}

.cron-help code {
  background: var(--tm-bg-card);
  padding: 2px 6px;
  border-radius: 3px;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  border: 1px solid var(--tm-border-light);
}

/* 执行历史抽屉 */
.history-content {
  height: 100%;
}

.history-summary {
  display: flex;
  align-items: center;
  gap: 12px;
}

.success-text {
  color: #67c23a;
  font-weight: 500;
}

.failed-text {
  color: #f56c6c;
  font-weight: 500;
}

/* 统计卡片样式 */
.stats-cards {
  margin-bottom: 20px;
}

.stat-card {
  border-radius: 8px;
  transition: transform 0.2s;
}

.stat-card:hover {
  transform: translateY(-2px);
}

.stat-content {
  text-align: center;
  padding: 12px 0;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  line-height: 1.2;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 13px;
  color: var(--tm-text-secondary);
}

/* 历史记录筛选表单样式 */
.history-filter-form {
  margin-bottom: 20px;
  padding: 16px;
  background: var(--tm-bg-card);
  border-radius: 8px;
  border: 1px solid var(--tm-border-light);
}

.history-filter-form .el-form-item {
  margin-bottom: 0;
  margin-right: 16px;
}

.history-filter-form .el-form-item:last-child {
  margin-right: 0;
}

/* 响应式 */
@media (max-width: 768px) {
  .list-toolbar {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
  }

  .toolbar-left,
  .toolbar-right {
    justify-content: center;
  }

  .stats-cards {
    flex-direction: column;
    gap: 12px;
  }

  .stat-card {
    width: 100%;
  }

  .history-filter-form .el-form-item {
    margin-right: 0;
    margin-bottom: 12px;
  }

  .history-filter-form .el-form-item:last-child {
    margin-bottom: 0;
  }
}

/* 步骤详情样式 */
.info-row {
  margin-bottom: 12px;
}

.info-row:last-child {
  margin-bottom: 0;
}

.info-label {
  display: inline-block;
  min-width: 60px;
  color: var(--tm-text-secondary);
  font-size: 13px;
  margin-right: 8px;
}

.info-value {
  color: var(--tm-text-primary);
  font-size: 13px;
  word-break: break-all;
}

.code-block {
  background: #1e1e1e;
  color: #d4d4d4;
  padding: 12px;
  border-radius: var(--tm-radius-small);
  max-height: 300px;
  overflow: auto;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 12px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-all;
  margin: 8px 0 0 0;
  box-shadow: inset 0 2px 8px rgba(0, 0, 0, 0.2);
}
</style>
