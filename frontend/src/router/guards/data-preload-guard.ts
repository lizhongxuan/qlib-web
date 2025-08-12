import type { NavigationGuardNext, RouteLocationNormalized } from 'vue-router'
import { ElMessage } from 'element-plus'

interface PreloadConfig {
  path: string
  preloaders: PreloadFunction[]
  priority: 'high' | 'medium' | 'low'
  cache?: boolean
  timeout?: number
}

interface PreloadFunction {
  name: string
  loader: () => Promise<any>
  required: boolean
  cache?: boolean
  cacheKey?: string
  cacheDuration?: number
}

interface PreloadResult {
  name: string
  success: boolean
  data?: any
  error?: any
  duration: number
}

/**
 * 数据预加载守卫
 * 在页面导航前预先加载必要的数据
 */
export const dataPreloadGuard = async (
  to: RouteLocationNormalized,
  from: RouteLocationNormalized,
  next: NavigationGuardNext
) => {
  try {
    const preloadConfig = getPreloadConfig(to.path, to.params, to.query)
    
    if (!preloadConfig || preloadConfig.preloaders.length === 0) {
      return next()
    }

    // 显示加载状态
    const loadingMessage = ElMessage({
      message: '正在加载页面数据...',
      type: 'info',
      duration: 0,
      showClose: false
    })

    try {
      const startTime = Date.now()
      
      // 执行预加载
      const results = await executePreload(preloadConfig, to)
      
      const endTime = Date.now()
      const totalDuration = endTime - startTime
      
      // 检查必需数据是否加载成功
      const requiredResults = results.filter(r => 
        preloadConfig.preloaders.find(p => p.name === r.name)?.required
      )
      const failedRequired = requiredResults.filter(r => !r.success)
      
      if (failedRequired.length > 0) {
        // 必需数据加载失败
        loadingMessage.close()
        handlePreloadFailure(failedRequired, to)
        return next(false)
      }
      
      // 缓存成功加载的数据
      cachePreloadResults(results, to.path)
      
      // 记录预加载性能
      recordPreloadPerformance(to.path, results, totalDuration)
      
      loadingMessage.close()
      
      // 如果加载时间过长，显示提示
      if (totalDuration > 3000) {
        ElMessage.success(`数据加载完成 (${(totalDuration / 1000).toFixed(1)}s)`)
      }
      
      next()
    } catch (error) {
      loadingMessage.close()
      console.error('数据预加载失败:', error)
      
      // 允许继续导航，但显示错误提示
      ElMessage.warning('部分数据加载失败，页面功能可能受限')
      next()
    }
  } catch (error) {
    console.error('数据预加载守卫错误:', error)
    next()
  }
}

/**
 * 获取页面预加载配置
 */
