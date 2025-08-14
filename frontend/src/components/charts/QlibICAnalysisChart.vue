<template>
  <div class="qlib-ic-analysis-chart">
    <div class="chart-header">
      <div class="header-left">
        <h3 class="chart-title">
          <el-icon><DataAnalysis /></el-icon>
          因子IC时序分析
        </h3>
        <p class="chart-subtitle">Information Coefficient (IC) 时间序列分析与有效性评估</p>
      </div>
      <div class="header-right">
        <el-button-group>
          <el-button 
            :type="analysisMode === 'ic' ? 'primary' : ''" 
            @click="analysisMode = 'ic'"
            size="small"
          >
            IC值
          </el-button>
          <el-button 
            :type="analysisMode === 'rank_ic' ? 'primary' : ''" 
            @click="analysisMode = 'rank_ic'"
            size="small"
          >
            RankIC
          </el-button>
          <el-button 
            :type="analysisMode === 'ic_ir' ? 'primary' : ''" 
            @click="analysisMode = 'ic_ir'"
            size="small"
          >
            IC_IR
          </el-button>
        </el-button-group>
        <el-divider direction="vertical" />
        <el-select v-model="rollingWindow" size="small" style="width: 120px" @change="updateChart">
          <el-option label="日频" :value="1" />
          <el-option label="5日均值" :value="5" />
          <el-option label="20日均值" :value="20" />
          <el-option label="60日均值" :value="60" />
        </el-select>
        <el-divider direction="vertical" />
        <el-dropdown @command="handleExport">
          <el-button size="small">
            导出 <el-icon><ArrowDown /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="png">导出图表</el-dropdown-item>
              <el-dropdown-item command="csv">导出数据</el-dropdown-item>
              <el-dropdown-item command="report">生成报告</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>

    <div class="chart-controls">
      <div class="factor-selector">
        <el-select 
          v-model="selectedFactors" 
          multiple 
          filterable 
          placeholder="选择因子进行IC分析"
          style="width: 350px"
          @change="updateChart"
        >
          <el-option
            v-for="factor in availableFactors"
            :key="factor.id"
            :label="factor.name"
            :value="factor.id"
          >
            <span class="factor-option">
              <span class="factor-name">{{ factor.name }}</span>
              <span class="factor-stats">
                <span class="ic-value" :class="getICClass(factor.avgIC)">
                  IC: {{ factor.avgIC.toFixed(3) }}
                </span>
                <span class="ic-ir-value">
                  IR: {{ factor.icIR.toFixed(2) }}
                </span>
              </span>
            </span>
          </el-option>
        </el-select>
      </div>
      
      <div class="analysis-options">
        <el-checkbox v-model="showConfidenceBand" @change="updateChart">显示置信区间</el-checkbox>
        <el-checkbox v-model="showTrend" @change="updateChart">显示趋势线</el-checkbox>
        <el-checkbox v-model="showDistribution" @change="updateChart">显示分布</el-checkbox>
      </div>

      <div class="time-selector">
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          size="small"
          @change="updateChart"
          style="width: 240px"
        />
      </div>
    </div>

    <!-- IC统计摘要 -->
    <div class="ic-summary" v-if="icSummary">
      <div class="summary-cards">
        <div class="summary-card" v-for="stat in icSummary" :key="stat.label">
          <div class="stat-label">{{ stat.label }}</div>
          <div class="stat-value" :class="stat.valueClass">{{ stat.value }}</div>
          <div class="stat-change" :class="stat.changeClass" v-if="stat.change">
            <el-icon>
              <component :is="stat.changeIcon" />
            </el-icon>
            {{ stat.change }}
          </div>
        </div>
      </div>
    </div>

    <div class="chart-container">
      <!-- 主图表 -->
      <div 
        ref="mainChartContainer" 
        class="main-chart"
        v-loading="loading"
        element-loading-text="正在计算IC指标..."
      ></div>
      
      <!-- 分布图表 -->
      <div 
        ref="distributionChartContainer" 
        class="distribution-chart"
        v-show="showDistribution"
      ></div>
    </div>

    <!-- IC分析详情 -->
    <div class="ic-analysis-detail">
      <el-tabs v-model="activeTab">
        <el-tab-pane label="IC统计" name="statistics">
          <div class="statistics-table">
            <el-table :data="icStatistics" size="small">
              <el-table-column prop="factorName" label="因子名称" width="150" fixed />
              <el-table-column prop="meanIC" label="平均IC" width="100" sortable>
                <template #default="scope">
                  <span :class="getICClass(scope.row.meanIC)">
                    {{ scope.row.meanIC.toFixed(4) }}
                  </span>
                </template>
              </el-table-column>
              <el-table-column prop="stdIC" label="IC标准差" width="100" />
              <el-table-column prop="icIR" label="IC_IR" width="100" sortable>
                <template #default="scope">
                  <span :class="getIRClass(scope.row.icIR)">
                    {{ scope.row.icIR.toFixed(3) }}
                  </span>
                </template>
              </el-table-column>
              <el-table-column prop="winRate" label="胜率" width="100">
                <template #default="scope">
                  <span :class="getWinRateClass(scope.row.winRate)">
                    {{ (scope.row.winRate * 100).toFixed(1) }}%
                  </span>
                </template>
              </el-table-column>
              <el-table-column prop="tStat" label="t统计量" width="100" />
              <el-table-column prop="pValue" label="p值" width="100">
                <template #default="scope">
                  <span :class="getPValueClass(scope.row.pValue)">
                    {{ scope.row.pValue.toFixed(4) }}
                  </span>
                </template>
              </el-table-column>
              <el-table-column prop="monthlyDecay" label="月衰减率" width="100" />
              <el-table-column prop="stability" label="稳定性评级" width="120">
                <template #default="scope">
                  <el-tag :type="getStabilityType(scope.row.stability)" size="small">
                    {{ scope.row.stability }}
                  </el-tag>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-tab-pane>
        
        <el-tab-pane label="时序分解" name="decomposition">
          <div class="decomposition-analysis">
            <div class="decomposition-chart" ref="decompositionChartContainer"></div>
            <div class="decomposition-summary">
              <h4>时序分解结果</h4>
              <div class="decomposition-components">
                <div class="component-item" v-for="component in decompositionResults" :key="component.name">
                  <span class="component-name">{{ component.name }}:</span>
                  <span class="component-value">{{ component.contribution }}%</span>
                  <span class="component-desc">{{ component.description }}</span>
                </div>
              </div>
            </div>
          </div>
        </el-tab-pane>
        
        <el-tab-pane label="预测分析" name="prediction">
          <div class="prediction-analysis">
            <div class="prediction-chart" ref="predictionChartContainer"></div>
            <div class="prediction-insights">
              <div class="insight-card" v-for="insight in predictiveInsights" :key="insight.type">
                <div class="insight-header">
                  <el-icon class="insight-icon" :class="insight.iconClass">
                    <component :is="insight.icon" />
                  </el-icon>
                  <span class="insight-title">{{ insight.title }}</span>
                  <el-tag :type="insight.severityType" size="small">{{ insight.severity }}</el-tag>
                </div>
                <div class="insight-content">{{ insight.content }}</div>
                <div class="insight-recommendations" v-if="insight.recommendations">
                  <div class="recommendations-title">建议措施:</div>
                  <ul class="recommendations-list">
                    <li v-for="rec in insight.recommendations" :key="rec">{{ rec }}</li>
                  </ul>
                </div>
              </div>
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
import { DataAnalysis, ArrowDown, TrendCharts, Warning, Check, Close, ArrowUp, ArrowDown as ArrowDownIcon } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

