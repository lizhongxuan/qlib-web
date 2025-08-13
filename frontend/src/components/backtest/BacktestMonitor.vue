<template>
  <div class="backtest-monitor">
    <el-card class="monitor-card">
      <template #header>
        <div class="monitor-header">
          <div class="header-title">
            <el-icon><Monitor /></el-icon>
            <span>实时回测监控</span>
          </div>
          <div class="header-controls">
            <el-button-group>
              <el-button 
                size="small" 
                @click="toggleAutoRefresh"
                :type="autoRefresh ? 'primary' : 'default'"
              >
                <el-icon><Timer /></el-icon>
                自动刷新
              </el-button>
              <el-button size="small" @click="refreshData">
                <el-icon><Refresh /></el-icon>
                刷新
              </el-button>
            </el-button-group>
            
            <el-button 
              size="small" 
              type="danger" 
              @click="stopBacktest"
              :loading="stopping"
            >
              <el-icon><Close /></el-icon>
              停止回测
            </el-button>
          </div>
        </div>
      </template>

      <!-- 进度概览 -->
      <div class="progress-section">
        <div class="progress-info">
          <h4>执行进度</h4>
          <el-progress 
            :percentage="progress.percentage" 
            :stroke-width="12"
            text-inside
            :status="getProgressStatus()"
          />
          
          <div class="progress-details">
            <el-row :gutter="24">
              <el-col :span="6">
                <el-statistic title="当前日期" :value="progress.currentDate" />
              </el-col>
              <el-col :span="6">
                <el-statistic 
                  title="已完成天数" 
                  :value="progress.completedDays" 
                  :suffix="`/${progress.totalDays}`" 
                />
              </el-col>
              <el-col :span="6">
                <el-statistic title="平均处理速度" :value="progress.avgSpeed" suffix="天/分钟" />
              </el-col>
              <el-col :span="6">
                <el-statistic title="预计剩余时间" :value="progress.estimatedRemaining" suffix="分钟" />
              </el-col>
            </el-row>
          </div>
        </div>
      </div>

      <!-- 实时性能指标 -->
      <div class="metrics-section">
        <h4>实时性能指标</h4>
        <div class="metrics-grid">
          <el-row :gutter="16">
            <el-col :span="4">
              <div class="metric-card">
                <div class="metric-header">
                  <el-icon><TrendCharts /></el-icon>
                  <span>累计收益率</span>
                </div>
                <div class="metric-value" :class="getValueClass(metrics.totalReturn)">
                  {{ formatPercentage(metrics.totalReturn) }}
                </div>
                <div class="metric-change">
                  <el-icon v-if="metrics.totalReturnChange > 0"><CaretTop /></el-icon>
                  <el-icon v-else-if="metrics.totalReturnChange < 0"><CaretBottom /></el-icon>
                  <span>{{ formatPercentage(Math.abs(metrics.totalReturnChange)) }}</span>
                </div>
              </div>
            </el-col>
            
            <el-col :span="4">
              <div class="metric-card">
                <div class="metric-header">
                  <el-icon><Position /></el-icon>
                  <span>基准收益率</span>
                </div>
                <div class="metric-value" :class="getValueClass(metrics.benchmarkReturn)">
                  {{ formatPercentage(metrics.benchmarkReturn) }}
                </div>
                <div class="metric-change">
                  <el-icon v-if="metrics.benchmarkReturnChange > 0"><CaretTop /></el-icon>
                  <el-icon v-else-if="metrics.benchmarkReturnChange < 0"><CaretBottom /></el-icon>
                  <span>{{ formatPercentage(Math.abs(metrics.benchmarkReturnChange)) }}</span>
                </div>
              </div>
            </el-col>
            
            <el-col :span="4">
              <div class="metric-card">
                <div class="metric-header">
                  <el-icon><DataAnalysis /></el-icon>
                  <span>超额收益</span>
                </div>
                <div class="metric-value" :class="getValueClass(metrics.excessReturn)">
                  {{ formatPercentage(metrics.excessReturn) }}
                </div>
                <div class="metric-change">
                  <el-icon v-if="metrics.excessReturnChange > 0"><CaretTop /></el-icon>
                  <el-icon v-else-if="metrics.excessReturnChange < 0"><CaretBottom /></el-icon>
                  <span>{{ formatPercentage(Math.abs(metrics.excessReturnChange)) }}</span>
                </div>
              </div>
            </el-col>
            
            <el-col :span="4">
              <div class="metric-card">
                <div class="metric-header">
                  <el-icon><Warning /></el-icon>
                  <span>最大回撤</span>
                </div>
                <div class="metric-value negative">
                  {{ formatPercentage(metrics.maxDrawdown) }}
                </div>
                <div class="metric-change">
                  <el-icon v-if="metrics.maxDrawdownChange > 0"><CaretTop /></el-icon>
                  <el-icon v-else-if="metrics.maxDrawdownChange < 0"><CaretBottom /></el-icon>
                  <span>{{ formatPercentage(Math.abs(metrics.maxDrawdownChange)) }}</span>
                </div>
              </div>
            </el-col>
            
            <el-col :span="4">
              <div class="metric-card">
                <div class="metric-header">
                  <el-icon><Odometer /></el-icon>
                  <span>夏普比率</span>
                </div>
                <div class="metric-value">
                  {{ metrics.sharpeRatio.toFixed(3) }}
                </div>
                <div class="metric-change">
                  <el-icon v-if="metrics.sharpeRatioChange > 0"><CaretTop /></el-icon>
                  <el-icon v-else-if="metrics.sharpeRatioChange < 0"><CaretBottom /></el-icon>
                  <span>{{ Math.abs(metrics.sharpeRatioChange).toFixed(3) }}</span>
                </div>
              </div>
            </el-col>
            
            <el-col :span="4">
              <div class="metric-card">
                <div class="metric-header">
                  <el-icon><Money /></el-icon>
                  <span>当前净值</span>
                </div>
                <div class="metric-value">
                  {{ metrics.netValue.toFixed(4) }}
                </div>
                <div class="metric-change">
                  <el-icon v-if="metrics.netValueChange > 0"><CaretTop /></el-icon>
                  <el-icon v-else-if="metrics.netValueChange < 0"><CaretBottom /></el-icon>
                  <span>{{ Math.abs(metrics.netValueChange).toFixed(4) }}</span>
                </div>
              </div>
            </el-col>
          </el-row>
        </div>
      </div>

      <!-- 实时图表 -->
      <div class="charts-section">
        <el-tabs v-model="activeChartTab" type="border-card">
          <el-tab-pane label="收益曲线" name="returns">
            <div ref="returnsChartRef" class="chart-container"></div>
          </el-tab-pane>
          <el-tab-pane label="回撤分析" name="drawdown">
            <div ref="drawdownChartRef" class="chart-container"></div>
          </el-tab-pane>
          <el-tab-pane label="持仓权重" name="positions">
            <div ref="positionsChartRef" class="chart-container"></div>
          </el-tab-pane>
        </el-tabs>
      </div>

      <!-- 执行日志 -->
      <div class="logs-section">
        <div class="logs-header">
          <h4>执行日志</h4>
          <div class="logs-controls">
            <el-select v-model="logLevel" size="small" style="width: 100px">
              <el-option label="全部" value="all" />
              <el-option label="信息" value="info" />
              <el-option label="警告" value="warn" />
              <el-option label="错误" value="error" />
            </el-select>
            <el-button size="small" @click="clearLogs">
              <el-icon><Delete /></el-icon>
              清空日志
            </el-button>
            <el-button size="small" @click="exportLogs">
              <el-icon><Download /></el-icon>
              导出日志
            </el-button>
          </div>
        </div>
        
        <div class="logs-container" ref="logsContainer">
          <div
            v-for="log in filteredLogs"
            :key="log.id"
            class="log-entry"
            :class="getLogClass(log.level)"
          >
            <span class="log-timestamp">{{ formatTime(log.timestamp) }}</span>
            <span class="log-level">{{ log.level.toUpperCase() }}</span>
            <span class="log-message">{{ log.message }}</span>
            <span v-if="log.data" class="log-data">{{ JSON.stringify(log.data) }}</span>
          </div>
        </div>
      </div>

      <!-- 系统资源监控 -->
      <div class="resources-section">
        <h4>系统资源</h4>
        <el-row :gutter="16">
          <el-col :span="6">
            <el-progress
              type="dashboard"
              :percentage="resources.cpu"
              :width="100"
            >
              <template #default="{ percentage }">
                <span class="resource-label">CPU</span>
                <span class="resource-value">{{ percentage }}%</span>
              </template>
            </el-progress>
          </el-col>
          <el-col :span="6">
            <el-progress
              type="dashboard"
              :percentage="resources.memory"
              :width="100"
              color="#67c23a"
            >
              <template #default="{ percentage }">
                <span class="resource-label">内存</span>
                <span class="resource-value">{{ percentage }}%</span>
              </template>
            </el-progress>
          </el-col>
          <el-col :span="6">
            <el-progress
              type="dashboard"
              :percentage="resources.disk"
              :width="100"
              color="#e6a23c"
            >
              <template #default="{ percentage }">
                <span class="resource-label">磁盘</span>
                <span class="resource-value">{{ percentage }}%</span>
              </template>
            </el-progress>
          </el-col>
          <el-col :span="6">
            <div class="network-info">
              <div class="network-item">
                <span class="network-label">网络延迟</span>
                <span class="network-value">{{ resources.latency }}ms</span>
              </div>
              <div class="network-item">
                <span class="network-label">数据吞吐</span>
                <span class="network-value">{{ resources.throughput }}MB/s</span>
              </div>
            </div>
          </el-col>
        </el-row>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Monitor, Timer, Refresh, Close, TrendCharts, Position, DataAnalysis,
  Warning, Odometer, Money, CaretTop, CaretBottom, Delete, Download
} from '@element-plus/icons-vue'

