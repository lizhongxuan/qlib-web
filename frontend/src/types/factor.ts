// 因子相关类型定义

export interface FactorDefinition {
  id: string
  name: string
  expression: string
  description: string
  category: FactorCategory
  status?: FactorStatus
  performance?: FactorPerformance
  expectedPerformance?: ExpectedPerformance
  createdBy: string
  createdAt: Date
  updatedAt?: Date
  tags?: string[]
  version?: string
}

export type FactorCategory = 
  | 'technical'      // 技术指标
  | 'fundamental'    // 基本面
  | 'sentiment'      // 情绪指标
  | 'composite'      // 组合因子
  | 'other'          // 其他

export type FactorStatus = 
  | 'active'         // 活跃
  | 'testing'        // 测试中
  | 'deprecated'     // 已废弃
  | 'draft'          // 草稿

export interface FactorPerformance {
  ic?: number              // 信息系数
  icStd?: number          // IC标准差
  ir?: number             // 信息比率
  rankIC?: number         // 排序信息系数
  winRate?: number        // 胜率（百分比）
  annualReturn?: number   // 年化收益率（百分比）
  maxDrawdown?: number    // 最大回撤（百分比）
  sharpe?: number         // 夏普比率
  volatility?: number     // 波动率（百分比）
  lastUpdated?: Date      // 性能指标最后更新时间
}

export interface ExpectedPerformance {
  annualReturn: number    // 预期年化收益（百分比）
  informationRatio: number // 预期信息比率
  winRate: number         // 预期胜率（百分比）
  confidence?: number     // 预测置信度（百分比）
}

export interface FactorTestConfig {
  factorId: string
  dateRange: [string, string]  // 测试时间范围
  stockPool: string            // 股票池
  frequency: 'daily' | 'weekly' | 'monthly'  // 更新频率
  benchmark: string            // 基准指数
  groups: number               // 分组数量
  rebalanceFreq?: string       // 调仓频率
  commission?: number          // 手续费率
}

export interface FactorTestResult {
  factorId: string
  testConfig: FactorTestConfig
  performance: FactorPerformance
  quality: FactorQuality
  groupResults: GroupBacktestResult[]
  icTimeSeries: ICTimeSeriesData[]
  distribution: FactorDistribution
  suggestions: string[]
  applicableScenarios: string[]
  warnings?: FactorWarning[]
  testDate: Date
}

export type FactorQuality = 'excellent' | 'good' | 'fair' | 'poor'

export interface GroupBacktestResult {
  group: string               // 分组名称（如G1, G2等）
  annualReturn: number        // 年化收益率
  volatility: number          // 波动率
  sharpe: number             // 夏普比率
  maxDrawdown: number        // 最大回撤
  avgWeight: number          // 平均权重
  stockCount?: number        // 平均持股数量
}

export interface ICTimeSeriesData {
  date: string
  ic: number
  rankIC?: number
  pValue?: number
}

export interface FactorDistribution {
  mean: number
  std: number
  min: number
  max: number
  skew: number         // 偏度
  kurtosis: number     // 峰度
  percentiles: {       // 分位数
    p1: number
    p5: number
    p25: number
    p50: number
    p75: number
    p95: number
    p99: number
  }
}

export interface FactorWarning {
  type: 'error' | 'warning' | 'info'
  title: string
  description: string
  suggestion?: string
}

export interface FactorOptimizationSuggestion {
  title: string
  description: string
  code?: string
  expectedImprovement?: string
  priority: 'high' | 'medium' | 'low'
}

export interface FactorLibraryItem {
  factor: FactorDefinition
  usage: {
    usageCount: number        // 使用次数
    lastUsed?: Date          // 最后使用时间
    avgRating?: number       // 平均评分
    ratingCount?: number     // 评分次数
  }
  metadata: {
    isPublic: boolean        // 是否公开
    isVerified: boolean      // 是否验证
    downloadCount?: number   // 下载次数
    shareCount?: number      // 分享次数
  }
}

export interface FactorSearchParams {
  keyword?: string           // 关键词搜索
  category?: FactorCategory  // 按类型筛选
  status?: FactorStatus     // 按状态筛选
  createdBy?: string        // 按创建者筛选
  dateRange?: [Date, Date]  // 按创建时间筛选
  performanceFilter?: {     // 按性能筛选
    minIC?: number
    maxIC?: number
    minIR?: number
    maxIR?: number
    minWinRate?: number
    maxWinRate?: number
  }
  tags?: string[]          // 按标签筛选
  sortBy?: 'createdAt' | 'performance' | 'usage' | 'rating'
  sortOrder?: 'asc' | 'desc'
  limit?: number
  offset?: number
}

export interface FactorBatchOperation {
  type: 'test' | 'export' | 'delete' | 'updateStatus' | 'addTags'
  factorIds: string[]
  params?: Record<string, any>
}

export interface FactorValidationError {
  type: 'syntax' | 'semantic' | 'runtime'
  message: string
  line?: number
  column?: number
  suggestion?: string
}

export interface FactorExpressionContext {
  availableFields: string[]     // 可用字段列表
  functions: FactorFunction[]   // 可用函数列表
  examples: string[]           // 示例表达式
  validation: {
    syntax: boolean           // 语法检查
    semantic: boolean         // 语义检查
    performance: boolean      // 性能检查
  }
}

export interface FactorFunction {
  name: string
  category: 'math' | 'stats' | 'timeseries' | 'cross-section' | 'other'
  description: string
  syntax: string
  parameters: FactorFunctionParameter[]
  examples: string[]
  returnType: string
}

export interface FactorFunctionParameter {
  name: string
  type: string
  required: boolean
  description: string
  defaultValue?: any
}

// AI相关类型
export interface AIFactorRequest {
  prompt: string              // 用户输入的自然语言描述
  context?: {                 // 上下文信息
    previousFactors?: string[]
    userPreferences?: any
    marketEnvironment?: string
  }
  options?: {
    creativity: number        // 创造性程度（0-1）
    complexity: number        // 复杂程度（0-1）
    conservative: boolean     // 是否保守
  }
}

export interface AIFactorResponse {
  factor: FactorDefinition
  confidence: number          // AI生成的置信度
  reasoning: string          // 生成逻辑说明
  alternatives?: FactorDefinition[]  // 备选方案
  warnings?: string[]        // 警告信息
  suggestions?: FactorOptimizationSuggestion[]
}

// 批量训练相关类型
export interface FactorTrainingBatch {
  id: string
  name: string
  factors: string[]          // 因子ID列表
  config: TrainingBatchConfig
  status: 'pending' | 'running' | 'completed' | 'failed'
  progress: number           // 进度百分比
  results?: FactorTrainingResult[]
  createdAt: Date
  startedAt?: Date
  completedAt?: Date
  error?: string
}

export interface TrainingBatchConfig {
  dataConfig: {
    stockPool: string
    startDate: string
    endDate: string
    frequency: string
  }
  modelConfig: {
    type: string
    params: Record<string, any>
  }
  crossValidation: {
    folds: number
    testRatio: number
  }
}

export interface FactorTrainingResult {
  factorId: string
  modelPath: string
  performance: FactorPerformance
  validation: {
    trainScore: number
    validScore: number
    testScore: number
    overfitting: boolean
  }
  featureImportance?: number
  trainingTime: number       // 训练时间（秒）
}