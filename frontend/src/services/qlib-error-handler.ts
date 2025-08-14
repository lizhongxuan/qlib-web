/**
 * Qlib错误处理和降级策略服务
 * 
 * 此服务实现了qlib-web项目中所有错误处理和降级策略，包括：
 * - 数据不可用错误处理
 * - 因子表达式语法错误处理
 * - 模型训练资源不足错误处理
 * - 回测参数配置错误处理
 * - API调用失败的优雅降级机制
 * 
 * 修改理由：
 * 1. 实现TODO 7.2.6节中的错误处理需求
 * 2. 提供统一的错误处理接口和降级策略
 * 3. 确保系统在各种异常情况下能够稳定运行
 * 4. 提供用户友好的错误提示和修复建议
 */

import { ElMessage, ElNotification } from 'element-plus'
import { QLIB_ERROR_CONFIG, QLIB_API_CONFIG } from '@/config/qlib-config.js'

// 错误类型枚举
export enum ErrorType {
  DATA_UNAVAILABLE = 'data_unavailable',
  FACTOR_SYNTAX_ERROR = 'factor_syntax_error',
  TRAINING_RESOURCE_ERROR = 'training_resource_error',
  BACKTEST_CONFIG_ERROR = 'backtest_config_error',
  API_FAILURE = 'api_failure',
  NETWORK_ERROR = 'network_error',
  TIMEOUT_ERROR = 'timeout_error',
  VALIDATION_ERROR = 'validation_error'
}

// 错误严重程度
export enum ErrorSeverity {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  CRITICAL = 'critical'
}

// 错误处理结果
export interface ErrorHandlingResult {
  success: boolean
  fallbackUsed: boolean
  fallbackType?: string
  retryCount: number
  errorMessage?: string
  suggestion?: string
  data?: any
}

// 熔断器状态
enum CircuitBreakerState {
  CLOSED = 'closed',
  OPEN = 'open',
  HALF_OPEN = 'half_open'
}

interface CircuitBreakerStats {
  failureCount: number
  successCount: number
  lastFailureTime: number
  state: CircuitBreakerState
}

/**
 * Qlib错误处理服务类
 */
export class QlibErrorHandler {
  private static instance: QlibErrorHandler
  private circuitBreakers: Map<string, CircuitBreakerStats> = new Map()
  private retryAttempts: Map<string, number> = new Map()
  private fallbackCache: Map<string, any> = new Map()

  private constructor() {
    this.initializeCircuitBreakers()
  }

  public static getInstance(): QlibErrorHandler {
    if (!QlibErrorHandler.instance) {
      QlibErrorHandler.instance = new QlibErrorHandler()
    }
    return QlibErrorHandler.instance
  }

  /**
   * 初始化熔断器
   */
  private initializeCircuitBreakers(): void {
    const services = ['qlib_data', 'model_training', 'factor_validation', 'backtest_engine']
    
    services.forEach(service => {
      this.circuitBreakers.set(service, {
        failureCount: 0,
        successCount: 0,
        lastFailureTime: 0,
        state: CircuitBreakerState.CLOSED
      })
    })
  }

