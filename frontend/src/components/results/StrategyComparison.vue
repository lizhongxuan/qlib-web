<template>
  <div class="strategy-comparison">
    <!-- 策略选择器 -->
    <el-card class="strategy-selector">
      <template #header>
        <div class="selector-header">
          <span>策略对比分析</span>
          <el-button @click="clearAll" size="small" :disabled="selectedStrategies.length === 0">
            <el-icon><Delete /></el-icon>
            清空
          </el-button>
        </div>
      </template>
      
      <div class="selector-content">
        <div class="selector-section">
          <label class="selector-label">选择对比策略 (最多5个):</label>
          <el-select
            v-model="selectedStrategyIds"
            multiple
            filterable
            placeholder="请选择要对比的策略"
            style="width: 100%"
            :max-collapse-tags="3"
            @change="handleStrategySelect"
          >
            <el-option
              v-for="strategy in availableStrategies"
              :key="strategy.id"
              :label="strategy.name"
              :value="strategy.id"
              :disabled="selectedStrategyIds.length >= 5 && !selectedStrategyIds.includes(strategy.id)"
            >
              <div class="strategy-option">
                <span class="strategy-name">{{ strategy.name }}</span>
                <span class="strategy-type">{{ strategy.type }}</span>
                <el-tag 
                  :type="getPerformanceTagType(strategy.score)" 
                  size="small"
                  class="strategy-score"
                >
                  {{ strategy.score.toFixed(1) }}
                </el-tag>
              </div>
            </el-option>
          </el-select>
        </div>

        <div v-if="selectedStrategies.length > 0" class="selected-strategies">
          <div class="selected-header">
            <span>已选择策略 ({{ selectedStrategies.length }}/5):</span>
          </div>
          <div class="strategy-tags">
            <el-tag
              v-for="strategy in selectedStrategies"
              :key="strategy.id"
              closable
              @close="removeStrategy(strategy.id)"
              size="large"
              class="strategy-tag"
            >
              <div class="tag-content">
                <span class="tag-name">{{ strategy.name }}</span>
                <span class="tag-score">{{ strategy.score.toFixed(1) }}分</span>
              </div>
            </el-tag>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 对比结果 -->
    <div v-if="selectedStrategies.length >= 2" class="comparison-results">
      <!-- 概览对比 -->
      <el-card class="overview-comparison">
        <template #header>
          <div class="comparison-header">
            <span>策略概览对比</span>
            <el-radio-group v-model="comparisonType" size="small">
              <el-radio-button label="table">表格</el-radio-button>
              <el-radio-button label="radar">雷达图</el-radio-button>
              <el-radio-button label="bar">柱状图</el-radio-button>
            </el-radio-group>
          </div>
        </template>

        <!-- 表格对比 -->
        <div v-if="comparisonType === 'table'" class="table-comparison">
          <el-table :data="comparisonData" border>
            <el-table-column prop="metric" label="指标" width="150" fixed />
            <el-table-column
              v-for="strategy in selectedStrategies"
              :key="strategy.id"
              :label="strategy.name"
              min-width="120"
              align="center"
            >
              <template #default="{ row }">
                <div class="metric-cell">
                  <span 
                    :class="getMetricClass(row.metric, row[strategy.id])"
                    class="metric-value"
                  >
                    {{ formatMetricValue(row.metric, row[strategy.id]) }}
                  </span>
                  <div v-if="row.rank" class="metric-rank">
                    第{{ row.rank[strategy.id] }}名
                  </div>
                </div>
              </template>
            </el-table-column>
          </el-table>
        </div>

        <!-- 雷达图对比 -->
        <div v-if="comparisonType === 'radar'" class="chart-comparison">
          <div ref="radarChart" class="chart-container"></div>
        </div>

        <!-- 柱状图对比 -->
        <div v-if="comparisonType === 'bar'" class="chart-comparison">
          <div ref="barChart" class="chart-container"></div>
        </div>
      </el-card>

      <!-- 详细分析 -->
      <div class="detailed-analysis">
        <el-row :gutter="24">
          <!-- 收益对比 -->
          <el-col :span="12">
            <el-card class="analysis-card">
              <template #header>
                <div class="card-header">
                  <span>收益率对比</span>
                  <el-select v-model="returnPeriod" size="small" style="width: 100px">
                    <el-option label="年化" value="annual" />
                    <el-option label="总收益" value="total" />
                    <el-option label="月度" value="monthly" />
                  </el-select>
                </div>
              </template>
              <div ref="returnChart" class="chart-container small"></div>
            </el-card>
          </el-col>

          <!-- 风险对比 -->
          <el-col :span="12">
            <el-card class="analysis-card">
              <template #header>
                <span>风险指标对比</span>
              </template>
              <div ref="riskChart" class="chart-container small"></div>
            </el-card>
          </el-col>
        </el-row>

        <el-row :gutter="24" style="margin-top: 24px;">
          <!-- 净值曲线对比 -->
          <el-col :span="24">
            <el-card class="analysis-card">
              <template #header>
                <div class="card-header">
                  <span>净值曲线对比</span>
                  <div class="chart-controls">
                    <el-checkbox-group v-model="visibleStrategies" size="small">
                      <el-checkbox 
                        v-for="strategy in selectedStrategies"
                        :key="strategy.id"
                        :label="strategy.id"
                      >
                        {{ strategy.name }}
                      </el-checkbox>
                    </el-checkbox-group>
                    <el-button size="small" @click="resetZoom">
                      <el-icon><ZoomOut /></el-icon>
                      重置缩放
                    </el-button>
                  </div>
                </div>
              </template>
              <div ref="navChart" class="chart-container large"></div>
            </el-card>
          </el-col>
        </el-row>

        <el-row :gutter="24" style="margin-top: 24px;">
          <!-- 回撤对比 -->
          <el-col :span="12">
            <el-card class="analysis-card">
              <template #header>
                <span>最大回撤对比</span>
              </template>
              <div ref="drawdownChart" class="chart-container small"></div>
            </el-card>
          </el-col>

          <!-- 夏普比率对比 -->
          <el-col :span="12">
            <el-card class="analysis-card">
              <template #header>
                <span>夏普比率对比</span>
              </template>
              <div ref="sharpeChart" class="chart-container small"></div>
            </el-card>
          </el-col>
        </el-row>
      </div>

      <!-- AI分析报告 -->
      <el-card class="ai-analysis-report">
        <template #header>
          <div class="analysis-header">
            <span>
              <el-icon><MagicStick /></el-icon>
              AI智能对比分析
            </span>
            <el-button @click="generateAnalysis" :loading="generatingAnalysis" size="small">
              <el-icon><Refresh /></el-icon>
              重新分析
            </el-button>
          </div>
        </template>

        <div class="analysis-content">
          <div class="analysis-summary">
            <h4>整体评价</h4>
            <p class="summary-text">{{ analysisReport.summary }}</p>
          </div>

          <div class="analysis-details">
            <el-row :gutter="24">
              <el-col :span="8">
                <div class="analysis-section">
                  <h5>🏆 最佳表现策略</h5>
                  <div class="best-strategy">
                    <span class="strategy-name">{{ analysisReport.bestStrategy.name }}</span>
                    <span class="strategy-reason">{{ analysisReport.bestStrategy.reason }}</span>
                  </div>
                </div>
              </el-col>

              <el-col :span="8">
                <div class="analysis-section">
                  <h5>⚖️ 风险收益平衡</h5>
                  <div class="balanced-strategy">
                    <span class="strategy-name">{{ analysisReport.balancedStrategy.name }}</span>
                    <span class="strategy-reason">{{ analysisReport.balancedStrategy.reason }}</span>
                  </div>
                </div>
              </el-col>

              <el-col :span="8">
                <div class="analysis-section">
                  <h5>💡 优化建议</h5>
                  <ul class="optimization-list">
                    <li v-for="suggestion in analysisReport.suggestions" :key="suggestion">
                      {{ suggestion }}
                    </li>
                  </ul>
                </div>
              </el-col>
            </el-row>
          </div>

          <div class="analysis-ranking">
            <h4>综合排名</h4>
            <div class="ranking-list">
              <div 
                v-for="(item, index) in analysisReport.ranking" 
                :key="item.id"
                class="ranking-item"
              >
                <div class="rank-number" :class="getRankClass(index)">{{ index + 1 }}</div>
                <div class="strategy-info">
                  <span class="strategy-name">{{ item.name }}</span>
                  <span class="strategy-score">{{ item.score.toFixed(1) }}分</span>
                </div>
                <div class="strategy-highlights">
                  <el-tag 
                    v-for="highlight in item.highlights" 
                    :key="highlight"
                    size="small"
                    type="info"
                  >
                    {{ highlight }}
                  </el-tag>
                </div>
              </div>
            </div>
          </div>
        </div>
      </el-card>

      <!-- 导出功能 -->
      <el-card class="export-section">
        <template #header>
          <span>导出对比报告</span>
        </template>
        
        <div class="export-options">
          <el-row :gutter="16">
            <el-col :span="6">
              <el-button @click="exportReport('pdf')" type="primary">
                <el-icon><Document /></el-icon>
                导出PDF报告
              </el-button>
            </el-col>
            <el-col :span="6">
              <el-button @click="exportReport('excel')">
                <el-icon><DocumentExcel /></el-icon>
                导出Excel数据
              </el-button>
            </el-col>
            <el-col :span="6">
              <el-button @click="exportReport('image')">
                <el-icon><Picture /></el-icon>
                导出图表
              </el-button>
            </el-col>
            <el-col :span="6">
              <el-button @click="shareComparison">
                <el-icon><Share /></el-icon>
                分享对比
              </el-button>
            </el-col>
          </el-row>
        </div>
      </el-card>
    </div>

    <!-- 空状态 -->
    <el-empty v-else description="请选择至少2个策略进行对比分析" image-size="120">
      <el-button type="primary" @click="selectDefaultStrategies">选择推荐策略</el-button>
    </el-empty>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Delete, ZoomOut, MagicStick, Refresh, Document, DocumentExcel,
  Picture, Share
} from '@element-plus/icons-vue'

