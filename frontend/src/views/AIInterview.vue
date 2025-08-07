<template>
  <div :class="['container', { 'dark-mode': isDarkMode }]">
    <div class="layout-grid">
      <!-- 左上角 - 应聘者信息（动态显示三个字段） -->
  <div class="panel candidate-info">
    <h2 class="panel-title">应聘者信息</h2>
    
    <!-- 添加照片展示框 -->
    <div class="avatar-container">
    <img :src="photoPath " alt="应聘者照片" class="avatar-image">
    <div v-if="!photoPath" class="avatar-placeholder">
      <span>暂无照片</span>
    </div>
  </div>
    <div class="info-item">
      <span class="info-label">姓名：</span>
      <span class="info-value">{{ username }}</span>
    </div>
    <div class="info-item">
      <span class="info-label">职位：</span>
      <span class="info-value">{{ jobTitle }}</span>
    </div>
    <div class="info-item">
      <span class="info-label">职位类别：</span>
      <span class="info-value">{{ jobCategory }}</span>
    </div>
</div>

      <!-- 中间 - 虚拟人区域 -->
      <div class="panel virtual-human">
        <iframe
          ref="demoIframe"
          src="http://localhost:5173"
          allow="microphone; autoplay"
          class="virtual-human-iframe"
        ></iframe>

<!-- 中下角 - 技能点评 -->

<div class="face-analysis">
  <h3 class="analysis-title">表情分析结果</h3>
  <div class="analysis-result">
    <div ref="expressionChartRef" class="expression-chart" style="height: 300px;"></div>
    <div v-if="!faceResult" class="no-data">
      <i class="icon-no-data"></i>
    </div>
  </div>
</div>
      </div>

    
<!-- 右上角 - 视频区域 -->
<div class="panel video-panel">
  <h2 class="panel-title">面试者视频</h2>
  <div class="video-content">
    <div class="video-wrapper">
      <video 
        ref="videoRef" 
        autoplay 
        playsinline 
        class="video-element"
        :class="{'video-active': cameraOn}"
      ></video>
      <canvas ref="canvasRef" style="display:none"></canvas>
      <div v-if="!cameraOn" class="video-overlay">
        <span class="video-placeholder-text">摄像头未开启</span>
      </div>
    </div>
    
  <!-- 修改后的视频控制区域 -->
<div class="video-controls">
  <div class="operation-tips">
    <p>操作提示：</p>
    <ul>
      <li>1. 请先开启虚拟人开启摄像头</li>
      <li>2. 面试结束后请先关闭虚拟人再关闭摄像头</li>
      <li>2. 关闭后请等待几秒</li>
      <li>3. 系统将自动跳转至历史记录</li>
    </ul>
  </div>
  <button 
    @click="cameraOn ? stopCamera() : startCamera()" 
    :class="['camera-btn', cameraOn ? 'btn-stop' : 'btn-start']"
  >
    <i :class="cameraOn ? 'icon-stop' : 'icon-start'"></i>
    {{ cameraOn ? '关闭摄像头' : '开启摄像头' }}
  </button>
</div>
    

  </div>
</div>
      <!-- 左下角 - 语音测评 -->
      <div class="panel evaluation-panel">
        <h2 class="panel-title">
          语音测评雷达图
          <span class="data-status">
            (数据{{ hasEvaluationData ? '已加载' : '加载中或无数据' }})
          </span>
        </h2>
        <div ref="evaluationChartRef" class="chart-container"></div>
      </div>

      <!-- 右下角 - 情绪分析 -->
      <div class="panel sentiment-panel">
        <h2 class="panel-title">
          情绪占比分析
          <span class="data-status">
            (数据{{ hasSentimentData ? '已加载' : '加载中或无数据' }})
          </span>
        </h2>
        <div ref="chartRef" class="chart-container"></div>
      </div>
    </div>
<!-- 在 container div 的末尾添加弹窗 -->
<div v-if="showModal" class="modal-overlay">
  <div class="modal-content">
    <h3>面试即将结束</h3>
    <p>{{ countdown }}秒后将自动跳转到历史记录页面...</p>
    <div class="modal-actions">
      <button @click="redirectNow" class="btn-now">立即跳转</button>
      <button @click="showModal = false" class="btn-cancel">取消</button>
    </div>
  </div>
</div>
    
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, nextTick, watch } from 'vue'
import axios from 'axios'
import * as echarts from 'echarts'
import { useRoute } from 'vue-router'  // 用于获取路由参数

/* ===== 状态 ===== */
const username = ref('加载中...')
const jobTitle = ref('加载中...')
const jobCategory = ref('加载中...')
const lastVoiceRecordId = ref(null)

const subtitle = ref('')
const sendText = ref('')
const demoIframe = ref(null)
const tempBuffer = ref('')
const mainBuffer = ref('')
const photoPath = ref('')
const chartRef = ref(null)
let chartInstance = null
const sentimentData = ref({ positive: 0, neutral: 0, negative: 0 })
const hasSentimentData = ref(false)
const currentInterviewJob = ref(null)
const skillsData = ref(null) //技能部分
const evaluationChartRef = ref(null)
let evaluationChartInstance = null
const evaluationResult = ref('')
const evaluationParsed = ref(null)
const hasEvaluationData = ref(false)
const cachedExpressionSummary = ref(null)  // 用来暂存关闭摄像头时的统计数据

const isDarkMode = ref(true)

