import { ref, reactive, watch, onUnmounted, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElNotification } from 'element-plus'
import { debounce, isEqual, cloneDeep } from 'lodash-es'

// 自动保存配置接口
interface AutoSaveConfig {
  enabled: boolean
  interval: number // 自动保存间隔（毫秒）
  debounceDelay: number // 防抖延迟（毫秒）
  maxVersions: number // 最大保存版本数
  showNotifications: boolean // 是否显示保存通知
  saveOnBlur: boolean // 失去焦点时保存
  saveOnRoute: boolean // 路由切换时保存
  compression: boolean // 是否压缩数据
  encryption: boolean // 是否加密数据
}

// 保存记录接口
interface SaveRecord {
  id: string
  timestamp: number
  data: any
  formType: string
  route: string
  version: number
  comment?: string
  compressed?: boolean
  encrypted?: boolean
}

// 表单状态接口
interface FormState {
  isDirty: boolean
  isValid: boolean
  hasChanges: boolean
  lastSaved: Date | null
  saveCount: number
  errors: string[]
}

// 冲突解决策略
type ConflictResolution = 'local' | 'remote' | 'merge' | 'ask'

// 表单自动保存管理器
class FormAutoSaveManager {
  private saves: Map<string, SaveRecord[]> = new Map()
  private watchers: Map<string, any> = new Map()
  private intervals: Map<string, NodeJS.Timeout> = new Map()
  private formStates: Map<string, FormState> = new Map()

  // 获取保存键
  private getSaveKey(formType: string, route: string): string {
    return `${formType}_${route.replace(/\//g, '_')}`
  }

