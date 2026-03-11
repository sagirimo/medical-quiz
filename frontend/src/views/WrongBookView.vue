<template>
  <div class="wrong-book-page">
    <!-- 头部 -->
    <div class="header slide-up">
      <button class="back-btn" @click="goBack">
        <span class="back-icon">←</span>
        <span>返回</span>
      </button>
      <h1>
        <span class="header-icon">📚</span>
        错题本
      </h1>
      <div class="header-actions">
        <button class="export-btn" @click="showExport = true" v-if="totalWrong > 0">
          <span>📤</span>
          <span>导出文本</span>
        </button>
      </div>
    </div>

    <!-- 统计概览 -->
    <div class="stats-overview slide-up stagger-1" v-if="totalWrong > 0">
      <div class="stat-card">
        <div class="stat-icon">📝</div>
        <div class="stat-content">
          <span class="stat-num">{{ totalWrong }}</span>
          <span class="stat-label">总错题</span>
        </div>
      </div>
    </div>

    <!-- 科目筛选 -->
    <div class="subject-tabs slide-up stagger-2">
      <button
        :class="['tab', { active: selectedSubject === 'all' }]"
        @click="selectedSubject = 'all'"
      >
        全部 ({{ totalWrong }})
      </button>
      <button
        v-for="subject in subjects"
        :key="subject"
        :class="['tab', { active: selectedSubject === subject }]"
        @click="selectedSubject = subject"
      >
        {{ subject }} ({{ getSubjectWrongCount(subject) }})
      </button>
    </div>

    <!-- 错题列表 -->
    <transition-group name="list" tag="div" class="wrong-list" v-if="filteredWrongQuestions.length > 0">
      <div
        v-for="(question, index) in filteredWrongQuestions"
        :key="question.id"
        class="wrong-item slide-up"
        :class="`stagger-${Math.min(index + 3, 8)}`"
      >
        <!-- 左侧红色边条 -->
        <div class="card-accent"></div>

        <div class="item-header">
          <span class="chapter-tag">{{ question.chapter }}</span>
          <span class="subject-tag">{{ question.subject }}</span>
          <button class="remove-btn" @click="removeWrong(question.id)" title="移除">
            <span>✕</span>
          </button>
        </div>

        <p class="question-text">{{ question.question }}</p>

        <div class="options">
          <div
            v-for="(text, letter) in question.options"
            :key="letter"
            :class="['option', {
              correct: letter === question.correctAnswer,
              wrong: letter === question.answer
            }]"
          >
            <span class="option-letter">{{ letter }}</span>
            <span class="option-text">{{ text }}</span>
            <span class="mark correct-mark" v-if="letter === question.correctAnswer">
              <span class="mark-icon">✓</span> 正确
            </span>
            <span class="mark wrong-mark" v-if="letter === question.answer && letter !== question.correctAnswer">
              <span class="mark-icon">✗</span> 你的答案
            </span>
          </div>
        </div>

        <!-- 错题原因区域 -->
        <div class="reason-section">
          <div class="reason-display" v-if="question.reason">
            <span class="reason-icon">💡</span>
            <div class="reason-content">
              <span class="reason-label">错题原因：</span>
              <span class="reason-text">{{ question.reason }}</span>
            </div>
          </div>
          <button
            class="add-reason-btn"
            v-else
            @click="editingQuestion = question.id"
          >
            <span class="btn-plus">+</span>
            添加错题原因
          </button>

          <div class="reason-edit" v-if="editingQuestion === question.id">
            <textarea
              v-model="reasonText"
              placeholder="输入错题原因，帮助复习..."
              rows="2"
            ></textarea>
            <div class="edit-actions">
              <button class="cancel-btn" @click="cancelEdit">取消</button>
              <button class="save-btn" @click="saveReason(question.id)">
                <span>✓</span> 保存
              </button>
            </div>
          </div>
        </div>
      </div>
    </transition-group>

    <!-- 空状态 -->
    <div class="empty-state fade-in" v-else>
      <div class="empty-icon animate-bounce">🎉</div>
      <h2>太棒了！</h2>
      <p>暂无错题，继续保持！</p>
      <router-link to="/" class="back-home-btn">
        返回首页继续练习
      </router-link>
    </div>

    <!-- 导出弹窗 -->
    <transition name="modal">
      <div class="modal-overlay" v-if="showExport" @click.self="showExport = false">
        <div class="modal scale-in">
          <div class="modal-header">
            <h2>导出错题</h2>
            <button class="modal-close" @click="showExport = false">✕</button>
          </div>
          <textarea
            class="export-text"
            :value="exportText"
            readonly
            ref="exportTextarea"
          ></textarea>
          <div class="modal-actions">
            <button class="copy-btn" @click="copyExport">
              <span>📋</span> 复制到剪贴板
            </button>
            <button class="close-btn" @click="showExport = false">关闭</button>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>


