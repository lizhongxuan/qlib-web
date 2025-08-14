/**
 * Qlib因子表达式验证服务
 * 
 * 此服务提供完整的qlib因子表达式语法验证功能，包括：
 * - 实时语法检查和错误提示
 * - 语义验证和数据可用性检查
 * - 智能修复建议和自动补全
 * - 性能评估和优化建议
 * 
 * 修改理由：
 * 1. 实现TODO 7.2.6节中因子表达式语法错误处理需求
 * 2. 提供实时的语法验证和智能提示
 * 3. 确保用户输入的因子表达式符合qlib语法规范
 * 4. 提供友好的错误修复建议和自动补全功能
 */

import { QLIB_FACTOR_CONFIG, QLIB_ERROR_CONFIG } from '@/config/qlib-config.js'
import { ElMessage } from 'element-plus'

// 验证结果接口
export interface FactorValidationResult {
  isValid: boolean
  errors: ValidationError[]
  warnings: ValidationWarning[]
  suggestions: string[]
  complexity: ComplexityAnalysis
  performance: PerformanceEstimate
}

export interface ValidationError {
  type: string
  message: string
  position?: { line: number; column: number; length: number }
  severity: 'error' | 'warning'
  fixSuggestions: string[]
}

export interface ValidationWarning {
  type: string
  message: string
  suggestion: string
  impact: 'low' | 'medium' | 'high'
}

export interface ComplexityAnalysis {
  score: number // 1-10, 10为最复杂
  factors: {
    nested_depth: number
    function_count: number
    data_field_count: number
    time_window_span: number
  }
  optimization_suggestions: string[]
}

export interface PerformanceEstimate {
  computation_cost: 'low' | 'medium' | 'high' | 'very_high'
  memory_usage: number // MB
  estimated_time: number // seconds
  bottlenecks: string[]
  optimizations: string[]
}

// 语法元素类型
enum TokenType {
  NUMBER = 'number',
  OPERATOR = 'operator',
  FUNCTION = 'function',
  DATA_FIELD = 'data_field',
  IDENTIFIER = 'identifier',
  PARENTHESIS = 'parenthesis',
  COMMA = 'comma',
  STRING = 'string'
}

interface Token {
  type: TokenType
  value: string
  position: { start: number; end: number }
}

/**
 * Qlib因子表达式验证器
 */
export class QlibFactorValidator {
  private static instance: QlibFactorValidator
  private validationCache: Map<string, FactorValidationResult> = new Map()
  private syntaxRules: any
  private functions: Set<string>
  private dataFields: Set<string>
  private operators: Set<string>

  private constructor() {
    this.initializeValidationRules()
  }

  public static getInstance(): QlibFactorValidator {
    if (!QlibFactorValidator.instance) {
      QlibFactorValidator.instance = new QlibFactorValidator()
    }
    return QlibFactorValidator.instance
  }

  /**
   * 初始化验证规则
   */
  private initializeValidationRules(): void {
    const config = QLIB_FACTOR_CONFIG.expression_syntax

    // 初始化函数集合
    this.functions = new Set([
      ...config.functions.math,
      ...config.functions.time_series,
      ...config.functions.cross_sectional,
      ...config.functions.technical,
      ...config.functions.statistical
    ])

    // 初始化数据字段集合
    this.dataFields = new Set([
      ...config.data_fields.price,
      ...config.data_fields.volume,
      ...config.data_fields.market_data,
      ...config.data_fields.derived
    ])

    // 初始化操作符集合
    this.operators = new Set([
      ...config.operators.arithmetic,
      ...config.operators.comparison,
      ...config.operators.logical
    ])

    // 语法规则
    this.syntaxRules = config.validation_rules
  }

  /**
   * 验证因子表达式
   */
  public async validateExpression(expression: string): Promise<FactorValidationResult> {
    // 检查缓存
    const cacheKey = this.generateCacheKey(expression)
    const cached = this.validationCache.get(cacheKey)
    if (cached) {
      return cached
    }

    const result = await this.performValidation(expression)
    
    // 缓存结果（最多缓存100个）
    if (this.validationCache.size >= 100) {
      const firstKey = this.validationCache.keys().next().value
      this.validationCache.delete(firstKey)
    }
    this.validationCache.set(cacheKey, result)

    return result
  }

