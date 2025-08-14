/**
 * Qlib分页加载和懒加载服务
 * 
 * 此服务实现了qlib回测结果的分页加载和懒加载机制，包括：
 * - 智能分页策略和虚拟滚动
 * - 懒加载和预加载优化
 * - 数据流式加载和缓存管理
 * - 无限滚动和性能监控
 * - 自适应加载策略
 * 
 * 修改理由：
 * 1. 实现TODO 7.2.7节中回测结果分页加载需求
 * 2. 处理大量回测数据的高效展示问题
 * 3. 提供流畅的用户滚动体验
 * 4. 减少内存占用和提升页面性能
 * 5. 支持复杂数据结构的分页展示
 */

import { ref, computed, reactive, watch } from 'vue'
import { qlibIntelligentCache } from './qlib-intelligent-cache'

// 分页配置接口
export interface PaginationConfig {
  pageSize: number
  initialPage: number
  prefetchPages: number
  maxCachedPages: number
  loadingThreshold: number
  virtualScrolling: boolean
  autoLoad: boolean
  sortBy?: string
  sortOrder?: 'asc' | 'desc'
  filters?: Record<string, any>
}

// 分页状态接口
export interface PaginationState {
  currentPage: number
  totalPages: number
  totalItems: number
  hasMore: boolean
  loading: boolean
  error: string | null
  loadedPages: Set<number>
  visibleRange: { start: number; end: number }
}

// 数据项接口
export interface DataItem {
  id: string
  [key: string]: any
}

// 分页响应接口
export interface PaginatedResponse<T = DataItem> {
  data: T[]
  pagination: {
    page: number
    pageSize: number
    total: number
    totalPages: number
    hasNext: boolean
    hasPrevious: boolean
  }
  metadata?: {
    loadTime: number
    cacheHit: boolean
    source: string
    version: string
  }
}

// 加载策略枚举
export enum LoadingStrategy {
  ON_DEMAND = 'on_demand',        // 按需加载
  PREDICTIVE = 'predictive',      // 预测性加载
  AGGRESSIVE = 'aggressive',      // 积极加载
  CONSERVATIVE = 'conservative'   // 保守加载
}

// 数据源接口
export interface DataSource<T = DataItem> {
  fetchPage(page: number, pageSize: number, options?: any): Promise<PaginatedResponse<T>>
  getTotal(filters?: Record<string, any>): Promise<number>
  invalidateCache?(): void
}

/**
 * Qlib分页加载管理器
 */
export class QlibPaginationLoader<T = DataItem> {
  private dataSource: DataSource<T>
  private config: PaginationConfig
  private state: PaginationState
  private dataCache: Map<number, T[]> = new Map()
  private loadingPromises: Map<number, Promise<PaginatedResponse<T>>> = new Map()
  private intersectionObserver: IntersectionObserver | null = null
  private performanceMetrics: {
    loadTimes: number[]
    cacheHitRatio: number
    totalRequests: number
    cacheHits: number
  }

  constructor(
    dataSource: DataSource<T>,
    config: Partial<PaginationConfig> = {}
  ) {
    this.dataSource = dataSource
    this.config = {
      pageSize: 20,
      initialPage: 1,
      prefetchPages: 2,
      maxCachedPages: 10,
      loadingThreshold: 0.8,
      virtualScrolling: false,
      autoLoad: true,
      ...config
    }

    this.state = reactive({
      currentPage: this.config.initialPage,
      totalPages: 0,
      totalItems: 0,
      hasMore: true,
      loading: false,
      error: null,
      loadedPages: new Set(),
      visibleRange: { start: 0, end: this.config.pageSize }
    })

    this.performanceMetrics = {
      loadTimes: [],
      cacheHitRatio: 0,
      totalRequests: 0,
      cacheHits: 0
    }

    this.initializeIntersectionObserver()
  }