<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useQuizStore } from '../stores/quiz'

const router = useRouter()
const store = useQuizStore()

const subjects = ['内科学', '外科学', '妇产科学', '儿科学']
const selectedSubject = ref('all')
const showExport = ref(false)
const editingQuestion = ref(null)
const reasonText = ref('')
const exportTextarea = ref(null)

const totalWrong = computed(() => Object.keys(store.wrongAnswers).length)

const filteredWrongQuestions = computed(() => {
  let questions = Object.entries(store.wrongAnswers).map(([id, data]) => ({
    id,
    ...data
  }))

  if (selectedSubject.value !== 'all') {
    questions = questions.filter(q => q.subject === selectedSubject.value)
  }

  // 按时间倒序
  questions.sort((a, b) => (b.timestamp || 0) - (a.timestamp || 0))
  return questions
})

const exportText = computed(() => store.getWrongQuestionsText())

const getSubjectWrongCount = (subject) => {
  return store.getWrongQuestionsBySubject(subject).length
}

const goBack = () => {
  router.push('/')
}

const removeWrong = (id) => {
  if (confirm('确定要从错题本移除吗？')) {
    store.removeFromWrongBook(id)
  }
}

const cancelEdit = () => {
  editingQuestion.value = null
  reasonText.value = ''
}

const saveReason = (id) => {
  store.addWrongReason(id, reasonText.value)
  editingQuestion.value = null
  reasonText.value = ''
}

const copyExport = async () => {
  try {
    await navigator.clipboard.writeText(exportText.value)
    alert('已复制到剪贴板！')
  } catch (err) {
    // 降级方案
    exportTextarea.value.select()
    document.execCommand('copy')
    alert('已复制到剪贴板！')
  }
}
</script>


