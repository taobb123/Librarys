<template>
  <div class="book-list">
    <div class="book-list-header">
      <h2>图书目录</h2>
      <div class="header-actions">
        <button @click="handleScan" class="scan-btn" :disabled="loading">
          {{ loading ? '扫描中...' : '扫描图书' }}
        </button>
        <button @click="handleUpdate" class="update-btn" :disabled="loading">
          {{ loading ? '更新中...' : '更新数据库' }}
        </button>
        <button @click="$emit('close')" class="close-btn" title="隐藏侧边栏">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M18 6L6 18M6 6l12 12"/>
          </svg>
        </button>
      </div>
    </div>

    <!-- 搜索框 -->
    <div class="search-container">
      <div class="search-box">
        <svg class="search-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="11" cy="11" r="8"></circle>
          <path d="m21 21-4.35-4.35"></path>
        </svg>
        <input
          v-model="searchKeyword"
          type="text"
          placeholder="搜索图书名称..."
          class="search-input"
        />
        <button
          v-if="searchKeyword"
          @click="clearSearch"
          class="clear-search-btn"
          title="清除搜索"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M18 6L6 18M6 6l12 12"/>
          </svg>
        </button>
      </div>
      <!-- 搜索结果提示 -->
      <div v-if="searchKeyword" class="search-result-info">
        找到 {{ searchResults.length }} 本图书
      </div>
    </div>

    <div class="categories">
      <button
        v-for="category in categoryList"
        :key="category"
        @click="selectCategory(category)"
        :class="['category-btn', { active: selectedCategory === category }]"
      >
        {{ category }}
        <span class="count">({{ (categories && categories[category]) || 0 }})</span>
      </button>
      <button
        @click="selectCategory('')"
        :class="['category-btn', { active: selectedCategory === '' }]"
      >
        全部
      </button>
    </div>

    <div class="books-container">
      <div v-if="loading && (!books || books.length === 0)" class="loading">加载中...</div>
      <div v-else-if="!displayBooks || displayBooks.length === 0" class="empty">
        {{ searchKeyword ? '未找到匹配的图书' : '暂无图书' }}
      </div>
      <div v-else class="books">
        <div
          v-for="book in displayBooks"
          :key="book.id"
          @click="selectBook(book)"
          @contextmenu.prevent="handleRightClick($event, book)"
          :class="['book-item', { active: currentBook?.id === book.id }]"
        >
          <div class="book-title">
            <span v-html="highlightText(book.title || '未知标题', searchKeyword)"></span>
          </div>
          <div class="book-meta">
            <span v-if="book.author" class="author">{{ book.author }}</span>
            <span v-if="book.category" class="category">{{ book.category }}</span>
            <span class="format">{{ book.file_format?.toUpperCase() || '' }}</span>
          </div>
        </div>
      </div>
      
      <!-- 右键菜单 -->
      <div
        v-if="contextMenu.show"
        class="context-menu"
        :style="{ left: contextMenu.x + 'px', top: contextMenu.y + 'px' }"
        @click.stop
      >
        <div class="context-menu-item" @click="openFileLocation">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
            <polyline points="9 22 9 12 15 12 15 22"/>
          </svg>
          <span>打开文件位置</span>
        </div>
        <div class="context-menu-item delete-item" @click="showDeleteConfirm">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="3 6 5 6 21 6"/>
            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
          </svg>
          <span>从文件夹删除</span>
        </div>
      </div>
      
      <!-- 删除确认对话框 -->
      <div
        v-if="deleteConfirm.show"
        class="delete-confirm-dialog"
        :style="{ left: deleteConfirm.x + 'px', top: deleteConfirm.y + 'px' }"
        @click.stop
      >
        <div class="confirm-buttons">
          <button class="confirm-btn cancel-btn" @click="cancelDelete">取消</button>
          <button class="confirm-btn ok-btn" @click="confirmDelete">确定</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useBookStore } from '@/stores/bookStore'
import * as bookApi from '@/api/books'

defineEmits<{
  close: []
}>()

const bookStore = useBookStore()

const searchKeyword = ref('')

// 右键菜单
const contextMenu = ref({
  show: false,
  x: 0,
  y: 0,
  book: null as any
})

