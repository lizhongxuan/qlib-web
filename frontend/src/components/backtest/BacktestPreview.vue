<template>
  <div class="backtest-preview">
    <el-card class="preview-card">
      <template #header>
        <div class="preview-header">
          <div class="header-title">
            <el-icon><View /></el-icon>
            <span>回测结果预览</span>
          </div>
          <div class="header-actions">
            <el-button-group>
              <el-button size="small" @click="refreshPreview">
                <el-icon><Refresh /></el-icon>
                刷新
              </el-button>
              <el-button size="small" @click="toggleFullscreen">
                <el-icon><FullScreen /></el-icon>
                全屏
              </el-button>
            </el-button-group>
            
            <el-dropdown @command="handleExport">
              <el-button size="small">
                <el-icon><Download /></el-icon>
                导出
                <el-icon class="el-icon--right"><ArrowDown /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="pdf">导出PDF报告</el-dropdown-item>
                  <el-dropdown-item command="excel">导出Excel数据</el-dropdown-item>
                  <el-dropdown-item command="image">导出图片</el-dropdown-item>
                  <el-dropdown-item command="json">导出JSON数据</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>
      </template>

      <!-- 快速概览 -->
      <div class="quick-overview">
        <h4>快速概览</h4>
        <el-row :gutter="16">
          <el-col :span="6">
            <div class="overview-card profit">
              <div class="overview-icon">
                <el-icon><TrendCharts /></el-icon>
              </div>
              <div class="overview-content">
                <div class="overview-title">总收益率</div>
                <div class="overview-value" :class="getReturnClass(overview.totalReturn)">
                  {{ formatPercentage(overview.totalReturn) }}
                </div>
                <div class="overview-subtitle">
                  超越基准 {{ formatPercentage(overview.excessReturn) }}
                </div>
              </div>
            </div>
          </el-col>
          
          <el-col :span="6">
            <div class="overview-card risk">
              <div class="overview-icon">
                <el-icon><Warning /></el-icon>
              </div>
              <div class="overview-content">
                <div class="overview-title">最大回撤</div>
                <div class="overview-value negative">
                  {{ formatPercentage(overview.maxDrawdown) }}
                </div>
                <div class="overview-subtitle">
                  回撤持续 {{ overview.drawdownDuration }} 天
                </div>
              </div>
            </div>
          </el-col>
          
          <el-col :span="6">
            <div class="overview-card performance">
              <div class="overview-icon">
                <el-icon><Odometer /></el-icon>
              </div>
              <div class="overview-content">
                <div class="overview-title">夏普比率</div>
                <div class="overview-value">
                  {{ overview.sharpeRatio.toFixed(3) }}
                </div>
                <div class="overview-subtitle">
                  风险调整后收益优秀
                </div>
              </div>
            </div>
          </el-col>
          
          <el-col :span="6">
            <div class="overview-card stability">
              <div class="overview-icon">
                <el-icon><DataAnalysis /></el-icon>
              </div>
              <div class="overview-content">
                <div class="overview-title">胜率</div>
                <div class="overview-value">
                  {{ overview.winRate.toFixed(1) }}%
                </div>
                <div class="overview-subtitle">
                  {{ overview.totalTrades }} 次交易
                </div>
              </div>
            </div>
          </el-col>
        </el-row>
      </div>

      <!-- 关键图表 -->
      <div class="key-charts">
        <el-tabs v-model="activeTab" type="card">
          <el-tab-pane label="净值曲线" name="netvalue">
            <div class="chart-section">
              <div class="chart-header">
                <h5>净值走势对比</h5>
                <div class="chart-controls">
                  <el-radio-group v-model="chartTimeRange" size="small">
                    <el-radio-button label="all">全部</el-radio-button>
                    <el-radio-button label="1y">近1年</el-radio-button>
                    <el-radio-button label="6m">近半年</el-radio-button>
                    <el-radio-button label="3m">近3月</el-radio-button>
                  </el-radio-group>
                </div>
              </div>
              <div ref="netValueChartRef" class="chart-container large"></div>
              
              <div class="chart-insights">
                <el-alert
                  :title="getChartInsightTitle('netvalue')"
                  type="info"
                  :closable="false"
                  show-icon
                >
                  <template #default>
                    {{ getChartInsightContent('netvalue') }}
                  </template>
                </el-alert>
              </div>
            </div>
          </el-tab-pane>

          <el-tab-pane label="回撤分析" name="drawdown">
            <div class="chart-section">
              <div class="chart-header">
                <h5>回撤分析</h5>
                <div class="chart-legend">
                  <span class="legend-item">
                    <span class="legend-color" style="background: #f56c6c"></span>
                    策略回撤
                  </span>
                  <span class="legend-item">
                    <span class="legend-color" style="background: #909399"></span>
                    基准回撤
                  </span>
                </div>
              </div>
              <div ref="drawdownChartRef" class="chart-container large"></div>
              
              <div class="drawdown-stats">
                <el-row :gutter="16">
                  <el-col :span="6">
                    <el-statistic title="最大回撤" :value="overview.maxDrawdown" :precision="2" suffix="%" />
                  </el-col>
                  <el-col :span="6">
                    <el-statistic title="平均回撤" :value="drawdownStats.avgDrawdown" :precision="2" suffix="%" />
                  </el-col>
                  <el-col :span="6">
                    <el-statistic title="回撤次数" :value="drawdownStats.drawdownCount" />
                  </el-col>
                  <el-col :span="6">
                    <el-statistic title="恢复时间" :value="drawdownStats.avgRecoveryDays" suffix="天" />
                  </el-col>
                </el-row>
              </div>
            </div>
          </el-tab-pane>

          <el-tab-pane label="收益分析" name="returns">
            <div class="chart-section">
              <div class="chart-header">
                <h5>收益分布分析</h5>
              </div>
              <el-row :gutter="16">
                <el-col :span="12">
                  <div ref="returnDistChartRef" class="chart-container"></div>
                </el-col>
                <el-col :span="12">
                  <div ref="monthlyReturnChartRef" class="chart-container"></div>
                </el-col>
              </el-row>
              
              <div class="returns-analysis">
                <h6>收益特征分析</h6>
                <el-descriptions :column="3" border>
                  <el-descriptions-item label="年化收益率">
                    {{ formatPercentage(returnStats.annualizedReturn) }}
                  </el-descriptions-item>
                  <el-descriptions-item label="年化波动率">
                    {{ formatPercentage(returnStats.annualizedVolatility) }}
                  </el-descriptions-item>
                  <el-descriptions-item label="收益风险比">
                    {{ returnStats.returnRiskRatio.toFixed(2) }}
                  </el-descriptions-item>
                  <el-descriptions-item label="正收益天数">
                    {{ returnStats.positiveDays }} / {{ returnStats.totalDays }}
                  </el-descriptions-item>
                  <el-descriptions-item label="最大单日收益">
                    {{ formatPercentage(returnStats.maxDailyReturn) }}
                  </el-descriptions-item>
                  <el-descriptions-item label="最大单日亏损">
                    {{ formatPercentage(returnStats.maxDailyLoss) }}
                  </el-descriptions-item>
                </el-descriptions>
              </div>
            </div>
          </el-tab-pane>

          <el-tab-pane label="持仓分析" name="positions">
            <div class="chart-section">
              <div class="chart-header">
                <h5>持仓分析</h5>
                <div class="position-date">
                  <el-date-picker
                    v-model="selectedPositionDate"
                    type="date"
                    placeholder="选择日期"
                    size="small"
                    style="width: 140px"
                    @change="updatePositionAnalysis"
                  />
                </div>
              </div>
              
              <el-row :gutter="16">
                <el-col :span="8">
                  <div ref="sectorPieChartRef" class="chart-container"></div>
                  <div class="chart-title">行业分布</div>
                </el-col>
                <el-col :span="8">
                  <div ref="topHoldingsChartRef" class="chart-container"></div>
                  <div class="chart-title">前十大持仓</div>
                </el-col>
                <el-col :span="8">
                  <div ref="turnoverChartRef" class="chart-container"></div>
                  <div class="chart-title">换手率趋势</div>
                </el-col>
              </el-row>
              
              <div class="position-table">
                <h6>详细持仓 ({{ selectedPositionDate || '最新' }})</h6>
                <el-table 
                  :data="currentPositions" 
                  size="small" 
                  max-height="300"
                  :default-sort="{ prop: 'weight', order: 'descending' }"
                >
                  <el-table-column prop="symbol" label="代码" width="80" />
                  <el-table-column prop="name" label="名称" width="120" />
                  <el-table-column prop="sector" label="行业" width="100" />
                  <el-table-column prop="weight" label="权重" width="80" sortable>
                    <template #default="{ row }">
                      {{ (row.weight * 100).toFixed(2) }}%
                    </template>
                  </el-table-column>
                  <el-table-column prop="return" label="持仓收益" width="90" sortable>
                    <template #default="{ row }">
                      <span :class="getReturnClass(row.return)">
                        {{ formatPercentage(row.return) }}
                      </span>
                    </template>
                  </el-table-column>
                  <el-table-column prop="holdingDays" label="持有天数" width="80" />
                  <el-table-column prop="value" label="市值(万)" width="90">
                    <template #default="{ row }">
                      {{ (row.value / 10000).toFixed(1) }}
                    </template>
                  </el-table-column>
                </el-table>
              </div>
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>

      <!-- AI 洞察分析 -->
      <div class="ai-insights">
        <div class="insights-header">
          <h4>
            <el-icon><ChatDotRound /></el-icon>
            AI 智能分析
          </h4>
          <el-button size="small" @click="generateInsights" :loading="generatingInsights">
            <el-icon><MagicStick /></el-icon>
            重新分析
          </el-button>
        </div>
        
        <el-row :gutter="16">
          <el-col :span="8">
            <el-card class="insight-card strengths" shadow="hover">
              <template #header>
                <div class="insight-header">
                  <el-icon><CircleCheck /></el-icon>
                  <span>策略优势</span>
                </div>
              </template>
              <ul class="insight-list">
                <li v-for="strength in insights.strengths" :key="strength">
                  {{ strength }}
                </li>
              </ul>
            </el-card>
          </el-col>
          
          <el-col :span="8">
            <el-card class="insight-card weaknesses" shadow="hover">
              <template #header>
                <div class="insight-header">
                  <el-icon><Warning /></el-icon>
                  <span>风险警示</span>
                </div>
              </template>
              <ul class="insight-list">
                <li v-for="weakness in insights.weaknesses" :key="weakness">
                  {{ weakness }}
                </li>
              </ul>
            </el-card>
          </el-col>
          
          <el-col :span="8">
            <el-card class="insight-card suggestions" shadow="hover">
              <template #header>
                <div class="insight-header">
                  <el-icon><Opportunity /></el-icon>
                  <span>优化建议</span>
                </div>
              </template>
              <ul class="insight-list">
                <li v-for="suggestion in insights.suggestions" :key="suggestion">
                  {{ suggestion }}
                </li>
              </ul>
            </el-card>
          </el-col>
        </el-row>
      </div>

      <!-- 快速操作 -->
      <div class="quick-actions">
        <h4>快速操作</h4>
        <div class="action-buttons">
          <el-button type="primary" @click="deployStrategy">
            <el-icon><Upload /></el-icon>
            部署策略
          </el-button>
          <el-button @click="optimizeStrategy">
            <el-icon><Setting /></el-icon>
            参数优化
          </el-button>
          <el-button @click="compareWithOthers">
            <el-icon><DataAnalysis /></el-icon>
            结果对比
          </el-button>
          <el-button @click="scheduleRerun">
            <el-icon><Timer /></el-icon>
            定时重跑
          </el-button>
          <el-button @click="shareResults">
            <el-icon><Share /></el-icon>
            分享结果
          </el-button>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  View, Refresh, FullScreen, Download, ArrowDown, TrendCharts,
  Warning, Odometer, DataAnalysis, ChatDotRound, MagicStick,
  CircleCheck, Opportunity, Upload, Setting, Timer, Share
} from '@element-plus/icons-vue'

