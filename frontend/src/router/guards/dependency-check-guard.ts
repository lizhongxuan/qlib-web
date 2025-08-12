import type { NavigationGuardNext, RouteLocationNormalized } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'

interface PageDependency {
  path: string
  name: string
  checker: () => Promise<boolean>
  resolver?: () => Promise<boolean>
  message?: string
  autoResolve?: boolean
}

interface DependencyResult {
  satisfied: boolean
  missing: string[]
  resolvable: string[]
  message?: string
}

/**
 * 依赖检查守卫
 * 确保页面访问前满足必要的依赖条件
 */
export const dependencyCheckGuard = async (
  to: RouteLocationNormalized,
  from: RouteLocationNormalized,
  next: NavigationGuardNext
) => {
  try {
    // 获取目标页面的依赖配置
    const dependencies = getPageDependencies(to.path)
    
    if (dependencies.length === 0) {
      return next()
    }

    // 检查所有依赖
    const dependencyResult = await checkDependencies(dependencies)
    
    if (dependencyResult.satisfied) {
      return next()
    }

    // 处理未满足的依赖
    const handled = await handleUnsatisfiedDependencies(
      dependencyResult,
      to,
      from,
      dependencies
    )
    
    if (handled) {
      next()
    } else {
      next(false)
    }
  } catch (error) {
    console.error('依赖检查守卫错误:', error)
    next()
  }
}

/**
 * 获取页面依赖配置
 */
const getPageDependencies = (path: string): PageDependency[] => {
  const dependencyMap: Record<string, PageDependency[]> = {
    '/training': [
      {
        path: '/factors',
        name: '因子数据',
        checker: checkFactorAvailability,
        resolver: createBasicFactor,
        message: '模型训练需要至少一个有效的因子',
        autoResolve: false
      },
      {
        path: '/data',
        name: '历史数据',
        checker: checkHistoricalData,
        message: '训练需要足够的历史数据'
      }
    ],
    '/backtest': [
      {
        path: '/training',
        name: '训练模型',
        checker: checkTrainedModel,
        resolver: navigateToTraining,
        message: '策略回测需要至少一个已训练的模型'
      },
      {
        path: '/factors',
        name: '因子配置',
        checker: checkFactorConfiguration,
        message: '回测需要完整的因子配置'
      },
      {
        path: '/data',
        name: '市场数据',
        checker: checkMarketData,
        message: '回测需要相应时间段的市场数据'
      }
    ],
    '/results': [
      {
        path: '/backtest',
        name: '回测结果',
        checker: checkBacktestResults,
        message: '需要完成至少一次回测才能查看结果'
      }
    ],
    '/deployment': [
      {
        path: '/backtest',
        name: '回测验证',
        checker: checkSuccessfulBacktest,
        message: '部署前需要完成成功的回测验证'
      },
      {
        path: '/results',
        name: '性能分析',
        checker: checkPerformanceAnalysis,
        message: '部署前建议完成详细的性能分析'
      },
      {
        path: '/broker',
        name: '券商连接',
        checker: checkBrokerConnection,
        resolver: configureBrokerConnection,
        message: '实盘部署需要配置券商接口'
      }
    ]
  }

  return dependencyMap[path] || []
}

/**
 * 检查所有依赖
 */
const checkDependencies = async (dependencies: PageDependency[]): Promise<DependencyResult> => {
  const results = await Promise.all(
    dependencies.map(async (dep) => ({
      dependency: dep,
      satisfied: await dep.checker()
    }))
  )

  const unsatisfied = results.filter(r => !r.satisfied)
  const resolvable = unsatisfied
    .filter(r => r.dependency.resolver)
    .map(r => r.dependency.name)

  return {
    satisfied: unsatisfied.length === 0,
    missing: unsatisfied.map(r => r.dependency.name),
    resolvable,
    message: unsatisfied.length > 0 ? unsatisfied[0].dependency.message : undefined
  }
}

/**
 * 处理未满足的依赖
 */
