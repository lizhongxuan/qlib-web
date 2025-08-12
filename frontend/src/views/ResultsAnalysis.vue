<template>
  <div class="results-analysis">
    <!-- 页面头部 -->
    <div class="page-header">
      <h1 class="page-title">
        <el-icon><DataAnalysis /></el-icon>
        结果分析中心
      </h1>
      <p class="page-subtitle">全面的策略表现分析和智能化投资建议</p>
    </div>

    <!-- 策略概览 -->
    <el-card class="overview-section">
      <template #header>
        <div class="section-header">
          <span>策略概览</span>
          <el-select v-model="selectedStrategy" style="width: 300px" @change="handleStrategyChange">
            <el-option 
              v-for="strategy in strategies" 
              :key="strategy.id"
              :label="strategy.name"
              :value="strategy.id"
            />
          </el-select>
        </div>
      </template>

      <div v-if="currentStrategy" class="strategy-overview">
        <div class="overview-cards">
          <el-row :gutter="24">
            <el-col :span="4">
              <div class="overview-card">
                <div class="card-icon positive">
                  <el-icon><TrendCharts /></el-icon>
                </div>
                <div class="card-content">
                  <div class="card-value">{{ currentStrategy.metrics.totalReturn.toFixed(2) }}%</div>
                  <div class="card-label">总收益率</div>
                </div>
              </div>
            </el-col>
            
            <el-col :span="4">
              <div class="overview-card">
                <div class="card-icon info">
                  <el-icon><PieChart /></el-icon>
                </div>
                <div class="card-content">
                  <div class="card-value">{{ currentStrategy.metrics.sharpeRatio.toFixed(2) }}</div>
                  <div class="card-label">夏普比率</div>
                </div>
              </div>
            </el-col>
            
            <el-col :span="4">
              <div class="overview-card">
                <div class="card-icon warning">
                  <el-icon><Warning /></el-icon>
                </div>
                <div class="card-content">
                  <div class="card-value">{{ (currentStrategy.metrics.maxDrawdown * 100).toFixed(2) }}%</div>
                  <div class="card-label">最大回撤</div>
                </div>
              </div>
            </el-col>
            
            <el-col :span="4">
              <div class="overview-card">
                <div class="card-icon success">
                  <el-icon><SuccessFilled /></el-icon>
                </div>
                <div class="card-content">
                  <div class="card-value">{{ currentStrategy.metrics.winRate.toFixed(1) }}%</div>
                  <div class="card-label">胜率</div>
                </div>
              </div>
            </el-col>
            
            <el-col :span="4">
              <div class="overview-card">
                <div class="card-icon primary">
                  <el-icon><Clock /></el-icon>
                </div>
                <div class="card-content">
                  <div class="card-value">{{ currentStrategy.metrics.avgHoldingDays }}</div>
                  <div class="card-label">平均持仓天数</div>
                </div>
              </div>
            </el-col>
            
            <el-col :span="4">
              <div class="overview-card">
                <div class="card-icon danger">
                  <el-icon><Odometer /></el-icon>
                </div>
                <div class="card-content">
                  <div class="card-value">{{ (currentStrategy.metrics.volatility * 100).toFixed(2) }}%</div>
                  <div class="card-label">年化波动率</div>
                </div>
              </div>
            </el-col>
          </el-row>
        </div>

        <div class="strategy-info">
          <el-descriptions :column="4" border>
            <el-descriptions-item label="策略类型">
              <el-tag>{{ currentStrategy.type }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="回测期间">
              {{ currentStrategy.backtest.startDate }} - {{ currentStrategy.backtest.endDate }}
            </el-descriptions-item>
            <el-descriptions-item label="股票池">
              {{ currentStrategy.universe }}
            </el-descriptions-item>
            <el-descriptions-item label="调仓频率">
              {{ getFrequencyText(currentStrategy.rebalanceFreq) }}
            </el-descriptions-item>
          </el-descriptions>
        </div>
      </div>
    </el-card>

    <!-- 详细分析 -->
    <el-card class="analysis-section">
      <el-tabs v-model="activeTab" type="card">
        <!-- 收益分析 -->
        <el-tab-pane label="收益分析" name="returns">
          <div class="returns-analysis">
            <el-row :gutter="24">
              <el-col :span="16">
                <el-card class="chart-card">
                  <template #header>
                    <div class="chart-header">
                      <span>净值曲线对比</span>
                      <el-checkbox-group v-model="visibleSeries" size="small">
                        <el-checkbox label="strategy">策略</el-checkbox>
                        <el-checkbox label="benchmark">基准</el-checkbox>
                        <el-checkbox label="excess">超额收益</el-checkbox>
                      </el-checkbox-group>
                    </div>
                  </template>
                  <div ref="returnsChart" class="chart-container large"></div>
                </el-card>
              </el-col>
              
              <el-col :span="8">
                <el-card class="metrics-card">
                  <template #header>
                    <span>收益指标</span>
                  </template>
                  <div class="metrics-list">
                    <div class="metric-item">
                      <span class="metric-name">累计收益率</span>
                      <span class="metric-value positive">+{{ currentStrategy?.metrics.totalReturn.toFixed(2) }}%</span>
                    </div>
                    <div class="metric-item">
                      <span class="metric-name">基准收益率</span>
                      <span class="metric-value">+{{ currentStrategy?.metrics.benchmarkReturn.toFixed(2) }}%</span>
                    </div>
                    <div class="metric-item">
                      <span class="metric-name">超额收益率</span>
                      <span class="metric-value positive">+{{ currentStrategy?.metrics.excessReturn.toFixed(2) }}%</span>
                    </div>
                    <div class="metric-item">
                      <span class="metric-name">年化收益率</span>
                      <span class="metric-value positive">+{{ currentStrategy?.metrics.annualReturn.toFixed(2) }}%</span>
                    </div>
                    <div class="metric-item">
                      <span class="metric-name">信息比率</span>
                      <span class="metric-value">{{ currentStrategy?.metrics.informationRatio.toFixed(3) }}</span>
                    </div>
                    <div class="metric-item">
                      <span class="metric-name">卡玛比率</span>
                      <span class="metric-value">{{ currentStrategy?.metrics.calmarRatio.toFixed(3) }}</span>
                    </div>
                  </div>
                </el-card>
                
                <el-card class="period-analysis" style="margin-top: 16px;">
                  <template #header>
                    <span>分期表现</span>
                  </template>
                  <el-table :data="periodPerformance" size="small">
                    <el-table-column prop="period" label="期间" width="80" />
                    <el-table-column prop="return" label="收益率">
                      <template #default="{ row }">
                        <span :class="row.return >= 0 ? 'positive' : 'negative'">
                          {{ row.return.toFixed(2) }}%
                        </span>
                      </template>
                    </el-table-column>
                    <el-table-column prop="benchmark" label="基准">
                      <template #default="{ row }">
                        <span :class="row.benchmark >= 0 ? 'positive' : 'negative'">
                          {{ row.benchmark.toFixed(2) }}%
                        </span>
                      </template>
                    </el-table-column>
                  </el-table>
                </el-card>
              </el-col>
            </el-row>
          </div>
        </el-tab-pane>

        <!-- 风险分析 -->
        <el-tab-pane label="风险分析" name="risk">
          <div class="risk-analysis">
            <el-row :gutter="24">
              <el-col :span="12">
                <el-card class="chart-card">
                  <template #header>
                    <span>回撤分析</span>
                  </template>
                  <div ref="drawdownChart" class="chart-container"></div>
                </el-card>
              </el-col>
              
              <el-col :span="12">
                <el-card class="chart-card">
                  <template #header>
                    <span>收益分布</span>
                  </template>
                  <div ref="returnDistributionChart" class="chart-container"></div>
                </el-card>
              </el-col>
            </el-row>
            
            <el-row :gutter="24" style="margin-top: 24px;">
              <el-col :span="12">
                <el-card class="risk-metrics-card">
                  <template #header>
                    <span>风险指标</span>
                  </template>
                  <el-descriptions :column="1" border>
                    <el-descriptions-item label="最大回撤">
                      {{ (currentStrategy?.metrics.maxDrawdown * 100).toFixed(2) }}%
                    </el-descriptions-item>
                    <el-descriptions-item label="VaR (95%)">
                      {{ (currentStrategy?.metrics.var95 * 100).toFixed(2) }}%
                    </el-descriptions-item>
                    <el-descriptions-item label="CVaR (95%)">
                      {{ (currentStrategy?.metrics.cvar95 * 100).toFixed(2) }}%
                    </el-descriptions-item>
                    <el-descriptions-item label="下行风险">
                      {{ (currentStrategy?.metrics.downsideRisk * 100).toFixed(2) }}%
                    </el-descriptions-item>
                    <el-descriptions-item label="Beta系数">
                      {{ currentStrategy?.metrics.beta.toFixed(3) }}
                    </el-descriptions-item>
                    <el-descriptions-item label="跟踪误差">
                      {{ (currentStrategy?.metrics.trackingError * 100).toFixed(2) }}%
                    </el-descriptions-item>
                  </el-descriptions>
                </el-card>
              </el-col>
              
              <el-col :span="12">
                <el-card class="drawdown-periods-card">
                  <template #header>
                    <span>主要回撤期</span>
                  </template>
                  <el-table :data="drawdownPeriods" size="small">
                    <el-table-column prop="startDate" label="开始日期" width="100" />
                    <el-table-column prop="endDate" label="结束日期" width="100" />
                    <el-table-column prop="duration" label="持续天数" width="80" />
                    <el-table-column prop="drawdown" label="回撤幅度">
                      <template #default="{ row }">
                        <span class="negative">{{ (row.drawdown * 100).toFixed(2) }}%</span>
                      </template>
                    </el-table-column>
                  </el-table>
                </el-card>
              </el-col>
            </el-row>
          </div>
        </el-tab-pane>

        <!-- 持仓分析 -->
        <el-tab-pane label="持仓分析" name="positions">
          <div class="positions-analysis">
            <el-row :gutter="24">
              <el-col :span="12">
                <el-card class="chart-card">
                  <template #header>
                    <span>行业分布</span>
                  </template>
                  <div ref="sectorChart" class="chart-container"></div>
                </el-card>
              </el-col>
              
              <el-col :span="12">
                <el-card class="chart-card">
                  <template #header>
                    <span>持仓集中度</span>
                  </template>
                  <div ref="concentrationChart" class="chart-container"></div>
                </el-card>
              </el-col>
            </el-row>
            
            <el-card class="positions-table" style="margin-top: 24px;">
              <template #header>
                <div class="table-header">
                  <span>重仓持股分析</span>
                  <el-select v-model="positionPeriod" size="small" style="width: 150px">
                    <el-option label="最新持仓" value="latest" />
                    <el-option label="平均持仓" value="average" />
                    <el-option label="最大持仓" value="maximum" />
                  </el-select>
                </div>
              </template>
              
              <el-table :data="topHoldings" size="small">
                <el-table-column prop="symbol" label="股票代码" width="100" />
                <el-table-column prop="name" label="股票名称" width="150" />
                <el-table-column prop="sector" label="行业" width="120" />
                <el-table-column prop="weight" label="权重" width="80">
                  <template #default="{ row }">
                    {{ (row.weight * 100).toFixed(2) }}%
                  </template>
                </el-table-column>
                <el-table-column prop="return" label="持仓收益" width="100">
                  <template #default="{ row }">
                    <span :class="row.return >= 0 ? 'positive' : 'negative'">
                      {{ (row.return * 100).toFixed(2) }}%
                    </span>
                  </template>
                </el-table-column>
                <el-table-column prop="contribution" label="收益贡献" width="100">
                  <template #default="{ row }">
                    <span :class="row.contribution >= 0 ? 'positive' : 'negative'">
                      {{ (row.contribution * 100).toFixed(2) }}%
                    </span>
                  </template>
                </el-table-column>
                <el-table-column prop="holdingDays" label="持有天数" width="80" />
                <el-table-column prop="turnover" label="换手率" width="80">
                  <template #default="{ row }">
                    {{ (row.turnover * 100).toFixed(1) }}%
                  </template>
                </el-table-column>
              </el-table>
            </el-card>
          </div>
        </el-tab-pane>

        <!-- 交易分析 -->
        <el-tab-pane label="交易分析" name="trading">
          <div class="trading-analysis">
            <el-row :gutter="24">
              <el-col :span="8">
                <el-card class="trading-stats">
                  <template #header>
                    <span>交易统计</span>
                  </template>
                  <div class="stats-grid">
                    <div class="stat-item">
                      <div class="stat-label">总交易次数</div>
                      <div class="stat-value">{{ tradingStats.totalTrades }}</div>
                    </div>
                    <div class="stat-item">
                      <div class="stat-label">盈利交易</div>
                      <div class="stat-value positive">{{ tradingStats.winningTrades }}</div>
                    </div>
                    <div class="stat-item">
                      <div class="stat-label">亏损交易</div>
                      <div class="stat-value negative">{{ tradingStats.losingTrades }}</div>
                    </div>
                    <div class="stat-item">
                      <div class="stat-label">平均收益</div>
                      <div class="stat-value">{{ (tradingStats.avgReturn * 100).toFixed(2) }}%</div>
                    </div>
                    <div class="stat-item">
                      <div class="stat-label">最大单笔盈利</div>
                      <div class="stat-value positive">{{ (tradingStats.maxWin * 100).toFixed(2) }}%</div>
                    </div>
                    <div class="stat-item">
                      <div class="stat-label">最大单笔亏损</div>
                      <div class="stat-value negative">{{ (tradingStats.maxLoss * 100).toFixed(2) }}%</div>
                    </div>
                  </div>
                </el-card>
              </el-col>
              
              <el-col :span="16">
                <el-card class="chart-card">
                  <template #header>
                    <span>月度交易分析</span>
                  </template>
                  <div ref="monthlyTradingChart" class="chart-container"></div>
                </el-card>
              </el-col>
            </el-row>
            
            <el-card class="trades-table" style="margin-top: 24px;">
              <template #header>
                <div class="table-header">
                  <span>交易明细</span>
                  <div class="table-controls">
                    <el-select v-model="tradeFilter" size="small" style="width: 120px; margin-right: 12px;">
                      <el-option label="全部" value="all" />
                      <el-option label="盈利" value="winning" />
                      <el-option label="亏损" value="losing" />
                    </el-select>
                    <el-button size="small" @click="exportTrades">
                      <el-icon><Download /></el-icon>
                      导出
                    </el-button>
                  </div>
                </div>
              </template>
              
              <el-table :data="filteredTrades" size="small" max-height="400">
                <el-table-column prop="symbol" label="股票代码" width="100" />
                <el-table-column prop="name" label="股票名称" width="150" />
                <el-table-column prop="buyDate" label="买入日期" width="100" />
                <el-table-column prop="sellDate" label="卖出日期" width="100" />
                <el-table-column prop="buyPrice" label="买入价格" width="100">
                  <template #default="{ row }">
                    ¥{{ row.buyPrice.toFixed(2) }}
                  </template>
                </el-table-column>
                <el-table-column prop="sellPrice" label="卖出价格" width="100">
                  <template #default="{ row }">
                    ¥{{ row.sellPrice.toFixed(2) }}
                  </template>
                </el-table-column>
                <el-table-column prop="return" label="收益率" width="100">
                  <template #default="{ row }">
                    <span :class="row.return >= 0 ? 'positive' : 'negative'">
                      {{ (row.return * 100).toFixed(2) }}%
                    </span>
                  </template>
                </el-table-column>
                <el-table-column prop="holdingDays" label="持有天数" width="80" />
                <el-table-column prop="profit" label="盈亏金额" width="120">
                  <template #default="{ row }">
                    <span :class="row.profit >= 0 ? 'positive' : 'negative'">
                      ¥{{ row.profit.toFixed(2) }}
                    </span>
                  </template>
                </el-table-column>
              </el-table>
            </el-card>
          </div>
        </el-tab-pane>

        <!-- AI建议 -->
        <el-tab-pane label="AI建议" name="suggestions">
          <div class="ai-suggestions">
            <el-card class="suggestions-overview">
              <template #header>
                <div class="suggestions-header">
                  <span>策略优化建议</span>
                  <el-button @click="generateSuggestions" :loading="generatingSuggestions">
                    <el-icon><MagicStick /></el-icon>
                    重新生成建议
                  </el-button>
                </div>
              </template>
              
              <div class="suggestions-content">
                <div class="suggestion-category">
                  <h3>📈 收益优化</h3>
                  <div class="suggestions-list">
                    <div v-for="suggestion in suggestions.returns" :key="suggestion.id" class="suggestion-item">
                      <div class="suggestion-header">
                        <el-tag :type="getSuggestionTagType(suggestion.priority)" size="small">
                          {{ getPriorityText(suggestion.priority) }}
                        </el-tag>
                        <span class="suggestion-title">{{ suggestion.title }}</span>
                      </div>
                      <div class="suggestion-content">{{ suggestion.content }}</div>
                      <div class="suggestion-impact">
                        预期收益提升: <span class="positive">+{{ suggestion.expectedImpact }}%</span>
                      </div>
                    </div>
                  </div>
                </div>
                
                <div class="suggestion-category">
                  <h3>🛡️ 风险控制</h3>
                  <div class="suggestions-list">
                    <div v-for="suggestion in suggestions.risk" :key="suggestion.id" class="suggestion-item">
                      <div class="suggestion-header">
                        <el-tag :type="getSuggestionTagType(suggestion.priority)" size="small">
                          {{ getPriorityText(suggestion.priority) }}
                        </el-tag>
                        <span class="suggestion-title">{{ suggestion.title }}</span>
                      </div>
                      <div class="suggestion-content">{{ suggestion.content }}</div>
                      <div class="suggestion-impact">
                        预期风险降低: <span class="info">{{ suggestion.riskReduction }}%</span>
                      </div>
                    </div>
                  </div>
                </div>
                
                <div class="suggestion-category">
                  <h3>⚡ 执行效率</h3>
                  <div class="suggestions-list">
                    <div v-for="suggestion in suggestions.execution" :key="suggestion.id" class="suggestion-item">
                      <div class="suggestion-header">
                        <el-tag :type="getSuggestionTagType(suggestion.priority)" size="small">
                          {{ getPriorityText(suggestion.priority) }}
                        </el-tag>
                        <span class="suggestion-title">{{ suggestion.title }}</span>
                      </div>
                      <div class="suggestion-content">{{ suggestion.content }}</div>
                      <div class="suggestion-impact">
                        预期改善: <span class="warning">{{ suggestion.improvement }}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </el-card>
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  DataAnalysis, TrendCharts, PieChart, Warning, SuccessFilled,
  Clock, Odometer, Download, MagicStick
} from '@element-plus/icons-vue'

