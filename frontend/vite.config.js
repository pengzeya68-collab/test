import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig(({ mode }) => {
  // 根据当前工作目录中的 `mode` 加载 .env 文件
  // 设置第三个参数为 '' 来加载所有环境变量，而不管是否有 `VITE_` 前缀。
  const env = loadEnv(mode, process.cwd() + '/frontend', '')

  return {
    plugins: [vue()],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src')
      }
    },
    server: {
      host: '0.0.0.0',
      port: 5173,
      strictPort: true,
      proxy: {
        // 代理 /api 到 Flask 后端
        '/api': {
          target: env.VITE_API_BASE_URL || 'http://127.0.0.1:5000',
          changeOrigin: true,
          secure: false,
          ws: false,
          // 可选：重写路径，如果后端的路由不包含 /api
          // rewrite: (path) => path.replace(/^\/api/, '')
        },
        // 代理 /auto-test 到 FastAPI 后端
        '/auto-test': {
          target: env.VITE_AUTO_TEST_API_BASE_URL || 'http://127.0.0.1:5002',
          changeOrigin: true,
          secure: false,
          ws: false
        }
      }
    }
  }
})