<style scoped>
.wrong-book-page {
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
  padding: 0.5rem 0.875rem;
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

.header-icon {
  font-size: 1.5rem;
}

.header h1 {
  flex: 1;
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--text-primary);
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.export-btn {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.5rem 1rem;
  background: var(--primary);
  color: white;
  border-radius: var(--radius-md);
  font-size: 0.875rem;
  font-weight: 500;
  transition: all var(--transition-base) ease;
}

.export-btn:hover {
  background: var(--primary-dark);
  transform: translateY(-1px);
}

/* 统计概览 */
.stats-overview {
  display: flex;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.stat-card {
  background: var(--bg-card);
  padding: 1rem 1.5rem;
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  gap: 1rem;
  box-shadow: var(--shadow-sm);
}

.stat-icon {
  font-size: 2rem;
}

.stat-content {
  display: flex;
  flex-direction: column;
}

.stat-num {
  font-size: 2rem;
  font-weight: 700;
  color: var(--error);
  line-height: 1;
}

.stat-label {
  font-size: 0.8125rem;
  color: var(--text-secondary);
  margin-top: 0.25rem;
}

/* 科目筛选标签 */
.subject-tabs {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
  overflow-x: auto;
  padding-bottom: 0.5rem;
  scrollbar-width: none;
}

.subject-tabs::-webkit-scrollbar {
  display: none;
}

.tab {
  padding: 0.5rem 1rem;
  background: var(--bg-card);
  border: 2px solid var(--border);
  border-radius: var(--radius-full);
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--text-secondary);
  white-space: nowrap;
  transition: all var(--transition-base) ease;
}

.tab:hover {
  border-color: var(--primary-light);
  color: var(--primary);
}

.tab.active {
  background: var(--primary);
  border-color: var(--primary);
  color: white;
}

/* 错题列表 */
.wrong-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.wrong-item {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: 1.25rem;
  padding-left: 1.5rem;
  position: relative;
  box-shadow: var(--shadow-sm);
  transition: all var(--transition-base) ease;
  opacity: 0;
}

.wrong-item:hover {
  box-shadow: var(--shadow-md);
}

/* 左侧红色边条 */
.card-accent {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 4px;
  background: linear-gradient(180deg, var(--error) 0%, #f97316 100%);
  border-radius: var(--radius-lg) 0 0 var(--radius-lg);
}

.item-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.875rem;
}

.chapter-tag, .subject-tag {
  font-size: 0.75rem;
  padding: 0.25rem 0.625rem;
  border-radius: var(--radius-full);
  font-weight: 500;
}

.chapter-tag {
  background: var(--bg-secondary);
  color: var(--text-secondary);
}

.subject-tag {
  background: var(--primary-light);
  color: var(--primary-dark);
}

.remove-btn {
  margin-left: auto;
  width: 28px;
  height: 28px;
  background: var(--bg-secondary);
  color: var(--text-muted);
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all var(--transition-base) ease;
}

.remove-btn:hover {
  background: var(--error-light);
  color: var(--error);
}

.question-text {
  font-size: 1rem;
  line-height: 1.7;
  margin-bottom: 1rem;
  color: var(--text-primary);
  font-weight: 500;
}

/* 选项样式 */
.options {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.option {
  display: flex;
  align-items: flex-start;
  gap: 0.625rem;
  padding: 0.625rem 0.875rem;
  border-radius: var(--radius-md);
  font-size: 0.875rem;
  background: var(--bg-secondary);
  transition: all var(--transition-base) ease;
}

.option.correct {
  background: var(--success-light);
}

.option.wrong {
  background: var(--error-light);
}

.option-letter {
  font-weight: 700;
  color: var(--text-secondary);
  flex-shrink: 0;
  width: 18px;
}

.option-text {
  flex: 1;
  color: var(--text-primary);
}

.mark {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.75rem;
  font-weight: 600;
  padding: 0.125rem 0.5rem;
  border-radius: var(--radius-full);
}

.mark-icon {
  font-size: 0.625rem;
}

.correct-mark {
  background: var(--success);
  color: white;
}

.wrong-mark {
  background: var(--error);
  color: white;
}

/* 错题原因区域 */
.reason-section {
  border-top: 1px solid var(--border-light);
  padding-top: 0.875rem;
}

.reason-display {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  font-size: 0.875rem;
}

.reason-icon {
  font-size: 1.25rem;
}

.reason-content {
  flex: 1;
}

.reason-label {
  color: var(--text-secondary);
  font-weight: 500;
}

.reason-text {
  color: var(--error);
  margin-top: 0.25rem;
  display: block;
}

.add-reason-btn {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.5rem 0.875rem;
  border: 2px dashed var(--border);
  background: transparent;
  border-radius: var(--radius-md);
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--text-secondary);
  transition: all var(--transition-base) ease;
}

.add-reason-btn:hover {
  border-color: var(--primary);
  color: var(--primary);
  background: var(--primary-light);
}

.btn-plus {
  font-size: 1rem;
  font-weight: 700;
}

.reason-edit {
  margin-top: 0.75rem;
}

.reason-edit textarea {
  width: 100%;
  padding: 0.75rem;
  border: 2px solid var(--border);
  border-radius: var(--radius-md);
  resize: vertical;
  font-size: 0.875rem;
  font-family: inherit;
  transition: border-color var(--transition-base) ease;
}

.reason-edit textarea:focus {
  outline: none;
  border-color: var(--primary);
}

.edit-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
  margin-top: 0.75rem;
}

