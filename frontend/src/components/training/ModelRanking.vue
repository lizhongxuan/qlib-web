<template>
  <el-card class="model-ranking">
    <template #header>
      <div class="ranking-header">
        <div class="header-content">
          <el-icon><TrendCharts /></el-icon>
          <span>模型性能排行榜</span>
        </div>
        <div class="header-actions">
          <el-select v-model="rankingMetric" size="small" style="width: 120px">
            <el-option label="准确率" value="accuracy" />
            <el-option label="F1分数" value="f1Score" />
            <el-option label="AUC" value="auc" />
            <el-option label="夏普比率" value="sharpeRatio" />
          </el-select>
          <el-button size="small" @click="refreshRanking">
            <el-icon><Refresh /></el-icon>
          </el-button>
        </div>
      </div>
    </template>

    <div class="ranking-content">
      <!-- 前三名展示 -->
      <div class="top-three">
        <div 
          v-for="(model, index) in topThreeModels" 
          :key="model.id"
          :class="['podium-item', `rank-${index + 1}`]"
          @click="$emit('model-selected', model)"
        >
          <div class="podium-rank">
            <div class="rank-icon">
              <el-icon v-if="index === 0"><Trophy /></el-icon>
              <el-icon v-else-if="index === 1"><Medal /></el-icon>
              <el-icon v-else><Award /></el-icon>
            </div>
            <div class="rank-number">{{ index + 1 }}</div>
          </div>
          
          <div class="podium-content">
            <div class="model-name">{{ model.name }}</div>
            <div class="model-type">{{ model.type }}</div>
            <div class="model-score">
              {{ formatMetricValue(model.metrics[rankingMetric], rankingMetric) }}
            </div>
            <div class="score-label">{{ getMetricLabel(rankingMetric) }}</div>
          </div>
          
          <div class="podium-details">
            <el-tag size="small" :type="getPerformanceTagType(model.performance)">
              {{ model.performance }}
            </el-tag>
            <div class="created-date">
              {{ formatDate(model.createdAt) }}
            </div>
          </div>
        </div>
      </div>

      <!-- 完整排行榜 -->
      <div class="full-ranking">
        <div class="ranking-table">
          <div class="table-header">
            <div class="rank-col">排名</div>
            <div class="model-col">模型信息</div>
            <div class="metrics-col">性能指标</div>
            <div class="trend-col">趋势</div>
            <div class="date-col">训练时间</div>
            <div class="action-col">操作</div>
          </div>
          
          <div 
            v-for="(model, index) in rankedModels" 
            :key="model.id"
            class="table-row"
            @click="$emit('model-selected', model)"
          >
            <div class="rank-col">
              <div class="rank-display">
                <span class="rank-number">{{ index + 1 }}</span>
                <div 
                  v-if="model.rankChange" 
                  :class="['rank-change', model.rankChange > 0 ? 'up' : 'down']"
                >
                  <el-icon v-if="model.rankChange > 0"><CaretTop /></el-icon>
                  <el-icon v-else><CaretBottom /></el-icon>
                  <span>{{ Math.abs(model.rankChange) }}</span>
                </div>
              </div>
            </div>
            
            <div class="model-col">
              <div class="model-info">
                <div class="model-name">{{ model.name }}</div>
                <div class="model-meta">
                  <el-tag size="small" :type="getModelTagType(model.type)">
                    {{ model.type }}
                  </el-tag>
                  <span class="model-author">by {{ model.author }}</span>
                </div>
              </div>
            </div>
            
            <div class="metrics-col">
              <div class="metrics-grid">
                <div class="metric-item primary">
                  <span class="metric-value">
                    {{ formatMetricValue(model.metrics[rankingMetric], rankingMetric) }}
                  </span>
                  <span class="metric-label">{{ getMetricLabel(rankingMetric) }}</span>
                </div>
                <div class="metric-item">
                  <span class="metric-value">
                    {{ formatMetricValue(model.metrics.accuracy, 'accuracy') }}
                  </span>
                  <span class="metric-label">准确率</span>
                </div>
                <div class="metric-item">
                  <span class="metric-value">
                    {{ formatMetricValue(model.metrics.f1Score, 'f1Score') }}
                  </span>
                  <span class="metric-label">F1</span>
                </div>
              </div>
            </div>
            
            <div class="trend-col">
              <div class="performance-trend">
                <div ref="trendChart" :data-model-id="model.id" class="mini-chart"></div>
                <div class="trend-info">
                  <span :class="['trend-text', model.trend > 0 ? 'positive' : 'negative']">
                    {{ model.trend > 0 ? '+' : '' }}{{ model.trend.toFixed(1) }}%
                  </span>
                </div>
              </div>
            </div>
            
            <div class="date-col">
              <div class="date-info">
                <div class="date-text">{{ formatDate(model.createdAt) }}</div>
                <div class="duration-text">{{ formatDuration(model.trainingTime) }}</div>
              </div>
            </div>
            
            <div class="action-col" @click.stop>
              <el-button size="small" @click="viewModelDetail(model)">
                详情
              </el-button>
              <el-button size="small" @click="compareModel(model)">
                对比
              </el-button>
              <el-dropdown @command="(cmd) => handleModelAction(cmd, model)" trigger="click">
                <el-button size="small">
                  <el-icon><MoreFilled /></el-icon>
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="clone">克隆配置</el-dropdown-item>
                    <el-dropdown-item command="export">导出模型</el-dropdown-item>
                    <el-dropdown-item command="analyze">分析报告</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </div>
        </div>

        <!-- 加载更多 -->
        <div v-if="hasMore" class="load-more">
          <el-button @click="loadMore" :loading="loadingMore">
            加载更多排行榜
          </el-button>
        </div>
      </div>

      <!-- 性能分析图表 -->
      <div class="performance-chart">
        <h4>性能趋势分析</h4>
        <div ref="performanceChart" class="chart-container"></div>
      </div>
    </div>

    <!-- 模型详情对话框 -->
    <el-dialog v-model="showModelDetail" :title="`模型详情 - ${selectedModel?.name}`" width="70%">
      <div v-if="selectedModel" class="model-detail-dialog">
        <el-tabs v-model="activeDetailTab">
          <el-tab-pane label="性能指标" name="metrics">
            <div class="metrics-detail">
              <el-row :gutter="24">
                <el-col :span="12">
                  <el-descriptions title="主要指标" :column="1" border>
                    <el-descriptions-item label="准确率">
                      {{ formatMetricValue(selectedModel.metrics.accuracy, 'accuracy') }}
                    </el-descriptions-item>
                    <el-descriptions-item label="精确率">
                      {{ formatMetricValue(selectedModel.metrics.precision || 0, 'precision') }}
                    </el-descriptions-item>
                    <el-descriptions-item label="召回率">
                      {{ formatMetricValue(selectedModel.metrics.recall || 0, 'recall') }}
                    </el-descriptions-item>
                    <el-descriptions-item label="F1分数">
                      {{ formatMetricValue(selectedModel.metrics.f1Score, 'f1Score') }}
                    </el-descriptions-item>
                  </el-descriptions>
                </el-col>
                <el-col :span="12">
                  <el-descriptions title="财务指标" :column="1" border>
                    <el-descriptions-item label="夏普比率">
                      {{ formatMetricValue(selectedModel.metrics.sharpeRatio || 0, 'sharpeRatio') }}
                    </el-descriptions-item>
                    <el-descriptions-item label="最大回撤">
                      {{ formatMetricValue(selectedModel.metrics.maxDrawdown || 0, 'maxDrawdown') }}
                    </el-descriptions-item>
                    <el-descriptions-item label="年化收益">
                      {{ formatMetricValue(selectedModel.metrics.annualReturn || 0, 'annualReturn') }}
                    </el-descriptions-item>
                    <el-descriptions-item label="波动率">
                      {{ formatMetricValue(selectedModel.metrics.volatility || 0, 'volatility') }}
                    </el-descriptions-item>
                  </el-descriptions>
                </el-col>
              </el-row>
            </div>
          </el-tab-pane>
          
          <el-tab-pane label="训练配置" name="config">
            <div class="config-detail">
              <pre>{{ JSON.stringify(selectedModel.config, null, 2) }}</pre>
            </div>
          </el-tab-pane>
          
          <el-tab-pane label="特征重要性" name="features">
            <div class="features-detail">
              <div ref="featureChart" class="feature-importance-chart"></div>
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>
    </el-dialog>
  </el-card>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import {
  TrendCharts, Refresh, Trophy, Medal, Award, CaretTop, CaretBottom,
  MoreFilled
} from '@element-plus/icons-vue'

