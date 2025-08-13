<template>
  <div class="risk-management-console">
    <!-- 风险概览仪表盘 -->
    <el-card class="risk-overview">
      <template #header>
        <div class="header-with-alert">
          <span>风险监控概览</span>
          <div class="alert-controls">
            <el-tag 
              :type="overallRiskLevel.type" 
              size="large"
              class="risk-level-tag"
            >
              {{ overallRiskLevel.text }}
            </el-tag>
            <el-button 
              v-if="hasActiveAlerts" 
              type="danger" 
              size="small"
              @click="handleEmergencyStop"
            >
              <el-icon><Warning /></el-icon>
              紧急停止
            </el-button>
          </div>
        </div>
      </template>

      <el-row :gutter="24">
        <el-col :span="6">
          <div class="risk-metric">
            <div class="metric-header">
              <span class="metric-title">当前回撤</span>
              <el-progress 
                type="dashboard" 
                :percentage="Math.abs(riskMetrics.currentDrawdown) * 100"
                :color="getDrawdownColor(riskMetrics.currentDrawdown)"
                :width="80"
              />
            </div>
            <div class="metric-details">
              <div class="metric-value">{{ Math.abs(riskMetrics.currentDrawdown * 100).toFixed(2) }}%</div>
              <div class="metric-limit">限制: {{ riskLimits.maxDrawdown * 100 }}%</div>
            </div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="risk-metric">
            <div class="metric-header">
              <span class="metric-title">持仓集中度</span>
              <el-progress 
                type="dashboard" 
                :percentage="riskMetrics.concentration * 100"
                :color="getConcentrationColor(riskMetrics.concentration)"
                :width="80"
              />
            </div>
            <div class="metric-details">
              <div class="metric-value">{{ (riskMetrics.concentration * 100).toFixed(1) }}%</div>
              <div class="metric-limit">建议: < 50%</div>
            </div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="risk-metric">
            <div class="metric-header">
              <span class="metric-title">波动率</span>
              <el-progress 
                type="dashboard" 
                :percentage="riskMetrics.volatility * 100"
                :color="getVolatilityColor(riskMetrics.volatility)"
                :width="80"
              />
            </div>
            <div class="metric-details">
              <div class="metric-value">{{ (riskMetrics.volatility * 100).toFixed(2) }}%</div>
              <div class="metric-limit">正常: < 25%</div>
            </div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="risk-metric">
            <div class="metric-header">
              <span class="metric-title">VaR (95%)</span>
              <el-progress 
                type="dashboard" 
                :percentage="Math.abs(riskMetrics.var95) * 100"
                :color="getVarColor(riskMetrics.var95)"
                :width="80"
              />
            </div>
            <div class="metric-details">
              <div class="metric-value">{{ Math.abs(riskMetrics.var95 * 100).toFixed(2) }}%</div>
              <div class="metric-limit">警戒: > 3%</div>
            </div>
          </div>
        </el-col>
      </el-row>
    </el-card>

    <el-row :gutter="24">
      <!-- 风险告警面板 -->
      <el-col :span="12">
        <el-card class="risk-alerts">
          <template #header>
            <div class="alerts-header">
              <span>风险告警</span>
              <div class="alert-stats">
                <el-badge :value="criticalAlerts.length" type="danger">
                  <el-tag type="danger" size="small">严重</el-tag>
                </el-badge>
                <el-badge :value="warningAlerts.length" type="warning">
                  <el-tag type="warning" size="small">警告</el-tag>
                </el-badge>
              </div>
            </div>
          </template>

          <div class="alerts-list">
            <div v-for="alert in recentAlerts" :key="alert.id" class="alert-item">
              <div class="alert-header">
                <el-icon :class="getAlertIconClass(alert.level)">
                  <Warning />
                </el-icon>
                <span class="alert-title">{{ alert.title }}</span>
                <span class="alert-time">{{ formatTime(alert.time) }}</span>
              </div>
              <div class="alert-content">{{ alert.message }}</div>
              <div class="alert-actions">
                <el-button size="small" @click="viewAlertDetail(alert)">详情</el-button>
                <el-button size="small" @click="acknowledgeAlert(alert)">确认</el-button>
                <el-button v-if="alert.level === 'critical'" size="small" type="danger" @click="takeAction(alert)">
                  立即处理
                </el-button>
              </div>
            </div>
          </div>

          <div v-if="recentAlerts.length === 0" class="no-alerts">
            <el-icon><CircleCheckFilled /></el-icon>
            <span>暂无风险告警</span>
          </div>
        </el-card>
      </el-col>

      <!-- 风险控制操作 -->
      <el-col :span="12">
        <el-card class="risk-controls">
          <template #header>
            <span>风险控制操作</span>
          </template>

          <div class="control-sections">
            <!-- 仓位控制 -->
            <div class="control-section">
              <h4>仓位控制</h4>
              <el-row :gutter="16">
                <el-col :span="12">
                  <el-button 
                    type="warning" 
                    size="small" 
                    @click="adjustPosition(-0.2)"
                    :disabled="isAdjusting"
                  >
                    <el-icon><Minus /></el-icon>
                    减仓20%
                  </el-button>
                </el-col>
                <el-col :span="12">
                  <el-button 
                    type="danger" 
                    size="small" 
                    @click="adjustPosition(-0.5)"
                    :disabled="isAdjusting"
                  >
                    <el-icon><Minus /></el-icon>
                    减仓50%
                  </el-button>
                </el-col>
              </el-row>
              <el-row :gutter="16" class="second-row">
                <el-col :span="24">
                  <el-button 
                    type="danger" 
                    size="small" 
                    @click="clearAllPositions"
                    :disabled="isAdjusting"
                    style="width: 100%"
                  >
                    <el-icon><Delete /></el-icon>
                    清空所有持仓
                  </el-button>
                </el-col>
              </el-row>
            </div>

            <!-- 止损设置 -->
            <div class="control-section">
              <h4>动态止损</h4>
              <el-form :model="stopLossConfig" size="small">
                <el-form-item label="止损阈值">
                  <el-input-number 
                    v-model="stopLossConfig.threshold" 
                    :min="0.01" 
                    :max="0.5"
                    :step="0.01"
                    :precision="2"
                    style="width: 100%"
                  />
                </el-form-item>
                <el-form-item label="追踪止损">
                  <el-switch v-model="stopLossConfig.trailing" />
                </el-form-item>
                <el-form-item>
                  <el-button 
                    type="primary" 
                    size="small" 
                    @click="updateStopLoss"
                    style="width: 100%"
                  >
                    更新止损设置
                  </el-button>
                </el-form-item>
              </el-form>
            </div>

            <!-- 资金管理 -->
            <div class="control-section">
              <h4>资金管理</h4>
              <el-form :model="capitalConfig" size="small">
                <el-form-item label="最大仓位">
                  <el-input-number 
                    v-model="capitalConfig.maxPosition" 
                    :min="0.1" 
                    :max="1.0"
                    :step="0.1"
                    :precision="1"
                    style="width: 100%"
                  />
                </el-form-item>
                <el-form-item label="日交易限额">
                  <el-input-number 
                    v-model="capitalConfig.dailyLimit" 
                    :min="1000" 
                    :max="1000000"
                    :step="1000"
                    style="width: 100%"
                  />
                </el-form-item>
                <el-form-item>
                  <el-button 
                    type="primary" 
                    size="small" 
                    @click="updateCapitalConfig"
                    style="width: 100%"
                  >
                    更新资金配置
                  </el-button>
                </el-form-item>
              </el-form>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 历史风险报告 -->
    <el-card class="risk-reports">
      <template #header>
        <div class="reports-header">
          <span>风险分析报告</span>
          <div class="report-controls">
            <el-select v-model="reportPeriod" size="small" style="width: 120px;">
              <el-option label="近7天" value="week" />
              <el-option label="近30天" value="month" />
              <el-option label="近90天" value="quarter" />
            </el-select>
            <el-button size="small" @click="generateReport">
              <el-icon><Document /></el-icon>
              生成报告
            </el-button>
          </div>
        </div>
      </template>

      <el-tabs v-model="activeReportTab">
        <el-tab-pane label="风险指标趋势" name="trends">
          <div class="risk-charts">
            <el-row :gutter="24">
              <el-col :span="12">
                <div class="chart-container">
                  <h4>回撤分析</h4>
                  <div ref="drawdownChart" class="chart"></div>
                </div>
              </el-col>
              <el-col :span="12">
                <div class="chart-container">
                  <h4>波动率分析</h4>
                  <div ref="volatilityChart" class="chart"></div>
                </div>
              </el-col>
            </el-row>
          </div>
        </el-tab-pane>

        <el-tab-pane label="行业风险暴露" name="exposure">
          <div class="exposure-analysis">
            <el-table :data="industryExposure" size="small">
              <el-table-column prop="industry" label="行业" width="150" />
              <el-table-column prop="weight" label="权重" width="100">
                <template #default="{ row }">
                  {{ (row.weight * 100).toFixed(2) }}%
                </template>
              </el-table-column>
              <el-table-column prop="riskContribution" label="风险贡献" width="120">
                <template #default="{ row }">
                  {{ (row.riskContribution * 100).toFixed(2) }}%
                </template>
              </el-table-column>
              <el-table-column prop="activeWeight" label="主动权重" width="120">
                <template #default="{ row }">
                  <span :class="{ 'overweight': row.activeWeight > 0, 'underweight': row.activeWeight < 0 }">
                    {{ (row.activeWeight * 100).toFixed(2) }}%
                  </span>
                </template>
              </el-table-column>
              <el-table-column prop="riskLevel" label="风险等级" width="100">
                <template #default="{ row }">
                  <el-tag :type="getRiskLevelType(row.riskLevel)" size="small">
                    {{ row.riskLevel }}
                  </el-tag>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-tab-pane>

        <el-tab-pane label="压力测试" name="stress">
          <div class="stress-test">
            <div class="stress-scenarios">
              <h4>压力情景分析</h4>
              <el-row :gutter="24">
                <el-col :span="8" v-for="scenario in stressScenarios" :key="scenario.name">
                  <div class="scenario-card">
                    <div class="scenario-header">
                      <span class="scenario-name">{{ scenario.name }}</span>
                      <el-tag :type="getScenarioType(scenario.impact)" size="small">
                        {{ scenario.impact > 0 ? '+' : '' }}{{ (scenario.impact * 100).toFixed(1) }}%
                      </el-tag>
                    </div>
                    <div class="scenario-description">{{ scenario.description }}</div>
                    <div class="scenario-details">
                      <div class="detail-item">
                        <span>预期损失: </span>
                        <span class="loss-value">¥{{ scenario.expectedLoss.toLocaleString() }}</span>
                      </div>
                      <div class="detail-item">
                        <span>最大损失: </span>
                        <span class="loss-value">¥{{ scenario.maxLoss.toLocaleString() }}</span>
                      </div>
                    </div>
                  </div>
                </el-col>
              </el-row>
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Warning, Minus, Delete, Document, CircleCheckFilled
} from '@element-plus/icons-vue'

