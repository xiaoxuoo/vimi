<template>
  <div class="app-container">
    <div class="header">
      <h2 class="result-title">📚 历史答题记录</h2>
      <p class="subtitle">回顾你的学习足迹，每一次努力都值得铭记</p>
    </div>

    <div v-if="loading" class="loading-overlay">
      <div class="book-loader">
        <div class="book">
          <div class="page"></div>
          <div class="page"></div>
          <div class="page"></div>
        </div>
        <span>正在翻阅你的答题记录...</span>
      </div>
    </div>

    <div v-if="!loading &&  answers.length === 0" class="empty-state">
      <div class="empty-illustration">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">
          <path d="M96 96v320h320V96H96zm304 304H112V112h288v288z" fill="#ddd"/>
          <path d="M160 160h192v32H160zM160 224h192v32H160zM160 288h192v32H160zM160 352h192v32H160z" fill="#ddd"/>
        </svg>
      </div>
      <p class="empty-text">暂无历史答题记录</p>
      <p class="empty-hint">快去完成一些题目吧！</p>
    </div>

    <div v-if="!loading && answers.length" class="result-container">
      <div 
        v-for="(group, index) in answers" 
        :key="group.analysis_id" 
        class="result-card group-card"
      >
        <div class="group-header">
          <div class="group-summary">
            <span class="group-date">⏱️ {{ formatGroupDate(group.created_at) }}</span>
            <span class="group-stats">
              <span class="correct-count">✅ {{ countCorrect(group.answers) }} 正确</span>
              <span class="incorrect-count">❌ {{ countIncorrect(group.answers) }} 错误</span>
              <span class="total-score">⭐ {{ totalScore(group.answers) }} 分</span>
            </span>
          </div>
          <button class="analysis-btn" @click="toggleAnalysis(index)">
            {{ analysisExpanded.includes(index) ? '隐藏分析报告' : '查看分析报告' }}
          </button>
          <button class="toggle-btn" @click="toggleGroup(index)">
            {{ expandedGroups.includes(index) ? '收起答题详情' : '展开答题详情' }}
          </button>
        </div>

        <!-- 分析报告区 -->
        <transition name="slide">
          <div v-if="analysisExpanded.includes(index)" class="analysis-content">
            <h3>分析报告</h3>
            
            <!-- 左右平均布局容器 -->
            <div class="analysis-layout">
              <!-- 左侧：雷达图 + 3个指标 -->
              <div class="left-section">
                <div class="radar-section">
                  <div class="radar-card">
                    <h4>能力雷达图</h4>
                    <div class="radar-chart-container">
                      <canvas :id="`radarChart-${index}`" width="400" height="400"></canvas>
                    </div>
                  </div>
                </div>
                
                <!-- 左侧3个指标 -->
                <div class="metrics-left">
                  <div 
                    v-for="(metric, metricKey) in getLeftMetrics(group.analysis)" 
                    :key="metricKey" 
                    class="metric-card"
                  >
                    <div class="metric-header">
                      <h4 :style="{ color: getMetricColor(metricKey) }">{{ metricKey }}</h4>
                      <div class="metric-score" :style="{ background: getScoreColor(metric.score) }">
                        {{ metric.score }}
                      </div>
                    </div>
                    <div class="metric-description">
                      {{ metric.description || '暂无描述信息' }}
                    </div>
                  </div>
                </div>
              </div>
              
              <!-- 右侧：3个指标 -->
              <div class="right-section">
                <div 
                  v-for="(metric, metricKey) in getRightMetrics(group.analysis)" 
                  :key="metricKey" 
                  class="metric-card"
                >
                  <div class="metric-header">
                    <h4 :style="{ color: getMetricColor(metricKey) }">{{ metricKey }}</h4>
                    <div class="metric-score" :style="{ background: getScoreColor(metric.score) }">
                      {{ metric.score }}
                    </div>
                  </div>
                  <div class="metric-description">
                    {{ metric.description || '暂无描述信息' }}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </transition>

        <!-- 答题详情区 -->
        <transition name="slide">
          <div v-if="expandedGroups.includes(index)" class="group-details">
            <div 
              v-for="(record, recordIndex) in group.answers" 
              :key="recordIndex" 
              class="answer-item"
              :class="{ correct: record.is_correct, incorrect: !record.is_correct }"
            >
              <div class="question-review">
                <div class="question-header">
                  <span class="question-number">题目 #{{ record.question_id }}</span>
                  <span class="question-meta badge">{{ group.direction }}</span>
                </div>

                <div class="question-content">
                  {{ record.question_content }}
                </div>

                <div class="answer-section">
                  <div class="user-answer">
                    <div class="answer-label">
                      <span class="label-icon">✏️</span>
                      <span>你的答案</span>
                    </div>
                    <div class="answer-content bubble">
                      {{ record.answer }}. {{ record.user_answer_text || '未回答' }}
                    </div>
                  </div>

                  <div class="correct-answer" v-if="!record.is_correct">
                    <div class="answer-label">
                      <span class="label-icon">✅</span>
                      <span>正确答案</span>
                    </div>
                    <div class="answer-content bubble">
                      {{ record.correct_answer }}. {{ record.correct_answer_text || record.reference_answer || '无' }}
                    </div>
                  </div>
                </div>

                <div class="result-status">
                  <div class="status-badge" :class="{ correct: record.is_correct }">
                    <span class="status-icon">{{ record.is_correct ? '🎉' : '💡' }}</span>
                    <span>{{ record.is_correct ? '回答正确' : '回答错误' }}</span>
                  </div>
                  <div class="meta-info">
                    <span class="score">⭐ {{ record.score }}分</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </transition>
      </div>
    </div>

    <button @click="goBack" class="retry-btn">
      <span class="btn-icon">🏠</span>
      <span>返回首页</span>
    </button>
  </div>