  /**
   * 执行完整验证
   */
  private async performValidation(expression: string): Promise<FactorValidationResult> {
    const errors: ValidationError[] = []
    const warnings: ValidationWarning[] = []
    const suggestions: string[] = []

    try {
      // 1. 预处理检查
      const preprocessResult = this.preprocessExpression(expression)
      if (!preprocessResult.success) {
        errors.push(...preprocessResult.errors)
      }

      // 2. 词法分析
      const tokens = this.tokenize(expression)
      const lexicalErrors = this.validateTokens(tokens)
      errors.push(...lexicalErrors)

      // 3. 语法分析
      if (errors.length === 0) {
        const syntaxErrors = await this.validateSyntax(tokens)
        errors.push(...syntaxErrors)
      }

      // 4. 语义分析
      if (errors.length === 0) {
        const semanticResult = await this.validateSemantics(expression, tokens)
        errors.push(...semanticResult.errors)
        warnings.push(...semanticResult.warnings)
      }

      // 5. 复杂度分析
      const complexity = this.analyzeComplexity(expression, tokens)

      // 6. 性能评估
      const performance = this.estimatePerformance(expression, tokens, complexity)

      // 7. 生成建议
      suggestions.push(...this.generateSuggestions(errors, warnings, complexity, performance))

      return {
        isValid: errors.filter(e => e.severity === 'error').length === 0,
        errors,
        warnings,
        suggestions,
        complexity,
        performance
      }
    } catch (error) {
      console.error('因子验证过程中发生错误:', error)
      
      return {
        isValid: false,
        errors: [{
          type: 'validation_error',
          message: '验证过程中发生内部错误',
          severity: 'error',
          fixSuggestions: ['请检查表达式格式', '联系技术支持']
        }],
        warnings: [],
        suggestions: ['请检查表达式是否包含特殊字符'],
        complexity: { score: 0, factors: { nested_depth: 0, function_count: 0, data_field_count: 0, time_window_span: 0 }, optimization_suggestions: [] },
        performance: { computation_cost: 'low', memory_usage: 0, estimated_time: 0, bottlenecks: [], optimizations: [] }
      }
    }
  }

  /**
   * 预处理表达式
   */
  private preprocessExpression(expression: string): { success: boolean; errors: ValidationError[] } {
    const errors: ValidationError[] = []

    // 检查表达式长度
    if (expression.length > this.syntaxRules.max_expression_length) {
      errors.push({
        type: 'expression_too_long',
        message: `表达式长度超过限制（最大${this.syntaxRules.max_expression_length}字符）`,
        severity: 'error',
        fixSuggestions: ['简化表达式', '拆分为多个子表达式', '使用变量存储中间结果']
      })
    }

    // 检查空表达式
    if (!expression.trim()) {
      errors.push({
        type: 'empty_expression',
        message: '表达式不能为空',
        severity: 'error',
        fixSuggestions: ['请输入有效的因子表达式']
      })
    }

    // 检查括号匹配
    const parenthesesResult = this.validateParentheses(expression)
    if (!parenthesesResult.isValid) {
      errors.push({
        type: 'mismatched_parentheses',
        message: parenthesesResult.message,
        position: parenthesesResult.position,
        severity: 'error',
        fixSuggestions: ['检查括号是否配对', '确认括号类型正确']
      })
    }

    // 检查基本字符
    const invalidChars = this.findInvalidCharacters(expression)
    if (invalidChars.length > 0) {
      errors.push({
        type: 'invalid_characters',
        message: `包含无效字符: ${invalidChars.join(', ')}`,
        severity: 'error',
        fixSuggestions: ['移除无效字符', '使用标准ASCII字符']
      })
    }

    return { success: errors.length === 0, errors }
  }

