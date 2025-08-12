<template>
  <div class="strategy-deployment">
    <!-- 页面头部 -->
    <div class="page-header">
      <h1 class="page-title">
        <el-icon><Upload /></el-icon>
        策略部署中心
      </h1>
      <p class="page-subtitle">安全、专业的量化策略实盘部署平台</p>
    </div>

    <!-- 部署向导 -->
    <el-card class="deployment-wizard" v-if="!deploymentCompleted">
      <template #header>
        <div class="wizard-header">
          <span>策略部署向导</span>
          <el-steps :active="currentStep" align-center class="deployment-steps">
            <el-step title="选择策略" icon="DocumentChecked" />
            <el-step title="配置部署" icon="Setting" />
            <el-step title="风险确认" icon="Warning" />
            <el-step title="启动部署" icon="VideoPlay" />
          </el-steps>
        </div>
      </template>

      <!-- 步骤 1: 选择策略 -->
      <div v-if="currentStep === 0" class="step-content">
        <h3>选择要部署的策略</h3>
        <div class="strategy-selection">
          <el-row :gutter="24">
            <el-col :span="8" v-for="strategy in availableStrategies" :key="strategy.id">
              <div 
                :class="['strategy-card', { selected: deploymentConfig.strategyId === strategy.id }]"
                @click="selectStrategy(strategy.id)"
              >
                <div class="strategy-header">
                  <div class="strategy-name">{{ strategy.name }}</div>
                  <el-tag :type="getStrategyTagType(strategy.type)" size="small">
                    {{ strategy.type }}
                  </el-tag>
                </div>
                
                <div class="strategy-metrics">
                  <div class="metric">
                    <span class="metric-label">回测收益率</span>
                    <span class="metric-value positive">{{ strategy.backtestReturn.toFixed(2) }}%</span>
                  </div>
                  <div class="metric">
                    <span class="metric-label">夏普比率</span>
                    <span class="metric-value">{{ strategy.sharpeRatio.toFixed(2) }}</span>
                  </div>
                  <div class="metric">
                    <span class="metric-label">最大回撤</span>
                    <span class="metric-value negative">{{ (strategy.maxDrawdown * 100).toFixed(2) }}%</span>
                  </div>
                </div>
                
                <div class="strategy-status">
                  <el-tag v-if="strategy.status === 'ready'" type="success" size="small">
                    可部署
                  </el-tag>
                  <el-tag v-else-if="strategy.status === 'deployed'" type="warning" size="small">
                    已部署
                  </el-tag>
                  <el-tag v-else type="info" size="small">
                    开发中
                  </el-tag>
                </div>
              </div>
            </el-col>
          </el-row>
        </div>
      </div>

      <!-- 步骤 2: 配置部署 -->
      <div v-if="currentStep === 1" class="step-content">
        <h3>部署配置</h3>
        <el-form :model="deploymentConfig" label-width="120px">
          <!-- 基本配置 -->
          <div class="config-section">
            <h4>基本配置</h4>
            <el-row :gutter="24">
              <el-col :span="8">
                <el-form-item label="部署名称" required>
                  <el-input v-model="deploymentConfig.name" placeholder="输入部署名称" />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="部署环境">
                  <el-select v-model="deploymentConfig.environment" style="width: 100%">
                    <el-option label="模拟交易" value="simulation" />
                    <el-option label="实盘交易" value="live" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="启动资金">
                  <el-input-number 
                    v-model="deploymentConfig.initialCapital" 
                    :min="10000" 
                    :max="100000000"
                    :step="10000"
                    style="width: 100%"
                  />
                </el-form-item>
              </el-col>
            </el-row>
          </div>

          <!-- 交易配置 -->
          <div class="config-section">
            <h4>交易配置</h4>
            <el-row :gutter="24">
              <el-col :span="6">
                <el-form-item label="券商接口">
                  <el-select v-model="deploymentConfig.broker" style="width: 100%">
                    <el-option label="模拟券商" value="mock" />
                    <el-option label="华泰证券" value="huatai" />
                    <el-option label="中信证券" value="zhongxin" />
                    <el-option label="招商证券" value="zhaoshang" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="6">
                <el-form-item label="调仓频率">
                  <el-select v-model="deploymentConfig.rebalanceFreq" style="width: 100%">
                    <el-option label="日调仓" value="daily" />
                    <el-option label="周调仓" value="weekly" />
                    <el-option label="月调仓" value="monthly" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="6">
                <el-form-item label="持仓数量">
                  <el-input-number 
                    v-model="deploymentConfig.positionCount" 
                    :min="5" 
                    :max="50"
                    style="width: 100%"
                  />
                </el-form-item>
              </el-col>
              <el-col :span="6">
                <el-form-item label="单股权重上限">
                  <el-input-number 
                    v-model="deploymentConfig.maxSingleWeight" 
                    :min="0.01" 
                    :max="0.2"
                    :step="0.01"
                    :precision="2"
                    style="width: 100%"
                  />
                </el-form-item>
              </el-col>
            </el-row>
          </div>

          <!-- 风险控制 -->
          <div class="config-section">
            <h4>风险控制</h4>
            <el-row :gutter="24">
              <el-col :span="8">
                <el-form-item label="止损阈值">
                  <el-input-number 
                    v-model="deploymentConfig.stopLossThreshold" 
                    :min="0.05" 
                    :max="0.3"
                    :step="0.01"
                    :precision="2"
                    style="width: 100%"
                  />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="最大回撤限制">
                  <el-input-number 
                    v-model="deploymentConfig.maxDrawdownLimit" 
                    :min="0.1" 
                    :max="0.5"
                    :step="0.01"
                    :precision="2"
                    style="width: 100%"
                  />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="日交易限额">
                  <el-input-number 
                    v-model="deploymentConfig.dailyTradingLimit" 
                    :min="1000" 
                    :max="1000000"
                    :step="1000"
                    style="width: 100%"
                  />
                </el-form-item>
              </el-col>
            </el-row>

            <el-row :gutter="24">
              <el-col :span="12">
                <el-form-item label="监控设置">
                  <el-checkbox-group v-model="deploymentConfig.monitoring">
                    <el-checkbox label="realtime">实时监控</el-checkbox>
                    <el-checkbox label="alerts">异常告警</el-checkbox>
                    <el-checkbox label="daily_report">日报推送</el-checkbox>
                    <el-checkbox label="weekly_report">周报推送</el-checkbox>
                  </el-checkbox-group>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="通知方式">
                  <el-checkbox-group v-model="deploymentConfig.notifications">
                    <el-checkbox label="email">邮件</el-checkbox>
                    <el-checkbox label="sms">短信</el-checkbox>
                    <el-checkbox label="wechat">微信</el-checkbox>
                    <el-checkbox label="app">APP推送</el-checkbox>
                  </el-checkbox-group>
                </el-form-item>
              </el-col>
            </el-row>
          </div>
        </el-form>
      </div>

      <!-- 步骤 3: 风险确认 -->
      <div v-if="currentStep === 2" class="step-content">
        <h3>风险确认与免责声明</h3>
        <div class="risk-warnings">
          <el-alert
            title="重要风险提示"
            type="warning"
            :closable="false"
          >
            <template #default>
              <div class="risk-content">
                <h4>请仔细阅读以下风险提示：</h4>
                <ul class="risk-list">
                  <li>量化交易存在本金损失风险，过往业绩不代表未来收益</li>
                  <li>市场环境变化可能导致策略失效或表现不佳</li>
                  <li>技术故障、网络中断等可能影响交易执行</li>
                  <li>流动性风险可能导致无法及时止损</li>
                  <li>监管政策变化可能影响策略合规性</li>
                </ul>
              </div>
            </template>
          </el-alert>

          <div class="strategy-risks">
            <h4>策略风险评估</h4>
            <el-descriptions :column="2" border>
              <el-descriptions-item label="风险等级">
                <el-tag type="danger">高风险</el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="预期最大回撤">
                {{ (selectedStrategy?.maxDrawdown * 100).toFixed(2) }}%
              </el-descriptions-item>
              <el-descriptions-item label="历史最大亏损">
                {{ (deploymentConfig.initialCapital * (selectedStrategy?.maxDrawdown || 0.15)).toFixed(0) }} 元
              </el-descriptions-item>
              <el-descriptions-item label="适合投资者">
                专业投资者
              </el-descriptions-item>
            </el-descriptions>
          </div>

          <div class="confirmations">
            <el-checkbox v-model="riskConfirmations.understand">
              我已充分了解量化交易的风险特性
            </el-checkbox>
            <el-checkbox v-model="riskConfirmations.accept">
              我愿意承担投资损失风险
            </el-checkbox>
            <el-checkbox v-model="riskConfirmations.professional">
              我具备相应的投资经验和风险识别能力
            </el-checkbox>
            <el-checkbox v-model="riskConfirmations.disclaimer">
              我已阅读并同意《策略部署免责声明》
            </el-checkbox>
          </div>
        </div>
      </div>

      <!-- 步骤 4: 启动部署 -->
      <div v-if="currentStep === 3" class="step-content">
        <h3>部署确认</h3>
        <div class="deployment-summary">
          <el-descriptions title="部署配置摘要" :column="2" border>
            <el-descriptions-item label="策略名称">
              {{ selectedStrategy?.name }}
            </el-descriptions-item>
            <el-descriptions-item label="部署名称">
              {{ deploymentConfig.name }}
            </el-descriptions-item>
            <el-descriptions-item label="部署环境">
              <el-tag :type="deploymentConfig.environment === 'live' ? 'danger' : 'success'">
                {{ deploymentConfig.environment === 'live' ? '实盘交易' : '模拟交易' }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="启动资金">
              ¥{{ deploymentConfig.initialCapital.toLocaleString() }}
            </el-descriptions-item>
            <el-descriptions-item label="调仓频率">
              {{ getFrequencyText(deploymentConfig.rebalanceFreq) }}
            </el-descriptions-item>
            <el-descriptions-item label="持仓数量">
              {{ deploymentConfig.positionCount }} 只股票
            </el-descriptions-item>
          </el-descriptions>

          <div class="final-confirmation">
            <el-alert
              title="最终确认"
              type="info"
              :closable="false"
            >
              请再次确认所有配置信息，点击"启动部署"后策略将开始运行
            </el-alert>
          </div>
        </div>
      </div>

      <!-- 向导操作按钮 -->
      <div class="wizard-actions">
        <el-button v-if="currentStep > 0" @click="prevStep">
          <el-icon><ArrowLeft /></el-icon>
          上一步
        </el-button>
        
        <el-button 
          v-if="currentStep < 3" 
          type="primary" 
          @click="nextStep"
          :disabled="!canProceed"
        >
          下一步
          <el-icon><ArrowRight /></el-icon>
        </el-button>
        
        <el-button 
          v-if="currentStep === 3" 
          type="danger" 
          @click="startDeployment"
          :loading="deploying"
          :disabled="!allRiskConfirmed"
        >
          <el-icon><VideoPlay /></el-icon>
          启动部署
        </el-button>
      </div>
    </el-card>

    <!-- 部署状态监控 -->
    <div v-if="deploymentCompleted || deployments.length > 0" class="deployments-management">
      <!-- 活跃部署概览 -->
      <el-card class="active-deployments">
        <template #header>
          <div class="deployments-header">
            <span>活跃部署</span>
            <el-button @click="refreshDeployments">
              <el-icon><Refresh /></el-icon>
              刷新状态
            </el-button>
          </div>
        </template>

        <div class="deployments-grid">
          <div v-for="deployment in deployments" :key="deployment.id" class="deployment-card">
            <div class="deployment-header">
              <div class="deployment-info">
                <div class="deployment-name">{{ deployment.name }}</div>
                <el-tag :type="getDeploymentStatusType(deployment.status)" size="small">
                  {{ getDeploymentStatusText(deployment.status) }}
                </el-tag>
              </div>
              <div class="deployment-actions">
                <el-button size="small" @click="viewDeploymentDetail(deployment)">详情</el-button>
                <el-dropdown @command="(cmd) => handleDeploymentAction(cmd, deployment)">
                  <el-button size="small">
                    <el-icon><MoreFilled /></el-icon>
                  </el-button>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item 
                        command="pause" 
                        :disabled="deployment.status !== 'running'"
                      >
                        暂停
                      </el-dropdown-item>
                      <el-dropdown-item 
                        command="resume" 
                        :disabled="deployment.status !== 'paused'"
                      >
                        恢复
                      </el-dropdown-item>
                      <el-dropdown-item command="stop" divided>停止</el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
              </div>
            </div>

            <div class="deployment-metrics">
              <div class="metric">
                <span class="label">当前收益</span>
                <span :class="['value', deployment.currentReturn >= 0 ? 'positive' : 'negative']">
                  {{ (deployment.currentReturn * 100).toFixed(2) }}%
                </span>
              </div>
              <div class="metric">
                <span class="label">今日PnL</span>
                <span :class="['value', deployment.todayPnL >= 0 ? 'positive' : 'negative']">
                  ¥{{ deployment.todayPnL.toFixed(2) }}
                </span>
              </div>
              <div class="metric">
                <span class="label">运行天数</span>
                <span class="value">{{ deployment.runningDays }} 天</span>
              </div>
            </div>

            <div class="deployment-progress">
              <div class="progress-info">
                <span>风险水平</span>
                <span>{{ (deployment.riskLevel * 100).toFixed(1) }}%</span>
              </div>
              <el-progress 
                :percentage="deployment.riskLevel * 100" 
                :color="getRiskColor(deployment.riskLevel)"
                :show-text="false"
                :stroke-width="4"
              />
            </div>
          </div>
        </div>
      </el-card>

      <!-- 实时监控面板 -->
      <el-card class="monitoring-panel">
        <template #header>
          <div class="panel-header">
            <span>实时监控面板</span>
            <el-select v-model="selectedDeploymentId" style="width: 300px">
              <el-option 
                v-for="deployment in deployments" 
                :key="deployment.id"
                :label="deployment.name"
                :value="deployment.id"
              />
            </el-select>
          </div>
        </template>

        <div v-if="currentDeployment" class="monitoring-content">
          <el-tabs v-model="activeMonitorTab">
            <el-tab-pane label="实时状态" name="status">
              <div class="real-time-status">
                <el-row :gutter="24">
                  <el-col :span="6">
                    <el-statistic title="账户净值" :value="currentDeployment.netValue" :precision="4" />
                  </el-col>
                  <el-col :span="6">
                    <el-statistic title="可用资金" :value="currentDeployment.availableCash" :precision="2" suffix="元" />
                  </el-col>
                  <el-col :span="6">
                    <el-statistic title="持仓市值" :value="currentDeployment.positionValue" :precision="2" suffix="元" />
                  </el-col>
                  <el-col :span="6">
                    <el-statistic title="当日成交" :value="currentDeployment.todayTrades" suffix="笔" />
                  </el-col>
                </el-row>

                <div class="status-charts">
                  <el-row :gutter="24">
                    <el-col :span="12">
                      <div class="chart-container">
                        <h4>净值曲线</h4>
                        <div ref="netValueChart" class="chart"></div>
                      </div>
                    </el-col>
                    <el-col :span="12">
                      <div class="chart-container">
                        <h4>持仓分布</h4>
                        <div ref="positionChart" class="chart"></div>
                      </div>
                    </el-col>
                  </el-row>
                </div>
              </div>
            </el-tab-pane>

            <el-tab-pane label="交易记录" name="trades">
              <el-table :data="recentTrades" size="small">
                <el-table-column prop="time" label="时间" width="100" />
                <el-table-column prop="symbol" label="股票代码" width="100" />
                <el-table-column prop="side" label="方向" width="80">
                  <template #default="{ row }">
                    <el-tag :type="row.side === 'buy' ? 'success' : 'danger'" size="small">
                      {{ row.side === 'buy' ? '买入' : '卖出' }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="quantity" label="数量" width="100" />
                <el-table-column prop="price" label="价格" width="100">
                  <template #default="{ row }">
                    ¥{{ row.price.toFixed(2) }}
                  </template>
                </el-table-column>
                <el-table-column prop="amount" label="金额" width="120">
                  <template #default="{ row }">
                    ¥{{ row.amount.toFixed(2) }}
                  </template>
                </el-table-column>
                <el-table-column prop="status" label="状态" width="100">
                  <template #default="{ row }">
                    <el-tag :type="getTradeStatusType(row.status)" size="small">
                      {{ row.status }}
                    </el-tag>
                  </template>
                </el-table-column>
              </el-table>
            </el-tab-pane>

            <el-tab-pane label="风险监控" name="risk">
              <div class="risk-monitoring">
                <el-row :gutter="24">
                  <el-col :span="12">
                    <el-card class="risk-metrics">
                      <template #header>
                        <span>风险指标</span>
                      </template>
                      <div class="risk-indicators">
                        <div class="indicator">
                          <div class="indicator-label">当前回撤</div>
                          <div class="indicator-value negative">
                            {{ (currentDeployment.currentDrawdown * 100).toFixed(2) }}%
                          </div>
                          <div class="indicator-limit">
                            限制: {{ (deploymentConfig.maxDrawdownLimit * 100).toFixed(2) }}%
                          </div>
                        </div>
                        <div class="indicator">
                          <div class="indicator-label">日内变动</div>
                          <div :class="['indicator-value', currentDeployment.intradayChange >= 0 ? 'positive' : 'negative']">
                            {{ (currentDeployment.intradayChange * 100).toFixed(2) }}%
                          </div>
                        </div>
                        <div class="indicator">
                          <div class="indicator-label">持仓集中度</div>
                          <div class="indicator-value">
                            {{ (currentDeployment.concentration * 100).toFixed(1) }}%
                          </div>
                        </div>
                      </div>
                    </el-card>
                  </el-col>
                  <el-col :span="12">
                    <el-card class="alerts-panel">
                      <template #header>
                        <span>风险告警</span>
                      </template>
                      <div class="alerts-list">
                        <div v-for="alert in riskAlerts" :key="alert.id" class="alert-item">
                          <div class="alert-header">
                            <el-icon :class="getAlertIconClass(alert.level)"><Warning /></el-icon>
                            <span class="alert-title">{{ alert.title }}</span>
                            <span class="alert-time">{{ formatTime(alert.time) }}</span>
                          </div>
                          <div class="alert-content">{{ alert.message }}</div>
                        </div>
                      </div>
                    </el-card>
                  </el-col>
                </el-row>
              </div>
            </el-tab-pane>
          </el-tabs>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Upload, DocumentChecked, Setting, Warning, VideoPlay,
  ArrowLeft, ArrowRight, Refresh, MoreFilled
} from '@element-plus/icons-vue'

// 响应式数据
const currentStep = ref(0)
const deploying = ref(false)
const deploymentCompleted = ref(false)
const selectedDeploymentId = ref('')
const activeMonitorTab = ref('status')

// 可用策略
const availableStrategies = ref([
  {
    id: 'strategy_1',
    name: 'LightGBM多因子策略v3.2',
    type: '机器学习',
    backtestReturn: 28.5,
    sharpeRatio: 1.45,
    maxDrawdown: -0.12,
    status: 'ready'
  },
  {
    id: 'strategy_2',
    name: 'LSTM时序预测策略v2.1',
    type: '深度学习',
    backtestReturn: 22.3,
    sharpeRatio: 1.28,
    maxDrawdown: -0.15,
    status: 'ready'
  }
])

// 部署配置
const deploymentConfig = reactive({
  strategyId: '',
  name: '',
  environment: 'simulation',
  initialCapital: 1000000,
  broker: 'mock',
  rebalanceFreq: 'monthly',
  positionCount: 30,
  maxSingleWeight: 0.05,
  stopLossThreshold: 0.08,
  maxDrawdownLimit: 0.2,
  dailyTradingLimit: 100000,
  monitoring: ['realtime', 'alerts'],
  notifications: ['email', 'app']
})

// 风险确认
const riskConfirmations = reactive({
  understand: false,
  accept: false,
  professional: false,
  disclaimer: false
})

// 部署列表
const deployments = ref([
  {
    id: 'deploy_1',
    name: 'LightGBM策略_生产环境',
    status: 'running',
    currentReturn: 0.08,
    todayPnL: 1250.0,
    runningDays: 45,
    riskLevel: 0.3,
    netValue: 1.0832,
    availableCash: 285000,
    positionValue: 715000,
    todayTrades: 8,
    currentDrawdown: -0.025,
    intradayChange: 0.012,
    concentration: 0.45
  }
])

// 模拟交易记录
const recentTrades = ref([
  {
    time: '14:35:22',
    symbol: '000001',
    side: 'buy',
    quantity: 1000,
    price: 12.45,
    amount: 12450,
    status: '已成交'
  },
  {
    time: '14:30:15',
    symbol: '600036',
    side: 'sell',
    quantity: 500,
    price: 45.80,
    amount: 22900,
    status: '已成交'
  }
])

// 风险告警
const riskAlerts = ref([
  {
    id: 1,
    level: 'warning',
    title: '持仓集中度偏高',
    message: '前五大持仓占比达到45%，建议关注分散化风险',
    time: new Date()
  },
  {
    id: 2,
    level: 'info',
    title: '调仓信号触发',
    message: '检测到3只股票调仓信号，将在下个交易日执行',
    time: new Date()
  }
])

// 计算属性
const selectedStrategy = computed(() => {
  return availableStrategies.value.find(s => s.id === deploymentConfig.strategyId)
})

const canProceed = computed(() => {
  switch (currentStep.value) {
    case 0:
      return deploymentConfig.strategyId !== ''
    case 1:
      return deploymentConfig.name !== ''
    case 2:
      return allRiskConfirmed.value
    default:
      return true
  }
})

const allRiskConfirmed = computed(() => {
  return Object.values(riskConfirmations).every(confirmed => confirmed)
})

const currentDeployment = computed(() => {
  return deployments.value.find(d => d.id === selectedDeploymentId.value) || deployments.value[0]
})

// 方法
const getStrategyTagType = (type: string) => {
  switch (type) {
    case '机器学习': return 'success'
    case '深度学习': return 'primary'
    case '技术指标': return 'warning'
    default: return 'info'
  }
}

const selectStrategy = (strategyId: string) => {
  deploymentConfig.strategyId = strategyId
  deploymentConfig.name = `${selectedStrategy.value?.name}_部署_${new Date().toLocaleDateString()}`
}

const getFrequencyText = (freq: string) => {
  switch (freq) {
    case 'daily': return '日调仓'
    case 'weekly': return '周调仓'
    case 'monthly': return '月调仓'
    default: return freq
  }
}

const prevStep = () => {
  currentStep.value = Math.max(0, currentStep.value - 1)
}

const nextStep = () => {
  if (!canProceed.value) {
    ElMessage.warning('请完成当前步骤的配置')
    return
  }
  currentStep.value = Math.min(3, currentStep.value + 1)
}

const startDeployment = async () => {
  if (!allRiskConfirmed.value) {
    ElMessage.warning('请完成所有风险确认')
    return
  }

  try {
    await ElMessageBox.confirm(
      '确定要启动策略部署吗？启动后策略将开始自动交易。',
      '确认部署',
      { type: 'warning' }
    )

    deploying.value = true

    // 模拟部署过程
    setTimeout(() => {
      deploying.value = false
      deploymentCompleted.value = true
      
      // 添加新的部署
      const newDeployment = {
        id: `deploy_${Date.now()}`,
        name: deploymentConfig.name,
        status: 'running',
        currentReturn: 0,
        todayPnL: 0,
        runningDays: 1,
        riskLevel: 0.1,
        netValue: 1.0000,
        availableCash: deploymentConfig.initialCapital * 0.8,
        positionValue: deploymentConfig.initialCapital * 0.2,
        todayTrades: 0,
        currentDrawdown: 0,
        intradayChange: 0,
        concentration: 0.2
      }
      
      deployments.value.unshift(newDeployment)
      selectedDeploymentId.value = newDeployment.id
      
      ElMessage.success('策略部署成功！')
    }, 3000)

  } catch {
    // 用户取消
  }
}

const getDeploymentStatusType = (status: string) => {
  switch (status) {
    case 'running': return 'success'
    case 'paused': return 'warning'
    case 'stopped': return 'danger'
    default: return 'info'
  }
}

const getDeploymentStatusText = (status: string) => {
  switch (status) {
    case 'running': return '运行中'
    case 'paused': return '已暂停'
    case 'stopped': return '已停止'
    default: return '未知'
  }
}

const getRiskColor = (riskLevel: number) => {
  if (riskLevel < 0.3) return '#67c23a'
  if (riskLevel < 0.7) return '#e6a23c'
  return '#f56c6c'
}

const refreshDeployments = () => {
  ElMessage.success('部署状态已刷新')
}

const viewDeploymentDetail = (deployment: any) => {
  selectedDeploymentId.value = deployment.id
  activeMonitorTab.value = 'status'
}

const handleDeploymentAction = async (command: string, deployment: any) => {
  switch (command) {
    case 'pause':
      deployment.status = 'paused'
      ElMessage.success('部署已暂停')
      break
    case 'resume':
      deployment.status = 'running'
      ElMessage.success('部署已恢复')
      break
    case 'stop':
      try {
        await ElMessageBox.confirm('确定要停止这个部署吗？', '确认停止')
        deployment.status = 'stopped'
        ElMessage.success('部署已停止')
      } catch {
        // 用户取消
      }
      break
  }
}

const getTradeStatusType = (status: string) => {
  switch (status) {
    case '已成交': return 'success'
    case '待成交': return 'warning'
    case '已撤销': return 'info'
    default: return 'info'
  }
}

const getAlertIconClass = (level: string) => {
  switch (level) {
    case 'warning': return 'alert-warning'
    case 'error': return 'alert-error'
    default: return 'alert-info'
  }
}

const formatTime = (time: Date) => {
  return time.toLocaleTimeString()
}

// 初始化选择第一个部署
if (deployments.value.length > 0) {
  selectedDeploymentId.value = deployments.value[0].id
}
</script>

<style scoped>
.strategy-deployment {
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

.deployment-wizard {
  margin-bottom: 32px;
}

.wizard-header {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.deployment-steps {
  margin: 0;
}

.step-content {
  padding: 32px 0;
}

.step-content h3 {
  margin: 0 0 24px 0;
  color: #303133;
  font-size: 20px;
}

.strategy-selection {
  margin-top: 24px;
}

.strategy-card {
  padding: 20px;
  border: 2px solid #e4e7ed;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  background: #fff;
}

.strategy-card:hover {
  border-color: #409eff;
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.1);
}

.strategy-card.selected {
  border-color: #409eff;
  background: #f0f8ff;
}

.strategy-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}

.strategy-name {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  line-height: 1.3;
}

.strategy-metrics {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 16px;
}

.metric {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.metric-label {
  font-size: 14px;
  color: #606266;
}

.metric-value {
  font-weight: 600;
}

.metric-value.positive {
  color: #67c23a;
}

.metric-value.negative {
  color: #f56c6c;
}

.config-section {
  margin-bottom: 32px;
  padding: 24px;
  background: #f8f9fa;
  border-radius: 8px;
}

.config-section h4 {
  margin: 0 0 20px 0;
  color: #303133;
  font-size: 16px;
  font-weight: 600;
  border-bottom: 2px solid #409eff;
  padding-bottom: 8px;
}

.risk-warnings {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.risk-content h4 {
  margin: 0 0 12px 0;
  color: #303133;
}

.risk-list {
  margin: 0;
  padding-left: 20px;
  color: #606266;
  line-height: 1.6;
}

.risk-list li {
  margin-bottom: 8px;
}

.strategy-risks h4 {
  margin: 0 0 16px 0;
  color: #303133;
}

.confirmations {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 24px;
  background: #f0f8ff;
  border-radius: 8px;
}

.wizard-actions {
  display: flex;
  justify-content: center;
  gap: 16px;
  padding-top: 32px;
  border-top: 1px solid #e4e7ed;
}

.deployments-management {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.deployments-header,
.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.deployments-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 24px;
}

.deployment-card {
  padding: 20px;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  background: #fff;
}

.deployment-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}

.deployment-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.deployment-name {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.deployment-actions {
  display: flex;
  gap: 8px;
}

.deployment-metrics {
  display: flex;
  justify-content: space-between;
  margin-bottom: 16px;
}

.deployment-metrics .metric {
  text-align: center;
}

.deployment-metrics .label {
  display: block;
  font-size: 12px;
  color: #909399;
  margin-bottom: 4px;
}

.deployment-metrics .value {
  font-weight: 600;
  font-size: 14px;
  color: #303133;
}

.deployment-metrics .value.positive {
  color: #67c23a;
}

.deployment-metrics .value.negative {
  color: #f56c6c;
}

.deployment-progress {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  font-size: 14px;
  color: #606266;
}

.monitoring-content {
  margin-top: 16px;
}

.real-time-status {
  display: flex;
  flex-direction: column;
  gap: 32px;
}

.status-charts {
  margin-top: 24px;
}

.chart-container {
  padding: 16px;
  background: #f8f9fa;
  border-radius: 6px;
}

.chart-container h4 {
  margin: 0 0 16px 0;
  color: #303133;
  text-align: center;
}

.chart {
  width: 100%;
  height: 200px;
  background: #fff;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #909399;
}

.risk-monitoring {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.risk-indicators {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.indicator {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 6px;
}

.indicator-label {
  font-size: 14px;
  color: #606266;
}

.indicator-value {
  font-size: 18px;
  font-weight: 600;
}

.indicator-value.positive {
  color: #67c23a;
}

.indicator-value.negative {
  color: #f56c6c;
}

.indicator-limit {
  font-size: 12px;
  color: #909399;
}

.alerts-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.alert-item {
  padding: 12px;
  background: #f8f9fa;
  border-radius: 6px;
  border-left: 4px solid #409eff;
}

.alert-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.alert-title {
  font-weight: 600;
  color: #303133;
}

.alert-time {
  margin-left: auto;
  font-size: 12px;
  color: #909399;
}

.alert-content {
  font-size: 14px;
  color: #606266;
  line-height: 1.4;
}

.alert-warning {
  color: #e6a23c;
}

.alert-error {
  color: #f56c6c;
}

.alert-info {
  color: #409eff;
}

@media (max-width: 768px) {
  .strategy-deployment {
    padding: 16px;
  }
  
  .deployments-grid {
    grid-template-columns: 1fr;
  }
  
  .deployment-header {
    flex-direction: column;
    gap: 12px;
  }
  
  .deployment-metrics {
    flex-direction: column;
    gap: 12px;
  }
  
  .panel-header,
  .deployments-header {
    flex-direction: column;
    gap: 12px;
  }
  
  .wizard-actions {
    flex-direction: column;
  }
  
  .confirmations {
    padding: 16px;
  }
}
</style>