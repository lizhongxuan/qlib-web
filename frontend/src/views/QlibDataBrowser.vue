<template>
  <div class="qlib-data-browser">
    <!-- 顶部工具栏 -->
    <div class="toolbar">
      <div class="toolbar-left">
        <h1 class="page-title">
          <el-icon><DataBoard /></el-icon>
          Qlib数据浏览器
        </h1>
        <el-breadcrumb separator="/">
          <el-breadcrumb-item :to="{ path: '/qlib-dashboard' }">Qlib中心</el-breadcrumb-item>
          <el-breadcrumb-item>数据浏览器</el-breadcrumb-item>
        </el-breadcrumb>
      </div>
      <div class="toolbar-right">
        <el-button-group>
          <el-button @click="refreshData" :loading="loading">
            <el-icon><Refresh /></el-icon>
            刷新数据
          </el-button>
          <el-button @click="exportData" :disabled="!hasData">
            <el-icon><Download /></el-icon>
            导出数据
          </el-button>
        </el-button-group>
      </div>
    </div>

    <!-- 数据查询面板 -->
    <el-card class="query-panel" shadow="never">
      <template #header>
        <div class="panel-header">
          <el-icon><Search /></el-icon>
          <span>数据查询</span>
          <el-tag v-if="hasData" type="success" size="small">
            {{ stockData.length }} 条记录
          </el-tag>
        </div>
      </template>
      
      <el-form :model="queryForm" label-width="80px" class="query-form">
        <el-row :gutter="24">
          <el-col :span="6">
            <el-form-item label="股票池">
              <el-select v-model="queryForm.instruments" placeholder="选择股票池">
                <el-option label="沪深300" value="CSI300" />
                <el-option label="中证500" value="CSI500" />
                <el-option label="中证800" value="CSI800" />
                <el-option label="中证1000" value="CSI1000" />
                <el-option label="全市场" value="ALL" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="时间范围">
              <el-date-picker
                v-model="queryForm.dateRange"
                type="daterange"
                range-separator="至"
                start-placeholder="开始日期"
                end-placeholder="结束日期"
                format="YYYY-MM-DD"
                value-format="YYYY-MM-DD"
              />
            </el-form-item>
          </el-col>
          <el-col :span="4">
            <el-form-item label="数据频率">
              <el-select v-model="queryForm.freq" placeholder="选择频率">
                <el-option label="日频" value="day" />
                <el-option label="周频" value="week" />
                <el-option label="月频" value="month" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item>
              <el-button-group>
                <el-button type="primary" @click="queryData" :loading="loading">
                  <el-icon><Search /></el-icon>
                  查询数据
                </el-button>
                <el-button @click="resetQuery">
                  <el-icon><RefreshLeft /></el-icon>
                  重置
                </el-button>
              </el-button-group>
            </el-form-item>
          </el-col>
        </el-row>
        
        <!-- 高级查询选项 -->
        <el-collapse v-model="advancedCollapse">
          <el-collapse-item title="高级选项" name="advanced">
            <el-row :gutter="24">
              <el-col :span="8">
                <el-form-item label="数据字段">
                  <el-select 
                    v-model="queryForm.fields" 
                    multiple 
                    placeholder="选择数据字段"
                  >
                    <el-option label="开盘价" value="open" />
                    <el-option label="最高价" value="high" />
                    <el-option label="最低价" value="low" />
                    <el-option label="收盘价" value="close" />
                    <el-option label="成交量" value="volume" />
                    <el-option label="成交额" value="amount" />
                    <el-option label="市值" value="market_cap" />
                    <el-option label="市盈率" value="pe_ratio" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="行业筛选">
                  <el-select 
                    v-model="queryForm.industries" 
                    multiple 
                    placeholder="选择行业"
                  >
                    <el-option label="金融" value="金融" />
                    <el-option label="消费" value="消费" />
                    <el-option label="科技" value="科技" />
                    <el-option label="医药" value="医药" />
                    <el-option label="工业" value="工业" />
                    <el-option label="材料" value="材料" />
                    <el-option label="能源" value="能源" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="市值范围">
                  <el-input-number 
                    v-model="queryForm.minMarketCap" 
                    :min="0" 
                    placeholder="最小市值(亿)" 
                    style="width: 48%; margin-right: 4%;"
                  />
                  <el-input-number 
                    v-model="queryForm.maxMarketCap" 
                    :min="0" 
                    placeholder="最大市值(亿)" 
                    style="width: 48%;"
                  />
                </el-form-item>
              </el-col>
            </el-row>
          </el-collapse-item>
        </el-collapse>
      </el-form>
    </el-card>

    <!-- 数据展示区域 -->
    <el-row :gutter="24" class="content-row">
      <!-- 左侧数据表格 -->
      <el-col :span="16">
        <el-card class="data-table-card" shadow="never">
          <template #header>
            <div class="panel-header">
              <el-icon><Grid /></el-icon>
              <span>数据详情</span>
              <div class="table-controls">
                <el-input
                  v-model="tableSearch"
                  placeholder="搜索股票代码或名称"
                  size="small"
                  style="width: 200px; margin-right: 12px;"
                  clearable
                >
                  <template #prefix>
                    <el-icon><Search /></el-icon>
                  </template>
                </el-input>
                <el-button size="small" @click="toggleTableSize">
                  <el-icon><FullScreen /></el-icon>
                </el-button>
              </div>
            </div>
          </template>
          
          <el-table
            :data="filteredTableData"
            :loading="loading"
            :size="tableSize"
            stripe
            border
            height="500"
            @selection-change="handleSelectionChange"
          >
            <el-table-column type="selection" width="55" />
            <el-table-column prop="instrument" label="股票代码" width="120" fixed="left">
              <template #default="scope">
                <el-button link type="primary" @click="viewStock(scope.row)">
                  {{ scope.row.instrument }}
                </el-button>
              </template>
            </el-table-column>
            <el-table-column prop="name" label="股票名称" width="120" />
            <el-table-column prop="datetime" label="日期" width="120" />
            <el-table-column prop="close" label="收盘价" width="100">
              <template #default="scope">
                {{ formatNumber(scope.row.close, 2) }}
              </template>
            </el-table-column>
            <el-table-column prop="volume" label="成交量" width="120">
              <template #default="scope">
                {{ formatNumber(scope.row.volume, 0) }}
              </template>
            </el-table-column>
            <el-table-column prop="market_cap" label="市值(亿)" width="120">
              <template #default="scope">
                {{ formatNumber((scope.row.market_cap || 0) / 100000000, 2) }}
              </template>
            </el-table-column>
            <el-table-column prop="industry" label="行业" width="100" />
            <el-table-column prop="pe_ratio" label="市盈率" width="100">
              <template #default="scope">
                {{ formatNumber(scope.row.pe_ratio, 2) }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="120" fixed="right">
              <template #default="scope">
                <el-button-group size="small">
                  <el-button type="primary" link @click="analyzeStock(scope.row)">
                    分析
                  </el-button>
                  <el-button type="success" link @click="addToFactor(scope.row)">
                    加入因子
                  </el-button>
                </el-button-group>
              </template>
            </el-table-column>
          </el-table>
          
          <!-- 分页 -->
          <div class="pagination-container">
            <el-pagination
              v-model:current-page="pagination.currentPage"
              v-model:page-size="pagination.pageSize"
              :page-sizes="[20, 50, 100, 200]"
              :total="stockData.length"
              layout="total, sizes, prev, pager, next, jumper"
              @size-change="handleSizeChange"
              @current-change="handleCurrentChange"
            />
          </div>
        </el-card>
      </el-col>
      
      <!-- 右侧统计信息 -->
      <el-col :span="8">
        <!-- 数据概览 -->
        <el-card class="stats-card" shadow="never">
          <template #header>
            <div class="panel-header">
              <el-icon><DataAnalysis /></el-icon>
              <span>数据概览</span>
            </div>
          </template>
          
          <div class="stats-content">
            <div class="stat-item">
              <div class="stat-value">{{ dataStats.stockCount }}</div>
              <div class="stat-label">股票数量</div>
            </div>
            <div class="stat-item">
              <div class="stat-value">{{ dataStats.tradingDays }}</div>
              <div class="stat-label">交易日数</div>
            </div>
            <div class="stat-item">
              <div class="stat-value">{{ formatPercent(dataStats.coverage) }}</div>
              <div class="stat-label">数据覆盖率</div>
            </div>
            <div class="stat-item">
              <div class="stat-value">{{ latestTradingDay }}</div>
              <div class="stat-label">最新交易日</div>
            </div>
          </div>
        </el-card>
        
        <!-- 行业分布 -->
        <el-card class="industry-card" shadow="never">
          <template #header>
            <div class="panel-header">
              <el-icon><PieChart /></el-icon>
              <span>行业分布</span>
            </div>
          </template>
          
          <div class="industry-distribution">
            <div v-for="(count, industry) in industryDistribution" :key="industry" class="industry-item">
              <div class="industry-name">{{ industry }}</div>
              <div class="industry-bar">
                <div 
                  class="industry-progress" 
                  :style="{ width: `${(count / maxIndustryCount) * 100}%` }"
                />
                <span class="industry-count">{{ count }}</span>
              </div>
            </div>
          </div>
        </el-card>
        
        <!-- 选中数据操作 -->
        <el-card v-if="selectedRows.length > 0" class="selection-card" shadow="never">
          <template #header>
            <div class="panel-header">
              <el-icon><Select /></el-icon>
              <span>批量操作</span>
              <el-tag size="small" type="primary">{{ selectedRows.length }} 项已选</el-tag>
            </div>
          </template>
          
          <div class="selection-actions">
            <el-button-group>
              <el-button @click="exportSelected">
                <el-icon><Download /></el-icon>
                导出选中
              </el-button>
              <el-button @click="analyzeSelected">
                <el-icon><DataAnalysis /></el-icon>
                批量分析
              </el-button>
            </el-button-group>
            <el-button-group>
              <el-button @click="createFactorFromSelected">
                <el-icon><MagicStick /></el-icon>
                生成因子
              </el-button>
              <el-button @click="clearSelection">
                <el-icon><Close /></el-icon>
                清除选择
              </el-button>
            </el-button-group>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 股票详情弹窗 -->
    <el-dialog
      v-model="stockDetailVisible"
      :title="`股票详情 - ${currentStock?.name || ''} (${currentStock?.instrument || ''})`"
      width="80%"
      @close="closeStockDetail"
    >
      <div v-if="currentStock" class="stock-detail">
        <el-row :gutter="24">
          <el-col :span="12">
            <h4>基本信息</h4>
            <el-descriptions :column="2" border>
              <el-descriptions-item label="股票代码">{{ currentStock.instrument }}</el-descriptions-item>
              <el-descriptions-item label="股票名称">{{ currentStock.name }}</el-descriptions-item>
              <el-descriptions-item label="所属行业">{{ currentStock.industry || 'N/A' }}</el-descriptions-item>
              <el-descriptions-item label="上市日期">{{ currentStock.list_date || 'N/A' }}</el-descriptions-item>
              <el-descriptions-item label="市值(亿)">
                {{ formatNumber((currentStock.market_cap || 0) / 100000000, 2) }}
              </el-descriptions-item>
              <el-descriptions-item label="流通市值(亿)">
                {{ formatNumber((currentStock.float_market_cap || 0) / 100000000, 2) }}
              </el-descriptions-item>
            </el-descriptions>
          </el-col>
          <el-col :span="12">
            <h4>价格信息</h4>
            <el-descriptions :column="2" border>
              <el-descriptions-item label="收盘价">{{ formatNumber(currentStock.close, 2) }}</el-descriptions-item>
              <el-descriptions-item label="开盘价">{{ formatNumber(currentStock.open, 2) }}</el-descriptions-item>
              <el-descriptions-item label="最高价">{{ formatNumber(currentStock.high, 2) }}</el-descriptions-item>
              <el-descriptions-item label="最低价">{{ formatNumber(currentStock.low, 2) }}</el-descriptions-item>
              <el-descriptions-item label="成交量">{{ formatNumber(currentStock.volume, 0) }}</el-descriptions-item>
              <el-descriptions-item label="市盈率">{{ formatNumber(currentStock.pe_ratio, 2) }}</el-descriptions-item>
            </el-descriptions>
          </el-col>
        </el-row>
      </div>
      <template #footer>
        <el-button @click="stockDetailVisible = false">关闭</el-button>
        <el-button type="primary" @click="analyzeStock(currentStock)">深度分析</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  DataBoard,
  Refresh,
  Download,
  Search,
  RefreshLeft,
  Grid,
  FullScreen,
  DataAnalysis,
  PieChart,
  Select,
  Close,
  MagicStick
} from '@element-plus/icons-vue'