const handleUnsatisfiedDependencies = async (
  result: DependencyResult,
  to: RouteLocationNormalized,
  from: RouteLocationNormalized,
  dependencies: PageDependency[]
): Promise<boolean> => {
  const firstMissing = result.missing[0]
  const missingDep = dependencies.find(d => d.name === firstMissing)
  
  if (!missingDep) return false

  // 如果可以自动解决
  if (missingDep.autoResolve && missingDep.resolver) {
    try {
      const resolved = await missingDep.resolver()
      if (resolved) {
        ElMessage.success(`已自动解决依赖：${missingDep.name}`)
        return true
      }
    } catch (error) {
      console.error(`自动解决依赖失败:`, error)
    }
  }

  // 显示依赖解决对话框
  return await showDependencyDialog(result, missingDep, to)
}

/**
 * 显示依赖解决对话框
 */
const showDependencyDialog = async (
  result: DependencyResult,
  missingDep: PageDependency,
  to: RouteLocationNormalized
): Promise<boolean> => {
  try {
    const actions = []
    
    if (missingDep.resolver) {
      actions.push({
        text: '自动解决',
        action: 'resolve'
      })
    }
    
    if (missingDep.path) {
      actions.push({
        text: `前往${missingDep.name}页面`,
        action: 'navigate'
      })
    }
    
    actions.push({
      text: '忽略并继续',
      action: 'ignore'
    })

    const message = `
      ${result.message || '页面访问需要满足一些前置条件'}
      
      缺少的依赖：${result.missing.join('、')}
      
      建议的解决方案：
      ${actions.map(a => `• ${a.text}`).join('\n')}
    `

    const actionResult = await ElMessageBox.confirm(
      message,
      '依赖检查',
      {
        confirmButtonText: actions[0]?.text || '确定',
        cancelButtonText: '取消',
        type: 'warning',
        customClass: 'dependency-dialog'
      }
    )

    // 执行选择的操作
    return await executeSelectedAction(actions[0]?.action || 'ignore', missingDep, to)
  } catch {
    return false
  }
}

/**
 * 执行选择的操作
 */
const executeSelectedAction = async (
  action: string,
  missingDep: PageDependency,
  to: RouteLocationNormalized
): Promise<boolean> => {
  switch (action) {
    case 'resolve':
      if (missingDep.resolver) {
        try {
          const resolved = await missingDep.resolver()
          if (resolved) {
            ElMessage.success(`已解决依赖：${missingDep.name}`)
            return true
          } else {
            ElMessage.error(`解决依赖失败：${missingDep.name}`)
            return false
          }
        } catch (error) {
          ElMessage.error(`解决依赖时发生错误：${error}`)
          return false
        }
      }
      return false

    case 'navigate':
      if (missingDep.path) {
        // 导航到依赖页面
        window.location.hash = missingDep.path
        return false
      }
      return false

    case 'ignore':
      ElMessage.warning('已忽略依赖检查，可能会影响页面功能')
      return true

    default:
      return false
  }
}

// 依赖检查器实现
const checkFactorAvailability = async (): Promise<boolean> => {
  // 检查是否有可用的因子
  try {
    const factors = JSON.parse(localStorage.getItem('user-factors') || '[]')
    return factors.length > 0
  } catch {
    return false
  }
}

const checkHistoricalData = async (): Promise<boolean> => {
  // 检查历史数据可用性
  try {
    // 这里应该调用API检查数据状态
    const dataStatus = localStorage.getItem('data-status')
    return dataStatus === 'available'
  } catch {
    return false
  }
}

const checkTrainedModel = async (): Promise<boolean> => {
  // 检查是否有已训练的模型
  try {
    const models = JSON.parse(localStorage.getItem('trained-models') || '[]')
    return models.some((model: any) => model.status === 'completed')
  } catch {
    return false
  }
}

const checkFactorConfiguration = async (): Promise<boolean> => {
  // 检查因子配置完整性
  try {
    const config = JSON.parse(localStorage.getItem('factor-config') || '{}')
    return Object.keys(config).length > 0
  } catch {
    return false
  }
}

