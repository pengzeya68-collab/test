<template>
  <div class="ai-tutor-page">
    <header class="page-header">
      <div class="header-titles">
        <h1 class="page-title">🤖 AI智能导师</h1>
        <p class="page-desc">你的专属测试学习私人教练，随时解答你的问题</p>
      </div>
    </header>

    <div class="tutor-container">
      <aside class="left-panel">
        <div class="panel-card">
          <h3 class="panel-title">功能列表</h3>
          <div class="function-list">
            <div
              class="function-item"
              :class="{ active: currentMode === 'chat' }"
              @click="switchMode('chat')"
            >
              <span class="func-icon">💬</span>
              <span>学习答疑</span>
            </div>
            <div
              class="function-item"
              :class="{ active: currentMode === 'code' }"
              @click="switchMode('code')"
            >
              <span class="func-icon">🔍</span>
              <span>代码审查</span>
            </div>
            <div
              class="function-item"
              :class="{ active: currentMode === 'advice' }"
              @click="getLearningAdvice"
            >
              <span class="func-icon">📈</span>
              <span>学习建议</span>
              <span v-if="getCostText('ai_learning_advice')" class="ai-cost-tag">{{ getCostText('ai_learning_advice') }}</span>
            </div>
            <div
              class="function-item"
              :class="{ active: currentMode === 'interview' }"
              @click="switchMode('interview')"
            >
              <span class="func-icon">🎤</span>
              <span>面试模拟</span>
            </div>
          </div>
        </div>

        <div class="panel-card">
          <h3 class="panel-title">快捷提问</h3>
          <div class="quick-questions">
            <button class="btn-quick" @click="quickQuestion('怎么学习Python自动化测试？')">Python自动化学习</button>
            <button class="btn-quick" @click="quickQuestion('接口测试需要掌握哪些技能？')">接口测试学习</button>
            <button class="btn-quick" @click="quickQuestion('测试工程师学习路径是什么？')">学习路径规划</button>
            <button class="btn-quick" @click="quickQuestion('测试工程师简历怎么写？')">简历优化建议</button>
            <button class="btn-quick" @click="quickQuestion('功能测试怎么转自动化测试？')">转自动化经验</button>
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
      </aside>

      <main class="right-panel">
        <div class="chat-container" ref="chatContainer">
          <div class="welcome-message" v-if="messages.length === 0">
            <div class="welcome-icon">🤖</div>
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
              <span v-if="msg.role === 'assistant'">🤖</span>
              <span v-else>👤</span>
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
                <span class="loading-dot"></span>
                <span class="loading-dot"></span>
                <span class="loading-dot"></span>
                <span class="loading-text">思考中...</span>
              </div>
            </div>
          </div>
        </div>

        <div class="input-container">
          <template v-if="currentMode === 'chat'">
            <textarea
              v-model="inputMessage"
              class="chat-textarea"
              rows="3"
              placeholder="有什么问题都可以问我哦... (Ctrl+Enter 发送)"
              @keydown.ctrl.enter="sendMessage"
            ></textarea>
            <div class="input-actions">
              <button class="btn-outline" @click="clearHistory">
                <span>🗑️</span> 清空对话
              </button>
              <button class="btn-primary" @click="sendMessage" :disabled="sending">
                <span>📨</span> {{ sending ? '发送中...' : '发送' }}
              </button>
              <span v-if="getCostText('ai_chat')" class="ai-cost-hint">{{ getCostText('ai_chat') }}</span>
            </div>
          </template>

          <template v-if="currentMode === 'code'">
            <div class="code-header">
              <select v-model="codeLanguage" class="native-select">
                <option value="python">Python</option>
                <option value="sql">SQL</option>
                <option value="shell">Shell</option>
                <option value="javascript">JavaScript</option>
              </select>
              <span class="code-tip">粘贴你的代码，我会帮你审查优化</span>
            </div>
            <textarea
              v-model="codeContent"
              class="chat-textarea code-textarea"
              rows="8"
              placeholder="请粘贴要审查的代码..."
            ></textarea>
            <div class="input-actions">
              <button class="btn-outline" @click="clearCode">🔄 清空</button>
              <button class="btn-primary" @click="reviewCode" :disabled="sending">
                ✅ {{ sending ? '审查中...' : '提交审查' }}
              </button>
              <span v-if="getCostText('ai_code_review')" class="ai-cost-hint">{{ getCostText('ai_code_review') }}</span>
            </div>
          </template>

          <template v-if="currentMode === 'interview'">
            <div class="interview-config" v-if="!interviewStarted">
              <div class="form-group">
                <label>目标岗位</label>
                <select v-model="interviewForm.position_level" class="native-select full">
                  <option value="功能测试工程师">功能测试工程师</option>
                  <option value="自动化测试工程师">自动化测试工程师</option>
                  <option value="测试开发工程师">测试开发工程师</option>
                  <option value="性能测试工程师">性能测试工程师</option>
                </select>
              </div>
              <div class="form-group">
                <label>工作经验</label>
                <select v-model="interviewForm.years_of_experience" class="native-select full">
                  <option :value="0">应届生</option>
                  <option :value="2">1-3年</option>
                  <option :value="4">3-5年</option>
                  <option :value="6">5年以上</option>
                </select>
              </div>
              <div class="form-group">
                <label>面试轮次</label>
                <select v-model="interviewForm.interview_round" class="native-select full">
                  <option value="一面">一面（技术基础）</option>
                  <option value="二面">二面（技术深度）</option>
                  <option value="三面">三面（综合能力）</option>
                </select>
              </div>
              <button class="btn-primary btn-full" @click="startInterview">🚀 开始模拟面试</button>
            </div>

            <div v-else>
              <div class="interview-status">
                <span class="status-icon">⏳</span>
                <div>
                  <strong>面试进行中</strong>
                  <p>请认真回答面试官的问题，回答完点击提交按钮</p>
                </div>
              </div>
              <textarea
                v-model="inputMessage"
                class="chat-textarea"
                rows="5"
                placeholder="请输入你的回答..."
              ></textarea>
              <div class="input-actions">
                <button class="btn-outline" @click="endInterview">🛑 结束面试</button>
                <button class="btn-primary" @click="sendInterviewAnswer" :disabled="sending">
                  📤 {{ sending ? '提交中...' : '提交回答' }}
                </button>
              </div>
            </div>
          </template>
        </div>
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import request from '@/utils/request'
import { useAICosts } from '@/composables/useAICosts'
import { renderMarkdown } from '@/utils/markdown'
import {
  chat as aiChat,
  codeReview as aiCodeReview,
  getLearningAdvice as aiGetLearningAdvice,
  clearHistory as aiClearHistory,
  startInterview as aiStartInterview
} from '@/api/interview-adapter'