interface ModelMetrics {
  accuracy: number
  precision?: number
  recall?: number
  f1Score: number
  auc?: number
  sharpeRatio?: number
  maxDrawdown?: number
  annualReturn?: number
  volatility?: number
}

interface RankedModel {
  id: string
  name: string
  type: string
  author: string
  metrics: ModelMetrics
  performance: 'excellent' | 'good' | 'fair' | 'poor'
  trend: number // 性能变化趋势百分比
  rankChange?: number // 排名变化
  createdAt: Date
  trainingTime: number // 训练耗时(秒)
  config: any
}

const emit = defineEmits(['model-selected'])

// 响应式数据
const rankingMetric = ref<keyof ModelMetrics>('accuracy')
const loadingMore = ref(false)
const hasMore = ref(true)
const showModelDetail = ref(false)
const selectedModel = ref<RankedModel | null>(null)
const activeDetailTab = ref('metrics')

// 图表DOM引用
const performanceChart = ref<HTMLElement>()
const featureChart = ref<HTMLElement>()

// 模拟模型数据
const models = ref<RankedModel[]>([
  {
    id: '1',
    name: 'LightGBM_Alpha_v3.2',
    type: 'LightGBM',
    author: 'DataScientist',
    metrics: {
      accuracy: 89.5,
      precision: 87.2,
      recall: 91.8,
      f1Score: 0.894,
      auc: 0.923,
      sharpeRatio: 2.45,
      maxDrawdown: -0.082,
      annualReturn: 0.187,
      volatility: 0.156
    },
    performance: 'excellent',
    trend: 2.3,
    rankChange: 1,
    createdAt: new Date('2024-01-20'),
    trainingTime: 1800,
    config: {
      modelType: 'LightGBM',
      parameters: {
        num_leaves: 31,
        learning_rate: 0.05
      }
    }
  },
  {
    id: '2',
    name: 'XGBoost_ProFactor_v2.1',
    type: 'XGBoost',
    author: 'QuanDev',
    metrics: {
      accuracy: 87.8,
      precision: 85.6,
      recall: 90.1,
      f1Score: 0.878,
      auc: 0.912,
      sharpeRatio: 2.21,
      maxDrawdown: -0.095,
      annualReturn: 0.164,
      volatility: 0.142
    },
    performance: 'excellent',
    trend: -0.8,
    rankChange: -1,
    createdAt: new Date('2024-01-18'),
    trainingTime: 2400,
    config: {
      modelType: 'XGBoost',
      parameters: {
        max_depth: 6,
        learning_rate: 0.05
      }
    }
  },
  {
    id: '3',
    name: 'LSTM_TimeSeries_v1.5',
    type: 'LSTM',
    author: 'DeepLearner',
    metrics: {
      accuracy: 85.2,
      precision: 83.8,
      recall: 87.6,
      f1Score: 0.856,
      auc: 0.887,
      sharpeRatio: 1.89,
      maxDrawdown: -0.112,
      annualReturn: 0.143,
      volatility: 0.178
    },
    performance: 'good',
    trend: 1.5,
    createdAt: new Date('2024-01-15'),
    trainingTime: 5400,
    config: {
      modelType: 'LSTM',
      parameters: {
        hidden_size: 64,
        num_layers: 2
      }
    }
  }
])

