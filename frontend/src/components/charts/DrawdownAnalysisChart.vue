<template>
  <div class="drawdown-analysis-chart">
    <div class="chart-header">
      <h3>回撤分析</h3>
      <div class="chart-controls">
        <el-select v-model="selectedMetric" @change="updateChart" style="width: 120px;">
          <el-option label="最大回撤" value="max_drawdown" />
          <el-option label="回撤持续期" value="drawdown_duration" />
          <el-option label="恢复期" value="recovery_period" />
        </el-select>
        <el-button-group>
          <el-button 
            :type="viewMode === 'line' ? 'primary' : 'default'"
            @click="setViewMode('line')"
            size="small"
          >
            线图
          </el-button>
          <el-button 
            :type="viewMode === 'area' ? 'primary' : 'default'"
            @click="setViewMode('area')"
            size="small"
          >
            面积图
          </el-button>
          <el-button 
            :type="viewMode === 'histogram' ? 'primary' : 'default'"
            @click="setViewMode('histogram')"
            size="small"
          >
            直方图
          </el-button>
        </el-button-group>
        <el-button @click="exportChart" size="small">
          <el-icon><Download /></el-icon>
          导出
        </el-button>
      </div>
    </div>

    <div class="chart-container">
      <div ref="chartRef" class="chart"></div>
    </div>

    <div class="chart-metrics">
      <el-row :gutter="16">
        <el-col :span="6">
          <div class="metric-card">
            <div class="metric-label">最大回撤</div>
            <div class="metric-value negative">{{ formatPercentage(drawdownMetrics.max_drawdown) }}</div>
            <div class="metric-trend">
              <el-icon v-if="drawdownMetrics.max_drawdown > -0.1" class="trend-icon positive"><ArrowUp /></el-icon>
              <el-icon v-else class="trend-icon negative"><ArrowDown /></el-icon>
              <span :class="drawdownMetrics.max_drawdown > -0.1 ? 'positive' : 'negative'">
                {{ drawdownMetrics.max_drawdown > -0.1 ? '风险较低' : '风险较高' }}
              </span>
            </div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="metric-card">
            <div class="metric-label">平均回撤</div>
            <div class="metric-value negative">{{ formatPercentage(drawdownMetrics.avg_drawdown) }}</div>
            <div class="metric-detail">
              回撤次数: {{ drawdownMetrics.drawdown_count }}
            </div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="metric-card">
            <div class="metric-label">最长回撤期</div>
            <div class="metric-value">{{ drawdownMetrics.max_duration }} 天</div>
            <div class="metric-detail">
              平均持续: {{ drawdownMetrics.avg_duration }} 天
            </div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="metric-card">
            <div class="metric-label">回撤恢复率</div>
            <div class="metric-value positive">{{ formatPercentage(drawdownMetrics.recovery_rate) }}</div>
            <div class="metric-detail">
              平均恢复期: {{ drawdownMetrics.avg_recovery }} 天
            </div>
          </div>
        </el-col>
      </el-row>
    </div>

    <div class="drawdown-periods" v-if="drawdownPeriods.length > 0">
      <h4>主要回撤期分析</h4>
      <el-table :data="drawdownPeriods" size="small">
        <el-table-column prop="start_date" label="开始日期" width="120">
          <template #default="scope">
            {{ formatDate(scope.row.start_date) }}
          </template>
        </el-table-column>
        <el-table-column prop="end_date" label="结束日期" width="120">
          <template #default="scope">
            {{ formatDate(scope.row.end_date) }}
          </template>
        </el-table-column>
        <el-table-column prop="max_drawdown" label="最大回撤" width="100">
          <template #default="scope">
            <span class="negative">{{ formatPercentage(scope.row.max_drawdown) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="duration" label="持续天数" width="100" />
        <el-table-column prop="recovery_period" label="恢复期(天)" width="100">
          <template #default="scope">
            <span v-if="scope.row.recovery_period">{{ scope.row.recovery_period }}</span>
            <span v-else class="text-muted">未完全恢复</span>
          </template>
        </el-table-column>
        <el-table-column prop="cause" label="可能原因" min-width="200">
          <template #default="scope">
            <el-tag 
              v-for="cause in scope.row.causes" 
              :key="cause"
              size="small"
              style="margin-right: 4px;"
            >
              {{ cause }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="80">
          <template #default="scope">
            <el-button 
              type="text" 
              size="small"
              @click="highlightPeriod(scope.row)"
            >
              高亮
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <div class="risk-analysis">
      <h4>风险分析建议</h4>
      <div class="analysis-cards">
        <el-card 
          v-for="analysis in riskAnalysis" 
          :key="analysis.category"
          shadow="hover"
          class="analysis-card"
        >
          <div class="analysis-header">
            <el-icon :class="`analysis-icon ${analysis.type}`">
              <InfoFilled v-if="analysis.type === 'info'" />
              <WarningFilled v-else-if="analysis.type === 'warning'" />
              <CircleCloseFilled v-else-if="analysis.type === 'danger'" />
              <SuccessFilled v-else />
            </el-icon>
            <h5>{{ analysis.title }}</h5>
          </div>
          <p>{{ analysis.description }}</p>
          <div class="analysis-suggestions">
            <div class="suggestion-title">建议措施:</div>
            <ul>
              <li v-for="suggestion in analysis.suggestions" :key="suggestion">
                {{ suggestion }}
              </li>
            </ul>
          </div>
        </el-card>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted, watch, nextTick } from 'vue'
import * as echarts from 'echarts'
import {
  Download,
  ArrowUp,
  ArrowDown,
  InfoFilled,
  WarningFilled,
  CircleCloseFilled,
  SuccessFilled
} from '@element-plus/icons-vue'

interface DrawdownData {
  date: string
  cumulative_return: number
  drawdown: number
  underwater_curve: number
}

interface DrawdownPeriod {
  start_date: string
  end_date: string
  max_drawdown: number
  duration: number
  recovery_period: number | null
  causes: string[]
}

interface DrawdownMetrics {
  max_drawdown: number
  avg_drawdown: number
  drawdown_count: number
  max_duration: number
  avg_duration: number
  recovery_rate: number
  avg_recovery: number
}

interface RiskAnalysisItem {
  category: string
  title: string
  description: string
  type: 'info' | 'success' | 'warning' | 'danger'
  suggestions: string[]
}

const props = defineProps<{
  data?: DrawdownData[]
  experimentId?: string
  compareExperiments?: string[]
}>()

// 响应式数据
const chartRef = ref()
const selectedMetric = ref('max_drawdown')
const viewMode = ref('line')
let chart: echarts.ECharts | null = null

const drawdownData = ref<DrawdownData[]>([])
const drawdownMetrics = reactive<DrawdownMetrics>({
  max_drawdown: 0,
  avg_drawdown: 0,
  drawdown_count: 0,
  max_duration: 0,
  avg_duration: 0,
  recovery_rate: 0,
  avg_recovery: 0
})

const drawdownPeriods = ref<DrawdownPeriod[]>([])
const riskAnalysis = ref<RiskAnalysisItem[]>([])

// 方法
const initChart = () => {
  if (!chartRef.value) return
  
  chart = echarts.init(chartRef.value)
  updateChart()
  
  // 添加图表事件监听
  chart.on('click', (params) => {
    if (params.componentType === 'series') {
      handleChartClick(params)
    }
  })
  
  // 添加数据缩放事件
  chart.on('datazoom', (params) => {
    handleDataZoom(params)
  })
}

const updateChart = () => {
  if (!chart || drawdownData.value.length === 0) return
  
  const option = getChartOption()
  chart.setOption(option, true)
}

const getChartOption = () => {
  const dates = drawdownData.value.map(d => d.date)
  const returns = drawdownData.value.map(d => d.cumulative_return)
  const drawdowns = drawdownData.value.map(d => d.drawdown)
  const underwater = drawdownData.value.map(d => d.underwater_curve)
  
  const baseOption = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      },
      formatter: (params: any[]) => {
        const date = params[0].axisValue
        let result = `<div style="margin-bottom: 8px;"><strong>${date}</strong></div>`
        
        params.forEach(param => {
          const value = param.seriesName === '累计收益率' 
            ? formatPercentage(param.value) 
            : formatPercentage(param.value)
          
          result += `
            <div style="display: flex; align-items: center; margin-bottom: 4px;">
              <span style="display: inline-block; width: 10px; height: 10px; border-radius: 50%; background: ${param.color}; margin-right: 8px;"></span>
              <span style="flex: 1;">${param.seriesName}:</span>
              <strong style="margin-left: 8px;">${value}</strong>
            </div>
          `
        })
        
        return result
      }
    },
    legend: {
      data: getSeriesNames(),
      bottom: 0
    },
    grid: [
      {
        left: '3%',
        right: '4%',
        top: '10%',
        height: '35%'
      },
      {
        left: '3%',
        right: '4%',
        top: '55%',
        height: '35%'
      }
    ],
    xAxis: [
      {
        type: 'category',
        data: dates,
        gridIndex: 0,
        axisLabel: { show: false }
      },
      {
        type: 'category',
        data: dates,
        gridIndex: 1
      }
    ],
    yAxis: [
      {
        type: 'value',
        gridIndex: 0,
        axisLabel: {
          formatter: (value: number) => formatPercentage(value)
        }
      },
      {
        type: 'value',
        gridIndex: 1,
        axisLabel: {
          formatter: (value: number) => formatPercentage(value)
        },
        max: 0
      }
    ],
    dataZoom: [
      {
        type: 'inside',
        xAxisIndex: [0, 1]
      },
      {
        type: 'slider',
        xAxisIndex: [0, 1],
        bottom: '5%'
      }
    ],
    series: getSeries(dates, returns, drawdowns, underwater)
  }
  
  return baseOption
}