// Props
interface Props {
  backtestId?: string
  autoStart?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  backtestId: '',
  autoStart: false
})

// Emits
const emit = defineEmits<{
  'backtest-stopped': []
  'backtest-completed': [result: any]
  'error': [error: any]
}>()

// 响应式数据
const stopping = ref(false)
const autoRefresh = ref(true)
const refreshInterval = ref<NodeJS.Timeout | null>(null)
const activeChartTab = ref('returns')
const logLevel = ref('all')

// 进度数据
const progress = reactive({
  percentage: 0,
  currentDate: '2022-01-01',
  completedDays: 0,
  totalDays: 365,
  avgSpeed: 0,
  estimatedRemaining: 0,
  status: 'running' as 'running' | 'paused' | 'completed' | 'error'
})

// 性能指标
const metrics = reactive({
  totalReturn: 0,
  totalReturnChange: 0,
  benchmarkReturn: 0,
  benchmarkReturnChange: 0,
  excessReturn: 0,
  excessReturnChange: 0,
  maxDrawdown: 0,
  maxDrawdownChange: 0,
  sharpeRatio: 0,
  sharpeRatioChange: 0,
  netValue: 1.0000,
  netValueChange: 0
})

// 系统资源
const resources = reactive({
  cpu: 45,
  memory: 32,
  disk: 18,
  latency: 12,
  throughput: 2.4
})

