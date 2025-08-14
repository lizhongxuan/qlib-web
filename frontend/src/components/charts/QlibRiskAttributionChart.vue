<template>
  <div class="qlib-risk-attribution-chart">
    <div class="chart-header">
      <div class="header-left">
        <h3 class="chart-title">
          <el-icon><Warning /></el-icon>
          风险归因分析
        </h3>
        <p class="chart-subtitle">基于Qlib模型的投资组合风险分解与归因分析</p>
      </div>
      <div class="header-right">
        <el-button-group>
          <el-button 
            :type="analysisType === 'factor' ? 'primary' : ''" 
            @click="analysisType = 'factor'"
            size="small"
          >
            因子风险
          </el-button>
          <el-button 
            :type="analysisType === 'sector' ? 'primary' : ''" 
            @click="analysisType = 'sector'"
            size="small"
          >
            行业风险
          </el-button>
          <el-button 
            :type="analysisType === 'time' ? 'primary' : ''" 
            @click="analysisType = 'time'"
            size="small"
          >
            时序风险
          </el-button>
        </el-button-group>
        <el-divider direction="vertical" />
        <el-select v-model="riskModel" size="small" style="width: 150px" @change="updateChart">
          <el-option label="Barra CNE6" value="barra_cne6" />
          <el-option label="多因子模型" value="multi_factor" />
          <el-option label="风格因子" value="style_factor" />
          <el-option label="行业因子" value="industry_factor" />
        </el-select>
        <el-divider direction="vertical" />
        <el-dropdown @command="handleExport">
          <el-button size="small">
            导出 <el-icon><ArrowDown /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="png">导出图表</el-dropdown-item>
              <el-dropdown-item command="excel">导出归因数据</el-dropdown-item>
              <el-dropdown-item command="report">生成风险报告</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>

    <div class="chart-controls">
      <div class="portfolio-selector">
        <el-select 
          v-model="selectedPortfolio" 
          placeholder="选择投资组合"
          style="width: 200px"
          @change="updateChart"
        >
          <el-option
            v-for="portfolio in availablePortfolios"
            :key="portfolio.id"
            :label="portfolio.name"
            :value="portfolio.id"
          >
            <span class="portfolio-option">
              <span class="portfolio-name">{{ portfolio.name }}</span>
              <span class="portfolio-risk">{{ portfolio.trackingError }}%</span>
            </span>
          </el-option>
        </el-select>
      </div>
      
      <div class="benchmark-selector">
        <el-select v-model="benchmarkIndex" size="small" style="width: 150px" @change="updateChart">
          <el-option label="沪深300" value="CSI300" />
          <el-option label="中证500" value="CSI500" />
          <el-option label="中证1000" value="CSI1000" />
          <el-option label="创业板指" value="ChiNext" />
        </el-select>
      </div>

      <div class="time-range-selector">
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          size="small"
          @change="updateChart"
          style="width: 240px"
        />
      </div>

      <div class="analysis-options">
        <el-checkbox v-model="showActiveRisk" @change="updateChart">显示主动风险</el-checkbox>
        <el-checkbox v-model="showSpecificRisk" @change="updateChart">显示特质风险</el-checkbox>
        <el-checkbox v-model="showTracking" @change="updateChart">显示跟踪误差</el-checkbox>
      </div>
    </div>

    <!-- 风险概览 -->
    <div class="risk-overview" v-if="riskSummary">
      <div class="risk-cards">
        <div class="risk-card" v-for="metric in riskSummary" :key="metric.label">
          <div class="risk-icon" :class="metric.iconClass">
            <el-icon>
              <component :is="metric.icon" />
            </el-icon>
          </div>
          <div class="risk-content">
            <div class="risk-label">{{ metric.label }}</div>
            <div class="risk-value" :class="metric.valueClass">{{ metric.value }}</div>
            <div class="risk-trend" :class="metric.trendClass" v-if="metric.trend">
              <el-icon>
                <component :is="metric.trendIcon" />
              </el-icon>
              <span>{{ metric.trend }}</span>
            </div>
          </div>
          <div class="risk-level">
            <el-tag :type="metric.levelType" size="small">{{ metric.level }}</el-tag>
          </div>
        </div>
      </div>
    </div>

    <div class="chart-container">
      <!-- 主要归因图表 -->
      <div class="main-chart-section">
        <div 
          ref="mainChartContainer" 
          class="main-chart"
          v-loading="loading"
          element-loading-text="正在计算风险归因..."
        ></div>
        
        <!-- 风险分解饼图 -->
        <div 
          ref="riskBreakdownContainer" 
          class="risk-breakdown-chart"
        ></div>
      </div>
      
      <!-- 时序风险图表 -->
      <div class="time-series-section" v-show="analysisType === 'time'">
        <div ref="timeSeriesChartContainer" class="time-series-chart"></div>
      </div>
    </div>

    <!-- 详细归因分析 -->
    <div class="attribution-detail">
      <el-tabs v-model="activeTab">
        <el-tab-pane label="因子归因" name="factor_attribution">
          <div class="factor-attribution">
            <div class="attribution-table">
              <el-table :data="factorAttribution" size="small" :max-height="350">
                <el-table-column prop="factorName" label="因子名称" width="150" fixed />
                <el-table-column prop="factorType" label="因子类型" width="100">
                  <template #default="scope">
                    <el-tag :type="getFactorTypeColor(scope.row.factorType)" size="small">
                      {{ scope.row.factorType }}
                    </el-tag>
                  </template>
                </el-table-column>
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
                      {{ (scope.row.factorReturn * 100).toFixed(2) }}%
                    </span>
                  </template>
                </el-table-column>
                <el-table-column prop="contribution" label="收益贡献" width="120" sortable>
                  <template #default="scope">
                    <span :class="getReturnClass(scope.row.contribution)">
                      {{ (scope.row.contribution * 100).toFixed(2) }}%
                    </span>
                  </template>
                </el-table-column>
                <el-table-column prop="riskContribution" label="风险贡献" width="120" sortable>
                  <template #default="scope">
                    <span :class="getRiskClass(scope.row.riskContribution)">
                      {{ (scope.row.riskContribution * 100).toFixed(2) }}%
                    </span>
                  </template>
                </el-table-column>
                <el-table-column prop="volatility" label="因子波动率" width="120" />
                <el-table-column prop="tStat" label="t统计量" width="100" sortable>
                  <template #default="scope">
                    <span :class="getTStatClass(scope.row.tStat)">
                      {{ scope.row.tStat.toFixed(2) }}
                    </span>
                  </template>
                </el-table-column>
                <el-table-column prop="significance" label="显著性" width="100">
                  <template #default="scope">
                    <el-tag 
                      :type="getSignificanceType(scope.row.significance)" 
                      size="small"
                    >
                      {{ scope.row.significance }}
                    </el-tag>
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </div>
        </el-tab-pane>
        
        <el-tab-pane label="行业归因" name="sector_attribution">
          <div class="sector-attribution">
            <div class="sector-chart-wrapper">
              <div ref="sectorAttributionContainer" class="sector-attribution-chart"></div>
              <div class="sector-summary">
                <h4>行业风险分解</h4>
                <div class="sector-risk-items">
                  <div class="sector-item" v-for="sector in sectorAttribution" :key="sector.name">
                    <div class="sector-header">
                      <span class="sector-name">{{ sector.name }}</span>
                      <span class="sector-weight">{{ (sector.weight * 100).toFixed(1) }}%</span>
                    </div>
                    <div class="sector-metrics">
                      <div class="metric">
                        <span class="metric-label">超配:</span>
                        <span class="metric-value" :class="getReturnClass(sector.overweight)">
                          {{ sector.overweight > 0 ? '+' : '' }}{{ (sector.overweight * 100).toFixed(1) }}%
                        </span>
                      </div>
                      <div class="metric">
                        <span class="metric-label">贡献:</span>
                        <span class="metric-value" :class="getReturnClass(sector.contribution)">
                          {{ sector.contribution > 0 ? '+' : '' }}{{ (sector.contribution * 100).toFixed(2) }}%
                        </span>
                      </div>
                      <div class="metric">
                        <span class="metric-label">风险:</span>
                        <span class="metric-value risk-value">
                          {{ (sector.riskContribution * 100).toFixed(2) }}%
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </el-tab-pane>
        
        <el-tab-pane label="特质风险" name="specific_risk">
          <div class="specific-risk-analysis">
            <div class="specific-risk-chart" ref="specificRiskContainer"></div>
            <div class="specific-risk-table">
              <el-table :data="specificRiskStocks" size="small" :max-height="300">
                <el-table-column prop="symbol" label="股票代码" width="100" />
                <el-table-column prop="name" label="股票名称" width="120" />
                <el-table-column prop="weight" label="权重%" width="100">
                  <template #default="scope">
                    {{ (scope.row.weight * 100).toFixed(2) }}%
                  </template>
                </el-table-column>
                <el-table-column prop="specificRisk" label="特质风险" width="120" sortable>
                  <template #default="scope">
                    <span :class="getRiskClass(scope.row.specificRisk)">
                      {{ (scope.row.specificRisk * 100).toFixed(2) }}%
                    </span>
                  </template>
                </el-table-column>
                <el-table-column prop="riskContribution" label="风险贡献" width="120" sortable>
                  <template #default="scope">
                    <span :class="getRiskClass(scope.row.riskContribution)">
                      {{ (scope.row.riskContribution * 100).toFixed(2) }}%
                    </span>
                  </template>
                </el-table-column>
                <el-table-column prop="residualReturn" label="超额收益" width="120" sortable>
                  <template #default="scope">
                    <span :class="getReturnClass(scope.row.residualReturn)">
                      {{ scope.row.residualReturn > 0 ? '+' : '' }}{{ (scope.row.residualReturn * 100).toFixed(2) }}%
                    </span>
                  </template>
                </el-table-column>
                <el-table-column prop="riskAdjustedReturn" label="风险调整收益" width="140" sortable>
                  <template #default="scope">
                    <span :class="getReturnClass(scope.row.riskAdjustedReturn)">
                      {{ scope.row.riskAdjustedReturn.toFixed(3) }}
                    </span>
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </div>
        </el-tab-pane>
        
        <el-tab-pane label="风险预警" name="risk_alerts">
          <div class="risk-alerts">
            <div class="alert-cards">
              <div class="alert-card" v-for="alert in riskAlerts" :key="alert.id">
                <div class="alert-header">
                  <div class="alert-icon" :class="alert.severityClass">
                    <el-icon>
                      <component :is="alert.icon" />
                    </el-icon>
                  </div>
                  <div class="alert-info">
                    <div class="alert-title">{{ alert.title }}</div>
                    <div class="alert-time">{{ alert.timestamp }}</div>
                  </div>
                  <div class="alert-severity">
                    <el-tag :type="alert.severityType" size="small">
                      {{ alert.severity }}
                    </el-tag>
                  </div>
                </div>
                <div class="alert-content">{{ alert.description }}</div>
                <div class="alert-recommendations" v-if="alert.recommendations">
                  <div class="recommendations-title">建议措施:</div>
                  <ul class="recommendations-list">
                    <li v-for="rec in alert.recommendations" :key="rec">{{ rec }}</li>
                  </ul>
                </div>
                <div class="alert-actions">
                  <el-button size="small" @click="acknowledgeAlert(alert.id)">
                    已知晓
                  </el-button>
                  <el-button size="small" type="primary" @click="handleAlert(alert)">
                    处理
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
import { Warning, ArrowDown, TrendCharts, DataAnalysis, CircleClose, InfoFilled, ArrowUp, ArrowDown as ArrowDownIcon } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'

