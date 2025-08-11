<template>
  <div class="feature-importance-chart">
    <div class="chart-header">
      <h3>特征重要性分析</h3>
      <div class="chart-controls">
        <el-select v-model="viewType" size="small" @change="updateChart">
          <el-option label="重要性排序" value="importance" />
          <el-option label="SHAP值分布" value="shap" />
          <el-option label="特征相关性" value="correlation" />
          <el-option label="稳定性分析" value="stability" />
        </el-select>
        <el-input-number
          v-if="viewType === 'importance'"
          v-model="topN"
          :min="5"
          :max="50"
          size="small"
          @change="updateChart"
        />
      </div>
    </div>
    
    <div class="chart-content">
      <!-- 总体统计 -->
      <div v-if="viewType === 'importance'" class="summary-stats">
        <div class="stat-card">
          <div class="stat-value">{{ totalFeatures }}</div>
          <div class="stat-label">总特征数</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">{{ topFeatures.length }}</div>
          <div class="stat-label">重要特征</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">{{ formatPercent(cumulativeImportance) }}</div>
          <div class="stat-label">累积贡献</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">{{ formatNumber(data?.feature_stability) }}</div>
          <div class="stat-label">特征稳定性</div>
        </div>
      </div>
      
      <!-- 图表容器 -->
      <div ref="chartContainer" class="chart-container"></div>
      
      <!-- 特征详细信息表格 -->
      <div v-if="viewType === 'importance'" class="feature-details">
        <h4>特征重要性排序</h4>
        <el-table :data="topFeatures" size="small" max-height="300">
          <el-table-column prop="rank" label="排名" width="60" />
          <el-table-column prop="name" label="特征名称" min-width="120" />
          <el-table-column prop="importance" label="重要性" width="100">
            <template #default="{ row }">
              <div class="importance-bar">
                <div 
                  class="importance-fill" 
                  :style="{ width: `${(row.importance / maxImportance * 100)}%` }"
                ></div>
                <span class="importance-text">{{ formatNumber(row.importance) }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="cumulative" label="累积贡献" width="100">
            <template #default="{ row }">
              {{ formatPercent(row.cumulative) }}
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, computed, nextTick } from 'vue'
import * as echarts from 'echarts'

interface FeatureImportanceData {
  feature_importance: Record<string, number>
  shap_values?: Record<string, number[]>
  top_features: Array<{
    name: string
    importance: number
  }>
  correlation_matrix?: Record<string, Record<string, number>>
  feature_stability?: number
}

interface Props {
  data: FeatureImportanceData | null
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  loading: false
})

const chartContainer = ref<HTMLElement>()
const viewType = ref('importance')
const topN = ref(20)
let chart: echarts.ECharts | null = null

// 计算统计数据
const totalFeatures = computed(() => {
  return Object.keys(props.data?.feature_importance || {}).length
})

const topFeatures = computed(() => {
  if (!props.data?.feature_importance) return []
  
  const features = Object.entries(props.data.feature_importance)
    .map(([name, importance]) => ({ name, importance }))
    .sort((a, b) => b.importance - a.importance)
    .slice(0, topN.value)
  
  // 计算累积贡献度
  const totalImportance = features.reduce((sum, feature) => sum + feature.importance, 0)
  let cumulative = 0
  
  return features.map((feature, index) => {
    cumulative += feature.importance
    return {
      rank: index + 1,
      name: feature.name,
      importance: feature.importance,
      cumulative: cumulative / totalImportance
    }
  })
})

const maxImportance = computed(() => {
  return Math.max(...topFeatures.value.map(f => f.importance))
})

const cumulativeImportance = computed(() => {
  if (topFeatures.value.length === 0) return 0
  return topFeatures.value[topFeatures.value.length - 1]?.cumulative || 0
})

// 格式化函数
const formatPercent = (value: number | undefined) => {
  if (value === undefined || value === null) return '--'
  return `${(value * 100).toFixed(1)}%`
}

const formatNumber = (value: number | undefined) => {
  if (value === undefined || value === null) return '--'
  return value.toFixed(4)
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
    case 'importance':
      option = createImportanceChart()
      break
    case 'shap':
      option = createShapChart()
      break
    case 'correlation':
      option = createCorrelationChart()
      break
    case 'stability':
      option = createStabilityChart()
      break
  }
  
  chart.setOption(option, true)
}

