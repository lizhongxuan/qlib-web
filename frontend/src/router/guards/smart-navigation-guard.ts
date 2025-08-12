import type { NavigationGuardNext, RouteLocationNormalized } from 'vue-router'
import { useNavigationStore } from '@/stores/navigation'
import { useWorkflowStore } from '@/stores/workflow'
import { ElMessage, ElMessageBox } from 'element-plus'

/**
 * 智能导航守卫
 * 提供智能路由建议、工作流检查、页面跳转优化
 */
export const smartNavigationGuard = async (
  to: RouteLocationNormalized,
  from: RouteLocationNormalized,
  next: NavigationGuardNext
) => {
  const navigationStore = useNavigationStore()
  const workflowStore = useWorkflowStore()

  try {
    // 1. 检查是否有未保存的更改
    const hasUnsavedChanges = await checkUnsavedChanges(from)
    if (hasUnsavedChanges) {
      const confirmed = await confirmLeaveWithUnsavedChanges()
      if (!confirmed) {
        return next(false)
      }
    }

    // 2. 工作流程导航智能建议
    if (workflowStore.isWorkflowActive) {
      const workflowSuggestion = await checkWorkflowNavigation(from, to, workflowStore)
      if (workflowSuggestion) {
        const shouldFollowWorkflow = await showWorkflowSuggestion(workflowSuggestion)
        if (shouldFollowWorkflow && workflowSuggestion.suggestedRoute !== to.path) {
          return next(workflowSuggestion.suggestedRoute)
        }
      }
    }

    // 3. 智能路由优化
    const optimizedRoute = await optimizeRouteNavigation(to, from)
    if (optimizedRoute && optimizedRoute !== to.path) {
      ElMessage.success(`已为您优化路由路径`)
      return next(optimizedRoute)
    }

    // 4. 记录导航意图，用于后续智能推荐
    recordNavigationIntent(from, to)

    // 5. 检查页面访问模式，提供智能建议
    const accessPattern = analyzeAccessPattern(to, from)
    if (accessPattern.suggestion) {
      // 异步显示建议，不阻塞导航
      setTimeout(() => {
        showAccessPatternSuggestion(accessPattern.suggestion!)
      }, 1000)
    }

    next()
  } catch (error) {
    console.error('智能导航守卫错误:', error)
    next()
  }
}

/**
 * 检查页面是否有未保存的更改
 */
const checkUnsavedChanges = async (from: RouteLocationNormalized): Promise<boolean> => {
  // 检查不同页面的未保存状态
  switch (from.path) {
    case '/factors':
      return checkFactorPageUnsavedChanges()
    case '/training':
      return checkTrainingPageUnsavedChanges()
    case '/backtest':
      return checkBacktestPageUnsavedChanges()
    default:
      return false
  }
}

const checkFactorPageUnsavedChanges = (): boolean => {
  // 检查因子编辑器是否有未保存的内容
  // 这里应该从对应的store或组件状态中获取
  return false
}

const checkTrainingPageUnsavedChanges = (): boolean => {
  // 检查训练配置是否有未保存的更改
  return false
}

const checkBacktestPageUnsavedChanges = (): boolean => {
  // 检查回测配置是否有未保存的更改
  return false
}

/**
 * 确认是否离开有未保存更改的页面
 */
const confirmLeaveWithUnsavedChanges = async (): Promise<boolean> => {
  try {
    await ElMessageBox.confirm(
      '当前页面有未保存的更改，确定要离开吗？',
      '确认离开',
      {
        confirmButtonText: '离开',
        cancelButtonText: '继续编辑',
        type: 'warning',
        customClass: 'smart-navigation-dialog'
      }
    )
    return true
  } catch {
    return false
  }
}

/**
 * 检查工作流导航建议
 */
const checkWorkflowNavigation = async (
  from: RouteLocationNormalized,
  to: RouteLocationNormalized,
  workflowStore: any
) => {
  const currentStep = workflowStore.currentStep
  if (!currentStep) return null

  // 检查是否跳过了推荐的工作流步骤
  const expectedNextRoute = getExpectedNextRoute(currentStep)
  if (expectedNextRoute && to.path !== expectedNextRoute) {
    // 用户要去的页面不是推荐的下一步
    const suggestion = generateWorkflowSuggestion(currentStep, to.path, expectedNextRoute)
    return suggestion
  }

  return null
}

const getExpectedNextRoute = (currentStep: any): string | null => {
  // 根据工作流步骤返回推荐的下一个路由
  switch (currentStep.key) {
    case 'factor-development':
      return '/training'
    case 'model-training':
      return '/backtest'
    case 'strategy-backtest':
      return '/results'
    case 'results-analysis':
      return '/deployment'
    default:
      return null
  }
}

const generateWorkflowSuggestion = (currentStep: any, targetRoute: string, expectedRoute: string) => {
  return {
    type: 'workflow-optimization',
    message: `根据当前工作流进度，建议先完成"${getRouteTitle(expectedRoute)}"再前往"${getRouteTitle(targetRoute)}"`,
    currentStep: currentStep.title,
    suggestedRoute: expectedRoute,
    targetRoute: targetRoute,
    reason: '这样可以保证工作流程的连贯性和数据的完整性'
  }
}

/**
 * 显示工作流建议
 */
