/**
 * Qlib API请求优化服务
 * 
 * 此服务实现了qlib API请求的防抖和请求合并优化，包括：
 * - 请求防抖和节流机制
 * - 智能请求合并和批处理
 * - 请求缓存和重复请求去除
 * - 自动重试和错误恢复
 * - 请求优先级管理
 * - 网络状态感知优化
 * 
 * 修改理由：
 * 1. 实现TODO 7.2.7节中API请求防抖和合并优化需求
 * 2. 减少不必要的网络请求，提升系统性能
 * 3. 实现智能的请求调度和优先级管理
 * 4. 提供网络异常情况下的优雅降级
 * 5. 优化用户体验，减少等待时间
 */

import { ref, reactive } from 'vue'
import { qlibIntelligentCache } from './qlib-intelligent-cache'
import { QLIB_API_CONFIG } from '@/config/qlib-config.js'

// 请求优先级枚举
export enum RequestPriority {
  LOW = 1,
  NORMAL = 5,
  HIGH = 8,
  CRITICAL = 10
}

// 请求状态枚举
export enum RequestStatus {
  PENDING = 'pending',
  RUNNING = 'running',
  COMPLETED = 'completed',
  FAILED = 'failed',
  CANCELLED = 'cancelled'
}

// 请求配置接口
export interface RequestConfig {
  url: string
  method: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH'
  data?: any
  params?: Record<string, any>
  headers?: Record<string, string>
  timeout?: number
  retryCount?: number
  priority?: RequestPriority
  debounceMs?: number
  throttleMs?: number
  enableCache?: boolean
  cacheTtl?: number
  mergeable?: boolean
  mergeKey?: string
  abortSignal?: AbortSignal
}

// 请求结果接口
export interface RequestResult<T = any> {
  data: T
  status: number
  statusText: string
  headers: Record<string, string>
  config: RequestConfig
  fromCache?: boolean
  merged?: boolean
  retryCount?: number
  duration: number
}

// 批量请求配置
export interface BatchRequestConfig {
  requests: RequestConfig[]
  maxConcurrent?: number
  failFast?: boolean
  retryFailedRequests?: boolean
}

// 请求统计信息
export interface RequestStats {
  total: number
  completed: number
  failed: number
  cached: number
  merged: number
  averageTime: number
  networkStatus: 'online' | 'offline' | 'slow'
}

// 合并请求项
interface MergeableRequest {
  id: string
  config: RequestConfig
  resolve: (result: any) => void
  reject: (error: any) => void
  timestamp: number
  priority: RequestPriority
}

// 防抖请求项
interface DebouncedRequest {
  id: string
  config: RequestConfig
  resolve: (result: any) => void
  reject: (error: any) => void
  timer: NodeJS.Timeout
}

/**
 * Qlib请求优化器
 */
export class QlibRequestOptimizer {
  private static instance: QlibRequestOptimizer
  private requestQueue: Map<RequestPriority, RequestConfig[]> = new Map()
  private activeRequests: Map<string, Promise<RequestResult>> = new Map()
  private debouncedRequests: Map<string, DebouncedRequest> = new Map()
  private mergeableRequests: Map<string, MergeableRequest[]> = new Map()
  private requestStats: RequestStats
  private maxConcurrentRequests = 6
  private batchProcessor: NodeJS.Timeout | null = null
  private networkMonitor: any = null

  private constructor() {
    this.initializeStats()
    this.initializeRequestQueue()
    this.startBatchProcessor()
    this.initializeNetworkMonitor()
  }

  public static getInstance(): QlibRequestOptimizer {
    if (!QlibRequestOptimizer.instance) {
      QlibRequestOptimizer.instance = new QlibRequestOptimizer()
    }
    return QlibRequestOptimizer.instance
  }

  /**
   * 初始化统计信息
   */
  private initializeStats(): void {
    this.requestStats = reactive({
      total: 0,
      completed: 0,
      failed: 0,
      cached: 0,
      merged: 0,
      averageTime: 0,
      networkStatus: 'online'
    })
  }

