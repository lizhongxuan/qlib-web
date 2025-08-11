/**
 * WebSocket 连接管理器
 */

export interface WebSocketMessage {
  type: string
  channel: string
  data: any
  timestamp: string
}

export interface ExperimentUpdate {
  experiment_id: string
  status: string
  progress?: number
  message?: string
  results?: any
}

export interface SystemNotification {
  title: string
  message: string
  type: 'info' | 'success' | 'warning' | 'error'
  timestamp: string
}

export class WebSocketManager {
  private ws: WebSocket | null = null
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 1000
  private subscribers = new Map<string, Set<Function>>()
  private isConnecting = false
  private connectionId = ''
  
  constructor(private baseUrl: string = '') {
    this.baseUrl = baseUrl || `ws://${window.location.host}`
  }

  /**
   * 连接WebSocket
   */
  async connect(): Promise<boolean> {
    if (this.isConnecting || (this.ws && this.ws.readyState === WebSocket.OPEN)) {
      return true
    }

    this.isConnecting = true
    
    return new Promise((resolve, reject) => {
      try {
        const wsUrl = `${this.baseUrl}/api/v1/ws/connect`
        this.ws = new WebSocket(wsUrl)
        
        this.ws.onopen = () => {
          console.log('WebSocket连接已建立')
          this.isConnecting = false
          this.reconnectAttempts = 0
          this.emit('connection', { status: 'connected' })
          resolve(true)
        }
        
        this.ws.onmessage = (event) => {
          try {
            const message: WebSocketMessage = JSON.parse(event.data)
            this.handleMessage(message)
          } catch (error) {
            console.error('解析WebSocket消息失败:', error)
          }
        }
        
        this.ws.onclose = (event) => {
          console.log('WebSocket连接已关闭', event.code, event.reason)
          this.isConnecting = false
          this.emit('connection', { status: 'disconnected', code: event.code, reason: event.reason })
          
          // 自动重连
          if (!event.wasClean && this.reconnectAttempts < this.maxReconnectAttempts) {
            this.scheduleReconnect()
          }
        }
        
        this.ws.onerror = (error) => {
          console.error('WebSocket连接错误:', error)
          this.isConnecting = false
          this.emit('connection', { status: 'error', error })
          reject(error)
        }
        
        // 连接超时
        setTimeout(() => {
          if (this.isConnecting) {
            this.isConnecting = false
            reject(new Error('WebSocket连接超时'))
          }
        }, 10000)
        
      } catch (error) {
        this.isConnecting = false
        reject(error)
      }
    })
  }

  /**
   * 断开连接
   */
  disconnect(): void {
    if (this.ws) {
      this.ws.close(1000, '用户主动断开')
      this.ws = null
    }
    this.subscribers.clear()
    this.connectionId = ''
  }

  /**
   * 订阅频道
   */
  subscribe(channel: string, callback: Function): void {
    if (!this.subscribers.has(channel)) {
      this.subscribers.set(channel, new Set())
    }
    this.subscribers.get(channel)!.add(callback)
    
    // 发送订阅消息到服务器
    this.send({
      type: 'subscribe',
      channel,
      data: {}
    })
  }

  /**
   * 取消订阅
   */
  unsubscribe(channel: string, callback?: Function): void {
    if (callback) {
      const channelSubscribers = this.subscribers.get(channel)
      if (channelSubscribers) {
        channelSubscribers.delete(callback)
        if (channelSubscribers.size === 0) {
          this.subscribers.delete(channel)
          // 发送取消订阅消息
          this.send({
            type: 'unsubscribe',
            channel,
            data: {}
          })
        }
      }
    } else {
      // 取消频道的所有订阅
      this.subscribers.delete(channel)
      this.send({
        type: 'unsubscribe',
        channel,
        data: {}
      })
    }
  }

  /**
   * 发送消息
   */
  send(message: Omit<WebSocketMessage, 'timestamp'>): boolean {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      console.warn('WebSocket未连接，无法发送消息')
      return false
    }

