const auth = require('../../utils/auth')
const { showToast } = require('../../utils/util')

Page({
  data: {
    activeTab: 'login',
    username: '',
    password: '',
    showPassword: false,
    loading: false,
    regUsername: '',
    regEmail: '',
    regPassword: '',
    regConfirm: ''
  },

  switchTab(e) {
    this.setData({ activeTab: e.currentTarget.dataset.tab })
  },

  onUsernameInput(e) { this.setData({ username: e.detail.value }) },
  onPasswordInput(e) { this.setData({ password: e.detail.value }) },
  onRegUsernameInput(e) { this.setData({ regUsername: e.detail.value }) },
  onRegEmailInput(e) { this.setData({ regEmail: e.detail.value }) },
  onRegPasswordInput(e) { this.setData({ regPassword: e.detail.value }) },
  onRegConfirmInput(e) { this.setData({ regConfirm: e.detail.value }) },

  togglePassword() {
    this.setData({ showPassword: !this.data.showPassword })
  },

  async handleLogin() {
    const { username, password } = this.data
    if (!username.trim()) { showToast('请输入用户名'); return }
    if (!password.trim()) { showToast('请输入密码'); return }
    if (!/[a-zA-Z]/.test(password) || !/[0-9]/.test(password)) { showToast('密码必须同时包含字母和数字'); return }

    this.setData({ loading: true })
    try {
      await auth.login(username, password)
      showToast('登录成功', 'success')
      setTimeout(() => { wx.reLaunch({ url: '/pages/index/index' }) }, 500)
    } catch (err) {
      showToast(err.message || '登录失败')
    } finally {
      this.setData({ loading: false })
    }
  },

  async handleRegister() {
    const { regUsername, regEmail, regPassword, regConfirm } = this.data
    if (!regUsername.trim()) { showToast('请输入用户名'); return }
    if (!regEmail.trim()) { showToast('请输入邮箱'); return }
    if (!regPassword.trim()) { showToast('请输入密码'); return }
    if (regPassword !== regConfirm) { showToast('两次密码不一致'); return }
    if (regPassword.length < 6) { showToast('密码至少6位'); return }

    this.setData({ loading: true })
    try {
      await auth.register({
        username: regUsername,
        email: regEmail,
        password: regPassword
      })
      showToast('注册成功', 'success')
      setTimeout(() => { wx.reLaunch({ url: '/pages/index/index' }) }, 500)
    } catch (err) {
      showToast(err.message || '注册失败')
    } finally {
      this.setData({ loading: false })
    }
  }
})
