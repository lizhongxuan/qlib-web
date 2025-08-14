<template>
  <div class="qlib-strategy-diagnostic-chart">
    <div class="chart-header">
      <div class="header-left">
        <h3 class="chart-title">
          <el-icon><Odometer /></el-icon>
          策略诊断分析
        </h3>
        <p class="chart-subtitle">基于Qlib框架的策略表现深度诊断与分解分析</p>
      </div>
      <div class="header-right">
        <el-button-group>
          <el-button 
            :type="diagnosticMode === 'performance' ? 'primary' : ''" 
            @click="diagnosticMode = 'performance'"
            size="small"
          >
            表现分解
          </el-button>
          <el-button 
            :type="diagnosticMode === 'attribution' ? 'primary' : ''" 
            @click="diagnosticMode = 'attribution'"
            size="small"
          >
            归因分析
          </el-button>
          <el-button 
            :type="diagnosticMode === 'regime' ? 'primary' : ''" 
            @click="diagnosticMode = 'regime'"
            size="small"
          >
            市场状态
          </el-button>
        </el-button-group>
        <el-divider direction="vertical" />
        <el-select v-model="analysisFrequency" size="small" style="width: 100px" @change="updateChart">
          <el-option label="日频" value="daily" />
          <el-option label="周频" value="weekly" />
          <el-option label="月频" value="monthly" />
          <el-option label="季频" value="quarterly" />
        </el-select>
        <el-divider direction="vertical" />
        <el-dropdown @command="handleExport">
          <el-button size="small">
            导出 <el-icon><ArrowDown /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="png">导出图表</el-dropdown-item>
              <el-dropdown-item command="pdf">生成诊断报告</el-dropdown-item>
              <el-dropdown-item command="excel">导出数据</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>

    <div class="chart-controls">
      <div class="strategy-selector">
        <el-select 
          v-model="selectedStrategies" 
          multiple 
          filterable 
          placeholder="选择策略进行对比"
          style="width: 300px"
          @change="updateChart"
        >
          <el-option
            v-for="strategy in availableStrategies"
            :key="strategy.id"
            :label="strategy.name"
            :value="strategy.id"
          >
            <span class="strategy-option">
              <span class="strategy-name">{{ strategy.name }}</span>
              <span class="strategy-sharpe">{{ strategy.sharpe }}</span>
            </span>
          </el-option>
        </el-select>
      </div>
      
      <div class="benchmark-selector">
        <el-select v-model="benchmarkStrategy" size="small" style="width: 150px" @change="updateChart">
          <el-option label="沪深300" value="CSI300" />
          <el-option label="中证500" value="CSI500" />
          <el-option label="市场中性" value="MARKET_NEUTRAL" />
          <el-option label="风险平价" value="RISK_PARITY" />
        </el-select>
      </div>

      <div class="time-period-selector">
        <el-select v-model="timePeriod" size="small" style="width: 120px" @change="updateChart">
          <el-option label="最近1个月" value="1M" />
          <el-option label="最近3个月" value="3M" />
          <el-option label="最近6个月" value="6M" />
          <el-option label="最近1年" value="1Y" />
          <el-option label="成立以来" value="ALL" />
        </el-select>
      </div>

      <div class="diagnostic-options">
        <el-checkbox v-model="showDrawdown" @change="updateChart">显示回撤</el-checkbox>
        <el-checkbox v-model="showRollingMetrics" @change="updateChart">滚动指标</el-checkbox>
        <el-checkbox v-model="showRegimeAnalysis" @change="updateChart">市场状态</el-checkbox>
      </div>
    </div>

    <!-- 策略诊断概览 -->
    <div class="diagnostic-overview" v-if="diagnosticSummary">
      <div class="summary-cards">
        <div class="summary-card" v-for="metric in diagnosticSummary" :key="metric.name">
          <div class="metric-header">
            <div class="metric-icon" :class="metric.iconClass">
              <el-icon>
                <component :is="metric.icon" />
              </el-icon>
            </div>
            <div class="metric-info">
              <div class="metric-name">{{ metric.name }}</div>
              <div class="metric-period">{{ metric.period }}</div>
            </div>
            <div class="metric-trend" :class="metric.trendClass">
              <el-icon>
                <component :is="metric.trendIcon" />
              </el-icon>
            </div>
          </div>
          <div class="metric-values">
            <div class="primary-value" :class="metric.valueClass">{{ metric.value }}</div>
            <div class="secondary-value">{{ metric.comparison }}</div>
          </div>
          <div class="metric-details">
            <div class="detail-item" v-for="detail in metric.details" :key="detail.label">
              <span class="detail-label">{{ detail.label }}:</span>
              <span class="detail-value" :class="detail.valueClass">{{ detail.value }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="chart-container">
      <!-- 主诊断图表 -->
      <div class="main-diagnostic-section">
        <div 
          ref="mainDiagnosticContainer" 
          class="main-diagnostic-chart"
          v-loading="loading"
          element-loading-text="正在进行策略诊断分析..."
        ></div>
        
        <!-- 辅助诊断图表 -->
        <div class="auxiliary-charts">
          <div ref="drawdownChartContainer" class="drawdown-chart" v-show="showDrawdown"></div>
          <div ref="rollingMetricsContainer" class="rolling-metrics-chart" v-show="showRollingMetrics"></div>
        </div>
      </div>
    </div>

    <!-- 详细诊断分析 -->
    <div class="diagnostic-detail">
      <el-tabs v-model="activeTab">
        <el-tab-pane label="表现分解" name="performance_breakdown">
          <div class="performance-breakdown">
            <div class="breakdown-charts">
              <div ref="performanceBreakdownContainer" class="performance-breakdown-chart"></div>
              <div class="breakdown-summary">
                <h4>收益来源分解</h4>
                <div class="breakdown-components">
                  <div class="component-item" v-for="component in performanceComponents" :key="component.name">
                    <div class="component-header">
                      <span class="component-name">{{ component.name }}</span>
                      <span class="component-percentage">{{ component.percentage }}%</span>
                    </div>
                    <div class="component-details">
                      <div class="component-value" :class="getComponentClass(component.value)">
                        {{ component.value > 0 ? '+' : '' }}{{ (component.value * 100).toFixed(2) }}%
                      </div>
                      <div class="component-description">{{ component.description }}</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            <div class="performance-table">
              <el-table :data="performanceBreakdownData" size="small">
                <el-table-column prop="period" label="时期" width="120" />
                <el-table-column prop="totalReturn" label="总收益率" width="120" sortable>
                  <template #default="scope">
                    <span :class="getReturnClass(scope.row.totalReturn)">
                      {{ scope.row.totalReturn > 0 ? '+' : '' }}{{ (scope.row.totalReturn * 100).toFixed(2) }}%
                    </span>
                  </template>
                </el-table-column>
                <el-table-column prop="alphaReturn" label="Alpha收益" width="120" sortable>
                  <template #default="scope">
                    <span :class="getReturnClass(scope.row.alphaReturn)">
                      {{ scope.row.alphaReturn > 0 ? '+' : '' }}{{ (scope.row.alphaReturn * 100).toFixed(2) }}%
                    </span>
                  </template>
                </el-table-column>
                <el-table-column prop="factorReturn" label="因子收益" width="120" sortable>
                  <template #default="scope">
                    <span :class="getReturnClass(scope.row.factorReturn)">
                      {{ scope.row.factorReturn > 0 ? '+' : '' }}{{ (scope.row.factorReturn * 100).toFixed(2) }}%
                    </span>
                  </template>
                </el-table-column>
                <el-table-column prop="selectionReturn" label="选股收益" width="120" sortable>
                  <template #default="scope">
                    <span :class="getReturnClass(scope.row.selectionReturn)">
                      {{ scope.row.selectionReturn > 0 ? '+' : '' }}{{ (scope.row.selectionReturn * 100).toFixed(2) }}%
                    </span>
                  </template>
                </el-table-column>
                <el-table-column prop="timingReturn" label="择时收益" width="120" sortable>
                  <template #default="scope">
                    <span :class="getReturnClass(scope.row.timingReturn)">
                      {{ scope.row.timingReturn > 0 ? '+' : '' }}{{ (scope.row.timingReturn * 100).toFixed(2) }}%
                    </span>
                  </template>
                </el-table-column>
                <el-table-column prop="interactionReturn" label="交互收益" width="120" sortable>
                  <template #default="scope">
                    <span :class="getReturnClass(scope.row.interactionReturn)">
                      {{ scope.row.interactionReturn > 0 ? '+' : '' }}{{ (scope.row.interactionReturn * 100).toFixed(2) }}%
                    </span>
                  </template>
                </el-table-column>
                <el-table-column prop="transactionCost" label="交易成本" width="120">
                  <template #default="scope">
                    <span class="negative">
                      -{{ (Math.abs(scope.row.transactionCost) * 100).toFixed(3) }}%
                    </span>
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </div>
        </el-tab-pane>
        
        <el-tab-pane label="风格归因" name="style_attribution">
          <div class="style-attribution">
            <div class="attribution-charts">
              <div ref="styleAttributionContainer" class="style-attribution-chart"></div>
              <div ref="styleExposureContainer" class="style-exposure-chart"></div>
            </div>
            
            <div class="style-analysis-table">
              <el-table :data="styleAttributionData" size="small">
                <el-table-column prop="styleFactor" label="风格因子" width="120" />
                <el-table-column prop="exposure" label="因子暴露" width="120" sortable>
                  <template #default="scope">
                    <span :class="getExposureClass(scope.row.exposure)">
                      {{ scope.row.exposure.toFixed(3) }}
                    </span>
                  </template>
                </el-table-column>
                <el-table-column prop="factorReturn" label="因子收益率" width="120" sortable>
                  <template #default="scope">
                    <span :class="getReturnClass(scope.row.factorReturn)">
                      {{ scope.row.factorReturn > 0 ? '+' : '' }}{{ (scope.row.factorReturn * 100).toFixed(2) }}%
                    </span>
                  </template>
                </el-table-column>
                <el-table-column prop="contribution" label="贡献度" width="120" sortable>
                  <template #default="scope">
                    <span :class="getReturnClass(scope.row.contribution)">
                      {{ scope.row.contribution > 0 ? '+' : '' }}{{ (scope.row.contribution * 100).toFixed(3) }}%
                    </span>
                  </template>
                </el-table-column>
                <el-table-column prop="tStat" label="t统计量" width="100">
                  <template #default="scope">
                    <span :class="getTStatClass(scope.row.tStat)">
                      {{ scope.row.tStat.toFixed(2) }}
                    </span>
                  </template>
                </el-table-column>
                <el-table-column prop="stability" label="稳定性" width="100">
                  <template #default="scope">
                    <el-tag :type="getStabilityType(scope.row.stability)" size="small">
                      {{ scope.row.stability }}
                    </el-tag>
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </div>
        </el-tab-pane>
        
        <el-tab-pane label="市场状态分析" name="market_regime">
          <div class="market-regime-analysis">
            <div class="regime-charts">
              <div ref="regimeAnalysisContainer" class="regime-analysis-chart"></div>
              <div class="regime-summary">
                <h4>不同市场状态下的表现</h4>
                <div class="regime-performance">
                  <div class="regime-item" v-for="regime in marketRegimes" :key="regime.name">
                    <div class="regime-header">
                      <span class="regime-name">{{ regime.name }}</span>
                      <span class="regime-duration">{{ regime.duration }}天</span>
                    </div>
                    <div class="regime-metrics">
                      <div class="metric">
                        <span class="metric-label">收益率:</span>
                        <span class="metric-value" :class="getReturnClass(regime.returns)">
                          {{ regime.returns > 0 ? '+' : '' }}{{ (regime.returns * 100).toFixed(2) }}%
                        </span>
                      </div>
                      <div class="metric">
                        <span class="metric-label">胜率:</span>
                        <span class="metric-value">{{ (regime.winRate * 100).toFixed(1) }}%</span>
                      </div>
                      <div class="metric">
                        <span class="metric-label">夏普:</span>
                        <span class="metric-value" :class="getSharpeClass(regime.sharpe)">
                          {{ regime.sharpe.toFixed(2) }}
                        </span>
                      </div>
                    </div>
                    <div class="regime-description">{{ regime.description }}</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </el-tab-pane>
        
        <el-tab-pane label="优化建议" name="optimization">
          <div class="optimization-suggestions">
            <div class="suggestion-cards">
              <div class="suggestion-card" v-for="suggestion in optimizationSuggestions" :key="suggestion.id">
                <div class="suggestion-header">
                  <div class="suggestion-icon" :class="suggestion.iconClass">
                    <el-icon>
                      <component :is="suggestion.icon" />
                    </el-icon>
                  </div>
                  <div class="suggestion-info">
                    <div class="suggestion-title">{{ suggestion.title }}</div>
                    <div class="suggestion-category">{{ suggestion.category }}</div>
                  </div>
                  <div class="suggestion-priority">
                    <el-tag :type="getPriorityType(suggestion.priority)" size="small">
                      {{ suggestion.priority }}
                    </el-tag>
                  </div>
                </div>
                <div class="suggestion-content">
                  <div class="suggestion-description">{{ suggestion.description }}</div>
                  <div class="suggestion-impact" v-if="suggestion.expectedImpact">
                    <strong>预期影响:</strong> {{ suggestion.expectedImpact }}
                  </div>
                </div>
                <div class="suggestion-actions">
                  <div class="action-steps">
                    <div class="steps-title">实施步骤:</div>
                    <ol class="steps-list">
                      <li v-for="step in suggestion.steps" :key="step">{{ step }}</li>
                    </ol>
                  </div>
                </div>
                <div class="suggestion-footer">
                  <el-button size="small" @click="implementSuggestion(suggestion)">
                    实施建议
                  </el-button>
                  <el-button size="small" type="info" @click="dismissSuggestion(suggestion.id)">
                    忽略
                  </el-button>
                </div>
              </div>
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, computed, nextTick } from 'vue'
import * as echarts from 'echarts'
import { Odometer, ArrowDown, TrendCharts, DataAnalysis, Cpu, Warning, Check, ArrowUp, ArrowDown as ArrowDownIcon } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'