interface RiskMetrics {
  currentDrawdown: number
  concentration: number
  volatility: number
  var95: number
}

interface RiskAlert {
  id: string
  level: 'critical' | 'warning' | 'info'
  title: string
  message: string
  time: Date
  acknowledged: boolean
}

interface IndustryExposure {
  industry: string
  weight: number
  riskContribution: number
  activeWeight: number
  riskLevel: string
}

interface StressScenario {
  name: string
  description: string
  impact: number
  expectedLoss: number
  maxLoss: number
}

interface Props {
  deploymentId: string
}

const props = defineProps<Props>()

// 响应式数据
const reportPeriod = ref('month')
const activeReportTab = ref('trends')
const isAdjusting = ref(false)

// 风险指标
const riskMetrics = reactive<RiskMetrics>({
  currentDrawdown: -0.035,
  concentration: 0.45,
  volatility: 0.18,
  var95: -0.025
})

// 风险限制
const riskLimits = reactive({
  maxDrawdown: 0.15,
  maxConcentration: 0.5,
  maxVolatility: 0.25,
  maxVar95: 0.03
})

// 止损配置
const stopLossConfig = reactive({
  threshold: 0.08,
  trailing: true
})

// 资金配置
const capitalConfig = reactive({
  maxPosition: 0.8,
  dailyLimit: 100000
})

