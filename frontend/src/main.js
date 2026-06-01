import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { ElLoading } from 'element-plus'
import 'element-plus/dist/index.css'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import App from './App.vue'
import router from './router'

// 引入全局样式
import './styles/global.scss'

const app = createApp(App)

// Element Plus 组件和图标由 unplugin-vue-components 自动按需导入
// Vue/VueRouter/Pinia API 由 unplugin-auto-import 自动导入
app.directive('loading', ElLoading.directive)

app.use(createPinia())
app.use(router)

app.mount('#app')