interface StrategyInfo {
  id: string
  name: string
  sharpe: number
  description: string
}

interface DiagnosticSummaryItem {
  name: string
  value: string
  comparison: string
  period: string
  icon: any
  iconClass?: string
  valueClass?: string
  trendIcon?: any
  trendClass?: string
  details: Array<{
    label: string
    value: string
    valueClass?: string
  }>
}

interface PerformanceComponent {
  name: string
  value: number
  percentage: number
  description: string
}

interface PerformanceBreakdownItem {
  period: string
  totalReturn: number
  alphaReturn: number
  factorReturn: number
  selectionReturn: number
  timingReturn: number
  interactionReturn: number
  transactionCost: number
}

interface StyleAttributionItem {
  styleFactor: string
  exposure: number
  factorReturn: number
  contribution: number
  tStat: number
  stability: string
}

interface MarketRegime {
  name: string
  duration: number
  returns: number
  winRate: number
  sharpe: number
  description: string
}

interface OptimizationSuggestion {
  id: string
  title: string
  category: string
  description: string
  priority: string
  expectedImpact?: string
  icon: any
  iconClass: string
  steps: string[]
}

// 响应式数据
const loading = ref(false)
const mainDiagnosticContainer = ref<HTMLElement>()
const drawdownChartContainer = ref<HTMLElement>()
const rollingMetricsContainer = ref<HTMLElement>()
const performanceBreakdownContainer = ref<HTMLElement>()
const styleAttributionContainer = ref<HTMLElement>()
const styleExposureContainer = ref<HTMLElement>()
const regimeAnalysisContainer = ref<HTMLElement>()

