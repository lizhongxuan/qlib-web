import { ref, reactive, computed, watch, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { useDataTransfer } from './useDataTransfer'
import { ElMessage } from 'element-plus'

// 预填充规则接口
interface PreFillRule {
  id: string
  name: string
  condition: (context: PreFillContext) => boolean
  action: (context: PreFillContext, formData: any) => any
  priority: number
  enabled: boolean
}

// 预填充上下文
interface PreFillContext {
  route: string
  transferData?: any
  userHistory: any[]
  formType: string
  currentFormData: any
  userPreferences: any
  marketConditions?: any
}

// 表单字段配置
interface FieldConfig {
  name: string
  type: 'input' | 'select' | 'number' | 'date' | 'checkbox' | 'radio'
  defaultValue?: any
  dependencies?: string[]
  validation?: (value: any) => boolean
  transform?: (value: any, context: PreFillContext) => any
}

// 智能预填充管理器
class SmartPreFillManager {
  private rules: Map<string, PreFillRule> = new Map()
  private userHistory: any[] = []
  private userPreferences: any = {}
  private fieldConfigs: Map<string, FieldConfig> = new Map()

  // 注册预填充规则
  registerRule(rule: PreFillRule): void {
    this.rules.set(rule.id, rule)
  }

  // 移除规则
  removeRule(ruleId: string): boolean {
    return this.rules.delete(ruleId)
  }

  // 获取所有规则
  getRules(): PreFillRule[] {
    return Array.from(this.rules.values()).sort((a, b) => b.priority - a.priority)
  }

  // 注册字段配置
  registerFieldConfig(config: FieldConfig): void {
    this.fieldConfigs.set(config.name, config)
  }

  // 设置用户历史记录
  setUserHistory(history: any[]): void {
    this.userHistory = history
  }

  // 设置用户偏好
  setUserPreferences(preferences: any): void {
    this.userPreferences = preferences
  }

  // 执行智能预填充
  executePreFill(context: PreFillContext, formData: any): any {
    let result = { ...formData }
    const appliedRules: string[] = []

    // 按优先级执行规则
    const enabledRules = this.getRules().filter(rule => rule.enabled)
    
    for (const rule of enabledRules) {
      try {
        if (rule.condition(context)) {
          result = rule.action(context, result)
          appliedRules.push(rule.name)
        }
      } catch (error) {
        console.error(`PreFill rule ${rule.id} execution failed:`, error)
      }
    }

    return {
      data: result,
      appliedRules
    }
  }

  // 获取字段建议值
  getFieldSuggestion(fieldName: string, context: PreFillContext): any {
    const config = this.fieldConfigs.get(fieldName)
    if (!config) return undefined

    // 从传递数据中获取
    if (context.transferData && context.transferData[fieldName]) {
      let value = context.transferData[fieldName]
      if (config.transform) {
        value = config.transform(value, context)
      }
      return value
    }

    // 从用户历史中获取最常用的值
    const historyValues = this.userHistory
      .filter(item => item[fieldName])
      .map(item => item[fieldName])

    if (historyValues.length > 0) {
      // 返回最频繁使用的值
      const frequencies = new Map()
      historyValues.forEach(value => {
        frequencies.set(value, (frequencies.get(value) || 0) + 1)
      })

      const mostFrequent = Array.from(frequencies.entries())
        .sort((a, b) => b[1] - a[1])[0]?.[0]

      return mostFrequent
    }

    // 返回默认值
    return config.defaultValue
  }
}

// 全局实例
const preFillManager = new SmartPreFillManager()

// 预定义规则
const defaultRules: PreFillRule[] = [
  // 因子传递规则
  {
    id: 'factor_transfer',
    name: '因子数据传递',
    condition: (context) => context.transferData?.transferType === 'factor',
    action: (context, formData) => ({
      ...formData,
      selectedFactors: context.transferData.selectedFactors || [context.transferData.id],
      factorExpressions: context.transferData.expressions || []
    }),
    priority: 100,
    enabled: true
  },

  // 模型传递规则
  {
    id: 'model_transfer',
    name: '模型数据传递',
    condition: (context) => context.transferData?.transferType === 'model',
    action: (context, formData) => ({
      ...formData,
      selectedModel: context.transferData.selectedModel || context.transferData.id,
      modelConfig: context.transferData.config || {}
    }),
    priority: 100,
    enabled: true
  },

  // 用户偏好规则
  {
    id: 'user_preferences',
    name: '用户偏好设置',
    condition: () => true,
    action: (context, formData) => {
      const preferences = context.userPreferences || {}
      return {
        ...formData,
        algorithm: formData.algorithm || preferences.preferredAlgorithm || 'LightGBM',
        dataSource: formData.dataSource || preferences.preferredDataSource || 'CSI300',
        timeRange: formData.timeRange || preferences.preferredTimeRange || '3years'
      }
    },
    priority: 50,
    enabled: true
  },

  // 历史成功配置规则
  {
    id: 'successful_config',
    name: '历史成功配置',
    condition: (context) => context.userHistory.length > 0,
    action: (context, formData) => {
      // 找到最近的成功配置
      const successfulConfigs = context.userHistory
        .filter(item => item.performance && item.performance > 0.1)
        .sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime())

      if (successfulConfigs.length > 0) {
        const bestConfig = successfulConfigs[0]
        return {
          ...formData,
          hyperparameters: formData.hyperparameters || bestConfig.hyperparameters,
          strategyConfig: formData.strategyConfig || bestConfig.strategyConfig
        }
      }
      return formData
    },
    priority: 70,
    enabled: true
  },

  // 市场环境适配规则
  {
    id: 'market_adaptation',
    name: '市场环境适配',
    condition: (context) => !!context.marketConditions,
    action: (context, formData) => {
      const market = context.marketConditions
      const adaptedConfig = { ...formData }

      // 根据市场波动率调整参数
      if (market.volatility > 0.7) {
        adaptedConfig.riskControl = {
          ...adaptedConfig.riskControl,
          stopLoss: Math.min(adaptedConfig.riskControl?.stopLoss || 0.1, 0.08),
          maxDrawdown: Math.min(adaptedConfig.riskControl?.maxDrawdown || 0.15, 0.12)
        }
      }

      // 根据市场趋势调整策略
      if (market.trend === 'bear') {
        adaptedConfig.positionSize = Math.min(adaptedConfig.positionSize || 0.05, 0.03)
        adaptedConfig.rebalanceFreq = 'weekly'
      }

      return adaptedConfig
    },
    priority: 60,
    enabled: true
  },

  // 自动完成配置规则
  {
    id: 'auto_complete',
    name: '自动完成配置',
    condition: (context) => context.route.includes('auto'),
    action: (context, formData) => ({
      ...formData,
      quickMode: true,
      useRecommendedSettings: true,
      skipAdvancedConfig: true
    }),
    priority: 80,
    enabled: true
  }
]

