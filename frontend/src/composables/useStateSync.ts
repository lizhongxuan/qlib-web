import { ref, reactive, watch, onUnmounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { throttle, debounce, isEqual, cloneDeep } from 'lodash-es'

// 状态同步配置接口
interface StateSyncConfig {
  enabled: boolean
  syncInterval: number // 同步间隔（毫秒）
  conflictResolution: 'local' | 'remote' | 'merge' | 'manual'
  maxRetries: number
  retryDelay: number
  compressionEnabled: boolean
  encryptionEnabled: boolean
  offlineSupport: boolean
  broadcastChanges: boolean // 是否广播变更给其他标签页
}

// 同步状态
interface SyncState {
  isOnline: boolean
  isSyncing: boolean
  lastSyncTime: Date | null
  syncCount: number
  errorCount: number
  conflictCount: number
  pendingChanges: number
}

// 同步记录
interface SyncRecord {
  id: string
  timestamp: number
  type: 'push' | 'pull' | 'conflict'
  data: any
  success: boolean
  error?: string
  conflicts?: ConflictInfo[]
}

// 冲突信息
interface ConflictInfo {
  field: string
  localValue: any
  remoteValue: any
  resolved: boolean
  resolution?: 'local' | 'remote' | 'merge'
}

// 状态变更事件
interface StateChangeEvent {
  source: string
  timestamp: number
  changes: Record<string, any>
  route: string
}

// 跨页面状态同步管理器
class StateSyncManager {
  private syncChannels: Map<string, BroadcastChannel> = new Map()
  private syncTimers: Map<string, NodeJS.Timeout> = new Map()
  private pendingChanges: Map<string, any> = new Map()
  private lastSyncData: Map<string, any> = new Map()
  private conflictResolvers: Map<string, (conflicts: ConflictInfo[]) => Promise<ConflictInfo[]>> = new Map()

  // 创建同步通道
  createSyncChannel(channelName: string): BroadcastChannel {
    if (this.syncChannels.has(channelName)) {
      return this.syncChannels.get(channelName)!
    }

    const channel = new BroadcastChannel(`state_sync_${channelName}`)
    this.syncChannels.set(channelName, channel)
    return channel
  }

  // 广播状态变更
  broadcastChange(channelName: string, changes: StateChangeEvent): void {
    const channel = this.syncChannels.get(channelName)
    if (channel) {
      channel.postMessage({
        type: 'state_change',
        payload: changes
      })
    }
  }

  // 监听状态变更
  listenToChanges(
    channelName: string, 
    callback: (event: StateChangeEvent) => void
  ): () => void {
    const channel = this.createSyncChannel(channelName)
    
    const handler = (event: MessageEvent) => {
      if (event.data.type === 'state_change') {
        callback(event.data.payload)
      }
    }

    channel.addEventListener('message', handler)

    return () => {
      channel.removeEventListener('message', handler)
    }
  }

  // 同步到远程服务器
  async syncToRemote(key: string, data: any, config: StateSyncConfig): Promise<boolean> {
    try {
      // 这里应该实现实际的远程同步逻辑
      // 模拟网络请求
      await new Promise(resolve => setTimeout(resolve, 500))
      
      // 模拟成功
      return Math.random() > 0.1 // 90% 成功率
    } catch (error) {
      console.error('Remote sync failed:', error)
      return false
    }
  }

  // 从远程服务器拉取
  async pullFromRemote(key: string, config: StateSyncConfig): Promise<any> {
    try {
      // 这里应该实现实际的远程拉取逻辑
      // 模拟网络请求
      await new Promise(resolve => setTimeout(resolve, 300))
      
      // 模拟返回数据
      return null // 无远程数据
    } catch (error) {
      console.error('Remote pull failed:', error)
      return null
    }
  }

  // 检测冲突
  detectConflicts(localData: any, remoteData: any): ConflictInfo[] {
    const conflicts: ConflictInfo[] = []
    
    const checkObject = (local: any, remote: any, path: string = '') => {
      for (const key in remote) {
        const currentPath = path ? `${path}.${key}` : key
        
        if (!(key in local)) {
          // 远程有，本地没有
          conflicts.push({
            field: currentPath,
            localValue: undefined,
            remoteValue: remote[key],
            resolved: false
          })
        } else if (!isEqual(local[key], remote[key])) {
          if (typeof local[key] === 'object' && typeof remote[key] === 'object') {
            checkObject(local[key], remote[key], currentPath)
          } else {
            conflicts.push({
              field: currentPath,
              localValue: local[key],
              remoteValue: remote[key],
              resolved: false
            })
          }
        }
      }
    }

    if (remoteData && localData) {
      checkObject(localData, remoteData)
    }

    return conflicts
  }

  // 解决冲突
  resolveConflicts(
    conflicts: ConflictInfo[], 
    strategy: StateSyncConfig['conflictResolution']
  ): any {
    const resolved: any = {}

    conflicts.forEach(conflict => {
      switch (strategy) {
        case 'local':
          resolved[conflict.field] = conflict.localValue
          break
        case 'remote':
          resolved[conflict.field] = conflict.remoteValue
          break
        case 'merge':
          // 简单的合并策略
          if (Array.isArray(conflict.localValue) && Array.isArray(conflict.remoteValue)) {
            resolved[conflict.field] = [...conflict.localValue, ...conflict.remoteValue]
          } else {
            resolved[conflict.field] = conflict.remoteValue
          }
          break
        default:
          resolved[conflict.field] = conflict.localValue
      }
    })

    return resolved
  }

  // 清理资源
  cleanup(): void {
    for (const timer of this.syncTimers.values()) {
      clearInterval(timer)
    }
    this.syncTimers.clear()

    for (const channel of this.syncChannels.values()) {
      channel.close()
    }
    this.syncChannels.clear()
  }
}

// 全局管理器实例
const stateSyncManager = new StateSyncManager()

// Composable 函数
export function useStateSync(
  stateData: any,
  syncKey: string = 'default',
  initialConfig: Partial<StateSyncConfig> = {}
) {
  const route = useRoute()
  const router = useRouter()

  // 默认配置
  const defaultConfig: StateSyncConfig = {
    enabled: true,
    syncInterval: 10000, // 10秒
    conflictResolution: 'local',
    maxRetries: 3,
    retryDelay: 1000,
    compressionEnabled: false,
    encryptionEnabled: false,
    offlineSupport: true,
    broadcastChanges: true
  }

  // 合并配置
  const config = reactive({ ...defaultConfig, ...initialConfig })

  // 同步状态
  const syncState = reactive<SyncState>({
    isOnline: navigator.onLine,
    isSyncing: false,
    lastSyncTime: null,
    syncCount: 0,
    errorCount: 0,
    conflictCount: 0,
    pendingChanges: 0
  })

  // 同步历史
  const syncHistory = ref<SyncRecord[]>([])
  const conflicts = ref<ConflictInfo[]>([])
  
  // 内部状态
  const channelName = `${syncKey}_${route.path}`
  let lastStateSnapshot: any = null
  let changeBuffer: any[] = []
  let retryCount = 0

  // 初始化
  const initialize = () => {
    lastStateSnapshot = cloneDeep(stateData)
    
    if (config.enabled) {
      setupSync()
      setupNetworkListeners()
      
      if (config.broadcastChanges) {
        setupBroadcastListeners()
      }
    }
  }

  // 设置同步
  const setupSync = () => {
    // 监听状态变化
    const debouncedSync = debounce(performSync, 1000)
    
    watch(
      () => stateData,
      (newState) => {
        if (!isEqual(newState, lastStateSnapshot)) {
          recordChange(newState)
          if (config.broadcastChanges) {
            broadcastStateChange(newState)
          }
          debouncedSync()
        }
      },
      { deep: true }
    )

    // 定期同步
    const syncTimer = setInterval(() => {
      if (syncState.pendingChanges > 0 || shouldPerformPeriodicSync()) {
        performSync()
      }
    }, config.syncInterval)

    stateSyncManager['syncTimers'].set(channelName, syncTimer)
  }

  // 设置网络监听
  const setupNetworkListeners = () => {
    const handleOnline = () => {
      syncState.isOnline = true
      ElMessage.success('网络连接已恢复')
      
      // 网络恢复后立即同步
      if (syncState.pendingChanges > 0) {
        performSync()
      }
    }

    const handleOffline = () => {
      syncState.isOnline = false
      if (config.offlineSupport) {
        ElMessage.warning('网络连接断开，将在离线模式下工作')
      } else {
        ElMessage.error('网络连接断开')
      }
    }

    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)

    // 清理函数
    onUnmounted(() => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
    })
  }

  // 设置广播监听
  const setupBroadcastListeners = () => {
    const unsubscribe = stateSyncManager.listenToChanges(
      channelName,
      handleRemoteStateChange
    )

    onUnmounted(unsubscribe)
  }

  // 记录变更
  const recordChange = (newState: any) => {
    const changes = getChanges(lastStateSnapshot, newState)
    if (Object.keys(changes).length > 0) {
      changeBuffer.push({
        timestamp: Date.now(),
        changes,
        route: route.path
      })
      syncState.pendingChanges = changeBuffer.length
      lastStateSnapshot = cloneDeep(newState)
    }
  }

  // 获取变更差异
  const getChanges = (oldState: any, newState: any): Record<string, any> => {
    const changes: Record<string, any> = {}
    
    const compareObjects = (old: any, current: any, path: string = '') => {
      for (const key in current) {
        const currentPath = path ? `${path}.${key}` : key
        
        if (!(key in old) || !isEqual(old[key], current[key])) {
          changes[currentPath] = current[key]
        }
      }
    }

    compareObjects(oldState, newState)
    return changes
  }

  // 广播状态变更
  const broadcastStateChange = (newState: any) => {
    const changeEvent: StateChangeEvent = {
      source: 'local',
      timestamp: Date.now(),
      changes: getChanges(lastStateSnapshot, newState),
      route: route.path
    }

    stateSyncManager.broadcastChange(channelName, changeEvent)
  }

  // 处理远程状态变更
  const handleRemoteStateChange = (event: StateChangeEvent) => {
    if (event.source === 'local') return // 忽略自己的变更

    // 检测冲突
    const eventConflicts = stateSyncManager.detectConflicts(stateData, event.changes)
    
    if (eventConflicts.length > 0) {
      conflicts.value.push(...eventConflicts)
      syncState.conflictCount += eventConflicts.length
      
      if (config.conflictResolution !== 'manual') {
        resolveConflictsAutomatically(eventConflicts)
      } else {
        ElMessage.warning(`检测到 ${eventConflicts.length} 个数据冲突，需要手动解决`)
      }
    } else {
      // 无冲突，直接应用变更
      applyChanges(event.changes)
    }
  }

  // 执行同步
  const performSync = async () => {
    if (syncState.isSyncing || !config.enabled) return

    try {
      syncState.isSyncing = true
      
      const syncRecord: SyncRecord = {
        id: `sync_${Date.now()}`,
        timestamp: Date.now(),
        type: 'push',
        data: cloneDeep(stateData),
        success: false
      }

      // 推送本地变更
      if (syncState.isOnline && changeBuffer.length > 0) {
        const success = await stateSyncManager.syncToRemote(
          channelName,
          changeBuffer,
          config
        )

        if (success) {
          changeBuffer = []
          syncState.pendingChanges = 0
          syncState.syncCount++
          retryCount = 0
          syncRecord.success = true
        } else {
          handleSyncError(syncRecord)
        }
      }

      // 拉取远程变更
      if (syncState.isOnline) {
        const remoteData = await stateSyncManager.pullFromRemote(channelName, config)
        
        if (remoteData) {
          await handleRemoteData(remoteData)
        }
      }

      syncState.lastSyncTime = new Date()
      syncHistory.value.push(syncRecord)
      
      // 限制历史记录数量
      if (syncHistory.value.length > 50) {
        syncHistory.value = syncHistory.value.slice(-25)
      }

    } catch (error) {
      console.error('Sync failed:', error)
      syncState.errorCount++
      ElMessage.error('状态同步失败')
    } finally {
      syncState.isSyncing = false
    }
  }

  // 处理同步错误
  const handleSyncError = (syncRecord: SyncRecord) => {
    syncState.errorCount++
    retryCount++

    if (retryCount <= config.maxRetries) {
      setTimeout(() => {
        performSync()
      }, config.retryDelay * retryCount)
    } else {
      ElMessage.error('同步失败次数过多，请检查网络连接')
      retryCount = 0
    }
  }

  // 处理远程数据
  const handleRemoteData = async (remoteData: any) => {
    const detectedConflicts = stateSyncManager.detectConflicts(stateData, remoteData)
    
    if (detectedConflicts.length > 0) {
      conflicts.value.push(...detectedConflicts)
      syncState.conflictCount += detectedConflicts.length

      if (config.conflictResolution !== 'manual') {
        await resolveConflictsAutomatically(detectedConflicts)
      }
    } else {
      applyChanges(remoteData)
    }
  }

  // 自动解决冲突
  const resolveConflictsAutomatically = async (conflictList: ConflictInfo[]) => {
    const resolved = stateSyncManager.resolveConflicts(conflictList, config.conflictResolution)
    applyChanges(resolved)
    
    // 标记冲突为已解决
    conflictList.forEach(conflict => {
      conflict.resolved = true
      conflict.resolution = config.conflictResolution
    })
  }

  // 应用变更
  const applyChanges = (changes: Record<string, any>) => {
    Object.assign(stateData, changes)
    lastStateSnapshot = cloneDeep(stateData)
  }

  // 手动解决冲突
  const resolveConflict = (conflictIndex: number, resolution: 'local' | 'remote' | 'merge') => {
    const conflict = conflicts.value[conflictIndex]
    if (conflict) {
      let resolvedValue
      
      switch (resolution) {
        case 'local':
          resolvedValue = conflict.localValue
          break
        case 'remote':
          resolvedValue = conflict.remoteValue
          break
        case 'merge':
          // 简单合并逻辑
          if (Array.isArray(conflict.localValue) && Array.isArray(conflict.remoteValue)) {
            resolvedValue = [...conflict.localValue, ...conflict.remoteValue]
          } else {
            resolvedValue = conflict.remoteValue
          }
          break
      }

      // 应用解决方案
      const changes = { [conflict.field]: resolvedValue }
      applyChanges(changes)
      
      // 标记为已解决
      conflict.resolved = true
      conflict.resolution = resolution
      
      ElMessage.success('冲突已解决')
    }
  }

  // 手动触发同步
  const manualSync = async () => {
    await performSync()
  }

  // 重置同步状态
  const resetSync = () => {
    changeBuffer = []
    syncState.pendingChanges = 0
    syncState.errorCount = 0
    syncState.conflictCount = 0
    conflicts.value = []
    retryCount = 0
    ElMessage.success('同步状态已重置')
  }

  // 导出同步数据
  const exportSyncData = () => {
    return JSON.stringify({
      stateData: cloneDeep(stateData),
      syncHistory: syncHistory.value,
      conflicts: conflicts.value,
      syncState,
      exportTime: new Date().toISOString()
    }, null, 2)
  }

  // 获取同步统计
  const getSyncStats = () => {
    return {
      isOnline: syncState.isOnline,
      isSyncing: syncState.isSyncing,
      lastSyncTime: syncState.lastSyncTime,
      syncCount: syncState.syncCount,
      errorCount: syncState.errorCount,
      conflictCount: syncState.conflictCount,
      pendingChanges: syncState.pendingChanges,
      historySize: syncHistory.value.length,
      activeConflicts: conflicts.value.filter(c => !c.resolved).length
    }
  }

  // 判断是否需要定期同步
  const shouldPerformPeriodicSync = (): boolean => {
    if (!syncState.lastSyncTime) return true
    
    const timeSinceLastSync = Date.now() - syncState.lastSyncTime.getTime()
    return timeSinceLastSync > config.syncInterval * 2
  }

  // 清理函数
  const cleanup = () => {
    const timer = stateSyncManager['syncTimers'].get(channelName)
    if (timer) {
      clearInterval(timer)
      stateSyncManager['syncTimers'].delete(channelName)
    }
  }

  // 组件卸载时清理
  onUnmounted(cleanup)

  // 初始化
  nextTick(initialize)

  return {
    // 状态
    syncState,
    syncHistory,
    conflicts,
    config,

    // 方法
    manualSync,
    resetSync,
    resolveConflict,
    exportSyncData,
    getSyncStats,
    cleanup
  }
}

// 导出管理器实例
export { stateSyncManager }

// 类型导出
export type { 
  StateSyncConfig, 
  SyncState, 
  SyncRecord, 
  ConflictInfo, 
  StateChangeEvent 
}