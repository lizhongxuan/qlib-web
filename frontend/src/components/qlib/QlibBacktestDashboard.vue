<template>
  <div class="qlib-backtest-dashboard">
    <!-- 仪表盘头部 -->
    <el-card class="dashboard-header">
      <template #header>
        <div class="header-content">
          <div class="header-title">
            <el-icon><TrendCharts /></el-icon>
            <span>Qlib专业回测分析仪表盘</span>
          </div>
          <div class="header-actions">
            <el-button @click="refreshDashboard" :loading="loading">
              <el-icon><Refresh /></el-icon>
              刷新数据
            </el-button>
            <el-button @click="exportReport">
              <el-icon><Document /></el-icon>
              导出报告
            </el-button>
            <el-button type="primary" @click="createNewBacktest">
              <el-icon><Plus /></el-icon>
              新建回测
            </el-button>
          </div>
        </div>
      </template>

      <!-- 策略选择器 -->
      <div class="strategy-selector">
        <el-row :gutter="16">
          <el-col :span="8">
            <el-form-item label="选择策略">
              <el-select 
                v-model="selectedStrategy" 
                placeholder="请选择回测策略"
                @change="loadBacktestResults"
              >
                <el-option
                  v-for="strategy in availableStrategies"
                  :key="strategy.id"
                  :label="strategy.name"
                  :value="strategy.id"
                >
                  <div class="strategy-option">
                    <span>{{ strategy.name }}</span>
                    <el-tag size="small" :type="getPerformanceTagType(strategy.performance)">
                      {{ strategy.performance }}
                    </el-tag>
                  </div>
                </el-option>
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="时间范围">
              <el-date-picker
                v-model="timeRange"
                type="daterange"
                start-placeholder="开始日期"
                end-placeholder="结束日期"
                format="YYYY-MM-DD"
                value-format="YYYY-MM-DD"
                @change="loadBacktestResults"
              />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="基准对比">
              <el-select v-model="selectedBenchmark" @change="loadBacktestResults">
                <el-option label="沪深300" value="CSI300" />
                <el-option label="中证500" value="CSI500" />
                <el-option label="上证50" value="SSE50" />
                <el-option label="创业板指" value="ChiNext" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
      </div>
    </el-card>

    <!-- 核心性能指标 -->
    <el-row :gutter="16" class="performance-overview">
      <el-col :span="6">
        <el-card class="metric-card annual-return">
          <el-statistic 
            title="年化收益率" 
            :value="backtestMetrics.annualReturn" 
            suffix="%" 
            :precision="2"
          />
          <div class="metric-comparison">
            <span class="comparison-text">vs 基准: </span>
            <span :class="['comparison-value', backtestMetrics.excessReturn >= 0 ? 'positive' : 'negative']">
              {{ backtestMetrics.excessReturn >= 0 ? '+' : '' }}{{ backtestMetrics.excessReturn.toFixed(2) }}%
            </span>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="metric-card sharpe-ratio">
          <el-statistic 
            title="夏普比率" 
            :value="backtestMetrics.sharpeRatio" 
            :precision="3"
          />
          <div class="metric-rating">
            <el-rate 
              v-model="sharpeRating" 
              disabled 
              :max="5"
              :colors="['#ff6b6b', '#feca57', '#48dbfb', '#0be881', '#5f27cd']"
            />
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="metric-card max-drawdown">
          <el-statistic 
            title="最大回撤" 
            :value="backtestMetrics.maxDrawdown" 
            suffix="%" 
            :precision="2"
          />
          <div class="drawdown-indicator">
            <el-progress 
              :percentage="Math.abs(backtestMetrics.maxDrawdown)"
              :color="getDrawdownColor(backtestMetrics.maxDrawdown)"
              :show-text="false"
              :stroke-width="8"
            />
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="metric-card win-rate">
          <el-statistic 
            title="胜率" 
            :value="backtestMetrics.winRate" 
            suffix="%" 
            :precision="1"
          />
          <div class="win-rate-chart">
            <el-progress 
              type="circle" 
              :percentage="backtestMetrics.winRate"
              :width="60"
              :stroke-width="6"
            />
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 详细分析图表 -->
    <el-row :gutter="16" class="charts-section">
      <!-- 净值曲线 -->
      <el-col :span="16">
        <el-card class="chart-card">
          <template #header>
            <div class="chart-header">
              <span>净值曲线对比</span>
              <div class="chart-controls">
                <el-radio-group v-model="chartTimeframe" size="small">
                  <el-radio-button label="1M">1个月</el-radio-button>
                  <el-radio-button label="3M">3个月</el-radio-button>
                  <el-radio-button label="6M">6个月</el-radio-button>
                  <el-radio-button label="1Y">1年</el-radio-button>
                  <el-radio-button label="ALL">全部</el-radio-button>
                </el-radio-group>
              </div>
            </div>
          </template>
          <div class="chart-container" ref="netValueChartRef">
            <div class="chart-placeholder">净值曲线图表区域</div>
          </div>
        </el-card>
      </el-col>

      <!-- 回撤分析 -->
      <el-col :span="8">
        <el-card class="chart-card">
          <template #header>
            <span>回撤分析</span>
          </template>
          <div class="chart-container" ref="drawdownChartRef">
            <div class="chart-placeholder">回撤分析图表</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" class="charts-section">
      <!-- 收益分布 -->
      <el-col :span="12">
        <el-card class="chart-card">
          <template #header>
            <span>月度收益分布</span>
          </template>
          <div class="chart-container" ref="returnDistributionRef">
            <div class="chart-placeholder">收益分布直方图</div>
          </div>
        </el-card>
      </el-col>

      <!-- 滚动指标 -->
      <el-col :span="12">
        <el-card class="chart-card">
          <template #header>
            <div class="chart-header">
              <span>滚动指标分析</span>
              <el-select v-model="rollingMetric" size="small" style="width: 120px">
                <el-option label="夏普比率" value="sharpe" />
                <el-option label="波动率" value="volatility" />
                <el-option label="Beta值" value="beta" />
                <el-option label="Alpha值" value="alpha" />
              </el-select>
            </div>
          </template>
          <div class="chart-container" ref="rollingMetricsRef">
            <div class="chart-placeholder">滚动指标图表</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 持仓分析 -->
    <el-row :gutter="16" class="position-section">
      <el-col :span="12">
        <el-card class="position-card">
          <template #header>
            <span>当前持仓分析</span>
          </template>
          <div class="position-overview">
            <div class="position-stats">
              <div class="stat-item">
                <span class="stat-label">持仓数量</span>
                <span class="stat-value">{{ positionData.totalPositions }}</span>
              </div>
              <div class="stat-item">
                <span class="stat-label">持仓市值</span>
                <span class="stat-value">¥{{ (positionData.totalValue / 10000).toFixed(1) }}万</span>
              </div>
              <div class="stat-item">
                <span class="stat-label">现金比例</span>
                <span class="stat-value">{{ positionData.cashRatio.toFixed(1) }}%</span>
              </div>
            </div>

            <div class="top-holdings">
              <h4>前十大持仓</h4>
              <el-table :data="positionData.topHoldings" size="small">
                <el-table-column prop="symbol" label="股票代码" width="100" />
                <el-table-column prop="name" label="股票名称" width="120" />
                <el-table-column prop="weight" label="权重" width="80">
                  <template #default="{ row }">
                    {{ row.weight.toFixed(2) }}%
                  </template>
                </el-table-column>
                <el-table-column prop="return" label="收益率" width="80">
                  <template #default="{ row }">
                    <span :class="[row.return >= 0 ? 'positive' : 'negative']">
                      {{ row.return >= 0 ? '+' : '' }}{{ row.return.toFixed(2) }}%
                    </span>
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card class="position-card">
          <template #header>
            <span>行业配置分析</span>
          </template>
          <div class="sector-allocation">
            <div class="chart-container" ref="sectorChartRef">
              <div class="chart-placeholder">行业配置饼图</div>
            </div>
            <div class="sector-details">
              <div 
                v-for="sector in sectorData" 
                :key="sector.name"
                class="sector-item"
              >
                <div class="sector-info">
                  <span class="sector-name">{{ sector.name }}</span>
                  <span class="sector-weight">{{ sector.weight.toFixed(1) }}%</span>
                </div>
                <el-progress 
                  :percentage="sector.weight" 
                  :color="sector.color"
                  :show-text="false"
                  :stroke-width="6"
                />
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 风险归因分析 -->
    <el-card class="risk-attribution-card">
      <template #header>
        <div class="risk-header">
          <span>风险归因分析</span>
          <el-tabs v-model="riskAnalysisTab" class="risk-tabs">
            <el-tab-pane label="风险分解" name="decomposition" />
            <el-tab-pane label="因子暴露" name="exposure" />
            <el-tab-pane label="相关性分析" name="correlation" />
          </el-tabs>
        </div>
      </template>

      <div v-if="riskAnalysisTab === 'decomposition'" class="risk-decomposition">
        <el-row :gutter="24">
          <el-col :span="12">
            <h4>收益来源分解</h4>
            <div class="decomposition-chart" ref="returnDecompositionRef">
              <div class="chart-placeholder">收益分解图表</div>
            </div>
          </el-col>
          <el-col :span="12">
            <h4>风险来源分解</h4>
            <div class="decomposition-chart" ref="riskDecompositionRef">
              <div class="chart-placeholder">风险分解图表</div>
            </div>
          </el-col>
        </el-row>
      </div>

      <div v-if="riskAnalysisTab === 'exposure'" class="factor-exposure">
        <h4>因子暴露度分析</h4>
        <el-table :data="factorExposure" border>
          <el-table-column prop="factor" label="因子名称" width="150" />
          <el-table-column prop="exposure" label="暴露度" width="120">
            <template #default="{ row }">
              <el-progress 
                :percentage="Math.abs(row.exposure) * 100" 
                :color="row.exposure >= 0 ? '#67c23a' : '#f56c6c'"
                :format="() => row.exposure.toFixed(3)"
              />
            </template>
          </el-table-column>
          <el-table-column prop="tValue" label="T统计量" width="120" />
          <el-table-column prop="significance" label="显著性" width="100">
            <template #default="{ row }">
              <el-tag 
                :type="getSignificanceType(row.significance)"
                size="small"
              >
                {{ row.significance }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="description" label="因子描述" />
        </el-table>
      </div>

      <div v-if="riskAnalysisTab === 'correlation'" class="correlation-analysis">
        <h4>相关性热力图</h4>
        <div class="correlation-heatmap" ref="correlationHeatmapRef">
          <div class="chart-placeholder">相关性热力图</div>
        </div>
      </div>
    </el-card>

    <!-- 交易分析 -->
    <el-card class="trading-analysis-card">
      <template #header>
        <span>交易行为分析</span>
      </template>

      <el-row :gutter="24">
        <el-col :span="8">
          <div class="trading-stats">
            <h4>交易统计</h4>
            <div class="stats-grid">
              <div class="stat-item">
                <span class="stat-label">总交易次数</span>
                <span class="stat-value">{{ tradingStats.totalTrades }}</span>
              </div>
              <div class="stat-item">
                <span class="stat-label">盈利交易</span>
                <span class="stat-value positive">{{ tradingStats.profitableTrades }}</span>
              </div>
              <div class="stat-item">
                <span class="stat-label">亏损交易</span>
                <span class="stat-value negative">{{ tradingStats.losingTrades }}</span>
              </div>
              <div class="stat-item">
                <span class="stat-label">平均持仓天数</span>
                <span class="stat-value">{{ tradingStats.avgHoldingDays }}天</span>
              </div>
              <div class="stat-item">
                <span class="stat-label">换手率</span>
                <span class="stat-value">{{ tradingStats.turnoverRate.toFixed(2) }}%</span>
              </div>
              <div class="stat-item">
                <span class="stat-label">交易成本</span>
                <span class="stat-value">{{ tradingStats.tradingCost.toFixed(3) }}%</span>
              </div>
            </div>
          </div>
        </el-col>
        <el-col :span="16">
          <div class="trading-timeline">
            <h4>交易时间线</h4>
            <div class="timeline-chart" ref="tradingTimelineRef">
              <div class="chart-placeholder">交易时间线图表</div>
            </div>
          </div>
        </el-col>
      </el-row>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  TrendCharts, Refresh, Document, Plus
} from '@element-plus/icons-vue'