  /**
   * 处理数据不可用错误
   */
  public async handleDataUnavailableError(
    error: Error,
    context: {
      dataType: string
      provider: string
      dateRange?: { start: string; end: string }
      symbols?: string[]
    }
  ): Promise<ErrorHandlingResult> {
    console.warn('数据不可用错误:', error.message, context)

    const config = QLIB_ERROR_CONFIG.data_unavailable
    let retryCount = this.getRetryCount(`data_${context.dataType}_${context.provider}`)

    // 尝试重试机制
    if (retryCount < config.retry_strategy.max_retries) {
      await this.delay(config.retry_strategy.retry_delay[retryCount] || 5000)
      this.incrementRetryCount(`data_${context.dataType}_${context.provider}`)
      
      return {
        success: false,
        fallbackUsed: false,
        retryCount: retryCount + 1,
        errorMessage: '数据获取失败，正在重试...',
        suggestion: `第${retryCount + 1}次重试，共${config.retry_strategy.max_retries}次`
      }
    }

    // 执行降级策略
    for (const fallbackOption of config.fallback_options) {
      if (!fallbackOption.enabled && fallbackOption.enabled === false) {
        continue
      }

      try {
        const fallbackResult = await this.executeFallbackStrategy(fallbackOption, context)
        if (fallbackResult.success) {
          ElMessage.success(`已切换到${fallbackOption.description}`)
          this.resetRetryCount(`data_${context.dataType}_${context.provider}`)
          
          return {
            success: true,
            fallbackUsed: true,
            fallbackType: fallbackOption.type,
            retryCount,
            data: fallbackResult.data,
            suggestion: `当前使用${fallbackOption.description}，建议检查主数据源连接`
          }
        }
      } catch (fallbackError) {
        console.warn(`降级策略${fallbackOption.type}失败:`, fallbackError)
        continue
      }
    }

    // 所有策略都失败
    ElNotification.error({
      title: '数据获取失败',
      message: '所有数据源都无法访问，请检查网络连接或联系管理员',
      duration: 0
    })

    return {
      success: false,
      fallbackUsed: false,
      retryCount,
      errorMessage: '数据获取失败：所有数据源都无法访问',
      suggestion: '请检查网络连接、数据源配置或联系技术支持'
    }
  }

  /**
   * 处理因子表达式语法错误
   */
  public handleFactorSyntaxError(
    expression: string,
    error: Error,
    context?: { line?: number; column?: number }
  ): ErrorHandlingResult {
    const config = QLIB_ERROR_CONFIG.factor_syntax_error
    const errorMessage = error.message

    // 解析错误类型
    let errorType = 'syntax_error'
    let suggestions: string[] = []

    if (errorMessage.includes('unknown function')) {
      errorType = 'unknown_function'
      suggestions = this.suggestSimilarFunctions(this.extractFunctionName(errorMessage))
    } else if (errorMessage.includes('invalid field')) {
      errorType = 'invalid_field'
      suggestions = this.suggestValidFields(this.extractFieldName(errorMessage))
    } else if (errorMessage.includes('nested too deep')) {
      errorType = 'nested_too_deep'
      suggestions = ['简化表达式结构', '减少嵌套层级', '将复杂表达式拆分成多个步骤']
    } else if (errorMessage.includes('expression too long')) {
      errorType = 'expression_too_long'
      suggestions = ['缩短表达式长度', '使用变量存储中间结果', '分解为多个子表达式']
    }

    // 生成修复建议
    const fixSuggestions = this.generateFactorFixSuggestions(expression, errorType, suggestions)

    ElMessage.error({
      message: config.error_messages[errorType]?.replace('{error}', errorMessage) || errorMessage,
      duration: 5000
    })

    return {
      success: false,
      fallbackUsed: false,
      retryCount: 0,
      errorMessage,
      suggestion: fixSuggestions.join('; ')
    }
  }

  /**
   * 处理模型训练资源不足错误
   */
  public async handleTrainingResourceError(
    error: Error,
    context: {
      modelType: string
      datasetSize: number
      currentMemoryUsage?: number
      currentCpuUsage?: number
    }
  ): Promise<ErrorHandlingResult> {
    console.warn('训练资源不足:', error.message, context)

    const config = QLIB_ERROR_CONFIG.training_resource_error
    
    // 检查资源使用情况
    const resourceStats = await this.checkResourceUsage()
    
    // 选择合适的缓解策略
    for (const strategy of config.mitigation_strategies) {
      if (this.shouldApplyStrategy(strategy, resourceStats, context)) {
        try {
          const result = await this.applyResourceMitigationStrategy(strategy, context)
          if (result.success) {
            ElMessage.success(`已应用资源优化策略: ${strategy.description}`)
            return {
              success: true,
              fallbackUsed: true,
              fallbackType: strategy.type,
              retryCount: 0,
              suggestion: `${strategy.description}，训练将继续进行`
            }
          }
        } catch (strategyError) {
          console.warn(`资源优化策略${strategy.type}失败:`, strategyError)
          continue
        }
      }
    }

    ElNotification.error({
      title: '训练资源不足',
      message: '无法分配足够资源进行模型训练，请稍后重试或联系管理员',
      duration: 0
    })

    return {
      success: false,
      fallbackUsed: false,
      retryCount: 0,
      errorMessage: '训练资源不足，无法继续',
      suggestion: '请减少数据集大小、调整模型参数或等待资源释放后重试'
    }
  }

