<template>
  <div class="quiz-page">
    <!-- 顶部进度条 -->
    <div class="progress-header slide-up">
      <button class="back-btn" @click="confirmExit">
        <span class="back-icon">←</span>
        <span>退出</span>
      </button>

      <div class="progress-info">
        <div class="progress-numbers">
          <span class="current-num">{{ currentIndex + 1 }}</span>
          <span class="divider">/</span>
          <span class="total-num">{{ totalQuestions }}</span>
        </div>
        <span class="session-progress" v-if="sessionAnsweredCount > 0">
          本次已答 {{ sessionAnsweredCount }} 题
        </span>
        <div class="progress-bar">
          <div
            class="progress-fill animated"
            :style="{ width: progress + '%' }"
          ></div>
        </div>
      </div>

      <div class="stats">
        <!-- 快速刷题模式开关 -->
        <div class="fast-mode-toggle" @click="toggleFastMode" :class="{ active: store.fastMode }">
          <span class="toggle-label">速刷</span>
          <span class="toggle-icon">{{ store.fastMode ? '⚡' : '○' }}</span>
        </div>
        <div class="accuracy-wrap" :class="accuracyClass">
          <span class="accuracy">{{ accuracy }}%</span>
          <span class="accuracy-label">正确率</span>
        </div>
        <div class="streak-badge" v-if="streak > 0" :class="{ 'streak-hot': streak >= 3 }">
          <span class="streak-icon">🔥</span>
          <span class="streak-num" :class="{ 'number-bounce': streakAnimating }">{{ streak }}</span>
          <span class="streak-text">连击</span>
        </div>
      </div>
    </div>

    <!-- 做题区域 -->
    <div class="quiz-content" v-if="currentQuestion">
      <!-- 题目头部 -->
      <div class="question-header slide-up stagger-1">
        <div class="chapter-tag">{{ currentQuestion.chapter }}</div>
        <div class="question-status" v-if="isQuestionDone">
          <span class="done-badge">已做过</span>
        </div>
      </div>

      <!-- 题目区域 -->
      <div class="question-box slide-up stagger-2" :key="currentQuestion.id">
        <p class="question-text">{{ currentQuestion.question }}</p>
      </div>

      <!-- 选项列表 -->
      <div class="options-list">
        <button
          v-for="(letter, index) in sortedOptionLetters"
          :key="letter"
          class="option-btn"
          :class="[getOptionClass(letter), `stagger-${index + 3}`]"
          :disabled="hasAnsweredCurrent"
          @click="selectOption(letter)"
        >
          <!-- 选项字母 -->
          <span class="option-letter">{{ letter }}</span>

          <!-- 选项文本 -->
          <span class="option-text">{{ currentQuestion.options[letter] }}</span>

          <!-- 正确图标 -->
          <span
            class="option-icon correct-icon"
            v-if="hasAnsweredCurrent && letter === currentQuestion.answer"
          >
            <span class="icon-circle">✓</span>
          </span>

          <!-- 错误图标 -->
          <span
            class="option-icon wrong-icon"
            v-if="hasAnsweredCurrent && letter === selectedAnswer && letter !== currentQuestion.answer"
          >
            <span class="icon-circle">✗</span>
          </span>
        </button>
      </div>

      <!-- 答题反馈 -->
      <transition name="feedback">
        <div v-if="hasAnsweredCurrent && justAnswered" class="feedback-area">
          <div :class="['feedback-message', isCorrect ? 'correct' : 'wrong']">
            <div class="feedback-icon-wrap">
              <span class="feedback-icon">{{ isCorrect ? '🎉' : '😅' }}</span>
            </div>
            <div class="feedback-content">
              <div class="feedback-title">{{ isCorrect ? '答对了！' : '答错了' }}</div>
              <div class="feedback-text">
                {{ isCorrect ? getCorrectMessage() : getWrongMessage() }}
              </div>
            </div>
          </div>
        </div>
      </transition>

      <!-- 导航按钮 -->
      <div class="nav-bar slide-up stagger-7">
        <button
          class="nav-btn"
          :disabled="currentIndex === 0"
          @click="goPrev"
        >
          <span class="nav-icon">←</span>
          <span>上一题</span>
        </button>

        <button
          v-if="currentIndex < totalQuestions - 1"
          class="nav-btn primary"
          @click="goNext"
        >
          <span>下一题</span>
          <span class="nav-icon">→</span>
        </button>

        <button v-else class="nav-btn finish" @click="finishQuiz">
          <span class="nav-icon">✓</span>
          <span>完成练习</span>
        </button>
      </div>

      <!-- 题目管理按钮 -->
      <div class="admin-bar slide-up stagger-8">
        <button class="admin-btn edit-btn" @click="openEditModal">
          <span class="btn-icon">✏️</span>
          <span>修改题目</span>
        </button>
        <button class="admin-btn add-btn" @click="openAddModal">
          <span class="btn-icon">➕</span>
          <span>添加新题</span>
        </button>
        <button class="admin-btn export-btn" @click="exportJSON">
          <span class="btn-icon">📥</span>
          <span>导出题库</span>
        </button>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-else class="empty-state fade-in">
      <div class="empty-icon">📚</div>
      <p>正在加载题目...</p>
    </div>

    <!-- 编辑题目弹窗 -->
    <transition name="modal">
      <div class="modal-overlay" v-if="showEditModal" @click.self="closeEditModal">
        <div class="modal scale-in">
          <div class="modal-header">
            <h2>✏️ 修改题目</h2>
            <button class="modal-close" @click="closeEditModal">✕</button>
          </div>
          <div class="modal-body">
            <div class="form-group">
              <label>题干</label>
              <textarea v-model="editForm.question" rows="3" placeholder="输入题目内容"></textarea>
            </div>
            <div class="form-group" v-for="letter in optionLetters" :key="letter">
              <label>选项 {{ letter }}</label>
              <input type="text" v-model="editForm.options[letter]" :placeholder="`选项 ${letter} 内容`">
            </div>
            <div class="form-group">
              <label>正确答案</label>
              <div class="answer-options">
                <button
                  v-for="letter in optionLetters"
                  :key="letter"
                  :class="['answer-option', { selected: editForm.answer === letter }]"
                  @click="editForm.answer = letter"
                >
                  {{ letter }}
                </button>
              </div>
            </div>
          </div>
          <div class="modal-actions">
            <button class="cancel-btn" @click="closeEditModal">取消</button>
            <button class="save-btn" @click="saveEdit">保存修改</button>
          </div>
        </div>
      </div>
    </transition>

    <!-- 添加题目弹窗 -->
    <transition name="modal">
      <div class="modal-overlay" v-if="showAddModal" @click.self="closeAddModal">
        <div class="modal scale-in">
          <div class="modal-header">
            <h2>➕ 添加新题目</h2>
            <button class="modal-close" @click="closeAddModal">✕</button>
          </div>
          <div class="modal-body">
            <div class="form-group">
              <label>题干</label>
              <textarea v-model="addForm.question" rows="3" placeholder="输入题目内容"></textarea>
            </div>
            <div class="form-group">
              <label>选项数量</label>
              <div class="option-count-btns">
                <button
                  :class="['count-btn', { active: addOptionCount === 4 }]"
                  @click="setAddOptionCount(4)"
                >4 选项</button>
                <button
                  :class="['count-btn', { active: addOptionCount === 5 }]"
                  @click="setAddOptionCount(5)"
                >5 选项</button>
              </div>
            </div>
            <div class="form-group" v-for="letter in getAddOptionLetters()" :key="letter">
              <label>选项 {{ letter }}</label>
              <input type="text" v-model="addForm.options[letter]" :placeholder="`选项 ${letter} 内容`">
            </div>
            <div class="form-group">
              <label>正确答案</label>
              <div class="answer-options">
                <button
                  v-for="letter in getAddOptionLetters()"
                  :key="letter"
                  :class="['answer-option', { selected: addForm.answer === letter }]"
                  @click="addForm.answer = letter"
                >
                  {{ letter }}
                </button>
              </div>
            </div>
          </div>
          <div class="modal-actions">
            <button class="cancel-btn" @click="closeAddModal">取消</button>
            <button class="save-btn" @click="saveAdd">添加题目</button>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>


