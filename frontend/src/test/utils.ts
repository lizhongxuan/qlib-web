import { mount, VueWrapper } from '@vue/test-utils'
import { ElConfigProvider } from 'element-plus'
import { ComponentPublicInstance } from 'vue'

/**
 * 创建带Element Plus配置的组件包装器
 */
export function createWrapper(
  component: any,
  options: any = {}
): VueWrapper<ComponentPublicInstance> {
  return mount(component, {
    global: {
      components: {
        ElConfigProvider,
      },
      ...options.global,
    },
    ...options,
  })
}

/**
 * 等待下一个Vue更新周期
 */
export async function flushPromises() {
  return new Promise(resolve => setTimeout(resolve, 0))
}

/**
 * 模拟API响应
 */
export function mockApiResponse<T>(data: T, success = true) {
  return Promise.resolve({
    data: {
      success,
      data,
      message: success ? '成功' : '失败',
    },
  })
}

/**
 * 模拟API错误响应
 */
export function mockApiError(message = '请求失败', status = 500) {
  return Promise.reject({
    response: {
      status,
      data: { message },
    },
  })
}

/**
 * 创建模拟的实验数据
 */
export function createMockExperiment(id = 'test-exp-123') {
  return {
    id,
    name: '测试实验',
    description: '这是一个测试实验',
    status: 'completed',
    progress: 100,
    created_at: '2024-01-01T10:00:00Z',
    completed_at: '2024-01-01T11:00:00Z',
    total_return: 0.156,
    sharpe_ratio: 1.25,
    max_drawdown: -0.08,
    is_favorite: false,
    tags: ['测试', '示例'],
  }
}

/**
 * 创建模拟的实验配置
 */
export function createMockExperimentConfig() {
  return {
    name: '测试实验',
    description: '这是一个测试实验',
    config: {
      data_config: {
        stock_pool: 'CSI300',
        start_time: '2020-01-01',
        end_time: '2021-12-31',
      },
      model_config: {
        name: 'LightGBM',
        params: {
          n_estimators: 100,
          learning_rate: 0.1,
        },
      },
      strategy_config: {
        name: 'TopkDropoutStrategy',
        params: {
          topk: 50,
        },
      },
      backtest_config: {
        trade_cost: 0.0015,
        benchmark: 'CSI300',
        initial_cash: 1000000,
      },
    },
    tags: ['测试', '示例'],
  }
}

/**
 * 创建模拟的仪表盘数据
 */
export function createMockDashboardData() {
  return {
    totalExperiments: 25,
    runningExperiments: 3,
    completedExperiments: 20,
    failedExperiments: 2,
    recentExperiments: [
      createMockExperiment('recent-1'),
      createMockExperiment('recent-2'),
      createMockExperiment('recent-3'),
    ],
  }
}