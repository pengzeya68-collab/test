<template>
  <div class="interface-test-list">
    <div class="main-container">
      <!-- 左侧：文件夹树 -->
      <div class="left-panel">
        <div class="folder-header">
          <span class="folder-title">📁 接口分组</span>
          <el-button type="primary" size="small" link @click="createFolder">
            <el-icon><Plus /></el-icon>
            新建分组
          </el-button>
        </div>
        <div class="folder-tree">
          <el-tree
            ref="folderTree"
            :data="folderTreeData"
            :props="treeProps"
            node-key="id"
            default-expand-all
            @node-click="handleFolderClick"
            v-loading="foldersLoading"
            empty-text="暂无分组"
          >
            <template #default="{ node }">
              <span class="tree-node-content">
                <span class="folder-name">{{ node.label }}</span>
                <el-tag size="small" type="info">{{ node.caseCount }}</el-tag>
              </span>
            </template>
          </el-tree>
        </div>
      </div>

      <!-- 右侧：内容区 -->
      <div class="right-panel">
        <!-- 顶部操作栏 -->
        <div class="header-bar">
          <div class="title-section">
            <h1 class="page-title">🌐 在线接口测试</h1>
            <span class="case-count">共 {{ totalCases }} 个用例
              <template v-if="currentFolder">» {{ currentFolder.name }}</template>
            </span>
          </div>
          <div class="header-actions">
            <!-- 批量导入下拉菜单 -->
            <el-dropdown trigger="click" @command="handleImportCommand">
              <el-button type="success" plain>
                <el-icon><Upload /></el-icon>
                导入
                <el-icon class="el-icon--right"><ArrowDown /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="postman">导入 Postman</el-dropdown-item>
                  <el-dropdown-item command="swagger">导入 Swagger/OpenAPI</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
            <el-button type="primary" @click="createNew">
              <el-icon><Plus /></el-icon>
              新建用例
            </el-button>
            <el-button type="success" @click="openRunTestDialog">
              <el-icon><VideoPlay /></el-icon>
              执行测试
            </el-button>
            <el-button type="info" @click="openPlanManager">
              <el-icon><Document /></el-icon>
              测试计划
            </el-button>
            <el-button type="warning" @click="openReportManager">
              <el-icon><Clock /></el-icon>
              执行历史
            </el-button>
            <el-button type="primary" plain icon="Setting" @click="envManagerVisible = true">
              环境管理
            </el-button>
          </div>
        </div>

        <!-- 搜索和过滤 -->
        <div class="filter-bar">
          <el-input
            v-model="searchKeyword"
            placeholder="搜索用例名称或URL..."
            prefix-icon="Search"
            clearable
            style="width: 300px"
            @input="handleSearch"
          />
          <el-select v-model="filterMethod" placeholder="请求方法" clearable style="width: 120px" @change="handleSearch">
            <el-option label="全部" value="" />
            <el-option label="GET" value="GET" />
            <el-option label="POST" value="POST" />
            <el-option label="PUT" value="PUT" />
            <el-option label="DELETE" value="DELETE" />
            <el-option label="PATCH" value="PATCH" />
          </el-select>
          <el-select v-model="selectedEnvId" placeholder="选择环境" clearable style="width: 180px">
            <el-option
              v-for="env in environments"
              :key="env.id"
              :label="env.name"
              :value="env.id"
            />
          </el-select>
        </div>

        <!-- 用例列表 -->
        <div class="case-list-container">
          <div v-loading="loading" class="case-table-wrapper">
            <el-table
              :data="paginatedCases"
              row-key="id"
              border
              size="small"
              style="width: 100%"
              @selection-change="handleSelectionChange"
            >
              <el-table-column type="selection" width="50" align="center" />
              <el-table-column label="方法" width="80" align="center">
                <template #default="{ row }">
                  <el-tag :type="getMethodTagType(row.method)" size="small">
                    {{ row.method }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="name" label="用例名称" min-width="180" show-overflow-tooltip />
              <el-table-column prop="url" label="URL" min-width="250" show-overflow-tooltip />
              <el-table-column prop="description" label="描述" min-width="120" show-overflow-tooltip />
              <el-table-column label="更新时间" width="100">
                <template #default="{ row }">
                  {{ formatDate(row.updated_at) }}
                </template>
              </el-table-column>
              <el-table-column label="操作" width="220" fixed="right">
                <template #default="{ row }">
                  <el-button type="primary" size="small" link @click="openCase(row.id)">编辑</el-button>
                  <el-button type="info" size="small" link @click="viewCaseDetail(row)">详情</el-button>
                  <el-button type="success" size="small" link @click="runSingleCase(row)">运行</el-button>
                  <el-button type="danger" size="small" link @click="deleteCase(row.id)">删除</el-button>
                </template>
              </el-table-column>
            </el-table>

            <!-- 分页 -->
            <div class="pagination-wrapper" v-if="totalCases > 0">
              <el-pagination
                v-model:current-page="currentPage"
                v-model:page-size="pageSize"
                :page-sizes="[10, 20, 50, 100]"
                :total="totalCases"
                layout="total, sizes, prev, pager, next, jumper"
                background
              />
            </div>

            <!-- 空状态 -->
            <div v-if="!loading && filteredCases.length === 0" class="empty-state">
              <el-empty :description="searchKeyword || filterMethod || currentFolder ? '没有找到匹配的用例' : '还没有接口测试用例'">
                <el-button v-if="!searchKeyword && !filterMethod && !currentFolder" type="primary" @click="createNew">创建第一个用例</el-button>
                <el-button v-else type="primary" @click="clearFilters">清除筛选</el-button>
              </el-empty>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ========== 对话框 ========== -->

    <!-- 新建文件夹对话框 -->
    <el-dialog
      v-model="createFolderDialogVisible"
      title="新建接口分组"
      width="500px"
      :close-on-click-modal="false"
    >
      <el-form :model="newFolder" label-width="80px">
        <el-form-item label="分组名称">
          <el-input v-model="newFolder.name" placeholder="给分组起个名字" />
        </el-form-item>
        <el-form-item label="分组描述">
          <el-input v-model="newFolder.description" type="textarea" rows="2" placeholder="描述一下这个分组的用途" />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="createFolderDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="saveFolder">保存</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 用例详情对话框 -->
    <el-dialog
      v-model="caseDetailDialogVisible"
      title="用例详情"
      width="80%"
      :close-on-click-modal="false"
    >
      <div v-if="currentCase" class="case-detail-content">
        <el-descriptions :column="2" border size="small">
          <el-descriptions-item label="用例名称">{{ currentCase.name }}</el-descriptions-item>
          <el-descriptions-item label="请求方法">
            <el-tag :type="getMethodTagType(currentCase.method)" size="small">{{ currentCase.method }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="URL" :span="2">{{ currentCase.url }}</el-descriptions-item>
          <el-descriptions-item label="描述" :span="2">{{ currentCase.description || '无' }}</el-descriptions-item>
        </el-descriptions>

        <el-tabs style="margin-top: 20px">
          <el-tab-pane label="请求信息">
            <div class="request-info">
              <h4>Headers</h4>
              <pre class="code-block">{{ formatJson(currentCase.headers) }}</pre>

              <h4>Body</h4>
              <pre class="code-block">{{ currentCase.body || '无' }}</pre>
            </div>
          </el-tab-pane>
          <el-tab-pane label="历史响应" v-if="caseExecutionHistory.length > 0">
            <el-timeline>
              <el-timeline-item
                v-for="(exec, index) in caseExecutionHistory"
                :key="index"
                :timestamp="exec.executed_at"
                placement="top"
              >
                <el-card shadow="hover">
                  <div class="execution-summary">
                    <el-tag :type="exec.status >= 200 && exec.status < 300 ? 'success' : 'danger'">
                      状态码: {{ exec.status || 'Error' }}
                    </el-tag>
                    <span class="exec-time">耗时: {{ exec.time }}ms</span>
                  </div>
                  <div v-if="exec.response" class="response-preview">
                    <h5>响应内容:</h5>
                    <pre class="code-block">{{ formatResponse(exec.response) }}</pre>
                  </div>
                  <div v-if="exec.error" class="error-preview">
                    <h5>错误信息:</h5>
                    <pre class="code-block error">{{ exec.error }}</pre>
                  </div>
                </el-card>
              </el-timeline-item>
            </el-timeline>
          </el-tab-pane>
          <el-tab-pane v-else label="历史响应">
            <el-empty description="暂无执行记录" />
          </el-tab-pane>
        </el-tabs>
      </div>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="caseDetailDialogVisible = false">关闭</el-button>
          <el-button type="success" @click="runSingleCase(currentCase)">运行此用例</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 执行测试对话框 - 选择或创建测试计划 -->
    <el-dialog
      v-model="runDialogVisible"
      title="执行测试"
      width="70%"
      :close-on-click-modal="false"
    >
      <div v-if="testPlans.length === 0" class="no-plan-guide">
        <el-empty description="还没有测试计划">
          <el-button type="primary" @click="openCreatePlanDialog">创建测试计划</el-button>
        </el-empty>
      </div>

      <div v-else class="run-plan-section">
        <div class="plan-select-section">
          <span>选择测试计划：</span>
          <el-select v-model="selectedPlanId" placeholder="请选择测试计划" style="width: 300px" @change="onPlanChange">
            <el-option
              v-for="plan in testPlans"
              :key="plan.id"
              :label="`${plan.name} (${plan.case_count}个用例)`"
              :value="plan.id"
            />
          </el-select>
          <el-button type="info" link @click="openCreatePlanDialog">新建计划</el-button>
        </div>

        <div v-if="selectedPlanId" class="plan-preview">
          <el-alert
            :title="`计划包含 ${selectedPlanCases.length} 个用例`"
            type="info"
            :closable="false"
          />
          <div class="plan-case-list">
            <el-table
              :data="selectedPlanCases"
              row-key="id"
              border
              size="small"
              style="margin-top: 10px"
              max-height="300"
            >
              <el-table-column label="顺序" width="60" align="center">
                <template #default="{ $index }">
                  <el-tag type="info">{{ $index + 1 }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column label="方法" width="80" align="center">
                <template #default="{ row }">
                  <el-tag :type="getMethodTagType(row.method)" size="small">{{ row.method }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="name" label="用例名称" />
              <el-table-column prop="url" label="URL" show-overflow-tooltip />
            </el-table>
          </div>
        </div>
      </div>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="runDialogVisible = false">取消</el-button>
          <el-button
            type="success"
            @click="executePlan"
            :disabled="!selectedPlanId || selectedPlanCases.length === 0 || executing"
            :loading="executing"
          >
            {{ executing ? '执行中...' : '开始执行' }}
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 创建测试计划对话框 -->
    <el-dialog
      v-model="createPlanDialogVisible"
      title="创建测试计划"
      width="80%"
      :close-on-click-modal="false"
    >
      <div class="create-plan-content">
        <el-form :model="newPlan" label-width="100px">
          <el-form-item label="计划名称">
            <el-input v-model="newPlan.name" placeholder="给你的测试计划起个名字" />
          </el-form-item>
          <el-form-item label="计划描述">
            <el-input v-model="newPlan.description" type="textarea" rows="2" placeholder="描述一下这个测试计划的用途" />
          </el-form-item>
          <el-form-item label="测试环境">
            <el-select v-model="newPlan.environment_id" placeholder="选择测试环境" style="width: 100%">
              <el-option
                v-for="env in environments"
                :key="env.id"
                :label="env.name + (env.is_default ? ' (默认)' : '')"
                :value="env.id"
              />
            </el-select>
          </el-form-item>
        </el-form>

        <div class="case-selection-section">
          <div class="section-header">
            <span class="section-title">选择用例</span>
            <div class="selection-actions">
              <el-checkbox v-model="selectAll" @change="handleSelectAll">全选</el-checkbox>
              <span class="selected-count">已选 {{ selectedCaseIds.length }} 个</span>
            </div>
          </div>

          <!-- 选择用例的搜索过滤 -->
          <div class="filter-bar-small">
            <el-input
              v-model="planSearchKeyword"
              placeholder="搜索用例..."
              prefix-icon="Search"
              clearable
              size="small"
              style="width: 200px"
            />
            <el-select v-model="planFilterMethod" placeholder="方法" clearable size="small" style="width: 100px">
              <el-option label="全部" value="" />
              <el-option label="GET" value="GET" />
              <el-option label="POST" value="POST" />
              <el-option label="PUT" value="PUT" />
              <el-option label="DELETE" value="DELETE" />
            </el-select>
          </div>

          <el-table
            ref="planCaseTable"
            :data="filteredPlanCases"
            row-key="id"
            border
            size="small"
            style="margin-top: 10px"
            max-height="250"
            @selection-change="handlePlanSelectionChange"
          >
            <el-table-column type="selection" width="50" />
            <el-table-column label="方法" width="80" align="center">
              <template #default="{ row }">
                <el-tag :type="getMethodTagType(row.method)" size="small">{{ row.method }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="name" label="用例名称" />
            <el-table-column prop="url" label="URL" show-overflow-tooltip />
          </el-table>
        </div>

        <div v-if="selectedCaseIds.length > 0" class="order-section">
          <div class="section-header">
            <span class="section-title">调整执行顺序</span>
            <span class="hint">拖拽调整，从上到下依次执行</span>
          </div>
          <ElTableDraggable @row-dragend="onRowDragEnd">
            <el-table
              :data="orderedSelectedCases"
              row-key="id"
              border
              size="small"
              style="margin-top: 10px"
            >
              <el-table-column width="50" align="center">
                <template #default>
                  <el-icon style="cursor: move; color: #909399;"><Rank /></el-icon>
                </template>
              </el-table-column>
              <el-table-column label="顺序" width="60" align="center">
                <template #default="{ $index }">
                  <el-tag type="info">{{ $index + 1 }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column label="方法" width="80" align="center">
                <template #default="{ row }">
                  <el-tag :type="getMethodTagType(row.method)" size="small">{{ row.method }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="name" label="用例名称" />
              <el-table-column label="操作" width="80" align="center">
                <template #default="{ row, $index }">
                  <el-button type="danger" size="small" link @click="removeFromOrdered($index)">移除</el-button>
                </template>
              </el-table-column>
            </el-table>
          </ElTableDraggable>
        </div>
      </div>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="createPlanDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="savePlan" :disabled="!newPlan.name.trim() || selectedCaseIds.length === 0">
            保存计划
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 测试计划管理对话框 -->
    <el-dialog
      v-model="planDialogVisible"
      title="测试计划管理"
      width="70%"
      :close-on-click-modal="false"
    >
      <div class="plan-header">
        <el-button type="primary" @click="openCreatePlanDialog">
          <el-icon><Plus /></el-icon>
          新建测试计划
        </el-button>
      </div>

      <el-table :data="testPlans" row-key="id" border style="width: 100%; margin-top: 15px">
        <el-table-column prop="name" label="计划名称" width="200" />
        <el-table-column prop="description" label="描述" />
        <el-table-column prop="case_count" label="用例数" width="100" align="center" />
        <el-table-column prop="updated_at" label="更新时间" width="160" />
        <el-table-column label="操作" width="250" align="center">
          <template #default="{ row }">
            <el-button type="success" size="small" link @click="executePlanById(row.id)">执行</el-button>
            <el-button type="primary" size="small" link @click="editPlan(row)">编辑</el-button>
            <el-button type="danger" size="small" link @click="deletePlan(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="testPlans.length === 0" description="暂无测试计划" />
    </el-dialog>

    <!-- 测试报告历史对话框 -->
    <el-dialog
      v-model="reportDialogVisible"
      title="执行历史"
      width="90%"
      :close-on-click-modal="false"
    >
      <div class="report-header">
        <el-button type="primary" @click="fetchReports" :loading="reportsLoading">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>

      <el-table :data="reports" v-loading="reportsLoading" border style="width: 100%; margin-top: 15px">
        <el-table-column prop="id" label="报告ID" width="80" />
        <el-table-column prop="plan_name" label="测试计划" width="180" />
        <el-table-column prop="total" label="总数" width="80" align="center" />
        <el-table-column prop="success" label="成功" width="80" align="center">
          <template #default="{ row }">
            <el-tag type="success" size="small">{{ row.success }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="failed" label="失败" width="80" align="center">
          <template #default="{ row }">
            <el-tag type="danger" size="small">{{ row.failed }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="total_time" label="耗时" width="100" align="center">
          <template #default="{ row }">
            {{ row.total_time }}ms
          </template>
        </el-table-column>
        <el-table-column prop="executed_at" label="执行时间" width="180" />
        <el-table-column label="操作" width="220" align="center">
          <template #default="{ row }">
            <el-button type="primary" size="small" link @click="viewReport(row)">查看详情</el-button>
            <el-button type="warning" size="small" link @click="reRunPlan(row)">再次运行</el-button>
            <el-button type="danger" size="small" link @click="deleteReport(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 报告分页 -->
      <div class="pagination-wrapper" v-if="reportTotal > 0">
        <el-pagination
          v-model:current-page="reportPage"
          v-model:page-size="reportPageSize"
          :page-sizes="[10, 20, 50]"
          :total="reportTotal"
          layout="total, sizes, prev, pager, next, jumper"
          background
          @size-change="handleReportPageSizeChange"
          @current-change="handleReportPageChange"
        />
      </div>

      <el-empty v-if="!reportsLoading && reports.length === 0" description="暂无执行记录" />
    </el-dialog>

    <!-- 自动化测试结果对话框 -->
    <el-dialog
      v-model="autoTestDialogVisible"
      title="测试执行结果"
      width="95%"
      :close-on-click-modal="false"
    >
      <div class="auto-test-summary">
        <div class="summary-left">
          <el-tag size="large" :type="autoTestResult.failed === 0 ? 'success' : 'warning'">
            {{ autoTestResult.total }} 个用例，
            {{ autoTestResult.success }} 个成功，
            {{ autoTestResult.failed }} 个失败
          </el-tag>
          <span class="total-time">总耗时: {{ autoTestResult.totalTime }}ms</span>
        </div>
        <div class="summary-right">
          <el-button type="primary" @click="exportReport">
            <el-icon><Download /></el-icon>
            导出报告
          </el-button>
        </div>
      </div>

      <el-table :data="autoTestResult.results" border size="small" style="margin-top: 15px" max-height="400">
        <el-table-column label="顺序" width="60" align="center">
          <template #default="{ $index }">
            <el-tag type="info">{{ $index + 1 }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="name" label="用例名称" width="180" show-overflow-tooltip />
        <el-table-column prop="method" label="方法" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="getMethodTagType(row.method)" size="small">{{ row.method }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="url" label="URL" min-width="200" show-overflow-tooltip />
        <el-table-column prop="status" label="状态码" width="100" align="center">
          <template #default="{row}">
            <el-tag :type="row.status >= 200 && row.status < 300 ? 'success' : 'danger'" size="small">
              {{ row.status || 'Error' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="time" label="耗时(ms)" width="100" align="center" />
        <el-table-column label="操作" width="80" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" link @click="viewResultDetail(row)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>

    <!-- 测试结果详情对话框 -->
    <el-dialog
      v-model="resultDetailDialogVisible"
      title="执行详情"
      width="80%"
      :close-on-click-modal="false"
    >
      <div v-if="currentResult" class="result-detail-content">
        <el-descriptions :column="2" border size="small">
          <el-descriptions-item label="用例名称">{{ currentResult.name }}</el-descriptions-item>
          <el-descriptions-item label="请求方法">
            <el-tag :type="getMethodTagType(currentResult.method)" size="small">{{ currentResult.method }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="状态码" :span="2">
            <el-tag :type="currentResult.status >= 200 && currentResult.status < 300 ? 'success' : 'danger'" size="large">
              {{ currentResult.status || 'Error' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="耗时" :span="2">{{ currentResult.time }}ms</el-descriptions-item>
          <el-descriptions-item label="请求URL" :span="2">
            <div class="url-break">{{ currentResult.url }}</div>
          </el-descriptions-item>
        </el-descriptions>

        <el-tabs style="margin-top: 20px">
          <el-tab-pane label="请求信息">
            <div class="request-info">
              <h4>Request Headers</h4>
              <pre class="code-block">{{ formatJson(currentResult.requestHeaders) }}</pre>

              <h4>Request Body</h4>
              <pre class="code-block">{{ currentResult.requestBody || '无' }}</pre>
            </div>
          </el-tab-pane>
          <el-tab-pane label="响应信息">
            <div v-if="currentResult.response" class="response-info">
              <h4>Response Headers</h4>
              <pre class="code-block">{{ formatJson(currentResult.responseHeaders) }}</pre>

              <h4>Response Body</h4>
              <pre class="code-block">{{ formatResponse(currentResult.response) }}</pre>
            </div>
            <div v-else-if="currentResult.error" class="error-info">
              <h4>错误信息</h4>
              <pre class="code-block error">{{ currentResult.error }}</pre>
            </div>
            <el-empty v-else description="无响应数据" />
          </el-tab-pane>
        </el-tabs>
      </div>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="resultDetailDialogVisible = false">关闭</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 导入弹窗 -->
    <el-dialog
      v-model="importDialogVisible"
      :title="importType === 'postman' ? '导入 Postman Collection' : '导入 Swagger/OpenAPI'"
      width="600px"
      :before-close="handleImportClose"
    >
      <div class="import-container" v-loading="importing">
        <el-alert
          :title="importType === 'postman' ? '请选择导出的 Postman Collection v2.1 JSON 文件' : '请提供 Swagger/OpenAPI 的 JSON 文件或在线地址'"
          type="info"
          show-icon
          style="margin-bottom: 20px"
        />

        <el-form label-width="100px">
          <!-- OpenAPI/Swagger 允许在线 URL 或文件上传 -->
          <el-form-item v-if="importType === 'swagger'" label="获取方式">
            <el-radio-group v-model="swaggerImportSource">
              <el-radio value="url" label="url">在线 URL</el-radio>
              <el-radio value="file" label="file">上传文件</el-radio>
            </el-radio-group>
          </el-form-item>

          <el-form-item v-if="importType === 'swagger' && swaggerImportSource === 'url'" label="在线地址">
            <el-input v-model="swaggerUrl" placeholder="http://api.example.com/v2/api-docs" />
          </el-form-item>

          <!-- 统一的文件上传框 -->
          <el-form-item v-show="importType === 'postman' || (importType === 'swagger' && swaggerImportSource === 'file')" label="选择文件">
            <el-upload
              class="upload-demo"
              drag
              action=""
              :auto-upload="false"
              :limit="1"
              :on-change="handleFileChange"
              :on-remove="handleFileRemove"
              accept=".json"
            >
              <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
              <div class="el-upload__text">
                将文件拖到此处，或 <em>点击上传</em>
              </div>
              <template #tip>
                <div class="el-upload__tip">只能上传 json 格式文件，且不超过 10MB</div>
              </template>
            </el-upload>
          </el-form-item>

          <el-form-item label="导入位置" v-if="currentFolder">
            <el-alert :title="'将导入到当前选中的分组: ' + currentFolder.name" type="success" :closable="false"/>
          </el-form-item>
          <el-form-item label="导入位置" v-else>
            <el-alert title="将自动创建对应名称的根分组" type="warning" :closable="false"/>
          </el-form-item>

        </el-form>
      </div>

      <!-- 解析结果预览区 (Conflict Detection) -->
      <div v-if="parsedData && parsedData.length > 0" class="import-preview">
        <h4>解析预览 (共解析到 {{ parsedData.length }} 个接口)</h4>
        <el-table :data="parsedData" max-height="300" size="small" border>
          <el-table-column prop="method" label="Method" width="80">
            <template #default="{ row }">
              <el-tag :type="getMethodTagType(row.method)" size="small">{{ row.method }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="name" label="接口名称" show-overflow-tooltip />
          <el-table-column prop="url" label="URL" show-overflow-tooltip />
          <el-table-column prop="conflict" label="状态" width="100" align="center">
            <template #default="{ row }">
              <el-tag :type="row.conflict ? 'warning' : 'success'" size="small">
                {{ row.conflict ? '覆盖' : '新增' }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="handleImportClose">取消</el-button>
          <el-button v-if="!parsedData" type="primary" @click="handleParseFile">解析并预览</el-button>
          <el-button v-else type="success" @click="handleConfirmImport">确认导入</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 环境管理抽屉 -->
    <EnvironmentManager v-model:visible="envManagerVisible" @close="handleEnvManagerClose" />
  </div>
</template>

<script setup>
import { ref, onMounted, computed, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { Plus, VideoPlay, Document, Clock, Refresh, Download, Setting, Rank, Upload, ArrowDown, UploadFilled } from '@element-plus/icons-vue'
import EnvironmentManager from '@/components/EnvironmentManager.vue'
import request from '@/utils/request'
import { ElMessage, ElMessageBox } from 'element-plus'

const router = useRouter()

// 数据
const cases = ref([])
const folders = ref([])
const loading = ref(false)
const foldersLoading = ref(false)
const testPlans = ref([])
const environments = ref([])

// 报告历史相关
const reports = ref([])
const reportsLoading = ref(false)
const reportPage = ref(1)
const reportPageSize = ref(10)
const reportTotal = ref(0)

const envManagerVisible = ref(false)
const selectedEnvId = ref(null)

// 分页
const currentPage = ref(1)
const pageSize = ref(20)
const totalCases = computed(() => filteredCases.value.length)

// 搜索和过滤
const searchKeyword = ref('')
const filterMethod = ref('')
const planSearchKeyword = ref('')
const planFilterMethod = ref('')

// 选中的用例
const selectedCaseIds = ref([])
const orderedSelectedCases = ref([])
const selectAll = ref(false)

// 对话框状态
const createFolderDialogVisible = ref(false)
const runDialogVisible = ref(false)
const createPlanDialogVisible = ref(false)
const planDialogVisible = ref(false)
const autoTestDialogVisible = ref(false)
const caseDetailDialogVisible = ref(false)
const resultDetailDialogVisible = ref(false)
const reportDialogVisible = ref(false)

// 导入状态
const importDialogVisible = ref(false)
const importType = ref('') // 'postman' or 'swagger'
const swaggerImportSource = ref('url') // 'url' or 'file'
const swaggerUrl = ref('')
const importFile = ref(null)
const importing = ref(false)
const parsedData = ref(null) // 解析后的预览数据

// 当前选中的文件夹
const currentFolder = ref(null)

// 当前选中的计划
const selectedPlanId = ref(null)
const selectedPlanCases = ref([])

// 新建文件夹
const newFolder = ref({
  name: '',
  description: ''
})

// 新建计划
const newPlan = ref({
  name: '',
  description: '',
  environment_id: null
})

// 测试结果
const executing = ref(false)
const autoTestResult = ref({
  total: 0,
  success: 0,
  failed: 0,
  totalTime: 0,
  results: []
})

// 用例详情
const currentCase = ref(null)
const caseExecutionHistory = ref([])

// 结果详情
const currentResult = ref(null)

// 表格ref
const planCaseTable = ref(null)

// 树形数据
const folderTreeData = computed(() => {
  const buildTree = (list, parentId = null) => {
    return list
      .filter(item => item.parent_id === parentId)
      .map(item => ({
        id: item.id,
        label: item.name,
        caseCount: item.case_count || 0,
        children: buildTree(list, item.id)
      }))
  }
  return buildTree(folders.value)
})

const treeProps = {
  children: 'children',
  label: 'label'
}

// ========== 计算属性 ==========

// 过滤后的用例列表（按文件夹过滤）
const filteredCases = computed(() => {
  let result = cases.value

  // 按文件夹过滤
  if (currentFolder.value) {
    result = result.filter(c => c.folder_id === currentFolder.value.id)
  }

  // 搜索过滤
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    result = result.filter(c =>
      c.name.toLowerCase().includes(keyword) ||
      (c.url && c.url.toLowerCase().includes(keyword)) ||
      (c.description && c.description.toLowerCase().includes(keyword))
    )
  }

  // 方法过滤
  if (filterMethod.value) {
    result = result.filter(c => c.method === filterMethod.value)
  }

  return result
})

// 分页后的用例列表
const paginatedCases = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filteredCases.value.slice(start, end)
})

// 计划中选择用例的过滤
const filteredPlanCases = computed(() => {
  let result = cases.value

  if (planSearchKeyword.value) {
    const keyword = planSearchKeyword.value.toLowerCase()
    result = result.filter(c =>
      c.name.toLowerCase().includes(keyword) ||
      (c.url && c.url.toLowerCase().includes(keyword))
    )
  }

  if (planFilterMethod.value) {
    result = result.filter(c => c.method === planFilterMethod.value)
  }

  return result
})

// ========== 方法 ==========

// 环境列表变化
const handleEnvListChange = () => {
  fetchEnvironments()
}

// 打开环境管理抽屉
const openEnvManager = () => {
  envManagerVisible.value = true
}

const handleEnvManagerClose = () => {
  envManagerVisible.value = false
  fetchEnvironments()
}

// 方法类型映射
const getMethodTagType = (method) => {
  const map = {
    GET: 'success',
    POST: 'primary',
    PUT: 'warning',
    DELETE: 'danger',
    PATCH: 'info'
  }
  return map[method] || 'info'
}

// 格式化日期
const formatDate = (dateStr) => {
  if (!dateStr) return ''
  return (dateStr || '').split('T')[0]
}

// 格式化 JSON
const formatJson = (str) => {
  if (!str) return '无'
  if (typeof str === 'object') return JSON.stringify(str, null, 2)
  try {
    return JSON.stringify(JSON.parse(str), null, 2)
  } catch {
    return str
  }
}

// 格式化响应内容
const formatResponse = (str) => {
  if (!str) return '无'
  if (typeof str === 'string') {
    try {
      return JSON.stringify(JSON.parse(str), null, 2)
    } catch {
      return str
    }
  }
  return JSON.stringify(str, null, 2)
}

// 搜索处理
const handleSearch = () => {
  currentPage.value = 1
}

// 清除筛选
const clearFilters = () => {
  searchKeyword.value = ''
  filterMethod.value = ''
  currentFolder.value = null
  handleSearch()
}

// ========== 文件夹操作 ==========

// 点击文件夹
const handleFolderClick = (node) => {
  currentFolder.value = {
    id: node.id,
    name: node.label
  }
  currentPage.value = 1
}

// 创建文件夹
const createFolder = () => {
  newFolder.value = {
    name: '',
    description: ''
  }
  createFolderDialogVisible.value = true
}

// 保存文件夹
const saveFolder = async () => {
  if (!newFolder.value.name.trim()) {
    ElMessage.warning('请输入分组名称')
    return
  }

  try {
    await request.post('/interface-test/folders', newFolder.value)
    ElMessage.success('创建成功')
    createFolderDialogVisible.value = false
    fetchFolders()
  } catch (e) {
    console.error('创建失败:', e)
    ElMessage.error('创建失败')
  }
}

// 获取文件夹列表
const fetchFolders = async () => {
  foldersLoading.value = true
  try {
    const res = await request.get('/interface-test/folders')
    folders.value = res.data || res
  } catch (err) {
    console.error('获取文件夹失败:', err)
  } finally {
    foldersLoading.value = false
  }
}

// ========== 数据获取 ==========

// 获取用例列表
const fetchCases = async () => {
  loading.value = true
  try {
    const res = await request.get('/interface-test/cases')
    cases.value = res.data || res
  } catch (err) {
    console.error('获取用例失败:', err)
    ElMessage.error('获取用例失败')
  } finally {
    loading.value = false
  }
}

// 获取测试计划列表
const fetchPlans = async () => {
  try {
    const res = await request.get('/interface-test/plans')
    testPlans.value = res.data || res
  } catch (e) {
    console.error('获取计划列表失败:', e)
    ElMessage.error('获取计划列表失败')
  }
}

// 获取环境列表
const fetchEnvironments = async () => {
  try {
    const res = await request.get('/interface-test/environments')
    environments.value = res.data || res
  } catch (e) {
    console.error('获取环境列表失败:', e)
  }
}

// 获取用例执行历史
const fetchCaseExecutionHistory = async (caseId) => {
  try {
    const res = await request.get(`/interface-test/cases/${caseId}/history`)
    caseExecutionHistory.value = res.data || res || []
  } catch (e) {
    caseExecutionHistory.value = []
  }
}

// 获取报告列表 (带分页)
const fetchReports = async () => {
  reportsLoading.value = true
  try {
    const res = await request.get('/interface-test/reports', {
      params: {
        page: reportPage.value,
        page_size: reportPageSize.value
      }
    })

    // 兼容可能的新分页返回结构，如果后端还没改，就当作直接返回数组处理
    if (res.items !== undefined) {
      reports.value = res.items
      reportTotal.value = res.total
    } else {
      // 旧的直接返回全部数组
      const allData = res.data || res
      reportTotal.value = allData.length
      const start = (reportPage.value - 1) * reportPageSize.value
      reports.value = allData.slice(start, start + reportPageSize.value)
    }
  } catch (e) {
    console.error('获取报告列表失败:', e)
    ElMessage.error('获取报告列表失败')
  } finally {
    reportsLoading.value = false
  }
}

const handleReportPageChange = () => {
  fetchReports()
}

const handleReportPageSizeChange = () => {
  reportPage.value = 1
  fetchReports()
}

// ========== 用例操作 ==========

// 新建用例
const createNew = () => {
  // 如果当前选中了文件夹，新建时自动带上 folder_id
  const query = currentFolder.value
    ? { folder_id: currentFolder.value.id }
    : {}
  router.push({
    path: '/interface-test/new',
    query
  })
}

// 打开用例
const openCase = (id) => {
  router.push(`/interface-test/${id}`)
}

// 查看用例详情
const viewCaseDetail = async (caseItem) => {
  currentCase.value = caseItem
  caseExecutionHistory.value = []
  caseDetailDialogVisible.value = true
  await fetchCaseExecutionHistory(caseItem.id)
}

// 删除用例
const deleteCase = async (id) => {
  try {
    await ElMessageBox.confirm('确定删除这个用例吗？', '确认删除', { type: 'warning' })
    await request.delete(`/interface-test/cases/${id}`)
    ElMessage.success('删除成功')
    fetchCases()
  } catch (error) {
    if (error !== 'cancel') {
      const msg = error.response?.data?.error || error.response?.data?.message || '删除失败，可能该接口已被场景引用'
      ElMessage.error(msg)
    }
    // 用户取消不处理
  }
}

// 单个用例执行
const runSingleCase = async (caseItem) => {
  // 检查是否选择了环境
  if (!selectedEnvId.value) {
    ElMessage.warning('请先在顶部下拉框选择执行环境！')
    return
  }

  if (caseItem === currentCase.value) {
    caseDetailDialogVisible.value = false
  }

  autoTestResult.value = {
    total: 1,
    success: 0,
    failed: 0,
    totalTime: 0,
    results: []
  }
  autoTestDialogVisible.value = true
  executing.value = true

  const result = {
    id: caseItem.id,
    name: caseItem.name,
    method: caseItem.method,
    url: caseItem.url,
    status: 0,
    success: false,
    time: 0,
    error: '',
    requestHeaders: {},
    requestBody: caseItem.body || '',
    response: null,
    responseHeaders: null
  }

  const startTime = Date.now()

  try {
    const envVariables = await getEnvVariables()
    let url = replaceVariables(caseItem.url, envVariables)
    let headers = {}
    if (caseItem.headers) {
      try {
        headers = JSON.parse(caseItem.headers)
        Object.keys(headers).forEach(key => {
          headers[key] = replaceVariables(headers[key], envVariables)
        })
      } catch(e) {}
    }
    result.requestHeaders = headers

    const res = await request.post('/interface-test/send', {
      method: caseItem.method,
      url: url,
      headers: headers,
      body: caseItem.body || '',
      body_type: caseItem.body_type || 'json',
      env_id: selectedEnvId.value
    })

    result.status = res.status_code
    result.time = res.elapsed_ms
    result.success = res.status_code >= 200 && res.status_code < 300
    result.response = res.response_content
    result.responseHeaders = res.response_headers || null
    if (result.success) autoTestResult.value.success++
    else autoTestResult.value.failed++
  } catch (e) {
    result.success = false
    result.error = e.message || '请求失败'
    autoTestResult.value.failed++
  }

  result.time = Date.now() - startTime
  autoTestResult.value.results.push(result)
  autoTestResult.value.totalTime = Date.now() - startTime
  executing.value = false
}

// 查看结果详情
const viewResultDetail = (resultItem) => {
  currentResult.value = resultItem
  resultDetailDialogVisible.value = true
}

// ========== 导入用例操作 ==========
const handleImportCommand = (command) => {
  importType.value = command
  importFile.value = null
  parsedData.value = null
  swaggerUrl.value = ''
  importDialogVisible.value = true
}

const handleFileChange = (file) => {
  importFile.value = file.raw
}

const handleFileRemove = () => {
  importFile.value = null
  parsedData.value = null
}

const handleImportClose = () => {
  importDialogVisible.value = false
  importFile.value = null
  parsedData.value = null
  swaggerUrl.value = ''
  importing.value = false
}

// 解析文件
const handleParseFile = async () => {
  importing.value = true
  parsedData.value = null

  try {
    const formData = new FormData()
    if (currentFolder.value) {
      formData.append('target_group_id', currentFolder.value.id)
    }

    if (importType.value === 'swagger' && swaggerImportSource.value === 'url') {
      if (!swaggerUrl.value) {
        ElMessage.warning('请输入 Swagger URL')
        importing.value = false
        return
      }
      formData.append('url', swaggerUrl.value)
    } else {
      if (!importFile.value) {
        ElMessage.warning('请选择文件')
        importing.value = false
        return
      }
      formData.append('file', importFile.value)
    }

    const endpoint = importType.value === 'postman' ? '/api/auto-test/import/postman' : '/api/auto-test/import/swagger'

    formData.append('dry_run', 'true')

    const res = await request.post(endpoint, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })

    if (res && res.cases) {
      parsedData.value = res.cases.map(c => ({
        ...c,
        conflict: cases.value.some(existing => existing.url === c.url && existing.method === c.method)
      }))
      ElMessage.success(`成功解析 ${res.cases.length} 个接口`)
    } else {
      ElMessage.error('解析失败，返回数据格式不正确')
    }

  } catch (error) {
    console.error('解析失败', error)
    ElMessage.error('解析失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    importing.value = false
  }
}

// 确认导入
const handleConfirmImport = async () => {
  importing.value = true
  try {
    const formData = new FormData()
    if (currentFolder.value) {
      formData.append('target_group_id', currentFolder.value.id)
    }

    if (importType.value === 'swagger' && swaggerImportSource.value === 'url') {
      formData.append('url', swaggerUrl.value)
    } else {
      formData.append('file', importFile.value)
    }

    const endpoint = importType.value === 'postman' ? '/api/auto-test/import/postman' : '/api/auto-test/import/swagger'

    formData.append('dry_run', 'false')

    const res = await request.post(endpoint, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })

    ElMessage.success(`导入成功，共导入 ${res?.imported_count || res?.cases?.length || 0} 个接口`)
    handleImportClose()

    // 刷新用例列表和左侧树
    fetchCases()
    fetchFolders()

  } catch (error) {
    console.error('导入失败', error)
    ElMessage.error('导入失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    importing.value = false
  }
}


// ========== 执行测试 ==========

// 获取环境变量
const getEnvVariables = async () => {
  let envVariables = {}
  try {
    // 如果用户选中了环境，使用选中的；否则找默认环境
    let selectedEnv = null
    if (selectedEnvId.value) {
      selectedEnv = environments.value.find(e => e.id === selectedEnvId.value)
    } else {
      selectedEnv = environments.value.find(env => env.is_default) || environments.value[0]
    }
    if (selectedEnv && selectedEnv.variables) {
      if (typeof selectedEnv.variables === 'string') {
        envVariables = JSON.parse(selectedEnv.variables)
      } else {
        envVariables = selectedEnv.variables || {}
      }
      if (selectedEnv.base_url && !('base_url' in envVariables)) {
        envVariables['base_url'] = selectedEnv.base_url
      }
    }
  } catch (e) {
    console.warn('获取环境变量失败，使用空变量')
  }
  return envVariables
}

// 变量替换
const replaceVariables = (str, variables) => {
  if (!str || !variables) return str
  return str.replace(/\{\{(\w+)\}\}/g, (match, key) => {
    return variables[key] || match
  })
}

// 打开执行测试对话框
const openRunTestDialog = async () => {
  await fetchPlans()
  selectedPlanId.value = null
  selectedPlanCases.value = []
  if (testPlans.value.length > 0) {
    selectedPlanId.value = testPlans.value[0].id
    await onPlanChange()
  }
  runDialogVisible.value = true
}

// 计划变更
const onPlanChange = async () => {
  if (!selectedPlanId.value) {
    selectedPlanCases.value = []
    return
  }
  try {
    const res = await request.get(`/interface-test/plans/${selectedPlanId.value}`)
    const data = res.data || res
    selectedPlanCases.value = data.cases || []
  } catch (e) {
    console.error('获取计划详情失败:', e)
    ElMessage.error('获取计划详情失败')
  }
}

// 执行指定计划
const executePlanById = async (planId) => {
  selectedPlanId.value = planId
  await onPlanChange()
  planDialogVisible.value = false
  runDialogVisible.value = true
}

// 执行选中的计划（调用后端API保存报告）
const executePlan = async () => {
  if (!selectedPlanId.value || selectedPlanCases.value.length === 0) {
    ElMessage.warning('请先选择要执行的计划')
    return
  }
  // 检查是否选择了环境
  if (!selectedEnvId.value) {
    ElMessage.warning('请先在顶部下拉框选择执行环境！')
    return
  }

  runDialogVisible.value = false
  autoTestDialogVisible.value = true
  executing.value = true

  try {
    const res = await request.post(`/interface-test/plans/${selectedPlanId.value}/execute`, {
      env_id: selectedEnvId.value
    })

    autoTestResult.value = {
      total: res.total,
      success: res.success,
      failed: res.failed,
      totalTime: res.totalTime,
      results: res.results
    }

    ElMessage.success('执行完成！')

    // 强制回到第一页
    reportPage.value = 1
    await fetchReports() // 刷新历史记录
  } catch (e) {
    console.error('执行失败:', e)
    ElMessage.error('执行失败: ' + (e.message || '未知错误'))
    autoTestResult.value = {
      total: 0,
      success: 0,
      failed: 0,
      totalTime: 0,
      results: []
    }
  } finally {
    executing.value = false
  }
}

// 打开报告管理
const openReportManager = async () => {
  reportPage.value = 1
  await fetchReports()
  reportDialogVisible.value = true
}

// 查看报告详情
const viewReport = async (report) => {
  try {
    const res = await request.get(`/interface-test/reports/${report.id}`)
    autoTestResult.value = {
      total: res.total,
      success: res.success,
      failed: res.failed,
      totalTime: res.total_time,
      results: res.results.map(r => ({
        ...r,
        name: r.case_name,
        url: r.url,
        requestHeaders: r.request_headers || {},
        requestBody: r.request_body || '',
        response: r.response,
        responseHeaders: r.response_headers
      }))
    }
    reportDialogVisible.value = false
    autoTestDialogVisible.value = true
  } catch (e) {
    console.error('获取报告详情失败:', e)
    ElMessage.error('获取报告详情失败')
  }
}

// 再次运行计划
const reRunPlan = async (report) => {
  if (executing.value) {
    ElMessage.warning('已有任务正在执行中，请稍候...')
    return
  }

  // 检查是否选择了环境
  if (!selectedEnvId.value) {
    ElMessage.warning('请先在顶部下拉框选择执行环境！')
    return
  }

  // 必须要有对应的 plan_id
  if (!report.plan_id) {
    ElMessage.error('该报告缺少执行计划信息，无法直接重新运行')
    return
  }

  reportDialogVisible.value = false
  autoTestDialogVisible.value = true
  executing.value = true

  try {
    const res = await request.post(`/interface-test/plans/${report.plan_id}/execute`, {
      env_id: selectedEnvId.value
    })

    autoTestResult.value = {
      total: res.total,
      success: res.success,
      failed: res.failed,
      totalTime: res.totalTime,
      results: res.results
    }

    ElMessage.success('执行完成！')

    reportPage.value = 1
    await fetchReports() // 刷新历史记录
  } catch (e) {
    console.error('执行失败:', e)
    ElMessage.error('执行失败: ' + (e.message || '未知错误'))
    autoTestResult.value = {
      total: 0,
      success: 0,
      failed: 0,
      totalTime: 0,
      results: []
    }
  } finally {
    executing.value = false
  }
}

// 删除报告
const deleteReport = async (report) => {
  try {
    await ElMessageBox.confirm(`确定要删除这份执行记录吗？`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await request.delete(`/interface-test/reports/${report.id}`)
    ElMessage.success('删除成功')
    fetchReports()
  } catch (e) {
    if (e !== 'cancel') {
      console.error('删除失败:', e)
      ElMessage.error('删除失败')
    }
  }
}

// 导出测试报告
const exportReport = () => {
  const report = generateReport()
  const blob = new Blob([report], { type: 'text/html' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `测试报告_${new Date().toISOString().slice(0, 10)}.html`
  link.click()
  URL.revokeObjectURL(url)
  ElMessage.success('报告已导出')
}

// 生成 HTML 报告
const generateReport = () => {
  const result = autoTestResult.value
  const date = new Date().toLocaleString('zh-CN')

  const rows = result.results.map((r, i) => `
    <tr class="${r.success ? 'success' : 'failed'}">
      <td>${i + 1}</td>
      <td>${r.name}</td>
      <td><span class="method ${r.method.toLowerCase()}">${r.method}</span></td>
      <td class="url">${r.url}</td>
      <td><span class="status ${r.status >= 200 && r.status < 300 ? 'success' : 'failed'}">${r.status || 'Error'}</span></td>
      <td>${r.time}ms</td>
      <td>${r.error || '-'}</td>
    </tr>
  `).join('')

  return `<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <title>接口测试报告 - ${date}</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; padding: 40px; background: #f5f7fa; }
    .container { max-width: 1200px; margin: 0 auto; background: white; border-radius: 8px; padding: 30px; box-shadow: 0 2px 12px rgba(0,0,0,0.1); }
    h1 { color: #303133; margin-bottom: 10px; }
    .meta { color: #909399; margin-bottom: 30px; }
    .summary { display: flex; gap: 20px; margin-bottom: 30px; }
    .stat { padding: 20px 30px; border-radius: 8px; background: #f5f7fa; }
    .stat.success { background: #f0f9eb; border: 1px solid #67c23a; }
    .stat.failed { background: #fef0f0; border: 1px solid #f56c6c; }
    .stat-label { color: #909399; font-size: 14px; }
    .stat-value { font-size: 28px; font-weight: bold; margin-top: 5px; }
    .success .stat-value { color: #67c23a; }
    .failed .stat-value { color: #f56c6c; }
    table { width: 100%; border-collapse: collapse; }
    th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ebeef5; }
    th { background: #f5f7fa; color: #606266; font-weight: 500; }
    tr:hover { background: #fafafa; }
    .method { padding: 2px 8px; border-radius: 4px; font-size: 12px; font-weight: 500; }
    .method.get { background: #e1f3d8; color: #67c23a; }
    .method.post { background: #d9ecff; color: #409eff; }
    .method.put { background: #fdf6ec; color: #e6a23c; }
    .method.delete { background: #fde2e2; color: #f56c6c; }
    .method.patch { background: #ecf5ff; color: #909399; }
    .status { padding: 2px 8px; border-radius: 4px; font-size: 12px; }
    .status.success { background: #e1f3d8; color: #67c23a; }
    .status.failed { background: #fde2e2; color: #f56c6c; }
    .url { max-width: 300px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  </style>
</head>
<body>
  <div class="container">
    <h1>接口测试报告</h1>
    <p class="meta">生成时间: ${date}</p>
    <div class="summary">
      <div class="stat">
        <div class="stat-label">总用例数</div>
        <div class="stat-value">${result.total}</div>
      </div>
      <div class="stat success">
        <div class="stat-label">成功</div>
        <div class="stat-value">${result.success}</div>
      </div>
      <div class="stat failed">
        <div class="stat-label">失败</div>
        <div class="stat-value">${result.failed}</div>
      </div>
      <div class="stat">
        <div class="stat-label">总耗时</div>
        <div class="stat-value">${result.totalTime}ms</div>
      </div>
    </div>
    <table>
      <thead>
        <tr>
          <th>#</th>
          <th>用例名称</th>
          <th>方法</th>
          <th>URL</th>
          <th>状态码</th>
          <th>耗时</th>
          <th>错误信息</th>
        </tr>
      </thead>
      <tbody>
        ${rows}
      </tbody>
    </table>
  </div>
</body>
</html>`
}

// ========== 测试计划管理 ==========

// 打开计划管理器
const openPlanManager = async () => {
  await fetchPlans()
  planDialogVisible.value = true
}

// 打开创建计划对话框
const openCreatePlanDialog = () => {
  runDialogVisible.value = false
  fetchEnvironments()
  newPlan.value = {
    name: '',
    description: '',
    environment_id: null
  }
  selectedCaseIds.value = []
  orderedSelectedCases.value = []
  selectAll.value = false
  planSearchKeyword.value = ''
  planFilterMethod.value = ''
  createPlanDialogVisible.value = true
}

// 表格选择变化
const handlePlanSelectionChange = (selection) => {
  selectedCaseIds.value = selection.map(item => item.id)
  orderedSelectedCases.value = selection
  // 同步全选状态
  if (filteredPlanCases.value.length > 0) {
    selectAll.value = selection.length === filteredPlanCases.value.length
  } else {
    selectAll.value = false
  }
}

// 全选
const handleSelectAll = (checked) => {
  if (planCaseTable.value) {
    planCaseTable.value.toggleAllSelection()
  }
  if (checked) {
    selectedCaseIds.value = filteredPlanCases.value.map(item => item.id)
    orderedSelectedCases.value = [...filteredPlanCases.value]
  } else {
    selectedCaseIds.value = []
    orderedSelectedCases.value = []
  }
}

// 拖拽结束
const onRowDragEnd = ({ newList }) => {
  orderedSelectedCases.value = newList
}

// 从有序列表中移除
const removeFromOrdered = (index) => {
  const removed = orderedSelectedCases.value.splice(index, 1)[0]
  selectedCaseIds.value = selectedCaseIds.value.filter(id => id !== removed.id)
}

// 保存计划
const savePlan = async () => {
  if (!newPlan.value.name.trim()) {
    ElMessage.warning('请输入计划名称')
    return
  }
  if (orderedSelectedCases.value.length === 0) {
    ElMessage.warning('请选择至少一个用例')
    return
  }

  const data = {
    name: newPlan.value.name,
    description: newPlan.value.description,
    case_ids: orderedSelectedCases.value.map(item => item.id),
    environment_id: newPlan.value.environment_id
  }

  try {
    await request.post('/interface-test/plans', data)
    ElMessage.success('保存成功')
    createPlanDialogVisible.value = false
    await fetchPlans()
  } catch (e) {
    console.error('保存失败:', e)
    ElMessage.error('保存失败')
  }
}

// 编辑计划
const editPlan = async (plan) => {
  try {
    const res = await request.get(`/interface-test/plans/${plan.id}`)
    const data = res.data || res
    newPlan.value = {
      name: data.name,
      description: data.description || '',
      environment_id: data.environment_id
    }
    selectedCaseIds.value = data.case_ids || []
    orderedSelectedCases.value = data.cases || []
    planSearchKeyword.value = ''
    planFilterMethod.value = ''
    createPlanDialogVisible.value = true
    planDialogVisible.value = false
  } catch (e) {
    console.error('获取计划详情失败:', e)
    ElMessage.error('获取计划详情失败')
  }
}

// 删除计划
const deletePlan = async (plan) => {
  try {
    await ElMessageBox.confirm(`确定要删除测试计划 "${plan.name}" 吗？`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await request.delete(`/interface-test/plans/${plan.id}`)
    ElMessage.success('删除成功')
    fetchPlans()
  } catch (e) {
    if (e !== 'cancel') {
      console.error('删除失败:', e)
      ElMessage.error('删除失败')
    }
  }
}

// 列表选择变化
const handleSelectionChange = (selection) => {
  selectedCaseIds.value = selection.map(item => item.id)
}

onMounted(() => {
  fetchCases()
  fetchFolders()
})
</script>

<style scoped>
.interface-test-list {
  min-height: calc(100vh - 60px);
  background-color: #f5f7fa;
}

.main-container {
  display: flex;
  height: calc(100vh - 0px);
  max-width: 100%;
}

/* 左侧面板 */
.left-panel {
  width: 280px;
  background: white;
  border-right: 1px solid #e4e7ed;
  display: flex;
  flex-direction: column;
}

.folder-header {
  padding: 16px;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.folder-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.folder-tree {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.tree-node-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
}

.folder-name {
  margin-right: 8px;
}

/* 右侧面板 */
.right-panel {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
}

.header-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.title-section {
  display: flex;
  align-items: center;
  gap: 16px;
}

.page-title {
  font-size: 24px;
  margin: 0;
  color: #303133;
}

.case-count {
  color: #909399;
  font-size: 14px;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.filter-bar {
  display: flex;
  gap: 15px;
  margin-bottom: 15px;
  padding: 15px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}

.case-list-container {
  background: white;
  border-radius: 8px;
  padding: 15px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}

.case-table-wrapper {
  min-height: 200px;
}

.pagination-wrapper {
  margin-top: 15px;
  display: flex;
  justify-content: flex-end;
}

.empty-state {
  padding: 40px 0;
}

/* 对话框样式 */
.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.no-plan-guide {
  padding: 40px 0;
  text-align: center;
}

.run-plan-section {
  padding: 10px 0;
}

.plan-select-section {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 15px;
}

.plan-preview {
  margin-top: 15px;
}

.plan-case-list {
  max-height: 300px;
  overflow-y: auto;
}

.create-plan-content {
  padding: 10px 0;
}

.case-selection-section {
  margin-top: 20px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.section-title {
  font-size: 16px;
  font-weight: 500;
  color: #303133;
}

.selection-actions {
  display: flex;
  align-items: center;
  gap: 15px;
}

.selected-count {
  color: #67c23a;
  font-size: 14px;
}

.filter-bar-small {
  display: flex;
  gap: 10px;
  margin-bottom: 10px;
}

.order-section {
  margin-top: 20px;
  padding: 15px;
  background: #f5f7fa;
  border-radius: 8px;
}

.hint {
  color: #909399;
  font-size: 12px;
}

.plan-header {
  margin-bottom: 10px;
}

.report-header {
  margin-bottom: 10px;
}

.auto-test-summary {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
}

.summary-left {
  display: flex;
  align-items: center;
  gap: 20px;
}

.summary-right {
  display: flex;
  gap: 10px;
}

.total-time {
  color: #909399;
  font-size: 14px;
}

/* 用例详情样式 */
.case-detail-content {
  padding: 10px 0;
}

.request-info h4,
.response-info h4,
.error-info h4 {
  margin: 15px 0 10px;
  color: #606266;
  font-size: 14px;
}

.code-block {
  background: #f5f7fa;
  padding: 12px;
  border-radius: 4px;
  font-family: 'Monaco', 'Menlo', monospace;
  font-size: 12px;
  max-height: 300px;
  overflow: auto;
  white-space: pre-wrap;
  word-break: break-all;
  margin: 0;
}

.code-block.error {
  background: #fef0f0;
  color: #f56c6c;
}

.url-break {
  word-break: break-all;
  font-size: 12px;
}

.execution-summary {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 10px;
}

.exec-time {
  color: #909399;
  font-size: 14px;
}

.response-preview,
.error-preview {
  margin-top: 10px;
}

.response-preview h5,
.error-preview h5 {
  color: #606266;
  font-size: 13px;
  margin-bottom: 5px;
}

/* 结果详情样式 */
.result-detail-content {
  padding: 10px 0;
}

.import-preview {
  margin-top: 20px;
  border-top: 1px solid var(--tm-border-light);
  padding-top: 15px;
}

.import-preview h4 {
  margin-top: 0;
  margin-bottom: 12px;
  color: var(--tm-text-primary);
}
</style>