// 接口定义
interface Strategy {
  id: string
  name: string
  type: string
  score: number
  annualReturn: number
  totalReturn: number
  sharpeRatio: number
  maxDrawdown: number
  winRate: number
  informationRatio: number
  volatility: number
  calmarRatio: number
}

interface ComparisonMetric {
  metric: string
  [key: string]: any
}

interface AnalysisReport {
  summary: string
  bestStrategy: {
    name: string
    reason: string
  }
  balancedStrategy: {
    name: string
    reason: string
  }
  suggestions: string[]
  ranking: Array<{
    id: string
    name: string
    score: number
    highlights: string[]
  }>
}

// 响应式数据
const selectedStrategyIds = ref<string[]>([])
const comparisonType = ref('table')
const returnPeriod = ref('annual')
const visibleStrategies = ref<string[]>([])
const generatingAnalysis = ref(false)

// 模拟可用策略数据
const availableStrategies = ref<Strategy[]>([
  {
    id: 'strategy_1',
    name: 'LightGBM多因子策略v3.2',
    type: '机器学习策略',
    score: 9.2,
    annualReturn: 0.285,
    totalReturn: 0.456,
    sharpeRatio: 1.45,
    maxDrawdown: -0.082,
    winRate: 62.5,
    informationRatio: 0.85,
    volatility: 0.18,
    calmarRatio: 3.48
  },
  {
    id: 'strategy_2',
    name: 'XGBoost量化选股v2.8',
    type: '机器学习策略',
    score: 8.7,
    annualReturn: 0.231,
    totalReturn: 0.387,
    sharpeRatio: 1.28,
    maxDrawdown: -0.095,
    winRate: 58.3,
    informationRatio: 0.72,
    volatility: 0.16,
    calmarRatio: 2.43
  },
  {
    id: 'strategy_3',
    name: 'LSTM深度学习策略v1.5',
    type: '深度学习策略',
    score: 8.3,
    annualReturn: 0.198,
    totalReturn: 0.325,
    sharpeRatio: 1.15,
    maxDrawdown: -0.125,
    winRate: 55.7,
    informationRatio: 0.68,
    volatility: 0.19,
    calmarRatio: 1.58
  },
  {
    id: 'strategy_4',
    name: '多空对冲策略v2.1',
    type: '对冲策略',
    score: 7.8,
    annualReturn: 0.156,
    totalReturn: 0.268,
    sharpeRatio: 1.02,
    maxDrawdown: -0.065,
    winRate: 52.8,
    informationRatio: 0.58,
    volatility: 0.14,
    calmarRatio: 2.40
  },
  {
    id: 'strategy_5',
    name: '动量反转混合策略v1.8',
    type: '技术策略',
    score: 7.3,
    annualReturn: 0.142,
    totalReturn: 0.245,
    sharpeRatio: 0.95,
    maxDrawdown: -0.108,
    winRate: 49.6,
    informationRatio: 0.51,
    volatility: 0.17,
    calmarRatio: 1.31
  }
])

