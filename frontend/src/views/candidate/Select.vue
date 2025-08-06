<template>
  <!-- 欢迎弹窗 -->
  <div v-if="showWelcomeModal" class="welcome-modal">
    <div class="welcome-content">
      <div class="welcome-header">
        <h2>欢迎来到面试系统</h2>
        <div class="welcome-subtitle">请选择您喜欢的形象和声音</div>
      </div>
      <div class="welcome-body">
        <div class="welcome-step">
          <span class="step-icon">1</span>
          <span>浏览并选择虚拟人形象</span>
        </div>
        <div class="welcome-step">
          <span class="step-icon">2</span>
          <span>挑选合适的声音</span>
        </div>
        <div class="welcome-step">
          <span class="step-icon">3</span>
          <span>点击"开始面试"按钮</span>
        </div>
      </div>
      <button class="welcome-confirm-btn" @click="closeWelcomeModal">
        开始选择
        <span class="btn-arrow">→</span>
      </button>
    </div>
  </div>

  <div :class="['container', { 'dark-mode': isDarkMode }]">

    <!-- 虚拟人形象水平滚动区域 -->
    <section class="horizontal-scroll-section">
      <h2>虚拟人形象</h2>
      <div class="horizontal-scroll-container">
        <div class="scroll-wrapper">
          <div 
            v-for="avatar in avatarList" 
            :key="avatar.id" 
            :class="['scroll-item', avatarId.trim() === avatar.avatar_id.trim() ? 'selected' : '']"
          >
            <img :src="avatar.image_url" alt="avatar image" class="scroll-image" />
            <div class="scroll-info">
              <div>{{ avatar.description || avatar.avatar_id || '虚拟人' }}</div>
              <div class="description-text">{{ avatar.description || '暂无描述' }}</div>
            </div>
            <button class="select-btn" @click="avatarId = avatar.avatar_id.trim()">
              {{ avatarId.trim() === avatar.avatar_id.trim() ? '已选择' : '选择' }}
            </button>
          </div>
        </div>
      </div>
    </section>

    <!-- 声音水平滚动区域 -->
    <section class="horizontal-scroll-section">
      <h2>声音 VCN</h2>
      <div class="horizontal-scroll-container">
        <div class="scroll-wrapper">
          <div 
            v-for="voice in voiceList" 
            :key="voice.id" 
            :class="['scroll-item', voiceVcn.trim() === voice.voice_vcn.trim() ? 'selected' : '']"
          >
            <img :src="voice.image_url" alt="voice image" class="scroll-image" />
            <div class="scroll-info">
              <div>{{ voice.description || voice.voice_vcn || '声音' }}</div>
              <div class="description-text">{{ voice.description || '暂无描述' }}</div>
            </div>
            <button class="select-btn" @click="voiceVcn = voice.voice_vcn.trim()">
              {{ voiceVcn.trim() === voice.voice_vcn.trim() ? '已选择' : '选择' }}
            </button>
          </div>
        </div>
      </div>
    </section>

    <button class="confirm-btn" @click="goToInterview">我选好了 开始面试吧</button>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

const isDarkMode = ref(false)
const avatarId = ref('')
const voiceVcn = ref('')
const avatarList = ref([])
const voiceList = ref([])
// 添加欢迎弹窗状态控制
const showWelcomeModal = ref(true)
const router = useRouter()

function toggleDarkMode() {
  isDarkMode.value = !isDarkMode.value
}
function closeWelcomeModal() {
  showWelcomeModal.value = false
}
function goToInterview() {
  if (!avatarId.value || !voiceVcn.value) {
    alert('请先选择形象和声音')
    return
  }

  router.push({
    path: '/intervier',
    query: {
      avatarId: avatarId.value.trim(),
      voiceVcn: voiceVcn.value.trim(),
    },
  })
}

onMounted(() => {
  fetchAvatarList()
  fetchVoiceList()
})

function fetchAvatarList() {
  axios.get('/api/ask/avatar/list').then(res => {
    // 处理数据时去除字段尾部空白
    avatarList.value = (res.data.data || []).map(item => ({
      ...item,
      avatar_id: item.avatar_id.trim(),
      image_url: item.image_url,
      description: item.description,
    }))
  }).catch(() => {
    avatarList.value = []
  })
}

function fetchVoiceList() {
  axios.get('/api/ask/voice/list').then(res => {
    voiceList.value = (res.data.data || []).map(item => ({
      ...item,
      voice_vcn: item.voice_vcn.trim(),
      image_url: item.image_url,
      description: item.description,
    }))
  }).catch(() => {
    voiceList.value = []
  })
}
</script>


<style scoped>
/* 基础变量 */
:root {
  --primary: #6c5ce7;
  --primary-light: #a29bfe;
  --secondary: #00cec9;
  --accent: #fd79a8;
  --dark: #2d3436;
  --light: #f5f6fa;
  --glass-bg: rgba(255, 255, 255, 0.25);
  --glass-border: rgba(255, 255, 255, 0.18);
}

