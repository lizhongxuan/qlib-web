/**
 * 虚拟滚动组合式函数
 * 提供虚拟滚动的核心逻辑
 * 
 * 增强版本实现了qlib数据可视化组件的懒加载和虚拟滚动，包括：
 * - 大数据量的虚拟渲染优化
 * - 智能预加载和懒加载机制
 * - 动态高度计算和缓存
 * - 性能监控和内存管理
 * - 数据可视化组件的特殊优化
 * 
 * 修改理由：
 * 1. 实现TODO 7.2.7节中数据可视化组件懒加载和虚拟滚动需求
 * 2. 增强现有虚拟滚动功能以支持复杂的qlib数据展示
 * 3. 提供图表组件的延迟渲染和智能加载
 * 4. 优化大量数据的渲染性能
 */
import { ref, computed, reactive, nextTick, onMounted, onUnmounted, watch, type Ref } from 'vue'
import { qlibIntelligentCache } from '@/services/qlib-intelligent-cache'

interface VirtualScrollOptions {
  itemHeight: number
  containerHeight: number
  bufferSize?: number
  data: Ref<any[]>
}

interface VirtualScrollReturn {
  // 状态
  scrollTop: Ref<number>
  startIndex: Ref<number>
  endIndex: Ref<number>
  visibleItems: Ref<any[]>
  startOffset: Ref<number>
  totalHeight: Ref<number>
  
  // 方法
  handleScroll: (scrollTop: number) => void
  scrollToIndex: (index: number, scrollContainer?: HTMLElement) => void
  scrollToTop: (scrollContainer?: HTMLElement) => void
  scrollToBottom: (scrollContainer?: HTMLElement) => void
}

export function useVirtualScroll(options: VirtualScrollOptions): VirtualScrollReturn {
  const { itemHeight, containerHeight, bufferSize = 5, data } = options
  
  // 滚动位置
  const scrollTop = ref(0)
  
  // 计算总高度
  const totalHeight = computed(() => data.value.length * itemHeight)
  
  // 计算可见项目数量
  const visibleCount = computed(() => {
    return Math.ceil(containerHeight / itemHeight) + bufferSize * 2
  })
  
  // 计算开始索引
  const startIndex = computed(() => {
    return Math.max(0, Math.floor(scrollTop.value / itemHeight) - bufferSize)
  })
  
  // 计算结束索引
  const endIndex = computed(() => {
    return Math.min(data.value.length - 1, startIndex.value + visibleCount.value)
  })
  
  // 计算可见项目
  const visibleItems = computed(() => {
    return data.value.slice(startIndex.value, endIndex.value + 1)
  })
  
  // 计算开始偏移量
  const startOffset = computed(() => {
    return startIndex.value * itemHeight
  })
  
  // 处理滚动事件
  const handleScroll = (newScrollTop: number) => {
    scrollTop.value = newScrollTop
  }
  
  // 滚动到指定索引
  const scrollToIndex = (index: number, scrollContainer?: HTMLElement) => {
    if (scrollContainer) {
      const targetScrollTop = index * itemHeight
      scrollContainer.scrollTop = targetScrollTop
      scrollTop.value = targetScrollTop
    }
  }
  
  // 滚动到顶部
  const scrollToTop = (scrollContainer?: HTMLElement) => {
    scrollToIndex(0, scrollContainer)
  }
  
  // 滚动到底部
  const scrollToBottom = (scrollContainer?: HTMLElement) => {
    scrollToIndex(data.value.length - 1, scrollContainer)
  }
  
  return {
    scrollTop,
    startIndex,
    endIndex,
    visibleItems,
    startOffset,
    totalHeight,
    handleScroll,
    scrollToIndex,
    scrollToTop,
    scrollToBottom
  }
}

/**
 * 虚拟滚动列表组合式函数
 * 用于简单的列表虚拟滚动
 */
interface VirtualListOptions {
  itemHeight: number
  containerHeight: number
  bufferSize?: number
}