const getPreloadConfig = (
  path: string, 
  params: any, 
  query: any
): PreloadConfig | null => {
  const configs: Record<string, PreloadConfig> = {
    '/dashboard': {
      path: '/dashboard',
      priority: 'high',
      cache: true,
      preloaders: [
        {
          name: 'user-summary',
          loader: () => loadUserSummary(),
          required: true,
          cache: true,
          cacheKey: 'user-summary',
          cacheDuration: 5 * 60 * 1000 // 5分钟
        },
        {
          name: 'recent-activities',
          loader: () => loadRecentActivities(),
          required: false,
          cache: true,
          cacheKey: 'recent-activities',
          cacheDuration: 2 * 60 * 1000 // 2分钟
        },
        {
          name: 'system-status',
          loader: () => loadSystemStatus(),
          required: false,
          cache: false
        }
      ]
    },
    '/factors': {
      path: '/factors',
      priority: 'high',
      cache: true,
      preloaders: [
        {
          name: 'factor-library',
          loader: () => loadFactorLibrary(),
          required: true,
          cache: true,
          cacheKey: 'factor-library',
          cacheDuration: 10 * 60 * 1000 // 10分钟
        },
        {
          name: 'factor-templates',
          loader: () => loadFactorTemplates(),
          required: false,
          cache: true,
          cacheKey: 'factor-templates',
          cacheDuration: 30 * 60 * 1000 // 30分钟
        },
        {
          name: 'data-dictionary',
          loader: () => loadDataDictionary(),
          required: false,
          cache: true,
          cacheKey: 'data-dictionary',
          cacheDuration: 60 * 60 * 1000 // 1小时
        }
      ]
    },
    '/training': {
      path: '/training',
      priority: 'high',
      cache: true,
      preloaders: [
        {
          name: 'available-factors',
          loader: () => loadAvailableFactors(),
          required: true,
          cache: true,
          cacheKey: 'available-factors',
          cacheDuration: 5 * 60 * 1000
        },
        {
          name: 'model-templates',
          loader: () => loadModelTemplates(),
          required: false,
          cache: true,
          cacheKey: 'model-templates',
          cacheDuration: 30 * 60 * 1000
        },
        {
          name: 'training-history',
          loader: () => loadTrainingHistory(),
          required: false,
          cache: true,
          cacheKey: 'training-history',
          cacheDuration: 2 * 60 * 1000
        }
      ]
    },
    '/training-management': {
      path: '/training-management',
      priority: 'medium',
      cache: true,
      preloaders: [
        {
          name: 'training-tasks',
          loader: () => loadTrainingTasks(),
          required: true,
          cache: false
        },
        {
          name: 'model-rankings',
          loader: () => loadModelRankings(),
          required: false,
          cache: true,
          cacheKey: 'model-rankings',
          cacheDuration: 5 * 60 * 1000
        }
      ]
    },
    '/backtest': {
      path: '/backtest',
      priority: 'high',
      cache: true,
      preloaders: [
        {
          name: 'trained-models',
          loader: () => loadTrainedModels(),
          required: true,
          cache: true,
          cacheKey: 'trained-models',
          cacheDuration: 5 * 60 * 1000
        },
        {
          name: 'backtest-templates',
          loader: () => loadBacktestTemplates(),
          required: false,
          cache: true,
          cacheKey: 'backtest-templates',
          cacheDuration: 30 * 60 * 1000
        },
        {
          name: 'market-data-status',
          loader: () => loadMarketDataStatus(),
          required: true,
          cache: false
        }
      ]
    },
    '/results': {
      path: '/results',
      priority: 'medium',
      cache: true,
      preloaders: [
        {
          name: 'backtest-results',
          loader: () => loadBacktestResults(query.strategy),
          required: true,
          cache: true,
          cacheKey: `backtest-results-${query.strategy || 'default'}`,
          cacheDuration: 10 * 60 * 1000
        },
        {
          name: 'benchmark-data',
          loader: () => loadBenchmarkData(),
          required: false,
          cache: true,
          cacheKey: 'benchmark-data',
          cacheDuration: 30 * 60 * 1000
        }
      ]
    },
    '/deployment': {
      path: '/deployment',
      priority: 'high',
      cache: false,
      preloaders: [
        {
          name: 'deployment-status',
          loader: () => loadDeploymentStatus(),
          required: true,
          cache: false
        },
        {
          name: 'available-strategies',
          loader: () => loadAvailableStrategies(),
          required: true,
          cache: true,
          cacheKey: 'available-strategies',
          cacheDuration: 5 * 60 * 1000
        },
        {
          name: 'broker-connections',
          loader: () => loadBrokerConnections(),
          required: false,
          cache: false
        }
      ]
    }
  }

  return configs[path] || null
}

/**
 * 执行预加载
 */
const executePreload = async (
  config: PreloadConfig, 
  to: RouteLocationNormalized
): Promise<PreloadResult[]> => {
  const results: PreloadResult[] = []
  
  // 根据优先级排序
  const sortedPreloaders = [...config.preloaders].sort((a, b) => {
    const priority = { high: 3, medium: 2, low: 1 }
    return (priority[config.priority] || 1) - (priority[config.priority] || 1)
  })
  
  // 并行执行预加载
  const preloadPromises = sortedPreloaders.map(async (preloader) => {
    const startTime = Date.now()
    
    try {
      // 检查缓存
      let data = null
      if (preloader.cache && preloader.cacheKey) {
        data = getCachedData(preloader.cacheKey)
        if (data) {
          return {
            name: preloader.name,
            success: true,
            data,
            duration: Date.now() - startTime
          }
        }
      }
      
      // 执行加载
      data = await preloader.loader()
      
      // 缓存数据
      if (preloader.cache && preloader.cacheKey && data) {
        setCachedData(preloader.cacheKey, data, preloader.cacheDuration)
      }
      
      return {
        name: preloader.name,
        success: true,
        data,
        duration: Date.now() - startTime
      }
    } catch (error) {
      return {
        name: preloader.name,
        success: false,
        error,
        duration: Date.now() - startTime
      }
    }
  })
  
  // 等待所有预加载完成
  const preloadResults = await Promise.all(preloadPromises)
  results.push(...preloadResults)
  
  return results
}