// 风险告警
const alerts = ref<RiskAlert[]>([
  {
    id: '1',
    level: 'critical',
    title: '回撤超过警戒线',
    message: '当前回撤3.5%已接近5%警戒线，建议立即减仓',
    time: new Date(),
    acknowledged: false
  },
  {
    id: '2',
    level: 'warning',
    title: '持仓集中度偏高',
    message: '前五大持仓占比达到45%，建议关注分散化风险',
    time: new Date(Date.now() - 300000),
    acknowledged: false
  },
  {
    id: '3',
    level: 'info',
    title: '波动率上升',
    message: '近期波动率上升至18%，请密切关注市场变化',
    time: new Date(Date.now() - 600000),
    acknowledged: true
  }
])

// 行业风险暴露
const industryExposure = ref<IndustryExposure[]>([
  {
    industry: '金融',
    weight: 0.25,
    riskContribution: 0.18,
    activeWeight: 0.05,
    riskLevel: '中'
  },
  {
    industry: '消费',
    weight: 0.20,
    riskContribution: 0.15,
    activeWeight: -0.03,
    riskLevel: '低'
  },
  {
    industry: '科技',
    weight: 0.18,
    riskContribution: 0.22,
    activeWeight: 0.08,
    riskLevel: '高'
  }
])