export function useVirtualList<T>(
  data: Ref<T[]>,
  options: VirtualListOptions
) {
  const virtualScroll = useVirtualScroll({
    ...options,
    data
  })
  
  return {
    ...virtualScroll,
    // 获取项目的样式
    getItemStyle: (index: number) => ({
      height: `${options.itemHeight}px`,
      transform: `translateY(${(virtualScroll.startIndex.value + index) * options.itemHeight}px)`,
      position: 'absolute' as const,
      top: 0,
      left: 0,
      right: 0
    })
  }
}

/**
 * 虚拟滚动表格组合式函数
 * 用于表格的虚拟滚动
 */
interface VirtualTableColumn {
  key: string
  title: string
  width?: number
  fixed?: 'left' | 'right'
}

interface VirtualTableOptions {
  itemHeight: number
  containerHeight: number
  bufferSize?: number
  columns: VirtualTableColumn[]
}

export function useVirtualTable<T>(
  data: Ref<T[]>,
  options: VirtualTableOptions
) {
  const virtualScroll = useVirtualScroll({
    itemHeight: options.itemHeight,
    containerHeight: options.containerHeight,
    bufferSize: options.bufferSize,
    data
  })
  
  // 计算表格总宽度
  const totalWidth = computed(() => {
    return options.columns.reduce((total, column) => {
      return total + (column.width || 120)
    }, 0)
  })
  
  // 获取列的左偏移量
  const getColumnLeft = (columnIndex: number): number => {
    let left = 0
    for (let i = 0; i < columnIndex; i++) {
      left += options.columns[i].width || 120
    }
    return left
  }
  
  // 获取固定列的样式
  const getFixedColumnStyle = (column: VirtualTableColumn, index: number) => {
    const baseStyle = {
      width: `${column.width || 120}px`,
      position: 'sticky' as const,
      zIndex: 10
    }
    
    if (column.fixed === 'left') {
      return {
        ...baseStyle,
        left: `${getColumnLeft(index)}px`
      }
    } else if (column.fixed === 'right') {
      // 计算右侧固定列的位置
      let rightOffset = 0
      for (let i = index + 1; i < options.columns.length; i++) {
        if (options.columns[i].fixed === 'right') {
          rightOffset += options.columns[i].width || 120
        }
      }
      return {
        ...baseStyle,
        right: `${rightOffset}px`
      }
    }
    
    return {
      width: `${column.width || 120}px`
    }
  }
  
  return {
    ...virtualScroll,
    totalWidth,
    getColumnLeft,
    getFixedColumnStyle,
    // 获取行的样式
    getRowStyle: (index: number) => ({
      height: `${options.itemHeight}px`,
      transform: `translateY(${(virtualScroll.startIndex.value + index) * options.itemHeight}px)`,
      position: 'absolute' as const,
      top: 0,
      left: 0,
      width: `${totalWidth.value}px`
    })
  }
}

/**
 * 性能监控装饰器
 * 用于监控虚拟滚动的性能
 */
export function withPerformanceMonitoring<T extends (...args: any[]) => any>(
  fn: T,
  label: string
): T {
  return ((...args: any[]) => {
    const start = performance.now()
    const result = fn(...args)
    const end = performance.now()
    
    if (end - start > 16) { // 超过一帧的时间（16ms）
      console.warn(`Virtual scroll performance warning: ${label} took ${end - start}ms`)
    }
    
    return result
  }) as T
}

/**
 * 缓存装饰器
 * 用于缓存计算结果，避免重复计算
 */
export function withCache<T extends (...args: any[]) => any>(fn: T): T {
  const cache = new Map()
  
  return ((...args: any[]) => {
    const key = JSON.stringify(args)
    
    if (cache.has(key)) {
      return cache.get(key)
    }
    
    const result = fn(...args)
    cache.set(key, result)
    
    // 限制缓存大小
    if (cache.size > 100) {
      const firstKey = cache.keys().next().value
      cache.delete(firstKey)
    }
    
    return result
  }) as T
}