// Props
interface Props {
  backtestId?: string
  results?: any
  autoRefresh?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  backtestId: '',
  results: null,
  autoRefresh: false
})

// Emits
const emit = defineEmits<{
  'deploy-strategy': [results: any]
  'optimize-parameters': [results: any]
  'compare-results': [results: any]
}>()

const router = useRouter()

// 响应式数据
const activeTab = ref('netvalue')
const chartTimeRange = ref('all')
const selectedPositionDate = ref('')
const generatingInsights = ref(false)

// 图表引用
const netValueChartRef = ref()
const drawdownChartRef = ref()
const returnDistChartRef = ref()
const monthlyReturnChartRef = ref()
const sectorPieChartRef = ref()
const topHoldingsChartRef = ref()
const turnoverChartRef = ref()

// 概览数据
const overview = reactive({
  totalReturn: 28.5,
  excessReturn: 16.2,
  maxDrawdown: -12.3,
  drawdownDuration: 45,
  sharpeRatio: 1.45,
  winRate: 62.8,
  totalTrades: 156
})

// 回撤统计
const drawdownStats = reactive({
  avgDrawdown: -5.2,
  drawdownCount: 8,
  avgRecoveryDays: 12
})

// 收益统计
const returnStats = reactive({
  annualizedReturn: 24.8,
  annualizedVolatility: 18.5,
  returnRiskRatio: 1.34,
  positiveDays: 145,
  totalDays: 252,
  maxDailyReturn: 8.5,
  maxDailyLoss: -6.2
})