// AI分析报告
const analysisReport = ref<AnalysisReport>({
  summary: '基于当前选择的策略，LightGBM多因子策略在收益和风险平衡方面表现最佳，XGBoost策略在稳定性方面表现突出。建议根据您的风险偏好选择合适的策略组合。',
  bestStrategy: {
    name: 'LightGBM多因子策略v3.2',
    reason: '年化收益率28.5%，夏普比率1.45，综合表现最优'
  },
  balancedStrategy: {
    name: '多空对冲策略v2.1',
    reason: '最大回撤仅6.5%，风险控制能力强，适合稳健投资'
  },
  suggestions: [
    '可考虑组合使用LightGBM和对冲策略以平衡收益和风险',
    '建议定期调整策略权重以适应市场变化',
    '关注LSTM策略的改进空间，可能通过参数优化提升表现'
  ],
  ranking: [
    {
      id: 'strategy_1',
      name: 'LightGBM多因子策略v3.2',
      score: 9.2,
      highlights: ['最高收益', '优秀夏普比率']
    },
    {
      id: 'strategy_2',
      name: 'XGBoost量化选股v2.8',
      score: 8.7,
      highlights: ['稳定表现', '良好信息比率']
    }
  ]
})

// 计算属性
const selectedStrategies = computed(() => {
  return availableStrategies.value.filter(s => selectedStrategyIds.value.includes(s.id))
})

