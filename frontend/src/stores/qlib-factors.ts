import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

// Qlib因子相关的类型定义
interface QlibFactor {
  name: string
  display_name: string
  expression: string
  description?: string
  category: 'price' | 'volume' | 'technical' | 'fundamental' | 'custom'
  frequency: 'daily' | 'weekly' | 'monthly'
  data_type: 'numeric' | 'categorical'
  universe: string[]
  created_at: string
  updated_at: string
  is_built_in: boolean
  parameters?: Record<string, any>
  dependencies?: string[]
  validation_status: 'pending' | 'valid' | 'invalid' | 'warning'
  validation_message?: string
}

interface QlibFactorGroup {
  name: string
  description: string
  factors: QlibFactor[]
  category: string
}

interface FactorICAnalysis {
  factor_name: string
  mean_ic: number
  ic_std: number
  information_ratio: number
  stability: number
  t_stat: number
  p_value: number
  turnover: number
  rank_ic: number
  rank_icir: number
}

interface FactorValidationResult {
  factor_name: string
  is_valid: boolean
  syntax_errors: string[]
  warnings: string[]
  suggestions: string[]
  data_coverage: number
  missing_ratio: number
  outlier_ratio: number
}

interface FactorPerformance {
  factor_name: string
  ic_mean: number
  ic_std: number
  ir: number
  monthly_ic: number[]
  cumulative_returns: number[]
  max_drawdown: number
  sharpe_ratio: number
  win_rate: number
}

interface CustomFactorTemplate {
  id: string
  name: string
  description: string
  template_code: string
  variables: string[]
  category: string
  examples: string[]
  difficulty: 'easy' | 'medium' | 'hard'
}

