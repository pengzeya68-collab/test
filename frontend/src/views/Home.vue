<template>
  <div class="home">
    <el-row justify="center">
      <el-col :span="16">
        <div class="hero">
          <h1>🚀 欢迎来到 TestMaster</h1>
          <p>专业的在线编程学习平台，助你快速提升编程技能</p>
          <el-button type="primary" size="large" @click="$router.push('/learning-paths')" style="margin-top: 20px;">
            开始学习
          </el-button>
        </div>
      </el-col>
    </el-row>

    <el-row gutter="20" justify="center" style="margin-top: 60px;">
      <el-col :span="5">
        <el-card class="feature-card">
          <template #header>
            <span>📚 结构化学习路径</span>
          </template>
          <p>精心设计的学习路径，从入门到精通，循序渐进</p>
        </el-card>
      </el-col>
      <el-col :span="5">
        <el-card class="feature-card">
          <template #header>
            <span>💪 海量编程练习</span>
          </template>
          <p>丰富的编程题库，覆盖各种难度和编程语言</p>
        </el-card>
      </el-col>
      <el-col :span="5">
        <el-card class="feature-card">
          <template #header>
            <span>📊 实时进度跟踪</span>
          </template>
          <p>记录你的学习进度，实时反馈学习效果</p>
        </el-card>
      </el-col>
      <el-col :span="5">
        <el-card class="feature-card">
          <template #header>
            <span>🏆 实践出真知</span>
          </template>
          <p>通过实战练习，真正掌握编程技能</p>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
</script>

<style scoped>
.hero {
  text-align: center;
  padding: 60px 0;
}

.hero h1 {
  font-size: 48px;
  color: #2385bb;
  margin-bottom: 20px;
}

.hero p {
  font-size: 20px;
  color: #666;
}

.feature-card {
  height: 180px;
  text-align: center;
}

.feature-card :deep(.el-card__header) {
  font-weight: bold;
  font-size: 18px;
}

.feature-card p {
  color: #666;
  line-height: 1.8;
}
</style>
