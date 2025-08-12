<template>
  <div class="training-task-detail">
    <el-tabs v-model="activeTab" type="card">
      <!-- 基本信息 -->
      <el-tab-pane label="基本信息" name="basic">
        <div class="basic-info">
          <el-row :gutter="24">
            <el-col :span="12">
              <el-descriptions title="任务信息" :column="1" border>
                <el-descriptions-item label="任务名称">
                  {{ task.name }}
                </el-descriptions-item>
                <el-descriptions-item label="模型类型">
                  <el-tag :type="getModelTagType(task.modelType)" size="small">
                    {{ task.modelType }}
                  </el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="任务状态">
                  <el-tag :type="getStatusTagType(task.status)" size="small">
                    {{ getStatusText(task.status) }}
                  </el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="训练进度">
                  <el-progress :percentage="task.progress" :status="getProgressStatus(task.status)" />
                </el-descriptions-item>
                <el-descriptions-item label="创建时间">
                  {{ formatDateTime(task.createdAt) }}
                </el-descriptions-item>
                <el-descriptions-item label="训练时长">
                  {{ formatDuration(task.duration) }}
                </el-descriptions-item>
              </el-descriptions>
            </el-col>
            
            <el-col :span="12">
              <el-descriptions title="性能指标" :column="1" border>
                <el-descriptions-item label="准确率">
                  <span v-if="task.bestMetrics?.accuracy" class="metric-value success">
                    {{ task.bestMetrics.accuracy.toFixed(2) }}%
                  </span>
                  <span v-else class="no-data">--</span>
                </el-descriptions-item>
                <el-descriptions-item label="F1分数">
                  <span v-if="task.bestMetrics?.f1Score" class="metric-value info">
                    {{ task.bestMetrics.f1Score.toFixed(3) }}
                  </span>
                  <span v-else class="no-data">--</span>
                </el-descriptions-item>
                <el-descriptions-item label="精确率">
                  <span v-if="task.bestMetrics?.precision" class="metric-value warning">
                    {{ task.bestMetrics.precision.toFixed(2) }}%
                  </span>
                  <span v-else class="no-data">--</span>
                </el-descriptions-item>
                <el-descriptions-item label="召回率">
                  <span v-if="task.bestMetrics?.recall" class="metric-value primary">
                    {{ task.bestMetrics.recall.toFixed(2) }}%
                  </span>
                  <span v-else class="no-data">--</span>
                </el-descriptions-item>
                <el-descriptions-item label="AUC">
                  <span v-if="task.bestMetrics?.auc" class="metric-value success">
                    {{ task.bestMetrics.auc.toFixed(3) }}
                  </span>
                  <span v-else class="no-data">--</span>
                </el-descriptions-item>
              </el-descriptions>
            </el-col>
          </el-row>
        </div>
      </el-tab-pane>

      <!-- 配置详情 -->
      <el-tab-pane label="配置详情" name="config">
        <div class="config-detail">
          <el-collapse v-model="activeConfigs">
            <el-collapse-item title="数据配置" name="data">
              <el-descriptions :column="2" border>
                <el-descriptions-item label="股票池">
                  {{ task.config.dataConfig.stockPool }}
                </el-descriptions-item>
                <el-descriptions-item label="数据频率">
                  {{ getFrequencyText(task.config.dataConfig.frequency) }}
                </el-descriptions-item>
                <el-descriptions-item label="时间范围" span="2">
                  {{ task.config.dataConfig.dateRange[0] }} 至 {{ task.config.dataConfig.dateRange[1] }}
                </el-descriptions-item>
              </el-descriptions>
            </el-collapse-item>
            
            <el-collapse-item title="模型配置" name="model">
              <div class="model-config">
                <h4>{{ task.config.modelConfig.type }} 参数配置</h4>
                <el-table :data="modelParamsTable" size="small">
                  <el-table-column prop="parameter" label="参数名" width="200" />
                  <el-table-column prop="value" label="参数值" />
                  <el-table-column prop="description" label="说明" />
                </el-table>
              </div>
            </el-collapse-item>
            
            <el-collapse-item title="训练配置" name="training">
              <el-descriptions :column="2" border>
                <el-descriptions-item label="训练轮数">
                  {{ task.config.trainingParams.epochs }}
                </el-descriptions-item>
                <el-descriptions-item label="批次大小">
                  {{ task.config.trainingParams.batchSize }}
                </el-descriptions-item>
                <el-descriptions-item label="学习率">
                  {{ task.config.trainingParams.learningRate }}
                </el-descriptions-item>
                <el-descriptions-item label="验证集比例">
                  {{ (task.config.trainingParams.validationSplit * 100).toFixed(0) }}%
                </el-descriptions-item>
                <el-descriptions-item label="早停耐心值">
                  {{ task.config.trainingParams.earlyStoppingPatience }}
                </el-descriptions-item>
                <el-descriptions-item label="保存最佳模型">
                  {{ task.config.trainingParams.saveBestModel ? '是' : '否' }}
                </el-descriptions-item>
              </el-descriptions>
            </el-collapse-item>
            
            <el-collapse-item title="因子信息" name="factors">
              <div class="factors-info">
                <div class="factors-summary">
                  <el-statistic title="因子总数" :value="task.factors.length" />
                  <div class="factor-categories">
                    <el-tag v-for="category in factorCategories" :key="category.name" class="category-tag">
                      {{ category.name }}: {{ category.count }}
                    </el-tag>
                  </div>
                </div>
                
                <el-table :data="task.factors" size="small" max-height="300">
                  <el-table-column prop="name" label="因子名称" width="200" />
                  <el-table-column prop="category" label="类别" width="120">
                    <template #default="{ row }">
                      <el-tag size="small" :type="getCategoryTagType(row.category)">
                        {{ getCategoryText(row.category) }}
                      </el-tag>
                    </template>
                  </el-table-column>
                  <el-table-column prop="description" label="描述" />
                  <el-table-column prop="createdBy" label="创建者" width="120" />
                </el-table>
              </div>
            </el-collapse-item>
          </el-collapse>
        </div>
      </el-tab-pane>

      <!-- 训练历史 -->
      <el-tab-pane label="训练历史" name="history">
        <div class="training-history">
          <div class="history-charts">
            <el-row :gutter="24">
              <el-col :span="12">
                <el-card class="chart-card">
                  <template #header>
                    <span>损失曲线</span>
                  </template>
                  <div ref="lossChart" class="chart-container"></div>
                </el-card>
              </el-col>
              
              <el-col :span="12">
                <el-card class="chart-card">
                  <template #header>
                    <span>准确率曲线</span>
                  </template>
                  <div ref="accChart" class="chart-container"></div>
                </el-card>
              </el-col>
            </el-row>
            
            <el-row :gutter="24" style="margin-top: 24px;" v-if="isDeepLearningModel">
              <el-col :span="12">
                <el-card class="chart-card">
                  <template #header>
                    <span>学习率变化</span>
                  </template>
                  <div ref="lrChart" class="chart-container"></div>
                </el-card>
              </el-col>
              
              <el-col :span="12">
                <el-card class="chart-card">
                  <template #header>
                    <span>梯度范数</span>
                  </template>
                  <div ref="gradChart" class="chart-container"></div>
                </el-card>
              </el-col>
            </el-row>
          </div>
          
          <div class="history-table">
            <h4>训练历史记录</h4>
            <el-table :data="trainingHistory" size="small" max-height="400">
              <el-table-column prop="epoch" label="轮次" width="80" />
              <el-table-column prop="trainLoss" label="训练损失" width="120">
                <template #default="{ row }">
                  {{ row.trainLoss.toFixed(4) }}
                </template>
              </el-table-column>
              <el-table-column prop="valLoss" label="验证损失" width="120">
                <template #default="{ row }">
                  {{ row.valLoss.toFixed(4) }}
                </template>
              </el-table-column>
              <el-table-column prop="trainAcc" label="训练准确率" width="120">
                <template #default="{ row }">
                  {{ row.trainAcc.toFixed(2) }}%
                </template>
              </el-table-column>
              <el-table-column prop="valAcc" label="验证准确率" width="120">
                <template #default="{ row }">
                  {{ row.valAcc.toFixed(2) }}%
                </template>
              </el-table-column>
              <el-table-column prop="duration" label="耗时" width="100">
                <template #default="{ row }">
                  {{ row.duration }}s
                </template>
              </el-table-column>
              <el-table-column prop="timestamp" label="时间" width="160">
                <template #default="{ row }">
                  {{ formatDateTime(row.timestamp) }}
                </template>
              </el-table-column>
            </el-table>
          </div>
        </div>
      </el-tab-pane>

      <!-- 特征分析 -->
      <el-tab-pane label="特征分析" name="features">
        <div class="feature-analysis">
          <el-card class="feature-importance-card">
            <template #header>
              <div class="feature-header">
                <span>特征重要性</span>
                <el-select v-model="featureImportanceType" size="small" style="width: 150px">
                  <el-option label="基于增益" value="gain" />
                  <el-option label="基于分割" value="split" />
                  <el-option label="基于SHAP" value="shap" />
                </el-select>
              </div>
            </template>
            <div ref="featureImportanceChart" class="chart-container large"></div>
          </el-card>
          
          <el-card class="feature-correlation-card">
            <template #header>
              <span>特征相关性矩阵</span>
            </template>
            <div ref="correlationChart" class="chart-container large"></div>
          </el-card>
          
          <div class="feature-stats">
            <h4>特征统计信息</h4>
            <el-table :data="featureStats" size="small">
              <el-table-column prop="feature" label="特征名称" width="200" />
              <el-table-column prop="importance" label="重要性" width="120">
                <template #default="{ row }">
                  <el-progress 
                    :percentage="row.importance * 100" 
                    :show-text="false"
                    :stroke-width="6"
                  />
                  <span style="margin-left: 8px;">{{ (row.importance * 100).toFixed(1) }}%</span>
                </template>
              </el-table-column>
              <el-table-column prop="correlation" label="与目标相关性" width="150">
                <template #default="{ row }">
                  <span :class="getCorrelationClass(row.correlation)">
                    {{ row.correlation.toFixed(3) }}
                  </span>
                </template>
              </el-table-column>
              <el-table-column prop="dataType" label="数据类型" width="120" />
              <el-table-column prop="nullCount" label="缺失值数量" width="120" />
              <el-table-column prop="uniqueCount" label="唯一值数量" width="120" />
            </el-table>
          </div>
        </div>
      </el-tab-pane>

      <!-- 性能分析 -->
      <el-tab-pane label="性能分析" name="performance">
        <div class="performance-analysis">
          <div class="performance-overview">
            <el-row :gutter="24">
              <el-col :span="6">
                <el-card class="metric-card">
                  <el-statistic 
                    title="最终准确率" 
                    :value="task.bestMetrics?.accuracy || 0" 
                    :precision="2"
                    suffix="%"
                  >
                    <template #suffix>
                      <span>%</span>
                      <el-icon class="metric-trend positive"><CaretTop /></el-icon>
                    </template>
                  </el-statistic>
                </el-card>
              </el-col>
              
              <el-col :span="6">
                <el-card class="metric-card">
                  <el-statistic 
                    title="F1分数" 
                    :value="task.bestMetrics?.f1Score || 0" 
                    :precision="3"
                  >
                    <template #suffix>
                      <el-icon class="metric-trend positive"><CaretTop /></el-icon>
                    </template>
                  </el-statistic>
                </el-card>
              </el-col>
              
              <el-col :span="6">
                <el-card class="metric-card">
                  <el-statistic 
                    title="训练效率" 
                    :value="trainingEfficiency" 
                    :precision="1"
                    suffix="分钟/轮"
                  >
                    <template #suffix>
                      <span>分钟/轮</span>
                      <el-icon class="metric-trend negative"><CaretBottom /></el-icon>
                    </template>
                  </el-statistic>
                </el-card>
              </el-col>
              
              <el-col :span="6">
                <el-card class="metric-card">
                  <el-statistic 
                    title="收敛轮次" 
                    :value="convergenceEpoch" 
                  >
                    <template #suffix>
                      <span>/{{ task.config.trainingParams.epochs }}</span>
                    </template>
                  </el-statistic>
                </el-card>
              </el-col>
            </el-row>
          </div>
          
          <div class="confusion-matrix">
            <el-card class="matrix-card">
              <template #header>
                <span>混淆矩阵</span>
              </template>
              <div ref="confusionMatrixChart" class="chart-container"></div>
            </el-card>
          </div>
          
          <div class="roc-curve">
            <el-card class="roc-card">
              <template #header>
                <span>ROC 曲线</span>
              </template>
              <div ref="rocChart" class="chart-container"></div>
            </el-card>
          </div>
        </div>
      </el-tab-pane>

      <!-- 日志记录 -->
      <el-tab-pane label="日志记录" name="logs">
        <div class="training-logs">
          <div class="logs-header">
            <div class="log-filters">
              <el-select v-model="logLevel" size="small" style="width: 120px">
                <el-option label="全部" value="all" />
                <el-option label="信息" value="info" />
                <el-option label="警告" value="warning" />
                <el-option label="错误" value="error" />
              </el-select>
              <el-input 
                v-model="logSearch"
                placeholder="搜索日志..."
                size="small"
                style="width: 200px"
                clearable
              >
                <template #prefix>
                  <el-icon><Search /></el-icon>
                </template>
              </el-input>
            </div>
            <div class="log-actions">
              <el-button size="small" @click="refreshLogs">
                <el-icon><Refresh /></el-icon>
                刷新
              </el-button>
              <el-button size="small" @click="downloadLogs">
                <el-icon><Download /></el-icon>
                下载日志
              </el-button>
            </div>
          </div>
          
          <div class="logs-content">
            <div 
              v-for="log in filteredLogs" 
              :key="log.id"
              :class="['log-entry', `log-${log.level}`]"
            >
              <span class="log-timestamp">{{ formatDateTime(log.timestamp) }}</span>
              <span class="log-level">{{ log.level.toUpperCase() }}</span>
              <span class="log-message">{{ log.message }}</span>
            </div>
          </div>
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { CaretTop, CaretBottom, Search, Refresh, Download } from '@element-plus/icons-vue'
import type { TrainingTask } from '@/types/training'

