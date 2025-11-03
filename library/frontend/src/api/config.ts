import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000'

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
})

export interface ModuleVisibility {
  books: boolean
  problems: boolean
}

// 获取模块显示配置
export async function getModuleVisibility(): Promise<ModuleVisibility> {
  const response = await api.get('/api/config/module-visibility')
  return response.data.data
}

// 更新模块显示配置
export async function updateModuleVisibility(visibility: ModuleVisibility): Promise<ModuleVisibility> {
  const response = await api.put('/api/config/module-visibility', visibility)
  return response.data.data
}

