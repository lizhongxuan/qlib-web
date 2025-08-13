import { ref, reactive, watch, computed, onUnmounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElNotification } from 'element-plus'
import { debounce, throttle } from 'lodash-es'

// 离线配置
interface OfflineConfig {
  enableOfflineMode: boolean // 是否启用离线模式
  enableCaching: boolean // 是否启用缓存
  cacheStrategy: 'cache-first' | 'network-first' | 'cache-only' | 'network-only' // 缓存策略
  maxCacheSize: number // 最大缓存大小（字节）
  maxCacheAge: number // 最大缓存时间（毫秒）
  enableOfflineQueue: boolean // 是否启用离线队列
  enablePeriodicSync: boolean // 是否启用定期同步
  syncInterval: number // 同步间隔（毫秒）
  enableBackgroundSync: boolean // 是否启用后台同步
  showOfflineNotifications: boolean // 是否显示离线通知
  offlinePageUrl?: string // 离线页面URL
}

// 离线状态
interface OfflineStatus {
  isOnline: boolean
  isOfflineMode: boolean
  lastOnlineTime: Date | null
  offlineDuration: number
  cacheSize: number
  queuedActions: number
  pendingSyncCount: number
  dataFreshness: 'fresh' | 'stale' | 'expired'
}

// 缓存项
interface CacheItem {
  key: string
  data: any
  timestamp: number
  expiresAt: number
  etag?: string
  url?: string
  method?: string
  size: number
}

// 离线操作
interface OfflineOperation {
  id: string
  type: 'api_call' | 'data_update' | 'file_upload' | 'custom'
  action: string
  data: any
  timestamp: number
  priority: 'high' | 'medium' | 'low'
  retryCount: number
  maxRetries: number
  status: 'pending' | 'retrying' | 'failed' | 'completed'
  error?: string
}

// 同步结果
interface SyncResult {
  success: boolean
  completedOperations: number
  failedOperations: number
  errors: string[]
}

// 离线状态管理器
class OfflineStateManager {
  private config: OfflineConfig
  private cache: Map<string, CacheItem> = new Map()
  private offlineQueue: OfflineOperation[] = []
  private status: OfflineStatus
  private syncTimer?: NodeJS.Timeout
  private cacheCleanupTimer?: NodeJS.Timeout
  private networkListeners: (() => void)[] = []

  constructor(config: Partial<OfflineConfig> = {}) {
    this.config = {
      enableOfflineMode: true,
      enableCaching: true,
      cacheStrategy: 'network-first',
      maxCacheSize: 50 * 1024 * 1024, // 50MB
      maxCacheAge: 24 * 60 * 60 * 1000, // 24小时
      enableOfflineQueue: true,
      enablePeriodicSync: true,
      syncInterval: 30000, // 30秒
      enableBackgroundSync: false,
      showOfflineNotifications: true,
      ...config
    }

    this.status = {
      isOnline: navigator.onLine,
      isOfflineMode: !navigator.onLine,
      lastOnlineTime: navigator.onLine ? new Date() : null,
      offlineDuration: 0,
      cacheSize: 0,
      queuedActions: 0,
      pendingSyncCount: 0,
      dataFreshness: 'fresh'
    }

    this.initialize()
  }

  // 初始化
  private initialize(): void {
    // 加载缓存
    this.loadCacheFromStorage()

    // 加载离线队列
    this.loadQueueFromStorage()

    // 设置网络监听
    this.setupNetworkListeners()

    // 设置定期同步
    if (this.config.enablePeriodicSync) {
      this.startPeriodicSync()
    }

    // 设置缓存清理
    this.startCacheCleanup()

    // 注册Service Worker (如果支持)
    if (this.config.enableBackgroundSync && 'serviceWorker' in navigator) {
      this.registerServiceWorker()
    }
  }