const mainDiagnosticChart = ref<echarts.ECharts>()
const drawdownChart = ref<echarts.ECharts>()
const rollingMetricsChart = ref<echarts.ECharts>()
const performanceBreakdownChart = ref<echarts.ECharts>()
const styleAttributionChart = ref<echarts.ECharts>()
const styleExposureChart = ref<echarts.ECharts>()
const regimeAnalysisChart = ref<echarts.ECharts>()

// 图表控制
const diagnosticMode = ref<'performance' | 'attribution' | 'regime'>('performance')
const analysisFrequency = ref('daily')
const selectedStrategies = ref<string[]>([])
const benchmarkStrategy = ref('CSI300')
const timePeriod = ref('6M')
const showDrawdown = ref(true)
const showRollingMetrics = ref(false)
const showRegimeAnalysis = ref(false)
const activeTab = ref('performance_breakdown')

// 数据
const availableStrategies = ref<StrategyInfo[]>([
  { id: 'momentum_strategy', name: '动量策略', sharpe: 1.45, description: '基于动量因子的多头策略' },
  { id: 'value_strategy', name: '价值策略', sharpe: 1.23, description: '基于价值因子的价值投资策略' },
  { id: 'growth_strategy', name: '成长策略', sharpe: 1.67, description: '基于成长因子的成长股策略' },
  { id: 'quality_strategy', name: '质量策略', sharpe: 1.34, description: '基于质量因子的优质股策略' }
])

const diagnosticSummary = ref<DiagnosticSummaryItem[]>()
const performanceComponents = ref<PerformanceComponent[]>([])
const performanceBreakdownData = ref<PerformanceBreakdownItem[]>([])
const styleAttributionData = ref<StyleAttributionItem[]>([])
const marketRegimes = ref<MarketRegime[]>([])
const optimizationSuggestions = ref<OptimizationSuggestion[]>([])

