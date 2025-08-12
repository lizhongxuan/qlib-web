<template>
  <el-card class="model-comparison" v-if="tasks.length > 0">
    <template #header>
      <div class="comparison-header">
        <div class="header-content">
          <el-icon><DataAnalysis /></el-icon>
          <span>模型对比分析</span>
          <el-tag size="small">{{ tasks.length }}/5 个模型</el-tag>
        </div>
        <div class="header-actions">
          <el-button size="small" @click="exportComparison">
            <el-icon><Download /></el-icon>
            导出报告
          </el-button>
          <el-button size="small" @click="clearComparison">
            <el-icon><Delete /></el-icon>
            清空对比
          </el-button>
        </div>
      </div>
    </template>

    <div class="comparison-content">
      <!-- 模型概览 -->
      <div class="models-overview">
        <div 
          v-for="task in tasks" 
          :key="task.id"
          class="model-overview-item"
        >
          <div class="model-card">
            <div class="model-header">
              <div class="model-title">
                <span class="model-name">{{ task.name }}</span>
                <el-button 
                  size="small" 
                  type="danger" 
                  text
                  @click="$emit('remove-task', task.id)"
                >
                  <el-icon><Close /></el-icon>
                </el-button>
              </div>
              <el-tag :type="getModelTagType(task.modelType)" size="small">
                {{ task.modelType }}
              </el-tag>
            </div>
            
            <div class="model-metrics">
              <div class="metric-item">
                <span class="metric-label">准确率</span>
                <span class="metric-value">
                  {{ formatMetric(task.bestMetrics?.accuracy, 'percentage') }}
                </span>
              </div>
              <div class="metric-item">
                <span class="metric-label">F1分数</span>
                <span class="metric-value">
                  {{ formatMetric(task.bestMetrics?.f1Score, 'decimal') }}
                </span>
              </div>
              <div class="metric-item">
                <span class="metric-label">训练时间</span>
                <span class="metric-value">{{ formatDuration(task.duration) }}</span>
              </div>
            </div>
            
            <div class="model-status">
              <el-tag :type="getStatusTagType(task.status)" size="small">
                {{ getStatusText(task.status) }}
              </el-tag>
              <span class="created-date">{{ formatDate(task.createdAt) }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 详细对比表格 -->
      <div class="detailed-comparison">
        <h4>详细对比</h4>
        <el-table :data="comparisonData" border>
          <el-table-column prop="metric" label="指标" width="150" fixed="left">
            <template #default="{ row }">
              <strong>{{ row.metric }}</strong>
            </template>
          </el-table-column>
          
          <el-table-column 
            v-for="task in tasks" 
            :key="task.id"
            :label="task.name"
            min-width="150"
            align="center"
          >
            <template #header>
              <div class="table-header">
                <span class="model-name">{{ truncateName(task.name) }}</span>
                <el-tag :type="getModelTagType(task.modelType)" size="small">
                  {{ task.modelType }}
                </el-tag>
              </div>
            </template>
            
            <template #default="{ row }">
              <div class="metric-cell">
                <span 
                  :class="['metric-value', getBestValueClass(row.metric, row.values[task.id], row.bestValue)]"
                >
                  {{ formatComparisonValue(row.values[task.id], row.format) }}
                </span>
                <div v-if="row.values[task.id] === row.bestValue" class="best-indicator">
                  <el-icon><Crown /></el-icon>
                </div>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- 可视化对比 -->
      <div class="visual-comparison">
        <el-tabs v-model="activeComparisonTab">
          <el-tab-pane label="性能雷达图" name="radar">
            <div class="chart-container">
              <div ref="radarChart" class="radar-chart"></div>
              <div class="chart-description">
                <p>雷达图展示了各模型在不同维度的综合表现</p>
                <div class="legend">
                  <div 
                    v-for="(task, index) in tasks" 
                    :key="task.id"
                    class="legend-item"
                  >
                    <div :class="['legend-color', `color-${index}`]"></div>
                    <span>{{ task.name }}</span>
                  </div>
                </div>
              </div>
            </div>
          </el-tab-pane>
          
          <el-tab-pane label="性能对比柱状图" name="bar">
            <div class="chart-container">
              <div ref="barChart" class="bar-chart"></div>
              <div class="chart-controls">
                <el-select v-model="selectedMetricForChart" style="width: 200px">
                  <el-option label="准确率" value="accuracy" />
                  <el-option label="F1分数" value="f1Score" />
                  <el-option label="精确率" value="precision" />
                  <el-option label="召回率" value="recall" />
                  <el-option label="训练时间" value="trainingTime" />
                </el-select>
              </div>
            </div>
          </el-tab-pane>
          
          <el-tab-pane label="训练曲线对比" name="curves">
            <div class="chart-container">
              <div ref="curvesChart" class="curves-chart"></div>
              <div class="chart-description">
                <p>展示各模型的训练损失和验证准确率变化曲线</p>
              </div>
            </div>
          </el-tab-pane>
          
          <el-tab-pane label="特征重要性对比" name="features">
            <div class="chart-container">
              <div ref="featuresChart" class="features-chart"></div>
              <div class="chart-description">
                <p>对比各模型中特征的重要性排序</p>
              </div>
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>

      <!-- 对比结论 -->
      <div class="comparison-conclusion">
        <h4>对比结论</h4>
        <el-card class="conclusion-card">
          <div class="conclusion-content">
            <div class="winner-announcement">
              <div class="winner-icon">
                <el-icon><Trophy /></el-icon>
              </div>
              <div class="winner-info">
                <h3>综合表现最佳：{{ bestModel?.name }}</h3>
                <p>{{ getWinnerDescription() }}</p>
              </div>
            </div>
            
            <div class="detailed-analysis">
              <el-row :gutter="24">
                <el-col :span="8">
                  <div class="analysis-item">
                    <h5>准确性分析</h5>
                    <p>{{ getAccuracyAnalysis() }}</p>
                  </div>
                </el-col>
                <el-col :span="8">
                  <div class="analysis-item">
                    <h5>效率分析</h5>
                    <p>{{ getEfficiencyAnalysis() }}</p>
                  </div>
                </el-col>
                <el-col :span="8">
                  <div class="analysis-item">
                    <h5>建议</h5>
                    <p>{{ getRecommendation() }}</p>
                  </div>
                </el-col>
              </el-row>
            </div>
            
            <div class="strengths-weaknesses">
              <el-table :data="modelStrengthsWeaknesses" size="small">
                <el-table-column prop="modelName" label="模型" width="200" />
                <el-table-column prop="strengths" label="优势" />
                <el-table-column prop="weaknesses" label="劣势" />
                <el-table-column prop="recommendation" label="适用场景" width="200" />
              </el-table>
            </div>
          </div>
        </el-card>
      </div>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import {
  DataAnalysis, Download, Delete, Close, Crown, Trophy
} from '@element-plus/icons-vue'
import type { TrainingTask } from '@/types/training'

interface Props {
  tasks: TrainingTask[]
}

const props = defineProps<Props>()
const emit = defineEmits(['remove-task'])

// 响应式数据
const activeComparisonTab = ref('radar')
const selectedMetricForChart = ref('accuracy')

// 图表DOM引用
const radarChart = ref<HTMLElement>()
const barChart = ref<HTMLElement>()
const curvesChart = ref<HTMLElement>()
const featuresChart = ref<HTMLElement>()

// 计算属性
const comparisonData = computed(() => {
  if (props.tasks.length === 0) return []
  
  const metrics = [
    { key: 'accuracy', label: '准确率', format: 'percentage', higherBetter: true },
    { key: 'f1Score', label: 'F1分数', format: 'decimal', higherBetter: true },
    { key: 'precision', label: '精确率', format: 'percentage', higherBetter: true },
    { key: 'recall', label: '召回率', format: 'percentage', higherBetter: true },
    { key: 'trainingTime', label: '训练时间', format: 'duration', higherBetter: false },
    { key: 'progress', label: '训练进度', format: 'percentage', higherBetter: true }
  ]
  
  return metrics.map(metric => {
    const values: Record<string, any> = {}
    const allValues: number[] = []
    
    props.tasks.forEach(task => {
      let value: any
      switch (metric.key) {
        case 'accuracy':
        case 'f1Score':
        case 'precision':
        case 'recall':
          value = task.bestMetrics?.[metric.key as keyof typeof task.bestMetrics] || 0
          break
        case 'trainingTime':
          value = task.duration
          break
        case 'progress':
          value = task.progress
          break
        default:
          value = 0
      }
      
      values[task.id] = value
      if (typeof value === 'number') {
        allValues.push(value)
      }
    })
    
    // 找出最佳值
    const bestValue = metric.higherBetter 
      ? Math.max(...allValues)
      : Math.min(...allValues)
    
    return {
      metric: metric.label,
      values,
      bestValue,
      format: metric.format
    }
  })
})

const bestModel = computed(() => {
  if (props.tasks.length === 0) return null
  
  // 综合评分算法：准确率 * 0.4 + F1 * 0.3 + (1 - 归一化训练时间) * 0.3
  const maxTrainingTime = Math.max(...props.tasks.map(t => t.duration))
  
  const scoredTasks = props.tasks.map(task => {
    const accuracy = task.bestMetrics?.accuracy || 0
    const f1Score = (task.bestMetrics?.f1Score || 0) * 100 // 转换为百分比
    const normalizedTime = task.duration / maxTrainingTime
    const timeScore = (1 - normalizedTime) * 100
    
    const score = accuracy * 0.4 + f1Score * 0.3 + timeScore * 0.3
    
    return { task, score }
  })
  
  return scoredTasks.reduce((best, current) => 
    current.score > best.score ? current : best
  ).task
})

const modelStrengthsWeaknesses = computed(() => {
  return props.tasks.map(task => {
    const accuracy = task.bestMetrics?.accuracy || 0
    const f1Score = task.bestMetrics?.f1Score || 0
    const trainingTime = task.duration
    
    let strengths = []
    let weaknesses = []
    let recommendation = ''
    
    if (accuracy > 85) {
      strengths.push('高准确率')
    } else if (accuracy < 75) {
      weaknesses.push('准确率较低')
    }
    
    if (f1Score > 0.85) {
      strengths.push('良好的综合性能')
    } else if (f1Score < 0.75) {
      weaknesses.push('F1分数偏低')
    }
    
    if (trainingTime < 1800) { // 30分钟
      strengths.push('训练速度快')
    } else if (trainingTime > 7200) { // 2小时
      weaknesses.push('训练耗时较长')
    }
    
    // 根据模型类型给出建议
    switch (task.modelType) {
      case 'LightGBM':
        recommendation = '适合快速迭代和中等规模数据集'
        break
      case 'XGBoost':
        recommendation = '适合需要高精度的生产环境'
        break
      case 'LSTM':
        recommendation = '适合时间序列预测任务'
        break
      case 'Transformer':
        recommendation = '适合复杂的多变量时序建模'
        break
      default:
        recommendation = '通用机器学习任务'
    }
    
    return {
      modelName: task.name,
      strengths: strengths.join('、') || '无明显优势',
      weaknesses: weaknesses.join('、') || '无明显劣势',
      recommendation
    }
  })
})

// 方法
const getModelTagType = (modelType: string) => {
  switch (modelType) {
    case 'LightGBM': return 'success'
    case 'XGBoost': return 'warning'
    case 'LSTM': return 'info'
    case 'Transformer': return 'danger'
    default: return 'info'
  }
}

const getStatusTagType = (status: string) => {
  switch (status) {
    case 'completed': return 'success'
    case 'running': return 'warning'
    case 'failed': return 'danger'
    default: return 'info'
  }
}

const getStatusText = (status: string) => {
  switch (status) {
    case 'completed': return '已完成'
    case 'running': return '训练中'
    case 'failed': return '失败'
    case 'paused': return '暂停'
    default: return '未知'
  }
}

const formatMetric = (value: any, type: string) => {
  if (value === undefined || value === null) return '--'
  
  switch (type) {
    case 'percentage':
      return `${value.toFixed(1)}%`
    case 'decimal':
      return value.toFixed(3)
    default:
      return value.toString()
  }
}

const formatComparisonValue = (value: any, format: string) => {
  if (value === undefined || value === null) return '--'
  
  switch (format) {
    case 'percentage':
      return `${value.toFixed(1)}%`
    case 'decimal':
      return value.toFixed(3)
    case 'duration':
      return formatDuration(value)
    default:
      return value.toString()
  }
}

const formatDuration = (seconds: number) => {
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  
  if (hours > 0) {
    return `${hours}h${minutes}m`
  }
  return `${minutes}m`
}

const formatDate = (date: Date) => {
  return date.toLocaleDateString('zh-CN')
}

const truncateName = (name: string) => {
  return name.length > 15 ? name.substring(0, 15) + '...' : name
}

const getBestValueClass = (metric: string, value: any, bestValue: any) => {
  if (value === bestValue) {
    return 'best-value'
  }
  return ''
}

const getWinnerDescription = () => {
  if (!bestModel.value) return ''
  
  const accuracy = bestModel.value.bestMetrics?.accuracy || 0
  const modelType = bestModel.value.modelType
  
  return `该模型在准确率(${accuracy.toFixed(1)}%)和综合性能方面表现最佳，${modelType}算法在当前数据集上展现出了优异的预测能力。`
}

const getAccuracyAnalysis = () => {
  const accuracies = props.tasks
    .filter(t => t.bestMetrics?.accuracy)
    .map(t => t.bestMetrics!.accuracy)
  
  if (accuracies.length === 0) return '暂无准确率数据'
  
  const maxAccuracy = Math.max(...accuracies)
  const minAccuracy = Math.min(...accuracies)
  const avgAccuracy = accuracies.reduce((sum, acc) => sum + acc, 0) / accuracies.length
  
  return `准确率范围：${minAccuracy.toFixed(1)}% - ${maxAccuracy.toFixed(1)}%，平均值：${avgAccuracy.toFixed(1)}%`
}

const getEfficiencyAnalysis = () => {
  const times = props.tasks.map(t => t.duration)
  const maxTime = Math.max(...times)
  const minTime = Math.min(...times)
  
  const fastestModel = props.tasks.find(t => t.duration === minTime)
  const slowestModel = props.tasks.find(t => t.duration === maxTime)
  
  return `最快：${fastestModel?.name}(${formatDuration(minTime)})，最慢：${slowestModel?.name}(${formatDuration(maxTime)})`
}

const getRecommendation = () => {
  if (!bestModel.value) return '请添加更多模型进行对比'
  
  const modelType = bestModel.value.modelType
  
  switch (modelType) {
    case 'LightGBM':
      return '推荐在生产环境中使用，具有良好的速度和精度平衡'
    case 'XGBoost':
      return '适合对准确性要求较高的场景'
    case 'LSTM':
      return '推荐用于时间序列预测任务'
    case 'Transformer':
      return '适合复杂的多变量建模，需要充足的计算资源'
    default:
      return '根据具体业务需求选择合适的模型'
  }
}

const exportComparison = () => {
  ElMessage.success('对比报告导出已开始')
}

const clearComparison = () => {
  props.tasks.forEach(task => {
    emit('remove-task', task.id)
  })
  ElMessage.success('已清空对比列表')
}

const initializeCharts = () => {
  // 这里可以初始化图表
  // 使用 ECharts 或其他图表库
}

// 监听器
watch(
  () => props.tasks,
  () => {
    nextTick(() => {
      initializeCharts()
    })
  },
  { deep: true }
)

watch(
  selectedMetricForChart,
  () => {
    // 重新渲染柱状图
    initializeCharts()
  }
)

// 生命周期
onMounted(() => {
  initializeCharts()
})
</script>

<style scoped>
.model-comparison {
  margin-bottom: 32px;
}

.comparison-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-content {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 16px;
  font-weight: 600;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.comparison-content {
  display: flex;
  flex-direction: column;
  gap: 32px;
}

/* 模型概览 */
.models-overview {
  display: flex;
  gap: 16px;
  overflow-x: auto;
  padding-bottom: 8px;
}

.model-overview-item {
  flex-shrink: 0;
  width: 280px;
}

.model-card {
  padding: 20px;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  background: #fff;
  transition: all 0.3s ease;
}

.model-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.model-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}

.model-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex: 1;
  margin-right: 12px;
}

