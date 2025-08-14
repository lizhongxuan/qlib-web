import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

// Qlib数据相关的类型定义
interface StockData {
  instrument: string
  name: string
  datetime: string
  close?: number
  open?: number
  high?: number
  low?: number
  volume?: number
  market_cap?: number
  pe_ratio?: number
  industry?: string
  list_date?: string
  float_market_cap?: number
}

interface DataQueryParams {
  instruments: string
  start_time: string
  end_time: string
  freq: string
  fields: string[]
}

interface DataStats {
  stockCount: number
  tradingDays: number
  coverage: number
  lastUpdate: string
}

interface CacheEntry {
  data: any
  timestamp: number
  expiry: number
}

export const useQlibDataStore = defineStore('qlib-data', () => {
  // 状态
  const stockData = ref<StockData[]>([])
  const dataStats = ref<DataStats>({
    stockCount: 0,
    tradingDays: 0,
    coverage: 0,
    lastUpdate: ''
  })
  const loading = ref(false)
  const error = ref<string | null>(null)
  const lastQuery = ref<DataQueryParams | null>(null)
  
  // 数据缓存（内存缓存）
  const dataCache = ref<Map<string, CacheEntry>>(new Map())
  const cacheTimeout = 5 * 60 * 1000 // 5分钟缓存

  // 计算属性
  const hasData = computed(() => stockData.value.length > 0)
  const uniqueInstruments = computed(() => 
    [...new Set(stockData.value.map(d => d.instrument))]
  )
  const uniqueTradingDays = computed(() => 
    [...new Set(stockData.value.map(d => d.datetime))]
  )
  const latestTradingDay = computed(() => {
    if (stockData.value.length === 0) return ''
    const dates = uniqueTradingDays.value.sort()
    return dates[dates.length - 1]
  })

  // 缓存相关方法
  const getCacheKey = (params: DataQueryParams): string => {
    return JSON.stringify(params)
  }

  const getCachedData = (key: string): any | null => {
    const entry = dataCache.value.get(key)
    if (!entry) return null
    
    if (Date.now() > entry.expiry) {
      dataCache.value.delete(key)
      return null
    }
    
    return entry.data
  }

  const setCachedData = (key: string, data: any): void => {
    dataCache.value.set(key, {
      data,
      timestamp: Date.now(),
      expiry: Date.now() + cacheTimeout
    })
  }

  const clearExpiredCache = (): void => {
    const now = Date.now()
    for (const [key, entry] of dataCache.value.entries()) {
      if (now > entry.expiry) {
        dataCache.value.delete(key)
      }
    }
  }

  // Actions
  const loadMarketData = async (params: DataQueryParams): Promise<void> => {
    // 检查缓存
    const cacheKey = getCacheKey(params)
    const cachedData = getCachedData(cacheKey)
    
    if (cachedData) {
      stockData.value = cachedData.data || []
      updateDataStats()
      lastQuery.value = params
      return
    }

    loading.value = true
    error.value = null

    try {
      const response = await fetch('/api/v1/data/market-data', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(params)
      })

      const result = await response.json()

      if (result.status === 'success') {
        stockData.value = result.data.data || []
        updateDataStats()
        lastQuery.value = params
        
        // 缓存数据
        setCachedData(cacheKey, result.data)
        
        // 清理过期缓存
        clearExpiredCache()
      } else {
        throw new Error(result.message || '加载市场数据失败')
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : '加载数据失败'
      console.error('加载市场数据失败:', err)
      
      // 在错误情况下生成示例数据
      generateSampleData()
    } finally {
      loading.value = false
    }
  }

  const generateSampleData = (): void => {
    const instruments = ['000001.SZ', '000002.SZ', '600000.SH', '600036.SH', '000858.SZ']
    const names = ['平安银行', '万科A', '浦发银行', '招商银行', '五粮液']
    
    stockData.value = []
    
    instruments.forEach((instrument, index) => {
      for (let i = 0; i < 10; i++) {
        const date = new Date(2023, 0, i + 1)
        stockData.value.push({
          instrument,
          name: names[index],
          datetime: date.toISOString().split('T')[0],
          close: Math.random() * 100 + 10,
          volume: Math.random() * 1000000,
          market_cap: Math.random() * 100000000000,
          industry: ['金融', '地产', '消费', '科技', '医药'][index]
        })
      }
    })
    
    updateDataStats()
  }

  const updateDataStats = (): void => {
    dataStats.value = {
      stockCount: uniqueInstruments.value.length,
      tradingDays: uniqueTradingDays.value.length,
      coverage: stockData.value.length > 0 ? 
        (stockData.value.filter(d => d.close).length / stockData.value.length * 100) : 0,
      lastUpdate: new Date().toLocaleDateString()
    }
  }

  const getStockByInstrument = (instrument: string): StockData[] => {
    return stockData.value.filter(d => d.instrument === instrument)
  }

  const getDataByDateRange = (startDate: string, endDate: string): StockData[] => {
    return stockData.value.filter(d => 
      d.datetime >= startDate && d.datetime <= endDate
    )
  }

  const getInstrumentsByIndustry = (industry: string): string[] => {
    const filtered = stockData.value.filter(d => d.industry === industry)
    return [...new Set(filtered.map(d => d.instrument))]
  }

  const refreshData = async (): Promise<void> => {
    if (lastQuery.value) {
      // 清除缓存强制刷新
      const cacheKey = getCacheKey(lastQuery.value)
      dataCache.value.delete(cacheKey)
      await loadMarketData(lastQuery.value)
    }
  }

  const clearData = (): void => {
    stockData.value = []
    dataStats.value = {
      stockCount: 0,
      tradingDays: 0,
      coverage: 0,
      lastUpdate: ''
    }
    error.value = null
    lastQuery.value = null
  }

  const clearCache = (): void => {
    dataCache.value.clear()
  }

  // 导出数据功能
  const exportToCSV = (): string => {
    if (stockData.value.length === 0) return ''
    
    const headers = Object.keys(stockData.value[0]).join(',')
    const rows = stockData.value.map(row => Object.values(row).join(','))
    return [headers, ...rows].join('\n')
  }

  const downloadCSV = (filename: string = 'qlib_stock_data.csv'): void => {
    const csvContent = exportToCSV()
    if (!csvContent) return
    
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    const url = URL.createObjectURL(blob)
    link.setAttribute('href', url)
    link.setAttribute('download', filename)
    link.style.visibility = 'hidden'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  return {
    // State
    stockData,
    dataStats,
    loading,
    error,
    lastQuery,
    
    // Computed
    hasData,
    uniqueInstruments,
    uniqueTradingDays,
    latestTradingDay,
    
    // Actions
    loadMarketData,
    generateSampleData,
    updateDataStats,
    getStockByInstrument,
    getDataByDateRange,
    getInstrumentsByIndustry,
    refreshData,
    clearData,
    clearCache,
    exportToCSV,
    downloadCSV
  }
})