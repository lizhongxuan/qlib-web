<template>
  <div class="qlib-risk-analyzer">
    <!-- 风险分析头部 -->
    <el-card class="analyzer-header">
      <template #header>
        <div class="header-content">
          <div class="header-title">
            <el-icon><Warning /></el-icon>
            <span>Qlib风险分析与归因界面</span>
          </div>
          <div class="header-actions">
            <el-button @click="refreshAnalysis" :loading="loading">
              <el-icon><Refresh /></el-icon>
              刷新分析
            </el-button>
            <el-button @click="exportReport">
              <el-icon><Download /></el-icon>
              导出报告
            </el-button>
            <el-button @click="configRiskModel">
              <el-icon><Setting /></el-icon>
              风险模型
            </el-button>
            <el-button type="primary" @click="runRiskAnalysis" :loading="analyzing">
              <el-icon><TrendCharts /></el-icon>
              运行分析
            </el-button>
          </div>
        </div>
      </template>

      <!-- 分析配置 -->
      <div class="analysis-config">
        <el-row :gutter="16">
          <el-col :span="6">
            <el-form-item label="策略选择">
              <el-select 
                v-model="selectedStrategy" 
                placeholder="请选择要分析的策略"
                @change="loadStrategyData"
              >
                <el-option
                  v-for="strategy in availableStrategies"
                  :key="strategy.id"
                  :label="strategy.name"
                  :value="strategy.id"
                >
                  <div class="strategy-option">
                    <span>{{ strategy.name }}</span>
                    <el-tag size="small" :type="getStrategyTagType(strategy.status)">
                      {{ strategy.status }}
                    </el-tag>
                  </div>
                </el-option>
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="分析时间">
              <el-date-picker
                v-model="timeRange"
                type="daterange"
                start-placeholder="开始日期"
                end-placeholder="结束日期"
                format="YYYY-MM-DD"
                value-format="YYYY-MM-DD"
                @change="loadStrategyData"
              />
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="基准对比">
              <el-select v-model="selectedBenchmark" @change="loadStrategyData">
                <el-option label="沪深300" value="CSI300" />
                <el-option label="中证500" value="CSI500" />
                <el-option label="上证50" value="SSE50" />
                <el-option label="创业板指" value="ChiNext" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="风险模型">
              <el-select v-model="selectedRiskModel">
                <el-option label="Barra CNE5" value="barra_cne5" />
                <el-option label="多因子模型" value="multi_factor" />
                <el-option label="协方差矩阵" value="covariance" />
                <el-option label="GARCH模型" value="garch" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
      </div>
    </el-card>

    <!-- 风险指标概览 -->
    <el-row :gutter="16" class="risk-overview">
      <el-col :span="6">
        <el-card class="metric-card volatility">
          <el-statistic 
            title="年化波动率" 
            :value="riskMetrics.volatility" 
            suffix="%" 
            :precision="2"
          />
          <div class="metric-comparison">
            <span class="comparison-text">vs 基准: </span>
            <span :class="['comparison-value', riskMetrics.volatilityExcess >= 0 ? 'higher' : 'lower']">
              {{ riskMetrics.volatilityExcess >= 0 ? '+' : '' }}{{ riskMetrics.volatilityExcess.toFixed(2) }}%
            </span>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="metric-card var">
          <el-statistic 
            title="VaR (95%)" 
            :value="riskMetrics.var95" 
            suffix="%" 
            :precision="2"
          />
          <div class="var-indicator">
            <el-progress 
              :percentage="Math.abs(riskMetrics.var95) * 10"
              :color="getVarColor(riskMetrics.var95)"
              :show-text="false"
              :stroke-width="8"
            />
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="metric-card cvar">
          <el-statistic 
            title="CVaR (95%)" 
            :value="riskMetrics.cvar95" 
            suffix="%" 
            :precision="2"
          />
          <div class="risk-level">
            <el-tag :type="getRiskLevelType(riskMetrics.cvar95)">
              {{ getRiskLevel(riskMetrics.cvar95) }}
            </el-tag>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="metric-card beta">
          <el-statistic 
            title="Beta系数" 
            :value="riskMetrics.beta" 
            :precision="3"
          />
          <div class="beta-chart">
            <el-progress 
              type="circle" 
              :percentage="Math.min(Math.abs(riskMetrics.beta) * 100, 100)"
              :width="60"
              :stroke-width="6"
              :color="getBetaColor(riskMetrics.beta)"
              :format="() => riskMetrics.beta.toFixed(2)"
            />
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 风险分析图表 -->
    <el-row :gutter="16" class="risk-charts">
      <!-- 风险时序分析 -->
      <el-col :span="16">
        <el-card class="chart-card">
          <template #header>
            <div class="chart-header">
              <span>风险时序分析</span>
              <div class="chart-controls">
                <el-radio-group v-model="riskChartType" size="small">
                  <el-radio-button label="volatility">波动率</el-radio-button>
                  <el-radio-button label="var">VaR</el-radio-button>
                  <el-radio-button label="drawdown">回撤</el-radio-button>
                  <el-radio-button label="beta">Beta</el-radio-button>
                </el-radio-group>
              </div>
            </div>
          </template>
          <div class="chart-container" ref="riskTimeSeriesRef">
            <div class="chart-placeholder">风险时序图表区域</div>
          </div>
        </el-card>
      </el-col>

      <!-- 风险分布图 -->
      <el-col :span="8">
        <el-card class="chart-card">
          <template #header>
            <span>收益分布与风险</span>
          </template>
          <div class="chart-container" ref="returnDistributionRef">
            <div class="chart-placeholder">收益分布图</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 风险归因分析 -->
    <el-card class="risk-attribution-card">
      <template #header>
        <div class="attribution-header">
          <span>风险归因分析</span>
          <el-tabs v-model="attributionTab" class="attribution-tabs">
            <el-tab-pane label="因子风险" name="factor" />
            <el-tab-pane label="行业风险" name="industry" />
            <el-tab-pane label="个股风险" name="specific" />
            <el-tab-pane label="时间分解" name="time" />
          </el-tabs>
        </div>
      </template>

      <!-- 因子风险归因 -->
      <div v-if="attributionTab === 'factor'" class="factor-attribution">
        <el-row :gutter="24">
          <el-col :span="16">
            <h4>因子风险贡献分解</h4>
            <div class="attribution-chart" ref="factorAttributionRef">
              <div class="chart-placeholder">因子风险归因图表</div>
            </div>
          </el-col>
          <el-col :span="8">
            <h4>风险因子排名</h4>
            <div class="factor-ranking">
              <div 
                v-for="factor in factorRiskRanking"
                :key="factor.name"
                class="factor-risk-item"
              >
                <div class="factor-info">
                  <span class="factor-name">{{ factor.name }}</span>
                  <span class="factor-risk">{{ (factor.contribution * 100).toFixed(2) }}%</span>
                </div>
                <el-progress 
                  :percentage="factor.contribution * 100" 
                  :color="factor.contribution > 0.1 ? '#f56c6c' : factor.contribution > 0.05 ? '#e6a23c' : '#67c23a'"
                  :show-text="false"
                  :stroke-width="6"
                />
              </div>
            </div>
          </el-col>
        </el-row>
      </div>

      <!-- 行业风险归因 -->
      <div v-if="attributionTab === 'industry'" class="industry-attribution">
        <el-row :gutter="24">
          <el-col :span="12">
            <h4>行业风险暴露</h4>
            <el-table :data="industryRiskExposure" border>
              <el-table-column prop="industry" label="行业" width="120" />
              <el-table-column prop="exposure" label="暴露度" width="120">
                <template #default="{ row }">
                  <el-progress 
                    :percentage="Math.abs(row.exposure) * 100" 
                    :color="row.exposure >= 0 ? '#67c23a' : '#f56c6c'"
                    :format="() => row.exposure.toFixed(3)"
                  />
                </template>
              </el-table-column>
              <el-table-column prop="risk_contribution" label="风险贡献" width="120">
                <template #default="{ row }">
                  {{ (row.risk_contribution * 100).toFixed(2) }}%
                </template>
              </el-table-column>
              <el-table-column prop="weight" label="组合权重" width="100">
                <template #default="{ row }">
                  {{ (row.weight * 100).toFixed(1) }}%
                </template>
              </el-table-column>
            </el-table>
          </el-col>
          <el-col :span="12">
            <h4>行业风险分布</h4>
            <div class="industry-risk-chart" ref="industryRiskChartRef">
              <div class="chart-placeholder">行业风险分布图</div>
            </div>
          </el-col>
        </el-row>
      </div>

      <!-- 个股风险归因 -->
      <div v-if="attributionTab === 'specific'" class="specific-attribution">
        <el-row :gutter="24">
          <el-col :span="16">
            <h4>个股特异风险</h4>
            <el-table :data="specificRiskData" border>
              <el-table-column prop="symbol" label="股票代码" width="100" />
              <el-table-column prop="name" label="股票名称" width="120" />
              <el-table-column prop="weight" label="权重" width="80">
                <template #default="{ row }">
                  {{ (row.weight * 100).toFixed(2) }}%
                </template>
              </el-table-column>
              <el-table-column prop="specific_risk" label="特异风险" width="120">
                <template #default="{ row }">
                  <span :class="[row.specific_risk > 0.3 ? 'high-risk' : row.specific_risk > 0.2 ? 'medium-risk' : 'low-risk']">
                    {{ (row.specific_risk * 100).toFixed(2) }}%
                  </span>
                </template>
              </el-table-column>
              <el-table-column prop="risk_contribution" label="风险贡献" width="120">
                <template #default="{ row }">
                  {{ (row.risk_contribution * 100).toFixed(2) }}%
                </template>
              </el-table-column>
              <el-table-column prop="residual_vol" label="残差波动" width="120">
                <template #default="{ row }">
                  {{ (row.residual_vol * 100).toFixed(2) }}%
                </template>
              </el-table-column>
              <el-table-column label="风险等级" width="100">
                <template #default="{ row }">
                  <el-tag :type="getSpecificRiskType(row.specific_risk)">
                    {{ getSpecificRiskLevel(row.specific_risk) }}
                  </el-tag>
                </template>
              </el-table-column>
            </el-table>
          </el-col>
          <el-col :span="8">
            <h4>个股风险分布</h4>
            <div class="specific-risk-summary">
              <div class="risk-summary-item">
                <span class="summary-label">高风险股票</span>
                <span class="summary-value high-risk">{{ highRiskStocks.length }}</span>
              </div>
              <div class="risk-summary-item">
                <span class="summary-label">中风险股票</span>
                <span class="summary-value medium-risk">{{ mediumRiskStocks.length }}</span>
              </div>
              <div class="risk-summary-item">
                <span class="summary-label">低风险股票</span>
                <span class="summary-value low-risk">{{ lowRiskStocks.length }}</span>
              </div>
            </div>
            <div class="specific-risk-chart" ref="specificRiskChartRef">
              <div class="chart-placeholder">个股风险分布图</div>
            </div>
          </el-col>
        </el-row>
      </div>

      <!-- 时间分解 -->
      <div v-if="attributionTab === 'time'" class="time-attribution">
        <h4>风险随时间变化分解</h4>
        <el-row :gutter="24">
          <el-col :span="12">
            <div class="time-decomposition-chart" ref="timeDecompositionRef">
              <div class="chart-placeholder">时间分解图表</div>
            </div>
          </el-col>
          <el-col :span="12">
            <div class="rolling-risk-chart" ref="rollingRiskRef">
              <div class="chart-placeholder">滚动风险图表</div>
            </div>
          </el-col>
        </el-row>
      </div>
    </el-card>

    <!-- 压力测试 -->
    <el-card class="stress-test-card">
      <template #header>
        <div class="stress-header">
          <span>压力测试</span>
          <div class="stress-controls">
            <el-button size="small" @click="runStressTest">
              <el-icon><Lightning /></el-icon>
              运行压力测试
            </el-button>
            <el-button size="small" @click="configStressScenarios">
              <el-icon><Setting /></el-icon>
              配置情景
            </el-button>
          </div>
        </div>
      </template>

      <el-row :gutter="24">
        <el-col :span="8">
          <h4>市场情景</h4>
          <div class="stress-scenarios">
            <div 
              v-for="scenario in stressScenarios"
              :key="scenario.name"
              class="scenario-item"
              @click="selectScenario(scenario)"
              :class="{ 'selected': selectedScenario?.name === scenario.name }"
            >
              <div class="scenario-header">
                <span class="scenario-name">{{ scenario.name }}</span>
                <el-tag :type="getScenarioType(scenario.severity)" size="small">
                  {{ scenario.severity }}
                </el-tag>
              </div>
              <div class="scenario-description">
                {{ scenario.description }}
              </div>
              <div class="scenario-params">
                <span>股票: {{ scenario.stock_shock }}%</span>
                <span>利率: {{ scenario.rate_shock }}bp</span>
              </div>
            </div>
          </div>
        </el-col>

        <el-col :span="16">
          <h4>压力测试结果</h4>
          <div v-if="stressTestResults.length === 0" class="no-stress-results">
            <el-empty description="请选择情景并运行压力测试" :image-size="80" />
          </div>
          <div v-else class="stress-results">
            <el-table :data="stressTestResults" border>
              <el-table-column prop="scenario" label="测试情景" width="120" />
              <el-table-column prop="portfolio_loss" label="组合损失" width="120">
                <template #default="{ row }">
                  <span :class="[row.portfolio_loss < 0 ? 'loss' : 'gain']">
                    {{ row.portfolio_loss.toFixed(2) }}%
                  </span>
                </template>
              </el-table-column>
              <el-table-column prop="benchmark_loss" label="基准损失" width="120">
                <template #default="{ row }">
                  <span :class="[row.benchmark_loss < 0 ? 'loss' : 'gain']">
                    {{ row.benchmark_loss.toFixed(2) }}%
                  </span>
                </template>
              </el-table-column>
              <el-table-column prop="relative_loss" label="相对损失" width="120">
                <template #default="{ row }">
                  <span :class="[row.relative_loss < 0 ? 'underperform' : 'outperform']">
                    {{ row.relative_loss.toFixed(2) }}%
                  </span>
                </template>
              </el-table-column>
              <el-table-column prop="var_breach" label="VaR突破" width="100">
                <template #default="{ row }">
                  <el-tag :type="row.var_breach ? 'danger' : 'success'" size="small">
                    {{ row.var_breach ? '是' : '否' }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="recovery_days" label="恢复天数" width="100" />
              <el-table-column label="风险等级" width="100">
                <template #default="{ row }">
                  <el-tag :type="getStressRiskType(row.portfolio_loss)">
                    {{ getStressRiskLevel(row.portfolio_loss) }}
                  </el-tag>
                </template>
              </el-table-column>
            </el-table>

            <div class="stress-summary">
              <h5>压力测试总结</h5>
              <el-row :gutter="16">
                <el-col :span="6">
                  <div class="summary-metric">
                    <span class="metric-label">最大损失</span>
                    <span class="metric-value loss">{{ maxLoss.toFixed(2) }}%</span>
                  </div>
                </el-col>
                <el-col :span="6">
                  <div class="summary-metric">
                    <span class="metric-label">平均损失</span>
                    <span class="metric-value">{{ avgLoss.toFixed(2) }}%</span>
                  </div>
                </el-col>
                <el-col :span="6">
                  <div class="summary-metric">
                    <span class="metric-label">VaR突破率</span>
                    <span class="metric-value">{{ varBreachRate.toFixed(1) }}%</span>
                  </div>
                </el-col>
                <el-col :span="6">
                  <div class="summary-metric">
                    <span class="metric-label">平均恢复期</span>
                    <span class="metric-value">{{ avgRecoveryDays.toFixed(0) }}天</span>
                  </div>
                </el-col>
              </el-row>
            </div>
          </div>
        </el-col>
      </el-row>
    </el-card>

    <!-- 风险监控告警 -->
    <el-card class="risk-monitoring-card">
      <template #header>
        <div class="monitoring-header">
          <span>风险监控告警</span>
          <div class="monitoring-controls">
            <el-switch 
              v-model="riskMonitoringEnabled" 
              active-text="启用监控"
              inactive-text="停用监控"
            />
            <el-button size="small" @click="configRiskThresholds">
              <el-icon><Setting /></el-icon>
              配置阈值
            </el-button>
          </div>
        </div>
      </template>

      <el-row :gutter="24">
        <el-col :span="16">
          <h4>实时风险指标</h4>
          <div class="real-time-metrics">
            <el-row :gutter="16">
              <el-col :span="6">
                <div class="rt-metric-card">
                  <div class="rt-metric-header">
                    <span>当日VaR</span>
                    <el-icon :class="['rt-status-icon', dailyVarStatus]">
                      <component :is="dailyVarStatus === 'normal' ? 'CircleCheck' : 'Warning'" />
                    </el-icon>
                  </div>
                  <div class="rt-metric-value">{{ realtimeMetrics.dailyVar.toFixed(2) }}%</div>
                  <div class="rt-metric-threshold">阈值: 2.5%</div>
                </div>
              </el-col>
              <el-col :span="6">
                <div class="rt-metric-card">
                  <div class="rt-metric-header">
                    <span>当日波动率</span>
                    <el-icon :class="['rt-status-icon', dailyVolStatus]">
                      <component :is="dailyVolStatus === 'normal' ? 'CircleCheck' : 'Warning'" />
                    </el-icon>
                  </div>
                  <div class="rt-metric-value">{{ realtimeMetrics.dailyVolatility.toFixed(2) }}%</div>
                  <div class="rt-metric-threshold">阈值: 3.0%</div>
                </div>
              </el-col>
              <el-col :span="6">
                <div class="rt-metric-card">
                  <div class="rt-metric-header">
                    <span>当日回撤</span>
                    <el-icon :class="['rt-status-icon', dailyDdStatus]">
                      <component :is="dailyDdStatus === 'normal' ? 'CircleCheck' : 'Warning'" />
                    </el-icon>
                  </div>
                  <div class="rt-metric-value">{{ realtimeMetrics.dailyDrawdown.toFixed(2) }}%</div>
                  <div class="rt-metric-threshold">阈值: 1.5%</div>
                </div>
              </el-col>
              <el-col :span="6">
                <div class="rt-metric-card">
                  <div class="rt-metric-header">
                    <span>集中度风险</span>
                    <el-icon :class="['rt-status-icon', concentrationStatus]">
                      <component :is="concentrationStatus === 'normal' ? 'CircleCheck' : 'Warning'" />
                    </el-icon>
                  </div>
                  <div class="rt-metric-value">{{ realtimeMetrics.concentrationRisk.toFixed(2) }}%</div>
                  <div class="rt-metric-threshold">阈值: 15.0%</div>
                </div>
              </el-col>
            </el-row>
          </div>
        </el-col>

        <el-col :span="8">
          <h4>风险告警历史</h4>
          <div class="risk-alerts">
            <div 
              v-for="alert in riskAlerts"
              :key="alert.id"
              class="alert-item"
              :class="alert.level"
            >
              <div class="alert-header">
                <el-icon>
                  <component :is="alert.level === 'critical' ? 'WarningFilled' : alert.level === 'warning' ? 'Warning' : 'InfoFilled'" />
                </el-icon>
                <span class="alert-title">{{ alert.title }}</span>
                <span class="alert-time">{{ formatTime(alert.timestamp) }}</span>
              </div>
              <div class="alert-content">{{ alert.message }}</div>
              <div class="alert-actions">
                <el-button size="small" text @click="viewAlertDetail(alert)">查看详情</el-button>
                <el-button size="small" text @click="acknowledgeAlert(alert)">确认</el-button>
              </div>
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
  Warning, Refresh, Download, Setting, TrendCharts, Lightning,
  CircleCheck, WarningFilled, InfoFilled
} from '@element-plus/icons-vue'

