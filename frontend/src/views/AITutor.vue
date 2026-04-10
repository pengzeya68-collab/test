<template>
  <div class="ai-tutor">
    <div class="container">
      <div class="page-header">
        <h1 class="page-title">AI智能导师</h1>
        <p class="page-subtitle">你的专属测试学习私人教练，随时解答你的问题</p>
      </div>

      <div class="tutor-container">
        <!-- 左侧功能面板 -->
        <div class="left-panel">
          <div class="panel-card">
            <h3 class="panel-title">功能列表</h3>
            <div class="function-list">
              <div 
                class="function-item" 
                :class="{ active: currentMode === 'chat' }"
                @click="switchMode('chat')"
              >
                <el-icon size="20"><ChatDotRound /></el-icon>
                <span>学习答疑</span>
              </div>
              <div 
                class="function-item" 
                :class="{ active: currentMode === 'code' }"
                @click="switchMode('code')"
              >
                <el-icon size="20"><Code /></el-icon>
                <span>代码审查</span>
              </div>
              <div 
                class="function-item" 
                :class="{ active: currentMode === 'advice' }"
                @click="getLearningAdvice"
              >
                <el-icon size="20"><Guide /></el-icon>
                <span>学习建议</span>
              </div>
              <div 
                class="function-item" 
                :class="{ active: currentMode === 'interview' }"
                @click="switchMode('interview')"
              >
                <el-icon size="20"><User /></el-icon>
                <span>面试模拟</span>
              </div>
            </div>
          </div>

          <div class="panel-card">
            <h3 class="panel-title">快捷提问</h3>
            <div class="quick-questions">
              <el-button 
                type="info" 
                size="small" 
                @click="quickQuestion('怎么学习Python自动化测试？')"
              >
                Python自动化学习
              </el-button>
              <el-button 
                type="info" 
                size="small" 
                @click="quickQuestion('接口测试需要掌握哪些技能？')"
              >
                接口测试学习
              </el-button>
              <el-button 
                type="info" 
                size="small" 
                @click="quickQuestion('测试工程师学习路径是什么？')"
              >
                学习路径规划
              </el-button>
              <el-button 
                type="info" 
                size="small" 
                @click="quickQuestion('测试工程师简历怎么写？')"
              >
                简历优化建议
              </el-button>
              <el-button 
                type="info" 
                size="small" 
                @click="quickQuestion('功能测试怎么转自动化测试？')"
              >
                转自动化经验
              </el-button>
            </div>
          </div>

          <div class="panel-card">
            <h3 class="panel-title">使用说明</h3>
            <div class="usage-tips">
              <p><strong>💡 学习答疑：</strong>有任何测试相关的问题都可以提问</p>
              <p><strong>💡 代码审查：</strong>粘贴你的代码，AI会帮你审查并给出优化建议</p>
              <p><strong>💡 学习建议：</strong>根据你的技能情况给出个性化学习规划</p>
              <p><strong>💡 面试模拟：</strong>模拟真实面试场景，提升面试能力</p>
            </div>
          </div>
        </div>

        <!-- 右侧对话区域 -->
        <div class="right-panel">
          <!-- 对话内容 -->
          <div class="chat-container" ref="chatContainer">
            <div class="welcome-message" v-if="messages.length === 0">
              <div class="welcome-avatar">
                <el-icon size="48" color="#409eff"><Robot /></el-icon>
              </div>
              <h2>你好！我是你的AI测试导师 TestMaster</h2>
              <p>我有10年软件测试行业经验，精通功能测试、接口测试、自动化测试、性能测试等技术。</p>
              <p>有什么问题都可以问我，我会尽力为你解答！</p>
            </div>

            <div 
              class="message-item" 
              v-for="(msg, index) in messages" 
              :key="index"
              :class="msg.role"
            >
              <div class="message-avatar">
                <el-icon size="24" v-if="msg.role === 'assistant'" color="#409eff"><Robot /></el-icon>
                <el-icon size="24" v-else color="#67c23a"><User /></el-icon>
              </div>
              <div class="message-content">
                <div class="message-header">
                  <span class="message-name">{{ msg.role === 'assistant' ? 'AI导师' : '我' }}</span>
                  <span class="message-time">{{ msg.time }}</span>
                </div>
                <div class="message-text" v-if="!msg.loading">
                  <div class="markdown-content" v-html="renderMarkdown(msg.content)"></div>
                </div>
                <div class="message-loading" v-else>
                  <el-spinner size="20" />
                  <span>正在思考中...</span>
                </div>
              </div>
            </div>
          </div>

          <!-- 输入区域 -->
          <div class="input-container">
            <!-- 普通聊天模式 -->
            <div v-if="currentMode === 'chat'">
              <el-input
                v-model="inputMessage"
                type="textarea"
                :rows="3"
                placeholder="有什么问题都可以问我哦..."
                @keydown.ctrl.enter="sendMessage"
              />
              <div class="input-actions">
                <el-button @click="clearHistory">
                  <el-icon><Delete /></el-icon>
                  清空对话
                </el-button>
                <el-button type="primary" @click="sendMessage" :loading="sending">
                  <el-icon><Promotion /></el-icon>
                  发送
                </el-button>
              </div>
            </div>

            <!-- 代码审查模式 -->
            <div v-if="currentMode === 'code'">
              <div class="code-header">
                <el-select v-model="codeLanguage" size="small" style="width: 120px;">
                  <el-option label="Python" value="python" />
                  <el-option label="SQL" value="sql" />
                  <el-option label="Shell" value="shell" />
                  <el-option label="JavaScript" value="javascript" />
                </el-select>
                <span class="code-tip">粘贴你的代码，我会帮你审查优化</span>
              </div>
              <el-input
                v-model="codeContent"
                type="textarea"
                :rows="8"
                placeholder="请粘贴要审查的代码..."
              />
              <div class="input-actions">
                <el-button @click="clearCode">
                  <el-icon><Refresh /></el-icon>
                  清空
                </el-button>
                <el-button type="primary" @click="reviewCode" :loading="sending">
                  <el-icon><Check /></el-icon>
                  提交审查
                </el-button>
              </div>
            </div>

            <!-- 面试模拟模式 -->
            <div v-if="currentMode === 'interview'">
              <div class="interview-config" v-if="!interviewStarted">
                <el-form :model="interviewForm" label-width="100px">
                  <el-form-item label="目标岗位">
                    <el-select v-model="interviewForm.position" style="width: 200px;">
                      <el-option label="功能测试工程师" value="功能测试工程师" />
                      <el-option label="自动化测试工程师" value="自动化测试工程师" />
                      <el-option label="测试开发工程师" value="测试开发工程师" />
                      <el-option label="性能测试工程师" value="性能测试工程师" />
                    </el-select>
                  </el-form-item>
                  <el-form-item label="工作经验">
                    <el-select v-model="interviewForm.experience" style="width: 200px;">
                      <el-option label="应届生" :value="0" />
                      <el-option label="1-3年" :value="2" />
                      <el-option label="3-5年" :value="4" />
                      <el-option label="5年以上" :value="6" />
                    </el-select>
                  </el-form-item>
                  <el-form-item label="面试轮次">
                    <el-select v-model="interviewForm.round" style="width: 200px;">
                      <el-option label="一面（技术基础）" value="一面" />
                      <el-option label="二面（技术深度）" value="二面" />
                      <el-option label="三面（综合能力）" value="三面" />
                    </el-select>
                  </el-form-item>
                </el-form>
                <el-button type="primary" @click="startInterview">开始模拟面试</el-button>
              </div>

              <div v-else>
                <div class="interview-status">
                  <el-alert 
                    title="面试进行中" 
                    type="info" 
                    :closable="false"
                    description="请认真回答面试官的问题，回答完点击提交按钮"
                  />
                </div>
                <el-input
                  v-model="inputMessage"
                  type="textarea"
                  :rows="5"
                  placeholder="请输入你的回答..."
                />
                <div class="input-actions">
                  <el-button @click="endInterview">
                    结束面试
                  </el-button>
                  <el-button type="primary" @click="sendInterviewAnswer" :loading="sending">
                    提交回答
                  </el-button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { 
  ChatDotRound, Guide, User, Delete, Promotion, 
  Refresh, Check
} from '@element-plus/icons-vue'
import request from '@/utils/request'
import { marked } from 'marked'