  /**
   * 初始化请求队列
   */
  private initializeRequestQueue(): void {
    Object.values(RequestPriority).forEach(priority => {
      if (typeof priority === 'number') {
        this.requestQueue.set(priority, [])
      }
    })
  }

  /**
   * 启动批处理器
   */
  private startBatchProcessor(): void {
    this.batchProcessor = setInterval(() => {
      this.processBatchRequests()
      this.processQueue()
    }, 100) // 每100ms处理一次
  }

  /**
   * 初始化网络监控
   */
  private initializeNetworkMonitor(): void {
    if (typeof navigator !== 'undefined' && 'connection' in navigator) {
      this.networkMonitor = (navigator as any).connection

      const updateNetworkStatus = () => {
        const connection = this.networkMonitor
        if (connection) {
          if (connection.effectiveType === 'slow-2g' || connection.effectiveType === '2g') {
            this.requestStats.networkStatus = 'slow'
          } else {
            this.requestStats.networkStatus = 'online'
          }
        }
      }

      updateNetworkStatus()
      this.networkMonitor.addEventListener('change', updateNetworkStatus)
    }

    // 监听在线/离线状态
    window.addEventListener('online', () => {
      this.requestStats.networkStatus = 'online'
    })

    window.addEventListener('offline', () => {
      this.requestStats.networkStatus = 'offline'
    })
  }

  /**
   * 优化的请求方法
   */
  public async request<T = any>(config: RequestConfig): Promise<RequestResult<T>> {
    this.requestStats.total++

    // 检查缓存
    if (config.enableCache !== false) {
      const cached = await this.checkCache<T>(config)
      if (cached) {
        this.requestStats.cached++
        return cached
      }
    }

    // 防抖处理
    if (config.debounceMs && config.debounceMs > 0) {
      return this.debounceRequest<T>(config)
    }

    // 合并处理
    if (config.mergeable && config.mergeKey) {
      return this.mergeRequest<T>(config)
    }

    // 立即执行请求
    return this.executeRequest<T>(config)
  }

  /**
   * 防抖请求
   */
  private debounceRequest<T>(config: RequestConfig): Promise<RequestResult<T>> {
    const key = this.generateRequestKey(config)
    
    return new Promise((resolve, reject) => {
      // 取消之前的防抖请求
      const existing = this.debouncedRequests.get(key)
      if (existing) {
        clearTimeout(existing.timer)
        existing.reject(new Error('Request cancelled by debounce'))
      }

      // 创建新的防抖请求
      const timer = setTimeout(async () => {
        this.debouncedRequests.delete(key)
        try {
          const result = await this.executeRequest<T>(config)
          resolve(result)
        } catch (error) {
          reject(error)
        }
      }, config.debounceMs!)

      this.debouncedRequests.set(key, {
        id: key,
        config,
        resolve,
        reject,
        timer
      })
    })
  }

  /**
   * 合并请求
   */
  private mergeRequest<T>(config: RequestConfig): Promise<RequestResult<T>> {
    const mergeKey = config.mergeKey!
    
    return new Promise((resolve, reject) => {
      const request: MergeableRequest = {
        id: this.generateRequestKey(config),
        config,
        resolve,
        reject,
        timestamp: Date.now(),
        priority: config.priority || RequestPriority.NORMAL
      }

      if (!this.mergeableRequests.has(mergeKey)) {
        this.mergeableRequests.set(mergeKey, [])
      }

      this.mergeableRequests.get(mergeKey)!.push(request)
    })
  }

  /**
   * 执行单个请求
   */
  private async executeRequest<T>(config: RequestConfig): Promise<RequestResult<T>> {
    const key = this.generateRequestKey(config)
    
    // 检查是否已有相同请求在执行
    if (this.activeRequests.has(key)) {
      return this.activeRequests.get(key) as Promise<RequestResult<T>>
    }

    const startTime = Date.now()
    const requestPromise = this.performRequest<T>(config, startTime)
    
    this.activeRequests.set(key, requestPromise)

    try {
      const result = await requestPromise
      this.requestStats.completed++
      this.updateAverageTime(Date.now() - startTime)
      return result
    } catch (error) {
      this.requestStats.failed++
      throw error
    } finally {
      this.activeRequests.delete(key)
    }
  }

