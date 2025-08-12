<template>
  <div class="strategy-backtest">
    <!-- 页面头部 -->
    <div class="page-header">
      <h1 class="page-title">
        <el-icon><TrendCharts /></el-icon>
        策略回测中心
      </h1>
      <p class="page-subtitle">专业的量化策略回测和性能分析平台</p>
    </div>

    <!-- 策略配置 -->
    <el-card class="config-section" v-if="!backtestRunning">
      <template #header>
        <div class="section-header">
          <span>回测配置</span>
          <el-tag type="info">步骤 1/3</el-tag>
        </div>
      </template>

      <el-form :model="backtestConfig" :rules="configRules" ref="configFormRef" label-width="120px">
        <!-- 基本配置 -->
        <div class="config-group">
          <h3>基本配置</h3>
          <el-row :gutter="24">
            <el-col :span="8">
              <el-form-item label="策略名称" prop="name">
                <el-input v-model="backtestConfig.name" placeholder="输入策略名称" />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="数据源">
                <el-select v-model="backtestConfig.dataSource" style="width: 100%">
                  <el-option label="本地数据" value="local" />
                  <el-option label="在线数据" value="online" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="股票池">
                <el-select v-model="backtestConfig.universe" style="width: 100%">
                  <el-option label="沪深300" value="HS300" />
                  <el-option label="中证500" value="ZZ500" />
                  <el-option label="中证1000" value="ZZ1000" />
                  <el-option label="全A股" value="ALL" />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>

          <el-row :gutter="24">
            <el-col :span="12">
              <el-form-item label="回测时间" prop="dateRange">
                <el-date-picker
                  v-model="backtestConfig.dateRange"
                  type="daterange"
                  start-placeholder="开始日期"
                  end-placeholder="结束日期"
                  format="YYYY-MM-DD"
                  value-format="YYYY-MM-DD"
                  style="width: 100%"
                />
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item label="初始资金">
                <el-input-number 
                  v-model="backtestConfig.initialCapital" 
                  :min="10000" 
                  :max="100000000"
                  :step="10000"
                  style="width: 100%"
                />
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item label="基准指数">
                <el-select v-model="backtestConfig.benchmark" style="width: 100%">
                  <el-option label="沪深300" value="000300" />
                  <el-option label="中证500" value="000905" />
                  <el-option label="上证50" value="000016" />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>
        </div>

        <!-- 策略配置 -->
        <div class="config-group">
          <h3>策略配置</h3>
          <el-row :gutter="24">
            <el-col :span="12">
              <el-form-item label="选择模型">
                <el-select 
                  v-model="backtestConfig.modelId" 
                  style="width: 100%"
                  @change="handleModelChange"
                >
                  <el-option 
                    v-for="model in availableModels" 
                    :key="model.id"
                    :label="model.name"
                    :value="model.id"
                  >
                    <div class="model-option">
                      <span class="model-name">{{ model.name }}</span>
                      <el-tag size="small" :type="getModelTagType(model.type)">
                        {{ model.type }}
                      </el-tag>
                    </div>
                  </el-option>
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item label="持仓数量">
                <el-input-number 
                  v-model="backtestConfig.topK" 
                  :min="10" 
                  :max="100"
                  style="width: 100%"
                />
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item label="调仓频率">
                <el-select v-model="backtestConfig.rebalanceFreq" style="width: 100%">
                  <el-option label="日调仓" value="daily" />
                  <el-option label="周调仓" value="weekly" />
                  <el-option label="月调仓" value="monthly" />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>
        </div>

        <!-- 交易配置 -->
        <div class="config-group">
          <h3>交易配置</h3>
          <el-row :gutter="24">
            <el-col :span="8">
              <el-form-item label="手续费率">
                <el-input-number 
                  v-model="backtestConfig.commission" 
                  :min="0" 
                  :max="0.01"
                  :step="0.0001"
                  :precision="4"
                  style="width: 100%"
                />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="印花税">
                <el-input-number 
                  v-model="backtestConfig.stampDuty" 
                  :min="0" 
                  :max="0.01"
                  :step="0.0001"
                  :precision="4"
                  style="width: 100%"
                />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="滑点">
                <el-input-number 
                  v-model="backtestConfig.slippage" 
                  :min="0" 
                  :max="0.01"
                  :step="0.0001"
                  :precision="4"
                  style="width: 100%"
                />
              </el-form-item>
            </el-col>
          </el-row>
        </div>

        <!-- 风险管理 -->
        <div class="config-group">
          <h3>风险管理</h3>
          <el-row :gutter="24">
            <el-col :span="8">
              <el-form-item label="最大回撤限制">
                <el-input-number 
                  v-model="backtestConfig.maxDrawdown" 
                  :min="0" 
                  :max="1"
                  :step="0.01"
                  :precision="2"
                  style="width: 100%"
                />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="单股最大权重">
                <el-input-number 
                  v-model="backtestConfig.maxWeight" 
                  :min="0" 
                  :max="0.5"
                  :step="0.01"
                  :precision="2"
                  style="width: 100%"
                />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="停损阈值">
                <el-input-number 
                  v-model="backtestConfig.stopLoss" 
                  :min="0" 
                  :max="0.5"
                  :step="0.01"
                  :precision="2"
                  style="width: 100%"
                />
              </el-form-item>
            </el-col>
          </el-row>
        </div>

        <div class="config-actions">
          <el-button @click="loadTemplate">
            <el-icon><Document /></el-icon>
            加载模板
          </el-button>
          <el-button @click="saveTemplate">
            <el-icon><DocumentAdd /></el-icon>
            保存模板
          </el-button>
          <el-button type="primary" @click="startBacktest" :loading="startingBacktest">
            <el-icon><VideoPlay /></el-icon>
            开始回测
          </el-button>
        </div>
      </el-form>
    </el-card>

    <!-- 回测执行中 -->
    <div v-if="backtestRunning" class="backtest-execution">
      <el-card class="execution-card">
        <template #header>
          <div class="execution-header">
            <span>回测执行中...</span>
            <el-button @click="stopBacktest" type="danger" size="small">
              <el-icon><Close /></el-icon>
              停止回测
            </el-button>
          </div>
        </template>

        <div class="execution-content">
          <div class="progress-section">
            <h3>执行进度</h3>
            <el-progress 
              :percentage="backtestProgress" 
              :stroke-width="12"
              text-inside
            />
            <div class="progress-info">
              <span>当前日期: {{ currentDate }}</span>
              <span>已完成: {{ completedDays }} / {{ totalDays }} 天</span>
              <span>预计剩余: {{ estimatedRemaining }}</span>
            </div>
          </div>

          <div class="realtime-metrics">
            <h3>实时指标</h3>
            <el-row :gutter="24">
              <el-col :span="6">
                <el-statistic title="累计收益率" :value="realtimeMetrics.totalReturn" :precision="2" suffix="%" />
              </el-col>
              <el-col :span="6">
                <el-statistic title="基准收益率" :value="realtimeMetrics.benchmarkReturn" :precision="2" suffix="%" />
              </el-col>
              <el-col :span="6">
                <el-statistic title="超额收益" :value="realtimeMetrics.excessReturn" :precision="2" suffix="%" />
              </el-col>
              <el-col :span="6">
                <el-statistic title="最大回撤" :value="realtimeMetrics.maxDrawdown" :precision="2" suffix="%" />
              </el-col>
            </el-row>
          </div>

          <div class="execution-logs">
            <h3>执行日志</h3>
            <div class="logs-container">
              <div v-for="log in executionLogs" :key="log.id" class="log-entry">
                <span class="log-time">{{ formatTime(log.timestamp) }}</span>
                <span class="log-message">{{ log.message }}</span>
              </div>
            </div>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 回测结果 -->
    <div v-if="backtestCompleted" class="backtest-results">
      <el-card class="results-overview">
        <template #header>
          <div class="results-header">
            <span>回测结果 - {{ completedBacktest?.name }}</span>
            <div class="header-actions">
              <el-button @click="exportResults">
                <el-icon><Download /></el-icon>
                导出报告
              </el-button>
              <el-button @click="shareResults">
                <el-icon><Share /></el-icon>
                分享结果
              </el-button>
              <el-button type="primary" @click="deployStrategy">
                <el-icon><Upload /></el-icon>
                部署策略
              </el-button>
            </div>
          </div>
        </template>

        <!-- 关键指标 -->
        <div class="key-metrics">
          <el-row :gutter="24">
            <el-col :span="4">
              <div class="metric-card">
                <div class="metric-value positive">{{ results.totalReturn.toFixed(2) }}%</div>
                <div class="metric-label">总收益率</div>
              </div>
            </el-col>
            <el-col :span="4">
              <div class="metric-card">
                <div class="metric-value">{{ results.sharpeRatio.toFixed(2) }}</div>
                <div class="metric-label">夏普比率</div>
              </div>
            </el-col>
            <el-col :span="4">
              <div class="metric-card">
                <div class="metric-value negative">{{ (results.maxDrawdown * 100).toFixed(2) }}%</div>
                <div class="metric-label">最大回撤</div>
              </div>
            </el-col>
            <el-col :span="4">
              <div class="metric-card">
                <div class="metric-value">{{ (results.volatility * 100).toFixed(2) }}%</div>
                <div class="metric-label">年化波动率</div>
              </div>
            </el-col>
            <el-col :span="4">
              <div class="metric-card">
                <div class="metric-value">{{ results.winRate.toFixed(1) }}%</div>
                <div class="metric-label">胜率</div>
              </div>
            </el-col>
            <el-col :span="4">
              <div class="metric-card">
                <div class="metric-value">{{ results.calmarRatio.toFixed(2) }}</div>
                <div class="metric-label">卡玛比率</div>
              </div>
            </el-col>
          </el-row>
        </div>

        <!-- 详细分析 -->
        <el-tabs v-model="activeResultTab" class="results-tabs">
          <el-tab-pane label="收益曲线" name="returns">
            <div ref="returnsChart" class="chart-container large"></div>
          </el-tab-pane>

          <el-tab-pane label="回撤分析" name="drawdown">
            <div ref="drawdownChart" class="chart-container large"></div>
          </el-tab-pane>

          <el-tab-pane label="持仓分析" name="positions">
            <div class="positions-analysis">
              <div ref="positionsChart" class="chart-container"></div>
              <el-table :data="positionsData" size="small" max-height="300">
                <el-table-column prop="symbol" label="股票代码" width="120" />
                <el-table-column prop="name" label="股票名称" width="150" />
                <el-table-column prop="weight" label="权重" width="100">
                  <template #default="{ row }">
                    {{ (row.weight * 100).toFixed(2) }}%
                  </template>
                </el-table-column>
                <el-table-column prop="return" label="收益率" width="100">
                  <template #default="{ row }">
                    <span :class="row.return >= 0 ? 'positive' : 'negative'">
                      {{ (row.return * 100).toFixed(2) }}%
                    </span>
                  </template>
                </el-table-column>
                <el-table-column prop="holdingDays" label="持有天数" width="100" />
              </el-table>
            </div>
          </el-tab-pane>

          <el-tab-pane label="交易记录" name="trades">
            <el-table :data="tradesData" size="small" max-height="400">
              <el-table-column prop="date" label="交易日期" width="120" />
              <el-table-column prop="symbol" label="股票代码" width="120" />
              <el-table-column prop="action" label="操作" width="80">
                <template #default="{ row }">
                  <el-tag :type="row.action === 'buy' ? 'success' : 'danger'" size="small">
                    {{ row.action === 'buy' ? '买入' : '卖出' }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="price" label="成交价格" width="100">
                <template #default="{ row }">
                  ¥{{ row.price.toFixed(2) }}
                </template>
              </el-table-column>
              <el-table-column prop="quantity" label="数量" width="100" />
              <el-table-column prop="amount" label="金额" width="120">
                <template #default="{ row }">
                  ¥{{ row.amount.toFixed(2) }}
                </template>
              </el-table-column>
              <el-table-column prop="commission" label="手续费" width="100">
                <template #default="{ row }">
                  ¥{{ row.commission.toFixed(2) }}
                </template>
              </el-table-column>
            </el-table>
          </el-tab-pane>

          <el-tab-pane label="风险分析" name="risk">
            <div class="risk-analysis">
              <el-row :gutter="24">
                <el-col :span="12">
                  <el-card class="risk-metrics-card">
                    <template #header>
                      <span>风险指标</span>
                    </template>
                    <el-descriptions :column="1" border>
                      <el-descriptions-item label="VaR (95%)">
                        {{ (results.var95 * 100).toFixed(2) }}%
                      </el-descriptions-item>
                      <el-descriptions-item label="CVaR (95%)">
                        {{ (results.cvar95 * 100).toFixed(2) }}%
                      </el-descriptions-item>
                      <el-descriptions-item label="下行风险">
                        {{ (results.downsideRisk * 100).toFixed(2) }}%
                      </el-descriptions-item>
                      <el-descriptions-item label="最大连续亏损天数">
                        {{ results.maxConsecutiveLosses }} 天
                      </el-descriptions-item>
                      <el-descriptions-item label="Beta系数">
                        {{ results.beta.toFixed(3) }}
                      </el-descriptions-item>
                    </el-descriptions>
                  </el-card>
                </el-col>
                <el-col :span="12">
                  <div ref="riskChart" class="chart-container"></div>
                </el-col>
              </el-row>
            </div>
          </el-tab-pane>
        </el-tabs>
      </el-card>

      <div class="actions-section">
        <el-button @click="restartBacktest">
          <el-icon><Refresh /></el-icon>
          重新回测
        </el-button>
        <el-button @click="optimizeStrategy">
          <el-icon><MagicStick /></el-icon>
          策略优化
        </el-button>
        <el-button @click="compareResults">
          <el-icon><DataAnalysis /></el-icon>
          结果对比
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  TrendCharts, VideoPlay, Close, Download, Share, Upload,
  Document, DocumentAdd, Refresh, MagicStick, DataAnalysis
} from '@element-plus/icons-vue'

