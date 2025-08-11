<template>
  <div class="position-weight-pie">
    <div class="chart-header">
      <h3>持仓权重分布</h3>
      <div class="chart-controls">
        <el-select v-model="displayMode" @change="updateChart" style="width: 120px;">
          <el-option label="按股票" value="stock" />
          <el-option label="按行业" value="industry" />
          <el-option label="按市值" value="market_cap" />
        </el-select>
        <el-button-group>
          <el-button 
            :type="chartType === 'pie' ? 'primary' : 'default'"
            @click="setChartType('pie')"
            size="small"
          >
            饼图
          </el-button>
          <el-button 
            :type="chartType === 'doughnut' ? 'primary' : 'default'"
            @click="setChartType('doughnut')"
            size="small"
          >
            环图
          </el-button>
        </el-button-group>
        <el-button @click="exportChart" size="small">
          <el-icon><Download /></el-icon>
          导出
        </el-button>
      </div>
    </div>

    <el-row :gutter="20">
      <el-col :span="16">
        <div class="chart-container">
          <div ref="chartRef" class="chart"></div>
        </div>
      </el-col>
      <el-col :span="8">
        <div class="position-details">
          <h4>持仓明细</h4>
          <div class="position-list" v-loading="loading">
            <div 
              v-for="(item, index) in displayData" 
              :key="item.code"
              class="position-item"
              :class="{ top: index < 3 }"
            >
              <div class="position-left">
                <div class="position-rank">{{ index + 1 }}</div>
                <div class="position-info">
                  <div class="position-name">{{ item.name }}</div>
                  <div class="position-code">{{ item.code }}</div>
                </div>
              </div>
              <div class="position-right">
                <div class="position-weight">{{ formatPercentage(item.weight) }}</div>
                <div class="position-return" :class="item.return >= 0 ? 'positive' : 'negative'">
                  {{ formatPercentage(item.return) }}
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 集中度分析 -->
        <div class="concentration-analysis">
          <h4>集中度分析</h4>
          <div class="concentration-metrics">
            <div class="concentration-item">
              <span class="label">前5持仓占比:</span>
              <span class="value">{{ formatPercentage(concentrationMetrics.top5) }}</span>
            </div>
            <div class="concentration-item">
              <span class="label">前10持仓占比:</span>
              <span class="value">{{ formatPercentage(concentrationMetrics.top10) }}</span>
            </div>
            <div class="concentration-item">
              <span class="label">有效股票数:</span>
              <span class="value">{{ concentrationMetrics.effective_count }}</span>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import * as echarts from 'echarts'
import { Download } from '@element-plus/icons-vue'

interface PositionData {
  code: string
  name: string
  weight: number
  return: number
  industry?: string
  market_cap_category?: string
}

interface ConcentrationMetrics {
  top5: number
  top10: number
  effective_count: number
}

const props = defineProps<{
  data?: PositionData[]
  experimentId?: string
}>()

// 响应式数据
const chartRef = ref()
const loading = ref(false)
const displayMode = ref('stock')
const chartType = ref('pie')

let mainChart: echarts.ECharts | null = null
const rawData = ref<PositionData[]>([])

const concentrationMetrics = reactive<ConcentrationMetrics>({
  top5: 0,
  top10: 0,
  effective_count: 0
})

// 计算属性
const displayData = computed(() => {
  let data = [...rawData.value]
  
  // 根据显示模式进行分组
  if (displayMode.value !== 'stock') {
    data = groupData(data, displayMode.value)
  }
  
  // 按权重排序
  data.sort((a, b) => b.weight - a.weight)
  
  return data
})

// 方法
const initChart = () => {
  if (!chartRef.value) return
  
  mainChart = echarts.init(chartRef.value)
  updateChart()
}

const updateChart = () => {
  if (!mainChart || displayData.value.length === 0) return
  
  const option = getChartOption()
  mainChart.setOption(option, true)
}

const getChartOption = () => {
  const data = displayData.value.map((item, index) => ({
    name: item.name,
    value: item.weight,
    code: item.code,
    return: item.return,
    itemStyle: {
      color: generateColor(index)
    }
  }))
  
  return {
    tooltip: {
      trigger: 'item',
      formatter: (params: any) => {
        const data = params.data
        return `
          <div style="margin-bottom: 4px;"><strong>${data.name}</strong></div>
          <div>权重: <strong>${formatPercentage(data.value)}</strong></div>
          <div>收益: <strong style="color: ${data.return >= 0 ? '#67c23a' : '#f56c6c'}">${formatPercentage(data.return)}</strong></div>
        `
      }
    },
    legend: {
      orient: 'vertical',
      left: 'left',
      data: data.map(item => item.name)
    },
    series: [{
      name: '持仓权重',
      type: 'pie',
      radius: chartType.value === 'doughnut' ? ['40%', '70%'] : '70%',
      center: ['60%', '50%'],
      data: data,
      emphasis: {
        itemStyle: {
          shadowBlur: 10,
          shadowOffsetX: 0,
          shadowColor: 'rgba(0, 0, 0, 0.5)'
        }
      },
      label: {
        show: displayData.value.length <= 10,
        formatter: '{b}: {d}%'
      }
    }]
  }
}

const setChartType = (type: string) => {
  chartType.value = type
  updateChart()
}

