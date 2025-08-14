<template>
  <div class="qlib-portfolio-chart">
    <div class="chart-header">
      <div class="header-left">
        <h3 class="chart-title">
          <el-icon><PieChart /></el-icon>
          投资组合持仓分析
        </h3>
        <p class="chart-subtitle">基于Qlib策略的投资组合权重分析与风险分散评估</p>
      </div>
      <div class="header-right">
        <el-button-group>
          <el-button 
            :type="viewType === 'weight' ? 'primary' : ''" 
            @click="viewType = 'weight'"
            size="small"
          >
            权重分布
          </el-button>
          <el-button 
            :type="viewType === 'sector' ? 'primary' : ''" 
            @click="viewType = 'sector'"
            size="small"
          >
            行业分布
          </el-button>
          <el-button 
            :type="viewType === 'evolution' ? 'primary' : ''" 
            @click="viewType = 'evolution'"
            size="small"
          >
            权重变化
          </el-button>
        </el-button-group>
        <el-divider direction="vertical" />
        <el-select v-model="portfolioDate" size="small" style="width: 150px" @change="updateChart">
          <el-option 
            v-for="date in availableDates" 
            :key="date" 
            :label="date" 
            :value="date" 
          />
        </el-select>
        <el-divider direction="vertical" />
        <el-dropdown @command="handleExport">
          <el-button size="small">
            导出 <el-icon><ArrowDown /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="png">导出图表</el-dropdown-item>
              <el-dropdown-item command="excel">导出持仓数据</el-dropdown-item>
              <el-dropdown-item command="report">生成持仓报告</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>

    <div class="chart-controls">
      <div class="strategy-selector">
        <el-select 
          v-model="selectedStrategy" 
          placeholder="选择投资策略"
          style="width: 200px"
          @change="updateChart"
        >
          <el-option
            v-for="strategy in availableStrategies"
            :key="strategy.id"
            :label="strategy.name"
            :value="strategy.id"
          >
            <span class="strategy-option">
              <span class="strategy-name">{{ strategy.name }}</span>
              <span class="strategy-return">{{ strategy.totalReturn }}%</span>
            </span>
          </el-option>
        </el-select>
      </div>
      
      <div class="filter-options">
        <el-checkbox v-model="showOnlyLongPositions" @change="updateChart">
          仅显示多头持仓
        </el-checkbox>
        <el-checkbox v-model="showBenchmarkComparison" @change="updateChart">
          显示基准对比
        </el-checkbox>
        <el-checkbox v-model="showRiskMetrics" @change="updateChart">
          显示风险指标
        </el-checkbox>
      </div>

      <div class="threshold-controls">
        <span class="threshold-label">最小权重阈值:</span>
        <el-slider
          v-model="minWeightThreshold"
          :min="0"
          :max="5"
          :step="0.1"
          :format-tooltip="(val) => `${val}%`"
          style="width: 120px"
          @change="updateChart"
        />
      </div>
    </div>

    <!-- 组合概览统计 -->
    <div class="portfolio-overview" v-if="portfolioMetrics">
      <div class="overview-cards">
        <div class="overview-card" v-for="metric in portfolioMetrics" :key="metric.label">
          <div class="metric-icon">
            <el-icon>
              <component :is="metric.icon" />
            </el-icon>
          </div>
          <div class="metric-content">
            <div class="metric-label">{{ metric.label }}</div>
            <div class="metric-value" :class="metric.valueClass">{{ metric.value }}</div>
            <div class="metric-desc" v-if="metric.description">{{ metric.description }}</div>
          </div>
        </div>
      </div>
    </div>

    <div class="chart-container">
      <!-- 主图表 -->
      <div class="main-chart-wrapper">
        <div 
          ref="mainChartContainer" 
          class="main-chart"
          v-loading="loading"
          element-loading-text="正在加载投资组合数据..."
        ></div>
        
        <!-- 图表控制面板 -->
        <div class="chart-control-panel" v-show="viewType === 'weight'">
          <div class="control-section">
            <div class="control-title">显示选项</div>
            <div class="control-options">
              <el-radio-group v-model="chartDisplayMode" @change="updateChart">
                <el-radio label="pie">饼图</el-radio>
                <el-radio label="treemap">树状图</el-radio>
                <el-radio label="sunburst">旭日图</el-radio>
              </el-radio-group>
            </div>
          </div>
          <div class="control-section">
            <div class="control-title">排序方式</div>
            <div class="control-options">
              <el-select v-model="sortMethod" size="small" @change="updateChart">
                <el-option label="按权重降序" value="weight_desc" />
                <el-option label="按权重升序" value="weight_asc" />
                <el-option label="按收益率" value="return" />
                <el-option label="按股票代码" value="symbol" />
              </el-select>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 辅助图表 -->
      <div class="auxiliary-charts" v-show="viewType === 'evolution'">
        <div ref="evolutionChartContainer" class="evolution-chart"></div>
      </div>
    </div>

    <!-- 持仓详细数据 -->
    <div class="portfolio-detail">
      <el-tabs v-model="activeDetailTab">
        <el-tab-pane label="持仓明细" name="holdings">
          <div class="holdings-table">
            <el-table 
              :data="filteredHoldings" 
              size="small" 
              :max-height="400"
              @sort-change="handleSort"
            >
              <el-table-column prop="symbol" label="股票代码" width="100" fixed />
              <el-table-column prop="name" label="股票名称" width="120" />
              <el-table-column prop="weight" label="权重%" width="100" sortable>
                <template #default="scope">
                  <div class="weight-cell">
                    <span :class="getWeightClass(scope.row.weight)">
                      {{ (scope.row.weight * 100).toFixed(2) }}%
                    </span>
                    <div class="weight-bar">
                      <div 
                        class="weight-fill" 
                        :style="{ width: `${scope.row.weight * 100}%` }"
                      ></div>
                    </div>
                  </div>
                </template>
              </el-table-column>
              <el-table-column prop="shares" label="持股数量" width="120" sortable />
              <el-table-column prop="price" label="价格" width="100">
                <template #default="scope">
                  ¥{{ scope.row.price.toFixed(2) }}
                </template>
              </el-table-column>
              <el-table-column prop="marketValue" label="市值" width="120">
                <template #default="scope">
                  ¥{{ formatNumber(scope.row.marketValue) }}
                </template>
              </el-table-column>
              <el-table-column prop="sector" label="行业" width="100" />
              <el-table-column prop="pnl" label="盈亏" width="100" sortable>
                <template #default="scope">
                  <span :class="getPnLClass(scope.row.pnl)">
                    {{ formatNumber(scope.row.pnl, true) }}
                  </span>
                </template>
              </el-table-column>
              <el-table-column prop="pnlPercent" label="盈亏%" width="100" sortable>
                <template #default="scope">
                  <span :class="getPnLClass(scope.row.pnlPercent)">
                    {{ scope.row.pnlPercent > 0 ? '+' : '' }}{{ (scope.row.pnlPercent * 100).toFixed(2) }}%
                  </span>
                </template>
              </el-table-column>
              <el-table-column prop="beta" label="Beta" width="80" />
              <el-table-column label="操作" width="120" fixed="right">
                <template #default="scope">
                  <el-button size="small" @click="viewStockDetail(scope.row)">
                    详情
                  </el-button>
                  <el-button 
                    size="small" 
                    type="warning" 
                    @click="adjustWeight(scope.row)"
                    v-if="canAdjustWeight"
                  >
                    调整
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-tab-pane>
        
        <el-tab-pane label="行业分析" name="sector">
          <div class="sector-analysis">
            <div class="sector-chart" ref="sectorChartContainer"></div>
            <div class="sector-summary">
              <h4>行业配置分析</h4>
              <div class="sector-stats">
                <div class="stat-item" v-for="sector in sectorAnalysis" :key="sector.name">
                  <div class="sector-info">
                    <span class="sector-name">{{ sector.name }}</span>
                    <span class="sector-weight">{{ (sector.weight * 100).toFixed(1) }}%</span>
                  </div>
                  <div class="sector-metrics">
                    <span class="sector-count">{{ sector.count }}只股票</span>
                    <span class="sector-return" :class="getPnLClass(sector.avgReturn)">
                      收益: {{ (sector.avgReturn * 100).toFixed(2) }}%
                    </span>
                  </div>
                  <div class="sector-risk">
                    <span class="sector-vol">波动率: {{ (sector.volatility * 100).toFixed(2) }}%</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </el-tab-pane>
        
        <el-tab-pane label="风险分析" name="risk">
          <div class="risk-analysis">
            <div class="risk-metrics-grid">
              <div class="risk-card" v-for="risk in riskMetrics" :key="risk.name">
                <div class="risk-header">
                  <span class="risk-name">{{ risk.name }}</span>
                  <el-tag :type="risk.levelType" size="small">{{ risk.level }}</el-tag>
                </div>
                <div class="risk-value" :class="risk.valueClass">{{ risk.value }}</div>
                <div class="risk-description">{{ risk.description }}</div>
                <div class="risk-action" v-if="risk.action">
                  <el-icon><Warning /></el-icon>
                  <span>{{ risk.action }}</span>
                </div>
              </div>
            </div>
            
            <div class="risk-chart-container">
              <div ref="riskChartContainer" class="risk-chart"></div>
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, computed, nextTick } from 'vue'
import * as echarts from 'echarts'
import { PieChart, ArrowDown, TrendCharts, Money, DataAnalysis, Warning, Stopwatch } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'