// 数据结构定义
interface Strategy {
  id: string
  name: string
  performance: 'excellent' | 'good' | 'average' | 'poor'
}

interface BacktestMetrics {
  annualReturn: number
  sharpeRatio: number
  maxDrawdown: number
  winRate: number
  excessReturn: number
}

interface Position {
  symbol: string
  name: string
  weight: number
  return: number
}

interface SectorData {
  name: string
  weight: number
  color: string
}

interface FactorExposure {
  factor: string
  exposure: number
  tValue: number
  significance: string
  description: string
}

// 响应式数据
const loading = ref(false)
const selectedStrategy = ref('')
const timeRange = ref(['2023-01-01', '2023-12-31'])
const selectedBenchmark = ref('CSI300')
const chartTimeframe = ref('ALL')
const rollingMetric = ref('sharpe')
const riskAnalysisTab = ref('decomposition')

const availableStrategies = ref<Strategy[]>([
  { id: 'strategy_1', name: 'LightGBM多因子策略v3', performance: 'excellent' },
  { id: 'strategy_2', name: 'LSTM时序预测策略', performance: 'good' },
  { id: 'strategy_3', name: '动量轮动策略', performance: 'average' }
])

const backtestMetrics = reactive<BacktestMetrics>({
  annualReturn: 0,
  sharpeRatio: 0,
  maxDrawdown: 0,
  winRate: 0,
  excessReturn: 0
})