// 日志数据
const logs = ref<Array<{
  id: number
  timestamp: number
  level: 'info' | 'warn' | 'error'
  message: string
  data?: any
}>>([])

// 图表引用
const returnsChartRef = ref()
const drawdownChartRef = ref()
const positionsChartRef = ref()
const logsContainer = ref()

// 计算属性
const filteredLogs = computed(() => {
  if (logLevel.value === 'all') return logs.value
  return logs.value.filter(log => log.level === logLevel.value)
})

// 方法
const toggleAutoRefresh = () => {
  autoRefresh.value = !autoRefresh.value
  if (autoRefresh.value) {
    startAutoRefresh()
  } else {
    stopAutoRefresh()
  }
}

const startAutoRefresh = () => {
  if (refreshInterval.value) return
  
  refreshInterval.value = setInterval(() => {
    refreshData()
  }, 2000) // 每2秒刷新一次
}

const stopAutoRefresh = () => {
  if (refreshInterval.value) {
    clearInterval(refreshInterval.value)
    refreshInterval.value = null
  }
}

const refreshData = async () => {
  try {
    // 模拟数据更新
    await simulateDataUpdate()
    
    // 更新图表
    updateCharts()
    
    // 滚动日志到底部
    scrollLogsToBottom()
  } catch (error) {
    console.error('刷新数据失败:', error)
    addLog('error', '数据刷新失败', { error })
  }
}

