import { createApp } from 'vue'
import { createPinia } from 'pinia'
import {
  ElAlert,
  ElAutocomplete,
  ElAvatar,
  ElBadge,
  ElButton,
  ElButtonGroup,
  ElCard,
  ElCheckbox,
  ElCheckboxGroup,
  ElCol,
  ElCollapse,
  ElCollapseItem,
  ElConfigProvider,
  ElDatePicker,
  ElDescriptions,
  ElDescriptionsItem,
  ElDialog,
  ElDivider,
  ElDrawer,
  ElDropdown,
  ElDropdownItem,
  ElDropdownMenu,
  ElEmpty,
  ElForm,
  ElFormItem,
  ElHeader,
  ElIcon,
  ElInput,
  ElInputNumber,
  ElLink,
  ElLoading,
  ElOption,
  ElPagination,
  ElPopconfirm,
  ElPopover,
  ElProgress,
  ElRadio,
  ElRadioButton,
  ElRadioGroup,
  ElRate,
  ElResult,
  ElRow,
  ElSelect,
  ElSkeleton,
  ElSlider,
  ElSwitch,
  ElTable,
  ElTableColumn,
  ElTabPane,
  ElTabs,
  ElTag,
  ElTimeline,
  ElTimelineItem,
  ElTooltip,
  ElTransfer,
  ElTree,
  ElUpload
} from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
// import ElTableDraggable from 'el-table-draggable'
import App from './App.vue'
import router from './router'

// 引入全局样式
import './styles/global.scss'

const app = createApp(App)
const elementPlusComponents = [
  ElAlert,
  ElAutocomplete,
  ElAvatar,
  ElBadge,
  ElButton,
  ElButtonGroup,
  ElCard,
  ElCheckbox,
  ElCheckboxGroup,
  ElCol,
  ElCollapse,
  ElCollapseItem,
  ElConfigProvider,
  ElDatePicker,
  ElDescriptions,
  ElDescriptionsItem,
  ElDialog,
  ElDivider,
  ElDrawer,
  ElDropdown,
  ElDropdownItem,
  ElDropdownMenu,
  ElEmpty,
  ElForm,
  ElFormItem,
  ElHeader,
  ElIcon,
  ElInput,
  ElInputNumber,
  ElLink,
  ElOption,
  ElPagination,
  ElPopconfirm,
  ElPopover,
  ElProgress,
  ElRadio,
  ElRadioButton,
  ElRadioGroup,
  ElRate,
  ElResult,
  ElRow,
  ElSelect,
  ElSkeleton,
  ElSlider,
  ElSwitch,
  ElTable,
  ElTableColumn,
  ElTabPane,
  ElTabs,
  ElTag,
  ElTimeline,
  ElTimelineItem,
  ElTooltip,
  ElTransfer,
  ElTree,
  ElUpload
]

for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

for (const component of elementPlusComponents) {
  app.use(component)
}

app.directive('loading', ElLoading.directive)

// Register el-table-draggable component (it's not a plugin)
// app.component('ElTableDraggable', ElTableDraggable)

app.use(createPinia())
app.use(router)

app.mount('#app')
