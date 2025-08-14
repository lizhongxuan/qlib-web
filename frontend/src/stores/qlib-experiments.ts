import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

// Qlib实验相关的类型定义
interface QlibExperiment {
  experiment_id: string
  name: string
  description?: string
  created_at: string
  updated_at: string
  created_by: string
  status: 'pending' | 'running' | 'finished' | 'failed' | 'cancelled'
  tags: string[]
  
  // 实验配置
  config: {
    dataset: {
      class: string
      module_path: string
      kwargs: {
        handler: any
        segments: {
          train: [string, string]
          valid: [string, string]
          test: [string, string]
        }
      }
    }
    
    model: {
      class: string
      module_path: string
      kwargs: Record<string, any>
    }
    
    task: {
      model: any
      dataset: any
      trainer?: any
    }
    
    recorder: {
      class: string
      module_path: string
      kwargs: {
        uri?: string
        experiment_name?: string
      }
    }
  }
  
  // 运行信息
  run_info?: {
    start_time: string
    end_time?: string
    duration?: number
    host: string
    python_version: string
    qlib_version: string
    git_commit?: string
    command: string
    working_directory: string
  }
  
  // 实验结果
  results?: {
    model_performance: {
      train: Record<string, number>
      valid: Record<string, number>
      test: Record<string, number>
    }
    
    prediction_score: {
      ic: number
      rank_ic: number
      icir: number
      rank_icir: number
    }
    
    backtest_results?: {
      return_wo_cost: number
      return_w_cost: number
      annual_return: number
      max_drawdown: number
      sharpe_ratio: number
      information_ratio: number
      win_rate: number
    }
    
    analysis_data?: {
      cumulative_returns: number[]
      positions: any[]
      trades: any[]
      feature_importance?: Record<string, number>
    }
  }
  
  // 实验工件
  artifacts: {
    model_path?: string
    prediction_path?: string
    backtest_path?: string
    logs_path?: string
    plots_path?: string
    total_size: number
  }
  
  // 资源使用情况
  resource_usage?: {
    cpu_time: number
    memory_peak: number
    disk_usage: number
    gpu_time?: number
    gpu_memory?: number
  }
  
  // 实验依赖
  dependencies: {
    parent_experiments?: string[]
    child_experiments?: string[]
    related_experiments?: string[]
    data_dependencies?: string[]
    model_dependencies?: string[]
  }
  
  // 版本控制
  version_info: {
    version: number
    is_latest: boolean
    previous_version?: string
    next_version?: string
    changelog?: string
  }
}

interface ExperimentWorkflow {
  workflow_id: string
  name: string
  description: string
  experiments: string[]
  status: 'draft' | 'running' | 'completed' | 'failed'
  created_at: string
  current_step: number
  total_steps: number
  
  // 工作流配置
  config: {
    execution_mode: 'sequential' | 'parallel' | 'conditional'
    retry_policy: {
      max_retries: number
      retry_delay: number
    }
    timeout: number
    notifications: {
      on_success: boolean
      on_failure: boolean
      on_completion: boolean
    }
  }
  
  // 工作流步骤
  steps: Array<{
    step_id: string
    name: string
    experiment_id: string
    status: 'pending' | 'running' | 'completed' | 'failed' | 'skipped'
    dependencies: string[]
    start_time?: string
    end_time?: string
    error_message?: string
  }>
}

interface ExperimentTemplate {
  template_id: string
  name: string
  description: string
  category: string
  config_template: any
  parameters: Array<{
    name: string
    type: 'string' | 'number' | 'boolean' | 'array' | 'object'
    description: string
    required: boolean
    default?: any
    options?: any[]
  }>
  created_at: string
  usage_count: number
  rating: number
}

interface ExperimentComparison {
  comparison_id: string
  name: string
  experiments: string[]
  metrics: string[]
  created_at: string
  
  results: {
    metric_comparison: Record<string, Record<string, number>>
    statistical_tests: Record<string, {
      p_value: number
      significant: boolean
      test_type: string
    }>
    recommendations: string[]
  }
}

