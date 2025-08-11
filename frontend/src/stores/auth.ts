import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from '@/api'
import type { User, LoginCredentials, RegisterData, Token } from '@/types/auth'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('token'))
  const refreshToken = ref<string | null>(localStorage.getItem('refresh_token'))
  const getUserFromStorage = (): User | null => {
    try {
      const savedUser = localStorage.getItem('user')
      return savedUser ? JSON.parse(savedUser) : null
    } catch (error) {
      console.warn('Failed to parse user from localStorage:', error)
      return null
    }
  }
  const user = ref<User | null>(getUserFromStorage())
  const loading = ref(false)

  // 计算属性
  const isAuthenticated = computed(() => !!token.value && !!user.value)
  const isAdmin = computed(() => user.value?.role === 'admin')
  const isManager = computed(() => user.value?.role === 'manager' || isAdmin.value)

  // 设置认证信息
  const setAuth = (tokenData: Token, userData: User) => {
    token.value = tokenData.access_token
    refreshToken.value = tokenData.refresh_token
    user.value = userData
    
    localStorage.setItem('token', tokenData.access_token)
    localStorage.setItem('user', JSON.stringify(userData))
    if (tokenData.refresh_token) {
      localStorage.setItem('refresh_token', tokenData.refresh_token)
    }
    
    // 设置 API 默认请求头
    api.defaults.headers.common['Authorization'] = `Bearer ${tokenData.access_token}`
  }

  // 清除认证信息
  const clearAuth = () => {
    token.value = null
    refreshToken.value = null
    user.value = null
    
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    localStorage.removeItem('refresh_token')
    
    // 清除 API 请求头
    delete api.defaults.headers.common['Authorization']
  }

  // 登录
  const login = async (credentials: LoginCredentials) => {
    loading.value = true
    
    try {
      const response = await api.post('/auth/login', credentials)
      const { access_token, token_type, expires_in, user: userData } = response.data
      
      const tokenData: Token = {
        access_token,
        refresh_token: null, // 后端暂时没有refresh_token
        token_type,
        expires_in
      }
      
      setAuth(tokenData, userData)
      return response.data
    } catch (error: any) {
      clearAuth()
      throw new Error(error.response?.data?.detail || '登录失败')
    } finally {
      loading.value = false
    }
  }

  // 注册
  const register = async (userData: RegisterData) => {
    loading.value = true
    
    try {
      const response = await api.post('/auth/register', userData)
      return response.data
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || '注册失败')
    } finally {
      loading.value = false
    }
  }

  // 登出
  const logout = async () => {
    try {
      if (token.value) {
        await api.post('/auth/logout')
      }
    } catch (error) {
      console.error('登出请求失败:', error)
    } finally {
      clearAuth()
    }
  }

  // 刷新令牌
  const refreshAccessToken = async () => {
    if (!refreshToken.value) {
      throw new Error('没有刷新令牌')
    }
    
    try {
      const response = await api.post('/auth/refresh', {
        refresh_token: refreshToken.value
      })
      
      const { access_token, refresh_token: newRefreshToken } = response.data
      
      token.value = access_token
      if (newRefreshToken) {
        refreshToken.value = newRefreshToken
        localStorage.setItem('refresh_token', newRefreshToken)
      }
      
      localStorage.setItem('auth_token', access_token)
      api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`
      
      return access_token
    } catch (error) {
      clearAuth()
      throw error
    }
  }

  // 获取当前用户信息
  const fetchCurrentUser = async () => {
    if (!token.value) return null
    
    try {
      const response = await api.get('/auth/me')
      user.value = response.data
      return response.data
    } catch (error) {
      clearAuth()
      throw error
    }
  }

  // 更新用户信息
  const updateProfile = async (profileData: Partial<User>) => {
    loading.value = true
    
    try {
      const response = await api.put('/auth/profile', profileData)
      user.value = { ...user.value, ...response.data }
      return response.data
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || '更新失败')
    } finally {
      loading.value = false
    }
  }

  // 修改密码
  const changePassword = async (oldPassword: string, newPassword: string) => {
    loading.value = true
    
    try {
      await api.post('/auth/change-password', {
        current_password: oldPassword,
        new_password: newPassword
      })
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || '密码修改失败')
    } finally {
      loading.value = false
    }
  }

  // 忘记密码
  const forgotPassword = async (email: string) => {
    loading.value = true
    
    try {
      await api.post('/auth/forgot-password', { email })
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || '发送失败')
    } finally {
      loading.value = false
    }
  }

  // 重置密码
  const resetPassword = async (token: string, newPassword: string) => {
    loading.value = true
    
    try {
      await api.post('/auth/reset-password', {
        token,
        new_password: newPassword
      })
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || '重置失败')
    } finally {
      loading.value = false
    }
  }

  // 验证邮箱
  const verifyEmail = async (token: string) => {
    loading.value = true
    
    try {
      await api.post('/auth/verify-email', { token })
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || '验证失败')
    } finally {
      loading.value = false
    }
  }

  // 初始化认证状态
  const initAuth = async () => {
    if (token.value) {
      api.defaults.headers.common['Authorization'] = `Bearer ${token.value}`
      
      // 如果没有用户信息，尝试获取
      if (!user.value) {
        try {
          await fetchCurrentUser()
        } catch (error) {
          clearAuth()
        }
      }
    }
  }

  return {
    // State
    token: computed(() => token.value),
    user: computed(() => user.value),
    loading: computed(() => loading.value),
    
    // Getters
    isAuthenticated,
    isAdmin,
    isManager,
    
    // Actions
    login,
    register,
    logout,
    refreshAccessToken,
    fetchCurrentUser,
    updateProfile,
    changePassword,
    forgotPassword,
    resetPassword,
    verifyEmail,
    initAuth,
    setAuth,
    clearAuth
  }
})