interface ICData {
  date: string
  ic: number
  rankIC: number
  icIR: number
  significance: number
}

interface FactorInfo {
  id: string
  name: string
  expression: string
  avgIC: number
  icIR: number
  category: string
}

interface ICSummaryItem {
  label: string
  value: string
  valueClass?: string
  change?: string
  changeClass?: string
  changeIcon?: any
}

interface ICStatistic {
  factorName: string
  meanIC: number
  stdIC: number
  icIR: number
  winRate: number
  tStat: number
  pValue: number
  monthlyDecay: number
  stability: string
}

interface DecompositionResult {
  name: string
  contribution: number
  description: string
}

interface PredictiveInsight {
  type: string
  title: string
  content: string
  severity: string
  severityType: string
  icon: any
  iconClass: string
  recommendations?: string[]
}

// 响应式数据
const loading = ref(false)
const mainChartContainer = ref<HTMLElement>()
const distributionChartContainer = ref<HTMLElement>()
const decompositionChartContainer = ref<HTMLElement>()
const predictionChartContainer = ref<HTMLElement>()
const mainChart = ref<echarts.ECharts>()
const distributionChart = ref<echarts.ECharts>()
const decompositionChart = ref<echarts.ECharts>()
const predictionChart = ref<echarts.ECharts>()