const groupData = (data: PositionData[], mode: string): PositionData[] => {
  const groups: Record<string, PositionData[]> = {}
  
  data.forEach(item => {
    let key = ''
    switch (mode) {
      case 'industry':
        key = item.industry || '其他'
        break
      case 'market_cap':
        key = item.market_cap_category || '其他'
        break
    }
    
    if (!groups[key]) {
      groups[key] = []
    }
    groups[key].push(item)
  })
  
  return Object.entries(groups).map(([name, items]) => {
    const totalWeight = items.reduce((sum, item) => sum + item.weight, 0)
    const avgReturn = items.reduce((sum, item) => sum + item.return * item.weight, 0) / totalWeight
    
    return {
      code: name,
      name,
      weight: totalWeight,
      return: avgReturn
    }
  })
}

const calculateConcentrationMetrics = () => {
  const sortedData = [...displayData.value].sort((a, b) => b.weight - a.weight)
  
  concentrationMetrics.top5 = sortedData.slice(0, 5).reduce((sum, item) => sum + item.weight, 0)
  concentrationMetrics.top10 = sortedData.slice(0, 10).reduce((sum, item) => sum + item.weight, 0)
  
  // 计算有效股票数
  const hhi = sortedData.reduce((sum, item) => sum + Math.pow(item.weight, 2), 0)
  concentrationMetrics.effective_count = Math.round(1 / hhi)
}

const loadData = async () => {
  loading.value = true
  try {
    if (props.data) {
      rawData.value = props.data
    } else if (props.experimentId) {
      const response = await fetch(`/api/v1/experiments/${props.experimentId}/positions`)
      const data = await response.json()
      
      if (data.success) {
        rawData.value = data.data.positions
      }
    } else {
      // 生成模拟数据
      generateMockData()
    }
    
    calculateConcentrationMetrics()
  } catch (error) {
    console.error('加载持仓数据失败:', error)
    generateMockData()
  } finally {
    loading.value = false
  }
}

const generateMockData = () => {
  const industries = ['银行', '医药', '科技', '消费', '制造']
  const marketCaps = ['大盘', '中盘', '小盘']
  
  const data: PositionData[] = []
  
  for (let i = 0; i < 20; i++) {
    data.push({
      code: `00000${i + 1}`.slice(-6),
      name: `股票${i + 1}`,
      weight: Math.random() * 0.1,
      return: (Math.random() - 0.5) * 0.3,
      industry: industries[Math.floor(Math.random() * industries.length)],
      market_cap_category: marketCaps[Math.floor(Math.random() * marketCaps.length)]
    })
  }
  
  // 标准化权重
  const totalWeight = data.reduce((sum, item) => sum + item.weight, 0)
  data.forEach(item => item.weight = item.weight / totalWeight)
  
  rawData.value = data
}

const exportChart = () => {
  if (!mainChart) return
  
  const url = mainChart.getDataURL({
    type: 'png',
    pixelRatio: 2,
    backgroundColor: '#fff'
  })
  
  const link = document.createElement('a')
  link.download = `position-weight-${Date.now()}.png`
  link.href = url
  link.click()
}

const generateColor = (index: number): string => {
  const colors = [
    '#409eff', '#67c23a', '#e6a23c', '#f56c6c', '#909399',
    '#36cfc9', '#73d13d', '#ff85c0', '#9254de', '#ffc53d'
  ]
  return colors[index % colors.length]
}

const formatPercentage = (value: number): string => {
  return (value * 100).toFixed(2) + '%'
}

// 监听器
watch(() => displayData.value, () => {
  updateChart()
  calculateConcentrationMetrics()
})

// 生命周期
onMounted(async () => {
  await loadData()
  await nextTick()
  initChart()
  
  window.addEventListener('resize', () => {
    mainChart?.resize()
  })
})

onUnmounted(() => {
  mainChart?.dispose()
  window.removeEventListener('resize', () => {
    mainChart?.resize()
  })
})
</script>

<style scoped>
.position-weight-pie {
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
  background: white;
  border-radius: 8px;
  padding: 20px;
}

.chart {
  height: 500px;
  width: 100%;
}

.position-details h4 {
  margin-bottom: 16px;
  font-size: 16px;
  font-weight: 600;
}

.position-list {
  max-height: 400px;
  overflow-y: auto;
}

.position-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  border-radius: 6px;
  margin-bottom: 8px;
  border: 1px solid #e4e7ed;
}

.position-item.top {
  border-left: 3px solid #409eff;
}

.position-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.position-rank {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: #409eff;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
}

.position-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.position-name {
  font-weight: 600;
  font-size: 14px;
}

.position-code {
  font-size: 12px;
  color: #666;
}

.position-right {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 2px;
}

.position-weight {
  font-weight: 600;
  font-size: 14px;
}

.position-return {
  font-size: 12px;
}

.position-return.positive {
  color: #67c23a;
}

.position-return.negative {
  color: #f56c6c;
}

.concentration-analysis {
  margin-top: 24px;
}

.concentration-analysis h4 {
  margin-bottom: 16px;
  font-size: 16px;
  font-weight: 600;
}

.concentration-metrics {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.concentration-item {
  display: flex;
  justify-content: space-between;
  padding: 8px 12px;
  background: #f8f9fa;
  border-radius: 4px;
}

.concentration-item .label {
  color: #666;
  font-size: 13px;
}

.concentration-item .value {
  font-weight: 600;
  font-size: 13px;
}
</style>