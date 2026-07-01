import axios from 'axios'
import { ElMessage } from 'element-plus'

// Axios 实例，统一 baseURL 与拦截器
const request = axios.create({
  baseURL: '/api',
  timeout: 300000 // 视频检测可能较慢，给足超时时间
})

// 响应拦截器：统一处理后端 { code, msg, data } 结构
request.interceptors.response.use(
  (response) => {
    const res = response.data
    if (res && typeof res.code !== 'undefined') {
      if (res.code === 0) {
        return res
      }
      ElMessage.error(res.msg || '请求失败')
      return Promise.reject(new Error(res.msg || '请求失败'))
    }
    return res
  },
  (error) => {
    const msg =
      error.code === 'ECONNABORTED'
        ? '请求超时，检测可能耗时较长，请稍候重试'
        : error.message || '网络异常，请检查后端服务是否启动'
    ElMessage.error(msg)
    return Promise.reject(error)
  }
)

// ---------------------------------------------------------------------------
// 接口封装
// ---------------------------------------------------------------------------
export const getDashboard = () => request.get('/dashboard')

export const detectImage = (formData) =>
  request.post('/detect/image', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })

export const detectVideo = (formData) =>
  request.post('/detect/video', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })

export const detectFrame = (data) => request.post('/detect/frame', data)

export const getRecords = (params) => request.get('/records', { params })

export const deleteRecord = (id) => request.delete(`/records/${id}`)

export const getSettings = () => request.get('/settings')

export const updateSettings = (data) => request.post('/settings', data)

export const getModelStatus = () => request.get('/model/status')

export default request