// 图表控制
const analysisMode = ref<'ic' | 'rank_ic' | 'ic_ir'>('ic')
const rollingWindow = ref(20)
const selectedFactors = ref<string[]>([])
const showConfidenceBand = ref(true)
const showTrend = ref(true)
const showDistribution = ref(false)
const dateRange = ref<[Date, Date]>([
  new Date(Date.now() - 180 * 24 * 60 * 60 * 1000),
  new Date()
])
const activeTab = ref('statistics')

// 数据
const availableFactors = ref<FactorInfo[]>([
  { id: 'momentum_20', name: '20日动量因子', expression: '($close / Ref($close, 20)) - 1', avgIC: 0.045, icIR: 1.23, category: 'momentum' },
  { id: 'rsi_14', name: 'RSI技术指标', expression: 'RSI($close, 14)', avgIC: 0.032, icIR: 0.89, category: 'technical' },
  { id: 'pe_inverse', name: '市盈率倒数', expression: '1 / $pe_ttm', avgIC: 0.028, icIR: 0.76, category: 'valuation' },
  { id: 'volume_ma', name: '成交量相对均值', expression: '$volume / Mean($volume, 20)', avgIC: 0.025, icIR: 0.68, category: 'volume' },
  { id: 'volatility_20', name: '20日波动率', expression: 'Std(Log($close / Ref($close, 1)), 20)', avgIC: -0.018, icIR: -0.45, category: 'risk' }
])

const icData = ref<Map<string, ICData[]>>(new Map())
const icSummary = ref<ICSummaryItem[]>()
const icStatistics = ref<ICStatistic[]>([])
const decompositionResults = ref<DecompositionResult[]>([])
const predictiveInsights = ref<PredictiveInsight[]>([])

// 方法
const initCharts = async () => {
  if (!mainChartContainer.value) return
  
  mainChart.value = echarts.init(mainChartContainer.value)
  
  if (distributionChartContainer.value) {
    distributionChart.value = echarts.init(distributionChartContainer.value)
  }
  
  if (decompositionChartContainer.value) {
    decompositionChart.value = echarts.init(decompositionChartContainer.value)
  }
  
  if (predictionChartContainer.value) {
    predictionChart.value = echarts.init(predictionChartContainer.value)
  }
  
  initMainChart()
  initDistributionChart()
  initDecompositionChart()
  initPredictionChart()
}

const initMainChart = () => {
  if (!mainChart.value) return
  
  const option = {
    title: {
      text: 'IC时序分析',
      left: 'center',
      textStyle: {
        fontSize: 14,
        fontWeight: 'bold'
      }
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross',
        crossStyle: {
          color: '#999'
        }
      },
      formatter: (params: any[]) => {
        let result = `<div style="font-weight: bold; margin-bottom: 5px;">${params[0].axisValue}</div>`
        params.forEach(param => {
          result += `
            <div style="margin: 2px 0;">
              <span style="color: ${param.color};">●</span>
              ${param.seriesName}: ${param.value?.toFixed(4) || 'N/A'}
            </div>
          `
        })
        return result
      }
    },
    legend: {
      top: 30,
      type: 'scroll'
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '10%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: []
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        formatter: '{value}'
      }
    },
    series: [],
    dataZoom: [
      {
        type: 'inside',
        start: 0,
        end: 100
      },
      {
        show: true,
        type: 'slider',
        top: '90%',
        start: 0,
        end: 100
      }
    ]
  }
  
  mainChart.value.setOption(option)
}

const initDistributionChart = () => {
  if (!distributionChart.value) return
  
  const option = {
    title: {
      text: 'IC分布直方图',
      textStyle: {
        fontSize: 14
      }
    },
    tooltip: {
      trigger: 'item',
      formatter: '{a} <br/>{b}: {c} ({d}%)'
    },
    xAxis: {
      type: 'category',
      data: []
    },
    yAxis: {
      type: 'value'
    },
    series: []
  }
  
  distributionChart.value.setOption(option)
}

