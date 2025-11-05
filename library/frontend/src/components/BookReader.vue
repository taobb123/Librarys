<template>
  <div class="book-reader">
    <div v-if="!currentBook" class="empty-reader">
      <div class="empty-content">
        <p>请从左侧选择一本图书开始阅读</p>
      </div>
    </div>

    <div v-else class="reader-container">
      <!-- 隐藏时显示的浮动按钮 -->
      <div v-if="!showHeader" class="header-toggle-btn" @click="saveShowHeader(true)" title="显示标题栏">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M3 12h18M3 6h18M3 18h18"/>
        </svg>
      </div>
      
      <div v-show="showHeader" class="reader-header">
        <div class="book-info">
          <h3>{{ currentBook.title }}</h3>
          <div class="book-details">
            <span v-if="currentBook.author">作者：{{ currentBook.author }}</span>
            <span v-if="currentBook.category">分类：{{ currentBook.category }}</span>
          </div>
        </div>
        <div class="reader-tools">
          <button @click="saveShowHeader(false)" class="tool-btn" title="隐藏标题栏">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M18 6L6 18M6 6l12 12"/>
            </svg>
          </button>
          <button @click="saveShowBookmarks(!showBookmarks)" class="tool-btn">
            {{ showBookmarks ? '隐藏' : '显示' }}书签
          </button>
          <button @click="addCurrentBookmark" class="tool-btn primary">
            添加书签
          </button>
        </div>
      </div>

      <div class="reader-body">
        <div v-if="showBookmarks" class="bookmarks-panel">
          <h4>书签和笔记</h4>
          <div v-if="bookmarks.length === 0" class="no-bookmarks">暂无书签</div>
          <div v-else class="bookmarks-list">
            <div
              v-for="bookmark in bookmarks"
              :key="bookmark.id"
              class="bookmark-item"
            >
              <div class="bookmark-content" @click="goToBookmark(bookmark)">
                <div v-if="bookmark.position" class="bookmark-position">
                  位置：{{ bookmark.position }}
                </div>
                <div v-if="bookmark.page_number" class="bookmark-page">
                  页码：{{ bookmark.page_number }}
                </div>
                <div v-if="bookmark.note" class="bookmark-note">
                  {{ bookmark.note }}
                </div>
                <div class="bookmark-time">
                  {{ formatDate(bookmark.created_at) }}
                </div>
              </div>
              <button @click="removeBookmark(bookmark.id)" class="delete-btn">删除</button>
            </div>
          </div>
        </div>

        <div class="reader-content">
          <div v-if="loading" class="loading">加载中...</div>
          <div v-else-if="error" class="error">
            <p>{{ error }}</p>
            <button @click="loadBook">重试</button>
          </div>
          <div v-else class="viewer">
            <!-- PDF阅读器 -->
            <iframe
              v-if="supportedFormats.pdf.includes(fileFormat)"
              :src="bookFileUrl"
              class="pdf-viewer"
              frameborder="0"
            ></iframe>

            <!-- EPUB阅读器（优先尝试EPUB.js，失败则使用转换后的HTML） -->
            <div
              v-if="supportedFormats.epub.includes(fileFormat) && !useEpubFallback"
              ref="epubContainer"
              class="epub-viewer"
            ></div>

            <!-- 文本格式阅读器（TXT、HTML等，以及EPUB转换后的HTML） -->
            <div
              v-else-if="supportedFormats.text.includes(fileFormat) || (fileFormat === 'epub' && useEpubFallback)"
              ref="textContainer"
              class="text-viewer"
              :class="{ 'html-viewer': isHtmlContent }"
            ></div>

            <!-- 电子书格式（AZW3, MOBI等）- 提供下载 -->
            <div
              v-else-if="supportedFormats.ebook.includes(fileFormat)"
              class="ebook-format"
            >
              <div class="format-info">
                <h4>{{ currentBook.file_format?.toUpperCase() }} 格式电子书</h4>
                <p class="format-desc">
                  {{ currentBook.file_format?.toUpperCase() }} 格式暂不支持在线阅读，您可以下载后使用电子书阅读器打开。
                </p>
                <div class="book-info-card">
                  <p><strong>书名：</strong>{{ currentBook.title }}</p>
                  <p v-if="currentBook.author"><strong>作者：</strong>{{ currentBook.author }}</p>
                  <p v-if="currentBook.file_size">
                    <strong>文件大小：</strong>{{ formatFileSize(currentBook.file_size) }}
                  </p>
                </div>
                <div class="action-buttons">
                  <a :href="bookFileUrl" download class="download-btn primary">
                    下载文件
                  </a>
                  <button @click="loadBook" class="download-btn">重试加载</button>
                </div>
              </div>
            </div>

            <!-- 其他格式提示 -->
            <div v-else class="unsupported-format">
              <div class="format-info">
                <h4>{{ currentBook.file_format?.toUpperCase() || '未知' }} 格式</h4>
                <p class="format-desc">该格式暂不支持在线阅读</p>
                <div class="book-info-card">
                  <p><strong>文件路径：</strong></p>
                  <p class="file-path">{{ currentBook.file_path }}</p>
                </div>
                <a :href="bookFileUrl" :download="currentBook.title" class="download-btn primary">
                  下载文件
                </a>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { useBookStore } from '@/stores/bookStore'