interface HoldingData {
  symbol: string
  name: string
  weight: number
  shares: number
  price: number
  marketValue: number
  sector: string
  pnl: number
  pnlPercent: number
  beta: number
  entryDate: string
}

interface StrategyInfo {
  id: string
  name: string
  totalReturn: number
  description: string
}

interface PortfolioMetric {
  label: string
  value: string
  icon: any
  valueClass?: string
  description?: string
}

interface SectorAnalysis {
  name: string
  weight: number
  count: number
  avgReturn: number
  volatility: number
}

interface RiskMetric {
  name: string
  value: string
  level: string
  levelType: string
  valueClass?: string
  description: string
  action?: string
}

// 响应式数据
const loading = ref(false)
const mainChartContainer = ref<HTMLElement>()
const evolutionChartContainer = ref<HTMLElement>()
const sectorChartContainer = ref<HTMLElement>()
const riskChartContainer = ref<HTMLElement>()
const mainChart = ref<echarts.ECharts>()
const evolutionChart = ref<echarts.ECharts>()
const sectorChart = ref<echarts.ECharts>()
const riskChart = ref<echarts.ECharts>()

// 图表控制
const viewType = ref<'weight' | 'sector' | 'evolution'>('weight')
const chartDisplayMode = ref<'pie' | 'treemap' | 'sunburst'>('pie')
const sortMethod = ref('weight_desc')
const portfolioDate = ref(new Date().toISOString().split('T')[0])
const selectedStrategy = ref('')
const showOnlyLongPositions = ref(true)
const showBenchmarkComparison = ref(false)
const showRiskMetrics = ref(false)
const minWeightThreshold = ref(0.5)
const activeDetailTab = ref('holdings')
const canAdjustWeight = ref(true)

