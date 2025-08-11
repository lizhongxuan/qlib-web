import { describe, it, expect, vi, beforeEach } from 'vitest'
import { experimentApi, configApi, dashboardApi } from '../experiment'
import { createMockExperimentConfig, createMockDashboardData, mockApiResponse } from '../../test/utils'

// 模拟request模块
vi.mock('../request', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}))

// 导入模拟的request
import request from '../request'

const mockRequest = request as any

describe('实验API', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })
  
  describe('experimentApi', () => {
    it('应该正确调用获取实验列表API', async () => {
      const mockData = {
        items: [{ id: '1', name: '实验1' }],
        total: 1,
      }
      mockRequest.get.mockResolvedValue(mockApiResponse(mockData))
      
      const params = { page: 1, pageSize: 10, status: 'completed' }
      const result = await experimentApi.getExperiments(params)
      
      expect(mockRequest.get).toHaveBeenCalledWith('/experiments', { params })
      expect(result.data.data).toEqual(mockData)
    })
    
    it('应该正确调用创建实验API', async () => {
      const config = createMockExperimentConfig()
      const mockData = { id: 'new-exp-123' }
      mockRequest.post.mockResolvedValue(mockApiResponse(mockData))
      
      const result = await experimentApi.createExperiment(config)
      
      expect(mockRequest.post).toHaveBeenCalledWith('/experiments', config)
      expect(result.data.data).toEqual(mockData)
    })
    
    it('应该正确调用获取实验详情API', async () => {
      const experimentId = 'test-exp-123'
      const mockData = { id: experimentId, name: '测试实验' }
      mockRequest.get.mockResolvedValue(mockApiResponse(mockData))
      
      const result = await experimentApi.getExperimentDetail(experimentId)
      
      expect(mockRequest.get).toHaveBeenCalledWith(`/experiments/${experimentId}`)
      expect(result.data.data).toEqual(mockData)
    })
    
    it('应该正确调用删除实验API', async () => {
      const experimentId = 'test-exp-123'
      mockRequest.delete.mockResolvedValue(mockApiResponse(null))
      
      const result = await experimentApi.deleteExperiment(experimentId)
      
      expect(mockRequest.delete).toHaveBeenCalledWith(`/experiments/${experimentId}`)
      expect(result.data.success).toBe(true)
    })
    
    it('应该正确调用获取实验性能数据API', async () => {
      const experimentId = 'test-exp-123'
      const mockData = { performance_metrics: { total_return: 0.156 } }
      mockRequest.get.mockResolvedValue(mockApiResponse(mockData))
      
      const result = await experimentApi.getExperimentPerformance(experimentId)
      
      expect(mockRequest.get).toHaveBeenCalledWith(`/experiments/${experimentId}/performance`)
      expect(result.data.data).toEqual(mockData)
    })
    
    it('应该正确调用获取实验持仓数据API', async () => {
      const experimentId = 'test-exp-123'
      const mockData = { positions: [] }
      mockRequest.get.mockResolvedValue(mockApiResponse(mockData))
      
      const result = await experimentApi.getExperimentPositions(experimentId)
      
      expect(mockRequest.get).toHaveBeenCalledWith(`/experiments/${experimentId}/positions`)
      expect(result.data.data).toEqual(mockData)
    })
    
    it('应该正确调用获取实验日志API', async () => {
      const experimentId = 'test-exp-123'
      const mockData = ['日志1', '日志2']
      mockRequest.get.mockResolvedValue(mockApiResponse(mockData))
      
      const result = await experimentApi.getExperimentLogs(experimentId)
      
      expect(mockRequest.get).toHaveBeenCalledWith(`/experiments/${experimentId}/logs`)
      expect(result.data.data).toEqual(mockData)
    })
  })
  
  describe('configApi', () => {
    it('应该正确调用获取股票池列表API', async () => {
      const mockData = ['CSI300', 'CSI500', 'CSI800']
      mockRequest.get.mockResolvedValue(mockApiResponse(mockData))
      
      const result = await configApi.getStockPools()
      
      expect(mockRequest.get).toHaveBeenCalledWith('/config/stock-pools')
      expect(result.data.data).toEqual(mockData)
    })
    
    it('应该正确调用获取模型列表API', async () => {
      const mockData = ['LightGBM', 'XGBoost', 'LSTM']
      mockRequest.get.mockResolvedValue(mockApiResponse(mockData))
      
      const result = await configApi.getModels()
      
      expect(mockRequest.get).toHaveBeenCalledWith('/config/models')
      expect(result.data.data).toEqual(mockData)
    })
    
    it('应该正确调用获取策略列表API', async () => {
      const mockData = ['TopkDropoutStrategy', 'SignalStrategy']
      mockRequest.get.mockResolvedValue(mockApiResponse(mockData))
      
      const result = await configApi.getStrategies()
      
      expect(mockRequest.get).toHaveBeenCalledWith('/config/strategies')
      expect(result.data.data).toEqual(mockData)
    })
    
    it('应该正确调用获取模型参数API', async () => {
      const modelName = 'LightGBM'
      const mockData = { n_estimators: { type: 'int', default: 100 } }
      mockRequest.get.mockResolvedValue(mockApiResponse(mockData))
      
      const result = await configApi.getModelParams(modelName)
      
      expect(mockRequest.get).toHaveBeenCalledWith(`/config/model-params/${modelName}`)
      expect(result.data.data).toEqual(mockData)
    })
  })
  
  describe('dashboardApi', () => {
    it('应该正确调用获取仪表盘统计数据API', async () => {
      const mockData = createMockDashboardData()
      mockRequest.get.mockResolvedValue(mockApiResponse(mockData))
      
      const result = await dashboardApi.getSummary()
      
      expect(mockRequest.get).toHaveBeenCalledWith('/dashboard/summary')
      expect(result.data.data).toEqual(mockData)
    })
    
    it('应该正确调用获取最近实验列表API', async () => {
      const mockData = [
        { id: '1', name: '实验1', status: 'completed' },
        { id: '2', name: '实验2', status: 'running' },
      ]
      mockRequest.get.mockResolvedValue(mockApiResponse(mockData))
      
      const result = await dashboardApi.getRecentExperiments()
      
      expect(mockRequest.get).toHaveBeenCalledWith('/dashboard/recent')
      expect(result.data.data).toEqual(mockData)
    })
  })
})