<template>
  <div class="attribution-chart">
    <div class="chart-header">
      <h3>收益归因分析</h3>
      <div class="chart-controls">
        <el-select v-model="viewType" size="small" @change="updateChart">
          <el-option label="综合视图" value="overview" />
          <el-option label="行业贡献" value="sector" />
          <el-option label="因子暴露" value="factor" />
          <el-option label="时间序列" value="timeseries" />
        </el-select>
      </div>
    </div>
    
    <div class="chart-content">
      <!-- 综合指标卡片 -->
      <div v-if="viewType === 'overview'" class="metrics-cards">
        <div class="metric-card">
          <div class="metric-value">{{ formatPercent(data?.total_return) }}</div>
          <div class="metric-label">总收益率</div>
        </div>
        <div class="metric-card">
          <div class="metric-value">{{ formatPercent(data?.alpha) }}</div>
          <div class="metric-label">超额收益(α)</div>
        </div>
        <div class="metric-card">
          <div class="metric-value">{{ formatNumber(data?.beta) }}</div>
          <div class="metric-label">市场敏感度(β)</div>
        </div>
        <div class="metric-card">
          <div class="metric-value">{{ formatPercent(data?.tracking_error) }}</div>
          <div class="metric-label">跟踪误差</div>
        </div>
      </div>
      
      <!-- 图表容器 -->
      <div ref="chartContainer" class="chart-container"></div>
      
      <!-- 归因分解表格 -->
      <div v-if="viewType === 'overview'" class="attribution-table">
        <h4>归因分解</h4>
        <el-table :data="attributionBreakdown" size="small">
          <el-table-column prop="component" label="组成部分" width="120" />
          <el-table-column prop="contribution" label="贡献度" width="100">
            <template #default="{ row }">
              <span :class="{'positive': row.contribution > 0, 'negative': row.contribution < 0}">
                {{ formatPercent(row.contribution) }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="description" label="说明" />
        </el-table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, computed, nextTick } from 'vue'
import * as echarts from 'echarts'

interface AttributionData {
  total_return: number
  benchmark_return: number
  active_return: number
  alpha: number
  beta: number
  tracking_error?: number
  information_ratio?: number
  sector_contribution: Record<string, number>
  factor_exposure: Record<string, number>
  attribution_summary: Record<string, number>
}

interface Props {
  data: AttributionData | null
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  loading: false
})

const chartContainer = ref<HTMLElement>()
const viewType = ref('overview')
let chart: echarts.ECharts | null = null

// 计算归因分解数据
const attributionBreakdown = computed(() => {
  if (!props.data?.attribution_summary) return []
  
  return [
    {
      component: '个股选择',
      contribution: props.data.attribution_summary.selection_effect || 0,
      description: '选择个股带来的超额收益'
    },
    {
      component: '资产配置',
      contribution: props.data.attribution_summary.allocation_effect || 0,
      description: '行业/资产配置带来的超额收益'
    },
    {
      component: '交互效应',
      contribution: props.data.attribution_summary.interaction_effect || 0,
      description: '配置与选择的交互作用'
    }
  ]
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
    case 'sector':
      option = createSectorChart()
      break
    case 'factor':
      option = createFactorChart()
      break
    case 'timeseries':
      option = createTimeSeriesChart()
      break
  }
  
  chart.setOption(option, true)
}

// 综合视图图表
const createOverviewChart = () => {
  const attribution = props.data!.attribution_summary
  
  return {
    title: {
      text: '收益归因分解',
      left: 'center',
      textStyle: { fontSize: 14 }
    },
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c}% ({d}%)'
    },
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],
      center: ['50%', '60%'],
      data: [
        {
          name: '个股选择效应',
          value: Math.abs((attribution.selection_effect || 0) * 100),
          itemStyle: { color: attribution.selection_effect > 0 ? '#67C23A' : '#F56C6C' }
        },
        {
          name: '资产配置效应',
          value: Math.abs((attribution.allocation_effect || 0) * 100),
          itemStyle: { color: attribution.allocation_effect > 0 ? '#409EFF' : '#E6A23C' }
        },
        {
          name: '交互效应',
          value: Math.abs((attribution.interaction_effect || 0) * 100),
          itemStyle: { color: attribution.interaction_effect > 0 ? '#909399' : '#F78989' }
        }
      ],
      emphasis: {
        itemStyle: {
          shadowBlur: 10,
          shadowOffsetX: 0,
          shadowColor: 'rgba(0, 0, 0, 0.5)'
        }
      }
    }]
  }
}

