import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { ElLoading } from 'element-plus'
import 'element-plus/dist/index.css'
import App from './App.vue'
import router from './router'
import permissionDirective from './directives/permission'
import { registerDirectives } from './directives'

// 引入全局样式
import './styles/global.scss'

const app = createApp(App)

// Element Plus 组件和图标由 unplugin-vue-components 自动按需导入
// Vue/VueRouter/Pinia API 由 unplugin-auto-import 自动导入
app.directive('loading', ElLoading.directive)
// RBAC 权限指令：v-permission="'case:create'" / v-permission.any=[...] / v-permission.all=[...]
app.directive('permission', permissionDirective)

// 2026 高级微交互指令：v-magnetic / v-spotlight / v-fade-in / v-count-up / v-ripple
registerDirectives(app)

app.use(createPinia())
app.use(router)

app.mount('#app')