// 当前持仓
const currentPositions = ref([
  {
    symbol: '000001',
    name: '平安银行',
    sector: '金融',
    weight: 0.058,
    return: 12.5,
    holdingDays: 30,
    value: 580000
  },
  {
    symbol: '000002',
    name: '万科A',
    sector: '房地产',
    weight: 0.045,
    return: -8.2,
    holdingDays: 25,
    value: 450000
  },
  {
    symbol: '600036',
    name: '招商银行',
    sector: '金融',
    weight: 0.062,
    return: 15.8,
    holdingDays: 35,
    value: 620000
  },
  {
    symbol: '000858',
    name: '五粮液',
    sector: '消费',
    weight: 0.041,
    return: 6.9,
    holdingDays: 20,
    value: 410000
  },
  {
    symbol: '300059',
    name: '东方财富',
    sector: '科技',
    weight: 0.038,
    return: 22.1,
    holdingDays: 40,
    value: 380000
  }
])

// AI洞察
const insights = reactive({
  strengths: [
    '策略夏普比率优秀，风险调整后收益表现良好',
    '超额收益稳定，相对基准有明显优势',
    '回撤控制较好，最大回撤在可接受范围内',
    '持仓分散度合理，行业配置均衡'
  ],
  weaknesses: [
    '在市场下跌期间表现相对较弱',
    '换手率偏高，交易成本可能影响收益',
    '对金融行业依赖度较高，存在集中度风险',
    '部分时期存在较长的业绩修复周期'
  ],
  suggestions: [
    '可考虑增加防御性因子，提升下跌市场适应性',
    '优化调仓频率，降低交易成本对收益的影响',
    '增强行业轮动能力，降低单一行业风险暴露',
    '引入市场情绪指标，提升择时能力'
  ]
})