// 删除确认对话框
const deleteConfirm = ref({
  show: false,
  x: 0,
  y: 0,
  book: null as any
})

const filteredBooks = computed(() => bookStore.filteredBooks || [])
const books = computed(() => bookStore.books || [])
const categories = computed(() => bookStore.categories || {})
const categoryList = computed(() => {
  const cats = bookStore.categoryList || []
  return Array.isArray(cats) ? cats : []
})
const selectedCategory = computed(() => bookStore.selectedCategory || '')
const currentBook = computed(() => bookStore.currentBook)
const loading = computed(() => bookStore.loading || false)

// 搜索结果
const searchResults = computed(() => {
  if (!searchKeyword.value.trim()) {
    return filteredBooks.value
  }
  
  const keyword = searchKeyword.value.toLowerCase().trim()
  return filteredBooks.value.filter(book => {
    const title = (book.title || '').toLowerCase()
    return title.includes(keyword)
  })
})

// 获取文件格式的优先级（数字越小优先级越高）
function getFormatPriority(format: string): number {
  const fmt = (format || '').toLowerCase()
  
  // PDF 优先显示（优先级 1）
  if (fmt === 'pdf') {
    return 1
  }
  
  // TXT、HTML、MD 等文本格式排在最后（优先级 3）
  if (['txt', 'html', 'htm', 'md', 'markdown'].includes(fmt)) {
    return 3
  }
  
  // 其他格式（EPUB、AZW3、MOBI等）排在中间（优先级 2）
  return 2
}

// 显示的图书列表（优先显示搜索结果，并按格式排序）
const displayBooks = computed(() => {
  const booksToShow = searchKeyword.value.trim() ? searchResults.value : filteredBooks.value
  
  // 按格式优先级排序，同优先级按标题排序
  return [...booksToShow].sort((a, b) => {
    const priorityA = getFormatPriority(a.file_format || '')
    const priorityB = getFormatPriority(b.file_format || '')
    
    // 先按格式优先级排序
    if (priorityA !== priorityB) {
      return priorityA - priorityB
    }
    
    // 同优先级按标题排序
    const titleA = (a.title || '').toLowerCase()
    const titleB = (b.title || '').toLowerCase()
    return titleA.localeCompare(titleB, 'zh-CN')
  })
})