import { getBookFileUrl } from '@/api/books'
// @ts-ignore - epubjs类型定义可能不完整
import Epub from 'epubjs'

const bookStore = useBookStore()

const currentBook = computed(() => bookStore.currentBook)
const bookmarks = computed(() => bookStore.bookmarks)
const loading = ref(false)
const error = ref('')

// UI 状态持久化
const STORAGE_KEYS = {
  SHOW_BOOKMARKS: 'library-show-bookmarks',
  SHOW_HEADER: 'library-show-header'
}

// 从 localStorage 恢复 UI 状态
function loadUIState() {
  try {
    const savedShowBookmarks = localStorage.getItem(STORAGE_KEYS.SHOW_BOOKMARKS)
    const savedShowHeader = localStorage.getItem(STORAGE_KEYS.SHOW_HEADER)
    return {
      showBookmarks: savedShowBookmarks === 'true',
      showHeader: savedShowHeader !== 'false' // 默认 true
    }
  } catch (error) {
    console.error('加载UI状态失败:', error)
    return { showBookmarks: false, showHeader: true }
  }
}

const uiState = loadUIState()
const showBookmarks = ref(uiState.showBookmarks)
const showHeader = ref(uiState.showHeader)

// 监听状态变化并保存
function saveShowBookmarks(value: boolean) {
  showBookmarks.value = value
  try {
    localStorage.setItem(STORAGE_KEYS.SHOW_BOOKMARKS, value.toString())
  } catch (error) {
    console.error('保存书签面板状态失败:', error)
  }
}

function saveShowHeader(value: boolean) {
  showHeader.value = value
  try {
    localStorage.setItem(STORAGE_KEYS.SHOW_HEADER, value.toString())
  } catch (error) {
    console.error('保存标题栏状态失败:', error)
  }
}
const epubContainer = ref<HTMLElement | null>(null)
const textContainer = ref<HTMLElement | null>(null)
const bookRef = ref<any>(null)
const renditionRef = ref<any>(null)
const textContent = ref<string>('')
const useEpubFallback = ref(false)
const isHtmlContent = ref(false)

// 支持的格式分类
const supportedFormats = {
  pdf: ['pdf'],
  epub: ['epub'],
  text: ['txt', 'md', 'markdown', 'html', 'htm'],
  ebook: ['azw3', 'mobi', 'azw']
}

// 获取当前文件格式
const fileFormat = computed(() => {
  return currentBook.value?.file_format?.toLowerCase() || ''
})

const bookFileUrl = computed(() => {
  if (!currentBook.value) return ''
  return getBookFileUrl(currentBook.value.id)
})

watch(
  currentBook,
  async (newBook) => {
    if (!newBook) {
      cleanup()
      return
    }

    loading.value = true
    error.value = ''

    try {
      const format = newBook.file_format?.toLowerCase()
      
      if (supportedFormats.epub.includes(format)) {
        // 先尝试使用EPUB.js
        useEpubFallback.value = false
        try {
          await nextTick()
          await loadEpub()
        } catch (err: any) {
          // 如果EPUB.js失败，使用后端转换的HTML
          console.warn('EPUB.js加载失败，使用HTML转换:', err)
          useEpubFallback.value = true
          await nextTick()
          await loadText()
        }
      } else if (supportedFormats.pdf.includes(format)) {
        // PDF使用iframe，无需额外处理
        loading.value = false
      } else if (supportedFormats.text.includes(format)) {
        await nextTick()
        await loadText()
      } else if (supportedFormats.ebook.includes(format)) {
        // 电子书格式，显示下载选项
        loading.value = false
      } else {
        // 其他格式，显示下载选项
        loading.value = false
      }
    } catch (err: any) {
      error.value = err.message || '加载失败'
      loading.value = false
    }
  },
  { immediate: true }
)

onUnmounted(() => {
  cleanup()
})

function cleanup() {
  if (renditionRef.value) {
    try {
      renditionRef.value.destroy()
    } catch (e) {
      // ignore
    }
    renditionRef.value = null
  }
  if (bookRef.value) {
    bookRef.value = null
  }
}

