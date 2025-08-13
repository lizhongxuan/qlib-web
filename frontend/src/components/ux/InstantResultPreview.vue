<template>
  <div class="instant-result-preview">
    <!-- 预览模式选择 -->
    <div class="preview-header">
      <h3>
        <el-icon><TrendCharts /></el-icon>
        即时结果预览
      </h3>
      <div class="preview-controls">
        <el-button-group>
          <el-button 
            :type="previewMode === 'summary' ? 'primary' : ''" 
            @click="previewMode = 'summary'"
          >
            概览
          </el-button>
          <el-button 
            :type="previewMode === 'detailed' ? 'primary' : ''" 
            @click="previewMode = 'detailed'"
          >
            详细
          </el-button>
          <el-button 
            :type="previewMode === 'realtime' ? 'primary' : ''" 
            @click="previewMode = 'realtime'"
          >
            实时
          </el-button>
        </el-button-group>
        
        <el-button @click="refreshPreview" :loading="isLoading">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>

    <!-- 概览模式 -->
    <div v-if="previewMode === 'summary'" class="preview-content">
      <!-- 核心指标卡片 -->
      <div class="metrics-grid">
        <el-card class="metric-card" v-for="metric in summaryMetrics" :key="metric.key">
          <el-statistic 
            :title="metric.title" 
            :value="metric.value" 
            :suffix="metric.suffix"
            :precision="metric.precision"
            :value-style="{ color: metric.color }"
          >
            <template #prefix>
              <el-icon :style="{ color: metric.color }">
                <component :is="metric.icon" />
              </el-icon>
            </template>
          </el-statistic>
          <div class="metric-trend">
            <el-icon :class="metric.trend === 'up' ? 'trend-up' : 'trend-down'">
              <component :is="metric.trend === 'up' ? 'CaretTop' : 'CaretBottom'" />
            </el-icon>
            <span :class="metric.trend === 'up' ? 'trend-up' : 'trend-down'">
              {{ metric.change }}%
            </span>
          </div>
        </el-card>
      </div>

      <!-- 快速图表 -->
      <div class="quick-charts">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-card>
              <template #header>
                <h4>净值曲线</h4>
              </template>
              <div ref="navChart" class="chart-container"></div>
            </el-card>
          </el-col>
          <el-col :span="12">
            <el-card>
              <template #header>
                <h4>收益分布</h4>
              </template>
              <div ref="returnChart" class="chart-container"></div>
            </el-card>
          </el-col>
        </el-row>
      </div>

      <!-- 关键洞察 -->
      <el-card class="insights-card">
        <template #header>
          <h4>关键洞察</h4>
        </template>
        <div class="insights-list">
          <div v-for="insight in keyInsights" :key="insight.id" class="insight-item">
            <div class="insight-icon">
              <el-icon :style="{ color: insight.color }">
                <component :is="insight.icon" />
              </el-icon>
            </div>
            <div class="insight-content">
              <h5>{{ insight.title }}</h5>
              <p>{{ insight.description }}</p>
            </div>
            <div class="insight-value">
              <el-tag :type="insight.type">{{ insight.value }}</el-tag>
            </div>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 详细模式 -->
    <div v-if="previewMode === 'detailed'" class="preview-content">
      <el-tabs v-model="activeDetailTab" class="detail-tabs">
        <!-- 性能分析 -->
        <el-tab-pane label="性能分析" name="performance">
          <div class="performance-analysis">
            <!-- 详细指标表格 -->
            <el-card class="metrics-table">
              <template #header>
                <h4>详细指标</h4>
              </template>
              <el-table :data="detailedMetrics" size="small">
                <el-table-column prop="category" label="类别" width="120" />
                <el-table-column prop="metric" label="指标" />
                <el-table-column prop="value" label="数值" width="120">
                  <template #default="{ row }">
                    <span :style="{ color: row.color }">{{ row.value }}{{ row.suffix }}</span>
                  </template>
                </el-table-column>
                <el-table-column prop="rank" label="排名" width="80">
                  <template #default="{ row }">
                    <el-tag :type="getRankType(row.rank)" size="small">{{ row.rank }}</el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="description" label="说明" />
              </el-table>
            </el-card>

            <!-- 时间序列图表 -->
            <el-card class="time-series">
              <template #header>
                <div class="chart-header">
                  <h4>时间序列分析</h4>
                  <el-select v-model="selectedTimeSeries" size="small">
                    <el-option label="净值曲线" value="nav" />
                    <el-option label="超额收益" value="excess" />
                    <el-option label="回撤" value="drawdown" />
                    <el-option label="换手率" value="turnover" />
                  </el-select>
                </div>
              </template>
              <div ref="timeSeriesChart" class="chart-container large"></div>
            </el-card>
          </div>
        </el-tab-pane>

        <!-- 风险分析 -->
        <el-tab-pane label="风险分析" name="risk">
          <div class="risk-analysis">
            <el-row :gutter="16">
              <el-col :span="12">
                <el-card>
                  <template #header>
                    <h4>风险指标</h4>
                  </template>
                  <div class="risk-metrics">
                    <div v-for="risk in riskMetrics" :key="risk.name" class="risk-item">
                      <div class="risk-info">
                        <span class="risk-name">{{ risk.name }}</span>
                        <span class="risk-value" :style="{ color: risk.color }">{{ risk.value }}</span>
                      </div>
                      <el-progress 
                        :percentage="risk.percentage" 
                        :color="risk.color"
                        :stroke-width="8"
                        :show-text="false"
                      />
                    </div>
                  </div>
                </el-card>
              </el-col>
              <el-col :span="12">
                <el-card>
                  <template #header>
                    <h4>风险分布</h4>
                  </template>
                  <div ref="riskChart" class="chart-container"></div>
                </el-card>
              </el-col>
            </el-row>

            <!-- 风险预警 -->
            <el-card class="risk-alerts">
              <template #header>
                <h4>风险预警</h4>
              </template>
              <div class="alerts-list">
                <el-alert
                  v-for="alert in riskAlerts"
                  :key="alert.id"
                  :title="alert.title"
                  :description="alert.description"
                  :type="alert.type"
                  :closable="false"
                  class="alert-item"
                >
                  <template #default>
                    <div class="alert-content">
                      <div class="alert-main">
                        <h5>{{ alert.title }}</h5>
                        <p>{{ alert.description }}</p>
                      </div>
                      <div class="alert-action">
                        <el-button size="small" @click="handleAlertAction(alert)">
                          {{ alert.action }}
                        </el-button>
                      </div>
                    </div>
                  </template>
                </el-alert>
              </div>
            </el-card>
          </div>
        </el-tab-pane>

        <!-- 持仓分析 -->
        <el-tab-pane label="持仓分析" name="positions">
          <div class="position-analysis">
            <el-row :gutter="16">
              <el-col :span="16">
                <el-card>
                  <template #header>
                    <h4>当前持仓</h4>
                  </template>
                  <el-table :data="currentPositions" size="small" max-height="400">
                    <el-table-column prop="symbol" label="股票代码" width="100" />
                    <el-table-column prop="name" label="股票名称" />
                    <el-table-column prop="weight" label="权重" width="80">
                      <template #default="{ row }">
                        {{ (row.weight * 100).toFixed(2) }}%
                      </template>
                    </el-table-column>
                    <el-table-column prop="pnl" label="盈亏" width="100">
                      <template #default="{ row }">
                        <span :class="row.pnl >= 0 ? 'profit' : 'loss'">
                          {{ row.pnl >= 0 ? '+' : '' }}{{ (row.pnl * 100).toFixed(2) }}%
                        </span>
                      </template>
                    </el-table-column>
                    <el-table-column prop="industry" label="行业" />
                  </el-table>
                </el-card>
              </el-col>
              <el-col :span="8">
                <el-card>
                  <template #header>
                    <h4>行业分布</h4>
                  </template>
                  <div ref="industryChart" class="chart-container"></div>
                </el-card>
              </el-col>
            </el-row>

            <!-- 交易记录 -->
            <el-card class="trade-records">
              <template #header>
                <div class="table-header">
                  <h4>最近交易</h4>
                  <el-button size="small" @click="showAllTrades">查看全部</el-button>
                </div>
              </template>
              <el-table :data="recentTrades" size="small">
                <el-table-column prop="date" label="日期" width="100" />
                <el-table-column prop="symbol" label="股票" width="100" />
                <el-table-column prop="action" label="操作" width="80">
                  <template #default="{ row }">
                    <el-tag :type="row.action === 'buy' ? 'success' : 'danger'" size="small">
                      {{ row.action === 'buy' ? '买入' : '卖出' }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="quantity" label="数量" width="100" />
                <el-table-column prop="price" label="价格" width="100" />
                <el-table-column prop="reason" label="交易原因" />
              </el-table>
            </el-card>
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>

    <!-- 实时模式 -->
    <div v-if="previewMode === 'realtime'" class="preview-content">
      <div class="realtime-dashboard">
        <!-- 实时状态 -->
        <el-card class="realtime-status">
          <template #header>
            <div class="status-header">
              <h4>实时状态</h4>
              <div class="status-indicator">
                <el-icon class="status-icon" :class="{ 'status-active': isRealTimeActive }">
                  <VideoPlay />
                </el-icon>
                <span>{{ isRealTimeActive ? '实时更新中' : '已暂停' }}</span>
                <el-button 
                  size="small" 
                  :type="isRealTimeActive ? 'danger' : 'success'"
                  @click="toggleRealTime"
                >
                  {{ isRealTimeActive ? '暂停' : '开始' }}
                </el-button>
              </div>
            </div>
          </template>

          <!-- 实时指标 -->
          <div class="realtime-metrics">
            <div v-for="metric in realtimeMetrics" :key="metric.key" class="realtime-metric">
              <div class="metric-label">{{ metric.label }}</div>
              <div class="metric-value" :style="{ color: metric.color }">
                {{ metric.value }}{{ metric.suffix }}
              </div>
              <div class="metric-change">
                <el-icon :class="metric.change >= 0 ? 'change-up' : 'change-down'">
                  <component :is="metric.change >= 0 ? 'CaretTop' : 'CaretBottom'" />
                </el-icon>
                <span>{{ Math.abs(metric.change) }}%</span>
              </div>
            </div>
          </div>
        </el-card>

        <!-- 实时图表 -->
        <el-card class="realtime-chart">
          <template #header>
            <div class="chart-header">
              <h4>实时净值</h4>
              <div class="chart-controls">
                <el-select v-model="realtimeTimeframe" size="small">
                  <el-option label="1分钟" value="1m" />
                  <el-option label="5分钟" value="5m" />
                  <el-option label="15分钟" value="15m" />
                  <el-option label="1小时" value="1h" />
                </el-select>
              </div>
            </div>
          </template>
          <div ref="realtimeChart" class="chart-container large"></div>
        </el-card>

        <!-- 实时事件流 -->
        <el-card class="realtime-events">
          <template #header>
            <h4>实时事件</h4>
          </template>
          <div class="events-stream">
            <div v-for="event in realtimeEvents" :key="event.id" class="event-item">
              <div class="event-time">{{ formatTime(event.timestamp) }}</div>
              <div class="event-content">
                <el-icon :style="{ color: event.color }">
                  <component :is="event.icon" />
                </el-icon>
                <span>{{ event.message }}</span>
              </div>
              <div class="event-value" v-if="event.value">
                {{ event.value }}
              </div>
            </div>
          </div>
        </el-card>
      </div>
    </div>

    <!-- 操作面板 -->
    <div class="action-panel">
      <el-button-group>
        <el-button @click="exportPreview">
          <el-icon><Download /></el-icon>
          导出
        </el-button>
        <el-button @click="sharePreview">
          <el-icon><Share /></el-icon>
          分享
        </el-button>
        <el-button @click="savePreview">
          <el-icon><DocumentCopy /></el-icon>
          保存
        </el-button>
      </el-button-group>
      
      <el-button type="primary" @click="viewFullResults">
        查看完整结果
        <el-icon><ArrowRight /></el-icon>
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  TrendCharts, Refresh, VideoPlay, CaretTop, CaretBottom,
  Download, Share, DocumentCopy, ArrowRight
} from '@element-plus/icons-vue'
import * as echarts from 'echarts'

