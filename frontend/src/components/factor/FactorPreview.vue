<template>
  <div class="factor-preview">
    <!-- 预览头部 -->
    <div class="preview-header">
      <h3>
        <el-icon><View /></el-icon>
        {{ factor?.name || '因子预览' }}
      </h3>
      <el-button type="text" @click="$emit('close')">
        <el-icon><Close /></el-icon>
      </el-button>
    </div>

    <div v-if="factor" class="preview-content">
      <!-- 因子基本信息 -->
      <el-card class="factor-info-card">
        <template #header>
          <span>因子信息</span>
        </template>
        
        <div class="factor-details">
          <div class="detail-row">
            <span class="label">因子名称:</span>
            <span class="value">{{ factor.name }}</span>
          </div>
          
          <div class="detail-row">
            <span class="label">因子类型:</span>
            <el-tag :type="getCategoryTagType(factor.category)">
              {{ getCategoryName(factor.category) }}
            </el-tag>
          </div>
          
          <div class="detail-row">
            <span class="label">表达式:</span>
            <code class="expression-code">{{ factor.expression }}</code>
          </div>
          
          <div class="detail-row">
            <span class="label">描述:</span>
            <span class="value">{{ factor.description }}</span>
          </div>
          
          <div class="detail-row">
            <span class="label">创建者:</span>
            <span class="value">{{ factor.createdBy }}</span>
          </div>
          
          <div class="detail-row">
            <span class="label">创建时间:</span>
            <span class="value">{{ formatDate(factor.createdAt) }}</span>
          </div>
        </div>
      </el-card>

      <!-- 历史表现预览 -->
      <el-card v-if="previewData" class="performance-card">
        <template #header>
          <div class="performance-header">
            <span>历史表现预览</span>
            <el-button 
              type="primary" 
              size="small" 
              @click="refreshPreview"
              :loading="loading"
            >
              <el-icon><Refresh /></el-icon>
              刷新数据
            </el-button>
          </div>
        </template>
        
        <!-- 关键指标 -->
        <div class="metrics-summary">
          <div class="metric-card">
            <div class="metric-icon">📈</div>
            <div class="metric-content">
              <div class="metric-value">{{ previewData.ic?.toFixed(4) }}</div>
              <div class="metric-label">信息系数(IC)</div>
            </div>
          </div>
          
          <div class="metric-card">
            <div class="metric-icon">📊</div>
            <div class="metric-content">
              <div class="metric-value">{{ previewData.ir?.toFixed(3) }}</div>
              <div class="metric-label">信息比率(IR)</div>
            </div>
          </div>
          
          <div class="metric-card">
            <div class="metric-icon">🎯</div>
            <div class="metric-content">
              <div class="metric-value">{{ previewData.winRate?.toFixed(1) }}%</div>
              <div class="metric-label">胜率</div>
            </div>
          </div>
          
          <div class="metric-card">
            <div class="metric-icon">📉</div>
            <div class="metric-content">
              <div class="metric-value">{{ previewData.maxDrawdown?.toFixed(1) }}%</div>
              <div class="metric-label">最大回撤</div>
            </div>
          </div>
        </div>

        <!-- IC时序图 -->
        <div class="chart-section">
          <h4>IC时序表现</h4>
          <div class="chart-container">
            <canvas ref="icChartRef" height="200"></canvas>
          </div>
        </div>

        <!-- 分布统计 -->
        <div class="distribution-section">
          <h4>因子值分布</h4>
          <div class="distribution-stats">
            <div class="stat-item">
              <span class="stat-label">均值:</span>
              <span class="stat-value">{{ previewData.distribution?.mean?.toFixed(4) }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">标准差:</span>
              <span class="stat-value">{{ previewData.distribution?.std?.toFixed(4) }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">偏度:</span>
              <span class="stat-value">{{ previewData.distribution?.skew?.toFixed(4) }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">峰度:</span>
              <span class="stat-value">{{ previewData.distribution?.kurtosis?.toFixed(4) }}</span>
            </div>
          </div>
          
          <div class="chart-container">
            <canvas ref="distributionChartRef" height="150"></canvas>
          </div>
        </div>
      </el-card>

      <!-- 风险提示 -->
      <el-card v-if="riskWarnings.length > 0" class="risk-card">
        <template #header>
          <span>风险提示</span>
        </template>
        
        <div class="risk-warnings">
          <el-alert
            v-for="(warning, index) in riskWarnings"
            :key="index"
            :title="warning.title"
            :description="warning.description"
            :type="warning.type"
            show-icon
            :closable="false"
            class="risk-alert"
          />
        </div>
      </el-card>

      <!-- 优化建议 -->
      <el-card v-if="optimizationSuggestions.length > 0" class="suggestions-card">
        <template #header>
          <span>优化建议</span>
        </template>
        
        <div class="suggestions-list">
          <div 
            v-for="(suggestion, index) in optimizationSuggestions"
            :key="index"
            class="suggestion-item"
          >
            <div class="suggestion-icon">💡</div>
            <div class="suggestion-content">
              <h5>{{ suggestion.title }}</h5>
              <p>{{ suggestion.description }}</p>
              <div v-if="suggestion.code" class="suggestion-code">
                <strong>改进表达式:</strong>
                <code>{{ suggestion.code }}</code>
              </div>
            </div>
          </div>
        </div>
      </el-card>

      <!-- 操作按钮 -->
      <div class="preview-actions">
        <el-button @click="$emit('close')">关闭预览</el-button>
        <el-button type="info" @click="editFactor">
          <el-icon><Edit /></el-icon>
          编辑因子
        </el-button>
        <el-button type="success" @click="saveFactor">
          <el-icon><Check /></el-icon>
          保存到库
        </el-button>
        <el-button type="primary" @click="useForTraining">
          <el-icon><Cpu /></el-icon>
          用于训练
        </el-button>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-else-if="loading" class="loading-state">
      <el-skeleton :rows="8" animated />
    </div>

    <!-- 空状态 -->
    <div v-else class="empty-state">
      <el-empty description="请选择要预览的因子" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { View, Close, Refresh, Edit, Check, Cpu } from '@element-plus/icons-vue'
import type { FactorDefinition } from '@/types/factor'

// Props
const props = defineProps<{
  factor?: FactorDefinition | null
}>()

// 事件定义
const emit = defineEmits<{
  close: []
  edit: [factor: FactorDefinition]
  save: [factor: FactorDefinition]
  useForTraining: [factor: FactorDefinition]
}>()

// 响应式数据
const loading = ref(false)
const icChartRef = ref<HTMLCanvasElement>()
const distributionChartRef = ref<HTMLCanvasElement>()

interface PreviewData {
  ic: number
  ir: number
  winRate: number
  maxDrawdown: number
  distribution: {
    mean: number
    std: number
    skew: number
    kurtosis: number
  }
  icTimeSeries: Array<{ date: string; ic: number }>
  distributionData: number[]
}

const previewData = ref<PreviewData | null>(null)

const riskWarnings = ref<Array<{
  title: string
  description: string
  type: 'warning' | 'error' | 'info'
}>>([])

const optimizationSuggestions = ref<Array<{
  title: string
  description: string
  code?: string
}>>([])

// 方法
const getCategoryName = (category: string) => {
  const names: Record<string, string> = {
    technical: '技术指标',
    fundamental: '基本面',
    sentiment: '情绪指标',
    composite: '组合因子',
    other: '其他'
  }
  return names[category] || category
}

const getCategoryTagType = (category: string) => {
  const types: Record<string, string> = {
    technical: 'primary',
    fundamental: 'success',
    sentiment: 'warning',
    composite: 'info',
    other: 'default'
  }
  return types[category] || 'default'
}

const formatDate = (date: Date) => {
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const loadPreviewData = async () => {
  if (!props.factor) return

  loading.value = true
  
  try {
    // 模拟加载预览数据
    await new Promise(resolve => setTimeout(resolve, 1500))
    
    // 生成模拟数据
    previewData.value = generateMockPreviewData(props.factor)
    
    // 生成风险提示和优化建议
    generateRiskWarnings(props.factor)
    generateOptimizationSuggestions(props.factor)
    
    // 渲染图表
    await renderCharts()
    
  } catch (error) {
    ElMessage.error('加载预览数据失败')
  } finally {
    loading.value = false
  }
}

const generateMockPreviewData = (factor: FactorDefinition): PreviewData => {
  // 根据因子类型生成不同的模拟数据
  const baseIC = Math.random() * 0.08 - 0.02 // -0.02 to 0.06
  const baseIR = Math.abs(baseIC) * (5 + Math.random() * 10) // 0.1 to 0.8
  
  // 生成IC时序数据
  const icTimeSeries = []
  for (let i = 0; i < 252; i++) {
    const date = new Date()
    date.setDate(date.getDate() - (252 - i))
    icTimeSeries.push({
      date: date.toISOString().split('T')[0],
      ic: baseIC + (Math.random() - 0.5) * 0.1
    })
  }
  
  // 生成分布数据
  const distributionData = []
  for (let i = 0; i < 1000; i++) {
    distributionData.push(Math.random() * 4 - 2) // -2 to 2
  }
  
  return {
    ic: baseIC,
    ir: baseIR,
    winRate: 45 + Math.random() * 20, // 45% to 65%
    maxDrawdown: -Math.random() * 20, // 0% to -20%
    distribution: {
      mean: 0.02,
      std: 1.25,
      skew: 0.15,
      kurtosis: 2.8
    },
    icTimeSeries,
    distributionData
  }
}

const generateRiskWarnings = (factor: FactorDefinition) => {
  riskWarnings.value = []
  
  if (factor.expression.includes('volume')) {
    riskWarnings.value.push({
      title: '流动性风险',
      description: '基于成交量的因子可能在市场极端情况下失效，建议结合其他因子使用',
      type: 'warning'
    })
  }
  
  if (factor.expression.includes('pe_ttm') || factor.expression.includes('pb')) {
    riskWarnings.value.push({
      title: '估值因子局限性',
      description: '估值因子在成长股集中的市场环境下可能表现不佳',
      type: 'info'
    })
  }
  
  if (previewData.value && previewData.value.ic < 0.01) {
    riskWarnings.value.push({
      title: '因子有效性较低',
      description: 'IC值较低，建议进一步优化或与其他因子组合使用',
      type: 'error'
    })
  }
}

const generateOptimizationSuggestions = (factor: FactorDefinition) => {
  optimizationSuggestions.value = []
  
  optimizationSuggestions.value.push({
    title: '行业中性化',
    description: '对因子进行行业中性化处理，可以减少行业偏差的影响',
    code: `demean(${factor.expression}, industry)`
  })
  
  optimizationSuggestions.value.push({
    title: '市值调整',
    description: '考虑添加市值因子进行调整，提高因子在不同市值股票上的稳定性',
    code: `${factor.expression} - 0.2 * log($market_cap)`
  })
  
  if (factor.category === 'technical') {
    optimizationSuggestions.value.push({
      title: '波动率标准化',
      description: '对技术指标进行波动率标准化，提高跨时间的稳定性',
      code: `(${factor.expression}) / Std(${factor.expression}, 252)`
    })
  }
}

const renderCharts = async () => {
  // 这里应该使用实际的图表库如ECharts或Chart.js
  // 简化实现，只是占位符
  
  if (icChartRef.value && previewData.value) {
    const ctx = icChartRef.value.getContext('2d')
    if (ctx) {
      // 绘制简单的IC时序图
      ctx.clearRect(0, 0, icChartRef.value.width, icChartRef.value.height)
      ctx.strokeStyle = '#409eff'
      ctx.lineWidth = 2
      ctx.beginPath()
      
      const data = previewData.value.icTimeSeries
      const width = icChartRef.value.width
      const height = icChartRef.value.height
      
      data.forEach((point, index) => {
        const x = (index / (data.length - 1)) * width
        const y = height / 2 - (point.ic * height * 5)
        
        if (index === 0) {
          ctx.moveTo(x, y)
        } else {
          ctx.lineTo(x, y)
        }
      })
      
      ctx.stroke()
    }
  }
  
  if (distributionChartRef.value && previewData.value) {
    const ctx = distributionChartRef.value.getContext('2d')
    if (ctx) {
      // 绘制简单的分布直方图
      ctx.clearRect(0, 0, distributionChartRef.value.width, distributionChartRef.value.height)
      ctx.fillStyle = '#67c23a'
      
      const width = distributionChartRef.value.width
      const height = distributionChartRef.value.height
      const barWidth = width / 20
      
      for (let i = 0; i < 20; i++) {
        const barHeight = Math.random() * height * 0.8
        ctx.fillRect(i * barWidth, height - barHeight, barWidth - 2, barHeight)
      }
    }
  }
}

const refreshPreview = () => {
  loadPreviewData()
}

const editFactor = () => {
  if (props.factor) {
    emit('edit', props.factor)
  }
}

const saveFactor = () => {
  if (props.factor) {
    emit('save', props.factor)
    ElMessage.success('因子已保存到因子库')
  }
}

const useForTraining = () => {
  if (props.factor) {
    emit('useForTraining', props.factor)
    ElMessage.success('因子已添加到训练配置')
  }
}

// 监听器
watch(() => props.factor, (newFactor) => {
  if (newFactor) {
    loadPreviewData()
  } else {
    previewData.value = null
    riskWarnings.value = []
    optimizationSuggestions.value = []
  }
}, { immediate: true })

// 生命周期
onMounted(() => {
  if (props.factor) {
    loadPreviewData()
  }
})
</script>

<style scoped>
.factor-preview {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 16px;
  border-bottom: 1px solid #e4e7ed;
  margin-bottom: 24px;
}

.preview-header h3 {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0;
  color: #303133;
}

.preview-content {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.factor-details {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.detail-row {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.label {
  min-width: 80px;
  font-weight: 500;
  color: #606266;
}

.value {
  color: #303133;
  flex: 1;
}

.expression-code {
  background: #f5f7fa;
  padding: 4px 8px;
  border-radius: 4px;
  font-family: 'Monaco', 'Consolas', monospace;
  color: #e6a23c;
  font-size: 13px;
  word-break: break-all;
  flex: 1;
}

.performance-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.metrics-summary {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.metric-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: #fafafa;
  border-radius: 8px;
}

.metric-icon {
  font-size: 24px;
}

.metric-content {
  flex: 1;
}

.metric-value {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.metric-label {
  font-size: 12px;
  color: #606266;
  margin-top: 2px;
}

.chart-section h4,
.distribution-section h4 {
  margin: 0 0 16px 0;
  color: #303133;
  font-size: 14px;
}

.chart-container {
  background: #fafafa;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
}

.distribution-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
  gap: 16px;
  margin-bottom: 16px;
}

.stat-item {
  text-align: center;
}

.stat-label {
  display: block;
  font-size: 12px;
  color: #606266;
  margin-bottom: 4px;
}

.stat-value {
  font-weight: 500;
  color: #303133;
}

.risk-warnings {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.risk-alert {
  margin-bottom: 0;
}

.suggestions-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.suggestion-item {
  display: flex;
  gap: 12px;
  padding: 16px;
  background: #fafafa;
  border-radius: 8px;
}

.suggestion-icon {
  font-size: 20px;
  margin-top: 2px;
}

.suggestion-content {
  flex: 1;
}

.suggestion-content h5 {
  margin: 0 0 8px 0;
  color: #303133;
  font-size: 14px;
}

.suggestion-content p {
  margin: 0 0 8px 0;
  color: #606266;
  font-size: 13px;
  line-height: 1.5;
}

.suggestion-code {
  margin-top: 8px;
}

.suggestion-code strong {
  color: #303133;
  font-size: 12px;
}

.suggestion-code code {
  display: block;
  background: white;
  padding: 8px;
  border-radius: 4px;
  font-family: 'Monaco', 'Consolas', monospace;
  color: #e6a23c;
  font-size: 12px;
  margin-top: 4px;
}

.preview-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding-top: 16px;
  border-top: 1px solid #e4e7ed;
  margin-top: auto;
}

.loading-state,
.empty-state {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 300px;
}

@media (max-width: 768px) {
  .metrics-summary {
    grid-template-columns: 1fr;
  }
  
  .distribution-stats {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .preview-actions {
    flex-direction: column;
    gap: 8px;
  }
  
  .detail-row {
    flex-direction: column;
    gap: 4px;
  }
  
  .label {
    min-width: auto;
  }
}
</style>