// 数据
const availableStrategies = ref<StrategyInfo[]>([
  { id: 'topk_lgb', name: 'TopK-LightGBM', totalReturn: 28.5, description: '基于LightGBM的TopK策略' },
  { id: 'long_short', name: '多空策略', totalReturn: 25.1, description: '多空配对交易策略' },
  { id: 'momentum', name: '动量策略', totalReturn: 22.3, description: '基于动量因子的策略' },
  { id: 'mean_reversion', name: '均值回归', totalReturn: 18.7, description: '均值回归策略' }
])

const availableDates = ref<string[]>([])
const holdingsData = ref<HoldingData[]>([])
const portfolioMetrics = ref<PortfolioMetric[]>()
const sectorAnalysis = ref<SectorAnalysis[]>([])
const riskMetrics = ref<RiskMetric[]>([])

// 计算属性
const filteredHoldings = computed(() => {
  let filtered = holdingsData.value.filter(holding => 
    holding.weight >= minWeightThreshold.value / 100
  )
  
  if (showOnlyLongPositions.value) {
    filtered = filtered.filter(holding => holding.weight > 0)
  }
  
  // 排序
  switch (sortMethod.value) {
    case 'weight_desc':
      filtered.sort((a, b) => b.weight - a.weight)
      break
    case 'weight_asc':
      filtered.sort((a, b) => a.weight - b.weight)
      break
    case 'return':
      filtered.sort((a, b) => b.pnlPercent - a.pnlPercent)
      break
    case 'symbol':
      filtered.sort((a, b) => a.symbol.localeCompare(b.symbol))
      break
  }
  
  return filtered
})

// 方法
const initCharts = async () => {
  await nextTick()
  
  if (mainChartContainer.value) {
    mainChart.value = echarts.init(mainChartContainer.value)
  }
  
  if (evolutionChartContainer.value) {
    evolutionChart.value = echarts.init(evolutionChartContainer.value)
  }
  
  if (sectorChartContainer.value) {
    sectorChart.value = echarts.init(sectorChartContainer.value)
  }
  
  if (riskChartContainer.value) {
    riskChart.value = echarts.init(riskChartContainer.value)
  }
  
  initMainChart()
  initEvolutionChart()
  initSectorChart()
  initRiskChart()
}

const initMainChart = () => {
  if (!mainChart.value) return
  
  const option = {
    title: {
      text: '投资组合权重分布',
      left: 'center',
      textStyle: {
        fontSize: 14,
        fontWeight: 'bold'
      }
    },
    tooltip: {
      trigger: 'item',
      formatter: '{a} <br/>{b}: {c}% ({d}%)'
    },
    legend: {
      top: 30,
      type: 'scroll'
    },
    series: []
  }
  
  mainChart.value.setOption(option)
}