interface Metric {
  key: string
  title: string
  value: number
  suffix: string
  precision?: number
  color: string
  icon: string
  trend: 'up' | 'down'
  change: number
}

interface Insight {
  id: string
  title: string
  description: string
  value: string
  icon: string
  color: string
  type: 'success' | 'warning' | 'danger' | 'info'
}

interface RiskAlert {
  id: string
  title: string
  description: string
  type: 'success' | 'warning' | 'error' | 'info'
  action: string
}

const router = useRouter()

// 响应式数据
const previewMode = ref('summary')
const activeDetailTab = ref('performance')
const selectedTimeSeries = ref('nav')
const realtimeTimeframe = ref('5m')
const isLoading = ref(false)
const isRealTimeActive = ref(false)

// 图表引用
const navChart = ref<HTMLElement>()
const returnChart = ref<HTMLElement>()
const timeSeriesChart = ref<HTMLElement>()
const riskChart = ref<HTMLElement>()
const industryChart = ref<HTMLElement>()
const realtimeChart = ref<HTMLElement>()

// 图表实例
let navChartInstance: echarts.ECharts
let returnChartInstance: echarts.ECharts
let timeSeriesChartInstance: echarts.ECharts
let riskChartInstance: echarts.ECharts
let industryChartInstance: echarts.ECharts
let realtimeChartInstance: echarts.ECharts

