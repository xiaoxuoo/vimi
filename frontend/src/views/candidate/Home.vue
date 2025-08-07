<template>
  <div class="home-container p-6">
    <!-- 欢迎卡片 -->
    <div class="welcome-card bg-gradient-to-r from-blue-500 to-blue-600 text-white p-6 rounded-lg shadow-lg mb-6">
      <h2 class="text-2xl font-bold mb-2">欢迎回来，{{ username }}！</h2>
      <p class="text-blue-100">今天是个寻找理想工作的好日子</p>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-grid">
      <div v-for="stat in interviewStatistics" :key="stat.title" class="stat-card">
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

    <!-- 最近面试 -->
    <div class="recent-interviews bg-white p-6 rounded-lg shadow">
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-lg font-semibold text-gray-700">最近面试</h3>
        <router-link to="/candidate/history" class="text-blue-500 hover:text-blue-600">
          查看全部
        </router-link>
      </div>
      <div v-if="paginatedInterviews.length > 0">
        <div v-for="interview in paginatedInterviews" :key="interview.id" 
             class="interview-item flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
          <div class="flex items-center space-x-4">
            <el-avatar :size="40">
              {{ interview.companyName ? interview.companyName.charAt(0) : '?' }}
            </el-avatar>
            <div>
              <h4 class="font-medium text-gray-900">{{ interview.job_title || '未知职位' }}</h4>
              <p class="text-sm text-gray-500">{{ interview.companyName || '未知公司' }}</p>
            </div>
          </div>
          <div class="text-right">
            <el-tag :type="getStatusTagType(interview.status)" size="small">
              {{ getStatusText(interview.status) }}
            </el-tag>
            <p class="text-sm text-gray-500 mt-1">{{ formatDateTime(interview.face_created_at) }}</p>
          </div>
        </div>
      </div>
      <div v-else class="text-center py-8 text-gray-500">
        暂无面试记录
      </div>

      <div class="pagination-wrapper mt-4">
        <el-pagination
          v-model:current-page="currentPage"
          :page-size="pageSize"
          :total="interviews.length"
          :page-sizes="[5, 10, 20]"
          layout="total, sizes, prev, pager, next"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import dayjs from 'dayjs'
import {
  Calendar,
  Timer,
  CircleCheck,
  CircleClose
} from '@element-plus/icons-vue'

export default {
  name: 'HomePage',
  data() {
    return {
      username: localStorage.getItem('username') || '求职者',
      interviews: [],
      currentPage: 1,
      pageSize: 5,
      interviewStatistics: [
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
      ]
    }
  },
  computed: {
    paginatedInterviews() {
      const start = (this.currentPage - 1) * this.pageSize
      return this.interviews.slice(start, start + this.pageSize)
    }
  },
  methods: {
    formatDateTime(val) {
      if (!val) return '无数据'
      return dayjs(val).format('YYYY-MM-DD HH:mm')
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
    handleSizeChange(size) {
      this.pageSize = size
      this.currentPage = 1
    },
    handlePageChange(page) {
      this.currentPage = page
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
      this.interviewStatistics[0].value = this.interviews.length
      this.interviewStatistics[1].value = this.interviews.filter(i => i.status === 'completed').length
      this.interviewStatistics[2].value = this.interviews.filter(i => i.status === 'scheduled').length
      this.interviewStatistics[3].value = this.interviews.filter(i => i.status === 'cancelled').length
    }
  },
  mounted() {
    this.fetchInterviews()
  }
}
</script>

<style scoped>
.home-container {
  max-width: 1200px;
  margin: 0 auto;
}

.welcome-card {
  background: linear-gradient(135deg, #6b46c1, #4299e1);
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

.recent-interviews {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 15px;
  padding: 25px;
  box-shadow: 0 15px 35px rgba(0, 0, 0, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.6);
}

.interview-item {
  cursor: pointer;
  margin-bottom: 10px;
}

.pagination-wrapper {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}
</style>