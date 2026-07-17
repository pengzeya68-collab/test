<template>
  <div class="project-practice">
    <div v-if="loading" class="loading-wrap">
      <div class="spinner">⏳</div>
      <p>加载项目列表...</p>
    </div>

    <div v-else-if="!activeProject">
      <div class="pp-header">
        <h3>🚀 项目实战</h3>
        <p class="pp-subtitle">通过真实项目练习，巩固测试技能</p>
      </div>

      <div class="project-grid" v-if="projects.length > 0">
        <div
          v-for="project in projects"
          :key="project.id"
          class="project-card"
          @click="openProject(project)"
        >
          <div class="pc-header">
            <span class="pc-difficulty" :class="'diff-' + (project.difficulty || 'medium')">
              {{ getDifficultyText(project.difficulty) }}
            </span>
            <span class="pc-hours">⏱️ {{ project.estimated_hours }}h</span>
          </div>
          <h4 class="pc-title">{{ project.title }}</h4>
          <p class="pc-desc">{{ project.description }}</p>
          <div class="pc-meta">
            <span>📋 {{ project.task_count || 0 }}个任务</span>
          </div>
          <div class="pc-progress" v-if="project.progress">
            <div class="pcp-bar">
              <div class="pcp-fill" :style="{ width: project.progress.percent + '%' }"></div>
            </div>
            <span class="pcp-text">{{ project.progress.completed_tasks }}/{{ project.progress.total_tasks }}</span>
          </div>
        </div>
      </div>

      <div class="empty-block" v-else>
        <p>📭 该学习路径暂无项目实战内容</p>
        <p class="empty-hint">管理员可以为此路径添加项目实战任务</p>
      </div>
    </div>

    <div v-else class="project-detail">
      <div class="pd-back">
        <el-button text @click="activeProject = null">← 返回项目列表</el-button>
      </div>

      <div class="pd-hero">
        <div class="pdh-tags">
          <span class="tag" :class="'diff-' + (activeProject.difficulty || 'medium')">{{ getDifficultyText(activeProject.difficulty) }}</span>
          <span class="tag tag-time">⏱️ {{ activeProject.estimated_hours }}小时</span>
        </div>
        <h2>{{ activeProject.title }}</h2>
        <p>{{ activeProject.description }}</p>

        <div class="pdh-progress" v-if="activeProject.progress">
          <div class="progress-header">
            <span>项目进度</span>
            <span>{{ activeProject.progress.percent }}%</span>
          </div>
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: activeProject.progress.percent + '%' }"></div>
          </div>
        </div>

        <div class="pdh-actions">
          <el-button type="primary" @click="startProject">开始项目</el-button>
        </div>
      </div>

      <div class="project-tabs">
        <el-button text class="ctab" :class="{ active: projectTab === 'tasks' }" @click="projectTab = 'tasks'">
          ✅ 任务清单 <span class="ctab-badge">{{ tasks.length }}</span>
        </el-button>
        <el-button text class="ctab" :class="{ active: projectTab === 'resources' }" @click="projectTab = 'resources'">
          📁 项目资料
        </el-button>
        <el-button text class="ctab" :class="{ active: projectTab === 'submissions' }" @click="projectTab = 'submissions'">
          📝 我的提交
        </el-button>
        <el-button text class="ctab" :class="{ active: projectTab === 'evaluation' }" @click="projectTab = 'evaluation'">
          🏆 验收评价
        </el-button>
      </div>

      <div class="project-tab-content">
        <div v-show="projectTab === 'tasks'" class="task-list">
          <div
            v-for="task in tasks"
            :key="task.id"
            class="task-card"
            :class="{ submitted: task.submission }"
          >
            <div class="tc-header">
              <div class="tch-left">
                <span class="tc-number">{{ task.sort_order + 1 }}</span>
                <div>
                  <h4>{{ task.title }}</h4>
                  <span class="tc-type">{{ task.task_type_label }}</span>
                </div>
              </div>
              <div class="tch-right">
                <span class="tc-score">{{ task.score }}分</span>
                <el-tag v-if="task.submission" size="small" type="success">已提交</el-tag>
              </div>
            </div>
            <div class="tc-body">
              <div class="tc-desc">{{ task.description }}</div>
              <div class="tc-requirements" v-if="task.requirements">
                <h5>任务要求</h5>
                <pre>{{ task.requirements }}</pre>
              </div>
              <div class="tc-hints" v-if="task.hints">
                <h5>💡 提示</h5>
                <pre>{{ task.hints }}</pre>
              </div>
            </div>
            <div class="tc-footer">
              <el-button size="small" @click="openSubmitDialog(task)">提交任务</el-button>
              <el-tag v-if="task.submission" size="small" :type="task.submission.status === 'accepted' ? 'success' : 'warning'" style="margin-left:8px">
                {{ task.submission.status === 'accepted' ? '已通过' : task.submission.status === 'rejected' ? '需修改' : '审核中' }}
              </el-tag>
              <span v-if="task.submission?.score !== undefined" class="tc-score-result">
                得分: {{ task.submission.score }}分
              </span>
            </div>
          </div>
        </div>

        <div v-show="projectTab === 'resources'" class="resource-list">
          <div v-for="res in resources" :key="res.id" class="resource-card">
            <div class="rc-icon">
              <span v-if="res.resource_type === 'document'">📄</span>
              <span v-else-if="res.resource_type === 'api_doc'">🔗</span>
              <span v-else-if="res.resource_type === 'test_data'">📊</span>
              <span v-else-if="res.resource_type === 'reference'">📚</span>
              <span v-else>🔗</span>
            </div>
            <div class="rc-body">
              <h4>{{ res.title }}</h4>
              <span class="rc-type">{{ res.resource_type_label }}</span>
              <div class="rc-content" v-if="res.content">{{ res.content.substring(0, 300) }}{{ res.content.length > 300 ? '...' : '' }}</div>
              <el-link v-if="res.url" :href="res.url" target="_blank" class="rc-link">打开链接 →</el-link>
            </div>
          </div>
          <div class="empty-block" v-if="resources.length === 0">
            <p>📭 暂无项目资料</p>
          </div>
        </div>

        <div v-show="projectTab === 'submissions'" class="submission-list">
          <div v-if="mySubmissions.length > 0" class="submission-items">
            <div v-for="sub in mySubmissions" :key="sub.id" class="submission-card">
              <div class="sc-header">
                <span class="sc-task">任务: {{ sub.task_title || '任务#' + sub.task_id }}</span>
                <el-tag size="small" :type="sub.status === 'accepted' ? 'success' : 'warning'">
                  {{ sub.status === 'accepted' ? '已通过' : sub.status === 'rejected' ? '需修改' : '审核中' }}
                </el-tag>
              </div>
              <div class="sc-content">{{ sub.content }}</div>
              <div class="sc-meta">
                <span>{{ formatTime(sub.submitted_at) }}</span>
                <span v-if="sub.score !== undefined">得分: {{ sub.score }}</span>
              </div>
            </div>
          </div>
          <div class="empty-block" v-else>
            <p>📝 暂无提交记录</p>
          </div>
        </div>

        <div v-show="projectTab === 'evaluation'" class="evaluation-area">
          <div v-if="evaluation" class="eval-card">
            <div class="ev-status" :class="{ passed: evaluation.is_passed }">
              {{ evaluation.is_passed ? '✅ 项目通过验收' : '⏳ 待验收' }}
            </div>
            <div class="ev-score" v-if="evaluation.is_passed">总分: {{ evaluation.total_score }}分</div>
            <div class="ev-comment" v-if="evaluation.comment">
              <h5>总评语</h5>
              <p>{{ evaluation.comment }}</p>
            </div>
            <div class="ev-feedback" v-if="evaluation.strengths">
              <h5>亮点</h5>
              <p>{{ evaluation.strengths }}</p>
            </div>
            <div class="ev-feedback" v-if="evaluation.improvements">
              <h5>改进建议</h5>
              <p>{{ evaluation.improvements }}</p>
            </div>
          </div>
          <div class="empty-block" v-else>
            <p>🏆 尚未验收，完成所有任务后将自动生成评价</p>
          </div>
        </div>
      </div>
    </div>

    <el-dialog v-model="submitDialogVisible" title="提交任务" width="550px" custom-class="dark-dialog" destroy-on-close>
      <div class="submit-dialog">
        <div class="sd-task-info">
          <strong>{{ submitTask?.title }}</strong>
          <span class="sd-type">{{ submitTask?.task_type_label }}</span>
        </div>
        <el-input
          v-model="submitContent"
          type="textarea"
          :rows="8"
          placeholder="请输入你的任务成果..."
          class="dark-input"
        />
      </div>
      <template #footer>
        <el-button @click="submitDialogVisible = false" class="btn-cancel">取消</el-button>
        <el-button type="primary" @click="doSubmit" class="btn-primary" :disabled="!submitContent.trim()">提交</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import request from '@/utils/request'