// 定时器
let realtimeTimer: NodeJS.Timeout | null = null

// 数据
const summaryMetrics = ref<Metric[]>([
  {
    key: 'total_return',
    title: '总收益率',
    value: 28.5,
    suffix: '%',
    precision: 1,
    color: '#67c23a',
    icon: 'TrendCharts',
    trend: 'up',
    change: 2.3
  },
  {
    key: 'sharpe_ratio',
    title: '夏普比率',
    value: 1.45,
    suffix: '',
    precision: 2,
    color: '#409eff',
    icon: 'DataAnalysis',
    trend: 'up',
    change: 0.8
  },
  {
    key: 'max_drawdown',
    title: '最大回撤',
    value: 8.2,
    suffix: '%',
    precision: 1,
    color: '#f56c6c',
    icon: 'Warning',
    trend: 'down',
    change: -1.2
  },
  {
    key: 'win_rate',
    title: '胜率',
    value: 65.3,
    suffix: '%',
    precision: 1,
    color: '#e6a23c',
    icon: 'Trophy',
    trend: 'up',
    change: 3.1
  }
])

const keyInsights = ref<Insight[]>([
  {
    id: '1',
    title: '策略表现优秀',
    description: '夏普比率超过1.4，风险调整后收益表现良好',
    value: '优秀',
    icon: 'SuccessFilled',
    color: '#67c23a',
    type: 'success'
  },
  {
    id: '2',
    title: '回撤控制良好',
    description: '最大回撤控制在10%以内，符合风险管理要求',
    value: '良好',
    icon: 'InfoFilled',
    color: '#409eff',
    type: 'info'
  },
  {
    id: '3',
    title: '建议增加持仓分散',
    description: '当前持仓集中度较高，建议增加持仓分散化',
    value: '待优化',
    icon: 'WarningFilled',
    color: '#e6a23c',
    type: 'warning'
  }
])