const positionData = reactive({
  totalPositions: 0,
  totalValue: 0,
  cashRatio: 0,
  topHoldings: [] as Position[]
})

const sectorData = ref<SectorData[]>([])
const factorExposure = ref<FactorExposure[]>([])

const tradingStats = reactive({
  totalTrades: 0,
  profitableTrades: 0,
  losingTrades: 0,
  avgHoldingDays: 0,
  turnoverRate: 0,
  tradingCost: 0
})

// 计算属性
const sharpeRating = computed(() => {
  const ratio = backtestMetrics.sharpeRatio
  if (ratio >= 3) return 5
  if (ratio >= 2) return 4
  if (ratio >= 1) return 3
  if (ratio >= 0.5) return 2
  return 1
})

// 方法
const loadBacktestResults = async () => {
  if (!selectedStrategy.value) return

  loading.value = true

  try {
    const response = await fetch('/api/v1/models/backtest', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        strategy_id: selectedStrategy.value,
        start_time: timeRange.value[0],
        end_time: timeRange.value[1],
        benchmark: selectedBenchmark.value
      })
    })

    const result = await response.json()

    if (result.status === 'success') {
      updateDashboardData(result.data)
      ElMessage.success('回测数据加载成功')
    } else {
      throw new Error(result.message || '加载回测数据失败')
    }
  } catch (error) {
    console.error('加载回测数据失败:', error)
    ElMessage.error('加载回测数据失败: ' + error.message)
    
    // 降级到示例数据
    generateSampleData()
  } finally {
    loading.value = false
  }
}