  /**
   * 初始化交叉观察器用于懒加载
   */
  private initializeIntersectionObserver(): void {
    if (typeof IntersectionObserver !== 'undefined') {
      this.intersectionObserver = new IntersectionObserver(
        (entries) => {
          entries.forEach((entry) => {
            if (entry.isIntersecting) {
              const pageNumber = parseInt(entry.target.getAttribute('data-page') || '0')
              if (pageNumber > 0) {
                this.loadPage(pageNumber)
              }
            }
          })
        },
        {
          rootMargin: '100px',
          threshold: 0.1
        }
      )
    }
  }

  /**
   * 加载指定页面
   */
  public async loadPage(page: number, options?: {
    force?: boolean
    silent?: boolean
    strategy?: LoadingStrategy
  }): Promise<T[]> {
    const opts = {
      force: false,
      silent: false,
      strategy: LoadingStrategy.ON_DEMAND,
      ...options
    }

    // 检查缓存
    if (!opts.force && this.dataCache.has(page)) {
      this.performanceMetrics.cacheHits++
      this.updateCacheHitRatio()
      return this.dataCache.get(page)!
    }

    // 检查是否已在加载中
    if (this.loadingPromises.has(page)) {
      return (await this.loadingPromises.get(page)!).data
    }

    // 设置加载状态
    if (!opts.silent) {
      this.state.loading = true
      this.state.error = null
    }

    const loadStartTime = performance.now()

    try {
      // 创建加载Promise
      const loadPromise = this.executePageLoad(page)
      this.loadingPromises.set(page, loadPromise)

      const response = await loadPromise

      // 更新状态
      this.updateStateFromResponse(response, page)

      // 缓存数据
      this.cachePageData(page, response.data)

      // 记录加载性能
      const loadTime = performance.now() - loadStartTime
      this.recordLoadTime(loadTime)

      // 清理加载Promise
      this.loadingPromises.delete(page)

      // 触发预加载
      if (opts.strategy !== LoadingStrategy.CONSERVATIVE) {
        this.triggerPrefetch(page, opts.strategy)
      }

      return response.data

    } catch (error) {
      this.state.error = error instanceof Error ? error.message : '数据加载失败'
      this.state.loading = false
      this.loadingPromises.delete(page)
      throw error
    } finally {
      if (!opts.silent) {
        this.state.loading = false
      }
    }
  }

  /**
   * 加载下一页
   */
  public async loadNext(): Promise<T[]> {
    if (!this.state.hasMore) {
      throw new Error('没有更多数据')
    }

    const nextPage = this.state.currentPage + 1
    const data = await this.loadPage(nextPage)
    this.state.currentPage = nextPage

    return data
  }

  /**
   * 加载上一页
   */
  public async loadPrevious(): Promise<T[]> {
    if (this.state.currentPage <= 1) {
      throw new Error('已经是第一页')
    }

    const prevPage = this.state.currentPage - 1
    const data = await this.loadPage(prevPage)
    this.state.currentPage = prevPage

    return data
  }

  /**
   * 跳转到指定页面
   */
  public async goToPage(page: number): Promise<T[]> {
    if (page < 1 || (this.state.totalPages > 0 && page > this.state.totalPages)) {
      throw new Error('页码超出范围')
    }

    const data = await this.loadPage(page, { strategy: LoadingStrategy.PREDICTIVE })
    this.state.currentPage = page

    return data
  }

  /**
   * 重新加载当前页
   */
  public async reload(): Promise<T[]> {
    // 清除缓存
    this.dataCache.delete(this.state.currentPage)
    this.state.loadedPages.delete(this.state.currentPage)

    return this.loadPage(this.state.currentPage, { force: true })
  }

  /**
   * 刷新所有数据
   */
  public async refresh(): Promise<void> {
    // 清除所有缓存
    this.clearCache()
    this.state.loadedPages.clear()

    // 重新加载当前页
    await this.loadPage(this.state.currentPage, { force: true })
  }