const detailedMetrics = ref([
  { category: '收益指标', metric: '年化收益率', value: '18.5', suffix: '%', rank: '前25%', color: '#67c23a', description: '超越基准8.3%' },
  { category: '收益指标', metric: '累计收益率', value: '68.9', suffix: '%', rank: '前20%', color: '#67c23a', description: '3年累计收益' },
  { category: '风险指标', metric: '年化波动率', value: '16.2', suffix: '%', rank: '前40%', color: '#409eff', description: '风险适中' },
  { category: '风险指标', metric: 'VaR(95%)', value: '3.8', suffix: '%', rank: '前30%', color: '#f56c6c', description: '日度风险价值' },
  { category: '效率指标', metric: '信息比率', value: '0.96', suffix: '', rank: '前35%', color: '#e6a23c', description: '超额收益稳定性' }
])

const riskMetrics = ref([
  { name: '市场风险', value: '中等', percentage: 60, color: '#e6a23c' },
  { name: '流动性风险', value: '较低', percentage: 30, color: '#67c23a' },
  { name: '集中度风险', value: '较高', percentage: 75, color: '#f56c6c' },
  { name: '行业风险', value: '中等', percentage: 55, color: '#409eff' }
])

const riskAlerts = ref<RiskAlert[]>([
  {
    id: '1',
    title: '持仓集中度预警',
    description: '前十大持仓占比超过60%，存在集中度风险',
    type: 'warning',
    action: '查看详情'
  },
  {
    id: '2',
    title: '行业暴露提醒',
    description: '制造业持仓占比较高，注意行业轮动风险',
    type: 'info',
    action: '调整持仓'
  }
])