/* 容器样式 */
.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
  min-height: 100vh;
  font-family: 'Inter', 'PingFang SC', sans-serif;
  background: linear-gradient(135deg, #f5f7fa 0%, #dfe6e9 100%);
  transition: all 0.5s ease;
}

.dark-mode {
  background: linear-gradient(135deg, #0f0a24 0%, #2e1065 100%); /* 深紫渐变 */
  --primary: #8b5cf6; /* 电光紫 */
  --primary-light: #c4b5fd; 
  --accent: #10b981; /* 荧光绿点缀 */
}

.dark-mode .scroll-info div:first-child {
  color: #8b5cf6; /* 电光紫，与主色一致 */
  text-shadow: 0 0 10px rgba(139, 92, 246, 0.3); /* 紫色光晕 */
  font-weight: 600;
  letter-spacing: 0.05em; /* 增加字母间距更科技 */
}
.dark-mode .description-text {
  color: #a5b4fc; /* 柔和的薰衣草蓝，提高可读性 */
  font-size: 0.9em;
  line-height: 1.5;
}
/* 模式切换按钮 */
.mode-toggle {
  position: fixed;
  top: 20px;
  right: 20px;
  padding: 0.6rem 1.2rem;
  background: var(--glass-bg);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1px solid var(--glass-border);
  border-radius: 50px;
  color: var(--dark);
  font-weight: 600;
  cursor: pointer;
  z-index: 100;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.dark-mode .mode-toggle {
  background: rgba(0, 0, 0, 0.25);
  color: var(--light);
  border-color: rgba(255, 255, 255, 0.1);
}

.mode-toggle:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15);
}

/* 主标题 */
.main-title {
  text-align: center;
  margin: 2rem 0 3rem;
  font-size: 2.8rem;
  font-weight: 800;
  background: linear-gradient(90deg, var(--primary), var(--secondary));
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  position: relative;
  padding-bottom: 1rem;
}

.main-title::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 100px;
  height: 4px;
  background: linear-gradient(90deg, var(--primary), var(--secondary));
  border-radius: 2px;
}

.dark-mode .main-title {
  text-shadow: 0 2px 10px rgba(108, 92, 231, 0.3);
}

/* 水平滚动区域 */
.horizontal-scroll-section {
  margin-bottom: 3rem;
}

.horizontal-scroll-section h2 {
  font-size: 1.8rem;
  margin-bottom: 1.5rem;
  color: var(--primary);
  display: flex;
  align-items: center;
  gap: 0.8rem;
}

.dark-mode .horizontal-scroll-section h2 {
  color: var(--primary-light);
}

.horizontal-scroll-section h2::before {
  content: '';
  display: inline-block;
  width: 12px;
  height: 12px;
  background: var(--primary);
  border-radius: 50%;
}

.dark-mode .horizontal-scroll-section h2::before {
  background: var(--primary-light);
}

.horizontal-scroll-container {
  width: 100%;
  overflow-x: auto;
  padding-bottom: 20px;
}

.scroll-wrapper {
  display: inline-flex;
  gap: 1.5rem;
  padding: 0 1rem;
}

.scroll-item {
  background: var(--glass-bg);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1px solid var(--glass-border);
  border-radius: 16px;
  padding: 1.5rem;
  text-align: center;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
  min-width: 220px;
  flex-shrink: 0;
}

.scroll-item::before {
  content: '';
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
  transform: rotate(30deg);
  transition: all 0.5s ease;
  opacity: 0;
}

.scroll-item:hover {
  transform: translateY(-8px);
  box-shadow: 0 12px 30px rgba(0, 0, 0, 0.15);
}

.scroll-item:hover::before {
  opacity: 1;
  animation: shine 3s infinite;
}

.scroll-item.selected {
  border: 2px solid var(--primary);
  background: rgba(108, 92, 231, 0.15);
  box-shadow: 0 0 0 4px rgba(108, 92, 231, 0.2);
}

.dark-mode .scroll-item {
  background: rgba(0, 0, 0, 0.2);
  border-color: rgba(255, 255, 255, 0.05);
}

.dark-mode .scroll-item.selected {
 border: 2px solid #10b981; /* 荧光绿边框 */
  background: rgba(16, 185, 129, 0.05); /* 微透绿光 */
}
.dark-mode .scroll-item.selected .scroll-info div:first-child {
  color: #10b981; /* 选中时名称变荧光绿 */
}
.scroll-image {
  width: 100%;
  height: 150px;
  object-fit: cover;
  border-radius: 12px;
  margin-bottom: 1rem;
  transition: all 0.3s ease;
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.1);
  
}

.scroll-item:hover .scroll-image {
  transform: scale(1.05) rotate(1deg);
  box-shadow: 0 12px 25px rgba(0, 0, 0, 0.15);
}

.scroll-info {
  margin-bottom: 1.2rem;
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--dark);
}

.dark-mode .scroll-info {
  color: var(--light);
}