const props = defineProps({
  pathId: { type: [Number, String], required: true }
})

const loading = ref(false)
const projects = ref([])
const activeProject = ref(null)
const tasks = ref([])
const resources = ref([])
const mySubmissions = ref([])
const evaluation = ref(null)
const projectTab = ref('tasks')

const submitDialogVisible = ref(false)
const submitTask = ref(null)
const submitContent = ref('')

const DIFFICULTY_MAP = { easy: '入门', medium: '进阶', hard: '挑战' }

const getDifficultyText = (d) => DIFFICULTY_MAP[d] || d || '进阶'

const formatTime = (t) => {
  if (!t) return ''
  return new Date(t).toLocaleString('zh-CN')
}

const fetchProjects = async () => {
  loading.value = true
  try {
    const res = await request.get(`/learning-paths/${props.pathId}/projects`)
    projects.value = res?.projects || []
  } catch (e) {
    console.error('获取项目列表失败', e)
  } finally {
    loading.value = false
  }
}

const openProject = async (project) => {
  try {
    const res = await request.get(`/projects/${project.id}`)
    activeProject.value = res
    tasks.value = []
    resources.value = []
    evaluation.value = null
    mySubmissions.value = []
    await Promise.all([fetchTasks(project.id), fetchResources(project.id), fetchEvaluation(project.id)])
  } catch (e) {
    ElMessage.error('获取项目详情失败')
  }
}