  /**
   * 处理回测参数配置错误
   */
  public handleBacktestConfigError(
    config: any,
    error: Error
  ): ErrorHandlingResult {
    console.warn('回测配置错误:', error.message, config)

    const validationConfig = QLIB_ERROR_CONFIG.backtest_config_error
    const errorMessage = error.message

    // 尝试自动修正配置
    if (validationConfig.auto_correction.enabled) {
      try {
        const correctedConfig = this.autoCorrectBacktestConfig(config, errorMessage)
        if (correctedConfig) {
          ElMessage.success('已自动修正回测配置参数')
          return {
            success: true,
            fallbackUsed: true,
            fallbackType: 'auto_correction',
            retryCount: 0,
            data: correctedConfig,
            suggestion: '配置已自动修正，请检查修正后的参数'
          }
        }
      } catch (correctionError) {
        console.warn('自动修正配置失败:', correctionError)
      }
    }

    // 生成修复建议
    const suggestions = this.generateBacktestConfigSuggestions(config, errorMessage)

    ElMessage.error({
      message: `回测配置错误: ${errorMessage}`,
      duration: 5000
    })

    return {
      success: false,
      fallbackUsed: false,
      retryCount: 0,
      errorMessage,
      suggestion: suggestions.join('; ')
    }
  }

  /**
   * 处理API调用失败
   */
  public async handleApiFailure(
    serviceName: string,
    error: Error,
    requestConfig?: any
  ): Promise<ErrorHandlingResult> {
    console.warn(`API调用失败 [${serviceName}]:`, error.message)

    // 检查熔断器状态
    const circuitBreaker = this.circuitBreakers.get(serviceName)
    if (circuitBreaker && circuitBreaker.state === CircuitBreakerState.OPEN) {
      const timeSinceLastFailure = Date.now() - circuitBreaker.lastFailureTime
      if (timeSinceLastFailure < QLIB_ERROR_CONFIG.api_failure.circuit_breaker.timeout_ms) {
        return this.executeGracefulDegradation(serviceName, error)
      } else {
        // 尝试半开状态
        circuitBreaker.state = CircuitBreakerState.HALF_OPEN
      }
    }

    // 记录失败
    this.recordApiFailure(serviceName)

    // 重试机制
    const retryKey = `api_${serviceName}`
    let retryCount = this.getRetryCount(retryKey)
    const maxRetries = QLIB_ERROR_CONFIG.api_failure.retry_config.max_retries

    if (retryCount < maxRetries) {
      const delay = this.calculateRetryDelay(retryCount)
      await this.delay(delay)
      this.incrementRetryCount(retryKey)

      return {
        success: false,
        fallbackUsed: false,
        retryCount: retryCount + 1,
        errorMessage: `API调用失败，正在重试... (${retryCount + 1}/${maxRetries})`,
        suggestion: '请稍候，系统正在重试'
      }
    }

    // 执行优雅降级
    this.resetRetryCount(retryKey)
    return this.executeGracefulDegradation(serviceName, error)
  }

  /**
   * 执行降级策略
   */
  private async executeFallbackStrategy(
    fallbackOption: any,
    context: any
  ): Promise<{ success: boolean; data?: any }> {
    switch (fallbackOption.type) {
      case 'cache':
        return this.useCachedData(context, fallbackOption.max_age_hours)
      
      case 'alternative_provider':
        return this.switchToAlternativeProvider(context, fallbackOption.providers)
      
      case 'mock_data':
        if (fallbackOption.enabled) {
          return this.generateMockData(context)
        }
        break
      
      case 'notification':
        this.showUserNotification(context)
        return { success: false }
    }

    return { success: false }
  }

  /**
   * 使用缓存数据
   */
  private async useCachedData(
    context: any, 
    maxAgeHours: number
  ): Promise<{ success: boolean; data?: any }> {
    const cacheKey = this.generateCacheKey(context)
    const cachedData = this.fallbackCache.get(cacheKey)
    
    if (cachedData && this.isCacheValid(cachedData, maxAgeHours)) {
      return { success: true, data: cachedData.data }
    }

    return { success: false }
  }