<script setup>
import { ref, computed, watch, reactive } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useQuizStore } from '../stores/quiz'

const route = useRoute()
const router = useRouter()
const store = useQuizStore()

const subject = decodeURIComponent(route.params.subject)

// 当前题目的答题状态
const selectedAnswer = ref('')
const justAnswered = ref(false)
const isCorrect = ref(false)
const streakAnimating = ref(false)

// 编辑题目弹窗
const showEditModal = ref(false)
const optionLetters = ['A', 'B', 'C', 'D', 'E']
const editForm = reactive({
  question: '',
  options: { A: '', B: '', C: '', D: '', E: '' },
  answer: ''
})

// 添加题目弹窗
const showAddModal = ref(false)
const addOptionCount = ref(4)
const addForm = reactive({
  question: '',
  options: { A: '', B: '', C: '', D: '', E: '' },
  answer: ''
})

// 计算属性
const currentQuestion = computed(() => store.currentQuestion)
const currentIndex = computed(() => store.currentIndex)
const totalQuestions = computed(() => store.currentQuestions.length)
const progress = computed(() => store.progress)
const accuracy = computed(() => store.accuracy)
const streak = computed(() => store.streak)

// 按字母顺序排列的选项字母（确保顺序稳定）
const sortedOptionLetters = computed(() => {
  if (!currentQuestion.value?.options) return []
  // 按 A, B, C, D, E 顺序获取存在的选项
  return optionLetters.filter(letter => letter in currentQuestion.value.options)
})