const fetchTasks = async (projectId) => {
  try {
    const res = await request.get(`/projects/${projectId}/tasks`)
    tasks.value = res?.tasks || []
    const subs = tasks.value.filter(t => t.submission).map(t => ({
      ...t.submission,
      task_id: t.id,
      task_title: t.title,
    }))
    mySubmissions.value = subs
  } catch (e) {
    console.error('获取任务列表失败', e)
  }
}

const fetchResources = async (projectId) => {
  try {
    const res = await request.get(`/projects/${projectId}/resources`)
    resources.value = res?.resources || []
  } catch (e) {
    console.error('获取项目资料失败', e)
  }
}

const fetchEvaluation = async (projectId) => {
  try {
    const res = await request.get(`/projects/${projectId}/evaluation`)
    evaluation.value = res?.evaluation || null
  } catch (e) {
    console.error('获取评价失败', e)
  }
}

const startProject = async () => {
  try {
    const res = await request.post(`/projects/${activeProject.value.id}/start`)
    if (activeProject.value && res?.progress) {
      activeProject.value.progress = res.progress
    }
    ElMessage.success(res?.message || '项目已开始，加油！')
  } catch (e) {
    ElMessage.error('启动失败')
  }
}

const openSubmitDialog = (task) => {
  submitTask.value = task
  submitContent.value = task.submission?.content || ''
  submitDialogVisible.value = true
}

const doSubmit = async () => {
  try {
    const res = await request.post(`/projects/${activeProject.value.id}/tasks/${submitTask.value.id}/submit`, {
      content: submitContent.value
    })
    ElMessage.success('任务提交成功')
    submitDialogVisible.value = false
    await fetchTasks(activeProject.value.id)
    if (activeProject.value) {
      activeProject.value.progress = {
        total_tasks: tasks.value.length,
        completed_tasks: tasks.value.filter(t => t.submission).length,
        percent: tasks.value.length > 0 ? Math.round(tasks.value.filter(t => t.submission).length / tasks.value.length * 100) : 0
      }
    }
    if (res?.all_submitted) {
      await fetchEvaluation(activeProject.value.id)
      ElMessage.success('🎉 恭喜！所有任务已完成，评价已生成')
    }
  } catch (e) {
    ElMessage.error('提交失败')
  }
}