interface Props {
  task: TrainingTask
}

const props = defineProps<Props>()
const emit = defineEmits(['task-updated'])

// 响应式数据
const activeTab = ref('basic')
const activeConfigs = ref(['data', 'model'])
const featureImportanceType = ref('gain')
const logLevel = ref('all')
const logSearch = ref('')

// 图表DOM引用
const lossChart = ref<HTMLElement>()
const accChart = ref<HTMLElement>()
const lrChart = ref<HTMLElement>()
const gradChart = ref<HTMLElement>()
const featureImportanceChart = ref<HTMLElement>()
const correlationChart = ref<HTMLElement>()
const confusionMatrixChart = ref<HTMLElement>()
const rocChart = ref<HTMLElement>()

// 模拟数据
const trainingHistory = ref([
  {
    epoch: 1,
    trainLoss: 0.8456,
    valLoss: 0.8234,
    trainAcc: 65.2,
    valAcc: 67.1,
    duration: 45,
    timestamp: new Date('2024-01-15T10:00:00')
  },
  {
    epoch: 2,
    trainLoss: 0.7123,
    valLoss: 0.7456,
    trainAcc: 72.8,
    valAcc: 71.3,
    duration: 43,
    timestamp: new Date('2024-01-15T10:01:00')
  },
  {
    epoch: 3,
    trainLoss: 0.6234,
    valLoss: 0.6789,
    trainAcc: 78.5,
    valAcc: 76.2,
    duration: 44,
    timestamp: new Date('2024-01-15T10:02:00')
  }
])