const { fetchCosts, getCostText } = useAICosts()

const currentMode = ref('chat')
const inputMessage = ref('')
const codeContent = ref('')
const codeLanguage = ref('python')
const messages = ref([])
const sending = ref(false)
const chatContainer = ref(null)
const interviewStarted = ref(false)
const interviewForm = ref({
  position_level: '功能测试工程师',
  years_of_experience: 2,
  interview_round: '一面'
})

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

  addMessage('user', question)
  addMessage('assistant', '', true)
  sending.value = true

  try {
    const res = await aiChat({ question, type: 'general' })
    messages.value[messages.value.length - 1] = {
      role: 'assistant',
      content: res.answer,
      time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
      loading: false
    }
  } catch (error) {
    console.error('发送消息失败:', error)
    ElMessage.error('发送消息失败，请稍后重试')
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
  addMessage('user', `请审查这段${codeLanguage.value}代码：\n\`\`\`${codeLanguage.value}\n${code}\n\`\`\``)
  addMessage('assistant', '', true)
  sending.value = true

  try {
    const res = await aiCodeReview({ code, language: codeLanguage.value })
    messages.value[messages.value.length - 1] = {
      role: 'assistant',
      content: res.review_result,
      time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
      loading: false
    }
  } catch (error) {
    console.error('代码审查失败:', error)
    ElMessage.error('代码审查失败，请稍后重试')
    messages.value.pop()
  } finally {
    sending.value = false
    scrollToBottom()
  }
}