</template>

<script>
import Chart from 'chart.js/auto';

export default {
  data() {
    return {
      answers: [],               // 接口返回的答题组数组
      loading: false,
      expandedGroups: [],        // 展开答题详情的组索引数组
      analysisExpanded: [],      // 展开分析报告的组索引数组
      radarCharts: {},           // 存储雷达图实例
      // 为每个指标定义独特颜色（现代科技感配色）
      metricColors: {
        '专业知识水平': '#00ccff',
        '存在的问题': '#ff6b6b',
        '岗位匹配度': '#4cd964',
        '技术能力': '#ffcc00',
        '技能匹配度': '#5ac8fa',
        '逻辑思维能力': '#ff9500'
      }
    }
  },
  created() {
    this.fetchUserAnswers()
  },
  methods: {
    fetchUserAnswers() {
      const user = JSON.parse(localStorage.getItem('user') || '{}')
      const userId = user.id

      if (!userId) {
        this.$notify({
          title: '提示',
          message: '请先登录查看答题记录',
          type: 'warning'
        });
        return
      }

      this.loading = true
      fetch(`/api/ask/user_answers_with_analysis/${userId}`)
        .then(res => res.json())
        .then(data => {
          this.answers = data
          this.loading = false
        })
        .catch(err => {
          console.error('加载用户答题记录失败:', err)
          this.$notify.error({
            title: '错误',
            message: '获取答题记录失败，请稍后重试'
          });
          this.loading = false
        })
    },

    toggleGroup(index) {
      if (this.expandedGroups.includes(index)) {
        this.expandedGroups = this.expandedGroups.filter(i => i !== index)
      } else {
        this.expandedGroups.push(index)
      }
    },

    toggleAnalysis(index) {
      if (this.analysisExpanded.includes(index)) {
        this.analysisExpanded = this.analysisExpanded.filter(i => i !== index)
        // 销毁雷达图实例
        if (this.radarCharts[index]) {
          this.radarCharts[index].destroy();
          this.radarCharts[index] = null;
        }
      } else {
        this.analysisExpanded.push(index)
        // 延迟初始化雷达图，确保DOM已渲染
        setTimeout(() => {
          this.initRadarChart(index);
        }, 300);
      }
    },

    // 提取所有指标
    getFixedMetrics(analysis) {
      const fixedKeys = [
        '专业知识水平',
        '存在的问题',
        '岗位匹配度',
        '技术能力',
        '技能匹配度',
        '逻辑思维能力'
      ];
      
      const result = {};
      fixedKeys.forEach(key => {
        result[key] = {
          description: analysis[key]?.description || '',
          score: analysis[key]?.score || 0
        };
      });
      return result;
    },

    // 左侧3个指标
    getLeftMetrics(analysis) {
      const allMetrics = this.getFixedMetrics(analysis);
      const leftKeys = ['专业知识水平', '岗位匹配度', '技术能力'];
      const result = {};
      leftKeys.forEach(key => {
        result[key] = allMetrics[key];
      });
      return result;
    },

    // 右侧3个指标
    getRightMetrics(analysis) {
      const allMetrics = this.getFixedMetrics(analysis);
      const rightKeys = ['存在的问题', '技能匹配度', '逻辑思维能力'];
      const result = {};
      rightKeys.forEach(key => {
        result[key] = allMetrics[key];
      });
      return result;
    },

    // 初始化雷达图
    initRadarChart(index) {
      const group = this.answers[index];
      const metrics = this.getFixedMetrics(group.analysis);
      const labels = Object.keys(metrics);
      const scores = labels.map(key => metrics[key].score);
      const colors = labels.map(key => this.metricColors[key]);
      
      const ctx = document.getElementById(`radarChart-${index}`).getContext('2d');
      
      // 销毁已有实例
      if (this.radarCharts[index]) {
        this.radarCharts[index].destroy();
      }
      
      // 创建渐变背景
       const gradient = ctx.createLinearGradient(0, 0, 400, 400);
      gradient.addColorStop(0, 'rgba(173, 216, 230, 0.3)'); // 浅蓝透明
      gradient.addColorStop(1, 'rgba(135, 206, 235, 0.1)'); // 更浅的蓝透明
      
      // 创建雷达图
      this.radarCharts[index] = new Chart(ctx, {
        type: 'radar',
        data: {
          labels: labels,
          datasets: [{
            label: '能力评分',
            data: scores,
            backgroundColor: gradient,
           borderColor: 'rgba(0, 0, 0, 0.8)', // 黑色边框
            borderWidth: 2,
            pointBackgroundColor: colors,
           pointBorderColor: '#000',
            pointHoverBackgroundColor: '#fff',
            pointHoverBorderColor: colors,
            pointRadius: 6,
            pointHoverRadius: 8,
            pointShadowColor: 'rgba(0, 0, 0, 0.3)',
            pointShadowBlur: 8,
            pointShadowOffsetX: 2,
            pointShadowOffsetY: 2
          }]
        },
        options: {
          animation: {
            duration: 2000,
            easing: 'easeOutQuart',
            animateRotate: true,
            animateScale: true
          },
          scales: {
            r: {
              angleLines: {
                display: true,
                color: 'rgba(100, 255, 200, 0.3)',
                lineWidth: 2
              },
              grid: {
                color: 'rgba(100, 200, 255, 0.2)',
                lineWidth: 1
              },
              pointLabels: {
                font: {
                  size: 12,
                  weight: 'bold'
                },
                color: labels.map(key => this.metricColors[key]),
                padding: 15
              },
              ticks: {
                backdropColor: 'transparent',
                color: '#888',
                showLabelBackdrop: false
              },
              suggestedMin: 0,
              suggestedMax: 100
            }
          },
          plugins: {
            legend: {
              display: false
            },
            tooltip: {
              backgroundColor: 'rgba(255, 255, 255, 0.9)',
              titleColor: '#333',
              bodyColor: '#666',
              borderColor: 'rgba(0, 0, 0, 0.1)',
              borderWidth: 1,
              padding: 12,
              boxPadding: 6,
              usePointStyle: true,
              callbacks: {
                label: function(context) {
                  return `${context.label}: ${context.raw}分`;
                }
              },
              boxShadow: '0 5px 15px rgba(0, 0, 0, 0.1)'
            }
          }
        }
      });
    },

    // 根据分数获取颜色
    getScoreColor(score) {
      if (score >= 80) return 'linear-gradient(135deg, #4CAF50, #8BC34A)';
      if (score >= 60) return 'linear-gradient(135deg, #FFC107, #FFEB3B)';
      return 'linear-gradient(135deg, #F44336, #FF9800)';
    },

    // 获取指标的颜色
    getMetricColor(metricKey) {
      return this.metricColors[metricKey] || '#333';
    },

    formatTime(dateString) {
      if (!dateString) return '未知';
      const isoStr = dateString.replace(' ', 'T');
      const date = new Date(isoStr);
      if (isNaN(date.getTime())) return '未知';

      const hh = String(date.getHours()).padStart(2, '0');
      const mm = String(date.getMinutes()).padStart(2, '0');
      const ss = String(date.getSeconds()).padStart(2, '0');
      return `${hh}:${mm}:${ss}`;
    },

    formatGroupDate(dateString) {
      if (!dateString) return '未知时间';
      const isoStr = dateString.replace(' ', 'T');
      const date = new Date(isoStr);
      if (isNaN(date.getTime())) return '无效时间';

      const Y = date.getFullYear();
      const M = String(date.getMonth() + 1).padStart(2, '0');
      const D = String(date.getDate()).padStart(2, '0');
      const hh = String(date.getHours()).padStart(2, '0');
      const mm = String(date.getMinutes()).padStart(2, '0');
      const ss = String(date.getSeconds()).padStart(2, '0');

      return `${Y}-${M}-${D} ${hh}:${mm}:${ss}`;
    },

    countCorrect(records) {
      return records.filter(r => r.is_correct).length;
    },

    countIncorrect(records) {
      return records.filter(r => !r.is_correct).length;
    },

    totalScore(records) {
      return records.reduce((sum, r) => sum + (r.score || 0), 0);
    },

    goBack() {
      this.$router.push({ name: 'Home' });
    }
  },
  beforeDestroy() {
    // 销毁所有雷达图实例
    Object.values(this.radarCharts).forEach(chart => {
      if (chart) chart.destroy();
    });
  }
}
</script>