/* ===== 路由 ===== */
const route = useRoute()


// 弹窗相关状态
const showModal = ref(false)
const countdown = ref(10)
let countdownTimer = null

//uuid
const questionSetId = localStorage.getItem('question_set_id') || ''
console.log('当前 question_set_id:', questionSetId)


/* ===== 常量 ===== */
const MERGE_INTERVAL = 1000
const SAVE_INTERVAL = 3000
// 收集统计数据：统计每种表情出现的次数
const expressionSummary = ref({})  // { 2: 5, 6: 3, ... }

const skillKeys = ['creativity', 'language_expression', 'logical_thinking', 'stress_response']

const skillLabels = {
  creativity: '创意',
  language_expression: '语言表达',
  logical_thinking: '逻辑思维',
  stress_response: '抗压能力',
}


// 新增摄像头相关状态
const videoRef = ref(null)
const canvasRef = ref(null)
const cameraOn = ref(false)
const captureInterval = ref(null)
//获取微表情识别
// 表情标签映射
// 微表情识别结果
const faceResult = ref(null)  // 存接口返回的data对象

// 表情标签映射
const expressionLabels = [
  '其他(非人脸)', '其他表情', '喜悦', '愤怒', '悲伤', '惊恐', '厌恶', '中性'
]

// 微表情图表相关
const expressionChartRef = ref(null)
let expressionChartInstance = null

function startCamera() {
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    alert('当前浏览器不支持摄像头访问')
    return
  }
  // 重置统计数据
  expressionSummary.value = {}

  navigator.mediaDevices.getUserMedia({ video: true })
    .then(stream => {
      cameraOn.value = true
      videoRef.value.srcObject = stream
      videoRef.value.play()
      startCapture()
    })
    .catch(err => {
      alert('摄像头开启失败: ' + err.message)
    })
}


// 关闭摄像头时调用
async function stopCamera() {
  if (videoRef.value && videoRef.value.srcObject) {
    videoRef.value.srcObject.getTracks().forEach(track => track.stop())
  }

  cameraOn.value = false
  if (captureInterval.value) clearInterval(captureInterval.value)

  // 如果录音ID还没准备好，先缓存统计数据，等录音保存成功后统一发
  if (!lastVoiceRecordId.value) {
    cachedExpressionSummary.value = { ...expressionSummary.value }
    console.log('关闭摄像头时无录音ID，缓存表情统计数据，等待录音结束保存')
  } else {
    console.log('关闭摄像头时录音ID存在，直接保存统计数据:', JSON.stringify(expressionSummary.value))
    await saveSummaryToBackend()
    cachedExpressionSummary.value = null
  }

// 显示弹窗并开始倒计时
  showModal.value = true
  startCountdown()
}

// 开始倒计时
function startCountdown() {
  countdown.value = 6
  countdownTimer = setInterval(() => {
    countdown.value--
    if (countdown.value <= 0) {
      clearInterval(countdownTimer)
      window.location.href = 'http://localhost:5174/candidate/history'
    }
  }, 1000)
}

// 立即跳转
function redirectNow() {
  clearInterval(countdownTimer)
  window.location.href = 'http://localhost:5174/candidate/history'
}



// 保存统计数据到后端
async function saveSummaryToBackend() {
  const user = JSON.parse(localStorage.getItem('user') || '{}')
  const userId = user.id
  const recordId = lastVoiceRecordId.value

  if (!recordId) {
    console.error('无法保存表情统计数据，recordId为空')
    return
  }

  try {
    const res = await axios.post('/api/voice_record/face_expression', {
      user_id: userId,
      record_id: recordId,
      summary: true,
      summary_data: expressionSummary.value,
      job_title: jobTitle.value,
      question_set_id: questionSetId 
    })
    console.log('保存统计接口返回:', res.data)
    if (res.data.code === 0) {
      console.log('统计数据已保存')
    } else {
      console.warn('保存统计失败:', res.data.desc)
    }
  } catch (e) {
    console.error('保存统计异常:', e)
  }
}


function startCapture() {
  captureInterval.value = setInterval(() => {
    captureAndSend()
  }, 3000) // 每3秒截一次
}

async function captureAndSend() {
  const video = videoRef.value
  const canvas = canvasRef.value
  if (!video || !canvas) {
    console.warn('摄像头或画布未准备好')
    return
  }

  // 捕捉视频帧为图片
  canvas.width = video.videoWidth
  canvas.height = video.videoHeight
  const ctx = canvas.getContext('2d')
  ctx.drawImage(video, 0, 0, canvas.width, canvas.height)

  // 转为 JPEG base64 编码（去掉前缀）
  const base64 = canvas.toDataURL('image/jpeg', 0.8)
  const base64Data = base64.replace(/^data:image\/\w+;base64,/, '')
  
  // 获取用户ID 和 刚保存的录音记录ID
  const user = JSON.parse(localStorage.getItem('user') || '{}')
  const userId = user.id
  const recordId = lastVoiceRecordId.value  // 你前面在 saveToBackend() 里存的
  console.log('传给表情接口的 recordId:', recordId)
   try {
    const res = await axios.post(
      '/api/voice_record/face_expression',
      {
        image_base64: base64Data,
        user_id: userId,
        record_id: recordId
      },
      { headers: { 'Content-Type': 'application/json' } }
    )

    if (res.data.code === 0 && res.data.data) {
      const data = res.data.data
      faceResult.value = data

      const rates = data?.fileList?.[0]?.rates || []
      console.log('本次微表情识别 rates:', rates)

      // 按索引累加每个概率
      for (let i = 0; i < rates.length; i++) {
        expressionSummary.value[i] = (expressionSummary.value[i] || 0) + rates[i]
      }
      console.log('累计统计:', JSON.stringify(expressionSummary.value))
    } else {
      faceResult.value = null
    }

  } catch (e) {
    faceResult.value = null
    console.error('请求失败:', e)
  }
}
// 监听 faceResult 变化，自动渲染图表
watch(faceResult, async (newVal) => {
  let rates = []
  if (newVal && newVal.fileList && newVal.fileList.length > 0) {
    rates = newVal.fileList[0].rates || []
  }
  await nextTick()
  renderExpressionChart(rates)
})



