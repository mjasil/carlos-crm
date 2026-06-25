import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://carlos-crm.onrender.com'

const api = axios.create({
  baseURL: API_URL,
  headers: { 'Content-Type': 'application/json' }
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('carlos_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

export default api