// 计算属性
const rankedModels = computed(() => {
  return [...models.value].sort((a, b) => {
    const aValue = a.metrics[rankingMetric.value] || 0
    const bValue = b.metrics[rankingMetric.value] || 0
    return bValue - aValue
  })
})

const topThreeModels = computed(() => {
  return rankedModels.value.slice(0, 3)
})

// 方法
const getMetricLabel = (metric: keyof ModelMetrics) => {
  const labels: Record<keyof ModelMetrics, string> = {
    accuracy: '准确率',
    precision: '精确率',
    recall: '召回率',
    f1Score: 'F1分数',
    auc: 'AUC',
    sharpeRatio: '夏普比率',
    maxDrawdown: '最大回撤',
    annualReturn: '年化收益',
    volatility: '波动率'
  }
  return labels[metric] || metric
}

const formatMetricValue = (value: number | undefined, metric: keyof ModelMetrics) => {
  if (value === undefined) return '--'
  
  switch (metric) {
    case 'accuracy':
    case 'precision':
    case 'recall':
      return `${value.toFixed(1)}%`
    case 'f1Score':
    case 'auc':
      return value.toFixed(3)
    case 'sharpeRatio':
      return value.toFixed(2)
    case 'maxDrawdown':
      return `${(value * 100).toFixed(1)}%`
    case 'annualReturn':
      return `${(value * 100).toFixed(1)}%`
    case 'volatility':
      return `${(value * 100).toFixed(1)}%`
    default:
      return value.toFixed(2)
  }
}

