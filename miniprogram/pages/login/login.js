const api = require('../../utils/api')
const auth = require('../../utils/auth')

Page({
  data: {
    mode: 'login',
    tab: 'login',
    username: '',
    password: '',
    regUsername: '',
    regEmail: '',
    regPassword: '',
    regConfirmPassword: '',
    serverUrl: '',
    baseUrl: '',
    loading: false,
    wechatLoading: false
  },

  onLoad(options) {
    const baseUrl = auth.getBaseUrl()
    this.setData({ baseUrl })
    if (options.mode === 'setup') {
      this.setData({ mode: 'setup', serverUrl: baseUrl })
    }
  },

  switchTab(e) {
    this.setData({ tab: e.currentTarget.dataset.tab })
  },

  onInput(e) {
    const field = e.currentTarget.dataset.field
    this.setData({ [field]: e.detail.value })
  },

  goSetup() {
    this.setData({ mode: 'setup', serverUrl: auth.getBaseUrl() })
  },

  async handleLogin() {
    const { username, password } = this.data
    if (!username || !password) {
      wx.showToast({ title: '请填写用户名和密码', icon: 'none' })
      return
    }

    this.setData({ loading: true })
    try {
      const res = await api.post('/auth/login', {
        username: username,
        password: password
      }, { skipAuth: true })

      auth.setToken(res.access_token, res.refresh_token)
      if (res.user) {
        auth.setUserInfo(res.user)
      }

      wx.showToast({ title: '登录成功', icon: 'success' })
      setTimeout(() => {
        wx.switchTab({ url: '/pages/index/index' })
      }, 500)
    } catch (err) {
      wx.showToast({ title: err.message || '登录失败', icon: 'none' })
    } finally {
      this.setData({ loading: false })
    }
  },

  async handleRegister() {
    const { regUsername, regEmail, regPassword, regConfirmPassword } = this.data
    if (!regUsername || !regEmail || !regPassword) {
      wx.showToast({ title: '请填写完整信息', icon: 'none' })
      return
    }
    if (regPassword !== regConfirmPassword) {
      wx.showToast({ title: '两次密码不一致', icon: 'none' })
      return
    }

    this.setData({ loading: true })
    try {
      const res = await api.post('/auth/register', {
        username: regUsername,
        email: regEmail,
        password: regPassword
      }, { skipAuth: true })

      if (res.access_token) {
        auth.setToken(res.access_token, res.refresh_token)
        wx.showToast({ title: '注册成功', icon: 'success' })
        setTimeout(() => {
          wx.switchTab({ url: '/pages/index/index' })
        }, 500)
      } else {
        wx.showToast({ title: '注册成功，请登录', icon: 'success' })
        this.setData({ tab: 'login', username: regUsername })
      }
    } catch (err) {
      wx.showToast({ title: err.message || '注册失败', icon: 'none' })
    } finally {
      this.setData({ loading: false })
    }
  },

  handleSaveServer() {
    let url = this.data.serverUrl.trim()
    if (!url) {
      wx.showToast({ title: '请输入服务器地址', icon: 'none' })
      return
    }
    if (url.endsWith('/')) {
      url = url.slice(0, -1)
    }
    if (!url.startsWith('http')) {
      url = 'https://' + url
    }
    auth.setBaseUrl(url)
    this.setData({ baseUrl: url, mode: 'login' })
    wx.showToast({ title: '保存成功', icon: 'success' })
  },

  async handleWechatLogin() {
    this.setData({ wechatLoading: true })
    try {
      const loginRes = await new Promise((resolve, reject) => {
        wx.login({
          success: resolve,
          fail: reject
        })
      })

      if (!loginRes.code) {
        wx.showToast({ title: '获取微信授权失败', icon: 'none' })
        return
      }

      const res = await api.post('/auth/wechat-login', {
        code: loginRes.code
      }, { skipAuth: true })

      auth.setToken(res.access_token, res.refresh_token)
      if (res.user) {
        auth.setUserInfo(res.user)
      }

      wx.showToast({ title: '登录成功', icon: 'success' })
      setTimeout(() => {
        wx.switchTab({ url: '/pages/index/index' })
      }, 500)
    } catch (err) {
      wx.showToast({ title: err.message || '微信登录失败', icon: 'none' })
    } finally {
      this.setData({ wechatLoading: false })
    }
  }
})
