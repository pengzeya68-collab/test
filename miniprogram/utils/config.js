const BASE_URL = 'https://34.150.26.84'

module.exports = {
  BASE_URL,
  API_PREFIX: '/api/v1',
  getApiUrl(path) {
    return `${BASE_URL}${path}`
  }
}