// 数据结构定义
interface Strategy {
  id: string
  name: string
  status: 'running' | 'completed' | 'failed'
}

interface RiskMetrics {
  volatility: number
  volatilityExcess: number
  var95: number
  cvar95: number
  beta: number
}

interface FactorRisk {
  name: string
  contribution: number
}

interface IndustryRisk {
  industry: string
  exposure: number
  risk_contribution: number
  weight: number
}

interface SpecificRisk {
  symbol: string
  name: string
  weight: number
  specific_risk: number
  risk_contribution: number
  residual_vol: number
}

interface StressScenario {
  name: string
  description: string
  severity: 'mild' | 'moderate' | 'severe'
  stock_shock: number
  rate_shock: number
}

interface StressTestResult {
  scenario: string
  portfolio_loss: number
  benchmark_loss: number
  relative_loss: number
  var_breach: boolean
  recovery_days: number
}

interface RiskAlert {
  id: string
  level: 'info' | 'warning' | 'critical'
  title: string
  message: string
  timestamp: string
  acknowledged: boolean
}

// 响应式数据
const loading = ref(false)
const analyzing = ref(false)
const selectedStrategy = ref('')
const timeRange = ref(['2023-01-01', '2023-12-31'])
const selectedBenchmark = ref('CSI300')
const selectedRiskModel = ref('barra_cne5')
const riskChartType = ref('volatility')
const attributionTab = ref('factor')
const selectedScenario = ref<StressScenario | null>(null)
const riskMonitoringEnabled = ref(true)

