const fs = require('fs')
const scss = 'src/styles/global.scss'
let t = fs.readFileSync(scss, 'utf8')
const marker = '/* === TM FULL-SKIN FORCE LAYER === */'
if (t.includes(marker)) {
  console.log('already has force layer')
  process.exit(0)
}
t += `

${marker}
/* 业务页通用外壳：卡片/面板/工具条/页面容器统一 token */
.page-container,
.page-wrap,
.page-content,
.main-content,
.content-area {
  color: var(--tm-text-primary);
}

.glass-card,
.tm-card,
.stat-card,
.feature-card,
.panel,
.panel-card,
.section-card,
.list-card,
.editor-panel,
.toolbar-card {
  background: var(--tm-bg-card) !important;
  border: 1px solid var(--border-subtle) !important;
  border-radius: var(--tm-radius-base);
  color: var(--tm-text-primary);
  box-shadow: var(--tm-shadow-base);
}

.btn-primary,
.primary-btn,
.submit-btn,
.login-btn,
.cta-btn {
  background: var(--tm-gradient-brand) !important;
  border-color: transparent !important;
  color: var(--tm-button-text-color, #fff) !important;
  box-shadow: 0 4px 14px rgba(var(--tm-color-primary-rgb), 0.28) !important;
}

.btn-primary:hover,
.primary-btn:hover,
.submit-btn:hover,
.login-btn:hover,
.cta-btn:hover {
  filter: brightness(1.05);
  box-shadow: 0 8px 22px rgba(var(--tm-color-primary-rgb), 0.35) !important;
}

.el-message-box,
.el-notification,
.el-popover.el-popper,
.el-picker__popper {
  background: var(--tm-bg-card-solid, var(--tm-bg-card)) !important;
  border: 1px solid var(--border-subtle) !important;
  color: var(--tm-text-primary) !important;
}

.el-message-box__title,
.el-message-box__content,
.el-notification__title,
.el-notification__content {
  color: var(--tm-text-primary) !important;
}

.el-drawer {
  background: var(--tm-bg-card-solid, var(--tm-bg-card)) !important;
  color: var(--tm-text-primary) !important;
}

.el-drawer__header {
  color: var(--tm-text-primary) !important;
  border-bottom: 1px solid var(--border-subtle);
  margin-bottom: 0;
  padding-bottom: 16px;
}

.el-menu {
  background: transparent !important;
  border-right: none !important;
}

.el-menu-item,
.el-sub-menu__title {
  color: var(--tm-text-secondary) !important;
}

.el-menu-item:hover,
.el-sub-menu__title:hover,
.el-menu-item.is-active {
  background: rgba(var(--tm-color-primary-rgb), 0.1) !important;
  color: var(--tm-color-primary) !important;
}

.el-breadcrumb__inner,
.el-breadcrumb__item:last-child .el-breadcrumb__inner {
  color: var(--tm-text-secondary) !important;
}

.el-descriptions__label,
.el-descriptions__content {
  color: var(--tm-text-primary) !important;
}

.el-descriptions__body .el-descriptions__table.is-bordered .el-descriptions__cell {
  border-color: var(--border-subtle) !important;
  background: transparent !important;
}

.el-collapse,
.el-collapse-item__header,
.el-collapse-item__wrap {
  background: transparent !important;
  border-color: var(--border-subtle) !important;
  color: var(--tm-text-primary) !important;
}

.el-slider__runway {
  background-color: var(--border-subtle) !important;
}

.el-slider__bar {
  background-color: var(--tm-color-primary) !important;
}

.el-progress-bar__outer {
  background-color: var(--border-subtle) !important;
}

.el-progress-bar__inner {
  background-image: var(--tm-gradient-brand) !important;
}

.el-steps .el-step__title {
  color: var(--tm-text-secondary) !important;
}
.el-steps .el-step__title.is-process,
.el-steps .el-step__title.is-finish {
  color: var(--tm-color-primary) !important;
}
.el-step__icon.is-text {
  border-color: var(--tm-color-primary);
  color: var(--tm-color-primary);
}
.el-step__head.is-process .el-step__icon.is-text,
.el-step__head.is-finish .el-step__icon.is-text {
  background: var(--tm-color-primary);
  color: #fff;
  border-color: var(--tm-color-primary);
}

.el-table__empty-text,
.el-loading-text {
  color: var(--tm-text-secondary) !important;
}

a {
  color: var(--tm-color-primary);
}
a:hover {
  color: var(--tm-color-primary-light);
}
`
fs.writeFileSync(scss, t)
console.log('force layer appended, new length', t.length)