interface PortfolioInfo {
  id: string
  name: string
  trackingError: number
  description: string
}

interface RiskSummaryItem {
  label: string
  value: string
  icon: any
  iconClass?: string
  valueClass?: string
  trend?: string
  trendClass?: string
  trendIcon?: any
  level: string
  levelType: string
}

interface FactorAttributionItem {
  factorName: string
  factorType: string
  exposure: number
  factorReturn: number
  contribution: number
  riskContribution: number
  volatility: number
  tStat: number
  significance: string
}

interface SectorAttributionItem {
  name: string
  weight: number
  benchmarkWeight: number
  overweight: number
  contribution: number
  riskContribution: number
  sectorReturn: number
}

interface SpecificRiskStock {
  symbol: string
  name: string
  weight: number
  specificRisk: number
  riskContribution: number
  residualReturn: number
  riskAdjustedReturn: number
}

interface RiskAlert {
  id: string
  title: string
  description: string
  severity: string
  severityType: string
  severityClass: string
  icon: any
  timestamp: string
  recommendations?: string[]
}

// 响应式数据
const loading = ref(false)
const mainChartContainer = ref<HTMLElement>()
const riskBreakdownContainer = ref<HTMLElement>()
const timeSeriesChartContainer = ref<HTMLElement>()
const sectorAttributionContainer = ref<HTMLElement>()
const specificRiskContainer = ref<HTMLElement>()