const getSeries = (dates: string[], returns: number[], drawdowns: number[], underwater: number[]) => {
  const series = []
  
  // 累计收益率曲线
  series.push({
    name: '累计收益率',
    type: 'line',
    data: returns,
    xAxisIndex: 0,
    yAxisIndex: 0,
    itemStyle: {
      color: '#409eff'
    },
    lineStyle: {
      width: 2
    },
    areaStyle: viewMode.value === 'area' ? {
      color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
        { offset: 0, color: 'rgba(64, 158, 255, 0.3)' },
        { offset: 1, color: 'rgba(64, 158, 255, 0.1)' }
      ])
    } : undefined
  })
  
  // 回撤曲线
  if (viewMode.value === 'histogram') {
    series.push({
      name: '回撤',
      type: 'bar',
      data: drawdowns,
      xAxisIndex: 1,
      yAxisIndex: 1,
      itemStyle: {
        color: (params: any) => {
          const value = Math.abs(params.value)
          if (value > 0.2) return '#f56c6c'
          if (value > 0.1) return '#e6a23c'
          if (value > 0.05) return '#409eff'
          return '#67c23a'
        }
      }
    })
  } else {
    series.push({
      name: '回撤',
      type: 'line',
      data: drawdowns,
      xAxisIndex: 1,
      yAxisIndex: 1,
      itemStyle: {
        color: '#f56c6c'
      },
      lineStyle: {
        width: 2
      },
      areaStyle: viewMode.value === 'area' ? {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(245, 108, 108, 0.3)' },
          { offset: 1, color: 'rgba(245, 108, 108, 0.1)' }
        ])
      } : undefined
    })
  }
  
  // 水下曲线（累计未恢复回撤）
  if (selectedMetric.value === 'drawdown_duration') {
    series.push({
      name: '水下曲线',
      type: 'line',
      data: underwater,
      xAxisIndex: 1,
      yAxisIndex: 1,
      itemStyle: {
        color: '#e6a23c'
      },
      lineStyle: {
        width: 1,
        type: 'dashed'
      }
    })
  }
  
  return series
}