const getPerformanceTagType = (performance: string) => {
  switch (performance) {
    case 'excellent': return 'success'
    case 'good': return 'primary'
    case 'fair': return 'warning'
    case 'poor': return 'danger'
    default: return 'info'
  }
}

const getModelTagType = (modelType: string) => {
  switch (modelType) {
    case 'LightGBM': return 'success'
    case 'XGBoost': return 'warning'
    case 'LSTM': return 'info'
    case 'Transformer': return 'danger'
    default: return 'info'
  }
}

const formatDate = (date: Date) => {
  return date.toLocaleDateString('zh-CN', {
    month: '2-digit',
    day: '2-digit'
  })
}

const formatDuration = (seconds: number) => {
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  
  if (hours > 0) {
    return `${hours}h${minutes}m`
  }
  return `${minutes}m`
}

const refreshRanking = () => {
  ElMessage.success('排行榜已刷新')
}

const viewModelDetail = (model: RankedModel) => {
  selectedModel.value = model
  showModelDetail.value = true
  nextTick(() => {
    initializeCharts()
  })
}

const compareModel = (model: RankedModel) => {
  ElMessage.info(`添加 ${model.name} 到对比列表`)
}

const handleModelAction = (command: string, model: RankedModel) => {
  switch (command) {
    case 'clone':
      ElMessage.success(`克隆 ${model.name} 的配置`)
      break
    case 'export':
      ElMessage.success(`导出 ${model.name}`)
      break
    case 'analyze':
      ElMessage.info(`生成 ${model.name} 的分析报告`)
      break
  }
}

const loadMore = () => {
  loadingMore.value = true
  
  // 模拟加载更多数据
  setTimeout(() => {
    loadingMore.value = false
    hasMore.value = false
    ElMessage.success('已加载全部排行榜数据')
  }, 1000)
}

const initializeCharts = () => {
  // 这里可以初始化图表
  // 暂时使用占位符
}

// 生命周期
onMounted(() => {
  // 初始化图表
  initializeCharts()
})
</script>

<style scoped>
.model-ranking {
  margin-bottom: 32px;
}

.ranking-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-content {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
}

.header-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.ranking-content {
  display: flex;
  flex-direction: column;
  gap: 32px;
}

/* 前三名展示 */
.top-three {
  display: flex;
  gap: 24px;
  justify-content: center;
}

.podium-item {
  flex: 1;
  max-width: 300px;
  padding: 24px;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
  text-align: center;
}

