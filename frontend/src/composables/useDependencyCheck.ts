import { ref, reactive, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'

// 依赖项接口
interface Dependency {
  id: string
  name: string
  type: 'data' | 'config' | 'resource' | 'permission' | 'service'
  required: boolean
  description: string
  checkFunction: () => Promise<DependencyResult>
  resolveFunction?: () => Promise<boolean>
  dependencies?: string[] // 依赖的其他依赖项
}

// 依赖检查结果
interface DependencyResult {
  available: boolean
  data?: any
  error?: string
  warning?: string
  suggestions?: string[]
  metadata?: Record<string, any>
}

// 检查配置
interface CheckConfig {
  autoCheck: boolean
  showProgress: boolean
  resolveAutomatically: boolean
  continueOnError: boolean
  timeout: number
  retryCount: number
  retryDelay: number
}

// 依赖状态
interface DependencyState {
  id: string
  name: string
  status: 'pending' | 'checking' | 'available' | 'missing' | 'error'
  result?: DependencyResult
  lastChecked?: Date
  retryCount: number
}

// 依赖检查管理器
class DependencyCheckManager {
  private dependencies: Map<string, Dependency> = new Map()
  private checkResults: Map<string, DependencyResult> = new Map()

  // 注册依赖项
  register(dependency: Dependency): void {
    this.dependencies.set(dependency.id, dependency)
  }

  // 批量注册依赖项
  registerMany(dependencies: Dependency[]): void {
    dependencies.forEach(dep => this.register(dep))
  }

  // 移除依赖项
  remove(dependencyId: string): boolean {
    return this.dependencies.delete(dependencyId)
  }

  // 获取依赖项
  get(dependencyId: string): Dependency | undefined {
    return this.dependencies.get(dependencyId)
  }

  // 获取所有依赖项
  getAll(): Dependency[] {
    return Array.from(this.dependencies.values())
  }

  // 检查单个依赖
  async checkDependency(dependencyId: string, timeout?: number): Promise<DependencyResult> {
    const dependency = this.dependencies.get(dependencyId)
    if (!dependency) {
      throw new Error(`Dependency ${dependencyId} not found`)
    }

    try {
      const result = timeout 
        ? await this.withTimeout(dependency.checkFunction(), timeout)
        : await dependency.checkFunction()
      
      this.checkResults.set(dependencyId, result)
      return result
    } catch (error) {
      const errorResult: DependencyResult = {
        available: false,
        error: error instanceof Error ? error.message : String(error)
      }
      this.checkResults.set(dependencyId, errorResult)
      return errorResult
    }
  }

  // 批量检查依赖
  async checkMultiple(
    dependencyIds: string[], 
    config: Partial<CheckConfig> = {}
  ): Promise<Map<string, DependencyResult>> {
    const results = new Map<string, DependencyResult>()
    const { timeout = 10000, retryCount = 2, retryDelay = 1000 } = config

    for (const id of dependencyIds) {
      let attempt = 0
      let lastError: any

      while (attempt <= retryCount) {
        try {
          const result = await this.checkDependency(id, timeout)
          results.set(id, result)
          break
        } catch (error) {
          lastError = error
          attempt++
          
          if (attempt <= retryCount) {
            await new Promise(resolve => setTimeout(resolve, retryDelay))
          }
        }
      }

      if (attempt > retryCount) {
        results.set(id, {
          available: false,
          error: `Failed after ${retryCount} retries: ${lastError}`
        })
      }
    }

    return results
  }

  // 解决依赖问题
  async resolveDependency(dependencyId: string): Promise<boolean> {
    const dependency = this.dependencies.get(dependencyId)
    if (!dependency || !dependency.resolveFunction) {
      return false
    }

    try {
      return await dependency.resolveFunction()
    } catch (error) {
      console.error(`Failed to resolve dependency ${dependencyId}:`, error)
      return false
    }
  }

  // 获取依赖树
  getDependencyTree(rootId: string): Dependency[] {
    const visited = new Set<string>()
    const result: Dependency[] = []

    const traverse = (id: string) => {
      if (visited.has(id)) return
      visited.add(id)

      const dep = this.dependencies.get(id)
      if (!dep) return

      result.push(dep)

      if (dep.dependencies) {
        dep.dependencies.forEach(traverse)
      }
    }

    traverse(rootId)
    return result
  }

  // 获取检查结果
  getResult(dependencyId: string): DependencyResult | undefined {
    return this.checkResults.get(dependencyId)
  }

  // 带超时的Promise包装
  private withTimeout<T>(promise: Promise<T>, timeout: number): Promise<T> {
    return Promise.race([
      promise,
      new Promise<never>((_, reject) => 
        setTimeout(() => reject(new Error('Timeout')), timeout)
      )
    ])
  }
}

// 全局管理器实例
const dependencyManager = new DependencyCheckManager()

// 预定义的常见依赖检查
const commonDependencies: Dependency[] = [
  {
    id: 'factors_data',
    name: '因子数据',
    type: 'data',
    required: true,
    description: '检查因子数据是否可用',
    checkFunction: async () => {
      // 模拟检查因子数据
      const factorsAvailable = Math.random() > 0.2
      return {
        available: factorsAvailable,
        data: factorsAvailable ? ['factor1', 'factor2'] : null,
        error: factorsAvailable ? undefined : '因子数据不可用'
      }
    },
    resolveFunction: async () => {
      // 模拟解决方案
      return Math.random() > 0.3
    }
  },
  {
    id: 'model_trained',
    name: '训练好的模型',
    type: 'resource',
    required: true,
    description: '检查是否有可用的训练模型',
    checkFunction: async () => {
      const modelsAvailable = Math.random() > 0.3
      return {
        available: modelsAvailable,
        data: modelsAvailable ? ['model1', 'model2'] : null,
        error: modelsAvailable ? undefined : '没有可用的训练模型'
      }
    },
    dependencies: ['factors_data']
  },
  {
    id: 'backtest_config',
    name: '回测配置',
    type: 'config',
    required: true,
    description: '检查回测配置是否完整',
    checkFunction: async () => {
      const configValid = Math.random() > 0.1
      return {
        available: configValid,
        warning: configValid ? undefined : '回测配置不完整',
        suggestions: ['检查时间范围设置', '确认策略参数']
      }
    }
  },
  {
    id: 'api_service',
    name: 'API服务',
    type: 'service',
    required: true,
    description: '检查后端API服务是否可用',
    checkFunction: async () => {
      try {
        // 模拟API健康检查
        await new Promise(resolve => setTimeout(resolve, 500))
        return {
          available: true,
          metadata: { latency: 120, version: '1.0.0' }
        }
      } catch {
        return {
          available: false,
          error: 'API服务不可用'
        }
      }
    }
  },
  {
    id: 'user_permissions',
    name: '用户权限',
    type: 'permission',
    required: true,
    description: '检查用户是否有足够的权限',
    checkFunction: async () => {
      const hasPermission = Math.random() > 0.05
      return {
        available: hasPermission,
        error: hasPermission ? undefined : '权限不足'
      }
    }
  }
]

// 注册预定义依赖
commonDependencies.forEach(dep => dependencyManager.register(dep))

// Composable 函数
export function useDependencyCheck(
  requiredDependencies: string[] = [],
  initialConfig: Partial<CheckConfig> = {}
) {
  const route = useRoute()
  const router = useRouter()

  // 默认配置
  const defaultConfig: CheckConfig = {
    autoCheck: true,
    showProgress: true,
    resolveAutomatically: false,
    continueOnError: false,
    timeout: 10000,
    retryCount: 2,
    retryDelay: 1000
  }

  // 合并配置
  const config = reactive({ ...defaultConfig, ...initialConfig })

  // 状态
  const isChecking = ref(false)
  const checkProgress = ref(0)
  const dependencyStates = reactive<Map<string, DependencyState>>(new Map())
  const checkHistory = ref<Array<{ timestamp: Date; results: Map<string, DependencyResult> }>>([])

  // 初始化依赖状态
  const initializeDependencyStates = () => {
    requiredDependencies.forEach(depId => {
      const dependency = dependencyManager.get(depId)
      if (dependency) {
        dependencyStates.set(depId, {
          id: depId,
          name: dependency.name,
          status: 'pending',
          retryCount: 0
        })
      }
    })
  }

  // 计算属性
  const allDependenciesAvailable = computed(() => {
    return Array.from(dependencyStates.values()).every(
      state => state.status === 'available'
    )
  })

  const requiredDependenciesMissing = computed(() => {
    return Array.from(dependencyStates.values()).filter(
      state => {
        const dep = dependencyManager.get(state.id)
        return dep?.required && state.status === 'missing'
      }
    )
  })

  const canProceed = computed(() => {
    return requiredDependenciesMissing.value.length === 0
  })

  const checkSummary = computed(() => {
    const states = Array.from(dependencyStates.values())
    return {
      total: states.length,
      available: states.filter(s => s.status === 'available').length,
      missing: states.filter(s => s.status === 'missing').length,
      error: states.filter(s => s.status === 'error').length,
      checking: states.filter(s => s.status === 'checking').length
    }
  })

  // 检查所有依赖
  const checkAllDependencies = async () => {
    if (isChecking.value) return

    try {
      isChecking.value = true
      checkProgress.value = 0

      const dependencies = requiredDependencies
      const total = dependencies.length

      for (let i = 0; i < dependencies.length; i++) {
        const depId = dependencies[i]
        await checkSingleDependency(depId)
        checkProgress.value = ((i + 1) / total) * 100
      }

      // 记录检查历史
      const results = new Map<string, DependencyResult>()
      dependencyStates.forEach((state, id) => {
        if (state.result) {
          results.set(id, state.result)
        }
      })

      checkHistory.value.push({
        timestamp: new Date(),
        results
      })

      // 限制历史记录数量
      if (checkHistory.value.length > 10) {
        checkHistory.value = checkHistory.value.slice(-5)
      }

    } finally {
      isChecking.value = false
    }
  }

  // 检查单个依赖
  const checkSingleDependency = async (dependencyId: string) => {
    const state = dependencyStates.get(dependencyId)
    if (!state) return

    try {
      state.status = 'checking'
      
      const result = await dependencyManager.checkDependency(dependencyId, config.timeout)
      
      state.result = result
      state.lastChecked = new Date()
      state.status = result.available ? 'available' : 'missing'

      if (!result.available && result.error) {
        state.status = 'error'
      }

    } catch (error) {
      state.status = 'error'
      state.result = {
        available: false,
        error: error instanceof Error ? error.message : String(error)
      }
    }
  }

  // 解决依赖问题
  const resolveDependency = async (dependencyId: string) => {
    const state = dependencyStates.get(dependencyId)
    if (!state) return false

    try {
      const resolved = await dependencyManager.resolveDependency(dependencyId)
      
      if (resolved) {
        // 重新检查依赖
        await checkSingleDependency(dependencyId)
        ElMessage.success(`依赖 ${state.name} 已解决`)
        return true
      } else {
        ElMessage.error(`无法解决依赖 ${state.name}`)
        return false
      }
    } catch (error) {
      ElMessage.error(`解决依赖失败: ${error}`)
      return false
    }
  }

  // 自动解决所有可解决的依赖
  const autoResolveIssues = async () => {
    const missingDependencies = Array.from(dependencyStates.values())
      .filter(state => state.status === 'missing' || state.status === 'error')

    for (const state of missingDependencies) {
      const dependency = dependencyManager.get(state.id)
      if (dependency?.resolveFunction) {
        await resolveDependency(state.id)
      }
    }
  }

  // 获取依赖建议
  const getDependencySuggestions = (dependencyId: string): string[] => {
    const state = dependencyStates.get(dependencyId)
    if (!state?.result) return []

    const suggestions = state.result.suggestions || []
    const dependency = dependencyManager.get(dependencyId)

    // 添加基于依赖类型的通用建议
    if (dependency) {
      switch (dependency.type) {
        case 'data':
          if (!state.result.available) {
            suggestions.push('检查数据源连接', '确认数据格式正确')
          }
          break
        case 'service':
          if (!state.result.available) {
            suggestions.push('检查网络连接', '确认服务状态')
          }
          break
        case 'permission':
          if (!state.result.available) {
            suggestions.push('联系管理员获取权限', '检查用户角色设置')
          }
          break
        case 'config':
          if (!state.result.available) {
            suggestions.push('检查配置参数', '使用默认配置')
          }
          break
      }
    }

    return suggestions
  }

  // 导航到依赖页面
  const navigateToDependency = async (dependencyId: string) => {
    const dependency = dependencyManager.get(dependencyId)
    if (!dependency) return

    // 根据依赖类型导航到相应页面
    switch (dependency.type) {
      case 'data':
        if (dependencyId === 'factors_data') {
          await router.push('/factors')
        }
        break
      case 'resource':
        if (dependencyId === 'model_trained') {
          await router.push('/training')
        }
        break
      case 'config':
        ElMessage.info('请在当前页面完成配置')
        break
      default:
        ElMessage.info('请检查系统设置')
    }
  }

  // 显示依赖详情
  const showDependencyDetails = (dependencyId: string) => {
    const dependency = dependencyManager.get(dependencyId)
    const state = dependencyStates.get(dependencyId)
    
    if (!dependency || !state) return

    const content = `
      <div>
        <h4>${dependency.name}</h4>
        <p><strong>类型:</strong> ${dependency.type}</p>
        <p><strong>必需:</strong> ${dependency.required ? '是' : '否'}</p>
        <p><strong>描述:</strong> ${dependency.description}</p>
        <p><strong>状态:</strong> ${state.status}</p>
        ${state.result?.error ? `<p><strong>错误:</strong> ${state.result.error}</p>` : ''}
        ${state.result?.warning ? `<p><strong>警告:</strong> ${state.result.warning}</p>` : ''}
      </div>
    `

    ElMessageBox.alert(content, '依赖详情', {
      dangerouslyUseHTMLString: true
    })
  }

  // 重新检查特定依赖
  const recheckDependency = async (dependencyId: string) => {
    await checkSingleDependency(dependencyId)
  }

  // 获取检查报告
  const getCheckReport = () => {
    const report = {
      timestamp: new Date(),
      route: route.path,
      summary: checkSummary.value,
      details: Object.fromEntries(
        Array.from(dependencyStates.entries()).map(([id, state]) => [
          id,
          {
            name: state.name,
            status: state.status,
            result: state.result,
            lastChecked: state.lastChecked
          }
        ])
      )
    }

    return JSON.stringify(report, null, 2)
  }

  // 重置检查状态
  const resetCheck = () => {
    dependencyStates.forEach(state => {
      state.status = 'pending'
      state.result = undefined
      state.lastChecked = undefined
      state.retryCount = 0
    })
    checkProgress.value = 0
  }

  // 初始化
  initializeDependencyStates()

  // 自动检查
  if (config.autoCheck && requiredDependencies.length > 0) {
    checkAllDependencies()
  }

  return {
    // 状态
    isChecking,
    checkProgress,
    dependencyStates,
    checkHistory,
    config,

    // 计算属性
    allDependenciesAvailable,
    requiredDependenciesMissing,
    canProceed,
    checkSummary,

    // 方法
    checkAllDependencies,
    checkSingleDependency,
    resolveDependency,
    autoResolveIssues,
    getDependencySuggestions,
    navigateToDependency,
    showDependencyDetails,
    recheckDependency,
    getCheckReport,
    resetCheck,

    // 管理器方法
    registerDependency: (dep: Dependency) => dependencyManager.register(dep),
    removeDependency: (id: string) => dependencyManager.remove(id)
  }
}

// 导出管理器实例
export { dependencyManager }

// 类型导出
export type { Dependency, DependencyResult, CheckConfig, DependencyState }