// 渲染微表情饼图
// 渲染微表情柱状图
function renderExpressionChart(rates) {
  if (!expressionChartRef.value) return;

  if (!expressionChartInstance) {
    expressionChartInstance = echarts.init(expressionChartRef.value);
  }

  // 无数据时填充0，长度8
  if (!rates || rates.length !== 8) {
    rates = new Array(8).fill(0);
  }

  const option = {
    backgroundColor: 'transparent',
    title: {
      text: '微表情分析',
      left: 'center',
      textStyle: { 
        color: isDarkMode.value ? '#00eaff' : '#1890ff',
        fontSize: 16 
      }
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: '{b}: {c}%'
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      top: '20%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: expressionLabels,
      axisLabel: {
        color: isDarkMode.value ? '#7f9bb3' : '#666',
        fontSize: 12,
        interval: 0,
        rotate: 30 // 标签旋转30度防止重叠
      },
      axisLine: {
        lineStyle: {
          color: isDarkMode.value ? 'rgba(127,155,179,0.3)' : 'rgba(102,102,102,0.3)'
        }
      },
      axisTick: { show: false }
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        color: isDarkMode.value ? '#7f9bb3' : '#666',
        fontSize: 12,
        formatter: '{value}%'
      },
      splitLine: {
        lineStyle: {
          color: isDarkMode.value ? 'rgba(127,155,179,0.1)' : 'rgba(102,102,102,0.1)'
        }
      }
    },
    series: [{
      name: '出现概率',
      type: 'bar',
      barWidth: '60%',
      data: rates.map(rate => (rate * 100).toFixed(1)),
      itemStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: '#1890ff' },
          { offset: 1, color: '#0050b3' }
        ]),
        borderRadius: [4, 4, 0, 0]
      },
      label: {
        show: true,
        position: 'top',
        color: isDarkMode.value ? '#00eaff' : '#1890ff',
        formatter: '{c}%'
      }
    }]
  };

  expressionChartInstance.setOption(option);
}


// 组件卸载时清理
onBeforeUnmount(() => {
   if (countdownTimer) clearInterval(countdownTimer)
  stopCamera()
  if (expressionChartInstance.value) {
    expressionChartInstance.dispose()
    expressionChartInstance = null
  }
})

/* ===== 定时器句柄 ===== */
let mergeTimer = null
let saveTimer = null

/* ===== 明暗模式切换 ===== */
function toggleDarkMode() {
  isDarkMode.value = !isDarkMode.value
  nextTick(() => {
    renderChart()
    renderEvaluationChart()
  })
}

/* ===== 发送 avatarId 和 voiceVcn 给 iframe ===== */
function postAvatarAndVoice() {
  const avatarId = route.query.avatarId || ''
  const voiceVcn = route.query.voiceVcn || ''

  console.log('[发送给iframe] avatar_id:', avatarId, 'voice_vcn:', voiceVcn)

  if (demoIframe.value && demoIframe.value.contentWindow) {
    demoIframe.value.contentWindow.postMessage(
      {
        type: 'set_avatar_voice',
        payload: {
          avatar_id: avatarId,
          voice_vcn: voiceVcn,
        },
      },
      'http://localhost:5173'
    )
  }
}


/* ===== 处理 iframe 消息 ===== */
function handleMessage(event) {
  if (event.origin !== 'http://localhost:5173') return

  if (event.data.type === 'subtitle_update') {
    const text = event.data.text || ''
    subtitle.value = text
    tempBuffer.value += text.endsWith(' ') ? text : text + ' '
  } else if (event.data.type === 'audio_blob') {
    const audioBase64 = event.data.audioData
    console.log('[收到音频数据]', audioBase64)
    uploadAudio(audioBase64)
  }
}

/* ===== 合并缓存 ===== */
function mergeTempToMain() {
  if (tempBuffer.value.trim()) {
    mainBuffer.value += tempBuffer.value
    console.log('[合并] 当前主缓存 =>', mainBuffer.value)
    tempBuffer.value = ''
  }
}

