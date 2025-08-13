import { ref, reactive, watch, computed, onUnmounted, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElNotification } from 'element-plus'
import { debounce, throttle, isEqual, cloneDeep } from 'lodash-es'

// 云端同步配置
interface CloudSyncConfig {
  endpoint: string // API端点
  enableAutoSync: boolean // 是否启用自动同步
  syncInterval: number // 同步间隔（毫秒）
  conflictResolution: 'local' | 'remote' | 'merge' | 'manual' // 冲突解决策略
  enableCompression: boolean // 是否启用压缩
  enableEncryption: boolean // 是否启用加密
  enableBatching: boolean // 是否启用批量同步
  batchSize: number // 批量大小
  maxRetries: number // 最大重试次数
  retryDelay: number // 重试延迟（毫秒）
  enableVersioning: boolean // 是否启用版本控制
  enableDeltaSync: boolean // 是否启用增量同步
  authHeaders?: Record<string, string> // 认证头
}

// 云端数据项
interface CloudDataItem<T = any> {
  id: string
  key: string
  value: T
  version: number
  timestamp: number
  userId?: string
  deviceId: string
  checksum: string
  metadata?: Record<string, any>
}

// 同步操作
interface SyncOperation {
  id: string
  type: 'create' | 'update' | 'delete'
  key: string
  localData?: any
  remoteData?: any
  timestamp: number
  status: 'pending' | 'syncing' | 'success' | 'failed' | 'conflict'
  retryCount: number
  error?: string
}

// 冲突信息
interface ConflictInfo {
  key: string
  localValue: any
  remoteValue: any
  localVersion: number
  remoteVersion: number
  localTimestamp: number
  remoteTimestamp: number
  resolved: boolean
  resolution?: 'local' | 'remote' | 'merge'
}

// 同步状态
interface SyncStatus {
  isOnline: boolean
  isConnected: boolean
  isSyncing: boolean
  lastSyncTime: Date | null
  nextSyncTime: Date | null
  syncCount: number
  errorCount: number
  conflictCount: number
  pendingOperations: number
  uploadProgress: number
  downloadProgress: number
}

// 云端同步管理器
class CloudSyncManager {
  private config: CloudSyncConfig
  private localData: Map<string, any> = new Map()
  private cloudData: Map<string, CloudDataItem> = new Map()
  private syncQueue: SyncOperation[] = []
  private conflicts: ConflictInfo[] = []
  private deviceId: string
  private userId?: string
  private syncTimer?: NodeJS.Timeout
  private retryTimers: Map<string, NodeJS.Timeout> = new Map()

  constructor(config: Partial<CloudSyncConfig> = {}) {
    this.config = {
      endpoint: '/api/v1/cloud-sync',
      enableAutoSync: true,
      syncInterval: 30000, // 30秒
      conflictResolution: 'local',
      enableCompression: true,
      enableEncryption: false,
      enableBatching: true,
      batchSize: 10,
      maxRetries: 3,
      retryDelay: 2000,
      enableVersioning: true,
      enableDeltaSync: true,
      ...config
    }

    this.deviceId = this.generateDeviceId()
    this.initializeSync()
  }