// 响应式数据
const activeTab = ref('returns')
const selectedStrategy = ref('strategy_1')
const visibleSeries = ref(['strategy', 'benchmark'])
const positionPeriod = ref('latest')
const tradeFilter = ref('all')
const generatingSuggestions = ref(false)

// 策略数据
const strategies = ref([
  {
    id: 'strategy_1',
    name: 'LightGBM多因子策略v3.2',
    type: '机器学习策略',
    universe: '沪深300',
    rebalanceFreq: 'monthly',
    backtest: {
      startDate: '2022-01-01',
      endDate: '2023-12-31'
    },
    metrics: {
      totalReturn: 28.5,
      benchmarkReturn: 15.2,
      excessReturn: 13.3,
      annualReturn: 24.8,
      sharpeRatio: 1.45,
      maxDrawdown: -0.12,
      winRate: 62.5,
      avgHoldingDays: 28,
      volatility: 0.18,
      informationRatio: 0.85,
      calmarRatio: 2.07,
      var95: -0.028,
      cvar95: -0.042,
      downsideRisk: 0.13,
      beta: 0.92,
      trackingError: 0.15
    }
  }
])

// 模拟数据
const periodPerformance = ref([
  { period: '2022Q1', return: 5.2, benchmark: 3.8 },
  { period: '2022Q2', return: -3.1, benchmark: -5.2 },
  { period: '2022Q3', return: 8.7, benchmark: 4.1 },
  { period: '2022Q4', return: 12.3, benchmark: 7.8 },
  { period: '2023Q1', return: 6.8, benchmark: 5.1 },
  { period: '2023Q2', return: -1.5, benchmark: -2.8 },
  { period: '2023Q3', return: 4.9, benchmark: 2.6 },
  { period: '2023Q4', return: 9.2, benchmark: 6.3 }
])

