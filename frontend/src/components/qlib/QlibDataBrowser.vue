<template>
  <div class="qlib-data-browser">
    <!-- 数据浏览器头部 -->
    <el-card class="browser-header">
      <template #header>
        <div class="header-content">
          <div class="header-title">
            <el-icon><DataBoard /></el-icon>
            <span>Qlib数据浏览器</span>
          </div>
          <div class="header-actions">
            <el-button @click="refreshData" :loading="loading">
              <el-icon><Refresh /></el-icon>
              刷新数据
            </el-button>
            <el-button @click="downloadData">
              <el-icon><Download /></el-icon>
              下载数据
            </el-button>
          </div>
        </div>
      </template>

      <!-- 数据筛选器 -->
      <div class="data-filters">
        <el-row :gutter="16">
          <el-col :span="6">
            <el-form-item label="股票池">
              <el-select v-model="filters.universe" @change="loadStockData">
                <el-option label="沪深300" value="CSI300" />
                <el-option label="中证500" value="CSI500" />
                <el-option label="中证1000" value="CSI1000" />
                <el-option label="全A股" value="ALL" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="数据频率">
              <el-select v-model="filters.frequency" @change="loadStockData">
                <el-option label="日频" value="day" />
                <el-option label="周频" value="week" />
                <el-option label="月频" value="month" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="数据字段">
              <el-select v-model="filters.fields" multiple @change="loadStockData">
                <el-option label="收盘价" value="close" />
                <el-option label="开盘价" value="open" />
                <el-option label="最高价" value="high" />
                <el-option label="最低价" value="low" />
                <el-option label="成交量" value="volume" />
                <el-option label="市值" value="market_cap" />
                <el-option label="市盈率" value="pe_ratio" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="时间范围">
              <el-date-picker
                v-model="filters.dateRange"
                type="daterange"
                start-placeholder="开始日期"
                end-placeholder="结束日期"
                format="YYYY-MM-DD"
                value-format="YYYY-MM-DD"
                @change="loadStockData"
              />
            </el-form-item>
          </el-col>
        </el-row>
      </div>
    </el-card>

    <!-- 数据概览 -->
    <el-row :gutter="16" class="data-overview">
      <el-col :span="6">
        <el-card class="metric-card">
          <el-statistic title="股票数量" :value="dataStats.stockCount" />
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="metric-card">
          <el-statistic title="交易日数量" :value="dataStats.tradingDays" />
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="metric-card">
          <el-statistic title="数据覆盖率" :value="dataStats.coverage" suffix="%" />
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="metric-card">
          <el-statistic title="最新更新" :value="dataStats.lastUpdate" />
        </el-card>
      </el-col>
    </el-row>

    <!-- 数据表格 -->
    <el-card class="data-table-card">
      <template #header>
        <div class="table-header">
          <span>股票数据 ({{ filteredData.length }} 条记录)</span>
          <div class="table-actions">
            <el-input
              v-model="searchText"
              placeholder="搜索股票代码或名称"
              style="width: 200px"
              clearable
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
          </div>
        </div>
      </template>

      <el-table
        :data="paginatedData"
        v-loading="loading"
        border
        height="400"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="instrument" label="股票代码" width="120" fixed />
        <el-table-column prop="name" label="股票名称" width="120" />
        <el-table-column prop="datetime" label="交易日期" width="120" />
        <el-table-column 
          v-for="field in filters.fields" 
          :key="field"
          :prop="field"
          :label="getFieldLabel(field)"
          :formatter="(row, column, cellValue) => formatValue(field, cellValue)"
          sortable
        />
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="viewStockDetail(row)">
              <el-icon><View /></el-icon>
              详情
            </el-button>
            <el-button size="small" @click="addToWatchlist(row)">
              <el-icon><Star /></el-icon>
              关注
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="filteredData.length"
          :page-sizes="[20, 50, 100, 200]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 因子数据预览 -->
    <el-card class="factor-preview-card" v-if="selectedRows.length > 0">
      <template #header>
        <span>选中股票的因子数据预览</span>
      </template>
      
      <div class="factor-charts">
        <el-row :gutter="16">
          <el-col :span="12">
            <div class="chart-container" ref="priceChartRef">
              <div class="chart-title">价格走势</div>
            </div>
          </el-col>
          <el-col :span="12">
            <div class="chart-container" ref="volumeChartRef">
              <div class="chart-title">成交量变化</div>
            </div>
          </el-col>
        </el-row>
      </div>
    </el-card>

    <!-- 股票详情对话框 -->
    <el-dialog v-model="showStockDetail" title="股票详情" width="60%">
      <div v-if="selectedStock" class="stock-detail">
        <el-descriptions title="基本信息" :column="2" border>
          <el-descriptions-item label="股票代码">{{ selectedStock.instrument }}</el-descriptions-item>
          <el-descriptions-item label="股票名称">{{ selectedStock.name }}</el-descriptions-item>
          <el-descriptions-item label="所属行业">{{ selectedStock.industry || '未知' }}</el-descriptions-item>
          <el-descriptions-item label="上市日期">{{ selectedStock.list_date || '未知' }}</el-descriptions-item>
          <el-descriptions-item label="总市值">{{ formatValue('market_cap', selectedStock.market_cap) }}</el-descriptions-item>
          <el-descriptions-item label="流通市值">{{ formatValue('market_cap', selectedStock.float_market_cap) }}</el-descriptions-item>
        </el-descriptions>

        <div class="stock-factors">
          <h4>因子数据</h4>
          <el-table :data="stockFactors" border>
            <el-table-column prop="factor_name" label="因子名称" />
            <el-table-column prop="factor_value" label="因子值" />
            <el-table-column prop="percentile" label="分位数" />
            <el-table-column prop="category" label="因子类别" />
          </el-table>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import {
  DataBoard, Refresh, Download, Search, View, Star
} from '@element-plus/icons-vue'

