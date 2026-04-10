<template>
  <div class="scenario-editor">
    <!-- 顶部信息栏 -->
    <div class="editor-header">
      <div class="header-left">
        <el-button @click="handleBack">
          <el-icon><Back /></el-icon>
          返回
        </el-button>
        <el-input
          v-model="scenarioForm.name"
          class="scenario-name-input"
          placeholder="场景名称"
          @blur="handleSaveBasic"
        />
      </div>
      <div class="header-right">
        <el-select
          v-model="selectedEnvId"
          placeholder="选择执行环境"
          clearable
          style="width: 160px; margin-right: 12px;"
        >
          <el-option
            v-for="env in environments"
            :key="env.id"
            :label="env.name"
            :value="env.id"
          />
        </el-select>
        <el-button @click="handleAddStep">
          <el-icon><Plus /></el-icon>
          添加步骤
        </el-button>
        <el-button type="primary" @click="handleRun" :loading="isRunning">
          <el-icon><VideoPlay /></el-icon>
          运行场景
        </el-button>
      </div>
    </div>

    <!-- 主内容区带标签页 -->
    <el-tabs v-model="activeTab" class="scenario-tabs">
      <el-tab-pane label="步骤编排" name="steps">
        <!-- 步骤列表（支持拖拽） -->
        <div class="steps-container">
          <draggable
            v-model="steps"
            item-key="id"
            handle=".drag-handle"
            @end="handleDragEnd"
            class="steps-list"
          >
            <template #item="{ element, index }">
              <div class="step-card" :class="{ 'is-inactive': !element.is_active }">
                <!-- 拖拽手柄 -->
                <div class="drag-handle">
                  <el-icon><Rank /></el-icon>
                </div>

                <!-- 步骤序号 -->
                <div class="step-order">{{ index + 1 }}</div>

                <!-- 步骤信息 -->
                <div class="step-info">
                  <div class="step-main">
                    <el-tag :type="getMethodType(element.api_case?.method)" effect="dark" size="small">
                      {{ element.api_case?.method || 'GET' }}
                    </el-tag>
                    <span class="step-name">{{ element.api_case?.name || '未选择接口' }}</span>
                  </div>
                  <div class="step-url">{{ element.api_case?.url || '' }}</div>
                </div>

                <!-- 局部变量覆盖 / 提取响应变量 -->
                <div class="step-actions-extend">
                  <el-popover
                    placement="bottom"
                    :width="450"
                    trigger="click"
                    @show="loadExtractors(element)"
                  >
                    <template #reference>
                      <el-button size="small" text>
                        <el-icon><Download /></el-icon>
                        提取变量
                        <el-badge v-if="getExtractorCount(element.extractors) > 0" :value="getExtractorCount(element.extractors)" />
                      </el-button>
                    </template>
                    <div class="extractors-panel">
                      <h4>响应提取变量</h4>
                      <p class="extractors-hint">执行完成后从响应 JSON 提取变量，供给下游步骤使用 &#123;&#123;variable_name&#125;&#125;</p>

                      <div class="extractors-list">
                        <div v-for="(ext, idx) in extractorForm" :key="idx" class="extractor-row">
                          <el-input
                            v-model="ext.variable_name"
                            placeholder="变量名称"
                            size="small"
                            style="width: 120px; margin-right: 8px;"
                          />
                          <el-input
                            v-model="ext.json_path"
                            placeholder="JSONPath 表达式，例如 $.data.token"
                            size="small"
                            style="flex: 1; margin-right: 8px;"
                          />
                          <el-button
                            type="danger"
                            size="small"
                            icon="Delete"
                            @click="removeExtractor(idx)"
                          />
                        </div>
                        <div class="extractor-actions">
                          <el-button size="small" type="primary" plain @click="addExtractor">
                            <el-icon><Plus /></el-icon> 添加规则
                          </el-button>
                          <el-button size="small" type="primary" @click="saveExtractors">
                            保存
                          </el-button>
                        </div>
                      </div>
                    </div>
                  </el-popover>

                  <el-popover
                    placement="bottom"
                    :width="400"
                    trigger="click"
                    @show="loadOverrides(element)"
                  >
                    <template #reference>
                      <el-button size="small" text>
                        <el-icon><Setting /></el-icon>
                        局部覆盖
                        <el-badge v-if="getOverrideCount(element.variable_overrides) > 0" :value="getOverrideCount(element.variable_overrides)" />
                      </el-button>
                    </template>
                    <div class="override-panel">
                      <h4>局部变量覆盖</h4>
                      <p class="override-hint">仅影响此场景中的此步骤，不修改接口库原始定义</p>

                      <el-tabs>
                        <el-tab-pane label="URL 覆盖">
                          <el-input
                            v-model="overrideForm.url"
                            placeholder="可选：覆盖 URL"
                            @change="saveOverrides(element)"
                          />
                        </el-tab-pane>
                        <el-tab-pane label="Headers 覆盖">
                          <div class="override-table">
                            <el-table :data="overrideForm.headers" size="small">
                              <el-table-column label="Key" min-width="100">
                                <template #default="{ row }">
                                  <el-input v-model="row.key" placeholder="Header key" />
                                </template>
                              </el-table-column>
                              <el-table-column label="Value" min-width="150">
                                <template #default="{ row }">
                                  <el-input v-model="row.value" placeholder="Header value" />
                                </template>
                              </el-table-column>
                              <el-table-column width="50">
                                <template #default="{ $index }">
                                  <el-button type="danger" size="small" text @click="removeOverrideHeader($index)">
                                    <el-icon><Delete /></el-icon>
                                  </el-button>
                                </template>
                              </el-table-column>
                            </el-table>
                            <el-button size="small" style="margin-top: 8px" @click="addOverrideHeader">
                              <el-icon><Plus /></el-icon> 添加
                            </el-button>
                          </div>
                        </el-tab-pane>
                        <el-tab-pane label="Payload 覆盖">
                          <div class="override-table">
                            <el-table :data="overrideForm.payloads" size="small">
                              <el-table-column label="Key" min-width="100">
                                <template #default="{ row }">
                                  <el-input v-model="row.key" placeholder="参数名" />
                                </template>
                              </el-table-column>
                              <el-table-column label="Value" min-width="150">
                                <template #default="{ row }">
                                  <el-input v-model="row.value" placeholder="参数值" />
                                </template>
                              </el-table-column>
                              <el-table-column width="50">
                                <template #default="{ $index }">
                                  <el-button type="danger" size="small" text @click="removeOverridePayload($index)">
                                    <el-icon><Delete /></el-icon>
                                  </el-button>
                                </template>
                              </el-table-column>
                            </el-table>
                            <el-button size="small" style="margin-top: 8px" @click="addOverridePayload">
                              <el-icon><Plus /></el-icon> 添加
                            </el-button>
                          </div>
                        </el-tab-pane>
                      </el-tabs>
                    </div>
                  </el-popover>
                </div>

                <!-- 操作按钮 -->
                <div class="step-actions">
                  <el-switch v-model="element.is_active" @change="handleStepActiveChange(element)" />
                  <el-button type="danger" size="small" text @click="handleRemoveStep(element)">
                    <el-icon><Delete /></el-icon>
                  </el-button>
                </div>
              </div>
            </template>
          </draggable>

          <el-empty v-if="steps.length === 0" description="暂无步骤，点击上方添加步骤按钮添加">
            <el-button type="primary" @click="handleAddStep">添加步骤</el-button>
          </el-empty>
        </div>
      </el-tab-pane>

      <el-tab-pane label="数据驱动" name="data-driven">
        <!-- 数据驱动面板 -->
        <div class="data-driven-panel">
          <div class="panel-header">
            <div class="panel-title">
              <el-icon><Grid /></el-icon>
              <span>数据驱动</span>
              <el-tag v-if="datasetColumns.length > 0" type="success" size="small">
                {{ datasetRows.length }} 行数据
              </el-tag>
            </div>
            <div class="panel-actions">
              <el-button size="small" @click="handleRunDataDriven" :disabled="datasetRows.length === 0">
                <el-icon><VideoPlay /></el-icon>
                数据驱动执行
              </el-button>
            </div>
          </div>

          <!-- 数据编辑区 -->
          <div class="data-matrix-container">
            <!-- 操作栏 -->
            <div class="matrix-toolbar">
              <el-button size="small" type="primary" @click="addDataRow">
                <el-icon><Plus /></el-icon> 添加行
              </el-button>
              <el-button size="small" @click="addDataColumn">
                <el-icon><Plus /></el-icon> 添加变量
              </el-button>
              <!-- 前端解析的 CSV/Excel 导入 -->
              <input
                ref="fileInputRef"
                type="file"
                accept=".csv,.xlsx,.xls"
                style="display: none"
                @change="handleFileChange"
              />
              <el-button size="small" @click="triggerFileImport">
                <el-icon><Upload /></el-icon> 导入 CSV/Excel
              </el-button>
              <el-button size="small" @click="clearDataset">
                <el-icon><Delete /></el-icon> 清空
              </el-button>
            </div>

            <!-- 数据表格 -->
            <div class="matrix-table-wrapper" v-if="datasetColumns.length > 0">
              <table class="matrix-table">
                <thead>
                  <tr>
                    <th class="row-index-col">#</th>
                    <th v-for="(col, colIndex) in datasetColumns" :key="'header-' + colIndex">
                      <el-input
                        v-model="datasetColumns[colIndex]"
                        size="small"
                        placeholder="变量名"
                        @change="handleDatasetChange"
                      />
                    </th>
                    <th class="action-col">操作</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(row, rowIndex) in datasetRows" :key="'row-' + rowIndex">
                    <td class="row-index-col">{{ rowIndex + 1 }}</td>
                    <td v-for="(col, colIndex) in datasetColumns" :key="'cell-' + rowIndex + '-' + colIndex">
                      <el-input
                        v-model="datasetRows[rowIndex][colIndex]"
                        size="small"
                        placeholder="值"
                      />
                    </td>
                    <td class="action-col">
                      <el-button type="danger" size="small" text @click="removeDataRow(rowIndex)">
                        <el-icon><Delete /></el-icon>
                      </el-button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            <el-empty v-else description="暂无数据，请添加变量名和数据行" />

            <!-- 使用提示 -->
            <div class="matrix-hint">
              <el-alert type="info" :closable="false" show-icon>
                <template #title>
                  <span>使用提示：在场景中的 URL、Headers、Payload 中使用&#123;&#123;变量名&#125;&#125;引用数据变量，如&#123;&#123;username&#125;&#125;、&#123;&#123;token&#125;&#125;</span>
                </template>
              </el-alert>
            </div>
          </div>
        </div>
      </el-tab-pane>

      <el-tab-pane label="执行历史" name="history">
        <!-- 执行历史面板 -->
        <div class="history-panel">
          <div class="history-toolbar">
            <el-button size="small" @click="refreshExecutionHistory">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
            <span class="history-summary">
              共 {{ executionHistory.total }} 次执行，
              成功: {{ executionHistory.success_count }} 次，
              失败: {{ executionHistory.failed_count }} 次
            </span>
          </div>

          <el-table :data="executionHistory.items" style="width: 100%" v-loading="historyLoading">
            <el-table-column prop="id" label="ID" width="80" align="center" />
            <el-table-column prop="status" label="状态" width="100" align="center">
              <template #default="{ row }">
                <el-tag :type="getStatusType(row.status)" size="small">
                  {{ getStatusText(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="total_steps" label="总步骤" width="80" align="center" />
            <el-table-column prop="success_steps" label="成功" width="80" align="center">
              <template #default="{ row }">
                <span class="success-text">{{ row.success_steps }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="failed_steps" label="失败" width="80" align="center">
              <template #default="{ row }">
                <span class="failed-text">{{ row.failed_steps }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="total_time" label="耗时" width="100" align="center">
              <template #default="{ row }">
                {{ (row.total_time / 1000).toFixed(2) }}s
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="执行时间" width="180" />
            <el-table-column label="操作" width="180" align="center" fixed="right">
              <template #default="{ row }">
                <el-button
                  v-if="row.report_url"
                  size="small"
                  type="primary"
                  link
                  @click="openReport(row.report_url)"
                >
                  查看报告
                </el-button>
              </template>
            </el-table-column>
          </el-table>

          <el-empty v-if="executionHistory.items.length === 0 && !historyLoading" description="暂无执行记录" />
        </div>
      </el-tab-pane>
    </el-tabs>

    <!-- 数据驱动执行结果对话框 -->
    <el-dialog v-model="dataDrivenResultDialogVisible" title="数据驱动执行结果" width="90%" destroy-on-close>
      <div v-if="dataDrivenResult" class="dd-result-content">
        <!-- 汇总信息 -->
        <el-descriptions :column="4" border class="result-summary">
          <el-descriptions-item label="场景名称">{{ dataDrivenResult.scenario_name }}</el-descriptions-item>
          <el-descriptions-item label="数据集">{{ dataDrivenResult.dataset_name }}</el-descriptions-item>
          <el-descriptions-item label="总迭代次数">{{ dataDrivenResult.total_iterations }}</el-descriptions-item>
          <el-descriptions-item label="总耗时">{{ dataDrivenResult.total_duration }} ms</el-descriptions-item>
          <el-descriptions-item label="成功">
            <el-tag type="success">{{ dataDrivenResult.success_iterations }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="失败">
            <el-tag type="danger">{{ dataDrivenResult.failed_iterations }}</el-tag>
          </el-descriptions-item>
        </el-descriptions>

        <!-- 每次迭代结果 -->
        <el-divider>迭代详情</el-divider>
        <div class="iteration-list">
          <el-collapse>
            <el-collapse-item
              v-for="iteration in dataDrivenResult.iterations"
              :key="iteration.iteration_index"
              :name="iteration.iteration_index"
            >
              <template #title>
                <div class="iteration-header">
                  <span>迭代 #{{ iteration.iteration_index + 1 }}</span>
                  <span class="iteration-data">{{ formatDataRow(iteration.data_row) }}</span>
                  <el-tag :type="iteration.success ? 'success' : 'danger'" size="small">
                    {{ iteration.success ? '成功' : '失败' }}
                  </el-tag>
                  <span class="iteration-duration">{{ iteration.duration }} ms</span>
                </div>
              </template>
              <div class="iteration-detail">
                <p v-if="iteration.error" class="error-msg">
                  <el-alert type="error" :title="iteration.error" :closable="false" />
                </p>
                <p v-if="Object.keys(iteration.context_vars || {}).length > 0" class="context-vars">
                  <strong>上下文变量：</strong>
                  <el-tag v-for="(value, key) in iteration.context_vars" :key="key" size="small" style="margin-right: 4px">
                    {{ key }}: {{ value }}
                  </el-tag>
                </p>
                <p v-if="iteration.step_results && iteration.step_results.length > 0" class="step-results">
                  <strong>步骤结果：</strong>
                  <div v-for="step in iteration.step_results" :key="step.step_id" class="step-result-item">
                    <el-tag :type="getMethodType(step.method)" size="small">{{ step.method }}</el-tag>
                    <span>{{ step.api_case_name }}</span>
                    <el-tag :type="step.success ? 'success' : 'danger'" size="small">
                      {{ step.status_code || 'Error' }}
                    </el-tag>
                  </div>
                </p>
              </div>
            </el-collapse-item>
          </el-collapse>
        </div>
      </div>
    </el-dialog>

    <!-- 添加步骤对话框 -->
    <el-dialog v-model="addStepDialogVisible" title="添加步骤" width="70%" destroy-on-close append-to-body>
      <div class="add-step-content">
        <el-input
          v-model="caseSearchKeyword"
          placeholder="搜索接口名称"
          size="default"
          style="width: 300px; margin-bottom: 16px"
          clearable
          @input="handleSearchCases"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>

        <el-table
          ref="caseTableRef"
          :data="availableCases"
          style="width: 100%"
          @selection-change="handleCaseSelectionChange"
        >
          <el-table-column type="selection" width="50" />
          <el-table-column label="请求方法" width="100" align="center">
            <template #default="{ row }">
              <el-tag :type="getMethodType(row.method)" effect="dark" size="small">
                {{ row.method }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="name" label="接口名称" min-width="180" />
          <el-table-column prop="url" label="URL" min-width="280" show-overflow-tooltip />
        </el-table>
      </div>
      <template #footer>
        <el-button @click="addStepDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleConfirmAddSteps">确定添加</el-button>
      </template>
    </el-dialog>

    <!-- 运行结果对话框 -->
    <el-dialog
      v-model="resultDialogVisible"
      title="场景执行结果"
      width="80%"
      append-to-body
      destroy-on-close
    >
      <!-- 后台执行中状态 - 带实时进度条和停止按钮 -->
      <div v-if="isRunning && !runResult" style="padding: 40px 20px; text-align: center;">
        <el-progress
          :percentage="runningTaskProgress?.percent || 0"
          :text-inside="true"
          :stroke-width="24"
          status="success"
          style="margin: 0 auto 20px; max-width: 80%;"
        ></el-progress>

        <p style="margin-top: 15px; color: #666; font-size: 14px;">
          正在执行: {{ runningTaskProgress?.current_api || '初始化中...' }}
        </p>
        <p style="margin-top: 5px; color: #909399; font-size: 13px;">
          {{ runningTaskProgress?.current || 0 }} / {{ runningTaskProgress?.total || 0 }} 步骤
        </p>

        <el-button
          type="danger"
          style="margin-top: 20px;"
          :loading="isCanceling"
          @click="handleCancelTask"
        >
          🛑 停止执行
        </el-button>
      </div>

      <div class="result-content" v-else-if="runResult">
        <div class="result-header-stats">
          <el-tag :type="runResult.failed_steps > 0 ? 'danger' : 'success'" size="large">
            {{ runResult.failed_steps > 0 ? '❌ 有步骤失败' : '✅ 全部通过' }}
          </el-tag>
          <span style="margin-left: 15px; color: #606266;">
            总步骤: {{ runResult.total_steps || 0 }} |
            成功: <span style="color: #67c23a">{{ runResult.success_steps || 0 }}</span> |
            失败: <span style="color: #f56c6c">{{ runResult.failed_steps || 0 }}</span> |
            跳过: <span style="color: #909399">{{ runResult.skipped_count || 0 }}</span> |
            总耗时: {{ runResult.total_time || '0ms' }}
          </span>
        </div>

        <el-divider />

        <!-- 步骤结果列表 -->
        <div class="step-results">
          <div
            v-for="(step, index) in runResult.step_results"
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
            <div v-else class="step-header" @click="toggleStepDetail(index)">
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

              <span style="margin-left: 10px; color: #909399; font-size: 13px;" v-if="step.status !== 'skipped'">
                {{ step.duration || 0 }}ms
              </span>
              <el-icon class="toggle-icon" :class="{ 'is-expanded': expandedSteps.includes(index) }">
                <ArrowRight />
              </el-icon>
            </div>

            <!-- 步骤详情（跳过状态不显示） -->
            <div class="step-detail" v-if="expandedSteps.includes(index) && step.status !== 'skipped'">
              <div class="detail-url">{{ step.url }}</div>

              <!-- 请求信息 -->
              <div class="detail-section" v-if="step.request">
                <h5>请求信息</h5>
                <div class="request-info">
                  <span class="info-tag">{{ step.request.method }} {{ step.request.url }}</span>
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
                  <span class="info-label">状态码:</span>
                  <el-tag :type="getStatusCodeType(step.status_code)" size="small">
                    {{ step.status_code || '无' }}
                  </el-tag>
                </div>
                <div class="response-body">
                  <h5>响应体</h5>
                  <pre class="body-display">{{ formatResponseBody(step.response) }}</pre>
                </div>
              </div>

              <!-- 提取的变量 -->
              <div class="detail-section" v-if="step.extracted_vars && Object.keys(step.extracted_vars).length > 0">
                <h5>提取的变量</h5>
                <el-tag
                  v-for="(value, key) in step.extracted_vars"
                  :key="key"
                  class="var-tag"
                  type="info"
                >
                  {{ key }}: {{ typeof value === 'object' ? JSON.stringify(value) : value }}
                </el-tag>
              </div>
            </div>
          </div>
        </div>

        <!-- 全局变量 -->
        <el-divider />
        <div class="context-vars">
          <h4>执行后的全局变量</h4>
          <el-empty v-if="Object.keys(runResult.context_vars || {}).length === 0" description="无提取的变量" />
          <el-tag
            v-for="(value, key) in runResult.context_vars"
            :key="key"
            class="var-tag"
            type="info"
          >
            {{ key }}: {{ typeof value === 'object' ? JSON.stringify(value) : value }}
          </el-tag>
        </div>
      </div>

      <template #footer>
        <span class="dialog-footer">
          <el-button
            v-show="!isRunning && runResult && runResult.status !== 'running'"
            type="primary"
            style="pointer-events: auto; z-index: 9999;"
            @click="openAllureReport"
          >
            📊 查看 Allure 详细报告
          </el-button>
          <el-button @click="resultDialogVisible = false">关闭</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, VideoPlay, Delete, Rank, Setting, Back, Search, Grid, Upload, Refresh, ArrowRight, Download } from '@element-plus/icons-vue'
import draggable from 'vuedraggable'
import axios from 'axios'
import Papa from 'papaparse'
import * as XLSX from 'xlsx'

const props = defineProps({
  scenarioId: {
    type: [Number, String],
    required: true
  }
})

const emit = defineEmits(['back'])

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

const scenarioForm = ref({
  name: '',
  description: '',
  is_active: true
})

const steps = ref([])
const addStepDialogVisible = ref(false)
const availableCases = ref([])
const caseSearchKeyword = ref('')
const selectedCases = ref([])
const caseTableRef = ref(null)
const resultDialogVisible = ref(false)
const runResult = ref(null)
let pollingTimer = null
const runningTaskProgress = ref(null)

// 标签页
const activeTab = ref('steps')

// 执行历史相关
const historyLoading = ref(false)
const executionHistory = ref({
  total: 0,
  success_count: 0,
  failed_count: 0,
  items: []
})

// 数据驱动相关
const dataDrivenResultDialogVisible = ref(false)
const dataDrivenResult = ref(null)
const datasetColumns = ref([])  // 变量名列表
const datasetRows = ref([])    // 数据行，二维数组
const fileInputRef = ref(null)  // 文件输入引用

const overrideForm = ref({
  url: '',
  headers: [],
  payloads: []
})
const currentOverrideStep = ref(null)

// ========== 提取响应变量配置 ==========
const extractorForm = ref([])
const currentExtractorStep = ref(null)

// 环境选择
const environments = ref([])
const selectedEnvId = ref(null)

// 执行 loading 状态
const isRunning = ref(false)
const isCanceling = ref(false)
let currentTaskId = null  // 当前执行的任务 ID
const expandedSteps = ref([])  // 展开的步骤详情

const getMethodType = (method) => {
  const types = { GET: 'success', POST: 'warning', PUT: 'primary', DELETE: 'danger', PATCH: 'info' }
  return types[method] || 'info'
}

const loadScenario = async () => {
  try {
    const res = await autoTestRequest.get(`/api/auto-test/scenarios/${props.scenarioId}`)
    scenarioForm.value = {
      name: res.name,
      description: res.description,
      is_active: res.is_active
    }
    steps.value = res.steps || []
    // 加载数据集
    await loadDataset()
  } catch (error) {
    ElMessage.error('加载场景失败')
  }
}

const loadDataset = async () => {
  try {
    const res = await autoTestRequest.get(`/api/auto-test/scenarios/${props.scenarioId}/dataset`)
    if (res && res.data_matrix) {
      datasetColumns.value = res.data_matrix.columns || []
      datasetRows.value = res.data_matrix.rows || []
    } else {
      datasetColumns.value = []
      datasetRows.value = []
    }
  } catch (error) {
    console.error('加载数据集失败:', error)
    datasetColumns.value = []
    datasetRows.value = []
  }
}

const saveDataset = async () => {
  try {
    await autoTestRequest.post(`/api/auto-test/scenarios/${props.scenarioId}/dataset`, {
      name: '默认数据集',
      data_matrix: {
        columns: datasetColumns.value,
        rows: datasetRows.value
      }
    })
  } catch (error) {
    console.error('保存数据集失败:', error)
  }
}

const handleDatasetChange = () => {
  // 数据变化时自动保存（防抖）
  clearTimeout(window.datasetSaveTimer)
  window.datasetSaveTimer = setTimeout(() => {
    saveDataset()
  }, 1000)
}

const addDataRow = () => {
  const newRow = datasetColumns.value.map(() => '')
  datasetRows.value.push(newRow)
  handleDatasetChange()
}

const addDataColumn = () => {
  datasetColumns.value.push(`var_${datasetColumns.value.length + 1}`)
  datasetRows.value.forEach(row => row.push(''))
  handleDatasetChange()
}

const removeDataRow = (index) => {
  datasetRows.value.splice(index, 1)
  handleDatasetChange()
}

const clearDataset = async () => {
  try {
    await ElMessageBox.confirm('确定要清空所有数据吗？', '提示', { type: 'warning' })
    datasetColumns.value = []
    datasetRows.value = []
    // 调用后端删除
    await autoTestRequest.delete(`/api/auto-test/scenarios/${props.scenarioId}/dataset`)
    ElMessage.success('已清空')
  } catch (error) {
    if (error !== 'cancel') console.error('清空数据集失败:', error)
  }
}

const handleFileUploadSuccess = (response) => {
  if (response.columns && response.rows) {
    datasetColumns.value = response.columns
    datasetRows.value = response.rows
    saveDataset()
    ElMessage.success(`成功导入 ${response.row_count} 行数据`)
  } else {
    ElMessage.error('文件格式错误')
  }
}

const handleFileUploadError = () => {
  ElMessage.error('文件上传失败')
}

// ========== 前端解析 CSV/Excel ==========

/**
 * 触发文件选择
 */
const triggerFileImport = () => {
  fileInputRef.value?.click()
}

/**
 * 处理文件选择
 * @param {Event} event
 */
const handleFileChange = (event) => {
  const file = event.target.files?.[0]
  if (!file) return

  const fileName = file.name.toLowerCase()

  if (fileName.endsWith('.csv')) {
    parseCSVFile(file)
  } else if (fileName.endsWith('.xlsx') || fileName.endsWith('.xls')) {
    parseExcelFile(file)
  } else {
    ElMessage.error('仅支持 .csv 或 .xlsx/.xls 文件')
  }

  // 清空 input，允许重复选择同一文件
  event.target.value = ''
}

/**
 * 解析 CSV 文件
 * @param {File} file
 */
const parseCSVFile = (file) => {
  Papa.parse(file, {
    header: false,
    skipEmptyLines: true,
    complete: (results) => {
      processFileData(results.data)
    },
    error: (error) => {
      console.error('CSV 解析失败:', error)
      ElMessage.error('CSV 解析失败: ' + error.message)
    }
  })
}

/**
 * 解析 Excel 文件
 * @param {File} file
 */
const parseExcelFile = (file) => {
  const reader = new FileReader()

  reader.onload = (e) => {
    try {
      const data = new Uint8Array(e.target.result)
      const workbook = XLSX.read(data, { type: 'array', cellDates: true })

      const firstSheetName = workbook.SheetNames[0]
      const worksheet = workbook.Sheets[firstSheetName]

      // 转换为二维数组
      const jsonData = XLSX.utils.sheet_to_json(worksheet, { header: 1, defval: '' })

      processFileData(jsonData)
    } catch (error) {
      console.error('Excel 解析失败:', error)
      ElMessage.error('Excel 解析失败: ' + error.message)
    }
  }

  reader.onerror = () => {
    ElMessage.error('文件读取失败')
  }

  reader.readAsArrayBuffer(file)
}

/**
 * 处理解析后的数据
 * @param {Array} data - 二维数组
 */
const processFileData = (data) => {
  if (!data || data.length === 0) {
    ElMessage.warning('文件内容为空')
    return
  }

  if (data.length === 1) {
    ElMessage.warning('文件只有表头，没有数据')
    return
  }

  // 第一行是表头（变量名）
  const columns = data[0].map((col, index) => {
    return String(col).trim() || `变量${index + 1}`
  })

  // 后续行是数据
  const rows = data.slice(1).map(row => {
    return columns.map((_, colIndex) => {
      const cellValue = row[colIndex]
      // 处理 Excel 日期格式
      if (cellValue && typeof cellValue === 'object' && cellValue instanceof Date) {
        return cellValue.toISOString().slice(0, 10)
      }
      return String(cellValue ?? '')
    })
  })

  datasetColumns.value = columns
  datasetRows.value = rows

  // 自动保存到后端
  saveDataset()

  ElMessage.success(`成功导入 ${rows.length} 行数据，共 ${columns.length} 个变量`)
}

const formatDataRow = (dataRow) => {
  if (!dataRow) return ''
  return Object.entries(dataRow).map(([k, v]) => `${k}=${v}`).join(', ')
}

const handleRunDataDriven = async () => {
  if (datasetRows.value.length === 0) {
    ElMessage.warning('请先添加数据')
    return
  }
  try {
    const res = await autoTestRequest.post(`/api/auto-test/scenarios/${props.scenarioId}/run-data-driven`)
    dataDrivenResult.value = res
    dataDrivenResultDialogVisible.value = true
  } catch (error) {
    ElMessage.error('数据驱动执行失败: ' + (error.response?.data?.detail || error.message))
  }
}

const handleSaveBasic = async () => {
  try {
    await autoTestRequest.put(`/api/auto-test/scenarios/${props.scenarioId}`, scenarioForm.value)
  } catch (error) {
    ElMessage.error('保存失败')
  }
}

const handleBack = () => {
  emit('back')
}

const handleAddStep = async () => {
  addStepDialogVisible.value = true
  caseSearchKeyword.value = ''
  selectedCases.value = []
  await loadAvailableCases()
}

const loadAvailableCases = async () => {
  try {
    const params = {}
    if (caseSearchKeyword.value) {
      params.keyword = caseSearchKeyword.value
    }
    const res = await autoTestRequest.get('/api/auto-test/scenarios/available-cases', { params })
    availableCases.value = res || []
  } catch (error) {
    console.error('加载接口列表失败:', error)
  }
}

const handleSearchCases = () => {
  loadAvailableCases()
}

const handleCaseSelectionChange = (selection) => {
  selectedCases.value = selection
}

const handleConfirmAddSteps = async () => {
  if (selectedCases.value.length === 0) {
    ElMessage.warning('请选择至少一个接口')
    return
  }

  try {
    for (let i = 0; i < selectedCases.value.length; i++) {
      const caseItem = selectedCases.value[i]
      await autoTestRequest.post(`/api/auto-test/scenarios/${props.scenarioId}/steps`, {
        api_case_id: caseItem.id,
        step_order: steps.value.length + i,
        is_active: true
      })
    }
    ElMessage.success('添加成功')
    addStepDialogVisible.value = false
    await loadScenario()
  } catch (error) {
    ElMessage.error('添加失败')
  }
}

const handleRemoveStep = async (step) => {
  try {
    await ElMessageBox.confirm('确定要移除此步骤吗？', '提示', { type: 'warning' })
    await autoTestRequest.delete(`/api/auto-test/scenarios/${props.scenarioId}/steps/${step.id}`)
    ElMessage.success('移除成功')
    await loadScenario()
  } catch (error) {
    if (error !== 'cancel') ElMessage.error('移除失败')
  }
}

const handleStepActiveChange = async (step) => {
  try {
    await autoTestRequest.put(`/api/auto-test/scenarios/${props.scenarioId}/steps/${step.id}`, {
      is_active: step.is_active
    })
  } catch (error) {
    ElMessage.error('更新失败')
  }
}

const handleDragEnd = async () => {
  try {
    const stepOrders = steps.value.map((step, index) => ({
      step_id: step.id,
      step_order: index
    }))
    await autoTestRequest.put(`/api/auto-test/scenarios/${props.scenarioId}/steps/reorder`, stepOrders)
  } catch (error) {
    ElMessage.error('保存排序失败')
    await loadScenario()
  }
}

const getOverrideCount = (overrides) => {
  if (!overrides) return 0
  let count = 0
  if (overrides.url) count++
  if (overrides.headers) count += Object.keys(overrides.headers).length
  if (overrides.payload) count += Object.keys(overrides.payload).length
  return count
}

const loadOverrides = (step) => {
  currentOverrideStep.value = step
  const overrides = step.variable_overrides || {}
  overrideForm.value = {
    url: overrides.url || '',
    headers: Object.entries(overrides.headers || {}).map(([key, value]) => ({ key, value })),
    payloads: Object.entries(overrides.payload || {}).map(([key, value]) => ({ key, value }))
  }
}

const addOverrideHeader = () => {
  overrideForm.value.headers.push({ key: '', value: '' })
}

const removeOverrideHeader = (index) => {
  overrideForm.value.headers.splice(index, 1)
}

const addOverridePayload = () => {
  overrideForm.value.payloads.push({ key: '', value: '' })
}

const removeOverridePayload = (index) => {
  overrideForm.value.payloads.splice(index, 1)
}

const saveOverrides = async (step) => {
  const overrides = {}
  if (overrideForm.value.url) overrides.url = overrideForm.value.url
  if (overrideForm.value.headers.length > 0) {
    const headers = {}
    overrideForm.value.headers.forEach(h => { if (h.key) headers[h.key] = h.value })
    if (Object.keys(headers).length > 0) overrides.headers = headers
  }
  if (overrideForm.value.payloads.length > 0) {
    const payloads = {}
    overrideForm.value.payloads.forEach(p => { if (p.key) payloads[p.key] = p.value })
    if (Object.keys(payloads).length > 0) overrides.payload = payloads
  }

  try {
    await autoTestRequest.put(`/api/auto-test/scenarios/${props.scenarioId}/steps/${step.id}`, {
      variable_overrides: Object.keys(overrides).length > 0 ? overrides : null
    })
    step.variable_overrides = Object.keys(overrides).length > 0 ? overrides : null
    ElMessage.success('保存成功')
  } catch (error) {
    ElMessage.error('保存失败')
  }
}

// ========== 提取响应变量方法 ==========

const getExtractorCount = (extractors) => {
  if (!extractors) return 0
  return Array.isArray(extractors) ? extractors.length : 0
}

const loadExtractors = (step) => {
  currentExtractorStep.value = step
  const extractors = step.extractors || []
  if (extractors.length > 0) {
    extractorForm.value = [...extractors]
  } else {
    extractorForm.value = []
  }
}

const addExtractor = () => {
  extractorForm.value.push({
    variable_name: '',
    json_path: ''
  })
}

const removeExtractor = (index) => {
  extractorForm.value.splice(index, 1)
}

const saveExtractors = async () => {
  if (!currentExtractorStep.value) return

  // 过滤掉空规则
  const validExtractors = extractorForm.value.filter(
    ext => ext.variable_name?.trim() && ext.json_path?.trim()
  )

  try {
    await autoTestRequest.put(`/api/auto-test/scenarios/${props.scenarioId}/steps/${currentExtractorStep.value.id}`, {
      extractors: validExtractors.length > 0 ? validExtractors : null
    })
    currentExtractorStep.value.extractors = validExtractors.length > 0 ? validExtractors : null
    ElMessage.success('保存成功')
  } catch (error) {
    ElMessage.error('保存失败')
  }
}

// 停止轮询
const stopPolling = () => {
  if (pollingTimer) {
    clearInterval(pollingTimer)
    pollingTimer = null
  }
}

// 轮询任务状态
const pollTaskStatus = async (taskId) => {
  stopPolling()
  pollingTimer = setInterval(async () => {
    try {
      const res = await autoTestRequest.get(`/api/auto-test/tasks/${taskId}`)
      const state = res.status  // Celery 任务状态: 'PENDING' | 'PROGRESS' | 'completed' | 'SUCCESS' | 'FAILURE' | 'REVOKED'

      if (state === 'completed' || state === 'SUCCESS') {
        stopPolling()
        isRunning.value = false
        runResult.value = res
        expandedSteps.value = []
        if (res && res.step_results) {
          const failedIndex = res.step_results.findIndex(s => s.status === 'failed')
          if (failedIndex >= 0) expandedSteps.value = [failedIndex]
        }
        resultDialogVisible.value = true
        loadExecutionHistory()
        ElMessage.success('执行完成')
      } else if (state === 'failed' || state === 'FAILURE' || state === 'REVOKED') {
        stopPolling()
        isRunning.value = false
        if (state === 'REVOKED') {
          ElMessage.warning('⛔ 任务已被终止')
          resultDialogVisible.value = false
          currentTaskId = null
        } else {
          ElMessage.error('执行失败: ' + (res.error || '未知错误'))
        }
      } else if (state === 'PROGRESS') {
        // 更新进度
        runningTaskProgress.value = res.progress
      }
      // PENDING 继续轮询
    } catch (error) {
      stopPolling()
      isRunning.value = false
      ElMessage.error('查询任务状态失败: ' + (error.response?.data?.detail || error.message))
    }
  }, 2000)
}

const handleRun = async () => {
  if (isRunning.value) {
    ElMessage.warning('已有任务正在执行中，请稍候...')
    return
  }
  isRunning.value = true
  runningTaskProgress.value = null
  resultDialogVisible.value = true
  runResult.value = null
  expandedSteps.value = []
  try {
    ElMessage.info({ message: '任务已提交，后台正在执行中，请稍候...', duration: 3000 })
    const res = await autoTestRequest.post(`/api/auto-test/scenarios/${props.scenarioId}/run`, {
      env_id: selectedEnvId.value
    })
    const taskId = res?.data?.task_id || res?.task_id
    if (!taskId) {
      isRunning.value = false
      ElMessage.error('任务提交失败，未获取到 task_id')
      return
    }
    // 保存当前任务 ID
    currentTaskId = taskId
    pollTaskStatus(taskId)
  } catch (error) {
    isRunning.value = false
    stopPolling()
    ElMessage.error('提交任务失败: ' + (error.response?.data?.detail || error.message))
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

// 切换步骤详情展开/收起
const toggleStepDetail = (index) => {
  const idx = expandedSteps.value.indexOf(index)
  if (idx > -1) {
    expandedSteps.value.splice(idx, 1)
  } else {
    expandedSteps.value.push(index)
  }
}

// 格式化响应体显示
const formatResponseBody = (response) => {
  if (!response) return ''
  if (typeof response === 'string') return response
  try {
    return JSON.stringify(response, null, 2)
  } catch {
    return String(response)
  }
}

// 获取状态码对应的 Tag 类型
const getStatusCodeType = (statusCode) => {
  if (!statusCode) return 'info'
  if (statusCode >= 200 && statusCode < 300) return 'success'
  if (statusCode >= 400 && statusCode < 500) return 'warning'
  if (statusCode >= 500) return 'danger'
  return 'info'
}

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

// 打开 Allure 详细报告
const openAllureReport = () => {
  console.log('--- 终极接管 Allure 按钮 ---', runResult.value);

  // 尝试获取当前运行结果 或 历史详情数据
  const resultData = runResult.value || {};

  // 第一优先级：后端传了 report_url
  // 第二优先级：前端自己用 report_id 拼装！
  let url = resultData.report_url;
  if (!url && resultData.report_id) {
    url = `/reports/${resultData.report_id}/index.html`;
  }

  if (url) {
    console.log('即将打开报告地址:', `http://127.0.0.1:5002${url}`);
    // 强行补齐前缀并打开
    window.open(resolveReportUrl(url), '_blank');
  } else {
    ElMessage.error('执行结果中缺失 report_id，无法拼接报告地址！');
  }
};

// ========== 执行历史相关 ==========
const loadExecutionHistory = async () => {
  historyLoading.value = true
  try {
    const res = await autoTestRequest.get(`/api/auto-test/scenarios/${props.scenarioId}/history`)
    const items = res.items || []
    // 统计成功失败 - 后端使用 completed 表示成功完成
    const successCount = items.filter(item => item.status === 'completed').length
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

const refreshExecutionHistory = () => {
  loadExecutionHistory()
}

const getStatusType = (status) => {
  const types = { success: 'success', failed: 'danger', error: 'warning' }
  return types[status] || 'info'
}

const getStatusText = (status) => {
  const texts = { success: '成功', failed: '失败', error: '异常' }
  return texts[status] || status
}

const openReport = (reportUrl) => {
  // 拼接完整 URL
  const fullUrl = resolveReportUrl(reportUrl)
  window.open(fullUrl, '_blank')
}

// 加载环境列表
const loadEnvironments = async () => {
  try {
    const res = await autoTestRequest.get('/api/interface-test/environments')
    environments.value = res || []
    // 默认选中第一个
    if (environments.value.length > 0) {
      const defaultEnv = environments.value.find(e => e.is_default)
      if (defaultEnv) {
        selectedEnvId.value = defaultEnv.id
      } else {
        selectedEnvId.value = environments.value[0].id
      }
    }
  } catch (error) {
    console.error('加载环境列表失败:', error)
  }
}

onMounted(() => {
  loadScenario()
  loadExecutionHistory()
  loadEnvironments()
})

onUnmounted(() => {
  stopPolling()
})
</script>

<style scoped>
.scenario-editor {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--tm-card-bg);
  border-radius: 12px;
  border: var(--tm-card-border);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
}

.editor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  background: rgba(var(--tm-bg-page-rgb), 0.5);
  border-bottom: 1px solid var(--tm-border-light);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-right {
  display: flex;
  gap: 12px;
}

.scenario-name-input {
  width: 300px;
  font-size: 18px;
  font-weight: 500;
}

.scenario-name-input :deep(.el-input__inner) {
  border: none;
  background: transparent;
}

.steps-container {
  padding: 0;
  overflow: visible;
}

.steps-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.step-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: var(--tm-card-bg);
  border: 1px solid var(--tm-border-light);
  border-radius: 4px;
  transition: all 0.3s;
}

.step-card:hover {
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.step-card.is-inactive {
  opacity: 0.5;
  background: rgba(var(--tm-bg-page-rgb), 0.5);
}

.drag-handle {
  cursor: move;
  color: var(--tm-text-secondary);
  font-size: 18px;
}

.step-order {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--tm-color-primary);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 500;
}

.step-info {
  flex: 1;
  min-width: 0;
}

.step-main {
  display: flex;
  align-items: center;
  gap: 8px;
}

.step-name {
  font-weight: 500;
  color: var(--tm-text-primary);
}

.step-url {
  margin-top: 4px;
  font-size: 12px;
  color: var(--tm-text-secondary);
  font-family: monospace;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.step-overrides {
  display: flex;
  gap: 8px;
}

.step-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.override-panel h4 {
  margin: 0 0 8px;
  color: var(--tm-text-primary);
}

.override-hint {
  margin: 0 0 16px;
  color: var(--tm-text-secondary);
  font-size: 12px;
}

.add-step-content {
  max-height: 60vh;
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
}

.summary-info {
  color: #606266;
}

.step-result-card {
  padding: 12px;
  margin-bottom: 12px;
  border: 1px solid var(--tm-border-light);
  border-radius: 4px;
  background: rgba(var(--tm-bg-page-rgb), 0.5);
}

.step-result-card.is-failed {
  border-color: rgba(245, 108, 108, 0.6);
  background: rgba(245, 108, 108, 0.05);
}

.step-header {
  display: flex;
  align-items: center;
  gap: 10px;
}

.step-detail {
  margin-top: 8px;
  padding-left: 38px;
}

.info-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.info-label {
  color: var(--tm-text-secondary);
}

.context-vars h4 {
  margin: 0 0 12px;
  color: var(--tm-text-primary);
}

.vars-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.var-tag {
  font-size: 12px;
}

/* 数据驱动面板 */
.data-driven-panel {
  background: var(--tm-card-bg);
  border: 1px solid var(--tm-border-light);
  border-radius: 4px;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid var(--tm-border-light);
  background: rgba(var(--tm-bg-page-rgb), 0.5);
}

.panel-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
  font-size: 14px;
}

.panel-actions {
  display: flex;
  gap: 8px;
}

.data-matrix-container {
  padding: 16px;
}

.matrix-toolbar {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.matrix-table-wrapper {
  overflow-x: auto;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
}

.matrix-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.matrix-table th,
.matrix-table td {
  padding: 8px;
  border: 1px solid var(--tm-border-light);
  text-align: left;
}

.matrix-table th {
  background: rgba(var(--tm-bg-page-rgb), 0.5);
  font-weight: 500;
  color: var(--tm-text-primary);
}

.matrix-table .row-index-col {
  width: 50px;
  text-align: center;
  background: rgba(var(--tm-bg-page-rgb), 0.5);
  color: var(--tm-text-secondary);
}

.matrix-table .action-col {
  width: 60px;
  text-align: center;
}

.matrix-table td .el-input {
  width: 100%;
}

.matrix-table td .el-input__inner {
  border: none;
  padding: 0 8px;
}

.matrix-table td .el-input__inner:focus {
  border: 1px solid #409eff;
  border-radius: 4px;
}

.matrix-hint {
  margin-top: 12px;
}

.matrix-hint code {
  background: rgba(var(--tm-bg-page-rgb), 0.5);
  padding: 2px 6px;
  border-radius: 3px;
  font-family: monospace;
  color: var(--tm-color-primary);
  border: 1px solid var(--tm-border-light);
}

/* 数据驱动结果 */
.dd-result-content {
  max-height: 70vh;
  overflow: auto;
}

.result-content {
  max-height: 70vh;
  overflow: auto;
}

.result-header-stats {
  display: flex;
  align-items: center;
  gap: 16px;
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
  border-color: rgba(245, 108, 108, 0.4);
  background: rgba(245, 108, 108, 0.02);
}

.step-result-card.is-skipped {
  opacity: 0.6;
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

.context-vars h4 {
  margin: 0 0 12px;
  color: var(--tm-text-primary);
}

.var-tag {
  margin: 4px;
}

.iteration-header {
  display: flex;
  align-items: center;
  gap: 12px;
}

.iteration-data {
  color: #909399;
  font-size: 12px;
}

.iteration-duration {
  color: #909399;
  font-size: 12px;
}

.iteration-detail {
  padding: 12px;
  background: rgba(var(--tm-bg-page-rgb), 0.5);
  border-radius: 4px;
}

.step-results {
  margin-top: 8px;
}

.step-result-item {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 4px;
}

/* 标签页样式 */
.scenario-tabs {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: var(--tm-card-bg);
  overflow: hidden;
  border-radius: 0 0 12px 12px;
}

:deep(.el-tabs__content) {
  flex: 1;
  overflow: auto;
  padding: 16px;
}

:deep(.el-tabs__header) {
  background: rgba(var(--tm-bg-page-rgb), 0.5);
  margin: 0;
  border-bottom: 1px solid var(--tm-border-light);
}

/* 执行历史面板 */
.history-panel {
  background: var(--tm-card-bg);
  border-radius: 4px;
  border: 1px solid var(--tm-border-light);
  padding: 16px;
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

.history-toolbar {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
}

.history-summary {
  color: var(--tm-text-secondary);
  font-size: 14px;
}

.success-text {
  color: #67c23a;
  font-weight: 500;
}

.failed-text {
  color: #f56c6c;
  font-weight: 500;
}

/* 提取变量面板样式 */
.extractors-panel h4 {
  margin: 0 0 8px;
  color: var(--tm-text-primary);
}

.extractors-hint {
  margin: 0 0 16px;
  color: var(--tm-text-secondary);
  font-size: 12px;
}

.extractors-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.extractor-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.extractor-actions {
  display: flex;
  gap: 8px;
  margin-top: 8px;
}

.step-actions-extend {
  display: flex;
  gap: 8px;
}
</style>