const getSeriesNames = () => {
  const names = ['累计收益率', '回撤']
  if (selectedMetric.value === 'drawdown_duration') {
    names.push('水下曲线')
  }
  return names
}

const setViewMode = (mode: string) => {
  viewMode.value = mode
  updateChart()
}

const handleChartClick = (params: any) => {
  const date = params.name
  const dataIndex = params.dataIndex
  
  // 显示该点的详细信息
  console.log('点击日期:', date, '数据:', drawdownData.value[dataIndex])
}

const handleDataZoom = (params: any) => {
  // 数据缩放时的处理
  console.log('数据缩放:', params)
}

const highlightPeriod = (period: DrawdownPeriod) => {
  if (!chart) return
  
  // 在图表中高亮显示指定的回撤期
  const startIndex = drawdownData.value.findIndex(d => d.date >= period.start_date)
  const endIndex = drawdownData.value.findIndex(d => d.date >= period.end_date)
  
  chart.dispatchAction({
    type: 'highlight',
    seriesIndex: 1, // 回撤系列
    dataIndex: Array.from({ length: endIndex - startIndex + 1 }, (_, i) => startIndex + i)
  })
  
  // 缩放到该区域
  chart.dispatchAction({
    type: 'dataZoom',
    startValue: period.start_date,
    endValue: period.end_date
  })
}