const currentMode = ref('chat')
const inputMessage = ref('')
const codeContent = ref('')
const codeLanguage = ref('python')
const messages = ref([])
const sending = ref(false)
const chatContainer = ref(null)
const interviewStarted = ref(false)
const interviewForm = ref({
  position: '功能测试工程师',
  experience: 2,
  round: '一面'
})

// 配置marked
marked.setOptions({
  breaks: true,
  gfm: true
})

const renderMarkdown = (content) => {
  return marked(content)
}

const switchMode = (mode) => {
  currentMode.value = mode
  if (mode === 'code') {
    codeContent.value = ''
  }
}

const quickQuestion = (question) => {
  currentMode.value = 'chat'
  inputMessage.value = question
  sendMessage()
}

const addMessage = (role, content, loading = false) => {
  const now = new Date()
  const time = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}`
  
  messages.value.push({
    role,
    content,
    time,
    loading
  })
  
  scrollToBottom()
}

const scrollToBottom = () => {
  nextTick(() => {
    if (chatContainer.value) {
      chatContainer.value.scrollTop = chatContainer.value.scrollHeight
    }
  })
}

const sendMessage = async () => {
  if (!inputMessage.value.trim()) {
    ElMessage.warning('请输入问题')
    return
  }
  
  const question = inputMessage.value.trim()
  inputMessage.value = ''
  
  // 添加用户消息
  addMessage('user', question)
  
  // 添加AI loading消息
  addMessage('assistant', '', true)
  sending.value = true
  
  try {
    const res = await request.post('/ai/chat', {
      question,
      type: 'general'
    })
    
    // 替换loading消息
    messages.value[messages.value.length - 1] = {
      role: 'assistant',
      content: res.answer,
      time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
      loading: false
    }
    
  } catch (error) {
    console.error('发送消息失败:', error)
    ElMessage.error('发送消息失败，请稍后重试')
    
    // 移除loading消息
    messages.value.pop()
  } finally {
    sending.value = false
    scrollToBottom()
  }
}

const reviewCode = async () => {
  if (!codeContent.value.trim()) {
    ElMessage.warning('请输入要审查的代码')
    return
  }
  
  const code = codeContent.value.trim()
  
  // 添加用户消息
  addMessage('user', `请审查这段${codeLanguage.value}代码：\n\`\`\`${codeLanguage.value}\n${code}\n\`\`\``)
  
  // 添加AI loading消息
  addMessage('assistant', '', true)
  sending.value = true
  
  try {
    const res = await request.post('/ai/code-review', {
      code,
      language: codeLanguage.value
    })
    
    // 替换loading消息
    messages.value[messages.value.length - 1] = {
      role: 'assistant',
      content: res.review_result,
      time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
      loading: false
    }
    
  } catch (error) {
    console.error('代码审查失败:', error)
    ElMessage.error('代码审查失败，请稍后重试')
    
    // 移除loading消息
    messages.value.pop()
  } finally {
    sending.value = false
    scrollToBottom()
  }
}