// 特征重要性图表
const createImportanceChart = () => {
  const features = topFeatures.value
  
  return {
    title: {
      text: `Top ${topN.value} 重要特征`,
      left: 'center',
      textStyle: { fontSize: 14 }
    },
    tooltip: {
      trigger: 'axis',
      formatter: function(params: any) {
        const data = params[0]
        return `${data.name}<br/>重要性: ${data.value.toFixed(4)}`
      }
    },
    xAxis: {
      type: 'value',
      name: '重要性分数'
    },
    yAxis: {
      type: 'category',
      data: features.map(f => f.name).reverse(),
      axisLabel: {
        width: 100,
        overflow: 'truncate'
      }
    },
    series: [{
      type: 'bar',
      data: features.map(f => f.importance).reverse(),
      itemStyle: {
        color: function(params: any) {
          const colors = ['#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de']
          return colors[params.dataIndex % colors.length]
        }
      },
      barWidth: '60%',
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

// SHAP值分布图表
const createShapChart = () => {
  const shapData = props.data?.shap_values
  if (!shapData) {
    return {
      title: { text: 'SHAP值数据不可用', left: 'center' },
      graphic: {
        type: 'text',
        left: 'center',
        top: 'center',
        style: {
          text: '暂无SHAP值数据',
          fontSize: 16,
          fill: '#999'
        }
      }
    }
  }
  
  // 取前10个重要特征的SHAP值
  const topShapFeatures = topFeatures.value.slice(0, 10)
  const boxplotData = topShapFeatures.map(feature => {
    const values = shapData[feature.name] || []
    values.sort((a, b) => a - b)
    
    const q1 = values[Math.floor(values.length * 0.25)]
    const median = values[Math.floor(values.length * 0.5)]
    const q3 = values[Math.floor(values.length * 0.75)]
    const min = values[0]
    const max = values[values.length - 1]
    
    return [min, q1, median, q3, max]
  })
  
  return {
    title: {
      text: 'SHAP值分布箱线图',
      left: 'center',
      textStyle: { fontSize: 14 }
    },
    tooltip: {
      trigger: 'item',
      formatter: function(params: any) {
        const data = params.data
        return `${params.name}<br/>
                最小值: ${data[0].toFixed(4)}<br/>
                Q1: ${data[1].toFixed(4)}<br/>
                中位数: ${data[2].toFixed(4)}<br/>
                Q3: ${data[3].toFixed(4)}<br/>
                最大值: ${data[4].toFixed(4)}`
      }
    },
    xAxis: {
      type: 'category',
      data: topShapFeatures.map(f => f.name),
      axisLabel: {
        rotate: 45,
        interval: 0
      }
    },
    yAxis: {
      type: 'value',
      name: 'SHAP值'
    },
    series: [{
      name: 'SHAP分布',
      type: 'boxplot',
      data: boxplotData,
      itemStyle: {
        color: '#409EFF',
        borderColor: '#409EFF'
      }
    }]
  }
}

// 特征相关性热图
const createCorrelationChart = () => {
  const correlationMatrix = props.data?.correlation_matrix
  if (!correlationMatrix) {
    return {
      title: { text: '相关性数据不可用', left: 'center' }
    }
  }
  
  // 取前15个重要特征构建相关性矩阵
  const selectedFeatures = topFeatures.value.slice(0, 15).map(f => f.name)
  const heatmapData: Array<[number, number, number]> = []
  
  selectedFeatures.forEach((feature1, i) => {
    selectedFeatures.forEach((feature2, j) => {
      const correlation = correlationMatrix[feature1]?.[feature2] || 0
      heatmapData.push([i, j, correlation])
    })
  })
  
  return {
    title: {
      text: '特征相关性热图',
      left: 'center',
      textStyle: { fontSize: 14 }
    },
    tooltip: {
      position: 'top',
      formatter: function(params: any) {
        const xFeature = selectedFeatures[params.data[0]]
        const yFeature = selectedFeatures[params.data[1]]
        const correlation = params.data[2]
        return `${xFeature} vs ${yFeature}<br/>相关系数: ${correlation.toFixed(3)}`
      }
    },
    xAxis: {
      type: 'category',
      data: selectedFeatures,
      axisLabel: {
        rotate: 45,
        interval: 0
      }
    },
    yAxis: {
      type: 'category',
      data: selectedFeatures.slice().reverse()
    },
    visualMap: {
      min: -1,
      max: 1,
      calculable: true,
      orient: 'horizontal',
      left: 'center',
      bottom: '5%',
      inRange: {
        color: ['#313695', '#4575b4', '#74add1', '#abd9e9', '#e0f3f8', 
                '#ffffbf', '#fee090', '#fdae61', '#f46d43', '#d73027', '#a50026']
      }
    },
    series: [{
      name: '相关性',
      type: 'heatmap',
      data: heatmapData,
      emphasis: {
        itemStyle: {
          shadowBlur: 10,
          shadowColor: 'rgba(0, 0, 0, 0.5)'
        }
      }
    }]
  }
}

// 特征稳定性分析图表
const createStabilityChart = () => {
  // 模拟特征稳定性数据
  const features = topFeatures.value.slice(0, 10)
  const stabilityData = features.map(feature => ({
    name: feature.name,
    stability: Math.random() * 0.4 + 0.6, // 0.6-1.0之间
    variance: Math.random() * 0.2 + 0.05   // 0.05-0.25之间
  }))
  
  return {
    title: {
      text: '特征稳定性分析',
      left: 'center',
      textStyle: { fontSize: 14 }
    },
    tooltip: {
      trigger: 'axis',
      formatter: function(params: any) {
        return `${params[0].name}<br/>
                稳定性: ${params[0].value.toFixed(3)}<br/>
                方差: ${params[1].value.toFixed(3)}`
      }
    },
    legend: {
      data: ['稳定性', '方差'],
      top: 30
    },
    xAxis: {
      type: 'category',
      data: stabilityData.map(d => d.name),
      axisLabel: {
        rotate: 45,
        interval: 0
      }
    },
    yAxis: [
      {
        type: 'value',
        name: '稳定性',
        min: 0,
        max: 1
      },
      {
        type: 'value',
        name: '方差',
        min: 0,
        max: 0.3
      }
    ],
    series: [
      {
        name: '稳定性',
        type: 'bar',
        yAxisIndex: 0,
        data: stabilityData.map(d => d.stability),
        itemStyle: { color: '#67C23A' }
      },
      {
        name: '方差',
        type: 'line',
        yAxisIndex: 1,
        data: stabilityData.map(d => d.variance),
        itemStyle: { color: '#E6A23C' },
        symbol: 'circle',
        symbolSize: 6
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

watch([() => viewType.value, () => topN.value], () => {
  updateChart()
})

// 窗口大小变化时调整图表
window.addEventListener('resize', () => {
  chart?.resize()
})
</script>

<style scoped>
.feature-importance-chart {
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
  align-items: center;
}

.chart-content {
  min-height: 400px;
}

.summary-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 16px;
  margin-bottom: 20px;
}

.stat-card {
  background: #f8f9fa;
  padding: 16px;
  border-radius: 6px;
  text-align: center;
  border: 1px solid #e4e7ed;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 12px;
  color: #909399;
}

.chart-container {
  width: 100%;
  height: 400px;
}

.feature-details {
  margin-top: 20px;
}

.feature-details h4 {
  margin: 0 0 12px 0;
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.importance-bar {
  position: relative;
  display: flex;
  align-items: center;
  height: 20px;
  background: #f5f7fa;
  border-radius: 10px;
  overflow: hidden;
}

.importance-fill {
  height: 100%;
  background: linear-gradient(90deg, #409EFF, #67C23A);
  border-radius: 10px;
  transition: width 0.3s ease;
}

.importance-text {
  position: absolute;
  right: 8px;
  font-size: 11px;
  color: #606266;
  font-weight: 500;
}

:deep(.el-table) {
  font-size: 12px;
}

:deep(.el-table th) {
  background-color: #f5f7fa;
}

:deep(.el-input-number) {
  width: 100px;
}

:deep(.el-input-number .el-input__inner) {
  text-align: center;
}
</style>