  // 设置网络监听
  private setupNetworkListeners(): void {
    const onOnline = () => {
      this.handleNetworkOnline()
    }

    const onOffline = () => {
      this.handleNetworkOffline()
    }

    window.addEventListener('online', onOnline)
    window.addEventListener('offline', onOffline)

    this.networkListeners.push(
      () => window.removeEventListener('online', onOnline),
      () => window.removeEventListener('offline', onOffline)
    )
  }

  // 网络连接恢复
  private handleNetworkOnline(): void {
    this.status.isOnline = true
    this.status.isOfflineMode = false
    this.status.lastOnlineTime = new Date()
    this.status.offlineDuration = 0

    if (this.config.showOfflineNotifications) {
      ElNotification({
        title: '网络已连接',
        message: '正在同步离线数据...',
        type: 'success',
        duration: 3000
      })
    }

    // 自动同步离线数据
    if (this.config.enableOfflineQueue) {
      this.syncOfflineOperations()
    }
  }

  // 网络连接断开
  private handleNetworkOffline(): void {
    this.status.isOnline = false
    this.status.isOfflineMode = true

    if (this.config.showOfflineNotifications) {
      ElNotification({
        title: '网络已断开',
        message: '现在处于离线模式，数据将缓存在本地',
        type: 'warning',
        duration: 5000
      })
    }
  }

  // 缓存数据
  setCache(key: string, data: any, options: {
    ttl?: number
    etag?: string
    url?: string
    method?: string
  } = {}): boolean {
    try {
      const now = Date.now()
      const ttl = options.ttl || this.config.maxCacheAge
      const dataString = JSON.stringify(data)
      const size = new Blob([dataString]).size

      // 检查缓存大小限制
      if (this.getCacheSize() + size > this.config.maxCacheSize) {
        this.cleanupOldCache()
        
        // 如果清理后仍然超出限制，拒绝缓存
        if (this.getCacheSize() + size > this.config.maxCacheSize) {
          return false
        }
      }

      const cacheItem: CacheItem = {
        key,
        data,
        timestamp: now,
        expiresAt: now + ttl,
        etag: options.etag,
        url: options.url,
        method: options.method,
        size
      }

      this.cache.set(key, cacheItem)
      this.saveCacheToStorage()
      this.updateCacheSize()

      return true
    } catch (error) {
      console.error('Failed to cache data:', error)
      return false
    }
  }

  // 获取缓存数据
  getCache(key: string): any | null {
    const item = this.cache.get(key)
    
    if (!item) {
      return null
    }

    // 检查是否过期
    if (Date.now() > item.expiresAt) {
      this.cache.delete(key)
      this.saveCacheToStorage()
      this.updateCacheSize()
      return null
    }

    return item.data
  }

  // 检查缓存是否存在且有效
  hasValidCache(key: string): boolean {
    const item = this.cache.get(key)
    return item ? Date.now() <= item.expiresAt : false
  }

  // 清除特定缓存
  clearCache(key: string): boolean {
    const deleted = this.cache.delete(key)
    if (deleted) {
      this.saveCacheToStorage()
      this.updateCacheSize()
    }
    return deleted
  }

  // 清除所有缓存
  clearAllCache(): void {
    this.cache.clear()
    this.saveCacheToStorage()
    this.updateCacheSize()
  }

  // 添加离线操作
  addOfflineOperation(operation: Omit<OfflineOperation, 'id' | 'timestamp' | 'retryCount' | 'status'>): string {
    const id = `op_${Date.now()}_${Math.random().toString(36).substr(2, 6)}`
    
    const offlineOp: OfflineOperation = {
      id,
      timestamp: Date.now(),
      retryCount: 0,
      status: 'pending',
      ...operation
    }

    this.offlineQueue.push(offlineOp)
    this.saveQueueToStorage()
    this.status.queuedActions = this.offlineQueue.length

    return id
  }