const availableStrategies = ref<Strategy[]>([
  { id: 'strategy_1', name: 'LightGBM多因子策略v3', status: 'running' },
  { id: 'strategy_2', name: 'LSTM时序预测策略', status: 'completed' },
  { id: 'strategy_3', name: '动量轮动策略', status: 'running' }
])

const riskMetrics = reactive<RiskMetrics>({
  volatility: 0,
  volatilityExcess: 0,
  var95: 0,
  cvar95: 0,
  beta: 0
})

const factorRiskRanking = ref<FactorRisk[]>([])
const industryRiskExposure = ref<IndustryRisk[]>([])
const specificRiskData = ref<SpecificRisk[]>([])

const stressScenarios = ref<StressScenario[]>([
  {
    name: '市场调整',
    description: '股市下跌10%，利率上升50bp',
    severity: 'mild',
    stock_shock: -10,
    rate_shock: 50
  },
  {
    name: '金融危机',
    description: '股市下跌30%，利率上升100bp',
    severity: 'moderate',
    stock_shock: -30,
    rate_shock: 100
  },
  {
    name: '极端崩盘',
    description: '股市下跌50%，利率上升200bp',
    severity: 'severe',
    stock_shock: -50,
    rate_shock: 200
  }
])

const stressTestResults = ref<StressTestResult[]>([])

