import React, {
  useState, useRef, useEffect, forwardRef, useImperativeHandle
} from 'react';
import md5 from 'md5';
import CryptoJS from 'crypto-js';
import { message } from 'antd';

const APPID = '8ab8ca05';
const API_KEY = '67e0e6de47d8997f3896a11678dd4357';

// 去重拼接，防止重复文字累积
function deduplicateAppend(prevText: string, currentText: string): string {
  let overlapLen = 0;
  const maxOverlap = Math.min(prevText.length, currentText.length);

  for (let i = maxOverlap; i > 0; i--) {
    if (prevText.endsWith(currentText.substring(0, i))) {
      overlapLen = i;
      break;
    }
  }

  return prevText + currentText.substring(overlapLen);
}

// 中文断句，按句号、问号、感叹号分句
function splitSentences(text: string): string[] {
  // 保留标点符号作为句尾
  return text.match(/[^。！？]+[。！？]?/g) || [];
}

const VoiceRecorder = forwardRef<
  { start: () => void; stop: () => void },
  { onResult?: (text: string) => void }
>(({ onResult }, ref) => {
  const [text, setText] = useState('');
  const [isRecording, setIsRecording] = useState(false);

  // 记录已发送给数据库的文本长度，用于只发送新增文本
  const sentLengthRef = useRef(0);

  const wsRef = useRef<WebSocket | null>(null);
  const audioCtxRef = useRef<AudioContext | null>(null);
  const processorRef = useRef<ScriptProcessorNode | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const lastDataTimeRef = useRef<number>(0);
  const heartbeatRef = useRef<NodeJS.Timeout | null>(null);
  const manualCloseRef = useRef(false);

  // MediaRecorder及录音数据存储
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  useImperativeHandle(ref, () => ({
    start: connectWebSocket,
    stop: cleanup
  }), []);

  const connectWebSocket = async () => {
    if (isRecording) return;

    setText('');
    setIsRecording(true);
    manualCloseRef.current = false;
    sentLengthRef.current = 0; // 重置已发送长度

    try {
      audioCtxRef.current = new (window.AudioContext || (window as any).webkitAudioContext)({
        sampleRate: 16000
      });

      streamRef.current = await navigator.mediaDevices.getUserMedia({
        audio: {
          sampleRate: 16000,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        },
        video: false
      });

      audioChunksRef.current = [];
      mediaRecorderRef.current = new MediaRecorder(streamRef.current);
      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data && event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };
      mediaRecorderRef.current.start();

      const source = audioCtxRef.current.createMediaStreamSource(streamRef.current);
      processorRef.current = audioCtxRef.current.createScriptProcessor(4096, 1, 1);

      source.connect(processorRef.current);
      processorRef.current.connect(audioCtxRef.current.destination);

      processorRef.current.onaudioprocess = (e) => {
        if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;

        const buf = e.inputBuffer.getChannelData(0);
        const int16 = new Int16Array(buf.length);

        for (let i = 0; i < buf.length; i++) {
          int16[i] = Math.min(32767, Math.max(-32768, buf[i] * 32768));
        }

        try {
          wsRef.current.send(int16.buffer);
          lastDataTimeRef.current = Date.now();
        } catch (error) {
          console.error('发送音频数据失败:', error);
        }
      };

      const url = getWsUrl();
      wsRef.current = new WebSocket(url);

      wsRef.current.onopen = () => {
        message.success('语音识别连接已建立');
        lastDataTimeRef.current = Date.now();

        heartbeatRef.current = setInterval(() => {
          if (Date.now() - lastDataTimeRef.current > 3000) {
            try {
              wsRef.current?.send(JSON.stringify({ type: 'heartbeat' }));
              console.log('发送心跳包');
            } catch (e) {
              console.warn('心跳发送失败:', e);
            }
          }
        }, 1000);
      };

      wsRef.current.onmessage = (e) => {
        try {
          const msg = JSON.parse(e.data);

          if (msg.action === 'result') {
            const result = JSON.parse(msg.data);

            let currentText = '';
            if (result.cn?.st?.rt) {
              result.cn.st.rt.forEach((r: any) => {
                if (r.ws) {
                  r.ws.forEach((w: any) => {
                    if (w.cw) {
                      w.cw.forEach((c: any) => {
                        if (c.w) currentText += c.w;
                      });
                    }
                  });
                }
              });

              setText(prev => {
                // 拼接文本，去重
                const newText = deduplicateAppend(prev, currentText);
                // 断句用于显示
                const sentences = splitSentences(newText);
                const displayText = sentences.join('\n');

                // 只取新增部分（相对已发送长度）
                const newContent = newText.substring(sentLengthRef.current);
                // 去除所有空白符，适合保存到数据库
                const pureNewContent = newContent.replace(/\s+/g, '');

                // 更新已发送长度
                sentLengthRef.current = newText.length;

                // 回调只传新增纯文本，方便存库
                setTimeout(() => {
                  onResult?.(pureNewContent);
                }, 0);

                return displayText; // 界面显示断句带换行的文本
              });
            }
          } else if (msg.action === 'started') {
            console.log('WebSocket连接已建立，准备接收音频');
          } else if (msg.action === 'error') {
            console.error('识别错误:', msg);
            message.error(`识别错误: ${msg.desc || '未知错误'}`);
          }
        } catch (parseError) {
          console.error('解析消息错误:', parseError, e.data);
        }
      };

      wsRef.current.onerror = (e) => {
        console.error('WebSocket错误:', e);
        message.error('语音识别连接错误');
      };

      wsRef.current.onclose = () => {
        console.log('WebSocket连接关闭');
        if (!manualCloseRef.current) {
          message.warning('连接已断开，正在尝试重新连接...');
          setTimeout(connectWebSocket, 3000);
        }
      };
    } catch (error) {
      console.error('连接失败:', error);
      message.error('语音识别初始化失败');
      cleanup();
    }
  };

  const getWsUrl = () => {
    const ts = Math.floor(Date.now() / 1000);
    const signa = md5(APPID + ts);
    const signatureSha = CryptoJS.HmacSHA1(signa, API_KEY);
    const signature = CryptoJS.enc.Base64.stringify(signatureSha);
    const encodedSignature = encodeURIComponent(signature);

    return `wss://rtasr.xfyun.cn/v1/ws?appid=${APPID}&ts=${ts}&signa=${encodedSignature}`;
  };

  const cleanup = () => {
    try {
      manualCloseRef.current = true;
      setIsRecording(false);

      if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
        mediaRecorderRef.current.onstop = () => {
          const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
          const reader = new FileReader();
          reader.onloadend = () => {
            window.parent.postMessage({
              type: 'audio_blob',
              audioData: reader.result
            }, '*');
          };
          reader.readAsDataURL(audioBlob);
        };
        mediaRecorderRef.current.stop();
      }

      if (wsRef.current) {
        wsRef.current.onclose = null;
        wsRef.current.close();
        wsRef.current = null;
      }

      if (heartbeatRef.current) {
        clearInterval(heartbeatRef.current);
        heartbeatRef.current = null;
      }

      if (processorRef.current) {
        processorRef.current.disconnect();
        processorRef.current.onaudioprocess = null;
        processorRef.current = null;
      }

      if (audioCtxRef.current && audioCtxRef.current.state !== 'closed') {
        audioCtxRef.current.close();
        audioCtxRef.current = null;
      }

      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
        streamRef.current = null;
      }
    } catch (error) {
      console.warn('清理资源时出错:', error);
    }
  };

  useEffect(() => {
    return () => {
      cleanup();
    };
  }, []);

  return (
    <div style={{ padding: '10px', border: '1px solid #eee', borderRadius: '4px' }}>
      <div style={{ marginBottom: '10px' }}>
        <span style={{
          display: 'inline-block',
          width: 10,
          height: 10,
          borderRadius: '50%',
          backgroundColor: isRecording ? '#52c41a' : '#ff4d4f',
          marginRight: 8
        }} />
        <span>{isRecording ? '正在录音和转写...' : '未开始录音'}</span>
      </div>
      <div style={{
        height: 100,
        padding: 10,
        border: '1px solid #d9d9d9',
        borderRadius: 4,
        overflowY: 'auto',
        backgroundColor: '#fafafa',
        whiteSpace: 'pre-wrap' // 支持断句换行显示
      }}>
        {text || <span style={{ color: '#bfbfbf' }}>实时转写结果将显示在这里...</span>}
      </div>
    </div>
  );
});

export default VoiceRecorder;