const exportChart = () => {
  if (!chart) return
  
  const url = chart.getDataURL({
    type: 'png',
    pixelRatio: 2,
    backgroundColor: '#fff'
  })
  
  const link = document.createElement('a')
  link.download = `drawdown-analysis-${Date.now()}.png`
  link.href = url
  link.click()
}

const loadData = async () => {
  try {
    let response
    
    if (props.data) {
      // 使用传入的数据
      drawdownData.value = props.data
    } else if (props.experimentId) {
      // 从API加载数据
      response = await fetch(`/api/v1/experiments/${props.experimentId}/drawdown-analysis`)
      const data = await response.json()
      
      if (data.success) {
        drawdownData.value = data.data.timeseries
        Object.assign(drawdownMetrics, data.data.metrics)
        drawdownPeriods.value = data.data.periods
        generateRiskAnalysis()
      }
    } else {
      // 生成模拟数据
      generateMockData()
    }
    
    calculateMetrics()
    updateChart()
  } catch (error) {
    console.error('加载回撤分析数据失败:', error)
    generateMockData()
  }
}

const generateMockData = () => {
  const data: DrawdownData[] = []
  let cumulativeReturn = 0
  let peak = 0
  
  for (let i = 0; i < 250; i++) {
    const date = new Date()
    date.setDate(date.getDate() - (250 - i))
    
    // 模拟每日收益率
    const dailyReturn = (Math.random() - 0.45) * 0.02
    cumulativeReturn += dailyReturn
    
    // 计算峰值和回撤
    peak = Math.max(peak, cumulativeReturn)
    const drawdown = cumulativeReturn - peak
    
    data.push({
      date: date.toISOString().split('T')[0],
      cumulative_return: cumulativeReturn,
      drawdown: drawdown,
      underwater_curve: drawdown
    })
  }
  
  drawdownData.value = data
}