const realtimeMetrics = reactive({
  dailyVar: 0,
  dailyVolatility: 0,
  dailyDrawdown: 0,
  concentrationRisk: 0
})

const riskAlerts = ref<RiskAlert[]>([])

// 计算属性
const highRiskStocks = computed(() => 
  specificRiskData.value.filter(stock => stock.specific_risk > 0.3)
)

const mediumRiskStocks = computed(() => 
  specificRiskData.value.filter(stock => stock.specific_risk > 0.2 && stock.specific_risk <= 0.3)
)

const lowRiskStocks = computed(() => 
  specificRiskData.value.filter(stock => stock.specific_risk <= 0.2)
)

const maxLoss = computed(() => {
  if (stressTestResults.value.length === 0) return 0
  return Math.min(...stressTestResults.value.map(r => r.portfolio_loss))
})

const avgLoss = computed(() => {
  if (stressTestResults.value.length === 0) return 0
  return stressTestResults.value.reduce((sum, r) => sum + r.portfolio_loss, 0) / stressTestResults.value.length
})

const varBreachRate = computed(() => {
  if (stressTestResults.value.length === 0) return 0
  const breaches = stressTestResults.value.filter(r => r.var_breach).length
  return breaches / stressTestResults.value.length * 100
})

const avgRecoveryDays = computed(() => {
  if (stressTestResults.value.length === 0) return 0
  return stressTestResults.value.reduce((sum, r) => sum + r.recovery_days, 0) / stressTestResults.value.length
})