  /**
   * 获取指定页面的数据
   */
  public getPageData(page: number): T[] | null {
    return this.dataCache.get(page) || null
  }

  /**
   * 获取所有已加载的数据
   */
  public getAllLoadedData(): T[] {
    const allData: T[] = []
    const sortedPages = Array.from(this.state.loadedPages).sort((a, b) => a - b)
    
    for (const page of sortedPages) {
      const pageData = this.dataCache.get(page)
      if (pageData) {
        allData.push(...pageData)
      }
    }

    return allData
  }

  /**
   * 获取可见范围内的数据
   */
  public getVisibleData(): T[] {
    const { start, end } = this.state.visibleRange
    const allData = this.getAllLoadedData()
    return allData.slice(start, end)
  }

  /**
   * 更新可见范围
   */
  public updateVisibleRange(start: number, end: number): void {
    this.state.visibleRange = { start, end }

    // 计算需要加载的页面
    const startPage = Math.floor(start / this.config.pageSize) + 1
    const endPage = Math.floor(end / this.config.pageSize) + 1

    // 懒加载需要的页面
    for (let page = startPage; page <= endPage; page++) {
      if (!this.state.loadedPages.has(page)) {
        this.loadPage(page, { silent: true, strategy: LoadingStrategy.ON_DEMAND })
      }
    }
  }

  /**
   * 注册懒加载元素
   */
  public observeElement(element: Element, page: number): void {
    if (this.intersectionObserver) {
      element.setAttribute('data-page', page.toString())
      this.intersectionObserver.observe(element)
    }
  }

  /**
   * 注销懒加载元素
   */
  public unobserveElement(element: Element): void {
    if (this.intersectionObserver) {
      this.intersectionObserver.unobserve(element)
    }
  }

  /**
   * 设置过滤器
   */
  public async setFilters(filters: Record<string, any>): Promise<void> {
    this.config.filters = filters
    await this.refresh()
  }

  /**
   * 设置排序
   */
  public async setSorting(sortBy: string, sortOrder: 'asc' | 'desc' = 'asc'): Promise<void> {
    this.config.sortBy = sortBy
    this.config.sortOrder = sortOrder
    await this.refresh()
  }

  /**
   * 获取性能指标
   */
  public getPerformanceMetrics(): {
    averageLoadTime: number
    cacheHitRatio: number
    totalRequests: number
    memoryUsage: string
  } {
    const averageLoadTime = this.performanceMetrics.loadTimes.length > 0
      ? this.performanceMetrics.loadTimes.reduce((a, b) => a + b, 0) / this.performanceMetrics.loadTimes.length
      : 0

    const memoryUsage = this.estimateMemoryUsage()

    return {
      averageLoadTime,
      cacheHitRatio: this.performanceMetrics.cacheHitRatio,
      totalRequests: this.performanceMetrics.totalRequests,
      memoryUsage
    }
  }

  /**
   * 获取当前状态
   */
  public getState(): PaginationState {
    return { ...this.state }
  }

  /**
   * 获取配置
   */
  public getConfig(): PaginationConfig {
    return { ...this.config }
  }

  /**
   * 更新配置
   */
  public updateConfig(newConfig: Partial<PaginationConfig>): void {
    Object.assign(this.config, newConfig)
    
    // 如果页面大小改变，需要重新加载
    if (newConfig.pageSize) {
      this.refresh()
    }
  }

  // 私有方法实现

  private async executePageLoad(page: number): Promise<PaginatedResponse<T>> {
    this.performanceMetrics.totalRequests++

    // 构建请求选项
    const options = {
      sortBy: this.config.sortBy,
      sortOrder: this.config.sortOrder,
      filters: this.config.filters
    }

    // 执行数据获取
    const response = await this.dataSource.fetchPage(page, this.config.pageSize, options)

    // 验证响应
    if (!response || !Array.isArray(response.data)) {
      throw new Error('无效的响应格式')
    }

    return response
  }

