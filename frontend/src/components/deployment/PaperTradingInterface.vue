<template>
  <div class="paper-trading-interface">
    <!-- 模拟交易控制面板 -->
    <el-card class="trading-controls">
      <template #header>
        <div class="controls-header">
          <span>模拟交易控制台</span>
          <div class="trading-status">
            <el-tag :type="tradingStatus === 'active' ? 'success' : 'danger'" size="large">
              {{ tradingStatus === 'active' ? '交易中' : '已暂停' }}
            </el-tag>
            <el-button 
              :type="tradingStatus === 'active' ? 'warning' : 'success'"
              size="small"
              @click="toggleTrading"
            >
              {{ tradingStatus === 'active' ? '暂停交易' : '恢复交易' }}
            </el-button>
          </div>
        </div>
      </template>

      <el-row :gutter="24">
        <el-col :span="6">
          <div class="control-group">
            <h4>策略控制</h4>
            <el-button-group class="strategy-controls">
              <el-button 
                size="small" 
                @click="executeRebalance"
                :disabled="tradingStatus !== 'active'"
              >
                <el-icon><Refresh /></el-icon>
                手动调仓
              </el-button>
              <el-button 
                size="small" 
                @click="forceLiquidation"
                :disabled="tradingStatus !== 'active'"
                type="danger"
              >
                <el-icon><Warning /></el-icon>
                强制清仓
              </el-button>
            </el-button-group>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="control-group">
            <h4>交易设置</h4>
            <el-form size="small">
              <el-form-item label="交易延迟(秒)">
                <el-input-number 
                  v-model="tradingSettings.delay" 
                  :min="0" 
                  :max="60"
                  size="small"
                  style="width: 100%"
                />
              </el-form-item>
              <el-form-item label="滑点设置">
                <el-input-number 
                  v-model="tradingSettings.slippage" 
                  :min="0" 
                  :max="0.01"
                  :step="0.0001"
                  :precision="4"
                  size="small"
                  style="width: 100%"
                />
              </el-form-item>
            </el-form>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="control-group">
            <h4>风险参数</h4>
            <el-form size="small">
              <el-form-item label="最大单笔(万)">
                <el-input-number 
                  v-model="riskParams.maxSingleOrder" 
                  :min="1" 
                  :max="100"
                  size="small"
                  style="width: 100%"
                />
              </el-form-item>
              <el-form-item label="最大仓位(%)">
                <el-input-number 
                  v-model="riskParams.maxPosition" 
                  :min="10" 
                  :max="100"
                  size="small"
                  style="width: 100%"
                />
              </el-form-item>
            </el-form>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="control-group">
            <h4>快速操作</h4>
            <el-button-group class="quick-actions">
              <el-button size="small" @click="resetStrategy">
                <el-icon><RefreshLeft /></el-icon>
                重置策略
              </el-button>
              <el-button size="small" @click="saveSnapshot" type="primary">
                <el-icon><Camera /></el-icon>
                保存快照
              </el-button>
            </el-button-group>
          </div>
        </el-col>
      </el-row>
    </el-card>

    <!-- 交易信号监控 -->
    <el-row :gutter="24">
      <el-col :span="12">
        <el-card class="trading-signals">
          <template #header>
            <div class="signals-header">
              <span>交易信号监控</span>
              <el-button size="small" @click="refreshSignals">
                <el-icon><Refresh /></el-icon>
                刷新信号
              </el-button>
            </div>
          </template>

          <div class="signals-list">
            <div v-for="signal in tradingSignals" :key="signal.id" class="signal-item">
              <div class="signal-header">
                <div class="signal-info">
                  <span class="stock-code">{{ signal.symbol }}</span>
                  <span class="stock-name">{{ signal.name }}</span>
                  <el-tag :type="signal.action === 'buy' ? 'success' : 'danger'" size="small">
                    {{ signal.action === 'buy' ? '买入' : '卖出' }}
                  </el-tag>
                </div>
                <div class="signal-strength">
                  <span class="strength-label">信号强度</span>
                  <el-progress 
                    :percentage="signal.strength * 100"
                    :color="getSignalColor(signal.strength)"
                    :show-text="false"
                    :stroke-width="6"
                  />
                  <span class="strength-value">{{ (signal.strength * 100).toFixed(0) }}%</span>
                </div>
              </div>
              
              <div class="signal-details">
                <div class="detail-row">
                  <span class="label">当前价格:</span>
                  <span class="value">¥{{ signal.currentPrice.toFixed(2) }}</span>
                </div>
                <div class="detail-row">
                  <span class="label">目标价格:</span>
                  <span class="value">¥{{ signal.targetPrice.toFixed(2) }}</span>
                </div>
                <div class="detail-row">
                  <span class="label">建议数量:</span>
                  <span class="value">{{ signal.suggestedQuantity }} 股</span>
                </div>
                <div class="detail-row">
                  <span class="label">预期收益:</span>
                  <span :class="['value', signal.expectedReturn > 0 ? 'positive' : 'negative']">
                    {{ (signal.expectedReturn * 100).toFixed(2) }}%
                  </span>
                </div>
              </div>

              <div class="signal-actions">
                <el-button 
                  size="small" 
                  type="primary" 
                  @click="executeSignal(signal)"
                  :disabled="tradingStatus !== 'active'"
                >
                  执行信号
                </el-button>
                <el-button size="small" @click="ignoreSignal(signal)">
                  忽略
                </el-button>
                <el-button size="small" @click="viewSignalDetail(signal)">
                  详情
                </el-button>
              </div>
            </div>
          </div>

          <div v-if="tradingSignals.length === 0" class="no-signals">
            <el-icon><DataBoard /></el-icon>
            <span>暂无交易信号</span>
          </div>
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card class="order-management">
          <template #header>
            <div class="orders-header">
              <span>订单管理</span>
              <div class="order-filters">
                <el-select v-model="orderFilter" size="small" style="width: 100px;">
                  <el-option label="全部" value="all" />
                  <el-option label="待成交" value="pending" />
                  <el-option label="已成交" value="filled" />
                  <el-option label="已取消" value="cancelled" />
                </el-select>
                <el-button size="small" @click="cancelAllPendingOrders" type="danger">
                  取消全部
                </el-button>
              </div>
            </div>
          </template>

          <el-table :data="filteredOrders" size="small" max-height="400">
            <el-table-column prop="time" label="时间" width="80">
              <template #default="{ row }">
                {{ formatTime(row.time) }}
              </template>
            </el-table-column>
            <el-table-column prop="symbol" label="代码" width="80" />
            <el-table-column prop="side" label="方向" width="60">
              <template #default="{ row }">
                <el-tag :type="row.side === 'buy' ? 'success' : 'danger'" size="small">
                  {{ row.side === 'buy' ? '买' : '卖' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="quantity" label="数量" width="80" />
            <el-table-column prop="price" label="价格" width="80">
              <template #default="{ row }">
                ¥{{ row.price.toFixed(2) }}
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="80">
              <template #default="{ row }">
                <el-tag :type="getOrderStatusType(row.status)" size="small">
                  {{ row.status }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="100">
              <template #default="{ row }">
                <el-button 
                  v-if="row.status === '待成交'" 
                  size="small" 
                  type="danger" 
                  @click="cancelOrder(row)"
                >
                  撤单
                </el-button>
                <el-button v-else size="small" @click="viewOrderDetail(row)">
                  详情
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <!-- 性能分析面板 -->
    <el-card class="performance-analysis">
      <template #header>
        <div class="performance-header">
          <span>模拟交易性能分析</span>
          <div class="analysis-controls">
            <el-select v-model="performancePeriod" size="small" style="width: 120px;">
              <el-option label="今日" value="today" />
              <el-option label="近7天" value="week" />
              <el-option label="近30天" value="month" />
            </el-select>
            <el-button size="small" @click="exportPerformance">
              <el-icon><Download /></el-icon>
              导出分析
            </el-button>
          </div>
        </div>
      </template>

      <el-tabs v-model="activePerformanceTab">
        <el-tab-pane label="收益分析" name="returns">
          <el-row :gutter="24">
            <el-col :span="8">
              <div class="performance-metric">
                <div class="metric-title">总收益率</div>
                <div :class="['metric-value', performanceData.totalReturn > 0 ? 'positive' : 'negative']">
                  {{ (performanceData.totalReturn * 100).toFixed(2) }}%
                </div>
                <div class="metric-subtitle">
                  绝对收益: ¥{{ performanceData.absoluteReturn.toLocaleString() }}
                </div>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="performance-metric">
                <div class="metric-title">年化收益率</div>
                <div :class="['metric-value', performanceData.annualizedReturn > 0 ? 'positive' : 'negative']">
                  {{ (performanceData.annualizedReturn * 100).toFixed(2) }}%
                </div>
                <div class="metric-subtitle">
                  基准对比: +{{ (performanceData.excessReturn * 100).toFixed(2) }}%
                </div>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="performance-metric">
                <div class="metric-title">夏普比率</div>
                <div class="metric-value">
                  {{ performanceData.sharpeRatio.toFixed(2) }}
                </div>
                <div class="metric-subtitle">
                  风险调整后收益
                </div>
              </div>
            </el-col>
          </el-row>
          
          <div class="performance-chart">
            <h4>净值曲线对比</h4>
            <div ref="performanceChart" class="chart"></div>
          </div>
        </el-tab-pane>

        <el-tab-pane label="交易统计" name="trading">
          <el-row :gutter="24">
            <el-col :span="12">
              <div class="trading-stats">
                <h4>交易统计概览</h4>
                <el-descriptions :column="2" border>
                  <el-descriptions-item label="总交易次数">
                    {{ tradingStats.totalTrades }}
                  </el-descriptions-item>
                  <el-descriptions-item label="盈利交易">
                    {{ tradingStats.profitableTrades }}
                  </el-descriptions-item>
                  <el-descriptions-item label="胜率">
                    {{ (tradingStats.winRate * 100).toFixed(1) }}%
                  </el-descriptions-item>
                  <el-descriptions-item label="平均持仓周期">
                    {{ tradingStats.avgHoldingPeriod }} 天
                  </el-descriptions-item>
                  <el-descriptions-item label="最大单笔盈利">
                    ¥{{ tradingStats.maxProfit.toLocaleString() }}
                  </el-descriptions-item>
                  <el-descriptions-item label="最大单笔亏损">
                    ¥{{ tradingStats.maxLoss.toLocaleString() }}
                  </el-descriptions-item>
                  <el-descriptions-item label="平均交易成本">
                    ¥{{ tradingStats.avgTransactionCost.toFixed(2) }}
                  </el-descriptions-item>
                  <el-descriptions-item label="换手率">
                    {{ (tradingStats.turnoverRate * 100).toFixed(1) }}%
                  </el-descriptions-item>
                </el-descriptions>
              </div>
            </el-col>
            <el-col :span="12">
              <div class="trade-distribution">
                <h4>交易分布分析</h4>
                <div ref="tradeDistributionChart" class="chart"></div>
              </div>
            </el-col>
          </el-row>
        </el-tab-pane>

        <el-tab-pane label="风险指标" name="risk">
          <el-row :gutter="24">
            <el-col :span="8">
              <div class="risk-metric">
                <div class="metric-title">最大回撤</div>
                <div class="metric-value negative">
                  {{ Math.abs(riskMetrics.maxDrawdown * 100).toFixed(2) }}%
                </div>
                <div class="metric-subtitle">
                  发生时间: {{ riskMetrics.drawdownDate }}
                </div>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="risk-metric">
                <div class="metric-title">波动率</div>
                <div class="metric-value">
                  {{ (riskMetrics.volatility * 100).toFixed(2) }}%
                </div>
                <div class="metric-subtitle">
                  年化波动率
                </div>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="risk-metric">
                <div class="metric-title">VaR (95%)</div>
                <div class="metric-value negative">
                  {{ Math.abs(riskMetrics.var95 * 100).toFixed(2) }}%
                </div>
                <div class="metric-subtitle">
                  日风险价值
                </div>
              </div>
            </el-col>
          </el-row>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Refresh, Warning, RefreshLeft, Camera, DataBoard, Download
} from '@element-plus/icons-vue'

interface TradingSignal {
  id: string
  symbol: string
  name: string
  action: 'buy' | 'sell'
  strength: number
  currentPrice: number
  targetPrice: number
  suggestedQuantity: number
  expectedReturn: number
}

interface Order {
  id: string
  time: Date
  symbol: string
  side: 'buy' | 'sell'
  quantity: number
  price: number
  status: string
}

interface PerformanceData {
  totalReturn: number
  absoluteReturn: number
  annualizedReturn: number
  excessReturn: number
  sharpeRatio: number
}

interface TradingStats {
  totalTrades: number
  profitableTrades: number
  winRate: number
  avgHoldingPeriod: number
  maxProfit: number
  maxLoss: number
  avgTransactionCost: number
  turnoverRate: number
}

interface RiskMetrics {
  maxDrawdown: number
  drawdownDate: string
  volatility: number
  var95: number
}

interface Props {
  deploymentId: string
}

const props = defineProps<Props>()

// 响应式数据
const tradingStatus = ref<'active' | 'paused'>('active')
const orderFilter = ref('all')
const performancePeriod = ref('month')
const activePerformanceTab = ref('returns')

// 交易设置
const tradingSettings = reactive({
  delay: 1,
  slippage: 0.001
})

// 风险参数
const riskParams = reactive({
  maxSingleOrder: 50,
  maxPosition: 80
})

// 交易信号
const tradingSignals = ref<TradingSignal[]>([
  {
    id: '1',
    symbol: '000001',
    name: '平安银行',
    action: 'buy',
    strength: 0.85,
    currentPrice: 12.45,
    targetPrice: 13.50,
    suggestedQuantity: 1000,
    expectedReturn: 0.084
  },
  {
    id: '2',
    symbol: '600519',
    name: '贵州茅台',
    action: 'sell',
    strength: 0.72,
    currentPrice: 1680.50,
    targetPrice: 1550.00,
    suggestedQuantity: 100,
    expectedReturn: -0.078
  }
])

// 订单列表
const orders = ref<Order[]>([
  {
    id: '1',
    time: new Date(),
    symbol: '000001',
    side: 'buy',
    quantity: 1000,
    price: 12.45,
    status: '待成交'
  },
  {
    id: '2',
    time: new Date(Date.now() - 300000),
    symbol: '600036',
    side: 'sell',
    quantity: 500,
    price: 45.80,
    status: '已成交'
  }
])

// 性能数据
const performanceData = reactive<PerformanceData>({
  totalReturn: 0.0832,
  absoluteReturn: 83200,
  annualizedReturn: 0.285,
  excessReturn: 0.162,
  sharpeRatio: 1.45
})

// 交易统计
const tradingStats = reactive<TradingStats>({
  totalTrades: 156,
  profitableTrades: 95,
  winRate: 0.609,
  avgHoldingPeriod: 3.2,
  maxProfit: 8500,
  maxLoss: -4200,
  avgTransactionCost: 15.6,
  turnoverRate: 2.3
})

// 风险指标
const riskMetrics = reactive<RiskMetrics>({
  maxDrawdown: -0.082,
  drawdownDate: '2024-01-10',
  volatility: 0.18,
  var95: -0.025
})

// 计算属性
const filteredOrders = computed(() => {
  if (orderFilter.value === 'all') return orders.value
  return orders.value.filter(order => {
    switch (orderFilter.value) {
      case 'pending': return order.status === '待成交'
      case 'filled': return order.status === '已成交'
      case 'cancelled': return order.status === '已取消'
      default: return true
    }
  })
})

// 方法
const toggleTrading = () => {
  tradingStatus.value = tradingStatus.value === 'active' ? 'paused' : 'active'
  ElMessage.success(`交易已${tradingStatus.value === 'active' ? '恢复' : '暂停'}`)
}

const executeRebalance = async () => {
  try {
    await ElMessageBox.confirm('确定要执行手动调仓吗？', '调仓确认')
    ElMessage.success('调仓指令已发送')
  } catch {
    // 用户取消
  }
}

const forceLiquidation = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要强制清仓吗？这将立即卖出所有持仓！',
      '清仓确认',
      { type: 'error' }
    )
    ElMessage.success('清仓指令已发送')
  } catch {
    // 用户取消
  }
}