const router = useRouter()

// 响应式数据
const backtestRunning = ref(false)
const backtestCompleted = ref(false)
const startingBacktest = ref(false)
const backtestProgress = ref(0)
const activeResultTab = ref('returns')
const currentDate = ref('2023-01-01')
const completedDays = ref(0)
const totalDays = ref(365)

// 表单引用
const configFormRef = ref()

// 回测配置
const backtestConfig = reactive({
  name: '',
  dataSource: 'local',
  universe: 'HS300',
  dateRange: ['2022-01-01', '2023-12-31'] as [string, string],
  initialCapital: 1000000,
  benchmark: '000300',
  modelId: '',
  topK: 30,
  rebalanceFreq: 'monthly',
  commission: 0.0003,
  stampDuty: 0.001,
  slippage: 0.0001,
  maxDrawdown: 0.3,
  maxWeight: 0.1,
  stopLoss: 0.2
})

// 表单验证规则
const configRules = {
  name: [
    { required: true, message: '请输入策略名称', trigger: 'blur' }
  ],
  dateRange: [
    { required: true, message: '请选择回测时间范围', trigger: 'change' }
  ]
}

// 可用模型
const availableModels = ref([
  {
    id: 'model_1',
    name: 'LightGBM_Alpha_v3.2',
    type: 'LightGBM',
    accuracy: 87.5
  },
  {
    id: 'model_2',
    name: 'XGBoost_ProFactor_v2.1',
    type: 'XGBoost',
    accuracy: 85.8
  },
  {
    id: 'model_3',
    name: 'LSTM_TimeSeries_v1.5',
    type: 'LSTM',
    accuracy: 83.2
  }
])