const initDecompositionChart = () => {
  if (!decompositionChart.value) return
  
  const option = {
    title: {
      text: 'IC时序分解',
      textStyle: {
        fontSize: 14
      }
    },
    tooltip: {
      trigger: 'axis'
    },
    legend: {},
    xAxis: {
      type: 'category',
      data: []
    },
    yAxis: [
      {
        type: 'value',
        name: '原始IC'
      },
      {
        type: 'value',
        name: '分解成分'
      }
    ],
    series: []
  }
  
  decompositionChart.value.setOption(option)
}

const initPredictionChart = () => {
  if (!predictionChart.value) return
  
  const option = {
    title: {
      text: 'IC预测分析',
      textStyle: {
        fontSize: 14
      }
    },
    tooltip: {
      trigger: 'axis'
    },
    legend: {},
    xAxis: {
      type: 'category',
      data: []
    },
    yAxis: {
      type: 'value'
    },
    series: []
  }
  
  predictionChart.value.setOption(option)
}

const updateChart = async () => {
  if (!mainChart.value || selectedFactors.value.length === 0) return
  
  loading.value = true
  
  try {
    await loadICData()
    
    const dates = getDatesInRange()
    const series: any[] = []
    
    // 为每个选中的因子创建IC时序数据
    for (const factorId of selectedFactors.value) {
      const factorICData = icData.value.get(factorId)
      if (!factorICData) continue
      
      const factor = availableFactors.value.find(f => f.id === factorId)
      if (!factor) continue
      
      let data: number[]
      switch (analysisMode.value) {
        case 'ic':
          data = factorICData.map(item => item.ic)
          break
        case 'rank_ic':
          data = factorICData.map(item => item.rankIC)
          break
        case 'ic_ir':
          data = factorICData.map(item => item.icIR)
          break
        default:
          data = factorICData.map(item => item.ic)
      }
      
      // 应用滚动窗口
      if (rollingWindow.value > 1) {
        data = calculateRollingMean(data, rollingWindow.value)
      }
      
      series.push({
        name: factor.name,
        type: 'line',
        smooth: true,
        data: data,
        lineStyle: {
          width: 2
        }
      })
      
      // 添加置信区间
      if (showConfidenceBand.value) {
        const confidenceUpper = data.map(val => val + 0.02)
        const confidenceLower = data.map(val => val - 0.02)
        
        series.push({
          name: `${factor.name} 上界`,
          type: 'line',
          data: confidenceUpper,
          lineStyle: {
            width: 1,
            type: 'dashed',
            opacity: 0.5
          },
          showSymbol: false,
          showInLegend: false
        })
        
        series.push({
          name: `${factor.name} 下界`,
          type: 'line',
          data: confidenceLower,
          lineStyle: {
            width: 1,
            type: 'dashed',
            opacity: 0.5
          },
          showSymbol: false,
          showInLegend: false,
          areaStyle: {
            opacity: 0.1
          }
        })
      }
      
      // 添加趋势线
      if (showTrend.value) {
        const trendData = calculateTrend(data)
        series.push({
          name: `${factor.name} 趋势`,
          type: 'line',
          data: trendData,
          lineStyle: {
            width: 1,
            type: 'dotted',
            color: '#999'
          },
          showSymbol: false,
          showInLegend: false
        })
      }
    }
    
    mainChart.value.setOption({
      xAxis: {
        data: dates
      },
      series: series
    })
    
    // 更新分布图表
    if (showDistribution.value) {
      updateDistributionChart()
    }
    
    // 计算IC统计
    calculateICStatistics()
    
    // 计算IC摘要
    calculateICSummary()
    
    // 进行时序分解
    performTimeSeriesDecomposition()
    
    // 生成预测性洞察
    generatePredictiveInsights()
    
  } catch (error) {
    console.error('更新图表失败:', error)
    ElMessage.error('更新图表失败')
  } finally {
    loading.value = false
  }
}

const loadICData = async () => {
  // 模拟从Qlib API获取IC数据
  for (const factorId of selectedFactors.value) {
    if (icData.value.has(factorId)) continue
    
    const mockData = generateMockICData(factorId)
    icData.value.set(factorId, mockData)
  }
}

