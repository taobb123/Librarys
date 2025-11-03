import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000'

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 默认30秒
})

// 扫描操作使用更长的超时时间（5分钟）
const scanApi = axios.create({
  baseURL: API_BASE_URL,
  timeout: 300000, // 5分钟，用于扫描大量图书
})

export interface Book {
  id: number
  title: string
  file_path: string
  file_format: string
  author?: string
  country?: string
  year?: number
  category?: string
  file_size?: number
}

export interface Category {
  [key: string]: number
}

export interface Bookmark {
  id: number
  book_id: number
  page_number?: number
  position?: string
  note?: string
  created_at: string
}

// 获取图书列表
export async function getBooks(category?: string): Promise<Book[]> {
  const params = category ? { category } : {}
  const response = await api.get('/api/books/list', { params })
  return response.data.data
}

// 获取分类列表
export async function getCategories(): Promise<Category> {
  const response = await api.get('/api/books/categories')
  return response.data.data
}

// 获取图书详情
export async function getBook(bookId: number): Promise<Book> {
  const response = await api.get(`/api/books/${bookId}`)
  return response.data.data
}

// 获取图书文件URL
export function getBookFileUrl(bookId: number): string {
  return `${API_BASE_URL}/api/books/${bookId}/file`
}

// 获取图书文本内容（用于TXT等格式）
export async function getBookText(bookId: number): Promise<{
  success: boolean
  content?: string
  encoding?: string
  format?: string
  type?: string
  original_format?: string
  message?: string
}> {
  const response = await api.get(`/api/books/${bookId}/text`)
  return response.data
}

// 扫描图书目录
export async function scanBooks(update: boolean = false): Promise<{
  added: number
  updated: number
  deleted: number
  total: number
}> {
  try {
    // 使用scanApi（更长的超时时间）进行扫描操作
    const response = await scanApi.post('/api/books/scan', { update })
    
    // 检查响应是否成功
    if (!response.data.success) {
      throw new Error(response.data.message || '扫描失败')
    }
    
    // 确保返回的数据结构正确
    const data = response.data.data || {}
    return {
      added: data.added || 0,
      updated: data.updated || 0,
      deleted: data.deleted || 0,
      total: data.total || 0
    }
  } catch (error: any) {
    // 改进错误处理，区分不同类型的错误
    if (error.response) {
      // 服务器返回了错误响应
      const errorMsg = error.response.data?.message || error.response.data?.error || '服务器错误'
      throw new Error(errorMsg)
    } else if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
      // 请求超时
      throw new Error('扫描操作超时（可能需要较长时间），请稍后重试或检查后端服务状态')
    } else if (error.request) {
      // 请求已发送但没有收到响应
      // 这可能是：1. 服务器未运行 2. 网络问题 3. 操作超时
      throw new Error('无法连接到服务器或操作超时。请检查：1) 后端服务是否运行在 http://localhost:5000  2) 网络连接是否正常  3) 如果图书数量很多，可能需要更长时间')
    } else {
      // 其他错误
      throw new Error(error.message || '扫描失败，请重试')
    }
  }
}

// 获取书签列表
export async function getBookmarks(bookId: number): Promise<Bookmark[]> {
  const response = await api.get(`/api/books/${bookId}/bookmarks`)
  return response.data.data
}

// 创建书签
export async function createBookmark(
  bookId: number,
  data: { page_number?: number; position?: string; note?: string }
): Promise<Bookmark> {
  const response = await api.post(`/api/books/${bookId}/bookmarks`, data)
  return response.data.data
}

// 更新书签
export async function updateBookmark(
  bookmarkId: number,
  data: { page_number?: number; position?: string; note?: string }
): Promise<void> {
  await api.put(`/api/books/bookmarks/${bookmarkId}`, data)
}

// 删除书签
export async function deleteBookmark(bookmarkId: number): Promise<void> {
  await api.delete(`/api/books/bookmarks/${bookmarkId}`)
}

// 在资源管理器中打开文件位置
export async function openFileLocation(bookId: number): Promise<void> {
  await api.post(`/api/books/${bookId}/open-location`)
}

// 从文件夹删除图书
export async function deleteBook(bookId: number): Promise<void> {
  await api.delete(`/api/books/${bookId}`)
}