export const useQlibFactorsStore = defineStore('qlib-factors', () => {
  // 状态
  const factorLibrary = ref<QlibFactor[]>([])
  const factorGroups = ref<QlibFactorGroup[]>([])
  const customFactors = ref<QlibFactor[]>([])
  const selectedFactors = ref<string[]>([])
  const currentEditingFactor = ref<QlibFactor | null>(null)
  const factorTemplates = ref<CustomFactorTemplate[]>([])
  
  // 分析结果缓存
  const icAnalysisResults = ref<FactorICAnalysis[]>([])
  const validationResults = ref<FactorValidationResult[]>([])
  const performanceResults = ref<FactorPerformance[]>([])
  
  // UI状态
  const loading = ref(false)
  const searchQuery = ref('')
  const selectedCategory = ref<string>('all')
  const selectedUniverse = ref<string>('CSI300')
  const analysisTimeRange = ref<[string, string]>(['2023-01-01', '2023-12-31'])
  
  // 错误状态
  const error = ref<string | null>(null)
  const lastUpdateTime = ref<string>('')

  // 计算属性
  const filteredFactorLibrary = computed(() => {
    let filtered = factorLibrary.value

    if (searchQuery.value) {
      const query = searchQuery.value.toLowerCase()
      filtered = filtered.filter(factor => 
        factor.name.toLowerCase().includes(query) ||
        factor.display_name.toLowerCase().includes(query) ||
        factor.description?.toLowerCase().includes(query)
      )
    }

    if (selectedCategory.value !== 'all') {
      filtered = filtered.filter(factor => factor.category === selectedCategory.value)
    }

    return filtered
  })

  const factorCategories = computed(() => {
    const categories = new Set([
      ...factorLibrary.value.map(f => f.category),
      ...customFactors.value.map(f => f.category)
    ])
    return Array.from(categories).sort()
  })

  const factorsByCategory = computed(() => {
    const grouped: Record<string, QlibFactor[]> = {}
    
    const allFactors = [...factorLibrary.value, ...customFactors.value]
    allFactors.forEach(factor => {
      if (!grouped[factor.category]) {
        grouped[factor.category] = []
      }
      grouped[factor.category].push(factor)
    })
    
    return grouped
  })

  const selectedFactorsList = computed(() => {
    const allFactors = [...factorLibrary.value, ...customFactors.value]
    return allFactors.filter(factor => selectedFactors.value.includes(factor.name))
  })

  const factorStats = computed(() => {
    return {
      total: factorLibrary.value.length + customFactors.value.length,
      builtIn: factorLibrary.value.length,
      custom: customFactors.value.length,
      validated: [...factorLibrary.value, ...customFactors.value]
        .filter(f => f.validation_status === 'valid').length,
      categories: factorCategories.value.length,
      selected: selectedFactors.value.length
    }
  })

  const topPerformingFactors = computed(() => {
    return performanceResults.value
      .sort((a, b) => b.ir - a.ir)
      .slice(0, 10)
  })

  // Actions
  const loadFactorLibrary = async (): Promise<void> => {
    loading.value = true
    error.value = null

    try {
      const response = await fetch('/api/v1/qlib-factors/factor-library', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json'
        }
      })

      const result = await response.json()

      if (result.status === 'success') {
        factorLibrary.value = result.data.factors || []
        factorGroups.value = result.data.groups || []
        lastUpdateTime.value = new Date().toISOString()
      } else {
        throw new Error(result.message || '加载因子库失败')
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : '加载因子库失败'
      console.error('加载因子库失败:', err)
      
      // 降级到示例数据
      generateSampleFactorLibrary()
    } finally {
      loading.value = false
    }
  }

  const generateSampleFactorLibrary = (): void => {
    factorLibrary.value = [
      {
        name: 'CLOSE',
        display_name: '收盘价',
        expression: '$close',
        description: '股票当日收盘价格',
        category: 'price',
        frequency: 'daily',
        data_type: 'numeric',
        universe: ['CSI300', 'CSI500', 'ALL'],
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
        is_built_in: true,
        validation_status: 'valid'
      },
      {
        name: 'VOLUME',
        display_name: '成交量',
        expression: '$volume',
        description: '股票当日成交量',
        category: 'volume',
        frequency: 'daily',
        data_type: 'numeric',
        universe: ['CSI300', 'CSI500', 'ALL'],
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
        is_built_in: true,
        validation_status: 'valid'
      },
      {
        name: 'ROC20',
        display_name: '20日收益率',
        expression: '($close / Ref($close, 20)) - 1',
        description: '当前价格相对于20个交易日前价格的变化率',
        category: 'technical',
        frequency: 'daily',
        data_type: 'numeric',
        universe: ['CSI300', 'CSI500'],
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
        is_built_in: true,
        parameters: { period: 20 },
        validation_status: 'valid'
      },
      {
        name: 'MA20',
        display_name: '20日移动平均',
        expression: 'Mean($close, 20)',
        description: '20个交易日的收盘价移动平均',
        category: 'technical',
        frequency: 'daily',
        data_type: 'numeric',
        universe: ['CSI300', 'CSI500', 'ALL'],
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
        is_built_in: true,
        parameters: { period: 20 },
        validation_status: 'valid'
      },
      {
        name: 'RSI14',
        display_name: '14日RSI',
        expression: 'RSI($close, 14)',
        description: '14日相对强弱指标',
        category: 'technical',
        frequency: 'daily',
        data_type: 'numeric',
        universe: ['CSI300', 'CSI500'],
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
        is_built_in: true,
        parameters: { period: 14 },
        validation_status: 'valid'
      }
    ]

    factorGroups.value = [
      {
        name: '价格因子',
        description: '基于价格的基础因子',
        category: 'price',
        factors: factorLibrary.value.filter(f => f.category === 'price')
      },
      {
        name: '成交量因子',
        description: '基于成交量的因子',
        category: 'volume',
        factors: factorLibrary.value.filter(f => f.category === 'volume')
      },
      {
        name: '技术指标因子',
        description: '技术分析相关因子',
        category: 'technical',
        factors: factorLibrary.value.filter(f => f.category === 'technical')
      }
    ]

    lastUpdateTime.value = new Date().toISOString()
  }

  const validateFactor = async (expression: string): Promise<FactorValidationResult> => {
    loading.value = true

    try {
      const response = await fetch('/api/v1/qlib-factors/validate-factor', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          expression,
          universe: selectedUniverse.value
        })
      })

      const result = await response.json()

      if (result.status === 'success') {
        const validationResult = result.data
        
        // 更新验证结果缓存
        const existingIndex = validationResults.value.findIndex(
          r => r.factor_name === validationResult.factor_name
        )
        if (existingIndex >= 0) {
          validationResults.value[existingIndex] = validationResult
        } else {
          validationResults.value.push(validationResult)
        }

        return validationResult
      } else {
        throw new Error(result.message || '因子验证失败')
      }
    } catch (err) {
      console.error('因子验证失败:', err)
      
      // 返回模拟验证结果
      const mockResult: FactorValidationResult = {
        factor_name: 'custom_factor',
        is_valid: Math.random() > 0.3,
        syntax_errors: Math.random() > 0.7 ? ['语法错误: 无效的函数调用'] : [],
        warnings: Math.random() > 0.5 ? ['警告: 因子值存在异常'] : [],
        suggestions: ['建议使用标准化处理', '考虑添加去极值处理'],
        data_coverage: 0.95,
        missing_ratio: 0.02,
        outlier_ratio: 0.03
      }
      
      return mockResult
    } finally {
      loading.value = false
    }
  }

  const analyzeFactorIC = async (factorNames: string[]): Promise<FactorICAnalysis[]> => {
    loading.value = true

    try {
      const response = await fetch('/api/v1/qlib-factors/ic-analysis', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          factors: factorNames,
          start_time: analysisTimeRange.value[0],
          end_time: analysisTimeRange.value[1],
          universe: selectedUniverse.value
        })
      })

      const result = await response.json()

      if (result.status === 'success') {
        icAnalysisResults.value = result.data.ic_analysis || []
        return icAnalysisResults.value
      } else {
        throw new Error(result.message || 'IC分析失败')
      }
    } catch (err) {
      console.error('IC分析失败:', err)
      
      // 生成模拟IC分析结果
      const mockResults = factorNames.map(name => ({
        factor_name: name,
        mean_ic: Math.random() * 0.1 - 0.05,
        ic_std: Math.random() * 0.05 + 0.02,
        information_ratio: Math.random() * 2 - 1,
        stability: Math.random() * 100,
        t_stat: Math.random() * 4 - 2,
        p_value: Math.random() * 0.1,
        turnover: Math.random() * 0.5,
        rank_ic: Math.random() * 0.08 - 0.04,
        rank_icir: Math.random() * 1.5 - 0.75
      }))
      
      icAnalysisResults.value = mockResults
      return mockResults
    } finally {
      loading.value = false
    }
  }

  const createCustomFactor = async (factorData: Partial<QlibFactor>): Promise<QlibFactor> => {
    const newFactor: QlibFactor = {
      name: factorData.name || `custom_factor_${Date.now()}`,
      display_name: factorData.display_name || factorData.name || '自定义因子',
      expression: factorData.expression || '',
      description: factorData.description || '',
      category: factorData.category || 'custom',
      frequency: factorData.frequency || 'daily',
      data_type: factorData.data_type || 'numeric',
      universe: factorData.universe || ['CSI300'],
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      is_built_in: false,
      parameters: factorData.parameters || {},
      validation_status: 'pending'
    }

    customFactors.value.unshift(newFactor)
    return newFactor
  }

  const updateCustomFactor = async (factorName: string, updates: Partial<QlibFactor>): Promise<QlibFactor | null> => {
    const factorIndex = customFactors.value.findIndex(f => f.name === factorName)
    if (factorIndex === -1) return null

    const updatedFactor = {
      ...customFactors.value[factorIndex],
      ...updates,
      updated_at: new Date().toISOString()
    }

    customFactors.value[factorIndex] = updatedFactor
    return updatedFactor
  }

  const deleteCustomFactor = async (factorName: string): Promise<boolean> => {
    const factorIndex = customFactors.value.findIndex(f => f.name === factorName)
    if (factorIndex === -1) return false

    customFactors.value.splice(factorIndex, 1)
    
    // 从选中列表中移除
    const selectedIndex = selectedFactors.value.indexOf(factorName)
    if (selectedIndex > -1) {
      selectedFactors.value.splice(selectedIndex, 1)
    }

    return true
  }

  const generateFactorFromTemplate = async (templateId: string, variables: Record<string, any>): Promise<QlibFactor | null> => {
    const template = factorTemplates.value.find(t => t.id === templateId)
    if (!template) return null

    // 替换模板变量
    let expression = template.template_code
    for (const [key, value] of Object.entries(variables)) {
      expression = expression.replace(new RegExp(`{{${key}}}`, 'g'), String(value))
    }

    const factorData: Partial<QlibFactor> = {
      name: `${template.name}_${Date.now()}`,
      display_name: `${template.name} (${Object.values(variables).join(', ')})`,
      expression,
      description: `基于模板"${template.name}"生成`,
      category: 'custom',
      parameters: variables
    }

    return await createCustomFactor(factorData)
  }

  const aiGenerateFactor = async (prompt: string): Promise<QlibFactor | null> => {
    loading.value = true

    try {
      const response = await fetch('/api/v1/qlib-factors/ai-generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ prompt })
      })

      const result = await response.json()

      if (result.status === 'success') {
        const aiFactorData = result.data
        return await createCustomFactor(aiFactorData)
      } else {
        throw new Error(result.message || 'AI生成因子失败')
      }
    } catch (err) {
      console.error('AI生成因子失败:', err)
      
      // 返回模拟AI生成的因子
      const mockFactorData: Partial<QlibFactor> = {
        name: `ai_factor_${Date.now()}`,
        display_name: `AI生成因子`,
        expression: `($close / Mean($close, 20)) - 1`,
        description: `基于提示"${prompt}"生成的因子`,
        category: 'custom'
      }
      
      return await createCustomFactor(mockFactorData)
    } finally {
      loading.value = false
    }
  }

  const optimizeFactor = async (factorName: string): Promise<QlibFactor | null> => {
    loading.value = true

    try {
      const response = await fetch('/api/v1/qlib-factors/optimize', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          factor_name: factorName,
          universe: selectedUniverse.value
        })
      })

      const result = await response.json()

      if (result.status === 'success') {
        const optimizedFactorData = result.data
        return await createCustomFactor({
          ...optimizedFactorData,
          name: `${factorName}_optimized`,
          display_name: `${factorName} (优化版)`
        })
      } else {
        throw new Error(result.message || '因子优化失败')
      }
    } catch (err) {
      console.error('因子优化失败:', err)
      return null
    } finally {
      loading.value = false
    }
  }

  const exportFactors = (factorNames?: string[]): string => {
    const allFactors = [...factorLibrary.value, ...customFactors.value]
    const factorsToExport = factorNames 
      ? allFactors.filter(f => factorNames.includes(f.name))
      : allFactors

    return JSON.stringify({
      factors: factorsToExport,
      exported_at: new Date().toISOString(),
      version: '1.0'
    }, null, 2)
  }

  const importFactors = async (factorsData: string): Promise<number> => {
    try {
      const data = JSON.parse(factorsData)
      const factors = data.factors || []
      let importedCount = 0

      for (const factorData of factors) {
        if (!factorData.is_built_in) {
          // 检查是否已存在同名因子
          const existingFactor = customFactors.value.find(f => f.name === factorData.name)
          if (!existingFactor) {
            await createCustomFactor(factorData)
            importedCount++
          }
        }
      }

      return importedCount
    } catch (err) {
      console.error('导入因子失败:', err)
      return 0
    }
  }

  const toggleFactorSelection = (factorName: string): void => {
    const index = selectedFactors.value.indexOf(factorName)
    if (index > -1) {
      selectedFactors.value.splice(index, 1)
    } else {
      selectedFactors.value.push(factorName)
    }
  }

  const selectAllFactors = (): void => {
    selectedFactors.value = filteredFactorLibrary.value.map(f => f.name)
  }

  const clearSelection = (): void => {
    selectedFactors.value = []
  }

  const searchFactors = (query: string): void => {
    searchQuery.value = query
  }

  const setCategory = (category: string): void => {
    selectedCategory.value = category
  }

  const setUniverse = (universe: string): void => {
    selectedUniverse.value = universe
  }

  const setAnalysisTimeRange = (range: [string, string]): void => {
    analysisTimeRange.value = range
  }

  const refreshFactorLibrary = async (): Promise<void> => {
    await loadFactorLibrary()
  }

  const clearCache = (): void => {
    icAnalysisResults.value = []
    validationResults.value = []
    performanceResults.value = []
  }

  const loadFactorTemplates = async (): Promise<void> => {
    // 模拟加载因子模板
    factorTemplates.value = [
      {
        id: 'template_1',
        name: '移动平均因子',
        description: '计算指定周期的移动平均',
        template_code: 'Mean($close, {{period}})',
        variables: ['period'],
        category: 'technical',
        examples: ['Mean($close, 20)', 'Mean($close, 60)'],
        difficulty: 'easy'
      },
      {
        id: 'template_2',
        name: '动量因子',
        description: '计算指定周期的价格动量',
        template_code: '($close / Ref($close, {{period}})) - 1',
        variables: ['period'],
        category: 'technical',
        examples: ['($close / Ref($close, 20)) - 1'],
        difficulty: 'easy'
      },
      {
        id: 'template_3',
        name: '布林带因子',
        description: '基于布林带的技术指标',
        template_code: '($close - Mean($close, {{period}})) / Std($close, {{period}})',
        variables: ['period'],
        category: 'technical',
        examples: ['($close - Mean($close, 20)) / Std($close, 20)'],
        difficulty: 'medium'
      }
    ]
  }

  return {
    // State
    factorLibrary,
    factorGroups,
    customFactors,
    selectedFactors,
    currentEditingFactor,
    factorTemplates,
    icAnalysisResults,
    validationResults,
    performanceResults,
    loading,
    searchQuery,
    selectedCategory,
    selectedUniverse,
    analysisTimeRange,
    error,
    lastUpdateTime,

    // Computed
    filteredFactorLibrary,
    factorCategories,
    factorsByCategory,
    selectedFactorsList,
    factorStats,
    topPerformingFactors,

    // Actions
    loadFactorLibrary,
    generateSampleFactorLibrary,
    validateFactor,
    analyzeFactorIC,
    createCustomFactor,
    updateCustomFactor,
    deleteCustomFactor,
    generateFactorFromTemplate,
    aiGenerateFactor,
    optimizeFactor,
    exportFactors,
    importFactors,
    toggleFactorSelection,
    selectAllFactors,
    clearSelection,
    searchFactors,
    setCategory,
    setUniverse,
    setAnalysisTimeRange,
    refreshFactorLibrary,
    clearCache,
    loadFactorTemplates
  }
})