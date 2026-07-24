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
        resolvers: [ElementPlusResolver({ importStyle: 'css' })],
        imports: ['vue', 'vue-router', 'pinia'],
        dts: false,
      }),
      Components({
        resolvers: [ElementPlusResolver({ importStyle: 'css' })],
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
    build: {
      rollupOptions: {
        output: {
          // Keep large, route-specific libraries out of the desktop dashboard
          // and web landing bundle. They are loaded only when their editor or
          // analysis workspace is opened.
          manualChunks(id) {
            if (!id.includes('node_modules')) return undefined
            if (id.includes('@codemirror')) return 'vendor-codemirror'
            if (id.includes('echarts') || id.includes('zrender')) return 'vendor-charts'
            if (id.includes('xlsx') || id.includes('papaparse')) return 'vendor-data'
            if (id.includes('marked') || id.includes('dompurify')) return 'vendor-markdown'
            if (id.includes('vuedraggable') || id.includes('sortablejs')) return 'vendor-dragdrop'
            return undefined
          },
        },
      },
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
  }
})