const generateSampleData = () => {
  // 生成示例数据
  backtestMetrics.annualReturn = 28.5
  backtestMetrics.sharpeRatio = 1.89
  backtestMetrics.maxDrawdown = -8.2
  backtestMetrics.winRate = 65.4
  backtestMetrics.excessReturn = 12.3

  positionData.totalPositions = 20
  positionData.totalValue = 9850000
  positionData.cashRatio = 1.5
  positionData.topHoldings = [
    { symbol: '000001.SZ', name: '平安银行', weight: 8.5, return: 12.3 },
    { symbol: '600036.SH', name: '招商银行', weight: 7.8, return: 15.6 },
    { symbol: '000858.SZ', name: '五粮液', weight: 6.9, return: -2.1 }
  ]

  sectorData.value = [
    { name: '金融', weight: 35.2, color: '#5470c6' },
    { name: '科技', weight: 28.7, color: '#91cc75' },
    { name: '消费', weight: 20.1, color: '#fac858' },
    { name: '医药', weight: 16.0, color: '#ee6666' }
  ]

  factorExposure.value = [
    { factor: '市值因子', exposure: -0.234, tValue: -2.89, significance: '显著', description: '偏好小市值股票' },
    { factor: '盈利因子', exposure: 0.456, tValue: 5.67, significance: '高度显著', description: '偏好高盈利股票' },
    { factor: '成长因子', exposure: 0.123, tValue: 1.45, significance: '不显著', description: '成长偏好中性' }
  ]

  tradingStats.totalTrades = 1250
  tradingStats.profitableTrades = 817
  tradingStats.losingTrades = 433
  tradingStats.avgHoldingDays = 12
  tradingStats.turnoverRate = 450.5
  tradingStats.tradingCost = 0.125
}

const updateDashboardData = (data: any) => {
  // 更新指标数据
  if (data.metrics) {
    Object.assign(backtestMetrics, data.metrics)
  }

  // 更新持仓数据
  if (data.positions) {
    Object.assign(positionData, data.positions)
  }

  // 更新其他数据...
}

const refreshDashboard = () => {
  loadBacktestResults()
}

const exportReport = () => {
  ElMessage.success('报告导出功能开发中')
}

