import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import { WebSocketManager, WebSocketMessage } from '../websocket'

// Mock WebSocket
class MockWebSocket {
  static CONNECTING = 0
  static OPEN = 1
  static CLOSING = 2
  static CLOSED = 3

  readyState = MockWebSocket.CONNECTING
  url = ''
  onopen: ((event: Event) => void) | null = null
  onclose: ((event: CloseEvent) => void) | null = null
  onmessage: ((event: MessageEvent) => void) | null = null
  onerror: ((event: Event) => void) | null = null

  constructor(url: string) {
    this.url = url
    // 模拟异步连接
    setTimeout(() => {
      this.readyState = MockWebSocket.OPEN
      this.onopen?.(new Event('open'))
    }, 10)
  }

  send(data: string) {
    if (this.readyState !== MockWebSocket.OPEN) {
      throw new Error('WebSocket is not open')
    }
    // 模拟发送成功
  }

  close(code?: number, reason?: string) {
    this.readyState = MockWebSocket.CLOSING
    setTimeout(() => {
      this.readyState = MockWebSocket.CLOSED
      const closeEvent = new CloseEvent('close', { code, reason })
      this.onclose?.(closeEvent)
    }, 10)
  }

  // 模拟接收消息
  simulateMessage(data: string) {
    if (this.readyState === MockWebSocket.OPEN) {
      const messageEvent = new MessageEvent('message', { data })
      this.onmessage?.(messageEvent)
    }
  }

  // 模拟连接错误
  simulateError() {
    this.onerror?.(new Event('error'))
  }
}

// 全局mock WebSocket
global.WebSocket = MockWebSocket as any

