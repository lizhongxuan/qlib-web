import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

// Qlib模型相关的类型定义
interface QlibModel {
  model_id: string
  name: string
  description?: string
  model_type: 'lightgbm' | 'xgboost' | 'catboost' | 'lstm' | 'gru' | 'linear' | 'mlp' | 'custom'
  framework: 'qlib' | 'sklearn' | 'pytorch' | 'tensorflow' | 'custom'
  version: string
  created_at: string
  updated_at: string
  created_by: string
  status: 'registered' | 'training' | 'trained' | 'failed' | 'deprecated'
  tags: string[]
  
  // 模型配置
  config: {
    model_params: Record<string, any>
    data_config: {
      features: string[]
      label: string
      universe: string
      start_time: string
      end_time: string
    }
    trainer_config: {
      batch_size?: number
      epochs?: number
      learning_rate?: number
      early_stopping?: boolean
      validation_split?: number
    }
  }
  
  // 训练信息
  training_info?: {
    start_time: string
    end_time?: string
    duration?: number
    train_size: number
    valid_size: number
    test_size: number
    resource_usage: {
      cpu_time: number
      memory_peak: number
      gpu_time?: number
    }
  }
  
  // 性能指标
  performance?: {
    train_metrics: Record<string, number>
    valid_metrics: Record<string, number>
    test_metrics: Record<string, number>
    ic: number
    rank_ic: number
    sharpe_ratio: number
    annual_return: number
    max_drawdown: number
    information_ratio: number
  }
  
  // 模型文件信息
  model_files: {
    model_path: string
    config_path: string
    log_path: string
    artifact_size: number
  }
  
  // 使用情况
  usage: {
    deployment_count: number
    backtest_count: number
    last_used?: string
    in_production: boolean
  }
}

interface TrainingTask {
  task_id: string
  model_id: string
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'
  progress: number
  start_time: string
  end_time?: string
  estimated_remaining?: number
  current_epoch?: number
  total_epochs?: number
  current_metric?: Record<string, number>
  error_message?: string
  logs: string[]
}

interface ModelRegistry {
  models: QlibModel[]
  categories: string[]
  frameworks: string[]
  last_sync: string
}

interface HyperparameterOptimization {
  optimization_id: string
  model_type: string
  parameter_space: Record<string, any>
  optimization_method: 'grid' | 'random' | 'bayesian' | 'optuna'
  max_trials: number
  current_trial: number
  best_params?: Record<string, any>
  best_score?: number
  status: 'pending' | 'running' | 'completed' | 'failed'
  trials: Array<{
    trial_id: string
    params: Record<string, any>
    score: number
    status: string
  }>
}

interface ModelComparison {
  comparison_id: string
  models: string[]
  metrics: string[]
  comparison_type: 'performance' | 'resource' | 'comprehensive'
  results: Record<string, any>
  created_at: string
}