<style scoped>
/* 主题变量定义 */
:root {
  --primary: #00ccff;
  --primary-dark: #0099cc;
  --primary-glow: rgba(0, 204, 255, 0.5);
  --bg-dark: #1a1a2e;
  --bg-medium: #16213e;
  --bg-light: #0f3460;
  --text-light: #e9e9e9;
  --text-medium: #bbbbbb;
  --text-dark: #333;
  --card-shadow: 0 8px 30px rgba(0, 0, 0, 0.3);
  --card-shadow-hover: 0 15px 40px rgba(0, 0, 0, 0.4);
  --transition-speed: 0.4s;
}

/* 全局样式 */
* {
  box-sizing: border-box;
  transition: all var(--transition-speed) ease;
}

.app-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
  background-color: var(--bg-dark);
  min-height: 100vh;
}

.header {
  text-align: center;
  margin-bottom: 30px;
  padding: 20px 0;
  background: linear-gradient(135deg, var(--bg-medium), var(--bg-light));
  border-radius: 12px;
  box-shadow: var(--card-shadow);
}

.result-title {
  color: var(--text-light);
  margin-bottom: 10px;
  font-size: 28px;
  text-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
}

.subtitle {
  color: var(--text-medium);
  font-size: 16px;
  margin: 0;
}

