<template>
  <div class="problem-reader">
    <div v-if="!problem" class="empty-reader">
      <div class="empty-content">
        <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"/>
          <path d="M12 16v-4M12 8h.01"/>
        </svg>
        <p>请从左侧列表选择一个问题</p>
      </div>
    </div>
    
    <div v-else class="problem-content">
      <div class="problem-header">
        <h2 class="problem-title">{{ problem.title }}</h2>
        <div class="problem-actions">
          <button @click="handleAnalyze" class="analyze-btn" :disabled="analyzing">
            {{ analyzing ? '分析中...' : 'AI分析' }}
          </button>
          <button @click="showTagEditor = true" class="tag-edit-btn">编辑标签</button>
        </div>
      </div>
      
      <div class="problem-meta">
        <span v-if="problem.category" class="category-badge">{{ problem.category }}</span>
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
      
      <div class="problem-body">
        <div class="content-section">
          <h3>问题内容</h3>
          <div class="content-text" v-html="formatContent(problem.content)"></div>
        </div>
        
        <div v-if="analysis" class="analysis-section">
          <h3>AI分析结果</h3>
          <div class="analysis-content" v-html="formatContent(analysis)"></div>
        </div>
      </div>
      
      <!-- 标签编辑对话框 -->
      <div v-if="showTagEditor" class="tag-editor-overlay" @click.self="showTagEditor = false">
        <div class="tag-editor-dialog" @click.stop>
          <h3>编辑标签</h3>
          <div class="tag-options">
            <label v-for="tag in ['兴趣', '待办', '已完成']" :key="tag" class="tag-option">
              <input
                type="checkbox"
                :value="tag"
                v-model="editingTags"
              />
              <span>{{ tag }}</span>
            </label>
          </div>
          <div class="dialog-actions">
            <button @click="showTagEditor = false" class="cancel-btn">取消</button>
            <button @click="saveTags" class="save-btn">保存</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import * as problemApi from '@/api/problems'
import type { Problem } from '@/api/problems'

const props = defineProps<{
  problem: Problem | null
}>()

const analysis = ref<string>('')
const analyzing = ref(false)
const showTagEditor = ref(false)
const editingTags = ref<string[]>([])

watch(() => props.problem, (newProblem) => {
  if (newProblem) {
    analysis.value = ''
    editingTags.value = [...(newProblem.tags || [])]
  }
}, { immediate: true })

function getTagClass(tag: string): string {
  const tagClasses: { [key: string]: string } = {
    '兴趣': 'tag-interest',
    '待办': 'tag-todo',
    '已完成': 'tag-completed'
  }
  return tagClasses[tag] || ''
}

function formatContent(content: string): string {
  if (!content) return ''
  // 简单的换行处理
  return content.replace(/\n/g, '<br>')
}

async function handleAnalyze() {
  if (!props.problem) return
  
  analyzing.value = true
  try {
    const result = await problemApi.analyzeProblem(props.problem.id)
    analysis.value = result.analysis
  } catch (error: any) {
    alert('AI分析失败：' + (error?.message || '未知错误'))
  } finally {
    analyzing.value = false
  }
}

async function saveTags() {
  if (!props.problem) return
  
  try {
    await problemApi.updateProblemTags(props.problem.id, editingTags.value)
    // 触发父组件更新（通过emit事件）
    emit('tagsUpdated', editingTags.value)
    showTagEditor.value = false
  } catch (error: any) {
    alert('保存标签失败：' + (error?.message || '未知错误'))
  }
}

const emit = defineEmits<{
  tagsUpdated: [tags: string[]]
}>()
</script>

<style scoped>
.problem-reader {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: white;
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

.empty-content svg {
  margin-bottom: 16px;
  opacity: 0.5;
}

.problem-content {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.problem-header {
  padding: 20px 24px;
  border-bottom: 1px solid #eee;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.problem-title {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
  color: #333;
  flex: 1;
}

.problem-actions {
  display: flex;
  gap: 8px;
}

.analyze-btn,
.tag-edit-btn {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.analyze-btn {
  background: #42b983;
  color: white;
}

.analyze-btn:hover:not(:disabled) {
  background: #35a372;
}

.analyze-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.tag-edit-btn {
  background: #f0f0f0;
  color: #333;
}

.tag-edit-btn:hover {
  background: #e0e0e0;
}

.problem-meta {
  padding: 12px 24px;
  border-bottom: 1px solid #eee;
  display: flex;
  align-items: center;
  gap: 12px;
}

.category-badge {
  padding: 4px 12px;
  background: #42b983;
  color: white;
  border-radius: 12px;
  font-size: 12px;
}

.problem-tags {
  display: flex;
  gap: 8px;
}

.tag {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
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

.problem-body {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

.content-section,
.analysis-section {
  margin-bottom: 32px;
}

.content-section h3,
.analysis-section h3 {
  margin: 0 0 16px 0;
  font-size: 18px;
  color: #333;
}

.content-text,
.analysis-content {
  line-height: 1.8;
  color: #666;
  white-space: pre-wrap;
}

.analysis-section {
  border-top: 2px solid #eee;
  padding-top: 24px;
}

.tag-editor-overlay {
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

.tag-editor-dialog {
  background: white;
  border-radius: 8px;
  padding: 24px;
  min-width: 300px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
}

.tag-editor-dialog h3 {
  margin: 0 0 20px 0;
  font-size: 18px;
}

.tag-options {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 24px;
}

.tag-option {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.tag-option input {
  width: 18px;
  height: 18px;
  cursor: pointer;
}

.dialog-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.cancel-btn,
.save-btn {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.cancel-btn {
  background: #f0f0f0;
  color: #333;
}

.cancel-btn:hover {
  background: #e0e0e0;
}

.save-btn {
  background: #42b983;
  color: white;
}

.save-btn:hover {
  background: #35a372;
}
</style>