async function loadEpub() {
  if (!epubContainer.value || !currentBook.value) return

  try {
    cleanup()

    // 创建EPUB实例
    const url = bookFileUrl.value
    bookRef.value = Epub(url)

    // 创建rendition
    renditionRef.value = bookRef.value.renderTo(epubContainer.value, {
      width: '100%',
      height: '100%',
      spread: 'none',
    })

    // 显示第一页
    await renditionRef.value.display()

    loading.value = false
  } catch (err: any) {
    error.value = `EPUB加载失败: ${err.message}`
    loading.value = false
    throw err
  }
}

async function loadText() {
  if (!textContainer.value || !currentBook.value) return

  try {
    const { getBookText } = await import('@/api/books')
    const result = await getBookText(currentBook.value.id)
    
    if (result.success && result.content) {
      textContent.value = result.content
      
      if (textContainer.value) {
        // 根据内容类型决定如何处理
        if (result.type === 'html' || currentBook.value.file_format?.toLowerCase() === 'html' || currentBook.value.file_format?.toLowerCase() === 'htm') {
          // HTML内容直接显示
          isHtmlContent.value = true
          textContainer.value.innerHTML = result.content
        } else if (result.format === 'html' && result.original_format === 'epub') {
          // EPUB转换的HTML
          isHtmlContent.value = true
          textContainer.value.innerHTML = result.content
        } else {
          // 纯文本内容，需要格式化
          isHtmlContent.value = false
          textContainer.value.innerHTML = formatTextContent(result.content)
        }
      }
      loading.value = false
    } else {
      throw new Error(result.message || '读取文本失败')
    }
  } catch (err: any) {
    error.value = `文本加载失败: ${err.message}`
    loading.value = false
    throw err
  }
}

function formatTextContent(content: string): string {
  // 将文本格式化为HTML，保留换行
  return content
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/\r\n/g, '<br>')
    .replace(/\n/g, '<br>')
    .replace(/\r/g, '<br>')
}

