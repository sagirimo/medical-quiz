<template>
  <div class="home">
    <!-- 头部 -->
    <div class="header slide-up">
      <h1>北医题库刷题系统</h1>
      <p class="subtitle">内科 | 外科 | 妇产 | 儿科</p>
    </div>

    <!-- 统计栏 -->
    <div class="stats-bar slide-up stagger-1" v-if="totalWrong > 0">
      <div class="stat-item">
        <div class="stat-icon">📚</div>
        <div class="stat-content">
          <span class="stat-value" :class="{ 'number-bounce': animateStats }">{{ totalWrong }}</span>
          <span class="stat-label">错题本</span>
        </div>
      </div>
      <div class="stat-divider"></div>
      <div class="stat-item">
        <div class="stat-icon">🔥</div>
        <div class="stat-content">
          <span class="stat-value streak-value" :class="{ 'number-bounce': animateStats }">{{ maxStreak }}</span>
          <span class="stat-label">最高连击</span>
        </div>
      </div>
    </div>

    <!-- 科目卡片网格 -->
    <div class="subject-grid">
      <div
        v-for="(subject, index) in subjects"
        :key="subject"
        class="subject-card slide-up"
        :class="[getSubjectClass(subject), `stagger-${index + 2}`]"
        @click="selectSubject(subject)"
      >
        <!-- 左侧彩色边条 -->
        <div class="card-accent" :class="getSubjectClass(subject)"></div>

        <!-- 错题徽章 -->
        <div class="wrong-badge" v-if="getWrongCount(subject) > 0">
          <span class="wrong-count">{{ getWrongCount(subject) }}</span>
          <span class="wrong-label">错题</span>
        </div>

        <!-- 科目图标 -->
        <div class="subject-icon">{{ getSubjectIcon(subject) }}</div>

        <!-- 科目名称 -->
        <h2>{{ subject }}</h2>

        <!-- 题目数量 -->
        <p class="question-count">{{ getQuestionCount(subject) }} 题</p>

        <!-- 进度条 -->
        <div class="progress-container" v-if="getProgress(subject) > 0">
          <div class="progress-bar">
            <div
              class="progress-fill animated"
              :style="{ width: getProgress(subject) + '%' }"
            ></div>
          </div>
          <span class="progress-text">{{ getProgress(subject) }}%</span>
        </div>
      </div>
    </div>

    <!-- 底部操作栏 -->
    <div class="action-bar slide-up stagger-6">
      <router-link to="/wrong-book" class="action-btn wrong-book-btn">
        <span class="btn-icon">📚</span>
        <span class="btn-text">错题本</span>
      </router-link>
    </div>
  </div>
</template>


<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useQuizStore } from '../stores/quiz'

const router = useRouter()
const store = useQuizStore()

const subjects = ['内科学', '外科学', '妇产科学', '儿科学']
const animateStats = ref(false)

const totalWrong = computed(() => Object.keys(store.wrongAnswers).length)
const maxStreak = computed(() => store.maxStreak)

const subjectData = ref({})

onMounted(async () => {
  // 加载所有科目的题目数量
  for (const subject of subjects) {
    const data = await store.loadQuestions(subject)
    if (data) {
      let count = 0
      Object.values(data).forEach(chapter => {
        count += chapter.length
      })
      subjectData.value[subject] = count
    }
  }

  // 触发数字动画
  setTimeout(() => {
    animateStats.value = true
  }, 500)
})

const getQuestionCount = (subject) => {
  return subjectData.value[subject] || '...'
}

const getWrongCount = (subject) => {
  return store.getWrongQuestionsBySubject(subject).length
}

const getProgress = (subject) => {
  const total = subjectData.value[subject]
  if (!total) return 0
  const answered = store.getAnsweredCountBySubject(subject)
  return Math.round((answered / total) * 100)
}

const getSubjectIcon = (subject) => {
  const icons = {
    '内科学': '❤️',
    '外科学': '🔪',
    '妇产科学': '👶',
    '儿科学': '🍼'
  }
  return icons[subject] || '📖'
}

const getSubjectClass = (subject) => {
  const classes = {
    '内科学': 'subject-internal',
    '外科学': 'subject-surgery',
    '妇产科学': 'subject-gyn',
    '儿科学': 'subject-ped'
  }
  return classes[subject] || ''
}