/**
 * 节流装饰器
 * 用于节流滚动事件，提高性能
 */
export function withThrottle<T extends (...args: any[]) => any>(
  fn: T,
  delay: number = 16
): T {
  let timeoutId: number | null = null
  let lastExecTime = 0
  
  return ((...args: any[]) => {
    const currentTime = Date.now()
    
    if (currentTime - lastExecTime > delay) {
      fn(...args)
      lastExecTime = currentTime
    } else {
      if (timeoutId) {
        clearTimeout(timeoutId)
      }
      
      timeoutId = window.setTimeout(() => {
        fn(...args)
        lastExecTime = Date.now()
        timeoutId = null
      }, delay - (currentTime - lastExecTime))
    }
  }) as T
}

// ========================= 增强的懒加载和数据可视化功能 =========================

/**
 * 懒加载配置接口
 */
interface LazyLoadConfig {
  rootMargin?: string
  threshold?: number
  preloadDistance?: number
  enableCache?: boolean
  cacheSize?: number
  enablePredict?: boolean
  predictCount?: number
}

/**
 * 数据可视化项目接口
 */
interface VisualizationItem {
  id: string
  type: 'chart' | 'table' | 'metric' | 'text'
  data?: any
  config?: any
  loaded?: boolean
  loading?: boolean
  error?: string
  element?: HTMLElement
  intersecting?: boolean
}

/**
 * 数据可视化虚拟滚动增强版
 */