// 注册默认规则
defaultRules.forEach(rule => preFillManager.registerRule(rule))

// Composable 函数
export function useSmartPreFill(formType: string = 'default') {
  const route = useRoute()
  const { currentTransfer } = useDataTransfer()

  // 响应式状态
  const isPreFilling = ref(false)
  const appliedRules = ref<string[]>([])
  const suggestions = ref<Record<string, any>>({})
  const formData = reactive<Record<string, any>>({})
  const preferencesLoaded = ref(false)

  // 用户历史和偏好
  const userHistory = ref<any[]>([])
  const userPreferences = ref<any>({})
  const marketConditions = ref<any>(null)

  // 预填充配置
  const preFillConfig = reactive({
    enabled: true,
    autoApply: true,
    showSuggestions: true,
    confirmBefore: false
  })

  // 执行智能预填充
  const executePreFill = async (targetFormData?: any) => {
    if (!preFillConfig.enabled) return targetFormData || {}

    try {
      isPreFilling.value = true

      const context: PreFillContext = {
        route: route.path,
        transferData: currentTransfer.value?.data,
        userHistory: userHistory.value,
        formType,
        currentFormData: targetFormData || formData,
        userPreferences: userPreferences.value,
        marketConditions: marketConditions.value
      }

      const result = preFillManager.executePreFill(context, targetFormData || formData)
      
      if (preFillConfig.autoApply) {
        Object.assign(formData, result.data)
      }

      appliedRules.value = result.appliedRules
      
      // 生成字段建议
      await generateSuggestions(context)

      if (result.appliedRules.length > 0) {
        ElMessage.success(`已应用 ${result.appliedRules.length} 条智能预填充规则`)
      }

      return result.data
    } catch (error) {
      console.error('Smart pre-fill execution failed:', error)
      ElMessage.error('智能预填充失败')
      return targetFormData || formData
    } finally {
      isPreFilling.value = false
    }
  }

  // 生成字段建议
  const generateSuggestions = async (context: PreFillContext) => {
    const newSuggestions: Record<string, any> = {}

    // 为每个已注册的字段生成建议
    for (const [fieldName] of preFillManager.fieldConfigs.entries()) {
      const suggestion = preFillManager.getFieldSuggestion(fieldName, context)
      if (suggestion !== undefined) {
        newSuggestions[fieldName] = suggestion
      }
    }

    suggestions.value = newSuggestions
  }

  // 应用单个字段建议
  const applySuggestion = (fieldName: string, value?: any) => {
    const suggestionValue = value ?? suggestions.value[fieldName]
    if (suggestionValue !== undefined) {
      formData[fieldName] = suggestionValue
      ElMessage.success(`已应用字段 ${fieldName} 的建议值`)
    }
  }

  // 应用所有建议
  const applyAllSuggestions = () => {
    Object.entries(suggestions.value).forEach(([fieldName, value]) => {
      if (value !== undefined && formData[fieldName] === undefined) {
        formData[fieldName] = value
      }
    })
    ElMessage.success(`已应用所有字段建议`)
  }

  // 清除预填充数据
  const clearPreFill = () => {
    Object.keys(formData).forEach(key => {
      delete formData[key]
    })
    suggestions.value = {}
    appliedRules.value = []
    ElMessage.success('已清除预填充数据')
  }

  // 加载用户历史
  const loadUserHistory = async () => {
    try {
      // 这里应该从API获取用户历史数据
      // 模拟数据
      userHistory.value = [
        {
          id: 'config_1',
          algorithm: 'LightGBM',
          dataSource: 'CSI300',
          performance: 0.15,
          createdAt: '2024-01-10',
          hyperparameters: { learning_rate: 0.1, n_estimators: 100 }
        },
        {
          id: 'config_2',
          algorithm: 'XGBoost',
          dataSource: 'CSI500',
          performance: 0.12,
          createdAt: '2024-01-08',
          hyperparameters: { learning_rate: 0.08, n_estimators: 150 }
        }
      ]
      preFillManager.setUserHistory(userHistory.value)
    } catch (error) {
      console.error('Failed to load user history:', error)
    }
  }

  // 加载用户偏好
  const loadUserPreferences = async () => {
    try {
      // 这里应该从API获取用户偏好
      // 模拟数据
      userPreferences.value = {
        preferredAlgorithm: 'LightGBM',
        preferredDataSource: 'CSI300',
        preferredTimeRange: '3years',
        riskTolerance: 0.65,
        investmentStyle: 'value_growth'
      }
      preFillManager.setUserPreferences(userPreferences.value)
      preferencesLoaded.value = true
    } catch (error) {
      console.error('Failed to load user preferences:', error)
    }
  }

  // 加载市场环境
  const loadMarketConditions = async () => {
    try {
      // 这里应该从API获取市场环境数据
      // 模拟数据
      marketConditions.value = {
        trend: 'bull',
        volatility: 0.45,
        liquidity: 0.8,
        sentiment: 'positive',
        lastUpdated: new Date()
      }
    } catch (error) {
      console.error('Failed to load market conditions:', error)
    }
  }

  // 注册字段配置
  const registerField = (config: FieldConfig) => {
    preFillManager.registerFieldConfig(config)
  }

  // 注册自定义规则
  const registerRule = (rule: PreFillRule) => {
    preFillManager.registerRule(rule)
  }

  // 获取字段建议值
  const getFieldSuggestion = (fieldName: string) => {
    return suggestions.value[fieldName]
  }

  // 检查字段是否有建议
  const hasSuggestion = (fieldName: string) => {
    return fieldName in suggestions.value && suggestions.value[fieldName] !== undefined
  }

  // 获取预填充统计
  const getPreFillStats = computed(() => ({
    totalRules: preFillManager.getRules().length,
    appliedRules: appliedRules.value.length,
    suggestionsCount: Object.keys(suggestions.value).length,
    hasTransferData: !!currentTransfer.value,
    preferencesLoaded: preferencesLoaded.value
  }))

  // 监听传递数据变化，自动执行预填充
  watch(
    () => currentTransfer.value,
    async (newTransfer) => {
      if (newTransfer && preFillConfig.autoApply) {
        await nextTick()
        await executePreFill()
      }
    },
    { immediate: true }
  )

  // 初始化
  const initialize = async () => {
    await Promise.all([
      loadUserHistory(),
      loadUserPreferences(),
      loadMarketConditions()
    ])
    
    if (preFillConfig.autoApply) {
      await executePreFill()
    }
  }

  return {
    // 状态
    isPreFilling,
    appliedRules,
    suggestions,
    formData,
    preferencesLoaded,
    preFillConfig,
    getPreFillStats,

    // 数据源
    userHistory,
    userPreferences,
    marketConditions,

    // 核心方法
    executePreFill,
    applySuggestion,
    applyAllSuggestions,
    clearPreFill,
    initialize,

    // 字段相关
    registerField,
    getFieldSuggestion,
    hasSuggestion,

    // 规则相关
    registerRule,

    // 数据加载
    loadUserHistory,
    loadUserPreferences,
    loadMarketConditions
  }
}

// 导出管理器实例
export { preFillManager }

// 类型导出
export type { PreFillRule, PreFillContext, FieldConfig }