const getLearningAdvice = async () => {
  currentMode.value = 'advice'
  
  // 添加系统消息
  addMessage('user', '请根据我的技能情况给出学习建议')
  
  // 添加AI loading消息
  addMessage('assistant', '', true)
  sending.value = true
  
  try {
    const res = await request.get('/ai/learning-advice')
    
    // 替换loading消息
    messages.value[messages.value.length - 1] = {
      role: 'assistant',
      content: res.advice,
      time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
      loading: false
    }
    
  } catch (error) {
    console.error('获取学习建议失败:', error)
    ElMessage.error('获取学习建议失败，请稍后重试')
    
    // 移除loading消息
    messages.value.pop()
  } finally {
    sending.value = false
    scrollToBottom()
  }
}

const startInterview = () => {
  interviewStarted.value = true
  
  const question = `我要模拟${interviewForm.position}面试，工作经验${interviewForm.experience}年，${interviewForm.round}。请开始面试。`
  
  // 添加用户消息
  addMessage('user', question)
  
  // 添加AI loading消息
  addMessage('assistant', '', true)
  sending.value = true
  
  request.post('/ai/chat', {
    question,
    type: 'interview'
  }).then(res => {
    // 替换loading消息
    messages.value[messages.value.length - 1] = {
      role: 'assistant',
      content: res.answer,
      time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
      loading: false
    }
  }).catch(error => {
    console.error('开始面试失败:', error)
    ElMessage.error('开始面试失败，请稍后重试')
    messages.value.pop()
  }).finally(() => {
    sending.value = false
    scrollToBottom()
  })
}

