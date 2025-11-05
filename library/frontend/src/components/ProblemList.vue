<template>
  <div class="problem-list">
    <div class="problem-list-header">
      <h2>问题目录</h2>
      <div class="header-actions">
        <button @click="showCollectDialog = true" class="collect-btn" :disabled="loading">
          采集问题
        </button>
        <button @click="handleInitSample" class="init-btn" :disabled="loading">
          初始化示例
        </button>
        <button @click="$emit('close')" class="close-btn" title="隐藏侧边栏">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M18 6L6 18M6 6l12 12"/>
          </svg>
        </button>
      </div>
    </div>

    <!-- 采集对话框 -->
    <div v-if="showCollectDialog" class="collect-dialog-overlay" @click="showCollectDialog = false">
      <div class="collect-dialog" @click.stop>
        <div class="dialog-header">
          <h3>从社交平台采集问题</h3>
          <button @click="showCollectDialog = false" class="close-btn-small">×</button>
        </div>
        <div class="dialog-content">
          <div class="form-group">
            <label>主题：</label>
            <input 
              v-model="collectTopic" 
              type="text" 
              placeholder="例如：股票"
              class="form-input"
            />
          </div>
          <div class="form-group">
            <label>采集数量：</label>
            <input 
              v-model.number="collectMaxResults" 
              type="number" 
              min="1"
              max="100"
              class="form-input"
            />
          </div>
          <div class="form-group">
            <label>平台：</label>
            <select v-model="collectPlatform" class="form-select">
              <option value="">全部平台</option>
              <option v-for="platform in availablePlatforms" :key="platform" :value="platform">
                {{ platform }}
              </option>
            </select>
          </div>
          <div class="form-group">
            <label>
              <input 
                v-model="collectAutoSave" 
                type="checkbox" 
              />
              自动保存到问题列表
            </label>
          </div>
          <div class="dialog-actions">
            <button @click="handleCollect" class="btn-primary" :disabled="collecting || !collectTopic">
              {{ collecting ? '采集中...' : '开始采集' }}
            </button>
            <button @click="showCollectDialog = false" class="btn-secondary">取消</button>
          </div>
          <div v-if="collectResult" class="collect-result">
            <p>采集完成！</p>
            <p>共采集 {{ collectResult.total_collected }} 条，已保存 {{ collectResult.saved }} 条</p>
            <div v-if="collectResult.questions.length > 0" class="collected-preview">
              <h4>采集预览：</h4>
              <div 
                v-for="(q, index) in collectResult.questions.slice(0, 5)" 
                :key="index"
                class="preview-item"
              >
                <strong>{{ q.title }}</strong>
                <span class="source-badge">{{ q.source }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 搜索和筛选 -->
    <div class="filter-container">
      <div class="search-box">
        <svg class="search-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="11" cy="11" r="8"></circle>
          <path d="m21 21-4.35-4.35"></path>
        </svg>
        <input
          v-model="searchKeyword"
          type="text"
          placeholder="搜索问题..."
          class="search-input"
        />
      </div>
      
      <!-- 分类和标签筛选 -->
      <div class="filters">
        <select v-model="selectedCategory" @change="handleFilterChange" class="filter-select">
          <option value="">全部分类</option>
          <option v-for="cat in categories" :key="cat" :value="cat">{{ cat }}</option>
        </select>
        
        <div class="tag-filters">
          <button
            v-for="tag in ['兴趣', '待办', '已完成']"
            :key="tag"
            @click="toggleTag(tag)"
            :class="['tag-btn', { active: selectedTags.includes(tag) }]"
          >
            {{ tag }}
          </button>
        </div>
      </div>
    </div>

    <!-- 问题列表 -->
    <div class="problems-container">
      <div v-if="loading && (!problems || problems.length === 0)" class="loading">加载中...</div>
      <div v-else-if="!displayProblems || displayProblems.length === 0" class="empty">
        {{ searchKeyword ? '未找到匹配的问题' : '暂无问题' }}
      </div>
      <div v-else class="problems">
        <div
          v-for="problem in displayProblems"
          :key="problem.id"
          @click="selectProblem(problem)"
          :class="['problem-item', { active: currentProblem?.id === problem.id }]"
        >
          <div class="problem-header">
            <div class="problem-title">{{ problem.title }}</div>
            <div class="problem-tags">
              <span
                v-for="tag in problem.tags"
                :key="tag"
                :class="['tag', getTagClass(tag)]"
              >
                {{ tag }}
              </span>
            </div>
          </div>
          <div class="problem-meta">
            <span v-if="problem.category" class="category">{{ problem.category }}</span>
            <span class="date">{{ formatDate(problem.created_at) }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import * as problemApi from '@/api/problems'
import type { Problem, CollectResult } from '@/api/problems'

const loading = ref(false)
const problems = ref<Problem[]>([])
const currentProblem = ref<Problem | null>(null)
const searchKeyword = ref('')
const selectedCategory = ref('')
const selectedTags = ref<string[]>([])

// 采集相关状态
const showCollectDialog = ref(false)
const collectTopic = ref('')
const collectMaxResults = ref(50)
const collectPlatform = ref('')
const collectAutoSave = ref(true)
const collecting = ref(false)
const collectResult = ref<CollectResult | null>(null)
const availablePlatforms = ref<string[]>([])

const categories = ['文学', '金融', '科技', '历史', '艺术']

// 筛选后的问题列表
const filteredProblems = computed(() => {
  let result = [...problems.value]
  
  // 分类筛选
  if (selectedCategory.value) {
    result = result.filter(p => p.category === selectedCategory.value)
  }
  
  // 标签筛选
  if (selectedTags.value.length > 0) {
    result = result.filter(p => 
      selectedTags.value.some(tag => p.tags.includes(tag))
    )
  }
  
  return result
})

// 搜索后的问题列表
const displayProblems = computed(() => {
  if (!searchKeyword.value.trim()) {
    return filteredProblems.value
  }
  
  const keyword = searchKeyword.value.toLowerCase().trim()
  return filteredProblems.value.filter(problem => {
    const title = (problem.title || '').toLowerCase()
    const content = (problem.content || '').toLowerCase()
    return title.includes(keyword) || content.includes(keyword)
  })
})

function handleFilterChange() {
  // 筛选变化时刷新
}

function toggleTag(tag: string) {
  const index = selectedTags.value.indexOf(tag)
  if (index > -1) {
    selectedTags.value.splice(index, 1)
  } else {
    selectedTags.value.push(tag)
  }
}

function getTagClass(tag: string): string {
  const tagClasses: { [key: string]: string } = {
    '兴趣': 'tag-interest',
    '待办': 'tag-todo',
    '已完成': 'tag-completed'
  }
  return tagClasses[tag] || ''
}

function formatDate(dateString: string): string {
  const date = new Date(dateString)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}

const emit = defineEmits<{
  select: [problem: Problem]
  close: []
}>()

function selectProblem(problem: Problem) {
  currentProblem.value = problem
  emit('select', problem)
}

async function fetchProblems() {
  loading.value = true
  try {
    problems.value = await problemApi.getProblems()
  } catch (error) {
    console.error('获取问题列表失败:', error)
    problems.value = []
  } finally {
    loading.value = false
  }
}

async function handleInitSample() {
  if (confirm('确定要初始化示例问题数据吗？这将添加股票市场相关的示例问题。')) {
    try {
      await problemApi.initSampleProblems()
      await fetchProblems()
      alert('示例数据初始化成功！')
    } catch (error: any) {
      alert('初始化失败：' + (error?.message || '未知错误'))
    }
  }
}

async function handleCollect() {
  if (!collectTopic.value.trim()) {
    alert('请输入主题')
    return
  }
  
  collecting.value = true
  collectResult.value = null
  
  try {
    const result = await problemApi.collectQuestions({
      topic: collectTopic.value.trim(),
      max_results: collectMaxResults.value,
      platform: collectPlatform.value || undefined,
      auto_save: collectAutoSave.value
    })
    
    collectResult.value = result
    
    if (collectAutoSave.value) {
      // 如果自动保存，刷新问题列表
      await fetchProblems()
    }
    
    if (result.total_collected > 0) {
      setTimeout(() => {
        showCollectDialog.value = false
        collectTopic.value = ''
        collectResult.value = null
      }, 3000)
    }
  } catch (error: any) {
    alert('采集失败：' + (error?.response?.data?.message || error?.message || '未知错误'))
  } finally {
    collecting.value = false
  }
}

async function loadAvailablePlatforms() {
  try {
    availablePlatforms.value = await problemApi.getCollectPlatforms()
  } catch (error) {
    console.error('加载平台列表失败:', error)
    availablePlatforms.value = ['知乎', '微博'] // 默认值
  }
}

onMounted(() => {
  fetchProblems()
  loadAvailablePlatforms()
})
</script>

<style scoped>
.problem-list {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #f5f5f5;
}

.problem-list-header {
  padding: 16px;
  border-bottom: 1px solid #ddd;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: white;
}

.problem-list-header h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.header-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.collect-btn {
  padding: 6px 12px;
  background: #28a745;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
}

.collect-btn:hover:not(:disabled) {
  background: #218838;
}

.collect-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.init-btn {
  padding: 6px 12px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
}

.init-btn:hover:not(:disabled) {
  background: #0056b3;
}

.init-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.collect-dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.collect-dialog {
  background: white;
  border-radius: 8px;
  width: 90%;
  max-width: 500px;
  max-height: 80vh;
  overflow-y: auto;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
}

.dialog-header {
  padding: 16px;
  border-bottom: 1px solid #ddd;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.dialog-header h3 {
  margin: 0;
  font-size: 18px;
}

.close-btn-small {
  width: 24px;
  height: 24px;
  padding: 0;
  background: transparent;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #666;
  line-height: 1;
}

.close-btn-small:hover {
  color: #333;
}

.dialog-content {
  padding: 20px;
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  margin-bottom: 6px;
  font-weight: 500;
  font-size: 14px;
}

.form-input,
.form-select {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.form-group label input[type="checkbox"] {
  margin-right: 6px;
}

.dialog-actions {
  display: flex;
  gap: 12px;
  margin-top: 20px;
}

.btn-primary {
  padding: 10px 20px;
  background: #28a745;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  flex: 1;
}

.btn-primary:hover:not(:disabled) {
  background: #218838;
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-secondary {
  padding: 10px 20px;
  background: #6c757d;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  flex: 1;
}

.btn-secondary:hover {
  background: #5a6268;
}

.collect-result {
  margin-top: 20px;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 4px;
}

.collect-result p {
  margin: 8px 0;
  font-size: 14px;
}

.collected-preview {
  margin-top: 12px;
}

.collected-preview h4 {
  margin: 0 0 12px 0;
  font-size: 14px;
}

.preview-item {
  padding: 8px;
  background: white;
  border-radius: 4px;
  margin-bottom: 8px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
}

.source-badge {
  padding: 2px 8px;
  background: #e9ecef;
  border-radius: 12px;
  font-size: 11px;
  color: #666;
}

.close-btn {
  width: 32px;
  height: 32px;
  padding: 0;
  background: #f0f0f0;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  color: #666;
}

.close-btn:hover {
  background: #e0e0e0;
  color: #333;
}

.filter-container {
  padding: 12px 16px;
  background: white;
  border-bottom: 1px solid #ddd;
}

.search-box {
  position: relative;
  margin-bottom: 12px;
}

.search-icon {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  color: #999;
  pointer-events: none;
}

.search-input {
  width: 100%;
  padding: 8px 12px 8px 36px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 13px;
  outline: none;
}

.filters {
  display: flex;
  gap: 12px;
  align-items: center;
  flex-wrap: wrap;
}

.filter-select {
  padding: 6px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 13px;
  cursor: pointer;
}

.tag-filters {
  display: flex;
  gap: 8px;
}

.tag-btn {
  padding: 6px 12px;
  background: #f0f0f0;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  transition: all 0.2s;
}

.tag-btn:hover {
  background: #e0e0e0;
}

.tag-btn.active {
  background: #42b983;
  color: white;
  border-color: #42b983;
}

.problems-container {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.loading,
.empty {
  text-align: center;
  padding: 40px 20px;
  color: #999;
}

.problems {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.problem-item {
  padding: 12px;
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
}

.problem-item:hover {
  border-color: #42b983;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.problem-item.active {
  border-color: #42b983;
  background: #e8f5e9;
}

.problem-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 8px;
}

.problem-title {
  font-size: 14px;
  font-weight: 500;
  color: #333;
  flex: 1;
}

.problem-tags {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  margin-left: 12px;
}

.tag {
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 500;
}

.tag-interest {
  background: #fff3cd;
  color: #856404;
}

.tag-todo {
  background: #cfe2ff;
  color: #084298;
}

.tag-completed {
  background: #d1e7dd;
  color: #0f5132;
}

.problem-meta {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: #666;
}

.category {
  color: #42b983;
}

.date {
  color: #999;
}
</style>