const getLearningAdvice = async () => {
  currentMode.value = 'advice'
  addMessage('user', '请根据我的技能情况给出学习建议')
  addMessage('assistant', '', true)
  sending.value = true

  try {
    const res = await aiGetLearningAdvice()
    messages.value[messages.value.length - 1] = {
      role: 'assistant',
      content: res.advice,
      time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
      loading: false
    }
  } catch (error) {
    console.error('获取学习建议失败:', error)
    ElMessage.error('获取学习建议失败，请稍后重试')
    messages.value.pop()
  } finally {
    sending.value = false
    scrollToBottom()
  }
}

const startInterview = async () => {
  interviewStarted.value = true
  const question = `我要模拟${interviewForm.position_level}面试，工作经验${interviewForm.years_of_experience}年，${interviewForm.interview_round}。请开始面试。`
  addMessage('user', question)
  addMessage('assistant', '', true)
  sending.value = true

  try {
    const res = await aiStartInterview({
      position: interviewForm.position_level,
      experience: interviewForm.years_of_experience,
      round: interviewForm.interview_round
    })
    messages.value[messages.value.length - 1] = {
      role: 'assistant',
      content: res.answer,
      time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
      loading: false
    }
  } catch (error) {
    console.error('开始面试失败:', error)
    ElMessage.error('开始面试失败，请稍后重试')
    messages.value.pop()
  } finally {
    sending.value = false
    scrollToBottom()
  }
}

const sendInterviewAnswer = async () => {
  if (!inputMessage.value.trim()) {
    ElMessage.warning('请输入你的回答')
    return
  }

  const answer = inputMessage.value.trim()
  inputMessage.value = ''
  addMessage('user', answer)
  addMessage('assistant', '', true)
  sending.value = true

  try {
    const res = await aiChat({ question: answer, type: 'interview' })
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
    await aiClearHistory()
    messages.value = []
    ElMessage.success('对话历史已清空')
  } catch (error) {
    console.error('清空历史失败:', error)
    ElMessage.error('清空历史失败')
  }
}

onMounted(() => {
  fetchCosts()
})
</script>

<style scoped>
.ai-tutor-page {
  width: 100%;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  padding: 32px 40px;
  box-sizing: border-box;
  background-color: var(--tm-bg-page);
  color: var(--tm-text-primary);
  gap: 24px;
}

.page-header {
  padding-bottom: 16px;
  border-bottom: 1px solid #27272a;
}
.header-titles {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.page-title {
  font-size: 26px;
  font-weight: 800;
  color: var(--tm-text-primary);
  margin: 0;
}
.page-desc {
  font-size: 14px;
  color: var(--tm-text-regular);
  margin: 0;
}

.tutor-container {
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: 20px;
  flex: 1;
  min-height: 0;
}

/* Left Panel */
.left-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.panel-card {
  background: var(--tm-card-bg);
  border: 1px solid var(--tm-border-light);
  border-radius: 12px;
  padding: 18px;
}
.panel-title {
  font-size: 15px;
  font-weight: 700;
  color: var(--tm-text-primary);
  margin: 0 0 14px 0;
}

.function-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.function-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 14px;
  color: var(--tm-text-regular);
}
.function-item:hover {
  background: rgba(var(--tm-color-primary-rgb), 0.06);
  color: var(--tm-text-regular);
}
.function-item.active {
  background: rgba(var(--tm-color-primary-rgb), 0.1);
  color: var(--tm-color-primary);
  font-weight: 600;
}
.func-icon { font-size: 16px; }