  // 移除离线操作
  removeOfflineOperation(id: string): boolean {
    const index = this.offlineQueue.findIndex(op => op.id === id)
    if (index > -1) {
      this.offlineQueue.splice(index, 1)
      this.saveQueueToStorage()
      this.status.queuedActions = this.offlineQueue.length
      return true
    }
    return false
  }

  // 同步离线操作
  async syncOfflineOperations(): Promise<SyncResult> {
    if (!this.status.isOnline || this.offlineQueue.length === 0) {
      return {
        success: true,
        completedOperations: 0,
        failedOperations: 0,
        errors: []
      }
    }

    const result: SyncResult = {
      success: true,
      completedOperations: 0,
      failedOperations: 0,
      errors: []
    }

    // 按优先级排序
    const sortedQueue = [...this.offlineQueue].sort((a, b) => {
      const priorityOrder = { high: 3, medium: 2, low: 1 }
      return priorityOrder[b.priority] - priorityOrder[a.priority]
    })

    for (const operation of sortedQueue) {
      if (operation.status === 'completed') {
        continue
      }

      try {
        operation.status = 'retrying'
        const success = await this.executeOperation(operation)
        
        if (success) {
          operation.status = 'completed'
          result.completedOperations++
        } else {
          operation.retryCount++
          if (operation.retryCount >= operation.maxRetries) {
            operation.status = 'failed'
            result.failedOperations++
            result.errors.push(`Operation ${operation.id} failed after ${operation.maxRetries} retries`)
          } else {
            operation.status = 'pending'
          }
        }
      } catch (error) {
        operation.retryCount++
        operation.error = error instanceof Error ? error.message : String(error)
        
        if (operation.retryCount >= operation.maxRetries) {
          operation.status = 'failed'
          result.failedOperations++
          result.errors.push(`Operation ${operation.id} failed: ${operation.error}`)
        } else {
          operation.status = 'pending'
        }
      }
    }

    // 移除已完成的操作
    this.offlineQueue = this.offlineQueue.filter(op => op.status !== 'completed')
    this.saveQueueToStorage()
    this.status.queuedActions = this.offlineQueue.length

    result.success = result.failedOperations === 0

    return result
  }

  // 执行单个操作
  private async executeOperation(operation: OfflineOperation): Promise<boolean> {
    switch (operation.type) {
      case 'api_call':
        return await this.executeApiCall(operation)
      case 'data_update':
        return await this.executeDataUpdate(operation)
      case 'file_upload':
        return await this.executeFileUpload(operation)
      case 'custom':
        return await this.executeCustomOperation(operation)
      default:
        throw new Error(`Unknown operation type: ${operation.type}`)
    }
  }