// 实时指标
const realtimeMetrics = reactive({
  totalReturn: 0,
  benchmarkReturn: 0,
  excessReturn: 0,
  maxDrawdown: 0
})

// 执行日志
const executionLogs = ref([
  { id: 1, timestamp: new Date(), message: '开始执行回测...' },
  { id: 2, timestamp: new Date(), message: '加载数据完成' },
  { id: 3, timestamp: new Date(), message: '模型预测中...' }
])

// 回测结果
const results = reactive({
  totalReturn: 25.8,
  sharpeRatio: 1.45,
  maxDrawdown: -0.12,
  volatility: 0.18,
  winRate: 62.5,
  calmarRatio: 2.15,
  var95: -0.025,
  cvar95: -0.035,
  downsideRisk: 0.12,
  maxConsecutiveLosses: 7,
  beta: 0.85
})

const completedBacktest = ref(null)
const positionsData = ref([])
const tradesData = ref([])

// 计算属性
const estimatedRemaining = computed(() => {
  if (backtestProgress.value === 0) return '--'
  const remaining = (100 - backtestProgress.value) / backtestProgress.value * (Date.now() - startTime.value) / 1000
  return `${Math.round(remaining / 60)} 分钟`
})

const startTime = ref(0)

// 方法
const getModelTagType = (type: string) => {
  switch (type) {
    case 'LightGBM': return 'success'
    case 'XGBoost': return 'warning'
    case 'LSTM': return 'info'
    default: return 'info'
  }
}