const dailyVarStatus = computed(() => 
  realtimeMetrics.dailyVar > 2.5 ? 'warning' : 'normal'
)

const dailyVolStatus = computed(() => 
  realtimeMetrics.dailyVolatility > 3.0 ? 'warning' : 'normal'
)

const dailyDdStatus = computed(() => 
  Math.abs(realtimeMetrics.dailyDrawdown) > 1.5 ? 'warning' : 'normal'
)

const concentrationStatus = computed(() => 
  realtimeMetrics.concentrationRisk > 15.0 ? 'warning' : 'normal'
)

// 方法
const loadStrategyData = async () => {
  if (!selectedStrategy.value) return

  loading.value = true

  try {
    const response = await fetch('/api/v1/models/risk-analysis', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        strategy_id: selectedStrategy.value,
        start_time: timeRange.value[0],
        end_time: timeRange.value[1],
        benchmark: selectedBenchmark.value,
        risk_model: selectedRiskModel.value
      })
    })

    const result = await response.json()

    if (result.status === 'success') {
      updateRiskData(result.data)
      ElMessage.success('风险数据加载成功')
    } else {
      throw new Error(result.message || '加载风险数据失败')
    }
  } catch (error) {
    console.error('加载风险数据失败:', error)
    ElMessage.error('加载风险数据失败: ' + error.message)
    
    // 降级到示例数据
    generateSampleRiskData()
  } finally {
    loading.value = false
  }
}