const checkMarketData = async (): Promise<boolean> => {
  // 检查市场数据
  return true // 假设市场数据总是可用的
}

const checkBacktestResults = async (): Promise<boolean> => {
  // 检查回测结果
  try {
    const results = JSON.parse(localStorage.getItem('backtest-results') || '[]')
    return results.length > 0
  } catch {
    return false
  }
}

const checkSuccessfulBacktest = async (): Promise<boolean> => {
  // 检查成功的回测
  try {
    const results = JSON.parse(localStorage.getItem('backtest-results') || '[]')
    return results.some((result: any) => result.status === 'completed' && result.performance?.sharpeRatio > 1)
  } catch {
    return false
  }
}

const checkPerformanceAnalysis = async (): Promise<boolean> => {
  // 检查性能分析完成情况
  try {
    const analysis = localStorage.getItem('performance-analysis')
    return analysis === 'completed'
  } catch {
    return false
  }
}

const checkBrokerConnection = async (): Promise<boolean> => {
  // 检查券商连接
  try {
    const brokerConfig = JSON.parse(localStorage.getItem('broker-config') || '{}')
    return brokerConfig.connected === true
  } catch {
    return false
  }
}

// 依赖解决器实现
const createBasicFactor = async (): Promise<boolean> => {
  // 创建基础因子
  try {
    const basicFactor = {
      id: `basic-factor-${Date.now()}`,
      name: '基础动量因子',
      expression: 'close / delay(close, 20) - 1',
      description: '系统自动创建的基础动量因子',
      created: Date.now()
    }
    
    const factors = JSON.parse(localStorage.getItem('user-factors') || '[]')
    factors.push(basicFactor)
    localStorage.setItem('user-factors', JSON.stringify(factors))
    
    return true
  } catch {
    return false
  }
}

const navigateToTraining = async (): Promise<boolean> => {
  // 导航到训练页面
  window.location.hash = '/training'
  return false // 返回false表示需要重定向
}

const configureBrokerConnection = async (): Promise<boolean> => {
  // 配置券商连接
  try {
    // 这里应该打开券商配置对话框
    // 暂时设置为模拟连接
    const brokerConfig = {
      type: 'simulation',
      connected: true,
      configuredAt: Date.now()
    }
    
    localStorage.setItem('broker-config', JSON.stringify(brokerConfig))
    return true
  } catch {
    return false
  }
}

/**
 * 批量依赖检查
 */
export const batchDependencyCheck = async (paths: string[]): Promise<Record<string, DependencyResult>> => {
  const results: Record<string, DependencyResult> = {}
  
  for (const path of paths) {
    const dependencies = getPageDependencies(path)
    if (dependencies.length > 0) {
      results[path] = await checkDependencies(dependencies)
    } else {
      results[path] = { satisfied: true, missing: [], resolvable: [] }
    }
  }
  
  return results
}

/**
 * 获取全局依赖状态
 */
export const getGlobalDependencyStatus = async () => {
  const allPaths = ['/training', '/backtest', '/results', '/deployment']
  const batchResults = await batchDependencyCheck(allPaths)
  
  const summary = {
    totalPages: allPaths.length,
    satisfiedPages: 0,
    unsatisfiedPages: 0,
    criticalIssues: [] as string[],
    recommendations: [] as string[]
  }
  
  Object.entries(batchResults).forEach(([path, result]) => {
    if (result.satisfied) {
      summary.satisfiedPages++
    } else {
      summary.unsatisfiedPages++
      if (result.missing.includes('历史数据') || result.missing.includes('券商连接')) {
        summary.criticalIssues.push(`${path}: ${result.missing.join('、')}`)
      }
    }
  })
  
  // 生成建议
  if (summary.criticalIssues.length > 0) {
    summary.recommendations.push('建议先解决关键依赖问题以确保系统正常运行')
  }
  
  if (summary.unsatisfiedPages > 0) {
    summary.recommendations.push('可以使用智能工作流向导来解决依赖问题')
  }
  
  return summary
}