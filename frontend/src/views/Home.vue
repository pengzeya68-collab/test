<template>
  <div class="home-page">
    <div class="hero-card">
      <div>
        <div class="eyebrow">桌面版已恢复</div>
        <h1>UI 自动化工作台</h1>
        <p>现在可以直接进入 UI 自动化模块，管理用例、编辑步骤、保存版本并执行本地回放。</p>
      </div>
      <div class="hero-actions">
        <el-button type="primary" size="large" @click="$router.push('/ui-automation/cases')">进入 UI 自动化</el-button>
        <el-button size="large" @click="$router.push('/auto-test')">查看工作台</el-button>
      </div>
    </div>

    <div class="cards">
      <el-card shadow="hover">
        <h3>你现在可以做什么</h3>
        <p>创建 UI 用例，配置基础 URL，维护执行步骤，查看运行记录和版本历史。</p>
      </el-card>
      <el-card shadow="hover">
        <h3>当前修复策略</h3>
        <p>先恢复最关键的桌面自动化能力，避免学习类页面乱码继续影响主流程。</p>
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
