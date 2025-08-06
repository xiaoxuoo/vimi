<template>
  <div class="app-container">
    <!-- 方向选择界面 -->
    <div v-if="!selectedDirection" class="direction-selection">
      <div class="title-container">
        <h2 class="exam-title">专业能力测评系统</h2>
        <div class="title-decoration"></div>
      </div>
      <p class="exam-subtitle">请选择您的考试方向</p>
      
      <div class="direction-buttons">
        <button 
          v-for="dir in directions" 
          :key="dir" 
          @click="selectDirection(dir)"
          :class="{ active: dir === selectedDirection }"
          class="direction-btn"
        >
          <span class="btn-icon">{{ getDirectionIcon(dir) }}</span>
          <span class="btn-text">{{ dir }}</span>
          <span class="btn-hover-effect"></span>
        </button>
      </div>
      
      <div class="selection-tip">
        <i class="tip-icon">💡</i>
        <span>请从上方选择一个考试方向开始答题</span>
      </div>
    </div>

    <!-- 答题界面 -->
    <div v-if="selectedDirection && !showResults && questions.length" class="question-view">
      <div class="progress-container">
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: progressPercentage + '%' }"></div>
        </div>
        <span class="progress-text">第 {{ currentQuestionIndex + 1 }} 题 / 共 {{ questions.length }} 题</span>
      </div>
      
      <div class="question-card">
        <div class="question-header">
          <div class="question-tag">{{ currentQuestion.type === 'choice' ? '选择题' : '简答题' }}</div>
          <h3 class="question-title">{{ currentQuestion.content }}</h3>
        </div>
        
        <!-- 选择题 -->
        <div v-if="currentQuestion.type === 'choice'" class="options-container">
          <label 
            v-for="(optText, optKey) in currentQuestion.options" 
            :key="optKey" 
            class="option-item"
            :class="{ selected: userAnswers[currentQuestion.id] === optKey }"
          >
            <input
              type="radio"
              :name="'q' + currentQuestion.id"
              :value="optKey"
              v-model="userAnswers[currentQuestion.id]"
              required
              class="option-input"
            />
            <span class="option-marker"></span>
            <span class="option-content">
              <span class="option-key">{{ optKey }}.</span>
              <span class="option-text">{{ optText }}</span>
            </span>
          </label>
        </div>
        
        <!-- 简答题 -->
        <div v-else class="text-answer-container">
          <textarea
            v-model="userAnswers[currentQuestion.id]"
            placeholder="请输入您的答案..."
            rows="4"
            class="answer-textarea"
            required
          ></textarea>
        </div>
      </div>
      
      <div class="navigation-buttons">
        <button 
          v-if="currentQuestionIndex > 0"
          @click="prevQuestion" 
          class="nav-btn prev-btn"
        >
          <span class="btn-icon">←</span>
          <span>上一题</span>
        </button>
        
        <button 
          @click="nextQuestion" 
          :disabled="!userAnswers[currentQuestion.id]"
          class="nav-btn next-btn"
        >
          <span>{{ isLastQuestion ? '提交答案' : '下一题' }}</span>
          <span class="btn-icon">→</span>
        </button>
      </div>
    </div>

    <!-- 结果界面 -->
    <div v-if="showResults" class="result-view">
       <!-- 顶部按钮 -->
      <div class="interview-btn-top-container">
        <button @click="goToInterviewTest" class="interview-btn">
          <span class="btn-icon">💬</span>
          <span>进入面试</span>
        </button>
      </div>
      <div class="result-header">
        <div class="result-header-content">
          <h2 class="result-title">答题结果</h2>
          <div class="result-stats">
            <div class="stat-item correct">
              <span class="stat-value">{{ correctCount }}</span>
              <span class="stat-label">正确</span>
            </div>
            <div class="stat-item total">
              <span class="stat-value">{{ questions.length }}</span>
              <span class="stat-label">总数</span>
            </div>
            <div class="stat-item score">
              <span class="stat-value">{{ score }}%</span>
              <span class="stat-label">得分</span>
            </div>
          </div>
        </div>
        <div class="result-decoration"></div>
      </div>
      
      <div class="result-details">
        <div 
          v-for="(result, index) in results" 
          :key="result.question_id" 
          class="result-card"
          :class="{ correct: result.correct }"
        >
          <div class="question-review">
            <h3 class="review-question">
              <span class="question-number">第 {{ index + 1 }} 题：</span>
              {{ getQuestionById(result.question_id).content }}
            </h3>
            
            <div class="answer-section">
              <div class="user-answer">
                <span class="answer-label">您的答案：</span>
                <span class="answer-content">{{ getUserAnswerText(result) }}</span>
              </div>
              
              <div class="correct-answer" v-if="!result.correct">
                <span class="answer-label">正确答案：</span>
                <span class="answer-content">{{ getCorrectAnswerText(result) }}</span>
              </div>
            </div>
            
            <div class="result-status">
              <i :class="result.correct ? 'icon-correct' : 'icon-incorrect'">
                {{ result.correct ? '✓' : '✗' }}
              </i>
              <span>{{ result.correct ? '回答正确' : '回答错误' }}</span>
              <span v-if="result.user_answer === '未回答'" class="missed-answer">(未回答)</span>
            </div>
          </div>
        </div>
      </div>
      
      <button @click="resetQuiz" class="retry-btn">
        <span class="btn-icon">🔄</span>
        <span>重新测试</span>
      </button>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-overlay">
      <div class="loading-spinner"></div>
      <span>加载中...</span>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      directions: ['人工智能', '大数据', '物联网'],
      selectedDirection: '',
      questions: [],
      currentQuestionIndex: 0,
      userAnswers: {},
      results: [],
      score: 0,
      correctCount: 0,
      loading: false,
      showResults: false,
      aiAnalysisLoading: false,
      aiAnalysisResult: null
    }
  },
  computed: {
    currentQuestion() {
      return this.questions[this.currentQuestionIndex] || {}
    },
    isLastQuestion() {
      return this.currentQuestionIndex === this.questions.length - 1
    },
    progressPercentage() {
      return ((this.currentQuestionIndex + 1) / this.questions.length) * 100
    }
  },
  methods: {
    getDirectionIcon(dir) {
      const icons = {
        '人工智能': '🤖',
        '大数据': '📊',
        '物联网': '🌐'
      }
      return icons[dir] || '📝'
    },
    selectDirection(dir) {
      this.selectedDirection = dir
      this.results = []
      this.userAnswers = {}
      this.score = 0
      this.correctCount = 0
      this.currentQuestionIndex = 0
      this.showResults = false
      this.aiAnalysisResult = null
      this.aiAnalysisLoading = false
      this.loadQuestions()
    },
    goToInterviewTest() {
      if (!this.results || this.results.length === 0) return

      const user = JSON.parse(localStorage.getItem('user') || '{}')
      const userId = user.id

      if (!userId) {
        alert('用户未登录')
        return
      }

      const payload = {
        user_id: userId,
        direction: this.selectedDirection,
        answers: this.results.map(r => ({
          question_id: r.question_id,
          question_content: this.getQuestionById(r.question_id).content,
          user_answer: r.user_answer,
          user_answer_text: this.getUserAnswerText(r)
        }))
      }

      fetch('/api/ask/analyze_answers', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      }).catch(err => {
        console.warn('后台智能分析失败（不影响跳转）:', err)
      })

      this.$router.push({ name: 'InterviewTest' })
    },
    loadQuestions() {
      this.loading = true
      fetch(`/api/ask/questions?direction=${encodeURIComponent(this.selectedDirection)}`)
        .then(res => {
          if (!res.ok) throw new Error('获取题目失败')
          return res.json()
        })
        .then(data => {
          this.questions = data
          this.loading = false
        })
        .catch(err => {
          console.error('获取题目错误:', err)
          alert('获取题目失败，请检查网络连接或联系管理员')
          this.loading = false
        })
    },
    prevQuestion() {
      if (this.currentQuestionIndex > 0) {
        this.currentQuestionIndex--
      }
    },
    nextQuestion() {
      if (!this.userAnswers[this.currentQuestion.id]) {
        alert('请完成当前题目')
        return
      }
      if (this.isLastQuestion) {
        this.submitAnswers()
      } else {
        this.currentQuestionIndex++
      }
    },
    submitAnswers() {
      this.loading = true
      this.aiAnalysisResult = null
      this.aiAnalysisLoading = false

      const user = JSON.parse(localStorage.getItem('user') || '{}')
      const userId = user.id

      if (!userId) {
        alert('用户未登录或用户ID无效')
        this.loading = false
        return
      }

      const answersPayload = this.questions.map(q => ({
        question_id: q.id,
        answer: this.userAnswers[q.id] || '未回答'
      }))

      fetch('/api/ask/submit_answers', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, answers: answersPayload })
      })
        .then(res => {
          if (!res.ok) throw new Error('提交答案失败')
          return res.json()
        })
        .then(data => {
          this.results = data.results.map(result => {
            const question = this.getQuestionById(result.question_id)
            return {
              ...result,
              user_answer: this.userAnswers[result.question_id] || '未回答',
              correct: result.correct !== undefined ? result.correct : false
            }
          })
          this.score = data.score || 0
          this.correctCount = this.results.filter(r => r.correct).length
          this.loading = false
          this.showResults = true
        })
        .catch(err => {
          console.error('提交答案错误:', err)
          alert('提交答案失败，请检查网络连接或联系管理员')
          this.loading = false
        })
    },
    clearAnalysis() {
      this.aiAnalysisResult = null
    },
    getQuestionById(id) {
      const question = this.questions.find(q => q.id === id) || {}
      return {
        type: 'text',
        options: {},
        ...question
      }
    },
    getUserAnswerText(result) {
      if (!result.user_answer || result.user_answer === '未回答') {
        return '未回答'
      }
      if (result.user_answer_text) {
        return `${result.user_answer}. ${result.user_answer_text}`
      }
      const question = this.getQuestionById(result.question_id)
      if (question.type === 'choice') {
        return `${result.user_answer}. ${question.options[result.user_answer] || '无效选项'}`
      }
      return result.user_answer
    },
    getCorrectAnswerText(result) {
      if (result.correct_answer_text) {
        return `${result.correct_answer}. ${result.correct_answer_text}`
      }
      const question = this.getQuestionById(result.question_id)
      if (question.type === 'choice') {
        return `${result.correct_answer}. ${question.options[result.correct_answer] || '无效选项'}`
      }
      return result.reference_answer || '无标准答案'
    },
    resetQuiz() {
      this.results = []
      this.userAnswers = {}
      this.score = 0
      this.correctCount = 0
      this.questions = []
      this.selectedDirection = ''
      this.currentQuestionIndex = 0
      this.showResults = false
      this.aiAnalysisResult = null
      this.aiAnalysisLoading = false
    }
  }
}
</script>