// 高亮搜索关键词
function highlightText(text: string, keyword: string): string {
  if (!keyword || !keyword.trim()) {
    return text
  }
  
  const regex = new RegExp(`(${keyword.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi')
  return text.replace(regex, '<mark>$1</mark>')
}

function clearSearch() {
  searchKeyword.value = ''
}

function handleRightClick(event: MouseEvent, book: any) {
  event.stopPropagation()
  
  // 计算菜单位置，确保不超出屏幕边界
  const menuWidth = 200
  const menuHeight = 50
  let x = event.clientX
  let y = event.clientY
  
  // 如果右边界超出，调整到左侧
  if (x + menuWidth > window.innerWidth) {
    x = window.innerWidth - menuWidth - 10
  }
  
  // 如果下边界超出，调整到上方
  if (y + menuHeight > window.innerHeight) {
    y = window.innerHeight - menuHeight - 10
  }
  
  contextMenu.value = {
    show: true,
    x: Math.max(10, x),
    y: Math.max(10, y),
    book: book
  }
  
  // 关闭删除确认对话框（如果打开）
  deleteConfirm.value.show = false
}

async function openFileLocation() {
  if (!contextMenu.value.book) return
  
  try {
    await bookApi.openFileLocation(contextMenu.value.book.id)
    // 关闭右键菜单
    contextMenu.value.show = false
  } catch (error: any) {
    alert('打开文件位置失败：' + (error.message || '未知错误'))
    contextMenu.value.show = false
  }
}

function showDeleteConfirm() {
  if (!contextMenu.value.book) return
  
  const book = contextMenu.value.book
  
  // 计算确认对话框位置（在右键菜单旁边）
  const menuWidth = 200
  const confirmWidth = 120
  const confirmHeight = 40
  let x = contextMenu.value.x + menuWidth + 10
  let y = contextMenu.value.y
  
  // 如果右边界超出，调整到菜单左侧
  if (x + confirmWidth > window.innerWidth) {
    x = contextMenu.value.x - confirmWidth - 10
  }
  
  // 如果下边界超出，调整到上方
  if (y + confirmHeight > window.innerHeight) {
    y = window.innerHeight - confirmHeight - 10
  }
  
  deleteConfirm.value = {
    show: true,
    x: Math.max(10, x),
    y: Math.max(10, y),
    book: book
  }
}

function cancelDelete() {
  deleteConfirm.value.show = false
  contextMenu.value.show = false
}

async function confirmDelete() {
  if (!deleteConfirm.value.book) return
  
  const book = deleteConfirm.value.book
  
  try {
    await bookApi.deleteBook(book.id)
    
    // 关闭对话框和右键菜单
    deleteConfirm.value.show = false
    contextMenu.value.show = false
    
    // 如果删除的是当前正在阅读的图书，清除当前图书
    if (currentBook.value?.id === book.id) {
      bookStore.clearCurrentBook()
    }
    
    // 重新加载图书列表和分类
    await bookStore.fetchBooks()
    await bookStore.fetchCategories()
  } catch (error: any) {
    const errorMsg = error?.response?.data?.message || error?.message || '未知错误'
    alert('删除失败：' + errorMsg)
    deleteConfirm.value.show = false
    contextMenu.value.show = false
  }
}

// 点击其他地方关闭右键菜单和确认对话框
function handleClickOutside(event: MouseEvent) {
  if (contextMenu.value.show) {
    contextMenu.value.show = false
  }
  if (deleteConfirm.value.show) {
    deleteConfirm.value.show = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})

function selectCategory(category: string) {
  bookStore.setSelectedCategory(category)
  bookStore.fetchBooks(category || undefined)
  // 切换分类时清除搜索
  searchKeyword.value = ''
}

function selectBook(book: any) {
  bookStore.fetchBook(book.id)
}

async function handleScan() {
  if (confirm('确定要扫描图书目录吗？\n这将添加新发现的图书。')) {
    try {
      const result = await bookStore.scanBooks(false)
      const message = result && typeof result === 'object'
        ? `扫描完成！\n新增：${result.added || 0} 本`
        : '扫描完成！'
      alert(message)
    } catch (error: any) {
      const errorMsg = error?.message || error?.toString() || '未知错误'
      alert(`扫描失败：${errorMsg}\n\n请检查：\n1. 后端服务是否运行\n2. 图书目录路径是否正确\n3. 数据库连接是否正常`)
    }
  }
}

async function handleUpdate() {
  if (confirm('确定要更新书籍数据库吗？\n这将：\n- 添加新发现的图书\n- 更新已修改的图书信息\n- 删除不存在的图书记录')) {
    try {
      const result = await bookStore.scanBooks(true)
      
      // 安全地访问结果属性
      if (result && typeof result === 'object') {
        const added = result.added ?? 0
        const updated = result.updated ?? 0
        const deleted = result.deleted ?? 0
        
        const message = `更新完成！\n\n新增：${added} 本\n更新：${updated} 本\n删除：${deleted} 本\n\n总计：${added + updated + deleted} 本图书已处理`
        alert(message)
      } else {
        alert('更新完成，但无法获取详细信息')
      }
    } catch (error: any) {
      // 提取详细的错误信息
      let errorMsg = '未知错误'
      
      if (error?.message) {
        errorMsg = error.message
      } else if (typeof error === 'string') {
        errorMsg = error
      } else if (error?.toString) {
        errorMsg = error.toString()
      }
      
      // 根据错误类型提供更具体的提示
      let suggestion = ''
      if (errorMsg.includes('超时') || errorMsg.includes('timeout')) {
        suggestion = '扫描大量图书需要较长时间，请：\n- 检查后端控制台是否仍在处理\n- 等待操作完成后再试\n- 如果确实超时，可以考虑分批扫描'
      } else if (errorMsg.includes('无法连接')) {
        suggestion = '请检查：\n- 后端服务是否运行（http://localhost:5000）\n- 后端控制台是否有错误信息\n- 防火墙是否阻止连接'
      } else {
        suggestion = '请检查：\n- 后端控制台的错误信息\n- 图书目录路径是否正确\n- 数据库连接是否正常'
      }
      
      alert(`更新失败：${errorMsg}\n\n${suggestion}`)
    }
  }
}
</script>

<style scoped>
.book-list {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #f5f5f5;
}

.book-list-header {
  padding: 16px;
  border-bottom: 1px solid #ddd;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: white;
}

.book-list-header h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.header-actions {
  display: flex;
  gap: 8px;
  align-items: center;
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

.close-btn svg {
  display: block;
}

.scan-btn,
.update-btn {
  padding: 6px 12px;
  background: #42b983;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
}

.scan-btn:hover:not(:disabled),
.update-btn:hover:not(:disabled) {
  background: #35a372;
}

.scan-btn:disabled,
.update-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.update-btn {
  background: #007bff;
}

.update-btn:hover:not(:disabled) {
  background: #0056b3;
}

.search-container {
  padding: 12px 16px;
  background: white;
  border-bottom: 1px solid #ddd;
}

.search-box {
  position: relative;
  display: flex;
  align-items: center;
}

.search-icon {
  position: absolute;
  left: 12px;
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
  transition: all 0.2s;
}

.search-input:focus {
  border-color: #42b983;
  box-shadow: 0 0 0 2px rgba(66, 185, 131, 0.1);
}

.clear-search-btn {
  position: absolute;
  right: 8px;
  width: 24px;
  height: 24px;
  padding: 0;
  background: transparent;
  border: none;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #999;
  transition: all 0.2s;
}

.clear-search-btn:hover {
  background: #f0f0f0;
  color: #666;
}

.search-result-info {
  margin-top: 8px;
  font-size: 12px;
  color: #666;
  padding: 4px 0;
}

.search-result-info::before {
  content: '🔍 ';
  margin-right: 4px;
}

.categories {
  padding: 12px 16px;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  background: white;
  border-bottom: 1px solid #ddd;
}

.category-btn {
  padding: 6px 12px;
  background: #f0f0f0;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.2s;
}

.category-btn:hover {
  background: #e0e0e0;
}

.category-btn.active {
  background: #42b983;
  color: white;
  border-color: #42b983;
}

.count {
  font-size: 11px;
  opacity: 0.8;
}

.books-container {
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

.books {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.book-item {
  padding: 12px;
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
}

.book-item:hover {
  border-color: #42b983;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.book-item.active {
  border-color: #42b983;
  background: #e8f5e9;
}

.book-title {
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 6px;
  color: #333;
}

.book-title mark {
  background: #ffeb3b;
  color: #333;
  padding: 0 2px;
  font-weight: 600;
  border-radius: 2px;
}

.book-meta {
  display: flex;
  gap: 8px;
  font-size: 12px;
  color: #666;
}

.author {
  color: #42b983;
}

.category {
  color: #666;
}

.format {
  color: #999;
  font-size: 11px;
}

.context-menu {
  position: fixed;
  background: white;
  border: 1px solid #ddd;
  border-radius: 4px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  z-index: 1000;
  min-width: 200px;
  overflow: hidden;
}

.context-menu-item {
  padding: 10px 16px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
  color: #333;
  transition: background 0.2s;
}

.context-menu-item:hover {
  background: #f5f5f5;
}

.context-menu-item svg {
  color: #666;
  flex-shrink: 0;
}

.context-menu-item span {
  flex: 1;
}

.context-menu-item.delete-item {
  color: #d32f2f;
}

.context-menu-item.delete-item:hover {
  background: #ffebee;
}

.context-menu-item.delete-item svg {
  color: #d32f2f;
}

.delete-confirm-dialog {
  position: fixed;
  background: white;
  border: 1px solid #ddd;
  border-radius: 4px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  z-index: 1001;
  padding: 8px;
}

.confirm-buttons {
  display: flex;
  gap: 8px;
}

.confirm-btn {
  padding: 6px 20px;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.2s;
  background: white;
  color: #333;
}

.confirm-btn:hover {
  background: #f5f5f5;
}

.confirm-btn.ok-btn {
  background: #d32f2f;
  color: white;
  border-color: #d32f2f;
}

.confirm-btn.ok-btn:hover {
  background: #b71c1c;
  border-color: #b71c1c;
}

.confirm-btn.cancel-btn:hover {
  background: #f5f5f5;
  border-color: #bbb;
}
</style>