/* ===== 保存并分析 ===== */
async function saveToBackend() {
  mergeTempToMain()
  if (!mainBuffer.value.trim()) return

  try {
    const user = JSON.parse(localStorage.getItem('user') || '{}')
    const userId = user.id

    if (!userId) {
      console.warn('未获取到登录用户 ID')
      return
    }

    console.log('准备发送数据:', {
      user_id: userId,
      transcription: mainBuffer.value,
    })

    const res = await axios.post('/api/voice_record/save', {
      user_id: userId,
      transcription: mainBuffer.value,
    })

    console.log('[保存成功]', res.data)

    const voiceId = res.data.id  // 录音记录id

    // 只在第一次赋值，后续不覆盖
    if (!lastVoiceRecordId.value) {
      lastVoiceRecordId.value = voiceId
      console.log('首次设置lastVoiceRecordId:', lastVoiceRecordId.value)
    } else {
      console.log('已有lastVoiceRecordId，不更新:', lastVoiceRecordId.value)
    }

    // 录音保存成功后，如果缓存了表情统计数据，触发保存
    if (cachedExpressionSummary.value) {
      expressionSummary.value = { ...cachedExpressionSummary.value }
      cachedExpressionSummary.value = null
      await saveSummaryToBackend()
    }

    // 其他逻辑，渲染情绪图表等
    const emotionJson = res.data.sentiment?.emotion || {}

    sentimentData.value = {
      positive: emotionJson.positive || 0,
      neutral: emotionJson.neutral || 0,
      negative: emotionJson.negative || 0,
    }

    hasSentimentData.value = true

    await nextTick()
    renderChart()
  } catch (e) {
    console.error('[保存失败]', e)
  }
}
// 获取最新情绪
async function fetchLatestSentiment() {
  try {
    const user = JSON.parse(localStorage.getItem('user') || '{}')
    const userId = user.id

    if (!userId) {
      console.warn('未获取到登录用户 ID')
      return
    }

    const res = await axios.get(`/api/voice_record/latest_sentiment?user_id=${userId}`)

    if (res.data && res.data.sentiment) {
      const emotionJson = res.data.sentiment?.emotion || {}
      const skillsJson = res.data.sentiment?.skills || null

      sentimentData.value = {
        positive: emotionJson.positive || 0,
        neutral: emotionJson.neutral || 0,
        negative: emotionJson.negative || 0,
      }
      hasSentimentData.value = true

      if (skillsJson) {
        skillsData.value = skillsJson
      } else {
        skillsData.value = null
      }
    } else {
      hasSentimentData.value = false
      skillsData.value = null
    }

    await nextTick()
    renderChart()
  } catch (error) {
    console.error('[获取最新情绪失败]', error)
    hasSentimentData.value = false
    skillsData.value = null
    await nextTick()
    renderChart()
  }
}



/* ===== 上传音频到服务器 ===== */
async function uploadAudio(base64Audio) {
  try {
    const base64Data = base64Audio.split(',')[1]
    const binaryString = atob(base64Data)
    const len = binaryString.length
    const uint8Array = new Uint8Array(len)
    for (let i = 0; i < len; i++) {
      uint8Array[i] = binaryString.charCodeAt(i)
    }
    const blob = new Blob([uint8Array], { type: 'audio/webm' })

    // === 获取当前登录用户 ID ===
    const user = JSON.parse(localStorage.getItem('user') || '{}')
    const userId = user.id

    if (!userId) {
      console.warn('未获取到登录用户 ID')
      return
    }

    // 这里直接用 this.currentInterviewJob.id
const jobId = currentInterviewJob.value?.id || localStorage.getItem('current_job_id')

    if (!jobId) {
      console.warn('未获取到申请的 job_id')
      return
    }

    const formData = new FormData()
    formData.append('file', blob, 'record.webm')
    formData.append('user_id', userId)
    formData.append('job_id', jobId)

    const res = await axios.post('/api/apply/upload_audio', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })

    console.log('[音频上传成功]', res.data)
  } catch (error) {
    console.error('[音频上传失败]', error)
  }
}

/* ===== 获取语音测评结果 ===== */
async function fetchEvaluationResult() {
  try {
    const user = JSON.parse(localStorage.getItem('user') || '{}')
    const userId = user.id || ''
    const jobId = localStorage.getItem('current_job_id') || ''

    const res = await axios.get(`/api/apply/evaluation`, {
      params: { user_id: userId, job_id: jobId },
    })

    const result = res.data.evaluation_result || ''

    evaluationResult.value = result

    if (result && result.trim()) {
      try {
        const parsed = JSON.parse(result)
        if (parsed && parsed.xml) {
          evaluationParsed.value = parseEvaluationXML(parsed.xml)
          hasEvaluationData.value = true
        } else {
          evaluationParsed.value = null
          hasEvaluationData.value = false
        }
      } catch (parseError) {
        console.error('JSON 解析错误:', parseError)
        evaluationParsed.value = null
        hasEvaluationData.value = false
      }
    } else {
      evaluationParsed.value = null
      hasEvaluationData.value = false
    }

    await nextTick()
    renderEvaluationChart()
  } catch (error) {
    console.error('[语音测评获取失败]', error)
    evaluationParsed.value = null
    hasEvaluationData.value = false
    await nextTick()
    renderEvaluationChart()
  }
}

/* ===== 解析语音测评XML ===== */
function parseEvaluationXML(xmlStr) {
  try {
    const parser = new DOMParser()
    const xmlDoc = parser.parseFromString(xmlStr, 'text/xml')
    const readNode = xmlDoc.querySelector('rec_paper > read_sentence')
    if (!readNode) {
      console.warn('[未找到评分节点]')
      return null
    }
    const getScore = (attr) => {
      const val = readNode.getAttribute(attr)
      return val ? parseFloat(parseFloat(val).toFixed(1)) : 0
    }
    return {
      fluency_score: getScore('fluency_score'),
      tone_score: getScore('tone_score'),
      phone_score: getScore('phone_score'),
      integrity_score: getScore('integrity_score'),
      total_score: getScore('total_score'),
    }
  } catch (err) {
    console.error('[XML解析失败]', err)
    return null
  }
}

