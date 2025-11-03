import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Book, Category, Bookmark } from '@/api/books'
import * as bookApi from '@/api/books'

export const useBookStore = defineStore('book', () => {
  // 状态
  const books = ref<Book[]>([])
  const categories = ref<Category>({})
  const currentBook = ref<Book | null>(null)
  const bookmarks = ref<Bookmark[]>([])
  const selectedCategory = ref<string>('')
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
  }
})