const mainChart = ref<echarts.ECharts>()
const riskBreakdownChart = ref<echarts.ECharts>()
const timeSeriesChart = ref<echarts.ECharts>()
const sectorAttributionChart = ref<echarts.ECharts>()
const specificRiskChart = ref<echarts.ECharts>()

// 图表控制
const analysisType = ref<'factor' | 'sector' | 'time'>('factor')
const riskModel = ref('barra_cne6')
const selectedPortfolio = ref('')
const benchmarkIndex = ref('CSI300')
const dateRange = ref<[Date, Date]>([
  new Date(Date.now() - 90 * 24 * 60 * 60 * 1000),
  new Date()
])
const showActiveRisk = ref(true)
const showSpecificRisk = ref(true)
const showTracking = ref(false)
const activeTab = ref('factor_attribution')

// 数据
const availablePortfolios = ref<PortfolioInfo[]>([
  { id: 'topk_portfolio', name: 'TopK策略组合', trackingError: 8.5, description: '基于TopK策略的投资组合' },
  { id: 'momentum_portfolio', name: '动量策略组合', trackingError: 12.3, description: '基于动量因子的投资组合' },
  { id: 'value_portfolio', name: '价值策略组合', trackingError: 6.8, description: '基于价值因子的投资组合' }
])

const riskSummary = ref<RiskSummaryItem[]>()
const factorAttribution = ref<FactorAttributionItem[]>([])
const sectorAttribution = ref<SectorAttributionItem[]>([])
const specificRiskStocks = ref<SpecificRiskStock[]>([])
const riskAlerts = ref<RiskAlert[]>([])

