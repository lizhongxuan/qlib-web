<template>
  <div class="qlib-factor-returns-chart">
    <div class="chart-header">
      <div class="header-left">
        <h3 class="chart-title">
          <el-icon><TrendCharts /></el-icon>
          因子收益分析
        </h3>
        <p class="chart-subtitle">基于Qlib因子表达式的收益率时序分析</p>
      </div>
      <div class="header-right">
        <el-button-group>
          <el-button 
            :type="viewMode === 'cumulative' ? 'primary' : ''" 
            @click="viewMode = 'cumulative'"
            size="small"
          >
            累计收益
          </el-button>
          <el-button 
            :type="viewMode === 'daily' ? 'primary' : ''" 
            @click="viewMode = 'daily'"
            size="small"
          >
            日收益
          </el-button>
          <el-button 
            :type="viewMode === 'rolling' ? 'primary' : ''" 
            @click="viewMode = 'rolling'"
            size="small"
          >
            滚动收益
          </el-button>
        </el-button-group>
        <el-divider direction="vertical" />
        <el-select v-model="timeRange" size="small" style="width: 120px">
          <el-option label="最近1个月" value="1M" />
          <el-option label="最近3个月" value="3M" />
          <el-option label="最近6个月" value="6M" />
          <el-option label="最近1年" value="1Y" />
          <el-option label="全部" value="ALL" />
        </el-select>
        <el-divider direction="vertical" />
        <el-dropdown @command="handleExport">
          <el-button size="small">
            导出 <el-icon><ArrowDown /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="png">导出PNG</el-dropdown-item>
              <el-dropdown-item command="csv">导出CSV</el-dropdown-item>
              <el-dropdown-item command="excel">导出Excel</el-dropdown-item>
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
          placeholder="选择因子进行对比"
          style="width: 300px"
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
              <span class="factor-ic">IC: {{ factor.ic.toFixed(3) }}</span>
            </span>
          </el-option>
        </el-select>
      </div>
      
      <div class="benchmark-selector">
        <el-select v-model="benchmark" size="small" style="width: 150px" @change="updateChart">
          <el-option label="沪深300" value="CSI300" />
          <el-option label="中证500" value="CSI500" />
          <el-option label="创业板指" value="CYBZ" />
          <el-option label="无基准" value="NONE" />
        </el-select>
      </div>

      <div class="analysis-options">
        <el-checkbox v-model="showVolatility" @change="updateChart">显示波动率</el-checkbox>
        <el-checkbox v-model="showDrawdown" @change="updateChart">显示回撤</el-checkbox>
        <el-checkbox v-model="showSharp" @change="updateChart">显示夏普比率</el-checkbox>
      </div>
    </div>

    <div class="chart-container">
      <div 
        ref="chartContainer" 
        class="main-chart"
        v-loading="loading"
        element-loading-text="正在计算因子收益..."
      ></div>
      
      <div class="chart-metrics" v-if="chartMetrics">
        <div class="metrics-grid">
          <div class="metric-item" v-for="metric in displayMetrics" :key="metric.key">
            <div class="metric-label">{{ metric.label }}</div>
            <div class="metric-value" :class="metric.valueClass">
              {{ metric.value }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="factor-analysis" v-if="factorAnalysis.length > 0">
      <el-collapse v-model="activeAnalysis">
        <el-collapse-item title="因子详细分析" name="detail">
          <div class="analysis-table">
            <el-table :data="factorAnalysis" size="small">
              <el-table-column prop="factorName" label="因子名称" width="200" />
              <el-table-column prop="expression" label="因子表达式" min-width="200" />
              <el-table-column prop="ic" label="信息系数(IC)" width="120" sortable>
                <template #default="scope">
                  <span :class="getICClass(scope.row.ic)">
                    {{ scope.row.ic.toFixed(4) }}
                  </span>
                </template>
              </el-table-column>
              <el-table-column prop="icIR" label="IC_IR" width="100" sortable />
              <el-table-column prop="returns" label="年化收益率" width="120" sortable>
                <template #default="scope">
                  <span :class="getReturnsClass(scope.row.returns)">
                    {{ (scope.row.returns * 100).toFixed(2) }}%
                  </span>
                </template>
              </el-table-column>
              <el-table-column prop="volatility" label="年化波动率" width="120" />
              <el-table-column prop="sharpe" label="夏普比率" width="100" sortable />
              <el-table-column prop="maxDrawdown" label="最大回撤" width="120">
                <template #default="scope">
                  <span class="negative">
                    {{ (scope.row.maxDrawdown * 100).toFixed(2) }}%
                  </span>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-collapse-item>
        
        <el-collapse-item title="AI投资洞察" name="insights" v-if="aiInsights">
          <div class="ai-insights">
            <div class="insight-item" v-for="insight in aiInsights" :key="insight.type">
              <div class="insight-header">
                <el-icon class="insight-icon"><Cpu /></el-icon>
                <span class="insight-title">{{ insight.title }}</span>
                <el-tag :type="getInsightType(insight.confidence)" size="small">
                  置信度: {{ (insight.confidence * 100).toFixed(0) }}%
                </el-tag>
              </div>
              <div class="insight-content">{{ insight.content }}</div>
              <div class="insight-suggestions" v-if="insight.suggestions">
                <div class="suggestions-title">投资建议:</div>
                <ul class="suggestions-list">
                  <li v-for="suggestion in insight.suggestions" :key="suggestion">
                    {{ suggestion }}
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </el-collapse-item>
      </el-collapse>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, computed, nextTick } from 'vue'