<style scoped>
/* 基础样式 */
:root {
  --primary-color: #4361ee;
  --primary-light: #e6e9ff;
  --secondary-color: #3a0ca3;
  --success-color: #4cc9f0;
  --error-color: #f72585;
  --warning-color: #f8961e;
  --light-color: #f8f9fa;
  --dark-color: #212529;
  --gray-color: #6c757d;
  --border-radius: 12px;
  --box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
  --transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
}

* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
  color: #000; /* 所有文字强制黑色 */
}

body {
  font-family: 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif;
  line-height: 1.6;
  background: linear-gradient(135deg, #f5f7fa 0%, #e4e8f0 100%);
}

.app-container {
  max-width: 800px;
  margin: 2rem auto;
  padding: 2rem;
  background-color: white;
  border-radius: var(--border-radius);
  box-shadow: var(--box-shadow);
  position: relative;
  overflow: hidden;
}

/* 方向选择界面 */
.direction-selection {
  text-align: center;
  position: relative;
  z-index: 1;
}

.title-container {
  position: relative;
  margin-bottom: 1.5rem;
}

.exam-title {
  font-size: 2.2rem;
  margin-bottom: 0.5rem;
  background: linear-gradient(90deg, #4361ee, #3a0ca3);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  display: inline-block;
  position: relative;
  z-index: 2;
}

.title-decoration {
  position: absolute;
  top: -15px;
  left: 50%;
  transform: translateX(-50%);
  width: 120px;
  height: 120px;
  background: radial-gradient(circle, rgba(67, 97, 238, 0.1) 0%, rgba(67, 97, 238, 0) 70%);
  z-index: 1;
}

.exam-subtitle {
  font-size: 1.2rem;
  margin-bottom: 2rem;
  color: #555;
  position: relative;
  display: inline-block;
}

.exam-subtitle::after {
  content: '';
  position: absolute;
  bottom: -8px;
  left: 50%;
  transform: translateX(-50%);
  width: 50px;
  height: 3px;
  background: linear-gradient(90deg, #4361ee, #3a0ca3);
  border-radius: 3px;
}

.direction-buttons {
  display: flex;
  justify-content: center;
  gap: 1.5rem;
  flex-wrap: wrap;
  margin: 2rem 0;
}

.direction-btn {
  position: relative;
  padding: 1.2rem 2rem;
  background-color: white;
  border: none;
  border-radius: var(--border-radius);
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: var(--transition);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  align-items: center;
  min-width: 160px;
}

.direction-btn:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.15);
}

.direction-btn.active {
  background-color: var(--primary-color);
  color: white;
}

.btn-icon {
  font-size: 2rem;
  margin-bottom: 0.5rem;
  transition: var(--transition);
}

.btn-text {
  position: relative;
  z-index: 2;
}

.btn-hover-effect {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, rgba(67, 97, 238, 0.1) 0%, rgba(67, 97, 238, 0) 100%);
  opacity: 0;
  transition: var(--transition);
}