const generateSampleRiskData = () => {
  // 生成示例风险数据
  riskMetrics.volatility = 18.5
  riskMetrics.volatilityExcess = 2.3
  riskMetrics.var95 = -2.1
  riskMetrics.cvar95 = -3.2
  riskMetrics.beta = 1.15

  factorRiskRanking.value = [
    { name: '市值因子', contribution: 0.25 },
    { name: '盈利因子', contribution: 0.18 },
    { name: '动量因子', contribution: 0.15 },
    { name: '价值因子', contribution: 0.12 },
    { name: '成长因子', contribution: 0.08 }
  ]

  industryRiskExposure.value = [
    { industry: '金融', exposure: 0.15, risk_contribution: 0.12, weight: 0.35 },
    { industry: '科技', exposure: -0.08, risk_contribution: 0.08, weight: 0.28 },
    { industry: '消费', exposure: 0.05, risk_contribution: 0.06, weight: 0.20 },
    { industry: '医药', exposure: 0.12, risk_contribution: 0.05, weight: 0.17 }
  ]

  specificRiskData.value = [
    { symbol: '000001.SZ', name: '平安银行', weight: 0.08, specific_risk: 0.25, risk_contribution: 0.02, residual_vol: 0.18 },
    { symbol: '600036.SH', name: '招商银行', weight: 0.07, specific_risk: 0.22, risk_contribution: 0.015, residual_vol: 0.16 },
    { symbol: '000858.SZ', name: '五粮液', weight: 0.06, specific_risk: 0.35, risk_contribution: 0.025, residual_vol: 0.28 }
  ]

  realtimeMetrics.dailyVar = 1.8
  realtimeMetrics.dailyVolatility = 2.1
  realtimeMetrics.dailyDrawdown = -0.8
  realtimeMetrics.concentrationRisk = 12.5

  riskAlerts.value = [
    {
      id: 'alert_1',
      level: 'warning',
      title: '波动率超限',
      message: '当日波动率达到2.8%，超过预设阈值',
      timestamp: '2024-01-15 14:30:00',
      acknowledged: false
    },
    {
      id: 'alert_2',
      level: 'info',
      title: '风险监控',
      message: 'VaR指标正常，风险可控',
      timestamp: '2024-01-15 09:00:00',
      acknowledged: true
    }
  ]
}

const updateRiskData = (data: any) => {
  if (data.risk_metrics) {
    Object.assign(riskMetrics, data.risk_metrics)
  }

  if (data.factor_attribution) {
    factorRiskRanking.value = data.factor_attribution
  }

  if (data.industry_exposure) {
    industryRiskExposure.value = data.industry_exposure
  }

  if (data.specific_risks) {
    specificRiskData.value = data.specific_risks
  }
}

const refreshAnalysis = () => {
  loadStrategyData()
}

