import React, { useEffect, useRef, useState } from 'react'
import { Button, message, Spin } from 'antd'
import AvatarPlatform, { PlayerEvents, SDKEvents } from './testSdk/3.1.2.1002/avatar-sdk-web_3.1.2.1002/index.js'
import VoiceRecorder, { VoiceRecorderRef } from './components/VoiceRecorder'

const SDK_CONFIG = {
  serverUrl: 'wss://avatar.cn-huadong-1.xf-yun.com/v1/interact',
  appId: 'e5850021',
  apiKey: 'dda0f69489a3db1e0d495f40a5fd40eb',
  apiSecret: 'OTNlMGI0OWUxM2JlMWRhM2EzNDVhZjAw',
  sceneId: '202632480413585408',
}

function App() {
  const interactiveRef = useRef<any>()
  const voiceRef = useRef<VoiceRecorderRef>(null)
  const [loading, setLoading] = useState(false)
  const [subtitle, setSubtitle] = useState('')
  const [text, setText] = useState('')
  const [preloadMessages, setPreloadMessages] = useState<string[]>([])
  const [isInitialized, setIsInitialized] = useState(false)

  const [avatarId, setAvatarId] = useState<string | null>(null)
  const [voiceVcn, setVoiceVcn] = useState<string | null>(null)

  const getGlobalParams = () => {
    if (!avatarId || !voiceVcn) return null
    return {
      avatar_dispatch: { interactive_mode: 0, content_analysis: 0 },
      stream: { protocol: 'xrtc', alpha: 0, bitrate: 1000000, fps: 25 },
      avatar: {
        avatar_id: avatarId,
        width: 1920,
        height: 1080,
        mask_region: [0, 0, 1080, 1920],
        scale: 1,
        move_h: 0,
        move_v: 0,
        audio_format: 1,
      },
      tts: { vcn: voiceVcn, speed: 50, pitch: 50, volume: 100 },
      subtitle: { subtitle: 1, font_color: '#ffffff' },
      background: { enabled: false, type: 'url', data: '' },
    }
  }

  useEffect(() => {
    function handleParentMessage(event: MessageEvent) {
      if (event.origin !== 'http://localhost:5174') return
      if (event.data.type === 'set_avatar_voice') {
        const { avatar_id, voice_vcn } = event.data.payload || {}
        if (avatar_id && voice_vcn) {
          setAvatarId(avatar_id)
          setVoiceVcn(voice_vcn)
          message.info(`已收到参数，形象ID：${avatar_id}，声音VCN：${voice_vcn}`)
        }
      } else if (event.data.type === 'preload_message' && event.data.payload) {
        const msgs = Array.isArray(event.data.payload) ? event.data.payload : [event.data.payload]
        setPreloadMessages((prev) => [...prev, ...msgs])
      }
    }
    window.addEventListener('message', handleParentMessage)
    return () => window.removeEventListener('message', handleParentMessage)
  }, [])

  useEffect(() => {
    if (!avatarId || !voiceVcn) return
    if (!interactiveRef.current) {
      initSDK()
    }
  }, [avatarId, voiceVcn])

  const initSDK = () => {
    if (interactiveRef.current) return
    if (!avatarId || !voiceVcn) {
      message.warning('请先通过父页面设置形象和声音参数')
      return
    }
    try {
      interactiveRef.current = new (AvatarPlatform as any)({ useInlinePlayer: true, binaryData: false })
      bindSDKEvents()
      bindPlayerEvents()
      interactiveRef.current.setApiInfo(SDK_CONFIG)
      interactiveRef.current.setGlobalParams(getGlobalParams()!)
      message.success('SDK 初始化成功')
    } catch (e: any) {
      message.error('初始化失败: ' + e.message)
    }
  }

  const bindSDKEvents = () => {
    if (!interactiveRef.current) return
    interactiveRef.current.removeAllListeners()
    interactiveRef.current
      .on(SDKEvents.connected, (res: any) => console.log('SDK connected', res))
      .on(SDKEvents.stream_start, () => console.log('SDK stream_start'))
      .on(SDKEvents.disconnected, (e: any) => {
        setLoading(false)
        setIsInitialized(false)
        message.error('连接断开')
        console.error(e)
      })
      .on(SDKEvents.subtitle_info, (data: any) => setSubtitle(data?.text || ''))
      .on(SDKEvents.error, (err: any) => console.error('SDK error', err))
  }

  const bindPlayerEvents = () => {
    const player = interactiveRef.current?.player
    if (!player) return
    player.removeAllListeners()
    player.on(PlayerEvents.error, (e: any) => console.error('Player error', e))
  }

  const startInterview = async () => {
    if (!interactiveRef.current) {
      initSDK()
    } else {
      if (!avatarId || !voiceVcn) {
        message.warning('请先通过父页面设置形象和声音参数')
        return
      }
      interactiveRef.current.setGlobalParams(getGlobalParams()!)
    }
    setLoading(true)
    try {
      await interactiveRef.current.start({ wrapper: document.querySelector('.wrapper1') })
      setIsInitialized(true)
      message.success('虚拟人启动成功')

      for (const msg of preloadMessages) {
        await sendPreloadedMessage(msg)
        await new Promise((resolve) => setTimeout(resolve, 500))
      }
      setPreloadMessages([])
      startVoiceInteraction()
    } catch (e: any) {
      message.error('启动失败: ' + e.message)
    }
    setLoading(false)
  }

  const sendPreloadedMessage = async (messageText: string) => {
    try {
      await interactiveRef.current.writeText(messageText, {
        tts: getGlobalParams()?.tts,
        nlp: true,
        avatar_dispatch: getGlobalParams()?.avatar_dispatch,
      })
    } catch (e: any) {
      console.error('发送预置消息失败:', e)
    }
  }

  const startVoiceInteraction = () => {
    if (!interactiveRef.current) {
      message.warning('请先启动虚拟人')
      return
    }
    startRecord()
    voiceRef.current?.start()
    message.success('语音交互已开启')
  }

  const startRecord = () => {
    if (!interactiveRef.current) return
    if (interactiveRef.current.recorder) {
      interactiveRef.current.recorder.stopRecord()
      interactiveRef.current.destroyRecorder()
    }
    interactiveRef.current.createRecorder({ sampleRate: 16000 })
    interactiveRef.current.recorder.startRecord(
      0,
      () => {
        console.log('录音自动停止')
      },
      { nlp: true }
    )
  }

  const stopAll = () => {
    voiceRef.current?.stop()
    if (!interactiveRef.current) return
    interactiveRef.current.recorder?.stopRecord()
    interactiveRef.current.stop()
    interactiveRef.current.destroy()
    interactiveRef.current = undefined
    setIsInitialized(false)
    message.success('虚拟人已停止')
  }

  const interruptSpeak = () => {
    if (!interactiveRef.current) {
      message.warning('虚拟人未启动')
      return
    }
    interactiveRef.current.interrupt()
    message.info('已打断播报')
  }

  const onVoiceResult = (text: string) => {
    setText(text)
    window.parent.postMessage({ type: 'subtitle_update', text }, '*')
  }

  const showCurrentParams = () => {
    message.info(`当前参数 - 形象ID: ${avatarId || '未设置'}, 声音VCN: ${voiceVcn || '未设置'}`)
    console.log('当前参数:', { avatarId, voiceVcn })
  }

  useEffect(() => {
    return () => {
      stopAll()
    }
  }, [])

  return (
    <Spin spinning={loading} tip="加载中...">
      <div style={{ padding: 24 }}>
        {/* Virtual Human Container with Integrated Controls */}
        <div style={{ 
          background: '#000', 
          borderRadius: 8,
          overflow: 'hidden',
          marginBottom: 20,
          boxShadow: '0 4px 12px rgba(0,0,0,0.15)'
        }}>
          {/* Virtual Human Display Area */}
          <div 
            className="wrapper1" 
            style={{ 
              width: '100%', 
              height: 290,  // Reduced height to accommodate controls
              position: 'relative'
            }}
          />

          {/* Control Panel */}
          <div style={{
            background: '#1a1a1a',
            padding: '12px 16px',
            display: 'flex',
            gap: '10px',
            borderTop: '1px solid #333',
            alignItems: 'center'
          }}>
            <Button 
              type="primary" 
              onClick={startInterview}
              style={{ flex: 1 }}
            >
              启动虚拟人
            </Button>
            <Button 
              onClick={interruptSpeak}
              style={{ 
                flex: 1,
                background: '#2a2a2a',
                color: '#fff',
                borderColor: '#444'
              }}
            >
              打断播报
            </Button>
            <Button 
              danger 
              onClick={stopAll}
              style={{ flex: 1 }}
            >
              关闭
            </Button>
            <Button 
              onClick={showCurrentParams}
              style={{ 
                background: '#2a2a2a',
                color: '#fff',
                borderColor: '#444'
              }}
            >
              参数
            </Button>
          </div>

          {/* Subtitle Display */}
          <div style={{
            padding: '8px 16px',
            background: '#1a1a1a',
            color: '#fff',
            borderTop: '1px solid #333',
            minHeight: 40
          }}>
            {subtitle || '暂无字幕'}
            {preloadMessages.length > 0 && (
              <span style={{ 
                color: '#ff9800', 
                marginLeft: 10,
                fontSize: 12
              }}>
                (待播报: {preloadMessages.length}条)
              </span>
            )}
          </div>
        </div>

        {/* Additional Controls */}
        <div style={{ marginBottom: 20 }}>
          <textarea
            rows={5}
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="实时语音识别结果"
            style={{ 
              width: '100%',
              background: '#1a1a1a',
              color: '#fff',
              borderColor: '#333',
              padding: 12
            }}
          />
        </div>

        <VoiceRecorder ref={voiceRef} onResult={onVoiceResult} />
      </div>
    </Spin>
  )
}

export default App