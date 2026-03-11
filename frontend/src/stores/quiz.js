import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useQuizStore = defineStore('quiz', () => {
  // 题库数据
  const questionsData = ref({})

  // 加载状态
  const isLoading = ref(false)

  // 当前做题状态（会话级别）
  const currentSubject = ref('')
  const currentChapter = ref('')
  const currentQuestions = ref([])
  const currentIndex = ref(0)
  const sessionAnswers = ref({}) // 本次会话的答案 { questionId: answer }
  const quizMode = ref('chapter')

  // 会话统计（每次开始新练习重置）
  const streak = ref(0)
  const maxStreak = ref(0)
  const sessionCorrect = ref(0)
  const sessionAnswered = ref(0)

  // 持久化数据
  const wrongAnswers = ref({}) // 错题本 { questionId: { answer, reason, ... } }
  const questionHistory = ref({}) // 做题历史 { questionId: { userAnswer, isCorrect, timestamp } }
  const chapterProgress = ref({}) // 章节进度 { subject_chapter: { answered: [ids], correct: [ids] } }

  // 从本地存储加载
  const loadFromStorage = () => {
    const saved = localStorage.getItem('quiz-state')
    if (saved) {
      const data = JSON.parse(saved)
      wrongAnswers.value = data.wrongAnswers || {}
      maxStreak.value = data.maxStreak || 0
      questionHistory.value = data.questionHistory || {}
      chapterProgress.value = data.chapterProgress || {}
    }
  }

  // 保存到本地存储
  const saveToStorage = () => {
    localStorage.setItem('quiz-state', JSON.stringify({
      wrongAnswers: wrongAnswers.value,
      maxStreak: maxStreak.value,
      questionHistory: questionHistory.value,
      chapterProgress: chapterProgress.value
    }))
  }

  // 加载题库数据
  const loadQuestions = async (subject) => {
    isLoading.value = true
    try {
      // 优先从后端 API 加载（支持持久化修改）
      const response = await fetch(`${API_BASE}/questions/${encodeURIComponent(subject)}`)
      if (response.ok) {
        const data = await response.json()
        questionsData.value[subject] = data
        return data
      }
      // 如果后端不可用，回退到本地文件
      const fallbackResponse = await fetch(`/${subject}.json`)
      const data = await fallbackResponse.json()
      questionsData.value[subject] = data
      return data
    } catch (error) {
      console.error('加载题库失败:', error)
      // 尝试从本地加载
      try {
        const fallbackResponse = await fetch(`/${subject}.json`)
        const data = await fallbackResponse.json()
        questionsData.value[subject] = data
        return data
      } catch (e) {
        return null
      }
    } finally {
      isLoading.value = false
    }
  }

  // 获取科目列表
  const subjects = computed(() => Object.keys(questionsData.value))

  // 获取章节列表
  const getChapters = (subject) => {
    return Object.keys(questionsData.value[subject] || {})
  }

  // 获取章节进度
  const getChapterProgress = (subject, chapter) => {
    const key = `${subject}_${chapter}`
    const progress = chapterProgress.value[key] || { answered: [], correct: [] }
    const total = questionsData.value[subject]?.[chapter]?.length || 0
    const answered = progress.answered?.length || 0
    const correct = progress.correct?.length || 0
    return {
      total,
      answered,
      correct,
      percent: total > 0 ? Math.round((answered / total) * 100) : 0,
      accuracy: answered > 0 ? Math.round((correct / answered) * 100) : 0
    }
  }

  // 开始章节模式答题
  const startChapterQuiz = (subject, chapter) => {
    currentSubject.value = subject
    currentChapter.value = chapter
    quizMode.value = 'chapter'
    currentQuestions.value = questionsData.value[subject]?.[chapter] || []
    currentIndex.value = 0
    sessionAnswers.value = {}
    sessionCorrect.value = 0
    sessionAnswered.value = 0
    streak.value = 0
  }

  // 开始随机模式答题
  const startRandomQuiz = (subject, chapters) => {
    currentSubject.value = subject
    currentChapter.value = '随机模式'
    quizMode.value = 'random'

    let allQuestions = []
    chapters.forEach(ch => {
      const chapterQuestions = questionsData.value[subject]?.[ch] || []
      allQuestions = allQuestions.concat(chapterQuestions)
    })

    currentQuestions.value = shuffleArray(allQuestions)
    currentIndex.value = 0
    sessionAnswers.value = {}
    sessionCorrect.value = 0
    sessionAnswered.value = 0
    streak.value = 0
  }

  // 判断题目是否已做过
  const isQuestionAnswered = (questionId) => {
    return questionId in questionHistory.value
  }

  // 获取题目的历史答案
  const getQuestionHistory = (questionId) => {
    return questionHistory.value[questionId]
  }

  // 提交答案
  const submitAnswer = (questionId, answer) => {
    const question = currentQuestions.value.find(q => q.id === questionId)
    if (!question) return null

    const isCorrect = answer === question.answer

    // 更新会话统计
    sessionAnswered.value++
    sessionAnswers.value[questionId] = answer

    if (isCorrect) {
      sessionCorrect.value++
      streak.value++
      if (streak.value > maxStreak.value) {
        maxStreak.value = streak.value
      }
      // 如果之前做错过，从错题本移除
      if (wrongAnswers.value[questionId]) {
        delete wrongAnswers.value[questionId]
      }
    } else {
      streak.value = 0
      // 添加到错题本
      wrongAnswers.value[questionId] = {
        answer,
        subject: question.subject,
        chapter: question.chapter,
        question: question.question,
        correctAnswer: question.answer,
        options: question.options,
        timestamp: Date.now()
      }
    }

    // 记录做题历史
    questionHistory.value[questionId] = {
      userAnswer: answer,
      isCorrect,
      timestamp: Date.now()
    }

    // 更新章节进度
    if (quizMode.value === 'chapter') {
      const key = `${question.subject}_${question.chapter}`
      if (!chapterProgress.value[key]) {
        chapterProgress.value[key] = { answered: [], correct: [] }
      }
      const progress = chapterProgress.value[key]
      if (!progress.answered.includes(questionId)) {
        progress.answered.push(questionId)
      } else {
        // 重新做题，更新记录
        const idx = progress.answered.indexOf(questionId)
        if (idx > -1) {
          progress.answered.splice(idx, 1)
        }
        progress.answered.push(questionId)
      }
      // 更新正确列表
      if (isCorrect) {
        if (!progress.correct.includes(questionId)) {
          progress.correct.push(questionId)
        }
      } else {
        const idx = progress.correct.indexOf(questionId)
        if (idx > -1) {
          progress.correct.splice(idx, 1)
        }
      }
    }

    saveToStorage()

    return {
      isCorrect,
      correctAnswer: question.answer,
      streak: streak.value
    }
  }

  // 清空章节做题记录
  const clearChapterProgress = (subject, chapter) => {
    const key = `${subject}_${chapter}`
    const questions = questionsData.value[subject]?.[chapter] || []

    // 删除该章节所有题目的历史记录
    questions.forEach(q => {
      delete questionHistory.value[q.id]
    })

    // 删除章节进度
    delete chapterProgress.value[key]

    saveToStorage()
  }

  // 清空科目所有做题记录
  const clearSubjectProgress = (subject) => {
    const chapters = getChapters(subject)
    chapters.forEach(ch => {
      clearChapterProgress(subject, ch)
    })
  }

  // 下一题
  const nextQuestion = () => {
    if (currentIndex.value < currentQuestions.value.length - 1) {
      currentIndex.value++
    }
  }

  // 上一题
  const prevQuestion = () => {
    if (currentIndex.value > 0) {
      currentIndex.value--
    }
  }

  // 添加错题原因
  const addWrongReason = (questionId, reason) => {
    if (wrongAnswers.value[questionId]) {
      wrongAnswers.value[questionId].reason = reason
      saveToStorage()
    }
  }

  // 从错题本移除
  const removeFromWrongBook = (questionId) => {
    delete wrongAnswers.value[questionId]
    saveToStorage()
  }

  // 获取当前题目
  const currentQuestion = computed(() => {
    return currentQuestions.value[currentIndex.value] || null
  })

  // 当前会话进度
  const progress = computed(() => {
    if (currentQuestions.value.length === 0) return 0
    const answered = Object.keys(sessionAnswers.value).length
    return Math.round((answered / currentQuestions.value.length) * 100)
  })

  // 当前会话正确率
  const accuracy = computed(() => {
    if (sessionAnswered.value === 0) return 0
    return Math.round((sessionCorrect.value / sessionAnswered.value) * 100)
  })

  // 获取科目下的错题
  const getWrongQuestionsBySubject = (subject) => {
    return Object.entries(wrongAnswers.value)
      .filter(([_, data]) => data.subject === subject)
      .map(([id, data]) => ({ id, ...data }))
  }

  // 获取科目已答题数
  const getAnsweredCountBySubject = (subject) => {
    let count = 0
    const chapters = getChapters(subject)
    chapters.forEach(chapter => {
      const key = `${subject}_${chapter}`
      const progress = chapterProgress.value[key]
      if (progress?.answered) {
        count += progress.answered.length
      }
    })
    return count
  }

  // 获取所有错题的文本格式
  const getWrongQuestionsText = () => {
    let text = '# 错题整理\n\n'
    const subjects = ['内科学', '外科学', '妇产科学', '儿科学']

    subjects.forEach(subject => {
      const wrongs = getWrongQuestionsBySubject(subject)
      if (wrongs.length === 0) return

      text += `## ${subject}\n\n`

      const byChapter = {}
      wrongs.forEach(q => {
        if (!byChapter[q.chapter]) byChapter[q.chapter] = []
        byChapter[q.chapter].push(q)
      })

      Object.entries(byChapter).forEach(([chapter, questions]) => {
        text += `### ${chapter}\n\n`
        questions.forEach((q, i) => {
          text += `${i + 1}. ${q.question}\n`
          Object.entries(q.options).forEach(([key, value]) => {
            const marker = key === q.correctAnswer ? '✓' : (key === q.answer ? '✗' : '')
            text += `   ${key}. ${value} ${marker}\n`
          })
          text += `   正确答案: ${q.correctAnswer}\n`
          if (q.reason) {
            text += `   错题原因: ${q.reason}\n`
          }
          text += '\n'
        })
      })
    })

    return text
  }

  // 快速刷题模式
  const fastMode = ref(false)

  // API 基础地址
  const API_BASE = 'http://localhost:3001/api'

  // 保存题库到服务器
  const saveToServer = async (subject) => {
    try {
      const response = await fetch(`${API_BASE}/questions/${encodeURIComponent(subject)}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(questionsData.value[subject])
      })
      const result = await response.json()
      if (!result.success) {
        console.error('保存失败:', result.error)
        return false
      }
      return true
    } catch (err) {
      console.error('保存失败:', err)
      return false
    }
  }

  // 编辑题目
  const editQuestion = async (questionId, newData) => {
    const question = currentQuestions.value.find(q => q.id === questionId)
    if (!question) return false

    // 更新当前会话中的题目
    Object.assign(question, newData)

    // 更新题库数据
    const subject = question.subject
    const chapter = question.chapter
    const chapterQuestions = questionsData.value[subject]?.[chapter]
    if (chapterQuestions) {
      const idx = chapterQuestions.findIndex(q => q.id === questionId)
      if (idx > -1) {
        chapterQuestions[idx] = { ...question, ...newData }
      }
    }

    // 更新错题本中的数据
    if (wrongAnswers.value[questionId]) {
      wrongAnswers.value[questionId] = {
        ...wrongAnswers.value[questionId],
        question: newData.question || question.question,
        options: newData.options || question.options,
        correctAnswer: newData.answer || question.answer
      }
      saveToStorage()
    }

    // 保存到服务器
    await saveToServer(subject)

    return true
  }

  // 添加新题目（在当前题目后面插入）
  const addQuestion = async (afterId, newQuestion) => {
    const currentIdx = currentQuestions.value.findIndex(q => q.id === afterId)
    if (currentIdx === -1) return false

    // 生成唯一 ID
    const newId = `${currentSubject.value}_${currentChapter.value}_${Date.now()}`
    newQuestion.id = newId
    newQuestion.subject = currentSubject.value
    newQuestion.chapter = currentChapter.value

    // 插入到当前题目后面
    currentQuestions.value.splice(currentIdx + 1, 0, newQuestion)

    // 更新题库数据
    if (!questionsData.value[currentSubject.value]) {
      questionsData.value[currentSubject.value] = {}
    }
    if (!questionsData.value[currentSubject.value][currentChapter.value]) {
      questionsData.value[currentSubject.value][currentChapter.value] = []
    }
    const chapterQuestions = questionsData.value[currentSubject.value][currentChapter.value]
    const insertIdx = chapterQuestions.findIndex(q => q.id === afterId)
    if (insertIdx > -1) {
      chapterQuestions.splice(insertIdx + 1, 0, newQuestion)
    } else {
      chapterQuestions.push(newQuestion)
    }

    // 保存到服务器
    await saveToServer(currentSubject.value)

    return true
  }

  // 导出当前科目题库为 JSON
  const exportSubjectJSON = (subject) => {
    const data = questionsData.value[subject]
    if (!data) return null
    return JSON.stringify(data, null, 2)
  }

  // 工具函数
  function shuffleArray(array) {
    const newArray = [...array]
    for (let i = newArray.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [newArray[i], newArray[j]] = [newArray[j], newArray[i]]
    }
    return newArray
  }

  // 初始化
  loadFromStorage()

  return {
    // 状态
    questionsData,
    isLoading,
    currentSubject,
    currentChapter,
    currentQuestions,
    currentIndex,
    sessionAnswers,
    wrongAnswers,
    questionHistory,
    chapterProgress,
    quizMode,
    streak,
    maxStreak,
    sessionCorrect,
    sessionAnswered,

    // 计算属性
    subjects,
    currentQuestion,
    progress,
    accuracy,

    // 方法
    loadQuestions,
    getChapters,
    getChapterProgress,
    startChapterQuiz,
    startRandomQuiz,
    submitAnswer,
    nextQuestion,
    prevQuestion,
    addWrongReason,
    removeFromWrongBook,
    clearChapterProgress,
    clearSubjectProgress,
    isQuestionAnswered,
    getQuestionHistory,
    getWrongQuestionsBySubject,
    getWrongQuestionsText,
    getAnsweredCountBySubject,
    // 新增
    fastMode,
    editQuestion,
    addQuestion,
    exportSubjectJSON,
    saveToServer
  }
})