// 本次会话已答题数
const sessionAnsweredCount = computed(() => Object.keys(store.sessionAnswers).length)

const accuracyClass = computed(() => {
  if (accuracy.value >= 80) return 'high'
  if (accuracy.value >= 60) return 'medium'
  return 'low'
})

// 当前题目是否已做过（在历史记录中）
const isQuestionDone = computed(() => {
  if (!currentQuestion.value) return false
  return store.isQuestionAnswered(currentQuestion.value.id)
})

// 当前题目本次会话是否已答
const hasAnsweredCurrent = computed(() => {
  if (!currentQuestion.value) return false
  return currentQuestion.value.id in store.sessionAnswers
})

// 监听连击数变化
watch(streak, (newVal, oldVal) => {
  if (newVal > oldVal && newVal >= 2) {
    streakAnimating.value = true
    setTimeout(() => {
      streakAnimating.value = false
    }, 300)
  }
})

// 监听题目切换，重置状态
watch(currentIndex, () => {
  selectedAnswer.value = ''
  justAnswered.value = false
  isCorrect.value = false
})

// 也可以监听题目ID变化
watch(() => currentQuestion.value?.id, (newId) => {
  if (newId) {
    selectedAnswer.value = ''
    justAnswered.value = false
    isCorrect.value = false
  }
})

const selectOption = (letter) => {
  if (hasAnsweredCurrent.value) return

  selectedAnswer.value = letter
  justAnswered.value = true

  const result = store.submitAnswer(currentQuestion.value.id, letter)
  isCorrect.value = result.isCorrect

  // 快速刷题模式：答对自动下一题
  if (store.fastMode && result.isCorrect) {
    setTimeout(() => {
      if (currentIndex.value < totalQuestions.value - 1) {
        goNext()
      }
    }, 600)
  }
}

const getOptionClass = (letter) => {
  if (!hasAnsweredCurrent.value) return ''

  if (letter === currentQuestion.value.answer) {
    return 'correct-answer'
  }
  if (letter === selectedAnswer.value && letter !== currentQuestion.value.answer) {
    return 'wrong-answer'
  }
  return ''
}