const initEvolutionChart = () => {
  if (!evolutionChart.value) return
  
  const option = {
    title: {
      text: '权重变化趋势',
      textStyle: {
        fontSize: 14
      }
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      }
    },
    legend: {},
    xAxis: {
      type: 'category',
      data: []
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        formatter: '{value}%'
      }
    },
    series: []
  }
  
  evolutionChart.value.setOption(option)
}

const initSectorChart = () => {
  if (!sectorChart.value) return
  
  const option = {
    title: {
      text: '行业配置',
      textStyle: {
        fontSize: 14
      }
    },
    tooltip: {
      trigger: 'item'
    },
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],
      data: []
    }]
  }
  
  sectorChart.value.setOption(option)
}

const initRiskChart = () => {
  if (!riskChart.value) return
  
  const option = {
    title: {
      text: '风险指标雷达图',
      textStyle: {
        fontSize: 14
      }
    },
    radar: {
      indicator: [
        { name: '集中度风险', max: 100 },
        { name: '行业集中度', max: 100 },
        { name: '波动率', max: 100 },
        { name: '跟踪误差', max: 100 },
        { name: '流动性风险', max: 100 },
        { name: 'Beta风险', max: 100 }
      ]
    },
    series: [{
      type: 'radar',
      data: []
    }]
  }
  
  riskChart.value.setOption(option)
}

const updateChart = async () => {
  if (!selectedStrategy.value) return
  
  loading.value = true
  
  try {
    await loadPortfolioData()
    
    switch (viewType.value) {
      case 'weight':
        updateWeightChart()
        break
      case 'sector':
        updateSectorChart()
        break
      case 'evolution':
        updateEvolutionChart()
        break
    }
    
    // 更新辅助数据
    calculatePortfolioMetrics()
    performSectorAnalysis()
    calculateRiskMetrics()
    
  } catch (error) {
    console.error('更新图表失败:', error)
    ElMessage.error('更新图表失败')
  } finally {
    loading.value = false
  }
}

const loadPortfolioData = async () => {
  // 模拟从Qlib API获取持仓数据
  const mockHoldings = generateMockHoldings()
  holdingsData.value = mockHoldings
  
  // 生成可用日期
  const dates = []
  for (let i = 30; i >= 0; i--) {
    const date = new Date()
    date.setDate(date.getDate() - i)
    dates.push(date.toISOString().split('T')[0])
  }
  availableDates.value = dates
}

const generateMockHoldings = (): HoldingData[] => {
  const stocks = [
    { symbol: '000001.XSHE', name: '平安银行', sector: '金融' },
    { symbol: '000002.XSHE', name: '万科A', sector: '房地产' },
    { symbol: '000858.XSHE', name: '五粮液', sector: '食品饮料' },
    { symbol: '600000.XSHG', name: '浦发银行', sector: '金融' },
    { symbol: '600036.XSHG', name: '招商银行', sector: '金融' },
    { symbol: '600519.XSHG', name: '贵州茅台', sector: '食品饮料' },
    { symbol: '600887.XSHG', name: '伊利股份', sector: '食品饮料' },
    { symbol: '000725.XSHE', name: '京东方A', sector: '电子' },
    { symbol: '002415.XSHE', name: '海康威视', sector: '电子' },
    { symbol: '300059.XSHE', name: '东方财富', sector: '金融' }
  ]
  
  const holdings: HoldingData[] = []
  const totalValue = 10000000 // 1000万总资产
  
  // 生成权重（确保总和为1）
  let weights = stocks.map(() => Math.random() * 0.15 + 0.01) // 1%-16%之间
  const weightSum = weights.reduce((sum, w) => sum + w, 0)
  weights = weights.map(w => w / weightSum)
  
  stocks.forEach((stock, index) => {
    const weight = weights[index]
    const price = Math.random() * 100 + 10 // 10-110元之间
    const marketValue = totalValue * weight
    const shares = Math.floor(marketValue / price / 100) * 100 // 整手数
    const actualMarketValue = shares * price
    const entryPrice = price * (0.8 + Math.random() * 0.4) // 成本价
    const pnl = (price - entryPrice) * shares
    const pnlPercent = (price - entryPrice) / entryPrice
    
    holdings.push({
      symbol: stock.symbol,
      name: stock.name,
      weight: weight,
      shares: shares,
      price: price,
      marketValue: actualMarketValue,
      sector: stock.sector,
      pnl: pnl,
      pnlPercent: pnlPercent,
      beta: 0.8 + Math.random() * 0.8, // 0.8-1.6之间
      entryDate: new Date(Date.now() - Math.random() * 90 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]
    })
  })
  
  return holdings.sort((a, b) => b.weight - a.weight)
}