.description-text {
  font-size: 0.9rem;
  color: #666;
  margin-top: 0.5rem;
  line-height: 1.5;
  min-height: 40px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
}

.dark-mode .description-text {
  color: #aaa;
}

/* 选择按钮 */
.select-btn {
  background: linear-gradient(135deg, var(--primary), var(--primary-light));
  border: none;
  border-radius: 50px;
  color: black;
  padding: 0.7rem 1rem;
  font-weight: 600;
  cursor: pointer;
  width: 100%;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
  box-shadow: 0 4px 15px rgba(108, 92, 231, 0.3);
}

.select-btn::after {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
  transition: all 0.5s ease;
}

.select-btn:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 25px rgba(108, 92, 231, 0.4);
}

.select-btn:hover::after {
  left: 100%;
}

.scroll-item.selected .select-btn {
  background: linear-gradient(135deg, var(--secondary), #00b4b4);
  box-shadow: 0 4px 15px rgba(0, 206, 201, 0.3);
}

/* 确认按钮 */
.confirm-btn {
  display: block;
  margin: 3rem auto 0;
  padding: 1rem 3rem;
  font-size: 1.2rem;
  font-weight: 600;
  background: linear-gradient(135deg, var(--primary), var(--primary-light));
  color: black;
  border: none;
  border-radius: 50px;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 8px 25px rgba(108, 92, 231, 0.4);
  position: relative;
  overflow: hidden;
}

.confirm-btn::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.4), transparent);
  transition: all 0.7s ease;
}

.confirm-btn:hover {
  transform: translateY(-5px);
  box-shadow: 0 12px 35px rgba(108, 92, 231, 0.5);
  letter-spacing: 1px;
}

.confirm-btn:hover::before {
  left: 100%;
}

/* 动画效果 */
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes shine {
  0% { transform: rotate(30deg) translate(-10%, -10%); }
  100% { transform: rotate(30deg) translate(10%, 10%); }
}

.scroll-item {
  animation: fadeIn 0.6s ease forwards;
  opacity: 0;
}

.scroll-item:nth-child(1) { animation-delay: 0.1s; }
.scroll-item:nth-child(2) { animation-delay: 0.2s; }
.scroll-item:nth-child(3) { animation-delay: 0.3s; }
.scroll-item:nth-child(4) { animation-delay: 0.4s; }
.scroll-item:nth-child(5) { animation-delay: 0.5s; }
.scroll-item:nth-child(6) { animation-delay: 0.6s; }

/* 隐藏滚动条 */
.horizontal-scroll-container::-webkit-scrollbar {
  height: 8px;
}

.horizontal-scroll-container::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.1);
  border-radius: 4px;
}

.horizontal-scroll-container::-webkit-scrollbar-thumb {
  background: var(--primary);
  border-radius: 4px;
}

.dark-mode .horizontal-scroll-container::-webkit-scrollbar-thumb {
  background: var(--primary-light);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .container {
    padding: 1.5rem;
  }
  
  .main-title {
    font-size: 2rem;
    margin: 1.5rem 0;
  }
  
  .scroll-item {
    min-width: 160px;
    padding: 1rem;
  }
  
  .confirm-btn {
    padding: 0.8rem 2rem;
    font-size: 1rem;
  }
}


/* 欢迎弹窗样式 */
.welcome-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(5px);
  animation: fadeIn 0.3s ease;
}

.welcome-content {
  background: linear-gradient(135deg, #0f0a24, #2e1065);
  border-radius: 16px;
  padding: 2rem;
  width: 90%;
  max-width: 500px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
  border: 1px solid rgba(139, 92, 246, 0.3);
  text-align: center;
}

.welcome-header h2 {
  color: #8b5cf6;
  font-size: 1.8rem;
  margin-bottom: 0.5rem;
}

.welcome-subtitle {
  color: #a5b4fc;
  font-size: 1rem;
  margin-bottom: 2rem;
}

.welcome-body {
  margin: 2rem 0;
}

.welcome-step {
  display: flex;
  align-items: center;
  margin-bottom: 1.5rem;
  padding: 1rem;
  background: rgba(139, 92, 246, 0.1);
  border-radius: 10px;
  color: #e0e7ff;
}

.step-icon {
  width: 30px;
  height: 30px;
  background: #8b5cf6;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 1rem;
  font-weight: bold;
  color: white;
}

.welcome-confirm-btn {
  background: linear-gradient(90deg, #8b5cf6, #10b981);
  color: white;
  border: none;
  border-radius: 50px;
  padding: 1rem 2rem;
  font-size: 1.1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto;
  width: 80%;
}

.welcome-confirm-btn:hover {
  transform: translateY(-3px);
  box-shadow: 0 5px 20px rgba(139, 92, 246, 0.5);
}

.btn-arrow {
  margin-left: 0.5rem;
  transition: all 0.3s ease;
}

.welcome-confirm-btn:hover .btn-arrow {
  transform: translateX(5px);
}

/* 动画 */
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}
</style>