// 行业贡献图表
const createSectorChart = () => {
  const sectorData = props.data!.sector_contribution
  const sectors = Object.keys(sectorData)
  const values = Object.values(sectorData)
  
  return {
    title: {
      text: '行业贡献分析',
      left: 'center',
      textStyle: { fontSize: 14 }
    },
    tooltip: {
      trigger: 'axis',
      formatter: '{b}: {c}%'
    },
    xAxis: {
      type: 'category',
      data: sectors,
      axisLabel: {
        rotate: 45,
        interval: 0
      }
    },
    yAxis: {
      type: 'value',
      name: '贡献度(%)',
      axisLabel: {
        formatter: '{value}%'
      }
    },
    series: [{
      type: 'bar',
      data: values.map((val, index) => ({
        value: (val * 100).toFixed(2),
        itemStyle: {
          color: val > 0 ? '#67C23A' : '#F56C6C'
        }
      })),
      emphasis: {
        itemStyle: {
          shadowBlur: 10,
          shadowOffsetX: 0,
          shadowColor: 'rgba(0, 0, 0, 0.5)'
        }
      }
    }]
  }
}

// 因子暴露图表
const createFactorChart = () => {
  const factorData = props.data!.factor_exposure
  const factors = Object.keys(factorData)
  const values = Object.values(factorData)
  
  return {
    title: {
      text: '风格因子暴露',
      left: 'center',
      textStyle: { fontSize: 14 }
    },
    tooltip: {
      trigger: 'axis',
      formatter: '{b}: {c}'
    },
    radar: {
      indicator: factors.map(factor => ({
        name: factor,
        max: 1,
        min: -1
      })),
      center: ['50%', '60%'],
      radius: '70%'
    },
    series: [{
      type: 'radar',
      data: [{
        value: values,
        name: '因子暴露',
        areaStyle: {
          opacity: 0.3
        },
        itemStyle: {
          color: '#409EFF'
        }
      }]
    }]
  }
}

// 时间序列图表（模拟数据）
const createTimeSeriesChart = () => {
  // 模拟时间序列数据
  const dates = Array.from({length: 30}, (_, i) => {
    const date = new Date()
    date.setDate(date.getDate() - 29 + i)
    return date.toLocaleDateString()
  })
  
  const portfolioReturns = Array.from({length: 30}, () => Math.random() * 0.04 - 0.02)
  const benchmarkReturns = Array.from({length: 30}, () => Math.random() * 0.03 - 0.015)
  
  return {
    title: {
      text: '收益率时间序列',
      left: 'center',
      textStyle: { fontSize: 14 }
    },
    tooltip: {
      trigger: 'axis',
      formatter: function(params: any) {
        return `${params[0].name}<br/>
                组合收益: ${(params[0].value * 100).toFixed(2)}%<br/>
                基准收益: ${(params[1].value * 100).toFixed(2)}%`
      }
    },
    legend: {
      data: ['组合收益', '基准收益'],
      top: 30
    },
    xAxis: {
      type: 'category',
      data: dates,
      axisLabel: {
        rotate: 45
      }
    },
    yAxis: {
      type: 'value',
      name: '收益率(%)',
      axisLabel: {
        formatter: '{value}%'
      }
    },
    series: [
      {
        name: '组合收益',
        type: 'line',
        data: portfolioReturns.map(val => (val * 100).toFixed(2)),
        itemStyle: { color: '#409EFF' },
        smooth: true
      },
      {
        name: '基准收益',
        type: 'line',
        data: benchmarkReturns.map(val => (val * 100).toFixed(2)),
        itemStyle: { color: '#67C23A' },
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
.attribution-chart {
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

.chart-controls {
  display: flex;
  gap: 12px;
}

.chart-content {
  min-height: 400px;
}

.metrics-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 16px;
  margin-bottom: 20px;
}

.metric-card {
  background: #f8f9fa;
  padding: 16px;
  border-radius: 6px;
  text-align: center;
  border: 1px solid #e4e7ed;
}

.metric-value {
  font-size: 24px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 4px;
}

.metric-label {
  font-size: 12px;
  color: #909399;
}

.chart-container {
  width: 100%;
  height: 400px;
}

.attribution-table {
  margin-top: 20px;
}

.attribution-table h4 {
  margin: 0 0 12px 0;
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.positive {
  color: #67C23A;
}

.negative {
  color: #F56C6C;
}

:deep(.el-table) {
  font-size: 12px;
}

:deep(.el-table th) {
  background-color: #f5f7fa;
}
</style>