const updateWeightChart = () => {
  if (!mainChart.value) return
  
  const data = filteredHoldings.value.map(holding => ({
    name: holding.name,
    value: (holding.weight * 100).toFixed(2),
    symbol: holding.symbol,
    sector: holding.sector
  }))
  
  let series: any
  
  switch (chartDisplayMode.value) {
    case 'pie':
      series = [{
        name: '持仓权重',
        type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 10,
          borderColor: '#fff',
          borderWidth: 2
        },
        label: {
          show: false,
          position: 'center'
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 16,
            fontWeight: 'bold',
            formatter: '{b}\n{c}%'
          }
        },
        labelLine: {
          show: false
        },
        data: data
      }]
      break
      
    case 'treemap':
      series = [{
        name: '持仓权重',
        type: 'treemap',
        data: data,
        leafDepth: 1,
        label: {
          show: true,
          formatter: '{b}\n{c}%'
        },
        itemStyle: {
          borderColor: '#fff'
        }
      }]
      break
      
    case 'sunburst':
      // 按行业分组数据
      const sectorData = new Map<string, any[]>()
      filteredHoldings.value.forEach(holding => {
        if (!sectorData.has(holding.sector)) {
          sectorData.set(holding.sector, [])
        }
        sectorData.get(holding.sector)!.push({
          name: holding.name,
          value: (holding.weight * 100).toFixed(2)
        })
      })
      
      const sunburstData = Array.from(sectorData.entries()).map(([sector, stocks]) => ({
        name: sector,
        children: stocks
      }))
      
      series = [{
        name: '持仓权重',
        type: 'sunburst',
        data: sunburstData,
        radius: [0, '95%'],
        sort: null,
        emphasis: {
          focus: 'ancestor'
        },
        levels: [{}, {
          r0: '15%',
          r: '35%',
          itemStyle: {
            borderWidth: 2
          },
          label: {
            rotate: 'tangential'
          }
        }, {
          r0: '35%',
          r: '70%',
          label: {
            position: 'outside',
            padding: 3,
            silent: false
          },
          itemStyle: {
            borderWidth: 1
          }
        }]
      }]
      break
  }
  
  mainChart.value.setOption({
    series: series
  })
}

const updateSectorChart = () => {
  if (!sectorChart.value) return
  
  const sectorWeights = new Map<string, number>()
  filteredHoldings.value.forEach(holding => {
    sectorWeights.set(
      holding.sector, 
      (sectorWeights.get(holding.sector) || 0) + holding.weight
    )
  })
  
  const data = Array.from(sectorWeights.entries()).map(([sector, weight]) => ({
    name: sector,
    value: (weight * 100).toFixed(2)
  }))
  
  sectorChart.value.setOption({
    series: [{
      data: data
    }]
  })
}

const updateEvolutionChart = () => {
  if (!evolutionChart.value) return
  
  // 模拟权重演化数据
  const dates = availableDates.value.slice(-14) // 最近14天
  const topHoldings = filteredHoldings.value.slice(0, 5) // 前5大持仓
  
  const series = topHoldings.map(holding => ({
    name: holding.name,
    type: 'line',
    smooth: true,
    data: dates.map(() => {
      // 模拟权重变化
      const baseWeight = holding.weight * 100
      const variation = (Math.random() - 0.5) * baseWeight * 0.3
      return (baseWeight + variation).toFixed(2)
    })
  }))
  
  evolutionChart.value.setOption({
    xAxis: {
      data: dates
    },
    series: series
  })
}

const calculatePortfolioMetrics = () => {
  const totalValue = holdingsData.value.reduce((sum, holding) => sum + holding.marketValue, 0)
  const totalPnL = holdingsData.value.reduce((sum, holding) => sum + holding.pnl, 0)
  const totalReturn = totalPnL / (totalValue - totalPnL)
  const stockCount = holdingsData.value.length
  const largestWeight = Math.max(...holdingsData.value.map(h => h.weight))
  
  // 计算行业集中度（HHI指数）
  const sectorWeights = new Map<string, number>()
  holdingsData.value.forEach(holding => {
    sectorWeights.set(
      holding.sector, 
      (sectorWeights.get(holding.sector) || 0) + holding.weight
    )
  })
  const hhi = Array.from(sectorWeights.values())
    .reduce((sum, weight) => sum + weight * weight, 0)
  
  portfolioMetrics.value = [
    {
      label: '总市值',
      value: formatNumber(totalValue),
      icon: Money,
      description: '投资组合当前总市值'
    },
    {
      label: '持股数量',
      value: stockCount.toString(),
      icon: DataAnalysis,
      description: '投资组合包含股票数量'
    },
    {
      label: '总收益',
      value: `${totalReturn > 0 ? '+' : ''}${(totalReturn * 100).toFixed(2)}%`,
      icon: TrendCharts,
      valueClass: getPnLClass(totalReturn),
      description: '投资组合累计收益率'
    },
    {
      label: '最大权重',
      value: `${(largestWeight * 100).toFixed(2)}%`,
      icon: PieChart,
      valueClass: largestWeight > 0.1 ? 'warning' : 'good',
      description: '单只股票最大权重占比'
    },
    {
      label: '行业集中度',
      value: (hhi * 100).toFixed(1),
      icon: DataAnalysis,
      valueClass: hhi > 0.25 ? 'warning' : hhi > 0.15 ? 'medium' : 'good',
      description: 'HHI指数衡量行业分散程度'
    }
  ]
}

