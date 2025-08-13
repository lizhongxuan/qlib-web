import { ref, reactive, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'

// 数据传递接口定义
interface TransferData {
  id: string
  type: 'factor' | 'model' | 'strategy' | 'experiment' | 'config'
  data: any
  source: string
  target?: string
  timestamp: number
  persistent?: boolean
  metadata?: Record<string, any>
}

interface TransferOptions {
  persistent?: boolean
  validation?: (data: any) => boolean
  transform?: (data: any) => any
  onSuccess?: (data: any) => void
  onError?: (error: Error) => void
}

// 全局数据传递存储
class DataTransferManager {
  private transfers = new Map<string, TransferData>()
  private subscribers = new Map<string, Set<(data: TransferData) => void>>()
  private history: TransferData[] = []

  // 存储数据
  store(id: string, type: TransferData['type'], data: any, options: TransferOptions = {}): void {
    const transferData: TransferData = {
      id,
      type,
      data: options.transform ? options.transform(data) : data,
      source: this.getCurrentRoute(),
      timestamp: Date.now(),
      persistent: options.persistent || false,
      metadata: {}
    }

    // 验证数据
    if (options.validation && !options.validation(transferData.data)) {
      const error = new Error(`Data validation failed for transfer ${id}`)
      options.onError?.(error)
      throw error
    }

    this.transfers.set(id, transferData)
    this.history.push({ ...transferData })

    // 保持历史记录在合理范围内
    if (this.history.length > 100) {
      this.history = this.history.slice(-50)
    }

    // 通知订阅者
    this.notifySubscribers(id, transferData)

    // 持久化存储
    if (transferData.persistent) {
      this.persistToStorage(transferData)
    }

    options.onSuccess?.(transferData.data)
  }

  // 获取数据
  retrieve(id: string): TransferData | null {
    const data = this.transfers.get(id)
    if (!data) {
      // 尝试从持久化存储中获取
      return this.retrieveFromStorage(id)
    }
    return data
  }

  // 删除数据
  remove(id: string): boolean {
    const success = this.transfers.delete(id)
    if (success) {
      this.removeFromStorage(id)
    }
    return success
  }

  // 清空所有非持久化数据
  clear(): void {
    const persistentData = new Map<string, TransferData>()
    for (const [id, data] of this.transfers.entries()) {
      if (data.persistent) {
        persistentData.set(id, data)
      }
    }
    this.transfers = persistentData
  }

  // 订阅数据变化
  subscribe(id: string, callback: (data: TransferData) => void): () => void {
    if (!this.subscribers.has(id)) {
      this.subscribers.set(id, new Set())
    }
    this.subscribers.get(id)!.add(callback)

    // 返回取消订阅函数
    return () => {
      this.subscribers.get(id)?.delete(callback)
      if (this.subscribers.get(id)?.size === 0) {
        this.subscribers.delete(id)
      }
    }
  }

  // 获取所有数据
  getAll(): TransferData[] {
    return Array.from(this.transfers.values())
  }

  // 根据类型获取数据
  getByType(type: TransferData['type']): TransferData[] {
    return Array.from(this.transfers.values()).filter(item => item.type === type)
  }

  // 获取历史记录
  getHistory(): TransferData[] {
    return [...this.history]
  }

  // 数据统计
  getStats() {
    const types = new Map<string, number>()
    const sources = new Map<string, number>()
    
    for (const data of this.transfers.values()) {
      types.set(data.type, (types.get(data.type) || 0) + 1)
      sources.set(data.source, (sources.get(data.source) || 0) + 1)
    }

    return {
      total: this.transfers.size,
      byType: Object.fromEntries(types),
      bySources: Object.fromEntries(sources),
      historySize: this.history.length
    }
  }

  private getCurrentRoute(): string {
    return window.location.pathname || 'unknown'
  }

  private notifySubscribers(id: string, data: TransferData): void {
    this.subscribers.get(id)?.forEach(callback => {
      try {
        callback(data)
      } catch (error) {
        console.error('Subscriber callback error:', error)
      }
    })
  }

  private persistToStorage(data: TransferData): void {
    try {
      const key = `transfer_${data.id}`
      localStorage.setItem(key, JSON.stringify(data))
    } catch (error) {
      console.error('Failed to persist transfer data:', error)
    }
  }

  private retrieveFromStorage(id: string): TransferData | null {
    try {
      const key = `transfer_${id}`
      const data = localStorage.getItem(key)
      return data ? JSON.parse(data) : null
    } catch (error) {
      console.error('Failed to retrieve transfer data:', error)
      return null
    }
  }

  private removeFromStorage(id: string): void {
    try {
      const key = `transfer_${id}`
      localStorage.removeItem(key)
    } catch (error) {
      console.error('Failed to remove transfer data:', error)
    }
  }
}

// 全局实例
const transferManager = new DataTransferManager()

// Composable 函数
export function useDataTransfer() {
  const router = useRouter()
  const route = useRoute()

  // 响应式状态
  const isTransferring = ref(false)
  const transferHistory = ref<TransferData[]>([])
  const transferStats = ref(transferManager.getStats())

  // 刷新统计信息
  const refreshStats = () => {
    transferStats.value = transferManager.getStats()
    transferHistory.value = transferManager.getHistory()
  }

  // 传递数据到指定页面
  const transferTo = async (
    target: string,
    data: any,
    options: TransferOptions & { 
      type?: TransferData['type']
      navigate?: boolean
      query?: Record<string, any>
    } = {}
  ) => {
    try {
      isTransferring.value = true
      
      const transferId = `transfer_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
      const transferType = options.type || 'config'

      // 存储数据
      transferManager.store(transferId, transferType, data, {
        persistent: options.persistent,
        validation: options.validation,
        transform: options.transform,
        onSuccess: options.onSuccess,
        onError: options.onError
      })

      // 导航到目标页面
      if (options.navigate !== false) {
        await router.push({
          path: target,
          query: {
            ...options.query,
            transfer: transferId
          }
        })
      }

      refreshStats()
      ElMessage.success('数据传递成功')
      
      return transferId
    } catch (error) {
      ElMessage.error('数据传递失败: ' + (error as Error).message)
      throw error
    } finally {
      isTransferring.value = false
    }
  }

  // 接收传递的数据
  const receiveTransfer = (transferId?: string): TransferData | null => {
    const id = transferId || route.query.transfer as string
    if (!id) return null

    const data = transferManager.retrieve(id)
    if (data) {
      // 更新目标页面
      data.target = route.path
      refreshStats()
    }
    
    return data
  }

  // 传递因子数据
  const transferFactor = (factorData: any, target: string, options: TransferOptions = {}) => {
    return transferTo(target, factorData, {
      ...options,
      type: 'factor',
      validation: (data) => data && data.expression,
      transform: (data) => ({
        ...data,
        transferredAt: Date.now(),
        transferType: 'factor'
      })
    })
  }

  // 传递模型数据
  const transferModel = (modelData: any, target: string, options: TransferOptions = {}) => {
    return transferTo(target, modelData, {
      ...options,
      type: 'model',
      validation: (data) => data && data.id,
      transform: (data) => ({
        ...data,
        transferredAt: Date.now(),
        transferType: 'model'
      })
    })
  }

  // 传递策略配置
  const transferStrategy = (strategyData: any, target: string, options: TransferOptions = {}) => {
    return transferTo(target, strategyData, {
      ...options,
      type: 'strategy',
      validation: (data) => data && data.config,
      transform: (data) => ({
        ...data,
        transferredAt: Date.now(),
        transferType: 'strategy'
      })
    })
  }

  // 传递实验配置
  const transferExperiment = (experimentData: any, target: string, options: TransferOptions = {}) => {
    return transferTo(target, experimentData, {
      ...options,
      type: 'experiment',
      validation: (data) => data && (data.factors || data.model),
      transform: (data) => ({
        ...data,
        transferredAt: Date.now(),
        transferType: 'experiment'
      })
    })
  }

  // 快速导航函数
  const navigateWithFactor = (factorIds: string[], target: string = '/training') => {
    return transferFactor({ selectedFactors: factorIds }, target, {
      navigate: true,
      query: { autoConfig: 'true' }
    })
  }

  const navigateWithModel = (modelId: string, target: string = '/backtest') => {
    return transferModel({ selectedModel: modelId }, target, {
      navigate: true,
      query: { autoConfig: 'true' }
    })
  }

  const navigateWithResults = (resultId: string, target: string = '/deployment') => {
    return transferStrategy({ resultId }, target, {
      navigate: true,
      query: { autoConfig: 'true' }
    })
  }

  // 清理传递数据
  const clearTransfer = (transferId: string) => {
    transferManager.remove(transferId)
    refreshStats()
  }

  // 清理所有非持久化数据
  const clearAllTransfers = () => {
    transferManager.clear()
    refreshStats()
    ElMessage.success('已清理所有临时传递数据')
  }

  // 订阅数据变化
  const subscribeToTransfer = (transferId: string, callback: (data: TransferData) => void) => {
    return transferManager.subscribe(transferId, callback)
  }

  // 获取特定类型的传递数据
  const getTransfersByType = (type: TransferData['type']) => {
    return transferManager.getByType(type)
  }

  // 检查是否有待处理的传递
  const hasPendingTransfers = computed(() => {
    return !!route.query.transfer
  })

  // 获取当前页面的传递数据
  const currentTransfer = computed(() => {
    if (route.query.transfer) {
      return receiveTransfer(route.query.transfer as string)
    }
    return null
  })

  // 传递状态信息
  const transferInfo = computed(() => {
    const stats = transferStats.value
    return {
      hasActiveTransfers: stats.total > 0,
      totalTransfers: stats.total,
      typeDistribution: stats.byType,
      historyCount: stats.historySize
    }
  })

  // 初始化时刷新统计
  refreshStats()

  return {
    // 状态
    isTransferring,
    transferHistory,
    transferStats,
    hasPendingTransfers,
    currentTransfer,
    transferInfo,

    // 基础方法
    transferTo,
    receiveTransfer,
    clearTransfer,
    clearAllTransfers,
    subscribeToTransfer,
    getTransfersByType,

    // 特定类型传递方法
    transferFactor,
    transferModel,
    transferStrategy,
    transferExperiment,

    // 快速导航方法
    navigateWithFactor,
    navigateWithModel,
    navigateWithResults,

    // 工具方法
    refreshStats
  }
}

// 导出管理器实例供高级用法
export { transferManager }

// 全局数据传递事件总线
export interface DataTransferEvents {
  'transfer:created': TransferData
  'transfer:retrieved': TransferData
  'transfer:removed': string
  'transfer:cleared': void
}

// 类型导出
export type { TransferData, TransferOptions }