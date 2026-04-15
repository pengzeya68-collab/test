import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd() + '/frontend', '')
  const unifiedBackend =
    env.VITE_FASTAPI_BASE_URL ||
    env.VITE_API_BASE_URL ||
    'http://127.0.0.1:5001'

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
        '/api': {
          target: unifiedBackend,
          changeOrigin: true,
          secure: false,
          ws: false,
          rewrite: (path) => {
            if (path.startsWith('/api/auto-test')) {
              return path;
            }
            if (path.startsWith('/api/admin')) {
              return path.replace('/api/admin', '/api/v1/admin');
            }
            return path;
          }
        },
        '/fastapi': {
          target: unifiedBackend,
          changeOrigin: true,
          secure: false,
          ws: false,
          rewrite: (requestPath) => requestPath.replace(/^\/fastapi/, '')
        },
        '/reports': {
          target: unifiedBackend,
          changeOrigin: true,
          secure: false,
          ws: false
        }
      }
    }
  }
})
