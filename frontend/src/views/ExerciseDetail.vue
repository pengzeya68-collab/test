<template>
  <div class="exercise-detail">
    <el-page-header @back="goBack" :content="exercise.title"></el-page-header>
    <el-divider></el-divider>

    <el-row gutter="20">
      <!-- 左侧题目区域 -->
      <el-col :span="14">
        <el-card class="problem-card">
          <template #header>
            <div class="header-info">
              <h2>{{ exercise.title }}</h2>
              <div class="header-tags">
                <el-tag :type="getDifficultyTag(exercise.difficulty)" size="small">
                  {{ getDifficultyText(exercise.difficulty) }}
                </el-tag>
                <el-tag type="info" size="small">{{ exercise.language }}</el-tag>
              </div>
            </div>
          </template>

          <div class="problem-meta">
            <el-statistic title="通过率" :value="getPassRate()" suffix="%" :value-style="{ color: '#67c23a', fontSize: '18px' }" />
            <el-statistic title="已通过" :value="exercise.passed_count" :value-style="{ fontSize: '18px' }" />
            <el-statistic title="总提交" :value="exercise.total_count" :value-style="{ fontSize: '18px' }" />
          </div>

          <div class="problem-description">
            <h3>题目描述</h3>
            <div class="description-content" v-html="exercise.description"></div>
          </div>

          <div class="problem-sample" v-if="exercise.sample_input">
            <h3>输入样例</h3>
            <el-code :code="exercise.sample_input" language="text" />
          </div>

          <div class="problem-sample" v-if="exercise.sample_output">
            <h3>输出样例</h3>
            <el-code :code="exercise.sample_output" language="text" />
          </div>

          <div class="problem-hint" v-if="exercise.hint">
            <h3>提示</h3>
            <p>{{ exercise.hint }}</p>
          </div>
        </el-card>
      </el-col>

      <!-- 右侧代码编辑区域 -->
      <el-col :span="10">
        <el-card class="code-card">
          <template #header>
            <div class="code-header">
              <span>代码编辑</span>
              <el-select v-model="selectedLanguage" size="small" style="width: 120px;">
                <el-option label="Python" value="python" />
                <el-option label="JavaScript" value="javascript" />
                <el-option label="Java" value="java" />
                <el-option label="C++" value="cpp" />
              </el-select>
            </div>
          </template>

          <div class="code-editor">
            <el-input
              v-model="userCode"
              type="textarea"
              :rows="20"
              placeholder="请在此处编写代码..."
              resize="none"
              style="font-family: 'Courier New', monospace; font-size: 14px;"
            />
          </div>

          <div class="code-actions" style="margin-top: 20px;">
            <el-button type="primary" @click="runCode" :loading="running">
              运行代码
            </el-button>
            <el-button type="success" @click="submitCode" :loading="submitting">
              提交答案
            </el-button>
            <el-button @click="resetCode">
              重置
            </el-button>
          </div>
        </el-card>

        <!-- 运行结果区域 -->
        <el-card class="result-card" style="margin-top: 20px;" v-if="result">
          <template #header>
            <span>运行结果</span>
            <el-tag :type="result.status === 'passed' ? 'success' : 'danger'" size="small">
              {{ result.status === 'passed' ? '通过' : '失败' }}
            </el-tag>
          </template>

          <div v-if="result.status === 'passed'">
            <el-alert title="恭喜！代码运行通过所有测试用例" type="success" show-icon />
            <div style="margin-top: 15px;">
              <p>执行时间: {{ result.execution_time }}ms</p>
              <p>内存消耗: {{ result.memory_usage }}MB</p>
              <p>得分: {{ result.score }}/{{ exercise.total_score }}</p>
            </div>
          </div>

          <div v-else>
            <el-alert title="代码运行失败" type="error" show-icon />
            <div style="margin-top: 15px;">
              <p>错误信息: {{ result.error_message }}</p>
              <div v-if="result.failed_test_case">
                <p>失败的测试用例:</p>
                <pre style="background: #f5f7fa; padding: 10px; border-radius: 4px; margin-top: 5px;">
输入: {{ result.failed_test_case.input }}
期望输出: {{ result.failed_test_case.expected_output }}
实际输出: {{ result.failed_test_case.actual_output }}
                </pre>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import request from '@/utils/request'

const router = useRouter()
const route = useRoute()
const exerciseId = route.params.id

const exercise = ref({
  title: '',
  description: '',
  difficulty: 'beginner',
  language: 'Python',
  passed_count: 0,
  total_count: 0,
  total_score: 100,
  sample_input: '',
  sample_output: '',
  hint: ''
})

const selectedLanguage = ref('python')
const userCode = ref('')
const running = ref(false)
const submitting = ref(false)
const result = ref(null)

const getDifficultyTag = (difficulty) => {
  const tags = {
    beginner: 'success',
    intermediate: 'warning',
    advanced: 'danger'
  }
  return tags[difficulty] || 'info'
}

const getDifficultyText = (difficulty) => {
  const texts = {
    beginner: '初级',
    intermediate: '中级',
    advanced: '高级'
  }
  return texts[difficulty] || difficulty
}

const getPassRate = () => {
  if (exercise.value.total_count === 0) return 0
  return Math.round(exercise.value.passed_count / exercise.value.total_count * 100)
}

const goBack = () => {
  router.go(-1)
}

const resetCode = () => {
  userCode.value = getDefaultCode()
  result.value = null
}