// 方法
const initCharts = async () => {
  await nextTick()
  
  if (mainDiagnosticContainer.value) {
    mainDiagnosticChart.value = echarts.init(mainDiagnosticContainer.value)
  }
  
  if (drawdownChartContainer.value) {
    drawdownChart.value = echarts.init(drawdownChartContainer.value)
  }
  
  if (rollingMetricsContainer.value) {
    rollingMetricsChart.value = echarts.init(rollingMetricsContainer.value)
  }
  
  if (performanceBreakdownContainer.value) {
    performanceBreakdownChart.value = echarts.init(performanceBreakdownContainer.value)
  }
  
  if (styleAttributionContainer.value) {
    styleAttributionChart.value = echarts.init(styleAttributionContainer.value)
  }
  
  if (styleExposureContainer.value) {
    styleExposureChart.value = echarts.init(styleExposureContainer.value)
  }
  
  if (regimeAnalysisContainer.value) {
    regimeAnalysisChart.value = echarts.init(regimeAnalysisContainer.value)
  }
  
  initAllCharts()
}

const initAllCharts = () => {
  initMainDiagnosticChart()
  initDrawdownChart()
  initRollingMetricsChart()
  initPerformanceBreakdownChart()
  initStyleAttributionChart()
  initStyleExposureChart()
  initRegimeAnalysisChart()
}

const initMainDiagnosticChart = () => {
  if (!mainDiagnosticChart.value) return
  
  const option = {
    title: {
      text: '策略表现诊断',
      left: 'center',
      textStyle: {
        fontSize: 14,
        fontWeight: 'bold'
      }
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      }
    },
    legend: {},
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: []
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        formatter: '{value}%'
      }
    },
    series: []
  }
  
  mainDiagnosticChart.value.setOption(option)
}

const initDrawdownChart = () => {
  if (!drawdownChart.value) return
  
  const option = {
    title: {
      text: '回撤分析',
      textStyle: {
        fontSize: 12
      }
    },
    tooltip: {
      trigger: 'axis'
    },
    xAxis: {
      type: 'category',
      data: []
    },
    yAxis: {
      type: 'value',
      max: 0,
      axisLabel: {
        formatter: '{value}%'
      }
    },
    series: []
  }
  
  drawdownChart.value.setOption(option)
}

const initRollingMetricsChart = () => {
  if (!rollingMetricsChart.value) return
  
  const option = {
    title: {
      text: '滚动指标',
      textStyle: {
        fontSize: 12
      }
    },
    tooltip: {
      trigger: 'axis'
    },
    legend: {},
    xAxis: {
      type: 'category',
      data: []
    },
    yAxis: [
      {
        type: 'value',
        name: '夏普比率'
      },
      {
        type: 'value',
        name: '波动率',
        axisLabel: {
          formatter: '{value}%'
        }
      }
    ],
    series: []
  }
  
  rollingMetricsChart.value.setOption(option)
}

const initPerformanceBreakdownChart = () => {
  if (!performanceBreakdownChart.value) return
  
  const option = {
    title: {
      text: '收益分解',
      textStyle: {
        fontSize: 14
      }
    },
    tooltip: {
      trigger: 'item'
    },
    series: [{
      type: 'sunburst',
      data: [],
      radius: [0, '95%'],
      label: {
        fontSize: 12
      }
    }]
  }
  
  performanceBreakdownChart.value.setOption(option)
}

const initStyleAttributionChart = () => {
  if (!styleAttributionChart.value) return
  
  const option = {
    title: {
      text: '风格因子贡献',
      textStyle: {
        fontSize: 14
      }
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'value',
      axisLabel: {
        formatter: '{value}%'
      }
    },
    yAxis: {
      type: 'category',
      data: []
    },
    series: []
  }
  
  styleAttributionChart.value.setOption(option)
}

const initStyleExposureChart = () => {
  if (!styleExposureChart.value) return
  
  const option = {
    title: {
      text: '风格暴露',
      textStyle: {
        fontSize: 14
      }
    },
    radar: {
      indicator: []
    },
    series: [{
      type: 'radar',
      data: []
    }]
  }
  
  styleExposureChart.value.setOption(option)
}

const initRegimeAnalysisChart = () => {
  if (!regimeAnalysisChart.value) return
  
  const option = {
    title: {
      text: '市场状态分析',
      textStyle: {
        fontSize: 14
      }
    },
    tooltip: {
      trigger: 'axis'
    },
    legend: {},
    xAxis: {
      type: 'category',
      data: []
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        formatter: '{value}%'
      }
    },
    series: []
  }
  
  regimeAnalysisChart.value.setOption(option)
}

const updateChart = async () => {
  if (selectedStrategies.value.length === 0) return
  
  loading.value = true
  
  try {
    await loadDiagnosticData()
    
    switch (diagnosticMode.value) {
      case 'performance':
        updatePerformanceChart()
        break
      case 'attribution':
        updateAttributionChart()
        break
      case 'regime':
        updateRegimeChart()
        break
    }
    
    if (showDrawdown.value) {
      updateDrawdownChart()
    }
    
    if (showRollingMetrics.value) {
      updateRollingMetricsChart()
    }
    
    calculateDiagnosticSummary()
    generateOptimizationSuggestions()
    
  } catch (error) {
    console.error('更新图表失败:', error)
    ElMessage.error('更新图表失败')
  } finally {
    loading.value = false
  }
}

const loadDiagnosticData = async () => {
  // 模拟从Qlib API获取诊断数据
  generateMockPerformanceData()
  generateMockStyleAttributionData()
  generateMockMarketRegimeData()
}

const generateMockPerformanceData = () => {
  // 生成表现分解数据
  performanceComponents.value = [
    { name: 'Alpha收益', value: 0.125, percentage: 45, description: '超越基准的主动收益' },
    { name: '因子收益', value: 0.089, percentage: 32, description: '因子暴露带来的收益' },
    { name: '选股收益', value: 0.034, percentage: 12, description: '个股选择带来的收益' },
    { name: '择时收益', value: 0.021, percentage: 8, description: '市场择时带来的收益' },
    { name: '交易成本', value: -0.008, percentage: -3, description: '交易摩擦成本' }
  ]
  
  // 生成时期分解数据
  const periods = ['2024Q1', '2024Q2', '2024Q3', '2024Q4']
  performanceBreakdownData.value = periods.map(period => ({
    period,
    totalReturn: Math.random() * 0.15 - 0.05,
    alphaReturn: Math.random() * 0.08 - 0.02,
    factorReturn: Math.random() * 0.06,
    selectionReturn: Math.random() * 0.04 - 0.02,
    timingReturn: Math.random() * 0.03 - 0.015,
    interactionReturn: Math.random() * 0.02 - 0.01,
    transactionCost: -(Math.random() * 0.01 + 0.002)
  }))
}