.cancel-btn, .save-btn {
  padding: 0.5rem 1rem;
  border-radius: var(--radius-md);
  font-size: 0.875rem;
  font-weight: 500;
  transition: all var(--transition-base) ease;
}

.cancel-btn {
  background: var(--bg-secondary);
  color: var(--text-secondary);
}

.cancel-btn:hover {
  background: var(--bg-primary);
}

.save-btn {
  background: var(--primary);
  color: white;
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.save-btn:hover {
  background: var(--primary-dark);
}

/* 空状态 */
.empty-state {
  text-align: center;
  padding: 4rem 2rem;
}

.empty-icon {
  font-size: 5rem;
  margin-bottom: 1.5rem;
}

.empty-icon.animate-bounce {
  animation: bounce 1s ease-in-out infinite;
}

.empty-state h2 {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 0.5rem;
}

.empty-state p {
  color: var(--text-secondary);
  font-size: 1rem;
  margin-bottom: 1.5rem;
}

.back-home-btn {
  display: inline-flex;
  padding: 0.75rem 1.5rem;
  background: var(--primary);
  color: white;
  border-radius: var(--radius-md);
  font-weight: 500;
  transition: all var(--transition-base) ease;
}

.back-home-btn:hover {
  background: var(--primary-dark);
  transform: translateY(-2px);
}

/* 列表过渡动画 */
.list-enter-active {
  animation: slideUp 0.3s ease-out;
}

.list-leave-active {
  transition: all 0.3s ease;
}

.list-leave-to {
  opacity: 0;
  transform: translateX(-20px);
}

/* 弹窗样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
  z-index: 1000;
}

.modal {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  width: 100%;
  max-width: 600px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  box-shadow: var(--shadow-xl);
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.25rem 1.5rem;
  border-bottom: 1px solid var(--border-light);
}

.modal-header h2 {
  font-size: 1.25rem;
  font-weight: 600;
}

.modal-close {
  width: 32px;
  height: 32px;
  background: var(--bg-secondary);
  border-radius: var(--radius-sm);
  color: var(--text-secondary);
  transition: all var(--transition-base) ease;
}

.modal-close:hover {
  background: var(--error-light);
  color: var(--error);
}

.export-text {
  flex: 1;
  min-height: 300px;
  margin: 1rem 1.5rem;
  padding: 1rem;
  border: 2px solid var(--border);
  border-radius: var(--radius-md);
  font-size: 0.875rem;
  font-family: 'SF Mono', Monaco, monospace;
  resize: none;
  background: var(--bg-secondary);
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  padding: 1rem 1.5rem;
  border-top: 1px solid var(--border-light);
}

.copy-btn, .close-btn {
  padding: 0.625rem 1.25rem;
  border-radius: var(--radius-md);
  font-size: 0.875rem;
  font-weight: 500;
  transition: all var(--transition-base) ease;
}

.copy-btn {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  background: var(--primary);
  color: white;
}

.copy-btn:hover {
  background: var(--primary-dark);
}

.close-btn {
  background: var(--bg-secondary);
  color: var(--text-secondary);
}

.close-btn:hover {
  background: var(--bg-primary);
}

/* 弹窗动画 */
.modal-enter-active .modal {
  animation: scaleIn 0.25s ease-out;
}

.modal-leave-active .modal {
  animation: scaleIn 0.2s ease-out reverse;
}

/* 响应式 */
@media (max-width: 600px) {
  .wrong-book-page {
    padding: 1rem;
  }

  .stat-card {
    padding: 0.875rem 1rem;
  }

  .stat-num {
    font-size: 1.5rem;
  }

  .wrong-item {
    padding: 1rem;
    padding-left: 1.25rem;
  }
}
</style>
