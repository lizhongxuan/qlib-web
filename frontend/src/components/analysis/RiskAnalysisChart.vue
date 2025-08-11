<template>
  <div class="risk-analysis-chart">
    <div class="chart-header">
      <h3>风险分析</h3>
      <div class="chart-controls">
        <el-select v-model="viewType" size="small" @change="updateChart">
          <el-option label="风险概览" value="overview" />
          <el-option label="VaR分析" value="var" />
          <el-option label="回撤分析" value="drawdown" />
          <el-option label="滚动风险" value="rolling" />
        </el-select>
      </div>
    </div>
    
    <div class="chart-content">
      <!-- 风险指标卡片 -->
      <div v-if="viewType === 'overview'" class="risk-metrics">
        <div class="metrics-row">
          <div class="metric-card risk">
            <div class="metric-icon">⚠️</div>
            <div class="metric-info">
              <div class="metric-value">{{ formatPercent(data?.var_95) }}</div>
              <div class="metric-label">VaR (95%)</div>
            </div>
          </div>
          
          <div class="metric-card risk">
            <div class="metric-icon">📉</div>
            <div class="metric-info">
              <div class="metric-value">{{ formatPercent(data?.max_drawdown) }}</div>
              <div class="metric-label">最大回撤</div>
            </div>
          </div>
          
          <div class="metric-card performance">
            <div class="metric-icon">📊</div>
            <div class="metric-info">
              <div class="metric-value">{{ formatNumber(data?.sharpe_ratio) }}</div>
              <div class="metric-label">夏普比率</div>
            </div>
          </div>
          
          <div class="metric-card volatility">
            <div class="metric-icon">🌊</div>
            <div class="metric-info">
              <div class="metric-value">{{ formatPercent(data?.volatility) }}</div>
              <div class="metric-label">波动率</div>
            </div>
          </div>
        </div>
        
        <div class="metrics-row">
          <div class="metric-card">
            <div class="metric-icon">📈</div>
            <div class="metric-info">
              <div class="metric-value">{{ formatNumber(data?.sortino_ratio) }}</div>
              <div class="metric-label">索提诺比率</div>
            </div>
          </div>
          
          <div class="metric-card">
            <div class="metric-icon">📏</div>
            <div class="metric-info">
              <div class="metric-value">{{ formatNumber(data?.calmar_ratio) }}</div>
              <div class="metric-label">卡玛比率</div>
            </div>
          </div>
          
          <div class="metric-card">
            <div class="metric-icon">🎯</div>
            <div class="metric-info">
              <div class="metric-value">{{ formatNumber(data?.correlation_with_benchmark) }}</div>
              <div class="metric-label">基准相关性</div>
            </div>
          </div>
          
          <div class="metric-card">
            <div class="metric-icon">⬇️</div>
            <div class="metric-info">
              <div class="metric-value">{{ formatPercent(data?.downside_deviation) }}</div>
              <div class="metric-label">下行偏差</div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 图表容器 -->
      <div ref="chartContainer" class="chart-container"></div>
      
      <!-- 风险等级评估 -->
      <div v-if="viewType === 'overview'" class="risk-assessment">
        <h4>风险等级评估</h4>
        <div class="risk-level">
          <div class="risk-indicator" :class="riskLevel.class">
            <div class="risk-dot"></div>
            <span>{{ riskLevel.label }}</span>
          </div>
          <div class="risk-description">
            {{ riskLevel.description }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, computed, nextTick } from 'vue'
import * as echarts from 'echarts'

interface RiskAnalysisData {
  var_95: number
  var_99: number
  max_drawdown: number
  volatility: number
  sharpe_ratio: number
  sortino_ratio?: number
  calmar_ratio?: number
  correlation_with_benchmark: number
  downside_deviation?: number
  risk_metrics_series?: {
    rolling_volatility: number[]
    rolling_var: number[]
    drawdown_series: number[]
  }
}

interface Props {
  data: RiskAnalysisData | null
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  loading: false
})

const chartContainer = ref<HTMLElement>()
const viewType = ref('overview')
let chart: echarts.ECharts | null = null

// 计算风险等级
const riskLevel = computed(() => {
  if (!props.data) return { class: 'unknown', label: '未知', description: '暂无数据' }
  
  const volatility = props.data.volatility || 0
  const maxDrawdown = Math.abs(props.data.max_drawdown || 0)
  const sharpe = props.data.sharpe_ratio || 0
  
  // 简化的风险评级逻辑
  const riskScore = volatility * 100 + maxDrawdown * 100 - sharpe * 10
  
  if (riskScore < 10) {
    return {
      class: 'low',
      label: '低风险',
      description: '波动性较小，回撤控制良好，适合稳健投资者'
    }
  } else if (riskScore < 25) {
    return {
      class: 'medium',
      label: '中等风险',
      description: '风险收益比较均衡，适合一般投资者'
    }
  } else if (riskScore < 40) {
    return {
      class: 'high',
      label: '高风险',
      description: '波动性较大，潜在回撤风险高，适合激进投资者'
    }
  } else {
    return {
      class: 'very-high',
      label: '极高风险',
      description: '风险极高，需谨慎投资，建议专业投资者参与'
    }
  }
})

