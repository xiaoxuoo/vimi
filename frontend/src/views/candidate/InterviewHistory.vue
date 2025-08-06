<template>
  <div class="container">
    <h2 class="page-title">面试记录分析</h2>
    
    <!-- 统计卡片 -->
    <div class="stats-grid">
      <div v-for="stat in statistics" :key="stat.title" class="stat-card">
        <div class="stat-content">
          <div>
            <p class="stat-title">{{ stat.title }}</p>
            <h3 class="stat-value">{{ stat.value }}</h3>
          </div>
          <el-icon :size="28" :class="stat.iconClass">
            <component :is="stat.icon" />
          </el-icon>
        </div>
      </div>
    </div>

    <!-- 面试记录表格 -->
    <el-card class="record-table-card">
      <template #header>
        <div class="table-header">
          <h2 class="table-title">面试记录</h2>
          <div class="table-filters">
            <el-select v-model="filterStatus" placeholder="状态筛选" clearable>
              <el-option
                v-for="item in statusOptions"
                :key="item.value"
                :label="item.label"
                :value="item.value"
              />
            </el-select>
            <el-date-picker
              v-model="dateRange"
              type="daterange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              :shortcuts="dateShortcuts"
            />
          </div>
        </div>
      </template>

      <el-table :data="paginatedInterviews" style="width: 100%">
        <el-table-column label="面试时间" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.face_created_at) }}
          </template>
        </el-table-column>

        <el-table-column prop="job_title" label="面试岗位" />

        <el-table-column label="面试方式" width="120">
          <template #default="{ row }">
            {{ row && row.type === 'online' ? '线下面试' : '线上面试' }}
          </template>
        </el-table-column>

        <el-table-column label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="getStatusTagType(row.status)">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="240" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="viewDetail(row)">详情</el-button>
            <el-button type="success" link @click="goToReport(row.record_id)">查看分析报告</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="currentPage"
          :page-size="pageSize"
          :total="filteredInterviews.length"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>

    <!-- 详情分析弹窗 -->
    <el-dialog
      title="面试详情分析"
      v-model="showDetailDialog"
      width="900px"
      @close="handleDialogClose"
      class="analysis-dialog"
    >
      <div v-if="detailRecord" class="dialog-content">
        <div class="record-info">
          <p><i class="fas fa-clock"></i> <strong>面试时间：</strong>{{ formatDateTime(detailRecord.face_created_at) }}</p>
          <p><i class="fas fa-briefcase"></i> <strong>岗位名称：</strong>{{ detailRecord.job_title }}</p>
          <p><i class="fas fa-map-marker-alt"></i> <strong>面试方式：</strong>{{ detailRecord.type === 'online' ? '线上面试' : '线下面试' }}</p>
        </div>

        <!-- 微表情统计 -->
        <section class="analysis-section">
          <h3 class="section-title">
            <i class="fas fa-smile-beam"></i>微表情统计
          </h3>
          <div class="chart-wrapper">
            <canvas id="expressionChart"></canvas>
          </div>
        </section>

        <!-- 情绪分析 -->
        <section v-if="detailRecord.emotion" class="analysis-section">
          <h3 class="section-title">
            <i class="fas fa-heart"></i>情绪分析
          </h3>
          <div class="chart-wrapper emotion-chart-container">
            <canvas id="emotionChart"></canvas>
          </div>
        </section>

        <!-- 技能分析 -->
        <section v-if="detailRecord.skills" class="analysis-section">
          <h3 class="section-title">
            <i class="fas fa-chart-pie"></i>技能分析
          </h3>
          <div class="chart-wrapper skills-chart-container">
            <canvas id="skillsChart"></canvas>
          </div>
          <div class="skills-comments">
            <div class="comment-item">
              <span class="comment-label">语言表达：</span>
              <span class="comment-text">{{ detailRecord.skills.language_expression?.comment || '无' }}</span>
            </div>
            <div class="comment-item">
              <span class="comment-label">逻辑思维：</span>
              <span class="comment-text">{{ detailRecord.skills.logical_thinking?.comment || '无' }}</span>
            </div>
            <div class="comment-item">
              <span class="comment-label">创造力：</span>
              <span class="comment-text">{{ detailRecord.skills.creativity?.comment || '无' }}</span>
            </div>
            <div class="comment-item">
              <span class="comment-label">抗压能力：</span>
              <span class="comment-text">{{ detailRecord.skills.stress_response?.comment || '无' }}</span>
            </div>
          </div>
        </section>
      </div>
      <div v-else class="loading-state">
        <i class="fas fa-spinner fa-spin"></i>
        <p>加载中...</p>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import axios from 'axios'
import dayjs from 'dayjs'
import Chart from 'chart.js/auto'
import {
  Calendar,
  Timer,
  CircleCheck,
  CircleClose
} from '@element-plus/icons-vue'

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

