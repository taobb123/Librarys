import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000'

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
})

export interface Problem {
  id: number
  title: string
  content: string
  category?: string
  tags: string[]
  related_book_ids?: number[]
  created_at: string
  updated_at: string
}

export interface ProblemAnalysis {
  problem_id: number
  analysis: string
}

export interface CollectedQuestion {
  title: string
  content: string
  source: string
  source_url?: string
  author?: string
  tags: string[]
  category?: string
  metadata?: {
    collected_at?: string
    source_metadata?: any
  }
}

export interface CollectResult {
  success: boolean
  total_collected: number
  saved: number
  questions: CollectedQuestion[]
}

// 获取问题列表
export async function getProblems(category?: string, tag?: string): Promise<Problem[]> {
  const params: any = {}
  if (category) params.category = category
  if (tag) params.tag = tag
  
  const response = await api.get('/api/problems/list', { params })
  return response.data.data
}

// 获取问题详情
export async function getProblem(problemId: number): Promise<Problem> {
  const response = await api.get(`/api/problems/${problemId}`)
  return response.data.data
}

// 创建问题
export async function createProblem(data: {
  title: string
  content: string
  category?: string
  tags?: string[]
  related_book_ids?: number[]
}): Promise<Problem> {
  const response = await api.post('/api/problems/', data)
  return response.data.data
}

// 更新问题
export async function updateProblem(
  problemId: number,
  data: {
    title?: string
    content?: string
    category?: string
    tags?: string[]
    related_book_ids?: number[]
  }
): Promise<void> {
  await api.put(`/api/problems/${problemId}`, data)
}

// 删除问题
export async function deleteProblem(problemId: number): Promise<void> {
  await api.delete(`/api/problems/${problemId}`)
}

// 更新问题标签
export async function updateProblemTags(problemId: number, tags: string[]): Promise<void> {
  await api.put(`/api/problems/${problemId}/tags`, { tags })
}

// 初始化示例数据
export async function initSampleProblems(): Promise<{ added: number }> {
  const response = await api.post('/api/problems/init-sample')
  return response.data.data
}

// AI分析问题
export async function analyzeProblem(problemId: number): Promise<ProblemAnalysis> {
  const response = await api.post(`/api/problems/${problemId}/analyze`)
  return response.data.data
}

// 从社交平台采集问题
export async function collectQuestions(data: {
  topic: string
  max_results?: number
  platform?: string
  auto_save?: boolean
}): Promise<CollectResult> {
  const response = await api.post('/api/problems/collect', data)
  return response.data
}

// 获取可用的采集平台列表
export async function getCollectPlatforms(): Promise<string[]> {
  const response = await api.get('/api/problems/collect/platforms')
  return response.data.data
}