// 方法
const refreshPreview = async () => {
  ElMessage.info('正在刷新预览数据...')
  
  // 模拟数据刷新
  await new Promise(resolve => setTimeout(resolve, 1000))
  
  // 更新数据（这里应该从API获取最新数据）
  updateCharts()
  
  ElMessage.success('预览数据已更新')
}

const toggleFullscreen = () => {
  ElMessage.info('全屏模式功能开发中')
}

const handleExport = async (command: string) => {
  ElMessage.loading('正在准备导出...')
  
  // 模拟导出过程
  await new Promise(resolve => setTimeout(resolve, 2000))
  
  switch (command) {
    case 'pdf':
      ElMessage.success('PDF报告导出成功')
      break
    case 'excel':
      ElMessage.success('Excel数据导出成功')
      break
    case 'image':
      ElMessage.success('图片导出成功')
      break
    case 'json':
      ElMessage.success('JSON数据导出成功')
      break
  }
}

const updatePositionAnalysis = () => {
  ElMessage.info(`正在加载 ${selectedPositionDate.value} 的持仓数据`)
  // 这里应该根据日期更新持仓数据
}

const generateInsights = async () => {
  generatingInsights.value = true
  
  try {
    // 模拟AI分析过程
    await new Promise(resolve => setTimeout(resolve, 3000))
    
    // 更新洞察（这里应该调用AI分析API）
    ElMessage.success('AI分析完成')
  } catch (error) {
    ElMessage.error('AI分析失败')
  } finally {
    generatingInsights.value = false
  }
}

const deployStrategy = () => {
  emit('deploy-strategy', {
    overview,
    insights,
    positions: currentPositions.value
  })
  router.push('/deployment')
}

const optimizeStrategy = () => {
  emit('optimize-parameters', {
    overview,
    suggestions: insights.suggestions
  })
  ElMessage.info('参数优化功能开发中')
}

const compareWithOthers = () => {
  emit('compare-results', {
    overview,
    returnStats
  })
  ElMessage.info('结果对比功能开发中')
}

const scheduleRerun = () => {
  ElMessage.info('定时重跑功能开发中')
}

const shareResults = () => {
  ElMessage.info('分享功能开发中')
}

const updateCharts = () => {
  // 这里应该调用图表库更新所有图表
  console.log('更新所有图表...')
}

// 辅助方法
const getReturnClass = (value: number) => {
  return value >= 0 ? 'positive' : 'negative'
}