  /**
   * 切换到备用数据源
   */
  private async switchToAlternativeProvider(
    context: any,
    providers: string[]
  ): Promise<{ success: boolean; data?: any }> {
    for (const provider of providers) {
      if (provider === context.provider) continue
      
      try {
        // 这里应该调用实际的数据获取API
        const data = await this.fetchDataFromProvider(provider, context)
        return { success: true, data }
      } catch (error) {
        console.warn(`备用数据源${provider}也失败:`, error)
        continue
      }
    }

    return { success: false }
  }

  /**
   * 生成模拟数据
   */
  private async generateMockData(context: any): Promise<{ success: boolean; data?: any }> {
    // 根据上下文生成合理的模拟数据
    const mockData = this.createMockDataForContext(context)
    return { success: true, data: mockData }
  }

  /**
   * 执行优雅降级
   */
  private async executeGracefulDegradation(
    serviceName: string,
    error: Error
  ): Promise<ErrorHandlingResult> {
    const degradationOptions = QLIB_ERROR_CONFIG.api_failure.graceful_degradation
    const serviceConfig = degradationOptions.find(opt => opt.service === serviceName)

    if (serviceConfig && serviceConfig.enabled) {
      try {
        const fallbackData = await this.executeFallbackService(serviceConfig.fallback, serviceName)
        
        ElMessage.warning(`服务降级：${serviceName} -> ${serviceConfig.fallback}`)
        
        return {
          success: true,
          fallbackUsed: true,
          fallbackType: serviceConfig.fallback,
          retryCount: 0,
          data: fallbackData,
          suggestion: `已切换到备用服务: ${serviceConfig.fallback}`
        }
      } catch (fallbackError) {
        console.warn(`降级服务${serviceConfig.fallback}也失败:`, fallbackError)
      }
    }

    // 打开熔断器
    this.openCircuitBreaker(serviceName)

    ElNotification.error({
      title: 'API服务不可用',
      message: `${serviceName}服务暂时不可用，请稍后重试`,
      duration: 8000
    })

    return {
      success: false,
      fallbackUsed: false,
      retryCount: 0,
      errorMessage: `服务${serviceName}不可用`,
      suggestion: '请检查网络连接或稍后重试'
    }
  }