export default {
  name: 'InterviewHistory',
  components: { Calendar, Timer, CircleCheck, CircleClose },
  data() {
    return {
      statistics: [
        { 
          title: '总面试场次', 
          value: 0, 
          icon: Calendar, 
          iconClass: 'stat-icon-blue' 
        },
        { 
          title: '已完成面试', 
          value: 0, 
          icon: CircleCheck, 
          iconClass: 'stat-icon-green' 
        },
        { 
          title: '待面试', 
          value: 0, 
          icon: Timer, 
          iconClass: 'stat-icon-orange' 
        },
        { 
          title: '未通过', 
          value: 0, 
          icon: CircleClose, 
          iconClass: 'stat-icon-red' 
        }
      ],
      interviews: [],
      filterStatus: '',
      dateRange: [],
      currentPage: 1,
      pageSize: 10,
      showDetailDialog: false,
      detailRecord: null,
      expressionChart: null,
      emotionChart: null,
      skillsChart: null,
      statusOptions: [
        { label: '待面试', value: 'scheduled' },
        { label: '进行中', value: 'ongoing' },
        { label: '已完成', value: 'completed' },
        { label: '已取消', value: 'cancelled' }
      ],
      dateShortcuts: [
        {
          text: '最近一周',
          onClick: picker => {
            const end = new Date()
            const start = new Date()
            start.setDate(start.getDate() - 7)
            picker.$emit('pick', [start, end])
          }
        },
        {
          text: '最近一月',
          onClick: picker => {
            const end = new Date()
            const start = new Date()
            start.setMonth(start.getMonth() - 1)
            picker.$emit('pick', [start, end])
          }
        }
      ]
    }
  },
  computed: {
    filteredInterviews() {
      let result = this.interviews
      if (this.filterStatus) {
        result = result.filter(i => i.status === this.filterStatus)
      }
      if (this.dateRange.length === 2) {
        const start = dayjs(this.dateRange[0]).startOf('day')
        const end = dayjs(this.dateRange[1]).endOf('day')
        result = result.filter(i => {
          const time = dayjs(i.face_created_at)
          return time.isAfter(start) && time.isBefore(end)
        })
      }
      return result
    },
    paginatedInterviews() {
      const start = (this.currentPage - 1) * this.pageSize
      return this.filteredInterviews.slice(start, start + this.pageSize)
    }
  },
  methods: {
    formatDateTime(val) {
      if (!val) return '无数据'
      return dayjs(val).format('YYYY-MM-DD HH:mm:ss')
    },
    getStatusText(status) {
      const map = {
        'scheduled': '待面试',
        'ongoing': '进行中',
        'completed': '已完成',
        'cancelled': '已取消'
      }
      return map[status] || status
    },
    getStatusTagType(status) {
      const map = {
        'scheduled': 'warning',
        'ongoing': 'primary',
        'completed': 'success',
        'cancelled': 'danger'
      }
      return map[status] || 'info'
    },
    async fetchInterviews() {
      try {
        const userStr = localStorage.getItem('user')
        const userId = userStr ? JSON.parse(userStr).id : null
        if (!userId) {
          console.warn('没有 user_id，请先登录')
          return
        }
        const res = await axios.get('/api/voice_record/expression_records', {
          params: { user_id: userId }
        })
        if (res.data.code === 0) {
          // 将已有分析记录的面试标记为已完成
          this.interviews = res.data.data.map(item => {
            if (item && item.face_created_at) {
              // 如果有分析数据，则认为是已完成面试
              if (item.expression_data || item.emotion || item.skills) {
                item.status = 'completed'
              }
              return item
            }
            return null
          }).filter(Boolean)
          
          this.updateStatistics()
        }
      } catch (error) {
        console.error('获取面试数据失败', error)
      }
    },
    updateStatistics() {
      this.statistics[0].value = this.interviews.length
      this.statistics[1].value = this.interviews.filter(i => i.status === 'completed').length
      this.statistics[2].value = this.interviews.filter(i => i.status === 'scheduled').length
      this.statistics[3].value = this.interviews.filter(i => i.status === 'cancelled').length
    },
    handleSizeChange(size) {
      this.pageSize = size
      this.currentPage = 1
    },
    handlePageChange(page) {
      this.currentPage = page
    },
    viewDetail(row) {
      this.detailRecord = null
      this.showDetailDialog = true
      this.detailRecord = row
      this.$nextTick(() => {
        this.renderCharts()
      })
    },
    goToReport(recordId) {
      if (!recordId) return
      this.$router.push({ name: 'ExpressionReport', params: { record_id: recordId } })
    },
    handleDialogClose() {
      this.detailRecord = null
      this.destroyCharts()
    },
    destroyCharts() {
      if (this.expressionChart) {
        this.expressionChart.destroy()
        this.expressionChart = null
      }
      if (this.emotionChart) {
        this.emotionChart.destroy()
        this.emotionChart = null
      }
      if (this.skillsChart) {
        this.skillsChart.destroy()
        this.skillsChart = null
      }
    },
    renderCharts() {
      this.destroyCharts()
      if (!this.detailRecord) return
      const expressionData = this.detailRecord.expression_data || {}
      const emotion = this.detailRecord.emotion || {}
      const skills = this.detailRecord.skills || {}

      // 微表情柱状图
      const expCtx = document.getElementById('expressionChart').getContext('2d')
      this.expressionChart = new Chart(expCtx, {
        type: 'bar',
        data: {
          labels: Object.keys(expressionData).map(key => expressionLabels[key]),
          datasets: [{
            label: '表情强度',
            data: Object.values(expressionData).map(val => val.toFixed(3)),
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
                  return `强度: ${context.raw}`
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

      // 情绪甜甜圈图
      const emoCtx = document.getElementById('emotionChart')?.getContext('2d')
      if (emoCtx) {
        this.emotionChart = new Chart(emoCtx, {
          type: 'doughnut',
          data: {
            labels: ['积极', '中性', '消极'],
            datasets: [{
              label: '情绪占比',
              data: [
                emotion.positive || 0,
                emotion.neutral || 0,
                emotion.negative || 0
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
              hoverOffset: 20,
              shadowBlur: 15,
              shadowColor: 'rgba(0, 0, 0, 0.3)'
            }]
          },
          options: {
            responsive: true,
            cutout: '60%',
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
                    return `${context.label}: ${context.raw}%`
                  }
                }
              }
            }
          }
        })
      }

      // 技能雷达图
      const skillCtx = document.getElementById('skillsChart')?.getContext('2d')
      if (skillCtx) {
        const skillLabels = []
        const skillScores = []
        for (const key in skills) {
          skillLabels.push(key)
          skillScores.push(skills[key]?.score || 0)
        }
        
        this.skillsChart = new Chart(skillCtx, {
          type: 'radar',
          data: {
            labels: ['语言表达', '逻辑思维', '创造力', '抗压能力'],
            datasets: [{
              label: '技能得分',
              data: [
                skills.language_expression?.score || 0,
                skills.logical_thinking?.score || 0,
                skills.creativity?.score || 0,
                skills.stress_response?.score || 0
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
                    return `${context.label}: ${context.raw}分`
                  }
                }
              }
            }
          }
        })
      }
    }
  },
  mounted() {
    this.fetchInterviews()
  }
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

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.stat-card {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 10px 20px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
  border: 1px solid rgba(255, 255, 255, 0.6);
  position: relative;
  overflow: hidden;
}

.stat-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 4px;
  background: linear-gradient(90deg, #6b46c1, #4299e1);
}

.stat-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 15px 30px rgba(0, 0, 0, 0.12);
}

.stat-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stat-title {
  color: #4a5568;
  font-size: 14px;
  margin-bottom: 8px;
}

.stat-value {
  color: #2d3748;
  font-size: 24px;
  font-weight: 700;
  margin: 0;
}

.stat-icon-blue {
  color: #4299e1;
}

.stat-icon-green {
  color: #48bb78;
}

.stat-icon-orange {
  color: #ed8936;
}

.stat-icon-red {
  color: #f56565;
}

.record-table-card {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 15px;
  padding: 25px;
  margin-bottom: 40px;
  box-shadow: 0 15px 35px rgba(0, 0, 0, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.6);
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.table-title {
  color: #2d3748;
  font-size: 20px;
  font-weight: 600;
  margin: 0;
}

.table-filters {
  display: flex;
  gap: 15px;
}

.pagination-wrapper {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}

/* 详情弹窗样式 */
.analysis-dialog {
  border-radius: 15px;
  overflow: hidden;
}

.analysis-dialog :deep(.el-dialog__header) {
  background: linear-gradient(90deg, #6b46c1, #4299e1);
  margin: 0;
  padding: 15px 20px;
}

.analysis-dialog :deep(.el-dialog__title) {
  color: white;
  font-size: 18px;
  font-weight: 600;
}

.analysis-dialog :deep(.el-dialog__headerbtn) {
  top: 15px;
}

.analysis-dialog :deep(.el-dialog__headerbtn .el-dialog__close) {
  color: white;
  font-size: 20px;
}

.analysis-dialog :deep(.el-dialog__body) {
  padding: 0;
}

.dialog-content {
  padding: 25px;
}

.record-info {
  background: #f8f9fa;
  padding: 15px;
  border-radius: 8px;
  margin-bottom: 25px;
}

.record-info p {
  margin: 8px 0;
  color: #4a5568;
  display: flex;
  align-items: center;
}

.record-info p i {
  margin-right: 10px;
  width: 20px;
  text-align: center;
  color: #6b46c1;
}

.analysis-section {
  margin-bottom: 35px;
  position: relative;
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
  margin-bottom: 20px;
}

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

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 50px;
  color: #718096;
}

.loading-state i {
  font-size: 40px;
  margin-bottom: 20px;
  color: #6b46c1;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .container {
    padding: 20px 15px;
  }
  
  .stats-grid {
    grid-template-columns: 1fr 1fr;
  }
  
  .table-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 15px;
  }
  
  .table-filters {
    width: 100%;
    flex-direction: column;
    gap: 10px;
  }
  
  .chart-wrapper {
    height: 250px;
    padding: 15px;
  }
  
  .comment-label {
    min-width: 90px;
  }
}
</style>