  // 执行API调用
  private async executeApiCall(operation: OfflineOperation): Promise<boolean> {
    try {
      const { url, method = 'GET', data, headers = {} } = operation.data

      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
          ...headers
        },
        body: data ? JSON.stringify(data) : undefined
      })

      return response.ok
    } catch (error) {
      console.error('API call failed:', error)
      return false
    }
  }

  // 执行数据更新
  private async executeDataUpdate(operation: OfflineOperation): Promise<boolean> {
    try {
      // 这里应该实现具体的数据更新逻辑
      // 例如：调用状态管理器的更新方法
      return true
    } catch (error) {
      console.error('Data update failed:', error)
      return false
    }
  }

  // 执行文件上传
  private async executeFileUpload(operation: OfflineOperation): Promise<boolean> {
    try {
      const { url, file, formData } = operation.data
      
      const uploadData = formData || new FormData()
      if (file) {
        uploadData.append('file', file)
      }

      const response = await fetch(url, {
        method: 'POST',
        body: uploadData
      })

      return response.ok
    } catch (error) {
      console.error('File upload failed:', error)
      return false
    }
  }

  // 执行自定义操作
  private async executeCustomOperation(operation: OfflineOperation): Promise<boolean> {
    try {
      const { handler, ...args } = operation.data
      
      if (typeof handler === 'function') {
        await handler(args)
        return true
      }
      
      return false
    } catch (error) {
      console.error('Custom operation failed:', error)
      return false
    }
  }

  // 根据缓存策略获取数据
  async fetchWithCacheStrategy(
    key: string,
    fetcher: () => Promise<any>,
    options: {
      ttl?: number
      forceRefresh?: boolean
    } = {}
  ): Promise<any> {
    const { ttl, forceRefresh = false } = options

    switch (this.config.cacheStrategy) {
      case 'cache-first':
        return await this.cacheFirst(key, fetcher, ttl, forceRefresh)
      case 'network-first':
        return await this.networkFirst(key, fetcher, ttl, forceRefresh)
      case 'cache-only':
        return this.getCache(key)
      case 'network-only':
        return await this.networkOnly(fetcher)
      default:
        return await this.networkFirst(key, fetcher, ttl, forceRefresh)
    }
  }

  // 缓存优先策略
  private async cacheFirst(key: string, fetcher: () => Promise<any>, ttl?: number, forceRefresh = false): Promise<any> {
    if (!forceRefresh && this.hasValidCache(key)) {
      return this.getCache(key)
    }

    if (this.status.isOnline) {
      try {
        const data = await fetcher()
        this.setCache(key, data, { ttl })
        return data
      } catch (error) {
        // 网络失败，返回缓存数据（如果有）
        const cachedData = this.getCache(key)
        if (cachedData !== null) {
          return cachedData
        }
        throw error
      }
    } else {
      // 离线模式，返回缓存数据
      const cachedData = this.getCache(key)
      if (cachedData !== null) {
        return cachedData
      }
      throw new Error('No cached data available in offline mode')
    }
  }

  // 网络优先策略
  private async networkFirst(key: string, fetcher: () => Promise<any>, ttl?: number, forceRefresh = false): Promise<any> {
    if (this.status.isOnline && !forceRefresh) {
      try {
        const data = await fetcher()
        this.setCache(key, data, { ttl })
        return data
      } catch (error) {
        // 网络失败，尝试返回缓存数据
        const cachedData = this.getCache(key)
        if (cachedData !== null) {
          return cachedData
        }
        throw error
      }
    } else {
      // 离线模式或强制刷新，返回缓存数据
      if (!forceRefresh && this.hasValidCache(key)) {
        return this.getCache(key)
      }
      
      const cachedData = this.getCache(key)
      if (cachedData !== null) {
        return cachedData
      }
      
      throw new Error('No data available in offline mode')
    }
  }

  // 仅网络策略
  private async networkOnly(fetcher: () => Promise<any>): Promise<any> {
    if (!this.status.isOnline) {
      throw new Error('Network request not available in offline mode')
    }
    return await fetcher()
  }

  // 获取缓存大小
  private getCacheSize(): number {
    let totalSize = 0
    this.cache.forEach(item => {
      totalSize += item.size
    })
    return totalSize
  }

  // 更新缓存大小状态
  private updateCacheSize(): void {
    this.status.cacheSize = this.getCacheSize()
  }

  // 清理过期缓存
  private cleanupOldCache(): void {
    const now = Date.now()
    const itemsToDelete: string[] = []

    // 首先删除过期的项目
    this.cache.forEach((item, key) => {
      if (now > item.expiresAt) {
        itemsToDelete.push(key)
      }
    })

    itemsToDelete.forEach(key => this.cache.delete(key))

    // 如果仍然超出限制，删除最旧的项目
    if (this.getCacheSize() > this.config.maxCacheSize) {
      const sortedItems = Array.from(this.cache.entries())
        .sort((a, b) => a[1].timestamp - b[1].timestamp)

      let currentSize = this.getCacheSize()
      let index = 0

      while (currentSize > this.config.maxCacheSize * 0.8 && index < sortedItems.length) {
        const [key, item] = sortedItems[index]
        this.cache.delete(key)
        currentSize -= item.size
        index++
      }
    }

    this.saveCacheToStorage()
    this.updateCacheSize()
  }

  // 启动定期同步
  private startPeriodicSync(): void {
    if (this.syncTimer) {
      clearInterval(this.syncTimer)
    }

    this.syncTimer = setInterval(() => {
      if (this.status.isOnline && this.offlineQueue.length > 0) {
        this.syncOfflineOperations()
      }
    }, this.config.syncInterval)
  }

  // 启动缓存清理
  private startCacheCleanup(): void {
    if (this.cacheCleanupTimer) {
      clearInterval(this.cacheCleanupTimer)
    }

    this.cacheCleanupTimer = setInterval(() => {
      this.cleanupOldCache()
    }, 60 * 60 * 1000) // 每小时清理一次
  }

  // 注册Service Worker
  private async registerServiceWorker(): Promise<void> {
    if ('serviceWorker' in navigator) {
      try {
        // 这里应该注册实际的Service Worker文件
        // const registration = await navigator.serviceWorker.register('/sw.js')
        console.log('Service Worker registered for background sync')
      } catch (error) {
        console.error('Service Worker registration failed:', error)
      }
    }
  }

  // 保存缓存到存储
  private saveCacheToStorage(): void {
    try {
      const cacheData = Array.from(this.cache.entries())
      localStorage.setItem('offline_cache', JSON.stringify(cacheData))
    } catch (error) {
      console.error('Failed to save cache to storage:', error)
    }
  }

  // 从存储加载缓存
  private loadCacheFromStorage(): void {
    try {
      const data = localStorage.getItem('offline_cache')
      if (data) {
        const cacheData = JSON.parse(data)
        this.cache = new Map(cacheData)
        this.updateCacheSize()
      }
    } catch (error) {
      console.error('Failed to load cache from storage:', error)
    }
  }

  // 保存队列到存储
  private saveQueueToStorage(): void {
    try {
      localStorage.setItem('offline_queue', JSON.stringify(this.offlineQueue))
    } catch (error) {
      console.error('Failed to save queue to storage:', error)
    }
  }

  // 从存储加载队列
  private loadQueueFromStorage(): void {
    try {
      const data = localStorage.getItem('offline_queue')
      if (data) {
        this.offlineQueue = JSON.parse(data)
        this.status.queuedActions = this.offlineQueue.length
      }
    } catch (error) {
      console.error('Failed to load queue from storage:', error)
    }
  }

  // 获取状态
  getStatus(): OfflineStatus {
    // 更新离线时长
    if (this.status.isOfflineMode && this.status.lastOnlineTime) {
      this.status.offlineDuration = Date.now() - this.status.lastOnlineTime.getTime()
    }

    // 更新数据新鲜度
    this.updateDataFreshness()

    return { ...this.status }
  }

  // 更新数据新鲜度
  private updateDataFreshness(): void {
    if (this.status.isOnline) {
      this.status.dataFreshness = 'fresh'
    } else if (this.status.offlineDuration < 30 * 60 * 1000) { // 30分钟内
      this.status.dataFreshness = 'stale'
    } else {
      this.status.dataFreshness = 'expired'
    }
  }

  // 清理资源
  cleanup(): void {
    if (this.syncTimer) {
      clearInterval(this.syncTimer)
    }

    if (this.cacheCleanupTimer) {
      clearInterval(this.cacheCleanupTimer)
    }

    this.networkListeners.forEach(removeListener => removeListener())
    this.networkListeners = []

    this.saveCacheToStorage()
    this.saveQueueToStorage()
  }
}