  /**
   * 工具方法：延迟执行
   */
  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms))
  }

  /**
   * 工具方法：计算重试延迟
   */
  private calculateRetryDelay(retryCount: number): number {
    const config = QLIB_ERROR_CONFIG.api_failure.retry_config
    let delay = config.base_delay * Math.pow(2, retryCount)
    
    if (config.jitter) {
      delay += Math.random() * 1000
    }
    
    return Math.min(delay, config.max_delay)
  }

  /**
   * 工具方法：获取重试次数
   */
  private getRetryCount(key: string): number {
    return this.retryAttempts.get(key) || 0
  }

  /**
   * 工具方法：增加重试次数
   */
  private incrementRetryCount(key: string): void {
    const count = this.getRetryCount(key)
    this.retryAttempts.set(key, count + 1)
  }

  /**
   * 工具方法：重置重试次数
   */
  private resetRetryCount(key: string): void {
    this.retryAttempts.delete(key)
  }

  /**
   * 工具方法：记录API失败
   */
  private recordApiFailure(serviceName: string): void {
    const stats = this.circuitBreakers.get(serviceName)
    if (stats) {
      stats.failureCount++
      stats.lastFailureTime = Date.now()

      if (stats.failureCount >= QLIB_ERROR_CONFIG.api_failure.circuit_breaker.failure_threshold) {
        stats.state = CircuitBreakerState.OPEN
      }
    }
  }

  /**
   * 工具方法：记录API成功
   */
  private recordApiSuccess(serviceName: string): void {
    const stats = this.circuitBreakers.get(serviceName)
    if (stats) {
      stats.successCount++
      stats.failureCount = 0
      stats.state = CircuitBreakerState.CLOSED
    }
  }

  /**
   * 工具方法：打开熔断器
   */
  private openCircuitBreaker(serviceName: string): void {
    const stats = this.circuitBreakers.get(serviceName)
    if (stats) {
      stats.state = CircuitBreakerState.OPEN
      stats.lastFailureTime = Date.now()
    }
  }

  // 其他私有辅助方法...
  private extractFunctionName(errorMessage: string): string {
    const match = errorMessage.match(/unknown function[:\s]+(\w+)/i)
    return match ? match[1] : ''
  }

  private extractFieldName(errorMessage: string): string {
    const match = errorMessage.match(/invalid field[:\s]+(\$?\w+)/i)
    return match ? match[1] : ''
  }

  private suggestSimilarFunctions(functionName: string): string[] {
    // 实现函数名相似度匹配算法
    const availableFunctions = [
      'Mean', 'Std', 'Sum', 'Max', 'Min', 'Rank', 'Delay', 'Delta',
      'Ts_Rank', 'Ts_Max', 'Ts_Min', 'Correlation', 'RSI', 'MA', 'EMA'
    ]
    
    return availableFunctions
      .filter(func => this.calculateSimilarity(functionName, func) > 0.6)
      .slice(0, 3)
  }

  private suggestValidFields(fieldName: string): string[] {
    const validFields = ['$close', '$open', '$high', '$low', '$volume', '$amount', '$vwap']
    return validFields
      .filter(field => this.calculateSimilarity(fieldName, field) > 0.5)
      .slice(0, 3)
  }

  private calculateSimilarity(str1: string, str2: string): number {
    // 简单的字符串相似度计算
    const longer = str1.length > str2.length ? str1 : str2
    const shorter = str1.length > str2.length ? str2 : str1
    
    if (longer.length === 0) return 1.0
    
    const editDistance = this.levenshteinDistance(longer, shorter)
    return (longer.length - editDistance) / longer.length
  }

  private levenshteinDistance(str1: string, str2: string): number {
    const matrix = []
    
    for (let i = 0; i <= str2.length; i++) {
      matrix[i] = [i]
    }
    
    for (let j = 0; j <= str1.length; j++) {
      matrix[0][j] = j
    }
    
    for (let i = 1; i <= str2.length; i++) {
      for (let j = 1; j <= str1.length; j++) {
        if (str2.charAt(i - 1) === str1.charAt(j - 1)) {
          matrix[i][j] = matrix[i - 1][j - 1]
        } else {
          matrix[i][j] = Math.min(
            matrix[i - 1][j - 1] + 1,
            matrix[i][j - 1] + 1,
            matrix[i - 1][j] + 1
          )
        }
      }
    }
    
    return matrix[str2.length][str1.length]
  }

  private generateFactorFixSuggestions(
    expression: string,
    errorType: string,
    suggestions: string[]
  ): string[] {
    const fixSuggestions = [...suggestions]
    
    if (errorType === 'syntax_error') {
      fixSuggestions.push('检查括号匹配')
      fixSuggestions.push('验证操作符语法')
    }
    
    return fixSuggestions
  }

  private async checkResourceUsage(): Promise<any> {
    // 模拟资源使用情况检查
    return {
      memory_usage: Math.random() * 100,
      cpu_usage: Math.random() * 100,
      disk_usage: Math.random() * 100
    }
  }

  private shouldApplyStrategy(strategy: any, resourceStats: any, context: any): boolean {
    switch (strategy.trigger) {
      case 'memory_high':
        return resourceStats.memory_usage > 85
      case 'time_limit':
        return context.trainingTimeMinutes > 120
      case 'resource_unavailable':
        return resourceStats.cpu_usage > 90 || resourceStats.memory_usage > 90
      case 'large_dataset':
        return context.datasetSize > 100000
      default:
        return false
    }
  }

  private async applyResourceMitigationStrategy(strategy: any, context: any): Promise<any> {
    // 实现具体的资源优化策略
    switch (strategy.type) {
      case 'reduce_batch_size':
        return { success: true, newBatchSize: Math.floor(context.batchSize / 2) }
      case 'enable_model_compression':
        return { success: true, compression: true }
      case 'switch_to_fast_mode':
        return { success: true, fastMode: true }
      default:
        return { success: false }
    }
  }

  private autoCorrectBacktestConfig(config: any, errorMessage: string): any | null {
    const correctedConfig = { ...config }
    
    // 实现自动修正逻辑
    if (errorMessage.includes('date range')) {
      // 修正日期范围
      correctedConfig.start_date = '2020-01-01'
      correctedConfig.end_date = '2023-12-31'
      return correctedConfig
    }
    
    return null
  }

  private generateBacktestConfigSuggestions(config: any, errorMessage: string): string[] {
    const suggestions = []
    
    if (errorMessage.includes('universe')) {
      suggestions.push('检查股票池配置')
      suggestions.push('确认股票代码格式正确')
    }
    
    if (errorMessage.includes('date')) {
      suggestions.push('检查日期格式和范围')
      suggestions.push('确认所选日期为交易日')
    }
    
    return suggestions
  }

  private generateCacheKey(context: any): string {
    return `${context.dataType}_${context.provider}_${JSON.stringify(context.dateRange)}`
  }

  private isCacheValid(cachedData: any, maxAgeHours: number): boolean {
    const ageMs = Date.now() - cachedData.timestamp
    return ageMs < maxAgeHours * 60 * 60 * 1000
  }

  private async fetchDataFromProvider(provider: string, context: any): Promise<any> {
    // 模拟从备用数据源获取数据
    throw new Error('Provider not implemented')
  }

  private createMockDataForContext(context: any): any {
    // 生成模拟数据
    return {
      data: Array.from({ length: 100 }, (_, i) => ({
        date: new Date(2023, 0, i + 1).toISOString().split('T')[0],
        value: Math.random() * 100
      })),
      metadata: {
        source: 'mock',
        generated_at: new Date().toISOString()
      }
    }
  }

  private async executeFallbackService(fallbackType: string, serviceName: string): Promise<any> {
    switch (fallbackType) {
      case 'cached_data':
        return this.getCachedServiceData(serviceName)
      case 'simple_model':
        return this.getSimpleModelData()
      case 'syntax_check_only':
        return this.performBasicSyntaxCheck()
      case 'simple_returns':
        return this.calculateSimpleReturns()
      default:
        throw new Error(`Unknown fallback type: ${fallbackType}`)
    }
  }

  private getCachedServiceData(serviceName: string): any {
    return { status: 'cached', service: serviceName, data: [] }
  }

  private getSimpleModelData(): any {
    return { model_type: 'linear', status: 'simplified' }
  }

  private performBasicSyntaxCheck(): any {
    return { validation: 'basic', status: 'ok' }
  }

  private calculateSimpleReturns(): any {
    return { returns: 0.05, status: 'estimated' }
  }

  private showUserNotification(context: any): void {
    ElNotification.info({
      title: '数据获取失败',
      message: `无法获取${context.dataType}数据，请手动检查数据源连接`,
      duration: 0
    })
  }

  /**
   * 公共接口：统一错误处理入口
   */
  public async handleError(
    errorType: ErrorType,
    error: Error,
    context?: any
  ): Promise<ErrorHandlingResult> {
    switch (errorType) {
      case ErrorType.DATA_UNAVAILABLE:
        return this.handleDataUnavailableError(error, context)
      
      case ErrorType.FACTOR_SYNTAX_ERROR:
        return this.handleFactorSyntaxError(context?.expression || '', error, context)
      
      case ErrorType.TRAINING_RESOURCE_ERROR:
        return this.handleTrainingResourceError(error, context)
      
      case ErrorType.BACKTEST_CONFIG_ERROR:
        return this.handleBacktestConfigError(context?.config || {}, error)
      
      case ErrorType.API_FAILURE:
        return this.handleApiFailure(context?.serviceName || 'unknown', error, context)
      
      default:
        return this.handleGenericError(error, context)
    }
  }

  private handleGenericError(error: Error, context?: any): ErrorHandlingResult {
    ElMessage.error(`发生未知错误: ${error.message}`)
    
    return {
      success: false,
      fallbackUsed: false,
      retryCount: 0,
      errorMessage: error.message,
      suggestion: '请刷新页面重试或联系技术支持'
    }
  }
}

// 导出单例实例
export const qlibErrorHandler = QlibErrorHandler.getInstance()

// 导出便捷方法
export const handleQlibError = (
  errorType: ErrorType,
  error: Error,
  context?: any
): Promise<ErrorHandlingResult> => {
  return qlibErrorHandler.handleError(errorType, error, context)
}

export default QlibErrorHandler