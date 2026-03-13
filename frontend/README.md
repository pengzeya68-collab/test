# TestMaster 前端项目

## 🚀 项目介绍
TestMaster 在线编程学习平台前端，基于 Vue 3 + Element Plus 开发。

## 📦 技术栈
- **框架**: Vue 3
- **构建工具**: Vite
- **UI 组件库**: Element Plus
- **路由**: Vue Router
- **状态管理**: Pinia
- **HTTP 客户端**: Axios

## 🛠️ 安装和运行

### 1. 安装依赖
```bash
cd frontend
npm install
```

### 2. 启动开发服务器
```bash
npm run dev
```
前端服务将运行在 `http://localhost:3000`

### 3. 生产构建
```bash
npm run build
```

## 📁 项目结构
```
frontend/
├── src/
│   ├── views/          # 页面组件
│   ├── router/         # 路由配置
│   ├── utils/          # 工具函数
│   ├── App.vue         # 根组件
│   └── main.js         # 入口文件
├── index.html          # HTML 模板
├── vite.config.js      # Vite 配置
└── package.json        # 依赖配置
```

## 🔧 配置说明
后端 API 代理配置在 `vite.config.js` 中，默认代理到 `http://localhost:5000`，如需修改请调整 proxy 配置。

## 📋 页面功能
- **首页**: 平台介绍和功能展示
- **登录/注册**: 用户认证
- **学习路径**: 浏览和查看学习路径
- **练习题库**: 浏览和完成编程练习
- **个人中心**: 用户信息和进度管理（开发中）