const formatPercentage = (value: number) => {
  return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`
}

const getChartInsightTitle = (chartType: string) => {
  switch (chartType) {
    case 'netvalue':
      return '净值走势分析'
    default:
      return '图表分析'
  }
}

const getChartInsightContent = (chartType: string) => {
  switch (chartType) {
    case 'netvalue':
      return '策略净值曲线整体呈上升趋势，相比基准指数表现优异。在大部分时间区间内保持正超额收益，体现了良好的选股能力。'
    default:
      return '图表显示策略表现良好。'
  }
}

// 生命周期
onMounted(() => {
  nextTick(() => {
    updateCharts()
  })
  
  // 设置默认日期为今天
  selectedPositionDate.value = new Date().toISOString().split('T')[0]
})
</script>

<style scoped>
.backtest-preview {
  width: 100%;
}

.preview-card {
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.preview-header {
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

.header-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.quick-overview {
  margin-bottom: 32px;
}

.quick-overview h4 {
  margin: 0 0 16px 0;
  color: #303133;
  font-size: 16px;
  font-weight: 600;
}

.overview-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  background: linear-gradient(135deg, #f0f8ff 0%, #e8f4fd 100%);
  border-radius: 12px;
  border: 1px solid #d4e4fd;
  transition: all 0.3s ease;
  height: 100px;
}

.overview-card:hover {
  box-shadow: 0 4px 16px rgba(64, 158, 255, 0.2);
  transform: translateY(-2px);
}

.overview-card.profit {
  border-left: 4px solid #67c23a;
}

.overview-card.risk {
  border-left: 4px solid #f56c6c;
}

.overview-card.performance {
  border-left: 4px solid #409eff;
}

.overview-card.stability {
  border-left: 4px solid #e6a23c;
}

.overview-icon {
  font-size: 32px;
  color: #409eff;
}

.overview-content {
  flex: 1;
}

.overview-title {
  font-size: 14px;
  color: #606266;
  margin-bottom: 4px;
}

.overview-value {
  font-size: 24px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
}

.overview-value.positive {
  color: #67c23a;
}

.overview-value.negative {
  color: #f56c6c;
}

.overview-subtitle {
  font-size: 12px;
  color: #909399;
}

.key-charts {
  margin-bottom: 32px;
}

.chart-section {
  padding: 16px 0;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.chart-header h5 {
  margin: 0;
  color: #303133;
  font-size: 14px;
  font-weight: 600;
}

.chart-controls {
  display: flex;
  align-items: center;
  gap: 12px;
}

.chart-legend {
  display: flex;
  gap: 16px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #606266;
}

.legend-color {
  width: 12px;
  height: 12px;
  border-radius: 2px;
}

.position-date {
  display: flex;
  align-items: center;
  gap: 8px;
}

.chart-container {
  width: 100%;
  height: 250px;
  background: #f5f7fa;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #909399;
  font-size: 14px;
  margin-bottom: 16px;
}

.chart-container.large {
  height: 350px;
}

.chart-title {
  text-align: center;
  font-size: 14px;
  color: #606266;
  margin-top: 8px;
}

.chart-insights {
  margin-top: 16px;
}

.drawdown-stats {
  margin-top: 16px;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 6px;
}

.returns-analysis {
  margin-top: 24px;
}

.returns-analysis h6 {
  margin: 0 0 16px 0;
  color: #303133;
  font-size: 14px;
  font-weight: 600;
}

.position-table {
  margin-top: 24px;
}

.position-table h6 {
  margin: 0 0 16px 0;
  color: #303133;
  font-size: 14px;
  font-weight: 600;
}

.positive {
  color: #67c23a;
}

.negative {
  color: #f56c6c;
}

.ai-insights {
  margin-bottom: 32px;
}

.insights-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.insights-header h4 {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0;
  color: #303133;
  font-size: 16px;
  font-weight: 600;
}

.insight-card {
  height: 100%;
}

.insight-card.strengths .insight-header {
  color: #67c23a;
}

.insight-card.weaknesses .insight-header {
  color: #f56c6c;
}

.insight-card.suggestions .insight-header {
  color: #409eff;
}

.insight-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
}

.insight-list {
  margin: 0;
  padding: 0;
  list-style: none;
}

.insight-list li {
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
  font-size: 14px;
  color: #606266;
  line-height: 1.5;
}

.insight-list li:last-child {
  border-bottom: none;
}

.quick-actions h4 {
  margin: 0 0 16px 0;
  color: #303133;
  font-size: 16px;
  font-weight: 600;
}

.action-buttons {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .preview-header {
    flex-direction: column;
    gap: 12px;
  }
  
  .header-actions {
    width: 100%;
    justify-content: space-between;
  }
  
  .overview-card {
    flex-direction: column;
    text-align: center;
    height: auto;
    min-height: 120px;
  }
  
  .chart-header {
    flex-direction: column;
    gap: 12px;
    align-items: flex-start;
  }
  
  .action-buttons {
    flex-direction: column;
  }
  
  .insights-header {
    flex-direction: column;
    gap: 12px;
    align-items: flex-start;
  }
}
</style>