const handleModelChange = (modelId: string) => {
  const model = availableModels.value.find(m => m.id === modelId)
  if (model) {
    ElMessage.info(`已选择模型: ${model.name}`)
  }
}

const loadTemplate = () => {
  ElMessage.info('加载配置模板功能开发中')
}

const saveTemplate = () => {
  ElMessage.success('配置模板已保存')
}

const startBacktest = async () => {
  try {
    await configFormRef.value.validate()
    
    startingBacktest.value = true
    
    // 模拟启动过程
    setTimeout(() => {
      startingBacktest.value = false
      backtestRunning.value = true
      startTime.value = Date.now()
      
      // 模拟回测进度
      simulateBacktest()
    }, 2000)
    
  } catch (error) {
    ElMessage.error('请完善配置信息')
  }
}

const simulateBacktest = () => {
  const interval = setInterval(() => {
    backtestProgress.value += Math.random() * 5
    completedDays.value = Math.floor(totalDays.value * backtestProgress.value / 100)
    
    // 更新实时指标
    realtimeMetrics.totalReturn += (Math.random() - 0.4) * 0.5
    realtimeMetrics.benchmarkReturn += (Math.random() - 0.45) * 0.3
    realtimeMetrics.excessReturn = realtimeMetrics.totalReturn - realtimeMetrics.benchmarkReturn
    realtimeMetrics.maxDrawdown = Math.min(realtimeMetrics.maxDrawdown, -Math.random() * 15)
    
    // 添加日志
    if (Math.random() < 0.3) {
      executionLogs.value.push({
        id: Date.now(),
        timestamp: new Date(),
        message: `处理日期: ${currentDate.value}, 预测股票数量: ${Math.floor(Math.random() * 50 + 20)}`
      })
      
      // 保持日志数量
      if (executionLogs.value.length > 10) {
        executionLogs.value = executionLogs.value.slice(-10)
      }
    }
    
    if (backtestProgress.value >= 100) {
      clearInterval(interval)
      backtestProgress.value = 100
      backtestRunning.value = false
      backtestCompleted.value = true
      
      // 生成结果数据
      generateResultsData()
      
      ElMessage.success('回测完成！')
    }
  }, 500)
}