/* 加载状态样式 */
.loading-overlay {
  display: flex;
  justify-content: center;
  align-items: center;
  flex-direction: column;
  padding: 50px 0;
  color: var(--text-medium);
}

.book-loader {
  text-align: center;
}

.book {
  width: 100px;
  height: 80px;
  position: relative;
  margin: 0 auto 20px;
}

.page {
  width: 100px;
  height: 80px;
  background-color: var(--primary);
  border-radius: 2px;
  position: absolute;
  transform-origin: left center;
  animation: flip 1.5s infinite ease-in-out;
}

.page:nth-child(1) {
  animation-delay: 0.1s;
}

.page:nth-child(2) {
  animation-delay: 0.2s;
}

.page:nth-child(3) {
  animation-delay: 0.3s;
}

@keyframes flip {
  0% { transform: rotateY(0deg); z-index: 10; }
  100% { transform: rotateY(-180deg); z-index: 0; }
}

/* 空状态样式 */
.empty-state {
  text-align: center;
  padding: 50px 0;
  color: var(--text-medium);
}

.empty-illustration svg {
  width: 120px;
  height: 120px;
  margin-bottom: 20px;
  filter: drop-shadow(0 5px 15px rgba(0, 0, 0, 0.3));
}

.empty-text {
  font-size: 18px;
  margin-bottom: 10px;
}

.empty-hint {
  font-size: 14px;
  margin: 0;
}

/* 结果容器样式 */
.result-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.result-card {
  background-color: var(--bg-medium);
  border-radius: 12px;
  box-shadow: var(--card-shadow);
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.05);
}