const generateMockICData = (factorId: string): ICData[] => {
  const data: ICData[] = []
  const startDate = dateRange.value[0]
  const endDate = dateRange.value[1]
  const days = Math.floor((endDate.getTime() - startDate.getTime()) / (1000 * 60 * 60 * 24))
  
  const factor = availableFactors.value.find(f => f.id === factorId)
  const baseIC = factor?.avgIC || 0.03
  
  for (let i = 0; i <= days; i++) {
    const currentDate = new Date(startDate.getTime() + i * 24 * 60 * 60 * 1000)
    const dateStr = currentDate.toISOString().split('T')[0]
    
    // 模拟IC时序数据，加入趋势和随机波动
    const trend = Math.sin(i / 30) * 0.01
    const noise = (Math.random() - 0.5) * 0.04
    const ic = baseIC + trend + noise
    
    data.push({
      date: dateStr,
      ic: ic,
      rankIC: ic * 0.9 + (Math.random() - 0.5) * 0.01, // RankIC通常比IC稳定
      icIR: ic / 0.03, // 简化的IR计算
      significance: Math.abs(ic) > 0.02 ? 1 : 0
    })
  }
  
  return data
}

const calculateRollingMean = (data: number[], window: number): number[] => {
  const result: number[] = []
  for (let i = 0; i < data.length; i++) {
    if (i < window - 1) {
      result.push(data[i])
    } else {
      const sum = data.slice(i - window + 1, i + 1).reduce((a, b) => a + b, 0)
      result.push(sum / window)
    }
  }
  return result
}

const calculateTrend = (data: number[]): number[] => {
  const n = data.length
  const x = Array.from({ length: n }, (_, i) => i)
  const y = data
  
  // 线性回归计算趋势线
  const xMean = x.reduce((a, b) => a + b, 0) / n
  const yMean = y.reduce((a, b) => a + b, 0) / n
  
  let numerator = 0
  let denominator = 0
  
  for (let i = 0; i < n; i++) {
    numerator += (x[i] - xMean) * (y[i] - yMean)
    denominator += (x[i] - xMean) ** 2
  }
  
  const slope = numerator / denominator
  const intercept = yMean - slope * xMean
  
  return x.map(xi => slope * xi + intercept)
}

const updateDistributionChart = () => {
  if (!distributionChart.value) return
  
  const allICValues: number[] = []
  for (const factorId of selectedFactors.value) {
    const factorICData = icData.value.get(factorId)
    if (factorICData) {
      allICValues.push(...factorICData.map(d => d.ic))
    }
  }
  
  // 创建直方图数据
  const bins = 20
  const min = Math.min(...allICValues)
  const max = Math.max(...allICValues)
  const binWidth = (max - min) / bins
  
  const histogram = Array(bins).fill(0)
  const binLabels: string[] = []
  
  for (let i = 0; i < bins; i++) {
    const binStart = min + i * binWidth
    const binEnd = min + (i + 1) * binWidth
    binLabels.push(`${binStart.toFixed(3)}-${binEnd.toFixed(3)}`)
    
    histogram[i] = allICValues.filter(val => val >= binStart && val < binEnd).length
  }
  
  distributionChart.value.setOption({
    xAxis: {
      data: binLabels
    },
    series: [{
      name: 'IC分布',
      type: 'bar',
      data: histogram,
      itemStyle: {
        color: '#409eff'
      }
    }]
  })
}

const calculateICStatistics = () => {
  const statistics: ICStatistic[] = []
  
  for (const factorId of selectedFactors.value) {
    const factorICData = icData.value.get(factorId)
    const factor = availableFactors.value.find(f => f.id === factorId)
    
    if (!factorICData || !factor) continue
    
    const icValues = factorICData.map(d => d.ic)
    const meanIC = icValues.reduce((a, b) => a + b, 0) / icValues.length
    const stdIC = Math.sqrt(icValues.reduce((sum, val) => sum + (val - meanIC) ** 2, 0) / icValues.length)
    const icIR = meanIC / stdIC
    const winRate = icValues.filter(val => val > 0).length / icValues.length
    const tStat = meanIC / (stdIC / Math.sqrt(icValues.length))
    const pValue = 2 * (1 - normalCDF(Math.abs(tStat)))
    
    // 计算月衰减率（简化）
    const monthlyDecay = Math.random() * 0.1
    
    // 评估稳定性
    let stability = '差'
    if (Math.abs(icIR) > 1.5) stability = '优秀'
    else if (Math.abs(icIR) > 1.0) stability = '良好'
    else if (Math.abs(icIR) > 0.5) stability = '一般'
    
    statistics.push({
      factorName: factor.name,
      meanIC,
      stdIC,
      icIR,
      winRate,
      tStat,
      pValue,
      monthlyDecay,
      stability
    })
  }
  
  icStatistics.value = statistics
}