const resetStrategy = async () => {
  try {
    await ElMessageBox.confirm('确定要重置策略吗？', '重置确认')
    ElMessage.success('策略已重置')
  } catch {
    // 用户取消
  }
}

const saveSnapshot = () => {
  ElMessage.success('策略快照已保存')
}

const refreshSignals = () => {
  ElMessage.success('交易信号已刷新')
}

const getSignalColor = (strength: number) => {
  if (strength > 0.8) return '#67c23a'
  if (strength > 0.6) return '#e6a23c'
  return '#f56c6c'
}

const executeSignal = async (signal: TradingSignal) => {
  try {
    await ElMessageBox.confirm(
      `确定要执行${signal.action === 'buy' ? '买入' : '卖出'}信号吗？`,
      '执行确认'
    )
    
    // 添加到订单列表
    const newOrder: Order = {
      id: Date.now().toString(),
      time: new Date(),
      symbol: signal.symbol,
      side: signal.action,
      quantity: signal.suggestedQuantity,
      price: signal.currentPrice,
      status: '待成交'
    }
    orders.value.unshift(newOrder)
    
    ElMessage.success('交易信号已执行')
  } catch {
    // 用户取消
  }
}

const ignoreSignal = (signal: TradingSignal) => {
  const index = tradingSignals.value.findIndex(s => s.id === signal.id)
  if (index > -1) {
    tradingSignals.value.splice(index, 1)
    ElMessage.info('信号已忽略')
  }
}