const performSectorAnalysis = () => {
  const sectorMap = new Map<string, {
    weight: number
    count: number
    totalReturn: number
    returns: number[]
  }>()
  
  holdingsData.value.forEach(holding => {
    const sector = holding.sector
    if (!sectorMap.has(sector)) {
      sectorMap.set(sector, {
        weight: 0,
        count: 0,
        totalReturn: 0,
        returns: []
      })
    }
    
    const sectorData = sectorMap.get(sector)!
    sectorData.weight += holding.weight
    sectorData.count += 1
    sectorData.totalReturn += holding.pnlPercent * holding.weight
    sectorData.returns.push(holding.pnlPercent)
  })
  
  sectorAnalysis.value = Array.from(sectorMap.entries()).map(([name, data]) => {
    const avgReturn = data.totalReturn / data.weight
    const volatility = Math.sqrt(
      data.returns.reduce((sum, r) => sum + (r - avgReturn) ** 2, 0) / data.returns.length
    )
    
    return {
      name,
      weight: data.weight,
      count: data.count,
      avgReturn,
      volatility
    }
  }).sort((a, b) => b.weight - a.weight)
}

const calculateRiskMetrics = () => {
  const weights = holdingsData.value.map(h => h.weight)
  const returns = holdingsData.value.map(h => h.pnlPercent)
  const betas = holdingsData.value.map(h => h.beta)
  
  // 集中度风险 (HHI)
  const concentrationRisk = weights.reduce((sum, w) => sum + w * w, 0)
  
  // 行业集中度
  const sectorWeights = new Map<string, number>()
  holdingsData.value.forEach(holding => {
    sectorWeights.set(
      holding.sector, 
      (sectorWeights.get(holding.sector) || 0) + holding.weight
    )
  })
  const sectorHHI = Array.from(sectorWeights.values())
    .reduce((sum, weight) => sum + weight * weight, 0)
  
  // 组合波动率（简化计算）
  const avgReturn = returns.reduce((sum, r) => sum + r, 0) / returns.length
  const portfolioVol = Math.sqrt(
    returns.reduce((sum, r) => sum + (r - avgReturn) ** 2, 0) / returns.length
  )
  
  // 组合Beta
  const portfolioBeta = weights.reduce((sum, weight, i) => sum + weight * betas[i], 0)
  
  riskMetrics.value = [
    {
      name: '集中度风险',
      value: (concentrationRisk * 100).toFixed(1),
      level: concentrationRisk > 0.2 ? '高' : concentrationRisk > 0.1 ? '中' : '低',
      levelType: concentrationRisk > 0.2 ? 'danger' : concentrationRisk > 0.1 ? 'warning' : 'success',
      description: '单只股票权重集中度，HHI指数',
      action: concentrationRisk > 0.2 ? '建议分散投资，降低单股权重' : undefined
    },
    {
      name: '行业集中度',
      value: (sectorHHI * 100).toFixed(1),
      level: sectorHHI > 0.3 ? '高' : sectorHHI > 0.2 ? '中' : '低',
      levelType: sectorHHI > 0.3 ? 'danger' : sectorHHI > 0.2 ? 'warning' : 'success',
      description: '行业配置集中度风险评估'
    },
    {
      name: '波动率风险',
      value: `${(portfolioVol * 100).toFixed(2)}%`,
      level: portfolioVol > 0.3 ? '高' : portfolioVol > 0.2 ? '中' : '低',
      levelType: portfolioVol > 0.3 ? 'danger' : portfolioVol > 0.2 ? 'warning' : 'success',
      description: '投资组合历史波动率水平'
    },
    {
      name: '系统性风险',
      value: portfolioBeta.toFixed(3),
      level: portfolioBeta > 1.2 ? '高' : portfolioBeta > 0.8 ? '中' : '低',
      levelType: portfolioBeta > 1.2 ? 'danger' : portfolioBeta > 0.8 ? 'warning' : 'success',
      description: '投资组合相对市场的Beta系数'
    }
  ]
  
  // 更新风险雷达图
  if (riskChart.value) {
    const radarData = [
      Math.min(concentrationRisk * 500, 100), // 集中度风险
      Math.min(sectorHHI * 333, 100), // 行业集中度
      Math.min(portfolioVol * 333, 100), // 波动率
      Math.min(Math.abs(portfolioBeta - 1) * 100, 100), // 跟踪误差
      Math.random() * 50 + 25, // 流动性风险（模拟）
      Math.min(Math.abs(portfolioBeta - 1) * 50, 100) // Beta风险
    ]
    
    riskChart.value.setOption({
      series: [{
        data: [{
          value: radarData,
          name: '风险指标'
        }]
      }]
    })
  }
}