const drawdownPeriods = ref([
  {
    startDate: '2022-04-15',
    endDate: '2022-05-30',
    duration: 45,
    drawdown: -0.08
  },
  {
    startDate: '2022-10-12',
    endDate: '2022-11-28',
    duration: 47,
    drawdown: -0.12
  },
  {
    startDate: '2023-06-05',
    endDate: '2023-07-15',
    duration: 40,
    drawdown: -0.06
  }
])

const topHoldings = ref([
  {
    symbol: '000001',
    name: '平安银行',
    sector: '金融业',
    weight: 0.045,
    return: 0.15,
    contribution: 0.0068,
    holdingDays: 32,
    turnover: 0.12
  },
  {
    symbol: '600036',
    name: '招商银行',
    sector: '金融业',
    weight: 0.052,
    return: 0.18,
    contribution: 0.0094,
    holdingDays: 28,
    turnover: 0.15
  },
  {
    symbol: '000858',
    name: '五粮液',
    sector: '食品饮料',
    weight: 0.038,
    return: 0.22,
    contribution: 0.0084,
    holdingDays: 35,
    turnover: 0.08
  }
])

const tradingStats = reactive({
  totalTrades: 1250,
  winningTrades: 781,
  losingTrades: 469,
  avgReturn: 0.023,
  maxWin: 0.185,
  maxLoss: -0.095
})