export const useQlibModelsStore = defineStore('qlib-models', () => {
  // 状态
  const modelRegistry = ref<QlibModel[]>([])
  const trainingTasks = ref<TrainingTask[]>([])
  const hyperparameterOptimizations = ref<HyperparameterOptimization[]>([])
  const modelComparisons = ref<ModelComparison[]>([])
  const selectedModels = ref<string[]>([])
  const currentEditingModel = ref<QlibModel | null>(null)
  
  // UI状态
  const loading = ref(false)
  const searchQuery = ref('')
  const selectedModelType = ref<string>('all')
  const selectedStatus = ref<string>('all')
  const selectedFramework = ref<string>('all')
  const sortBy = ref<'name' | 'created_at' | 'performance' | 'usage'>('created_at')
  const sortOrder = ref<'asc' | 'desc'>('desc')
  
  // 错误状态
  const error = ref<string | null>(null)
  const lastSyncTime = ref<string>('')

  // 计算属性
  const filteredModels = computed(() => {
    let filtered = modelRegistry.value

    if (searchQuery.value) {
      const query = searchQuery.value.toLowerCase()
      filtered = filtered.filter(model => 
        model.name.toLowerCase().includes(query) ||
        model.description?.toLowerCase().includes(query) ||
        model.model_id.toLowerCase().includes(query) ||
        model.tags.some(tag => tag.toLowerCase().includes(query))
      )
    }

    if (selectedModelType.value !== 'all') {
      filtered = filtered.filter(model => model.model_type === selectedModelType.value)
    }

    if (selectedStatus.value !== 'all') {
      filtered = filtered.filter(model => model.status === selectedStatus.value)
    }

    if (selectedFramework.value !== 'all') {
      filtered = filtered.filter(model => model.framework === selectedFramework.value)
    }

    // 排序
    filtered.sort((a, b) => {
      let comparison = 0
      
      switch (sortBy.value) {
        case 'name':
          comparison = a.name.localeCompare(b.name)
          break
        case 'created_at':
          comparison = new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
          break
        case 'performance':
          const aPerf = a.performance?.sharpe_ratio || 0
          const bPerf = b.performance?.sharpe_ratio || 0
          comparison = aPerf - bPerf
          break
        case 'usage':
          const aUsage = a.usage.deployment_count + a.usage.backtest_count
          const bUsage = b.usage.deployment_count + b.usage.backtest_count
          comparison = aUsage - bUsage
          break
      }

      return sortOrder.value === 'asc' ? comparison : -comparison
    })

    return filtered
  })

  const modelTypes = computed(() => {
    const types = new Set(modelRegistry.value.map(m => m.model_type))
    return Array.from(types).sort()
  })

  const frameworks = computed(() => {
    const fw = new Set(modelRegistry.value.map(m => m.framework))
    return Array.from(fw).sort()
  })

  const modelStats = computed(() => {
    return {
      total: modelRegistry.value.length,
      trained: modelRegistry.value.filter(m => m.status === 'trained').length,
      training: modelRegistry.value.filter(m => m.status === 'training').length,
      failed: modelRegistry.value.filter(m => m.status === 'failed').length,
      in_production: modelRegistry.value.filter(m => m.usage.in_production).length,
      avg_performance: modelRegistry.value
        .filter(m => m.performance?.sharpe_ratio)
        .reduce((sum, m) => sum + (m.performance?.sharpe_ratio || 0), 0) / 
        modelRegistry.value.filter(m => m.performance?.sharpe_ratio).length || 0
    }
  })

  const activeTrainingTasks = computed(() => {
    return trainingTasks.value.filter(task => 
      task.status === 'running' || task.status === 'pending'
    )
  })

  const topPerformingModels = computed(() => {
    return modelRegistry.value
      .filter(m => m.performance?.sharpe_ratio)
      .sort((a, b) => (b.performance?.sharpe_ratio || 0) - (a.performance?.sharpe_ratio || 0))
      .slice(0, 10)
  })

  const selectedModelsList = computed(() => {
    return modelRegistry.value.filter(model => selectedModels.value.includes(model.model_id))
  })

  // Actions
  const loadModelRegistry = async (): Promise<void> => {
    loading.value = true
    error.value = null

    try {
      const response = await fetch('/api/v1/models/registry', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json'
        }
      })

      const result = await response.json()

      if (result.status === 'success') {
        modelRegistry.value = result.data.models || []
        lastSyncTime.value = new Date().toISOString()
      } else {
        throw new Error(result.message || '加载模型注册表失败')
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : '加载模型注册表失败'
      console.error('加载模型注册表失败:', err)
      
      // 降级到示例数据
      generateSampleModelRegistry()
    } finally {
      loading.value = false
    }
  }

  const generateSampleModelRegistry = (): void => {
    modelRegistry.value = [
      {
        model_id: 'model_lightgbm_001',
        name: 'LightGBM多因子模型v1',
        description: '基于LightGBM的多因子选股模型',
        model_type: 'lightgbm',
        framework: 'qlib',
        version: '1.0.0',
        created_at: '2024-01-01T10:00:00Z',
        updated_at: '2024-01-01T12:00:00Z',
        created_by: 'quant_researcher',
        status: 'trained',
        tags: ['多因子', 'lightgbm', '选股'],
        config: {
          model_params: {
            n_estimators: 100,
            learning_rate: 0.1,
            max_depth: 6,
            num_leaves: 31
          },
          data_config: {
            features: ['ROC20', 'MA20', 'RSI14'],
            label: 'LABEL0',
            universe: 'CSI300',
            start_time: '2020-01-01',
            end_time: '2023-12-31'
          },
          trainer_config: {
            early_stopping: true,
            validation_split: 0.2
          }
        },
        training_info: {
          start_time: '2024-01-01T10:00:00Z',
          end_time: '2024-01-01T12:00:00Z',
          duration: 7200,
          train_size: 150000,
          valid_size: 30000,
          test_size: 30000,
          resource_usage: {
            cpu_time: 7200,
            memory_peak: 2048
          }
        },
        performance: {
          train_metrics: { mse: 0.023, mae: 0.12 },
          valid_metrics: { mse: 0.025, mae: 0.13 },
          test_metrics: { mse: 0.027, mae: 0.14 },
          ic: 0.085,
          rank_ic: 0.078,
          sharpe_ratio: 1.45,
          annual_return: 0.28,
          max_drawdown: -0.08,
          information_ratio: 1.23
        },
        model_files: {
          model_path: '/models/lightgbm_001.pkl',
          config_path: '/models/lightgbm_001_config.json',
          log_path: '/logs/lightgbm_001.log',
          artifact_size: 1024 * 1024 * 50
        },
        usage: {
          deployment_count: 2,
          backtest_count: 15,
          last_used: '2024-01-10T09:00:00Z',
          in_production: true
        }
      },
      {
        model_id: 'model_lstm_001',
        name: 'LSTM时序预测模型',
        description: '基于LSTM的股价时序预测模型',
        model_type: 'lstm',
        framework: 'pytorch',
        version: '1.0.0',
        created_at: '2024-01-02T14:00:00Z',
        updated_at: '2024-01-02T18:00:00Z',
        created_by: 'ml_engineer',
        status: 'trained',
        tags: ['时序', 'lstm', '深度学习'],
        config: {
          model_params: {
            hidden_size: 128,
            num_layers: 2,
            dropout: 0.2,
            sequence_length: 20
          },
          data_config: {
            features: ['CLOSE', 'VOLUME', 'HIGH', 'LOW'],
            label: 'LABEL0',
            universe: 'CSI500',
            start_time: '2020-01-01',
            end_time: '2023-12-31'
          },
          trainer_config: {
            batch_size: 256,
            epochs: 100,
            learning_rate: 0.001,
            early_stopping: true
          }
        },
        training_info: {
          start_time: '2024-01-02T14:00:00Z',
          end_time: '2024-01-02T18:00:00Z',
          duration: 14400,
          train_size: 200000,
          valid_size: 40000,
          test_size: 40000,
          resource_usage: {
            cpu_time: 3600,
            memory_peak: 4096,
            gpu_time: 10800
          }
        },
        performance: {
          train_metrics: { mse: 0.018, mae: 0.10 },
          valid_metrics: { mse: 0.022, mae: 0.11 },
          test_metrics: { mse: 0.024, mae: 0.12 },
          ic: 0.092,
          rank_ic: 0.088,
          sharpe_ratio: 1.67,
          annual_return: 0.31,
          max_drawdown: -0.06,
          information_ratio: 1.45
        },
        model_files: {
          model_path: '/models/lstm_001.pth',
          config_path: '/models/lstm_001_config.json',
          log_path: '/logs/lstm_001.log',
          artifact_size: 1024 * 1024 * 120
        },
        usage: {
          deployment_count: 1,
          backtest_count: 8,
          last_used: '2024-01-08T15:00:00Z',
          in_production: false
        }
      }
    ]

    lastSyncTime.value = new Date().toISOString()
  }

  const registerModel = async (modelData: Partial<QlibModel>): Promise<QlibModel> => {
    const newModel: QlibModel = {
      model_id: modelData.model_id || `model_${Date.now()}`,
      name: modelData.name || '新模型',
      description: modelData.description || '',
      model_type: modelData.model_type || 'lightgbm',
      framework: modelData.framework || 'qlib',
      version: modelData.version || '1.0.0',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      created_by: 'current_user',
      status: 'registered',
      tags: modelData.tags || [],
      config: modelData.config || {
        model_params: {},
        data_config: {
          features: [],
          label: 'LABEL0',
          universe: 'CSI300',
          start_time: '2020-01-01',
          end_time: '2023-12-31'
        },
        trainer_config: {}
      },
      model_files: {
        model_path: '',
        config_path: '',
        log_path: '',
        artifact_size: 0
      },
      usage: {
        deployment_count: 0,
        backtest_count: 0,
        in_production: false
      }
    }

    modelRegistry.value.unshift(newModel)
    return newModel
  }

  const trainModel = async (modelId: string, trainConfig?: any): Promise<TrainingTask> => {
    const model = modelRegistry.value.find(m => m.model_id === modelId)
    if (!model) {
      throw new Error('模型不存在')
    }

    const trainingTask: TrainingTask = {
      task_id: `task_${Date.now()}`,
      model_id: modelId,
      status: 'pending',
      progress: 0,
      start_time: new Date().toISOString(),
      logs: [`开始训练模型 ${model.name}`]
    }

    trainingTasks.value.unshift(trainingTask)

    try {
      const response = await fetch('/api/v1/models/train', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          model_id: modelId,
          config: trainConfig || model.config
        })
      })

      const result = await response.json()

      if (result.status === 'success') {
        // 更新训练任务状态
        trainingTask.status = 'running'
        trainingTask.task_id = result.data.task_id || trainingTask.task_id
        
        // 模拟训练进度更新
        simulateTrainingProgress(trainingTask.task_id)
      } else {
        throw new Error(result.message || '启动训练失败')
      }
    } catch (err) {
      trainingTask.status = 'failed'
      trainingTask.error_message = err instanceof Error ? err.message : '训练失败'
      trainingTask.end_time = new Date().toISOString()
    }

    return trainingTask
  }

  const simulateTrainingProgress = (taskId: string): void => {
    const task = trainingTasks.value.find(t => t.task_id === taskId)
    if (!task) return

    const interval = setInterval(() => {
      if (task.status !== 'running') {
        clearInterval(interval)
        return
      }

      task.progress = Math.min(task.progress + Math.random() * 10, 100)
      task.logs.push(`训练进度: ${task.progress.toFixed(1)}%`)

      if (task.progress >= 100) {
        task.status = 'completed'
        task.end_time = new Date().toISOString()
        task.logs.push('训练完成')
        
        // 更新模型状态
        const model = modelRegistry.value.find(m => m.model_id === task.model_id)
        if (model) {
          model.status = 'trained'
          model.updated_at = new Date().toISOString()
        }
        
        clearInterval(interval)
      }
    }, 1000)
  }

  const cancelTraining = async (taskId: string): Promise<boolean> => {
    const task = trainingTasks.value.find(t => t.task_id === taskId)
    if (!task || task.status !== 'running') return false

    try {
      const response = await fetch(`/api/v1/models/training/${taskId}/cancel`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      })

      const result = await response.json()

      if (result.status === 'success') {
        task.status = 'cancelled'
        task.end_time = new Date().toISOString()
        task.logs.push('训练已取消')
        return true
      } else {
        throw new Error(result.message || '取消训练失败')
      }
    } catch (err) {
      console.error('取消训练失败:', err)
      return false
    }
  }

  const optimizeHyperparameters = async (modelType: string, parameterSpace: Record<string, any>): Promise<HyperparameterOptimization> => {
    const optimization: HyperparameterOptimization = {
      optimization_id: `opt_${Date.now()}`,
      model_type,
      parameter_space: parameterSpace,
      optimization_method: 'optuna',
      max_trials: 50,
      current_trial: 0,
      status: 'pending',
      trials: []
    }

    hyperparameterOptimizations.value.unshift(optimization)

    try {
      const response = await fetch('/api/v1/models/optimize', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          model_type,
          parameter_space: parameterSpace,
          max_trials: 50
        })
      })

      const result = await response.json()

      if (result.status === 'success') {
        optimization.status = 'running'
        // 模拟优化进度
        simulateOptimizationProgress(optimization.optimization_id)
      } else {
        throw new Error(result.message || '启动超参数优化失败')
      }
    } catch (err) {
      optimization.status = 'failed'
      console.error('超参数优化失败:', err)
    }

    return optimization
  }

  const simulateOptimizationProgress = (optimizationId: string): void => {
    const optimization = hyperparameterOptimizations.value.find(o => o.optimization_id === optimizationId)
    if (!optimization) return

    const interval = setInterval(() => {
      if (optimization.status !== 'running') {
        clearInterval(interval)
        return
      }

      optimization.current_trial += 1
      
      // 模拟试验结果
      const trial = {
        trial_id: `trial_${optimization.current_trial}`,
        params: generateRandomParams(optimization.parameter_space),
        score: Math.random() * 2,
        status: 'completed'
      }
      
      optimization.trials.push(trial)
      
      // 更新最佳结果
      if (!optimization.best_score || trial.score > optimization.best_score) {
        optimization.best_score = trial.score
        optimization.best_params = trial.params
      }

      if (optimization.current_trial >= optimization.max_trials) {
        optimization.status = 'completed'
        clearInterval(interval)
      }
    }, 2000)
  }

  const generateRandomParams = (parameterSpace: Record<string, any>): Record<string, any> => {
    const params: Record<string, any> = {}
    
    for (const [key, space] of Object.entries(parameterSpace)) {
      if (Array.isArray(space)) {
        params[key] = space[Math.floor(Math.random() * space.length)]
      } else if (typeof space === 'object' && space.min !== undefined && space.max !== undefined) {
        params[key] = Math.random() * (space.max - space.min) + space.min
      } else {
        params[key] = space
      }
    }
    
    return params
  }

  const compareModels = async (modelIds: string[], metrics: string[]): Promise<ModelComparison> => {
    const comparison: ModelComparison = {
      comparison_id: `comp_${Date.now()}`,
      models: modelIds,
      metrics,
      comparison_type: 'performance',
      results: {},
      created_at: new Date().toISOString()
    }

    try {
      const response = await fetch('/api/v1/models/compare', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          model_ids: modelIds,
          metrics
        })
      })

      const result = await response.json()

      if (result.status === 'success') {
        comparison.results = result.data.comparison_results
      } else {
        throw new Error(result.message || '模型比较失败')
      }
    } catch (err) {
      console.error('模型比较失败:', err)
      
      // 生成模拟比较结果
      comparison.results = generateMockComparisonResults(modelIds, metrics)
    }

    modelComparisons.value.unshift(comparison)
    return comparison
  }

  const generateMockComparisonResults = (modelIds: string[], metrics: string[]): Record<string, any> => {
    const results: Record<string, any> = {}
    
    modelIds.forEach(modelId => {
      results[modelId] = {}
      metrics.forEach(metric => {
        results[modelId][metric] = Math.random() * 2
      })
    })
    
    return results
  }

  const deleteModel = async (modelId: string): Promise<boolean> => {
    const modelIndex = modelRegistry.value.findIndex(m => m.model_id === modelId)
    if (modelIndex === -1) return false

    try {
      const response = await fetch(`/api/v1/models/${modelId}`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json'
        }
      })

      const result = await response.json()

      if (result.status === 'success') {
        modelRegistry.value.splice(modelIndex, 1)
        
        // 从选中列表中移除
        const selectedIndex = selectedModels.value.indexOf(modelId)
        if (selectedIndex > -1) {
          selectedModels.value.splice(selectedIndex, 1)
        }
        
        return true
      } else {
        throw new Error(result.message || '删除模型失败')
      }
    } catch (err) {
      console.error('删除模型失败:', err)
      return false
    }
  }

  const updateModel = async (modelId: string, updates: Partial<QlibModel>): Promise<QlibModel | null> => {
    const modelIndex = modelRegistry.value.findIndex(m => m.model_id === modelId)
    if (modelIndex === -1) return null

    const updatedModel = {
      ...modelRegistry.value[modelIndex],
      ...updates,
      updated_at: new Date().toISOString()
    }

    modelRegistry.value[modelIndex] = updatedModel
    return updatedModel
  }

  const exportModel = async (modelId: string): Promise<string> => {
    const model = modelRegistry.value.find(m => m.model_id === modelId)
    if (!model) throw new Error('模型不存在')

    return JSON.stringify({
      model,
      exported_at: new Date().toISOString(),
      version: '1.0'
    }, null, 2)
  }

  const importModel = async (modelData: string): Promise<QlibModel> => {
    const data = JSON.parse(modelData)
    const model = data.model
    
    // 生成新的model_id以避免冲突
    model.model_id = `${model.model_id}_imported_${Date.now()}`
    model.created_at = new Date().toISOString()
    model.updated_at = new Date().toISOString()
    
    return await registerModel(model)
  }

  const toggleModelSelection = (modelId: string): void => {
    const index = selectedModels.value.indexOf(modelId)
    if (index > -1) {
      selectedModels.value.splice(index, 1)
    } else {
      selectedModels.value.push(modelId)
    }
  }

  const selectAllModels = (): void => {
    selectedModels.value = filteredModels.value.map(m => m.model_id)
  }

  const clearSelection = (): void => {
    selectedModels.value = []
  }

  const searchModels = (query: string): void => {
    searchQuery.value = query
  }

  const setFilters = (filters: {
    modelType?: string
    status?: string
    framework?: string
  }): void => {
    if (filters.modelType !== undefined) selectedModelType.value = filters.modelType
    if (filters.status !== undefined) selectedStatus.value = filters.status
    if (filters.framework !== undefined) selectedFramework.value = filters.framework
  }

  const setSorting = (field: typeof sortBy.value, order: typeof sortOrder.value): void => {
    sortBy.value = field
    sortOrder.value = order
  }

  const refreshModelRegistry = async (): Promise<void> => {
    await loadModelRegistry()
  }

  const getTrainingTask = (taskId: string): TrainingTask | undefined => {
    return trainingTasks.value.find(t => t.task_id === taskId)
  }

  const getOptimization = (optimizationId: string): HyperparameterOptimization | undefined => {
    return hyperparameterOptimizations.value.find(o => o.optimization_id === optimizationId)
  }

  return {
    // State
    modelRegistry,
    trainingTasks,
    hyperparameterOptimizations,
    modelComparisons,
    selectedModels,
    currentEditingModel,
    loading,
    searchQuery,
    selectedModelType,
    selectedStatus,
    selectedFramework,
    sortBy,
    sortOrder,
    error,
    lastSyncTime,

    // Computed
    filteredModels,
    modelTypes,
    frameworks,
    modelStats,
    activeTrainingTasks,
    topPerformingModels,
    selectedModelsList,

    // Actions
    loadModelRegistry,
    generateSampleModelRegistry,
    registerModel,
    trainModel,
    cancelTraining,
    optimizeHyperparameters,
    compareModels,
    deleteModel,
    updateModel,
    exportModel,
    importModel,
    toggleModelSelection,
    selectAllModels,
    clearSelection,
    searchModels,
    setFilters,
    setSorting,
    refreshModelRegistry,
    getTrainingTask,
    getOptimization
  }
})