  /**
   * 词法分析
   */
  private tokenize(expression: string): Token[] {
    const tokens: Token[] = []
    let i = 0

    while (i < expression.length) {
      const char = expression[i]

      // 跳过空白字符
      if (/\s/.test(char)) {
        i++
        continue
      }

      // 数字
      if (/\d/.test(char) || (char === '.' && /\d/.test(expression[i + 1]))) {
        const start = i
        while (i < expression.length && /[\d.]/.test(expression[i])) {
          i++
        }
        tokens.push({
          type: TokenType.NUMBER,
          value: expression.slice(start, i),
          position: { start, end: i }
        })
        continue
      }

      // 数据字段（以$开头）
      if (char === '$') {
        const start = i
        i++ // 跳过$
        while (i < expression.length && /\w/.test(expression[i])) {
          i++
        }
        tokens.push({
          type: TokenType.DATA_FIELD,
          value: expression.slice(start, i),
          position: { start, end: i }
        })
        continue
      }

      // 标识符或函数
      if (/[a-zA-Z_]/.test(char)) {
        const start = i
        while (i < expression.length && /\w/.test(expression[i])) {
          i++
        }
        const value = expression.slice(start, i)
        
        // 检查下一个字符是否为'('来判断是否为函数
        const isFunction = i < expression.length && expression[i] === '('
        
        tokens.push({
          type: isFunction ? TokenType.FUNCTION : TokenType.IDENTIFIER,
          value,
          position: { start, end: i }
        })
        continue
      }

      // 操作符
      if (this.isOperator(char)) {
        const start = i
        let operator = char
        
        // 检查双字符操作符
        if (i + 1 < expression.length) {
          const twoChar = expression.slice(i, i + 2)
          if (['>=', '<=', '==', '!=', '**'].includes(twoChar)) {
            operator = twoChar
            i++
          }
        }
        
        i++
        tokens.push({
          type: TokenType.OPERATOR,
          value: operator,
          position: { start, end: i }
        })
        continue
      }

      // 括号
      if (['(', ')'].includes(char)) {
        tokens.push({
          type: TokenType.PARENTHESIS,
          value: char,
          position: { start: i, end: i + 1 }
        })
        i++
        continue
      }

      // 逗号
      if (char === ',') {
        tokens.push({
          type: TokenType.COMMA,
          value: char,
          position: { start: i, end: i + 1 }
        })
        i++
        continue
      }

      // 字符串
      if (['"', "'"].includes(char)) {
        const quote = char
        const start = i
        i++ // 跳过开始引号
        
        while (i < expression.length && expression[i] !== quote) {
          if (expression[i] === '\\') i++ // 跳过转义字符
          i++
        }
        
        if (i < expression.length) i++ // 跳过结束引号
        
        tokens.push({
          type: TokenType.STRING,
          value: expression.slice(start, i),
          position: { start, end: i }
        })
        continue
      }

      // 未知字符
      i++
    }

    return tokens
  }

  /**
   * 验证令牌
   */
  private validateTokens(tokens: Token[]): ValidationError[] {
    const errors: ValidationError[] = []

    for (const token of tokens) {
      switch (token.type) {
        case TokenType.FUNCTION:
          if (!this.functions.has(token.value)) {
            const suggestions = this.findSimilarFunctions(token.value)
            errors.push({
              type: 'unknown_function',
              message: `未知函数: ${token.value}`,
              position: { line: 1, column: token.position.start, length: token.value.length },
              severity: 'error',
              fixSuggestions: suggestions.length > 0 
                ? [`建议使用: ${suggestions.join(', ')}`]
                : ['检查函数名拼写', '查看可用函数列表']
            })
          }
          break

        case TokenType.DATA_FIELD:
          if (!this.dataFields.has(token.value)) {
            const suggestions = this.findSimilarFields(token.value)
            errors.push({
              type: 'unknown_field',
              message: `未知数据字段: ${token.value}`,
              position: { line: 1, column: token.position.start, length: token.value.length },
              severity: 'error',
              fixSuggestions: suggestions.length > 0
                ? [`建议使用: ${suggestions.join(', ')}`]
                : ['检查字段名拼写', '查看可用数据字段']
            })
          }
          break

        case TokenType.OPERATOR:
          if (!this.operators.has(token.value)) {
            errors.push({
              type: 'unknown_operator',
              message: `未知操作符: ${token.value}`,
              position: { line: 1, column: token.position.start, length: token.value.length },
              severity: 'error',
              fixSuggestions: ['检查操作符拼写', '使用标准操作符']
            })
          }
          break

        case TokenType.NUMBER:
          if (!this.isValidNumber(token.value)) {
            errors.push({
              type: 'invalid_number',
              message: `无效数字格式: ${token.value}`,
              position: { line: 1, column: token.position.start, length: token.value.length },
              severity: 'error',
              fixSuggestions: ['检查数字格式', '避免多个小数点']
            })
          }
          break
      }
    }

    return errors
  }