const calculateMetrics = () => {
  if (drawdownData.value.length === 0) return
  
  const drawdowns = drawdownData.value.map(d => d.drawdown).filter(d => d < 0)
  
  drawdownMetrics.max_drawdown = Math.min(...drawdowns)
  drawdownMetrics.avg_drawdown = drawdowns.length > 0 ? drawdowns.reduce((a, b) => a + b, 0) / drawdowns.length : 0
  drawdownMetrics.drawdown_count = drawdowns.length
  
  // 计算回撤期
  const periods = findDrawdownPeriods()
  drawdownPeriods.value = periods
  
  if (periods.length > 0) {
    drawdownMetrics.max_duration = Math.max(...periods.map(p => p.duration))
    drawdownMetrics.avg_duration = periods.reduce((a, b) => a + b.duration, 0) / periods.length
    
    const recoveredPeriods = periods.filter(p => p.recovery_period !== null)
    drawdownMetrics.recovery_rate = recoveredPeriods.length / periods.length
    drawdownMetrics.avg_recovery = recoveredPeriods.length > 0 
      ? recoveredPeriods.reduce((a, b) => a + (b.recovery_period || 0), 0) / recoveredPeriods.length 
      : 0
  }
}

const findDrawdownPeriods = (): DrawdownPeriod[] => {
  const periods: DrawdownPeriod[] = []
  let inDrawdown = false
  let currentPeriod: Partial<DrawdownPeriod> | null = null
  let peak = 0
  
  for (let i = 0; i < drawdownData.value.length; i++) {
    const point = drawdownData.value[i]
    
    if (point.cumulative_return > peak) {
      peak = point.cumulative_return
      
      // 结束当前回撤期
      if (inDrawdown && currentPeriod) {
        currentPeriod.end_date = point.date
        currentPeriod.recovery_period = i - drawdownData.value.findIndex(d => d.date === currentPeriod!.start_date!)
        
        periods.push(currentPeriod as DrawdownPeriod)
        currentPeriod = null
        inDrawdown = false
      }
    } else if (point.drawdown < -0.01 && !inDrawdown) {
      // 开始新的回撤期
      inDrawdown = true
      currentPeriod = {
        start_date: point.date,
        max_drawdown: point.drawdown,
        duration: 1,
        causes: generateDrawdownCauses(point.drawdown)
      }
    } else if (inDrawdown && currentPeriod) {
      // 更新当前回撤期
      currentPeriod.max_drawdown = Math.min(currentPeriod.max_drawdown!, point.drawdown)
      currentPeriod.duration = i - drawdownData.value.findIndex(d => d.date === currentPeriod!.start_date!) + 1
    }
  }
  
  // 处理未结束的回撤期
  if (inDrawdown && currentPeriod) {
    currentPeriod.end_date = drawdownData.value[drawdownData.value.length - 1].date
    currentPeriod.recovery_period = null
    periods.push(currentPeriod as DrawdownPeriod)
  }
  
  return periods.filter(p => Math.abs(p.max_drawdown) > 0.02) // 过滤小回撤
}

const generateDrawdownCauses = (drawdown: number): string[] => {
  const causes = []
  
  if (drawdown < -0.2) {
    causes.push('市场大幅下跌', '系统性风险')
  } else if (drawdown < -0.1) {
    causes.push('市场调整', '行业轮动')
  } else {
    causes.push('正常波动', '短期调整')
  }
  
  return causes
}

const generateRiskAnalysis = () => {
  const analysis: RiskAnalysisItem[] = []
  
  // 基于回撤指标生成分析
  if (drawdownMetrics.max_drawdown < -0.2) {
    analysis.push({
      category: 'high_risk',
      title: '高风险警告',
      description: '最大回撤超过20%，属于高风险水平，需要重点关注风险管理。',
      type: 'danger',
      suggestions: [
        '考虑降低仓位或增加对冲',
        '优化止损策略',
        '分散投资组合',
        '增加风险监控频率'
      ]
    })
  } else if (drawdownMetrics.max_drawdown < -0.1) {
    analysis.push({
      category: 'medium_risk',
      title: '中等风险',
      description: '最大回撤在10-20%之间，风险水平适中，但仍需注意控制。',
      type: 'warning',
      suggestions: [
        '保持适当的风险敞口',
        '定期评估策略表现',
        '考虑动态调整仓位'
      ]
    })
  } else {
    analysis.push({
      category: 'low_risk',
      title: '低风险',
      description: '最大回撤较小，风险控制良好。',
      type: 'success',
      suggestions: [
        '保持当前风险控制水平',
        '可适当优化收益率'
      ]
    })
  }
  
  // 回撤持续期分析
  if (drawdownMetrics.avg_duration > 30) {
    analysis.push({
      category: 'duration_risk',
      title: '回撤持续期较长',
      description: '平均回撤持续时间较长，可能影响资金效率。',
      type: 'warning',
      suggestions: [
        '优化策略的时机选择',
        '增加趋势判断指标',
        '考虑止损机制的及时性'
      ]
    })
  }
  
  // 恢复能力分析
  if (drawdownMetrics.recovery_rate < 0.8) {
    analysis.push({
      category: 'recovery_risk',
      title: '回撤恢复能力不足',
      description: '部分回撤未能完全恢复，策略的韧性有待提高。',
      type: 'warning',
      suggestions: [
        '检查策略的长期有效性',
        '优化参数设置',
        '增加策略的适应性'
      ]
    })
  }
  
  riskAnalysis.value = analysis
}