const featureStats = ref([
  {
    feature: 'RSI_14',
    importance: 0.15,
    correlation: 0.234,
    dataType: 'float',
    nullCount: 0,
    uniqueCount: 1234
  },
  {
    feature: 'MACD',
    importance: 0.12,
    correlation: -0.156,
    dataType: 'float',
    nullCount: 5,
    uniqueCount: 1189
  },
  {
    feature: 'Volume_MA20',
    importance: 0.08,
    correlation: 0.089,
    dataType: 'float',
    nullCount: 0,
    uniqueCount: 1256
  }
])

const logs = ref([
  {
    id: 1,
    timestamp: new Date('2024-01-15T10:00:00'),
    level: 'info',
    message: 'Training started with 1234 samples'
  },
  {
    id: 2,
    timestamp: new Date('2024-01-15T10:00:30'),
    level: 'info',
    message: 'Epoch 1/100 completed - Loss: 0.8456, Acc: 65.2%'
  },
  {
    id: 3,
    timestamp: new Date('2024-01-15T10:01:15'),
    level: 'warning',
    message: 'Learning rate adjusted to 0.001'
  },
  {
    id: 4,
    timestamp: new Date('2024-01-15T10:30:00'),
    level: 'info',
    message: 'Training completed successfully'
  }
])