.model-name {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  line-height: 1.3;
}

.model-metrics {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 16px;
}

.metric-item {
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
  color: #303133;
}

.model-status {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.created-date {
  font-size: 12px;
  color: #909399;
}

/* 详细对比表格 */
.detailed-comparison {
  background: #fff;
  border-radius: 8px;
}

.detailed-comparison h4 {
  margin: 0 0 16px 0;
  color: #303133;
}

.table-header {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.table-header .model-name {
  font-weight: 600;
  text-align: center;
  line-height: 1.2;
}

.metric-cell {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.metric-value.best-value {
  color: #67c23a;
  font-weight: bold;
}

.best-indicator {
  color: #f7ba2a;
  font-size: 16px;
}

/* 可视化对比 */
.visual-comparison {
  background: #f8f9fa;
  padding: 24px;
  border-radius: 8px;
}

.chart-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.radar-chart,
.bar-chart,
.curves-chart,
.features-chart {
  width: 100%;
  height: 400px;
  background: #fff;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #909399;
}

.chart-description {
  text-align: center;
  color: #606266;
}

.chart-description p {
  margin: 0 0 12px 0;
}

.legend {
  display: flex;
  justify-content: center;
  gap: 24px;
  flex-wrap: wrap;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.legend-color {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}

.legend-color.color-0 {
  background: #409eff;
}

.legend-color.color-1 {
  background: #67c23a;
}

.legend-color.color-2 {
  background: #e6a23c;
}

.legend-color.color-3 {
  background: #f56c6c;
}

.legend-color.color-4 {
  background: #909399;
}

.chart-controls {
  display: flex;
  justify-content: center;
}

/* 对比结论 */
.comparison-conclusion h4 {
  margin: 0 0 16px 0;
  color: #303133;
}

.conclusion-card {
  background: linear-gradient(135deg, #f0f8ff 0%, #e8f4fd 100%);
  border: 1px solid #d4e4fd;
}

.conclusion-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.winner-announcement {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  background: linear-gradient(135deg, #ffd700 0%, #ffed4e 100%);
  border-radius: 8px;
}

.winner-icon {
  font-size: 32px;
  color: #f7ba2a;
}

.winner-info h3 {
  margin: 0 0 8px 0;
  color: #333;
  font-size: 18px;
}

.winner-info p {
  margin: 0;
  color: #666;
  line-height: 1.5;
}

.detailed-analysis {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.analysis-item h5 {
  margin: 0 0 8px 0;
  color: #303133;
  font-size: 14px;
}

.analysis-item p {
  margin: 0;
  color: #606266;
  font-size: 14px;
  line-height: 1.5;
}

.strengths-weaknesses {
  margin-top: 16px;
}

@media (max-width: 768px) {
  .models-overview {
    flex-direction: column;
    gap: 16px;
  }
  
  .model-overview-item {
    width: 100%;
  }
  
  .comparison-header {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
  }
  
  .header-actions {
    justify-content: center;
  }
  
  .winner-announcement {
    flex-direction: column;
    text-align: center;
    gap: 12px;
  }
  
  .legend {
    flex-direction: column;
    align-items: center;
    gap: 8px;
  }
}
</style>