// Composable 函数
export function useOfflineState(config: Partial<OfflineConfig> = {}) {
  const route = useRoute()
  const router = useRouter()

  // 创建离线管理器
  const offlineManager = new OfflineStateManager(config)

  // 响应式状态
  const status = reactive<OfflineStatus>(offlineManager.getStatus())
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  // 更新状态
  const updateStatus = () => {
    Object.assign(status, offlineManager.getStatus())
  }

  // 定期更新状态
  const statusTimer = setInterval(updateStatus, 5000)

  // 缓存数据
  const cacheData = (key: string, data: any, options?: { ttl?: number; etag?: string }) => {
    return offlineManager.setCache(key, data, options)
  }

  // 获取缓存数据
  const getCachedData = (key: string) => {
    return offlineManager.getCache(key)
  }

  // 带缓存策略的数据获取
  const fetchWithCache = async (
    key: string,
    fetcher: () => Promise<any>,
    options?: { ttl?: number; forceRefresh?: boolean }
  ) => {
    try {
      isLoading.value = true
      error.value = null
      
      const data = await offlineManager.fetchWithCacheStrategy(key, fetcher, options)
      updateStatus()
      
      return data
    } catch (err) {
      error.value = err instanceof Error ? err.message : String(err)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  // 添加离线操作
  const addOfflineOperation = (
    type: OfflineOperation['type'],
    action: string,
    data: any,
    options: {
      priority?: OfflineOperation['priority']
      maxRetries?: number
    } = {}
  ) => {
    const operation = {
      type,
      action,
      data,
      priority: options.priority || 'medium',
      maxRetries: options.maxRetries || 3
    }

    const id = offlineManager.addOfflineOperation(operation)
    updateStatus()
    
    return id
  }

  // 手动同步
  const manualSync = async () => {
    try {
      isLoading.value = true
      error.value = null
      
      const result = await offlineManager.syncOfflineOperations()
      updateStatus()
      
      if (result.success) {
        ElMessage.success(`同步完成：${result.completedOperations} 个操作成功`)
      } else {
        ElMessage.warning(`同步部分完成：${result.completedOperations} 成功，${result.failedOperations} 失败`)
      }
      
      return result
    } catch (err) {
      error.value = err instanceof Error ? err.message : String(err)
      ElMessage.error('同步失败: ' + error.value)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  // 清除缓存
  const clearCache = (key?: string) => {
    if (key) {
      offlineManager.clearCache(key)
    } else {
      offlineManager.clearAllCache()
    }
    
    updateStatus()
    ElMessage.success(key ? '缓存已清除' : '所有缓存已清除')
  }

  // 检查网络状态
  const checkConnection = async (): Promise<boolean> => {
    try {
      const response = await fetch('/api/health', {
        method: 'HEAD',
        cache: 'no-cache'
      })
      return response.ok
    } catch {
      return false
    }
  }

  // 计算属性
  const isOnline = computed(() => status.isOnline)
  const isOffline = computed(() => !status.isOnline)
  const hasQueuedOperations = computed(() => status.queuedActions > 0)
  const cacheUsage = computed(() => {
    const maxSize = config.maxCacheSize || 50 * 1024 * 1024
    return {
      used: status.cacheSize,
      max: maxSize,
      percentage: (status.cacheSize / maxSize) * 100
    }
  })

  const dataFreshnessColor = computed(() => {
    switch (status.dataFreshness) {
      case 'fresh': return 'success'
      case 'stale': return 'warning'
      case 'expired': return 'danger'
      default: return 'info'
    }
  })

  // 清理函数
  const cleanup = () => {
    clearInterval(statusTimer)
    offlineManager.cleanup()
  }

  // 组件卸载时清理
  onUnmounted(cleanup)

  // 初始化状态
  updateStatus()

  return {
    // 状态
    status,
    isLoading,
    error,

    // 计算属性
    isOnline,
    isOffline,
    hasQueuedOperations,
    cacheUsage,
    dataFreshnessColor,

    // 方法
    cacheData,
    getCachedData,
    fetchWithCache,
    addOfflineOperation,
    manualSync,
    clearCache,
    checkConnection,
    cleanup,

    // 离线管理器
    offlineManager
  }
}

// 导出离线状态管理器类
export { OfflineStateManager }

// 类型导出
export type { OfflineConfig, OfflineStatus, CacheItem, OfflineOperation, SyncResult }