export const useQlibExperimentsStore = defineStore('qlib-experiments', () => {
  // 状态
  const experiments = ref<QlibExperiment[]>([])
  const workflows = ref<ExperimentWorkflow[]>([])
  const templates = ref<ExperimentTemplate[]>([])
  const comparisons = ref<ExperimentComparison[]>([])
  const selectedExperiments = ref<string[]>([])
  const currentEditingExperiment = ref<QlibExperiment | null>(null)
  
  // UI状态
  const loading = ref(false)
  const searchQuery = ref('')
  const selectedStatus = ref<string>('all')
  const selectedTimeRange = ref<'day' | 'week' | 'month' | 'all'>('all')
  const sortBy = ref<'created_at' | 'name' | 'performance' | 'duration'>('created_at')
  const sortOrder = ref<'asc' | 'desc'>('desc')
  const currentView = ref<'list' | 'grid' | 'timeline'>('list')
  
  // 错误状态
  const error = ref<string | null>(null)
  const lastSyncTime = ref<string>('')

  // 计算属性
  const filteredExperiments = computed(() => {
    let filtered = experiments.value

    // 搜索过滤
    if (searchQuery.value) {
      const query = searchQuery.value.toLowerCase()
      filtered = filtered.filter(exp => 
        exp.name.toLowerCase().includes(query) ||
        exp.description?.toLowerCase().includes(query) ||
        exp.experiment_id.toLowerCase().includes(query) ||
        exp.tags.some(tag => tag.toLowerCase().includes(query))
      )
    }

    // 状态过滤
    if (selectedStatus.value !== 'all') {
      filtered = filtered.filter(exp => exp.status === selectedStatus.value)
    }

    // 时间范围过滤
    if (selectedTimeRange.value !== 'all') {
      const now = new Date()
      const timeLimit = new Date()
      
      switch (selectedTimeRange.value) {
        case 'day':
          timeLimit.setDate(now.getDate() - 1)
          break
        case 'week':
          timeLimit.setDate(now.getDate() - 7)
          break
        case 'month':
          timeLimit.setMonth(now.getMonth() - 1)
          break
      }
      
      filtered = filtered.filter(exp => 
        new Date(exp.created_at) >= timeLimit
      )
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
          const aPerf = a.results?.prediction_score?.icir || 0
          const bPerf = b.results?.prediction_score?.icir || 0
          comparison = aPerf - bPerf
          break
        case 'duration':
          const aDuration = a.run_info?.duration || 0
          const bDuration = b.run_info?.duration || 0
          comparison = aDuration - bDuration
          break
      }

      return sortOrder.value === 'asc' ? comparison : -comparison
    })

    return filtered
  })

  const experimentStats = computed(() => {
    return {
      total: experiments.value.length,
      running: experiments.value.filter(e => e.status === 'running').length,
      finished: experiments.value.filter(e => e.status === 'finished').length,
      failed: experiments.value.filter(e => e.status === 'failed').length,
      avg_duration: experiments.value
        .filter(e => e.run_info?.duration)
        .reduce((sum, e) => sum + (e.run_info?.duration || 0), 0) / 
        experiments.value.filter(e => e.run_info?.duration).length || 0,
      success_rate: experiments.value.length > 0 ? 
        experiments.value.filter(e => e.status === 'finished').length / experiments.value.length * 100 : 0
    }
  })

  const topPerformingExperiments = computed(() => {
    return experiments.value
      .filter(e => e.results?.prediction_score?.icir)
      .sort((a, b) => (b.results?.prediction_score?.icir || 0) - (a.results?.prediction_score?.icir || 0))
      .slice(0, 10)
  })

  const activeWorkflows = computed(() => {
    return workflows.value.filter(w => w.status === 'running')
  })

  const selectedExperimentsList = computed(() => {
    return experiments.value.filter(exp => selectedExperiments.value.includes(exp.experiment_id))
  })

  const experimentsByDate = computed(() => {
    const grouped: Record<string, QlibExperiment[]> = {}
    
    experiments.value.forEach(exp => {
      const date = exp.created_at.split('T')[0]
      if (!grouped[date]) {
        grouped[date] = []
      }
      grouped[date].push(exp)
    })
    
    return grouped
  })

  // Actions
  const loadExperiments = async (): Promise<void> => {
    loading.value = true
    error.value = null

    try {
      const response = await fetch('/api/v1/experiments', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json'
        }
      })

      const result = await response.json()

      if (result.status === 'success') {
        experiments.value = result.data.experiments || []
        lastSyncTime.value = new Date().toISOString()
      } else {
        throw new Error(result.message || '加载实验记录失败')
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : '加载实验记录失败'
      console.error('加载实验记录失败:', err)
      
      // 降级到示例数据
      generateSampleExperiments()
    } finally {
      loading.value = false
    }
  }

  const generateSampleExperiments = (): void => {
    experiments.value = [
      {
        experiment_id: 'exp_001',
        name: 'LightGBM多因子策略v1',
        description: '基于Alpha158因子集的LightGBM模型实验',
        created_at: '2024-01-15T10:30:00Z',
        updated_at: '2024-01-15T12:45:00Z',
        created_by: 'quant_researcher',
        status: 'finished',
        tags: ['多因子', 'lightgbm', '选股'],
        
        config: {
          dataset: {
            class: 'DatasetH',
            module_path: 'qlib.data.dataset',
            kwargs: {
              handler: {
                class: 'Alpha158',
                module_path: 'qlib.contrib.data.handler'
              },
              segments: {
                train: ['2020-01-01', '2021-12-31'],
                valid: ['2022-01-01', '2022-12-31'],
                test: ['2023-01-01', '2023-12-31']
              }
            }
          },
          
          model: {
            class: 'LGBModel',
            module_path: 'qlib.contrib.model.lightgbm',
            kwargs: {
              n_estimators: 100,
              learning_rate: 0.1
            }
          },
          
          task: {},
          
          recorder: {
            class: 'MLflowRecorder',
            module_path: 'qlib.workflow.recorder',
            kwargs: {
              experiment_name: 'lightgbm_multifactor'
            }
          }
        },
        
        run_info: {
          start_time: '2024-01-15T10:30:00Z',
          end_time: '2024-01-15T12:45:00Z',
          duration: 8100,
          host: 'qlib-server-01',
          python_version: '3.8.10',
          qlib_version: '0.9.1',
          command: 'python run_exp.py --config lightgbm_config.yaml',
          working_directory: '/workspace/experiments'
        },
        
        results: {
          model_performance: {
            train: { mse: 0.023, mae: 0.12, r2: 0.78 },
            valid: { mse: 0.025, mae: 0.13, r2: 0.76 },
            test: { mse: 0.027, mae: 0.14, r2: 0.74 }
          },
          
          prediction_score: {
            ic: 0.085,
            rank_ic: 0.078,
            icir: 1.234,
            rank_icir: 1.156
          },
          
          backtest_results: {
            return_wo_cost: 0.285,
            return_w_cost: 0.267,
            annual_return: 0.267,
            max_drawdown: -0.082,
            sharpe_ratio: 1.45,
            information_ratio: 1.23,
            win_rate: 0.583
          }
        },
        
        artifacts: {
          model_path: '/artifacts/exp_001/model.pkl',
          prediction_path: '/artifacts/exp_001/prediction.pkl',
          backtest_path: '/artifacts/exp_001/backtest.pkl',
          logs_path: '/artifacts/exp_001/logs.txt',
          plots_path: '/artifacts/exp_001/plots/',
          total_size: 1024 * 1024 * 150
        },
        
        resource_usage: {
          cpu_time: 7200,
          memory_peak: 4096,
          disk_usage: 2048
        },
        
        dependencies: {
          data_dependencies: ['CSI300_data', 'Alpha158_features'],
          model_dependencies: []
        },
        
        version_info: {
          version: 1,
          is_latest: true
        }
      },
      
      {
        experiment_id: 'exp_002',
        name: 'LSTM时序预测实验',
        description: '基于LSTM的股价时序预测模型',
        created_at: '2024-01-16T14:20:00Z',
        updated_at: '2024-01-16T18:35:00Z',
        created_by: 'ml_engineer',
        status: 'running',
        tags: ['时序', 'lstm', '深度学习'],
        
        config: {
          dataset: {
            class: 'TSDatasetH',
            module_path: 'qlib.data.dataset',
            kwargs: {
              handler: {
                class: 'TSDataHandler',
                module_path: 'qlib.contrib.data.handler'
              },
              segments: {
                train: ['2020-01-01', '2022-12-31'],
                valid: ['2023-01-01', '2023-06-30'],
                test: ['2023-07-01', '2023-12-31']
              }
            }
          },
          
          model: {
            class: 'LSTMModel',
            module_path: 'qlib.contrib.model.pytorch_lstm',
            kwargs: {
              d_feat: 20,
              hidden_size: 128,
              num_layers: 2
            }
          },
          
          task: {},
          
          recorder: {
            class: 'MLflowRecorder',
            module_path: 'qlib.workflow.recorder',
            kwargs: {
              experiment_name: 'lstm_timeseries'
            }
          }
        },
        
        run_info: {
          start_time: '2024-01-16T14:20:00Z',
          host: 'gpu-server-01',
          python_version: '3.8.10',
          qlib_version: '0.9.1',
          command: 'python run_exp.py --config lstm_config.yaml',
          working_directory: '/workspace/experiments'
        },
        
        artifacts: {
          logs_path: '/artifacts/exp_002/logs.txt',
          total_size: 1024 * 1024 * 80
        },
        
        dependencies: {
          data_dependencies: ['CSI500_data', 'TS_features'],
          model_dependencies: []
        },
        
        version_info: {
          version: 1,
          is_latest: true
        }
      }
    ]

    lastSyncTime.value = new Date().toISOString()
  }

  const createExperiment = async (experimentData: Partial<QlibExperiment>): Promise<QlibExperiment> => {
    const newExperiment: QlibExperiment = {
      experiment_id: experimentData.experiment_id || `exp_${Date.now()}`,
      name: experimentData.name || '新实验',
      description: experimentData.description || '',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      created_by: 'current_user',
      status: 'pending',
      tags: experimentData.tags || [],
      config: experimentData.config || {
        dataset: {
          class: 'DatasetH',
          module_path: 'qlib.data.dataset',
          kwargs: {
            handler: {},
            segments: {
              train: ['2020-01-01', '2021-12-31'],
              valid: ['2022-01-01', '2022-12-31'],
              test: ['2023-01-01', '2023-12-31']
            }
          }
        },
        model: {
          class: 'LGBModel',
          module_path: 'qlib.contrib.model.lightgbm',
          kwargs: {}
        },
        task: {},
        recorder: {
          class: 'MLflowRecorder',
          module_path: 'qlib.workflow.recorder',
          kwargs: {}
        }
      },
      artifacts: {
        total_size: 0
      },
      dependencies: {},
      version_info: {
        version: 1,
        is_latest: true
      }
    }

    experiments.value.unshift(newExperiment)
    return newExperiment
  }

  const runExperiment = async (experimentId: string): Promise<void> => {
    const experiment = experiments.value.find(e => e.experiment_id === experimentId)
    if (!experiment) {
      throw new Error('实验不存在')
    }

    try {
      const response = await fetch(`/api/v1/experiments/${experimentId}/run`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          config: experiment.config
        })
      })

      const result = await response.json()

      if (result.status === 'success') {
        experiment.status = 'running'
        experiment.run_info = {
          start_time: new Date().toISOString(),
          host: 'local',
          python_version: '3.8.10',
          qlib_version: '0.9.1',
          command: 'python run_exp.py',
          working_directory: '/workspace'
        }
        
        // 模拟实验运行进度
        simulateExperimentProgress(experimentId)
      } else {
        throw new Error(result.message || '启动实验失败')
      }
    } catch (err) {
      experiment.status = 'failed'
      console.error('运行实验失败:', err)
    }
  }

  const simulateExperimentProgress = (experimentId: string): void => {
    const experiment = experiments.value.find(e => e.experiment_id === experimentId)
    if (!experiment) return

    let progress = 0
    const interval = setInterval(() => {
      if (experiment.status !== 'running') {
        clearInterval(interval)
        return
      }

      progress += Math.random() * 10
      
      if (progress >= 100) {
        experiment.status = 'finished'
        experiment.run_info!.end_time = new Date().toISOString()
        experiment.run_info!.duration = Math.floor((new Date().getTime() - new Date(experiment.run_info!.start_time).getTime()) / 1000)
        
        // 生成模拟结果
        experiment.results = {
          model_performance: {
            train: { mse: Math.random() * 0.05, mae: Math.random() * 0.2, r2: 0.7 + Math.random() * 0.2 },
            valid: { mse: Math.random() * 0.05, mae: Math.random() * 0.2, r2: 0.7 + Math.random() * 0.2 },
            test: { mse: Math.random() * 0.05, mae: Math.random() * 0.2, r2: 0.7 + Math.random() * 0.2 }
          },
          prediction_score: {
            ic: Math.random() * 0.1,
            rank_ic: Math.random() * 0.1,
            icir: Math.random() * 2,
            rank_icir: Math.random() * 2
          },
          backtest_results: {
            return_wo_cost: Math.random() * 0.4,
            return_w_cost: Math.random() * 0.3,
            annual_return: Math.random() * 0.3,
            max_drawdown: -Math.random() * 0.15,
            sharpe_ratio: Math.random() * 2,
            information_ratio: Math.random() * 2,
            win_rate: 0.4 + Math.random() * 0.3
          }
        }
        
        clearInterval(interval)
      }
    }, 2000)
  }

  const cancelExperiment = async (experimentId: string): Promise<boolean> => {
    const experiment = experiments.value.find(e => e.experiment_id === experimentId)
    if (!experiment || experiment.status !== 'running') return false

    try {
      const response = await fetch(`/api/v1/experiments/${experimentId}/cancel`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      })

      const result = await response.json()

      if (result.status === 'success') {
        experiment.status = 'cancelled'
        if (experiment.run_info) {
          experiment.run_info.end_time = new Date().toISOString()
        }
        return true
      } else {
        throw new Error(result.message || '取消实验失败')
      }
    } catch (err) {
      console.error('取消实验失败:', err)
      return false
    }
  }

  const deleteExperiment = async (experimentId: string): Promise<boolean> => {
    const experimentIndex = experiments.value.findIndex(e => e.experiment_id === experimentId)
    if (experimentIndex === -1) return false

    try {
      const response = await fetch(`/api/v1/experiments/${experimentId}`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json'
        }
      })

      const result = await response.json()

      if (result.status === 'success') {
        experiments.value.splice(experimentIndex, 1)
        
        // 从选中列表中移除
        const selectedIndex = selectedExperiments.value.indexOf(experimentId)
        if (selectedIndex > -1) {
          selectedExperiments.value.splice(selectedIndex, 1)
        }
        
        return true
      } else {
        throw new Error(result.message || '删除实验失败')
      }
    } catch (err) {
      console.error('删除实验失败:', err)
      return false
    }
  }

  const cloneExperiment = async (experimentId: string): Promise<QlibExperiment | null> => {
    const originalExperiment = experiments.value.find(e => e.experiment_id === experimentId)
    if (!originalExperiment) return null

    const clonedData = {
      ...originalExperiment,
      name: `${originalExperiment.name} (克隆)`,
      status: 'pending' as const,
      tags: [...originalExperiment.tags, '克隆']
    }

    return await createExperiment(clonedData)
  }

  const compareExperiments = async (experimentIds: string[], metrics: string[]): Promise<ExperimentComparison> => {
    const comparison: ExperimentComparison = {
      comparison_id: `comp_${Date.now()}`,
      name: `实验对比_${new Date().toLocaleDateString()}`,
      experiments: experimentIds,
      metrics,
      created_at: new Date().toISOString(),
      results: {
        metric_comparison: {},
        statistical_tests: {},
        recommendations: []
      }
    }

    try {
      const response = await fetch('/api/v1/experiments/compare', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          experiment_ids: experimentIds,
          metrics
        })
      })

      const result = await response.json()

      if (result.status === 'success') {
        comparison.results = result.data.comparison_results
      } else {
        throw new Error(result.message || '实验对比失败')
      }
    } catch (err) {
      console.error('实验对比失败:', err)
      
      // 生成模拟对比结果
      comparison.results = generateMockComparisonResults(experimentIds, metrics)
    }

    comparisons.value.unshift(comparison)
    return comparison
  }

  const generateMockComparisonResults = (experimentIds: string[], metrics: string[]): any => {
    const metricComparison: Record<string, Record<string, number>> = {}
    const statisticalTests: Record<string, any> = {}
    
    metrics.forEach(metric => {
      metricComparison[metric] = {}
      experimentIds.forEach(expId => {
        metricComparison[metric][expId] = Math.random() * 2
      })
      
      statisticalTests[metric] = {
        p_value: Math.random() * 0.1,
        significant: Math.random() > 0.5,
        test_type: 't-test'
      }
    })
    
    return {
      metric_comparison: metricComparison,
      statistical_tests: statisticalTests,
      recommendations: [
        '实验A在IC指标上表现最佳',
        '建议进一步调优实验B的参数',
        '实验C在稳定性方面表现突出'
      ]
    }
  }

  const createWorkflow = async (workflowData: Partial<ExperimentWorkflow>): Promise<ExperimentWorkflow> => {
    const newWorkflow: ExperimentWorkflow = {
      workflow_id: workflowData.workflow_id || `workflow_${Date.now()}`,
      name: workflowData.name || '新工作流',
      description: workflowData.description || '',
      experiments: workflowData.experiments || [],
      status: 'draft',
      created_at: new Date().toISOString(),
      current_step: 0,
      total_steps: workflowData.experiments?.length || 0,
      config: workflowData.config || {
        execution_mode: 'sequential',
        retry_policy: {
          max_retries: 3,
          retry_delay: 60
        },
        timeout: 3600,
        notifications: {
          on_success: true,
          on_failure: true,
          on_completion: true
        }
      },
      steps: workflowData.experiments?.map((expId, index) => ({
        step_id: `step_${index}`,
        name: `步骤 ${index + 1}`,
        experiment_id: expId,
        status: 'pending',
        dependencies: index > 0 ? [`step_${index - 1}`] : []
      })) || []
    }

    workflows.value.unshift(newWorkflow)
    return newWorkflow
  }

  const exportExperiment = async (experimentId: string): Promise<string> => {
    const experiment = experiments.value.find(e => e.experiment_id === experimentId)
    if (!experiment) throw new Error('实验不存在')

    return JSON.stringify({
      experiment,
      exported_at: new Date().toISOString(),
      version: '1.0'
    }, null, 2)
  }

  const importExperiment = async (experimentData: string): Promise<QlibExperiment> => {
    const data = JSON.parse(experimentData)
    const experiment = data.experiment
    
    // 生成新的experiment_id以避免冲突
    experiment.experiment_id = `${experiment.experiment_id}_imported_${Date.now()}`
    experiment.created_at = new Date().toISOString()
    experiment.updated_at = new Date().toISOString()
    experiment.status = 'pending'
    
    return await createExperiment(experiment)
  }

  const toggleExperimentSelection = (experimentId: string): void => {
    const index = selectedExperiments.value.indexOf(experimentId)
    if (index > -1) {
      selectedExperiments.value.splice(index, 1)
    } else {
      selectedExperiments.value.push(experimentId)
    }
  }

  const selectAllExperiments = (): void => {
    selectedExperiments.value = filteredExperiments.value.map(e => e.experiment_id)
  }

  const clearSelection = (): void => {
    selectedExperiments.value = []
  }

  const searchExperiments = (query: string): void => {
    searchQuery.value = query
  }

  const setFilters = (filters: {
    status?: string
    timeRange?: string
  }): void => {
    if (filters.status !== undefined) selectedStatus.value = filters.status
    if (filters.timeRange !== undefined) selectedTimeRange.value = filters.timeRange as any
  }

  const setSorting = (field: typeof sortBy.value, order: typeof sortOrder.value): void => {
    sortBy.value = field
    sortOrder.value = order
  }

  const setView = (view: typeof currentView.value): void => {
    currentView.value = view
  }

  const refreshExperiments = async (): Promise<void> => {
    await loadExperiments()
  }

  const getExperiment = (experimentId: string): QlibExperiment | undefined => {
    return experiments.value.find(e => e.experiment_id === experimentId)
  }

  const getWorkflow = (workflowId: string): ExperimentWorkflow | undefined => {
    return workflows.value.find(w => w.workflow_id === workflowId)
  }

  return {
    // State
    experiments,
    workflows,
    templates,
    comparisons,
    selectedExperiments,
    currentEditingExperiment,
    loading,
    searchQuery,
    selectedStatus,
    selectedTimeRange,
    sortBy,
    sortOrder,
    currentView,
    error,
    lastSyncTime,

    // Computed
    filteredExperiments,
    experimentStats,
    topPerformingExperiments,
    activeWorkflows,
    selectedExperimentsList,
    experimentsByDate,

    // Actions
    loadExperiments,
    generateSampleExperiments,
    createExperiment,
    runExperiment,
    cancelExperiment,
    deleteExperiment,
    cloneExperiment,
    compareExperiments,
    createWorkflow,
    exportExperiment,
    importExperiment,
    toggleExperimentSelection,
    selectAllExperiments,
    clearSelection,
    searchExperiments,
    setFilters,
    setSorting,
    setView,
    refreshExperiments,
    getExperiment,
    getWorkflow
  }
})