  // 生成设备ID
  private generateDeviceId(): string {
    let deviceId = localStorage.getItem('device_id')
    if (!deviceId) {
      deviceId = `device_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
      localStorage.setItem('device_id', deviceId)
    }
    return deviceId
  }

  // 初始化同步
  private initializeSync(): void {
    // 从本地存储恢复数据
    this.restoreFromLocal()

    // 设置自动同步
    if (this.config.enableAutoSync) {
      this.startAutoSync()
    }

    // 监听网络状态
    window.addEventListener('online', () => {
      this.handleNetworkOnline()
    })

    window.addEventListener('offline', () => {
      this.handleNetworkOffline()
    })

    // 监听页面卸载
    window.addEventListener('beforeunload', () => {
      this.saveToLocal()
    })
  }

  // 设置数据
  set<T>(key: string, value: T, metadata?: Record<string, any>): void {
    const version = this.getNextVersion(key)
    const timestamp = Date.now()
    
    // 更新本地数据
    this.localData.set(key, {
      value,
      version,
      timestamp,
      metadata
    })

    // 添加到同步队列
    this.addToSyncQueue({
      id: `op_${timestamp}_${Math.random().toString(36).substr(2, 6)}`,
      type: this.cloudData.has(key) ? 'update' : 'create',
      key,
      localData: { value, version, timestamp, metadata },
      timestamp,
      status: 'pending',
      retryCount: 0
    })

    // 立即保存到本地存储
    this.saveToLocal()

    // 如果在线，尝试立即同步
    if (navigator.onLine && this.config.enableAutoSync) {
      this.debouncedSync()
    }
  }

  // 获取数据
  get<T>(key: string, defaultValue?: T): T | undefined {
    const localItem = this.localData.get(key)
    return localItem ? localItem.value : defaultValue
  }

  // 删除数据
  delete(key: string): boolean {
    const existed = this.localData.has(key)
    
    if (existed) {
      this.localData.delete(key)
      
      // 如果云端也有这个数据，添加删除操作到队列
      if (this.cloudData.has(key)) {
        this.addToSyncQueue({
          id: `op_${Date.now()}_${Math.random().toString(36).substr(2, 6)}`,
          type: 'delete',
          key,
          timestamp: Date.now(),
          status: 'pending',
          retryCount: 0
        })
      }

      this.saveToLocal()
    }

    return existed
  }

  // 获取下一个版本号
  private getNextVersion(key: string): number {
    const localItem = this.localData.get(key)
    const cloudItem = this.cloudData.get(key)
    
    const localVersion = localItem ? localItem.version : 0
    const remoteVersion = cloudItem ? cloudItem.version : 0
    
    return Math.max(localVersion, remoteVersion) + 1
  }

  // 添加到同步队列
  private addToSyncQueue(operation: SyncOperation): void {
    this.syncQueue.push(operation)

    // 如果启用批量处理，限制队列大小
    if (this.config.enableBatching && this.syncQueue.length > this.config.batchSize * 2) {
      this.syncQueue = this.syncQueue.slice(-this.config.batchSize)
    }
  }

  // 执行同步
  async sync(): Promise<boolean> {
    if (!navigator.onLine) {
      return false
    }

    try {
      // 上传本地更改
      const uploadSuccess = await this.uploadChanges()
      
      // 下载远程更改
      const downloadSuccess = await this.downloadChanges()
      
      return uploadSuccess && downloadSuccess
    } catch (error) {
      console.error('Sync failed:', error)
      return false
    }
  }

  // 上传本地更改
  private async uploadChanges(): Promise<boolean> {
    const pendingOps = this.syncQueue.filter(op => op.status === 'pending')
    if (pendingOps.length === 0) return true

    try {
      // 批量处理或单个处理
      if (this.config.enableBatching && pendingOps.length > 1) {
        return await this.batchUpload(pendingOps.slice(0, this.config.batchSize))
      } else {
        return await this.singleUpload(pendingOps[0])
      }
    } catch (error) {
      console.error('Upload failed:', error)
      return false
    }
  }

  // 批量上传
  private async batchUpload(operations: SyncOperation[]): Promise<boolean> {
    const uploadData = operations.map(op => ({
      id: op.id,
      type: op.type,
      key: op.key,
      data: op.localData,
      deviceId: this.deviceId,
      userId: this.userId
    }))

    try {
      const response = await fetch(`${this.config.endpoint}/batch`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...this.config.authHeaders
        },
        body: JSON.stringify({
          operations: uploadData,
          enableCompression: this.config.enableCompression,
          enableEncryption: this.config.enableEncryption
        })
      })

      if (!response.ok) {
        throw new Error(`Upload failed: ${response.statusText}`)
      }

      const result = await response.json()
      
      // 处理结果
      operations.forEach((op, index) => {
        const opResult = result.results[index]
        if (opResult.success) {
          op.status = 'success'
          if (opResult.data) {
            this.cloudData.set(op.key, opResult.data)
          }
        } else {
          op.status = 'failed'
          op.error = opResult.error
        }
      })

      // 移除成功的操作
      this.syncQueue = this.syncQueue.filter(op => op.status !== 'success')
      
      return true
    } catch (error) {
      // 标记所有操作为失败
      operations.forEach(op => {
        op.status = 'failed'
        op.error = error instanceof Error ? error.message : String(error)
        op.retryCount++
      })
      
      return false
    }
  }

  // 单个上传
  private async singleUpload(operation: SyncOperation): Promise<boolean> {
    try {
      operation.status = 'syncing'
      
      const response = await fetch(`${this.config.endpoint}/${operation.type}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...this.config.authHeaders
        },
        body: JSON.stringify({
          key: operation.key,
          data: operation.localData,
          deviceId: this.deviceId,
          userId: this.userId
        })
      })

      if (!response.ok) {
        throw new Error(`Upload failed: ${response.statusText}`)
      }

      const result = await response.json()
      
      if (result.success) {
        operation.status = 'success'
        if (result.data) {
          this.cloudData.set(operation.key, result.data)
        }
        
        // 从队列中移除
        this.syncQueue = this.syncQueue.filter(op => op.id !== operation.id)
        
        return true
      } else if (result.conflict) {
        // 处理冲突
        this.handleConflict(operation.key, operation.localData, result.remoteData)
        operation.status = 'conflict'
        return false
      } else {
        throw new Error(result.error || 'Unknown error')
      }
    } catch (error) {
      operation.status = 'failed'
      operation.error = error instanceof Error ? error.message : String(error)
      operation.retryCount++
      
      // 安排重试
      if (operation.retryCount <= this.config.maxRetries) {
        this.scheduleRetry(operation)
      }
      
      return false
    }
  }

  // 下载远程更改
  private async downloadChanges(): Promise<boolean> {
    try {
      const lastSyncTime = this.getLastSyncTime()
      const url = this.config.enableDeltaSync && lastSyncTime
        ? `${this.config.endpoint}/changes?since=${lastSyncTime.getTime()}`
        : `${this.config.endpoint}/all`

      const response = await fetch(url, {
        method: 'GET',
        headers: {
          ...this.config.authHeaders
        }
      })

      if (!response.ok) {
        throw new Error(`Download failed: ${response.statusText}`)
      }

      const data = await response.json()
      
      // 处理远程数据
      if (data.items) {
        data.items.forEach((item: CloudDataItem) => {
          this.processRemoteItem(item)
        })
      }

      // 更新最后同步时间
      this.setLastSyncTime(new Date())
      
      return true
    } catch (error) {
      console.error('Download failed:', error)
      return false
    }
  }

  // 处理远程数据项
  private processRemoteItem(remoteItem: CloudDataItem): void {
    const localItem = this.localData.get(remoteItem.key)
    
    if (!localItem) {
      // 本地没有，直接添加
      this.localData.set(remoteItem.key, {
        value: remoteItem.value,
        version: remoteItem.version,
        timestamp: remoteItem.timestamp,
        metadata: remoteItem.metadata
      })
      this.cloudData.set(remoteItem.key, remoteItem)
    } else {
      // 检查冲突
      if (localItem.version > remoteItem.version) {
        // 本地更新，无需处理
        return
      } else if (localItem.version < remoteItem.version) {
        // 远程更新，应用更改
        this.applyRemoteChange(remoteItem)
      } else {
        // 版本相同，检查时间戳
        if (localItem.timestamp !== remoteItem.timestamp) {
          // 可能的冲突
          this.handleConflict(remoteItem.key, localItem, remoteItem)
        }
      }
    }
  }

  // 应用远程更改
  private applyRemoteChange(remoteItem: CloudDataItem): void {
    this.localData.set(remoteItem.key, {
      value: remoteItem.value,
      version: remoteItem.version,
      timestamp: remoteItem.timestamp,
      metadata: remoteItem.metadata
    })
    this.cloudData.set(remoteItem.key, remoteItem)
  }

  // 处理冲突
  private handleConflict(key: string, localData: any, remoteData: any): void {
    const conflict: ConflictInfo = {
      key,
      localValue: localData.value,
      remoteValue: remoteData.value,
      localVersion: localData.version,
      remoteVersion: remoteData.version,
      localTimestamp: localData.timestamp,
      remoteTimestamp: remoteData.timestamp,
      resolved: false
    }

    this.conflicts.push(conflict)

    // 根据配置自动解决冲突
    if (this.config.conflictResolution !== 'manual') {
      this.resolveConflict(conflict, this.config.conflictResolution)
    }
  }

  // 解决冲突
  resolveConflict(conflict: ConflictInfo, resolution: 'local' | 'remote' | 'merge'): void {
    switch (resolution) {
      case 'local':
        // 保持本地值
        conflict.resolution = 'local'
        break
      
      case 'remote':
        // 使用远程值
        this.localData.set(conflict.key, {
          value: conflict.remoteValue,
          version: conflict.remoteVersion,
          timestamp: conflict.remoteTimestamp
        })
        conflict.resolution = 'remote'
        break
      
      case 'merge':
        // 简单合并策略
        const mergedValue = this.mergeValues(conflict.localValue, conflict.remoteValue)
        const newVersion = Math.max(conflict.localVersion, conflict.remoteVersion) + 1
        
        this.localData.set(conflict.key, {
          value: mergedValue,
          version: newVersion,
          timestamp: Date.now()
        })
        conflict.resolution = 'merge'
        break
    }

    conflict.resolved = true
  }

  // 合并值
  private mergeValues(localValue: any, remoteValue: any): any {
    // 简单的合并逻辑，实际应用中可能需要更复杂的策略
    if (Array.isArray(localValue) && Array.isArray(remoteValue)) {
      return [...localValue, ...remoteValue.filter(item => !localValue.includes(item))]
    } else if (typeof localValue === 'object' && typeof remoteValue === 'object') {
      return { ...localValue, ...remoteValue }
    } else {
      // 对于基本类型，使用时间戳较新的值
      return localValue
    }
  }

  // 安排重试
  private scheduleRetry(operation: SyncOperation): void {
    const delay = this.config.retryDelay * Math.pow(2, operation.retryCount - 1)
    
    const timer = setTimeout(() => {
      operation.status = 'pending'
      this.retryTimers.delete(operation.id)
    }, delay)
    
    this.retryTimers.set(operation.id, timer)
  }

  // 启动自动同步
  private startAutoSync(): void {
    if (this.syncTimer) {
      clearInterval(this.syncTimer)
    }

    this.syncTimer = setInterval(() => {
      if (navigator.onLine) {
        this.sync()
      }
    }, this.config.syncInterval)
  }

  // 停止自动同步
  stopAutoSync(): void {
    if (this.syncTimer) {
      clearInterval(this.syncTimer)
      this.syncTimer = undefined
    }
  }

  // 网络连接恢复
  private handleNetworkOnline(): void {
    if (this.config.enableAutoSync) {
      this.sync()
    }
  }

  // 网络连接断开
  private handleNetworkOffline(): void {
    // 暂停同步，数据继续保存到本地
  }

  // 防抖同步
  private debouncedSync = debounce(() => {
    this.sync()
  }, 1000)

  // 保存到本地存储
  private saveToLocal(): void {
    try {
      const data = {
        localData: Object.fromEntries(this.localData),
        cloudData: Object.fromEntries(this.cloudData),
        syncQueue: this.syncQueue,
        conflicts: this.conflicts,
        lastSyncTime: this.getLastSyncTime()?.getTime()
      }
      
      localStorage.setItem('cloud_sync_data', JSON.stringify(data))
    } catch (error) {
      console.error('Failed to save to local storage:', error)
    }
  }

  // 从本地存储恢复
  private restoreFromLocal(): void {
    try {
      const data = localStorage.getItem('cloud_sync_data')
      if (data) {
        const parsed = JSON.parse(data)
        
        this.localData = new Map(Object.entries(parsed.localData || {}))
        this.cloudData = new Map(Object.entries(parsed.cloudData || {}))
        this.syncQueue = parsed.syncQueue || []
        this.conflicts = parsed.conflicts || []
        
        if (parsed.lastSyncTime) {
          this.setLastSyncTime(new Date(parsed.lastSyncTime))
        }
      }
    } catch (error) {
      console.error('Failed to restore from local storage:', error)
    }
  }

  // 获取最后同步时间
  private getLastSyncTime(): Date | null {
    const time = localStorage.getItem('last_sync_time')
    return time ? new Date(parseInt(time)) : null
  }

  // 设置最后同步时间
  private setLastSyncTime(time: Date): void {
    localStorage.setItem('last_sync_time', time.getTime().toString())
  }

  // 获取同步状态
  getStatus(): SyncStatus {
    const lastSyncTime = this.getLastSyncTime()
    const nextSyncTime = lastSyncTime && this.config.enableAutoSync
      ? new Date(lastSyncTime.getTime() + this.config.syncInterval)
      : null

    return {
      isOnline: navigator.onLine,
      isConnected: true, // 这里应该实际检查与服务器的连接
      isSyncing: this.syncQueue.some(op => op.status === 'syncing'),
      lastSyncTime,
      nextSyncTime,
      syncCount: 0, // 这里应该保存实际的同步计数
      errorCount: this.syncQueue.filter(op => op.status === 'failed').length,
      conflictCount: this.conflicts.filter(c => !c.resolved).length,
      pendingOperations: this.syncQueue.filter(op => op.status === 'pending').length,
      uploadProgress: 0,
      downloadProgress: 0
    }
  }

  // 获取所有冲突
  getConflicts(): ConflictInfo[] {
    return [...this.conflicts]
  }

  // 清理资源
  cleanup(): void {
    this.stopAutoSync()
    
    this.retryTimers.forEach(timer => clearTimeout(timer))
    this.retryTimers.clear()
    
    this.saveToLocal()
  }
}