.direction-btn:hover .btn-hover-effect {
  opacity: 1;
}

.direction-btn.active .btn-icon,
.direction-btn.active .btn-text {
  color: white;
}

.selection-tip {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  margin-top: 1.5rem;
  padding: 0.8rem 1.5rem;
  background-color: #f8f9fa;
  border-radius: 50px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.tip-icon {
  margin-right: 0.8rem;
  font-size: 1.2rem;
}

/* 答题界面 */
.question-view {
  margin-top: 1.5rem;
  animation: fadeIn 0.5s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

.progress-container {
  margin-bottom: 2rem;
  position: relative;
}

.progress-bar {
  height: 10px;
  background-color: #e9ecef;
  border-radius: 5px;
  overflow: hidden;
  margin-bottom: 0.5rem;
  box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.1);
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #4361ee, #3a0ca3);
  transition: width 0.5s ease;
  position: relative;
  overflow: hidden;
}

.progress-fill::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(90deg, 
    rgba(255, 255, 255, 0.3) 0%, 
    rgba(255, 255, 255, 0.5) 50%, 
    rgba(255, 255, 255, 0.3) 100%);
  animation: progressShine 2s infinite;
}

@keyframes progressShine {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
}

.progress-text {
  font-size: 0.9rem;
  color: #666;
  display: block;
  text-align: right;
}