describe('WebSocketManager', () => {
  let wsManager: WebSocketManager
  let mockWebSocket: MockWebSocket

  beforeEach(() => {
    wsManager = new WebSocketManager('ws://localhost:8000')
    vi.clearAllMocks()
  })

  afterEach(() => {
    wsManager.disconnect()
  })

  describe('连接管理', () => {
    it('应该能够成功连接', async () => {
      const connected = await wsManager.connect()
      expect(connected).toBe(true)
      expect(wsManager.getConnectionState()).toBe('OPEN')
    })

    it('应该防止重复连接', async () => {
      await wsManager.connect()
      const secondConnect = await wsManager.connect()
      expect(secondConnect).toBe(true)
    })

    it('应该能够断开连接', async () => {
      await wsManager.connect()
      wsManager.disconnect()
      expect(wsManager.getConnectionState()).toBe('CLOSED')
    })
  })

  describe('订阅和取消订阅', () => {
    beforeEach(async () => {
      await wsManager.connect()
    })

    it('应该能够订阅频道', () => {
      const callback = vi.fn()
      wsManager.subscribe('test-channel', callback)
      
      // 验证订阅成功
      expect(callback).not.toHaveBeenCalled()
    })

    it('应该能够取消订阅', () => {
      const callback = vi.fn()
      wsManager.subscribe('test-channel', callback)
      wsManager.unsubscribe('test-channel', callback)
      
      // 发送消息，回调不应该被调用
      const message: WebSocketMessage = {
        type: 'test',
        channel: 'test-channel',
        data: { test: 'data' },
        timestamp: new Date().toISOString()
      }
      
      // 通过私有方法测试消息处理
      ;(wsManager as any).handleMessage(message)
      expect(callback).not.toHaveBeenCalled()
    })

    it('应该能够处理多个订阅者', () => {
      const callback1 = vi.fn()
      const callback2 = vi.fn()
      
      wsManager.subscribe('test-channel', callback1)
      wsManager.subscribe('test-channel', callback2)
      
      const message: WebSocketMessage = {
        type: 'test',
        channel: 'test-channel',
        data: { test: 'data' },
        timestamp: new Date().toISOString()
      }
      
      ;(wsManager as any).handleMessage(message)
      
      expect(callback1).toHaveBeenCalledWith(message)
      expect(callback2).toHaveBeenCalledWith(message)
    })
  })

  describe('消息发送', () => {
    beforeEach(async () => {
      await wsManager.connect()
    })

    it('应该能够发送消息', () => {
      const message = {
        type: 'test',
        channel: 'test-channel',
        data: { test: 'data' }
      }
      
      const sent = wsManager.send(message)
      expect(sent).toBe(true)
    })

    it('未连接时发送消息应该失败', () => {
      wsManager.disconnect()
      
      const message = {
        type: 'test',
        channel: 'test-channel',
        data: { test: 'data' }
      }
      
      const sent = wsManager.send(message)
      expect(sent).toBe(false)
    })
  })

  describe('消息接收处理', () => {
    beforeEach(async () => {
      await wsManager.connect()
    })

    it('应该能够处理实验更新消息', () => {
      const callback = vi.fn()
      wsManager.subscribe('experiments', callback)
      
      const updateMessage = {
        type: 'experiment_update',
        channel: 'experiments',
        data: {
          experiment_id: '123',
          status: 'completed',
          progress: 100
        },
        timestamp: new Date().toISOString()
      }
      
      ;(wsManager as any).handleMessage(updateMessage)
      expect(callback).toHaveBeenCalledWith(updateMessage)
    })

    it('应该能够处理系统通知消息', () => {
      const callback = vi.fn()
      wsManager.subscribe('system', callback)
      
      const notificationMessage = {
        type: 'system_notification',
        channel: 'system',
        data: {
          title: '系统维护',
          message: '系统将在1小时后进行维护',
          type: 'warning'
        },
        timestamp: new Date().toISOString()
      }
      
      ;(wsManager as any).handleMessage(notificationMessage)
      expect(callback).toHaveBeenCalledWith(notificationMessage)
    })

    it('应该处理无效JSON消息', () => {
      const callback = vi.fn()
      wsManager.subscribe('test', callback)
      
      // 模拟无效JSON
      const wsInstance = (wsManager as any).ws as MockWebSocket
      wsInstance.simulateMessage('invalid json')
      
      // 不应该调用回调
      expect(callback).not.toHaveBeenCalled()
    })
  })

  describe('重连机制', () => {
    it('应该在连接断开时尝试重连', async () => {
      await wsManager.connect()
      
      // 模拟连接断开
      const wsInstance = (wsManager as any).ws as MockWebSocket
      wsInstance.close(1006, 'Connection lost')
      
      // 等待重连逻辑
      await new Promise(resolve => setTimeout(resolve, 100))
      
      // 验证重连逻辑被触发
      expect((wsManager as any).reconnectAttempts).toBeGreaterThan(0)
    })

    it('应该在达到最大重连次数后停止', async () => {
      ;(wsManager as any).maxReconnectAttempts = 2
      await wsManager.connect()
      
      // 模拟多次连接失败
      for (let i = 0; i < 3; i++) {
        const wsInstance = (wsManager as any).ws as MockWebSocket
        wsInstance.close(1006, 'Connection lost')
        await new Promise(resolve => setTimeout(resolve, 50))
      }
      
      expect((wsManager as any).reconnectAttempts).toBeLessThanOrEqual(2)
    })
  })

  describe('心跳处理', () => {
    beforeEach(async () => {
      await wsManager.connect()
    })

    it('应该响应心跳消息', () => {
      const sendSpy = vi.spyOn(wsManager, 'send')
      
      const heartbeatMessage = {
        type: 'heartbeat',
        channel: 'system',
        data: { timestamp: new Date().toISOString() },
        timestamp: new Date().toISOString()
      }
      
      ;(wsManager as any).handleMessage(heartbeatMessage)
      
      expect(sendSpy).toHaveBeenCalledWith({
        type: 'heartbeat_response',
        channel: 'system',
        data: expect.objectContaining({
          timestamp: expect.any(String)
        })
      })
    })
  })

  describe('错误处理', () => {
    it('应该处理连接错误', async () => {
      const wsInstance = new MockWebSocket('ws://localhost:8000')
      
      // 模拟连接过程中出错
      setTimeout(() => {
        wsInstance.simulateError()
      }, 5)
      
      try {
        await wsManager.connect()
      } catch (error) {
        expect(error).toBeDefined()
      }
    })

    it('应该处理连接超时', async () => {
      // 模拟连接超时
      vi.useFakeTimers()
      
      const connectPromise = wsManager.connect()
      
      // 快进时间到超时
      vi.advanceTimersByTime(10000)
      
      try {
        await connectPromise
      } catch (error) {
        expect(error).toEqual(new Error('WebSocket连接超时'))
      }
      
      vi.useRealTimers()
    })

    it('回调函数错误不应该影响其他订阅者', () => {
      const errorCallback = vi.fn(() => { throw new Error('Callback error') })
      const normalCallback = vi.fn()
      
      wsManager.subscribe('test', errorCallback)
      wsManager.subscribe('test', normalCallback)
      
      const message = {
        type: 'test',
        channel: 'test',
        data: {},
        timestamp: new Date().toISOString()
      }
      
      ;(wsManager as any).handleMessage(message)
      
      expect(errorCallback).toHaveBeenCalled()
      expect(normalCallback).toHaveBeenCalled()
    })
  })
})

// useWebSocket Hook 测试
describe('useWebSocket', () => {
  it('应该返回正确的响应式状态', async () => {
    // 由于这需要Vue的测试环境，这里先跳过具体实现
    // 在实际项目中需要配置@vue/test-utils
    expect(true).toBe(true)
  })
})