const exportReport = () => {
  ElMessage.success('风险分析报告导出功能开发中')
}

const configRiskModel = () => {
  ElMessage.info('跳转到风险模型配置页面')
}

const runRiskAnalysis = () => {
  analyzing.value = true
  
  setTimeout(() => {
    analyzing.value = false
    ElMessage.success('风险分析完成')
  }, 3000)
}

const runStressTest = () => {
  if (!selectedScenario.value) {
    ElMessage.warning('请先选择压力测试情景')
    return
  }

  // 模拟压力测试
  const results = stressScenarios.value.map(scenario => ({
    scenario: scenario.name,
    portfolio_loss: scenario.stock_shock * 0.8 + Math.random() * 5,
    benchmark_loss: scenario.stock_shock + Math.random() * 3,
    relative_loss: Math.random() * 4 - 2,
    var_breach: Math.random() > 0.7,
    recovery_days: Math.floor(Math.random() * 30) + 5
  }))

  stressTestResults.value = results
  ElMessage.success('压力测试完成')
}

const selectScenario = (scenario: StressScenario) => {
  selectedScenario.value = scenario
}

const configStressScenarios = () => {
  ElMessage.info('配置压力测试情景')
}

const configRiskThresholds = () => {
  ElMessage.info('配置风险阈值')
}

const viewAlertDetail = (alert: RiskAlert) => {
  ElMessage.info(`查看告警详情: ${alert.title}`)
}

const acknowledgeAlert = (alert: RiskAlert) => {
  alert.acknowledged = true
  ElMessage.success('告警已确认')
}

const getStrategyTagType = (status: string) => {
  const types: Record<string, string> = {
    running: 'primary',
    completed: 'success',
    failed: 'danger'
  }
  return types[status] || 'default'
}

const getVarColor = (var95: number) => {
  if (var95 <= -5) return '#f56c6c'
  if (var95 <= -3) return '#e6a23c'
  return '#67c23a'
}

const getRiskLevelType = (cvar: number) => {
  if (cvar <= -5) return 'danger'
  if (cvar <= -3) return 'warning'
  return 'success'
}

const getRiskLevel = (cvar: number) => {
  if (cvar <= -5) return '高风险'
  if (cvar <= -3) return '中风险'
  return '低风险'
}

const getBetaColor = (beta: number) => {
  if (Math.abs(beta - 1) > 0.5) return '#f56c6c'
  if (Math.abs(beta - 1) > 0.2) return '#e6a23c'
  return '#67c23a'
}

const getScenarioType = (severity: string) => {
  const types: Record<string, string> = {
    mild: 'success',
    moderate: 'warning',
    severe: 'danger'
  }
  return types[severity] || 'default'
}

const getSpecificRiskType = (risk: number) => {
  if (risk > 0.3) return 'danger'
  if (risk > 0.2) return 'warning'
  return 'success'
}

const getSpecificRiskLevel = (risk: number) => {
  if (risk > 0.3) return '高'
  if (risk > 0.2) return '中'
  return '低'
}

const getStressRiskType = (loss: number) => {
  if (loss < -20) return 'danger'
  if (loss < -10) return 'warning'
  return 'success'
}

const getStressRiskLevel = (loss: number) => {
  if (loss < -20) return '极高'
  if (loss < -10) return '高'
  if (loss < -5) return '中'
  return '低'
}

const formatTime = (timestamp: string) => {
  return new Date(timestamp).toLocaleTimeString('zh-CN')
}

// 生命周期
onMounted(() => {
  if (availableStrategies.value.length > 0) {
    selectedStrategy.value = availableStrategies.value[0].id
    loadStrategyData()
  }
})
</script>

<style scoped>
.qlib-risk-analyzer {
  padding: 20px;
}