const currentPositions = ref([
  { symbol: '000001', name: '平安银行', weight: 0.08, pnl: 0.125, industry: '银行' },
  { symbol: '000002', name: '万科A', weight: 0.06, pnl: -0.032, industry: '房地产' },
  { symbol: '000858', name: '五粮液', weight: 0.09, pnl: 0.088, industry: '食品饮料' },
  { symbol: '000876', name: '新希望', weight: 0.05, pnl: 0.045, industry: '农业' },
  { symbol: '002415', name: '海康威视', weight: 0.07, pnl: 0.067, industry: '电子' }
])

const recentTrades = ref([
  { date: '2024-01-15', symbol: '000001', action: 'buy', quantity: 1000, price: '12.50', reason: '因子信号触发' },
  { date: '2024-01-15', symbol: '000002', action: 'sell', quantity: 500, price: '18.20', reason: '止盈离场' },
  { date: '2024-01-14', symbol: '000858', action: 'buy', quantity: 200, price: '180.50', reason: '价值回归' }
])

const realtimeMetrics = ref([
  { key: 'current_nav', label: '当前净值', value: '1.285', suffix: '', color: '#67c23a', change: 0.85 },
  { key: 'daily_pnl', label: '当日盈亏', value: '+2.3', suffix: '%', color: '#67c23a', change: 1.2 },
  { key: 'position_count', label: '持仓数量', value: '28', suffix: '只', color: '#409eff', change: 0 },
  { key: 'turnover', label: '换手率', value: '12.5', suffix: '%', color: '#e6a23c', change: -0.5 }
])

const realtimeEvents = ref([
  {
    id: '1',
    timestamp: Date.now() - 300000,
    message: '触发买入信号',
    value: '000001 平安银行',
    icon: 'Plus',
    color: '#67c23a'
  },
  {
    id: '2',
    timestamp: Date.now() - 600000,
    message: '止盈离场',
    value: '000002 万科A',
    icon: 'Minus',
    color: '#f56c6c'
  },
  {
    id: '3',
    timestamp: Date.now() - 900000,
    message: '风险预警',
    value: '行业集中度过高',
    icon: 'WarningFilled',
    color: '#e6a23c'
  }
])

// 方法
const refreshPreview = async () => {
  isLoading.value = true
  
  // 模拟数据更新
  await new Promise(resolve => setTimeout(resolve, 1000))
  
  // 更新指标数据
  summaryMetrics.value.forEach(metric => {
    metric.value += (Math.random() - 0.5) * 2
    metric.change = (Math.random() - 0.5) * 5
  })
  
  // 重新渲染图表
  updateCharts()
  
  isLoading.value = false
  ElMessage.success('预览已刷新')
}

const toggleRealTime = () => {
  isRealTimeActive.value = !isRealTimeActive.value
  
  if (isRealTimeActive.value) {
    startRealTimeUpdates()
    ElMessage.success('开始实时更新')
  } else {
    stopRealTimeUpdates()
    ElMessage.info('暂停实时更新')
  }
}