  private updateStateFromResponse(response: PaginatedResponse<T>, page: number): void {
    this.state.totalItems = response.pagination.total
    this.state.totalPages = response.pagination.totalPages
    this.state.hasMore = response.pagination.hasNext
    this.state.loadedPages.add(page)
  }

  private cachePageData(page: number, data: T[]): void {
    // 检查缓存大小限制
    if (this.dataCache.size >= this.config.maxCachedPages) {
      this.evictOldestCachePage()
    }

    this.dataCache.set(page, data)

    // 同时缓存到智能缓存系统
    const cacheKey = this.generateCacheKey(page)
    qlibIntelligentCache.set(
      cacheKey,
      data,
      {
        ttl: 30 * 60 * 1000, // 30分钟
        tags: ['pagination', 'backtest_results'],
        priority: this.calculateCachePriority(page)
      }
    )
  }

  private evictOldestCachePage(): void {
    // 移除最旧的缓存页面
    const oldestPage = Math.min(...this.dataCache.keys())
    this.dataCache.delete(oldestPage)
    this.state.loadedPages.delete(oldestPage)

    // 从智能缓存中移除
    const cacheKey = this.generateCacheKey(oldestPage)
    qlibIntelligentCache.delete(cacheKey)
  }

  private async triggerPrefetch(currentPage: number, strategy: LoadingStrategy): Promise<void> {
    const prefetchCount = this.calculatePrefetchCount(strategy)
    const pagesToPrefetch: number[] = []

    // 确定预加载页面
    for (let i = 1; i <= prefetchCount; i++) {
      const nextPage = currentPage + i
      const prevPage = currentPage - i

      if (nextPage <= this.state.totalPages && !this.state.loadedPages.has(nextPage)) {
        pagesToPrefetch.push(nextPage)
      }
      
      if (prevPage >= 1 && !this.state.loadedPages.has(prevPage)) {
        pagesToPrefetch.push(prevPage)
      }
    }

    // 异步预加载
    pagesToPrefetch.forEach(page => {
      setTimeout(() => {
        if (!this.state.loadedPages.has(page)) {
          this.loadPage(page, { silent: true, strategy: LoadingStrategy.CONSERVATIVE })
        }
      }, 100)
    })
  }

  private calculatePrefetchCount(strategy: LoadingStrategy): number {
    switch (strategy) {
      case LoadingStrategy.AGGRESSIVE:
        return this.config.prefetchPages * 2
      case LoadingStrategy.PREDICTIVE:
        return this.config.prefetchPages
      case LoadingStrategy.ON_DEMAND:
        return Math.ceil(this.config.prefetchPages / 2)
      case LoadingStrategy.CONSERVATIVE:
        return 0
      default:
        return this.config.prefetchPages
    }
  }

  private calculateCachePriority(page: number): number {
    const distanceFromCurrent = Math.abs(page - this.state.currentPage)
    return Math.max(1, 10 - distanceFromCurrent)
  }

  private generateCacheKey(page: number): string {
    const filters = JSON.stringify(this.config.filters || {})
    const sorting = `${this.config.sortBy}_${this.config.sortOrder}`
    return `pagination_${page}_${this.config.pageSize}_${sorting}_${btoa(filters).slice(0, 10)}`
  }

  private recordLoadTime(loadTime: number): void {
    this.performanceMetrics.loadTimes.push(loadTime)
    
    // 只保留最近100次的记录
    if (this.performanceMetrics.loadTimes.length > 100) {
      this.performanceMetrics.loadTimes.shift()
    }
  }

  private updateCacheHitRatio(): void {
    this.performanceMetrics.cacheHitRatio = 
      this.performanceMetrics.cacheHits / this.performanceMetrics.totalRequests
  }

  private estimateMemoryUsage(): string {
    let totalSize = 0
    
    this.dataCache.forEach(pageData => {
      totalSize += JSON.stringify(pageData).length
    })

    const sizeInMB = totalSize / (1024 * 1024)
    return `${sizeInMB.toFixed(2)} MB`
  }