/* 组头部样式 */
.group-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 20px;
  background-color: var(--bg-light);
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.group-summary {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.group-date {
  color: var(--text-medium);
  font-size: 14px;
}

.group-stats {
  display: flex;
  gap: 15px;
  font-size: 14px;
}

.correct-count {
  color: #4cd964;
}

.incorrect-count {
  color: #ff6b6b;
}

.total-score {
  color: #ffcc00;
}

/* 按钮样式 */
.analysis-btn, .toggle-btn {
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.3s ease;
  margin-left: 10px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.analysis-btn {
  background-color: var(--primary);
  color: var(--text-dark);
  box-shadow: 0 4px 15px var(--primary-glow);
}

.analysis-btn:hover {
  background-color: var(--primary-dark);
  transform: translateY(-2px);
  box-shadow: 0 6px 20px var(--primary-glow);
}

.toggle-btn {
  background-color: rgba(255, 255, 255, 0.1);
  color: var(--text-light);
}

.toggle-btn:hover {
  background-color: rgba(255, 255, 255, 0.2);
  transform: translateY(-2px);
}

/* 动画过渡效果 */
.slide-enter-active, .slide-leave-active {
  transition: max-height 0.6s cubic-bezier(0.175, 0.885, 0.32, 1.275), 
              opacity 0.4s ease, 
              padding 0.4s ease;
}

.slide-enter, .slide-leave-to {
  max-height: 0;
  opacity: 0;
  padding-top: 0;
  padding-bottom: 0;
  overflow: hidden;
}

/* 分析报告样式 */
.analysis-content {
  background-color: var(--bg-medium);
  border-radius: 12px;
  padding: 25px;
  margin: 15px;
  box-shadow: inset 0 2px 10px rgba(0, 0, 0, 0.2);
}

.analysis-content h3 {
  color: var(--text-light);
  border-bottom: 2px solid var(--primary);
  padding-bottom: 12px;
  margin-top: 0;
  font-size: 20px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* 左右平均布局 */
.analysis-layout {
  display: flex;
  gap: 25px;
  margin-top: 20px;
}

/* 左侧区域：雷达图 + 3个指标 */
.left-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.radar-section {
  width: 100%;
}

/* 左侧指标容器 */
.metrics-left {
  display: grid;
  grid-template-columns: 1fr;
  gap: 20px;
}

/* 右侧区域：3个指标 */
.right-section {
  flex: 1;
  display: grid;
  grid-template-columns: 1fr;
  gap: 20px;
}

/* 雷达图3D效果 */
.radar-card {
  background: linear-gradient(145deg, var(--bg-light), var(--bg-medium));
  border-radius: 12px;
  padding: 20px;
  box-shadow: 
    5px 5px 15px rgba(0, 0, 0, 0.3),
    -5px -5px 15px rgba(255, 255, 255, 0.05);
  transform-style: preserve-3d;
  transform: perspective(1000px) rotateX(2deg) rotateY(2deg);
  transition: all 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.radar-card:hover {
  transform: perspective(1000px) rotateX(0deg) rotateY(0deg) translateY(-5px);
  box-shadow: 
    8px 8px 25px rgba(0, 0, 0, 0.4),
    -8px -8px 25px rgba(255, 255, 255, 0.08);
}

.radar-card h4 {
  color: var(--text-light);
  text-align: center;
  margin-top: 0;
  margin-bottom: 20px;
  font-size: 16px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.radar-chart-container {
  position: relative;
  width: 100%;
  height: 0;
  padding-bottom: 100%;
}

.radar-chart-container canvas {
  position: absolute;
  top: 0;
  left: 0;
  width: 100% !important;
  height: 100% !important;
  filter: drop-shadow(0 5px 15px rgba(0, 204, 255, 0.2));
}

/* 指标卡片3D效果 */
.metric-card {
  background: linear-gradient(145deg, var(--bg-light), var(--bg-medium));
  border-radius: 10px;
  padding: 20px;
  box-shadow: 
    5px 5px 15px rgba(0, 0, 0, 0.3),
    -3px -3px 10px rgba(255, 255, 255, 0.05);
  transition: all 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  transform-style: preserve-3d;
  transform: perspective(800px) rotateX(1deg);
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.metric-card:hover {
  transform: perspective(800px) rotateX(0deg) translateY(-8px);
  box-shadow: 
    8px 8px 25px rgba(0, 0, 0, 0.4),
    -5px -5px 15px rgba(255, 255, 255, 0.08);
}

.metric-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.metric-header h4 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  text-shadow: 0 1px 5px rgba(0, 0, 0, 0.3);
}

.metric-score {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 18px;
  box-shadow: 
    0 3px 10px rgba(0, 0, 0, 0.3),
    inset 0 1px 2px rgba(255, 255, 255, 0.2);
  transform: translateZ(5px);
  position: relative;
  z-index: 2;
}

.metric-score::after {
  content: '';
  position: absolute;
  width: 38px;
  height: 38px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.15);
  z-index: -1;
}

.metric-description {
  color: var(--text-medium);
  font-size: 14px;
  line-height: 1.6;
  padding: 15px;
  background-color: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.3);
  transform: translateZ(2px);
}

/* 答题详情样式 */
.group-details {
  padding: 20px;
}

.answer-item {
  margin-bottom: 20px;
  padding: 15px;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background-color: rgba(255, 255, 255, 0.03);
}

.answer-item.correct {
  border-color: rgba(76, 217, 100, 0.3);
  background-color: rgba(76, 217, 100, 0.05);
}

.answer-item.incorrect {
  border-color: rgba(255, 107, 107, 0.3);
  background-color: rgba(255, 107, 107, 0.05);
}

.question-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 10px;
}

.question-number {
  font-weight: bold;
  color: var(--text-light);
}

.badge {
  background-color: rgba(0, 204, 255, 0.15);
  color: var(--primary);
  padding: 3px 10px;
  border-radius: 15px;
  font-size: 12px;
}

.question-content {
  color: var(--text-light);
  margin-bottom: 15px;
  line-height: 1.6;
}

.answer-section {
  margin-bottom: 15px;
}

.user-answer, .correct-answer {
  margin-bottom: 15px;
}

.answer-label {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
  font-weight: bold;
  font-size: 14px;
}

.label-icon {
  margin-right: 8px;
}

.user-answer .answer-label {
  color: #ff9500;
}

.correct-answer .answer-label {
  color: #4cd964;
}

.answer-content {
  font-size: 14px;
  line-height: 1.5;
  color: var(--text-medium);
}

.bubble {
  background-color: rgba(255, 255, 255, 0.05);
  padding: 10px 15px;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

.result-status {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 15px;
  border-top: 1px dashed rgba(255, 255, 255, 0.1);
}

.status-badge {
  display: flex;
  align-items: center;
  padding: 5px 12px;
  border-radius: 15px;
  font-size: 13px;
  background-color: rgba(255, 255, 255, 0.05);
  color: var(--text-medium);
}

.status-badge.correct {
  background-color: rgba(76, 217, 100, 0.15);
  color: #4cd964;
}

.status-icon {
  margin-right: 5px;
}

.meta-info {
  font-size: 13px;
  color: var(--text-medium);
}

/* 返回按钮 */
.retry-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 12px 24px;
  background: linear-gradient(135deg, var(--primary), var(--primary-dark));
  color: var(--text-dark);
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 16px;
  font-weight: 500;
  margin-top: 30px;
  margin-bottom: 30px;
  transition: all 0.3s ease;
  box-shadow: 0 5px 15px var(--primary-glow);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.retry-btn:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 25px var(--primary-glow);
}

.btn-icon {
  margin-right: 10px;
}

/* 响应式调整 */
@media (max-width: 768px) {
  .analysis-layout {
    flex-direction: column;
  }
  
  .left-section, .right-section {
    grid-template-columns: 1fr;
  }
  
  .group-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 15px;
  }
  
  .group-header > div {
    width: 100%;
  }
  
  .group-header button {
    margin-left: 0;
    margin-right: 10px;
  }
  
  .group-stats {
    flex-wrap: wrap;
  }
}
/* 新增分组卡片样式 */
.group-card {
  margin-bottom: 1.5rem;
}

.group-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.2rem;
  background-color: #f8f9fa;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.group-header:hover {
  background-color: #e9ecef;
}