import * as echarts from 'echarts'
import { TrendCharts, ArrowDown, Cpu } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useQlibFactorsStore } from '@/stores/qlib-factors'

interface FactorReturnsData {
  date: string
  factorValue: number
  returns: number
  cumulativeReturns: number
  benchmarkReturns?: number
  volatility?: number
  drawdown?: number
}

interface FactorInfo {
  id: string
  name: string
  expression: string
  ic: number
  category: string
}

interface ChartMetric {
  label: string
  value: string
  key: string
  valueClass?: string
}

interface FactorAnalysisItem {
  factorName: string
  expression: string
  ic: number
  icIR: number
  returns: number
  volatility: number
  sharpe: number
  maxDrawdown: number
}

interface AIInsight {
  type: string
  title: string
  content: string
  confidence: number
  suggestions?: string[]
}

// 响应式数据
const loading = ref(false)
const chartContainer = ref<HTMLElement>()
const chart = ref<echarts.ECharts>()

// 图表控制
const viewMode = ref<'cumulative' | 'daily' | 'rolling'>('cumulative')
const timeRange = ref('3M')
const selectedFactors = ref<string[]>([])
const benchmark = ref('CSI300')
const showVolatility = ref(false)
const showDrawdown = ref(true)
const showSharp = ref(false)

// 数据
const availableFactors = ref<FactorInfo[]>([
  { id: 'momentum_20', name: '20日动量因子', expression: '($close / Ref($close, 20)) - 1', ic: 0.045, category: 'momentum' },
  { id: 'rsi_14', name: 'RSI技术指标', expression: 'RSI($close, 14)', ic: 0.032, category: 'technical' },
  { id: 'pe_inverse', name: '市盈率倒数', expression: '1 / $pe_ttm', ic: 0.028, category: 'valuation' },
  { id: 'volume_ma', name: '成交量相对均值', expression: '$volume / Mean($volume, 20)', ic: 0.025, category: 'volume' },
  { id: 'volatility_20', name: '20日波动率', expression: 'Std(Log($close / Ref($close, 1)), 20)', ic: -0.018, category: 'risk' }
])

const factorReturnsData = ref<Map<string, FactorReturnsData[]>>(new Map())
const chartMetrics = ref<ChartMetric[]>()
const factorAnalysis = ref<FactorAnalysisItem[]>([])
const aiInsights = ref<AIInsight[]>()
const activeAnalysis = ref(['detail'])

// Store
const qlibFactorsStore = useQlibFactorsStore()

// 计算属性
const displayMetrics = computed(() => {
  if (!chartMetrics.value) return []
  return chartMetrics.value.map(metric => ({
    ...metric,
    valueClass: getMetricClass(metric.key, metric.value)
  }))
})

