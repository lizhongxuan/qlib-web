// 实验配置相关类型
export interface DataConfig {
  stockPool: string
  startTime: string
  endTime: string
}

export interface ModelConfig {
  name: string
  params: Record<string, any>
}

export interface StrategyConfig {
  name: string
  params: Record<string, any>
}

export interface BacktestConfig {
  tradeCost: number
}

export interface ExperimentConfig {
  name: string
  dataConfig: DataConfig
  modelConfig: ModelConfig
  strategyConfig: StrategyConfig
  backtestConfig: BacktestConfig
}

// 实验状态相关类型
export type ExperimentStatusType = 'pending' | 'running' | 'completed' | 'failed'

export interface ExperimentStatus {
  id: string
  name: string
  status: ExperimentStatusType
  createdAt: string
  completedAt: string | null
  progress: number
}

// 实验结果相关类型
export interface PerformanceMetrics {
  totalReturn: number
  annualReturn: number
  sharpeRatio: number
  maxDrawdown: number
  volatility: number
}

export interface ExperimentResults {
  performance: PerformanceMetrics
  positions?: Array<{
    date: string
    symbol: string
    weight: number
  }>
  logs?: string[]
}

export interface ExperimentDetail {
  id: string
  name: string
  config: ExperimentConfig
  status: ExperimentStatusType
  createdAt: string
  completedAt: string | null
  results?: ExperimentResults
}

// API响应类型
export interface ApiResponse<T> {
  success: boolean
  data: T
  message?: string
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  pageSize: number
}