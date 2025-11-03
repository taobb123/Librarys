<template>
  <div class="system-config">
    <button 
      ref="toggleButtonRef"
      @click="showConfig = !showConfig" 
      class="config-toggle-btn" 
      title="系统配置"
    >
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="3"/>
        <path d="M12 1v6m0 6v6M5.64 5.64l4.24 4.24m4.24 4.24l4.24 4.24M1 12h6m6 0h6M5.64 18.36l4.24-4.24m4.24-4.24l4.24-4.24"/>
      </svg>
    </button>
    
    <div v-if="showConfig" ref="panelRef" class="config-panel" @click.stop>
      <div class="config-header">
        <h3>系统配置</h3>
        <button @click="showConfig = false" class="close-btn">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M18 6L6 18M6 6l12 12"/>
          </svg>
        </button>
      </div>
      
      <div class="config-content">
        <div class="config-item">
          <label class="config-label">
            <input type="checkbox" v-model="localVisibility.books" @change="saveConfig" />
            <span>显示图书模块</span>
          </label>
        </div>
        
        <div class="config-item">
          <label class="config-label">
            <input type="checkbox" v-model="localVisibility.problems" @change="saveConfig" />
            <span>显示问题模块</span>
          </label>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import * as configApi from '@/api/config'
import type { ModuleVisibility } from '@/api/config'

const emit = defineEmits<{
  visibilityChange: [visibility: ModuleVisibility]
}>()

const showConfig = ref(false)
const toggleButtonRef = ref<HTMLButtonElement | null>(null)
const panelRef = ref<HTMLDivElement | null>(null)
const localVisibility = ref<ModuleVisibility>({
  books: true,
  problems: true
})

async function loadConfig() {
  try {
    localVisibility.value = await configApi.getModuleVisibility()
    emit('visibilityChange', localVisibility.value)
  } catch (error) {
    console.error('加载配置失败:', error)
  }
}

async function saveConfig() {
  try {
    await configApi.updateModuleVisibility(localVisibility.value)
    emit('visibilityChange', localVisibility.value)
  } catch (error) {
    alert('保存配置失败：' + (error as Error).message)
  }
}

function handleClickOutside(event: MouseEvent) {
  if (!showConfig.value) return
  
  const target = event.target as HTMLElement
  const toggleButton = toggleButtonRef.value
  const panel = panelRef.value
  
  // 如果点击不在按钮和面板上，则关闭配置面板
  if (toggleButton && panel) {
    if (!toggleButton.contains(target) && !panel.contains(target)) {
      showConfig.value = false
    }
  }
}

watch(() => showConfig.value, (isOpen) => {
  if (isOpen) {
    // 延迟添加监听，避免立即触发关闭
    setTimeout(() => {
      document.addEventListener('click', handleClickOutside)
    }, 0)
  } else {
    document.removeEventListener('click', handleClickOutside)
  }
})

watch(() => localVisibility.value, (newVal) => {
  emit('visibilityChange', newVal)
}, { deep: true })

onMounted(() => {
  loadConfig()
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
.system-config {
  position: relative;
  flex-shrink: 0;
}

.config-toggle-btn {
  width: 40px;
  height: 40px;
  background: #42b983;
  color: white;
  border: none;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.config-toggle-btn:hover {
  background: #35a372;
  transform: scale(1.1);
}

.config-panel {
  position: absolute;
  top: 50px;
  right: 0;
  background: white;
  border: 1px solid #ddd;
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
  z-index: 1000;
  min-width: 250px;
}

.config-header {
  padding: 16px;
  border-bottom: 1px solid #eee;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.config-header h3 {
  margin: 0;
  font-size: 16px;
}

.close-btn {
  width: 24px;
  height: 24px;
  padding: 0;
  background: transparent;
  border: none;
  cursor: pointer;
  color: #666;
}

.config-content {
  padding: 16px;
}

.config-item {
  margin-bottom: 12px;
}

.config-label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.config-label input[type="checkbox"] {
  width: 18px;
  height: 18px;
  cursor: pointer;
}
</style>

