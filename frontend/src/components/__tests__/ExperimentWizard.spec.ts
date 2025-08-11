import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { ElButton, ElMessage } from 'element-plus'
import ExperimentWizard from '../experiment/ExperimentWizard.vue'

// Mock Element Plus消息
vi.mock('element-plus', async () => {
  const actual = await vi.importActual('element-plus')
  return {
    ...actual,
    ElMessage: {
      success: vi.fn(),
      error: vi.fn(),
      warning: vi.fn()
    }
  }
})

// Mock fetch
global.fetch = vi.fn()

describe('ExperimentWizard', () => {
  let wrapper: any

  beforeEach(() => {
    // Reset mocks
    vi.clearAllMocks()
    
    // Mock successful API responses
    ;(global.fetch as any).mockResolvedValue({
      ok: true,
      json: async () => ({
        success: true,
        data: {
          stock_pools: [
            { value: 'csi300', label: '沪深300' },
            { value: 'csi500', label: '中证500' }
          ],
          models: [
            { name: 'LightGBM', display_name: 'LightGBM' },
            { name: 'LSTM', display_name: 'LSTM' }
          ]
        }
      })
    })

    wrapper = mount(ExperimentWizard, {
      global: {
        components: {
          ElButton
        },
        stubs: {
          'el-card': { template: '<div class="mock-card"><slot /></div>' },
          'el-steps': { template: '<div class="mock-steps"><slot /></div>' },
          'el-step': { template: '<div class="mock-step"><slot /></div>' },
          'el-form': { template: '<form class="mock-form"><slot /></form>' },
          'el-form-item': { template: '<div class="mock-form-item"><slot /></div>' },
          'el-input': { template: '<input class="mock-input" />' },
          'el-select': { template: '<select class="mock-select"><slot /></select>' },
          'el-option': { template: '<option class="mock-option"><slot /></option>' },
          'el-date-picker': { template: '<input type="date" class="mock-date-picker" />' },
          'el-radio-group': { template: '<div class="mock-radio-group"><slot /></div>' },
          'el-radio': { template: '<input type="radio" class="mock-radio" />' },
          'el-switch': { template: '<input type="checkbox" class="mock-switch" />' },
          'el-slider': { template: '<input type="range" class="mock-slider" />' },
          'el-progress': { template: '<div class="mock-progress"></div>' },
          'el-alert': { template: '<div class="mock-alert"><slot /></div>' },
          'el-tag': { template: '<span class="mock-tag"><slot /></span>' },
          'el-button-group': { template: '<div class="mock-button-group"><slot /></div>' },
          'el-row': { template: '<div class="mock-row"><slot /></div>' },
          'el-col': { template: '<div class="mock-col"><slot /></div>' },
          'el-descriptions': { template: '<div class="mock-descriptions"><slot /></div>' },
          'el-descriptions-item': { template: '<div class="mock-descriptions-item"><slot /></div>' }
        }
      }
    })
  })

  describe('组件初始化', () => {
    it('应该正确渲染', () => {
      expect(wrapper.exists()).toBe(true)
      expect(wrapper.find('.experiment-wizard').exists()).toBe(true)
    })

    it('应该初始化为第一步', () => {
      expect(wrapper.vm.currentStep).toBe(1)
    })

    it('应该初始化表单数据', () => {
      expect(wrapper.vm.experimentForm).toEqual({
        name: '',
        description: '',
        tags: [],
        data_config: {
          stock_pool: '',
          start_date: '',
          end_date: ''
        },
        model_config: {
          name: '',
          params: {}
        },
        strategy_config: {
          name: '',
          params: {},
          risk_control: {
            max_drawdown: 0.2,
            daily_loss_limit: 0.05,
            stop_loss: 0.15
          }
        }
      })
    })
  })

  describe('步骤导航', () => {
    it('下一步按钮应该存在', () => {
      const nextButton = wrapper.find('[data-testid="next-button"]')
      // 由于我们使用了stub，检查是否存在相关元素
      expect(wrapper.text()).toContain('下一步')
    })

    it('第一步不应该显示上一步按钮', () => {
      expect(wrapper.text()).not.toContain('上一步')
    })

    it('点击下一步应该验证当前步骤', async () => {
      const validateSpy = vi.spyOn(wrapper.vm, 'validateCurrentStep')
      
      // 模拟点击下一步
      await wrapper.vm.nextStep()
      
      expect(validateSpy).toHaveBeenCalled()
    })
  })

  describe('表单验证', () => {
    it('第一步验证应该检查实验名称', async () => {
      // 空名称应该验证失败
      wrapper.vm.experimentForm.name = ''
      const isValid = await wrapper.vm.validateCurrentStep()
      expect(isValid).toBe(false)
    })

    it('有效的实验名称应该通过验证', async () => {
      wrapper.vm.experimentForm.name = '测试实验'
      const isValid = await wrapper.vm.validateCurrentStep()
      expect(isValid).toBe(true)
    })

    it('应该验证时间范围', async () => {
      wrapper.vm.currentStep = 2
      wrapper.vm.experimentForm.data_config.stock_pool = 'csi300'
      
      // 设置无效的时间范围
      wrapper.vm.timeRange = ['2023-01-01', '2022-12-31'] // 结束日期早于开始日期
      wrapper.vm.onTimeRangeChange()
      
      const isValid = await wrapper.vm.validateCurrentStep()
      expect(isValid).toBe(false)
    })
  })

  describe('数据加载', () => {
    it('应该在步骤变化时加载相应数据', async () => {
      const loadStepDataSpy = vi.spyOn(wrapper.vm, 'loadStepData')
      
      wrapper.vm.currentStep = 2
      await wrapper.vm.nextStep()
      
      expect(loadStepDataSpy).toHaveBeenCalled()
    })

    it('应该加载模型参数', async () => {
      wrapper.vm.experimentForm.model_config.name = 'LightGBM'
      
      await wrapper.vm.loadModelParams()
      
      expect(global.fetch).toHaveBeenCalledWith('/api/v1/config/model-params/LightGBM')
    })

    it('加载失败时应该处理错误', async () => {
      ;(global.fetch as any).mockRejectedValueOnce(new Error('Network error'))
      
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
      
      await wrapper.vm.loadModelParams()
      
      expect(consoleSpy).toHaveBeenCalledWith('加载模型参数失败:', expect.any(Error))
      consoleSpy.mockRestore()
    })
  })

  describe('智能推荐', () => {
    it('应该加载参数推荐', async () => {
      wrapper.vm.experimentForm.model_config.name = 'LightGBM'
      wrapper.vm.experimentForm.data_config.stock_pool = 'csi300'
      
      await wrapper.vm.loadParameterRecommendations()
      
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/recommendations/model-params/LightGBM')
      )
    })

    it('应该应用推荐参数', async () => {
      const mockRecommendations = {
        recommended_params: {
          n_estimators: 100,
          learning_rate: 0.1
        }
      }
      
      ;(global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          data: mockRecommendations
        })
      })
      
      wrapper.vm.experimentForm.model_config.name = 'LightGBM'
      await wrapper.vm.loadParameterRecommendations()
      
      expect(wrapper.vm.experimentForm.model_config.params).toEqual(
        mockRecommendations.recommended_params
      )
    })

    it('应该能使用推荐值', () => {
      wrapper.vm.paramRecommendations = {
        recommended_params: {
          n_estimators: 100
        }
      }
      
      wrapper.vm.useRecommendedValue('n_estimators')
      
      expect(wrapper.vm.experimentForm.model_config.params.n_estimators).toBe(100)
      expect(ElMessage.success).toHaveBeenCalledWith('已应用推荐值: 100')
    })
  })

  describe('标签管理', () => {
    it('应该能添加标签', () => {
      wrapper.vm.newTag = '测试标签'
      wrapper.vm.addTag()
      
      expect(wrapper.vm.experimentForm.tags).toContain('测试标签')
      expect(wrapper.vm.newTag).toBe('')
    })

    it('不应该添加重复标签', () => {
      wrapper.vm.experimentForm.tags = ['已存在']
      wrapper.vm.newTag = '已存在'
      wrapper.vm.addTag()
      
      expect(wrapper.vm.experimentForm.tags).toEqual(['已存在'])
    })

    it('应该能移除标签', () => {
      wrapper.vm.experimentForm.tags = ['标签1', '标签2']
      wrapper.vm.removeTag('标签1')
      
      expect(wrapper.vm.experimentForm.tags).toEqual(['标签2'])
    })
  })

  describe('时间范围设置', () => {
    it('应该能设置预设时间范围', () => {
      wrapper.vm.setTimeRange('1y')
      
      expect(wrapper.vm.timeRange).toHaveLength(2)
      expect(wrapper.vm.experimentForm.data_config.start_date).toBeDefined()
      expect(wrapper.vm.experimentForm.data_config.end_date).toBeDefined()
    })

    it('应该正确计算时间差', () => {
      const mockDate = new Date('2023-12-31')
      vi.setSystemTime(mockDate)
      
      wrapper.vm.setTimeRange('1y')
      
      const startDate = new Date(wrapper.vm.experimentForm.data_config.start_date)
      const endDate = new Date(wrapper.vm.experimentForm.data_config.end_date)
      const yearDiff = endDate.getFullYear() - startDate.getFullYear()
      
      expect(yearDiff).toBe(1)
    })
  })

  describe('实验提交', () => {
    beforeEach(() => {
      // 设置有效的实验配置
      wrapper.vm.experimentForm = {
        name: '测试实验',
        description: '测试描述',
        tags: ['测试'],
        data_config: {
          stock_pool: 'csi300',
          start_date: '2022-01-01',
          end_date: '2023-01-01'
        },
        model_config: {
          name: 'LightGBM',
          params: { n_estimators: 100 }
        },
        strategy_config: {
          name: 'TopkDropoutStrategy',
          params: { topk: 50 },
          risk_control: {
            max_drawdown: 0.2,
            daily_loss_limit: 0.05,
            stop_loss: 0.15
          }
        }
      }
      
      wrapper.vm.currentStep = 5
    })

    it('应该提交实验配置', async () => {
      ;(global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          data: { id: '123', name: '测试实验' }
        })
      })
      
      await wrapper.vm.submitExperiment()
      
      expect(global.fetch).toHaveBeenCalledWith('/api/v1/experiments', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(wrapper.vm.experimentForm)
      })
      
      expect(ElMessage.success).toHaveBeenCalledWith('实验创建成功！')
    })

    it('提交失败时应该显示错误信息', async () => {
      ;(global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: false,
          message: '配置验证失败'
        })
      })
      
      await wrapper.vm.submitExperiment()
      
      expect(ElMessage.error).toHaveBeenCalledWith('配置验证失败')
    })

    it('网络错误时应该显示错误信息', async () => {
      ;(global.fetch as any).mockRejectedValueOnce(new Error('Network error'))
      
      await wrapper.vm.submitExperiment()
      
      expect(ElMessage.error).toHaveBeenCalledWith('网络错误，创建实验失败')
    })
  })

  describe('风险评估', () => {
    it('应该正确计算风险等级', () => {
      wrapper.vm.experimentForm.model_config.name = 'LSTM'
      wrapper.vm.experimentForm.strategy_config.name = 'TopkLongShortStrategy'
      
      const riskLevel = wrapper.vm.riskLevel
      expect(riskLevel.type).toBe('danger')
      expect(riskLevel.label).toBe('高风险')
    })

    it('应该为低风险配置返回正确标签', () => {
      wrapper.vm.experimentForm.model_config.name = 'LinearModel'
      wrapper.vm.experimentForm.strategy_config.name = 'TopkDropoutStrategy'
      
      const riskLevel = wrapper.vm.riskLevel
      expect(riskLevel.type).toBe('success')
      expect(riskLevel.label).toBe('低风险')
    })
  })

  describe('资源估算', () => {
    it('应该为深度学习模型提供更高的资源估算', () => {
      wrapper.vm.experimentForm.model_config.name = 'LSTM'
      
      const estimation = wrapper.vm.resourceEstimation
      expect(estimation.training_time).toBe('30-45分钟')
      expect(estimation.memory_usage).toBe('2-4GB')
    })

    it('应该为传统模型提供较低的资源估算', () => {
      wrapper.vm.experimentForm.model_config.name = 'LightGBM'
      
      const estimation = wrapper.vm.resourceEstimation
      expect(estimation.training_time).toBe('5-15分钟')
      expect(estimation.memory_usage).toBe('512MB-1GB')
    })
  })
})