// 工具函数
const formatPercentage = (value: number): string => {
  return (value * 100).toFixed(2) + '%'
}

const formatDate = (dateString: string): string => {
  return new Date(dateString).toLocaleDateString()
}

// 监听器
watch(() => props.data, () => {
  loadData()
}, { immediate: false })

watch(() => props.experimentId, () => {
  loadData()
}, { immediate: false })

// 生命周期
onMounted(async () => {
  await nextTick()
  await loadData()
  initChart()
  
  // 窗口大小变化时调整图表
  window.addEventListener('resize', () => {
    chart?.resize()
  })
})

onUnmounted(() => {
  chart?.dispose()
  window.removeEventListener('resize', () => {
    chart?.resize()
  })
})
</script>

<style scoped>
.drawdown-analysis-chart {
  padding: 20px;
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
}

.chart-controls {
  display: flex;
  align-items: center;
  gap: 16px;
}

.chart-container {
  margin-bottom: 20px;
}

.chart {
  height: 500px;
  width: 100%;
}

.chart-metrics {
  margin-bottom: 30px;
}

.metric-card {
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
  text-align: center;
}

.metric-label {
  font-size: 14px;
  color: #666;
  margin-bottom: 8px;
}

.metric-value {
  font-size: 24px;
  font-weight: 600;
  margin-bottom: 4px;
}

.metric-value.positive {
  color: #67c23a;
}

.metric-value.negative {
  color: #f56c6c;
}

.metric-trend {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  font-size: 12px;
}

.trend-icon {
  font-size: 14px;
}

.trend-icon.positive {
  color: #67c23a;
}

.trend-icon.negative {
  color: #f56c6c;
}

.metric-detail {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
}

.drawdown-periods {
  margin-bottom: 30px;
}

.drawdown-periods h4 {
  margin-bottom: 16px;
  font-size: 16px;
  font-weight: 600;
}

.negative {
  color: #f56c6c;
}

.positive {
  color: #67c23a;
}

.text-muted {
  color: #999;
}

.risk-analysis h4 {
  margin-bottom: 16px;
  font-size: 16px;
  font-weight: 600;
}

.analysis-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 16px;
}

.analysis-card {
  height: 100%;
}

.analysis-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.analysis-icon {
  font-size: 18px;
}

.analysis-icon.info {
  color: #409eff;
}

.analysis-icon.success {
  color: #67c23a;
}

.analysis-icon.warning {
  color: #e6a23c;
}

.analysis-icon.danger {
  color: #f56c6c;
}

.analysis-header h5 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
}

.analysis-card p {
  margin: 0 0 12px 0;
  color: #666;
  line-height: 1.5;
}

.analysis-suggestions {
  font-size: 13px;
}

.suggestion-title {
  font-weight: 600;
  margin-bottom: 8px;
}

.analysis-suggestions ul {
  margin: 0;
  padding-left: 16px;
}

.analysis-suggestions li {
  margin-bottom: 4px;
  line-height: 1.4;
}
</style>