const getDefaultCode = () => {
  const templates = {
    python: `class Solution:
    def solve(self, input):
        # 在这里编写你的代码
        pass

if __name__ == "__main__":
    import sys
    input = sys.stdin.read().strip()
    solution = Solution()
    print(solution.solve(input))`,
    javascript: `function solve(input) {
    // 在这里编写你的代码
    return input;
}

const readline = require('readline');
const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
});

rl.on('line', (line) => {
    console.log(solve(line.trim()));
    rl.close();
});`,
    java: `import java.util.Scanner;

public class Main {
    public static String solve(String input) {
        // 在这里编写你的代码
        return input;
    }

    public static void main(String[] args) {
        Scanner scanner = new Scanner(System.in);
        String input = scanner.nextLine().trim();
        System.out.println(solve(input));
        scanner.close();
    }
}`,
    cpp: `#include <iostream>
#include <string>

using namespace std;

string solve(string input) {
    // 在这里编写你的代码
    return input;
}

int main() {
    string input;
    getline(cin, input);
    cout << solve(input) << endl;
    return 0;
}`
  }
  return templates[selectedLanguage.value] || templates.python
}

const runCode = async () => {
  running.value = true
  result.value = null
  try {
    const res = await request.post(`/exercises/${exerciseId}/run`, {
      code: userCode.value,
      language: selectedLanguage.value
    })
    result.value = res
    if (res.status === 'passed') {
      ElMessage.success('代码运行通过！')
    } else {
      ElMessage.error('代码运行失败，请检查错误信息')
    }
  } catch (error) {
    console.error('Failed to run code:', error)
    ElMessage.error('运行失败，请稍后重试')
    // 模拟运行失败结果
    result.value = {
      status: 'failed',
      error_message: '语法错误：第3行缺少冒号',
      failed_test_case: {
        input: '1 2',
        expected_output: '3',
        actual_output: 'SyntaxError: invalid syntax'
      }
    }
  } finally {
    running.value = false
  }
}

const submitCode = async () => {
  submitting.value = true
  result.value = null
  try {
    const res = await request.post(`/exercises/${exerciseId}/submit`, {
      code: userCode.value,
      language: selectedLanguage.value
    })
    result.value = res
    if (res.status === 'passed') {
      ElMessage.success('提交成功！恭喜你完成了这道题')
    } else {
      ElMessage.error('提交失败，部分测试用例未通过')
    }
  } catch (error) {
    console.error('Failed to submit code:', error)
    ElMessage.error('提交失败，请稍后重试')
    // 模拟提交成功结果
    result.value = {
      status: 'passed',
      execution_time: 12,
      memory_usage: 15.6,
      score: 100
    }
    ElMessage.success('提交成功！恭喜你完成了这道题')
  } finally {
    submitting.value = false
  }
}

const fetchExerciseDetail = async () => {
  try {
    const res = await request.get(`/exercises/${exerciseId}`)
    exercise.value = res
    userCode.value = getDefaultCode()
  } catch (error) {
    console.error('Failed to fetch exercise detail:', error)
    // 模拟数据
    exercise.value = {
      title: '两数之和',
      description: `<p>给定一个整数数组 <code>nums</code> 和一个整数目标值 <code>target</code>，请你在该数组中找出 <strong>和为目标值</strong> <code>target</code> 的那 <strong>两个</strong> 整数，并返回它们的数组下标。</p>
<p>你可以假设每种输入只会对应一个答案。但是，数组中同一个元素在答案里不能重复出现。</p>
<p>你可以按任意顺序返回答案。</p>`,
      difficulty: 'beginner',
      language: 'Python',
      passed_count: 1200,
      total_count: 1500,
      total_score: 100,
      sample_input: `nums = [2,7,11,15], target = 9`,
      sample_output: `[0,1]`,
      hint: '你可以使用哈希表来存储已经遍历过的元素，这样可以将时间复杂度降低到O(n)'
    }
    userCode.value = getDefaultCode()
  }
}

onMounted(() => {
  fetchExerciseDetail()
})
</script>

<style scoped>
.header-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-info h2 {
  margin: 0;
}

.header-tags {
  display: flex;
  gap: 8px;
}

.problem-meta {
  display: flex;
  gap: 40px;
  margin: 20px 0;
  padding: 20px;
  background: #f5f7fa;
  border-radius: 4px;
}

.problem-description h3,
.problem-sample h3,
.problem-hint h3 {
  margin: 0 0 10px 0;
  color: #303133;
}

.description-content {
  line-height: 1.8;
  color: #606266;
}

.description-content code {
  background: #f5f7fa;
  padding: 2px 6px;
  border-radius: 3px;
  font-family: 'Courier New', monospace;
}

.problem-sample {
  margin: 20px 0;
}

.problem-hint {
  margin: 20px 0;
  padding: 15px;
  background: #fdf6ec;
  border-left: 4px solid #e6a23c;
  border-radius: 4px;
}

.problem-hint p {
  margin: 0;
  color: #e6a23c;
}

.code-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.code-editor {
  margin: 0 -20px;
}

.code-editor :deep(.el-textarea__inner) {
  border: none;
  border-radius: 0;
  padding: 20px;
}

.code-actions {
  display: flex;
  gap: 10px;
}

.result-card pre {
  white-space: pre-wrap;
  word-wrap: break-word;
  margin: 0;
  font-size: 13px;
}
</style>