// Store
import { useQlibDataStore } from '@/stores/qlib-data'

const router = useRouter()
const qlibDataStore = useQlibDataStore()

// 响应式数据
const loading = ref(false)
const advancedCollapse = ref([])
const tableSearch = ref('')
const tableSize = ref<'default' | 'large' | 'small'>('default')
const stockDetailVisible = ref(false)
const currentStock = ref<any>(null)
const selectedRows = ref<any[]>([])

// 查询表单
const queryForm = ref({
  instruments: 'CSI300',
  dateRange: [] as string[],
  freq: 'day',
  fields: ['open', 'high', 'low', 'close', 'volume'],
  industries: [] as string[],
  minMarketCap: null as number | null,
  maxMarketCap: null as number | null
})

// 分页
const pagination = ref({
  currentPage: 1,
  pageSize: 50
})

// 计算属性
const stockData = computed(() => qlibDataStore.stockData)
const dataStats = computed(() => qlibDataStore.dataStats)
const hasData = computed(() => stockData.value.length > 0)
const uniqueInstruments = computed(() => qlibDataStore.uniqueInstruments)
const latestTradingDay = computed(() => qlibDataStore.latestTradingDay)

const filteredTableData = computed(() => {
  let filtered = stockData.value
  
  // 搜索过滤
  if (tableSearch.value) {
    const searchLower = tableSearch.value.toLowerCase()
    filtered = filtered.filter(item =>
      item.instrument.toLowerCase().includes(searchLower) ||
      (item.name && item.name.toLowerCase().includes(searchLower))
    )
  }
  
  // 分页
  const start = (pagination.value.currentPage - 1) * pagination.value.pageSize
  const end = start + pagination.value.pageSize
  return filtered.slice(start, end)
})

