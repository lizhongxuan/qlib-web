<template>
  <div class="drawdown-chart" :style="{ height: height + 'px' }">
    <div ref="chartContainer" class="chart-container"></div>
    <div v-if="loading" class="chart-loading">
      <el-icon class="is-loading">
        <Loading />
      </el-icon>
      <span>加载回撤分析...</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import * as echarts from 'echarts'
import { Loading } from '@element-plus/icons-vue'

interface DrawdownData {
  date: string
  cumulative_return: number
  drawdown: number
  underwater_curve: number
  max_drawdown_start?: string
  max_drawdown_end?: string
}

const props = defineProps<{
  data: DrawdownData[]
  height?: number
  loading?: boolean
  theme?: 'light' | 'dark'
}>()

const chartContainer = ref<HTMLElement>()
let chartInstance: echarts.ECharts | null = null

const initChart = () => {
  if (!chartContainer.value || !props.data.length) return
  
  chartInstance = echarts.init(chartContainer.value, props.theme || 'light')
  
  // 计算最大回撤区间
  const maxDrawdown = Math.min(...props.data.map(d => d.drawdown))
  const maxDrawdownIndex = props.data.findIndex(d => d.drawdown === maxDrawdown)
  
  const option = {
    title: {
      text: '回撤分析',
      left: 'center',
      textStyle: {
        fontSize: 16,
        fontWeight: 'bold'
      }
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      },
      formatter: function (params: any[]) {
        let result = `<div style="margin-bottom: 8px; font-weight: bold;">${params[0].axisValue}</div>`
        params.forEach(param => {
          const value = param.value
          const formatted = param.seriesName === '累计收益率' 
            ? `${(value * 100).toFixed(2)}%`
            : `${(value * 100).toFixed(2)}%`
          result += `
            <div style="display: flex; align-items: center; margin-bottom: 4px;">
              <span style="display:inline-block;margin-right:5px;border-radius:10px;width:10px;height:10px;background-color:${param.color};"></span>
              <span style="margin-right: 8px;">${param.seriesName}:</span>
              <strong style="color: ${param.seriesName === '回撤' ? '#f56c6c' : '#67c23a'}">${formatted}</strong>
            </div>
          `
        })
        return result
      }
    },
    legend: {
      data: ['累计收益率', '回撤', '水下曲线'],
      top: 'bottom'
    },
    grid: [
      {
        left: '3%',
        right: '4%',
        top: '15%',
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
        data: props.data.map(d => d.date),
        gridIndex: 0,
        axisLabel: { show: false }
      },
      {
        type: 'category',
        data: props.data.map(d => d.date),
        gridIndex: 1
      }
    ],
    yAxis: [
      {
        type: 'value',
        gridIndex: 0,
        name: '累计收益率',
        nameLocation: 'middle',
        nameGap: 50,
        axisLabel: {
          formatter: function (value: number) {
            return (value * 100).toFixed(1) + '%'
          }
        }
      },
      {
        type: 'value',
        gridIndex: 1,
        name: '回撤',
        nameLocation: 'middle',
        nameGap: 50,
        max: 0,
        axisLabel: {
          formatter: function (value: number) {
            return (value * 100).toFixed(1) + '%'
          }
        }
      }
    ],
    dataZoom: [
      {
        type: 'inside',
        xAxisIndex: [0, 1],
        start: 0,
        end: 100
      },
      {
        show: true,
        type: 'slider',
        xAxisIndex: [0, 1],
        top: '95%',
        start: 0,
        end: 100
      }
    ],
    series: [
      {
        name: '累计收益率',
        type: 'line',
        xAxisIndex: 0,
        yAxisIndex: 0,
        data: props.data.map(d => d.cumulative_return),
        smooth: true,
        symbol: 'none',
        lineStyle: {
          color: '#67c23a',
          width: 2
        },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(103, 194, 58, 0.3)' },
            { offset: 1, color: 'rgba(103, 194, 58, 0)' }
          ])
        },
        markPoint: {
          data: [
            { type: 'max', name: '最高点' },
            {
              coord: [maxDrawdownIndex, props.data[maxDrawdownIndex]?.cumulative_return],
              name: '最大回撤起点',
              itemStyle: { color: '#f56c6c' }
            }
          ]
        }
      },
      {
        name: '回撤',
        type: 'line',
        xAxisIndex: 1,
        yAxisIndex: 1,
        data: props.data.map(d => d.drawdown),
        smooth: true,
        symbol: 'none',
        lineStyle: {
          color: '#f56c6c',
          width: 2
        },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(245, 108, 108, 0.3)' },
            { offset: 1, color: 'rgba(245, 108, 108, 0)' }
          ])
        },
        markLine: {
          data: [
            {
              yAxis: maxDrawdown,
              name: `最大回撤: ${(maxDrawdown * 100).toFixed(2)}%`,
              lineStyle: { color: '#f56c6c', type: 'dashed' },
              label: {
                formatter: function() {
                  return `最大回撤: ${(maxDrawdown * 100).toFixed(2)}%`
                }
              }
            }
          ]
        }
      },
      {
        name: '水下曲线',
        type: 'line',
        xAxisIndex: 1,
        yAxisIndex: 1,
        data: props.data.map(d => d.underwater_curve),
        smooth: true,
        symbol: 'none',
        lineStyle: {
          color: '#409EFF',
          width: 1,
          type: 'dashed'
        }
      }
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
.drawdown-chart {
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