const showWorkflowSuggestion = async (suggestion: any): Promise<boolean> => {
  try {
    const result = await ElMessageBox.confirm(
      `${suggestion.message}\n\n${suggestion.reason}`,
      '工作流建议',
      {
        confirmButtonText: '按建议导航',
        cancelButtonText: '继续原计划',
        type: 'info',
        customClass: 'workflow-suggestion-dialog'
      }
    )
    return true
  } catch {
    return false
  }
}

/**
 * 优化路由导航
 */
const optimizeRouteNavigation = async (
  to: RouteLocationNormalized,
  from: RouteLocationNormalized
): Promise<string | null> => {
  // 检查是否可以通过更直接的路径到达目标页面
  if (to.path === '/training' && from.path === '/dashboard') {
    // 如果用户从仪表盘直接跳转到训练页面，检查是否有可用的因子
    const hasFactors = await checkAvailableFactors()
    if (!hasFactors) {
      // 建议先去因子开发页面
      const shouldGoToFactors = await ElMessageBox.confirm(
        '检测到您还没有创建因子，是否先前往因子开发页面？',
        '智能导航建议',
        {
          confirmButtonText: '前往因子开发',
          cancelButtonText: '直接进入训练',
          type: 'info'
        }
      )
      if (shouldGoToFactors) {
        return '/factors'
      }
    }
  }

  return null
}

/**
 * 记录导航意图
 */
const recordNavigationIntent = (from: RouteLocationNormalized, to: RouteLocationNormalized) => {
  // 记录用户的导航模式，用于后续智能推荐
  const navigationPattern = {
    from: from.path,
    to: to.path,
    timestamp: Date.now(),
    params: to.params,
    query: to.query
  }

  // 保存到本地存储或发送到分析服务
  const existingPatterns = JSON.parse(localStorage.getItem('navigation-patterns') || '[]')
  existingPatterns.push(navigationPattern)
  
  // 只保留最近100条记录
  if (existingPatterns.length > 100) {
    existingPatterns.splice(0, existingPatterns.length - 100)
  }
  
  localStorage.setItem('navigation-patterns', JSON.stringify(existingPatterns))
}

/**
 * 分析访问模式
 */
const analyzeAccessPattern = (to: RouteLocationNormalized, from: RouteLocationNormalized) => {
  const patterns = JSON.parse(localStorage.getItem('navigation-patterns') || '[]')
  
  // 分析最近的导航模式
  const recentPatterns = patterns.slice(-20) // 最近20次导航
  
  // 检查是否有重复的无效导航（频繁在两个页面间跳转）
  const backAndForth = checkBackAndForthPattern(recentPatterns, from.path, to.path)
  if (backAndForth.detected) {
    return {
      type: 'back-and-forth',
      suggestion: {
        message: `检测到您在"${getRouteTitle(from.path)}"和"${getRouteTitle(to.path)}"之间频繁切换`,
        recommendation: '建议使用分屏或标签页功能提高效率',
        action: 'open-split-view'
      }
    }
  }

  // 检查是否错过了中间步骤
  const missedSteps = checkMissedWorkflowSteps(from.path, to.path)
  if (missedSteps.length > 0) {
    return {
      type: 'missed-steps',
      suggestion: {
        message: `您可能跳过了一些推荐步骤：${missedSteps.join('、')}`,
        recommendation: '是否需要先完成这些步骤？',
        action: 'show-workflow-guide'
      }
    }
  }

  return { type: 'normal' }
}

const checkBackAndForthPattern = (patterns: any[], fromPath: string, toPath: string) => {
  let backAndForthCount = 0
  let lastFrom = ''
  let lastTo = ''

  for (const pattern of patterns) {
    if ((pattern.from === fromPath && pattern.to === toPath) ||
        (pattern.from === toPath && pattern.to === fromPath)) {
      if (lastFrom === pattern.to && lastTo === pattern.from) {
        backAndForthCount++
      }
      lastFrom = pattern.from
      lastTo = pattern.to
    }
  }

  return {
    detected: backAndForthCount >= 3,
    count: backAndForthCount
  }
}

const checkMissedWorkflowSteps = (fromPath: string, toPath: string): string[] => {
  const workflowOrder = ['/factors', '/training', '/backtest', '/results', '/deployment']
  const fromIndex = workflowOrder.indexOf(fromPath)
  const toIndex = workflowOrder.indexOf(toPath)

  if (fromIndex !== -1 && toIndex !== -1 && toIndex > fromIndex + 1) {
    // 跳过了中间步骤
    return workflowOrder.slice(fromIndex + 1, toIndex).map(getRouteTitle)
  }

  return []
}

/**
 * 显示访问模式建议
 */
const showAccessPatternSuggestion = (suggestion: any) => {
  ElMessage({
    message: suggestion.message,
    type: 'info',
    duration: 5000,
    showClose: true
  })
}

// 辅助函数
const getRouteTitle = (path: string): string => {
  const titleMap: Record<string, string> = {
    '/dashboard': '仪表盘',
    '/factors': '因子开发',
    '/training': '模型训练',
    '/backtest': '策略回测',
    '/results': '结果分析',
    '/deployment': '策略部署'
  }
  return titleMap[path] || path
}

const checkAvailableFactors = async (): Promise<boolean> => {
  // 检查是否有可用的因子
  // 这里应该调用实际的API或检查store状态
  return false
}