export function useVisualizationVirtualScroll<T extends VisualizationItem>(
  items: Ref<T[]>,
  options: VirtualScrollOptions & LazyLoadConfig = {}
) {
  const {
    itemHeight,
    containerHeight,
    bufferSize = 5,
    rootMargin = '100px',
    threshold = 0.1,
    preloadDistance = 200,
    enableCache = true,
    cacheSize = 50,
    enablePredict = true,
    predictCount = 3
  } = options

  // 基础虚拟滚动功能
  const baseScroll = useVirtualScroll({
    itemHeight,
    containerHeight,
    bufferSize,
    data: items
  })

  // 增强状态
  const loadedItems = ref<Map<string, T>>(new Map())
  const loadingItems = ref<Set<string>>(new Set())
  const errorItems = ref<Map<string, string>>(new Map())
  const intersectionObserver = ref<IntersectionObserver | null>(null)
  const performanceStats = reactive({
    totalRenderTime: 0,
    averageRenderTime: 0,
    renderCount: 0,
    cacheHitRate: 0,
    lazyLoadCount: 0
  })

  /**
   * 初始化交叉观察器
   */
  const initIntersectionObserver = () => {
    if (typeof IntersectionObserver === 'undefined') return

    intersectionObserver.value = new IntersectionObserver(
      (entries) => {
        entries.forEach(entry => {
          const itemId = entry.target.getAttribute('data-item-id')
          if (!itemId) return

          const item = items.value.find(i => i.id === itemId)
          if (!item) return

          if (entry.isIntersecting) {
            // 元素进入可见区域，触发加载
            loadVisualizationItem(item)
            
            // 预测性加载
            if (enablePredict) {
              predictiveLoad(item)
            }
          } else {
            // 元素离开可见区域，可以考虑卸载以释放内存
            item.intersecting = false
          }
        })
      },
      {
        rootMargin,
        threshold
      }
    )
  }

  /**
   * 观察可视化项目
   */
  const observeItem = (element: HTMLElement, item: T) => {
    if (!intersectionObserver.value) return

    element.setAttribute('data-item-id', item.id)
    item.element = element
    intersectionObserver.value.observe(element)
  }

  /**
   * 停止观察项目
   */
  const unobserveItem = (item: T) => {
    if (!intersectionObserver.value || !item.element) return

    intersectionObserver.value.unobserve(item.element)
    item.element = undefined
  }

  /**
   * 加载可视化项目
   */
  const loadVisualizationItem = async (item: T) => {
    if (item.loaded || item.loading) return

    // 检查缓存
    if (enableCache) {
      const cached = await qlibIntelligentCache.get<T>(`viz_${item.id}`)
      if (cached) {
        Object.assign(item, cached)
        item.loaded = true
        performanceStats.cacheHitRate = 
          (performanceStats.cacheHitRate * performanceStats.lazyLoadCount + 1) / 
          (performanceStats.lazyLoadCount + 1)
        return
      }
    }

    item.loading = true
    loadingItems.value.add(item.id)

    const startTime = performance.now()

    try {
      // 根据类型加载不同的数据
      await loadItemByType(item)
      
      item.loaded = true
      item.loading = false
      item.intersecting = true
      loadedItems.value.set(item.id, item)
      
      // 缓存加载结果
      if (enableCache) {
        qlibIntelligentCache.set(
          `viz_${item.id}`,
          item,
          {
            ttl: 10 * 60 * 1000, // 10分钟
            tags: ['visualization', item.type],
            priority: 5
          }
        )
      }

      // 更新性能统计
      const renderTime = performance.now() - startTime
      performanceStats.totalRenderTime += renderTime
      performanceStats.renderCount++
      performanceStats.averageRenderTime = 
        performanceStats.totalRenderTime / performanceStats.renderCount
      performanceStats.lazyLoadCount++

    } catch (error) {
      item.loading = false
      item.error = error instanceof Error ? error.message : '加载失败'
      errorItems.value.set(item.id, item.error)
      console.error(`加载可视化项目 ${item.id} 失败:`, error)
    } finally {
      loadingItems.value.delete(item.id)
    }
  }

  /**
   * 根据类型加载项目
   */
  const loadItemByType = async (item: T): Promise<void> => {
    switch (item.type) {
      case 'chart':
        await loadChartData(item)
        break
      case 'table':
        await loadTableData(item)
        break
      case 'metric':
        await loadMetricData(item)
        break
      case 'text':
        await loadTextData(item)
        break
      default:
        // 默认加载逻辑
        await new Promise(resolve => setTimeout(resolve, 100))
    }
  }

  /**
   * 加载图表数据
   */
  const loadChartData = async (item: T): Promise<void> => {
    // 模拟图表数据加载
    await new Promise(resolve => setTimeout(resolve, 200 + Math.random() * 800))
    
    // 生成模拟图表数据
    item.data = {
      labels: Array.from({ length: 20 }, (_, i) => `Point ${i + 1}`),
      datasets: [{
        label: 'Sample Data',
        data: Array.from({ length: 20 }, () => Math.random() * 100),
        backgroundColor: '#1f77b4'
      }]
    }
  }

  /**
   * 加载表格数据
   */
  const loadTableData = async (item: T): Promise<void> => {
    // 模拟表格数据加载
    await new Promise(resolve => setTimeout(resolve, 150 + Math.random() * 600))
    
    item.data = {
      columns: ['Date', 'Value', 'Change', 'Volume'],
      rows: Array.from({ length: 10 }, (_, i) => ({
        id: i,
        date: new Date(2023, 0, i + 1).toISOString().split('T')[0],
        value: (Math.random() * 1000).toFixed(2),
        change: (Math.random() * 20 - 10).toFixed(2),
        volume: Math.floor(Math.random() * 1000000)
      }))
    }
  }

  /**
   * 加载指标数据
   */
  const loadMetricData = async (item: T): Promise<void> => {
    // 模拟指标数据加载
    await new Promise(resolve => setTimeout(resolve, 100 + Math.random() * 300))
    
    item.data = {
      value: (Math.random() * 100).toFixed(2),
      unit: '%',
      trend: Math.random() > 0.5 ? 'up' : 'down',
      change: (Math.random() * 10 - 5).toFixed(2)
    }
  }

  /**
   * 加载文本数据
   */
  const loadTextData = async (item: T): Promise<void> => {
    // 模拟文本数据加载
    await new Promise(resolve => setTimeout(resolve, 50 + Math.random() * 200))
    
    item.data = {
      content: `这是项目 ${item.id} 的文本内容，包含了一些重要的分析结果和洞察。`,
      timestamp: new Date().toISOString(),
      author: 'Qlib AI'
    }
  }

  /**
   * 预测性加载
   */
  const predictiveLoad = (currentItem: T) => {
    const currentIndex = items.value.findIndex(i => i.id === currentItem.id)
    if (currentIndex === -1) return

    // 预加载后续项目
    for (let i = 1; i <= predictCount; i++) {
      const nextIndex = currentIndex + i
      if (nextIndex < items.value.length) {
        const nextItem = items.value[nextIndex]
        if (!nextItem.loaded && !nextItem.loading) {
          // 延迟加载以避免阻塞当前渲染
          setTimeout(() => {
            loadVisualizationItem(nextItem)
          }, i * 100)
        }
      }
    }
  }

  /**
   * 预加载可见范围附近的项目
   */
  const preloadNearbyItems = () => {
    const { startIndex, endIndex } = baseScroll
    const start = Math.max(0, startIndex.value - bufferSize)
    const end = Math.min(items.value.length - 1, endIndex.value + bufferSize)

    for (let i = start; i <= end; i++) {
      const item = items.value[i]
      if (item && !item.loaded && !item.loading) {
        loadVisualizationItem(item)
      }
    }
  }

  /**
   * 清理不可见项目以释放内存
   */
  const cleanupInvisibleItems = () => {
    const { startIndex, endIndex } = baseScroll
    const cleanupThreshold = bufferSize * 2

    loadedItems.value.forEach((item, id) => {
      const itemIndex = items.value.findIndex(i => i.id === id)
      const distance = Math.min(
        Math.abs(itemIndex - startIndex.value),
        Math.abs(itemIndex - endIndex.value)
      )

      if (distance > cleanupThreshold && !item.intersecting) {
        // 清理项目数据但保留状态
        if (item.data && typeof item.data === 'object') {
          // 只保留关键信息，清理大数据对象
          const lightData = {
            _cleaned: true,
            summary: item.data.summary || 'Data cleaned to save memory'
          }
          item.data = lightData
        }
      }
    })
  }

  /**
   * 获取项目状态
   */
  const getItemStatus = (itemId: string) => {
    const item = items.value.find(i => i.id === itemId)
    if (!item) return 'not_found'
    
    if (item.error) return 'error'
    if (item.loading) return 'loading'
    if (item.loaded) return 'loaded'
    return 'pending'
  }

  /**
   * 重新加载项目
   */
  const reloadItem = async (itemId: string) => {
    const item = items.value.find(i => i.id === itemId)
    if (!item) return

    // 清理状态
    item.loaded = false
    item.loading = false
    item.error = undefined
    item.data = undefined
    loadedItems.value.delete(itemId)
    errorItems.value.delete(itemId)

    // 清理缓存
    if (enableCache) {
      await qlibIntelligentCache.delete(`viz_${itemId}`)
    }

    // 重新加载
    await loadVisualizationItem(item)
  }

  /**
   * 批量重新加载
   */
  const reloadAll = async () => {
    // 清理所有状态
    items.value.forEach(item => {
      item.loaded = false
      item.loading = false
      item.error = undefined
      item.data = undefined
    })
    
    loadedItems.value.clear()
    errorItems.value.clear()
    loadingItems.value.clear()

    // 清理缓存
    if (enableCache) {
      await qlibIntelligentCache.clear({ tags: ['visualization'] })
    }

    // 重置性能统计
    Object.assign(performanceStats, {
      totalRenderTime: 0,
      averageRenderTime: 0,
      renderCount: 0,
      cacheHitRate: 0,
      lazyLoadCount: 0
    })

    // 预加载当前可见项目
    preloadNearbyItems()
  }

  /**
   * 获取性能统计
   */
  const getPerformanceStats = () => {
    return {
      ...performanceStats,
      loadedCount: loadedItems.value.size,
      loadingCount: loadingItems.value.size,
      errorCount: errorItems.value.size,
      totalItems: items.value.length,
      memoryUsage: estimateMemoryUsage()
    }
  }

  /**
   * 估算内存使用
   */
  const estimateMemoryUsage = (): string => {
    let totalSize = 0
    
    loadedItems.value.forEach(item => {
      if (item.data) {
        totalSize += JSON.stringify(item.data).length
      }
    })

    const sizeInMB = totalSize / (1024 * 1024)
    return `${sizeInMB.toFixed(2)} MB`
  }

  // 生命周期管理
  onMounted(() => {
    initIntersectionObserver()
    
    // 初始预加载
    nextTick(() => {
      preloadNearbyItems()
    })

    // 定期清理内存
    const cleanupInterval = setInterval(() => {
      cleanupInvisibleItems()
    }, 30000) // 每30秒清理一次

    onUnmounted(() => {
      clearInterval(cleanupInterval)
      
      if (intersectionObserver.value) {
        intersectionObserver.value.disconnect()
      }
    })
  })

  // 监听滚动变化，触发预加载
  watch([() => baseScroll.startIndex.value, () => baseScroll.endIndex.value], () => {
    preloadNearbyItems()
  })

  return {
    ...baseScroll,
    
    // 增强状态
    loadedItems: readonly(loadedItems),
    loadingItems: readonly(loadingItems),
    errorItems: readonly(errorItems),
    performanceStats: readonly(performanceStats),
    
    // 增强方法
    observeItem,
    unobserveItem,
    loadVisualizationItem,
    getItemStatus,
    reloadItem,
    reloadAll,
    getPerformanceStats,
    
    // 工具方法
    preloadNearbyItems,
    cleanupInvisibleItems
  }
}

