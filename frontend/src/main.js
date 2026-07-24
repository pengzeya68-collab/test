import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { ElLoading } from 'element-plus/es/components/loading/index'
import 'element-plus/es/components/loading/style/css'
// Service APIs are invoked from JavaScript, so component auto-import cannot
// reliably include their styles in the desktop renderer bundle.
import 'element-plus/es/components/message/style/css'
import 'element-plus/es/components/message-box/style/css'
import 'element-plus/es/components/notification/style/css'
import App from '@app-root'
import router from '@app-router'
import permissionDirective from './directives/permission'
import { registerDirectives } from './directives'
import { applyTheme, loadSavedTheme } from './utils/ThemeConfig'

// 引入全局样式
import './styles/global.scss'

// Apply the saved palette before Vue renders to avoid a visible theme flash.
applyTheme(loadSavedTheme())

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
