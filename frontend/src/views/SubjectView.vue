<template>
  <div class="subject-page">
    <!-- 头部 -->
    <div class="header slide-up">
      <button class="back-btn" @click="goBack">
        <span class="back-icon">←</span>
        <span>返回</span>
      </button>
      <h1>{{ subject }}</h1>
      <button class="clear-all-btn" @click="clearAllProgress" v-if="hasProgress">
        清空记录
      </button>
    </div>

    <!-- 模式切换标签 -->
    <div class="mode-tabs slide-up stagger-1">
      <button
        :class="['tab', { active: mode === 'chapter' }]"
        @click="mode = 'chapter'"
      >
        <span class="tab-icon">📖</span>
        <span>章节模式</span>
      </button>
      <button
        :class="['tab', { active: mode === 'random' }]"
        @click="mode = 'random'"
      >
        <span class="tab-icon">🎲</span>
        <span>随机模式</span>
      </button>
    </div>

    <!-- 章节模式 -->
    <div v-if="mode === 'chapter'" class="chapter-list">
      <div
        v-for="(questions, chapter, index) in chapters"
        :key="chapter"
        class="chapter-card slide-up"
        :class="`stagger-${Math.min(index + 2, 8)}`"
      >
        <!-- 左侧渐变边条 -->
        <div class="card-accent"></div>

        <div class="chapter-header" @click="startChapterQuiz(chapter)">
          <div class="chapter-info">
            <h3>{{ chapter }}</h3>
            <span class="count">{{ questions.length }} 题</span>
          </div>

          <!-- 进度显示 -->
          <div class="chapter-progress-bar">
            <div class="progress-bar">
              <div
                class="progress-fill animated"
                :style="{ width: getChapterProgress(chapter).percent + '%' }"
              ></div>
            </div>
            <span class="progress-text" v-if="getChapterProgress(chapter).answered > 0">
              {{ getChapterProgress(chapter).answered }}/{{ getChapterProgress(chapter).total }}
              <span class="accuracy" :class="getAccuracyClass(chapter)">
                ({{ getChapterProgress(chapter).accuracy }}%)
              </span>
            </span>
          </div>
        </div>

        <div class="chapter-footer">
          <span class="wrong-count" v-if="getChapterWrongCount(chapter) > 0">
            <span class="wrong-icon">⚠️</span>
            {{ getChapterWrongCount(chapter) }} 道错题
          </span>
          <span v-else></span>
          <button
            class="clear-btn"
            v-if="getChapterProgress(chapter).answered > 0"
            @click.stop="clearChapterProgress(chapter)"
          >
            清空记录
          </button>
        </div>
      </div>
    </div>

    <!-- 随机模式 -->
    <div v-else class="random-mode slide-up">
      <p class="hint">选择要练习的章节（可多选）：</p>

      <div class="chapter-checkboxes">
        <label
          v-for="(questions, chapter, index) in chapters"
          :key="chapter"
          class="checkbox-item"
          :class="`stagger-${Math.min(index + 1, 8)}`"
        >
          <input
            type="checkbox"
            :value="chapter"
            v-model="selectedChapters"
          />
          <span class="checkmark">
            <span class="check-icon">✓</span>
          </span>
          <span class="label-text">
            {{ chapter }}
            <span class="question-count-text">({{ questions.length }}题)</span>
            <span v-if="getChapterProgress(chapter).answered > 0" class="chapter-progress-hint">
              已做{{ getChapterProgress(chapter).answered }}题
            </span>
          </span>
        </label>
      </div>

      <div class="selection-info" v-if="selectedChapters.length > 0">
        <span class="selection-icon">✨</span>
        已选择 {{ selectedChapters.length }} 个章节，共 {{ totalSelected }} 题
      </div>

      <button
        class="start-btn"
        :disabled="selectedChapters.length === 0"
        @click="startRandomQuiz"
      >
        <span class="btn-icon">🚀</span>
        开始随机练习
      </button>
    </div>
  </div>
</template>


<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useQuizStore } from '../stores/quiz'

const route = useRoute()
const router = useRouter()
const store = useQuizStore()

const subject = decodeURIComponent(route.params.subject)
const mode = ref('chapter')
const selectedChapters = ref([])
const chapters = ref({})

onMounted(async () => {
  const data = await store.loadQuestions(subject)
  if (data) {
    chapters.value = data
  }
})

const totalSelected = computed(() => {
  let count = 0
  selectedChapters.value.forEach(ch => {
    count += chapters.value[ch]?.length || 0
  })
  return count
})