.group-summary {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.group-date {
  font-weight: 500;
  color: #4361ee;
  font-size: 1rem;
}

.group-stats {
  display: flex;
  gap: 1rem;
  font-size: 0.9rem;
}

.correct-count {
  color: #4cc9f0;
}

.incorrect-count {
  color: #f72585;
}

.total-score {
  color: #4361ee;
}

.toggle-icon {
  font-size: 1.1rem;
  color: #6c757d;
}

.group-details {
  margin-top: 0.5rem;
}

.answer-item {
  background-color: white;
  border-radius: 8px;
  padding: 1rem;
  margin-bottom: 0.8rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.answer-item.correct {
  border-left: 3px solid #4cc9f0;
}

.answer-item.incorrect {
  border-left: 3px solid #f72585;
}

/* 调整原有样式以适应分组 */
.result-container {
  margin-top: 1.5rem;
}

/* 展开动画 */
.slide-enter-active, .slide-leave-active {
  transition: all 0.3s ease;
  max-height: 5000px;
  overflow: hidden;
}

.slide-enter, .slide-leave-to {
  max-height: 0;
  opacity: 0;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .group-stats {
    flex-direction: column;
    gap: 0.3rem;
  }
  
  .group-header {
    padding: 1rem;
  }
}
.result-container {
  margin-top: 1.5rem;
}

.summary-card {
  background-color: white;
  border-radius: 12px;
  padding: 1.5rem;
  margin-bottom: 1rem;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  cursor: pointer;
  transition: all 0.3s ease;
}

.summary-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 6px 25px rgba(0, 0, 0, 0.12);
}

.summary-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stats {
  display: flex;
  gap: 2rem;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.stat-icon {
  font-size: 1.2rem;
}

.stat-value {
  font-weight: bold;
  font-size: 1.1rem;
}

.stat-label {
  color: #6c757d;
}

.correct-count .stat-value {
  color: #4cc9f0;
}

.incorrect-count .stat-value {
  color: #f72585;
}

.total-score .stat-value {
  color: #4361ee;
}

.toggle-icon {
  font-size: 1.2rem;
  color: #6c757d;
}

.detailed-records {
  margin-top: 1rem;
  transition: all 0.3s ease;
}

/* 展开动画 */
.slide-enter-active, .slide-leave-active {
  transition: all 0.3s ease;
  max-height: 5000px; /* 足够大的值容纳内容 */
  overflow: hidden;
}

.slide-enter, .slide-leave-to {
  max-height: 0;
  opacity: 0;
  transform: translateY(-20px);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .stats {
    flex-direction: column;
    gap: 1rem;
  }
  
  .stat-item {
    justify-content: space-between;
  }
}
/* 之前的样式保留，新增以下样式 */

.sort-controls {
  margin: 1.5rem 0;
  display: flex;
  gap: 10px;
  justify-content: center;
  flex-wrap: wrap;
}

.sort-controls button {
  padding: 0.5rem 1rem;
  background-color: #f0f0f0;
  border: none;
  border-radius: 20px;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 0.85rem;
}

.sort-controls button.active {
  background-color: var(--primary-color);
  color: white;
}

.sort-controls button:hover {
  background-color: #e0e0e0;
}

.sort-controls button.active:hover {
  background-color: var(--primary-color);
  opacity: 0.9;
}

/* 卡片折叠/展开样式 */
.collapsed-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.8rem 0;
  font-size: 0.9rem;
}

.user-answer-summary {
  flex: 1;
}

.expanded-content {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px dashed #eee;
}

.question-content {
  margin: 10px 0;
  font-size: 16px;
  font-weight: 500;
  line-height: 1.5;
}

.result-details-footer {
  display: flex;
  justify-content: flex-end;
}

/* 卡片交互效果 */
.result-card {
  cursor: pointer;
  transition: all 0.3s ease;
}

.result-card:hover {
  transform: translateY(-3px);
}

.result-card.expanded {
  margin-bottom: 1.5rem;
}

/* 响应式调整 */
@media (max-width: 768px) {
  .collapsed-content {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }
  
  .sort-controls {
    flex-direction: column;
    align-items: center;
  }
  
  .sort-controls button {
    width: 100%;
    max-width: 200px;
  }
}

@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@300;400;500;700&display=swap');

:root {
  --primary-color: #4361ee;
  --success-color: #4cc9f0;
  --error-color: #f72585;
  --text-color: #2b2d42;
  --light-bg: #f8f9fa;
  --card-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
}

* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

.app-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 2rem 1rem;
  font-family: 'Noto Sans SC', sans-serif;
  color: var(--text-color);
}

