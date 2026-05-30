const api = require('../../utils/api')
const auth = require('../../utils/auth')
const { showToast } = require('../../utils/util')

Page({
  data: { oldPassword: '', newPassword: '', confirmPassword: '', loading: false },

  onLoad() {
    if (!auth.isLoggedIn()) {
      wx.reLaunch({ url: '/pages/login/login' })
      return
    }
  },

  onOldPwdInput(e) { this.setData({ oldPassword: e.detail.value }) },
  onNewPwdInput(e) { this.setData({ newPassword: e.detail.value }) },
  onConfirmInput(e) { this.setData({ confirmPassword: e.detail.value }) },

  async changePassword() {
    const { oldPassword, newPassword, confirmPassword } = this.data
    if (!oldPassword) { showToast('请输入当前密码'); return }
    if (!newPassword) { showToast('请输入新密码'); return }
    if (newPassword.length < 6) { showToast('新密码至少6位'); return }
    if (newPassword !== confirmPassword) { showToast('两次密码不一致'); return }

    this.setData({ loading: true })
    try {
      await api.post('/api/v1/auth/change-password', {
        old_password: oldPassword,
        new_password: newPassword
      })
      showToast('密码修改成功', 'success')
      setTimeout(() => wx.navigateBack(), 1500)
    } catch (err) {
      showToast(err.message || '修改失败')
    } finally {
      this.setData({ loading: false })
    }
  }
})