// 压力测试情景
const stressScenarios = ref<StressScenario[]>([
  {
    name: '市场大跌',
    description: '市场下跌20%的极端情况',
    impact: -0.15,
    expectedLoss: 150000,
    maxLoss: 200000
  },
  {
    name: '流动性危机',
    description: '市场流动性严重不足',
    impact: -0.12,
    expectedLoss: 120000,
    maxLoss: 180000
  },
  {
    name: '利率冲击',
    description: '央行大幅加息的冲击',
    impact: -0.08,
    expectedLoss: 80000,
    maxLoss: 120000
  }
])

// 计算属性
const overallRiskLevel = computed(() => {
  const criticalCount = criticalAlerts.value.length
  const warningCount = warningAlerts.value.length
  
  if (criticalCount > 0) {
    return { type: 'danger', text: '高风险' }
  } else if (warningCount > 2) {
    return { type: 'warning', text: '中等风险' }
  } else {
    return { type: 'success', text: '低风险' }
  }
})

const criticalAlerts = computed(() => {
  return alerts.value.filter(alert => alert.level === 'critical' && !alert.acknowledged)
})

const warningAlerts = computed(() => {
  return alerts.value.filter(alert => alert.level === 'warning' && !alert.acknowledged)
})

const recentAlerts = computed(() => {
  return alerts.value.slice(0, 5)
})

const hasActiveAlerts = computed(() => {
  return criticalAlerts.value.length > 0
})

// 方法
const getDrawdownColor = (drawdown: number) => {
  const absDrawdown = Math.abs(drawdown)
  if (absDrawdown < 0.02) return '#67c23a'
  if (absDrawdown < 0.05) return '#e6a23c'
  return '#f56c6c'
}

const getConcentrationColor = (concentration: number) => {
  if (concentration < 0.3) return '#67c23a'
  if (concentration < 0.5) return '#e6a23c'
  return '#f56c6c'
}

const getVolatilityColor = (volatility: number) => {
  if (volatility < 0.15) return '#67c23a'
  if (volatility < 0.25) return '#e6a23c'
  return '#f56c6c'
}

const getVarColor = (var95: number) => {
  const absVar = Math.abs(var95)
  if (absVar < 0.02) return '#67c23a'
  if (absVar < 0.03) return '#e6a23c'
  return '#f56c6c'
}

const getAlertIconClass = (level: string) => {
  switch (level) {
    case 'critical': return 'alert-critical'
    case 'warning': return 'alert-warning'
    default: return 'alert-info'
  }
}

const getRiskLevelType = (level: string) => {
  switch (level) {
    case '高': return 'danger'
    case '中': return 'warning'
    case '低': return 'success'
    default: return 'info'
  }
}

const getScenarioType = (impact: number) => {
  if (impact < -0.1) return 'danger'
  if (impact < -0.05) return 'warning'
  return 'info'
}

const formatTime = (time: Date) => {
  return time.toLocaleTimeString()
}

const handleEmergencyStop = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要紧急停止策略运行吗？这将立即停止所有交易并清空持仓。',
      '紧急停止确认',
      { type: 'error' }
    )
    
    ElMessage.success('紧急停止指令已发送')
  } catch {
    // 用户取消
  }
}