const allTrades = ref([
  {
    symbol: '000001',
    name: '平安银行',
    buyDate: '2023-01-15',
    sellDate: '2023-02-20',
    buyPrice: 12.45,
    sellPrice: 14.28,
    return: 0.147,
    holdingDays: 36,
    profit: 1830
  },
  {
    symbol: '600519',
    name: '贵州茅台',
    buyDate: '2023-03-10',
    sellDate: '2023-04-05',
    buyPrice: 1850,
    sellPrice: 1680,
    return: -0.092,
    holdingDays: 26,
    profit: -1700
  }
])

const suggestions = reactive({
  returns: [
    {
      id: 1,
      priority: 'high',
      title: '优化因子权重配置',
      content: '建议增加动量因子权重至25%，降低价值因子权重至20%，以提升策略在趋势行情中的表现',
      expectedImpact: 2.3
    },
    {
      id: 2,
      priority: 'medium',
      title: '增加小盘股暴露',
      content: '适当增加中证1000成分股比例，利用小盘股的超额收益机会',
      expectedImpact: 1.8
    }
  ],
  risk: [
    {
      id: 3,
      priority: 'high',
      title: '加强行业分散化',
      content: '限制单一行业权重不超过15%，当前金融行业权重过高(18.5%)',
      riskReduction: 15
    },
    {
      id: 4,
      priority: 'medium',
      title: '设置动态止损',
      content: '根据市场波动率动态调整止损阈值，牛市8%，熊市12%',
      riskReduction: 12
    }
  ],
  execution: [
    {
      id: 5,
      priority: 'medium',
      title: '优化调仓时机',
      content: '建议在月初第5个交易日调仓，避开财报密集发布期',
      improvement: '减少5%交易成本'
    }
  ]
})

