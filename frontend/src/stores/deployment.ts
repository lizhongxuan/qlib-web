import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

interface Deployment {
  id: string
  name: string
  strategyId: string
  modelId: string
  status: 'pending' | 'running' | 'paused' | 'stopped' | 'error' | 'completed'
  environment: 'simulation' | 'paper' | 'live'
  createdAt: Date
  updatedAt: Date
  createdBy: string
  description?: string
  tags: string[]
  
  // 部署配置
  config: {
    initialCapital: number
    broker: string
    rebalanceFreq: 'daily' | 'weekly' | 'monthly'
    positionCount: number
    maxSingleWeight: number
    stopLossThreshold: number
    maxDrawdownLimit: number
    dailyTradingLimit: number
    monitoring: string[]
    notifications: string[]
  }
  
  // 实时状态
  runtime: {
    startTime?: Date
    endTime?: Date
    runningDays: number
    currentNetValue: number
    netValueChange: number
    availableCash: number
    positionValue: number
    totalReturn: number
    currentDrawdown: number
    todayPnL: number
    todayTrades: number
    totalTrades: number
    lastTradeTime?: Date
  }
  
  // 性能指标
  performance?: {
    cumulativeReturn: number
    annualizedReturn: number
    sharpeRatio: number
    maxDrawdown: number
    winRate: number
    volatility: number
    calmarRatio: number
    informationRatio: number
    trackingError: number
    beta: number
    alpha: number
    var95: number
    cvar95: number
  }
  
  // 持仓信息
  positions: Array<{
    symbol: string
    name: string
    quantity: number
    currentPrice: number
    avgCost: number
    marketValue: number
    weight: number
    unrealizedPnL: number
    returnRate: number
    holdingDays: number
  }>
  
  // 交易记录
  trades: Array<{
    id: string
    time: Date
    symbol: string
    name: string
    side: 'buy' | 'sell'
    quantity: number
    price: number
    amount: number
    commission: number
    status: 'pending' | 'filled' | 'cancelled' | 'rejected'
    reason?: string
  }>
  
  // 风险监控
  riskMetrics: {
    concentration: number
    leverageRatio: number
    exposureByIndustry: Record<string, number>
    exposureBySector: Record<string, number>
    riskLevel: 'low' | 'medium' | 'high' | 'critical'
    alerts: Array<{
      id: string
      level: 'info' | 'warning' | 'error' | 'critical'
      type: string
      message: string
      time: Date
      acknowledged: boolean
    }>
  }
  
  // 系统状态
  systemStatus: {
    strategy: 'running' | 'paused' | 'error'
    dataConnection: 'connected' | 'disconnected' | 'error'
    tradingInterface: 'active' | 'inactive' | 'error'
    lastUpdate: Date
    networkLatency: number
    cpuUsage: number
    memoryUsage: number
    errorCount: number
  }
}

interface DeploymentLog {
  id: string
  deploymentId: string
  timestamp: Date
  level: 'debug' | 'info' | 'warning' | 'error'
  category: 'system' | 'trading' | 'risk' | 'performance'
  message: string
  details?: Record<string, any>
}

interface DeploymentTemplate {
  id: string
  name: string
  description: string
  environment: Deployment['environment']
  defaultConfig: Partial<Deployment['config']>
  category: string
  riskLevel: 'conservative' | 'moderate' | 'aggressive'
}