const adjustPosition = async (ratio: number) => {
  try {
    const action = ratio > 0 ? '加仓' : '减仓'
    await ElMessageBox.confirm(
      `确定要${action}${Math.abs(ratio * 100)}%吗？`,
      '仓位调整确认',
      { type: 'warning' }
    )
    
    isAdjusting.value = true
    
    // 模拟调整过程
    setTimeout(() => {
      isAdjusting.value = false
      ElMessage.success(`${action}操作已完成`)
    }, 2000)
  } catch {
    // 用户取消
  }
}

const clearAllPositions = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要清空所有持仓吗？这将卖出所有股票！',
      '清仓确认',
      { type: 'error' }
    )
    
    isAdjusting.value = true
    
    // 模拟清仓过程
    setTimeout(() => {
      isAdjusting.value = false
      ElMessage.success('清仓操作已完成')
    }, 3000)
  } catch {
    // 用户取消
  }
}

const updateStopLoss = () => {
  ElMessage.success('止损设置已更新')
}

const updateCapitalConfig = () => {
  ElMessage.success('资金配置已更新')
}

const viewAlertDetail = (alert: RiskAlert) => {
  ElMessage.info(`查看告警详情: ${alert.title}`)
}

const acknowledgeAlert = (alert: RiskAlert) => {
  alert.acknowledged = true
  ElMessage.success('告警已确认')
}

const takeAction = (alert: RiskAlert) => {
  ElMessage.info(`正在处理告警: ${alert.title}`)
}

const generateReport = () => {
  ElMessage.success('风险报告生成中，请稍候...')
}
</script>

<style scoped>
.risk-management-console {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.header-with-alert {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.alert-controls {
  display: flex;
  align-items: center;
  gap: 12px;
}

.risk-level-tag {
  font-size: 14px;
  padding: 8px 16px;
}

.risk-metric {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
  text-align: center;
}

.metric-header {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.metric-title {
  font-size: 14px;
  color: #606266;
  font-weight: 600;
}

.metric-details {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.metric-value {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.metric-limit {
  font-size: 12px;
  color: #909399;
}

.alerts-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.alert-stats {
  display: flex;
  gap: 12px;
}

.alerts-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
  max-height: 400px;
  overflow-y: auto;
}

.alert-item {
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
  border-left: 4px solid #409eff;
}

.alert-item .alert-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.alert-title {
  font-weight: 600;
  color: #303133;
  flex: 1;
}

.alert-time {
  font-size: 12px;
  color: #909399;
}

.alert-content {
  font-size: 14px;
  color: #606266;
  margin-bottom: 12px;
  line-height: 1.4;
}

.alert-actions {
  display: flex;
  gap: 8px;
}

.alert-critical {
  color: #f56c6c;
}

.alert-warning {
  color: #e6a23c;
}

.alert-info {
  color: #409eff;
}

.no-alerts {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 40px;
  color: #909399;
}

.control-sections {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.control-section {
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
}

.control-section h4 {
  margin: 0 0 16px 0;
  color: #303133;
  font-size: 14px;
  font-weight: 600;
  border-bottom: 1px solid #e4e7ed;
  padding-bottom: 8px;
}

.second-row {
  margin-top: 12px;
}

.reports-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.report-controls {
  display: flex;
  gap: 12px;
}

.risk-charts {
  margin-top: 16px;
}

.chart-container {
  padding: 16px;
  background: #f8f9fa;
  border-radius: 6px;
  text-align: center;
}

.chart-container h4 {
  margin: 0 0 16px 0;
  color: #303133;
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

.exposure-analysis {
  margin-top: 16px;
}

.overweight {
  color: #f56c6c;
}

.underweight {
  color: #67c23a;
}

.stress-test {
  margin-top: 16px;
}

.stress-scenarios h4 {
  margin: 0 0 16px 0;
  color: #303133;
}

.scenario-card {
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
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
  font-size: 14px;
  color: #606266;
  margin-bottom: 12px;
  line-height: 1.4;
}

.scenario-details {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
}

.loss-value {
  font-weight: 600;
  color: #f56c6c;
}

@media (max-width: 768px) {
  .header-with-alert,
  .alerts-header,
  .reports-header {
    flex-direction: column;
    gap: 12px;
  }
  
  .alert-controls,
  .alert-stats,
  .report-controls {
    flex-wrap: wrap;
  }
  
  .risk-metric {
    padding: 16px;
  }
  
  .alert-actions {
    flex-wrap: wrap;
  }
}
</style>