const industryDistribution = computed(() => {
  const distribution: Record<string, number> = {}
  stockData.value.forEach(stock => {
    const industry = stock.industry || '未知'
    distribution[industry] = (distribution[industry] || 0) + 1
  })
  return distribution
})

const maxIndustryCount = computed(() => {
  return Math.max(...Object.values(industryDistribution.value), 1)
})

// 方法
const formatNumber = (num: number | null | undefined, decimals = 0) => {
  if (num === null || num === undefined || isNaN(num)) return 'N/A'
  return num.toLocaleString('zh-CN', { 
    maximumFractionDigits: decimals,
    minimumFractionDigits: decimals 
  })
}

const formatPercent = (num: number) => {
  if (num === null || num === undefined || isNaN(num)) return 'N/A'
  return `${num.toFixed(1)}%`
}

const queryData = async () => {
  loading.value = true
  try {
    const params = {
      instruments: queryForm.value.instruments,
      start_time: queryForm.value.dateRange[0] || '2023-01-01',
      end_time: queryForm.value.dateRange[1] || '2023-12-31',
      freq: queryForm.value.freq,
      fields: queryForm.value.fields
    }
    
    await qlibDataStore.loadMarketData(params)
    ElMessage.success('数据查询成功')
    pagination.value.currentPage = 1
  } catch (error) {
    console.error('查询数据失败:', error)
    ElMessage.error('数据查询失败')
  } finally {
    loading.value = false
  }
}