/* ===== 渲染情绪柱状图 ===== */
function renderChart() {
  if (!chartRef.value) return
  if (!chartInstance) {
    chartInstance = echarts.init(chartRef.value)
  }

  const textColor = isDarkMode.value ? '#00eaff' : '#333'
  const bgColor = isDarkMode.value ? '#0f1c2f' : '#fff'

  chartInstance.setOption({
    backgroundColor: bgColor,
    title: {
      text: '情绪分析占比',
      left: 'center',
      top: '5%',
      textStyle: {
        color: textColor,
        fontSize: 16,
        fontWeight: 'bold'
      }
    },
    tooltip: {
      trigger: 'item',
      formatter: '{b} : {d}%',
      backgroundColor: isDarkMode.value ? '#1f1f1f' : '#fff',
      borderColor: isDarkMode.value ? '#00eaff' : '#ccc',
      textStyle: {
        color: textColor
      }
    },
    legend: {
      orient: 'horizontal',
      top: 'auto',
      bottom: '2%',
      textStyle: {
        color: textColor,
        fontSize: 13
      },
      itemGap: 25,
      data: ['积极情绪', '中性情绪', '消极情绪']
    },
    series: [
      {
        name: '情绪占比',
        type: 'pie',
        radius: ['45%', '65%'],
        avoidLabelOverlap: true,
        itemStyle: {
          borderRadius: 8,
          borderColor: bgColor,
          borderWidth: 2
        },
        label: {
          show: true,
          position: 'outside',
          formatter: '{b}: {d}%',
          color: textColor
        },
        labelLine: {
          length: 15,
          length2: 10,
          lineStyle: {
            color: textColor
          }
        },
        data: [
          {
            value: sentimentData.value.positive,
            name: '积极情绪',
            itemStyle: {
              color: {
                type: 'linear',
                x: 0,
                y: 0,
                x2: 1,
                y2: 1,
                colorStops: [
                  { offset: 0, color: '#00ffaa' },
                  { offset: 1, color: '#009966' }
                ]
              }
            }
          },
          {
            value: sentimentData.value.neutral,
            name: '中性情绪',
            itemStyle: {
              color: {
                type: 'linear',
                x: 1,
                y: 0,
                x2: 0,
                y2: 1,
                colorStops: [
                  { offset: 0, color: '#9be7ff' },
                  { offset: 1, color: '#1890ff' }
                ]
              }
            }
          },
          {
            value: sentimentData.value.negative,
            name: '消极情绪',
            itemStyle: {
              color: {
                type: 'linear',
                x: 1,
                y: 1,
                x2: 0,
                y2: 0,
                colorStops: [
                  { offset: 0, color: '#ff6a6a' },
                  { offset: 1, color: '#f5222d' }
                ]
              }
            }
          }
        ]
      }
    ]
  })
}

/* ===== 渲染语音测评雷达图 ===== */
function renderEvaluationChart() {
  if (!evaluationChartRef.value) return
  if (!evaluationChartInstance) {
    evaluationChartInstance = echarts.init(evaluationChartRef.value)
  }

  const data = evaluationParsed.value
    ? [
        evaluationParsed.value.fluency_score || 0,
        evaluationParsed.value.tone_score || 0,
        evaluationParsed.value.phone_score || 0,
        evaluationParsed.value.integrity_score || 0,
        evaluationParsed.value.total_score || 0,
      ]
    : [0, 0, 0, 0, 0]

  evaluationChartInstance.setOption({
    backgroundColor: isDarkMode.value ? '#2b2f38' : '#fff',
    tooltip: {
      trigger: 'item',
      textStyle: {
        color: '#fff',
        fontSize: 12,
      },
      backgroundColor: '#333',
      borderColor: '#666',
    },
    legend: {
      top: 10,
      data: ['候选人能力', '岗位要求'],
      textStyle: {
        color: '#ddd',
      },
      icon: 'rect',
    },
    radar: {
      shape: 'polygon',
      radius: '70%',
      indicator: [
        { name: '流利度', max: 100 },
        { name: '音调准确度', max: 100 },
        { name: '发音准确度', max: 100 },
        { name: '完整度', max: 100 },
        { name: '综合评分', max: 100 },
      ],
      splitNumber: 5,
      axisName: {
        color: '#ddd',
        fontSize: 13,
      },
      splitLine: {
        lineStyle: {
          color: '#444',
        },
      },
      splitArea: {
        areaStyle: {
          color: ['transparent'],
        },
      },
      axisLine: {
        lineStyle: {
          color: '#444',
        },
      },
    },
    series: [
      {
        name: '评分',
        type: 'radar',
        symbol: 'circle',
        symbolSize: 6,
        areaStyle: {
          opacity: 0,
        },
        lineStyle: {
          width: 2,
          color: '#00c0ff',
        },
        itemStyle: {
          color: '#00c0ff',
        },
        data: [
          {
            value: data,
            name: '候选人能力',
          },
          {
            value: [70, 60, 60, 80, 60], // 假设岗位要求的基准线
            name: '评分标准',
            lineStyle: {
              color: '#aaa',
              type: 'dashed',
            },
            itemStyle: {
              color: '#aaa',
            },
          },
        ],
      },
    ],
  })
}