// 计算属性
const currentStrategy = computed(() => {
  return strategies.value.find(s => s.id === selectedStrategy.value)
})

const filteredTrades = computed(() => {
  if (tradeFilter.value === 'all') return allTrades.value
  if (tradeFilter.value === 'winning') return allTrades.value.filter(t => t.return > 0)
  return allTrades.value.filter(t => t.return < 0)
})

// 方法
const getFrequencyText = (freq: string) => {
  switch (freq) {
    case 'daily': return '日调仓'
    case 'weekly': return '周调仓'
    case 'monthly': return '月调仓'
    default: return freq
  }
}

const handleStrategyChange = () => {
  ElMessage.info('策略已切换')
}

const getSuggestionTagType = (priority: string) => {
  switch (priority) {
    case 'high': return 'danger'
    case 'medium': return 'warning'
    case 'low': return 'info'
    default: return 'info'
  }
}

const getPriorityText = (priority: string) => {
  switch (priority) {
    case 'high': return '高优先级'
    case 'medium': return '中优先级'
    case 'low': return '低优先级'
    default: return '普通'
  }
}

const generateSuggestions = () => {
  generatingSuggestions.value = true
  
  setTimeout(() => {
    generatingSuggestions.value = false
    ElMessage.success('AI建议已更新')
  }, 2000)
}