const viewSignalDetail = (signal: TradingSignal) => {
  ElMessage.info(`查看信号详情: ${signal.symbol}`)
}

const getOrderStatusType = (status: string) => {
  switch (status) {
    case '已成交': return 'success'
    case '待成交': return 'warning'
    case '已取消': return 'info'
    default: return 'info'
  }
}

const cancelOrder = (order: Order) => {
  order.status = '已取消'
  ElMessage.success('订单已取消')
}

const cancelAllPendingOrders = async () => {
  try {
    await ElMessageBox.confirm('确定要取消所有待成交订单吗？', '取消确认')
    
    orders.value.forEach(order => {
      if (order.status === '待成交') {
        order.status = '已取消'
      }
    })
    
    ElMessage.success('所有待成交订单已取消')
  } catch {
    // 用户取消
  }
}

const viewOrderDetail = (order: Order) => {
  ElMessage.info(`查看订单详情: ${order.symbol}`)
}

const exportPerformance = () => {
  ElMessage.info('性能分析报告导出中...')
}

const formatTime = (time: Date) => {
  return time.toLocaleTimeString('zh-CN', { 
    hour: '2-digit', 
    minute: '2-digit' 
  })
}
</script>

<style scoped>
.paper-trading-interface {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.controls-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.trading-status {
  display: flex;
  align-items: center;
  gap: 12px;
}

.control-group {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.control-group h4 {
  margin: 0;
  color: #303133;
  font-size: 14px;
  font-weight: 600;
  border-bottom: 1px solid #e4e7ed;
  padding-bottom: 8px;
}

.strategy-controls,
.quick-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.signals-header,
.orders-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.order-filters {
  display: flex;
  gap: 8px;
}

.signals-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
  max-height: 400px;
  overflow-y: auto;
}

.signal-item {
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
}

.signal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.signal-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.stock-code {
  font-weight: 600;
  color: #303133;
}

.stock-name {
  color: #606266;
  font-size: 14px;
}

.signal-strength {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  justify-content: flex-end;
}

.strength-label {
  font-size: 12px;
  color: #909399;
}

.strength-value {
  font-size: 12px;
  font-weight: 600;
  color: #303133;
  min-width: 30px;
}

.signal-details {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  margin-bottom: 12px;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  font-size: 14px;
}

.label {
  color: #606266;
}

.value {
  font-weight: 600;
  color: #303133;
}

.value.positive {
  color: #67c23a;
}

.value.negative {
  color: #f56c6c;
}

.signal-actions {
  display: flex;
  gap: 8px;
}

.no-signals {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 40px;
  color: #909399;
}

.performance-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.analysis-controls {
  display: flex;
  gap: 12px;
}

.performance-metric,
.risk-metric {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 24px;
  background: #f8f9fa;
  border-radius: 8px;
  text-align: center;
}

.metric-title {
  font-size: 14px;
  color: #606266;
  margin-bottom: 8px;
}

.metric-value {
  font-size: 28px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
}

.metric-value.positive {
  color: #67c23a;
}

.metric-value.negative {
  color: #f56c6c;
}

.metric-subtitle {
  font-size: 12px;
  color: #909399;
}

.performance-chart,
.trade-distribution {
  margin-top: 24px;
}

.performance-chart h4,
.trade-distribution h4 {
  margin: 0 0 16px 0;
  color: #303133;
  text-align: center;
}

.chart {
  width: 100%;
  height: 250px;
  background: #fff;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #909399;
  border: 1px solid #e4e7ed;
}

.trading-stats {
  margin-top: 16px;
}

.trading-stats h4 {
  margin: 0 0 16px 0;
  color: #303133;
}

@media (max-width: 768px) {
  .controls-header,
  .signals-header,
  .orders-header,
  .performance-header {
    flex-direction: column;
    gap: 12px;
  }
  
  .trading-status,
  .order-filters,
  .analysis-controls {
    flex-wrap: wrap;
  }
  
  .control-group {
    padding: 16px;
    background: #f8f9fa;
    border-radius: 6px;
  }
  
  .signal-header {
    flex-direction: column;
    gap: 12px;
  }
  
  .signal-details {
    grid-template-columns: 1fr;
  }
  
  .signal-actions {
    flex-wrap: wrap;
  }
}
</style>