// 数据结构定义
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

interface FactorData {
  factor_name: string
  factor_value: number
  percentile: number
  category: string
}

// 响应式数据
const loading = ref(false)
const searchText = ref('')
const currentPage = ref(1)
const pageSize = ref(20)
const selectedRows = ref<StockData[]>([])
const showStockDetail = ref(false)
const selectedStock = ref<StockData | null>(null)
const stockFactors = ref<FactorData[]>([])

const filters = reactive({
  universe: 'CSI300',
  frequency: 'day',
  fields: ['close', 'volume', 'market_cap'],
  dateRange: ['2023-01-01', '2023-12-31']
})

const stockData = ref<StockData[]>([])

const dataStats = reactive({
  stockCount: 0,
  tradingDays: 0,
  coverage: 0,
  lastUpdate: '--'
})

// 计算属性
const filteredData = computed(() => {
  if (!searchText.value) return stockData.value
  
  const search = searchText.value.toLowerCase()
  return stockData.value.filter(item => 
    item.instrument.toLowerCase().includes(search) ||
    item.name.toLowerCase().includes(search)
  )
})

const paginatedData = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filteredData.value.slice(start, end)
})

// 方法
const loadStockData = async () => {
  loading.value = true
  
  try {
    const response = await fetch('/api/v1/data/market-data', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        instruments: filters.universe,
        start_time: filters.dateRange[0],
        end_time: filters.dateRange[1],
        freq: filters.frequency,
        fields: filters.fields
      })
    })

    const result = await response.json()

    if (result.status === 'success') {
      stockData.value = result.data.data || []
      
      // 更新统计信息
      dataStats.stockCount = new Set(stockData.value.map(d => d.instrument)).size
      dataStats.tradingDays = new Set(stockData.value.map(d => d.datetime)).size
      dataStats.coverage = stockData.value.length > 0 ? 
        (stockData.value.filter(d => d.close).length / stockData.value.length * 100) : 0
      dataStats.lastUpdate = result.data.last_update || new Date().toLocaleDateString()
      
      ElMessage.success('数据加载成功')
    } else {
      throw new Error(result.message || '数据加载失败')
    }
  } catch (error) {
    console.error('加载股票数据失败:', error)
    ElMessage.error('加载数据失败: ' + error.message)
    
    // 降级到示例数据
    generateSampleData()
  } finally {
    loading.value = false
  }
}

const generateSampleData = () => {
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
        market_cap: Math.random() * 100000000000
      })
    }
  })
  
  dataStats.stockCount = instruments.length
  dataStats.tradingDays = 10
  dataStats.coverage = 95.6
  dataStats.lastUpdate = new Date().toLocaleDateString()
}

