// 训练相关类型定义

export interface TrainingConfig {
  name: string
  description?: string
  dataConfig: {
    stockPool: string
    dateRange: [string, string] | string[]
    frequency: 'daily' | 'weekly' | 'monthly'
  }
  modelConfig: {
    type: string
    params: Record<string, any>
  }
  trainingParams: {
    epochs: number
    batchSize: number
    learningRate: number
    validationSplit: number
    earlyStoppingPatience: number
    saveBestModel: boolean
    randomSeed?: number
    nJobs?: number
    verbose?: boolean
    callbacks?: string[]
    scheduler?: string
  }
  evaluationConfig?: {
    primaryMetric: string
    crossValidation: boolean
    cvFolds: number
  }
}

export interface TrainingTask {
  id: string
  name: string
  config: TrainingConfig
  factors: any[]
  status: 'pending' | 'running' | 'paused' | 'completed' | 'failed'
  progress: number
  createdAt: Date
  startedAt?: Date
  completedAt?: Date
  error?: string
  metrics?: TrainingMetrics
  checkpoints?: TrainingCheckpoint[]
}

export interface TrainingMetrics {
  trainLoss: number
  valLoss: number
  trainAcc: number
  valAcc: number
  bestValAcc: number
  learningRate?: number
  gradNorm?: number
  epoch?: number
  history?: {
    epoch: number
    trainLoss: number
    valLoss: number
    trainAcc: number
    valAcc: number
    timestamp: Date
  }[]
}

export interface TrainingCheckpoint {
  id: string
  epoch: number
  timestamp: Date
  metrics: {
    loss: number
    acc: number
    valLoss?: number
    valAcc?: number
  }
  filePath: string
  size: string
}

export interface ModelRecommendation {
  type: string
  name: string
  description: string
  confidence: number
  reasons: string[]
  expectedPerformance: {
    accuracy: number
    trainingTime: number
    resourceUsage: number
  }
  recommendedParams: Record<string, any>
}

export interface HyperparameterOptimizationConfig {
  algorithm: 'bayesian' | 'grid' | 'random' | 'genetic'
  objective: 'maximize_accuracy' | 'maximize_auc' | 'maximize_f1' | 'minimize_loss'
  maxIterations: number
  parameters: {
    [paramName: string]: {
      type: 'int' | 'float' | 'categorical'
      min?: number
      max?: number
      step?: number
      choices?: any[]
      distribution?: 'uniform' | 'log-uniform' | 'normal'
    }
  }
}

export interface OptimizationTrial {
  id: number
  params: Record<string, any>
  score: number
  duration: number
  status: 'completed' | 'failed' | 'running'
  timestamp: Date
  error?: string
}

export interface OptimizationResult {
  bestParams: Record<string, any>
  bestScore: number
  trials: OptimizationTrial[]
  convergenceHistory: number[]
  parameterImportance: Record<string, number>
  completedAt: Date
  totalDuration: number
}

// 资源监控相关类型
export interface ResourceMetrics {
  cpu: {
    usage: number
    cores: number
    load: number
  }
  memory: {
    usage: number
    used: number
    total: number
  }
  gpu?: {
    available: boolean
    usage: number
    memoryUsage: number
    memoryUsed: number
    memoryTotal: number
    model: string
    temperature: number
  }
  disk?: {
    usage: number
    used: number
    total: number
  }
  network?: {
    bytesReceived: number
    bytesSent: number
  }
}

// 训练日志相关类型
export interface TrainingLog {
  id: number
  timestamp: Date
  level: 'debug' | 'info' | 'warning' | 'error'
  category: 'training' | 'validation' | 'checkpoint' | 'resource' | 'system'
  message: string
  data?: Record<string, any>
}

// 模型评估结果类型
export interface EvaluationResult {
  modelId: string
  modelName: string
  metrics: {
    accuracy: number
    precision: number
    recall: number
    f1Score: number
    auc?: number
    sharpeRatio?: number
    informationRatio?: number
    maxDrawdown?: number
    volatility?: number
    returns?: number
  }
  confusionMatrix?: number[][]
  featureImportance?: {
    feature: string
    importance: number
  }[]
  predictions?: {
    actual: number[]
    predicted: number[]
    timestamps: Date[]
  }
  crossValidationScores?: number[]
  evaluatedAt: Date
}

// 训练任务批处理类型
export interface BatchTrainingTask {
  id: string
  name: string
  tasks: TrainingTask[]
  status: 'pending' | 'running' | 'completed' | 'failed' | 'partial'
  createdAt: Date
  completedAt?: Date
  totalTasks: number
  completedTasks: number
  failedTasks: number
  bestTask?: {
    taskId: string
    score: number
  }
}

// 模型比较结果类型
export interface ModelComparison {
  id: string
  name: string
  models: {
    id: string
    name: string
    type: string
    metrics: EvaluationResult['metrics']
  }[]
  comparisonMetrics: string[]
  winner?: {
    modelId: string
    reason: string
  }
  createdAt: Date
}

// 训练模板类型
export interface TrainingTemplate {
  id: string
  name: string
  description: string
  category: 'quick' | 'professional' | 'experimental'
  config: Partial<TrainingConfig>
  isPublic: boolean
  createdBy: string
  createdAt: Date
  usageCount: number
  rating?: number
  tags: string[]
}

// 实时训练状态
export interface RealtimeTrainingStatus {
  taskId: string
  currentEpoch: number
  totalEpochs: number
  progress: number
  currentMetrics: TrainingMetrics
  estimatedTimeRemaining: number
  resourceUsage: ResourceMetrics
  recentLogs: TrainingLog[]
  lastUpdated: Date
}