.quick-questions {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.btn-quick {
  width: 100%;
  text-align: left;
  padding: 8px 12px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid var(--tm-border-light);
  border-radius: 6px;
  color: var(--tm-text-regular);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}
.btn-quick:hover {
  background: rgba(var(--tm-color-primary-rgb), 0.08);
  border-color: rgba(var(--tm-color-primary-rgb), 0.2);
  color: var(--tm-text-regular);
}

.usage-tips {
  font-size: 12px;
  line-height: 1.8;
  color: var(--tm-text-secondary);
}
.usage-tips p { margin: 0 0 6px 0; }
.usage-tips strong { color: var(--tm-text-regular); }

/* Right Panel */
.right-panel {
  background: var(--tm-card-bg);
  border: 1px solid var(--tm-border-light);
  border-radius: 14px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-height: 0;
}

.chat-container {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
  background: rgba(9, 9, 11, 0.3);
  min-height: 0;
}

.welcome-message {
  text-align: center;
  padding: 60px 20px;
}
.welcome-icon {
  font-size: 52px;
  margin-bottom: 20px;
  animation: float 3s ease-in-out infinite;
}
@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-8px); }
}
.welcome-message h2 {
  font-size: 22px;
  font-weight: 800;
  color: var(--tm-text-primary);
  margin: 0 0 14px 0;
}
.welcome-message p {
  font-size: 14px;
  line-height: 1.8;
  margin: 0 0 6px 0;
  color: var(--tm-text-regular);
}

/* Messages */
.message-item {
  display: flex;
  gap: 12px;
  margin-bottom: 22px;
}
.message-item.user {
  flex-direction: row-reverse;
}
.message-avatar {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  background: var(--tm-card-bg);
  border: 1px solid var(--tm-border-light);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-size: 18px;
}
.message-content {
  max-width: 72%;
}
.message-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 6px;
}
.message-item.user .message-header {
  flex-direction: row-reverse;
}
.message-name {
  font-size: 12px;
  font-weight: 600;
  color: var(--tm-text-secondary);
}
.message-time {
  font-size: 11px;
  color: #52525b;
}
.message-text {
  background: var(--tm-card-bg);
  padding: 14px 18px;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.04);
  line-height: 1.7;
  font-size: 14px;
  color: var(--tm-text-regular);
}
.message-item.user .message-text {
  background: rgba(var(--tm-color-primary-rgb), 0.08);
  border-color: rgba(var(--tm-color-primary-rgb), 0.15);
  color: var(--tm-text-primary);
}

/* Loading dots */
.message-loading {
  background: var(--tm-card-bg);
  padding: 16px 20px;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.04);
  display: flex;
  align-items: center;
  gap: 6px;
}
.loading-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--tm-color-primary);
  animation: dotPulse 1.4s ease-in-out infinite;
}
.loading-dot:nth-child(2) { animation-delay: 0.2s; }
.loading-dot:nth-child(3) { animation-delay: 0.4s; }
@keyframes dotPulse {
  0%, 80%, 100% { opacity: 0.3; transform: scale(0.8); }
  40% { opacity: 1; transform: scale(1); }
}
.loading-text {
  margin-left: 8px;
  font-size: 13px;
  color: var(--tm-text-secondary);
}