  /**
   * 语法验证
   */
  private async validateSyntax(tokens: Token[]): Promise<ValidationError[]> {
    const errors: ValidationError[] = []

    // 检查表达式结构
    const structureErrors = this.validateExpressionStructure(tokens)
    errors.push(...structureErrors)

    // 检查函数调用语法
    const functionErrors = this.validateFunctionCalls(tokens)
    errors.push(...functionErrors)

    // 检查操作符使用
    const operatorErrors = this.validateOperatorUsage(tokens)
    errors.push(...operatorErrors)

    return errors
  }

  /**
   * 语义验证
   */
  private async validateSemantics(expression: string, tokens: Token[]): Promise<{
    errors: ValidationError[]
    warnings: ValidationWarning[]
  }> {
    const errors: ValidationError[] = []
    const warnings: ValidationWarning[] = []

    // 检查数据可用性
    try {
      const dataCheckResult = await this.checkDataAvailability(tokens)
      errors.push(...dataCheckResult.errors)
      warnings.push(...dataCheckResult.warnings)
    } catch (error) {
      console.warn('数据可用性检查失败:', error)
      warnings.push({
        type: 'data_check_failed',
        message: '无法验证数据可用性',
        suggestion: '请确保数据源连接正常',
        impact: 'medium'
      })
    }

    // 检查函数兼容性
    const compatibilityResult = this.checkFunctionCompatibility(tokens)
    warnings.push(...compatibilityResult)

    // 检查性能影响
    const performanceWarnings = this.checkPerformanceImpact(expression, tokens)
    warnings.push(...performanceWarnings)

    return { errors, warnings }
  }

  /**
   * 复杂度分析
   */
  private analyzeComplexity(expression: string, tokens: Token[]): ComplexityAnalysis {
    const factors = {
      nested_depth: this.calculateNestedDepth(tokens),
      function_count: tokens.filter(t => t.type === TokenType.FUNCTION).length,
      data_field_count: tokens.filter(t => t.type === TokenType.DATA_FIELD).length,
      time_window_span: this.calculateTimeWindowSpan(tokens)
    }

    // 计算复杂度得分 (1-10)
    let score = 1
    score += Math.min(factors.nested_depth * 0.5, 2)
    score += Math.min(factors.function_count * 0.2, 2)
    score += Math.min(factors.data_field_count * 0.1, 1)
    score += Math.min(factors.time_window_span / 50, 2)
    score = Math.min(Math.ceil(score), 10)

    const optimization_suggestions: string[] = []
    if (factors.nested_depth > 5) {
      optimization_suggestions.push('考虑简化嵌套结构')
    }
    if (factors.function_count > 10) {
      optimization_suggestions.push('减少函数调用次数')
    }
    if (factors.time_window_span > 252) {
      optimization_suggestions.push('优化时间窗口大小')
    }

    return { score, factors, optimization_suggestions }
  }