.podium-item.rank-1 {
  background: linear-gradient(135deg, #ffd700 0%, #ffed4e 100%);
  border: 2px solid #f7ba2a;
}

.podium-item.rank-2 {
  background: linear-gradient(135deg, #c0c0c0 0%, #e8e8e8 100%);
  border: 2px solid #a8a8a8;
}

.podium-item.rank-3 {
  background: linear-gradient(135deg, #cd7f32 0%, #deb887 100%);
  border: 2px solid #b8860b;
}

.podium-item:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 30px rgba(0, 0, 0, 0.15);
}

.podium-rank {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 16px;
}

.rank-icon {
  font-size: 32px;
  margin-bottom: 8px;
}

.rank-number {
  font-size: 24px;
  font-weight: bold;
  color: #333;
}

.podium-content {
  margin-bottom: 16px;
}

.model-name {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin-bottom: 4px;
}

.model-type {
  font-size: 14px;
  color: #666;
  margin-bottom: 12px;
}

.model-score {
  font-size: 24px;
  font-weight: bold;
  color: #333;
  line-height: 1;
  margin-bottom: 4px;
}

.score-label {
  font-size: 12px;
  color: #666;
}

.podium-details {
  display: flex;
  flex-direction: column;
  gap: 8px;
  align-items: center;
}

.created-date {
  font-size: 12px;
  color: #888;
}

/* 完整排行榜 */
.full-ranking {
  background: #fff;
  border-radius: 8px;
}

.ranking-table {
  width: 100%;
}

.table-header {
  display: flex;
  background: #f8f9fa;
  padding: 16px;
  border-radius: 8px 8px 0 0;
  font-weight: 600;
  color: #606266;
  font-size: 14px;
}

.table-row {
  display: flex;
  align-items: center;
  padding: 16px;
  border-bottom: 1px solid #ebeef5;
  cursor: pointer;
  transition: background-color 0.3s ease;
}

.table-row:hover {
  background-color: #f5f7fa;
}

.rank-col {
  width: 80px;
  flex-shrink: 0;
}

.model-col {
  width: 250px;
  flex-shrink: 0;
}

.metrics-col {
  width: 300px;
  flex-shrink: 0;
}

.trend-col {
  width: 120px;
  flex-shrink: 0;
}

.date-col {
  width: 120px;
  flex-shrink: 0;
}

.action-col {
  flex: 1;
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

.rank-display {
  display: flex;
  align-items: center;
  gap: 8px;
}

.rank-number {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.rank-change {
  display: flex;
  align-items: center;
  gap: 2px;
  font-size: 12px;
}

.rank-change.up {
  color: #67c23a;
}

.rank-change.down {
  color: #f56c6c;
}

.model-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.model-name {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.model-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}

.model-author {
  font-size: 13px;
  color: #909399;
}

.metrics-grid {
  display: flex;
  gap: 24px;
}

.metric-item {
  text-align: center;
}

.metric-item.primary {
  border: 2px solid #409eff;
  border-radius: 6px;
  padding: 8px;
  background: #f0f8ff;
}

.metric-value {
  display: block;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  line-height: 1.2;
}

.metric-label {
  font-size: 12px;
  color: #909399;
  margin-top: 2px;
}

.performance-trend {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.mini-chart {
  width: 60px;
  height: 30px;
  background: #f5f7fa;
  border-radius: 4px;
}

.trend-text.positive {
  color: #67c23a;
}

.trend-text.negative {
  color: #f56c6c;
}

.date-info {
  text-align: center;
}

.date-text {
  font-size: 14px;
  color: #303133;
  margin-bottom: 4px;
}

.duration-text {
  font-size: 12px;
  color: #909399;
}

.load-more {
  text-align: center;
  padding: 24px;
}

.performance-chart {
  background: #f8f9fa;
  padding: 24px;
  border-radius: 8px;
}

.performance-chart h4 {
  margin: 0 0 16px 0;
  color: #303133;
}

.chart-container {
  width: 100%;
  height: 300px;
  background: #fff;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #909399;
}

/* 对话框样式 */
.model-detail-dialog {
  min-height: 500px;
}

.metrics-detail {
  padding: 16px 0;
}

.config-detail {
  padding: 16px;
  background: #f5f7fa;
  border-radius: 6px;
}

.config-detail pre {
  margin: 0;
  font-family: 'Monaco', 'Menlo', monospace;
  font-size: 12px;
  line-height: 1.5;
  color: #303133;
}

.features-detail {
  padding: 16px 0;
}

.feature-importance-chart {
  width: 100%;
  height: 400px;
  background: #f5f7fa;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #909399;
}

@media (max-width: 768px) {
  .top-three {
    flex-direction: column;
    gap: 16px;
  }
  
  .podium-item {
    max-width: none;
    padding: 20px;
  }
  
  .ranking-table {
    overflow-x: auto;
  }
  
  .table-header,
  .table-row {
    min-width: 800px;
  }
  
  .metrics-grid {
    flex-direction: column;
    gap: 12px;
  }
  
  .action-col {
    flex-direction: column;
    gap: 8px;
  }
}
</style>