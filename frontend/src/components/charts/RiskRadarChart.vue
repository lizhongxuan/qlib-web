<template>
  <div class="risk-radar-chart" :style="{ height: height + 'px' }">
    <div ref="chartContainer" class="chart-container"></div>
    <div v-if="loading" class="chart-loading">
      <el-icon class="is-loading">
        <Loading />
      </el-icon>
      <span>加载风险分析...</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import * as echarts from 'echarts'
import { Loading } from '@element-plus/icons-vue'

interface RiskMetric {
  name: string
  value: number
  max: number
  unit?: string
  description?: string
}

interface RiskData {
  strategy: string
  metrics: RiskMetric[]
  color?: string
}

const props = defineProps<{
  data: RiskData[]
  height?: number
  loading?: boolean
  theme?: 'light' | 'dark'
}>()

const chartContainer = ref<HTMLElement>()
let chartInstance: echarts.ECharts | null = null

const initChart = () => {
  if (!chartContainer.value || !props.data.length) return
  
  chartInstance = echarts.init(chartContainer.value, props.theme || 'light')
  
  // 获取所有指标名称
  const indicators = props.data[0]?.metrics.map(metric => ({
    name: metric.name,
    max: metric.max
  })) || []
  
  const option = {
    title: {
      text: '风险指标雷达图',
      left: 'center',
      textStyle: {
        fontSize: 16,
        fontWeight: 'bold'
      }
    },
    tooltip: {
      trigger: 'item',
      formatter: function (params: any) {
        const dataIndex = params.dataIndex
        const seriesIndex = params.seriesIndex
        const strategy = props.data[seriesIndex]
        const metric = strategy.metrics[dataIndex]
        
        return `
          <div>
            <strong>${strategy.strategy}</strong><br/>
            <strong>${metric.name}</strong><br/>
            数值: <span style="color: ${params.color}">${metric.value.toFixed(4)}${metric.unit || ''}</span><br/>
            最大值: ${metric.max}${metric.unit || ''}<br/>
            ${metric.description ? `说明: ${metric.description}` : ''}
          </div>
        `
      }
    },
    legend: {
      data: props.data.map(d => d.strategy),
      bottom: '5%'
    },
    radar: {
      center: ['50%', '50%'],
      radius: '60%',
      indicator: indicators,
      name: {
        textStyle: {
          color: props.theme === 'dark' ? '#fff' : '#333',
          fontSize: 12
        }
      },
      splitArea: {
        areaStyle: {
          color: [
            'rgba(114, 172, 209, 0.02)',
            'rgba(114, 172, 209, 0.05)',
            'rgba(114, 172, 209, 0.1)',
            'rgba(114, 172, 209, 0.15)',
            'rgba(114, 172, 209, 0.2)'
          ]
        }
      },
      splitLine: {
        lineStyle: {
          color: props.theme === 'dark' ? 'rgba(255, 255, 255, 0.2)' : 'rgba(0, 0, 0, 0.1)'
        }
      },
      axisLine: {
        lineStyle: {
          color: props.theme === 'dark' ? 'rgba(255, 255, 255, 0.3)' : 'rgba(0, 0, 0, 0.2)'
        }
      }
    },
    series: props.data.map((strategy, index) => ({
      name: strategy.strategy,
      type: 'radar',
      data: [
        {
          value: strategy.metrics.map(metric => metric.value),
          name: strategy.strategy,
          symbol: 'circle',
          symbolSize: 6,
          lineStyle: {
            color: strategy.color || `hsl(${index * 137.508}%, 70%, 50%)`,
            width: 2
          },
          itemStyle: {
            color: strategy.color || `hsl(${index * 137.508}%, 70%, 50%)`
          },
          areaStyle: {
            color: strategy.color || `hsl(${index * 137.508}%, 70%, 50%)`,
            opacity: 0.1
          }
        }
      ],
      emphasis: {
        areaStyle: {
          opacity: 0.3
        }
      }
    }))
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
.risk-radar-chart {
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