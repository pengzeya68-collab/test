<template>
  <div class="home-page">
    <div class="hero-card">
      <div>
        <div class="eyebrow">TestMaster 测试工程师成长平台</div>
        <h1>测试学习与实践平台</h1>
        <p>围绕学习路径、实战习题、测试工具和自动化能力，持续提升测试技能。</p>
      </div>
      <div class="hero-actions">
        <el-button type="primary" size="large" @click="$router.push('/learning-paths')">开始学习</el-button>
        <el-button size="large" @click="$router.push('/tools')">测试工具</el-button>
      </div>
    </div>

    <div class="cards">
      <el-card shadow="hover">
        <h3>系统化学习</h3>
        <p>从测试基础到自动化实践，按学习路径循序提升，并通过习题巩固知识。</p>
      </el-card>
      <el-card shadow="hover">
        <h3>测试实践工具</h3>
        <p>使用接口、场景、UI 自动化、数据与性能工具，把测试能力落到真实项目中。</p>
      </el-card>
    </div>
  </div>
</template>

<style scoped>
.home-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
}
.hero-card {
  display: flex;
  justify-content: space-between;
  gap: 24px;
  align-items: center;
  background: linear-gradient(135deg, #ffffff 0%, #f0fdf4 100%);
  border: 1px solid rgba(187, 247, 208, 0.8);
  border-radius: 20px;
  padding: 28px;
}
.eyebrow {
  color: #2f6f4f;
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}
.hero-card h1 {
  margin: 10px 0 12px;
}
.hero-card p {
  margin: 0;
  color: #475569;
  line-height: 1.7;
  max-width: 720px;
}
.hero-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}
.cards {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 20px;
}
.cards h3 {
  margin-top: 0;
}
.cards p {
  color: #475569;
  line-height: 1.7;
}
</style>