const createNewBacktest = () => {
  ElMessage.info('跳转到回测创建页面')
}

const getPerformanceTagType = (performance: string) => {
  const types: Record<string, string> = {
    excellent: 'success',
    good: 'primary',
    average: 'warning',
    poor: 'danger'
  }
  return types[performance] || 'default'
}

const getDrawdownColor = (drawdown: number) => {
  if (drawdown >= -5) return '#67c23a'
  if (drawdown >= -10) return '#e6a23c'
  return '#f56c6c'
}

const getSignificanceType = (significance: string) => {
  const types: Record<string, string> = {
    '高度显著': 'success',
    '显著': 'primary',
    '不显著': 'info'
  }
  return types[significance] || 'default'
}

// 生命周期
onMounted(() => {
  if (availableStrategies.value.length > 0) {
    selectedStrategy.value = availableStrategies.value[0].id
    loadBacktestResults()
  }
})
</script>

<style scoped>
.qlib-backtest-dashboard {
  padding: 20px;
}

.dashboard-header {
  margin-bottom: 20px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 18px;
  font-weight: 600;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.strategy-selector {
  padding: 16px 0;
}

.strategy-option {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.performance-overview {
  margin-bottom: 24px;
}

.metric-card {
  text-align: center;
  position: relative;
  overflow: hidden;
}

.metric-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(90deg, #409eff, #67c23a);
}

.metric-comparison {
  margin-top: 8px;
  font-size: 12px;
}

.comparison-text {
  color: #909399;
}

.comparison-value.positive {
  color: #67c23a;
}

.comparison-value.negative {
  color: #f56c6c;
}

.metric-rating {
  margin-top: 8px;
}

.drawdown-indicator {
  margin-top: 12px;
}

.win-rate-chart {
  margin-top: 12px;
  display: flex;
  justify-content: center;
}

.charts-section {
  margin-bottom: 24px;
}

.chart-card {
  height: 100%;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chart-controls {
  display: flex;
  gap: 8px;
  align-items: center;
}

.chart-container {
  height: 300px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px dashed #d9d9d9;
  border-radius: 6px;
}

.chart-placeholder {
  color: #999;
  font-size: 14px;
}

.position-section {
  margin-bottom: 24px;
}

.position-card {
  height: 100%;
}

.position-overview {
  padding: 16px 0;
}

.position-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.stat-item {
  text-align: center;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 6px;
}

.stat-label {
  display: block;
  font-size: 12px;
  color: #909399;
  margin-bottom: 4px;
}

.stat-value {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.stat-value.positive {
  color: #67c23a;
}

.stat-value.negative {
  color: #f56c6c;
}

.top-holdings h4 {
  margin-bottom: 16px;
  color: #303133;
}

.positive {
  color: #67c23a;
}

.negative {
  color: #f56c6c;
}

.sector-allocation {
  padding: 16px 0;
}

.sector-details {
  margin-top: 16px;
}

.sector-item {
  margin-bottom: 12px;
}

.sector-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: 4px;
  font-size: 12px;
}

.sector-name {
  color: #303133;
}

.sector-weight {
  color: #909399;
}

.risk-attribution-card {
  margin-bottom: 24px;
}

.risk-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.risk-tabs {
  margin: 0;
}

.risk-decomposition,
.factor-exposure,
.correlation-analysis {
  padding: 16px 0;
}

.decomposition-chart {
  height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px dashed #d9d9d9;
  border-radius: 6px;
}

.correlation-heatmap {
  height: 300px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px dashed #d9d9d9;
  border-radius: 6px;
}

.trading-analysis-card {
  margin-bottom: 24px;
}

.trading-stats h4,
.trading-timeline h4 {
  margin-bottom: 16px;
  color: #303133;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.timeline-chart {
  height: 250px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px dashed #d9d9d9;
  border-radius: 6px;
}

@media (max-width: 768px) {
  .qlib-backtest-dashboard {
    padding: 12px;
  }
  
  .header-content {
    flex-direction: column;
    gap: 16px;
  }
  
  .strategy-selector .el-col {
    margin-bottom: 16px;
  }
  
  .performance-overview .el-col {
    margin-bottom: 16px;
  }
  
  .charts-section .el-col {
    margin-bottom: 16px;
  }
  
  .position-section .el-col {
    margin-bottom: 16px;
  }
  
  .position-stats {
    grid-template-columns: 1fr;
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
  }
}
</style>