/* Markdown */
.markdown-content { line-height: 1.7; }
.markdown-content h1,
.markdown-content h2,
.markdown-content h3,
.markdown-content h4 {
  margin: 14px 0 8px 0;
  font-weight: 700;
  color: var(--tm-text-primary);
}
.markdown-content h1 { font-size: 18px; border-bottom: 1px solid #27272a; padding-bottom: 6px; }
.markdown-content h2 { font-size: 16px; }
.markdown-content h3 { font-size: 15px; }
.markdown-content p { margin: 8px 0; color: var(--tm-text-regular); }
.markdown-content ul,
.markdown-content ol { margin: 8px 0; padding-left: 22px; color: var(--tm-text-regular); }
.markdown-content li { margin: 4px 0; }
.markdown-content code {
  background: rgba(var(--tm-color-primary-rgb), 0.1);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 13px;
  color: #c084fc;
}
.markdown-content pre {
  background: var(--tm-card-bg);
  padding: 14px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 10px 0;
  border: 1px solid #27272a;
}
.markdown-content pre code {
  background: none;
  padding: 0;
  color: var(--tm-text-primary);
  line-height: 1.6;
}
.markdown-content blockquote {
  border-left: 3px solid var(--tm-color-primary);
  padding-left: 14px;
  margin: 10px 0;
  color: var(--tm-text-regular);
  background: rgba(var(--tm-color-primary-rgb), 0.04);
  padding: 10px 14px;
  border-radius: 0 8px 8px 0;
}
.markdown-content table {
  border-collapse: collapse;
  width: 100%;
  margin: 10px 0;
}
.markdown-content th,
.markdown-content td {
  border: 1px solid #27272a;
  padding: 6px 10px;
  text-align: left;
}
.markdown-content th {
  background: rgba(255, 255, 255, 0.04);
  font-weight: 700;
  color: var(--tm-text-primary);
}

/* Input Container */
.input-container {
  padding: 18px;
  border-top: 1px solid var(--tm-border-light);
  background: var(--tm-card-bg);
}

.chat-textarea {
  width: 100%;
  resize: none;
  background: rgba(9, 9, 11, 0.8);
  border: 1px solid #27272a;
  border-radius: 10px;
  padding: 14px;
  color: var(--tm-text-primary);
  font-size: 14px;
  font-family: inherit;
  line-height: 1.6;
  box-sizing: border-box;
  outline: none;
  transition: border-color 0.2s;
}
.chat-textarea:focus {
  border-color: var(--tm-color-primary);
}
.chat-textarea::placeholder {
  color: #52525b;
}
.code-textarea {
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
}

.input-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 12px;
}

.btn-primary {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: linear-gradient(135deg, var(--tm-color-primary), var(--tm-color-primary-dark));
  color: #fff;
  border: none;
  padding: 10px 20px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}
.btn-primary:hover { opacity: 0.9; transform: translateY(-1px); }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }
.btn-outline {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: transparent;
  color: var(--tm-text-regular);
  border: 1px solid var(--tm-border-light);
  padding: 9px 18px;
  border-radius: 8px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}
.btn-outline:hover {
  border-color: var(--tm-color-primary);
  color: var(--tm-text-regular);
}

/* Code mode */
.code-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}
.native-select {
  background: rgba(9, 9, 11, 0.8);
  border: 1px solid #27272a;
  border-radius: 6px;
  padding: 8px 12px;
  color: var(--tm-text-primary);
  font-size: 13px;
  cursor: pointer;
  outline: none;
}
.native-select.full { width: 100%; }
.code-tip {
  font-size: 13px;
  color: var(--tm-text-secondary);
}

/* Interview */
.interview-config {
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.form-group {
  display: flex;
  align-items: center;
  gap: 14px;
}
.form-group label {
  width: 80px;
  font-size: 13px;
  color: var(--tm-text-regular);
  text-align: right;
  flex-shrink: 0;
}
.form-group select {
  flex: 1;
}
.btn-full {
  width: 100%;
  justify-content: center;
  padding: 12px;
  font-size: 15px;
}

.interview-status {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 14px 16px;
  background: rgba(59, 130, 246, 0.06);
  border: 1px solid rgba(59, 130, 246, 0.15);
  border-radius: 10px;
  margin-bottom: 14px;
}
.status-icon { font-size: 20px; flex-shrink: 0; }
.interview-status strong {
  display: block;
  font-size: 14px;
  color: var(--tm-text-primary);
  margin-bottom: 2px;
}
.interview-status p {
  font-size: 13px;
  color: var(--tm-text-regular);
  margin: 0;
}

@media (max-width: 1000px) {
  .tutor-container { grid-template-columns: 1fr; }
  .left-panel { order: 2; }
  .right-panel { order: 1; min-height: 500px; }
  .message-content { max-width: 88%; }
  .ai-tutor-page { padding: 20px 16px; }
}

.ai-cost-hint {
  font-size: 11px;
  color: #ffa502;
  margin-left: 8px;
  white-space: nowrap;
}
.ai-cost-tag {
  font-size: 10px;
  color: #ffa502;
  background: rgba(255,165,2,0.1);
  padding: 1px 6px;
  border-radius: 8px;
  margin-left: auto;
}
</style>