const exportTrades = () => {
  ElMessage.success('交易记录导出已开始')
}

// 生命周期
onMounted(() => {
  // 初始化图表
})
</script>

<style scoped>
.results-analysis {
  padding: 24px;
  max-width: 1600px;
  margin: 0 auto;
}

.page-header {
  text-align: center;
  margin-bottom: 32px;
}

.page-title {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  font-size: 28px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 12px 0;
}

.page-subtitle {
  color: #606266;
  font-size: 16px;
  margin: 0;
}

.overview-section,
.analysis-section {
  margin-bottom: 32px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.strategy-overview {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.overview-cards {
  margin-bottom: 24px;
}

.overview-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  background: linear-gradient(135deg, #f0f8ff 0%, #e8f4fd 100%);
  border-radius: 8px;
  border: 1px solid #d4e4fd;
}

.card-icon {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  color: #fff;
}

.card-icon.positive {
  background: linear-gradient(135deg, #67c23a, #85ce61);
}

.card-icon.info {
  background: linear-gradient(135deg, #409eff, #66b1ff);
}

.card-icon.warning {
  background: linear-gradient(135deg, #e6a23c, #ebb563);
}

.card-icon.success {
  background: linear-gradient(135deg, #67c23a, #85ce61);
}

.card-icon.primary {
  background: linear-gradient(135deg, #409eff, #66b1ff);
}

.card-icon.danger {
  background: linear-gradient(135deg, #f56c6c, #f78989);
}

.card-content {
  flex: 1;
}

.card-value {
  font-size: 24px;
  font-weight: 600;
  color: #303133;
  line-height: 1;
  margin-bottom: 4px;
}

.card-label {
  font-size: 14px;
  color: #606266;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chart-container {
  width: 100%;
  height: 300px;
  background: #f5f7fa;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #909399;
}

.chart-container.large {
  height: 400px;
}

.metrics-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.metric-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  background: #f8f9fa;
  border-radius: 6px;
}

.metric-name {
  color: #606266;
  font-size: 14px;
}

.metric-value {
  font-weight: 600;
  color: #303133;
}

.metric-value.positive {
  color: #67c23a;
}

.metric-value.negative {
  color: #f56c6c;
}

.positive {
  color: #67c23a;
}

.negative {
  color: #f56c6c;
}

.info {
  color: #409eff;
}

.warning {
  color: #e6a23c;
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.table-controls {
  display: flex;
  align-items: center;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.stat-item {
  text-align: center;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 6px;
}

.stat-label {
  font-size: 14px;
  color: #606266;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 20px;
  font-weight: 600;
  color: #303133;
}

.suggestions-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.suggestions-content {
  display: flex;
  flex-direction: column;
  gap: 32px;
}

.suggestion-category h3 {
  margin: 0 0 16px 0;
  color: #303133;
  font-size: 18px;
  font-weight: 600;
}

.suggestions-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.suggestion-item {
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
  border-left: 4px solid #409eff;
}

.suggestion-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.suggestion-title {
  font-weight: 600;
  color: #303133;
}

.suggestion-content {
  color: #606266;
  line-height: 1.6;
  margin-bottom: 12px;
}

.suggestion-impact {
  font-size: 14px;
  color: #909399;
}

@media (max-width: 768px) {
  .results-analysis {
    padding: 16px;
  }
  
  .overview-cards .el-row {
    flex-direction: column;
    gap: 16px;
  }
  
  .overview-card {
    padding: 16px;
  }
  
  .chart-header {
    flex-direction: column;
    gap: 12px;
  }
  
  .table-header {
    flex-direction: column;
    gap: 12px;
  }
  
  .table-controls {
    width: 100%;
    justify-content: center;
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
  }
  
  .suggestions-header {
    flex-direction: column;
    gap: 12px;
  }
}
</style>