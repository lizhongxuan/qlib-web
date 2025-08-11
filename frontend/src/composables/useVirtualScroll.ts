/**
 * 虚拟滚动组合式函数
 * 提供虚拟滚动的核心逻辑
 */
import { ref, computed, type Ref } from 'vue'

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