const sendInterviewAnswer = async () => {
  if (!inputMessage.value.trim()) {
    ElMessage.warning('请输入你的回答')
    return
  }
  
  const answer = inputMessage.value.trim()
  inputMessage.value = ''
  
  // 添加用户消息
  addMessage('user', answer)
  
  // 添加AI loading消息
  addMessage('assistant', '', true)
  sending.value = true
  
  try {
    const res = await request.post('/ai/chat', {
      question: answer,
      type: 'interview'
    })
    
    // 替换loading消息
    messages.value[messages.value.length - 1] = {
      role: 'assistant',
      content: res.answer,
      time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
      loading: false
    }
    
  } catch (error) {
    console.error('提交回答失败:', error)
    ElMessage.error('提交回答失败，请稍后重试')
    messages.value.pop()
  } finally {
    sending.value = false
    scrollToBottom()
  }
}

const endInterview = () => {
  interviewStarted.value = false
  ElMessage.success('面试模拟已结束')
}

const clearCode = () => {
  codeContent.value = ''
}

const clearHistory = async () => {
  try {
    await request.post('/ai/clear-history')
    messages.value = []
    ElMessage.success('对话历史已清空')
  } catch (error) {
    console.error('清空历史失败:', error)
    ElMessage.error('清空历史失败')
  }
}
</script>

<style scoped>
.ai-tutor {
  padding: 30px 0;
  min-height: calc(100vh - 60px);
  background-color: var(--tm-bg-color);
  background-image: var(--tm-bg-image);
  background-size: cover;
  background-position: center;
}

.container {
  width: 100%;
  max-width: 1440px;
  padding: 0 24px;
  margin: 0 auto;
  box-sizing: border-box;
}

.page-header {
  margin-bottom: 30px;
}

.page-title {
  font-size: 32px;
  font-weight: bold;
  color: var(--tm-text-primary);
  margin: 0 0 8px 0;
}

.page-subtitle {
  font-size: 14px;
  color: var(--tm-text-secondary);
  margin: 0;
}

.tutor-container {
  display: grid;
  grid-template-columns: 320px 1fr;
  gap: 24px;
  height: calc(100vh - 200px);
}

.left-panel {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.panel-card {
  background: var(--tm-card-bg);
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  border: var(--tm-card-border);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
}

.panel-title {
  font-size: 16px;
  font-weight: bold;
  color: var(--tm-text-primary);
  margin: 0 0 16px 0;
}

.function-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.function-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 14px;
  color: var(--tm-text-secondary);
}

.function-item:hover {
  background: var(--tm-bg-hover);
  color: var(--tm-color-primary);
}

.function-item.active {
  background: rgba(var(--tm-color-primary), 0.1);
  color: var(--tm-color-primary);
}

.quick-questions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.quick-questions .el-button {
  width: 100%;
  justify-content: flex-start;
}

.usage-tips {
  font-size: 13px;
  line-height: 2;
  color: var(--tm-text-secondary);
}

.usage-tips p {
  margin: 0 0 8px 0;
}