  /**
   * 执行实际的HTTP请求
   */
  private async performRequest<T>(config: RequestConfig, startTime: number): Promise<RequestResult<T>> {
    const {
      url,
      method = 'GET',
      data,
      params,
      headers = {},
      timeout = 30000,
      retryCount = 3,
      abortSignal
    } = config

    // 构建完整URL
    let fullUrl = url.startsWith('http') ? url : `${QLIB_API_CONFIG.base_url}${url}`
    
    // 添加查询参数
    if (params && Object.keys(params).length > 0) {
      const searchParams = new URLSearchParams()
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          searchParams.append(key, String(value))
        }
      })
      fullUrl += `?${searchParams.toString()}`
    }

    // 构建请求选项
    const requestOptions: RequestInit = {
      method,
      headers: {
        'Content-Type': 'application/json',
        ...headers
      },
      signal: abortSignal
    }

    // 添加请求体
    if (data && (method === 'POST' || method === 'PUT' || method === 'PATCH')) {
      requestOptions.body = JSON.stringify(data)
    }

    // 设置超时
    const timeoutController = new AbortController()
    const timeoutId = setTimeout(() => timeoutController.abort(), timeout)

    // 合并AbortSignal
    if (abortSignal) {
      const combinedController = new AbortController()
      const abortHandler = () => combinedController.abort()
      
      abortSignal.addEventListener('abort', abortHandler)
      timeoutController.signal.addEventListener('abort', abortHandler)
      
      requestOptions.signal = combinedController.signal
    } else {
      requestOptions.signal = timeoutController.signal
    }

    let lastError: Error | null = null
    let attemptCount = 0

    while (attemptCount <= retryCount) {
      try {
        const response = await fetch(fullUrl, requestOptions)
        clearTimeout(timeoutId)

        // 检查响应状态
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`)
        }

        // 解析响应
        const responseData = await response.json()

        // 构建响应头对象
        const responseHeaders: Record<string, string> = {}
        response.headers.forEach((value, key) => {
          responseHeaders[key] = value
        })

        const result: RequestResult<T> = {
          data: responseData,
          status: response.status,
          statusText: response.statusText,
          headers: responseHeaders,
          config,
          retryCount: attemptCount,
          duration: Date.now() - startTime
        }

        // 缓存成功的请求结果
        if (config.enableCache !== false) {
          this.cacheResult(config, result)
        }

        return result

      } catch (error) {
        lastError = error instanceof Error ? error : new Error(String(error))
        attemptCount++

        // 如果不是最后一次尝试，等待一段时间后重试
        if (attemptCount <= retryCount) {
          const delay = Math.min(1000 * Math.pow(2, attemptCount - 1), 5000)
          await this.sleep(delay)
        }
      }
    }

    clearTimeout(timeoutId)
    throw lastError || new Error('Request failed')
  }

  /**
   * 批量请求
   */
  public async batchRequest(config: BatchRequestConfig): Promise<RequestResult[]> {
    const {
      requests,
      maxConcurrent = this.maxConcurrentRequests,
      failFast = false,
      retryFailedRequests = false
    } = config

    const results: RequestResult[] = []
    const errors: Error[] = []

    // 按优先级排序请求
    const sortedRequests = requests.sort((a, b) => 
      (b.priority || RequestPriority.NORMAL) - (a.priority || RequestPriority.NORMAL)
    )

    // 分批执行请求
    for (let i = 0; i < sortedRequests.length; i += maxConcurrent) {
      const batch = sortedRequests.slice(i, i + maxConcurrent)
      const batchPromises = batch.map(async (req, index) => {
        try {
          const result = await this.request(req)
          return { result, index: i + index, error: null }
        } catch (error) {
          return { result: null, index: i + index, error }
        }
      })

      const batchResults = await Promise.all(batchPromises)

      for (const { result, index, error } of batchResults) {
        if (result) {
          results[index] = result
        } else if (error) {
          errors[index] = error as Error
          
          if (failFast) {
            throw error
          }
        }
      }
    }

    // 重试失败的请求
    if (retryFailedRequests && errors.length > 0) {
      const retryRequests = errors
        .map((error, index) => error ? requests[index] : null)
        .filter(Boolean) as RequestConfig[]

      if (retryRequests.length > 0) {
        const retryResults = await this.batchRequest({
          requests: retryRequests,
          maxConcurrent,
          failFast: false,
          retryFailedRequests: false
        })

        // 合并重试结果
        let retryIndex = 0
        for (let i = 0; i < errors.length; i++) {
          if (errors[i] && retryIndex < retryResults.length) {
            results[i] = retryResults[retryIndex++]
          }
        }
      }
    }

    return results
  }

  /**
   * 处理批量合并请求
   */
  private processBatchRequests(): void {
    this.mergeableRequests.forEach(async (requests, mergeKey) => {
      if (requests.length === 0) return

      // 检查是否有足够的请求进行合并，或者最早的请求是否超时
      const oldestRequest = requests[0]
      const shouldProcess = requests.length >= 5 || 
                           (Date.now() - oldestRequest.timestamp > 500)

      if (shouldProcess) {
        const batchRequests = requests.splice(0)
        
        try {
          // 合并请求参数
          const mergedConfig = this.mergeRequestConfigs(batchRequests.map(r => r.config))
          const result = await this.executeRequest(mergedConfig)
          
          // 分发结果给所有请求
          batchRequests.forEach(req => {
            req.resolve({
              ...result,
              merged: true
            })
          })
          
          this.requestStats.merged += batchRequests.length - 1

        } catch (error) {
          // 如果合并请求失败，尝试单独执行每个请求
          batchRequests.forEach(async req => {
            try {
              const result = await this.executeRequest(req.config)
              req.resolve(result)
            } catch (individualError) {
              req.reject(individualError)
            }
          })
        }
      }
    })
  }

  /**
   * 处理请求队列
   */
  private processQueue(): void {
    const currentActive = this.activeRequests.size
    if (currentActive >= this.maxConcurrentRequests) {
      return
    }

    // 按优先级处理队列
    const priorities = Array.from(this.requestQueue.keys()).sort((a, b) => b - a)
    
    for (const priority of priorities) {
      const queue = this.requestQueue.get(priority)!
      
      while (queue.length > 0 && this.activeRequests.size < this.maxConcurrentRequests) {
        const config = queue.shift()!
        this.executeRequest(config).catch(() => {}) // 忽略错误，由调用者处理
      }
    }
  }

  /**
   * 合并请求配置
   */
  private mergeRequestConfigs(configs: RequestConfig[]): RequestConfig {
    // 这里实现具体的合并逻辑
    // 简单示例：合并查询参数
    const baseConfig = configs[0]
    const mergedParams = configs.reduce((acc, config) => {
      return { ...acc, ...config.params }
    }, {})

    return {
      ...baseConfig,
      params: mergedParams
    }
  }

  /**
   * 检查缓存
   */
  private async checkCache<T>(config: RequestConfig): Promise<RequestResult<T> | null> {
    const cacheKey = this.generateCacheKey(config)
    const cached = await qlibIntelligentCache.get<RequestResult<T>>(cacheKey)
    
    if (cached) {
      return {
        ...cached,
        fromCache: true
      }
    }
    
    return null
  }

  /**
   * 缓存结果
   */
  private async cacheResult(config: RequestConfig, result: RequestResult): Promise<void> {
    const cacheKey = this.generateCacheKey(config)
    const ttl = config.cacheTtl || 5 * 60 * 1000 // 默认5分钟

    await qlibIntelligentCache.set(cacheKey, result, {
      ttl,
      tags: ['api_request', config.method.toLowerCase()],
      priority: config.priority || RequestPriority.NORMAL
    })
  }

  /**
   * 生成请求键
   */
  private generateRequestKey(config: RequestConfig): string {
    const { url, method, data, params } = config
    const keyData = { url, method, data, params }
    return `req_${btoa(JSON.stringify(keyData)).slice(0, 20)}`
  }

  /**
   * 生成缓存键
   */
  private generateCacheKey(config: RequestConfig): string {
    return `api_cache_${this.generateRequestKey(config)}`
  }

  /**
   * 更新平均响应时间
   */
  private updateAverageTime(duration: number): void {
    const total = this.requestStats.completed + this.requestStats.failed
    const currentAverage = this.requestStats.averageTime
    
    this.requestStats.averageTime = 
      (currentAverage * (total - 1) + duration) / total
  }

  /**
   * 睡眠函数
   */
  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms))
  }

  /**
   * 取消请求
   */
  public cancelRequest(requestKey: string): void {
    // 取消防抖请求
    const debouncedReq = this.debouncedRequests.get(requestKey)
    if (debouncedReq) {
      clearTimeout(debouncedReq.timer)
      debouncedReq.reject(new Error('Request cancelled'))
      this.debouncedRequests.delete(requestKey)
    }

    // 取消合并请求
    this.mergeableRequests.forEach((requests, mergeKey) => {
      const index = requests.findIndex(r => r.id === requestKey)
      if (index !== -1) {
        const request = requests[index]
        request.reject(new Error('Request cancelled'))
        requests.splice(index, 1)
      }
    })
  }

  /**
   * 取消所有请求
   */
  public cancelAllRequests(): void {
    // 取消防抖请求
    this.debouncedRequests.forEach(req => {
      clearTimeout(req.timer)
      req.reject(new Error('All requests cancelled'))
    })
    this.debouncedRequests.clear()

    // 取消合并请求
    this.mergeableRequests.forEach(requests => {
      requests.forEach(req => {
        req.reject(new Error('All requests cancelled'))
      })
    })
    this.mergeableRequests.clear()

    // 清空队列
    this.requestQueue.forEach(queue => queue.length = 0)
  }

  /**
   * 获取统计信息
   */
  public getStats(): RequestStats {
    return { ...this.requestStats }
  }

  /**
   * 重置统计信息
   */
  public resetStats(): void {
    this.requestStats.total = 0
    this.requestStats.completed = 0
    this.requestStats.failed = 0
    this.requestStats.cached = 0
    this.requestStats.merged = 0
    this.requestStats.averageTime = 0
  }

  /**
   * 设置最大并发请求数
   */
  public setMaxConcurrentRequests(max: number): void {
    this.maxConcurrentRequests = Math.max(1, Math.min(max, 20))
  }

  /**
   * 获取网络状态
   */
  public getNetworkStatus(): 'online' | 'offline' | 'slow' {
    return this.requestStats.networkStatus
  }

  /**
   * 销毁优化器
   */
  public destroy(): void {
    if (this.batchProcessor) {
      clearInterval(this.batchProcessor)
      this.batchProcessor = null
    }

    this.cancelAllRequests()

    if (this.networkMonitor) {
      this.networkMonitor.removeEventListener('change', () => {})
    }
  }
}

// 导出单例实例
export const qlibRequestOptimizer = QlibRequestOptimizer.getInstance()

// 导出便捷方法
export const optimizedRequest = <T = any>(config: RequestConfig) => 
  qlibRequestOptimizer.request<T>(config)

export const batchRequest = (config: BatchRequestConfig) => 
  qlibRequestOptimizer.batchRequest(config)

export const getRequestStats = () => 
  qlibRequestOptimizer.getStats()

export const cancelRequest = (requestKey: string) => 
  qlibRequestOptimizer.cancelRequest(requestKey)

export default QlibRequestOptimizer