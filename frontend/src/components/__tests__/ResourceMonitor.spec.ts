/**
 * ResourceMonitor组件测试
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, VueWrapper } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import ResourceMonitor from '../system/ResourceMonitor.vue'

// Mock ECharts
vi.mock('echarts', () => ({
  default: {
    init: vi.fn(() => ({
      setOption: vi.fn(),
      resize: vi.fn(),
      dispose: vi.fn(),
      on: vi.fn(),
      off: vi.fn()
    })),
    registerTheme: vi.fn()
  }
}))

// Mock API请求
vi.mock('@/api/request', () => ({
  apiRequest: vi.fn()
}))

describe('ResourceMonitor', () => {
  let wrapper: VueWrapper<any>
  let pinia: any

  beforeEach(() => {
    pinia = createPinia()
    setActivePinia(pinia)
    
    // Mock window.ResizeObserver
    global.ResizeObserver = vi.fn().mockImplementation(() => ({
      observe: vi.fn(),
      unobserve: vi.fn(),
      disconnect: vi.fn()
    }))
  })

  afterEach(() => {
    if (wrapper) {
      wrapper.unmount()
    }
    vi.clearAllMocks()
  })

  it('应该正确渲染组件', () => {
    wrapper = mount(ResourceMonitor, {
      global: {
        plugins: [pinia]
      }
    })

    expect(wrapper.find('.resource-monitor').exists()).toBe(true)
    expect(wrapper.find('.resource-cards').exists()).toBe(true)
    expect(wrapper.find('.resource-charts').exists()).toBe(true)
  })

  it('应该显示资源卡片', async () => {
    wrapper = mount(ResourceMonitor, {
      global: {
        plugins: [pinia]
      }
    })

    // 等待组件加载完成
    await wrapper.vm.$nextTick()

    const cards = wrapper.findAll('.resource-card')
    expect(cards.length).toBeGreaterThan(0)

    // 检查CPU卡片
    const cpuCard = wrapper.find('[data-test="cpu-card"]')
    expect(cpuCard.exists()).toBe(true)
    expect(cpuCard.find('.card-title').text()).toContain('CPU')

    // 检查内存卡片
    const memoryCard = wrapper.find('[data-test="memory-card"]')
    expect(memoryCard.exists()).toBe(true)
    expect(memoryCard.find('.card-title').text()).toContain('内存')

    // 检查磁盘卡片
    const diskCard = wrapper.find('[data-test="disk-card"]')
    expect(diskCard.exists()).toBe(true)
    expect(diskCard.find('.card-title').text()).toContain('磁盘')
  })

  it('应该正确处理资源数据更新', async () => {
    const mockResourceData = {
      cpu: {
        usage_percent: 65.5,
        load_average: [1.2, 1.5, 1.8]
      },
      memory: {
        total: 16000000000,
        used: 9984000000,
        percent: 62.4
      },
      disk: {
        total: 500000000000,
        used: 200000000000,
        percent: 40.0
      }
    }

    wrapper = mount(ResourceMonitor, {
      global: {
        plugins: [pinia]
      }
    })

    // 模拟数据更新
    await wrapper.vm.updateResourceData(mockResourceData)

    expect(wrapper.vm.cpuUsage).toBe(65.5)
    expect(wrapper.vm.memoryUsage).toBe(62.4)
    expect(wrapper.vm.diskUsage).toBe(40.0)
  })

  it('应该正确处理告警状态', async () => {
    wrapper = mount(ResourceMonitor, {
      global: {
        plugins: [pinia]
      }
    })

    // 测试CPU高使用率告警
    const highCpuData = {
      cpu: { usage_percent: 95.0 },
      memory: { percent: 50.0 },
      disk: { percent: 30.0 }
    }

    await wrapper.vm.updateResourceData(highCpuData)

    const cpuCard = wrapper.find('[data-test="cpu-card"]')
    expect(cpuCard.classes()).toContain('alert-danger')
    
    // 测试内存高使用率告警
    const highMemoryData = {
      cpu: { usage_percent: 50.0 },
      memory: { percent: 92.0 },
      disk: { percent: 30.0 }
    }

    await wrapper.vm.updateResourceData(highMemoryData)
    
    const memoryCard = wrapper.find('[data-test="memory-card"]')
    expect(memoryCard.classes()).toContain('alert-danger')
  })

  it('应该正确切换时间范围', async () => {
    wrapper = mount(ResourceMonitor, {
      global: {
        plugins: [pinia]
      }
    })

    const timeRangeSelector = wrapper.find('[data-test="time-range-selector"]')
    expect(timeRangeSelector.exists()).toBe(true)

    // 测试切换到1小时
    await timeRangeSelector.find('[value="1h"]').trigger('click')
    expect(wrapper.vm.timeRange).toBe('1h')

    // 测试切换到24小时
    await timeRangeSelector.find('[value="24h"]').trigger('click')
    expect(wrapper.vm.timeRange).toBe('24h')
  })

  it('应该正确格式化数值显示', () => {
    wrapper = mount(ResourceMonitor, {
      global: {
        plugins: [pinia]
      }
    })

    // 测试百分比格式化
    expect(wrapper.vm.formatPercent(65.567)).toBe('65.6%')
    expect(wrapper.vm.formatPercent(100)).toBe('100.0%')

    // 测试字节格式化
    expect(wrapper.vm.formatBytes(1024)).toBe('1.0 KB')
    expect(wrapper.vm.formatBytes(1048576)).toBe('1.0 MB')
    expect(wrapper.vm.formatBytes(1073741824)).toBe('1.0 GB')
  })

  it('应该处理WebSocket连接错误', async () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
    
    wrapper = mount(ResourceMonitor, {
      global: {
        plugins: [pinia]
      }
    })

    // 模拟WebSocket错误
    wrapper.vm.handleWebSocketError(new Error('Connection failed'))

    expect(consoleSpy).toHaveBeenCalled()
    expect(wrapper.vm.connectionStatus).toBe('error')

    consoleSpy.mockRestore()
  })

  it('应该在组件卸载时清理资源', async () => {
    wrapper = mount(ResourceMonitor, {
      global: {
        plugins: [pinia]
      }
    })

    const clearIntervalSpy = vi.spyOn(window, 'clearInterval')
    const disposeSpy = vi.fn()
    
    // 模拟chart实例
    wrapper.vm.chart = { dispose: disposeSpy }
    wrapper.vm.updateTimer = 123

    wrapper.unmount()

    expect(clearIntervalSpy).toHaveBeenCalledWith(123)
    expect(disposeSpy).toHaveBeenCalled()
  })

  it('应该响应主题变化', async () => {
    wrapper = mount(ResourceMonitor, {
      global: {
        plugins: [pinia]
      }
    })

    const setOptionSpy = vi.fn()
    wrapper.vm.chart = { setOption: setOptionSpy }

    // 模拟主题变化
    await wrapper.vm.updateChartTheme('dark')

    expect(setOptionSpy).toHaveBeenCalled()
  })
})