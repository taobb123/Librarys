<template>
  <div class="library-view">
    <!-- 隐藏时显示的浮动按钮 -->
    <button
      v-if="!showSidebar"
      @click="showSidebar = true"
      class="sidebar-toggle-btn"
      title="显示图书目录"
    >
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M3 12h18M3 6h18M3 18h18"/>
      </svg>
    </button>
    
    <transition name="sidebar-slide">
      <div v-show="showSidebar" class="sidebar">
        <BookList @close="showSidebar = false" />
      </div>
    </transition>
    
    <div class="reader-area">
      <BookReader />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import BookList from '@/components/BookList.vue'
import BookReader from '@/components/BookReader.vue'
import { useBookStore } from '@/stores/bookStore'

const bookStore = useBookStore()
const showSidebar = ref(true)

onMounted(async () => {
  // 初始化加载数据
  try {
    await Promise.all([
      bookStore.fetchCategories(),
      bookStore.fetchBooks(),
    ])
  } catch (error) {
    console.error('初始化失败:', error)
    // 即使API调用失败，也显示界面
  }
})
</script>

<style scoped>
.library-view {
  height: 100vh;
  display: flex;
  overflow: hidden;
  position: relative;
}

.sidebar {
  width: 350px;
  min-width: 300px;
  max-width: 400px;
  border-right: 1px solid #ddd;
  overflow: hidden;
  position: relative;
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
  position: absolute;
  top: 16px;
  left: 16px;
  width: 48px;
  height: 48px;
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

.sidebar-toggle-btn:hover {
  background: rgba(66, 185, 131, 1);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
  transform: scale(1.1);
}

.reader-area {
  flex: 1;
  overflow: hidden;
}
</style>