const resetQuery = () => {
  queryForm.value = {
    instruments: 'CSI300',
    dateRange: [],
    freq: 'day',
    fields: ['open', 'high', 'low', 'close', 'volume'],
    industries: [],
    minMarketCap: null,
    maxMarketCap: null
  }
}

const refreshData = async () => {
  await queryData()
}

const exportData = () => {
  if (!hasData.value) {
    ElMessage.warning('暂无数据可导出')
    return
  }
  
  try {
    qlibDataStore.downloadCSV('qlib_stock_data.csv')
    ElMessage.success('数据导出成功')
  } catch (error) {
    ElMessage.error('数据导出失败')
  }
}

const toggleTableSize = () => {
  const sizes: Array<'default' | 'large' | 'small'> = ['default', 'large', 'small']
  const currentIndex = sizes.indexOf(tableSize.value)
  tableSize.value = sizes[(currentIndex + 1) % sizes.length]
}

const handleSelectionChange = (selection: any[]) => {
  selectedRows.value = selection
}

const handleSizeChange = (val: number) => {
  pagination.value.pageSize = val
  pagination.value.currentPage = 1
}

const handleCurrentChange = (val: number) => {
  pagination.value.currentPage = val
}

const viewStock = (stock: any) => {
  currentStock.value = stock
  stockDetailVisible.value = true
}

