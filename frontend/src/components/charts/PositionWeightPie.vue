<template>
  <div class="position-weight-pie" :style="{ height: height + 'px' }">
    <div ref="chartContainer" class="chart-container"></div>
    <div v-if="loading" class="chart-loading">
      <el-icon class="is-loading">
        <Loading />
      </el-icon>
      <span>加载持仓分析...</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import * as echarts from 'echarts'
import { Loading } from '@element-plus/icons-vue'

interface PositionData {
  symbol: string
  weight: number
  sector?: string
  market_value?: number
  return?: number
}

const props = defineProps<{
  data: PositionData[]
  height?: number
  loading?: boolean
  theme?: 'light' | 'dark'
  showSector?: boolean
  topN?: number
}>()

const chartContainer = ref<HTMLElement>()
let chartInstance: echarts.ECharts | null = null

const initChart = () => {
  if (!chartContainer.value || !props.data.length) return
  
  chartInstance = echarts.init(chartContainer.value, props.theme || 'light')
  
  // 处理数据：取前N个持仓，其余归为"其他"
  const topN = props.topN || 10
  const sortedData = [...props.data].sort((a, b) => b.weight - a.weight)
  const topData = sortedData.slice(0, topN)
  const othersWeight = sortedData.slice(topN).reduce((sum, item) => sum + item.weight, 0)
  
  let chartData = topData.map(item => ({
    name: item.symbol,
    value: item.weight,
    sector: item.sector,
    return: item.return || 0,
    market_value: item.market_value || 0
  }))
  
  if (othersWeight > 0) {
    chartData.push({
      name: '其他',
      value: othersWeight,
      sector: '其他',
      return: 0,
      market_value: 0
    })
  }
  
  // 行业分布数据（如果需要显示）
  const sectorData = props.showSector ? 
    Object.entries(
      props.data.reduce((acc: Record<string, number>, item) => {
        const sector = item.sector || '未分类'
        acc[sector] = (acc[sector] || 0) + item.weight
        return acc
      }, {})
    ).map(([name, value]) => ({ name, value })) : []
  
  const option = {
    title: [
      {
        text: '持仓权重分布',
        left: 'center',
        top: '5%',
        textStyle: {
          fontSize: 16,
          fontWeight: 'bold'
        }
      },
      ...(props.showSector ? [{
        text: '行业分布',
        left: 'center',
        top: '55%',
        textStyle: {
          fontSize: 14,
          fontWeight: 'bold'
        }
      }] : [])
    ],
    tooltip: [
      {
        trigger: 'item',
        formatter: function (params: any) {
          const data = params.data
          const weight = (data.value * 100).toFixed(2)
          const returnStr = data.return !== undefined ? 
            `<br/>收益率: <span style="color: ${data.return >= 0 ? '#67c23a' : '#f56c6c'}">${(data.return * 100).toFixed(2)}%</span>` : ''
          const marketValue = data.market_value ? 
            `<br/>市值: ${(data.market_value / 10000).toFixed(2)}万` : ''
          const sector = data.sector && data.sector !== '其他' ? 
            `<br/>行业: ${data.sector}` : ''
          
          return `<strong>${data.name}</strong><br/>权重: ${weight}%${returnStr}${marketValue}${sector}`
        }
      },
      ...(props.showSector ? [{
        trigger: 'item',
        formatter: function (params: any) {
          return `<strong>${params.name}</strong><br/>权重: ${(params.value * 100).toFixed(2)}%`
        }
      }] : [])
    ],
    legend: [
      {
        type: 'scroll',
        orient: 'vertical',
        right: '5%',
        top: '15%',
        bottom: props.showSector ? '55%' : '15%',
        data: chartData.map(d => d.name),
        formatter: function (name: string) {
          const item = chartData.find(d => d.name === name)
          return `${name}: ${(item!.value * 100).toFixed(1)}%`
        }
      },
      ...(props.showSector ? [{
        type: 'scroll',
        orient: 'vertical',
        right: '5%',
        top: '65%',
        bottom: '5%',
        data: sectorData.map(d => d.name)
      }] : [])
    ],
    series: [
      {
        name: '持仓权重',
        type: 'pie',
        radius: ['40%', '70%'],
        center: ['30%', props.showSector ? '30%' : '50%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 8,
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
            fontSize: '14',
            fontWeight: 'bold',
            formatter: function (params: any) {
              return `${params.name}\n${(params.value * 100).toFixed(2)}%`
            }
          },
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        },
        labelLine: {
          show: false
        },
        data: chartData,
        animationType: 'scale',
        animationEasing: 'elasticOut',
        animationDelay: function (idx: number) {
          return Math.random() * 200
        }
      },
      ...(props.showSector ? [{
        name: '行业分布',
        type: 'pie',
        radius: ['30%', '60%'],
        center: ['30%', '75%'],
        itemStyle: {
          borderRadius: 6,
          borderColor: '#fff',
          borderWidth: 1
        },
        label: {
          show: false
        },
        emphasis: {
          label: {
            show: true,
            fontSize: '12',
            formatter: function (params: any) {
              return `${params.name}\n${(params.value * 100).toFixed(1)}%`
            }
          }
        },
        data: sectorData
      }] : [])
    ]
  }
  
  chartInstance.setOption(option)
}

const resizeChart = () => {
  if (chartInstance) {
    chartInstance.resize()
  }
}

watch(() => props.data, () => {
  if (chartInstance) {
    initChart()
  }
}, { deep: true })

watch(() => props.theme, () => {
  if (chartInstance) {
    chartInstance.dispose()
    initChart()
  }
})

onMounted(() => {
  initChart()
  window.addEventListener('resize', resizeChart)
})

onBeforeUnmount(() => {
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
  window.removeEventListener('resize', resizeChart)
})

defineExpose({
  getInstance: () => chartInstance,
  resize: resizeChart
})
</script>

<style scoped>
.position-weight-pie {
  position: relative;
  width: 100%;
}

.chart-container {
  width: 100%;
  height: 100%;
}

.chart-loading {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--el-text-color-secondary);
  font-size: 14px;
}
</style>