const goNext = () => {
  selectedAnswer.value = ''
  justAnswered.value = false
  store.nextQuestion()
}

const goPrev = () => {
  selectedAnswer.value = ''
  justAnswered.value = false
  store.prevQuestion()
}

const confirmExit = () => {
  if (confirm('确定要退出吗？本次做题记录已保存。')) {
    router.push('/')
  }
}

const finishQuiz = () => {
  router.push('/')
}

const getCorrectMessage = () => {
  const messages = [
    '太棒了！',
    '完全正确！',
    '继续保持！',
    '真厉害！',
    '答对了！'
  ]
  if (streak.value >= 5) {
    return `${streak.value}连击！太厉害了！`
  }
  return messages[Math.floor(Math.random() * messages.length)]
}

const getWrongMessage = () => {
  const messages = [
    '别灰心，继续加油！',
    '再接再厉！',
    '记住这个知识点哦~',
    '下次一定能答对！'
  ]
  return messages[Math.floor(Math.random() * messages.length)]
}

// 快速刷题模式切换
const toggleFastMode = () => {
  store.fastMode = !store.fastMode
}

// 打开编辑弹窗
const openEditModal = () => {
  if (!currentQuestion.value) return
  editForm.question = currentQuestion.value.question
  editForm.options = { ...currentQuestion.value.options }
  editForm.answer = currentQuestion.value.answer
  showEditModal.value = true
}

const closeEditModal = () => {
  showEditModal.value = false
}

// 保存编辑
const saveEdit = async () => {
  if (!editForm.question.trim()) {
    alert('请输入题干')
    return
  }
  if (!editForm.answer) {
    alert('请选择正确答案')
    return
  }

  const success = await store.editQuestion(currentQuestion.value.id, {
    question: editForm.question,
    options: { ...editForm.options },
    answer: editForm.answer
  })
  closeEditModal()
  if (success) {
    alert('题目已修改并保存到题库！')
  } else {
    alert('修改成功，但保存到服务器失败，请检查服务器是否运行')
  }
}

// 打开添加弹窗
const openAddModal = () => {
  addForm.question = ''
  addForm.options = { A: '', B: '', C: '', D: '', E: '' }
  addForm.answer = ''
  addOptionCount.value = 4
  showAddModal.value = true
}

const closeAddModal = () => {
  showAddModal.value = false
}

const setAddOptionCount = (count) => {
  addOptionCount.value = count
}

const getAddOptionLetters = () => {
  return optionLetters.slice(0, addOptionCount.value)
}

// 保存添加
const saveAdd = async () => {
  if (!addForm.question.trim()) {
    alert('请输入题干')
    return
  }

  const letters = getAddOptionLetters()
  for (const letter of letters) {
    if (!addForm.options[letter]?.trim()) {
      alert(`请输入选项 ${letter} 的内容`)
      return
    }
  }

  if (!addForm.answer) {
    alert('请选择正确答案')
    return
  }

  const options = {}
  letters.forEach(letter => {
    options[letter] = addForm.options[letter]
  })

  const success = await store.addQuestion(currentQuestion.value.id, {
    question: addForm.question,
    options,
    answer: addForm.answer
  })
  closeAddModal()
  if (success) {
    alert('新题目已添加并保存到题库！')
  } else {
    alert('添加成功，但保存到服务器失败，请检查服务器是否运行')
  }
}