const hasProgress = computed(() => {
  for (const chapter in chapters.value) {
    if (getChapterProgress(chapter).answered > 0) {
      return true
    }
  }
  return false
})

const getChapterProgress = (chapter) => {
  return store.getChapterProgress(subject, chapter)
}

const getAccuracyClass = (chapter) => {
  const progress = getChapterProgress(chapter)
  if (progress.accuracy >= 80) return 'high'
  if (progress.accuracy >= 60) return 'medium'
  return 'low'
}

const getChapterWrongCount = (chapter) => {
  const wrongs = store.getWrongQuestionsBySubject(subject)
  return wrongs.filter(q => q.chapter === chapter).length
}

const goBack = () => {
  router.push('/')
}

const startChapterQuiz = (chapter) => {
  store.startChapterQuiz(subject, chapter)
  router.push(`/quiz/${encodeURIComponent(subject)}`)
}

const startRandomQuiz = () => {
  store.startRandomQuiz(subject, selectedChapters.value)
  router.push(`/quiz/${encodeURIComponent(subject)}`)
}

const clearChapterProgress = (chapter) => {
  if (confirm(`确定要清空「${chapter}」的做题记录吗？错题本中的错题将保留。`)) {
    store.clearChapterProgress(subject, chapter)
  }
}

const clearAllProgress = () => {
  if (confirm(`确定要清空「${subject}」所有章节的做题记录吗？错题本中的错题将保留。`)) {
    store.clearSubjectProgress(subject)
  }
}
</script>


<style scoped>
.subject-page {
  max-width: 800px;
  margin: 0 auto;
  padding: 1.5rem;
}

/* 头部样式 */
.header {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.back-btn {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.5rem 1rem;
  background: var(--bg-card);
  border-radius: var(--radius-md);
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--text-secondary);
  transition: all var(--transition-base) ease;
  box-shadow: var(--shadow-sm);
}

.back-btn:hover {
  background: var(--bg-secondary);
  color: var(--primary);
}

.back-icon {
  transition: transform var(--transition-base) ease;
}

.back-btn:hover .back-icon {
  transform: translateX(-2px);
}

.header h1 {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--text-primary);
  flex: 1;
}

.clear-all-btn {
  padding: 0.5rem 1rem;
  border: 2px solid var(--error-light);
  background: transparent;
  color: var(--error);
  border-radius: var(--radius-md);
  font-size: 0.875rem;
  font-weight: 500;
  transition: all var(--transition-base) ease;
}

.clear-all-btn:hover {
  background: var(--error);
  border-color: var(--error);
  color: white;
}

/* 模式切换标签 */
.mode-tabs {
  display: flex;
  gap: 0.75rem;
  margin-bottom: 1.5rem;
  padding: 0.25rem;
  background: var(--bg-secondary);
  border-radius: var(--radius-lg);
}

.tab {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  background: transparent;
  border-radius: var(--radius-md);
  font-size: 0.9375rem;
  font-weight: 500;
  color: var(--text-secondary);
  transition: all var(--transition-base) ease;
}

.tab:hover {
  color: var(--text-primary);
}

.tab.active {
  background: var(--bg-card);
  color: var(--primary);
  box-shadow: var(--shadow-sm);
}

.tab-icon {
  font-size: 1.125rem;
}

/* 章节列表 */
.chapter-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.chapter-card {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  overflow: hidden;
  position: relative;
  box-shadow: var(--shadow-sm);
  opacity: 0;
  transition: all var(--transition-base) ease;
}

.chapter-card:hover {
  box-shadow: var(--shadow-md);
}

/* 左侧渐变边条 */
.card-accent {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 4px;
  background: linear-gradient(180deg, var(--primary) 0%, var(--success) 100%);
}

.chapter-card:hover .card-accent {
  width: 5px;
}

.chapter-header {
  padding: 1.25rem 1.5rem;
  padding-left: 1.75rem;
  cursor: pointer;
  transition: background var(--transition-base) ease;
}

.chapter-header:hover {
  background: var(--bg-secondary);
}

.chapter-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
}

.chapter-info h3 {
  font-size: 1.0625rem;
  font-weight: 600;
  color: var(--text-primary);
}

.count {
  color: var(--text-secondary);
  font-size: 0.875rem;
  font-weight: 500;
}