const generateMockStyleAttributionData = () => {
  const styleFactors = [
    '市值因子', '价值因子', '成长因子', '盈利因子', 
    '杠杆因子', '流动性因子', '波动率因子', '动量因子'
  ]
  
  styleAttributionData.value = styleFactors.map(factor => {
    const exposure = (Math.random() - 0.5) * 2 // -1 到 1
    const factorReturn = (Math.random() - 0.5) * 0.04 // -2% 到 2%
    const contribution = exposure * factorReturn * 0.1
    const tStat = contribution / 0.01
    
    let stability = '不稳定'
    if (Math.abs(tStat) > 2) stability = '稳定'
    else if (Math.abs(tStat) > 1.5) stability = '较稳定'
    
    return {
      styleFactor: factor,
      exposure,
      factorReturn,
      contribution,
      tStat,
      stability
    }
  })
}

const generateMockMarketRegimeData = () => {
  marketRegimes.value = [
    {
      name: '牛市上涨',
      duration: 120,
      returns: 0.185,
      winRate: 0.68,
      sharpe: 1.85,
      description: '市场趋势向上，策略表现优异'
    },
    {
      name: '震荡调整',
      duration: 89,
      returns: -0.045,
      winRate: 0.52,
      sharpe: -0.34,
      description: '市场波动较大，策略表现一般'
    },
    {
      name: '熊市下跌',
      duration: 67,
      returns: -0.123,
      winRate: 0.41,
      sharpe: -0.67,
      description: '市场下行，策略受到冲击'
    },
    {
      name: '横盘整理',
      duration: 156,
      returns: 0.023,
      winRate: 0.55,
      sharpe: 0.45,
      description: '市场平稳，策略稳定运行'
    }
  ]
}

const updatePerformanceChart = () => {
  if (!mainDiagnosticChart.value) return
  
  // 生成净值曲线数据
  const dates = []
  const strategyReturns = []
  const benchmarkReturns = []
  
  for (let i = 180; i >= 0; i--) {
    const date = new Date()
    date.setDate(date.getDate() - i)
    dates.push(date.toISOString().split('T')[0])
    
    // 模拟策略和基准净值
    const strategyReturn = 1 + (180 - i) * 0.001 + Math.sin((180 - i) / 30) * 0.05
    const benchmarkReturn = 1 + (180 - i) * 0.0005 + Math.sin((180 - i) / 40) * 0.03
    
    strategyReturns.push((strategyReturn * 100).toFixed(2))
    benchmarkReturns.push((benchmarkReturn * 100).toFixed(2))
  }
  
  mainDiagnosticChart.value.setOption({
    xAxis: {
      data: dates
    },
    series: [
      {
        name: '策略净值',
        type: 'line',
        data: strategyReturns,
        smooth: true,
        lineStyle: { width: 2, color: '#409eff' }
      },
      {
        name: '基准净值',
        type: 'line',
        data: benchmarkReturns,
        smooth: true,
        lineStyle: { width: 2, color: '#999', type: 'dashed' }
      }
    ]
  })
  
  // 更新收益分解图表
  if (performanceBreakdownChart.value) {
    const sunburstData = [
      {
        name: '总收益',
        children: performanceComponents.value.map(comp => ({
          name: comp.name,
          value: Math.abs(comp.value * 100)
        }))
      }
    ]
    
    performanceBreakdownChart.value.setOption({
      series: [{
        data: sunburstData
      }]
    })
  }
}

const updateAttributionChart = () => {
  if (!styleAttributionChart.value) return
  
  const factors = styleAttributionData.value.map(item => item.styleFactor)
  const contributions = styleAttributionData.value.map(item => (item.contribution * 100).toFixed(3))
  
  styleAttributionChart.value.setOption({
    yAxis: {
      data: factors
    },
    series: [{
      name: '贡献度',
      type: 'bar',
      data: contributions,
      itemStyle: {
        color: (params: any) => params.value >= 0 ? '#67c23a' : '#f56c6c'
      }
    }]
  })
  
  // 更新风格暴露雷达图
  if (styleExposureChart.value) {
    const indicators = styleAttributionData.value.map(item => ({
      name: item.styleFactor,
      max: 2
    }))
    
    const exposureData = styleAttributionData.value.map(item => Math.abs(item.exposure))
    
    styleExposureChart.value.setOption({
      radar: {
        indicator: indicators
      },
      series: [{
        data: [{
          value: exposureData,
          name: '因子暴露'
        }]
      }]
    })
  }
}

const updateRegimeChart = () => {
  if (!regimeAnalysisChart.value) return
  
  const regimeNames = marketRegimes.value.map(regime => regime.name)
  const regimeReturns = marketRegimes.value.map(regime => (regime.returns * 100).toFixed(2))
  const regimeSharpe = marketRegimes.value.map(regime => regime.sharpe)
  
  regimeAnalysisChart.value.setOption({
    xAxis: {
      data: regimeNames
    },
    series: [
      {
        name: '收益率',
        type: 'bar',
        data: regimeReturns,
        itemStyle: {
          color: '#409eff'
        }
      },
      {
        name: '夏普比率',
        type: 'line',
        yAxisIndex: 1,
        data: regimeSharpe,
        lineStyle: {
          color: '#e6a23c'
        }
      }
    ],
    yAxis: [
      {
        type: 'value',
        axisLabel: {
          formatter: '{value}%'
        }
      },
      {
        type: 'value',
        position: 'right'
      }
    ]
  })
}