  private clearCache(): void {
    this.dataCache.clear()
    
    // 清理智能缓存中的分页数据
    qlibIntelligentCache.clear({ tags: ['pagination'] })
  }

  /**
   * 销毁分页加载器
   */
  public destroy(): void {
    // 断开交叉观察器
    if (this.intersectionObserver) {
      this.intersectionObserver.disconnect()
      this.intersectionObserver = null
    }

    // 清理缓存
    this.clearCache()

    // 取消所有进行中的加载
    this.loadingPromises.clear()

    console.log('分页加载器已销毁')
  }
}

/**
 * 创建分页加载器的便捷函数
 */
export function createPaginationLoader<T = DataItem>(
  dataSource: DataSource<T>,
  config?: Partial<PaginationConfig>
): QlibPaginationLoader<T> {
  return new QlibPaginationLoader<T>(dataSource, config)
}

/**
 * 创建回测结果数据源
 */
export class BacktestResultDataSource implements DataSource<any> {
  private baseUrl: string

  constructor(baseUrl: string = '/api/v1/backtest-results') {
    this.baseUrl = baseUrl
  }

  async fetchPage(page: number, pageSize: number, options?: any): Promise<PaginatedResponse<any>> {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString(),
      ...(options?.filters || {}),
      ...(options?.sortBy && { sort_by: options.sortBy }),
      ...(options?.sortOrder && { sort_order: options.sortOrder })
    })

    const response = await fetch(`${this.baseUrl}?${params}`)
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`)
    }

    const data = await response.json()
    
    return {
      data: data.results || data.data || [],
      pagination: {
        page,
        pageSize,
        total: data.total || data.count || 0,
        totalPages: Math.ceil((data.total || data.count || 0) / pageSize),
        hasNext: data.has_next || false,
        hasPrevious: data.has_previous || false
      },
      metadata: {
        loadTime: Date.now(),
        cacheHit: false,
        source: 'api',
        version: '1.0'
      }
    }
  }

  async getTotal(filters?: Record<string, any>): Promise<number> {
    const params = new URLSearchParams({
      count_only: 'true',
      ...(filters || {})
    })

    const response = await fetch(`${this.baseUrl}?${params}`)
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`)
    }

    const data = await response.json()
    return data.total || data.count || 0
  }

  invalidateCache(): void {
    qlibIntelligentCache.clear({ tags: ['backtest_results'] })
  }
}

/**
 * Vue Composition API 钩子
 */
export function usePagination<T = DataItem>(
  dataSource: DataSource<T>,
  config?: Partial<PaginationConfig>
) {
  const loader = new QlibPaginationLoader<T>(dataSource, config)
  
  const currentPage = computed(() => loader.getState().currentPage)
  const totalPages = computed(() => loader.getState().totalPages)
  const totalItems = computed(() => loader.getState().totalItems)
  const hasMore = computed(() => loader.getState().hasMore)
  const loading = computed(() => loader.getState().loading)
  const error = computed(() => loader.getState().error)

  const loadPage = (page: number, options?: any) => loader.loadPage(page, options)
  const loadNext = () => loader.loadNext()
  const loadPrevious = () => loader.loadPrevious()
  const goToPage = (page: number) => loader.goToPage(page)
  const reload = () => loader.reload()
  const refresh = () => loader.refresh()

  const getAllData = () => loader.getAllLoadedData()
  const getVisibleData = () => loader.getVisibleData()
  const getPerformanceMetrics = () => loader.getPerformanceMetrics()

  return {
    // 状态
    currentPage,
    totalPages,
    totalItems,
    hasMore,
    loading,
    error,
    
    // 方法
    loadPage,
    loadNext,
    loadPrevious,
    goToPage,
    reload,
    refresh,
    getAllData,
    getVisibleData,
    getPerformanceMetrics,
    
    // 原始加载器引用
    loader
  }
}

export default QlibPaginationLoader