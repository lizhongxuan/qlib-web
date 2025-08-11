import request from './request'
import type { 
  ExperimentConfig, 
  ExperimentStatus, 
  ExperimentDetail,
  ApiResponse,
  PaginatedResponse
} from '@/types/experiment'

// 实验相关API
export const experimentApi = {
  // 获取实验列表
  getExperiments: (params?: { 
    page?: number
    pageSize?: number
    status?: string 
  }) => {
    return request.get<ApiResponse<PaginatedResponse<ExperimentStatus>>>('/experiments', { params })
  },

  // 创建新实验
  createExperiment: (config: ExperimentConfig) => {
    return request.post<ApiResponse<{ id: string }>>('/experiments', config)
  },

  // 获取实验详情
  getExperimentDetail: (id: string) => {
    return request.get<ApiResponse<ExperimentDetail>>(`/experiments/${id}`)
  },

  // 删除实验
  deleteExperiment: (id: string) => {
    return request.delete<ApiResponse<null>>(`/experiments/${id}`)
  },

  // 获取实验性能数据
  getExperimentPerformance: (id: string) => {
    return request.get<ApiResponse<any>>(`/experiments/${id}/performance`)
  },

  // 获取实验持仓数据
  getExperimentPositions: (id: string) => {
    return request.get<ApiResponse<any>>(`/experiments/${id}/positions`)
  },

  // 获取实验日志
  getExperimentLogs: (id: string) => {
    return request.get<ApiResponse<string[]>>(`/experiments/${id}/logs`)
  }
}

// 配置相关API
export const configApi = {
  // 获取股票池列表
  getStockPools: () => {
    return request.get<ApiResponse<string[]>>('/config/stock-pools')
  },

  // 获取模型列表
  getModels: () => {
    return request.get<ApiResponse<string[]>>('/config/models')
  },

  // 获取策略列表
  getStrategies: () => {
    return request.get<ApiResponse<string[]>>('/config/strategies')
  },

  // 获取模型参数配置
  getModelParams: (modelName: string) => {
    return request.get<ApiResponse<Record<string, any>>>(`/config/model-params/${modelName}`)
  }
}

// 仪表盘相关API
export const dashboardApi = {
  // 获取仪表盘统计数据
  getSummary: () => {
    return request.get<ApiResponse<{
      totalExperiments: number
      runningExperiments: number
      completedExperiments: number
      failedExperiments: number
    }>>('/dashboard/summary')
  },

  // 获取最近实验列表
  getRecentExperiments: () => {
    return request.get<ApiResponse<ExperimentStatus[]>>('/dashboard/recent')
  }
}