.header {
  text-align: center;
  margin-bottom: 2.5rem;
}

.result-title {
  font-size: 2.2rem;
  font-weight: 700;
  color: var(--primary-color);
  margin-bottom: 0.5rem;
  position: relative;
  display: inline-block;
}

.result-title::after {
  content: '';
  position: absolute;
  bottom: -8px;
  left: 50%;
  transform: translateX(-50%);
  width: 60px;
  height: 4px;
  background: linear-gradient(90deg, var(--primary-color), #4cc9f0);
  border-radius: 2px;
}

.subtitle {
  font-size: 1rem;
  color: #6c757d;
  font-weight: 300;
}

/* 加载动画 */
.loading-overlay {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 300px;
}

.book-loader {
  text-align: center;
}

.book {
  position: relative;
  width: 60px;
  height: 45px;
  margin: 0 auto 20px;
  perspective: 120px;
}

.page {
  position: absolute;
  width: 30px;
  height: 45px;
  background: white;
  border: 2px solid var(--primary-color);
  border-radius: 0 4px 4px 0;
  transform-origin: left center;
  animation: flip 1.5s infinite ease-in-out;
}

.page:nth-child(1) {
  animation-delay: 0.1s;
  z-index: 3;
}

.page:nth-child(2) {
  animation-delay: 0.3s;
  z-index: 2;
}

.page:nth-child(3) {
  animation-delay: 0.5s;
  z-index: 1;
}

@keyframes flip {
  0%, 100% { transform: rotateY(0deg); }
  50% { transform: rotateY(-180deg); }
}

/* 空状态 */
.empty-state {
  text-align: center;
  padding: 3rem 0;
}

.empty-illustration {
  width: 150px;
  height: 150px;
  margin: 0 auto 1.5rem;
  opacity: 0.6;
}

.empty-text {
  font-size: 1.2rem;
  color: #6c757d;
  margin-bottom: 0.5rem;
}

.empty-hint {
  font-size: 0.9rem;
  color: #adb5bd;
}

/* 答题卡片 */
.result-details {
  margin-top: 1.5rem;
}

.result-card {
  position: relative;
  border-radius: 12px;
  padding: 1.5rem;
  margin-bottom: 1.5rem;
  background-color: white;
  box-shadow: var(--card-shadow);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
  overflow: hidden;
}

.result-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.12);
}