// 方法
const initChart = async () => {
  if (!chartContainer.value) return
  
  chart.value = echarts.init(chartContainer.value)
  
  const option = {
    title: {
      text: '因子收益分析',
      left: 'center',
      textStyle: {
        fontSize: 16,
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
          const value = viewMode.value === 'cumulative' 
            ? (param.value * 100).toFixed(2) + '%'
            : (param.value * 100).toFixed(3) + '%'
          result += `
            <div style="margin: 2px 0;">
              <span style="color: ${param.color};">●</span>
              ${param.seriesName}: ${value}
            </div>
          `
        })
        return result
      }
    },
    legend: {
      top: 30,
      type: 'scroll',
      pageButtonPosition: 'end'
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: showDrawdown.value || showVolatility.value ? '35%' : '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: []
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        formatter: viewMode.value === 'cumulative' ? '{value}%' : '{value}%'
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
    ],
    toolbox: {
      feature: {
        dataZoom: {
          yAxisIndex: 'none'
        },
        restore: {},
        saveAsImage: {}
      }
    }
  }
  
  chart.value.setOption(option)
}

const updateChart = async () => {
  if (!chart.value || selectedFactors.value.length === 0) return
  
  loading.value = true
  
  try {
    // 获取因子数据
    await loadFactorData()
    
    const dates = getDatesForTimeRange()
    const series: any[] = []
    
    // 为每个选中的因子创建数据系列
    for (const factorId of selectedFactors.value) {
      const factorData = factorReturnsData.value.get(factorId)
      if (!factorData) continue
      
      const factor = availableFactors.value.find(f => f.id === factorId)
      if (!factor) continue
      
      const data = factorData
        .filter(item => dates.includes(item.date))
        .map(item => {
          switch (viewMode.value) {
            case 'cumulative':
              return (item.cumulativeReturns * 100).toFixed(2)
            case 'daily':
              return (item.returns * 100).toFixed(3)
            case 'rolling':
              return (item.returns * 100).toFixed(3) // 这里可以计算滚动收益
            default:
              return item.cumulativeReturns * 100
          }
        })
      
      series.push({
        name: factor.name,
        type: 'line',
        smooth: true,
        data: data,
        lineStyle: {
          width: 2
        },
        emphasis: {
          focus: 'series'
        }
      })
    }
    
    // 添加基准数据
    if (benchmark.value !== 'NONE') {
      const benchmarkData = generateBenchmarkData(dates)
      series.push({
        name: benchmark.value,
        type: 'line',
        smooth: true,
        data: benchmarkData,
        lineStyle: {
          type: 'dashed',
          width: 2,
          color: '#999'
        }
      })
    }
    
    // 添加回撤数据（如果启用）
    if (showDrawdown.value) {
      // 在下方添加回撤图表
      const option = chart.value.getOption() as any
      option.grid = [
        {
          left: '3%',
          right: '4%',
          height: '50%',
          containLabel: true
        },
        {
          left: '3%',
          right: '4%',
          top: '70%',
          height: '25%',
          containLabel: true
        }
      ]
      
      option.yAxis = [
        {
          type: 'value',
          gridIndex: 0,
          axisLabel: {
            formatter: '{value}%'
          }
        },
        {
          type: 'value',
          gridIndex: 1,
          axisLabel: {
            formatter: '{value}%'
          },
          max: 0
        }
      ]
      
      option.xAxis = [
        {
          type: 'category',
          gridIndex: 0,
          data: dates
        },
        {
          type: 'category',
          gridIndex: 1,
          data: dates
        }
      ]
      
      // 添加回撤数据系列
      for (const factorId of selectedFactors.value) {
        const factorData = factorReturnsData.value.get(factorId)
        if (!factorData) continue
        
        const factor = availableFactors.value.find(f => f.id === factorId)
        if (!factor) continue
        
        const drawdownData = factorData
          .filter(item => dates.includes(item.date))
          .map(item => (item.drawdown || 0) * 100)
        
        series.push({
          name: `${factor.name} 回撤`,
          type: 'line',
          xAxisIndex: 1,
          yAxisIndex: 1,
          data: drawdownData,
          lineStyle: {
            width: 1,
            opacity: 0.7
          },
          areaStyle: {
            color: 'rgba(255, 0, 0, 0.1)'
          }
        })
      }
    }
    
    chart.value.setOption({
      xAxis: showDrawdown.value ? [{ data: dates }, { data: dates }] : { data: dates },
      series: series,
      legend: {
        data: series.map(s => s.name)
      }
    })
    
    // 计算图表指标
    calculateChartMetrics()
    
    // 生成AI洞察
    generateAIInsights()
    
  } catch (error) {
    console.error('更新图表失败:', error)
    ElMessage.error('更新图表失败')
  } finally {
    loading.value = false
  }
}