onMounted(() => {
  fetchProjects()
})
</script>

<style scoped>
.project-practice {
  padding: 4px 0;
}

.pp-header {
  margin-bottom: 20px;
}

.pp-header h3 {
  margin: 0 0 4px;
  font-size: 18px;
  color: #e0e0e0;
}

.pp-subtitle {
  margin: 0;
  color: #888;
  font-size: 13px;
}

.project-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
}

.project-card {
  background: rgba(255, 255, 255, .03);
  border: 1px solid rgba(255, 255, 255, .08);
  border-radius: 10px;
  padding: 20px;
  cursor: pointer;
  transition: all .2s;
}

.project-card:hover {
  border-color: rgba(64, 158, 255, .3);
  background: rgba(64, 158, 255, .04);
  transform: translateY(-2px);
}

.pc-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.pc-difficulty {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 4px;
  background: rgba(255,255,255,.06);
  color: #aaa;
}

.pc-difficulty.diff-medium { color: #e6a23c; }
.pc-difficulty.diff-easy { color: #67c23a; }
.pc-difficulty.diff-hard { color: #f56c6c; }

.pc-hours {
  font-size: 12px;
  color: #777;
}

.pc-title {
  margin: 0 0 6px;
  font-size: 16px;
  color: #e0e0e0;
}

.pc-desc {
  margin: 0 0 12px;
  font-size: 13px;
  color: #999;
  line-height: 1.5;
}

.pc-meta {
  font-size: 12px;
  color: #777;
  margin-bottom: 8px;
}

.pc-progress {
  display: flex;
  align-items: center;
  gap: 8px;
}

.pcp-bar {
  flex: 1;
  height: 6px;
  background: rgba(255,255,255,.06);
  border-radius: 3px;
  overflow: hidden;
}

.pcp-fill {
  height: 100%;
  background: #409eff;
  border-radius: 3px;
  transition: width .3s;
}

.pcp-text {
  font-size: 11px;
  color: #888;
  white-space: nowrap;
}

.loading-wrap {
  text-align: center;
  padding: 40px;
  color: #888;
}

.spinner {
  font-size: 32px;
}

.empty-block {
  text-align: center;
  padding: 40px;
  color: #666;
}

.empty-hint {
  font-size: 12px;
  color: #555;
  margin-top: 8px;
}

/* Project Detail */
.pd-back {
  margin-bottom: 12px;
}

.pd-hero {
  background: rgba(64, 158, 255, .04);
  border: 1px solid rgba(64, 158, 255, .12);
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 20px;
}

.pdh-tags {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
}

.tag {
  font-size: 12px;
  padding: 2px 10px;
  border-radius: 4px;
  background: rgba(255,255,255,.06);
  color: #aaa;
}

.tag.diff-medium { color: #e6a23c; }
.tag.diff-easy { color: #67c23a; }
.tag.diff-hard { color: #f56c6c; }
.tag.tag-time { color: #409eff; }

.pd-hero h2 {
  margin: 0 0 8px;
  font-size: 22px;
  color: #e0e0e0;
}

.pd-hero > p {
  margin: 0 0 16px;
  color: #999;
  font-size: 14px;
}

.pdh-progress {
  margin-bottom: 16px;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  color: #aaa;
  margin-bottom: 4px;
}

.progress-bar {
  height: 8px;
  background: rgba(255,255,255,.06);
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #409eff, #67c23a);
  border-radius: 4px;
  transition: width .5s;
}

.custom-tabs,
.project-tabs {
  display: flex;
  gap: 4px;
  margin-bottom: 16px;
  border-bottom: 1px solid rgba(255,255,255,.08);
  padding-bottom: 0;
}

.ctab {
  padding: 10px 16px !important;
  font-size: 14px !important;
  color: #888 !important;
  border-radius: 0 !important;
  border-bottom: 2px solid transparent !important;
  transition: all .2s;
  display: flex;
  align-items: center;
  gap: 6px;
}

.ctab:hover { color: #ccc !important; }
.ctab.active {
  color: #409eff !important;
  border-bottom-color: #409eff !important;
}

.ctab-badge {
  font-size: 11px;
  background: rgba(64,158,255,.15);
  color: #409eff;
  padding: 0 6px;
  border-radius: 10px;
}

/* Task Cards */
.task-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.task-card {
  background: rgba(255,255,255,.02);
  border: 1px solid rgba(255,255,255,.06);
  border-radius: 10px;
  padding: 16px;
  transition: border-color .2s;
}

.task-card.submitted {
  border-color: rgba(103,194,58,.2);
  background: rgba(103,194,58,.03);
}

.tc-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 10px;
}

.tch-left {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

.tc-number {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: rgba(64,158,255,.12);
  color: #409eff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 600;
  flex-shrink: 0;
}

.tch-left h4 {
  margin: 0 0 4px;
  font-size: 15px;
  color: #e0e0e0;
}

.tc-type {
  font-size: 12px;
  color: #888;
  background: rgba(255,255,255,.04);
  padding: 2px 8px;
  border-radius: 3px;
}

.tc-score {
  font-size: 13px;
  color: #e6a23c;
  font-weight: 600;
}

.tc-body {
  margin-bottom: 12px;
}

.tc-desc {
  color: #aaa;
  font-size: 13px;
  line-height: 1.6;
  margin-bottom: 8px;
}

.tc-requirements h5,
.tc-hints h5 {
  margin: 0 0 4px;
  font-size: 12px;
  color: #409eff;
}

.tc-requirements pre,
.tc-hints pre {
  margin: 0;
  font-size: 12px;
  color: #999;
  white-space: pre-wrap;
  background: rgba(0,0,0,.2);
  padding: 8px 12px;
  border-radius: 6px;
  max-height: 200px;
  overflow-y: auto;
}

.tc-footer {
  display: flex;
  align-items: center;
}

.tc-score-result {
  margin-left: auto;
  font-size: 13px;
  color: #67c23a;
  font-weight: 600;
}

/* Resources */
.resource-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.resource-card {
  display: flex;
  gap: 14px;
  padding: 14px;
  background: rgba(255,255,255,.02);
  border: 1px solid rgba(255,255,255,.06);
  border-radius: 8px;
}

.rc-icon {
  font-size: 24px;
  flex-shrink: 0;
}

.rc-body h4 {
  margin: 0 0 4px;
  font-size: 14px;
  color: #e0e0e0;
}

.rc-type {
  font-size: 11px;
  color: #777;
}

.rc-content {
  margin-top: 8px;
  font-size: 13px;
  color: #999;
  line-height: 1.5;
}

.rc-link {
  display: inline-block;
  margin-top: 8px;
  color: #409eff;
  font-size: 13px;
  text-decoration: none;
}

.rc-link:hover {
  text-decoration: underline;
}

/* Submissions */
.submission-card {
  background: rgba(255,255,255,.02);
  border: 1px solid rgba(255,255,255,.06);
  border-radius: 8px;
  padding: 14px;
  margin-bottom: 8px;
}

.sc-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
}

.sc-task {
  font-weight: 500;
  color: #ccc;
  font-size: 13px;
}

.sc-content {
  color: #aaa;
  font-size: 13px;
  line-height: 1.5;
  margin-bottom: 8px;
  white-space: pre-wrap;
}

.sc-meta {
  font-size: 12px;
  color: #666;
  display: flex;
  gap: 16px;
}

/* Evaluation */
.eval-card {
  background: rgba(255,255,255,.02);
  border: 1px solid rgba(255,255,255,.06);
  border-radius: 10px;
  padding: 20px;
}

.ev-status {
  font-size: 20px;
  font-weight: 600;
  color: #e6a23c;
  margin-bottom: 12px;
}

.ev-status.passed {
  color: #67c23a;
}

.ev-score {
  font-size: 16px;
  color: #409eff;
  margin-bottom: 12px;
}

.ev-comment h5,
.ev-feedback h5 {
  margin: 12px 0 4px;
  font-size: 13px;
  color: #ccc;
}

.ev-comment p,
.ev-feedback p {
  margin: 0;
  color: #999;
  font-size: 13px;
  line-height: 1.6;
}

.submit-dialog {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.sd-task-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.sd-type {
  font-size: 12px;
  color: #888;
  background: rgba(255,255,255,.04);
  padding: 2px 8px;
  border-radius: 3px;
}
</style>