const startRealTimeUpdates = () => {
  realtimeTimer = setInterval(() => {
    // 更新实时指标
    realtimeMetrics.value.forEach(metric => {
      const change = (Math.random() - 0.5) * 0.1
      metric.change = change
      
      if (metric.key === 'current_nav') {
        metric.value = (parseFloat(metric.value) + change * 0.01).toFixed(3)
      }
    })
    
    // 添加新事件
    if (Math.random() > 0.7) {
      const events = [
        { message: '价格更新', value: '净值: 1.285', icon: 'TrendCharts', color: '#409eff' },
        { message: '交易信号', value: '买入信号触发', icon: 'Plus', color: '#67c23a' },
        { message: '风险监控', value: '风险指标正常', icon: 'Shield', color: '#67c23a' }
      ]
      
      const randomEvent = events[Math.floor(Math.random() * events.length)]
      realtimeEvents.value.unshift({
        id: Date.now().toString(),
        timestamp: Date.now(),
        ...randomEvent
      })
      
      // 限制事件数量
      if (realtimeEvents.value.length > 10) {
        realtimeEvents.value = realtimeEvents.value.slice(0, 10)
      }
    }
    
    // 更新实时图表
    updateRealtimeChart()
  }, 3000)
}

const stopRealTimeUpdates = () => {
  if (realtimeTimer) {
    clearInterval(realtimeTimer)
    realtimeTimer = null
  }
}

const getRankType = (rank: string) => {
  if (rank.includes('前20%')) return 'success'
  if (rank.includes('前40%')) return 'warning'
  return 'info'
}

const handleAlertAction = (alert: RiskAlert) => {
  ElMessage.info(`处理风险预警: ${alert.title}`)
}

const showAllTrades = () => {
  ElMessage.info('跳转到完整交易记录页面')
}

const exportPreview = () => {
  ElMessage.success('预览结果已导出')
}

const sharePreview = () => {
  ElMessage.success('预览链接已复制到剪贴板')
}

const savePreview = () => {
  ElMessage.success('预览已保存到我的收藏')
}

const viewFullResults = () => {
  router.push('/results')
}

const formatTime = (timestamp: number) => {
  return new Date(timestamp).toLocaleTimeString()
}

// 图表方法
const initCharts = async () => {
  await nextTick()
  
  // 初始化各个图表
  if (navChart.value) {
    navChartInstance = echarts.init(navChart.value)
    updateNavChart()
  }
  
  if (returnChart.value) {
    returnChartInstance = echarts.init(returnChart.value)
    updateReturnChart()
  }
  
  if (timeSeriesChart.value) {
    timeSeriesChartInstance = echarts.init(timeSeriesChart.value)
    updateTimeSeriesChart()
  }
  
  if (riskChart.value) {
    riskChartInstance = echarts.init(riskChart.value)
    updateRiskChart()
  }
  
  if (industryChart.value) {
    industryChartInstance = echarts.init(industryChart.value)
    updateIndustryChart()
  }
  
  if (realtimeChart.value) {
    realtimeChartInstance = echarts.init(realtimeChart.value)
    updateRealtimeChart()
  }
}

const updateCharts = () => {
  updateNavChart()
  updateReturnChart()
  updateTimeSeriesChart()
  updateRiskChart()
  updateIndustryChart()
  updateRealtimeChart()
}

const updateNavChart = () => {
  if (!navChartInstance) return
  
  const dates = Array.from({ length: 30 }, (_, i) => {
    const date = new Date()
    date.setDate(date.getDate() - 29 + i)
    return date.toISOString().split('T')[0]
  })
  
  const navData = dates.map((_, i) => 1 + (i / 30) * 0.285 + Math.random() * 0.02)
  
  navChartInstance.setOption({
    xAxis: { type: 'category', data: dates },
    yAxis: { type: 'value' },
    series: [{
      type: 'line',
      data: navData,
      smooth: true,
      itemStyle: { color: '#67c23a' }
    }],
    grid: { top: 10, right: 10, bottom: 30, left: 40 }
  })
}

