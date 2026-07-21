import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'
import removeConsole from 'vite-plugin-remove-console'
import path from 'path'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  // A normal web build must never depend on a leaked shell environment value.
  const isDesktopBuild = mode === 'desktop'
  const unifiedBackend =
    env.VITE_FASTAPI_BASE_URL ||
    env.VITE_API_BASE_URL ||
    'http://127.0.0.1:5001'

  return {
    base: isDesktopBuild ? './' : '/',
    plugins: [
      vue(),
      AutoImport({
        resolvers: [ElementPlusResolver()],
        imports: ['vue', 'vue-router', 'pinia'],
        dts: false,
      }),
      Components({
        resolvers: [ElementPlusResolver()],
        dts: false,
      }),
      removeConsole({ excludes: ['error', 'warn'] }),
    ],
    css: {
      preprocessorOptions: {
        scss: {
          api: 'modern-compiler'
        }
      }
    },
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
        '@app-root': path.resolve(__dirname, isDesktopBuild ? './src/DesktopApp.vue' : './src/App.vue'),
        '@app-router': path.resolve(__dirname, isDesktopBuild ? './src/router/desktop.js' : './src/router/index.js')
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
    },
    build: {
      rollupOptions: {
        output: {
          manualChunks(id) {
            // 仅对真正独立且体积较大的库做显式分包，避免循环 chunk 依赖
            if (id.includes('node_modules/element-plus')) return 'element-plus'
            if (id.includes('node_modules/echarts')) return 'echarts'
            if (id.includes('node_modules/xlsx')) return 'xlsx'
            if (id.includes('node_modules/papaparse')) return 'papaparse'
            if (id.includes('node_modules/vuedraggable') || id.includes('node_modules/sortablejs')) return 'draggable'
          }
        }
      }
    }
  }
})