const normalCDF = (x: number): number => {
  // 简化的正态分布累积分布函数
  return 0.5 * (1 + Math.sign(x) * Math.sqrt(1 - Math.exp(-2 * x * x / Math.PI)))
}

const calculateICSummary = () => {
  if (selectedFactors.value.length === 0) {
    icSummary.value = []
    return
  }
  
  const allICValues: number[] = []
  for (const factorId of selectedFactors.value) {
    const factorICData = icData.value.get(factorId)
    if (factorICData) {
      allICValues.push(...factorICData.map(d => d.ic))
    }
  }
  
  const avgIC = allICValues.reduce((a, b) => a + b, 0) / allICValues.length
  const maxIC = Math.max(...allICValues)
  const minIC = Math.min(...allICValues)
  const volatility = Math.sqrt(allICValues.reduce((sum, val) => sum + (val - avgIC) ** 2, 0) / allICValues.length)
  
  icSummary.value = [
    {
      label: '平均IC',
      value: avgIC.toFixed(4),
      valueClass: getICClass(avgIC),
      change: '+0.002',
      changeClass: 'positive',
      changeIcon: ArrowUp
    },
    {
      label: '最大IC',
      value: maxIC.toFixed(4),
      valueClass: getICClass(maxIC)
    },
    {
      label: '最小IC',
      value: minIC.toFixed(4),
      valueClass: getICClass(minIC)
    },
    {
      label: 'IC波动率',
      value: volatility.toFixed(4),
      valueClass: volatility > 0.05 ? 'warning' : 'good'
    }
  ]
}

const performTimeSeriesDecomposition = () => {
  // 模拟时序分解结果
  decompositionResults.value = [
    { name: '趋势成分', contribution: 45, description: '长期趋势变化' },
    { name: '季节成分', contribution: 25, description: '周期性波动' },
    { name: '残差成分', contribution: 30, description: '随机噪声和异常值' }
  ]
  
  // 更新分解图表
  if (decompositionChart.value && selectedFactors.value.length > 0) {
    const factorId = selectedFactors.value[0]
    const factorICData = icData.value.get(factorId)
    
    if (factorICData) {
      const dates = factorICData.map(d => d.date)
      const icValues = factorICData.map(d => d.ic)
      
      // 模拟趋势、季节和残差成分
      const trend = icValues.map((_, i) => Math.sin(i / 50) * 0.02)
      const seasonal = icValues.map((_, i) => Math.sin(i / 7) * 0.01)
      const residual = icValues.map((val, i) => val - trend[i] - seasonal[i])
      
      decompositionChart.value.setOption({
        xAxis: { data: dates.slice(-100) }, // 显示最近100个点
        series: [
          {
            name: '原始IC',
            type: 'line',
            yAxisIndex: 0,
            data: icValues.slice(-100),
            lineStyle: { width: 2 }
          },
          {
            name: '趋势成分',
            type: 'line',
            yAxisIndex: 1,
            data: trend.slice(-100),
            lineStyle: { width: 1, type: 'dashed' }
          },
          {
            name: '季节成分',
            type: 'line',
            yAxisIndex: 1,
            data: seasonal.slice(-100),
            lineStyle: { width: 1, type: 'dotted' }
          },
          {
            name: '残差成分',
            type: 'scatter',
            yAxisIndex: 1,
            data: residual.slice(-100),
            symbolSize: 3
          }
        ]
      })
    }
  }
}

