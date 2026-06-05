import axios from 'axios'
import { getToken, removeToken } from '@/utils/storage'
import { ElMessage } from 'element-plus'

const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1',
  timeout: 120000,
})

// 请求拦截器：自动带 token
request.interceptors.request.use((config) => {
  const token = getToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 响应拦截器：错误统一处理
request.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const status = error.response?.status
    const detail = error.response?.data?.detail

    if (status === 401) {
      removeToken()
      window.location.href = '/login'
      ElMessage.error('登录已过期，请重新登录')
    } else if (detail) {
      ElMessage.error(detail)
    } else {
      ElMessage.error('网络错误，请稍后重试')
    }

    return Promise.reject(error)
  },
)

export default request
