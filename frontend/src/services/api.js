import axios from 'axios'

const api = axios.create({
  baseURL: '/blackrock/challenge/v1',
  timeout: 60000,
  headers: { 'Content-Type': 'application/json' },
})

// Retry interceptor — retry 3 times on network failure
api.interceptors.response.use(null, async (error) => {
  const config = error.config
  if (!config) return Promise.reject(error)
  config._retryCount = (config._retryCount || 0) + 1
  if (config._retryCount <= 3 && (!error.response || error.response.status >= 500)) {
    await new Promise((r) => setTimeout(r, 1000 * config._retryCount))
    return api(config)
  }
  return Promise.reject(error)
})

export const transactionAPI = {
  parse: (expenses) => api.post('/transactions:parse', { expenses }),
  validate: (data) => api.post('/transactions:validator', data),
  filter: (data) => api.post('/transactions:filter', data),
}

export const returnsAPI = {
  nps: (data) => api.post('/returns:nps', data),
  index: (data) => api.post('/returns:index', data),
}

export const performanceAPI = {
  get: () => api.get('/performance'),
}

export default api
