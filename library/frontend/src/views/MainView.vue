<template>
  <div class="main-view">
    <!-- 顶部工具栏 -->
    <div class="top-toolbar">
      <!-- 目录打开按钮组 -->
      <div class="sidebar-toggle-group">
        <button
          v-if="visibility.books && !showBookSidebar"
          @click="saveShowBookSidebar(true)"
          class="sidebar-toggle-btn"
          title="显示图书目录"
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M3 12h18M3 6h18M3 18h18"/>
          </svg>
          <span>图书</span>
        </button>
        <button
          v-if="visibility.problems && !showProblemSidebar"
          @click="saveShowProblemSidebar(true)"
          class="sidebar-toggle-btn"
          title="显示问题目录"
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M3 12h18M3 6h18M3 18h18"/>
          </svg>
          <span>问题</span>
        </button>
      </div>
      <!-- 系统配置按钮 -->
      <SystemConfig @visibility-change="handleVisibilityChange" />
    </div>
    
    <!-- 图书模块 -->
    <div v-if="visibility.books" class="module-section">
      <div class="module-content">
        <transition name="sidebar-slide">
          <div v-if="showBookSidebar" class="list-area">
            <BookList @close="saveShowBookSidebar(false)" />
          </div>
        </transition>
        <div class="reader-area">
          <BookReader />
        </div>
      </div>
    </div>
    
    <!-- 问题模块 -->
    <div v-if="visibility.problems" class="module-section">
      <div class="module-content">
        <transition name="sidebar-slide">
          <div v-if="showProblemSidebar" class="list-area">
            <ProblemList @select="handleProblemSelect" @close="saveShowProblemSidebar(false)" />
          </div>
        </transition>
        <div class="reader-area">
          <ProblemReader :problem="currentProblem" @tagsUpdated="handleTagsUpdate" />
        </div>
      </div>
    </div>
    
    <!-- 如果两个模块都隐藏，显示提示 -->
    <div v-if="!visibility.books && !visibility.problems" class="empty-state">
      <div class="empty-content">
        <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"/>
          <path d="M12 16v-4M12 8h.01"/>
        </svg>
        <p>所有模块已隐藏</p>
        <p class="hint">请通过右上角的配置按钮启用模块</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import BookList from '@/components/BookList.vue'
import BookReader from '@/components/BookReader.vue'
import ProblemList from '@/components/ProblemList.vue'
import ProblemReader from '@/components/ProblemReader.vue'
import SystemConfig from '@/components/SystemConfig.vue'
import * as configApi from '@/api/config'
import type { ModuleVisibility } from '@/api/config'
import type { Problem } from '@/api/problems'
import { useBookStore } from '@/stores/bookStore'

const bookStore = useBookStore()

const visibility = ref<ModuleVisibility>({
  books: true,
  problems: false
})

const currentProblem = ref<Problem | null>(null)

// UI 状态持久化
const STORAGE_KEYS = {
  SHOW_BOOK_SIDEBAR: 'library-show-book-sidebar',
  SHOW_PROBLEM_SIDEBAR: 'library-show-problem-sidebar'
}

// 从 localStorage 恢复侧边栏状态
function loadSidebarState() {
  try {
    const savedShowBookSidebar = localStorage.getItem(STORAGE_KEYS.SHOW_BOOK_SIDEBAR)
    const savedShowProblemSidebar = localStorage.getItem(STORAGE_KEYS.SHOW_PROBLEM_SIDEBAR)
    return {
      showBookSidebar: savedShowBookSidebar !== 'false', // 默认 true
      showProblemSidebar: savedShowProblemSidebar !== 'false' // 默认 true
    }
  } catch (error) {
    console.error('加载侧边栏状态失败:', error)
    return { showBookSidebar: true, showProblemSidebar: true }
  }
}

const sidebarState = loadSidebarState()
const showBookSidebar = ref(sidebarState.showBookSidebar)
const showProblemSidebar = ref(sidebarState.showProblemSidebar)

// 保存侧边栏状态
function saveShowBookSidebar(value: boolean) {
  showBookSidebar.value = value
  try {
    localStorage.setItem(STORAGE_KEYS.SHOW_BOOK_SIDEBAR, value.toString())
  } catch (error) {
    console.error('保存图书侧边栏状态失败:', error)
  }
}

function saveShowProblemSidebar(value: boolean) {
  showProblemSidebar.value = value
  try {
    localStorage.setItem(STORAGE_KEYS.SHOW_PROBLEM_SIDEBAR, value.toString())
  } catch (error) {
    console.error('保存问题侧边栏状态失败:', error)
  }
}

function handleVisibilityChange(newVisibility: ModuleVisibility) {
  visibility.value = { ...newVisibility }
}

function handleProblemSelect(problem: Problem) {
  currentProblem.value = problem
}

function handleTagsUpdate(tags: string[]) {
  if (currentProblem.value) {
    currentProblem.value.tags = [...tags]
  }
}

onMounted(async () => {
  try {
    visibility.value = await configApi.getModuleVisibility()
  } catch (error) {
    console.error('加载配置失败:', error)
  }
  
  // 恢复上次的状态
  try {
    // 先加载图书列表和分类
    await bookStore.fetchBooks()
    await bookStore.fetchCategories()
    // 恢复上次选中的分类
    if (bookStore.selectedCategory) {
      await bookStore.fetchBooks(bookStore.selectedCategory)
    }
    // 恢复上次阅读的图书
    await bookStore.restoreLastBook()
  } catch (error) {
    console.error('恢复状态失败:', error)
  }
})
</script>

<style scoped>
.main-view {
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  position: relative;
}

.top-toolbar {
  position: absolute;
  top: 80px;
  right: 16px;
  z-index: 100;
  display: flex;
  align-items: center;
  gap: 12px;
}

.sidebar-toggle-group {
  display: flex;
  gap: 8px;
}

.module-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border-bottom: 2px solid #ddd;
}

.module-section:last-child {
  border-bottom: none;
}

.module-content {
  flex: 1;
  display: flex;
  flex-direction: row;
  overflow: hidden;
}

.list-area {
  width: 350px;
  min-width: 300px;
  max-width: 400px;
  border-right: 1px solid #ddd;
  overflow: hidden;
  flex-shrink: 0;
  position: relative;
}

.reader-area {
  flex: 1;
  overflow: hidden;
}

.sidebar-slide-enter-active,
.sidebar-slide-leave-active {
  transition: transform 0.3s ease;
}

.sidebar-slide-enter-from {
  transform: translateX(-100%);
}

.sidebar-slide-leave-to {
  transform: translateX(-100%);
}

.sidebar-toggle-btn {
  padding: 8px 14px;
  background: rgba(66, 185, 131, 0.9);
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.sidebar-toggle-btn:hover {
  background: rgba(66, 185, 131, 1);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
  transform: translateY(-2px);
}

.sidebar-toggle-btn svg {
  flex-shrink: 0;
}

.empty-state {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.empty-content {
  text-align: center;
  color: #999;
}

.empty-content svg {
  margin-bottom: 16px;
  opacity: 0.5;
}

.hint {
  font-size: 14px;
  color: #bbb;
  margin-top: 8px;
}

/* 响应式：当屏幕较小时，改为上下布局 */
@media (max-width: 768px) {
  .module-content {
    flex-direction: column;
  }
  
  .list-area {
    width: 100%;
    max-width: 100%;
    max-height: 40%;
    border-right: none;
    border-bottom: 1px solid #ddd;
  }
  
  .reader-area {
    flex: 1;
    min-height: 300px;
  }
}
</style>