const updateDrawdownChart = () => {
  if (!drawdownChart.value) return
  
  // 生成回撤数据
  const dates = []
  const drawdownData = []
  let peak = 1
  let current = 1
  
  for (let i = 180; i >= 0; i--) {
    const date = new Date()
    date.setDate(date.getDate() - i)
    dates.push(date.toISOString().split('T')[0])
    
    const dailyReturn = (Math.random() - 0.48) * 0.02 // 略偏正的日收益
    current *= (1 + dailyReturn)
    peak = Math.max(peak, current)
    
    const drawdown = ((current - peak) / peak * 100).toFixed(2)
    drawdownData.push(drawdown)
  }
  
  drawdownChart.value.setOption({
    xAxis: {
      data: dates
    },
    series: [{
      name: '回撤',
      type: 'line',
      data: drawdownData,
      areaStyle: {
        color: 'rgba(245, 108, 108, 0.3)'
      },
      lineStyle: {
        color: '#f56c6c'
      }
    }]
  })
}

const updateRollingMetricsChart = () => {
  if (!rollingMetricsChart.value) return
  
  // 生成滚动指标数据
  const dates = []
  const rollingSharpe = []
  const rollingVol = []
  
  for (let i = 60; i >= 0; i--) {
    const date = new Date()
    date.setDate(date.getDate() - i)
    dates.push(date.toISOString().split('T')[0])
    
    const sharpe = 1.2 + Math.sin(i / 10) * 0.3 + (Math.random() - 0.5) * 0.2
    const vol = 0.15 + Math.sin(i / 15) * 0.05 + (Math.random() - 0.5) * 0.02
    
    rollingSharpe.push(sharpe.toFixed(2))
    rollingVol.push((vol * 100).toFixed(2))
  }
  
  rollingMetricsChart.value.setOption({
    xAxis: {
      data: dates
    },
    series: [
      {
        name: '60日滚动夏普比率',
        type: 'line',
        data: rollingSharpe,
        yAxisIndex: 0,
        lineStyle: { color: '#67c23a' }
      },
      {
        name: '60日滚动波动率',
        type: 'line',
        data: rollingVol,
        yAxisIndex: 1,
        lineStyle: { color: '#e6a23c' }
      }
    ]
  })
}

const calculateDiagnosticSummary = () => {
  const totalReturn = performanceComponents.value.reduce((sum, comp) => sum + comp.value, 0)
  const avgSharpe = 1.45 // 模拟平均夏普比率
  const maxDrawdown = -0.083 // 模拟最大回撤
  const winRate = 0.585 // 模拟胜率
  
  diagnosticSummary.value = [
    {
      name: '总收益率',
      value: `${(totalReturn * 100).toFixed(2)}%`,
      comparison: `vs 基准 +${((totalReturn - 0.08) * 100).toFixed(2)}%`,
      period: '近6个月',
      icon: TrendCharts,
      iconClass: 'return-icon',
      valueClass: totalReturn > 0 ? 'positive' : 'negative',
      trendIcon: totalReturn > 0.08 ? ArrowUp : ArrowDownIcon,
      trendClass: totalReturn > 0.08 ? 'trend-up' : 'trend-down',
      details: [
        { label: 'Alpha', value: `${((totalReturn - 0.08) * 100).toFixed(2)}%`, valueClass: 'positive' },
        { label: '跟踪误差', value: '8.5%', valueClass: 'normal' }
      ]
    },
    {
      name: '夏普比率',
      value: avgSharpe.toFixed(2),
      comparison: '行业前25%',
      period: '近6个月',
      icon: DataAnalysis,
      iconClass: 'sharpe-icon',
      valueClass: avgSharpe > 1 ? 'good' : 'poor',
      trendIcon: ArrowUp,
      trendClass: 'trend-up',
      details: [
        { label: '波动率', value: '16.8%', valueClass: 'normal' },
        { label: '信息比率', value: '0.89', valueClass: 'good' }
      ]
    },
    {
      name: '最大回撤',
      value: `${(Math.abs(maxDrawdown) * 100).toFixed(1)}%`,
      comparison: '控制良好',
      period: '近6个月',
      icon: Warning,
      iconClass: 'drawdown-icon',
      valueClass: Math.abs(maxDrawdown) < 0.1 ? 'good' : 'warning',
      trendIcon: ArrowDownIcon,
      trendClass: 'trend-down',
      details: [
        { label: '回撤天数', value: '23天', valueClass: 'normal' },
        { label: '恢复时间', value: '15天', valueClass: 'good' }
      ]
    },
    {
      name: '胜率',
      value: `${(winRate * 100).toFixed(1)}%`,
      comparison: '稳定盈利',
      period: '近6个月',
      icon: Check,
      iconClass: 'winrate-icon',
      valueClass: winRate > 0.55 ? 'good' : 'normal',
      trendIcon: ArrowUp,
      trendClass: 'trend-up',
      details: [
        { label: '盈亏比', value: '1.68', valueClass: 'good' },
        { label: '平均持仓', value: '12天', valueClass: 'normal' }
      ]
    }
  ]
}

const generateOptimizationSuggestions = () => {
  optimizationSuggestions.value = [
    {
      id: 'reduce_turnover',
      title: '降低组合换手率',
      category: '交易优化',
      description: '当前策略换手率偏高(月均35%)，建议通过延长持仓周期和优化交易时机来降低交易成本。',
      priority: '高',
      expectedImpact: '预期提升年化收益1.2-1.8%',
      icon: TrendCharts,
      iconClass: 'optimization-icon',
      steps: [
        '分析高频交易的收益贡献度',
        '设置最小持仓时间限制',
        '优化交易信号的阈值参数',
        '实施交易成本控制机制'
      ]
    },
    {
      id: 'factor_diversification',
      title: '增强因子多样性',
      category: '因子优化',
      description: '当前策略过度依赖动量因子，建议增加价值、质量等其他类型因子以提高策略稳健性。',
      priority: '中',
      expectedImpact: '预期降低组合波动率15-20%',
      icon: DataAnalysis,
      iconClass: 'factor-icon',
      steps: [
        '评估现有因子的相关性',
        '筛选低相关的补充因子',
        '进行因子配权优化',
        '回测验证改进效果'
      ]
    },
    {
      id: 'risk_management',
      title: '加强风险管理',
      category: '风险控制',
      description: '在市场高波动期间策略回撤较大，建议加入动态风险管理机制。',
      priority: '高',
      expectedImpact: '预期减少最大回撤30-40%',
      icon: Warning,
      iconClass: 'risk-icon',
      steps: [
        '建立波动率预测模型',
        '设置动态仓位调整机制',
        '增加止损和止盈规则',
        '实施实时风险监控'
      ]
    }
  ]
}

