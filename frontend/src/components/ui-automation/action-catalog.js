import { Link, Mouse, EditPen, Position, Check, CircleCheck, Timer, Refresh, ArrowLeft, Aim, DataLine } from '@element-plus/icons-vue'

export const ACTION_GROUPS = [
  { name: '页面导航', actions: [
    { type: 'goto', label: '打开网页', icon: Link, input: 'url' },
    { type: 'reload', label: '刷新页面', icon: Refresh },
    { type: 'go_back', label: '返回上一页', icon: ArrowLeft },
    { type: 'switch_page', label: '切换到新页面', icon: Link, input: 'index' },
    { type: 'close_page', label: '关闭当前页面', icon: Refresh },
    { type: 'set_viewport', label: '设置浏览器尺寸', icon: Aim, input: 'viewport' },
  ]},
  { name: '页面操作', actions: [
    { type: 'click', label: '点击元素', icon: Mouse, locator: true },
    { type: 'double_click', label: '双击元素', icon: Mouse, locator: true },
    { type: 'fill', label: '输入内容', icon: EditPen, locator: true, input: 'value' },
    { type: 'type', label: '模拟逐字输入', icon: EditPen, locator: true, input: 'value' },
    { type: 'clear', label: '清空输入', icon: EditPen, locator: true },
    { type: 'press', label: '按下键盘', icon: Position, locator: true, input: 'key' },
    { type: 'select_option', label: '选择下拉项', icon: Check, locator: true, input: 'value' },
    { type: 'upload_file', label: '上传文件', icon: EditPen, locator: true, input: 'files' },
    { type: 'download', label: '下载并校验文件', icon: DataLine, locator: true, input: 'downloadOptions' },
    { type: 'check', label: '勾选', icon: Check, locator: true },
    { type: 'uncheck', label: '取消勾选', icon: Check, locator: true },
    { type: 'hover', label: '鼠标悬停', icon: Mouse, locator: true },
    { type: 'focus', label: '聚焦元素', icon: Aim, locator: true },
    { type: 'scroll_into_view', label: '滚动到元素', icon: Aim, locator: true },
    { type: 'drag_and_drop', label: '拖拽到目标元素', icon: Mouse, locator: true, input: 'targetLocator' },
    { type: 'accept_dialog', label: '确认下一个弹窗', icon: Check },
    { type: 'dismiss_dialog', label: '取消下一个弹窗', icon: Check },
  ]},
  { name: '检查结果', actions: [
    { type: 'assert_visible', label: '检查元素可见', icon: CircleCheck, locator: true },
    { type: 'assert_hidden', label: '检查元素隐藏', icon: CircleCheck, locator: true },
    { type: 'assert_enabled', label: '检查元素可用', icon: CircleCheck, locator: true },
    { type: 'assert_disabled', label: '检查元素禁用', icon: CircleCheck, locator: true },
    { type: 'assert_editable', label: '检查元素可编辑', icon: CircleCheck, locator: true },
    { type: 'assert_checked', label: '检查元素已勾选', icon: CircleCheck, locator: true },
    { type: 'assert_text_equals', label: '检查文字相等', icon: CircleCheck, locator: true, input: 'expected' },
    { type: 'assert_text_contains', label: '检查包含文字', icon: CircleCheck, locator: true, input: 'expected' },
    { type: 'assert_text_matches', label: '检查文字正则匹配', icon: CircleCheck, locator: true, input: 'expected' },
    { type: 'assert_value', label: '检查输入值', icon: CircleCheck, locator: true, input: 'expected' },
    { type: 'assert_element_count', label: '检查元素数量', icon: CircleCheck, locator: true, input: 'expected' },
    { type: 'assert_url', label: '检查页面地址', icon: CircleCheck, input: 'expected' },
    { type: 'assert_title', label: '检查页面标题', icon: CircleCheck, input: 'expected' },
  ]},
  { name: '等待', actions: [
    { type: 'wait_for_element', label: '等待元素出现', icon: Timer, locator: true },
    { type: 'wait_for_load_state', label: '等待页面加载', icon: Timer, input: 'state' },
    { type: 'wait_for_url', label: '等待页面地址', icon: Timer, input: 'url' },
    { type: 'wait_for_timeout', label: '固定等待', icon: Timer, input: 'ms' },
  ]},
  { name: '数据', actions: [
    { type: 'set_variable', label: '设置变量', icon: DataLine, input: 'variable' },
    { type: 'extract_text', label: '提取元素文字', icon: DataLine, locator: true, input: 'name' },
    { type: 'extract_value', label: '提取输入值', icon: DataLine, locator: true, input: 'name' },
    { type: 'extract_url', label: '提取当前地址', icon: DataLine, input: 'name' },
  ]},
]

export const ACTIONS = ACTION_GROUPS.flatMap(group => group.actions)
export const ACTION_MAP = Object.fromEntries(ACTIONS.map(action => [action.type, action]))
export const actionLabel = type => ACTION_MAP[type]?.label || type
export const needsLocator = type => !!ACTION_MAP[type]?.locator
export const inputKind = type => ACTION_MAP[type]?.input || null