/* 进度条 */
.chapter-progress-bar {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.progress-bar {
  flex: 1;
  height: 6px;
  background: var(--bg-secondary);
  border-radius: var(--radius-full);
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  border-radius: var(--radius-full);
  transition: width var(--transition-slow) ease;
}

.progress-fill.animated {
  background: linear-gradient(
    90deg,
    var(--primary) 0%,
    var(--success) 50%,
    var(--primary) 100%
  );
  background-size: 200% 100%;
  animation: wave 2s linear infinite;
}

.progress-text {
  font-size: 0.8125rem;
  color: var(--text-secondary);
  white-space: nowrap;
  font-weight: 500;
}

.accuracy {
  font-weight: 600;
  margin-left: 0.25rem;
}

.accuracy.high { color: var(--success); }
.accuracy.medium { color: var(--warning); }
.accuracy.low { color: var(--error); }

/* 章节底部 */
.chapter-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 1.5rem;
  padding-left: 1.75rem;
  background: var(--bg-secondary);
  border-top: 1px solid var(--border-light);
}

.wrong-count {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  font-size: 0.8125rem;
  color: var(--error);
  font-weight: 500;
}

.wrong-icon {
  font-size: 0.875rem;
}

.clear-btn {
  padding: 0.375rem 0.875rem;
  border: 1px solid var(--border);
  background: var(--bg-card);
  border-radius: var(--radius-sm);
  font-size: 0.75rem;
  font-weight: 500;
  color: var(--text-secondary);
  transition: all var(--transition-base) ease;
}

.clear-btn:hover {
  border-color: var(--error);
  color: var(--error);
  background: var(--error-light);
}

/* 随机模式 */
.random-mode {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: 1.5rem;
  box-shadow: var(--shadow-sm);
}

.hint {
  color: var(--text-secondary);
  font-size: 0.9375rem;
  margin-bottom: 1.25rem;
  font-weight: 500;
}

.chapter-checkboxes {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  max-height: 300px;
  overflow-y: auto;
  padding-right: 0.5rem;
}

.checkbox-item {
  display: flex;
  align-items: center;
  gap: 0.875rem;
  padding: 0.875rem 1rem;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--transition-base) ease;
}

.checkbox-item:hover {
  background: var(--bg-secondary);
}

.checkbox-item input {
  display: none;
}

/* 自定义复选框 */
.checkmark {
  width: 22px;
  height: 22px;
  border: 2px solid var(--border);
  border-radius: var(--radius-sm);
  transition: all var(--transition-base) ease;
  position: relative;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.checkbox-item:hover .checkmark {
  border-color: var(--primary-light);
}

.checkbox-item input:checked + .checkmark {
  background: var(--primary);
  border-color: var(--primary);
}

.check-icon {
  color: white;
  font-size: 0.75rem;
  font-weight: 700;
  opacity: 0;
  transform: scale(0);
  transition: all var(--transition-fast) ease;
}

.checkbox-item input:checked + .checkmark .check-icon {
  opacity: 1;
  transform: scale(1);
}

.label-text {
  flex: 1;
  font-size: 0.9375rem;
  color: var(--text-primary);
}

.question-count-text {
  color: var(--text-secondary);
  font-size: 0.875rem;
}

.chapter-progress-hint {
  font-size: 0.75rem;
  color: var(--success);
  margin-left: 0.5rem;
  font-weight: 500;
}

/* 选择信息 */
.selection-info {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  margin-top: 1.25rem;
  padding: 0.875rem;
  background: var(--primary-light);
  border-radius: var(--radius-md);
  text-align: center;
  color: var(--primary-dark);
  font-weight: 500;
}

.selection-icon {
  font-size: 1.125rem;
}

/* 开始按钮 */
.start-btn {
  width: 100%;
  margin-top: 1.5rem;
  padding: 1rem;
  border-radius: var(--radius-md);
  background: var(--primary);
  color: white;
  font-size: 1rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  transition: all var(--transition-base) ease;
}

.start-btn:hover:not(:disabled) {
  background: var(--primary-dark);
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.start-btn:active:not(:disabled) {
  transform: translateY(0);
}

.start-btn:disabled {
  background: var(--border);
  cursor: not-allowed;
}

.btn-icon {
  font-size: 1.25rem;
}

/* 响应式 */
@media (max-width: 600px) {
  .subject-page {
    padding: 1rem;
  }

  .header h1 {
    font-size: 1.25rem;
  }

  .clear-all-btn {
    padding: 0.375rem 0.75rem;
    font-size: 0.75rem;
  }
}
</style>