const handleExport = (command: string) => {
  switch (command) {
    case 'png':
      if (mainDiagnosticChart.value) {
        const url = mainDiagnosticChart.value.getDataURL({
          pixelRatio: 2,
          backgroundColor: '#fff'
        })
        const link = document.createElement('a')
        link.download = `strategy-diagnostic-${Date.now()}.png`
        link.href = url
        link.click()
      }
      break
    case 'pdf':
    case 'excel':
      ElMessage.info('功能开发中...')
      break
  }
}

const implementSuggestion = (suggestion: OptimizationSuggestion) => {
  ElMessageBox.confirm(
    `确认实施优化建议: ${suggestion.title}？\n\n${suggestion.expectedImpact}`,
    '实施优化',
    {
      confirmButtonText: '确认',
      cancelButtonText: '取消',
      type: 'info'
    }
  ).then(() => {
    ElMessage.success('优化建议已加入实施计划')
    // 这里可以添加实际的实施逻辑
  }).catch(() => {
    // 用户取消
  })
}

const dismissSuggestion = (suggestionId: string) => {
  optimizationSuggestions.value = optimizationSuggestions.value.filter(
    suggestion => suggestion.id !== suggestionId
  )
  ElMessage.info('已忽略该建议')
}

// 辅助方法
const getComponentClass = (value: number): string => {
  return value > 0 ? 'positive' : 'negative'
}

const getReturnClass = (value: number): string => {
  return value > 0 ? 'positive' : 'negative'
}

const getExposureClass = (exposure: number): string => {
  if (Math.abs(exposure) > 1) return 'high-exposure'
  if (Math.abs(exposure) > 0.5) return 'medium-exposure'
  return 'low-exposure'
}

const getTStatClass = (tStat: number): string => {
  if (Math.abs(tStat) > 2) return 'significant'
  return 'not-significant'
}

const getStabilityType = (stability: string): string => {
  const typeMap: Record<string, string> = {
    '稳定': 'success',
    '较稳定': 'warning',
    '不稳定': 'danger'
  }
  return typeMap[stability] || 'info'
}

const getSharpeClass = (sharpe: number): string => {
  if (sharpe > 1.5) return 'excellent'
  if (sharpe > 1.0) return 'good'
  if (sharpe > 0.5) return 'fair'
  return 'poor'
}

const getPriorityType = (priority: string): string => {
  const typeMap: Record<string, string> = {
    '高': 'danger',
    '中': 'warning',
    '低': 'info'
  }
  return typeMap[priority] || 'info'
}

// 监听器
watch([diagnosticMode, analysisFrequency, selectedStrategies, benchmarkStrategy, timePeriod, showDrawdown, showRollingMetrics, showRegimeAnalysis], () => {
  if (selectedStrategies.value.length > 0) {
    updateChart()
  }
}, { deep: true })

// 生命周期
onMounted(async () => {
  await initCharts()
  
  // 默认选择第一个策略
  selectedStrategies.value = [availableStrategies.value[0]?.id || '']
  if (selectedStrategies.value[0]) {
    await updateChart()
  }
})
</script>

<style lang="scss" scoped>
.qlib-strategy-diagnostic-chart {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #f0f0f0;
}

.header-left {
  .chart-title {
    margin: 0;
    font-size: 18px;
    color: #2c3e50;
    display: flex;
    align-items: center;
    gap: 8px;
    
    .el-icon {
      color: #409eff;
    }
  }
  
  .chart-subtitle {
    margin: 5px 0 0 0;
    color: #666;
    font-size: 13px;
  }
}

.chart-controls {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 20px;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 6px;
  flex-wrap: wrap;
}

.strategy-option {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  
  .strategy-sharpe {
    color: #67c23a;
    font-weight: bold;
  }
}

.diagnostic-options {
  display: flex;
  gap: 15px;
}

.diagnostic-overview {
  margin-bottom: 20px;
}

.summary-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 15px;
}

.summary-card {
  padding: 20px;
  background: linear-gradient(135deg, #f6f8fa 0%, #e9ecef 100%);
  border-radius: 8px;
  border-left: 4px solid #409eff;
}

.metric-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 15px;
}

