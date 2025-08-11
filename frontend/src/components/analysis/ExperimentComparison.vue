<template>
  <div class="experiment-comparison">
    <el-card>
      <template #header>
        <div class="comparison-header">
          <h3>实验对比分析</h3>
          <div class="header-actions">
            <el-button @click="showAddDialog = true">
              <el-icon><Plus /></el-icon>
              添加实验
            </el-button>
            <el-button @click="exportComparison">
              <el-icon><Download /></el-icon>
              导出报告
            </el-button>
          </div>
        </div>
      </template>

      <!-- 实验选择区域 -->
      <div class="experiment-selector">
        <div class="selected-experiments">
          <div 
            v-for="experiment in selectedExperiments" 
            :key="experiment.id"
            class="experiment-tag"
            :style="{ borderColor: experiment.color }"
          >
            <div class="experiment-info">
              <span class="experiment-name">{{ experiment.name }}</span>
              <span class="experiment-date">{{ formatDate(experiment.created_at) }}</span>
            </div>
            <el-button 
              type="text" 
              size="small"
              @click="removeExperiment(experiment.id)"
            >
              <el-icon><Close /></el-icon>
            </el-button>
          </div>
        </div>
      </div>

      <!-- 对比维度选择 -->
      <div class="comparison-dimensions">
        <el-tabs v-model="activeTab" @tab-change="handleTabChange">
          <el-tab-pane label="性能指标" name="performance">
            <div class="metrics-comparison">
              <el-row :gutter="16">
                <el-col :span="12">
                  <div class="chart-container">
                    <h4>收益率对比</h4>
                    <div ref="returnChartRef" class="chart"></div>
                  </div>
                </el-col>
                <el-col :span="12">
                  <div class="chart-container">
                    <h4>风险指标对比</h4>
                    <div ref="riskChartRef" class="chart"></div>
                  </div>
                </el-col>
              </el-row>
              
              <div class="metrics-table">
                <h4>详细指标对比</h4>
                <el-table :data="performanceComparison" border>
                  <el-table-column prop="metric" label="指标" width="150" fixed="left">
                    <template #default="scope">
                      <strong>{{ scope.row.metric }}</strong>
                    </template>
                  </el-table-column>
                  <el-table-column 
                    v-for="experiment in selectedExperiments"
                    :key="experiment.id"
                    :prop="experiment.id"
                    :label="experiment.name"
                    min-width="120"
                  >
                    <template #header>
                      <div class="experiment-header" :style="{ color: experiment.color }">
                        {{ experiment.name }}
                      </div>
                    </template>
                    <template #default="scope">
                      <span :class="getMetricClass(scope.row.type, scope.row[experiment.id])">
                        {{ formatMetricValue(scope.row.type, scope.row[experiment.id]) }}
                      </span>
                    </template>
                  </el-table-column>
                  <el-table-column label="最佳" width="100">
                    <template #default="scope">
                      <el-tag 
                        :type="getBestPerformerType(scope.row)"
                        size="small"
                      >
                        {{ getBestPerformer(scope.row) }}
                      </el-tag>
                    </template>
                  </el-table-column>
                </el-table>
              </div>
            </div>
          </el-tab-pane>

          <el-tab-pane label="收益曲线" name="returns">
            <div class="returns-comparison">
              <div class="chart-controls">
                <el-radio-group v-model="returnsViewMode" @change="updateReturnsChart">
                  <el-radio-button value="cumulative">累计收益</el-radio-button>
                  <el-radio-button value="daily">日收益</el-radio-button>
                  <el-radio-button value="rolling">滚动收益</el-radio-button>
                </el-radio-group>
                <el-select v-model="rollingWindow" v-if="returnsViewMode === 'rolling'" style="width: 100px; margin-left: 12px;">
                  <el-option label="30天" :value="30" />
                  <el-option label="60天" :value="60" />
                  <el-option label="90天" :value="90" />
                </el-select>
              </div>
              <div ref="returnsChartRef" class="chart large-chart"></div>
            </div>
          </el-tab-pane>

          <el-tab-pane label="回撤对比" name="drawdown">
            <div class="drawdown-comparison">
              <el-row :gutter="16">
                <el-col :span="16">
                  <div ref="drawdownChartRef" class="chart large-chart"></div>
                </el-col>
                <el-col :span="8">
                  <div class="drawdown-stats">
                    <h4>回撤统计</h4>
                    <div class="stats-list">
                      <div 
                        v-for="experiment in selectedExperiments" 
                        :key="experiment.id"
                        class="stat-item"
                      >
                        <div class="stat-header" :style="{ color: experiment.color }">
                          {{ experiment.name }}
                        </div>
                        <div class="stat-metrics">
                          <div class="stat-row">
                            <span>最大回撤:</span>
                            <span class="negative">{{ formatPercentage(experiment.metrics?.max_drawdown || 0) }}</span>
                          </div>
                          <div class="stat-row">
                            <span>回撤次数:</span>
                            <span>{{ experiment.metrics?.drawdown_count || 0 }}</span>
                          </div>
                          <div class="stat-row">
                            <span>平均回撤:</span>
                            <span class="negative">{{ formatPercentage(experiment.metrics?.avg_drawdown || 0) }}</span>
                          </div>
                          <div class="stat-row">
                            <span>恢复天数:</span>
                            <span>{{ experiment.metrics?.avg_recovery_days || 0 }} 天</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </el-col>
              </el-row>
            </div>
          </el-tab-pane>

          <el-tab-pane label="持仓对比" name="positions">
            <div class="positions-comparison">
              <div class="position-controls">
                <el-date-picker
                  v-model="positionDate"
                  type="date"
                  placeholder="选择对比日期"
                  @change="loadPositionData"
                  style="margin-right: 16px;"
                />
                <el-select v-model="positionViewMode" @change="updatePositionCharts">
                  <el-option label="权重对比" value="weight" />
                  <el-option label="行业分布" value="industry" />
                  <el-option label="个股重叠" value="overlap" />
                </el-select>
              </div>
              
              <el-row :gutter="16">
                <el-col :span="12">
                  <div ref="position1ChartRef" class="chart"></div>
                </el-col>
                <el-col :span="12">
                  <div ref="position2ChartRef" class="chart"></div>
                </el-col>
              </el-row>
              
              <!-- 持仓重叠分析 -->
              <div class="position-overlap" v-if="positionOverlap.length > 0">
                <h4>重叠持仓分析</h4>
                <el-table :data="positionOverlap" size="small">
                  <el-table-column prop="stock_code" label="股票代码" width="100" />
                  <el-table-column prop="stock_name" label="股票名称" width="120" />
                  <el-table-column 
                    v-for="experiment in selectedExperiments"
                    :key="experiment.id"
                    :label="`${experiment.name}权重`"
                    width="120"
                  >
                    <template #default="scope">
                      {{ formatPercentage(scope.row.weights[experiment.id] || 0) }}
                    </template>
                  </el-table-column>
                  <el-table-column prop="weight_diff" label="权重差异" width="100">
                    <template #default="scope">
                      <span :class="Math.abs(scope.row.weight_diff) > 0.02 ? 'warning' : ''">
                        {{ formatPercentage(Math.abs(scope.row.weight_diff)) }}
                      </span>
                    </template>
                  </el-table-column>
                </el-table>
              </div>
            </div>
          </el-tab-pane>

          <el-tab-pane label="策略配置" name="config">
            <div class="config-comparison">
              <div class="config-table">
                <el-table :data="configComparison" border>
                  <el-table-column prop="category" label="配置类别" width="120" />
                  <el-table-column prop="parameter" label="参数" width="150" />
                  <el-table-column 
                    v-for="experiment in selectedExperiments"
                    :key="experiment.id"
                    :label="experiment.name"
                    min-width="150"
                  >
                    <template #default="scope">
                      <span :class="getDiffClass(scope.row, experiment.id)">
                        {{ formatConfigValue(scope.row[experiment.id]) }}
                      </span>
                    </template>
                  </el-table-column>
                  <el-table-column label="差异" width="80">
                    <template #default="scope">
                      <el-icon v-if="hasConfigDifference(scope.row)" class="warning-icon">
                        <WarningFilled />
                      </el-icon>
                      <el-icon v-else class="success-icon">
                        <CircleCheckFilled />
                      </el-icon>
                    </template>
                  </el-table-column>
                </el-table>
              </div>
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>
    </el-card>

    <!-- 添加实验对话框 -->
    <el-dialog v-model="showAddDialog" title="添加对比实验" width="600px">
      <div class="experiment-search">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索实验名称"
          @input="searchExperiments"
          style="margin-bottom: 16px;"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        
        <el-table 
          :data="availableExperiments" 
          @selection-change="handleSelectionChange"
          max-height="400"
        >
          <el-table-column type="selection" width="55" />
          <el-table-column prop="name" label="实验名称" />
          <el-table-column prop="created_at" label="创建时间" width="150">
            <template #default="scope">
              {{ formatDate(scope.row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="100">
            <template #default="scope">
              <el-tag :type="getStatusType(scope.row.status)">
                {{ getStatusText(scope.row.status) }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
      </div>
      
      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" @click="addSelectedExperiments">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted, nextTick, watch } from 'vue'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'
import {
  Plus,
  Download,
  Close,
  Search,
  WarningFilled,
  CircleCheckFilled
} from '@element-plus/icons-vue'

interface Experiment {
  id: string
  name: string
  created_at: string
  status: string
  color?: string
  metrics?: any
  config?: any
  returns_data?: any[]
  drawdown_data?: any[]
  positions?: any[]
}

interface MetricComparison {
  metric: string
  type: 'percentage' | 'ratio' | 'number'
  [key: string]: any
}

interface PositionOverlap {
  stock_code: string
  stock_name: string
  weights: Record<string, number>
  weight_diff: number
}

const props = defineProps<{
  initialExperiments?: string[]
}>()

// 响应式数据
const selectedExperiments = ref<Experiment[]>([])
const availableExperiments = ref<Experiment[]>([])
const performanceComparison = ref<MetricComparison[]>([])
const configComparison = ref<any[]>([])
const positionOverlap = ref<PositionOverlap[]>([])

const showAddDialog = ref(false)
const searchKeyword = ref('')
const selectedForAdd = ref<Experiment[]>([])

const activeTab = ref('performance')
const returnsViewMode = ref('cumulative')
const rollingWindow = ref(30)
const positionViewMode = ref('weight')
const positionDate = ref('')

// 图表引用
const returnChartRef = ref()
const riskChartRef = ref()
const returnsChartRef = ref()
const drawdownChartRef = ref()
const position1ChartRef = ref()
const position2ChartRef = ref()

let returnChart: echarts.ECharts | null = null
let riskChart: echarts.ECharts | null = null
let returnsChart: echarts.ECharts | null = null
let drawdownChart: echarts.ECharts | null = null
let position1Chart: echarts.ECharts | null = null
let position2Chart: echarts.ECharts | null = null

const colors = ['#409eff', '#67c23a', '#e6a23c', '#f56c6c', '#909399']

// 方法
const initCharts = async () => {
  await nextTick()
  
  if (returnChartRef.value) {
    returnChart = echarts.init(returnChartRef.value)
  }
  if (riskChartRef.value) {
    riskChart = echarts.init(riskChartRef.value)
  }
  if (returnsChartRef.value) {
    returnsChart = echarts.init(returnsChartRef.value)
  }
  if (drawdownChartRef.value) {
    drawdownChart = echarts.init(drawdownChartRef.value)
  }
  if (position1ChartRef.value) {
    position1Chart = echarts.init(position1ChartRef.value)
  }
  if (position2ChartRef.value) {
    position2Chart = echarts.init(position2ChartRef.value)
  }
  
  updateAllCharts()
}

const updateAllCharts = () => {
  updateReturnChart()
  updateRiskChart()
  updateReturnsChart()
  updateDrawdownChart()
  updatePositionCharts()
}

const updateReturnChart = () => {
  if (!returnChart || selectedExperiments.value.length === 0) return
  
  const data = selectedExperiments.value.map(exp => ({
    name: exp.name,
    value: exp.metrics?.total_return || 0,
    itemStyle: { color: exp.color }
  }))
  
  const option = {
    title: { text: '总收益率对比', left: 'center' },
    tooltip: {
      formatter: (params: any) => {
        return `${params.name}: ${formatPercentage(params.value)}`
      }
    },
    xAxis: {
      type: 'category',
      data: data.map(d => d.name),
      axisLabel: { interval: 0, rotate: 45 }
    },
    yAxis: {
      type: 'value',
      axisLabel: { formatter: (value: number) => formatPercentage(value) }
    },
    series: [{
      type: 'bar',
      data: data,
      itemStyle: {
        borderRadius: [4, 4, 0, 0]
      }
    }]
  }
  
  returnChart.setOption(option)
}

const updateRiskChart = () => {
  if (!riskChart || selectedExperiments.value.length === 0) return
  
  const categories = ['夏普比率', '最大回撤', '波动率', 'Calmar比率']
  const data = selectedExperiments.value.map(exp => ({
    name: exp.name,
    value: [
      exp.metrics?.sharpe_ratio || 0,
      Math.abs(exp.metrics?.max_drawdown || 0),
      exp.metrics?.volatility || 0,
      exp.metrics?.calmar_ratio || 0
    ],
    itemStyle: { color: exp.color }
  }))
  
  const option = {
    title: { text: '风险指标雷达图', left: 'center' },
    tooltip: {},
    legend: {
      data: data.map(d => d.name),
      bottom: 0
    },
    radar: {
      indicator: categories.map(cat => ({ name: cat, max: 1 })),
      radius: '70%'
    },
    series: [{
      type: 'radar',
      data: data.map(d => ({
        ...d,
        value: d.value.map((v, i) => {
          // 标准化数值到0-1范围
          if (i === 0 || i === 3) return Math.min(v / 2, 1) // 夏普比率和Calmar比率
          if (i === 1) return Math.min(v * 5, 1) // 最大回撤
          return Math.min(v * 10, 1) // 波动率
        })
      }))
    }]
  }
  
  riskChart.setOption(option)
}

const updateReturnsChart = () => {
  if (!returnsChart || selectedExperiments.value.length === 0) return
  
  const series = selectedExperiments.value.map(exp => {
    let data = exp.returns_data || []
    
    if (returnsViewMode.value === 'daily') {
      data = data.map((item, index) => ({
        ...item,
        value: index === 0 ? item.return : item.return - data[index - 1].return
      }))
    } else if (returnsViewMode.value === 'rolling') {
      data = calculateRollingReturns(data, rollingWindow.value)
    }
    
    return {
      name: exp.name,
      type: 'line',
      data: data.map(d => [d.date, d.return]),
      itemStyle: { color: exp.color },
      lineStyle: { color: exp.color },
      smooth: true
    }
  })
  
  const option = {
    tooltip: {
      trigger: 'axis',
      formatter: (params: any[]) => {
        let result = `<div><strong>${params[0].axisValue}</strong></div>`
        params.forEach(param => {
          result += `<div style="color: ${param.color}">${param.seriesName}: ${formatPercentage(param.value[1])}</div>`
        })
        return result
      }
    },
    legend: {
      data: series.map(s => s.name),
      bottom: 0
    },
    xAxis: {
      type: 'time'
    },
    yAxis: {
      type: 'value',
      axisLabel: { formatter: (value: number) => formatPercentage(value) }
    },
    dataZoom: [{
      type: 'inside'
    }, {
      type: 'slider',
      bottom: '10%'
    }],
    series
  }
  
  returnsChart.setOption(option)
}

const updateDrawdownChart = () => {
  if (!drawdownChart || selectedExperiments.value.length === 0) return
  
  const series = selectedExperiments.value.map(exp => ({
    name: exp.name,
    type: 'line',
    data: (exp.drawdown_data || []).map(d => [d.date, d.drawdown]),
    itemStyle: { color: exp.color },
    lineStyle: { color: exp.color },
    areaStyle: { color: exp.color, opacity: 0.2 },
    smooth: true
  }))
  
  const option = {
    title: { text: '回撤对比', left: 'center' },
    tooltip: {
      trigger: 'axis',
      formatter: (params: any[]) => {
        let result = `<div><strong>${params[0].axisValue}</strong></div>`
        params.forEach(param => {
          result += `<div style="color: ${param.color}">${param.seriesName}: ${formatPercentage(param.value[1])}</div>`
        })
        return result
      }
    },
    legend: {
      data: series.map(s => s.name),
      bottom: 0
    },
    xAxis: {
      type: 'time'
    },
    yAxis: {
      type: 'value',
      max: 0,
      axisLabel: { formatter: (value: number) => formatPercentage(value) }
    },
    dataZoom: [{
      type: 'inside'
    }, {
      type: 'slider',
      bottom: '10%'
    }],
    series
  }
  
  drawdownChart.setOption(option)
}

const updatePositionCharts = () => {
  if (selectedExperiments.value.length < 2) return
  
  const exp1 = selectedExperiments.value[0]
  const exp2 = selectedExperiments.value[1]
  
  if (position1Chart && exp1.positions) {
    updatePositionChart(position1Chart, exp1)
  }
  if (position2Chart && exp2.positions) {
    updatePositionChart(position2Chart, exp2)
  }
}

const updatePositionChart = (chart: echarts.ECharts, experiment: Experiment) => {
  const positions = experiment.positions || []
  
  let data = []
  if (positionViewMode.value === 'weight') {
    data = positions.slice(0, 10).map((pos, index) => ({
      name: pos.stock_name,
      value: pos.weight,
      itemStyle: { color: colors[index % colors.length] }
    }))
  } else if (positionViewMode.value === 'industry') {
    // 按行业分组
    const industryGroups: Record<string, number> = {}
    positions.forEach(pos => {
      const industry = pos.industry || '其他'
      industryGroups[industry] = (industryGroups[industry] || 0) + pos.weight
    })
    
    data = Object.entries(industryGroups).map(([industry, weight], index) => ({
      name: industry,
      value: weight,
      itemStyle: { color: colors[index % colors.length] }
    }))
  }
  
  const option = {
    title: { text: experiment.name, left: 'center' },
    tooltip: {
      formatter: (params: any) => {
        return `${params.name}: ${formatPercentage(params.value)}`
      }
    },
    series: [{
      type: 'pie',
      radius: '70%',
      data,
      label: { show: data.length <= 8 }
    }]
  }
  
  chart.setOption(option)
}

const calculateRollingReturns = (data: any[], window: number) => {
  return data.map((item, index) => {
    if (index < window - 1) return { ...item, return: 0 }
    
    const startValue = data[index - window + 1].return
    const endValue = item.return
    return { ...item, return: endValue - startValue }
  })
}

const loadExperimentData = async (experimentId: string) => {
  try {
    const [detailRes, returnsRes, drawdownRes, positionsRes] = await Promise.all([
      fetch(`/api/v1/experiments/${experimentId}`),
      fetch(`/api/v1/experiments/${experimentId}/returns`),
      fetch(`/api/v1/experiments/${experimentId}/drawdown`),
      fetch(`/api/v1/experiments/${experimentId}/positions`)
    ])
    
    const [detail, returns, drawdown, positions] = await Promise.all([
      detailRes.json(),
      returnsRes.json(),
      drawdownRes.json(),
      positionsRes.json()
    ])
    
    return {
      ...detail.data,
      returns_data: returns.data || [],
      drawdown_data: drawdown.data || [],
      positions: positions.data?.positions || []
    }
  } catch (error) {
    console.error(`加载实验数据失败: ${experimentId}`, error)
    return null
  }
}

const addExperiment = async (experiment: Experiment) => {
  if (selectedExperiments.value.find(e => e.id === experiment.id)) {
    ElMessage.warning('该实验已添加')
    return
  }
  
  if (selectedExperiments.value.length >= 5) {
    ElMessage.warning('最多只能对比5个实验')
    return
  }
  
  // 分配颜色
  const color = colors[selectedExperiments.value.length % colors.length]
  experiment.color = color
  
  // 加载实验数据
  const experimentData = await loadExperimentData(experiment.id)
  if (experimentData) {
    selectedExperiments.value.push({ ...experiment, ...experimentData })
    generatePerformanceComparison()
    generateConfigComparison()
    updateAllCharts()
  }
}

const removeExperiment = (experimentId: string) => {
  const index = selectedExperiments.value.findIndex(e => e.id === experimentId)
  if (index > -1) {
    selectedExperiments.value.splice(index, 1)
    generatePerformanceComparison()
    generateConfigComparison()
    updateAllCharts()
  }
}

const generatePerformanceComparison = () => {
  const metrics = [
    { key: 'total_return', label: '总收益率', type: 'percentage' },
    { key: 'annual_return', label: '年化收益率', type: 'percentage' },
    { key: 'sharpe_ratio', label: '夏普比率', type: 'ratio' },
    { key: 'max_drawdown', label: '最大回撤', type: 'percentage' },
    { key: 'volatility', label: '波动率', type: 'percentage' },
    { key: 'calmar_ratio', label: 'Calmar比率', type: 'ratio' },
    { key: 'win_rate', label: '胜率', type: 'percentage' },
    { key: 'profit_loss_ratio', label: '盈亏比', type: 'ratio' }
  ]
  
  performanceComparison.value = metrics.map(metric => {
    const row: any = {
      metric: metric.label,
      type: metric.type
    }
    
    selectedExperiments.value.forEach(exp => {
      row[exp.id] = exp.metrics?.[metric.key] || 0
    })
    
    return row
  })
}

const generateConfigComparison = () => {
  if (selectedExperiments.value.length < 2) {
    configComparison.value = []
    return
  }
  
  const configKeys = new Set<string>()
  selectedExperiments.value.forEach(exp => {
    if (exp.config) {
      // 提取配置参数
      Object.keys(exp.config.model_config?.params || {}).forEach(key => configKeys.add(`model.${key}`))
      Object.keys(exp.config.strategy_config?.params || {}).forEach(key => configKeys.add(`strategy.${key}`))
      Object.keys(exp.config.data_config || {}).forEach(key => configKeys.add(`data.${key}`))
    }
  })
  
  configComparison.value = Array.from(configKeys).map(key => {
    const [category, param] = key.split('.')
    const row: any = {
      category: category === 'model' ? '模型' : category === 'strategy' ? '策略' : '数据',
      parameter: param
    }
    
    selectedExperiments.value.forEach(exp => {
      let value = null
      if (category === 'model') {
        value = exp.config?.model_config?.params?.[param]
      } else if (category === 'strategy') {
        value = exp.config?.strategy_config?.params?.[param]
      } else if (category === 'data') {
        value = exp.config?.data_config?.[param]
      }
      row[exp.id] = value
    })
    
    return row
  })
}

const searchExperiments = async () => {
  try {
    const response = await fetch(`/api/v1/experiments?search=${encodeURIComponent(searchKeyword.value)}&status=completed&limit=50`)
    const data = await response.json()
    
    if (data.success) {
      availableExperiments.value = data.data.items.filter(
        (exp: Experiment) => !selectedExperiments.value.find(e => e.id === exp.id)
      )
    }
  } catch (error) {
    console.error('搜索实验失败:', error)
  }
}

const handleSelectionChange = (selection: Experiment[]) => {
  selectedForAdd.value = selection
}

const addSelectedExperiments = async () => {
  for (const experiment of selectedForAdd.value) {
    await addExperiment(experiment)
  }
  
  showAddDialog.value = false
  selectedForAdd.value = []
  searchKeyword.value = ''
}

const loadPositionData = async () => {
  if (!positionDate.value) return
  
  for (const experiment of selectedExperiments.value) {
    try {
      const response = await fetch(`/api/v1/experiments/${experiment.id}/positions?date=${positionDate.value}`)
      const data = await response.json()
      
      if (data.success) {
        experiment.positions = data.data.positions
      }
    } catch (error) {
      console.error('加载持仓数据失败:', error)
    }
  }
  
  updatePositionCharts()
  calculatePositionOverlap()
}

const calculatePositionOverlap = () => {
  if (selectedExperiments.value.length < 2) {
    positionOverlap.value = []
    return
  }
  
  const allStocks = new Set<string>()
  selectedExperiments.value.forEach(exp => {
    exp.positions?.forEach(pos => allStocks.add(pos.stock_code))
  })
  
  const overlaps: PositionOverlap[] = []
  allStocks.forEach(stockCode => {
    const weights: Record<string, number> = {}
    let hasMultiple = false
    let stockName = ''
    
    selectedExperiments.value.forEach(exp => {
      const position = exp.positions?.find(pos => pos.stock_code === stockCode)
      if (position) {
        weights[exp.id] = position.weight
        stockName = position.stock_name
        if (Object.keys(weights).length > 1) hasMultiple = true
      } else {
        weights[exp.id] = 0
      }
    })
    
    if (hasMultiple) {
      const weightValues = Object.values(weights)
      const maxWeight = Math.max(...weightValues)
      const minWeight = Math.min(...weightValues)
      
      overlaps.push({
        stock_code: stockCode,
        stock_name: stockName,
        weights,
        weight_diff: maxWeight - minWeight
      })
    }
  })
  
  positionOverlap.value = overlaps.sort((a, b) => b.weight_diff - a.weight_diff)
}

const handleTabChange = (tabName: string) => {
  activeTab.value = tabName
  
  if (tabName === 'positions') {
    // 设置默认日期为最近日期
    if (!positionDate.value && selectedExperiments.value.length > 0) {
      positionDate.value = new Date().toISOString().split('T')[0]
      loadPositionData()
    }
  }
}

const exportComparison = () => {
  // 导出对比报告逻辑
  ElMessage.success('导出功能开发中...')
}

// 工具函数
const formatDate = (dateString: string): string => {
  return new Date(dateString).toLocaleDateString()
}

const formatPercentage = (value: number): string => {
  return (value * 100).toFixed(2) + '%'
}

const formatMetricValue = (type: string, value: number): string => {
  if (type === 'percentage') return formatPercentage(value)
  if (type === 'ratio') return value.toFixed(3)
  return value.toFixed(2)
}

const formatConfigValue = (value: any): string => {
  if (value === null || value === undefined) return '-'
  if (typeof value === 'boolean') return value ? '是' : '否'
  if (typeof value === 'number') return value.toString()
  return String(value)
}

const getMetricClass = (type: string, value: number): string => {
  if (type === 'percentage' && value < 0) return 'negative'
  if (value > 0) return 'positive'
  return ''
}

const getBestPerformer = (row: any): string => {
  if (selectedExperiments.value.length === 0) return '-'
  
  let bestExp = selectedExperiments.value[0]
  let bestValue = row[bestExp.id]
  
  selectedExperiments.value.forEach(exp => {
    const value = row[exp.id]
    if ((row.type !== 'percentage' || row.metric !== '最大回撤') && value > bestValue) {
      bestValue = value
      bestExp = exp
    } else if (row.metric === '最大回撤' && Math.abs(value) < Math.abs(bestValue)) {
      bestValue = value
      bestExp = exp
    }
  })
  
  return bestExp.name.substring(0, 8)
}

const getBestPerformerType = (row: any): string => {
  return 'success'
}

const getDiffClass = (row: any, experimentId: string): string => {
  const values = selectedExperiments.value.map(exp => row[exp.id])
  const uniqueValues = [...new Set(values)]
  return uniqueValues.length > 1 ? 'diff' : ''
}

const hasConfigDifference = (row: any): boolean => {
  const values = selectedExperiments.value.map(exp => row[exp.id])
  const uniqueValues = [...new Set(values)]
  return uniqueValues.length > 1
}

const getStatusType = (status: string): string => {
  const typeMap: Record<string, string> = {
    'completed': 'success',
    'running': 'warning',
    'failed': 'danger',
    'pending': 'info'
  }
  return typeMap[status] || 'info'
}

const getStatusText = (status: string): string => {
  const textMap: Record<string, string> = {
    'completed': '已完成',
    'running': '运行中',
    'failed': '失败',
    'pending': '等待中'
  }
  return textMap[status] || status
}

// 生命周期
onMounted(async () => {
  // 初始化实验
  if (props.initialExperiments && props.initialExperiments.length > 0) {
    for (const expId of props.initialExperiments.slice(0, 5)) {
      // 创建基础实验对象
      const experiment: Experiment = {
        id: expId,
        name: `实验 ${expId}`,
        created_at: new Date().toISOString(),
        status: 'completed'
      }
      await addExperiment(experiment)
    }
  }
  
  await initCharts()
  await searchExperiments()
  
  // 窗口大小变化时调整图表
  window.addEventListener('resize', () => {
    returnChart?.resize()
    riskChart?.resize()
    returnsChart?.resize()
    drawdownChart?.resize()
    position1Chart?.resize()
    position2Chart?.resize()
  })
})

onUnmounted(() => {
  returnChart?.dispose()
  riskChart?.dispose()
  returnsChart?.dispose()
  drawdownChart?.dispose()
  position1Chart?.dispose()
  position2Chart?.dispose()
  
  window.removeEventListener('resize', () => {
    returnChart?.resize()
    riskChart?.resize()
    returnsChart?.resize()
    drawdownChart?.resize()
    position1Chart?.resize()
    position2Chart?.resize()
  })
})
</script>

<style scoped>
.experiment-comparison {
  padding: 20px;
}

.comparison-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.comparison-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.experiment-selector {
  margin-bottom: 20px;
}

.selected-experiments {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  min-height: 60px;
  padding: 12px;
  border: 2px dashed #e4e7ed;
  border-radius: 8px;
  background: #fafafa;
}

.experiment-tag {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: white;
  border: 2px solid #409eff;
  border-radius: 6px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.experiment-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.experiment-name {
  font-weight: 600;
  font-size: 14px;
}

.experiment-date {
  font-size: 12px;
  color: #666;
}

.experiment-header {
  font-weight: 600;
}

.chart-container {
  background: white;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
}

.chart-container h4 {
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 600;
}

.chart {
  height: 300px;
  width: 100%;
}

.large-chart {
  height: 400px;
}

.chart-controls {
  margin-bottom: 16px;
  display: flex;
  align-items: center;
}

.position-controls {
  margin-bottom: 16px;
  display: flex;
  align-items: center;
}

.metrics-table {
  margin-top: 20px;
}

.metrics-table h4 {
  margin-bottom: 16px;
  font-size: 16px;
  font-weight: 600;
}

.drawdown-stats {
  background: #f8f9fa;
  padding: 16px;
  border-radius: 8px;
}

.drawdown-stats h4 {
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 600;
}

.stats-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.stat-item {
  padding: 12px;
  background: white;
  border-radius: 6px;
}

.stat-header {
  font-weight: 600;
  margin-bottom: 8px;
}

.stat-metrics {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stat-row {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
}

.position-overlap {
  margin-top: 20px;
}

.position-overlap h4 {
  margin-bottom: 16px;
  font-size: 16px;
  font-weight: 600;
}

.config-comparison {
  background: white;
}

.config-table {
  margin-top: 16px;
}

.positive {
  color: #67c23a;
}

.negative {
  color: #f56c6c;
}

.warning {
  color: #e6a23c;
}

.diff {
  background: #fff7e6;
  border-radius: 2px;
  padding: 2px 4px;
}

.warning-icon {
  color: #e6a23c;
}

.success-icon {
  color: #67c23a;
}

.experiment-search {
  margin-bottom: 16px;
}
</style>