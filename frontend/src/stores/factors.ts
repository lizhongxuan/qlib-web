import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

interface Factor {
  id: string
  name: string
  expression: string
  description?: string
  category: string
  type: 'technical' | 'fundamental' | 'alternative' | 'ai_generated'
  status: 'draft' | 'validated' | 'published' | 'deprecated'
  createdAt: Date
  updatedAt: Date
  createdBy: string
  tags: string[]
  performance?: {
    ic: number
    icir: number
    sharpe: number
    returns: number
    maxDrawdown: number
  }
  validationResults?: {
    isValid: boolean
    errors: string[]
    warnings: string[]
    suggestions: string[]
  }
  usage: {
    usedInModels: string[]
    usedInStrategies: string[]
    lastUsed?: Date
  }
}

interface FactorTemplate {
  id: string
  name: string
  category: string
  template: string
  variables: string[]
  description: string
  examples: string[]
}

interface FactorGroup {
  id: string
  name: string
  description: string
  factorIds: string[]
  createdAt: Date
  category: string
}

export const useFactorsStore = defineStore('factors', () => {
  // 状态
  const factors = ref<Factor[]>([])
  const factorTemplates = ref<FactorTemplate[]>([])
  const factorGroups = ref<FactorGroup[]>([])
  const selectedFactors = ref<string[]>([])
  const currentEditingFactor = ref<Factor | null>(null)
  const isLoading = ref(false)
  const searchQuery = ref('')
  const filterCategory = ref<string>('all')
  const filterStatus = ref<string>('all')
  const filterType = ref<string>('all')
  const sortBy = ref<'name' | 'createdAt' | 'performance' | 'usage'>('createdAt')
  const sortOrder = ref<'asc' | 'desc'>('desc')

  // 计算属性
  const filteredFactors = computed(() => {
    let result = factors.value

    // 搜索过滤
    if (searchQuery.value) {
      const query = searchQuery.value.toLowerCase()
      result = result.filter(factor => 
        factor.name.toLowerCase().includes(query) ||
        factor.description?.toLowerCase().includes(query) ||
        factor.expression.toLowerCase().includes(query) ||
        factor.tags.some(tag => tag.toLowerCase().includes(query))
      )
    }

    // 分类过滤
    if (filterCategory.value !== 'all') {
      result = result.filter(factor => factor.category === filterCategory.value)
    }

    // 状态过滤
    if (filterStatus.value !== 'all') {
      result = result.filter(factor => factor.status === filterStatus.value)
    }

    // 类型过滤
    if (filterType.value !== 'all') {
      result = result.filter(factor => factor.type === filterType.value)
    }

    // 排序
    result.sort((a, b) => {
      let comparison = 0
      
      switch (sortBy.value) {
        case 'name':
          comparison = a.name.localeCompare(b.name)
          break
        case 'createdAt':
          comparison = new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime()
          break
        case 'performance':
          const aPerf = a.performance?.sharpe || 0
          const bPerf = b.performance?.sharpe || 0
          comparison = aPerf - bPerf
          break
        case 'usage':
          const aUsage = a.usage.usedInModels.length + a.usage.usedInStrategies.length
          const bUsage = b.usage.usedInModels.length + b.usage.usedInStrategies.length
          comparison = aUsage - bUsage
          break
      }

      return sortOrder.value === 'asc' ? comparison : -comparison
    })

    return result
  })

  const factorCategories = computed(() => {
    const categories = [...new Set(factors.value.map(f => f.category))]
    return categories.sort()
  })

  const factorsByCategory = computed(() => {
    const grouped: Record<string, Factor[]> = {}
    factors.value.forEach(factor => {
      if (!grouped[factor.category]) {
        grouped[factor.category] = []
      }
      grouped[factor.category].push(factor)
    })
    return grouped
  })

  const selectedFactorsList = computed(() => {
    return factors.value.filter(factor => selectedFactors.value.includes(factor.id))
  })

  const factorStats = computed(() => {
    return {
      total: factors.value.length,
      published: factors.value.filter(f => f.status === 'published').length,
      validated: factors.value.filter(f => f.status === 'validated').length,
      draft: factors.value.filter(f => f.status === 'draft').length,
      aiGenerated: factors.value.filter(f => f.type === 'ai_generated').length,
      technical: factors.value.filter(f => f.type === 'technical').length,
      fundamental: factors.value.filter(f => f.type === 'fundamental').length
    }
  })

  // 动作
  const loadFactors = async () => {
    isLoading.value = true
    try {
      // 模拟API调用
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      // 模拟数据
      factors.value = [
        {
          id: 'factor_1',
          name: '20日动量因子',
          expression: '($close / Ref($close, 20)) - 1',
          description: '计算当前价格相对于20天前价格的变化率',
          category: '技术指标',
          type: 'technical',
          status: 'published',
          createdAt: new Date('2024-01-01'),
          updatedAt: new Date('2024-01-15'),
          createdBy: 'user1',
          tags: ['动量', '技术分析', '短期'],
          performance: {
            ic: 0.08,
            icir: 1.2,
            sharpe: 1.45,
            returns: 0.285,
            maxDrawdown: -0.08
          },
          validationResults: {
            isValid: true,
            errors: [],
            warnings: [],
            suggestions: ['建议结合成交量指标']
          },
          usage: {
            usedInModels: ['model_1', 'model_2'],
            usedInStrategies: ['strategy_1'],
            lastUsed: new Date('2024-01-10')
          }
        },
        {
          id: 'factor_2',
          name: '市盈率倒数',
          expression: '1 / $pe_ratio',
          description: '市盈率的倒数，用于价值投资策略',
          category: '基本面',
          type: 'fundamental',
          status: 'validated',
          createdAt: new Date('2024-01-02'),
          updatedAt: new Date('2024-01-12'),
          createdBy: 'user2',
          tags: ['价值', '基本面', '长期'],
          performance: {
            ic: 0.12,
            icir: 1.8,
            sharpe: 1.65,
            returns: 0.32,
            maxDrawdown: -0.12
          },
          validationResults: {
            isValid: true,
            errors: [],
            warnings: ['数据更新频率较低'],
            suggestions: ['可结合其他价值指标']
          },
          usage: {
            usedInModels: ['model_3'],
            usedInStrategies: [],
            lastUsed: new Date('2024-01-08')
          }
        }
      ]
    } catch (error) {
      console.error('加载因子失败:', error)
    } finally {
      isLoading.value = false
    }
  }

  const createFactor = async (factorData: Partial<Factor>): Promise<Factor> => {
    const newFactor: Factor = {
      id: `factor_${Date.now()}`,
      name: factorData.name || '新因子',
      expression: factorData.expression || '',
      description: factorData.description || '',
      category: factorData.category || '自定义',
      type: factorData.type || 'technical',
      status: 'draft',
      createdAt: new Date(),
      updatedAt: new Date(),
      createdBy: 'current_user',
      tags: factorData.tags || [],
      validationResults: {
        isValid: false,
        errors: [],
        warnings: [],
        suggestions: []
      },
      usage: {
        usedInModels: [],
        usedInStrategies: []
      }
    }

    factors.value.unshift(newFactor)
    return newFactor
  }

  const updateFactor = async (factorId: string, updates: Partial<Factor>): Promise<Factor | null> => {
    const factorIndex = factors.value.findIndex(f => f.id === factorId)
    if (factorIndex === -1) return null

    const updatedFactor = {
      ...factors.value[factorIndex],
      ...updates,
      updatedAt: new Date()
    }

    factors.value[factorIndex] = updatedFactor
    return updatedFactor
  }

  const deleteFactor = async (factorId: string): Promise<boolean> => {
    const factorIndex = factors.value.findIndex(f => f.id === factorId)
    if (factorIndex === -1) return false

    factors.value.splice(factorIndex, 1)
    
    // 从选中列表中移除
    const selectedIndex = selectedFactors.value.indexOf(factorId)
    if (selectedIndex > -1) {
      selectedFactors.value.splice(selectedIndex, 1)
    }

    return true
  }

  const validateFactor = async (factorId: string): Promise<boolean> => {
    const factor = factors.value.find(f => f.id === factorId)
    if (!factor) return false

    isLoading.value = true
    try {
      // 模拟验证过程
      await new Promise(resolve => setTimeout(resolve, 2000))
      
      // 模拟验证结果
      const validationResults = {
        isValid: Math.random() > 0.3,
        errors: Math.random() > 0.7 ? ['表达式语法错误'] : [],
        warnings: Math.random() > 0.5 ? ['因子值存在异常'] : [],
        suggestions: ['建议使用标准化处理', '考虑添加行业中性化']
      }

      await updateFactor(factorId, {
        validationResults,
        status: validationResults.isValid ? 'validated' : 'draft'
      })

      return validationResults.isValid
    } catch (error) {
      console.error('验证因子失败:', error)
      return false
    } finally {
      isLoading.value = false
    }
  }

  const testFactor = async (factorId: string, testConfig: any): Promise<any> => {
    const factor = factors.value.find(f => f.id === factorId)
    if (!factor) return null

    isLoading.value = true
    try {
      // 模拟测试过程
      await new Promise(resolve => setTimeout(resolve, 3000))
      
      // 模拟测试结果
      const performance = {
        ic: Math.random() * 0.2 - 0.1,
        icir: Math.random() * 3,
        sharpe: Math.random() * 2,
        returns: Math.random() * 0.5 - 0.1,
        maxDrawdown: -Math.random() * 0.2
      }

      await updateFactor(factorId, { performance })
      return performance
    } catch (error) {
      console.error('测试因子失败:', error)
      return null
    } finally {
      isLoading.value = false
    }
  }

  const aiGenerateFactor = async (prompt: string): Promise<Factor | null> => {
    isLoading.value = true
    try {
      // 模拟AI生成过程
      await new Promise(resolve => setTimeout(resolve, 2000))
      
      // 模拟AI生成的因子
      const aiFactorData = {
        name: `AI生成因子_${Date.now()}`,
        expression: `($close / MA($close, 20)) - 1`,
        description: `基于提示"${prompt}"生成的因子`,
        category: 'AI生成',
        type: 'ai_generated' as const,
        tags: ['AI生成', '自动化']
      }

      return await createFactor(aiFactorData)
    } catch (error) {
      console.error('AI生成因子失败:', error)
      return null
    } finally {
      isLoading.value = false
    }
  }

  const duplicateFactor = async (factorId: string): Promise<Factor | null> => {
    const originalFactor = factors.value.find(f => f.id === factorId)
    if (!originalFactor) return null

    const duplicatedData = {
      ...originalFactor,
      name: `${originalFactor.name} (副本)`,
      status: 'draft' as const,
      tags: [...originalFactor.tags, '副本']
    }

    return await createFactor(duplicatedData)
  }

  const exportFactors = (factorIds?: string[]): string => {
    const factorsToExport = factorIds 
      ? factors.value.filter(f => factorIds.includes(f.id))
      : factors.value

    return JSON.stringify(factorsToExport, null, 2)
  }

  const importFactors = async (factorsData: string): Promise<number> => {
    try {
      const importedFactors = JSON.parse(factorsData) as Factor[]
      let importedCount = 0

      for (const factorData of importedFactors) {
        // 检查是否已存在同名因子
        const existingFactor = factors.value.find(f => f.name === factorData.name)
        if (!existingFactor) {
          await createFactor(factorData)
          importedCount++
        }
      }

      return importedCount
    } catch (error) {
      console.error('导入因子失败:', error)
      return 0
    }
  }

  const toggleFactorSelection = (factorId: string) => {
    const index = selectedFactors.value.indexOf(factorId)
    if (index > -1) {
      selectedFactors.value.splice(index, 1)
    } else {
      selectedFactors.value.push(factorId)
    }
  }

  const selectAllFactors = () => {
    selectedFactors.value = filteredFactors.value.map(f => f.id)
  }

  const clearSelection = () => {
    selectedFactors.value = []
  }

  const batchDeleteFactors = async (factorIds: string[]): Promise<number> => {
    let deletedCount = 0
    for (const factorId of factorIds) {
      if (await deleteFactor(factorId)) {
        deletedCount++
      }
    }
    return deletedCount
  }

  const batchUpdateStatus = async (factorIds: string[], status: Factor['status']): Promise<number> => {
    let updatedCount = 0
    for (const factorId of factorIds) {
      if (await updateFactor(factorId, { status })) {
        updatedCount++
      }
    }
    return updatedCount
  }

  const searchFactors = (query: string) => {
    searchQuery.value = query
  }

  const setFilters = (filters: {
    category?: string
    status?: string
    type?: string
  }) => {
    if (filters.category !== undefined) filterCategory.value = filters.category
    if (filters.status !== undefined) filterStatus.value = filters.status
    if (filters.type !== undefined) filterType.value = filters.type
  }

  const setSorting = (field: typeof sortBy.value, order: typeof sortOrder.value) => {
    sortBy.value = field
    sortOrder.value = order
  }

  const resetFilters = () => {
    searchQuery.value = ''
    filterCategory.value = 'all'
    filterStatus.value = 'all'
    filterType.value = 'all'
    sortBy.value = 'createdAt'
    sortOrder.value = 'desc'
  }

  return {
    // 状态
    factors,
    factorTemplates,
    factorGroups,
    selectedFactors,
    currentEditingFactor,
    isLoading,
    searchQuery,
    filterCategory,
    filterStatus,
    filterType,
    sortBy,
    sortOrder,

    // 计算属性
    filteredFactors,
    factorCategories,
    factorsByCategory,
    selectedFactorsList,
    factorStats,

    // 动作
    loadFactors,
    createFactor,
    updateFactor,
    deleteFactor,
    validateFactor,
    testFactor,
    aiGenerateFactor,
    duplicateFactor,
    exportFactors,
    importFactors,
    toggleFactorSelection,
    selectAllFactors,
    clearSelection,
    batchDeleteFactors,
    batchUpdateStatus,
    searchFactors,
    setFilters,
    setSorting,
    resetFilters
  }
})