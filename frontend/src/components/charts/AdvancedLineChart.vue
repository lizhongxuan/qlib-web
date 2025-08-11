<template>
  <div class="advanced-line-chart" :style="{ height: height + 'px' }">
    <div ref="chartContainer" class="chart-container" :style="chartStyle"></div>
    <div v-if="loading" class="chart-loading">
      <el-icon class="is-loading">
        <Loading />
      </el-icon>
      <span>加载中...</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch, computed } from 'vue'
import * as echarts from 'echarts'
import { Loading } from '@element-plus/icons-vue'

interface ChartDataPoint {
  date: string
  value: number
  [key: string]: any
}

interface SeriesConfig {
  name: string
  data: ChartDataPoint[]
  color?: string
  type?: 'line' | 'bar' | 'scatter'
  yAxisIndex?: number
}

const props = defineProps<{
  series: SeriesConfig[]
  height?: number
  loading?: boolean
  showToolbox?: boolean
  showDataZoom?: boolean
  showBrush?: boolean
  theme?: 'light' | 'dark'
  title?: string
  subtitle?: string
}>()

const emit = defineEmits<{
  chartReady: [chart: echarts.ECharts]
  dataZoom: [params: any]
  brush: [params: any]
}>()

const chartContainer = ref<HTMLElement>()
let chartInstance: echarts.ECharts | null = null

const chartStyle = computed(() => ({
  height: '100%',
  width: '100%'
}))

const initChart = () => {
  if (!chartContainer.value) return
  
  chartInstance = echarts.init(chartContainer.value, props.theme || 'light')
  
  const option = {
    title: {
      text: props.title,
      subtext: props.subtitle,
      left: 'center'
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross',
        animation: false
      },
      formatter: function (params: any[]) {
        let result = `<div style="margin-bottom: 8px; font-weight: bold;">${params[0].axisValue}</div>`
        params.forEach(param => {
          const value = typeof param.value === 'number' ? 
            param.value.toFixed(4) : param.value
          result += `
            <div style="display: flex; align-items: center; margin-bottom: 4px;">
              <span style="display:inline-block;margin-right:5px;border-radius:10px;width:10px;height:10px;background-color:${param.color};"></span>
              <span style="margin-right: 8px;">${param.seriesName}:</span>
              <strong>${value}</strong>
            </div>
          `
        })
        return result
      }
    },
    legend: {
      data: props.series.map(s => s.name),
      top: 'bottom'
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: props.showDataZoom ? '15%' : '10%',
      top: props.title ? '15%' : '8%',
      containLabel: true
    },
    toolbox: props.showToolbox ? {
      feature: {
        saveAsImage: {
          title: '保存为图片'
        },
        restore: {
          title: '重置'
        },
        dataZoom: {
          title: {
            zoom: '区域缩放',
            back: '缩放还原'
          }
        },
        brush: props.showBrush ? {
          title: {
            rect: '矩形选择',
            polygon: '圈选',
            lineX: '横向选择',
            lineY: '纵向选择',
            keep: '保持选择',
            clear: '清除选择'
          }
        } : undefined
      }
    } : undefined,
    xAxis: {
      type: 'category',
      data: props.series[0]?.data.map(d => d.date) || [],
      axisPointer: {
        value: '2016-10-7',
        snap: true,
        lineStyle: {
          color: '#004E52',
          opacity: 0.5,
          width: 2
        },
        label: {
          show: true,
          formatter: function (params: any) {
            return params.value
          },
          backgroundColor: '#004E52'
        },
        handle: {
          show: true,
          color: '#004E52'
        }
      },
      splitLine: {
        show: false
      }
    },
    yAxis: [
      {
        type: 'value',
        scale: true,
        axisLabel: {
          formatter: '{value}'
        },
        splitLine: {
          show: true,
          lineStyle: {
            color: '#eee',
            type: 'dashed'
          }
        }
      }
    ],
    dataZoom: props.showDataZoom ? [
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
    ] : undefined,
    brush: props.showBrush ? {
      xAxisIndex: 'all',
      brushLink: 'all',
      outOfBrush: {
        colorAlpha: 0.1
      }
    } : undefined,
    series: props.series.map((seriesConfig, index) => ({
      name: seriesConfig.name,
      type: seriesConfig.type || 'line',
      data: seriesConfig.data.map(d => d.value),
      yAxisIndex: seriesConfig.yAxisIndex || 0,
      smooth: true,
      symbol: 'circle',
      symbolSize: 4,
      lineStyle: {
        color: seriesConfig.color || `hsl(${index * 137.508}%, 70%, 50%)`,
        width: 2
      },
      itemStyle: {
        color: seriesConfig.color || `hsl(${index * 137.508}%, 70%, 50%)`
      },
      areaStyle: seriesConfig.type === 'line' ? {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          {
            offset: 0,
            color: seriesConfig.color || `hsl(${index * 137.508}%, 70%, 50%)`
          },
          {
            offset: 1,
            color: 'transparent'
          }
        ]),
        opacity: 0.1
      } : undefined,
      markPoint: {
        data: [
          { type: 'max', name: '最大值' },
          { type: 'min', name: '最小值' }
        ]
      },
      markLine: {
        data: [{ type: 'average', name: '平均值' }]
      }
    }))
  }
  
  chartInstance.setOption(option)
  
  // 注册事件
  chartInstance.on('datazoom', (params) => {
    emit('dataZoom', params)
  })
  
  chartInstance.on('brush', (params) => {
    emit('brush', params)
  })
  
  emit('chartReady', chartInstance)
}

const resizeChart = () => {
  if (chartInstance) {
    chartInstance.resize()
  }
}

// 监听数据变化
watch(() => props.series, () => {
  if (chartInstance) {
    initChart()
  }
}, { deep: true })

// 监听主题变化
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

// 暴露方法给父组件
defineExpose({
  getInstance: () => chartInstance,
  resize: resizeChart
})
</script>

<style scoped>
.advanced-line-chart {
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