export const useDeploymentStore = defineStore('deployment', () => {
  // 状态
  const deployments = ref<Deployment[]>([])
  const deploymentLogs = ref<DeploymentLog[]>([])
  const deploymentTemplates = ref<DeploymentTemplate[]>([])
  const selectedDeployments = ref<string[]>([])
  const currentDeployment = ref<Deployment | null>(null)
  const isLoading = ref(false)
  const searchQuery = ref('')
  const filterEnvironment = ref<string>('all')
  const filterStatus = ref<string>('all')
  const sortBy = ref<'name' | 'createdAt' | 'performance' | 'return'>('createdAt')
  const sortOrder = ref<'asc' | 'desc'>('desc')
  const autoRefresh = ref(true)
  const refreshInterval = ref<number>()

  // 计算属性
  const filteredDeployments = computed(() => {
    let result = deployments.value

    // 搜索过滤
    if (searchQuery.value) {
      const query = searchQuery.value.toLowerCase()
      result = result.filter(deployment => 
        deployment.name.toLowerCase().includes(query) ||
        deployment.description?.toLowerCase().includes(query) ||
        deployment.tags.some(tag => tag.toLowerCase().includes(query))
      )
    }

    // 环境过滤
    if (filterEnvironment.value !== 'all') {
      result = result.filter(deployment => deployment.environment === filterEnvironment.value)
    }

    // 状态过滤
    if (filterStatus.value !== 'all') {
      result = result.filter(deployment => deployment.status === filterStatus.value)
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
          const aPerf = a.performance?.sharpeRatio || 0
          const bPerf = b.performance?.sharpeRatio || 0
          comparison = aPerf - bPerf
          break
        case 'return':
          const aReturn = a.runtime.totalReturn || 0
          const bReturn = b.runtime.totalReturn || 0
          comparison = aReturn - bReturn
          break
      }

      return sortOrder.value === 'asc' ? comparison : -comparison
    })

    return result
  })

  const activeDeployments = computed(() => {
    return deployments.value.filter(d => 
      d.status === 'running' || d.status === 'paused'
    )
  })

  const runningDeployments = computed(() => {
    return deployments.value.filter(d => d.status === 'running')
  })

  const pausedDeployments = computed(() => {
    return deployments.value.filter(d => d.status === 'paused')
  })

  const stoppedDeployments = computed(() => {
    return deployments.value.filter(d => d.status === 'stopped')
  })

  const errorDeployments = computed(() => {
    return deployments.value.filter(d => d.status === 'error')
  })

  const deploymentsByEnvironment = computed(() => {
    const grouped: Record<string, Deployment[]> = {}
    deployments.value.forEach(deployment => {
      if (!grouped[deployment.environment]) {
        grouped[deployment.environment] = []
      }
      grouped[deployment.environment].push(deployment)
    })
    return grouped
  })

  const deploymentStats = computed(() => {
    return {
      total: deployments.value.length,
      running: runningDeployments.value.length,
      paused: pausedDeployments.value.length,
      stopped: stoppedDeployments.value.length,
      error: errorDeployments.value.length,
      simulation: deployments.value.filter(d => d.environment === 'simulation').length,
      paper: deployments.value.filter(d => d.environment === 'paper').length,
      live: deployments.value.filter(d => d.environment === 'live').length
    }
  })

  const totalPortfolioValue = computed(() => {
    return activeDeployments.value.reduce((total, deployment) => {
      return total + deployment.runtime.availableCash + deployment.runtime.positionValue
    }, 0)
  })

  const totalPnL = computed(() => {
    return activeDeployments.value.reduce((total, deployment) => {
      return total + deployment.runtime.todayPnL
    }, 0)
  })

  const criticalAlerts = computed(() => {
    const alerts: any[] = []
    activeDeployments.value.forEach(deployment => {
      deployment.riskMetrics.alerts
        .filter(alert => alert.level === 'critical' && !alert.acknowledged)
        .forEach(alert => alerts.push({ ...alert, deploymentId: deployment.id, deploymentName: deployment.name }))
    })
    return alerts
  })

  const recentLogs = computed(() => {
    return deploymentLogs.value
      .sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime())
      .slice(0, 100)
  })

  // 动作
  const loadDeployments = async () => {
    isLoading.value = true
    try {
      // 模拟API调用
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      // 模拟数据
      deployments.value = [
        {
          id: 'deploy_1',
          name: 'LightGBM策略_生产环境',
          strategyId: 'strategy_1',
          modelId: 'model_1',
          status: 'running',
          environment: 'live',
          createdAt: new Date('2024-01-01'),
          updatedAt: new Date(),
          createdBy: 'user1',
          description: '基于LightGBM模型的多因子量化策略',
          tags: ['多因子', 'LightGBM', '生产'],
          config: {
            initialCapital: 1000000,
            broker: 'huatai',
            rebalanceFreq: 'monthly',
            positionCount: 30,
            maxSingleWeight: 0.05,
            stopLossThreshold: 0.08,
            maxDrawdownLimit: 0.15,
            dailyTradingLimit: 100000,
            monitoring: ['realtime', 'alerts'],
            notifications: ['email', 'app']
          },
          runtime: {
            startTime: new Date('2024-01-01T09:30:00'),
            runningDays: 45,
            currentNetValue: 1.0832,
            netValueChange: 0.012,
            availableCash: 285000,
            positionValue: 715000,
            totalReturn: 0.0832,
            currentDrawdown: -0.025,
            todayPnL: 1250.0,
            todayTrades: 8,
            totalTrades: 156,
            lastTradeTime: new Date('2024-01-15T14:35:22')
          },
          performance: {
            cumulativeReturn: 0.0832,
            annualizedReturn: 0.285,
            sharpeRatio: 1.45,
            maxDrawdown: -0.082,
            winRate: 0.609,
            volatility: 0.18,
            calmarRatio: 3.48,
            informationRatio: 1.25,
            trackingError: 0.08,
            beta: 0.95,
            alpha: 0.162,
            var95: -0.025,
            cvar95: -0.032
          },
          positions: [
            {
              symbol: '600519',
              name: '贵州茅台',
              quantity: 100,
              currentPrice: 1680.50,
              avgCost: 1620.30,
              marketValue: 168050,
              weight: 0.168,
              unrealizedPnL: 6020,
              returnRate: 0.037,
              holdingDays: 15
            },
            {
              symbol: '000858',
              name: '五粮液',
              quantity: 200,
              currentPrice: 156.80,
              avgCost: 148.20,
              marketValue: 31360,
              weight: 0.031,
              unrealizedPnL: 1720,
              returnRate: 0.058,
              holdingDays: 8
            }
          ],
          trades: [
            {
              id: 'trade_1',
              time: new Date('2024-01-15T14:35:22'),
              symbol: '000001',
              name: '平安银行',
              side: 'buy',
              quantity: 1000,
              price: 12.45,
              amount: 12450,
              commission: 6.23,
              status: 'filled'
            },
            {
              id: 'trade_2',
              time: new Date('2024-01-15T14:30:15'),
              symbol: '600036',
              name: '招商银行',
              side: 'sell',
              quantity: 500,
              price: 45.80,
              amount: 22900,
              commission: 11.45,
              status: 'filled'
            }
          ],
          riskMetrics: {
            concentration: 0.45,
            leverageRatio: 1.0,
            exposureByIndustry: {
              '食品饮料': 0.35,
              '银行': 0.25,
              '医药生物': 0.20,
              '电子': 0.15,
              '其他': 0.05
            },
            exposureBySector: {
              '消费': 0.40,
              '金融': 0.30,
              '科技': 0.20,
              '医疗': 0.10
            },
            riskLevel: 'medium',
            alerts: [
              {
                id: 'alert_1',
                level: 'warning',
                type: 'concentration',
                message: '持仓集中度偏高，前五大持仓占比达到45%',
                time: new Date(),
                acknowledged: false
              }
            ]
          },
          systemStatus: {
            strategy: 'running',
            dataConnection: 'connected',
            tradingInterface: 'active',
            lastUpdate: new Date(),
            networkLatency: 45,
            cpuUsage: 28,
            memoryUsage: 65,
            errorCount: 0
          }
        },
        {
          id: 'deploy_2',
          name: 'LSTM策略_模拟测试',
          strategyId: 'strategy_2',
          modelId: 'model_2',
          status: 'paused',
          environment: 'simulation',
          createdAt: new Date('2024-01-10'),
          updatedAt: new Date(),
          createdBy: 'user2',
          description: '基于LSTM模型的时序预测策略',
          tags: ['LSTM', '时序预测', '模拟'],
          config: {
            initialCapital: 500000,
            broker: 'mock',
            rebalanceFreq: 'weekly',
            positionCount: 20,
            maxSingleWeight: 0.08,
            stopLossThreshold: 0.10,
            maxDrawdownLimit: 0.20,
            dailyTradingLimit: 50000,
            monitoring: ['realtime'],
            notifications: ['email']
          },
          runtime: {
            startTime: new Date('2024-01-10T09:30:00'),
            runningDays: 5,
            currentNetValue: 1.0125,
            netValueChange: -0.008,
            availableCash: 175000,
            positionValue: 325000,
            totalReturn: 0.0125,
            currentDrawdown: -0.015,
            todayPnL: -480.0,
            todayTrades: 3,
            totalTrades: 24,
            lastTradeTime: new Date('2024-01-14T11:20:15')
          },
          positions: [
            {
              symbol: '000002',
              name: '万科A',
              quantity: 2000,
              currentPrice: 18.50,
              avgCost: 17.80,
              marketValue: 37000,
              weight: 0.074,
              unrealizedPnL: 1400,
              returnRate: 0.039,
              holdingDays: 3
            }
          ],
          trades: [
            {
              id: 'trade_3',
              time: new Date('2024-01-14T11:20:15'),
              symbol: '000002',
              name: '万科A',
              side: 'buy',
              quantity: 500,
              price: 18.50,
              amount: 9250,
              commission: 4.63,
              status: 'filled'
            }
          ],
          riskMetrics: {
            concentration: 0.30,
            leverageRatio: 1.0,
            exposureByIndustry: {
              '房地产': 0.50,
              '科技': 0.30,
              '其他': 0.20
            },
            exposureBySector: {
              '地产': 0.50,
              '科技': 0.30,
              '其他': 0.20
            },
            riskLevel: 'low',
            alerts: []
          },
          systemStatus: {
            strategy: 'paused',
            dataConnection: 'connected',
            tradingInterface: 'active',
            lastUpdate: new Date(),
            networkLatency: 25,
            cpuUsage: 15,
            memoryUsage: 45,
            errorCount: 0
          }
        }
      ]

      // 加载部署日志
      deploymentLogs.value = [
        {
          id: 'log_1',
          deploymentId: 'deploy_1',
          timestamp: new Date(),
          level: 'info',
          category: 'trading',
          message: '成功买入平安银行1000股',
          details: { symbol: '000001', quantity: 1000, price: 12.45 }
        },
        {
          id: 'log_2',
          deploymentId: 'deploy_1',
          timestamp: new Date(Date.now() - 300000),
          level: 'warning',
          category: 'risk',
          message: '持仓集中度超过警戒线',
          details: { concentration: 0.45, threshold: 0.40 }
        }
      ]

    } catch (error) {
      console.error('加载部署失败:', error)
    } finally {
      isLoading.value = false
    }
  }

  const createDeployment = async (deploymentData: Partial<Deployment>): Promise<Deployment> => {
    const newDeployment: Deployment = {
      id: `deploy_${Date.now()}`,
      name: deploymentData.name || '新部署',
      strategyId: deploymentData.strategyId || '',
      modelId: deploymentData.modelId || '',
      status: 'pending',
      environment: deploymentData.environment || 'simulation',
      createdAt: new Date(),
      updatedAt: new Date(),
      createdBy: 'current_user',
      description: deploymentData.description || '',
      tags: deploymentData.tags || [],
      config: deploymentData.config || {
        initialCapital: 1000000,
        broker: 'mock',
        rebalanceFreq: 'monthly',
        positionCount: 30,
        maxSingleWeight: 0.05,
        stopLossThreshold: 0.08,
        maxDrawdownLimit: 0.15,
        dailyTradingLimit: 100000,
        monitoring: ['realtime'],
        notifications: ['email']
      },
      runtime: {
        runningDays: 0,
        currentNetValue: 1.0,
        netValueChange: 0,
        availableCash: deploymentData.config?.initialCapital || 1000000,
        positionValue: 0,
        totalReturn: 0,
        currentDrawdown: 0,
        todayPnL: 0,
        todayTrades: 0,
        totalTrades: 0
      },
      positions: [],
      trades: [],
      riskMetrics: {
        concentration: 0,
        leverageRatio: 1.0,
        exposureByIndustry: {},
        exposureBySector: {},
        riskLevel: 'low',
        alerts: []
      },
      systemStatus: {
        strategy: 'running',
        dataConnection: 'connected',
        tradingInterface: 'active',
        lastUpdate: new Date(),
        networkLatency: 0,
        cpuUsage: 0,
        memoryUsage: 0,
        errorCount: 0
      }
    }

    deployments.value.unshift(newDeployment)
    addLog(newDeployment.id, 'info', 'system', '部署创建成功')
    return newDeployment
  }

  const updateDeployment = async (deploymentId: string, updates: Partial<Deployment>): Promise<Deployment | null> => {
    const deploymentIndex = deployments.value.findIndex(d => d.id === deploymentId)
    if (deploymentIndex === -1) return null

    const updatedDeployment = {
      ...deployments.value[deploymentIndex],
      ...updates,
      updatedAt: new Date()
    }

    deployments.value[deploymentIndex] = updatedDeployment
    return updatedDeployment
  }

  const deleteDeployment = async (deploymentId: string): Promise<boolean> => {
    const deploymentIndex = deployments.value.findIndex(d => d.id === deploymentId)
    if (deploymentIndex === -1) return false

    const deployment = deployments.value[deploymentIndex]
    
    // 检查是否可以删除
    if (deployment.status === 'running') {
      throw new Error('正在运行的部署无法删除，请先停止部署')
    }

    deployments.value.splice(deploymentIndex, 1)
    
    // 从选中列表中移除
    const selectedIndex = selectedDeployments.value.indexOf(deploymentId)
    if (selectedIndex > -1) {
      selectedDeployments.value.splice(selectedIndex, 1)
    }

    // 删除相关日志
    deploymentLogs.value = deploymentLogs.value.filter(log => log.deploymentId !== deploymentId)

    return true
  }

  const startDeployment = async (deploymentId: string): Promise<boolean> => {
    const deployment = deployments.value.find(d => d.id === deploymentId)
    if (!deployment || deployment.status === 'running') return false

    await updateDeployment(deploymentId, {
      status: 'running',
      runtime: {
        ...deployment.runtime,
        startTime: new Date()
      }
    })

    addLog(deploymentId, 'info', 'system', '部署启动成功')
    return true
  }

  const pauseDeployment = async (deploymentId: string): Promise<boolean> => {
    const deployment = deployments.value.find(d => d.id === deploymentId)
    if (!deployment || deployment.status !== 'running') return false

    await updateDeployment(deploymentId, { status: 'paused' })
    addLog(deploymentId, 'info', 'system', '部署已暂停')
    return true
  }

  const resumeDeployment = async (deploymentId: string): Promise<boolean> => {
    const deployment = deployments.value.find(d => d.id === deploymentId)
    if (!deployment || deployment.status !== 'paused') return false

    await updateDeployment(deploymentId, { status: 'running' })
    addLog(deploymentId, 'info', 'system', '部署已恢复')
    return true
  }

  const stopDeployment = async (deploymentId: string): Promise<boolean> => {
    const deployment = deployments.value.find(d => d.id === deploymentId)
    if (!deployment || (deployment.status !== 'running' && deployment.status !== 'paused')) return false

    await updateDeployment(deploymentId, {
      status: 'stopped',
      runtime: {
        ...deployment.runtime,
        endTime: new Date()
      }
    })

    addLog(deploymentId, 'info', 'system', '部署已停止')
    return true
  }

  const acknowledgeAlert = async (deploymentId: string, alertId: string): Promise<boolean> => {
    const deployment = deployments.value.find(d => d.id === deploymentId)
    if (!deployment) return false

    const alert = deployment.riskMetrics.alerts.find(a => a.id === alertId)
    if (!alert) return false

    alert.acknowledged = true
    await updateDeployment(deploymentId, { riskMetrics: deployment.riskMetrics })
    
    addLog(deploymentId, 'info', 'risk', `告警已确认: ${alert.message}`)
    return true
  }

  const emergencyStop = async (deploymentId: string, reason: string): Promise<boolean> => {
    const deployment = deployments.value.find(d => d.id === deploymentId)
    if (!deployment) return false

    // 立即停止并清空所有持仓
    await updateDeployment(deploymentId, {
      status: 'stopped',
      positions: [],
      runtime: {
        ...deployment.runtime,
        endTime: new Date(),
        positionValue: 0,
        availableCash: deployment.runtime.availableCash + deployment.runtime.positionValue
      }
    })

    addLog(deploymentId, 'error', 'system', `紧急停止: ${reason}`)
    return true
  }

  const refreshDeploymentData = async (deploymentId?: string) => {
    const deploymentsToUpdate = deploymentId 
      ? deployments.value.filter(d => d.id === deploymentId)
      : runningDeployments.value

    for (const deployment of deploymentsToUpdate) {
      // 模拟实时数据更新
      const updatedRuntime = {
        ...deployment.runtime,
        currentNetValue: deployment.runtime.currentNetValue + (Math.random() - 0.5) * 0.01,
        netValueChange: (Math.random() - 0.5) * 0.02,
        todayPnL: deployment.runtime.todayPnL + (Math.random() - 0.5) * 200,
        lastUpdate: new Date()
      }

      const updatedSystemStatus = {
        ...deployment.systemStatus,
        lastUpdate: new Date(),
        networkLatency: Math.floor(Math.random() * 100) + 20,
        cpuUsage: Math.floor(Math.random() * 40) + 20,
        memoryUsage: Math.floor(Math.random() * 30) + 50
      }

      await updateDeployment(deployment.id, {
        runtime: updatedRuntime,
        systemStatus: updatedSystemStatus
      })
    }
  }

  const addLog = (deploymentId: string, level: DeploymentLog['level'], category: DeploymentLog['category'], message: string, details?: Record<string, any>) => {
    const log: DeploymentLog = {
      id: `log_${Date.now()}_${Math.random()}`,
      deploymentId,
      timestamp: new Date(),
      level,
      category,
      message,
      details
    }

    deploymentLogs.value.unshift(log)
    
    // 保留最新1000条日志
    if (deploymentLogs.value.length > 1000) {
      deploymentLogs.value = deploymentLogs.value.slice(0, 1000)
    }
  }

  const getDeploymentLogs = (deploymentId: string, limit?: number) => {
    const logs = deploymentLogs.value
      .filter(log => log.deploymentId === deploymentId)
      .sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime())
    
    return limit ? logs.slice(0, limit) : logs
  }

  const exportDeploymentData = (deploymentId: string) => {
    const deployment = deployments.value.find(d => d.id === deploymentId)
    if (!deployment) return null

    const logs = getDeploymentLogs(deploymentId)

    return JSON.stringify({
      deployment,
      logs,
      exportedAt: new Date().toISOString()
    }, null, 2)
  }

  const startAutoRefresh = () => {
    if (refreshInterval.value) {
      clearInterval(refreshInterval.value)
    }

    if (autoRefresh.value) {
      refreshInterval.value = window.setInterval(() => {
        refreshDeploymentData()
      }, 5000) // 每5秒刷新一次
    }
  }

  const stopAutoRefresh = () => {
    if (refreshInterval.value) {
      clearInterval(refreshInterval.value)
      refreshInterval.value = undefined
    }
  }

  const toggleAutoRefresh = () => {
    autoRefresh.value = !autoRefresh.value
    if (autoRefresh.value) {
      startAutoRefresh()
    } else {
      stopAutoRefresh()
    }
  }

  const searchDeployments = (query: string) => {
    searchQuery.value = query
  }

  const setFilters = (filters: {
    environment?: string
    status?: string
  }) => {
    if (filters.environment !== undefined) filterEnvironment.value = filters.environment
    if (filters.status !== undefined) filterStatus.value = filters.status
  }

  const setSorting = (field: typeof sortBy.value, order: typeof sortOrder.value) => {
    sortBy.value = field
    sortOrder.value = order
  }

  const resetFilters = () => {
    searchQuery.value = ''
    filterEnvironment.value = 'all'
    filterStatus.value = 'all'
    sortBy.value = 'createdAt'
    sortOrder.value = 'desc'
  }

  const toggleDeploymentSelection = (deploymentId: string) => {
    const index = selectedDeployments.value.indexOf(deploymentId)
    if (index > -1) {
      selectedDeployments.value.splice(index, 1)
    } else {
      selectedDeployments.value.push(deploymentId)
    }
  }

  const selectAllDeployments = () => {
    selectedDeployments.value = filteredDeployments.value.map(d => d.id)
  }

  const clearSelection = () => {
    selectedDeployments.value = []
  }

  return {
    // 状态
    deployments,
    deploymentLogs,
    deploymentTemplates,
    selectedDeployments,
    currentDeployment,
    isLoading,
    searchQuery,
    filterEnvironment,
    filterStatus,
    sortBy,
    sortOrder,
    autoRefresh,

    // 计算属性
    filteredDeployments,
    activeDeployments,
    runningDeployments,
    pausedDeployments,
    stoppedDeployments,
    errorDeployments,
    deploymentsByEnvironment,
    deploymentStats,
    totalPortfolioValue,
    totalPnL,
    criticalAlerts,
    recentLogs,

    // 动作
    loadDeployments,
    createDeployment,
    updateDeployment,
    deleteDeployment,
    startDeployment,
    pauseDeployment,
    resumeDeployment,
    stopDeployment,
    acknowledgeAlert,
    emergencyStop,
    refreshDeploymentData,
    addLog,
    getDeploymentLogs,
    exportDeploymentData,
    startAutoRefresh,
    stopAutoRefresh,
    toggleAutoRefresh,
    searchDeployments,
    setFilters,
    setSorting,
    resetFilters,
    toggleDeploymentSelection,
    selectAllDeployments,
    clearSelection
  }
})