.question-card {
  background-color: white;
  border-radius: var(--border-radius);
  padding: 2rem;
  margin-bottom: 2rem;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  border: 1px solid rgba(0, 0, 0, 0.05);
  position: relative;
  overflow: hidden;
}

.question-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 4px;
  height: 100%;
  background: linear-gradient(to bottom, #4361ee, #3a0ca3);
}

.question-header {
  margin-bottom: 1.5rem;
  position: relative;
}

.question-tag {
  position: absolute;
  top: -10px;
  right: -10px;
  background: linear-gradient(135deg, #4361ee, #3a0ca3);
  color: white;
  padding: 0.3rem 1rem;
  border-radius: 50px;
  font-size: 0.8rem;
  font-weight: bold;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.question-title {
  font-size: 1.3rem;
  font-weight: 600;
  line-height: 1.5;
  padding-right: 1rem;
}

/* 选项样式 */
.options-container {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.option-item {
  display: flex;
  align-items: center;
  padding: 1.2rem;
  border: 1px solid #e9ecef;
  border-radius: var(--border-radius);
  cursor: pointer;
  transition: var(--transition);
  background-color: white;
  position: relative;
  overflow: hidden;
}

.option-item:hover {
  border-color: var(--primary-color);
  box-shadow: 0 4px 12px rgba(67, 97, 238, 0.1);
  transform: translateX(5px);
}

.option-item.selected {
  border-color: var(--primary-color);
  background-color: rgba(67, 97, 238, 0.05);
}

.option-item.selected::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 3px;
  height: 100%;
  background-color: var(--primary-color);
}

.option-input {
  position: absolute;
  opacity: 0;
}

.option-marker {
  display: inline-block;
  width: 20px;
  height: 20px;
  border: 2px solid #adb5bd;
  border-radius: 50%;
  margin-right: 1.2rem;
  position: relative;
  transition: var(--transition);
  flex-shrink: 0;
}

.option-item.selected .option-marker {
  border-color: var(--primary-color);
  background-color: var(--primary-color);
}

.option-item.selected .option-marker::after {
  content: '';
  position: absolute;
  top: 4px;
  left: 4px;
  width: 8px;
  height: 8px;
  background-color: white;
  border-radius: 50%;
}

.option-content {
  display: flex;
  align-items: center;
}

.option-key {
  font-weight: bold;
  margin-right: 0.8rem;
  color: var(--primary-color);
}

.option-text {
  color: #000;
}

/* 简答题样式 */
.text-answer-container {
  margin-top: 1.5rem;
  position: relative;
}

.answer-textarea {
  width: 100%;
  padding: 1.2rem;
  border: 1px solid #e9ecef;
  border-radius: var(--border-radius);
  font-family: inherit;
  font-size: 1rem;
  transition: var(--transition);
  resize: vertical;
  min-height: 120px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.answer-textarea:focus {
  outline: none;
  border-color: var(--primary-color);
  box-shadow: 0 0 0 3px rgba(67, 97, 238, 0.2);
}

.answer-textarea::placeholder {
  color: #adb5bd;
}

/* 导航按钮 */
.navigation-buttons {
  display: flex;
  justify-content: space-between;
  margin-top: 2rem;
}

.nav-btn {
  padding: 0.8rem 1.8rem;
  border: none;
  border-radius: 50px;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: var(--transition);
  display: flex;
  align-items: center;
  gap: 0.5rem;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.nav-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  box-shadow: none;
}

.prev-btn {
  background-color: white;
  color: var(--primary-color);
  border: 1px solid var(--primary-color);
}

.prev-btn:not(:disabled):hover {
  background-color: #f0f2ff;
  transform: translateX(-3px);
}

.next-btn {
  background: linear-gradient(90deg, #4361ee, #3a0ca3);
  color: white;
}

.next-btn:not(:disabled):hover {
  transform: translateX(3px);
  box-shadow: 0 6px 12px rgba(67, 97, 238, 0.3);
}

.btn-icon {
  font-size: 1.2rem;
}

/* 结果界面 */
.result-view {
  margin-top: 1.5rem;
  animation: fadeIn 0.5s ease;
}

.interview-btn-top-container {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 1rem;
}

.interview-btn {
  padding: 0.8rem 1.8rem;
  background: linear-gradient(90deg, #4cc9f0, #4361ee);
  color: white;
  border: none;
  border-radius: 50px;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: var(--transition);
  display: flex;
  align-items: center;
  gap: 0.5rem;
  box-shadow: 0 4px 12px rgba(76, 201, 240, 0.3);
}

.interview-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(76, 201, 240, 0.4);
}

.result-header {
  background: linear-gradient(135deg, #4361ee, #3a0ca3);
  color: white;
  padding: 2rem;
  border-radius: var(--border-radius) var(--border-radius) 0 0;
  position: relative;
  overflow: hidden;
}

.result-header-content {
  position: relative;
  z-index: 2;
}

.result-decoration {
  position: absolute;
  top: 0;
  right: 0;
  width: 200px;
  height: 100%;
  background: radial-gradient(circle at center, rgba(255, 255, 255, 0.1) 0%, transparent 70%);
}

.result-title {
  font-size: 1.8rem;
  margin-bottom: 1.5rem;
  text-align: center;
  position: relative;
  display: inline-block;
  left: 50%;
  transform: translateX(-50%);
}

.result-title::after {
  content: '';
  position: absolute;
  bottom: -10px;
  left: 50%;
  transform: translateX(-50%);
  width: 60px;
  height: 3px;
  background-color: white;
  border-radius: 3px;
}

.result-stats {
  display: flex;
  justify-content: center;
  gap: 3rem;
  margin-top: 2rem;
}

.stat-item {
  text-align: center;
  min-width: 100px;
  position: relative;
  padding: 0 1rem;
}

.stat-item::after {
  content: '';
  position: absolute;
  top: 50%;
  right: -1.5rem;
  transform: translateY(-50%);
  width: 1px;
  height: 40px;
  background-color: rgba(255, 255, 255, 0.3);
}

.stat-item:last-child::after {
  display: none;
}

.stat-value {
  display: block;
  font-size: 2.2rem;
  font-weight: bold;
  margin-bottom: 0.3rem;
}

.stat-label {
  font-size: 1rem;
  opacity: 0.9;
}

.result-details {
  margin-top: 1rem;
}

.result-card {
  border: 1px solid #e9ecef;
  border-radius: var(--border-radius);
  margin-bottom: 1.5rem;
  overflow: hidden;
  background-color: white;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  transition: var(--transition);
}

.result-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.1);
}

.result-card.correct {
  border-left: 5px solid var(--success-color);
}

.result-card:not(.correct) {
  border-left: 5px solid var(--error-color);
}

.question-review {
  padding: 1.8rem;
}

.review-question {
  font-size: 1.2rem;
  margin-bottom: 1.5rem;
  line-height: 1.5;
}

.question-number {
  font-weight: bold;
  color: var(--primary-color);
}

.answer-section {
  margin-bottom: 1.5rem;
}

.answer-label {
  font-weight: 600;
  margin-right: 0.5rem;
  color: #555;
}

.user-answer {
  margin-bottom: 1rem;
  padding: 1rem;
  background-color: #f8f9fa;
  border-radius: var(--border-radius);
}

.correct-answer {
  padding: 1rem;
  background-color: rgba(76, 201, 240, 0.1);
  border-radius: var(--border-radius);
  border-left: 3px solid var(--success-color);
}

.result-status {
  display: flex;
  align-items: center;
  font-weight: 600;
  padding: 0.8rem 1rem;
  border-radius: var(--border-radius);
  gap: 0.8rem;
}

.result-card.correct .result-status {
  background-color: rgba(76, 201, 240, 0.1);
  color: var(--success-color);
}

.result-card:not(.correct) .result-status {
  background-color: rgba(247, 37, 133, 0.1);
  color: var(--error-color);
}

.icon-correct, .icon-incorrect {
  font-size: 1.2rem;
}

.missed-answer {
  margin-left: 0.5rem;
  font-size: 0.9em;
  opacity: 0.8;
}

/* 重新测试按钮 */
.retry-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  padding: 1rem;
  background-color: white;
  border: 1px solid var(--primary-color);
  border-radius: 0 0 var(--border-radius) var(--border-radius);
  font-size: 1.1rem;
  font-weight: 500;
  cursor: pointer;
  transition: var(--transition);
  margin-top: 1.5rem;
  gap: 0.8rem;
}

.retry-btn:hover {
  background-color: var(--primary-color);
  color: white;
  box-shadow: 0 4px 12px rgba(67, 97, 238, 0.3);
}

/* 加载状态 */
.loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(255, 255, 255, 0.9);
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  z-index: 1000;
  backdrop-filter: blur(5px);
}

.loading-spinner {
  width: 60px;
  height: 60px;
  border: 5px solid rgba(67, 97, 238, 0.1);
  border-radius: 50%;
  border-top-color: var(--primary-color);
  animation: spin 1s linear infinite;
  margin-bottom: 1.5rem;
  position: relative;
}

.loading-spinner::after {
  content: '';
  position: absolute;
  top: -5px;
  left: -5px;
  right: -5px;
  bottom: -5px;
  border: 5px solid transparent;
  border-radius: 50%;
  border-top-color: rgba(67, 97, 238, 0.3);
  animation: spin 1.5s linear infinite reverse;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 响应式设计 */
@media (max-width: 768px) {
  .app-container {
    padding: 1.5rem;
    margin: 1rem;
    border-radius: 12px;
  }
  
  .exam-title {
    font-size: 1.8rem;
  }
  
  .direction-buttons {
    flex-direction: column;
    gap: 1rem;
  }
  
  .direction-btn {
    width: 100%;
  }
  
  .result-stats {
    flex-direction: column;
    gap: 1.5rem;
  }
  
  .stat-item {
    text-align: left;
    min-width: auto;
    padding: 0;
  }
  
  .stat-item::after {
    display: none;
  }
  
  .question-card {
    padding: 1.5rem;
  }
  
  .navigation-buttons {
    flex-direction: column-reverse;
    gap: 1rem;
  }
  
  .nav-btn {
    width: 100%;
    justify-content: center;
  }
  
  .prev-btn {
    order: 2;
  }
  
  .next-btn {
    order: 1;
  }
}
</style>