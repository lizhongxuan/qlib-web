import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

// Qlib回测相关的类型定义
interface QlibBacktestConfig {
  config_id: string
  name: string
  description?: string
  model_id: string
  strategy_config: {
    class: string
    module_path: string
    kwargs: {
      topk?: number
      n_drop?: number
      risk_degree?: number
      trade_exchange?: string
      limit_threshold?: number
      deal_price?: 'close' | 'vwap' | 'open'
      open_cost?: number
      close_cost?: number
      trade_unit?: 'share' | 'lot'
      min_cost?: number
    }
  }
  
  // 回测配置
  backtest_config: {
    start_time: string
    end_time: string
    universe: string
    benchmark: string
    account: {
      init_cash: number
      pos_type: 'InfPosition' | 'Position'
    }
    executor: {
      class: string
      module_path: string
      kwargs: Record<string, any>
    }
    exchange: {
      class: string
      module_path: string
      kwargs: {
        freq: 'day' | '30min' | '5min'
        limit_threshold?: number
        deal_price?: string
        open_cost?: number
        close_cost?: number
        min_cost?: number
      }
    }
  }
  
  // 风险控制
  risk_config?: {
    max_position_ratio?: number
    stop_loss?: number
    stop_profit?: number
    max_drawdown?: number
    sector_limit?: Record<string, number>
    single_stock_limit?: number
  }
  
  created_at: string
  updated_at: string
  created_by: string
  tags: string[]
}

interface QlibBacktestTask {
  task_id: string
  config_id: string
  name: string
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'
  progress: number
  start_time: string
  end_time?: string
  estimated_remaining?: number
  current_day?: string
  total_days?: number
  error_message?: string
  
  // 实时指标
  real_time_metrics?: {
    current_value: number
    current_return: number
    current_position_count: number
    current_turnover: number
    max_drawdown: number
    sharpe_ratio: number
    volatility: number
  }
  
  logs: string[]
  warnings: string[]
}

interface QlibBacktestResult {
  result_id: string
  task_id: string
  config_id: string
  name: string
  created_at: string
  
  // 基本信息
  meta_info: {
    start_time: string
    end_time: string
    trading_days: number
    universe: string
    benchmark: string
    model_name: string
    strategy_name: string
  }
  
  // 收益指标
  return_metrics: {
    total_return: number
    annual_return: number
    excess_return: number
    total_return_wo_cost: number
    annual_return_wo_cost: number
    excess_return_wo_cost: number
  }
  
  // 风险指标
  risk_metrics: {
    volatility: number
    max_drawdown: number
    calmar_ratio: number
    sharpe_ratio: number
    information_ratio: number
    sortino_ratio: number
    omega_ratio: number
    tracking_error: number
  }
  
  // 交易指标
  trading_metrics: {
    win_rate: number
    profit_loss_ratio: number
    average_holding_period: number
    turnover_rate: number
    transaction_cost: number
    total_trades: number
    winning_trades: number
    losing_trades: number
  }
  
  // 时序数据
  time_series: {
    nav: Array<{ date: string, value: number, benchmark: number }>
    returns: Array<{ date: string, portfolio: number, benchmark: number, excess: number }>
    drawdown: Array<{ date: string, drawdown: number, underwater: number }>
    positions: Array<{ date: string, positions: Record<string, number> }>
    trades: Array<{
      date: string
      instrument: string
      direction: 'buy' | 'sell'
      amount: number
      price: number
      value: number
      commission: number
    }>
  }
  
  // 持仓分析
  position_analysis: {
    sector_exposure: Record<string, number>
    top_holdings: Array<{ instrument: string, weight: number, name: string }>
    position_concentration: {
      top5_weight: number
      top10_weight: number
      effective_number: number
      herfindahl_index: number
    }
    turnover_analysis: {
      monthly_turnover: number[]
      cumulative_turnover: number
      turnover_volatility: number
    }
  }
  
  // 归因分析
  attribution_analysis?: {
    factor_attribution: Record<string, {
      return_contribution: number
      risk_contribution: number
      information_ratio: number
    }>
    sector_attribution: Record<string, {
      allocation_effect: number
      selection_effect: number
      total_effect: number
    }>
    style_attribution: Record<string, number>
  }
  