const handleSort = ({ column, prop, order }: any) => {
  // 表格排序处理已通过计算属性实现
}

const handleExport = (command: string) => {
  switch (command) {
    case 'png':
      if (mainChart.value) {
        const url = mainChart.value.getDataURL({
          pixelRatio: 2,
          backgroundColor: '#fff'
        })
        const link = document.createElement('a')
        link.download = `portfolio-${Date.now()}.png`
        link.href = url
        link.click()
      }
      break
    case 'excel':
    case 'report':
      ElMessage.info('功能开发中...')
      break
  }
}

const viewStockDetail = (holding: HoldingData) => {
  ElMessageBox.alert(
    `股票代码: ${holding.symbol}\n股票名称: ${holding.name}\n当前权重: ${(holding.weight * 100).toFixed(2)}%\n持股数量: ${holding.shares}股\n当前价格: ¥${holding.price.toFixed(2)}\n盈亏: ${formatNumber(holding.pnl, true)}\n所属行业: ${holding.sector}`,
    '持仓详情',
    { confirmButtonText: '确定' }
  )
}

const adjustWeight = (holding: HoldingData) => {
  ElMessage.info('权重调整功能开发中...')
}

// 辅助方法
const formatNumber = (num: number, showSign = false): string => {
  const absNum = Math.abs(num)
  const sign = showSign && num > 0 ? '+' : ''
  
  if (absNum >= 1e8) {
    return `${sign}${(num / 1e8).toFixed(2)}亿`
  } else if (absNum >= 1e4) {
    return `${sign}${(num / 1e4).toFixed(2)}万`
  } else {
    return `${sign}${num.toFixed(2)}`
  }
}

const getWeightClass = (weight: number): string => {
  if (weight > 0.1) return 'high-weight'
  if (weight > 0.05) return 'medium-weight'
  return 'low-weight'
}

const getPnLClass = (pnl: number): string => {
  return pnl > 0 ? 'positive' : 'negative'
}

// 监听器
watch([viewType, chartDisplayMode, sortMethod, selectedStrategy, showOnlyLongPositions, showBenchmarkComparison, minWeightThreshold, portfolioDate], () => {
  if (selectedStrategy.value) {
    updateChart()
  }
}, { deep: true })

// 生命周期
onMounted(async () => {
  await initCharts()
  
  // 默认选择第一个策略
  selectedStrategy.value = availableStrategies.value[0]?.id || ''
  if (selectedStrategy.value) {
    await updateChart()
  }
})
</script>

<style lang="scss" scoped>
.qlib-portfolio-chart {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #f0f0f0;
}

.header-left {
  .chart-title {
    margin: 0;
    font-size: 18px;
    color: #2c3e50;
    display: flex;
    align-items: center;
    gap: 8px;
    
    .el-icon {
      color: #409eff;
    }
  }
  
  .chart-subtitle {
    margin: 5px 0 0 0;
    color: #666;
    font-size: 13px;
  }
}

.chart-controls {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 20px;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 6px;
  flex-wrap: wrap;
}

.strategy-option {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  
  .strategy-return {
    color: #67c23a;
    font-weight: bold;
  }
}

.filter-options {
  display: flex;
  gap: 15px;
}

.threshold-controls {
  display: flex;
  align-items: center;
  gap: 10px;
  
  .threshold-label {
    font-size: 13px;
    color: #666;
  }
}

.portfolio-overview {
  margin-bottom: 20px;
}

.overview-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 15px;
}

