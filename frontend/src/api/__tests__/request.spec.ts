import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import axios from 'axios'
import MockAdapter from 'axios-mock-adapter'
import { ElMessage } from 'element-plus'

// 模拟Element Plus的消息组件
vi.mock('element-plus', () => ({
  ElMessage: {
    error: vi.fn(),
    success: vi.fn(),
    warning: vi.fn(),
  },
}))

// 模拟环境变量
vi.mock('import.meta.env', () => ({
  VITE_API_BASE_URL: 'http://localhost:8000/api',
  DEV: true,
}))

describe('API Request 拦截器', () => {
  let mock: MockAdapter
  
  beforeEach(() => {
    // 动态导入request模块之前设置mock
    mock = new MockAdapter(axios)
    vi.clearAllMocks()
  })
  
  afterEach(() => {
    mock.restore()
  })
  
  it('应该正确处理成功的API响应', async () => {
    const responseData = { success: true, data: { id: 123 }, message: '成功' }
    mock.onGet('/test').reply(200, responseData)
    
    // 动态导入request模块
    const requestModule = await import('../request')
    const request = requestModule.default
    
    const response = await request.get('/test')
    
    expect(response.data).toEqual(responseData)
    expect(response.status).toBe(200)
  })
  
  it('应该正确处理API业务失败响应', async () => {
    const responseData = { success: false, message: '业务错误' }
    mock.onGet('/test').reply(200, responseData)
    
    const requestModule = await import('../request')
    const request = requestModule.default
    
    await expect(request.get('/test')).rejects.toThrow('业务错误')
    expect(ElMessage.error).toHaveBeenCalledWith('业务错误')
  })
  
  it('应该正确处理400错误响应', async () => {
    mock.onGet('/test').reply(400, { message: '请求参数错误' })
    
    const requestModule = await import('../request')
    const request = requestModule.default
    
    await expect(request.get('/test')).rejects.toThrow()
    expect(ElMessage.error).toHaveBeenCalledWith('请求参数错误')
  })
  
  it('应该正确处理401未授权响应', async () => {
    mock.onGet('/test').reply(401, { message: '未授权' })
    
    const requestModule = await import('../request')
    const request = requestModule.default
    
    await expect(request.get('/test')).rejects.toThrow()
    expect(ElMessage.error).toHaveBeenCalledWith('未授权，请重新登录')
  })
  
  it('应该正确处理403禁止访问响应', async () => {
    mock.onGet('/test').reply(403)
    
    const requestModule = await import('../request')
    const request = requestModule.default
    
    await expect(request.get('/test')).rejects.toThrow()
    expect(ElMessage.error).toHaveBeenCalledWith('访问被拒绝')
  })
  
  it('应该正确处理404不存在响应', async () => {
    mock.onGet('/test').reply(404)
    
    const requestModule = await import('../request')
    const request = requestModule.default
    
    await expect(request.get('/test')).rejects.toThrow()
    expect(ElMessage.error).toHaveBeenCalledWith('请求的资源不存在')
  })
  
  it('应该正确处理500服务器错误响应', async () => {
    mock.onGet('/test').reply(500)
    
    const requestModule = await import('../request')
    const request = requestModule.default
    
    await expect(request.get('/test')).rejects.toThrow()
    expect(ElMessage.error).toHaveBeenCalledWith('服务器内部错误')
  })
  
  it('应该正确处理网络连接失败', async () => {
    mock.onGet('/test').networkError()
    
    const requestModule = await import('../request')
    const request = requestModule.default
    
    await expect(request.get('/test')).rejects.toThrow()
    expect(ElMessage.error).toHaveBeenCalledWith('网络连接失败，请检查网络')
  })
  
  it('应该正确处理请求超时', async () => {
    mock.onGet('/test').timeout()
    
    const requestModule = await import('../request')
    const request = requestModule.default
    
    await expect(request.get('/test')).rejects.toThrow()
    expect(ElMessage.error).toHaveBeenCalledWith('网络连接失败，请检查网络')
  })
  
  it('应该在开发环境输出日志', async () => {
    const consoleSpy = vi.spyOn(console, 'log').mockImplementation(() => {})
    
    mock.onGet('/test').reply(200, { success: true, data: {} })
    
    const requestModule = await import('../request')
    const request = requestModule.default
    
    await request.get('/test')
    
    // 在开发环境应该输出请求和响应日志
    expect(consoleSpy).toHaveBeenCalled()
    
    consoleSpy.mockRestore()
  })
  
  it('应该正确设置请求配置', async () => {
    const requestModule = await import('../request')
    const request = requestModule.default
    
    expect(request.defaults.timeout).toBe(30000)
    expect(request.defaults.headers['Content-Type']).toBe('application/json')
  })
})