const comparisonData = computed(() => {
  if (selectedStrategies.value.length === 0) return []

  const metrics = [
    '年化收益率',
    '总收益率', 
    '夏普比率',
    '最大回撤',
    '胜率',
    '信息比率',
    '年化波动率',
    '卡玛比率'
  ]

  return metrics.map(metric => {
    const row: ComparisonMetric = { metric }
    const ranks: { [key: string]: number } = {}
    
    selectedStrategies.value.forEach(strategy => {
      switch (metric) {
        case '年化收益率':
          row[strategy.id] = strategy.annualReturn
          break
        case '总收益率':
          row[strategy.id] = strategy.totalReturn
          break
        case '夏普比率':
          row[strategy.id] = strategy.sharpeRatio
          break
        case '最大回撤':
          row[strategy.id] = strategy.maxDrawdown
          break
        case '胜率':
          row[strategy.id] = strategy.winRate / 100
          break
        case '信息比率':
          row[strategy.id] = strategy.informationRatio
          break
        case '年化波动率':
          row[strategy.id] = strategy.volatility
          break
        case '卡玛比率':
          row[strategy.id] = strategy.calmarRatio
          break
      }
    })

    // 计算排名
    const values = selectedStrategies.value.map(s => ({
      id: s.id,
      value: row[s.id]
    }))
    
    // 回撤和波动率是越小越好，其他指标是越大越好
    const isReverseSort = metric === '最大回撤' || metric === '年化波动率'
    values.sort((a, b) => isReverseSort ? a.value - b.value : b.value - a.value)
    
    values.forEach((item, index) => {
      ranks[item.id] = index + 1
    })
    
    row.rank = ranks
    return row
  })
})

// 方法
const getPerformanceTagType = (score: number) => {
  if (score >= 9) return 'success'
  if (score >= 8) return 'primary'
  if (score >= 7) return 'warning'
  return 'danger'
}

const handleStrategySelect = () => {
  // 更新可见策略列表
  visibleStrategies.value = [...selectedStrategyIds.value]
  
  if (selectedStrategies.value.length >= 2) {
    // 自动生成分析报告
    generateAnalysis()
  }
}

const removeStrategy = (strategyId: string) => {
  selectedStrategyIds.value = selectedStrategyIds.value.filter(id => id !== strategyId)
  visibleStrategies.value = visibleStrategies.value.filter(id => id !== strategyId)
}

const clearAll = () => {
  selectedStrategyIds.value = []
  visibleStrategies.value = []
}

