// rtasrClient.ts  —— 仅替换此文件，其余代码保持不变
import CryptoJS from 'crypto-js'

interface RtasrClientOptions {
  appId: string
  apiKey: string
  lang?: string
  onResult: (text: string, isFinal: boolean) => void
  onError?: (err: any) => void
  onClose?: () => void
}

export class RtasrClient {
  private readonly appId: string
  private readonly apiKey: string
  private readonly lang: string
  private readonly onResult: (text: string, isFinal: boolean) => void
  private readonly onError?: (err: any) => void
  private readonly onClose?: () => void

  private ws: WebSocket | null = null
  private bufferQueue: Uint8Array[] = []
  private sendTimer: number | null = null
  public  isReady = false

  constructor(opts: RtasrClientOptions) {
    this.appId   = opts.appId
    this.apiKey  = opts.apiKey
    this.lang    = opts.lang || 'cn'
    this.onResult = opts.onResult
    this.onError  = opts.onError
    this.onClose  = opts.onClose
  }

  /* ---------------- private 工具 ---------------- */
  private genSigna(ts: string) {
    const md5 = CryptoJS.MD5(this.appId + ts).toString()
    const hmac = CryptoJS.HmacSHA1(md5, this.apiKey)
    return CryptoJS.enc.Base64.stringify(hmac)
  }

  private buildUrl() {
    const ts = Math.floor(Date.now() / 1000).toString()
    const signa = this.genSigna(ts)
    const query = new URLSearchParams({ appid: this.appId, ts, signa, lang: this.lang })
    return `wss://rtasr.xfyun.cn/v1/ws?${query.toString()}`
  }

  /* ---------------- 对外 API ---------------- */
  start() {
    if (this.ws) return          // 已经在跑
    const url = this.buildUrl()
    this.ws = new WebSocket(url)
    this.ws.binaryType = 'arraybuffer'

    this.ws.onopen = () => {
      this.isReady = true
      this.openSendLoop()
      console.info('[RTASR] socket open')
    }

    this.ws.onmessage = evt => this.handleMessage(evt.data)
    this.ws.onerror   = err => this.onError?.(err)
    this.ws.onclose   = () => {
      console.info('[RTASR] socket close')
      this.isReady = false
      this.closeSendLoop()
      this.ws = null
      this.bufferQueue = []
      this.onClose?.()
    }
  }

  /** 持续推入 PCM 数据（Uint8Array，16k/16bit/mono）*/
  pushAudio(pcm: Uint8Array) {
    if (!this.isReady) return
    this.bufferQueue.push(pcm)
  }

  /** 主动结束，会发送 {"end":true} 再关闭 */
  finish() {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ end: true }))
    }
  }

  close() {
    this.finish()
    this.ws?.close()
  }

  /* ---------------- 内部实现 ---------------- */
  private handleMessage(raw: any) {
    try {
      const msg = JSON.parse(typeof raw === 'string' ? raw : raw.toString())
      if (msg.action === 'result' && msg.code === '0' && msg.data) {
        const data = JSON.parse(msg.data)
        /*** 中文普通话结构解析 ***/
        if (data.cn?.st) {
          const rtArr = data.cn.st.rt ?? []
          const sentence = rtArr
            .flatMap((rt: any) => rt.ws)
            .flatMap((ws: any) => ws.cw)
            .map((cw: any) => cw.w)
            .join('')
          const isFinal = data.cn.st.type === '0'
          this.onResult(sentence, isFinal)
        }
        /*** 如果你开启了翻译功能，可按 doc 解析 data.src / data.dst ***/
      } else if (msg.action === 'error') {
        this.onError?.(msg)
        this.close()
      }
    } catch (e) {
      this.onError?.(e)
    }
  }

  /** 40 ms 定时把 bufferQueue 里的数据按照 1280 byte 封包发送 */
  private openSendLoop() {
    if (this.sendTimer) return
    this.sendTimer = window.setInterval(() => {
      if (!this.ws || this.ws.readyState !== WebSocket.OPEN) return
      if (this.bufferQueue.length === 0) return

      const target = 1280
      let need = target
      const sendingParts: Uint8Array[] = []

      while (need > 0 && this.bufferQueue.length > 0) {
        const chunk = this.bufferQueue[0]
        if (chunk.byteLength <= need) {
          sendingParts.push(chunk)
          this.bufferQueue.shift()
          need -= chunk.byteLength
        } else {
          // chunk 比需发送的大，切片
          sendingParts.push(chunk.subarray(0, need))
          this.bufferQueue[0] = chunk.subarray(need)
          need = 0
        }
      }

      if (sendingParts.length === 0) return
      const totalLen = sendingParts.reduce((sum, b) => sum + b.byteLength, 0)
      const merged = new Uint8Array(totalLen)
      let offset = 0
      sendingParts.forEach(b => {
        merged.set(b, offset)
        offset += b.byteLength
      })

      this.ws.send(merged.buffer)
      console.debug(`[RTASR] >>> sent ${merged.byteLength} B, queue=${this.bufferQueue.length}`)
    }, 40)
  }

  private closeSendLoop() {
    if (this.sendTimer) {
      clearInterval(this.sendTimer)
      this.sendTimer = null
    }
  }
}