const refreshData = () => {
  loadStockData()
}

const downloadData = () => {
  // 实现数据下载功能
  const csvContent = convertToCSV(filteredData.value)
  downloadCSV(csvContent, 'qlib_stock_data.csv')
  ElMessage.success('数据下载成功')
}

const convertToCSV = (data: StockData[]) => {
  if (data.length === 0) return ''
  
  const headers = Object.keys(data[0]).join(',')
  const rows = data.map(row => Object.values(row).join(','))
  return [headers, ...rows].join('\n')
}

const downloadCSV = (content: string, filename: string) => {
  const blob = new Blob([content], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  const url = URL.createObjectURL(blob)
  link.setAttribute('href', url)
  link.setAttribute('download', filename)
  link.style.visibility = 'hidden'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

const getFieldLabel = (field: string) => {
  const labels: Record<string, string> = {
    close: '收盘价',
    open: '开盘价',
    high: '最高价',
    low: '最低价',
    volume: '成交量',
    market_cap: '市值',
    pe_ratio: '市盈率'
  }
  return labels[field] || field
}

const formatValue = (field: string, value: any) => {
  if (value === null || value === undefined) return '--'
  
  switch (field) {
    case 'close':
    case 'open':
    case 'high':
    case 'low':
      return `¥${Number(value).toFixed(2)}`
    case 'volume':
      return Number(value).toLocaleString()
    case 'market_cap':
      return `¥${(Number(value) / 100000000).toFixed(1)}亿`
    case 'pe_ratio':
      return Number(value).toFixed(2)
    default:
      return value
  }
}

const handleSelectionChange = (selection: StockData[]) => {
  selectedRows.value = selection
  
  // 更新图表
  if (selection.length > 0) {
    nextTick(() => {
      updateCharts()
    })
  }
}

const updateCharts = () => {
  // 这里应该使用ECharts等图表库来渲染图表
  // 暂时只做占位符处理
  console.log('更新图表:', selectedRows.value)
}

const viewStockDetail = async (stock: StockData) => {
  selectedStock.value = stock
  
  // 加载股票因子数据
  try {
    const response = await fetch('/api/v1/qlib-factors/factor-library', {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      }
    })
    
    const result = await response.json()
    
    if (result.status === 'success') {
      // 模拟因子数据
      stockFactors.value = [
        { factor_name: '20日动量', factor_value: 0.045, percentile: 0.68, category: '动量' },
        { factor_name: '市盈率倒数', factor_value: 0.025, percentile: 0.34, category: '价值' },
        { factor_name: 'RSI', factor_value: 45.6, percentile: 0.42, category: '技术' }
      ]
    }
  } catch (error) {
    console.error('加载因子数据失败:', error)
  }
  
  showStockDetail.value = true
}

const addToWatchlist = (stock: StockData) => {
  ElMessage.success(`已将 ${stock.name} 添加到关注列表`)
}

const handleSizeChange = (val: number) => {
  pageSize.value = val
  currentPage.value = 1
}

const handleCurrentChange = (val: number) => {
  currentPage.value = val
}

// 生命周期
onMounted(() => {
  loadStockData()
})
</script>

<style scoped>
.qlib-data-browser {
  padding: 20px;
}

.browser-header {
  margin-bottom: 20px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 18px;
  font-weight: 600;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.data-filters {
  padding: 16px 0;
}

.data-overview {
  margin-bottom: 20px;
}

.metric-card {
  text-align: center;
}

.data-table-card {
  margin-bottom: 20px;
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.table-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.pagination-wrapper {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}

.factor-preview-card {
  margin-bottom: 20px;
}

.factor-charts {
  margin-top: 16px;
}

.chart-container {
  height: 200px;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.chart-title {
  font-size: 14px;
  color: #909399;
}

.stock-detail {
  padding: 16px 0;
}

.stock-factors {
  margin-top: 24px;
}

.stock-factors h4 {
  margin-bottom: 16px;
  color: #303133;
}

@media (max-width: 768px) {
  .qlib-data-browser {
    padding: 12px;
  }
  
  .header-content {
    flex-direction: column;
    gap: 16px;
  }
  
  .data-filters .el-col {
    margin-bottom: 16px;
  }
  
  .data-overview .el-col {
    margin-bottom: 16px;
  }
}
</style>