const updateReturnChart = () => {
  if (!returnChartInstance) return
  
  const data = Array.from({ length: 50 }, () => (Math.random() - 0.5) * 10)
  
  returnChartInstance.setOption({
    xAxis: { type: 'value' },
    yAxis: { type: 'value' },
    series: [{
      type: 'scatter',
      data: data.map((val, i) => [i, val]),
      itemStyle: { color: '#409eff' }
    }],
    grid: { top: 10, right: 10, bottom: 30, left: 40 }
  })
}

const updateTimeSeriesChart = () => {
  if (!timeSeriesChartInstance) return
  
  const dates = Array.from({ length: 100 }, (_, i) => {
    const date = new Date()
    date.setDate(date.getDate() - 99 + i)
    return date.toISOString().split('T')[0]
  })
  
  const data = dates.map((_, i) => 1 + (i / 100) * 0.285 + Math.sin(i / 10) * 0.05)
  
  timeSeriesChartInstance.setOption({
    xAxis: { type: 'category', data: dates },
    yAxis: { type: 'value' },
    series: [{
      type: 'line',
      data: data,
      smooth: true,
      itemStyle: { color: '#409eff' }
    }],
    grid: { top: 20, right: 30, bottom: 40, left: 60 },
    dataZoom: [{ type: 'inside' }, { type: 'slider' }]
  })
}

const updateRiskChart = () => {
  if (!riskChartInstance) return
  
  const data = riskMetrics.value.map(risk => ({
    name: risk.name,
    value: risk.percentage
  }))
  
  riskChartInstance.setOption({
    series: [{
      type: 'pie',
      data: data,
      radius: ['40%', '70%']
    }]
  })
}

const updateIndustryChart = () => {
  if (!industryChartInstance) return
  
  const data = [
    { name: '银行', value: 25 },
    { name: '房地产', value: 15 },
    { name: '食品饮料', value: 20 },
    { name: '电子', value: 18 },
    { name: '其他', value: 22 }
  ]
  
  industryChartInstance.setOption({
    series: [{
      type: 'pie',
      data: data,
      radius: '70%'
    }]
  })
}

const updateRealtimeChart = () => {
  if (!realtimeChartInstance) return
  
  const now = Date.now()
  const data = Array.from({ length: 60 }, (_, i) => {
    const time = new Date(now - (59 - i) * 60000)
    return [time, 1.285 + Math.sin(i / 10) * 0.01 + Math.random() * 0.005]
  })
  
  realtimeChartInstance.setOption({
    xAxis: { type: 'time' },
    yAxis: { type: 'value' },
    series: [{
      type: 'line',
      data: data,
      smooth: true,
      itemStyle: { color: '#67c23a' }
    }],
    grid: { top: 20, right: 30, bottom: 40, left: 60 }
  })
}

// 生命周期
onMounted(() => {
  initCharts()
})

onUnmounted(() => {
  stopRealTimeUpdates()
  
  // 销毁图表实例
  navChartInstance?.dispose()
  returnChartInstance?.dispose()
  timeSeriesChartInstance?.dispose()
  riskChartInstance?.dispose()
  industryChartInstance?.dispose()
  realtimeChartInstance?.dispose()
})
</script>

