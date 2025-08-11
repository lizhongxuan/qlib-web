/**
 * NotificationCenter组件测试
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, VueWrapper } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { ElNotification, ElMessage } from 'element-plus'
import NotificationCenter from '../notification/NotificationCenter.vue'

// Mock Element Plus组件
vi.mock('element-plus', () => ({
  ElNotification: {
    success: vi.fn(),
    warning: vi.fn(),
    error: vi.fn(),
    info: vi.fn(),
    close: vi.fn(),
    closeAll: vi.fn()
  },
  ElMessage: {
    success: vi.fn(),
    warning: vi.fn(),
    error: vi.fn(),
    info: vi.fn()
  }
}))

// Mock API请求
vi.mock('@/api/request', () => ({
  apiRequest: vi.fn()
}))

// Mock浏览器通知API
Object.defineProperty(global, 'Notification', {
  value: class MockNotification {
    static permission = 'granted'
    static requestPermission = vi.fn().mockResolvedValue('granted')
    constructor(title: string, options?: any) {
      this.title = title
      this.body = options?.body
      this.icon = options?.icon
      this.onclick = options?.onclick
      this.onclose = options?.onclose
    }
    close = vi.fn()
    title: string
    body?: string
    icon?: string
    onclick?: () => void
    onclose?: () => void
  },
  configurable: true
})

describe('NotificationCenter', () => {
  let wrapper: VueWrapper<any>
  let pinia: any

  const mockNotifications = [
    {
      id: '1',
      type: 'experiment_completed',
      title: '实验完成',
      message: '您的实验已成功完成',
      is_read: false,
      created_at: '2024-08-08T10:30:00Z',
      priority: 'high'
    },
    {
      id: '2',
      type: 'system_maintenance',
      title: '系统维护通知',
      message: '系统将在今晚进行维护',
      is_read: true,
      created_at: '2024-08-08T09:00:00Z',
      priority: 'medium'
    },
    {
      id: '3',
      type: 'experiment_failed',
      title: '实验失败',
      message: '您的实验执行失败，请检查配置',
      is_read: false,
      created_at: '2024-08-08T08:15:00Z',
      priority: 'high'
    }
  ]

  beforeEach(() => {
    pinia = createPinia()
    setActivePinia(pinia)
    
    vi.clearAllMocks()
  })

  afterEach(() => {
    if (wrapper) {
      wrapper.unmount()
    }
  })

  it('应该正确渲染通知中心', () => {
    wrapper = mount(NotificationCenter, {
      global: {
        plugins: [pinia]
      },
      props: {
        notifications: mockNotifications
      }
    })

    expect(wrapper.find('.notification-center').exists()).toBe(true)
    expect(wrapper.find('.notification-header').exists()).toBe(true)
    expect(wrapper.find('.notification-list').exists()).toBe(true)
  })

  it('应该显示正确的通知数量', () => {
    wrapper = mount(NotificationCenter, {
      global: {
        plugins: [pinia]
      },
      props: {
        notifications: mockNotifications
      }
    })

    const notificationItems = wrapper.findAll('.notification-item')
    expect(notificationItems).toHaveLength(3)

    // 检查未读通知数量
    const unreadCount = wrapper.find('[data-test="unread-count"]')
    expect(unreadCount.text()).toBe('2') // 2个未读通知
  })

  it('应该正确显示通知内容', () => {
    wrapper = mount(NotificationCenter, {
      global: {
        plugins: [pinia]
      },
      props: {
        notifications: mockNotifications
      }
    })

    const firstNotification = wrapper.find('[data-test="notification-0"]')
    expect(firstNotification.find('.notification-title').text()).toBe('实验完成')
    expect(firstNotification.find('.notification-message').text()).toBe('您的实验已成功完成')
    expect(firstNotification.classes()).toContain('unread')

    const secondNotification = wrapper.find('[data-test="notification-1"]')
    expect(secondNotification.classes()).toContain('read')
  })

  it('应该正确处理通知类型和图标', () => {
    wrapper = mount(NotificationCenter, {
      global: {
        plugins: [pinia]
      },
      props: {
        notifications: mockNotifications
      }
    })

    // 实验完成通知
    const completedNotification = wrapper.find('[data-test="notification-0"]')
    const completedIcon = completedNotification.find('.notification-icon')
    expect(completedIcon.classes()).toContain('success')

    // 实验失败通知
    const failedNotification = wrapper.find('[data-test="notification-2"]')
    const failedIcon = failedNotification.find('.notification-icon')
    expect(failedIcon.classes()).toContain('error')
  })

  it('应该支持标记通知为已读', async () => {
    const mockMarkAsRead = vi.fn().mockResolvedValue(true)
    
    wrapper = mount(NotificationCenter, {
      global: {
        plugins: [pinia]
      },
      props: {
        notifications: mockNotifications,
        onMarkAsRead: mockMarkAsRead
      }
    })

    const firstNotification = wrapper.find('[data-test="notification-0"]')
    const markAsReadBtn = firstNotification.find('.mark-read-btn')
    
    await markAsReadBtn.trigger('click')
    
    expect(mockMarkAsRead).toHaveBeenCalledWith('1')
  })

  it('应该支持删除通知', async () => {
    const mockDeleteNotification = vi.fn().mockResolvedValue(true)
    
    wrapper = mount(NotificationCenter, {
      global: {
        plugins: [pinia]
      },
      props: {
        notifications: mockNotifications,
        onDelete: mockDeleteNotification
      }
    })

    const firstNotification = wrapper.find('[data-test="notification-0"]')
    const deleteBtn = firstNotification.find('.delete-btn')
    
    await deleteBtn.trigger('click')
    
    expect(mockDeleteNotification).toHaveBeenCalledWith('1')
  })

  it('应该支持全部标记为已读', async () => {
    const mockMarkAllAsRead = vi.fn().mockResolvedValue(true)
    
    wrapper = mount(NotificationCenter, {
      global: {
        plugins: [pinia]
      },
      props: {
        notifications: mockNotifications,
        onMarkAllAsRead: mockMarkAllAsRead
      }
    })

    const markAllBtn = wrapper.find('[data-test="mark-all-read"]')
    await markAllBtn.trigger('click')
    
    expect(mockMarkAllAsRead).toHaveBeenCalled()
  })

  it('应该支持清空所有通知', async () => {
    const mockClearAll = vi.fn().mockResolvedValue(true)
    
    wrapper = mount(NotificationCenter, {
      global: {
        plugins: [pinia]
      },
      props: {
        notifications: mockNotifications,
        onClearAll: mockClearAll
      }
    })

    const clearAllBtn = wrapper.find('[data-test="clear-all"]')
    await clearAllBtn.trigger('click')
    
    expect(mockClearAll).toHaveBeenCalled()
  })

  it('应该支持按类型筛选通知', async () => {
    wrapper = mount(NotificationCenter, {
      global: {
        plugins: [pinia]
      },
      props: {
        notifications: mockNotifications
      }
    })

    const typeFilter = wrapper.find('[data-test="type-filter"]')
    
    // 筛选实验相关通知
    await typeFilter.setValue('experiment')
    
    const filteredItems = wrapper.findAll('.notification-item:not(.hidden)')
    expect(filteredItems.length).toBe(2) // 2个实验相关通知
  })

  it('应该支持按状态筛选通知', async () => {
    wrapper = mount(NotificationCenter, {
      global: {
        plugins: [pinia]
      },
      props: {
        notifications: mockNotifications
      }
    })

    const statusFilter = wrapper.find('[data-test="status-filter"]')
    
    // 筛选未读通知
    await statusFilter.setValue('unread')
    
    const filteredItems = wrapper.findAll('.notification-item:not(.hidden)')
    expect(filteredItems.length).toBe(2) // 2个未读通知
  })

  it('应该正确请求浏览器通知权限', async () => {
    wrapper = mount(NotificationCenter, {
      global: {
        plugins: [pinia]
      }
    })

    const requestPermissionSpy = vi.spyOn(Notification, 'requestPermission')
    
    await wrapper.vm.requestNotificationPermission()
    
    expect(requestPermissionSpy).toHaveBeenCalled()
    expect(wrapper.vm.browserNotificationEnabled).toBe(true)
  })

  it('应该正确发送浏览器通知', async () => {
    wrapper = mount(NotificationCenter, {
      global: {
        plugins: [pinia]
      }
    })

    const notification = mockNotifications[0]
    
    const browserNotification = await wrapper.vm.showBrowserNotification(notification)
    
    expect(browserNotification).toBeInstanceOf(Notification)
    expect(browserNotification.title).toBe('实验完成')
    expect(browserNotification.body).toBe('您的实验已成功完成')
  })

  it('应该正确处理WebSocket实时通知', async () => {
    const mockWebSocketMessage = {
      type: 'notification',
      data: {
        id: '4',
        type: 'experiment_started',
        title: '实验开始',
        message: '您的新实验已开始执行',
        priority: 'medium'
      }
    }

    wrapper = mount(NotificationCenter, {
      global: {
        plugins: [pinia]
      },
      props: {
        notifications: []
      }
    })

    await wrapper.vm.handleWebSocketMessage(mockWebSocketMessage)

    expect(wrapper.emitted('new-notification')).toBeTruthy()
    expect(wrapper.emitted('new-notification')[0][0]).toEqual(mockWebSocketMessage.data)
  })

  it('应该正确处理通知设置', async () => {
    const mockSettings = {
      browserNotifications: true,
      emailNotifications: false,
      experimentNotifications: true,
      systemNotifications: true,
      sound: true
    }

    wrapper = mount(NotificationCenter, {
      global: {
        plugins: [pinia]
      },
      props: {
        settings: mockSettings
      }
    })

    expect(wrapper.vm.notificationSettings.browserNotifications).toBe(true)
    expect(wrapper.vm.notificationSettings.emailNotifications).toBe(false)
    
    // 测试设置更新
    await wrapper.vm.updateSettings({ emailNotifications: true })
    
    expect(wrapper.emitted('settings-updated')).toBeTruthy()
  })

  it('应该正确计算时间显示', () => {
    wrapper = mount(NotificationCenter, {
      global: {
        plugins: [pinia]
      }
    })

    const now = new Date()
    const oneHourAgo = new Date(now.getTime() - 60 * 60 * 1000)
    const oneDayAgo = new Date(now.getTime() - 24 * 60 * 60 * 1000)

    expect(wrapper.vm.formatTimeAgo(oneHourAgo.toISOString())).toBe('1小时前')
    expect(wrapper.vm.formatTimeAgo(oneDayAgo.toISOString())).toBe('1天前')
  })

  it('应该正确处理空通知列表', () => {
    wrapper = mount(NotificationCenter, {
      global: {
        plugins: [pinia]
      },
      props: {
        notifications: []
      }
    })

    const emptyState = wrapper.find('[data-test="empty-state"]')
    expect(emptyState.exists()).toBe(true)
    expect(emptyState.text()).toContain('暂无通知')
  })

  it('应该正确处理通知加载状态', async () => {
    wrapper = mount(NotificationCenter, {
      global: {
        plugins: [pinia]
      },
      props: {
        loading: true
      }
    })

    const loadingIndicator = wrapper.find('[data-test="loading"]')
    expect(loadingIndicator.exists()).toBe(true)

    await wrapper.setProps({ loading: false })
    expect(wrapper.find('[data-test="loading"]').exists()).toBe(false)
  })
})