.metric-icon {
  .el-icon {
    font-size: 20px;
  }
  
  &.return-icon .el-icon { color: #67c23a; }
  &.sharpe-icon .el-icon { color: #409eff; }
  &.drawdown-icon .el-icon { color: #e6a23c; }
  &.winrate-icon .el-icon { color: #67c23a; }
}

.metric-info {
  flex: 1;
  margin-left: 10px;
  
  .metric-name {
    font-weight: bold;
    color: #2c3e50;
    margin-bottom: 2px;
  }
  
  .metric-period {
    font-size: 11px;
    color: #999;
  }
}

.metric-trend {
  &.trend-up { color: #67c23a; }
  &.trend-down { color: #f56c6c; }
}

.metric-values {
  margin-bottom: 10px;
  
  .primary-value {
    font-size: 24px;
    font-weight: bold;
    margin-bottom: 3px;
    
    &.positive { color: #67c23a; }
    &.negative { color: #f56c6c; }
    &.good { color: #67c23a; }
    &.poor { color: #f56c6c; }
    &.warning { color: #e6a23c; }
  }
  
  .secondary-value {
    font-size: 12px;
    color: #666;
  }
}

.metric-details {
  display: flex;
  gap: 15px;
  
  .detail-item {
    flex: 1;
    
    .detail-label {
      font-size: 11px;
      color: #666;
    }
    
    .detail-value {
      display: block;
      font-weight: bold;
      font-size: 13px;
      
      &.positive { color: #67c23a; }
      &.negative { color: #f56c6c; }
      &.good { color: #67c23a; }
      &.normal { color: #409eff; }
      &.warning { color: #e6a23c; }
    }
  }
}

.chart-container {
  .main-diagnostic-section {
    .main-diagnostic-chart {
      height: 400px;
      margin-bottom: 20px;
    }
    
    .auxiliary-charts {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 20px;
      
      .drawdown-chart,
      .rolling-metrics-chart {
        height: 250px;
      }
    }
  }
}

.diagnostic-detail {
  margin-top: 30px;
}

.performance-breakdown {
  .breakdown-charts {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
    margin-bottom: 20px;
    
    .performance-breakdown-chart {
      height: 350px;
    }
    
    .breakdown-summary {
      h4 {
        margin-top: 0;
        color: #2c3e50;
      }
    }
  }
  
  .breakdown-components {
    .component-item {
      margin-bottom: 15px;
      padding: 12px;
      background: #f8f9fa;
      border-radius: 6px;
      
      .component-header {
        display: flex;
        justify-content: space-between;
        margin-bottom: 8px;
        
        .component-name {
          font-weight: bold;
          color: #2c3e50;
        }
        
        .component-percentage {
          color: #409eff;
          font-weight: bold;
        }
      }
      
      .component-details {
        .component-value {
          font-size: 16px;
          font-weight: bold;
          margin-bottom: 3px;
          
          &.positive { color: #67c23a; }
          &.negative { color: #f56c6c; }
        }
        
        .component-description {
          font-size: 12px;
          color: #666;
        }
      }
    }
  }
  
  .performance-table {
    :deep(.el-table) {
      font-size: 12px;
    }
    
    .positive { color: #67c23a; }
    .negative { color: #f56c6c; }
  }
}

.style-attribution {
  .attribution-charts {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
    margin-bottom: 20px;
    
    .style-attribution-chart,
    .style-exposure-chart {
      height: 350px;
    }
  }
  
  .style-analysis-table {
    :deep(.el-table) {
      font-size: 12px;
    }
    
    .high-exposure { color: #f56c6c; font-weight: bold; }
    .medium-exposure { color: #e6a23c; }
    .low-exposure { color: #67c23a; }
    
    .positive { color: #67c23a; }
    .negative { color: #f56c6c; }
    
    .significant { color: #67c23a; font-weight: bold; }
    .not-significant { color: #999; }
  }
}

.market-regime-analysis {
  .regime-charts {
    display: grid;
    grid-template-columns: 2fr 1fr;
    gap: 20px;
    
    .regime-analysis-chart {
      height: 400px;
    }
    
    .regime-summary {
      h4 {
        margin-top: 0;
        color: #2c3e50;
      }
    }
  }
  
  .regime-performance {
    .regime-item {
      margin-bottom: 15px;
      padding: 12px;
      background: #f8f9fa;
      border-radius: 6px;
      
      .regime-header {
        display: flex;
        justify-content: space-between;
        margin-bottom: 8px;
        
        .regime-name {
          font-weight: bold;
          color: #2c3e50;
        }
        
        .regime-duration {
          color: #666;
          font-size: 12px;
        }
      }
      
      .regime-metrics {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 8px;
        margin-bottom: 8px;
        
        .metric {
          font-size: 12px;
          
          .metric-label {
            color: #666;
          }
          
          .metric-value {
            font-weight: bold;
            margin-left: 5px;
            
            &.positive { color: #67c23a; }
            &.negative { color: #f56c6c; }
            &.excellent { color: #67c23a; }
            &.good { color: #409eff; }
            &.fair { color: #e6a23c; }
            &.poor { color: #f56c6c; }
          }
        }
      }
      
      .regime-description {
        font-size: 11px;
        color: #666;
      }
    }
  }
}

.optimization-suggestions {
  .suggestion-cards {
    display: flex;
    flex-direction: column;
    gap: 20px;
  }
  
  .suggestion-card {
    border: 1px solid #e4e7ed;
    border-radius: 8px;
    padding: 20px;
    background: #fff;
  }
  
  .suggestion-header {
    display: flex;
    align-items: center;
    gap: 15px;
    margin-bottom: 15px;
  }
  
  .suggestion-icon {
    .el-icon {
      font-size: 24px;
      color: #409eff;
    }
    
    &.optimization-icon .el-icon { color: #409eff; }
    &.factor-icon .el-icon { color: #67c23a; }
    &.risk-icon .el-icon { color: #e6a23c; }
  }
  
  .suggestion-info {
    flex: 1;
    
    .suggestion-title {
      font-weight: bold;
      color: #2c3e50;
      margin-bottom: 3px;
    }
    
    .suggestion-category {
      font-size: 12px;
      color: #666;
    }
  }
  
  .suggestion-content {
    margin-bottom: 15px;
    
    .suggestion-description {
      color: #555;
      line-height: 1.5;
      margin-bottom: 10px;
    }
    
    .suggestion-impact {
      color: #67c23a;
      font-weight: 500;
    }
  }
  
  .suggestion-actions {
    .action-steps {
      margin-bottom: 15px;
      
      .steps-title {
        font-weight: 500;
        color: #2c3e50;
        margin-bottom: 8px;
      }
      
      .steps-list {
        margin: 0;
        padding-left: 20px;
        
        li {
          color: #555;
          margin: 5px 0;
        }
      }
    }
  }
  
  .suggestion-footer {
    display: flex;
    gap: 10px;
  }
}

@media (max-width: 768px) {
  .chart-header {
    flex-direction: column;
    gap: 15px;
  }
  
  .chart-controls {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .summary-cards {
    grid-template-columns: 1fr;
  }
  
  .auxiliary-charts {
    grid-template-columns: 1fr !important;
  }
  
  .breakdown-charts,
  .attribution-charts,
  .regime-charts {
    grid-template-columns: 1fr !important;
  }
  
  .regime-metrics {
    grid-template-columns: 1fr !important;
  }
}
</style>