// 计算属性
const isDeepLearningModel = computed(() => {
  return ['LSTM', 'GRU', 'Transformer'].includes(props.task.modelType)
})

const modelParamsTable = computed(() => {
  const params = props.task.config.modelConfig.params
  return Object.entries(params).map(([key, value]) => ({
    parameter: key,
    value: value?.toString() || '--',
    description: getParamDescription(key, props.task.modelType)
  }))
})

const factorCategories = computed(() => {
  const categories: Record<string, number> = {}
  props.task.factors.forEach(factor => {
    const category = getCategoryText(factor.category)
    categories[category] = (categories[category] || 0) + 1
  })
  
  return Object.entries(categories).map(([name, count]) => ({
    name,
    count
  }))
})

const trainingEfficiency = computed(() => {
  if (props.task.duration === 0 || props.task.config.trainingParams.epochs === 0) return 0
  return (props.task.duration / 60) / props.task.config.trainingParams.epochs
})

const convergenceEpoch = computed(() => {
  // 模拟收敛轮次计算
  return Math.floor(props.task.config.trainingParams.epochs * 0.7)
})

const filteredLogs = computed(() => {
  let filtered = logs.value
  
  if (logLevel.value !== 'all') {
    filtered = filtered.filter(log => log.level === logLevel.value)
  }
  
  if (logSearch.value.trim()) {
    const query = logSearch.value.toLowerCase()
    filtered = filtered.filter(log => 
      log.message.toLowerCase().includes(query)
    )
  }
  
  return filtered
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

const getProgressStatus = (status: string) => {
  if (status === 'failed') return 'exception'
  if (status === 'completed') return 'success'
  return undefined
}

const getFrequencyText = (frequency: string) => {
  switch (frequency) {
    case 'daily': return '日频'
    case 'weekly': return '周频'
    case 'monthly': return '月频'
    default: return frequency
  }
}

const getCategoryText = (category: string) => {
  switch (category) {
    case 'technical': return '技术指标'
    case 'fundamental': return '基本面'
    case 'market': return '市场因子'
    case 'sentiment': return '情绪因子'
    default: return category
  }
}

const getCategoryTagType = (category: string) => {
  switch (category) {
    case 'technical': return 'primary'
    case 'fundamental': return 'success'
    case 'market': return 'warning'
    case 'sentiment': return 'info'
    default: return 'info'
  }
}

const getParamDescription = (param: string, modelType: string) => {
  const descriptions: Record<string, Record<string, string>> = {
    'LightGBM': {
      'num_leaves': '叶子节点数量，控制模型复杂度',
      'learning_rate': '学习率，控制每次迭代的步长',
      'feature_fraction': '每次迭代使用的特征比例'
    },
    'XGBoost': {
      'max_depth': '树的最大深度',
      'learning_rate': '学习率',
      'n_estimators': '树的数量'
    },
    'LSTM': {
      'hidden_size': '隐藏层神经元数量',
      'num_layers': 'LSTM层数',
      'dropout': 'Dropout比例'
    }
  }
  
  return descriptions[modelType]?.[param] || '参数说明'
}

const getCorrelationClass = (correlation: number) => {
  if (Math.abs(correlation) > 0.7) return 'high-correlation'
  if (Math.abs(correlation) > 0.3) return 'medium-correlation'
  return 'low-correlation'
}

const formatDateTime = (date: Date) => {
  return date.toLocaleString('zh-CN')
}

const formatDuration = (seconds: number) => {
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  
  if (hours > 0) {
    return `${hours}时${minutes}分`
  }
  return `${minutes}分`
}

const refreshLogs = () => {
  // 刷新日志
}

const downloadLogs = () => {
  // 下载日志
}

// 生命周期
onMounted(() => {
  // 初始化图表
})
</script>

<style scoped>
.training-task-detail {
  width: 100%;
}

.basic-info {
  padding: 16px 0;
}

.metric-value {
  font-weight: 600;
}

.metric-value.success {
  color: #67c23a;
}

.metric-value.info {
  color: #409eff;
}

.metric-value.warning {
  color: #e6a23c;
}

.metric-value.primary {
  color: #409eff;
}

.no-data {
  color: #c0c4cc;
}

.config-detail {
  padding: 16px 0;
}

.model-config h4 {
  margin: 0 0 16px 0;
  color: #303133;
}

.factors-info {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.factors-summary {
  display: flex;
  align-items: center;
  gap: 24px;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 6px;
}

.factor-categories {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.category-tag {
  margin-bottom: 4px;
}

.training-history {
  display: flex;
  flex-direction: column;
  gap: 32px;
}

.chart-card {
  height: 100%;
}

.chart-container {
  width: 100%;
  height: 300px;
  background: #f5f7fa;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #909399;
}

.chart-container.large {
  height: 400px;
}

.history-table h4 {
  margin: 0 0 16px 0;
  color: #303133;
}

.feature-analysis {
  display: flex;
  flex-direction: column;
  gap: 32px;
}

.feature-importance-card,
.feature-correlation-card {
  width: 100%;
}

.feature-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.feature-stats h4 {
  margin: 0 0 16px 0;
  color: #303133;
}

.high-correlation {
  color: #f56c6c;
  font-weight: 600;
}

.medium-correlation {
  color: #e6a23c;
  font-weight: 500;
}

.low-correlation {
  color: #909399;
}

.performance-analysis {
  display: flex;
  flex-direction: column;
  gap: 32px;
}

.metric-card {
  background: linear-gradient(135deg, #f0f8ff 0%, #e8f4fd 100%);
  border: 1px solid #d4e4fd;
}

.metric-trend {
  margin-left: 8px;
}

.metric-trend.positive {
  color: #67c23a;
}

.metric-trend.negative {
  color: #f56c6c;
}

.confusion-matrix,
.roc-curve {
  width: 100%;
}

.matrix-card,
.roc-card {
  width: 100%;
}

.training-logs {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.logs-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.log-filters,
.log-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.logs-content {
  height: 400px;
  overflow-y: auto;
  background: #1e1e1e;
  color: #e8e8e8;
  padding: 16px;
  border-radius: 6px;
  font-family: 'Monaco', 'Menlo', monospace;
  font-size: 13px;
  line-height: 1.5;
}

.log-entry {
  margin-bottom: 8px;
  display: flex;
  gap: 12px;
}

.log-timestamp {
  color: #666;
  flex-shrink: 0;
}

.log-level {
  flex-shrink: 0;
  width: 60px;
  font-weight: bold;
}

.log-info .log-level {
  color: #67c23a;
}

.log-warning .log-level {
  color: #e6a23c;
}

.log-error .log-level {
  color: #f56c6c;
}

.log-message {
  flex: 1;
}

@media (max-width: 768px) {
  .logs-header {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
  }
  
  .log-filters,
  .log-actions {
    justify-content: center;
  }
  
  .factors-summary {
    flex-direction: column;
    gap: 16px;
    text-align: center;
  }
  
  .feature-header {
    flex-direction: column;
    gap: 12px;
  }
}
</style>