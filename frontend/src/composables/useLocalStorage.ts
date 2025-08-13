import { ref, reactive, watch, computed, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { debounce, throttle } from 'lodash-es'

// 存储配置接口
interface StorageConfig {
  prefix: string // 存储键前缀
  enableCompression: boolean // 是否启用压缩
  enableEncryption: boolean // 是否启用加密
  enableVersioning: boolean // 是否启用版本控制
  maxVersions: number // 最大版本数
  autoCleanup: boolean // 是否自动清理过期数据
  maxAge: number // 数据最大存活时间（毫秒）
  watchChanges: boolean // 是否监听外部变化
  syncAcrossTabs: boolean // 是否跨标签页同步
}

// 存储项接口
interface StorageItem<T = any> {
  value: T
  timestamp: number
  version: number
  compressed?: boolean
  encrypted?: boolean
  metadata?: Record<string, any>
  expiresAt?: number
}

// 存储事件接口
interface StorageEvent<T = any> {
  key: string
  oldValue: T | null
  newValue: T | null
  source: 'local' | 'external'
  timestamp: number
}

// 本地存储管理器
class LocalStorageManager {
  private config: StorageConfig
  private listeners: Map<string, Set<(event: StorageEvent) => void>> = new Map()
  private watchers: Map<string, any> = new Map()
  private compressionEnabled: boolean = false

  constructor(config: Partial<StorageConfig> = {}) {
    this.config = {
      prefix: 'qlib_',
      enableCompression: false,
      enableEncryption: false,
      enableVersioning: true,
      maxVersions: 5,
      autoCleanup: true,
      maxAge: 7 * 24 * 60 * 60 * 1000, // 7天
      watchChanges: true,
      syncAcrossTabs: true,
      ...config
    }

    // 检查是否支持压缩
    this.checkCompressionSupport()

    // 设置跨标签页同步
    if (this.config.syncAcrossTabs) {
      this.setupCrossTabSync()
    }

    // 定期清理过期数据
    if (this.config.autoCleanup) {
      this.setupAutoCleanup()
    }
  }

  // 生成完整的存储键
  private getFullKey(key: string): string {
    return `${this.config.prefix}${key}`
  }

  // 设置数据
  set<T>(key: string, value: T, options: {
    expires?: number
    metadata?: Record<string, any>
    skipVersioning?: boolean
  } = {}): boolean {
    try {
      const fullKey = this.getFullKey(key)
      const now = Date.now()

      // 获取当前版本号
      let version = 1
      if (this.config.enableVersioning && !options.skipVersioning) {
        const existing = this.get(key, { includeMetadata: true })
        if (existing && typeof existing === 'object' && 'version' in existing) {
          version = (existing as any).version + 1
        }
      }

      // 创建存储项
      const item: StorageItem<T> = {
        value,
        timestamp: now,
        version,
        metadata: options.metadata,
        expiresAt: options.expires ? now + options.expires : undefined
      }

      // 压缩数据
      let serializedData = JSON.stringify(item)
      if (this.config.enableCompression && this.compressionEnabled) {
        try {
          serializedData = this.compress(serializedData)
          item.compressed = true
        } catch (error) {
          console.warn('压缩失败，使用原始数据:', error)
        }
      }

      // 加密数据
      if (this.config.enableEncryption) {
        try {
          serializedData = this.encrypt(serializedData)
          item.encrypted = true
        } catch (error) {
          console.warn('加密失败，使用原始数据:', error)
        }
      }

      // 存储到 localStorage
      localStorage.setItem(fullKey, serializedData)

      // 版本控制
      if (this.config.enableVersioning && !options.skipVersioning) {
        this.manageVersions(key, item)
      }

      // 触发监听器
      this.notifyListeners(key, null, value, 'local')

      return true
    } catch (error) {
      console.error('LocalStorage set error:', error)
      ElMessage.error('数据保存失败')
      return false
    }
  }

  // 获取数据
  get<T>(key: string, options: {
    includeMetadata?: boolean
    defaultValue?: T
    version?: number
  } = {}): T | null {
    try {
      const fullKey = this.getFullKey(key)
      let data = localStorage.getItem(fullKey)

      if (!data) {
        return options.defaultValue ?? null
      }

      // 解密数据
      if (this.config.enableEncryption) {
        try {
          data = this.decrypt(data)
        } catch (error) {
          console.warn('解密失败:', error)
          return options.defaultValue ?? null
        }
      }

      // 解压缩数据
      if (this.config.enableCompression) {
        try {
          data = this.decompress(data)
        } catch (error) {
          // 如果解压缩失败，可能是未压缩的数据
        }
      }

      const item: StorageItem<T> = JSON.parse(data)

      // 检查是否过期
      if (item.expiresAt && Date.now() > item.expiresAt) {
        this.remove(key)
        return options.defaultValue ?? null
      }

      // 版本控制
      if (options.version && item.version !== options.version) {
        return this.getVersion(key, options.version) ?? options.defaultValue ?? null
      }

      return options.includeMetadata ? item as any : item.value
    } catch (error) {
      console.error('LocalStorage get error:', error)
      return options.defaultValue ?? null
    }
  }

  // 移除数据
  remove(key: string): boolean {
    try {
      const fullKey = this.getFullKey(key)
      const oldValue = this.get(key)
      
      localStorage.removeItem(fullKey)
      
      // 清理版本数据
      if (this.config.enableVersioning) {
        this.removeVersions(key)
      }

      // 触发监听器
      this.notifyListeners(key, oldValue, null, 'local')

      return true
    } catch (error) {
      console.error('LocalStorage remove error:', error)
      return false
    }
  }

  // 检查键是否存在
  has(key: string): boolean {
    const fullKey = this.getFullKey(key)
    return localStorage.getItem(fullKey) !== null
  }

  // 获取所有键
  keys(): string[] {
    const keys: string[] = []
    const prefix = this.config.prefix
    
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i)
      if (key && key.startsWith(prefix)) {
        keys.push(key.substring(prefix.length))
      }
    }
    
    return keys
  }

  // 清空所有数据
  clear(): boolean {
    try {
      const keys = this.keys()
      keys.forEach(key => this.remove(key))
      return true
    } catch (error) {
      console.error('LocalStorage clear error:', error)
      return false
    }
  }

  // 获取存储大小
  getSize(): { used: number; total: number; available: number } {
    let used = 0
    let total = 5 * 1024 * 1024 // 假设 5MB 总容量

    try {
      // 计算已使用空间
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i)
        const value = localStorage.getItem(key!)
        if (key && value) {
          used += key.length + value.length
        }
      }

      // 尝试检测实际可用空间
      const testKey = '_test_storage_limit_'
      let testData = 'a'
      let actualTotal = used

      try {
        while (true) {
          const newData = testData.repeat(1024) // 1KB 增量
          localStorage.setItem(testKey, newData)
          actualTotal += newData.length
          testData = newData
        }
      } catch {
        localStorage.removeItem(testKey)
        total = actualTotal
      }
    } catch (error) {
      console.warn('无法检测存储空间大小:', error)
    }

    return {
      used,
      total,
      available: total - used
    }
  }

  // 添加变化监听器
  addListener(key: string, callback: (event: StorageEvent) => void): () => void {
    if (!this.listeners.has(key)) {
      this.listeners.set(key, new Set())
    }
    
    this.listeners.get(key)!.add(callback)

    // 返回移除监听器的函数
    return () => {
      this.listeners.get(key)?.delete(callback)
      if (this.listeners.get(key)?.size === 0) {
        this.listeners.delete(key)
      }
    }
  }

  // 通知监听器
  private notifyListeners(key: string, oldValue: any, newValue: any, source: 'local' | 'external'): void {
    const listeners = this.listeners.get(key)
    if (listeners) {
      const event: StorageEvent = {
        key,
        oldValue,
        newValue,
        source,
        timestamp: Date.now()
      }

      listeners.forEach(callback => {
        try {
          callback(event)
        } catch (error) {
          console.error('Storage listener error:', error)
        }
      })
    }
  }

  // 版本管理
  private manageVersions<T>(key: string, item: StorageItem<T>): void {
    const versionKey = `${key}_versions`
    const versions = this.get(versionKey, { defaultValue: [] as StorageItem<T>[] })
    
    if (Array.isArray(versions)) {
      versions.push(item)
      
      // 限制版本数量
      if (versions.length > this.config.maxVersions) {
        versions.splice(0, versions.length - this.config.maxVersions)
      }
      
      this.set(versionKey, versions, { skipVersioning: true })
    }
  }

  // 获取指定版本
  private getVersion<T>(key: string, version: number): T | null {
    const versionKey = `${key}_versions`
    const versions = this.get(versionKey, { defaultValue: [] as StorageItem<T>[] })
    
    if (Array.isArray(versions)) {
      const versionItem = versions.find(v => v.version === version)
      return versionItem ? versionItem.value : null
    }
    
    return null
  }

  // 移除版本数据
  private removeVersions(key: string): void {
    const versionKey = `${key}_versions`
    const fullVersionKey = this.getFullKey(versionKey)
    localStorage.removeItem(fullVersionKey)
  }

  // 设置跨标签页同步
  private setupCrossTabSync(): void {
    window.addEventListener('storage', (e) => {
      if (e.key?.startsWith(this.config.prefix)) {
        const key = e.key.substring(this.config.prefix.length)
        const oldValue = e.oldValue ? JSON.parse(e.oldValue) : null
        const newValue = e.newValue ? JSON.parse(e.newValue) : null
        
        this.notifyListeners(key, oldValue, newValue, 'external')
      }
    })
  }

  // 设置自动清理
  private setupAutoCleanup(): void {
    setInterval(() => {
      this.cleanup()
    }, 60 * 60 * 1000) // 每小时清理一次
  }

  // 清理过期数据
  cleanup(): number {
    let cleanedCount = 0
    const now = Date.now()
    const keys = this.keys()

    keys.forEach(key => {
      try {
        const item = this.get(key, { includeMetadata: true }) as StorageItem
        if (item && item.expiresAt && now > item.expiresAt) {
          this.remove(key)
          cleanedCount++
        }
      } catch (error) {
        console.warn(`清理键 ${key} 时出错:`, error)
      }
    })

    if (cleanedCount > 0) {
      console.log(`已清理 ${cleanedCount} 个过期项`)
    }

    return cleanedCount
  }

  // 导出数据
  export(): string {
    const data: Record<string, any> = {}
    const keys = this.keys()

    keys.forEach(key => {
      try {
        data[key] = this.get(key, { includeMetadata: true })
      } catch (error) {
        console.warn(`导出键 ${key} 时出错:`, error)
      }
    })

    return JSON.stringify({
      data,
      exportTime: new Date().toISOString(),
      config: this.config
    }, null, 2)
  }

  // 导入数据
  import(jsonData: string): boolean {
    try {
      const imported = JSON.parse(jsonData)
      
      if (imported.data && typeof imported.data === 'object') {
        Object.entries(imported.data).forEach(([key, value]) => {
          this.set(key, value, { skipVersioning: true })
        })
        return true
      }
      
      return false
    } catch (error) {
      console.error('导入数据失败:', error)
      return false
    }
  }

  // 检查压缩支持
  private checkCompressionSupport(): void {
    // 这里可以检查是否支持压缩算法
    // 简化实现，实际项目中可以使用更高效的压缩算法
    this.compressionEnabled = true
  }

  // 简单压缩（实际项目中应使用更高效的算法）
  private compress(data: string): string {
    // 这里使用简单的压缩方法，实际应用中可以使用 pako 或其他压缩库
    return btoa(data)
  }

  // 简单解压缩
  private decompress(data: string): string {
    try {
      return atob(data)
    } catch {
      // 如果解压缩失败，返回原始数据
      return data
    }
  }

  // 简单加密（实际项目中应使用更安全的加密）
  private encrypt(data: string): string {
    // 这里使用简单的加密方法，实际应用中应使用更安全的加密算法
    return btoa(data)
  }

  // 简单解密
  private decrypt(data: string): string {
    return atob(data)
  }
}