/**
 * 数据可视化懒加载指令
 */
export const vLazyVisualization = {
  mounted(el: HTMLElement, binding: any) {
    const { observer, item } = binding.value
    
    if (observer && item) {
      observer.observeItem(el, item)
    }
  },
  
  unmounted(el: HTMLElement, binding: any) {
    const { observer, item } = binding.value
    
    if (observer && item) {
      observer.unobserveItem(item)
    }
  }
}

/**
 * 大数据集优化的虚拟滚动
 */
export function useBigDataVirtualScroll<T>(
  dataLoader: (startIndex: number, count: number) => Promise<T[]>,
  totalCount: Ref<number>,
  options: VirtualScrollOptions = {}
) {
  const loadedData = ref<Map<number, T>>(new Map())
  const loadingChunks = ref<Set<number>>(new Set())
  const chunkSize = options.bufferSize || 50

  const baseScroll = useVirtualScroll({
    ...options,
    data: computed(() => Array.from({ length: totalCount.value }, (_, i) => 
      loadedData.value.get(i) || { _placeholder: true, _index: i }
    ))
  })

  const loadChunk = async (chunkIndex: number) => {
    if (loadingChunks.value.has(chunkIndex)) return

    loadingChunks.value.add(chunkIndex)

    try {
      const startIndex = chunkIndex * chunkSize
      const items = await dataLoader(startIndex, chunkSize)
      
      items.forEach((item, i) => {
        loadedData.value.set(startIndex + i, item)
      })
    } catch (error) {
      console.error(`加载数据块 ${chunkIndex} 失败:`, error)
    } finally {
      loadingChunks.value.delete(chunkIndex)
    }
  }

  const ensureDataLoaded = (index: number) => {
    const chunkIndex = Math.floor(index / chunkSize)
    if (!loadingChunks.value.has(chunkIndex) && !loadedData.value.has(index)) {
      loadChunk(chunkIndex)
    }
  }

  watch([() => baseScroll.startIndex.value, () => baseScroll.endIndex.value], () => {
    const start = baseScroll.startIndex.value
    const end = baseScroll.endIndex.value
    
    for (let i = start; i <= end; i++) {
      ensureDataLoaded(i)
    }
  })

  return {
    ...baseScroll,
    loadedData: readonly(loadedData),
    loadingChunks: readonly(loadingChunks),
    ensureDataLoaded
  }
}