const closeStockDetail = () => {
  stockDetailVisible.value = false
  currentStock.value = null
}

const analyzeStock = (stock: any) => {
  // 跳转到因子分析页面，传递股票信息
  router.push({
    path: '/qlib-factor-workshop',
    query: {
      instrument: stock.instrument,
      name: stock.name,
      action: 'analyze'
    }
  })
}

const addToFactor = (stock: any) => {
  // 跳转到因子开发页面，添加到因子篮子
  router.push({
    path: '/qlib-factor-workshop',
    query: {
      instrument: stock.instrument,
      name: stock.name,
      action: 'add_factor'
    }
  })
  ElMessage.success(`已添加 ${stock.name} 到因子开发篮子`)
}

const exportSelected = () => {
  if (selectedRows.value.length === 0) {
    ElMessage.warning('请先选择要导出的数据')
    return
  }
  
  // 导出选中的数据
  const csvContent = [
    // 表头
    Object.keys(selectedRows.value[0]).join(','),
    // 数据行
    ...selectedRows.value.map(row => Object.values(row).join(','))
  ].join('\n')
  
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  const url = URL.createObjectURL(blob)
  link.setAttribute('href', url)
  link.setAttribute('download', `selected_stocks_${Date.now()}.csv`)
  link.style.visibility = 'hidden'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  
  ElMessage.success('选中数据导出成功')
}

const analyzeSelected = () => {
  if (selectedRows.value.length === 0) {
    ElMessage.warning('请先选择要分析的数据')
    return
  }
  
  // 跳转到批量分析页面
  const instruments = selectedRows.value.map(row => row.instrument).join(',')
  router.push({
    path: '/qlib-factor-workshop',
    query: {
      instruments,
      action: 'batch_analyze'
    }
  })
}