  /**
   * 性能评估
   */
  private estimatePerformance(
    expression: string, 
    tokens: Token[], 
    complexity: ComplexityAnalysis
  ): PerformanceEstimate {
    // 基于复杂度计算性能估计
    let computation_cost: 'low' | 'medium' | 'high' | 'very_high'
    let memory_usage = 0 // MB
    let estimated_time = 0 // seconds

    if (complexity.score <= 3) {
      computation_cost = 'low'
      memory_usage = 50 + complexity.factors.data_field_count * 10
      estimated_time = 1 + complexity.factors.function_count * 0.1
    } else if (complexity.score <= 6) {
      computation_cost = 'medium'
      memory_usage = 100 + complexity.factors.data_field_count * 20
      estimated_time = 5 + complexity.factors.function_count * 0.5
    } else if (complexity.score <= 8) {
      computation_cost = 'high'
      memory_usage = 200 + complexity.factors.data_field_count * 50
      estimated_time = 15 + complexity.factors.function_count * 1
    } else {
      computation_cost = 'very_high'
      memory_usage = 500 + complexity.factors.data_field_count * 100
      estimated_time = 60 + complexity.factors.function_count * 5
    }

    const bottlenecks: string[] = []
    const optimizations: string[] = []

    // 识别性能瓶颈
    if (complexity.factors.nested_depth > 5) {
      bottlenecks.push('深度嵌套计算')
      optimizations.push('简化嵌套结构')
    }

    const technicalFunctions = tokens.filter(t => 
      t.type === TokenType.FUNCTION && 
      QLIB_FACTOR_CONFIG.expression_syntax.functions.technical.includes(t.value)
    )

    if (technicalFunctions.length > 3) {
      bottlenecks.push('大量技术指标计算')
      optimizations.push('减少技术指标使用或使用缓存')
    }

    if (complexity.factors.time_window_span > 252) {
      bottlenecks.push('长时间窗口计算')
      optimizations.push('优化时间窗口或使用滚动计算')
    }

    return {
      computation_cost,
      memory_usage,
      estimated_time,
      bottlenecks,
      optimizations
    }
  }

  /**
   * 生成建议
   */
  private generateSuggestions(
    errors: ValidationError[],
    warnings: ValidationWarning[],
    complexity: ComplexityAnalysis,
    performance: PerformanceEstimate
  ): string[] {
    const suggestions: string[] = []

    // 基于错误的建议
    if (errors.length > 0) {
      suggestions.push('修复语法错误后再运行')
    }

    // 基于警告的建议
    if (warnings.length > 0) {
      suggestions.push('注意警告信息，可能影响因子效果')
    }

    // 基于复杂度的建议
    if (complexity.score > 7) {
      suggestions.push('表达式复杂度较高，考虑简化')
    }

    // 基于性能的建议
    if (performance.computation_cost === 'high' || performance.computation_cost === 'very_high') {
      suggestions.push('计算成本较高，建议优化后再使用')
    }

    if (performance.optimizations.length > 0) {
      suggestions.push(...performance.optimizations)
    }

    // 通用建议
    if (suggestions.length === 0) {
      suggestions.push('表达式验证通过，可以使用')
    }

    return suggestions
  }

  // 辅助方法实现...
  private generateCacheKey(expression: string): string {
    return `factor_${btoa(expression).slice(0, 32)}`
  }

  private validateParentheses(expression: string): {
    isValid: boolean
    message: string
    position?: { line: number; column: number; length: number }
  } {
    const stack = []
    const pairs = { '(': ')' }

    for (let i = 0; i < expression.length; i++) {
      const char = expression[i]
      
      if (char in pairs) {
        stack.push({ char, position: i })
      } else if (Object.values(pairs).includes(char)) {
        if (stack.length === 0) {
          return {
            isValid: false,
            message: '多余的右括号',
            position: { line: 1, column: i, length: 1 }
          }
        }
        
        const last = stack.pop()
        if (pairs[last.char] !== char) {
          return {
            isValid: false,
            message: '括号类型不匹配',
            position: { line: 1, column: i, length: 1 }
          }
        }
      }
    }

    if (stack.length > 0) {
      const unclosed = stack[stack.length - 1]
      return {
        isValid: false,
        message: '未闭合的左括号',
        position: { line: 1, column: unclosed.position, length: 1 }
      }
    }

    return { isValid: true, message: '' }
  }