<style scoped lang="scss">
.instant-result-preview {
  max-width: 1400px;
  margin: 0 auto;
  padding: 24px;

  .preview-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 24px;

    h3 {
      display: flex;
      align-items: center;
      gap: 8px;
      margin: 0;
      font-size: 24px;
      color: var(--el-text-color-primary);
    }

    .preview-controls {
      display: flex;
      gap: 12px;
      align-items: center;
    }
  }

  .preview-content {
    margin-bottom: 24px;
  }

  // 概览模式样式
  .metrics-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 16px;
    margin-bottom: 24px;

    .metric-card {
      .metric-trend {
        display: flex;
        align-items: center;
        gap: 4px;
        margin-top: 8px;
        font-size: 14px;

        .trend-up {
          color: var(--el-color-success);
        }

        .trend-down {
          color: var(--el-color-danger);
        }
      }
    }
  }

  .quick-charts {
    margin-bottom: 24px;
  }

  .insights-card {
    .insights-list {
      .insight-item {
        display: flex;
        align-items: center;
        gap: 16px;
        padding: 12px;
        margin-bottom: 12px;
        border: 1px solid var(--el-border-color);
        border-radius: 8px;

        .insight-icon {
          flex-shrink: 0;
        }

        .insight-content {
          flex: 1;

          h5 {
            margin: 0 0 4px 0;
            font-size: 14px;
          }

          p {
            margin: 0;
            color: var(--el-text-color-regular);
            font-size: 13px;
          }
        }

        .insight-value {
          flex-shrink: 0;
        }
      }
    }
  }

  // 详细模式样式
  .detail-tabs {
    .performance-analysis {
      .metrics-table {
        margin-bottom: 24px;
      }

      .time-series {
        .chart-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
        }
      }
    }

    .risk-analysis {
      .risk-metrics {
        .risk-item {
          margin-bottom: 16px;

          .risk-info {
            display: flex;
            justify-content: space-between;
            margin-bottom: 8px;

            .risk-name {
              font-weight: 500;
            }

            .risk-value {
              font-weight: bold;
            }
          }
        }
      }

      .risk-alerts {
        margin-top: 24px;

        .alerts-list {
          .alert-item {
            margin-bottom: 12px;

            .alert-content {
              display: flex;
              align-items: center;
              gap: 16px;

              .alert-main {
                flex: 1;

                h5 {
                  margin: 0 0 4px 0;
                }

                p {
                  margin: 0;
                }
              }

              .alert-action {
                flex-shrink: 0;
              }
            }
          }
        }
      }
    }

    .position-analysis {
      .profit {
        color: var(--el-color-success);
      }

      .loss {
        color: var(--el-color-danger);
      }

      .trade-records {
        margin-top: 24px;

        .table-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
        }
      }
    }
  }

  // 实时模式样式
  .realtime-dashboard {
    .realtime-status {
      margin-bottom: 24px;

      .status-header {
        display: flex;
        justify-content: space-between;
        align-items: center;

        .status-indicator {
          display: flex;
          align-items: center;
          gap: 8px;

          .status-icon {
            &.status-active {
              color: var(--el-color-success);
              animation: pulse 2s infinite;
            }
          }
        }
      }

      .realtime-metrics {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 16px;

        .realtime-metric {
          text-align: center;
          padding: 16px;
          background-color: var(--el-color-info-light-9);
          border-radius: 8px;

          .metric-label {
            font-size: 14px;
            color: var(--el-text-color-regular);
            margin-bottom: 8px;
          }

          .metric-value {
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 8px;
          }

          .metric-change {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 4px;
            font-size: 12px;

            .change-up {
              color: var(--el-color-success);
            }

            .change-down {
              color: var(--el-color-danger);
            }
          }
        }
      }
    }

    .realtime-chart {
      margin-bottom: 24px;

      .chart-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
      }
    }

    .realtime-events {
      .events-stream {
        max-height: 300px;
        overflow-y: auto;

        .event-item {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 8px 0;
          border-bottom: 1px solid var(--el-border-color-lighter);

          .event-time {
            font-size: 12px;
            color: var(--el-text-color-placeholder);
            min-width: 80px;
          }

          .event-content {
            display: flex;
            align-items: center;
            gap: 8px;
            flex: 1;
          }

          .event-value {
            font-size: 12px;
            color: var(--el-text-color-regular);
          }
        }
      }
    }
  }

  .chart-container {
    height: 200px;

    &.large {
      height: 300px;
    }
  }

  .action-panel {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px 0;
    border-top: 1px solid var(--el-border-color);
  }
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

@media (max-width: 768px) {
  .instant-result-preview {
    padding: 16px;

    .preview-header {
      flex-direction: column;
      gap: 16px;
      align-items: flex-start;

      .preview-controls {
        width: 100%;
        justify-content: space-between;
      }
    }

    .metrics-grid {
      grid-template-columns: 1fr;
    }

    .realtime-metrics {
      grid-template-columns: repeat(2, 1fr);
    }

    .action-panel {
      flex-direction: column;
      gap: 16px;
    }
  }
}
</style>