.right-panel {
  background: var(--tm-card-bg);
  border-radius: 12px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  border: var(--tm-card-border);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.chat-container {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
  background: rgba(var(--tm-bg-page-rgb), 0.5);
  /* 聊天气泡最佳阅读宽度限制，居中显示 */
  max-width: 900px;
  margin: 0 auto;
  width: 100%;
}

.welcome-message {
  text-align: center;
  padding: 60px 20px;
  color: var(--tm-text-secondary);
}

.welcome-avatar {
  margin-bottom: 20px;
}

.welcome-message h2 {
  font-size: 24px;
  font-weight: bold;
  color: var(--tm-text-primary);
  margin: 0 0 16px 0;
}

.welcome-message p {
  font-size: 14px;
  line-height: 1.8;
  margin: 0 0 8px 0;
  color: var(--tm-text-secondary);
}

.message-item {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
}

.message-item.user {
  flex-direction: row-reverse;
}

.message-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: var(--tm-card-bg);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-shadow: 0 2px 8px 0 rgba(0, 0, 0, 0.1);
}

.message-content {
  max-width: 70%;
}

.message-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.message-item.user .message-header {
  flex-direction: row-reverse;
}

.message-name {
  font-size: 13px;
  font-weight: 500;
  color: var(--tm-text-secondary);
}

.message-time {
  font-size: 12px;
  color: var(--tm-text-secondary);
}

.message-text {
  background: var(--tm-card-bg);
  padding: 16px 20px;
  border-radius: 12px;
  box-shadow: 0 2px 8px 0 rgba(0, 0, 0, 0.08);
  line-height: 1.8;
  font-size: 14px;
  color: var(--tm-text-primary);
}

.message-item.user .message-text {
  background: rgba(var(--tm-color-primary), 0.1);
}

.message-loading {
  background: var(--tm-card-bg);
  padding: 16px 20px;
  border-radius: 12px;
  box-shadow: 0 2px 8px 0 rgba(0, 0, 0, 0.08);
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: var(--tm-text-secondary);
}

/* Markdown样式 */
.markdown-content {
  line-height: 1.8;
}

.markdown-content h1,
.markdown-content h2,
.markdown-content h3,
.markdown-content h4 {
  margin: 16px 0 8px 0;
  font-weight: bold;
  color: var(--tm-text-primary);
}

.markdown-content h1 {
  font-size: 20px;
  border-bottom: 1px solid var(--tm-border-light);
  padding-bottom: 8px;
}

.markdown-content h2 {
  font-size: 18px;
}

.markdown-content h3 {
  font-size: 16px;
}

.markdown-content p {
  margin: 8px 0;
  color: var(--tm-text-primary);
}

.markdown-content ul,
.markdown-content ol {
  margin: 8px 0;
  padding-left: 24px;
  color: var(--tm-text-primary);
}

.markdown-content li {
  margin: 4px 0;
  color: var(--tm-text-primary);
}

.markdown-content code {
  background: rgba(var(--tm-bg-page-rgb), 0.5);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 13px;
  color: #e6a23c;
}

.markdown-content pre {
  background: #282c34;
  padding: 16px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 12px 0;
}

.markdown-content pre code {
  background: none;
  padding: 0;
  color: #abb2bf;
  line-height: 1.6;
}

.markdown-content blockquote {
  border-left: 4px solid var(--tm-color-primary);
  padding-left: 16px;
  margin: 12px 0;
  color: var(--tm-text-secondary);
  background: rgba(var(--tm-bg-page-rgb), 0.5);
  padding: 12px 16px;
  border-radius: 0 8px 8px 0;
}

.markdown-content table {
  border-collapse: collapse;
  width: 100%;
  margin: 12px 0;
}

.markdown-content th,
.markdown-content td {
  border: 1px solid var(--tm-border-light);
  padding: 8px 12px;
  text-align: left;
}

.markdown-content th {
  background: rgba(var(--tm-bg-page-rgb), 0.5);
  font-weight: bold;
}

.input-container {
  padding: 20px;
  border-top: 1px solid var(--tm-border-light);
  background: var(--tm-card-bg);
}

.code-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.code-tip {
  font-size: 13px;
  color: var(--tm-text-secondary);
}

.input-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 12px;
}

.interview-config {
  margin-bottom: 20px;
}

.interview-status {
  margin-bottom: 20px;
}

@media (max-width: 1200px) {
  .tutor-container {
    grid-template-columns: 1fr;
    height: auto;
  }

  .left-panel {
    order: 2;
  }

  .right-panel {
    order: 1;
    min-height: 500px;
  }

  .message-content {
    max-width: 85%;
  }
}
</style>