    try {
      const fullMessage: WebSocketMessage = {
        ...message,
        timestamp: new Date().toISOString()
      }
      this.ws.send(JSON.stringify(fullMessage))
      return true
    } catch (error) {
      console.error('发送WebSocket消息失败:', error)
      return false
    }
  }

  /**
   * 获取连接状态
   */
  getConnectionState(): string {
    if (!this.ws) return 'CLOSED'
    
    switch (this.ws.readyState) {
      case WebSocket.CONNECTING: return 'CONNECTING'
      case WebSocket.OPEN: return 'OPEN'
      case WebSocket.CLOSING: return 'CLOSING'
      case WebSocket.CLOSED: return 'CLOSED'
      default: return 'UNKNOWN'
    }
  }

  /**
   * 处理接收到的消息
   */
  private handleMessage(message: WebSocketMessage): void {
    // 处理连接ID
    if (message.type === 'connection' && message.data?.connection_id) {
      this.connectionId = message.data.connection_id
    }

    // 分发消息到订阅者
    this.emit(message.channel, message)
    
    // 全局消息处理
    switch (message.type) {
      case 'experiment_update':
        this.handleExperimentUpdate(message.data)
        break
      case 'system_notification':
        this.handleSystemNotification(message.data)
        break
      case 'heartbeat':
        this.handleHeartbeat(message.data)
        break
    }
  }

  /**
   * 处理实验更新
   */
  private handleExperimentUpdate(data: ExperimentUpdate): void {
    // 可以在这里添加全局实验更新逻辑
    console.log('实验更新:', data)
  }

  /**
   * 处理系统通知
   */
  private handleSystemNotification(data: SystemNotification): void {
    // 可以在这里添加全局通知显示逻辑
    console.log('系统通知:', data)
  }

  /**
   * 处理心跳
   */
  private handleHeartbeat(data: any): void {
    // 响应心跳
    this.send({
      type: 'heartbeat_response',
      channel: 'system',
      data: { timestamp: new Date().toISOString() }
    })
  }

  /**
   * 发射事件给订阅者
   */
  private emit(channel: string, data: any): void {
    const channelSubscribers = this.subscribers.get(channel)
    if (channelSubscribers) {
      channelSubscribers.forEach(callback => {
        try {
          callback(data)
        } catch (error) {
          console.error('执行WebSocket回调失败:', error)
        }
      })
    }
  }

  /**
   * 计划重连
   */
  private scheduleReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('WebSocket重连次数已达上限')
      return
    }

    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts)
    this.reconnectAttempts++
    
    console.log(`${delay}ms后尝试第${this.reconnectAttempts}次重连`)
    
    setTimeout(() => {
      this.connect().catch(error => {
        console.error('WebSocket重连失败:', error)
      })
    }, delay)
  }
}

// 创建全局WebSocket管理器实例
const wsManager = new WebSocketManager()

export default wsManager

/**
 * WebSocket Hook for Vue 3
 */
export function useWebSocket() {
  const isConnected = ref(false)
  const connectionState = ref('CLOSED')
  
  // 监控连接状态
  const updateConnectionState = () => {
    connectionState.value = wsManager.getConnectionState()
    isConnected.value = connectionState.value === 'OPEN'
  }
  
  // 订阅连接状态变化
  wsManager.subscribe('connection', (data: any) => {
    updateConnectionState()
  })
  
  onMounted(() => {
    updateConnectionState()
  })
  
  const connect = () => wsManager.connect()
  const disconnect = () => wsManager.disconnect()
  const subscribe = (channel: string, callback: Function) => wsManager.subscribe(channel, callback)
  const unsubscribe = (channel: string, callback?: Function) => wsManager.unsubscribe(channel, callback)
  const send = (message: Omit<WebSocketMessage, 'timestamp'>) => wsManager.send(message)
  
  return {
    isConnected: readonly(isConnected),
    connectionState: readonly(connectionState),
    connect,
    disconnect,
    subscribe,
    unsubscribe,
    send
  }
}

// 为了支持 Vue 3 的响应式API
import { ref, readonly, onMounted } from 'vue'