// 方法
const initCharts = async () => {
  await nextTick()
  
  if (mainChartContainer.value) {
    mainChart.value = echarts.init(mainChartContainer.value)
  }
  
  if (riskBreakdownContainer.value) {
    riskBreakdownChart.value = echarts.init(riskBreakdownContainer.value)
  }
  
  if (timeSeriesChartContainer.value) {
    timeSeriesChart.value = echarts.init(timeSeriesChartContainer.value)
  }
  
  if (sectorAttributionContainer.value) {
    sectorAttributionChart.value = echarts.init(sectorAttributionContainer.value)
  }
  
  if (specificRiskContainer.value) {
    specificRiskChart.value = echarts.init(specificRiskContainer.value)
  }
  
  initMainChart()
  initRiskBreakdownChart()
  initTimeSeriesChart()
  initSectorAttributionChart()
  initSpecificRiskChart()
}

const initMainChart = () => {
  if (!mainChart.value) return
  
  const option = {
    title: {
      text: '风险归因分析',
      left: 'center',
      textStyle: {
        fontSize: 14,
        fontWeight: 'bold'
      }
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
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
  
  mainChart.value.setOption(option)
}

const initRiskBreakdownChart = () => {
  if (!riskBreakdownChart.value) return
  
  const option = {
    title: {
      text: '风险分解',
      textStyle: {
        fontSize: 14
      }
    },
    tooltip: {
      trigger: 'item',
      formatter: '{a} <br/>{b}: {c}% ({d}%)'
    },
    legend: {
      orient: 'horizontal',
      bottom: 10
    },
    series: [{
      name: '风险分解',
      type: 'pie',
      radius: ['30%', '70%'],
      avoidLabelOverlap: false,
      itemStyle: {
        borderRadius: 10,
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
          fontSize: 16,
          fontWeight: 'bold'
        }
      },
      labelLine: {
        show: false
      },
      data: []
    }]
  }
  
  riskBreakdownChart.value.setOption(option)
}

const initTimeSeriesChart = () => {
  if (!timeSeriesChart.value) return
  
  const option = {
    title: {
      text: '风险时序分析',
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
  
  timeSeriesChart.value.setOption(option)
}

const initSectorAttributionChart = () => {
  if (!sectorAttributionChart.value) return
  
  const option = {
    title: {
      text: '行业归因',
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
    legend: {},
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
  
  sectorAttributionChart.value.setOption(option)
}

const initSpecificRiskChart = () => {
  if (!specificRiskChart.value) return
  
  const option = {
    title: {
      text: '特质风险散点图',
      textStyle: {
        fontSize: 14
      }
    },
    tooltip: {
      trigger: 'item'
    },
    xAxis: {
      type: 'value',
      name: '权重%'
    },
    yAxis: {
      type: 'value',
      name: '特质风险%'
    },
    series: [{
      type: 'scatter',
      symbolSize: (data: number[]) => Math.sqrt(data[2]) * 5,
      data: []
    }]
  }
  
  specificRiskChart.value.setOption(option)
}

const updateChart = async () => {
  if (!selectedPortfolio.value) return
  
  loading.value = true
  
  try {
    await loadRiskData()
    
    switch (analysisType.value) {
      case 'factor':
        updateFactorChart()
        break
      case 'sector':
        updateSectorChart()
        break
      case 'time':
        updateTimeSeriesChart()
        break
    }
    
    updateRiskBreakdownChart()
    calculateRiskSummary()
    generateRiskAlerts()
    
  } catch (error) {
    console.error('更新图表失败:', error)
    ElMessage.error('更新图表失败')
  } finally {
    loading.value = false
  }
}

const loadRiskData = async () => {
  // 模拟从Qlib API获取风险归因数据
  generateMockFactorAttribution()
  generateMockSectorAttribution()
  generateMockSpecificRiskData()
}

const generateMockFactorAttribution = () => {
  const factors = [
    { name: '市值因子', type: '风格', weight: 0.25 },
    { name: '价值因子', type: '风格', weight: 0.20 },
    { name: '盈利因子', type: '风格', weight: 0.18 },
    { name: '成长因子', type: '风格', weight: 0.15 },
    { name: '杠杆因子', type: '风格', weight: 0.12 },
    { name: '流动性因子', type: '风格', weight: 0.10 }
  ]
  
  factorAttribution.value = factors.map(factor => {
    const exposure = (Math.random() - 0.5) * 2 // -1 到 1 之间
    const factorReturn = (Math.random() - 0.5) * 0.04 // -2% 到 2% 之间
    const contribution = exposure * factorReturn * factor.weight
    const riskContribution = Math.abs(exposure) * factor.weight * 0.1
    const volatility = Math.random() * 0.3 + 0.1 // 10% 到 40% 之间
    const tStat = contribution / (volatility / Math.sqrt(252))
    
    let significance = '不显著'
    if (Math.abs(tStat) > 2.58) significance = '高度显著'
    else if (Math.abs(tStat) > 1.96) significance = '显著'
    else if (Math.abs(tStat) > 1.64) significance = '弱显著'
    
    return {
      factorName: factor.name,
      factorType: factor.type,
      exposure,
      factorReturn,
      contribution,
      riskContribution,
      volatility,
      tStat,
      significance
    }
  })
}

const generateMockSectorAttribution = () => {
  const sectors = [
    { name: '金融', portfolioWeight: 0.25, benchmarkWeight: 0.30 },
    { name: '科技', portfolioWeight: 0.20, benchmarkWeight: 0.15 },
    { name: '医药', portfolioWeight: 0.15, benchmarkWeight: 0.12 },
    { name: '制造', portfolioWeight: 0.18, benchmarkWeight: 0.20 },
    { name: '消费', portfolioWeight: 0.12, benchmarkWeight: 0.13 },
    { name: '其他', portfolioWeight: 0.10, benchmarkWeight: 0.10 }
  ]
  
  sectorAttribution.value = sectors.map(sector => {
    const overweight = sector.portfolioWeight - sector.benchmarkWeight
    const sectorReturn = (Math.random() - 0.5) * 0.06 // -3% 到 3% 之间
    const contribution = overweight * sectorReturn
    const riskContribution = Math.abs(overweight) * 0.15 // 简化风险贡献计算
    
    return {
      name: sector.name,
      weight: sector.portfolioWeight,
      benchmarkWeight: sector.benchmarkWeight,
      overweight,
      contribution,
      riskContribution,
      sectorReturn
    }
  })
}

const generateMockSpecificRiskData = () => {
  const stocks = [
    '000001.XSHE', '000002.XSHE', '600000.XSHG', '600036.XSHG',
    '000858.XSHE', '600519.XSHG', '002415.XSHE', '300059.XSHE'
  ]
  
  specificRiskStocks.value = stocks.map((symbol, index) => {
    const weight = Math.random() * 0.08 + 0.01 // 1% 到 9% 之间
    const specificRisk = Math.random() * 0.4 + 0.1 // 10% 到 50% 之间
    const riskContribution = weight * specificRisk * 0.5
    const residualReturn = (Math.random() - 0.5) * 0.08 // -4% 到 4% 之间
    const riskAdjustedReturn = residualReturn / specificRisk
    
    return {
      symbol,
      name: `股票${index + 1}`,
      weight,
      specificRisk,
      riskContribution,
      residualReturn,
      riskAdjustedReturn
    }
  })
}

const updateFactorChart = () => {
  if (!mainChart.value) return
  
  const categories = factorAttribution.value.map(item => item.factorName)
  const contributions = factorAttribution.value.map(item => (item.contribution * 100).toFixed(3))
  const riskContributions = factorAttribution.value.map(item => (item.riskContribution * 100).toFixed(3))
  
  mainChart.value.setOption({
    xAxis: {
      data: categories
    },
    series: [
      {
        name: '收益贡献',
        type: 'bar',
        data: contributions,
        itemStyle: {
          color: '#67c23a'
        }
      },
      {
        name: '风险贡献',
        type: 'bar',
        data: riskContributions,
        itemStyle: {
          color: '#f56c6c'
        }
      }
    ]
  })
}

const updateSectorChart = () => {
  if (!sectorAttributionChart.value) return
  
  const sectors = sectorAttribution.value.map(item => item.name)
  const contributions = sectorAttribution.value.map(item => (item.contribution * 100).toFixed(3))
  const riskContributions = sectorAttribution.value.map(item => (item.riskContribution * 100).toFixed(3))
  
  sectorAttributionChart.value.setOption({
    yAxis: {
      data: sectors
    },
    series: [
      {
        name: '收益贡献',
        type: 'bar',
        data: contributions,
        itemStyle: {
          color: '#409eff'
        }
      },
      {
        name: '风险贡献',
        type: 'bar',
        data: riskContributions,
        itemStyle: {
          color: '#e6a23c'
        }
      }
    ]
  })
}

const updateTimeSeriesChart = () => {
  if (!timeSeriesChart.value) return
  
  // 生成时序数据
  const dates = []
  const totalRisk = []
  const factorRisk = []
  const specificRisk = []
  
  for (let i = 30; i >= 0; i--) {
    const date = new Date()
    date.setDate(date.getDate() - i)
    dates.push(date.toISOString().split('T')[0])
    
    const total = Math.random() * 0.05 + 0.15 // 15% 到 20% 之间
    const factor = total * (0.6 + Math.random() * 0.2) // 60%-80% 为因子风险
    const specific = total - factor
    
    totalRisk.push((total * 100).toFixed(2))
    factorRisk.push((factor * 100).toFixed(2))
    specificRisk.push((specific * 100).toFixed(2))
  }
  
  timeSeriesChart.value.setOption({
    xAxis: {
      data: dates
    },
    series: [
      {
        name: '总风险',
        type: 'line',
        data: totalRisk,
        smooth: true,
        lineStyle: { width: 2, color: '#f56c6c' }
      },
      {
        name: '因子风险',
        type: 'line',
        data: factorRisk,
        smooth: true,
        lineStyle: { width: 2, color: '#409eff' }
      },
      {
        name: '特质风险',
        type: 'line',
        data: specificRisk,
        smooth: true,
        lineStyle: { width: 2, color: '#67c23a' }
      }
    ]
  })
}

const updateRiskBreakdownChart = () => {
  if (!riskBreakdownChart.value) return
  
  const factorRiskTotal = factorAttribution.value.reduce((sum, item) => sum + item.riskContribution, 0)
  const specificRiskTotal = specificRiskStocks.value.reduce((sum, item) => sum + item.riskContribution, 0)
  const otherRisk = 0.05 // 其他风险
  
  const data = [
    { name: '因子风险', value: (factorRiskTotal * 100).toFixed(2) },
    { name: '特质风险', value: (specificRiskTotal * 100).toFixed(2) },
    { name: '其他风险', value: (otherRisk * 100).toFixed(2) }
  ]
  
  riskBreakdownChart.value.setOption({
    series: [{
      data: data
    }]
  })
  
  // 更新特质风险散点图
  if (specificRiskChart.value) {
    const scatterData = specificRiskStocks.value.map(stock => [
      stock.weight * 100,
      stock.specificRisk * 100,
      stock.riskContribution * 1000 // 用于控制点大小
    ])
    
    specificRiskChart.value.setOption({
      series: [{
        data: scatterData
      }]
    })
  }
}

const calculateRiskSummary = () => {
  const totalRisk = factorAttribution.value.reduce((sum, item) => sum + item.riskContribution, 0) +
                   specificRiskStocks.value.reduce((sum, item) => sum + item.riskContribution, 0)
  
  const factorRisk = factorAttribution.value.reduce((sum, item) => sum + item.riskContribution, 0)
  const specificRisk = specificRiskStocks.value.reduce((sum, item) => sum + item.riskContribution, 0)
  const trackingError = Math.sqrt(totalRisk) * Math.sqrt(252) // 年化跟踪误差
  
  // 计算风险集中度
  const riskConcentration = Math.max(...factorAttribution.value.map(item => item.riskContribution)) / totalRisk
  
  riskSummary.value = [
    {
      label: '总风险',
      value: `${(Math.sqrt(totalRisk) * 100).toFixed(2)}%`,
      icon: Warning,
      iconClass: 'risk-icon',
      valueClass: totalRisk > 0.04 ? 'high-risk' : totalRisk > 0.02 ? 'medium-risk' : 'low-risk',
      trend: '+0.3%',
      trendClass: 'trend-up',
      trendIcon: ArrowUp,
      level: totalRisk > 0.04 ? '高' : totalRisk > 0.02 ? '中' : '低',
      levelType: totalRisk > 0.04 ? 'danger' : totalRisk > 0.02 ? 'warning' : 'success'
    },
    {
      label: '因子风险',
      value: `${(Math.sqrt(factorRisk) * 100).toFixed(2)}%`,
      icon: TrendCharts,
      valueClass: 'factor-risk',
      level: '中等',
      levelType: 'warning'
    },
    {
      label: '特质风险',
      value: `${(Math.sqrt(specificRisk) * 100).toFixed(2)}%`,
      icon: DataAnalysis,
      valueClass: 'specific-risk',
      level: '可控',
      levelType: 'success'
    },
    {
      label: '跟踪误差',
      value: `${(trackingError * 100).toFixed(2)}%`,
      icon: TrendCharts,
      valueClass: trackingError > 0.1 ? 'high-tracking' : 'normal-tracking',
      trend: '-0.1%',
      trendClass: 'trend-down',
      trendIcon: ArrowDownIcon,
      level: trackingError > 0.1 ? '偏高' : '正常',
      levelType: trackingError > 0.1 ? 'warning' : 'success'
    }
  ]
}

const generateRiskAlerts = () => {
  const alerts: RiskAlert[] = []
  
  // 检查风险集中度
  const maxFactorRisk = Math.max(...factorAttribution.value.map(item => item.riskContribution))
  if (maxFactorRisk > 0.3) {
    alerts.push({
      id: 'factor_concentration',
      title: '因子风险集中度过高',
      description: '单一因子风险贡献超过30%，可能导致投资组合风险过于集中',
      severity: '高风险',
      severityType: 'danger',
      severityClass: 'danger-alert',
      icon: Warning,
      timestamp: new Date().toLocaleString(),
      recommendations: [
        '考虑降低主导因子的权重',
        '增加其他类型因子的配置',
        '进行因子对冲以降低集中风险'
      ]
    })
  }
  
  // 检查行业集中度
  const maxSectorWeight = Math.max(...sectorAttribution.value.map(item => Math.abs(item.overweight)))
  if (maxSectorWeight > 0.1) {
    alerts.push({
      id: 'sector_concentration',
      title: '行业配置偏离过大',
      description: '某行业权重偏离基准超过10%，存在行业集中风险',
      severity: '中风险',
      severityType: 'warning',
      severityClass: 'warning-alert',
      icon: InfoFilled,
      timestamp: new Date().toLocaleString(),
      recommendations: [
        '平衡行业配置权重',
        '考虑行业轮动策略',
        '加强行业风险监控'
      ]
    })
  }
  
  // 检查特质风险
  const maxSpecificRisk = Math.max(...specificRiskStocks.value.map(item => item.specificRisk))
  if (maxSpecificRisk > 0.4) {
    alerts.push({
      id: 'specific_risk',
      title: '个股特质风险偏高',
      description: '部分个股特质风险超过40%，可能影响组合稳定性',
      severity: '中风险',
      severityType: 'warning',
      severityClass: 'warning-alert',
      icon: CircleClose,
      timestamp: new Date().toLocaleString(),
      recommendations: [
        '降低高风险个股权重',
        '增加持股分散化',
        '加强个股基本面分析'
      ]
    })
  }
  
  riskAlerts.value = alerts
}

const handleExport = (command: string) => {
  switch (command) {
    case 'png':
      if (mainChart.value) {
        const url = mainChart.value.getDataURL({
          pixelRatio: 2,
          backgroundColor: '#fff'
        })
        const link = document.createElement('a')
        link.download = `risk-attribution-${Date.now()}.png`
        link.href = url
        link.click()
      }
      break
    case 'excel':
    case 'report':
      ElMessage.info('功能开发中...')
      break
  }
}

const acknowledgeAlert = (alertId: string) => {
  riskAlerts.value = riskAlerts.value.filter(alert => alert.id !== alertId)
  ElMessage.success('已确认风险预警')
}

const handleAlert = (alert: RiskAlert) => {
  ElMessageBox.confirm(
    `确认处理风险预警: ${alert.title}？`,
    '风险处理',
    {
      confirmButtonText: '确认',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(() => {
    acknowledgeAlert(alert.id)
    ElMessage.success('风险预警已处理')
  }).catch(() => {
    // 用户取消
  })
}

// 辅助方法
const getFactorTypeColor = (type: string): string => {
  const colorMap: Record<string, string> = {
    '风格': 'primary',
    '行业': 'success',
    '国家': 'warning'
  }
  return colorMap[type] || 'info'
}

const getExposureClass = (exposure: number): string => {
  if (Math.abs(exposure) > 1) return 'high-exposure'
  if (Math.abs(exposure) > 0.5) return 'medium-exposure'
  return 'low-exposure'
}

const getReturnClass = (value: number): string => {
  return value > 0 ? 'positive' : 'negative'
}

const getRiskClass = (value: number): string => {
  if (value > 0.2) return 'high-risk'
  if (value > 0.1) return 'medium-risk'
  return 'low-risk'
}

const getTStatClass = (tStat: number): string => {
  if (Math.abs(tStat) > 2) return 'significant'
  if (Math.abs(tStat) > 1.64) return 'marginally-significant'
  return 'not-significant'
}

const getSignificanceType = (significance: string): string => {
  const typeMap: Record<string, string> = {
    '高度显著': 'success',
    '显著': 'success',
    '弱显著': 'warning',
    '不显著': 'info'
  }
  return typeMap[significance] || 'info'
}

// 监听器
watch([analysisType, riskModel, selectedPortfolio, benchmarkIndex, dateRange, showActiveRisk, showSpecificRisk, showTracking], () => {
  if (selectedPortfolio.value) {
    updateChart()
  }
}, { deep: true })

// 生命周期
onMounted(async () => {
  await initCharts()
  
  // 默认选择第一个投资组合
  selectedPortfolio.value = availablePortfolios.value[0]?.id || ''
  if (selectedPortfolio.value) {
    await updateChart()
  }
})
</script>

<style lang="scss" scoped>
.qlib-risk-attribution-chart {
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
      color: #e6a23c;
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

.portfolio-option {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  
  .portfolio-risk {
    color: #e6a23c;
    font-weight: bold;
  }
}

.analysis-options {
  display: flex;
  gap: 15px;
}

.risk-overview {
  margin-bottom: 20px;
}

.risk-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 15px;
}

.risk-card {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 15px;
  background: linear-gradient(135deg, #fff5f5 0%, #fffbf0 100%);
  border-radius: 8px;
  border-left: 4px solid #e6a23c;
  position: relative;
}

.risk-icon {
  .el-icon {
    font-size: 24px;
    color: #e6a23c;
  }
  
  &.risk-icon .el-icon {
    color: #f56c6c;
  }
}

.risk-content {
  flex: 1;
  
  .risk-label {
    font-size: 12px;
    color: #666;
    margin-bottom: 3px;
  }
  
  .risk-value {
    font-size: 16px;
    font-weight: bold;
    margin-bottom: 3px;
    
    &.high-risk, &.high-tracking { color: #f56c6c; }
    &.medium-risk, &.factor-risk { color: #e6a23c; }
    &.low-risk, &.specific-risk, &.normal-tracking { color: #67c23a; }
  }
  
  .risk-trend {
    font-size: 11px;
    display: flex;
    align-items: center;
    gap: 3px;
    
    &.trend-up { color: #f56c6c; }
    &.trend-down { color: #67c23a; }
  }
}

.risk-level {
  position: absolute;
  top: 10px;
  right: 10px;
}

.chart-container {
  .main-chart-section {
    display: grid;
    grid-template-columns: 2fr 1fr;
    gap: 20px;
    margin-bottom: 20px;
    
    .main-chart {
      height: 400px;
    }
    
    .risk-breakdown-chart {
      height: 400px;
    }
  }
  
  .time-series-section {
    .time-series-chart {
      height: 300px;
      margin-top: 20px;
    }
  }
}

.attribution-detail {
  margin-top: 30px;
}

.factor-attribution {
  .attribution-table {
    :deep(.el-table) {
      font-size: 12px;
    }
    
    .high-exposure { color: #f56c6c; font-weight: bold; }
    .medium-exposure { color: #e6a23c; }
    .low-exposure { color: #67c23a; }
    
    .positive { color: #67c23a; }
    .negative { color: #f56c6c; }
    
    .high-risk { color: #f56c6c; font-weight: bold; }
    .medium-risk { color: #e6a23c; }
    .low-risk { color: #67c23a; }
    
    .significant { color: #67c23a; font-weight: bold; }
    .marginally-significant { color: #e6a23c; }
    .not-significant { color: #999; }
  }
}

.sector-attribution {
  .sector-chart-wrapper {
    display: grid;
    grid-template-columns: 2fr 1fr;
    gap: 20px;
    
    .sector-attribution-chart {
      height: 400px;
    }
    
    .sector-summary {
      h4 {
        margin-top: 0;
        color: #2c3e50;
      }
    }
  }
  
  .sector-risk-items {
    .sector-item {
      margin-bottom: 15px;
      padding: 12px;
      background: #f8f9fa;
      border-radius: 6px;
      
      &:last-child {
        margin-bottom: 0;
      }
    }
    
    .sector-header {
      display: flex;
      justify-content: space-between;
      margin-bottom: 8px;
      
      .sector-name {
        font-weight: bold;
        color: #2c3e50;
      }
      
      .sector-weight {
        color: #409eff;
        font-weight: bold;
      }
    }
    
    .sector-metrics {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 10px;
      
      .metric {
        display: flex;
        justify-content: space-between;
        font-size: 12px;
        
        .metric-label {
          color: #666;
        }
        
        .metric-value {
          font-weight: bold;
          
          &.positive { color: #67c23a; }
          &.negative { color: #f56c6c; }
          &.risk-value { color: #e6a23c; }
        }
      }
    }
  }
}

.specific-risk-analysis {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  
  .specific-risk-chart {
    height: 300px;
  }
  
  .specific-risk-table {
    :deep(.el-table) {
      font-size: 12px;
    }
  }
}

.risk-alerts {
  .alert-cards {
    display: flex;
    flex-direction: column;
    gap: 15px;
  }
  
  .alert-card {
    border: 1px solid #e4e7ed;
    border-radius: 8px;
    padding: 15px;
    background: #fff;
    
    &.danger-alert {
      border-left: 4px solid #f56c6c;
      background: linear-gradient(135deg, #fff5f5 0%, #ffffff 100%);
    }
    
    &.warning-alert {
      border-left: 4px solid #e6a23c;
      background: linear-gradient(135deg, #fffbf0 0%, #ffffff 100%);
    }
  }
  
  .alert-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 10px;
    
    .alert-icon {
      &.danger-alert .el-icon { color: #f56c6c; }
      &.warning-alert .el-icon { color: #e6a23c; }
    }
    
    .alert-info {
      flex: 1;
      
      .alert-title {
        font-weight: bold;
        color: #2c3e50;
        margin-bottom: 2px;
      }
      
      .alert-time {
        font-size: 11px;
        color: #999;
      }
    }
  }
  
  .alert-content {
    color: #555;
    line-height: 1.5;
    margin-bottom: 10px;
  }
  
  .alert-recommendations {
    margin-bottom: 15px;
    
    .recommendations-title {
      font-weight: 500;
      color: #2c3e50;
      margin-bottom: 8px;
    }
    
    .recommendations-list {
      margin: 0;
      padding-left: 20px;
      
      li {
        color: #555;
        margin: 5px 0;
        font-size: 13px;
      }
    }
  }
  
  .alert-actions {
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
  
  .risk-cards {
    grid-template-columns: 1fr;
  }
  
  .main-chart-section {
    grid-template-columns: 1fr !important;
  }
  
  .sector-chart-wrapper,
  .specific-risk-analysis {
    grid-template-columns: 1fr !important;
  }
}
</style>