/**
 * 处理预加载失败
 */
const handlePreloadFailure = (failedResults: PreloadResult[], to: RouteLocationNormalized) => {
  const failedNames = failedResults.map(r => r.name).join('、')
  
  ElMessage.error({
    message: `关键数据加载失败：${failedNames}`,
    duration: 5000,
    showClose: true
  })
  
  // 记录失败信息
  console.error('预加载失败详情:', failedResults)
}

/**
 * 缓存预加载结果
 */
const cachePreloadResults = (results: PreloadResult[], path: string) => {
  const successResults = results.filter(r => r.success)
  
  if (successResults.length > 0) {
    const cacheKey = `preload-${path}`
    const cacheData = {
      results: successResults.map(r => ({ name: r.name, data: r.data })),
      timestamp: Date.now(),
      path
    }
    
    try {
      localStorage.setItem(cacheKey, JSON.stringify(cacheData))
    } catch (error) {
      console.warn('缓存预加载结果失败:', error)
    }
  }
}

/**
 * 记录预加载性能
 */
const recordPreloadPerformance = (
  path: string, 
  results: PreloadResult[], 
  totalDuration: number
) => {
  const performanceData = {
    path,
    totalDuration,
    totalLoaders: results.length,
    successCount: results.filter(r => r.success).length,
    failureCount: results.filter(r => !r.success).length,
    averageDuration: results.reduce((sum, r) => sum + r.duration, 0) / results.length,
    timestamp: Date.now()
  }
  
  // 保存到性能监控
  const performanceHistory = JSON.parse(
    localStorage.getItem('preload-performance') || '[]'
  )
  
  performanceHistory.push(performanceData)
  
  // 只保留最近100条记录
  if (performanceHistory.length > 100) {
    performanceHistory.splice(0, performanceHistory.length - 100)
  }
  
  localStorage.setItem('preload-performance', JSON.stringify(performanceHistory))
}

// 缓存相关函数
const getCachedData = (key: string) => {
  try {
    const cached = localStorage.getItem(`cache-${key}`)
    if (!cached) return null
    
    const data = JSON.parse(cached)
    
    // 检查是否过期
    if (data.expiry && Date.now() > data.expiry) {
      localStorage.removeItem(`cache-${key}`)
      return null
    }
    
    return data.value
  } catch {
    return null
  }
}

const setCachedData = (key: string, value: any, duration?: number) => {
  try {
    const expiry = duration ? Date.now() + duration : null
    const cacheData = { value, expiry, timestamp: Date.now() }
    localStorage.setItem(`cache-${key}`, JSON.stringify(cacheData))
  } catch (error) {
    console.warn('设置缓存失败:', error)
  }
}

// 数据加载函数（模拟API调用）
const loadUserSummary = async () => {
  await new Promise(resolve => setTimeout(resolve, 300))
  return {
    totalExperiments: 15,
    runningTasks: 2,
    totalFactors: 8,
    deployedStrategies: 3
  }
}

const loadRecentActivities = async () => {
  await new Promise(resolve => setTimeout(resolve, 200))
  return [
    { id: 1, type: 'training', message: '模型训练完成', timestamp: Date.now() - 3600000 },
    { id: 2, type: 'backtest', message: '回测执行成功', timestamp: Date.now() - 7200000 }
  ]
}

const loadSystemStatus = async () => {
  await new Promise(resolve => setTimeout(resolve, 100))
  return {
    dataService: 'healthy',
    trainingService: 'healthy',
    deploymentService: 'healthy'
  }
}

const loadFactorLibrary = async () => {
  await new Promise(resolve => setTimeout(resolve, 500))
  return JSON.parse(localStorage.getItem('user-factors') || '[]')
}

const loadFactorTemplates = async () => {
  await new Promise(resolve => setTimeout(resolve, 300))
  return [
    { id: 'momentum', name: '动量因子', category: 'technical' },
    { id: 'value', name: '价值因子', category: 'fundamental' }
  ]
}

