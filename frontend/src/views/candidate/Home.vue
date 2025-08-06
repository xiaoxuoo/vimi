<template>
  <div class="container">
    <h2 class="page-title">表情识别分析记录</h2>
    
    <div v-if="records.length === 0" class="empty-state">
      <div class="empty-icon">📊</div>
      <p>暂无分析记录</p>
    </div>

    <div 
      v-for="item in records" 
      :key="item.record_id" 
      class="record-card"
    >
      <!-- 记录时间 -->
      <div class="record-time">
        <i class="fas fa-clock"></i>
        <span>记录时间：{{ formatDate(item.face_created_at) }}</span>
      </div>

      <!-- 微表情统计 -->
      <div class="section">
        <h3 class="section-title">
          <i class="fas fa-smile-beam"></i>微表情统计
        </h3>
        <div class="chart-wrapper">
          <canvas :id="`expression-chart-${item.record_id}`"></canvas>
        </div>
      </div>

      <!-- 情绪分析 -->
      <div v-if="item.emotion" class="section">
        <h3 class="section-title">
          <i class="fas fa-heart"></i>情绪分析
        </h3>
        <div class="chart-wrapper emotion-chart-container">
          <canvas :id="`emotion-chart-${item.record_id}`"></canvas>
        </div>
      </div>

      <!-- 技能分析 -->
      <div v-if="item.skills" class="section">
        <h3 class="section-title">
          <i class="fas fa-chart-pie"></i>技能分析
        </h3>
        <div class="chart-wrapper skills-chart-container">
          <canvas :id="`skills-chart-${item.record_id}`"></canvas>
        </div>
        <div class="skills-comments">
          <div class="comment-item">
            <span class="comment-label">语言表达：</span>
            <span class="comment-text">{{ item.skills.language_expression?.comment }}</span>
          </div>
          <div class="comment-item">
            <span class="comment-label">逻辑思维：</span>
            <span class="comment-text">{{ item.skills.logical_thinking?.comment }}</span>
          </div>
          <div class="comment-item">
            <span class="comment-label">创造力：</span>
            <span class="comment-text">{{ item.skills.creativity?.comment }}</span>
          </div>
          <div class="comment-item">
            <span class="comment-label">抗压能力：</span>
            <span class="comment-text">{{ item.skills.stress_response?.comment }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import axios from 'axios'
import Chart from 'chart.js/auto'

const records = ref([])
const charts = ref({})

// 表情标签映射
const expressionLabels = [
  '其他(非人脸)', 
  '其他表情', 
  '喜悦', 
  '愤怒', 
  '悲伤', 
  '惊恐', 
  '厌恶', 
  '中性'
]

onMounted(async () => {
  const user = JSON.parse(localStorage.getItem('user') || '{}')
  const userId = user.id

  if (!userId) return

  try {
    const res = await axios.get('/api/voice_record/expression_records', {
      params: { user_id: userId }
    })

    if (res.data.code === 0) {
      records.value = res.data.data
      nextTick(() => {
        initCharts()
      })
    } else {
      console.error('数据加载失败', res.data.desc)
    }
  } catch (error) {
    console.error('请求失败', error)
  }
})

function initCharts() {
  records.value.forEach(item => {
    // 销毁已存在的图表，避免重复创建
    if (charts.value[item.record_id]) {
      charts.value[item.record_id].forEach(chart => chart.destroy())
    }
    
    charts.value[item.record_id] = []
    
    // 微表情统计图表 - 3D柱状图
    const expressionCtx = document.getElementById(`expression-chart-${item.record_id}`).getContext('2d')
    const expressionChart = new Chart(expressionCtx, {
      type: 'bar',
      data: {
        labels: Object.keys(item.expression_data).map(key => expressionLabels[key]),
        datasets: [{
          label: '表情强度',
          data: Object.values(item.expression_data).map(val => val.toFixed(3)),
          backgroundColor: [
            'rgba(153, 102, 255, 0.7)',
            'rgba(255, 159, 64, 0.7)',
            'rgba(75, 192, 192, 0.7)',
            'rgba(255, 99, 132, 0.7)',
            'rgba(54, 162, 235, 0.7)',
            'rgba(255, 206, 86, 0.7)',
            'rgba(108, 117, 125, 0.7)',
            'rgba(231, 233, 237, 0.7)'
          ],
          borderColor: [
            'rgba(153, 102, 255, 1)',
            'rgba(255, 159, 64, 1)',
            'rgba(75, 192, 192, 1)',
            'rgba(255, 99, 132, 1)',
            'rgba(54, 162, 235, 1)',
            'rgba(255, 206, 86, 1)',
            'rgba(108, 117, 125, 1)',
            'rgba(231, 233, 237, 1)'
          ],
          borderWidth: 1,
          borderRadius: 6,
          barPercentage: 0.6,
          // 3D效果增强
          borderSkipped: false,
          shadowBlur: 10,
          shadowColor: 'rgba(0, 0, 0, 0.2)'
        }]
      },
      options: {
        responsive: true,
        animation: {
          duration: 1500,
          easing: 'easeOutQuart'
        },
        plugins: {
          legend: {
            display: false
          },
          tooltip: {
            backgroundColor: 'rgba(0, 0, 0, 0.8)',
            padding: 12,
            cornerRadius: 6,
            titleFont: {
              size: 14,
              weight: 'bold'
            },
            bodyFont: {
              size: 13
            },
            callbacks: {
              label: function(context) {
                return `强度: ${context.raw}`;
              }
            }
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            grid: {
              color: 'rgba(200, 200, 200, 0.15)',
              drawBorder: false
            },
            ticks: {
              padding: 10,
              font: {
                size: 11
              }
            }
          },
          x: {
            grid: {
              display: false
            },
            ticks: {
              padding: 10,
              font: {
                size: 11
              }
            }
          }
        }
      }
    })
    charts.value[item.record_id].push(expressionChart)

    // 情绪分析图表 - 3D环形图
    if (item.emotion) {
      const emotionCtx = document.getElementById(`emotion-chart-${item.record_id}`).getContext('2d')
      const emotionChart = new Chart(emotionCtx, {
        type: 'doughnut',
        data: {
          labels: ['积极', '中性', '消极'],
          datasets: [{
            data: [
              item.emotion.positive || 0,
              item.emotion.neutral || 0,
              item.emotion.negative || 0
            ],
            backgroundColor: [
              'rgba(75, 192, 192, 0.85)',
              'rgba(54, 162, 235, 0.85)',
              'rgba(255, 99, 132, 0.85)'
            ],
            borderColor: [
              'rgba(75, 192, 192, 1)',
              'rgba(54, 162, 235, 1)',
              'rgba(255, 99, 132, 1)'
            ],
            borderWidth: 2,
            hoverOffset: 20, // 3D悬浮效果
            shadowBlur: 15,
            shadowColor: 'rgba(0, 0, 0, 0.3)'
          }]
        },
        options: {
          responsive: true,
          cutout: '60%', // 环形大小
          animation: {
            animateRotate: true,
            animateScale: true,
            duration: 2000,
            easing: 'easeOutCirc'
          },
          plugins: {
            legend: {
              position: 'bottom',
              labels: {
                padding: 20,
                font: {
                  size: 13,
                  weight: '500'
                },
                usePointStyle: true,
                pointStyle: 'circle'
              }
            },
            tooltip: {
              backgroundColor: 'rgba(0, 0, 0, 0.8)',
              padding: 12,
              cornerRadius: 6,
              callbacks: {
                label: function(context) {
                  return `${context.label}: ${context.raw}%`;
                }
              }
            }
          }
        }
      })
      charts.value[item.record_id].push(emotionChart)
    }

    // 技能分析图表 - 3D雷达图
    if (item.skills) {
      const skillsCtx = document.getElementById(`skills-chart-${item.record_id}`).getContext('2d')
      const skillsChart = new Chart(skillsCtx, {
        type: 'radar',
        data: {
          labels: ['语言表达', '逻辑思维', '创造力', '抗压能力'],
          datasets: [{
            label: '技能评分',
            data: [
              item.skills.language_expression?.score || 0,
              item.skills.logical_thinking?.score || 0,
              item.skills.creativity?.score || 0,
              item.skills.stress_response?.score || 0
            ],
            backgroundColor: 'rgba(153, 102, 255, 0.25)',
            borderColor: 'rgba(153, 102, 255, 0.9)',
            pointBackgroundColor: 'rgba(153, 102, 255, 1)',
            pointBorderColor: '#fff',
            pointHoverBackgroundColor: '#fff',
            pointHoverBorderColor: 'rgba(153, 102, 255, 1)',
            pointRadius: 6,
            pointHoverRadius: 8,
            borderWidth: 2,
            // 3D效果
            borderDash: [],
            shadowBlur: 10,
            shadowColor: 'rgba(153, 102, 255, 0.3)'
          }]
        },
        options: {
          responsive: true,
          animation: {
            duration: 2000,
            easing: 'easeOutQuart'
          },
          scales: {
            r: {
              angleLines: {
                color: 'rgba(200, 200, 200, 0.25)',
                lineWidth: 1
              },
              grid: {
                color: 'rgba(200, 200, 200, 0.2)',
                lineWidth: 1
              },
              pointLabels: {
                font: {
                  size: 13,
                  weight: '500'
                },
                padding: 15
              },
              ticks: {
                backdropColor: 'transparent',
                stepSize: 20,
                max: 100,
                font: {
                  size: 10
                }
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
              backgroundColor: 'rgba(0, 0, 0, 0.8)',
              padding: 12,
              cornerRadius: 6,
              callbacks: {
                label: function(context) {
                  return `${context.label}: ${context.raw}分`;
                }
              }
            }
          }
        }
      })
      charts.value[item.record_id].push(skillsChart)
    }
  })
}

function formatDate(dateStr) {
  return new Date(dateStr).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}
</script>

<style scoped>
.container {
  max-width: 1100px;
  margin: 0 auto;
  padding: 30px 20px;
  background: linear-gradient(135deg, #f0f4f8 0%, #d9e2ec 100%);
  min-height: 100vh;
}

.page-title {
  text-align: center;
  color: #2d3748;
  margin-bottom: 40px;
  font-size: 28px;
  font-weight: 700;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  letter-spacing: 0.5px;
  position: relative;
  padding-bottom: 15px;
}

.page-title::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 80px;
  height: 3px;
  background: linear-gradient(90deg, #6b46c1, #4299e1);
  border-radius: 3px;
}

.record-card {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 15px;
  padding: 25px;
  margin-bottom: 40px;
  box-shadow: 0 15px 35px rgba(0, 0, 0, 0.08);
  transform-style: preserve-3d;
  transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  border: 1px solid rgba(255, 255, 255, 0.6);
  position: relative;
  overflow: hidden;
}

.record-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 5px;
  background: linear-gradient(90deg, #6b46c1, #4299e1);
  transform: translateZ(0);
}

.record-card:hover {
  transform: translateY(-8px) rotateX(3deg);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.12);
}

.record-time {
  color: #4a5568;
  font-size: 15px;
  margin-bottom: 25px;
  padding-bottom: 15px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
  display: flex;
  align-items: center;
  font-weight: 500;
}

.record-time i {
  margin-right: 10px;
  color: #6b46c1;
  font-size: 18px;
}

.section {
  margin-bottom: 35px;
  position: relative;
  transform: translateZ(5px);
}

.section:last-child {
  margin-bottom: 0;
}

.section-title {
  color: #2d3748;
  font-size: 19px;
  margin: 0 0 20px 0;
  padding-bottom: 10px;
  border-bottom: 2px solid #edf2f7;
  display: flex;
  align-items: center;
  font-weight: 600;
}

.section-title i {
  margin-right: 10px;
  color: #4299e1;
  font-size: 20px;
}

.chart-wrapper {
  height: 320px;
  padding: 20px;
  background: rgba(255, 255, 255, 0.7);
  border-radius: 12px;
  box-shadow: inset 0 3px 15px rgba(0, 0, 0, 0.05);
  transform-style: preserve-3d;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.chart-wrapper::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(0, 0, 0, 0.05), transparent);
}

.record-card:hover .chart-wrapper {
  transform: translateZ(15px);
  box-shadow: inset 0 5px 20px rgba(0, 0, 0, 0.07);
}

/* 不同图表容器的特殊样式 */
.emotion-chart-container {
  max-width: 500px;
  margin: 0 auto;
}

.skills-chart-container {
  max-width: 600px;
  margin: 0 auto;
}

.skills-comments {
  margin-top: 20px;
  padding: 20px;
  background: rgba(247, 250, 252, 0.8);
  border-radius: 10px;
  border-left: 3px solid #6b46c1;
  transform: translateZ(3px);
}

.comment-item {
  margin-bottom: 12px;
  display: flex;
  flex-wrap: wrap;
}

.comment-item:last-child {
  margin-bottom: 0;
}

.comment-label {
  font-weight: 600;
  min-width: 110px;
  color: #2d3748;
  padding-right: 10px;
}

.comment-text {
  color: #4a5568;
  flex: 1;
  line-height: 1.5;
}

.empty-state {
  text-align: center;
  padding: 80px 30px;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 15px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.05);
  transform: translateZ(5px);
}

.empty-icon {
  font-size: 80px;
  margin-bottom: 25px;
  color: #cbd5e0;
  filter: drop-shadow(0 4px 6px rgba(0, 0, 0, 0.05));
}

.empty-state p {
  color: #718096;
  font-size: 19px;
  font-weight: 500;
}

/* 3D效果增强 */
::v-deep .chartjs-render-monitor {
  transform: translateZ(10px);
  transition: all 0.4s ease;
}

.record-card:hover ::v-deep .chartjs-render-monitor {
  transform: translateZ(20px) scale(1.02);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .container {
    padding: 20px 15px;
  }
  
  .record-card {
    padding: 20px 15px;
    margin-bottom: 30px;
  }
  
  .chart-wrapper {
    height: 280px;
    padding: 15px;
  }
  
  .section-title {
    font-size: 17px;
  }
  
  .comment-label {
    min-width: 90px;
  }
}
</style>
