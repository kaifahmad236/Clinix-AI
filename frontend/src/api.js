import axios from 'axios'

export const API_BASE = 'http://localhost:8000'

const api = axios.create({ baseURL: API_BASE })

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('clinixai_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('clinixai_token')
      localStorage.removeItem('clinixai_user')
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    }
    return Promise.reject(err)
  }
)

// ---- Auth ----
export const signup = (name, email, password) =>
  api.post('/api/auth/signup', { name, email, password })

export const login = (email, password) =>
  api.post('/api/auth/login', { email, password })

// ---- Chat ----
export const sendMessage = (message, session_id) =>
  api.post('/api/chat/send', { message, session_id })

export const getSessionHistory = (sessionId) =>
  api.get(`/api/chat/history/${sessionId}`)

// ---- Reports ----
export const uploadReport = (file) => {
  const formData = new FormData()
  formData.append('file', file)
  return api.post('/api/reports/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export const listReports = () => api.get('/api/reports/')
export const getReport = (id) => api.get(`/api/reports/${id}`)

// ---- Dashboard ----
export const listSessions = () => api.get('/api/dashboard/sessions')

export default api