function formatFileSize(bytes?: number): string {
  if (!bytes) return '未知'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB'
  if (bytes < 1024 * 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(2) + ' MB'
  return (bytes / (1024 * 1024 * 1024)).toFixed(2) + ' GB'
}

function formatDate(dateString: string) {
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN')
}

function addCurrentBookmark() {
  const note = prompt('请输入笔记（可选）：')
  const position = renditionRef.value
    ? `第 ${renditionRef.value.currentLocation()?.start?.displayed?.page || '?'} 页`
    : '当前位置'

  bookStore.addBookmark({
    position: position,
    note: note || undefined,
  })
}

function removeBookmark(bookmarkId: number) {
  if (confirm('确定要删除这个书签吗？')) {
    bookStore.removeBookmark(bookmarkId)
  }
}

function goToBookmark(bookmark: any) {
  if (renditionRef.value && bookmark.position) {
    // 尝试跳转到书签位置
    // EPUB.js的位置导航需要特定的格式
    try {
      // 这里可以根据bookmark中的位置信息实现跳转
      console.log('跳转到书签:', bookmark)
    } catch (e) {
      console.error('跳转失败:', e)
    }
  }
}

async function loadBook() {
  if (!currentBook.value) return
  error.value = ''
  loading.value = true
  try {
    const format = currentBook.value.file_format?.toLowerCase()
    
    if (supportedFormats.epub.includes(format)) {
      useEpubFallback.value = false
      try {
        await nextTick()
        await loadEpub()
      } catch (err: any) {
        console.warn('EPUB.js加载失败，使用HTML转换:', err)
        useEpubFallback.value = true
        await nextTick()
        await loadText()
      }
    } else if (supportedFormats.pdf.includes(format)) {
      loading.value = false
    } else if (supportedFormats.text.includes(format)) {
      await nextTick()
      await loadText()
    } else if (supportedFormats.ebook.includes(format)) {
      loading.value = false
    } else {
      loading.value = false
    }
  } catch (err: any) {
    error.value = err.message || '加载失败'
    loading.value = false
  }
}
</script>

<style scoped>
.book-reader {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #f9f9f9;
}

.empty-reader {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.empty-content {
  text-align: center;
  color: #999;
}

.reader-container {
  height: 100%;
  display: flex;
  flex-direction: column;
  position: relative;
}

.reader-header {
  padding: 16px;
  background: white;
  border-bottom: 1px solid #ddd;
  display: flex;
  justify-content: space-between;
  align-items: center;
  transition: transform 0.3s ease, opacity 0.3s ease;
  position: relative;
  z-index: 10;
}

.header-toggle-btn {
  position: absolute;
  top: 12px;
  right: 12px;
  width: 40px;
  height: 40px;
  background: rgba(66, 185, 131, 0.9);
  color: white;
  border: none;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  transition: all 0.3s ease;
}

.header-toggle-btn:hover {
  background: rgba(66, 185, 131, 1);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
  transform: scale(1.1);
}

.book-info h3 {
  margin: 0 0 8px 0;
  font-size: 18px;
  color: #333;
}

.book-details {
  display: flex;
  gap: 16px;
  font-size: 13px;
  color: #666;
}

.reader-tools {
  display: flex;
  gap: 8px;
}

.tool-btn {
  padding: 8px 16px;
  background: #f0f0f0;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.2s;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.tool-btn:hover {
  background: #e0e0e0;
}

.tool-btn.primary {
  background: #42b983;
  color: white;
  border-color: #42b983;
}

.tool-btn.primary:hover {
  background: #35a372;
}

.tool-btn svg {
  display: inline-block;
  vertical-align: middle;
}

.reader-body {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.bookmarks-panel {
  width: 300px;
  background: white;
  border-right: 1px solid #ddd;
  padding: 16px;
  overflow-y: auto;
}

.bookmarks-panel h4 {
  margin: 0 0 16px 0;
  font-size: 16px;
}

.no-bookmarks {
  text-align: center;
  padding: 40px 20px;
  color: #999;
}

.bookmarks-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.bookmark-item {
  padding: 12px;
  background: #f5f5f5;
  border-radius: 4px;
  position: relative;
}

.bookmark-content {
  cursor: pointer;
  padding-right: 50px;
}

.bookmark-content:hover {
  opacity: 0.8;
}

.bookmark-position,
.bookmark-page {
  font-size: 12px;
  color: #666;
  margin-bottom: 4px;
}

.bookmark-note {
  font-size: 13px;
  color: #333;
  margin: 8px 0;
}

.bookmark-time {
  font-size: 11px;
  color: #999;
}

.delete-btn {
  position: absolute;
  bottom: 12px;
  right: 12px;
  padding: 2px 6px;
  background: #ff5252;
  color: white;
  border: none;
  border-radius: 3px;
  cursor: pointer;
  font-size: 11px;
  line-height: 1.4;
  min-width: auto;
  height: auto;
}

.delete-btn:hover {
  background: #ff1744;
}

.reader-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.loading,
.error {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #999;
}

.error button {
  margin-top: 16px;
  padding: 8px 16px;
  background: #42b983;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.viewer {
  height: 100%;
  overflow: hidden;
}

.pdf-viewer {
  width: 100%;
  height: 100%;
  border: none;
}

.epub-viewer {
  width: 100%;
  height: 100%;
  overflow-y: auto;
  padding: 20px;
}

.text-viewer {
  width: 100%;
  height: 100%;
  overflow-y: auto;
  padding: 20px;
  background: #fff;
  color: #333;
  font-size: 14px;
  line-height: 1.8;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Microsoft YaHei', Arial, sans-serif;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.text-viewer.html-viewer {
  white-space: normal;
  padding: 0;
}

.text-viewer.html-viewer :deep(img) {
  max-width: 100%;
  height: auto;
}

.text-viewer.html-viewer :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 16px 0;
}

.text-viewer.html-viewer :deep(table td),
.text-viewer.html-viewer :deep(table th) {
  border: 1px solid #ddd;
  padding: 8px;
}

.text-viewer.html-viewer :deep(a) {
  color: #42b983;
  text-decoration: none;
}

.text-viewer.html-viewer :deep(a:hover) {
  text-decoration: underline;
}

.ebook-format,
.unsupported-format {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  padding: 40px 20px;
  text-align: center;
  color: #666;
}

.format-info {
  max-width: 500px;
  width: 100%;
}

.format-info h4 {
  margin: 0 0 16px 0;
  font-size: 20px;
  color: #333;
}

.format-desc {
  margin: 0 0 24px 0;
  color: #666;
  line-height: 1.6;
}

.book-info-card {
  background: #f5f5f5;
  border-radius: 8px;
  padding: 16px;
  margin: 24px 0;
  text-align: left;
}

.book-info-card p {
  margin: 8px 0;
  font-size: 14px;
  line-height: 1.6;
}

.file-path {
  word-break: break-all;
  font-size: 12px;
  color: #999;
  margin-top: 8px;
}

.action-buttons {
  display: flex;
  gap: 12px;
  justify-content: center;
  flex-wrap: wrap;
}

.download-btn {
  padding: 12px 24px;
  background: #f0f0f0;
  color: #333;
  text-decoration: none;
  border-radius: 4px;
  display: inline-block;
  border: 1px solid #ddd;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.download-btn:hover {
  background: #e0e0e0;
}

.download-btn.primary {
  background: #42b983;
  color: white;
  border-color: #42b983;
}

.download-btn.primary:hover {
  background: #35a372;
}
</style>