const selectSubject = (subject) => {
  router.push(`/subject/${encodeURIComponent(subject)}`)
}
</script>


<style scoped>
.home {
  max-width: 900px;
  margin: 0 auto;
  padding: 2rem;
  min-height: 100vh;
}

/* 头部样式 */
.header {
  text-align: center;
  margin-bottom: 2rem;
}

.header h1 {
  font-size: 2rem;
  font-weight: 700;
  background: linear-gradient(135deg, var(--primary) 0%, var(--success) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 0.5rem;
}

.subtitle {
  color: var(--text-secondary);
  font-size: 1rem;
  font-weight: 500;
}

/* 统计栏 */
.stats-bar {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 2rem;
  margin-bottom: 2rem;
  padding: 1.25rem;
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.stat-icon {
  font-size: 1.5rem;
}

.stat-content {
  display: flex;
  flex-direction: column;
}

.stat-value {
  font-size: 1.75rem;
  font-weight: 700;
  color: var(--primary);
  line-height: 1.2;
}

.stat-value.streak-value {
  color: var(--error);
}

.stat-label {
  font-size: 0.75rem;
  color: var(--text-secondary);
}

.stat-divider {
  width: 1px;
  height: 40px;
  background: var(--border);
}

/* 科目卡片网格 */
.subject-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.subject-card {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: 1.5rem;
  padding-left: 1.75rem;
  cursor: pointer;
  transition: all var(--transition-base) ease;
  position: relative;
  overflow: hidden;
  box-shadow: var(--shadow-sm);
  opacity: 0;
}

.subject-card:hover {
  transform: translateY(-6px);
  box-shadow: var(--shadow-lg);
}

/* 卡片左侧彩色边条 */
.card-accent {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 4px;
  transition: width var(--transition-base) ease;
}

.subject-card:hover .card-accent {
  width: 6px;
}

.card-accent.subject-internal {
  background: linear-gradient(180deg, #ef4444 0%, #f97316 100%);
}

.card-accent.subject-surgery {
  background: linear-gradient(180deg, #3b82f6 0%, #06b6d4 100%);
}

.card-accent.subject-gyn {
  background: linear-gradient(180deg, #ec4899 0%, #f472b6 100%);
}

.card-accent.subject-ped {
  background: linear-gradient(180deg, #10b981 0%, #34d399 100%);
}

/* 错题徽章 */
.wrong-badge {
  position: absolute;
  top: 1rem;
  right: 1rem;
  display: flex;
  align-items: center;
  gap: 0.25rem;
  background: var(--error-light);
  color: var(--error-dark);
  padding: 0.25rem 0.625rem;
  border-radius: var(--radius-full);
  font-size: 0.75rem;
  font-weight: 600;
}

.wrong-count {
  font-weight: 700;
}

.wrong-label {
  opacity: 0.8;
}

/* 科目图标 */
.subject-icon {
  font-size: 2.5rem;
  margin-bottom: 0.5rem;
  transition: transform var(--transition-base) ease;
}

.subject-card:hover .subject-icon {
  transform: scale(1.1);
}

/* 科目名称 */
.subject-card h2 {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 0.25rem;
}

/* 题目数量 */
.question-count {
  color: var(--text-secondary);
  font-size: 0.875rem;
  margin-bottom: 0.75rem;
}

/* 进度条容器 */
.progress-container {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-top: 0.5rem;
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
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--primary);
  min-width: 36px;
}

/* 底部操作栏 */
.action-bar {
  text-align: center;
}

.action-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.875rem 2rem;
  border-radius: var(--radius-full);
  font-weight: 600;
  text-decoration: none;
  transition: all var(--transition-base) ease;
}

.wrong-book-btn {
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  color: white;
  box-shadow: var(--shadow-md);
}

.wrong-book-btn:hover {
  transform: translateY(-2px) scale(1.02);
  box-shadow: var(--shadow-lg);
}

.wrong-book-btn:active {
  transform: translateY(0) scale(0.98);
}

.btn-icon {
  font-size: 1.25rem;
}

.btn-text {
  font-size: 0.9375rem;
}

/* 响应式设计 */
@media (max-width: 600px) {
  .home {
    padding: 1rem;
  }

  .subject-grid {
    grid-template-columns: 1fr;
    gap: 1rem;
  }

  .stats-bar {
    gap: 1.5rem;
  }

  .stat-value {
    font-size: 1.5rem;
  }
}
</style>