const simulateDataUpdate = async () => {
  // 模拟进度更新
  if (progress.status === 'running' && progress.percentage < 100) {
    const increment = Math.random() * 2
    progress.percentage = Math.min(100, progress.percentage + increment)
    progress.completedDays = Math.floor((progress.percentage / 100) * progress.totalDays)
    progress.avgSpeed = Math.random() * 10 + 5
    progress.estimatedRemaining = Math.max(0, (100 - progress.percentage) / 2)
    
    // 更新当前日期
    const startDate = new Date('2022-01-01')
    const currentDateObj = new Date(startDate.getTime() + progress.completedDays * 24 * 60 * 60 * 1000)
    progress.currentDate = currentDateObj.toISOString().split('T')[0]
  }
  
  // 模拟指标更新
  const prevTotalReturn = metrics.totalReturn
  const prevBenchmarkReturn = metrics.benchmarkReturn
  const prevMaxDrawdown = metrics.maxDrawdown
  const prevSharpeRatio = metrics.sharpeRatio
  const prevNetValue = metrics.netValue
  
  metrics.totalReturn += (Math.random() - 0.48) * 0.5
  metrics.benchmarkReturn += (Math.random() - 0.52) * 0.3
  metrics.excessReturn = metrics.totalReturn - metrics.benchmarkReturn
  metrics.maxDrawdown = Math.min(metrics.maxDrawdown, -Math.random() * 2)
  metrics.sharpeRatio = Math.max(0, metrics.sharpeRatio + (Math.random() - 0.5) * 0.1)
  metrics.netValue = 1 + (metrics.totalReturn / 100)
  
  // 计算变化
  metrics.totalReturnChange = metrics.totalReturn - prevTotalReturn
  metrics.benchmarkReturnChange = metrics.benchmarkReturn - prevBenchmarkReturn
  metrics.excessReturnChange = metrics.excessReturn - (prevTotalReturn - prevBenchmarkReturn)
  metrics.maxDrawdownChange = metrics.maxDrawdown - prevMaxDrawdown
  metrics.sharpeRatioChange = metrics.sharpeRatio - prevSharpeRatio
  metrics.netValueChange = metrics.netValue - prevNetValue
  
  // 模拟系统资源更新
  resources.cpu = Math.max(10, Math.min(90, resources.cpu + (Math.random() - 0.5) * 10))
  resources.memory = Math.max(10, Math.min(80, resources.memory + (Math.random() - 0.5) * 5))
  resources.disk = Math.max(5, Math.min(50, resources.disk + (Math.random() - 0.5) * 2))
  resources.latency = Math.max(5, Math.min(100, resources.latency + (Math.random() - 0.5) * 10))
  resources.throughput = Math.max(0.1, Math.min(10, resources.throughput + (Math.random() - 0.5) * 1))
  
  // 随机添加日志
  if (Math.random() < 0.3) {
    const messages = [
      '处理股票预测数据',
      '计算组合权重',
      '执行交易信号',
      '更新持仓信息',
      '风险检查通过',
      '数据验证完成'
    ]
    const levels = ['info', 'info', 'info', 'warn'] as const
    const message = messages[Math.floor(Math.random() * messages.length)]
    const level = levels[Math.floor(Math.random() * levels.length)]
    
    addLog(level, `${message} - 日期: ${progress.currentDate}`, {
      date: progress.currentDate,
      progress: `${progress.percentage.toFixed(1)}%`
    })
  }
  
  // 检查完成状态
  if (progress.percentage >= 100 && progress.status === 'running') {
    progress.status = 'completed'
    addLog('info', '回测执行完成!', {
      totalReturn: metrics.totalReturn.toFixed(2),
      sharpeRatio: metrics.sharpeRatio.toFixed(3)
    })
    stopAutoRefresh()
    emit('backtest-completed', {
      metrics: { ...metrics },
      progress: { ...progress }
    })
  }
}

const stopBacktest = async () => {
  try {
    await ElMessageBox.confirm('确定要停止当前回测吗？', '确认停止', {
      type: 'warning'
    })
    
    stopping.value = true
    
    // 模拟停止过程
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    progress.status = 'paused'
    stopAutoRefresh()
    addLog('warn', '回测已被用户停止')
    
    emit('backtest-stopped')
    ElMessage.warning('回测已停止')
  } catch {
    // 用户取消
  } finally {
    stopping.value = false
  }
}

const updateCharts = () => {
  // 这里应该调用图表库（如ECharts）更新图表
  // 由于示例代码，这里只是模拟
  console.log('更新图表...')
}

const addLog = (level: 'info' | 'warn' | 'error', message: string, data?: any) => {
  const log = {
    id: Date.now() + Math.random(),
    timestamp: Date.now(),
    level,
    message,
    data
  }
  
  logs.value.push(log)
  
  // 限制日志数量
  if (logs.value.length > 500) {
    logs.value = logs.value.slice(-400)
  }
  
  nextTick(() => {
    scrollLogsToBottom()
  })
}

const scrollLogsToBottom = () => {
  if (logsContainer.value) {
    logsContainer.value.scrollTop = logsContainer.value.scrollHeight
  }
}

const clearLogs = () => {
  logs.value = []
  ElMessage.success('日志已清空')
}

