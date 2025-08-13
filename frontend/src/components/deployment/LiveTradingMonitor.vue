<template>
  <div class="live-trading-monitor">
    <!-- 实时状态概览 -->
    <el-card class="status-overview">
      <template #header>
        <div class="header-with-refresh">
          <span>实时交易状态</span>
          <div class="refresh-controls">
            <el-switch 
              v-model="autoRefresh" 
              active-text="自动刷新"
              :active-value="true"
              :inactive-value="false"
            />
            <el-button size="small" @click="refreshData">
              <el-icon><Refresh /></el-icon>
              手动刷新
            </el-button>
          </div>
        </div>
      </template>

      <div class="status-grid">
        <el-row :gutter="24">
          <el-col :span="6">
            <el-statistic 
              title="账户净值" 
              :value="monitorData.netValue" 
              :precision="4"
              :class="{ 'value-up': monitorData.netValueChange > 0, 'value-down': monitorData.netValueChange < 0 }"
            >
              <template #suffix>
                <span class="change-indicator">
                  <el-icon v-if="monitorData.netValueChange > 0"><CaretTop /></el-icon>
                  <el-icon v-else-if="monitorData.netValueChange < 0"><CaretBottom /></el-icon>
                  {{ Math.abs(monitorData.netValueChange * 100).toFixed(2) }}%
                </span>
              </template>
            </el-statistic>
          </el-col>
          <el-col :span="6">
            <el-statistic 
              title="可用资金" 
              :value="monitorData.availableCash" 
              :precision="2" 
              suffix="元"
            />
          </el-col>
          <el-col :span="6">
            <el-statistic 
              title="持仓市值" 
              :value="monitorData.positionValue" 
              :precision="2" 
              suffix="元"
            />
          </el-col>
          <el-col :span="6">
            <el-statistic 
              title="当日成交" 
              :value="monitorData.todayTrades" 
              suffix="笔"
            />
          </el-col>
        </el-row>

        <el-row :gutter="24" class="second-row">
          <el-col :span="6">
            <el-statistic 
              title="今日收益" 
              :value="monitorData.todayPnL" 
              :precision="2" 
              suffix="元"
              :class="{ 'value-up': monitorData.todayPnL > 0, 'value-down': monitorData.todayPnL < 0 }"
            />
          </el-col>
          <el-col :span="6">
            <el-statistic 
              title="累计收益率" 
              :value="monitorData.totalReturn * 100" 
              :precision="2" 
              suffix="%"
              :class="{ 'value-up': monitorData.totalReturn > 0, 'value-down': monitorData.totalReturn < 0 }"
            />
          </el-col>
          <el-col :span="6">
            <el-statistic 
              title="当前回撤" 
              :value="Math.abs(monitorData.currentDrawdown * 100)" 
              :precision="2" 
              suffix="%"
              class="value-down"
            />
          </el-col>
          <el-col :span="6">
            <el-statistic 
              title="运行天数" 
              :value="monitorData.runningDays" 
              suffix="天"
            />
          </el-col>
        </el-row>
      </div>
    </el-card>

    <!-- 图表监控 -->
    <el-row :gutter="24" class="charts-section">
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="chart-header">
              <span>净值曲线</span>
              <el-select v-model="netValueTimeRange" size="small" style="width: 120px;">
                <el-option label="今日" value="today" />
                <el-option label="近7天" value="week" />
                <el-option label="近30天" value="month" />
                <el-option label="全部" value="all" />
              </el-select>
            </div>
          </template>
          <div ref="netValueChart" class="chart-container"></div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>持仓分布</span>
          </template>
          <div ref="positionChart" class="chart-container"></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 实时交易记录 -->
    <el-card class="trading-records">
      <template #header>
        <div class="records-header">
          <span>实时交易记录</span>
          <div class="record-filters">
            <el-select v-model="tradeFilter" size="small" style="width: 100px;">
              <el-option label="全部" value="all" />
              <el-option label="买入" value="buy" />
              <el-option label="卖出" value="sell" />
            </el-select>
            <el-button size="small" @click="exportTrades">
              <el-icon><Download /></el-icon>
              导出
            </el-button>
          </div>
        </div>
      </template>

      <el-table :data="filteredTrades" size="small" max-height="300">
        <el-table-column prop="time" label="时间" width="100">
          <template #default="{ row }">
            {{ formatTime(row.time) }}
          </template>
        </el-table-column>
        <el-table-column prop="symbol" label="股票代码" width="100" />
        <el-table-column prop="name" label="股票名称" width="120" />
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
        <el-table-column prop="commission" label="手续费" width="100">
          <template #default="{ row }">
            ¥{{ row.commission.toFixed(2) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button size="small" @click="viewTradeDetail(row)">详情</el-button>
            <el-button 
              v-if="row.status === '待成交'" 
              size="small" 
              type="danger" 
              @click="cancelTrade(row)"
            >
              撤单
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 持仓明细 -->
    <el-card class="position-details">
      <template #header>
        <div class="position-header">
          <span>当前持仓明细</span>
          <div class="position-actions">
            <el-button size="small" @click="refreshPositions">
              <el-icon><Refresh /></el-icon>
              刷新持仓
            </el-button>
            <el-button size="small" @click="exportPositions">
              <el-icon><Download /></el-icon>
              导出持仓
            </el-button>
          </div>
        </div>
      </template>

      <el-table :data="positions" size="small">
        <el-table-column prop="symbol" label="股票代码" width="100" />
        <el-table-column prop="name" label="股票名称" width="150" />
        <el-table-column prop="quantity" label="持仓数量" width="100" />
        <el-table-column prop="currentPrice" label="现价" width="100">
          <template #default="{ row }">
            ¥{{ row.currentPrice.toFixed(2) }}
          </template>
        </el-table-column>
        <el-table-column prop="avgCost" label="成本价" width="100">
          <template #default="{ row }">
            ¥{{ row.avgCost.toFixed(2) }}
          </template>
        </el-table-column>
        <el-table-column prop="marketValue" label="市值" width="120">
          <template #default="{ row }">
            ¥{{ row.marketValue.toFixed(2) }}
          </template>
        </el-table-column>
        <el-table-column prop="unrealizedPnL" label="浮动盈亏" width="120">
          <template #default="{ row }">
            <span :class="{ 'profit': row.unrealizedPnL > 0, 'loss': row.unrealizedPnL < 0 }">
              ¥{{ row.unrealizedPnL.toFixed(2) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="returnRate" label="收益率" width="100">
          <template #default="{ row }">
            <span :class="{ 'profit': row.returnRate > 0, 'loss': row.returnRate < 0 }">
              {{ (row.returnRate * 100).toFixed(2) }}%
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="weight" label="权重" width="100">
          <template #default="{ row }">
            {{ (row.weight * 100).toFixed(2) }}%
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button size="small" @click="viewStockDetail(row)">详情</el-button>
            <el-button size="small" type="danger" @click="manualTrade(row)">交易</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 系统状态监控 -->
    <el-card class="system-status">
      <template #header>
        <span>系统状态监控</span>
      </template>

      <el-row :gutter="24">
        <el-col :span="8">
          <div class="status-item">
            <div class="status-label">策略运行状态</div>
            <div class="status-value">
              <el-tag :type="systemStatus.strategy === 'running' ? 'success' : 'danger'">
                {{ systemStatus.strategy === 'running' ? '正常运行' : '已停止' }}
              </el-tag>
            </div>
          </div>
        </el-col>
        <el-col :span="8">
          <div class="status-item">
            <div class="status-label">数据连接状态</div>
            <div class="status-value">
              <el-tag :type="systemStatus.dataConnection === 'connected' ? 'success' : 'danger'">
                {{ systemStatus.dataConnection === 'connected' ? '连接正常' : '连接异常' }}
              </el-tag>
            </div>
          </div>
        </el-col>
        <el-col :span="8">
          <div class="status-item">
            <div class="status-label">交易接口状态</div>
            <div class="status-value">
              <el-tag :type="systemStatus.tradingInterface === 'active' ? 'success' : 'danger'">
                {{ systemStatus.tradingInterface === 'active' ? '接口正常' : '接口异常' }}
              </el-tag>
            </div>
          </div>
        </el-col>
      </el-row>

      <el-row :gutter="24" class="second-status-row">
        <el-col :span="8">
          <div class="status-item">
            <div class="status-label">最后更新时间</div>
            <div class="status-value">{{ formatTime(systemStatus.lastUpdate) }}</div>
          </div>
        </el-col>
        <el-col :span="8">
          <div class="status-item">
            <div class="status-label">网络延迟</div>
            <div class="status-value">{{ systemStatus.networkLatency }}ms</div>
          </div>
        </el-col>
        <el-col :span="8">
          <div class="status-item">
            <div class="status-label">CPU使用率</div>
            <div class="status-value">{{ systemStatus.cpuUsage }}%</div>
          </div>
        </el-col>
      </el-row>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Refresh, CaretTop, CaretBottom, Download
} from '@element-plus/icons-vue'

interface MonitorData {
  netValue: number
  netValueChange: number
  availableCash: number
  positionValue: number
  todayTrades: number
  todayPnL: number
  totalReturn: number
  currentDrawdown: number
  runningDays: number
}

interface Trade {
  id: string
  time: Date
  symbol: string
  name: string
  side: 'buy' | 'sell'
  quantity: number
  price: number
  amount: number
  status: string
  commission: number
}

interface Position {
  symbol: string
  name: string
  quantity: number
  currentPrice: number
  avgCost: number
  marketValue: number
  unrealizedPnL: number
  returnRate: number
  weight: number
}

interface SystemStatus {
  strategy: string
  dataConnection: string
  tradingInterface: string
  lastUpdate: Date
  networkLatency: number
  cpuUsage: number
}

interface Props {
  deploymentId: string
}

const props = defineProps<Props>()

// 响应式数据
const autoRefresh = ref(true)
const netValueTimeRange = ref('today')
const tradeFilter = ref('all')
const refreshTimer = ref<number>()

// 监控数据
const monitorData = reactive<MonitorData>({
  netValue: 1.0832,
  netValueChange: 0.012,
  availableCash: 285000,
  positionValue: 715000,
  todayTrades: 8,
  todayPnL: 1250.0,
  totalReturn: 0.0832,
  currentDrawdown: -0.025,
  runningDays: 45
})

// 交易记录
const trades = ref<Trade[]>([
  {
    id: '1',
    time: new Date('2024-01-15 14:35:22'),
    symbol: '000001',
    name: '平安银行',
    side: 'buy',
    quantity: 1000,
    price: 12.45,
    amount: 12450,
    status: '已成交',
    commission: 6.23
  },
  {
    id: '2',
    time: new Date('2024-01-15 14:30:15'),
    symbol: '600036',
    name: '招商银行',
    side: 'sell',
    quantity: 500,
    price: 45.80,
    amount: 22900,
    status: '已成交',
    commission: 11.45
  }
])

// 持仓明细
const positions = ref<Position[]>([
  {
    symbol: '600519',
    name: '贵州茅台',
    quantity: 100,
    currentPrice: 1680.50,
    avgCost: 1620.30,
    marketValue: 168050,
    unrealizedPnL: 6020,
    returnRate: 0.037,
    weight: 0.168
  },
  {
    symbol: '000858',
    name: '五粮液',
    quantity: 200,
    currentPrice: 156.80,
    avgCost: 148.20,
    marketValue: 31360,
    unrealizedPnL: 1720,
    returnRate: 0.058,
    weight: 0.031
  }
])

// 系统状态
const systemStatus = reactive<SystemStatus>({
  strategy: 'running',
  dataConnection: 'connected',
  tradingInterface: 'active',
  lastUpdate: new Date(),
  networkLatency: 45,
  cpuUsage: 28
})

// 计算属性
const filteredTrades = computed(() => {
  if (tradeFilter.value === 'all') return trades.value
  return trades.value.filter(trade => trade.side === tradeFilter.value)
})

// 方法
const refreshData = () => {
  // 模拟数据更新
  monitorData.netValue += (Math.random() - 0.5) * 0.01
  monitorData.netValueChange = (Math.random() - 0.5) * 0.02
  monitorData.todayPnL += (Math.random() - 0.5) * 200
  systemStatus.lastUpdate = new Date()
  systemStatus.networkLatency = Math.floor(Math.random() * 100) + 20
  systemStatus.cpuUsage = Math.floor(Math.random() * 40) + 20
  
  ElMessage.success('数据已刷新')
}

const startAutoRefresh = () => {
  if (refreshTimer.value) {
    clearInterval(refreshTimer.value)
  }
  
  if (autoRefresh.value) {
    refreshTimer.value = window.setInterval(() => {
      refreshData()
    }, 5000) // 每5秒刷新一次
  }
}

const stopAutoRefresh = () => {
  if (refreshTimer.value) {
    clearInterval(refreshTimer.value)
    refreshTimer.value = undefined
  }
}

const formatTime = (time: Date) => {
  return time.toLocaleTimeString()
}

const getTradeStatusType = (status: string) => {
  switch (status) {
    case '已成交': return 'success'
    case '待成交': return 'warning'
    case '已撤销': return 'info'
    default: return 'info'
  }
}

const exportTrades = () => {
  ElMessage.info('导出交易记录功能开发中...')
}

const exportPositions = () => {
  ElMessage.info('导出持仓明细功能开发中...')
}

const refreshPositions = () => {
  // 模拟持仓数据更新
  positions.value.forEach(pos => {
    pos.currentPrice += (Math.random() - 0.5) * 10
    pos.marketValue = pos.quantity * pos.currentPrice
    pos.unrealizedPnL = pos.marketValue - (pos.quantity * pos.avgCost)
    pos.returnRate = pos.unrealizedPnL / (pos.quantity * pos.avgCost)
  })
  ElMessage.success('持仓数据已刷新')
}

const viewTradeDetail = (trade: Trade) => {
  ElMessage.info(`查看交易详情: ${trade.symbol}`)
}

const cancelTrade = (trade: Trade) => {
  ElMessage.info(`撤销交易: ${trade.symbol}`)
}

const viewStockDetail = (position: Position) => {
  ElMessage.info(`查看股票详情: ${position.symbol}`)
}

const manualTrade = (position: Position) => {
  ElMessage.info(`手动交易: ${position.symbol}`)
}

// 生命周期
onMounted(() => {
  startAutoRefresh()
})

onUnmounted(() => {
  stopAutoRefresh()
})

// 监听自动刷新状态变化
watch(autoRefresh, (newValue) => {
  if (newValue) {
    startAutoRefresh()
  } else {
    stopAutoRefresh()
  }
})
</script>

<style scoped>
.live-trading-monitor {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.header-with-refresh {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.refresh-controls {
  display: flex;
  align-items: center;
  gap: 12px;
}

.status-grid {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.second-row {
  margin-top: 0;
}

.value-up {
  color: #67c23a;
}

.value-down {
  color: #f56c6c;
}

.change-indicator {
  font-size: 14px;
  margin-left: 8px;
}

.charts-section {
  margin: 0;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chart-container {
  width: 100%;
  height: 300px;
  background: #f8f9fa;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #909399;
}

.records-header,
.position-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.record-filters,
.position-actions {
  display: flex;
  gap: 8px;
}

.profit {
  color: #67c23a;
}

.loss {
  color: #f56c6c;
}

.system-status {
  margin-top: 0;
}

.status-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 6px;
  text-align: center;
}

.status-label {
  font-size: 14px;
  color: #606266;
}

.status-value {
  font-weight: 600;
  color: #303133;
}

.second-status-row {
  margin-top: 16px;
}

@media (max-width: 768px) {
  .header-with-refresh,
  .chart-header,
  .records-header,
  .position-header {
    flex-direction: column;
    gap: 12px;
  }
  
  .refresh-controls,
  .record-filters,
  .position-actions {
    flex-wrap: wrap;
  }
  
  .status-grid .el-row {
    flex-direction: column;
  }
  
  .status-grid .el-col {
    margin-bottom: 12px;
  }
}
</style>