.analyzer-header {
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

.analysis-config {
  padding: 16px 0;
}

.strategy-option {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.risk-overview {
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
  background: linear-gradient(90deg, #f56c6c, #e6a23c);
}

.metric-comparison {
  margin-top: 8px;
  font-size: 12px;
}

.comparison-text {
  color: #909399;
}

.comparison-value.higher {
  color: #f56c6c;
}

.comparison-value.lower {
  color: #67c23a;
}

.var-indicator {
  margin-top: 12px;
}

.risk-level {
  margin-top: 8px;
}

.beta-chart {
  margin-top: 12px;
  display: flex;
  justify-content: center;
}

.risk-charts {
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

.risk-attribution-card {
  margin-bottom: 24px;
}

.attribution-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.attribution-tabs {
  margin: 0;
}

.factor-attribution,
.industry-attribution,
.specific-attribution,
.time-attribution {
  padding: 16px 0;
}

.factor-attribution h4,
.industry-attribution h4,
.specific-attribution h4,
.time-attribution h4 {
  margin-bottom: 16px;
  color: #303133;
}

.attribution-chart {
  height: 250px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px dashed #d9d9d9;
  border-radius: 6px;
}

.factor-ranking {
  max-height: 250px;
  overflow-y: auto;
}

.factor-risk-item {
  margin-bottom: 12px;
}

.factor-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: 4px;
  font-size: 12px;
}

.factor-name {
  color: #303133;
}

.factor-risk {
  color: #909399;
}

.industry-risk-chart,
.specific-risk-chart {
  height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px dashed #d9d9d9;
  border-radius: 6px;
}

.specific-risk-summary {
  margin-bottom: 16px;
}

.risk-summary-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
}

.summary-label {
  color: #606266;
  font-size: 14px;
}

.summary-value {
  font-weight: 600;
  font-size: 16px;
}

.summary-value.high-risk {
  color: #f56c6c;
}

.summary-value.medium-risk {
  color: #e6a23c;
}

.summary-value.low-risk {
  color: #67c23a;
}

.high-risk {
  color: #f56c6c;
}

.medium-risk {
  color: #e6a23c;
}

.low-risk {
  color: #67c23a;
}

.time-decomposition-chart,
.rolling-risk-chart {
  height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px dashed #d9d9d9;
  border-radius: 6px;
}

.stress-test-card {
  margin-bottom: 24px;
}

.stress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stress-controls {
  display: flex;
  gap: 8px;
}

.stress-scenarios {
  max-height: 400px;
  overflow-y: auto;
}

.scenario-item {
  padding: 12px;
  margin-bottom: 12px;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.3s;
}

.scenario-item:hover {
  border-color: #409eff;
  background: #f5f7fa;
}

.scenario-item.selected {
  border-color: #409eff;
  background: rgba(64, 158, 255, 0.1);
}

.scenario-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.scenario-name {
  font-weight: 600;
  color: #303133;
}

.scenario-description {
  font-size: 13px;
  color: #666;
  margin-bottom: 8px;
}

.scenario-params {
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: #909399;
}

.no-stress-results {
  text-align: center;
  padding: 40px 0;
}

.stress-results {
  margin-top: 16px;
}

.loss {
  color: #f56c6c;
}

.gain {
  color: #67c23a;
}

.underperform {
  color: #f56c6c;
}

.outperform {
  color: #67c23a;
}

.stress-summary {
  margin-top: 24px;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 6px;
}

.stress-summary h5 {
  margin-bottom: 16px;
  color: #303133;
}

.summary-metric {
  text-align: center;
  padding: 12px;
  background: white;
  border-radius: 6px;
}

.metric-label {
  display: block;
  font-size: 12px;
  color: #909399;
  margin-bottom: 4px;
}

.metric-value {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.metric-value.loss {
  color: #f56c6c;
}

.risk-monitoring-card {
  margin-bottom: 24px;
}

.monitoring-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.monitoring-controls {
  display: flex;
  gap: 16px;
  align-items: center;
}

.real-time-metrics {
  margin-bottom: 24px;
}

.rt-metric-card {
  padding: 16px;
  background: #f5f7fa;
  border-radius: 6px;
  border-left: 4px solid #409eff;
}

.rt-metric-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.rt-status-icon {
  font-size: 16px;
}

.rt-status-icon.normal {
  color: #67c23a;
}

.rt-status-icon.warning {
  color: #e6a23c;
}

.rt-metric-value {
  font-size: 20px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
}

.rt-metric-threshold {
  font-size: 12px;
  color: #909399;
}

.risk-alerts {
  max-height: 400px;
  overflow-y: auto;
}

.alert-item {
  padding: 12px;
  margin-bottom: 12px;
  border-radius: 6px;
  border-left: 4px solid #409eff;
}

.alert-item.critical {
  background: #fef0f0;
  border-left-color: #f56c6c;
}

.alert-item.warning {
  background: #fdf6ec;
  border-left-color: #e6a23c;
}

.alert-item.info {
  background: #f4f4f5;
  border-left-color: #909399;
}

.alert-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.alert-title {
  flex: 1;
  font-weight: 600;
  color: #303133;
}

.alert-time {
  font-size: 12px;
  color: #909399;
}

.alert-content {
  font-size: 13px;
  color: #666;
  margin-bottom: 8px;
}

.alert-actions {
  display: flex;
  gap: 8px;
}

@media (max-width: 768px) {
  .qlib-risk-analyzer {
    padding: 12px;
  }
  
  .header-content {
    flex-direction: column;
    gap: 16px;
  }
  
  .analysis-config .el-col {
    margin-bottom: 16px;
  }
  
  .risk-overview .el-col {
    margin-bottom: 16px;
  }
  
  .risk-charts .el-col {
    margin-bottom: 16px;
  }
  
  .real-time-metrics .el-col {
    margin-bottom: 16px;
  }
}
</style>