const selectDefaultStrategies = () => {
  // 选择评分最高的3个策略
  const topStrategies = [...availableStrategies.value]
    .sort((a, b) => b.score - a.score)
    .slice(0, 3)
    .map(s => s.id)
  
  selectedStrategyIds.value = topStrategies
  handleStrategySelect()
  ElMessage.success('已选择推荐策略进行对比')
}

const getMetricClass = (metric: string, value: number) => {
  if (metric === '最大回撤' || metric === '年化波动率') {
    return Math.abs(value) <= 0.1 ? 'metric-good' : 'metric-poor'
  }
  
  if (metric === '年化收益率' || metric === '总收益率') {
    return value >= 0.2 ? 'metric-excellent' : value >= 0.1 ? 'metric-good' : 'metric-average'
  }
  
  if (metric === '夏普比率' || metric === '信息比率') {
    return value >= 1.5 ? 'metric-excellent' : value >= 1.0 ? 'metric-good' : 'metric-average'
  }
  
  return 'metric-average'
}

const formatMetricValue = (metric: string, value: number) => {
  if (metric.includes('收益率') || metric === '胜率' || metric === '年化波动率') {
    return `${(value * 100).toFixed(2)}%`
  }
  return value.toFixed(2)
}

const getRankClass = (index: number) => {
  if (index === 0) return 'rank-first'
  if (index === 1) return 'rank-second'
  if (index === 2) return 'rank-third'
  return 'rank-normal'
}

const generateAnalysis = () => {
  generatingAnalysis.value = true
  
  setTimeout(() => {
    // 更新分析报告
    const sortedStrategies = [...selectedStrategies.value].sort((a, b) => b.score - a.score)
    
    analysisReport.value.bestStrategy = {
      name: sortedStrategies[0]?.name || '',
      reason: `年化收益率${(sortedStrategies[0]?.annualReturn * 100).toFixed(1)}%，夏普比率${sortedStrategies[0]?.sharpeRatio.toFixed(2)}，综合表现最优`
    }
    
    // 找到风险最低的策略
    const lowestRiskStrategy = [...selectedStrategies.value].sort((a, b) => a.maxDrawdown - b.maxDrawdown)[0]
    analysisReport.value.balancedStrategy = {
      name: lowestRiskStrategy?.name || '',
      reason: `最大回撤仅${Math.abs(lowestRiskStrategy?.maxDrawdown * 100).toFixed(1)}%，风险控制能力强`
    }
    
    analysisReport.value.ranking = sortedStrategies.map(strategy => ({
      id: strategy.id,
      name: strategy.name,
      score: strategy.score,
      highlights: getStrategyHighlights(strategy)
    }))
    
    generatingAnalysis.value = false
    ElMessage.success('AI分析报告已更新')
  }, 2000)
}

const getStrategyHighlights = (strategy: Strategy) => {
  const highlights = []
  
  if (strategy.annualReturn >= 0.25) highlights.push('高收益')
  if (strategy.sharpeRatio >= 1.4) highlights.push('优秀夏普比率')
  if (Math.abs(strategy.maxDrawdown) <= 0.08) highlights.push('低回撤')
  if (strategy.winRate >= 60) highlights.push('高胜率')
  if (strategy.informationRatio >= 0.8) highlights.push('良好信息比率')
  
  return highlights.length > 0 ? highlights : ['均衡表现']
}

const resetZoom = () => {
  ElMessage.info('图表缩放已重置')
}

const exportReport = (type: string) => {
  ElMessage.success(`开始导出${type.toUpperCase()}格式报告`)
}

const shareComparison = () => {
  ElMessage.success('对比链接已复制到剪贴板')
}

// 监听选择变化
watch(selectedStrategies, (newStrategies) => {
  if (newStrategies.length >= 2) {
    // 初始化图表等
  }
}, { immediate: true })

// 暴露给父组件的方法
defineExpose({
  addStrategy: (strategyId: string) => {
    if (selectedStrategyIds.value.length < 5 && !selectedStrategyIds.value.includes(strategyId)) {
      selectedStrategyIds.value.push(strategyId)
      handleStrategySelect()
    }
  },
  getComparisonData: () => comparisonData.value
})

onMounted(() => {
  // 初始化
})
</script>

<style scoped>
.strategy-comparison {
  width: 100%;
}