const loadFactorData = async () => {
  // 模拟从Qlib API获取因子数据
  for (const factorId of selectedFactors.value) {
    if (factorReturnsData.value.has(factorId)) continue
    
    const mockData = generateMockFactorData(factorId)
    factorReturnsData.value.set(factorId, mockData)
  }
}

const generateMockFactorData = (factorId: string): FactorReturnsData[] => {
  const data: FactorReturnsData[] = []
  const startDate = new Date('2023-01-01')
  const endDate = new Date()
  const days = Math.floor((endDate.getTime() - startDate.getTime()) / (1000 * 60 * 60 * 24))
  
  let cumulativeReturns = 0
  let peak = 0
  
  for (let i = 0; i <= days; i++) {
    const currentDate = new Date(startDate.getTime() + i * 24 * 60 * 60 * 1000)
    const dateStr = currentDate.toISOString().split('T')[0]
    
    // 模拟因子收益
    const baseReturn = (Math.random() - 0.5) * 0.02 // 日收益率在-1%到1%之间
    const factorMultiplier = getFactorMultiplier(factorId)
    const dailyReturn = baseReturn * factorMultiplier
    
    cumulativeReturns += dailyReturn
    peak = Math.max(peak, cumulativeReturns)
    const drawdown = (peak - cumulativeReturns) / (1 + peak)
    
    data.push({
      date: dateStr,
      factorValue: Math.random(),
      returns: dailyReturn,
      cumulativeReturns: cumulativeReturns,
      volatility: Math.abs(dailyReturn) * 2,
      drawdown: -drawdown
    })
  }
  
  return data
}

const getFactorMultiplier = (factorId: string): number => {
  const multipliers: Record<string, number> = {
    'momentum_20': 1.2,
    'rsi_14': 0.8,
    'pe_inverse': 1.0,
    'volume_ma': 1.1,
    'volatility_20': 0.7
  }
  return multipliers[factorId] || 1.0
}

const generateBenchmarkData = (dates: string[]): number[] => {
  return dates.map(() => {
    // 模拟基准收益
    const baseReturn = (Math.random() - 0.48) * 0.01 // 略偏正的收益
    return (baseReturn * 100).toFixed(2)
  })
}

const getDatesForTimeRange = (): string[] => {
  const endDate = new Date()
  let startDate: Date
  
  switch (timeRange.value) {
    case '1M':
      startDate = new Date(endDate.getTime() - 30 * 24 * 60 * 60 * 1000)
      break
    case '3M':
      startDate = new Date(endDate.getTime() - 90 * 24 * 60 * 60 * 1000)
      break
    case '6M':
      startDate = new Date(endDate.getTime() - 180 * 24 * 60 * 60 * 1000)
      break
    case '1Y':
      startDate = new Date(endDate.getTime() - 365 * 24 * 60 * 60 * 1000)
      break
    default:
      startDate = new Date('2023-01-01')
  }
  
  const dates: string[] = []
  const current = new Date(startDate)
  
  while (current <= endDate) {
    dates.push(current.toISOString().split('T')[0])
    current.setDate(current.getDate() + 1)
  }
  
  return dates
}