/* ===== 监听语音测评分数变化，更新雷达图 ===== */
watch(evaluationParsed, async () => {
  await nextTick()
  renderEvaluationChart()
})

/* ===== 生命周期 ===== */
onMounted(() => {
  window.addEventListener('message', handleMessage)
  mergeTimer = setInterval(mergeTempToMain, MERGE_INTERVAL)
  saveTimer = setInterval(saveToBackend, SAVE_INTERVAL)
  fetchLatestSentiment()
  fetchEvaluationResult()
  fetchUserJobInfo()
 // 初始渲染图表（无数据）
  renderExpressionChart([])
  // 延迟1秒发送 avatarId 和 voiceVcn 给 iframe，确保iframe加载完毕
  setTimeout(() => {
    postAvatarAndVoice()
  }, 1000)
})

onBeforeUnmount(() => {
  window.removeEventListener('message', handleMessage)
  clearInterval(mergeTimer)
  clearInterval(saveTimer)
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
  if (evaluationChartInstance) {
    evaluationChartInstance.dispose()
    evaluationChartInstance = null
  }
})

/* ===== 获取应聘者信息 ===== */
async function fetchUserJobInfo() {
  try {
    const user = JSON.parse(localStorage.getItem('user') || '{}')
    const jobId = localStorage.getItem('current_job_id') || ''

    if (!user.id) {
      console.warn('没有登录用户ID')
      return
    }
    if (!jobId) {
      console.warn('没有申请岗位ID')
      return
    }

    const res = await axios.get('/api/user/job_info', {
      params: {
        user_id: user.id,
        job_id: jobId
      }
    })

    const defaultValue = '未知'
    username.value = res.data.username || defaultValue
    jobTitle.value = res.data.job_title || defaultValue
    jobCategory.value = res.data.job_category || defaultValue
    photoPath.value = res.data.photo_path || ''

  } catch (error) {
    username.value = '请求失败'
    jobTitle.value = '-'
    jobCategory.value = '-'
    photoPath.value = ''
    console.error('获取应聘者信息失败', error)
  }
}
</script>

<style scoped>
/* 基础样式 */
.container {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
  min-height: 100vh;
  background-color: #f5f7fa;
  color: #333;
  transition: all 0.3s ease;
}

.container.dark-mode {
  background-color:#0d1b2a;
  color: #e0e0e0;
}

.mode-toggle {
  position: fixed;
  top: 20px;
  right: 20px;
  padding: 8px 16px;
  background-color: #1890ff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  z-index: 100;
  font-size: 14px;
}

.main-title {
  font-size: 28px;
  text-align: center;
  margin-bottom: 30px;
  color: inherit;
}

/* 布局网格 */
.layout-grid {
  display: grid;
  grid-template-columns: 350px 1fr 380px;
  grid-template-rows: auto auto;
  gap: 20px;
  grid-template-areas:
    "candidate-info virtual-human video-panel"
    "evaluation-panel virtual-human sentiment-panel";
}

/* 面板通用样式 */
.panel {
  background-color: #fff;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.dark-mode .panel {
  background-color: #2c2c2c;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
}

.panel-title {
  font-size: 18px;
  margin-bottom: 15px;
  color: inherit;
  border-bottom: 1px solid #eee;
  padding-bottom: 10px;
}

.dark-mode .panel-title {
  border-bottom-color: #444;
}

.data-status {
  font-size: 12px;
  color: #888;
}

/* 应聘者信息 */
.candidate-info {
  grid-area: candidate-info;
   width: 350px; /* 原为300px，减小宽度 */
  padding: 25px; /* 原为20px，减小内边距 */
   max-height: 360px;
}

.info-item {
  margin-bottom: 16px;
  font-size: 15px;
}

.info-label {
  font-weight: 600;
  color: #666;
}

.dark-mode .info-label {
  color: #aaa;
}

.info-value {
  color: #333;
}

.dark-mode .info-value {
  color: #e0e0e0;
}

/* 虚拟人区域 */
.virtual-human {
  grid-area: virtual-human;
  display: flex;
  flex-direction: column;
   gap: 10px;
  padding: 15px;
   width: 100%; /* 缩小宽度为80% */
   padding-bottom: 20px;
}

.virtual-human-iframe {
  width: 100%;
  height: 380px;
  border: none;
  border-radius: 6px;
  background-color: #000;
  margin: 0;
   margin-bottom: 15px; /* 增加与技能点评的间距 */
}

