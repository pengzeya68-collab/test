# TestMaster Workspace

TestMaster 辅助前端项目（React + Vite），用于实验性功能或独立模块开发。

## 说明

- 本项目不是主前端，主前端位于 `../frontend`（Vue 3 + Vite）。
- 如需开发主功能，请优先使用 `frontend` 目录。

## 环境要求

- Node.js >= 18
- npm >= 9

## 安装依赖

```bash
cd workspace
npm install
```

## 开发环境启动

```bash
npm run dev
```

开发服务器默认运行在 http://localhost:5174，代理后端 API 到 http://localhost:5001。

## 构建

```bash
npm run build
```

## 代码检查

```bash
npm run lint
```