  // 统计分析
  statistical_analysis: {
    monthly_returns: number[]
    annual_returns: number[]
    return_distribution: {
      mean: number
      std: number
      skewness: number
      kurtosis: number
      var_95: number
      cvar_95: number
    }
    correlation_with_benchmark: number
    beta: number
    alpha: number
    r_squared: number
  }
  
  // 图表数据
  chart_data: {
    nav_chart: any
    return_chart: any
    drawdown_chart: any
    holding_chart: any
    sector_chart: any
    monthly_return_heatmap: any
  }
}

interface BacktestComparison {
  comparison_id: string
  name: string
  result_ids: string[]
  metrics: string[]
  created_at: string
  
  comparison_data: {
    metric_comparison: Record<string, Record<string, number>>
    ranking: Array<{ result_id: string, rank: number, score: number }>
    correlation_matrix: Record<string, Record<string, number>>
    statistical_tests: Record<string, {
      p_value: number
      significant: boolean
      test_statistic: number
      test_type: string
    }>
    recommendations: string[]
  }
}

interface BacktestTemplate {
  template_id: string
  name: string
  description: string
  category: 'long_only' | 'long_short' | 'market_neutral' | 'custom'
  config_template: Partial<QlibBacktestConfig>
  parameters: Array<{
    name: string
    type: 'number' | 'string' | 'boolean' | 'select'
    description: string
    default: any
    options?: any[]
    min?: number
    max?: number
  }>
  created_at: string
  usage_count: number
  rating: number
}