const calculateChartMetrics = () => {
  if (selectedFactors.value.length === 0) {
    chartMetrics.value = []
    return
  }
  
  const metrics: ChartMetric[] = []
  
  for (const factorId of selectedFactors.value) {
    const factorData = factorReturnsData.value.get(factorId)
    if (!factorData) continue
    
    const factor = availableFactors.value.find(f => f.id === factorId)
    if (!factor) continue
    
    const returns = factorData.map(d => d.returns)
    const cumulativeReturn = factorData[factorData.length - 1]?.cumulativeReturns || 0
    const volatility = Math.sqrt(returns.reduce((sum, r) => sum + r * r, 0) / returns.length) * Math.sqrt(252)
    const sharpe = returns.length > 0 ? (cumulativeReturn / returns.length * 252) / volatility : 0
    const maxDrawdown = Math.min(...factorData.map(d => d.drawdown || 0))
    
    metrics.push(
      { label: `${factor.name} 累计收益`, value: `${(cumulativeReturn * 100).toFixed(2)}%`, key: 'returns' },
      { label: `${factor.name} 年化波动率`, value: `${(volatility * 100).toFixed(2)}%`, key: 'volatility' },
      { label: `${factor.name} 夏普比率`, value: sharpe.toFixed(3), key: 'sharpe' },
      { label: `${factor.name} 最大回撤`, value: `${(Math.abs(maxDrawdown) * 100).toFixed(2)}%`, key: 'drawdown' }
    )
  }
  
  chartMetrics.value = metrics
  
  // 更新因子分析表格
  updateFactorAnalysis()
}

const updateFactorAnalysis = () => {
  const analysis: FactorAnalysisItem[] = []
  
  for (const factorId of selectedFactors.value) {
    const factor = availableFactors.value.find(f => f.id === factorId)
    const factorData = factorReturnsData.value.get(factorId)
    
    if (!factor || !factorData) continue
    
    const returns = factorData.map(d => d.returns)
    const cumulativeReturn = factorData[factorData.length - 1]?.cumulativeReturns || 0
    const volatility = Math.sqrt(returns.reduce((sum, r) => sum + r * r, 0) / returns.length) * Math.sqrt(252)
    const sharpe = returns.length > 0 ? (cumulativeReturn / returns.length * 252) / volatility : 0
    const maxDrawdown = Math.min(...factorData.map(d => d.drawdown || 0))
    const icIR = factor.ic / Math.sqrt(0.02) // 简化计算
    
    analysis.push({
      factorName: factor.name,
      expression: factor.expression,
      ic: factor.ic,
      icIR: icIR,
      returns: cumulativeReturn / (factorData.length / 252), // 年化收益
      volatility: volatility,
      sharpe: sharpe,
      maxDrawdown: Math.abs(maxDrawdown)
    })
  }
  
  factorAnalysis.value = analysis
}

const generateAIInsights = () => {
  const insights: AIInsight[] = []
  
  if (selectedFactors.value.length > 0) {
    // 生成基于因子表现的AI洞察
    const bestFactor = factorAnalysis.value.reduce((prev, current) => 
      prev.sharpe > current.sharpe ? prev : current
    )
    
    insights.push({
      type: 'performance',
      title: '因子表现分析',
      content: `在当前选择的因子中，${bestFactor.factorName}表现最佳，夏普比率达到${bestFactor.sharpe.toFixed(3)}，显示出良好的风险调整后收益。`,
      confidence: 0.85,
      suggestions: [
        `考虑增加${bestFactor.factorName}在投资组合中的权重`,
        '建议结合其他类型因子以降低单一因子风险',
        '定期监控因子IC稳定性，及时调整策略'
      ]
    })
    
    if (factorAnalysis.value.some(f => Math.abs(f.ic) > 0.04)) {
      insights.push({
        type: 'ic_analysis',
        title: 'IC分析洞察',
        content: '检测到部分因子IC值较高，表明因子具有较强的预测能力，但需要关注IC的时间稳定性。',
        confidence: 0.78,
        suggestions: [
          '建议进行IC衰减分析，评估因子长期有效性',
          '考虑因子轮动策略，根据IC变化调整权重'
        ]
      })
    }
  }
  
  aiInsights.value = insights
}

const handleExport = (command: string) => {
  switch (command) {
    case 'png':
      if (chart.value) {
        const url = chart.value.getDataURL({
          pixelRatio: 2,
          backgroundColor: '#fff'
        })
        const link = document.createElement('a')
        link.download = `factor-returns-${Date.now()}.png`
        link.href = url
        link.click()
      }
      break
    case 'csv':
    case 'excel':
      ElMessage.info('导出功能开发中...')
      break
  }
}