// 格式化函数
const formatPercent = (value: number | undefined) => {
  if (value === undefined || value === null) return '--'
  return `${(value * 100).toFixed(2)}%`
}

const formatNumber = (value: number | undefined) => {
  if (value === undefined || value === null) return '--'
  return value.toFixed(3)
}

// 创建图表
const createChart = () => {
  if (!chartContainer.value || !props.data) return
  
  chart = echarts.init(chartContainer.value)
  updateChart()
}

// 更新图表
const updateChart = () => {
  if (!chart || !props.data) return
  
  let option: any = {}
  
  switch (viewType.value) {
    case 'overview':
      option = createOverviewChart()
      break
    case 'var':
      option = createVaRChart()
      break
    case 'drawdown':
      option = createDrawdownChart()
      break
    case 'rolling':
      option = createRollingRiskChart()
      break
  }
  
  chart.setOption(option, true)
}

// 风险概览图表
const createOverviewChart = () => {
  const data = props.data!
  
  return {
    title: {
      text: '风险指标对比',
      left: 'center',
      textStyle: { fontSize: 14 }
    },
    tooltip: {
      trigger: 'axis',
      formatter: '{b}: {c}'
    },
    radar: {
      indicator: [
        { name: '波动率', max: 0.5, min: 0 },
        { name: '最大回撤', max: 0.3, min: 0 },
        { name: 'VaR(95%)', max: 0.1, min: 0 },
        { name: '下行偏差', max: 0.3, min: 0 },
        { name: '夏普比率', max: 3, min: -1 }
      ],
      center: ['50%', '60%'],
      radius: '70%'
    },
    series: [{
      type: 'radar',
      data: [{
        value: [
          data.volatility || 0,
          Math.abs(data.max_drawdown || 0),
          Math.abs(data.var_95 || 0),
          data.downside_deviation || 0,
          Math.max(-1, Math.min(3, data.sharpe_ratio || 0))
        ],
        name: '风险指标',
        areaStyle: {
          opacity: 0.3,
          color: '#F56C6C'
        },
        itemStyle: {
          color: '#F56C6C'
        }
      }]
    }]
  }
}

// VaR分析图表
const createVaRChart = () => {
  const data = props.data!
  
  // 模拟VaR分布数据
  const returns = Array.from({length: 100}, () => Math.random() * 0.08 - 0.04)
  returns.sort((a, b) => a - b)
  
  const var95Index = Math.floor(returns.length * 0.05)
  const var99Index = Math.floor(returns.length * 0.01)
  
  return {
    title: {
      text: 'VaR分析 - 收益率分布',
      left: 'center',
      textStyle: { fontSize: 14 }
    },
    tooltip: {
      trigger: 'axis',
      formatter: function(params: any) {
        return `收益率: ${(params[0].value * 100).toFixed(2)}%`
      }
    },
    xAxis: {
      type: 'value',
      name: '收益率(%)',
      axisLabel: {
        formatter: function(value: number) {
          return (value * 100).toFixed(1) + '%'
        }
      }
    },
    yAxis: {
      type: 'value',
      name: '频次'
    },
    series: [
      {
        name: '收益率分布',
        type: 'bar',
        data: returns.map((ret, index) => [ret, 1]),
        itemStyle: {
          color: function(params: any) {
            const value = params.data[0]
            if (value <= data.var_99) return '#F56C6C' // 99% VaR
            if (value <= data.var_95) return '#E6A23C' // 95% VaR
            return '#409EFF'
          }
        }
      }
    ],
    markLine: {
      data: [
        { 
          xAxis: data.var_95, 
          name: 'VaR 95%',
          label: { formatter: 'VaR 95%: {c}%' }
        },
        { 
          xAxis: data.var_99, 
          name: 'VaR 99%',
          label: { formatter: 'VaR 99%: {c}%' }
        }
      ],
      lineStyle: { color: '#F56C6C' },
      label: { color: '#F56C6C' }
    }
  }
}

// 回撤分析图表
const createDrawdownChart = () => {
  const drawdownSeries = props.data?.risk_metrics_series?.drawdown_series || 
    Array.from({length: 252}, (_, i) => Math.max(-0.15, Math.random() * 0.05 - 0.08))
  
  const dates = Array.from({length: drawdownSeries.length}, (_, i) => {
    const date = new Date()
    date.setDate(date.getDate() - drawdownSeries.length + i + 1)
    return date.toLocaleDateString()
  })
  
  return {
    title: {
      text: '回撤分析',
      left: 'center',
      textStyle: { fontSize: 14 }
    },
    tooltip: {
      trigger: 'axis',
      formatter: function(params: any) {
        return `${params[0].name}<br/>回撤: ${(params[0].value * 100).toFixed(2)}%`
      }
    },
    xAxis: {
      type: 'category',
      data: dates,
      axisLabel: {
        rotate: 45,
        interval: Math.floor(dates.length / 10)
      }
    },
    yAxis: {
      type: 'value',
      name: '回撤(%)',
      axisLabel: {
        formatter: function(value: number) {
          return (value * 100).toFixed(1) + '%'
        }
      }
    },
    series: [{
      name: '回撤',
      type: 'line',
      data: drawdownSeries,
      areaStyle: {
        color: 'rgba(245, 108, 108, 0.3)'
      },
      itemStyle: {
        color: '#F56C6C'
      },
      smooth: true
    }],
    markLine: {
      data: [{
        yAxis: props.data?.max_drawdown || 0,
        name: '最大回撤',
        label: {
          formatter: '最大回撤: {c}%'
        }
      }],
      lineStyle: { color: '#E6A23C', type: 'dashed' },
      label: { color: '#E6A23C' }
    }
  }
}