.result-card.correct {
  border-left: 4px solid var(--success-color);
}

.result-card.incorrect {
  border-left: 4px solid var(--error-color);
}

.card-decoration {
  position: absolute;
  width: 100%;
  height: 100%;
  top: 0;
  left: 0;
  pointer-events: none;
}

.corner {
  position: absolute;
  width: 20px;
  height: 20px;
  border-width: 2px;
  border-style: solid;
  opacity: 0.3;
}

.top-left {
  top: 10px;
  left: 10px;
  border-top-left-radius: 8px;
  border-right: none;
  border-bottom: none;
}

.top-right {
  top: 10px;
  right: 10px;
  border-top-right-radius: 8px;
  border-left: none;
  border-bottom: none;
}

.bottom-left {
  bottom: 10px;
  left: 10px;
  border-bottom-left-radius: 8px;
  border-right: none;
  border-top: none;
}

.bottom-right {
  bottom: 10px;
  right: 10px;
  border-bottom-right-radius: 8px;
  border-left: none;
  border-top: none;
}

.result-card.correct .corner {
  border-color: var(--success-color);
}

.result-card.incorrect .corner {
  border-color: var(--error-color);
}

/* 问题头部 */
.question-header {
  display: flex;
  align-items: center;
  margin-bottom: 1.2rem;
}

.question-number {
  font-weight: 700;
  font-size: 1.1rem;
  color: var(--primary-color);
}

.badge {
  margin-left: 0.8rem;
  padding: 0.2rem 0.6rem;
  background-color: #e9ecef;
  border-radius: 20px;
  font-size: 0.75rem;
  color: #495057;
}

/* 答案部分 */
.answer-section {
  margin-bottom: 1.2rem;
}

.answer-label {
  display: flex;
  align-items: center;
  margin-bottom: 0.5rem;
  font-size: 0.9rem;
  color: #6c757d;
}

.label-icon {
  margin-right: 0.5rem;
  font-size: 1rem;
}

.bubble {
  padding: 0.8rem 1rem;
  border-radius: 8px;
  background-color: var(--light-bg);
  margin-bottom: 0.8rem;
  position: relative;
}

.bubble::after {
  content: '';
  position: absolute;
  top: -8px;
  left: 20px;
  width: 0;
  height: 0;
  border-left: 8px solid transparent;
  border-right: 8px solid transparent;
  border-bottom: 8px solid var(--light-bg);
}

.user-answer .bubble {
  background-color: #e9f5ff;
}

.user-answer .bubble::after {
  border-bottom-color: #e9f5ff;
}

.correct-answer .bubble {
  background-color: #e6fcf5;
}

.correct-answer .bubble::after {
  border-bottom-color: #e6fcf5;
}

/* 结果状态 */
.result-status {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 0.8rem;
  border-top: 1px dashed #dee2e6;
}

.status-badge {
  display: flex;
  align-items: center;
  padding: 0.3rem 0.8rem;
  border-radius: 20px;
  font-size: 0.85rem;
  font-weight: 500;
}

.status-badge.correct {
  background-color: rgba(76, 201, 240, 0.1);
  color: var(--success-color);
}

.status-badge:not(.correct) {
  background-color: rgba(247, 37, 133, 0.1);
  color: var(--error-color);
}

.status-icon {
  margin-right: 0.4rem;
  font-size: 1rem;
}

.meta-info {
  display: flex;
  align-items: center;
  font-size: 0.8rem;
  color: #6c757d;
}

.timestamp, .score {
  display: flex;
  align-items: center;
  margin-left: 1rem;
}

/* 返回按钮 */
.retry-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 3rem auto 0;
  padding: 0.8rem 2rem;
  background: linear-gradient(135deg, var(--primary-color), #4cc9f0);
  color: white;
  border: none;
  border-radius: 30px;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(67, 97, 238, 0.3);
}

.retry-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(67, 97, 238, 0.4);
}

.btn-icon {
  margin-right: 0.5rem;
  font-size: 1.2rem;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .app-container {
    padding: 1.5rem 1rem;
  }
  
  .result-title {
    font-size: 1.8rem;
  }
  
  .result-status {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .meta-info {
    margin-top: 0.5rem;
  }
  
  .timestamp, .score {
    margin-left: 0;
    margin-right: 1rem;
  }
}
</style>