.strategy-selector {
  margin-bottom: 24px;
}

.selector-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.selector-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.selector-label {
  font-weight: 600;
  color: #303133;
  margin-bottom: 8px;
  display: block;
}

.strategy-option {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.strategy-name {
  font-weight: 600;
  color: #303133;
}

.strategy-type {
  color: #909399;
  font-size: 12px;
}

.strategy-score {
  margin-left: auto;
}

.selected-strategies {
  border-top: 1px solid #e4e7ed;
  padding-top: 16px;
}

.selected-header {
  font-weight: 600;
  color: #303133;
  margin-bottom: 12px;
}

.strategy-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.strategy-tag {
  padding: 8px 12px;
  height: auto;
}

.tag-content {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.tag-name {
  font-weight: 600;
}

.tag-score {
  font-size: 12px;
  opacity: 0.8;
}

.comparison-results {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.overview-comparison {
  margin-bottom: 24px;
}

.comparison-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.table-comparison {
  overflow-x: auto;
}

.metric-cell {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.metric-value {
  font-weight: 600;
}

.metric-value.metric-excellent {
  color: #67c23a;
}

.metric-value.metric-good {
  color: #409eff;
}

.metric-value.metric-average {
  color: #e6a23c;
}

.metric-value.metric-poor {
  color: #f56c6c;
}

.metric-rank {
  font-size: 12px;
  color: #909399;
}

.chart-comparison {
  width: 100%;
  display: flex;
  justify-content: center;
}

.chart-container {
  width: 100%;
  background: #f5f7fa;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #909399;
  font-size: 14px;
}

.chart-container.small {
  height: 300px;
}

.chart-container.large {
  height: 400px;
}

.detailed-analysis {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.analysis-card {
  height: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chart-controls {
  display: flex;
  align-items: center;
  gap: 16px;
}

.ai-analysis-report {
  margin-top: 24px;
}

.analysis-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.analysis-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.analysis-summary {
  padding: 16px;
  background: #f0f8ff;
  border-radius: 6px;
}

.analysis-summary h4 {
  margin: 0 0 12px 0;
  color: #303133;
}

.summary-text {
  color: #606266;
  line-height: 1.6;
  margin: 0;
}

.analysis-details {
  padding: 16px;
  background: #f8f9fa;
  border-radius: 6px;
}

.analysis-section {
  text-align: center;
}

.analysis-section h5 {
  margin: 0 0 12px 0;
  color: #303133;
  font-size: 16px;
}

.best-strategy,
.balanced-strategy {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.strategy-name {
  font-weight: 600;
  color: #409eff;
}

.strategy-reason {
  font-size: 14px;
  color: #606266;
}

.optimization-list {
  text-align: left;
  padding-left: 16px;
  margin: 0;
}

.optimization-list li {
  color: #606266;
  line-height: 1.6;
  margin-bottom: 8px;
}

.analysis-ranking {
  padding: 16px;
  background: #fafafa;
  border-radius: 6px;
}

.analysis-ranking h4 {
  margin: 0 0 16px 0;
  color: #303133;
}

.ranking-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.ranking-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px;
  background: #fff;
  border-radius: 6px;
  border: 1px solid #e4e7ed;
}

.rank-number {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  color: #fff;
}

.rank-number.rank-first {
  background: linear-gradient(135deg, #ffd700, #ffed4e);
  color: #d48806;
}

.rank-number.rank-second {
  background: linear-gradient(135deg, #c0c0c0, #e8e8e8);
  color: #595959;
}

.rank-number.rank-third {
  background: linear-gradient(135deg, #cd7f32, #daa520);
  color: #8b4513;
}

.rank-number.rank-normal {
  background: #909399;
}

.strategy-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.strategy-score {
  color: #409eff;
  font-weight: 600;
}

.strategy-highlights {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.export-section {
  margin-top: 24px;
}

.export-options {
  padding: 16px;
}

@media (max-width: 768px) {
  .comparison-header {
    flex-direction: column;
    gap: 12px;
  }
  
  .chart-controls {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
  
  .analysis-details .el-row {
    flex-direction: column;
  }
  
  .ranking-item {
    flex-direction: column;
    text-align: center;
    gap: 8px;
  }
  
  .export-options .el-row {
    flex-direction: column;
    gap: 12px;
  }
}
</style>