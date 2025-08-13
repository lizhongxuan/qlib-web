import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

interface Model {
  id: string
  name: string
  type: 'LightGBM' | 'XGBoost' | 'LSTM' | 'Linear' | 'RandomForest' | 'SVM' | 'Custom'
  status: 'training' | 'completed' | 'failed' | 'cancelled' | 'deployed'
  description?: string
  createdAt: Date
  updatedAt: Date
  createdBy: string
  tags: string[]
  
  // 训练配置
  config: {
    dataSource: string
    timeRange: {
      startDate: string
      endDate: string
    }
    features: string[]
    target: string
    trainTestSplit: number
    validationMethod: 'time_series' | 'k_fold' | 'holdout'
    hyperparameters: Record<string, any>
  }
  
  // 训练进度
  training: {
    progress: number
    currentEpoch?: number
    totalEpochs?: number
    eta?: number
    logs: string[]
    startTime?: Date
    endTime?: Date
    duration?: number
  }
  
  // 性能指标
  performance?: {
    trainMetrics: {
      accuracy?: number
      mse?: number
      mae?: number
      r2?: number
      ic?: number
      icir?: number
    }
    testMetrics: {
      accuracy?: number
      mse?: number
      mae?: number
      r2?: number
      ic?: number
      icir?: number
    }
    validationMetrics?: {
      accuracy?: number
      mse?: number
      mae?: number
      r2?: number
      ic?: number
      icir?: number
    }
    crossValidation?: {
      mean: number
      std: number
      scores: number[]
    }
    featureImportance?: Array<{
      feature: string
      importance: number
    }>
  }
  
  // 模型文件信息
  artifacts: {
    modelPath?: string
    size?: number
    format?: string
    version?: string
    checksum?: string
  }
  
  // 使用情况
  usage: {
    usedInStrategies: string[]
    usedInBacktests: string[]
    deployments: string[]
    lastUsed?: Date
    totalPredictions?: number
  }
  
  // 版本控制
  version: {
    major: number
    minor: number
    patch: number
    parentModelId?: string
    changelog?: string
  }
}

interface TrainingJob {
  id: string
  modelId: string
  status: 'queued' | 'running' | 'completed' | 'failed' | 'cancelled'
  priority: 'low' | 'normal' | 'high'
  progress: number
  startTime?: Date
  endTime?: Date
  errorMessage?: string
  resourceUsage?: {
    cpu: number
    memory: number
    gpu?: number
  }
}

interface ModelTemplate {
  id: string
  name: string
  type: Model['type']
  description: string
  defaultConfig: Partial<Model['config']>
  defaultHyperparams: Record<string, any>
  category: string
  difficulty: 'beginner' | 'intermediate' | 'advanced'
}