  private findInvalidCharacters(expression: string): string[] {
    const validChars = /[a-zA-Z0-9_$+\-*/%().,<>=!&|~"'\s]/
    const invalid = []
    
    for (const char of expression) {
      if (!validChars.test(char)) {
        invalid.push(char)
      }
    }
    
    return [...new Set(invalid)]
  }

  private isOperator(char: string): boolean {
    return ['+', '-', '*', '/', '>', '<', '=', '!', '&', '|', '~', '%'].includes(char)
  }

  private findSimilarFunctions(functionName: string): string[] {
    const available = Array.from(this.functions)
    return available
      .map(func => ({ func, similarity: this.calculateSimilarity(functionName, func) }))
      .filter(({ similarity }) => similarity > 0.6)
      .sort((a, b) => b.similarity - a.similarity)
      .slice(0, 3)
      .map(({ func }) => func)
  }

  private findSimilarFields(fieldName: string): string[] {
    const available = Array.from(this.dataFields)
    return available
      .map(field => ({ field, similarity: this.calculateSimilarity(fieldName, field) }))
      .filter(({ similarity }) => similarity > 0.5)
      .sort((a, b) => b.similarity - a.similarity)
      .slice(0, 3)
      .map(({ field }) => field)
  }

  private calculateSimilarity(str1: string, str2: string): number {
    const longer = str1.length > str2.length ? str1 : str2
    const shorter = str1.length > str2.length ? str2 : str1
    
    if (longer.length === 0) return 1.0
    
    const editDistance = this.levenshteinDistance(longer, shorter)
    return (longer.length - editDistance) / longer.length
  }

  private levenshteinDistance(str1: string, str2: string): number {
    const matrix = Array(str2.length + 1).fill(null).map(() => Array(str1.length + 1).fill(null))
    
    for (let i = 0; i <= str1.length; i++) matrix[0][i] = i
    for (let j = 0; j <= str2.length; j++) matrix[j][0] = j
    
    for (let j = 1; j <= str2.length; j++) {
      for (let i = 1; i <= str1.length; i++) {
        const indicator = str1[i - 1] === str2[j - 1] ? 0 : 1
        matrix[j][i] = Math.min(
          matrix[j][i - 1] + 1,
          matrix[j - 1][i] + 1,
          matrix[j - 1][i - 1] + indicator
        )
      }
    }
    
    return matrix[str2.length][str1.length]
  }

  private isValidNumber(value: string): boolean {
    return /^\d+(\.\d+)?$/.test(value) && !value.includes('..')
  }

  private validateExpressionStructure(tokens: Token[]): ValidationError[] {
    const errors: ValidationError[] = []
    
    // 检查是否为空
    if (tokens.length === 0) {
      errors.push({
        type: 'empty_expression',
        message: '表达式不能为空',
        severity: 'error',
        fixSuggestions: ['请输入有效的因子表达式']
      })
      return errors
    }

    // 检查表达式必须包含数据字段
    const hasDataField = tokens.some(t => t.type === TokenType.DATA_FIELD)
    if (!hasDataField && this.syntaxRules.required_data_fields.length > 0) {
      errors.push({
        type: 'missing_data_field',
        message: `表达式必须包含数据字段，如: ${this.syntaxRules.required_data_fields.join(', ')}`,
        severity: 'error',
        fixSuggestions: [`添加数据字段: ${this.syntaxRules.required_data_fields[0]}`]
      })
    }

    return errors
  }

  private validateFunctionCalls(tokens: Token[]): ValidationError[] {
    const errors: ValidationError[] = []
    
    for (let i = 0; i < tokens.length; i++) {
      if (tokens[i].type === TokenType.FUNCTION) {
        // 检查函数后面是否跟着左括号
        if (i + 1 >= tokens.length || tokens[i + 1].value !== '(') {
          errors.push({
            type: 'missing_function_parenthesis',
            message: `函数 ${tokens[i].value} 缺少括号`,
            position: { line: 1, column: tokens[i].position.start, length: tokens[i].value.length },
            severity: 'error',
            fixSuggestions: [`在 ${tokens[i].value} 后添加括号`]
          })
        }
      }
    }

    return errors
  }

  private validateOperatorUsage(tokens: Token[]): ValidationError[] {
    const errors: ValidationError[] = []
    
    for (let i = 0; i < tokens.length; i++) {
      if (tokens[i].type === TokenType.OPERATOR) {
        // 检查操作符前后是否有操作数
        const hasLeftOperand = i > 0 && this.isValidOperand(tokens[i - 1])
        const hasRightOperand = i < tokens.length - 1 && this.isValidOperand(tokens[i + 1])
        
        if (!hasLeftOperand && !hasRightOperand) {
          errors.push({
            type: 'missing_operands',
            message: `操作符 ${tokens[i].value} 缺少操作数`,
            position: { line: 1, column: tokens[i].position.start, length: tokens[i].value.length },
            severity: 'error',
            fixSuggestions: ['在操作符前后添加操作数']
          })
        }
      }
    }

    return errors
  }

  private isValidOperand(token: Token): boolean {
    return [
      TokenType.NUMBER,
      TokenType.DATA_FIELD,
      TokenType.IDENTIFIER
    ].includes(token.type) || token.value === ')'
  }

  private calculateNestedDepth(tokens: Token[]): number {
    let maxDepth = 0
    let currentDepth = 0
    
    for (const token of tokens) {
      if (token.value === '(') {
        currentDepth++
        maxDepth = Math.max(maxDepth, currentDepth)
      } else if (token.value === ')') {
        currentDepth--
      }
    }
    
    return maxDepth
  }

  private calculateTimeWindowSpan(tokens: Token[]): number {
    let maxWindow = 0
    
    // 查找时间窗口相关的数字
    for (let i = 0; i < tokens.length; i++) {
      const token = tokens[i]
      if (token.type === TokenType.FUNCTION && 
          ['Mean', 'Std', 'Sum', 'Delay', 'Ref'].includes(token.value)) {
        // 查找函数参数中的数字
        let j = i + 1
        let parenCount = 0
        
        while (j < tokens.length) {
          if (tokens[j].value === '(') parenCount++
          else if (tokens[j].value === ')') parenCount--
          else if (tokens[j].type === TokenType.NUMBER && parenCount === 1) {
            const num = parseInt(tokens[j].value)
            if (!isNaN(num)) {
              maxWindow = Math.max(maxWindow, num)
            }
          }
          
          if (parenCount === 0) break
          j++
        }
      }
    }
    
    return maxWindow
  }

  private async checkDataAvailability(tokens: Token[]): Promise<{
    errors: ValidationError[]
    warnings: ValidationWarning[]
  }> {
    const errors: ValidationError[] = []
    const warnings: ValidationWarning[] = []

    // 检查数据字段可用性
    const dataFields = tokens.filter(t => t.type === TokenType.DATA_FIELD)
    
    for (const field of dataFields) {
      // 这里应该调用实际的数据可用性检查API
      // 暂时使用模拟检查
      if (Math.random() < 0.1) { // 10%概率数据不可用
        warnings.push({
          type: 'data_availability',
          message: `数据字段 ${field.value} 可能不可用`,
          suggestion: '检查数据源连接和字段配置',
          impact: 'medium'
        })
      }
    }

    return { errors, warnings }
  }

  private checkFunctionCompatibility(tokens: Token[]): ValidationWarning[] {
    const warnings: ValidationWarning[] = []
    
    // 检查函数组合的兼容性
    const functions = tokens.filter(t => t.type === TokenType.FUNCTION)
    
    // 示例：检查某些函数组合是否会导致性能问题
    const technicalFunctions = functions.filter(f => 
      QLIB_FACTOR_CONFIG.expression_syntax.functions.technical.includes(f.value)
    )
    
    if (technicalFunctions.length > 3) {
      warnings.push({
        type: 'function_compatibility',
        message: '使用了大量技术指标函数',
        suggestion: '考虑减少技术指标数量或使用缓存',
        impact: 'high'
      })
    }

    return warnings
  }

  private checkPerformanceImpact(expression: string, tokens: Token[]): ValidationWarning[] {
    const warnings: ValidationWarning[] = []
    
    // 检查表达式长度对性能的影响
    if (expression.length > 500) {
      warnings.push({
        type: 'performance_impact',
        message: '表达式较长，可能影响计算性能',
        suggestion: '考虑简化表达式或拆分为多个步骤',
        impact: 'medium'
      })
    }

    // 检查嵌套深度
    const nestedDepth = this.calculateNestedDepth(tokens)
    if (nestedDepth > 5) {
      warnings.push({
        type: 'performance_impact',
        message: '表达式嵌套层级过深',
        suggestion: '减少嵌套层级以提高可读性和性能',
        impact: 'medium'
      })
    }

    return warnings
  }

  /**
   * 获取自动补全建议
   */
  public getAutoCompleteSuggestions(
    expression: string,
    cursorPosition: number
  ): Array<{ label: string; type: string; description: string }> {
    const suggestions = []
    const beforeCursor = expression.slice(0, cursorPosition)
    const afterCursor = expression.slice(cursorPosition)

    // 分析当前上下文
    const context = this.analyzeContext(beforeCursor)

    if (context.expectingFunction) {
      // 推荐函数
      const functionSuggestions = Array.from(this.functions).map(func => ({
        label: func,
        type: 'function',
        description: this.getFunctionDescription(func)
      }))
      suggestions.push(...functionSuggestions)
    }

    if (context.expectingDataField) {
      // 推荐数据字段
      const fieldSuggestions = Array.from(this.dataFields).map(field => ({
        label: field,
        type: 'field',
        description: this.getFieldDescription(field)
      }))
      suggestions.push(...fieldSuggestions)
    }

    if (context.expectingOperator) {
      // 推荐操作符
      const operatorSuggestions = Array.from(this.operators).map(op => ({
        label: op,
        type: 'operator',
        description: this.getOperatorDescription(op)
      }))
      suggestions.push(...operatorSuggestions)
    }

    return suggestions.slice(0, 10) // 限制返回数量
  }

  private analyzeContext(text: string): {
    expectingFunction: boolean
    expectingDataField: boolean
    expectingOperator: boolean
  } {
    const lastChar = text.trim().slice(-1)
    const lastToken = text.trim().split(/\s+/).pop() || ''

    return {
      expectingFunction: lastChar === '(' || /^[a-zA-Z_]*$/.test(lastToken),
      expectingDataField: lastChar === '$' || lastToken.startsWith('$'),
      expectingOperator: /^\d+$/.test(lastToken) || lastToken.startsWith('$') || lastChar === ')'
    }
  }

  private getFunctionDescription(func: string): string {
    const descriptions = {
      'Mean': '计算时间序列平均值',
      'Std': '计算时间序列标准差',
      'Sum': '计算时间序列总和',
      'Max': '获取时间序列最大值',
      'Min': '获取时间序列最小值',
      'Rank': '计算排名',
      'Delay': '获取延迟值',
      'Delta': '计算差值',
      'RSI': '相对强弱指标',
      'MA': '移动平均',
      'EMA': '指数移动平均'
    }
    return descriptions[func] || '内置函数'
  }

  private getFieldDescription(field: string): string {
    const descriptions = {
      '$close': '收盘价',
      '$open': '开盘价',
      '$high': '最高价',
      '$low': '最低价',
      '$volume': '成交量',
      '$amount': '成交额',
      '$vwap': '成交量加权平均价',
      '$change': '价格变动',
      '$pct_chg': '涨跌幅'
    }
    return descriptions[field] || '数据字段'
  }

  private getOperatorDescription(op: string): string {
    const descriptions = {
      '+': '加法运算',
      '-': '减法运算',
      '*': '乘法运算',
      '/': '除法运算',
      '>': '大于比较',
      '<': '小于比较',
      '>=': '大于等于',
      '<=': '小于等于',
      '==': '等于',
      '!=': '不等于',
      '&': '逻辑与',
      '|': '逻辑或'
    }
    return descriptions[op] || '操作符'
  }

  /**
   * 清理缓存
   */
  public clearCache(): void {
    this.validationCache.clear()
  }
}

// 导出单例实例
export const qlibFactorValidator = QlibFactorValidator.getInstance()

export default QlibFactorValidator