const generatePredictiveInsights = () => {
  const insights: PredictiveInsight[] = []
  
  if (icStatistics.value.length > 0) {
    const avgIR = icStatistics.value.reduce((sum, stat) => sum + Math.abs(stat.icIR), 0) / icStatistics.value.length
    
    if (avgIR > 1.0) {
      insights.push({
        type: 'strong_signal',
        title: '因子信号强度高',
        content: `当前选择的因子平均IC_IR为${avgIR.toFixed(2)}，显示出较强的预测能力。`,
        severity: '优秀',
        severityType: 'success',
        icon: Check,
        iconClass: 'success-icon',
        recommendations: [
          '可以增加这些因子在投资策略中的权重',
          '建议定期监控IC稳定性，防止因子失效',
          '考虑与其他类型因子组合，提高策略稳健性'
        ]
      })
    }
    
    const unstableFactors = icStatistics.value.filter(stat => stat.pValue > 0.05)
    if (unstableFactors.length > 0) {
      insights.push({
        type: 'stability_warning',
        title: '因子稳定性预警',
        content: `发现${unstableFactors.length}个因子的IC不够显著(p值>0.05)，可能存在失效风险。`,
        severity: '警告',
        severityType: 'warning',
        icon: Warning,
        iconClass: 'warning-icon',
        recommendations: [
          '建议进一步验证这些因子的有效性',
          '考虑调整因子权重或替换为更稳定的因子',
          '增加样本外测试以验证因子预测能力'
        ]
      })
    }
  }
  
  predictiveInsights.value = insights
  
  // 更新预测图表
  if (predictionChart.value && selectedFactors.value.length > 0) {
    const factorId = selectedFactors.value[0]
    const factorICData = icData.value.get(factorId)
    
    if (factorICData) {
      const dates = factorICData.map(d => d.date)
      const icValues = factorICData.map(d => d.ic)
      
      // 简单的移动平均预测
      const prediction = []
      const confidence = []
      for (let i = 0; i < 30; i++) {
        const futureDate = new Date(new Date(dates[dates.length - 1]).getTime() + (i + 1) * 24 * 60 * 60 * 1000)
        dates.push(futureDate.toISOString().split('T')[0])
        
        const recentAvg = icValues.slice(-20).reduce((a, b) => a + b, 0) / 20
        prediction.push(recentAvg + (Math.random() - 0.5) * 0.01)
        confidence.push(recentAvg + 0.02)
        confidence.push(recentAvg - 0.02)
      }
      
      predictionChart.value.setOption({
        xAxis: { data: dates },
        series: [
          {
            name: '历史IC',
            type: 'line',
            data: [...icValues, ...Array(30).fill(null)],
            lineStyle: { width: 2, color: '#409eff' }
          },
          {
            name: '预测IC',
            type: 'line',
            data: [...Array(icValues.length).fill(null), ...prediction],
            lineStyle: { width: 2, color: '#e6a23c', type: 'dashed' }
          }
        ]
      })
    }
  }
}

const getDatesInRange = (): string[] => {
  const dates: string[] = []
  const current = new Date(dateRange.value[0])
  const end = new Date(dateRange.value[1])
  
  while (current <= end) {
    dates.push(current.toISOString().split('T')[0])
    current.setDate(current.getDate() + 1)
  }
  
  return dates
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
        link.download = `ic-analysis-${Date.now()}.png`
        link.href = url
        link.click()
      }
      break
    case 'csv':
    case 'report':
      ElMessage.info('功能开发中...')
      break
  }
}

// CSS类名辅助方法
const getICClass = (ic: number): string => {
  if (Math.abs(ic) > 0.04) return 'high-ic'
  if (Math.abs(ic) > 0.02) return 'medium-ic'
  return 'low-ic'
}

const getIRClass = (ir: number): string => {
  if (Math.abs(ir) > 1.5) return 'high-ir'
  if (Math.abs(ir) > 1.0) return 'medium-ir'
  return 'low-ir'
}

const getWinRateClass = (winRate: number): string => {
  if (winRate > 0.6) return 'high-win-rate'
  if (winRate > 0.5) return 'medium-win-rate'
  return 'low-win-rate'
}

const getPValueClass = (pValue: number): string => {
  if (pValue < 0.01) return 'very-significant'
  if (pValue < 0.05) return 'significant'
  return 'not-significant'
}

const getStabilityType = (stability: string): string => {
  const typeMap: Record<string, string> = {
    '优秀': 'success',
    '良好': 'success',
    '一般': 'warning',
    '差': 'danger'
  }
  return typeMap[stability] || 'info'
}

// 监听器
watch([analysisMode, rollingWindow, showConfidenceBand, showTrend, showDistribution, dateRange], () => {
  if (selectedFactors.value.length > 0) {
    updateChart()
  }
}, { deep: true })