// Composable 函数
export function useLocalStorage<T>(
  key: string,
  defaultValue?: T,
  config: Partial<StorageConfig> = {}
) {
  // 创建存储管理器实例
  const storage = new LocalStorageManager(config)
  
  // 响应式状态
  const storedValue = ref<T>(storage.get(key, { defaultValue }) ?? defaultValue!)
  const isLoading = ref(false)
  const error = ref<string | null>(null)
  const lastUpdated = ref<Date | null>(null)
  
  // 存储统计
  const stats = reactive({
    size: 0,
    version: 1,
    hasExpiry: false,
    expiresAt: null as Date | null
  })

  // 更新统计信息
  const updateStats = () => {
    const item = storage.get(key, { includeMetadata: true }) as StorageItem<T>
    if (item) {
      stats.version = item.version || 1
      stats.hasExpiry = !!item.expiresAt
      stats.expiresAt = item.expiresAt ? new Date(item.expiresAt) : null
    }
    
    const storageInfo = storage.getSize()
    stats.size = storageInfo.used
  }

  // 保存数据
  const save = (value: T, options?: {
    expires?: number
    metadata?: Record<string, any>
  }) => {
    try {
      isLoading.value = true
      error.value = null
      
      const success = storage.set(key, value, options)
      
      if (success) {
        storedValue.value = value
        lastUpdated.value = new Date()
        updateStats()
        ElMessage.success('数据已保存')
      } else {
        throw new Error('保存失败')
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : String(err)
      ElMessage.error('保存失败: ' + error.value)
    } finally {
      isLoading.value = false
    }
  }

  // 加载数据
  const load = () => {
    try {
      isLoading.value = true
      error.value = null
      
      const value = storage.get(key, { defaultValue })
      if (value !== null) {
        storedValue.value = value
        lastUpdated.value = new Date()
        updateStats()
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : String(err)
      ElMessage.error('加载失败: ' + error.value)
    } finally {
      isLoading.value = false
    }
  }

  // 移除数据
  const remove = () => {
    try {
      const success = storage.remove(key)
      if (success) {
        storedValue.value = defaultValue!
        lastUpdated.value = new Date()
        updateStats()
        ElMessage.success('数据已删除')
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : String(err)
      ElMessage.error('删除失败: ' + error.value)
    }
  }

  // 检查是否存在
  const exists = computed(() => storage.has(key))

  // 设置过期时间
  const setExpiry = (expirationTime: number) => {
    if (exists.value) {
      save(storedValue.value, { expires: expirationTime })
    }
  }

  // 自动保存（防抖）
  const autoSave = debounce((value: T) => {
    save(value)
  }, 1000)

  // 监听外部变化
  const unsubscribe = storage.addListener(key, (event) => {
    if (event.source === 'external') {
      storedValue.value = event.newValue ?? defaultValue!
      lastUpdated.value = new Date()
      updateStats()
    }
  })

  // 监听值变化并自动保存
  const stopWatcher = watch(
    storedValue,
    (newValue) => {
      if (config.watchChanges !== false) {
        autoSave(newValue)
      }
    },
    { deep: true }
  )

  // 初始化统计信息
  updateStats()

  // 清理函数
  const cleanup = () => {
    unsubscribe()
    stopWatcher()
  }

  // 组件卸载时清理
  onUnmounted(cleanup)

  return {
    // 状态
    value: storedValue,
    isLoading,
    error,
    lastUpdated,
    stats,
    exists,

    // 方法
    save,
    load,
    remove,
    setExpiry,
    cleanup,

    // 存储管理器实例
    storage
  }
}

// 导出存储管理器类
export { LocalStorageManager }

// 类型导出
export type { StorageConfig, StorageItem, StorageEvent }