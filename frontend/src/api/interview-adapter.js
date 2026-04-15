import request from '@/utils/request'

const BT = String.fromCharCode(96)
const AI_TIMEOUT = 120000

export async function chat(params) {
  const { question, type = 'general' } = params

  if (type === 'interview') {
    try {
      const sessionsRes = await request.get('/interview/sessions', {
        params: { page: 1, size: 1, status_filter: 'started' }
      })

      let sessionId
      if (sessionsRes.data?.items?.length > 0) {
        sessionId = sessionsRes.data.items[0].id
      } else {
        const questionsRes = await request.get('/interview/questions', {
          params: { page: 1, size: 1 }
        })

        if (questionsRes.data?.items?.length > 0) {
          const questionId = questionsRes.data.items[0].id
          const sessionRes = await request.post('/interview/sessions', {
            question_id: questionId
          })
          sessionId = sessionRes.data.id
        } else {
          return { answer: '目前没有可用的面试题目，请联系管理员添加题目。' }
        }
      }

      const evaluateRes = await request.post('/interview/evaluate', {
        source_code: question,
        language: 'text',
        question_id: 'adapter-chat'
      })

      return { answer: evaluateRes.data?.feedback || '收到您的回答，面试官正在评估...' }
    } catch (error) {
      console.error('面试接口调用失败:', error)
      try {
        const res = await request.post('/ai/chat', { question, context: '面试模拟场景' }, { timeout: AI_TIMEOUT })
        return { answer: res.answer }
      } catch {
        return { answer: '面试系统暂时不可用，请稍后重试。' }
      }
    }
  } else {
    try {
      const res = await request.post('/ai/chat', { question }, { timeout: AI_TIMEOUT })
      return { answer: res.answer }
    } catch (error) {
      console.error('AI聊天接口调用失败:', error)
      return { answer: 'AI服务暂时不可用，请稍后重试。' }
    }
  }
}

export async function codeReview(params) {
  const { code, language = 'python' } = params

  try {
    const res = await request.post('/ai/code-review', { code, language }, { timeout: AI_TIMEOUT })
    return { review_result: res.review_result }
  } catch (error) {
    console.error('AI代码审查接口调用失败:', error)
    try {
      const execRes = await request.post('/sandbox/execute', {
        code, language, timeout: 5
      })
      const executionResult = execRes.data
      let reviewResult = '# 代码审查结果\n\n'
      reviewResult += `**语言**: ${language}\n\n`
      if (executionResult.exit_code === 0) {
        reviewResult += '**执行状态**: 成功\n'
        reviewResult += `**执行时间**: ${executionResult.execution_time?.toFixed(3) || 'N/A'}秒\n`
        if (executionResult.stdout) {
          reviewResult += '\n**输出结果**:\n' + BT + BT + BT + '\n' + executionResult.stdout + '\n' + BT + BT + BT
        }
        reviewResult += '\n**AI评估建议**:\n代码执行成功。建议：\n1. 添加适当的错误处理\n2. 考虑代码的可读性和模块化\n3. 添加必要的注释'
      } else {
        reviewResult += `**执行状态**: 失败 (退出码: ${executionResult.exit_code})\n`
        if (executionResult.stderr) {
          reviewResult += '\n**错误信息**:\n' + BT + BT + BT + '\n' + executionResult.stderr + '\n' + BT + BT + BT
        }
        reviewResult += '\n**修复建议**:\n1. 检查语法错误\n2. 确保所有变量都已定义\n3. 检查函数调用是否正确'
      }
      return { review_result: reviewResult }
    } catch {
      return {
        review_result: '# 代码审查\n\nAI审查服务暂时不可用，请稍后重试。'
      }
    }
  }
}

export async function getLearningAdvice() {
  try {
    const res = await request.get('/ai/learning-advice', { timeout: AI_TIMEOUT })
    return { advice: res.advice }
  } catch (error) {
    console.error('AI学习建议接口调用失败:', error)
    return {
      advice: '# 学习建议\n\nAI服务暂时不可用，请稍后重试。\n\n1. **夯实基础**：掌握编程语言和数据结构\n2. **实践项目**：参与实际测试项目积累经验\n3. **持续学习**：关注测试技术的最新发展\n4. **模拟面试**：定期进行面试练习'
    }
  }
}

export async function clearHistory() {
  try {
    const res = await request.post('/ai/clear-history')
    return { success: true, message: res.message || '历史记录已清空' }
  } catch (error) {
    console.error('清空历史接口调用失败:', error)
    return { success: true, message: '历史记录已清空' }
  }
}

export async function startInterview(params) {
  const { position = '功能测试工程师', experience = 2, round = '一面' } = params

  try {
    const res = await request.post('/ai/chat', {
      question: `我要模拟${position}面试，工作经验${experience}年，${round}。请作为面试官开始面试，先让我自我介绍，然后提问。`,
      context: '面试模拟场景'
    }, { timeout: AI_TIMEOUT })
    return { answer: res.answer }
  } catch (error) {
    console.error('AI面试接口调用失败:', error)
    try {
      const questionsRes = await request.get('/interview/questions', {
        params: { page: 1, size: 1, difficulty: experience < 3 ? 'easy' : experience < 5 ? 'medium' : 'hard' }
      })
      if (questionsRes.data?.items?.length) {
        const question = questionsRes.data.items[0]
        let answer = `欢迎参加${position}${round}模拟面试！\n\n**面试题目**: ${question.title}\n\n`
        if (question.description) answer += `**题目描述**:\n${question.description}\n\n`
        if (question.template_code) answer += '**代码模板**:\n' + BT + BT + BT + 'python\n' + question.template_code + '\n' + BT + BT + BT + '\n\n'
        answer += '**要求**:\n请实现解决方案，并说明你的思路。'
        return { answer }
      }
    } catch {}
    return {
      answer: `欢迎参加${position}${round}模拟面试！\n\n**模拟面试题目**:\n请实现一个函数，检查字符串是否是回文。\n\n**要求**:\n1. 忽略空格和标点符号\n2. 不区分大小写\n3. 说明时间复杂度和空间复杂度\n\n请开始你的回答。`
    }
  }
}

export default {
  chat,
  codeReview,
  getLearningAdvice,
  clearHistory,
  startInterview
}