// 滚动风险图表
const createRollingRiskChart = () => {
  const volatilitySeries = props.data?.risk_metrics_series?.rolling_volatility ||
    Array.from({length: 252}, () => Math.random() * 0.3 + 0.1)
  
  const varSeries = props.data?.risk_metrics_series?.rolling_var ||
    Array.from({length: 252}, () => Math.random() * -0.05 - 0.02)
  
  const dates = Array.from({length: volatilitySeries.length}, (_, i) => {
    const date = new Date()
    date.setDate(date.getDate() - volatilitySeries.length + i + 1)
    return date.toLocaleDateString()
  })
  
  return {
    title: {
      text: '滚动风险指标',
      left: 'center',
      textStyle: { fontSize: 14 }
    },
    tooltip: {
      trigger: 'axis',
      formatter: function(params: any) {
        return `${params[0].name}<br/>
                滚动波动率: ${(params[0].value * 100).toFixed(2)}%<br/>
                滚动VaR: ${(params[1].value * 100).toFixed(2)}%`
      }
    },
    legend: {
      data: ['滚动波动率', '滚动VaR'],
      top: 30
    },
    xAxis: {
      type: 'category',
      data: dates,
      axisLabel: {
        rotate: 45,
        interval: Math.floor(dates.length / 10)
      }
    },
    yAxis: [
      {
        type: 'value',
        name: '波动率(%)',
        position: 'left',
        axisLabel: {
          formatter: function(value: number) {
            return (value * 100).toFixed(1) + '%'
          }
        }
      },
      {
        type: 'value',
        name: 'VaR(%)',
        position: 'right',
        axisLabel: {
          formatter: function(value: number) {
            return (value * 100).toFixed(1) + '%'
          }
        }
      }
    ],
    series: [
      {
        name: '滚动波动率',
        type: 'line',
        yAxisIndex: 0,
        data: volatilitySeries,
        itemStyle: { color: '#409EFF' },
        smooth: true
      },
      {
        name: '滚动VaR',
        type: 'line',
        yAxisIndex: 1,
        data: varSeries,
        itemStyle: { color: '#F56C6C' },
        smooth: true
      }
    ]
  }
}

// 生命周期和监听器
onMounted(() => {
  nextTick(() => {
    createChart()
  })
})

watch(() => props.data, () => {
  nextTick(() => {
    if (chart) {
      updateChart()
    } else {
      createChart()
    }
  })
}, { deep: true })

// 窗口大小变化时调整图表
window.addEventListener('resize', () => {
  chart?.resize()
})
</script>

<style scoped>
.risk-analysis-chart {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.chart-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.chart-content {
  min-height: 400px;
}

.risk-metrics {
  margin-bottom: 20px;
}

.metrics-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 16px;
  margin-bottom: 16px;
}

.metric-card {
  display: flex;
  align-items: center;
  background: #f8f9fa;
  padding: 16px;
  border-radius: 6px;
  border: 1px solid #e4e7ed;
  transition: all 0.3s ease;
}

.metric-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.metric-card.risk {
  border-left: 4px solid #F56C6C;
}

.metric-card.performance {
  border-left: 4px solid #67C23A;
}

.metric-card.volatility {
  border-left: 4px solid #E6A23C;
}

.metric-icon {
  font-size: 24px;
  margin-right: 12px;
}

.metric-info {
  flex: 1;
}

.metric-value {
  font-size: 20px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 2px;
}

.metric-label {
  font-size: 12px;
  color: #909399;
}

.chart-container {
  width: 100%;
  height: 400px;
}

.risk-assessment {
  margin-top: 20px;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 6px;
}

.risk-assessment h4 {
  margin: 0 0 12px 0;
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.risk-level {
  display: flex;
  align-items: center;
  gap: 12px;
}

.risk-indicator {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 600;
  font-size: 14px;
}

.risk-indicator.low {
  color: #67C23A;
}

.risk-indicator.medium {
  color: #E6A23C;
}

.risk-indicator.high {
  color: #F56C6C;
}

.risk-indicator.very-high {
  color: #F56C6C;
}

.risk-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: currentColor;
}

.risk-description {
  font-size: 12px;
  color: #606266;
}

:deep(.el-select) {
  width: 120px;
}
</style>