const exportLogs = () => {
  const logText = logs.value
    .map(log => `[${formatTime(log.timestamp)}] ${log.level.toUpperCase()}: ${log.message}`)
    .join('\n')
  
  const blob = new Blob([logText], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `backtest-logs-${Date.now()}.txt`
  a.click()
  URL.revokeObjectURL(url)
  
  ElMessage.success('日志导出成功')
}

// 辅助方法
const getProgressStatus = () => {
  switch (progress.status) {
    case 'completed': return 'success'
    case 'error': return 'exception'
    case 'paused': return 'warning'
    default: return undefined
  }
}

const getValueClass = (value: number) => {
  return value >= 0 ? 'positive' : 'negative'
}

const getLogClass = (level: string) => {
  return {
    'log-info': level === 'info',
    'log-warn': level === 'warn',
    'log-error': level === 'error'
  }
}

const formatPercentage = (value: number) => {
  return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`
}

const formatTime = (timestamp: number) => {
  return new Date(timestamp).toLocaleTimeString('zh-CN')
}

// 生命周期
onMounted(() => {
  // 初始化数据
  addLog('info', '开始监控回测执行')
  
  if (props.autoStart && autoRefresh.value) {
    startAutoRefresh()
  }
  
  // 模拟初始数据
  simulateDataUpdate()
})

onUnmounted(() => {
  stopAutoRefresh()
})
</script>

<style scoped>
.backtest-monitor {
  width: 100%;
}

.monitor-card {
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.monitor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.header-controls {
  display: flex;
  gap: 12px;
  align-items: center;
}

.progress-section {
  margin-bottom: 32px;
}

.progress-section h4 {
  margin: 0 0 16px 0;
  color: #303133;
  font-size: 16px;
  font-weight: 600;
}

.progress-details {
  margin-top: 16px;
}

.metrics-section {
  margin-bottom: 32px;
}

.metrics-section h4 {
  margin: 0 0 16px 0;
  color: #303133;
  font-size: 16px;
  font-weight: 600;
}

.metrics-grid {
  margin-top: 16px;
}

.metric-card {
  padding: 16px;
  background: linear-gradient(135deg, #f0f8ff 0%, #e8f4fd 100%);
  border-radius: 8px;
  border: 1px solid #d4e4fd;
  text-align: center;
  transition: all 0.3s ease;
}

.metric-card:hover {
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.2);
}

.metric-header {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin-bottom: 12px;
  color: #606266;
  font-size: 14px;
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

.metric-change {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  font-size: 12px;
  color: #909399;
}

.charts-section {
  margin-bottom: 32px;
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
  font-size: 14px;
}

.logs-section {
  margin-bottom: 32px;
}

.logs-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.logs-header h4 {
  margin: 0;
  color: #303133;
  font-size: 16px;
  font-weight: 600;
}

.logs-controls {
  display: flex;
  gap: 8px;
  align-items: center;
}

.logs-container {
  height: 300px;
  overflow-y: auto;
  background: #1e1e1e;
  border-radius: 6px;
  padding: 16px;
  font-family: 'Monaco', 'Menlo', monospace;
  font-size: 13px;
}

.log-entry {
  display: flex;
  gap: 12px;
  margin-bottom: 4px;
  line-height: 1.4;
}

.log-entry.log-info .log-message {
  color: #e8e8e8;
}

.log-entry.log-warn .log-message {
  color: #f1c40f;
}

.log-entry.log-error .log-message {
  color: #e74c3c;
}

.log-timestamp {
  color: #666;
  flex-shrink: 0;
  min-width: 80px;
}

.log-level {
  color: #888;
  flex-shrink: 0;
  min-width: 50px;
  font-weight: 600;
}

.log-message {
  flex: 1;
}

.log-data {
  color: #3498db;
  font-size: 12px;
}

.resources-section {
  margin-bottom: 32px;
}

.resources-section h4 {
  margin: 0 0 16px 0;
  color: #303133;
  font-size: 16px;
  font-weight: 600;
}

.resource-label {
  display: block;
  font-size: 14px;
  color: #606266;
  margin-bottom: 4px;
}

.resource-value {
  display: block;
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.network-info {
  height: 100px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 16px;
}

.network-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.network-label {
  color: #606266;
  font-size: 14px;
}

.network-value {
  color: #303133;
  font-weight: 600;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .monitor-header {
    flex-direction: column;
    gap: 12px;
  }
  
  .header-controls {
    width: 100%;
    justify-content: space-between;
  }
  
  .metric-card {
    margin-bottom: 16px;
  }
  
  .logs-header {
    flex-direction: column;
    gap: 12px;
    align-items: flex-start;
  }
  
  .logs-controls {
    width: 100%;
    justify-content: flex-end;
  }
}
</style>