.control-buttons {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.control-btn {
  padding: 10px 15px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.control-btn:hover {
  opacity: 0.9;
}

.start-btn {
  background-color: #52c41a;
  color: white;
}

.interrupt-btn {
  background-color: #faad14;
  color: white;
}

.end-btn {
  background-color: #f5222d;
  color: white;
}

.transcribe-btn {
  background-color: #722ed1;
  color: white;
}

.send-text-group {
  display: flex;
  flex: 1;
  min-width: 200px;
}

.send-text-input {
  flex: 1;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px 0 0 4px;
  font-size: 14px;
  outline: none;
}

.dark-mode .send-text-input {
  background-color: #333;
  border-color: #444;
  color: #e0e0e0;
}

.send-btn {
  background-color: #1890ff;
  color: white;
  border-radius: 0 4px 4px 0;
}

.subtitle-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.subtitle-title {
  font-size: 16px;
  margin-bottom: 10px;
  color: inherit;
}

.subtitle-content {
  flex: 1;
  padding: 15px;
  background-color: #f9f9f9;
  border-radius: 6px;
  border: 1px solid #eee;
  overflow-y: auto;
  font-size: 15px;
  line-height: 1.5;
}

.dark-mode .subtitle-content {
  background-color: #333;
  border-color: #444;
}

/* 视频区域 */
/* 视频面板 */
.video-panel {
  grid-area: video-panel;
}

.video-content {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.video-wrapper {
  position: relative;
  width: 100%;
  aspect-ratio: 16/9;
  border-radius: 8px;
  overflow: hidden;
  background-color: #000;
}

.video-element {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
  transition: opacity 0.3s;
}

.video-element.video-active {
  opacity: 1;
}

.video-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: rgba(0, 0, 0, 0.5);
}

.video-placeholder-text {
  color: #fff;
  font-size: 16px;
}

.video-controls {
  display: flex;
  justify-content: center;
}

.camera-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 8px 16px;
  border: none;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s;
  gap: 6px;
}

.btn-start {
  background-color: #1890ff;
  color: white;
}

.btn-stop {
  background-color: #f5222d;
  color: white;
}

.camera-btn i {
  font-size: 14px;
}

/* 表情分析区域 */
.face-analysis {
  background-color: var(--face-bg);
  border-radius: 8px;
  padding: 12px;
  margin-top: 10px;
}

.analysis-title {
  font-size: 15px;
  margin-bottom: 10px;
  color: var(--analysis-title-color);
  display: flex;
  align-items: center;
  gap: 6px;
}

.analysis-result {
  height: 300px;
  overflow-y: auto;
  padding: 10px;
   background-color: #1a1a1a;  /* 深色背景 */
  border-radius: 6px;
  font-family: 'Courier New', monospace;
}

.analysis-result pre {
  margin: 0;
  font-size: 12px;
  line-height: 1.5;
  color: var(--analysis-text-color);
  white-space: pre-wrap;
}

.no-data {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--analysis-placeholder-color);
  font-size: 13px;
  gap: 8px;
}

/* 暗黑模式适配 */
.dark-mode .face-analysis {
  --analysis-bg: #2a2a2a;
  --analysis-title-color: #e0e0e0;
  --analysis-result-bg: #1a1a1a;
  --analysis-text-color: #0f0;
  --analysis-placeholder-color: #666;
}

.dark-mode .analysis-result {
  border: 1px solid #333;
}

.dark-mode .no-data i {
  color: #555;
}

/* 亮色模式 */
:not(.dark-mode) .face-analysis {
  --analysis-bg: #f5f7fa;
  --analysis-title-color: #333;
  --analysis-result-bg: #f0f0f0;
  --analysis-text-color: #333;
  --analysis-placeholder-color: #999;
}

:not(.dark-mode) .analysis-result {
  border: 1px solid #e0e0e0;
}
.video-panel {
  grid-area: video-panel;
}

.video-container {
  width: 100%;
  aspect-ratio: 4/3;
  background-color: #f0f0f0;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}

.dark-mode .video-container {
  background-color: #333;
}

.video-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 15px;
  color: #888;
}

.dark-mode .video-placeholder {
  color: #aaa;
}

.video-control-btn {
  padding: 8px 16px;
  background-color: #1890ff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

/* 图表区域 */
.chart-container {
  width: 100%;
  height: 480px;
  position: relative; /* 为图表定位做准备 */
  flex: 1; /* 占据剩余空间 */
  
}

.evaluation-panel {
    position: relative;
  grid-area: evaluation-panel;
    top: -100px;  /* 向上移动50像素 */
     display: flex;
  flex-direction: column;
  height: 100%; /* 继承父容器高度 */
  overflow: hidden; /* 防止内容溢出 */
   width: 100%;
   
}

.sentiment-panel {
  grid-area: sentiment-panel;
}

/* 响应式调整 */
@media (max-width: 1200px) {
  .layout-grid {
    grid-template-columns: 1fr 1fr;
    grid-template-areas:
      "candidate-info video-panel"
      "virtual-human virtual-human"
      "evaluation-panel sentiment-panel";
  }
}

@media (max-width: 768px) {
  .layout-grid {
    grid-template-columns: 1fr;
    grid-template-areas:
      "candidate-info"
      "video-panel"
      "virtual-human"
      "sentiment-panel"
      "evaluation-panel";
  }
}
/* 圆形头像容器 */
.avatar-container {
  width: 120px;
  height: 120px;
  margin: 0 auto 15px;
  border-radius: 50%;
  overflow: hidden;
  position: relative;
  border: 3px solid #e0e0e0;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  background-color: #f8f8f8;
  display: flex;
  justify-content: center;
  align-items: center;
}

/* 头像图片 */
.avatar-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

/* 头像占位符 */
.avatar-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: #e0e0e0;
  color: #999;
  font-size: 14px;
}

/* 暗黑模式适配 */
.dark-mode .avatar-container {
  border-color: #444;
  background-color: #2a2a2a;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
}

.dark-mode .avatar-placeholder {
  background-color: #333;
  color: #777;
}