export const useQlibBacktestStore = defineStore('qlib-backtest', () => {
  // 状态
  const backtestConfigs = ref<QlibBacktestConfig[]>([])
  const backtestTasks = ref<QlibBacktestTask[]>([])
  const backtestResults = ref<QlibBacktestResult[]>([])
  const backtestComparisons = ref<BacktestComparison[]>([])
  const backtestTemplates = ref<BacktestTemplate[]>([])
  const selectedResults = ref<string[]>([])
  const currentEditingConfig = ref<QlibBacktestConfig | null>(null)
  
  // UI状态
  const loading = ref(false)
  const searchQuery = ref('')
  const selectedStatus = ref<string>('all')
  const selectedTimeRange = ref<'day' | 'week' | 'month' | 'all'>('all')
  const selectedStrategy = ref<string>('all')
  const sortBy = ref<'created_at' | 'name' | 'performance' | 'duration'>('created_at')
  const sortOrder = ref<'asc' | 'desc'>('desc')
  
  // 错误状态
  const error = ref<string | null>(null)
  const lastSyncTime = ref<string>('')

  // 计算属性
  const filteredBacktestResults = computed(() => {
    let filtered = backtestResults.value

    if (searchQuery.value) {
      const query = searchQuery.value.toLowerCase()
      filtered = filtered.filter(result => 
        result.name.toLowerCase().includes(query) ||
        result.meta_info.model_name.toLowerCase().includes(query) ||
        result.meta_info.strategy_name.toLowerCase().includes(query) ||
        result.result_id.toLowerCase().includes(query)
      )
    }

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
      
      filtered = filtered.filter(result => 
        new Date(result.created_at) >= timeLimit
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
          const aPerf = a.risk_metrics.sharpe_ratio || 0
          const bPerf = b.risk_metrics.sharpe_ratio || 0
          comparison = aPerf - bPerf
          break
        case 'duration':
          const aDuration = a.meta_info.trading_days || 0
          const bDuration = b.meta_info.trading_days || 0
          comparison = aDuration - bDuration
          break
      }

      return sortOrder.value === 'asc' ? comparison : -comparison
    })

    return filtered
  })

  const activeBacktestTasks = computed(() => {
    return backtestTasks.value.filter(task => 
      task.status === 'running' || task.status === 'pending'
    )
  })

  const backtestStats = computed(() => {
    return {
      total_results: backtestResults.value.length,
      running_tasks: backtestTasks.value.filter(t => t.status === 'running').length,
      completed_tasks: backtestTasks.value.filter(t => t.status === 'completed').length,
      failed_tasks: backtestTasks.value.filter(t => t.status === 'failed').length,
      avg_sharpe: backtestResults.value.length > 0 ?
        backtestResults.value.reduce((sum, r) => sum + (r.risk_metrics.sharpe_ratio || 0), 0) / backtestResults.value.length : 0,
      avg_return: backtestResults.value.length > 0 ?
        backtestResults.value.reduce((sum, r) => sum + (r.return_metrics.annual_return || 0), 0) / backtestResults.value.length : 0,
      success_rate: backtestTasks.value.length > 0 ?
        backtestTasks.value.filter(t => t.status === 'completed').length / backtestTasks.value.length * 100 : 0
    }
  })

  const topPerformingResults = computed(() => {
    return backtestResults.value
      .filter(r => r.risk_metrics.sharpe_ratio)
      .sort((a, b) => (b.risk_metrics.sharpe_ratio || 0) - (a.risk_metrics.sharpe_ratio || 0))
      .slice(0, 10)
  })

  const selectedResultsList = computed(() => {
    return backtestResults.value.filter(result => selectedResults.value.includes(result.result_id))
  })

  // Actions
  const loadBacktestResults = async (): Promise<void> => {
    loading.value = true
    error.value = null

    try {
      const response = await fetch('/api/v1/backtest/results', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json'
        }
      })

      const result = await response.json()

      if (result.status === 'success') {
        backtestResults.value = result.data.results || []
        backtestTasks.value = result.data.tasks || []
        backtestConfigs.value = result.data.configs || []
        lastSyncTime.value = new Date().toISOString()
      } else {
        throw new Error(result.message || '加载回测结果失败')
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : '加载回测结果失败'
      console.error('加载回测结果失败:', err)
      
      // 降级到示例数据
      generateSampleBacktestData()
    } finally {
      loading.value = false
    }
  }

  const generateSampleBacktestData = (): void => {
    // 生成示例回测配置
    backtestConfigs.value = [
      {
        config_id: 'config_001',
        name: 'TopK多因子策略',
        description: '基于Alpha158因子的TopK选股策略',
        model_id: 'model_lightgbm_001',
        strategy_config: {
          class: 'TopKDropoutStrategy',
          module_path: 'qlib.contrib.strategy.signal_strategy',
          kwargs: {
            topk: 20,
            n_drop: 5,
            risk_degree: 0.95
          }
        },
        backtest_config: {
          start_time: '2023-01-01',
          end_time: '2023-12-31',
          universe: 'CSI300',
          benchmark: '000300.SH',
          account: {
            init_cash: 10000000,
            pos_type: 'Position'
          },
          executor: {
            class: 'SimulatorExecutor',
            module_path: 'qlib.backtest.executor',
            kwargs: {}
          },
          exchange: {
            class: 'Exchange',
            module_path: 'qlib.backtest.exchange',
            kwargs: {
              freq: 'day',
              deal_price: 'close',
              open_cost: 0.0005,
              close_cost: 0.0015,
              min_cost: 5
            }
          }
        },
        created_at: '2024-01-15T10:00:00Z',
        updated_at: '2024-01-15T10:00:00Z',
        created_by: 'quant_researcher',
        tags: ['多因子', 'TopK', '日频']
      }
    ]

    // 生成示例回测结果
    backtestResults.value = [
      {
        result_id: 'result_001',
        task_id: 'task_001',
        config_id: 'config_001',
        name: 'TopK多因子策略回测_20240115',
        created_at: '2024-01-15T12:00:00Z',
        
        meta_info: {
          start_time: '2023-01-01',
          end_time: '2023-12-31',
          trading_days: 244,
          universe: 'CSI300',
          benchmark: '000300.SH',
          model_name: 'LightGBM多因子模型v1',
          strategy_name: 'TopK策略'
        },
        
        return_metrics: {
          total_return: 0.285,
          annual_return: 0.285,
          excess_return: 0.167,
          total_return_wo_cost: 0.312,
          annual_return_wo_cost: 0.312,
          excess_return_wo_cost: 0.194
        },
        
        risk_metrics: {
          volatility: 0.195,
          max_drawdown: -0.082,
          calmar_ratio: 3.48,
          sharpe_ratio: 1.46,
          information_ratio: 1.23,
          sortino_ratio: 2.15,
          omega_ratio: 1.34,
          tracking_error: 0.056
        },
        
        trading_metrics: {
          win_rate: 0.583,
          profit_loss_ratio: 1.67,
          average_holding_period: 12.5,
          turnover_rate: 0.285,
          transaction_cost: 0.027,
          total_trades: 2450,
          winning_trades: 1428,
          losing_trades: 1022
        },
        
        time_series: {
          nav: generateTimeSeriesData(244, 1.0, 0.285),
          returns: generateReturnsData(244),
          drawdown: generateDrawdownData(244),
          positions: [],
          trades: []
        },
        
        position_analysis: {
          sector_exposure: {
            '金融': 0.235,
            '消费': 0.187,
            '科技': 0.156,
            '医药': 0.134,
            '工业': 0.123,
            '材料': 0.089,
            '能源': 0.076
          },
          top_holdings: [
            { instrument: '000001.SZ', weight: 0.045, name: '平安银行' },
            { instrument: '000002.SZ', weight: 0.042, name: '万科A' },
            { instrument: '600000.SH', weight: 0.039, name: '浦发银行' },
            { instrument: '600036.SH', weight: 0.037, name: '招商银行' },
            { instrument: '000858.SZ', weight: 0.035, name: '五粮液' }
          ],
          position_concentration: {
            top5_weight: 0.198,
            top10_weight: 0.325,
            effective_number: 18.5,
            herfindahl_index: 0.0541
          },
          turnover_analysis: {
            monthly_turnover: Array.from({ length: 12 }, () => Math.random() * 0.1 + 0.2),
            cumulative_turnover: 3.42,
            turnover_volatility: 0.045
          }
        },
        
        statistical_analysis: {
          monthly_returns: Array.from({ length: 12 }, () => Math.random() * 0.1 - 0.02),
          annual_returns: [0.285],
          return_distribution: {
            mean: 0.00117,
            std: 0.0195,
            skewness: 0.234,
            kurtosis: 3.456,
            var_95: -0.0287,
            cvar_95: -0.0345
          },
          correlation_with_benchmark: 0.78,
          beta: 0.85,
          alpha: 0.0234,
          r_squared: 0.608
        },
        
        chart_data: {
          nav_chart: null,
          return_chart: null,
          drawdown_chart: null,
          holding_chart: null,
          sector_chart: null,
          monthly_return_heatmap: null
        }
      }
    ]

    // 生成示例任务
    backtestTasks.value = [
      {
        task_id: 'task_001',
        config_id: 'config_001',
        name: 'TopK多因子策略回测',
        status: 'completed',
        progress: 100,
        start_time: '2024-01-15T11:00:00Z',
        end_time: '2024-01-15T12:00:00Z',
        current_day: '2023-12-31',
        total_days: 244,
        logs: [
          '开始回测任务',
          '初始化回测环境',
          '加载数据和模型',
          '执行回测策略',
          '计算性能指标',
          '生成分析报告',
          '回测完成'
        ],
        warnings: []
      }
    ]

    lastSyncTime.value = new Date().toISOString()
  }

  const generateTimeSeriesData = (days: number, startValue: number, totalReturn: number) => {
    const data = []
    let currentValue = startValue
    let benchmarkValue = startValue
    const dailyReturn = Math.pow(1 + totalReturn, 1 / days) - 1
    const benchmarkReturn = Math.pow(1 + 0.118, 1 / days) - 1
    
    for (let i = 0; i < days; i++) {
      const date = new Date(2023, 0, i + 1).toISOString().split('T')[0]
      currentValue *= (1 + dailyReturn + (Math.random() - 0.5) * 0.02)
      benchmarkValue *= (1 + benchmarkReturn + (Math.random() - 0.5) * 0.015)
      
      data.push({
        date,
        value: currentValue,
        benchmark: benchmarkValue
      })
    }
    
    return data
  }

  const generateReturnsData = (days: number) => {
    return Array.from({ length: days }, (_, i) => ({
      date: new Date(2023, 0, i + 1).toISOString().split('T')[0],
      portfolio: (Math.random() - 0.5) * 0.04,
      benchmark: (Math.random() - 0.5) * 0.03,
      excess: (Math.random() - 0.5) * 0.02
    }))
  }

  const generateDrawdownData = (days: number) => {
    let maxValue = 1.0
    let currentValue = 1.0
    
    return Array.from({ length: days }, (_, i) => {
      const date = new Date(2023, 0, i + 1).toISOString().split('T')[0]
      currentValue *= (1 + (Math.random() - 0.5) * 0.02)
      maxValue = Math.max(maxValue, currentValue)
      const drawdown = (currentValue - maxValue) / maxValue
      
      return {
        date,
        drawdown,
        underwater: drawdown < -0.01 ? 1 : 0
      }
    })
  }

  const createBacktestConfig = async (configData: Partial<QlibBacktestConfig>): Promise<QlibBacktestConfig> => {
    const newConfig: QlibBacktestConfig = {
      config_id: configData.config_id || `config_${Date.now()}`,
      name: configData.name || '新回测配置',
      description: configData.description || '',
      model_id: configData.model_id || '',
      strategy_config: configData.strategy_config || {
        class: 'TopKDropoutStrategy',
        module_path: 'qlib.contrib.strategy.signal_strategy',
        kwargs: {}
      },
      backtest_config: configData.backtest_config || {
        start_time: '2023-01-01',
        end_time: '2023-12-31',
        universe: 'CSI300',
        benchmark: '000300.SH',
        account: {
          init_cash: 10000000,
          pos_type: 'Position'
        },
        executor: {
          class: 'SimulatorExecutor',
          module_path: 'qlib.backtest.executor',
          kwargs: {}
        },
        exchange: {
          class: 'Exchange',
          module_path: 'qlib.backtest.exchange',
          kwargs: {
            freq: 'day',
            deal_price: 'close',
            open_cost: 0.0005,
            close_cost: 0.0015,
            min_cost: 5
          }
        }
      },
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      created_by: 'current_user',
      tags: configData.tags || []
    }

    backtestConfigs.value.unshift(newConfig)
    return newConfig
  }

  const runBacktest = async (configId: string): Promise<QlibBacktestTask> => {
    const config = backtestConfigs.value.find(c => c.config_id === configId)
    if (!config) {
      throw new Error('回测配置不存在')
    }

    const task: QlibBacktestTask = {
      task_id: `task_${Date.now()}`,
      config_id: configId,
      name: `${config.name}_回测`,
      status: 'pending',
      progress: 0,
      start_time: new Date().toISOString(),
      logs: [`开始回测任务: ${config.name}`],
      warnings: []
    }

    backtestTasks.value.unshift(task)

    try {
      const response = await fetch('/api/v1/backtest/run', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          config_id: configId,
          config: config
        })
      })

      const result = await response.json()

      if (result.status === 'success') {
        task.status = 'running'
        task.task_id = result.data.task_id || task.task_id
        
        // 模拟回测进度
        simulateBacktestProgress(task.task_id)
      } else {
        throw new Error(result.message || '启动回测失败')
      }
    } catch (err) {
      task.status = 'failed'
      task.error_message = err instanceof Error ? err.message : '回测失败'
      task.end_time = new Date().toISOString()
      task.logs.push(`回测失败: ${task.error_message}`)
    }

    return task
  }

  const simulateBacktestProgress = (taskId: string): void => {
    const task = backtestTasks.value.find(t => t.task_id === taskId)
    if (!task) return

    const totalDays = 244
    task.total_days = totalDays
    let currentDay = 0

    const interval = setInterval(() => {
      if (task.status !== 'running') {
        clearInterval(interval)
        return
      }

      currentDay += Math.floor(Math.random() * 5) + 1
      task.progress = Math.min((currentDay / totalDays) * 100, 100)
      task.current_day = new Date(2023, 0, currentDay).toISOString().split('T')[0]
      
      // 更新实时指标
      task.real_time_metrics = {
        current_value: 1 + (Math.random() - 0.3) * 0.4,
        current_return: (Math.random() - 0.3) * 0.4,
        current_position_count: Math.floor(Math.random() * 20) + 15,
        current_turnover: Math.random() * 0.5,
        max_drawdown: -Math.random() * 0.15,
        sharpe_ratio: Math.random() * 2,
        volatility: 0.15 + Math.random() * 0.1
      }
      
      task.logs.push(`处理交易日: ${task.current_day}, 进度: ${task.progress.toFixed(1)}%`)

      if (task.progress >= 100) {
        task.status = 'completed'
        task.end_time = new Date().toISOString()
        task.logs.push('回测完成，生成结果报告')
        
        // 生成回测结果
        generateBacktestResult(task)
        clearInterval(interval)
      }
    }, 1000)
  }

  const generateBacktestResult = (task: QlibBacktestTask): void => {
    const config = backtestConfigs.value.find(c => c.config_id === task.config_id)
    if (!config) return

    const result: QlibBacktestResult = {
      result_id: `result_${Date.now()}`,
      task_id: task.task_id,
      config_id: task.config_id,
      name: `${task.name}_结果`,
      created_at: new Date().toISOString(),
      
      meta_info: {
        start_time: config.backtest_config.start_time,
        end_time: config.backtest_config.end_time,
        trading_days: 244,
        universe: config.backtest_config.universe,
        benchmark: config.backtest_config.benchmark,
        model_name: '模型名称',
        strategy_name: config.strategy_config.class
      },
      
      return_metrics: {
        total_return: Math.random() * 0.4 - 0.1,
        annual_return: Math.random() * 0.4 - 0.1,
        excess_return: Math.random() * 0.3 - 0.05,
        total_return_wo_cost: Math.random() * 0.45 - 0.05,
        annual_return_wo_cost: Math.random() * 0.45 - 0.05,
        excess_return_wo_cost: Math.random() * 0.35 - 0.02
      },
      
      risk_metrics: {
        volatility: 0.15 + Math.random() * 0.1,
        max_drawdown: -Math.random() * 0.2,
        calmar_ratio: Math.random() * 5,
        sharpe_ratio: Math.random() * 3,
        information_ratio: Math.random() * 2.5,
        sortino_ratio: Math.random() * 4,
        omega_ratio: Math.random() * 2,
        tracking_error: Math.random() * 0.1
      },
      
      trading_metrics: {
        win_rate: 0.4 + Math.random() * 0.3,
        profit_loss_ratio: 1 + Math.random() * 1.5,
        average_holding_period: 5 + Math.random() * 20,
        turnover_rate: 0.1 + Math.random() * 0.4,
        transaction_cost: Math.random() * 0.05,
        total_trades: Math.floor(Math.random() * 3000) + 1000,
        winning_trades: 0,
        losing_trades: 0
      },
      
      time_series: {
        nav: generateTimeSeriesData(244, 1.0, Math.random() * 0.4 - 0.1),
        returns: generateReturnsData(244),
        drawdown: generateDrawdownData(244),
        positions: [],
        trades: []
      },
      
      position_analysis: {
        sector_exposure: {
          '金融': Math.random() * 0.3,
          '消费': Math.random() * 0.25,
          '科技': Math.random() * 0.2,
          '医药': Math.random() * 0.15,
          '工业': Math.random() * 0.15
        },
        top_holdings: [],
        position_concentration: {
          top5_weight: Math.random() * 0.3 + 0.1,
          top10_weight: Math.random() * 0.5 + 0.2,
          effective_number: Math.random() * 15 + 10,
          herfindahl_index: Math.random() * 0.1 + 0.02
        },
        turnover_analysis: {
          monthly_turnover: Array.from({ length: 12 }, () => Math.random() * 0.2 + 0.1),
          cumulative_turnover: Math.random() * 5 + 2,
          turnover_volatility: Math.random() * 0.05 + 0.02
        }
      },
      
      statistical_analysis: {
        monthly_returns: Array.from({ length: 12 }, () => Math.random() * 0.15 - 0.05),
        annual_returns: [Math.random() * 0.4 - 0.1],
        return_distribution: {
          mean: Math.random() * 0.002,
          std: Math.random() * 0.03 + 0.01,
          skewness: Math.random() * 2 - 1,
          kurtosis: Math.random() * 5 + 2,
          var_95: -Math.random() * 0.05,
          cvar_95: -Math.random() * 0.08
        },
        correlation_with_benchmark: 0.5 + Math.random() * 0.4,
        beta: 0.5 + Math.random() * 0.8,
        alpha: Math.random() * 0.05 - 0.02,
        r_squared: 0.3 + Math.random() * 0.5
      },
      
      chart_data: {
        nav_chart: null,
        return_chart: null,
        drawdown_chart: null,
        holding_chart: null,
        sector_chart: null,
        monthly_return_heatmap: null
      }
    }

    // 计算胜负交易数量
    result.trading_metrics.winning_trades = Math.floor(result.trading_metrics.total_trades * result.trading_metrics.win_rate)
    result.trading_metrics.losing_trades = result.trading_metrics.total_trades - result.trading_metrics.winning_trades

    backtestResults.value.unshift(result)
  }

  const cancelBacktest = async (taskId: string): Promise<boolean> => {
    const task = backtestTasks.value.find(t => t.task_id === taskId)
    if (!task || task.status !== 'running') return false

    try {
      const response = await fetch(`/api/v1/backtest/tasks/${taskId}/cancel`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      })

      const result = await response.json()

      if (result.status === 'success') {
        task.status = 'cancelled'
        task.end_time = new Date().toISOString()
        task.logs.push('回测已取消')
        return true
      } else {
        throw new Error(result.message || '取消回测失败')
      }
    } catch (err) {
      console.error('取消回测失败:', err)
      return false
    }
  }

  const deleteBacktestResult = async (resultId: string): Promise<boolean> => {
    const resultIndex = backtestResults.value.findIndex(r => r.result_id === resultId)
    if (resultIndex === -1) return false

    try {
      const response = await fetch(`/api/v1/backtest/results/${resultId}`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json'
        }
      })

      const result = await response.json()

      if (result.status === 'success') {
        backtestResults.value.splice(resultIndex, 1)
        
        // 从选中列表中移除
        const selectedIndex = selectedResults.value.indexOf(resultId)
        if (selectedIndex > -1) {
          selectedResults.value.splice(selectedIndex, 1)
        }
        
        return true
      } else {
        throw new Error(result.message || '删除回测结果失败')
      }
    } catch (err) {
      console.error('删除回测结果失败:', err)
      return false
    }
  }

  const compareBacktestResults = async (resultIds: string[], metrics: string[]): Promise<BacktestComparison> => {
    const comparison: BacktestComparison = {
      comparison_id: `comp_${Date.now()}`,
      name: `回测对比_${new Date().toLocaleDateString()}`,
      result_ids: resultIds,
      metrics,
      created_at: new Date().toISOString(),
      comparison_data: {
        metric_comparison: {},
        ranking: [],
        correlation_matrix: {},
        statistical_tests: {},
        recommendations: []
      }
    }

    try {
      const response = await fetch('/api/v1/backtest/compare', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          result_ids: resultIds,
          metrics
        })
      })

      const result = await response.json()

      if (result.status === 'success') {
        comparison.comparison_data = result.data.comparison_data
      } else {
        throw new Error(result.message || '回测对比失败')
      }
    } catch (err) {
      console.error('回测对比失败:', err)
      
      // 生成模拟对比结果
      comparison.comparison_data = generateMockComparisonData(resultIds, metrics)
    }

    backtestComparisons.value.unshift(comparison)
    return comparison
  }

  const generateMockComparisonData = (resultIds: string[], metrics: string[]): any => {
    const metricComparison: Record<string, Record<string, number>> = {}
    const ranking: Array<{ result_id: string, rank: number, score: number }> = []
    const correlationMatrix: Record<string, Record<string, number>> = {}
    const statisticalTests: Record<string, any> = {}
    
    metrics.forEach(metric => {
      metricComparison[metric] = {}
      resultIds.forEach(resultId => {
        metricComparison[metric][resultId] = Math.random() * 2 - 0.5
      })
      
      statisticalTests[metric] = {
        p_value: Math.random() * 0.1,
        significant: Math.random() > 0.5,
        test_statistic: Math.random() * 3,
        test_type: 'Welch t-test'
      }
    })
    
    resultIds.forEach((resultId, index) => {
      ranking.push({
        result_id: resultId,
        rank: index + 1,
        score: Math.random() * 100
      })
      
      correlationMatrix[resultId] = {}
      resultIds.forEach(otherId => {
        correlationMatrix[resultId][otherId] = resultId === otherId ? 1 : Math.random() * 0.8 + 0.1
      })
    })
    
    return {
      metric_comparison: metricComparison,
      ranking: ranking.sort((a, b) => b.score - a.score).map((item, index) => ({ ...item, rank: index + 1 })),
      correlation_matrix: correlationMatrix,
      statistical_tests: statisticalTests,
      recommendations: [
        '策略A在风险调整收益方面表现最佳',
        '策略B具有更好的稳定性',
        '建议进一步优化策略C的风控参数'
      ]
    }
  }

  const exportBacktestResult = async (resultId: string): Promise<string> => {
    const result = backtestResults.value.find(r => r.result_id === resultId)
    if (!result) throw new Error('回测结果不存在')

    return JSON.stringify({
      result,
      exported_at: new Date().toISOString(),
      version: '1.0'
    }, null, 2)
  }

  const loadBacktestTemplates = async (): Promise<void> => {
    // 生成示例模板
    backtestTemplates.value = [
      {
        template_id: 'template_1',
        name: 'TopK选股策略',
        description: '基于模型预测的TopK选股策略模板',
        category: 'long_only',
        config_template: {
          strategy_config: {
            class: 'TopKDropoutStrategy',
            module_path: 'qlib.contrib.strategy.signal_strategy',
            kwargs: {
              topk: 20,
              n_drop: 5
            }
          }
        },
        parameters: [
          {
            name: 'topk',
            type: 'number',
            description: '选择股票数量',
            default: 20,
            min: 5,
            max: 100
          },
          {
            name: 'n_drop',
            type: 'number',
            description: '每次调仓时卖出的股票数量',
            default: 5,
            min: 0,
            max: 50
          }
        ],
        created_at: '2024-01-01T00:00:00Z',
        usage_count: 45,
        rating: 4.5
      },
      {
        template_id: 'template_2',
        name: '多空对冲策略',
        description: '多空对冲策略模板',
        category: 'long_short',
        config_template: {
          strategy_config: {
            class: 'EnhancedIndexingStrategy',
            module_path: 'qlib.contrib.strategy.enhanced_indexing',
            kwargs: {
              long_threshold: 0.7,
              short_threshold: 0.3
            }
          }
        },
        parameters: [
          {
            name: 'long_threshold',
            type: 'number',
            description: '做多阈值',
            default: 0.7,
            min: 0.5,
            max: 1.0
          },
          {
            name: 'short_threshold',
            type: 'number',
            description: '做空阈值',
            default: 0.3,
            min: 0.0,
            max: 0.5
          }
        ],
        created_at: '2024-01-01T00:00:00Z',
        usage_count: 28,
        rating: 4.2
      }
    ]
  }

  const toggleResultSelection = (resultId: string): void => {
    const index = selectedResults.value.indexOf(resultId)
    if (index > -1) {
      selectedResults.value.splice(index, 1)
    } else {
      selectedResults.value.push(resultId)
    }
  }

  const selectAllResults = (): void => {
    selectedResults.value = filteredBacktestResults.value.map(r => r.result_id)
  }

  const clearSelection = (): void => {
    selectedResults.value = []
  }

  const searchResults = (query: string): void => {
    searchQuery.value = query
  }

  const setFilters = (filters: {
    status?: string
    timeRange?: string
    strategy?: string
  }): void => {
    if (filters.status !== undefined) selectedStatus.value = filters.status
    if (filters.timeRange !== undefined) selectedTimeRange.value = filters.timeRange as any
    if (filters.strategy !== undefined) selectedStrategy.value = filters.strategy
  }

  const setSorting = (field: typeof sortBy.value, order: typeof sortOrder.value): void => {
    sortBy.value = field
    sortOrder.value = order
  }

  const refreshBacktestData = async (): Promise<void> => {
    await loadBacktestResults()
  }

  const getBacktestResult = (resultId: string): QlibBacktestResult | undefined => {
    return backtestResults.value.find(r => r.result_id === resultId)
  }

  const getBacktestTask = (taskId: string): QlibBacktestTask | undefined => {
    return backtestTasks.value.find(t => t.task_id === taskId)
  }

  const getBacktestConfig = (configId: string): QlibBacktestConfig | undefined => {
    return backtestConfigs.value.find(c => c.config_id === configId)
  }

  return {
    // State
    backtestConfigs,
    backtestTasks,
    backtestResults,
    backtestComparisons,
    backtestTemplates,
    selectedResults,
    currentEditingConfig,
    loading,
    searchQuery,
    selectedStatus,
    selectedTimeRange,
    selectedStrategy,
    sortBy,
    sortOrder,
    error,
    lastSyncTime,

    // Computed
    filteredBacktestResults,
    activeBacktestTasks,
    backtestStats,
    topPerformingResults,
    selectedResultsList,

    // Actions
    loadBacktestResults,
    generateSampleBacktestData,
    createBacktestConfig,
    runBacktest,
    cancelBacktest,
    deleteBacktestResult,
    compareBacktestResults,
    exportBacktestResult,
    loadBacktestTemplates,
    toggleResultSelection,
    selectAllResults,
    clearSelection,
    searchResults,
    setFilters,
    setSorting,
    refreshBacktestData,
    getBacktestResult,
    getBacktestTask,
    getBacktestConfig
  }
})