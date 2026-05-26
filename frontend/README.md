# TestMaster Frontend

TestMaster 前端项目，基于 Vue 3 + Vite + Element Plus 构建。

## 环境要求

- Node.js >= 18
- npm >= 9

## 安装依赖

```bash
cd frontend
npm install
```

## 开发环境启动

```bash
npm run dev
```

开发服务器默认运行在 http://localhost:5173，代理后端 API 到 http://localhost:5001。

## 构建生产包

```bash
npm run build
```

## 代码检查

```bash
npm run lint
```

## 项目结构

```
frontend/
├── public/          # 静态资源
├── src/
│   ├── api/         # API 接口封装
│   ├── components/  # 公共组件
│   ├── router/      # 路由配置
│   ├── stores/      # Pinia 状态管理
│   ├── utils/       # 工具函数
│   ├── views/       # 页面视图
│   ├── App.vue
│   └── main.js
├── index.html
├── package.json
├── vite.config.js
└── tailwind.config.js
```

## 代理配置

开发环境下，Vite 代理规则如下：
- `/api/v1` -> `http://localhost:5001/api/v1`
- `/api` -> `http://localhost:5001/api`

生产环境请通过 Nginx 或后端 CORS 配置跨域。

## 环境变量

可在 `frontend` 目录下创建 `.env.local` 覆盖默认配置：

```
VITE_API_BASE_URL=/api/v1
```