export const useModelsStore = defineStore('models', () => {
  // 状态
  const models = ref<Model[]>([])
  const trainingJobs = ref<TrainingJob[]>([])
  const modelTemplates = ref<ModelTemplate[]>([])
  const selectedModels = ref<string[]>([])
  const currentEditingModel = ref<Model | null>(null)
  const isLoading = ref(false)
  const searchQuery = ref('')
  const filterType = ref<string>('all')
  const filterStatus = ref<string>('all')
  const sortBy = ref<'name' | 'createdAt' | 'performance' | 'usage'>('createdAt')
  const sortOrder = ref<'asc' | 'desc'>('desc')

  // 计算属性
  const filteredModels = computed(() => {
    let result = models.value

    // 搜索过滤
    if (searchQuery.value) {
      const query = searchQuery.value.toLowerCase()
      result = result.filter(model => 
        model.name.toLowerCase().includes(query) ||
        model.description?.toLowerCase().includes(query) ||
        model.type.toLowerCase().includes(query) ||
        model.tags.some(tag => tag.toLowerCase().includes(query))
      )
    }

    // 类型过滤
    if (filterType.value !== 'all') {
      result = result.filter(model => model.type === filterType.value)
    }

    // 状态过滤
    if (filterStatus.value !== 'all') {
      result = result.filter(model => model.status === filterStatus.value)
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
          const aPerf = a.performance?.testMetrics?.ic || 0
          const bPerf = b.performance?.testMetrics?.ic || 0
          comparison = aPerf - bPerf
          break
        case 'usage':
          const aUsage = a.usage.usedInStrategies.length + a.usage.usedInBacktests.length
          const bUsage = b.usage.usedInStrategies.length + b.usage.usedInBacktests.length
          comparison = aUsage - bUsage
          break
      }

      return sortOrder.value === 'asc' ? comparison : -comparison
    })

    return result
  })

  const modelsByType = computed(() => {
    const grouped: Record<string, Model[]> = {}
    models.value.forEach(model => {
      if (!grouped[model.type]) {
        grouped[model.type] = []
      }
      grouped[model.type].push(model)
    })
    return grouped
  })

  const modelsByStatus = computed(() => {
    const grouped: Record<string, Model[]> = {}
    models.value.forEach(model => {
      if (!grouped[model.status]) {
        grouped[model.status] = []
      }
      grouped[model.status].push(model)
    })
    return grouped
  })

  const activeTrainingJobs = computed(() => {
    return trainingJobs.value.filter(job => 
      job.status === 'queued' || job.status === 'running'
    )
  })

  const completedTrainingJobs = computed(() => {
    return trainingJobs.value.filter(job => job.status === 'completed')
  })

  const failedTrainingJobs = computed(() => {
    return trainingJobs.value.filter(job => job.status === 'failed')
  })

  const modelStats = computed(() => {
    return {
      total: models.value.length,
      training: models.value.filter(m => m.status === 'training').length,
      completed: models.value.filter(m => m.status === 'completed').length,
      failed: models.value.filter(m => m.status === 'failed').length,
      deployed: models.value.filter(m => m.status === 'deployed').length,
      lightgbm: models.value.filter(m => m.type === 'LightGBM').length,
      xgboost: models.value.filter(m => m.type === 'XGBoost').length,
      lstm: models.value.filter(m => m.type === 'LSTM').length
    }
  })

  const bestPerformingModels = computed(() => {
    return models.value
      .filter(m => m.performance?.testMetrics?.ic)
      .sort((a, b) => (b.performance?.testMetrics?.ic || 0) - (a.performance?.testMetrics?.ic || 0))
      .slice(0, 5)
  })

  // 动作
  const loadModels = async () => {
    isLoading.value = true
    try {
      // 模拟API调用
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      // 模拟数据
      models.value = [
        {
          id: 'model_1',
          name: 'LightGBM多因子模型v3.2',
          type: 'LightGBM',
          status: 'completed',
          description: '基于技术指标和基本面因子的LightGBM模型',
          createdAt: new Date('2024-01-01'),
          updatedAt: new Date('2024-01-15'),
          createdBy: 'user1',
          tags: ['多因子', '技术分析', '基本面'],
          config: {
            dataSource: 'CSI300',
            timeRange: {
              startDate: '2020-01-01',
              endDate: '2023-12-31'
            },
            features: ['factor_1', 'factor_2', 'factor_3'],
            target: 'future_return_5d',
            trainTestSplit: 0.8,
            validationMethod: 'time_series',
            hyperparameters: {
              n_estimators: 1000,
              learning_rate: 0.1,
              max_depth: 6,
              num_leaves: 31
            }
          },
          training: {
            progress: 100,
            currentEpoch: 1000,
            totalEpochs: 1000,
            logs: ['训练开始', '第100轮完成', '第500轮完成', '训练完成'],
            startTime: new Date('2024-01-01T09:00:00'),
            endTime: new Date('2024-01-01T10:30:00'),
            duration: 5400
          },
          performance: {
            trainMetrics: {
              accuracy: 0.68,
              mse: 0.012,
              ic: 0.08,
              icir: 1.2
            },
            testMetrics: {
              accuracy: 0.65,
              mse: 0.015,
              ic: 0.075,
              icir: 1.15
            },
            crossValidation: {
              mean: 0.067,
              std: 0.008,
              scores: [0.065, 0.070, 0.068, 0.066, 0.069]
            },
            featureImportance: [
              { feature: 'factor_1', importance: 0.45 },
              { feature: 'factor_2', importance: 0.35 },
              { feature: 'factor_3', importance: 0.20 }
            ]
          },
          artifacts: {
            modelPath: '/models/lightgbm_v3.2.pkl',
            size: 15728640,
            format: 'pickle',
            version: '3.2.0'
          },
          usage: {
            usedInStrategies: ['strategy_1', 'strategy_2'],
            usedInBacktests: ['backtest_1'],
            deployments: ['deploy_1'],
            lastUsed: new Date('2024-01-10'),
            totalPredictions: 50000
          },
          version: {
            major: 3,
            minor: 2,
            patch: 0,
            changelog: '优化特征工程，提升模型稳定性'
          }
        },
        {
          id: 'model_2',
          name: 'LSTM时序预测模型v2.1',
          type: 'LSTM',
          status: 'training',
          description: '基于深度学习的时序预测模型',
          createdAt: new Date('2024-01-02'),
          updatedAt: new Date('2024-01-12'),
          createdBy: 'user2',
          tags: ['深度学习', '时序预测', 'LSTM'],
          config: {
            dataSource: 'CSI500',
            timeRange: {
              startDate: '2020-01-01',
              endDate: '2023-12-31'
            },
            features: ['price_sequence', 'volume_sequence'],
            target: 'future_return_10d',
            trainTestSplit: 0.8,
            validationMethod: 'time_series',
            hyperparameters: {
              hidden_size: 128,
              num_layers: 2,
              dropout: 0.2,
              learning_rate: 0.001,
              batch_size: 64,
              epochs: 100
            }
          },
          training: {
            progress: 65,
            currentEpoch: 65,
            totalEpochs: 100,
            eta: 1800,
            logs: ['训练开始', '第20轮完成', '第40轮完成', '第60轮完成'],
            startTime: new Date('2024-01-12T14:00:00')
          },
          artifacts: {
            modelPath: '/models/lstm_v2.1_checkpoint.pth',
            size: 25165824,
            format: 'pytorch'
          },
          usage: {
            usedInStrategies: [],
            usedInBacktests: [],
            deployments: [],
            totalPredictions: 0
          },
          version: {
            major: 2,
            minor: 1,
            patch: 0,
            parentModelId: 'model_2_old',
            changelog: '增加注意力机制，提升预测精度'
          }
        }
      ]

      // 模拟训练任务数据
      trainingJobs.value = [
        {
          id: 'job_1',
          modelId: 'model_2',
          status: 'running',
          priority: 'normal',
          progress: 65,
          startTime: new Date('2024-01-12T14:00:00'),
          resourceUsage: {
            cpu: 85,
            memory: 70,
            gpu: 90
          }
        }
      ]

    } catch (error) {
      console.error('加载模型失败:', error)
    } finally {
      isLoading.value = false
    }
  }

  const createModel = async (modelData: Partial<Model>): Promise<Model> => {
    const newModel: Model = {
      id: `model_${Date.now()}`,
      name: modelData.name || '新模型',
      type: modelData.type || 'LightGBM',
      status: 'training',
      description: modelData.description || '',
      createdAt: new Date(),
      updatedAt: new Date(),
      createdBy: 'current_user',
      tags: modelData.tags || [],
      config: modelData.config || {
        dataSource: '',
        timeRange: { startDate: '', endDate: '' },
        features: [],
        target: '',
        trainTestSplit: 0.8,
        validationMethod: 'time_series',
        hyperparameters: {}
      },
      training: {
        progress: 0,
        logs: ['模型创建成功，准备开始训练...']
      },
      artifacts: {},
      usage: {
        usedInStrategies: [],
        usedInBacktests: [],
        deployments: [],
        totalPredictions: 0
      },
      version: {
        major: 1,
        minor: 0,
        patch: 0
      }
    }

    models.value.unshift(newModel)
    return newModel
  }

  const updateModel = async (modelId: string, updates: Partial<Model>): Promise<Model | null> => {
    const modelIndex = models.value.findIndex(m => m.id === modelId)
    if (modelIndex === -1) return null

    const updatedModel = {
      ...models.value[modelIndex],
      ...updates,
      updatedAt: new Date()
    }

    models.value[modelIndex] = updatedModel
    return updatedModel
  }

  const deleteModel = async (modelId: string): Promise<boolean> => {
    const modelIndex = models.value.findIndex(m => m.id === modelId)
    if (modelIndex === -1) return false

    // 检查是否有依赖关系
    const model = models.value[modelIndex]
    if (model.usage.usedInStrategies.length > 0 || model.usage.deployments.length > 0) {
      throw new Error('模型正在被使用，无法删除')
    }

    models.value.splice(modelIndex, 1)
    
    // 从选中列表中移除
    const selectedIndex = selectedModels.value.indexOf(modelId)
    if (selectedIndex > -1) {
      selectedModels.value.splice(selectedIndex, 1)
    }

    return true
  }

  const startTraining = async (modelId: string): Promise<TrainingJob | null> => {
    const model = models.value.find(m => m.id === modelId)
    if (!model) return null

    // 创建训练任务
    const trainingJob: TrainingJob = {
      id: `job_${Date.now()}`,
      modelId,
      status: 'queued',
      priority: 'normal',
      progress: 0,
      startTime: new Date(),
      resourceUsage: {
        cpu: 0,
        memory: 0
      }
    }

    trainingJobs.value.unshift(trainingJob)

    // 更新模型状态
    await updateModel(modelId, {
      status: 'training',
      training: {
        ...model.training,
        progress: 0,
        startTime: new Date(),
        logs: [...model.training.logs, '训练任务已排队']
      }
    })

    // 模拟训练过程
    simulateTraining(trainingJob)

    return trainingJob
  }

  const stopTraining = async (modelId: string): Promise<boolean> => {
    const job = trainingJobs.value.find(j => j.modelId === modelId && j.status === 'running')
    if (!job) return false

    job.status = 'cancelled'
    job.endTime = new Date()

    await updateModel(modelId, {
      status: 'cancelled',
      training: {
        ...models.value.find(m => m.id === modelId)?.training || { progress: 0, logs: [] },
        endTime: new Date()
      }
    })

    return true
  }

  const retryTraining = async (modelId: string): Promise<TrainingJob | null> => {
    const model = models.value.find(m => m.id === modelId)
    if (!model || model.status !== 'failed') return null

    // 重置模型状态
    await updateModel(modelId, {
      status: 'training',
      training: {
        ...model.training,
        progress: 0,
        logs: [...model.training.logs, '重新开始训练...']
      }
    })

    return await startTraining(modelId)
  }

  const compareModels = (modelIds: string[]) => {
    const modelsToCompare = models.value.filter(m => modelIds.includes(m.id))
    
    return {
      models: modelsToCompare,
      comparison: {
        performance: modelsToCompare.map(m => ({
          id: m.id,
          name: m.name,
          ic: m.performance?.testMetrics?.ic || 0,
          icir: m.performance?.testMetrics?.icir || 0,
          accuracy: m.performance?.testMetrics?.accuracy || 0
        })),
        config: modelsToCompare.map(m => ({
          id: m.id,
          name: m.name,
          type: m.type,
          features: m.config.features.length,
          hyperparameters: Object.keys(m.config.hyperparameters).length
        }))
      }
    }
  }

  const cloneModel = async (modelId: string, newName?: string): Promise<Model | null> => {
    const originalModel = models.value.find(m => m.id === modelId)
    if (!originalModel) return null

    const clonedData = {
      ...originalModel,
      name: newName || `${originalModel.name} (副本)`,
      status: 'training' as const,
      tags: [...originalModel.tags, '克隆'],
      version: {
        major: 1,
        minor: 0,
        patch: 0,
        parentModelId: modelId
      }
    }

    return await createModel(clonedData)
  }

  const exportModel = async (modelId: string): Promise<string | null> => {
    const model = models.value.find(m => m.id === modelId)
    if (!model || model.status !== 'completed') return null

    // 模拟导出过程
    return JSON.stringify({
      metadata: {
        id: model.id,
        name: model.name,
        type: model.type,
        version: model.version,
        performance: model.performance
      },
      config: model.config,
      exportedAt: new Date().toISOString()
    }, null, 2)
  }

  const deployModel = async (modelId: string, deploymentConfig: any): Promise<boolean> => {
    const model = models.value.find(m => m.id === modelId)
    if (!model || model.status !== 'completed') return false

    // 更新模型状态为已部署
    await updateModel(modelId, {
      status: 'deployed',
      usage: {
        ...model.usage,
        deployments: [...model.usage.deployments, `deploy_${Date.now()}`]
      }
    })

    return true
  }

  // 辅助函数
  const simulateTraining = (job: TrainingJob) => {
    const interval = setInterval(async () => {
      if (job.status !== 'running' && job.status !== 'queued') {
        clearInterval(interval)
        return
      }

      if (job.status === 'queued') {
        job.status = 'running'
      }

      // 更新进度
      job.progress = Math.min(job.progress + Math.random() * 10, 100)
      
      // 更新资源使用
      job.resourceUsage = {
        cpu: 80 + Math.random() * 20,
        memory: 60 + Math.random() * 30,
        gpu: 85 + Math.random() * 15
      }

      // 更新模型训练进度
      const model = models.value.find(m => m.id === job.modelId)
      if (model) {
        const newLog = `第${Math.floor(job.progress)}轮训练完成`
        await updateModel(job.modelId, {
          training: {
            ...model.training,
            progress: job.progress,
            currentEpoch: Math.floor(job.progress),
            logs: [...model.training.logs, newLog].slice(-10) // 保留最新10条日志
          }
        })
      }

      // 训练完成
      if (job.progress >= 100) {
        job.status = 'completed'
        job.endTime = new Date()
        
        // 模拟性能指标
        const performance = {
          trainMetrics: {
            accuracy: 0.6 + Math.random() * 0.15,
            ic: 0.05 + Math.random() * 0.05,
            icir: 0.8 + Math.random() * 0.8
          },
          testMetrics: {
            accuracy: 0.55 + Math.random() * 0.15,
            ic: 0.04 + Math.random() * 0.05,
            icir: 0.7 + Math.random() * 0.8
          }
        }

        await updateModel(job.modelId, {
          status: 'completed',
          performance,
          training: {
            ...model?.training || { progress: 100, logs: [] },
            progress: 100,
            endTime: new Date()
          }
        })

        clearInterval(interval)
      }
    }, 2000)
  }

  const toggleModelSelection = (modelId: string) => {
    const index = selectedModels.value.indexOf(modelId)
    if (index > -1) {
      selectedModels.value.splice(index, 1)
    } else {
      selectedModels.value.push(modelId)
    }
  }

  const selectAllModels = () => {
    selectedModels.value = filteredModels.value.map(m => m.id)
  }

  const clearSelection = () => {
    selectedModels.value = []
  }

  const searchModels = (query: string) => {
    searchQuery.value = query
  }

  const setFilters = (filters: {
    type?: string
    status?: string
  }) => {
    if (filters.type !== undefined) filterType.value = filters.type
    if (filters.status !== undefined) filterStatus.value = filters.status
  }

  const setSorting = (field: typeof sortBy.value, order: typeof sortOrder.value) => {
    sortBy.value = field
    sortOrder.value = order
  }

  const resetFilters = () => {
    searchQuery.value = ''
    filterType.value = 'all'
    filterStatus.value = 'all'
    sortBy.value = 'createdAt'
    sortOrder.value = 'desc'
  }

  return {
    // 状态
    models,
    trainingJobs,
    modelTemplates,
    selectedModels,
    currentEditingModel,
    isLoading,
    searchQuery,
    filterType,
    filterStatus,
    sortBy,
    sortOrder,

    // 计算属性
    filteredModels,
    modelsByType,
    modelsByStatus,
    activeTrainingJobs,
    completedTrainingJobs,
    failedTrainingJobs,
    modelStats,
    bestPerformingModels,

    // 动作
    loadModels,
    createModel,
    updateModel,
    deleteModel,
    startTraining,
    stopTraining,
    retryTraining,
    compareModels,
    cloneModel,
    exportModel,
    deployModel,
    toggleModelSelection,
    selectAllModels,
    clearSelection,
    searchModels,
    setFilters,
    setSorting,
    resetFilters
  }
})