.overview-card {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 15px;
  background: linear-gradient(135deg, #f6f8fa 0%, #e9ecef 100%);
  border-radius: 8px;
  border-left: 4px solid #409eff;
}

.metric-icon {
  .el-icon {
    font-size: 24px;
    color: #409eff;
  }
}

.metric-content {
  flex: 1;
  
  .metric-label {
    font-size: 12px;
    color: #666;
    margin-bottom: 3px;
  }
  
  .metric-value {
    font-size: 16px;
    font-weight: bold;
    margin-bottom: 2px;
    
    &.positive { color: #67c23a; }
    &.negative { color: #f56c6c; }
    &.warning { color: #e6a23c; }
    &.good { color: #67c23a; }
    &.medium { color: #e6a23c; }
  }
  
  .metric-desc {
    font-size: 10px;
    color: #999;
  }
}

.chart-container {
  position: relative;
}

.main-chart-wrapper {
  display: flex;
  gap: 20px;
}

.main-chart {
  flex: 1;
  height: 400px;
}

.chart-control-panel {
  width: 200px;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 6px;
  
  .control-section {
    margin-bottom: 20px;
    
    &:last-child {
      margin-bottom: 0;
    }
  }
  
  .control-title {
    font-size: 13px;
    font-weight: bold;
    color: #2c3e50;
    margin-bottom: 8px;
  }
  
  .control-options {
    .el-radio-group {
      display: flex;
      flex-direction: column;
      gap: 5px;
      
      :deep(.el-radio) {
        margin-right: 0;
      }
    }
  }
}

.auxiliary-charts {
  margin-top: 20px;
}

.evolution-chart {
  height: 300px;
}

.portfolio-detail {
  margin-top: 30px;
}

.holdings-table {
  :deep(.el-table) {
    font-size: 12px;
  }
  
  .weight-cell {
    .weight-bar {
      width: 100%;
      height: 4px;
      background: #f0f0f0;
      border-radius: 2px;
      margin-top: 3px;
      overflow: hidden;
      
      .weight-fill {
        height: 100%;
        background: linear-gradient(90deg, #67c23a, #409eff);
        border-radius: 2px;
        transition: width 0.3s ease;
      }
    }
  }
  
  .high-weight { color: #f56c6c; font-weight: bold; }
  .medium-weight { color: #e6a23c; }
  .low-weight { color: #67c23a; }
  
  .positive { color: #67c23a; }
  .negative { color: #f56c6c; }
}

.sector-analysis {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  align-items: start;
}

.sector-chart {
  height: 300px;
}

.sector-summary {
  h4 {
    margin-top: 0;
    color: #2c3e50;
  }
}

.sector-stats {
  .stat-item {
    margin-bottom: 15px;
    padding: 10px;
    background: #f8f9fa;
    border-radius: 6px;
    
    &:last-child {
      margin-bottom: 0;
    }
  }
  
  .sector-info {
    display: flex;
    justify-content: space-between;
    margin-bottom: 5px;
    
    .sector-name {
      font-weight: bold;
      color: #2c3e50;
    }
    
    .sector-weight {
      color: #409eff;
      font-weight: bold;
    }
  }
  
  .sector-metrics {
    display: flex;
    justify-content: space-between;
    font-size: 12px;
    margin-bottom: 3px;
    
    .sector-count {
      color: #666;
    }
    
    .sector-return {
      font-weight: bold;
    }
  }
  
  .sector-risk {
    font-size: 11px;
    color: #999;
  }
}

.risk-analysis {
  .risk-metrics-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 15px;
    margin-bottom: 20px;
  }
  
  .risk-card {
    padding: 15px;
    border: 1px solid #e4e7ed;
    border-radius: 8px;
    background: #fff;
    
    .risk-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 10px;
      
      .risk-name {
        font-weight: bold;
        color: #2c3e50;
      }
    }
    
    .risk-value {
      font-size: 20px;
      font-weight: bold;
      margin-bottom: 8px;
      color: #409eff;
    }
    
    .risk-description {
      font-size: 12px;
      color: #666;
      margin-bottom: 8px;
    }
    
    .risk-action {
      display: flex;
      align-items: center;
      gap: 5px;
      padding: 8px;
      background: #fff2e8;
      border-radius: 4px;
      font-size: 12px;
      color: #e6a23c;
      
      .el-icon {
        color: #e6a23c;
      }
    }
  }
  
  .risk-chart-container {
    .risk-chart {
      height: 400px;
    }
  }
}

@media (max-width: 768px) {
  .chart-header {
    flex-direction: column;
    gap: 15px;
  }
  
  .chart-controls {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .main-chart-wrapper {
    flex-direction: column;
  }
  
  .chart-control-panel {
    width: 100%;
  }
  
  .sector-analysis {
    grid-template-columns: 1fr;
  }
  
  .risk-metrics-grid {
    grid-template-columns: 1fr;
  }
}
</style>