// 导出题库 JSON
const exportJSON = () => {
  const subjectName = store.currentSubject
  const jsonStr = store.exportSubjectJSON(subjectName)
  if (!jsonStr) {
    alert('导出失败')
    return
  }

  // 创建下载链接
  const blob = new Blob([jsonStr], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${subjectName}.json`
  a.click()
  URL.revokeObjectURL(url)
}
</script>


<style scoped>
.quiz-page {
  max-width: 700px;
  margin: 0 auto;
  padding: 1rem;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

/* 顶部进度条 */
.progress-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem 1.25rem;
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  margin-bottom: 1.5rem;
  box-shadow: var(--shadow-sm);
}

.back-btn {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.5rem 0.875rem;
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--text-secondary);
  transition: all var(--transition-base) ease;
}

.back-btn:hover {
  background: var(--primary-light);
  color: var(--primary-dark);
}

.back-icon {
  transition: transform var(--transition-base) ease;
}

.back-btn:hover .back-icon {
  transform: translateX(-2px);
}

.progress-info {
  flex: 1;
}

.progress-numbers {
  display: flex;
  align-items: baseline;
  gap: 0.25rem;
  margin-bottom: 0.25rem;
}

.current-num {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--primary);
}

.divider {
  color: var(--text-muted);
  font-weight: 500;
}

.total-num {
  font-size: 0.9375rem;
  color: var(--text-secondary);
}

.session-progress {
  font-size: 0.75rem;
  color: var(--text-muted);
  margin-bottom: 0.5rem;
  display: block;
}

.progress-bar {
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

.stats {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 0.5rem;
}

.accuracy-wrap {
  text-align: right;
  padding: 0.375rem 0.75rem;
  border-radius: var(--radius-md);
  background: var(--bg-secondary);
}

.accuracy-wrap.high {
  background: var(--success-light);
}

.accuracy-wrap.high .accuracy {
  color: var(--success-dark);
}

.accuracy-wrap.medium {
  background: var(--warning-light);
}

.accuracy-wrap.medium .accuracy {
  color: var(--warning);
}

.accuracy-wrap.low {
  background: var(--error-light);
}

.accuracy-wrap.low .accuracy {
  color: var(--error-dark);
}

.accuracy {
  font-weight: 700;
  font-size: 1rem;
  color: var(--text-primary);
}

.accuracy-label {
  display: block;
  font-size: 0.625rem;
  color: var(--text-muted);
  font-weight: 500;
}

.streak-badge {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.25rem 0.625rem;
  background: var(--bg-secondary);
  border-radius: var(--radius-full);
  font-size: 0.8125rem;
  transition: all var(--transition-base) ease;
}

.streak-badge.streak-hot {
  background: linear-gradient(135deg, #fed7aa 0%, #fecaca 100%);
}

.streak-icon {
  font-size: 0.875rem;
}

.streak-num {
  font-weight: 700;
  color: var(--error);
}

.streak-text {
  font-size: 0.75rem;
  color: var(--text-secondary);
}

/* 做题区域 */
.quiz-content {
  flex: 1;
}

.question-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.chapter-tag {
  display: inline-flex;
  align-items: center;
  padding: 0.375rem 0.875rem;
  background: var(--primary-light);
  color: var(--primary-dark);
  border-radius: var(--radius-full);
  font-size: 0.8125rem;
  font-weight: 600;
}

.done-badge {
  padding: 0.375rem 0.625rem;
  background: var(--warning-light);
  color: var(--warning);
  border-radius: var(--radius-sm);
  font-size: 0.75rem;
  font-weight: 600;
}

/* 题目区域 */
.question-box {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: 1.75rem;
  margin-bottom: 1.5rem;
  box-shadow: var(--shadow-sm);
  position: relative;
  overflow: hidden;
}

.question-box::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 4px;
  background: linear-gradient(180deg, var(--primary) 0%, var(--success) 100%);
}

.question-text {
  font-size: 1.125rem;
  line-height: 1.8;
  margin: 0;
  color: var(--text-primary);
  font-weight: 500;
}

/* 选项列表 */
.options-list {
  display: flex;
  flex-direction: column;
  gap: 0.875rem;
}

.option-btn {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  padding: 1rem 1.25rem;
  background: var(--bg-card);
  border: 2px solid var(--border);
  border-radius: var(--radius-md);
  cursor: pointer;
  text-align: left;
  transition: all var(--transition-base) ease;
  position: relative;
  overflow: hidden;
  /* 入场动画 */
  animation: slideUp var(--transition-slow) ease-out forwards;
}

.option-btn:hover:not(:disabled) {
  border-color: var(--primary);
  transform: translateX(4px);
  box-shadow: var(--shadow-md);
}

.option-btn:disabled {
  cursor: default;
}

/* 选项字母 */
.option-letter {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: var(--bg-secondary);
  border-radius: var(--radius-sm);
  font-weight: 700;
  font-size: 0.9375rem;
  color: var(--text-secondary);
  flex-shrink: 0;
  transition: all var(--transition-base) ease;
}

.option-btn:hover:not(:disabled) .option-letter {
  background: var(--primary-light);
  color: var(--primary-dark);
}

/* 正确答案样式 */
.option-btn.correct-answer {
  background: var(--success-light);
  border-color: var(--success);
}

.option-btn.correct-answer .option-letter {
  background: var(--success);
  color: white;
}

/* 错误答案样式 */
.option-btn.wrong-answer {
  background: var(--error-light);
  border-color: var(--error);
  animation: shake 0.4s ease-in-out;
}

.option-btn.wrong-answer .option-letter {
  background: var(--error);
  color: white;
}

.option-text {
  flex: 1;
  line-height: 1.6;
  font-size: 0.9375rem;
  color: var(--text-primary);
}

/* 选项图标 */
.option-icon {
  display: flex;
  align-items: center;
  justify-content: center;
}

.icon-circle {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  font-size: 0.875rem;
  font-weight: 700;
  animation: popIn 0.3s ease-out forwards;
}

.correct-icon .icon-circle {
  background: var(--success);
  color: white;
}

.wrong-icon .icon-circle {
  background: var(--error);
  color: white;
}

/* 反馈区域 */
.feedback-area {
  margin-top: 1.5rem;
}

.feedback-message {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem 1.5rem;
  border-radius: var(--radius-md);
  margin-bottom: 1.5rem;
}

.feedback-message.correct {
  background: var(--success-light);
  border: 2px solid var(--success);
}

.feedback-message.wrong {
  background: var(--error-light);
  border: 2px solid var(--error);
}

.feedback-icon-wrap {
  font-size: 2.5rem;
  animation: bounce 0.5s ease-in-out;
}

.feedback-icon {
  display: block;
}

.feedback-content {
  flex: 1;
}

.feedback-title {
  font-weight: 700;
  font-size: 1.125rem;
  margin-bottom: 0.25rem;
}

.feedback-message.correct .feedback-title {
  color: var(--success-dark);
}

.feedback-message.wrong .feedback-title {
  color: var(--error-dark);
}

.feedback-text {
  font-size: 0.9375rem;
  color: var(--text-secondary);
}

/* 反馈动画过渡 */
.feedback-enter-active {
  animation: slideUp 0.3s ease-out;
}

.feedback-leave-active {
  transition: opacity 0.2s ease;
}

.feedback-leave-to {
  opacity: 0;
}

/* 导航按钮 */
.nav-bar {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  padding: 1rem 0;
  margin-top: 1.5rem;
}

.nav-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.875rem 1.5rem;
  border: 2px solid var(--border);
  background: var(--bg-card);
  border-radius: var(--radius-md);
  font-size: 0.9375rem;
  font-weight: 600;
  color: var(--text-primary);
  transition: all var(--transition-base) ease;
}

.nav-btn:hover:not(:disabled) {
  border-color: var(--primary);
  color: var(--primary);
}

.nav-btn:active:not(:disabled) {
  transform: scale(0.98);
}

.nav-btn.primary {
  background: var(--primary);
  color: white;
  border-color: var(--primary);
}

.nav-btn.primary:hover {
  background: var(--primary-dark);
  border-color: var(--primary-dark);
}

.nav-btn.finish {
  background: var(--success);
  color: white;
  border-color: var(--success);
}

.nav-btn.finish:hover {
  background: var(--success-dark);
  border-color: var(--success-dark);
}

.nav-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.nav-icon {
  font-size: 1rem;
}

/* 空状态 */
.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);
}

.empty-icon {
  font-size: 4rem;
  margin-bottom: 1rem;
  opacity: 0.5;
}

.empty-state p {
  font-size: 1.125rem;
}

/* 响应式 */
@media (max-width: 600px) {
  .quiz-page {
    padding: 0.75rem;
  }

  .progress-header {
    padding: 0.875rem 1rem;
    gap: 0.75rem;
  }

  .question-box {
    padding: 1.25rem;
  }

  .question-text {
    font-size: 1rem;
  }
}

/* 快速刷题模式开关 */
.fast-mode-toggle {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.375rem 0.625rem;
  background: var(--bg-secondary);
  border-radius: var(--radius-full);
  cursor: pointer;
  transition: all var(--transition-base) ease;
  font-size: 0.75rem;
  font-weight: 600;
}

.fast-mode-toggle:hover {
  background: var(--bg-primary);
}

.fast-mode-toggle.active {
  background: linear-gradient(135deg, #fef08a 0%, #fde047 100%);
  color: #854d0e;
}

.toggle-icon {
  font-size: 0.875rem;
}

/* 管理按钮区域 */
.admin-bar {
  display: flex;
  gap: 0.75rem;
  padding: 1rem 0;
  margin-top: 0.5rem;
  border-top: 1px solid var(--border-light);
}

.admin-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  background: var(--bg-secondary);
  border: 2px solid var(--border);
  border-radius: var(--radius-md);
  font-size: 0.8125rem;
  font-weight: 500;
  color: var(--text-secondary);
  transition: all var(--transition-base) ease;
}

.admin-btn:hover {
  border-color: var(--primary);
  color: var(--primary);
  transform: translateY(-2px);
}

.btn-icon {
  font-size: 1rem;
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
  max-width: 560px;
  max-height: 85vh;
  display: flex;
  flex-direction: column;
  box-shadow: var(--shadow-xl);
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.25rem;
  border-bottom: 1px solid var(--border-light);
}

.modal-header h2 {
  font-size: 1.125rem;
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

.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: 1rem 1.25rem;
}

.form-group {
  margin-bottom: 1rem;
}

.form-group label {
  display: block;
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 0.5rem;
}

.form-group textarea,
.form-group input {
  width: 100%;
  padding: 0.75rem;
  border: 2px solid var(--border);
  border-radius: var(--radius-md);
  font-size: 0.9375rem;
  font-family: inherit;
  background: var(--bg-primary);
  color: var(--text-primary);
  transition: border-color var(--transition-base) ease;
}

.form-group textarea:focus,
.form-group input:focus {
  outline: none;
  border-color: var(--primary);
}

.answer-options {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.answer-option {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-secondary);
  border: 2px solid var(--border);
  border-radius: var(--radius-sm);
  font-weight: 700;
  font-size: 1rem;
  transition: all var(--transition-base) ease;
}

.answer-option:hover {
  border-color: var(--primary);
}

.answer-option.selected {
  background: var(--success);
  border-color: var(--success);
  color: white;
}

.option-count-btns {
  display: flex;
  gap: 0.5rem;
}

.count-btn {
  flex: 1;
  padding: 0.625rem 1rem;
  background: var(--bg-secondary);
  border: 2px solid var(--border);
  border-radius: var(--radius-md);
  font-size: 0.875rem;
  font-weight: 500;
  transition: all var(--transition-base) ease;
}

.count-btn:hover {
  border-color: var(--primary);
}

.count-btn.active {
  background: var(--primary);
  border-color: var(--primary);
  color: white;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  padding: 1rem 1.25rem;
  border-top: 1px solid var(--border-light);
}

.cancel-btn,
.save-btn {
  padding: 0.625rem 1.25rem;
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
}

.save-btn:hover {
  background: var(--primary-dark);
}

/* 弹窗动画 */
.modal-enter-active .modal {
  animation: scaleIn 0.25s ease-out;
}

.modal-leave-active .modal {
  animation: scaleIn 0.2s ease-out reverse;
}

@keyframes scaleIn {
  from {
    opacity: 0;
    transform: scale(0.95);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}
</style>