// Composable 函数
export function useCloudSync<T>(
  key: string,
  defaultValue?: T,
  config: Partial<CloudSyncConfig> = {}
) {
  const route = useRoute()

  // 创建同步管理器
  const syncManager = new CloudSyncManager(config)

  // 响应式状态
  const value = ref<T>(syncManager.get(key, defaultValue) ?? defaultValue!)
  const isLoading = ref(false)
  const error = ref<string | null>(null)
  const lastUpdated = ref<Date | null>(null)
  const syncStatus = reactive<SyncStatus>(syncManager.getStatus())
  const conflicts = ref<ConflictInfo[]>([])

  // 更新同步状态
  const updateStatus = () => {
    Object.assign(syncStatus, syncManager.getStatus())
    conflicts.value = syncManager.getConflicts().filter(c => c.key === key)
  }

  // 设置值
  const setValue = (newValue: T, metadata?: Record<string, any>) => {
    try {
      isLoading.value = true
      error.value = null

      syncManager.set(key, newValue, metadata)
      value.value = newValue
      lastUpdated.value = new Date()

      updateStatus()
      ElMessage.success('数据已保存并开始同步')
    } catch (err) {
      error.value = err instanceof Error ? err.message : String(err)
      ElMessage.error('保存失败: ' + error.value)
    } finally {
      isLoading.value = false
    }
  }

  // 获取值
  const getValue = (): T | undefined => {
    return syncManager.get(key, defaultValue)
  }

  // 删除值
  const deleteValue = () => {
    try {
      syncManager.delete(key)
      value.value = defaultValue!
      lastUpdated.value = new Date()

      updateStatus()
      ElMessage.success('数据已删除')
    } catch (err) {
      error.value = err instanceof Error ? err.message : String(err)
      ElMessage.error('删除失败: ' + error.value)
    }
  }

  // 手动同步
  const manualSync = async () => {
    try {
      isLoading.value = true
      error.value = null

      const success = await syncManager.sync()
      
      if (success) {
        // 更新本地值
        const latestValue = syncManager.get(key, defaultValue)
        if (latestValue !== undefined) {
          value.value = latestValue
        }
        
        lastUpdated.value = new Date()
        ElMessage.success('同步完成')
      } else {
        ElMessage.warning('同步未完全成功，请检查网络连接')
      }

      updateStatus()
    } catch (err) {
      error.value = err instanceof Error ? err.message : String(err)
      ElMessage.error('同步失败: ' + error.value)
    } finally {
      isLoading.value = false
    }
  }

  // 解决冲突
  const resolveConflict = (conflictIndex: number, resolution: 'local' | 'remote' | 'merge') => {
    const conflict = conflicts.value[conflictIndex]
    if (conflict) {
      syncManager.resolveConflict(conflict, resolution)
      
      // 更新本地值
      const latestValue = syncManager.get(key, defaultValue)
      if (latestValue !== undefined) {
        value.value = latestValue
      }
      
      updateStatus()
      ElMessage.success('冲突已解决')
    }
  }

  // 监听值变化
  watch(
    value,
    (newValue) => {
      if (config.enableAutoSync !== false) {
        syncManager.set(key, newValue)
        updateStatus()
      }
    },
    { deep: true }
  )

  // 定期更新状态
  const statusTimer = setInterval(updateStatus, 5000)

  // 计算属性
  const hasConflicts = computed(() => conflicts.value.some(c => !c.resolved))
  const canSync = computed(() => syncStatus.isOnline && !syncStatus.isSyncing)
  const needsSync = computed(() => syncStatus.pendingOperations > 0)

  // 清理函数
  const cleanup = () => {
    clearInterval(statusTimer)
    syncManager.cleanup()
  }

  // 组件卸载时清理
  onUnmounted(cleanup)

  // 初始化状态
  updateStatus()

  return {
    // 状态
    value,
    isLoading,
    error,
    lastUpdated,
    syncStatus,
    conflicts,

    // 计算属性
    hasConflicts,
    canSync,
    needsSync,

    // 方法
    setValue,
    getValue,
    deleteValue,
    manualSync,
    resolveConflict,
    cleanup,

    // 同步管理器
    syncManager
  }
}

// 导出云端同步管理器类
export { CloudSyncManager }

// 类型导出
export type { CloudSyncConfig, CloudDataItem, SyncOperation, ConflictInfo, SyncStatus }