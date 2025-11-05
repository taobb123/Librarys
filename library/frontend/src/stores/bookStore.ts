import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Book, Category, Bookmark } from '@/api/books'
import * as bookApi from '@/api/books'

const STORAGE_KEY = 'library-book-store'
const STORAGE_KEYS = {
  CURRENT_BOOK_ID: 'library-current-book-id',
  SELECTED_CATEGORY: 'library-selected-category'
}

// 从 localStorage 恢复状态
function loadFromStorage() {
  try {
    const savedBookId = localStorage.getItem(STORAGE_KEYS.CURRENT_BOOK_ID)
    const savedCategory = localStorage.getItem(STORAGE_KEYS.SELECTED_CATEGORY)
    return {
      currentBookId: savedBookId ? parseInt(savedBookId) : null,
      selectedCategory: savedCategory || ''
    }
  } catch (error) {
    console.error('加载状态失败:', error)
    return { currentBookId: null, selectedCategory: '' }
  }
}

export const useBookStore = defineStore('book', () => {
  // 状态
  const books = ref<Book[]>([])
  const categories = ref<Category>({})
  const currentBook = ref<Book | null>(null)
  const bookmarks = ref<Bookmark[]>([])
  const selectedCategory = ref<string>(loadFromStorage().selectedCategory)
  const loading = ref(false)

  // 计算属性
  const filteredBooks = computed(() => {
    if (!selectedCategory.value) {
      return books.value
    }
    return books.value.filter(book => book.category === selectedCategory.value)
  })

  const categoryList = computed(() => {
    return Object.keys(categories.value)
  })

  // 方法
  async function fetchBooks(category?: string) {
    loading.value = true
    try {
      books.value = await bookApi.getBooks(category)
    } catch (error) {
      console.error('获取图书列表失败:', error)
      // 不抛出错误，保持空数组
      books.value = []
    } finally {
      loading.value = false
    }
  }

  async function fetchCategories() {
    try {
      categories.value = await bookApi.getCategories()
    } catch (error) {
      console.error('获取分类失败:', error)
      // 不抛出错误，保持空对象
      categories.value = {}
    }
  }

  async function fetchBook(bookId: number) {
    loading.value = true
    try {
      currentBook.value = await bookApi.getBook(bookId)
      await fetchBookmarks(bookId)
      // 保存当前图书ID到 localStorage
      try {
        localStorage.setItem(STORAGE_KEYS.CURRENT_BOOK_ID, bookId.toString())
      } catch (error) {
        console.error('保存当前图书状态失败:', error)
      }
    } catch (error) {
      console.error('获取图书详情失败:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  async function fetchBookmarks(bookId: number) {
    try {
      bookmarks.value = await bookApi.getBookmarks(bookId)
    } catch (error) {
      console.error('获取书签失败:', error)
      throw error
    }
  }

  function setSelectedCategory(category: string) {
    selectedCategory.value = category
    // 保存到 localStorage
    try {
      if (category) {
        localStorage.setItem(STORAGE_KEYS.SELECTED_CATEGORY, category)
      } else {
        localStorage.removeItem(STORAGE_KEYS.SELECTED_CATEGORY)
      }
    } catch (error) {
      console.error('保存分类状态失败:', error)
    }
  }

  async function scanBooks(update: boolean = false) {
    loading.value = true
    try {
      const result = await bookApi.scanBooks(update)
      await fetchBooks()
      await fetchCategories()
      return result
    } catch (error) {
      console.error('扫描图书失败:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  async function addBookmark(data: { page_number?: number; position?: string; note?: string }) {
    if (!currentBook.value) return
    try {
      const bookmark = await bookApi.createBookmark(currentBook.value.id, data)
      bookmarks.value.unshift(bookmark)
    } catch (error) {
      console.error('添加书签失败:', error)
      throw error
    }
  }

  async function removeBookmark(bookmarkId: number) {
    try {
      await bookApi.deleteBookmark(bookmarkId)
      bookmarks.value = bookmarks.value.filter(b => b.id !== bookmarkId)
    } catch (error) {
      console.error('删除书签失败:', error)
      throw error
    }
  }

  function clearCurrentBook() {
    currentBook.value = null
    bookmarks.value = []
    // 清除 localStorage 中的当前图书ID
    try {
      localStorage.removeItem(STORAGE_KEYS.CURRENT_BOOK_ID)
    } catch (error) {
      console.error('清除当前图书状态失败:', error)
    }
  }

  // 恢复上一次的图书（在应用启动时调用）
  async function restoreLastBook() {
    try {
      const saved = loadFromStorage()
      if (saved.currentBookId) {
        // 先确保图书列表已加载
        if (books.value.length === 0) {
          await fetchBooks()
        }
        // 检查图书是否还存在
        const bookExists = books.value.some(book => book.id === saved.currentBookId)
        if (bookExists) {
          await fetchBook(saved.currentBookId)
        } else {
          // 如果图书不存在，清除保存的ID
          localStorage.removeItem(STORAGE_KEYS.CURRENT_BOOK_ID)
        }
      }
    } catch (error) {
      console.error('恢复上次图书失败:', error)
    }
  }

  return {
    // 状态
    books,
    categories,
    currentBook,
    bookmarks,
    selectedCategory,
    loading,
    // 计算属性
    filteredBooks,
    categoryList,
    // 方法
    fetchBooks,
    fetchCategories,
    fetchBook,
    fetchBookmarks,
    setSelectedCategory,
    scanBooks,
    addBookmark,
    removeBookmark,
    clearCurrentBook,
    restoreLastBook,
  }
})