const loadDataDictionary = async () => {
  await new Promise(resolve => setTimeout(resolve, 200))
  return {
    fields: ['open', 'high', 'low', 'close', 'volume'],
    functions: ['mean', 'std', 'rank', 'delay']
  }
}

const loadAvailableFactors = async () => {
  await new Promise(resolve => setTimeout(resolve, 400))
  return JSON.parse(localStorage.getItem('user-factors') || '[]')
}

const loadModelTemplates = async () => {
  await new Promise(resolve => setTimeout(resolve, 300))
  return [
    { id: 'lgb', name: 'LightGBM', type: 'tree-based' },
    { id: 'xgb', name: 'XGBoost', type: 'tree-based' },
    { id: 'lstm', name: 'LSTM', type: 'neural-network' }
  ]
}

const loadTrainingHistory = async () => {
  await new Promise(resolve => setTimeout(resolve, 200))
  return JSON.parse(localStorage.getItem('training-history') || '[]')
}

const loadTrainingTasks = async () => {
  await new Promise(resolve => setTimeout(resolve, 300))
  return JSON.parse(localStorage.getItem('training-tasks') || '[]')
}

const loadModelRankings = async () => {
  await new Promise(resolve => setTimeout(resolve, 400))
  return JSON.parse(localStorage.getItem('model-rankings') || '[]')
}

const loadTrainedModels = async () => {
  await new Promise(resolve => setTimeout(resolve, 300))
  return JSON.parse(localStorage.getItem('trained-models') || '[]')
}

const loadBacktestTemplates = async () => {
  await new Promise(resolve => setTimeout(resolve, 200))
  return [
    { id: 'default', name: '默认配置', description: '标准回测配置' },
    { id: 'high-freq', name: '高频交易', description: '适用于高频策略' }
  ]
}

const loadMarketDataStatus = async () => {
  await new Promise(resolve => setTimeout(resolve, 100))
  return {
    lastUpdate: Date.now() - 3600000,
    coverage: '2020-01-01 to 2024-12-31',
    status: 'healthy'
  }
}

const loadBacktestResults = async (strategyId?: string) => {
  await new Promise(resolve => setTimeout(resolve, 600))
  return JSON.parse(localStorage.getItem('backtest-results') || '[]')
}

const loadBenchmarkData = async () => {
  await new Promise(resolve => setTimeout(resolve, 400))
  return {
    hs300: { return: 0.08, volatility: 0.18 },
    zz500: { return: 0.06, volatility: 0.22 }
  }
}

const loadDeploymentStatus = async () => {
  await new Promise(resolve => setTimeout(resolve, 200))
  return JSON.parse(localStorage.getItem('deployment-status') || '[]')
}

const loadAvailableStrategies = async () => {
  await new Promise(resolve => setTimeout(resolve, 300))
  return JSON.parse(localStorage.getItem('available-strategies') || '[]')
}

const loadBrokerConnections = async () => {
  await new Promise(resolve => setTimeout(resolve, 100))
  return JSON.parse(localStorage.getItem('broker-connections') || '[]')
}

/**
 * 清除过期缓存
 */
export const clearExpiredCache = () => {
  const keys = Object.keys(localStorage)
  keys.forEach(key => {
    if (key.startsWith('cache-')) {
      try {
        const data = JSON.parse(localStorage.getItem(key) || '{}')
        if (data.expiry && Date.now() > data.expiry) {
          localStorage.removeItem(key)
        }
      } catch {
        localStorage.removeItem(key)
      }
    }
  })
}

/**
 * 获取预加载性能统计
 */
export const getPreloadPerformanceStats = () => {
  const history = JSON.parse(localStorage.getItem('preload-performance') || '[]')
  
  if (history.length === 0) {
    return null
  }
  
  const stats = {
    totalRequests: history.length,
    averageDuration: history.reduce((sum: number, h: any) => sum + h.totalDuration, 0) / history.length,
    successRate: history.reduce((sum: number, h: any) => sum + h.successCount, 0) / 
                 history.reduce((sum: number, h: any) => sum + h.totalLoaders, 0),
    slowestPage: history.reduce((max: any, h: any) => h.totalDuration > (max?.totalDuration || 0) ? h : max, null),
    fastestPage: history.reduce((min: any, h: any) => h.totalDuration < (min?.totalDuration || Infinity) ? h : min, null)
  }
  
  return stats
}