const createFactorFromSelected = () => {
  if (selectedRows.value.length === 0) {
    ElMessage.warning('请先选择数据')
    return
  }
  
  // 基于选中数据创建因子
  const instruments = selectedRows.value.map(row => row.instrument).join(',')
  router.push({
    path: '/qlib-factor-workshop',
    query: {
      instruments,
      action: 'create_factor'
    }
  })
}

const clearSelection = () => {
  selectedRows.value = []
}

// 生命周期
onMounted(async () => {
  // 设置默认时间范围
  const endDate = new Date().toISOString().split('T')[0]
  const startDate = new Date(Date.now() - 365 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]
  queryForm.value.dateRange = [startDate, endDate]
  
  // 自动查询数据
  await queryData()
})

// 监听查询表单变化，清空选择
watch(() => queryForm.value, () => {
  selectedRows.value = []
}, { deep: true })
</script>

<style scoped lang="scss">
.qlib-data-browser {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f5f7fa;
  
  .toolbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 16px 24px;
    background: white;
    border-bottom: 1px solid #e4e7ed;
    
    .toolbar-left {
      .page-title {
        display: flex;
        align-items: center;
        gap: 8px;
        margin: 0 0 8px 0;
        font-size: 20px;
        font-weight: 500;
      }
      
      .el-breadcrumb {
        font-size: 14px;
      }
    }
  }
  
  .query-panel {
    margin: 20px 24px 0;
    
    .panel-header {
      display: flex;
      align-items: center;
      gap: 8px;
      font-weight: 500;
    }
    
    .query-form {
      .el-select,
      .el-date-picker {
        width: 100%;
      }
    }
  }
  
  .content-row {
    margin: 20px 24px;
    flex: 1;
    
    .el-card {
      height: fit-content;
      margin-bottom: 20px;
      
      .panel-header {
        display: flex;
        align-items: center;
        gap: 8px;
        font-weight: 500;
        
        .table-controls {
          margin-left: auto;
          display: flex;
          align-items: center;
        }
        
        .el-tag {
          margin-left: auto;
        }
      }
    }
    
    .data-table-card {
      .pagination-container {
        margin-top: 16px;
        text-align: right;
      }
    }
    
    .stats-card {
      .stats-content {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 16px;
        
        .stat-item {
          text-align: center;
          
          .stat-value {
            font-size: 24px;
            font-weight: 600;
            color: #409eff;
            margin-bottom: 4px;
          }
          
          .stat-label {
            font-size: 12px;
            color: #909399;
          }
        }
      }
    }
    
    .industry-card {
      .industry-distribution {
        .industry-item {
          display: flex;
          align-items: center;
          margin-bottom: 12px;
          
          &:last-child {
            margin-bottom: 0;
          }
          
          .industry-name {
            width: 60px;
            font-size: 12px;
            color: #606266;
          }
          
          .industry-bar {
            flex: 1;
            position: relative;
            height: 20px;
            background: #f0f2f5;
            border-radius: 10px;
            margin-left: 12px;
            
            .industry-progress {
              height: 100%;
              background: linear-gradient(90deg, #409eff, #67c23a);
              border-radius: 10px;
              transition: width 0.3s;
            }
            
            .industry-count {
              position: absolute;
              right: 8px;
              top: 50%;
              transform: translateY(-50%);
              font-size: 11px;
              color: #606266;
              font-weight: 500;
            }
          }
        }
      }
    }
    
    .selection-card {
      .selection-actions {
        display: flex;
        flex-direction: column;
        gap: 12px;
        
        .el-button-group {
          display: flex;
          
          .el-button {
            flex: 1;
            margin: 0 !important;
          }
        }
      }
    }
  }
  
  .stock-detail {
    h4 {
      margin: 0 0 16px 0;
      color: #409eff;
      font-weight: 500;
    }
    
    .el-descriptions {
      margin-bottom: 24px;
      
      &:last-child {
        margin-bottom: 0;
      }
    }
  }
}
</style>