const getICClass = (ic: number): string => {
  if (Math.abs(ic) > 0.04) return 'high-ic'
  if (Math.abs(ic) > 0.02) return 'medium-ic'
  return 'low-ic'
}

const getReturnsClass = (returns: number): string => {
  if (returns > 0.1) return 'high-returns'
  if (returns > 0.05) return 'positive'
  return 'negative'
}

const getMetricClass = (key: string, value: string): string => {
  if (key === 'returns') {
    const numValue = parseFloat(value)
    return numValue > 0 ? 'positive' : 'negative'
  }
  if (key === 'sharpe') {
    const numValue = parseFloat(value)
    return numValue > 1 ? 'good' : numValue > 0.5 ? 'medium' : 'poor'
  }
  return ''
}

const getInsightType = (confidence: number): string => {
  if (confidence > 0.8) return 'success'
  if (confidence > 0.6) return 'warning'
  return 'info'
}

// 监听器
watch([viewMode, timeRange, benchmark, showVolatility, showDrawdown, showSharp], () => {
  if (selectedFactors.value.length > 0) {
    updateChart()
  }
}, { deep: true })

// 生命周期
onMounted(async () => {
  await nextTick()
  await initChart()
  
  // 默认选择前两个因子
  selectedFactors.value = availableFactors.value.slice(0, 2).map(f => f.id)
  await updateChart()
})

// 暴露给模板的方法
defineExpose({
  updateChart,
  exportChart: () => handleExport('png')
})
</script>

<style lang="scss" scoped>
.qlib-factor-returns-chart {
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

.header-right {
  display: flex;
  align-items: center;
  gap: 10px;
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

.factor-selector {
  .factor-option {
    display: flex;
    justify-content: space-between;
    align-items: center;
    width: 100%;
  }
  
  .factor-name {
    font-weight: 500;
  }
  
  .factor-ic {
    font-size: 12px;
    color: #666;
    margin-left: 10px;
  }
}

.analysis-options {
  display: flex;
  gap: 15px;
}

.chart-container {
  position: relative;
}

.main-chart {
  width: 100%;
  height: 500px;
}

.chart-metrics {
  margin-top: 20px;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 6px;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 15px;
}

.metric-item {
  text-align: center;
  
  .metric-label {
    font-size: 12px;
    color: #666;
    margin-bottom: 4px;
  }
  
  .metric-value {
    font-size: 16px;
    font-weight: bold;
    
    &.positive {
      color: #67c23a;
    }
    
    &.negative {
      color: #f56c6c;
    }
    
    &.good {
      color: #67c23a;
    }
    
    &.medium {
      color: #e6a23c;
    }
    
    &.poor {
      color: #f56c6c;
    }
  }
}

.factor-analysis {
  margin-top: 20px;
}

.analysis-table {
  :deep(.el-table) {
    font-size: 12px;
  }
  
  .high-ic {
    color: #67c23a;
    font-weight: bold;
  }
  
  .medium-ic {
    color: #e6a23c;
  }
  
  .low-ic {
    color: #999;
  }
  
  .high-returns {
    color: #67c23a;
    font-weight: bold;
  }
  
  .positive {
    color: #67c23a;
  }
  
  .negative {
    color: #f56c6c;
  }
}

.ai-insights {
  .insight-item {
    margin-bottom: 20px;
    padding: 15px;
    background: linear-gradient(135deg, #f6f8ff 0%, #e8f4f8 100%);
    border-left: 4px solid #409eff;
    border-radius: 6px;
    
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
      color: #409eff;
    }
    
    .insight-title {
      font-weight: bold;
      color: #2c3e50;
    }
  }
  
  .insight-content {
    color: #555;
    line-height: 1.5;
    margin-bottom: 10px;
  }
  
  .suggestions-title {
    font-weight: 500;
    color: #2c3e50;
    margin-bottom: 5px;
  }
  
  .suggestions-list {
    margin: 0;
    padding-left: 20px;
    
    li {
      color: #555;
      margin: 3px 0;
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
    gap: 15px;
  }
  
  .metrics-grid {
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  }
  
  .main-chart {
    height: 350px;
  }
}
</style>