const stopBacktest = async () => {
  try {
    await ElMessageBox.confirm('确定要停止当前回测吗？', '确认停止', {
      type: 'warning'
    })
    
    backtestRunning.value = false
    ElMessage.warning('回测已停止')
  } catch {
    // 用户取消
  }
}

const generateResultsData = () => {
  // 生成持仓数据
  positionsData.value = [
    { symbol: '000001', name: '平安银行', weight: 0.05, return: 0.12, holdingDays: 30 },
    { symbol: '000002', name: '万科A', weight: 0.04, return: -0.08, holdingDays: 25 },
    { symbol: '600036', name: '招商银行', weight: 0.06, return: 0.15, holdingDays: 35 }
  ]
  
  // 生成交易数据
  tradesData.value = [
    {
      date: '2023-01-15',
      symbol: '000001',
      action: 'buy',
      price: 12.34,
      quantity: 1000,
      amount: 12340,
      commission: 3.70
    },
    {
      date: '2023-02-10',
      symbol: '000002',
      action: 'sell',
      price: 25.67,
      quantity: 500,
      amount: 12835,
      commission: 3.85
    }
  ]
  
  completedBacktest.value = { name: backtestConfig.name }
}

const formatTime = (timestamp: Date) => {
  return timestamp.toLocaleTimeString('zh-CN')
}

