import { ref, reactive, watch, computed, onUnmounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { debounce, throttle, isEqual, cloneDeep } from 'lodash-es'

// 会话状态配置
interface SessionConfig {
  persistAcrossReload: boolean // 页面刷新时是否保持状态
  enableHistory: boolean // 是否启用历史记录
  maxHistorySize: number // 最大历史记录数量
  autoSave: boolean // 是否自动保存
  saveInterval: number // 自动保存间隔（毫秒）
  enableCompression: boolean // 是否启用压缩
  enableEncryption: boolean // 是否启用加密
  namespace: string // 命名空间，用于避免冲突
}

// 会话状态项
interface SessionStateItem<T = any> {
  value: T
  timestamp: number
  route: string
  sessionId: string
  metadata?: Record<string, any>
  compressed?: boolean
  encrypted?: boolean
}

// 历史记录项
interface HistoryItem<T = any> {
  id: string
  value: T
  timestamp: number
  route: string
  action: 'create' | 'update' | 'delete'
  description?: string
}

// 会话事件
interface SessionEvent<T = any> {
  type: 'state_change' | 'route_change' | 'session_start' | 'session_end'
  key: string
  oldValue: T | null
  newValue: T | null
  timestamp: number
  route: string
}

// 会话状态管理器
class SessionStateManager {
  private sessionId: string
  private states: Map<string, any> = new Map()
  private history: Map<string, HistoryItem[]> = new Map()
  private listeners: Map<string, Set<(event: SessionEvent) => void>> = new Map()
  private saveTimers: Map<string, NodeJS.Timeout> = new Map()
  private config: SessionConfig

  constructor(config: Partial<SessionConfig> = {}) {
    this.config = {
      persistAcrossReload: true,
      enableHistory: true,
      maxHistorySize: 20,
      autoSave: true,
      saveInterval: 5000, // 5秒
      enableCompression: false,
      enableEncryption: false,
      namespace: 'qlib_session',
      ...config
    }

    this.sessionId = this.generateSessionId()
    this.initializeSession()
  }

  // 生成会话ID
  private generateSessionId(): string {
    return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  }

  // 初始化会话
  private initializeSession(): void {
    // 如果启用跨刷新持久化，尝试恢复状态
    if (this.config.persistAcrossReload) {
      this.restoreFromSessionStorage()
    }

    // 监听页面卸载事件
    window.addEventListener('beforeunload', () => {
      this.saveToSessionStorage()
    })

    // 监听页面可见性变化
    document.addEventListener('visibilitychange', () => {
      if (document.hidden) {
        this.saveToSessionStorage()
      }
    })
  }

  // 生成存储键
  private getStorageKey(key: string): string {
    return `${this.config.namespace}_${key}`
  }

  // 设置状态
  setState<T>(key: string, value: T, metadata?: Record<string, any>): void {
    const oldValue = this.states.get(key)
    
    // 创建状态项
    const stateItem: SessionStateItem<T> = {
      value,
      timestamp: Date.now(),
      route: window.location.pathname,
      sessionId: this.sessionId,
      metadata
    }

    this.states.set(key, stateItem)

    // 添加到历史记录
    if (this.config.enableHistory) {
      this.addToHistory(key, value, oldValue ? 'update' : 'create')
    }

    // 触发事件
    this.emit('state_change', key, oldValue?.value, value)

    // 自动保存
    if (this.config.autoSave) {
      this.scheduleAutoSave(key)
    }
  }

  // 获取状态
  getState<T>(key: string, defaultValue?: T): T | undefined {
    const stateItem = this.states.get(key) as SessionStateItem<T>
    return stateItem ? stateItem.value : defaultValue
  }

  // 删除状态
  removeState(key: string): boolean {
    const oldValue = this.states.get(key)
    const removed = this.states.delete(key)

    if (removed && oldValue) {
      // 添加删除记录
      if (this.config.enableHistory) {
        this.addToHistory(key, null, 'delete')
      }

      // 触发事件
      this.emit('state_change', key, oldValue.value, null)

      // 清理定时器
      const timer = this.saveTimers.get(key)
      if (timer) {
        clearTimeout(timer)
        this.saveTimers.delete(key)
      }
    }

    return removed
  }

  // 检查状态是否存在
  hasState(key: string): boolean {
    return this.states.has(key)
  }

  // 获取所有状态键
  getAllKeys(): string[] {
    return Array.from(this.states.keys())
  }

  // 获取所有状态
  getAllStates(): Record<string, any> {
    const result: Record<string, any> = {}
    this.states.forEach((stateItem, key) => {
      result[key] = stateItem.value
    })
    return result
  }

  // 清空所有状态
  clearAll(): void {
    const keys = this.getAllKeys()
    keys.forEach(key => this.removeState(key))
  }

  // 添加事件监听器
  addListener(eventType: SessionEvent['type'] | string, key: string, callback: (event: SessionEvent) => void): () => void {
    const eventKey = `${eventType}_${key}`
    
    if (!this.listeners.has(eventKey)) {
      this.listeners.set(eventKey, new Set())
    }
    
    this.listeners.get(eventKey)!.add(callback)

    return () => {
      this.listeners.get(eventKey)?.delete(callback)
      if (this.listeners.get(eventKey)?.size === 0) {
        this.listeners.delete(eventKey)
      }
    }
  }

  // 触发事件
  private emit(eventType: SessionEvent['type'], key: string, oldValue: any, newValue: any): void {
    const event: SessionEvent = {
      type: eventType,
      key,
      oldValue,
      newValue,
      timestamp: Date.now(),
      route: window.location.pathname
    }

    // 触发特定键的监听器
    const specificListeners = this.listeners.get(`${eventType}_${key}`)
    specificListeners?.forEach(callback => {
      try {
        callback(event)
      } catch (error) {
        console.error('Session event listener error:', error)
      }
    })

    // 触发通用监听器
    const generalListeners = this.listeners.get(`${eventType}_*`)
    generalListeners?.forEach(callback => {
      try {
        callback(event)
      } catch (error) {
        console.error('Session event listener error:', error)
      }
    })
  }

  // 添加到历史记录
  private addToHistory<T>(key: string, value: T, action: HistoryItem['action'], description?: string): void {
    if (!this.history.has(key)) {
      this.history.set(key, [])
    }

    const historyList = this.history.get(key)!
    const historyItem: HistoryItem<T> = {
      id: `${key}_${Date.now()}_${Math.random().toString(36).substr(2, 6)}`,
      value,
      timestamp: Date.now(),
      route: window.location.pathname,
      action,
      description
    }

    historyList.push(historyItem)

    // 限制历史记录数量
    if (historyList.length > this.config.maxHistorySize) {
      historyList.splice(0, historyList.length - this.config.maxHistorySize)
    }
  }

  // 获取历史记录
  getHistory(key: string): HistoryItem[] {
    return this.history.get(key) || []
  }

  // 获取所有历史记录
  getAllHistory(): Record<string, HistoryItem[]> {
    const result: Record<string, HistoryItem[]> = {}
    this.history.forEach((historyList, key) => {
      result[key] = [...historyList]
    })
    return result
  }

  // 清空历史记录
  clearHistory(key?: string): void {
    if (key) {
      this.history.delete(key)
    } else {
      this.history.clear()
    }
  }

  // 回滚到历史版本
  rollbackTo(key: string, historyId: string): boolean {
    const historyList = this.history.get(key)
    if (!historyList) return false

    const historyItem = historyList.find(item => item.id === historyId)
    if (!historyItem) return false

    // 设置为历史值
    this.setState(key, historyItem.value, { rolledBackFrom: historyId })
    return true
  }

  // 定时自动保存
  private scheduleAutoSave(key: string): void {
    // 清除现有定时器
    const existingTimer = this.saveTimers.get(key)
    if (existingTimer) {
      clearTimeout(existingTimer)
    }

    // 设置新定时器
    const timer = setTimeout(() => {
      this.saveStateToSessionStorage(key)
      this.saveTimers.delete(key)
    }, this.config.saveInterval)

    this.saveTimers.set(key, timer)
  }

  // 保存单个状态到 sessionStorage
  private saveStateToSessionStorage(key: string): void {
    if (!this.config.persistAcrossReload) return

    try {
      const stateItem = this.states.get(key)
      if (stateItem) {
        const storageKey = this.getStorageKey(key)
        let data = JSON.stringify(stateItem)

        // 压缩
        if (this.config.enableCompression) {
          data = this.compress(data)
        }

        // 加密
        if (this.config.enableEncryption) {
          data = this.encrypt(data)
        }

        sessionStorage.setItem(storageKey, data)
      }
    } catch (error) {
      console.error('Failed to save state to sessionStorage:', error)
    }
  }

  // 保存所有状态到 sessionStorage
  private saveToSessionStorage(): void {
    if (!this.config.persistAcrossReload) return

    this.states.forEach((_, key) => {
      this.saveStateToSessionStorage(key)
    })

    // 保存历史记录
    if (this.config.enableHistory) {
      try {
        const historyKey = this.getStorageKey('_history')
        const historyData = JSON.stringify(Object.fromEntries(this.history))
        sessionStorage.setItem(historyKey, historyData)
      } catch (error) {
        console.error('Failed to save history to sessionStorage:', error)
      }
    }
  }

  // 从 sessionStorage 恢复状态
  private restoreFromSessionStorage(): void {
    try {
      // 恢复状态
      for (let i = 0; i < sessionStorage.length; i++) {
        const fullKey = sessionStorage.key(i)
        if (fullKey?.startsWith(this.config.namespace)) {
          const key = fullKey.substring(this.config.namespace.length + 1)
          if (key === '_history') continue

          let data = sessionStorage.getItem(fullKey)
          if (!data) continue

          // 解密
          if (this.config.enableEncryption) {
            data = this.decrypt(data)
          }

          // 解压缩
          if (this.config.enableCompression) {
            data = this.decompress(data)
          }

          const stateItem: SessionStateItem = JSON.parse(data)
          this.states.set(key, stateItem)
        }
      }

      // 恢复历史记录
      if (this.config.enableHistory) {
        const historyKey = this.getStorageKey('_history')
        const historyData = sessionStorage.getItem(historyKey)
        if (historyData) {
          const parsed = JSON.parse(historyData)
          this.history = new Map(Object.entries(parsed))
        }
      }
    } catch (error) {
      console.error('Failed to restore from sessionStorage:', error)
    }
  }

  // 简单压缩
  private compress(data: string): string {
    return btoa(data)
  }

  // 简单解压缩
  private decompress(data: string): string {
    return atob(data)
  }

  // 简单加密
  private encrypt(data: string): string {
    return btoa(data)
  }

  // 简单解密
  private decrypt(data: string): string {
    return atob(data)
  }

  // 获取会话统计信息
  getStats(): {
    sessionId: string
    stateCount: number
    historyCount: number
    totalHistoryItems: number
    memoryUsage: number
  } {
    let totalHistoryItems = 0
    this.history.forEach(historyList => {
      totalHistoryItems += historyList.length
    })

    return {
      sessionId: this.sessionId,
      stateCount: this.states.size,
      historyCount: this.history.size,
      totalHistoryItems,
      memoryUsage: JSON.stringify(Object.fromEntries(this.states)).length
    }
  }

  // 导出会话数据
  export(): string {
    return JSON.stringify({
      sessionId: this.sessionId,
      states: Object.fromEntries(this.states),
      history: Object.fromEntries(this.history),
      config: this.config,
      exportTime: new Date().toISOString()
    }, null, 2)
  }

  // 导入会话数据
  import(data: string): boolean {
    try {
      const imported = JSON.parse(data)
      
      if (imported.states) {
        this.states = new Map(Object.entries(imported.states))
      }
      
      if (imported.history) {
        this.history = new Map(Object.entries(imported.history))
      }
      
      return true
    } catch (error) {
      console.error('Failed to import session data:', error)
      return false
    }
  }
}

// Composable 函数
export function useSessionState<T>(
  key: string,
  defaultValue?: T,
  config: Partial<SessionConfig> = {}
) {
  const route = useRoute()
  const router = useRouter()

  // 创建或获取会话管理器
  const sessionManager = new SessionStateManager(config)

  // 响应式状态
  const state = ref<T>(sessionManager.getState(key, defaultValue) ?? defaultValue!)
  const isLoading = ref(false)
  const error = ref<string | null>(null)
  const lastUpdated = ref<Date | null>(null)
  const history = ref<HistoryItem<T>[]>([])

  // 会话统计
  const stats = reactive({
    sessionId: sessionManager.getStats().sessionId,
    changeCount: 0,
    lastRoute: route.path
  })

  // 更新历史记录
  const updateHistory = () => {
    history.value = sessionManager.getHistory(key) as HistoryItem<T>[]
  }

  // 设置状态
  const setState = (value: T, metadata?: Record<string, any>) => {
    try {
      isLoading.value = true
      error.value = null

      sessionManager.setState(key, value, metadata)
      state.value = value
      lastUpdated.value = new Date()
      stats.changeCount++
      
      updateHistory()
      ElMessage.success('状态已更新')
    } catch (err) {
      error.value = err instanceof Error ? err.message : String(err)
      ElMessage.error('状态更新失败: ' + error.value)
    } finally {
      isLoading.value = false
    }
  }

  // 获取状态
  const getState = (): T | undefined => {
    return sessionManager.getState(key, defaultValue)
  }

  // 清除状态
  const clearState = () => {
    try {
      sessionManager.removeState(key)
      state.value = defaultValue!
      lastUpdated.value = new Date()
      
      updateHistory()
      ElMessage.success('状态已清除')
    } catch (err) {
      error.value = err instanceof Error ? err.message : String(err)
      ElMessage.error('状态清除失败: ' + error.value)
    }
  }

  // 回滚到历史版本
  const rollback = (historyId: string) => {
    try {
      const success = sessionManager.rollbackTo(key, historyId)
      if (success) {
        state.value = sessionManager.getState(key, defaultValue)!
        lastUpdated.value = new Date()
        
        updateHistory()
        ElMessage.success('已回滚到历史版本')
      } else {
        ElMessage.error('回滚失败')
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : String(err)
      ElMessage.error('回滚失败: ' + error.value)
    }
  }

  // 清空历史记录
  const clearHistory = () => {
    sessionManager.clearHistory(key)
    updateHistory()
    ElMessage.success('历史记录已清空')
  }

  // 监听状态变化
  const unsubscribe = sessionManager.addListener('state_change', key, (event) => {
    if (event.newValue !== null) {
      state.value = event.newValue
      lastUpdated.value = new Date(event.timestamp)
      updateHistory()
    }
  })

  // 监听路由变化
  watch(
    () => route.path,
    (newPath) => {
      stats.lastRoute = newPath
      sessionManager.emit('route_change', key, stats.lastRoute, newPath)
    }
  )

  // 自动保存值变化
  const debouncedSetState = debounce((value: T) => {
    sessionManager.setState(key, value)
    updateHistory()
  }, 1000)

  watch(
    state,
    (newValue) => {
      if (config.autoSave !== false) {
        debouncedSetState(newValue)
      }
    },
    { deep: true }
  )

  // 计算属性
  const hasHistory = computed(() => history.value.length > 0)
  const canRollback = computed(() => history.value.length > 1)
  const stateExists = computed(() => sessionManager.hasState(key))

  // 初始化历史记录
  updateHistory()

  // 清理函数
  const cleanup = () => {
    unsubscribe()
  }

  // 组件卸载时清理
  onUnmounted(cleanup)

  return {
    // 状态
    state,
    isLoading,
    error,
    lastUpdated,
    history,
    stats,

    // 计算属性
    hasHistory,
    canRollback,
    stateExists,

    // 方法
    setState,
    getState,
    clearState,
    rollback,
    clearHistory,
    cleanup,

    // 会话管理器实例
    sessionManager
  }
}

// 导出会话管理器类
export { SessionStateManager }

// 类型导出
export type { SessionConfig, SessionStateItem, HistoryItem, SessionEvent }