  // 保存数据到本地存储
  saveToStorage(key: string, data: any, config: AutoSaveConfig): SaveRecord {
    const saveRecord: SaveRecord = {
      id: `save_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      timestamp: Date.now(),
      data: config.compression ? this.compressData(data) : data,
      formType: key.split('_')[0],
      route: key.split('_').slice(1).join('/'),
      version: this.getNextVersion(key),
      compressed: config.compression,
      encrypted: config.encryption
    }

    // 加密数据
    if (config.encryption) {
      saveRecord.data = this.encryptData(saveRecord.data)
    }

    // 获取现有保存记录
    const existingSaves = this.saves.get(key) || []
    
    // 添加新记录
    existingSaves.push(saveRecord)
    
    // 限制版本数量
    if (existingSaves.length > config.maxVersions) {
      existingSaves.splice(0, existingSaves.length - config.maxVersions)
    }
    
    this.saves.set(key, existingSaves)
    
    // 持久化到 localStorage
    try {
      localStorage.setItem(`autosave_${key}`, JSON.stringify(existingSaves))
    } catch (error) {
      console.error('Failed to save to localStorage:', error)
    }

    return saveRecord
  }

  // 从本地存储加载数据
  loadFromStorage(key: string): SaveRecord[] {
    try {
      const cached = this.saves.get(key)
      if (cached) return cached

      const stored = localStorage.getItem(`autosave_${key}`)
      if (stored) {
        const records = JSON.parse(stored) as SaveRecord[]
        this.saves.set(key, records)
        return records
      }
    } catch (error) {
      console.error('Failed to load from localStorage:', error)
    }
    return []
  }

  // 获取最新保存记录
  getLatestSave(key: string): SaveRecord | null {
    const saves = this.loadFromStorage(key)
    return saves.length > 0 ? saves[saves.length - 1] : null
  }

  // 获取下一个版本号
  private getNextVersion(key: string): number {
    const saves = this.loadFromStorage(key)
    return saves.length > 0 ? Math.max(...saves.map(s => s.version)) + 1 : 1
  }

  // 删除保存记录
  deleteSave(key: string, saveId?: string): boolean {
    try {
      if (saveId) {
        const saves = this.loadFromStorage(key)
        const filtered = saves.filter(s => s.id !== saveId)
        this.saves.set(key, filtered)
        localStorage.setItem(`autosave_${key}`, JSON.stringify(filtered))
      } else {
        this.saves.delete(key)
        localStorage.removeItem(`autosave_${key}`)
      }
      return true
    } catch (error) {
      console.error('Failed to delete save:', error)
      return false
    }
  }

  // 清理过期数据
  cleanup(maxAge: number = 7 * 24 * 60 * 60 * 1000): void {
    const cutoff = Date.now() - maxAge
    
    for (const [key, saves] of this.saves.entries()) {
      const filtered = saves.filter(save => save.timestamp > cutoff)
      if (filtered.length !== saves.length) {
        this.saves.set(key, filtered)
        if (filtered.length > 0) {
          localStorage.setItem(`autosave_${key}`, JSON.stringify(filtered))
        } else {
          localStorage.removeItem(`autosave_${key}`)
        }
      }
    }
  }

  // 获取表单状态
  getFormState(key: string): FormState {
    return this.formStates.get(key) || {
      isDirty: false,
      isValid: true,
      hasChanges: false,
      lastSaved: null,
      saveCount: 0,
      errors: []
    }
  }

  // 更新表单状态
  setFormState(key: string, state: Partial<FormState>): void {
    const current = this.getFormState(key)
    this.formStates.set(key, { ...current, ...state })
  }

  // 数据压缩（简单的JSON压缩）
  private compressData(data: any): string {
    return JSON.stringify(data)
  }

  // 数据解压缩
  private decompressData(data: string): any {
    return JSON.parse(data)
  }

  // 数据加密（简单的Base64编码，实际应用中应使用更安全的加密）
  private encryptData(data: any): string {
    return btoa(JSON.stringify(data))
  }

  // 数据解密
  private decryptData(data: string): any {
    return JSON.parse(atob(data))
  }

  // 获取统计信息
  getStats(): { totalSaves: number; totalSize: number; formCount: number } {
    let totalSaves = 0
    let totalSize = 0
    let formCount = this.saves.size

    for (const saves of this.saves.values()) {
      totalSaves += saves.length
      totalSize += JSON.stringify(saves).length
    }

    return { totalSaves, totalSize, formCount }
  }
}

// 全局管理器实例
const autoSaveManager = new FormAutoSaveManager()

// Composable 函数
export function useFormAutoSave(
  formData: any,
  formType: string = 'default',
  initialConfig: Partial<AutoSaveConfig> = {}
) {
  const route = useRoute()

  // 默认配置
  const defaultConfig: AutoSaveConfig = {
    enabled: true,
    interval: 30000, // 30秒
    debounceDelay: 2000, // 2秒
    maxVersions: 10,
    showNotifications: false,
    saveOnBlur: true,
    saveOnRoute: true,
    compression: false,
    encryption: false
  }

  // 合并配置
  const config = reactive({ ...defaultConfig, ...initialConfig })
  
  // 状态
  const isAutoSaving = ref(false)
  const lastSaveTime = ref<Date | null>(null)
  const saveHistory = ref<SaveRecord[]>([])
  const hasUnsavedChanges = ref(false)
  const saveKey = ref('')
  
  // 表单状态
  const formState = reactive<FormState>({
    isDirty: false,
    isValid: true,
    hasChanges: false,
    lastSaved: null,
    saveCount: 0,
    errors: []
  })

  // 初始数据快照
  let initialSnapshot: any = null
  let lastSavedSnapshot: any = null

  // 初始化
  const initialize = () => {
    saveKey.value = autoSaveManager['getSaveKey'](formType, route.path)
    initialSnapshot = cloneDeep(formData)
    lastSavedSnapshot = cloneDeep(formData)
    
    // 加载保存历史
    loadSaveHistory()
    
    // 设置监听器
    setupWatchers()
    
    // 设置自动保存间隔
    if (config.enabled) {
      setupAutoSaveInterval()
    }
  }

  // 加载保存历史
  const loadSaveHistory = () => {
    saveHistory.value = autoSaveManager.loadFromStorage(saveKey.value)
    const latestSave = autoSaveManager.getLatestSave(saveKey.value)
    if (latestSave) {
      lastSaveTime.value = new Date(latestSave.timestamp)
      formState.lastSaved = lastSaveTime.value
      formState.saveCount = saveHistory.value.length
    }
  }

  // 设置监听器
  const setupWatchers = () => {
    // 监听表单数据变化
    const debouncedSave = debounce(performAutoSave, config.debounceDelay)
    
    const stopWatcher = watch(
      () => formData,
      (newData) => {
        checkForChanges(newData)
        if (config.enabled && hasUnsavedChanges.value) {
          debouncedSave()
        }
      },
      { deep: true }
    )

    // 保存监听器引用以便清理
    autoSaveManager['watchers'].set(saveKey.value, stopWatcher)

    // 监听路由变化
    if (config.saveOnRoute) {
      watch(
        () => route.path,
        () => {
          if (hasUnsavedChanges.value) {
            performSave('路由切换自动保存')
          }
        }
      )
    }
  }

  // 设置自动保存间隔
  const setupAutoSaveInterval = () => {
    if (autoSaveManager['intervals'].has(saveKey.value)) {
      clearInterval(autoSaveManager['intervals'].get(saveKey.value))
    }

    const interval = setInterval(() => {
      if (hasUnsavedChanges.value) {
        performAutoSave()
      }
    }, config.interval)

    autoSaveManager['intervals'].set(saveKey.value, interval)
  }

  // 检查数据变化
  const checkForChanges = (newData: any) => {
    const hasChangesFromInitial = !isEqual(newData, initialSnapshot)
    const hasChangesFromLastSave = !isEqual(newData, lastSavedSnapshot)
    
    hasUnsavedChanges.value = hasChangesFromLastSave
    formState.isDirty = hasChangesFromInitial
    formState.hasChanges = hasChangesFromLastSave
    
    autoSaveManager.setFormState(saveKey.value, formState)
  }

  // 执行自动保存
  const performAutoSave = async () => {
    if (!config.enabled || !hasUnsavedChanges.value || isAutoSaving.value) {
      return
    }

    await performSave('自动保存')
  }

  // 执行保存
  const performSave = async (comment?: string) => {
    try {
      isAutoSaving.value = true

      const saveRecord = autoSaveManager.saveToStorage(
        saveKey.value,
        cloneDeep(formData),
        config
      )

      if (comment) {
        saveRecord.comment = comment
      }

      // 更新状态
      lastSaveTime.value = new Date(saveRecord.timestamp)
      lastSavedSnapshot = cloneDeep(formData)
      hasUnsavedChanges.value = false
      
      formState.lastSaved = lastSaveTime.value
      formState.saveCount++
      formState.hasChanges = false
      
      autoSaveManager.setFormState(saveKey.value, formState)

      // 更新历史记录
      saveHistory.value.push(saveRecord)
      if (saveHistory.value.length > config.maxVersions) {
        saveHistory.value.shift()
      }

      // 显示通知
      if (config.showNotifications) {
        ElMessage.success('表单已自动保存')
      }

      return saveRecord
    } catch (error) {
      console.error('Auto save failed:', error)
      ElMessage.error('自动保存失败')
      throw error
    } finally {
      isAutoSaving.value = false
    }
  }

  // 手动保存
  const save = async (comment?: string) => {
    return await performSave(comment || '手动保存')
  }

  // 恢复数据
  const restore = async (saveId?: string): Promise<any> => {
    try {
      const saves = autoSaveManager.loadFromStorage(saveKey.value)
      let targetSave: SaveRecord | null = null

      if (saveId) {
        targetSave = saves.find(s => s.id === saveId) || null
      } else {
        targetSave = autoSaveManager.getLatestSave(saveKey.value)
      }

      if (!targetSave) {
        throw new Error('未找到保存记录')
      }

      let restoredData = targetSave.data

      // 解密数据
      if (targetSave.encrypted) {
        restoredData = autoSaveManager['decryptData'](restoredData)
      }

      // 解压缩数据
      if (targetSave.compressed) {
        restoredData = autoSaveManager['decompressData'](restoredData)
      }

      // 更新表单数据
      Object.assign(formData, restoredData)
      
      // 更新快照
      lastSavedSnapshot = cloneDeep(restoredData)
      hasUnsavedChanges.value = false
      formState.hasChanges = false
      
      ElMessage.success('数据恢复成功')
      return restoredData
    } catch (error) {
      console.error('Restore failed:', error)
      ElMessage.error('数据恢复失败')
      throw error
    }
  }

  // 清除保存数据
  const clearSaves = () => {
    autoSaveManager.deleteSave(saveKey.value)
    saveHistory.value = []
    lastSaveTime.value = null
    formState.lastSaved = null
    formState.saveCount = 0
    ElMessage.success('已清除所有保存记录')
  }

  // 删除特定保存记录
  const deleteSave = (saveId: string) => {
    autoSaveManager.deleteSave(saveKey.value, saveId)
    saveHistory.value = saveHistory.value.filter(s => s.id !== saveId)
    ElMessage.success('保存记录已删除')
  }

  // 导出保存数据
  const exportSaves = (): string => {
    const saves = autoSaveManager.loadFromStorage(saveKey.value)
    return JSON.stringify({
      formType,
      route: route.path,
      exportTime: new Date().toISOString(),
      saves
    }, null, 2)
  }

  // 导入保存数据
  const importSaves = (data: string): boolean => {
    try {
      const imported = JSON.parse(data)
      if (imported.saves && Array.isArray(imported.saves)) {
        autoSaveManager['saves'].set(saveKey.value, imported.saves)
        localStorage.setItem(`autosave_${saveKey.value}`, JSON.stringify(imported.saves))
        loadSaveHistory()
        ElMessage.success('保存数据导入成功')
        return true
      } else {
        throw new Error('无效的导入数据格式')
      }
    } catch (error) {
      ElMessage.error('导入失败: ' + (error as Error).message)
      return false
    }
  }

  // 检查是否有更新的远程数据
  const checkForConflicts = async (): Promise<ConflictResolution | null> => {
    // 这里应该实现与服务器的冲突检查逻辑
    // 返回建议的解决策略
    return null
  }

  // 启用/禁用自动保存
  const toggleAutoSave = (enabled: boolean) => {
    config.enabled = enabled
    if (enabled) {
      setupAutoSaveInterval()
    } else {
      const interval = autoSaveManager['intervals'].get(saveKey.value)
      if (interval) {
        clearInterval(interval)
        autoSaveManager['intervals'].delete(saveKey.value)
      }
    }
  }

  // 获取保存统计
  const getSaveStats = () => {
    return {
      totalSaves: saveHistory.value.length,
      lastSaveTime: lastSaveTime.value,
      hasUnsavedChanges: hasUnsavedChanges.value,
      autoSaveEnabled: config.enabled,
      ...autoSaveManager.getStats()
    }
  }

  // 监听页面失去焦点
  if (config.saveOnBlur) {
    window.addEventListener('beforeunload', (e) => {
      if (hasUnsavedChanges.value) {
        e.preventDefault()
        e.returnValue = '您有未保存的更改，确定要离开吗？'
        performSave('页面关闭前保存')
      }
    })
  }

  // 清理函数
  const cleanup = () => {
    const watcher = autoSaveManager['watchers'].get(saveKey.value)
    if (watcher) {
      watcher()
      autoSaveManager['watchers'].delete(saveKey.value)
    }

    const interval = autoSaveManager['intervals'].get(saveKey.value)
    if (interval) {
      clearInterval(interval)
      autoSaveManager['intervals'].delete(saveKey.value)
    }
  }

  // 组件卸载时清理
  onUnmounted(cleanup)

  // 初始化
  nextTick(initialize)

  return {
    // 状态
    isAutoSaving,
    lastSaveTime,
    saveHistory,
    hasUnsavedChanges,
    formState,
    config,

    // 方法
    save,
    restore,
    clearSaves,
    deleteSave,
    exportSaves,
    importSaves,
    checkForConflicts,
    toggleAutoSave,
    getSaveStats,
    cleanup
  }
}

// 导出管理器实例
export { autoSaveManager }

// 全局清理函数
export const cleanupAutoSave = () => {
  autoSaveManager.cleanup()
}

// 类型导出
export type { AutoSaveConfig, SaveRecord, FormState, ConflictResolution }