const exportResults = () => {
  ElMessage.success('报告导出已开始')
}

const shareResults = () => {
  ElMessage.info('分享功能开发中')
}

const deployStrategy = () => {
  router.push('/deployment')
}

const restartBacktest = () => {
  backtestRunning.value = false
  backtestCompleted.value = false
  backtestProgress.value = 0
  Object.assign(realtimeMetrics, {
    totalReturn: 0,
    benchmarkReturn: 0,
    excessReturn: 0,
    maxDrawdown: 0
  })
}

const optimizeStrategy = () => {
  ElMessage.info('策略优化功能开发中')
}

const compareResults = () => {
  ElMessage.info('结果对比功能开发中')
}

// 生命周期
onMounted(() => {
  // 初始化
})
</script>

<style scoped>
.strategy-backtest {
  padding: 24px;
  max-width: 1400px;
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

.config-section {
  margin-bottom: 24px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.config-group {
  margin-bottom: 32px;
  padding: 24px;
  background: #f8f9fa;
  border-radius: 8px;
}

.config-group h3 {
  margin: 0 0 20px 0;
  color: #303133;
  font-size: 16px;
  font-weight: 600;
  border-bottom: 2px solid #409eff;
  padding-bottom: 8px;
}

.model-option {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.model-name {
  flex: 1;
}

.config-actions {
  text-align: center;
  padding-top: 24px;
  border-top: 1px solid #e4e7ed;
  display: flex;
  gap: 16px;
  justify-content: center;
}

.backtest-execution {
  margin-bottom: 24px;
}

.execution-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.execution-content {
  display: flex;
  flex-direction: column;
  gap: 32px;
}

.progress-section h3,
.realtime-metrics h3,
.execution-logs h3 {
  margin: 0 0 16px 0;
  color: #303133;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  margin-top: 12px;
  font-size: 14px;
  color: #606266;
}

.logs-container {
  height: 200px;
  overflow-y: auto;
  background: #1e1e1e;
  color: #e8e8e8;
  padding: 16px;
  border-radius: 6px;
  font-family: 'Monaco', 'Menlo', monospace;
  font-size: 13px;
}

.log-entry {
  margin-bottom: 4px;
  display: flex;
  gap: 12px;
}

.log-time {
  color: #666;
  flex-shrink: 0;
}

.log-message {
  flex: 1;
}

.backtest-results {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.results-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.key-metrics {
  margin-bottom: 32px;
}

.metric-card {
  text-align: center;
  padding: 20px;
  background: linear-gradient(135deg, #f0f8ff 0%, #e8f4fd 100%);
  border-radius: 8px;
  border: 1px solid #d4e4fd;
}

.metric-value {
  font-size: 24px;
  font-weight: 600;
  margin-bottom: 8px;
  color: #303133;
}

.metric-value.positive {
  color: #67c23a;
}

.metric-value.negative {
  color: #f56c6c;
}

.metric-label {
  font-size: 14px;
  color: #606266;
}

.results-tabs {
  margin-top: 24px;
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

.positions-analysis {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.positive {
  color: #67c23a;
}

.negative {
  color: #f56c6c;
}

.risk-analysis {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.risk-metrics-card {
  height: fit-content;
}

.actions-section {
  display: flex;
  gap: 16px;
  justify-content: center;
  padding: 24px;
  background: #f8f9fa;
  border-radius: 8px;
}

@media (max-width: 768px) {
  .strategy-backtest {
    padding: 16px;
  }
  
  .config-group {
    padding: 16px;
  }
  
  .config-actions,
  .actions-section {
    flex-direction: column;
  }
  
  .header-actions {
    flex-direction: column;
    gap: 8px;
  }
  
  .results-header {
    flex-direction: column;
    gap: 16px;
  }
  
  .progress-info {
    flex-direction: column;
    gap: 8px;
  }
}
</style>