/* 技能点评面板 */
.skills-panel {
  grid-area: virtual-human;
  display: flex;
  flex-direction: column;
   padding: 12px;
    margin-top: 20px; /* 增加上边距 */
  padding-top: 20px; /* 可选：增加内上边距 */
  border-top: 1px solid #eee; /* 可选：添加分隔线 */
    background: rgba(30, 30, 60, 0.8);
  border-radius: 12px;
  padding: 16px;
  color: #fff;
}

.skills-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 16px;
}

.skill-item {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 10px;
  padding: 12px;
  box-shadow: 0 2px 6px rgba(0,0,0,0.2);
  transition: all 0.3s ease;
}

.skill-item:hover {
  transform: translateY(-4px);
  background: rgba(255, 255, 255, 0.1);
}

.skill-label {
  font-weight: bold;
  font-size: 14px;
  color: #cfcfff;
}

.skill-chart-container {
  margin-top: 8px;
  display: flex;
  justify-content: center;
  align-items: center;
}

.skill-chart {
  position: relative;
  width: 80px;
  height: 80px;
}

.circular-chart {
  width: 100%;
  height: 100%;
  transform: rotate(-90deg);
}

.circle-bg {
  fill: none;
  stroke: #eee;
  stroke-width: 3.8;
}

.circle-fill {
  fill: none;
  stroke: #00c3ff;
  stroke-width: 3.8;
  stroke-linecap: round;
  transition: stroke-dasharray 0.5s ease;
}

.skill-score {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-size: 16px;
  color: #ffffff;
  font-weight: bold;
}

.skill-comment {
  margin-top: 10px;
  font-size: 13px;
  color: #ccc;
  min-height: 32px;
}

.circular-chart {
  display: block;
  width: 100%;
  height: 100%;
}

.circle-bg {
  fill: none;
  stroke: #eee;
  stroke-width: 3;
}

.dark-mode .circle-bg {
  stroke: #444;
}

.circle-fill {
  fill: none;
  stroke-width: 3;
  stroke-linecap: round;
  animation: circle-fill-animation 1.5s ease-in-out forwards;
}

.skill-item:nth-child(1) .circle-fill {
  stroke: #4CC790;
}

.skill-item:nth-child(2) .circle-fill {
  stroke: #3A7BD5;
}

.skill-item:nth-child(3) .circle-fill {
  stroke: #F27121;
}

.skill-item:nth-child(4) .circle-fill {
  stroke: #8E54E9;
}

.skill-score {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-size: 12px;
  font-weight: bold;
  color: var(--skill-score-color);
}

.dark-mode .skill-score {
  color: #fff;
}

.skill-comment {
  font-size: 13px;
  line-height: 1.5;
  color: var(--skill-comment-color);
  padding: 8px;
  background: var(--skill-comment-bg);
  border-radius: 6px;
  margin-top: 10px;
}

.dark-mode .skill-comment {
  color: #ccc;
  background: #333;
}

.no-skills {
  text-align: center;
  padding: 20px;
  color: #888;
}

.dark-mode .no-skills {
  color: #666;
}

@keyframes circle-fill-animation {
  0% {
    stroke-dasharray: 0, 100;
  }
}
/* 微表情识别面板 */
.face-analysis {
  background-color: var(--face-bg);
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 8px 16px rgba(0, 150, 255, 0.15);
  transition: background-color 0.3s ease;
  color: var(--face-text);
  display: flex;
  flex-direction: column;
  align-items: center;
  min-height: 340px;
}

.analysis-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--face-title);
  margin-bottom: 18px;
  user-select: none;
}

.analysis-result {
  width: 100%;
  flex-grow: 1;
  position: relative;
  min-height: 280px;
  display: flex;
  justify-content: center;
  align-items: center;
}

.expression-chart {
  width: 100%;
  max-width: 480px;
  height: 280px;
}

/* 无数据提示 */
.no-data {
  font-size: 16px;
  color: var(--face-placeholder);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
}

.no-data i.icon-no-data {
  font-size: 48px;
  color: var(--face-placeholder-icon);
}

/* 弹窗样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background-color: white;
  padding: 25px;
  border-radius: 8px;
  max-width: 400px;
  width: 90%;
  text-align: center;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
}

.dark-mode .modal-content {
  background-color: #2c2c2c;
  color: #e0e0e0;
}

.modal-content h3 {
  margin-top: 0;
  margin-bottom: 15px;
  font-size: 20px;
}

.modal-actions {
  display: flex;
  justify-content: center;
  gap: 15px;
  margin-top: 20px;
}

.btn-now, .btn-cancel {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.btn-now {
  background-color: #1890ff;
  color: white;
}

.btn-cancel {
  background-color: #f5f5f5;
  color: #333;
}

.dark-mode .btn-cancel {
  background-color: #444;
  color: #e0e0e0;
}
/* 操作提示样式 */
.operation-tips {
  background-color: rgba(24, 144, 255, 0.1);
  border-left: 3px solid #1890ff;
  padding: 10px 15px;
  margin-bottom: 15px;
  border-radius: 4px;
  font-size: 13px;
  line-height: 1.6;
}

.dark-mode .operation-tips {
  background-color: rgba(24, 144, 255, 0.2);
  border-left-color: #00eaff;
}

.operation-tips p {
  font-weight: bold;
  margin-bottom: 5px;
  color: #1890ff;
}

.dark-mode .operation-tips p {
  color: #00eaff;
}

.operation-tips ul {
  margin: 0;
  padding-left: 20px;
}

.operation-tips li {
  margin-bottom: 3px;
}
</style>