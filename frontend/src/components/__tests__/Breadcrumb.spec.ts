import { describe, it, expect, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createRouter, createWebHistory } from 'vue-router'
import Breadcrumb from '../Breadcrumb.vue'

// 创建模拟路由
const createMockRouter = (path = '/') => {
  const router = createRouter({
    history: createWebHistory(),
    routes: [
      { path: '/', name: 'home', component: { template: '<div>Home</div>' } },
      { path: '/dashboard', name: 'dashboard', component: { template: '<div>Dashboard</div>' } },
      { path: '/experiments/new', name: 'new-experiment', component: { template: '<div>New</div>' } },
      { path: '/experiments', name: 'experiments', component: { template: '<div>List</div>' } },
      { path: '/experiments/:id', name: 'experiment-detail', component: { template: '<div>Detail</div>' } },
      { path: '/settings', name: 'settings', component: { template: '<div>Settings</div>' } },
    ],
  })
  
  router.push(path)
  return router
}

describe('Breadcrumb组件', () => {
  it('应该正确渲染首页面包屑', async () => {
    const router = createMockRouter('/')
    const wrapper = mount(Breadcrumb, {
      global: {
        plugins: [router],
      },
    })
    
    await router.isReady()
    
    expect(wrapper.text()).toContain('首页')
  })
  
  it('应该正确渲染仪表盘面包屑', async () => {
    const router = createMockRouter('/dashboard')
    const wrapper = mount(Breadcrumb, {
      global: {
        plugins: [router],
      },
    })
    
    await router.isReady()
    
    expect(wrapper.text()).toContain('仪表盘')
  })
  
  it('应该正确渲染新建实验面包屑', async () => {
    const router = createMockRouter('/experiments/new')
    const wrapper = mount(Breadcrumb, {
      global: {
        plugins: [router],
      },
    })
    
    await router.isReady()
    
    const text = wrapper.text()
    expect(text).toContain('仪表盘')
    expect(text).toContain('新建实验')
  })
  
  it('应该正确渲染实验列表面包屑', async () => {
    const router = createMockRouter('/experiments')
    const wrapper = mount(Breadcrumb, {
      global: {
        plugins: [router],
      },
    })
    
    await router.isReady()
    
    const text = wrapper.text()
    expect(text).toContain('仪表盘')
    expect(text).toContain('历史记录')
  })
  
  it('应该正确渲染实验详情面包屑', async () => {
    const router = createMockRouter('/experiments/test-exp-123456')
    const wrapper = mount(Breadcrumb, {
      global: {
        plugins: [router],
      },
    })
    
    await router.isReady()
    
    const text = wrapper.text()
    expect(text).toContain('仪表盘')
    expect(text).toContain('历史记录')
    expect(text).toContain('实验详情')
    expect(text).toContain('test-exp-')
  })
  
  it('应该正确渲染设置页面包屑', async () => {
    const router = createMockRouter('/settings')
    const wrapper = mount(Breadcrumb, {
      global: {
        plugins: [router],
      },
    })
    
    await router.isReady()
    
    const text = wrapper.text()
    expect(text).toContain('仪表盘')
    expect(text).toContain('系统设置')
  })
  
  it('应该为未知路径提供默认面包屑', async () => {
    const router = createMockRouter('/unknown-path')
    const wrapper = mount(Breadcrumb, {
      global: {
        plugins: [router],
      },
    })
    
    await router.isReady()
    
    expect(wrapper.text()).toContain('仪表盘')
  })
  
  it('应该渲染正确的图标', async () => {
    const router = createMockRouter('/dashboard')
    const wrapper = mount(Breadcrumb, {
      global: {
        plugins: [router],
      },
    })
    
    await router.isReady()
    
    // 检查是否有图标元素
    expect(wrapper.find('.breadcrumb-icon').exists()).toBe(true)
  })
})