// 生命周期
onMounted(async () => {
  await nextTick()
  await initCharts()
  
  // 默认选择前两个因子
  selectedFactors.value = availableFactors.value.slice(0, 2).map(f => f.id)
  await updateChart()
})
</script>

<style lang="scss" scoped>
.qlib-ic-analysis-chart {
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

.factor-option {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.factor-stats {
  display: flex;
  gap: 10px;
  font-size: 12px;
  
  .ic-value {
    font-weight: bold;
    
    &.high-ic { color: #67c23a; }
    &.medium-ic { color: #e6a23c; }
    &.low-ic { color: #999; }
  }
  
  .ic-ir-value {
    color: #666;
  }
}

.ic-summary {
  margin-bottom: 20px;
}

.summary-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 15px;
}

.summary-card {
  background: linear-gradient(135deg, #f6f8fa 0%, #e9ecef 100%);
  padding: 15px;
  border-radius: 8px;
  text-align: center;
  border-left: 4px solid #409eff;
}

.stat-label {
  font-size: 13px;
  color: #666;
  margin-bottom: 5px;
}

.stat-value {
  font-size: 18px;
  font-weight: bold;
  margin-bottom: 5px;
  
  &.high-ic, &.positive, &.good { color: #67c23a; }
  &.medium-ic, &.warning { color: #e6a23c; }
  &.low-ic, &.negative { color: #f56c6c; }
}

.stat-change {
  font-size: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 3px;
  
  &.positive { color: #67c23a; }
  &.negative { color: #f56c6c; }
}

.chart-container {
  position: relative;
}

.main-chart {
  width: 100%;
  height: 400px;
  margin-bottom: 20px;
}

.distribution-chart {
  width: 100%;
  height: 300px;
  margin-bottom: 20px;
}

.ic-analysis-detail {
  margin-top: 30px;
}

.statistics-table {
  :deep(.el-table) {
    font-size: 12px;
  }
  
  .high-ic, .high-ir, .high-win-rate, .very-significant {
    color: #67c23a;
    font-weight: bold;
  }
  
  .medium-ic, .medium-ir, .medium-win-rate, .significant {
    color: #e6a23c;
  }
  
  .low-ic, .low-ir, .low-win-rate, .not-significant {
    color: #f56c6c;
  }
}

.decomposition-analysis {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 20px;
  align-items: start;
}

.decomposition-chart {
  height: 300px;
}

.decomposition-summary {
  h4 {
    margin-top: 0;
    color: #2c3e50;
  }
}

.decomposition-components {
  .component-item {
    display: flex;
    flex-direction: column;
    margin-bottom: 15px;
    padding: 10px;
    background: #f8f9fa;
    border-radius: 6px;
    
    .component-name {
      font-weight: bold;
      color: #2c3e50;
    }
    
    .component-value {
      font-size: 16px;
      color: #409eff;
      margin: 5px 0;
    }
    
    .component-desc {
      font-size: 12px;
      color: #666;
    }
  }
}

.prediction-analysis {
  .prediction-chart {
    height: 300px;
    margin-bottom: 20px;
  }
}

.prediction-insights {
  .insight-card {
    margin-bottom: 15px;
    padding: 15px;
    border-radius: 8px;
    border: 1px solid #e4e7ed;
    
    &:last-child {
      margin-bottom: 0;
    }
  }
  
  .insight-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 10px;
    
    .insight-icon {
      &.success-icon { color: #67c23a; }
      &.warning-icon { color: #e6a23c; }
    }
    
    .insight-title {
      font-weight: bold;
      color: #2c3e50;
      flex: 1;
    }
  }
  
  .insight-content {
    color: #555;
    line-height: 1.5;
    margin-bottom: 10px;
  }
  
  .recommendations-title {
    font-weight: 500;
    color: #2c3e50;
    margin-bottom: 8px;
  }
  
  .recommendations-list {
    margin: 0;
    padding-left: 20px;
    
    li {
      color: #555;
      margin: 5px 0;
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
  
  .summary-cards {
    grid-template-columns: 1fr 1fr;
  }
  
  .decomposition-analysis {
    grid-template-columns: 1fr;
  }
  
  .main-chart, .distribution-chart {
    height: 300px;
  }
}
</style>