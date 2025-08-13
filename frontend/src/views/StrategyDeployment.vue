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

    <!-- 功能导航标签 -->
    <el-card class="navigation-tabs">
      <el-tabs v-model="activeTab" @tab-change="handleTabChange">
        <el-tab-pane label="部署向导" name="wizard">
          <template #label>
            <span class="tab-label">
              <el-icon><Setting /></el-icon>
              部署向导
            </span>
          </template>
        </el-tab-pane>
        <el-tab-pane label="实盘监控" name="monitor">
          <template #label>
            <span class="tab-label">
              <el-icon><Monitor /></el-icon>
              实盘监控
            </span>
          </template>
        </el-tab-pane>
        <el-tab-pane label="风险管理" name="risk">
          <template #label>
            <span class="tab-label">
              <el-icon><Warning /></el-icon>
              风险管理
            </span>
          </template>
        </el-tab-pane>
        <el-tab-pane label="模拟交易" name="paper">
          <template #label>
            <span class="tab-label">
              <el-icon><TrendCharts /></el-icon>
              模拟交易
            </span>
          </template>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <!-- 部署向导 -->
    <div v-if="activeTab === 'wizard'">
      <DeploymentWizard
        v-model="deploymentConfig"
        :strategies="availableStrategies"
        :deploying="deploying"
        @deploy="handleDeployment"
        ref="deploymentWizardRef"
      />
    </div>

    <!-- 实盘监控 -->
    <div v-if="activeTab === 'monitor'">
      <LiveTradingMonitor 
        :deployment-id="selectedDeploymentId"
      />
    </div>

    <!-- 风险管理 -->
    <div v-if="activeTab === 'risk'">
      <RiskManagementConsole 
        :deployment-id="selectedDeploymentId"
      />
    </div>

    <!-- 模拟交易 -->
    <div v-if="activeTab === 'paper'">
      <PaperTradingInterface 
        :deployment-id="selectedDeploymentId"
      />
    </div>


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
import { ElMessage } from 'element-plus'
import {
  Upload, Setting, Warning, Monitor, TrendCharts
} from '@element-plus/icons-vue'
import DeploymentWizard from '@/components/deployment/DeploymentWizard.vue'
import LiveTradingMonitor from '@/components/deployment/LiveTradingMonitor.vue'
import RiskManagementConsole from '@/components/deployment/RiskManagementConsole.vue'
import PaperTradingInterface from '@/components/deployment/PaperTradingInterface.vue'

// 响应式数据
const activeTab = ref('wizard')
const deploying = ref(false)
const selectedDeploymentId = ref('')
const deploymentWizardRef = ref()

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

// 部署列表
const deployments = ref([
  {
    id: 'deploy_1',
    name: 'LightGBM策略_生产环境',
    status: 'running',
    currentReturn: 0.08,
    todayPnL: 1250.0,
    runningDays: 45,
    riskLevel: 0.3
  }
])

// 方法
const handleTabChange = (tabName: string) => {
  activeTab.value = tabName
  
  // 如果切换到监控、风险或模拟交易页面，确保有选中的部署ID
  if ((tabName === 'monitor' || tabName === 'risk' || tabName === 'paper') && deployments.value.length > 0) {
    if (!selectedDeploymentId.value) {
      selectedDeploymentId.value = deployments.value[0].id
    }
  }
}

const handleDeployment = async (config: any) => {
  deploying.value = true

  // 模拟部署过程
  setTimeout(() => {
    deploying.value = false
    
    // 添加新的部署
    const newDeployment = {
      id: `deploy_${Date.now()}`,
      name: config.name,
      status: 'running',
      currentReturn: 0,
      todayPnL: 0,
      runningDays: 1,
      riskLevel: 0.1
    }
    
    deployments.value.unshift(newDeployment)
    selectedDeploymentId.value = newDeployment.id
    
    // 重置向导
    if (deploymentWizardRef.value) {
      deploymentWizardRef.value.resetWizard()
    }
    
    // 切换到实盘监控页面
    activeTab.value = 'monitor'
    
    ElMessage.success('策略部署成功！')
  }, 3000)
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

.navigation-tabs {
  margin-bottom: 24px;
}

.tab-label {
  display: flex;
  align-items: center;
  gap: 6px;
}


@media (max-width: 768px) {
  .strategy-deployment {
    padding: 16px;
  }
  
  .tab-label {
    font-size: 14px;
  }
}
</style>